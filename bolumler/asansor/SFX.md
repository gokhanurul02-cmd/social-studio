# SFX — "Asansörün halatı kopsaydı?" v1 (kullanıcı kaydı + efektler)

Üretim: `scripts/sfx_miks.py` (zamanlar shots.js ile aynı formüllerle kelime zamanlarından). Kaynak: Earshot bankası
(`social sfx sfx render`, kodla üretilen yerel ses bankası) + numpy prosedürel sentez (tel kopma, halat kırbacı, düşüş,
fren ciyaklaması/kıvılcım, klank, bonk, ekran tıkları, titreşim, rüzgâr, uğultu). Dosyalar: `ses/sfx/*.wav`, SFX izi `ses/sfx/sfx_track.wav`.
Seviye: her efekt aynı penceredeki konuşma RMS'inin "hedef" dB altına oturtulur; **müzik yok**; anlatı kaydı değiştirilmez.
Ölçüm: konuşmalı pencerelerde konuşma − efekt RMS farkı **19.0 dB**; konuşma RMS − efekt (aktif) RMS **18.6 dB**.
Final miks: `ses/kullanici/miks.wav` (anlatı + SFX, iki geçişli loudnorm linear → -14 LUFS, ≤ -1.5 dBTP hedef).

| Vurgu (s) | Başlangıç (s) | Efekt | Hedef (konuşmaya göre) |
|---|---|---|---|
| 0.00 | 0.00 | kabin/havalandırma uğultusu (alçak) | -26.0 dB |
| 1.22 | 1.02 | zoom-whoosh geçiş → snap | -18.0 dB |
| 1.27 | 1.27 | çelik teller tek tek kopar (ting ting) | -15.0 dB |
| 2.64 | 2.44 | zoom-whoosh geçiş → drop0 | -18.0 dB |
| 2.66 | 2.52 | halat kopup yukarı kırbaçlanır | -14.0 dB |
| 2.69 | 2.69 | düşüş gürültüsü + ray tıkırtısı | -17.0 dB |
| 3.36 | 3.16 | zoom-whoosh geçiş → fall | -18.0 dB |
| 4.90 | 4.70 | zoom-whoosh geçiş → xstom | -18.0 dB |
| 4.90 | 4.90 | düşüş rüzgârı (mide) | -20.0 dB |
| 7.04 | 6.84 | zoom-whoosh geçiş → phone | -18.0 dB |
| 7.04 | 7.04 | düşüş gürültüsü (alçak, arka) | -24.0 dB |
| 8.04 | 8.04 | klavye tıkları | -20.0 dB |
| 9.11 | 9.10 | mesaj gönderildi (pop) | -17.0 dB |
| 11.22 | 11.03 | zoom-whoosh geçiş → crouchB | -18.0 dB |
| 13.02 | 12.84 | kart çevirme swish (ters köşe) | -16.0 dB |
| 13.22 | 13.22 | güvenlik freni ciyaklaması + kıvılcım | -15.0 dB |
| 15.53 | 15.53 | kabin aniden durur (klank) | -14.0 dB |
| 17.16 | 16.86 | zıplama whoosh | -18.0 dB |
| 17.60 | 17.40 | zoom-whoosh geçiş → bonk | -18.0 dB |
| 17.94 | 17.94 | kafa tavana çarpar (bonk) | -13.0 dB |
| 18.02 | 17.67 | yıldızlar (parıltı) | -21.0 dB |
| 19.02 | 18.84 | kart çevirme swish (mekanizma) | -17.0 dB |
| 19.02 | 19.02 | regülatör kasnağı hızlanır | -21.0 dB |
| 21.11 | 21.10 | ağırlıklar açılır, mandal tık | -15.0 dB |
| 21.54 | 21.34 | zoom-whoosh geçiş → clamp | -18.0 dB |
| 21.96 | 21.96 | çeneler raya kenetlenir: ciyaklama + kıvılcım | -14.0 dB |
| 23.06 | 23.06 | kabin raylarda durur (klank) | -15.0 dB |
| 23.16 | 22.96 | zoom-whoosh geçiş → final | -18.0 dB |
| 25.00 | 25.00 | son oturma (alçak klank, sert son) | -18.0 dB |
