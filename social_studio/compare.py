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
def compare(a, b, out, source_analysis=None, render_analysis=None):
    from PIL import Image, ImageChops, ImageStat, ImageDraw
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Comparison output is not empty')
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.social-job').open('x') as claim:
        claim.write('comparison')
    ia, ib = video_info(a), video_info(b)
    duration = min(ia['duration'], ib['duration'])
    import cv2
    import numpy as np
    ca, cb = cv2.VideoCapture(str(a)), cv2.VideoCapture(str(b))
    from .perceptual import ssim, OptionalMetrics
    optional = OptionalMetrics()
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
                           'psnr_db': 99.0 if mse == 0 else 10 * math.log10(255**2/mse),
                           'ssim': ssim(va, vb), **optional.score(va, vb)})
    finally:
        ca.release()
        cb.release()
    if not scores:
        raise RuntimeError('Karşılaştırılabilir kare bulunamadı.')
    worst = sorted(scores, key=lambda x: x['ssim'])
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
    from .comparison_details import analysis_bundle, timeline_comparison, audio_comparison
    left = analysis_bundle(a, out / 'source-analysis', source_analysis)
    right = left if Path(a).resolve() == Path(b).resolve() else analysis_bundle(b, out / 'render-analysis', render_analysis)
    report['mean_ssim'] = sum(row['ssim'] for row in scores) / len(scores)
    report['metric_methods'] = {
        'ssim': {'method': 'OpenCV 11x11 Gaussian SSIM, sigma 1.5, RGB channels averaged', 'confidence': 'structural measurement'},
        **optional.status}
    report['scene_scores'] = []
    for index, scene in enumerate(left['scenes']):
        rows = [row for row in scores if scene['start'] <= row['time'] < scene['end']]
        if rows:
            scene_score = {'scene': index, 'start': scene['start'], 'end': scene['end'], 'compared_frames': len(rows),
                           'method': 'reference-time bins; no semantic scene alignment', 'confidence': 'measurement'}
            for name in ['ssim', 'mae_255', 'psnr_db', 'lpips', 'clip_cosine']:
                values = [row[name] for row in rows if name in row]
                scene_score['mean_' + name] = sum(values) / len(values) if values else None
            report['scene_scores'].append(scene_score)
    report['audio_comparison'] = audio_comparison(a, b, left, right, float(Fraction(ia['fps'])))
    report['timing_comparison'] = timeline_comparison(left, right, float(Fraction(ia['fps'])))
    report['note'] += ' No measurement is a similarity percentage. SSIM, LPIPS and CLIP measure different properties.'
    save(out/'comparison.json', report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Video karşılaştırması</title>'
        '<style>body{background:#10151f;color:white;font:18px system-ui;max-width:1100px;margin:40px auto}'
        'img{max-width:100%}</style><h1>Kaynak / Render / Fark</h1>' +
        f'<p>{len(scores)} kare. Ortalama piksel farkı: {report["mean_mae_255"]:.3f} / 255. '
        f'Süre farkı: {report["duration_delta"]:.4f}s. SSIM: {report["mean_ssim"]:.4f}.</p>'
        '<p>Hiçbir ölçüm benzerlik yüzdesi değildir. En kötü anlar en düşük SSIM değerine göre seçildi.</p>'
        '<table><tr><th>Sahne</th><th>Başlangıç</th><th>Son</th><th>SSIM</th><th>MAE</th></tr>' +
        ''.join(f'<tr><td>{row["scene"]}</td><td>{row["start"]:.3f}</td><td>{row["end"]:.3f}</td><td>{row["mean_ssim"]:.4f}</td><td>{row["mean_mae_255"]:.3f}</td></tr>' for row in report['scene_scores']) + '</table>' + ''.join(
        f'<img src="{x.name}" alt="Karşılaştırma">' for x in sheet_items), encoding='utf-8')
    print(out/'index.html')
    return report


