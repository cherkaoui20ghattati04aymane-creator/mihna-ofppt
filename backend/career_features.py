"""Phase 11 career features — deterministic, explainable, local rules.

Every function here works only from data already saved by the user (CV, Profile,
applications) and from offer/company records. Nothing is generated or assumed:
missing information stays missing and is reported as such. Gemini can *add*
recommendations on top (see phase11_routes), but scores are always computed here.
"""
from __future__ import annotations

import re
from collections import Counter, OrderedDict
from datetime import date, datetime

from .matching import norm, skills_from, canonical, offer_skills
from .validation import SENT_STATUSES, STATUSES

# Related (transferable) skills. Used only to say "you know X, which is related to the
# missing Y" — never to claim that the user knows Y.
RELATED = {
    'typescript': ['javascript'], 'react': ['javascript', 'html', 'css'], 'angular': ['typescript', 'javascript'],
    'vue.js': ['javascript', 'html', 'css'], 'node.js': ['javascript'], 'next.js': ['react'],
    'django': ['python', 'flask'], 'flask': ['python', 'django'], 'pandas': ['python', 'excel'], 'numpy': ['python'],
    'scikit-learn': ['python', 'machine learning'], 'machine learning': ['python', 'statistiques'],
    'deep learning': ['machine learning', 'python'], 'tensorflow': ['deep learning', 'python'],
    'pytorch': ['deep learning', 'python'], 'power bi': ['excel', 'tableau software', 'sql'],
    'tableau software': ['power bi', 'excel'], 'postgresql': ['sql', 'mysql'], 'mysql': ['sql', 'postgresql'],
    'oracle': ['sql'], 'mongodb': ['sql'], 'spring': ['java'], 'kotlin': ['java'], 'android': ['java', 'kotlin'],
    'laravel': ['php'], 'symfony': ['php'], '.net': ['c#'], 'c#': ['java', '.net'], 'kubernetes': ['docker'],
    'docker': ['linux'], 'aws': ['cloud', 'linux'], 'azure': ['cloud'], 'devops': ['docker', 'git', 'linux'],
    'marketing digital': ['marketing', 'seo', 'réseaux sociaux'], 'seo': ['marketing digital'],
    'community management': ['réseaux sociaux', 'communication'], 'contrôle de gestion': ['comptabilité', 'finance', 'excel'],
    'audit': ['comptabilité', 'finance'], 'fiscalité': ['comptabilité'], 'paie': ['rh'], 'recrutement': ['rh'],
    'supply chain': ['logistique', 'achats'], 'sap': ['erp'], 'erp': ['sap', 'sage'], 'figma': ['design'],
    'illustrator': ['photoshop', 'design'], 'photoshop': ['illustrator', 'design'], 'scrum': ['agile'],
}
ACTION_VERBS = ('développé', 'developpe', 'conçu', 'concu', 'réalisé', 'realise', 'analysé', 'analyse', 'créé', 'cree',
                'géré', 'gere', 'mis en place', 'automatisé', 'automatise', 'optimisé', 'optimise', 'coordonné',
                'coordonne', 'participé', 'participe', 'rédigé', 'redige', 'animé', 'anime', 'piloté', 'pilote',
                'built', 'designed', 'developed', 'managed', 'led', 'implemented', 'analyzed', 'created')
OFFICIAL_RESOURCES = {
    'python': ('Documentation officielle Python', 'https://docs.python.org/fr/3/tutorial/'),
    'javascript': ('MDN Web Docs — JavaScript', 'https://developer.mozilla.org/fr/docs/Web/JavaScript/Guide'),
    'html': ('MDN Web Docs — HTML', 'https://developer.mozilla.org/fr/docs/Learn/HTML'),
    'css': ('MDN Web Docs — CSS', 'https://developer.mozilla.org/fr/docs/Learn/CSS'),
    'typescript': ('Documentation TypeScript', 'https://www.typescriptlang.org/docs/'),
    'react': ('Documentation React', 'https://react.dev/learn'),
    'sql': ('Documentation SQLite (langage SQL)', 'https://www.sqlite.org/lang.html'),
    'postgresql': ('Documentation PostgreSQL', 'https://www.postgresql.org/docs/current/tutorial.html'),
    'git': ('Livre Pro Git (officiel)', 'https://git-scm.com/book/fr/v2'),
    'docker': ('Documentation Docker', 'https://docs.docker.com/get-started/'),
    'pandas': ('Documentation pandas', 'https://pandas.pydata.org/docs/getting_started/index.html'),
    'django': ('Documentation Django', 'https://docs.djangoproject.com/fr/stable/intro/'),
    'flask': ('Documentation Flask', 'https://flask.palletsprojects.com/'),
    'node.js': ('Documentation Node.js', 'https://nodejs.org/fr/learn'),
    'scikit-learn': ('Guide utilisateur scikit-learn', 'https://scikit-learn.org/stable/user_guide.html'),
    'linux': ('Documentation Ubuntu', 'https://ubuntu.com/tutorials'),
}
EDUCATION_WORDS = ('diplome', 'diplôme', 'bac+', 'bac +', 'licence', 'master', 'ingenieur', 'ingénieur', 'degree', 'bachelor',
                   'dut', 'bts', 'technicien', 'formation', 'etudiant', 'étudiant', 'student', 'graduate')
CERT_WORDS = ('certif', 'certified', 'certificat', 'toeic', 'toefl', 'ielts', 'delf', 'pmp', 'itil', 'ccna')
EXPERIENCE_PATTERN = re.compile(r'(\d+)\s*(?:\+|à|-|to)?\s*\d*\s*(?:ans|an|years|year|yrs)\b', re.I)


def _split(value):
    return [p.strip() for p in re.split(r'[,;|\n•]+', str(value or '')) if p.strip()]


def _sentences(value):
    return [p.strip() for p in re.split(r'(?<=[.!?])\s+|[\r\n]+', str(value or '')) if p.strip()]


def cv_text(cv: dict) -> str:
    parts = [cv.get(k, '') for k in ('title', 'summary', 'technical', 'soft', 'languages')]
    for section in ('education', 'experience', 'projects', 'certifications'):
        for item in cv.get(section) or []:
            parts.extend(str(item.get(k) or '') for k in ('title', 'organization', 'period', 'description'))
    return ' '.join(str(p or '') for p in parts)


def offer_text(offer: dict) -> str:
    return '\n'.join(str(offer.get(k) or '') for k in ('Titre', 'Description', 'competences'))


# ---------------------------------------------------------------- A. Skills gap
def skills_gap(cv: dict, offer: dict) -> dict:
    text = offer_text(offer)
    required, optional = offer_skills(text)
    own = set(canonical(s) for s in skills_from(cv_text(cv)))
    present = [s for s in required if canonical(s) in own]
    missing = [s for s in required if canonical(s) not in own]
    related = []
    for skill in missing:
        bridges = [r for r in RELATED.get(skill, []) if canonical(r) in own]
        if bridges:
            related.append({'missing': skill, 'you_have': bridges,
                            'note': f'Vous mentionnez {", ".join(bridges)}, proche de {skill}. Ce n’est pas une équivalence.'})
    experience, education, certifications = [], [], []
    for sentence in _sentences(text)[:120]:
        clean = sentence[:400]
        low = norm(clean)
        if EXPERIENCE_PATTERN.search(clean) or 'experience' in low:
            experience.append(clean)
        if any(norm(w) in low for w in EDUCATION_WORDS):
            education.append(clean)
        if any(w in low for w in CERT_WORDS):
            certifications.append(clean)
    years = [int(m.group(1)) for m in EXPERIENCE_PATTERN.finditer(text) if int(m.group(1)) < 30]
    coverage = round(100 * len(present) / len(required)) if required else None
    recommendations = []
    for item in related:
        recommendations.append(f'Pour « {item["missing"]} » : appuyez-vous sur {", ".join(item["you_have"])} ; '
                               'réalisez un petit projet pratique avant de l’indiquer dans votre CV.')
    for skill in missing:
        if skill not in {r['missing'] for r in related}:
            recommendations.append(f'« {skill} » est demandé et absent de votre CV : à apprendre, ou à ajouter seulement '
                                   'si vous l’avez réellement pratiqué.')
    if years:
        recommendations.append(f'L’offre mentionne {max(years)} an(s) d’expérience : mettez en avant stages et projets '
                               'avec leurs dates exactes ; n’arrondissez pas votre durée d’expérience.')
    if education:
        recommendations.append('Vérifiez que l’intitulé exact de votre formation et son année figurent dans le CV.')
    if certifications:
        recommendations.append('Des certifications sont citées : n’indiquez que celles que vous avez obtenues ; '
                               'les autres peuvent figurer dans votre feuille de route.')
    if not required:
        recommendations.append('Aucune compétence du vocabulaire contrôlé n’a été repérée dans cette offre : lisez-la en '
                               'détail, l’analyse automatique est limitée.')
    return {
        'offer': {'id': offer.get('ID'), 'title': offer.get('Titre'), 'company': offer.get('entreprise_nom')},
        'required_skills': required, 'optional_skills': optional, 'present': present, 'missing': missing, 'related': related,
        'experience_requirements': experience[:8], 'years_mentioned': max(years) if years else None,
        'education_requirements': education[:6], 'certification_requirements': certifications[:6],
        'coverage': coverage, 'recommendations': recommendations[:12], 'mode': 'local',
        'method': 'Comparaison du texte de l’offre avec le vocabulaire contrôlé de compétences, appliquée au CV enregistré. '
                  'Une compétence absente n’est jamais ajoutée ni supposée.',
    }


# ---------------------------------------------------------------- E. CV quality
def _criterion(key, label, points, maximum, explanation, tips=(), evaluated=True):
    return {'key': key, 'label': label, 'points': round(points, 1) if evaluated else None, 'max': maximum,
            'explanation': explanation, 'tips': [t for t in tips if t], 'evaluated': evaluated}


def cv_quality(cv: dict, offer: dict | None = None) -> dict:
    crit = []
    # Contact (10)
    contact = [bool(cv.get('name')), bool(cv.get('email') or cv.get('phone')), bool(cv.get('city')),
               bool(cv.get('linkedin') or cv.get('github') or cv.get('portfolio'))]
    weights = (3, 4, 2, 1)
    crit.append(_criterion('contact', 'Coordonnées', sum(w for w, ok in zip(weights, contact) if ok), 10,
                           'Nom (3), email ou téléphone (4), ville (2), lien professionnel (1).',
                           ['Ajoutez un email ou un téléphone.' if not contact[1] else '',
                            'Indiquez votre ville.' if not contact[2] else '']))
    # Completeness (20)
    checks = OrderedDict([('Titre', bool(cv.get('title'))), ('Résumé', bool(cv.get('summary'))),
                          ('Compétences', bool(cv.get('technical'))), ('Formation', bool(cv.get('education'))),
                          ('Expérience ou projets', bool(cv.get('experience') or cv.get('projects'))),
                          ('Langues', bool(cv.get('languages')))])
    done = sum(checks.values())
    crit.append(_criterion('completeness', 'Complétude', 20 * done / len(checks), 20,
                           f'{done} rubrique(s) essentielle(s) sur {len(checks)} renseignée(s).',
                           ['Rubriques vides : ' + ', '.join(k for k, v in checks.items() if not v) + '.'] if done < len(checks) else []))
    # Readability (15)
    summary = str(cv.get('summary') or '')
    words = re.findall(r'\w+', summary)
    sentences = _sentences(summary) or ([summary] if summary else [])
    avg = (len(words) / len(sentences)) if sentences else 0
    r = 0.0
    tips = []
    if 25 <= len(words) <= 110:
        r += 7
    elif words:
        r += 3
        tips.append('Visez un résumé de 2 à 4 phrases (25 à 110 mots).')
    else:
        tips.append('Rédigez un court résumé.')
    if sentences and avg <= 28:
        r += 5
    elif sentences:
        tips.append('Raccourcissez les phrases du résumé (moins de 28 mots en moyenne).')
    long_caps = re.findall(r'\b[A-ZÉÈÀ]{6,}\b', cv_text(cv))
    if not long_caps:
        r += 3
    else:
        tips.append('Évitez les mots entièrement en majuscules.')
    crit.append(_criterion('readability', 'Lisibilité', r, 15,
                           f'Résumé : {len(words)} mot(s), {round(avg, 1)} mot(s)/phrase en moyenne.', tips))
    # Organisation (10)
    entries = [(s, i) for s in ('education', 'experience', 'projects', 'certifications') for i in (cv.get(s) or [])]
    with_title = sum(1 for _, i in entries if i.get('title'))
    with_period = sum(1 for s, i in entries if i.get('period') or s == 'projects')
    org = 10 if not entries else 10 * (with_title + with_period) / (2 * len(entries))
    crit.append(_criterion('organization', 'Organisation des rubriques', org, 10,
                           f'{len(entries)} entrée(s) : {with_title} avec intitulé, {with_period} datée(s) (dates facultatives pour les projets).',
                           ['Ajoutez un intitulé et une période à chaque entrée.'] if org < 10 else []))
    # Skills relevance (15)
    listed = _split(cv.get('technical'))
    recognised = [s for s in listed if skills_from(s)]
    s_points = 0.0
    if listed:
        s_points += 7 if 4 <= len(listed) <= 20 else 3
        s_points += 8 * len(recognised) / len(listed)
    crit.append(_criterion('skills', 'Pertinence des compétences', s_points, 15,
                           f'{len(listed)} compétence(s) listée(s), {len(recognised)} reconnue(s) par le vocabulaire contrôlé.',
                           ['Listez de 4 à 20 compétences techniques précises.' if not 4 <= len(listed) <= 20 else '']))
    # Experience descriptions (15)
    described = [i for s, i in entries if s in ('experience', 'projects')]
    if described:
        good = sum(1 for i in described if len(str(i.get('description') or '')) >= 60)
        verbs = sum(1 for i in described if any(v in norm(i.get('description') or '') for v in map(norm, ACTION_VERBS)))
        e_points = 15 * (0.6 * good + 0.4 * verbs) / len(described)
        e_tip = ['Décrivez chaque expérience en au moins une phrase commençant par un verbe d’action (réalisé, conçu…).'] if e_points < 15 else []
        e_exp = f'{good}/{len(described)} description(s) détaillée(s), {verbs}/{len(described)} avec verbe d’action.'
    else:
        e_points, e_exp, e_tip = 0, 'Aucune expérience ni projet décrit.', ['Ajoutez au moins un projet ou un stage.']
    crit.append(_criterion('descriptions', 'Descriptions des expériences', e_points, 15, e_exp, e_tip))
    # Formatting (5)
    periods = [str(i.get('period') or '') for _, i in entries if i.get('period')]
    consistent = (not periods) or all(re.search(r'\d{4}', p) for p in periods)
    too_long = [k for k in ('title', 'summary') if len(str(cv.get(k) or '')) > (120 if k == 'title' else 1200)]
    f_points = (3 if consistent else 1) + (2 if not too_long else 0)
    crit.append(_criterion('formatting', 'Mise en forme', f_points, 5,
                           'Périodes avec une année, titre ≤ 120 caractères, résumé ≤ 1 200 caractères.',
                           ['Indiquez les années dans chaque période.' if not consistent else '',
                            'Raccourcissez : ' + ', '.join(too_long) if too_long else '']))
    # Job relevance (10)
    if offer:
        gap = skills_gap(cv, offer)
        if gap['required_skills']:
            j_points = 10 * len(gap['present']) / len(gap['required_skills'])
            j_exp = f'{len(gap["present"])} compétence(s) de l’offre sur {len(gap["required_skills"])} présentes dans le CV.'
        else:
            j_points, j_exp = 5, 'Aucune compétence reconnue dans l’offre : note neutre (5/10).'
        crit.append(_criterion('job', 'Pertinence pour l’offre', j_points, 10, j_exp,
                               ['Compétences de l’offre absentes : ' + ', '.join(gap['missing'][:6]) + ' (à ne pas ajouter sans les maîtriser).'] if gap['missing'] else []))
    else:
        crit.append(_criterion('job', 'Pertinence pour l’offre', 0, 10, 'Non évaluée : aucune offre sélectionnée.',
                               ['Choisissez une offre pour évaluer ce critère.'], evaluated=False))
    evaluated = [c for c in crit if c['evaluated']]
    earned = sum(c['points'] for c in evaluated)
    possible = sum(c['max'] for c in evaluated)
    score = round(100 * earned / possible) if possible else 0
    return {'score': score, 'earned': round(earned, 1), 'possible': possible, 'criteria': crit, 'mode': 'local',
            'grade': 'Solide' if score >= 80 else 'À renforcer' if score >= 55 else 'À compléter',
            'method': 'Score = points obtenus / points des critères évalués × 100. Chaque critère et son barème sont affichés. '
                      'Si aucune offre n’est choisie, le critère « Pertinence pour l’offre » est exclu du calcul.',
            'disclaimer': 'Ce score est un indicateur de qualité rédactionnelle. Il ne garantit ni le passage d’un logiciel '
                          'de tri (ATS) ni une sélection.'}


# ---------------------------------------------------------------- B. Career roadmap
def career_roadmap(profile: dict, cvs: list[dict], target_offers: list[dict], state: dict, facts: dict) -> dict:
    """Build steps from real data. `facts` holds booleans/counts read from the database.

    Automatic steps are ticked only from saved records; learning steps are ticked only
    when the user declares them done (stored in `state['declared_done']`).
    """
    declared = set(state.get('declared_done') or [])
    objective = state.get('objective') or profile.get('headline') or ''
    latest = cvs[0] if cvs else {}
    own_text = cv_text(latest) + ' ' + ' '.join(profile.get('skills') or [])
    own = {canonical(s) for s in skills_from(own_text)}
    demand = Counter()
    per_offer = []
    for offer in target_offers:
        required = list(dict.fromkeys(skills_from(offer_text(offer))))
        missing = [s for s in required if canonical(s) not in own]
        demand.update(missing)
        per_offer.append({'id': offer.get('ID'), 'title': offer.get('Titre'), 'missing': missing,
                          'coverage': round(100 * (len(required) - len(missing)) / len(required)) if required else None})
    steps = []

    def add(step_id, phase, title, detail, auto=None, resource=None):
        done = bool(auto) if auto is not None else step_id in declared
        steps.append({'id': step_id, 'phase': phase, 'title': title, 'detail': detail, 'done': done,
                      'kind': 'auto' if auto is not None else 'declared', 'resource': resource})

    add('profile', 'Fondations', 'Compléter le profil', 'Nom, titre, compétences, formation.', auto=facts.get('profile_complete'))
    add('cv', 'Fondations', 'Créer et valider un CV original', 'Brouillon prérempli depuis le profil.', auto=facts.get('cv_count', 0) > 0)
    add('quality', 'Fondations', 'Atteindre un score qualité CV ≥ 70', f'Score actuel : {facts.get("quality_score", "non calculé")}.',
        auto=(facts.get('quality_score') or 0) >= 70)
    add('targets', 'Cibler', 'Sauvegarder au moins 3 offres cibles', f'{len(target_offers)} offre(s) cible(s).', auto=len(target_offers) >= 3)
    for skill, count in demand.most_common(6):
        resource = OFFICIAL_RESOURCES.get(skill)
        add('learn:' + norm(skill), 'Développer', f'Apprendre {skill}',
            f'Demandé dans {count} offre(s) cible(s). Pratiquez sur un petit projet, puis ajoutez-le au CV si vous le maîtrisez.',
            resource={'label': resource[0], 'url': resource[1]} if resource else None)
        add('proof:' + norm(skill), 'Développer', f'Prouver {skill} par un projet',
            'Ajoutez un projet réel (titre, période, description) dans votre profil ou CV.')
    add('tailored', 'Candidater', 'Adapter un CV à une offre cible', 'Une version validée par offre.', auto=facts.get('tailored_count', 0) > 0)
    add('apply', 'Candidater', 'Préparer une candidature', 'Avec le CV adapté.', auto=facts.get('application_count', 0) > 0)
    add('interview', 'Candidater', 'Faire une simulation d’entretien', 'Questions + retours enregistrés.', auto=facts.get('interview_count', 0) > 0)
    total = len(steps)
    done = sum(1 for s in steps if s['done'])
    return {'objective': objective, 'steps': steps, 'progress': round(100 * done / total) if total else 0,
            'done': done, 'total': total, 'skills_to_develop': [{'skill': s, 'offers': c} for s, c in demand.most_common(10)],
            'targets': per_offer, 'mode': 'local',
            'method': 'Étapes « auto » cochées uniquement à partir de vos données enregistrées ; étapes « déclarées » cochées '
                      'par vous. Aucune formation ni qualification n’est ajoutée à votre profil.'}


# ---------------------------------------------------------------- C. Application analytics
STATUS_ORDER = STATUSES


def application_analytics(applications: list[dict], history: list[dict], offers_by_id: dict, scores: dict) -> dict:
    total = len(applications)
    by_status = Counter(a.get('statut') or 'Non renseigné' for a in applications)
    reached_interview = set()
    for h in history:
        if h.get('new_status') in ('Entretien', 'Acceptée'):
            reached_interview.add(h.get('candidature_id'))
    for a in applications:
        if a.get('statut') in ('Entretien', 'Acceptée'):
            reached_interview.add(a.get('id'))
    application_ids = {a.get('id') for a in applications}
    sent_ids = {a.get('id') for a in applications if a.get('statut') in SENT_STATUSES}
    sent_ids.update(h.get('candidature_id') for h in history
                    if h.get('new_status') in SENT_STATUSES and h.get('candidature_id') in application_ids)
    responded_ids = reached_interview | {a.get('id') for a in applications if a.get('statut') == 'Refusée'}
    responded_ids.update(h.get('candidature_id') for h in history if h.get('new_status') == 'Refusée')
    months = Counter()
    for a in applications:
        raw = str(a.get('date_candidature') or a.get('created_at') or '')[:7]
        if re.fullmatch(r'\d{4}-\d{2}', raw):
            months[raw] += 1
    categories = Counter()
    for a in applications:
        offer = offers_by_id.get(a.get('offre_id'))
        categories[(offer or {}).get('domain_group') or ('Candidature spontanée' if not a.get('offre_id') else 'Non classée')] += 1
    accepted = by_status.get('Acceptée', 0)
    rejected = by_status.get('Refusée', 0)
    score_values = [v for v in scores.values() if v is not None]

    def rate(n, d):
        return round(100 * n / d, 1) if d else None
    return {
        'total': total, 'by_status': [{'status': s, 'count': by_status.get(s, 0)} for s in STATUS_ORDER] +
        [{'status': s, 'count': c} for s, c in by_status.items() if s not in STATUS_ORDER],
        'interviews': len(reached_interview), 'accepted': accepted, 'rejected': rejected,
        'trend': [{'month': m, 'count': months[m]} for m in sorted(months)],
        'categories': [{'category': c, 'count': n} for c, n in categories.most_common(8)],
        'matching_scores': {'count': len(score_values),
                            'average': round(sum(score_values) / len(score_values), 1) if score_values else None,
                            'items': [{'application_id': k, 'score': v} for k, v in scores.items()]},
        'conversion': {'sent_rate': rate(len(sent_ids), total), 'interview_rate': rate(len(reached_interview & sent_ids), len(sent_ids)),
                       'acceptance_rate': rate(accepted, len(sent_ids)), 'response_rate': rate(len(responded_ids & sent_ids), len(sent_ids))},
        'definitions': {
            'interview_rate': 'Candidatures ayant atteint « Entretien » ou « Acceptée » (statut actuel ou historique) / candidatures envoyées.',
            'acceptance_rate': 'Candidatures « Acceptée » / candidatures envoyées.',
            'response_rate': 'Candidatures distinctes ayant atteint un entretien, une acceptation ou un refus, sur les candidatures envoyées.',
            'matching_scores': 'Score local CV ↔ offre, calculé pour les candidatures liées à une offre et à un CV enregistrés.'},
    }


# ---------------------------------------------------------------- D. Company insights
def _name_key(value):
    return re.sub(r'[^a-z0-9]+', ' ', norm(value or '')).strip()


def company_insights(company: dict, offers: list[dict]) -> dict:
    key = _name_key(company.get('Nom'))
    linked = [o for o in offers if (o.get('entreprise_ref') is not None and str(o.get('entreprise_ref')) == str(company.get('rowid')))
              or (key and _name_key(o.get('entreprise_nom')) == key)]
    website = company.get('Site Web') or ''
    emails = [e for e in _split(company.get('Emails')) if '@' in e]
    location = company.get('ville') or company.get('Adresse') or ''
    facts = [f for f in (
        ('Secteur', company.get('Secteur')), ('Adresse', company.get('Adresse')), ('Ville', company.get('ville')),
        ('Quartier', company.get('quartier')), ('Téléphone', company.get('Téléphone'))) if f[1]]
    return {
        'id': company.get('rowid'), 'name': company.get('Nom'), 'industry': company.get('Secteur') or None,
        'location': location or None, 'website': website or None,
        'website_status': 'renseigné dans la base, non vérifié automatiquement' if website else 'non renseigné',
        'maps_url': company.get('Google Maps') or None, 'emails_count': len(emails),
        'coordinates_verified': bool(company.get('geo_verified_at')),
        'last_verification': company.get('geo_verified_at') or None,
        'source': company.get('geo_source') or 'Répertoire historique du projet (provenance non enregistrée par ligne)',
        'facts': [{'label': a, 'value': b} for a, b in facts],
        'opportunities': [{'id': o.get('ID'), 'title': o.get('Titre'), 'source': o.get('source'),
                           'availability': o.get('availability'), 'match': 'référence' if o.get('entreprise_ref') is not None else 'nom identique'}
                          for o in linked[:30]],
        'opportunity_count': len(linked),
        'not_available': ['Effectif', 'Chiffre d’affaires', 'Avis / notes'],
        'notice': 'Seules les informations présentes dans la base sont affichées. Effectif, chiffre d’affaires et avis ne '
                  'sont pas disponibles et ne sont pas estimés.',
    }


def companies_overview(companies: list[dict], offers: list[dict]) -> dict:
    sectors = Counter(c.get('Secteur') or 'Non renseigné' for c in companies)
    keys = Counter(_name_key(o.get('entreprise_nom')) for o in offers if o.get('entreprise_nom'))
    with_offers = sum(1 for c in companies if keys.get(_name_key(c.get('Nom'))))
    return {'total': len(companies), 'with_website': sum(1 for c in companies if c.get('Site Web')),
            'with_email': sum(1 for c in companies if c.get('Emails')),
            'with_verified_coordinates': sum(1 for c in companies if c.get('geo_verified_at')),
            'with_open_offers': with_offers,
            'sectors': [{'sector': s, 'count': n} for s, n in sectors.most_common(12)]}


# ---------------------------------------------------------------- F. Interview assessment
def interview_assessment(answers: list[dict], feedback: dict | None) -> dict:
    answered = [a for a in answers if str(a.get('answer') or '').strip()]
    lengths = [len(re.findall(r'\w+', a.get('answer') or '')) for a in answered]
    star = sum(1 for a in answered if sum(w in norm(a.get('answer') or '') for w in ('situation', 'tache', 'action', 'resultat', 'projet', 'j ai')) >= 2)
    completeness = round(100 * len(answered) / len(answers)) if answers else 0
    depth = round(100 * sum(1 for n in lengths if n >= 40) / len(answered)) if answered else 0
    recs = []
    if completeness < 100:
        recs.append('Répondez à toutes les questions, même brièvement.')
    if depth < 60:
        recs.append('Développez vos réponses (au moins 40 mots) avec un exemple concret.')
    if answered and star < len(answered) / 2:
        recs.append('Structurez vos exemples : situation, tâche, action, résultat (méthode STAR).')
    for item in (feedback or {}).get('answer_feedback', [])[:5]:
        if item.get('focus'):
            recs.append(str(item['focus'])[:300])
    level = 'Bonne préparation' if completeness == 100 and depth >= 60 else 'Préparation partielle' if completeness >= 50 else 'À poursuivre'
    return {'answered': len(answered), 'questions': len(answers), 'completeness': completeness, 'depth': depth,
            'structured_examples': star, 'level': level, 'recommendations': recs[:8],
            'method': 'Indicateurs locaux : réponses fournies, longueur (≥ 40 mots), présence d’éléments de structure. '
                      'Ce n’est pas une évaluation de recrutement.'}


def month_key(value):
    try:
        return datetime.fromisoformat(str(value)[:19]).strftime('%Y-%m')
    except ValueError:
        return None


def today():
    return date.today().isoformat()
