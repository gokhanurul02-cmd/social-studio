# SFX — "Ya bir sivrisinek senin boyunda olsaydı?" İNGİLİZCE sürüm (project-en + kullanıcının İngilizce kaydı)

Üretim: `scripts/sfx_miks_en.py` (zamanlar `project-en/src/shots.js` ile aynı formüllerle `ses/en/kelimeler.trmap.json`'dan).
Kaynak: Earshot bankası (`social sfx sfx render`, yerel/ücretsiz) + numpy prosedürel sentez (`scripts/sfx_miks.py` fonksiyonları +
yorgan hışırtısı). Dosyalar: `ses/sfx-en/*.wav`, SFX izi `ses/sfx-en/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur (hepsi ≤ -15 dB); müzik YOK.
Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | sivrisinek kanat vızıltısı (alçak, makro) | -26 dB |
| 0.64 | 0.44 | zoom-whoosh geçiş → night0 | -17 dB |
| 1.70 | 1.70 | kanat açılışı vızıltı (büyüme sonu, alçak) | -25 dB |
| 2.05 | 0.28 | büyüme şişme/whoosh (makro → insan boyu) | -18 dB |
| 2.42 | 2.22 | zoom-whoosh geçiş → wake0 | -17 dB |
| 3.36 | 3.16 | zoom-whoosh geçiş → reveal0 | -17 dB |
| 6.60 | 6.60 | yorgan hışırtısı (kafaya çekilir) | -18 dB |
| 7.75 | 7.56 | yorgan çekiş swish katmanı | -20 dB |
| 7.85 | 7.85 | yorgan altında titreme hışırtısı | -21 dB |
| 9.52 | 9.32 | zoom-whoosh geçiş → pierce0 | -17 dB |
| 10.34 | 10.33 | hortum yorganı deler (kumaş thunk) | -17 dB |
| 10.62 | 10.61 | hortum deriye saplanır (thunk) | -16 dB |
| 10.62 | 10.45 | saplanma gövdesi (alçak impact) | -19 dB |
| 11.24 | 11.04 | zoom-whoosh geçiş → x1 | -17 dB |
| 11.91 | 11.91 | pipet slurp (pipetle) | -17 dB |
| 13.48 | 13.48 | kan çekme slurp (tek seferde çeker) | -16 dB |
| 14.88 | 14.68 | zoom-whoosh geçiş → dry0 | -17 dB |
| 14.98 | 14.98 | büzüşme kuru yaprak hışırtısı | -16 dB |
| 17.00 | 17.00 | karın şişmesi balon gerilme | -19 dB |
| 19.16 | 18.98 | kart çevirme flip/swish (ters köşe: kapı) | -16 dB |
| 19.31 | 19.31 | kanat vızıltısı (kapıya yönelirken, alçak) | -24 dB |
| 19.51 | 19.49 | kapıya doğru adım 1 (kitin tık) | -19 dB |
| 19.96 | 19.94 | kapıya doğru adım 2 (kitin tık) | -19 dB |
| 20.41 | 20.39 | kapıya doğru adım 3 (kitin tık) | -19 dB |
| 21.05 | 21.04 | ilk adım (ağır tık) | -18 dB |
| 22.78 | 22.78 | kırılma snap katmanı | -18 dB |
| 22.78 | 22.78 | bacak kırılması crack/snap | -17 dB |
| 23.03 | 23.03 | ikinci bacak kırılır (crack) | -18 dB |
| 24.37 | 24.31 | yere yığılma (thud) | -19 dB |
| 24.52 | 24.52 | yerde kanat çırpınması (alçak vızıltı) | -25 dB |
| 26.16 | 26.03 | kart çevirme flip/swish (gerçeklere geçiş) | -16 dB |
| 29.92 | 29.92 | oksijen sönmesi fizz | -17 dB |
| 31.94 | 31.74 | zoom-whoosh geçiş → sc0 | -17 dB |
| 35.16 | 34.99 | ağırlık oku iner (kısa vuruş) | -18 dB |
| 36.12 | 35.92 | zoom-whoosh geçiş → sc2 | -17 dB |
| 36.94 | 36.94 | bacak kesiti çatlar (crack) | -17 dB |
| 38.30 | 38.10 | zoom-whoosh geçiş → fin0 | -17 dB |
