"""Synthetic lavfi clips for the multi-source transition and camera-motion detectors.

Run: .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from social_studio.media import FFMPEG, run  # noqa: E402
from social_studio.transitions import analyze_transitions, scenes_from_transitions  # noqa: E402
from social_studio.visual import camera_analysis  # noqa: E402

FPS = 30
W, H = 320, 180


def ffmpeg(*args):
    run([FFMPEG, '-v', 'error', '-y', *args], capture=True)


def encode(*args):
    return ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '12', '-pix_fmt', 'yuv420p', '-g', '15', *args]


@unittest.skipUnless(Path(str(FFMPEG)).exists() or shutil.which('ffmpeg'), 'ffmpeg not available')
class VisualCutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='visual-cuts-'))
        cls.tex_a = cls.tmp / 'tex_a.png'
        cls.tex_b = cls.tmp / 'tex_b.png'
        # static blurred-noise textures with clearly different colours (flow needs texture)
        for out, colour, seed in ((cls.tex_a, '0x3366aa', 1), (cls.tex_b, '0xcc8844', 7)):
            ffmpeg('-f', 'lavfi', '-i', f'color=c={colour}:s=1600x900:d=1',
                   '-vf', f'noise=alls=90:allf=u:all_seed={seed},boxblur=2:1,eq=contrast=1.4',
                   '-frames:v', '1', out)
        cls.cache = {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def still(self, tex, seconds, x=200, y=200):
        return ['-loop', '1', '-framerate', str(FPS), '-t', str(seconds), '-i', str(tex)], \
            f'crop={W}:{H}:{x}:{y},setsar=1'

    def analyse(self, name):
        if name not in self.cache:
            sig, transitions, report = analyze_transitions(self.tmp / f'{name}.mp4', FPS)
            scenes = scenes_from_transitions(transitions, sig['n'], FPS)
            samples, segments = camera_analysis(sig, scenes, transitions)
            self.cache[name] = (sig, transitions, scenes, segments, report)
        return self.cache[name]

    def make_two_shots(self, name, middle_filter, extra=()):
        a_in, a_f = self.still(self.tex_a, 3)
        b_in, b_f = self.still(self.tex_b, 3)
        ffmpeg(*a_in, *b_in, '-filter_complex',
               f'[0:v]{a_f}[a];[1:v]{b_f}[b];{middle_filter}', *extra, *encode(), self.tmp / f'{name}.mp4')

    # ------------------------------------------------------------ cuts ----
    def test_hard_cut(self):
        a_in, a_f = self.still(self.tex_a, 2)
        b_in, b_f = self.still(self.tex_b, 2)
        ffmpeg(*a_in, *b_in, '-filter_complex', f'[0:v]{a_f}[a];[1:v]{b_f}[b];[a][b]concat=n=2:v=1[v]',
               '-map', '[v]', *encode(), self.tmp / 'cut.mp4')
        sig, transitions, scenes, _, report = self.analyse('cut')
        cuts = [t for t in transitions if t['type'] == 'hard_cut']
        self.assertEqual(len(cuts), 1, transitions)
        self.assertLessEqual(abs(cuts[0]['start_frame'] - 60), 1)
        self.assertTrue(cuts[0]['edit_boundary'])
        self.assertGreaterEqual(cuts[0]['confidence'], 0.6)
        self.assertIn('histogram', cuts[0]['sources'])
        self.assertEqual(len(scenes), 2)
        for key in ('start', 'end', 'start_frame', 'end_frame'):
            self.assertIn(key, scenes[0])          # old scenes.json schema kept
        self.assertLessEqual(abs(scenes[1]['start_frame'] - 60), 1)
        self.assertEqual(scenes[1]['transition_in']['type'], 'hard_cut')

    def test_dissolve(self):
        self.make_two_shots('dissolve', '[a][b]xfade=transition=fade:duration=0.8:offset=1.5[v]', ('-map', '[v]'))
        _, transitions, scenes, _, _ = self.analyse('dissolve')
        dis = [t for t in transitions if t['type'] == 'dissolve']
        self.assertEqual(len(dis), 1, transitions)
        self.assertFalse([t for t in transitions if t['type'] == 'hard_cut'], transitions)
        # xfade runs from frame 45 to 69; the blend fit should cover most of it
        self.assertLessEqual(abs(dis[0]['start_frame'] - 46), 4)
        self.assertLessEqual(abs(dis[0]['end_frame'] - 68), 4)
        self.assertEqual(len(scenes), 2)

    def test_fade_through_black(self):
        a_in, a_f = self.still(self.tex_a, 2)
        b_in, b_f = self.still(self.tex_b, 2)
        ffmpeg(*a_in, *b_in, '-filter_complex',
               f'[0:v]{a_f},fade=t=out:st=1.4:d=0.5[a];[1:v]{b_f},fade=t=in:st=0.1:d=0.5[b];[a][b]concat=n=2:v=1[v]',
               '-map', '[v]', *encode(), self.tmp / 'fade.mp4')
        _, transitions, scenes, _, _ = self.analyse('fade')
        fades = [t for t in transitions if t['type'] == 'fade']
        self.assertEqual(len(fades), 1, transitions)
        self.assertEqual(fades[0]['subtype'], 'dip_to_black')
        self.assertLessEqual(abs(fades[0]['start_frame'] - 42), 3)
        self.assertEqual(len(scenes), 2)

    def test_card_flip_on_black(self):
        # vertical-axis card flip: width shrinks to an edge-on sliver, content switches, width grows back
        a_in, a_f = self.still(self.tex_a, 2)
        b_in, b_f = self.still(self.tex_b, 2)
        width = "if(between(t,1.7,2.3),max(4,trunc(320*abs(cos(PI*(t-1.7)/0.6))/2)*2),320)"
        ffmpeg(*a_in, *b_in, '-filter_complex',
               f"[0:v]{a_f}[a];[1:v]{b_f}[b];[a][b]concat=n=2:v=1,"
               f"scale=w='{width}':h={H}:eval=frame,pad={W}:{H}:(ow-iw)/2:0:black:eval=frame,setsar=1[v]",
               '-map', '[v]', *encode(), self.tmp / 'flip.mp4')
        _, transitions, scenes, _, _ = self.analyse('flip')
        flips = [t for t in transitions if t['type'] == 'flip']
        self.assertEqual(len(flips), 1, transitions)
        self.assertEqual(flips[0]['subtype'], 'vertical_axis')
        self.assertLessEqual(abs(flips[0]['peak_frame'] - 60), 2)
        self.assertLessEqual(abs(flips[0]['start_frame'] - 52), 2)
        self.assertLessEqual(abs(flips[0]['end_frame'] - 68), 2)
        self.assertEqual(len(scenes), 2)
        self.assertFalse([t for t in transitions if t['type'] == 'hard_cut'], transitions)

    # ---------------------------------------------------------- camera ----
    def test_whip_pan_on_fixed_background(self):
        # 0-1 s static, 1.0-1.3 s whip (24 px/frame), static, 2.3-4 s slow pan (3 px/frame)
        x = "if(lt(t,1),0,if(lt(t,1.3),(t-1)*720,if(lt(t,2.3),216,216+(t-2.3)*90)))"
        ffmpeg('-loop', '1', '-framerate', str(FPS), '-t', '4', '-i', self.tex_a,
               '-vf', f"crop={W}:{H}:x='{x}':y=300,setsar=1", *encode(), self.tmp / 'pan.mp4')
        _, transitions, scenes, segments, _ = self.analyse('pan')
        self.assertEqual(len(scenes), 1, transitions)              # in-shot camera move: no scene cut
        whips = [t for t in transitions if t['type'] == 'whip']
        self.assertEqual(len(whips), 1, transitions)
        self.assertEqual(whips[0]['direction'], 'right')
        self.assertFalse(whips[0]['edit_boundary'])
        self.assertLessEqual(abs(whips[0]['start'] - 1.0), 0.1)
        self.assertLessEqual(abs(whips[0]['end'] - 1.3), 0.1)
        pans = [s for s in segments if s['type'] == 'pan_right' and s['start'] >= 2.0]
        self.assertTrue(pans, segments)
        self.assertLessEqual(abs(pans[0]['start'] - 2.3), 0.2)
        self.assertGreaterEqual(pans[0]['end'], 3.8)
        self.assertGreaterEqual(pans[0]['confidence'], 0.5)
        self.assertEqual(pans[0]['easing'], 'linear')
        self.assertAlmostEqual(pans[0]['mean_rates']['pan_right'], 90 / H, delta=0.1)
        static = [s for s in segments if s['type'] == 'static' and s['end'] <= 1.05]
        self.assertTrue(static, segments)

    def test_zoom_in(self):
        ffmpeg('-loop', '1', '-framerate', str(FPS), '-t', '3', '-i', self.tex_b,
               '-vf', "zoompan=z='1+0.004*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:"
                      f"s={W}x{H}:fps={FPS},setsar=1", *encode(), self.tmp / 'zoom.mp4')
        _, transitions, scenes, segments, _ = self.analyse('zoom')
        self.assertEqual(len(scenes), 1, transitions)
        self.assertFalse([t for t in transitions if t['edit_boundary']], transitions)
        zooms = [s for s in segments if s['family'] in ('zoom', 'dolly')]
        self.assertTrue(zooms, segments)
        longest = max(zooms, key=lambda s: s['end'] - s['start'])
        self.assertEqual(longest['direction'], 'in')
        self.assertGreaterEqual(longest['end'] - longest['start'], 2.0)
        self.assertGreater(longest['mean_rates']['zoom_in'], 0.05)

    # ------------------------------------------------------- sampling -----
    def test_hook_sampling_is_even_and_bounded(self):
        from social_studio.analyze import sample_plan
        transitions = [{'type': 'flip', 'start_frame': 234, 'end_frame': 243, 'peak_frame': 237,
                        'edit_boundary': True, 'confidence': 0.8}]
        plan = sample_plan(22.155, 30000 / 1001, 664, transitions, 1.0, 120)
        frames = plan['frames']
        hook = [f for f in frames if f / (30000 / 1001) < 3]
        gaps = {b - a for a, b in zip(hook, hook[1:])}
        self.assertGreaterEqual(len(hook), 10)
        self.assertLessEqual(max(gaps) - min(gaps), 1)              # evenly spaced, not 0/1/2
        self.assertTrue({233, 237, 244} <= set(frames))
        self.assertLessEqual(len(sample_plan(22.155, 29.97, 664, transitions, 1.0, 9)['frames']), 9)
        self.assertEqual(len(set(frames)), len(frames))


if __name__ == '__main__':
    unittest.main()
