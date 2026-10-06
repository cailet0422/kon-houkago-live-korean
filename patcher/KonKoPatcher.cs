// 케이온! 방과후 라이브!! 한국어 패치 - GUI patcher
// Build: csc /target:winexe /codepage:65001 /resource:kon_ko.patch,kon_ko.patch /out:KonKoPatcher.exe KonKoPatcher.cs
using System;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;

class PatcherForm : Form
{
    const string ResName = "kon_ko.patch";
    TextBox isoBox;
    Button browseBtn, patchBtn;
    ProgressBar bar;
    Label status;
    volatile bool busy;

    PatcherForm()
    {
        Text = "케이온! 방과후 라이브!! 한국어 패치";
        Font = new Font("Malgun Gothic", 9.5f);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        ClientSize = new Size(520, 210);
        StartPosition = FormStartPosition.CenterScreen;
        AllowDrop = true;

        var title = new Label { Text = "케이온! 방과후 라이브!! (PSP, ULJM05709) 한국어 패치", Left = 16, Top = 14, Width = 490, Height = 22,
                                Font = new Font("Malgun Gothic", 11f, FontStyle.Bold) };
        var hint = new Label { Text = "일본판 원본 ISO 파일을 선택하거나 이 창으로 끌어다 놓은 뒤 [패치]를 누르세요.", Left = 16, Top = 42, Width = 490, Height = 20 };
        isoBox = new TextBox { Left = 16, Top = 70, Width = 400, ReadOnly = true };
        browseBtn = new Button { Text = "찾아보기...", Left = 424, Top = 68, Width = 80, Height = 27 };
        patchBtn = new Button { Text = "패치", Left = 16, Top = 106, Width = 488, Height = 34, Enabled = false,
                                Font = new Font("Malgun Gothic", 10.5f, FontStyle.Bold) };
        bar = new ProgressBar { Left = 16, Top = 150, Width = 488, Height = 18, Maximum = 1000 };
        status = new Label { Left = 16, Top = 176, Width = 488, Height = 22, Text = "대기 중" };
        Controls.AddRange(new Control[] { title, hint, isoBox, browseBtn, patchBtn, bar, status });

        browseBtn.Click += delegate {
            using (var d = new OpenFileDialog { Filter = "PSP ISO (*.iso)|*.iso|모든 파일 (*.*)|*.*", Title = "원본 ISO 선택" })
                if (d.ShowDialog(this) == DialogResult.OK) SetIso(d.FileName);
        };
        DragEnter += (s, e) => { if (e.Data.GetDataPresent(DataFormats.FileDrop)) e.Effect = DragDropEffects.Copy; };
        DragDrop += (s, e) => { var f = (string[])e.Data.GetData(DataFormats.FileDrop); if (f.Length > 0) SetIso(f[0]); };
        patchBtn.Click += delegate { Start(); };
        FormClosing += (s, e) => { if (busy && MessageBox.Show(this, "패치 중입니다. 정말 종료할까요?", Text, MessageBoxButtons.YesNo) != DialogResult.Yes) e.Cancel = true; };
    }

    void SetIso(string path)
    {
        if (busy) return;
        isoBox.Text = path;
        patchBtn.Enabled = File.Exists(path);
        status.Text = "준비됨";
        bar.Value = 0;
    }

    void Ui(Action a) { if (IsHandleCreated) BeginInvoke(a); }
    void Report(string msg, double frac) { Ui(() => { status.Text = msg; bar.Value = Math.Max(0, Math.Min(1000, (int)(frac * 1000))); }); }

    void Start()
    {
        string src = isoBox.Text;
        string dst = Path.Combine(Path.GetDirectoryName(src), "K-On_Houkago_Live_KO.iso");
        if (string.Equals(Path.GetFullPath(src), Path.GetFullPath(dst), StringComparison.OrdinalIgnoreCase))
        {
            MessageBox.Show(this, "이미 패치된 파일입니다.", Text);
            return;
        }
        if (File.Exists(dst) && MessageBox.Show(this, dst + "\n파일이 이미 있습니다. 덮어쓸까요?", Text, MessageBoxButtons.YesNo) != DialogResult.Yes)
            return;
        busy = true;
        patchBtn.Enabled = browseBtn.Enabled = false;
        var t = new Thread(() =>
        {
            string err = null;
            try { Run(src, dst); }
            catch (Exception ex) { err = ex.Message; try { if (File.Exists(dst)) File.Delete(dst); } catch { } }
            Ui(() =>
            {
                busy = false;
                patchBtn.Enabled = browseBtn.Enabled = true;
                if (err == null)
                {
                    status.Text = "완료!";
                    MessageBox.Show(this, "패치가 완료되었습니다.\n\n" + dst + "\n\n※ 게임 내 「설정!」의 인스톨은 OFF로 두세요.", Text,
                                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    status.Text = "실패";
                    MessageBox.Show(this, err, Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            });
        });
        t.IsBackground = true;
        t.Start();
    }

    static string Hex(byte[] b) { var s = new StringBuilder(); foreach (var x in b) s.Append(x.ToString("x2")); return s.ToString(); }

    static Stream OpenPatch()
    {
        string side = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), ResName);
        if (File.Exists(side)) return File.OpenRead(side);
        var s = Assembly.GetExecutingAssembly().GetManifestResourceStream(ResName);
        if (s == null) throw new Exception("패치 데이터(" + ResName + ")를 찾을 수 없습니다.");
        return s;
    }

    void Run(string src, string dst)
    {
        using (var p = OpenPatch())
        {
            var r = new BinaryReader(p);
            if (Encoding.ASCII.GetString(r.ReadBytes(8)) != "KONKO01\0") throw new Exception("패치 데이터가 손상되었습니다.");
            long osz = r.ReadInt64(); byte[] osha = r.ReadBytes(20);
            long nsz = r.ReadInt64(); byte[] nsha = r.ReadBytes(20);
            int blk = r.ReadInt32(); int nops = r.ReadInt32();
            var kind = new byte[nops]; var cnt = new int[nops]; var arg = new int[nops];
            for (int i = 0; i < nops; i++) { kind[i] = r.ReadByte(); cnt[i] = r.ReadInt32(); arg[i] = r.ReadInt32(); }

            // 1) check the original image
            long len = new FileInfo(src).Length;
            if (len != osz)
                throw new Exception("원본 ISO가 아닙니다.\n\n필요한 파일: K-On! Houkago Live!! (Japan).iso\n크기 " + osz.ToString("N0") +
                                    " 바이트 (선택한 파일: " + len.ToString("N0") + " 바이트)\n\n이미 패치했거나 다른 버전/압축(CSO) 파일일 수 있습니다.");
            using (var sha = SHA1.Create())
            using (var f = new FileStream(src, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20))
            {
                var buf = new byte[1 << 22]; long done = 0; int n;
                while ((n = f.Read(buf, 0, buf.Length)) > 0)
                {
                    sha.TransformBlock(buf, 0, n, null, 0); done += n;
                    Report("원본 확인 중... " + (done * 100 / len) + "%", 0.3 * done / len);
                }
                sha.TransformFinalBlock(buf, 0, 0);
                if (Hex(sha.Hash) != Hex(osha))
                    throw new Exception("원본 ISO 내용이 일치하지 않습니다(SHA-1 불일치).\n덤프가 손상되었거나 다른 버전입니다.\n\n필요: " + Hex(osha));
            }

            // 2) rebuild
            using (var data = new DeflateStream(p, CompressionMode.Decompress))
            using (var s = new FileStream(src, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16))
            using (var o = new FileStream(dst, FileMode.Create, FileAccess.Write, FileShare.None, 1 << 20))
            using (var sha = SHA1.Create())
            {
                var b = new byte[blk]; var zero = new byte[blk];
                long written = 0;
                for (int i = 0; i < nops; i++)
                {
                    if (kind[i] == 0) s.Position = (long)arg[i] * blk;
                    for (int k = 0; k < cnt[i]; k++)
                    {
                        int want = (int)Math.Min(blk, nsz - written);
                        byte[] outb = b;
                        if (kind[i] == 0) ReadFull(s, b, want);
                        else if (kind[i] == 1) ReadFull(data, b, want);
                        else outb = zero;
                        o.Write(outb, 0, want);
                        sha.TransformBlock(outb, 0, want, null, 0);
                        written += want;
                    }
                    if ((i & 15) == 0) Report("패치 적용 중... " + (written * 100 / nsz) + "%", 0.3 + 0.7 * written / nsz);
                }
                sha.TransformFinalBlock(b, 0, 0);
                if (written != nsz || Hex(sha.Hash) != Hex(nsha)) throw new Exception("결과 파일 검증에 실패했습니다.");
            }
            Report("완료!", 1);
        }
    }

    static void ReadFull(Stream s, byte[] b, int n)
    {
        int got = 0;
        while (got < n)
        {
            int k = s.Read(b, got, n - got);
            if (k <= 0) throw new Exception("데이터를 읽을 수 없습니다(파일 손상).");
            got += k;
        }
    }

    [STAThread]
    static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        var f = new PatcherForm();
        if (args.Length > 0) f.Shown += delegate { f.SetIso(args[0]); };
        Application.Run(f);
    }
}
