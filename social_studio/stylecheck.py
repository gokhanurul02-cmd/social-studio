"""Style conformance report: reference style vs one or more new videos, metric by metric.

    social stylecheck REFERENCE CANDIDATE_ANALYSIS [CANDIDATE_ANALYSIS ...] [--out DIR]

REFERENCE is a ``style.json`` (as written by the video-analiz skill), a folder that contains one, or a
``social analyze`` output folder.  Every CANDIDATE is a ``social analyze`` output folder of the new video.

Each row states the reference value, the new value, the difference, the explicit rule and PASS / FAIL.
Rows that cannot be compared like-for-like are INFO (shown, not gating) and rows with a missing
measurement are SKIP.  There is deliberately no overall "similarity percentage": a style match is the
set of rules that passed, and the agent still has to look at frames.

Loudness is checked against the delivery target (-16..-14 LUFS, <= -1 dBTP), not against the
reference's own mix: references are often clipped (-8 LUFS / +1.5 dBTP), which we must not copy.
Speech pace is compared as syllables per second when the two languages differ, because words per
minute is not comparable between English and agglutinative Turkish.
"""
from __future__ import annotations

import json
import math
import re
import statistics
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

# ----------------------------------------------------------------------------- thresholds
# Every gate is listed here, printed in the report and overridable with --thresholds FILE.json.
THRESHOLDS = {
    'aspect_abs': 0.01,                 # width/height
    'fps_exact': True,                  # rational fps must be equal
    'caption_baseline_abs': 0.012,      # fraction of frame height (~23 px at 1920)
    'caption_size_rel': 0.12,           # font size / frame height, relative
    'caption_fill_delta_e': 12.0,       # CIE76 ΔE of caption fill colour
    'caption_group_mean_rel': 0.25,     # mean caption group duration, relative
    'caption_rate_rel': 0.25,           # caption groups per second, relative
    'first_caption_max_late_s': 0.35,   # first caption may appear at most this much later than the reference
    'transitions_per_s_abs': 0.15,      # transitions (cut/flip/whip/zoom burst) per second, absolute
    'palette_delta_e': 15.0,            # weighted mean of each reference colour's nearest new colour (CIE76)
    'lufs_range': [-16.0, -14.0],       # delivery target, integrated LUFS
    'true_peak_max': -1.0,              # dBTP
    'wpm_rel': 0.15,                    # same-language words per minute (speaking span), relative
    'syllable_rate_rel': 0.20,          # syllables per second (speaking span), relative; same language only
    'max_pause_extra_s': 0.20,          # longest gap between words may exceed the reference by this much
    # composition (local estimates, see composition.py; the candidate is gated, the reference only shown)
    'comp_flat_fill_max': 0.27,         # one low-texture non-sky single-colour block may cover at most this share of the frame
    'comp_edge_contact': 0.22,          # subject touches a frame border over >= this fraction of it ...
    'comp_edge_area': 0.30,             # ... while covering >= this share of the frame (non-crowd shots) = edge cut
    'comp_flag_min_samples': 2,         # consecutive samples (3 fps) before a flat-fill/edge-cut event is reported
    'comp_flat_fill_events_max': 0,     # allowed number of flat-fill events in the candidate
    'comp_edge_cut_events_max': 0,      # allowed number of edge-cut events in the candidate
    'comp_area_median_abs': 0.08,       # median subject area share, absolute
    'comp_shot_share_abs': 0.25,        # share of each shot type (wide/medium/close/crowd), absolute
    'comp_horizon_abs': 0.12,           # median horizon y/H, absolute (only when both detect one in >= 50 % of samples)
    'comp_centered_abs': 0.25,          # share of samples with the subject centred (|x-0.5| <= 0.12), absolute
    'comp_pair_max': 7,                 # same-moment pairs written per candidate
}

# ----------------------------------------------------------------------------- small helpers


def _load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _maybe(path):
    try:
        return _load(path) if Path(path).is_file() else None
    except (OSError, ValueError):
        return None


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _fps(value):
    try:
        return Fraction(str(value)).limit_denominator(100000)
    except (ValueError, ZeroDivisionError):
        return None


def hex_to_lab(hx):
    hx = hx.lstrip('#')
    rgb = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    y = (0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])
    z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = [v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116 for v in (x, y, z)]
    return (116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2]))


def delta_e(a, b):
    return math.dist(hex_to_lab(a), hex_to_lab(b))


def palette_distance(ref, new):
    """Weighted mean over reference colours of the ΔE to the closest new colour."""
    if not ref or not new:
        return None
    total = sum(w for _, w in ref) or 1.0
    return sum(w * min(delta_e(h, n) for n, _ in new) for h, w in ref) / total


# ----------------------------------------------------------------------------- speech pace

EN_WORDS = {'the', 'you', 'of', 'to', 'and', 'a', 'if', 'would', 'them', 'it', 'is', 'that', 'with', 'just', 'but', 'need', 'one'}
TR_WORDS = {'bir', 've', 'bu', 'için', 'gibi', 'da', 'de', 'ne', 'çok', 'peki', 'ama', 'sadece', 'en', 'az', 'kaç', 'olurdu'}
TR_ONES = ['', 'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz']
TR_TENS = ['', 'on', 'yirmi', 'otuz', 'kırk', 'elli', 'altmış', 'yetmiş', 'seksen', 'doksan']
EN_ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
           'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
EN_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']


def guess_language(text, declared=None):
    """Whisper is often forced to 'tr'; decide from the words themselves."""
    words = re.findall(r"[^\W\d_]+", text.lower())
    if not words:
        return declared or 'unknown'
    en = sum(w in EN_WORDS for w in words)
    tr = sum(w in TR_WORDS for w in words) + sum(any(c in w for c in 'çğışöü') for w in words)
    if en > tr:
        return 'en'
    if tr > en:
        return 'tr'
    return declared or 'unknown'


def _tr_number(n):
    if n == 0:
        return 'sıfır'
    out = []
    for value, word in ((1000000, 'milyon'), (1000, 'bin')):
        if n >= value:
            k, n = divmod(n, value)
            if not (value == 1000 and k == 1):
                out.append(_tr_number(k))
            out.append(word)
    if n >= 100:
        h, n = divmod(n, 100)
        if h > 1:
            out.append(TR_ONES[h])
        out.append('yüz')
    out += [TR_TENS[n // 10], TR_ONES[n % 10]]
    return ' '.join(w for w in out if w)


def _en_number(n):
    if n == 0:
        return 'zero'
    out = []
    for value, word in ((1000000, 'million'), (1000, 'thousand'), (100, 'hundred')):
        if n >= value:
            k, n = divmod(n, value)
            out += [_en_number(k), word]
    if n >= 20:
        out += [EN_TENS[n // 10], EN_ONES[n % 10]]
    elif n:
        out.append(EN_ONES[n])
    return ' '.join(w for w in out if w)


def count_syllables(word, lang):
    word = word.lower().strip()
    digits = re.sub(r'[^\d]', '', word)
    if digits and digits == re.sub(r'[.,\s]', '', word):
        n = int(digits)
        spoken = _tr_number(n) if lang == 'tr' else _en_number(n)
        return sum(count_syllables(w, lang) for w in spoken.split())
    letters = re.sub(r"[^\w]", '', word)
    if not letters:
        return 0
    if lang == 'tr':
        return max(1, sum(c in 'aeıioöuüâîû' for c in letters))
    groups = re.findall(r'[aeiouy]+', letters)
    n = len(groups)
    if letters.endswith('e') and not letters.endswith('le') and n > 1:
        n -= 1
    return max(1, n)


def speech_pace(transcript):
    """Words and syllables over the speaking span (first word start .. last word end)."""
    if not transcript:
        return None
    segs = transcript.get('segments', [])
    words = [w for s in segs for w in s.get('words', [])]
    text = ' '.join(s.get('text', '') for s in segs)
    if not words:
        return None
    lang = guess_language(text, transcript.get('language'))
    span = max(1e-6, words[-1]['end'] - words[0]['start'])
    syl = sum(count_syllables(w['word'], lang) for w in words)
    gaps = [b['start'] - a['end'] for a, b in zip(words, words[1:])]
    return {'language': lang, 'words': len(words), 'span_s': span, 'wpm_span': len(words) * 60 / span,
            'syllables': syl, 'syllables_per_s': syl / span, 'max_pause_s': max(gaps) if gaps else 0.0}


# ----------------------------------------------------------------------------- camera / transition vocab
# Reference style.json camera and transition descriptions are free text (Turkish); map them onto the
# analyser's families so both sides use one vocabulary.
CAMERA_KEYWORDS = [
    ('pull_back', ('geri', 'çekiliş', 'cekilis', 'pull back', 'dolly out', 'reveal')),
    ('push_in', ('ileri dalış', 'dolly in', 'push in', 'ileri zoom')),
    ('static', ('sabit', 'göz hizası', 'goz hizasi', 'static')),
    ('lateral', ('yanal', 'kayma', 'pan', 'truck')),
]
TRANSITION_KEYWORDS = [
    ('flip', ('kart çevirme', 'kart cevirme', 'flip')),
    ('zoom_burst', ('zoom burst', 'zoom patlaması', 'dalış')),
    ('whip', ('whip',)),
    ('hard_cut', ('kesim', 'hard cut')),
    ('dissolve', ('dissolve', 'geçiş karışım')),
]
CAMERA_FAMILY = {'dolly_out': 'pull_back', 'zoom_out': 'pull_back', 'dolly_in': 'push_in', 'zoom_in': 'push_in',
                 'static': 'static', 'pan_left': 'lateral', 'pan_right': 'lateral', 'truck_left': 'lateral',
                 'truck_right': 'lateral', 'tilt_up': 'tilt', 'tilt_down': 'tilt'}


def classify(text, table):
    t = text.lower()
    found = [name for name, keys in table if any(k in t for k in keys)]
    return found


# ----------------------------------------------------------------------------- profiles
# A profile is {metric: {'value': x, 'source': str}}; missing metrics are simply absent.


def _put(profile, key, value, source):
    if value is not None:
        profile[key] = {'value': value, 'source': source}


def _parse_range(value):
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return [float(value[0]), float(value[1])]
    if isinstance(value, str):
        m = re.match(r'\s*(\d+(?:\.\d+)?)\s*[-–…]\s*(\d+(?:\.\d+)?)', value)
        if m:
            return [float(m.group(1)), float(m.group(2))]
    if _num(value):
        return [float(value), float(value)]
    return None


# Hand-measured style.json values and automated analyser values differ systematically (a hand count of
# transitions, a single-frame palette).  When the reference style.json sits next to its analysis folder,
# these metrics are taken from the SAME automated measurement that the candidate gets; the hand value is
# kept in the source note.
LIKE_FOR_LIKE = ('palette', 'transitions_per_s', 'transition_types', 'caption_baseline_y_ratio',
                 'caption_size_ratio', 'caption_group_mean_s', 'caption_groups_per_s', 'caption_stroke')


def profile_from_style(style, base_dir, cache_dir=None, measure=True):
    p = {'_kind': 'style.json'}
    form = style.get('format', {})
    duration = form.get('duration_s')
    if form.get('width') and form.get('height'):
        _put(p, 'aspect', form['width'] / form['height'], 'style.json format')
    _put(p, 'fps', str(form['fps']) if form.get('fps') else None, 'style.json format')
    _put(p, 'duration_s', duration, 'style.json format')
    cap = style.get('captions', {})
    _put(p, 'caption_baseline_y_ratio', cap.get('baseline_y_ratio'), 'style.json captions')
    _put(p, 'caption_size_ratio', cap.get('size_ratio'), 'style.json captions')
    _put(p, 'caption_fill_hex', cap.get('fill'), 'style.json captions')
    if 'stroke' in cap:
        _put(p, 'caption_stroke', bool(cap.get('stroke')), 'style.json captions')
    if 'shadow' in cap:
        _put(p, 'caption_shadow', bool(cap['shadow']), 'style.json captions')
    anim = str(cap.get('animation', ''))
    if anim:
        _put(p, 'caption_animation', 'cut' if any(k in anim.lower() for k in ('kesme', 'cut', 'yok')) else anim, 'style.json captions')
    _put(p, 'caption_words_per_group', _parse_range(cap.get('words_per_group')), 'style.json captions')
    rh = style.get('rhythm', {})
    _put(p, 'caption_group_mean_s', rh.get('mean_caption_group_s'), 'style.json rhythm')
    if rh.get('caption_groups') and duration:
        _put(p, 'caption_groups_per_s', rh['caption_groups'] / duration, 'style.json rhythm')
    hook = style.get('hook', {})
    if hook.get('first_text_frame') is not None and _fps(form.get('fps')):
        _put(p, 'first_caption_s', hook['first_text_frame'] / float(_fps(form['fps'])), 'style.json hook')
    trans = rh.get('transitions') or []
    if duration and trans:
        _put(p, 'transitions_per_s', len(trans) / duration, 'style.json rhythm.transitions')
        types = sorted({k for tr in trans for k in classify(str(tr.get('type', '')), TRANSITION_KEYWORDS)})
        _put(p, 'transition_types', types, 'style.json rhythm.transitions')
    cams = style.get('camera') or []
    if cams:
        _put(p, 'camera_families', sorted({k for c in cams for k in classify(str(c), CAMERA_KEYWORDS)}), 'style.json camera')
    pal = style.get('palette') or []
    if pal:
        _put(p, 'palette', [(c['hex'], float(c.get('share', 1))) for c in pal if c.get('hex')], 'style.json palette')
    audio = style.get('audio', {})
    _put(p, 'integrated_lufs', audio.get('lufs'), 'style.json audio')
    _put(p, 'true_peak_dbtp', audio.get('true_peak_dbtp'), 'style.json audio')
    m = re.search(r'(\d+(?:\.\d+)?)\s*kelime', str(audio.get('voice', '')))
    if m:
        _put(p, 'wpm_span', float(m.group(1)), 'style.json audio.voice (whole video)')
    # Fill pace/language from the sibling analysis folder when style.json was written next to one.
    for folder in (base_dir / 'analysis', base_dir):
        pace = speech_pace(_maybe(folder / 'transcript.json'))
        if pace:
            p['_language'] = pace['language']
            _put(p, 'wpm_span', pace['wpm_span'], f'{folder.name}/transcript.json speaking span')
            _put(p, 'syllables_per_s', pace['syllables_per_s'], f'{folder.name}/transcript.json speaking span')
            _put(p, 'max_pause_s', pace['max_pause_s'], f'{folder.name}/transcript.json word gaps')
            break
    p['_beats'] = [b for b in (style.get('beats') or []) if isinstance(b, dict) and _num(b.get('start_s')) and _num(b.get('end_s'))]
    sibling = base_dir / 'analysis'
    if (sibling / 'analysis.json').is_file():
        auto = profile_from_analysis(sibling, cache_dir, measure)
        for key in LIKE_FOR_LIKE:
            if key in auto:
                hand = p.get(key)
                p[key] = dict(auto[key])
                if hand is not None:
                    p[key]['source'] += f' [aynı otomatik ölçüm; style.json elle: {fmt(hand["value"], key)}]'
        if '_transition_times' in auto and 'transitions_per_s' in auto:
            p['_transition_times'] = auto['_transition_times']
        for key, value in auto.items():
            if key.startswith('comp_') or key in ('_comp_samples', '_comp_duration', '_comp_flags', '_video', '_job'):
                p[key] = value
        p['_notes'] = p.get('_notes', []) + auto.get('_notes', [])
    return p


def _source_video(job, analysis):
    for key in ('source',):
        value = (analysis or {}).get(key)
        if value and Path(value).is_file():
            return Path(value)
    return None


def measure_loudness(video):
    from .media import FFMPEG
    proc = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(video), '-vn', '-af',
                           'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    found = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', proc.stderr.decode('utf-8', 'replace'), re.S)
    if not found:
        return None
    data = json.loads(found[-1])
    return float(data['input_i']), float(data['input_tp'])


def _transitions(job, analysis, cache_dir, measure):
    data = _maybe(job / 'transitions.json')
    if data is not None:
        return data.get('transitions', data if isinstance(data, list) else []), 'transitions.json'
    if not measure or cache_dir is None:
        return None, None
    cache = Path(cache_dir) / f'transitions-{job.parent.name}-{job.name}.json'
    cached = _maybe(cache)
    if cached is not None:
        return cached.get('transitions', []), cache.name + ' (stylecheck run)'
    video = _source_video(job, analysis)
    if video is None:
        return None, None
    try:  # analyser module may be absent or changing; this is a best-effort measurement
        from . import transitions as tr_mod
        fps = float(_fps(analysis['video']['fps']))
        target = video
        if tr_mod.needs_proxy(analysis['video']):
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            folder = Path(cache_dir) / f'proxy-{job.parent.name}-{job.name}'
            folder.mkdir(parents=True, exist_ok=True)
            target, _ = tr_mod.make_proxy(video, analysis['video'], folder)
        _, _, report = tr_mod.analyze_transitions(str(target), fps)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
        return report.get('transitions', []), cache.name + ' (stylecheck run)'
    except Exception as exc:  # noqa: BLE001 - report, do not crash the style check
        return None, f'transition detection failed: {exc}'


FAST_MOVES = {'whip', 'zoom_burst'}


def merge_fast_moves(transitions, gap=0.15):
    """One fast camera move is often reported as 2-3 adjacent whip/zoom_burst fragments; count it once."""
    out = []
    for t in sorted(transitions, key=lambda r: float(r.get('start', 0))):
        prev = out[-1] if out else None
        if (prev and prev.get('type') in FAST_MOVES and t.get('type') in FAST_MOVES
                and float(t.get('start', 0)) - float(prev.get('end', prev.get('start', 0))) <= gap):
            prev['end'] = max(float(prev.get('end', 0)), float(t.get('end', 0)))
            prev['merged'] = prev.get('merged', 1) + 1
            continue
        out.append(dict(t))
    return out


def profile_from_analysis(job, cache_dir=None, measure=True):
    job = Path(job)
    p = {'_kind': 'analysis'}
    analysis = _maybe(job / 'analysis.json') or {}
    video = analysis.get('video', {})
    duration = video.get('duration')
    if video.get('width') and video.get('height'):
        _put(p, 'aspect', video['width'] / video['height'], 'analysis.json video')
    _put(p, 'fps', str(video['fps']) if video.get('fps') else None, 'analysis.json video')
    _put(p, 'duration_s', duration, 'analysis.json video')
    ocr = _maybe(job / 'onscreen_text.json') or {}
    records = [r for r in ocr.get('records', []) if r.get('kind', 'caption') == 'caption']
    style = ocr.get('caption_style_summary') or {}
    if records:
        def med(key):
            vals = [r['style'][key] for r in records if _num((r.get('style') or {}).get(key))]
            return statistics.median(vals) if vals else None
        _put(p, 'caption_baseline_y_ratio', style.get('baseline_y_ratio') or med('baseline_y_ratio'), 'onscreen_text.json')
        _put(p, 'caption_size_ratio', style.get('font_size_ratio') or med('font_size_ratio'), 'onscreen_text.json')
        _put(p, 'caption_fill_hex', style.get('fill_hex'), 'onscreen_text.json')
        if 'shadow' in style:
            _put(p, 'caption_shadow', bool(style['shadow']), 'onscreen_text.json')
        if 'stroke_hex' in style:
            _put(p, 'caption_stroke', bool(style.get('stroke_hex')), 'onscreen_text.json (OCR stroke detector)')
        _put(p, 'caption_animation', style.get('dominant_animation'), 'onscreen_text.json')
        wpg = [len((r.get('style') or {}).get('words') or r.get('text', '').split()) for r in records]
        _put(p, 'caption_words_per_group', [min(wpg), max(wpg)], 'onscreen_text.json')
        durations = [r['end'] - r['start'] for r in records]
        _put(p, 'caption_group_mean_s', statistics.mean(durations), 'onscreen_text.json')
        if duration:
            _put(p, 'caption_groups_per_s', len(records) / duration, 'onscreen_text.json')
        _put(p, 'first_caption_s', min(r['start'] for r in records), 'onscreen_text.json')
        p['_caption_texts'] = [r.get('text', '') for r in records]
    transitions, tsource = _transitions(job, analysis, cache_dir, measure)
    if transitions is not None and duration:
        transitions = merge_fast_moves(transitions)
        tsource = f'{tsource} (bitişik whip/zoom_burst parçaları tek sayıldı)'
        p['_transition_times'] = sorted(float(t.get('start', 0)) for t in transitions)
        _put(p, 'transitions_per_s', len(transitions) / duration, tsource)
        _put(p, 'transition_types', sorted({t['type'] for t in transitions if t.get('type')}), tsource)
    elif tsource:
        p['_notes'] = p.get('_notes', []) + [tsource]
    vis = _maybe(job / 'visual_analysis.json') or {}
    segs = vis.get('camera_segments') or []
    if segs:
        fams = {CAMERA_FAMILY.get(s.get('type'), CAMERA_FAMILY.get(s.get('family'))) for s in segs
                if s.get('confidence', 1) >= 0.2}
        _put(p, 'camera_families', sorted(f for f in fams if f), 'visual_analysis.json camera_segments (confidence >= 0.2)')
    elif vis.get('motion'):
        fams = {CAMERA_FAMILY.get(m.get('camera_estimate')) for m in vis['motion']}
        _put(p, 'camera_families', sorted(f for f in fams if f), 'visual_analysis.json motion')
    colours = {}
    for pal in vis.get('palettes', []):
        weight = max(0.0, (pal.get('end', 1) - pal.get('start', 0)))
        for c in pal.get('colors', []):
            colours[c['hex']] = colours.get(c['hex'], 0.0) + c.get('ratio', 0) * (weight or 1)
    if colours:
        _put(p, 'palette', sorted(colours.items(), key=lambda kv: -kv[1]), 'visual_analysis.json palettes')
    audio = _maybe(job / 'audio_analysis.json') or {}
    lufs, tp = audio.get('integrated_lufs'), audio.get('true_peak_dbtp')
    src = 'audio_analysis.json'
    if not _num(lufs) and measure:
        vid = _source_video(job, analysis)
        got = measure_loudness(vid) if vid else None
        if got:
            (lufs, tp), src = got, 'ffmpeg loudnorm (stylecheck run)'
    _put(p, 'integrated_lufs', lufs if _num(lufs) else None, src)
    _put(p, 'true_peak_dbtp', tp if _num(tp) else None, src)
    _composition_profile(p, job, analysis, cache_dir, measure)
    pace = speech_pace(_maybe(job / 'transcript.json'))
    if pace:
        p['_language'] = pace['language']
        _put(p, 'wpm_span', pace['wpm_span'], 'transcript.json speaking span')
        _put(p, 'syllables_per_s', pace['syllables_per_s'], 'transcript.json speaking span')
        _put(p, 'max_pause_s', pace['max_pause_s'], 'transcript.json word gaps')
    return p


# ----------------------------------------------------------------------------- composition

def _comp_limits(th):
    return {'flat_fill_ratio': th['comp_flat_fill_max'], 'edge_contact': th['comp_edge_contact'],
            'edge_area': th['comp_edge_area'], 'min_flag_run': th['comp_flag_min_samples']}


def comp_metrics(samples, duration, th=None):
    """Metric dict from composition samples (also used for a reference window)."""
    from . import composition as cm
    th = th or THRESHOLDS
    limits = dict(cm.LIMITS, **_comp_limits(th))
    stats, flags, _, _ = cm.summarize(samples, duration, [], limits)
    out = {'comp_shot_type_share': stats['shot_type_share'],
           'comp_subject_area_median': (stats['subject_area'] or {}).get('median'),
           'comp_subject_area_iqr': (stats['subject_area'] or {}).get('iqr'),
           'comp_horizon_y': (stats['horizon_y'] or {}).get('median') if stats['horizon_detected_share'] >= 0.5 else None,
           'comp_centered_share': stats['centered_share'],
           'comp_thirds_distance': (stats['thirds_distance'] or {}).get('median'),
           'comp_flat_fill_events': len(flags['flat_fill']), 'comp_edge_cut_events': len(flags['edge_cut'])}
    return out, flags


def _job_video(job, analysis):
    for cand in (Path(job) / 'proxy-540p.mp4', Path((analysis or {}).get('source') or '')):
        if cand and cand.is_file():
            return cand
    return None


def _composition_profile(p, job, analysis, cache_dir, measure):
    from . import composition as cm
    comp = cm.load_composition(job)
    src = 'composition.json'
    if comp is None and measure and cache_dir is not None:
        cache = Path(cache_dir) / f'composition-{job.parent.name}-{job.name}.json'
        comp = _maybe(cache)
        if not (comp and comp.get('samples')):
            try:
                Path(cache_dir).mkdir(parents=True, exist_ok=True)
                comp = cm.analyze_composition(job, out=cache)
            except Exception as exc:  # noqa: BLE001 - best effort, report
                p['_notes'] = p.get('_notes', []) + [f'kompozisyon ölçülemedi: {exc}']
                comp = None
        src = cache.name + ' (stylecheck run)'
    if not comp or not comp.get('samples'):
        return
    samples = comp['samples']
    duration = comp.get('duration') or (samples[-1]['t'] + 0.2)
    metrics, flags = comp_metrics(samples, duration)
    for key, value in metrics.items():
        _put(p, key, value, f'{src} ({len(samples)} örnek, ~{comp.get("sample_fps", 3):g} fps tahmini)')
    p['_comp_samples'] = samples
    p['_comp_duration'] = duration
    p['_comp_flags'] = flags
    p['_video'] = str(_job_video(job, analysis) or comp.get('video') or '')
    p['_job'] = str(job)


def load_profile(path, cache_dir=None, measure=True):
    path = Path(path)
    if path.is_file() and path.suffix.lower() == '.json':
        return profile_from_style(_load(path), path.parent, cache_dir, measure), str(path)
    if path.is_dir() and (path / 'style.json').is_file() and not (path / 'analysis.json').is_file():
        return profile_from_style(_load(path / 'style.json'), path, cache_dir, measure), str(path / 'style.json')
    if path.is_dir() and (path / 'analysis.json').is_file():
        return profile_from_analysis(path, cache_dir, measure), str(path)
    raise FileNotFoundError(f'Not a style.json or social analyze folder: {path}')


# ----------------------------------------------------------------------------- comparison

METRICS = [
    # key, label, unit
    ('aspect', 'En/boy oranı', 'w/h'),
    ('fps', 'Kare hızı', 'fps'),
    ('caption_baseline_y_ratio', 'Altyazı taban çizgisi', 'y/H'),
    ('caption_size_ratio', 'Altyazı font boyu', 'px/H'),
    ('caption_fill_hex', 'Altyazı dolgu rengi', 'hex'),
    ('caption_stroke', 'Altyazı konturu', 'var/yok'),
    ('caption_shadow', 'Altyazı gölgesi', 'var/yok'),
    ('caption_animation', 'Altyazı animasyonu', 'tür'),
    ('caption_words_per_group', 'Grup başına kelime', 'min–maks'),
    ('caption_group_mean_s', 'Ortalama grup süresi', 's'),
    ('caption_groups_per_s', 'Altyazı değişimi', 'grup/s'),
    ('first_caption_s', 'İlk altyazı', 's'),
    ('transitions_per_s', 'Geçiş yoğunluğu', 'geçiş/s'),
    ('transition_types', 'Geçiş türleri', 'küme'),
    ('camera_families', 'Kamera hareketi türleri', 'küme'),
    ('palette', 'Palet', 'ΔE'),
    ('integrated_lufs', 'Entegre loudness', 'LUFS'),
    ('true_peak_dbtp', 'True peak', 'dBTP'),
    ('wpm_span', 'Konuşma hızı', 'kelime/dk'),
    ('syllables_per_s', 'Hece hızı', 'hece/s'),
    ('max_pause_s', 'En uzun konuşma boşluğu', 's'),
    ('comp_shot_type_share', 'Çekim tipi dağılımı (tahmin)', 'pay'),
    ('comp_subject_area_median', 'Özne alan oranı medyanı', 'alan/kare'),
    ('comp_subject_area_iqr', 'Özne alan oranı IQR', 'alan/kare'),
    ('comp_horizon_y', 'Ufuk çizgisi y oranı (tahmin)', 'y/H'),
    ('comp_centered_share', 'Özne ortada payı', 'pay'),
    ('comp_thirds_distance', 'Ağırlık merkezi – üçte bir noktası uzaklığı', 'norm.'),
    ('comp_flat_fill_events', 'Düz blok kadrajı doldurma olayı', 'adet'),
    ('comp_edge_cut_events', 'Özne kenar kesilmesi olayı', 'adet'),
]
COMP_EVENT_KEYS = ('comp_flat_fill_events', 'comp_edge_cut_events')
GATED_TRANSITIONS = {'flip', 'whip', 'zoom_burst', 'hard_cut', 'dissolve', 'wipe', 'fade'}


def _v(profile, key):
    row = profile.get(key)
    return None if row is None else row['value']


def _rel(a, b):
    return abs(b - a) / abs(a) if a else float('inf')


def compare_metric(key, ref, new, th, ref_profile, new_profile):
    """Return (diff, rule, status, note)."""
    if key in ('integrated_lufs', 'true_peak_dbtp'):
        if new is None:
            return None, '', 'SKIP', 'yeni videoda ölçüm yok'
        if key == 'integrated_lufs':
            lo, hi = th['lufs_range']
            note = 'teslim hedefi; referans miksi kopyalanmaz' if ref is not None and not (lo <= ref <= hi) else ''
            return (new - ref if ref is not None else None), f'{lo}…{hi} LUFS', 'PASS' if lo <= new <= hi else 'FAIL', note
        return (new - ref if ref is not None else None), f'≤ {th["true_peak_max"]} dBTP', 'PASS' if new <= th['true_peak_max'] else 'FAIL', ''
    if key in COMP_EVENT_KEYS:
        if new is None:
            return None, '', 'SKIP', 'yeni videoda kompozisyon ölçümü yok'
        limit = th['comp_flat_fill_events_max'] if key == 'comp_flat_fill_events' else th['comp_edge_cut_events_max']
        what = (f'tek renk blok ≥ {th["comp_flat_fill_max"]:.0%} kare' if key == 'comp_flat_fill_events'
                else f'özne kenar teması ≥ {th["comp_edge_contact"]:.0%} ve alan ≥ {th["comp_edge_area"]:.0%}')
        note = ('referansta da var (kasıtlı yakın plan olabilir); kareden doğrula' if ref and new else '')
        return (new - ref if ref is not None else None), f'≤ {limit} olay ({what})', 'PASS' if new <= limit else 'FAIL', note
    if ref is None or new is None:
        return None, '', 'SKIP', 'referansta ölçüm yok' if ref is None else 'yeni videoda ölçüm yok'
    if key == 'comp_shot_type_share':
        types = sorted(set(ref) | set(new))
        diffs = {t: new.get(t, 0.0) - ref.get(t, 0.0) for t in types}
        worst = max(diffs, key=lambda t: abs(diffs[t]))
        return diffs[worst], f'her türde |fark| ≤ {th["comp_shot_share_abs"]}', 'PASS' if abs(diffs[worst]) <= th['comp_shot_share_abs'] else 'FAIL', f'en büyük fark: {worst}'
    if key == 'comp_subject_area_median':
        d = new - ref
        return d, f'|fark| ≤ {th["comp_area_median_abs"]}', 'PASS' if abs(d) <= th['comp_area_median_abs'] else 'FAIL', ''
    if key == 'comp_horizon_y':
        d = new - ref
        # perspective grids and clouds make the horizon estimate noisy: shown against the tolerance, not gating
        return d, f'bilgi; |fark| ≤ {th["comp_horizon_abs"]} beklenir', 'INFO', ('tolerans dışı; ' if abs(d) > th['comp_horizon_abs'] else '') + 'ufuk tahmini gürültülü, kareden doğrula'
    if key == 'comp_centered_share':
        d = new - ref
        return d, f'|fark| ≤ {th["comp_centered_abs"]}', 'PASS' if abs(d) <= th['comp_centered_abs'] else 'FAIL', ''
    if key in ('comp_subject_area_iqr', 'comp_thirds_distance'):
        return new - ref, 'bilgi (kapı değil)', 'INFO', ''
    if key == 'aspect':
        d = new - ref
        return d, f'|fark| ≤ {th["aspect_abs"]}', 'PASS' if abs(d) <= th['aspect_abs'] else 'FAIL', ''
    if key == 'fps':
        a, b = _fps(ref), _fps(new)
        return None, 'aynı rasyonel değer', 'PASS' if a == b else 'FAIL', ''
    if key == 'caption_baseline_y_ratio':
        d = new - ref
        return d, f'|fark| ≤ {th["caption_baseline_abs"]}', 'PASS' if abs(d) <= th['caption_baseline_abs'] else 'FAIL', ''
    if key == 'caption_size_ratio':
        d = new - ref
        return d, f'±{th["caption_size_rel"]:.0%}', 'PASS' if _rel(ref, new) <= th['caption_size_rel'] else 'FAIL', ''
    if key == 'caption_fill_hex':
        d = delta_e(ref, new)
        return d, f'ΔE ≤ {th["caption_fill_delta_e"]}', 'PASS' if d <= th['caption_fill_delta_e'] else 'FAIL', ''
    if key in ('caption_stroke', 'caption_shadow', 'caption_animation'):
        same_method = ref_profile.get(key, {}).get('source', '').split()[0] == new_profile.get(key, {}).get('source', '').split()[0]
        if key == 'caption_stroke' and not same_method:
            # the OCR stroke detector misses thin (<~3 px) outlines that a hand measurement saw
            return None, 'aynı', 'INFO', 'farklı ölçüm yöntemleri (elle vs OCR); kareden gözle doğrula'
        return None, 'aynı', 'PASS' if ref == new else 'FAIL', ''
    if key == 'caption_words_per_group':
        ok = new[0] >= ref[0] and new[1] <= ref[1]
        return None, f'{ref[0]:g}…{ref[1]:g} aralığında', 'PASS' if ok else 'FAIL', ''
    if key == 'caption_group_mean_s':
        d = new - ref
        return d, f'±{th["caption_group_mean_rel"]:.0%}', 'PASS' if _rel(ref, new) <= th['caption_group_mean_rel'] else 'FAIL', ''
    if key == 'caption_groups_per_s':
        d = new - ref
        return d, f'±{th["caption_rate_rel"]:.0%}', 'PASS' if _rel(ref, new) <= th['caption_rate_rel'] else 'FAIL', ''
    if key == 'first_caption_s':
        d = new - ref
        return d, f'≤ ref + {th["first_caption_max_late_s"]} s', 'PASS' if d <= th['first_caption_max_late_s'] else 'FAIL', ''
    if key == 'transitions_per_s':
        d = new - ref
        return d, f'|fark| ≤ {th["transitions_per_s_abs"]}', 'PASS' if abs(d) <= th['transitions_per_s_abs'] else 'FAIL', ''
    if key == 'transition_types':
        need = {t for t in ref if t in GATED_TRANSITIONS}
        have = set(new)
        # whip and zoom_burst are the same family for style purposes (fast blurred in-shot move)
        fast = {'whip', 'zoom_burst'}
        missing = {t for t in need if t not in have and not (t in fast and have & fast)}
        extra = sorted(have - set(ref) - fast)
        note = ('eksik: ' + ', '.join(sorted(missing)) if missing else '') + (('; referansta yok: ' + ', '.join(extra)) if extra else '')
        return None, 'referanstaki türler mevcut', 'PASS' if not missing else 'FAIL', note.strip('; ')
    if key == 'camera_families':
        need = {f for f in ref if f in ('pull_back', 'push_in', 'static', 'lateral')}
        missing = need - set(new)
        return None, 'referanstaki aileler mevcut', 'PASS' if not missing else 'FAIL', ('eksik: ' + ', '.join(sorted(missing))) if missing else ''
    if key == 'palette':
        d = palette_distance(ref, new)
        return d, f'ağırlıklı ΔE ≤ {th["palette_delta_e"]}', 'PASS' if d is not None and d <= th['palette_delta_e'] else 'FAIL', ''
    if key == 'wpm_span':
        lr, ln = ref_profile.get('_language'), new_profile.get('_language')
        d = new - ref
        if lr and ln and lr != ln:
            return d, f'±{th["wpm_rel"]:.0%} (aynı dil)', 'INFO', f'diller farklı ({lr}/{ln}); hece hızına bak'
        return d, f'±{th["wpm_rel"]:.0%}', 'PASS' if _rel(ref, new) <= th['wpm_rel'] else 'FAIL', ''
    if key == 'syllables_per_s':
        d = new - ref
        lr, ln = ref_profile.get('_language'), new_profile.get('_language')
        if lr and ln and lr != ln:
            # languages have different natural syllable rates; this is shown, not gated
            return d, f'±{th["syllable_rate_rel"]:.0%} (aynı dil)', 'INFO', f'diller farklı ({lr}/{ln}); kulakla ve boşluk metriğiyle değerlendir'
        return d, f'±{th["syllable_rate_rel"]:.0%}', 'PASS' if _rel(ref, new) <= th['syllable_rate_rel'] else 'FAIL', ''
    if key == 'max_pause_s':
        d = new - ref
        return d, f'≤ ref + {th["max_pause_extra_s"]} s', 'PASS' if d <= th['max_pause_extra_s'] else 'FAIL', ''
    return None, '', 'INFO', ''


def fmt(value, key=None):
    if value is None:
        return '—'
    if key == 'palette':
        return ' '.join(h for h, _ in value[:4])
    if isinstance(value, bool):
        return 'var' if value else 'yok'
    if isinstance(value, dict):
        return ', '.join(f'{k} {v:.2f}' for k, v in value.items()) or '∅'
    if isinstance(value, (list, tuple)):
        if key == 'caption_words_per_group':
            return f'{value[0]:g}–{value[1]:g}'
        return ', '.join(str(v) for v in value) or '∅'
    if isinstance(value, float):
        return f'{value:.4f}' if abs(value) < 0.1 else f'{value:.3f}' if abs(value) < 10 else f'{value:.1f}'
    return str(value)


def windowed_reference(ref, cand):
    """An excerpt (e.g. a 10 s test of a 22 s format) is compared with the same opening window of the
    reference for time-density metrics; whole-video density would punish a dense opening."""
    ref_d, cand_d = _v(ref, 'duration_s'), _v(cand, 'duration_s')
    times = ref.get('_transition_times')
    if not (ref_d and cand_d) or cand_d >= 0.8 * ref_d:
        return ref
    out = dict(ref)
    if times:
        n = sum(t < cand_d for t in times)
        out['transitions_per_s'] = {'value': n / cand_d, 'source': ref['transitions_per_s']['source'],
                                    'window': f'referans = ilk {cand_d:.1f} s penceresi: {n / cand_d:.3f} geçiş/s (aday kesit)'}
    window = [s for s in ref.get('_comp_samples') or [] if s['t'] < cand_d]
    if len(window) >= 3:
        metrics, flags = comp_metrics(window, cand_d)
        for key, value in metrics.items():
            if value is not None and key in ref:
                out[key] = {'value': value, 'source': ref[key]['source'],
                            'window': f'referans = ilk {cand_d:.1f} s penceresi (aday kesit)'}
        out['_comp_flags'] = flags
    return out


def rethreshold_composition(prof, th):
    """Recompute composition rows/flags with the active (possibly overridden) thresholds."""
    if not prof.get('_comp_samples'):
        return
    metrics, flags = comp_metrics(prof['_comp_samples'], prof['_comp_duration'], th)
    for key, value in metrics.items():
        if key in prof and value is not None:
            prof[key]['value'] = value
        elif key in prof:
            del prof[key]
    prof['_comp_flags'] = flags


def composition_warnings(prof, name):
    """Timestamped warning list for one video, e.g. 'v1 0.0–0.9 s flat_fill 0.48'."""
    out = []
    flags = prof.get('_comp_flags') or {}
    for ev in flags.get('flat_fill', []):
        out.append({'video': name, 'kind': 'flat_fill', 't_start': ev['t_start'], 't_end': ev['t_end'], 'value': ev['peak'],
                    'text': f'{name} {ev["t_start"]:.1f}–{ev["t_end"]:.1f} s flat_fill {ev["peak"]:.2f}'})
    for ev in flags.get('edge_cut', []):
        out.append({'video': name, 'kind': 'edge_cut', 't_start': ev['t_start'], 't_end': ev['t_end'], 'value': ev['peak'],
                    'side': ev.get('side'), 'subject_area': ev.get('subject_area'),
                    'text': f'{name} {ev["t_start"]:.1f}–{ev["t_end"]:.1f} s edge_cut {ev.get("side", "")} {ev["peak"]:.2f}'
                            f' (özne alanı {ev.get("subject_area", 0):.2f})'})
    return sorted(out, key=lambda w: w['t_start'])


# ----------------------------------------------------------------------------- same-moment pairs

def pair_moments(ref, cand_d, n_max):
    """(role, t_ref, t_cand) moments.  Style.json beats if present (beat mid-points + the hook frame), else
    evenly spaced relative positions.  A candidate that is a short excerpt (< 80 % of the reference) is
    compared at the same absolute time, otherwise at the same relative position."""
    ref_d = _v(ref, 'duration_s') or ref.get('_comp_duration') or cand_d
    excerpt = cand_d < 0.8 * ref_d
    moments = [('hook', 0.3)]
    for b in ref.get('_beats') or []:
        moments.append((str(b.get('role', 'beat')), (b['start_s'] + b['end_s']) / 2))
    if len(moments) == 1:
        n = max(3, min(n_max, 6))
        moments += [(f'{round(100 * (i + .5) / n)}%', ref_d * (i + .5) / n) for i in range(n)]
    out = []
    for role, t in moments:
        if excerpt:
            if t >= cand_d - 0.1:
                continue
            tc = t
        else:
            tc = t / ref_d * cand_d
        out.append((role, round(t, 2), round(min(tc, cand_d - 0.05), 2)))
    return out[:n_max]


def _annotate(img, rec, label):
    import cv2
    h, w = img.shape[:2]
    out = img.copy()
    if rec.get('subject_bbox'):
        x, y, bw, bh = rec['subject_bbox']
        cv2.rectangle(out, (int(x * w), int(y * h)), (int((x + bw) * w), int((y + bh) * h)), (0, 0, 255), 2)
    if rec.get('horizon_y') is not None:
        cv2.line(out, (0, int(rec['horizon_y'] * h)), (w, int(rec['horizon_y'] * h)), (0, 255, 0), 1)
    if rec.get('centroid'):
        cv2.circle(out, (int(rec['centroid'][0] * w), int(rec['centroid'][1] * h)), 5, (255, 0, 255), -1)
    cv2.rectangle(out, (0, 0), (w, 22), (0, 0, 0), -1)
    cv2.putText(out, label, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return out


COMP_PAIR_FIELDS = ('shot_type', 'subject_area', 'flat_fill_ratio', 'horizon_y', 'blob_count')


def build_pairs(ref, cand, out, cand_name, th):
    """Frame pairs at matching moments + composition difference table (no pixel similarity)."""
    import cv2
    import numpy as np
    from . import composition as cm
    rv, cv_ = ref.get('_video'), cand.get('_video')
    if not (rv and cv_ and Path(rv).is_file() and Path(cv_).is_file()):
        return [], 'eşleşen anlar için video bulunamadı'
    cand_d = _v(cand, 'duration_s') or cand.get('_comp_duration')
    pairs_dir = Path(out) / 'pairs'
    pairs_dir.mkdir(parents=True, exist_ok=True)
    limits = dict(cm.LIMITS, **_comp_limits(th))
    rows = []
    for i, (role, tr, tc) in enumerate(pair_moments(ref, cand_d, th['comp_pair_max']), 1):
        a, b = cm.frame_at(rv, tr, 360), cm.frame_at(cv_, tc, 360)
        if a is None or b is None:
            continue
        ra, rb = cm.measure_frame(cv2.resize(a, (cm.WORK_WIDTH, round(a.shape[0] * cm.WORK_WIDTH / a.shape[1]))), limits), \
            cm.measure_frame(cv2.resize(b, (cm.WORK_WIDTH, round(b.shape[0] * cm.WORK_WIDTH / b.shape[1]))), limits)
        height = 640
        fit = lambda im: cv2.resize(im, (round(im.shape[1] * height / im.shape[0]), height))
        left = _annotate(fit(a), ra, f'REF {tr:.2f}s {role}')
        right = _annotate(fit(b), rb, f'{cand_name} {tc:.2f}s {ra["shot_type"]}->{rb["shot_type"]}')
        safe = re.sub(r'[^0-9A-Za-z]+', '-', role).strip('-') or 'beat'
        name = f'{cand_name}-{i:02d}-{safe}.jpg'
        cv2.imwrite(str(pairs_dir / name), np.hstack([left, np.full((height, 8, 3), 255, np.uint8), right]),
                    [cv2.IMWRITE_JPEG_QUALITY, 90])
        rows.append({'role': role, 't_ref': tr, 't_cand': tc, 'image': f'pairs/{name}',
                     'ref': {k: ra.get(k) for k in COMP_PAIR_FIELDS + ('centroid', 'edge_cut')},
                     'cand': {k: rb.get(k) for k in COMP_PAIR_FIELDS + ('centroid', 'edge_cut')},
                     'diff': {'subject_area': round(rb['subject_area'] - ra['subject_area'], 3),
                              'flat_fill_ratio': round(rb['flat_fill_ratio'] - ra['flat_fill_ratio'], 3),
                              'centroid_x': (round(rb['centroid'][0] - ra['centroid'][0], 3) if ra.get('centroid') and rb.get('centroid') else None),
                              'centroid_y': (round(rb['centroid'][1] - ra['centroid'][1], 3) if ra.get('centroid') and rb.get('centroid') else None),
                              'horizon_y': (round(rb['horizon_y'] - ra['horizon_y'], 3) if ra.get('horizon_y') is not None and rb.get('horizon_y') is not None else None),
                              'shot_type': 'aynı' if ra['shot_type'] == rb['shot_type'] else f'{ra["shot_type"]} -> {rb["shot_type"]}'}})
    return rows, None


def build_report(ref_path, cand_paths, out=None, thresholds=None, measure=True):
    th = dict(THRESHOLDS, **(thresholds or {}))
    cache = Path(out) if out else None
    ref, ref_label = load_profile(ref_path, cache, measure)
    rethreshold_composition(ref, th)
    candidates = []
    for c in cand_paths:
        prof, label = load_profile(c, cache, measure)
        rethreshold_composition(prof, th)
        ref_c = windowed_reference(ref, prof)
        rows = []
        for key, name, unit in METRICS:
            r, n = _v(ref_c, key), _v(prof, key)
            diff, rule, status, note = compare_metric(key, r, n, th, ref_c, prof)
            if (ref_c.get(key) or {}).get('window'):
                note = (note + '; ' if note else '') + ref_c[key]['window']
            rows.append({'metric': key, 'label': name, 'unit': unit, 'reference': r, 'candidate': n, 'diff': diff,
                         'rule': rule, 'status': status, 'note': note,
                         'reference_source': (ref_c.get(key) or {}).get('source'), 'candidate_source': (prof.get(key) or {}).get('source')})
        counts = {s: sum(r['status'] == s for r in rows) for s in ('PASS', 'FAIL', 'INFO', 'SKIP')}
        name = Path(label).name
        pairs, pair_note = [], None
        if measure and cache is not None and ref.get('_comp_samples') and prof.get('_comp_samples'):
            try:
                pairs, pair_note = build_pairs(ref, prof, cache, name, th)
            except Exception as exc:  # noqa: BLE001 - pairs are a visual aid; never lose the report
                pair_note = f'eşleşen kare çiftleri üretilemedi: {exc}'
        candidates.append({'path': label, 'language': prof.get('_language'), 'rows': rows, 'counts': counts,
                           'verdict': 'FAIL' if counts['FAIL'] else 'PASS', 'notes': prof.get('_notes', []),
                           'composition_warnings': composition_warnings(prof, name),
                           'reference_composition_warnings': composition_warnings(ref_c, 'REF'),
                           'pairs': pairs, 'pairs_note': pair_note})
    report = {'schema': 'social-studio.stylecheck.v1', 'reference': ref_label, 'reference_language': ref.get('_language'),
              'thresholds': th, 'candidates': candidates,
              'note': ('Metrik bazında kurallar; genel benzerlik yüzdesi yoktur. INFO satırları kapı değildir. '
                       'Kareleri gözle incelemenin yerini tutmaz.')}
    return report


def comp_markdown(i, c):
    out = ['', f'## Kompozisyon – Aday {i}', '',
           'Tahmin: özne maskesi (satır arka plan rengi + spektral artık), düz blok, kenar teması, ufuk; güven 0.35–0.75. '
           'Her uyarıyı kareden doğrula.', '']
    warns = c.get('composition_warnings') or []
    out.append('Uyarılar (aday): ' + ('yok' if not warns else ''))
    out += [f'- {w["text"]}' for w in warns]
    refw = c.get('reference_composition_warnings') or []
    if refw:
        out.append('Referansta aynı pencerede: ' + '; '.join(w['text'] for w in refw))
    pairs = c.get('pairs') or []
    if pairs:
        out += ['', 'Aynı-an karşılaştırması (görseller `pairs/` altında; fark = aday − referans):', '',
                '| An (rol) | t ref / aday | Çekim tipi | Özne alanı ref → aday | Merkez Δx / Δy | Düz blok Δ | Ufuk Δ | Görsel |',
                '|---|---|---|---|---|---|---|---|']
        for p in pairs:
            d = p['diff']
            f = lambda v: '—' if v is None else f'{v:+.2f}'
            out.append(f'| {p["role"]} | {p["t_ref"]:.2f} / {p["t_cand"]:.2f} | {d["shot_type"]} | '
                       f'{p["ref"]["subject_area"]:.2f} → {p["cand"]["subject_area"]:.2f} | {f(d["centroid_x"])} / {f(d["centroid_y"])} | '
                       f'{f(d["flat_fill_ratio"])} | {f(d["horizon_y"])} | {p["image"]} |')
    elif c.get('pairs_note'):
        out.append(f'Eşleşen kare çiftleri: {c["pairs_note"]}')
    return out


def to_markdown(report):
    lines = ['# Stil uyum raporu', '', f'Referans: `{report["reference"]}`', '']
    cands = report['candidates']
    for i, c in enumerate(cands, 1):
        lines.append(f'- Aday {i}: `{c["path"]}` → **{c["verdict"]}** '
                     f'({c["counts"]["PASS"]} geçti, {c["counts"]["FAIL"]} kaldı, {c["counts"]["INFO"]} bilgi, {c["counts"]["SKIP"]} atlandı)')
    lines += ['', '| Metrik | Kural | Referans | ' + ' | '.join(f'Aday {i} | Fark {i} | Durum {i}' for i in range(1, len(cands) + 1)) + ' |',
              '|---|---|---|' + '---|---|---|' * len(cands)]
    for idx, (key, name, unit) in enumerate(METRICS):
        first = cands[0]['rows'][idx]
        cells = [f'{name} ({unit})', first['rule'] or '—', fmt(first['reference'], key)]
        for c in cands:
            r = c['rows'][idx]
            status = r['status'] + (f' – {r["note"]}' if r['note'] else '')
            cells += [fmt(r['candidate'], key), fmt(r['diff']), status]
        lines.append('| ' + ' | '.join(cells) + ' |')
    for i, c in enumerate(cands, 1):
        lines += comp_markdown(i, c)
    lines += ['', 'Eşikler (değiştirmek için `--thresholds dosya.json`):', '', '```json',
              json.dumps(report['thresholds'], ensure_ascii=False, indent=1), '```', '', report['note']]
    for i, c in enumerate(cands, 1):
        for n in c['notes']:
            lines.append(f'- Aday {i} notu: {n}')
    return '\n'.join(lines) + '\n'


def stylecheck(reference, candidates, out=None, thresholds_file=None, measure=True):
    thresholds = _load(thresholds_file) if thresholds_file else None
    report = build_report(reference, candidates, out, thresholds, measure)
    md = to_markdown(report)
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / 'stylecheck.json').write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
        (out / 'STYLECHECK.md').write_text(md, encoding='utf-8')
    try:
        print(md)
    except UnicodeEncodeError:  # legacy Windows console code pages
        print(md.encode(sys.stdout.encoding or 'ascii', 'replace').decode(sys.stdout.encoding or 'ascii'))
    return report


def stylecheck_cli(args):
    report = stylecheck(args.reference, args.candidates, args.out, args.thresholds, not args.no_measure)
    if args.strict and any(c['verdict'] == 'FAIL' for c in report['candidates']):
        raise SystemExit(1)
