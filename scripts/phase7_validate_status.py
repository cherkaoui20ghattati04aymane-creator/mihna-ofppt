"""Recheck unchecked Phase 6 Himalayas records; writes a separate JSONL file."""
import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.collectors.free_apis import check_himalayas_job

DEFAULT_INPUT = Path(tempfile.gettempdir()) / 'stagex_phase6_himalayas_e97yuql8.jsonl'
PER_MINUTE_SAFE_LIMIT = 50


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=str(DEFAULT_INPUT))
    parser.add_argument('--output')
    parser.add_argument('--batch-size', type=int, default=PER_MINUTE_SAFE_LIMIT,
                        choices=range(1, PER_MINUTE_SAFE_LIMIT + 1))
    parser.add_argument('--refresh-open-before', help='Also refresh records marked open before this ISO timestamp.')
    args = parser.parse_args()
    input_path = Path(args.input)
    rows = [json.loads(line) for line in input_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    todo = [r for r in rows if r.get('current_status') in (None, '', 'unverified', 'unchecked')]
    if args.refresh_open_before:
        cutoff = datetime.fromisoformat(args.refresh_open_before.replace('Z', '+00:00'))
        for record in rows:
            verification = record.get('status_verification') or {}
            checked_at = verification.get('checked_at')
            try:
                stale = (not checked_at) or datetime.fromisoformat(checked_at.replace('Z', '+00:00')) < cutoff
            except (TypeError, ValueError):
                stale = True
            if record.get('current_status') == 'open' and stale and record not in todo:
                todo.append(record)
    unchecked_before = sum(r.get('current_status') in (None, '', 'unverified', 'unchecked') for r in rows)
    counts = {'open': 0, 'closed': 0, 'not_found': 0, 'failed': 0, 'unchecked': 0}
    checked_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for index, record in enumerate(todo):
        try:
            result = check_himalayas_job(record.get('source_id'))
            code = result['http_status']
            status = {200: 'open', 410: 'closed', 404: 'not_found'}.get(code, 'failed')
            record['current_status'] = status
            record['status_verification'] = {
                'source': 'Himalayas documented job status API', 'http_status': code,
                'checked_at': checked_at,
            }
            # Refresh source dates and essential source fields only when the live status API returns them.
            job = result.get('job') or {}
            if job.get('expiryDate'):
                record['expires_at'] = _parse_source_date(job['expiryDate']) or record.get('expires_at')
        except Exception as exc:
            record['current_status'] = 'failed'
            record['status_verification'] = {
                'source': 'Himalayas documented job status API', 'checked_at': checked_at,
                'error': type(exc).__name__,
            }
        counts[record['current_status']] += 1
        if (index + 1) % args.batch_size == 0 and index + 1 < len(todo):
            sleep(60)
        elif index + 1 < len(todo):
            sleep(1.05)
    counts['unchecked'] = sum(r.get('current_status') in ('unverified', 'unchecked', None, '') for r in rows)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        handle = output_path.open('x', encoding='utf-8', newline='\n')
    else:
        handle = tempfile.NamedTemporaryFile(mode='x', encoding='utf-8', newline='\n',
            prefix='stagex_phase7_himalayas_status_', suffix='.jsonl', delete=False)
        output_path = Path(handle.name)
    with handle:
        for record in rows:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'input': str(input_path), 'output': str(output_path),
                      'checked_this_run': len(todo), 'previously_unchecked': unchecked_before,
                      'records': len(rows),
                      'new_status_results': counts, 'http_404': counts['not_found'],
                      'records_import_eligible_open': sum(r.get('current_status') == 'open' for r in rows)},
                     ensure_ascii=False, indent=2))


def _parse_source_date(value):
    from backend.collectors.schema import parse_date
    return parse_date(value)


if __name__ == '__main__':
    main()
