"""One bounded Wadifa Info public recruitment snapshot to isolated JSONL."""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

URL = 'https://www.wadifa-info.com/api/v1/concours'
ATTRIBUTION = 'Source: Wadifa Info'
LICENSE = 'CC BY 4.0'


def main():
    response = requests.get(URL, params={'limit': 20}, timeout=30,
                            headers={'Accept': 'application/json',
                                     'User-Agent': 'StageX-Marrakech-phase7-review/1.0'})
    print(f'HTTP {response.status_code} {response.url}')
    response.raise_for_status()
    payload = response.json()
    rows = payload.get('items') if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError('Unexpected Wadifa Info payload: items list missing')
    captured = datetime.now(timezone.utc).isoformat(timespec='seconds')
    normalized = []
    rejected = []
    for item in rows:
        if not isinstance(item, dict) or not item.get('grade') or not item.get('url'):
            rejected.append({'reason': 'missing title or source URL'})
            continue
        official_notice = item.get('official_notice')
        if official_notice:
            notice_url = urlsplit(str(official_notice))
            if notice_url.scheme != 'https' or notice_url.hostname != 'www.emploi-public.ma':
                rejected.append({'reason': 'official notice outside verified host', 'url': item.get('url')})
                continue
        normalized.append({
            'record_type': 'public_sector_recruitment_competition',
            'source': 'Wadifa Info', 'license': LICENSE, 'attribution': ATTRIBUTION,
            'source_id': item.get('id'), 'title': item.get('grade'),
            'employer': item.get('employer'), 'number_of_posts': item.get('posts'),
            'published_at': item.get('published'), 'deadline': item.get('deadline'),
            'deadline_status': 'deadline_not_passed' if item.get('deadline') else 'unknown',
            'location_classification': 'unknown', 'country': 'MA', 'city': None,
            'source_url': item.get('url'), 'official_notice_url': official_notice,
            'source_status': 'unverified', 'captured_at': captured,
            'source_item': item,
        })
    out = Path(tempfile.gettempdir()) / f'stagex_phase7_wadifa_{datetime.now():%Y%m%d_%H%M%S}.jsonl'
    with out.open('x', encoding='utf-8', newline='\n') as handle:
        for row in normalized:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'output': str(out), 'returned': len(rows), 'staged': len(normalized),
                      'rejected': rejected}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
