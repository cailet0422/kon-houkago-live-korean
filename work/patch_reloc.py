p = 'D:/newjakup/tools/build.py'
s = open(p, encoding='utf-8').read()
a = s.index("        self.eb.d[self.cur:self.cur + len(data) + 1] = data + b'\\x00'")
b = s.index("# ------------------------------------------------------------------ teatime events")
new = r'''        self.eb.d[self.cur:self.cur + len(data) + 1] = data + b'\x00'
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


'''
s = s[:a] + new + s[b:]
s = s.replace("        self.moved = 0\n\n    def free_left", "        self.moved = 0\n        self.freed = []\n\n    def free_left")
old2 = """            if reloc.relocate(int(o['off'], 16), b):
                continue
            log(f"WARN eboot {o['off']} too long {len(b)}>{o['cap']}: {t!r}")
            bad += 1
            continue"""
assert old2 in s
s = s.replace(old2, """            if reloc.relocate(int(o['off'], 16), b):
                continue
            pending.append((o, b, t))
            continue""")
s = s.replace("    reloc = EbootRelocator(eb)\n    bad = 0", "    reloc = EbootRelocator(eb)\n    bad = 0\n    pending = []")
s = s.replace("    log(f'eboot strings written ({bad} skipped", """    for o, b, t in pending:
        if not reloc.relocate_code(int(o['off'], 16), b):
            log(f"WARN eboot {o['off']} too long {len(b)}>{o['cap']}: {t!r}")
            bad += 1
    log(f'eboot strings written ({bad} skipped""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
