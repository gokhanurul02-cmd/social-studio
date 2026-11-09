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
from .audio import *
from .analyze import analyze
from .compare import compare
from .publish import *
def render(args):
    project = Path(args.project).resolve()
    output = Path(args.out).resolve()
    if output.exists():
        raise FileExistsError(f'Ã‡Ä±ktÄ± zaten var; yeni bir ad seÃ§in: {output}')
    hf(['check', str(project), '--json'])
    output.parent.mkdir(parents=True, exist_ok=True)
    hf(['render', str(project), '--quality', args.quality, '--workers', str(args.workers), '-o', str(output)])
    report = quality_check(output)
    if report.get('true_peak_ok') is False:
        print('Not: true peak -1 dBTP Ã¼zerinde; miks seviyesini inceleyin.')


def _hyperframes_status():
    try:
        return json.loads(hf(['doctor', '--json'], capture=True))
    except (OSError, RuntimeError, KeyError) as exc:
        return {'checks': [], 'skipped': str(exc)}


def doctor():
    packages = ['opencv-python', 'numpy', 'rapidocr-onnxruntime', 'paddleocr', 'pytesseract', 'librosa', 'scikit-image', 'torch', 'lpips', 'open-clip-torch', 'edge-tts', 'faster-whisper', 'scenedetect', 'yt-dlp', 'Pillow', 'elevenlabs']
    versions = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    data = {'python': sys.version.split()[0], 'root': str(ROOT), 'packages': versions,
            'ffmpeg_exists': FFMPEG.is_file(), 'ffprobe_exists': FFPROBE.is_file(),
            'earshot_exists': venv_python(EAR / '.venv').is_file(),
            'elevenlabs_key_present': bool(os.environ.get('ELEVENLABS_API_KEY')),
            'postiz_key_present': bool(os.environ.get('POSTIZ_API_KEY')),
            'hyperframes': _hyperframes_status()}
    required_names = {'CLI binary', 'Node.js', 'FFmpeg', 'FFprobe', 'Chrome'}
    required_checks = [c for c in data['hyperframes'].get('checks', []) if c['name'] in required_names]
    data['core_ready'] = (versions.get('Pillow') is not None and FFMPEG.is_file() and FFPROBE.is_file()
                          )
    data['optional_note'] = 'HyperFrames doctor.ok Docker ve alternatif modeller eksikse false olabilir. '
    data['optional_note'] += 'Bu kurulum faster-whisper ve Edge TTS kullanÄ±r; Docker Ã§ekirdek akÄ±ÅŸÄ±n ÅŸartÄ± deÄŸildir.'
    save(ROOT/'doctor.json', data)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data['core_ready']:
        raise RuntimeError('Bir veya daha fazla baÄŸÄ±mlÄ±lÄ±k hazÄ±r deÄŸil; doctor.json dosyasÄ±nÄ± inceleyin.')


def inbox(args):
    directory = Path(args.folder).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    journal_path = directory/'.social-inbox.json'
    journal = load(journal_path) if journal_path.exists() else {}
    print(f'Gelen video klasÃ¶rÃ¼: {directory}', flush=True)
    while True:
        for file in sorted(directory.iterdir()):
            if file.suffix.lower() not in ('.mp4', '.mov', '.mkv', '.webm', '.m4v') or not file.is_file():
                continue
            stat = file.stat()
            identity = f'{file.name}:{stat.st_size}:{stat.st_mtime_ns}'
            if identity in journal:
                continue
            # Do not analyze a file while it is still being copied.
            if time.time()-stat.st_mtime < 5:
                print(f'Kopyalama henÃ¼z tamamlanmamÄ±ÅŸ olabilir, bekleniyor: {file.name}', flush=True)
                continue
            try:
                job = analyze(str(file), out=ROOT / 'jobs' / f'{stamp()}-{slug(file.stem)}', speech=not args.no_speech, model=args.model)
                journal[identity] = {'job': str(job), 'status': 'analyzed'}
                save(journal_path, journal)
            except Exception as e:
                print(f'Analiz tamamlanamadÄ± ({file.name}): {e}', file=sys.stderr, flush=True)
                if not args.watch:
                    raise
        if not args.watch:
            break
        time.sleep(5)


def launch(args):
    """Start the user's interactive agent; inherit its normal authentication and permissions."""
    request = args.prompt or 'Show the available social content workflows and help me create a video.'
    if args.source:
        source = args.source if re.match(r'https?://', args.source) else str(Path(args.source).resolve())
        request = ('Rebuild this reference as editable code and a finished verified MP4. Source: '
                   + json.dumps(source, ensure_ascii=False) + '. ' + (args.prompt or ''))
    preamble = f'Read {WORKFLOW_PATH} and use the social-rebuild workflow for a reference, social-create for a brief. '
    if args.agent == 'codex':
        command = shutil.which('codex.cmd') or shutil.which('codex')
        if not command:
            raise RuntimeError('Codex CLI bulunamadÄ±.')
        # Windows npm .cmd shims are invoked through cmd with a conservative single argument.
        # Prefer the npm package JS entrypoint so user text never crosses a cmd.exe parser.
        npm_codex = Path(os.environ.get('APPDATA', ''))/'npm/node_modules/@openai/codex/bin/codex.js'
        if npm_codex.is_file():
            run(['node', npm_codex, '--cd', ROOT, preamble+request])
        elif os.name != 'nt' or Path(command).suffix.lower() == '.exe':
            run([command, '--cd', ROOT, preamble+request])
        else:
            raise RuntimeError('Codex JS/exe giriÅŸ noktasÄ± bulunamadÄ±; terminalde codex aÃ§Ä±p social becerisini seÃ§in.')
    else:
        command = shutil.which('claude.exe') or shutil.which('claude')
        if not command or (os.name == 'nt' and Path(command).suffix.lower() != '.exe'):
            raise RuntimeError('Claude Code Ã§alÄ±ÅŸtÄ±rÄ±labilir dosyasÄ± bulunamadÄ±.')
        run([command, preamble+request], cwd=ROOT)


def main():
    p = argparse.ArgumentParser(description='Social Studio â€” yerel sosyal medya Ã¼retim araÃ§larÄ±')
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('doctor', help='BaÄŸÄ±mlÄ±lÄ±k ve hesap durumunu kontrol et')
    a = s.add_parser('analyze', help='Video/URL â†’ sahneler, kareler, ses ve konuÅŸma')
    a.add_argument('source'); a.add_argument('--out'); a.add_argument('--no-speech', action='store_true')
    a.add_argument('--model', default='large-v3-turbo'); a.add_argument('--language', default='tr')
    a.add_argument('--interval', type=float, default=1.0)
    a.add_argument('--scene-threshold', type=float, default=3.0,
                   help='Sabit zeminli grafiklerde 3; Ã§ok fazla kesme algÄ±lanÄ±rsa artÄ±rÄ±n')
    a.add_argument('--min-scene', type=float, default=0.3, help='En kÄ±sa sahne sÃ¼resi (saniye)')
    a.add_argument('--ocr-fps', type=float, default=4.0)
    a.add_argument('--ocr-threshold', type=float, default=3.0)
    t = s.add_parser('transcribe', help='Kelime zamanlÄ± JSON, TXT ve SRT')
    t.add_argument('source'); t.add_argument('--out', required=True)
    t.add_argument('--model', default='large-v3-turbo'); t.add_argument('--language', default='tr')
    t.add_argument('--allow-model-download', action='store_true')
    t.add_argument('--device', choices=['cpu','cuda'], default='cpu')
    v = s.add_parser('voice', help='TÃ¼rkÃ§e seslendirme')
    g = v.add_mutually_exclusive_group(required=True); g.add_argument('--text'); g.add_argument('--file')
    v.add_argument('--out', required=True); v.add_argument('--voice'); v.add_argument('--rate', default='+0%')
    v.add_argument('--provider', choices=['edge','elevenlabs'], default='edge')
    for name, help_text in [('hf','HyperFrames CLI'), ('postiz','Postiz CLI'), ('remotion','Remotion CLI'),
                            ('sfx','Earshot efekt ve ses analizi CLI')]:
        x = s.add_parser(name, help=help_text); x.add_argument('args', nargs=argparse.REMAINDER)
    r = s.add_parser('render', help='HyperFrames kontrol â†’ render â†’ medya kontrolÃ¼')
    r.add_argument('project'); r.add_argument('--out', required=True)
    r.add_argument('--quality', choices=['draft','looks','delivery'], default='delivery')
    r.add_argument('--workers', type=int, default=2)
    c = s.add_parser('check', help='Decode, codec, sÃ¼re, LUFS ve true peak')
    c.add_argument('source'); c.add_argument('--out')
    c = s.add_parser('master', help='Ä°ki geÃ§iÅŸli loudness mastering; video yeniden kodlanmaz')
    c.add_argument('source'); c.add_argument('--out', required=True)
    c.add_argument('--lufs', type=float, default=-16); c.add_argument('--peak', type=float, default=-1.5)
    c = s.add_parser('compare', help='Kaynak/render bÃ¼tÃ¼n kare farklarÄ± ve gÃ¶rsel rapor')
    c.add_argument('source'); c.add_argument('render'); c.add_argument('--out', required=True)
    c = s.add_parser('plan', help='Agentin dolduracaÄŸÄ± taslak iÃ§erik takvimi')
    c.add_argument('--brand', required=True); c.add_argument('--days', type=int, default=30)
    c.add_argument('--start', default=datetime.now(IST).date().isoformat()); c.add_argument('--out', required=True)
    c.add_argument('--platform', default='instagram')
    a = s.add_parser('analytics', help='CSV/JSON performans verilerini hesapla')
    a.add_argument('file'); a.add_argument('--out', required=True)
    a = s.add_parser('inbox', help='KlasÃ¶re bÄ±rakÄ±lan videolarÄ± analiz et')
    a.add_argument('folder', nargs='?', default=str(ROOT/'inbox')); a.add_argument('--watch', action='store_true')
    a.add_argument('--no-speech', action='store_true'); a.add_argument('--model', default='large-v3-turbo')
    a = s.add_parser('launch', help='Normal izinleriyle yerel Codex veya Claude Code aÃ§')
    a.add_argument('agent', choices=['codex','claude']); a.add_argument('--source'); a.add_argument('--prompt')
    a = s.add_parser('handoff', help='Mevcut Postiz sistemine video/kapak/metin/tarih ZIP paketi hazÄ±rla; yayÄ±n yapmaz')
    a.add_argument('source'); a.add_argument('--out',required=True); a.add_argument('--brand',default='')
    a.add_argument('--platform',default='instagram'); a.add_argument('--scheduled-at')
    g = a.add_mutually_exclusive_group(); g.add_argument('--caption'); g.add_argument('--caption-file')
    a = p.parse_args()
    if a.command == 'doctor': doctor()
    elif a.command == 'analyze':
        if not (0.1 <= a.scene_threshold <= 100 and 0.05 <= a.min_scene <= 60 and a.interval > 0):
            raise ValueError('scene-threshold 0.1â€¦100, min-scene 0.05â€¦60, interval > 0 olmalÄ±.')
        analyze(a.source, a.out, not a.no_speech, a.model, a.language, a.interval,a.scene_threshold,a.min_scene,a.ocr_fps,a.ocr_threshold)
    elif a.command == 'transcribe': transcribe(Path(a.source).resolve(), Path(a.out).resolve(), a.model, a.language, a.device, a.allow_model_download)
    elif a.command == 'voice': voice(a)
    elif a.command == 'hf': hf(a.args)
    elif a.command == 'postiz': node_tool('postiz', 'postiz', a.args)
    elif a.command == 'remotion': node_tool('@remotion/cli', 'remotion', a.args)
    elif a.command == 'sfx': run([venv_python(EAR / '.venv'), EAR/'run.py', *a.args])
    elif a.command == 'render': render(a)
    elif a.command == 'check': quality_check(a.source, a.out)
    elif a.command == 'master':
        if not (-36 <= a.lufs <= -5 and -12 <= a.peak <= 0):
            raise ValueError('LUFS -36â€¦-5 ve peak -12â€¦0 aralÄ±ÄŸÄ±nda olmalÄ±.')
        master(a)
    elif a.command == 'compare': compare(a.source, a.render, a.out)
    elif a.command == 'plan':
        if not 1 <= a.days <= 366: raise ValueError('--days 1â€“366 aralÄ±ÄŸÄ±nda olmalÄ±.')
        calendar(a)
    elif a.command == 'analytics': analytics(a)
    elif a.command == 'inbox': inbox(a)
    elif a.command == 'launch': launch(a)
    elif a.command == 'handoff': handoff(a)


