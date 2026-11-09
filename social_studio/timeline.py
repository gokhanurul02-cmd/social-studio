"""Join every measurement file into one time-ordered event list and a fixed time grid.

Only measured values are written; cells without a measurement contain an em dash.
No interpretation is added here: the agent reads TIMELINE.md and does that part.
Usage: python -m social_studio.timeline <analysis_dir> [out_dir]
"""
import json
import sys
from fractions import Fraction
from pathlib import Path

DASH = '—'
FINE_END = 3.0      # first seconds use the fine grid
FINE_STEP = 0.1
COARSE_STEP = 0.5
INPUTS = ['scenes.json', 'transitions.json', 'visual_analysis.json', 'onscreen_text.json',
          'audio_analysis.json', 'transcript.json']
TRACKS = ['cut', 'transition', 'camera', 'text', 'speech', 'music', 'sfx', 'energy']


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _fps(job):
    try:
        value = _read(job / 'analysis.json')['video']['fps']
        return float(Fraction(str(value)))
    except Exception:
        return 30.0


def _duration(job, loaded):
    try:
        return float(_read(job / 'analysis.json')['video']['duration'])
    except Exception:
        pass
    ends = [e for data in loaded.values() for e in _ends(data)]
    return max(ends) if ends else 0.0


def _ends(data):
    out = []
    if isinstance(data, list):
        for row in data:
            if isinstance(row, dict) and _num(row.get('end')):
                out.append(row['end'])
    elif isinstance(data, dict):
        for key in ('records', 'segments', 'transitions', 'camera_segments', 'rms_curve'):
            out += _ends(data.get(key))
    return out


def _label(*parts):
    out = []
    for p in parts:
        if p in (None, '', 'none'):
            continue
        s = str(p)
        if any(s == prev or s in prev.split('_') for prev in out):
            continue  # e.g. type "zoom_out" already carries direction "out"
        out.append(s)
    return ' '.join(out)


def _event(track, t0, t1, fps, value, source, confidence=None, **extra):
    t0 = float(t0)
    t1 = float(t1 if _num(t1) else t0)
    row = {'t_start': round(t0, 3), 't_end': round(t1, 3),
           'frame_start': extra.pop('frame_start', None), 'frame_end': extra.pop('frame_end', None),
           'track': track, 'value': value, 'source': source, 'confidence': confidence}
    if row['frame_start'] is None:
        row['frame_start'] = round(t0 * fps)
    if row['frame_end'] is None:
        row['frame_end'] = round(t1 * fps)
    row.update(extra)
    return row


def _get(row, *names, default=None):
    for name in names:
        if isinstance(row, dict) and row.get(name) is not None:
            return row[name]
    return default


def build_events(job):
    """Return (events, missing, meta). Missing inputs are skipped and listed, never fatal."""
    job = Path(job)
    fps = _fps(job)
    loaded, missing = {}, []
    for name in INPUTS:
        path = job / name
        if not path.is_file():
            missing.append({'file': name, 'reason': 'file not found'})
            continue
        try:
            data = _read(path)
        except (OSError, ValueError) as exc:
            missing.append({'file': name, 'reason': f'unreadable: {exc}'})
            continue
        if isinstance(data, dict) and data.get('skipped'):
            missing.append({'file': name, 'reason': f'skipped: {data["skipped"]}'})
        loaded[name] = data
    events = []

    scenes = loaded.get('scenes.json')
    if isinstance(scenes, dict):
        scenes = scenes.get('scenes')
    for scene in scenes if isinstance(scenes, list) else []:
        start = _get(scene, 'start')
        if _num(start) and start > 0:
            events.append(_event('cut', start, start, fps, 'cut', 'scenes.json', 'scene detector',
                                 frame_start=_get(scene, 'start_frame'), frame_end=_get(scene, 'start_frame')))

    trans = loaded.get('transitions.json')
    rows = trans.get('transitions') if isinstance(trans, dict) else trans
    for row in rows if isinstance(rows, list) else []:
        if _num(_get(row, 'start')):
            events.append(_event('transition', row['start'], _get(row, 'end', default=row['start']), fps,
                                 _label(_get(row, 'type', 'kind'), _get(row, 'direction')) or 'transition',
                                 'transitions.json', _get(row, 'confidence'),
                                 frame_start=_get(row, 'start_frame'), frame_end=_get(row, 'end_frame')))

    visual = loaded.get('visual_analysis.json') or {}
    camera = visual.get('camera_segments') if isinstance(visual, dict) else None
    if isinstance(camera, list) and camera:
        for row in camera:
            if _num(_get(row, 'start')):
                events.append(_event('camera', row['start'], _get(row, 'end', default=row['start']), fps,
                                     _label(_get(row, 'type'), _get(row, 'direction'), _get(row, 'easing')) or 'camera',
                                     'visual_analysis.json:camera_segments', _get(row, 'confidence'),
                                     frame_start=_get(row, 'start_frame'), frame_end=_get(row, 'end_frame')))
    elif isinstance(visual, dict):
        for row in visual.get('motion_per_second') or []:
            if _num(_get(row, 'start')) and _num(_get(row, 'end')):
                mag = _get(row, 'magnitude_px_per_s')
                events.append(_event('camera', row['start'], row['end'], fps,
                                     _label(_get(row, 'camera_estimate'), f'{mag:.1f}px/s' if _num(mag) else None) or DASH,
                                     'visual_analysis.json:motion_per_second', _get(row, 'confidence'),
                                     fallback=True))

    ocr = loaded.get('onscreen_text.json')
    for row in (ocr.get('records') if isinstance(ocr, dict) else None) or []:
        if _num(_get(row, 'start')) and _get(row, 'text'):
            extra = {k: row[k] for k in ('bbox', 'kind', 'style') if row.get(k) is not None}
            events.append(_event('text', row['start'], _get(row, 'end', default=row['start']), fps, row['text'],
                                 'onscreen_text.json', _get(row, 'confidence'),
                                 frame_start=_get(row, 'start_frame'), frame_end=_get(row, 'end_frame'), **extra))

    transcript = loaded.get('transcript.json')
    for seg in (transcript.get('segments') if isinstance(transcript, dict) else None) or []:
        if not _num(_get(seg, 'start')):
            continue
        events.append(_event('speech', seg['start'], _get(seg, 'end', default=seg['start']), fps,
                             str(_get(seg, 'text', default='')).strip(), 'transcript.json', _get(seg, 'avg_logprob'),
                             unit='segment'))
        for w in seg.get('words') or []:
            if _num(_get(w, 'start')):
                events.append(_event('speech', w['start'], _get(w, 'end', default=w['start']), fps,
                                     str(_get(w, 'word', 'text', default='')).strip(), 'transcript.json',
                                     _get(w, 'probability'), unit='word'))

    audio = loaded.get('audio_analysis.json') or {}
    if isinstance(audio, dict):
        tempo = audio.get('tempo_bpm')
        for b in audio.get('beats') or []:
            t = _get(b, 'time', 't') if isinstance(b, dict) else b
            if _num(t):
                events.append(_event('music', t, t, fps, f'beat{" " + format(tempo, ".0f") + " bpm" if _num(tempo) else ""}',
                                     'audio_analysis.json:beats', 'beat detector'))
        for o in audio.get('onsets') or []:
            t = _get(o, 'time', 't') if isinstance(o, dict) else o
            if _num(t):
                kind = _get(o, 'type', 'kind', 'class') if isinstance(o, dict) else None
                events.append(_event('sfx', t, t, fps, _label('onset', kind), 'audio_analysis.json:onsets',
                                     _get(o, 'confidence') if isinstance(o, dict) else 'onset detector'))
        # energy: mean dBFS per 0.5 s window from the rms curve
        curve = [r for r in audio.get('rms_curve') or [] if _num(_get(r, 'time')) and _num(_get(r, 'dbfs'))]
        windows = {}
        for r in curve:
            windows.setdefault(int(r['time'] // COARSE_STEP), []).append(r['dbfs'])
        for k, vals in sorted(windows.items()):
            events.append(_event('energy', k * COARSE_STEP, (k + 1) * COARSE_STEP, fps,
                                 f'{sum(vals) / len(vals):.1f} dBFS', 'audio_analysis.json:rms_curve', 'rms mean'))
    events.sort(key=lambda e: (e['t_start'], TRACKS.index(e['track']) if e['track'] in TRACKS else 99))
    meta = {'fps': fps, 'duration': _duration(job, loaded), 'loudness': {
        'integrated_lufs': audio.get('integrated_lufs') if isinstance(audio, dict) else None,
        'true_peak_dbtp': audio.get('true_peak_dbtp') if isinstance(audio, dict) else None,
        'tempo_bpm': audio.get('tempo_bpm') if isinstance(audio, dict) else None}}
    return events, missing, meta


def _overlap(e, a, b):
    """Event is active in [a, b): ranges overlap, point events must fall inside."""
    if e['t_end'] <= e['t_start']:
        return a <= e['t_start'] < b
    return e['t_start'] < b and e['t_end'] > a


def _join(items):
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return ' / '.join(out) if out else DASH


def build_grid(events, duration, fps):
    edges = []
    fine_n = int(round(min(FINE_END, duration) / FINE_STEP))
    for i in range(fine_n):
        edges.append((round(i * FINE_STEP, 6), round(min((i + 1) * FINE_STEP, duration), 6)))
    i = 0
    while FINE_END + i * COARSE_STEP < duration - 1e-9:
        a = FINE_END + i * COARSE_STEP
        edges.append((a, min(a + COARSE_STEP, duration)))
        i += 1
    by = {name: [e for e in events if e['track'] == name] for name in TRACKS}
    has_words = any(e.get('unit') == 'word' for e in by['speech'])
    rows = []
    for a, b in edges:
        words = [e['value'] for e in by['speech'] if e.get('unit') == 'word' and a <= e['t_start'] < b]
        if not has_words:  # no word timings: fall back to segment onsets
            words = [e['value'] for e in by['speech'] if e.get('unit') == 'segment' and a <= e['t_start'] < b]
        energy = [e['value'] for e in by['energy'] if _overlap(e, a, b)]
        rows.append({
            't_start': round(a, 3), 't_end': round(b, 3),
            'frame_start': round(a * fps), 'frame_end': max(round(a * fps), round(b * fps) - 1),
            'speech': _join(words),
            'text': _join(e['value'] for e in by['text'] if _overlap(e, a, b)),
            'camera': _join(e['value'] for e in by['camera'] if _overlap(e, a, b)),
            'transition': _join([e['value'] if e['track'] == 'transition' else 'cut'
                                 for e in by['transition'] + by['cut'] if _overlap(e, a, b)]),
            'audio': _join(e['value'] for e in by['sfx'] + by['music'] if _overlap(e, a, b)),
            'energy': energy[0] if energy else DASH})
    return rows


def _md(timeline):
    meta = timeline['meta']
    lines = ['# Zaman çizelgesi (ölçüm birleşimi)', '',
             f'Süre {meta["duration"]:.3f} s, {meta["fps"]:.3f} fps. Yalnızca ölçülen değerler; "{DASH}" = o aralıkta ölçüm yok. '
             'Yorum yok, yorumu ajan yapar.', '']
    if timeline['missing']:
        lines.append('Eksik / atlanan girdiler: ' + '; '.join(f'{m["file"]} ({m["reason"]})' for m in timeline['missing']))
        lines.append('')
    lines += ['Izgara: ilk 3 s için 0.1 s, sonrası için 0.5 s. Konuşma = o aralıkta başlayan kelimeler; diğer sütunlar o aralıkta etkin olanlar.', '',
              '| t (s) | kare | konuşma | ekran metni | kamera | geçiş/kesme | ses olayı | enerji |',
              '|---|---|---|---|---|---|---|---|']
    esc = lambda s: str(s).replace('|', '\\|')
    for r in timeline['grid']:
        lines.append(f'| {r["t_start"]:.1f}–{r["t_end"]:.1f} | {r["frame_start"]}–{r["frame_end"]} | ' + ' | '.join(
            esc(r[k]) for k in ('speech', 'text', 'camera', 'transition', 'audio', 'energy')) + ' |')
    lines += ['', '## Olaylar (iz bazında)']
    for track in TRACKS:
        rows = [e for e in timeline['events'] if e['track'] == track and e.get('unit') != 'word' and track != 'energy']
        if not rows:
            continue
        lines += ['', f'### {track}', '', '| t_start–t_end | kare | değer | kaynak | güven |', '|---|---|---|---|---|']
        for e in rows:
            conf = e['confidence']
            conf = f'{conf:.2f}' if _num(conf) else (conf or DASH)
            lines.append(f'| {e["t_start"]:.3f}–{e["t_end"]:.3f} | {e["frame_start"]}–{e["frame_end"]} | '
                         f'{esc(e["value"])} | {e["source"]} | {conf} |')
    return '\n'.join(lines) + '\n'


def build_timeline(job, out=None):
    job = Path(job)
    out = Path(out) if out else job
    out.mkdir(parents=True, exist_ok=True)
    events, missing, meta = build_events(job)
    timeline = {'method': 'join of local measurement files; no interpretation',
                'fps': meta['fps'], 'duration': meta['duration'], 'tracks': TRACKS,
                'missing': missing, 'meta': meta, 'events': events,
                'grid': build_grid(events, meta['duration'], meta['fps'])}
    (out / 'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'TIMELINE.md').write_text(_md(timeline), encoding='utf-8')
    return timeline


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('usage: python -m social_studio.timeline <analysis_dir> [out_dir]')
    result = build_timeline(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f'timeline: {len(result["events"])} events, {len(result["grid"])} grid rows, missing={[m["file"] for m in result["missing"]]}')
