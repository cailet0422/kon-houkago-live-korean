"""Helpers to build relabel items for column lists (one label per row inside an x-range)."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from songrows import rows_of


def col_items(src, x0, x1, texts, style, pad=1, root='D:/newjakup'):
    img = Image.open(os.path.join(root, src) if not os.path.isabs(src) else src)
    rows = rows_of(img, x0, x1)
    if len(rows) != len(texts):
        raise ValueError(f'{src} [{x0},{x1}): {len(rows)} rows found, {len(texts)} texts given: {rows}')
    items = []
    for b, t in zip(rows, texts):
        if t is None:
            continue
        items.append({"box": [max(0, b[0] - pad), max(0, b[1] - pad), min(img.width, b[2] + pad),
                              min(img.height, b[3] + pad)], "text": t, **style})
    return items
