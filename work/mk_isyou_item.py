"""sel_isyou_edit_item_kiridashi: grid of 80x16 labels (costume / hair / accessory numbers)."""
import json
N = ['유이', '미오', '리츠', '무기', '아즈사']
items = []
def lab(col, row, text):
    x, y = 2 + 80 * col, 2 + 16 * row
    items.append({"box": [x, y, x + 80, y + 16], "text": text})
for c in range(5):
    for r in range(21):
        lab(c, r, f'{N[c]} 코스 {r + 1}')
for k in range(20):
    lab(5, k, f'{N[k // 4]} 헤어 {k % 4 + 1}')
lab(5, 20, '유이 코스 22')
for k in range(38):
    c, r = k // 10, k % 10
    lab(c, 21 + r, f'액세서리 {k + 1}')
spec = {"src": "work/sprites/sprite__sel_isyou_edit_item_kiridashi.png",
        "out": "assets_ko/sprite/sel_isyou_edit_item_kiridashi.png",
        "defaults": {"auto": False, "font": "round", "fill": "#141414", "size": 11, "align": "l", "pad": 1, "erase": "alpha"},
        "items": items}
json.dump(spec, open('assets_src/specs/sel_isyou_edit_item_kiridashi.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(items))
