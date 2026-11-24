"""Phase 11.5 regressions for multilingual identity and verified source synchronization."""
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.collectors.gleif import search
from backend.collectors.jobicy import normalize, sync
from backend.collectors.schema import canonical_url, fingerprint
from backend.db import connect


def test_arabic_fingerprints_and_job_query_identifiers():
    assert fingerprint({'title':'مهندس البرمجيات'}) != fingerprint({'title':'مدير المالية'})
    assert canonical_url('https://example.com/job?id=4&utm_source=x') == 'https://example.com/job?id=4'
    assert canonical_url('https://example.com/job?id=4') != canonical_url('https://example.com/job?id=5')


def test_jobicy_sync_preserves_history_and_uses_only_verified_open_jobs(app, client, tmp_path):
    database = Path(app.config['DATABASE'])
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    data = {'id':7,'jobGeo':'Anywhere','url':'https://jobicy.com/jobs/7-stage',
            'jobTitle':'تدريب برمجة','companyName':'Company fixture','pubDate':stamp}
    item = normalize(data)
    assert item['city'] == '' and item['expires_at'] is None
    assert normalize({**data,'jobGeo':'Europe'}) is None
    assert sync(database,[],tmp_path/'snapshots',{'7':item},{'7':'unknown'},stamp)['new'] == 0
    assert sync(database,[],tmp_path/'snapshots',{'7':item},{'7':'active'},stamp)['new'] == 1
    assert sync(database,[],tmp_path/'snapshots',{'7':item},{'7':'active'},stamp)['new'] == 0
    results = client.get('/api/offres').get_json()
    assert any(x['source']=='Jobicy' and x['location_group']=='remote_worldwide_eligible' for x in results)
    assert sync(database,[],tmp_path/'snapshots',{}, {'7':'closed'},stamp)['closed'] == 1
    assert not any(x['source']=='Jobicy' for x in client.get('/api/offres').get_json())
    with connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM offres WHERE source='Jobicy'").fetchone()[0] == 1


def test_gleif_snapshot_search_keeps_legal_identity_separate(tmp_path):
    cache = tmp_path/'legal.json'
    cache.write_text(json.dumps({'captured_at':'2026-11-24', 'records':[
        {'name':'Société de Démonstration','lei':'TEST','registered_city':'Fès'}
    ]}), encoding='utf8')
    assert search(cache,'societe fes')['total'] == 1
    assert search(cache,'Casablanca')['items'] == []

def test_location_and_contract_use_structured_evidence():
    from backend.collectors.classification import classify_offer, filter_offer
    remote = {'Titre':'CDI développeur', 'ville':'مراكش',
              'source_metadata':{'location_classification':'remote_worldwide_eligible'}}
    assert classify_offer(remote)['opportunity_type'] == 'cdi'
    assert not filter_offer(remote,location='Marrakech')
    assert filter_offer({'ville':'طنجة'},location='Tanger')
    assert classify_offer({'Titre':'Stage d’été en ingénierie'})['opportunity_type']=='summer_internship'

def test_jobicy_access_and_quota_errors_stop_discovery():
    from types import SimpleNamespace
    import pytest
    from backend.collectors.jobicy import SourcePaused, discover

    for status in (401,403,429):
        calls=[]
        def reject(*args,**kwargs):
            calls.append(args)
            return SimpleNamespace(status_code=status)
        with pytest.raises(SourcePaused, match=str(status)):
            discover(SimpleNamespace(get=reject))
        assert len(calls)==1
