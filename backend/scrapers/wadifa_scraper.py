"""Connecteur Wadifa.info — flux RSS/Atom uniquement.

État de l'étude (17 novembre 2026) : la page d'accueil, le robots.txt et les conditions d'utilisation
de wadifa.info n'ont pas pu être consultés depuis l'environnement d'audit (accès réseau bloqué).
La structure réelle du site, l'existence d'un flux et les droits de réutilisation ne sont donc PAS
vérifiés. Le connecteur :
- est verrouillé tant que l'administrateur n'a pas saisi l'adresse exacte du flux ET la référence
  d'une autorisation écrite (consultation automatique, stockage, réaffichage) ;
- vérifie robots.txt au moment de la collecte et s'arrête s'il interdit l'adresse ;
- ne lit qu'un flux XML (aucune analyse de pages HTML, aucun contournement) ;
- n'enregistre que titre, organisme, ville, type, dates, URL d'origine, source et date de collecte.
Les offres de Wadifa sont surtout des concours publics : elles sont étiquetées « Concours » et ne
sont jamais présentées comme des stages si le texte ne le dit pas.
"""
from __future__ import annotations

from urllib.parse import urlparse

from .base import PoliteFetcher
from .quality import build_record, deduplicate, parse_feed

SOURCE = 'Wadifa.info'
BASE_URL = 'https://www.wadifa.info'
ALLOWED_HOSTS = ('wadifa.info',)


def collect(settings, fetcher=None):
    url = str(settings.get('feed_url') or '').strip()
    parsed = urlparse(url)
    if parsed.scheme != 'https' or (parsed.hostname or '').removeprefix('www.') != 'wadifa.info':
        raise ValueError('Renseignez l’adresse HTTPS exacte du flux RSS de wadifa.info (vérifiée manuellement).')
    fetcher = fetcher or PoliteFetcher(BASE_URL, min_delay=8, max_pages=2)
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
