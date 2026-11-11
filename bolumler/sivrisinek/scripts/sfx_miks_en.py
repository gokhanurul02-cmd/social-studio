# (EN) # Ses efektleri + miks — METIN v2 / onizleme-v1 sahneleri + kullanici kaydi v2 (project-v2metin).
# (EN) #   .venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\sfx_miks_en.py
# (EN) # sfx_miks.py (v3) ile ayni yaklasim ve ayni ses kaynaklari (Earshot bankasi + numpy sentez fonksiyonlari oradan alinir),
# (EN) # ama olay zamanlari project-en/src/shots.js (onizleme-v1) formulleriyle ses/en/kelimeler.trmap.json'dan hesaplanir.
# (EN) # Cikti: ses/sfx-en/*.wav, ses/sfx-en/sfx_track.wav, ses/en/miks.wav (-14 LUFS, <= -1.5 dBTP), SFX-en.md
import json, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sfx_miks as M          # synth/earshot helpers (module-level code only reads the v3 files; nothing is written)

JOB = HERE.parent
FF, SR = M.FF, M.SR
OUT = JOB / 'ses' / 'sfx-en'
M.OUT = OUT                    # earshot()/synth() cache into this folder
M.rng = np.random.default_rng(11)
VDIR = JOB / 'ses' / 'en'

W = json.loads((VDIR / 'kelimeler.trmap.json').read_text(encoding='utf-8'))
S = {}
for w in W: S.setdefault(w['c'], []).append(w)
an = lambda c, k: S[c][k - 1]['s']
voice, vsr = sf.read(VDIR / 'ses.wav', dtype='float32')
assert vsr == SR
DUR = W[-1]['e'] + 0.6
N = int(DUR * SR) + SR

# ---------------------------------------------------------------- project-en/src/shots.js timeline (same formulas)
T = dict(grow0=an(1, 5) - 0.32, night0=an(1, 5) + 0.04, grow1=an(1, 8) + 0.35, wake0=an(2, 1), open=an(2, 2) + 0.05,
         reveal0=an(2, 4), ots0=an(2, 8), pull0=an(3, 1), probe0=an(3, 4), pierce0=an(3, 7), bite=an(3, 10),
         x1=an(4, 1), x2=an(4, 4), x3=an(4, 9), dry0=an(5, 1), balloon0=an(5, 7), door0=an(6, 1),
         legsA=an(7, 1), legsB=an(7, 3), crack=an(7, 6), fall0=an(7, 7), tr0=an(8, 1), tr1=an(8, 5), tr2=an(8, 10),
         sc0=an(9, 1), sc1=an(9, 6), sc2=an(9, 10), fin0=an(10, 1), fin1=an(10, 4), eye=an(10, 6))
# shot_pierce: fascicle tip y from TOP-1.2 = 7.8 to VES_Y+0.05 = -1.2 over [pierce0-0.15, bite+0.25], easeInOutCubic
def tip_cross(y):
    u = M.ease_inv((7.8 - y) / (7.8 + 1.2))
    return T['pierce0'] - 0.15 + u * (T['bite'] + 0.25 - (T['pierce0'] - 0.15))
T['fabric'] = tip_cross(2.6)   # SEC.FAB_Y1: top of the quilted blanket
T['skin'] = tip_cross(0.0)     # skin surface


def syn_cloth(d):       # blanket rustle: band-passed noise with irregular swishes (fabric friction)
    n = int(d * SR); t = np.arange(n) / SR; rng = M.rng
    x = rng.standard_normal(n)
    x = M.bp(x, 700, 6500) + 0.4 * M.bp(rng.standard_normal(n), 250, 900)
    mod = M.lp(np.abs(rng.standard_normal(n)), 9) * 3
    swell = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.7
    return M.norm(x * (0.35 + mod) * swell * M.env_adsr(n, 0.05, 0.2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = []
    def add(t_acc, x, label, rel=-16.0, align='peak'):
        off = M.peak_s(x) if align == 'peak' else 0.0
        ev.append(dict(t=t_acc, start=t_acc - off, x=x, label=label, rel=rel))
    E, Y = M.earshot, M.synth

    # 1 macro/night: alçak kanat vızıltısı + büyüme şişme/whoosh (grow0 -> grow1)
    add(0.0, Y('vizilti_1', M.syn_buzz, 2.4), 'sivrisinek kanat vızıltısı (alçak, makro)', -26, align='start')
    g = T['grow1'] - T['grow0']
    add(T['grow1'], E('pro_whoosh_big/swell', 'buyume_swell', dur=g + 0.3, apex=g), 'büyüme şişme/whoosh (makro → insan boyu)', -18.5)
    add(T['grow1'] - 0.35, Y('vizilti_2', M.syn_buzz, 0.9), 'kanat açılışı vızıltı (büyüme sonu, alçak)', -25, align='start')
    # zoom-whoosh geçişleri (shots.js: W('night'..'fin1'))
    WH = [('night0', 'whoosh_fast/crisp'), ('wake0', 'whoosh_fast/sleeve'), ('reveal0', 'whoosh_fast/tight'), ('pierce0', 'whoosh_fast/heavy'),
          ('x1', 'swipe/glide'), ('dry0', 'whoosh_fast/sleeve'), ('sc0', 'whoosh_fast/whistle'), ('sc2', 'whoosh_fast/tight'), ('fin0', 'swipe/velvet')]
    for i, (k, snd) in enumerate(WH):
        add(T[k], E(snd, f'whoosh_{i:02d}_{k}', dur=0.55, apex=0.2, seed=200 + i), f'zoom-whoosh geçiş → {k}', -17)
    # 3D kart çevirme (F('door'), F('tr1'))
    add(T['door0'], E('swish/blade', 'flip_door', dur=0.45, apex=0.18), 'kart çevirme flip/swish (ters köşe: kapı)', -16)
    add(T['tr0'], E('fit/whoosh.short/bamboo_swish', 'flip_trake', dur=0.5), 'kart çevirme flip/swish (gerçeklere geçiş)', -16)
    # 3 yorgan kafaya çekilir: hışırtı (pull0+0.05 -> an(3,3)+0.05) + titreme
    yd = an(3, 3) + 0.05 - T['pull0']
    add(T['pull0'] + 0.02, Y('yorgan_hisirti', syn_cloth, yd + 0.25), 'yorgan hışırtısı (kafaya çekilir)', -18, align='start')
    add(an(3, 3) - 0.05, E('swipe/cloth', 'yorgan_swipe', dur=0.6, apex=0.18), 'yorgan çekiş swish katmanı', -20)
    add(an(3, 3) + 0.05, Y('yorgan_titreme', syn_cloth, 0.5), 'yorgan altında titreme hışırtısı', -21, align='start')
    # hortum yorganı ve deriyi deler: thunk x2
    add(T['fabric'], E('pro_pop_in/knock', 'delme_yorgan', pitch='G2'), 'hortum yorganı deler (kumaş thunk)', -17)
    add(T['skin'], E('pro_pop_in/knock', 'delme_deri'), 'hortum deriye saplanır (thunk)', -16)
    add(T['skin'] + 0.005, E('pro_impact/short', 'delme_govde', dur=0.5), 'saplanma gövdesi (alçak impact)', -19)
    # 4 pipet slurp: "pipetle" + x-ray boşalma (x3-0.05 -> an(4,11)+0.15)
    add(T['x2'] + 0.05, Y('slurp_1', M.syn_slurp, 0.8), 'pipet slurp (pipetle)', -17, align='start')
    add(T['x3'], Y('slurp_2', M.syn_slurp, an(4, 11) + 0.25 - T['x3']), 'kan çekme slurp (tek seferde çeker)', -16, align='start')
    # 5 kuru yaprak büzüşme (dry0+0.1 -> an(5,6)+0.35) + balon gerilme (balloon0 -> an(5,11)+0.2)
    add(T['dry0'] + 0.1, Y('kuru_yaprak', M.syn_leaves, an(5, 6) + 0.35 - T['dry0'] - 0.1), 'büzüşme kuru yaprak hışırtısı', -16, align='start')
    add(T['balloon0'], Y('balon_gerilme', M.syn_stretch, an(5, 11) + 0.2 - T['balloon0']), 'karın şişmesi balon gerilme', -19, align='start')
    # 6 kapıya yürüyüş: ağır kitin adımlar + alçak vızıltı
    for i, dt in enumerate([0.35, 0.8, 1.25]):
        add(T['door0'] + dt, E('pro_tap/soft', f'adim_{i}', pitch='E2', seed=300 + i), f'kapıya doğru adım {i + 1} (kitin tık)', -19)
    add(T['door0'] + 0.15, Y('vizilti_3', M.syn_buzz, 1.3), 'kanat vızıltısı (kapıya yönelirken, alçak)', -24, align='start')
    # 7 ilk adım + bacaklar makarna gibi kırılır + yığılma
    add(T['legsA'] + 0.15, E('tap/table', 'ilk_adim', pitch='D2'), 'ilk adım (ağır tık)', -18)
    add(T['crack'], Y('kirilma_1', M.syn_crack, 0.35), 'bacak kırılması crack/snap', -17)
    add(T['crack'], E('click/snap', 'kirilma_snap'), 'kırılma snap katmanı', -18)
    add(T['crack'] + 0.25, Y('kirilma_2', M.syn_crack, 0.35), 'ikinci bacak kırılır (crack)', -18)
    add(T['fall0'] + 0.35, E('impact/punch', 'yigilma_thud', dur=0.9), 'yere yığılma (thud)', -19)
    add(T['fall0'] + 0.5, Y('vizilti_4', M.syn_buzz, 0.8), 'yerde kanat çırpınması (alçak vızıltı)', -25, align='start')
    # 8 trake: oksijen sönmesi fizz (reach daralır, renk kırmızıya an(8,14))
    add(an(8, 14) - 0.3, Y('oksijen_fizz', M.syn_fizz, 1.0), 'oksijen sönmesi fizz', -17, align='start')
    # 9 ölçek: ağırlık oku iner (an(9,7)+0.1) + bacak kesiti çatlar (uCrack an(9,12) ->)
    add(an(9, 7) + 0.1, E('pro_impact/short', 'ok_iner', dur=0.5), 'ağırlık oku iner (kısa vuruş)', -18)
    add(an(9, 12) + 0.1, Y('kesit_catlak', M.syn_crack, 0.3), 'bacak kesiti çatlar (crack)', -17)
    return ev


if __name__ == '__main__':
    ev = main()
    vtrack = np.zeros(N, dtype='float32'); vtrack[:len(voice)] = voice
    voice_db = M.rms_db(voice[np.abs(voice) > 1e-3])
    sfx = np.zeros(N, dtype='float32'); rows = []
    for e in ev:
        x = e['x']; k = int(round(e['start'] * SR)); k0 = max(0, k); x = x[k0 - k:]
        seg_v = vtrack[k0:k0 + len(x)]
        voiced = seg_v[np.abs(seg_v) > 1e-3]
        ref = M.rms_db(voiced) if len(voiced) > SR * 0.1 else voice_db
        act = x[np.abs(x) > 0.02 * np.max(np.abs(x))]
        g = 10 ** ((ref + e['rel'] - M.rms_db(act)) / 20)
        sfx[k0:k0 + len(x)] += x * g
        rows.append((e['t'], e['start'], e['label'], e['rel'], 20 * np.log10(g)))
    sf.write(OUT / 'sfx_track.wav', sfx[:int(DUR * SR)], SR, subtype='PCM_24')
    mix = vtrack + sfx
    raw = OUT / 'miks_raw.wav'; sf.write(raw, mix[:int(DUR * SR)], SR, subtype='FLOAT')
    dst = VDIR / 'miks.wav'
    r = subprocess.run([FF, '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FF, '-y', '-v', 'error', '-i', str(raw), '-af', af, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s24le', str(dst)], check=True)
    L = ['# SFX — "Ya bir sivrisinek senin boyunda olsaydı?" İNGİLİZCE sürüm (project-en + kullanıcının İngilizce kaydı)', '',
         'Üretim: `scripts/sfx_miks_en.py` (zamanlar `project-en/src/shots.js` ile aynı formüllerle `ses/en/kelimeler.trmap.json`\'dan).',
         'Kaynak: Earshot bankası (`social sfx sfx render`, yerel/ücretsiz) + numpy prosedürel sentez (`scripts/sfx_miks.py` fonksiyonları +',
         'yorgan hışırtısı). Dosyalar: `ses/sfx-en/*.wav`, SFX izi `ses/sfx-en/sfx_track.wav`.',
         'Seviye: her efekt aynı penceredeki konuşma RMS\'inin "hedef" dB altına oturtulur (hepsi ≤ -15 dB); müzik YOK.',
         'Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP).', '',
         '| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |', '|---|---|---|---|']
    for t, s0, lab, rel, gdb in sorted(rows):
        L.append(f'| {t:.2f} | {max(0, s0):.2f} | {lab} | {rel:+.0f} dB |')
    (JOB / 'SFX-en.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(len(rows), 'efekt; miks ->', dst, '| ham', m['input_i'], 'LUFS', m['input_tp'], 'dBTP')
    for t, s0, lab, rel, gdb in sorted(rows): print(f'{t:6.2f} {lab}  gain {gdb:+.1f} dB')
