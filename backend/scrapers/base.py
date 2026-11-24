"""Client HTTP poli : robots.txt, délai entre requêtes, domaine verrouillé, taille et délai bornés."""
from __future__ import annotations

import logging
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger('stages.scrapers')

USER_AGENT = 'StagesMarrakechAI/2.0 (+projet etudiant OFPPT; collecte autorisee uniquement)'
TIMEOUT = (5, 15)
MAX_BYTES = 3_000_000


class ScraperError(Exception):
    code = 'error'


class NotAuthorized(ScraperError):
    code = 'not_authorized'


class RobotsDisallowed(ScraperError):
    code = 'robots_disallowed'


class NetworkError(ScraperError):
    code = 'network'


class PageUnavailable(ScraperError):
    code = 'unavailable'


class BlockedByProtection(ScraperError):
    """CAPTCHA, connexion requise ou anti-bot : on s'arrête, sans contournement."""
    code = 'protected'


class PoliteFetcher:
    def __init__(self, base_url, session=None, min_delay=5.0, max_pages=5, sleep=time.sleep):
        parsed = urlparse(base_url)
        if parsed.scheme != 'https' or not parsed.hostname:
            raise ValueError('URL de base HTTPS requise.')
        self.base = f'https://{parsed.hostname}'
        self.host = parsed.hostname.lower()
        self.session = session or requests.Session()
        self.min_delay = float(min_delay)
        self.max_pages = int(max_pages)
        self.sleep = sleep
        self.robots = None
        self.robots_text = None
        self.pages = 0
        self._last = 0.0

    def _same_site(self, url):
        host = (urlparse(url).hostname or '').lower()
        return urlparse(url).scheme == 'https' and (host == self.host or host == 'www.' + self.host or 'www.' + host == self.host)

    def _get(self, url, accept):
        if not self._same_site(url):
            raise ValueError('URL hors du site autorisé refusée.')
        wait = self.min_delay - (time.monotonic() - self._last)
        if self._last and wait > 0:
            self.sleep(wait)
        self._last = time.monotonic()
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=False,
                                        headers={'User-Agent': USER_AGENT, 'Accept': accept})
        except requests.Timeout as exc:
            raise NetworkError('Délai dépassé en contactant le site.') from exc
        except requests.RequestException as exc:
            raise NetworkError('Site injoignable (réseau ou DNS).') from exc
        if 300 <= response.status_code < 400:
            location = urljoin(url, response.headers.get('Location', ''))
            if not self._same_site(location):
                raise PageUnavailable('Redirection hors du site refusée.')
            raise PageUnavailable('Page déplacée (redirection) : vérifiez l’adresse du flux.')
        if response.status_code in (401, 403, 429):
            raise BlockedByProtection(f'Accès refusé par le site (HTTP {response.status_code}) : collecte arrêtée, aucun contournement.')
        if response.status_code == 404:
            raise PageUnavailable('Page ou flux introuvable (404).')
        if response.status_code >= 400:
            raise PageUnavailable(f'Site indisponible (HTTP {response.status_code}).')
        if len(response.content) > MAX_BYTES:
            raise PageUnavailable('Réponse trop volumineuse.')
        lowered = response.text[:5000].lower()
        if any(marker in lowered for marker in ('g-recaptcha', 'hcaptcha', 'cf-challenge', 'captcha')):
            raise BlockedByProtection('Protection anti-robot détectée : collecte arrêtée, aucun contournement.')
        return response

    def load_robots(self):
        url = self.base + '/robots.txt'
        try:
            response = self._get(url, 'text/plain')
            text = response.text
        except PageUnavailable:
            text = ''  # robots.txt absent : pas d'interdiction déclarée (l'autorisation écrite reste requise)
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        self.robots, self.robots_text = parser, text
        delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay('*')
        if delay:
            self.min_delay = max(self.min_delay, float(delay))
        return parser

    def allowed(self, url):
        if self.robots is None:
            self.load_robots()
        return self.robots.can_fetch(USER_AGENT, url)

    def fetch(self, url, accept='application/rss+xml, application/atom+xml, application/xml, text/xml'):
        if self.pages >= self.max_pages:
            raise PageUnavailable('Limite de pages de la collecte atteinte.')
        if not self.allowed(url):
            raise RobotsDisallowed('robots.txt du site interdit cette adresse : collecte annulée.')
        self.pages += 1
        logger.info('scraper fetch host=%s page=%d', self.host, self.pages)
        return self._get(url, accept)
