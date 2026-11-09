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
            scene_threshold=3.0, min_scene_seconds=0.3, ocr_fps=4.0, ocr_threshold=3.0, max_frames=120,
            allow_model_download=False):
    if not (0 < ocr_fps <= 30 and ocr_threshold >= 0 and max_frames >= 1):
        raise ValueError('ocr-fps must be in (0,30], ocr-threshold >= 0')
    job = Path(out).resolve() if out else ROOT / 'jobs' / f'{stamp()}-{slug(Path(value).stem)}'
    if job.exists() and any(job.iterdir()):
        raise FileExistsError(f'Analiz klasörü boş değil; önceki işi korumak için yeni klasör seçin: {job}')
    job.mkdir(parents=True, exist_ok=True)
    source = input_file(value, job)
    info = video_info(source)
    save(job / 'probe.json', probe(source))
    fps = float(Fraction(info['fps']))
    video, proxy_meta = source, None
    from .transitions import needs_proxy, make_proxy, analyze_transitions, scenes_from_transitions
    if needs_proxy(info):
        print('Görsel ölçümler için 540p proxy hazırlanıyor...', flush=True)
        try:
            video, proxy_meta = make_proxy(source, info, job)
        except (OSError, RuntimeError) as exc:
            proxy_meta = {'skipped': f'proxy encode failed, original decoded instead: {exc}'}
    print('Sahne geçişleri, kamera hareketi ve kareler ölçülüyor...', flush=True)
    signals, transitions, transition_report = None, [], None
    try:
        signals, transitions, transition_report = analyze_transitions(video, fps, scene_threshold, min_scene_seconds)
        transition_report['video'] = 'proxy' if video != source else 'original'
        save(job / 'transitions.json', transition_report)
        scenes = scenes_from_transitions(transitions, signals['n'], fps, min_scene_seconds)
    except (ImportError, OSError, RuntimeError) as exc:
        print(f'Çok kaynaklı geçiş ölçümü yapılamadı, PySceneDetect kullanılıyor: {exc}', flush=True)
        from scenedetect import detect, AdaptiveDetector
        detector = AdaptiveDetector(adaptive_threshold=3.0, min_content_val=scene_threshold,
                                    min_scene_len=max(1, round(fps*min_scene_seconds)))
        scenes = [{'start': s.get_seconds(), 'end': e.get_seconds(),
                   'start_frame': s.get_frames(), 'end_frame': e.get_frames()}
                  for s, e in detect(str(video), detector, show_progress=False)]
        save(job / 'transitions.json', {'skipped': str(exc), 'transitions': []})
    if not scenes:
        scenes = [{'start': 0, 'end': info['duration'], 'start_frame': 0, 'end_frame': info['frames']}]
    save(job / 'scenes.json', scenes)
    frame_count = signals['n'] if signals else info['frames']
    plan = sample_plan(info['duration'], fps, frame_count, transitions, interval, max_frames)
    entries = extract_frames(video, plan, fps, job / 'frames')
    save(job / 'frames.json', entries)
    # Keep the overview compact; full cut-adjacent frames remain available individually.
    overview = entries if len(entries) <= 60 else [entries[round(i * (len(entries)-1) / 59)] for i in range(60)]
    contact_sheet([(f'{x["time"]:.3f}s / f{x["frame"]}', x['file']) for x in overview], job / 'contact-sheet.jpg')
    speech_status = {}
    if info['has_audio']:
        run([FFMPEG, '-v', 'error', '-y', '-i', source, '-vn', '-ac', '1', '-ar', '16000',
             job / 'audio.wav'], capture=True)
        if speech:
            try:
                transcribe(job / 'audio.wav', job, model, language, allow_model_download=allow_model_download)
            except (ImportError, OSError, RuntimeError) as exc:
                speech_status = {'skipped': str(exc)}
    manifest = {'created': datetime.now(IST).isoformat(), 'source': str(source),
                'video': info, 'scene_count': len(scenes), 'speech_requested': speech,
                'transcript_exists': (job / 'transcript.json').is_file(),
                'scene_detector': {'engine': 'multi-source transitions.py (histogram, pixel diff, ffmpeg scene, '
                                             'PySceneDetect AdaptiveDetector, edge-band geometry, blend fit, optical flow)',
                                   'adaptive_threshold':3.0, 'min_content_val':scene_threshold,
                                   'min_scene_seconds':min_scene_seconds,
                                   'scene_boundaries': 'hard_cut, dissolve, fade, flip, wipe (in-shot whips excluded)'}}
    from .ocr import scan_text
    ocr_source, ocr_info = source, info
    if video != source and proxy_meta and 'width' in proxy_meta:
        # The proxy keeps fps and frame count; captions stay ~30+ px tall at 540p, enough for OCR.
        ocr_source, ocr_info = video, {**info, 'width': proxy_meta['width'], 'height': proxy_meta['height']}
    text_report = scan_text(ocr_source, ocr_info, job / 'onscreen_text.json', ocr_fps, ocr_threshold,
                           transcript=(job / 'transcript.json') if manifest['transcript_exists'] else None)
    manifest['measurements'] = {'ocr': {k: text_report[k] for k in ['method', 'confidence', 'skipped'] if k in text_report}}
    manifest['measurements']['ocr']['file'] = 'onscreen_text.json'
    manifest['measurements']['ocr']['video'] = 'proxy' if ocr_source != source else 'original'
    manifest['transcription'] = speech_status
    from .audio_analysis import analyze_audio
    transcript = load(job / 'transcript.json') if manifest['transcript_exists'] else None
    audio_report = analyze_audio(source, info, job / 'audio_analysis.json', scenes, transcript)
    manifest['measurements']['audio'] = {k: audio_report[k] for k in ['method', 'confidence', 'skipped'] if k in audio_report}
    manifest['measurements']['audio']['file'] = 'audio_analysis.json'
    from .visual import analyze_visual
    visual_report = analyze_visual(source, info, scenes, entries, job / 'visual_analysis.json',
                                   signals=signals, transitions=transitions, video=video)
    manifest['measurements']['visual'] = {k: visual_report[k] for k in ['method', 'confidence', 'skipped'] if k in visual_report}
    manifest['measurements']['visual']['file'] = 'visual_analysis.json'
    manifest['measurements']['visual']['camera_segments'] = len(visual_report.get('camera_segments', []))
    if transition_report:
        manifest['measurements']['transitions'] = {
            'method': transition_report['method'], 'confidence': transition_report['confidence'],
            'file': 'transitions.json', 'count': len(transitions), 'counts': transition_report['counts'],
            'edit_boundaries': sum(1 for t in transitions if t['edit_boundary']),
            'items': [{k: t[k] for k in ('id', 'type', 'start', 'end', 'start_frame', 'end_frame', 'confidence',
                                         'edit_boundary')} for t in transitions]}
    else:
        manifest['measurements']['transitions'] = {'file': 'transitions.json', 'skipped': 'multi-source detector failed'}
    if proxy_meta:
        manifest['measurements']['proxy'] = proxy_meta
    manifest['sampling'] = {'max_frames': max_frames, 'actual_frames': len(entries), 'method': plan['method'],
                            'hook_frames': plan['hook_frames'], 'transition_frames': plan['transition_frames'],
                            'uniform_frames': plan['uniform_frames'], 'source': 'proxy' if video != source else 'original'}
    save(job / 'analysis.json', manifest)
    from .summary import build_summary
    build_summary(job)
    try:
        from .composition import analyze_composition
        comp = analyze_composition(job, video=video)
        manifest['measurements']['composition'] = {'file': 'composition.json', 'method': comp.get('method'),
                                                   'confidence': comp.get('confidence'), 'skipped': comp.get('skipped')}
        save(job / 'analysis.json', manifest)
    except Exception as exc:  # composition is an extra estimate; never lose the finished analysis
        print(f'Kompozisyon ölçülemedi: {exc}', flush=True)
    try:
        from .timeline import build_timeline
        build_timeline(job)
    except Exception as exc:  # a timeline problem must not lose the finished analysis
        print(f'Zaman çizelgesi üretilemedi: {exc}', flush=True)
    (job / 'REBUILD.md').write_text(
        f'# Referans yeniden kurma\n\nKaynak: {source}\n\n'
        f'{info["width"]} × {info["height"]}, {info["fps"]} fps, {info["duration"]:.3f} s.\n\n'
        'Agent: önce TIMELINE.md dosyasını oku (saniye saniye: konuşma, ekran metni, kamera, geçiş, ses, enerji; '
        'ham veri timeline.json). Sonra summary.md ve summary.json içindeki ölçüm/kaynak/yöntem/güven kayıtlarına bak. '
        'Eksik girdiler TIMELINE.md başında listelidir; onları elle ölç. '
        'onscreen_text.json, audio_analysis.json, visual_analysis.json ve transitions.json ayrıntıları içerir. '
        'contact-sheet.jpg ve kesme/geçiş çevresindeki ardışık kareleri gözle doğrula. '
        'scenes.json ve transcript.json ile katman, metin, font, renk, giriş/çıkış, '
        'easing ve ses vurgularını ölç. Ölçülmemiş özellikleri tahmin olarak belirt. '
        'Kaynağı tek video katmanı yapıp yeniden kurulduğunu iddia etme. '
        'Düzenlenebilir proje oluştur, özgün ses isteniyorsa onu koru, render al, '
        'social compare ile ölç ve farkları düzelt.\n', encoding='utf-8')
    print(f'Analiz hazır: {job}', flush=True)
    return job


def sample_plan(duration, fps, n_frames, transitions=(), interval=1.0, max_frames=120):
    """Frame indices for frames.json: evenly spaced hook (first 3 s), transition frames, uniform rest."""
    last = max(0, n_frames - 1)
    budget = max(1, max_frames)
    hook_end = min(3.0, duration)
    hook_n = min(12, max(1, budget // 4 if budget >= 8 else budget // 2 or 1))
    hook = sorted({min(last, round(i * hook_end / hook_n * fps)) for i in range(hook_n)})
    marks = []
    ranked = sorted(transitions, key=lambda t: (not t.get('edit_boundary'), -t.get('confidence', 0)))
    for tr in ranked:
        if tr['type'] == 'hard_cut':
            marks.append([tr['start_frame'] - 1, tr['start_frame']])
        else:
            marks.append([tr['start_frame'] - 1, tr['peak_frame'], tr['end_frame'] + 1])
    mark_budget = max(0, (budget - len(hook)) // 2)
    chosen = set(hook)
    trans = []
    for group in marks:
        group = sorted({min(last, max(0, f)) for f in group} - chosen)
        if len(trans) + len(group) > mark_budget:
            break
        trans += group
        chosen.update(group)
    remaining = budget - len(chosen)
    uniform = []
    span = duration - hook_end
    if remaining > 0 and span > 0:
        step = max(interval, span / remaining)
        t = hook_end
        while t < duration - 0.5 / fps and len(uniform) < remaining:
            f = min(last, round(t * fps))
            if f not in chosen:
                uniform.append(f)
                chosen.add(f)
            t += step
    return {'frames': sorted(chosen), 'hook_frames': len(hook), 'transition_frames': len(trans),
            'uniform_frames': len(uniform),
            'method': (f'{len(hook)} evenly spaced frames in the first {hook_end:g} s, before/peak/after frames '
                       f'of detected transitions, then uniform spacing (>= {interval:g} s) up to max_frames')}


def extract_frames(video, plan, fps, folder, width=540):
    """Decode once and write the planned frames (540 px wide JPEG)."""
    import cv2
    folder.mkdir(exist_ok=True)
    wanted = plan['frames']
    want = set(wanted)
    entries, index = [], 0
    cap = cv2.VideoCapture(str(video))
    try:
        while want and cap.grab():
            if index in want:
                ok, image = cap.retrieve()
                if ok:
                    h, w = image.shape[:2]
                    if w != width:
                        image = cv2.resize(image, (width, max(2, round(h * width / w / 2) * 2)),
                                           interpolation=cv2.INTER_AREA)
                    t = round(index / fps, 6)
                    file = folder / f'{len(entries):04d}-{t:.6f}.jpg'
                    cv2.imwrite(str(file), image, [cv2.IMWRITE_JPEG_QUALITY, 92])
                    entries.append({'time': t, 'frame': index, 'file': str(file)})
                want.discard(index)
            index += 1
    finally:
        cap.release()
    if not entries:  # decoder failure: fall back to ffmpeg seeks
        for i, f in enumerate(wanted):
            t = round(f / fps, 6)
            file = folder / f'{i:04d}-{t:.6f}.jpg'
            frame_at(video, t, file, width)
            entries.append({'time': t, 'frame': f, 'file': str(file)})
    return entries
