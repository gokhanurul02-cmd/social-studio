"""Frame-accurate caption / on-screen text timeline.

Two stages keep OCR calls few while timing stays exact to the frame:
  A. every frame is decoded at low resolution and, inside each text region, a
     "text-like" mask (bright fill with dark outline, dark fill with bright
     outline, or edges) is compared with the previous frame (IoU).
  B. one OCR call per segment, on its middle frame, gives the text; the same
     frame gives style (colours, stroke, shadow, size, baseline, case).
Nothing here needs the network.  Only OCR needs an engine; change detection,
style and font matching work without one when a region is supplied.
"""
from collections import Counter
from fractions import Fraction
import glob
import math
import os
from pathlib import Path
import statistics
import subprocess

import numpy as np

from .media import FFMPEG

LOW_WIDTH = 540
CAP_EM, ASC_EM, XH_EM = 0.727, 0.76, 0.545   # Verdana-like proportions (estimate)


# ---------------------------------------------------------------- decoding
def _fps(info):
    return float(Fraction(str(info['fps'])))


def _stream(source, width, height, fps_mode='passthrough'):
    """Yield gray frames (H x W uint8) one by one, one per source frame."""
    cmd = [str(FFMPEG), '-v', 'error', '-i', str(source), '-an', '-sn',
           '-vf', f'scale={width}:{height}:flags=area,format=gray',
           '-fps_mode', fps_mode, '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = width * height
    try:
        while True:
            raw = proc.stdout.read(size)
            if len(raw) < size:
                break
            yield np.frombuffer(raw, np.uint8).reshape(height, width)
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


def read_frame(source, info, frame, width=1080):
    """Full-resolution (scaled to <=width) BGR frame by index, mid-frame seek."""
    w = min(width, info['width'])
    h = int(round(info['height'] * w / info['width']))
    t = (frame + 0.5) / _fps(info)
    cmd = [str(FFMPEG), '-v', 'error', '-ss', f'{t:.6f}', '-i', str(source), '-an',
           '-frames:v', '1', '-vf', f'scale={w}:{h}:flags=lanczos', '-f', 'rawvideo',
           '-pix_fmt', 'bgr24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    if len(raw) < w * h * 3:
        return None
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).copy()


# ------------------------------------------------------------------- masks
def text_mask(gray, mode, radius):
    """Boolean mask of text-like pixels. radius ~ stroke search distance in px.
    light: bright blobs (letter fills) whose pixels mostly sit next to dark
    pixels (outline); dark: the inverse; edge: dilated Canny edges."""
    import cv2
    if mode in ('light', 'dark'):
        k = np.ones((2 * radius + 1, 2 * radius + 1), np.uint8)
        if mode == 'light':
            body = gray >= 215
            near = cv2.dilate((gray <= 100).astype(np.uint8), k) > 0
        else:
            body = gray <= 60
            near = cv2.dilate((gray >= 170).astype(np.uint8), k) > 0
        n, labels, stats, _ = cv2.connectedComponentsWithStats(body.astype(np.uint8), connectivity=8)
        if n <= 1:
            return np.zeros(gray.shape, bool)
        ring = np.bincount(labels[body & near], minlength=n)
        keep = (ring >= 0.3 * stats[:, cv2.CC_STAT_AREA]) & (stats[:, cv2.CC_STAT_AREA] >= 4)
        keep[0] = False
        return keep[labels]
    edges = cv2.Canny(gray, 80, 160)
    return cv2.dilate(edges, np.ones((3, 3), np.uint8)) > 0


def _min_pixels(shape):
    return max(12, int(0.002 * shape[0] * shape[1]))


def iou_masks(a, b):
    union = int(np.count_nonzero(a | b))
    if union == 0:
        return 1.0, 0
    return int(np.count_nonzero(a & b)) / union, union


# --------------------------------------------------- stage A: change tracking
def track_regions(source, info, regions, iou_threshold=0.6, width=LOW_WIDTH, grab=8):
    """One decoding pass; per region per frame: mask count, IoU with previous
    frame, change flag. Also keeps small windows of gray crops/masks around
    changes (for animation analysis). regions: dicts with y0,y1 (0..1) and mode."""
    H = int(round(info['height'] * width / info['width'])) // 2 * 2
    W = width
    radius = 2
    tracks = []
    for reg in regions:
        r0 = max(0, int(math.floor(reg['y0'] * H)))
        r1 = min(H, int(math.ceil(reg['y1'] * H)))
        tracks.append({'region': reg, 'rows': (r0, r1), 'count': [], 'iou': [], 'change': [],
                       'contain': [], 'store': {}, 'prev': None, 'prev_gray': None,
                       'capture_until': -1})
    n = 0
    for gray in _stream(source, W, H):
        for tr in tracks:
            r0, r1 = tr['rows']
            crop = gray[r0:r1]
            m = text_mask(crop, tr['region']['mode'], radius)
            minpx = _min_pixels(m.shape)
            cnt = int(np.count_nonzero(m))
            eff = m if cnt >= minpx else np.zeros_like(m)
            prev = tr['prev']
            if prev is None:
                iou, union = (0.0, cnt) if cnt >= minpx else (1.0, 0)
                contain = 0.0
            else:
                iou, union = iou_masks(prev, eff)
                pc = int(np.count_nonzero(prev))
                contain = int(np.count_nonzero(prev & eff)) / pc if pc else 0.0
            change = bool(union >= minpx and iou < iou_threshold)
            tr['count'].append(int(np.count_nonzero(eff)))
            tr['iou'].append(float(iou))
            tr['contain'].append(float(contain))
            tr['change'].append(change)
            if change:
                tr['capture_until'] = n + grab
                if prev is not None and (n - 1) not in tr['store']:
                    tr['store'][n - 1] = (tr['prev_gray'], prev)
            if n <= tr['capture_until']:
                tr['store'][n] = (crop.copy(), eff.copy())
            tr['prev'], tr['prev_gray'] = eff, crop
        n += 1
    for tr in tracks:
        tr['frames'] = n
        tr['width'], tr['height'] = W, H
        tr.pop('prev'), tr.pop('prev_gray')
    return tracks


def build_segments(track, min_gap=3):
    """Collapse change flags into segments. Returns list of dicts with
    start/end frame (inclusive), has_text, change cluster length."""
    n = track['frames']
    change = [i for i, c in enumerate(track['change']) if c]
    clusters = []
    for i in change:
        if clusters and i - clusters[-1][-1] <= min_gap:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    starts = [c[0] for c in clusters]
    spans = [c[-1] - c[0] + 1 for c in clusters]
    if not starts or starts[0] != 0:
        # nothing changed before the first cluster: frame 0 state is a segment
        starts.insert(0, 0)
        spans.insert(0, 1)
    segments = []
    for k, s in enumerate(starts):
        e = (starts[k + 1] - 1) if k + 1 < len(starts) else n - 1
        stable = min(e, s + max(spans[k], 4))
        tail = track['count'][max(s, (s + e) // 2): e + 1] or [0]
        minpx = _min_pixels(next(iter(track['store'].values()))[1].shape) if track['store'] else 12
        segments.append({'start': s, 'end': e, 'cluster': spans[k], 'stable': stable,
                         'has_text': statistics.median(tail) >= minpx,
                         'count': int(statistics.median(tail))})
    return segments


def classify_animation(track, seg, prev_seg):
    """cut / pop / fade / word-by-word from the frames after the change."""
    s = seg['start']
    store = track['store']
    stable_idx = min(seg['end'], s + 8)
    if s == 0 or stable_idx not in store:
        return {'type': 'present_at_start' if s == 0 else 'unknown', 'confidence': 'low'}
    _, stable = store[stable_idx]
    stable_count = max(1, int(np.count_nonzero(stable)))

    def extent(mask):
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            return 0, 0
        return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    sw, sh = extent(stable)
    # word-by-word / accumulation: previous text is contained in the new text
    if prev_seg and prev_seg['has_text'] and prev_seg['end'] + 1 == s and track['contain'][s] >= 0.9 \
            and stable_count > 1.12 * max(1, prev_seg['count']):
        return {'type': 'word-by-word', 'confidence': 'medium'}
    first = store.get(s)
    sizes, brightness = [], []
    prev_gray = store.get(s - 1, (None, None))[0]
    for i in range(s, stable_idx + 1):
        if i not in store:
            continue
        g, m = store[i]
        sizes.append(extent(m))
        core = stable
        if prev_gray is not None and core.any():
            brightness.append(float(g[core].mean()))
    base = float(prev_gray[stable].mean()) if prev_gray is not None and stable.any() else None
    fin = brightness[-1] if brightness else None
    if first is not None:
        c0 = int(np.count_nonzero(first[1]))
        w0, h0 = sizes[0] if sizes else (sw, sh)
        same_size = abs(w0 - sw) <= 0.06 * sw + 1 and abs(h0 - sh) <= 0.10 * sh + 1
        if seg['cluster'] == 1 and c0 >= 0.9 * stable_count and same_size:
            return {'type': 'cut', 'confidence': 'high'}
    if base is not None and fin is not None and abs(fin - base) >= 25:
        lo, hi = sorted((base, fin))
        mids = [b for b in brightness[:-1] if lo + 0.2 * (hi - lo) < b < hi - 0.2 * (hi - lo)]
        if len(mids) >= 2:
            return {'type': 'fade', 'confidence': 'medium',
                    'frames': len(mids) + 1}
    heights = [h for _, h in sizes if h]
    widths = [w for w, _ in sizes if w]
    if heights and (max(heights) > 1.08 * sh or min(heights) < 0.9 * sh
                    or max(widths) > 1.08 * sw or min(widths) < 0.9 * sw):
        return {'type': 'pop', 'confidence': 'medium',
                'scale_range': [round(min(heights) / max(1, sh), 2), round(max(heights) / max(1, sh), 2)]}
    return {'type': 'cut', 'confidence': 'medium'}


# ------------------------------------------------------------- region finding
def discover_regions(source, info, recognize, samples=16, width=720):
    """OCR sparse sample frames (on text-like masks first, raw frame as a
    fallback) and cluster the boxes into text regions. Returns (regions, ocr_calls)."""
    import cv2
    from .ocr import normalize_text
    frames = info.get('frames') or int(info['duration'] * _fps(info))
    idx = sorted({min(frames - 1, max(0, int((i + 0.5) * frames / samples))) for i in range(samples)})
    detections, calls, raw_budget = [], 0, 6
    for fi in idx:
        img = read_frame(source, info, fi, width)
        if img is None:
            continue
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        found = False
        for mode in ('light', 'dark'):
            m = text_mask(gray, mode, max(2, round(w * 0.004)))
            if int(np.count_nonzero(m)) < 0.0004 * w * h:
                continue
            out = cv2.cvtColor(np.where(m, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
            rows = recognize(out)
            calls += 1
            for row in rows:
                detections.append(_det(row, mode, fi, w, h, normalize_text))
                found = found or detections[-1] is not None
        if not found and raw_budget > 0:
            raw_budget -= 1
            rows = recognize(img)
            calls += 1
            for row in rows:
                detections.append(_det(row, 'edge', fi, w, h, normalize_text))
    detections = [d for d in detections if d]
    return cluster_regions(detections, len(idx)), calls


def _det(row, mode, fi, w, h, normalize):
    text = normalize(row['text'])['text']
    if not text or not any(c.isalnum() for c in text) or row['confidence'] < 0.6:
        return None
    pts = np.asarray(row['quad'])
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    if (y1 - y0) / h < 0.008 or (y1 - y0) / h > 0.25:
        return None
    return {'mode': mode, 'frame': fi, 'text': text, 'conf': row['confidence'],
            'x0': x0 / w, 'x1': x1 / w, 'y0': y0 / h, 'y1': y1 / h}


def cluster_regions(detections, sample_count):
    detections = sorted(detections, key=lambda d: (d['y0'] + d['y1']) / 2)
    groups = []
    for d in detections:
        for g in groups:
            gh = g['y1'] - g['y0']
            dh = d['y1'] - d['y0']
            gap = max(d['y0'] - g['y1'], g['y0'] - d['y1'])
            if gap < 0.9 * min(max(gh, dh), 0.1) and gap < 1.0 * max(dh, 1e-6) + 0.01:
                g['items'].append(d)
                g['y0'], g['y1'] = min(g['y0'], d['y0']), max(g['y1'], d['y1'])
                break
        else:
            groups.append({'items': [d], 'y0': d['y0'], 'y1': d['y1']})
    regions = []
    for g in groups:
        frames = {d['frame'] for d in g['items']}
        best = max(d['conf'] for d in g['items'])
        longest = max(len(d['text']) for d in g['items'])
        if len(frames) < 2 and (best < 0.9 or longest < 3):
            continue
        modes = Counter(d['mode'] for d in g['items'])
        mode = 'light' if modes['light'] >= modes['dark'] and modes['light'] >= modes['edge'] \
            else ('dark' if modes['dark'] >= modes['edge'] else 'edge')
        h = statistics.median(d['y1'] - d['y0'] for d in g['items'])
        regions.append({'y0': max(0.0, g['y0'] - 0.7 * h), 'y1': min(1.0, g['y1'] + 0.7 * h),
                        'x0': min(d['x0'] for d in g['items']), 'x1': max(d['x1'] for d in g['items']),
                        'mode': mode, 'hits': len(frames), 'text_height_ratio': float(h),
                        'sample_texts': [d['text'] for d in g['items'][:4]]})
    # merge regions that now overlap vertically
    regions.sort(key=lambda r: r['y0'])
    merged = []
    for r in regions:
        if merged and r['y0'] <= merged[-1]['y1']:
            p = merged[-1]
            p.update(y1=max(p['y1'], r['y1']), x0=min(p['x0'], r['x0']), x1=max(p['x1'], r['x1']),
                     hits=max(p['hits'], r['hits']))
        else:
            merged.append(r)
    return merged


# ----------------------------------------------------------------- style
def _hex(bgr):
    b, g, r = (int(round(v)) for v in bgr)
    return f'#{r:02x}{g:02x}{b:02x}'


def classify_case(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 'none'
    if len(letters) >= 2 and all(c == c.upper() for c in letters):
        return 'upper'
    if all(c == c.lower() for c in letters):
        return 'lower'
    words = [w for w in text.split() if any(c.isalpha() for c in w)]
    first_alpha = lambda w: next(c for c in w if c.isalpha())
    if len(words) >= 2 and all(first_alpha(w).isupper() for w in words):
        return 'title'
    if first_alpha(words[0]).isupper() and all(
            c == c.lower() for w in words[1:] for c in w if c.isalpha()):
        return 'sentence'
    return 'sentence' if first_alpha(words[0]).isupper() else 'mixed'


def fill_mask(bgr, mode):
    import cv2
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return text_mask(gray, 'dark' if mode == 'dark' else 'light', max(2, round(bgr.shape[1] * 0.004)))


def estimate_style(frame, bbox_px, text, mode='light'):
    """Style of one text box from a full-resolution frame. Estimates; colours
    and stroke are measured, shadow/size are heuristics."""
    import cv2
    H, W = frame.shape[:2]
    x0, y0, x1, y1 = bbox_px
    pad = max(6, int((y1 - y0) * 0.6))
    cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    crop = frame[cy0:cy1, cx0:cx1]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    mask = fill_mask(crop, 'dark' if mode == 'dark' else 'light')
    # keep only the OCR box (tight) to avoid scene noise
    box = np.zeros_like(mask)
    box[y0 - cy0:y1 - cy0 + 1, x0 - cx0:x1 - cx0 + 1] = True
    mask &= box
    mask = _clean(mask)
    style = {'fill_hex': None, 'stroke_hex': None, 'stroke_px_ratio': 0.0, 'shadow': False,
             'font_size_ratio': None, 'baseline_y_ratio': None, 'align': None, 'case': classify_case(text),
             'words': text.split(), 'measurement_confidence': 'low'}
    cx = (x0 + x1) / 2 / W
    style['align'] = 'center' if abs(cx - 0.5) < 0.04 else ('left' if cx < 0.5 else 'right')
    if int(np.count_nonzero(mask)) < 30:
        return style
    inner = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    pix = crop[inner if inner.any() else mask]
    style['fill_hex'] = _hex(np.median(pix, axis=0))
    fill_gray = float(np.median(gray[inner if inner.any() else mask]))
    # stroke: thickness where ring pixels stay close to the stroke colour
    ring_cols = {}
    prev = mask.astype(np.uint8)
    ring1 = (cv2.dilate(prev, np.ones((3, 3), np.uint8)) > 0) & ~mask
    ring2 = (cv2.dilate(prev, np.ones((5, 5), np.uint8)) > 0) & ~mask
    ring_pixels = gray[ring2]
    if ring_pixels.size:
        order = np.argsort(ring_pixels)
        pick = order[:max(1, len(order) // 3)] if mode != 'dark' else order[-max(1, len(order) // 3):]
        cols = crop[ring2][pick]
        stroke_bgr = np.median(cols, axis=0)
        sg = float(np.median(ring_pixels[pick]))
        width_px, aa_skipped = 0, False
        for d in range(1, 13):
            outer = (cv2.dilate(prev, np.ones((2 * d + 1, 2 * d + 1), np.uint8)) > 0)
            inner_d = (cv2.dilate(prev, np.ones((2 * d - 1, 2 * d - 1), np.uint8)) > 0)
            band = outer & ~inner_d
            if not band.any():
                break
            frac = float(np.mean(np.abs(gray[band].astype(float) - sg) <= 45))
            if frac >= 0.55:
                width_px = d - (0.5 if d > 1 and not width_px and aa_skipped else 0)
            elif d == 1:
                aa_skipped = True      # anti-aliased fill/stroke transition ring
            else:
                break
        contrast = abs(fill_gray - sg)
        if width_px and contrast > 80:
            style['stroke_hex'] = _hex(stroke_bgr)
            style['stroke_px_ratio'] = round(width_px / H, 5)
            style['stroke_px'] = width_px
        # drop shadow: below-right region darker than above-left at same distance
        k = max(2, int(round(max(width_px, 1) + 2)))
        sh = max(3, int((y1 - y0) * 0.08))
        down = np.roll(mask, (sh, sh // 2), axis=(0, 1))
        up = np.roll(mask, (-sh, -sh // 2), axis=(0, 1))
        grown = cv2.dilate(mask.astype(np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8)) > 0
        a, b = down & ~grown, up & ~grown
        if a.sum() > 50 and b.sum() > 50:
            style['shadow'] = bool(gray[b].mean() - gray[a].mean() > 14)
    # size / baseline from connected components of the fill mask
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    comps = [(stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT],
              stats[i, cv2.CC_STAT_HEIGHT]) for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 20]
    if comps:
        tall = max(c[2] for c in comps)
        comps = [c for c in comps if c[2] >= 0.3 * tall]
        bottoms = [c[1] for c in comps]
        baseline = Counter(round(b / 2) * 2 for b in bottoms).most_common(1)[0][0]
        on_base = [c for c in comps if abs(c[1] - baseline) <= 3]
        tall = max(c[2] for c in on_base)
        small = [c[2] for c in on_base if c[2] < 0.8 * tall]
        has_upper_digit = any(ch.isupper() or ch.isdigit() for ch in text)
        asc = any(ch in 'bdfhklt' for ch in text.lower())
        if small and tall > 1.25 * statistics.median(small):
            xh = statistics.median(small)
            if has_upper_digit:
                em, basis = tall / CAP_EM, 'cap_height'
            elif asc:
                em, basis = tall / ASC_EM, 'ascender_height'
            else:
                em, basis = xh / XH_EM, 'x_height'
            style['x_height_px'] = float(xh)
        elif has_upper_digit and not small:
            em, basis = tall / CAP_EM, 'cap_height'
        else:
            em, basis = tall / XH_EM if not has_upper_digit else tall / CAP_EM, \
                'x_height' if not has_upper_digit else 'cap_height'
        style['cap_or_ascender_px'] = float(tall)
        style['font_size_basis'] = basis
        style['font_size_ratio'] = round(float(em / H), 5)
        style['baseline_y_ratio'] = round(float((cy0 + baseline) / H), 5)
        style['measurement_confidence'] = 'medium'
    return style


def _clean(mask):
    import cv2
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if n <= 1:
        return mask
    tall = max(stats[i, cv2.CC_STAT_HEIGHT] for i in range(1, n))
    keep = np.zeros(n, bool)
    for i in range(1, n):
        keep[i] = stats[i, cv2.CC_STAT_AREA] >= 12 and stats[i, cv2.CC_STAT_HEIGHT] >= 0.12 * tall
    return keep[labels]


# ------------------------------------------------------------- font matching
FONT_FILES = ['verdanab.ttf', 'tahomabd.ttf', 'arialbd.ttf', 'impact.ttf', 'segoeuib.ttf',
              'seguibl.ttf', 'calibrib.ttf', 'trebucbd.ttf', 'bahnschrift.ttf', 'comicbd.ttf',
              'georgiab.ttf', 'arialnb.ttf', 'verdana.ttf', 'arial.ttf']


def candidate_fonts():
    folders = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
               os.path.expanduser('~/AppData/Local/Microsoft/Windows/Fonts'),
               '/usr/share/fonts/truetype/dejavu']
    found = {}
    for folder in folders:
        for name in FONT_FILES + ['DejaVuSans-Bold.ttf']:
            p = os.path.join(folder, name)
            if os.path.isfile(p):
                found.setdefault(name, p)
        for p in glob.glob(os.path.join(folder, '[Mm]ontserrat*[Bb]old*.ttf')) + \
                glob.glob(os.path.join(folder, '[Mm]ontserrat*[Bb]lack*.ttf')):
            found.setdefault(os.path.basename(p), p)
    return found


def match_fonts(samples, top=3):
    """samples: list of (text, fill_mask_bool_array). Renders text with each
    candidate font and compares ink shape (IoU, shifted/scaled) to the mask."""
    import cv2
    from PIL import Image, ImageDraw, ImageFont
    fonts = candidate_fonts()
    if not fonts:
        return {'skipped': 'no candidate font files found'}
    if not samples:
        return {'skipped': 'no caption sample with a usable fill mask'}
    th = 48

    def norm(m):
        ys, xs = np.nonzero(m)
        crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8) * 255
        s = th / crop.shape[0]
        return cv2.resize(crop, (max(1, int(round(crop.shape[1] * s))), th), interpolation=cv2.INTER_AREA)
    scores = {name: [] for name in fonts}
    for text, mask in samples:
        if not mask.any():
            continue
        target = norm(mask) > 127
        for name, path in fonts.items():
            try:
                font = ImageFont.truetype(path, 160)
                box = font.getbbox(text)
                img = Image.new('L', (box[2] - box[0] + 20, box[3] - box[1] + 20), 0)
                ImageDraw.Draw(img).text((10 - box[0], 10 - box[1]), text, fill=255, font=font)
                rend = np.asarray(img) > 127
                if not rend.any():
                    continue
                rend = norm(rend) > 127
            except Exception:
                continue
            best = 0.0
            for sc in (0.97, 1.0, 1.03):
                r = cv2.resize(rend.astype(np.uint8) * 255, None, fx=sc, fy=sc,
                               interpolation=cv2.INTER_AREA) > 127
                Hh = max(r.shape[0], target.shape[0]) + 8
                Ww = max(r.shape[1], target.shape[1]) + 8
                A = np.zeros((Hh, Ww), bool)
                oy, ox = (Hh - target.shape[0]) // 2, (Ww - target.shape[1]) // 2
                A[oy:oy + target.shape[0], ox:ox + target.shape[1]] = target
                for dy in (-2, 0, 2):
                    for dx in (-3, -1, 0, 1, 3):
                        B = np.zeros((Hh, Ww), bool)
                        ry, rx = (Hh - r.shape[0]) // 2 + dy, (Ww - r.shape[1]) // 2 + dx
                        ys, xs = max(0, ry), max(0, rx)
                        ye, xe = min(Hh, ry + r.shape[0]), min(Ww, rx + r.shape[1])
                        B[ys:ye, xs:xe] = r[ys - ry:ye - ry, xs - rx:xe - rx]
                        u = np.count_nonzero(A | B)
                        if u:
                            best = max(best, np.count_nonzero(A & B) / u)
            scores[name].append(best)
    ranked = sorted(((statistics.mean(v), n) for n, v in scores.items() if v), reverse=True)
    if not ranked:
        return {'skipped': 'font rendering failed'}
    return {'method': 'Pillow render vs fill-mask IoU (height-normalised, small shift/scale search)',
            'samples': len(samples), 'confidence': 'low: score compares letter shapes only',
            'all_scores': {n: round(float(sc), 3) for sc, n in ranked},
            'candidates': [{'font': n, 'file': fonts[n], 'score': round(float(s), 3)}
                           for s, n in ranked[:top]]}


# --------------------------------------------------------------- summary
def style_summary(records, fps, font_report):
    caps = [r for r in records if r['kind'] == 'caption']
    if not caps:
        return {'skipped': 'no caption records'}
    st = [r['style'] for r in caps]

    def mode_of(key):
        vals = [s[key] for s in st if s.get(key) is not None]
        return Counter(vals).most_common(1)[0][0] if vals else None

    def med(key):
        vals = [s[key] for s in st if s.get(key) is not None]
        return float(statistics.median(vals)) if vals else None
    words = [len(s['words']) for s in st]
    durations = [r['end'] - r['start'] for r in caps]
    anims = Counter(r['animation']['type'] for r in caps)
    return {'group_count': len(caps), 'fill_hex': mode_of('fill_hex'), 'stroke_hex': mode_of('stroke_hex'),
            'stroke_px_ratio': med('stroke_px_ratio'),
            'shadow': sum(1 for s in st if s['shadow']) > len(st) / 2,
            'font_size_ratio': med('font_size_ratio'), 'baseline_y_ratio': med('baseline_y_ratio'),
            'align': mode_of('align'), 'case': mode_of('case'),
            'case_counts': dict(Counter(s['case'] for s in st)),
            'words_per_group': {'mean': round(statistics.mean(words), 2), 'median': statistics.median(words),
                                'min': min(words), 'max': max(words)},
            'mean_duration_s': round(statistics.mean(durations), 3),
            'mean_duration_frames': round(statistics.mean(r['end_frame'] - r['start_frame'] + 1 for r in caps), 1),
            'animation_counts': dict(anims),
            'dominant_animation': anims.most_common(1)[0][0],
            'safe_zone_violations': sum(1 for r in caps if r['safe_zone_violation']),
            'font_candidates': font_report}
