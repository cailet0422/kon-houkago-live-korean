"""Collect every translated string with its Japanese source -> work/corpus.json
entries: {src: kks|eboot|tts, key, jp, ko, file}  (file = where the Korean lives, for fixing)"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
T = os.path.join(ROOT, 'text')


def load(p):
    return json.load(open(p, encoding='utf-8'))


def collect():
    out = []
    # KKS (later files override earlier, same order as build.TextDB)
    src = {o['id']: o for o in load(os.path.join(T, 'kks_source.json'))}
    where, ko = {}, {}
    files = [os.path.join(T, 'ko_derived.json')] + sorted(glob.glob(os.path.join(T, 'ko', 'kks_*.json')))
    if os.path.exists(os.path.join(T, 'kks_ko.json')):
        files.append(os.path.join(T, 'kks_ko.json'))
    for p in files:
        for k, v in load(p).items():
            if v:
                ko[int(k)] = v
                where[int(k)] = os.path.relpath(p, ROOT)
    for i, v in ko.items():
        if i in src:
            out.append({'src': 'kks', 'key': i, 'jp': src[i]['jp'], 'ko': v, 'file': where[i]})
    # EBOOT
    import eboot_text
    esrc, etr = eboot_text.load_all()
    for o in esrc:
        if o['off'] in etr:
            out.append({'src': 'eboot', 'key': o['off'], 'jp': o['jp'], 'ko': etr[o['off']], 'file': 'eboot'})
    # TTS events
    tsrc = {o['file']: o for o in load(os.path.join(T, 'tts_source.json'))}
    for p in sorted(glob.glob(os.path.join(T, 'tts_ko_*.json'))):
        for fn, recs in load(p).items():
            for i, (rec, k) in enumerate(zip(tsrc[fn]['lines'], recs)):
                if k:
                    out.append({'src': 'tts', 'key': f'{fn}:{i}', 'jp': '\n'.join(rec['jp']),
                                'ko': '\n'.join(k), 'file': os.path.relpath(p, ROOT), 'spk': rec['spk']})
    return out


if __name__ == '__main__':
    c = collect()
    json.dump(c, open(os.path.join(ROOT, 'work', 'corpus.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(c), {s: sum(1 for e in c if e['src'] == s) for s in ('kks', 'eboot', 'tts')})
