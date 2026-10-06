"""Audit replaced sprite textures against the EBOOT sprite rectangles.

For every assets_ko/sprite/*.png with sprite rects:
  outside: changed, visible pixels that lie outside every sprite rect (never drawn -> cut off)
  edge:    changed, visible pixels on the 1-px border of a rect whose original border pixel was empty
           (new content runs into the rect edge -> clipped)"""
import os
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import sprite_rects

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TAPES = ['sel_common_load_tape_kiridashi', 'sel_common_load_tape_kiridashi_2', 'sel_common_load_tape_kiridashi_3']


def audit(verbose=False):
    R = sprite_rects.load()
    res = []
    for f in sorted(os.listdir(os.path.join(ROOT, 'assets_ko', 'sprite'))):
        n = f[:-4]
        key = f'PSP_GAME/USRDIR/sprite/{n}.uvr'
        rects = list(R.get(key, []))
        if sprite_rects.rects_for(n) is None and n not in TAPES:
            continue                      # sprite table does not describe this texture
        if n in TAPES:
            rects = sum((R.get(f'PSP_GAME/USRDIR/sprite/{t}.uvr', []) for t in TAPES), [])
        src = os.path.join(ROOT, 'work', 'sprites', f'sprite__{n}.png')
        if not rects or not os.path.exists(src):
            continue
        o = np.asarray(Image.open(src).convert('RGBA')).astype(int)
        k = np.asarray(Image.open(os.path.join(ROOT, 'assets_ko', 'sprite', f)).convert('RGBA')).astype(int)
        if o.shape != k.shape:
            continue
        h, w = o.shape[:2]
        po = o[..., :3] * o[..., 3:4] // 255
        pk = k[..., :3] * k[..., 3:4] // 255
        changed = (np.abs(po - pk).max(-1) > 48) & (k[..., 3] > 60)
        inside = np.zeros((h, w), bool)
        edge_bad = np.zeros((h, w), bool)
        for x, y, rw, rh, sid in rects:
            x1, y1 = min(w, x + rw), min(h, y + rh)
            inside[y:y1, x:x1] = True
        for x, y, rw, rh, sid in rects:
            x1, y1 = min(w, x + rw), min(h, y + rh)
            ring = np.zeros((h, w), bool)
            ring[y:y1, x:x1] = True
            ring[y + 1:y1 - 1, x + 1:x1 - 1] = False
            edge_bad |= ring & changed & (o[..., 3] < 60)
        import cv2
        near_orig = cv2.dilate((o[..., 3] > 60).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        outside = changed & ~inside & ~near_orig      # new content where the original had nothing
        res.append((int(outside.sum()), int(edge_bad.sum()), n, outside, edge_bad, rects))
    return res


if __name__ == '__main__':
    res = audit()
    bad = [r for r in res if r[0] > 3 or r[1] > 3]
    print(len(res), 'textures checked;', len(bad), 'flagged')
    for o_, e_, n, *_ in sorted(bad, key=lambda r: -(r[0] + r[1])):
        print(f'{n:45s} outside={o_:5d} edge={e_:5d}')
