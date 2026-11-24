"""Phase 11: saved offers, skills gap, CV quality, roadmap, analytics, company insights,
interview history, dashboard, exports, Gemini feature gating and migration v11.

All Gemini calls use simulated clients: they prove the code paths, not Google's service.
"""
import json
import sqlite3
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

CV = {'name': 'Profil Test', 'title': 'Étudiant développeur', 'email': 'demo@example.test', 'city': 'Marrakech',
      'summary': 'Étudiant en développement, je réalise des projets web avec Python et SQL. Je cherche un stage pour progresser.',
      'technical': 'Python, SQL, Git, JavaScript', 'languages': 'Français, anglais',
      'education': [{'title': 'Technicien spécialisé en développement', 'organization': 'Institut fictif', 'period': '2025 - 2026',
                     'description': 'Programmation, bases de données.'}],
      'projects': [{'title': 'Application de suivi', 'period': '2026',
                    'description': 'Développé une application Flask avec Python et SQL pour suivre des tâches pédagogiques.'}]}


@pytest.fixture
def saved_cv(client):
    r = client.post('/api/cvs', json={'name': 'CV principal', 'template': 'modern', 'data': CV})
    assert r.status_code == 201
    return r.json['id']


# ---------------------------------------------------------------- G. Saved opportunities
def test_saved_offers_add_list_duplicate_remove(client):
    first = client.post('/api/saved-offers', json={'offer_id': 1})
    again = client.post('/api/saved-offers', json={'offer_id': 1})
    assert first.status_code == 201 and again.status_code == 200 and again.json['duplicate'] is True
    listed = client.get('/api/saved-offers').json['items']
    assert len(listed) == 1 and listed[0]['offer']['Titre'] == 'Stage Python'
    assert client.get('/api/saved-offers/ids').json['ids'] == [1]
    assert client.post('/api/saved-offers', json={'offer_id': 999}).status_code == 404
    assert client.delete('/api/saved-offers/1').status_code == 200
    assert client.delete('/api/saved-offers/1').status_code == 404
    assert client.get('/api/saved-offers').json['items'] == []


# ---------------------------------------------------------------- A. Skills gap
def test_skills_gap_separates_present_missing_and_never_claims_missing(client, saved_cv):
    gap = client.post('/api/skills-gap', json={'cv_id': saved_cv, 'offer_id': 3}).json  # Java SQL offer
    assert 'sql' in gap['present'] and 'java' in gap['missing']
    assert set(gap['present']).isdisjoint(gap['missing'])
    assert gap['coverage'] == 50 and gap['mode'] == 'local'
    assert any('java' in r for r in gap['recommendations'])
    stored = client.get(f'/api/cvs/{saved_cv}').json['data']
    assert 'java' not in stored['technical'].lower().split(', ')


def test_skills_gap_related_skills_and_requirements():
    from backend.career_features import skills_gap
    offer = {'ID': 9, 'Titre': 'Développeur React', 'Description': 'Vous maîtrisez React et TypeScript. 2 ans d’expérience. '
             'Diplôme Bac+3 en informatique. Certification AWS appréciée.'}
    gap = skills_gap(CV, offer)
    assert {'react', 'typescript'} <= set(gap['missing'])
    assert any(r['missing'] == 'typescript' and 'javascript' in r['you_have'] for r in gap['related'])
    assert gap['years_mentioned'] == 2 and gap['education_requirements'] and gap['certification_requirements']


# ---------------------------------------------------------------- E. CV quality
def test_cv_quality_is_transparent_and_excludes_job_criterion_without_offer(client, saved_cv):
    plain = client.post('/api/cv-quality', json={'cv_id': saved_cv}).json
    assert 0 <= plain['score'] <= 100 and plain['possible'] == 90
    job = next(c for c in plain['criteria'] if c['key'] == 'job')
    assert job['evaluated'] is False and job['points'] is None
    assert sum(c['max'] for c in plain['criteria']) == 100
    assert 'ATS' in plain['disclaimer']
    targeted = client.post('/api/cv-quality', json={'cv_id': saved_cv, 'offer_id': 1}).json
    assert targeted['possible'] == 100
    empty = client.post('/api/cv-quality', json={'cv': {'name': '', 'title': ''}}).json
    assert empty['score'] < plain['score']


# ---------------------------------------------------------------- B. Roadmap
def test_roadmap_uses_saved_offers_and_only_learning_steps_can_be_declared(client, saved_cv):
    client.post('/api/saved-offers', json={'offer_id': 3})
    roadmap = client.get('/api/roadmap').json
    assert roadmap['targets_from'] == 'offres sauvegardées'
    assert any(s['skill'] == 'java' for s in roadmap['skills_to_develop'])
    cv_step = next(s for s in roadmap['steps'] if s['id'] == 'cv')
    assert cv_step['done'] is True and cv_step['kind'] == 'auto'
    refused = client.put('/api/roadmap', json={'step': 'apply', 'done': True})
    assert refused.status_code == 400
    updated = client.put('/api/roadmap', json={'step': 'learn:java', 'done': True, 'objective': 'Développeur backend'}).json
    assert next(s for s in updated['steps'] if s['id'] == 'learn:java')['done'] is True
    assert updated['objective'] == 'Développeur backend'
    profile = client.get('/api/profile').json['profile']
    assert 'java' not in [s.lower() for s in profile['skills']]


# ---------------------------------------------------------------- C. Application analytics
def test_application_analytics_are_computed_from_records(client, saved_cv):
    base = client.get('/api/analytics/applications').json
    assert base['total'] == 5  # the five historical rows of the fixture
    applied = client.post('/api/offres/1/apply', json={'cv_id': saved_cv, 'action': 'prepare', 'confirmed': True, 'message': 'x'})
    assert applied.status_code == 201
    ident = applied.json['id']
    client.patch(f'/api/candidatures/{ident}', json={'statut': 'Envoyée'})
    client.patch(f'/api/candidatures/{ident}', json={'statut': 'Entretien'})
    data = client.get('/api/analytics/applications').json
    assert data['total'] == 6 and data['interviews'] >= 1
    assert next(s for s in data['by_status'] if s['status'] == 'Entretien')['count'] == 1
    assert data['matching_scores']['count'] == 1 and data['matching_scores']['items'][0]['application_id'] == ident
    assert data['conversion']['interview_rate'] is not None and 'definitions' in data
    csv_text = client.get('/api/candidatures/export.csv').data.decode('utf-8-sig')
    assert csv_text.splitlines()[0].startswith('id;entreprise') and len(csv_text.splitlines()) == 7


# ---------------------------------------------------------------- D. Company insights
def test_company_insights_show_only_stored_facts(client):
    overview = client.get('/api/companies/overview').json
    assert overview['total'] == 2 and overview['with_website'] == 1
    insight = client.get('/api/companies/1/insights').json
    assert insight['name'] == 'L’Agence d\'essai' and insight['website_status'].startswith('renseigné')
    assert insight['coordinates_verified'] is False and 'Effectif' in insight['not_available']
    for forbidden in ('employees', 'revenue', 'rating'):
        assert forbidden not in json.dumps(insight)
    assert client.get('/api/companies/999/insights').status_code == 404


# ---------------------------------------------------------------- F. Interview history
def test_interview_history_reopen_assessment_and_delete(client, saved_cv):
    saved = client.post('/api/career/interviews', json={'cv_id': saved_cv, 'offer_id': 1,
        'answers': [{'question': 'Présentez un projet', 'answer': 'Dans mon projet de formation, la situation était un suivi de tâches. '
                     'Mon action a été de développer une application Flask ; le résultat est un outil utilisé par ma classe pendant deux mois '
                     'et documenté avec soin pour les autres étudiants.'},
                    {'question': 'Pourquoi ce stage ?', 'answer': ''}],
        'feedback': {'answer_feedback': [], 'note': 'Retour local'}})
    assert saved.status_code == 201
    summary = client.get('/api/career/interviews-summary').json['items']
    assert summary[0]['offer_title'] == 'Stage Python' and summary[0]['cv_name'] == 'CV principal'
    detail = client.get('/api/career/interviews/' + saved.json['id']).json
    assert detail['answers'][0]['question'] == 'Présentez un projet'
    assert detail['assessment']['answered'] == 1 and detail['assessment']['completeness'] == 50
    assert detail['assessment']['recommendations']
    assert client.delete('/api/career/interviews/' + saved.json['id']).status_code == 200
    assert client.get('/api/career/interviews/' + saved.json['id']).status_code == 404


# ---------------------------------------------------------------- Dashboard and export
def test_dashboard_summary_and_personal_export(client, saved_cv):
    client.post('/api/saved-offers', json={'offer_id': 2})
    client.post('/api/skills-gap', json={'cv_id': saved_cv, 'offer_id': 1})
    dash = client.get('/api/dashboard').json
    assert dash['cvs']['original'] == 1 and dash['saved']['count'] == 1
    assert dash['matching']['last_30_days'].get('skills_gap') == 1
    assert any(e['kind'] == 'saved' for e in dash['activity'])
    exported = json.loads(client.get('/api/me/export').data)
    assert exported['cvs'][0]['name'] == 'CV principal' and exported['saved_offers'][0]['offer_id'] == 2


# ---------------------------------------------------------------- Gemini feature gating
def test_gemini_feature_unavailable_is_explicit(client, saved_cv):
    preview = client.post('/api/ai/feature/gap/preview', json={'cv_id': saved_cv, 'offer_id': 1}).json
    assert 'email' not in json.dumps(preview['payload']) and 'demo@example.test' not in json.dumps(preview['payload'])
    run = client.post('/api/ai/feature/gap', json={'cv_id': saved_cv, 'offer_id': 1, 'consent': True, 'digest': preview['digest']}).json
    assert run['mode'] == 'unavailable' and run['reasons']


@pytest.fixture
def gemini_app(legacy_database, tmp_path):
    from backend.web import create_app
    return create_app({'DATABASE': str(legacy_database), 'PRIVATE_DIR': str(tmp_path / 'private'),
                       'BACKUP_DIR': str(tmp_path / 'backups'), 'TESTING': True, 'SMTP_ENABLED': False,
                       'GEMINI_ENABLED': True, 'GEMINI_API_KEY': 'FAUSSE-CLE-DE-TEST-0123456789abcdef',
                       'GEMINI_FREE_TIER_CONFIRMED': True, 'GEMINI_MODEL': 'gemini-3.1-flash-lite', 'MAPS_ENABLED': False})


def _client(app):
    c = app.test_client()
    info = c.get('/api/auth/session').json
    r = c.post('/api/auth/setup', json={'password': 'Mot-de-passe-test-123!'}, headers={'X-CSRF-Token': info['csrf']})
    c.environ_base['HTTP_X_CSRF_TOKEN'] = r.json['csrf']
    return c


def _fake(monkeypatch, text):
    from backend.services import gemini_service as gs
    call = Mock(return_value=SimpleNamespace(text=text))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: SimpleNamespace(
        models=SimpleNamespace(generate_content=call), close=Mock()))
    return call


def test_gemini_feature_requires_consent_and_filters_invented_claims(gemini_app, monkeypatch):
    c = _client(gemini_app)
    cv_id = c.post('/api/cvs', json={'name': 'CV', 'template': 'modern', 'data': CV}).json['id']
    call = _fake(monkeypatch, json.dumps({'items': [
        'Mettez en avant votre projet Flask en Python dans le résumé.',
        'Vous maîtrisez déjà Java, ajoutez-le en tête.',          # claims a missing skill → rejected
        'Ajoutez Kubernetes à votre profil.',                      # skill unrelated to CV/offer → rejected
        'Apprenez les bases de Java par un petit projet.']}))
    preview = c.post('/api/ai/feature/gap/preview', json={'cv_id': cv_id, 'offer_id': 3}).json
    refused = c.post('/api/ai/feature/gap', json={'cv_id': cv_id, 'offer_id': 3, 'digest': preview['digest']})
    assert refused.status_code == 400 and call.call_count == 0
    result = c.post('/api/ai/feature/gap', json={'cv_id': cv_id, 'offer_id': 3, 'consent': True, 'digest': preview['digest']}).json
    assert result['mode'] == 'gemini' and result['rejected'] == 2
    assert result['items'] == ['Mettez en avant votre projet Flask en Python dans le résumé.',
                               'Apprenez les bases de Java par un petit projet.']
    assert 'FAUSSE-CLE' not in json.dumps(result)


def test_gemini_tailored_summary_accepts_only_source_passage_ids(gemini_app, monkeypatch):
    c = _client(gemini_app)
    cv_id = c.post('/api/cvs', json={'name': 'CV', 'template': 'modern', 'data': CV}).json['id']
    preview = c.post('/api/ai/feature/tailor_summary/preview', json={'cv_id': cv_id, 'offer_id': 3}).json
    body = {'cv_id': cv_id, 'offer_id': 3, 'consent': True, 'digest': preview['digest']}
    _fake(monkeypatch, json.dumps({'summary': 'Développeur Java avec 5 ans d’expérience.'}))
    assert c.post('/api/ai/feature/tailor_summary', json=body).json['mode'] == 'local_fallback'
    from backend.services.gemini_service import reset_state_for_tests
    reset_state_for_tests()  # the rejected answer is cached for 15 min (quota protection); clear it for the second scenario
    _fake(monkeypatch, json.dumps({'passages': [1]}))
    ok = c.post('/api/ai/feature/tailor_summary', json=body).json
    assert ok['mode'] == 'gemini' and ok['summary'] == preview['payload']['passages_cv']['1']


def test_gemini_quota_error_falls_back_to_local(gemini_app, monkeypatch):
    from backend.services import gemini_service as gs

    class Quota(Exception):
        code = 429
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: SimpleNamespace(
        models=SimpleNamespace(generate_content=Mock(side_effect=Quota('429 RESOURCE_EXHAUSTED'))), close=Mock()))
    c = _client(gemini_app)
    cv_id = c.post('/api/cvs', json={'name': 'CV', 'template': 'modern', 'data': CV}).json['id']
    preview = c.post('/api/ai/feature/quality/preview', json={'cv_id': cv_id}).json
    result = c.post('/api/ai/feature/quality', json={'cv_id': cv_id, 'consent': True, 'digest': preview['digest']}).json
    assert result['mode'] == 'local_fallback' and '429' in result['notice']


# ---------------------------------------------------------------- Isolation + migration
def test_phase11_records_are_isolated_between_accounts(legacy_database, tmp_path, monkeypatch):
    from backend.web import create_app
    root = tmp_path / 'private' / 'user_data'
    secret = 'test-internal-secret-' + 'y' * 50
    monkeypatch.setenv('AUTH_MULTI_USER_MODE', 'true')
    monkeypatch.setenv('AUTH_USER_DATA_ROOT', str(root))
    monkeypatch.setenv('AUTH_INTERNAL_SECRET', secret)
    app = create_app({'DATABASE': str(legacy_database), 'PRIVATE_DIR': str(tmp_path / 'private'),
                      'BACKUP_DIR': str(tmp_path / 'backups'), 'AUTH_USER_DATA_ROOT': str(root), 'TESTING': True, 'SMTP_ENABLED': False})
    c = app.test_client()
    csrf = c.post('/api/internal/gateway-session', json={}, headers={'X-Internal-Gateway-Secret': secret}).json['csrf']
    a, b = str(uuid.uuid4()), str(uuid.uuid4())

    def call(user, method, path, **kw):
        headers = {'X-Internal-User-ID': user, **({'X-CSRF-Token': csrf} if method != 'get' else {})}
        return getattr(c, method)(path, headers=headers, **kw)
    assert call(a, 'post', '/api/saved-offers', json={'offer_id': 1}).status_code == 201
    call(a, 'put', '/api/roadmap', json={'objective': 'Objectif privé A'})
    assert call(b, 'get', '/api/saved-offers').json['items'] == []
    assert call(b, 'get', '/api/roadmap').json['objective'] == ''
    assert call(b, 'get', '/api/dashboard').json['saved']['count'] == 0
    assert call(a, 'get', '/api/dashboard').json['saved']['count'] == 1


def test_migration_v11_is_additive_and_backed_up(tmp_path, legacy_database):
    from backend.db import migrate_all
    path = tmp_path / 'copy.db'
    path.write_bytes(legacy_database.read_bytes())
    migrate_all(path, tmp_path / 'b')
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO saved_offers(offer_id,created_at) VALUES (1,'2026-11-23')")
        before = {t: db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in ('offres', 'entreprises', 'candidatures')}
        assert db.execute('PRAGMA user_version').fetchone()[0] == 11
    migrate_all(path, tmp_path / 'b')  # idempotent
    with sqlite3.connect(path) as db:
        assert {t: db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in before} == before
        assert db.execute('SELECT COUNT(*) FROM saved_offers').fetchone()[0] == 1
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert list((tmp_path / 'b').glob('avant_phase14_saved_roadmap_*.db'))
