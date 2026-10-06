"""Clean text off the small menu balls of sel_tea_kiridashi using the matching big (text-free) ball
scaled down as fill, so the Korean labels sit on an intact ball (the old alpha/inpaint erase punched holes)."""
import json
import numpy as np
import cv2
from PIL import Image

SRC = 'work/sprites/sprite__sel_tea_kiridashi.png'
OUT = 'work/sprites/clean__sel_tea_kiridashi.png'
im = Image.open(SRC).convert('RGBA')
A = np.asarray(im).copy()
BIG = {'r1': [(5, 69), (85, 69), (165, 69), (245, 69), (325, 69)], 'r2': [(136, 261), (217, 261), (297, 261), (377, 261)]}
# small ball component boxes (x, y, w, h) in label order
SMALL = {'r1': [(138, 146, 51, 47), (199, 145, 50, 48), (258, 146, 51, 47), (317, 145, 52, 48), (382, 146, 47, 47)],
         'r2': [(138, 202, 51, 47), (201, 202, 48, 47), (258, 201, 51, 48), (317, 202, 52, 47)]}
BANDS = {'r1': (155, 182), 'r2': (211, 237)}
for row in ('r1', 'r2'):
    y0b, y1b = BANDS[row]
    for (bx, by), (sx, sy, sw, sh) in zip(BIG[row], SMALL[row]):
        big = np.asarray(im.crop((bx, by, bx + 72, by + 71)).resize((47, 45), Image.LANCZOS)).astype(np.float32)
        reg = A[sy - 3:sy + sh + 3, sx - 6:sx + sw + 6].astype(np.float32)
        txt = (reg[..., :3].min(-1) > 205) | ((reg[..., :3].max(-1) < 70) & (reg[..., 3] > 120))
        best = None
        for dx in range(0, reg.shape[1] - 47 + 1):
            for dy in range(0, reg.shape[0] - 45 + 1):
                sub = reg[dy:dy + 45, dx:dx + 47]
                m = (~txt[dy:dy + 45, dx:dx + 47]) & (big[..., 3] > 230) & (sub[..., 3] > 230)
                if m.sum() < 400:
                    continue
                e = np.abs(sub - big)[m].mean()
                if best is None or e < best[0]:
                    best = (e, dx, dy)
        e, dx, dy = best
        ox, oy = sx - 6 + dx, sy - 3 + dy
        if (sx, sy) == (382, 146):   # yellow: the search locks onto the bright text; ball has no overhang
            ox, oy = 382, 146
        # text pixels inside the label band
        X0, X1 = sx - 6, sx + sw + 6
        band = np.zeros(A.shape[:2], bool)
        band[y0b:y1b, X0:X1] = True
        rgb = A[..., :3].astype(int)
        t = band & (((rgb.min(-1) > 205) & (A[..., 3] > 40)) | ((rgb.max(-1) < 70) & (A[..., 3] > 120)))
        t = cv2.dilate(t.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & band
        disk = np.zeros(A.shape[:2], bool)
        bigfull = np.zeros(A.shape, np.float32)
        body = cv2.morphologyEx((big[..., 3] > 128).astype(np.uint8), cv2.MORPH_OPEN,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 0
        disk[oy:oy + 45, ox:ox + 47] = body
        bigfull[oy:oy + 45, ox:ox + 47] = big
        A[disk] = bigfull[disk].astype(np.uint8)
        A[t & ~disk] = 0
        print(row, (sx, sy), 'offset', (ox, oy), 'err %.1f' % e)
Image.fromarray(A, 'RGBA').save(OUT)
spec = json.load(open('assets_src/specs/sel_tea_kiridashi.json', encoding='utf-8'))
spec['src'] = OUT
for it in spec['items']:
    if it['box'][1] >= 150:
        it['erase'] = 'none'
        it['outline'] = [['#141414', 2]]
json.dump(spec, open('assets_src/specs/sel_tea_kiridashi.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
