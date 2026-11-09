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


