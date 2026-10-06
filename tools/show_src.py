"""print kks source strings id range: show_src.py start end"""
import json, sys
d = json.load(open('D:/newjakup/text/kks_source.json', encoding='utf-8'))
a, b = int(sys.argv[1]), int(sys.argv[2])
for o in d[a:b]:
    refs = sorted(set(r.split(':')[0].replace('KKS_', '') for r in o['refs']))
    print(f"{o['id']}|{o['w']}|{','.join(refs)[:40]}|{o['jp']!r}")
