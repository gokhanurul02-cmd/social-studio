# (INGILIZCE SURUM: ses/en + project-en) Ses efektleri + miks (ucretli API yok, muzik yok):
#   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-kurbaga-kalbi\scripts\sfx_miks.py
# 1) Olay zamanlari project/src/shots.js ile AYNI formullerle kelime zamanlarindan (an(c,w)).
# 2) Bankadakiler Earshot (`social sfx sfx render`), olmayanlar (squish, kalp atisi, adim, kalabalik, boing, buz catirtisi,
#    buz kirilma, buzdolabi contasi/menteşe, bugu fisiltisi, ruzgar) numpy ile prosedurel sentez.
# 3) Her efekt ayni penceredeki konusma RMS'inin `rel` dB altina (hepsi <= -16 dB). Anlati HIC degistirilmez (yalniz toplam
#    miks iki gecisli loudnorm linear -> -14 LUFS / <= -1.5 dBTP).  -> ses/en/miks.wav ; SFX-en.md
import json, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
SOCIAL = str(ROOT / 'social.cmd')
OUT = JOB / 'ses' / 'sfx-en'
SR = 48000
rng = np.random.default_rng(11)

W = json.loads((JOB / 'ses' / 'en' / 'kelimeler.trmap.json').read_text(encoding='utf-8'))
S = {}
for w in W: S.setdefault(w['c'], []).append(w)
an = lambda c, k: S[c][k - 1]['s']
voice, vsr = sf.read(JOB / 'ses' / 'en' / 'ses.wav', dtype='float32')
assert vsr == SR
DUR = W[-1]['e'] + 0.6
N = int(DUR * SR) + SR

T = dict(grab=an(1, 3), pull=an(1, 4), implant=an(1, 5), sec1=an(1, 7), xpea=an(2, 1), xflow=an(2, 5), purple=an(2, 8),
         rain=an(3, 1), fill=an(3, 6), dold=an(3, 8), pump=an(4, 1), race1=an(4, 5), race2=an(4, 7), hurdle=an(5, 1), jump=an(5, 4),
         winter=an(6, 1), heartA=an(7, 1), heartB=an(7, 4), mix=an(7, 7), frogsnow=an(8, 1), frozenx=an(8, 6), restart=an(8, 9),
         atar=an(8, 11), fridge=an(9, 1), out=an(9, 5), spring=an(9, 8))
WHOOSH = ['implant', 'sec1', 'xpea', 'purple', 'rain', 'fill', 'pump', 'race1', 'hurdle', 'heartA', 'frogsnow', 'frozenx', 'out', 'spring']


def earshot(sound, name, dur=None, apex=None, pitch=None, seed=None):
    p = OUT / f'{name}.wav'
    if not p.exists():
        cmd = [SOCIAL, 'sfx', 'sfx', 'render', sound, '-o', str(p), '--peak', '-1', '--sr', str(SR)]
        if dur: cmd += ['--dur', f'{dur:.3f}']
        if apex is not None: cmd += ['--apex', f'{apex:.3f}']
        if pitch: cmd += ['--pitch', pitch]
        if seed is not None: cmd += ['--seed', str(seed)]
        subprocess.run(cmd, check=True, capture_output=True)
    x, sr = sf.read(p, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    assert sr == SR
    return x


def env(n, a, r):
    t = np.arange(n) / SR; d = n / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
def bp(x, lo, hi, o=2): return signal.sosfilt(signal.butter(o, [lo, hi], btype='band', fs=SR, output='sos'), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, btype='high', fs=SR, output='sos'), x)
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, btype='low', fs=SR, output='sos'), x)
def norm(x, pk=0.89): return (x / (np.max(np.abs(x)) + 1e-9) * pk).astype('float32')


def thump(f0=55, d=0.16, click=0.3):
    n = int(d * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.8 * np.exp(-t * 40))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) + click * lp(rng.standard_normal(n), 900) * np.exp(-t * 90)
    return x


def syn_beats(d, rate, f0=60, double=True, jitter=0.0):
    n = int(d * SR); x = np.zeros(n)
    t = 0.0
    while t < d:
        for off, g in ([(0, 1.0), (0.2 / max(rate, 1) * 1.3, 0.6)] if double else [(0, 1.0)]):
            k = int((t + off) * SR); y = thump(f0 * (1 + rng.uniform(-jitter, jitter)), 0.18) * g
            m = min(len(y), n - k)
            if m > 0: x[k:k + m] += y[:m]
        t += 1.0 / rate * (1 + rng.uniform(-jitter, jitter))
    return norm(x * env(n, 0.02, 0.1))


def syn_swarm_beats(d, n_hearts=100):   # 100 tiny hearts, all slightly different rates -> chaotic flutter/rumble
    n = int(d * SR); x = np.zeros(n)
    for h in range(n_hearts):
        rate = rng.uniform(1.6, 3.0) * 1.4; t = rng.uniform(0, 1 / rate); f0 = rng.uniform(70, 140)
        y0 = thump(f0, 0.09, 0.5)
        while t < d:
            k = int(t * SR); m = min(len(y0), n - k)
            if m > 0: x[k:k + m] += y0[:m] * rng.uniform(0.5, 1.0)
            t += 1 / rate
    return norm(lp(x, 1800) * env(n, 0.25, 0.4))


def syn_squish(d=0.35):  # wet squelch: filtered noise bursts + low wobble
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * (18 + 30 * t) * t)) * np.exp(-t * 9)
    x += 0.6 * np.sin(2 * np.pi * (180 - 120 * t) * t) * np.exp(-t * 14)
    for tc in rng.uniform(0.02, d * 0.7, 5):
        k = int(tc * SR); m = int(0.025 * SR); tt = np.arange(m) / SR
        x[k:k + m] += 0.6 * np.sin(2 * np.pi * rng.uniform(500, 1200) * (1 + 2 * tt) * tt) * np.exp(-tt * 120)
    return norm(x * env(n, 0.005, 0.08))


def syn_plips(times, d):  # little "pit" impacts of hearts landing
    n = int(d * SR); x = np.zeros(n)
    for tc in times:
        k = int(tc * SR); m = int(0.06 * SR); tt = np.arange(m) / SR
        if k < 0 or k + m > n: continue
        f = rng.uniform(380, 700)
        x[k:k + m] += (np.sin(2 * np.pi * f * (1 - 2.5 * tt) * tt) * np.exp(-tt * 70) + 0.3 * bp(rng.standard_normal(m), 800, 3000) * np.exp(-tt * 150)) * rng.uniform(0.4, 1)
    return norm(x)


def syn_steps(d, rate):
    n = int(d * SR); x = np.zeros(n); t = 0.0
    while t < d:
        k = int(t * SR); m = int(0.07 * SR); tt = np.arange(m) / SR
        if k + m < n: x[k:k + m] += (lp(rng.standard_normal(m), 1500) * np.exp(-tt * 70) + 0.8 * np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 50)) * rng.uniform(0.7, 1)
        t += 1 / rate * rng.uniform(0.95, 1.05)
    return norm(x * env(n, 0.05, 0.2))


def syn_crowd(d):
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(bp(rng.standard_normal(n), 250 + 120 * k, 900 + 200 * k) * (0.6 + 0.4 * lp(rng.standard_normal(n), 3) * 4) for k in range(4))
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * t)
    return norm(x * env(n, 0.4, 0.6))


def syn_boing(d=0.7):
    n = int(d * SR); t = np.arange(n) / SR
    f = 140 + 520 * (1 - np.exp(-t * 6)) + 35 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 3)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    return norm(x + 0.3 * np.sin(2 * 2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6))


def syn_crackle(d, density=90, lo=2500):   # ice freezing crackle
    n = int(d * SR); x = np.zeros(n)
    for tc in np.sort(rng.uniform(0, d - 0.02, int(density * d))):
        k = int(tc * SR); m = int(rng.uniform(0.002, 0.012) * SR)
        x[k:k + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / (m / 5)) * rng.uniform(0.2, 1)
    t = np.arange(n) / SR
    x = hp(x, lo) + 0.15 * np.sin(2 * np.pi * 2400 * t) * hp(rng.standard_normal(n), 3000) * 0.1
    return norm(x * env(n, 0.1, 0.3))


def syn_icebreak(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t * 25)
    for tc in np.sort(rng.uniform(0, 0.25, 14)):
        k = int(tc * SR); m = int(0.03 * SR); tt = np.arange(m) / SR
        x[k:k + m] += np.sin(2 * np.pi * rng.uniform(2500, 6000) * tt) * np.exp(-tt * 80) * 0.6
    x += 0.5 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 18)
    return norm(x)


def syn_hiss(d):  # fog/steam whisper
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 2500, 9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.9 * t))
    return norm(x * env(n, 0.3, 0.5))


def syn_wind(d):
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 200, 900) * (0.5 + 0.5 * lp(rng.standard_normal(n), 1.5) * 6)
    return norm(x * env(n, 0.3, 0.4))


def syn_hum(d):
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) / k for k, f in enumerate([100, 200, 300, 120], 1)) + 0.05 * rng.standard_normal(n)
    return norm(x * env(n, 0.2, 0.3))


def syn_seal(d=0.5):  # fridge door gasket unstick + creak
    n = int(d * SR); t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), 600) * np.exp(-t * 30) * 1.2
    cr = np.sin(2 * np.pi * np.cumsum(260 + 90 * np.sin(2 * np.pi * 7 * t) + 40 * rng.standard_normal(n) * 0.2) / SR)
    x += 0.4 * bp(cr * (lp(np.abs(rng.standard_normal(n)), 40) > 0.5), 300, 3000) * env(n, 0.08, 0.15)
    return norm(x)


def synth(name, x):
    sf.write(OUT / f'{name}.wav', x, SR, subtype='PCM_24'); return x


def peak_s(x):
    e = np.convolve(np.abs(x), np.ones(240) / 240, 'same'); return int(np.argmax(e)) / SR


def events():
    ev = []
    def add(t_acc, x, label, rel=-16.0, align='peak'):
        off = peak_s(x) if align == 'peak' else 0.0
        ev.append(dict(t=t_acc, start=t_acc - off, x=x, label=label, rel=rel))
    # --- 1. frog + tweezers
    add(T['grab'] + 0.05, synth('cimbiz_squish', syn_squish(0.35)), 'cımbız ıslak dokuya girer (squish)', -16)
    add(T['grab'] + 0.08, earshot('fit/click/floss_lid', 'cimbiz_tik'), 'cımbız kapanır (metal tık)', -20)
    add(T['pull'] + 0.15, synth('kalp_squelch', syn_squish(0.45)), 'kalp çekilip çıkar (squelch)', -16)
    add(0.0, synth('kalp_minik_1', syn_beats(T['implant'], 3.2, 95, jitter=0.03)), 'minik kurbağa kalbi hızlı atış', -22, align='start')
    add(T['sec1'] + 0.45, earshot('pro_pop_in/knock', 'kalp_yerlesir'), 'kalp göğse yerleşir (pıt)', -17)
    add(T['sec1'] + 0.5, synth('kalp_minik_2', syn_beats(T['purple'] - T['sec1'] - 0.5, 4.4, 85, jitter=0.03)), 'minik kalp göğüste çırpınır (hızlı)', -20, align='start')
    add(T['xpea'] + 0.15, earshot('pop/2', 'bezelye_pop'), 'bezelye belirir (pop)', -18)
    add(T['purple'] + 0.1, earshot('pro_sub_drop/soft', 'mosmor_drop', dur=1.0), 'morarma alçak düşüş', -19)
    # --- 3. hearts fly in
    add(T['rain'] + 0.2, earshot('pro_whoosh_big/windy', 'kalpler_whoosh', dur=1.6, apex=1.0), 'kalpler gökten uçar (whoosh)', -18)
    r = np.random.default_rng(4); a = [r.random() for _ in range(110)]
    # same draw order as shots.js mulberry(4)? -> not identical RNG; arrivals spread over the same window
    arr = sorted(T['rain'] + 0.6 + (T['dold'] + 0.3 - T['rain'] - 0.6) * x for x in a)
    t0 = T['rain'] + 0.5
    add(t0, synth('kalpler_pit', syn_plips([x - t0 for x in arr], T['pump'] - t0 + 0.3)), 'kalpler göğse dolar (pıt pıt)', -17, align='start')
    add(T['dold'], synth('kalp_100_kaos_1', syn_swarm_beats(T['race1'] - T['dold'] + 0.4)), '100 kalp kaotik çoklu atış', -17, align='start')
    # --- 4–5. race, jump
    add(T['race1'], synth('kalp_100_kaos_2', syn_swarm_beats(T['winter'] - T['race1'])), '100 kalp atışı (koşu altında, alçak)', -24, align='start')
    add(T['race1'], synth('adimlar_1', syn_steps(T['jump'] - T['race1'], 3.6)), 'koşu adımları', -18, align='start')
    add(T['race1'], synth('kalabalik_1', syn_crowd(T['winter'] - T['race1'])), 'kalabalık (hafif)', -24, align='start')
    add(T['jump'] + 0.05, earshot('whoosh_big/cape', 'zipla_whoosh', dur=1.0, apex=0.35), 'zıplama whoosh', -17)
    add(T['jump'] + 0.1, synth('zipla_boing', syn_boing(0.75)), 'kurbağa zıplaması boing', -18)
    add(T['winter'] - 0.28, earshot('impact/punch', 'inis_thud', dur=0.6), 'iniş (thud)', -18)
    # --- 6. flip -> winter, ice
    add(T['winter'], earshot('swish/blade', 'flip_kis', dur=0.45, apex=0.18), 'kart çevirme swish (ters köşe)', -16)
    add(T['winter'] + 0.05, synth('buz_donma', syn_crackle(1.4, 110)), 'buz donma çatırtısı', -17, align='start')
    add(T['winter'], synth('kis_ruzgar', syn_wind(T['heartA'] - T['winter'] + 0.2)), 'kış rüzgârı (alçak)', -24, align='start')
    # --- 7. three-chamber heart
    add(T['heartA'], synth('kalp_tek', syn_beats(T['mix'] - T['heartA'], 1.6, 55)), 'kalp atışı (kesit, yavaş)', -18, align='start')
    for i, k in enumerate([4, 5, 6]): add(an(7, k), earshot('pro_hover_tick/glass', f'oda_tik_{i}'), f'oda {i + 1} parlar (tık)', -19)
    add(an(7, 9), synth('kan_karisir', syn_squish(1.2) * 0.8), 'kan karışır (sıvı çalkantı)', -19)
    # --- 8. frog freezes, heart stops, restarts
    add(an(8, 4), synth('kurbaga_donma', syn_crackle(1.2, 70, 3500)), 'kurbağa donar (buz çatırtısı)', -17, align='start')
    add(T['frozenx'], earshot('pro_shimmer/m1', 'donmus_parilti', dur=0.9), 'donmuş kalp (buzlu parıltı)', -21)
    add(T['restart'] + 0.05, synth('buz_kirilma', syn_icebreak(0.6)), 'buz kırılır (bahar)', -16)
    add(T['atar'], synth('kalp_yeniden', norm(thump(60, 0.3, 0.5) + 0.5 * np.pad(thump(65, 0.25, 0.3), (int(0.2 * SR), 0))[:int(0.3 * SR)])), 'kalp yeniden atar (tık/thump)', -14.5)
    # --- 9. fridge, out, spring
    add(T['fridge'], earshot('swish/soft', 'flip_buzdolabi', dur=0.45, apex=0.18), 'kart çevirme swish (buzdolabı)', -16)
    add(T['fridge'], synth('buzdolabi_ugultu', syn_hum(T['out'] - T['fridge'] + 0.5)), 'buzdolabı uğultusu (alçak)', -25, align='start')
    add(T['out'] + 0.02, synth('kapak_conta', syn_seal(0.5)), 'buzdolabı kapağı/conta açılma', -16)
    add(T['out'] + 0.05, synth('bugu_fisilti', syn_hiss(1.6)), 'buğu fısıltısı', -19, align='start')
    add(T['spring'], synth('adimlar_2', syn_steps(DUR - T['spring'], 3.6)), 'bahar pisti koşu adımları', -18, align='start')
    add(T['spring'], synth('kalabalik_2', syn_crowd(DUR - T['spring'])), 'kalabalık (hafif)', -25, align='start')
    # --- transitions
    sounds = ['whoosh_fast/crisp', 'whoosh_fast/tight', 'whoosh_fast/heavy', 'whoosh_fast/sleeve', 'whoosh_fast/whistle', 'swipe/glide', 'swipe/velvet']
    for i, k in enumerate(WHOOSH):
        add(T[k], earshot(sounds[i % len(sounds)], f'whoosh_{i:02d}_{k}', dur=0.5, apex=0.2, seed=200 + i), f'zoom-whoosh geçiş → {k}', -18)
    return ev


def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-9)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    ev = events()
    vtrack = np.zeros(N, dtype='float32'); vtrack[:len(voice)] = voice
    voice_db = rms_db(voice[np.abs(voice) > 1e-3])
    sfx = np.zeros(N, dtype='float32'); rows = []
    for e in ev:
        x = e['x']; k = int(round(e['start'] * SR)); k0 = max(0, k); x = x[k0 - k:]
        seg_v = vtrack[k0:k0 + len(x)]
        voiced = seg_v[np.abs(seg_v) > 1e-3]
        ref = rms_db(voiced) if len(voiced) > SR * 0.1 else voice_db
        act = x[np.abs(x) > 0.02 * np.max(np.abs(x))]
        g = 10 ** ((ref + e['rel'] - rms_db(act)) / 20)
        sfx[k0:k0 + len(x)] += x * g
        rows.append((e['t'], e['start'], e['label'], e['rel']))
    sf.write(OUT / 'sfx_track.wav', sfx, SR, subtype='PCM_24')
    mix = vtrack + sfx
    raw = OUT / 'miks_raw.wav'; sf.write(raw, mix[:int(DUR * SR)], SR, subtype='FLOAT')
    dst = JOB / 'ses' / 'en' / 'miks.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(raw), '-af', af, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s24le', str(dst)], check=True)
    # speech vs effects level (voiced windows)
    vm = np.abs(lp(np.abs(vtrack), 10)) > 0.01
    d_voiced = rms_db(vtrack[vm]) - rms_db(sfx[vm])
    d_all = rms_db(vtrack[vm]) - rms_db(sfx[np.abs(sfx) > 1e-5])
    L = ['# SFX — "Ya bir kurbağanın kalbi sana takılsaydı?" v1 (kullanıcı kaydı + efektler)', '',
         'Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası',
         '(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (squish, kalp atışları, 100 kalp kaosu, adım,',
         'kalabalık, boing, buz donma/kırılma, conta, buğu, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.',
         'Seviye: her efekt aynı penceredeki konuşma RMS\'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.',
         f'Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **{d_voiced:.1f} dB**; konuşma RMS − efekt (aktif) RMS **{d_all:.1f} dB**.',
         'Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).', '',
         '| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |', '|---|---|---|---|']
    for t, s0, lab, rel in sorted(rows): L.append(f'| {t:.2f} | {s0:.2f} | {lab} | {rel:+.1f} dB |')
    (JOB / 'SFX-en.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(len(rows), 'efekt; miks ->', dst, '| ham', m['input_i'], 'LUFS', m['input_tp'], 'dBTP | konusma-efekt', round(d_voiced, 1), round(d_all, 1))
