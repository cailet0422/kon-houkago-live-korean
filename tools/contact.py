"""Contact sheets: contact.py <dir> <out_prefix> [per_sheet=36] [thumb=180]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

d, pre = sys.argv[1], sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 36
T = int(sys.argv[4]) if len(sys.argv) > 4 else 180
files = sorted(f for f in os.listdir(d) if f.endswith('.png'))
f = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 11)
cols = 6
for s in range(0, len(files), per):
    chunk = files[s:s + per]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (T + 6), rows * (T + 30)), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for k, fn in enumerate(chunk):
        im = Image.open(os.path.join(d, fn)).convert('RGBA')
        w, h = im.size
        im.thumbnail((T, T))
        bg = Image.new('RGBA', im.size, (70, 70, 110, 255))
        # checker to reveal alpha
        for y in range(0, im.size[1], 8):
            for x in range(0, im.size[0], 8):
                if (x // 8 + y // 8) % 2:
                    bg.paste((90, 90, 130, 255), (x, y, x + 8, y + 8))
        bg.alpha_composite(im)
        x, y = (k % cols) * (T + 6), (k // cols) * (T + 30)
        sheet.paste(bg.convert('RGB'), (x, y))
        name = fn.replace('sprite__', '')[:34]
        dr.text((x, y + T + 2), f'{s + k}:{name}', font=f, fill=(255, 255, 0))
        dr.text((x, y + T + 15), f'{w}x{h}', font=f, fill=(180, 180, 180))
    sheet.save(f'{pre}_{s // per:02d}.png')
print((len(files) + per - 1) // per, 'sheets')
