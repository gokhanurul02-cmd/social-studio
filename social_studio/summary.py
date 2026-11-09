"""Join measured outputs with per-metric provenance, without editorial judgments."""
from pathlib import Path

from .media import load, save


def metric(value, unit, source, method, confidence='derived from measurements'):
    return {'value': value, 'unit': unit, 'source': source, 'method': method, 'confidence': confidence}


def build_summary(job):
    job = Path(job)
    analysis = load(job / 'analysis.json')
    duration = analysis['video']['duration']
    hook_end = min(3, duration)
    missing_files = [n for n in ('scenes.json', 'onscreen_text.json', 'audio_analysis.json', 'visual_analysis.json')
                     if not (job / n).exists()]
    scenes = load(job / 'scenes.json') if (job / 'scenes.json').exists() else []
    ocr = load(job / 'onscreen_text.json') if (job / 'onscreen_text.json').exists() else {'skipped': 'file not found'}
    audio = load(job / 'audio_analysis.json') if (job / 'audio_analysis.json').exists() else {'skipped': 'file not found'}
    visual = load(job / 'visual_analysis.json') if (job / 'visual_analysis.json').exists() else {'skipped': 'file not found'}
    transcript = load(job / 'transcript.json') if (job / 'transcript.json').exists() else None
    speech = transcript.get('segments', []) if transcript else []
    words = [w for segment in speech for w in segment.get('words', [])]
    word_count = len(words) if words else sum(len(segment['text'].split()) for segment in speech)
    texts = ocr.get('records', [])
    hook_cuts = sum(0 < scene['start'] < hook_end for scene in scenes)
    hook_texts = [row for row in texts if row['start'] < hook_end]
    hook_speech = [row for row in speech if row['start'] < hook_end]
    onset_times = [(o.get('time', o.get('t')) if isinstance(o, dict) else o) for o in audio.get('onsets', [])]
    hook_onsets = [t for t in onset_times if isinstance(t, (int, float)) and t < hook_end]
    hook_events = hook_cuts + len(hook_texts) + len(hook_speech) + len(hook_onsets)
    metrics = {
        'hook_cuts': metric(hook_cuts, 'cuts', 'scenes.json', f'0 < cut time < {hook_end}s'),
        'hook_text_events': metric(len(hook_texts) if 'skipped' not in ocr else None, 'events',
                                   'onscreen_text.json', f'text onset before {hook_end}s', 'OCR estimates'),
        'hook_speech_segments': metric(len(hook_speech) if transcript else None, 'segments',
                                       'transcript.json', f'segment onset before {hook_end}s', 'Whisper estimates'),
        'hook_audio_onsets': metric(len(hook_onsets) if 'skipped' not in audio else None, 'onsets',
                                    'audio_analysis.json', f'onset before {hook_end}s', 'onset detector dependent'),
        'hook_event_density': metric(hook_events / hook_end if transcript and 'skipped' not in ocr and 'skipped' not in audio else None,
                                     'events/s', ['scenes.json', 'onscreen_text.json', 'transcript.json', 'audio_analysis.json'],
                                     'sum of cut, text, speech-segment and audio-onset events / hook duration',
                                     'descriptive event count, not an engagement or quality score'),
        'words_per_minute': metric(word_count * 60 / duration if transcript else None, 'words/min',
                                   'transcript.json', 'transcript word count / full video minutes', 'ASR estimates'),
        'text_density': metric(sum(len(row['text']) for row in texts) / duration if 'skipped' not in ocr else None,
                               'recognized characters/s', 'onscreen_text.json', 'characters over merged text events / duration', 'OCR estimates'),
        'text_area_time_ratio': metric(sum((r['bbox'][2]-r['bbox'][0])*(r['bbox'][3]-r['bbox'][1])*(r['end']-r['start']) for r in texts) / duration if 'skipped' not in ocr else None,
                                       'box-area seconds/video seconds', 'onscreen_text.json', 'sum of OCR box area * visible duration / duration; overlapping boxes count separately', 'OCR estimates'),
        'cuts_per_second': metric(visual.get('cuts', {}).get('per_second'), 'cuts/s', 'visual_analysis.json', 'detected cuts / duration'),
        'cut_beat_alignment': metric(audio.get('cut_beat_alignment', {}).get('aligned_ratio'), 'ratio',
                                     'audio_analysis.json', 'cuts within 80ms of nearest estimated beat / all cuts', 'beat detector dependent'),
    }
    from .timeline import build_events, INPUTS as INPUTS_N
    events, tl_missing, tl_meta = build_events(job)
    hook_window = [e for e in events if e['t_start'] < hook_end and e.get('unit') != 'word' and not e.get('fallback')]
    hook_by = {t: sum(e['track'] == t for e in hook_window) for t in ('transition', 'camera', 'text', 'speech')}
    transitions = [e for e in events if e['track'] == 'transition']
    have_transitions = not any(m['file'] == 'transitions.json' for m in tl_missing)
    texts_ok = 'skipped' not in ocr and bool(texts)
    loud = tl_meta['loudness']
    metrics.update({
        'hook_timeline_events': metric(sum(hook_by.values()) if len(tl_missing) < len(INPUTS_N) else None, 'events', 'timeline.json',
                                       f'transition + camera segment + text + speech segment onsets before {hook_end}s',
                                       'descriptive event count; ' + ', '.join(f'{k}={v}' for k, v in hook_by.items())),
        'transitions_per_second': metric(len(transitions) / duration if have_transitions else None, 'transitions/s',
                                         'transitions.json', 'transition events / duration', 'transition detector dependent'),
        'mean_caption_group_seconds': metric(sum(r['end'] - r['start'] for r in texts) / len(texts) if texts_ok else None,
                                             's', 'onscreen_text.json', 'mean (end - start) of merged text records', 'OCR estimates'),
        'integrated_lufs': metric(loud['integrated_lufs'], 'LUFS', 'audio_analysis.json', 'ITU-R BS.1770 integrated loudness', 'ffmpeg ebur128'),
        'true_peak_dbtp': metric(loud['true_peak_dbtp'], 'dBTP', 'audio_analysis.json', 'true peak', 'ffmpeg ebur128'),
    })
    result = {'method': 'join of local measurement files', 'confidence': 'see individual metric provenance',
              'duration': duration, 'hook_window': [0, hook_end], 'metrics': metrics,
              'hook_text': hook_texts, 'hook_speech': hook_speech, 'hook_onsets': hook_onsets,
              'palettes': {'source': 'visual_analysis.json', 'values': visual.get('palettes', [])},
              'energy_curve': {'source': 'audio_analysis.json', 'values': audio.get('rms_curve', [])},
              'motion_curve': {'source': 'visual_analysis.json', 'values': visual.get('motion_per_second', [])},
              'hook_breakdown': hook_by, 'missing_files': missing_files,
              'timeline_missing': tl_missing,
              'skipped': {name: data['skipped'] for name, data in [('ocr', ocr), ('audio', audio), ('visual', visual)] if 'skipped' in data}}
    save(job / 'summary.json', result)
    fmt = lambda v: 'ölçülmedi' if v is None else (f'{v:.3f}' if isinstance(v, float) else str(v))
    lines = ['# Video ölçümleri', '', f'Süre {duration:.3f} s. Saniye saniye ayrıntı: TIMELINE.md ve timeline.json.', '',
             '| Ölçüm | Değer | Birim | Kaynak |', '|---|---|---|---|']
    for name, row in metrics.items():
        src = ', '.join(row['source']) if isinstance(row['source'], list) else row['source']
        lines.append(f'| {name} | {fmt(row["value"])} | {row["unit"]} | {src} |')
    lines += ['', 'Yöntem ve güven bilgisi summary.json içinde her ölçümün yanında kayıtlıdır.',
              'Enerji ve hareket eğrileri ile sahne paletleri aynı JSON içinde kaynaklarıyla birlikte bulunur.', '']
    skipped = dict(result['skipped'])
    for n in missing_files:
        skipped.setdefault(n, 'dosya yok')
    if skipped:
        lines += ['## Atlanan / eksik ölçümler', ''] + [f'- {name}: {reason}' for name, reason in skipped.items()]
    else:
        lines.append('Atlanan ölçüm yok.')
    if tl_missing:
        lines += ['', '## Zaman çizelgesinde eksik girdiler', ''] + [f'- {m["file"]}: {m["reason"]}' for m in tl_missing]
    (job / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result
