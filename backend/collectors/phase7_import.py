"""Safe, explicit Phase 7 import of validated Himalayas records only."""
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .schema import canonical_url, parse_date
from ..db import backup_database, connect

SOURCE = 'Himalayas'
ALLOWED_CLASSIFICATIONS = {'remote_morocco_eligible', 'remote_worldwide_eligible'}


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _https_himalayas(value, route):
    parts = urlsplit(str(value or ''))
    return (parts.scheme == 'https' and parts.hostname == 'himalayas.app'
            and not parts.username and not parts.password and parts.path.startswith(route)
            and not parts.fragment)


def load_and_validate(jsonl_path):
    rows, rejected, seen_ids, seen_urls = [], [], set(), set()
    with open(jsonl_path, encoding='utf-8') as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except ValueError:
                rejected.append({'line': line_no, 'reason': 'invalid JSON'})
                continue
            reasons = []
            sid = str(item.get('source_id') or '').strip()
            source_url = str(item.get('url') or '').strip()
            apply_url = str(item.get('apply_url') or '').strip()
            if item.get('source') != SOURCE:
                reasons.append('wrong source')
            if item.get('current_status') != 'open' or (item.get('status_verification') or {}).get('http_status') != 200:
                reasons.append('status not verified open via HTTP 200')
            if item.get('location_classification') not in ALLOWED_CLASSIFICATIONS:
                reasons.append('unsupported or unknown eligibility classification')
            for key, value in (('title', item.get('title')), ('company', item.get('company')),
                               ('description', item.get('description')), ('published_at', item.get('published_at'))):
                if not str(value or '').strip():
                    reasons.append(f'missing {key}')
            if not sid or sid != source_url or not _https_himalayas(source_url, '/companies/'):
                reasons.append('invalid source ID/original listing URL')
            if not _https_himalayas(apply_url, '/companies/'):
                reasons.append('invalid required Himalayas application URL')
            if not item.get('attribution') or not item.get('eligibility_basis'):
                reasons.append('missing attribution or eligibility provenance')
            if sid and sid in seen_ids:
                reasons.append('duplicate source ID within staging')
            canon = canonical_url(source_url)
            if not canon:
                reasons.append('invalid canonical URL')
            if canon and canon in seen_urls:
                reasons.append('duplicate original URL within staging')
            if reasons:
                rejected.append({'line': line_no, 'source_id': sid or None, 'reasons': reasons})
                continue
            seen_ids.add(sid)
            seen_urls.add(canon)
            item['_canonical_url'] = canon
            item['_published'] = parse_date(item.get('published_at'))
            item['_expires'] = parse_date(item.get('expires_at'))
            if not item['_published']:
                rejected.append({'line': line_no, 'source_id': sid, 'reasons': ['unparseable publication date']})
                continue
            rows.append(item)
    return rows, rejected


def preview_import(database_path, jsonl_path):
    offers, rejected = load_and_validate(jsonl_path)
    uri = Path(database_path).resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True, timeout=15)) as db:
        db.row_factory = sqlite3.Row
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {'offres', 'entreprises', 'offer_source_identity', 'candidatures'}
        missing_tables = sorted(required - tables)
        identity_conflicts, candidates = [], []
        if not missing_tables:
            for item in offers:
                found = db.execute('SELECT offer_id FROM offer_source_identity WHERE source=? AND (external_id=? OR canonical_url=?) LIMIT 1',
                                   (SOURCE, item['source_id'], item['_canonical_url'])).fetchone()
                if found:
                    identity_conflicts.append({'source_id': item['source_id'], 'existing_offer_id': found['offer_id']})
        counts = {}
        if not missing_tables:
            for table in ('entreprises', 'offres', 'candidatures'):
                counts[table] = db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            existing = db.execute('SELECT "ID",Titre,entreprise_nom,ville,"Date publication" FROM offres').fetchall()
            for item in offers:
                title = str(item.get('title') or '').casefold().strip()
                company = str(item.get('company') or '').casefold().strip()
                matches = [row for row in existing if str(row['Titre'] or '').casefold().strip() == title
                           and str(row['entreprise_nom'] or '').casefold().strip() == company]
                if matches:
                    candidates.append({'source_id': item['source_id'], 'existing_offer_ids': [row['ID'] for row in matches],
                                       'decision': 'review only; source IDs remain distinct'})
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        version = db.execute('PRAGMA user_version').fetchone()[0]
    return {
        'database': str(Path(database_path).resolve()), 'database_sha256': _sha256(database_path),
        'database_user_version': version, 'database_integrity': integrity,
        'database_counts': counts, 'missing_tables': missing_tables,
        'input_records': len(offers) + len(rejected), 'eligible_validated_open_records': len(offers),
        'by_location_classification': {name: sum(row.get('location_classification') == name for row in offers)
                                       for name in sorted(ALLOWED_CLASSIFICATIONS)},
        'intern_employment_type': sum(str(row.get('source_employment_type') or '').casefold() == 'intern' for row in offers),
        'rejected': rejected, 'existing_source_identity_conflicts': identity_conflicts,
        'possible_existing_content_matches': candidates, 'unresolved_company_relationships': len(offers),
        'company_relationships_to_create': 0,
        'import_blockers': (['database integrity is not ok'] if integrity != 'ok' else [])
            + ([f'missing schema tables: {missing_tables}'] if missing_tables else [])
            + ([f'{len(identity_conflicts)} existing source identity conflicts'] if identity_conflicts else []),
    }, offers


def backup_and_verify(database_path, backup_dir):
    before = _sha256(database_path)
    target = backup_database(database_path, backup_dir, 'phase7_avant_import')
    backup_hash = _sha256(target)
    uri = Path(target).resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True, timeout=15)) as check:
        integrity = check.execute('PRAGMA integrity_check').fetchone()[0]
        version = check.execute('PRAGMA user_version').fetchone()[0]
        counts = {name: check.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                  for name in ('entreprises', 'offres', 'candidatures')}
    if integrity != 'ok' or before != _sha256(database_path) or backup_hash != _sha256(target):
        raise RuntimeError('Backup verification failed; refusing database writes.')
    return {'path': str(target.resolve()), 'sha256': backup_hash, 'integrity': integrity,
            'user_version': version, 'counts': counts, 'source_sha256': before}


def apply_import(database_path, backup_dir, jsonl_path, expected_sha256):
    report, offers = preview_import(database_path, jsonl_path)
    if report['database_sha256'] != expected_sha256:
        raise RuntimeError('Database changed after the final import preview; refusing writes.')
    if report['database_integrity'] != 'ok' or report['import_blockers'] or report['rejected']:
        raise RuntimeError('Preview has validation blockers; refusing writes.')
    # Confirm the additive Phase 11 column was migrated before any insert.
    with closing(sqlite3.connect(Path(database_path).resolve().as_uri() + '?mode=ro', uri=True)) as check:
        offer_columns = {row[1] for row in check.execute('PRAGMA table_info(offres)')}
    if 'source_metadata_json' not in offer_columns:
        raise RuntimeError('Additive source metadata migration is required before import.')
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    inserted_ids, duplicate_candidates, candidates = [], [], []
    with connect(database_path) as db:
        db.execute('BEGIN IMMEDIATE')
        for item in offers:
            existing = db.execute('SELECT offer_id FROM offer_source_identity WHERE source=? AND (external_id=? OR canonical_url=?) LIMIT 1',
                                  (SOURCE, item['source_id'], item['_canonical_url'])).fetchone()
            if existing:
                raise RuntimeError('A source identity appeared after preview; transaction aborted.')
            offer_id = db.execute('SELECT COALESCE(MAX("ID"),0)+1 FROM offres').fetchone()[0]
            metadata = {
                'record_type': 'remote_job', 'source': SOURCE, 'source_id': item['source_id'],
                'source_url': item['url'], 'application_url': item['apply_url'],
                'attribution': item['attribution'], 'location_classification': item['location_classification'],
                'location_eligibility': item.get('location_eligibility'),
                'eligibility_basis': item.get('eligibility_basis'),
                'source_location_restrictions': item.get('source_location_restrictions'),
                'source_employment_type': item.get('source_employment_type'),
                'source_seniority': item.get('source_seniority'), 'current_status': item['current_status'],
                'status_verification': item.get('status_verification'), 'captured_at': item.get('captured_at'),
                'published_at_raw': item.get('published_at'), 'expires_at_raw': item.get('expires_at'),
                'query_keywords': item.get('query_keywords'), 'remote': True,
                'company_match_verified': False,
            }
            db.execute('''INSERT INTO offres("ID","Titre","Description","Type contrat","Type stage",
                "Date publication","Date expiration","Lien annonce","Lien public","Entreprise ID",source,
                entreprise_nom,entreprise_ref,relation_verified,ville,competences,collected_at,last_verified_at,
                statut_offre,source_metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (offer_id,item['title'],item.get('description'),item.get('source_employment_type'),None,
                 item['_published'],item['_expires'],item['url'],item['apply_url'],None,SOURCE,item['company'],
                 None,0,None,', '.join(item.get('source_seniority') or []),item.get('captured_at') or stamp,
                 item.get('status_verification',{}).get('checked_at') or stamp,'active',
                 json.dumps(metadata,ensure_ascii=False,sort_keys=True)))
            db.execute('''INSERT INTO offer_source_identity
                (offer_id,source,external_id,canonical_url,first_seen,last_seen,content_hash)
                VALUES (?,?,?,?,?,?,?)''',
                (offer_id,SOURCE,item['source_id'],item['_canonical_url'],stamp,stamp,
                 hashlib.sha256(json.dumps(metadata,sort_keys=True,ensure_ascii=False).encode()).hexdigest()))
            inserted_ids.append(offer_id)
            candidates.append({'ID':offer_id,'title':item['title'],'company':item['company'],'published_at':item['_published']})
        existing = db.execute('SELECT "ID",Titre,entreprise_nom,"Date publication" FROM offres WHERE source<>?',(SOURCE,)).fetchall()
        for added in candidates:
            for old in existing:
                if str(old['Titre'] or '').casefold().strip() == added['title'].casefold().strip() and str(old['entreprise_nom'] or '').casefold().strip() == added['company'].casefold().strip():
                    duplicate_candidates.append({'new_offer_id':added['ID'],'existing_offer_id':old['ID']})
    return {'imported':len(inserted_ids),'offer_ids':inserted_ids,'duplicate_candidates':duplicate_candidates}
