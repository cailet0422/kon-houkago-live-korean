"""Replace raw control bytes accidentally written into a source file with escape sequences."""
import sys

p = sys.argv[1]
s = open(p, 'rb').read()
n = s.count(b'\x00') + s.count(b'\x01')
s = s.replace(b'\x00', b'\\x00').replace(b'\x01', b'\\x01')
open(p, 'wb').write(s)
print('fixed', n)
