import unittest

from backend.collectors.free_apis import (parse_himalayas_payload, fetch_himalayas,
                                          deduplicate_records, check_himalayas_job)


def job(**changes):
    value = {
        'guid': 'https://himalayas.app/companies/example/jobs/analyst',
        'applicationLink': 'https://himalayas.app/companies/example/jobs/analyst?utm_source=api',
        'title': 'Analyst - Marrakech',
        'companyName': 'Example SARL',
        'description': '<p>Remote role for Morocco.</p>',
        'excerpt': 'Remote role',
        'locationRestrictions': ['Morocco'],
        'categories': ['Finance'],
        'employmentType': 'Full Time',
        'pubDate': 1795107128,
        'expiryDate': 1799275137,
    }
    value.update(changes)
    return value


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
        import json
        self.content = json.dumps(payload).encode()

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Session:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.payloads.pop(0))


class HimalayasConnectorTests(unittest.TestCase):
    def test_normalizes_source_urls_dates_and_country_eligibility(self):
        metrics = {}
        items = parse_himalayas_payload({'jobs': [job()]}, query='Marrakech', metrics=metrics,
                                        captured_at='2026-11-23T12:00:00+00:00')
        self.assertEqual(1, len(items))
        item = items[0]
        self.assertEqual('Himalayas', item['source'])
        self.assertEqual('Example SARL', item['company'])
        self.assertEqual('https://himalayas.app/companies/example/jobs/analyst', item['job_url'])
        self.assertIn('utm_source=api', item['apply_url'])
        self.assertEqual('remote_morocco_eligible', item['location_classification'])
        self.assertFalse(item['city_verified'])
        self.assertEqual('Marrakech', item['query_location_hint'])
        self.assertTrue(item['published_at'])
        self.assertTrue(item['expires_at'])
        self.assertEqual(1, metrics['valid_count'])

    def test_rejects_unknown_country_eligibility_and_unsafe_links(self):
        metrics = {}
        items = parse_himalayas_payload({'jobs': [
            job(locationRestrictions=['Spain']),
            job(guid='http://himalayas.app/companies/example/jobs/analyst'),
        ]}, metrics=metrics)
        self.assertEqual([], items)
        self.assertEqual(2, metrics['rejected_count'])

    def test_recognizes_documented_worldwide_and_country_object_restrictions(self):
        items = parse_himalayas_payload({'jobs': [
            job(guid='https://himalayas.app/companies/example/jobs/worldwide',
                applicationLink='https://himalayas.app/companies/example/jobs/worldwide?utm_source=api',
                locationRestrictions=[]),
            job(guid='https://himalayas.app/companies/example/jobs/morocco',
                applicationLink='https://himalayas.app/companies/example/jobs/morocco?utm_source=api',
                locationRestrictions=[{'alpha2': 'MA', 'name': 'Morocco', 'slug': 'morocco'}]),
        ]})
        self.assertEqual(2, len(items))
        self.assertEqual('remote_worldwide_eligible', items[0]['location_classification'])
        self.assertEqual('remote_morocco_eligible', items[1]['location_classification'])

    def test_fetch_requires_a_filter_and_respects_one_page_cap(self):
        with self.assertRaises(ValueError):
            fetch_himalayas('', '', session=Session([]))
        with self.assertRaises(ValueError):
            fetch_himalayas('Marrakech', 'Morocco', 6, session=Session([]))

    def test_fetch_uses_documented_query(self):
        session = Session([{'jobs': [job()], 'totalCount': 1, 'limit': 20}])
        metrics = {}
        items = fetch_himalayas('Marrakech', 'MA', 1, session=session,
                                metrics=metrics, pause_seconds=0)
        self.assertEqual(1, len(items))
        self.assertEqual(1, metrics['request_count'])
        self.assertEqual('https://himalayas.app/jobs/api/search', session.calls[0][0])
        self.assertEqual({'q': 'Marrakech', 'country': 'MA', 'page': 1},
                         session.calls[0][1]['params'])

    def test_pagination_stays_bounded_and_deduplication_uses_source_identity(self):
        first = job(guid='https://himalayas.app/companies/example/jobs/one',
                    applicationLink='https://himalayas.app/companies/example/jobs/one?utm_source=api')
        second = job(guid='https://himalayas.app/companies/example/jobs/two',
                     applicationLink='https://himalayas.app/companies/example/jobs/two?utm_source=api')
        session = Session([
            {'jobs': [first], 'totalCount': 21, 'limit': 20},
            {'jobs': [second], 'totalCount': 21, 'limit': 20},
        ])
        metrics = {}
        items = fetch_himalayas('Marrakech', 'MA', 2, session=session,
                                metrics=metrics, pause_seconds=0)
        self.assertEqual(2, len(items))
        self.assertEqual(2, metrics['request_count'])
        self.assertEqual(2, metrics['pages'])
        self.assertEqual(2, session.calls[1][1]['params']['page'])
        unique, duplicate_count = deduplicate_records(items + [items[0]])
        self.assertEqual(2, len(unique))
        self.assertEqual(1, duplicate_count)

    def test_status_endpoint_preserves_open_closed_and_not_found_http_states(self):
        class StatusSession:
            def __init__(self, status): self.status=status
            def get(self, *args, **kwargs): return Response({'job':{'title':'Listing'}} if self.status==200 else {},self.status)
        url='https://himalayas.app/companies/example/jobs/role'
        self.assertEqual(200,check_himalayas_job(url,session=StatusSession(200))['http_status'])
        self.assertEqual(410,check_himalayas_job(url,session=StatusSession(410))['http_status'])
        self.assertEqual(404,check_himalayas_job(url,session=StatusSession(404))['http_status'])


if __name__ == '__main__':
    unittest.main()
