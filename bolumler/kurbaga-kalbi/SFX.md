# SFX — "Ya bir kurbağanın kalbi sana takılsaydı?" v1 (kullanıcı kaydı + efektler)

Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası
(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (squish, kalp atışları, 100 kalp kaosu, adım,
kalabalık, boing, buz donma/kırılma, conta, buğu, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.
Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **20.0 dB**; konuşma RMS − efekt (aktif) RMS **19.1 dB**.
Final miks: `ses/kullanici/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | minik kurbağa kalbi hızlı atış | -22.0 dB |
| 0.77 | 0.75 | cımbız ıslak dokuya girer (squish) | -16.0 dB |
| 0.80 | 0.79 | cımbız kapanır (metal tık) | -20.0 dB |
| 1.25 | 1.24 | kalp çekilip çıkar (squelch) | -16.0 dB |
| 1.58 | 1.38 | zoom-whoosh geçiş → implant | -18.0 dB |
| 2.24 | 2.04 | zoom-whoosh geçiş → sec1 | -18.0 dB |
| 2.69 | 2.68 | kalp göğse yerleşir (pıt) | -17.0 dB |
| 2.74 | 2.74 | minik kalp göğüste çırpınır (hızlı) | -20.0 dB |
| 3.20 | 3.00 | zoom-whoosh geçiş → xpea | -18.0 dB |
| 3.35 | 3.34 | bezelye belirir (pop) | -18.0 dB |
| 5.82 | 5.62 | zoom-whoosh geçiş → purple | -18.0 dB |
| 5.92 | 5.43 | morarma alçak düşüş | -19.0 dB |
| 7.10 | 6.90 | zoom-whoosh geçiş → rain | -18.0 dB |
| 7.30 | 6.30 | kalpler gökten uçar (whoosh) | -18.0 dB |
| 7.60 | 7.60 | kalpler göğse dolar (pıt pıt) | -17.0 dB |
| 8.88 | 8.69 | zoom-whoosh geçiş → fill | -18.0 dB |
| 9.58 | 9.58 | 100 kalp kaotik çoklu atış | -17.0 dB |
| 10.58 | 10.38 | zoom-whoosh geçiş → pump | -18.0 dB |
| 12.22 | 12.02 | zoom-whoosh geçiş → race1 | -18.0 dB |
| 12.22 | 12.22 | 100 kalp atışı (koşu altında, alçak) | -24.0 dB |
| 12.22 | 12.22 | kalabalık (hafif) | -24.0 dB |
| 12.22 | 12.22 | koşu adımları | -18.0 dB |
| 14.18 | 13.98 | zoom-whoosh geçiş → hurdle | -18.0 dB |
| 15.31 | 14.96 | zıplama whoosh | -17.0 dB |
| 15.36 | 15.35 | kurbağa zıplaması boing | -18.0 dB |
| 16.86 | 16.80 | iniş (thud) | -18.0 dB |
| 17.14 | 16.96 | kart çevirme swish (ters köşe) | -16.0 dB |
| 17.14 | 17.14 | kış rüzgârı (alçak) | -24.0 dB |
| 17.19 | 17.19 | buz donma çatırtısı | -17.0 dB |
| 19.08 | 18.88 | zoom-whoosh geçiş → heartA | -18.0 dB |
| 19.08 | 19.08 | kalp atışı (kesit, yavaş) | -18.0 dB |
| 20.54 | 20.54 | oda 1 parlar (tık) | -19.0 dB |
| 20.68 | 20.68 | oda 2 parlar (tık) | -19.0 dB |
| 20.98 | 20.98 | oda 3 parlar (tık) | -19.0 dB |
| 21.94 | 21.93 | kan karışır (sıvı çalkantı) | -19.0 dB |
| 23.14 | 22.94 | zoom-whoosh geçiş → frogsnow | -18.0 dB |
| 24.12 | 24.12 | kurbağa donar (buz çatırtısı) | -17.0 dB |
| 25.02 | 24.67 | donmuş kalp (buzlu parıltı) | -21.0 dB |
| 25.02 | 24.82 | zoom-whoosh geçiş → frozenx | -18.0 dB |
| 25.97 | 25.96 | buz kırılır (bahar) | -16.0 dB |
| 26.72 | 26.72 | kalp yeniden atar (tık/thump) | -14.5 dB |
| 27.02 | 26.84 | kart çevirme swish (buzdolabı) | -16.0 dB |
| 27.02 | 27.02 | buzdolabı uğultusu (alçak) | -25.0 dB |
| 29.20 | 29.00 | zoom-whoosh geçiş → out | -18.0 dB |
| 29.22 | 28.90 | buzdolabı kapağı/conta açılma | -16.0 dB |
| 29.25 | 29.25 | buğu fısıltısı | -19.0 dB |
| 30.34 | 30.14 | zoom-whoosh geçiş → spring | -18.0 dB |
| 30.34 | 30.34 | bahar pisti koşu adımları | -18.0 dB |
| 30.34 | 30.34 | kalabalık (hafif) | -25.0 dB |
