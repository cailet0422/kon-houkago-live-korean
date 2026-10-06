"""Patch helpers for the decrypted K-On EBOOT (PRX; vaddr = file offset - 0xA0)."""
import struct

BASE = 0xA0
TBL16 = 0x2e7a88   # u16[1024]  glyph index -> UTF-16 char
TBL8 = 0x2e6a88    # u32[1024]  glyph index -> ptr to UTF-8 string (relocated), 0 = unused
NGLYPH = 1024


class Eboot:
    def __init__(self, path):
        self.d = bytearray(open(path, 'rb').read())
        ptrs = self.utf8_ptrs()
        tg = sorted(set(p for p in ptrs if p))
        self.slot_cap = {}
        for a, b in zip(tg, tg[1:] + [tg[-1] + 4]):
            self.slot_cap[a] = b - a

    def u32(self, va):
        return struct.unpack_from('<I', self.d, va + BASE)[0]

    def utf8_ptrs(self):
        return list(struct.unpack_from('<%dI' % NGLYPH, self.d, TBL8 + BASE))

    def glyph_char16(self, i):
        return chr(struct.unpack_from('<H', self.d, TBL16 + BASE + 2 * i)[0])

    def glyph_utf8(self, i):
        p = self.utf8_ptrs()[i]
        if not p:
            return None
        o = p + BASE
        return bytes(self.d[o:self.d.index(b'\0', o)]).decode('utf-8', 'replace')

    def set_glyph(self, i, ch, utf16=True):
        """Map glyph index i to character ch in the lookup tables (UTF-16 optional)."""
        if utf16:
            struct.pack_into('<H', self.d, TBL16 + BASE + 2 * i, ord(ch) if ch else 0)
        p = self.utf8_ptrs()[i]
        if p:
            b = ch.encode('utf-8') + b'\0' if ch else b'\0'
            cap = self.slot_cap[p]
            assert len(b) <= cap, (i, ch, cap)
            o = p + BASE
            self.d[o:o + cap] = b + b'\0' * (cap - len(b))

    def save(self, path):
        open(path, 'wb').write(self.d)
