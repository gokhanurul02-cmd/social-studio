# SFX — "Ya bir kurbağanın kalbi sana takılsaydı?" v1 (kullanıcı kaydı + efektler)

Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası
(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (squish, kalp atışları, 100 kalp kaosu, adım,
kalabalık, boing, buz donma/kırılma, conta, buğu, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.
Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **20.1 dB**; konuşma RMS − efekt (aktif) RMS **19.3 dB**.
Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | minik kurbağa kalbi hızlı atış | -22.0 dB |
| 0.73 | 0.71 | cımbız ıslak dokuya girer (squish) | -16.0 dB |
| 0.76 | 0.75 | cımbız kapanır (metal tık) | -20.0 dB |
| 1.23 | 1.22 | kalp çekilip çıkar (squelch) | -16.0 dB |
| 1.46 | 1.26 | zoom-whoosh geçiş → implant | -18.0 dB |
| 2.22 | 2.02 | zoom-whoosh geçiş → sec1 | -18.0 dB |
| 2.67 | 2.66 | kalp göğse yerleşir (pıt) | -17.0 dB |
| 2.72 | 2.72 | minik kalp göğüste çırpınır (hızlı) | -20.0 dB |
| 2.94 | 2.74 | zoom-whoosh geçiş → xpea | -18.0 dB |
| 3.09 | 3.08 | bezelye belirir (pop) | -18.0 dB |
| 6.06 | 5.86 | zoom-whoosh geçiş → purple | -18.0 dB |
| 6.16 | 5.67 | morarma alçak düşüş | -19.0 dB |
| 7.46 | 7.26 | zoom-whoosh geçiş → rain | -18.0 dB |
| 7.66 | 6.66 | kalpler gökten uçar (whoosh) | -18.0 dB |
| 7.96 | 7.96 | kalpler göğse dolar (pıt pıt) | -17.0 dB |
| 8.78 | 8.59 | zoom-whoosh geçiş → fill | -18.0 dB |
| 9.82 | 9.82 | 100 kalp kaotik çoklu atış | -17.0 dB |
| 10.44 | 10.24 | zoom-whoosh geçiş → pump | -18.0 dB |
| 12.36 | 12.16 | zoom-whoosh geçiş → race1 | -18.0 dB |
| 12.36 | 12.36 | 100 kalp atışı (koşu altında, alçak) | -24.0 dB |
| 12.36 | 12.36 | kalabalık (hafif) | -24.0 dB |
| 12.36 | 12.36 | koşu adımları | -18.0 dB |
| 14.10 | 13.90 | zoom-whoosh geçiş → hurdle | -18.0 dB |
| 15.19 | 14.84 | zıplama whoosh | -17.0 dB |
| 15.24 | 15.23 | kurbağa zıplaması boing | -18.0 dB |
| 17.02 | 16.96 | iniş (thud) | -18.0 dB |
| 17.30 | 17.12 | kart çevirme swish (ters köşe) | -16.0 dB |
| 17.30 | 17.30 | kış rüzgârı (alçak) | -24.0 dB |
| 17.35 | 17.35 | buz donma çatırtısı | -17.0 dB |
| 19.80 | 19.60 | zoom-whoosh geçiş → heartA | -18.0 dB |
| 19.80 | 19.80 | kalp atışı (kesit, yavaş) | -18.0 dB |
| 21.60 | 21.60 | oda 1 parlar (tık) | -19.0 dB |
| 21.75 | 21.75 | oda 2 parlar (tık) | -19.0 dB |
| 21.90 | 21.90 | oda 3 parlar (tık) | -19.0 dB |
| 23.42 | 23.40 | kan karışır (sıvı çalkantı) | -19.0 dB |
| 24.84 | 24.64 | zoom-whoosh geçiş → frogsnow | -18.0 dB |
| 25.74 | 25.74 | kurbağa donar (buz çatırtısı) | -17.0 dB |
| 26.92 | 26.57 | donmuş kalp (buzlu parıltı) | -21.0 dB |
| 26.92 | 26.72 | zoom-whoosh geçiş → frozenx | -18.0 dB |
| 28.19 | 28.19 | buz kırılır (bahar) | -16.0 dB |
| 28.66 | 28.66 | kalp yeniden atar (tık/thump) | -14.5 dB |
| 29.82 | 29.64 | kart çevirme swish (buzdolabı) | -16.0 dB |
| 29.82 | 29.82 | buzdolabı uğultusu (alçak) | -25.0 dB |
| 31.54 | 31.34 | zoom-whoosh geçiş → out | -18.0 dB |
| 31.56 | 31.24 | buzdolabı kapağı/conta açılma | -16.0 dB |
| 31.59 | 31.59 | buğu fısıltısı | -19.0 dB |
| 32.60 | 32.40 | zoom-whoosh geçiş → spring | -18.0 dB |
| 32.60 | 32.60 | bahar pisti koşu adımları | -18.0 dB |
| 32.60 | 32.60 | kalabalık (hafif) | -25.0 dB |
