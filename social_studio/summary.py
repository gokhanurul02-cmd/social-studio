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
    scenes = load(job / 'scenes.json')
    ocr = load(job / 'onscreen_text.json')
    audio = load(job / 'audio_analysis.json')
    visual = load(job / 'visual_analysis.json')
    transcript = load(job / 'transcript.json') if (job / 'transcript.json').exists() else None
    speech = transcript.get('segments', []) if transcript else []
    words = [w for segment in speech for w in segment.get('words', [])]
    word_count = len(words) if words else sum(len(segment['text'].split()) for segment in speech)
    texts = ocr.get('records', [])
    hook_cuts = sum(0 < scene['start'] < hook_end for scene in scenes)
    hook_texts = [row for row in texts if row['start'] < hook_end]
    hook_speech = [row for row in speech if row['start'] < hook_end]
    hook_onsets = [t for t in audio.get('onsets', []) if t < hook_end]
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
        'cuts_per_second': metric(visual['cuts']['per_second'], 'cuts/s', 'visual_analysis.json', 'detected cuts / duration'),
        'cut_beat_alignment': metric(audio.get('cut_beat_alignment', {}).get('aligned_ratio'), 'ratio',
                                     'audio_analysis.json', 'cuts within 80ms of nearest estimated beat / all cuts', 'beat detector dependent'),
    }
    result = {'method': 'join of local measurement files', 'confidence': 'see individual metric provenance',
              'duration': duration, 'hook_window': [0, hook_end], 'metrics': metrics,
              'hook_text': hook_texts, 'hook_speech': hook_speech, 'hook_onsets': hook_onsets,
              'palettes': {'source': 'visual_analysis.json', 'values': visual.get('palettes', [])},
              'energy_curve': {'source': 'audio_analysis.json', 'values': audio.get('rms_curve', [])},
              'motion_curve': {'source': 'visual_analysis.json', 'values': visual.get('motion_per_second', [])},
              'skipped': {name: data['skipped'] for name, data in [('ocr', ocr), ('audio', audio), ('visual', visual)] if 'skipped' in data}}
    save(job / 'summary.json', result)
    lines = ['# Video ölçümleri', '', '| Ölçüm | Değer | Birim | Kaynak |', '|---|---|---|---|']
    for name, row in metrics.items():
        lines.append(f'| {name} | {row["value"]} | {row["unit"]} | {row["source"]} |')
    lines += ['', 'Yöntem ve güven bilgisi summary.json içinde her ölçümün yanında kayıtlıdır.',
              'Enerji ve hareket eğrileri ile sahne paletleri aynı JSON içinde kaynaklarıyla birlikte bulunur.',
              '', 'Atlanan ölçümler', str(result['skipped'])]
    (job / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result
