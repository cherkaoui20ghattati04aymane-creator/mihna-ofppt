"""Narrow connectors for free APIs whose terms permit the intended use.

This module currently supports the Himalayas Remote Jobs API. The API terms
permit display on StageX's own app with attribution and require use of its
applicationLink. Search results are kept when the record explicitly restricts
eligibility to Morocco or when the documented empty restrictions array means
worldwide eligibility. Missing physical city is never inferred from a remote
tag, timezone, title, company, or keyword.
"""
from datetime import datetime, timezone
from time import sleep
from urllib.parse import quote, urlsplit

import requests

from .schema import normalize_offer

HIMALAYAS_API = 'https://himalayas.app/jobs/api/search'
HIMALAYAS_HOST = 'himalayas.app'
TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 2_000_000
MAX_PAGES = 5
PAGE_SIZE = 20
USER_AGENT = 'StageX-Marrakech-Phase5/1.0 (read-only public API client)'


def _api_get(session, url, params=None):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != HIMALAYAS_HOST
            or parts.username or parts.password):
        raise ValueError('URL Himalayas refusée.')
    response = session.get(url, params=params, timeout=TIMEOUT_SECONDS,
                           allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection API refusée.')
    response.raise_for_status()
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError('Réponse API supérieure à la limite locale.')
    return response


def _allowed_api_url(value):
    parts = urlsplit(str(value or '').strip())
    return (parts.scheme == 'https' and parts.hostname == HIMALAYAS_HOST
            and not parts.username and not parts.password)


def parse_himalayas_payload(payload, *, query='', require_country='Morocco',
                            metrics=None, captured_at=None):
    """Normalize one API page; reject records without explicit country eligibility.

    ``query`` is retained only as extraction provenance. It is not used to
    assign a city. The API response has no structured city field.
    """
    metrics = metrics if metrics is not None else {}
    jobs = payload.get('jobs') if isinstance(payload, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('Réponse Himalayas invalide : liste jobs absente.')
    metrics['received_count'] = metrics.get('received_count', 0) + len(jobs)
    metrics.setdefault('rejected_count', 0)
    metrics.setdefault('valid_count', 0)
    result = []
    captured_at = captured_at or datetime.now(timezone.utc).isoformat(timespec='seconds')
    for raw in jobs:
        if not isinstance(raw, dict):
            metrics['rejected_count'] += 1
            continue
        restrictions = raw.get('locationRestrictions')
        if not isinstance(restrictions, list):
            metrics['rejected_count'] += 1
            continue
        # Provider documentation defines an empty restrictions array as
        # worldwide. Handle both the documented object schema and the strings
        # returned in the live sample.
        if not restrictions:
            eligibility = 'Worldwide'
            classification = 'remote_worldwide_eligible'
        else:
            allowed = False
            for restriction in restrictions:
                if isinstance(restriction, str) and restriction.casefold() == require_country.casefold():
                    allowed = True
                elif isinstance(restriction, dict) and (
                    str(restriction.get('name') or '').casefold() == require_country.casefold()
                    or (require_country.casefold() == 'morocco'
                        and str(restriction.get('alpha2') or '').upper() == 'MA')
                    or (require_country.casefold() == 'morocco'
                        and str(restriction.get('slug') or '').casefold() == 'morocco')
                ):
                    allowed = True
            if not allowed:
                metrics['rejected_count'] += 1
                continue
            eligibility = require_country
            classification = 'remote_morocco_eligible'
        source_url = raw.get('guid')
        application_url = raw.get('applicationLink')
        if not _allowed_api_url(source_url) or not _allowed_api_url(application_url):
            metrics['rejected_count'] += 1
            continue
        slug = raw.get('guid') or ''
        item = normalize_offer({
            'source_id': slug,
            'title': raw.get('title'),
            'company': raw.get('companyName'),
            # The source API exposes country eligibility, not a structured city.
            'city': '',
            'sector': ', '.join(raw.get('categories') or []) if isinstance(raw.get('categories'), list) else '',
            'description': raw.get('description') or raw.get('excerpt') or '',
            'contract_type': raw.get('employmentType'),
            'skills': raw.get('categories') or [],
            'published_at': raw.get('pubDate'),
            'expires_at': raw.get('expiryDate'),
            'job_url': source_url,
            # Himalayas requires Apply actions to use this API field.
            'apply_url': application_url,
        }, 'Himalayas')
        if not item:
            metrics['rejected_count'] += 1
            continue
        item.update({
            'attribution': 'Source : Himalayas',
            'remote': True,
            'location_eligibility': eligibility,
            'location_classification': classification,
            'eligibility_basis': 'worldwide (source-defined)' if eligibility == 'Worldwide' else 'explicit country restriction',
            'city_verified': False,
            'query_location_hint': query,
            'captured_at': captured_at,
            'source_application_url': application_url,
            # Retain source fields useful for review; do not infer a city from them.
            'source_seniority': raw.get('seniority') if isinstance(raw.get('seniority'), list) else [],
            'source_location_restrictions': restrictions,
            'source_employment_type': raw.get('employmentType'),
        })
        result.append(item)
        metrics['valid_count'] += 1
    return result


def fetch_himalayas(query='', country='Morocco', max_pages=1, *, session=None,
                    metrics=None, pause_seconds=1.05):
    """Fetch a bounded number of documented search pages (20 jobs/page max).

    At least one search filter is mandatory. For StageX's country classification,
    records must separately state the country in ``locationRestrictions``.
    """
    query = str(query or '').strip()[:120]
    country = str(country or '').strip().upper()[:2]
    if not query and not country:
        raise ValueError('Un filtre q ou country est requis; le flux complet est refusé.')
    if country and country != 'MA':
        raise ValueError('Ce connecteur StageX accepte uniquement le code pays documenté pour le Maroc : MA.')
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError(f'max_pages doit être compris entre 1 et {MAX_PAGES}.')
    session = session or requests.Session()
    metrics = metrics if metrics is not None else {}
    metrics.setdefault('request_count', 0)
    metrics.setdefault('pages', 0)
    all_items = []
    for page in range(1, max_pages + 1):
        params = {'page': page}
        if query:
            params['q'] = query
        if country:
            params['country'] = country
        response = _api_get(session, HIMALAYAS_API, params=params)
        metrics['request_count'] += 1
        metrics['pages'] += 1
        payload = response.json()
        all_items.extend(parse_himalayas_payload(payload, query=query,
                          require_country='Morocco', metrics=metrics))
        returned = payload.get('jobs') if isinstance(payload, dict) else []
        total = payload.get('totalCount') if isinstance(payload, dict) else None
        limit = payload.get('limit') if isinstance(payload, dict) else None
        if not returned or (isinstance(total, int) and isinstance(limit, int)
                            and page * limit >= total):
            break
        if page < max_pages:
            sleep(max(0, float(pause_seconds)))
    return all_items


def deduplicate_records(records):
    """Keep the first source-ID/canonical-URL identity and report duplicates."""
    unique = {}
    duplicates = 0
    for record in records:
        identity = record.get('source_id') or record.get('canonical_url')
        key = (record.get('source'), identity)
        if not identity or key in unique:
            duplicates += 1
            continue
        unique[key] = record
    return list(unique.values()), duplicates


def check_himalayas_job(guid, *, session=None):
    """Use Himalayas' documented status API, including documented 404/410 states."""
    parts = urlsplit(str(guid or '').strip())
    if (parts.scheme != 'https' or parts.hostname != HIMALAYAS_HOST
            or not parts.path.startswith('/companies/') or parts.query or parts.fragment):
        raise ValueError('Identifiant de poste Himalayas invalide.')
    # Only accept the documented company/jobs/slug route and build the API URL
    # from validated path segments.
    segments = [segment for segment in parts.path.split('/') if segment]
    if len(segments) != 4 or segments[0] != 'companies' or segments[2] != 'jobs':
        raise ValueError('Chemin de poste Himalayas invalide.')
    path = '/'.join(quote(segment, safe='-._~') for segment in segments)
    url = f'https://{HIMALAYAS_HOST}/jobs/api/{path}'
    session = session or requests.Session()
    response = session.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection API refusée.')
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError('Réponse API supérieure à la limite locale.')
    if response.status_code not in (200, 404, 410):
        response.raise_for_status()
    payload = response.json()
    job = payload.get('job') if isinstance(payload, dict) else None
    if response.status_code == 200 and not isinstance(job, dict):
        raise ValueError('Réponse du statut Himalayas invalide.')
    return {'http_status': response.status_code, 'job': job if isinstance(job, dict) else None,
            'payload': payload}
