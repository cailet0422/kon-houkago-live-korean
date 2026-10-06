"""Batch image text-localisation through Codex (GPT-6 image_gen) + merge onto the original.

usage: codex_edit.py <jobs.json> [--only name,...] [--jobs 3] [--force]
job = {"name": "cp_title_music_04", "src": "work/sprites/sprite__cp_title_music_04.png",
       "out": "assets_ko/sprite/cp_title_music_04.png",
       "texts": [["ふでペン ～ボールペン～", "붓펜 ~볼펜~"]],
       "style": "optional extra style notes", "merge": {"thresh": 60, "dilate": 2, "rect": [x0,y0,x1,y1]},
       "bg": "#00ff00"   (optional: composite transparent src on this colour, key it out afterwards)}
Raw Codex outputs are kept in work/codex/<name>/output.png so merges can be redone without re-generating.
"""
import concurrent.futures as cf
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from imgmerge import merge  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def _find_codex():
    """The Codex Store app updates itself into a new versioned folder; ask Windows where it lives."""
    try:
        loc = subprocess.run(['powershell', '-NoProfile', '-Command',
                              '(Get-AppxPackage OpenAI.Codex).InstallLocation'],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        exe = os.path.join(loc, 'app', 'resources', 'codex.exe')
        if loc and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return 'codex'


CODEX = _find_codex()
WORK = os.path.join(ROOT, 'work', 'codex')
LIMIT_MARKERS = ('out of credits', 'usage limit', 'rate limit', "you've hit", 'quota', 'try again at', 'limit reached')

PROMPT = """Use your imagegen skill (built-in image_gen tool) to EDIT the attached image input.png ({w}x{h}, a texture from the PSP rhythm game "K-On! Houkago Live!!").
Translate the Japanese text in the image into Korean by replacing it in place:
{pairs}
Keep each Korean text exactly as written (verbatim Hangul, do not translate further, do not add or drop characters).
Match the original lettering style as closely as possible: same colours, outline/stroke, shadow, weight, slant, size and position; fit each Korean text in the same area as the Japanese it replaces.
{style}
Do not change anything else: keep characters, backgrounds, frames, icons and all other pixels as they are.{bgnote}
After generating, save the final image in the current working directory as output.png, resized to exactly {w}x{h} pixels.
Reply with the saved path only."""


GLOSSARY = """えんそう!->연주!, つうしん!->통신!, うたおう!->노래하자!, きせかえ!->옷입히기!, とけい!->시계!, あるばむ!->앨범!,
せってい!->설정!, あいてむ!->아이템!, せーぶ!->세이브!, 部室->부실, 放課後ティータイム->방과후 티타임, 軽音部->경음부, おきて->규칙,
唯->유이, 澪->미오, 律/りっちゃん->리츠/릿짱, 紬/ムギ->츠무기/무기, 梓/あずにゃん->아즈사/아즈냥, さわ子->사와코, 和->노도카, 憂->우이,
コンボ->콤보, タイミングバー->타이밍 바, 音符->음표, ボタン->버튼, コスチューム->코스튬, アイテム->아이템, イベント->이벤트,
MCボイス->MC 보이스, 称号->칭호, ムービー->무비, 素材パック->소재 팩, バンド->밴드, リーダー->리더, メンバー->멤버, アラーム->알람.
Keep English words (costume, item, GRAPHIC, SOUND, VOICE, Perfect, COLLECTION, EVENT ...) and page numbers like 1/4 unchanged."""


def run_job(job, force=False):
    name = job['name']
    d = os.path.join(WORK, name)
    os.makedirs(d, exist_ok=True)
    src = os.path.join(ROOT, job['src'])
    im = Image.open(src).convert('RGBA')
    if job.get('scale'):
        k = job['scale']
        im = im.resize((im.width * k, im.height * k), Image.LANCZOS)
    w, h = im.size
    inp = os.path.join(d, 'input.png')
    bg = job.get('bg')
    if bg:
        c = tuple(int(bg[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        base = Image.new('RGBA', im.size, c)
        base.alpha_composite(im)
        base.convert('RGB').save(inp)
    else:
        im.save(inp)
    outp = os.path.join(d, 'output.png')
    if force or not os.path.exists(outp):
        if job.get('texts'):
            pairs = '\n'.join(f'- "{jp}"  ->  "{ko}"' for jp, ko in job['texts'])
        else:
            pairs = ('Read every piece of Japanese text in the image yourself and translate it into natural, concise Korean '
                     '(friendly game UI tone, about as short as the Japanese so it fits the same boxes). '
                     'Use this glossary consistently:\n' + GLOSSARY)
        bgnote = ''
        if bg:
            bgnote = f'\nThe flat {bg} background is a chroma key: keep it perfectly flat {bg} everywhere outside the artwork.'
        prompt = PROMPT.format(w=w, h=h, pairs=pairs, style=job.get('style', ''), bgnote=bgnote)
        open(os.path.join(d, 'prompt.txt'), 'w', encoding='utf-8').write(prompt)
        with open(os.path.join(d, 'prompt.txt'), 'rb') as fi, open(os.path.join(d, 'log.txt'), 'wb') as fo:
            subprocess.run([CODEX, 'exec', '-m', 'gpt-6-astra', '--sandbox', 'workspace-write',
                            '--skip-git-repo-check', '-C', d, '--image=input.png', '-'],
                           stdin=fi, stdout=fo, stderr=subprocess.STDOUT, timeout=1500)
    if not os.path.exists(outp):
        log = open(os.path.join(d, 'log.txt'), encoding='utf-8', errors='replace').read().lower()
        if any(k in log for k in LIMIT_MARKERS):
            return name, 'LIMIT'
        return name, 'FAILED (no output)'
    return name, finish(job)


def chroma_key(edit_path, bg, out_path):
    e = np.asarray(Image.open(edit_path).convert('RGB')).astype(np.float32)
    c = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    dist = np.sqrt(((e - c) ** 2).sum(-1))
    a = np.clip((dist - 40) / 90, 0, 1)
    # despill: remove key colour contribution from semi-transparent edge pixels
    rgb = (e - c * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3)
    rgb = np.clip(rgb, 0, 255)
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(out_path)


def finish(job):
    d = os.path.join(WORK, job['name'])
    edit = os.path.join(d, 'output.png')
    out = os.path.join(ROOT, job['out'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    m = job.get('merge', {})
    if job.get('bg'):
        keyed = os.path.join(d, 'keyed.png')
        chroma_key(edit, job['bg'], keyed)
        src = Image.open(os.path.join(ROOT, job['src'])).convert('RGBA')
        k = Image.open(keyed).convert('RGBA').resize(src.size, Image.LANCZOS)
        if m.get('whole', False):
            k.save(out)
            return 'ok (keyed, whole)'
        so = np.asarray(src).copy()
        ko = np.asarray(k)
        if 'rects' in m:
            # take keyed pixels only inside the given text rects
            for x0, y0, x1, y1 in m['rects']:
                so[y0:y1, x0:x1] = ko[y0:y1, x0:x1]
        else:
            # automatic: replace where the keyed edit differs from the original (premultiplied), dilated
            import cv2
            pa = so[..., :3].astype(np.int32) * so[..., 3:4] // 255
            pb = ko[..., :3].astype(np.int32) * ko[..., 3:4] // 255
            diff = (np.abs(pa - pb).max(-1) > m.get('thresh', 70)) | (np.abs(so[..., 3].astype(int) - ko[..., 3]) > 120)
            diff = cv2.morphologyEx(diff.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
            mask = cv2.dilate(diff, np.ones((2 * m.get('dilate', 3) + 1,) * 2, np.uint8)) > 0
            if 'rect' in m:
                x0, y0, x1, y1 = m['rect']
                lim = np.zeros_like(mask)
                lim[y0:y1, x0:x1] = True
                mask &= lim
            so[mask] = ko[mask]
        Image.fromarray(so, 'RGBA').save(out)
        return 'ok (keyed)'
    n = merge(os.path.join(ROOT, job['src']), edit, out, m.get('thresh', 60), m.get('dilate', 2), m.get('rect'))
    return f'ok ({n} px)'


if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1], encoding='utf-8'))
    only = None
    nj = 3
    force = '--force' in sys.argv
    merge_only = '--merge-only' in sys.argv
    if '--only' in sys.argv:
        only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    if '--jobs' in sys.argv:
        nj = int(sys.argv[sys.argv.index('--jobs') + 1])
    jobs = [j for j in jobs if not only or j['name'] in only]
    if merge_only:
        for j in jobs:
            print(j['name'], finish(j), flush=True)
        sys.exit()
    hit = False
    with cf.ThreadPoolExecutor(nj) as ex:
        for name, res in ex.map(lambda j: run_job(j, force), jobs):
            print(name, res, flush=True)
            hit |= res == 'LIMIT'
    if hit:
        print('CODEX_LIMIT_REACHED', flush=True)
        sys.exit(3)
