"""CRI CPK archive tool (TOC/GTOC/ETOC layout as used by K-On! Houkago Live!!).

usage:
  cpk.py list    <cpk>
  cpk.py extract <cpk> <outdir> [substring filter...]
  cpk.py rebuild <orig_cpk> <replace_dir> <out_cpk>
      Files found in replace_dir (same relative path as in the CPK) replace the
      originals and are stored uncompressed. Everything else is copied raw.
"""
import os
import struct
import sys

from utf_table import UTFTable, decrypt_utf

try:
    from crilayla_fast import decompress as _fast_decompress
except Exception:  # pragma: no cover
    _fast_decompress = None


# --------------------------------------------------------------- CRILAYLA
def crilayla_decompress(src):
    if _fast_decompress:
        return _fast_decompress(src)
    assert src[:8] == b'CRILAYLA'
    usize, hoff = struct.unpack_from('<II', src, 8)
    res = bytearray(usize + 0x100)
    res[:0x100] = src[0x10 + hoff:0x10 + hoff + 0x100]
    inp = 0x10 + hoff - 1
    out_end = 0x100 + usize - 1
    pool = 0
    left = 0
    done = 0

    def bits(n):
        nonlocal pool, left, inp
        v = 0
        while n:
            if left == 0:
                pool = src[inp]
                left = 8
                inp -= 1
            k = left if left < n else n
            v = (v << k) | ((pool >> (left - k)) & ((1 << k) - 1))
            left -= k
            n -= k
        return v

    vle = (2, 3, 5, 8)
    while done < usize:
        if bits(1):
            ref = out_end - done + bits(13) + 3
            ln = 3
            for lv in vle:
                x = bits(lv)
                ln += x
                if x != (1 << lv) - 1:
                    break
            else:
                while True:
                    x = bits(8)
                    ln += x
                    if x != 255:
                        break
            for _ in range(ln):
                res[out_end - done] = res[ref]
                ref -= 1
                done += 1
        else:
            res[out_end - done] = bits(8)
            done += 1
    return bytes(res)


# --------------------------------------------------------------- CPK
class CPK:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        h = self.f.read(0x10)
        assert h[:4] == b'CPK '
        sz = struct.unpack_from('<Q', h, 8)[0]
        self.hdr_raw = self.f.read(sz)
        self.header = UTFTable.parse(decrypt_utf(self.hdr_raw))
        hr = self.header.rows[0]
        self.toc_off = hr['TocOffset']
        self.content_off = hr['ContentOffset']
        self.toc = self._read_chunk(self.toc_off, b'TOC ')
        self.gtoc_raw = self._read_raw(hr['GtocOffset']) if hr.get('GtocOffset') else None
        self.etoc = self._read_chunk(hr['EtocOffset'], b'ETOC') if hr.get('EtocOffset') else None
        base = min(self.toc_off, self.content_off)
        self.base = base
        self.files = self.toc.rows

    def _read_raw(self, off):
        self.f.seek(off)
        h = self.f.read(0x10)
        sz = struct.unpack_from('<Q', h, 8)[0]
        return h + self.f.read(sz)

    def _read_chunk(self, off, magic):
        raw = self._read_raw(off)
        assert raw[:4] == magic, raw[:4]
        return UTFTable.parse(decrypt_utf(raw[0x10:]))

    @staticmethod
    def relpath(r):
        return (r['DirName'] + '/' if r['DirName'] else '') + r['FileName']

    def read_raw(self, r):
        self.f.seek(self.base + r['FileOffset'])
        return self.f.read(r['FileSize'])

    def read(self, r):
        d = self.read_raw(r)
        if r['ExtractSize'] != r['FileSize'] and d[:8] == b'CRILAYLA':
            d = crilayla_decompress(d)
        return d


def cmd_list(cpk):
    c = CPK(cpk)
    for r in sorted(c.files, key=lambda r: r['FileOffset']):
        print(f"{r['ID']:5d} {r['FileOffset'] + c.base:10d} {r['FileSize']:9d} {r['ExtractSize']:9d} {CPK.relpath(r)}")


def cmd_extract(cpk, outdir, filters):
    c = CPK(cpk)
    n = 0
    for r in c.files:
        p = CPK.relpath(r)
        if filters and not any(f in p for f in filters):
            continue
        if r['FileName'] == 'padding.bin':
            continue
        dst = os.path.join(outdir, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as o:
            o.write(c.read(r))
        n += 1
    print(f'extracted {n} files')


def _chunk(magic, table_bytes):
    return magic + struct.pack('<IQ', 0xFF, len(table_bytes)) + table_bytes


def _compress_many(paths):
    """{path: (stored_bytes, extract_size)} using tools/crilayla_c/crilayla.exe (C# build)."""
    import subprocess
    import tempfile
    exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crilayla_c', 'crilayla.exe')
    res = {}
    tmp = tempfile.mkdtemp(prefix='cri_')
    args, outs = [], {}
    for k, p in enumerate(paths):
        o = os.path.join(tmp, f'{k}.cri')
        args += [p, o]
        outs[p] = o
    for i in range(0, len(args), 200):
        subprocess.run([exe] + args[i:i + 200], check=True, capture_output=True)
    for p in paths:
        raw = open(p, 'rb').read()
        o = outs[p]
        if os.path.exists(o):
            c = open(o, 'rb').read()
            assert crilayla_decompress(c) == raw, 'CRILAYLA roundtrip failed: ' + p
            res[p] = (c, len(raw))
            os.remove(o)
        else:
            res[p] = (raw, len(raw))
    os.rmdir(tmp)
    return res


def cmd_rebuild(orig, repdir, out):
    """Rebuild CPK keeping file order/IDs; replaced files stored uncompressed.

    The huge 'padding.bin' (UMD outer-track filler) is shrunk by however much
    the content grew so the disc image size stays roughly the same.
    """
    c = CPK(orig)
    hr = c.header.rows[0]
    align = hr['Align']
    order = sorted(c.files, key=lambda r: r['FileOffset'])
    repl = {}
    for r in order:
        p = os.path.join(repdir, CPK.relpath(r))
        if os.path.isfile(p):
            repl[id(r)] = p
    # store replaced files CRILAYLA-compressed like the original (real hardware loads them the
    # same way as untouched files); fall back to raw when compression does not help
    comp = _compress_many([repl[id(r)] for r in order if id(r) in repl])
    # measure growth to shrink padding
    grow = 0
    for r in order:
        if id(r) in repl:
            ns = len(comp[repl[id(r)]][0])
            grow += ((ns + align - 1) // align - (r['FileSize'] + align - 1) // align) * align
    pad_row = next((r for r in order if r['FileName'] == 'padding.bin'), None)

    toc_bytes_len = len(_chunk(b'TOC ', c.toc.build()))
    gtoc_len = len(c.gtoc_raw) if c.gtoc_raw else 0
    toc_off = c.toc_off
    gtoc_off = hr['GtocOffset']
    content_off = c.content_off
    assert toc_off + toc_bytes_len <= gtoc_off and gtoc_off + gtoc_len <= content_off

    with open(out, 'wb') as o:
        c.f.seek(0)
        o.write(c.f.read(content_off))  # keep original header-area bytes (hash etc.)
        pos = content_off
        for r in order:
            if r is pad_row:
                newsize = max(align, r['FileSize'] - max(grow, 0))
                newsize = (newsize // align) * align
                r['FileOffset'] = pos - c.base
                r['FileSize'] = r['ExtractSize'] = newsize
                o.write(b'\0' * newsize)
                pos += newsize
                continue
            if id(r) in repl:
                data, esize = comp[repl[id(r)]]
                r['FileSize'] = len(data)
                r['ExtractSize'] = esize
            else:
                data = c.read_raw(r)
            r['FileOffset'] = pos - c.base
            o.write(data)
            pos += len(data)
            padn = (-pos) % align
            o.write(b'\0' * padn)
            pos += padn
        content_size = pos - content_off
        etoc_off = pos
        etoc = _chunk(b'ETOC', c.etoc.build())
        o.write(etoc)
        pos += len(etoc)
        # headers
        hr['ContentSize'] = content_size
        hr['EtocOffset'] = etoc_off
        hr['EtocSize'] = len(etoc)
        toc = _chunk(b'TOC ', c.toc.build())
        assert len(toc) <= gtoc_off - toc_off
        hr['TocSize'] = len(toc)
        hdr = c.header.build()
        o.seek(0)
        o.write(b'CPK ' + struct.pack('<IQ', 0xFF, len(hdr)) + hdr)
        o.seek(toc_off - 6)
        o.write(b'(c)CRI')
        o.seek(toc_off)
        o.write(toc)
        if c.gtoc_raw:
            o.seek(gtoc_off)
            o.write(c.gtoc_raw)
    print(f'rebuilt {out}: {len(repl)} files replaced, growth {grow} bytes')


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'list':
        cmd_list(a[2])
    elif a[1] == 'extract':
        cmd_extract(a[2], a[3], a[4:])
    elif a[1] == 'rebuild':
        cmd_rebuild(a[2], a[3], a[4])
