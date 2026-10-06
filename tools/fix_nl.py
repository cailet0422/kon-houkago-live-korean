"""Repair source files where a '\\n' escape inside quotes was turned into a real newline."""
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8').read()
n = s.count("'\n'")
s = s.replace("'\n'", "'\\n'")
open(p, 'w', encoding='utf-8').write(s)
print('fixed', n)
