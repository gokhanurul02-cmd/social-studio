# Kullanicinin METIN v2 kaydi (Orcun Togan, ses/kullanici-v2/kayit.mp3) -> project-v2metin anlati sesi.
#   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\v2metin_ses_hazirla.py
# Kayit HIZLANDIRILMAZ / KESILMEZ: yalniz iki gecisli loudnorm (linear) -> -14 LUFS / -1.5 dBTP, mono 48 kHz.
# faster-whisper (large-v3-turbo, yerel) kelime zamanlari -> METIN-v2.md'nin 101 kelimesine difflib ile hizalanir
# (rakamlar "100"/"300" -> "yuz"/"uc yuz" acilir; eslesmeyenler komsulardan enterpole edilir).
# Cikti: ses/kullanici-v2/{ses.wav, kelimeler.json, whisper.json}; project-v2metin/voice.json bu kayda isaret eder.
import json, re, subprocess, difflib
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
SRC = JOB / 'ses' / 'kullanici-v2' / 'kayit.mp3'
OUT = JOB / 'ses' / 'kullanici-v2'
PROJ = JOB / 'project-v2metin'
NUM = {'100': ['yüz'], '300': ['üç', 'yüz']}


def norm(s):
    s = s.lower().replace('i̇', 'i').replace('İ', 'i')
    return re.sub(r"[^a-zçğıöşü0-9]", '', s)


def metin_words():
    rows = []
    for line in (JOB / 'METIN-v2.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|', line)
        if m:
            c = int(m.group(1))
            for tok in m.group(2).split():
                w = re.sub(r'[.,;:!?…"“”]+$', '', tok)
                if w: rows.append({'w': w, 'c': c})
    return rows


def main():
    wav = OUT / 'ses.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(SRC), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(SRC), '-af', af, '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], check=True)
    print('kaynak', m['input_i'], 'LUFS', m['input_tp'], 'dBTP ->', wav)

    from faster_whisper import WhisperModel
    model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
    segs, _ = model.transcribe(str(wav), language='tr', word_timestamps=True, vad_filter=False, beam_size=5)
    raw = [{'w': w.word.strip(), 's': w.start, 'e': w.end} for s in segs for w in (s.words or [])]
    (OUT / 'whisper.json').write_text(json.dumps(raw, ensure_ascii=False, indent=0), encoding='utf-8')
    rec = []
    for x in raw:
        k = norm(x['w'])
        if k in NUM:
            parts = NUM[k]; d = (x['e'] - x['s']) / len(parts)
            for i, p in enumerate(parts): rec.append({'w': p, 's': x['s'] + i * d, 'e': x['s'] + (i + 1) * d})
        else: rec.append(x)
    ref = metin_words()
    a, b = [norm(r['w']) for r in ref], [norm(r['w']) for r in rec]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(ref)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = (rec[blk.b + k]['s'], rec[blk.b + k]['e'])
    miss = [ref[i]['w'] for i in range(len(ref)) if times[i] is None]
    i = 0
    while i < len(ref):
        if times[i] is None:
            j = i
            while j < len(ref) and times[j] is None: j += 1
            t0 = times[i - 1][1] if i > 0 else 0.0
            t1 = times[j][0] if j < len(ref) else rec[-1]['e']
            n = j - i
            for k in range(n): times[i + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n)
            i = j
        else: i += 1
    words = [{'w': r['w'], 's': round(t[0], 3), 'e': round(t[1], 3), 'c': r['c']} for r, t in zip(ref, times)]
    (OUT / 'kelimeler.json').write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding='utf-8')
    matched = len(ref) - len(miss)
    print(f'{len(ref)} METIN kelimesi, {len(rec)} taninan, {matched} eslesti; eslesmeyen: {miss}; son kelime {words[-1]["e"]:.2f} s')
    print('whisper:', ' '.join(x['w'] for x in raw))
    (PROJ / 'voice.json').write_text(json.dumps({
        'words': 'ses/kullanici-v2/kelimeler.json', 'audio': 'ses/kullanici-v2/ses.wav', 'mix': 'ses/kullanici-v2/miks.wav',
        'source': 'ses/kullanici-v2/kayit.mp3 (kullanicinin kendi kaydi, Orcun Togan; METIN-v2.md, onizleme-v1 sahneleri)',
        'note': 'audio = normalize yalin anlati; mix = anlati + SFX (scripts/sfx_miks_v2metin.py) -> render/video.cjs muxlar',
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    for c in range(1, 11):
        ws = [w for w in words if w['c'] == c]
        print(c, f"{ws[0]['s']:.2f}-{ws[-1]['e']:.2f}", ' '.join(w['w'] for w in ws))


if __name__ == '__main__':
    main()
