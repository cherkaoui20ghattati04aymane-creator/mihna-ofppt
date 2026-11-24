"""Appel RÉEL à Google Gemini — exécuté uniquement à la demande :

    set RUN_GEMINI_REAL_TEST=1
    .venv\\Scripts\\python.exe -m pytest tests\\test_gemini_real.py -q -s

Utilise la clé de votre .env. N'affiche jamais la clé. Ignoré dans tous les autres cas.
"""
import os

import pytest

pytestmark = pytest.mark.gemini_real


@pytest.fixture(autouse=True)
def allow_real_network(monkeypatch):
    # Annule le blocage réseau de conftest.py pour CE test explicite uniquement.
    import socket
    monkeypatch.undo()
    yield socket


@pytest.mark.real_sdk_detection
def test_real_gemini_connection():
    if os.environ.get('RUN_GEMINI_REAL_TEST') != '1':
        pytest.skip('Test réel désactivé : définir RUN_GEMINI_REAL_TEST=1 pour appeler vraiment Gemini.')
    from backend.config import settings
    from backend.services.gemini_service import GeminiService
    service = GeminiService(settings())
    state = service.status()
    assert state['enabled'], 'Configuration incomplète : ' + ' '.join(state['reasons'])
    result = service.verify_connection()
    print(f"\nGemini réel : {'RÉUSSI' if result['ok'] else 'ÉCHEC'} · modèle {result['model']} · {result['latency_ms']} ms"
          + ('' if result['ok'] else f" · {result.get('error_label')}"))
    assert result['ok'], result.get('error_label')
