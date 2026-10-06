import json
L = {'oomori': '작사 : 오모리 쇼코', 'inaba': '작사 : 이나바 에미', 'kanata': '작사 : KANATA'}
C = {'fujisue': '작곡 : 후지스에 이츠키', 'kawaguchi': '작곡 : 카와구치 스스무', 'tomhack': '작곡 : Tom-H@ck',
     'tamura': '작곡 : 타무라 신지', 'momoishi': '작곡 : 모모이시 하지메', 'maesawa': '작곡 : 마에사와 히로유키',
     'tozawa': '작곡 : 아시자와 카즈노리', 'komori': '작곡 : 코모리 시게오', 'oka': '작곡 : 오카 나오키'}


def one(box, text):          # one-line credit "lyrics  composer"
    return [{"box": box, "text": text}]


def two(box, a, b):          # two stacked lines
    x0, y0, x1, y1 = box
    m = (y0 + y1) // 2
    return [{"box": [x0, y0, x1 + 30, m], "text": a, "align": "l"}, {"box": [x0, m, x1 + 30, y1], "text": b, "align": "l"}]


def split(box, a, b, gap=2):  # same line, split horizontally into two boxes found separately
    return [{"box": box[0], "text": a, "align": "l"}, {"box": box[1], "text": b, "align": "l"}]


S = {
    3: one([11, 84, 250, 101], L['inaba'] + '  ' + C['fujisue']),
    4: two([11, 61, 114, 93], L['inaba'], C['kawaguchi']),
    6: two([5, 53, 133, 85], L['kanata'], C['tomhack']),
    7: two([288, 4, 394, 34], L['oomori'], C['tamura']),
    8: one([5, 60, 224, 77], L['oomori'] + '  ' + C['tamura']),
    9: split([[5, 85, 115, 108], [118, 94, 254, 119]], L['oomori'], C['tomhack']),
    10: two([10, 60, 114, 92], L['oomori'], C['momoishi']),
    11: two([10, 52, 114, 84], L['oomori'], C['maesawa']),
    12: one([5, 44, 219, 61], L['oomori'] + '  ' + C['tozawa']),
    13: two([326, 8, 479, 51], L['oomori'], C['tomhack']),
    14: one([5, 53, 244, 69], L['oomori'] + '  ' + C['tomhack']),
    15: two([10, 52, 114, 84], L['oomori'], C['komori']),
    16: one([10, 53, 216, 69], L['oomori'] + '  ' + C['oka']),
    17: two([6, 125, 134, 157], L['oomori'], C['tomhack']),
    18: split([[9, 61, 113, 77], [114, 61, 250, 77]], L['oomori'], C['momoishi']),
}
specs = []
for k, items in S.items():
    n = 'cp_title_music_%02d_mongon' % k
    specs.append({"src": "work/sprites/sprite__%s.png" % n, "out": "assets_ko/sprite/%s.png" % n,
                  "defaults": {"font": "round", "pad": 0, "overflow": 2, "align": "l", "auto": False, "fill": ["#fff0f5", "#ffa8c4"], "outline": [["#c83c6e", 1]], "size": 12 if k not in (13, 17) else 14}, "items": items})
json.dump(specs, open('assets_src/specs/mongon_credits.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
