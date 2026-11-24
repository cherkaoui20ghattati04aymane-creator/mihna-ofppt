"""Keep the local Himalayas catalog current without deleting historical references."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

import requests

from .db import backup_database, connect

LOGGER = logging.getLogger(__name__)
SOURCE = 'Himalayas'
CHECK_INTERVAL = timedelta(hours=23)
URL_PATH = re.compile(r'/companies/[a-zA-Z0-9_-]+/jobs/[a-zA-Z0-9_-]+/?')


def recently_verified(checked_at):
    try:
        checked = datetime.fromisoformat(checked_at or '')
        now = datetime.now(timezone.utc)
        return now - timedelta(days=1) <= checked <= now
    except (ValueError, TypeError):
        return False


def status_url(original):
    url = urlsplit(original or '')
    if (url.scheme, url.netloc) != ('https', 'himalayas.app') or not URL_PATH.fullmatch(url.path):
        return None
    return 'https://himalayas.app/jobs/api' + url.path.rstrip('/')


def _due_offers(database, now):
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True, timeout=15)) as db:
        return [url for url, checked in db.execute('''SELECT "Lien annonce", MIN(COALESCE(last_verified_at,''))
            FROM offres WHERE source=? AND COALESCE(statut_offre,'') != 'expired' GROUP BY "Lien annonce"''', (SOURCE,))
            if checked < (now - CHECK_INTERVAL).isoformat(timespec='seconds') and status_url(url)]


def refresh(database, workspace_root, backup_dir, stop):
    """Check each distinct listing at most once per batch, stopping on source errors."""
    now = datetime.now(timezone.utc)
    paths = [database, *sorted(workspace_root.glob('*.db'))]
    listings = sorted({listing for path in paths for listing in _due_offers(path, now)})
    if not listings:
        return
    results = {}
    with requests.Session() as client:
        client.headers['User-Agent'] = 'Mihna local catalog refresh/1.0'
        for listing in listings:
            if stop.is_set():
                return
            try:
                reply = client.get(status_url(listing), timeout=12, allow_redirects=False)
                if reply.status_code == 200:
                    job = reply.json().get('job')
                    if not isinstance(job, dict) or job.get('guid', '').rstrip('/') != listing.rstrip('/'):
                        raise ValueError('Mismatched listing in API response')
                    application_url = job.get('applicationLink', '')
                    if not isinstance(application_url, str) or not status_url(application_url):
                        raise ValueError('Missing authorized application URL')
                    results[listing] = ('active', application_url)
                elif reply.status_code in (404, 410):
                    results[listing] = ('expired', None)
                else:
                    LOGGER.warning('Himalayas refresh stopped on HTTP %s', reply.status_code)
                    break
            except (requests.RequestException, ValueError, AttributeError) as exc:
                LOGGER.warning('Himalayas refresh stopped (%s)', type(exc).__name__)
                break
            if stop.wait(1.25):
                return
    if not results:
        return
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for index, path in enumerate(paths):
        backup = backup_database(path, backup_dir, f'avant_himalayas_{index}')
        with closing(sqlite3.connect(backup.resolve().as_uri() + '?mode=ro', uri=True)) as check:
            if check.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or check.execute(
                    'PRAGMA foreign_key_check').fetchone():
                raise RuntimeError('Himalayas backup verification failed')
        with connect(path) as db:
            db.executemany('''UPDATE offres SET statut_offre=?, "Lien public"=COALESCE(?, "Lien public"),
                last_verified_at=? WHERE source=? AND "Lien annonce"=?''',
                [(status, url, stamp, SOURCE, listing) for listing, (status, url) in results.items()])
    LOGGER.warning('Himalayas refresh verified %d listings (%d deactivated)',
                   len(results), sum(status == 'expired' for status, _ in results.values()))


def run_daily(database, workspace_root, backup_dir, stop):
    while not stop.is_set():
        try:
            refresh(Path(database), Path(workspace_root), Path(backup_dir), stop)
        except (OSError, sqlite3.Error, RuntimeError) as exc:
            LOGGER.warning('Himalayas refresh did not finish (%s)', type(exc).__name__)
        stop.wait(3600)
