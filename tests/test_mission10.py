"""Tests de la mission 10 : service Gemini, CV Studio (couleurs, photo, modèles), assistants IA,
matching explicable, connecteurs Jawb/Wadifa, migration d'index, garde Dash, pagination."""
import base64
import hashlib
import io
import json
import logging
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PIL import Image
from pypdf import PdfReader

from backend.services import gemini_service as gs
from backend.cv_design import (PALETTES, contrast_warnings, normalize_photo, sanitize_upload, validate_design, TEMPLATES)
from backend.cv_service import make_pdf, validate_cv


# ------------------------------------------------------------------ outils
def image_bytes(fmt='PNG', size=(400, 300), color=(40, 90, 160), mode='RGB'):
    out = io.BytesIO()
    Image.new(mode, size, color).save(out, fmt)
    return out.getvalue()


def data_url(raw, mime='image/png'):
    return f'data:{mime};base64,' + base64.b64encode(raw).decode()


def fake_client(text):
    call = Mock(return_value=SimpleNamespace(text=text))
    return SimpleNamespace(models=SimpleNamespace(generate_content=call), close=Mock()), call


GEMINI_ON = {'GEMINI_ENABLED': True, 'GEMINI_API_KEY': 'FAKE-KEY-123', 'GEMINI_FREE_TIER_CONFIRMED': True,
             'GEMINI_MODEL': 'gemini-3.5-flash-lite'}


@pytest.fixture
def gemini_app(app):
    app.config.update(GEMINI_ON)
    return app


# ------------------------------------------------------------ service Gemini
def test_gemini_service_disabled_reasons_and_no_key_leak(tmp_path):
    state = gs.GeminiService({'GEMINI_API_KEY': ''}).status()
    assert state['enabled'] is False and any('GEMINI_API_KEY' in r for r in state['reasons'])
    state = gs.GeminiService({**GEMINI_ON, 'PRIVATE_DIR': str(tmp_path)}).status()
    assert state['enabled'] is True and 'FAKE-KEY-123' not in json.dumps(state)
    assert gs.GeminiService({**GEMINI_ON, 'GEMINI_MODEL': 'gemini-pro-inconnu'}).enabled is False
    with pytest.raises(gs.GeminiDisabled):
        gs.GeminiService({}).generate_json('t', {}, {}, 'x', client=fake_client('{}')[0])


def test_gemini_rate_limit_daily_quota_and_counter_file(tmp_path):
    cfg = {**GEMINI_ON, 'PRIVATE_DIR': str(tmp_path), 'GEMINI_RATE_PER_MINUTE': 2, 'GEMINI_DAILY_LIMIT': 3}
    service = gs.GeminiService(cfg)
    client, _ = fake_client('{"ok": true}')
    assert service.generate_json('t', {'a': 1}, {}, 'x', client=client) == {'ok': True}
    service.generate_json('t', {'a': 2}, {}, 'x', client=client)
    with pytest.raises(gs.GeminiRateLimited):
        service.generate_json('t', {'a': 3}, {}, 'x', client=client)
    gs.reset_state_for_tests()
    service.generate_json('t', {'a': 4}, {}, 'x', client=client)
    gs.reset_state_for_tests()
    with pytest.raises(gs.GeminiQuotaExceeded):
        service.generate_json('t', {'a': 5}, {}, 'x', client=client)
    usage = json.loads((tmp_path / 'gemini_usage.json').read_text())
    assert usage['count'] == 3 and usage['day'] == date.today().isoformat()


def test_gemini_cache_avoids_repeated_calls(monkeypatch, tmp_path):
    client, call = fake_client('{"v": 1}')
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: client)
    service = gs.GeminiService({**GEMINI_ON, 'PRIVATE_DIR': str(tmp_path)})
    assert service.generate_json('t', {'same': 1}, {}, 'x') == {'v': 1}
    assert service.generate_json('t', {'same': 1}, {}, 'x') == {'v': 1}
    assert call.call_count == 1
    assert call.call_args.kwargs['config']['response_mime_type'] == 'application/json'


@pytest.mark.parametrize('error,expected', [
    (SimpleNamespace(code=429), gs.GeminiQuotaExceeded), (SimpleNamespace(code=401), gs.GeminiAuthError),
    (TimeoutError('read timed out'), gs.GeminiTimeout), (RuntimeError('boom'), gs.GeminiError)])
def test_gemini_errors_are_translated(error, expected):
    exc = error if isinstance(error, Exception) else type('APIError', (Exception,), {'code': error.code})('x')
    assert isinstance(gs.GeminiService.translate_error(exc), expected)


def test_gemini_invalid_json_and_logs_without_content(caplog):
    client, _ = fake_client('pas du json')
    with caplog.at_level(logging.INFO, logger='stages.gemini'):
        with pytest.raises(gs.GeminiInvalidResponse):
            gs.GeminiService(GEMINI_ON).generate_json('cv_grammar', {'secret': 'Texte privé du candidat'}, {}, 'x', client=client)
    joined = ' '.join(r.getMessage() for r in caplog.records)
    assert 'cv_grammar' in joined and 'Texte privé' not in joined and 'FAKE-KEY' not in joined


def test_sdk_missing_is_reported_as_disabled(monkeypatch):
    monkeypatch.setitem(sys.modules, 'google.genai', None)
    monkeypatch.setitem(sys.modules, 'google', None)
    with pytest.raises(gs.GeminiDisabled):
        gs.GeminiService(GEMINI_ON).get_client()


# --------------------------------------------------------------- design CV
def test_palettes_custom_colors_and_contrast():
    assert set(PALETTES) == {'bleu', 'noir', 'vert', 'bordeaux', 'gris', 'violet'}
    assert validate_design(None)['palette'] == 'bleu'
    assert validate_design({'palette': 'vert'})['primary'] == PALETTES['vert']['primary']
    custom = validate_design({'palette': 'custom', 'primary': '#123456', 'secondary': '#abcdef', 'heading': '#000000',
                              'accent': '#FF0000', 'section_bg': '#FFFFFF'})
    assert custom['secondary'] == '#ABCDEF'
    for bad in ({'palette': 'inconnue'}, {'palette': 'custom', 'primary': 'red'}, {'palette': 'custom', 'primary': '#12345'}, 'texte'):
        with pytest.raises(ValueError):
            validate_design(bad)
    assert contrast_warnings({**custom, 'heading': '#FAFAFA'})


def test_color_change_keeps_all_cv_information(cv_data):
    first = validate_cv({**cv_data, 'design': {'palette': 'bordeaux'}})
    second = validate_cv({**first, 'design': {'palette': 'violet'}})
    assert {k: v for k, v in first.items() if k != 'design'} == {k: v for k, v in second.items() if k != 'design'}


# ------------------------------------------------------------------- photo
def test_photo_is_optional_validated_and_reencoded():
    assert normalize_photo(None) is None and normalize_photo({'enabled': False, 'image': 'x'}) is None
    photo = normalize_photo({'image': data_url(image_bytes()), 'shape': 'circle', 'size': 90})
    raw = base64.b64decode(photo['image'].split(',', 1)[1])
    image = Image.open(io.BytesIO(raw))
    assert image.format == 'JPEG' and image.size[0] == image.size[1] == 300 and 'exif' not in image.info
    # Données ajoutées après l'image (ex. script) : supprimées par le ré-encodage.
    polyglot = image_bytes() + b'<script>alert(1)</script>'
    cleaned = normalize_photo({'image': data_url(polyglot), 'shape': 'square', 'size': 100})
    assert b'<script>' not in base64.b64decode(cleaned['image'].split(',', 1)[1])


@pytest.mark.parametrize('value', [
    {'image': data_url(image_bytes('GIF'), 'image/gif')},
    {'image': 'data:image/svg+xml;base64,' + base64.b64encode(b'<svg onload=alert(1)>').decode()},
    {'image': data_url(b'%PDF-1.4 pas une image')},
    {'image': data_url(image_bytes(size=(50, 50)))},
    {'image': data_url(image_bytes()), 'shape': 'hexagone'},
    {'image': data_url(image_bytes()), 'size': 400},
], ids=['gif', 'svg', 'pdf_deguise', 'trop_petite', 'forme_inconnue', 'taille_hors_limites'])
def test_photo_rejections(value):
    with pytest.raises(ValueError):
        normalize_photo(value)


def test_photo_upload_endpoint_and_limits(client):
    good = client.post('/api/cvs/photo', data={'photo': (io.BytesIO(image_bytes('JPEG')), 'moi.jpg')}, content_type='multipart/form-data')
    assert good.status_code == 200 and good.json['image'].startswith('data:image/jpeg;base64,')
    exe = client.post('/api/cvs/photo', data={'photo': (io.BytesIO(b'MZ\x90\x00'), 'virus.exe')}, content_type='multipart/form-data')
    assert exe.status_code == 400
    fake = client.post('/api/cvs/photo', data={'photo': (io.BytesIO(b'not an image'), 'faux.png')}, content_type='multipart/form-data')
    assert fake.status_code == 400
    assert client.post('/api/cvs/photo', data={}, content_type='multipart/form-data').status_code == 400


def test_cv_with_photo_is_saved_encrypted_and_photo_can_be_removed(client, cv_data, app):
    data = {**cv_data, 'design': {'palette': 'vert'}, 'photo': {'image': data_url(image_bytes()), 'shape': 'circle', 'size': 80}}
    saved = client.post('/api/cvs', json={'name': 'Avec photo', 'template': 'elegant', 'data': data})
    assert saved.status_code == 201, saved.json
    loaded = client.get(f"/api/cvs/{saved.json['id']}").json
    assert loaded['template'] == 'elegant' and loaded['data']['photo']['shape'] == 'circle' and loaded['data']['design']['palette'] == 'vert'
    with sqlite3.connect(app.config['DATABASE']) as db:
        payload = db.execute('SELECT payload FROM cvs WHERE id=?', (saved.json['id'],)).fetchone()[0]
    assert b'data:image' not in payload and b'Profil' not in payload
    without = client.post('/api/cvs', json={'name': 'Sans photo', 'template': 'modern', 'data': {**data, 'photo': {'enabled': False}}})
    assert 'photo' not in client.get(f"/api/cvs/{without.json['id']}").json['data']
    assert client.get(f"/api/cvs/{saved.json['id']}/pdf").data.startswith(b'%PDF-')


# ----------------------------------------------------------------- modèles
@pytest.mark.parametrize('template', list(TEMPLATES))
def test_every_template_renders_a4_pdf_with_and_without_photo(template, cv_data):
    photo = {'image': data_url(image_bytes()), 'shape': 'square', 'size': 100}
    for data in (cv_data, {**cv_data, 'photo': photo, 'design': {'palette': 'bordeaux'}}):
        reader = PdfReader(io.BytesIO(make_pdf(data, template)))
        page = reader.pages[0]
        assert round(float(page.mediabox.width)) == 595 and round(float(page.mediabox.height)) == 842
        text = page.extract_text()
        assert 'Profil Démonstration' in text and 'Python' in text
        has_image = bool(page.images)
        assert has_image == ('photo' in data and template != 'ats')


def test_long_cv_paginates_without_error(cv_data):
    many = [{'title': f'Projet {i}', 'organization': 'École', 'period': '2025', 'description': 'Description détaillée. ' * 40} for i in range(14)]
    pdf = make_pdf({**cv_data, 'projects': many}, 'elegant')
    assert len(PdfReader(io.BytesIO(pdf)).pages) >= 2


def test_preview_and_design_endpoints(client, cv_data):
    options = client.get('/api/cvs/design-options').json
    assert len(options['templates']) == 5 and len(options['palettes']) == 6 and 'section_bg' in options['color_keys']
    assert client.post('/api/cvs/preview', json={'data': {**cv_data, 'design': {'palette': 'gris'}}, 'template': 'minimal'}).data.startswith(b'%PDF-')
    assert client.post('/api/cvs/preview', json={'data': cv_data, 'template': 'inconnu'}).status_code == 400
    check = client.post('/api/cvs/design/check', json={'design': {'palette': 'custom', 'heading': '#FFFFF0'}}).json
    assert check['warnings']
    assert client.post('/api/cvs', json={'name': 'x', 'template': 'classic', 'data': cv_data}).status_code == 201


# ------------------------------------------------------------ assistant CV
def test_cv_assistant_local_actions_propose_without_modifying(client, cv_id, cv_data):
    before = client.get(f'/api/cvs/{cv_id}').json['data']
    draft = {**cv_data, 'summary': 'je suis etudiant en developpement ,motivé', 'experience': [
        {'title': 'Stage', 'organization': 'Entreprise fictive', 'period': '2025', 'description': "J'ai fait des rapports. J'ai travaillé sur le tri des donnees. J'ai aidé à la saisie"}]}
    for action in ('analyze', 'grammar', 'descriptions', 'skills', 'summary', 'missing'):
        r = client.post(f'/api/ai/cv/{action}', json={'cv': draft})
        assert r.status_code == 200, (action, r.json)
        assert r.json['mode'] == 'local' and isinstance(r.json['suggestions'], list)
    grammar = client.post('/api/ai/cv/grammar', json={'cv': draft}).json['suggestions']
    assert any(s['proposed'] and 'développement' in s['proposed'] for s in grammar)
    assert all(s['original'] is None or s['proposed'] for s in grammar)
    optimize = client.post('/api/ai/cv/optimize', json={'cv_id': cv_id, 'offer_id': 1}).json
    assert 'python' in optimize['matched']
    assert client.post('/api/ai/cv/optimize', json={'cv_id': cv_id}).status_code == 400
    assert client.post('/api/ai/cv/inconnue', json={'cv': draft}).status_code == 404
    assert client.get(f'/api/cvs/{cv_id}').json['data'] == before


def test_cv_assistant_never_invents_numbers_or_unproven_skills():
    from backend.cv_assistant import validate_gemini
    cv = validate_cv({'name': 'A', 'title': 'Étudiant', 'summary': 'Projet Python réalisé.', 'technical': 'SQL',
                      'projects': [{'title': 'Projet', 'description': 'Analyse avec Python et Pandas.'}]})
    value = {'suggestions': [
        {'target_field': 'summary', 'original': 'Projet Python réalisé.', 'proposed': 'Projet Python réalisé pour 500 clients.', 'reason': 'x'},
        {'target_field': 'summary', 'original': 'Texte différent', 'proposed': 'Nouveau', 'reason': 'x'},
        {'target_field': 'summary', 'original': 'Projet Python réalisé.', 'proposed': 'Projet Python mené à bien.', 'reason': 'ok'}]}
    kept = validate_gemini('grammar', cv, value)
    assert len(kept) == 1 and kept[0]['proposed'] == 'Projet Python mené à bien.'
    skills = {'suggestions': [
        {'target_field': 'technical', 'original': 'SQL', 'proposed': 'SQL, Pandas', 'reason': 'x', 'evidence': 'Analyse avec Python et Pandas.'},
        {'target_field': 'technical', 'original': 'SQL', 'proposed': 'SQL, Kubernetes', 'reason': 'x', 'evidence': 'Kubernetes expert'}]}
    kept = validate_gemini('skills', cv, skills)
    assert [s['proposed'] for s in kept] == ['SQL, Pandas']


def test_cv_assistant_gemini_requires_preview_consent_and_falls_back(client, cv_data, gemini_app, monkeypatch):
    preview = client.post('/api/ai/cv/grammar/preview', json={'cv': cv_data}).json
    sent = json.dumps(preview['payload'], ensure_ascii=False)
    assert cv_data['email'] not in sent and cv_data['name'] not in sent and 'photo' not in preview['payload']['cv']
    assert client.post('/api/ai/cv/grammar', json={'cv': cv_data, 'mode': 'gemini'}).status_code == 400
    assert client.post('/api/ai/cv/grammar', json={'cv': cv_data, 'mode': 'gemini', 'consent': True, 'digest': 'faux'}).status_code == 400
    answer = {'suggestions': [{'target_field': 'summary', 'original': cv_data['summary'], 'proposed': 'Profil fictif destiné aux tests.', 'reason': 'Style'}]}
    client_mock, call = fake_client(json.dumps(answer))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: client_mock)
    ok = client.post('/api/ai/cv/grammar', json={'cv': cv_data, 'mode': 'gemini', 'consent': True, 'digest': preview['digest']}).json
    assert ok['mode'] == 'gemini' and ok['suggestions'][0]['proposed'] == 'Profil fictif destiné aux tests.'
    assert cv_data['email'] not in call.call_args.kwargs['contents']
    broken, _ = fake_client('{"suggestions": "invalide"}')
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: broken)
    gs.reset_state_for_tests()
    fallback = client.post('/api/ai/cv/grammar', json={'cv': {**cv_data, 'summary': 'autre texte'}, 'mode': 'gemini', 'consent': True,
                                                        'digest': client.post('/api/ai/cv/grammar/preview', json={'cv': {**cv_data, 'summary': 'autre texte'}}).json['digest']}).json
    assert fallback['mode'] == 'local' and fallback['fallback'] is True


# --------------------------------------------------------- assistant carrière
def test_career_tasks_local(client, cv_id):
    for task in ('explain_offer', 'application_help', 'cover_letter', 'interview', 'skills'):
        payload = {'offer_id': 1} if task == 'explain_offer' else {'cv_id': cv_id, 'offer_id': 1}
        r = client.post(f'/api/ai/career/{task}', json=payload)
        assert r.status_code == 200, (task, r.json)
        assert r.json['mode'] == 'local'
    letter = client.post('/api/ai/career/cover_letter', json={'cv_id': cv_id, 'offer_id': 1}).json['result']['letter']
    assert 'Stage Python' in letter and '[' in letter and 'Profil Démonstration' in letter
    explained = client.post('/api/ai/career/explain_offer', json={'offer_id': 1}).json['result']
    assert explained['status'] in ('active', 'expired', 'unknown') and 'python' in explained['requirements']
    assert client.post('/api/ai/career/cover_letter', json={'cv_id': cv_id}).status_code == 400
    assert client.post('/api/ai/career/explain_offer', json={'offer_id': 999}).status_code == 404


def test_career_gemini_letter_with_contact_details_is_rejected(client, cv_id, gemini_app, monkeypatch):
    base = {'cv_id': cv_id, 'offer_id': 1}
    preview = client.post('/api/ai/career/cover_letter/preview', json=base).json
    assert 'demo@example.test' not in json.dumps(preview['payload'], ensure_ascii=False)
    leaked, _ = fake_client(json.dumps({'text': 'Madame, Monsieur, ' + 'texte ' * 60 + ' appelez-moi au +212 600 000 000'}))
    monkeypatch.setattr(gs.GeminiService, 'get_client', lambda self, timeout_ms=None: leaked)
    result = client.post('/api/ai/career/cover_letter', json={**base, 'mode': 'gemini', 'consent': True, 'digest': preview['digest']}).json
    assert result['mode'] == 'local' and result['fallback'] is True


def test_career_gemini_skills_must_be_quoted_from_offers():
    from backend.career_ai import validate_gemini
    payload = {'offers_excerpts': ['Stage Python Docker et SQL à Marrakech']}
    value = {'recommendations': [{'skill': 'Docker', 'reason': 'demandé', 'evidence': 'Python Docker et SQL'},
                                 {'skill': 'Rust', 'reason': 'inventé', 'evidence': 'Rust partout'}]}
    kept = validate_gemini('skills', value, payload, {'technical': 'Python'})
    assert [x['skill'] for x in kept['recommendations']] == ['Docker']


# ----------------------------------------------------------------- matching
def test_matching_is_explainable_with_strengths_and_suggestions(client):
    profile = {'skills': ['Python', 'Pandas'], 'education': 'Data Science', 'experience': 'Projet Python', 'domain': '', 'location': 'Marrakech', 'opportunity': 'Stage'}
    result = client.post('/api/matching', json={'profile': profile}).json['results'][0]
    assert result['offer']['ID'] == 1 and result['strengths'] and result['details'] and result['score_label']
    assert any('Compétences' in d for d in result['details'])
    assert 'sql' in result['missing'] and any('sql' in s for s in result['suggestions'])


def test_corpus_idf_matches_reference_formula():
    import math
    from collections import Counter
    from backend.matching import cosine, tokens
    corpus = ['python sql données', 'marketing seo', 'java sql']
    def reference(a, b):
        aa, bb = Counter(tokens(a)), Counter(tokens(b))
        sets = [set(tokens(c)) for c in corpus]
        vec = lambda c: {t: n * (math.log((len(sets) + 1) / (1 + sum(t in s for s in sets))) + 1) for t, n in c.items()}
        va, vb = vec(aa), vec(bb)
        return sum(v * vb.get(t, 0) for t, v in va.items()) / (math.sqrt(sum(v * v for v in va.values())) * math.sqrt(sum(v * v for v in vb.values())))
    assert abs(cosine('python sql', 'python sql données', corpus) - reference('python sql', 'python sql données')) < 1e-12


def test_city_is_inferred_from_offer_text_and_flagged():
    from backend.matching import rank
    offer = {'ID': 9, 'Titre': 'Stage Python à Marrakech', 'Description': 'Python et SQL. ' * 20, 'Type contrat': 'Stage'}
    result = rank({'skills': ['Python'], 'location': 'Marrakech', 'opportunity': 'Stage'}, [offer],
                  {'skills': 40, 'education': 25, 'experience': 15, 'location': 10, 'opportunity': 10})[0]
    assert result['components']['location'] == 100 and result['city_inferred'] is True and 'déduite' in result['limitations']


def test_vocabulary_avoids_french_false_positives():
    from backend.matching import skills_from
    assert 'tableau software' not in skills_from('Création de tableaux de bord et tableau Excel')
    assert 'java' not in skills_from('Développeur JavaScript') and 'javascript' in skills_from('Développeur JavaScript')
    assert 'c#' in skills_from('Stage C# et .NET') and 'node.js' in skills_from('API Node.js')


# ----------------------------------------------------------------- scrapers
from backend.scrapers import quality
from backend.scrapers.base import BlockedByProtection, PoliteFetcher, RobotsDisallowed, PageUnavailable


def test_quality_dates_deadlines_cities_and_urls():
    assert quality.normalize_date('Tue, 10 Nov 2026 08:00:00 GMT') == '2026-11-10'
    assert quality.normalize_date('12/03/2026') == '2026-03-12'
    assert quality.normalize_date('3 mars 2026') == '2026-03-03'
    assert quality.normalize_date('15 دجنبر 2026') == '2026-12-15'
    assert quality.normalize_date('31/02/2026') is None and quality.normalize_date('bientôt') is None
    assert quality.deadline_from('Date limite : 20/12/2026') == '2026-12-20'
    assert quality.deadline_from('Publié le 20/12/2026') is None
    assert quality.city_from('مباراة بمراكش') is None and quality.city_from('Concours Marrakech') == 'Marrakech'
    assert quality.city_from('مباراة في مراكش') == 'Marrakech'
    assert quality.valid_url('https://jawb.ma/offre/1', ('jawb.ma',)) and not quality.valid_url('http://jawb.ma/x', ('jawb.ma',))
    assert not quality.valid_url('https://evil.example/jawb.ma', ('jawb.ma',))
    assert quality.opportunity_type('Stage PFE Data') == 'Stage PFE' and quality.opportunity_type('مباراة لتوظيف') == 'Concours'


class FakeResponse:
    def __init__(self, text='', status=200, headers=None):
        self.text, self.status_code, self.headers = text, status, headers or {}
        self.content = text.encode()


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kwargs):
        self.calls.append(url)
        assert kwargs['allow_redirects'] is False and kwargs['timeout']
        for prefix, response in self.routes.items():
            if url.startswith(prefix):
                return response
        return FakeResponse(status=404)


RSS = '''<?xml version="1.0"?><rss><channel>
<item><title>Stage PFE Data chez Atlas Digital</title><link>https://jawb.ma/offres/1</link><pubDate>Tue, 10 Nov 2026 08:00:00 GMT</pubDate>
<description>Stage à Marrakech. Date limite : {future}. Python et SQL.</description></item>
<item><title>Stage marketing</title><link>https://jawb.ma/offres/2</link><description>Marrakech. Date limite : 01/01/2020</description></item>
<item><title>Doublon</title><link>https://jawb.ma/offres/1/</link></item>
<item><title>Lien externe</title><link>https://autre-site.example/offre</link></item>
<item><title></title><link>https://jawb.ma/offres/3</link></item>
</channel></rss>'''.replace('{future}', (date.today() + timedelta(days=20)).strftime('%d/%m/%Y'))


def fetcher_for(routes):
    return PoliteFetcher('https://jawb.ma', session=FakeSession(routes), min_delay=0, sleep=lambda s: None)


def test_fetcher_respects_robots_protections_and_redirects():
    blocked = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse('User-agent: *\nDisallow: /rss.xml')})
    with pytest.raises(RobotsDisallowed):
        blocked.fetch('https://jawb.ma/rss.xml?ville=Marrakech')
    captcha = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse(''), 'https://jawb.ma/rss.xml': FakeResponse('<div class="g-recaptcha"></div>')})
    with pytest.raises(BlockedByProtection):
        captcha.fetch('https://jawb.ma/rss.xml')
    forbidden = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse(''), 'https://jawb.ma/rss.xml': FakeResponse(status=403)})
    with pytest.raises(BlockedByProtection):
        forbidden.fetch('https://jawb.ma/rss.xml')
    moved = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse(''), 'https://jawb.ma/rss.xml': FakeResponse(status=302, headers={'Location': 'https://evil.example/'})})
    with pytest.raises(PageUnavailable):
        moved.fetch('https://jawb.ma/rss.xml')
    with pytest.raises(ValueError):
        fetcher_for({}).fetch('https://evil.example/rss.xml')


def test_jawb_collect_quality_without_descriptions():
    from backend.scrapers import jawb_scraper
    fetcher = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse('User-agent: *\nAllow: /'), 'https://jawb.ma/rss.xml': FakeResponse(RSS)})
    result = jawb_scraper.collect({'city': 'Marrakech'}, fetcher)
    assert result['robots_allowed'] is True and result['duplicates'] == 1 and len(result['errors']) == 2
    first, second = result['records']
    assert first['organization'] == 'Atlas Digital' and first['city'] == 'Marrakech' and first['opportunity_type'] == 'Stage PFE'
    assert first['status'] == 'active' and first['description'] == '' and first['published_at'] == '2026-11-10'
    assert second['status'] == 'expired' and second['verification_status'] == 'expiree'


def test_wadifa_requires_explicit_feed_url():
    from backend.scrapers import wadifa_scraper
    with pytest.raises(ValueError):
        wadifa_scraper.collect({'feed_url': ''})
    with pytest.raises(ValueError):
        wadifa_scraper.collect({'feed_url': 'https://wadifa.info.evil.example/feed'})


def test_scraper_pipeline_locked_then_staged_then_reviewed_import(client, app, monkeypatch):
    from backend.scrapers import pipeline
    path = app.config['DATABASE']
    assert client.post('/api/scrapers/jawb/run', json={}).status_code == 403
    assert client.post('/api/scrapers/jawb/config', json={'enabled': True}).status_code == 400
    ok = client.post('/api/scrapers/jawb/config', json={'enabled': True, 'permission_ref': 'Accord écrit Jawb n°TEST',
                                                        'consultation_allowed': True, 'storage_allowed': True, 'display_allowed': True})
    assert ok.status_code == 200
    assert client.get('/api/scrapers').json['sources']['jawb']['ready'] is False  # collecte externe globale désactivée
    client.post('/api/collect/settings', json={'external_enabled': True})
    fake = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse(''), 'https://jawb.ma/rss.xml': FakeResponse(RSS)})
    monkeypatch.setattr('backend.scrapers.jawb_scraper.PoliteFetcher', lambda *a, **k: fake)
    with sqlite3.connect(path) as db:
        before = db.execute('SELECT COUNT(*) FROM offres').fetchone()[0]
    run = client.post('/api/scrapers/jawb/run', json={})
    assert run.status_code == 201 and run.json['staged'] == 2, run.json
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offres').fetchone()[0] == before
    details = client.get(f"/api/collect/runs/{run.json['id']}").json
    assert all(item['decision'] == 'pending' and item['offer']['description'] == '' for item in details['staged'])
    for item in details['staged']:
        client.post(f"/api/collect/runs/{run.json['id']}/staged/{item['id']}/decision", json={'decision': 'approved'})
    assert client.post(f"/api/collect/runs/{run.json['id']}/import", json={'sources': ['Jawb.ma']}).status_code == 400
    assert client.post(f"/api/collect/runs/{run.json['id']}/import", json={'sources': ['Autre'], 'rights_confirmed': True}).status_code == 400
    imported = client.post(f"/api/collect/runs/{run.json['id']}/import", json={'sources': ['Jawb.ma'], 'rights_confirmed': True})
    assert imported.status_code == 200 and imported.json['imported'] == 2, imported.json
    with sqlite3.connect(path) as db:
        rows = db.execute("SELECT statut_offre,\"Lien public\" FROM offres WHERE source='Jawb.ma' ORDER BY \"ID\"").fetchall()
    assert sorted(r[0] for r in rows) == ['active', 'expired'] and all(r[1].startswith('https://jawb.ma/') for r in rows)
    offers = client.get('/api/offres').json
    assert [o['availability'] for o in offers if o.get('source') == 'Jawb.ma'].count('expired') == 1


def test_scraper_network_failure_is_logged_not_raised(app, monkeypatch, client):
    from backend.scrapers import pipeline
    client.post('/api/collect/settings', json={'external_enabled': True})
    client.post('/api/scrapers/jawb/config', json={'enabled': True, 'permission_ref': 'ref', 'consultation_allowed': True,
                                                   'storage_allowed': True, 'display_allowed': True})
    down = fetcher_for({'https://jawb.ma/robots.txt': FakeResponse(''), 'https://jawb.ma/rss.xml': FakeResponse(status=503)})
    monkeypatch.setattr('backend.scrapers.jawb_scraper.PoliteFetcher', lambda *a, **k: down)
    result = client.post('/api/scrapers/jawb/run', json={})
    assert result.status_code == 502 and result.json['status'] == 'failed' and '503' in result.json['error']
    assert client.get(f"/api/collect/runs/{result.json['id']}").json['run']['status'] == 'failed'


# ------------------------------------------------- base, performance, garde
def test_phase10_index_migration_backs_up_and_keeps_data(legacy_database, tmp_path, app):
    path = app.config['DATABASE']
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] >= 7  # later additive migrations raise it further
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        assert {'idx_offres_publication', 'idx_candidatures_statut', 'idx_staging_run_decision'} <= names
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0] == 5
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert list(Path(app.config['BACKUP_DIR']).glob('avant_phase10_index_*.db'))


def test_offers_pagination_header(client):
    page = client.get('/api/offres?page=1&per_page=2')
    assert page.status_code == 200 and len(page.json) == 2 and page.headers['X-Total-Count'] == '3'
    assert client.get('/api/offres?page=abc').status_code == 400
    assert len(client.get('/api/offres').json) == 3


def test_app_starts_without_dash(monkeypatch, legacy_database, tmp_path):
    monkeypatch.setitem(sys.modules, 'dash', None)
    monkeypatch.delitem(sys.modules, 'backend.analytics', raising=False)
    from backend.web import create_app
    app = create_app({'DATABASE': str(legacy_database), 'PRIVATE_DIR': str(tmp_path / 'p'), 'BACKUP_DIR': str(tmp_path / 'b'), 'TESTING': True})
    client = app.test_client()
    assert client.get('/health').json == {'status': 'ok'}
    info = client.get('/api/auth/session').json
    client.post('/api/auth/setup', json={'password': 'Mot-de-passe-test-123!'}, headers={'X-CSRF-Token': info['csrf']})
    assert client.get('/analytics/').status_code == 503


def test_new_pages_are_served_and_csp_kept(client):
    for path in ('/assistant-carriere.html', '/js/cv-studio.js', '/js/career-ai.js', '/css/studio.css'):
        assert client.get(path).status_code == 200, path
    for source in ('/js/cv-studio.js', '/js/career-ai.js'):
        assert 'innerHTML' not in client.get(source).data.decode('utf-8')
    assert "script-src 'self' https://maps" in client.get('/cv.html').headers['Content-Security-Policy']


def test_public_demo_allows_local_ai_only(tmp_path):
    from backend.web import create_app
    from scripts.create_public_demo_database import create_public_demo_database
    database = Path(create_public_demo_database(tmp_path / 'demo.db'))
    app = create_app({'DATABASE': str(database), 'PRIVATE_DIR': str(tmp_path / 'private'), 'BACKUP_DIR': str(tmp_path / 'backups'),
                      'PUBLIC_DEMO_MODE': True, 'PUBLIC_DEMO_DATA_CONFIRMED': True, 'DISABLE_BACKGROUND_SCHEDULER': True, 'TESTING': True})
    client = app.test_client()
    headers = {'X-CSRF-Token': client.get('/api/auth/session').json['csrf']}
    cv = {'name': 'Démo', 'title': 'Étudiant', 'technical': 'Python'}
    assert client.post('/api/ai/cv/analyze', json={'cv': cv}, headers=headers).status_code == 200
    assert client.post('/api/ai/cv/grammar', json={'cv': cv, 'mode': 'gemini'}, headers=headers).status_code == 403
    assert client.post('/api/ai/cv/grammar/preview', json={'cv': cv}, headers=headers).status_code == 403
    assert client.post('/api/scrapers/jawb/run', json={}, headers=headers).status_code == 403


def test_pdf_export_token_is_bound_to_its_session(client, app, cv_data):
    token = client.post('/api/cvs/export', json={'data': cv_data, 'template': 'modern'}).json['token']
    other = app.test_client()
    info = other.get('/api/auth/session').json
    other.post('/api/auth/login', json={'password': 'Mot-de-passe-test-123!'}, headers={'X-CSRF-Token': info['csrf']})
    assert other.get('/api/cvs/export/' + token).status_code == 404
    second = client.post('/api/cvs/export', json={'data': cv_data, 'template': 'modern'}).json['token']
    assert client.get('/api/cvs/export/' + second).data.startswith(b'%PDF-')


def test_deleting_missing_alert_returns_404(client):
    assert client.delete('/api/alerts/999999').status_code == 404
