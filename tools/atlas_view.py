"""Render atlas rows zoomed with index labels for manual transcription."""
import sys
from PIL import Image, ImageDraw, ImageFont
atlas, r0, r1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
cell = int(sys.argv[5]) if len(sys.argv) > 5 else 16
guess = sys.argv[6] if len(sys.argv) > 6 else None
Z = 3
im = Image.open(atlas).convert('RGBA')
cols = im.width // cell
g = {}
if guess:
    for l in open(guess, encoding='utf-8'):
        p = l.rstrip('\n').split('\t')
        g[int(p[0])] = p[1]
f = ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', 14)
fj = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 22)
rh = cell * Z + (28 if guess else 4)
W = 40 + cols * (cell * Z + 4)
o = Image.new('RGB', (W, (r1 - r0) * rh + 4), (30, 30, 70))
d = ImageDraw.Draw(o)
for r in range(r0, r1):
    y = (r - r0) * rh
    d.text((2, y + 10), str(r * cols), font=f, fill=(255, 255, 0))
    for c in range(cols):
        i = r * cols + c
        cc = im.crop((c * cell, r * cell, c * cell + cell, r * cell + cell)).resize((cell * Z, cell * Z), Image.NEAREST)
        bg = Image.new('RGBA', cc.size, (60, 60, 120, 255) if c % 2 else (40, 40, 100, 255))
        bg.alpha_composite(cc)
        x = 40 + c * (cell * Z + 4)
        o.paste(bg.convert('RGB'), (x, y))
        if guess and g.get(i):
            d.text((x + 12, y + cell * Z), g[i], font=fj, fill=(120, 255, 120))
o.save(out)
