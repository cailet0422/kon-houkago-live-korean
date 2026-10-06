"""Tile screenshots: grid.py out.png in1.png in2.png ... (crops PPSSPP window chrome)"""
import sys
from PIL import Image
ims = []
for f in sys.argv[2:]:
    im = Image.open(f).convert('RGB')
    # crop title bar + menu (~ 52px at 1936 wide), keep 16:9 area
    w, h = im.size
    im = im.crop((8, 52, w - 8, h - 8))
    ims.append(im.resize((640, int(640 * im.height / im.width))))
cols = 2 if len(ims) > 1 else 1
H = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols
out = Image.new('RGB', (640 * cols, H * rows))
for k, im in enumerate(ims):
    out.paste(im, ((k % cols) * 640, (k // cols) * H))
out.save(sys.argv[1])
