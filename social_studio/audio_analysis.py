"""Measured audio envelopes, loudness, rhythm and speech/music structure.

Everything here is local (ffmpeg + numpy/scipy/librosa). Values are either
*measured* (loudness, levels, timings from signal) or *estimates* (tempo, beats,
downbeats, event classes, speech/music split); each estimate carries a confidence.
Existing keys of ``audio_analysis.json`` are kept; new keys are additive.
"""
import json
import math
import re
import subprocess
from pathlib import Path

from .media import FFMPEG, load, save

SR = 16000            # envelope / RMS analysis rate (unchanged from earlier versions)
MSR = 22050           # librosa analysis rate
LUFS_SR = 48000       # BS.1770 K-weighting rate
WARMUP_S = 0.4        # momentary window length; earlier values are not valid
SILENCE_DB = -45
EBUR_FLOOR = -120.0


def np_clip(x, lo, hi):
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------- decoding

def pcm(source, sample_rate=16000):
    import numpy as np
    result = subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(source), '-vn', '-ac', '1',
                             '-ar', str(sample_rate), '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype='<f4').copy()


def _pcm_stereo(source, sample_rate=LUFS_SR, channels=2):
    import numpy as np
    result = subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(source), '-vn', '-ac', str(channels),
                             '-ar', str(sample_rate), '-f', 'f32le', '-'], capture_output=True, check=True)
    data = np.frombuffer(result.stdout, dtype='<f4').copy()
    return data[:len(data) // channels * channels].reshape(-1, channels)


def _num(text):
    text = text.strip()
    if text in ('-inf', 'inf', 'nan'):
        return None
    return float(text)


def _db(x, floor=-120.0):
    import numpy as np
    return float(20 * np.log10(max(float(x), 1e-6))) if x > 0 else floor


# --------------------------------------------------------------------------- loudness (EBU R128)

def measure_ebur128(source):
    """One ffmpeg ebur128 pass -> integrated LUFS, LRA, true peak and momentary/short-term curves."""
    proc = subprocess.run([str(FFMPEG), '-hide_banner', '-nostats', '-i', str(source), '-vn', '-af',
                           'ebur128=peak=true:framelog=info', '-f', 'null', '-'], capture_output=True)
    text = proc.stderr.decode(errors='replace')
    curve = []
    for line in text.splitlines():
        match = re.search(r'\bt:\s*([\d.]+).*?\bM:\s*(-?[\d.]+|-?inf)\s+S:\s*(-?[\d.]+|-?inf)', line)
        if match:
            time_s, momentary, short = float(match[1]), _num(match[2]), _num(match[3])
            warm = time_s < WARMUP_S - 1e-9
            invalid = warm or momentary is None or momentary <= EBUR_FLOOR
            row = {'time': time_s, 'momentary_lufs': None if invalid else momentary,
                   'short_term_lufs': None if (time_s < 3 - 1e-9 or short is None or short <= EBUR_FLOOR) else short}
            if invalid:
                row['note'] = 'warm-up (<400 ms window not filled)' if warm else 'below measurement floor (digital silence)'
            curve.append(row)
    summary = text.split('Summary:')[-1] if 'Summary:' in text else ''

    def grab(label, block_start, unit):
        block = summary.split(block_start)[-1] if block_start in summary else ''
        found = re.search(label + r':\s*(-?[\d.]+|-?inf)\s*' + unit, block)
        return _num(found[1]) if found else None
    result = {
        'integrated_lufs': grab(r'\bI', 'Integrated loudness', 'LUFS'),
        'lra': grab(r'LRA', 'Loudness range', 'LU'),
        'lra_low_lufs': grab(r'LRA low', 'Loudness range', 'LUFS'),
        'lra_high_lufs': grab(r'LRA high', 'Loudness range', 'LUFS'),
        'lra_threshold_lufs': grab(r'Threshold', 'Loudness range', 'LUFS'),
        'gating_threshold_lufs': grab(r'Threshold', 'Integrated loudness', 'LUFS'),
        'true_peak_dbtp': grab(r'Peak', 'True peak', 'dBFS'),
        'curve': curve}
    if result['integrated_lufs'] is not None and result['integrated_lufs'] <= -70:
        result['integrated_lufs'] = None     # ebur128 reports -70 when everything is gated out
    return result


# --------------------------------------------------------------------------- K-weighted interval loudness

class KWeighted:
    """BS.1770 K-weighted power with prefix sums: loudness of any interval without re-filtering."""

    B1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    A1 = [1.0, -1.69065929318241, 0.73248077421585]
    B2 = [1.0, -2.0, 1.0]
    A2 = [1.0, -1.99004745483398, 0.99007225036621]

    def __init__(self, stereo, sr=LUFS_SR):
        import numpy as np
        from scipy.signal import lfilter
        self.sr = sr
        power, raw = np.zeros(len(stereo)), np.zeros(len(stereo))
        for ch in range(stereo.shape[1]):
            x = stereo[:, ch].astype('float64')
            k = lfilter(self.B2, self.A2, lfilter(self.B1, self.A1, x))
            power += k * k
            raw += x * x
        self.cum = np.concatenate([[0.0], np.cumsum(power)])
        self.raw_cum = np.concatenate([[0.0], np.cumsum(raw / stereo.shape[1])])
        self.n = len(power)

    def rms_dbfs(self, start, end):
        a, b = max(0, int(round(start * self.sr))), min(self.n, int(round(end * self.sr)))
        if b - a < self.sr * 0.02:
            return None
        mean = (self.raw_cum[b] - self.raw_cum[a]) / (b - a)
        return 10 * math.log10(mean) if mean > 0 else -120.0

    def power(self, start, end):
        a, b = max(0, int(round(start * self.sr))), min(self.n, int(round(end * self.sr)))
        return (self.cum[b] - self.cum[a]), max(0, b - a)

    def lufs(self, start, end):
        energy, count = self.power(start, end)
        if count < self.sr * 0.02 or energy <= 0:
            return None
        return -0.691 + 10 * math.log10(energy / count)

    def lufs_of(self, intervals):
        energy = count = 0
        for start, end in intervals:
            e, c = self.power(start, end)
            energy, count = energy + e, count + c
        if count < self.sr * 0.02 or energy <= 0:
            return None
        return -0.691 + 10 * math.log10(energy / count)


def interval_lufs(samples, sr=LUFS_SR):
    """Ungated K-weighted LUFS of a mono/stereo float array at 48 kHz (for tests and short intervals)."""
    import numpy as np
    samples = np.asarray(samples, dtype='float64')
    if samples.ndim == 1:
        samples = samples[:, None]
    return KWeighted(samples, sr).lufs(0, len(samples) / sr)


# --------------------------------------------------------------------------- speech structure

def _word_rows(transcript):
    rows = []
    for index, seg in enumerate((transcript or {}).get('segments', [])):
        for w in seg.get('words', []) or []:
            if w.get('end') is not None and w.get('start') is not None:
                rows.append({'start': float(w['start']), 'end': float(w['end']),
                             'word': str(w.get('word', '')).strip(), 'segment': index,
                             'probability': w.get('probability')})
    return rows


def speech_intervals(transcript, merge_gap=0.12):
    """Speech-active intervals from Whisper word timings (segments if no words)."""
    words = _word_rows(transcript)
    spans = [(w['start'], w['end']) for w in words] or \
            [(float(s['start']), float(s['end'])) for s in (transcript or {}).get('segments', [])]
    merged = []
    for start, end in sorted(spans):
        if merged and start - merged[-1][1] < merge_gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def _spectral_speech_intervals(samples, sr=SR):
    """Fallback when no transcript: syllabic (2.5-7 Hz) modulation of the 300-3400 Hz envelope."""
    import numpy as np
    from scipy.signal import butter, sosfilt
    sos = butter(4, [300, 3400], btype='band', fs=sr, output='sos')
    band = sosfilt(sos, samples)
    hop = int(sr * .01)
    n = len(band) // hop
    if n < 150:
        return []
    env = np.log10(np.sqrt(np.mean(band[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-6)
    win, step = 100, 25
    flags = np.zeros(n, bool)
    for s in range(0, n - win + 1, step):
        seg = env[s:s + win] - env[s:s + win].mean()
        spec = np.abs(np.fft.rfft(seg * np.hanning(win))) ** 2
        freqs = np.fft.rfftfreq(win, .01)
        syl = spec[(freqs >= 2.5) & (freqs <= 7)].sum()
        tot = spec[(freqs >= .5) & (freqs <= 20)].sum() + 1e-12
        level = 20 * np.log10(np.sqrt(np.mean(band[s * hop:(s + win) * hop] ** 2)) + 1e-9)
        if syl / tot > .45 and level > -50:
            flags[s:s + win] = True
    out, start = [], None
    for i, flag in enumerate(list(flags) + [False]):
        if flag and start is None:
            start = i
        if not flag and start is not None:
            if (i - start) * .01 >= .4:
                out.append((start * .01, i * .01))
            start = None
    return out


def _gaps(speech, duration, min_gap=0.15):
    gaps, cursor = [], 0.0
    for a, b in speech:
        if a - cursor >= min_gap:
            gaps.append((cursor, a))
        cursor = max(cursor, b)
    if duration - cursor >= min_gap:
        gaps.append((cursor, duration))
    return gaps


def speech_metrics(transcript, samples=None, sr=SR, duration=None, pause_min=0.15):
    """Words/min (overall, speech-only, per segment), pauses, sentence timings, emphasis words."""
    import numpy as np
    if not transcript or not transcript.get('segments'):
        return {'skipped': 'No transcript'}
    words = _word_rows(transcript)
    segments = transcript['segments']
    first = segments[0]['start']
    last = segments[-1]['end']
    duration = duration or last
    n_words = len(words) if words else sum(len(s['text'].split()) for s in segments)
    speech = speech_intervals(transcript)
    active = sum(b - a for a, b in speech)
    result = {'method': 'Whisper word timings', 'confidence': 'ASR timing/word-count estimates (~0.1 s boundary error)',
              'word_count': n_words, 'language': transcript.get('language'),
              'words_per_minute_total': n_words * 60 / duration if duration else None,
              'words_per_minute_speaking_span': n_words * 60 / (last - first) if last > first else None,
              'words_per_minute_articulation': n_words * 60 / active if active else None,
              'speech_start': first, 'speech_end': last, 'speech_active_s': active,
              'speech_ratio': active / duration if duration else None,
              'note': 'total = over whole video; speaking_span = first to last word; articulation = excluding pauses >120 ms'}
    result['segments'] = []
    for i, seg in enumerate(segments):
        n = len(seg.get('words') or []) or len(seg['text'].split())
        dur = seg['end'] - seg['start']
        result['segments'].append({'index': i, 'start': seg['start'], 'end': seg['end'], 'duration': dur,
                                   'words': n, 'words_per_minute': n * 60 / dur if dur > 0 else None,
                                   'text': seg['text']})
    pauses = []
    for prev, nxt in zip(words, words[1:]):
        gap = nxt['start'] - prev['end']
        if gap >= pause_min:
            pauses.append({'start': prev['end'], 'end': nxt['start'], 'duration': gap,
                           'after_word': prev['word'], 'before_word': nxt['word'],
                           'kind': 'between_segments' if prev['segment'] != nxt['segment'] else 'within_segment'})
    if not words:
        for prev, nxt in zip(segments, segments[1:]):
            gap = nxt['start'] - prev['end']
            if gap >= pause_min:
                pauses.append({'start': prev['end'], 'end': nxt['start'], 'duration': gap, 'kind': 'between_segments'})
    result['pauses'] = pauses
    result['pause_total_s'] = sum(p['duration'] for p in pauses)
    result['pause_threshold_s'] = pause_min
    sentences, current = [], []
    for w in words:
        current.append(w)
        if re.search(r'[.!?\u2026]["\u201d\')]*$', w['word']):
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)
    if not sentences:
        sentences = [[{'start': s['start'], 'end': s['end'], 'word': s['text']}] for s in segments]
    result['sentences'] = []
    for chunk in sentences:
        a, b = chunk[0]['start'], chunk[-1]['end']
        n = len(chunk) if words else len(chunk[0]['word'].split())
        result['sentences'].append({'start': a, 'end': b, 'duration': b - a, 'words': n,
                                    'words_per_minute': n * 60 / (b - a) if b > a else None,
                                    'text': ' '.join(w['word'] for w in chunk).strip()})
    emphasis = {'method': 'word RMS (dB) z-score vs median word + duration-per-letter, from transcript word times',
                'confidence': 'heuristic; a music bed adds a constant floor, TTS has little natural emphasis',
                'words': []}
    if samples is not None and len(words) >= 8:
        rows = []
        for w in words:
            a, b = int(w['start'] * sr), int(w['end'] * sr)
            seg = samples[a:b]
            if len(seg) < sr * .1 or not re.search(r'\w', w['word']):
                continue
            rms = float(np.sqrt(np.mean(seg.astype('float64') ** 2)))
            letters = max(1, len(re.sub(r'\W', '', w['word'])))
            rows.append((w, _db(rms), (w['end'] - w['start']) / letters))
        levels = np.array([r[1] for r in rows])
        durs = np.array([r[2] for r in rows])
        l_med, l_sd = np.median(levels), max(np.std(levels), 1.0)
        d_med, d_sd = np.median(durs), max(np.std(durs), 1e-3)
        for w, level, per_letter in rows:
            z_level, z_dur = (level - l_med) / l_sd, (per_letter - d_med) / d_sd
            letters = len(re.sub(r'\W', '', w['word']))
            score = z_level + (.5 * z_dur if letters >= 4 else 0)
            if z_level >= 1.0 or score >= 1.5:
                emphasis['words'].append({
                    'word': w['word'], 'start': w['start'], 'end': w['end'], 'rms_dbfs': level,
                    'level_vs_median_db': float(level - l_med), 'duration_per_letter_ms': per_letter * 1000,
                    'score': float(score)})
        emphasis['words'].sort(key=lambda r: -r['score'])
        emphasis['words'] = emphasis['words'][:max(5, len(rows) // 8)]
        emphasis['median_word_rms_dbfs'] = float(l_med)
    else:
        emphasis['skipped'] = 'needs word timestamps (>=8 words) and samples'
    result['emphasis'] = emphasis
    return result


# --------------------------------------------------------------------------- speech / music

def _env_db(samples, sr=SR, win_s=.05):
    import numpy as np
    hop = int(sr * win_s)
    n = len(samples) // hop
    if n == 0:
        return np.array([])
    blocks = samples[:n * hop].astype('float64').reshape(n, hop)
    return 20 * np.log10(np.sqrt(np.mean(blocks ** 2, axis=1)) + 1e-6)


def speech_music(speech, samples, kw, duration, sr=SR, detection='whisper_word_timings'):
    """Music-bed level in speech gaps, speech-music difference, music entry/exit/fades."""
    import numpy as np
    result = {'method': 'speech intervals (' + detection + ') split the timeline; the music bed is measured in speech gaps '
                        '(quietest 100 ms window per interior gap, median over gaps, full-band stereo-mean) and tracked through a 50 ms RMS envelope',
              'confidence': 'bed level measured in gaps; presence under speech is inferred, not separated',
              'speech_detection': detection, 'speech_intervals': [{'start': a, 'end': b} for a, b in speech]}
    gaps = _gaps(speech, duration)
    rows = []
    for a, b in gaps:
        row = {'start': a, 'end': b, 'duration': b - a, 'usable': b - a >= .1}
        if row['usable'] and kw:
            # Whisper word ends include voice tails: take the quietest 100 ms window inside the gap
            best = None
            t0 = a
            while t0 + .1 <= b + 1e-9:
                level = kw.rms_dbfs(t0, t0 + .1)
                if level is not None and (best is None or level < best[0]):
                    best = (level, t0)
                t0 += .02
            if best:
                row['bed_dbfs'] = best[0]
                row['bed_window'] = [best[1], best[1] + .1]
                row['bed_lufs'] = kw.lufs(best[1], best[1] + .1)
                row['gap_mean_dbfs'] = kw.rms_dbfs(a, b)
            else:
                row['usable'] = False
        elif row['usable']:
            seg = samples[int(a * sr):int(b * sr)]
            row['bed_dbfs'] = _db(float(np.sqrt(np.mean(seg.astype('float64') ** 2)))) if len(seg) else -120.0
            row['bed_lufs'] = None
        rows.append(row)
    result['gaps'] = rows
    for r in rows:
        r['interior'] = r['start'] > .02 and r['end'] < duration - .02
    # edge gaps (before the first / after the last word) hold fades, so the bed comes from interior gaps when possible
    usable = [r for r in rows if r['usable'] and r['interior'] and r['bed_dbfs'] > -80] or              [r for r in rows if r['usable'] and r['bed_dbfs'] > -80]
    speech_db = kw.lufs_of(speech) if kw and speech else None
    result['speech_lufs'] = speech_db
    result['speech_lufs_note'] = 'K-weighted, ungated, over speech intervals; includes any music playing under the voice'
    if not usable:
        result.update({'music_present': None, 'bed_dbfs': None, 'bed_lufs': None, 'speech_minus_bed_db': None,
                       'note': 'no usable speech gap (>=0.16 s) to measure a bed'})
        return result
    bed_db = float(np.median([r['bed_dbfs'] for r in usable]))
    lufs_vals = [r['bed_lufs'] for r in usable if r['bed_lufs'] is not None]
    bed_lufs = float(np.median(lufs_vals)) if lufs_vals else None
    present = bed_db > -55
    result.update({'music_present': bool(present), 'bed_dbfs': bed_db, 'bed_lufs': bed_lufs,
                   'bed_dbfs_range': [min(r['bed_dbfs'] for r in usable), max(r['bed_dbfs'] for r in usable)],
                   'bed_estimate': 'median of per-gap quietest 100 ms windows over interior gaps; Whisper word ends include voice tails, so short gaps can read high (see bed_dbfs_range)',
                   'gap_count_measured': len(usable)})
    result['speech_minus_bed_db'] = (speech_db - bed_lufs) if speech_db is not None and bed_lufs is not None else None
    result['speech_minus_bed_note'] = 'speech LUFS (including bed) minus bed LUFS; the true voice-over-music ratio is slightly larger'
    if not present:
        result['entry'] = result['exit'] = None
        return result
    env = _env_db(samples, sr)
    t = (np.arange(len(env)) + .5) * .05
    in_speech = np.zeros(len(env), bool)
    for a, b in speech:
        in_speech[(t >= a - .04) & (t <= b + .04)] = True
    on = (env >= bed_db - 12)
    first_speech = speech[0][0] if speech else None
    last_speech = speech[-1][1] if speech else 0.0
    nonspeech_on = [i for i in range(len(env)) if not in_speech[i] and on[i]]
    entry = {'time': None, 'basis': None}
    if first_speech is not None and first_speech < .15:
        entry.update(time=0.0, basis='inferred: speech starts at t~0, bed first measured in the first gap')
    elif nonspeech_on:
        entry.update(time=float(t[nonspeech_on[0]] - .025), basis='first non-speech frame within 12 dB of the bed')
        if entry['time'] <= .05:
            entry['time'] = 0.0
    fade_in = None
    if first_speech is None or first_speech > .3:
        lim = int((first_speech if first_speech is not None else duration) / .05)
        head = env[:lim]
        if len(head) >= 4 and head[0] < bed_db - 3 and (head >= bed_db - 3).any():
            s = int(np.argmax(head >= bed_db - 3))
            fade_in = {'start': 0.0, 'end': float(t[s] - .025), 'from_dbfs': float(head[0]),
                       'to_dbfs': bed_db, 'basis': 'envelope below bed - 3 dB at file start'}
    exit_info, fade_out = {'time': None, 'basis': None}, None
    tail = [i for i in range(len(env)) if t[i] > last_speech + .04]
    if tail:
        ev = env[tail]
        tt = t[tail] - .025
        above = np.where(ev >= bed_db - 12)[0]
        if len(above):
            last_on = above[-1]
            exit_info.update(time=float(tt[last_on] + .05 if last_on < len(ev) - 1 else duration),
                             basis='last tail frame within 12 dB of the bed')
        else:
            exit_info.update(time=float(last_speech), basis='music already >12 dB below the bed after the last word')
        ref = float(np.max(ev[:3]))
        held = np.where(ev >= ref - 3)[0]
        if ref >= bed_db - 6 and held[-1] < len(ev) - 1:
            s = int(held[-1])
            quiet = np.where((ev <= ref - 20) & (np.arange(len(ev)) > s))[0]
            if len(quiet):
                e_time, to_db, reached = float(tt[quiet[0]]), float(ev[quiet[0]]), True
            else:
                e_time, to_db, reached = float(duration), float(ev[-1]), False
            s_time = float(tt[s])
            span = max(e_time - s_time, 1e-3)
            fade_out = {'start': s_time, 'end': e_time, 'duration': span, 'from_dbfs': ref, 'to_dbfs': to_db,
                        'slope_db_per_s': (to_db - ref) / span, 'reaches_minus20_db_below_start': reached,
                        'truncated_by_file_end': not reached,
                        'basis': 'tail envelope after the last word (50 ms RMS): last frame within 3 dB of the post-speech level '
                                 'to first frame 20 dB below it'}
    else:
        exit_info.update(time=float(duration), basis='speech runs to the end; exit not observable')
    result['entry'] = entry
    result['fade_in'] = fade_in
    result['exit'] = exit_info
    result['fade_out'] = fade_out
    result['music_active_interval'] = [entry['time'], exit_info['time']]
    result['continuity_note'] = 'music is assumed continuous under speech between measured gaps'
    return result


# --------------------------------------------------------------------------- rhythm (librosa)

def _tempo_from_env(librosa, np, env, sr, hop, lo=60, hi=200, start_bpm=120):
    """Tempo, beats and an explicit confidence from one onset-strength envelope."""
    if len(env) < sr / hop * 3 or float(np.max(env)) <= 1e-6:
        return {'tempo_bpm': None, 'confidence': 0.0, 'note': 'envelope too short or flat'}
    tempo, frames = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=hop, start_bpm=start_bpm, tightness=100)
    tempo = float(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) else None
    beats = [float(x) for x in librosa.frames_to_time(frames, sr=sr, hop_length=hop)]
    ac = librosa.autocorrelate(env - env.mean())
    ac = ac / ac[0] if ac[0] > 0 else ac
    fps = sr / hop
    l_lo, l_hi = int(fps * 60 / hi), min(len(ac) - 1, int(fps * 60 / lo))
    clarity = float(np.clip(np.max(ac[l_lo:l_hi + 1]), 0, 1)) if l_hi > l_lo else 0.0
    out = {'tempo_bpm': tempo, 'beats': beats, 'pulse_clarity': clarity}
    if len(beats) >= 4:
        ibi = np.diff(beats)
        cv = float(np.std(ibi) / np.mean(ibi))
        out['tempo_bpm_from_beats'] = float(60 / np.median(ibi))
        out['beat_interval_cv'] = cv
        out['confidence'] = float(np.clip(.6 * min(1, clarity / .5) + .4 * max(0, 1 - cv * 4), 0, 1))
    else:
        out['confidence'] = 0.0
        out['note'] = 'fewer than 4 beats'
    return out


def _guess_downbeats(np, env, sr, hop, beats, meter=4):
    if len(beats) < meter * 2:
        return {'times': [], 'meter_assumed': meter, 'confidence': 0.0, 'method': 'skipped: fewer than 8 beats'}
    idx = np.clip((np.array(beats) * sr / hop).astype(int), 0, len(env) - 1)
    vals = env[idx]
    sums = [float(vals[p::meter].mean()) for p in range(meter)]
    best = int(np.argmax(sums))
    spread = (max(sums) - float(np.mean(sums))) / (float(np.mean(sums)) + 1e-9)
    return {'times': [float(b) for b in beats[best::meter]], 'meter_assumed': meter, 'phase': best,
            'confidence': float(np.clip(spread / .5, 0, 1)),
            'method': 'librosa has no downbeat tracker: assume 4/4, pick the beat phase with the highest mean onset strength',
            'caveat': 'heuristic; correct only for steady 4/4 music with accented downbeats'}


def _classify_onset(row):
    """Rough class from spectral/decay descriptors. Returns (class, confidence, scores)."""
    low, flat, dec, rise, cen = (row['sub_ratio'], row['flatness'], row['decay_ms'], row['rise_db'], row['centroid_hz'])
    low_wide = row['low_ratio']
    scores = {
        'bass_hit': (1.0 if low > .6 else max(0, (low - .25) / .35)) * (1.0 if cen < 600 else .3) * (1 if dec >= 60 else .5),
        'impact': min(1, rise / 20) * min(1, dec / 250) * (1 if (low_wide > .12 or flat > .05) else .4) * (1 if low <= .6 else .6),
        'pop_click': min(1, rise / 15) * (1 if dec < 80 else max(0, 1 - (dec - 80) / 200)) * (1 if cen > 1500 else .5),
        'tonal_note': min(1, max(0, .15 - flat) / .15) * (1 if dec >= 80 else .5) * (.7 if rise < 25 else .5),
    }
    name = max(scores, key=scores.get)
    best = scores[name]
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1]
    if best < .25:
        return 'unclassified', 0.2, scores
    return name, float(np_clip(.35 + .4 * margin + .25 * best, 0, .85)), scores


def detect_onsets(librosa, np, y, sr, speech, min_gap_ms=40, word_starts=()):
    """Spectral-flux onsets at ~5.8 ms resolution, refined on the waveform, with power + rough class."""
    hop, n_fft = 128, 512
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, n_fft=n_fft, lag=1, max_size=3, aggregate=np.median)
    if not len(env) or float(env.max()) <= 0:
        return [], env
    floor = np.percentile(env, 90)
    wait = max(1, int(min_gap_ms / 1000 * sr / hop))
    pre = int(.02 * sr / hop) + 1
    avg = int(.1 * sr / hop)
    peaks = librosa.util.peak_pick(env, pre_max=pre, post_max=pre, pre_avg=avg, post_avg=avg,
                                   delta=max(2.0, .6 * floor), wait=wait)
    sm = max(1, int(sr * .001))
    amp = np.convolve(np.abs(y), np.ones(sm) / sm, mode='same')
    events = []
    for p in peaks:
        t0 = float(p * hop / sr)
        a, b = max(0, int((t0 - .025) * sr)), min(len(y), int((t0 + .015) * sr))
        if b - a < 8:
            continue
        local = amp[a:b]
        peak_idx = int(np.argmax(local))
        pk = float(local[peak_idx])
        pre_level = float(np.percentile(amp[max(0, a - int(.03 * sr)):a + 1], 90)) if a > 0 else 0.0
        if pk <= 1e-5 or pk < pre_level * 1.5:
            continue
        thresh = max(pre_level, .3 * pk)
        cross = np.nonzero(local[:peak_idx + 1] >= thresh)[0]
        t = float((a + (int(cross[0]) if len(cross) else peak_idx)) / sr)
        s0, s1 = max(0, int((t - .03) * sr)), int(t * sr) + 1
        e0, e1 = int(t * sr), min(len(y), int((t + .05) * sr))
        pre_rms = float(np.sqrt(np.mean(y[s0:s1].astype('float64') ** 2))) if s1 > s0 else 0.0
        post_rms = float(np.sqrt(np.mean(y[e0:e1].astype('float64') ** 2))) if e1 > e0 else 0.0
        level = _db(post_rms)
        rise = level - _db(max(pre_rms, 1e-5))
        if level < -60 or rise < 6:
            continue
        w0, w1 = int(t * sr), min(len(y), int((t + .08) * sr))
        win = y[w0:w1].astype('float64')
        if len(win) < 256:
            continue
        spec = np.abs(np.fft.rfft(win * np.hanning(len(win)), 2048)) ** 2
        freqs = np.fft.rfftfreq(2048, 1 / sr)
        total = spec.sum() + 1e-18
        band = freqs >= 50
        centroid = float((freqs * spec).sum() / total)
        flat = float(np.exp(np.mean(np.log(spec[band] + 1e-18))) / (np.mean(spec[band]) + 1e-18))
        seg = y[int(t * sr):min(len(y), int((t + 1.0) * sr))].astype('float64')
        k = int(sr * .005)
        blocks = len(seg) // k
        dec = 1000.0
        if blocks >= 4:
            r = 20 * np.log10(np.sqrt(np.mean(seg[:blocks * k].reshape(blocks, k) ** 2, axis=1)) + 1e-9)
            pk_i = int(np.argmax(r[:max(2, int(.05 / .005))]))
            below = np.nonzero(r[pk_i:] <= r[pk_i] - 20)[0]
            dec = float((below[0] if len(below) else len(r) - pk_i) * 5)
        row = {'time': t, 'time_ms': round(t * 1000, 1), 'flux': float(env[p]),
               'rise_db': float(rise), 'strength': float(np_clip(rise / 30, 0, 1)), 'level_dbfs': float(level),
               'centroid_hz': centroid, 'low_ratio': float(spec[freqs < 200].sum() / total),
               'sub_ratio': float(spec[freqs < 120].sum() / total),
               'high_ratio': float(spec[freqs > 4000].sum() / total), 'flatness': flat, 'decay_ms': dec}
        row['during_speech'] = any(a_ - .02 <= t <= b_ + .02 for a_, b_ in speech)
        row['word_aligned'] = any(abs(t - w) <= .06 for w in word_starts)
        cls, conf, _ = _classify_onset(row)
        if row['word_aligned']:
            cls, conf = 'speech_onset', .6
        elif row['during_speech'] and (cls in ('pop_click', 'tonal_note', 'unclassified') or (rise < 18 and cls != 'bass_hit')):
            cls, conf = 'speech_onset', min(conf, .5) if conf else .3
        row['class'], row['class_confidence'] = cls, float(conf)
        events.append(row)
    return events, env


def detect_sweeps(librosa, np, y, sr, speech):
    """Whoosh / riser candidates: slow, noise-like broadband energy growth (>=0.3 s, >=8 dB)."""
    from scipy.ndimage import median_filter, uniform_filter1d
    n_fft, hop = 2048, 512
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    band = (freqs >= 1500) & (freqs <= 9000)
    if not band.any() or S.shape[1] < 10:
        return []
    energy = 10 * np.log10(S[band].sum(axis=0) + 1e-12)
    energy = uniform_filter1d(median_filter(energy, size=3), size=5)
    flat = librosa.feature.spectral_flatness(S=np.sqrt(S[band]))[0]
    cen = librosa.feature.spectral_centroid(S=np.sqrt(S), sr=sr)[0]
    fps = sr / hop
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(energy, prominence=6, distance=max(1, int(.5 * fps)))
    out, rejected = [], 0
    for p in peaks:
        s = p
        while s > 0 and energy[s - 1] <= energy[s] + 1.0:
            s -= 1
        rise = float(energy[p] - energy[s])
        dur = (p - s) / fps
        if dur < .3 or rise < 8 or rise / dur < 3:
            continue
        e = p
        while e < len(energy) - 1 and energy[e + 1] <= energy[e] + 1.0:
            e += 1
        fall, fall_dur = float(energy[p] - energy[e]), (e - p) / fps
        mean_flat = float(np.mean(flat[s:p + 1]))
        if mean_flat < .03:
            continue
        t0, t1 = s / fps, p / fps
        overlap = sum(max(0, min(t1, b) - max(t0, a)) for a, b in speech) / max(t1 - t0, 1e-6)
        conf = .3 + .25 * min(1, rise / 20) + .2 * min(1, mean_flat / .3) + .1 * min(1, dur / 1.0)
        if overlap > .5:
            rejected += 1          # voiced/fricative speech also grows in this band; cannot separate a whoosh under a voice
            continue
        kind = 'whoosh' if fall >= 8 and fall_dur >= .2 else 'riser'
        if kind == 'whoosh':
            conf += .05
        out.append({'type': kind, 'start': float(t0), 'peak_time': float(t1),
                    'end': float(e / fps) if kind == 'whoosh' else float(t1),
                    'rise_db': rise, 'rise_s': float(dur), 'fall_db': fall, 'fall_s': float(fall_dur),
                    'flatness': mean_flat, 'centroid_start_hz': float(cen[s]), 'centroid_end_hz': float(cen[p]),
                    'speech_overlap': float(overlap), 'confidence': float(np_clip(conf, 0, .85)),
                    'method': '1.5-9 kHz band energy growth with noise-like flatness'})
    detect_sweeps.rejected_in_speech = rejected
    return out


def analyze_rhythm(source, speech, duration, report, word_starts=()):
    import numpy as np
    import librosa
    y = pcm(source, MSR)
    if len(y) < MSR:
        raise ValueError('audio shorter than 1 s')
    events, _ = detect_onsets(librosa, np, y, MSR, speech, word_starts=word_starts)
    report['onset_events'] = events
    report['onsets'] = [e['time'] for e in events]
    report['onset_method'] = {
        'method': 'librosa onset_strength (spectral flux, 512-pt STFT, 128-sample hop = 5.8 ms), peak-picked and refined on the waveform',
        'resolution_ms': 5.8, 'confidence': 'onset times measured (~5-10 ms); strength measured; class is a rough guess',
        'strength': 'min(1, rise_db / 30), rise_db = RMS 50 ms after minus 30 ms before the onset',
        'classes': ['impact', 'bass_hit', 'pop_click', 'tonal_note', 'speech_onset', 'unclassified'],
        'class_note': 'speech_onset = within 60 ms of a Whisper word start or soft onset inside speech; bass_hit = energy mostly below 120 Hz; impact = loud broadband decaying hit; whoosh/riser are in sfx_candidates (slow growth cannot be a flux peak)'}
    report['sfx_candidates'] = detect_sweeps(librosa, np, y, MSR, speech)
    report['sfx_detection'] = {'method': 'noise-like 1.5-9 kHz energy growth >=8 dB over >=0.3 s (whoosh = rise then fall, riser = rise)',
                               'rejected_overlapping_speech': getattr(detect_sweeps, 'rejected_in_speech', 0),
                               'limit': 'sweeps under a voice (>50% overlap with speech) are rejected: speech energy growth looks the same'}
    hop = 256
    estimates, envs = {}, {}
    envs['full_mix'] = librosa.onset.onset_strength(y=y, sr=MSR, hop_length=hop)
    try:
        if duration <= 900:
            perc = librosa.effects.percussive(y, margin=2.0)
            envs['percussive_hpss'] = librosa.onset.onset_strength(y=perc, sr=MSR, hop_length=hop)
        else:
            estimates['percussive_hpss'] = {'skipped': 'longer than 15 min'}
    except Exception as exc:  # noqa: BLE001 - optional stage
        estimates['percussive_hpss'] = {'skipped': str(exc)}
    base = envs.get('percussive_hpss', envs['full_mix'])
    if speech:
        masked = base.copy()
        fr = librosa.frames_to_time(np.arange(len(masked)), sr=MSR, hop_length=hop)
        for a, b in speech:
            masked[(fr >= a - .05) & (fr <= b + .05)] = 0
        frac = float((masked == 0).mean())
        report['speech_masked_fraction'] = frac
        if frac < .85:
            envs['percussive_speech_masked'] = masked
    for name, env in envs.items():
        estimates[name] = _tempo_from_env(librosa, np, env, MSR, hop)
    usable = {k: v for k, v in estimates.items() if v.get('tempo_bpm')}
    primary_name = max(usable, key=lambda k: usable[k]['confidence']) if usable else None
    primary = usable[primary_name] if primary_name else None
    report['tempo'] = {'primary': primary_name,
                       'estimates': {k: {kk: vv for kk, vv in v.items() if kk != 'beats'} for k, v in estimates.items()}}
    if primary:
        reliable = primary['confidence'] >= .5 and duration >= 4
        report['tempo_bpm'] = primary.get('tempo_bpm_from_beats') or primary['tempo_bpm']
        report['tempo_confidence'] = primary['confidence']
        report['beats'] = primary['beats']
        report['beat_info'] = {'source': primary_name, 'reliable': bool(reliable), 'count': len(primary['beats']),
                               'note': 'beats are a metronomic grid fitted to onset energy; with tempo_confidence < 0.5 '
                                       'treat as a guess (speech-dominated or beatless audio)'}
        report['downbeats'] = _guess_downbeats(np, envs[primary_name], MSR, hop, primary['beats'])
    else:
        report['tempo_bpm'], report['tempo_confidence'], report['beats'] = None, 0.0, []
        report['beat_info'] = {'source': None, 'reliable': False, 'count': 0, 'note': 'no tempo estimate'}
        report['downbeats'] = {'times': [], 'confidence': 0.0, 'method': 'skipped'}
    report['rhythm'] = {'method': f'librosa {librosa.__version__}: spectral-flux onsets, HPSS-percussive and speech-masked '
                                  'beat tracking, 4/4 downbeat-phase heuristic, noise-band sweep detector',
                        'confidence': 'estimate; tempo/beat confidence in tempo_confidence (0-1); event classes are guesses'}


# --------------------------------------------------------------------------- cut / beat alignment

def _times(items, keys=('start', 'time')):
    if isinstance(items, dict):
        for k in ('transitions', 'records', 'scenes', 'cuts'):
            if k in items:
                items = items[k]
                break
        else:
            return []
    out = []
    for item in items or []:
        if isinstance(item, (int, float)):
            out.append(float(item))
            continue
        for k in keys:
            if isinstance(item, dict) and item.get(k) is not None:
                out.append(float(item[k]))
                break
    return out


def _nearest(t, grid):
    best = None
    for g in grid:
        d = (t - g) * 1000
        if best is None or abs(d) < abs(best):
            best = d
    return best


def cut_alignment(scenes, beats, tolerance_ms=80):
    rows = []
    for scene in scenes[1:]:
        delta = min((abs(scene['start'] - beat) * 1000 for beat in beats), default=None)
        rows.append({'cut': scene['start'], 'nearest_beat_ms': delta,
                     'aligned': delta <= tolerance_ms if delta is not None else None})
    return {'method': 'nearest beat, absolute time distance', 'confidence': 'depends on estimated beat times',
            'tolerance_ms': tolerance_ms, 'cuts': rows,
            'aligned_ratio': sum(row['aligned'] for row in rows) / len(rows) if rows and beats else None}


def cut_beat_alignment(beats=(), onsets=(), scenes=(), transitions=None, text_records=None,
                       tolerance_ms=80, beat_confidence=None):
    """Align scene cuts (first scene start is not a cut), transitions (``transitions[].start``) and
    caption changes (``records[].start``) to beats and onsets. Each of ``scenes``/``transitions``/
    ``text_records`` may be a list or the loaded JSON dict. Distances are signed: event minus beat, ms."""
    beats = [float(b) for b in beats]
    onsets = [float(o) for o in onsets]
    cut_times = _times(scenes)[1:]
    trans_times = _times(transitions)
    text_times = sorted(set(round(t, 3) for t in _times(text_records)))
    out = {'method': 'nearest beat / onset, signed distance (event minus beat, ms; negative = event early)',
           'confidence': 'depends on estimated beat times' + ('' if beat_confidence is None else f' (tempo confidence {beat_confidence:.2f})'),
           'tolerance_ms': tolerance_ms, 'beat_count': len(beats), 'onset_count': len(onsets),
           'beat_confidence': beat_confidence}
    median_ibi = None
    if len(beats) >= 2:
        diffs = sorted(b - a for a, b in zip(beats, beats[1:]))
        median_ibi = diffs[len(diffs) // 2]
    out['chance_aligned_ratio'] = min(1.0, 2 * tolerance_ms / 1000 / median_ibi) if median_ibi else None
    out['chance_note'] = 'aligned ratio expected if events were placed at random (2 * tolerance / beat interval)'

    def block(times, label):
        rows = []
        for t in times:
            sb = _nearest(t, beats) if beats else None
            so = _nearest(t, onsets) if onsets else None
            rows.append({label: t, 'nearest_beat_ms': abs(sb) if sb is not None else None, 'signed_beat_ms': sb,
                         'aligned': abs(sb) <= tolerance_ms if sb is not None else None,
                         'nearest_onset_ms': abs(so) if so is not None else None, 'signed_onset_ms': so,
                         'onset_aligned': abs(so) <= tolerance_ms if so is not None else None})
        done = [r for r in rows if r['aligned'] is not None]
        ond = [r for r in rows if r['onset_aligned'] is not None]
        return rows, {'count': len(rows),
                      'aligned_ratio': sum(r['aligned'] for r in done) / len(done) if done else None,
                      'onset_aligned_ratio': sum(r['onset_aligned'] for r in ond) / len(ond) if ond else None,
                      'median_signed_beat_ms': sorted(r['signed_beat_ms'] for r in done)[len(done) // 2] if done else None}
    out['cuts'], out['cuts_summary'] = block(cut_times, 'cut')
    out['aligned_ratio'] = out['cuts_summary']['aligned_ratio']
    out['onset_aligned_ratio'] = out['cuts_summary']['onset_aligned_ratio']
    if transitions is not None:
        out['transitions'], out['transitions_summary'] = block(trans_times, 'start')
    else:
        out['transitions'] = None
        out['transitions_note'] = 'transitions.json not available'
    if text_records is not None:
        out['text_changes'], out['text_changes_summary'] = block(text_times, 'start')
    else:
        out['text_changes'] = None
        out['text_changes_note'] = 'onscreen_text.json not available'
    return out


def sfx_vs_cuts(events, cuts, tolerance_ms=120):
    rows = []
    for ev in events:
        t = ev.get('peak_time', ev.get('time'))
        if t is None or not cuts:
            continue
        d = _nearest(t, cuts)
        rows.append({'type': ev.get('type') or ev.get('class'), 'time': t, 'nearest_cut_ms': d,
                     'near_cut': abs(d) <= tolerance_ms})
    return rows


def _load_sibling(output, name):
    path = Path(output).parent / name
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None
    return None


# --------------------------------------------------------------------------- main entry

def analyze_audio(source, info, output, scenes=(), transcript=None, transitions=None, text_records=None):
    import numpy as np
    report = {'method': 'mono 16kHz PCM, 100ms non-overlapping RMS', 'confidence': 'measured signal energy',
              'schema_version': 2, 'sample_rate': 16000, 'resolution_s': .1, 'rms_curve': [], 'loudness_curve': [],
              'silence_intervals': [], 'beats': [], 'onsets': [], 'tempo_bpm': None,
              'integrated_lufs': None, 'true_peak_dbtp': None, 'lra': None, 'loudness_range': None}
    if not info['has_audio']:
        report['skipped'] = 'No audio stream'
        save(output, report)
        return report
    warnings = report['warnings'] = []
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
            label = 'silence' if db < SILENCE_DB else 'speech_candidate' if voice else 'non_speech_audio'
            report['rms_curve'].append({'time': start, 'end': end, 'rms': rms, 'dbfs': db,
                                        'classification': label})
            if db < SILENCE_DB and silent_start is None:
                silent_start = start
            if db >= SILENCE_DB and silent_start is not None:
                report['silence_intervals'].append({'start': silent_start, 'end': start})
                silent_start = None
        if silent_start is not None:
            report['silence_intervals'].append({'start': silent_start, 'end': len(samples) / sr})
        duration = float(info.get('duration') or len(samples) / sr)
        report['classification'] = {
            'method': 'VAD-filtered Whisper transcript overlap and -45 dBFS energy threshold',
            'confidence': 'heuristic; non-speech audio may contain music, effects or noise',
            'transcript_available': bool(transcript),
            'music_separation': {'skipped': 'No stem separation; the music bed is measured in speech gaps (see speech_music)'}}

        try:
            meter = measure_ebur128(source)
            report['loudness_curve'] = meter['curve']
            report['integrated_lufs'] = meter['integrated_lufs']
            report['true_peak_dbtp'] = meter['true_peak_dbtp']
            report['lra'] = meter['lra']
            report['loudness_range'] = {'lra_lu': meter['lra'], 'low_lufs': meter['lra_low_lufs'],
                                        'high_lufs': meter['lra_high_lufs'], 'threshold_lufs': meter['lra_threshold_lufs'],
                                        'unit': 'LU'}
            report['loudness_method'] = {
                'method': 'FFmpeg ebur128=peak=true, one pass: EBU R128 integrated (gated), LRA, 4x-oversampled true peak; '
                          'curve = momentary (400 ms window) at 100 ms reporting',
                'confidence': 'measured', 'gating_threshold_lufs': meter['gating_threshold_lufs'],
                'note': 'RMS dBFS and LUFS are different units',
                'null_values_note': 'momentary_lufs/short_term_lufs are null while the 400 ms / 3 s window is not yet full '
                                    '(first 0.4 s / 3 s) and where ebur128 reports its -120.7 floor (digital silence)'}
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            warnings.append(f'loudness failed: {exc}')

        if transcript and transcript.get('segments'):
            spans, detection = speech_intervals(transcript), 'whisper_word_timings'
        else:
            try:
                spans = _spectral_speech_intervals(samples)
                detection = 'spectral_heuristic_syllabic_modulation (low confidence, no transcript)'
            except ImportError as exc:
                spans, detection = [], 'unavailable: no transcript or optional spectral backend'
                report['classification']['speech_detection'] = {'skipped': str(exc)}
        kw = None
        try:
            try:
                from .media import probe
                chans = next(st.get('channels', 2) for st in probe(source)['streams'] if st['codec_type'] == 'audio')
            except (StopIteration, KeyError, OSError, ValueError, subprocess.SubprocessError):
                chans = 2
            kw = KWeighted(_pcm_stereo(source, channels=1 if chans == 1 else 2))
        except (OSError, subprocess.SubprocessError, ValueError, ImportError) as exc:
            warnings.append(f'K-weighted interval loudness failed: {exc}')
        try:
            report['speech_music'] = speech_music(spans, samples, kw, duration, sr, detection)
        except Exception as exc:  # noqa: BLE001 - keep the rest of the report
            warnings.append(f'speech_music failed: {exc}')
        try:
            report['speech_metrics'] = speech_metrics(transcript, samples, sr, duration)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f'speech_metrics failed: {exc}')

        try:
            analyze_rhythm(source, spans, duration, report, [w['start'] for w in _word_rows(transcript)])
        except (ImportError, AttributeError, RuntimeError, ValueError) as exc:
            report['rhythm'] = {'skipped': f'librosa unavailable or failed: {exc}'}
            energy = [row['rms'] for row in report['rms_curve']]
            rises = np.diff(energy, prepend=0)
            threshold = max(.02, float(np.median(abs(rises))) * 4)
            report['onsets'] = [i * .1 for i, rise in enumerate(rises) if rise > threshold]
            report['onset_method'] = {'method': '100ms RMS positive rise threshold', 'confidence': 'low; coarse estimate'}

        sibling_trans = transitions if transitions is not None else _load_sibling(output, 'transitions.json')
        sibling_text = text_records if text_records is not None else _load_sibling(output, 'onscreen_text.json')
        if isinstance(sibling_text, dict) and sibling_text.get('skipped'):
            sibling_text = None
        alignment = cut_beat_alignment(report['beats'], report['onsets'], scenes, sibling_trans, sibling_text,
                                       beat_confidence=report.get('tempo_confidence'))
        cuts = _times(scenes)[1:] + _times(sibling_trans)
        if cuts and report.get('sfx_candidates') is not None:
            strong = [e for e in report.get('onset_events', []) if e['class'] in ('impact', 'bass_hit') and e['strength'] >= .5]
            alignment['sfx_vs_cuts'] = sfx_vs_cuts(report['sfx_candidates'] + strong, sorted(cuts))
        report['cut_beat_alignment'] = alignment
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        report['skipped'] = f'Audio measurement failed: {exc}'
    if not report.get('warnings'):
        report.pop('warnings', None)
    save(output, report)
    return report
