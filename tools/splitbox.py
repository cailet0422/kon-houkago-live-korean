"""Split boxes into words by vertical-projection gaps: splitbox.py <png> x0,y0,x1,y1 [mingap=3]"""
import sys
import numpy as np
from PIL import Image
img = np.asarray(Image.open(sys.argv[1]).convert('RGBA'))[..., 3] > 40
gap = int(sys.argv[3]) if len(sys.argv) > 3 else 3
x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(',')]
cols = img[y0:y1, x0:x1].any(0)
words, start, run = [], None, 0
for i, c in enumerate(cols):
    if c:
        if start is None:
            start = i
        run = 0
        last = i
    elif start is not None:
        run += 1
        if run >= gap:
            words.append((x0 + start, x0 + last + 1))
            start = None
if start is not None:
    words.append((x0 + start, x0 + last + 1))
for a, b in words:
    rows = np.nonzero(img[y0:y1, a:b].any(1))[0]
    print([a, y0 + int(rows.min()), b, y0 + int(rows.max()) + 1])
