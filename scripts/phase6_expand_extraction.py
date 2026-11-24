"""One-time Phase 6 filtered extraction to a new isolated JSONL file.

This CLI calls only the existing Himalayas public connector. It does not import
the application, read a project database, or schedule/activate collection.
"""
import json
import re
import sys
import tempfile
import unicodedata
from time import sleep
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.collectors.free_apis import (MAX_PAGES, check_himalayas_job,
                                           deduplicate_records, fetch_himalayas)

QUERIES = [
    'Marrakech', 'Morocco', 'Maroc', 'Casablanca', 'Rabat',
    'Software Developer', 'Web Developer', 'Data Analyst', 'Data Scientist',
    'Digital Marketing', 'Graphic Designer', 'Business Analyst', 'Internship',
    'Intern', 'Junior Developer',
]
MAX_STATUS_CHECKS = 40


def _norm(value):
    value = unicodedata.normalize('NFKD', str(value or '').casefold())
    value = ''.join(c for c in value if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def possible_duplicate_pairs(records):
    """Report conservative review candidates; never merge similar jobs."""
    groups = defaultdict(list)
    for record in records:
        title, company = _norm(record.get('title')), _norm(record.get('company'))
        published = record.get('published_at')
        location = _norm(record.get('city') or record.get('location_classification'))
        if title and company and published and location:
            groups[(title, company, location, published)].append(record)
    return [[a.get('source_id'), b.get('source_id')]
            for group in groups.values() for i, a in enumerate(group)
            for b in group[i + 1:] if a.get('source_id') != b.get('source_id')]


def stage_records(records, output_path=None):
    merged = {}
    for record in records:
        identity = record.get('source_id') or record.get('canonical_url')
        key = (record.get('source'), identity)
        if key in merged:
            merged[key]['_query_matches'] = sorted(set(merged[key].get('_query_matches', []) +
                                                        record.get('_query_matches', [])))
        else:
            merged[key] = dict(record)
    unique, exact_duplicates = deduplicate_records(list(merged.values()))
    exact_duplicates += len(records) - len(merged)
    for record in unique:
        record['query_matches'] = sorted(set(record.pop('_query_matches', [])))
    if output_path:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = path.open('x', encoding='utf-8', newline='\n')
    else:
        handle = tempfile.NamedTemporaryFile(mode='x', encoding='utf-8', newline='\n',
                    prefix='stagex_phase6_himalayas_', suffix='.jsonl', delete=False)
        path = Path(handle.name)
    with handle:
        for record in unique:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
    return path, unique, exact_duplicates


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='New JSONL path; existing files are never overwritten.')
    parser.add_argument('--status-check-limit', type=int, default=40,
                        help='Maximum individual official job-status checks; 0 disables them.')
    args = parser.parse_args()
    if not 0 <= args.status_check_limit <= MAX_STATUS_CHECKS:
        parser.error(f'--status-check-limit must be between 0 and {MAX_STATUS_CHECKS}')

    all_records, query_reports = [], []
    for index, query in enumerate(QUERIES):
        metrics = {}
        pages = 2 if query == 'Software Developer' else 1
        records = fetch_himalayas(query, 'MA', pages, metrics=metrics)
        for record in records:
            record['_query_matches'] = [query]
        all_records.extend(records)
        query_reports.append({
            'query': query,
            'http': 'successful JSON response; numeric status is not exposed by existing connector',
            'requests': metrics.get('request_count', 0), 'pages_received': metrics.get('pages', 0),
            'records_received': metrics.get('received_count', 0),
            'valid_morocco_or_worldwide': metrics.get('valid_count', 0),
            'rejected': metrics.get('rejected_count', 0), 'pagination_cap': pages,
        })
        if index + 1 < len(QUERIES):
            sleep(1.05)

    # Exact identity only; title/company similarities are review candidates, not merges.
    combined = {}
    for record in all_records:
        identity = record.get('source_id') or record.get('canonical_url')
        key = (record.get('source'), identity)
        if key in combined:
            combined[key]['_query_matches'] = sorted(set(combined[key].get('_query_matches', []) +
                                                               record.get('_query_matches', [])))
        else:
            combined[key] = record
    exact_duplicate_count = len(all_records) - len(combined)
    possible_duplicates = possible_duplicate_pairs(list(combined.values()))

    # The provider exposes a per-listing status endpoint. Check a bounded subset
    # sequentially; do not fetch protected pages or infer status from title.
    status_reports = []
    rows = list(combined.values())
    for record in rows:
        record['expiry_derived_status'] = record.get('status', 'unknown')
        record['current_status'] = 'unverified'
        record['status_verification'] = 'not_checked'
    for index, record in enumerate(rows[:args.status_check_limit]):
        try:
            result = check_himalayas_job(record.get('source_id'))
            record['current_status'] = 'open' if result['http_status'] == 200 else 'closed'
            record['status_verification'] = {
                'source': 'Himalayas documented job status API',
                'http_status': result['http_status'],
                'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            }
            status_reports.append({'source_id': record.get('source_id'),
                                   'http': result['http_status'],
                                   'status': record['current_status']})
        except Exception as exc:  # Preserve failed checks as unknown, never discard evidence.
            record['current_status'] = 'unknown'
            record['status_verification'] = {'source': 'Himalayas documented job status API',
                                             'result': 'request error', 'error': type(exc).__name__}
            status_reports.append({'source_id': record.get('source_id'), 'http': 'request error',
                                   'status': 'unknown', 'error': type(exc).__name__})
        if index + 1 < min(len(rows), args.status_check_limit):
            sleep(1.05)

    path, staged, _ = stage_records(list(combined.values()), args.output)
    classification_counts = {}
    for record in staged:
        category = record.get('location_classification', 'unknown')
        classification_counts[category] = classification_counts.get(category, 0) + 1
    report = {
        'source': 'Himalayas', 'captured_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'country_filter': 'MA', 'queries': query_reports,
        'requests_total': sum(x['requests'] for x in query_reports),
        'status_checks': status_reports,
        'status_checks_not_attempted': max(0, len(staged) - len(status_reports)),
        'unique_staged': len(staged), 'exact_duplicate_records': exact_duplicate_count,
        'possible_duplicate_pairs_for_review': possible_duplicates,
        'classification_counts': classification_counts,
        'morocco_eligible': sum(r.get('location_classification') in
            ('remote_morocco_eligible', 'remote_worldwide_eligible') for r in staged),
        'verified_physical_marrakech': sum(r.get('city_verified') and
            _norm(r.get('city')) == 'marrakech' for r in staged),
        'with_application_url': sum(bool(r.get('source_application_url')) for r in staged),
        'with_source_attribution': sum(bool(r.get('attribution')) for r in staged),
        'staging_file': str(path), 'database_imported': False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
