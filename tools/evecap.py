"""Album event thumbnails (sel_album_eve_cap_XX): replace the speech-bubble text with the
Korean line already used in the teatime event, and paste Korean tutorial pages where the
thumbnail shows a tutorial screen.

usage: evecap.py [index ...]
"""
import glob
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONT = 'C:/Windows/Fonts/NanumGothicExtraBold.ttf'

# thumbnail -> (event file, record) shown in its bubble
BUBBLE = {
    1: ('0001', 13), 2: ('0002', 1), 4: ('0004', 5), 8: ('0055', 10), 9: ('0056', 0), 10: ('0057', 23),
    12: ('0202', 7), 13: ('0303', 3), 14: ('0304', 1), 15: ('0402', 4), 16: ('0404', 3), 17: ('0405', 7),
    18: ('0502', 13), 19: ('0505', 4), 20: ('0601', 7), 21: ('0602', 3), 22: ('0604', 8), 23: ('0702', 6),
    24: ('0802', 4), 25: ('0901', 3), 26: ('0902', 2), 27: ('0903', 5), 28: ('0904', 1), 29: ('1001', 2),
    30: ('1003', 2), 31: ('1005', 5), 32: ('1305', 6), 33: ('9901', 9), 34: ('9902', 2), 35: ('9905', 1),
    36: ('9906', 7), 37: ('9907', 6), 38: ('9913', 7), 39: ('9915', 7), 40: ('9917', 3), 41: ('9918', 2),
    42: ('9920', 0), 43: ('9921', 5), 44: ('9922', 3), 45: ('9923', 0), 46: ('9925', 2), 47: ('9926', 5),
    48: ('9927', 8), 49: ('9928', 3), 50: ('9929', 8),
}
# thumbnail -> Korean tutorial page shown in it
TUTORIAL = {5: 'sel_tea_album_tutorial_2_kiridashi', 6: 'sel_tea_tokei_tutorial_1_kiridashi',
            7: 'sel_tea_utaou_tutorial_2_kiridashi'}
# red system message box (white text)
YCUT = {9: 48, 10: 46}
CLIP = {9: (0, 6, 112, 50)}
CUR = None
REDBOX = {3: ['「통신!」에서 사용할 플레이어 네임을', '입력해 주세요']}


def tts_lines():
    d = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'text', 'tts_ko_*.json'))):
        d.update(json.load(open(p, encoding='utf-8')))
    return d


def filled(m):
    m = m.astype(np.uint8)
    h, w = m.shape
    fl = m.copy()
    cv2.floodFill(fl, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    return (m > 0) | (fl == 0)


def text_img(lines, size, color, maxw):
    """render lines (tight) at 4x then downsample; returns RGBA and per-line height."""
    S = 4
    f = ImageFont.truetype(FONT, size * S)
    widths = [f.getbbox(l)[2] for l in lines]
    asc, desc = f.getmetrics()
    lh = int(size * 1.18) * S
    W, H = max(widths) + 4 * S, lh * len(lines) + 2 * S
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for i, l in enumerate(lines):
        d.text((S, i * lh), l, font=f, fill=255)
    w, h = W // S, H // S
    sx = min(1.0, maxw / w)
    m = m.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    im = Image.new('RGBA', m.size, color)
    im.putalpha(m)
    return im


def do_bubble(arr, lines):
    rgb = arr[..., :3].astype(int)
    vis = arr[..., 3] > 0
    pinkw = (rgb[..., 0] > 235) & (rgb[..., 1] > 218) & (rgb[..., 2] > 212) & (rgb[..., 0] - rgb[..., 2] >= 5) & vis
    pinkw[YCUT.get(CUR, 64):] = False
    if CUR in CLIP:
        cx0, cy0, cx1, cy1 = CLIP[CUR]
        keep = np.zeros_like(pinkw)
        keep[cy0:cy1, cx0:cx1] = True
        pinkw &= keep
    pinkw = cv2.morphologyEx(pinkw.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    pinkw = cv2.morphologyEx(pinkw, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pinkw, 4)
    if n < 2:
        raise RuntimeError('no bubble')
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    inside = filled(lab == k)
    inside = cv2.erode(inside.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    core = cv2.erode(inside.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    ink = core & (rgb.max(-1) < 170)
    ys, xs = np.nonzero(ink)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    # fill colour = median of light pixels inside
    light = inside & (rgb.min(-1) > 215)
    fill = np.median(arr[light], axis=0).astype(np.uint8)
    far = np.abs(rgb - fill[:3].astype(int)).max(-1) > 14
    pinkb = (rgb[..., 0] - rgb[..., 1] > 30) & (rgb[..., 1] > 120)
    er = cv2.dilate((inside & far & ~pinkb).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    er &= inside & ~pinkb
    # keep the pink "next" arrow
    arrow = inside & (rgb[..., 0] > 200) & (rgb[..., 1] < 130)
    er &= ~cv2.dilate(arrow.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    arr[er] = fill
    col = tuple(int(v) for v in np.median(arr[ink & ~er], axis=0)) if (ink & ~er).any() else (70, 60, 60, 255)
    ibx = np.nonzero(inside.any(0))[0]
    x0 = max(x0, ibx.min() + 7)
    right = ibx.max() - 3
    nrows = len(lines)
    size = 7 if nrows >= 3 else 8
    t = text_img(lines, size, (80, 70, 72, 255), right - x0 - 6)
    cy = (y0 + y1) // 2
    img = Image.fromarray(arr, 'RGBA')
    img.alpha_composite(t, (int(x0), int(cy - t.height // 2)))
    return np.asarray(img).copy()


def do_redbox(arr, lines):
    rgb = arr[..., :3].astype(int)
    red = (rgb[..., 0] > 180) & (rgb[..., 1] < 80) & (rgb[..., 2] < 110)
    n, lab, st, _ = cv2.connectedComponentsWithStats(red.astype(np.uint8), 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    box = filled(lab == k)
    box = cv2.erode(box.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    txt = box & (rgb.min(-1) > 150)
    ys, xs = np.nonzero(txt)
    x0, y0, y1 = xs.min(), ys.min(), ys.max() + 1
    fill = np.median(arr[box & red], axis=0).astype(np.uint8)
    arr[cv2.dilate(txt.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & box] = fill
    bx = np.nonzero(box.any(0))[0]
    t = text_img(lines, 7, (255, 255, 255, 255), bx.max() - x0 - 4)
    img = Image.fromarray(arr, 'RGBA')
    img.alpha_composite(t, (int(x0), int((y0 + y1) // 2 - t.height // 2)))
    return np.asarray(img).copy()


def do_tutorial(arr, page):
    """paste the Korean tutorial page over the red frame shown in the thumbnail."""
    rgb = arr[..., :3].astype(int)
    red = (rgb[..., 0] > 170) & (rgb[..., 1] < 80) & (rgb[..., 2] < 120) & (arr[..., 3] > 0)
    n, lab, st, _ = cv2.connectedComponentsWithStats(red.astype(np.uint8), 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[k, :4]
    src = Image.open(os.path.join(ROOT, 'assets_ko', 'sprite', page + '.png')).convert('RGBA')
    ref = np.asarray(Image.open(os.path.join(ROOT, 'work', 'sprites', 'sprite__' + page + '.png')).convert('RGBA')).astype(int)
    rr = (ref[..., 0] > 170) & (ref[..., 1] < 80) & (ref[..., 2] < 120)
    ys, xs = np.nonzero(rr)
    # red area of the texture page (inside its white rim) maps onto the red area of the thumbnail
    rx0, ry0, rx1, ry1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    sx, sy = w / (rx1 - rx0), h / (ry1 - ry0)
    pg = src.crop((0, 0, 408, 208))
    pg = pg.resize((max(1, int(round(408 * sx))), max(1, int(round(208 * sy)))), Image.LANCZOS)
    ox, oy = int(round(x - rx0 * sx)), int(round(y - ry0 * sy))
    img = Image.fromarray(arr, 'RGBA')
    vis = img.split()[3]
    img.alpha_composite(pg, (ox, oy))
    img.putalpha(vis)
    return np.asarray(img).copy()


def run(i, tts):
    n = 'sel_album_eve_cap_%02d' % i
    arr = np.asarray(Image.open(os.path.join(ROOT, 'work', 'sprites', 'sprite__%s.png' % n)).convert('RGBA')).copy()
    global CUR
    CUR = i
    if i in BUBBLE:
        f, r = BUBBLE[i]
        lines = tts['TTS_Nm_%s.tts' % f][r]
        arr = do_bubble(arr, lines)
    elif i in REDBOX:
        arr = do_redbox(arr, REDBOX[i])
    elif i in TUTORIAL:
        arr = do_tutorial(arr, TUTORIAL[i])
    else:
        return None
    out = os.path.join(ROOT, 'assets_ko', 'sprite', n + '.png')
    Image.fromarray(arr, 'RGBA').save(out)
    return out


if __name__ == '__main__':
    tts = tts_lines()
    idx = [int(a) for a in sys.argv[1:]] or range(51)
    for i in idx:
        try:
            print(i, run(i, tts))
        except Exception as e:
            print(i, 'ERROR', e)
