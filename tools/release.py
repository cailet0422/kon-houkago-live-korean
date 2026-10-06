"""Make release/kon_houkago_live_ko.xdelta from the built ISO, verify it, and refresh the
hashes in release/README_KR.txt."""
import hashlib
import os
import re
import zlib

import sys

import pyxdelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORIG = os.path.join(ROOT, 'k-on!_houkago_live!!_(japan)', 'K-On! Houkago Live!! (Japan).iso')
NEW = os.path.join(ROOT, 'build', 'K-On_Houkago_Live_KO.iso')
OUT = os.path.join(ROOT, 'release', 'kon_houkago_live_ko.xdelta')
README = os.path.join(ROOT, 'release', 'README_KR.txt')


def sha1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def build_gui_patcher():
    """block-delta patch + C# GUI patcher (KonKoPatcher.exe) with the patch embedded."""
    import shutil
    import subprocess
    import mkpatch
    mkpatch.main()
    d = os.path.join(ROOT, 'patcher')
    csc = r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    subprocess.run([csc, '-nologo', '-target:winexe', '-codepage:65001', '-optimize+',
                    '-resource:kon_ko.patch,kon_ko.patch', '-out:KonKoPatcher.exe', 'KonKoPatcher.cs'],
                   cwd=d, check=True)
    shutil.copy(os.path.join(d, 'KonKoPatcher.exe'), os.path.join(ROOT, 'release', 'KonKoPatcher.exe'))
    print('KonKoPatcher.exe', os.path.getsize(os.path.join(d, 'KonKoPatcher.exe')), 'bytes')


def build_android_patcher():
    """APK with the same patch as an uncompressed asset (patcher/android, offline Gradle 8.11.1 + AGP 8.10.1)."""
    import glob
    import shutil
    import subprocess
    d = os.path.join(ROOT, 'patcher', 'android')
    shutil.copy(os.path.join(ROOT, 'patcher', 'kon_ko.patch'), os.path.join(d, 'app', 'src', 'main', 'assets', 'kon_ko.patch'))
    gradle = glob.glob(os.path.join(os.path.expanduser('~'), '.gradle', 'wrapper', 'dists', 'gradle-8.11.1-bin',
                                    '*', 'gradle-8.11.1', 'bin', 'gradle.bat'))[0]
    env = dict(os.environ, JAVA_HOME=r'C:\Program Files\Java\jdk-21')
    subprocess.run([gradle, '--offline', '-q', 'assembleRelease'], cwd=d, env=env, check=True)
    shutil.copy(os.path.join(d, 'app', 'build', 'outputs', 'apk', 'release', 'app-release.apk'),
                os.path.join(ROOT, 'release', 'KonKoPatcher.apk'))
    print('KonKoPatcher.apk built')


if __name__ == '__main__':
    assert pyxdelta.run(ORIG, NEW, OUT)
    tmp = OUT + '.verify.iso'
    assert pyxdelta.decode(ORIG, OUT, tmp)
    new_sha = sha1(NEW)
    assert sha1(tmp) == new_sha, 'patch verification failed'
    os.remove(tmp)
    s = open(README, encoding='utf-8').read()
    s = re.sub(r'(K-On_Houkago_Live_KO\.iso[^\n]*\n  SHA-1 : )[0-9a-f]{40}', r'\g<1>' + new_sha, s)
    open(README, 'w', encoding='utf-8').write(s)
    print('patch', os.path.getsize(OUT), 'bytes; result sha1', new_sha)
    build_gui_patcher()
    build_android_patcher()
