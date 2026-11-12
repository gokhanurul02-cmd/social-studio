# "How Splinters Get Unstuck" analizi

Kaynak: `jobs/zdf/zdf-06-splinters/analysis/proxy-540p.mp4` (orijinal 1296×2304, 9:16, AV1, 29.97 fps, 2.6 Mbps) · 30.36 s · 910 kare · İngilizce · kanal: Zack D. Films
Ölçümler: `analysis/` · Gözle doğrulama: `inspect/part0.jpg` (kare 0–550), `part1.jpg` (560–900), her 10. kare; sık kontrol `d4.jpg` (0–46, her 2. kare), `d5.jpg` (690–730, her 2. kare). Tile etiketi tile sırasıdır: kare = dilim başlangıcı + 10×etiket.
Etiketler: **[ö]** ölçüm, **[g]** kareden gözle doğrulandı, **[t]** tahmin.

## 1. Kısa özet
"Kıymık vücuttan nasıl çıkar" sorusunu **tek bir mikroskobik kesit** üzerinden anlatan, karaktersiz, makro 3D anatomi videosu. Aynı kanalın hummingbird/blood-vessels videolarından farkı: hiç insan karakter, saha ya da harita yok; dünya "mavi gökyüzü + kesilmiş deri" tek dünya. Yapı: **gündelik bilinen çözüm (cımbızla çek, 0–4.8 s) → "ama bazen olmaz" (kart çevirme ile kesite dalış) → bedenin tepkisi (şişme, irin, basınç okları, 12.7–23 s) → "şanslıysan vücudun atar" (23–30 s) ve cımbız motifinin geri dönüşü**. Hook'ta gri ahşap yüzeyde parmak, ters köşe cümle başında değil içeride, doruk 14–22 s arası parlayan irin ve basınç okları.

## 2. Teknik kimlik
| Alan | Değer | Kaynak |
|---|---|---|
| Süre / kare | 30.36 s, 910 kare, 29.97 fps, 1296×2304 | [ö] probe.json |
| Ses | entegre **−15.0 LUFS**, true peak **−2.5 dBTP**, LRA 2.0 LU | [ö] |
| Konuşma | 81 kelime, **160.1 kelime/dk** (artikülasyon 175.5), konuşma oranı %91, **8 duraklama** 0.18–0.32 s, toplam 2.04 s (cümle içi virgüllerde ve cümle sonlarında) | [ö] |
| Konuşma bitişi | 29.88 s; 30.0–30.1 s arası çok sert fade-out (−271 dB/s), son 0.3 s sessiz kare | [ö] |
| Müzik / efekt | `sfx_candidates` boş; boşluklarda ölçülen bed −20…−35 dBFS ama ses kuyruğu yüzünden güvenilmez (aralık geniş), müzik **doğrulanamadı** | [ö], kulakla [t] |
| Geçiş | tool 6 geçiş (0.20/s). Gözle gerçek kurgu sınırı 4 (0.6 whip, 5.04 flip, 12.4 gizli whip kesmesi, 23.7 çözülme) → ≈0.13/s. Bkz. §10 | [ö]+[g] |
| Altyazı | 35 grup, ortalama **0.86 s**, 2.29 kelime/grup (1–4), beyaz #fffdfc + koyu kahve ince konturlu (#32100b), y≈0.795 | [ö] |
| Kamera | 20 segment; 6 sabit ama sahne-içi animasyon sürekli (parçacık/şişme) | [ö]+[g] |
| Üretim | 3D render (Blender sınıfı) makro deri kesiti; el/parmak fotogerçekçi (derinlik alanı bokeh'li), altyazı kurguda | [t] gerekçe: PBR deri, kıl şeritleri, parçacık sistemli irin |

## 3. Saniye saniye akış
| Zaman (s) | Kare | Söylenen | Ekranda | Kamera / geçiş | Amaç |
|---|---|---|---|---|---|
| 0.00–0.07 | 0–2 | — | **Gri-siyah ahşap kütük, kesinlikle desatüre**; sağ altta fotogerçekçi el, işaret parmağı ahşaba dokunuyor/sürtünüyor [g] | tilt_down [ö] | Hook: kıymığın doğduğu yer, renk yok, hemen "tehlike" dokusu |
| 0.07–0.60 | 2–18 | "If you" | Aynı ahşap, parmak hafifçe sürtünüyor (f2–14) [g] | static→whip [ö] | Soru bağlamı |
| 0.60–1.50 | 18–45 | "get a splinter" | **Sağa whip ile mavi gökyüzü zeminine kesme** (f15–27, 0.5–0.9 s, hareket bulanıklığı); el yarı kıvrık, işaret parmağı doğrulur, **parmak ucunda küçük koyu kıymık belirir** (f26–30, ≈0.9 s) [g] | whip right 0.5–0.9 (**edit boundary**), zoom_burst in 1.27 [ö+g] | Hook ödülü: "splinter" kelimesinden hemen sonra kıymık görünür |
| 1.50–2.50 | 45–75 | "most people" | Tek yakın plan parmak, ucunda dik duran ince koyu kıymık, düz açık mavi fon, sakin [g] | static [ö] | Normalliği sahneye indir |
| 2.50–3.64 | 75–109 | "just go ahead" | **Cımbız yukarıdan iniyor** (f80–100), ucu kıymığı kavrıyor (f100) [g] | static | Bilinen çözümü göster |
| 3.64–4.87 | 109–146 | "and pull them out" | Cımbız kıymığı yukarı çekip çıkarıyor, parmak temiz kalıyor (f110–140) [g] | static | **Beklenen çözüm tamam**: bir sonraki "ama" için zemin |
| 4.87–6.11 | 146–183 | "But sometimes" | Parmak **kapı gibi dönerek** (vertical-axis flip, siyah kenarlar f150) kesit görünümüne giriyor: epidermis hücre katmanı, kıl köklü dermis, damarlar, sarı yağ hücreleri; çapraz yatan koyu kıymık ortada (f160–180) [g] | flip 4.94–5.24, **edit boundary** [ö+g]; zoom_in 3.5–4.9 + roll_cw 4.14–4.57 [ö] | **Ters köşe:** "ama" ile makro iç görünüm. Yüzeyden kesite dalış |
| 6.11–7.01 | 183–210 | "they get lodged" | Kesit: kıymık dermisin içine eğik saplı, deri hafifçe çukurlaşıyor [g] | static | Mekanizmayı göster |
| 7.01–7.91 | 210–237 | "so deep" | Kamera yukarı kayıyor (tilt_up 6.87–7.84), deri yüzeyi ve kıymığın gömüldüğü çukur (f220–230) [g] | tilt_up → dolly_out 7.84–8.17 [ö] | "Derin" hissi: yüzeyin altındaki dünya |
| 7.91–9.01 | 237–270 | "into your skin" | Yüzeyden yan görünüm: cilt dokusu, tüyler, kıymık görünmez; **cımbız iniyor** (f250–290) ama kıymık yok [g] | static 8.17–11.58 [ö] | "Ulaşılamaz": cımbız var, hedef yok |
| 9.01–9.71 | 270–291 | "that you can't" | Cımbız çukurun üzerinde duruyor, deriyi hafif itiyor (f270–290) [g] | static | Çaresizlik |
| 9.71–10.48 | 291–314 | "reach them" | Cımbız yukarı çekiliyor/çıkıyor, çukur kalıyor (f300–310) [g] | static | Hata durumu |
| 10.48–11.28 | 314–338 | "If the area" | Yüzey, çukurun etrafı hafif kızarıyor (f320–330) [g] | static | Enfeksiyon başlıyor |
| 11.28–12.35 | 338–370 | "gets infected" | Kızarıklık büyür, yüzeyde yumuşak kabarıklık (f340–360) [g] | static→tilt_down 11.58–12.28 [ö] | Şişme başlangıcı |
| 12.35–12.68 | 370–380 | "it will" | **Hızlı yukarı bulanıklık**, büyük kırmızı şişlik yüzeyin üzerinde (f370) [g] | whip up 12.31–12.45 (conf 0.9) [ö]; gözle: yüzey→kesit arası gizli kesme | Geçiş: dışarıdan içeri |
| 12.68–13.78 | 380–413 | "start to swell" | Kesit: **kırmızı balon gibi şişlik** ekranın üstünü dolduruyor; altta kıymık, etrafında ilk sarı noktalar (f380–410) [g] | tilt_down 12.48–13.55; static 13.55–21.82 [ö] | Şişme: görsel büyüklük |
| 13.78–15.05 | 413–451 | "as pus forms" | **Parlak sarı-yeşil irin hücreleri** kıymığın etrafında çoğalıyor (f420–450) [g] | static, sahne içi parçacık animasyonu | **Görsel doruk 1:** enerjik, neredeyse neon irin |
| 15.05–16.08 | 451–482 | "under the skin" | İrin yoğun parlak kütle, kıymığın dibinde kümeleniyor (f460–490) [g] | static | Yoğunluk zirvesi |
| 16.08–16.92 | 482–507 | "This creates" | **Beyaz-mavi oklar** iki yandan içeri giriyor (f490–500) [g] | static | Yeni eleman: basınç göstergesi |
| 16.92–18.05 | 507–541 | "pressure around" | Oklar kıymığa doğru titreşiyor, irin parçacıkları azalıyor, kırmızı doku sıkışıyor (f510–540) [g] | static | **Mekanizma:** basınç = oklarla görselleştirildi |
| 18.05–19.25 | 541–577 | "the splinter that can" | Kıymık dikleşmeye başlıyor, oklar sürüyor (f550–570) [g] | static | Hedef nesne: kıymık |
| 19.25–20.15 | 577–604 | "sometimes" | Kıymık hafifçe yukarı kayıyor (f580–600) [g] | static | "Bazen": belirsizlik |
| 20.15–21.82 | 604–654 | "push it upwards towards the" | Kıymık yukarı ilerliyor, irin yoğunluğu düşüyor (f610–650) [g] | static→tilt_up 21.82–23.09 | **Görsel ilerleme:** kıymık yüzeye yaklaşıyor |
| 21.82–22.99 | 654–689 | "skin's surface" | Kamera yukarı kayıyor, balon ve üstteki gökyüzü görünüyor (f660–680); sahne kesitten dışarıya doğru açılıyor [g] | tilt_up 21.82–23.09, zoom_out 23.09–23.66 [ö] | Konuma ulaş: yüzey |
| 22.99–24.32 | 689–729 | "And if you're lucky" | **Çapraz çözülme** (f690–715): kesitten dış yüzey görünümüne; kırmızı kabarcık, deri üstünde kıllar (f690–720) [g] | dissolve 23.69–23.89 (conf 0.42), **edit boundary** [ö+g]; ağır zoom_out | Rahatlama: iyi ihtimal |
| 24.32–25.19 | 729–755 | "after a certain" | Kabarcık küçülüyor/yatışıyor (f730–750) [g] | static 23.92–28.36 | Zamanın geçişi |
| 25.19–26.33 | 755–789 | "period of time" | **Kabarcığın tepesinden koyu kıymık ucu fışkırıyor** (f760–790) [g] | static | **Görsel ödül:** kıymık dışarı çıkıyor |
| 26.33–27.56 | 789–826 | "your body could have" | Kıymık yarı dışarıda, kabarcık küçük (f800–820) [g] | static | "Vücudun yapar" |
| 27.56–28.29 | 826–848 | "completely" | **Cımbız sağ üstten giriyor** (f830–850) [g] | static | Açılış motifinin geri dönüşü |
| 28.29–29.10 | 848–872 | "removed it" | Cımbız kıymığı kavrıyor (f850–870) [g] | dissolve 28.4–30.0 (tool, **yanlış pozitif**) | Çıkarma eylemi |
| 29.10–30.03 | 872–900 | "from your skin" | Kıymık yukarı çekilip kayboluyor, geriye düz kırmızı yara/kabarcık izi kalıyor (f880–900) [g] | static | Çözüm: temiz yara |
| 30.03–30.36 | 900–910 | — | Son kare: izi gösteren sakin deri; ses fade-out 30.0–30.1, 0.3 s sessiz kuyruk [ö+g] | static | Bitiş (döngü yok) |

## 4. Altyazı
- Beyaz dolgu (#fffdfc), koyu kahverengi ince kontur (#32100b), gölge yok, ortalı, taban çizgisi **y≈0.795**, font boyutu ≈%3.8 (ZDF kanalındaki tüm videolarla aynı); font adayı Montserrat ExtraBold/Bold (düşük güven). [ö]
- 35 grup, ortalama 0.86 s, 1–4 kelime (ortalama 2.29, medyan 2). 26 kesme, 9 "pop" (sınıflama kamera/sahne değişiminden etkileniyor; tilelerde yazı boyutu sabit → fiilen kesme) [ö+g]. Vurgu rengi, büyük harf, emoji yok.
- Alt %20 güvenli alan çakışması 24/35 grup. [ö]
- Ekranda altyazı dışı yazı yok, etiket ("splinter", "pus") konmamış: bilgi tamamen görselde. [g]
- Altyazı kelimeleri konuşmayı izliyor ama bazı uzun cümlelerde 1 kelimelik gruplar tekrarlıyor ("pressure", "around", "sometimes", "completely"): 16.9–20.2 s arası dört ardışık tek-iki kelimelik grup, anlatımı yavaşlatıp irin/basınç sahnesini vurguluyor. [ö]

## 5. Görsel dil
- **Tek dünya, iki yüz:** (1) **dış dünya** düz canlı cyan #5aa7da gökyüzü zeminde fotogerçekçi el/parmak, deri yüzeyi; (2) **kesit dünyası** kırmızı dermis + sarı yağ + siyah damar ağı. Gökyüzü kesitte de en üstte kalıyor, yani kesit "yer altı" gibi. İki dünya arası geçişler tam anlatım sınırlarında: 4.9 (flip), 12.4 (whip), 23.7 (dissolve). [g]
- **Karakter yok:** insan yüzü, adam, saha yok; yalnızca el, cımbız ve kesit. Zack D. imzası (karakter) bu videoda yok; imza **cımbız** motifi ve gökyüzü fonu. [g]
- **Palet:** zemin #5aa7da; deri #c66d68/#e2c0b8; kesit kırmızısı #c42919; irin sarı-yeşil neon; basınç okları beyaz-mavi. Ahşap sahne tamamen gri (renksiz) → ilk karede kontrast. [ö+g]
- **Kamera imzası:** hareketler kısa patlama (zoom_in 1.27, tilt/whip 12.4, tilt_up 21.8–23.1), ardından uzun static bloklar (13.55–21.82 s = 8.3 s, 23.92–28.36 s = 4.4 s). Hareket sahne içi (irin, oklar, kıymık ilerlemesi) tarafından taşınıyor. [ö+g]
- **Çekim tipi** (tool): yakın %18.5, kalabalık %58.7, orta %22.8; "kalabalık" = irin parçacıkları/kıllar (insan değil), yorumlanmamalı. [ö]
- Merkezleme %100; kesitte çok katmanlı derinlik (ön plan kıllar bokeh'li). [ö+g]

## 6. Ses
- Tek anlatıcı; **8 duraklama**, hepsi 0.18–0.32 s ve virgül/cümle sonlarında (örn. "splinter," | "sometimes," | "infected," | "lucky," | "time,"): doğal nefes boşlukları kurguda bırakılmış, hummingbird/blood-vessels'taki "duraksız" kurgudan **daha gevşek**. 160 kelime/dk (artikülasyon 175). [ö]
- Miks: −15.0 LUFS, −2.5 dBTP → platform normalizasyonuna ve clipping'e hazır, blood-vessels'tan 2.7 LU daha sessiz. [ö]
- Müzik/efekt: ölçülemedi; boşluklarda bed rakamları (−20…−35 dBFS) ses kuyruğunu yakaladığı için güvenilmez. **Ses efekti adayı yok**; pus/pressure sahnesi için (13–22 s) bile efekt tespit edilmedi. Kulakla doğrulanmadı. [ö/t]
- Bitiş: konuşma 29.88'de bitiyor, ses 30.0–30.1 arasında bir anda kesiliyor; görüntü 0.3 s daha devam ediyor. [ö]

## 7. Neden işe yarıyor [t]
1. **0–1 s: rahatsız edici, tanıdık eylem.** Gri ahşap + parmak, 0.6 s'de mavi zemine whip kesmesi ve kıymığın doğuşu; izleyici "bu bana oldu" diye bağ kuruyor.
2. **Beklenen çözüm sonra bozuluyor (4.87 s).** Önce "çoğu kişi çeker" ve cımbızla başarılı çekim gösteriliyor; hemen ardından "ama bazen" kapı flip'i ile derin kesite giriyor: ters köşe düşük maliyetli ve net.
3. **"Ulaşamazsın" görselleştirilmiş (9–10.5 s).** Cımbız ekranda ve işe yaramıyor; kelime ile görüntü örtüşüyor.
4. **Biyolojik hikâye üç görsel parçaya bölünmüş:** şişme (12.7–13.8), irin (13.8–16), basınç okları + kıymığın yukarı ilerlemesi (16–22.9). Her biri kendi kelime grubuna denk.
5. **Parlak irin = görsel doruk (13.8–16 s).** Dik kırmızı fonda neon sarı-yeşil, videonun tek parlak vurgusu ve izleyicinin en iğrenç/en akılda kalan anı.
6. **Ödül (25.2–26.3 s):** kıymık kabarcığın tepesinden fışkırıyor. Sonra tweezers motifi kapanışta dönüyor (27.6–30 s): hem açılışa halka kuruyor, hem "vücudun çıkardı" cümlesini görsel olarak somutluyor.
7. **Ritim:** 0.86 s'de bir altyazı, ama kamera uzun static bloklarla ağırlaştırılmış; blood-vessels'tan daha yavaş, "medikal belgesel" tonunda.
8. **Zayıf nokta [t]:** açık bir sonuç/komik kapanış yok (kıymık çıkıyor, video bitiyor), döngü yok, karakter yok; blood-vessels kadar "ölçek" cümlesi veya hummingbird'teki gibi kahkaha anı eksik.

## 8. Aynı tarzda yapmak için kalıp
- Format: "X vücutta ne yapar / nasıl çıkar?" 80–85 kelime, 30 s, ≈160 kelime/dk, cümle sonlarında 0.2–0.3 s nefes.
- Akış: tanıdık eylem + renksiz sahne (0–1.5) → bilinen çözüm yap ve göster (1.5–4.9) → "But sometimes" + flip ile iç kesit (4.9–7) → çözümün neden çalışmadığını araçla göster (7.9–10.5) → vücudun tepkisi: şişme/irin/basınç (10.5–23) → "şanslıysan" ve doğal sonuç + açılış motifinin geri dönüşü (23–30).
- Görsel: mavi gök fonu + makro deri kesiti, neon irin parçacığı, beyaz basınç okları, tek aletin (cımbız) hem açılışta hem kapanışta tekrarı.
- Altyazı: beyaz + koyu kontur, y≈0.795, 1–4 kelime, kesme; etiket yok.
- Ses: gevşek duraksız, −15 LUFS civarı, kapanışta bitişte sert fade-out.

## 9. İçerik bayrakları
- Hafif gore: irin/şişen kabarcık, parçacıklı sarı-yeşil irin; platform kurallarında "grafik tıbbi" sınırına yakın, yaş/duyarlılık uyarısı düşünülmeli.
- Tıbbi bilgi: "enfeksiyon → basınç → kıymık yüzeye çıkar" gerçek olsa da genel; kendi üretiminde kaynaklandır, "cımbızla çek" ve "asla bırak" ayrımı yapma.
- Cımbız, kıymık, deri kesiti kanal imzası değil ama stil bütünlüğü Zack D. Films'e ait; kendi marka/karakterini kullan.

## 10. Ölçüm sınırları
- **Geçişler:** tool 6 geçiş (id 1–6) listeledi; 28.4–30.0 s "dissolve" (1.64 s, güven 0.43) kareden **yanlış pozitif**: o aralıkta f851–899 tile'larında aynı yüzey sahnesi (cımbız iniyor ve kıymığı alıyor). 1.23–1.40 "zoom_burst" kurgu değil, parmağın yükselirken kamera itmesi. 12.31–12.45 whip (güven 0.9) gerçek, ama içerik değişimi tool'da `content_change: false`; gözle yüzey görünümü kesite geçiyor (f370–380), yani gizli kesme. Gerçek kurgu sınırı: 0.6 whip (içerik değişimi true, edit_boundary false → yine de gerçek kesme: ahşap→mavi), 5.04 flip, 12.4, 23.7.
- **Çekim tipi/"crowd"** irin parçacığı ve kıl sayısına dayanıyor; kalabalık anlamı yok.
- **Altyazı OCR:** "Butomeme." gerçekte "But sometimes", "staît to swell" gerçekte "start to swell"; her iki kayıt transcript ile düzeltildi. "pop" animasyon etiketleri kamera hareketinin yazı bbox'una etkisi olabilir.
- **Ses:** müzik/efekt kulakla doğrulanmadı; `speech_music.music_present: true` ve bed değerleri (−20…−35 dBFS) konuşma kuyruğunu içerir, güvenilmez. Beat grid (tempo güveni 0.32) güvenilmez.
- **Anlatı–görsel uyumsuzluğu:** konuşma "vücudun kendisi çıkardı" diyor, görüntü son 2.5 s'de cımbızı gösteriyor (27.6–30 s); cımbız burada ya sembolik ya da kurgu hatası. [g] doğrulandı, **[t]** amaç yorumu.
