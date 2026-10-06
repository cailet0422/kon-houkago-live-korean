"""K-On! Houkago Live!! Korean patch builder.

python build.py [--no-iso]
Inputs : original ISO (+ extracted copy in work/), text/*.json translations, assets_ko/
Output : build/K-On_Houkago_Live_KO.iso
"""
import glob
import json
import os
import shutil
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK, cmd_rebuild  # noqa: E402
from eboot import Eboot  # noqa: E402
from fmdx import FMDX  # noqa: E402
from font_atlas import LEFT_PUNCT, RIGHT_PUNCT, build_sys_atlas, preview, render_glyph, white_alpha_palette  # noqa: E402
from tts import TTS, read_records, write_records  # noqa: E402
from uvr import UVR, make_uvr  # noqa: E402
import numpy as np  # noqa: E402
from kks import encode_record, load_tbl, read_kks, record_lines, wrap_text, write_kks  # noqa: E402
import isopatch  # noqa: E402
import eboot_text  # noqa: E402
from mips import find_addr_refs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORIG_ISO = os.path.join(ROOT, 'k-on!_houkago_live!!_(japan)', 'K-On! Houkago Live!! (Japan).iso')
EXTRACT = os.path.join(ROOT, 'work', 'iso_extract', 'PSP_GAME')
STD = os.path.join(ROOT, 'work', 'std', 'PSP_GAME', 'USRDIR')   # extracted std.cpk
EBOOT_DEC = os.path.join(ROOT, 'work', 'eboot', 'EBOOT_dec.BIN')
TEXT = os.path.join(ROOT, 'text')
ASSETS = os.path.join(ROOT, 'assets_ko')
BUILD = os.path.join(ROOT, 'build')
STAGE = os.path.join(BUILD, 'stage')          # replacement tree for std.cpk
TBL = load_tbl(os.path.join(ROOT, 'tables', 'sys_runtime.tbl'))
CHAR2IDX = {v: k for k, v in TBL.items()}

# KKS files built against an older atlas (garbage with SYS_RunTime, never displayed)
SKIP_KEEP = {'KKS_Acce2', 'KKS_AcceSetumei2', 'KKS_PvCollectionSetumei'}
# glyph cells that always keep their original image (latin, digits, symbols usable in Korean text)
RESERVED = set(range(0, 96)) | set(range(265, 317))
# character normalisation for Korean text -> original symbol cells
NORMALIZE = {' ': 0, '～': 290, '~': 290, '…': 291, '「': 292, '」': 293, '『': 294, '』': 295,
             '○': 296, '◎': 297, '●': 298, '×': 299, '△': 300, '▲': 301, '▽': 302, '▼': 303,
             '□': 304, '■': 305, 'ー': 308, '―': 308, '！': 309, '？': 310, '・': 289, '、': 287, '。': 288,
             '♪': 272, '☆': 270, '★': 271, '※': 279, '→': 278, '←': 278, '↑': 274, '↓': 277,
             '（': 283, '）': 284, '“': 275, '”': 276, '"': 77, "'": 68, '’': 68, '‘': 68,
             '%': 80, '％': 80, '&': 74, '＆': 309 - 1, '/': 73, '／': 73, ':': 87, '：': 87, '-': 85, '－': 85,
             '+': 83, '＋': 83, '·': 289, '♥': 272}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def load_json(name, default):
    p = os.path.join(TEXT, name)
    if not os.path.exists(p):
        return default
    return json.load(open(p, encoding='utf-8'))


# ------------------------------------------------------------------ text
class TextDB:
    def __init__(self):
        self.src = load_json('kks_source.json', [])
        merged = dict(load_json('ko_derived.json', {}))
        for p in sorted(glob.glob(os.path.join(TEXT, 'ko', 'kks_*.json'))):
            merged.update(json.load(open(p, encoding='utf-8')))
        merged.update(load_json('kks_ko.json', {}))
        self.ko = {int(k): v for k, v in merged.items() if v}
        self.by_ref = {}
        for o in self.src:
            for r in o['refs']:
                self.by_ref[r] = o

    def translation_for(self, kks_name, rec_idx):
        o = self.by_ref.get(f'{kks_name}:{rec_idx}')
        if o is None:
            return None
        return self.ko.get(o['id'])


def kks_files():
    refs = set(open(os.path.join(ROOT, 'work', 'kks_refs.txt')).read().split())
    out = []
    for p in sorted(glob.glob(os.path.join(STD, 'font', 'KKS_*.bin'))):
        n = os.path.basename(p)[:-4]
        if n not in refs or os.path.getsize(p) == 0:
            continue
        if 'PVlyrics' in n or 'PVEDIT' in n:   # lyrics use SYS_RunTime_Utaou; left in Japanese
            continue
        out.append((n, p))
    return out


# ------------------------------------------------------------------ glyphs
def plan_glyphs(db, eb_src, eb_tr):
    """Decide which atlas cells keep Japanese glyphs and where each Korean char goes."""
    keep = set(RESERVED)
    eb_chars = set()
    for o in eb_src:
        t = eb_tr.get(o['off'])
        if t is None:     # untranslated UI string still needs its Japanese glyphs
            keep.update(CHAR2IDX[c] for c in o['jp'] if c in CHAR2IDX)
        else:
            eb_chars.update(eboot_text.layout(t).replace('%s', ''))
    ko_chars = set()
    for n, p in kks_files():
        recs = read_kks(p)
        for i, (h, g) in enumerate(recs[32:]):
            t = db.translation_for(n, i)
            if t is None:
                if n not in SKIP_KEEP:
                    keep.update(g)
            else:
                ko_chars.update(t.replace('\n', ''))
    ko_chars |= eb_chars
    charmap = {}
    new_chars = []
    # EBOOT-visible chars first so they land on indices that own a UTF-8 slot (< 1000)
    for c in sorted(ko_chars, key=lambda c: (c not in eb_chars, c)):
        if c in LEFT_PUNCT or c in RIGHT_PUNCT:
            new_chars.append(c)          # Korean-style tight punctuation gets its own cell
        elif c in NORMALIZE:
            charmap[c] = NORMALIZE[c]
        elif c in CHAR2IDX and CHAR2IDX[c] in keep:
            charmap[c] = CHAR2IDX[c]
        elif 'Ａ' <= c <= 'ｚ' or '０' <= c <= '９':
            charmap[c] = CHAR2IDX[chr(ord(c) - 0xfee0)]
        else:
            new_chars.append(c)
    free = [i for i in range(1, 1024) if i not in keep]
    if len(new_chars) > len(free):
        raise SystemExit(f'glyph budget exceeded: need {len(new_chars)} new cells, only {len(free)} free')
    # most frequent / eboot-visible chars get indices < 1000 (those have UTF-8 slots)
    layout = {}
    for c, i in zip(new_chars, free):
        charmap[c] = i
        layout[i] = c
    log(f'glyphs: keep {len(keep)} jp cells, {len(new_chars)} new korean cells, {len(free) - len(new_chars)} spare')
    return charmap, layout, keep


class EbootRelocator:
    """Moves over-long EBOOT strings into the (unused) name-filter word list and repoints data pointers.

    The NG-word pointer table (1001 entries) is redirected to a single never-typeable string, which
    frees ~17KB of .rodata. Only strings referenced purely through 32-bit data pointers are moved.
    """
    NG_TABLE = 0x2e3700            # vaddr of u32[1001] NG word pointers
    NG_COUNT = 1001
    DATA_LO, DATA_HI = 0x1f7258 + 0xA0, 0x2ed360

    def __init__(self, eb):
        self.eb = eb
        d = eb.d
        ptrs = [struct.unpack_from('<I', d, self.NG_TABLE + 0xA0 + 4 * k)[0] for k in range(self.NG_COUNT)]
        lo, hi = min(ptrs), max(ptrs)
        end = hi + 0xA0
        end = d.index(b'\x00', end) + 1
        self.pool_lo = lo + 0xA0          # file offsets
        self.pool_hi = (end + 3) & ~3
        d[self.pool_lo:self.pool_lo + 4] = b'\x01\x00\x00\x00'
        for k in range(self.NG_COUNT):
            struct.pack_into('<I', d, self.NG_TABLE + 0xA0 + 4 * k, lo)
        d[self.pool_lo + 4:self.pool_hi] = b'\x00' * (self.pool_hi - self.pool_lo - 4)
        self.cur = self.pool_lo + 4
        self.vals = {}
        for fo in range(self.DATA_LO, self.DATA_HI, 4):
            if self.pool_lo <= fo < self.pool_hi:
                continue
            self.vals.setdefault(struct.unpack_from('<I', d, fo)[0], []).append(fo)
        self.moved = 0
        self.freed = []

    def free_left(self):
        return self.pool_hi - self.cur

    def relocate(self, file_off, data):
        va = file_off - 0xA0
        refs = self.vals.get(va)
        if not refs or find_addr_refs(va):
            return False
        need = (len(data) + 1 + 3) & ~3
        if self.cur + need > self.pool_hi:
            return False
        self.eb.d[self.cur:self.cur + len(data) + 1] = data + b'\x00'
        for fo in refs:
            struct.pack_into('<I', self.eb.d, fo, self.cur - 0xA0)
        # the original slot is now unreferenced: remember it for code-referenced strings
        self.freed.append((file_off, self.eb.d.index(b'\x00', file_off) - file_off))
        self.cur += need
        self.moved += 1
        return True

    def relocate_code(self, file_off, data):
        """Strings loaded via lui/addiu pairs: move them into a freed slot reachable with the same lui
        value and patch the 16-bit immediate of each addiu (and any data pointers)."""
        va = file_off - 0xA0
        pairs = find_addr_refs(va)
        if not pairs:
            return False
        hi = (va + 0x8000) >> 16
        lo = va & 0xffff
        d = self.eb.d
        js = sorted({j for _, j in pairs})
        for j in js:
            ins = struct.unpack_from('<I', d, 0xA0 + j)[0]
            if (ins >> 26) != 0x09 or (ins & 0xffff) != lo:      # only plain addiu
                return False
        need = len(data) + 1
        for k, (fo, ln) in enumerate(self.freed):
            nva = fo - 0xA0
            if ln + 1 >= need and ((nva + 0x8000) >> 16) == hi:
                d[fo:fo + ln + 1] = data + b'\x00' * (ln + 1 - len(data))
                for j in js:
                    ins = struct.unpack_from('<I', d, 0xA0 + j)[0]
                    struct.pack_into('<I', d, 0xA0 + j, (ins & 0xffff0000) | (nva & 0xffff))
                for ref in self.vals.get(va, []):
                    struct.pack_into('<I', d, ref, nva)
                rest = ln + 1 - need
                self.freed[k] = (fo + need, rest - 1) if rest > 1 else (fo, -1)
                self.moved += 1
                return True
        return False


# ------------------------------------------------------------------ teatime events
def build_tts(stage):
    tr = {}
    for p in sorted(glob.glob(os.path.join(TEXT, 'tts_ko_*.json'))):
        tr.update(json.load(open(p, encoding='utf-8')))
    n_done = 0
    for f in sorted(glob.glob(os.path.join(STD, 'teatime_event', 'Event', '*.tts'))):
        name = os.path.basename(f)
        lines_ko = tr.get(name)
        if not lines_ko:
            continue
        t = TTS(open(f, 'rb').read())
        recs = read_records(t.part(1))
        assert len(recs) == len(lines_ko), (name, len(recs), len(lines_ko))
        old = UVR(t.part(0))
        old_a = np.asarray(old.to_image())[..., 3]
        cells = {}          # key -> new index ; key = ('ch', c) or ('old', idx)
        def cell_for(key):
            if key not in cells:
                cells[key] = len(cells) + 1
            return cells[key]
        new_recs = []
        for (a, spk, glines), ko in zip(recs, lines_ko):
            if ko is None:  # keep original Japanese line (e.g. quoted song lyrics)
                new_recs.append((a, spk, [[cell_for(('old', g)) if g else 0 for g in ln] for ln in glines]))
                continue
            gl = [[0 if c == ' ' else cell_for(('ch', c)) for c in ln] for ln in ko]
            gl += [[] for _ in range(3 - len(gl))]
            new_recs.append((len(ko), spk, gl))
        n = len(cells) + 1
        h = 32
        while 32 * (h // 16) < n:
            h *= 2
        assert h <= 128, (name, n)
        w = 512
        alpha = np.zeros((h, w), np.uint8)
        for key, i in cells.items():
            r, c = divmod(i, 32)
            if key[0] == 'ch':
                g = render_glyph(key[1])
                if g[0].max() == 0 and g[15].max() > 0:
                    # keep the cell's bottom row empty: filtering would bleed it into the cell
                    # below (or, wrapping, into the empty cell 0 used for blanks)
                    g = np.vstack([g[1:], np.zeros((1, 16), np.uint8)])
            else:
                orr, occ = divmod(key[1], 32)
                g = old_a[orr * 16:orr * 16 + 16, occ * 16:occ * 16 + 16]
            alpha[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = g
        atlas = make_uvr(t.part(0), w, h, alpha, white_alpha_palette())
        data = t.build({0: atlas, 1: write_records(new_recs)})
        dst = os.path.join(stage, 'PSP_GAME', 'USRDIR', 'teatime_event', 'Event', name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)
        n_done += 1
    log(f'teatime events rebuilt: {n_done}')


# ------------------------------------------------------------------ main build
def main():
    no_iso = '--no-iso' in sys.argv
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    db = TextDB()
    log(f'translations loaded: {len(db.ko)}/{len(db.src)} kks strings')

    eb_src, eb_tr = eboot_text.load_all()
    log(f'eboot ui strings: {len(eb_tr)}/{len(eb_src)} translated')
    charmap, layout, keep = plan_glyphs(db, eb_src, eb_tr)

    # --- font atlas
    static_path = os.path.join(STD, 'bind', 'static.bin')
    static = FMDX(open(static_path, 'rb').read())
    sys_name = 'PSP_GAME/USRDIR/font/SYS_RunTime.uvr'
    new_atlas = build_sys_atlas(static.get(sys_name), layout, keep)
    preview(new_atlas, os.path.join(BUILD, 'SYS_RunTime_preview.png'))

    # --- KKS text
    new_kks = {}
    over = []
    for n, p in kks_files():
        recs = read_kks(p)
        width = len(recs[0][1]) // 5
        # visual width of this file's text box = longest original line
        disp = max([len(l) for h, g in recs[32:] for l in record_lines(g, width, TBL)] + [1])
        disp = min(disp, width)
        out = []
        for i, (h, g) in enumerate(recs):
            t = db.translation_for(n, i - 32) if i >= 32 else None
            if t is None:
                out.append((h, g))
            else:
                jp_lines = record_lines(g, width, TBL)
                if '\n' in t or len(jp_lines) > 1:
                    t = '\n'.join(wrap_text(t, disp))
                elif len(t) > disp:
                    over.append((n, i - 32, disp, t))   # single-line item wider than the original
                try:
                    out.append(encode_record(t, width, charmap))
                except ValueError as ex:
                    log('WARN', n, i - 32, ex)
                    out.append((h, g))
        tmp = os.path.join(BUILD, 'tmp.kks')
        write_kks(tmp, out)
        new_kks[n] = open(tmp, 'rb').read()
        dst = os.path.join(STAGE, 'PSP_GAME', 'USRDIR', 'font', n + '.bin')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(tmp, dst)

    build_tts(STAGE)

    with open(os.path.join(BUILD, 'kks_overflow.txt'), 'w', encoding='utf-8') as fo:
        for o in over:
            fo.write('	'.join(map(str, o)) + '\n')
    log(f'kks: {len(over)} single-line strings wider than their box (see build/kks_overflow.txt)')

    # --- bind packages
    index = json.load(open(os.path.join(ROOT, 'work', 'bind_index.json')))
    touched = {}
    def bind_set(inner, data, only_hash=None):
        for pkg, h, _ in index.get(inner, []):
            if only_hash is not None and h != only_hash:
                continue          # a different variant (e.g. 32x32 placeholder in *_dummy.bin) stays as is
            if pkg not in touched:
                touched[pkg] = FMDX(open(os.path.join(STD, 'bind', pkg), 'rb').read())
            touched[pkg].set(inner, data)
    touched['static.bin'] = static
    static.set(sys_name, new_atlas)
    for n, data in new_kks.items():
        bind_set(f'PSP_GAME/USRDIR/font/{n}.bin', data)
    # --- translated textures (assets_ko/<path under USRDIR>.png)
    from PIL import Image
    n_tex = 0
    for png in sorted(glob.glob(os.path.join(ASSETS, '**', '*.png'), recursive=True)):
        rel = os.path.relpath(png, ASSETS).replace(os.sep, '/')
        inner = 'PSP_GAME/USRDIR/' + rel[:-4] + '.uvr'
        if inner not in index:
            if not rel.startswith(('_', 'xmb/')):
                log('WARN asset without target:', rel)
            continue
        # pick the package variant whose texture matches the PNG size (some textures also exist as
        # 32x32 placeholders in *_dummy.bin packages; those must not be overwritten)
        want = Image.open(png).size
        pkg0, h0, orig = None, None, None
        for pkg, h, _ in index[inner]:
            fx = FMDX(open(os.path.join(STD, 'bind', pkg), 'rb').read())
            d0 = fx.get(inner)
            if (UVR(d0).w, UVR(d0).h) == want:
                pkg0, h0, orig = pkg, h, d0
                break
        if orig is None:
            log('WARN no variant matches size:', rel)
            continue
        import hashlib
        hk = hashlib.sha1(orig + open(png, 'rb').read() + b'kmeans1dxt1').hexdigest()
        cpath = os.path.join(BUILD, 'texcache', hk + '.uvr')
        if os.path.exists(cpath):
            new = open(cpath, 'rb').read()
        else:
            new = UVR(orig).from_image(Image.open(png))
            os.makedirs(os.path.dirname(cpath), exist_ok=True)
            open(cpath, 'wb').write(new)
        bind_set(inner, new, only_hash=h0)
        loose = os.path.join(STD, rel[:-4] + '.uvr')
        if os.path.exists(loose):
            dst = os.path.join(STAGE, 'PSP_GAME', 'USRDIR', rel[:-4] + '.uvr')
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(new)
        n_tex += 1
    log(f'textures replaced: {n_tex}')
    for pkg, f in touched.items():
        dst = os.path.join(STAGE, 'PSP_GAME', 'USRDIR', 'bind', pkg)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(f.build())
    log(f'bind packages rebuilt: {len(touched)}')

    # --- EBOOT
    eb = Eboot(EBOOT_DEC)
    for i in range(1024):
        if i in layout:
            eb.set_glyph(i, layout[i])
    for i, ch in eboot_text.ASCII_SLOTS.items():
        eb.set_glyph(i, ch, utf16=False)
    reloc = EbootRelocator(eb)
    bad = 0
    pending = []
    for o in eb_src:
        t = eb_tr.get(o['off'])
        if t is None:
            continue
        try:
            b = eboot_text.encode(t, charmap, eb)
        except KeyError as ex:
            log('WARN eboot', o['off'], ex)
            bad += 1
            continue
        if len(b) > o['cap']:
            if reloc.relocate(int(o['off'], 16), b):
                continue
            pending.append((o, b, t))
            continue
        off = int(o['off'], 16)   # file offset
        eb.d[off:off + o['cap'] + 1] = b + b'\0' * (o['cap'] + 1 - len(b))
    for o, b, t in pending:
        if not reloc.relocate_code(int(o['off'], 16), b):
            log(f"WARN eboot {o['off']} too long {len(b)}>{o['cap']}: {t!r}")
            bad += 1
    log(f'eboot strings written ({bad} skipped, {reloc.moved} relocated, {reloc.free_left()} bytes free)')
    eb_out = os.path.join(BUILD, 'EBOOT.BIN')
    eb.save(eb_out)

    # --- std.cpk
    cpk_out = os.path.join(BUILD, 'std.cpk')
    cmd_rebuild(os.path.join(EXTRACT, 'USRDIR', 'std.cpk'), STAGE, cpk_out)

    if no_iso:
        return
    iso_out = os.path.join(BUILD, 'K-On_Houkago_Live_KO.iso')
    log('writing iso ...')
    pairs = [
        ('PSP_GAME/INSDIR/STD.DNS', None),          # install data dropped: its space is reused by std.cpk
        ('PSP_GAME/USRDIR/std.cpk', cpk_out),
        ('PSP_GAME/SYSDIR/EBOOT.BIN', eb_out),
    ]
    # XMB assets (icon, Korean title)
    for fn in ('ICON0.PNG', 'PARAM.SFO'):
        p = os.path.join(ROOT, 'assets_ko', 'xmb', fn)
        if os.path.exists(p):
            pairs.append(('PSP_GAME/' + fn, p))
    isopatch.replace(ORIG_ISO, iso_out, pairs)
    log('done:', iso_out)


if __name__ == '__main__':
    main()
