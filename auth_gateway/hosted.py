"""Run the gateway and its loopback-only backend as one supervised web program."""
from __future__ import annotations

import argparse
import os
import signal
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote

import requests

from .config import load_config
from .launcher import check_database


def gunicorn(app, bind):
    return subprocess.Popen([
        sys.executable, '-m', 'gunicorn', '--bind', bind, '--workers', '1',
        '--threads', '2', '--timeout', '90', app,
    ])


def stop(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def preflight(config):
    if not config['AUTH_HOSTED_SQLITE'] or len(config['AUTH_INTERNAL_SECRET']) < 48:
        raise RuntimeError('Le profil SQLite hébergé et le secret du canal privé sont requis.')
    os.umask(0o077)
    os.environ['GEMINI_SEARCH_ENABLED'] = 'false'
    os.environ['SMTP_ENABLED'] = 'false'
    checked = check_database({**config, 'AUTH_APP_DATABASE': os.environ['DATABASE']})
    auth_path = Path(unquote(config['AUTH_DATABASE_URL'][len('sqlite:///'):])).resolve()
    for path, expected in ((checked['path'], 'offres'), (auth_path, 'auth_users')):
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
            if (db.execute('PRAGMA integrity_check').fetchone() != ('ok',)
                    or db.execute('PRAGMA foreign_key_check').fetchone()
                    or db.execute('SELECT 1 FROM sqlite_schema WHERE type=? AND name=?',
                                  ('table', expected)).fetchone() is None):
                raise RuntimeError('Une base persistante échoue au contrôle de démarrage.')
            if db.execute('PRAGMA journal_mode').fetchone() != ('delete',):
                raise RuntimeError('Le profil hébergé exige une base préparée en journalisation DELETE.')
            if expected == 'offres' and db.execute('PRAGMA user_version').fetchone() != (11,):
                raise RuntimeError('Vérifiez la migration du catalogue avant son démarrage hébergé.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bind', help='Provider-assigned IP address and port for the gateway.')
    options = parser.parse_args()
    config = load_config()
    port = config['AUTH_BACKEND_PORT']
    if config['AUTH_BACKEND_URL'] != f'http://127.0.0.1:{port}':
        parser.error('Le port du backend doit correspondre à son URL de boucle locale.')
    preflight(config)

    def shutdown(*_):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, shutdown)
    backend = gunicorn('backend.wsgi:app', f'127.0.0.1:{port}')
    try:
        with requests.Session() as session:
            session.trust_env = False
            for _ in range(60):
                if backend.poll() is not None:
                    raise RuntimeError('Le backend privé a quitté pendant le démarrage.')
                try:
                    if session.get(config['AUTH_BACKEND_URL'] + '/health', timeout=1).ok:
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError('Le backend privé ne répond pas.')

        gateway = gunicorn('auth_gateway.wsgi:app', options.bind)
        try:
            while gateway.poll() is None and backend.poll() is None:
                time.sleep(0.5)
            return 1
        finally:
            stop(gateway)
    finally:
        stop(backend)


if __name__ == '__main__':
    sys.exit(main())
