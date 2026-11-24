"""Import staged Wadifa competitions only after matching the live feed and official URLs."""
import argparse
from contextlib import closing
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

SOURCE = 'Wadifa Info'
ATTRIBUTION = 'Source : Wadifa Info'


def verified_records(staged, feed, notice_status):
    keys = {'title': 'grade', 'employer': 'employer', 'published_at': 'published',
            'deadline': 'deadline', 'source_url': 'url', 'official_notice_url': 'official_notice'}
    live = {str(item['id']): item for item in feed['items']}
    today = datetime.now(timezone.utc).date()
    records = {}
    for item in staged:
        ident = str(item['source_id'])
        current = live.get(ident)
        if not current or notice_status.get(ident) != 200 or item.get('source') != SOURCE:
            continue
        if any(item.get(field) != current.get(key) for field, key in keys.items()):
            continue
        if not item['title'] or not item['employer'] or ident in records:
            raise ValueError('Incomplete or duplicate staged source identity')
        original, official = [urlsplit(item[field]) for field in ('source_url', 'official_notice_url')]
        if (original.scheme, original.hostname) != ('https', 'www.wadifa-info.com'):
            continue
        if official.scheme != 'https' or official.hostname not in ('www.emploi-public.ma', 'emploi-public.ma'):
            continue
        if not original.path.strip('/') or not official.path.strip('/'):
            continue
        try:
            publication, deadline = (date.fromisoformat(item[field]) for field in ('published_at', 'deadline'))
        except (TypeError, ValueError):
            continue
        if publication > today or deadline < today:
            continue
        records[ident] = item
    return records


def import_records(primary, workspaces, records):
    paths = [primary, *workspaces]
    schemas = ['main', *(f'workspace_{i}' for i in range(len(workspaces)))]
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with closing(sqlite3.connect(primary.resolve().as_uri() + '?mode=rw', uri=True, timeout=30)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        for schema, path in zip(schemas[1:], workspaces):
            db.execute(f'ATTACH DATABASE ? AS {schema}', (path.resolve().as_uri() + '?mode=rw',))
        db.execute('BEGIN IMMEDIATE')
        for schema in schemas:
            if db.execute(f'PRAGMA {schema}.user_version').fetchone()[0] != 11:
                raise ValueError('Expected database schema v11')
            if db.execute(f'PRAGMA {schema}.journal_mode').fetchone()[0] != 'delete':
                raise ValueError('Atomic multi-database import requires rollback journaling')
        max_id = max(db.execute(f'SELECT COALESCE(MAX(ID),0) FROM {schema}.offres').fetchone()[0] for schema in schemas)
        inserted = 0
        for ident,item in records.items():
            existing = {schema: db.execute(f'''SELECT offer_id FROM {schema}.offer_source_identity
                WHERE source=? AND (external_id=? OR canonical_url=?)''', (SOURCE, ident, item['source_url'])).fetchall()
                for schema in schemas}
            ids = {row[0] for matches in existing.values() for row in matches}
            if ids:
                if len(ids) != 1 or not all(len(matches) == 1 for matches in existing.values()):
                    raise ValueError('Conflicting or unsynchronized Wadifa identity')
                continue
            if any(db.execute(f'SELECT 1 FROM {schema}.offres WHERE "Lien annonce"=? OR "Lien public"=?',
                              (item['source_url'], item['official_notice_url'])).fetchone() for schema in schemas):
                continue
            max_id += 1
            metadata = json.dumps({
                'record_type': 'public_sector_recruitment_competition', 'source_id': ident,
                'source_url': item['source_url'], 'official_notice_url': item['official_notice_url'],
                'attribution': ATTRIBUTION, 'license': 'CC BY 4.0', 'number_of_posts': item['number_of_posts'],
                'country': 'MA', 'location_classification': 'unknown', 'captured_at': item['captured_at'],
                'verified_at': now,
            }, ensure_ascii=False)
            for schema in schemas:
                db.execute(f'''INSERT INTO {schema}.offres(ID,Titre,"Date publication","Date expiration",
                    "Lien annonce","Lien public",source,entreprise_nom,relation_verified,collected_at,
                    last_verified_at,statut_offre,source_metadata_json)
                    VALUES (?,?,?,?,?,?,?,?,0,?,?,'active',?)''',
                    (max_id,item['title'],item['published_at'],item['deadline'],item['source_url'],
                     item['official_notice_url'],SOURCE,item['employer'],item['captured_at'],now,metadata))
                db.execute(f'''INSERT INTO {schema}.offer_source_identity
                    (offer_id,source,external_id,canonical_url,first_seen,last_seen,content_hash)
                    VALUES (?,?,?,?,?,?,?)''', (max_id,SOURCE,ident,item['source_url'],now,now,
                                               hashlib.sha256(metadata.encode()).hexdigest()))
            inserted += 1
        for schema in schemas:
            if db.execute(f'PRAGMA {schema}.integrity_check').fetchall() != [('ok',)] or db.execute(
                    f'PRAGMA {schema}.foreign_key_check').fetchone():
                raise ValueError('Integrity check failed after import')
        db.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('stage', 'feed', 'notices'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--apply', action='store_true', help='Apply only after backing up each destination database')
    args = parser.parse_args()
    staged = [json.loads(line) for line in args.stage.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    records = verified_records(staged, json.loads(args.feed.read_bytes()), json.loads(args.notices.read_bytes()))
    print(f'{len(records)} of {len(staged)} staged records verified against the current feed and official notices.')
    if args.apply:
        count = import_records(Path('database/stages_marrakech.db'), sorted(Path('private/user_data').glob('*.db')), records)
        print(f'{count} offers added to the production catalog and each existing workspace.')


if __name__ == '__main__':
    main()
