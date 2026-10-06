/* CRILAYLA compressor (layout matching tools/cpk.py crilayla_decompress).
 *
 *   "CRILAYLA" u32 usize u32 csize | compressed[csize] | raw prefix[0x100]
 *
 * The data after the first 0x100 bytes is processed from its end towards its start
 * ("reversed stream"); the bit stream is read by the decoder from the highest byte
 * downwards, MSB first. Match: 1, 13-bit (dist-3), VLE length-3 (2,3,5,8,8,8.. bits);
 * literal: 0, 8 bits.
 *
 * usage: crilayla <in> <out>      (exit 2 if the result would not be smaller)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIN 8194
#define MINM 3
#define HBITS 16
#define HSIZE (1 << HBITS)
#define MAXCHAIN 256

static unsigned char *bits_buf;
static size_t bits_len, bits_cap;
static unsigned cur;
static int nbits;

static void put(unsigned v, int n) {
    while (n--) {
        cur = (cur << 1) | ((v >> n) & 1);
        if (++nbits == 8) {
            if (bits_len == bits_cap) { bits_cap = bits_cap * 2 + 1024; bits_buf = realloc(bits_buf, bits_cap); }
            bits_buf[bits_len++] = (unsigned char)cur;
            cur = 0; nbits = 0;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 3) return 1;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *src = malloc(n + 1);
    if (fread(src, 1, n, f) != (size_t)n) return 1;
    fclose(f);
    if (n <= 0x100 + 16) return 2;
    long u = n - 0x100;
    unsigned char *r = malloc(u);              /* reversed stream */
    for (long i = 0; i < u; i++) r[i] = src[n - 1 - i];

    int *head = malloc(sizeof(int) * HSIZE);
    int *prev = malloc(sizeof(int) * u);
    for (int i = 0; i < HSIZE; i++) head[i] = -1;
#define HASH(p) ((((unsigned)r[p] << 8) ^ ((unsigned)r[(p) + 1] << 4) ^ (unsigned)r[(p) + 2]) * 2654435761u >> (32 - HBITS))

    long i = 0;
    while (i < u) {
        int best = 0, bdist = 0;
        if (i + MINM <= u) {
            unsigned h = HASH(i);
            int c = head[h], chain = 0;
            while (c >= 0 && chain++ < MAXCHAIN) {
                long d = i - c;
                if (d > WIN) break;
                if (d >= 3) {
                    long l = 0, mx = u - i;
                    while (l < mx && r[c + l] == r[i + l]) l++;
                    if (l > best) { best = (int)l; bdist = (int)d; if (l >= 4096) break; }
                }
                c = prev[c];
            }
        }
        long step;
        if (best >= MINM) {
            put(1, 1);
            put(bdist - 3, 13);
            long L = best - MINM;
            static const int vle[4] = {2, 3, 5, 8};
            int k;
            for (k = 0; k < 4; k++) {
                unsigned m = (1u << vle[k]) - 1;
                unsigned x = L < m ? (unsigned)L : m;
                put(x, vle[k]);
                L -= x;
                if (x != m) break;
            }
            if (k == 4) {
                for (;;) {
                    unsigned x = L < 255 ? (unsigned)L : 255;
                    put(x, 8);
                    L -= x;
                    if (x != 255) break;
                }
            }
            step = best;
        } else {
            put(0, 1);
            put(r[i], 8);
            step = 1;
        }
        for (long s = 0; s < step; s++, i++) {
            if (i + MINM <= u) {
                unsigned h = HASH(i);
                prev[i] = head[h];
                head[h] = (int)i;
            }
        }
    }
    if (nbits) put(0, 8 - nbits);                 /* flush */
    /* decoder reads from the last compressed byte downwards: store the stream reversed,
       padded at the low end to a multiple of 4 */
    size_t pad = (4 - bits_len % 4) % 4;
    size_t csize = bits_len + pad;
    if ((long)(0x10 + csize + 0x100) >= n) return 2;
    FILE *o = fopen(argv[2], "wb");
    if (!o) return 1;
    unsigned char hdr[16] = {'C', 'R', 'I', 'L', 'A', 'Y', 'L', 'A'};
    unsigned uu = (unsigned)u, cc = (unsigned)csize;
    memcpy(hdr + 8, &uu, 4);
    memcpy(hdr + 12, &cc, 4);
    fwrite(hdr, 1, 16, o);
    for (size_t k = 0; k < pad; k++) fputc(0, o);
    for (size_t k = 0; k < bits_len; k++) fputc(bits_buf[bits_len - 1 - k], o);
    fwrite(src, 1, 0x100, o);
    fclose(o);
    return 0;
}
