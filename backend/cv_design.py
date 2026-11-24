"""Personnalisation du CV : modèles, palettes de couleurs et photo facultative.

La photo n'est jamais obligatoire. Une image envoyée est décodée par Pillow, vérifiée
(format, poids, dimensions, bombe de décompression), recadrée en carré et ré-encodée en
JPEG sans métadonnées. Aucun fichier n'est écrit sur disque ni exécuté : l'image
normalisée reste dans le profil CV chiffré.
"""
from __future__ import annotations

import base64
import binascii
import io
import re

TEMPLATES = {
    'modern': 'Moderne · bandeau',
    'ats': 'Professionnel · ATS',
    'elegant': 'Élégant · deux colonnes',
    'minimal': 'Minimaliste',
    'classic': 'Classique · centré',
}
# Les lecteurs ATS gèrent mal les images : la photo n'est pas imprimée dans ce modèle.
TEMPLATES_WITHOUT_PHOTO = {'ats'}

COLOR_KEYS = ('primary', 'secondary', 'heading', 'accent', 'section_bg')
COLOR_LABELS = {'primary': 'Couleur principale', 'secondary': 'Couleur secondaire', 'heading': 'Couleur des titres',
                'accent': 'Éléments graphiques', 'section_bg': 'Fond des sections'}

PALETTES = {
    'bleu': {'label': 'Bleu professionnel', 'primary': '#11213D', 'secondary': '#3D5A80', 'heading': '#215CF3',
             'accent': '#215CF3', 'section_bg': '#EEF3FB'},
    'noir': {'label': 'Noir et blanc', 'primary': '#111111', 'secondary': '#4A4A4A', 'heading': '#111111',
             'accent': '#111111', 'section_bg': '#F2F2F2'},
    'vert': {'label': 'Vert moderne', 'primary': '#0F5132', 'secondary': '#2E7D5B', 'heading': '#146C43',
             'accent': '#20A97A', 'section_bg': '#EAF7F0'},
    'bordeaux': {'label': 'Bordeaux élégant', 'primary': '#5C1A2B', 'secondary': '#8A3B4E', 'heading': '#6D1F33',
                 'accent': '#B08D57', 'section_bg': '#F8EEF0'},
    'gris': {'label': 'Gris minimaliste', 'primary': '#2F3437', 'secondary': '#6B7280', 'heading': '#374151',
             'accent': '#9CA3AF', 'section_bg': '#F3F4F6'},
    'violet': {'label': 'Violet moderne', 'primary': '#3B1F73', 'secondary': '#6D4BB3', 'heading': '#4C2A92',
               'accent': '#8B5CF6', 'section_bg': '#F3EEFD'},
}
DEFAULT_PALETTE = 'bleu'
HEX = re.compile(r'#[0-9A-Fa-f]{6}')

PHOTO_FORMATS = {'JPEG', 'PNG', 'WEBP'}
PHOTO_MAX_BYTES = 4 * 1024 * 1024
PHOTO_MIN_SIDE = 96
PHOTO_MAX_SIDE = 6000
PHOTO_OUTPUT_SIDE = 600
PHOTO_SHAPES = ('circle', 'square')


def default_design():
    palette = PALETTES[DEFAULT_PALETTE]
    return {'palette': DEFAULT_PALETTE, **{key: palette[key] for key in COLOR_KEYS}}


def validate_design(value):
    """Palette prédéfinie ou couleurs personnalisées #RRGGBB. Absent → palette par défaut."""
    if value in (None, '', {}):
        return default_design()
    if not isinstance(value, dict):
        raise ValueError('Paramètres de couleurs invalides.')
    palette = value.get('palette') or 'custom'
    if palette != 'custom' and palette not in PALETTES:
        raise ValueError('Palette de couleurs inconnue.')
    base = PALETTES.get(palette, PALETTES[DEFAULT_PALETTE])
    result = {'palette': palette}
    for key in COLOR_KEYS:
        color = value.get(key) or base[key]
        if not isinstance(color, str) or not HEX.fullmatch(color.strip()):
            raise ValueError(f'{COLOR_LABELS[key]} : couleur invalide (format #RRGGBB attendu).')
        result[key] = color.strip().upper()
    return result


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    channel = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * channel[0] + 0.7152 * channel[1] + 0.0722 * channel[2]


def contrast_ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_text_on(background):
    """Blanc ou quasi-noir selon le meilleur contraste (WCAG)."""
    return '#FFFFFF' if contrast_ratio(background, '#FFFFFF') >= contrast_ratio(background, '#111111') else '#111111'


def mix(color, other, weight):
    """Mélange deux couleurs hexadécimales (weight = part de ``other``)."""
    a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x * (1 - weight) + y * weight):02X}' for x, y in zip(a, b))


def contrast_warnings(design):
    warnings = []
    if contrast_ratio(design['heading'], '#FFFFFF') < 3:
        warnings.append('Les titres risquent d’être peu lisibles sur fond blanc : choisissez une couleur plus foncée.')
    if contrast_ratio(design['heading'], design['section_bg']) < 3:
        warnings.append('Le contraste entre la couleur des titres et le fond des sections est faible.')
    if contrast_ratio(design['secondary'], '#FFFFFF') < 3:
        warnings.append('La couleur secondaire est claire : le texte qui l’utilise peut être difficile à lire à l’impression.')
    return warnings


# ----------------------------------------------------------------------- photo
def _decode_data_url(value):
    if not isinstance(value, str):
        raise ValueError('Photo invalide.')
    match = re.fullmatch(r'data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\s]+)', value.strip())
    if not match:
        raise ValueError('Photo : seuls les formats JPEG, PNG ou WEBP encodés sont acceptés.')
    try:
        raw = base64.b64decode(match.group(2), validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('Photo endommagée.') from exc
    return raw


def _open_image(raw):
    from PIL import Image, UnidentifiedImageError
    if not raw or len(raw) > PHOTO_MAX_BYTES:
        raise ValueError('Photo trop volumineuse (4 Mo maximum) ou vide.')
    Image.MAX_IMAGE_PIXELS = 40_000_000
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()  # contrôle d'intégrité sans décoder les pixels
        image = Image.open(io.BytesIO(raw))
        fmt = image.format
        if fmt not in PHOTO_FORMATS:
            raise ValueError('Photo : format non autorisé (JPEG, PNG ou WEBP uniquement).')
        if getattr(image, 'is_animated', False) and getattr(image, 'n_frames', 1) > 1:
            raise ValueError('Photo : les images animées ne sont pas acceptées.')
        width, height = image.size
        if min(width, height) < PHOTO_MIN_SIDE or max(width, height) > PHOTO_MAX_SIDE:
            raise ValueError(f'Photo : dimensions entre {PHOTO_MIN_SIDE} et {PHOTO_MAX_SIDE} pixels requises.')
        image.load()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ValueError('Photo illisible ou non sûre.') from exc
    return image, fmt


def _to_rgb(image):
    from PIL import Image
    from PIL import ImageOps
    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGBA')
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        return background
    return image.convert('RGB')


def _jpeg_data_url(image, quality=88):
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=quality, optimize=True)  # aucune métadonnée copiée
    return 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def sanitize_upload(raw, max_side=1200):
    """Upload brut → aperçu JPEG normalisé (proportions conservées) pour le recadrage côté navigateur."""
    image, _ = _open_image(raw)
    image = _to_rgb(image)
    image.thumbnail((max_side, max_side))
    return {'image': _jpeg_data_url(image), 'width': image.size[0], 'height': image.size[1]}


def normalize_photo(value):
    """Photo facultative : None si absente ou désactivée, sinon dictionnaire validé."""
    if value in (None, '', {}):
        return None
    if not isinstance(value, dict):
        raise ValueError('Photo invalide.')
    if value.get('enabled') is False or not value.get('image'):
        return None
    shape = value.get('shape', 'circle')
    if shape not in PHOTO_SHAPES:
        raise ValueError('Forme de photo inconnue (cercle ou carré).')
    try:
        size = int(value.get('size', 90))
    except (TypeError, ValueError) as exc:
        raise ValueError('Taille de photo invalide.') from exc
    if not 60 <= size <= 140:
        raise ValueError('La taille de la photo doit être comprise entre 60 et 140 points.')
    raw = _decode_data_url(value['image'])
    image, fmt = _open_image(raw)
    width, height = image.size
    already_clean = (fmt == 'JPEG' and width == height and width <= PHOTO_OUTPUT_SIDE
                     and not image.info.get('exif') and image.mode == 'RGB')
    if already_clean:
        data_url = 'data:image/jpeg;base64,' + base64.b64encode(raw).decode('ascii')
    else:
        image = _to_rgb(image)
        side = min(image.size)
        left, top = (image.size[0] - side) // 2, (image.size[1] - side) // 2
        image = image.crop((left, top, left + side, top + side))
        if side > PHOTO_OUTPUT_SIDE:
            image = image.resize((PHOTO_OUTPUT_SIDE, PHOTO_OUTPUT_SIDE))
        data_url = _jpeg_data_url(image)
    return {'enabled': True, 'image': data_url, 'shape': shape, 'size': size}


def photo_bytes(photo):
    return base64.b64decode(photo['image'].split(',', 1)[1])
