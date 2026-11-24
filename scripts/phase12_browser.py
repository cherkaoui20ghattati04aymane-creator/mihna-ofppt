"""Exercise the real gateway and browser against a disposable database.

Run from the project root. Omit --record for QA; use --record only after tests pass.
"""
import argparse
import os
from pathlib import Path
import re
import runpy
import secrets
import subprocess
import sys
import tempfile
import threading

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PAGES = ('alertes','analyses','assistant-carriere','candidatures','carte','collecte',
         'competences','cv','entreprise?id=1','entreprises','entretiens','envoyer_cv',
         'index','matching','offre?id=1','offres','parametres','parcours','profile',
         'qualite-cv','recherche-ia','sauvegardes','statistiques')
EMAIL = 'camille.validation@example.test'


class Quiet(WSGIRequestHandler):
    def log(self, *_args):
        pass


def encode_video(source, target):
    import imageio_ffmpeg
    target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(source),
                    '-c:v','libx264','-crf','23','-pix_fmt','yuv420p',
                    '-movflags','+faststart',str(target)],check=True)


def listen(app):
    server = make_server('127.0.0.1',0,app,threaded=True,request_handler=Quiet)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}'


def exercise(page, browser, url, output, filming):
    password='MihnaQA-'+secrets.token_hex(12)
    errors=[]
    tiles=set()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('response',lambda r:tiles.add(r.status) if 'tile.openstreetmap.org/' in r.url else None)

    def chapter(label):
        if not filming:
            return
        page.evaluate("""text => {
            document.getElementById('demo-label')?.remove();
            const label=document.createElement('aside');
            label.id='demo-label';
            label.style.cssText='position:fixed;bottom:12px;left:12px;z-index:100000;background:#17203a;color:#fff;padding:8px 14px;border-radius:7px;font:600 14px system-ui;pointer-events:none';
            label.textContent='Mihna · '+text+' · Compte isolé';
            document.body.append(label);
        }""",label)
        page.wait_for_timeout(1100)

    def go(path):
        assert page.goto(url+path,wait_until='domcontentloaded').status == 200
        if path.endswith('.html') or '.html?' in path:
            page.locator('main .page-footer').wait_for(timeout=15000)

    def button(label):
        return page.get_by_role('button',name=label,exact=True)

    def register(tab,email):
        tab.goto(url+'/register')
        for key,value in {'first_name':'Camille','last_name':'Validation','email':email,
                          'password':password,'confirm_password':password}.items():
            tab.locator('#'+key).fill(value)
        tab.locator('button[type=submit]').click()
        tab.wait_for_url('**/account')

    go('/login')
    chapter('01 · Accueil')
    page.goto(url+'/register')
    chapter('02 · Inscription')
    register(page,EMAIL)
    chapter('Compte créé')
    button('Se déconnecter').click()
    page.wait_for_url('**/login')
    assert page.request.get(url+'/api/offres').status==401
    page.locator('#email').fill(EMAIL)
    page.locator('#password').fill('Invalid-Pass-12345')
    page.locator('button[type=submit]').click()
    page.locator('[role=alert]').first.wait_for()
    page.locator('#password').fill(password)
    page.locator('button[type=submit]').click()
    page.wait_for_url('**/index.html')
    chapter('03 · Connexion')
    go('/profile.html')
    assert page.get_by_label('Prénom',exact=True).input_value()=='Camille'
    for key,value in {'Ville':'Marrakech','Pays':'Maroc','Téléphone':'0600000000','Titre professionnel':'Analyste de données',
                      'Résumé professionnel':'Je réalise des projets de formation en Python et SQL.'}.items():
        page.get_by_label(key,exact=False).first.fill(value)
    page.get_by_label('Compétences techniques',exact=False).first.fill('Python, SQL, Git')
    page.get_by_label('Langues',exact=False).first.fill('Français, arabe')
    button('Enregistrer mon profil').click()
    page.get_by_text('Profil enregistré dans votre espace.').wait_for()
    page.reload()
    assert page.get_by_label('Pays',exact=True).input_value()=='Maroc'
    chapter('04 · Profil enregistré')

    go('/cv.html')
    chapter('05 · Studio CV')
    page.get_by_label('Nom de cette version',exact=True).fill('CV Analyse de données')
    button('Valider et enregistrer cette version').click()
    page.wait_for_url('**/cv.html?version=*')
    cv_id=int(page.url.rsplit('=',1)[1])
    page.reload()
    page.get_by_text('Version chargée.').wait_for()
    page.get_by_label('Nom de cette version',exact=True).fill('CV Analyse de données · version revue')
    button('Valider et enregistrer cette version').click()
    page.get_by_text('Version enregistrée et chiffrée.').wait_for()
    assert page.url.endswith('='+str(cv_id))
    button('Nouveau CV').click()
    page.get_by_label('Nom de cette version',exact=True).fill('CV Projet Python')
    button('Valider et enregistrer cette version').click()
    page.wait_for_url('**/cv.html?version=*')
    assert not page.url.endswith('='+str(cv_id))
    page.get_by_label('Charger un CV',exact=True).select_option(str(cv_id))
    page.get_by_text('Version chargée.').first.wait_for()
    chapter('CV modifié et rouvert')
    with page.expect_download() as event:
        button('Télécharger le PDF').click()
    pdf=output/'original.pdf'
    event.value.save_as(pdf)
    assert pdf.read_bytes().startswith(b'%PDF')
    page.get_by_text('Aperçu texte accessible',exact=True).click()
    page.get_by_text('Aperçu texte accessible',exact=True).scroll_into_view_if_needed()
    chapter('06 · PDF téléchargé et aperçu')

    go('/offres.html')
    page.get_by_role('searchbox',name='Rechercher').fill('Python')
    page.locator('.offer-list .offer-link').first.wait_for()
    chapter('07 · Recherche d’opportunités')
    page.locator('.offer-list .offer-link').first.click()
    page.wait_for_url('**/offre.html?id=1')
    page.locator('main .page-footer').wait_for()
    button('Sauvegarder').click()
    chapter('08 · Offre, provenance et sauvegarde')
    go('/entreprises.html')
    page.locator('.company-card').first.click()
    page.locator('main .page-footer').wait_for()
    chapter('09 · Répertoire et fiche entreprise')

    go('/matching.html')
    page.get_by_label('CV enregistré',exact=True).select_option(str(cv_id))
    expect(page.get_by_role('textbox',name='Compétences',exact=True)).to_have_value(re.compile('Python'))
    button('Lancer le matching local').click()
    page.get_by_text('Très compatibles',exact=True).wait_for()
    page.get_by_text('Très compatibles',exact=True).scroll_into_view_if_needed()
    chapter('10 · Classement local et explications')

    go('/cv.html?tailor=1&source='+str(cv_id))
    page.get_by_text('Brouillon adapté chargé.',exact=False).wait_for()
    button('Valider et enregistrer le CV adapté').click()
    page.wait_for_url('**/cv.html?version=*')
    tailored=int(page.url.rsplit('=',1)[1])
    assert tailored!=cv_id
    chapter('11 · CV adapté, original conservé')
    with page.expect_download() as event:
        button('Télécharger le PDF').click()
    event.value.save_as(output/'tailored.pdf')

    go('/offre.html?id=1')
    button('Postuler').first.click()
    dialog=page.get_by_role('dialog')
    assert dialog.get_by_label('CV à utiliser').input_value()==str(tailored)
    dialog.get_by_text('Je confirme l’enregistrement de cette offre',exact=False).click()
    dialog.get_by_role('button',name='Enregistrer à préparer').click()
    dialog.wait_for(state='hidden')
    go('/candidatures.html')
    page.get_by_role('combobox',name='Statut de',exact=False).first.select_option('Prête à envoyer')
    page.get_by_text('Statut et historique mis à jour.').wait_for()
    chapter('12 · Candidature préparée et suivie')

    go('/assistant-carriere.html?offer=1&task=interview')
    page.locator('.interview-question textarea').first.fill('J’ai réalisé un projet de formation avec Python et SQL.')
    button('Enregistrer et reprendre plus tard').click()
    page.get_by_text('Brouillon enregistré.').wait_for()
    page.reload()
    button('Reprendre le brouillon').click()
    assert page.locator('.interview-question textarea').first.input_value().startswith('J’ai réalisé')
    chapter('13 · Entretien repris depuis un brouillon')
    button('Évaluer mes réponses et enregistrer la simulation').click()
    page.get_by_text('Simulation enregistrée dans votre espace.').wait_for()
    go('/entretiens.html')
    chapter('14 · Historique d’entretien')
    for path,label in (
        ('/index.html','15 · Tableau de bord'),
        ('/statistiques.html','16 · Analyse des candidatures'),
        ('/competences.html','17 · Analyse des écarts'),
        ('/parcours.html','18 · Feuille de route'),
        ('/qualite-cv.html','19 · Qualité du CV'),
        ('/sauvegardes.html','20 · Offres sauvegardées'),
        ('/alertes.html','21 · Alertes et préférences'),
        ('/collecte.html','22 · Sources de données'),
        ('/carte.html','23 · Carte'),
    ):
        go(path)
        chapter(label)
    go('/analytics/')
    page.locator('#react-entry-point .dash-graph').first.wait_for(timeout=20000)
    chapter('24 · Dash connecté à SQLite')

    go('/profile.html')
    page.locator('#profile-theme').select_option('dark')
    button('Enregistrer mon profil').click()
    page.locator('html.dark').wait_for(state='attached')
    page.reload()
    page.locator('html.dark').wait_for(state='attached')
    page.set_viewport_size({'width':390,'height':820})
    go('/index.html')
    chapter('25 · Affichage mobile et thème sombre')
    if not filming:
        for width,height in ((1280,900),(820,950),(390,820)):
            page.set_viewport_size({'width':width,'height':height})
            for name in PAGES:
                slug,_,query=name.partition('?')
                go('/'+slug+'.html'+('?' + query if query else ''))
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'),(width,name)
            print(f'Responsive: {len(PAGES)} pages at {width}px')
        with browser.new_context() as alternate:
            other=alternate.new_page()
            register(other,'other.validation@example.test')
            assert other.request.get(url+f'/api/cvs/{cv_id}').status==404
            assert not other.request.get(url+'/api/career/interview-drafts').json()['items']
        assert not errors,errors
        print(f'Browser workflow: passed; JavaScript errors: {len(errors)}; OpenStreetMap HTTP statuses: {sorted(tiles)}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',type=Path,help='MP4 output path')
    parser.add_argument('--pdf-evidence',type=Path,help='Optional isolated PDF evidence directory')
    args=parser.parse_args()
    os.chdir(ROOT)
    with tempfile.TemporaryDirectory(prefix='mihna-phase12-') as temp:
        root=Path(temp)
        secret=secrets.token_urlsafe(48)
        os.environ.update(AUTH_PROFILE='multi_user',AUTH_ALLOW_REGISTRATION='true',AUTH_MULTI_USER_MODE='true',
            AUTH_CONFIG_FILE=str(root/'absent.env'),AUTH_SESSION_SECRET=secret,AUTH_INTERNAL_SECRET=secret,
            AUTH_USER_DATA_ROOT=str(root/'workspaces'),DISABLE_BACKGROUND_SCHEDULER='true',SMTP_ENABLED='false',
            PUBLIC_DEMO_MODE='false',GEMINI_SEARCH_ENABLED='false',GEMINI_ENABLED='false')
        db=runpy.run_path('tests/conftest.py')['legacy_database'].__wrapped__(root)
        from backend.web import create_app
        from auth_gateway.app import create_app as gateway
        backend,backend_url=listen(create_app({'DATABASE':str(db),'PRIVATE_DIR':str(root/'private'),
                                               'BACKUP_DIR':str(root/'backup')}))
        public,url=listen(gateway({'AUTH_BACKEND_URL':backend_url,
                                   'AUTH_DATABASE_URL':'sqlite:///'+(root/'auth.db').as_posix()}))
        output=args.pdf_evidence or root
        output.mkdir(parents=True,exist_ok=True)
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(channel='msedge',headless=True)
                options={'viewport':{'width':1280,'height':900},'accept_downloads':True}
                if args.record:
                    options.update(record_video_dir=str(root/'recording'),record_video_size={'width':1280,'height':900})
                with browser.new_context(**options) as context:
                    page=context.new_page()
                    video=page.video
                    exercise(page,browser,url,output,args.record is not None)
                if video and args.record:
                    encode_video(Path(video.path()),args.record)
                    print(f'MP4 encoded: {args.record.stat().st_size} bytes',flush=True)
                browser.close()
        finally:
            public.shutdown()
            backend.shutdown()


if __name__=='__main__':
    main()
