"""stylecheck with fake style.json / analysis folders (no video decoding: measure=False)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from social_studio import stylecheck as sc  # noqa: E402


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


STYLE = {
    'format': {'width': 2160, 'height': 3840, 'fps': '30000/1001', 'duration_s': 22.0},
    'hook': {'first_text_frame': 1},
    'rhythm': {'caption_groups': 26, 'mean_caption_group_s': 0.83,
               'transitions': [{'t': 1.4, 'type': 'kamera içi hızlı geri çekiliş'}, {'t': 2.4, 'type': 'whip'},
                               {'t': 4.1, 'type': 'zoom burst'}, {'t': 7.8, 'type': '3D kart çevirme'}]},
    'palette': [{'hex': '#24ACE9', 'share': 0.6}, {'hex': '#8DC4E9', 'share': 0.4}],
    'captions': {'size_ratio': 0.040, 'baseline_y_ratio': 0.795, 'fill': '#FFFFFF', 'stroke': '#000000',
                 'shadow': True, 'words_per_group': '1-4', 'animation': 'yok, kesme'},
    'camera': ['göz hizası tanıtım', 'hızlı geri+yukarı reveal ease-out', 'whip/zoom burst + motion blur'],
    'audio': {'voice': 'erkek, ~198 kelime/dk', 'lufs': -8.2, 'true_peak_dbtp': 1.5},
}


def words(text, start, step):
    out = []
    for i, w in enumerate(text.split()):
        out.append({'word': ' ' + w, 'start': start + i * step, 'end': start + i * step + step * 0.9})
    return out


def make_analysis(folder, *, duration=10.0, baseline=0.796, size=0.041, lufs=-15.0, tp=-1.5,
                  transitions=('zoom_burst', 'whip', 'flip'), pause=0.3, palette='#2fb0e8', caption_s=0.8):
    write(folder / 'analysis.json', {'source': str(folder / 'missing.mp4'),
                                     'video': {'width': 1080, 'height': 1920, 'fps': '30000/1001', 'duration': duration}})
    recs, t = [], 0.1
    for txt in ['Bir otobüsü', 'ipe bağlı', '2400', 'kediye ihtiyacın olurdu'] * 3:
        recs.append({'start': t, 'end': t + caption_s, 'text': txt, 'kind': 'caption',
                     'style': {'words': txt.split(), 'baseline_y_ratio': baseline, 'font_size_ratio': size}})
        t += caption_s
    write(folder / 'onscreen_text.json', {'records': recs, 'caption_style_summary': {
        'fill_hex': '#fffeff', 'stroke_hex': None, 'shadow': True, 'font_size_ratio': size,
        'baseline_y_ratio': baseline, 'dominant_animation': 'cut'}})
    write(folder / 'transitions.json', {'transitions': [{'type': k, 'start': 1.0 + i, 'end': 1.2 + i} for i, k in enumerate(transitions)]})
    write(folder / 'visual_analysis.json', {
        'camera_segments': [{'type': 'dolly_out', 'confidence': 0.6}, {'type': 'static', 'confidence': 0.8}],
        'palettes': [{'start': 0, 'end': duration, 'colors': [{'hex': palette, 'ratio': 0.7}, {'hex': '#b1d0dc', 'ratio': 0.3}]}]})
    write(folder / 'audio_analysis.json', {'integrated_lufs': lufs, 'true_peak_dbtp': tp})
    w1 = words('Bir otobüsü ipe bağlı kedilere çektirmek isteseydin', 0.0, 0.3)
    w2 = words('Peki aynı şeyi atlarla yapsaydın', w1[-1]['end'] + pause, 0.3)
    write(folder / 'transcript.json', {'language': 'tr', 'segments': [
        {'text': 'Bir otobüsü ipe bağlı kedilere çektirmek isteseydin', 'words': w1},
        {'text': 'Peki aynı şeyi atlarla yapsaydın', 'words': w2}]})
    return folder


def comp_samples(n=30, step=0.33, flat=(), edge=(), area=0.22, shot='medium', horizon=0.45):
    out = []
    for i in range(n):
        t = round(0.17 + i * step, 3)
        out.append({'t': t, 'subject_area': area, 'shot_type': shot, 'blob_count': 12, 'horizon_y': horizon,
                    'centroid': [0.5, 0.55], 'thirds_distance': 0.2, 'shot_confidence': 0.6,
                    'flat_fill_ratio': 0.45 if i in flat else 0.02, 'flat_fill_ratio_incl_sky': 0.3,
                    'edge_cut': i in edge, 'edge_worst': 'bottom', 'edge_contact': {'bottom': 0.6, 'left': 0, 'right': 0, 'top': 0}})
    return out


def add_composition(folder, **kw):
    samples = comp_samples(**kw)
    write(folder / 'composition.json', {'schema': 'social-studio.composition.v1', 'duration': 10.0, 'sample_fps': 3.0,
                                         'samples': samples})
    return folder


def row(report, key, cand=0):
    return next(r for r in report['candidates'][cand]['rows'] if r['metric'] == key)


class StylecheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / 'ref' / 'style.json', STYLE)
        # an English sibling transcript makes the reference language "en"
        first = words('If you strapped a baby to a pair of trucks', 0.0, 0.28)
        second = words('you would need 5000 of them', first[-1]['end'] + 0.35, 0.28)
        write(self.root / 'ref' / 'analysis' / 'transcript.json', {'language': 'tr', 'segments': [
            {'text': 'If you strapped a baby to a pair of trucks', 'words': first},
            {'text': 'you would need 5000 of them', 'words': second}]})

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, *cands):
        return sc.build_report(self.root / 'ref' / 'style.json', [str(c) for c in cands], out=None, measure=False)

    def test_matching_candidate_passes_and_has_no_percentage(self):
        rep = self.check(make_analysis(self.root / 'good'))
        c = rep['candidates'][0]
        self.assertEqual(c['verdict'], 'PASS', [r for r in c['rows'] if r['status'] == 'FAIL'])
        self.assertNotIn('similarity', json.dumps(rep).lower())
        self.assertEqual(row(rep, 'caption_baseline_y_ratio')['status'], 'PASS')
        self.assertEqual(row(rep, 'fps')['status'], 'PASS')

    def test_caption_position_and_size_fail_outside_thresholds(self):
        rep = self.check(make_analysis(self.root / 'bad', baseline=0.70, size=0.055))
        self.assertEqual(row(rep, 'caption_baseline_y_ratio')['status'], 'FAIL')
        self.assertEqual(row(rep, 'caption_size_ratio')['status'], 'FAIL')
        self.assertEqual(rep['candidates'][0]['verdict'], 'FAIL')

    def test_loudness_uses_delivery_target_not_clipped_reference(self):
        rep = self.check(make_analysis(self.root / 'loud', lufs=-8.2, tp=1.5))
        self.assertEqual(row(rep, 'integrated_lufs')['status'], 'FAIL')
        self.assertEqual(row(rep, 'true_peak_dbtp')['status'], 'FAIL')
        ok = self.check(make_analysis(self.root / 'ok'))
        self.assertEqual(row(ok, 'integrated_lufs')['status'], 'PASS')
        self.assertIn('referans miksi', row(ok, 'integrated_lufs')['note'])

    def test_missing_flip_fails_transition_types(self):
        rep = self.check(make_analysis(self.root / 'noflip', transitions=('whip',)))
        r = row(rep, 'transition_types')
        self.assertEqual(r['status'], 'FAIL')
        self.assertIn('flip', r['note'])

    def test_cross_language_pace_is_info_and_pause_is_gated(self):
        rep = self.check(make_analysis(self.root / 'pause', pause=1.2))
        self.assertEqual(row(rep, 'wpm_span')['status'], 'INFO')
        self.assertEqual(row(rep, 'syllables_per_s')['status'], 'INFO')
        self.assertEqual(row(rep, 'max_pause_s')['status'], 'FAIL')

    def test_two_candidates_and_markdown(self):
        rep = self.check(make_analysis(self.root / 'v1', baseline=0.70), make_analysis(self.root / 'v2'))
        self.assertEqual([c['verdict'] for c in rep['candidates']], ['FAIL', 'PASS'])
        md = sc.to_markdown(rep)
        self.assertIn('Aday 2', md)
        self.assertIn('| Altyazı taban çizgisi', md)

    def test_palette_distance_and_words_range(self):
        far = self.check(make_analysis(self.root / 'red', palette='#e02020'))
        self.assertEqual(row(far, 'palette')['status'], 'FAIL')
        self.assertEqual(row(far, 'caption_words_per_group')['status'], 'PASS')
        self.assertEqual(row(far, 'caption_words_per_group')['reference'], [1.0, 4.0])

    def test_analysis_folder_as_reference_and_stroke_same_method(self):
        ref = make_analysis(self.root / 'refdir')
        rep = sc.build_report(ref, [str(make_analysis(self.root / 'cand'))], measure=False)
        self.assertEqual(row(rep, 'caption_stroke')['status'], 'PASS')
        self.assertEqual(rep['candidates'][0]['verdict'], 'PASS')

    def test_excerpt_window_for_transition_density(self):
        ref = make_analysis(self.root / 'long', duration=30.0, transitions=('whip', 'zoom_burst', 'flip', 'whip', 'flip', 'whip'))
        # all reference transitions start in the first 7 s -> dense opening
        rep = sc.build_report(ref, [str(make_analysis(self.root / 'short', duration=10.0))], measure=False)
        r = row(rep, 'transitions_per_s')
        self.assertAlmostEqual(r['reference'], 0.6)
        self.assertIn('pencere', r['note'])

    def test_fragmented_fast_move_counts_once(self):
        frags = [{'type': 'zoom_burst', 'start': 0.90, 'end': 0.90}, {'type': 'zoom_burst', 'start': 0.93, 'end': 1.03},
                 {'type': 'whip', 'start': 1.07, 'end': 1.10}, {'type': 'flip', 'start': 1.15, 'end': 1.4},
                 {'type': 'whip', 'start': 3.0, 'end': 3.1}]
        merged = sc.merge_fast_moves(frags)
        self.assertEqual([m['type'] for m in merged], ['zoom_burst', 'flip', 'whip'])
        self.assertEqual(merged[0]['merged'], 3)

    def test_syllables_and_numbers(self):
        self.assertEqual(sc.count_syllables('otobüsü', 'tr'), 4)
        self.assertEqual(sc.count_syllables('2400', 'tr'), 5)   # iki bin dört yüz
        self.assertEqual(sc.count_syllables('5000', 'en'), 3)   # five thousand
        self.assertEqual(sc.guess_language('If you strapped a baby', 'tr'), 'en')
        self.assertLess(sc.delta_e('#ffffff', '#fffeff'), 1)

    def test_composition_flags_fail_with_timestamped_warnings(self):
        add_composition(self.root / 'ref' / 'analysis', area=0.24)  # reference analysis sits next to style.json
        write(self.root / 'ref' / 'analysis' / 'analysis.json', {'video': {'width': 1080, 'height': 1920, 'fps': '30000/1001', 'duration': 22.0}})
        bad = add_composition(make_analysis(self.root / 'bad'), flat=(0, 1, 2), edge=(20, 21, 22))
        good = add_composition(make_analysis(self.root / 'good'))
        rep = self.check(bad, good)
        self.assertEqual(row(rep, 'comp_flat_fill_events', 0)['status'], 'FAIL')
        self.assertEqual(row(rep, 'comp_edge_cut_events', 0)['status'], 'FAIL')
        self.assertEqual(row(rep, 'comp_flat_fill_events', 1)['status'], 'PASS')
        self.assertEqual(row(rep, 'comp_subject_area_median', 1)['status'], 'PASS')
        warns = rep['candidates'][0]['composition_warnings']
        self.assertEqual({w['kind'] for w in warns}, {'flat_fill', 'edge_cut'})
        self.assertRegex(warns[0]['text'], r'^bad 0\.0–1\.\d s flat_fill 0\.45$')
        self.assertEqual(rep['candidates'][1]['composition_warnings'], [])
        md = sc.to_markdown(rep)
        self.assertIn('Kompozisyon – Aday 1', md)
        self.assertNotIn('similarity', json.dumps(rep).lower())

    def test_composition_distribution_gates(self):
        add_composition(self.root / 'ref' / 'analysis', area=0.24, shot='medium')
        write(self.root / 'ref' / 'analysis' / 'analysis.json', {'video': {'width': 1080, 'height': 1920, 'fps': '30000/1001', 'duration': 22.0}})
        far = add_composition(make_analysis(self.root / 'far'), area=0.55, shot='close')
        rep = self.check(far)
        self.assertEqual(row(rep, 'comp_subject_area_median')['status'], 'FAIL')
        self.assertEqual(row(rep, 'comp_shot_type_share')['status'], 'FAIL')
        self.assertEqual(row(rep, 'comp_horizon_y')['status'], 'INFO')      # noisy estimate is shown, not gated

    def test_missing_composition_is_skipped_not_failed(self):
        rep = self.check(make_analysis(self.root / 'plain'))
        self.assertEqual(row(rep, 'comp_flat_fill_events')['status'], 'SKIP')
        self.assertEqual(row(rep, 'comp_shot_type_share')['status'], 'SKIP')
        self.assertEqual(rep['candidates'][0]['verdict'], 'PASS')

    def test_pair_moments_use_beats_and_excerpt_window(self):
        ref = {'duration_s': {'value': 22.0}, '_beats': [{'start_s': 0, 'end_s': 4, 'role': 'kur'},
                                                         {'start_s': 4, 'end_s': 8, 'role': 'ödül'},
                                                         {'start_s': 15, 'end_s': 19, 'role': 'son'}]}
        short = sc.pair_moments(ref, 10.0, 7)
        self.assertEqual([m[0] for m in short], ['hook', 'kur', 'ödül'])      # 'son' lies beyond the excerpt
        self.assertEqual(short[1][1], short[1][2])                           # excerpt: same absolute time
        full = sc.pair_moments(ref, 22.0, 7)
        self.assertEqual(len(full), 4)
        scaled = sc.pair_moments(ref, 11.0 * 2 * 0.9, 7)                      # 19.8 s >= 80 % of 22 -> relative time
        self.assertAlmostEqual(scaled[1][2], scaled[1][1] * 19.8 / 22.0, places=1)

    def test_cli_registration(self):
        import subprocess
        root = Path(__file__).resolve().parents[1]
        exe = root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        out = subprocess.run([str(exe if exe.exists() else sys.executable), '-c',
                              'import sys; sys.argv=["social","stylecheck","--help"]; from social_studio.cli import main; main()'],
                             cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('candidates', out.stdout)


if __name__ == '__main__':
    unittest.main()
