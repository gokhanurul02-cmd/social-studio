from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import html
import importlib.metadata as metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from fractions import Fraction


from .media import *
def calendar(args):
    start = datetime.fromisoformat(args.start).replace(tzinfo=IST)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out/'calendar.json').exists() or (out/'calendar.csv').exists():
        raise FileExistsError(f'Mevcut takvimin üzerine yazılmaz; yeni klasör seçin: {out}')
    rows = []
    pillars = [('Eğitici', 'Bir sorunu çöz', 'Kaydet'), ('Güven', 'Süreç veya gerçek kanıt', 'Sorunu yaz'),
               ('Hikâye', 'Önce / sonra veya yolculuk', 'Paylaş'), ('Teklif', 'Net fayda ve teklif', 'İletişime geç')]
    for i in range(args.days):
        pillar, angle, cta = pillars[i % len(pillars)]
        date = start + timedelta(days=i)
        rows.append({'date': date.date().isoformat(), 'time': '19:00', 'timezone': 'Europe/Istanbul',
                     'brand': args.brand, 'platform': args.platform, 'pillar': pillar, 'angle': angle,
                     'hook': '', 'script': '', 'caption': '', 'cta': cta, 'asset': '', 'status': 'draft',
                     'time_basis': 'Taslak varsayım; gerçek hesap verisiyle agent tarafından değiştirilmeli.'})
    save(out/'calendar.json', rows)
    with (out/'calendar.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(out/'calendar.json')


def analytics(args):
    path = Path(args.file)
    if path.suffix.lower() == '.json':
        rows = load(path)
    else:
        with path.open(encoding='utf-8-sig', newline='') as f:
            sample = f.read(4096)
            f.seek(0)
            rows = list(csv.DictReader(f, dialect=csv.Sniffer().sniff(sample, delimiters=',;\t')))
    if not isinstance(rows, list) or not rows:
        raise ValueError('Boş olmayan JSON dizi veya başlıklı CSV gerekli.')
    from .performance import analyze_posts
    save(args.out, analyze_posts(rows, path))
    print(Path(args.out).resolve())


def handoff(args):
    """Create a provider-neutral offline publication package for the existing Postiz owner."""
    source = Path(args.source).resolve()
    info = video_info(source)
    out = Path(args.out).resolve()
    archive = out.parent/(out.name+'.zip')
    if archive.exists() or (out.exists() and any(out.iterdir())):
        raise FileExistsError('Aktarım paketi zaten var; yeni bir çıktı adı seçin.')
    scheduled = None
    if args.scheduled_at:
        date = datetime.fromisoformat(args.scheduled_at)
        if date.tzinfo is None:
            raise ValueError('Tarih saat dilimi içermeli; örnek: 2026-11-06T19:00:00+03:00')
        scheduled = date.astimezone(IST).isoformat()
    caption = Path(args.caption_file).read_text(encoding='utf-8-sig') if args.caption_file else (args.caption or '')
    media_dir = out/'media'
    media_dir.mkdir(parents=True,exist_ok=True)
    video = media_dir/('video'+source.suffix.lower())
    shutil.copyfile(source,video)
    cover = media_dir/'cover.jpg'
    frame_at(source,min(.75,info['duration']/2),cover,1080)
    def describe(file, kind, role):
        with file.open('rb') as f:
            digest = hashlib.file_digest(f,'sha256').hexdigest()
        return {'file':file.relative_to(out).as_posix(),'type':kind,'role':role,
                'bytes':file.stat().st_size,'sha256':digest}
    manifest = {'schema_version':'social-studio.handoff.v1','created_at':datetime.now(IST).isoformat(),
                'status':'draft','brand':args.brand,'platform':args.platform,'caption':caption,
                'scheduled_at':scheduled,'timezone':'Europe/Istanbul','platform_settings':{},
                'media':[describe(video,'video','primary'),describe(cover,'image','cover')],
                'video':info,'warnings':[] if caption.strip() else ['Açıklama metni boş.'],
                'note':'Yerel aktarım sözleşmesidir; resmî Postiz API gövdesi değildir. Bu komut yayın yapmaz.'}
    save(out/'publication.json',manifest)
    (out/'caption.txt').write_text(caption,encoding='utf-8')
    (out/'README.md').write_text('# Postiz aktarım paketi\n\n'
        'publication.json + media/ klasörünü mevcut sisteme aktarın. Dosya yolları paket köküne göredir. '
        'SHA-256 kayıtlarını doğrulayın. status=draft; scheduled_at yalnız plan bilgisidir. '
        'platform_settings ve gerçek hesap/integration ID mevcut sunucuda tamamlanır. '
        'Bu JSON doğrudan Postiz posts:create gövdesi olarak kullanılmaz; mevcut API şemasına eşlenir. '
        'Kapak otomatik seçilmiştir; gerekirse tasarım kapağıyla değiştirip hash kaydını güncelleyin.\n',encoding='utf-8')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(out.rglob('*')):
            if file.is_file():
                z.write(file,file.relative_to(out).as_posix())
    print(archive)
    return archive


