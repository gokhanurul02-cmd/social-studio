"""Frame-accurate caption timeline tests on a synthetic video (no network)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from social_studio import captions as C
from social_studio import ocr
from social_studio.media import FFMPEG, video_info

W, H, FPS, FRAMES = 360, 640, 30, 72
FONT = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts' / 'verdanab.ttf'
# (first_frame, last_frame, text, animation)
SCRIPT = [(5, 19, 'hello world', 'cut'), (20, 39, 'second line', 'cut'),
          (48, 71, 'Dwayne Rock', 'cut')]
CAPTION_Y = 0.795


def _font(size):
    if FONT.is_file():
        return ImageFont.truetype(str(FONT), size)
    return ImageFont.load_default(size)


def _background(i):
    y, x = np.mgrid[0:H, 0:W]
    base = np.zeros((H, W, 3), np.uint8)
    base[..., 0] = 40 + (y * 120 // H)
    base[..., 1] = 120 + ((x + i) % 60)
    base[..., 2] = 200
    return Image.fromarray(base)


def render_frame(i, script, fade=None):
    img = _background(i)
    for a, b, text, _ in script:
        if a <= i <= b:
            layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            font = _font(26)
            bbox = d.textbbox((0, 0), text, font=font, stroke_width=2)
            x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
            y = int(CAPTION_Y * H) - 20
            d.text((x, y), text, font=font, fill=(255, 255, 255, 255), stroke_width=2,
                   stroke_fill=(0, 0, 0, 255), anchor='ls' if False else None)
            if fade and a <= i < a + fade:
                alpha = (i - a + 1) / (fade + 1)
                layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
            img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')
    return img


def make_video(path, script, fade=None):
    cmd = [str(FFMPEG), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FRAMES):
        p.stdin.write(np.asarray(render_frame(i, script, fade)).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError('ffmpeg failed')


class CaptionTimeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.video = cls.dir / 'captions.mp4'
        make_video(cls.video, SCRIPT)
        cls.fade_video = cls.dir / 'fade.mp4'
        make_video(cls.fade_video, [(10, 50, 'fade in text', 'fade')], fade=5)
        cls.info = video_info(cls.video)
        cls.region = {'y0': 0.70, 'y1': 0.86, 'mode': 'light'}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_change_frames_without_ocr(self):
        """Works with no OCR engine: change frames are exact to the frame."""
        tracks = C.track_regions(self.video, self.info, [self.region])
        self.assertEqual(tracks[0]['frames'], FRAMES)
        segs = [s for s in C.build_segments(tracks[0])]
        text = [(s['start'], s['end']) for s in segs if s['has_text']]
        for (first, last, _, _), (start, end) in zip(SCRIPT, text):
            self.assertLessEqual(abs(start - first), 1)
            self.assertLessEqual(abs(end - last), 1)
        self.assertEqual(len(text), len(SCRIPT))

    def test_scan_text_without_engine_reports_change_timeline(self):
        out = self.dir / 'noengine.json'
        with patch('social_studio.ocr.recognizer', return_value=(None, None, ['not installed'])):
            report = ocr.scan_text(self.video, self.info, out, regions=[self.region])
        self.assertIn('skipped', report)
        starts = [row['start_frame'] for row in report['change_timeline']]
        for first, _, _, _ in SCRIPT:
            self.assertTrue(any(abs(s - first) <= 1 for s in starts), (first, starts))
        with patch('social_studio.ocr.recognizer', return_value=(None, None, ['not installed'])):
            report = ocr.scan_text(self.video, self.info, self.dir / 'skip.json')
        self.assertIn('skipped', report)

    def test_scan_text_schema_with_stub_engine(self):
        """Stub engine: schema, kinds, style, safe zone, frame fields."""
        texts = iter([t for _, _, t, _ in SCRIPT])

        def stub(image):
            return []
        stub.line = lambda image: (next(texts), 0.95)
        out = self.dir / 'stub.json'
        with patch('social_studio.ocr.recognizer', return_value=('stub', stub, [])):
            report = ocr.scan_text(self.video, self.info, out, regions=[self.region])
        self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['method'], 'stub')
        recs = report['records']
        self.assertEqual([r['text'] for r in recs], [t for _, _, t, _ in SCRIPT])
        for rec, (first, last, _, _) in zip(recs, SCRIPT):
            for key in ['start', 'end', 'text', 'bbox', 'confidence', 'text_height_ratio', 'colors',
                        'start_frame', 'end_frame', 'kind', 'style', 'animation', 'safe_zone_violation']:
                self.assertIn(key, rec)
            self.assertLessEqual(abs(rec['start_frame'] - first), 1)
            self.assertAlmostEqual(rec['start'], rec['start_frame'] / FPS, places=3)
            self.assertEqual(rec['kind'], 'caption')
            self.assertEqual(rec['animation']['type'], 'cut')
            style = rec['style']
            self.assertEqual(style['fill_hex'], '#ffffff')
            self.assertEqual(style['align'], 'center')
            self.assertAlmostEqual(style['baseline_y_ratio'], CAPTION_Y + 0.0, delta=0.04)
            self.assertIsNotNone(style['font_size_ratio'])
        self.assertEqual(recs[0]['style']['case'], 'lower')
        self.assertEqual(recs[2]['style']['case'], 'title')
        summary = report['caption_style_summary']
        self.assertEqual(summary['group_count'], 3)
        self.assertEqual(summary['dominant_animation'], 'cut')
        self.assertIn('words_per_group', summary)

    def test_stroke_is_detected(self):
        frame = np.asarray(render_frame(10, SCRIPT).convert('RGB'))[:, :, ::-1].copy()
        rows = np.nonzero((frame.mean(axis=2) > 235).any(axis=1))[0]
        mask = C.fill_mask(frame, 'light')
        ys, xs = np.nonzero(mask)
        style = C.estimate_style(frame, (xs.min(), ys.min(), xs.max(), ys.max()), 'hello world')
        self.assertEqual(style['fill_hex'], '#ffffff')
        self.assertIsNotNone(style['stroke_hex'])
        self.assertGreater(style['stroke_px_ratio'], 0)
        self.assertTrue(len(rows) > 0)

    def test_fade_animation(self):
        tracks = C.track_regions(self.fade_video, self.info, [self.region])
        segs = C.build_segments(tracks[0])
        text = [s for s in segs if s['has_text']]
        self.assertTrue(text)
        anim = C.classify_animation(tracks[0], text[0], None)
        self.assertIn(anim['type'], ('fade', 'pop'))   # gradual entry is never a plain cut
        self.assertNotEqual(anim['type'], 'cut')

    @unittest.skipUnless(FONT.is_file(), 'Verdana Bold not installed')
    def test_font_candidates_find_verdana(self):
        frame = np.asarray(render_frame(10, SCRIPT).convert('RGB'))[:, :, ::-1].copy()
        mask = C._clean(C.fill_mask(frame, 'light'))
        ys, xs = np.nonzero(mask)
        crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        report = C.match_fonts([('hello world', crop)])
        if 'skipped' in report:
            self.skipTest(report['skipped'])
        self.assertEqual(report['candidates'][0]['font'], 'verdanab.ttf')
        self.assertEqual(len(report['candidates']), 3)

    def test_turkish_normalisation_and_non_latin_flag(self):
        result = ocr.normalize_text('  Çok  güzel\u2019 şey ')
        self.assertEqual(result['text'], "Çok güzel' şey")
        self.assertEqual(result['non_latin_ratio'], 0)
        bad = ocr.normalize_text('no\u4eba need')
        self.assertGreater(bad['non_latin_ratio'], 0)
        self.assertIn('\u4eba', bad['non_latin_chars'])
        tr = ocr.normalize_text('bu icin cok guzel')
        self.assertTrue(tr.get('turkish_suspected'))
        self.assertEqual(tr['turkish_diacritic_suggestions']['icin'], 'için')

    def test_case_classes(self):
        self.assertEqual(C.classify_case('now if you'), 'lower')
        self.assertEqual(C.classify_case('Now if you did'), 'sentence')
        self.assertEqual(C.classify_case('HELLO WORLD'), 'upper')
        self.assertEqual(C.classify_case('Dwayne Rock'), 'title')

    @unittest.skipUnless(ocr.recognizer()[1] is not None, 'no OCR engine installed')
    def test_real_engine_reads_synthetic_captions(self):
        report = ocr.scan_text(self.video, self.info, self.dir / 'real.json')
        self.assertNotIn('skipped', report, report.get('skipped'))
        got = [r['text'].casefold().replace('.', '') for r in report['records'] if r['kind'] == 'caption']
        self.assertEqual(got, ['hello world', 'second line', 'dwayne rock'])
        for rec, (first, _, _, _) in zip([r for r in report['records'] if r['kind'] == 'caption'], SCRIPT):
            self.assertLessEqual(abs(rec['start_frame'] - first), 1)


if __name__ == '__main__':
    unittest.main()
