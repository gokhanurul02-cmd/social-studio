"""Measured audio envelopes and explicitly qualified rhythm estimates."""
import re
import subprocess

from .media import FFMPEG, load, save


def pcm(source, sample_rate=16000):
    import numpy as np
    result = subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(source), '-vn', '-ac', '1',
                             '-ar', str(sample_rate), '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype='<f4').copy()


def cut_alignment(scenes, beats, tolerance_ms=80):
    rows = []
    for scene in scenes[1:]:
        delta = min((abs(scene['start'] - beat) * 1000 for beat in beats), default=None)
        rows.append({'cut': scene['start'], 'nearest_beat_ms': delta,
                     'aligned': delta <= tolerance_ms if delta is not None else None})
    return {'method': 'nearest beat, absolute time distance', 'confidence': 'depends on estimated beat times',
            'tolerance_ms': tolerance_ms, 'cuts': rows,
            'aligned_ratio': sum(row['aligned'] for row in rows) / len(rows) if rows and beats else None}


def analyze_audio(source, info, output, scenes=(), transcript=None):
    import numpy as np
    report = {'method': 'mono 16kHz PCM, 100ms non-overlapping RMS', 'confidence': 'measured signal energy',
              'sample_rate': 16000, 'resolution_s': .1, 'rms_curve': [], 'loudness_curve': [],
              'silence_intervals': [], 'beats': [], 'onsets': [], 'tempo_bpm': None}
    if not info['has_audio']:
        report['skipped'] = 'No audio stream'
        save(output, report)
        return report
    try:
        samples = pcm(source)
        sr, hop = 16000, 1600
        speech = transcript.get('segments', []) if transcript else []
        silent_start = None
        for offset in range(0, len(samples), hop):
            block = samples[offset:offset + hop].astype(float)
            start, end = offset / sr, min((offset + len(block)) / sr, info['duration'])
            rms = float(np.sqrt(np.mean(block * block)))
            db = float(20 * np.log10(max(rms, 1e-6)))
            voice = any(seg['start'] < end and seg['end'] > start for seg in speech)
            label = 'silence' if db < -45 else 'speech_candidate' if voice else 'non_speech_audio'
            report['rms_curve'].append({'time': start, 'end': end, 'rms': rms, 'dbfs': db,
                                        'classification': label})
            if db < -45 and silent_start is None:
                silent_start = start
            if db >= -45 and silent_start is not None:
                report['silence_intervals'].append({'start': silent_start, 'end': start})
                silent_start = None
        if silent_start is not None:
            report['silence_intervals'].append({'start': silent_start, 'end': len(samples) / sr})
        report['classification'] = {
            'method': 'VAD-filtered Whisper transcript overlap and -45 dBFS energy threshold',
            'confidence': 'heuristic; non-speech audio may contain music, effects or noise',
            'transcript_available': bool(transcript),
            'music_separation': {'skipped': 'Energy and VAD do not isolate a music stem'}}
        meter = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(source), '-vn', '-af',
                                'ebur128', '-f', 'null', '-'], capture_output=True)
        for line in meter.stderr.decode(errors='replace').splitlines():
            match = re.search(r'\bt:\s*([\d.]+).*?\bM:\s*(-?[\d.]+)', line)
            if match:
                report['loudness_curve'].append({'time': float(match[1]), 'momentary_lufs': float(match[2])})
        report['loudness_method'] = {'method': 'FFmpeg ebur128 momentary, 400ms window / 100ms reporting',
                                     'confidence': 'measured', 'note': 'RMS dBFS and LUFS are different units'}
        try:
            import librosa
            onset_env = librosa.onset.onset_strength(y=samples, sr=sr)
            tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            report['tempo_bpm'] = float(np.asarray(tempo).reshape(-1)[0]) if len(beat_frames) else None
            report['beats'] = [float(x) for x in librosa.frames_to_time(beat_frames, sr=sr)]
            report['onsets'] = [float(x) for x in librosa.onset.onset_detect(y=samples, sr=sr, units='time')]
            report['rhythm'] = {'method': 'librosa onset strength and beat tracker',
                                 'confidence': 'estimate, especially uncertain for speech/effects'}
        except (ImportError, AttributeError, RuntimeError, ValueError) as exc:
            report['rhythm'] = {'skipped': f'librosa unavailable or failed: {exc}'}
            energy = [row['rms'] for row in report['rms_curve']]
            rises = np.diff(energy, prepend=0)
            threshold = max(.02, float(np.median(abs(rises))) * 4)
            report['onsets'] = [i * .1 for i, rise in enumerate(rises) if rise > threshold]
            report['onset_method'] = {'method': '100ms RMS positive rise threshold', 'confidence': 'low; coarse estimate'}
        report['cut_beat_alignment'] = cut_alignment(scenes, report['beats'])
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        report['skipped'] = f'Audio measurement failed: {exc}'
    save(output, report)
    return report
