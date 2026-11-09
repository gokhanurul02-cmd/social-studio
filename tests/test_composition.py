"""composition.py on synthetic frames (Pillow) and a tiny ffmpeg clip."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from social_studio import composition as cm  # noqa: E402

W, H = 180, 320
SKY, GROUND, LINE = (60, 170, 235), (120, 215, 245), (225, 245, 255)


def scene(subject=None, horizon=0.40, fill=None, ground_lines=True):
    """RGB scene: sky above horizon, light-blue grid floor below, optional subject box and flat colour block."""
    im = Image.new('RGB', (W, H), SKY)
    d = ImageDraw.Draw(im)
    hy = int(horizon * H)
    d.rectangle([0, hy, W, H], fill=GROUND)
    if ground_lines:
        for y in range(hy + 8, H, 14):
            d.line([0, y, W, y], fill=LINE, width=1)
        for x in range(-W, 2 * W, 22):
            d.line([x, H, W // 2 + (x - W // 2) // 6, hy], fill=LINE, width=1)
    if fill:
        d.rectangle(fill[0], fill=fill[1])
    if subject:
        d.rectangle(subject[0], fill=subject[1])
        d.ellipse([subject[0][0] + 2, subject[0][1] + 2, subject[0][0] + 14, subject[0][1] + 14], fill=(255, 255, 255))
    return np.asarray(im)[:, :, ::-1].copy()      # BGR


class FrameTests(unittest.TestCase):
    def test_small_centred_subject_is_wide_and_clean(self):
        r = cm.measure_frame(scene(subject=([80, 150, 100, 200], (230, 120, 30))))
        self.assertLess(r['subject_area'], 0.08)
        self.assertEqual(r['shot_type'], 'wide')
        self.assertAlmostEqual(r['centroid'][0], 0.5, delta=0.06)
        self.assertEqual(r['flat_fill_ratio'], 0.0)
        self.assertFalse(r['edge_cut'])
        bx, by, bw, bh = r['subject_bbox']
        self.assertLess(bw, 0.3)

    def test_flat_block_filling_frame_is_flagged_but_sky_is_not(self):
        yellow = ([0, 0, W, int(0.55 * H)], (215, 190, 30))
        r = cm.measure_frame(scene(fill=yellow))
        self.assertGreaterEqual(r['flat_fill_ratio'], 0.45)
        sky_only = cm.measure_frame(scene())
        self.assertLess(sky_only['flat_fill_ratio'], cm.LIMITS['flat_fill_ratio'])
        self.assertGreater(sky_only['flat_fill_ratio_incl_sky'], 0.2)  # sky is seen but exempted

    def test_subject_touching_edge_is_cut(self):
        big = ([40, 120, 150, H], (150, 90, 50))           # runs off the bottom
        r = cm.measure_frame(scene(subject=big))
        self.assertGreaterEqual(r['subject_area'], 0.3)
        self.assertTrue(r['edge_cut'], r['edge_contact'])
        self.assertEqual(r['edge_worst'], 'bottom')
        inside = cm.measure_frame(scene(subject=([40, 60, 140, 250], (150, 90, 50))))
        self.assertFalse(inside['edge_cut'])

    def test_horizon_row(self):
        for hz in (0.30, 0.55):
            y, conf, method = cm.horizon(scene(horizon=hz, ground_lines=False))
            self.assertIsNotNone(y)
            self.assertAlmostEqual(y, hz, delta=0.04)
            self.assertGreater(conf, 0.4)

    def test_thirds_distance_and_shot_class(self):
        self.assertAlmostEqual(cm.thirds_distance(1 / 3, 1 / 3), 0.0)
        self.assertGreater(cm.thirds_distance(0.5, 0.5), 0.2)
        self.assertEqual(cm.classify_shot(0.04, 3), 'wide')
        self.assertEqual(cm.classify_shot(0.2, 3), 'medium')
        self.assertEqual(cm.classify_shot(0.5, 3), 'close')
        self.assertEqual(cm.classify_shot(0.2, 120), 'crowd')

    def test_runs_merge_and_need_two_samples(self):
        samples = [{'t': t, 'flat_fill_ratio': v} for t, v in [(0.17, .4), (0.5, .4), (0.83, 0), (1.16, .4), (1.5, 0)]]
        ev = cm._runs(samples, 'flat_fill_ratio', 2, 0.27)
        self.assertEqual(len(ev), 1)
        self.assertAlmostEqual(ev[0]['t_start'], 0.0, delta=0.01)


class VideoTests(unittest.TestCase):
    def test_analyze_composition_writes_schema(self):
        from social_studio.media import FFMPEG
        import cv2
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frames = tmp / 'f'
            frames.mkdir()
            n = 12
            for i in range(n):
                if i < 6:    # flat yellow block at the start
                    img = scene(fill=([0, 0, W, int(0.5 * H)], (215, 190, 30)), subject=([70, 160, 110, 260], (200, 80, 40)))
                else:
                    img = scene(subject=([80, 150, 100, 200], (230, 120, 30)))
                cv2.imwrite(str(frames / f'{i:03d}.png'), img)
            video = tmp / 'clip.mp4'
            subprocess.run([str(FFMPEG), '-v', 'error', '-y', '-framerate', '6', '-i', str(frames / '%03d.png'),
                            '-pix_fmt', 'yuv420p', str(video)], check=True)
            job = tmp / 'job'
            job.mkdir()
            (job / 'analysis.json').write_text(json.dumps({'source': str(video), 'video': {
                'width': W, 'height': H, 'fps': '6', 'duration': 2.0}}), encoding='utf-8')
            rep = cm.analyze_composition(job, fps_sample=6)
            saved = json.loads((job / 'composition.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['schema'], cm.SCHEMA)
            self.assertGreaterEqual(len(saved['samples']), 10)
            for key in ('stats', 'flags', 'segments', 'scenes', 'method', 'confidence'):
                self.assertIn(key, saved)
            self.assertTrue(saved['flags']['flat_fill'], saved['stats'])
            self.assertLess(saved['flags']['flat_fill'][0]['t_start'], 0.3)
            self.assertLess(saved['flags']['flat_fill'][0]['t_end'], 1.3)
            self.assertIsNotNone(cm.load_composition(job))
            self.assertEqual(rep['sample_fps'], 6)


if __name__ == '__main__':
    unittest.main()
