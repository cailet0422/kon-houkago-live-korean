"""Glyph rendering + SYS_RunTime atlas builder."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from uvr import UVR

KO_FONT = 'C:/Windows/Fonts/NanumSquareRoundEB.ttf'
CELL = 16


PAIRS = {'‼': '!!', '⁉': '!?', '⁈': '?!'}
# punctuation that should hug the previous / next glyph instead of sitting mid-cell
LEFT_PUNCT = set('.,!?~…:;」』)）‼⁉、。')
RIGHT_PUNCT = set('「『(（')


def render_glyph(ch, font_path=KO_FONT, size=15, cell=CELL, ss=4, yoff=0.0):
    """Render one glyph centred in a cell, supersampled -> alpha array (cell x cell uint8).

    Two-character ligatures (e.g. '‼') are drawn condensed into one cell."""
    if ch in PAIRS or (len(ch) == 2):
        pair = PAIRS.get(ch, ch)
        a = render_glyph(pair[0], font_path, size, cell, ss, yoff)
        b = render_glyph(pair[1], font_path, size, cell, ss, yoff)
        out = np.zeros_like(a)
        ca = np.nonzero(a.max(0) > 20)[0]
        cb = np.nonzero(b.max(0) > 20)[0]
        ga = a[:, ca.min():ca.max() + 1] if len(ca) else a[:, :0]
        gb = b[:, cb.min():cb.max() + 1] if len(cb) else b[:, :0]
        x = 1
        out[:, x:x + ga.shape[1]] = ga
        x += ga.shape[1] + 1
        out[:, x:x + gb.shape[1]] = np.maximum(out[:, x:x + gb.shape[1]], gb[:, :cell - x])
        return out
    f = ImageFont.truetype(font_path, size * ss)
    big = cell * ss
    im = Image.new('L', (big, big), 0)
    d = ImageDraw.Draw(im)
    # centre on the em box of a reference Hangul syllable so all glyphs share a baseline
    ref = d.textbbox((0, 0), '가', font=f)
    bb = d.textbbox((0, 0), ch, font=f)
    w = bb[2] - bb[0]
    x = (big - w) / 2 - bb[0]
    if ch in LEFT_PUNCT:
        x = ss * 1 - bb[0]
    elif ch in RIGHT_PUNCT:
        x = big - w - ss * 1 - bb[0]
    y = (big - (ref[3] - ref[1])) / 2 - ref[1] + yoff * ss
    d.text((x, y), ch, font=f, fill=255)
    small = im.resize((cell, cell), Image.LANCZOS)
    a = np.asarray(small).astype(np.float32)
    # mild contrast boost so strokes stay solid at 16px
    a = np.clip((a - 20) * 1.25, 0, 255)
    a = _hint_double_tick(ch, a)
    return a.astype(np.uint8)


def _hint_double_tick(ch, a):
    """ㅑ/ㅒ/ㅕ/ㅖ: the two short ticks are only one pixel apart at 16px and blur into one
    (쨩 reads as 짱). Clear the row between the two ticks and make the ticks solid."""
    o = ord(ch) - 0xAC00
    if not (0 <= o < 11172):
        return a
    v = (o // 28) % 21
    if v not in (2, 6):   # ㅑ, ㅕ (ㅒ/ㅖ have two stems; left as rendered)
        return a
    right = v in (2, 3)
    h, w = a.shape
    top = a[: h * 2 // 3] if (o % 28) else a
    cols = top.sum(0)
    half = range(w // 2, w)
    stem = max(half, key=lambda c: cols[c])
    if v in (3, 7):  # ㅒ/ㅖ: two stems; ticks attach to the outer (right) / inner (left) one
        pass
    tc = [c for c in (range(stem + 1, min(w, stem + 3)) if right else range(max(0, stem - 2), stem))]
    if not tc:
        return a
    prof = a[:, tc].max(1)
    rows = [r for r in range(1, h - 1) if prof[r] > 120]
    # find two tick runs
    runs = []
    for r in rows:
        if runs and r == runs[-1][-1] + 1:
            runs[-1].append(r)
        else:
            runs.append([r])
    if len(runs) == 1 and len(runs[0]) >= 3:
        rr = runs[0]
        mid = rr[len(rr) // 2]
        runs = [[r for r in rr if r < mid], [r for r in rr if r > mid]]
        gap = [mid]
    elif len(runs) >= 2:
        gap = list(range(runs[0][-1] + 1, runs[1][0]))
    else:
        return a
    a = a.copy()
    for r in gap:
        a[r, tc] = 0
    for run in runs[:2]:
        if run:
            r = max(run, key=lambda r: prof[r])
            a[r, tc] = np.maximum(a[r, tc], 255)
    return a


def white_alpha_palette():
    pal = np.zeros((256, 4), np.uint8)
    pal[:, 0:3] = 255
    pal[:, 3] = np.arange(256)
    pal[0] = (0, 0, 0, 0)
    return pal


def build_sys_atlas(template_uvr_bytes, layout, keep_cells, font_path=KO_FONT, size=15):
    """layout: {index: char} for cells to (re)draw; keep_cells: indices copied from the original.

    Returns new UVR bytes. Cells neither kept nor drawn are cleared.
    """
    u = UVR(template_uvr_bytes)
    orig_rgba = np.asarray(u.to_image())
    cols = u.w // CELL
    alpha = np.zeros((u.h, u.w), np.uint8)
    for i in keep_cells:
        r, c = divmod(i, cols)
        alpha[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = orig_rgba[r * CELL:(r + 1) * CELL,
                                                                            c * CELL:(c + 1) * CELL, 3]
    for i, ch in layout.items():
        r, c = divmod(i, cols)
        alpha[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = render_glyph(ch, font_path, size)
    return u.rebuild(alpha, white_alpha_palette())


def preview(uvr_bytes, out_png, scale=2):
    u = UVR(uvr_bytes)
    im = u.to_image()
    bg = Image.new('RGBA', im.size, (40, 40, 90, 255))
    bg.alpha_composite(im)
    bg.resize((im.width * scale, im.height * scale), Image.NEAREST).save(out_png)
