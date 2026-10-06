import json
import glob
from pathlib import Path

p = 'D:/newjakup/tools/codex_edit.py'
s = open(p, encoding='utf-8').read()
old = """        pairs = '\\n'.join(f'- "{jp}"  ->  "{ko}"' for jp, ko in job['texts'])"""
assert old in s, 'pattern'
new = """        if job.get('texts'):
            pairs = '\\n'.join(f'- "{jp}"  ->  "{ko}"' for jp, ko in job['texts'])
        else:
            pairs = ('Read every piece of Japanese text in the image yourself and translate it into natural, concise Korean '
                     '(friendly game UI tone, about as short as the Japanese so it fits the same boxes). '
                     'Use this glossary consistently:\\n' + GLOSSARY)"""
s = s.replace(old, new)
g = '''GLOSSARY = """えんそう!->연주!, つうしん!->통신!, うたおう!->노래하자!, きせかえ!->옷입히기!, とけい!->시계!, あるばむ!->앨범!,
せってい!->설정!, あいてむ!->아이템!, せーぶ!->세이브!, 部室->부실, 放課後ティータイム->방과후 티타임, 軽音部->경음부, おきて->규칙,
唯->유이, 澪->미오, 律/りっちゃん->리츠/릿짱, 紬/ムギ->츠무기/무기, 梓/あずにゃん->아즈사/아즈냥, さわ子->사와코, 和->노도카, 憂->우이,
コンボ->콤보, タイミングバー->타이밍 바, 音符->음표, ボタン->버튼, コスチューム->코스튬, アイテム->아이템, イベント->이벤트,
MCボイス->MC 보이스, 称号->칭호, ムービー->무비, 素材パック->소재 팩, バンド->밴드, リーダー->리더, メンバー->멤버, アラーム->알람.
Keep English words (costume, item, GRAPHIC, SOUND, VOICE, Perfect, COLLECTION, EVENT ...) and page numbers like 1/4 unchanged."""


def run_job(job, force=False):'''
if 'GLOSSARY = ' not in s:
    s = s.replace('def run_job(job, force=False):', g, 1)
open(p, 'w', encoding='utf-8').write(s)

jobs = []
for f in sorted(glob.glob('D:/newjakup/work/sprites/sprite__sel_tea_*tutorial_*_kiridashi.png')):
    n = Path(f).stem[len('sprite__'):]
    jobs.append({"name": n, "src": f"work/sprites/sprite__{n}.png", "out": f"assets_ko/sprite/{n}.png", "texts": [],
                 "style": "Text inside yellow boxes is black bold; keep the box shapes. Small text in white boxes and "
                          "speech bubbles must also be translated.",
                 "merge": {"thresh": 50, "dilate": 2}})
json.dump(jobs, open('D:/newjakup/assets_src/codex_tutorials.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(jobs))
