"""Programmatic Korean title logo: '케이온!' + '방과후 라이브!!' composed onto atr_title_2_kiridashi.

The K-ON! badge and the music staff of the original are kept; only the lettering is replaced."""
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
F_BIG = os.path.expandvars('%LOCALAPPDATA%/Microsoft/Windows/Fonts/BlackHanSans-Regular.ttf')
F_SUB = os.path.expandvars('%LOCALAPPDATA%/Microsoft/Windows/Fonts/BMJUA_ttf.ttf')
if not os.path.exists(F_SUB):
    F_SUB = 'C:/Windows/Fonts/BMJUA_ttf.ttf'
S = 4  # supersampling


def glyph(ch, font, size):
    f = ImageFont.truetype(font, size)
    bb = f.getbbox(ch)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    m = Image.new('L', (w + 8, h + 8), 0)
    ImageDraw.Draw(m).text((4 - bb[0], 4 - bb[1]), ch, font=f, fill=255)
    return m


def word(chars, font, size, rots, dys, gap, fills):
    """lay out rotated glyphs; returns list of (mask, fill) placed on one canvas (L masks, same size)."""
    gl = [glyph(c, font, size).rotate(r, expand=True, resample=Image.BICUBIC) for c, r in zip(chars, rots)]
    W = sum(g.width for g in gl) + gap * (len(gl) - 1) + 40 * S
    H = max(g.height for g in gl) + max(abs(d) for d in dys) * 2 + 40 * S
    out = []
    x = 20 * S
    for g, d, fc in zip(gl, dys, fills):
        m = Image.new('L', (W, H), 0)
        m.paste(g, (x, (H - g.height) // 2 + d))
        out.append((m, fc))
        x += g.width + gap
    return out, (W, H)


def stylise(parts, size, outline, edge, shadow=None):
    """parts: [(mask, fill)] -> RGBA with per-glyph fill, shared outline + edge line (+ drop shadow)."""
    W, H = size
    union = Image.new('L', (W, H), 0)
    for m, _ in parts:
        union = Image.fromarray(np.maximum(np.asarray(union), np.asarray(m)))
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    u = np.asarray(union)
    o1 = cv2.dilate(u, k(outline))
    o2 = cv2.dilate(o1, k(edge[1]))
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shadow:
        dx, dy, col = shadow
        sh = Image.new('RGBA', (W, H), col)
        sh.putalpha(Image.fromarray(o2))
        can.alpha_composite(sh, (dx, dy))
    for msk, col in ((o2, edge[0]), (o1, None)):
        layer = Image.new('RGBA', (W, H), col if col else outline_col[0])
        layer.putalpha(Image.fromarray(msk))
        can.alpha_composite(layer)
    for m, fc in parts:
        if not np.asarray(m).any():
            continue
        if isinstance(fc, tuple) and isinstance(fc[0], str):
            top, bot = np.array(hexc(fc[0]), float), np.array(hexc(fc[1]), float)
            ys = np.nonzero(np.asarray(m).any(1))[0]
            t = np.clip((np.arange(H) - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)[:, None, None]
            grad = (top * (1 - t) + bot * t).repeat(W, 1).astype(np.uint8)
            layer = Image.fromarray(grad, 'RGBA')
        else:
            layer = Image.new('RGBA', (W, H), hexc(fc))
        layer.putalpha(m)
        can.alpha_composite(layer)
    return can


outline_col = ['#fff4c8']


def hexc(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def crop_alpha(im):
    bb = im.getbbox()
    return im.crop(bb)


def big_logo():
    global outline_col
    outline_col = ['#fff4c8']
    parts, size = word('케이온!', F_BIG, 120 * S // 2, [7, -5, 4, -9], [10, -16, 6, -12], -3 * S,
                       ['#e2261c'] * 4)
    return crop_alpha(stylise(parts, size, 5 * S, ('#9a1a10', 1 * S), (3 * S, 3 * S, (90, 20, 10, 160))))


def sub_logo():
    global outline_col
    outline_col = ['#ffffff']
    g = ('#5ad23c', '#18a020')
    o = ('#ffb43c', '#ff6a00')
    parts, size = word('방과후 라이브!!', F_SUB, 64 * S // 2, [4, -3, 5, 0, -4, 3, -5, 6, 6],
                       [4, -4, 2, 0, -6, 2, -4, 0, 0], -2 * S, [g, g, g, g, o, o, o, o, o])
    return crop_alpha(stylise(parts, size, 4 * S, ('#6a4a2a', 1 * S), (2 * S, 2 * S, (40, 30, 20, 120))))


def letters_mask(a, box, k=5):
    """thick opaque blobs (lettering) inside box, without thin staff lines."""
    x0, y0, x1, y1 = box
    al = (a[..., 3] > 150).astype(np.uint8)
    lim = np.zeros_like(al)
    lim[y0:y1, x0:x1] = 1
    al &= lim
    op = cv2.morphologyEx(al, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    return cv2.dilate(op, np.ones((5, 5), np.uint8)) > 0


def fit(im, w, h):
    r = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


def compose(src, out):
    base = Image.open(src).convert('RGBA')
    a = np.asarray(base).copy()
    badge = base.crop((84, 5, 130, 31))           # "K-ON!" badge
    a[0:100, 0:300] = 0                            # whole big lettering area
    m = letters_mask(a, (10, 100, 290, 160))
    a[m] = 0
    img = Image.fromarray(a, 'RGBA')
    big = fit(big_logo(), 292, 88)
    img.alpha_composite(big, (4 + (292 - big.width) // 2, 5 + (88 - big.height) // 2))
    img.alpha_composite(badge, (4 + (292 - big.width) // 2 + int(big.width * 0.30), 0))
    sub = fit(sub_logo(), 262, 50)
    img.alpha_composite(sub, (28 + (262 - sub.width) // 2, 104 + (50 - sub.height) // 2))
    img.save(out)
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets_ko/sprite/atr_title_2_kiridashi.png')
    out = sys.argv[2] if len(sys.argv) > 2 else src
    big_logo().save(os.path.join(ROOT, 'work/logo/ko_big.png'))
    sub_logo().save(os.path.join(ROOT, 'work/logo/ko_sub.png'))
    print(compose(src, out))
