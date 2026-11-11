# ElevenLabs kaydi gelince TEK ADIM:
#   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\elevenlabs_hazirla.py <kayit.mp3|wav> [--render]
# Yaptiklari:
#   1) kaydi -14 LUFS / -1.5 dBTP mono 48 kHz wav'a cevirir -> ses/elevenlabs/ses.wav
#   2) faster-whisper (large-v3-turbo, yerel onbellek) ile kelime zamanlarini cikarir
#   3) taninan kelimeleri METIN.md'deki 10 cumlenin kelimelerine hizalar (difflib), eslesmeyenleri
#      komsularindan enterpole eder -> ses/elevenlabs/kelimeler.json  ({w,s,e,c}, w = METIN'deki kelime)
#   4) project/voice.json'u bu iki dosyaya cevirir (butun sahne zamanlari shots.js'te an(c,w) ile yeniden hesaplanir)
#   5) --render: renders/onizleme-v2.mp4 (720p, ses muxlu) uretir
import json, re, subprocess, sys, difflib
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
OUT = JOB / 'ses' / 'elevenlabs'


def norm(s):
    s = s.lower().replace('i̇', 'i')
    return re.sub(r"[^a-zçğıöşü0-9]", '', s)


def metin_words():
    rows = []
    for line in (JOB / 'METIN.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|', line)
        if m:
            c = int(m.group(1))
            for tok in m.group(2).split():
                w = re.sub(r'[.,;:!?…"“”]+$', '', tok)
                if w: rows.append({'w': w, 'c': c})
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__ or 'usage: elevenlabs_hazirla.py <audio> [--render]'); sys.exit(1)
    src = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    wav = OUT / 'ses.wav'
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(src), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7', '-ar', '48000', '-ac', '1', str(wav)], check=True)

    from faster_whisper import WhisperModel
    model = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
    segs, _ = model.transcribe(str(wav), language='tr', word_timestamps=True, vad_filter=False, beam_size=5)
    rec = [{'w': w.word.strip(), 's': w.start, 'e': w.end} for s in segs for w in (s.words or [])]
    ref = metin_words()
    a, b = [norm(r['w']) for r in ref], [norm(r['w']) for r in rec]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(ref)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = (rec[blk.b + k]['s'], rec[blk.b + k]['e'])
    # unmatched METIN words: spread evenly between the neighbouring matched words
    i = 0
    while i < len(ref):
        if times[i] is None:
            j = i
            while j < len(ref) and times[j] is None: j += 1
            t0 = times[i - 1][1] if i > 0 else 0.0
            t1 = times[j][0] if j < len(ref) else (rec[-1]['e'] if rec else t0 + 0.4 * (j - i))
            n = j - i
            for k in range(n): times[i + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n)
            i = j
        else: i += 1
    words = [{'w': r['w'], 's': round(t[0], 3), 'e': round(t[1], 3), 'c': r['c']} for r, t in zip(ref, times)]
    (OUT / 'kelimeler.json').write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding='utf-8')
    matched = sum(1 for blk in sm.get_matching_blocks() for _ in range(blk.size))
    print(f'{len(ref)} METIN kelimesi, {len(rec)} taninan, {matched} eslesti; son kelime {words[-1]["e"]:.2f} s')
    vj = JOB / 'project' / 'voice.json'
    v = json.loads(vj.read_text(encoding='utf-8'))
    v.update({'words': 'ses/elevenlabs/kelimeler.json', 'audio': 'ses/elevenlabs/ses.wav'})
    vj.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf-8')
    print('voice.json ->', v['words'], v['audio'])
    if '--render' in sys.argv:
        subprocess.run(['node', 'render/video.cjs', '../renders/onizleme-v2.mp4', '720', '1280', '8'], cwd=JOB / 'project', check=True,
                       env={**__import__('os').environ, 'CRF': '21'})


if __name__ == '__main__':
    main()
