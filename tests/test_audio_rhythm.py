"""Synthetic-signal tests for loudness, rhythm, event and speech/music analysis (ffmpeg lavfi sources)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from social_studio import audio_analysis as aa  # noqa: E402
from social_studio.media import FFMPEG, run  # noqa: E402


def make(path, *lavfi, af=None, duration=None, channels=1):
    args = [FFMPEG, '-v', 'error', '-y']
    for src in lavfi:
        args += ['-f', 'lavfi', '-i', src]
    if len(lavfi) > 1:
        args += ['-filter_complex', af, '-map', '[o]']
    elif af:
        args += ['-af', af]
    args += ['-ac', str(channels), '-ar', '22050', path]
    run(args, capture=True)
    return path


class AudioRhythmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        # 120 BPM click track: a decaying 1.5 kHz burst every 0.5 s for 10 s
        cls.clicks = make(cls.dir / 'clicks.wav',
                          'aevalsrc=0.8*sin(2*PI*1500*mod(t\\,0.5))*exp(-60*mod(t\\,0.5)):s=22050:d=10')
        cls.silence = make(cls.dir / 'silence.wav', 'anullsrc=r=22050:cl=mono', af='atrim=duration=3')
        # quiet tone + noise swell 1.0 -> 3.0 s, fading out by 3.5 s
        cls.whoosh = make(
            cls.dir / 'whoosh.wav', 'sine=f=220:r=22050:d=5', 'anoisesrc=d=5:c=white:r=22050:a=0.5',
            af="[0:a]volume=0.03[t];[1:a]highpass=f=1500,"
               "volume='if(lt(t,1),0,if(lt(t,3),(t-1)/2,max(0,1-(t-3)/0.5)))':eval=frame[n];"
               "[t][n]amix=inputs=2:normalize=0[o]")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def analyze(self, path, duration, **kw):
        out = self.dir / (Path(path).stem + '.json')
        return aa.analyze_audio(path, {'has_audio': True, 'duration': duration}, out, **kw)

    def test_click_track_tempo_beats_onsets(self):
        report = self.analyze(self.clicks, 10)
        self.assertAlmostEqual(report['tempo_bpm'], 120, delta=3)
        self.assertGreater(report['tempo_confidence'], .5)
        beats = report['beats']
        self.assertGreaterEqual(len(beats), 18)
        self.assertAlmostEqual(beats[1] - beats[0], .5, delta=.03)
        onsets = report['onsets']
        self.assertGreaterEqual(len(onsets), 18)
        grid = [i * .5 for i in range(20)]
        errors = [min(abs(o - g) for g in grid) for o in onsets]
        self.assertLess(max(errors), .015)           # millisecond-level, not 100 ms blocks
        self.assertIn('beat_info', report)
        self.assertTrue(report['downbeats']['times'])
        for event in report['onset_events']:
            self.assertIn('strength', event)
            self.assertIn(event['class'], report['onset_method']['classes'])

    def test_click_events_classified_as_clicks_or_hits_not_sweeps(self):
        report = self.analyze(self.clicks, 10)
        classes = {e['class'] for e in report['onset_events']}
        self.assertTrue(classes <= {'pop_click', 'impact', 'tonal_note', 'unclassified'}, classes)
        self.assertEqual(report['sfx_candidates'], [])

    def test_silence_has_no_events_or_loudness(self):
        report = self.analyze(self.silence, 3)
        self.assertEqual(report['onsets'], [])
        self.assertEqual(report['beats'], [])
        self.assertIsNone(report['integrated_lufs'])
        self.assertTrue(all(row['momentary_lufs'] is None for row in report['loudness_curve']))

    def test_whoosh_detected_as_noise_sweep(self):
        report = self.analyze(self.whoosh, 5)
        sweeps = report['sfx_candidates']
        self.assertTrue(sweeps, 'no whoosh/riser found')
        best = max(sweeps, key=lambda s: s['confidence'])
        self.assertIn(best['type'], ('whoosh', 'riser'))
        self.assertAlmostEqual(best['peak_time'], 3.0, delta=.35)
        self.assertGreaterEqual(best['rise_s'], 1.0)
        self.assertLess(best['confidence'], .9)       # always an estimate

    def test_lufs_matches_normalized_tone(self):
        raw = make(self.dir / 'tone_raw.wav', 'sine=f=1000:r=48000:d=8', af='volume=-20dB')
        first = aa.measure_ebur128(raw)
        gain = -14 - first['integrated_lufs']
        norm = make(self.dir / 'tone14.wav', 'sine=f=1000:r=48000:d=8', af=f'volume=-20dB,volume={gain}dB')
        report = self.analyze(norm, 8)
        self.assertAlmostEqual(report['integrated_lufs'], -14.0, delta=.3)
        self.assertAlmostEqual(report['lra'], 0.0, delta=.3)
        self.assertEqual(report['loudness_range']['lra_lu'], report['lra'])
        # a -14 LUFS 1 kHz sine (rms = peak/sqrt2) has true peak ~ -14 + 3.01 - 0.7(K) dBTP: just check sanity
        self.assertLess(report['true_peak_dbtp'], -8)
        self.assertGreater(report['true_peak_dbtp'], -14)
        # independent K-weighted implementation agrees with ebur128 within 0.3 LU
        samples = aa._pcm_stereo(norm, channels=1)
        self.assertAlmostEqual(aa.interval_lufs(samples), report['integrated_lufs'], delta=.3)

    def test_loudness_warmup_values_are_null(self):
        report = self.analyze(self.whoosh, 5)
        curve = report['loudness_curve']
        early = [r for r in curve if r['time'] < .4 - 1e-6]
        self.assertTrue(early)
        for row in early:
            self.assertIsNone(row['momentary_lufs'])
            self.assertIn('warm-up', row['note'])
        later = [r for r in curve if r['time'] >= 1]
        self.assertTrue(all(r['momentary_lufs'] is None or r['momentary_lufs'] > -100 for r in later))
        self.assertIn('null_values_note', report['loudness_method'])

    def test_speech_music_bed_and_fade(self):
        # music bed at ~-26 dBFS, 'speech' (loud tone bursts) at 0-2 s and 2.5-4 s; music fades out 4.6-5.0 s
        bed = "aevalsrc=0.05*(sin(2*PI*220*t)+sin(2*PI*330*t))*min(1\\,max(0\\,(5-t)/0.4)):s=22050:d=5"
        voice = "aevalsrc=0.5*sin(2*PI*180*t)*(lt(t\\,2)+gt(t\\,2.5)*lt(t\\,4)):s=22050:d=5"
        path = make(self.dir / 'mix.wav', bed, voice, af='[0:a][1:a]amix=inputs=2:normalize=0[o]')
        transcript = {'segments': [
            {'start': 0.0, 'end': 2.0, 'text': 'one two three four five.', 'words': [
                {'start': .0, 'end': .4, 'word': ' one'}, {'start': .4, 'end': .8, 'word': ' two'},
                {'start': .8, 'end': 1.2, 'word': ' three'}, {'start': 1.2, 'end': 1.6, 'word': ' four'},
                {'start': 1.6, 'end': 2.0, 'word': ' five.'}]},
            {'start': 2.5, 'end': 4.0, 'text': 'six seven eight.', 'words': [
                {'start': 2.5, 'end': 3.0, 'word': ' six'}, {'start': 3.0, 'end': 3.5, 'word': ' seven'},
                {'start': 3.5, 'end': 4.0, 'word': ' eight.'}]}]}
        report = self.analyze(path, 5, transcript=transcript)
        sm = report['speech_music']
        self.assertTrue(sm['music_present'])
        # bed: two sines of amp .05 -> rms = .05 -> -26 dBFS
        self.assertAlmostEqual(sm['bed_dbfs'], -26, delta=2.0)
        self.assertGreater(sm['speech_minus_bed_db'], 10)
        self.assertEqual(sm['entry']['time'], 0.0)
        self.assertIsNotNone(sm['fade_out'])
        self.assertAlmostEqual(sm['fade_out']['start'], 4.6, delta=.25)
        metrics = report['speech_metrics']
        self.assertEqual(metrics['word_count'], 8)
        self.assertAlmostEqual(metrics['words_per_minute_total'], 8 * 60 / 5, delta=.1)
        self.assertEqual(len(metrics['pauses']), 1)
        self.assertAlmostEqual(metrics['pauses'][0]['duration'], .5, delta=.01)
        self.assertEqual(len(metrics['sentences']), 2)
        self.assertAlmostEqual(metrics['sentences'][1]['duration'], 1.5, delta=.01)

    def test_alignment_accepts_scenes_transitions_and_text(self):
        beats = [i * .5 for i in range(20)]
        scenes = [{'start': 0}, {'start': 1.02}, {'start': 2.26}]
        transitions = {'transitions': [{'start': 3.0, 'type': 'whip'}, {'start': 4.24}]}
        text = {'records': [{'start': 0.5, 'text': 'a'}, {'start': 5.2, 'text': 'b'}]}
        result = aa.cut_beat_alignment(beats, [1.0, 2.0], scenes, transitions, text, tolerance_ms=80)
        self.assertEqual([round(r['nearest_beat_ms']) for r in result['cuts']], [20, 240])
        self.assertEqual(result['aligned_ratio'], .5)
        self.assertEqual(len(result['transitions']), 2)
        self.assertEqual(result['transitions_summary']['aligned_ratio'], .5)
        self.assertEqual(result['text_changes_summary']['aligned_ratio'], .5)
        self.assertAlmostEqual(result['chance_aligned_ratio'], .32, places=2)
        self.assertIsNone(aa.cut_beat_alignment(beats, [], scenes)['transitions'])
        # old helper unchanged
        self.assertEqual(aa.cut_alignment([{'start': 0}, {'start': 1.02}], [1])['aligned_ratio'], 1)

    def test_librosa_missing_falls_back(self):
        from unittest.mock import patch
        with patch.dict('sys.modules', {'librosa': None}):
            report = self.analyze(self.clicks, 10)
        self.assertIn('skipped', report['rhythm'])
        self.assertIsNotNone(report['integrated_lufs'])      # loudness does not need librosa
        self.assertIn('cut_beat_alignment', report)


if __name__ == '__main__':
    unittest.main()
