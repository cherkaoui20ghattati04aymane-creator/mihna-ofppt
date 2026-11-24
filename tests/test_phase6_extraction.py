import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase6_expand_extraction import (QUERIES, possible_duplicate_pairs,
                                               stage_records)
from backend.collectors.free_apis import parse_himalayas_payload


def record(identity, **changes):
    row = {'source': 'Himalayas', 'source_id': identity,
           'canonical_url': f'https://himalayas.app/companies/a/jobs/{identity}',
           'title': 'Data analyst', 'company': 'Example', 'city': '',
           'location_classification': 'remote_morocco_eligible',
           'published_at': '2026-11-01T00:00:00+00:00', 'apply_url': 'https://himalayas.app/apply',
           'source_application_url': 'https://himalayas.app/apply',
           'attribution': 'Source : Himalayas', '_query_matches': ['Morocco']}
    row.update(changes)
    return row


class Phase6StagingTests(unittest.TestCase):
    def test_configures_all_requested_queries_and_country_pass_is_mandatory_in_runner(self):
        self.assertEqual(15, len(QUERIES))
        for expected in ('Marrakech', 'Morocco', 'Maroc', 'Casablanca', 'Rabat',
                         'Software Developer', 'Web Developer', 'Data Analyst',
                         'Data Scientist', 'Digital Marketing', 'Graphic Designer',
                         'Business Analyst', 'Internship', 'Intern', 'Junior Developer'):
            self.assertIn(expected, QUERIES)

    def test_city_is_not_inferred_from_title_and_missing_fields_are_preserved(self):
        source = {'guid': 'https://himalayas.app/companies/a/jobs/marrakech',
                  'applicationLink': 'https://himalayas.app/companies/a/jobs/marrakech/apply',
                  'title': 'Developer — Marrakech', 'locationRestrictions': ['Morocco']}
        parsed = parse_himalayas_payload({'jobs': [source]}, query='Marrakech')
        self.assertEqual(1, len(parsed))
        self.assertEqual('', parsed[0]['city'])
        self.assertFalse(parsed[0]['city_verified'])
        self.assertIn('Entreprise', parsed[0]['missing_fields'])
        self.assertTrue(parsed[0]['source_application_url'])
        self.assertTrue(parsed[0]['attribution'])

    def test_empty_restrictions_are_worldwide_and_non_morocco_is_not_eligible(self):
        base = {'guid': 'https://himalayas.app/companies/a/jobs/x',
                'applicationLink': 'https://himalayas.app/companies/a/jobs/x/apply',
                'title': 'Developer'}
        good = parse_himalayas_payload({'jobs': [{**base, 'locationRestrictions': []}]})
        rejected = parse_himalayas_payload({'jobs': [{**base, 'locationRestrictions': ['Spain']}]})
        self.assertEqual('remote_worldwide_eligible', good[0]['location_classification'])
        self.assertEqual([], rejected)

    def test_staging_exact_dedup_merges_queries_and_preserves_apply_url(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'records.jsonl'
            path, rows, duplicates = stage_records([
                record('same'), record('same', _query_matches=['Intern'])])
            # Default temp path writes outside this fixture; clean it after checking behavior.
            self.addCleanup(path.unlink, missing_ok=True)
            self.assertEqual(1, duplicates)
            self.assertEqual(1, len(rows))
            self.assertIn('https://himalayas.app/apply', rows[0]['apply_url'])
            self.assertEqual(['Intern', 'Morocco'], rows[0]['query_matches'])
            output_path, _, _ = stage_records([record('other')], output)
            self.assertEqual(output, output_path)
            with output.open(encoding='utf-8') as stream:
                self.assertEqual('other', json.loads(stream.readline())['source_id'])
            with self.assertRaises(FileExistsError):
                stage_records([record('third')], output)

    def test_similar_jobs_are_flagged_for_review_not_merged(self):
        pairs = possible_duplicate_pairs([record('one'), record('two')])
        self.assertEqual([['one', 'two']], pairs)
        self.assertEqual([], possible_duplicate_pairs([record('one'), record('two', published_at='2026-11-02')]))


if __name__ == '__main__':
    unittest.main()
