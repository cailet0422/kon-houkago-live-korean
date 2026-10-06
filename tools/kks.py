"""KKS text (font/KKS_*.bin) decode/encode. Record = u16 header + 180 u16 glyph indices."""
import struct, sys, os, glob, json

REC = 362

def load_tbl(path):
    t = {}
    for l in open(path, encoding='utf-8'):
        l = l.rstrip('\n')
        if '=' in l:
            k, v = l.split('=', 1)
            t[int(k, 16)] = v
    return t

def rec_size(d):
    """Record size = 2 + 2*5*line_width. Detected from the atlas listing (record 1 starts with glyph 0x20)."""
    v = struct.unpack('<%dH' % (len(d) // 2), d)
    rs = (v.index(0x20) - 1) * 2
    assert len(d) % rs == 0 and (rs - 2) % 10 == 0, (len(d), rs)
    return rs

def read_kks(path):
    d = open(path, 'rb').read()
    rs = rec_size(d)
    n = (rs - 2) // 2
    recs = []
    for i in range(len(d) // rs):
        v = struct.unpack_from('<%dH' % (n + 1), d, i * rs)
        recs.append((v[0], list(v[1:])))
    return recs

def decode(glyphs, tbl):
    # trailing zeros trimmed; interior zeros shown as '\n' candidates -> use {0}
    g = list(glyphs)
    while g and g[-1] == 0:
        g.pop()
    return ''.join(tbl.get(x, '{%d}' % x) if x else '{0}' for x in g)

if __name__ == '__main__':
    tbl = load_tbl(os.path.join(os.path.dirname(__file__), '../tables/sys_runtime.tbl'))
    for p in sorted(glob.glob(sys.argv[1])):
        recs = read_kks(p)
        print('#', os.path.basename(p), len(recs))
        for i, (h, g) in enumerate(recs):
            s = decode(g, tbl)
            if s:
                print(f'{i:3d} h={h} {s}')


def record_lines(glyphs, width, tbl):
    """Split a record into its (up to 5) lines of text."""
    lines = []
    for k in range(len(glyphs) // width):
        seg = list(glyphs[k * width:(k + 1) * width])
        while seg and seg[-1] == 0:
            seg.pop()
        lines.append(''.join(tbl.get(x, '{%d}' % x) if x else '{0}' for x in seg))
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def wrap_text(text, width):
    """Wrap Korean text: honour explicit \n, then break at spaces to fit `width` glyphs."""
    out = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split(' '):
            cand = word if not cur else cur + ' ' + word
            if len(cand) <= width:
                cur = cand
                continue
            if cur:
                out.append(cur)
            while len(word) > width:
                out.append(word[:width])
                word = word[width:]
            cur = word
        out.append(cur)
    return out


def encode_record(text, width, charmap, nlines=5):
    lines = wrap_text(text, width)
    if len(lines) > nlines:
        raise ValueError(f'too many lines ({len(lines)}>{nlines}) for width {width}: {text!r}')
    g = []
    for ln in lines:
        seg = [charmap[c] for c in ln]
        g += seg + [0] * (width - len(seg))
    g += [0] * (width * nlines - len(g))
    return len(lines) if text else 1, g


def write_kks(path_out, recs):
    n = len(recs[0][1])
    out = bytearray()
    for h, g in recs:
        out += struct.pack('<%dH' % (n + 1), h, *g)
    open(path_out, 'wb').write(out)
