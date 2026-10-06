"""Tutorial-page relabeller: yellow header box + white speech bubbles.

detect: tutkit.py detect <name>   -> prints header/bubble components, writes work/annot/<name>_tk.png
apply : tutkit.py apply <spec.json>
spec = [{"name": "sel_tea_tokei_tutorial_1_kiridashi",
         "header": ["line1", "line2"],
         "bubbles": [{"id": 0, "lines": [...], "style": {...}}],     # id = index from detect
         "extra": [relabel items]}]
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import relabel  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HEAD_ST = {"auto": False, "font": "round", "fill": "#ffffff", "outline": [["#000000", 1], ["#ffffff", 1]],
           "align": "l", "pad": 0, "overflow": 2, "size": 14}
BUB_ST = {"auto": False, "font": "round", "fill": ["#ffee00", "#ff9900"], "outline": [["#000000", 1], ["#ffffff", 1]],
          "align": "c", "pad": 0, "overflow": 2, "size": 12}


def load(name):
    return np.asarray(Image.open(os.path.join(ROOT, 'work/sprites/sprite__%s.png' % name)).convert('RGBA')).copy()


def filled(mask):
    m = mask.astype(np.uint8)
    h, w = m.shape
    fl = m.copy()
    cv2.floodFill(fl, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    return (m > 0) | (fl == 0)


def components(mask, min_area):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a >= min_area:
            out.append((lab == i, [int(x), int(y), int(x + w), int(y + h)]))
    return out


def header(arr):
    rgb = arr[..., :3].astype(int)
    yel = (rgb[..., 0] > 230) & (rgb[..., 1] > 215) & (rgb[..., 2] < 80) & (arr[..., 3] > 200)
    comps = components(yel, 3000)
    if not comps:
        return None
    m, b = max(comps, key=lambda c: c[0].sum())
    return filled(m), b


def bubbles(arr):
    rgb = arr[..., :3].astype(int)
    wh = (rgb.min(-1) > 225) & (arr[..., 3] > 200)
    res = []
    for m, b in components(wh, 400):
        if b[2] - b[0] > 380:     # page frame
            continue
        f = filled(m)
        holes = f & ~m
        if holes.sum() < 30:      # no text inside
            continue
        res.append((f, b))
    return res


def bubble_border(arr, clip, dark=90, seed=None):
    """bubble interior: the light region around seed bounded by dark outline pixels or the clip edge,
    with text (holes) filled in."""
    x0, y0, x1, y1 = clip
    rgb = arr[..., :3].astype(int)
    walls = (rgb.max(-1) < dark) | (arr[..., 3] < 100)
    lim = np.zeros(walls.shape, bool)
    lim[y0:y1, x0:x1] = True
    walls |= ~lim
    walls[y0, x0:x1] = walls[y1 - 1, x0:x1] = True
    walls[y0:y1, x0] = walls[y0:y1, x1 - 1] = True
    light = (rgb.min(-1) > 200) & ~walls
    n, lab = cv2.connectedComponents((~walls).astype(np.uint8), connectivity=4)
    if seed is None:
        cnt = np.bincount(lab[light], minlength=n)
        cnt[0] = 0
        R = lab == int(np.argmax(cnt))
    else:
        ys, xs = np.nonzero(light)
        k = np.argmin((xs - seed[0]) ** 2 + (ys - seed[1]) ** 2)
        R = lab == lab[ys[k], xs[k]]
    f = filled(R)
    f = cv2.dilate(f.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    f &= lim
    # keep the outline: only cells that are not part of the outer dark ring
    ring = f & ~(cv2.erode(f.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    f &= ~ring
    f |= R
    ys, xs = np.nonzero(f)
    return f, [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def bubble_at(arr, seed, clip=None, thr=225):
    """white region containing seed (optionally restricted to clip rect), holes filled."""
    rgb = arr[..., :3].astype(int)
    wh = (rgb.min(-1) > thr) & (arr[..., 3] > 200)
    if clip:
        lim = np.zeros_like(wh)
        x0, y0, x1, y1 = clip
        lim[y0:y1, x0:x1] = True
        wh &= lim
    n, lab = cv2.connectedComponents(wh.astype(np.uint8), connectivity=4)
    if not wh[seed[1], seed[0]]:
        ys, xs = np.nonzero(wh)
        k = np.argmin((xs - seed[0]) ** 2 + (ys - seed[1]) ** 2)
        seed = (xs[k], ys[k])
    m = lab == lab[seed[1], seed[0]]
    ys, xs = np.nonzero(m)
    return filled(m), [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def detect(name):
    arr = load(name)
    img = Image.fromarray(arr).convert('RGB')
    d = ImageDraw.Draw(img)
    hd = header(arr)
    if hd:
        d.rectangle(hd[1], outline=(0, 0, 255))
        print('header', hd[1])
    for i, (f, b) in enumerate(bubbles(arr)):
        d.rectangle(b, outline=(0, 160, 0))
        d.text((b[0] + 2, b[1] + 2), str(i), fill=(0, 160, 0))
        print('bubble', i, b)
    img.save(os.path.join(ROOT, 'work/annot/%s_tk.png' % name))


def ink_rows(arr, interior, bgtest):
    """rows (y0,y1) and x-extent of non-background pixels inside interior mask."""
    ink = interior & ~bgtest
    ys = np.nonzero(ink.any(1))[0]
    if len(ys) == 0:
        return [], None
    rows, s = [], ys[0]
    for a, b in zip(ys, ys[1:]):
        if b - a > 2:
            rows.append((s, a + 1))
            s = b
    rows.append((s, ys[-1] + 1))
    xs = np.nonzero(ink.any(0))[0]
    return rows, (xs[0], xs[-1] + 1)


def place_lines(img, lines, rows, xr, area, st, center_x=None):
    """render lines; reuse original row positions if counts match else distribute in area."""
    ax0, ay0, ax1, ay1 = area
    n = len(lines)
    if len(rows) == n and not st.get('recenter'):
        ys = rows
    else:
        if rows:
            top, bot = rows[0][0], rows[-1][1]
        else:
            top, bot = ay0, ay1
        lh = st.get('size', 12) + 3
        gap = st.get('linegap', 1)
        tot = n * lh + (n - 1) * gap
        y = (top + bot) // 2 - tot // 2
        ys = [(y + k * (lh + gap), y + k * (lh + gap) + lh) for k in range(n)]
    for t, (y0, y1) in zip(lines, ys):
        h = max(y1 - y0, 10)
        box = [ax0, y0 - 1, ax1, y0 - 1 + h + 2]
        tim, M = relabel.render_text((box[2] - box[0], box[3] - box[1]), t, st)
        img.alpha_composite(tim, (box[0] - M, box[1] - M))


def apply_one(job):
    name = job['name']
    arr = load(name)
    rgb = arr[..., :3].astype(int)
    plan = []
    if job.get('header'):
        hm, hb = header(arr)
        inside = cv2.erode(hm.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        yel = (rgb[..., 0] > 230) & (rgb[..., 1] > 215) & (rgb[..., 2] < 80)
        rows, xr = ink_rows(arr, inside, yel)
        col = np.median(arr[inside & yel], axis=0).astype(np.uint8)
        arr[inside] = col
        st = dict(HEAD_ST, **job.get('header_style', {}))
        area = [xr[0], 0, max(xr[1], hb[2] - 8), 0]
        plan.append((job['header'], rows, xr, area, st))
    bl = bubbles(load(name))
    for bj in job.get('bubbles', []):
        if 'border' in bj:
            f, b = bubble_border(load(name), bj['border'], seed=bj.get('seed'))
            if bj.get('open'):
                k = bj['open']
                f = cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_OPEN, np.ones((k, k), np.uint8)) > 0
            for x0, y0, x1, y1 in bj.get('exclude', []):
                f[y0:y1, x0:x1] = False
        elif 'seed' in bj:
            f, b = bubble_at(load(name), bj['seed'], bj.get('clip'), bj.get('thr', 225))
        else:
            f, b = bl[bj['id']]
        inside = cv2.erode(f.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        px = arr[inside]
        keys, cnt = np.unique(px.view(np.uint32), return_counts=True)
        bgc = np.array([keys[np.argmax(cnt)]], np.uint32).view(np.uint8) if 'bg' not in bj else np.array(relabel.hexc(bj['bg']), np.uint8)
        whm = np.abs(rgb - bgc[:3].astype(int)).max(-1) < 30
        core = cv2.erode(f.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        rows, xr = ink_rows(arr, core, whm)
        arr[inside] = bgc
        st = dict(BUB_ST, recenter=True, **bj.get('style', {}))
        if 'area' in bj:
            area = bj['area']
        else:
            # widest horizontal span usable: shrink bubble bbox
            cx = (xr[0] + xr[1]) // 2 if xr else (b[0] + b[2]) // 2
            hw = max((xr[1] - xr[0]) // 2 if xr else 0, int((b[2] - b[0]) * 0.36))
            area = [cx - hw, b[1], cx + hw, b[3]]
        plan.append((bj['lines'], rows, xr, area, st))
    img = Image.fromarray(arr, 'RGBA')
    for lines, rows, xr, area, st in plan:
        place_lines(img, lines, rows, xr, area, st)
    out = os.path.join(ROOT, 'assets_ko/sprite/%s.png' % name)
    img.save(out)
    if job.get('extra'):
        spec = {"src": 'assets_ko/sprite/%s.png' % name, "out": 'assets_ko/sprite/%s.png' % name,
                "items": job['extra'], "defaults": job.get('extra_defaults', {})}
        relabel.apply(spec, ROOT)
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'detect':
        for n in sys.argv[2:]:
            print('==', n)
            detect(n)
    else:
        for p in sys.argv[2:]:
            for job in json.load(open(p, encoding='utf-8')):
                print(apply_one(job))
