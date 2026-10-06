import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = 'work/sprites/sprite__atr_title_2_kiridashi.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets_ko/sprite/atr_title_2_kiridashi.png'
base = Image.open(sys.argv[2] if len(sys.argv) > 2 else SRC).convert('RGBA')
arr = np.asarray(base).copy()
LINES = [('처음부터', [309, 7, 372, 18], [309, 54, 372, 68]),
         ('이어하기', [309, 23, 372, 34], [309, 70, 372, 84]),
         ('인스톨', [309, 39, 372, 50], [309, 86, 372, 100])]
for _, a, g in LINES:
    for x0, y0, x1, y1 in (a, g):
        arr[y0:y1, x0:x1] = 0
img = Image.fromarray(arr, 'RGBA')
f = ImageFont.truetype('C:/Windows/Fonts/NanumGothicExtraBold.ttf', 44)
for t, a, g in LINES:
    cx, cy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    m = Image.new('L', (64 * 4, 16 * 4), 0)
    ImageDraw.Draw(m).text((32 * 4, 8 * 4), t, font=f, fill=255, anchor='mm')
    m = m.resize((64, 16), Image.LANCZOS)
    w = Image.new('RGBA', m.size, (255, 255, 255, 255)); w.putalpha(m)
    img.alpha_composite(w, (int(cx - 32), int(cy - 8)))
    gm = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.9))
    gm = gm.point(lambda v: min(255, int(v * 1.25)))
    gw = Image.new('RGBA', gm.size, (255, 255, 255, 255)); gw.putalpha(gm)
    gx, gy = (g[0] + g[2]) / 2, (g[1] + g[3]) / 2
    img.alpha_composite(gw, (int(gx - 32), int(gy - 8)))
img.save(OUT)
print(OUT)
