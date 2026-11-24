"""Phase 9 account-profile and notification safety regression tests."""
import sqlite3


def test_profile_persists_and_prefills_only_selected_cv_sections(client, app):
    page = client.get('/profile.html')
    assert page.status_code == 200
    assert b'data-page="profile"' in page.data

    profile = {
        'first_name': 'Amina', 'last_name': 'Test', 'email': 'amina@example.test',
        'summary': 'Résumé privé', 'skills': ['Python'], 'languages': ['Français'],
        'cv_sections': ['contact', 'summary', 'skills', 'languages'],
    }
    saved = client.put('/api/profile', json=profile)
    assert saved.status_code == 200
    assert client.get('/api/profile').json['profile']['summary'] == 'Résumé privé'

    draft = client.get('/api/profile/cv-draft')
    assert draft.status_code == 200
    assert draft.json['data']['name'] == 'Amina Test'
    assert draft.json['data']['technical'] == 'Python'
    assert draft.json['data']['languages'] == 'Français'
    assert draft.json['data']['education'] == []

    with sqlite3.connect(app.config['DATABASE']) as db:
        payload = db.execute('SELECT payload FROM user_profile WHERE id=1').fetchone()[0]
    assert b'amina@example.test' not in payload
    assert 'Résumé privé'.encode() not in payload


def test_interview_history_is_encrypted_and_only_saved_after_explicit_request(client, app, cv_data):
    cv = client.post('/api/cvs', json={'name': 'Version de test', 'template': 'modern', 'data': cv_data})
    assert cv.status_code == 201
    payload = {
        'cv_id': cv.json['id'], 'offer_id': 1,
        'answers': [{'question': 'Présentez-vous', 'answer': 'Ma réponse privée'}],
        'feedback': {'answer_feedback': [], 'note': 'Retour local'},
    }
    saved = client.post('/api/career/interviews', json=payload)
    assert saved.status_code == 201
    history = client.get('/api/career/interviews')
    assert len(history.json['items']) == 1
    assert history.json['items'][0]['answers'][0]['answer'] == 'Ma réponse privée'

    with sqlite3.connect(app.config['DATABASE']) as db:
        encrypted = db.execute('SELECT payload FROM ai_interview_history').fetchone()[0]
    assert b'Ma r' not in encrypted
    assert 'Ma réponse privée'.encode() not in encrypted


def test_cv_section_order_is_preserved_in_pdf(cv_data):
    from backend.cv_service import extract_pdf, make_pdf, validate_cv

    data = validate_cv({
        **cv_data,
        'experience': [{'title': 'Stage fictif', 'organization': 'Organisation de test', 'period': '2025', 'description': 'Tâches de test.'}],
        'section_order': ['education', 'experience', 'projects', 'certifications'],
    })
    rendered = extract_pdf(make_pdf(data, 'modern'))
    assert rendered.index('Formation') < rendered.index('Expériences professionnelles')


def test_alert_email_requires_explicit_consent_and_smtp(client, app, monkeypatch):
    response = client.put('/api/alerts/preferences', json={
        'enabled': True, 'email_enabled': True, 'email_consent': False,
        'email_recipient': 'candidate@example.test', 'skills': [],
    })
    assert response.status_code == 400
    assert 'accord' in response.json['erreur'].lower()

    response = client.put('/api/alerts/preferences', json={
        'enabled': True, 'email_enabled': True, 'email_consent': True,
        'email_recipient': 'candidate@example.test', 'skills': [],
    })
    assert response.status_code == 400
    assert 'SMTP' in response.json['erreur']

    import backend.alert_mail as alert_mail
    calls = []
    monkeypatch.setattr(alert_mail.smtplib, 'SMTP', lambda *args, **kwargs: calls.append(args))
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.execute("UPDATE alert_preferences SET email_enabled=1,email_payload='encrypted-fixture',email_consent_at=NULL WHERE id=1")
        db.execute("INSERT OR IGNORE INTO alerts(offer_id,created_at,score,explanation) VALUES (1,'2026-11-01',50,'fixture')")
        alert_id = db.execute('SELECT id FROM alerts WHERE offer_id=1').fetchone()[0]
    alert_mail.deliver_new_alerts(app.config['DATABASE'], [alert_id])
    assert calls == []
