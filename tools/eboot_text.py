"""EBOOT UI string translations: merge auto (from KKS memory) + generated + manual, and encode.

Translation value syntax:
  plain text                 -> written as is (ASCII mapped to the glyph table's full-width forms)
  "@W|l1\\nl2"  / "@Wc|..."   -> each line padded with U+3000 to W glyphs (c = centred); last line
                                also padded. Lines longer than W just wrap naturally.
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SPACE_GLYPH = 316   # blank atlas cell whose UTF-8 slot is patched to a 1-byte ASCII space
# glyph index -> 1-byte ASCII UTF-8 slot (latin letters + a few symbols); digits stay full-width
# because the game formats numbers with full-width digits at run time.
ASCII_SLOTS = {SPACE_GLYPH: ' ', 68: "'", 71: '(', 72: ')', 73: '/', 75: '!', 76: '?', 84: ',', 85: '-',
               86: '.', 87: ':'}
ASCII_SLOTS.update({11 + k: chr(ord('A') + k) for k in range(26)})
ASCII_SLOTS.update({37 + k: chr(ord('a') + k) for k in range(26)})
NAMES = {'唯': '유이', '澪': '미오', '律': '리츠', '紬': '츠무기', '梓': '아즈사'}
DIRS = {'前': '앞', '右': '오른쪽', '左': '왼쪽'}
DIST = {'近': '근', '遠': '원'}


def generated(src):
    out = {}
    for o in src:
        jp, off = o['jp'], o['off']
        m = re.fullmatch(r'([０-９]{2})個', jp)
        if m:
            out[off] = str(int(''.join(chr(ord(c) - 0xfee0) for c in m.group(1)))) + '개'
            continue
        m = re.fullmatch(r'(唯|澪|律|紬|梓)カメラ　(前|右|左)　(近|遠)', jp)
        if m:
            out[off] = f'{NAMES[m.group(1)]} 카메라 {DIRS[m.group(2)]} {DIST[m.group(3)]}'
            continue
        m = re.fullmatch(r'バンドカメラ([１-３])', jp)
        if m:
            out[off] = '밴드 카메라' + chr(ord(m.group(1)) - 0xfee0)
            continue
        m = re.fullmatch(r'(唯|澪|律|紬|梓)のモーション選択', jp)
        if m:
            out[off] = f'{NAMES[m.group(1)]} 모션 선택'
            continue
        m = re.fullmatch(r'(唯|澪|律|紬|梓)のカメラ選択', jp)
        if m:
            out[off] = f'{NAMES[m.group(1)]} 카메라'
            continue
        m = re.fullmatch(r'(唯|澪|律|紬|梓)ＭＣの選択', jp)
        if m:
            out[off] = f'{NAMES[m.group(1)]} MC 선택'
            continue
        m = re.fullmatch(r'モーション（(唯|澪|律|紬|梓)）', jp)
        if m:
            out[off] = f'모션({NAMES[m.group(1)]})'
            continue
        m = re.fullmatch(r'ＭＣ（(唯|澪|律|紬|梓)）', jp)
        if m:
            out[off] = f'MC({NAMES[m.group(1)]})'
            continue
    return out


def load_all():
    src = json.load(open(os.path.join(ROOT, 'text', 'eboot_ui_source.json'), encoding='utf-8'))
    tr = {}
    tr.update(json.load(open(os.path.join(ROOT, 'text', 'eboot_auto.json'), encoding='utf-8')))
    tr.update(generated(src))
    tr.update(json.load(open(os.path.join(ROOT, 'text', 'eboot_ko_manual.json'), encoding='utf-8')))
    return src, tr


def layout(text):
    """Expand @W| syntax into a single line string padded with ideographic spaces."""
    m = re.match(r'@(\d+)(c?)\|', text)
    if not m:
        return text
    w, centre = int(m.group(1)), bool(m.group(2))
    body = text[m.end():]
    out = ''
    for ln in body.split('\n'):
        # long lines wrap on their own: pad only the remainder of the last visual row
        rem = len(ln) % w
        pad = (w - rem) % w if (ln and rem) else (0 if ln else w)
        if centre and len(ln) < w:
            left = pad // 2
            out += ' ' * left + ln + ' ' * (pad - left)
        else:
            out += ln + ' ' * pad
    return out


def encode(text, charmap, eboot):
    """Korean text -> UTF-8 bytes made only of glyph-table entries."""
    s = layout(text)
    out = b''
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 1 < len(s) and s[i + 1] in 'sd':   # printf specifier, keep ASCII
            out += s[i:i + 2].encode()
            i += 2
            continue
        c = s[i]
        if c in ' 　':
            idx = SPACE_GLYPH
        else:
            idx = charmap.get(c)
            if idx is None:
                raise KeyError(f'char {c!r} has no glyph ({text!r})')
        u = eboot.glyph_utf8(idx)
        if not u:
            raise KeyError(f'glyph {idx} ({c!r}) has no UTF-8 slot')
        out += u.encode('utf-8')
        i += 1
    return out
