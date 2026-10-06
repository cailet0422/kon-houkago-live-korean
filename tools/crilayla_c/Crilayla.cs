// CRILAYLA compressor (layout matching tools/cpk.py crilayla_decompress).
//   "CRILAYLA" u32 usize u32 csize | compressed[csize] | raw prefix[0x100]
// The data after the first 0x100 bytes is processed from its end towards its start; the bit
// stream is read by the decoder from the highest byte downwards, MSB first.
// Match: 1, 13-bit (dist-3), VLE length-3 (2,3,5,8,8,8.. bits); literal: 0, 8 bits.
// usage: crilayla <in> <out> [<in> <out> ...]   prints "name size" or "name STORE" per file
using System;
using System.Collections.Generic;
using System.IO;

static class Crilayla
{
    const int WIN = 8194, MINM = 3, HBITS = 16, MAXCHAIN = 2048;

    class Bits
    {
        public List<byte> buf = new List<byte>();
        uint cur; int n;
        public void Put(uint v, int k)
        {
            while (k-- > 0)
            {
                cur = (cur << 1) | ((v >> k) & 1);
                if (++n == 8) { buf.Add((byte)cur); cur = 0; n = 0; }
            }
        }
        public void Flush() { if (n > 0) Put(0, 8 - n); }
    }

    static byte[] Compress(byte[] src)
    {
        int n = src.Length;
        if (n <= 0x100 + 16) return null;
        int u = n - 0x100;
        byte[] r = new byte[u];
        for (int i = 0; i < u; i++) r[i] = src[n - 1 - i];
        int[] head = new int[1 << HBITS];
        for (int i = 0; i < head.Length; i++) head[i] = -1;
        int[] prev = new int[u];
        Func<int, int> hash = p => (int)((((uint)r[p] << 8) ^ ((uint)r[p + 1] << 4) ^ r[p + 2]) * 2654435761u >> (32 - HBITS));
        var bs = new Bits();
        int[] vle = { 2, 3, 5, 8 };
        int pos = 0;
        Func<int, int[]> find = q =>
        {
            int b = 0, bd = 0;
            if (q + MINM <= u)
            {
                int c = head[hash(q)], chain = 0;
                while (c >= 0 && chain++ < MAXCHAIN)
                {
                    int d = q - c;
                    if (d > WIN) break;
                    if (d >= 3)
                    {
                        int l = 0, mx = u - q;
                        while (l < mx && r[c + l] == r[q + l]) l++;
                        if (l > b) { b = l; bd = d; if (l >= 4096) break; }
                    }
                    c = prev[c];
                }
            }
            return new[] { b, bd };
        };
        while (pos < u)
        {
            var m0 = find(pos);
            int best = m0[0], bdist = m0[1];
            if (best >= MINM && best < 64 && pos + 1 < u)
            {
                // lazy evaluation: emit a literal if the next position gives a clearly longer match
                if (pos + MINM <= u)
                {
                    int h0 = hash(pos);
                    prev[pos] = head[h0];
                    head[h0] = pos;
                }
                var m1 = find(pos + 1);
                head[hash(pos)] = prev[pos];
                if (m1[0] > best + 1) { best = 0; }
            }
            int step;
            if (best >= MINM)
            {
                bs.Put(1, 1);
                bs.Put((uint)(bdist - 3), 13);
                long L = best - MINM;
                int k;
                for (k = 0; k < 4; k++)
                {
                    uint m = (1u << vle[k]) - 1;
                    uint x = L < m ? (uint)L : m;
                    bs.Put(x, vle[k]);
                    L -= x;
                    if (x != m) break;
                }
                if (k == 4)
                {
                    while (true)
                    {
                        uint x = L < 255 ? (uint)L : 255;
                        bs.Put(x, 8);
                        L -= x;
                        if (x != 255) break;
                    }
                }
                step = best;
            }
            else
            {
                bs.Put(0, 1);
                bs.Put(r[pos], 8);
                step = 1;
            }
            for (int s = 0; s < step; s++, pos++)
            {
                if (pos + MINM <= u)
                {
                    int h = hash(pos);
                    prev[pos] = head[h];
                    head[h] = pos;
                }
            }
        }
        bs.Flush();
        int blen = bs.buf.Count;
        int pad = (4 - blen % 4) % 4;
        int csize = blen + pad;
        if (0x10 + csize + 0x100 >= n) return null;
        var o = new MemoryStream();
        o.Write(System.Text.Encoding.ASCII.GetBytes("CRILAYLA"), 0, 8);
        o.Write(BitConverter.GetBytes((uint)u), 0, 4);
        o.Write(BitConverter.GetBytes((uint)csize), 0, 4);
        for (int k = 0; k < pad; k++) o.WriteByte(0);
        for (int k = blen - 1; k >= 0; k--) o.WriteByte(bs.buf[k]);
        o.Write(src, 0, 0x100);
        return o.ToArray();
    }

    static int Main(string[] args)
    {
        for (int i = 0; i + 1 < args.Length; i += 2)
        {
            byte[] src = File.ReadAllBytes(args[i]);
            byte[] c = Compress(src);
            if (c == null) { Console.WriteLine(args[i] + " STORE"); continue; }
            File.WriteAllBytes(args[i + 1], c);
            Console.WriteLine(args[i] + " " + c.Length);
        }
        return 0;
    }
}
