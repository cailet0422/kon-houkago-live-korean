"""CRI @UTF table reader/writer (big-endian)."""
import struct

T_U8, T_S8, T_U16, T_S16, T_U32, T_S32, T_U64, T_S64, T_F32, T_F64, T_STR, T_DATA = range(12)
S_ZERO, S_CONST, S_ROW, S_CONST2 = 0x10, 0x30, 0x50, 0x70

_FMT = {T_U8: '>B', T_S8: '>b', T_U16: '>H', T_S16: '>h', T_U32: '>I', T_S32: '>i',
        T_U64: '>Q', T_S64: '>q', T_F32: '>f', T_F64: '>d'}


class Column:
    def __init__(self, name, storage, typ, const=None):
        self.name, self.storage, self.typ, self.const = name, storage, typ, const

    def __repr__(self):
        return f"Column({self.name!r}, st={self.storage:#x}, t={self.typ}, c={self.const!r})"


class UTFTable:
    def __init__(self):
        self.name = ''
        self.columns = []
        self.rows = []  # list of dict
        self.version = 1

    # ------------------------------------------------------------------ read
    @classmethod
    def parse(cls, buf, off=0):
        t = cls()
        assert buf[off:off + 4] == b'@UTF', buf[off:off + 4]
        base = off + 8
        (size, ver, rows_off, str_off, data_off, name_off, ncols, row_w, nrows) = struct.unpack_from(
            '>IHHIIIHHI', buf, off + 4)
        t.version = ver
        strtab = buf[base + str_off: base + data_off]

        def rstr(o):
            e = strtab.index(b'\0', o)
            return strtab[o:e].decode('cp932')

        t.name = rstr(name_off)
        p = off + 0x20

        def read_val(typ, p):
            if typ in _FMT:
                f = _FMT[typ]
                return struct.unpack_from(f, buf, p)[0], p + struct.calcsize(f)
            if typ == T_STR:
                so = struct.unpack_from('>I', buf, p)[0]
                return rstr(so), p + 4
            if typ == T_DATA:
                do, dl = struct.unpack_from('>II', buf, p)
                return bytes(buf[base + data_off + do: base + data_off + do + dl]), p + 8
            raise ValueError(typ)

        for _ in range(ncols):
            flag = buf[p]
            nameo = struct.unpack_from('>I', buf, p + 1)[0]
            p += 5
            st, ty = flag & 0xF0, flag & 0x0F
            c = Column(rstr(nameo), st, ty)
            if st in (S_CONST, S_CONST2):
                c.const, p = read_val(ty, p)
            t.columns.append(c)
        p = base + rows_off
        for _ in range(nrows):
            row = {}
            q = p
            for c in t.columns:
                if c.storage == S_ZERO:
                    row[c.name] = None
                elif c.storage in (S_CONST, S_CONST2):
                    row[c.name] = c.const
                else:
                    row[c.name], q = read_val(c.typ, q)
            t.rows.append(row)
            p += row_w
        return t

    # ----------------------------------------------------------------- write
    def build(self):
        strings = bytearray()
        strmap = {}

        def addstr(s):
            if s not in strmap:
                strmap[s] = len(strings)
                strings.extend(s.encode('cp932') + b'\0')
            return strmap[s]

        data = bytearray()

        addstr('<NULL>')
        name_off = addstr(self.name)

        def enc(typ, v):
            if typ in _FMT:
                return struct.pack(_FMT[typ], v)
            if typ == T_STR:
                return struct.pack('>I', addstr(v))
            if typ == T_DATA:
                if v is None or len(v) == 0:
                    return struct.pack('>II', 0, 0)
                o = len(data)
                data.extend(v)
                return struct.pack('>II', o, len(v))
            raise ValueError(typ)

        colbuf = bytearray()
        for c in self.columns:
            colbuf.append(c.storage | c.typ)
            colbuf += struct.pack('>I', addstr(c.name))
            if c.storage in (S_CONST, S_CONST2):
                colbuf += enc(c.typ, c.const)
        rowbuf = bytearray()
        row_w = 0
        for i, r in enumerate(self.rows):
            rb = bytearray()
            for c in self.columns:
                if c.storage == S_ROW:
                    rb += enc(c.typ, r[c.name])
            if i == 0:
                row_w = len(rb)
            rowbuf += rb
        rows_off = 0x18 + len(colbuf)
        str_off = rows_off + len(rowbuf)
        data_off = str_off + len(strings)
        # align data to 8
        pad = (-(data_off + 8)) % 8
        strings += b'\0' * pad
        data_off = str_off + len(strings)
        body = struct.pack('>HHIIIHHI', self.version, rows_off, str_off, data_off, name_off,
                           len(self.columns), row_w, len(self.rows)) + colbuf + rowbuf + strings + data
        size = len(body)
        pad = (-size) % 8
        body += b'\0' * pad
        return b'@UTF' + struct.pack('>I', len(body)) + body


def decrypt_utf(buf):
    """@UTF tables in CPK may be XOR-obfuscated."""
    if buf[:4] == b'@UTF':
        return bytes(buf)
    out = bytearray(len(buf))
    m, t = 0x655f, 0x4115
    for i, b in enumerate(buf):
        out[i] = b ^ (m & 0xFF)
        m = (m * t) & 0xFFFFFFFF
    return bytes(out)
