<div align="center">

[![English](https://img.shields.io/badge/README-English-lightgrey?style=for-the-badge)](README.md)
[![한국어](https://img.shields.io/badge/README-한국어-blue?style=for-the-badge)](README.ko.md)

# 케이온! 방과후 라이브!! 한국어 패치

**K-On! Houkago Live!! Korean Translation Patch** · PSP · ULJM05709

[![Release](https://img.shields.io/github/v/release/cailet0422/kon-houkago-live-korean?style=flat-square&label=최신%20버전)](https://github.com/cailet0422/kon-houkago-live-korean/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
![Platform](https://img.shields.io/badge/지원-PSP%20%7C%20PS%20Vita%20%7C%20PPSSPP-ff69b4?style=flat-square)

**🌸 다운로드 페이지: https://cailet0422.github.io/kon-houkago-live-korean/**

<img src="docs/images/loading.png" width="45%"> <img src="docs/images/clubroom.png" width="45%">

</div>

일본에서만 발매된 PSP 리듬 게임 **케이온! 방과후 라이브!!** (けいおん! 放課後ライブ!!, 세가, 2010)의 한국어 패치입니다.
게임 내 모든 텍스트와 메뉴, 튜토리얼, 타이틀 로고, 대부분의 글자 텍스처를 한국어로 옮겼습니다.

> [!IMPORTANT]
> 이 저장소에는 게임이 **포함되어 있지 않습니다.** 직접 소유한 일본판 UMD를 덤프한 ISO
> (`K-On! Houkago Live!! (Japan).iso`)가 필요하며, 수정되지 않은 바로 그 원본 ISO에만 적용됩니다.

---

## 목차

- [스크린샷](#스크린샷)
- [번역 범위](#번역-범위)
- [다운로드](#다운로드)
- [시작하기 전에: 원본 ISO 확인](#시작하기-전에-원본-iso-확인)
- [1단계 — 패치 적용](#1단계--패치-적용)
  - [Windows](#windows-konkopatcherexe)
  - [안드로이드](#안드로이드-konkopatcherapk)
  - [macOS / 리눅스 / 기타 (xdelta)](#macos--리눅스--기타-xdelta)
- [2단계 — 게임 실행](#2단계--게임-실행)
  - [PSP 실기](#psp-실기)
  - [PS Vita / PS TV (Adrenaline)](#ps-vita--ps-tv-adrenaline)
  - [PPSSPP (Windows / macOS / 리눅스)](#ppsspp-windows--macos--리눅스)
  - [PPSSPP (안드로이드)](#ppsspp-안드로이드)
  - [PPSSPP (아이폰 / 아이패드)](#ppsspp-아이폰--아이패드)
  - [스팀덱](#스팀덱)
- [중요: 「인스톨」은 반드시 OFF](#중요-인스톨은-반드시-off)
- [문제 해결 / 자주 묻는 질문](#문제-해결--자주-묻는-질문)
- [저장소 구성](#저장소-구성)
- [라이선스](#라이선스)
- [면책 조항](#면책-조항)

---

## 스크린샷

| | |
|:-:|:-:|
| <img src="docs/images/dialogue.png" width="420"> | <img src="docs/images/tutorial.png" width="420"> |
| 부실 대화 | 튜토리얼 |
| <img src="docs/images/song_select.png" width="420"> | <img src="docs/images/play_info.png" width="420"> |
| 곡 선택 | 플레이 정보 |

## 번역 범위

- 게임 내 모든 텍스트: 메뉴, 설명문, 아이템, 의상, 칭호, 시스템 메시지
- 부실(티타임) 이벤트 대사 49편 전부
- 타이틀 로고(로딩 테이프·세이브 아이콘·XMB 아이콘 포함), 메뉴 라벨, 튜토리얼 전 페이지,
  곡 타이틀 카드, 앨범 썸네일, 스태프롤, 부실 소품(포스터·간판·칠판 낙서 등) 텍스처
- PSP XMB에 표시되는 게임 제목
- 용어는 국내에 알려진 케이온! 번역을 따랐습니다 (응땅, 기-타, 릿쨩, 아즈냥, 방과후 티타임, 내 사랑은 호치키스 등)

**일부러 번역하지 않은 부분**

- 노래 가사(노래하자! 모드 자막 등): 음원과의 일치 및 가사 저작권 때문에 원문 유지
- 스태프롤의 일반 스태프 실명, 저작권 표기
- 이름 입력 화면의 가나 키보드

## 다운로드

[**최신 릴리스**](https://github.com/cailet0422/kon-houkago-live-korean/releases/latest)에서 받으세요.

| 파일 | 대상 | 비고 |
|---|---|---|
| `KonKoPatcher.exe` | Windows 7 이상 | 클릭 몇 번으로 끝나는 자동 패치 프로그램 (패치 데이터 내장) |
| `KonKoPatcher.apk` | 안드로이드 5.0 이상 | 휴대폰에서 바로 패치 |
| `kon_houkago_live_ko.xdelta` | 모든 OS | 표준 xdelta3 패치 파일 |

세 가지 모두 완전히 같은 ISO를 만듭니다. 이 중 **하나만** 받으면 됩니다.

## 시작하기 전에: 원본 ISO 확인

**일본판**, 압축하지 않은 **.iso** 파일이어야 합니다 (CSO/CHD/ZSO 불가).

| | |
|---|---|
| 파일명 (Redump 기준) | `K-On! Houkago Live!! (Japan).iso` |
| 게임 ID | `ULJM-05709` |
| 크기 | `1,756,659,712` 바이트 |
| CRC32 | `2F89D4E5` |
| SHA-1 | `7e0120b1557249a3678315d57b72c6fe4cbcfb92` |

Windows·안드로이드 패처는 이 값을 자동으로 확인합니다. 직접 확인하려면:

```powershell
# Windows (PowerShell)
Get-FileHash -Algorithm SHA1 "K-On! Houkago Live!! (Japan).iso"
```
```bash
# macOS
shasum -a 1 "K-On! Houkago Live!! (Japan).iso"
# 리눅스
sha1sum "K-On! Houkago Live!! (Japan).iso"
```

> [!TIP]
> 가지고 있는 파일이 **.cso**라면 먼저 .iso로 풀어 주세요 (예: `maxcso --decompress game.cso`).
> CSO는 무손실 압축이라 풀면 해시가 다시 일치합니다.
> 직접 덤프했는데도 해시가 다르다면 덤프가 손상되었을 가능성이 큽니다. 다시 덤프해 보세요.

패치 결과물은 원본과 크기가 같고 SHA-1은 `ffa313fb7a3f3567995ebf9e91ca63cb9100d2d6` 입니다.

## 1단계 — 패치 적용

패치된 ISO를 저장할 여유 공간 **약 1.8GB**가 필요합니다. 원본 파일은 바뀌지 않습니다.

### Windows (`KonKoPatcher.exe`)

1. `KonKoPatcher.exe`를 받아 아무 폴더에나 둡니다.
2. 실행합니다. *“Windows의 PC 보호”* 창이 뜨면 **추가 정보 → 실행**을 누르세요
   (코드 서명이 없어서 나오는 경고입니다).
3. **[찾아보기...]** 로 원본 ISO를 고르거나, ISO 파일을 **창에 끌어다 놓습니다** (exe 아이콘에 끌어다 놓아도 됩니다).
4. **[패치]** 를 누르면 다음이 자동으로 진행됩니다.
   1. 원본 ISO 확인 (크기 + SHA-1)
   2. 패치 적용
   3. 결과 파일 검증
5. **완료!** 가 표시되면 **원본 ISO와 같은 폴더**에 `K-On_Houkago_Live_KO.iso`가 만들어져 있습니다.

.NET Framework 4가 필요합니다 (Windows 8 이상은 기본 설치, Windows 7은 없으면 마이크로소프트에서 설치).

### 안드로이드 (`KonKoPatcher.apk`)

1. 휴대폰에서 `KonKoPatcher.apk`를 받습니다.
2. 파일을 열어 설치합니다. 요청이 뜨면 브라우저/파일 관리자에 **출처를 알 수 없는 앱 설치**를 허용하세요.
3. 원본 ISO를 휴대폰(내부 저장소 또는 SD카드)에 복사해 둡니다.
4. **케이온! 한국어 패치** 앱을 엽니다.
5. **[원본 ISO 선택]** 을 눌러 원본 ISO를 고릅니다.
6. **[패치]** 를 누르고, 결과를 저장할 위치와 파일 이름을 정합니다
   (예: `Download/K-On_Houkago_Live_KO.iso`).
7. **완료!** 가 뜰 때까지 기다립니다 (보통 1~5분). **진행 중에는 앱을 닫지 마세요.**

만들어진 ISO는 안드로이드용 PPSSPP에서 바로 실행할 수 있습니다 (아래 참고).

### macOS / 리눅스 / 기타 (xdelta)

xdelta3를 지원하는 아무 도구로 `kon_houkago_live_ko.xdelta`를 적용하면 됩니다.

**명령줄**

```bash
# macOS:  brew install xdelta
# 데비안/우분투:  sudo apt install xdelta3
# 페도라:  sudo dnf install xdelta
xdelta3 -d -s "K-On! Houkago Live!! (Japan).iso" kon_houkago_live_ko.xdelta "K-On_Houkago_Live_KO.iso"
```

Windows에서도 `xdelta3.exe`로 똑같이 할 수 있습니다.

**GUI** — *Delta Patcher*(Windows/macOS/리눅스), *xdelta UI* 등 아무 xdelta 프로그램이나 사용 가능합니다.

1. 원본 파일(Original file) → 일본판 ISO
2. 패치 파일(Patch / XDelta file) → `kon_houkago_live_ko.xdelta`
3. 출력(Output) → `K-On_Houkago_Live_KO.iso`
4. 적용(Apply / Patch)

xdelta가 *checksum* 또는 *source* 오류를 내면 원본 ISO가 맞지 않는 것입니다 → [원본 ISO 확인](#시작하기-전에-원본-iso-확인)

## 2단계 — 게임 실행

### PSP 실기

**커스텀 펌웨어(CFW)** 가 설치된 PSP-1000 / 2000 / 3000 / E1000(스트리트) / N1000(PSP Go)에서 동작합니다
(예: 펌웨어 6.60/6.61 + [ARK-4](https://github.com/PSP-Archive/ARK-4), PRO-C, LME).
CFW 설치 방법 자체는 이 문서에서 다루지 않습니다. 사용하는 CFW의 안내를 따라 주세요.

1. PSP를 컴퓨터에 연결하거나(**설정 → USB 연결**) 메모리 스틱을 카드 리더기에 꽂습니다.
2. `K-On_Houkago_Live_KO.iso`를 메모리 스틱 최상위의 **`ISO`** 폴더에 복사합니다 (없으면 만드세요).
   ```
   ms0:/ISO/K-On_Houkago_Live_KO.iso      ← 메모리 스틱 (PSP-1000/2000/3000/E1000, PSP Go의 M2 카드)
   ef0:/ISO/K-On_Houkago_Live_KO.iso      ← PSP Go 내장 메모리
   ```
   ISO 용량이 1.76GB이므로 **2GB 이상**(FAT32) 메모리 스틱이 필요합니다.
3. USB 연결을 끊고 XMB의 **게임 → 메모리 스틱**으로 갑니다.
   한국어 아이콘과 함께 **케이온! 방과후 라이브!!** 가 보입니다.
4. 게임을 실행합니다. 게임 내 설정의 **「인스톨」은 OFF 상태를 유지**하세요 ([아래 설명](#중요-인스톨은-반드시-off)).

게임이 실행되지 않거나 멈추면 XMB에서 CFW의 VSH 메뉴(보통 **SELECT** 버튼)를 열어
**ISO 드라이버**(예: Inferno ↔ NP9660 / M33)를 바꾼 뒤 다시 실행해 보세요.

기존 일본판 세이브 데이터를 그대로 이어서 쓸 수 있습니다.

> [!NOTE]
> 개발과 테스트는 주로 PPSSPP에서 진행했습니다. 실기에서 플레이하셨다면
> 잘 되든 안 되든 [Issues](https://github.com/cailet0422/kon-houkago-live-korean/issues)에 결과를 알려 주세요.

### PS Vita / PS TV (Adrenaline)

[Adrenaline](https://github.com/TheOfficialFloW/Adrenaline)(비타에서 돌아가는 PSP CFW)이 설치된 비타/PS TV가 필요합니다.

1. VitaShell의 USB 또는 FTP 모드로 `K-On_Houkago_Live_KO.iso`를 **`ux0:pspemu/ISO/`** 에 복사합니다
   (`ISO` 폴더가 없으면 만드세요).
2. **Adrenaline**을 실행하고 PSP XMB의 **게임 → 메모리 스틱**에서 게임을 실행합니다.
3. 게임 내 설정의 **「인스톨」은 OFF**로 두세요.

PSP 실기와 똑같이 동작합니다.

### PPSSPP (Windows / macOS / 리눅스)

1. [ppsspp.org](https://www.ppsspp.org/download/)에서 PPSSPP를 설치합니다 (**v1.20**에서 동작 확인, 최신 버전 권장).
   - 리눅스는 Flathub(`org.ppsspp.PPSSPP`)로도 설치할 수 있습니다.
2. PPSSPP를 실행하고 **불러오기(Load...)** 를 눌러 `K-On_Houkago_Live_KO.iso`를 선택합니다.
   또는 **게임** 탭에서 ISO가 있는 폴더로 이동해 홈으로 지정해 두면 매번 목록에 표시됩니다.
3. 기본 설정 그대로도 잘 동작합니다. 선택 사항:
   - **설정 → 시스템 → 언어 → 한국어** 로 PPSSPP 메뉴를 한국어로 바꿀 수 있습니다.
   - **설정 → 그래픽 → 렌더링 해상도**를 2배 이상으로 올리면 한글이 더 선명합니다.
   - 텍스처 *업스케일링* 필터(xBRZ 등)는 작은 한글을 뭉개 보이게 할 수 있으니 쓰지 않는 것을 권합니다.
4. 게임 내 설정의 **「인스톨」은 OFF**로 두세요.

기존 일본판 PPSSPP 세이브(`memstick/PSP/SAVEDATA`)를 그대로 쓸 수 있습니다.
단, **패치 전에 만든 상태 저장(세이브 스테이트)** 에는 일본어 텍스처가 메모리째 들어 있습니다.
게임을 처음부터 부팅한 뒤 게임 내 세이브로 불러오세요.

### PPSSPP (안드로이드)

1. Google Play에서 **PPSSPP**를 설치합니다 (또는 ppsspp.org의 APK).
2. 패치된 ISO를 휴대폰에 둡니다. `KonKoPatcher.apk`로 패치했다면 저장한 위치(예: `Download`)에 이미 있습니다.
   `PSP/GAME` 같은 전용 폴더를 만들어 두면 정리하기 편합니다.
3. PPSSPP의 **게임** 탭에서 그 폴더로 이동해(저장소 접근 권한 허용) 게임을 누릅니다.
   팁: **홈**(집 모양 아이콘)으로 지정하면 다음부터 바로 보입니다.
4. 게임 내 설정의 **「인스톨」은 OFF**로 두세요.

### PPSSPP (아이폰 / 아이패드)

1. App Store에서 **PPSSPP**를 설치합니다.
2. iOS용 패치 앱은 없으므로 컴퓨터나 안드로이드 기기에서 패치한 뒤,
   Finder/iTunes 파일 공유, AirDrop, 클라우드 드라이브 등으로
   **파일 → 나의 iPhone/iPad → PPSSPP** 폴더에 옮깁니다.
3. PPSSPP에서 그 폴더로 이동해 게임을 실행합니다.
4. 게임 내 설정의 **「인스톨」은 OFF**로 두세요.

### 스팀덱

1. 데스크톱 모드 → **Discover → PPSSPP**로 설치하거나 EmuDeck을 사용합니다.
2. 다른 컴퓨터(Windows/macOS/리눅스)에서 패치한 ISO를 스팀덱으로 복사합니다
   (EmuDeck 사용 시 `Emulation/roms/psp/`).
   `xdelta3`가 설치되어 있다면 스팀덱에서 직접 패치해도 됩니다.
3. PPSSPP(또는 EmuDeck의 Steam ROM Manager)로 실행합니다. **「인스톨」은 OFF**로 두세요.

## 중요: 「인스톨」은 반드시 OFF

게임 내 **설정!** 메뉴에는 로딩을 빠르게 하려고 데이터를 메모리 스틱에 복사하는 **인스톨** 옵션이 있습니다.
패치된 ISO를 원본과 같은 크기로 맞추기 위해 ISO 안의 인스톨용 데이터 파일을 비웠기 때문에,
**인스톨을 켜면 게임이 정상 동작하지 않습니다.** 기본값이 OFF이니 그대로 두기만 하면 됩니다.

## 문제 해결 / 자주 묻는 질문

<details>
<summary><b>패처가 “원본 ISO가 아닙니다”라고 하거나 xdelta가 실패해요</b></summary>

필요한 일본판 ISO가 아닙니다. 이미 패치한 파일, CSO 파일, 다른 지역판/버전, 손상된 덤프일 수 있습니다.
[원본 ISO 확인](#시작하기-전에-원본-iso-확인)의 크기와 SHA-1을 비교해 보세요.
</details>

<details>
<summary><b>아직 일본어로 나오는 부분이 있어요</b></summary>

노래 가사, 이름 입력 가나 키보드, 스태프 실명, 저작권 표기는 일부러 원문을 유지했습니다.
그 밖의 부분을 발견하면 스크린샷과 함께 이슈로 알려 주세요.
</details>

<details>
<summary><b>패치했는데 PPSSPP에서 일본어 텍스처가 보여요</b></summary>

일본판으로 만든 상태 저장(세이브 스테이트)을 불러왔을 가능성이 큽니다. 상태 저장에는 텍스처가 메모리째 저장됩니다.
게임을 정상 부팅한 뒤 게임 내 세이브를 불러오세요.
</details>

<details>
<summary><b>일본판 세이브 데이터를 그대로 쓸 수 있나요?</b></summary>

네. 세이브 형식은 바뀌지 않았으니 기존 세이브에서 이어서 하면 됩니다.
</details>

<details>
<summary><b>패치된 ISO를 CSO로 압축해도 되나요?</b></summary>

대부분 괜찮겠지만(maxcso 등), CSO로는 테스트하지 않았습니다. 문제가 생기면 ISO 그대로 사용하세요.
</details>

## 저장소 구성

이 저장소에는 패치 제작에 쓴 도구와 한국어 번역 데이터가 들어 있으며, 참고용으로 공개합니다.
직접 빌드하려면 원본 게임이 필요하고, 게임 내용이 담긴 파일(원문 텍스트 덤프, 추출·수정한 텍스처, ISO)은 포함하지 않았습니다.

| 경로 | 내용 |
|---|---|
| `text/` | 한국어 번역 (KKS 스크립트, EBOOT 문자열, 티타임 이벤트) |
| `assets_src/` | 텍스처 재작업 사양 (라벨 문구, 글꼴, 위치) |
| `tools/` | 파이썬 빌드 파이프라인: CPK/CRILAYLA, EBOOT 재배치, UVR/GIM 텍스처, 폰트 아틀라스, ISO 재구성, 패치 생성 |
| `tables/` | 문자 테이블 |
| `work/` | 이미지 제작용 스크립트 (로고, 스태프롤, 튜토리얼 등) |
| `patcher/` | Windows GUI 패처 (C#, .NET Framework 4)와 안드로이드 패처 (Java) |

주요 진입점: `tools/build.py` (한국어 ISO 빌드), `tools/release.py` (xdelta·EXE·APK 생성)

## 라이선스

이 저장소의 도구, 패처 소스 코드, 한국어 번역은 [MIT 라이선스](LICENSE)로 공개합니다.
*케이온!* 및 *케이온! 방과후 라이브!!* 자체와 원본 게임의 모든 내용은 각 권리자에게 있으며 이 라이선스의 대상이 **아닙니다.**

## 면책 조항

이 패치는 개인적인 즐거움을 위해 만든 비공식 팬 번역입니다. 세가, 교토 애니메이션 등 *케이온!* 의 어떤 권리자와도 관계가 없으며 승인받지 않았습니다.
게임 데이터는 배포하지 않습니다. 원본 게임을 정품으로 소유해 주세요. 사용에 따른 책임은 사용자에게 있습니다.
