"""Identify glyphs in a 16px-cell font atlas by template matching against system JP fonts.

usage: glyph_ocr.py <atlas.png> <out.tsv> [cell=16] [cols=32]
Writes: index \t char \t score \t second_char \t second_score
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [
    ('C:/Windows/Fonts/msgothic.ttc', 0),
    ('C:/Windows/Fonts/meiryo.ttc', 0),
    ('C:/Windows/Fonts/YuGothM.ttc', 0),
    ('C:/Windows/Fonts/BIZ-UDGothicR.ttc', 0),
    ('C:/Windows/Fonts/NotoSansJP-Medium.ttf', 0),
]


def charset():
    chars = set()
    for c in range(0x20, 0x7f):
        chars.add(chr(c))
    for hi in list(range(0x81, 0xa0)) + list(range(0xe0, 0xf0)):
        for lo in range(0x40, 0xfd):
            try:
                ch = bytes([hi, lo]).decode('cp932')
                if len(ch) == 1 and ch.isprintable():
                    chars.add(ch)
            except UnicodeDecodeError:
                pass
    for ch in '♪♥☆★…‥〜～！？♡◎〇①②③④⑤⑥⑦⑧⑨⑩™®©':
        chars.add(ch)
    return sorted(chars)


def norm(v):
    v = v.astype(np.float32)
    v = v - v.mean(axis=-1, keepdims=True)
    n = np.linalg.norm(v, axis=-1, keepdims=True) + 1e-6
    return v / n


def blur(a):
    # small 3x3 box blur for tolerance
    p = np.pad(a, ((0, 0), (1, 1), (1, 1)), mode='constant')
    s = sum(p[:, dy:dy + a.shape[1], dx:dx + a.shape[2]] for dy in range(3) for dx in range(3))
    return s / 9.0


def render_set(chars, font_path, idx, size, cell):
    f = ImageFont.truetype(font_path, size, index=idx)
    out = np.zeros((len(chars), cell, cell), np.float32)
    for i, ch in enumerate(chars):
        im = Image.new('L', (cell * 2, cell * 2), 0)
        d = ImageDraw.Draw(im)
        bb = d.textbbox((0, 0), ch, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if w <= 0 or h <= 0:
            continue
        d.text((cell - w / 2 - bb[0], cell - h / 2 - bb[1]), ch, font=f, fill=255)
        out[i] = np.asarray(im, np.float32)[cell // 2:cell // 2 + cell, cell // 2:cell // 2 + cell]
    return out


def center_cells(cells):
    """shift each cell so that its ink bbox is centered"""
    out = np.zeros_like(cells)
    n, h, w = cells.shape
    for i in range(n):
        c = cells[i]
        ys, xs = np.nonzero(c > 40)
        if len(ys) == 0:
            continue
        cy = (ys.min() + ys.max() + 1) / 2
        cx = (xs.min() + xs.max() + 1) / 2
        dy, dx = int(round(h / 2 - cy)), int(round(w / 2 - cx))
        out[i] = np.roll(np.roll(c, dy, 0), dx, 1)
    return out


def main():
    atlas, outp = sys.argv[1], sys.argv[2]
    cell = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    im = np.asarray(Image.open(atlas).convert('RGBA'))[..., 3].astype(np.float32)
    H, W = im.shape
    cols, rows = W // cell, H // cell
    cells = im.reshape(rows, cell, cols, cell).transpose(0, 2, 1, 3).reshape(-1, cell, cell)
    empty = cells.reshape(len(cells), -1).max(1) < 30
    cc = center_cells(cells)
    cvec = norm(blur(cc).reshape(len(cc), -1))
    chars = charset()
    best = np.full(len(cells), -2.0, np.float32)
    bestc = np.zeros(len(cells), np.int64)
    scores_all = np.full((len(cells), len(chars)), -2.0, np.float32)
    for fp, fi in FONTS:
        for size in (13, 14, 15):
            try:
                r = render_set(chars, fp, fi, size, cell)
            except OSError:
                continue
            r = center_cells(r)
            rv = norm(blur(r).reshape(len(r), -1))
            s = cvec @ rv.T
            scores_all = np.maximum(scores_all, s)
    order = np.argsort(-scores_all, axis=1)[:, :3]
    with open(outp, 'w', encoding='utf-8') as o:
        for i in range(len(cells)):
            if empty[i]:
                o.write(f'{i}\t\t0\t\t0\n')
                continue
            a, b = order[i, 0], order[i, 1]
            o.write(f'{i}\t{chars[a]}\t{scores_all[i, a]:.3f}\t{chars[b]}\t{scores_all[i, b]:.3f}\n')


if __name__ == '__main__':
    main()
