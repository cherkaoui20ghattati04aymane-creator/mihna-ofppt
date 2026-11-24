"""Import a bounded GLEIF LEI reference snapshot. This catalog is separate from employers."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata

TERMS = 'https://www.gleif.org/en/meta/lei-data-terms-of-use/'
ENDPOINT = 'https://api.gleif.org/api/v1/lei-records'


def normalize(payload):
    records = {}
    for row in payload['data']:
        ident = row.get('id','')
        attributes = row.get('attributes') or {}
        entity = attributes.get('entity') or {}
        address = entity.get('legalAddress') or {}
        name = (entity.get('legalName') or {}).get('name')
        if (not re.fullmatch('[A-Z0-9]{20}', ident) or address.get('country') != 'MA'
                or entity.get('category') != 'GENERAL' or not isinstance(name,str) or not name.strip()):
            continue
        records[ident] = {
            'lei':ident, 'name':name.strip(), 'registered_city':address.get('city') or None,
            'entity_status':entity.get('status'),
            'registration_status':(attributes.get('registration') or {}).get('status'),
            'source_url': ENDPOINT+'/'+ident,
        }
    return records


def _fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold())
                   if not unicodedata.combining(c))


def search(path, query):
    query = _fold(query.strip())
    if not 2 <= len(query) <= 100:
        raise ValueError('Saisissez entre 2 et 100 caractères.')
    if not path.is_file():
        raise LookupError('Référentiel GLEIF indisponible.')
    payload = json.loads(path.read_bytes())
    matches = [item for item in payload['records']
               if all(term in _fold(f"{item['name']} {item['lei']} {item['registered_city'] or ''}")
                      for term in query.split())]
    return {'items':matches[:25], 'total':len(matches),'captured_at':payload['captured_at'],
            'source':'GLEIF', 'license':'CC0 1.0','terms_url':TERMS}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_pages',nargs='+',type=Path)
    args=p.parse_args()
    records = {}
    for source in args.source_pages:
        records.update(normalize(json.loads(source.read_bytes())))
    if not records:
        raise ValueError('Empty GLEIF snapshot')
    output = Path('database/gleif_ma.json')
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps({
        'captured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source':ENDPOINT,'license':'CC0 1.0','terms_url':TERMS,
        'records':sorted(records.values(),key=lambda x:(x['name'].casefold(),x['lei']))
    }, ensure_ascii=False,indent=2)+'\n', encoding='utf8')
    temporary.replace(output)
    print(f'{len(records)} public Moroccan legal identities')
    

if __name__ == '__main__':
    main()
