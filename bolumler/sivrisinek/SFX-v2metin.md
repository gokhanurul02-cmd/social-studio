# SFX — "Ya bir sivrisinek senin boyunda olsaydı?" METIN v2 (önizleme-v1 sahneleri + kullanıcı kaydı v2)

Üretim: `scripts/sfx_miks_v2metin.py` (zamanlar `project-v2metin/src/shots.js` ile aynı formüllerle `ses/kullanici-v2/kelimeler.json`'dan).
Kaynak: Earshot bankası (`social sfx sfx render`, yerel/ücretsiz) + numpy prosedürel sentez (`scripts/sfx_miks.py` fonksiyonları +
yorgan hışırtısı). Dosyalar: `ses/sfx-v2metin/*.wav`, SFX izi `ses/sfx-v2metin/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur (hepsi ≤ -15 dB); müzik YOK.
Final miks: `ses/kullanici-v2/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | sivrisinek kanat vızıltısı (alçak, makro) | -25 dB |
| 1.36 | 1.16 | zoom-whoosh geçiş → night0 | -17 dB |
| 2.30 | 2.30 | kanat açılışı vızıltı (büyüme sonu, alçak) | -24 dB |
| 2.65 | 1.00 | büyüme şişme/whoosh (makro → insan boyu) | -18 dB |
| 3.10 | 2.90 | zoom-whoosh geçiş → wake0 | -17 dB |
| 4.44 | 4.24 | zoom-whoosh geçiş → reveal0 | -17 dB |
| 7.86 | 7.86 | yorgan hışırtısı (kafaya çekilir) | -15 dB |
| 8.51 | 8.32 | yorgan çekiş swish katmanı | -18 dB |
| 8.61 | 8.61 | yorgan altında titreme hışırtısı | -21 dB |
| 10.16 | 9.96 | zoom-whoosh geçiş → pierce0 | -17 dB |
| 10.84 | 10.83 | hortum yorganı deler (kumaş thunk) | -17 dB |
| 11.08 | 11.07 | hortum deriye saplanır (thunk) | -16 dB |
| 11.09 | 10.91 | saplanma gövdesi (alçak impact) | -19 dB |
| 11.78 | 11.58 | zoom-whoosh geçiş → x1 | -17 dB |
| 12.95 | 12.95 | pipet slurp (pipetle) | -17 dB |
| 14.46 | 14.46 | kan çekme slurp (tek seferde çeker) | -16 dB |
| 15.70 | 15.50 | zoom-whoosh geçiş → dry0 | -17 dB |
| 15.80 | 15.80 | büzüşme kuru yaprak hışırtısı | -16 dB |
| 17.82 | 17.82 | karın şişmesi balon gerilme | -17 dB |
| 19.96 | 19.78 | kart çevirme flip/swish (ters köşe: kapı) | -16 dB |
| 20.11 | 20.11 | kanat vızıltısı (kapıya yönelirken, alçak) | -24 dB |
| 20.31 | 20.29 | kapıya doğru adım 1 (kitin tık) | -19 dB |
| 20.76 | 20.74 | kapıya doğru adım 2 (kitin tık) | -19 dB |
| 21.21 | 21.19 | kapıya doğru adım 3 (kitin tık) | -19 dB |
| 21.99 | 21.98 | ilk adım (ağır tık) | -18 dB |
| 23.58 | 23.58 | kırılma snap katmanı | -18 dB |
| 23.58 | 23.58 | bacak kırılması crack/snap | -17 dB |
| 23.83 | 23.83 | ikinci bacak kırılır (crack) | -18 dB |
| 24.61 | 24.55 | yere yığılma (thud) | -17 dB |
| 24.76 | 24.76 | yerde kanat çırpınması (alçak vızıltı) | -25 dB |
| 25.72 | 25.59 | kart çevirme flip/swish (gerçeklere geçiş) | -16 dB |
| 30.20 | 30.20 | oksijen sönmesi fizz | -17 dB |
| 31.38 | 31.18 | zoom-whoosh geçiş → sc0 | -17 dB |
| 33.82 | 33.65 | ağırlık oku iner (kısa vuruş) | -18 dB |
| 35.02 | 34.82 | zoom-whoosh geçiş → sc2 | -17 dB |
| 36.04 | 36.04 | bacak kesiti çatlar (crack) | -17 dB |
| 37.08 | 36.88 | zoom-whoosh geçiş → fin0 | -17 dB |
