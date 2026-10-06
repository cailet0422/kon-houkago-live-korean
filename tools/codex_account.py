"""Talk to the Codex app-server (JSON-RPC over stdio) for account usage.

usage: codex_account.py read            -> rate limits + usage
       codex_account.py reset           -> consume one rate-limit reset credit
"""
import json
import subprocess
import sys
import uuid

sys.path.insert(0, __import__('os').path.dirname(__file__))
from codex_edit import CODEX  # noqa: E402


def call(reqs):
    p = subprocess.Popen([CODEX, 'app-server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
    def send(obj):
        p.stdin.write(json.dumps(obj) + '\n')
        p.stdin.flush()

    def wait(i):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get('id') == i:
                return m
    send({'jsonrpc': '2.0', 'id': 0, 'method': 'initialize',
          'params': {'clientInfo': {'name': 'kon-patch', 'version': '1.0'},
                     'capabilities': {'experimentalApi': True}}})
    wait(0)
    send({'jsonrpc': '2.0', 'method': 'initialized'})
    out = []
    for k, (method, params) in enumerate(reqs, 1):
        send({'jsonrpc': '2.0', 'id': k, 'method': method, 'params': params})
        out.append((method, wait(k)))
    p.stdin.close()
    p.kill()
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'read':
        reqs = [('account/read', {}), ('account/rateLimits/read', None), ('account/usage/read', {})]
    else:
        reqs = [('account/rateLimitResetCredit/consume', {'idempotencyKey': str(uuid.uuid4())}),
                ('account/rateLimits/read', None)]
    for m, r in call(reqs):
        print('==', m)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])
