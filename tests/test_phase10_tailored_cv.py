"""Phase 10 factual tailoring, persistence, and application selection tests."""
import sqlite3
import uuid


def test_tailoring_preview_preserves_source_and_never_inserts_missing_skills(client, cv_data):
    source = client.post('/api/cvs', json={'name': 'CV original', 'template': 'modern', 'data': cv_data})
    assert source.status_code == 201
    original = client.get('/api/cvs/'+str(source.json['id'])).json['data']
    preview = client.post('/api/cvs/tailored/preview', json={'cv_id': source.json['id'], 'offer_id': 1})
    assert preview.status_code == 200, preview.json
    data = preview.json['data']
    analysis = preview.json['analysis']
    assert preview.json['mode'] == 'local'
    assert set(analysis['missing_requirements']).isdisjoint(set(data['technical'].split(', ')))
    assert data['title'] == cv_data['title']
    assert client.get('/api/cvs/'+str(source.json['id'])).json['data'] == original


def test_tailored_draft_validation_pdf_application_and_multiple_versions(client, app, cv_data):
    source = client.post('/api/cvs', json={'name': 'CV original', 'template': 'modern', 'data': cv_data})
    assert source.status_code == 201
    preview = client.post('/api/cvs/tailored/preview', json={'cv_id': source.json['id'], 'offer_id': 1})
    assert preview.status_code == 200
    body = {'name': 'CV adapté · Stage Python', 'template': 'modern', 'source_cv_id': source.json['id'],
            'offer_id': 1, 'action': 'draft', 'data': preview.json['data']}
    created = client.post('/api/cvs/tailored', json=body)
    assert created.status_code == 201, created.json
    ident = created.json['id']
    assert created.json['cv_status'] == 'draft'
    assert client.get('/api/cvs/'+str(ident)+'/pdf').status_code == 400
    assert ident not in [cv['id'] for cv in client.get('/api/offres/1/application').json['cvs']]

    saved = client.patch('/api/cvs/'+str(ident)+'/tailored', json={**body, 'action': 'validate'})
    assert saved.status_code == 200, saved.json
    assert saved.json['cv_status'] == 'validated'
    assert client.get('/api/cvs/'+str(ident)+'/pdf').data.startswith(b'%PDF-')
    assert ident in [cv['id'] for cv in client.get('/api/offres/1/application').json['cvs']]

    another = client.post('/api/cvs/tailored', json={**body, 'name': 'Deuxième version', 'action': 'validate'})
    assert another.status_code == 201 and another.json['id'] != ident
    assert len(client.get('/api/cvs/tailored').json) == 2
    assert client.delete('/api/cvs/'+str(source.json['id'])).status_code == 400

    applied = client.post('/api/offres/1/apply', json={'cv_id': ident, 'action': 'prepare', 'confirmed': True,
                                                        'message': 'Candidature préparée avec la version choisie.'})
    assert applied.status_code == 201, applied.json
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT cv_id FROM candidatures WHERE id=?', (applied.json['id'],)).fetchone()[0] == ident
        assert db.execute('SELECT COUNT(*) FROM cvs WHERE cv_kind="original"').fetchone()[0] == 1


def test_existing_account_workspace_gets_additive_tailoring_migration(app, tmp_path):
    from backend.user_data import provision_user_database

    root = tmp_path / 'phase10_workspaces'
    ident = str(uuid.uuid4())
    workspace, backup_dir = provision_user_database(app.config['DATABASE'], root, ident)
    with sqlite3.connect(workspace) as db:
        db.execute('DROP INDEX IF EXISTS idx_cvs_tailoring_offer')
        for name in ('validated_at', 'tailoring_payload', 'tailoring_mode', 'offer_id', 'source_cv_id', 'cv_status', 'cv_kind'):
            db.execute(f'ALTER TABLE cvs DROP COLUMN "{name}"')
        db.execute('PRAGMA user_version=9')
    migrated, _ = provision_user_database(app.config['DATABASE'], root, ident)
    with sqlite3.connect(migrated) as db:
        names = {row[1] for row in db.execute('PRAGMA table_info(cvs)')}
        assert db.execute('PRAGMA user_version').fetchone()[0] >= 10  # v11 (Phase 11) may follow
        assert {'cv_kind', 'cv_status', 'source_cv_id', 'offer_id', 'tailoring_mode', 'tailoring_payload', 'validated_at'} <= names
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert list(backup_dir.glob('avant_phase13_cv_tailoring_*.db'))


def _validated_tailored(client, cv_data, name='CV adapté · Python'):
    source = client.post('/api/cvs', json={'name': 'CV original', 'template': 'modern', 'data': cv_data})
    assert source.status_code == 201
    preview = client.post('/api/cvs/tailored/preview', json={'cv_id': source.json['id'], 'offer_id': 1})
    assert preview.status_code == 200
    body = {'name': name, 'template': 'modern', 'source_cv_id': source.json['id'],
            'offer_id': 1, 'action': 'validate', 'data': preview.json['data']}
    return source.json['id'], body


def test_identical_double_submission_does_not_create_a_duplicate(client, cv_data):
    source_id, body = _validated_tailored(client, cv_data)
    first = client.post('/api/cvs/tailored', json=body)
    second = client.post('/api/cvs/tailored', json=body)
    assert first.status_code == 201 and second.status_code == 200
    assert second.json['duplicate'] is True and second.json['id'] == first.json['id']
    assert len(client.get('/api/cvs/tailored').json) == 1
    changed = client.post('/api/cvs/tailored', json={**body, 'data': {**body['data'], 'summary': 'Résumé relu par moi.'}})
    assert changed.status_code == 201 and changed.json['id'] != first.json['id']


def test_tailored_version_cannot_be_used_as_source_and_original_stays_unchanged(client, cv_data):
    source_id, body = _validated_tailored(client, cv_data)
    original = client.get(f'/api/cvs/{source_id}').json['data']
    tailored = client.post('/api/cvs/tailored', json=body).json['id']
    edited = client.patch(f'/api/cvs/{tailored}/tailored', json={**body, 'data': {**body['data'], 'title': 'Titre relu'}})
    assert edited.status_code == 200
    assert client.get(f'/api/cvs/{source_id}').json['data'] == original
    refused = client.post('/api/cvs/tailored/preview', json={'cv_id': tailored, 'offer_id': 1})
    assert refused.status_code == 400 and 'original' in refused.json['erreur']


def test_tailored_version_reopen_and_delete(client, cv_data):
    source_id, body = _validated_tailored(client, cv_data)
    tailored = client.post('/api/cvs/tailored', json=body).json['id']
    reopened = client.get(f'/api/cvs/{tailored}').json
    assert reopened['cv_kind'] == 'tailored' and reopened['source_cv_id'] == source_id and reopened['offer_id'] == 1
    assert reopened['tailoring']['mode'] == 'local'
    assert client.delete(f'/api/cvs/{tailored}').status_code == 200
    assert client.get(f'/api/cvs/{tailored}').status_code == 404
    assert client.delete(f'/api/cvs/{source_id}').status_code == 200
