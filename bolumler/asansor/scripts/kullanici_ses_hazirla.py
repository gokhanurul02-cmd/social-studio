# Kullanicinin kendi kaydi (Orcun Togan) -> projenin anlati sesi + kelime zamanlari.
#   .venv\Scripts\python.exe -X utf8 jobs\20261111-zdf-asansor\scripts\kullanici_ses_hazirla.py ses\kullanici-orcun.mp3
# Kayit HIZLANDIRILMAZ / KESILMEZ: yalniz iki gecisli loudnorm (linear) ile -14 LUFS / -1.5 dBTP, mono 48 kHz.
# Kelime zamanlari: faster-whisper (large-v3-turbo, yerel) kelime damgalari, METIN.md'nin 87 kelimesine difflib ile hizalanir
# (Whisper'in kacirdigi / farkli yazdigi kelimeler komsulardan enterpolasyonla doldurulur) -> cumle indeksi c (10 satir).
# Sonra project/voice.json gecici zamanlardan bu kayda cevrilir: shots.js'teki tum an(c,w) zamanlari otomatik kayar.
import json, re, subprocess, sys, difflib
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
SRC = JOB / (sys.argv[1] if len(sys.argv) > 1 else 'ses/kullanici-orcun.mp3')
OUT = JOB / 'ses' / 'kullanici'
sys.path.insert(0, str(Path(__file__).parent))
from gecici_zaman import CUMLELER   # METIN.md v1, 10 cumle (tek kaynak)

norm = lambda w: re.sub(r'[^\wçğıöşü]', '', w.replace('İ', 'i').replace('I', 'ı').lower())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wav = OUT / 'ses.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(SRC), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(SRC), '-af', af, '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], check=True)
    # whisper word timings (cached; delete the file to recompute)
    wj = JOB / 'ses' / 'kelimeler-whisper.json'
    if not wj.exists():
        from faster_whisper import WhisperModel
        model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
        segs, _ = model.transcribe(str(wav), language='tr', word_timestamps=True, vad_filter=False, beam_size=5,
                                   initial_prompt=' '.join(CUMLELER))
        rec = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in (s.words or [])]
        wj.write_text(json.dumps(rec, ensure_ascii=False, indent=0), encoding='utf-8')
    rec = json.loads(wj.read_text(encoding='utf-8'))
    ref = [(c, w) for c, s in enumerate(CUMLELER, 1) for w in s.split()]
    a, b = [norm(w) for _, w in ref], [norm(x['w']) for x in rec]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    T = [None] * len(ref)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal' or (op == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1): T[i1 + k] = (rec[j1 + k]['s'], rec[j1 + k]['e'])
    miss = [i for i, x in enumerate(T) if x is None]
    for i in miss:   # interpolate between known neighbours
        lo = next((j for j in range(i - 1, -1, -1) if T[j]), None); hi = next((j for j in range(i + 1, len(T)) if T[j]), None)
        t0 = T[lo][1] if lo is not None else 0.0; t1 = T[hi][0] if hi is not None else t0 + 0.4
        n = (hi if hi is not None else len(T)) - (lo if lo is not None else -1)
        k = i - (lo if lo is not None else -1); T[i] = (t0 + (t1 - t0) * (k - 1) / n, t0 + (t1 - t0) * k / n)
    out = [{'w': w, 's': round(T[i][0], 3), 'e': round(T[i][1], 3), 'c': c} for i, (c, w) in enumerate(ref)]
    (OUT / 'kelimeler.json').write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    (JOB / 'project' / 'voice.json').write_text(json.dumps({
        'words': 'ses/kullanici/kelimeler.json', 'audio': 'ses/kullanici/ses.wav', 'mix': 'ses/kullanici/miks.wav',
        'source': f'{SRC.relative_to(JOB).as_posix()} (kullanicinin kendi kaydi, Orcun Togan; METIN.md v1)',
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('input', m['input_i'], 'LUFS', m['input_tp'], 'dBTP ->', wav)
    print('whisper', len(rec), 'kelime; METIN', len(ref), '; enterpole edilen:', [ref[i][1] for i in miss] or 'yok')
    for c in range(1, len(CUMLELER) + 1):
        ws = [w for w in out if w['c'] == c]
        print(c, f"{ws[0]['s']:.2f}-{ws[-1]['e']:.2f}", ' '.join(w['w'] for w in ws))


if __name__ == '__main__':
    main()
