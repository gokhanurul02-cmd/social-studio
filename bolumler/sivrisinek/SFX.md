# SFX — "Ya bir sivrisinek senin boyunda olsaydı?" v2 (kullanıcı kaydı + efektler)

Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası
(`social sfx sfx render`, kodla üretilen 201 ses, ücretsiz/yerel) + bankada olmayanlar için numpy prosedürel sentez
(slurp, balon gerilme, kuru yaprak, vızıltı, fizz, crack gövdesi). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur; müzik yatağı YOK.
Final miks: `ses/kullanici/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | sivrisinek kanat vızıltısı (alçak) | -25 dB |
| 1.83 | 0.98 | büyüme şişme/whoosh (makro → insan boyu) | -18 dB |
| 2.52 | 2.32 | zoom-whoosh geçiş → reveal0 | -17 dB |
| 4.76 | 4.56 | zoom-whoosh geçiş → pierce0 | -17 dB |
| 5.43 | 5.41 | hortum deriye saplanma (thunk) | -16 dB |
| 5.43 | 5.26 | saplanma gövdesi (alçak impact) | -19 dB |
| 5.67 | 5.67 | kan çekme slurp/pipet | -16 dB |
| 6.26 | 6.26 | karın şişmesi balon gerilme | -17 dB |
| 7.16 | 6.96 | zoom-whoosh geçiş → x1 | -17 dB |
| 11.08 | 10.88 | zoom-whoosh geçiş → dry0 | -17 dB |
| 11.13 | 11.13 | büzüşme kuru yaprak hışırtısı | -16 dB |
| 12.30 | 12.12 | kart çevirme flip/swish (ters köşe) | -16 dB |
| 12.45 | 12.45 | kanat vızıltısı (kapıya yönelirken, alçak) | -23 dB |
| 14.12 | 13.99 | kart çevirme flip/swish (gerçeklere geçiş) | -16 dB |
| 16.38 | 16.18 | zoom-whoosh geçiş → tr1 | -17 dB |
| 21.48 | 21.48 | oksijen sönmesi fizz | -17 dB |
| 23.24 | 23.04 | zoom-whoosh geçiş → legsA | -17 dB |
| 24.76 | 24.56 | zoom-whoosh geçiş → sc0 | -17 dB |
| 26.98 | 26.81 | ağırlık oku iner (kısa vuruş) | -18 dB |
| 28.12 | 27.92 | zoom-whoosh geçiş → sc2 | -17 dB |
| 29.26 | 29.26 | bacak kesiti çatlar (crack) | -17 dB |
| 30.00 | 29.80 | zoom-whoosh geçiş → legsB | -17 dB |
| 31.38 | 31.38 | kırılma snap katmanı | -18 dB |
| 31.38 | 31.38 | bacak kırılması crack/snap | -17 dB |
| 31.63 | 31.63 | ikinci bacak kırılır (crack) | -18 dB |
| 33.14 | 33.08 | yere yığılma (thud) | -17 dB |
| 33.66 | 33.38 | zoom-whoosh geçiş → fin0 | -17 dB |
