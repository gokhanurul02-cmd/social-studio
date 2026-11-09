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


