"""Helpers to disassemble the decrypted K-On EBOOT (PRX, vaddr = file_off - 0xA0)."""
import struct, capstone
BASE = 0xA0
D = open('D:/newjakup/work/eboot/EBOOT_dec.BIN', 'rb').read()
TEXT_END = 0x1f7258
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)

def words():
    return struct.unpack_from('<%dI' % (TEXT_END // 4), D, BASE)

def find_addr_refs(target):
    """find lui/addiu(or ori/lw/sw...) pairs forming target address"""
    w = words()
    hi = (target + 0x8000) >> 16
    lo = target & 0xffff
    res = []
    for i, x in enumerate(w):
        if (x >> 26) == 0x0f and (x & 0xffff) == hi:
            rt = (x >> 16) & 31
            for j in range(i + 1, min(i + 40, len(w))):
                y = w[j]
                op = y >> 26
                if op in (0x09, 0x23, 0x21, 0x25, 0x2b, 0x29, 0x28, 0x20, 0x24, 0x0d) and ((y >> 21) & 31) == rt and (y & 0xffff) == lo:
                    res.append((i * 4, j * 4))
                    break
    return res

def dis(addr, n=40):
    code = D[BASE + addr: BASE + addr + n * 4]
    for ins in md.disasm(code, addr):
        print(f'{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}')
