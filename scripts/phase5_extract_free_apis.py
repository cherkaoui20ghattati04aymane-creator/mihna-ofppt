"""Bounded Phase 5 extraction into an isolated JSONL staging file.

This script does not import the application, open a database, or modify project
data. It intentionally requires a query and caps Himalayas pagination.
"""
import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.collectors.free_apis import MAX_PAGES, deduplicate_records, fetch_himalayas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', default='Marrakech', help='Keyword filter; defaults to Marrakech.')
    parser.add_argument('--country', default='MA', help='ISO country filter; this connector accepts MA (Morocco).')
    parser.add_argument('--max-pages', type=int, default=1, choices=range(1, MAX_PAGES + 1),
                        help=f'Maximum API pages (1–{MAX_PAGES}, 20 jobs/page).')
    parser.add_argument('--output', help='New JSONL path. Existing files are never overwritten.')
    args = parser.parse_args()

    metrics = {}
    records = fetch_himalayas(args.query, args.country, args.max_pages, metrics=metrics)
    records, duplicates = deduplicate_records(records)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    if output_path is None:
        handle = tempfile.NamedTemporaryFile(mode='x', encoding='utf-8', newline='\n',
                    prefix='stagex_phase5_himalayas_', suffix='.jsonl', delete=False)
        output_path = Path(handle.name)
    else:
        handle = output_path.open('x', encoding='utf-8', newline='\n')
    with handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')

    summary = {
        'source': 'Himalayas',
        'captured_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'query': args.query,
        'country_filter': args.country,
        'requests': metrics.get('request_count', 0),
        'pages': metrics.get('pages', 0),
        'records_received': metrics.get('received_count', 0),
        'valid_records': metrics.get('valid_count', 0),
        'duplicates': duplicates,
        'rejected_records': metrics.get('rejected_count', 0),
        'morocco_eligible_remote': sum(r.get('location_classification') in
                                       ('remote_morocco_eligible', 'remote_worldwide_eligible') for r in records),
        'explicit_morocco_restricted': sum(r.get('location_classification') == 'remote_morocco_eligible' for r in records),
        'worldwide_remote_eligible': sum(r.get('location_classification') == 'remote_worldwide_eligible' for r in records),
        'marrakech_keyword_matches': sum('marrakech' in (r.get('title') or '').casefold() for r in records),
        'physical_marrakech_confirmed': 0,
        'staging_file': str(output_path),
        'imported_to_project_database': False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
