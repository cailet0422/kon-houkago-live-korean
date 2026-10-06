p = 'D:/newjakup/tools/codex_edit.py'
s = open(p, encoding='utf-8').read()
a = s.index('def _find_codex():')
b = s.index('CODEX = _find_codex()')
new = '''def _find_codex():
    """The Codex Store app updates itself into a new versioned folder; ask Windows where it lives."""
    try:
        loc = subprocess.run(['powershell', '-NoProfile', '-Command',
                              '(Get-AppxPackage OpenAI.Codex).InstallLocation'],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        exe = os.path.join(loc, 'app', 'resources', 'codex.exe')
        if loc and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return 'codex'


'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('ok')
