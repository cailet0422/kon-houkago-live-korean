"""Sprite UV rectangles from the EBOOT sprite table.

EBOOT_dec: texture path pointer table (541 x u32 vaddr) at file 0x2E5770 (3036976);
sprite table at file 0x2AF278: 3647 records of <u16 x, y, w, h, u32 sprite_id, u32 texture_index>."""
import os
import re
import struct
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EB = os.path.join(ROOT, 'work', 'eboot', 'EBOOT_dec.BIN')
TEX_TABLE, TEX_N = 3036976, 541
SPR_TABLE, SPR_N = 0x2AF278, 3647


def load():
    d = open(EB, 'rb').read()
    names = {}
    for m in re.finditer(rb'PSP_GAME/USRDIR/[A-Za-z0-9_/\-\.]+?\.uvr\x00', d):
        names[m.start() - 0xA0] = m.group()[:-1].decode()
    tex = [names.get(struct.unpack_from('<I', d, TEX_TABLE + 4 * i)[0]) for i in range(TEX_N)]
    rects = defaultdict(list)
    for i in range(SPR_N):
        x, y, w, h, sid, t = struct.unpack_from('<4HII', d, SPR_TABLE + 16 * i)
        if t < len(tex) and tex[t]:
            rects[tex[t]].append((x, y, w, h, sid))
    return rects


if __name__ == '__main__':
    r = load()
    print(len(r), 'textures with sprites')
    for k in ('PSP_GAME/USRDIR/sprite/sel_common_load_tape_kiridashi.uvr', 'PSP_GAME/USRDIR/sprite/sel_tea_kiridashi.uvr'):
        print(k, r[k])


_CACHE = None


def rects_for(name, min_cover=0.85):
    """Sprite rects for a sprite texture name (e.g. 'sel_option'), or None when the table does not
    explain the texture (less than min_cover of its original visible pixels inside the rects)."""
    global _CACHE
    import numpy as np
    from PIL import Image
    if _CACHE is None:
        _CACHE = load()
    rects = _CACHE.get(f'PSP_GAME/USRDIR/sprite/{name}.uvr')
    src = os.path.join(ROOT, 'work', 'sprites', f'sprite__{name}.png')
    if not rects or not os.path.exists(src):
        return None
    a = np.asarray(Image.open(src).convert('RGBA'))[..., 3] > 60
    m = np.zeros_like(a)
    for x, y, w, h, _ in rects:
        m[y:y + h, x:x + w] = True
    if a.sum() == 0 or (a & m).sum() / a.sum() < min_cover:
        return None
    return rects


def rect_at(rects, box):
    """rect containing the centre of box (x0,y0,x1,y1); smallest if nested."""
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hit = [r for r in rects if r[0] <= cx < r[0] + r[2] and r[1] <= cy < r[1] + r[3]]
    return min(hit, key=lambda r: r[2] * r[3]) if hit else None
