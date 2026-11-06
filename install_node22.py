"""Isolate Postiz's exact Node requirement without changing the user's system Node."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen, urlretrieve

root = Path(__file__).resolve().parent
version = '22.23.4'
base = f'https://nodejs.org/dist/v{version}/'
with urlopen(base+'SHASUMS256.txt', timeout=30) as response:
    lines = response.read().decode().splitlines()
checksum = next(line.split()[0] for line in lines if line.split()[-1] == 'win-x64/node.exe')
out = root/'runtimes/node22/node.exe'
out.parent.mkdir(parents=True, exist_ok=True)
urlretrieve(base+'win-x64/node.exe', out)
actual = hashlib.sha256(out.read_bytes()).hexdigest()
if checksum != actual:
    raise RuntimeError('Node SHA-256 mismatch.')
out.with_suffix('.source.json').write_text(json.dumps({'url': base+'win-x64/node.exe', 'sha256': actual}, indent=2), encoding='utf-8')
print('Postiz Node', version, 'verified.')
