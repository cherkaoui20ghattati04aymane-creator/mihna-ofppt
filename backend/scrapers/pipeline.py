"""Orchestration : autorisation → collecte → qualité → staging (revue humaine) → import existant.

Rien n'est importé dans ``offres`` par ce module : les annonces arrivent en staging (statut
« pending ») et suivent le parcours existant du Centre de collecte (décision ligne par ligne,
sauvegarde avant import, confirmation des droits).
"""
from __future__ import annotations

import json
import logging
import time

from ..collectors.schema import identity_key, normalize_offer
from ..collectors.service import create_run, get_setting, set_setting, sources_config
from ..db import connect, now
from . import jawb_scraper, wadifa_scraper
from .base import NotAuthorized, ScraperError

logger = logging.getLogger('stages.scrapers')
SCRAPERS = {'jawb': jawb_scraper, 'wadifa': wadifa_scraper}
RIGHTS = ('consultation_allowed', 'storage_allowed', 'display_allowed')
DEFAULTS = {
    'jawb': {'enabled': False, 'permission_ref': '', 'consultation_allowed': False, 'storage_allowed': False,
             'display_allowed': False, 'description_allowed': False, 'city': 'Marrakech', 'profession': '', 'feed_url': ''},
    'wadifa': {'enabled': False, 'permission_ref': '', 'consultation_allowed': False, 'storage_allowed': False,
               'display_allowed': False, 'description_allowed': False, 'feed_url': ''},
}
SETTING_KEY = 'scrapers_config'


def get_config(path):
    stored = get_setting(path, SETTING_KEY, {}) or {}
    if isinstance(stored, str):
        try:
            stored = json.loads(stored)
        except ValueError:
            stored = {}
    return {key: {**defaults, **(stored.get(key) or {})} for key, defaults in DEFAULTS.items()}


def set_config(path, source, values):
    if source not in SCRAPERS:
        raise LookupError('Connecteur inconnu.')
    if not isinstance(values, dict):
        raise ValueError('Configuration invalide.')
    current = get_config(path)
    entry = dict(current[source])
    for key, default in DEFAULTS[source].items():
        if key not in values:
            continue
        value = values[key]
        if isinstance(default, bool):
            if not isinstance(value, bool):
                raise ValueError(f'« {key} » doit être vrai ou faux.')
        else:
            if not isinstance(value, str) or len(value) > 500:
                raise ValueError(f'« {key} » invalide.')
            value = value.strip()
        entry[key] = value
    if entry['enabled']:
        missing = authorization_reasons(entry)
        if missing:
            raise ValueError('Activation refusée : ' + ' '.join(missing))
    current[source] = entry
    with connect(path) as db:
        set_setting(db, SETTING_KEY, current)
    return current


def authorization_reasons(entry):
    reasons = []
    if not str(entry.get('permission_ref') or '').strip():
        reasons.append('Référence de l’autorisation écrite du site manquante.')
    for key, label in zip(RIGHTS, ('consultation automatique', 'stockage local', 'réaffichage')):
        if entry.get(key) is not True:
            reasons.append(f'Droit de {label} non confirmé.')
    return reasons


def status(path):
    cfg, external = get_config(path), sources_config(path)['external_enabled']
    out = {}
    for key, entry in cfg.items():
        reasons = authorization_reasons(entry)
        if not entry['enabled']:
            reasons.insert(0, 'Connecteur désactivé.')
        if not external:
            reasons.append('Collecte externe globale désactivée (Centre de collecte).')
        if key == 'wadifa' and not entry.get('feed_url'):
            reasons.append('Adresse du flux RSS de wadifa.info non renseignée.')
        out[key] = {**entry, 'source_name': SCRAPERS[key].SOURCE, 'ready': not reasons, 'reasons': reasons}
    return out


def _offer_from(record, source_name):
    kind = record['opportunity_type']
    contract = 'Stage' if kind.startswith('Stage') else kind if kind != 'Non précisé' else ''
    return normalize_offer({
        'source_id': record['dedupe_key'], 'title': record['title'], 'company': record['organization'] or '',
        'city': record['city'] or '', 'description': record['description'], 'contract_type': contract,
        'internship_type': 'PFE' if kind == 'Stage PFE' else '', 'published_at': record['published_at'],
        'expires_at': record['deadline'], 'url': record['url']}, source_name)


def run(path, source, fetcher=None):
    if source not in SCRAPERS:
        raise LookupError('Connecteur inconnu.')
    state = status(path)[source]
    if not state['ready']:
        raise NotAuthorized('Collecte bloquée : ' + ' '.join(state['reasons']))
    module = SCRAPERS[source]
    run_id = create_run(path, 'scraper')
    started, stamp = time.perf_counter(), now()
    metadata = {'kind': 'scraper', 'source_key': source, 'source_name': module.SOURCE,
                'permission_ref': state['permission_ref'], **{k: True for k in RIGHTS},
                'description_allowed': state['description_allowed'],
                'fields_stored': ['titre', 'organisme', 'ville', 'type', 'date de publication', 'date limite', 'URL d’origine',
                                  'source', 'date de collecte', 'statut de vérification'] + (['description'] if state['description_allowed'] else [])}
    try:
        result = module.collect(state, fetcher)
        metadata.update(robots_allowed=bool(result['robots_allowed']), url=result['url'], parse_errors=result['errors'])
        staged = 0
        with connect(path) as db:
            for record in result['records']:
                offer = _offer_from(record, module.SOURCE)
                if not offer:
                    continue
                offer['verification_status'] = record['verification_status']
                offer['collected_at'] = record['collected_at']
                cur = db.execute("INSERT OR IGNORE INTO collector_staging(run_id,source,identity_key,payload_json,decision) VALUES (?,?,?,?,'pending')",
                                 (run_id, module.SOURCE, identity_key(offer), json.dumps(offer, ensure_ascii=False)))
                staged += cur.rowcount
            duration = int((time.perf_counter() - started) * 1000)
            db.execute('INSERT INTO collector_source_runs(run_id,source,status,started_at,finished_at,fetched_count,duplicates,error_summary,duration_ms) VALUES (?,?,?,?,?,?,?,?,?)',
                       (run_id, module.SOURCE, 'previewed', stamp, now(), staged, result['duplicates'],
                        (f"{len(result['errors'])} annonce(s) rejetée(s) (titre ou URL invalide)." if result['errors'] else None), duration))
            db.execute("UPDATE collector_runs SET status='previewed',finished_at=?,source_count=1,fetched_count=?,duplicates=?,duration_ms=?,error_count=?,source_metadata_json=? WHERE id=?",
                       (now(), staged, result['duplicates'], duration, len(result['errors']), json.dumps(metadata, ensure_ascii=False), run_id))
        logger.info('scraper source=%s run=%s staged=%d duplicates=%d rejected=%d', source, run_id, staged, result['duplicates'], len(result['errors']))
        return {'id': run_id, 'status': 'previewed', 'source': module.SOURCE, 'staged': staged, 'duplicates': result['duplicates'],
                'rejected': len(result['errors']), 'robots_allowed': result['robots_allowed'],
                'message': 'Annonces en attente de votre revue dans le Centre de collecte. Rien n’a été importé.'}
    except (ScraperError, ValueError) as exc:
        with connect(path) as db:
            db.execute("UPDATE collector_runs SET status='failed',finished_at=?,error_summary=?,error_count=1,source_metadata_json=? WHERE id=?",
                       (now(), str(exc)[:500], json.dumps(metadata, ensure_ascii=False), run_id))
        logger.warning('scraper source=%s run=%s status=failed code=%s', source, run_id, getattr(exc, 'code', 'invalid'))
        return {'id': run_id, 'status': 'failed', 'source': module.SOURCE, 'error': str(exc)}
