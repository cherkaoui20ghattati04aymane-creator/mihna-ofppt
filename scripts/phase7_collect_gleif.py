"""Take a tiny GLEIF Morocco identity sample into isolated JSONL staging."""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

API = 'https://api.gleif.org/api/v1/lei-records'
ATTRIBUTION = 'GLEIF LEI reference data'
TERMS_URL = 'https://www.gleif.org/en/lei-data/access-and-use-lei-data'


def main():
    response = requests.get(API, params={
        'filter[entity.legalAddress.country]': 'MA', 'page[size]': 3,
    }, timeout=30, headers={'Accept': 'application/vnd.api+json',
                            'User-Agent': 'StageX-Marrakech-phase7-review/1.0'})
    print(f'HTTP {response.status_code} {response.url}')
    response.raise_for_status()
    payload = response.json()
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    staged, rejected = [], []
    for row in payload.get('data', []):
        attrs = row.get('attributes') or {}
        entity = attrs.get('entity') or {}
        registration = attrs.get('registration') or {}
        category = (entity.get('category') or '').upper()
        state = (entity.get('status') or '').upper()
        registration_state = (registration.get('status') or '').upper()
        legal_address = entity.get('legalAddress') or {}
        legal_name = (entity.get('legalName') or {}).get('name')
        if category != 'GENERAL' or not legal_name or legal_address.get('country') != 'MA':
            rejected.append({'lei': row.get('id'), 'reason': 'not a verified Moroccan general legal entity'})
            continue
        staged.append({
            'record_type': 'company_identity_only', 'lei': row.get('id'),
            'legal_name': legal_name,
            'registered_city': legal_address.get('city'),
            'registered_country': legal_address.get('country'),
            'registered_address': legal_address.get('addressLines'),
            'postal_code': legal_address.get('postalCode'),
            'entity_status': state, 'registration_status': registration_state,
            'registered_status_current': state == 'ACTIVE' and registration_state == 'ISSUED',
            'company_website': None, 'logo_url': None, 'sector': None,
            'public_careers_page': None,
            'source': 'GLEIF', 'source_url': f'https://api.gleif.org/api/v1/lei-records/{row.get("id")}',
            'attribution': ATTRIBUTION, 'license': 'CC0 1.0', 'terms_url': TERMS_URL,
            'captured_at': stamp,
            'not_hiring_evidence': True,
        })
    out = Path(tempfile.gettempdir()) / f'stagex_phase7_gleif_{datetime.now():%Y%m%d_%H%M%S}.jsonl'
    with out.open('x', encoding='utf-8', newline='\n') as handle:
        for row in staged:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'output': str(out), 'returned': len(payload.get('data', [])),
                      'staged': len(staged), 'rejected': rejected,
                      'golden_copy': (payload.get('meta') or {}).get('goldenCopy')},
                     ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
