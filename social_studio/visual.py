"""Scene palettes, cut statistics and qualified global-motion estimates."""
import math
import statistics

from .media import frame_at, save


def motion_estimate(previous, current, dt):
    import cv2
    import numpy as np
    flow = cv2.calcOpticalFlowFarneback(previous, current, None, .5, 3, 15, 3, 5, 1.2, 0)
    h, w = flow.shape[:2]
    yy, xx = np.mgrid[8:h-8:8, 8:w-8:8]
    points = np.column_stack([xx.ravel(), yy.ravel()]).astype('float32')
    displacement = flow[yy, xx].reshape(-1, 2)
    matrix, inliers = cv2.estimateAffinePartial2D(points, points + displacement, method=cv2.RANSAC,
                                                ransacReprojThreshold=1.5)
    magnitude = float(np.linalg.norm(flow, axis=2).mean()) / dt
    label, scale = 'mixed', None
    confidence = float(inliers.mean()) if inliers is not None else 0.0
    if magnitude < .25:
        label = 'static'
    elif matrix is not None:
        scale = float(math.hypot(matrix[0, 0], matrix[1, 0]))
        center = np.array([w / 2, h / 2])
        translation = matrix[:, :2] @ center + matrix[:, 2] - center
        if abs(scale - 1) > .005 and confidence > .5:
            label = 'zoom_in' if scale > 1 else 'zoom_out'
        elif max(abs(translation)) > .25 and confidence > .5:
            if abs(translation[0]) > abs(translation[1]):
                label = 'pan_right' if translation[0] > 0 else 'pan_left'
            else:
                label = 'tilt_down' if translation[1] > 0 else 'tilt_up'
    return {'magnitude_px_per_s': magnitude, 'magnitude_frame_width_per_s': magnitude / w,
            'camera_estimate': label, 'scale': scale, 'confidence': confidence,
            'confidence_kind': 'affine inlier fraction, not calibrated probability',
            'method': 'Farneback flow and RANSAC similarity fit; object motion can mimic camera motion'}


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


def analyze_visual(source, info, scenes, entries, output):
    report = {'method': 'scene timing, sparse palette and 2fps low-resolution optical flow',
              'confidence': 'mixed measurements and explicitly labeled motion estimates',
              'motion': [], 'palettes': [], 'detections': []}
    durations = [row['end'] - row['start'] for row in scenes]
    report['cuts'] = {'count': max(0, len(scenes) - 1),
                      'per_second': max(0, len(scenes) - 1) / info['duration'],
                      'shot_durations': durations, 'mean': statistics.mean(durations),
                      'median': statistics.median(durations), 'minimum': min(durations),
                      'method': 'detected scene boundaries', 'confidence': 'scene detector dependent'}
    try:
        import cv2
        for index, scene in enumerate(scenes):
            candidates = [e for e in entries if scene['start'] <= e['time'] < scene['end']]
            if candidates:
                closest = min(candidates, key=lambda e: abs(e['time'] - (scene['start'] + scene['end']) / 2))
                image = cv2.imread(closest['file'])
                if image is not None:
                    report['palettes'].append({'scene': index, 'start': scene['start'], 'end': scene['end'],
                                                'sample_time': closest['time'], **palette(image)})
        detector = None
        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data'):
            detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        hog = cv2.HOGDescriptor() if hasattr(cv2, 'HOGDescriptor') else None
        if hog is not None:
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        report['presence_detection'] = {'method': 'OpenCV Haar/HOG', 'confidence': 'uncalibrated'}
        if detector is None or hog is None:
            report['presence_detection']['skipped'] = 'This OpenCV build lacks Haar and/or HOG detection'
        cap = cv2.VideoCapture(str(source))
        previous, previous_time, previous_scene = None, None, None
        t = 0.0
        try:
            while t < info['duration']:
                cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                ok, image = cap.read()
                if not ok:
                    break
                h, w = image.shape[:2]
                small = cv2.resize(image, (256, max(64, round(256 * h / w))))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                scene_id = next((i for i, scene in enumerate(scenes) if scene['start'] <= t < scene['end']), None)
                if previous is not None and previous_scene == scene_id:
                    report['motion'].append({'time': t, 'start': previous_time, 'end': t,
                                              **motion_estimate(previous, gray, t - previous_time)})
                if round(t * 2) % 2 == 0:
                    boxes = [] if detector is None or detector.empty() else detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                    people = hog.detectMultiScale(small, winStride=(8, 8), padding=(8, 8))[0] if hog is not None else []
                    sw, sh = small.shape[1], small.shape[0]
                    normalized = lambda rows: [[float(x / sw), float(y / sh), float((x + bw) / sw), float((y + bh) / sh)] for x, y, bw, bh in rows]
                    report['detections'].append({'time': t, 'face_count': len(boxes), 'faces': normalized(boxes),
                                                  'person_count': len(people), 'persons': normalized(people),
                                                  'method': 'OpenCV frontal Haar + HOG people',
                                                  'confidence': 'uncalibrated detections; stylized faces/poses may be missed'})
                previous, previous_time, previous_scene = gray, t, scene_id
                t += .5
        finally:
            cap.release()
        # Aggregate magnitudes into one-second intervals without inventing cross-cut flow.
        bins = {}
        for row in report['motion']:
            bins.setdefault(int(row['start']), []).append(row)
        report['motion_per_second'] = [
            {'start': second, 'end': min(second + 1, info['duration']),
             'magnitude_px_per_s': statistics.mean(r['magnitude_px_per_s'] for r in rows),
             'camera_estimate': max(rows, key=lambda r: r['confidence'])['camera_estimate'],
             'confidence': statistics.mean(r['confidence'] for r in rows)}
            for second, rows in sorted(bins.items())]
    except (ImportError, OSError, ValueError) as exc:
        report['skipped'] = f'Visual measurements unavailable: {exc}'
    save(output, report)
    return report
