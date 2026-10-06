"""show untranslated kks source strings: show_todo.py [start_id] [count]"""
import json, sys, glob, os
ROOT = 'D:/newjakup'
d = json.load(open(f'{ROOT}/text/kks_source.json', encoding='utf-8'))
done = set(json.load(open(f'{ROOT}/text/ko_derived.json', encoding='utf-8')))
for p in glob.glob(f'{ROOT}/text/ko/kks_*.json'):
    done |= set(json.load(open(p, encoding='utf-8')))
SKIP = {'KKS_Acce2', 'KKS_AcceSetumei2', 'KKS_PvCollectionSetumei'}
a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
n = int(sys.argv[2]) if len(sys.argv) > 2 else 150
k = 0
for o in d:
    if o['id'] < a or str(o['id']) in done:
        continue
    if all(r.split(':')[0] in SKIP for r in o['refs']):
        continue
    refs = sorted(set(r.split(':')[0].replace('KKS_', '') for r in o['refs']))
    print(f"{o['id']}|{o['w']}|{','.join(refs)[:40]}|{o['jp']!r}")
    k += 1
    if k >= n:
        break
