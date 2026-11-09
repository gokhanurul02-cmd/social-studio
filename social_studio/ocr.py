"""Offline screen-text sampling with optional OCR engines."""
import csv
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess

from .media import save


def recognizer():
    """Return an engine only when its weights are already local."""
    reasons = []
    spec = importlib.util.find_spec('rapidocr_onnxruntime')
    if spec and list(Path(spec.origin).parent.rglob('*.onnx')):
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()

            def rapid(image):
                result, _ = engine(image)
                return [{'quad': box, 'text': text, 'confidence': float(score)}
                        for box, text, score in (result or [])]
            return 'RapidOCR bundled ONNX models', rapid, reasons
        except Exception as exc:
            reasons.append(f'RapidOCR: {exc}')
    else:
        reasons.append('RapidOCR package or bundled ONNX weights unavailable')
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


def scan_text(source, info, output, sample_fps=4.0, difference_threshold=3.0):
    import cv2
    method, recognize, reasons = recognizer()
    report = {'method': method, 'confidence': 'engine scores are uncalibrated',
              'sample_fps': sample_fps, 'timing_uncertainty_s': 1 / sample_fps,
              'difference_threshold': difference_threshold, 'notes': reasons, 'records': [], 'ocr_frames': 0}
    if recognize is None:
        report['skipped'] = '; '.join(reasons)
        save(output, report)
        return report
    cap = cv2.VideoCapture(str(source))
    previous, active = None, {}
    t = 0.0
    try:
        while t < info['duration']:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, image = cap.read()
            if not ok:
                break
            gray = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (160, 160))
            end = min(info['duration'], t + 1 / sample_fps)
            if change_score(previous, gray) > difference_threshold:
                detected = recognize(image)
                report['ocr_frames'] += 1
                current = {}
                for row in detected:
                    item = describe_text(row, image, t, end)
                    if not item['text']:
                        continue
                    key = (item['text'].casefold(), tuple(round(v * 20) for v in item['bbox']))
                    if key in active:
                        item = active[key]
                        item['end'] = end
                    else:
                        report['records'].append(item)
                    current[key] = item
                active = current
            else:
                for item in active.values():
                    item['end'] = end
            previous = gray
            t += 1 / sample_fps
    except Exception as exc:
        report['skipped'] = f'OCR interrupted: {type(exc).__name__}: {exc}'
    finally:
        cap.release()
    save(output, report)
    return report
