"""Minimal ISO9660 in-place file replacer for PSP UMD images.

usage:
  isopatch.py list <iso>
  isopatch.py replace <in_iso> <out_iso> <iso_path>=<local_file> [...]

A replacement file is written at its original LBA when it fits in the space
up to the next extent; otherwise it is appended at the end of the image.
Directory records (size / LBA, both-endian) are updated in place.
Paths are like PSP_GAME/USRDIR/std.cpk (case-insensitive).
"""
import os
import shutil
import struct
import sys

SECTOR = 2048


def read_dir(f, lba, size, prefix=''):
    out = []
    f.seek(lba * SECTOR)
    data = f.read(size)
    pos = 0
    while pos < len(data):
        ln = data[pos]
        if ln == 0:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + ln]
        ext = struct.unpack_from('<I', rec, 2)[0]
        dlen = struct.unpack_from('<I', rec, 10)[0]
        flags = rec[25]
        nlen = rec[32]
        name = rec[33:33 + nlen]
        rec_off = lba * SECTOR + pos
        if name not in (b'\0', b'\1'):
            nm = name.decode('ascii', 'replace').split(';')[0]
            path = prefix + nm
            if flags & 2:
                out.append((path + '/', ext, dlen, rec_off, True))
                out += read_dir(f, ext, dlen, path + '/')
            else:
                out.append((path, ext, dlen, rec_off, False))
        pos += ln
    return out


def list_iso(path):
    with open(path, 'rb') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        assert pvd[1:6] == b'CD001'
        root = pvd[156:156 + 34]
        rlba = struct.unpack_from('<I', root, 2)[0]
        rsize = struct.unpack_from('<I', root, 10)[0]
        vol_blocks = struct.unpack_from('<I', pvd, 80)[0]
        return read_dir(f, rlba, rsize), vol_blocks


def replace(in_iso, out_iso, pairs):
    entries, vol_blocks = list_iso(in_iso)
    files = [e for e in entries if not e[4]]
    if os.path.abspath(in_iso) != os.path.abspath(out_iso):
        shutil.copyfile(in_iso, out_iso)
    # extents sorted to know the free room after each file
    # files being emptied free their extents for the others
    emptied = {k.lower() for k, v in pairs if not v}
    all_ext = sorted((e[1], e[1] + (e[2] + SECTOR - 1) // SECTOR) for e in entries
                     if e[0].lower() not in emptied)
    total_blocks = os.path.getsize(out_iso) // SECTOR
    with open(out_iso, 'r+b') as f:
        end_block = total_blocks
        for iso_path, local in pairs:
            ent = next((e for e in files if e[0].lower() == iso_path.lower()), None)
            assert ent, iso_path
            _, lba, size, rec_off, _ = ent
            nsize = os.path.getsize(local) if local else 0
            nxt = min([s for s, _ in all_ext if s > lba] + [total_blocks])
            room = (nxt - lba) * SECTOR
            if nsize <= room:
                new_lba = lba
            else:
                new_lba = end_block
                end_block += (nsize + SECTOR - 1) // SECTOR
                print(f'  {iso_path}: {nsize} > room {room}, appended at LBA {new_lba}')
            if local:
                f.seek(new_lba * SECTOR)
                with open(local, 'rb') as src:
                    shutil.copyfileobj(src, f, 16 << 20)
                pad = (-nsize) % SECTOR
                f.write(b'\0' * pad)
                # zero leftover old data inside the old slot (keeps xdelta small & clean)
                if new_lba == lba and nsize < size:
                    left = ((size + SECTOR - 1) // SECTOR * SECTOR) - ((nsize + SECTOR - 1) // SECTOR * SECTOR)
                    f.write(b'\0' * max(0, left))
            f.seek(rec_off + 2)
            f.write(struct.pack('<I', new_lba) + struct.pack('>I', new_lba))
            f.write(struct.pack('<I', nsize) + struct.pack('>I', nsize))
            print(f'replaced {iso_path}: lba {lba}->{new_lba} size {size}->{nsize}')
        if end_block > total_blocks:
            f.truncate(end_block * SECTOR)
            f.seek(16 * SECTOR + 80)
            f.write(struct.pack('<I', end_block) + struct.pack('>I', end_block))


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'list':
        ents, vb = list_iso(a[2])
        print('volume blocks', vb)
        for p, lba, size, _, isdir in sorted(ents, key=lambda e: e[1]):
            print(f'{lba:8d} {size:11d} {p}')
    elif a[1] == 'replace':
        pairs = []
        for s in a[4:]:
            k, v = s.split('=', 1)
            pairs.append((k, v or None))
        replace(a[2], a[3], pairs)
