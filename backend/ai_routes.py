"""Routes de l'assistance IA (CV + carrière) et de la personnalisation du CV.

Mode local par défaut. Le mode Gemini exige : un aperçu exact des données transmises
(``/preview``), puis un consentement explicite accompagné de l'empreinte de cet aperçu.
Toute erreur Gemini renvoie la version locale avec un message clair.
"""
import hashlib
import json

from flask import Blueprint, jsonify, request

from . import career_ai, cv_assistant
from .api import body, config, get_cv, get_offer, offers, companies
from .application_service import resolve_channel
from .cv_design import (COLOR_KEYS, COLOR_LABELS, PALETTES, PHOTO_MAX_BYTES, TEMPLATES, TEMPLATES_WITHOUT_PHOTO,
                        contrast_warnings, sanitize_upload, validate_design)
from .cv_service import validate_cv
from .services.gemini_service import GeminiError, GeminiService

ai = Blueprint('ai', __name__, url_prefix='/api')

INTERVIEW_FEEDBACK_SCHEMA={'type':'object','properties':{'answer_feedback':{'type':'array','items':{'type':'object','properties':{
    'index':{'type':'integer'},'feedback':{'type':'string'},'focus':{'type':'string'}},'required':['index','feedback','focus']}}},
    'required':['answer_feedback']}


def _digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _draft_cv(data):
    """CV issu d'une version enregistrée (cv_id) ou du brouillon de la page (cv), sans la photo."""
    if type(data.get('cv_id')) is int:
        cv = get_cv(data['cv_id'])['data']
        cv.pop('photo', None)
        return cv
    raw = data.get('cv')
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError('Brouillon de CV invalide.')
    raw = {k: v for k, v in raw.items() if k != 'photo'}
    placeholder = {k: raw.get(k) or '—' for k in ('name', 'title')}
    cv = validate_cv({**raw, **placeholder})
    for key in ('name', 'title'):
        if not raw.get(key):
            cv[key] = ''
    return cv


def _offer(data, required=False):
    ident = data.get('offer_id')
    if ident in (None, ''):
        if required:
            raise ValueError('Choisissez une offre.')
        return None
    if type(ident) is not int:
        raise ValueError('Identifiant d’offre invalide.')
    return get_offer(ident)


def _gemini_ready(data, payload):
    if data.get('consent') is not True:
        raise ValueError('Votre consentement explicite est obligatoire avant toute transmission à Gemini.')
    if data.get('digest') != _digest(payload):
        raise ValueError('Les données ont changé depuis l’aperçu. Relisez le contenu à transmettre.')


# ------------------------------------------------------------------ statut
@ai.get('/ai/status')
def ai_status():
    state = GeminiService(config()).status()
    return jsonify(**state, local_available=True, cv_actions=list(cv_assistant.ACTIONS), career_tasks=list(career_ai.TASKS),
                   gemini_cv_actions=['analyze', *cv_assistant.INSTRUCTIONS], privacy='Le nom, l’email, le téléphone, les liens et la photo ne sont jamais transmis.')


@ai.post('/ai/verify')
def ai_verify():
    """Test RÉEL de connexion (requête minimale, aucune donnée personnelle). Jamais la clé en réponse."""
    if config().get('PUBLIC_DEMO_MODE'):
        return jsonify(erreur='Gemini est désactivé en démonstration publique.'), 403
    service = GeminiService(config())
    result = service.verify_connection()
    return jsonify(result=result, status=service.status())


# --------------------------------------------------------------- CV : design
@ai.get('/cvs/design-options')
def design_options():
    return jsonify(templates=[{'id': k, 'label': v, 'photo': k not in TEMPLATES_WITHOUT_PHOTO} for k, v in TEMPLATES.items()],
                   palettes=[{'id': k, **v} for k, v in PALETTES.items()], color_keys=list(COLOR_KEYS),
                   color_labels=COLOR_LABELS, photo={'max_bytes': PHOTO_MAX_BYTES, 'formats': ['image/jpeg', 'image/png', 'image/webp'],
                                                     'min_side': 96, 'max_side': 6000})


@ai.post('/cvs/design/check')
def design_check():
    design = validate_design(body().get('design'))
    return jsonify(design=design, warnings=contrast_warnings(design))


@ai.post('/cvs/photo')
def upload_photo():
    upload = request.files.get('photo')
    if upload is None or not upload.filename:
        raise ValueError('Sélectionnez une image (JPEG, PNG ou WEBP).')
    if not upload.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise ValueError('Extension non autorisée : JPEG, PNG ou WEBP uniquement.')
    content = upload.read(PHOTO_MAX_BYTES + 1)
    if len(content) > PHOTO_MAX_BYTES:
        raise ValueError('Photo trop volumineuse (4 Mo maximum).')
    # Décodée et ré-encodée en mémoire par Pillow ; jamais écrite sur disque ni exécutée.
    return jsonify(sanitize_upload(content))


# ------------------------------------------------------------ CV : assistant
def _cv_request(action):
    if action not in cv_assistant.ACTIONS:
        raise LookupError('Action d’assistance inconnue.')
    data = body()
    cv = _draft_cv(data)
    if cv is None:
        raise ValueError('Fournissez le CV à analyser.')
    offer = _offer(data, required=action == 'optimize')
    return data, cv, offer


@ai.post('/ai/cv/<action>/preview')
def cv_assist_preview(action):
    _, cv, offer = _cv_request(action)
    payload = cv_assistant.gemini_payload(action, cv, offer)
    return jsonify(payload=payload, digest=_digest(payload),
                   note='Seules ces données seront transmises à Gemini. Nom, email, téléphone, liens et photo sont exclus.')


@ai.post('/ai/cv/<action>')
def cv_assist(action):
    data, cv, offer = _cv_request(action)
    local = cv_assistant.run_local(action, cv, offers() if action == 'skills' else (), offer)  # évite de charger toutes les offres inutilement
    if data.get('mode', 'local') != 'gemini':
        local['notice'] = 'Analyse locale : aucune donnée transmise. Les propositions ne sont appliquées qu’après votre validation.'
        return jsonify(local)
    payload = cv_assistant.gemini_payload(action, cv, offer)
    _gemini_ready(data, payload)
    service = GeminiService(config())
    try:
        if action == 'analyze':
            value = service.generate_json('cv_analyze', payload, cv_assistant.ANALYZE_SCHEMA, cv_assistant.ANALYZE_INSTRUCTION,
                                          temperature=0.2, max_output_tokens=4000)
            weaknesses, strengths = cv_assistant.validate_analyze(cv, value)
            analysis = {**local['analysis'], 'strengths_ai': strengths}
            return jsonify(action=action, mode='gemini', analysis=analysis, suggestions=weaknesses + local['suggestions'],
                           notice='Analyse Gemini vérifiée (aucun fait ni chiffre ajouté) + contrôles locaux. Le score reste calculé localement.')
        instruction = cv_assistant.COMMON_RULES + ' ' + cv_assistant.INSTRUCTIONS[action]
        value = service.generate_json('cv_' + action, payload, cv_assistant.GEMINI_SCHEMA, instruction, temperature=0.2, max_output_tokens=5000)
        suggestions = cv_assistant.validate_gemini(action, cv, value)
        if not suggestions:
            raise GeminiError('Gemini n’a proposé aucune modification vérifiable. Propositions locales affichées.')
        extra = {k: local[k] for k in ('matched', 'missing', 'offer') if k in local}
        return jsonify(action=action, mode='gemini', suggestions=suggestions, **extra,
                       notice='Propositions Gemini vérifiées (cibles existantes, aucun chiffre ajouté). Relisez avant d’accepter.')
    except (GeminiError, ValueError) as exc:  # ValueError : réponse non vérifiable
        local['notice'] = getattr(exc, 'user_message', 'Réponse Gemini non vérifiable : propositions locales affichées.')
        local['fallback'] = True
        return jsonify(local)


# ---------------------------------------------------------- assistant carrière
def _career_request(task):
    if task not in career_ai.TASKS:
        raise LookupError('Tâche inconnue.')
    data = body()
    cv = _draft_cv(data)
    offer = _offer(data, required=task in ('cover_letter', 'interview', 'explain_offer', 'application_help'))
    if task != 'explain_offer' and cv is None:
        raise ValueError('Sélectionnez un CV enregistré ou fournissez votre brouillon.')
    return data, cv, offer


@ai.post('/ai/career/<task>/preview')
def career_preview(task):
    _, cv, offer = _career_request(task)
    payload = career_ai.gemini_payload(task, cv, offer, offers() if task == 'skills' else ())
    return jsonify(payload=payload, digest=_digest(payload),
                   note='Seules ces données seront transmises à Gemini. Nom, email, téléphone, liens et photo sont exclus.')


@ai.post('/ai/career/<task>')
def career(task):
    data, cv, offer = _career_request(task)
    channel = None
    if task == 'application_help':
        company = next((c for c in companies() if c['id'] == offer.get('entreprise_ref')), None)
        channel = resolve_channel(offer, company)
    all_offers = offers() if task == 'skills' else ()
    local = career_ai.run_local(task, cv, offer, all_offers, channel)
    result = {'task': task, 'mode': 'local', 'result': local}
    if data.get('mode', 'local') != 'gemini':
        result['notice'] = 'Version locale : aucune donnée transmise à un service externe.'
        return jsonify(result)
    payload = career_ai.gemini_payload(task, cv, offer, all_offers)
    _gemini_ready(data, payload)
    schema, instruction = career_ai.TASK_SPEC[task]
    try:
        value = GeminiService(config()).generate_json('career_' + task, payload, schema, instruction, temperature=0.4, max_output_tokens=4000)
        checked = career_ai.validate_gemini(task, value, payload, cv)
        return jsonify(task=task, mode='gemini', result=checked, local=local,
                       notice='Réponse Gemini vérifiée. Relisez-la : elle ne remplace pas votre jugement.')
    except (GeminiError, ValueError) as exc:  # ValueError : réponse non vérifiable
        result.update(notice=getattr(exc, 'user_message', 'Réponse Gemini non vérifiable : version locale affichée.'), fallback=True)
        return jsonify(result)


def _interview_feedback_request():
    data=body();cv=_draft_cv(data)
    if cv is None:raise ValueError('Sélectionnez le CV utilisé pour cet entretien.')
    offer=_offer(data,required=True)
    answers=career_ai.validate_interview_answers(data.get('answers'))
    return data,cv,offer,answers


@ai.post('/ai/interview/feedback/preview')
def interview_feedback_preview():
    _,cv,offer,answers=_interview_feedback_request()
    payload=career_ai.gemini_payload('interview_feedback',cv,offer,answers=answers)
    return jsonify(payload=payload,digest=_digest(payload),
                   note='L’aperçu contient le CV anonymisé, l’offre et vos réponses. Retirez vous-même tout nom ou détail personnel avant de donner votre accord.')


@ai.post('/ai/interview/feedback')
def interview_feedback_route():
    data,cv,offer,answers=_interview_feedback_request()
    local=career_ai.interview_feedback(cv,offer,answers)
    if data.get('mode','local')!='gemini':
        return jsonify(mode='local',feedback=local,notice='Retour local de rédaction; aucune donnée transmise à un service externe.')
    payload=career_ai.gemini_payload('interview_feedback',cv,offer,answers=answers)
    _gemini_ready(data,payload)
    try:
        value=GeminiService(config()).generate_json('career_interview_feedback',payload,INTERVIEW_FEEDBACK_SCHEMA,
            career_ai.RULES+' Donne un retour bienveillant et concret à chaque réponse. Ne déduis ni ne vérifie les faits; n’invente pas d’expérience, de résultat ou de compétence. Pour chaque entrée, conserve le même index et propose un feedback et un axe de travail en français.',
            temperature=0.3,max_output_tokens=3000)
        checked=career_ai.validate_interview_feedback(value,answers)
        return jsonify(mode='gemini',feedback=checked,notice='Retour Gemini vérifié structurellement, à relire. Les réponses restent vos propres mots.')
    except (GeminiError,ValueError) as exc:
        return jsonify(mode='local',feedback=local,fallback=True,
                       notice=getattr(exc,'user_message','Gemini indisponible : retour local de rédaction affiché.'))
