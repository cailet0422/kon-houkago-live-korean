"""Hand-drawn hollow name sprites for cp_eff_sp_00_<chara>_kiridashi (3 wobble frames + vertical column)."""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import relabel  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONT = 'C:/Windows/Fonts/BMJUA_ttf.ttf'
GAP = 0.12
NAMES = {'yu': '유이', 'mi': '미오', 'ri': '리츠', 'mu': '츠무기', 'az': '아즈사'}
SS = 4


def glyph_mask(text, w, h, vertical=False):
    """text mask (uint8, SS-scaled) fitting w x h."""
    W, H = w * SS, h * SS
    if vertical:
        n = len(text)
        size = int(min(W * 1.0, H / n * 1.0))
        f = ImageFont.truetype(FONT, size)
        m = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(m)
        step = H / n
        for i, ch in enumerate(text):
            d.text((W / 2, step * (i + 0.5)), ch, font=f, fill=255, anchor='mm')
        return np.asarray(m)
    size = int(H * 1.2)
    while True:
        f = ImageFont.truetype(FONT, size)
        adv = [f.getbbox(ch)[2] - f.getbbox(ch)[0] for ch in text]
        tw = sum(adv) + GAP * size * (len(text) - 1)
        if tw <= W * 0.97 or size < 8:
            break
        size -= 2
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    x = (W - tw) / 2
    for ch, a in zip(text, adv):
        d.text((x + a / 2, H / 2), ch, font=f, fill=255, anchor='mm')
        x += a + GAP * size
    return np.asarray(m)


def wobble(m, seed, amp):
    rng = np.random.default_rng(seed)
    h, w = m.shape
    dx = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 12 * SS / 4) * amp * 40
    dy = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 12 * SS / 4) * amp * 40
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(m, xx + dx, yy + dy, cv2.INTER_LINEAR)


def hollow(m, ring, ext, seed, fat=0.0):
    """white ring outline + grey extrusion, interior transparent with a faint dark tint."""
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    body = (m > 127).astype(np.uint8)
    if fat:
        body = cv2.dilate(body, k(int(fat * SS)))
        body = cv2.morphologyEx(body, cv2.MORPH_CLOSE, k(int(fat * SS)))
    outer = cv2.dilate(body, k(int(ring * SS * 0.5)))
    inner = cv2.erode(body, k(int(ring * SS * 0.5)))
    rim = (outer > 0) & (inner == 0)
    h, w = m.shape
    canvas = np.zeros((h, w, 4), np.float32)
    # extrusion: shifted silhouette rim in grey, drawn first
    sh = np.roll(np.roll(outer, ext * SS, 0), ext * SS, 1)
    shr = (sh > 0) & ~(outer > 0)
    canvas[shr] = (150, 150, 160, 255)
    # dark contour line just outside the rim and inside
    cont = cv2.dilate(outer, k(SS)) > 0
    canvas[cont & ~(outer > 0)] = (40, 40, 48, 255)
    canvas[inner > 0] = (30, 30, 40, 90)
    canvas[rim] = (255, 255, 255, 255)
    # sketchy hatch inside the rim (thin dark strokes)
    rng = np.random.default_rng(seed)
    hat = np.zeros((h, w), np.uint8)
    for _ in range(int(h * w / (SS * SS) / 120)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        cv2.line(hat, (int(x), int(y)), (int(x + 6 * SS), int(y - 3 * SS)), 1, max(1, SS // 2))
    canvas[(hat > 0) & rim] = (205, 205, 215, 255)
    img = Image.fromarray(canvas.astype(np.uint8), 'RGBA')
    return img.resize((w // SS, h // SS), Image.LANCZOS)


def build(chara):
    import sprite_rects
    n = 'cp_eff_sp_00_%s_kiridashi' % chara
    src = Image.open(os.path.join(ROOT, 'work/sprites/sprite__%s.png' % n)).convert('RGBA')
    # same layout for every character (the table entry for Azusa's 3rd column is bogus: 2,2,252,124)
    rects = [(4, 4, 208, 76, 0), (4, 84, 208, 76, 0), (4, 164, 208, 76, 0),
             (214, 4, 40, 76, 0), (214, 84, 40, 76, 0), (214, 164, 40, 76, 0)]
    out = Image.new('RGBA', src.size, (0, 0, 0, 0))
    big = sorted([r for r in rects if r[2] > 80], key=lambda r: r[1])
    small = sorted([r for r in rects if r[2] <= 80], key=lambda r: r[1])
    text = NAMES[chara]
    for i, (x, y, w, h, _) in enumerate(big):
        m = glyph_mask(text, w - 22, h - 22)
        m = np.pad(m, 4 * SS)
        m = wobble(m, 100 + i, 1.6)
        t = hollow(m, 2.4, 2, i, fat=1.2).resize((w - 14, h - 14), Image.LANCZOS)
        out.alpha_composite(t, (x + 7, y + 7))
    for i, (x, y, w, h, _) in enumerate(small):
        m = glyph_mask(text, w - 12, h - 12, vertical=True)
        m = np.pad(m, 3 * SS)
        m = wobble(m, 200 + i, 0.8)
        t = hollow(m, 1.3, 1, 10 + i, fat=0.4).resize((w - 6, h - 6), Image.LANCZOS)
        out.alpha_composite(t, (x + 3, y + 3))
    p = os.path.join(ROOT, 'assets_ko/sprite/%s.png' % n)
    out.save(p)
    return p


if __name__ == '__main__':
    for c in (sys.argv[1:] or NAMES):
        print(build(c))
