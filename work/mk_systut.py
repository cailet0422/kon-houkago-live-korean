import json, subprocess
T1 = ["「연주!」 모드에서는,", "사쿠라고 경음부원이 되어 밴드 연주를 합니다",
      "리드 기타, 리듬 기타, 베이스, 키보드, 드럼", "5개 파트 중 좋아하는 파트를 골라 연주합시다",
      "높은 점수로 클리어하면 멋진 상을 받을 수 있대요", "많이 연주해서 하이스코어를 노려 봅시다!",
      "「연주!」 모드에서 얻은 아이템은", "여기 있는 멤버들에게 줄 수 있습니다",
      "△버튼으로 아이템 목록을 열고 줄 상대를 고르세요", "유이에게 「케이크」를 줘 보세요",
      "아이템을 주면 캐릭터가 반응을 보입니다", "주는 상대와 상황에 따라서는",
      "이벤트가 일어나기도 합니다", "여러 가지로 시도해 봅시다",
      "음식 아이템은 사용하면 없어지지만", "「연주!」 모드에서 다시 얻을 수 있으니",
      "안심하세요", "아이템 중에는 좀처럼 얻기 힘든", "레어한 것도 있는 것 같습니다",
      "앨범! 모드에 대해서"]
T2 = ["새로운 모드가 추가되었습니다", "「통신!」에서는 2~5명이 모여서", "통신 협력 플레이를 할 수 있습니다",
      "WLAN/WIRELESS 스위치가", "ON으로 되어 있는지 확인해 주세요", "「통신!」에서 사용할 유저 네임을",
      "입력해 주세요", "유저 네임은", "「설정!」에서 언제든지 변경할 수 있습니다",
      "옷입히기! 모드가 개방되었습니다", "이 모드에서는 연주! 모드에서 사용할",
      "헤어스타일·의상·액세서리를 바꿀 수 있습니다", "부실 메뉴에서", "옷입히기! 모드를 골라 옷을 갈아입읍시다",
      "새 머리 모양과 의상은", "연주! 모드에서 얻을 수 있습니다", "여러 곡과 파트로 플레이해 봅시다!",
      "「노래하자!」에서는 반주 음원과", "소재를 사용해 나만의 무비를 만들 수 있습니다",
      "만든 무비에 맞춰 즐겁게 「노래하자!」", "오리지널 무비를 배경으로", "좋아하는 곡을 불러 봅시다!"]
CENTER = {(1, 19), (2, 0), (2, 9)}
specs = []
for n, T in ((1, T1), (2, T2)):
    src = f'work/sprites/sprite__sel_tea_system_tutorial_{n}_kiridashi.png'
    out = subprocess.run(['python', 'tools/relabel.py', 'regions', src, 'work/annot/x.png', '30', '1'],
                         capture_output=True, text=True).stdout.splitlines()
    boxes = [json.loads(l.split(' ', 1)[1].split(']')[0] + ']') for l in out]
    assert len(boxes) == len(T), (n, len(boxes), len(T))
    items = []
    for i, (b, t) in enumerate(zip(boxes, T)):
        x0, y0, x1, y1 = b
        if (n, i) in CENTER:
            c = (x0 + x1) // 2
            box = [c - 110, y0 - 1, c + 110, y1 + 1]
            al = 'c'
        else:
            box = [x0, y0 - 1, max(x1, 300), y1 + 1]
            al = 'l'
        items.append({"box": box, "text": t, "align": al, "erase_box": b})
    specs.append({"src": src, "out": f"assets_ko/sprite/sel_tea_system_tutorial_{n}_kiridashi.png",
                  "defaults": {"auto": False, "fill": "#fafafa", "font": "round", "size": 13, "pad": 0}, "items": items})
json.dump(specs, open('assets_src/specs/sel_tea_system_tutorial.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
