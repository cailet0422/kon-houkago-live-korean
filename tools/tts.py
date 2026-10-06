"""Teatime event container (teatime_event/Event/TTS_Nm_*.tts).

Layout: script bytecode ... then a table of (u32 offset, u32 size, u32 type) triples that are
contiguous in the file:  type 0 = glyph atlas (UVR), type 1 = text records, type 2 = voice wav.
Text record = 0x40 bytes: u16 a, u16 b, 3 lines x 10 glyph indices (u16) into the event atlas.
"""
import struct


class TTS:
    def __init__(self, data):
        self.data = bytes(data)
        g = data.find(b'GBIX')
        self.table_off = None
        for p in range(0, g, 4):
            if struct.unpack_from('<I', data, p)[0] == g:
                self.table_off = p
                break
        assert self.table_off is not None
        self.entries = []
        q = self.table_off
        while q + 12 <= g:
            o, s, t = struct.unpack_from('<3I', data, q)
            if self.entries and o != self.entries[-1][0] + self.entries[-1][1]:
                break
            self.entries.append([o, s, t])
            q += 12
        assert self.entries[-1][0] + self.entries[-1][1] == len(data)

    def part(self, typ):
        for o, s, t in self.entries:
            if t == typ:
                return self.data[o:o + s]
        return None

    def build(self, replace):
        """replace: {type: new_bytes} for types 0/1 (first entry of that type)."""
        head = bytearray(self.data[:self.entries[0][0]])
        body = bytearray()
        pos = self.entries[0][0]
        done = set()
        new_entries = []
        for o, s, t in self.entries:
            blob = self.data[o:o + s]
            if t in replace and t not in done:
                blob = replace[t]
                done.add(t)
            new_entries.append((pos, len(blob), t))
            body += blob
            pos += len(blob)
        for k, (o, s, t) in enumerate(new_entries):
            struct.pack_into('<3I', head, self.table_off + 12 * k, o, s, t)
        return bytes(head + body)


def read_records(text):
    recs = []
    for i in range(len(text) // 0x40):
        v = struct.unpack_from('<32H', text, i * 0x40)
        recs.append((v[0], v[1], [list(v[2 + 10 * k:12 + 10 * k]) for k in range(3)]))
    return recs


def write_records(recs):
    out = bytearray()
    for a, b, lines in recs:
        flat = []
        for ln in lines:
            flat += list(ln) + [0] * (10 - len(ln))
        out += struct.pack('<32H', a, b, *flat[:30])
    return bytes(out)
