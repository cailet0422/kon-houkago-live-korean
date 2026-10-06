"""Build the block-delta patch used by the GUI patcher (patcher/KonKoPatcher.exe).

Format (little endian):
  magic   b'KONKO01\\0'
  u64 orig_size, 20B orig_sha1, u64 new_size, 20B new_sha1, u32 block, u32 n_ops
  ops: (u8 kind, u32 count, u32 arg)   kind 0 = copy `count` blocks from original block `arg`
                                       kind 1 = take `count` blocks from the data stream
                                       kind 2 = `count` zero blocks
  rest: raw-deflate stream of all data blocks, in order
The last block of the new image may be short; its length is implied by new_size.
"""
import hashlib
import os
import struct
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORIG = os.path.join(ROOT, 'k-on!_houkago_live!!_(japan)', 'K-On! Houkago Live!! (Japan).iso')
NEW = os.path.join(ROOT, 'build', 'K-On_Houkago_Live_KO.iso')
OUT = os.path.join(ROOT, 'patcher', 'kon_ko.patch')
B = 2048


def sha1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''):
            h.update(b)
    return h.digest()


def main():
    idx = {}
    with open(ORIG, 'rb') as f:
        i = 0
        for b in iter(lambda: f.read(B), b''):
            if len(b) == B:
                idx.setdefault(hashlib.sha1(b).digest(), i)
            i += 1
    ops = []

    def add(kind, arg):
        if ops:
            k, c, a = ops[-1]
            if k == kind and (kind != 0 or a + c == arg):
                ops[-1] = (k, c + 1, a)
                return
        ops.append((kind, 1, arg))
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    tmp = OUT + '.data'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(NEW, 'rb') as f, open(tmp, 'wb') as d:
        for b in iter(lambda: f.read(B), b''):
            if len(b) == B and not any(b):
                add(2, 0)
                continue
            j = idx.get(hashlib.sha1(b).digest()) if len(b) == B else None
            if j is not None:
                add(0, j)
            else:
                add(1, 0)
                d.write(comp.compress(b))
        d.write(comp.flush())
    with open(OUT, 'wb') as o:
        o.write(b'KONKO01\0')
        o.write(struct.pack('<Q', os.path.getsize(ORIG)) + sha1(ORIG))
        o.write(struct.pack('<Q', os.path.getsize(NEW)) + sha1(NEW))
        o.write(struct.pack('<II', B, len(ops)))
        for k, c, a in ops:
            o.write(struct.pack('<BII', k, c, a))
        with open(tmp, 'rb') as d:
            for chunk in iter(lambda: d.read(1 << 24), b''):
                o.write(chunk)
    os.remove(tmp)
    print('ops', len(ops), 'patch', os.path.getsize(OUT), 'bytes')


def apply(orig, patch, out):
    """Reference implementation (used to verify the patch)."""
    with open(patch, 'rb') as p:
        assert p.read(8) == b'KONKO01\0'
        osz, = struct.unpack('<Q', p.read(8)); p.read(20)
        nsz, = struct.unpack('<Q', p.read(8)); nsha = p.read(20)
        blk, nops = struct.unpack('<II', p.read(8))
        ops = [struct.unpack('<BII', p.read(9)) for _ in range(nops)]
        dec = zlib.decompressobj(-15)
        pending = b''
        h = hashlib.sha1()
        written = 0
        with open(orig, 'rb') as s, open(out, 'wb') as o:
            for k, c, a in ops:
                for n in range(c):
                    want = min(blk, nsz - written)
                    if k == 0:
                        s.seek((a + n) * blk)
                        b = s.read(want)
                    elif k == 2:
                        b = bytes(want)
                    else:
                        while len(pending) < want:
                            pending += dec.decompress(p.read(1 << 20))
                        b, pending = pending[:want], pending[want:]
                    o.write(b)
                    h.update(b)
                    written += len(b)
        assert written == nsz and h.digest() == nsha, 'verify failed'


if __name__ == '__main__':
    main()
    t = os.path.join(ROOT, 'work', 'verify_patch.iso')
    apply(ORIG, OUT, t)
    os.remove(t)
    print('verified')
