"""Timeline join tests with fake measurement files; no media or network needed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from social_studio.timeline import build_timeline, build_events  # noqa: E402
from social_studio.summary import build_summary  # noqa: E402


def write(job, name, data):
    (job / name).write_text(json.dumps(data), encoding='utf-8')


def full_job(job):
    write(job, 'analysis.json', {'video': {'fps': '30/1', 'duration': 6.0}})
    write(job, 'scenes.json', [{'start': 0, 'end': 2.0, 'start_frame': 0, 'end_frame': 60},
                               {'start': 2.0, 'end': 6.0, 'start_frame': 60, 'end_frame': 180}])
    write(job, 'transitions.json', {'transitions': [{'start': 2.0, 'end': 2.2, 'start_frame': 60, 'end_frame': 66,
                                                      'type': 'whip', 'confidence': 0.8}]})
    write(job, 'visual_analysis.json', {'cuts': {'per_second': 0.17},
                                         'camera_segments': [{'start': 0.5, 'end': 1.5, 'type': 'push-in',
                                                              'direction': 'forward', 'easing': 'ease-out', 'confidence': 0.7}]})
    write(job, 'onscreen_text.json', {'records': [{'start': 0.3, 'end': 1.0, 'text': 'HELLO', 'bbox': [0, 0, 1, 1],
                                                    'confidence': 0.9, 'start_frame': 9, 'end_frame': 30, 'kind': 'caption'},
                                                   {'start': 3.0, 'end': 4.0, 'text': 'A|B', 'bbox': [0, 0, 1, 1]}]})
    write(job, 'audio_analysis.json', {'rms_curve': [{'time': i / 10, 'end': i / 10 + .1, 'dbfs': -10.0} for i in range(60)],
                                        'onsets': [0.45, {'time': 3.2, 'type': 'impact'}], 'beats': [1.0], 'tempo_bpm': 120,
                                        'integrated_lufs': -14.1, 'true_peak_dbtp': -1.2})
    write(job, 'transcript.json', {'segments': [{'start': 0.0, 'end': 1.0, 'text': 'hi there', 'words': [
        {'start': 0.0, 'end': 0.2, 'word': ' hi', 'probability': 0.9}, {'start': 0.5, 'end': 0.9, 'word': ' there', 'probability': 0.9}]}]})


class TimelineTests(unittest.TestCase):
    def test_full_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)
            full_job(job)
            tl = build_timeline(job)
            self.assertEqual(tl['missing'], [])
            tracks = {e['track'] for e in tl['events']}
            self.assertTrue({'cut', 'transition', 'camera', 'text', 'speech', 'music', 'sfx', 'energy'} <= tracks)
            for key in ('t_start', 't_end', 'frame_start', 'frame_end', 'track', 'value', 'source', 'confidence'):
                self.assertIn(key, tl['events'][0])
            self.assertEqual([r['t_start'] for r in tl['grid'][:3]], [0.0, 0.1, 0.2])
            self.assertEqual(tl['grid'][30]['t_start'], 3.0)
            self.assertEqual(len(tl['grid']), 30 + 6)
            row = {r['t_start']: r for r in tl['grid']}
            self.assertEqual(row[0.5]['speech'], 'there')
            self.assertEqual(row[0.3]['text'], 'HELLO')
            self.assertIn('push-in', row[0.5]['camera'])
            self.assertIn('impact', row[3.0]['audio'])
            self.assertEqual(row[0.0]['text'], '—')
            events = {(e['track'], e['value']) for e in tl['events']}
            self.assertIn(('transition', 'whip'), events)
            md = (job / 'TIMELINE.md').read_text(encoding='utf-8')
            self.assertTrue(md.startswith('# Zaman'))
            self.assertIn('A\\|B', md)

    def test_missing_files_listed(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)
            write(job, 'analysis.json', {'video': {'fps': '30000/1001', 'duration': 4.0}})
            write(job, 'transcript.json', {'segments': [{'start': 1.0, 'end': 2.0, 'text': 'no words here'}]})
            write(job, 'onscreen_text.json', {'records': [], 'skipped': 'no ocr'})
            tl = build_timeline(job)
            missing = {m['file']: m['reason'] for m in tl['missing']}
            self.assertIn('scenes.json', missing)
            self.assertIn('transitions.json', missing)
            self.assertIn('skipped', missing['onscreen_text.json'])
            row = {r['t_start']: r for r in tl['grid']}
            self.assertEqual(row[1.0]['speech'], 'no words here')  # segment fallback
            self.assertEqual(row[2.0]['speech'], '—')
            self.assertEqual(tl['grid'][0]['camera'], '—')

    def test_empty_dir_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            tl = build_timeline(Path(d))
            self.assertEqual(len(tl['missing']), 6)
            self.assertEqual(tl['events'], [])

    def test_motion_fallback_and_alt_names(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)
            write(job, 'analysis.json', {'video': {'fps': '25', 'duration': 2.0}})
            write(job, 'visual_analysis.json', {'motion_per_second': [
                {'start': 0, 'end': 1, 'magnitude_px_per_s': 5.0, 'camera_estimate': 'pan', 'confidence': 0.4}]})
            write(job, 'transitions.json', [{'start': 1.0, 'end': 1.1, 'kind': 'dissolve'}])
            events, missing, _ = build_events(job)
            cam = [e for e in events if e['track'] == 'camera']
            self.assertTrue(cam[0]['fallback'])
            self.assertEqual([e['value'] for e in events if e['track'] == 'transition'], ['dissolve'])
            self.assertEqual(cam[0]['frame_end'], 25)

    def test_summary_new_metrics_and_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)
            full_job(job)
            res = build_summary(job)
            m = res['metrics']
            self.assertEqual(m['integrated_lufs']['value'], -14.1)
            self.assertEqual(m['true_peak_dbtp']['value'], -1.2)
            self.assertAlmostEqual(m['transitions_per_second']['value'], 1 / 6.0)
            self.assertAlmostEqual(m['mean_caption_group_seconds']['value'], 0.85)
            self.assertEqual(res['hook_breakdown']['transition'], 1)
            self.assertEqual(res['hook_breakdown']['text'], 1)
            md = (job / 'summary.md').read_text(encoding='utf-8')
            self.assertNotIn('None', md)

    def test_summary_without_optional_files(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)
            write(job, 'analysis.json', {'video': {'fps': '30', 'duration': 5.0}})
            res = build_summary(job)
            self.assertIn('scenes.json', res['missing_files'])
            md = (job / 'summary.md').read_text(encoding='utf-8')
            self.assertIn('dosya yok', md)
            self.assertNotIn('None', md)


if __name__ == '__main__':
    unittest.main()
