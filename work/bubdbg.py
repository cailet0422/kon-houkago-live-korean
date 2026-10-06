import sys, json
sys.path.insert(0, 'tools')
import tutkit, numpy as np
from PIL import Image
# args: name x0,y0,x1,y1 ...
name = sys.argv[1]
a = tutkit.load(name)
img = Image.fromarray(a).convert('RGB')
ov = np.asarray(img).copy()
for c in sys.argv[2:]:
    clip = [int(v) for v in c.split(',')]
    f, b = tutkit.bubble_border(a, clip)
    print(clip, b, int(f.sum()))
    ov[f] = (ov[f] * 0.4 + np.array([0, 255, 0]) * 0.6).astype(np.uint8)
Image.fromarray(ov).crop((0, 0, 410, 210)).resize((820, 420), Image.NEAREST).save('work/annot/bubdbg.png')
