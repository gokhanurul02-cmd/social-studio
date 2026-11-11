# (INGILIZCE SURUM: ses/en + project-en) Ses efektleri + miks (ucretli API yok, muzik yok):
#   .venv\Scripts\python.exe -X utf8 jobs\20261111-zdf-asansor\scripts\sfx_miks.py
# 1) Olay zamanlari project/src/shots.js ile AYNI formullerle kelime zamanlarindan (an(c,w)).
# 2) Bankadakiler Earshot (`social sfx sfx render`), olmayanlar (tel kopma tingleri, halat kirbaci, dusus ugultusu/ruzgar,
#    fren ciyaklamasi + kivilcim citirtisi, metal klank, tavana bonk, ekran tiklari, titresim) numpy ile prosedurel sentez.
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

T = dict(snap=an(1, 4), kop=an(1, 8), fall=an(2, 1), xst=an(2, 4), phone=an(3, 1), typeA=an(3, 3), sendT=an(3, 6),
         crouchA=an(4, 1), crouchB=an(4, 5), kir=an(4, 8), stop=an(5, 1), durur=an(5, 7), jump=an(6, 1), launch=an(6, 6),
         bonk=an(6, 7), hit=an(6, 8), gov=an(7, 1), trip=an(7, 6), clamp=an(7, 7), kenet=an(7, 8), final=an(7, 12), durdur=an(7, 18))
# shots.js ile ayni gecisler: whoosh listesi + kart cevirmeler (stop, gov)
WHOOSH = ['snap', 'drop0', 'fall', 'xstom', 'phone', 'crouchB', 'bonk', 'clamp', 'final']
SHOT_T = dict(snap=T['snap'], drop0=T['kop'], fall=T['fall'], xstom=T['xst'], phone=T['phone'], crouchB=T['crouchB'], bonk=T['bonk'],
              clamp=T['clamp'], final=T['final'])


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


def ping(f=3200, d=0.25, click=0.6):   # one steel wire parting: bright damped partials + click
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * k * (1 + 0.003 * k) * t) * np.exp(-t * (18 + 9 * k)) / k for k in (1, 2.76, 5.4))
    x[:int(0.003 * SR)] += rng.standard_normal(int(0.003 * SR)) * click
    return x
def syn_snap(times, d):
    x = np.zeros(int(d * SR) + SR // 2)
    for t in times:
        y = ping(rng.uniform(2500, 5200), 0.22) * rng.uniform(0.4, 1.0); k = int(t * SR); m = min(len(y), len(x) - k)
        if m > 0: x[k:k + m] += y[:m]
    return norm(x)
def syn_whip(d=0.5):  # rope whipping up: swept band noise + low body
    n = int(d * SR); t = np.arange(n) / SR; z = rng.standard_normal(n)
    y = bp(z, 300, 4000) * np.exp(-((t - d * 0.3) / (d * 0.18)) ** 2); return norm(y + 0.5 * lp(z, 120) * env(n, 0.01, d * 0.7))
def syn_rumble(d):     # free fall: low rumble + rail rattle + rising wind
    n = int(d * SR); t = np.arange(n) / SR; z = rng.standard_normal(n)
    y = lp(z, 90) * 3 + bp(z, 800, 2500) * 0.25 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 13 * t))) + bp(rng.standard_normal(n), 400, 1600) * np.linspace(0.2, 1, n)
    return norm(y * env(n, 0.05, 0.2))
def syn_screech(d):    # safety gear: steel on steel + spark crackle
    n = int(d * SR); t = np.arange(n) / SR
    f = 2900 + 220 * np.sin(2 * np.pi * 7 * t) - 600 * t / d
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + bp(rng.standard_normal(n), 2500, 7000) * 0.8
    c = np.zeros(n); c[rng.integers(0, n, int(d * 300))] = rng.uniform(-1, 1, int(d * 300)); y += hp(c, 3000) * 0.8
    return norm(y * env(n, 0.01, 0.12))
def syn_clank(d=0.6):  # car stops hard: thump + metallic ring
    n = int(d * SR); t = np.arange(n) / SR
    th = thump(48, 0.3, 0.8); th = np.pad(th, (0, max(0, n - len(th))))[:n]
    return norm(th * 1.2 + sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 6) for f in (410, 1130, 2270)) * 0.25)
def syn_bonk(d=0.5):   # head on the ceiling: hollow knock + comic pitch drop
    n = int(d * SR); t = np.arange(n) / SR
    th = thump(110, 0.12, 1.0); th = np.pad(th, (0, max(0, n - len(th))))[:n]
    return norm(np.sin(2 * np.pi * (520 - 260 * t / d) * t) * np.exp(-t * 9) + th)
def syn_taps(times, d):
    x = np.zeros(int(d * SR) + SR // 4); L = int(0.012 * SR)
    for t in times:
        y = hp(rng.standard_normal(L), 2500) * np.exp(-np.arange(L) / SR * 400); k = int(t * SR); x[k:k + L] += y[:len(x[k:k + L])]
    return norm(x)
def syn_buzz(d):       # phone vibrating on/off
    n = int(d * SR); t = np.arange(n) / SR
    y = np.sign(np.sin(2 * np.pi * 172 * t)) * 0.5 * (np.sin(2 * np.pi * 1.1 * t) > -0.2); return norm(lp(y, 900) * env(n, 0.01, 0.05))


def events():
    ev = []
    def add(t_acc, x, label, rel=-16.0, align='peak'):
        off = peak_s(x) if align == 'peak' else 0.0
        ev.append(dict(t=t_acc, start=t_acc - off, x=x, label=label, rel=rel))
    # --- 1. cabin, rope snap, drop
    add(0.0, synth('kabin_ugultu', syn_hum(T['snap'] + 0.3)), 'kabin/havalandırma uğultusu (alçak)', -26, align='start')
    u0, u1 = T['snap'] + 0.05, T['kop'] + 0.12
    times = sorted(u0 + (u1 - u0) * (0.05 + 0.85 * x) for x in rng.random(40))
    add(u0, synth('tel_kopma', syn_snap([x - u0 for x in times], u1 - u0)), 'çelik teller tek tek kopar (ting ting)', -15, align='start')
    add(T['kop'] + 0.02, synth('halat_kirbac', syn_whip(0.5)), 'halat kopup yukarı kırbaçlanır', -14)
    add(T['kop'] + 0.05, synth('dusus_1', syn_rumble(T['xst'] - T['kop'])), 'düşüş gürültüsü + ray tıkırtısı', -17, align='start')
    add(T['xst'], synth('ruzgar_dusus', syn_wind(T['phone'] - T['xst'] + 0.2)), 'düşüş rüzgârı (mide)', -20, align='start')
    # --- 3. phone typing + send
    ta, tb = T['typeA'], T['sendT'] - 0.05
    add(ta, synth('ekran_tik', syn_taps([(tb - ta) * k / 13 for k in range(14)], tb - ta)), 'klavye tıkları', -20, align='start')
    add(T['sendT'] + 0.03, earshot('pop/2', 'mesaj_gonder'), 'mesaj gönderildi (pop)', -17)
    add(T['phone'], synth('dusus_2', syn_rumble(T['stop'] - T['phone'])), 'düşüş gürültüsü (alçak, arka)', -24, align='start')
    # --- 5. flip: the car stops by itself
    add(T['stop'], earshot('swish/blade', 'flip_ama', dur=0.45, apex=0.18), 'kart çevirme swish (ters köşe)', -16)
    add(T['stop'] + 0.2, synth('fren_ciyak_1', syn_screech(max(0.3, T['durur'] - T['stop'] - 0.15))), 'güvenlik freni ciyaklaması + kıvılcım', -15, align='start')
    add(T['durur'] + 0.05, synth('durus_klank', syn_clank(0.6)), 'kabin aniden durur (klank)', -14)
    # --- 6. jump, bonk
    add(T['launch'], earshot('whoosh_big/cape', 'zipla_whoosh', dur=0.8, apex=0.3), 'zıplama whoosh', -18)
    add(T['hit'], synth('bonk', syn_bonk(0.5)), 'kafa tavana çarpar (bonk)', -13)
    add(T['hit'] + 0.08, earshot('pro_shimmer/m1', 'yildizlar', dur=0.9), 'yıldızlar (parıltı)', -21)
    # --- 7. governor + safety gear (peak)
    add(T['gov'], earshot('swish/soft', 'flip_gov', dur=0.45, apex=0.18), 'kart çevirme swish (mekanizma)', -17)
    add(T['gov'], synth('regulator_donus', syn_rumble(T['trip'] - T['gov']) * 0.7), 'regülatör kasnağı hızlanır', -21, align='start')
    add(T['trip'] + 0.03, earshot('fit/click/floss_lid', 'regulator_tik'), 'ağırlıklar açılır, mandal tık', -15)
    add(T['kenet'], synth('fren_ciyak_2', syn_screech(max(0.3, T['final'] - T['kenet'] - 0.15))), 'çeneler raya kenetlenir: ciyaklama + kıvılcım', -14, align='start')
    # --- sert son: kabin raylarda asılı, son kelimede küçük oturma
    add(T['final'] - 0.1, synth('final_klank', syn_clank(0.7)), 'kabin raylarda durur (klank)', -15)
    add(T['durdur'] + 0.1, synth('final_oturma', syn_clank(0.5) * 0.6), 'son oturma (alçak klank, sert son)', -18)
    # --- transitions (zoom-whoosh)
    sounds = ['whoosh_fast/crisp', 'whoosh_fast/tight', 'whoosh_fast/heavy', 'whoosh_fast/sleeve', 'whoosh_fast/whistle', 'swipe/glide', 'swipe/velvet']
    for i, k in enumerate(WHOOSH):
        add(SHOT_T[k], earshot(sounds[i % len(sounds)], f'whoosh_{i:02d}_{k}', dur=0.5, apex=0.2, seed=200 + i), f'zoom-whoosh geçiş → {k}', -18)
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
    L = ['# SFX — "Asansörün halatı kopsaydı?" v1 (kullanıcı kaydı + efektler)', '',
         'Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası',
         '(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (tel kopma, halat kırbacı, düşüş,',
         'fren ciyaklaması/kıvılcım, klank, bonk, ekran tıkları, titreşim, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.',
         'Seviye: her efekt aynı penceredeki konuşma RMS\'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.',
         f'Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **{d_voiced:.1f} dB**; konuşma RMS − efekt (aktif) RMS **{d_all:.1f} dB**.',
         'Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).', '',
         '| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |', '|---|---|---|---|']
    for t, s0, lab, rel in sorted(rows): L.append(f'| {t:.2f} | {s0:.2f} | {lab} | {rel:+.1f} dB |')
    (JOB / 'SFX-en.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(len(rows), 'efekt; miks ->', dst, '| ham', m['input_i'], 'LUFS', m['input_tp'], 'dBTP | konusma-efekt', round(d_voiced, 1), round(d_all, 1))
