"""Qualité des données collectées : nettoyage, dates, URLs, doublons, statut."""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit

FR_MONTHS = {'janvier': 1, 'fevrier': 2, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7,
             'aout': 8, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'decembre': 12, 'décembre': 12}
AR_MONTHS = {'يناير': 1, 'فبراير': 2, 'مارس': 3, 'أبريل': 4, 'ابريل': 4, 'ماي': 5, 'مايو': 5, 'يونيو': 6, 'يوليوز': 7,
             'يوليو': 7, 'غشت': 8, 'أغسطس': 8, 'شتنبر': 9, 'سبتمبر': 9, 'أكتوبر': 10, 'اكتوبر': 10, 'نونبر': 11,
             'نوفمبر': 11, 'دجنبر': 12, 'ديسمبر': 12}
CITY_ALIASES = {'marrakech': 'Marrakech', 'marrakesh': 'Marrakech', 'مراكش': 'Marrakech', 'casablanca': 'Casablanca',
                'الدار البيضاء': 'Casablanca', 'rabat': 'Rabat', 'الرباط': 'Rabat', 'tanger': 'Tanger', 'tangier': 'Tanger', 'طنجة': 'Tanger',
                'agadir': 'Agadir', 'أكادير': 'Agadir', 'fes': 'Fès', 'fès': 'Fès', 'فاس': 'Fès', 'meknes': 'Meknès',
                'mèknès': 'Meknès', 'meknès': 'Meknès', 'مكناس': 'Meknès', 'oujda': 'Oujda', 'وجدة': 'Oujda',
                'kenitra': 'Kénitra', 'kénitra': 'Kénitra', 'القنيطرة': 'Kénitra',
                'tetouan': 'Tétouan', 'tétouan': 'Tétouan', 'تطوان': 'Tétouan',
                'safi': 'Safi', 'آسفي': 'Safi', 'essaouira': 'Essaouira', 'الصويرة': 'Essaouira', 'el jadida': 'El Jadida',
                'الجديدة': 'El Jadida', 'beni mellal': 'Béni Mellal', 'بني ملال': 'Béni Mellal', 'ouarzazate': 'Ouarzazate'}
DEADLINE_MARKERS = r'(?:date limite|dernier délai|délai|avant le|jusqu[’\']au|آخر أجل|اخر اجل|قبل)'
VERIFICATION = ('non_verifiee', 'verifiee_manuellement', 'expiree')


def clean(value, limit=500):
    value = html.unescape(re.sub(r'<[^>]+>', ' ', str(value or '')))
    return re.sub(r'\s+', ' ', value).strip()[:limit]


def _fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(c))


def normalize_date(value):
    """Retourne une date ISO (AAAA-MM-JJ) ou None. Formats : ISO, RFC 822, JJ/MM/AAAA, '12 mars 2026', arabe."""
    if value in (None, ''):
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).date().isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    match = re.search(r'\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b', text)
    if match:
        day, month, year = map(int, match.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    folded = _fold(text)
    for name, month in {**FR_MONTHS, **AR_MONTHS}.items():
        key = _fold(name) if name in FR_MONTHS else name
        found = re.search(r'(\d{1,2})\s*(?:er)?\s+' + re.escape(key) + r'\s+(\d{4})', folded if name in FR_MONTHS else text)
        if found:
            try:
                return date(int(found.group(2)), month, int(found.group(1))).isoformat()
            except ValueError:
                return None
    return None


def deadline_from(text):
    """Date limite seulement si un marqueur explicite précède la date (jamais devinée)."""
    raw = str(text or '')
    for match in re.finditer(DEADLINE_MARKERS + r'[^\d]{0,25}([\d/.\-]{8,10}|\d{1,2}\s*(?:er)?\s+\S+\s+\d{4})', raw, re.IGNORECASE):
        found = normalize_date(match.group(1))
        if found:
            return found
    return None


def city_from(text):
    lowered = str(text or '').lower()
    for alias, city in CITY_ALIASES.items():
        if re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', lowered):
            return city
    return None


def opportunity_type(text):
    folded = _fold(text)
    if re.search(r'\bpfe\b|projet de fin', folded):
        return 'Stage PFE'
    if re.search(r'\bstage|stagiaire|internship|تدريب', folded):
        return 'Stage'
    if re.search(r'concours|مباراة|مباريات', folded + ' ' + str(text)):
        return 'Concours'
    if re.search(r'\bcdi\b|\bcdd\b|emploi|recrut|توظيف', folded + ' ' + str(text)):
        return 'Emploi'
    return 'Non précisé'


def valid_url(value, allowed_hosts):
    try:
        parts = urlsplit(str(value or '').strip())
    except ValueError:
        return None
    host = (parts.hostname or '').lower()
    if parts.scheme != 'https' or parts.username or parts.password or not host:
        return None
    if not any(host == h or host.endswith('.' + h) for h in allowed_hosts):
        return None
    return urlunsplit(('https', host, parts.path or '/', parts.query, ''))


def dedupe_key(title, organization, city, url):
    if url:
        from ..collectors.schema import canonical_url
        address = canonical_url(url)
        if address:
            return 'url:' + hashlib.sha256(address.encode()).hexdigest()[:24]
    material = '|'.join(re.sub(r'[\W_]+', ' ', _fold(x or '')).strip() for x in (title, organization, city))
    return 'txt:' + hashlib.sha256(material.encode()).hexdigest()[:24]


def status_for(deadline):
    if not deadline:
        return 'unknown'
    return 'expired' if date.fromisoformat(deadline) < date.today() else 'active'


def parse_feed(xml_text, limit=100):
    """RSS 2.0 / Atom générique. Retourne des dictionnaires bruts (titre, lien, date, résumé, catégories, auteur)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError('Flux XML illisible.') from exc
    def local(tag):
        return tag.rsplit('}', 1)[-1].lower()
    items = [node for node in root.iter() if local(node.tag) in ('item', 'entry')]
    out = []
    for node in items[:limit]:
        record = {'categories': []}
        for child in node:
            key = local(child.tag)
            if key == 'link':
                record['link'] = child.attrib.get('href') or (child.text or '').strip()
            elif key == 'category':
                record['categories'].append(child.attrib.get('term') or (child.text or '').strip())
            elif key in ('title', 'description', 'summary', 'pubdate', 'published', 'updated', 'guid', 'id', 'creator', 'author'):
                record[key] = (child.text or '').strip() or ''.join(child.itertext()).strip()
        out.append(record)
    return out


def build_record(raw, source, allowed_hosts, store_description=False):
    """Champ par champ, uniquement ce qui est permis. Retourne (record, erreurs)."""
    errors = []
    title = clean(raw.get('title'), 300)
    url = valid_url(raw.get('link') or raw.get('guid') or raw.get('id'), allowed_hosts)
    if not title:
        errors.append('titre manquant')
    if not url:
        errors.append('URL absente ou hors du site source')
    text = ' '.join([raw.get('title') or '', clean(raw.get('description') or raw.get('summary'), 3000), ' '.join(raw.get('categories') or [])])
    published = normalize_date(raw.get('pubdate') or raw.get('published') or raw.get('updated'))
    deadline = deadline_from(text)
    organization = clean(raw.get('organization') or raw.get('creator') or raw.get('author'), 200) or None
    if not organization:
        match = re.search(r'(?:chez|at|@)\s+([A-ZÀ-Ý][\w&.\'’ -]{2,60})', raw.get('title') or '')
        organization = clean(match.group(1), 200) if match else None
    record = {
        'title': title, 'organization': organization, 'city': city_from(text), 'opportunity_type': opportunity_type(text),
        'published_at': published, 'deadline': deadline, 'url': url, 'source': source,
        'collected_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'verification_status': 'expiree' if status_for(deadline) == 'expired' else 'non_verifiee',
        'status': status_for(deadline), 'description': clean(raw.get('description') or raw.get('summary'), 3000) if store_description else '',
    }
    record['dedupe_key'] = dedupe_key(title, organization, record['city'], url)
    return (None if errors else record), errors


def deduplicate(records):
    seen, unique, duplicates = set(), [], 0
    for record in records:
        if record['dedupe_key'] in seen:
            duplicates += 1
            continue
        seen.add(record['dedupe_key'])
        unique.append(record)
    return unique, duplicates
