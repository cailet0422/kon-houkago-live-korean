"""FMDX bind package (bind/*.bin) reader/writer.

Layout: 'FMDX' u32 total u32 count u32 unk, zero pad to 0x54,
then count * (name[0x80], u32 offset, u32 size, u32 0, u32 0), data 16-aligned.
`total` = sum(sizes) + a per-file constant delta which we preserve.
"""
import struct
import sys
import os

ENT = 0x90
HDR = 0x54


class FMDX:
    def __init__(self, data):
        assert data[:4] == b'FMDX'
        self.total, n, self.unk = struct.unpack_from('<III', data, 4)
        self.entries = []  # [name, bytes, extra(8 bytes)]
        for k in range(n):
            p = HDR + k * ENT
            name = data[p:p + 0x80].split(b'\0')[0].decode('ascii')
            off, size = struct.unpack_from('<II', data, p + 0x80)
            extra = data[p + 0x88:p + 0x90]
            self.entries.append([name, data[off:off + size], extra, off])
        self.delta = self.total - sum(len(e[1]) for e in self.entries)
        self.names = {e[0]: i for i, e in enumerate(self.entries)}

    def get(self, name):
        return self.entries[self.names[name]][1]

    def set(self, name, data):
        self.entries[self.names[name]][1] = bytes(data)

    def build(self):
        n = len(self.entries)
        hdr_end = HDR + n * ENT
        pos = (hdr_end + 15) // 16 * 16
        out = bytearray(pos)
        # keep original data order
        order = sorted(range(n), key=lambda i: self.entries[i][3])
        offs = {}
        body = bytearray()
        for i in order:
            offs[i] = pos + len(body)
            body += self.entries[i][1]
            body += b'\0' * ((-len(body)) % 16)
        out += body
        total = sum(len(e[1]) for e in self.entries) + self.delta
        struct.pack_into('<4sIII', out, 0, b'FMDX', total, n, self.unk)
        for k, (name, data, extra, _) in enumerate(self.entries):
            p = HDR + k * ENT
            nb = name.encode('ascii')
            out[p:p + len(nb)] = nb
            struct.pack_into('<II', out, p + 0x80, offs[k], len(data))
            out[p + 0x88:p + 0x90] = extra
        return bytes(out)


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'list':
        f = FMDX(open(a[2], 'rb').read())
        for name, data, _, off in f.entries:
            print(f'{off:8x} {len(data):8d} {name}')
    elif a[1] == 'unpack':
        f = FMDX(open(a[2], 'rb').read())
        for name, data, _, _ in f.entries:
            p = os.path.join(a[3], name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(data)
