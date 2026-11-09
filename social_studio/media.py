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


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = (ROOT / 'WORKFLOWS.md').as_posix()
EAR = Path(os.environ.get('SOCIAL_EARSHOT', ROOT.parent / 'earshot-main'))

def venv_python(folder):
    return Path(folder) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

def resolve_tool(name):
    override = os.environ.get('SOCIAL_' + name.upper())
    if override:
        return Path(override).expanduser()
    for folder in [ROOT / 'bin', EAR / 'bin']:
        for filename in [name, name + '.exe']:
            candidate = folder / filename
            if candidate.is_file():
                return candidate
    return Path(shutil.which(name) or name)

FFMPEG = resolve_tool('ffmpeg')
FFPROBE = resolve_tool('ffprobe')
PYTHON = venv_python(ROOT / '.venv')
IST = timezone(timedelta(hours=3))
os.environ['PATH'] = str(FFMPEG.parent) + os.pathsep + os.environ.get('PATH', '')
os.environ['PYTHONUTF8'] = '1'

def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def run(args, cwd=None, capture=False):
    p = subprocess.run([str(x) for x in args], cwd=cwd, shell=False,
                       stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE if capture else None)
    if p.returncode:
        detail = (p.stderr or b'').decode('utf-8', errors='replace')[-3500:]
        raise RuntimeError(f'{Path(str(args[0])).name} exit {p.returncode}\n{detail}')
    return (p.stdout or b'').decode('utf-8', errors='replace')


def node_tool(package, binary, args, cwd=None, capture=False):
    package_dir = ROOT / 'node_modules' / package
    bins = load(package_dir / 'package.json')['bin']
    entry = bins if isinstance(bins, str) else bins[binary]
    isolated_node = ROOT / 'runtimes/node22' / ('node.exe' if os.name == 'nt' else 'bin/node')
    executable = isolated_node if package == 'postiz' and isolated_node.is_file() else 'node'
    return run([executable, package_dir / entry, *args], cwd=cwd, capture=capture)


def hf(args, cwd=None, capture=False):
    return node_tool('hyperframes', 'hyperframes', args, cwd, capture)


def probe(path):
    return json.loads(run([FFPROBE, '-v', 'error', '-show_format', '-show_streams',
                           '-of', 'json', path], capture=True))


def video_info(path):
    info = probe(path)
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    if not v:
        raise ValueError('Video akışı bulunamadı.')
    rate = v.get('avg_frame_rate', '0/0')
    if rate == '0/0':
        rate = v.get('r_frame_rate', '30/1')
    duration = float(v.get('duration') or info['format']['duration'])
    return {'width': v['width'], 'height': v['height'], 'fps': rate,
            'duration': duration, 'frames': int(v.get('nb_frames') or round(duration * float(Fraction(rate)))),
            'has_audio': any(s['codec_type'] == 'audio' for s in info['streams']),
            'codec': v['codec_name']}


def stamp():
    return datetime.now(IST).strftime('%Y%m%d-%H%M%S-%f')


def slug(text):
    return re.sub(r'[^\w-]+', '-', text, flags=re.UNICODE).strip('-')[:60] or 'video'


def input_file(value, job):
    if re.match(r'https?://', value):
        from yt_dlp import YoutubeDL
        with YoutubeDL({'outtmpl': str(job / 'source.%(ext)s'), 'noplaylist': True,
                        'format': 'bv*[height<=1080]+ba/b[height<=1080]/best',
                        'merge_output_format': 'mp4', 'ffmpeg_location': str(FFMPEG.parent),
                        'quiet': True}) as ydl:
            result = ydl.extract_info(value, download=True)
            final = next((Path(x['filepath']) for x in result.get('requested_downloads', [])
                          if Path(x.get('filepath', '')).is_file()), None)
            if final is None:
                final = Path(ydl.prepare_filename(result))
            if not final.is_file():
                matches = [p for p in job.glob('source.*') if p.suffix in ('.mp4', '.webm', '.mkv', '.mov')]
                if not matches:
                    raise RuntimeError('İndirme tamamlandı fakat video bulunamadı.')
                final = matches[0]
            save(job / 'source-metadata.json', {k: result.get(k) for k in
                 ['webpage_url', 'title', 'uploader', 'upload_date', 'license', 'duration']})
            return final.resolve()
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Dosya bulunamadı: {path}')
    return path


def frame_at(source, seconds, output, width=540):
    run([FFMPEG, '-v', 'error', '-y', '-ss', f'{seconds:.6f}', '-i', source,
         '-frames:v', '1', '-vf', f'scale={width}:-2', '-update', '1', output], capture=True)


def contact_sheet(items, output):
    from PIL import Image, ImageDraw, ImageFont
    font_path = os.environ.get('SOCIAL_FONT')
    font = ImageFont.truetype(font_path, 17) if font_path else ImageFont.load_default()
    cols, cell_w, cell_h = 6, 200, 270
    sheet = Image.new('RGB', (cols * cell_w, math.ceil(len(items) / cols) * cell_h), '#10151f')
    draw = ImageDraw.Draw(sheet)
    for i, (label, file) in enumerate(items):
        im = Image.open(file).convert('RGB')
        im.thumbnail((cell_w - 12, cell_h - 32))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(im, (x + (cell_w - im.width) // 2, y + 4))
        draw.text((x + 8, y + cell_h - 26), label, fill='white', font=font)
    sheet.save(output)


