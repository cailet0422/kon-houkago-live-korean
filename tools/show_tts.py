import json, sys
d = json.load(open('D:/newjakup/text/tts_source.json', encoding='utf-8'))
SPK = {1: '唯', 2: '澪', 4: '律', 8: '紬', 16: '梓', 32: 'さわ', 64: '和', 128: '憂'}
a, b = int(sys.argv[1]), int(sys.argv[2])
for e in d[a:b]:
    print('##', e['file'], e['nrec'])
    for k, l in enumerate(e['lines']):
        who = '+'.join(v for m, v in SPK.items() if l['spk'] & m) or str(l['spk'])
        print(f"{k:2d} [{who}] " + ' / '.join(l['jp']))
