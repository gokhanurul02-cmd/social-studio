"""Timeline and waveform diagnostics used by the visual comparison report."""
from pathlib import Path

from .media import load
from .perceptual import audio_delay, match_times


def analysis_bundle(source, folder, supplied=None):
    from .analyze import analyze
    if supplied:
        folder = Path(supplied)
        manifest = load(folder / 'analysis.json')
        from .media import video_info
        actual = video_info(source)
        if any(manifest['video'][key] != actual[key] for key in ['width', 'height', 'fps', 'frames']):
            raise ValueError('Analysis metadata does not match supplied video')
    else:
        analyze(str(source), folder, speech=False, max_frames=24)
    return {name: load(folder / filename) for name, filename in [
        ('scenes', 'scenes.json'), ('text', 'onscreen_text.json'), ('audio', 'audio_analysis.json')]}


def timeline_comparison(a, b, fps):
    cuts = match_times([r['start'] for r in a['scenes'][1:]], [r['start'] for r in b['scenes'][1:]], fps)
    text = {'method': 'same recognized text and temporal order', 'confidence': 'OCR and 4fps sampling dependent'}
    if 'skipped' in a['text'] or 'skipped' in b['text']:
        text['skipped'] = 'Both OCR timelines are required'
    else:
        used = set()
        matches = []
        for left in a['text']['records']:
            candidates = [(i, right) for i, right in enumerate(b['text']['records'])
                          if i not in used and left['text'].casefold() == right['text'].casefold()]
            if candidates:
                i, right = min(candidates, key=lambda item: abs(item[1]['start'] - left['start']))
                used.add(i)
                matches.append({'text': left['text'], 'start_delta_frames': (right['start'] - left['start']) * fps,
                                 'end_delta_frames': (right['end'] - left['end']) * fps})
        text['matches'] = matches
        text['mean_absolute_delta_frames'] = sum(abs(r['start_delta_frames']) + abs(r['end_delta_frames']) for r in matches) / (2 * len(matches)) if matches else None
        text['unmatched_source'] = len(a['text']['records']) - len(matches)
        text['unmatched_render'] = len(b['text']['records']) - len(matches)
    return {'cuts': cuts, 'text': text}


def audio_comparison(source, rendered, a, b, fps):
    import numpy as np
    from .audio_analysis import pcm
    if 'skipped' in a['audio'] or 'skipped' in b['audio']:
        return {'skipped': 'Both videos need measurable audio streams'}
    try:
        report = audio_delay(pcm(source), pcm(rendered))
        delay = report.get('delay_ms', 0) / 1000
        report['onset_alignment'] = match_times(a['audio']['onsets'], [t - delay for t in b['audio']['onsets']], fps, .08)
        report['onset_alignment']['note'] = 'Render onset times corrected by estimated waveform delay'
        curves = [bundle['audio'].get('loudness_curve', []) for bundle in [a, b]]
        count = min(map(len, curves))
        differences = [(curves[0][i]['momentary_lufs'] - curves[1][i]['momentary_lufs']) ** 2
                       for i in range(count)
                       if all(curve[i].get('momentary_lufs') is not None for curve in curves)]
        report['loudness_curve_rmse_lu'] = float(np.sqrt(np.mean(differences))) if differences else None
        report['loudness_compared_bins'] = len(differences)
        report['loudness_method'] = 'RMSE of overlapping 100ms ebur128 momentary LUFS reports at original timestamps'
        return report
    except Exception as exc:
        return {'skipped': f'Audio comparison failed: {exc}'}
