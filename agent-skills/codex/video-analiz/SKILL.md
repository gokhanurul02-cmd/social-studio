---
name: video-analiz
description: Verilen bir referans videoyu veya linki Social Studio araçlarıyla kare kare analiz edip ölçülmüş bir yapım dosyası (ANALIZ.md + SPEC.md + style.json) çıkarır. Kullanıcı "bu videoyu analiz et", "nasıl yapılmış", "bunun gibisini yapacağız" dediğinde veya yeniden kurma/özgün üretim öncesinde kullan.
---

# Video analizi

Amaç, başka bir ajanın videoyu **hiç izlemeden** aynı kalitede yeniden kurabileceği veya aynı tarzda yeni bölüm üretebileceği kadar ölçülmüş bir yapım dosyası çıkarmak. Teknik metadata özeti yetmez. Her iddia ya ölçüme ya da açıkça "tahmin" etiketine dayanır.

## 0. Hazırlık

- Araç kökü: `social.cmd` dosyasının bulunduğu `social-studio` klasörü. Bilmiyorsan `SOCIAL_STUDIO_ROOT` ortam değişkenine, sonra çalışma klasörüne ve üst klasörlere bak. PowerShell'de tam yolu tırnak içinde çağır.
- Video veya link yoksa tek kısa mesajla iste. Örnek video uydurma.
- Aynı kaynak için `jobs/` altında daha önce yapılmış analiz varsa kontrol et: klasörde **`summary.json` ve `timeline.json` (ve `TIMELINE.md`) varsa** yeniden kullan. Bunlar yoksa analiz eski formattadır; eski çıktıya güvenme, yeni bir iş klasörüne yeniden analiz et (eskisini silme, üzerine yazma).
- Yeni iş klasörü: `jobs/<YYYYMMDD>-<kısa-ad>/`. Var olan klasörün üzerine yazma.
- Dil varsayılanı: `social analyze` konuşmayı Türkçe (`--language tr`) varsayar. Video başka dildeyse `--language auto` (veya `en`, `de` gibi açık kod) ver; yanlış dil transkripti ve kelime zamanlarını bozar. Dil belli değilse önce `auto` ile çalıştır, ANALIZ.md'ye tespit edilen dili yaz. Konuşmasız videoda `--no-speech`.

## 1. Ham ölçümleri çıkar

```
social analyze "<VIDEO_VEYA_URL>" --out "jobs/<is>/analysis"
```

Araç şunları üretir: `analysis.json`, `probe.json`, `scenes.json`, `frames.json`, `contact-sheet.jpg`, `transcript.json`, `onscreen_text.json`, `audio_analysis.json`, `visual_analysis.json`, `transitions.json`, `summary.json`/`summary.md` ve hepsini birleştiren **`timeline.json` + `TIMELINE.md`**. Eksik/atlanan girdiler `TIMELINE.md` başında ve `timeline.json` içindeki `missing` listesinde yazılıdır. Birleştirmeyi tek başına yeniden üretmek için: `python -m social_studio.timeline <analysis_klasörü>`.

**Önce `TIMELINE.md`'yi oku.** Her 0.1 s (ilk 3 s) ve 0.5 s için: konuşulan kelimeler, ekran metni, kamera, geçiş/kesme, ses olayı, enerji. "—" ölçüm yok demektir, "olay yok" demek değildir. Sonra `summary.md`'yi oku (hook olay sayısı, geçiş/s, altyazı grup süresi, LUFS/TP).

Bir dosya yoksa veya `missing` listesindeyse aynı bilgiyi elle çıkar ve ANALIZ.md'de "araçta yok, elle ölçüldü" diye belirt (tarifler 2. bölümün sonunda).

## 2. Gözle doğrula (atlanamaz)

`TIMELINE.md` ve `scenes.json` ölçüm adayıdır, gerçek değildir. Önce tabloyu oku, sonra kareyi aç; çelişki varsa kareye güven.

1. `contact-sheet.jpg` dosyasını aç, videonun genel akışını çıkar.
2. `TIMELINE.md`'deki her kesim/geçiş satırının etrafındaki ardışık kareleri aç. Gerçek kesim mi, dissolve mu, whip pan mı, speed ramp mı, kart çevirme mi, karar ver.
3. **Dedektör 0 veya çok az geçiş verdiyse** (Cybertruck testinde 22 s'lik videoda 1 sahne çıktı; gerçekte 2 kart çevirme + 4 hızlı kamera geçişi vardı) "aday yok" deyip geçme: tüm videoyu 10 fps zaman damgalı şeritlerle tara (aşağıdaki tarif), sonra şüpheli yerlerde 30 fps'e in.
4. Dedektörün kaçırdığı geçişleri bul: aynı arka planlı motion-graphics kesimleri, kamera içi hızlı hareketler, metin değişimleri.
5. İlk 3 saniyeyi kare kare incele. Hook burada.
6. Altyazı ve ekran metninin her değiştiği kareyi bul ve kare numarasıyla yaz (OCR atlandıysa maske taramasıyla).

### Elle ölçüm tarifleri

- **Zaman damgalı 10 fps tile şeridi** (tüm video taraması): her kareye zaman damgası yaz, 8x4 ızgara, her dosya 3.2 s:
  `ffmpeg -i SRC -vf "fps=10,scale=160:-2,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.6,tile=8x4" -vsync 0 strip_%02d.jpg`
  Windows'ta `drawtext` font bulamazsa `fontfile='C\:/Windows/Fonts/arial.ttf'` ekle.
- **Kare numarasıyla çıkarma**: belirli kare aralığı için zamana değil kareye bağlan:
  `ffmpeg -i SRC -vf "select='between(n,120,131)',scale=540:-2" -vsync 0 kare_%02d.jpg`
  UYARI: `-ss` ile birlikte kullanırsan zaman damgaları ±0.2 s (birkaç kare) kayabilir ve `n` aramadan sonra yeniden sayılır. Kare numarası kritikse `-ss`'siz, `-i`'den sonra `select=between(n,a,b)` ile çık; `-ss`'i yalnızca kabaca konumlandırmada kullan ve çıkan kareyi numarayla doğrula.
- **Ardışık kareler (kesim çevresi)**: yukarıdaki `select between(n,a,b)` (a,b = aday kare ± 6).
- **Altyazı bandı maske taraması** (OCR yokken değişim karesi): altyazı bandını kırp, değişen kareleri listele:
  `ffmpeg -i SRC -vf "crop=iw:ih*0.18:0:ih*0.55,scale=270:-2,format=gray,select='gt(scene,0.02)',showinfo" -f null -` ve çıktıdaki `n:` / `pts_time:` değerlerini al. Bant konumunu önce bir kareden ölç; eşiği 0.01–0.05 arasında dene, bulunan her değişimi kareyi açarak doğrula.
- **Ses vurguları ve ses seviyesi**: `ffmpeg -i SRC -af "ebur128=peak=true" -f null -` (entegre LUFS, LRA, true peak) ve `silencedetect=n=-35dB:d=0.25`.
- **Renk**: ilgili kareyi açıp baskın renkleri piksel örnekleyerek hex olarak yaz.

## 3. Yapım dosyasını yaz

Şablon: `references/analiz-sablonu.md`. Üç dosya üret:

- `jobs/<is>/ANALIZ.md`: insan ve ajan için okunur rapor (şablonun tamamı, "Neden işe yarıyor" ve "İçerik bayrakları" dahil).
- `jobs/<is>/SPEC.md`: yeniden kurma için ölçülmüş shot tablosu, katman ve kaynak listesi.
- `jobs/<is>/style.json`: makinece okunur stil özeti (format, palet, font, altyazı stili, kamera dili, tempo, ses, `content_flags`). Şema şablonun sonunda.

Kurallar:
- Zamanları saniye (3 ondalık) **ve** kare numarasıyla yaz, kaynak fps'i rasyonel olarak tut (ör. `30000/1001`).
- Her satırda kaynak belirt: `[ölçüm: TIMELINE.md / scenes.json]`, `[ölçüm: kare 0123]`, `[tahmin]`.
- Gözlenen gerçek, çıkarılan stil ve önerilen değişikliği ayrı bölümlerde tut.
- Fontu kesin bilemiyorsan en yakın 2–3 adayı ve ayırt edici glif farkını yaz.
- Videoyu yapan motoru tahmin et (Three.js / Blender render / Remotion / After Effects / gerçek çekim) ve gerekçesini yaz. Yeniden kurma motoru bu karara göre seçilecek.
- "Neden işe yarıyor" bölümü yorumdur: her iddiayı bir ölçüme bağla ve `[tahmin]` etiketle. İzleyici tepkisini ölçemezsin.
- İçerik bayraklarını (gerçek kişi benzerliği, marka/logo, telifli müzik) boş bırakma; yoksa "yok" yaz.

## 4. Kalite kapısı

Teslim etmeden önce `references/kalite-kontrol.md` içindeki "Analiz" listesini tek tek işaretle. Eksik kalan madde varsa ANALIZ.md'nin "Açık sorular ve sınırlar" bölümüne yaz.

## 5. Teslim

Kullanıcıya kısa bir özet ver: videonun formülü (hook, yapı, ritim) 3–5 cümle, yeniden kurmanın zor olacağı 2–3 nokta ve dosya yolları. Raporun tamamını sohbete yapıştırma.

Sonraki adım: aynı videoyu kurmak için `videoyu-kopyala`, aynı tarzda yeni konu için `ayni-tarzda-uret`.
