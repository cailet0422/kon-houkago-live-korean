package kr.konko.patcher;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import android.os.PowerManager;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.security.MessageDigest;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;

/** K-On! Houkago Live!! Korean patch: original ISO -> patched ISO using the embedded block-delta patch. */
public class MainActivity extends Activity {
    static final String PATCH_ASSET = "kon_ko.patch";
    static final String OUT_NAME = "K-On_Houkago_Live_KO.iso";
    static final int REQ_OPEN = 1, REQ_SAVE = 2;

    TextView srcView, statusView;
    Button pickBtn, patchBtn;
    ProgressBar bar;
    Uri srcUri;
    volatile boolean busy;
    final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        int pad = dp(20);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("케이온! 방과후 라이브!!\n한국어 패치");
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.rgb(214, 40, 70));
        root.addView(title);

        TextView desc = new TextView(this);
        desc.setText("PSP 일본판 원본 ISO (ULJM05709)를 선택한 뒤 [패치]를 누르세요.\n"
                + "패치된 ISO를 저장할 위치를 고르면 자동으로 진행됩니다.\n"
                + "여유 공간 약 1.8GB가 필요하며, 진행 중에는 앱을 닫지 마세요.");
        desc.setPadding(0, dp(12), 0, dp(16));
        root.addView(desc);

        pickBtn = new Button(this);
        pickBtn.setText("원본 ISO 선택");
        root.addView(pickBtn);

        srcView = new TextView(this);
        srcView.setText("선택된 파일 없음");
        srcView.setPadding(0, dp(6), 0, dp(14));
        root.addView(srcView);

        patchBtn = new Button(this);
        patchBtn.setText("패치");
        patchBtn.setEnabled(false);
        patchBtn.setTextSize(18);
        root.addView(patchBtn);

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(1000);
        bar.setPadding(0, dp(16), 0, 0);
        root.addView(bar, new LinearLayout.LayoutParams(-1, -2));

        statusView = new TextView(this);
        statusView.setText("대기 중");
        statusView.setGravity(Gravity.CENTER_HORIZONTAL);
        statusView.setPadding(0, dp(8), 0, dp(20));
        root.addView(statusView);

        TextView note = new TextView(this);
        note.setText("※ PSP 실기/에뮬레이터에서 게임 내 「설정!」의 인스톨은 OFF로 두세요.\n"
                + "※ PPSSPP에서 바로 실행할 수 있습니다.");
        note.setTextSize(13);
        note.setTextColor(Color.GRAY);
        root.addView(note);

        ScrollView sv = new ScrollView(this);
        sv.addView(root);
        setContentView(sv);

        pickBtn.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                startActivityForResult(i, REQ_OPEN);
            }
        });
        patchBtn.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/octet-stream");
                i.putExtra(Intent.EXTRA_TITLE, OUT_NAME);
                startActivityForResult(i, REQ_SAVE);
            }
        });
    }

    int dp(int v) { return (int) (v * getResources().getDisplayMetrics().density + 0.5f); }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (res != RESULT_OK || data == null || data.getData() == null) return;
        if (req == REQ_OPEN) {
            srcUri = data.getData();
            srcView.setText(displayName(srcUri));
            patchBtn.setEnabled(true);
            statusView.setText("준비됨");
            bar.setProgress(0);
        } else if (req == REQ_SAVE) {
            start(srcUri, data.getData());
        }
    }

    String displayName(Uri u) {
        Cursor c = null;
        try {
            c = getContentResolver().query(u, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null);
            if (c != null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {
        } finally {
            if (c != null) c.close();
        }
        return u.getLastPathSegment();
    }

    void report(final String msg, final double frac) {
        ui.post(new Runnable() {
            public void run() {
                statusView.setText(msg);
                bar.setProgress((int) Math.max(0, Math.min(1000, frac * 1000)));
            }
        });
    }

    void start(final Uri src, final Uri dst) {
        busy = true;
        pickBtn.setEnabled(false);
        patchBtn.setEnabled(false);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
        final PowerManager.WakeLock wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "konko:patch");
        wl.acquire(60 * 60 * 1000L);
        new Thread(new Runnable() {
            public void run() {
                String err = null;
                try {
                    doPatch(src, dst);
                } catch (Throwable t) {
                    err = t.getMessage() != null ? t.getMessage() : t.toString();
                    try { DocumentsContract.deleteDocument(getContentResolver(), dst); } catch (Throwable ignored) { }
                } finally {
                    if (wl.isHeld()) wl.release();
                }
                final String e = err;
                ui.post(new Runnable() {
                    public void run() {
                        busy = false;
                        pickBtn.setEnabled(true);
                        patchBtn.setEnabled(true);
                        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                        if (e == null) {
                            statusView.setText("완료!");
                            dialog("패치 완료", "패치된 ISO가 저장되었습니다.\n\n" + displayName(dst)
                                    + "\n\n※ 게임 내 「설정!」의 인스톨은 OFF로 두세요.");
                        } else {
                            statusView.setText("실패");
                            dialog("패치 실패", e);
                        }
                    }
                });
            }
        }).start();
    }

    void dialog(String t, String m) {
        new AlertDialog.Builder(this).setTitle(t).setMessage(m).setPositiveButton("확인", null).show();
    }

    @Override
    public void onBackPressed() {
        if (busy) {
            dialog("패치 중", "패치가 끝날 때까지 기다려 주세요.");
            return;
        }
        super.onBackPressed();
    }

    static String hex(byte[] b) {
        StringBuilder s = new StringBuilder();
        for (byte x : b) s.append(String.format("%02x", x & 0xff));
        return s.toString();
    }

    static void readFully(InputStream in, byte[] b, int n) throws IOException {
        int got = 0;
        while (got < n) {
            int k = in.read(b, got, n - got);
            if (k < 0) throw new IOException("패치 데이터를 읽을 수 없습니다 (손상).");
            got += k;
        }
    }

    void doPatch(Uri srcUri, Uri dstUri) throws Exception {
        InputStream patch = getAssets().open(PATCH_ASSET);
        DataInputStream hdrIn = new DataInputStream(patch);
        byte[] hdr = new byte[72];
        hdrIn.readFully(hdr);
        ByteBuffer h = ByteBuffer.wrap(hdr).order(ByteOrder.LITTLE_ENDIAN);
        byte[] magic = new byte[8];
        h.get(magic);
        if (!new String(magic, "US-ASCII").equals("KONKO01\0")) throw new IOException("패치 데이터가 손상되었습니다.");
        long osz = h.getLong();
        byte[] osha = new byte[20]; h.get(osha);
        long nsz = h.getLong();
        byte[] nsha = new byte[20]; h.get(nsha);
        int blk = h.getInt();
        int nops = h.getInt();
        byte[] opsRaw = new byte[nops * 9];
        hdrIn.readFully(opsRaw);
        ByteBuffer ob = ByteBuffer.wrap(opsRaw).order(ByteOrder.LITTLE_ENDIAN);
        byte[] kind = new byte[nops];
        int[] cnt = new int[nops], arg = new int[nops];
        for (int i = 0; i < nops; i++) { kind[i] = ob.get(); cnt[i] = ob.getInt(); arg[i] = ob.getInt(); }

        ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(srcUri, "r");
        if (pfd == null) throw new IOException("원본 파일을 열 수 없습니다.");
        FileInputStream fin = new FileInputStream(pfd.getFileDescriptor());
        FileChannel ch = fin.getChannel();
        try {
            long len = pfd.getStatSize() >= 0 ? pfd.getStatSize() : ch.size();
            if (len != osz) {
                throw new IOException("원본 ISO가 아닙니다.\n\n필요한 크기: " + String.format("%,d", osz) + " 바이트\n선택한 파일: "
                        + String.format("%,d", len) + " 바이트\n\n이미 패치했거나 다른 버전/압축(CSO) 파일일 수 있습니다.");
            }
            // 1) verify original
            MessageDigest sha = MessageDigest.getInstance("SHA-1");
            ByteBuffer buf = ByteBuffer.allocate(1 << 22);
            long done = 0;
            ch.position(0);
            while (true) {
                buf.clear();
                int n = ch.read(buf);
                if (n <= 0) break;
                sha.update(buf.array(), 0, n);
                done += n;
                report("원본 확인 중... " + (done * 100 / len) + "%", 0.3 * done / len);
            }
            if (!hex(sha.digest()).equals(hex(osha))) {
                throw new IOException("원본 ISO 내용이 일치하지 않습니다 (SHA-1 불일치).\n덤프가 손상되었거나 다른 버전입니다.");
            }

            // 2) rebuild
            InflaterInputStream data = new InflaterInputStream(patch, new Inflater(true), 1 << 16);
            OutputStream os = getContentResolver().openOutputStream(dstUri, "w");
            if (os == null) throw new IOException("저장 위치에 쓸 수 없습니다.");
            OutputStream out = new BufferedOutputStream(os, 1 << 20);
            MessageDigest osh = MessageDigest.getInstance("SHA-1");
            byte[] b = new byte[blk];
            byte[] zero = new byte[blk];
            ByteBuffer bb = ByteBuffer.wrap(b);
            long written = 0;
            try {
                for (int i = 0; i < nops; i++) {
                    long pos = (long) arg[i] * blk;
                    for (int k = 0; k < cnt[i]; k++) {
                        int want = (int) Math.min(blk, nsz - written);
                        byte[] src = b;
                        if (kind[i] == 0) {
                            bb.clear();
                            bb.limit(want);
                            long p = pos + (long) k * blk;
                            while (bb.hasRemaining()) {
                                int r = ch.read(bb, p + bb.position());
                                if (r < 0) throw new IOException("원본을 읽는 중 오류가 발생했습니다.");
                            }
                        } else if (kind[i] == 1) {
                            readFully(data, b, want);
                        } else {
                            src = zero;
                        }
                        out.write(src, 0, want);
                        osh.update(src, 0, want);
                        written += want;
                    }
                    if ((i & 15) == 0) report("패치 적용 중... " + (written * 100 / nsz) + "%", 0.3 + 0.7 * written / nsz);
                }
                out.flush();
            } finally {
                out.close();
            }
            if (written != nsz || !hex(osh.digest()).equals(hex(nsha))) throw new IOException("결과 파일 검증에 실패했습니다.");
            report("완료!", 1);
        } finally {
            ch.close();
            fin.close();
            pfd.close();
            patch.close();
        }
    }
}
