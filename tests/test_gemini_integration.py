"""Intégration Gemini : configuration, SDK, erreurs, mode local, non-exposition de la clé.

Tous ces tests utilisent des clients SIMULÉS : ils prouvent le comportement du code, pas la
connexion réelle à Google. Le test réel est dans test_gemini_real.py (opt-in).
"""
import io
import json
import logging
import sys
import types
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.config import settings
from backend.services import gemini_service as gs

SECRET = 'FAUSSE-CLE-DE-TEST-0123456789abcdefghijk'
ON = {'GEMINI_ENABLED': True, 'GEMINI_API_KEY': SECRET, 'GEMINI_FREE_TIER_CONFIRMED': True, 'GEMINI_MODEL': 'gemini-3.5-flash-lite'}


class FakeAPIError(Exception):
    def __init__(self, code, message):
        super().__init__(f'{code} {message}')
        self.code = code


def client_returning(text=None, error=None):
    call = Mock(side_effect=error) if error else Mock(return_value=SimpleNamespace(text=text))
    return SimpleNamespace(models=SimpleNamespace(generate_content=call), close=Mock()), call


# 1. Lecture de la configuration ------------------------------------------------
def test_configuration_is_read_from_environment_and_tolerates_formatting(monkeypatch):
    monkeypatch.setenv('GEMINI_ENABLED', ' True ')
    monkeypatch.setenv('GEMINI_API_KEY', f'  "{SECRET}"  ')
    monkeypatch.setenv('GEMINI_FREE_TIER_CONFIRMED', 'oui')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
    cfg = settings()
    assert cfg['GEMINI_ENABLED'] is True and cfg['GEMINI_FREE_TIER_CONFIRMED'] is True
    assert cfg['GEMINI_API_KEY'] == SECRET and cfg['GEMINI_MODEL'] == 'gemini-3.1-flash-lite'
    monkeypatch.setenv('GEMINI_ENABLED', 'false')
    assert settings()['GEMINI_ENABLED'] is False


def test_env_file_with_bom_is_loaded(tmp_path, monkeypatch):
    from dotenv import load_dotenv
    env = tmp_path / '.env'
    env.write_bytes('﻿GEMINI_ENABLED=true\nGEMINI_API_KEY=abc\n'.encode('utf-8'))
    monkeypatch.delenv('GEMINI_ENABLED', raising=False)
    load_dotenv(env, override=True, encoding='utf-8-sig')
    import os
    assert os.environ['GEMINI_ENABLED'] == 'true'


# 2-3. Clé absente / Gemini désactivé ----------------------------------------
@pytest.mark.parametrize('override,fragment', [
    ({'GEMINI_API_KEY': ''}, 'GEMINI_API_KEY'), ({'GEMINI_API_KEY': 'YOUR_API_KEY'}, 'valeur d’exemple'),
    ({'GEMINI_ENABLED': False}, 'GEMINI_ENABLED'), ({'GEMINI_FREE_TIER_CONFIRMED': False}, 'GEMINI_FREE_TIER_CONFIRMED'),
    ({'GEMINI_MODEL': 'gemini-ultra-inconnu'}, 'GEMINI_ALLOWED_MODELS')])
def test_incomplete_configuration_never_activates_gemini(override, fragment):
    state = gs.GeminiService({**ON, **override}).status()
    assert state['enabled'] is False and state['state'] == 'disabled'
    assert any(fragment in reason for reason in state['reasons'])
    with pytest.raises(gs.GeminiDisabled):
        gs.GeminiService({**ON, **override}).generate_json('t', {}, {}, 'x')


@pytest.mark.real_sdk_detection
def test_missing_sdk_is_detected_without_simulation(monkeypatch):
    monkeypatch.setattr('importlib.util.find_spec', lambda name: None)
    state = gs.GeminiService(ON).status()
    assert state['sdk_installed'] is False and state['enabled'] is False
    assert any('google-genai' in reason for reason in state['reasons'])


# 4. Initialisation du SDK ------------------------------------------------------
def test_sdk_client_initialised_with_key_and_timeout(monkeypatch):
    captured = {}

    class Client:
        def __init__(self, api_key, http_options):
            captured.update(api_key=api_key, timeout=http_options.timeout)

    fake_types = types.SimpleNamespace(HttpOptions=lambda timeout: SimpleNamespace(timeout=timeout))
    genai = types.ModuleType('google.genai'); genai.Client = Client; genai.types = fake_types
    google = types.ModuleType('google'); google.genai = genai
    monkeypatch.setitem(sys.modules, 'google', google)
    monkeypatch.setitem(sys.modules, 'google.genai', genai)
    monkeypatch.setitem(sys.modules, 'google.genai.types', fake_types)
    gs.GeminiService({**ON, 'GEMINI_API_KEY': f' {SECRET} ', 'GEMINI_TIMEOUT_SECONDS': 15}).get_client()
    assert captured == {'api_key': SECRET, 'timeout': 15000}


# 5-7 + réseau / modèle / réponse vide -------------------------------------------
@pytest.mark.parametrize('error,expected', [
    (FakeAPIError(400, 'API key not valid. Please pass a valid API key.'), gs.GeminiAuthError),
    (FakeAPIError(401, 'UNAUTHENTICATED'), gs.GeminiAuthError),
    (FakeAPIError(403, 'PERMISSION_DENIED'), gs.GeminiAuthError),
    (FakeAPIError(429, 'RESOURCE_EXHAUSTED'), gs.GeminiQuotaExceeded),
    (FakeAPIError(404, 'models/x is not found'), gs.GeminiModelUnavailable),
    (type('ReadTimeout', (Exception,), {})('timed out'), gs.GeminiTimeout),
    (type('ConnectError', (Exception,), {})('[Errno 11001] getaddrinfo failed'), gs.GeminiNetworkError),
    (FakeAPIError(503, 'UNAVAILABLE'), gs.GeminiError)])
def test_provider_errors_are_classified(error, expected):
    client, _ = client_returning(error=error)
    with pytest.raises(expected) as caught:
        gs.GeminiService(ON).generate_json('t', {'a': 1}, {}, 'x', client=client)
    assert SECRET not in caught.value.user_message


def test_empty_response_is_invalid():
    client, _ = client_returning('   ')
    with pytest.raises(gs.GeminiInvalidResponse):
        gs.GeminiService(ON).generate_text('t', 'x', 'y', client=client)


# Test de connexion réel simulé : états honnêtes ---------------------------------
def test_status_never_claims_connected_before_a_successful_real_check(tmp_path):
    cfg = {**ON, 'PRIVATE_DIR': str(tmp_path)}
    service = gs.GeminiService(cfg)
    assert service.status()['state'] == 'configured' and service.status()['verified'] is False
    failing, _ = client_returning(error=FakeAPIError(401, 'UNAUTHENTICATED'))
    result = service.verify_connection(client=failing)
    assert result['ok'] is False and result['error_code'] == 'auth'
    assert service.status()['state'] == 'error' and service.status()['verified'] is False
    working, call = client_returning('OK')
    assert service.verify_connection(client=working)['ok'] is True
    assert service.status()['state'] == 'connected' and 'test réel réussi' in service.status()['label']
    assert 'OK' in call.call_args.kwargs['contents']  # requête minimale, aucune donnée utilisateur
    # Une nouvelle clé invalide le statut « connecté » précédent.
    assert gs.GeminiService({**cfg, 'GEMINI_API_KEY': SECRET + 'X'}).status()['state'] == 'configured'


def test_verification_accepts_empty_text_but_not_errors(tmp_path):
    service = gs.GeminiService({**ON, 'PRIVATE_DIR': str(tmp_path)})
    empty, _ = client_returning('')
    result = service.verify_connection(client=empty)
    assert result['ok'] is True and result['reply_received'] is False


def test_list_models_filters_generate_content():
    models = [SimpleNamespace(name='models/gemini-3.5-flash-lite', supported_actions=['generateContent']),
              SimpleNamespace(name='models/text-embedding-004', supported_actions=['embedContent']),
              SimpleNamespace(name='models/gemini-embedding-2', supported_actions=['embedContent'])]
    client = SimpleNamespace(models=SimpleNamespace(list=lambda: iter(models)), close=Mock())
    assert gs.GeminiService(ON).list_models(client=client) == ['gemini-3.5-flash-lite']


# 8. Mode local conservé ---------------------------------------------------------
def test_local_mode_works_and_gemini_failure_falls_back(client, app, cv_data, monkeypatch):
    assert client.post('/api/ai/cv/analyze', json={'cv': cv_data}).json['mode'] == 'local'
    app.config.update(ON)
    preview = client.post('/api/ai/cv/analyze/preview', json={'cv': cv_data}).json
    down, _ = client_returning(error=type('ConnectError', (Exception,), {})('getaddrinfo failed'))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: down)
    r = client.post('/api/ai/cv/analyze', json={'cv': cv_data, 'mode': 'gemini', 'consent': True, 'digest': preview['digest']}).json
    assert r['mode'] == 'local' and r['fallback'] is True and 'Internet' in r['notice']
    assert r['analysis']['score'] >= 0  # l'analyse locale reste affichée


def test_gemini_cv_analysis_explains_weaknesses_without_invented_facts(client, app, cv_data, monkeypatch):
    app.config.update(ON)
    preview = client.post('/api/ai/cv/analyze/preview', json={'cv': cv_data}).json
    answer = {'strengths': ['Compétences Python cohérentes avec la formation.', 'A dirigé 12 personnes.'],
              'weaknesses': [{'label': 'Expériences', 'explanation': 'Aucune expérience professionnelle décrite.',
                              'suggestion': 'Détaillez un projet : rôle, outils, résultat.'}]}
    fake, _ = client_returning(json.dumps(answer, ensure_ascii=False))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: fake)
    r = client.post('/api/ai/cv/analyze', json={'cv': cv_data, 'mode': 'gemini', 'consent': True, 'digest': preview['digest']}).json
    assert r['mode'] == 'gemini'
    assert r['analysis']['strengths_ai'] == ['Compétences Python cohérentes avec la formation.']  # « 12 personnes » rejeté
    assert any(s['label'].startswith('Point faible') for s in r['suggestions'])
    assert client.get('/api/cvs').json == []  # rien n'est enregistré automatiquement


# 9. Protection contre l'exposition de la clé ---------------------------------------
def test_key_never_exposed_in_api_logs_or_errors(client, app, caplog, monkeypatch):
    app.config.update(ON)
    leaking, _ = client_returning(error=FakeAPIError(400, f'API key not valid: {SECRET}'))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: leaking)
    with caplog.at_level(logging.DEBUG):
        bodies = [client.get('/api/ai/status').data, client.get('/api/assistant/status').data,
                  client.post('/api/ai/verify', json={}).data, client.get('/api/ai/status').data]
    for body in bodies:
        assert SECRET.encode() not in body
    assert SECRET not in caplog.text
    verify = json.loads(bodies[2])
    assert verify['result']['ok'] is False and verify['result']['error_code'] == 'auth'
    assert verify['status']['state'] == 'error'


def test_startup_log_reports_configuration_without_key(legacy_database, tmp_path, caplog):
    from backend.web import create_app
    with caplog.at_level(logging.WARNING):
        create_app({'DATABASE': str(legacy_database), 'PRIVATE_DIR': str(tmp_path / 'p'), 'BACKUP_DIR': str(tmp_path / 'b'), **ON})
    line = next(r.getMessage() for r in caplog.records if 'Gemini au démarrage' in r.getMessage())
    assert 'clé présente=True' in line and 'prêt=True' in line and SECRET not in caplog.text


def test_verify_endpoint_requires_session_and_is_blocked_in_public_demo(app):
    anonymous = app.test_client()
    assert anonymous.post('/api/ai/verify', json={}).status_code in (401, 403)


def test_env_is_ignored_by_git_and_example_has_no_real_key():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert '.env' in (root / '.gitignore').read_text().splitlines()
    example = (root / '.env.example').read_text(encoding='utf-8')
    key_line = next(line for line in example.splitlines() if line.startswith('GEMINI_API_KEY='))
    assert key_line.split('=', 1)[1].strip() in ('', 'YOUR_API_KEY')
    assert 'AIza' not in example
