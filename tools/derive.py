"""Derive translations for composite KKS strings from already translated parts.

Writes text/ko_derived.json (loaded by build.py before the manual files, so manual wins).
"""
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src = json.load(open(os.path.join(ROOT, 'text', 'kks_source.json'), encoding='utf-8'))
manual = {}
for p in sorted(glob.glob(os.path.join(ROOT, 'text', 'ko', 'kks_*.json'))):
    manual.update(json.load(open(p, encoding='utf-8')))
jp2ko = {}
for o in src:
    k = manual.get(str(o['id']))
    if k:
        jp2ko.setdefault(o['jp'], k)

NAMES = {'唯': '유이', '澪': '미오', '律': '리츠', '紬': '츠무기', '梓': '아즈사',
         'さわ子': '사와코', '和': '노도카', '憂': '우이'}
PREFIX = {'アクセサリー:': '액세서리:', 'コスチューム:': '코스튬:', 'アイテム:': '아이템:',
          'ヘアスタイル:': '헤어스타일:', 'モード:': '모드:', 'プレイ:': '플레이:', 'サウンド:': '사운드:',
          '称号:': '칭호:', 'イベント:': '이벤트:', 'ムービー:': '무비:', 'イラスト:': '일러스트:',
          '[NORMAL]': '[NORMAL]', '[HARD]': '[HARD]', '[EASY]': '[EASY]'}


def tr(s, depth=0):
    if s in jp2ko:
        return jp2ko[s]
    if depth > 3:
        return None
    m = re.fullmatch(r'(唯|澪|律|紬|梓)(MC\d+)', s)
    if m:
        return NAMES[m.group(1)] + m.group(2)
    m = re.fullmatch(r'バンド(MC\d+)', s)
    if m:
        return '밴드' + m.group(1)
    for pat, fmt in ((r'(.+) でムービー作成。', '{} 무비 제작.'), (r'(.+) のSP演出です。', '{}의 SP 연출입니다.'),
                     (r'(.+) のステージです。', '{}의 스테이지입니다.')):
        m = re.fullmatch(pat, s)
        if m:
            t = tr(m.group(1), depth + 1)
            return fmt.format(t) if t else None
    m = re.fullmatch(r'「(.+)」', s)
    if m:
        t = tr(m.group(1), depth + 1)
        return f'「{t}」' if t else None
    for a, b in PREFIX.items():
        if s.startswith(a) and len(s) > len(a):
            t = tr(s[len(a):], depth + 1)
            return b + t if t else None
    m = re.fullmatch(r'(.+)（(唯|澪|律|紬|梓|さわ子|和|憂)）', s)
    if m:
        t = tr(m.group(1), depth + 1)
        return f'{t}({NAMES[m.group(2)]})' if t else None
    return None


out = {}
for o in src:
    if str(o['id']) in manual:
        continue
    t = tr(o['jp'])
    if t:
        out[str(o['id'])] = t
json.dump(out, open(os.path.join(ROOT, 'text', 'ko_derived.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
done = len(manual) + len(out)
print(f'manual {len(manual)}, derived {len(out)}, total {done}/{len(src)}')
