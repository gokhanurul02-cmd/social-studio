"""Offline screen-text sampling with optional OCR engines."""
import csv
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import time
import unicodedata

from .media import save


_RAPID = {}


def _rapid_engine():
    """Load RapidOCR once. The wheel ships its ONNX weights in <package>/models."""
    if 'engine' in _RAPID:
        return _RAPID['engine']
    spec = importlib.util.find_spec('rapidocr_onnxruntime')
    if not spec or not spec.origin:
        raise ImportError('rapidocr_onnxruntime package not installed')
    weights = list((Path(spec.origin).parent / 'models').glob('*.onnx'))
    if len(weights) < 2:
        raise FileNotFoundError('bundled ONNX weights missing in ' + str(Path(spec.origin).parent / 'models'))
    from rapidocr_onnxruntime import RapidOCR
    _RAPID['engine'] = RapidOCR()
    return _RAPID['engine']


def recognizer():
    """Return an engine only when its weights are already local."""
    reasons = []
    try:
        engine = _rapid_engine()

        def rapid(image):
            result, _ = engine(image)
            return [{'quad': box, 'text': text, 'confidence': float(score)}
                    for box, text, score in (result or [])]

        def rapid_line(image):
            # recognition only (no detector) for an already-tight single line
            result, _ = engine(image, use_det=False, use_cls=False, use_rec=True)
            return (result[0][0], float(result[0][1])) if result else ('', 0.0)
        rapid.line = rapid_line
        return 'RapidOCR bundled ONNX models (PP-OCRv4 ch/en; ü/Ü only Turkish glyphs in vocabulary)', rapid, reasons
    except Exception as exc:
        reasons.append(f'RapidOCR: {type(exc).__name__}: {exc}')
    det, rec = os.getenv('SOCIAL_PADDLE_DET_MODEL'), os.getenv('SOCIAL_PADDLE_REC_MODEL')
    if det and rec and Path(det).is_dir() and Path(rec).is_dir():
        try:
            from paddleocr import PaddleOCR
            engine = PaddleOCR(det_model_dir=det, rec_model_dir=rec, lang='en',
                               use_angle_cls=False, show_log=False)

            def paddle(image):
                lines = engine.ocr(image, cls=False)
                return [{'quad': box, 'text': content[0], 'confidence': float(content[1])}
                        for box, content in (lines[0] or [])]
            return 'PaddleOCR local model directories', paddle, reasons
        except Exception as exc:
            reasons.append(f'PaddleOCR: {exc}')
    else:
        reasons.append('PaddleOCR local det/rec model directories unavailable')
    binary = shutil.which('tesseract')
    if binary:
        languages = subprocess.run([binary, '--list-langs'], capture_output=True, text=True, check=True).stdout.splitlines()
        selected = [lang for lang in ['tur', 'eng'] if lang in languages]
        if selected:
            def tesseract(image):
                import cv2
                encoded = cv2.imencode('.png', image)[1].tobytes()
                result = subprocess.run([binary, 'stdin', 'stdout', '-l', '+'.join(selected), 'tsv'],
                                        input=encoded, capture_output=True, check=True)
                groups = {}
                for word in csv.DictReader(io.StringIO(result.stdout.decode('utf-8')), delimiter='\t'):
                    if not word['text'].strip() or float(word['conf']) < 0:
                        continue
                    key = tuple(word[k] for k in ['block_num', 'par_num', 'line_num'])
                    groups.setdefault(key, []).append(word)
                rows = []
                for words in groups.values():
                    left = min(int(w['left']) for w in words)
                    top = min(int(w['top']) for w in words)
                    right = max(int(w['left']) + int(w['width']) for w in words)
                    bottom = max(int(w['top']) + int(w['height']) for w in words)
                    rows.append({'quad': [[left, top], [right, top], [right, bottom], [left, bottom]],
                                 'text': ' '.join(w['text'] for w in words),
                                 'confidence': sum(float(w['conf']) for w in words) / (100 * len(words))})
                return rows
            reasons.append('Tesseract installed languages: ' + '+'.join(selected))
            return 'Tesseract TSV ' + '+'.join(selected), tesseract, reasons
    return None, None, reasons + ['Tesseract with tur or eng traineddata unavailable']


def change_score(previous, current):
    import cv2
    import numpy as np
    if previous is None:
        return float('inf')
    delta = cv2.absdiff(previous, current)
    # A small caption can change while most pixels remain unchanged.
    return max(float(tile.mean()) for row in np.array_split(delta, 8) for tile in np.array_split(row, 8, axis=1))


def describe_text(row, image, start, end):
    import numpy as np
    h, w = image.shape[:2]
    points = np.asarray(row['quad'])
    x0, y0 = np.floor(points.min(axis=0)).astype(int)
    x1, y1 = np.ceil(points.max(axis=0)).astype(int)
    x0, x1 = max(0, x0), min(w, x1)
    y0, y1 = max(0, y0), min(h, y1)
    crop = image[y0:y1, x0:x1]
    colors = {'text': None, 'background': None, 'method': 'luminance-tail medians in OCR box', 'confidence': 'low'}
    if crop.size:
        pixels = crop.reshape(-1, 3)[:, ::-1]
        brightness = pixels.mean(axis=1)
        median = float(np.median(brightness))
        # Text/background separation is an estimate, especially for textured footage.
        foreground = brightness >= np.percentile(brightness, 85) if median < 128 else brightness <= np.percentile(brightness, 15)
        for name, mask in [('text', foreground), ('background', ~foreground)]:
            if mask.any():
                colors[name] = '#' + ''.join(f'{int(v):02x}' for v in np.median(pixels[mask], axis=0))
    flags = []
    if h > w:
        if y0 / h < .12:
            flags.append('top_12_percent')
        if y1 / h > .8:
            flags.append('bottom_20_percent')
    return {'start': start, 'end': end, 'text': row['text'].strip(),
            'bbox': [x0 / w, y0 / h, x1 / w, y1 / h],
            'confidence': row['confidence'], 'confidence_calibrated': False,
            'text_height_px': int(y1 - y0), 'text_height_ratio': float((y1 - y0) / h),
            'colors': colors, 'safe_area_violations': flags}


_TR_STOP = {'icin': 'için', 'cok': 'çok', 'degil': 'değil', 'sey': 'şey', 'once': 'önce', 'gibi': 'gibi',
            'ama': 'ama', 'daha': 'daha', 'bir': 'bir', 've': 've', 'ile': 'ile', 'bu': 'bu', 'sonra': 'sonra',
            'kadar': 'kadar', 'seyi': 'şeyi', 'basla': 'başla', 'nasil': 'nasıl'}


def normalize_text(text):
    """Unicode-clean OCR text. Returns text plus script statistics. The bundled
    engine has no ç ğ ı İ ö ş in its vocabulary, so Turkish words come back with
    the plain Latin letter; this only flags likely cases (never invents text)."""
    raw = text or ''
    t = unicodedata.normalize('NFKC', raw)
    t = unicodedata.normalize('NFC', t)
    t = ''.join(' ' if unicodedata.category(c) in ('Zs', 'Cc') else c for c in t)
    for a, b in (('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"')):
        t = t.replace(a, b)
    t = ' '.join(t.split())
    letters = [c for c in t if c.isalpha()]
    foreign = [c for c in letters if 'LATIN' not in unicodedata.name(c, 'LATIN')]
    ratio = len(foreign) / len(letters) if letters else 0.0
    words = [w.strip('.,!?;:"\'').casefold() for w in t.split()]
    tr_hits = [w for w in words if w in _TR_STOP]
    out = {'text': t, 'non_latin_ratio': round(ratio, 3), 'non_latin_chars': ''.join(sorted(set(foreign)))}
    if words and tr_hits and len(tr_hits) >= max(1, len(words) // 3):
        fixed = {w: _TR_STOP[w] for w in tr_hits if _TR_STOP[w] != w}
        out['turkish_suspected'] = True
        if fixed:
            out['turkish_diacritic_suggestions'] = fixed
    return out


def _ink_lines(mask):
    """Split a text mask into text lines (row runs); returns [(y0,y1,x0,x1)]."""
    import numpy as np
    rows = np.nonzero(mask.sum(axis=1) > 0)[0]
    if len(rows) == 0:
        return []
    runs, start, prev = [], rows[0], rows[0]
    for r in rows[1:]:
        if r - prev > 1:
            runs.append([start, prev])
            start = r
        prev = r
    runs.append([start, prev])
    tall = max(b - a + 1 for a, b in runs)
    merged = [runs[0]]
    for a, b in runs[1:]:
        if a - merged[-1][1] <= 0.35 * tall:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    out = []
    for a, b in merged:
        cols = np.nonzero(mask[a:b + 1].sum(axis=0) > 0)[0]
        if b - a + 1 >= 0.35 * tall and len(cols):
            out.append((int(a), int(b), int(cols[0]), int(cols[-1])))
    return out


def _ocr_region(recognize, frame, region, mode):
    """OCR one horizontal region of a full-resolution frame. Text-like masks are
    split into lines and each tight line is recognised without the detector
    (reliable on caption-style text); the detector path on mask / raw crop is
    the fallback. Quads are returned in full-frame coordinates."""
    import cv2
    import numpy as np
    from .captions import fill_mask, _clean
    h = frame.shape[0]
    y0, y1 = int(max(0, region['y0'] * h)), int(min(h, region['y1'] * h))
    crop = frame[y0:y1]
    line_rec = getattr(recognize, 'line', None)
    if mode in ('light', 'dark'):
        mask = _clean(fill_mask(crop, mode))
        if line_rec is not None and mask.any():
            rows = []
            for a, b, c, d in _ink_lines(mask):
                pad = max(4, int((b - a + 1) * 0.4))
                tight = np.where(mask[a:b + 1, c:d + 1], 0, 255).astype(np.uint8)
                img = cv2.cvtColor(np.pad(tight, pad, constant_values=255), cv2.COLOR_GRAY2BGR)
                text, conf = line_rec(img)
                if text.strip():
                    rows.append({'quad': [[c, a + y0], [d, a + y0], [d, b + y0], [c, b + y0]],
                                 'text': text, 'confidence': conf})
            if rows and min(r['confidence'] for r in rows) >= 0.6:
                return rows, 'mask-line'
        attempts = [('mask', cv2.cvtColor(np.where(mask, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR))]
    else:
        attempts = []
    attempts.append(('raw', crop))
    best_rows, best_score, best_name = [], -1.0, 'none'
    for name, image in attempts:
        rows = [r for r in recognize(image) if normalize_text(r['text'])['text']]
        score = sum(r['confidence'] * len(r['text']) for r in rows)
        if rows and score > best_score:
            best_rows, best_score, best_name = rows, score, name
        if rows and min(r['confidence'] for r in rows) >= 0.8:
            break
    for r in best_rows:
        r['quad'] = [[p[0], p[1] + y0] for p in r['quad']]
    return best_rows, best_name


def _merge_rows(rows):
    """Join OCR lines of one region (top to bottom) into one record row."""
    import numpy as np
    def box(r):
        return (min(p[0] for p in r['quad']), min(p[1] for p in r['quad']),
                max(p[0] for p in r['quad']), max(p[1] for p in r['quad']))
    lines = []
    for r in sorted(rows, key=lambda r: box(r)[1]):
        b = box(r)
        for ln in lines:
            lb = ln['y']
            overlap = min(lb[1], b[3]) - max(lb[0], b[1])
            if overlap > 0.5 * min(lb[1] - lb[0], b[3] - b[1]):
                ln['rows'].append(r)
                ln['y'] = (min(lb[0], b[1]), max(lb[1], b[3]))
                break
        else:
            lines.append({'y': (b[1], b[3]), 'rows': [r]})
    rows = [r for ln in sorted(lines, key=lambda l: l['y'][0])
            for r in sorted(ln['rows'], key=lambda r: box(r)[0])]
    pts = np.asarray([p for r in rows for p in r['quad']], float)
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    weights = [max(1, len(r['text'])) for r in rows]
    conf = sum(r['confidence'] * wgt for r, wgt in zip(rows, weights)) / sum(weights)
    return {'quad': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
            'text': ' '.join(r['text'].strip() for r in rows), 'confidence': conf, 'lines': len(lines)}


def scan_text(source, info, output, sample_fps=4.0, difference_threshold=3.0,
              iou_threshold=0.6, discovery_samples=16, regions=None):
    """Frame-accurate on-screen text timeline (see captions.py). sample_fps and
    difference_threshold are kept for CLI compatibility only: every frame is
    examined and change detection uses text-mask IoU < iou_threshold."""
    from . import captions as C
    started = time.time()
    method, recognize, reasons = recognizer()
    fps = C._fps(info)
    report = {'method': method, 'confidence': 'engine scores are uncalibrated',
              'timing': 'frame-accurate: per-frame text-mask IoU, OCR only on segment middle frames',
              'fps': fps, 'sample_fps': fps, 'timing_uncertainty_s': 1 / fps,
              'difference_threshold': difference_threshold, 'iou_threshold': iou_threshold,
              'legacy_args_ignored': {'sample_fps': sample_fps, 'difference_threshold': difference_threshold},
              'notes': reasons, 'records': [], 'ocr_frames': 0, 'regions': []}
    if recognize is None and not regions:
        report['skipped'] = '; '.join(reasons)
        save(output, report)
        return report
    try:
        if regions is None:
            regions, calls = C.discover_regions(source, info, recognize, discovery_samples)
            report['ocr_frames'] += calls
        else:
            regions = [dict(r) for r in regions]
        report['regions'] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
                             for r in regions]
        if not regions:
            report['notes'] = reasons + ['no text region found in sample frames']
            report['elapsed_s'] = round(time.time() - started, 2)
            save(output, report)
            return report
        tracks = C.track_regions(source, info, regions, iou_threshold)
        pending = []
        for ri, tr in enumerate(tracks):
            segs = C.build_segments(tr)
            prev = None
            for seg in segs:
                seg['animation'] = C.classify_animation(tr, seg, prev) if seg['has_text'] else None
                prev = seg
            kept = [s for s in segs if s['has_text']]
            if not kept and regions[ri].get('hits', 0) >= 2:
                # OCR saw text here but the mask tracker could not follow it (e.g. unusual
                # styling): fall back to one whole-video segment, timing not frame-accurate.
                kept = [{'start': 0, 'end': tr['frames'] - 1, 'has_text': True, 'cluster': 1, 'count': 0,
                         'animation': {'type': 'unknown', 'confidence': 'low'}, 'fallback': 'static_whole_video'}]
                report['notes'].append(f'region {ri}: mask tracking found no text; whole-video segment used')
            pending.append((ri, tr, kept))
        if recognize is None:
            # No engine: expose the frame-accurate change timeline only.
            report['change_timeline'] = [
                {'region': ri, 'start_frame': s['start'], 'end_frame': s['end'],
                 'start': s['start'] / fps, 'end': (s['end'] + 1) / fps, 'animation': s['animation']}
                for ri, tr, segs in pending for s in segs]
            report['skipped'] = '; '.join(reasons) + ' (text content skipped; change_timeline only)'
            report['elapsed_s'] = round(time.time() - started, 2)
            save(output, report)
            return report
        for ri, tr, segs in pending:
            region = regions[ri]
            for seg in segs:
                mid = (min(seg['end'], seg['start'] + 4) + seg['end']) // 2
                frame = C.read_frame(source, info, mid, 1080)
                if frame is None:
                    seg['text_row'] = None
                    continue
                rows, used = _ocr_region(recognize, frame, region, region['mode'])
                report['ocr_frames'] += 1
                seg['ocr_frame'], seg['ocr_input'] = mid, used
                seg['text_row'] = _merge_rows(rows) if rows else None
                seg['frame_img'] = frame
        records = []
        for ri, tr, segs in pending:
            last = None
            for seg in segs:
                row = seg.get('text_row')
                if row is None:
                    last = None
                    continue
                norm = normalize_text(row['text'])
                if not norm['text']:
                    continue
                if last is not None and last['end'] + 1 == seg['start'] and \
                        last['text'].casefold() == norm['text'].casefold():
                    last['end'] = seg['end']      # same text across a false split
                    continue
                last = {'start': seg['start'], 'end': seg['end'], 'text': norm['text'], 'seg': seg,
                        'row': row, 'norm': norm, 'region': ri}
                records.append(last)
        out = []
        for rec in records:
            seg, row, norm = rec['seg'], rec['row'], rec['norm']
            frame = seg['frame_img']
            row = dict(row, text=norm['text'])
            item = describe_text(row, frame, rec['start'] / fps, (rec['end'] + 1) / fps)
            ih, iw = frame.shape[:2]
            bx = (int(round(item['bbox'][0] * iw)), int(round(item['bbox'][1] * ih)),
                  int(round(item['bbox'][2] * iw)) - 1, int(round(item['bbox'][3] * ih)) - 1)
            style = C.estimate_style(frame, bx, norm['text'], regions[rec['region']]['mode'])
            if style['fill_hex']:
                item['colors'].update({'text': style['fill_hex'], 'stroke': style['stroke_hex'],
                                       'method': 'median of letter-fill mask pixels (stroke: darkest ring)',
                                       'confidence': 'medium'})
            flags = list(item['safe_area_violations'])
            if item['bbox'][0] < 0.05 or item['bbox'][2] > 0.95:
                flags.append('side_5_percent')
            item['safe_area_violations'] = flags
            flags_conf, conf = [], row['confidence']
            if norm['non_latin_ratio'] > 0:
                flags_conf.append('non_latin')
                conf = min(conf, 0.3)
            if norm.get('turkish_suspected'):
                flags_conf.append('turkish_diacritics_unsupported_by_engine')
            item.update({'start_frame': rec['start'], 'end_frame': rec['end'],
                         'duration_frames': rec['end'] - rec['start'] + 1,
                         'region': rec['region'], 'kind': None, 'style': style,
                         'animation': seg['animation'] or {'type': 'unknown', 'confidence': 'low'},
                         'safe_zone_violation': bool(flags), 'lines': row.get('lines', 1),
                         'confidence_adjusted': conf, 'low_confidence': bool(flags_conf) or conf < 0.6,
                         'confidence_flags': flags_conf, 'ocr_input': seg.get('ocr_input'),
                         'ocr_frame': seg.get('ocr_frame')})
            if norm['non_latin_ratio'] > 0:
                item['non_latin_chars'] = norm['non_latin_chars']
            if norm.get('turkish_diacritic_suggestions'):
                item['turkish_diacritic_suggestions'] = norm['turkish_diacritic_suggestions']
            item['_frame'], item['_bbox_px'] = frame, bx
            out.append(item)
        per_region = {}
        for it in out:
            per_region.setdefault(it['region'], []).append(it)
        for ri, items in per_region.items():
            r = regions[ri]
            kind = 'caption' if len(items) >= 3 else ('title' if (r['y0'] + r['y1']) / 2 < 0.4 else 'label')
            for it in items:
                it['kind'] = kind
        out.sort(key=lambda r: (r['start_frame'], r['region']))
        font_samples = []
        caps = sorted((it for it in out if it['kind'] == 'caption' and it['confidence'] >= 0.85
                       and not it['confidence_flags'] and len(it['text']) >= 4),
                      key=lambda it: -len(it['text']))
        for it in caps[:6]:
            x0, y0, x1, y1 = it['_bbox_px']
            fm = C._clean(C.fill_mask(it['_frame'], regions[it['region']]['mode'])[y0:y1 + 1, x0:x1 + 1])
            if fm.any():
                font_samples.append((it['text'], fm))
        try:
            font_report = C.match_fonts(font_samples)
        except Exception as exc:
            font_report = {'skipped': f'{type(exc).__name__}: {exc}'}
        for it in out:
            it.pop('_frame')
            it.pop('_bbox_px')
        report['records'] = out
        report['caption_style_summary'] = C.style_summary(out, fps, font_report)
        report['font_candidates'] = font_report
        report['non_latin_records'] = sum(1 for r in out if 'non_latin' in r['confidence_flags'])
        report['notes'] = reasons + [
            'bundled RapidOCR vocabulary lacks c-cedilla, g-breve, dotless i, dotted I, o-umlaut, s-cedilla '
            '(only u-umlaut present): Turkish diacritics may come back as plain letters; records are flagged '
            'turkish_diacritics_unsupported_by_engine when common Turkish words are seen']
    except Exception as exc:
        import traceback
        report['skipped'] = f'OCR interrupted: {type(exc).__name__}: {exc}'
        report['traceback'] = traceback.format_exc()[-1500:]
    report['elapsed_s'] = round(time.time() - started, 2)
    save(output, report)
    return report
