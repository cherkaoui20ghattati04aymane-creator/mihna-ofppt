import secrets

import pytest

from auth_gateway.config import load_config


@pytest.fixture
def hosted_layout(tmp_path, monkeypatch):
    root = tmp_path / 'persistent'
    root.mkdir(mode=0o700)
    catalogue = root / 'catalogue.db'
    auth_database = root / 'accounts.db'
    catalogue.touch()
    auth_database.touch()
    environment = {
        'AUTH_CONFIG_FILE': str(tmp_path / 'absent.env'),
        'AUTH_ENV': 'production',
        'AUTH_PROFILE': 'multi_user',
        'AUTH_ALLOW_REGISTRATION': 'true',
        'AUTH_MULTI_USER_MODE': 'true',
        'PUBLIC_DEMO_MODE': 'false',
        'DISABLE_BACKGROUND_SCHEDULER': 'true',
        'AUTH_PRODUCTION_SQLITE_ROOT': str(root),
        'AUTH_DATABASE_URL': 'sqlite:///' + auth_database.as_posix(),
        'AUTH_BACKEND_URL': 'http://127.0.0.1:5101',
        'AUTH_SESSION_SECRET': secrets.token_urlsafe(48),
        'AUTH_COOKIE_SECURE': 'true',
        'AUTH_ALLOWED_HOSTS': 'mihna.example',
        'AUTH_TRUSTED_PROXY_HOPS': '1',
        'DATABASE': str(catalogue),
        'PRIVATE_DIR': str(root / 'private'),
        'BACKUP_DIR': str(root / 'backups'),
        'AUTH_USER_DATA_ROOT': str(root / 'workspaces'),
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    return root


def test_production_multi_user_requires_explicit_durable_layout(hosted_layout, monkeypatch):
    assert load_config()['AUTH_HOSTED_SQLITE']
    monkeypatch.delenv('AUTH_PRODUCTION_SQLITE_ROOT')
    with pytest.raises(RuntimeError, match='réservé au lancement local'):
        load_config()


@pytest.mark.parametrize(('key', 'value', 'message'), [
    ('DATABASE', 'database/catalogue.db', 'dossier persistant'),
    ('AUTH_USER_DATA_ROOT', '../workspaces', 'dossier persistant'),
    ('AUTH_BACKEND_URL', 'http://localhost:5101', '127.0.0.1'),
    ('AUTH_MULTI_USER_MODE', 'false', 'isolation par compte'),
    ('AUTH_COOKIE_SECURE', 'false', 'HTTPS'),
])
def test_hosted_sqlite_cannot_weaken_production_guards(hosted_layout, monkeypatch, key, value, message):
    monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match=message):
        load_config()
