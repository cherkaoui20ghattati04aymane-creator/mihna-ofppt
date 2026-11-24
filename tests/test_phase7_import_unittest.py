"""Dependency-light isolated tests for the Phase 7 import safety path."""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from backend.api import _enrich_offer
from backend.collectors.phase7_import import apply_import, backup_and_verify, preview_import
from backend.db import migrate, migrate_phase5, migrate_phase7, migrate_phase9, migrate_phase10, migrate_phase11


class Phase7ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stagex-phase7-test-')
        self.root = Path(self.temp.name)
        self.db_path = self.root / 'private.db'
        with closing(sqlite3.connect(self.db_path)) as db:
            db.executescript('''
                CREATE TABLE entreprises (Nom TEXT, Adresse TEXT, "Téléphone" TEXT,
                  "Site Web" TEXT, "Google Maps" TEXT, Emails TEXT, Secteur TEXT);
                CREATE TABLE offres (ID INTEGER, Titre TEXT, Description TEXT, "Type contrat" TEXT,
                  "Type stage" TEXT, "Entreprise ID" INTEGER, "Date publication" TEXT,
                  "Date expiration" TEXT, "Lien annonce" TEXT, "Lien public" TEXT);
                CREATE TABLE candidatures (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT,
                  secteur TEXT, email TEXT, telephone TEXT, date_candidature TEXT, statut TEXT, commentaire TEXT);
            ''')
            db.execute('INSERT INTO entreprises(Nom) VALUES (?)', ('Acme Maroc',))
            db.execute('INSERT INTO offres(ID,Titre) VALUES (?,?)', (1, 'Existing record'))
            for n in range(5):
                db.execute('INSERT INTO candidatures(nom_entreprise,statut) VALUES (?,?)', (f'Candidate {n}', 'Envoyée'))
            db.commit()
        backup_dir = self.root/'backups'
        migrate(self.db_path,backup_dir)
        migrate_phase5(self.db_path,backup_dir)
        migrate_phase7(self.db_path,backup_dir)
        migrate_phase9(self.db_path,backup_dir)
        migrate_phase10(self.db_path,backup_dir)
        migrate_phase11(self.db_path,backup_dir)
        self.stage = self.root / 'source.jsonl'
        self.record = {
            'source':'Himalayas','source_id':'https://himalayas.app/companies/acme/jobs/intern-1',
            'url':'https://himalayas.app/companies/acme/jobs/intern-1',
            'apply_url':'https://himalayas.app/companies/acme/jobs/intern-1?utm_source=api',
            'title':'Data Intern','company':'Acme Maroc','description':'Remote internship for Morocco.',
            'source_employment_type':'Intern','source_seniority':['Entry-level'],
            'published_at':'2026-11-20T00:00:00+00:00','expires_at':'2026-12-01T00:00:00+00:00',
            'current_status':'open','status_verification':{'http_status':200,'checked_at':'2026-11-23T06:00:00+00:00'},
            'attribution':'Source : Himalayas','location_classification':'remote_morocco_eligible',
            'location_eligibility':'Morocco','eligibility_basis':'explicit country restriction',
            'source_location_restrictions':['Morocco'],'captured_at':'2026-11-23T06:00:00+00:00',
        }
        self.stage.write_text(json.dumps(self.record)+'\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_preview_backup_import_metadata_and_idempotency(self):
        preview, _ = preview_import(self.db_path, self.stage)
        self.assertEqual(1, preview['eligible_validated_open_records'])
        self.assertEqual([], preview['import_blockers'])
        self.assertEqual([], preview['rejected'])
        backup = backup_and_verify(self.db_path, self.root/'backups')
        self.assertEqual('ok', backup['integrity'])
        final, _ = preview_import(self.db_path, self.stage)
        result = apply_import(self.db_path, self.root/'backups', self.stage, final['database_sha256'])
        self.assertEqual(1, result['imported'])
        with closing(sqlite3.connect(self.db_path)) as db:
            db.row_factory = sqlite3.Row
            offer = dict(db.execute('SELECT * FROM offres WHERE source="Himalayas"').fetchone())
            self.assertIsNone(offer['Entreprise ID'])
            self.assertEqual(0, offer['relation_verified'])
            self.assertEqual(5, db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0])
            self.assertEqual('ok', db.execute('PRAGMA integrity_check').fetchone()[0])
            with closing(sqlite3.connect(backup['path'])) as backup_db:
                self.assertEqual(1, backup_db.execute('SELECT COUNT(*) FROM offres').fetchone()[0])
            db.commit()
        enriched = _enrich_offer(offer)
        self.assertEqual(self.record['apply_url'], enriched['application_url'])
        self.assertEqual(self.record['url'], enriched['source_original_url'])
        self.assertEqual('Source : Himalayas', enriched['source_attribution'])
        self.assertEqual('À distance · Maroc explicitement éligible', enriched['source_location_label'])
        second, _ = preview_import(self.db_path, self.stage)
        self.assertEqual(1, len(second['existing_source_identity_conflicts']))
        with self.assertRaisesRegex(RuntimeError, 'blockers'):
            apply_import(self.db_path, self.root/'backups', self.stage, second['database_sha256'])

    def test_unverified_record_is_rejected(self):
        self.record['current_status'] = 'failed'
        self.stage.write_text(json.dumps(self.record)+'\n', encoding='utf-8')
        preview, _ = preview_import(self.db_path, self.stage)
        self.assertEqual(0, preview['eligible_validated_open_records'])
        self.assertTrue(any('status not verified open' in reason for row in preview['rejected'] for reason in row['reasons']))


if __name__ == '__main__':
    unittest.main()
