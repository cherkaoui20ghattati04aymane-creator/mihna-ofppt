"""Score déterministe et explicable : chaque composante et contribution sont retournées.

Composantes pondérées (total 100) : compétences/technologies, formation + domaine d'étude,
expérience/projets, localisation, type d'opportunité. Les mots-clés communs sont affichés
comme indice complémentaire (non pondéré). Aucune compétence n'est attribuée au candidat :
seules celles qu'il a saisies sont comparées au texte de l'offre.
"""
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache

VOCABULARY = [
    # Données / IA
    'python', 'sql', 'excel', 'power bi', 'tableau software', 'pandas', 'numpy', 'machine learning', 'deep learning',
    'data science', 'data analysis', 'statistiques', 'big data', 'spark', 'tensorflow', 'pytorch', 'nlp',
    'intelligence artificielle', 'scikit-learn',
    # Développement
    'javascript', 'typescript', 'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'flask', 'django',
    'java', 'spring', 'php', 'laravel', 'symfony', 'c#', '.net', 'c++', 'kotlin', 'flutter', 'android', 'ios',
    'git', 'api rest', 'mysql', 'postgresql', 'mongodb', 'oracle', 'docker', 'kubernetes', 'linux', 'cloud',
    'aws', 'azure', 'devops', 'cybersécurité', 'réseaux', 'wordpress', 'agile', 'scrum', 'uml', 'tests unitaires',
    # Gestion / commerce
    'marketing', 'marketing digital', 'seo', 'community management', 'communication', 'comptabilité', 'finance',
    'audit', 'contrôle de gestion', 'fiscalité', 'vente', 'commerce', 'négociation', 'service client',
    'rh', 'recrutement', 'paie', 'logistique', 'supply chain', 'achats', 'gestion de projet', 'gestion',
    'management', 'sap', 'sage', 'erp', 'crm',
    # Tourisme / hôtellerie (fort à Marrakech)
    'tourisme', 'hôtellerie', 'réception', 'restauration', 'événementiel',
    # Design / technique
    'design', 'canva', 'photoshop', 'illustrator', 'figma', 'autocad', 'électricité', 'maintenance',
    'réseaux sociaux',
    # Langues
    'anglais', 'français', 'arabe', 'espagnol', 'allemand',
]
ALIASES = {'js': 'javascript', 'powerbi': 'power bi', 'ml': 'machine learning', 'comptabilite': 'comptabilite',
           'english': 'anglais', 'french': 'francais', 'human resources': 'rh', 'ressources humaines': 'rh',
           'node': 'node.js', 'nodejs': 'node.js', 'vue': 'vue.js', 'vuejs': 'vue.js', 'postgres': 'postgresql',
           'ia': 'intelligence artificielle', 'ai': 'intelligence artificielle', 'dotnet': '.net',
           'gestion projet': 'gestion de projet', 'sklearn': 'scikit-learn', 'rest': 'api rest',
           'securite informatique': 'cybersecurite', 'social media': 'reseaux sociaux'}
STOP = set('de la le les des du un une et en a au aux pour dans avec sur ou par the and of to is est sont nous vous '
           'votre vos notre nos stage stagiaire emploi recherche entreprise poste profil mission missions h f'.split())
CITIES = ['Marrakech', 'Casablanca', 'Rabat', 'Tanger', 'Agadir', 'Fès', 'Meknès', 'Oujda', 'Kénitra', 'Tétouan',
          'El Jadida', 'Safi', 'Essaouira', 'Ouarzazate', 'Béni Mellal', 'Mohammedia', 'Laâyoune', 'Nador']
COMPONENT_LABELS = {'skills': 'Compétences et technologies', 'education': 'Formation et domaine d’étude',
                    'experience': 'Expérience et projets', 'location': 'Localisation', 'opportunity': 'Type de stage / contrat'}


def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(c))


def tokens(value):
    return [t for t in re.findall(r'[a-z0-9+#]+', norm(value)) if len(t) > 1 and t not in STOP]


def canonical(skill):
    return ALIASES.get(norm(skill).strip(), norm(skill).strip())


@lru_cache(maxsize=2048)
def _term_pattern(term):
    return re.compile(r'(?<!\w)' + re.escape(norm(term)) + r'(?![\w+#])')


def has_term(term, value):
    return bool(_term_pattern(term).search(norm(value)))


def skills_from(value):
    # Texte normalisé une seule fois et motifs précompilés (gain important sur les gros corpus).
    text = norm(value)
    return [s for s in VOCABULARY if _term_pattern(s).search(text)]


def city_from(value):
    text = norm(value)
    return next((c for c in CITIES if re.search(r'(?<!\w)' + re.escape(norm(c)) + r'(?!\w)', text)), None)


def local_profile(value):
    return {'skills': skills_from(value), 'education': '', 'experience': '', 'domain': '', 'location': '', 'opportunity': 'Stage'}


def validate_profile(data):
    if not isinstance(data, dict):
        raise ValueError('Profil invalide.')
    skills = data.get('skills', [])
    if not isinstance(skills, list) or len(skills) > 100 or any(not isinstance(s, str) or len(s) > 100 for s in skills):
        raise ValueError('Liste de compétences invalide.')
    result = {'skills': list(dict.fromkeys(s.strip() for s in skills if s.strip()))}
    for field in ('education', 'experience', 'domain', 'location', 'opportunity'):
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > 6000:
            raise ValueError('Champ de profil invalide.')
        result[field] = value.strip()
    return result


class Corpus:
    """Fréquences documentaires calculées une seule fois par classement (évite un coût O(n²))."""

    def __init__(self, documents):
        self.size = len(documents)
        self.df = Counter()
        for document in documents:
            self.df.update(set(tokens(document)))

    def vector(self, counter):
        return {t: n * (math.log((self.size + 1) / (1 + self.df.get(t, 0))) + 1) for t, n in counter.items()}


def cosine(a, b, corpus):
    if not isinstance(corpus, Corpus):
        corpus = Corpus(corpus)
    aa, bb = Counter(tokens(a)), Counter(tokens(b))
    if not aa or not bb:
        return 0.0
    va, vb = corpus.vector(aa), corpus.vector(bb)
    return sum(v * vb.get(t, 0) for t, v in va.items()) / (math.sqrt(sum(v * v for v in va.values())) * math.sqrt(sum(v * v for v in vb.values())))


def score_label(score):
    if score >= 70:
        return 'Très compatible'
    if score >= 40:
        return 'Partiellement compatible'
    return 'Peu compatible'


def offer_skills(text):
    """Separate explicitly optional clauses from the skills used in coverage."""
    required, optional = {}, {}
    for clause in re.split(r'[;\n]|(?<=[.!?])\s+', text):
        normalized = norm(clause)
        bonus = re.search(r'\b(?:facultati\w*|optionnel\w*|souhait\w*|appreci\w*|preferred|nice to have|a plus|un plus|bonus)\b', normalized)
        mandatory = re.search(r'\b(?:obligatoire\w*|exige\w*|required|mandatory|must have)\b', normalized)
        target = optional if bonus and not mandatory else required
        for skill in skills_from(clause):
            target.setdefault(canonical(skill),skill)
    return list(required.values()), [skill for key,skill in optional.items() if key not in required]


def rank(profile, offers, weights, interpretations=None):
    profile = validate_profile(profile)
    required = {'skills', 'education', 'experience', 'location', 'opportunity'}
    if set(weights) != required or any(type(v) not in (int, float) or not 0 <= v <= 100 for v in weights.values()) or abs(sum(weights.values())-100) > .01:
        raise ValueError('Les cinq pondérations doivent totaliser 100.')
    documents = [' '.join([str(o.get('Titre') or ''), str(o.get('Description') or ''), str(o.get('competences') or '')])
                 for o in offers]
    corpus = Corpus(documents)
    profile_keywords = set(tokens(' '.join([profile['education'], profile['domain'], profile['experience'], ' '.join(profile['skills'])])))
    results = []
    for offer, description in zip(offers, documents):
        requirements, optional = offer_skills('\n'.join(str(offer.get(key) or '')
                                                    for key in ('Titre','Description','competences')))
        matched = [r for r in requirements if any(canonical(r) == canonical(s) for s in profile['skills'])]
        interpretation = (interpretations or {}).get(str(offer['ID']), {})
        for pair in interpretation.get('pairs', []):
            if canonical(pair['offer_skill']) in {canonical(skill) for skill in optional}:
                continue
            if pair['offer_skill'] not in matched:
                matched.append(pair['offer_skill'])
            if pair['offer_skill'] not in requirements:
                requirements.append(pair['offer_skill'])
        missing = [r for r in requirements if r not in matched]
        location = (offer.get('source_metadata') or {}).get('location_classification') or offer.get('location_group') or ''
        remote = location in ('remote_morocco_eligible','remote_worldwide_eligible')
        stored_city = '' if remote else offer.get('ville') or ''
        inferred_city = None if stored_city or remote else city_from(str(offer.get('Titre') or '') + ' ' + str(offer.get('Description') or ''))
        city = stored_city or inferred_city or ''
        offer_type = offer.get('Type contrat') or ''
        components = {
            'skills': len(matched)/len(requirements) if requirements else 0,
            'education': cosine(profile['education']+' '+profile['domain'], description, corpus),
            'experience': cosine(profile['experience'], description, corpus),
            'location': float(bool(city and profile['location'] and norm(city) == norm(profile['location']))),
            'opportunity': float(bool(profile['opportunity'] and norm(profile['opportunity']) == norm(offer_type))),
        }
        contributions = {k: round(components[k]*weights[k], 2) for k in weights}
        uncertain = len(tokens(offer.get('Description') or '')) < 30 or not requirements or not city
        score = round(sum(contributions.values()), 1)
        common_keywords = sorted((profile_keywords & set(tokens(description))) - {norm(s) for s in matched})[:12]

        strengths = []
        if matched:
            strengths.append('Compétences demandées déjà présentes dans votre profil : ' + ', '.join(matched[:8]) + '.')
        if components['education'] >= 0.25:
            strengths.append('Votre formation / domaine d’étude partage du vocabulaire avec l’offre.')
        if components['experience'] >= 0.25:
            strengths.append('Vos expériences ou projets évoquent des tâches proches de l’offre.')
        if components['location']:
            strengths.append(f'Localisation compatible ({city}).')
        if components['opportunity']:
            strengths.append(f'Type d’opportunité recherché identique ({offer_type}).')

        suggestions = []
        if missing:
            suggestions.append('Compétences de l’offre absentes de votre profil : ' + ', '.join(missing[:6]) +
                               '. Ne les ajoutez que si vous les maîtrisez ; sinon, présentez-les comme objectifs d’apprentissage.')
        if not profile['experience']:
            suggestions.append('Décrivez au moins un projet ou une expérience (même pédagogique) pour renforcer la comparaison.')
        if not profile['location']:
            suggestions.append('Indiquez votre ville pour activer le critère de localisation.')
        if components['education'] < 0.1 and profile['education']:
            suggestions.append('Précisez l’intitulé exact de votre formation et ses matières principales.')

        details = [f"{COMPONENT_LABELS['skills']} : {len(matched)} sur {len(requirements)} compétence(s) repérée(s) dans l’offre → {contributions['skills']} / {weights['skills']} pts."
                   if requirements else f"{COMPONENT_LABELS['skills']} : aucune compétence du vocabulaire contrôlé n’a été repérée dans l’offre → 0 pt.",
                   f"{COMPONENT_LABELS['education']} : similarité textuelle {round(components['education']*100)} % → {contributions['education']} / {weights['education']} pts.",
                   f"{COMPONENT_LABELS['experience']} : similarité textuelle {round(components['experience']*100)} % → {contributions['experience']} / {weights['experience']} pts.",
                   f"{COMPONENT_LABELS['location']} : " + ('offre à distance, sans comparaison de villes' if remote else f'offre à {city}' + (' (ville déduite du texte de l’offre)' if inferred_city else '') if city else 'ville de l’offre inconnue') +
                   (f', votre ville : {profile["location"]}' if profile['location'] else ', votre ville n’est pas renseignée') + f" → {contributions['location']} / {weights['location']} pts.",
                   f"{COMPONENT_LABELS['opportunity']} : offre « {offer_type or 'non précisé'} », recherche « {profile['opportunity'] or 'non précisée'} » → {contributions['opportunity']} / {weights['opportunity']} pts."]

        results.append({
            'offer': offer, 'score': score, 'score_label': score_label(score),
            'components': {k: round(v*100, 2) for k, v in components.items()},
            'weights': weights, 'contributions': contributions, 'matched': matched, 'missing': missing,
            'optional_skills': optional,
            'common_keywords': common_keywords, 'strengths': strengths, 'suggestions': suggestions,
            'details': details, 'uncertain': uncertain, 'city_inferred': bool(inferred_city),
            'explanation': interpretation.get('explanation') or f'{len(matched)} compétence(s) retrouvée(s) sur {len(requirements)} repérée(s). Comparaison textuelle du domaine et des projets.',
            'recommendation': interpretation.get('recommendation') or ('Précisez vos projets liés à '+', '.join(missing[:4])+', uniquement si vous les avez réalisés.' if missing else 'Ajoutez des exemples concrets et vérifiables de vos projets.'),
            'limitations': 'Le télétravail ne vaut pas correspondance de villes.' if remote else 'Localisation inconnue : composante à zéro.' if not city else ('Ville déduite du texte de l’offre, à vérifier.' if inferred_city else ''),
        })
    return sorted(results, key=lambda item: (-item['score'], item['offer']['ID']))
