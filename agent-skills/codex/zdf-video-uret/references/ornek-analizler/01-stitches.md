# "How Stitches Work" analizi

Kaynak: `How_Stitches_Work [ttuKeS5k4Uo].mp4` · 1296×2304 (9:16), AV1, 30000/1001 fps · 31.03 s · 930 kare · İngilizce
Ölçümler: `analysis/` · Gözle doğrulama: `inspect/part1.jpg` (kare 0–550), `inspect/part2.jpg` (560–920), her 10. kare; ek yoğun tile'lar `d1` (0–195, her 5 kare), `d2` (300–495, her 5), `d3` (564–798, her 6), `d_cuts` (kare 574–580, 718–735, 762–775 tek tek)
Etiketler: **[ö]** ölçüm, **[g]** kareden gözle doğrulandı, **[t]** tahmin.

## 1. Kısa özet
Zack D. Films'in "tıbbi süreç" alt türü: tek bir bacak yarası (baldır), tek ve kesintisiz bir 3D makro çekim; kamera yaradan içeri dalıyor, doku katmanlarını (şişme, yeni doku, damar ağı) sırayla gösteriyor ve en sonda geri çekilerek iyileşmiş izi gösteriyor. Formül: **tek yara, tek kamera yolu, beş cümlelik kronolojik anlatım**. Ters köşe, soru, şaka ve ekran yazısı yok; bu video kanalın "mizah/şok" videolarından (Kolibri Kalbi, Cybertruck) farklı olarak sakin ve öğretici. [g]

## 2. Teknik kimlik
| Alan | Değer | Kaynak |
|---|---|---|
| Ses | entegre **-12.0 LUFS**, true peak **+1.4 dBTP**, LRA 1.6 LU (çok düz dinamik) | [ö] |
| Konuşma | 77 kelime, **148.9 kelime/dk** (konuşma aralığında 152.6; duraklamasız 168), konuşma oranı %88.6 | [ö] |
| Duraklama | 9 adet >0.15 s, toplam 2.78 s; en uzunu 0.52 s (1.24–1.76 s, "stitches," sonrası); cümle sonlarında 0.22–0.40 s nefes payı | [ö] |
| Müzik / efekt | konuşma boşluklarında −27.9 dBFS'lik sürekli bir taban ölçüldü (konuşmadan ≈14 dB aşağı); 0–30.65 s boyunca var, 30.3–30.5 s'de hızla kesiliyor. Ritim tespiti güvenilmez (112 bpm, güven 0.41). Ayrı efekt (whoosh/riser) tespit edilmedi; 3 tane "impact/bass_hit" onset var: 8.53, 18.61, 19.11 s | [ö], kulakla doğrulanmadı |
| Kesim ritmi | Araç 5 "dissolve" saydı (0.16/s) ama kareden bakınca **gerçek kurgu kesmesi 0**; 1 gerçek morf/çapraz geçiş (25.56–25.76 s). Gerisi tek çekim içinde kamera hareketi + doku değişimi | [ö] → [g] düzeltildi |
| Kamera | 12 segment: 0–3.8 zoom in (doğrusal), 3.8–11.7 **sabit**, 11.7–17.5 zoom in (ease in/out), 17.5–23.1 tilt down, 23.1–23.9 sabit, 23.9–29.96 zoom out, son 1 s sabit | [ö] |
| Altyazı / ekran yazısı | **hiç yok** (OCR 0 kayıt; 18 tile'da hiç yazı görünmüyor) | [ö+g] |
| Üretim | Foto-gerçekçi 3D render (deri gözenek/tüy detayı, yumuşak odak kaybı, mavi gökyüzü degrade arka plan), yara ve doku shader'ı, dikiş ipi için ayrı animasyon; altyazısız | [t] |

## 3. Saniye saniye akış
Kare = zaman × 29.97. Altyazı olmadığı için satırlar cümle/ifade bazlı; ekran içerikleri kareden doğrulandı.

| Zaman (s) | Kare | Söylenen | Ekranda | Kamera / geçiş | Amaç |
|---|---|---|---|---|---|
| 0.00–1.24 | 0–37 | "When you get stitches," | Mavi gökyüzü önünde, şortlu bir kişinin **baldırı**; baldırda uzun, açık, kırmızı yara. İkinci bacak ve ayakkabı kadrajın altında. Hemen kırmızı yaranın tepesine ince beyaz **dikiş ipi** giriyor, ilk halkalar ~0.5 s'de oluşuyor [g] | zoom in: alt çerçeveden yaraya doğru yaklaşıyor [g] | Hook: ilk karede açık yara; ses "stitches" derken ip zaten işliyor |
| 1.76–3.3 | 53–100 | "a doctor threads a needle" | Dikiş halkaları yukarıdan aşağı birer birer ekleniyor (60. karede yarısı, ~100. karede tamamı). **Doktor, el ve iğne hiç görünmüyor**; ip kendi kendine dikiyor [g] | zoom in sürüyor, baldır dolguyla kadrajı kaplıyor | Kelimeler "doctor/needle" derken nesne yok: görüntü kavramı değil sonucu gösteriyor |
| 3.5–5.4 | 105–162 | "through your wound and pulls it tight" | Dikişli yara; alt uçta ip kuyruğu yatay bir çizgi olarak uzanıyor (110–160. karelerde) ve gerilmiş gibi duruyor [g] | zoom in biter ~3.8 s, ardından **sabit** (3.8–11.7) [ö+g] | Çekme eylemini ip kuyruğu temsil ediyor |
| 5.5–6.4 | 165–193 | "to close the skin." | **Makas** soldan alt köşeden giriyor, ip kuyruğunu kesiyor (≈kare 165–185, 5.5–6.2 s), çıkıyor. Yara artık ince koyu bir yarık ve dikiş halkaları [g] | sabit | Dikiş işlemi bitti; makas = tek "insan eylemi" göstergesi |
| 6.74–7.0 | 202–210 | (duraklama) | Aynı kadraj, hiçbir şey olmuyor | sabit | Nefes |
| 7.0–10.0 | 210–300 | "As the stitches hold the edges together, the wound" | **3 s boyunca aynı görüntü**: sabit kadrajda ip halkaları, koyu yarık, tüylü deri. Görsel değişim yok (190–300. kareler birebir aynı çerçeve) [g]. 8.53 s'de bir "impact" onset'i ölçüldü; karede karşılığı yok [ö] | sabit | Anlatımın görsele göre öne geçtiği en uzun boşluk |
| 10.0–11.0 | 300–330 | "becomes inflamed" | Kenarlar **kırmızıya dönüyor**: 315–335. karelerde dikişin iki yanında şişen pembe-kırmızı dudaklar alt ve üstten yayılıyor [g] | sabit → 11.7'de zoom in başlıyor | Kelime ile görüntü senkron: ilk gerçek görsel olay |
| 11.0–14.1 | 330–423 | "as new cells begin to repair the tissue." | Kırmızı şişlik büyüyor ve dudaklar belirginleşiyor; kamera giderek **makroya** yaklaşıyor (deri gözenekleri, tüyler). **Hücre görseli yok**: "new cells" sadece şişen dokuyla anlatılıyor [g] | zoom in ease in/out | Zayıf eşleşme: anlatım hücre diyor, görüntü genel şişlik |
| 14.12–14.44 | 423–433 | (duraklama) | Makro, kırmızı dudaklar | zoom in | Nefes |
| 14.44–18.8 | 433–563 | "Afterwards, connective tissues and collagen start to create skin." | İki kırmızı dudak arasında, ~14.7. saniyeden itibaren **sarı-turuncu şerit** beliriyor ve 15–17. s arasında boşluğu dolduruyor; ip halkaları kalın beyaz halkalar olarak yakın planda. 17.5'ten sonra kamera aşağı kayıyor [g] | zoom in → 17.5'te tilt down | Yeni doku (sarı) = "connective tissue/collagen" yorumu [t]; renk kodlu görsel |
| 18.8–19.02 | 563–570 | (duraklama) | Sarı şerit; hafif kararma. 18.61'de "impact", 19.11'de **bass_hit** onset'i [ö] | tilt down | Ses vurgusu "Then" ile aynı |
| 19.02–20.5 | 570–614 | "Then, blood vessels form" | Sarı şerit turuncuya, ardından pembeye dönüyor; 19.5. s'den (≈kare 585) itibaren yaranın **içinde parlak kırmızı dallı damarlar yukarıdan aşağı büyüyor** [g]. Araç burada 3 "dissolve" saydı (19.2, 19.65, 20.0 s): kareler (574–580) aynı kamera hareketi sürerken renk değişimi; **yanlış alarm**, kurgu yok [g] | tilt down, ekranda kesme yok | **Görsel doruk 1**: damar ağının yoktan var olması |
| 20.5–22.0 | 614–660 | "to nourish these developing tissues," | Damar ağı yoğunlaşıyor, parlak kırmızı en yüksek parlaklıkta (≈kare 620–680). 22.0'daki "dissolve" yine damarların koyulaşmasıdır [g] | tilt down | Beslenme = kan damarı yoğunluğu |
| 22.0–24.58 | 660–737 | "filling in the area." | Kırmızı **koyu bordoya** çekiliyor (kare ≈680–720), damarlar yara boşluğunu dolduruyor, makro deriden kaçış başlamadan sakin an [g] | 23.1–23.9 sabit | Sonuç öncesi sakinleşme |
| 24.4–25.4 | 732–760 | (duraklama, "And") | **Hızlı geri çekilme**: makro damarlı yarıktan baldır görünümüne 0.5–1 s'de geçiş, sol kenarda gökyüzü beliriyor [g] | zoom out (hızlı, ease out) | Ölçek sürprizi: bu küçük şeyin bir bacakta olduğu görülüyor |
| 24.78–26.0 | 743–780 | "And over a few weeks," | Baldırda dikişli, kırmızı yara; 25.56–25.76 s arasında dikiş ipleri **eriyip kayboluyor**, yerinde ince pembe bir iz kalıyor (tek gerçek geçiş) [g] | zoom out | Haftaların geçişi tek morfla gösteriliyor |
| 26.0–29.0 | 780–870 | "the wound will have healed together and the" | Şortlu baldır; iz giderek solgunlaşıyor; **bacak yürüyor**: arka plandaki diğer bacak öne geliyor, ayakkabı ve mor çorap alt kadrajda beliriyor (810. kareden sonra) [g] | zoom out ease out | Tamamlanma + hayat devam ediyor |
| 29.0–30.28 | 869–907 | "stitches are removed." | Aynı iyileşmiş baldır; **dikişler 4 s önce kayboldu**, yani "removed" denirken görüntü zaten bitmiş. Müzik 30.3–30.5 s'de kesiliyor [g+ö] | zoom out biter 29.96, sonra sabit | Kapanış cümlesi; görüntü sözün önünde |
| 30.28–31.03 | 907–930 | — | Sessiz, sabit, iyileşmiş bacak; 30.6 s'de "pop_click" [ö]. Son kare = ilk karenin aynı kadrajı (şortlu baldır, mavi gökyüzü, ayakkabı) ama yara iz olmuş [g] | sabit | Döngü: başa sarınca aynı kadraja açık yarayla dönülüyor |

## 4. Altyazı
- **Yok.** 0 OCR kaydı; 18 numaralı tile'ın hiçbirinde yazı yok. [ö+g]
- Kanalın diğer videolarında (saws) yazı var; bu video altyazısız, anlatıcı ve görsel taşıyor. Platformda otomatik altyazıya bırakılmış olabilir [t].

## 5. Görsel dil
- **Tek dünya, tek karakter parçası**: mavi-gökyüzü degrade üzerinde şortlu, sporcu ayakkabılı bir bacak. Yüz, doktor, hasta hikâyesi yok; vücut parçası "başroldeki nesne". [g]
- **Dokular katman katman**: yaranın içine inildikçe palet gökyüzü mavisi + ten rengi → pembe/kırmızı (şişlik) → sarı-turuncu (yeni doku) → parlak kırmızı (damar) → bordo → ten + mavi (iyileşme). Her cümle bir renk. [g]
- **Kamera tek yönde akıyor**: yaklaş (0–3.8) → bekle (3.8–11.7) → daha çok yaklaş (11.7–17.5) → aşağı kay (17.5–23.1) → geri çekil (23.9–29.96). Bu, kanalın diğer videolarındaki "zoom burst + dünya değişimi" imzasından farklıdır; burada hız yok, derinlik var. [ö+g]
- **Çekim tipi**: araç "close %23, crowd %77" dedi (damar/halka yoğunluğu yüzünden); kareden **hep yakın/makro**, tek çıkış son geri çekilme. [ö → g düzeltildi]
- Detay seviyesi yüksek (deri gözeneği, tüy, ip halkası gölgesi); mikro-derinlik odağı (arka plan flulaşıyor) sinema hissi veriyor. [g]

## 6. Ses
- Tek anlatıcı, 149 kelime/dk, kanal ortalamasından yavaş; cümle aralarında 0.2–0.5 s nefes var (9 duraklama). Bu video "okuma" hızında, hızlı kesim hissi yok. [ö]
- -12.0 LUFS, +1.4 dBTP: yüksek ama hafif kırpılan miks; dinamik çok dar (LRA 1.6). [ö]
- Konuşma boşluklarında sürekli −28 dBFS'lik bir taban ölçüldü ve kapanışta hızlı kesiliyor; bu bir müzik yatağı olabilir ama ayrıştırılmadı. Bilinen tek ses vurgusu 19.1 s'deki bas vuruşu ("Then," = damarların başladığı an) ve 8.5/18.6 s impact'leri. Kulakla doğrulanmadı. [ö/t]

## 7. Neden işe yarıyor [t]
1. **İlk karede açık yara + hemen dikiş**: 0–1.2 s'de yara görülüyor, ip hemen işlemeye başlıyor. "Ne olacak?" merakı kelimeye gerek bırakmıyor. (0–3 s)
2. **Anlatıma karşı çıkmayan, merak eden bir ritim**: her cümle bir görsel durum. En güçlü senkron: "inflamed" ↔ kırmızılaşma (10–11 s), "blood vessels form" ↔ damar ağının yeşermesi (19.5 s).
3. **Görsel doruk = 19.5–22 s damar ağı**: video boyunca tek canlı, hareketli, parlak anlar bunlar; hem bilgi (damarlar beslenme getirir) hem estetik ödül.
4. **Ölçek sürprizi = 24.4–25.4 s geri çekilme**: izleyici o ana kadar makro yaranın içindeydi; birden baldır ve mavi gökyüzü görünüyor. Bu videonun tek "ters köşe"sidir.
5. **Döngü = 30.3–31.0 s**: son kare ilk karenin kadrajı; yarasız baldır → başa sarınca yara. Düzenleme tarafı kasıtlı olabilir [t].
6. **Zayıf yönler (kopyalarken kaçınılacak)**: 7–10 s'de 3 saniye boş sabit görüntü; "new cells" için hücre görseli yok; "stitches are removed" sözü görüntüden 4 s geç. İzleyici kaybı en çok 7–10 s aralığında beklenir [t].

## 8. Aynı tarzda yapmak için kalıp
- Konu: "[Bir tıbbi/mühendislik süreci] nasıl çalışır?"; 70–80 kelime, 30–31 s, 150 kelime/dk, cümle sonlarında kısa nefes.
- Akış: nesneyi tanıt ve sürecin ilk eylemini ilk karede başlat (0–3 s) → işlem biter (3–6.5 s) → **sabit bekleme** (yaz, 3 s'den kısa tut) → doku/durum değişimleri cümle başına bir renk (10–24 s) → doruk (damar ağı gibi büyüyen detay) → ölçeği geri çekme (24–26 s) → sonuç + döngü (26–31 s).
- Tek kamera: ileri zoom, aşağı kayma, geri çekilme; kurgu kesmesi yok.
- Altyazı yok; renk ve parlaklık anlatının vurgu aracı.
- Sabit "bacak" gibi tekrar kullanılabilir karakter parçası; mavi gökyüzü degrade arka plan.

## 9. İçerik bayrakları
- Kanal kimliği Zack D. Films'e ait; bu videoda marka yazısı **görülmedi** (saws videosunda mekanizma üzerinde "ZACK D FILMS" yazıyor). [g]
- Tıbbi anlatım basitleştirilmiş: dikişten sonra yaranın "şişmesi" iltihaplanma olarak adlandırılıyor; "yeni hücreler" ve "kollajen" görselleştirilmemiş. Bilgi iddiaları aynı tarzda üretimde doğrulanmalı. [t]
- Yara görüntüsü açık ama kansız; şiddet/gore yok. [g]

## 10. Ölçüm sınırları
- **Geçişler**: araç 5 dissolve sayıp 0.16/s verdi; kareden 4'ü (19.2, 19.65, 20.0, 22.0 s) yara dokusundaki renk değişimleridir, kurgu değil. Yalnız 25.56–25.76 s'deki dikişlerin kaybolması gerçek geçiştir. Gerçek kesim oranı ≈0.03/s. [g]
- **Çekim tipi** "crowd %77" etiketi makro damar/halka yoğunluğundan; gerçek çekim hep yakın. [g]
- **Müzik**: bed ölçümü konuşma boşluklarından (9 boşluk, −23 ile −35 dBFS aralığı), ayrıştırma yok, kulakla doğrulanmadı. [ö]
- **Kare numaraları**: yoğun tile d3'te kare = 564 + 6×etiket (ilk seçilen kare 564); yaklaşık ±4 kare. [g]
- **Müzik/ritim** (112 bpm) güvenilmez, beat güveni 0.41. [ö]
