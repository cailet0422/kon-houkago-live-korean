"""Merge an AI-edited image back onto the original texture.

Only pixels that changed noticeably (dilated) are taken from the edited image, so the rest of the
texture stays bit-identical and the original alpha channel is preserved.

usage: imgmerge.py <orig.png> <edited.png> <out.png> [threshold=48] [dilate=3] [x0,y0,x1,y1]
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def merge(orig_path, edit_path, out_path, thresh=48, dilate=3, rect=None, keep_alpha=True):
    o = Image.open(orig_path).convert('RGBA')
    e = Image.open(edit_path).convert('RGBA')
    if e.size != o.size:
        e = e.resize(o.size, Image.LANCZOS)
    oa = np.asarray(o).astype(np.int32)
    ea = np.asarray(e).astype(np.int32)
    # compare against the original composited on its own colour (alpha-aware)
    diff = np.abs(oa[..., :3] - ea[..., :3]).sum(-1)
    mask = diff > thresh
    if rect:
        m2 = np.zeros_like(mask)
        x0, y0, x1, y1 = rect
        m2[y0:y1, x0:x1] = True
        mask &= m2
    mimg = Image.fromarray((mask * 255).astype(np.uint8))
    if dilate:
        mimg = mimg.filter(ImageFilter.MaxFilter(dilate * 2 + 1))
    # feather the seam a little
    soft = np.asarray(mimg.filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255.0
    out = oa.astype(np.float32).copy()
    out[..., :3] = oa[..., :3] * (1 - soft[..., None]) + ea[..., :3] * soft[..., None]
    if not keep_alpha:
        out[..., 3] = np.maximum(oa[..., 3], (soft * 255))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(out_path)
    return int(mask.sum())


if __name__ == '__main__':
    a = sys.argv
    thresh = int(a[4]) if len(a) > 4 else 48
    dil = int(a[5]) if len(a) > 5 else 3
    rect = tuple(int(v) for v in a[6].split(',')) if len(a) > 6 else None
    print(merge(a[1], a[2], a[3], thresh, dil, rect), 'pixels changed')
