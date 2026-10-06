"""Terminology pass: align with established Korean K-On! translations
(응땅, 기-타, 릿쨩, -쨩 honorifics kept, 데스데빌)."""
import glob
import json
import os
import re

ROOT = 'D:/newjakup'

# --- manual KKS entries (id -> text)
KKS = {
    6: '유이:응땅!', 114: '기-타에게 푹 빠졌어', 131: '「응땅! 응땅!」',
    167: '(미오쨩도 사와코 선생님도 즐거워 보여~)', 217: '「자! 아즈사쨩 전용 컵이야」',
    232: '기-타에게 푹 빠졌어 플레이 기념.',
    391: '[머리파츠]미오쨩이 쓰는 헤드폰이야.', 395: '[머리파츠]릿쨩이 학원제 때 썼었지.',
    404: '[얼굴파츠]노도카쨩이랑 똑같은 안경이야.',
    824: '검은 비키니야. 미오쨩한테 잘 어울리네!', 825: '릿쨩다운 스포티한 비키니네!',
    830: '멜빵바지가 릿쨩답네!', 831: '무기쨩다운 우아한 코디네이트네~.',
    832: '작은 아즈사쨩한테 롱티가 어울려~.', 836: '타이트 스커트가 무기쨩한테 딱이네.',
    847: '아즈사쨩이 중학생 때 입던 교복이야.', 852: '스쿨 수영복! 유이쨩, 잘 어울리네~.',
    911: '응땅!', 1747: '릿쨩다운 기운 넘치는 헤어스타일이네!', 1748: '무기쨩이 머리를 묶으니 신선하네~.',
    1952: '유이의 애용 기타. 이름은 「기-타」.', 1970: '누구나 쉽게 리듬을 타요. 응땅!',
    2042: '미오쨩 팬클럽의 포스터.',
    2474: '릿쨩~', 2476: '릿쨩 대원', 2480: '응땅', 2493: '네 차례야, 기-타!', 2499: '릿쨩, 한 곡 더!',
    2505: '노도카쨩~!', 2598: '릿쨩 멋있어~!',
    2662: '기-타밖에 못 쳐요 히라사와 유이!', 2702: '기-타에게 푹 빠졌어!',
    2738: '부터 기-타에게 푹 빠졌어 클리어.', 2888: '기-타와 응땅', 3099: '기-타 너무 좋아!',
}

# --- teatime events: (file, record) -> lines (max 10 chars per line)
TTS = {
    ('TTS_Nm_0001.tts', 7): ['자자, 아즈사쨩', '차 한잔 어때?'],
    ('TTS_Nm_0001.tts', 14): ['오오⁉', '역시 릿쨩!'],
    ('TTS_Nm_0005.tts', 3): ['알겠사옵니다!', '릿쨩 대장님‼'],
    ('TTS_Nm_0055.tts', 5): ['저기 릿쨩!', '한 번 더!', '한 번 더 하자!'],
    ('TTS_Nm_0056.tts', 5): ['오오!', '역시 릿쨩!'],
    ('TTS_Nm_0056.tts', 6): ['미오쨩~', '다리가 떨리시네요', '괜찮으신가요?'],
    ('TTS_Nm_0057.tts', 8): ['아즈사쨩……'],
    ('TTS_Nm_0202.tts', 0): ['릿쨩의 드럼', '정말 멋지다'],
    ('TTS_Nm_0303.tts', 3): ['말랑말랑~!', '미오쨩 손가락', '말랑말랑~!'],
    ('TTS_Nm_0304.tts', 3): ['유이쨩', '케이크 있어', '이따 먹을까?'],
    ('TTS_Nm_0404.tts', 1): ['오~', '들어 보자', '릿쨩!'],
    ('TTS_Nm_0404.tts', 7): ['릿쨩', '너무했어'],
    ('TTS_Nm_0404.tts', 9): ['미오쨩', '괜찮으니까', '유령 같은 건 없어'],
    ('TTS_Nm_0405.tts', 0): ['미오쨩, 이', '카세트테이프는……'],
    ('TTS_Nm_0505.tts', 2): ['자자, 미오쨩', '릿쨩도 일부러', '그런 건 아니잖아'],
    ('TTS_Nm_0601.tts', 0): ['릿쨩~', '노래를 너무 불러서', '목소리가 이상해~'],
    ('TTS_Nm_0602.tts', 1): ['앰프는 무겁구나~', '무기쨩~'],
    ('TTS_Nm_0604.tts', 1): ['무기쨩?'],
    ('TTS_Nm_0903.tts', 6): ['자', '아즈사쨩 전용', '컵이야'],
    ('TTS_Nm_1305.tts', 6): ['좋겠다~', '집집마다 한 대씩', '무기쨩이 있으면~'],
    ('TTS_Nm_9902.tts', 5): ['냠! 하후!?', '리, 릿쨔앙!', '이거, 엄청 크다!'],
    ('TTS_Nm_9905.tts', 7): ['유이쨩~', '아즈사쨩~'],
    ('TTS_Nm_9913.tts', 0): ['응, 땅', '응, 땅!'],
    ('TTS_Nm_9913.tts', 3): ['그, 응땅이라는 게', '……뭔가요?'],
    ('TTS_Nm_9913.tts', 4): ['리듬이야!', '아즈냥도 해 보자', '자……응, 땅!'],
    ('TTS_Nm_9913.tts', 5): ['에, 에엣?', '음, 응땅?'],
    ('TTS_Nm_9913.tts', 6): ['에헤헤, 응, 땅!'],
    ('TTS_Nm_9913.tts', 7): ['응, 땅', '응, 땅……'],
    ('TTS_Nm_9917.tts', 1): ['릿쨩!', '이런 곳에 오면', '학생회 녀석들이……'],
    ('TTS_Nm_9917.tts', 3): ['아아, 릿쨩……', '당신은 어째서', '릿쨩인가요?'],
    ('TTS_Nm_9918.tts', 0): ['무기쨩~', '오늘 간식은', '뭐야~?'],
    ('TTS_Nm_9918.tts', 10): ['유이쨩'],
    ('TTS_Nm_9920.tts', 11): ['릿쨩', '미오쨩이', '안 듣고 있어'],
    ('TTS_Nm_9922.tts', 0): ['야~, 릿쨩!', '이 제출 서류', '틀렸잖아!'],
    ('TTS_Nm_9922.tts', 6): ['맞다 맞다……', '데스데빌 사와코', '선생님이었지……'],
    ('TTS_Nm_9922.tts', 9): ['아즈사쨩……', '경음부에 꽤', '익숙해졌구나……'],
    ('TTS_Nm_9923.tts', 1): ['무기쨩, 너', '좋은 신부가', '될 거야~'],
    ('TTS_Nm_9923.tts', 6): ['아즈사쨩도 먹을래?'],
    ('TTS_Nm_9923.tts', 7): ['무기쨩', '한 그릇 더!', '아, 크림 올려 줘'],
    ('TTS_Nm_9925.tts', 1): ['앗!', '노도카쨩~!'],
    ('TTS_Nm_9925.tts', 4): ['그런데', '왜 노도카쨩이~?'],
    ('TTS_Nm_9925.tts', 6): ['아, 그렇구나!', '노도카쨩은', '학생회였지!'],
    ('TTS_Nm_9926.tts', 1): ['오늘은 노도카쨩한테', '내 연주를 들려주고', '싶어!'],
    ('TTS_Nm_9926.tts', 4): ['잘 봐!', '노도카쨩!'],
    ('TTS_Nm_9927.tts', 7): ['유이쨩, 정말', '열심히 하고 있어'],
}

# --- EBOOT strings (file offset -> text)
EBOOT = {'0x274544': '기-타에게 푹 빠졌어', '0x297344': '기-타에게 푹 빠졌어'}

kks_files = sorted(glob.glob(f'{ROOT}/text/ko/kks_*.json'))
done = set()
for p in kks_files:
    d = json.load(open(p, encoding='utf-8'))
    ch = False
    for k in list(d):
        if int(k) in KKS:
            d[k] = KKS[int(k)]
            ch = True
            done.add(int(k))
    if ch:
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('kks fixed', len(done), 'missing', sorted(set(KKS) - done))

for (fn, i), lines in TTS.items():
    over = [l for l in lines if len(l) > 10]
    if over:
        print('TOO LONG', fn, i, over)
tts_done = 0
for p in sorted(glob.glob(f'{ROOT}/text/tts_ko_*.json')):
    d = json.load(open(p, encoding='utf-8'))
    ch = False
    for (fn, i), lines in TTS.items():
        if fn in d:
            d[fn][i] = lines
            ch = True
            tts_done += 1
    if ch:
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('tts fixed', tts_done, '/', len(TTS))

p = f'{ROOT}/text/eboot_ko_manual.json'
d = json.load(open(p, encoding='utf-8'))
d.update(EBOOT)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('eboot fixed', len(EBOOT))
