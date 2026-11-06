"""Social Studio: reproducible local tools; editorial reasoning lives in agent skills."""
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

ROOT = Path(__file__).resolve().parent
WORKFLOW_PATH = (ROOT/'WORKFLOWS.md').as_posix()
EAR = ROOT.parent / 'earshot-main'
FFMPEG = ROOT / 'bin/ffmpeg.exe' if (ROOT / 'bin/ffmpeg.exe').is_file() else EAR / 'bin/ffmpeg.exe'
FFPROBE = ROOT / 'bin/ffprobe.exe' if (ROOT / 'bin/ffprobe.exe').is_file() else EAR / 'bin/ffprobe.exe'
PYTHON = ROOT / '.venv/Scripts/python.exe'
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
    isolated_node = ROOT/'runtimes/node22/node.exe'
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
    font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/arial.ttf'
    font = ImageFont.truetype(str(font_path), 17)
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


def srt_time(value):
    ms = round(float(value) * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def transcribe(source, out, model='large-v3-turbo', language='tr', device='cpu'):
    from faster_whisper import WhisperModel
    out.mkdir(parents=True, exist_ok=True)
    print(f'Konuşma çözülüyor: {model}, {device}', flush=True)
    model_obj = WhisperModel(model, device=device, compute_type='int8' if device == 'cpu' else 'float16')
    segments, info = model_obj.transcribe(str(source), language=None if language == 'auto' else language,
                                           word_timestamps=True, vad_filter=True, beam_size=5)
    rows = []
    for s in segments:
        rows.append({'start': s.start, 'end': s.end, 'text': s.text.strip(),
                     'avg_logprob': s.avg_logprob, 'no_speech_prob': s.no_speech_prob,
                     'words': [{'start': w.start, 'end': w.end, 'word': w.word, 'probability': w.probability}
                               for w in (s.words or [])]})
    save(out / 'transcript.json', {'language': info.language, 'probability': info.language_probability,
                                  'engine': 'faster-whisper', 'model': model, 'segments': rows,
                                  'low_confidence_words': [w for s in rows for w in s['words'] if w['probability'] < .75]})
    (out / 'transcript.txt').write_text('\n'.join(s['text'] for s in rows), encoding='utf-8')
    (out / 'captions.srt').write_text('\n\n'.join(
        f'{i+1}\n{srt_time(s["start"])} --> {srt_time(s["end"])}\n{s["text"]}'
        for i, s in enumerate(rows)), encoding='utf-8')
    return rows


def analyze(value, out=None, speech=True, model='large-v3-turbo', language='tr', interval=1.0,
            scene_threshold=3.0, min_scene_seconds=0.3):
    job = Path(out).resolve() if out else ROOT / 'jobs' / f'{stamp()}-{slug(Path(value).stem)}'
    if job.exists() and any(job.iterdir()):
        raise FileExistsError(f'Analiz klasörü boş değil; önceki işi korumak için yeni klasör seçin: {job}')
    job.mkdir(parents=True, exist_ok=True)
    source = input_file(value, job)
    info = video_info(source)
    save(job / 'probe.json', probe(source))
    print('Sahne kesmeleri ve kareler çıkarılıyor...', flush=True)
    from scenedetect import detect, AdaptiveDetector
    fps = float(Fraction(info['fps']))
    detector = AdaptiveDetector(adaptive_threshold=3.0, min_content_val=scene_threshold,
                                min_scene_len=max(1, round(fps*min_scene_seconds)))
    scene_list = detect(str(source), detector, show_progress=False)
    scenes = [{'start': s.get_seconds(), 'end': e.get_seconds(),
               'start_frame': s.get_frames(), 'end_frame': e.get_frames()} for s, e in scene_list]
    if not scenes:
        scenes = [{'start': 0, 'end': info['duration'], 'start_frame': 0, 'end_frame': info['frames']}]
    save(job / 'scenes.json', scenes)
    frames = job / 'frames'
    frames.mkdir(exist_ok=True)
    upper = max(0, info['duration'] - 1 / fps)
    step = max(interval, info['duration'] / 36)
    sample_times = {round(min(i * step, upper), 6) for i in range(max(1, math.ceil(info['duration'] / step)))}
    for scene in scenes:
        # At each cut inspect the actual consecutive frames, not only a uniform sheet.
        for offset in (-2, -1, 0, 1, 2):
            sample_times.add(round(min(upper, max(0, scene['start'] + offset / fps)), 6))
    entries = []
    for i, t in enumerate(sorted(sample_times)):
        file = frames / f'{i:04d}-{t:.6f}.jpg'
        frame_at(source, t, file)
        entries.append({'time': t, 'frame': round(t * fps), 'file': str(file)})
    save(job / 'frames.json', entries)
    # Keep the overview compact; full cut-adjacent frames remain available individually.
    overview = entries if len(entries) <= 60 else [entries[round(i * (len(entries)-1) / 59)] for i in range(60)]
    contact_sheet([(f'{x["time"]:.3f}s / f{x["frame"]}', x['file']) for x in overview], job / 'contact-sheet.jpg')
    if info['has_audio']:
        run([FFMPEG, '-v', 'error', '-y', '-i', source, '-vn', '-ac', '1', '-ar', '16000',
             job / 'audio.wav'], capture=True)
        if speech:
            transcribe(job / 'audio.wav', job, model, language)
    manifest = {'created': datetime.now(IST).isoformat(), 'source': str(source),
                'video': info, 'scene_count': len(scenes), 'speech_requested': speech,
                'transcript_exists': (job / 'transcript.json').is_file(),
                'scene_detector': {'engine':'PySceneDetect AdaptiveDetector','adaptive_threshold':3.0,
                                   'min_content_val':scene_threshold,'min_scene_seconds':min_scene_seconds}}
    save(job / 'analysis.json', manifest)
    (job / 'REBUILD.md').write_text(
        f'# Referans yeniden kurma\n\nKaynak: {source}\n\n'
        f'{info["width"]} × {info["height"]}, {info["fps"]} fps, {info["duration"]:.3f} s.\n\n'
        'Agent: contact-sheet.jpg ve kesme çevresindeki ardışık kareleri incele. '
        'scenes.json ve transcript.json ile katman, metin, font, renk, giriş/çıkış, '
        'easing ve ses vurgularını ölç. Ölçülmemiş özellikleri tahmin olarak belirt. '
        'Kaynağı tek video katmanı yapıp yeniden kurulduğunu iddia etme. '
        'Düzenlenebilir proje oluştur, özgün ses isteniyorsa onu koru, render al, '
        'social compare ile ölç ve farkları düzelt.\n', encoding='utf-8')
    print(f'Analiz hazır: {job}', flush=True)
    return job


def voice(args):
    text = Path(args.file).read_text(encoding='utf-8-sig') if args.file else args.text
    if not text:
        raise ValueError('--text veya --file gerekli.')
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f'Ses dosyası zaten var: {out}')
    if args.provider == 'edge':
        import edge_tts
        async def synth():
            # Sentence boundaries yield a useful draft SRT without another model pass.
            comm = edge_tts.Communicate(text, args.voice or 'tr-TR-EmelNeural', rate=args.rate,
                                        boundary='SentenceBoundary')
            subtitles = edge_tts.SubMaker()
            with out.open('wb') as f:
                async for chunk in comm.stream():
                    if chunk['type'] == 'audio':
                        f.write(chunk['data'])
                    elif chunk['type'] == 'SentenceBoundary':
                        subtitles.feed(chunk)
            out.with_suffix('.srt').write_text(subtitles.get_srt(), encoding='utf-8')
        asyncio.run(synth())
    else:
        from elevenlabs.client import ElevenLabs
        key = os.environ.get('ELEVENLABS_API_KEY')
        if not key or not args.voice:
            raise ValueError('ElevenLabs: ELEVENLABS_API_KEY ortam değişkeni ve --voice VOICE_ID gerekli.')
        client = ElevenLabs(api_key=key)
        with out.open('wb') as f:
            for chunk in client.text_to_speech.convert(voice_id=args.voice, text=text,
                    model_id='eleven_multilingual_v2', output_format='mp3_44100_128'):
                f.write(chunk)
    if not out.is_file() or out.stat().st_size < 100:
        raise RuntimeError('Ses dosyası boş.')
    save(out.with_suffix('.source.json'), {'provider': args.provider, 'voice': args.voice or 'tr-TR-EmelNeural',
                                         'created': datetime.now(IST).isoformat()})
    print(out)


def quality_check(source, out=None):
    source = Path(source).resolve()
    info = probe(source)
    report = {'file': str(source), 'probe': info, 'decode_ok': False, 'loudness': None}
    run([FFMPEG, '-v', 'error', '-i', source, '-f', 'null', '-'], capture=True)
    report['decode_ok'] = True
    if any(s['codec_type'] == 'audio' for s in info['streams']):
        p = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(source), '-vn', '-af',
                            'loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json', '-f', 'null', '-'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode:
            raise RuntimeError('Ses ölçümü başarısız.')
        raw = p.stderr.decode('utf-8', errors='replace')
        matches = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', raw, re.DOTALL)
        if matches:
            report['loudness'] = json.loads(matches[-1])
            report['true_peak_ok'] = float(report['loudness']['input_tp']) <= -1.0
            report['note'] = 'LUFS ve true peak ölçümü estetik/ses senkronu değerlendirmesinin yerine geçmez.'
    target = Path(out) if out else source.with_suffix('.quality.json')
    save(target, report)
    print(target)
    return report


def master(args):
    source, output = Path(args.source).resolve(), Path(args.out).resolve()
    if output.exists():
        raise FileExistsError(f'Çıktı zaten var: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(source), '-vn', '-af',
        f'loudnorm=I={args.lufs}:TP={args.peak}:LRA=9:print_format=json', '-f', 'null', '-'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError('İlk geçiş ses ölçümü başarısız.')
    raw = p.stderr.decode('utf-8', errors='replace')
    matches = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', raw, re.DOTALL)
    if not matches:
        raise RuntimeError('Mastering için ses akışı bulunamadı.')
    d = json.loads(matches[-1])
    if not math.isfinite(float(d['input_i'])):
        raise RuntimeError('Ses tamamen sessiz; mastering uygulanmadı.')
    filt = (f'loudnorm=I={args.lufs}:TP={args.peak}:LRA=9:measured_I={d["input_i"]}'
            f':measured_TP={d["input_tp"]}:measured_LRA={d["input_lra"]}'
            f':measured_thresh={d["input_thresh"]}:offset={d["target_offset"]}:linear=true')
    run([FFMPEG, '-v', 'error', '-n', '-i', source, '-map', '0:v?', '-map', '0:a:0',
         '-c:v', 'copy', '-af', filt, '-ar', '48000', '-c:a', 'aac', '-b:a', '192k',
         '-movflags', '+faststart', output], capture=True)
    quality_check(output)


def compare(a, b, out):
    from PIL import Image, ImageChops, ImageStat, ImageDraw
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    ia, ib = video_info(a), video_info(b)
    duration = min(ia['duration'], ib['duration'])
    import cv2
    import numpy as np
    ca, cb = cv2.VideoCapture(str(a)), cv2.VideoCapture(str(b))
    scores = []
    try:
        # Inspect the whole overlapping timeline, downscaled to bound CPU and memory.
        count = min(ia['frames'], ib['frames'])
        if ia['fps'] != ib['fps']:
            count = max(1, math.floor(duration * float(Fraction(ia['fps']))))
        for i in range(count):
            ok_a, fa = ca.read()
            if ia['fps'] == ib['fps']:
                ok_b, fb = cb.read()
            else:
                cb.set(cv2.CAP_PROP_POS_MSEC, i / float(Fraction(ia['fps'])) * 1000)
                ok_b, fb = cb.read()
            if not ok_a or not ok_b:
                break
            target_h = max(2, round(320 * ia['height'] / ia['width']))
            va = cv2.resize(fa, (320, target_h)).astype(np.float32)
            vb = cv2.resize(fb, (320, target_h)).astype(np.float32)
            mse = float(np.mean((va-vb)**2))
            scores.append({'frame': i, 'time': i / float(Fraction(ia['fps'])),
                           'mae_255': float(np.mean(np.abs(va-vb))),
                           'psnr_db': 99.0 if mse == 0 else 10 * math.log10(255**2/mse)})
    finally:
        ca.release()
        cb.release()
    if not scores:
        raise RuntimeError('Karşılaştırılabilir kare bulunamadı.')
    worst = sorted(scores, key=lambda x: x['mae_255'], reverse=True)
    selected = []
    for row in worst:
        if all(abs(row['time']-x['time']) >= 0.35 for x in selected):
            selected.append(row)
        if len(selected) >= 6:
            break
    sheet_items = []
    for j, row in enumerate(selected):
        x, y = out/f'a-{j}.jpg', out/f'b-{j}.jpg'
        frame_at(a, row['time'], x, 320)
        frame_at(b, row['time'], y, 320)
        aa, bb = Image.open(x).convert('RGB'), Image.open(y).convert('RGB')
        bb = bb.resize(aa.size)
        diff = ImageChops.difference(aa, bb)
        canvas = Image.new('RGB', (aa.width*3, aa.height+32), '#10151f')
        for col, im in enumerate([aa, bb, diff]):
            canvas.paste(im, (col*aa.width, 32))
        ImageDraw.Draw(canvas).text((8, 8), f'{row["time"]:.3f}s | source / render / difference', fill='white')
        file = out/f'comparison-{j}.jpg'
        canvas.save(file)
        sheet_items.append(file)
    report = {'source': ia, 'render': ib, 'duration_delta': ib['duration']-ia['duration'],
              'dimensions_match': (ia['width'], ia['height']) == (ib['width'], ib['height']),
              'fps_match': Fraction(ia['fps']) == Fraction(ib['fps']),
              'compared_frames': len(scores), 'mean_mae_255': sum(s['mae_255'] for s in scores)/len(scores),
              'worst_moments': selected, 'frame_scores': scores,
              'note': 'Görüntü farkı ölçülür; ses senkronu ve anlamsal benzerlik agent tarafından ayrıca incelenir.'}
    save(out/'comparison.json', report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Video karşılaştırması</title>'
        '<style>body{background:#10151f;color:white;font:18px system-ui;max-width:1100px;margin:40px auto}'
        'img{max-width:100%}</style><h1>Kaynak / Render / Fark</h1>' +
        f'<p>{len(scores)} kare. Ortalama piksel farkı: {report["mean_mae_255"]:.3f} / 255. '
        f'Süre farkı: {report["duration_delta"]:.4f}s.</p>' + ''.join(
        f'<img src="{x.name}" alt="Karşılaştırma">' for x in sheet_items), encoding='utf-8')
    print(out/'index.html')
    return report


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
    def number(row, key):
        raw = row.get(key)
        if raw in (None, ''):
            return None
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f'Geçersiz metrik: {key}={raw}')
        return value
    result = []
    for row in rows:
        parts = [number(row, k) for k in ['likes', 'comments', 'shares', 'saves']]
        interactions = sum(x for x in parts if x is not None)
        reach, views = number(row, 'reach'), number(row, 'views')
        denominator = reach if reach and reach > 0 else views
        result.append({**row, 'interactions': interactions,
                       'engagement_rate': round(100*interactions/denominator, 4) if denominator else None,
                       'engagement_denominator': 'reach' if reach and reach > 0 else 'views',
                       'missing_metrics': [k for k, v in zip(['likes','comments','shares','saves'], parts) if v is None]})
    ranked = sorted(result, key=lambda x: x['engagement_rate'] if x['engagement_rate'] is not None else -1,
                    reverse=True)
    save(args.out, {'posts': ranked, 'note': 'Etkileşim = beğeni+yorum+paylaşım+kaydetme. '
         'Oran erişim varsa erişime, yoksa görüntülemeye bölünür; farklı paydalı oranları ayrı yorumlayın. '
         'Eksik metrikler sıfır varsayılmadan işaretlenir. Küçük örneklem nedensellik kanıtlamaz.'})
    print(Path(args.out).resolve())


def render(args):
    project = Path(args.project).resolve()
    output = Path(args.out).resolve()
    if output.exists():
        raise FileExistsError(f'Çıktı zaten var; yeni bir ad seçin: {output}')
    hf(['check', str(project), '--json'])
    output.parent.mkdir(parents=True, exist_ok=True)
    hf(['render', str(project), '--quality', args.quality, '--workers', str(args.workers), '-o', str(output)])
    report = quality_check(output)
    if report.get('true_peak_ok') is False:
        print('Not: true peak -1 dBTP üzerinde; miks seviyesini inceleyin.')


def doctor():
    packages = ['edge-tts', 'faster-whisper', 'scenedetect', 'yt-dlp', 'Pillow', 'elevenlabs']
    versions = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    data = {'python': sys.version.split()[0], 'root': str(ROOT), 'packages': versions,
            'ffmpeg_exists': FFMPEG.is_file(), 'ffprobe_exists': FFPROBE.is_file(),
            'earshot_exists': (EAR/'.venv/Scripts/python.exe').is_file(),
            'elevenlabs_key_present': bool(os.environ.get('ELEVENLABS_API_KEY')),
            'postiz_key_present': bool(os.environ.get('POSTIZ_API_KEY')),
            'hyperframes': json.loads(hf(['doctor', '--json'], capture=True))}
    required_names = {'CLI binary', 'Node.js', 'FFmpeg', 'FFprobe', 'Chrome'}
    required_checks = [c for c in data['hyperframes'].get('checks', []) if c['name'] in required_names]
    data['core_ready'] = (all(versions.values()) and FFMPEG.is_file() and FFPROBE.is_file()
                          and len(required_checks) == len(required_names)
                          and all(c['ok'] for c in required_checks))
    data['optional_note'] = 'HyperFrames doctor.ok Docker ve alternatif modeller eksikse false olabilir. '
    data['optional_note'] += 'Bu kurulum faster-whisper ve Edge TTS kullanır; Docker çekirdek akışın şartı değildir.'
    save(ROOT/'doctor.json', data)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data['core_ready']:
        raise RuntimeError('Bir veya daha fazla bağımlılık hazır değil; doctor.json dosyasını inceleyin.')


def inbox(args):
    directory = Path(args.folder).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    journal_path = directory/'.social-inbox.json'
    journal = load(journal_path) if journal_path.exists() else {}
    print(f'Gelen video klasörü: {directory}', flush=True)
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
                print(f'Kopyalama henüz tamamlanmamış olabilir, bekleniyor: {file.name}', flush=True)
                continue
            try:
                job = analyze(str(file), speech=not args.no_speech, model=args.model)
                journal[identity] = {'job': str(job), 'status': 'analyzed'}
                save(journal_path, journal)
            except Exception as e:
                print(f'Analiz tamamlanamadı ({file.name}): {e}', file=sys.stderr, flush=True)
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
            raise RuntimeError('Codex CLI bulunamadı.')
        # Windows npm .cmd shims are invoked through cmd with a conservative single argument.
        # Prefer the npm package JS entrypoint so user text never crosses a cmd.exe parser.
        npm_codex = Path(os.environ.get('APPDATA', ''))/'npm/node_modules/@openai/codex/bin/codex.js'
        if npm_codex.is_file():
            run(['node', npm_codex, '--cd', ROOT, preamble+request])
        elif Path(command).suffix.lower() == '.exe':
            run([command, '--cd', ROOT, preamble+request])
        else:
            raise RuntimeError('Codex JS/exe giriş noktası bulunamadı; terminalde codex açıp social becerisini seçin.')
    else:
        command = shutil.which('claude.exe') or shutil.which('claude')
        if not command or Path(command).suffix.lower() != '.exe':
            raise RuntimeError('Claude Code çalıştırılabilir dosyası bulunamadı.')
        run([command, preamble+request], cwd=ROOT)


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


def main():
    p = argparse.ArgumentParser(description='Social Studio — yerel sosyal medya üretim araçları')
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('doctor', help='Bağımlılık ve hesap durumunu kontrol et')
    a = s.add_parser('analyze', help='Video/URL → sahneler, kareler, ses ve konuşma')
    a.add_argument('source'); a.add_argument('--out'); a.add_argument('--no-speech', action='store_true')
    a.add_argument('--model', default='large-v3-turbo'); a.add_argument('--language', default='tr')
    a.add_argument('--interval', type=float, default=1.0)
    a.add_argument('--scene-threshold', type=float, default=3.0,
                   help='Sabit zeminli grafiklerde 3; çok fazla kesme algılanırsa artırın')
    a.add_argument('--min-scene', type=float, default=0.3, help='En kısa sahne süresi (saniye)')
    t = s.add_parser('transcribe', help='Kelime zamanlı JSON, TXT ve SRT')
    t.add_argument('source'); t.add_argument('--out', required=True)
    t.add_argument('--model', default='large-v3-turbo'); t.add_argument('--language', default='tr')
    t.add_argument('--device', choices=['cpu','cuda'], default='cpu')
    v = s.add_parser('voice', help='Türkçe seslendirme')
    g = v.add_mutually_exclusive_group(required=True); g.add_argument('--text'); g.add_argument('--file')
    v.add_argument('--out', required=True); v.add_argument('--voice'); v.add_argument('--rate', default='+0%')
    v.add_argument('--provider', choices=['edge','elevenlabs'], default='edge')
    for name, help_text in [('hf','HyperFrames CLI'), ('postiz','Postiz CLI'), ('remotion','Remotion CLI'),
                            ('sfx','Earshot efekt ve ses analizi CLI')]:
        x = s.add_parser(name, help=help_text); x.add_argument('args', nargs=argparse.REMAINDER)
    r = s.add_parser('render', help='HyperFrames kontrol → render → medya kontrolü')
    r.add_argument('project'); r.add_argument('--out', required=True)
    r.add_argument('--quality', choices=['draft','looks','delivery'], default='delivery')
    r.add_argument('--workers', type=int, default=2)
    c = s.add_parser('check', help='Decode, codec, süre, LUFS ve true peak')
    c.add_argument('source'); c.add_argument('--out')
    c = s.add_parser('master', help='İki geçişli loudness mastering; video yeniden kodlanmaz')
    c.add_argument('source'); c.add_argument('--out', required=True)
    c.add_argument('--lufs', type=float, default=-16); c.add_argument('--peak', type=float, default=-1.5)
    c = s.add_parser('compare', help='Kaynak/render bütün kare farkları ve görsel rapor')
    c.add_argument('source'); c.add_argument('render'); c.add_argument('--out', required=True)
    c = s.add_parser('plan', help='Agentin dolduracağı taslak içerik takvimi')
    c.add_argument('--brand', required=True); c.add_argument('--days', type=int, default=30)
    c.add_argument('--start', default=datetime.now(IST).date().isoformat()); c.add_argument('--out', required=True)
    c.add_argument('--platform', default='instagram')
    a = s.add_parser('analytics', help='CSV/JSON performans verilerini hesapla')
    a.add_argument('file'); a.add_argument('--out', required=True)
    a = s.add_parser('inbox', help='Klasöre bırakılan videoları analiz et')
    a.add_argument('folder', nargs='?', default=str(ROOT/'inbox')); a.add_argument('--watch', action='store_true')
    a.add_argument('--no-speech', action='store_true'); a.add_argument('--model', default='large-v3-turbo')
    a = s.add_parser('launch', help='Normal izinleriyle yerel Codex veya Claude Code aç')
    a.add_argument('agent', choices=['codex','claude']); a.add_argument('--source'); a.add_argument('--prompt')
    a = s.add_parser('handoff', help='Mevcut Postiz sistemine video/kapak/metin/tarih ZIP paketi hazırla; yayın yapmaz')
    a.add_argument('source'); a.add_argument('--out',required=True); a.add_argument('--brand',default='')
    a.add_argument('--platform',default='instagram'); a.add_argument('--scheduled-at')
    g = a.add_mutually_exclusive_group(); g.add_argument('--caption'); g.add_argument('--caption-file')
    a = p.parse_args()
    if a.command == 'doctor': doctor()
    elif a.command == 'analyze':
        if not (0.1 <= a.scene_threshold <= 100 and 0.05 <= a.min_scene <= 60 and a.interval > 0):
            raise ValueError('scene-threshold 0.1…100, min-scene 0.05…60, interval > 0 olmalı.')
        analyze(a.source, a.out, not a.no_speech, a.model, a.language, a.interval,a.scene_threshold,a.min_scene)
    elif a.command == 'transcribe': transcribe(Path(a.source).resolve(), Path(a.out).resolve(), a.model, a.language, a.device)
    elif a.command == 'voice': voice(a)
    elif a.command == 'hf': hf(a.args)
    elif a.command == 'postiz': node_tool('postiz', 'postiz', a.args)
    elif a.command == 'remotion': node_tool('@remotion/cli', 'remotion', a.args)
    elif a.command == 'sfx': run([EAR/'.venv/Scripts/python.exe', EAR/'run.py', *a.args])
    elif a.command == 'render': render(a)
    elif a.command == 'check': quality_check(a.source, a.out)
    elif a.command == 'master':
        if not (-36 <= a.lufs <= -5 and -12 <= a.peak <= 0):
            raise ValueError('LUFS -36…-5 ve peak -12…0 aralığında olmalı.')
        master(a)
    elif a.command == 'compare': compare(a.source, a.render, a.out)
    elif a.command == 'plan':
        if not 1 <= a.days <= 366: raise ValueError('--days 1–366 aralığında olmalı.')
        calendar(a)
    elif a.command == 'analytics': analytics(a)
    elif a.command == 'inbox': inbox(a)
    elif a.command == 'launch': launch(a)
    elif a.command == 'handoff': handoff(a)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except KeyboardInterrupt:
        print('Durduruldu.', file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f'HATA: {e}', file=sys.stderr)
        sys.exit(1)
