"""Download the release linked by the Windows build distributor and check its published SHA-256."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
downloads = root/'downloads'
downloads.mkdir(exist_ok=True)
req = urllib.request.Request('https://api.github.com/repos/GyanD/codexffmpeg/releases/latest',
                             headers={'User-Agent': 'social-studio-local'})
with urllib.request.urlopen(req, timeout=30) as response:
    release = json.load(response)
asset = next(a for a in release['assets'] if a['name'].endswith('essentials_build.zip'))
url = asset['browser_download_url']
archive = downloads/'ffmpeg-release-essentials.zip'
digest = asset.get('digest') or ''
if not digest.startswith('sha256:'):
    raise RuntimeError('GitHub release SHA-256 digest alanı bulunamadı.')
checksum = digest.split(':', 1)[1]
print('FFmpeg release indiriliyor...', flush=True)
urllib.request.urlretrieve(url, archive)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != checksum:
    raise RuntimeError('FFmpeg SHA-256 doğrulaması başarısız.')
(root/'bin').mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for name in ['ffmpeg.exe','ffprobe.exe']:
        members = [n for n in z.namelist() if n.endswith('/bin/'+name)]
        if len(members) != 1:
            raise RuntimeError('Arşivde beklenen binary bulunamadı: '+name)
        with z.open(members[0]) as source, (root/'bin'/name).open('wb') as dest:
            shutil.copyfileobj(source, dest)
(root/'bin/source.json').write_text(json.dumps({'url': url, 'sha256': actual}, indent=2), encoding='utf-8')
print('FFmpeg + FFprobe doğrulandı.', flush=True)
