"""Programmatic re-labelling of text sprites (Japanese -> Korean).

regions:  relabel.py regions <in.png> <out_annot.png> [dx=5] [dy=2]
          -> prints numbered text-blob boxes and writes an annotated preview.
apply:    relabel.py apply <spec.json>
spec = {"src": "work/sprites/x.png", "out": "assets_ko/sprite/x.png",
        "items": [{"box": [x0,y0,x1,y1], "text": "연주!", ...style overrides...}],
        "defaults": {...style...}}
style keys: font, fill (hex or [top,bottom] gradient), outline [[hex,width],...] (inner->outer),
            shadow [dx,dy,hex], align (c|l|r), valign (c|t|b), pad, erase ("alpha"|"hex colour"|"none"),
            size (px, else auto-fit), squeeze (allow horizontal squash, default True), auto (sample style)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = {
    'round': 'C:/Windows/Fonts/NanumSquareRoundEB.ttf',
    'roundb': 'C:/Windows/Fonts/NanumSquareRoundB.ttf',
    'maple': os.path.expandvars('%LOCALAPPDATA%/Microsoft/Windows/Fonts/Maplestory Bold.ttf'),
    'hanna': os.path.expandvars('%LOCALAPPDATA%/Microsoft/Windows/Fonts/BMHANNA_11yrs_ttf.ttf'),
    'dohyeon': os.path.expandvars('%LOCALAPPDATA%/Microsoft/Windows/Fonts/BMDOHYEON_ttf.ttf'),
    'gothic': 'C:/Windows/Fonts/NanumGothicExtraBold.ttf',
    'malgun': 'C:/Windows/Fonts/malgunbd.ttf',
    'pen': 'C:/Windows/Fonts/NanumPen.ttf',
    'butpen': 'C:/Windows/Fonts/HakgyoansimButpenB.ttf',
}
SS = 4  # supersampling


def hexc(c, a=255):
    if isinstance(c, (list, tuple)):
        return tuple(c) + ((a,) if len(c) == 3 else ())
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def find_regions(img, dx=5, dy=2, amin=40):
    import cv2
    a = (np.asarray(img.convert('RGBA'))[..., 3] > amin).astype(np.uint8)
    k = cv2.dilate(a, np.ones((2 * dy + 1, 2 * dx + 1), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(k, 8)
    boxes = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        # shrink back to the real ink extent
        sub = a[y:y + h, x:x + w] & (lab[y:y + h, x:x + w] == i)
        ys, xs = np.nonzero(sub)
        if len(ys) == 0:
            continue
        boxes.append([int(x + xs.min()), int(y + ys.min()), int(x + xs.max() + 1), int(y + ys.max() + 1)])
    boxes.sort(key=lambda b: (b[1] // 8, b[0]))
    return boxes


def annotate(img, boxes, out):
    im = img.convert('RGBA')
    bg = Image.new('RGBA', im.size, (60, 60, 100, 255))
    bg.alpha_composite(im)
    scale = 2 if max(im.size) <= 512 else 1
    bg = bg.resize((im.width * scale, im.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(bg)
    f = ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf', 12)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        d.rectangle([x0 * scale, y0 * scale, x1 * scale - 1, y1 * scale - 1], outline=(255, 0, 0, 255))
        d.text((x0 * scale + 1, y0 * scale - 12 if y0 > 6 else y1 * scale), str(i), font=f, fill=(255, 255, 0, 255))
    bg.save(out)


def sample_style(img, box):
    """Guess fill (maybe vertical gradient) and outline layers by distance-from-edge colour bands."""
    import cv2
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert('RGBA'))[y0:y1, x0:x1].astype(np.int32)
    opaque = (a[..., 3] > 160).astype(np.uint8)
    if opaque.sum() < 12:
        return {}
    dist = cv2.distanceTransform(np.pad(opaque, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
    maxd = min(float(dist.max()), 12.0)

    def dom(mask):
        p = a[mask][:, :3]
        if len(p) < 3:
            return None
        q = (p // 20) * 20 + 10
        vals, cnt = np.unique(q, axis=0, return_counts=True)
        return vals[cnt.argmax()]

    bands = []
    d = 0.5
    while d < maxd:
        m = (dist > d) & (dist <= d + 1.0)
        c = dom(m)
        if c is not None:
            bands.append(c)
        d += 1.0
    if not bands:
        return {}
    core = dist > max(1.0, maxd * 0.6)
    fill_c = dom(core) if core.sum() > 3 else bands[-1]
    # outline layers: leading bands that differ from the fill colour
    layers = []
    for c in bands:
        if np.abs(c - fill_c).max() < 40:
            break
        if layers and np.abs(c - layers[-1][0]).max() < 40:
            layers[-1][1] += 1
        else:
            layers.append([c, 1])
    st = {}
    # vertical gradient of the fill
    ys = np.nonzero(core)[0]
    if len(ys) > 10:
        top = dom(core & (np.arange(core.shape[0])[:, None] < np.percentile(ys, 30)))
        bot = dom(core & (np.arange(core.shape[0])[:, None] > np.percentile(ys, 70)))
        if top is not None and bot is not None and np.abs(top - bot).max() > 45:
            st['fill'] = ['#%02x%02x%02x' % tuple(top), '#%02x%02x%02x' % tuple(bot)]
    st.setdefault('fill', '#%02x%02x%02x' % tuple(fill_c))
    if layers:
        # renderer expects inner -> outer
        st['outline'] = [['#%02x%02x%02x' % tuple(c), max(1, int(w))] for c, w in reversed(layers)]
    return st


def sample_style_simple(img, box):
    """Guess fill / outline colours of the text inside box."""
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert('RGBA'))[y0:y1, x0:x1].astype(np.int32)
    opaque = a[..., 3] > 200
    if opaque.sum() < 10:
        return {}
    px = a[opaque][:, :3]
    lum = px @ np.array([299, 587, 114]) // 1000
    # inner (far from transparency) vs rim pixels
    m = Image.fromarray((opaque * 255).astype(np.uint8))
    core = np.asarray(m.filter(ImageFilter.MinFilter(3))) > 0
    rim = opaque & ~core
    def dom(mask):
        p = a[mask][:, :3]
        if len(p) == 0:
            return None
        q = (p // 24) * 24 + 12
        vals, cnt = np.unique(q, axis=0, return_counts=True)
        return '#%02x%02x%02x' % tuple(vals[cnt.argmax()])
    rim_c = dom(rim)
    core_c = dom(core)
    # outline width: erode until core disappears
    w = 1
    cur = m
    for k in range(1, 6):
        cur = cur.filter(ImageFilter.MinFilter(3))
        if (np.asarray(cur) > 0).sum() < opaque.sum() * 0.25:
            w = k
            break
    st = {'fill': core_c or rim_c}
    if rim_c and core_c and rim_c != core_c:
        st['outline'] = [[rim_c, max(1, min(3, w // 2 + 1))]]
    return st


def fit_font(path, text, bw, bh, size=None, squeeze=True):
    lo, hi = 4, 200
    if size:
        hi = size
    best = None
    for s in range(hi, lo - 1, -1):
        f = ImageFont.truetype(path, s * SS)
        bb = f.getbbox(text)
        tw, th = (bb[2] - bb[0]) / SS, (bb[3] - bb[1]) / SS
        if th <= bh:
            best = (f, tw, th)
            break
    f, tw, th = best
    sx = 1.0
    if tw > bw:
        if squeeze and bw / tw >= 0.72:
            sx = bw / tw
        else:
            # shrink font until it fits with at most 0.8 squeeze
            for s in range(int(f.size / SS), lo - 1, -1):
                f = ImageFont.truetype(path, s * SS)
                bb = f.getbbox(text)
                tw = (bb[2] - bb[0]) / SS
                if tw * 0.8 <= bw:
                    sx = min(1.0, bw / tw)
                    break
    return f, sx


def render_text(size_wh, text, st):
    """Render styled text into an RGBA image of exactly size_wh (box size)."""
    bw, bh = size_wh
    font_path = FONTS.get(st.get('font', 'round'), st.get('font'))
    pad = st.get('pad', 0)
    outl = st.get('outline', [])
    ow = sum(w for _, w in outl)
    shadow = st.get('shadow')
    sh = max(abs(shadow[0]), abs(shadow[1])) if shadow else 0
    ovf = st.get('overflow', 1)          # outline may spill this many px outside the box
    inner_w = max(1, bw - 2 * (pad + max(0, ow - ovf)) - sh)
    inner_h = max(1, bh - 2 * (pad + max(0, ow - ovf)) - sh)
    f, sx = fit_font(font_path, text, inner_w, inner_h, st.get('size'), st.get('squeeze', True))
    trk = st.get('tracking', 0) * SS
    if trk:
        # re-fit with the extra spacing taken into account
        extra = trk * (len(text) - 1) / SS
        f, sx = fit_font(font_path, text, max(1, inner_w - extra), inner_h, st.get('size'), st.get('squeeze', True))
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0] + int(trk * (len(text) - 1)), bb[3] - bb[1]
    W, H = tw + 2 * (ow + 2) * SS, th + 2 * (ow + 2) * SS
    mask = Image.new('L', (W, H), 0)
    if trk:
        xx = (ow + 2) * SS - bb[0]
        dm = ImageDraw.Draw(mask)
        for ch in text:
            dm.text((xx, (ow + 2) * SS - bb[1]), ch, font=f, fill=255)
            xx += f.getlength(ch) + trk
    else:
        ImageDraw.Draw(mask).text(((ow + 2) * SS - bb[0], (ow + 2) * SS - bb[1]), text, font=f, fill=255)
    layers = []
    cur = mask
    for col, w in outl:
        cur = cur.filter(ImageFilter.MaxFilter(2 * w * SS + 1))
        layers.append((cur, col))
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shadow:
        base = layers[-1][0] if layers else mask
        sh_img = Image.new('RGBA', (W, H), hexc(shadow[2]))
        sh_img.putalpha(base)
        canvas.alpha_composite(sh_img, (shadow[0] * SS, shadow[1] * SS))
    for lm, col in reversed(layers):
        c = Image.new('RGBA', (W, H), hexc(col))
        c.putalpha(lm)
        canvas.alpha_composite(c)
    fill = st.get('fill', '#ffffff')
    if st.get('charfills'):
        # per-character colours (logo style): colour each glyph's own mask
        cf = st['charfills']
        x = (ow + 2) * SS - bb[0]
        fc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for k, ch in enumerate(text):
            cm = Image.new('L', (W, H), 0)
            ImageDraw.Draw(cm).text((x, (ow + 2) * SS - bb[1]), ch, font=f, fill=255)
            layer = Image.new('RGBA', (W, H), hexc(cf[k % len(cf)]))
            layer.putalpha(cm)
            fc.alpha_composite(layer)
            x += f.getlength(ch)
        canvas.alpha_composite(fc)
        fill = None
    if fill is None:
        pass
    elif isinstance(fill, list) and len(fill) == 2 and isinstance(fill[0], str):
        top, bot = np.array(hexc(fill[0]), np.float32), np.array(hexc(fill[1]), np.float32)
        t = np.linspace(0, 1, H)[:, None, None]
        grad = (top * (1 - t) + bot * t).repeat(W, 1).astype(np.uint8)
        fc = Image.fromarray(grad, 'RGBA')
    else:
        fc = Image.new('RGBA', (W, H), hexc(fill))
    if fill is not None:
        fc.putalpha(mask)
        canvas.alpha_composite(fc)
    # downsample with horizontal squeeze
    out_w = max(1, round(W / SS * sx))
    out_h = max(1, round(H / SS))
    small = canvas.resize((out_w, out_h), Image.LANCZOS)
    M = ow + 2
    box = Image.new('RGBA', (bw + 2 * M, bh + 2 * M), (0, 0, 0, 0))
    al, va = st.get('align', 'c'), st.get('valign', 'c')
    x = M + ((bw - out_w) // 2 if al == 'c' else (-ow if al == 'l' else bw - out_w + ow))
    y = M + ((bh - out_h) // 2 if va == 'c' else (-ow if va == 't' else bh - out_h + ow))
    box.alpha_composite(small.crop((max(0, -x), max(0, -y), out_w, out_h)), (max(0, x), max(0, y)))
    return box, M


def text_mask(arr, box, colors, tol):
    """Pixels inside box whose colour is close to one of the text colours (opaque-ish)."""
    x0, y0, x1, y1 = box
    sub = arr[y0:y1, x0:x1].astype(np.int32)
    m = np.zeros(sub.shape[:2], bool)
    for c in colors:
        rgb = np.array(hexc(c)[:3])
        m |= (np.abs(sub[..., :3] - rgb).max(-1) <= tol) & (sub[..., 3] > 60)
    full = np.zeros(arr.shape[:2], bool)
    full[y0:y1, x0:x1] = m
    return full


def inpaint_erase(arr, box, colors, tol=60, grow=1):
    """Remove text strokes: inpaint where they cover an underlying object, clear alpha elsewhere."""
    import cv2
    tm = text_mask(arr, box, colors, tol)
    if grow:
        tm = cv2.dilate(tm.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)) > 0
        x0, y0, x1, y1 = box
        lim = np.zeros_like(tm)
        lim[y0:y1, x0:x1] = True
        tm &= lim
    obj = (arr[..., 3] > 60) & ~tm
    k = np.ones((9, 9), np.uint8)
    objc = cv2.morphologyEx(obj.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
    # fill holes of the object silhouette
    ff = objc.astype(np.uint8).copy()
    h, w = ff.shape
    flood = ff.copy()
    cv2.floodFill(flood, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    holes = (flood == 0)
    objc |= holes
    inside = tm & objc
    outside = tm & ~objc
    rgb = np.ascontiguousarray(arr[..., :3][..., ::-1])
    rgb = cv2.inpaint(rgb, inside.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
    arr[..., :3] = rgb[..., ::-1]
    arr[inside, 3] = np.maximum(arr[inside, 3], 255)
    arr[outside] = 0
    ys, xs = np.nonzero(tm)
    if len(ys) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def _style(defaults, src, it):
    st = dict(defaults)
    if st.get('auto', True) and it.get('auto', True):
        st.update(sample_style(src, it['box']))
    st.update({k: v for k, v in it.items() if k not in ('box', 'text')})
    return st


def apply(spec, root='.'):
    src = Image.open(os.path.join(root, spec['src'])).convert('RGBA')
    arr = np.asarray(src).copy()
    defaults = spec.get('defaults', {})
    tboxes = []
    for it in spec['items']:
        st = _style(defaults, src, it)
        x0, y0, x1, y1 = it['box']
        er = st.get('erase', 'alpha')
        tb = list(it.get('tbox', it['box']))
        if er == 'alpha':
            arr[y0:y1, x0:x1] = 0
        elif er == 'inpaint':
            got = inpaint_erase(arr, it['box'], st.get('textcolors', ['#ffffff', '#000000']),
                                st.get('tol', 60), st.get('grow', 1))
            if got and 'tbox' not in it and st.get('fit_to_text'):
                tb = got
        elif er == 'inpaint_dark':
            # inpaint every pixel noticeably darker than a light background (handwriting on paper)
            import cv2
            sub = arr[y0:y1, x0:x1, :3].astype(np.int32)
            m = (sub[..., 1:].mean(-1) < st.get('thr', 215)).astype(np.uint8)
            g = st.get('grow', 2)
            m = cv2.dilate(m, np.ones((2 * g + 1, 2 * g + 1), np.uint8))
            full = np.zeros(arr.shape[:2], np.uint8)
            full[y0:y1, x0:x1] = m * 255
            rgb = np.ascontiguousarray(arr[..., :3][..., ::-1])
            rgb = cv2.inpaint(rgb, full, 5, cv2.INPAINT_TELEA)
            arr[..., :3] = rgb[..., ::-1]
        elif er != 'none':
            arr[y0:y1, x0:x1] = hexc(er)
        tboxes.append(tb)
    img = Image.fromarray(arr, 'RGBA')
    # keep every label inside the sprite rectangle the game actually draws (EBOOT sprite table);
    # text running onto a rect edge gets clipped in game
    rects = None
    if not spec.get('no_rect_clip'):
        try:
            import sprite_rects
            rects = sprite_rects.rects_for(os.path.splitext(os.path.basename(spec['out']))[0])
        except Exception:
            rects = None
    for it, tb in zip(spec['items'], tboxes):
        st = _style(defaults, src, it)
        clip = None
        if rects and it.get('text') and not st.get('angle') and not it.get('no_rect_clip'):
            r = sprite_rects.rect_at(rects, it['box'])
            if r:
                rx0, ry0, rx1, ry1 = r[0] + 1, r[1] + 1, r[0] + r[2] - 1, r[1] + r[3] - 1
                ow = sum(w for _, w in st.get('outline', []))
                m = max(0, ow - st.get('overflow', 1))
                tb = [max(tb[0], rx0 + ow - m), max(tb[1], ry0 + ow - m), min(tb[2], rx1 - ow + m), min(tb[3], ry1 - ow + m)]
                if tb[2] - tb[0] < 4 or tb[3] - tb[1] < 4:
                    tb = [rx0, ry0, rx1, ry1]
                st = dict(st, overflow=min(st.get('overflow', 1), ow))
                clip = (rx0, ry0, rx1, ry1)
        if it.get('text'):
            if clip:
                layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                _draw_item(layer, it, tb, st)
                cm = Image.new('L', img.size, 0)
                ImageDraw.Draw(cm).rectangle((clip[0], clip[1], clip[2] - 1, clip[3] - 1), fill=255)
                layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.split()[3]), np.asarray(cm))))
                img.alpha_composite(layer)
                continue
            _draw_item(img, it, tb, st)
    out = os.path.join(root, spec['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    return out


def _draw_item(img, it, tb, st):
    if True:
        if True:
            x0, y0, x1, y1 = tb
            g = st.get('widen', 0)
            x0, x1 = max(0, x0 - g), min(img.width, x1 + g)
            rot = st.get('rotate', 0)
            if st.get('angle'):
                import math
                ang = st['angle']
                L = int(math.hypot(x1 - x0, y1 - y0) * st.get('len', 0.85))
                t, M = render_text((L, st.get('th', 14)), it['text'], st)
                t = t.rotate(ang, expand=True, resample=Image.BICUBIC)
                cx, cy = (x0 + x1) // 2 - t.width // 2, (y0 + y1) // 2 - t.height // 2
                crop = t.crop((max(0, -cx), max(0, -cy), t.width, t.height))
                img.alpha_composite(crop, (max(0, cx), max(0, cy)))
                return
            if rot in (90, -90, 270):
                t, M = render_text((y1 - y0, x1 - x0), it['text'], st)
                t = t.rotate(rot, expand=True)
            else:
                t, M = render_text((x1 - x0, y1 - y0), it['text'], st)
            cx, cy = x0 - M, y0 - M
            crop = t.crop((max(0, -cx), max(0, -cy), t.width, t.height))
            img.alpha_composite(crop, (max(0, cx), max(0, cy)))


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'regions':
        img = Image.open(a[2])
        dx = int(a[4]) if len(a) > 4 else 5
        dy = int(a[5]) if len(a) > 5 else 2
        boxes = find_regions(img, dx, dy)
        annotate(img, boxes, a[3])
        for i, b in enumerate(boxes):
            print(i, b, sample_style(img, b))
    elif a[1] == 'apply':
        for p in a[2:]:
            spec = json.load(open(p, encoding='utf-8'))
            specs = spec if isinstance(spec, list) else [spec]
            for s in specs:
                print(apply(s, 'D:/newjakup'))
