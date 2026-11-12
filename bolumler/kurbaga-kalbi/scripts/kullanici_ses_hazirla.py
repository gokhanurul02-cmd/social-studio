# Kullanicinin kendi ElevenLabs kaydi (Orcun Togan) -> projenin anlati sesi.
#   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-kurbaga-kalbi\scripts\kullanici_ses_hazirla.py
# Kayit HIZLANDIRILMAZ / KESILMEZ: yalniz iki gecisli loudnorm (linear) ile -14 LUFS / -1.5 dBTP, mono 48 kHz.
# Kelime zamanlari ses/kelimeler-whisper.json (bu kaydin Whisper zamanlari) -> cumle indeksi (c, METIN.md v4, 9 satir).
import json, subprocess
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
SRC = JOB / 'ses' / 'kullanici-orcun.mp3'
OUT = JOB / 'ses' / 'kullanici'
COUNTS = [7, 10, 8, 8, 7, 5, 11, 11, 10]   # METIN.md v4 satir basina kelime (toplam 77)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wav = OUT / 'ses.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(SRC), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(SRC), '-af', af, '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], check=True)
    words = json.loads((JOB / 'ses' / 'kelimeler-whisper.json').read_text(encoding='utf-8'))
    assert len(words) == sum(COUNTS), (len(words), sum(COUNTS))
    out, i = [], 0
    for c, n in enumerate(COUNTS, 1):
        for _ in range(n):
            w = words[i]; out.append({'w': w['w'], 's': w['s'], 'e': w['e'], 'c': c}); i += 1
    (OUT / 'kelimeler.json').write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    (JOB / 'project' / 'voice.json').write_text(json.dumps({
        'words': 'ses/kullanici/kelimeler.json', 'audio': 'ses/kullanici/ses.wav', 'mix': 'ses/kullanici/miks.wav',
        'source': 'ses/kullanici-orcun.mp3 (kullanicinin kendi ElevenLabs kaydi, Orcun Togan; METIN.md v4)',
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('input', m['input_i'], 'LUFS', m['input_tp'], 'dBTP ->', wav)
    for c in range(1, len(COUNTS) + 1):
        ws = [w for w in out if w['c'] == c]
        print(c, f"{ws[0]['s']:.2f}-{ws[-1]['e']:.2f}", ' '.join(w['w'] for w in ws))


if __name__ == '__main__':
    main()
