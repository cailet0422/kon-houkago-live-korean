import json, sys
sys.path.insert(0, 'tools')
import relabel
from PIL import Image
src = 'work/sprites/sprite__sel_common_kiridashi.png'
im = Image.open(src).convert('RGBA')
boxes = relabel.find_regions(im, 4, 2)
T = {1: '결정', 2: '뒤로', 3: '선택', 4: '삭제', 5: '선택', 6: '선택', 7: '시착', 9: '아이템', 10: '메뉴 표시',
     11: '전환', 12: '캐릭터 전환', 13: '재생', 14: '다음', 15: '메뉴 숨기기', 17: '미리보기', 18: '재생',
     19: '촬영', 21: '플레이 시작', 22: '메뉴', 23: '시계! 종료'}
PILL = {19, 22}
items = []
for i, t in T.items():
    x0, y0, x1, y1 = boxes[i]
    tx = x0 + (39 if i in PILL else 16)
    items.append({"box": [tx, y0, x1 + (3 if i == 17 else 0), y1], "text": t})
items.append({"box": [160, 75, 187, 89], "text": "회전"})
MAN = [([172, 139, 221, 153], '상하 이동'), ([272, 139, 354, 153], '시각 알림!'), ([392, 138, 443, 152], '재생 변경'),
       ([155, 171, 238, 185], '메뉴 숨기기'), ([272, 170, 350, 184], '커서 이동'), ([377, 171, 461, 185], '모션 전환'),
       ([162, 203, 233, 217], '메뉴 표시'), ([272, 200, 350, 214], '커서 이동'), ([408, 203, 491, 217], '전체 모션'),
       ([148, 230, 245, 245], '메뉴 표시 전환'), ([290, 228, 351, 245], '메인 편집'), ([403, 231, 491, 245], '개인 모션'),
       ([79, 175, 104, 190], '진행'), ([25, 203, 79, 218], '확대/축소')]
for b, t in MAN:
    items.append({"box": b, "text": t})
spec = {"src": src, "out": "assets_ko/sprite/sel_common_kiridashi.png",
        "defaults": {"auto": False, "font": "round", "fill": "#ffffff", "outline": [["#2a2a2a", 1]], "size": 12,
                     "align": "l", "pad": 0, "overflow": 1}, "items": items}
json.dump(spec, open('assets_src/specs/sel_common_kiridashi.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
