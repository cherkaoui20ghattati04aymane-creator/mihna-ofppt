"""Preview or explicitly apply the validated Phase 7 Himalayas import."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.collectors.phase7_import import apply_import, backup_and_verify, preview_import
from backend.db import migrate_phase11

DEFAULT_DB = ROOT / 'database' / 'stages_marrakech.db'
DEFAULT_INPUT = Path('himalayas_status.jsonl')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=str(DEFAULT_DB))
    parser.add_argument('--input', default=str(DEFAULT_INPUT))
    parser.add_argument('--backup-dir', default=str(ROOT / 'backups'))
    parser.add_argument('--apply', action='store_true', help='backup, verify, migrate additively, and import')
    args = parser.parse_args()
    report, _ = preview_import(args.database, args.input)
    print('PREVIEW\n' + json.dumps(report, ensure_ascii=False, indent=2))
    if not args.apply:
        return
    if report['import_blockers'] or report['rejected']:
        raise SystemExit('Import refused: preview contains blockers.')
    backup = backup_and_verify(args.database, args.backup_dir)
    print('VERIFIED BACKUP\n' + json.dumps(backup, ensure_ascii=False, indent=2))
    migrate_phase11(args.database, args.backup_dir)
    final_preview, _ = preview_import(args.database, args.input)
    if final_preview['import_blockers'] or final_preview['rejected']:
        raise SystemExit('Import refused after additive migration; backup is available.')
    result = apply_import(args.database, args.backup_dir, args.input,
                          expected_sha256=final_preview['database_sha256'])
    print('IMPORT\n' + json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
