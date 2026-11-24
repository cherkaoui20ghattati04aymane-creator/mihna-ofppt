"""Bounded synchronization of the documented free Jobicy jobs and status APIs."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

import requests

from ..db import backup_database
from .schema import content_hash, normalize_offer

SOURCE = 'Jobicy'
API = 'https://jobicy.com/api/jobs'
TERMS = 'https://github.com/Jobicy/remote-jobs-api#fair-use'
_LOG = logging.getLogger(__name__)

class SourcePaused(ValueError):
    """An access or quota response requires an operator review."""


def normalize(job):
    ident = job.get('id')
    if type(ident) is not int or ident <= 0 or str(job.get('jobGeo') or '').strip().casefold() != 'anywhere':
        return None
    url = str(job.get('url') or '')
    pieces = urlsplit(url)
    if (pieces.scheme, pieces.netloc) != ('https', 'jobicy.com') or not pieces.path.startswith('/jobs/'):
        return None
    types = job.get('jobType')
    item = normalize_offer({
        'source_id': str(ident), 'title': job.get('jobTitle'), 'company': job.get('companyName'),
        'description': job.get('jobDescription') or job.get('jobExcerpt'), 'url': url,
        'contract_type': ', '.join(t for t in types if isinstance(t, str)) if isinstance(types, list) else types,
        'published_at': job.get('pubDate'),
    }, SOURCE)
    if item is None:
        return None
    item['metadata'] = {
        'source_id': str(ident), 'source_url': url, 'attribution': 'Source : Jobicy',
        'terms_url': TERMS, 'location_classification': 'remote_worldwide_eligible',
        'source_location_restrictions': job['jobGeo'], 'remote': True,
        'salary': {key: job[key] for key in ('salaryMin','salaryMax','salaryCurrency','salaryPeriod')
                   if type(job.get(key)) in (str, int, float) and job[key] != ''},
    }
    return item


def status_map(payload):
    if not isinstance(payload, dict) or payload.get('success') is not True or not isinstance(payload.get('jobs'), list):
        raise ValueError('Invalid Jobicy status payload')
    return {str(row['id']): row['status'] for row in payload['jobs'] if isinstance(row, dict)
            and type(row.get('id')) is int and row.get('status') in ('active','closed','unknown')}


def _request(client, url, params):
    response = client.get(url, params=params, timeout=20, allow_redirects=False)
    if response.status_code in (401, 403, 429):
        raise SourcePaused(f'Jobicy HTTP {response.status_code}')
    if response.status_code != 200:
        raise ValueError(f'Jobicy HTTP {response.status_code}')
    payload = response.json()
    if not isinstance(payload, dict) or payload.get('success') is not True or not isinstance(payload.get('jobs'), list):
        raise ValueError('Invalid Jobicy response')
    return payload


def discover(client, page_limit=2):
    params = {'count':20, 'geo':'anywhere'}
    items = {}
    seen_cursors = set()
    for _ in range(page_limit):
        payload = _request(client, API, params)
        for job in payload['jobs']:
            if isinstance(job, dict) and (item := normalize(job)):
                items[item['source_id']] = item
        cursor = payload.get('nextCursor')
        if not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
            break
        seen_cursors.add(cursor)
        params['cursor'] = cursor
    return items


def known_identities(primary):
    with closing(sqlite3.connect(primary.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        return [row[0] for row in db.execute('''SELECT i.external_id FROM offer_source_identity i
            JOIN offres o ON o.ID=i.offer_id WHERE i.source=? AND o.source=i.source
            AND i.external_id IS NOT NULL AND o.statut_offre!='expired'
            ORDER BY o.last_verified_at LIMIT 300''', (SOURCE,))]


def verify_statuses(client, ids):
    valid_ids = sorted({ident for ident in ids if ident.isascii() and ident.isdecimal()})
    result = {}
    for index in range(0, len(valid_ids), 100):
        batch = valid_ids[index:index+100]
        response = status_map(_request(client, API+'/status', {'ids':','.join(batch)}))
        result.update({ident: response[ident] for ident in batch if ident in response})
    return result


def sync(primary, workspaces, backups, items, statuses, checked_at):
    checked = datetime.fromisoformat(checked_at)
    if not timedelta(0) <= datetime.now(timezone.utc) - checked <= timedelta(hours=1):
        raise ValueError('Jobicy verification is not recent')
    paths = [primary, *workspaces]
    for index,path in enumerate(paths):
        snapshot = backup_database(path, backups, f'avant_jobicy_{index}')
        with closing(sqlite3.connect(snapshot.resolve().as_uri()+'?mode=ro', uri=True)) as check:
            if check.execute('PRAGMA integrity_check').fetchone() != ('ok',) or check.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Invalid Jobicy backup')
    schemas = ['main', *(f'account_{i}' for i in range(len(workspaces)))]
    with closing(sqlite3.connect(primary.resolve().as_uri()+'?mode=rw', uri=True, timeout=25)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        for schema,path in zip(schemas[1:],workspaces):
            db.execute(f'ATTACH DATABASE ? AS {schema}', (path.resolve().as_uri()+'?mode=rw',))
        db.execute('BEGIN IMMEDIATE')
        if any(db.execute(f'PRAGMA {s}.user_version').fetchone() != (11,) or
               db.execute(f'PRAGMA {s}.journal_mode').fetchone() != ('delete',) for s in schemas):
            raise ValueError('Expected v11 with atomic rollback journaling')
        highest = max(db.execute(f'SELECT COALESCE(MAX(ID),0) FROM {s}.offres').fetchone()[0] for s in schemas)
        counts = {s:{'new':0,'updated':0,'closed':0} for s in schemas}
        for ident,status in statuses.items():
            item = items.get(ident)
            existing = {s:db.execute(f'SELECT offer_id FROM {s}.offer_source_identity WHERE source=? AND external_id=?',
                                     (SOURCE, ident)).fetchone() for s in schemas}
            if status == 'active' and item and not any(existing.values()):
                if any(db.execute(f'SELECT 1 FROM {s}.offres WHERE "Lien annonce"=? OR "Lien public"=?',
                                  (item['url'],item['url'])).fetchone() for s in schemas):
                    continue
                highest += 1
                for s in schemas:
                    db.execute(f'''INSERT INTO {s}.offres(ID,Titre,Description,"Type contrat","Date publication",
                        "Lien annonce","Lien public",source,entreprise_nom,collected_at,last_verified_at,statut_offre,source_metadata_json)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,'active',?)''',
                        (highest,item['title'],item['description'] or None,item['contract_type'] or None,item['published_at'],
                         item['url'],item['url'],SOURCE,item['company'] or None,checked_at,checked_at,
                         json.dumps(item['metadata'],ensure_ascii=False)))
                    db.execute(f'''INSERT INTO {s}.offer_source_identity
                        (offer_id,source,external_id,canonical_url,first_seen,last_seen,content_hash)
                        VALUES (?,?,?,?,?,?,?)''',(highest,SOURCE,ident,item['canonical_url'],checked_at,checked_at,content_hash(item)))
                    counts[s]['new'] += 1
                continue
            for s,match in existing.items():
                if not match:
                    continue
                label = {'active':'active','closed':'expired','unknown':'unknown'}[status]
                db.execute(f'''UPDATE {s}.offres SET statut_offre=?,last_verified_at=?
                    WHERE ID=? AND source=?''',(label,checked_at,match[0],SOURCE))
                if status == 'active':
                    db.execute(f'UPDATE {s}.offer_source_identity SET last_seen=? WHERE source=? AND external_id=?',
                               (checked_at,SOURCE,ident))
                    if item:
                        db.execute(f'''UPDATE {s}.offres SET Titre=?,Description=COALESCE(?,Description),
                            "Type contrat"=COALESCE(?,"Type contrat"),"Date publication"=COALESCE(?,"Date publication"),
                            "Lien annonce"=?,"Lien public"=?,entreprise_nom=COALESCE(?,entreprise_nom),source_metadata_json=?
                            WHERE ID=? AND source=?''',
                            (item['title'],item['description'] or None,item['contract_type'] or None,item['published_at'],
                             item['url'],item['url'],item['company'] or None,
                             json.dumps(item['metadata'],ensure_ascii=False),match[0],SOURCE))
                        db.execute(f'''UPDATE {s}.offer_source_identity SET canonical_url=?,content_hash=?
                            WHERE source=? AND external_id=?''',
                            (item['canonical_url'],content_hash(item),SOURCE,ident))
                counts[s]['updated'] += 1
                counts[s]['closed'] += status == 'closed'
        for s,values in counts.items():
            run = db.execute(f'''INSERT INTO {s}.collector_runs
                (mode,status,started_at,finished_at,source_count,fetched_count,new_offers,updated_offers,expired_offers,imported_at,imported_offers)
                VALUES ('jobicy-sync','imported',?,?,1,?,?,?,?,?,?)''',
                (checked_at,checked_at,len(items),values['new'],values['updated'],values['closed'],checked_at,values['new'])).lastrowid
            db.execute(f'''INSERT INTO {s}.collector_source_runs
                (run_id,source,status,started_at,finished_at,fetched_count,new_offers,updated_offers,imported_at,imported_offers)
                VALUES (?,?,'imported',?,?,?,?,?,?,?)''',
                (run,SOURCE,checked_at,checked_at,len(items),values['new'],values['updated'],checked_at,values['new']))
            if db.execute(f'PRAGMA {s}.foreign_key_check').fetchone():
                raise ValueError('Jobicy sync would break referential integrity')
        db.commit()
    return counts['main']


def run_periodic(primary, workspaces, backups, stop, hours):
    primary, workspaces, backups = map(Path, (primary, workspaces, backups))
    state_path = backups/'last_attempt.txt'
    pause_path = backups/'paused.txt'
    while not stop.is_set():
        try:
            if pause_path.is_file():
                stop.wait(3600)
                continue
            with closing(sqlite3.connect(primary.resolve().as_uri()+'?mode=ro', uri=True)) as db:
                last, = db.execute("SELECT MAX(finished_at) FROM collector_source_runs WHERE source=?", (SOURCE,)).fetchone()
            attempt = datetime.fromisoformat(state_path.read_text(encoding='ascii')) if state_path.is_file() else None
            current = datetime.now(timezone.utc)
            if (not attempt or current-attempt >= timedelta(hours=1)) and (
                    not last or current-datetime.fromisoformat(last) >= timedelta(hours=hours)):
                backups.mkdir(parents=True, exist_ok=True)
                temporary = state_path.with_suffix('.tmp')
                temporary.write_text(current.isoformat(), encoding='ascii')
                temporary.replace(state_path)
                with requests.Session() as client:
                    client.headers.update({'User-Agent':'Mihna catalog sync/1.0','Accept':'application/json'})
                    items = discover(client)
                    statuses = verify_statuses(client, [*known_identities(primary),*items])
                if not stop.is_set():
                    result = sync(primary, sorted(workspaces.glob('*.db')), backups, items, statuses,
                                  datetime.now(timezone.utc).isoformat(timespec='seconds'))
                    _LOG.warning('Jobicy sync: %s', result)
        except SourcePaused as exc:
            pause_path.write_text(str(exc)+'\n', encoding='ascii')
            _LOG.warning('Jobicy requires operator review (%s)', exc)
        except (OSError, ValueError, sqlite3.Error, requests.RequestException) as exc:
            _LOG.warning('Jobicy sync paused (%s)', str(exc) if str(exc).startswith('Jobicy HTTP ') else type(exc).__name__)
        stop.wait(3600)
