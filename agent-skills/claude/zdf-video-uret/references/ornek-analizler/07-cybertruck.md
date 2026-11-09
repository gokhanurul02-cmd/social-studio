# Cybertruck "kaç tane gerekir" analizi

Kaynak: `jobs/cybertruck-rebuild-v1/reference-source.mp4` · Analiz tarihi: 2026-11-09 · Araç sürümü: `ea4426d` (main, origin'den 5 commit önde)
Ham ölçümler: `jobs/20261109-cybertruck-skilltest/analysis/` · Gözle doğrulama kareleri: `inspect/`

> Not: Bu analiz `video-analiz` skill'inin deneme koşusudur. Aynı kaynak için `jobs/cybertruck-rebuild-v1/analysis` zaten vardı; skill "yeniden kullan" diyor, ama yeni araç dosyalarını test etmek için bilerek baştan analiz edildi.

## 1. Teknik kimlik
| Alan | Değer | Kaynak |
|---|---|---|
| Çözünürlük | 2160×3840 (9:16, 4K) | [ölçüm: probe.json] |
| fps (rasyonel) | 30000/1001 | [ölçüm: probe.json] |
| Süre / kare sayısı | 22.155 s / 664 kare | [ölçüm: analysis.json] |
| Video kodek | AV1 | [ölçüm: probe.json] |
| Ses | var; entegre **-8.2 LUFS**, true peak **+1.5 dBTP** (clip), LRA 1.3 LU | [ölçüm: ffmpeg ebur128, elle — araç entegre LUFS/TP yazmıyor] |
| Muhtemel üretim motoru | 3D sahne: Blender (Eevee) veya Unreal render; kurgu + altyazı + kart çevirme: CapCut [tahmin] | gerekçe: Tron tarzı ışıklı ızgara zemin, HDRI bulut gökyüzü, Mixamo benzeri rig'li karakterler (ilk karede yarı T-poz kollar), kalabalıkta instancing, hareket bulanıklığı + kromatik sapma. Kart çevirme sırasında altyazı dönmüyor (kare 0234–0243) → altyazı ve geçiş kurgu yazılımında eklenmiş. Altyazı fontu/kontur stili CapCut otomatik altyazısına benziyor. |

## 2. Formül
Saçma bir "birim karşılaştırması" üç kez tekrarlanıyor: bir Cybertruck çiftini çekmek için kaç bebek, kaç anakonda, kaç Dwayne Johnson gerekir. Her turda tek bir figür gösteriliyor, sonra kamera geri ve yukarı çekilirken figür sayısı patlıyor ve sayı altyazıda tek başına beliriyor (5000 → 160 → 1.5). Sayılar azalırken "güç" artıyor; son tur ünlü bir kişiyle ve en küçük sayıyla ters köşe yapıyor. Gerilim "kaç tane?" sorusundan, ödül de sayı + dev kalabalık görüntüsünden geliyor.

## 3. Hook (0–3 s)
- İlk kare (0000): altyazı yok. Bezli bebek, iki Cybertruck'ın arka tamponu önünde, parmağını emiyor; alçak açı, bebek göz hizası. İlk ses: anlatıcı doğrudan "If you…" ile başlıyor, müzik altta. [ölçüm: kare 0000, transcript.json]
- İlk metin: "If you" kare **0001** (0.033 s) — kare 0000 boş. İlk cümle: "If you strapped a baby to a pair of Cybertrucks to pull them, you would need 5000 of them" [ölçüm: capchange taraması, transcript.json]
- İlk 3 sn: sert kesim yok; 0.30 s'de koşum takımı bebeğin üstüne "pop" ile beliriyor (kare 0009–0012), 1.40–1.70 s hızlı geri-yukarı kamera çekilişi (Cybertruck'lar ortaya çıkıyor), 2.40–2.60 s hareket bulanık hızlı kamera geçişi alçak arka açıya. 3 sn içinde 6 altyazı grubu. [ölçüm: inspect/strip_0.jpg]
- Merak boşluğu: "Bir bebek bu kamyonları çekebilir mi, kaç tane lazım?" Sayı 4.27 s'de veriliyor.

## 4. Anlatı akışı
| # | Zaman (s / kare) | Beat | Amaç |
|---|---|---|---|
| 1 | 0.000–4.270 / 0000–0127 | Bebek tanıtılır, ipe bağlanır, kamyonlar gösterilir | kur |
| 2 | 4.271–7.473 / 0128–0223 | "5000 of them": kalabalık patlaması + uzun geri çekiliş | ödül 1 |
| 3 | 7.474–11.244 / 0224–0336 | Kart çevirme, anakonda girer, tek yılan kamyonda | tırmandır |
| 4 | 11.245–14.914 / 0337–0446 | "160": yılanlar çoğalır, geri-yukarı çekiliş | ödül 2 |
| 5 | 14.915–18.784 / 0447–0562 | "But if you got Dwayne the Rock Johnson": hızlı dalış, yakın plan, ip/yılan yakalar | ters köşe |
| 6 | 18.785–22.155 / 0563–0664 | "just one and a half of him": ikinci küçük figür, kamyonlar kıpırdar | ödül 3 / kapanış |
Döngü (loop) kurgusu yok; son kare kamyonlar hareket halinde, altyazı 21.588 s'de (kare 0647) kalkıyor. [ölçüm: capchange]

## 5. Shot tablosu
Video tek kamera dilinde akıyor; "shot" burada kamera sürekliliğinin koptuğu yerlere göre bölündü. ±3 kare işaretli olanlar 10 fps şeritten [ölçüm: inspect/strip_*.jpg, ±0.1 s]; diğerleri kare kare.

| # | Başlangıç–bitiş (s) | Kareler | İçerik | Kamera | Geçiş (girişte) | Ekran metni | Ses olayı |
|---|---|---|---|---|---|---|---|
| 1 | 0.000–1.368 | 0000–0040 | Bebek, koşum takımı beliriyor, kamyon tamponları arkada | bebek göz hizası, orta plan, normal lens hissi; 0.9 s'den sonra hafif geri kayma | — (açılış) | If you / strapped a / baby | anlatım başlar |
| 2 | 1.368–2.400 | 0041–0072 (±3) | İki Cybertruck arkadan, bebek ipe bağlı küçük figür | 1.40→1.70 s hızlı geri + yukarı çekiliş ease-out, sonra sabit geniş plan | kamera içi hızlı çekiliş | to a pair of / Cybertrucks | — |
| 3 | 2.400–4.100 | 0072–0123 (±3) | Kamyon altından alçak arka açı, bebek ipleri çekerek kameraya emekliyor | 2.40→2.60 s hareket bulanık hızlı geçiş, sonra alçak açı, geniş lens hissi, neredeyse sabit | whip/hızlı kamera hareketi | to pull them / you would need | 3.2 s onset [ölçüm: audio_analysis.json] |
| 4 | 4.100–7.808 | 0123–0233 | Bebek çoğalır, yüzlerce ipli bebek, sonra ufka kadar uzanan "halı" | 4.10→4.30 s ileri zoom patlaması (yoğun motion blur, kromatik sapma, kırmızı ip çizgileri), 4.3→7.0 s uzun geri + yukarı çekiliş ease-out, 7.0–7.8 sabit | zoom burst (ffmpeg scene skoru 0.32 @4.104 s) | 5000 of them / just to / make them move / Now if you did | müzik altta |
| T1 | 7.808–8.108 | 0234–0243 | **3D kart çevirme** (dikey eksen), siyah zemin, kare 0237'de kenardan görünüm | — | kurgu geçişi | altyazı dönmeden üstte kalır | — |
| 5 | 7.941–10.250 | 0238–0307 (±3) | Zemin seviyesinden yan açı, bebekler emekler; anakonda soldan girer, 9.0 s'den itibaren yılan gövdesi ön planda | alçak yan açı, sığ alan derinliği, yılanla birlikte hafif takip | T1 | the same thing / with anacondas / it would take | — |
| T2 | 10.25–10.58 | ~0307–0317 (±3) | **3D kart çevirme** (T1 ile aynı) | — | kurgu geçişi | it would take | ffmpeg scene skoru 0.20 @10.344 s |
| 6 | 10.58–15.45 | ~0317–0463 (±3) | Kamyonlar arkadan, tek yılan → 160 yılan, ip çizgileri | 11.2→14.5 s yavaş geri + yukarı çekiliş ease-in-out, hafif motion blur | T2 | at least / 160 / of the giant snakes / to pull the truck / But if you got | — |
| 7 | 15.45–19.386 | ~0463–0580 | 15.45–15.6 hızlı ileri dalış, Dwayne Johnson benzeri karakter yakın planda kameraya işaret ediyor, sonra orta plan; yılanları yakalar, eğilir, kalkar, yürür | 15.4→15.6 whip/dalış (yoğun blur), 16.0→16.6 geri çekiliş, sonra önden orta-geniş sabit | whip | Dwayne the Rock / Johnson / to tow the trucks / you would need / just one | — |
| 8 | 19.386–22.155 | 0581–0664 | Sol yanda ikinci, küçük koyu kostümlü figür ("yarım"), kamyonlar yerinden oynar, zeminde kırmızı izler | 3/4 açı, hafif yüksek, yavaş yanal kayma | kesim değil; kamera açısı 19.2–19.4 arasında yumuşak dönüş [tahmin] | and a half of him / to get them / rolling | 21.6 s'den sonra müzik söner, 22.1 s sessizlik |

## 6. Ritim
- Kamera sürekliliğine göre 8 bölüm: ortalama 2.77 s, medyan 2.70 s, en kısa 1.03 s (#2), en uzun 4.87 s (#6). [ölçüm: tablo; araç: 1 sahne, 0 kesim — yanlış]
- Gerçek kurgu geçişi 2 (kart çevirme), kamera içi hızlı geçiş 4 (1.4, 2.4, 4.1, 15.45 s). ≈0.27 geçiş/s. En yoğun bölüm 0–4.3 s (3 hızlı hareket + 8 altyazı grubu).
- Altyazı ritmi asıl tempo: 26 grup / 21.555 s → grup başına ortalama 0.83 s (en kısa "at least" 0.367 s, en uzun "5000 of them" 1.535 s). [ölçüm: capchange]
- Kesim–beat hizası: ölçülemedi (librosa yok, beat listesi boş). [bilinmiyor]
- Enerji: konuşma boyunca RMS -5…-13 dBFS düz; konuşma boşlukları (7.2–7.5, 14.8–15.0 s) yalnızca ~-22 dBFS müzik yatağı. Görsel tepe noktaları sayı anları: 4.3 s, 11.2 s, 15.5 s. [ölçüm: audio_analysis.json rms_curve]

## 7. Altyazı ve ekran metni
- Font adayları: **Verdana Bold** (1), Tahoma Bold (2), DejaVu Sans Bold (3). Ayırt edici: tek katlı açık kuyruklu "g", geniş "a/e" ve büyük x-yüksekliği Verdana'ya işaret ediyor; Tahoma daha dar olurdu. [ölçüm: inspect/cap_giant.png, tahmin]
- Boyut: 1080×1920 ölçeğinde rakam/büyük harf yüksekliği ≈55 px (satır 1472–1526) → font boyutu ≈76 px, ekran yüksekliğine oran ≈0.040. [ölçüm: kare 0366, f12_2.png]
- Tümü küçük harf ağırlıklı, cümle büyük harfi korunuyor ("Now", "But", özel isimler). Grup başına 1–4 kelime, tek satır, ortalı.
- Renk: beyaz dolgu (#FFFFFF), ince siyah kontur (1080p'de ≈2 px), hafif yumuşak gölge. Vurgu rengi yok; sayılar ("5000", "160") ayrı grup olarak tek başına veriliyor. [ölçüm: cap_giant.png]
- Konum: taban çizgisi y ≈ 0.795 (1526/1920). Alt %20 güvenli alanın tam sınırında — TikTok/Reels açıklama metniyle çakışabilir. [ölçüm]
- Animasyon: yok; grup tek karede değişiyor (kesme). Geçişlerde dönmüyor/bulanmıyor. [ölçüm: kare 0220–0247]
- Değişim kareleri (araç OCR yapamadı; altyazı bandında beyaz piksel maskesi IoU taraması ile elle ölçüldü, kare kare doğrulama 0220–0247):

| # | Kare | s | Metin |
|---|---|---|---|
| 1 | 0001 | 0.033 | If you |
| 2 | 0009 | 0.300 | strapped a |
| 3 | 0027 | 0.901 | baby |
| 4 | 0041 | 1.368 | to a pair of |
| 5 | 0057 | 1.902 | Cybertrucks |
| 6 | 0085 | 2.836 | to pull them |
| 7 | 0109 | 3.637 | you would need |
| 8 | 0128 | 4.271 | 5000 of them |
| 9 | 0174 | 5.806 | just to |
| 10 | 0189 | 6.306 | make them move |
| 11 | 0224 | 7.474 | Now if you did |
| 12 | 0244 | 8.141 | the same thing |
| 13 | 0270 | 9.009 | with anacondas |
| 14 | 0306 | 10.210 | it would take |
| 15 | 0326 | 10.878 | at least |
| 16 | 0337 | 11.245 | 160 |
| 17 | 0375 | 12.513 | of the giant snakes |
| 18 | 0410 | 13.680 | to pull the truck |
| 19 | 0447 | 14.915 | But if you got |
| 20 | 0466 | 15.549 | Dwayne the Rock |
| 21 | 0493 | 16.450 | Johnson |
| 22 | 0509 | 16.984 | to tow the trucks |
| 23 | 0546 | 18.218 | you would need |
| 24 | 0563 | 18.785 | just one |
| 25 | 0581 | 19.386 | and a half of him |
| 26 | 0611 | 20.387 | to get them |
| 27 | 0631 | 21.054 | rolling |
| — | 0647 | 21.588 | (altyazı kalkar) |

Metinler 10 fps şeritlerden okundu; kare numaraları maske taramasından. Altyazılar transcript.json kelime zamanlarıyla uyumlu.

## 8. Görsel stil
- Palet (kare 0366, 6 renk kuantize): #24ACE9 %25, #6EB5E9 %21, #8DC4E9 %16, #5265A6 %13, #4AB1E9 %13, #4A9DE0 %12. Araç tek palet verdi (tek sahne sandığı için): #57C2E8 %34, #31C0E7 %32, #8EC6E8 %24. Sahne bazında: bebek kalabalığı bölümünde kırmızı/mor ip tonları (≈#E04A5A, #6A4FB0) zemini kaplıyor; yılan bölümünde siyah-sarı benek (#1A1A1A / #E8C832) aksan [tahmin, gözle]. [ölçüm: f12_2.png; visual_analysis.json]
- Işık: yumuşak, yüksek güneş, kısa yumuşak gölgeler; parlak gökyüzü, krom kamyonlar ortamı yansıtıyor. Malzeme: PBR (krom, ten, deri). [gözle]
- Karakterler: stilize-gerçekçi 3D, oyun kalitesinde; bebek büyük kafalı; ünlü benzeri karakter gerçek kişiye (Dwayne Johnson) benzetilmiş. Animasyonlar stok mocap hissi (emekleme, işaret etme, eğilme). [tahmin]
- Çevre: sonsuz açık mavi zemin, beyaz ızgara çizgileri, ortada beyaz şerit; ufuk sisli; HDRI bulutlu gökyüzü. Hızlı hareketlerde güçlü motion blur ve kenarda kromatik sapma; yakın plan yılanda sığ alan derinliği.
- Kalabalık: "5000" bölümünde binlerce instanced bebek (ufka kadar), "160" bölümünde ≈60–100 görünen yılan. [gözle tahmin]

## 9. Ses
- Konuşma: yetişkin erkek hissi, enerjik, düz tonlama, **197.7 kelime/dk**; TTS olma ihtimali yüksek (nefes yok, cümle sonları eşit) [tahmin]. Dil İngilizce (araç Türkçe varsayılanına rağmen doğru algıladı). [ölçüm: transcript.json]
- Müzik: konuşma boşluklarında ≈-22 dBFS sürekli yatak; tür/BPM ölçülemedi (librosa yok). 21.6 s'den itibaren sönüyor, 22.1 s'de sessizlik. [ölçüm: rms_curve; BPM bilinmiyor]
- Efektler: araç yalnızca 3.2 s'de bir onset buldu (100 ms RMS, düşük güven). Kalabalık patlaması (4.1 s), dalış (15.45 s) ve kart çevirmelerde whoosh olup olmadığı ayrılamadı. [bilinmiyor]
- Miks: entegre -8.2 LUFS, true peak +1.5 dBTP — clipping var; platform normalizasyonundan önce çok yüksek. Konuşma müziğin ≈10–15 dB üstünde. [ölçüm: ebur128]

## 10. Yeniden kurma planı
- Motor: Three.js (önceki `cybertruck-rebuild-v1` işinde kullanıldı) — instancing ile kalabalık, `seek(t)` ile deterministik kamera. Altyazı ve kart çevirme 3D sahneden bağımsız 2D katman olarak kurulmalı (orijinalde de öyle).
- Katmanlar: zemin ızgarası + gökyüzü (kodla), Cybertruck modeli (hazır asset), bebek / anakonda / güreşçi karakter + animasyonlar (hazır asset veya yeni), ipler (kodla, çizgi), motion blur + kromatik sapma (post-process), altyazı (kodla, Verdana Bold), ses (orijinal veya yeni TTS + müzik).
- Eksik asset: rig'li bebek, anakonda, ünlü benzeri karakter. Ünlü benzerliği hukuken riskli; jenerik "güçlü adam" ile değiştirilmesi önerilir (önerilen değişiklik).
- En zor 3 an: (1) 4.1–7.0 s kalabalık patlaması ve uzun çekiliş (binlerce animasyonlu instance), (2) 8.1–10.2 s yakın plan yılan gövdesi + sığ alan derinliği, (3) 15.45 s dalış ve yakın plan karakter performansı.
- Önizleme: 540p still'ler 0.0, 1.7, 2.8, 4.2, 6.5, 8.0, 9.5, 11.5, 14.0, 15.6, 17.2, 20.5 s; kısa test render 4.0–7.5 s ve 15.2–16.8 s.

## 11. Şablonlaştırılabilir kalıp
- Format: "X'i yapmak için kaç tane Y gerekir?" × 3 tur, her turda daha güçlü bir Y ve daha küçük bir sayı; son tur ters köşe (ünlü/absürt güç).
- Tur yapısı (~7 s): tek figür tanıtımı (≈2 s) → görev bağlamı (≈1.5 s) → sayı altyazısı tek başına + figür çoğalması ve geri-yukarı çekiliş (≈3 s).
- Kamera dili: göz hizası tanıtım → hızlı geri çekiliş reveal → zoom patlaması → uzun ease-out geri+yukarı çekiliş; turlar arası 0.3 s 3D kart çevirme.
- Altyazı: 1–4 kelime, ortalı, beyaz + ince siyah kontur, y≈0.79, sayı her zaman kendi grubunda; animasyonsuz kesme.
- Ses: hızlı (≈200 kelime/dk) tek anlatıcı, alçak müzik yatağı, sonda müzik sönmesi.

## 12. Açık sorular ve sınırlar
- Araç kesim dedektörü (PySceneDetect, eşik 3) **hiç kesim bulmadı**; kart çevirmeler ve whip geçişleri elle bulundu. Shot 5–8 sınırlarının bir kısmı 10 fps şeritten (±3 kare).
- OCR çalışmadı (RapidOCR/PaddleOCR/Tesseract yok); altyazı zamanları elle maske taramasıyla ölçüldü, metinler gözle okundu.
- BPM, beat, kesim–beat hizası ve efekt listesi ölçülemedi (librosa yok).
- Araç kamera hareketini her saniye "mixed" (güven 0.04–0.38) olarak etiketledi; kamera tanımları gözle yazıldı.
- Font kesin değil (Verdana Bold en güçlü aday).
- Shot 8 başındaki açı değişimi kesim mi yumuşak kamera dönüşü mü, kare kare doğrulanmadı.
- Ünlü kişi benzerliği: yeniden kurma ve özgün üretimde kullanıcıyla netleştirilmeli.

---
### Kalite kapısı (references/kalite-kontrol.md → Analiz)
- [x] Çözünürlük, rasyonel fps, süre, kare sayısı ve ses formatı probe'dan alındı (ses kodeki probe'dan; LUFS/TP elle ebur128).
- [~] Her kesim adayı ardışık karelerle doğrulandı, kaçan geçişler eklendi — araç aday vermedi; 10 fps şeritlerle tümü tarandı, T1 kare kare, diğerleri ±3 kare.
- [x] İlk 3 saniye 10 fps incelendi, hook yazıldı.
- [x] Her altyazı değişimi kare numarasıyla yazıldı.
- [x] Font adayları, boyut oranı, konum, kontur ve animasyon ölçüldü.
- [~] Palet hex olarak çıkarıldı — tek kare ölçüldü, diğer sahneler gözle.
- [x] Her shot için kamera açısı, hareket yönü ve easing yazıldı (gözle).
- [~] Konuşma ve LUFS ölçüldü; müzik BPM ve efekt zamanları ölçülemedi.
- [x] Üretim motoru tahmini gerekçeli.
- [x] Ölçüm ve tahmin her satırda ayrıldı.
- [x] SPEC.md ve style.json üretildi, ANALIZ.md'nin bütün bölümleri dolu.
