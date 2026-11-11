# Gecici seslendirme: METIN.md'deki 10 cumleyi Edge TTS (tr-TR-AhmetNeural, +15%) ile ayri ayri sentezler,
# her cumlenin basindaki/sonundaki sessizligi WordBoundary zamanlarindan kirpar, cumleler arasi bosluk = GAP,
# ses\gecici\ses.wav + ses\gecici\kelimeler.json ({w,s,e,c}) yazar.
# kullanim (social-studio kokunden): .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\gecici_ses.py
import asyncio, json, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
import edge_tts

JOB = Path(__file__).resolve().parents[1]
OUT = JOB / 'ses' / 'gecici'
FF = str(JOB.parents[1] / 'bin' / 'ffmpeg.exe')
VOICE, RATE, GAP, SR = 'tr-TR-AhmetNeural', '+15%', 0.06, 48000
PAD_IN, PAD_OUT = 0.03, 0.06


def sentences():
    rows = []
    for line in (JOB / 'METIN.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|', line)
        if m: rows.append((int(m.group(1)), m.group(2)))
    assert len(rows) == 10, rows
    return rows


async def synth(text, mp3):
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
    words, audio = [], bytearray()
    async for ch in comm.stream():
        if ch['type'] == 'audio': audio += ch['data']
        elif ch['type'] == 'WordBoundary':
            s = ch['offset'] / 1e7; words.append({'w': ch['text'], 's': s, 'e': s + ch['duration'] / 1e7})
    mp3.write_bytes(bytes(audio))
    return words


def decode(mp3):
    raw = subprocess.run([FF, '-v', 'error', '-i', str(mp3), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / 'parcalar'; tmp.mkdir(exist_ok=True)
    pieces, allw, t = [], [], 0.0
    for c, text in sentences():
        mp3 = tmp / f'c{c:02d}.mp3'
        words = asyncio.run(synth(text, mp3))
        a = decode(mp3)
        # trim using word boundaries, then refine the tail with an energy gate
        s0 = max(0.0, words[0]['s'] - PAD_IN)
        e0 = min(len(a) / SR, words[-1]['e'] + PAD_OUT)
        env = np.abs(a); i_end = int(e0 * SR)
        while i_end < len(a) - 1 and env[i_end:i_end + 480].max() > 0.01: i_end += 480
        seg = a[int(s0 * SR):i_end].copy()
        ws = [{'w': w['w'], 's': w['s'] - s0, 'e': w['e'] - s0} for w in words]
        # compress comma pauses inside the sentence: any silent gap between words > MAXP is cut to MAXP
        MAXP = 0.12
        for k in range(len(ws) - 1, 0, -1):
            g0, g1 = ws[k - 1]['e'], ws[k]['s']
            if g1 - g0 > MAXP + 0.02:
                i0, i1 = int((g0 + 0.03) * SR), int((g1 - (MAXP - 0.03)) * SR)
                if i1 > i0 and np.abs(seg[i0:i1]).max() < 0.03:
                    cut = (i1 - i0) / SR
                    xf = int(0.004 * SR)
                    seg = np.concatenate([seg[:i0], seg[i1:]])
                    seg[max(0, i0 - xf):i0] *= np.linspace(1, 0.6, min(xf, i0))
                    for w in ws[k:]: w['s'] -= cut; w['e'] -= cut
        fade = int(0.008 * SR); seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        for w in ws:
            allw.append({'w': w['w'], 's': round(t + w['s'], 3), 'e': round(t + w['e'], 3), 'c': c})
        pieces.append(seg); t += len(seg) / SR
        if c < 10:
            pieces.append(np.zeros(int(GAP * SR), np.float32)); t += GAP
        print(c, f'{len(seg)/SR:.2f}s', len(words), 'kelime', text)
    audio = np.concatenate(pieces)
    tail = np.zeros(int(0.5 * SR), np.float32)  # short room at the end for the final frame
    audio = np.concatenate([audio, tail])
    raw = OUT / 'ses_raw.wav'
    with wave.open(str(raw), 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    # loudness to -14 LUFS / -1.5 dBTP (two-pass-free single loudnorm is close enough for a temp track)
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(raw), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7', '-ar', str(SR), '-ac', '1', str(OUT / 'ses.wav')], check=True)
    raw.unlink()
    (OUT / 'kelimeler.json').write_text(json.dumps(allw, ensure_ascii=False, indent=0), encoding='utf-8')
    n = len(allw); dur = allw[-1]['e']
    print(f'{n} kelime, konusma {dur:.2f}s, {n / dur * 60:.0f} kelime/dk, toplam {len(audio)/SR:.2f}s')


if __name__ == '__main__':
    main()
