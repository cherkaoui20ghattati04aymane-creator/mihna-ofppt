"""Lecture seule : robots.txt de Jawb.ma et Wadifa.info pour les adresses de flux prévues.

Usage : .venv\\Scripts\\python.exe scripts\\check_sources.py [--wadifa-feed https://www.wadifa.info/feed/]
N'enregistre rien et ne collecte aucune annonce. Les conditions d'utilisation doivent être lues
manuellement : ce script ne remplace pas une autorisation écrite.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--wadifa-feed', default='https://www.wadifa.info/feed/')
    args = parser.parse_args(argv)
    from backend.scrapers.base import PoliteFetcher, ScraperError
    from backend.scrapers.jawb_scraper import feed_url
    for base, url in (('https://jawb.ma', feed_url('Marrakech')), ('https://www.wadifa.info', args.wadifa_feed)):
        fetcher = PoliteFetcher(base, min_delay=1)
        try:
            fetcher.load_robots()
            print(f'{base} : robots.txt lu ({len(fetcher.robots_text or "")} caractères).')
            print('   ', url, '->', 'AUTORISÉ par robots.txt' if fetcher.allowed(url) else 'INTERDIT par robots.txt')
            print('    Crawl-delay appliqué :', fetcher.min_delay, 's')
        except ScraperError as exc:
            print(f'{base} : vérification impossible ({exc}).')
    print('Rappel : lisez les CGU de chaque site et obtenez une autorisation écrite avant d’activer un connecteur.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
