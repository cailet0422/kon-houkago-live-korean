"""Korean logo on the load-tape textures.

The logo sprite (texture x0..84, y86..256, stored rotated) is drawn opaque at screen (282,183) over the
cassette's lower-right corner. Rebuild what the screen shows there (bg colour + polka dots + the cassette
sprite, which is texture (92..390, 38..228) drawn at screen (90,38)), rotate it into the box, then put the
Korean logo on top."""
import os
import sys
import numpy as np
import cv2
from PIL import Image
sys.path.insert(0, 'tools')
import logo_ko

BOX = (0, 86, 84, 256)            # texture box (x0, y0, x1, y1)
SCR = (282, 183)                  # its top-left on screen once rotated upright
CAS_TEX, CAS_SCR = (92, 38, 390, 228), (90, 38)
DOTS = [(378.2, 182.8), (333.8, 233.5), (429.3, 232.5)]
R = 12.3
TRANSPARENT = False
STYLE = {'sel_common_load_tape_kiridashi': ((255, 255, 255), (248, 130, 191)),
         'sel_common_load_tape_kiridashi_2': ((0, 202, 205), (250, 252, 255)),
         'sel_common_load_tape_kiridashi_3': ((255, 170, 139), (250, 252, 255))}


def screen_patch(tex, bg, dot):
    S = 4
    w, h = BOX[3] - BOX[1], BOX[2] - BOX[0]          # upright patch: 170 x 84
    big = np.zeros((h * S, w * S, 3), np.uint8)
    big[:] = bg
    for cx, cy in DOTS:
        cv2.circle(big, (int(round((cx - SCR[0]) * S)), int(round((cy - SCR[1]) * S))), int(R * S), dot, -1, cv2.LINE_AA)
    patch = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
    x0, y0, x1, y1 = CAS_TEX
    cas = tex[y0:y1, x0:x1, :3]
    # cassette placed at CAS_SCR; copy the overlapping part
    sx0, sy0 = CAS_SCR
    for yy in range(h):
        sy = SCR[1] + yy
        ty = sy - sy0
        if not 0 <= ty < cas.shape[0]:
            continue
        for xx in range(w):
            tx = SCR[0] + xx - sx0
            if 0 <= tx < cas.shape[1]:
                patch[yy, xx] = cas[ty, tx]
    return patch


def run(name, logo):
    base_p = f'assets_ko/sprite/{name}.png'
    # _2/_3 carry the relabelled "로딩!" from relabel.py; the white tape has no other edits
    src_p = base_p if (os.path.exists(base_p) and not name.endswith('kiridashi')) else f'work/sprites/sprite__{name}.png'
    tex = np.asarray(Image.open(src_p).convert('RGBA')).copy()
    # The game shows only texels x 8..72, y 104..248 of the logo box (measured with a probe texture);
    # other texels of the box are sampled by the side panels, so only this window is replaced.
    wx0, wy0, wx1, wy1 = 8, 104, 73, 249
    clean = np.asarray(Image.open(f'work/sprites/clean__{name}.png').convert('RGB'))
    tex[wy0:wy1, wx0:wx1, :3] = clean[wy0:wy1, wx0:wx1]
    tex[wy0:wy1, wx0:wx1, 3] = 255
    img = Image.fromarray(tex, 'RGBA')
    r = logo.rotate(-90, expand=True, resample=Image.BICUBIC)
    # the game only shows texels x 8..72, y 104..248 of this box (measured with a probe texture)
    r = logo_ko.fit(r, 61, 141)
    img.alpha_composite(r, (10 + (61 - r.width) // 2, 105 + (141 - r.height) // 2))
    img.save(base_p)
    return img


def save_icon(logo):
    """sel_save_icon: logo sits on its own pastel background; remove the old one by inpainting."""
    name = 'sel_save_icon'
    a = np.asarray(Image.open(f'work/sprites/sprite__{name}.png').convert('RGBA')).copy()
    x0, y0, x1, y1 = 28, 424, 122, 480
    sub = a[y0:y1, x0:x1, :3].astype(int)
    ring = np.concatenate([a[y0:y1, x1:x1 + 8, :3].reshape(-1, 3), a[y0 - 6:y0, x0:x1, :3].reshape(-1, 3)])
    cols, cnt = np.unique((ring // 8) * 8, axis=0, return_counts=True)
    pal = cols[np.argsort(-cnt)[:6]] + 4
    d = np.min(np.linalg.norm(sub[:, :, None, :] - pal[None, None], axis=-1), -1)
    m = cv2.dilate((d > 22).astype(np.uint8), np.ones((5, 5), np.uint8))
    full = np.zeros(a.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = m * 255
    rgb = cv2.inpaint(np.ascontiguousarray(a[..., :3][..., ::-1]), full, 6, cv2.INPAINT_TELEA)
    a[..., :3] = rgb[..., ::-1]
    img = Image.fromarray(a, 'RGBA')
    r = logo_ko.fit(logo, x1 - x0 - 2, y1 - y0 - 2)
    img.alpha_composite(r, (x0 + (x1 - x0 - r.width) // 2, y0 + (y1 - y0 - r.height) // 2))
    img.save(f'assets_ko/sprite/{name}.png')


if __name__ == '__main__':
    L = Image.open('work/logo/ko_codex.png').convert('RGBA')
    for n in STYLE:
        run(n, L)
    save_icon(L)
    print('ok')
