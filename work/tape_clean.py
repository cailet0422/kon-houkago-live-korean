"""Remove the Japanese logo from the load-tape textures: rebuild the background under it
(flat colour + completed polka dots + the pink tape-corner rectangle) and use it inside the logo mask."""
import numpy as np, cv2
from PIL import Image
BOX = (0, 86, 84, 256)
NAMES = ['sel_common_load_tape_kiridashi', 'sel_common_load_tape_kiridashi_2', 'sel_common_load_tape_kiridashi_3']


def logo_mask(sub):
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    red = (r > 170) & (g < 110) & (b < 110)
    green = (g > r + 25) & (g > b + 25)
    orange = (r > 210) & (g > 90) & (g < 215) & (b < 100)
    dark = sub.max(-1) < 75
    cream = (r > 235) & (g > 215) & (b < 238) & (b > 140) & (r - b > 18)
    m = red | green | orange | dark | cream
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # fill holes
    h, w = m.shape
    fl = m.copy()
    cv2.floodFill(fl, np.zeros((h + 2, w + 2), np.uint8), (w - 1, 0), 1)
    return (m > 0) | (fl == 0)


def clean(n):
    a = np.asarray(Image.open(f'work/sprites/sprite__{n}.png').convert('RGBA')).copy()
    x0, y0, x1, y1 = BOX
    sub = a[y0:y1, x0:x1, :3].astype(int)
    m = logo_mask(sub)
    vis = ~cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    # background colour = most common visible colour
    px = sub[vis]
    keys, cnt = np.unique(px // 4, axis=0, return_counts=True)
    bgc = keys[cnt.argmax()] * 4 + 2
    near_bg = np.abs(sub - bgc).max(-1) < 24
    # tape-corner rectangle: pink, axis aligned
    pink = (np.abs(sub - np.array([240, 165, 210])).max(-1) < 45) & ~near_bg
    out = np.ascontiguousarray((np.zeros_like(sub) + bgc).astype(np.uint8))
    # dots: colour that is not bg and not pink-rect, visible
    other = vis & ~near_bg & ~pink & (sub.max(-1) > 120)
    dotc = np.median(sub[other], 0) if other.sum() > 20 else None
    if dotc is not None:
        n_, lab, st, _ = cv2.connectedComponentsWithStats(other.astype(np.uint8), 8)
        for k in range(1, n_):
            if st[k, 4] < 15:
                continue
            if np.abs(np.median(sub[lab == k], 0) - dotc).max() > 30:
                continue
            ys, xs = np.nonzero(lab == k)
            # circle fit (algebraic) on the component's outer pixels
            A = np.stack([xs, ys, np.ones_like(xs)], 1).astype(float)
            bb = -(xs ** 2 + ys ** 2).astype(float)
            # use boundary only
            cm = (lab == k).astype(np.uint8)
            edge = cm & ~cv2.erode(cm, np.ones((3, 3), np.uint8)).astype(bool)
            ey, ex = np.nonzero(edge & ~cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool))
            if len(ex) < 8:
                continue
            A = np.stack([ex, ey, np.ones_like(ex)], 1).astype(float)
            bb = -(ex ** 2 + ey ** 2).astype(float)
            D, E, F = np.linalg.lstsq(A, bb, rcond=None)[0]
            cx, cy = -D / 2, -E / 2
            rr = np.sqrt(max(cx * cx + cy * cy - F, 1))
            if not (8 <= rr <= 16):
                continue
            rr = min(rr, 13.0)
            cv2.circle(out, (int(round(cx)), int(round(cy))), int(round(rr)), tuple(int(v) for v in dotc), -1, cv2.LINE_AA)
    if pink.sum() > 50:
        def span(v):
            idx = np.nonzero(v >= 3)[0]
            runs, st_ = [], idx[0]
            for p_, q_ in zip(idx, idx[1:]):
                if q_ - p_ > 6:
                    runs.append((st_, p_)); st_ = q_
            runs.append((st_, idx[-1]))
            return max(runs, key=lambda r: r[1] - r[0])
        pv = pink & vis
        ys, xs = np.nonzero(pv)
        ry0 = ys.min(); rx1 = xs.max()
        top = pv[ry0:ry0 + 4]
        rx0 = np.nonzero(top.any(0))[0].min()
        right = pv[:, rx1 - 3:rx1 + 1]
        ry1 = np.nonzero(right.any(1))[0].max()
        if n.endswith('_3'):          # same tape design as _2; its lower edge is hidden by the logo
            rx0, ry0, rx1, ry1 = 39, 100 - 86, 77, 187 - 86
        pc = np.median(sub[pink], 0)
        ring = np.zeros_like(pink)
        ring[ry0 - 2:ry1 + 3, rx0 - 2:rx1 + 3] = True
        ring[ry0:ry1 + 1, rx0:rx1 + 1] = False
        dk = ring & vis & (sub.max(-1) < 170)
        if dk.sum() > 10:
            ec = np.median(sub[dk], 0)
            cv2.rectangle(out, (int(rx0) - 1, int(ry0) - 1), (int(rx1) + 1, int(ry1) + 1), tuple(int(v) for v in ec), -1)
        cv2.rectangle(out, (int(rx0), int(ry0)), (int(rx1), int(ry1)), tuple(int(v) for v in pc), -1)
        print(n, 'rect', rx0, ry0 + 86, rx1, ry1 + 86, 'outline', dk.sum())
    res = out.astype(int)
    a[y0:y1, x0:x1, :3] = res
    return a, m


if __name__ == '__main__':
    o = Image.new('RGB', (3 * 252, 510))
    for k, n in enumerate(NAMES):
        a, m = clean(n)
        Image.fromarray(a, 'RGBA').save(f'work/sprites/clean__{n}.png')
        o.paste(Image.fromarray(a).convert('RGB').crop(BOX).resize((252, 510), Image.NEAREST), (k * 252, 0))
    o.save('work/annot/tape_clean.png')
