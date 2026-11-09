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
            # H.264/YUV and platform font rasterizers can shift white by a few levels.
            channels = [int(style['fill_hex'][i:i+2], 16) for i in [1, 3, 5]]
            self.assertTrue(all(c >= 248 for c in channels), style['fill_hex'])
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


def _rec(start, end, text, bbox, region, conf=0.95, h=0.04, lines=1, fps=30):
    return {'start': start / fps, 'end': (end + 1) / fps, 'start_frame': start, 'end_frame': end,
            'duration_frames': end - start + 1, 'text': text, 'bbox': bbox, 'region': region,
            'confidence': conf, 'text_height_ratio': h, 'lines': lines,
            'style': {'stroke_hex': '#000000', 'shadow': False, 'words': text.split(), 'case': 'upper',
                      'fill_hex': '#ffffff', 'stroke_px_ratio': 0.002, 'font_size_ratio': 0.04,
                      'baseline_y_ratio': 0.8, 'align': 'center'},
            'animation': {'type': 'cut', 'confidence': 'high'}, 'safe_zone_violation': False,
            'confidence_flags': [], 'confidence_adjusted': conf}


TRANSCRIPT = {'language': 'tr', 'segments': [
    {'start': 0.0, 'end': 4.0, 'text': 'Tüketmeyin için çok sağlıklı su',
     'words': [{'word': ' Tüketmeyin', 'start': 0.0, 'end': 1.0}, {'word': ' için', 'start': 1.0, 'end': 1.5},
               {'word': ' çok', 'start': 1.5, 'end': 2.0}, {'word': ' sağlıklı', 'start': 2.0, 'end': 3.0},
               {'word': ' su', 'start': 3.0, 'end': 4.0}]}]}


class TurkishAndKinds(unittest.TestCase):
    def test_transcript_correction_and_word_split(self):
        vocab = ocr.build_vocab(TRANSCRIPT)
        text, fixes = ocr.correct_text('TUKETMEYIN icin COK', vocab)
        self.assertEqual(text, 'TÜKETMEYİN için ÇOK')
        self.assertTrue(all(f['method'] == 'transcript-diacritic' for f in fixes))
        text, fixes = ocr.correct_text('SAGLIKLISU', vocab)
        self.assertEqual(text, 'SAĞLIKLI SU')
        self.assertEqual(fixes[0]['method'], 'transcript-word-split')
        # unknown words are never invented
        self.assertEqual(ocr.correct_text('BAMBASKA', vocab)[0], 'BAMBASKA')
        # no transcript, no change
        self.assertEqual(ocr.correct_text('TUKETMEYIN', None), ('TUKETMEYIN', []))

    @unittest.skipUnless(ocr.ocr_model_status()['ok'] and ocr.recognizer()[1] is not None,
                         'latin OCR model not installed')
    def test_latin_model_reads_turkish_letters(self):
        import cv2
        _, rec, _ = ocr.recognizer()
        self.assertTrue(rec.turkish)
        img = Image.new('RGB', (1500, 160), 'white')
        ImageDraw.Draw(img).text((20, 40), 'SAĞLIKSIZ SU TÜKETMEYİN', font=_font(64), fill='black')
        arr = np.asarray(img)[:, :, ::-1].copy()
        ys, xs = np.nonzero(arr[:, :, 0] < 128)
        tight = cv2.copyMakeBorder(arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 14, 14, 14, 14,
                                   cv2.BORDER_CONSTANT, value=(255, 255, 255))
        text, conf = rec.line(tight)
        self.assertEqual(ocr.tr_fold(text).replace(' ', ''), 'sagliksizsutuketmeyin')
        self.assertIn('Ü', text)                       # the Chinese/English vocabulary cannot output this
        fixed, fixes = ocr.correct_text(text, ocr.build_vocab(TRANSCRIPT), harmony=True)
        self.assertEqual(fixed, 'SAĞLIKSIZ SU TÜKETMEYİN')   # Ğ via lexicon, İ via vowel harmony
        self.assertTrue(fixes)

    def test_artifact_cleanup(self):
        self.assertEqual(ocr.clean_artifacts('| the same thing')[0], 'the same thing')
        self.assertEqual(ocr.clean_artifacts('to-tow-the-trucks')[0], 'to tow the trucks')
        self.assertEqual(ocr.clean_artifacts('A-101')[0], 'A-101')

    def test_logo_variants_merge_and_scene_text_split(self):
        fps, total = 30, 600
        regions = [{'mode': 'light'}, {'mode': 'edge'}, {'mode': 'light'}]
        logo_box = [0.27, 0.88, 0.73, 0.97]
        variants = ['Mudanya SU OTOMATI', 'Mudanga SUSTOMATI', '(Mndawn SILSTOMATI', 'Mudanya', 'Hudaun VNOIGTISI',
                    'Mudanya SULOTOMATI', 'CMudanya SULSTOMATI', 'udaja']
        records = [_rec(i * 70, i * 70 + 60, variants[i % len(variants)], logo_box, 2, conf=0.6 + 0.04 * (i % 8))
                   for i in range(8)]
        captions = [(0, 'ALPAR YAPI', 0.3), (90, 'HIZMETINIZDE', 0.3), (200, 'KOLAY ODEME', 0.3)]
        for start, text, y in captions:
            records.append(_rec(start, start + 60, text, [0.2, y, 0.8, y + 0.05], 0))
        records.append(_rec(40, 300, 'sumatic HEMEN ARAYIN 0545 3031616 BAGISIKLIK FILTRELENMIS ICECEK MINERALLI SU 25 SANIYE',
                            [0.1, 0.4, 0.9, 0.7], 1, conf=0.7, h=0.015, lines=3))
        words = [('alpar', 0.0, 1.0), ('yapı', 1.0, 2.0), ('hizmetinizdedir', 3.0, 4.5), ('ödeme', 7.0, 8.0)]
        out = C.classify_kinds(records, regions, fps, total, words)
        kinds = [r['kind'] for r in out]
        self.assertEqual(kinds.count('logo') + kinds.count('watermark'), 1)
        logo = [r for r in out if r['kind'] in ('logo', 'watermark')][0]
        self.assertEqual(logo['merged_records'], 8)
        self.assertGreaterEqual(len(logo['appearances']), 1)
        self.assertIn('variants', logo)
        self.assertEqual(kinds.count('caption'), 3)
        self.assertEqual(kinds.count('scene_text'), 1)
        self.assertEqual(len(out), 5)
        summary = C.style_summary(out, fps, {})
        self.assertEqual(summary['group_count'], 3)

    def test_changing_texts_in_one_band_stay_captions(self):
        regions = [{'mode': 'light'}]
        texts = ['to pull them', 'to pull the truck', 'to tow the trucks', 'to get them', 'you would need', 'you would need']
        records = [_rec(i * 20, i * 20 + 14, t, [0.25, 0.77, 0.75, 0.81], 0) for i, t in enumerate(texts)]
        out = C.classify_kinds(records, regions, 30, 400, None)
        self.assertEqual([r['kind'] for r in out], ['caption'] * 6)


if __name__ == '__main__':
    unittest.main()
