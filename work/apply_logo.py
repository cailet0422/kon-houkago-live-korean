"""Apply work/logo/logo_ko_3x.png to title atlas, load tapes, save icon and XMB ICON0."""
import os, subprocess, sys
sys.path.insert(0, 'tools')
import numpy as np, cv2, logo_ko
from PIL import Image
L = Image.open('work/logo/logo_ko_3x.png').convert('RGBA').resize((384, 160), Image.LANCZOS)
logo = L.crop((0, 0, 300, 160)); logo = logo.crop(logo.getbbox()); logo.save('work/logo/ko_codex.png')
base = Image.open('assets_ko/sprite/atr_title_2_kiridashi.png').convert('RGBA')
a = np.asarray(base).copy(); a[0:160, 0:300] = 0
base = Image.fromarray(a, 'RGBA'); base.alpha_composite(L.crop((0, 0, 300, 160)), (0, 0))
base.save('assets_ko/sprite/atr_title_2_kiridashi.png')
for f in ('assets_ko/sprite/sel_common_load_tape_kiridashi.png', 'assets_ko/sprite/sel_save_icon.png'):
    if os.path.exists(f): os.remove(f)
subprocess.run(['python', 'tools/relabel.py', 'apply', 'assets_src/specs/load_tape.json'], check=True, stdout=subprocess.DEVNULL)
subprocess.run(['python', 'work/mk_tape_logo.py'], check=True)
src = Image.open('work/iso_extract/PSP_GAME/ICON0.PNG').convert('RGBA')
a = np.asarray(src).copy(); x0, y0, x1, y1 = 24, 18, 122, 64
sub = a[y0:y1, x0:x1, :3].astype(int); r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
m = ((g < 150) & (r > 150) & (b < 120)) | ((g > r + 10) & (b < g)) | ((r > 200) & (g > 120) & (b < 90)) | (sub.max(-1) < 110) | ((b > r + 20) & (b > 150))
m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)); full = np.zeros(a.shape[:2], np.uint8); full[y0:y1, x0:x1] = m * 255
a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3][..., ::-1]), full, 4, cv2.INPAINT_TELEA)[..., ::-1]
out = Image.fromarray(a, 'RGBA'); r_ = logo_ko.fit(logo, 90, 48)
out.alpha_composite(r_, (72 - r_.width // 2, 41 - r_.height // 2))
out.convert('RGB').save('assets_ko/xmb/ICON0.PNG', optimize=True)
print('logo applied')
