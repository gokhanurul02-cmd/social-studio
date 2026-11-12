# "How Long Are Your Blood Vessels" analizi

Kaynak: `jobs/zdf/zdf-05-blood-vessels/analysis/proxy-540p.mp4` (orijinal 1296×2304, 9:16, AV1, 29.97 fps, 4.3 Mbps) · 39.44 s · 1182 kare · İngilizce · kanal: Zack D. Films
Ölçümler: `analysis/` (transcript, transitions, onscreen_text, audio_analysis, visual_analysis, composition) · Gözle doğrulama: `inspect/part0.jpg` (kare 0–550), `part1.jpg` (560–1110), `part2.jpg` (1120–1180), her 10. kare; sık kontrol `d1.jpg` (520–575, her 3. kare), `d2.jpg` (700–770, her 3. kare). Tile etiketi kaynak kare değil tile sırasıdır: kare = dilim başlangıcı + 10×etiket.
Etiketler: **[ö]** ölçüm, **[g]** kareden gözle doğrulandı, **[t]** tahmin.

## 1. Kısa özet
Tek cümlelik bir "ölçek şakası": kan damarlarının hepsini çıkarıp uç uca eklesen ne kadar uzar? Seyirci önce "şu kadar kısa bir ip" bekletiliyor (6.9–8.9 s), sonra damarlar **New York'tan başlayıp ABD'yi, Grand Canyon'u, Pasifik'i, Japonya'yı, Asya'yı, Avrupa'yı geçerek** dünyayı 2–4 kez sarıyor. Formül: **Tek görsel metafor (kırmızı çizgi) + sürekli ilerleyen kamera = tek hareketle bir coğrafi yolculuk**; konuşma duraksız, her 0.9 s'de yeni altyazı. Dönüş yok, ters köşe yok; yapı "beklenti küçük → gerçek devasa" ölçek patlaması. Kapanış döngü değil, sayı vurgusu ("2 to 4 times over") üzerinde siyaha düşen küre.

## 2. Teknik kimlik
| Alan | Değer | Kaynak |
|---|---|---|
| Süre / kare | 39.44 s, 1182 kare, 29.97 fps, 1296×2304 | [ö] probe.json |
| Ses | entegre **−12.3 LUFS**, true peak **+0.2 dBTP** (hafif clip), LRA 2.4 LU | [ö] |
| Konuşma | 118 kelime, **179.5 kelime/dk** (konuşma aralığında 181.9), konuşma oranı %98.7, 0.15 s'den uzun duraklama **yok** | [ö] |
| Müzik / efekt | konuşma dışı tek boşluk son 0.52 s: bed −41.9 dBFS (fiilen sessiz). `sfx_candidates` boş; tek güçlü "impact" onset 33.25 s (≈kelime "way" sonrası, vessel ucunun ekrana girdiği an). Müzik yatağı **doğrulanamadı** | [ö], kulakla [t] |
| Ses çıkışı | son sözden (38.92) sonra 39.0–39.4 s arası 0.4 s'lik fade-out | [ö] |
| Geçiş | tool 14 geçiş (0.355/s). Gözle: gerçek kurgu sınırı ≈6 (8.98 flip, 10.0 kesme, 12.45 kesme, 17.7–18.1 çözülme+zoom, 30.7 flip, ≈39.1 siyaha çıkış), kalanı kamera içi whip/burst. Bkz. §10 | [ö]+[g] |
| Altyazı | 43 grup (+1 sahne yazısı), ortalama **0.88–0.91 s**, ortalama 2.65 kelime/grup (1–5), beyaz #fdfeff + ince siyah kontur, y≈0.795 | [ö] |
| Kamera | 24 kamera segmenti; 6 sabit, kalanı tilt/pan/dolly | [ö] |
| Üretim | 3D render (Blender/Unreal sınıfı): fotogerçekçi insan rig'i, damar ağı sim'i, düşük-poligon (lowpoly) ABD haritası, fotogerçekçi dünya küresi; altyazı kurguda | [t] gerekçe: PBR deri/kot, aynı zemin/gökyüzü setinin tekrarı |

## 3. Saniye saniye akış
fps 29.97: kare ≈ saniye × 30. Her satırdaki "ekranda" kareden gözle yazıldı.

| Zaman (s) | Kare | Söylenen | Ekranda | Kamera / geçiş | Amaç |
|---|---|---|---|---|---|
| 0.00–0.03 | 0–1 | — | Mavi gökyüzü, yeşil futbol sahası; lacivert tişört + açık mavi kot giyen, kısa kahverengi saçlı fotogerçekçi adam kollar iki yanda, ayakta. Altyazı henüz yok [g] | pan_right başlıyor [ö] | Karakteri ve setin "oyun alanı" olduğunu 1 karede tanıt |
| 0.03–0.47 | 1–14 | "If you" | **Kırmızı damar ağı adamın içinden hayalet gibi çıkıyor** (f10'da adamla üst üste, f20'de yanında ayrı duruyor); adam ağzı açık şaşırıyor [g] | pan_right → zoom_out (0.73–1.2) [ö] | **Hook:** ilk 0.3 s'de imkânsız eylem (damarlar vücuttan ayrılıyor), cümle bitmeden |
| 0.47–1.84 | 14–55 | "somehow removed" | Damar vücudu (başı, kolları, bacakları, gövde ağı seçilebilir) adamın yanında dik duruyor, adam bakıyor [g] | static (1.2–3.7) [ö] | Premis: "çıkarılmış damarlar" gerçek nesne olarak sahnede |
| 1.84–3.20 | 55–96 | "all of the blood vessels" | Aynı iki figür yan yana; damar figürü hafifçe titreyip bozulmaya başlıyor (f80) [g] | static | Sayıyı/kapsamı vurgula ("all") |
| 3.20–4.14 | 96–124 | "in your body" | Damarlar dikey bir sütuna doğru buruşup kıvrılıyor (f90–120) [g] | pan_left 3.74–6.0 [ö] | "Sen" dili + hazırlık |
| 4.14–5.71 | 124–171 | "and tied them together" | Kırmızı yumak düğümlenir ve havada asılı kalır; adam yürüyerek uzaklaşıyor, kamera sahayı tilt ile gösteriyor [g] | pan_left, f130'dan itibaren zemin eğiliyor [g] | "Uç uca bağlama" eylemini görselleştir |
| 5.71–6.91 | 171–207 | "you might think" | Kamera aşağı **tilt**: saha çizgileri hızla akıyor, düz ince kırmızı çizgi sahanın ortasında dikey uzanıyor (f190–200) [g] | whip tilt_up 6.04–6.81 [ö], gözle aşağı bakış | Beklenti kurulumu: "şu kadar sanırsın" |
| 6.91–8.98 | 207–269 | "it would be about this long" | Kuşbakışı saha: yarda numaraları 10–50, ortada **ZACK D FILMS logosu oval**, uçta büyük "ZACK D FILMS" yazısı (f240); kırmızı ince çizgi sahayı boydan boya değil, kısa bir kısmını kaplıyor [g] | yavaş kaydırma [g] | **Beklenti nesnesi:** "bu kadar" = küçük. Kanal imzası dünyaya gömülü |
| 8.98–10.01 | 269–300 | "But the human body" | Saha **3D kart gibi dönüyor** (siyah kenarlar, f270) ve yerini mavi gökte tek başına duran adama bırakıyor (A-poz, kol açık, f280–290) [g] | flip vertical_axis 8.98–9.28, **edit boundary** [ö+g] | **Ters köşe 1/ölçek kırılması:** "ama" kelimesi ile beklenti iptal |
| 10.01–11.14 | 300–334 | "has thousands" | Adam yarı saydam kabuk olur, bacaklarında damarlar görünür; hemen **kotun paçasına zoom**: paça kenarından damarlar aşağı dökülüyor (f310–330) [g] | hard_cut 10.01 + tilt_up [ö] | "Binlerce" yoğunluğu: tek hamlede içe dalış |
| 11.14–12.61 | 334–378 | "of these tiny vessels" | Paçanın içinden damar kümesi dökülür, yakınlaşır (f340–370) [g] | tilt_up 10.04–12.41, hard_cut 12.45 [ö] | Ölçek: "tiny" ama çok |
| 12.61–13.98 | 378–419 | "that weave in and out" | Başı ve boynu olan damar-vücut (f380); kafa/boyun kabuğu soyulup kayboluyor (f410–420) [g] | tilt_down 12.48–14.78 [ö] | Kesit "her yere uzanır" |
| 13.98–15.68 | 419–470 | "of every body part" | Ön cepheden tam damar vücudu: kollar, parmak uçları, bacaklar, gövde ağı; yavaş aşağı kayıyor [g] | tilt_down, static 14.78–15.55 [ö] | Detay şov: damarlar vücudu "yeniden çizer" |
| 15.68–16.75 | 470–502 | "And with all of them" | Vücut buruşup dinamik karışık bir ağa dönüşür (f470–500) [g] | tilt_up 15.55–16.18, dolly_out [ö] | "Hepsini birleştir" |
| 16.75–17.58 | 502–527 | "combined" | Ağ kompakt bir kırmızı top (yumak) halinde toplanıyor (f510–520) [g] | dolly_out 16.18–17.68 [ö] | Sıkıştırma: elde bir top damar |
| 17.58–18.59 | 527–557 | "if you started" | Yumak **cyan→yeşil çapraz çözülme ile eriyor** (f536–550), kamera yeşil zemin üzerinden **hızlı zoom**: gri gökdelenler, mavi su, kırmızı çizgi (f545–557) [g] | flip 17.72 (tool), gözle: dissolve + zoom_burst 17.98–18.28 [ö+g] | Çevre değişimi: oyun sahası → harita |
| 18.59–19.72 | 557–591 | "in New York" | Lowpoly ABD haritası; New York gökdelen kümesi, kıyıdaki mavi su; çizgi şehir merkezinden başlıyor (f560–590) [g] | zoom_out 17.98–19.15, tilt_down 19.15–23.8 [ö] | **Başlangıç noktası:** "New York"u görsel olarak çivile |
| 19.72–20.92 | 591–627 | "your blood vessels" | Harita yeşilden **sarıya** geçer (ışık/renk kayması), kırmızı çizgi yukarı doğru uzuyor (f600–620) [g] | tilt_down [ö] | Çizgi = "senin damarların"; renk kaymasıyla mesafe hissi |
| 20.92–22.49 | 627–674 | "would make it all the way to the" | Turuncu çöl/plato, düz çizgi hızlanıyor; kamera çizgiyi izliyor (f630–660) [g] | tilt_down [ö] | Hız hissi, kelimeyi bekletme: "to the..." → Canyon bekleniyor |
| 22.49–23.66 | 674–709 | "Grand Canyon" | **Grand Canyon:** turuncu yelpaze duvarlar, ortada mavi nehir, kırmızı çizgi kanyonu enine kesiyor; yanında koyu bir ikinci çizgi (f680–705) [g] | tilt_down biter, hafif blur [ö] | **Görsel doruk 1:** coğrafi simge, kelimeyle aynı kare |
| 23.66–24.59 | 709–737 | "It would go on" | Kanyon uzaklaşırken yeşil-sarı blur patlaması, mavi okyanusa dalıyor (f712–730) [g] | whip left 23.86–24.39 [ö]; wipe/flip 24.49–25.0 **yanlış pozitif** (§10) | Sürpriz: "bitmedi, devam" |
| 24.59–25.76 | 737–772 | "to reach all the way" | Koyu mavi okyanus, bulutlar akıyor; kırmızı çizgi sağ üstte, koyu çizgi sol altta, kısa bir parça görünüyor [g] | pan_left 25.06–30.56 [ö] | Uzaklık: büyük boşluk, yalnız çizgi |
| 25.76–27.56 | 772–826 | "across the Pacific Ocean" | Pasifik; f800–820'de Hokkaido kıyısı (yeşil) belirir [g] | pan_left, dolly out [g] | Coğrafi işaret: "Japonya" yaklaşıyor |
| 27.56–28.96 | 826–868 | "over Japan Asia" | Kamera çıkar: dünya küresi; Kuzey Asya, kırmızı + koyu paralel çizgi küreyi yatay sarıyor (f830–870) [g] | zoom_out sürekli [g] | Ölçek patlaması: haritadan küreye |
| 28.96–30.56 | 868–916 | "and all of Europe" | Küre Avrupa'ya dönüyor: Hazar/Akdeniz kıyıları, çizgi sol kenardan çıkıyor (f870–910) [g] | pan_left [ö] | **Görsel doruk 2:** yarım dünya turu, tek sürekli hareket |
| 30.56–31.73 | 916–951 | "And not only" | Küre bir sapla siyaha eriyor (flip, f920) → adam saha üzerinde, etrafında kırmızı halka çizen ince damar çizgisi (f930–950), sağ üstten kalın kırmızı sivri damar ucu giriyor [g] | flip vertical_axis 30.6–30.9 **edit boundary** [ö+g] | Döngüyü kapat: "başlangıca döneriz" |
| 31.73–33.50 | 951–1004 | "would it make it all the way back" | Adam yukarı bakıyor, ağzı açık; kırmızı sivri damar uçları sağ üst ve sağ alttan sahaya giriyor (f960–1000) [g] | static 30.93–34.93 [ö] | **Reaksiyon çekimi:** seyirci karakterle aynı şaşkınlıkta |
| 33.50–34.83 | 1004–1044 | "to your starting point" | Damar ucu adamın ayağının yanına iniyor, adam baktığı yönü damar ucuna çeviriyor (f1030–1050) [g] | static [ö] | Ödül: çizgi tam başladığı yere dönmüş |
| 34.83–35.07 | 1044–1051 | "but" | Aynı kare | — | **Ters köşe 2/yükseltme:** "ama daha fazlası var" |
| 35.07–36.40 | 1051–1090 | "it would be able" | Adamdan küreye **hızlı zoom burst** (f1060 blur), siyah uzay, küçük yıldız parçacıkları; küre üzerinde kırmızı halkalar (f1070–1100) [g] | zoom_burst 35.2–35.67 [ö] | Sayı vurgusuna geçiş |
| 36.40–37.00 | 1090–1109 | "to make this trip" | Küre ortada, üzerine çok sayıda kırmızı halka sarılmış [g] | zoom_out 34.93–37.07 [ö] | Kanıt: görsel sayı |
| 37.00–38.00 | 1109–1139 | "2 to 4" | Küre küçülüyor, 3–4 kırmızı halka ekvator çevresinde; altyazı rakamla "2 to 4" [g] | static | **Doruk:** sayının kendisi ekranda |
| 38.00–39.07 | 1139–1171 | "times over" | Küre ekran üstünde küçük, yıldız tozu, yavaş dönüyor [g] | static 37.07–38.64 | Sayıyı hazmettir |
| 39.07–39.44 | 1171–1182 | — | Konuşma bitti (38.92), siyaha geçiş/flip; ses 39.0–39.4 s fade-out [ö+g] | flip 38.67–39.27 (tool), gözle: siyaha çıkış | Sessiz kapanış, döngü yok |

## 4. Altyazı
- Beyaz dolgu (#fdfeff), ince siyah kontur, gölge yok, ortalı, taban çizgisi **y≈0.795**, font boyutu ekran yüksekliğinin ≈%3.8'i; font adayı Montserrat Bold/ExtraBold (skor 0.58, düşük güven). Hummingbird videosuyla aynı stil. [ö]
- 43 grup, ortalama 0.88–0.91 s, grup başı 1–5 kelime (ortalama 2.65, medyan 3). Tool animasyon sınıflaması 23 kesme / 17 pop / 3 fade verdi; "pop" kayıtlarının bir kısmı `scale_range` 17.3 gibi saçma değerler (kamera hareketi/arka plan değişimi karıştı) → altyazı **fiilen kesme** [ö + g: tilelerde yazı boyutu sabit]. Vurgu rengi yok.
- Alt %20 güvenli alanla çakışma 22/43 grup. [ö]
- **Ekranda altyazı dışı yazı:** yalnızca sahanın üzerindeki "ZACK D FILMS" (6.9–8.7 s, yarda çizgisi altında ve 50 yarda logosunda, dünyaya gömülü). Rakam grafiği, etiket yok; "2 to 4" bile normal altyazı olarak geliyor. [g]
- Altyazı konuşmayı **kelime sınırından** takip ediyor ve cümle kırmıyor ("all the way" / "to the" / "Grand Canyon" ayrı grup). Önemli kelime (New York, Grand Canyon, Pacific Ocean, Japan, Asia, Europe, 2 to 4) kendi grubuna oturup 0.9–1.2 s ekranda kalıyor. [ö]

## 5. Görsel dil
- **Dört dünya**, hepsi aynı çizgi (kırmızı damar) ile bağlı: (1) mavi gök + yeşil futbol sahası (karakter dünyası, 0–10, 30.6–35 s), (2) mavi arka plan üzerinde damar vücudu (10–17.6 s), (3) lowpoly ABD haritası → fotogerçekçi küre (17.6–30.5 s, tek kesintisiz yolculuk), (4) siyah uzay + küre + halkalar (35–39 s). Dünya değişimi anlamlı: saha = "burada", harita/küre = "ölçek". [g]
- **Karakter:** kısa kahverengi saçlı, lacivert tişört + açık kot, hiç konuşmayan reaksiyon karakteri (şaşırma, bakma). Hummingbird videosundaki sarı "ZACK D FILMS" tişörtlü kel karakterden **farklı** → kanal tek karaktere bağlı değil, "seyirci vekili" rolü sabit. [g]
- **Palet:** sahada doygun cyan #50c2fa gök + çim yeşili #6e8a27, kırmızı damar #992223; harita yeşilden sarıya, çöl turuncusu (kanyon), derin deniz laciverti, küre mavi-bej. Hepsi doygunluk ~0.69, parlaklık ~0.68 [ö]. Kırmızı çizgi her dünyada tek sıcak vurgu. [g]
- **Kamera imzası:** neredeyse hiç durmuyor; harita/küre bölümünde (17.6–30.5) kamera çizgiyi "arkadan takip" ediyor, tek hamlede zoom_out, tilt, blur patlamaları. Sahada ise sabit/yavaş pan. Bu iki kamera ritmi birbirine zıt: karakter sahnesi sakin, yolculuk sahnesi hızlı. [ö+g]
- **Çekim tipi** (tool): yakın %22.7, kalabalık %43.7 (damar/bina yoğunluğu), orta %31.1, geniş %2.5 [ö]; etiketler damar ağı/küre gibi nesnelerde yanıltıcı (§10).
- Merkezileme: özne ekran merkezine %98 oturuyor, üçte kural yok [ö].

## 6. Ses
- Tek anlatıcı, duraksız (0.15 s üstü boşluk yok), 179.5 kelime/dk. Cümle boşlukları kurguyla silinmiş [t]. Altyazı ritmi bu yoğunluğa bağlı. [ö]
- Çok yüksek miks: −12.3 LUFS, +0.2 dBTP; dar LRA (2.4 LU), yani anlatım yüksek ve düz. Platform normalizasyonunda ~1–2 dB kısılır. [ö]
- Müzik: ölçülebilir tek boşlukta (son 0.52 s) bed −41.9 dBFS ≈ sessizlik; **müzik yatağı yok ya da çok kısık** [ö/t]. Ses efekti adayı yok; tek güçlü onset (33.25 s, "impact", güç 0.81) damar ucunun adamın yanına inmesine denk geliyor [ö+g tahmini]. Kulakla doğrulanmadı.
- Kesme/beat hizalaması 0.29 (beklenen şans 0.36) → kurgu müziğe değil sözün kelimelerine hizalı. [ö]

## 7. Neden işe yarıyor [t]
1. **0.0–0.5 s: imkânsız eylem.** Adamın içinden damar vücudu çıkıyor; soru bitmeden "ne olduğunu" gösteriyor, şaşkın yüz seyirciyi içeri çekiyor.
2. **Ölçek yalanı ve düzeltmesi (6.9→9.3 s).** "Bu kadar uzun sanırsın" ile kısa bir çizgi gösterip "ama binlerce" ile kart çevirerek (8.98 s) beklentiyi yıkıyor; ters köşe tamamen görsel (kart çevirme).
3. **Tek çizgi, tek yolculuk (17.7–30.5 s).** 13 saniye boyunca aynı kırmızı çizgi New York → Grand Canyon → Pasifik → Japonya → Asya → Avrupa. Her kelime (New York, Grand Canyon, Pacific, Japan, Asia, Europe) altyazı **ve** görsel işaretle aynı karede doğuyor; izleyici izlemeden "anlıyor".
4. **Doruklar:** 22.5–23.7 s Grand Canyon (ilk güçlü ödül), 27.6–30.5 s küre turu (ikinci), 37–38 s "2 to 4" ve kırmızı halkalar (sayı patlaması).
5. **Reaksiyon çekimi (30.6–35 s).** Çizgi geri döndüğünde adamın yüzüne dönülüyor; seyirci kendi şaşkınlığını karakterde görüyor.
6. **"But" ile yükseltme (34.8 s):** başlangıca dönüşten sonra "hayır, daha fazla" ile sayı ikinci kez büyüyor; kapanış 2–4 kat.
7. **Ritim:** her 0.9 s'de yeni altyazı, yolculukta sürekli kamera hareketi, duraksız anlatım; izleyiciye kaydırma boşluğu yok.
8. **Zayıf nokta [t]:** döngü yok (son kare siyah küre), kanal imzasını bağlayan karakter/komik kapanış hummingbird'teki kadar güçlü değil.

## 8. Aynı tarzda yapmak için kalıp
- Format: "X'in toplam uzunluğu/miktarı ne kadar olur?" tek ölçü sorusu; 110–120 kelime, 38–40 s, duraksız ≈180 kelime/dk.
- Akış: imkânsız eylem (0–0.5) → nesneyi çıkar/ayrıştır (0.5–5) → küçük beklenti göster (5–9) → ters köşe: "ama" + sayı (9–10) → içe dalış ve ölçek (10–17.5) → tek sürekli yolculuk ile ölçeği büyüt, her coğrafi/nesne işaretini kelimeyle aynı karede göster (17.5–30.5) → reaksiyon çekimi (30.5–35) → "ama" ile sayıyı yükselt (35–37) → sayı kartı (37–39) → siyah.
- Görsel: tek renkli vurgu nesnesi (kırmızı çizgi) + üç dünya (karakter, nesne, ölçek); karakter hiç konuşmuyor, sadece tepki veriyor.
- Altyazı: beyaz + siyah kontur, y≈0.795, 1–4 kelime, kesme, önemli kelime kendi grubunda.
- Ses: duraksız anlatım, −12 LUFS civarı, müzik kısık/yok; ses efektine gerek bırakmayan kamera hareketi.

## 9. İçerik bayrakları
- Kanal imzası (saha logosu "ZACK D FILMS", karakter tasarımı, düşük-poligon harita) kanala ait: aynı tarzda üretimde kendi marka ve karakterini kullan.
- Bilimsel iddia (damarlar 60.000 mil / dünyayı 2–4 kez sarar) anlatı amaçlı; kendi üretiminde sayıyı kaynakla doğrula ve doğru birimi ekle.
- İçerik zararsız; gore yok (kan/damar şematik, kesit yok).

## 10. Ölçüm sınırları
- **Geçişler:** tool 14 geçiş listeledi; gözle kontrol: 24.49–25.02 s'deki iki "wipe" ve bir "flip" (id 9, 10, 11) kesintisiz bir pan_left + blur (Pasifik'te kamera hızlanması) üzerinde **yanlış pozitif** (f735–750 tile'larında aynı okyanus devam ediyor). 6.04–6.81 s'deki iki whip kamera tilt'i, kurgu kesmesi değil. 17.72 s "flip" aslında yumak → harita **çapraz çözülme + zoom burst** (f536–560, `d1.jpg`). 38.67–39.27 s "flip" siyaha çıkış. 8.98 flip, 30.6 flip, 10.01 ve 12.45 kesmeleri gerçek.
- **Çekim tipi / "crowd" etiketi** damar ağı, bina ve küre gibi yoğun nesneleri "kalabalık" sayıyor; insan değil. Yüzdeler bu yüzden yorumlanmamalı.
- **Kamera segmentleri:** 6.04–6.34 "complex" ve 23.86–24.62 pan_left kamera hareketi değil, sahne içi hızlanma + blur.
- **Altyazı OCR:** "4, the blood vessels" aslında "the blood vessels"; "ZCMS" ve uzun "50|4]0..." kaydı sahadaki "ZACK D FILMS" logosunun/yarda rakamlarının okunması (scene_text), altyazı değil. Animasyon sınıflaması (pop) yukarıda açıklanan nedenle şüpheli.
- **Koyu ikinci çizgi** (Grand Canyon'dan Avrupa'ya kırmızı çizginin yanında): ne olduğu kareden belli değil. Gölge ya da "düz rota" olabilir; **[t]** gölge, doğrulanmadı.
- **Ses:** müzik/efekt yokluğu bed ölçümü tek boşlukta; kulakla doğrulanmadı. Beat grid güvenilmez (tempo güveni 0.32).
- **Karakter süresi:** adamın göründüğü diğer sahneler 0–10 ve 30.6–35 s dışında yok; haritada ek gösterim bulunmadı.
