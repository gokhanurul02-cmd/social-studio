"""Composition measurement: subject box, framing, horizon, flat fills, edge cuts, shot type, crowd density.

    python -m social_studio.composition ANALYSIS_DIR [--video FILE] [--fps 3] [--out FILE]

Everything is a local, cheap *estimate* (numpy + OpenCV, no models, no new dependencies).  Each series carries
``method`` and ``confidence``.  The subject is not "recognised": it is the part of the frame that differs from
the per-row background colour and/or is spectrally salient (Hou & Zhang spectral residual, implemented in
numpy because ``cv2.saliency`` needs opencv-contrib).  Fails are expected on busy backgrounds, so the
numbers are for comparison between a reference and a candidate shot with the same pipeline, and every
flag still has to be confirmed on the frame.

Output: ``composition.json`` (schema ``social-studio.composition.v1``) = samples (time series), scenes,
segments, flags (flat_fill / edge_cut events with times), stats (distributions).
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

SCHEMA = 'social-studio.composition.v1'
WORK_WIDTH = 160            # analysis width in px (height follows the aspect)
SAMPLE_FPS = 3.0
MAX_SAMPLES = 150

# Heuristic gates; stylecheck re-exports/overrides them through its THRESHOLDS table.
LIMITS = {
    'flat_fill_ratio': 0.27,    # one low-texture, non-sky colour block covering >= 27 % of the frame (calibrated on the cybertruck reference: its largest legit block is 25 %)
    'edge_contact': 0.22,       # subject touches a frame border over >= 22 % of that border...
    'edge_area': 0.30,          # ...and covers >= 30 % of the frame (a small subject at the edge is fine)
    'wide_area': 0.08,          # subject area ratio < 8 % -> wide shot
    'close_area': 0.30,         # >= 30 % -> close-up, between -> medium
    'crowd_blobs': 40,          # >= 40 repeated small blobs -> crowd
    'min_flag_run': 2,          # samples in a row before a flag is reported (3 fps -> ~0.67 s)
}
POWER_POINTS = [(1 / 3, 1 / 3), (2 / 3, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 2 / 3)]


def _cv2():
    import cv2
    return cv2


# ----------------------------------------------------------------------------- per-frame measurement

def spectral_residual(gray):
    """Spectral residual saliency map in 0..1 (numpy implementation)."""
    cv2 = _cv2()
    g = cv2.resize(gray.astype(np.float32), (64, max(8, round(64 * gray.shape[0] / gray.shape[1]))))
    f = np.fft.fft2(g)
    log_amp = np.log(np.abs(f) + 1e-8)
    phase = np.angle(f)
    residual = log_amp - cv2.blur(log_amp, (3, 3))
    sal = np.abs(np.fft.ifft2(np.exp(residual + 1j * phase))) ** 2
    sal = cv2.GaussianBlur(sal.astype(np.float32), (0, 0), 2.0)
    sal = cv2.resize(sal, (gray.shape[1], gray.shape[0]))
    lo, hi = float(sal.min()), float(sal.max())
    return (sal - lo) / (hi - lo + 1e-9)


def row_background_distance(lab):
    """Distance of every pixel from the background colour of its own row.

    Background = median of the outer 14 % columns on both sides of that row (a subject wider than ~70 % of
    the frame therefore still reads as subject).  Rows whose side strips are themselves a different colour
    from the row median (subject touching the sides) fall back to the whole-row median.
    """
    w = lab.shape[1]
    k = max(2, int(0.14 * w))
    side = np.concatenate([lab[:, :k], lab[:, -k:]], axis=1)
    bg = np.median(side, axis=1, keepdims=True)
    return np.sqrt(((lab - bg) ** 2).sum(axis=2))


def subject_mask(bgr):
    """Return (mask uint8 0/1, method, confidence).  Largest salient/non-background blobs."""
    cv2 = _cv2()
    h, w = bgr.shape[:2]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab = cv2.GaussianBlur(lab, (0, 0), 1.2)
    dist = row_background_distance(lab)
    dist = np.clip(dist / 60.0, 0, 1)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    sal = spectral_residual(gray)
    score = np.clip(0.7 * dist + 0.3 * sal * (dist > 0.12), 0, 1)
    score8 = (score * 255).astype(np.uint8)
    thr, mask = cv2.threshold(score8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    floor = 0.34 * 255
    if thr < floor:
        mask = (score8 >= floor).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return np.zeros((h, w), np.uint8), 'row-median colour distance + spectral residual', 0.1
    areas = stats[1:, cv2.CC_STAT_AREA]
    big = areas.max()
    keep = [i + 1 for i, a in enumerate(areas) if a >= 0.25 * big and a >= 0.002 * h * w]
    out = np.isin(labels, keep).astype(np.uint8)
    frac = out.mean()
    conf = 0.75 if 0.005 < frac < 0.6 else 0.35   # a 'subject' that is nearly the whole frame is suspect
    return out, 'row-median colour distance + spectral residual (Otsu, largest blobs)', conf


def count_blobs(bgr, mask):
    """Repeated small blobs: connected components of a locally-contrasting layer (crowd density)."""
    cv2 = _cv2()
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    local = cv2.absdiff(gray, cv2.GaussianBlur(gray, (0, 0), 4.0))
    sub = local[mask > 0] if mask.any() else local.ravel()
    thr = max(10, float(np.percentile(sub, 60)))
    layer = (local >= thr).astype(np.uint8)
    if mask.any():
        layer &= cv2.dilate(mask, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(layer, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    small = areas[(areas >= 4) & (areas <= 0.01 * h * w)]
    return int(len(small))


def flat_fill(bgr):
    """Largest low-texture single-colour block.  Returns (ratio, ratio_incl_sky, info dict).

    Sky exemption: a bluish/bright block touching the top border is background, not a framing error.
    """
    cv2 = _cv2()
    h, w = bgr.shape[:2]
    blur = cv2.GaussianBlur(bgr, (0, 0), 1.0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 1.5)
    flat = (grad < 12.0).astype(np.uint8)
    # quantise colour so smooth gradients (sky) stay together, different hues separate
    q = (cv2.cvtColor(blur, cv2.COLOR_BGR2HSV))
    hue_bin = (q[:, :, 0] // 10).astype(np.int32)
    sat_bin = (q[:, :, 1] // 64).astype(np.int32)
    val_bin = (q[:, :, 2] // 48).astype(np.int32)
    key = hue_bin * 100 + sat_bin * 10 + val_bin
    best, best_sky, info = 0.0, 0.0, {}
    flat_pixels = flat > 0
    for code in np.unique(key[flat_pixels]):
        layer = ((key == code) & flat_pixels).astype(np.uint8)
        if layer.sum() < 0.03 * h * w:
            continue
        layer = cv2.morphologyEx(layer, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(layer, connectivity=4)
        for i in range(1, n):
            a = stats[i, cv2.CC_STAT_AREA]
            ratio = a / (h * w)
            if ratio < 0.03:
                continue
            x, y, bw, bh = (int(stats[i, c]) for c in (cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT))
            comp = labels == i
            b, g, r = (float(bgr[:, :, c][comp].mean()) for c in (0, 1, 2))
            hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0, 0]
            is_sky = (y <= 1 and 80 <= int(hsv[0]) <= 125 and int(hsv[2]) >= 120) or (y <= 1 and b > r + 25 and b > 140)
            best_sky = max(best_sky, ratio)
            if is_sky:
                continue
            if ratio > best:
                best = ratio
                info = {'bbox': [round(x / w, 3), round(y / h, 3), round(bw / w, 3), round(bh / h, 3)],
                        'rgb': '#%02x%02x%02x' % (int(r), int(g), int(b))}
    return float(best), float(best_sky), info


def horizon(bgr):
    """Horizon y/H from the strongest horizontal colour/luminance step in the row-mean profile and, when a
    long near-horizontal Hough line sits near it, that line.  Returns (y_ratio | None, confidence, method)."""
    cv2 = _cv2()
    h, w = bgr.shape[:2]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    prof = np.median(lab, axis=1)                          # h x 3, robust to a centred subject
    k = max(2, h // 40)
    step = np.zeros(h)
    for y in range(k, h - k):
        step[y] = np.linalg.norm(prof[y:y + k].mean(axis=0) - prof[y - k:y].mean(axis=0))
    lo, hi = int(0.08 * h), int(0.88 * h)
    seg = step[lo:hi]
    if seg.size == 0 or seg.max() < 4:
        return None, 0.0, 'row-median colour step (no clear step)'
    y = lo + int(np.argmax(seg))
    contrast = float(seg.max())
    conf = float(min(0.9, 0.3 + contrast / 40.0))
    method = 'row-median colour step'
    edges = cv2.Canny(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 40, 120)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=int(0.35 * w), minLineLength=int(0.5 * w), maxLineGap=6)
    if lines is not None:
        for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
            if abs(y2 - y1) <= 0.04 * abs(x2 - x1) and abs((y1 + y2) / 2 - y) <= 0.04 * h:
                y = int(round((y1 + y2) / 2))
                conf = min(0.95, conf + 0.1)
                method = 'row-median colour step + Hough line'
                break
    return round(y / h, 4), round(conf, 3), method


def classify_shot(area, blobs, th=LIMITS):
    if blobs >= th['crowd_blobs'] and area >= 0.02:
        return 'crowd'
    if area < th['wide_area']:
        return 'wide'
    if area < th['close_area']:
        return 'medium'
    return 'close'


def thirds_distance(cx, cy):
    return min(math.hypot(cx - px, cy - py) for px, py in POWER_POINTS)


def measure_frame(bgr, limits=LIMITS):
    """Composition numbers for one BGR frame (already downscaled)."""
    cv2 = _cv2()
    h, w = bgr.shape[:2]
    mask, method, conf = subject_mask(bgr)
    area = float(mask.mean())
    ys, xs = np.nonzero(mask)
    rec = {'subject_area': round(area, 4), 'subject_method': method, 'subject_confidence': round(conf, 2)}
    if len(xs) >= 4:
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        cx, cy = float(xs.mean()) / w, float(ys.mean()) / h
        rec.update({'subject_bbox': [round(x0 / w, 4), round(y0 / h, 4), round((x1 - x0) / w, 4), round((y1 - y0) / h, 4)],
                    'centroid': [round(cx, 4), round(cy, 4)], 'thirds_distance': round(thirds_distance(cx, cy), 4)})
        contact = {'left': float(mask[:, 0].mean()), 'right': float(mask[:, -1].mean()),
                   'top': float(mask[0, :].mean()), 'bottom': float(mask[-1, :].mean())}
        # a subject standing on the bottom edge (floor contact) is normal for a small figure; the gate needs area too
        worst = max(contact, key=contact.get)
        rec['edge_contact'] = {k: round(v, 3) for k, v in contact.items()}
        rec['edge_worst'] = worst
        rec['edge_cut'] = bool(contact[worst] >= limits['edge_contact'] and area >= limits['edge_area'])
    else:
        rec.update({'subject_bbox': None, 'centroid': None, 'thirds_distance': None,
                    'edge_contact': None, 'edge_worst': None, 'edge_cut': False})
    blobs = count_blobs(bgr, mask)
    rec['blob_count'] = blobs
    fill, fill_sky, info = flat_fill(bgr)
    rec['flat_fill_ratio'] = round(fill, 4)
    rec['flat_fill_ratio_incl_sky'] = round(fill_sky, 4)
    if info:
        rec['flat_fill_block'] = info
    ho, hconf, hmethod = horizon(bgr)
    rec['horizon_y'] = ho if hconf >= 0.4 else None
    rec['horizon_confidence'] = hconf
    rec['shot_type'] = classify_shot(area, blobs, limits)
    if rec['shot_type'] == 'crowd' and rec['edge_cut']:
        rec['edge_cut'] = False          # a crowd carpet legitimately runs off the frame
        rec['edge_cut_suppressed'] = 'crowd'
    rec['shot_confidence'] = round(min(conf, 0.7), 2)
    return rec


# ----------------------------------------------------------------------------- video sampling

def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return None


def sample_times(duration, fps_sample=SAMPLE_FPS, max_samples=MAX_SAMPLES):
    n = max(1, min(max_samples, int(math.floor(duration * fps_sample)) + 1))
    step = duration / n if n else 0
    return [round((i + 0.5) * step, 3) for i in range(n)] if duration > 0 else [0.0]


def read_frames(video, times, fps, width=WORK_WIDTH):
    """Yield (t, bgr) for the nearest frame of each time; one sequential decode."""
    cv2 = _cv2()
    cap = cv2.VideoCapture(str(video))
    wanted = {}
    for t in times:
        wanted.setdefault(int(round(t * fps)), []).append(t)
    idx, last = 0, max(wanted) if wanted else -1
    try:
        while idx <= last and cap.grab():
            if idx in wanted:
                ok, img = cap.retrieve()
                if ok:
                    h, w = img.shape[:2]
                    img = cv2.resize(img, (width, max(2, round(h * width / w))), interpolation=cv2.INTER_AREA)
                    for t in wanted[idx]:
                        yield t, img
            idx += 1
    finally:
        cap.release()


def frame_at(video, t, width=WORK_WIDTH):
    cv2 = _cv2()
    cap = cv2.VideoCapture(str(video))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, img = cap.read()
    finally:
        cap.release()
    if not ok:
        return None
    h, w = img.shape[:2]
    return cv2.resize(img, (width, max(2, round(h * width / w))), interpolation=cv2.INTER_AREA)


def _quart(values):
    v = sorted(x for x in values if x is not None)
    if not v:
        return None
    q = lambda p: float(np.percentile(v, p))
    return {'median': round(q(50), 4), 'q1': round(q(25), 4), 'q3': round(q(75), 4), 'iqr': round(q(75) - q(25), 4),
            'min': round(v[0], 4), 'max': round(v[-1], 4), 'n': len(v)}


def _runs(samples, key, min_run, limit_key=None):
    """Merge consecutive flagged samples into [t_start, t_end, peak] events."""
    events, cur = [], None
    step = None
    if len(samples) > 1:
        step = float(np.median(np.diff([s['t'] for s in samples])))
    for s in samples:
        v = s.get(key)
        flagged = bool(v) if not isinstance(v, (int, float)) or isinstance(v, bool) else v >= (limit_key or 0)
        if flagged:
            if cur is None:
                cur = {'t_start': s['t'], 't_end': s['t'], 'n': 0, 'peak': 0.0, 'samples': []}
            cur['t_end'] = s['t']
            cur['n'] += 1
            cur['peak'] = max(cur['peak'], float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 1.0)
            cur['samples'].append(s['t'])
        elif cur:
            events.append(cur)
            cur = None
    if cur:
        events.append(cur)
    half = (step or 0.33) / 2
    out = []
    for e in events:
        if e['n'] >= min_run or (len(samples) <= 3):
            out.append({'t_start': round(max(0.0, e['t_start'] - half), 3), 't_end': round(e['t_end'] + half, 3),
                        'peak': round(e['peak'], 3), 'samples': e['n']})
    return out


def summarize(samples, duration, scenes, limits=LIMITS):
    shots = {}
    for s in samples:
        shots[s['shot_type']] = shots.get(s['shot_type'], 0) + 1
    n = len(samples) or 1
    thirds = [s['thirds_distance'] for s in samples if s.get('thirds_distance') is not None]
    cents = [s['centroid'] for s in samples if s.get('centroid')]
    stats = {
        'shot_type_share': {k: round(v / n, 3) for k, v in sorted(shots.items())},
        'subject_area': _quart([s['subject_area'] for s in samples]),
        'horizon_y': _quart([s['horizon_y'] for s in samples]),
        'horizon_detected_share': round(sum(s['horizon_y'] is not None for s in samples) / n, 3),
        'centroid_x': _quart([c[0] for c in cents]),
        'centroid_y': _quart([c[1] for c in cents]),
        'thirds_distance': _quart(thirds),
        'centered_share': round(sum(abs(c[0] - 0.5) <= 0.12 for c in cents) / max(1, len(cents)), 3),
        'flat_fill_ratio': _quart([s['flat_fill_ratio'] for s in samples]),
        'flat_fill_samples_over_limit': sum(s['flat_fill_ratio'] >= limits['flat_fill_ratio'] for s in samples),
        'edge_cut_samples': sum(bool(s.get('edge_cut')) for s in samples),
        'crowd_blob_count': _quart([s['blob_count'] for s in samples]),
        'sample_count': len(samples),
    }
    flags = {'flat_fill': _runs(samples, 'flat_fill_ratio', limits['min_flag_run'], limits['flat_fill_ratio']),
             'edge_cut': _runs(samples, 'edge_cut', limits['min_flag_run'])}
    for ev in flags['edge_cut']:
        near = [s for s in samples if ev['t_start'] <= s['t'] <= ev['t_end'] and s.get('edge_cut')]
        if near:
            ev['side'] = max(set(x['edge_worst'] for x in near), key=[x['edge_worst'] for x in near].count)
            ev['peak'] = round(max(x['edge_contact'][x['edge_worst']] for x in near), 3)
            ev['subject_area'] = round(float(np.median([x['subject_area'] for x in near])), 3)
    scene_rows = []
    for i, sc in enumerate(scenes or []):
        a, b = float(sc.get('start', 0)), float(sc.get('end', duration))
        inside = [s for s in samples if a <= s['t'] < b] or [min(samples, key=lambda s: abs(s['t'] - (a + b) / 2))] if samples else []
        if not inside:
            continue
        st = [s['shot_type'] for s in inside]
        scene_rows.append({'scene': i, 'start': round(a, 3), 'end': round(b, 3), 'samples': len(inside),
                           'shot_type': max(set(st), key=st.count),
                           'subject_area_median': round(float(np.median([s['subject_area'] for s in inside])), 4),
                           'flat_fill_max': round(max(s['flat_fill_ratio'] for s in inside), 3),
                           'edge_cut_samples': sum(bool(s.get('edge_cut')) for s in inside)})
    segments, cur = [], None
    for s in samples:
        if cur and cur['shot_type'] == s['shot_type']:
            cur['end'] = s['t']
            cur['_a'].append(s['subject_area'])
        else:
            if cur:
                segments.append(cur)
            cur = {'start': s['t'], 'end': s['t'], 'shot_type': s['shot_type'], '_a': [s['subject_area']]}
    if cur:
        segments.append(cur)
    for g in segments:
        g['subject_area_median'] = round(float(np.median(g.pop('_a'))), 4)
        g['start'], g['end'] = round(g['start'], 3), round(g['end'], 3)
    return stats, flags, scene_rows, segments


def analyze_composition(job, video=None, out=None, fps_sample=SAMPLE_FPS, limits=None):
    """Measure composition for an analysis folder.  ``video``: proxy-540p.mp4 > source in analysis.json."""
    limits = dict(LIMITS, **(limits or {}))
    job = Path(job)
    analysis = _read_json(job / 'analysis.json') or {}
    info = analysis.get('video', {})
    if video is None:
        for cand in (job / 'proxy-540p.mp4', Path(analysis.get('source', ''))):
            if cand and Path(cand).is_file():
                video = cand
                break
    out = Path(out) if out else job / 'composition.json'
    if video is None:
        report = {'schema': SCHEMA, 'skipped': 'no video file (proxy or source) found', 'samples': []}
        out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
        return report
    try:
        fps = float(Fraction(str(info.get('fps', 30))))
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    duration = float(info.get('duration') or 0)
    if duration <= 0:
        import cv2
        cap = cv2.VideoCapture(str(video))
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or fps)
        cap.release()
    times = sample_times(duration, fps_sample)
    samples = []
    for t, img in read_frames(video, times, fps):
        rec = measure_frame(img, limits)
        rec['t'] = t
        samples.append(rec)
    scenes = _read_json(job / 'scenes.json')
    if isinstance(scenes, dict):
        scenes = scenes.get('scenes')
    stats, flags, scene_rows, segments = summarize(samples, duration, scenes, limits)
    report = {
        'schema': SCHEMA,
        'method': ('local estimates at ~%g fps from %s: subject = row-median colour distance + spectral residual saliency '
                   '(numpy), horizon = row-median colour step (+Hough), flat fill = largest low-gradient single-colour block '
                   'excluding sky, shot type from subject area + repeated blob count' % (fps_sample, Path(video).name)),
        'confidence': 'estimate: 0.35-0.75 per sample (see samples[].subject_confidence); confirm flags on the frame',
        'video': str(video), 'duration': duration, 'sample_fps': fps_sample, 'work_width': WORK_WIDTH,
        'limits': limits, 'stats': stats, 'flags': flags, 'scenes': scene_rows, 'segments': segments,
        'samples': samples,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return report


def load_composition(job):
    data = _read_json(Path(job) / 'composition.json')
    return data if isinstance(data, dict) and data.get('samples') else None


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Composition measurement for an analysis folder')
    ap.add_argument('analysis_dir')
    ap.add_argument('--video')
    ap.add_argument('--fps', type=float, default=SAMPLE_FPS)
    ap.add_argument('--out')
    a = ap.parse_args()
    rep = analyze_composition(a.analysis_dir, a.video, a.out, a.fps)
    if rep.get('skipped'):
        raise SystemExit(rep['skipped'])
    print(json.dumps({'stats': rep['stats'], 'flags': rep['flags']}, ensure_ascii=False, indent=1))
