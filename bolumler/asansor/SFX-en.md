# SFX — "Asansörün halatı kopsaydı?" v1 (kullanıcı kaydı + efektler)

Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası
(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (tel kopma, halat kırbacı, düşüş,
fren ciyaklaması/kıvılcım, klank, bonk, ekran tıkları, titreşim, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.
Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **18.7 dB**; konuşma RMS − efekt (aktif) RMS **18.5 dB**.
Final miks: `ses/en/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | kabin/havalandırma uğultusu (alçak) | -26.0 dB |
| 1.24 | 1.04 | zoom-whoosh geçiş → snap | -18.0 dB |
| 1.29 | 1.29 | çelik teller tek tek kopar (ting ting) | -15.0 dB |
| 2.78 | 2.58 | zoom-whoosh geçiş → drop0 | -18.0 dB |
| 2.80 | 2.65 | halat kopup yukarı kırbaçlanır | -14.0 dB |
| 2.83 | 2.83 | düşüş gürültüsü + ray tıkırtısı | -17.0 dB |
| 3.66 | 3.46 | zoom-whoosh geçiş → fall | -18.0 dB |
| 6.16 | 5.96 | zoom-whoosh geçiş → xstom | -18.0 dB |
| 6.16 | 6.16 | düşüş rüzgârı (mide) | -20.0 dB |
| 8.18 | 7.98 | zoom-whoosh geçiş → phone | -18.0 dB |
| 8.18 | 8.18 | düşüş gürültüsü (alçak, arka) | -24.0 dB |
| 9.42 | 9.42 | klavye tıkları | -20.0 dB |
| 10.01 | 10.00 | mesaj gönderildi (pop) | -17.0 dB |
| 12.32 | 12.13 | zoom-whoosh geçiş → crouchB | -18.0 dB |
| 13.68 | 13.50 | kart çevirme swish (ters köşe) | -16.0 dB |
| 13.88 | 13.88 | güvenlik freni ciyaklaması + kıvılcım | -15.0 dB |
| 15.79 | 15.79 | kabin aniden durur (klank) | -14.0 dB |
| 17.10 | 16.80 | zıplama whoosh | -18.0 dB |
| 17.92 | 17.72 | zoom-whoosh geçiş → bonk | -18.0 dB |
| 18.16 | 18.16 | kafa tavana çarpar (bonk) | -13.0 dB |
| 18.24 | 17.89 | yıldızlar (parıltı) | -21.0 dB |
| 19.72 | 19.54 | kart çevirme swish (mekanizma) | -17.0 dB |
| 19.72 | 19.72 | regülatör kasnağı hızlanır | -21.0 dB |
| 22.25 | 22.24 | ağırlıklar açılır, mandal tık | -15.0 dB |
| 22.54 | 22.34 | zoom-whoosh geçiş → clamp | -18.0 dB |
| 22.94 | 22.94 | çeneler raya kenetlenir: ciyaklama + kıvılcım | -14.0 dB |
| 24.70 | 24.70 | kabin raylarda durur (klank) | -15.0 dB |
| 24.80 | 24.60 | zoom-whoosh geçiş → final | -18.0 dB |
| 26.22 | 26.21 | son oturma (alçak klank, sert son) | -18.0 dB |
