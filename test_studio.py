"""Real-media integration checks. Artifacts stay under jobs/verification-* for inspection."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from unittest.mock import patch
import contextlib
import importlib.util
import json
import os
import hashlib
import zipfile
import unittest
import studio


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class StudioChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = studio.ROOT/'jobs'/('verification-'+studio.stamp())
        cls.work.mkdir(parents=True)
        cls.source = cls.work/'source.mp4'
        cls.other = cls.work/'other.mp4'
        studio.run([studio.FFMPEG, '-v', 'error', '-n', '-f', 'lavfi', '-i',
                    'testsrc2=size=96x160:rate=10:duration=1', '-an', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', cls.source], capture=True)
        studio.run([studio.FFMPEG, '-v', 'error', '-n', '-f', 'lavfi', '-i',
                    'color=blue:size=80x120:rate=5:duration=0.6', '-an', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', cls.other], capture=True)

    def test_01_probe_and_missing_source(self):
        info = studio.video_info(self.source)
        self.assertEqual((info['width'],info['height']), (96,160))
        self.assertEqual(info['frames'],10)
        self.assertFalse(info['has_audio'])
        with self.assertRaises(FileNotFoundError):
            studio.input_file(str(self.work/'missing.mp4'), self.work)

    def test_02_analysis_and_existing_job_protection(self):
        out = self.work/'analysis'
        studio.analyze(str(self.source), out, speech=False)
        self.assertTrue((out/'contact-sheet.jpg').is_file())
        self.assertTrue((out/'scenes.json').is_file())
        self.assertFalse(studio.load(out/'analysis.json')['transcript_exists'])
        entries = studio.load(out/'frames.json')
        self.assertTrue(all(0 <= x['time'] <= .91 for x in entries))
        with self.assertRaises(FileExistsError):
            studio.analyze(str(self.other), out, speech=False)
        self.assertEqual(studio.load(out/'analysis.json')['source'], str(self.source.resolve()))

    def test_03_comparison_identity_and_known_mismatch(self):
        same = studio.compare(self.source, self.source, self.work/'same')
        different = studio.compare(self.source, self.other, self.work/'different')
        self.assertEqual(same['mean_mae_255'],0)
        self.assertEqual(same['compared_frames'],10)
        self.assertFalse(different['dimensions_match'])
        self.assertFalse(different['fps_match'])
        self.assertGreater(different['mean_mae_255'],10)
        self.assertLess(different['duration_delta'],0)

    def test_04_analytics_missing_and_zero_denominator(self):
        file = self.work/'posts.json'
        studio.save(file, [{'id':'reach','reach':100,'likes':10,'comments':2,'shares':3,'saves':5},
                           {'id':'view','views':200,'likes':10}, {'id':'empty','reach':0,'views':0}])
        out = self.work/'performance.json'
        studio.analytics(SimpleNamespace(file=str(file),out=str(out)))
        rows = {p['id']:p for p in studio.load(out)['posts']}
        self.assertEqual(rows['reach']['engagement_rate'],20)
        self.assertEqual(rows['view']['engagement_rate'],5)
        self.assertIn('saves',rows['view']['missing_metrics'])
        self.assertIsNone(rows['empty']['engagement_rate'])
        studio.save(file,[{'reach':-1}])
        with self.assertRaises(ValueError):
            studio.analytics(SimpleNamespace(file=str(file),out=str(out)))

    def test_05_calendar_offsets_and_existing_copy_protection(self):
        args = SimpleNamespace(start='2026-11-06',brand='Fixture',platform='instagram',days=3,
                               out=str(self.work/'plan'))
        studio.calendar(args)
        rows = studio.load(Path(args.out)/'calendar.json')
        self.assertEqual(rows[2]['date'],'2026-11-08')
        self.assertTrue(all(r['status']=='draft' for r in rows))
        self.assertEqual(rows[0]['timezone'],'Europe/Istanbul')
        with self.assertRaises(FileExistsError):
            studio.calendar(args)

    def test_06_url_ingestion_over_http(self):
        server = ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(self.work)))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        out = self.work/'url-import'
        out.mkdir()
        try:
            path = studio.input_file(f'http://127.0.0.1:{server.server_port}/source.mp4',out)
            self.assertEqual(studio.video_info(path)['frames'],10)
            self.assertTrue((out/'source-metadata.json').is_file())
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_07_inbox_idempotency(self):
        directory = self.work/'inbox'
        directory.mkdir()
        target = directory/'drop.mp4'
        target.write_bytes(self.source.read_bytes())
        os.utime(target,(1000000000,1000000000))
        args = SimpleNamespace(folder=str(directory),watch=False,no_speech=True,model='small')
        with patch.object(studio,'ROOT',self.work):
            studio.inbox(args)
            journal = studio.load(directory/'.social-inbox.json')
            self.assertEqual(len(journal),1)
            job = Path(next(iter(journal.values()))['job'])
            self.assertTrue((job/'analysis.json').is_file())
            studio.inbox(args)
            self.assertEqual(studio.load(directory/'.social-inbox.json'),journal)
        self.assertEqual(target.read_bytes(),self.source.read_bytes())

    def test_08_launch_arguments_are_not_shell_code(self):
        source = str(self.work/'source & example.mp4')
        for agent in ['codex','claude']:
            with patch.object(studio,'run') as mocked, patch.object(studio.shutil, 'which', return_value=agent + '.exe'):
                studio.launch(SimpleNamespace(agent=agent,source=source,prompt='Use literal $ and ` text'))
                argv = mocked.call_args.args[0]
                self.assertIsInstance(argv,list)
                self.assertIn('source & example.mp4',argv[-1])
                self.assertIn('literal $ and ` text',argv[-1])

    def test_09_portable_tools_and_repository_skills(self):
        from social_studio import media
        with patch.dict(os.environ, {'SOCIAL_FFMPEG': str(self.source)}):
            self.assertEqual(media.resolve_tool('ffmpeg'), self.source)
        self.assertIn('Scripts' if os.name == 'nt' else 'bin', str(media.venv_python(self.work)))
        earshot = self.work / 'earshot-portable'
        earshot.mkdir()
        (earshot / 'run.py').write_text('# fixture', encoding='utf-8')
        with patch.object(media, 'ROOT', self.work / 'tool'), patch.dict(os.environ, {'SOCIAL_EARSHOT': ''}):
            self.assertEqual(media.find_earshot(), earshot)
        for file in (studio.ROOT / 'agent-skills').rglob('SKILL.md'):
            self.assertTrue(file.read_text(encoding='utf-8').startswith('---'))

    def test_10_motion_graphics_cut_detection(self):
        source = self.work / 'cuts.mp4'
        argv = [studio.FFMPEG, '-v', 'error', '-n']
        for color in ['red', 'green', 'blue', 'white']:
            argv += ['-f', 'lavfi', '-i', f'color={color}:s=96x160:r=30:d=1']
        argv += ['-filter_complex', '[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]',
                 '-map', '[v]', '-c:v', 'libx264', str(source)]
        studio.run(argv, capture=True)
        out = self.work / 'motion-cuts'
        studio.analyze(str(source), out, speech=False)
        observed = [row['start_frame'] for row in studio.load(out / 'scenes.json')[1:]]
        self.assertEqual(len(observed), 3)
        for got, expected in zip(observed, [30, 60, 90]):
            self.assertLessEqual(abs(got - expected), 1)

    def test_11_publication_handoff_is_portable_and_offline(self):
        args = SimpleNamespace(source=str(self.source),out=str(self.work/'handoff.v1'),brand='Fixture',
            platform='instagram',scheduled_at='2026-11-06T16:00:00Z',caption='Deneme açıklaması',caption_file=None)
        archive = studio.handoff(args)
        self.assertEqual(archive.name,'handoff.v1.zip')
        with zipfile.ZipFile(archive) as z:
            manifest = json.loads(z.read('publication.json'))
            self.assertEqual(manifest['status'],'draft')
            self.assertEqual(manifest['scheduled_at'],'2026-11-06T19:00:00+03:00')
            for media in manifest['media']:
                self.assertFalse(Path(media['file']).is_absolute())
                raw = z.read(media['file'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),media['sha256'])
            primary = next(m for m in manifest['media'] if m['role']=='primary')
            self.assertEqual(z.read(primary['file']),self.source.read_bytes())
        with self.assertRaises(FileExistsError):
            studio.handoff(args)

    def test_12_handoff_requires_explicit_time_zone(self):
        args = SimpleNamespace(source=str(self.source),out=str(self.work/'invalid-handoff'),brand='',
            platform='instagram',scheduled_at='2026-11-06T19:00:00',caption='',caption_file=None)
        with self.assertRaises(ValueError):
            studio.handoff(args)
        self.assertFalse(Path(args.out).exists())

    def test_13_ocr_merging_and_optional_skip(self):
        from social_studio.ocr import scan_text, describe_text
        import numpy as np
        image = np.zeros((160, 96, 3), dtype=np.uint8)
        row = {'text': 'HELLO', 'confidence': .9, 'quad': [[1, 1], [90, 1], [90, 20], [1, 20]]}
        item = describe_text(row, image, 0, .25)
        self.assertIn('top_12_percent', item['safe_area_violations'])
        self.assertAlmostEqual(item['text_height_ratio'], 19 / 160)
        with patch('social_studio.ocr.recognizer', return_value=('fixture', lambda image: [row], [])):
            report = scan_text(self.source, studio.video_info(self.source), self.work / 'ocr.json')
        self.assertEqual(len(report['records']), 1)
        self.assertEqual(report['records'][0]['end'], 1)
        with patch('social_studio.ocr.recognizer', return_value=(None, None, ['not installed'])):
            report = scan_text(self.source, studio.video_info(self.source), self.work / 'ocr-skip.json')
        self.assertIn('skipped', report)

    def test_14_audio_energy_silence_and_alignment(self):
        from social_studio.audio_analysis import analyze_audio, cut_alignment
        source = self.work / 'tone.wav'
        studio.run([studio.FFMPEG, '-v', 'error', '-n', '-f', 'lavfi', '-i',
                    'sine=frequency=440:sample_rate=16000:duration=2', source], capture=True)
        with patch.dict('sys.modules', {'librosa': None}):
            report = analyze_audio(source, {'has_audio': True, 'duration': 2}, self.work / 'tone.json')
        self.assertEqual(len(report['rms_curve']), 20)
        self.assertAlmostEqual(report['rms_curve'][5]['dbfs'], -21.07, delta=.2)
        self.assertTrue(report['loudness_curve'])
        self.assertIn('skipped', report['rhythm'])
        aligned = cut_alignment([{'start': 0}, {'start': 1.02}], [1])
        self.assertAlmostEqual(aligned['cuts'][0]['nearest_beat_ms'], 20)
        self.assertEqual(aligned['aligned_ratio'], 1)
        report = analyze_audio(self.source, studio.video_info(self.source), self.work / 'silent.json')
        self.assertIn('skipped', report)

    def test_15_visual_palette_motion_and_sampling_limit(self):
        from social_studio.visual import palette, motion_estimate
        import cv2
        import numpy as np
        image = np.zeros((160, 96, 3), np.uint8)
        image[:, :, 2] = 255
        colors = palette(image)
        self.assertAlmostEqual(sum(c['ratio'] for c in colors['colors']), 1)
        self.assertEqual(colors['colors'][0]['hex'], '#ff0000')
        rng = np.random.default_rng(123)
        gray = rng.integers(0, 255, (160, 96), dtype=np.uint8)
        moved = cv2.warpAffine(gray, np.float32([[1, 0, 3], [0, 1, 0]]), (96, 160))
        motion = motion_estimate(gray, moved, .5)
        self.assertEqual(motion['camera_estimate'], 'pan_right')
        out = self.work / 'limited'
        studio.analyze(str(self.source), out, speech=False, max_frames=2)
        self.assertLessEqual(len(studio.load(out / 'frames.json')), 2)
        self.assertTrue((out / 'visual_analysis.json').is_file())

    def test_16_summary_provenance_and_unmeasured_values(self):
        out = self.work / 'summary-test'
        with patch('social_studio.ocr.recognizer', return_value=(None, None, ['fixture absent'])):
            studio.analyze(str(self.source), out, speech=False)
        summary = studio.load(out / 'summary.json')
        self.assertEqual(summary['metrics']['hook_cuts']['value'], 0)
        self.assertIsNone(summary['metrics']['words_per_minute']['value'])
        self.assertIsNone(summary['metrics']['hook_event_density']['value'])
        self.assertIn('ocr', summary['skipped'])
        for row in summary['metrics'].values():
            self.assertTrue(all(key in row for key in ['method', 'confidence', 'source']))
        self.assertTrue((out / 'summary.md').exists())

    def test_17_perceptual_and_audio_timing(self):
        from social_studio.perceptual import ssim, audio_delay, match_times
        import numpy as np
        image = np.random.default_rng(4).integers(0, 255, (80, 80, 3), dtype=np.uint8)
        self.assertAlmostEqual(ssim(image, image), 1)
        self.assertEqual(ssim(np.zeros((2, 2, 3)), np.zeros((2, 2, 3))), 1)
        self.assertIn('skipped', audio_delay(np.array([]), np.array([])))
        self.assertLess(ssim(image, 255 - image), 0)
        source = np.random.default_rng(5).normal(size=16000)
        target = np.concatenate([np.zeros(1600), source])
        self.assertAlmostEqual(audio_delay(source, target)['delay_ms'], 100, delta=1)
        self.assertAlmostEqual(match_times([1, 2], [1.1, 2.1], 30)['mean_absolute_delta_frames'], 3)
        same = studio.compare(self.source, self.source, self.work / 'perceptual-same')
        self.assertAlmostEqual(same['mean_ssim'], 1)
        self.assertTrue(same['scene_scores'])
        self.assertIn('skipped', same['audio_comparison'])
        with self.assertRaises(FileExistsError):
            studio.compare(self.source, self.source, self.work / 'perceptual-same')


    def test_18_performance_join_ratios_and_correlations(self):
        from social_studio.performance import analyze_posts, pearson
        source = self.work / 'export.json'
        rows = []
        for i in range(1, 4):
            job = self.work / f'performance-{i}'
            studio.save(job / 'summary.json', {'metrics': {'hook_event_density': {'value': i}}})
            rows.append({'video_id': job.name, 'views': 100, 'likes': i,
                         'avg_watch_time': i * 2, 'duration': 10, 'retention_3s': '65%',
                         'completion_rate': .5, 'follows': 2})
        report = analyze_posts(rows, source)
        self.assertEqual(report['posts'][0]['retention_3s_ratio'], .65)
        self.assertEqual(report['posts'][0]['follows_per_1000_views'], 20)
        corr = next(r for r in report['correlations'] if r['feature'] == 'hook_event_density' and r['outcome'] == 'watch_ratio')
        self.assertEqual(corr['n'], 3)
        self.assertAlmostEqual(corr['r'], 1)
        self.assertIsNone(pearson([(1, 2), (2, 3)])['r'])
        self.assertIsNone(pearson([(1, 2)] * 3)['r'])
        missing = analyze_posts([{'views': 0, 'avg_watch_time': 2}], source)['posts'][0]
        self.assertIsNone(missing['watch_ratio'])
        self.assertIsNone(missing['retention_3s_ratio'])
        for row in [{'retention_3s': 65}, {'avg_watch_time': 'NaN'}, {'follows': -1}]:
            with self.assertRaises(ValueError):
                analyze_posts([row], source)

    def test_20_offline_analysis_without_optional_engines(self):
        source = self.work / 'offline-input.mp4'
        studio.run([studio.FFMPEG, '-v', 'error', '-n', '-f', 'lavfi', '-i',
                    'testsrc2=size=96x160:rate=10:duration=1', '-f', 'lavfi', '-i',
                    'sine=frequency=440:duration=1', '-c:v', 'libx264', '-c:a', 'aac', '-shortest', source], capture=True)
        out = self.work / 'offline-example'
        with patch('social_studio.ocr.recognizer', return_value=(None, None, ['engines absent'])), \
             patch('social_studio.audio_analysis._spectral_speech_intervals', side_effect=ImportError('scipy absent')), \
             patch('social_studio.audio_analysis.KWeighted', side_effect=ImportError('scipy absent')), \
             patch('social_studio.audio_analysis.analyze_rhythm', side_effect=ImportError('librosa absent')), \
             patch('faster_whisper.WhisperModel', side_effect=OSError('model not cached')) as whisper, \
             patch('socket.create_connection', side_effect=AssertionError('No network in tests')):
            studio.analyze(str(source), out)
        self.assertTrue(whisper.call_args.kwargs['local_files_only'])
        for filename in ['analysis.json', 'onscreen_text.json', 'audio_analysis.json',
                         'visual_analysis.json', 'summary.json', 'summary.md', 'REBUILD.md']:
            self.assertTrue((out / filename).is_file(), filename)
        manifest = studio.load(out / 'analysis.json')
        self.assertIn('skipped', manifest['measurements']['ocr'])
        self.assertIn('skipped', manifest['transcription'])
        audio = studio.load(out / 'audio_analysis.json')
        self.assertIn(len(audio['rms_curve']), [10, 11])  # AAC may add a partial tail bin.
        self.assertTrue(audio['loudness_curve'])
        self.assertIn('skipped', audio['rhythm'])

    def test_19_audio_comparison_skips_warmup_bins_and_text_delta(self):
        from social_studio.comparison_details import audio_comparison, timeline_comparison
        import numpy as np
        samples = np.random.default_rng(7).normal(size=16000)
        data = {'audio': {'onsets': [.5], 'loudness_curve': [
            {'momentary_lufs': None}, {'momentary_lufs': -20}]},
            'scenes': [{'start': 0}, {'start': 1}],
            'text': {'records': [{'text': 'Merhaba', 'start': .2, 'end': .8}]}}
        with patch('social_studio.audio_analysis.pcm', return_value=samples):
            result = audio_comparison('a', 'b', data, data, 30)
        self.assertEqual(result['loudness_compared_bins'], 1)
        self.assertEqual(result['loudness_curve_rmse_lu'], 0)
        other = {**data, 'text': {'records': [{'text': 'Merhaba', 'start': .3, 'end': .9}]}}
        self.assertAlmostEqual(timeline_comparison(data, other, 30)['text']['mean_absolute_delta_frames'], 3)


if __name__ == '__main__':
    os.environ['PYTHONUTF8']='1'
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StudioChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    studio.save(studio.ROOT/'test-results.json',{
        'count':result.testsRun,'passed':result.wasSuccessful(),
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'artifacts':str(StudioChecks.work),'checked_at':studio.datetime.now(studio.IST).isoformat()})
    sys.exit(0 if result.wasSuccessful() else 1)
