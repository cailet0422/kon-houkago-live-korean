"""Staff roll pages: translate roles, headers, companies, song credits and cast.
Individual staff names (kanji, readings unknown) are kept as in the original credits."""
import json
import subprocess

PINK = {"auto": False, "font": "round", "fill": ["#ffe6ee", "#ff8fa8"], "outline": [["#e8708f", 1]],
        "shadow": [1, 1, "#1a1838"], "align": "l", "pad": 0, "overflow": 1, "size": 13}
YEL = dict(PINK, fill=["#fff6a8", "#ffc860"])

OM, IN = '오모리 쇼코', '이나바 에미'
SONGS = {
    4: [('Happy!? Sorry!!', OM, '타무라 신지', '코모리 시게오'), ('Don\'t say "lazy"', OM, '마에사와 히로유키', '코모리 시게오')],
    5: [('Sweet Bitter Beauty Song', OM, '타무라 신지', '코모리 시게오'), ('후와후와 타임', '아키야마 미오', '마에사와 히로유키', '마에사와 히로유키')],
    6: [('내 사랑은 호치키스', IN, '후지스에 이츠키', '모모이시 하지메'), ('붓펜 ~볼펜~', IN, '카와구치 스스무', '카와구치 스스무')],
    7: [('카레 다음 라이스', IN, '마에사와 히로유키', '마에사와 히로유키'), ('기-타에게 푹 빠졌어', OM, 'Tom-H@ck', 'Tom-H@ck')],
    8: [('Sunday Siesta', OM, '모모이시 하지메', '모모이시 하지메'), ('Heart Goes Boom!!', OM, '마에사와 히로유키', '마에사와 히로유키')],
    9: [('Hello Little Girl', OM, '아시자와 카즈노리', '코모리 시게오'), ('Girly Storm 질주 Stick', OM, 'Tom-H@ck', 'Tom-H@ck')],
    10: [('목표는 해피 100%↑↑↑', OM, '모모이시 하지메', '모모이시 하지메'), ('Dear My Keys ~건반의 마법~', OM, '코모리 시게오', '코모리 시게오')],
    11: [('Humming Bird', OM, '오카 나오키', '코모리 시게오'), ('말괄량이 Way To Go', OM, 'Tom-H@ck', 'Tom-H@ck')],
    12: [('나는 나의 길을 간다', OM, 'Tom-H@ck', 'Tom-H@ck'), ("『Let's Go』", 'KANATA', 'Tom-H@ck', 'Tom-H@ck')],
}
# page -> {region index: text}  (regions from relabel.find_regions(dx=7, dy=1))
TXT = {
    1: {0: '<캐스트>', 1: '히라사와 유이', 2: '토요사키 아키', 3: '아키야마 미오', 4: '히카사 요코',
        5: '타이나카 리츠', 6: '사토 사토미', 7: '코토부키 츠무기', 8: '코토부키 미나코', 9: '나카노 아즈사',
        10: '타케타츠 아야나', 11: '야마나카 사와코', 12: '사나다 아사미', 13: '히라사와 우이', 14: '요네자와 마도카',
        15: '마나베 노도카', 16: '토토 치카'},
    2: {0: '스페셜 땡스', 1: '카키후라이', 2: '주식회사 호분샤', 3: '협력', 4: '사쿠라고 경음부'},
    3: {0: '<악곡 제작>', 1: '주식회사 포니캐니언', 2: '「Cagayake!GIRLS」', 3: '작사 : ' + OM, 4: '작곡 : Tom-H@ck',
        5: '사운드 프로그래밍 : Tom-H@ck'},
    13: {0: '뮤직 프로듀서', 2: '뮤직 코디네이터', 4: '믹싱 엔지니어'},
    14: {0: '프로듀서', 2: '(포니캐니언)', 4: '(포니캐니언)', 6: '(포니캐니언)'},
    15: {0: '<패키지 일러스트>', 1: '주식회사 쿄토 애니메이션'},
    16: {0: '<보이스 녹음/연출>', 1: '주식회사 톤 파브리크', 3: '<보이스 편집>', 4: '스튜디오 곤구',
         6: '<보이스 제작 담당>', 7: '유한회사 라쿠온샤', 9: '<녹음 스튜디오>', 10: '스튜디오 곤구'},
    17: {0: '<게임 개발 협력>', 1: '주식회사 디지털 미디어 라보', 2: '프로젝트 매니저', 4: '디렉터',
         6: '연출 어드바이저', 9: '사운드 매니지먼트'},
    18: {0: '주식회사 진', 1: '프로젝트 매니저', 4: '디렉터', 6: '플래너'},
    19: {0: '디자이너', 1: '디자인 리더', 6: '배경', 10: '카메라'},
    20: {0: '의상 모델링', 6: '모션'},
    21: {0: '콘솔', 4: '프로그래머'},
    23: {0: '<제작>', 1: '주식회사 세가', 2: '프로듀서', 4: '디렉터'},
    24: {0: '어시스턴트 디렉터', 2: '프로젝트 매니저'},
    25: {0: '프로모션', 3: '퍼블리시티', 6: '영업', 9: '라이선스'},
    26: {0: 'AM 프로모션', 3: '패키지&매뉴얼 제작', 7: 'WEB 디자인'},
    27: {0: '테스트 팀'},
    28: {0: '개발 서포트'},
    29: {0: '스페셜 땡스'},
    30: {0: '시니어 프로듀서'}, 31: {0: '치프 프로듀서'}, 32: {0: '이그제큐티브 슈퍼바이저'},
    33: {0: '이그제큐티브 프로듀서'},
}
for p, songs in SONGS.items():
    d = {}
    for k, (t, ly, co, sp) in enumerate(songs):
        b = 4 * k
        d[b] = f'「{t}」'
        d[b + 1] = '작사 : ' + ly
        d[b + 2] = '작곡 : ' + co
        d[b + 3] = '사운드 프로그래밍 : ' + sp
    TXT[p] = d
# boxes that the detector merged with a name: role label only
OVERRIDE = {(19, 3): [7, 75, 165, 91]}
EXTRA = {19: [([7, 75, 165, 91], '캐릭터 모델링')]}

specs = []
for p in range(1, 35):
    if p not in TXT and p not in EXTRA:
        continue
    src = 'work/sprites/sprite__sel_staffroll_name_%02d.png' % p
    out = subprocess.run(['python', 'tools/relabel.py', 'regions', src, 'work/annot/x.png', '7', '1'],
                         capture_output=True, text=True).stdout.splitlines()
    boxes = [json.loads(l.split(' ', 1)[1].split(']')[0] + ']') for l in out]
    items = []
    for i, t in TXT.get(p, {}).items():
        b = boxes[i]
        st = YEL if (p == 1 and i % 2 == 1) else PINK
        items.append(dict(st, box=[max(0, b[0] - 1), max(0, b[1] - 1), min(256, b[2] + 3), min(256, b[3] + 2)], tbox=[b[0], b[1], 254, b[3]], text=t,
                          squeeze=True, erase='alpha'))
    for b, t in EXTRA.get(p, []):
        items.append(dict(PINK, box=b, tbox=[b[0], b[1], 166, b[3]], text=t, erase='alpha'))
    for it in items:
        it['size'] = 13
    specs.append({"src": src, "out": "assets_ko/sprite/sel_staffroll_name_%02d.png" % p, "items": items})
json.dump(specs, open('assets_src/specs/staffroll.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(specs))
