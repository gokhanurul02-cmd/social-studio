# Kanıtlanmış video kütüphanesi

Kaynak: kullanıcının "Claude Animasyon Sistemi" paketi (rehber: `Claude Animasyon Sistemi.md`, videolar: `kaynak/`). Örnekler 720×1280'e sıkıştırılmış, asılları 1080×1920. Hepsi kod ile çizilmiş (SVG + Remotion), yalnız ses yapay zekâ (ElevenLabs). Her video `NN/analysis/` altında tam ölçüldü (`social analyze`, 2026-11-09, branch analiz-uretim-iyilestirme): TIMELINE.md, transitions.json, onscreen_text.json, audio_analysis.json, composition.json.

Yeni bölüm üretirken: kalıba en yakın videoyu seç, `social stylecheck jobs/referans-kutuphanesi/NN/analysis <aday analiz>` ile karşılaştır, kuralları `ayni-tarzda-uret/references/hikaye-ve-sahne-kurallari.md`'den uygula.

## Ölçüm tablosu

| | 01 Keskin balta | 02 Uçak camındaki delik | 03 99 telefonla sahte trafik | 04 Gece 3'te gelen telefon |
|---|---|---|---|---|
| Kalıp | Masal | Bu neden var? | Gerçek olay | Sen karar ver |
| Süre | 38.5 s | 48.0 s | 48.0 s | 57.7 s |
| Kelime | 74 | 93 | 83 | 95 |
| Kelime/dk (toplam / artikülasyon) | 115 / 143 | 116 / 154 | 104 / 123 | 99 / 146 |
| Konuşma oranı | 0.80 | 0.80 | 0.80 | 0.70 |
| Toplam duraklama | 5.7 s | 9.8 s | 7.4 s | 16.2 s |
| LUFS / true peak | -17.5 / -0.4 | -16.2 / -0.2 | -16.1 / -0.4 | -16.7 / +0.1 |
| Müzik yatağı | yok (yalnız ses) | yok | belirsiz | var (≈-50 dBFS, konuşma +34 dB) |
| Efekt adayları | 2 whoosh | — | 1 riser + 5 whoosh | 3 whoosh + 2 riser, 26 bass hit |
| Altyazı stili | el yazısı serif, üstte (y≈0.55), kelime kelime, vurgu kırmızı | üst bant + alt etiket, fade | pop, 4 kelime/grup | kalın büyük harf sans, sarı vurgu, kelime kelime (y≈0.61) |
| Kamera | çoğunlukla sabit, kısa yumuşak pan'lar (0.3–0.7 s, ease_in_out) | sabit + dolly in/out (≈0.6 s, ease_in_out) | dolly_in/tilt_up kısa itişler | sabit; sahne başına kesme |
| Geçiş | 1 kağıt/sayfa wipe (2.3 s), gerisi kamera içi | zoom_burst + flip/hard_cut karışık | zoom_burst ağırlıklı, hard_cut, dissolve | sık hard_cut (≈1/1.5 s) |
| Çekim tipi payı | yakın .60 / orta .40 | orta .84 | yakın .63 / kalabalık .20 | orta .43 / yakın .31 / kalabalık .25 |
| Özne alanı medyanı | 0.34 | 0.17 | 0.41 | 0.28 |

Rehberdeki ölçüyle uyum: 70–100 kelime ✓ (74–95), konuşma oranı %60–75 hedefine karşı ölçülen %70–80, kelime/sn ≈1.7–1.9 (rehber ≈2).

## Videolara göre notlar (gözle + ölçüm)

- **01 Keskin balta (Masal):** Tek dünya (sepya kağıt dokulu orman, vinyet), çöp adam karakterler oynuyor (balta sallar, oturur, güler). Dev yazı yalnız açılışta ("Hiç durmamış, yine de kaybetmiş.") ve derste ("Baltayı bilemek vakit kaybı değildir."). Güneşin gökyüzündeki yolu zamanı anlatıyor; iki sayaç 36 / 78'e çıkıyor. Düşünce balonuyla "bilenen balta" açıklaması. Son cümle ilk cümleyi kapatıyor, ardından soru + "Yorumlara yaz".
- **02 Uçak camındaki delik (Bu neden var?):** Tek nesne (pencere) katman katman açılıyor: 3 katman etiketi, basınç okları, delik yakın planı; sonda ilk kareye dönüş. "Değil." dönüşü 5.6 s'de. Sürekli köşe logosu ("Bu Neden Var?") OCR'da `logo` olarak ayrıldı.
- **03 99 telefonla sahte trafik (Gerçek olay):** Önce tuhaf sonuç ("Bu adam el arabasıyla trafik yarattı"), sonra kim/nerede/ne zaman (2020, Berlin, Simon Weckert), "Nasıl mı?" sonrası mekanizma, ders cümlesi ("Harita yolu görmüyor, telefonları görüyor"). Riser/whoosh efektleri geçişlere oturuyor.
- **04 Gece 3'te gelen telefon (Sen karar ver):** "Sen" dili, üstte kalıcı HUD (1. BÖLÜM, saat, STRES çubuğu, KASA tutarı) gerilimi sayısal olarak yükseltiyor; büyük kalın kelime kelime altyazı sarı vurgu ile; koyu, gece paleti, spot ışık. Sonda A/B seçim kartları + "Yorumlara A ya da B yaz", 2. bölüm vaadi. En hızlı kesim ritmi ve tek müzikli/efektli örnek.

## Ölçüm sınırları (bu kütüphaneye özel)

- OCR, el yazısı/serif ve kelime kelime açılan altyazılarda parça okuma yapıyor (01: "Hig durmamış"); 04'teki kalıcı HUD metni bazen altyazıyla birleşiyor. Metin için transcript'i esas al.
- 01'deki çok sayıda "whip" karakter hareketinden (balta sallama) kaynaklı olabilir; kamera aslında çoğunlukla sabit.
- Müzik yatağı tespiti çok düşük seviyede (01–02 "yok") — ses yalnız anlatım olabilir; kulakla doğrula.
