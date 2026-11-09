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
def srt_time(value):
    ms = round(float(value) * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def transcribe(source, out, model='large-v3-turbo', language='tr', device='cpu', allow_model_download=False):
    from faster_whisper import WhisperModel
    if any((out / name).exists() for name in ['transcript.json', 'transcript.txt', 'captions.srt']):
        raise FileExistsError('Transcript output already exists')
    if allow_model_download:
        print(f'Model download enabled; weights will be cached: {model}', flush=True)
    out.mkdir(parents=True, exist_ok=True)
    print(f'Konuşma çözülüyor: {model}, {device}', flush=True)
    model_obj = WhisperModel(model, device=device, compute_type='int8' if device == 'cpu' else 'float16',
                             local_files_only=not allow_model_download)
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


