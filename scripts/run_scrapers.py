"""Collecte planifiable Jawb.ma / Wadifa.info vers le staging (jamais d'import automatique).

Usage :
    .venv\\Scripts\\python.exe scripts\\run_scrapers.py --source jawb
    .venv\\Scripts\\python.exe scripts\\run_scrapers.py --source all

Le connecteur doit avoir été autorisé dans l'application (référence d'autorisation écrite et
trois droits confirmés). Les résultats attendent votre revue dans le Centre de collecte.
Journal : logs/scrapers.log (sans contenu d'annonce ni donnée personnelle).
"""
import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['jawb', 'wadifa', 'all'], required=True)
    args = parser.parse_args(argv)
    from backend.config import settings
    from backend.db import migrate, migrate_phase5, migrate_phase7, migrate_phase9, migrate_phase10
    from backend.scrapers import pipeline
    cfg = settings()
    (ROOT / 'logs').mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / 'logs' / 'scrapers.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    for step in (migrate, migrate_phase5, migrate_phase7, migrate_phase9, migrate_phase10):
        step(cfg['DATABASE'], cfg['BACKUP_DIR'])
    sources = ['jawb', 'wadifa'] if args.source == 'all' else [args.source]
    code = 0
    for source in sources:
        try:
            result = pipeline.run(cfg['DATABASE'], source)
        except Exception as exc:  # noqa: BLE001 - message lisible pour la planification
            result, code = {'source': source, 'status': 'blocked', 'error': str(exc)}, 2
        if result.get('status') == 'failed':
            code = max(code, 1)
        print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
