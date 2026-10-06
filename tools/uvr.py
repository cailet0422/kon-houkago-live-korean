"""Sega UVR (PSP) texture <-> PNG.

Header: [GBIX] 'UVRT' u32 size, u8 fmt0, u8 fmt1, u16 0, u16 w, u16 h, then body.
fmt1 low nibble (data format):
  0xC / 0xA : 8bpp palettised (256 entries)      0x8 / 0x6 : 4bpp palettised (16 entries)
  0x0       : direct colour                     0x1       : direct colour + mipmaps
fmt0 (pixel format of palette / direct pixels): 0=RGB565 1=RGBA5551 2=RGBA4444 3=RGBA8888,
  0xA = 4-bit intensity (direct), 0xC = 8-bit intensity (direct).
Pixel data is PSP-swizzled (16-byte x 8-row blocks).

usage:
  uvr.py topng <in.uvr> <out.png>
  uvr.py frompng <in.png> <template.uvr> <out.uvr>   (keeps header/format of template)
"""
import struct
import sys

import numpy as np
from PIL import Image


def _unpack16(v, fmt):
    v = v.astype(np.uint32)
    if fmt == 0:
        r, g, b, a = (v & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, ((v >> 11) & 31) * 255 // 31, np.full_like(v, 255)
    elif fmt == 1:
        r, g, b, a = (v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31, ((v >> 15) & 1) * 255
    else:
        r, g, b, a = (v & 15) * 17, ((v >> 4) & 15) * 17, ((v >> 8) & 15) * 17, ((v >> 12) & 15) * 17
    return np.stack([r, g, b, a], -1).astype(np.uint8)


def _pack16(rgba, fmt):
    c = rgba.astype(np.uint32)
    r, g, b, a = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    if fmt == 0:
        v = (r * 31 // 255) | ((g * 63 // 255) << 5) | ((b * 31 // 255) << 11)
    elif fmt == 1:
        v = (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10) | ((a >= 128).astype(np.uint32) << 15)
    else:
        v = ((r + 8) // 17) | (((g + 8) // 17) << 4) | (((b + 8) // 17) << 8) | (((a + 8) // 17) << 12)
    return v.astype(np.uint16)


class UVR:
    def __init__(self, data):
        self.raw = bytes(data)
        p = 0
        if data[:4] == b'GBIX':
            gl = struct.unpack_from('<I', data, 4)[0]
            p = 8 + gl
        assert data[p:p + 4] == b'UVRT', data[p:p + 4]
        self.hdr_off = p
        self.chunk_size = struct.unpack_from('<I', data, p + 4)[0]
        self.fmt0, self.fmt1 = data[p + 8], data[p + 9]
        self.w, self.h = struct.unpack_from('<HH', data, p + 12)
        self.body_off = p + 16
        df = self.fmt1 & 0x0F
        self.direct = df in (0x0, 0x1)
        self.dxt = self.direct and self.fmt0 in (0xA, 0xB, 0xC)
        if self.direct:
            self.ncol = 0
            self.bpp = {3: 32, 0: 16, 1: 16, 2: 16, 0xA: 4, 0xB: 8, 0xC: 8}[self.fmt0]
            self.pal_bytes = 0
        else:
            self.bpp = 8 if df in (0xC, 0xA, 0xE) else 4
            self.ncol = 256 if self.bpp == 8 else 16
            self.pal_entry = 4 if self.fmt0 == 3 else 2
            self.pal_bytes = self.ncol * self.pal_entry
        pb = self.body_off
        if self.ncol:
            if self.pal_entry == 4:
                self.palette = np.frombuffer(data, np.uint8, self.ncol * 4, pb).reshape(self.ncol, 4).copy()
            else:
                self.palette = _unpack16(np.frombuffer(data, '<u2', self.ncol, pb), self.fmt0)
        else:
            self.palette = None
        self.pix_off = pb + self.pal_bytes
        npx = self.w * self.h * self.bpp // 8
        self.pixraw = np.frombuffer(data, np.uint8, npx, self.pix_off).copy()

    # --- swizzle helpers (PSP: blocks of 16 bytes x 8 rows)
    @staticmethod
    def unswizzle(buf, width_bytes, height):
        bw = width_bytes // 16
        bh = (height + 7) // 8
        a = buf[:width_bytes * height].reshape(bh, bw, 8, 16)
        return a.transpose(0, 2, 1, 3).reshape(height, width_bytes)

    @staticmethod
    def swizzle(img, width_bytes, height):
        bw = width_bytes // 16
        bh = height // 8
        a = img.reshape(bh, 8, bw, 16).transpose(0, 2, 1, 3)
        return a.reshape(-1)

    def _rows(self, swizzled=True):
        wb = self.w * self.bpp // 8
        buf = self.pixraw
        if swizzled and wb >= 16 and self.h >= 8:
            return self.unswizzle(buf, wb, self.h)
        return buf.reshape(self.h, wb)

    def indices(self, swizzled=True):
        buf = self._rows(swizzled)
        if self.bpp == 4:
            lo = buf & 0x0F
            hi = buf >> 4
            buf = np.stack([lo, hi], axis=-1).reshape(self.h, self.w)
        return buf

    def to_image(self, swizzled=True):
        if self.dxt:
            return Image.fromarray(dxt_decode(self.pixraw, self.w, self.h, self.fmt0), 'RGBA')
        if not self.direct:
            return Image.fromarray(self.palette[self.indices(swizzled)], 'RGBA')
        rows = self._rows(swizzled)
        if self.bpp == 32:
            return Image.fromarray(rows.reshape(self.h, self.w, 4), 'RGBA')
        if self.bpp == 16:
            return Image.fromarray(_unpack16(rows.view('<u2').reshape(self.h, self.w), self.fmt0), 'RGBA')
        v = self.indices(swizzled) if self.bpp == 4 else rows
        a = (v.astype(np.uint16) * (17 if self.bpp == 4 else 1)).astype(np.uint8)
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = 255
        out[..., 3] = a
        return Image.fromarray(out, 'RGBA')

    def _pack_rows(self, rows, swizzled):
        wb = self.w * self.bpp // 8
        if swizzled and wb >= 16 and self.h >= 8:
            return self.swizzle(rows, wb, self.h)
        return rows.reshape(-1)

    def rebuild(self, idx, palette=None, swizzled=True):
        """Palettised: idx HxW indices + RGBA palette (n x 4)."""
        pal = self.palette if palette is None else palette
        assert idx.shape == (self.h, self.w)
        if self.bpp == 4:
            a = idx.reshape(self.h, self.w // 2, 2)
            rows = ((a[..., 0] & 0xF) | ((a[..., 1] & 0xF) << 4)).astype(np.uint8)
        else:
            rows = idx.astype(np.uint8)
        out = bytearray(self.raw[:self.body_off])
        if self.pal_entry == 4:
            out += pal.astype(np.uint8).tobytes()
        else:
            out += _pack16(pal, self.fmt0).tobytes()
        out += self._pack_rows(rows, swizzled).tobytes()
        out += self.raw[self.pix_off + len(self.pixraw):]
        return bytes(out)

    def from_image(self, img, swizzled=True):
        """Encode an RGBA image (same size) in this texture's own format."""
        img = img.convert('RGBA')
        assert img.size == (self.w, self.h), (img.size, self.w, self.h)
        if self.dxt:
            if self.fmt0 != 0xA:
                raise NotImplementedError('DXT3/5 encode')
            out = bytearray(self.raw[:self.pix_off])
            out += dxt1_encode(np.asarray(img), self.w, self.h)
            out += self.raw[self.pix_off + len(self.pixraw):]
            return bytes(out)
        if not self.direct:
            idx, pal = build_palette(img, self.ncol)
            return self.rebuild(idx, pal, swizzled)
        a = np.asarray(img)
        if self.bpp == 32:
            rows = a.reshape(self.h, self.w * 4)
        elif self.bpp == 16:
            rows = _pack16(a, self.fmt0).view(np.uint8).reshape(self.h, self.w * 2)
        else:
            lum = a[..., 3].astype(np.uint16)
            if self.bpp == 4:
                v = ((lum + 8) // 17).astype(np.uint8).reshape(self.h, self.w // 2, 2)
                rows = (v[..., 0] | (v[..., 1] << 4)).astype(np.uint8)
            else:
                rows = lum.astype(np.uint8)
        out = bytearray(self.raw[:self.pix_off])
        out += self._pack_rows(rows, swizzled).tobytes()
        out += self.raw[self.pix_off + len(self.pixraw):]
        return bytes(out)


def _c565(c):
    c = c.astype(np.int32)
    return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], -1)


def dxt_decode(raw, w, h, fmt):
    """PSP DXT: colour block = 4 index bytes then two RGB565 colours (0xA=DXT1, 0xB=DXT3, 0xC=DXT5)."""
    bs = 8 if fmt == 0xA else 16
    nb = (w // 4) * (h // 4)
    b = np.frombuffer(bytes(raw[:nb * bs]), np.uint8).reshape(nb, bs)
    cb = b[:, :8]
    lines = cb[:, 0:4].astype(np.uint32)
    c1 = cb[:, 4].astype(np.uint32) | (cb[:, 5].astype(np.uint32) << 8)
    c2 = cb[:, 6].astype(np.uint32) | (cb[:, 7].astype(np.uint32) << 8)
    a, bb = _c565(c1), _c565(c2)
    four = (c1 > c2) | (fmt != 0xA)
    col = np.zeros((nb, 4, 4), np.int32)
    col[:, 0, :3] = a
    col[:, 1, :3] = bb
    col[:, 2, :3] = np.where(four[:, None], (2 * a + bb) // 3, (a + bb) // 2)
    col[:, 3, :3] = np.where(four[:, None], (a + 2 * bb) // 3, 0)
    col[:, :, 3] = 255
    col[~four, 3, 3] = 0
    idx = np.stack([(lines >> (2 * x)) & 3 for x in range(4)], -1)          # nb x 4(y) x 4(x)
    px = np.take_along_axis(col[:, None, :, :].repeat(4, 1), idx[..., None].astype(np.int64).repeat(4, -1), 2)
    if fmt == 0xB:      # explicit 4-bit alpha, u16 per row, after the colour block
        al = b[:, 8:16].reshape(nb, 4, 2).astype(np.uint32)
        al = al[..., 0] | (al[..., 1] << 8)
        px[..., 3] = np.stack([(al >> (4 * x)) & 15 for x in range(4)], -1) * 17
    elif fmt == 0xC:    # interpolated alpha: u32 + u16 index bits, then alpha1, alpha2
        ab = b[:, 8:16].astype(np.uint64)
        bits = ab[:, 0] | (ab[:, 1] << 8) | (ab[:, 2] << 16) | (ab[:, 3] << 24) | (ab[:, 4] << 32) | (ab[:, 5] << 40)
        a1, a2 = ab[:, 6].astype(np.int32), ab[:, 7].astype(np.int32)
        tab = np.zeros((nb, 8), np.int32)
        tab[:, 0], tab[:, 1] = a1, a2
        big = a1 > a2
        for k in range(2, 8):
            tab[:, k] = np.where(big, ((8 - k) * a1 + (k - 1) * a2) // 7, 0)
        for k in range(2, 6):
            tab[:, k] = np.where(big, tab[:, k], ((6 - k) * a1 + (k - 1) * a2) // 5)
        tab[:, 6] = np.where(big, tab[:, 6], 0)
        tab[:, 7] = np.where(big, tab[:, 7], 255)
        ai = np.stack([(bits >> np.uint64(3 * k)) & np.uint64(7) for k in range(16)], -1).astype(np.int64)
        px[..., 3] = np.take_along_axis(tab, ai, 1).reshape(nb, 4, 4)
    img = px.reshape(h // 4, w // 4, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
    return np.clip(img, 0, 255).astype(np.uint8)


def _to565(c):
    c = np.clip(np.rint(c), 0, 255).astype(np.int32)
    return ((c[..., 0] * 31 + 127) // 255 << 11) | ((c[..., 1] * 63 + 127) // 255 << 5) | ((c[..., 2] * 31 + 127) // 255)


def dxt1_encode(img, w, h):
    """PSP DXT1 (block = 4 index bytes, colour0, colour1), blocks in row-major order.
    Endpoints from the principal axis of each block, refined once by least squares."""
    a = img.astype(np.float32).reshape(h // 4, 4, w // 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 4)
    nb = a.shape[0]
    rgb = a[..., :3]
    clear = a[..., 3] < 128
    op = ~clear
    wgt = op.astype(np.float32)[..., None]
    cnt = np.maximum(wgt.sum(1), 1)
    mean = (rgb * wgt).sum(1) / cnt
    d = (rgb - mean[:, None]) * wgt
    cov = np.einsum('bni,bnj->bij', d, d)
    axis = np.ones((nb, 3), np.float32)
    for _ in range(8):
        axis = np.einsum('bij,bj->bi', cov, axis)
        axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-6)
    t = np.einsum('bni,bi->bn', rgb - mean[:, None], axis)
    tmin = np.where(op, t, np.inf).min(1)
    tmax = np.where(op, t, -np.inf).max(1)
    tmin = np.where(np.isfinite(tmin), tmin, 0)
    tmax = np.where(np.isfinite(tmax), tmax, 0)
    e0 = mean + axis * tmax[:, None]
    e1 = mean + axis * tmin[:, None]
    has_clear = clear.any(1)

    def palette(c0, c1, three):
        p0, p1 = _c565(c0).astype(np.float32), _c565(c1).astype(np.float32)
        pal = np.zeros((nb, 4, 3), np.float32)
        pal[:, 0], pal[:, 1] = p0, p1
        pal[:, 2] = np.where(three[:, None], (p0 + p1) // 2, (2 * p0 + p1) // 3)
        pal[:, 3] = np.where(three[:, None], 0, (p0 + 2 * p1) // 3)
        return pal

    def assign(c0, c1):
        three = has_clear | (c0 <= c1)
        pal = palette(c0, c1, three)
        dist = ((rgb[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1)
        dist[:, :, 3] = np.where(three[:, None], np.inf, dist[:, :, 3])
        idx = dist.argmin(-1)
        idx = np.where(clear, 3, idx)
        return idx, three

    def order(e0, e1):
        c0, c1 = _to565(e0), _to565(e1)
        # opaque blocks: c0 > c1 (4 colours); blocks with transparency: c0 <= c1 (3 colours + clear)
        sw = np.where(has_clear, c0 > c1, c0 < c1)
        c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
        same = (c0 == c1) & ~has_clear
        c1 = np.where(same & (c1 > 0), c1 - 1, c1)
        c0 = np.where(same & (c1 == 0) & (c0 == 0), 1, c0)
        return c0, c1

    c0, c1 = order(e0, e1)
    idx, three = assign(c0, c1)
    # one least-squares refinement of the endpoints
    wt4 = np.array([[1, 0], [0, 1], [2 / 3, 1 / 3], [1 / 3, 2 / 3]], np.float32)
    wt3 = np.array([[1, 0], [0, 1], [.5, .5], [0, 0]], np.float32)
    W = np.where(three[:, None, None], wt3[idx], wt4[idx]) * wgt
    A = np.einsum('bni,bnj->bij', W, W) + np.eye(2, dtype=np.float32) * 1e-3
    B = np.einsum('bni,bnc->bic', W, rgb)
    sol = np.linalg.solve(A, B)
    n0, n1 = order(sol[:, 0], sol[:, 1])
    idx2, three2 = assign(n0, n1)

    def err(c0, c1, idx, three):
        pal = palette(c0, c1, three)
        got = np.take_along_axis(pal, idx[..., None].repeat(3, -1), 1)
        return (((got - rgb) ** 2).sum(-1) * op).sum(1)
    better = err(n0, n1, idx2, three2) < err(c0, c1, idx, three)
    c0 = np.where(better, n0, c0)
    c1 = np.where(better, n1, c1)
    idx = np.where(better[:, None], idx2, idx)
    rows = idx.reshape(nb, 4, 4)
    lines = (rows[..., 0] | (rows[..., 1] << 2) | (rows[..., 2] << 4) | (rows[..., 3] << 6)).astype(np.uint8)
    out = np.zeros((nb, 8), np.uint8)
    out[:, 0:4] = lines
    out[:, 4], out[:, 5] = c0 & 255, c0 >> 8
    out[:, 6], out[:, 7] = c1 & 255, c1 >> 8
    return out.tobytes()


def build_palette(img, ncol):
    """RGBA palette by k-means (keeps small colour areas such as thin coloured lettering);
    fully transparent pixels get their own entry."""
    import cv2
    a = np.asarray(img.convert('RGBA')).reshape(-1, 4)
    clear = a[:, 3] < 8
    px = a[~clear].astype(np.float32)
    k = ncol - 1 if clear.any() else ncol
    uniq = np.unique(a[~clear], axis=0)
    if len(uniq) <= k:
        cent = uniq.astype(np.float32)
    else:
        # weight alpha a bit higher so edge alpha levels survive
        w = np.array([1, 1, 1, 1.5], np.float32)
        samp = px if len(px) <= 200000 else px[np.random.default_rng(0).choice(len(px), 200000, replace=False)]
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 0.5)
        cv2.setRNGSeed(1)
        _, _, cent = cv2.kmeans(samp * w, k, None, crit, 1, cv2.KMEANS_PP_CENTERS)
        cent = cent / w
    cent = np.clip(np.rint(cent), 0, 255)
    pal = np.zeros((ncol, 4), np.uint8)
    base = 1 if clear.any() else 0
    pal[base:base + len(cent)] = cent.astype(np.uint8)
    idx = np.zeros(len(a), np.uint8)
    cf = cent.astype(np.float32)
    cn = (cf ** 2).sum(1)
    for s0 in range(0, len(px), 65536):
        blk = px[s0:s0 + 65536]
        d = cn[None, :] - 2 * blk @ cf.T
        sel = np.argmin(d, 1).astype(np.uint8) + base
        tmp = np.nonzero(~clear)[0][s0:s0 + 65536]
        idx[tmp] = sel
    return idx.reshape(img.size[1], img.size[0]), pal


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'topng':
        u = UVR(open(a[2], 'rb').read())
        sw = not (len(a) > 4 and a[4] == 'linear')
        u.to_image(sw).save(a[3])
        print(a[2], u.w, u.h, u.bpp, hex(u.fmt0), hex(u.fmt1))
    elif a[1] == 'frompng':
        u = UVR(open(a[3], 'rb').read())
        open(a[4], 'wb').write(u.from_image(Image.open(a[2])))


def make_uvr(template, w, h, idx, palette):
    """New palettised UVR with the template's GBIX/format but new size (idx HxW, palette RGBA)."""
    t = UVR(template)
    head = bytearray(t.raw[:t.hdr_off])
    ncol = t.ncol
    assert idx.shape == (h, w)
    if t.bpp == 4:
        a = idx.reshape(h, w // 2, 2)
        rows = ((a[..., 0] & 0xF) | ((a[..., 1] & 0xF) << 4)).astype(np.uint8)
    else:
        rows = idx.astype(np.uint8)
    wb = w * t.bpp // 8
    pix = UVR.swizzle(rows, wb, h) if (wb >= 16 and h >= 8) else rows.reshape(-1)
    pal = palette.astype(np.uint8).tobytes() if t.pal_entry == 4 else _pack16(palette, t.fmt0).tobytes()
    body = pal + pix.tobytes()
    chunk = bytearray(b'UVRT' + struct.pack('<I', 8 + len(body)))
    chunk += bytes([t.fmt0, t.fmt1]) + t.raw[t.hdr_off + 10:t.hdr_off + 12] + struct.pack('<HH', w, h)
    return bytes(head + chunk + body)
