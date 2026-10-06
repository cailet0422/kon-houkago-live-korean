import java.io.*;
import java.nio.*;
import java.nio.channels.FileChannel;
import java.security.MessageDigest;
import java.util.zip.*;

/** Desktop check of the Android patch loop (same Inflater/FileChannel usage as MainActivity.doPatch). */
public class PatchTest {
    static String hex(byte[] b) { StringBuilder s = new StringBuilder(); for (byte x : b) s.append(String.format("%02x", x & 0xff)); return s.toString(); }

    public static void main(String[] a) throws Exception {
        InputStream patch = new FileInputStream(a[1]);
        DataInputStream hdrIn = new DataInputStream(patch);
        byte[] hdr = new byte[72]; hdrIn.readFully(hdr);
        ByteBuffer h = ByteBuffer.wrap(hdr).order(ByteOrder.LITTLE_ENDIAN);
        h.position(8); long osz = h.getLong(); h.position(h.position() + 20);
        long nsz = h.getLong(); byte[] nsha = new byte[20]; h.get(nsha);
        int blk = h.getInt(); int nops = h.getInt();
        byte[] opsRaw = new byte[nops * 9]; hdrIn.readFully(opsRaw);
        ByteBuffer ob = ByteBuffer.wrap(opsRaw).order(ByteOrder.LITTLE_ENDIAN);
        byte[] kind = new byte[nops]; int[] cnt = new int[nops], arg = new int[nops];
        for (int i = 0; i < nops; i++) { kind[i] = ob.get(); cnt[i] = ob.getInt(); arg[i] = ob.getInt(); }
        FileChannel ch = new FileInputStream(a[0]).getChannel();
        InflaterInputStream data = new InflaterInputStream(patch, new Inflater(true), 1 << 16);
        MessageDigest osh = MessageDigest.getInstance("SHA-1");
        byte[] b = new byte[blk], zero = new byte[blk];
        ByteBuffer bb = ByteBuffer.wrap(b);
        long written = 0;
        for (int i = 0; i < nops; i++) {
            long pos = (long) arg[i] * blk;
            for (int k = 0; k < cnt[i]; k++) {
                int want = (int) Math.min(blk, nsz - written);
                byte[] src = b;
                if (kind[i] == 0) {
                    bb.clear(); bb.limit(want);
                    long p = pos + (long) k * blk;
                    while (bb.hasRemaining()) if (ch.read(bb, p + bb.position()) < 0) throw new IOException("eof");
                } else if (kind[i] == 1) {
                    int got = 0; while (got < want) { int r = data.read(b, got, want - got); if (r < 0) throw new IOException("data eof"); got += r; }
                } else src = zero;
                osh.update(src, 0, want);
                written += want;
            }
        }
        String got = hex(osh.digest());
        System.out.println("written=" + written + " sha1=" + got + (got.equals(hex(nsha)) && written == nsz ? " OK" : " MISMATCH"));
    }
}
