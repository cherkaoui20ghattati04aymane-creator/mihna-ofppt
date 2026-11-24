# Parcours navigateur v2 (Chrome + Playwright). Lancer le serveur sur une COPIE de la base, puis :
#   python tests/e2e_v2_navigateur.py   (non collecté par pytest)
"""Parcours navigateur réel (Chrome) : CV Studio, photo, couleurs, IA locale, assistant carrière, matching, responsive."""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

import os
BASE = os.environ.get('E2E_BASE', 'http://127.0.0.1:5077')
OUT = Path(os.environ.get('E2E_OUT', 'test-results/e2e_v2')); OUT.mkdir(parents=True, exist_ok=True)
PHOTO = os.environ.get('E2E_PHOTO', 'tests/fixtures/photo_synthetique.png')
report = {'checks': [], 'console_errors': [], 'failed': []}


def check(name, cond, detail=''):
    (report['checks'] if cond else report['failed']).append(name + (f' — {detail}' if detail else ''))
    print(('OK   ' if cond else 'FAIL ') + name, detail, flush=True)


with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('E2E_CHANNEL', 'chrome'))
    ctx = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    page = ctx.new_page()
    page.on('console', lambda m: report['console_errors'].append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: report['console_errors'].append('pageerror: ' + str(e)))
    page.on('response', lambda r: report['console_errors'].append(f'HTTP {r.status} {r.url}') if r.status >= 400 else None)

    # 1. Authentification (création du mot de passe sur une copie)
    page.goto(BASE + '/index.html')
    page.get_by_label('Mot de passe').fill('Mot-de-passe-E2E-2026!')
    page.locator('.auth-dialog button[type=submit]').click()
    page.get_by_role('heading', name='Bonjour, prêt pour la suite ?').wait_for()
    check('Création du mot de passe et accueil', True)

    # 2. Navigation de toutes les pages
    pages = ['index', 'entreprises', 'offres', 'matching', 'cv', 'assistant-carriere', 'candidatures', 'carte', 'collecte', 'recherche-ia', 'alertes']
    for name in pages:
        page.goto(f'{BASE}/{name}.html')
        page.wait_for_selector('.page-title h1', timeout=15000)
        check(f'Page {name}.html chargée', 'Impossible de charger' not in page.inner_text('main'))

    # 3. CV Studio
    page.goto(BASE + '/cv.html')
    page.get_by_role('button', name='Charger un exemple fictif').click()
    page.wait_for_selector('.cv-live-preview:not([hidden])', timeout=20000)
    check('Aperçu PDF généré', True)
    page.get_by_role('radio', name='Élégant · deux colonnes').click()
    page.locator('.palette', has_text='Bordeaux élégant').click()
    page.wait_for_timeout(1500)
    name_value = page.get_by_label('Nom complet *').input_value()
    check('Changement de modèle/couleurs sans perte de données', name_value == 'Profil Démonstration', name_value)
    page.locator('summary', has_text='Personnaliser chaque couleur').click()
    page.get_by_label('Couleur des titres (hexadécimal)').fill('#FFFFF0'); page.get_by_label('Couleur des titres (hexadécimal)').press('Enter')
    page.wait_for_selector('.notice.warning', timeout=8000)
    check('Avertissement de contraste affiché', True)
    page.get_by_role('button', name='Revenir à la palette Bleu professionnel').click()

    # Photo : upload, recadrage, forme, suppression
    page.locator('input[type=file][accept^="image"]').set_input_files(PHOTO)
    page.wait_for_selector('.photo-editor:not([hidden])', timeout=10000)
    page.get_by_label('Zoom').fill('1.6')
    page.get_by_label('Forme de la photo').select_option('square')
    page.wait_for_timeout(1800)
    shape = page.evaluate("document.querySelector('.photo-canvas').className")
    check('Photo vérifiée, recadrée et forme carrée', 'square' in shape, shape)
    page.screenshot(path=str(OUT / '01_cv_studio_desktop.png'), full_page=False)
    page.get_by_role('button', name='Supprimer la photo').click()
    hidden = page.evaluate("document.querySelector('.photo-editor').hidden")
    check('Suppression de la photo', hidden is True)
    page.locator('input[type=file][accept^="image"]').set_input_files(PHOTO)
    page.wait_for_selector('.photo-editor:not([hidden])', timeout=10000)
    page.wait_for_timeout(1200)

    # Assistant IA local : correction proposée puis acceptée
    page.get_by_label('Profil / résumé').fill('je suis etudiant en developpement web ,motivé')
    page.get_by_role('button', name='Corriger l’orthographe').click()
    page.wait_for_selector('.suggestion .after', timeout=10000)
    page.locator('.suggestion', has_text='Profil / résumé').get_by_role('button', name='Accepter').click()
    summary = page.get_by_label('Profil / résumé').input_value()
    check('Suggestion IA appliquée seulement après « Accepter »', 'développement' in summary and summary[0] == 'J', summary)
    page.get_by_role('button', name='Analyser mon CV').click()
    page.wait_for_selector('.cv-score .score', timeout=10000)
    check('Analyse locale du CV (score de complétude)', True, page.inner_text('.cv-score .score'))
    page.get_by_label('Offre à comparer').select_option(index=1)
    page.get_by_role('button', name='Optimiser pour une offre').click()
    page.wait_for_timeout(1200)
    check('Optimisation pour une offre', 'Erreur' not in page.inner_text('.ai-results'))

    # Sauvegarde et téléchargement PDF
    page.get_by_label('Nom de cette version').fill('Version E2E photo')
    page.get_by_role('button', name='Enregistrer cette version').click()
    page.wait_for_selector('.toast', timeout=8000)
    with page.expect_download() as download:
        page.get_by_role('button', name='Télécharger le PDF').click()
    pdf_path = OUT / 'cv_e2e.pdf'; download.value.save_as(pdf_path)
    check('Téléchargement du PDF', pdf_path.read_bytes().startswith(b'%PDF-'), f'{pdf_path.stat().st_size} octets')
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / '02_cv_assistant.png'), full_page=True)

    # 4. Assistant carrière
    page.goto(BASE + '/assistant-carriere.html')
    page.wait_for_selector('.task-tab')
    page.get_by_label('Offre', exact=True).select_option(index=1)
    page.get_by_role('tab', name='Lettre de motivation').click()
    page.get_by_role('button', name='Lancer').click()
    page.wait_for_selector('textarea.letter', timeout=10000)
    letter = page.input_value('textarea.letter')
    check('Lettre de motivation locale', 'Madame, Monsieur' in letter and 'Profil Démonstration' in letter)
    page.get_by_role('tab', name='Préparer l’entretien').click(); page.get_by_role('button', name='Lancer').click()
    page.wait_for_selector('.career-output .suggestion h3', timeout=10000)
    check('Préparation d’entretien', page.locator('.career-output .suggestion').count() >= 4)
    for tab in ('Expliquer une offre', 'Aide à la candidature', 'Compétences à développer'):
        page.get_by_role('tab', name=tab).click(); page.get_by_role('button', name='Lancer').click()
        try:
            page.wait_for_selector('.career-output .section-info', timeout=8000)
        except Exception:
            pass
        check(f'Assistant carrière : {tab}', 'Mode : local' in page.inner_text('.career-output'), page.inner_text('.career-output')[:200].replace('\n',' | '))
    page.screenshot(path=str(OUT / '03_assistant_carriere.png'), full_page=True)

    # 5. Matching explicable
    page.goto(BASE + '/matching.html')
    page.wait_for_selector('.page-title h1')
    page.goto(BASE + '/offres.html'); page.wait_for_selector('.offer')
    href = page.locator('.offer a', has_text='Expliquer / préparer').first.get_attribute('href')
    check('Bouton « Expliquer / préparer » sur les offres', href and 'assistant-carriere.html?offer=' in href, href)

    # 5b. Centre de collecte : connecteurs verrouillés par défaut
    page.goto(BASE + '/collecte.html'); page.wait_for_selector('#collection-scrapers', timeout=15000)
    txt = page.inner_text('#collection-scrapers')
    check('Connecteurs Jawb/Wadifa affichés et verrouillés', 'Verrouillé' in txt and 'Jawb.ma' in txt and 'Wadifa.info' in txt)
    page.locator('#collection-scrapers').screenshot(path=str(OUT / '05_connecteurs.png'))

    # 6. Mobile
    mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, storage_state=ctx.storage_state())
    m = mobile.new_page(); m.on('pageerror', lambda e: report['console_errors'].append('mobile pageerror: ' + str(e)))
    for name in ('cv', 'assistant-carriere', 'offres'):
        m.goto(f'{BASE}/{name}.html'); m.wait_for_selector('.page-title h1', timeout=15000); m.wait_for_timeout(800)
        overflow = m.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        check(f'Mobile 390px sans débordement horizontal : {name}', overflow <= 2, f'{overflow}px')
        m.screenshot(path=str(OUT / f'04_mobile_{name}.png'), full_page=False)
    browser.close()

report['console_errors'] = [e for e in report['console_errors'] if 'favicon' not in e]
(OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
print(json.dumps({'ok': len(report['checks']), 'failed': report['failed'], 'console_errors': report['console_errors']}, ensure_ascii=False, indent=1))
