"""Minimal PARAM.SFO editor: sfo.py <in> <out> KEY=value ..."""
import struct
import sys


def read(data):
    magic, ver, kt, dt, n = struct.unpack_from('<4sIIII', data, 0)
    ents = []
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', data, 20 + i * 16)
        key = data[kt + ko:data.index(b'\0', kt + ko)].decode()
        ents.append((key, fmt, ln, mx, dt + do))
    return ents


def set_str(data, key, value):
    data = bytearray(data)
    for i, (k, fmt, ln, mx, off) in enumerate(read(data)):
        if k == key:
            b = value.encode('utf-8') + b'\0'
            assert len(b) <= mx, (key, len(b), mx)
            data[off:off + mx] = b + b'\0' * (mx - len(b))
            struct.pack_into('<I', data, 20 + i * 16 + 4, len(b))
            return bytes(data)
    raise KeyError(key)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for kv in sys.argv[3:]:
        k, v = kv.split('=', 1)
        d = set_str(d, k, v)
    open(sys.argv[2], 'wb').write(d)
    for e in read(d):
        print(e[:4])
