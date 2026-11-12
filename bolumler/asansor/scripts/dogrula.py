# Final dogrulama: MP4'un sesinden Whisper transkripti == kullanici kaydinin kelimeleri; ebur128 LUFS / TP.
#   .venv\Scripts\python.exe -X utf8 jobs\20261111-zdf-asansor\scripts\dogrula.py renders\v1-1080p.mp4
import json, re, subprocess, sys, difflib
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
mp4 = JOB / sys.argv[1]
wav = JOB / 'inspect' / 'dogrula.wav'
subprocess.run([FF, '-y', '-v', 'error', '-i', str(mp4), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
norm = lambda w: re.sub(r'[^\wçğıöşü]', '', w.lower().replace('İ', 'i').replace('I', 'ı'))
from faster_whisper import WhisperModel
model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
segs, _ = model.transcribe(str(wav), language='tr', word_timestamps=True, vad_filter=False, beam_size=5)
rec = [{'w': w.word.strip(), 's': round(w.start, 2), 'e': round(w.end, 2)} for s in segs for w in (s.words or [])]
ref = json.loads((JOB / 'ses' / 'kullanici' / 'kelimeler.json').read_text(encoding='utf-8'))
a, b = [norm(r['w']) for r in ref], [norm(r['w']) for r in rec]
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
match = sum(bl.size for bl in sm.get_matching_blocks())
diffs = [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
# timing drift of matched words
dts = []
for bl in sm.get_matching_blocks():
    for k in range(bl.size): dts.append(abs(ref[bl.a + k]['s'] - rec[bl.b + k]['s']))
r = subprocess.run([FF, '-hide_banner', '-nostats', '-i', str(mp4), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace')
tail = r.stderr[r.stderr.rindex('Summary:'):]
I = re.search(r'I:\s+(-?[\d.]+) LUFS', tail).group(1); TP = re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail).group(1)
res = {'kayit_kelime': len(a), 'transkript_kelime': len(b), 'eslesen': match, 'farklar': diffs,
       'zaman_sapmasi_ort_s': round(sum(dts) / max(1, len(dts)), 3), 'zaman_sapmasi_max_s': round(max(dts or [0]), 3),
       'LUFS': float(I), 'TP_dBTP': float(TP), 'transkript': ' '.join(x['w'] for x in rec)}
(JOB / 'inspect' / 'dogrula.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(res, ensure_ascii=False, indent=1))
