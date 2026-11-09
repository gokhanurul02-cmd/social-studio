"""Scene palettes, cut statistics and camera-motion estimates from dense optical flow.

Camera conventions (image y points down):
- pan_right > 0  : picture content moves left  (camera turns/trucks right)
- tilt_up   > 0  : picture content moves down  (camera tilts up or pedestals up)
- zoom_in   > 0  : content expands from the centre (zoom in or dolly in)
- roll_cw   > 0  : content rotates counter-clockwise on screen
Rates are in short sides per second (translation), log-scale per second (zoom) and
degrees per second (roll).  Object motion, parallax and motion blur can imitate camera
moves; every estimate carries a confidence score and the evidence it is built from.
"""
import math
import statistics

from .media import save

STATIC_LIMIT = 0.04        # short sides / s of camera-model motion considered static
FAMILY_LABELS = {'pan': ('pan_right', 'pan_left'), 'tilt': ('tilt_up', 'tilt_down'),
                 'zoom': ('zoom_in', 'zoom_out'), 'roll': ('roll_cw', 'roll_ccw')}
RATE_KEY = {'pan': 'pan_right', 'tilt': 'tilt_up', 'zoom': 'zoom_in', 'dolly': 'zoom_in', 'roll': 'roll_cw'}


# ------------------------------------------------------------ flow fit -----

def fit_flow(flow, prev_gray, step=8, max_points=700):
    """Fit a similarity transform to textured flow vectors; return compact numbers."""
    import cv2
    import numpy as np
    h, w = flow.shape[:2]
    short = min(h, w)
    my, mx = max(2, round(h * 0.04)), max(2, round(w * 0.04))
    yy, xx = np.mgrid[my:h - my:step, mx:w - mx:step]
    gx = cv2.Sobel(prev_gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(prev_gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 2)[yy, xx].ravel()
    vec = flow[yy, xx].reshape(-1, 2)
    pts = np.column_stack([xx.ravel(), yy.ravel()]).astype('float32')
    mags = np.linalg.norm(vec, axis=1)
    out = {'speed_median': float(np.median(mags)), 'speed_mean': float(mags.mean()),
           'valid': False, 'tx': 0.0, 'ty': 0.0, 'scale': 1.0, 'rot': 0.0, 'inliers': 0.0,
           'textured_points': 0, 'radial_rate': 0.0, 'radial_spread': None,
           'model': None, 'inliers_similarity': 0.0, 'inliers_homography': 0.0}
    textured = grad > max(6.0, float(np.percentile(grad, 40)))
    if textured.sum() < 40:
        return out
    pts, vec = pts[textured], vec[textured]
    if len(pts) > max_points:
        keep = np.linspace(0, len(pts) - 1, max_points).astype(int)
        pts, vec = pts[keep], vec[keep]
    out['speed_median'] = float(np.median(np.linalg.norm(vec, axis=1)))
    out['textured_points'] = int(textured.sum())
    thr = max(0.75, 0.2 * out['speed_median'])
    matrix, inl = cv2.estimateAffinePartial2D(pts, pts + vec, method=cv2.RANSAC,
                                              ransacReprojThreshold=thr, maxIters=300,
                                              confidence=0.99, refineIters=10)
    hom, inl_h = cv2.findHomography(pts, pts + vec, cv2.RANSAC, max(1.0, thr), maxIters=300, confidence=0.99)
    c = np.array([w / 2, h / 2])
    r = pts - c
    rn2 = (r * r).sum(1)
    far = rn2 > (0.2 * short) ** 2
    q = ((vec * r).sum(1) / np.maximum(rn2, 1))[far]
    if q.size >= 20:
        med = float(np.median(q))
        iqr = float(np.percentile(q, 75) - np.percentile(q, 25))
        out['radial_rate'] = med
        out['radial_spread'] = iqr / max(abs(med), 1e-4) if abs(med) > 2e-4 else None
    sim_in = float(inl.mean()) if matrix is not None and inl is not None else 0.0
    hom_in = float(inl_h.mean()) if hom is not None and inl_h is not None else 0.0
    out['inliers_similarity'], out['inliers_homography'] = sim_in, hom_in
    if matrix is not None and sim_in >= 0.5 or (matrix is not None and sim_in >= hom_in - 0.1):
        t = matrix[:, :2] @ c + matrix[:, 2] - c
        out.update({'valid': True, 'model': 'similarity', 'tx': float(t[0]), 'ty': float(t[1]),
                    'scale': float(math.hypot(matrix[0, 0], matrix[1, 0])),
                    'rot': float(math.atan2(matrix[1, 0], matrix[0, 0])), 'inliers': sim_in})
    elif hom is not None:
        # perspective / parallax-consistent motion (e.g. dolly or pedestal over a ground plane):
        # summarise the homography's flow field as translation, radial scale and rotation.
        grid = np.array([[x, y] for y in np.linspace(0.1 * h, 0.9 * h, 9) for x in np.linspace(0.1 * w, 0.9 * w, 7)],
                        dtype='float32')
        moved = cv2.perspectiveTransform(grid[None], hom)[0]
        dv = moved - grid
        centre = cv2.perspectiveTransform(c.reshape(1, 1, 2).astype('float32'), hom)[0, 0] - c
        rr = grid - c
        n2 = np.maximum((rr * rr).sum(1), 1)
        radial = float(np.median((dv * rr).sum(1) / n2))
        tangential = float(np.median((rr[:, 0] * dv[:, 1] - rr[:, 1] * dv[:, 0]) / n2))
        out.update({'valid': True, 'model': 'homography', 'tx': float(centre[0]), 'ty': float(centre[1]),
                    'scale': float(math.exp(radial)), 'rot': tangential, 'inliers': hom_in})
    return out


def motion_estimate(previous, current, dt):
    """Legacy single-pair API kept for compatibility. Labels follow the OLD convention:
    the direction the picture content moves (content moving right -> 'pan_right').
    New code should use camera_analysis / camera_segments (camera-direction convention)."""
    import cv2
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    fit = fit_flow(dis.calc(previous, current, None), previous)
    h, w = previous.shape[:2]
    magnitude = fit['speed_median'] / dt
    label = 'mixed'
    if magnitude < .25:
        label = 'static'
    elif fit['valid'] and fit['inliers'] > .5:
        shift = max(abs(fit['tx']), abs(fit['ty']))
        if abs(math.log(fit['scale'])) * min(h, w) / 2 > max(shift, .25):
            label = 'zoom_in' if fit['scale'] > 1 else 'zoom_out'
        elif shift > .25:
            if abs(fit['tx']) > abs(fit['ty']):
                label = 'pan_right' if fit['tx'] > 0 else 'pan_left'
            else:
                label = 'tilt_down' if fit['ty'] > 0 else 'tilt_up'
    return {'magnitude_px_per_s': magnitude, 'magnitude_frame_width_per_s': magnitude / w,
            'camera_estimate': label, 'scale': fit['scale'], 'confidence': fit['inliers'],
            'confidence_kind': 'model inlier fraction, not calibrated probability',
            'method': 'DIS flow and RANSAC similarity fit (legacy content-direction labels)'}


def rates(fit, short, fps):
    """Camera rates per second from one consecutive-frame flow fit."""
    return {'pan_right': -fit['tx'] / short * fps,
            'tilt_up': fit['ty'] / short * fps,
            'zoom_in': math.log(max(1e-6, fit['scale'])) * fps,
            'roll_cw': -math.degrees(fit['rot']) * fps}


def classify(fit, short, fps):
    """Label one flow sample; returns (label, family, components, confidence, note)."""
    speed = fit['speed_median'] / short * fps
    if not fit['valid']:
        if speed < STATIC_LIMIT:
            return 'static', 'static', {}, 0.4, 'few textured points; low image motion'
        return 'complex', 'complex', {}, 0.2, 'too few textured points for a camera model'
    r = rates(fit, short, fps)
    radial = fit['radial_rate'] * fps
    zoom_like = r['zoom_in'] if abs(r['zoom_in']) >= 0.5 * abs(radial) else radial
    # displacement at half a short side from the centre, in short sides / s
    # roll only from the rigid (similarity) model and only at plausible rates; perspective
    # models and aliased repetitive textures produce spurious rotation.
    roll_ok = fit.get('model') == 'similarity' and abs(r['roll_cw']) <= 90
    comps = {'pan': abs(r['pan_right']), 'tilt': abs(r['tilt_up']),
             'zoom': 0.5 * abs(zoom_like), 'roll': 0.5 * math.radians(abs(r['roll_cw'])) if roll_ok else 0.0}
    primary = max(comps, key=comps.get)
    if comps[primary] < STATIC_LIMIT and (speed < 2 * STATIC_LIMIT or fit['inliers'] >= 0.5):
        conf = min(0.95, 0.5 + 0.45 * min(1.0, fit['inliers'])) * (1.0 if speed < 2 * STATIC_LIMIT else 0.8)
        return 'static', 'static', comps, round(conf, 3),             'camera-model motion below 0.04 short sides/s' + ('' if speed < 2 * STATIC_LIMIT else '; objects move')
    if fit['inliers'] < 0.3:
        return 'complex', 'complex', comps, round(0.3 + 0.4 * (1 - fit['inliers']), 3), \
            'flow does not fit one camera model (object motion, parallax or blur)'
    q_fit = min(1.0, max(0.0, (fit['inliers'] - 0.25) / 0.5))
    q_mag = min(1.0, max(0.0, (comps[primary] - STATIC_LIMIT) / 0.12))
    second = sorted(comps.values())[-2]
    q_dom = min(1.0, max(0.0, (comps[primary] - second) / max(1e-6, comps[primary]) * 1.6))
    conf = q_fit * (0.4 + 0.6 * q_mag) * (0.5 + 0.5 * q_dom)
    sign = {'pan': r['pan_right'], 'tilt': r['tilt_up'], 'zoom': zoom_like, 'roll': r['roll_cw']}[primary]
    label = FAMILY_LABELS[primary][0 if sign > 0 else 1]
    note = 'perspective (homography) model: parallax-consistent move' if fit.get('model') == 'homography' else ''
    if fit.get('model') == 'homography':
        conf *= 0.85
    if primary == 'zoom' and fit['radial_spread'] is not None and fit['radial_spread'] > 0.8:
        label = label.replace('zoom', 'dolly')
        note = (note + '; ' if note else '') + 'radial flow varies with depth (parallax): dolly-like'
    return label, primary, comps, round(conf, 3), note


# --------------------------------------------------------- segments --------

def _easing(values):
    if len(values) < 4:
        return 'unknown'
    v = [abs(x) for x in values]
    mean = statistics.mean(v)
    if mean <= 0:
        return 'unknown'
    if max(v) / mean < 1.3:
        return 'linear'
    n = len(v)
    centroid = sum(i / (n - 1) * x for i, x in enumerate(v)) / sum(v)
    third = max(1, n // 3)
    head, tail = statistics.mean(v[:third]), statistics.mean(v[-third:])
    mid = statistics.mean(v[third:n - third] or v)
    if mid > 1.25 * head and mid > 1.25 * tail:
        return 'ease_in_out'
    if centroid < 0.45:
        return 'ease_out'
    if centroid > 0.55:
        return 'ease_in'
    return 'ease_in_out'


def camera_analysis(sig, scenes, transitions, min_segment=0.3):
    """Per-sample labels and merged camera segments (split at edit transitions)."""
    fps, short, n, every = sig['fps'], sig['short'], sig['n'], sig['flow_every']
    blocked = set()
    for tr in transitions:
        # flow is meaningless across an edit transition or across a cut hidden in a burst
        if tr['edit_boundary']:
            blocked.update(range(tr['start_frame'], tr['end_frame'] + 2))
        elif tr.get('content_change'):
            blocked.add(tr['peak_frame'])
    scene_of = [0] * n
    for idx, sc in enumerate(scenes):
        for f in range(max(0, sc['start_frame']), min(n, sc['end_frame'])):
            scene_of[f] = idx
    # continuity zones: split at scene boundaries and at bursts that hide a content change
    splits = {tr['peak_frame'] for tr in transitions if tr.get('content_change') and not tr['edit_boundary']}
    zone_of, zone = [0] * n, 0
    for f in range(n):
        if f and (scene_of[f] != scene_of[f - 1] or f in splits):
            zone += 1
        zone_of[f] = zone
    frames = [f for f in range(1, n) if sig['flow'][f] is not None and f not in blocked
              and zone_of[f] == zone_of[f - 1]]
    samples = []
    for pos, f in enumerate(frames):
        # running median over +-2 samples suppresses flow aliasing on repetitive textures
        near = [sig['flow'][g] for g in frames[max(0, pos - 2):pos + 3]
                if zone_of[g] == zone_of[f] and abs(g - f) <= 2 * every + 1]
        fit = dict(sig['flow'][f])
        valid = [x for x in near if x['valid']]
        if fit['valid'] and len(valid) >= 2:
            for key in ('tx', 'ty', 'rot', 'radial_rate', 'inliers'):
                fit[key] = statistics.median(x[key] for x in valid)
            fit['scale'] = math.exp(statistics.median(math.log(max(1e-6, x['scale'])) for x in valid))
        fit['speed_median'] = statistics.median(x['speed_median'] for x in near)
        label, family, comps, conf, note = classify(fit, short, fps)
        samples.append({'frame': f, 'time': round(f / fps, 4), 'label': label, 'family': family,
                        'rates': {k: round(v, 4) for k, v in rates(fit, short, fps).items()},
                        'components': {k: round(v, 4) for k, v in comps.items()},
                        'speed_short_per_s': round(fit['speed_median'] / short * fps, 4),
                        'inliers': round(fit['inliers'], 3), 'confidence': conf,
                        **({'note': note} if note else {}), 'scene': scene_of[f], 'zone': zone_of[f]})
    if not samples:
        return samples, []
    gap = 3 * every + 1
    groups = [s['label'].replace('dolly', 'zoom') for s in samples]
    k = max(1, round(0.2 * fps / every))
    smooth = []
    for i, s in enumerate(samples):
        window = [groups[j] for j in range(max(0, i - k), min(len(samples), i + k + 1))
                  if samples[j]['zone'] == s['zone'] and abs(samples[j]['frame'] - s['frame']) <= k * every + gap]
        smooth.append(max(set(window), key=lambda x: (window.count(x), x == groups[i])))
    runs = []
    for i, s in enumerate(samples):
        split = not runs or s['frame'] - samples[runs[-1]['idx'][-1]]['frame'] > gap or s['zone'] != runs[-1]['zone']
        if not split and runs[-1]['label'] == smooth[i]:
            runs[-1]['idx'].append(i)
        else:
            runs.append({'label': smooth[i], 'idx': [i], 'scene': s['scene'], 'zone': s['zone']})

    def adjacent(a, b):
        first, second = (a, b) if a['idx'][0] < b['idx'][0] else (b, a)
        return first['zone'] == second['zone'] and \
            samples[second['idx'][0]]['frame'] - samples[first['idx'][-1]]['frame'] <= gap

    min_samples = max(2, round(min_segment * fps / every))
    while True:
        small = [i for i, r in enumerate(runs) if len(r['idx']) < min_samples and not r.get('keep')]
        if not small:
            break
        s = min(small, key=lambda i: len(runs[i]['idx']))
        cand = [j for j in (s - 1, s + 1) if 0 <= j < len(runs) and adjacent(runs[j], runs[s])]
        if not cand:
            runs[s]['keep'] = True
            continue
        same = [j for j in cand if runs[j]['label'].split('_')[0] == runs[s]['label'].split('_')[0]]
        target = max(same or cand, key=lambda j: len(runs[j]['idx']))
        lo, hi = sorted((s, target))
        runs[lo] = {'label': runs[target]['label'], 'idx': runs[lo]['idx'] + runs[hi]['idx'],
                    'scene': runs[lo]['scene'], 'zone': runs[lo]['zone'], 'keep': runs[target].get('keep', False)}
        del runs[hi]
    merged = []
    for r in runs:
        if merged and merged[-1]['label'] == r['label'] and adjacent(merged[-1], r):
            merged[-1]['idx'] += r['idx']
        else:
            merged.append(r)
    return samples, [_segment(samples, r, fps, every) for r in merged]


def _segment(samples, run, fps, every):
    rows = [samples[i] for i in run['idx']]
    label = run['label']
    family = label.split('_')[0] if label not in ('static', 'complex') else label
    agree = sum(1 for s in rows if s['label'].replace('dolly', 'zoom') == label) / len(rows)
    if family == 'zoom' and sum(1 for s in rows if s['label'].startswith('dolly')) > len(rows) / 2:
        label, family = label.replace('zoom', 'dolly'), 'dolly'
    mean_rates = {k: round(statistics.mean(s['rates'][k] for s in rows), 4) for k in rows[0]['rates']}
    key = RATE_KEY.get(family)
    series = [(s['time'], abs(s['rates'][key]) if key else s['speed_short_per_s']) for s in rows]
    span = rows[-1]['time'] - rows[0]['time']
    step = max(1, round(len(series) / max(1, span * 10 + 1)))
    values = [v for _, v in series]
    secondary = []
    base = family.replace('dolly', 'zoom')
    if family not in ('static', 'complex'):
        prim_c = statistics.mean(s['components'].get(base, 0) for s in rows)
        for fam in ('pan', 'tilt', 'zoom', 'roll'):
            if fam == base:
                continue
            mean_c = statistics.mean(s['components'].get(fam, 0) for s in rows)
            if prim_c > 0 and mean_c >= 0.4 * prim_c and mean_c > STATIC_LIMIT:
                secondary.append(FAMILY_LABELS[fam][0 if mean_rates[RATE_KEY[fam]] > 0 else 1])
    duration = (rows[-1]['frame'] - rows[0]['frame'] + every) / fps
    mean_conf = statistics.mean(s['confidence'] for s in rows)
    length_q = min(1.0, duration / 0.6)
    conf = round(mean_conf * (0.5 + 0.5 * agree) * (0.6 + 0.4 * length_q), 3)
    return {'start': round((rows[0]['frame'] - every) / fps, 4), 'end': round(rows[-1]['frame'] / fps, 4),
            'start_frame': rows[0]['frame'] - every, 'end_frame': rows[-1]['frame'],
            'type': label, 'family': family,
            'direction': label.split('_', 1)[1] if family not in ('static', 'complex') else None,
            'secondary': secondary, 'scene': run['scene'], 'mean_rates': mean_rates,
            'speed_unit': ('short sides/s' if family in ('pan', 'tilt', 'static', 'complex')
                           else 'log-scale/s' if family in ('zoom', 'dolly') else 'deg/s'),
            'mean_speed': round(statistics.mean(values), 4), 'peak_speed': round(max(values), 4),
            'peak_time': series[values.index(max(values))][0],
            'easing': _easing(values) if family not in ('static', 'complex') else None,
            'speed_curve': [[round(t, 3), round(v, 4)] for t, v in series[::step]],
            'agreement': round(agree, 3), 'confidence': conf,
            'confidence_explained': (f'mean per-sample score {mean_conf:.2f} (RANSAC inlier fit x margin over the '
                                     f'static threshold x dominance over other components) x label agreement '
                                     f'{agree:.2f} x duration factor {length_q:.2f}')}


# ------------------------------------------------------------ palettes -----

def palette(image):
    import cv2
    import numpy as np
    small = cv2.resize(image, (96, 96))
    pixels = small.reshape(-1, 3).astype('float32')
    cv2.setRNGSeed(0)
    _, labels, centers = cv2.kmeans(pixels, 5, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, .2), 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=5)
    colors = [{'hex': '#' + ''.join(f'{int(round(v)):02x}' for v in center[::-1]),
               'ratio': float(count / len(pixels))} for center, count in zip(centers, counts)]
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    return {'colors': sorted(colors, key=lambda c: -c['ratio']),
            'brightness': float(hsv[:, :, 2].mean() / 255),
            'saturation': float(hsv[:, :, 1].mean() / 255),
            'method': '5-cluster k-means on 96x96 BGR pixels; HSV V/S means',
            'confidence': 'sample measurement; within-shot color changes may be missed'}


def _detections(video, report):
    import cv2
    detector = None
    if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data'):
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    hog = cv2.HOGDescriptor() if hasattr(cv2, 'HOGDescriptor') else None
    if hog is not None:
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    report['presence_detection'] = {'method': 'OpenCV Haar/HOG', 'confidence': 'uncalibrated'}
    if detector is None or hog is None or detector.empty():
        report['presence_detection']['skipped'] = 'This OpenCV build lacks Haar and/or HOG detection'
        return
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    every = max(1, round(fps / 2))
    index = 0
    try:
        while cap.grab():
            if index % every == 0:
                _, image = cap.retrieve()
                h, w = image.shape[:2]
                small = cv2.resize(image, (256, max(64, round(256 * h / w))))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                boxes = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                people = hog.detectMultiScale(small, winStride=(8, 8), padding=(8, 8))[0]
                sw, sh = small.shape[1], small.shape[0]
                norm = lambda rows: [[float(x / sw), float(y / sh), float((x + bw) / sw), float((y + bh) / sh)]
                                     for x, y, bw, bh in rows]
                report['detections'].append({'time': index / fps, 'face_count': len(boxes), 'faces': norm(boxes),
                                             'person_count': len(people), 'persons': norm(people),
                                             'method': 'OpenCV frontal Haar + HOG people',
                                             'confidence': 'uncalibrated detections; stylized faces/poses may be missed'})
            index += 1
    finally:
        cap.release()


# -------------------------------------------------------------- report -----

def analyze_visual(source, info, scenes, entries, output, signals=None, transitions=None, video=None):
    """Write visual_analysis.json. `signals`/`transitions` come from transitions.analyze_transitions;
    `video` is the decoded file (proxy) when it differs from `source`."""
    report = {'method': 'scene timing, per-scene palettes and dense DIS optical flow fitted to a '
                        'similarity camera model on every analysed frame',
              'confidence': 'mixed measurements and explicitly labeled motion estimates',
              'conventions': {'pan_right': '+ when picture content moves left',
                              'tilt_up': '+ when picture content moves down (tilt up or pedestal up)',
                              'zoom_in': '+ when content expands (zoom in or dolly in); log-scale per second',
                              'roll_cw': '+ when content rotates counter-clockwise; degrees per second',
                              'units': 'pan/tilt in short sides of the frame per second'},
              'motion': [], 'palettes': [], 'detections': []}
    durations = [row['end'] - row['start'] for row in scenes]
    report['cuts'] = {'count': max(0, len(scenes) - 1),
                      'per_second': max(0, len(scenes) - 1) / info['duration'],
                      'shot_durations': durations, 'mean': statistics.mean(durations),
                      'median': statistics.median(durations), 'minimum': min(durations),
                      'method': 'edit-transition boundaries (hard cut, dissolve, fade, flip, wipe); see transitions.json',
                      'confidence': 'multi-source detector; in-shot whips/zoom bursts are not counted as cuts'}
    try:
        import cv2
        from fractions import Fraction
        fps = float(Fraction(info['fps']))
        for index, scene in enumerate(scenes):
            candidates = [e for e in entries if scene['start'] <= e['time'] < scene['end']]
            if candidates:
                closest = min(candidates, key=lambda e: abs(e['time'] - (scene['start'] + scene['end']) / 2))
                image = cv2.imread(closest['file'])
                if image is not None:
                    report['palettes'].append({'scene': index, 'start': scene['start'], 'end': scene['end'],
                                                'sample_time': closest['time'], **palette(image)})
        if signals is None:
            from .transitions import analyze_transitions
            signals, transitions, _ = analyze_transitions(video or source, fps)
        samples, segments = camera_analysis(signals, scenes, transitions or [])
        short, every = signals['short'], signals['flow_every']
        report['camera_method'] = {
            'flow': (f'OpenCV DIS optical flow (MEDIUM) between consecutive frames at '
                     f'{signals["size"][0]}x{signals["size"][1]}, every {every} frame(s) = '
                     f'{fps / every:.1f} samples/s'),
            'model': ('RANSAC similarity (scale, rotation, translation) on textured grid points; median radial '
                      'flow and its spread separate uniform zoom from parallax (dolly)'),
            'segmenting': '0.4 s majority smoothing, runs shorter than 0.3 s merged, split at edit transitions',
            'easing': ('speed-curve thirds/centroid: ease_out = fast start, ease_in = fast end, ease_in_out = '
                       'slow ends, linear = peak/mean < 1.3'),
            'confidence': ('per sample: inlier fit x margin over static threshold x dominance; per segment also '
                           'label agreement and duration. Heuristic 0-1 checked on synthetic pans/zooms, not a '
                           'probability. Large moving foreground objects can read as camera motion.')}
        report['camera_segments'] = segments
        stride = max(1, round(fps / 10 / every))
        report['camera_samples'] = samples[::stride]
        report['camera_samples_rate'] = round(fps / every / stride, 2)
        for s in samples[::stride]:
            report['motion'].append({'time': s['time'], 'start': round(s['time'] - every / fps, 4), 'end': s['time'],
                                     'magnitude_px_per_s': s['speed_short_per_s'] * short,
                                     'magnitude_frame_width_per_s': s['speed_short_per_s'] * short / signals['size'][0],
                                     'camera_estimate': s['label'], 'scale': math.exp(s['rates']['zoom_in'] / fps),
                                     'confidence': s['confidence'],
                                     'confidence_kind': 'heuristic fit x margin x dominance score (0-1)',
                                     'method': 'DIS flow + RANSAC similarity on textured points'})
        bins = {}
        for s in samples:
            bins.setdefault(int(s['time'] - 1e-9), []).append(s)
        per_second = []
        for second, rows in sorted(bins.items()):
            weight = {}
            for r in rows:
                weight[r['label']] = weight.get(r['label'], 0) + r['confidence'] + 1e-3
            label = max(weight, key=weight.get)
            share = sum(1 for r in rows if r['label'] == label) / len(rows)
            per_second.append({'start': second, 'end': min(second + 1, info['duration']),
                               'magnitude_px_per_s': statistics.mean(r['speed_short_per_s'] for r in rows) * short,
                               'magnitude_short_side_per_s': round(statistics.mean(r['speed_short_per_s'] for r in rows), 4),
                               'camera_estimate': label,
                               'confidence': round(statistics.mean(r['confidence'] for r in rows if r['label'] == label) * share, 3),
                               'label_share': round(share, 3),
                               'mean_rates': {k: round(statistics.mean(r['rates'][k] for r in rows), 4)
                                              for k in rows[0]['rates']}})
        report['motion_per_second'] = per_second
        _detections(video or source, report)
    except (ImportError, OSError, ValueError) as exc:
        report['skipped'] = f'Visual measurements unavailable: {exc}'
    save(output, report)
    return report
