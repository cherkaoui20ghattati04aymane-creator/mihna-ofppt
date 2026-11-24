import io
import re
from pypdf import PdfReader
from .validation import text, email, safe_url
from .cv_design import TEMPLATES, validate_design, normalize_photo

SECTIONS = {
    'education': 'Formation', 'experience': 'Expériences professionnelles', 'projects': 'Projets',
    'certifications': 'Certifications',
}


def validate_cv(data):
    if not isinstance(data, dict):
        raise ValueError('Profil CV invalide.')
    result = {}
    limits={'name':120,'title':200,'email':254,'phone':80,'city':120,'summary':6000,'technical':2000,'soft':2000,'languages':1000,'linkedin':500,'github':500,'portfolio':500}
    for field in ('name', 'title', 'email', 'phone', 'city', 'summary', 'technical', 'soft', 'languages', 'linkedin', 'github', 'portfolio'):
        result[field] = text(data.get(field, ''), limits[field])
    if not result['name'] or not result['title']:
        raise ValueError('Nom et titre professionnel obligatoires.')
    if result['email']:
        result['email'] = email(result['email'])
    for field in ('linkedin', 'github', 'portfolio'):
        if result[field] and not safe_url(result[field]):
            raise ValueError('Les liens doivent commencer par https:// ou http://.')
    for section in SECTIONS:
        entries = data.get(section, [])
        if not isinstance(entries, list) or len(entries) > 30:
            raise ValueError('Section CV invalide ou trop longue.')
        result[section] = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError('Entrée CV invalide.')
            entry = {k: text(item.get(k, ''), {'title':200,'organization':200,'period':100,'description':4000}[k]) for k in ('title', 'organization', 'period', 'description')}
            dates = re.findall(r'(?<!\d)(19\d{2}|20\d{2})(?:[-/.](0?[1-9]|1[0-2]))?(?!\d)', entry['period'])
            if len(dates) >= 2 and (int(dates[0][0]), int(dates[0][1] or 0)) > (int(dates[-1][0]), int(dates[-1][1] or 0)):
                raise ValueError('Une période CV ne peut pas se terminer avant sa date de début.')
            if any(entry.values()):
                result[section].append(entry)
    # Personnalisation : couleurs validées (#RRGGBB) et photo facultative re-encodée.
    result['design'] = validate_design(data.get('design'))
    order = data.get('section_order', ['experience', 'education', 'projects', 'certifications'])
    if not isinstance(order, list) or len(order) != 4 or any(not isinstance(item, str) for item in order) or set(order) != {'education', 'experience', 'projects', 'certifications'}:
        raise ValueError('Ordre des rubriques CV invalide.')
    result['section_order'] = order
    photo = normalize_photo(data.get('photo'))
    if photo:
        result['photo'] = photo
    return result


def extract_pdf(content):
    if not content or len(content) > 5 * 1024 * 1024 or not content.startswith(b'%PDF-'):
        raise ValueError('PDF invalide ou supérieur à 5 Mo.')
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted or len(reader.pages) > 15 or not len(reader.pages):
            raise ValueError('PDF chiffré, vide ou supérieur à 15 pages.')
        value = '\n'.join((page.extract_text() or '') for page in reader.pages)[:40000]
    except Exception as exc:
        raise ValueError('PDF illisible, chiffré ou endommagé.') from exc
    if not value.strip():
        raise ValueError('Ce PDF ne contient pas de texte lisible. Renseignez votre profil manuellement (OCR non intégré).')
    return value


def make_pdf(data, template='modern'):
    """Génère le PDF A4 du CV avec l’un des modèles de ``cv_design.TEMPLATES``."""
    from .cv_pdf import build_pdf
    data = validate_cv(data)
    if template not in TEMPLATES:
        raise ValueError('Modèle de CV inconnu.')
    return build_pdf(data, template)
