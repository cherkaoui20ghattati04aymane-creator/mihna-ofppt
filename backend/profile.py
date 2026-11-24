"""Validation and CV mapping for an account's encrypted professional profile."""
from __future__ import annotations

from .validation import email as validate_email, safe_url, text


ENTRY_SECTIONS = ('education', 'experience', 'projects', 'certifications')
CV_SECTIONS = ('contact', 'summary', 'education', 'experience', 'projects', 'certifications',
               'skills', 'languages', 'links')
ENTRY_LIMITS = {'title': 200, 'organization': 200, 'period': 100, 'description': 4000}
LIST_LIMITS = {'skills': 80, 'soft_skills': 50, 'languages': 30}


def empty_profile(seed=None):
    seed = seed if isinstance(seed, dict) else {}
    return {
        'first_name': str(seed.get('first_name') or '')[:80],
        'last_name': str(seed.get('last_name') or '')[:80],
        'email': str(seed.get('email') or '')[:254],
        'phone': '', 'city': '', 'country': '', 'headline': '', 'summary': '',
        'education': [], 'experience': [], 'projects': [], 'certifications': [],
        'skills': [], 'soft_skills': [], 'languages': [],
        'links': {'linkedin': '', 'github': '', 'portfolio': ''},
        'cv_sections': list(CV_SECTIONS), 'theme': 'light',
    }


def validate_profile(data):
    if not isinstance(data, dict):
        raise ValueError('Profil invalide.')
    result = empty_profile()
    limits = {'first_name': 80, 'last_name': 80, 'email': 254, 'phone': 80,
              'city': 120, 'country': 100, 'headline': 200, 'summary': 6000}
    for key, limit in limits.items():
        result[key] = text(data.get(key, ''), limit)
    if result['email']:
        result['email'] = validate_email(result['email'])
    for section in ENTRY_SECTIONS:
        entries = data.get(section, [])
        if not isinstance(entries, list) or len(entries) > 30:
            raise ValueError(f'Section {section} invalide.')
        clean = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError(f'Entrée {section} invalide.')
            row = {key: text(item.get(key, ''), limit) for key, limit in ENTRY_LIMITS.items()}
            if any(row.values()):
                clean.append(row)
        result[section] = clean
    for key, maximum in LIST_LIMITS.items():
        values = data.get(key, [])
        if not isinstance(values, list) or len(values) > maximum:
            raise ValueError(f'Liste {key} invalide.')
        cleaned = []
        for value in values:
            if not isinstance(value, str):
                raise ValueError(f'Valeur {key} invalide.')
            item = text(value, 100)
            if item and item not in cleaned:
                cleaned.append(item)
        result[key] = cleaned
    links = data.get('links', {})
    if not isinstance(links, dict):
        raise ValueError('Liens professionnels invalides.')
    for key in ('linkedin', 'github', 'portfolio'):
        value = text(links.get(key, ''), 500)
        if value and not safe_url(value):
            raise ValueError('Les liens professionnels doivent commencer par http:// ou https://.')
        result['links'][key] = value
    selected = data.get('cv_sections', list(CV_SECTIONS))
    if not isinstance(selected, list) or any(item not in CV_SECTIONS for item in selected):
        raise ValueError('Sélection des rubriques du CV invalide.')
    result['cv_sections'] = list(dict.fromkeys(selected))
    theme = data.get('theme', 'light')
    if theme not in ('light', 'dark'):
        raise ValueError('Thème invalide.')
    result['theme'] = theme
    return result


def cv_draft(profile):
    """Create an editable, unsaved CV from only selected facts in the profile."""
    selected = set(profile.get('cv_sections') or ())
    first = profile.get('first_name', '').strip()
    last = profile.get('last_name', '').strip()
    name = ' '.join(part for part in (first, last) if part)
    links = profile.get('links') or {}
    include_contact = 'contact' in selected
    return {
        'name': name,
        'title': profile.get('headline', '') if 'summary' in selected else '',
        'email': profile.get('email', '') if include_contact else '',
        'phone': profile.get('phone', '') if include_contact else '',
        'city': profile.get('city', '') if include_contact else '',
        'summary': profile.get('summary', '') if 'summary' in selected else '',
        'education': profile.get('education', []) if 'education' in selected else [],
        'experience': profile.get('experience', []) if 'experience' in selected else [],
        'projects': profile.get('projects', []) if 'projects' in selected else [],
        'certifications': profile.get('certifications', []) if 'certifications' in selected else [],
        'technical': ', '.join(profile.get('skills') or []) if 'skills' in selected else '',
        'soft': ', '.join(profile.get('soft_skills') or []) if 'skills' in selected else '',
        'languages': ', '.join(profile.get('languages') or []) if 'languages' in selected else '',
        'linkedin': links.get('linkedin', '') if 'links' in selected else '',
        'github': links.get('github', '') if 'links' in selected else '',
        'portfolio': links.get('portfolio', '') if 'links' in selected else '',
        'section_order': ['experience', 'education', 'projects', 'certifications'],
    }
