import json

names = ("Credits glossary: 作詞->작사, 作曲->작곡, 大森祥子->오모리 쇼코, 前澤寛之->마에사와 히로유키, 秋山澪->아키야마 미오, "
         "稲葉エミ->이나바 에미, 藤末樹->후지스에 이츠키, 川口進->카와구치 스스무, 田村信二->타무라 신지, 百石元->모모이시 하지메, "
         "戸沢和則->토자와 카즈노리, 小森茂生->코모리 시게오, 岡ナオキ->오카 나오키, 吉田詩織->요시다 시오리. "
         "Write the credit as e.g. '작사 : 오모리 쇼코' / '작곡 : Tom-H@ck' (romanised names like Tom-H@ck or KANATA stay as they are). "
         "Keep 'PUSH ○ BUTTON!!' and 'PLEASE WAIT...' exactly unchanged. Keep the same colours, outline and rotation of the credit lines.")
jobs = []
for i in range(19):
    n = f'cp_title_music_{i:02d}_mongon'
    jobs.append({"name": n, "src": f"work/sprites/sprite__{n}.png", "out": f"assets_ko/sprite/{n}.png",
                 "texts": [], "style": names, "bg": "#00ff00", "merge": {"thresh": 70, "dilate": 3}})
json.dump(jobs, open('D:/newjakup/assets_src/codex_mongon.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(jobs))
