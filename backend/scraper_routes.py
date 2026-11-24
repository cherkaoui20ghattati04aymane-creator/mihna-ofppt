"""Routes des connecteurs Jawb.ma / Wadifa.info (configuration, état, collecte vers staging)."""
from flask import Blueprint, jsonify

from .api import body, config
from .scrapers import pipeline
from .scrapers.base import NotAuthorized

scrapers = Blueprint('scrapers', __name__, url_prefix='/api/scrapers')


@scrapers.get('')
def scraper_status():
    return jsonify(sources=pipeline.status(config()['DATABASE']),
                   policy='Flux officiels uniquement, robots.txt respecté, autorisation écrite requise, revue humaine avant import.')


@scrapers.post('/<source>/config')
def scraper_config(source):
    pipeline.set_config(config()['DATABASE'], source, body())
    return jsonify(sources=pipeline.status(config()['DATABASE']))


@scrapers.post('/<source>/run')
def scraper_run(source):
    try:
        result = pipeline.run(config()['DATABASE'], source)
    except NotAuthorized as exc:
        return jsonify(erreur=str(exc)), 403
    return jsonify(result), (201 if result['status'] == 'previewed' else 502)
