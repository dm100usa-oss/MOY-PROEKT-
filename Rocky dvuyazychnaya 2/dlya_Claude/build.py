import json, re, sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import Color

F = '/home/claude/fonts/'
pdfmetrics.registerFont(TTFont('B', F + 'BalsamiqSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('BB', F + 'BalsamiqSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('BI', F + 'BalsamiqSans-Italic.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('B', normal='B', bold='BB', italic='BI', boldItalic='BB')

IMG = '/home/claude/book/img/'
D = json.load(open('/home/claude/book/text.json'))
RAT = json.load(open(IMG + 'ratios.json'))

PW, PH = 8.625 * 72, 11.25 * 72          # страница с запасом под обрез
TW, TH = 8.5 * 72, 11 * 72                # после обреза
GUT, OUT, TOP, BOT = 63, 54, 58, 64       # поля от линии обреза
TXW = TW - GUT - OUT                      # ширина текста 495
TXH = TH - TOP - BOT                      # высота текста
EN_C, ES_C = Color(.08, .08, .08), Color(.22, .22, .22)

sEN = ParagraphStyle('en', fontName='B', fontSize=16, leading=24, textColor=EN_C, alignment=TA_JUSTIFY)
sES = ParagraphStyle('es', parent=sEN, textColor=ES_C)
sT1 = ParagraphStyle('t1', fontName='BB', fontSize=18, leading=23, textColor=EN_C, alignment=TA_CENTER)
sT2 = ParagraphStyle('t2', parent=sT1, textColor=ES_C)
GAP_IN, GAP_PAIR = 6, 26
IMG_MAXH_TEXT, IMG_MAXH_OPEN = 290, 300

TITLES = [('Lucky Rocky and His Friends', 'Rocky el Afortunado y sus amigos'),
          ('About Friendship', 'Acerca de la amistad'),
          ('Lost Glasses', 'Los lentes perdidos'),
          ('Rescuing a Little Mouse', 'El rescate del pequeño ratoncito'),
          ('Hard-Working Bee', 'La laboriosa abejita')]

# картинки по главам: начало, конец, после абзаца (горизонтальные), вертикальные с диапазоном сцены
PLAN = [
    dict(start='friends', end='owl_home', after={25: 'rain_tea'}, vert=[('porch', 1, 3), ('owl_door', 21, 24)]),
    dict(start='owl_hug', end=None, after={16: 'castle', 18: 'owl_beaver', 28: 'beaver_house'},
         vert=[('tea_pudding', 9, 17), ('fish', 30, 30)]),
    dict(start='grandpa', end=None, after={24: 'shelf'}, vert=[('store', 15, 19)]),
    dict(start='boats', end='medals', after={25: 'branch'}, vert=[('max_boat', 7, 12), ('max_cap', 29, 35)]),
    dict(start='owl_reads', end=None, after={11: 'bee_house', 18: 'doctor'},
         vert=[('bee_fly', 22, 24), ('pantry', 28, 31), ('knitting', 32, 38)]),
]


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def para(t, st):
    p = Paragraph(esc(t), st)
    w, h = p.wrap(TXW, 10000)
    return p, h


def sentences(t):
    return re.split(r'(?<=[.!?»"”])\s+(?=[—«"A-ZÁÉÍÓÚÑ¡¿])', t)


def img_box(key, maxh):
    r = RAT[key]
    w = TXW
    h = w * r
    if h > maxh:
        h = maxh; w = h / r
    return w, h



NOSPLIT = {'on': False}
def split_to_fit(chunks, pg):
    """если пара не помещается, а места на странице много, делим её по предложениям"""
    en, es = chunks[0]
    free = TXH - pg['used'] - GAP_PAIR
    pe, he = para(en, sEN); ps, hs = para(es, sES)
    if he + GAP_IN + hs <= free or free < 50:
        return chunks
    se, ss = sentences(en), sentences(es)
    if len(se) < 2 or len(ss) < 2:
        return chunks
    tot_e = len(en)
    cum_s = [len(' '.join(ss[:j])) / len(es) for j in range(len(ss) + 1)]
    for k in range(len(se) - 1, 0, -1):
        r = len(' '.join(se[:k])) / tot_e
        j = min(range(1, len(ss)), key=lambda j: abs(cum_s[j] - r))
        a = (' '.join(se[:k]), ' '.join(ss[:j])); b = (' '.join(se[k:]), ' '.join(ss[j:]))
        h = para(a[0], sEN)[1] + GAP_IN + para(a[1], sES)[1]
        if h <= free:
            return [a, b] + chunks[1:]
    return chunks


import re as _re
MARK = {}
CUR = {'k': 0}
def _prep(ci):
    b = D['blocks'][ci]; pairs = D['chs'][ci]; items = []
    for e, sp in b['words']:
        pe = _re.compile(r'\b(' + _re.escape(e) + r'(?:s|es)?)\b', _re.I)
        n = _re.sub(r'^(el|la|los|las) ', '', sp)
        alt = [_re.escape(n) + '(?:s|es)?']
        if n.endswith('z'): alt.append(_re.escape(n[:-1]) + 'ces')
        ps = _re.compile(r'\b(' + '|'.join(alt) + r')\b', _re.I)
        k = next((i for i, (a, c) in enumerate(pairs, 1) if pe.search(a) and ps.search(c)), None)
        items.append(dict(k=k, en=pe, es=ps, done_en=False, done_es=False))
    return items

def para_m(t, st, ci, lang):
    if ci not in MARK: MARK[ci] = _prep(ci)
    out = esc(t)
    for it in MARK[ci]:
        if it['k'] != CUR['k'] or it['done_' + lang]: continue
        m = it[lang].search(out)
        if m:
            out = out[:m.start()] + '<b>' + m.group(1) + '</b>' + out[m.end():]
            it['done_' + lang] = True
    pp = Paragraph(out, st); w, h = pp.wrap(TXW, 10000)
    return pp, h

# ---------------- раскладка ----------------
pages = []            # каждая: dict(kind, items, num_show, pairs)


def new_text_page():
    pages.append(dict(kind='text', items=[], used=0, pairs=set(), chapter=None))
    return pages[-1]


def add_full(key):
    pages.append(dict(kind='full', key=key))


def layout():
    pages.clear()
    pages.append(dict(kind='fullimg', key='title'))
    pages.append(dict(kind='copyright'))
    pages.append(dict(kind='fullimg', key='p_belongs'))
    pages.append(dict(kind='fullimg', key='p_contents'))
    chap_start = []
    report = []
    for ci, (pairs, plan) in enumerate(zip(D['chs'], PLAN)):
        pending = [dict(key=k, a=a, b=b, done=False) for k, a, b in plan['vert']]
        pg = new_text_page(); chap_start.append(len(pages))
        # начало главы: картинка + название
        if plan['start']:
            w, h = img_box(plan['start'], IMG_MAXH_OPEN)
            pg['items'].append(('img', plan['start'], w, h, 0)); pg['used'] += h + 22
        p1, h1 = para(TITLES[ci][0], sT1); p2, h2 = para(TITLES[ci][1], sT2)
        pg['items'].append(('par', p1, h1, 0)); pg['items'].append(('par', p2, h2, 3))
        pg['used'] += h1 + h2 + 3 + 26

        def finalize(page_idx, last=False):
            """страница закончена: решаем, куда встают вертикальные картинки"""
            nonlocal pg
            P = pages[page_idx]
            inserted = False
            for v in pending:
                if v['done']:
                    continue
                on = {k for k in P['pairs'] if v['a'] <= k <= v['b']}
                if not on:
                    continue
                pno = page_idx + 1
                range_done = max(P['pairs']) >= v['b'] or last
                if pno % 2 == 0 or range_done:
                    if not inserted:
                        add_full(v['key']); v['done'] = True; inserted = True
                        ok = pno % 2 == 0
                        report.append((v['key'], len(pages), pno, ok))

        def place_block(h):
            nonlocal pg
            if pg['used'] + h > TXH + 0.5:
                finalize(len(pages) - 1)
                pg = new_text_page()
            pg['used'] += h

        for k, (en, es) in enumerate(pairs, 1):
            CUR['k'] = k
            starts = [v for v in pending if not v['done'] and v['a'] == k]
            if starts and len(pages) % 2 == 1 and pg['used'] > 0:
                free = TXH - pg['used']
                if free <= TXH * 0.40:
                    finalize(len(pages) - 1); pg = new_text_page()
                    NOSPLIT['on'] = True
            pe, he = para(en, sEN); ps, hs = para(es, sES)
            gap = GAP_PAIR if pg['items'] and pg['items'][-1][0] != 'img' or pg['used'] > 0 else 0
            tot = he + GAP_IN + hs
            if tot > TXH - 20:           # слишком длинная пара: делим по предложениям
                se, ss = sentences(en), sentences(es)
                cut_e, cut_s = (len(se) + 1) // 2, (len(ss) + 1) // 2
                chunks = [(' '.join(se[:cut_e]), ' '.join(ss[:cut_s])), (' '.join(se[cut_e:]), ' '.join(ss[cut_s:]))]
            else:
                chunks = [(en, es)]
            chunks = chunks if NOSPLIT['on'] else split_to_fit(chunks, pg)
            NOSPLIT['on'] = False
            for en2, es2 in chunks:
                pe, he = para_m(en2, sEN, ci, 'en'); ps, hs = para_m(es2, sES, ci, 'es')
                tot = (GAP_PAIR if pg['used'] > 0 else 0) + he + GAP_IN + hs
                if pg['used'] + tot > TXH + 0.5:
                    finalize(len(pages) - 1); pg = new_text_page()
                    tot = he + GAP_IN + hs
                y0 = pg['used'] + (tot - he - GAP_IN - hs)
                pg['items'].append(('par', pe, he, tot - he - GAP_IN - hs)); pg['items'].append(('par', ps, hs, GAP_IN))
                pg['used'] += tot; pg['pairs'].add(k)
            # горизонтальная картинка после абзаца
            if k in plan['after']:
                key = plan['after'][k]; w, h = img_box(key, {'beaver_house': 225}.get(key, IMG_MAXH_TEXT))
                need = 22 + h
                free = TXH - pg['used'] - 22
                if pg['used'] + need > TXH + 0.5 and free >= 170:
                    w, h = img_box(key, free); need = 22 + h
                if pg['used'] + need > TXH + 0.5:
                    finalize(len(pages) - 1); pg = new_text_page(); need = h
                pg['items'].append(('img', key, w, h, need - h)); pg['used'] += need
        if plan['end']:
            key = plan['end']; w, h = img_box(key, IMG_MAXH_TEXT); need = 26 + h
            free = TXH - pg['used'] - 26
            if pg['used'] + need > TXH + 0.5 and free >= 170:
                w, h = img_box(key, free); need = 26 + h
            if pg['used'] + need > TXH + 0.5:
                finalize(len(pages) - 1); pg = new_text_page(); need = h
            pg['items'].append(('img', key, w, h, need - h)); pg['used'] += need
        finalize(len(pages) - 1, last=True)
        for v in pending:
            if not v['done']:
                add_full(v['key']); report.append((v['key'], len(pages), None, False))
        pages.append(dict(kind='words', ci=ci))
        pages.append(dict(kind='turn', ci=ci))
    return chap_start, report


def trim_x(pno):
    return 0 if pno % 2 == 1 else PW - TW    # нечётная: запас справа; чётная: слева


def draw(path):
    c = canvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle('The Adventures of Lucky Rocky: The Magic of Friendship - Bilingual Edition')
    c.setAuthor('Ricardo Demi')
    by = (PH - TH) / 2
    for i, P in enumerate(pages, 1):
        tx = trim_x(i)
        left = tx + (GUT if i % 2 == 1 else OUT)
        k = P['kind']
        if k in ('full', 'fullimg'):
            c.drawImage(IMG + P['key'] + '.jpg', 0, 0, PW, PH)
        elif k == 'title':
            cx = tx + TW / 2
            def ctr(t, f, s, y, col=EN_C):
                c.setFont(f, s); c.setFillColor(col); c.drawCentredString(cx, y, t)
            ctr('The Adventures of', 'BB', 30, by + 610)
            ctr('Lucky Rocky', 'BB', 54, by + 555)
            ctr('The Magic of Friendship', 'BB', 28, by + 510)
            ctr('Las aventuras de', 'BB', 26, by + 420, ES_C)
            ctr('Rocky el Afortunado', 'BB', 44, by + 375, ES_C)
            ctr('La magia de la amistad', 'BB', 26, by + 338, ES_C)
            ctr('Bilingual Edition · Edición bilingüe', 'B', 18, by + 250)
            ctr('English – Español', 'B', 16, by + 226, ES_C)
            ctr('Ricardo Demi', 'BB', 24, by + 150)
            ctr('Magic of Discoveries', 'B', 14, by + 80, ES_C)
        elif k == 'copyright':
            st = ParagraphStyle('c', fontName='B', fontSize=11, leading=16, textColor=EN_C, alignment=TA_LEFT)
            txt = ['<b>The Adventures of Lucky Rocky: The Magic of Friendship</b><br/>'
                   '<b>Las aventuras de Rocky el Afortunado: La magia de la amistad</b>',
                   'Bilingual English–Spanish Edition · Edición bilingüe inglés–español',
                   'Text copyright © 2026 Ricardo Demi. All rights reserved.<br/>'
                   'Texto © 2026 Ricardo Demi. Todos los derechos reservados.',
                   'No part of this book may be reproduced in any form without written permission from the publisher.<br/>'
                   'Ninguna parte de este libro puede reproducirse sin permiso escrito del editor.',
                   'ISBN: 000-0-000000-00-0',
                   'Published by Magic of Discoveries LLC · Miami, Florida<br/>magicofdiscoveries.com']
            y = by + 330
            for t in txt:
                p = Paragraph(t, st); w, h = p.wrap(TXW, 500); p.drawOn(c, left, y - h); y -= h + 12
        elif k == 'words':
            draw_words(c, P['ci'], left, by, i)
        elif k == 'turn':
            draw_turn(c, P['ci'], left, by, i)
        else:
            y = by + TH - TOP
            for it in P['items']:
                if it[0] == 'par':
                    _, p, h, before = it; y -= before; p.drawOn(c, left, y - h); y -= h
                else:
                    _, key, w, h, before = it; y -= before
                    c.drawImage(IMG + key + '.jpg', left + (TXW - w) / 2, y - h, w, h); y -= h
            num(c, i, tx)
        c.showPage()
    c.save()


def num(c, i, tx):
    c.setFont('B', 12); c.setFillColor(ES_C); c.drawCentredString(tx + TW / 2, (PH - TH) / 2 + 30, str(i))


def blanks(word):
    # показываем первую букву и каждую вторую, остальные — пропуски
    out=[]; k=0
    for ch in word.upper():
        if ch == ' ':
            out.append('  '); k = 0; continue
        out.append(ch if (k == 0 or k % 2 == 0) else '_'); k += 1
    return ' '.join(out)


def head(c, cx, y, t1, t2):
    c.setFillColor(EN_C); c.setFont('BB', 26); c.drawCentredString(cx, y, t1)
    c.setFillColor(ES_C); c.setFont('BB', 22); c.drawCentredString(cx, y - 28, t2)


def draw_words(c, ci, left, by, i):
    b = D['blocks'][ci]
    cx = left + TXW / 2
    y = by + TH - TOP - 10
    c.setFillColor(ES_C); c.setFont('B', 14)
    c.drawCentredString(cx, y - 8, f'{TITLES[ci][0]} · {TITLES[ci][1]}')
    y -= 50
    head(c, cx, y, 'Words', 'Palabras')
    y -= 50
    colw = TXW / 2; rowh = 84; ics = 68
    for n, (e, s) in enumerate(b['words']):
        col, row = n % 2, n // 2
        x = left + col * colw + 8
        yy = y - row * rowh
        c.drawImage(IMG + f'ic/{ci+1}-{n+1:02d}.jpg', x, yy - ics, ics, ics)
        c.setFillColor(EN_C); c.setFont('BB', 18); c.drawString(x + ics + 12, yy - 28, e)
        c.setFillColor(ES_C); c.setFont('B', 18); c.drawString(x + ics + 12, yy - 52, s)
    y -= 4 * rowh + 34
    head(c, cx, y, "Let's talk", 'Conversemos')
    y -= 24
    qe = ParagraphStyle('q', fontName='B', fontSize=16, leading=21, textColor=EN_C, leftIndent=22, firstLineIndent=-22)
    qs = ParagraphStyle('qs', parent=qe, fontName='BI', textColor=ES_C, firstLineIndent=0)
    for n, (e, s) in enumerate(b['qs'], 1):
        p = Paragraph(esc(f'{n}. {e}'), qe); w, h = p.wrap(TXW, 300); y -= 12; p.drawOn(c, left, y - h); y -= h + 2
        p = Paragraph(esc(s), qs); w, h = p.wrap(TXW, 300); p.drawOn(c, left, y - h); y -= h
    num(c, i, trim_x(i))


def draw_turn(c, ci, left, by, i):
    b = D['blocks'][ci]
    cx = left + TXW / 2
    y = by + TH - TOP - 30
    head(c, cx, y, 'Your turn!', '¡Tu turno!')
    y -= 68
    c.setFillColor(EN_C); c.setFont('B', 15); c.drawCentredString(cx, y, 'Fill in the missing letters.')
    c.setFillColor(ES_C); c.drawCentredString(cx, y - 20, 'Completa las letras que faltan.')
    y -= 58
    colw = TXW / 2; rowh = 132; ics = 96
    import re as _r
    for n, (e, s) in enumerate(b['words']):
        col, row = n % 2, n // 2
        x = left + col * colw + 4
        yy = y - row * rowh
        c.drawImage(IMG + f'ic/{ci+1}-{n+1:02d}.jpg', x, yy - ics, ics, ics)
        art, noun = (s.split(' ', 1) + [''])[:2]
        tx = x + ics + 12
        c.setFillColor(EN_C); c.setFont('BB', 17); c.drawString(tx, yy - 40, blanks(e))
        c.setFillColor(ES_C); c.setFont('BB', 17); c.drawString(tx, yy - 70, art.upper() + '  ' + blanks(noun))
    num(c, i, trim_x(i))


if __name__ == '__main__':
    cs, rep = layout()
    json.dump([p for p in cs], open('/home/claude/book/chapstarts.json', 'w'))
    draw(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/book/rocky.pdf')
    print('страниц:', len(pages), 'главы начинаются:', cs)
    for r in rep:
        print(r)
