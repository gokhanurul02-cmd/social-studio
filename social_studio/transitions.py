"""Multi-source shot transition detection.

One sequential decode of a low-resolution proxy feeds every visual measurement:
histogram and pixel differences, sharpness, uniform edge bands (card flips, slides),
dense DIS optical flow fitted to a camera model, plus ffmpeg's scene score and
PySceneDetect as independent evidence.  Thresholds are expressed relative to the
analysis frame (short side) so they hold for any input resolution.
"""
from __future__ import annotations

import math
import re
import statistics
from fractions import Fraction
from pathlib import Path

from .media import FFMPEG, run

ANALYSIS_SHORT = 270          # flow / difference resolution (short side, px)
THUMB_SHORT = 54              # thumbnails kept in memory for blend/wipe fitting
PROXY_SHORT = 540
HEAVY_CODECS = {'av1', 'hevc', 'h265', 'vp9', 'prores', 'dnxhd', 'mjpeg'}
EDIT_TYPES = {'hard_cut', 'dissolve', 'flip', 'wipe', 'fade'}
BURST_SPEED = 0.03            # short sides per frame (~0.9 short sides/s at 30 fps)


# ---------------------------------------------------------------- proxy ----

def needs_proxy(info):
    return min(info['width'], info['height']) > 600 or str(info.get('codec', '')).lower() in HEAVY_CODECS


def make_proxy(source, info, folder):
    """Encode a 540p (short side) all-intra-ish H.264 proxy once; returns (path, meta)."""
    w, h = info['width'], info['height']
    short = min(w, h)
    scale = min(1.0, PROXY_SHORT / short)
    pw = max(2, int(round(w * scale / 2)) * 2)
    ph = max(2, int(round(h * scale / 2)) * 2)
    out = Path(folder) / f'proxy-{min(pw, ph)}p.mp4'
    gop = max(1, round(float(Fraction(info['fps']))))
    run([FFMPEG, '-v', 'error', '-y', '-i', source, '-an', '-sn', '-dn', '-map', '0:v:0',
         '-vf', f'scale={pw}:{ph}:flags=area', '-fps_mode', 'passthrough',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-g', str(gop),
         '-pix_fmt', 'yuv420p', out], capture=True)
    return out, {'file': out.name, 'width': pw, 'height': ph, 'codec': 'h264', 'crf': 18,
                 'keyframe_interval': gop,
                 'purpose': 'visual measurements only; probe, audio, OCR use the original'}


# ------------------------------------------------------- external sources ---

def ffmpeg_scene_scores(video, width):
    out = run([FFMPEG, '-v', 'error', '-i', video, '-an', '-vf',
               f"scale={width}:-2,select='gte(scene,0)',metadata=print:file=-", '-f', 'null', '-'],
              capture=True)
    return [float(x) for x in re.findall(r'lavfi\.scene_score=([0-9.]+)', out)]


def pyscenedetect_cuts(video, fps, threshold, min_scene_seconds):
    try:
        from scenedetect import detect, AdaptiveDetector
    except ImportError as exc:
        return [], f'PySceneDetect unavailable: {exc}'
    detector = AdaptiveDetector(adaptive_threshold=3.0, min_content_val=threshold,
                                min_scene_len=max(1, round(fps * min_scene_seconds)))
    scenes = detect(str(video), detector, show_progress=False)
    return [s.get_frames() for s, _ in scenes[1:]], None


# ------------------------------------------------------------- signals -----

def _edge_band(profile_mean, profile_std, tol_std=7.0, tol_mean=14.0):
    """Length of uniform-colour band from each end of a column/row profile."""
    n = len(profile_mean)
    out = []
    for order in (range(n), range(n - 1, -1, -1)):
        ref, length = None, 0
        for k in order:
            if profile_std[k] > tol_std:
                break
            if ref is None:
                ref = profile_mean[k]
            elif abs(profile_mean[k] - ref) > tol_mean:
                break
            length += 1
        out.append((length, float(ref) if ref is not None else -1.0))
    return out


def measure(video, fps, flow_every=None, progress=None):
    """Decode video sequentially and return per-frame signals (index i = change i-1 -> i)."""
    import cv2
    import numpy as np
    from .visual import fit_flow

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise OSError(f'Video açılamadı: {video}')
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if flow_every is None:
        flow_every = 1 if total <= 2400 else max(1, round(fps / 12))
    import os
    import threading
    from collections import deque
    from concurrent.futures import ThreadPoolExecutor
    local = threading.local()

    def flow_job(a, b):
        # OpenCV releases the GIL; one DIS instance per worker thread
        if not hasattr(local, 'dis'):
            local.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        return fit_flow(local.dis.calc(a, b, None), a)

    pool = ThreadPoolExecutor(max_workers=max(1, min(8, (os.cpu_count() or 2) - 1)))
    pending = deque()
    sig = {k: [] for k in ('hd', 'mad', 'sharp', 'luma', 'std', 'cw', 'ch', 'bands', 'flow')}
    thumbs, hists, profiles = [], [], []
    prev_gray = prev_hist = None
    size = thumb_size = None
    index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if size is None:
                h, w = frame.shape[:2]
                s = min(1.0, ANALYSIS_SHORT / min(w, h))
                size = (max(16, int(round(w * s / 2)) * 2), max(16, int(round(h * s / 2)) * 2))
                t = THUMB_SHORT / min(size)
                thumb_size = (max(8, round(size[0] * t)), max(8, round(size[1] * t)))
            small = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256]).ravel()
            hist /= max(1e-9, float(hist.sum()))
            col_m, col_s = gray.mean(0), gray.std(0)
            row_m, row_s = gray.mean(1), gray.std(1)
            profiles.append((col_m.astype('float32'), col_s.astype('float32'),
                             row_m.astype('float32'), row_s.astype('float32')))
            sig['sharp'].append(float(cv2.Laplacian(gray, cv2.CV_32F).var()))
            sig['luma'].append(float(gray.mean()))
            sig['std'].append(float(gray.std()))
            thumbs.append(cv2.resize(gray, thumb_size, interpolation=cv2.INTER_AREA))
            hists.append(hist)
            if prev_gray is None:
                sig['hd'].append(0.0)
                sig['mad'].append(0.0)
                sig['flow'].append(None)
            else:
                sig['hd'].append(float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)))
                sig['mad'].append(float(cv2.absdiff(prev_gray, gray).mean() / 255))
                sig['flow'].append(None)
                if index % flow_every == 0:
                    pending.append((index, pool.submit(flow_job, prev_gray, gray)))
                    while len(pending) > 48:
                        k, fut = pending.popleft()
                        sig['flow'][k] = fut.result()
            prev_gray, prev_hist = gray, hist
            index += 1
            if progress and index % 300 == 0:
                progress(index, total)
        while pending:
            k, fut = pending.popleft()
            sig['flow'][k] = fut.result()
    finally:
        cap.release()
        pool.shutdown(wait=True, cancel_futures=True)
    if not index:
        raise OSError(f'Video karesi okunamadı: {video}')
    # Edge bands: a column/row counts as backdrop when it is far flatter than this video's
    # typical picture (relative tolerance keeps low-contrast footage from reading as bands).
    base_std = _rolling_median(sig['std'], max(3, round(fps * 2)))
    sig['base_std'] = base_std
    for k, (col_m, col_s, row_m, row_s) in enumerate(profiles):
        tol = max(1.5, min(7.0, 0.3 * base_std[k]))
        (left, lc), (right, rc) = _edge_band(col_m, col_s, tol)
        (top, tc), (bottom, bc) = _edge_band(row_m, row_s, tol)
        W, H = len(col_m), len(row_m)
        sig['cw'].append(max(0.0, 1 - (left + right) / W))
        sig['ch'].append(max(0.0, 1 - (top + bottom) / H))
        sig['bands'].append((left / W, right / W, top / H, bottom / H, lc, rc, tc, bc))
    sig.update({'n': index, 'fps': fps, 'size': size, 'short': min(size), 'flow_every': flow_every,
                'thumbs': thumbs, 'hists': hists})
    return sig


# ----------------------------------------------------------- helpers -------

def _median(values, default=0.0):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else default


def _rolling_median(values, radius):
    n = len(values)
    return [_median(values[max(0, i - radius):min(n, i + radius + 1)]) for i in range(n)]


def _speed(sig):
    """Robust per-frame image speed (short sides / frame); interpolated where flow skipped."""
    short = sig['short']
    raw = [None if f is None else f['speed_median'] / short for f in sig['flow']]
    known = [i for i, v in enumerate(raw) if v is not None]
    if not known:
        return [0.0] * sig['n']
    out = []
    for i, v in enumerate(raw):
        if v is not None:
            out.append(v)
            continue
        lo = max((k for k in known if k < i), default=None)
        hi = min((k for k in known if k > i), default=None)
        out.append(raw[lo] if hi is None else raw[hi] if lo is None else
                   raw[lo] + (raw[hi] - raw[lo]) * (i - lo) / (hi - lo))
    return out


def _bhatt(a, b):
    import numpy as np
    return float(math.sqrt(max(0.0, 1 - float(np.sum(np.sqrt(a * b))))))


def _components(rows, short, fps):
    """Mean camera components (short sides/s) over flow fits."""
    rows = [r for r in rows if r and r.get('valid')]
    if not rows:
        return None
    pan = statistics.mean(-r['tx'] for r in rows) / short * fps
    tilt = statistics.mean(r['ty'] for r in rows) / short * fps
    zoom = statistics.mean(math.log(max(1e-6, r['scale'])) for r in rows) * fps
    radial = statistics.mean(r['radial_rate'] for r in rows) * fps
    return {'pan_right': pan, 'tilt_up': tilt, 'zoom_in': zoom, 'radial_in': radial}


def _burst_kind(comp):
    if comp is None:
        return 'whip', None
    trans = math.hypot(comp['pan_right'], comp['tilt_up'])
    radial = 0.5 * max(abs(comp['zoom_in']), abs(comp['radial_in']))
    if radial >= trans:
        sign = comp['radial_in'] if abs(comp['radial_in']) > abs(comp['zoom_in']) else comp['zoom_in']
        return 'zoom_burst', 'in' if sign > 0 else 'out'
    if abs(comp['pan_right']) >= abs(comp['tilt_up']):
        return 'whip', 'right' if comp['pan_right'] > 0 else 'left'
    return 'whip', 'up' if comp['tilt_up'] > 0 else 'down'


# ---------------------------------------------------------- detection ------

def detect_transitions(sig, ff_scores=None, psd_cuts=None):
    import numpy as np
    n, fps, short = sig['n'], sig['fps'], sig['short']
    ff = list(ff_scores or [])[:n] + [0.0] * max(0, n - len(ff_scores or []))
    psd = set(psd_cuts or [])
    hd, mad, sharp = sig['hd'], sig['mad'], sig['sharp']
    speed = _speed(sig)
    events, used = [], [False] * n

    def t(i):
        return round(i / fps, 6)

    def claim(a, b):
        for k in range(max(0, a), min(n, b + 1)):
            used[k] = True

    def free(a, b):
        return not any(used[max(0, a):min(n, b + 1)])

    def peak_evidence(a, b):
        a, b = max(0, a), min(n - 1, b)
        rng = range(a, b + 1)
        return {'hist_distance_max': round(max(hd[k] for k in rng), 4),
                'ffmpeg_scene_max': round(max(ff[k] for k in rng), 4),
                'mean_abs_diff_max': round(max(mad[k] for k in rng), 4),
                'pyscenedetect_cut': any(k in psd for k in range(a - 1, b + 2))}

    # 1. fades: (near-)uniform frames, extended while frames move monotonically toward them.
    blank = [sig['std'][i] < max(1.5, min(6.0, 0.25 * sig['base_std'][i])) for i in range(n)]
    i = 0
    while i < n:
        if not blank[i] or used[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and blank[j + 1] and mad[j + 1] < 0.03 and (hd[j + 1] < 0.1 or sig['luma'][j + 1] < 40):
            j += 1
        ref = sig['thumbs'][(i + j) // 2].astype('float32')
        dist = lambda k: float(np.abs(sig['thumbs'][k].astype('float32') - ref).mean())
        smooth = lambda k: mad[k] < 0.12 and (hd[k] < 0.3 or min(sig['luma'][k - 1], sig['luma'][k]) < 40)  # no cut
        a = i
        while a - 1 >= 0 and smooth(a) and dist(a - 1) > dist(a) * 1.03 + 0.5 and i - a < 3 * fps:
            a -= 1
        b = j
        while b + 1 < n and smooth(b + 1) and dist(b + 1) > dist(b) * 1.03 + 0.5 and b - j < 3 * fps:
            b += 1
        ramp_in, ramp_out = a < i, b > j
        if not ramp_in and not ramp_out and ((j - i + 1) > 0.5 * fps or i == 0 or j == n - 1):
            i = j + 1           # a solid-colour shot bounded by cuts, not a fade
            continue
        sub = 'dip_to_black' if ramp_in and ramp_out else 'fade_out' if ramp_in else 'fade_in' if ramp_out else 'blank'
        if i == 0:
            sub = 'fade_in'
        elif j == n - 1:
            sub = 'fade_out'
        colour = 'black' if sig['luma'][i] < 40 else 'white' if sig['luma'][i] > 215 else 'colour'
        conf = 0.9 if (ramp_in or ramp_out) else 0.6
        events.append({'type': 'fade', 'subtype': f'{sub}_{colour}' if colour != 'black' else sub,
                       'start_frame': a, 'end_frame': b, 'peak_frame': (i + j) // 2,
                       'confidence': conf, 'content_change': True,
                       'evidence': {**peak_evidence(a, b), 'uniform_frames': j - i + 1,
                                    'uniform_luma': round(sig['luma'][i], 1)},
                       'sources': ['uniform_frame', 'monotonic_approach']})
        claim(a, b)
        i = j + 1

    # 2. geometric transitions: uniform bands growing quickly from the frame edges
    #    (3D card flip around a vertical/horizontal axis, slide/push with a backdrop).
    radius = max(3, round(fps * 2))
    for axis in ('cw', 'ch'):
        base = _rolling_median(sig[axis], radius)
        g = [sig[axis][k] / max(1e-3, base[k]) for k in range(n)]
        i = 0
        while i < n:
            if g[i] >= 0.995 or used[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and g[j + 1] < 0.995 and not used[j + 1]:
                j += 1
            low_value = min(g[i:j + 1])
            plateau = [k for k in range(i, j + 1) if g[k] <= low_value + 0.01]
            low = plateau[len(plateau) // 2]
            jump = max(abs(g[k] - g[k - 1]) for k in range(max(1, i), j + 2) if k < n)
            bands = sig['bands'][low]
            sides = (bands[0], bands[1]) if axis == 'cw' else (bands[2], bands[3])
            colours = (bands[4], bands[5]) if axis == 'cw' else (bands[6], bands[7])
            band_std = _band_std(sig['thumbs'][low], bands)
            if not blank[low] and low_value < 0.8 and jump >= 0.08 and (j - i + 1) <= 2 * fps and band_std < max(1.5, min(8.0, 0.3 * sig['base_std'][low])):
                symmetric = min(sides) > 0 and max(sides) / max(1e-6, min(sides)) < 4 and                     abs(colours[0] - colours[1]) < 20
                kind = 'flip' if symmetric else 'wipe'
                sub = ('vertical_axis' if axis == 'cw' else 'horizontal_axis') if kind == 'flip' else                     ('horizontal' if axis == 'cw' else 'vertical') + '_slide'
                depth = 1 - low_value
                conf = min(0.97, 0.55 + 0.5 * depth) * (1.0 if kind == 'flip' else 0.85)
                a, b = i, j
                events.append({'type': kind, 'subtype': sub, 'start_frame': a, 'end_frame': b,
                               'peak_frame': low, 'confidence': round(conf, 3), 'content_change': True,
                               'evidence': {**peak_evidence(a, b), 'content_extent_min': round(low_value, 3),
                                            'max_extent_change_per_frame': round(jump, 3),
                                            'band_pixel_std': round(band_std, 2),
                                            'edge_bands_at_peak': {k: round(v, 3) for k, v in zip(
                                                ('left', 'right', 'top', 'bottom'), bands[:4])},
                                            'band_luma': [round(c, 1) for c in colours]},
                               'sources': ['edge_band_geometry', 'histogram', 'ffmpeg_scene']})
                claim(a, b)
            i = j + 1

    # 3. abrupt appearance changes (hard cut, or a cut hidden inside a motion-blur burst).
    rad = max(3, round(fps * 0.2))
    sharp_base = _rolling_median(sharp, max(3, round(fps)))
    candidates = []
    for k in range(1, n):
        if used[k]:
            continue
        neigh = hd[max(1, k - rad):k] + hd[k + 1:k + rad + 1]
        fneigh = ff[max(1, k - rad):k] + ff[k + 1:k + rad + 1]
        base = _median(neigh, 0.0)
        fbase = _median(fneigh, 0.0)
        hist_peak = hd[k] >= 0.22 and hd[k] >= 2.5 * base + 0.02 and hd[k] >= max(neigh or [0])
        ff_peak = ff[k] >= 0.3 and ff[k] >= 2.5 * fbase + 0.03 and ff[k] >= max(fneigh or [0])
        if hist_peak or ff_peak or (k in psd and (hd[k] >= 1.8 * base + 0.03 or ff[k] >= 0.15)):
            candidates.append((k, hist_peak, ff_peak))
    for k, hist_peak, ff_peak in candidates:
        if used[k]:
            continue
        ctx = [speed[x] for x in range(max(1, k - 3), min(n, k + 4)) if x != k]
        ctx_speed = max(ctx) if ctx else 0.0
        sharp_drop = (min(sharp[x] for x in range(max(0, k - 1), min(n, k + 2))) / sharp_base[k]
                      if sharp_base[k] > 5 else 1.0)          # flat frames carry no blur evidence
        agree = sum([hist_peak, ff_peak, k in psd, mad[k] >= 0.12])
        ev = {**peak_evidence(k, k), 'neighbour_flow_short_per_frame': round(ctx_speed, 4),
              'sharpness_ratio': round(sharp_drop, 3)}
        if ctx_speed >= BURST_SPEED * 0.8 or sharp_drop < 0.6:
            a, b = _burst_extent(speed, k, fps, used)
            comp = _components([sig['flow'][x] for x in range(a, b + 1) if x != k], short, fps)
            kind, direction = _burst_kind(comp)
            conf = min(0.95, 0.45 + 0.12 * agree + (0.1 if sharp_drop < 0.8 else 0))
            events.append({'type': kind, 'direction': direction, 'start_frame': a, 'end_frame': b,
                           'peak_frame': k, 'confidence': round(conf, 3), 'content_change': True,
                           'evidence': {**ev, 'camera_components_short_per_s': _round(comp)},
                           'sources': ['histogram' if hist_peak else None, 'ffmpeg_scene' if ff_peak else None,
                                       'pyscenedetect' if k in psd else None, 'optical_flow', 'sharpness']})
            claim(a, b)
        else:
            conf = min(0.97, 0.4 + 0.15 * agree + (0.1 if hd[k] > 0.4 else 0))
            events.append({'type': 'hard_cut', 'start_frame': k, 'end_frame': k, 'peak_frame': k,
                           'confidence': round(conf, 3), 'content_change': True, 'evidence': ev,
                           'sources': ['histogram' if hist_peak else None, 'ffmpeg_scene' if ff_peak else None,
                                       'pyscenedetect' if k in psd else None,
                                       'pixel_difference' if mad[k] >= 0.12 else None]})
            claim(k, k)

    # 4. motion bursts inside a shot (whip pan / zoom burst) with no appearance jump.
    sm = [_median(speed[max(0, k - 1):k + 2]) for k in range(n)]
    base = _rolling_median(sm, max(3, round(fps * 1.5)))
    k = 1
    while k < n:
        if used[k] or not (sm[k] >= BURST_SPEED and sm[k] >= 2.5 * base[k] + 0.002):
            k += 1
            continue
        j = k
        while j + 1 < n and not used[j + 1] and sm[j + 1] >= BURST_SPEED and sm[j + 1] >= 2.5 * base[j + 1] + 0.002:
            j += 1
        peak = max(range(k, j + 1), key=lambda x: sm[x])
        a, b = _burst_extent(sm, peak, fps, used)
        if (b - a + 1) / fps <= 1.0 and free(a, b):
            comp = _components([sig['flow'][x] for x in range(a, b + 1)], short, fps)
            kind, direction = _burst_kind(comp)
            sharp_drop = (min(sharp[x] for x in range(a, b + 1)) / sharp_base[peak]) if sharp_base[peak] > 5 else 1.0
            ratio = sm[peak] / max(1e-6, base[peak])
            conf = min(0.9, 0.35 + 0.1 * min(4, ratio / 2.5) + (0.15 if sharp_drop < 0.75 else 0))
            events.append({'type': kind, 'direction': direction, 'start_frame': a, 'end_frame': b,
                           'peak_frame': peak, 'confidence': round(conf, 3), 'content_change': False,
                           'evidence': {**peak_evidence(a, b), 'flow_peak_short_per_frame': round(sm[peak], 4),
                                        'flow_peak_to_baseline': round(ratio, 2),
                                        'sharpness_ratio': round(sharp_drop, 3),
                                        'camera_components_short_per_s': _round(comp)},
                           'sources': ['optical_flow', 'sharpness']})
            claim(a, b)
        k = max(j, b) + 1

    # 5. gradual changes without a single spike: dissolve (linear blend) or wipe (moving edge).
    for ev in _gradual(sig, used, hd, speed):
        a, b = ev['start_frame'], ev['end_frame']
        if free(a, b):
            ev['evidence'].update(peak_evidence(a, b))
            events.append(ev)
            claim(a, b)

    events.sort(key=lambda e: e['start_frame'])
    out = []
    for idx, e in enumerate(events, 1):
        e['sources'] = [s for s in e['sources'] if s]
        row = {'id': idx, 'type': e['type']}
        for key in ('subtype', 'direction'):
            if e.get(key):
                row[key] = e[key]
        row.update({'start': t(e['start_frame']), 'end': t(e['end_frame']),
                    'start_frame': e['start_frame'], 'end_frame': e['end_frame'],
                    'peak_frame': e['peak_frame'], 'peak_time': t(e['peak_frame']),
                    'duration': round((e['end_frame'] - e['start_frame'] + 1) / fps, 4),
                    'confidence': e['confidence'], 'content_change': e['content_change'],
                    'edit_boundary': e['type'] in EDIT_TYPES,
                    'evidence': e['evidence'], 'sources': e['sources']})
        out.append(row)
    return out


def _band_std(thumb, bands):
    import numpy as np
    h, w = thumb.shape
    l, r = int(round(bands[0] * w)), int(round(bands[1] * w))
    t, b = int(round(bands[2] * h)), int(round(bands[3] * h))
    parts = [thumb[:, :l], thumb[:, w - r:] if r else thumb[:, :0], thumb[:t], thumb[h - b:] if b else thumb[:0]]
    values = np.concatenate([x.ravel() for x in parts]).astype('float32')
    return float(values.std()) if values.size else 99.0


def _round(comp):
    return None if comp is None else {k: round(v, 4) for k, v in comp.items()}


def _burst_extent(speed, peak, fps, used):
    n = len(speed)
    level = max(0.012, 0.4 * speed[peak])
    limit = max(2, round(fps * 0.3))
    a = peak
    while a - 1 >= 1 and not used[a - 1] and speed[a - 1] >= level and peak - a < limit:
        a -= 1
    b = peak
    while b + 1 < n and not used[b + 1] and speed[b + 1] >= level and b - peak < limit:
        b += 1
    return a, b


def _gradual(sig, used, hd, speed):
    """Dissolve / wipe candidates from long-range histogram change, verified by blend fits."""
    import numpy as np
    n, fps = sig['n'], sig['fps']
    thumbs = sig['thumbs']
    found = []
    widths = sorted({max(2, round(fps * s)) for s in (0.15, 0.3, 0.6, 1.0)})
    for w in widths:
        long = [0.0] * n
        for i in range(w, n - w):
            long[i] = _bhatt(sig['hists'][i - w], sig['hists'][i + w])
        for i in range(w, n - w):
            if long[i] < 0.2 or long[i] < max(long[max(0, i - w):i + w + 1]):
                continue
            if max(hd[i - w + 1:i + w + 1]) > 0.6 * long[i]:
                continue           # a single spike explains it (handled as cut)
            window = speed[i - w:i + w + 1]
            if max(window) >= BURST_SPEED or sum(1 for v in window if v >= 0.02) >= 0.25 * len(window):
                continue           # sustained image motion: camera move, not a blend
            fit = _blend_fit(thumbs, i - w, i + w)
            if fit:
                fit['evidence']['long_range_hist_distance'] = round(long[i], 4)
                fit['evidence']['window_frames'] = 2 * w
                found.append(fit)
    # prefer the widest well-fitting window (a narrow window inside a long dissolve sees only part of it)
    found.sort(key=lambda e: (-(e['end_frame'] - e['start_frame']), -e['confidence'], e['start_frame']))
    chosen = []
    for e in found:
        if any(used[e['start_frame']:e['end_frame'] + 1]):
            continue
        touching = [c for c in chosen if c['type'] == e['type'] and
                    e['start_frame'] <= c['end_frame'] + 2 and e['end_frame'] >= c['start_frame'] - 2]
        if touching:
            c = touching[0]
            c['start_frame'] = min(c['start_frame'], e['start_frame'])
            c['end_frame'] = max(c['end_frame'], e['end_frame'])
            continue
        chosen.append(e)
    return chosen


def _blend_fit(thumbs, a, b):
    import numpy as np
    A = thumbs[a].astype('float32')
    B = thumbs[b].astype('float32')
    D = A - B
    norm = float((D * D).sum())
    if norm <= 1e-6 or float(np.abs(D).mean()) < 6:
        return None
    alphas, resid, wipe_p, wipe_r = [], [], [], []
    for k in range(a + 1, b):
        T = thumbs[k].astype('float32')
        alpha = float(((T - B) * D).sum() / norm)
        alpha = min(1.0, max(0.0, alpha))
        R = T - (alpha * A + (1 - alpha) * B)
        alphas.append(alpha)
        resid.append(float(np.abs(R).mean() / np.abs(D).mean()))
        eA, eB = np.abs(T - A), np.abs(T - B)
        best_p, best_r = None, 9.0
        for axis in (0, 1):
            ca, cb = eA.mean(axis), eB.mean(axis)
            mask = cb < ca
            changes = int(np.count_nonzero(mask[1:] != mask[:-1]))
            r = float(np.minimum(ca, cb).mean() / max(1e-6, np.abs(D).mean()))
            if changes <= 1 and r < best_r:
                best_p, best_r = float(mask.mean()), r
        wipe_p.append(best_p)
        wipe_r.append(best_r)
    if len(alphas) < 2:
        return None
    mono = sum(1 for x, y in zip(alphas, alphas[1:]) if y <= x + 0.03) / (len(alphas) - 1)
    span = alphas[0] - alphas[-1]
    med_res = statistics.median(resid)
    if med_res < 0.3 and mono >= 0.85 and span >= 0.5:
        idx = [k for k, al in zip(range(a + 1, b), alphas) if 0.04 < al < 0.96]
        s, e = (min(idx), max(idx)) if idx else (a + 1, b - 1)
        conf = round(max(0.3, min(0.95, (1 - med_res / 0.3) * 0.6 + mono * 0.35)), 3)
        mid = min(range(a + 1, b), key=lambda k: abs(alphas[k - a - 1] - 0.5))
        return {'type': 'dissolve', 'start_frame': s, 'end_frame': e, 'peak_frame': mid, 'confidence': conf,
                'content_change': True, 'sources': ['long_range_histogram', 'linear_blend_fit'],
                'evidence': {'blend_residual_median': round(med_res, 4), 'alpha_monotonic': round(mono, 3)}}
    if all(p is not None for p in wipe_p):
        wm = sum(1 for x, y in zip(wipe_p, wipe_p[1:]) if y >= x - 0.02) / (len(wipe_p) - 1)
        if statistics.median(wipe_r) < 0.25 and wm >= 0.85 and wipe_p[-1] - wipe_p[0] >= 0.5:
            idx = [k for k, p in zip(range(a + 1, b), wipe_p) if 0.02 < p < 0.98]
            s, e = (min(idx), max(idx)) if idx else (a + 1, b - 1)
            mid = min(range(a + 1, b), key=lambda k: abs(wipe_p[k - a - 1] - 0.5))
            return {'type': 'wipe', 'subtype': 'edge_wipe', 'start_frame': s, 'end_frame': e, 'peak_frame': mid,
                    'confidence': round(min(0.9, 0.5 + 0.4 * wm * (1 - statistics.median(wipe_r) / 0.25)), 3),
                    'content_change': True, 'sources': ['long_range_histogram', 'partition_fit'],
                    'evidence': {'partition_residual_median': round(statistics.median(wipe_r), 4),
                                 'partition_monotonic': round(wm, 3)}}
    return None


# ------------------------------------------------------------- scenes ------

def scenes_from_transitions(transitions, n_frames, fps, min_scene_seconds=0.3):
    """Old scenes.json schema; boundaries only at edit transitions (not in-shot whips)."""
    cuts = []
    for tr in transitions:
        if not tr['edit_boundary']:
            continue
        if tr['type'] == 'hard_cut':
            frame = tr['start_frame']
        elif tr['type'] == 'fade' and tr.get('subtype', '').startswith('fade_in') and tr['start_frame'] == 0:
            continue
        elif tr['type'] == 'fade' and tr.get('subtype', '').startswith('fade_out') and tr['end_frame'] >= n_frames - 1:
            continue
        else:
            frame = tr['peak_frame']
        if 0 < frame < n_frames:
            cuts.append((frame, tr))
    min_len = max(1, round(fps * min_scene_seconds))
    kept = []
    for frame, tr in sorted(cuts, key=lambda c: c[0]):
        if kept and frame - kept[-1][0] < min_len:
            if tr['confidence'] > kept[-1][1]['confidence']:
                kept[-1] = (frame, tr)
            continue
        if frame < min_len or n_frames - frame < min_len:
            continue
        kept.append((frame, tr))
    bounds = [0] + [f for f, _ in kept] + [n_frames]
    scenes = []
    for k in range(len(bounds) - 1):
        row = {'start': bounds[k] / fps, 'end': bounds[k + 1] / fps,
               'start_frame': bounds[k], 'end_frame': bounds[k + 1]}
        if k:
            tr = kept[k - 1][1]
            row['transition_in'] = {'id': tr['id'], 'type': tr['type'], 'start': tr['start'],
                                    'end': tr['end'], 'confidence': tr['confidence']}
        scenes.append(row)
    return scenes


def analyze_transitions(video, fps, scene_threshold=3.0, min_scene_seconds=0.3, progress=None):
    """Run every source on `video` (ideally the proxy). Returns (signals, transitions, report)."""
    sig = measure(video, fps, progress=progress)
    ff = ffmpeg_scene_scores(video, sig['size'][0])
    psd, psd_skip = pyscenedetect_cuts(video, fps, scene_threshold, min_scene_seconds)
    transitions = detect_transitions(sig, ff, psd)
    counts = {}
    for tr in transitions:
        counts[tr['type']] = counts.get(tr['type'], 0) + 1
    report = {
        'method': ('multi-source: HSV histogram Bhattacharyya distance, grey mean-abs-diff, ffmpeg scene score, '
                   'PySceneDetect AdaptiveDetector, uniform edge-band geometry (flip/slide), '
                   'linear-blend and partition fits (dissolve/wipe), DIS optical flow + Laplacian sharpness (whip/zoom burst)'),
        'confidence': ('heuristic 0-1 score per transition from agreeing sources and margin over thresholds; '
                       'checked on synthetic lavfi clips and one hand-annotated 3D reference, not a calibrated probability'),
        'analysis_size': list(sig['size']), 'frames_decoded': sig['n'], 'fps': fps,
        'flow_every_frames': sig['flow_every'],
        'types': {'hard_cut': 'single-frame appearance jump without motion blur',
                  'dissolve': 'frames fit a linear blend of the shots before/after',
                  'fade': 'frames approach a uniform (black/white) frame',
                  'flip': '3D card flip; uniform bands grow from both edges and the picture turns edge-on',
                  'wipe': 'moving straight edge or one-sided slide reveals the next shot',
                  'whip': 'fast translational camera move with motion blur (in-shot unless content_change)',
                  'zoom_burst': 'fast radial (push/pull) move with motion blur'},
        'edit_boundary': 'true types (hard_cut, dissolve, fade, flip, wipe) define scenes.json boundaries; '
                         'whip/zoom_burst stay in-shot. content_change=true marks a burst that hides an appearance jump.',
        'counts': counts,
        'sources': {'ffmpeg_scene_frames': len(ff), 'pyscenedetect_cuts': psd,
                    **({'pyscenedetect_skipped': psd_skip} if psd_skip else {})},
        'transitions': transitions,
    }
    return sig, transitions, report
