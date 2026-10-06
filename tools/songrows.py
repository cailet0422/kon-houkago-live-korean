"""Build relabel specs for song-title atlases (one title per row / per cell).

usage: songrows.py <src.png> <out.png> <spec.json> [order=0..18 comma list | auto] [font]
Rows are found from the alpha profile; row k is song order[k].
"""
import json
import sys

import numpy as np
from PIL import Image

KO = {2: '후와후와 타임', 3: '내 사랑은 호치키스', 4: '붓펜 ~볼펜~', 5: '카레 다음 라이스', 6: "『Let's Go』",
      9: '기-타에게 푹 빠졌어', 13: '말괄량이 Way To Go', 14: '나는 나의 길을 간다',
      15: 'Dear My Keys ~건반의 마법~', 17: 'Girly Storm 질주 Stick', 18: '목표는 해피 100%↑↑↑'}


# approximate original lettering of cp_result_song_kiridashi / sel_* song lists
STYLES = {
    2: {'fill': ['#b8e8f8', '#3a88c0'], 'outline': [['#16284a', 1], ['#9fd0ff', 1]]},
    3: {'fill': '#e0287a', 'outline': [['#ffffff', 2]]},
    4: {'fill': '#ffffff', 'outline': [['#101010', 2]]},
    5: {'fill': ['#ffc030', '#f07000'], 'outline': [['#101010', 2]]},
    6: {'fill': '#e81c1c', 'outline': [['#fff8e0', 2]]},
    9: {'fill': ['#f8b0d0', '#e05080'], 'outline': [['#ffffff', 1], ['#c0a0d0', 1]]},
    13: {'fill': ['#c8b8f8', '#6858c0'], 'outline': [['#101010', 2]]},
    14: {'fill': ['#f8f000', '#20c040'], 'outline': [['#101010', 2]]},
    15: {'fill': '#fff4f8', 'outline': [['#e87898', 2]]},
    17: {'fill': ['#fff040', '#f09000'], 'outline': [['#101010', 2]]},
    18: {'fill': ['#ffb040', '#f06000'], 'outline': [['#ffffff', 1], ['#503010', 1]]},
}


def rows_of(img, x0=0, x1=None, amin=40, gap=1):
    a = np.asarray(img.convert('RGBA'))[..., 3] > amin
    if x1 is None:
        x1 = a.shape[1]
    prof = a[:, x0:x1].sum(1)
    rows, start = [], None
    for y, v in enumerate(prof):
        if v > 0 and start is None:
            start = y
        if v == 0 and start is not None:
            rows.append([start, y])
            start = None
    if start is not None:
        rows.append([start, len(prof)])
    out = []
    for y0, y1 in rows:
        cols = np.nonzero(a[y0:y1, x0:x1].any(0))[0]
        out.append([x0 + int(cols.min()), y0, x0 + int(cols.max()) + 1, y1])
    return out


def make(src, out, order, font='round', x0=0, x1=None, pad=1):
    img = Image.open(src)
    rows = rows_of(img, x0, x1)
    items = []
    for k, box in enumerate(rows):
        if k >= len(order):
            break
        s = order[k]
        if s in KO:
            b = [max(0, box[0] - pad), max(0, box[1] - pad), min(img.width, box[2] + pad), min(img.height, box[3] + pad)]
            it = {'box': b, 'text': KO[s], 'font': font, 'erase': 'alpha'}
            if s in STYLES:
                it.update(STYLES[s])
                it['auto'] = False
            items.append(it)
    return {'src': src, 'out': out, 'items': items}, rows


if __name__ == '__main__':
    src, out, spec = sys.argv[1:4]
    order = list(range(19)) if len(sys.argv) < 5 or sys.argv[4] == 'auto' else [int(v) for v in sys.argv[4].split(',')]
    font = sys.argv[5] if len(sys.argv) > 5 else 'round'
    sp, rows = make(src, out, order, font)
    print(len(rows), 'rows')
    json.dump(sp, open(spec, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
