"""Rendu PDF A4 des modèles de CV (ReportLab).

Chaque modèle garde une hiérarchie claire : identité → profil → expériences/formation →
compétences. Les couleurs viennent de ``data['design']`` (validé) et la photo, facultative,
de ``data['photo']`` (image JPEG normalisée).
"""
from __future__ import annotations

import io
from html import escape
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, FrameBreak, HRFlowable, KeepTogether,
                                NextPageTemplate, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from .cv_design import TEMPLATES_WITHOUT_PHOTO, mix, photo_bytes, readable_text_on

SECTIONS = {'education': 'Formation', 'experience': 'Expériences professionnelles', 'projects': 'Projets',
            'certifications': 'Certifications'}
MAIN_ORDER = ('experience', 'education', 'projects', 'certifications')
WIDTH, HEIGHT = A4
MARGIN = 40


def _fonts():
    if 'CV' in pdfmetrics.getRegisteredFontNames():
        return
    folder = Path(reportlab.__file__).parent / 'fonts'
    pdfmetrics.registerFont(TTFont('CV', str(folder / 'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('CV-Bold', str(folder / 'VeraBd.ttf')))
    pdfmetrics.registerFont(TTFont('CV-Italic', str(folder / 'VeraIt.ttf')))
    pdfmetrics.registerFont(TTFont('CV-BoldItalic', str(folder / 'VeraBI.ttf')))
    pdfmetrics.registerFontFamily('CV', normal='CV', bold='CV-Bold', italic='CV-Italic', boldItalic='CV-BoldItalic')


class Photo(Flowable):
    """Photo ronde ou carrée, dessinée avec un découpage vectoriel (aucun fichier temporaire)."""

    def __init__(self, photo, border, align='LEFT'):
        super().__init__()
        self.size = float(photo['size'])
        self.shape = photo['shape']
        self.image = ImageReader(io.BytesIO(photo_bytes(photo)))
        self.border = colors.HexColor(border)
        self.hAlign = align

    def wrap(self, available_width, available_height):
        return self.size, self.size

    def draw(self):
        c, s = self.canv, self.size
        c.saveState()
        path = c.beginPath()
        if self.shape == 'circle':
            path.circle(s / 2, s / 2, s / 2)
        else:
            path.roundRect(0, 0, s, s, 6)
        c.clipPath(path, stroke=0, fill=0)
        c.drawImage(self.image, 0, 0, width=s, height=s, preserveAspectRatio=True, anchor='c', mask='auto')
        c.restoreState()
        c.saveState()
        c.setStrokeColor(self.border)
        c.setLineWidth(1.6)
        if self.shape == 'circle':
            c.circle(s / 2, s / 2, s / 2 - 0.8, stroke=1, fill=0)
        else:
            c.roundRect(0.8, 0.8, s - 1.6, s - 1.6, 6, stroke=1, fill=0)
        c.restoreState()


class Builder:
    def __init__(self, data, template):
        _fonts()
        self.data, self.template = data, template
        self.section_order = data.get('section_order', MAIN_ORDER)
        self.d = data['design']
        self.photo = data.get('photo') if template not in TEMPLATES_WITHOUT_PHOTO else None
        body = colors.HexColor('#26374C')
        self.s = {
            'body': ParagraphStyle('body', fontName='CV', fontSize=9.2, leading=13.6, spaceAfter=4, textColor=body,
                                   splitLongWords=True),
            'small': ParagraphStyle('small', fontName='CV', fontSize=8.4, leading=12, textColor=body, spaceAfter=3),
            'entry': ParagraphStyle('entry', fontName='CV-Bold', fontSize=9.6, leading=13.4,
                                    textColor=colors.HexColor('#1B2533')),
            'meta': ParagraphStyle('meta', fontName='CV-Italic', fontSize=8.4, leading=12,
                                   textColor=colors.HexColor(self.d['secondary']), spaceAfter=2),
            'heading': ParagraphStyle('heading', fontName='CV-Bold', fontSize=10.6, leading=15,
                                      textColor=colors.HexColor(self.d['heading']), spaceBefore=11, spaceAfter=5),
            'name': ParagraphStyle('name', fontName='CV-Bold', fontSize=24, leading=29,
                                   textColor=colors.HexColor(self.d['primary']), spaceAfter=3),
            'title': ParagraphStyle('title', fontName='CV', fontSize=12.4, leading=17,
                                    textColor=colors.HexColor(self.d['secondary']), spaceAfter=6),
            'contact': ParagraphStyle('contact', fontName='CV', fontSize=8.6, leading=12.4, textColor=body),
        }

    # ------------------------------------------------------------ helpers
    def p(self, value, style='body', **overrides):
        style_obj = self.s[style]
        if overrides:
            style_obj = ParagraphStyle(style + str(id(overrides)), parent=style_obj, **overrides)
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), style_obj)

    def contacts(self):
        return [self.data[k] for k in ('email', 'phone', 'city') if self.data.get(k)]

    def links(self):
        return [self.data[k] for k in ('linkedin', 'github', 'portfolio') if self.data.get(k)]

    def heading(self, label, width=None, band=False, centered=False):
        if not band:
            return [self.p(label.upper() if self.template == 'minimal' else label, 'heading',
                           alignment=TA_CENTER if centered else TA_LEFT),
                    HRFlowable(width='100%', thickness=0.8 if self.template != 'minimal' else 0.4,
                               color=colors.HexColor(self.d['accent']), spaceBefore=0, spaceAfter=5)]
        table = Table([[self.p(label, 'heading', spaceBefore=0, spaceAfter=0,
                               alignment=TA_CENTER if centered else TA_LEFT)]], colWidths=[width])
        edge = (('LINEBELOW', (0, 0), (-1, -1), 1.2, colors.HexColor(self.d['accent'])) if centered
                else ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor(self.d['accent'])))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(self.d['section_bg'])), edge,
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        return [Spacer(1, 9), table, Spacer(1, 5)]

    def entries(self, key):
        """Une liste de flowables par entrée (sans KeepTogether imbriqué)."""
        blocks = []
        for item in self.data.get(key) or []:
            parts = []
            if item.get('title') or item.get('organization'):
                parts.append(self.p(' · '.join(x for x in (item.get('title'), item.get('organization')) if x), 'entry'))
            if item.get('period'):
                parts.append(self.p(item['period'], 'meta'))
            if item.get('description'):
                parts.append(self.p(item['description']))
            parts.append(Spacer(1, 4))
            blocks.append(parts)
        return blocks

    def section(self, key, label, width, band=False, centered=False):
        body = self.entries(key)
        if not body:
            return []
        story = [KeepTogether(self.heading(label, width, band, centered) + body[0])]
        for parts in body[1:]:
            story.append(KeepTogether(parts))
        return story

    def text_section(self, key, label, width, band=False, centered=False):
        if not self.data.get(key):
            return []
        return [KeepTogether(self.heading(label, width, band, centered) + [self.p(self.data[key])])]

    def skills_block(self, width, band=False):
        flow = []
        for key, label in (('technical', 'Compétences techniques'), ('soft', 'Compétences personnelles'),
                           ('languages', 'Langues')):
            flow += self.text_section(key, label, width, band)
        return flow

    def footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('CV', 7.5)
        canvas.setFillColor(colors.HexColor('#7A8597'))
        canvas.drawRightString(WIDTH - MARGIN, 22, str(doc.page))
        canvas.restoreState()

    # ------------------------------------------------------------ modèles
    def modern(self):
        width = WIDTH - 2 * MARGIN
        band_text = readable_text_on(self.d['primary'])
        light = mix(self.d['primary'], '#FFFFFF', 0.72) if band_text == '#FFFFFF' else mix(self.d['primary'], '#000000', 0.55)
        info = [self.p(self.data['name'], 'name', textColor=colors.HexColor(band_text)),
                self.p(self.data['title'], 'title', textColor=colors.HexColor(light))]
        line = '  |  '.join(self.contacts())
        if line:
            info.append(self.p(line, 'contact', textColor=colors.HexColor(light)))
        for value in self.links():
            info.append(self.p(value, 'contact', textColor=colors.HexColor(light)))
        if self.photo:
            cells, widths = [[Photo(self.photo, self.d['accent']), info]], [self.photo['size'] + 18, width - self.photo['size'] - 18]
        else:
            cells, widths = [[info]], [width]
        band = Table(cells, colWidths=widths)
        band.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(self.d['primary'])),
                                  ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 16), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                                  ('TOPPADDING', (0, 0), (-1, -1), 16), ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
                                  ('LINEBELOW', (0, 0), (-1, -1), 3, colors.HexColor(self.d['accent']))]))
        story = [band, Spacer(1, 6)]
        story += self.text_section('summary', 'Profil', width, band=True)
        for key in self.section_order:
            story += self.section(key, SECTIONS[key], width, band=True)
        story += self.skills_block(width, band=True)
        return self.simple_doc(story)

    def ats(self):
        width = WIDTH - 2 * MARGIN
        story = [self.p(self.data['name'], 'name'), self.p(self.data['title'], 'title')]
        if self.contacts():
            story.append(self.p('  |  '.join(self.contacts()), 'contact'))
        for value in self.links():
            story.append(self.p(value, 'contact'))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor(self.d['accent']), spaceBefore=8, spaceAfter=4))
        story += self.text_section('summary', 'Profil', width)
        for key in self.section_order:
            story += self.section(key, SECTIONS[key], width)
        story += self.skills_block(width)
        return self.simple_doc(story)

    def minimal(self):
        width = WIDTH - 2 * MARGIN - 14
        ident = [self.p(self.data['name'], 'name', fontSize=26, leading=30),
                 self.p(self.data['title'], 'title'),
                 self.p('   ·   '.join(self.contacts() + self.links()), 'small')]
        if self.photo:
            head = Table([[ident, Photo(self.photo, self.d['accent'], 'RIGHT')]],
                         colWidths=[width - self.photo['size'] - 6, self.photo['size'] + 6])
            head.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                      ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
            story = [head]
        else:
            story = ident
        story.append(Spacer(1, 12))
        story += self.text_section('summary', 'Profil', width)
        for key in self.section_order:
            story += self.section(key, SECTIONS[key], width)
        story += self.skills_block(width)
        return self.simple_doc(story, margin=MARGIN + 7)

    def classic(self):
        width = WIDTH - 2 * MARGIN
        story = []
        if self.photo:
            story += [Photo(self.photo, self.d['accent'], 'CENTER'), Spacer(1, 6)]
        story += [self.p(self.data['name'], 'name', alignment=TA_CENTER),
                  self.p(self.data['title'], 'title', alignment=TA_CENTER)]
        line = '  ·  '.join(self.contacts() + self.links())
        if line:
            story.append(self.p(line, 'contact', alignment=TA_CENTER))
        story.append(HRFlowable(width='40%', thickness=1.4, color=colors.HexColor(self.d['accent']), spaceBefore=8,
                                spaceAfter=2, hAlign='CENTER'))
        story += self.text_section('summary', 'Profil', width, band=True, centered=True)
        for key in self.section_order:
            story += self.section(key, SECTIONS[key], width, band=True, centered=True)
        story += self.skills_block(width, band=True)
        return self.simple_doc(story)

    def elegant(self):
        side_w = 170
        gap = 18
        main_w = WIDTH - side_w - gap - 2 * MARGIN + 10
        output = io.BytesIO()
        doc = BaseDocTemplate(output, pagesize=A4, title=self.data['title'], author=self.data['name'], invariant=1,
                              leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
        side = Frame(18, MARGIN, side_w, HEIGHT - 2 * MARGIN, id='side', leftPadding=8, rightPadding=8)
        main = Frame(18 + side_w + gap, MARGIN, main_w, HEIGHT - 2 * MARGIN, id='main', leftPadding=0, rightPadding=4)
        later = Frame(MARGIN, MARGIN, WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN, id='later')

        def first_page(canvas, document):
            canvas.saveState()
            canvas.setFillColor(colors.HexColor(self.d['section_bg']))
            canvas.rect(0, 0, 18 + side_w + 8, HEIGHT, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor(self.d['accent']))
            canvas.rect(18 + side_w + 8, 0, 2.5, HEIGHT, stroke=0, fill=1)
            canvas.restoreState()
            self.footer(canvas, document)

        doc.addPageTemplates([PageTemplate('first', [side, main], onPage=first_page),
                              PageTemplate('later', [later], onPage=self.footer)])
        side_text = readable_text_on(self.d['section_bg'])
        sidebar = []
        if self.photo:
            sidebar += [Photo(self.photo, self.d['accent'], 'CENTER'), Spacer(1, 12)]

        def side_heading(label):
            return [self.p(label.upper(), 'heading', fontSize=9, spaceBefore=10, spaceAfter=3),
                    HRFlowable(width='100%', thickness=0.6, color=colors.HexColor(self.d['accent']), spaceAfter=4)]

        if self.contacts() or self.links():
            sidebar += side_heading('Contact')
            sidebar += [self.p(v, 'small', textColor=colors.HexColor(side_text)) for v in self.contacts() + self.links()]
        for key, label in (('technical', 'Compétences'), ('soft', 'Qualités'), ('languages', 'Langues')):
            values = [v.strip() for v in str(self.data.get(key) or '').replace(';', ',').replace('\n', ',').split(',') if v.strip()]
            if values:
                sidebar += side_heading(label)
                sidebar += [self.p('• ' + v, 'small', textColor=colors.HexColor(side_text)) for v in values[:30]]
        story = [NextPageTemplate('later')] + sidebar + [FrameBreak()]
        story += [self.p(self.data['name'], 'name'), self.p(self.data['title'], 'title'),
                  HRFlowable(width=60, thickness=3, color=colors.HexColor(self.d['accent']), spaceAfter=6, hAlign='LEFT')]
        story += self.text_section('summary', 'Profil', main_w)
        for key in self.section_order:
            story += self.section(key, SECTIONS[key], main_w)
        doc.build(story)
        return output.getvalue()

    def simple_doc(self, story, margin=MARGIN):
        output = io.BytesIO()
        doc = BaseDocTemplate(output, pagesize=A4, title=self.data['title'], author=self.data['name'], invariant=1,
                              leftMargin=margin, rightMargin=margin, topMargin=36, bottomMargin=40)
        frame = Frame(margin, 40, WIDTH - 2 * margin, HEIGHT - 76, id='body', leftPadding=0, rightPadding=0)
        doc.addPageTemplates([PageTemplate('page', [frame], onPage=self.footer)])
        doc.build(story)
        return output.getvalue()


def build_pdf(data, template):
    builder = Builder(data, template)
    return getattr(builder, template)()
