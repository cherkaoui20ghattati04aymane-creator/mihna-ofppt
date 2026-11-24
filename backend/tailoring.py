"""Factual, local CV tailoring from a saved CV, account Profile, and one offer."""
from __future__ import annotations

import copy
import re

from .matching import norm, skills_from


def _sentences(value: str) -> list[str]:
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+|[\r\n]+', value or '') if part.strip()]


def _merge_entries(cv_entries, profile_entries, section, conflicts):
    merged = [copy.deepcopy(item) for item in (cv_entries or [])]
    exact = {tuple(norm(item.get(key, '')) for key in ('title', 'organization', 'period', 'description'))
             for item in merged}
    by_identity = {}
    for item in merged:
        identity = tuple(norm(item.get(key, '')) for key in ('title', 'organization'))
        if any(identity):
            by_identity.setdefault(identity, []).append(item)
    for item in profile_entries or []:
        key = tuple(norm(item.get(name, '')) for name in ('title', 'organization', 'period', 'description'))
        if key in exact:
            continue
        identity = key[:2]
        if any(identity) and identity in by_identity:
            for previous in by_identity[identity]:
                if previous.get('period') != item.get('period') or previous.get('description') != item.get('description'):
                    conflicts.append({'section': section, 'title': item.get('title', ''),
                                      'cv_period': previous.get('period', ''), 'profile_period': item.get('period', ''),
                                      'note': 'Les rubriques CV et Profil diffèrent. Les deux sont conservées pour vérification.'})
        value = copy.deepcopy(item)
        merged.append(value)
        exact.add(key)
        if any(identity):
            by_identity.setdefault(identity, []).append(value)
    return merged


def _field_text(data):
    values = [data.get(key, '') for key in ('title', 'summary', 'technical', 'soft', 'languages')]
    for section in ('education', 'experience', 'projects', 'certifications'):
        for item in data.get(section) or []:
            values.extend(item.get(key, '') for key in ('title', 'organization', 'period', 'description'))
    return ' '.join(str(value or '') for value in values)


def _rank_entries(items, offer_text):
    terms = skills_from(offer_text)
    indexed = list(enumerate(items or []))
    def rank(pair):
        index, item = pair
        text = ' '.join(str(item.get(key, '') or '') for key in ('title', 'organization', 'period', 'description'))
        matched = [skill for skill in terms if skill in skills_from(text)]
        return (-len(matched), index)
    return [copy.deepcopy(item) for _, item in sorted(indexed, key=rank)]


def _rank_skill_tokens(value, offer_text):
    tokens = [part.strip() for part in re.split(r'[,;|\n•]+', value or '') if part.strip()]
    offer_terms = skills_from(offer_text)
    positions = {term: norm(offer_text).find(norm(term)) for term in offer_terms}
    def rank(pair):
        index, token = pair
        terms = skills_from(token)
        found = [positions[term] for term in terms if term in positions and positions[term] >= 0]
        return (min(found) if found else 10**9, index)
    return ', '.join(token for _, token in sorted(enumerate(tokens), key=rank))


def _requirements(offer_text):
    rows = []
    for snippet in _sentences(offer_text)[:80]:
        clean = snippet[:500]
        normalized = norm(clean)
        if any(word in normalized for word in ('souhait', 'apprecie', 'atout', 'prefer', 'nice to have', 'desirable')):
            category = 'preferred'
        elif any(word in normalized for word in ('experience', 'annee', 'ans ', 'diplome', 'formation', 'licence', 'master', 'bac ')):
            category = 'experience_education'
        elif any(word in normalized for word in ('mission', 'responsabil', 'tache', 'activite', 'contribu', 'particip')):
            category = 'responsibilities'
        else:
            category = 'requirements'
        terms = skills_from(clean)
        rows.append({'category': category, 'text': clean, 'recognized_skills': terms})
    return rows[:40]


def build_tailored_cv(source_cv: dict, profile: dict, offer: dict) -> dict:
    """Return a reordered, unsaved draft and its traceable local analysis.

    The function only reorders existing text and combines exact saved Profile/CV
    facts. It does not generate qualifications, dates, proficiency, or outcomes.
    """
    original = copy.deepcopy(source_cv)
    profile = profile if isinstance(profile, dict) else {}
    offer_text = '\n'.join(str(offer.get(key) or '') for key in ('Titre', 'Description'))
    conflicts = []
    draft = copy.deepcopy(original)
    profile_map = {
        'name': ' '.join(part.strip() for part in (profile.get('first_name', ''), profile.get('last_name', '')) if part.strip()),
        'email': profile.get('email', ''), 'phone': profile.get('phone', ''), 'city': profile.get('city', ''),
        'title': profile.get('headline', ''), 'summary': profile.get('summary', ''),
        'linkedin': (profile.get('links') or {}).get('linkedin', ''),
        'github': (profile.get('links') or {}).get('github', ''),
        'portfolio': (profile.get('links') or {}).get('portfolio', ''),
    }
    profile_fill_fields = []
    for key, value in profile_map.items():
        if not draft.get(key) and value:
            draft[key] = value
            profile_fill_fields.append(key)
    for section in ('education', 'experience', 'projects', 'certifications'):
        draft[section] = _merge_entries(draft.get(section), profile.get(section), section, conflicts)
    for key, profile_values in (('technical', profile.get('skills') or []),
                                ('soft', profile.get('soft_skills') or []),
                                ('languages', profile.get('languages') or [])):
        existing = [part.strip() for part in re.split(r'[,;|\n•]+', str(draft.get(key) or '')) if part.strip()]
        seen = {norm(item) for item in existing}
        for item in profile_values:
            if item and norm(item) not in seen:
                existing.append(item)
                seen.add(norm(item))
        draft[key] = ', '.join(existing)

    profile_cv_sections = {'title': profile.get('headline', ''), 'summary': profile.get('summary', ''),
                           'technical': ', '.join(profile.get('skills') or [])}
    known_text = _field_text(draft) + ' ' + ' '.join(str(value or '') for value in profile_cv_sections.values())
    requirements = list(dict.fromkeys(skills_from(offer_text)))
    ordered_requirements = sorted(requirements, key=lambda item: (norm(offer_text).find(norm(item)) if norm(item) in norm(offer_text) else 10**9, item))
    present = set(skills_from(known_text))
    matched = [item for item in ordered_requirements if item in present]
    missing = [item for item in ordered_requirements if item not in present]

    old_summary = draft.get('summary') or ''
    summary_parts = _sentences(old_summary)
    prioritized = [part for part in summary_parts if set(skills_from(part)).intersection(matched)]
    draft['summary'] = ' '.join(prioritized + [part for part in summary_parts if part not in prioritized])
    draft['technical'] = _rank_skill_tokens(draft.get('technical', ''), offer_text)

    old_orders = {}
    for section in ('experience', 'projects', 'education', 'certifications'):
        old_orders[section] = list(draft.get(section) or [])
        draft[section] = _rank_entries(draft.get(section), offer_text)
    section_base = list(draft.get('section_order') or ['experience', 'education', 'projects', 'certifications'])
    def section_rank(section):
        evidence_text = ' '.join(' '.join(str(v or '') for v in item.values()) for item in draft.get(section, []))
        return -len(set(skills_from(evidence_text)).intersection(matched)), section_base.index(section) if section in section_base else 99
    draft['section_order'] = sorted(['experience', 'education', 'projects', 'certifications'], key=section_rank)

    title = str(offer.get('Titre') or '').strip()
    requirement_rows = _requirements(offer_text)
    evidence = []
    for skill in matched:
        sources = []
        if skill in set(skills_from(_field_text(original))):
            sources.append('CV enregistré')
        profile_text = ' '.join(str(profile.get(key) or '') for key in ('headline', 'summary', 'skills', 'soft_skills', 'languages'))
        for section in ('education', 'experience', 'projects', 'certifications'):
            profile_text += ' ' + ' '.join(' '.join(str(item.get(k) or '') for k in ('title', 'organization', 'period', 'description')) for item in profile.get(section, []) if isinstance(item, dict))
        if skill in set(skills_from(profile_text)):
            sources.append('Profil enregistré')
        evidence.append({'skill': skill, 'sources': sources})

    return {'data': draft, 'analysis': {
        'mode': 'local', 'offer': {'id': offer.get('ID'), 'title': title},
        'source_cv': {'id': None, 'title': original.get('title', '')},
        'profile_fields_added_when_cv_blank': profile_fill_fields,
        'matched_skills': matched, 'missing_requirements': missing,
        'skill_evidence': evidence, 'requirements': requirement_rows,
        'conflicting_profile_entries': conflicts,
        'target_headline_suggestion': {'text': ('Candidature au poste de ' + title) if title else '',
                                       'source': 'Intitulé de l’offre', 'automatically_applied': False},
        'changes': ['Priorité des phrases existantes du résumé', 'Priorité des compétences déjà saisies',
                    'Réorganisation stable des rubriques et entrées existantes'],
        'user_confirmed_additions': [],
        'notice': 'Adaptation locale : seules les informations du CV et du Profil ont été conservées ou réordonnées. Les exigences manquantes sont séparées et aucune donnée n’a été inventée.'
    }}
