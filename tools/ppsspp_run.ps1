# Launch PPSSPP with an ISO, play a key script, take screenshots, then quit.
# Script syntax (one per line):  wait <sec> | key <name> [holdms] | shot <file.png> | repeat <n> key <name> <gapsec>
# Key names: up down left right circle cross square triangle start select l r ff
param([string]$Iso, [string]$Script, [string]$OutDir = "D:\newjakup\work\shots", [string]$Exe = "D:\newjakup\work\ppsspp_test\PPSSPPWindows64.exe")

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class KB {
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  public struct RECT { public int L, T, R, B; }
  public static void Press(byte vk, int ms, bool ext) {
    byte sc = (byte)MapVirtualKey(vk, 0);
    uint f = ext ? 1u : 0u;
    keybd_event(vk, sc, f, UIntPtr.Zero);
    System.Threading.Thread.Sleep(ms);
    keybd_event(vk, sc, f | 2u, UIntPtr.Zero);
  }
}
"@
Add-Type -AssemblyName System.Drawing

$keys = @{ up=@(0x49,$false); down=@(0x4B,$false); left=@(0x4A,$false); right=@(0x4C,$false);
  circle=@(0x44,$false); cross=@(0x53,$false); square=@(0x41,$false); triangle=@(0x57,$false);
  start=@(0x4D,$false); select=@(0x4E,$false); l=@(0x51,$false); r=@(0x57,$false); ff=@(0x09,$false); f2=@(0x71,$false); f4=@(0x73,$false) }

New-Item -ItemType Directory -Force $OutDir | Out-Null
$p = Start-Process $Exe -ArgumentList "`"$Iso`"" -PassThru
Start-Sleep 3
$p.Refresh()
$h = $p.MainWindowHandle

function Focus { [KB]::SetForegroundWindow($script:h) | Out-Null }
function Shot($name) {
  $r = New-Object KB+RECT
  [KB]::GetWindowRect($script:h, [ref]$r) | Out-Null
  $w = $r.R - $r.L; $hh = $r.B - $r.T
  $bmp = New-Object Drawing.Bitmap $w, $hh
  $g = [Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  $bmp.Save((Join-Path $OutDir $name))
  $g.Dispose(); $bmp.Dispose()
}

foreach ($line in Get-Content $Script) {
  $t = $line.Trim()
  if ($t -eq '' -or $t.StartsWith('#')) { continue }
  $a = $t -split '\s+'
  switch ($a[0]) {
    'wait' { Start-Sleep -Milliseconds ([int]([double]$a[1] * 1000)) }
    'key' { Focus; $k = $keys[$a[1]]; $ms = 80; if ($a.Length -gt 2) { $ms = [int]$a[2] }; [KB]::Press([byte]$k[0], $ms, $k[1]) }
    'repeat' { $n = [int]$a[1]; $k = $keys[$a[3]]; $gap = [double]$a[4]
      for ($i = 0; $i -lt $n; $i++) { Focus; [KB]::Press([byte]$k[0], 80, $k[1]); Start-Sleep -Milliseconds ([int]($gap * 1000)) } }
    'shot' { Focus; Start-Sleep -Milliseconds 300; Shot $a[1] }
  }
}
try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch {}
