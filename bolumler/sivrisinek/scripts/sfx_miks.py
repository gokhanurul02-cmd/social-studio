# Ses efektleri + miks (ucretli API yok):
#   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\sfx_miks.py
# 1) Olay zamanlari project/src/shots.js ile AYNI formullerle kelime zamanlarindan hesaplanir (an(c,w)).
# 2) Bankada olan sesler Earshot (`social sfx sfx render`, 201 sesli kod-bankasi) ile, bankada olmayanlar
#    (slurp, balon gerilme, kuru yaprak, kanat vizi, fizz, crack govdesi) numpy ile prosedurel sentezlenir.
# 3) Her efekt, ayni penceredeki konusmanin RMS'inin `rel` dB altina oturtulur (varsayilan -16 dB) -> konusma hep net.
# 4) Anlati + SFX toplanir, iki gecisli loudnorm (linear) ile -14 LUFS / -1 dBTP -> ses/kullanici/miks.wav ; SFX.md yazilir.
import json, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal

JOB = Path(__file__).resolve().parents[1]
ROOT = JOB.parents[1]
FF = str(ROOT / 'bin' / 'ffmpeg.exe')
SOCIAL = str(ROOT / 'social.cmd')
OUT = JOB / 'ses' / 'sfx'
SR = 48000
rng = np.random.default_rng(7)

W = json.loads((JOB / 'ses' / 'kullanici' / 'kelimeler.json').read_text(encoding='utf-8'))
S = {}
for w in W: S.setdefault(w['c'], []).append(w)
an = lambda c, k: S[c][k - 1]['s']
en = lambda c, k: S[c][k - 1]['e']
voice, vsr = sf.read(JOB / 'ses' / 'kullanici' / 'ses.wav', dtype='float32')
assert vsr == SR
DUR = W[-1]['e'] + 0.6
N = int(DUR * SR) + SR

# ---------------------------------------------------------------- shots.js timeline (same formulas)
T = dict(grow0=an(1, 5) - 0.32, night0=an(1, 5) + 0.04, grow1=an(1, 7) + 0.25, reveal0=an(2, 1),
         probe0=an(3, 1), pierce0=an(3, 3), bite=an(3, 5) - 0.05, balloon0=an(3, 7),
         x1=an(4, 1), x3=an(5, 1), dry0=an(5, 4), door0=an(6, 1), tr0=an(7, 1), tr1=an(8, 1), tr2=an(9, 5), o2out=an(9, 8),
         legsA=an(10, 1), sc0=an(11, 1), sc1=an(11, 5), sc2=an(11, 9), legsB=an(12, 1), crack=an(12, 4), fall0=an(12, 5),
         thud=an(12, 9), fin0=an(12, 10))
# fascicle tip crosses the skin surface (section.js: tip from TOP-1.2=7.8 to VES_Y=-1.2 over [pierce0-0.15, bite+0.25], easeInOutCubic)
def ease_inv(y):
    lo, hi = 0.0, 1.0
    for _ in range(50):
        m = (lo + hi) / 2; v = 4 * m ** 3 if m < 0.5 else 1 - (-2 * m + 2) ** 3 / 2
        lo, hi = (m, hi) if v < y else (lo, m)
    return lo
u_skin = ease_inv((7.8 - 0.0) / (7.8 + 1.25))
T['skin'] = T['pierce0'] - 0.15 + u_skin * (T['bite'] + 0.25 - (T['pierce0'] - 0.15))


# ---------------------------------------------------------------- sources
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


def env_adsr(n, a, r, shape=1.0):
    t = np.arange(n) / SR; d = n / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
    return e ** shape


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos'); return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def norm(x, peak=0.89):
    return (x / (np.max(np.abs(x)) + 1e-9) * peak).astype('float32')


def syn_buzz(d):        # mosquito wing whine: ~600 Hz saw with vibrato + harmonics, band-limited
    n = int(d * SR); t = np.arange(n) / SR
    f = 590 + 25 * np.sin(2 * np.pi * 5.3 * t) + 12 * np.sin(2 * np.pi * 13 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum((1 / k) * np.sin(k * ph) for k in range(1, 9)) * (0.8 + 0.2 * np.sin(2 * np.pi * 41 * t))
    x = bp(x, 400, 5000) + 0.05 * hp(rng.standard_normal(n), 3000)
    return norm(x * env_adsr(n, 0.15, 0.3))


def syn_slurp(d):       # straw slurp: sucked noise with gurgling bubbles and a rising formant
    n = int(d * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for i, fc in enumerate(np.linspace(500, 1300, 24)):
        a, b = int(i / 24 * n), int((i + 1) / 24 * n)
        seg = bp(noise[max(0, a - 2000):b], fc * 0.7, fc * 1.4)[-(b - a):]
        out[a:b] = seg
    gate = (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * (11 + 4 * t) * t + 2 * np.sin(2 * np.pi * 3 * t))))
    gate = lp(gate, 60)
    bub = np.zeros(n)
    for tb in np.sort(rng.uniform(0.05, d - 0.08, 9)):
        k = int(tb * SR); m = int(0.05 * SR); tt = np.arange(m) / SR
        fb = rng.uniform(300, 700) * (1 + 3 * tt)
        bub[k:k + m] += np.sin(2 * np.pi * np.cumsum(fb) / SR) * np.exp(-tt * 60)
    x = out * gate + 0.8 * bub
    return norm(x * env_adsr(n, 0.04, 0.12))


def syn_stretch(d):     # rubber balloon stretching: rough, rising squeak (FM + friction noise)
    n = int(d * SR); t = np.arange(n) / SR
    f0 = 240 + 380 * (t / d) ** 1.4
    jitter = lp(rng.standard_normal(n), 30) * 25
    ph = 2 * np.pi * np.cumsum(f0 + jitter) / SR
    stick = (lp(np.abs(rng.standard_normal(n)), 120) > 0.7).astype(float)
    x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)) * (0.5 + 0.5 * lp(stick, 80))
    x = bp(x, 180, 4000) + 0.15 * bp(rng.standard_normal(n), 1500, 6000)
    return norm(x * env_adsr(n, 0.06, 0.15))


def syn_leaves(d):      # dry-leaf crumple: dense random crackles, high-passed, with a crumpling envelope
    n = int(d * SR); x = np.zeros(n)
    times = np.sort(rng.uniform(0, d - 0.02, int(70 * d)))
    for tc in times:
        k = int(tc * SR); m = int(rng.uniform(0.004, 0.02) * SR)
        x[k:k + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.3, 1)
    x = hp(x, 1800) + 0.25 * bp(rng.standard_normal(n), 2500, 9000) * lp(np.abs(x), 30) * 4
    return norm(x * env_adsr(n, 0.08, 0.25))


def syn_fizz(d):        # oxygen fizzling out: high hiss with sparse pops, falling brightness
    n = int(d * SR); t = np.arange(n) / SR
    hiss = hp(rng.standard_normal(n), 4000) * np.exp(-t / (d * 0.45))
    pops = np.zeros(n)
    for tc in np.sort(rng.uniform(0, d * 0.8, 25)):
        k = int(tc * SR); m = 200
        pops[k:k + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / 40)
    x = hiss + 0.6 * hp(pops, 2000)
    return norm(x * env_adsr(n, 0.01, 0.2))


def syn_crack(d=0.35):  # bone/chitin crack: sharp broadband transient + splinter crackles + low knock
    n = int(d * SR); t = np.arange(n) / SR
    tr = rng.standard_normal(n) * np.exp(-t * 90)
    spl = np.zeros(n)
    for tc in [0.0, 0.012, 0.03, 0.05, 0.075]:
        k = int(tc * SR); m = int(0.015 * SR)
        spl[k:k + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / 120)
    knock = np.sin(2 * np.pi * 160 * t) * np.exp(-t * 35)
    x = bp(tr, 800, 9000) + 0.8 * hp(spl, 1500) + 0.6 * knock
    return norm(x)


def synth(name, fn, *a):
    p = OUT / f'{name}.wav'
    x = fn(*a); sf.write(p, x, SR, subtype='PCM_24'); return x


# ---------------------------------------------------------------- events: (name, time of accent, source array, peak offset s, rel dB, label)
def peak_s(x):
    e = np.convolve(np.abs(x), np.ones(240) / 240, 'same'); return int(np.argmax(e)) / SR


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = []
    def add(t_acc, x, label, rel=-16.0, align='peak'):
        off = peak_s(x) if align == 'peak' else 0.0
        ev.append(dict(t=t_acc, start=t_acc - off, x=x, label=label, rel=rel))

    # büyüme: şişme/whoosh (grow0 -> grow1)
    add(T['grow0'] + 0.85, earshot('pro_whoosh_big/swell', 'buyume_swell', dur=1.4, apex=0.85), 'büyüme şişme/whoosh (makro → insan boyu)', -18.5)
    # kanat vızıltısı (alçak): makro/gece + kapıya yürüyüş
    add(0.0, synth('vizilti_1', syn_buzz, 2.6), 'sivrisinek kanat vızıltısı (alçak)', -25, align='start')
    add(T['door0'] + 0.15, synth('vizilti_2', syn_buzz, 1.5), 'kanat vızıltısı (kapıya yönelirken, alçak)', -23, align='start')
    # zoom-whoosh geçişleri (her biri farklı varyant)
    W = [('reveal0', 'whoosh_fast/crisp'), ('pierce0', 'whoosh_fast/tight'), ('x1', 'whoosh_fast/heavy'), ('dry0', 'whoosh_fast/sleeve'),
         ('tr1', 'swipe/glide'), ('legsA', 'whoosh_fast/crisp'), ('sc0', 'whoosh_fast/whistle'), ('sc2', 'whoosh_fast/tight'),
         ('legsB', 'whoosh_fast/heavy'), ('fin0', 'swipe/velvet')]
    for i, (k, snd) in enumerate(W):
        add(T[k], earshot(snd, f'whoosh_{i:02d}_{k}', dur=0.55, apex=0.2, seed=100 + i), f'zoom-whoosh geçiş → {k}', -17)
    # 3D kart çevirme: flip/swish
    add(T['door0'], earshot('swish/blade', 'flip_door', dur=0.45, apex=0.18), 'kart çevirme flip/swish (ters köşe)', -16)
    add(T['tr0'], earshot('fit/whoosh.short/bamboo_swish', 'flip_trake', dur=0.5), 'kart çevirme flip/swish (gerçeklere geçiş)', -16)
    # hortum deriye saplanır: thunk
    add(T['skin'], earshot('pro_pop_in/knock', 'saplanma_knock'), 'hortum deriye saplanma (thunk)', -16)
    add(T['skin'] + 0.005, earshot('pro_impact/short', 'saplanma_govde', dur=0.5), 'saplanma gövdesi (alçak impact)', -19)
    # kan çekme slurp, karın şişmesi
    add(T['bite'] + 0.1, synth('kan_slurp', syn_slurp, 0.75), 'kan çekme slurp/pipet', -16, align='start')
    add(T['balloon0'], synth('balon_gerilme', syn_stretch, 0.75), 'karın şişmesi balon gerilme', -17, align='start')
    # büzüşme: kuru yaprak
    add(T['dry0'] + 0.05, synth('kuru_yaprak', syn_leaves, 1.0), 'büzüşme kuru yaprak hışırtısı', -16, align='start')
    # oksijen sönmesi fizz
    add(T['o2out'] - 0.3, synth('oksijen_fizz', syn_fizz, 1.0), 'oksijen sönmesi fizz', -17, align='start')
    # ağırlık oku iner (küçük vuruş) + bacak kesiti çatlar
    add(an(11, 6) + 0.1, earshot('pro_impact/short', 'ok_iner', dur=0.5), 'ağırlık oku iner (kısa vuruş)', -18)
    add(an(11, 13), synth('kesit_catlak', syn_crack, 0.3), 'bacak kesiti çatlar (crack)', -17)
    # bacaklar kırılır: crack/snap x2 (kink at crack, 2nd pair +0.25 s)
    c1 = synth('kirilma_1', syn_crack, 0.35); add(T['crack'], c1, 'bacak kırılması crack/snap', -17)
    add(T['crack'], earshot('click/snap', 'kirilma_snap'), 'kırılma snap katmanı', -18)
    add(T['crack'] + 0.25, synth('kirilma_2', syn_crack, 0.35), 'ikinci bacak kırılır (crack)', -18)
    # yığılma: thud
    add(T['thud'], earshot('impact/punch', 'yigilma_thud', dur=0.9), 'yere yığılma (thud)', -17)
    return ev


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-9)


if __name__ == '__main__':
    ev = main()
    vtrack = np.zeros(N, dtype='float32'); vtrack[:len(voice)] = voice
    voice_db = rms_db(voice[np.abs(voice) > 1e-3])
    sfx = np.zeros(N, dtype='float32'); rows = []
    for e in ev:
        x = e['x']; k = int(round(e['start'] * SR)); k0 = max(0, k); x = x[k0 - k:]
        seg_v = vtrack[k0:k0 + len(x)]
        # reference: speech RMS over the voiced part of the effect's window (or the whole-narration RMS in a pause)
        voiced = seg_v[np.abs(seg_v) > 1e-3]
        ref = rms_db(voiced) if len(voiced) > SR * 0.1 else voice_db
        act = x[np.abs(x) > 0.02 * np.max(np.abs(x))]
        g = 10 ** ((ref + e['rel'] - rms_db(act)) / 20)
        sfx[k0:k0 + len(x)] += x * g
        rows.append((e['t'], e['start'], e['label'], e['rel'], 20 * np.log10(g)))
    sf.write(OUT / 'sfx_track.wav', sfx, SR, subtype='PCM_24')
    mix = vtrack + sfx
    raw = OUT / 'miks_raw.wav'; sf.write(raw, mix[:int(DUR * SR)], SR, subtype='FLOAT')
    dst = JOB / 'ses' / 'kullanici' / 'miks.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(raw), '-af', af, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s24le', str(dst)], check=True)
    # SFX.md
    L = ['# SFX — "Ya bir sivrisinek senin boyunda olsaydı?" v2 (kullanıcı kaydı + efektler)', '',
         'Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası',
         '(`social sfx sfx render`, kodla üretilen 201 ses, ücretsiz/yerel) + bankada olmayanlar için numpy prosedürel sentez',
         '(slurp, balon gerilme, kuru yaprak, vızıltı, fizz, crack gövdesi). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.',
         'Seviye: her efekt aynı penceredeki konuşma RMS\'inin "hedef" dB altına oturtulur; müzik yatağı YOK.',
         'Final miks: `ses/kullanici/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).', '',
         '| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |', '|---|---|---|---|']
    for t, s0, lab, rel, gdb in sorted(rows):
        L.append(f'| {t:.2f} | {s0:.2f} | {lab} | {rel:+.0f} dB |')
    (JOB / 'SFX.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(len(rows), 'efekt; miks ->', dst, '| ham', m['input_i'], 'LUFS', m['input_tp'], 'dBTP')
    for t, s0, lab, rel, gdb in sorted(rows): print(f'{t:6.2f} {lab}  gain {gdb:+.1f} dB')
