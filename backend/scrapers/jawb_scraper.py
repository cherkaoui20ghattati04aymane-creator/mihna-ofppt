"""Connecteur Jawb.ma — flux RSS public documenté par Jawb (aucun scraping HTML).

Registre des droits (vérifié le 6 et le 9 novembre 2026 dans le projet, voir GUIDE_SOURCES_AUTORISEES.md) :
le guide API de Jawb décrit le flux pour la page carrière de l'entreprise et les CGU réservent la
réutilisation du contenu. Le connecteur reste donc VERROUILLÉ tant qu'une autorisation écrite n'est
pas référencée (consultation automatique, stockage, réaffichage). Les descriptions ne sont stockées
que si leur republication est explicitement autorisée ; sinon : champs factuels + lien d'origine.
"""
from __future__ import annotations

from urllib.parse import urlencode

from .base import PoliteFetcher
from .quality import build_record, deduplicate, parse_feed

SOURCE = 'Jawb.ma'
BASE_URL = 'https://jawb.ma'
FEED_PATH = '/rss.xml'
ALLOWED_HOSTS = ('jawb.ma',)


def feed_url(city='Marrakech', profession=''):
    params = {'ville': city} if city else {}
    if profession:
        params['metier'] = profession
    return BASE_URL + FEED_PATH + ('?' + urlencode(params) if params else '')


def collect(settings, fetcher=None):
    """Retourne {'records', 'errors', 'duplicates', 'robots_allowed', 'url'} sans rien écrire."""
    fetcher = fetcher or PoliteFetcher(BASE_URL, min_delay=5, max_pages=2)
    url = settings.get('feed_url') or feed_url(settings.get('city', 'Marrakech'), settings.get('profession', ''))
    robots_allowed = fetcher.allowed(url)
    response = fetcher.fetch(url)
    records, errors = [], []
    for index, raw in enumerate(parse_feed(response.text)):
        record, problems = build_record(raw, SOURCE, ALLOWED_HOSTS, store_description=settings.get('description_allowed') is True)
        if record:
            records.append(record)
        else:
            errors.append({'item': index + 1, 'errors': problems})
    records, duplicates = deduplicate(records)
    return {'records': records, 'errors': errors, 'duplicates': duplicates, 'robots_allowed': robots_allowed, 'url': url}
