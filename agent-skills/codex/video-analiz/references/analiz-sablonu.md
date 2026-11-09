# ANALIZ.md şablonu

Her bölümü doldur. Önce `TIMELINE.md` ve `summary.md` oku; tabloları onlardan doldur, sonra kareyle doğrula. Ölçemediğin alana `[tahmin]` veya `[bilinmiyor]` yaz, boş bırakma.

---

# <Video adı> analizi

Kaynak: <yol/URL> · Analiz tarihi: <tarih> · Araç sürümü: <git commit>

## 1. Teknik kimlik
| Alan | Değer | Kaynak |
|---|---|---|
| Çözünürlük | 1080×1920 | probe.json |
| fps (rasyonel) | 30000/1001 | |
| Süre / kare sayısı | 22.155 s / 664 | |
| Ses | Opus stereo 48 kHz | probe.json |
| Entegre LUFS / true peak | -14.2 LUFS / -1.1 dBTP | summary.json (yoksa elle ebur128) |
| Konuşma dili | en (tespit/verilen) | transcript.json |
| Muhtemel üretim motoru | Blender Cycles render + CapCut altyazı [tahmin] | gerekçe: ... |

## 2. Formül (tek paragraf)
Videonun neden izlendiğini anlatan 3–5 cümle: vaat, gerilim, ödül, döngü.

## 2b. Neden işe yarıyor (izleyici psikolojisi, `[tahmin]`)
Ölçüme dayalı yorum. Her madde bir ölçüme (zaman/kare) bağlanır ve `[tahmin]` etiketi taşır; izleyici davranışı ölçülmedi.
- Merak boşluğu: hangi soru, hangi saniyede açılıyor, hangi saniyede kapanıyor (boşluk süresi):
- Tekrar kalıbı: neyin kaç kez tekrarlandığı (tur sayısı, aralıkları) ve her turdaki varyasyon:
- Ödül anları: zaman damgaları, ödülün türü (sayı/görüntü/ters köşe) ve onu işaretleyen ölçüm (geçiş, ses tepe noktası, altyazı değişimi):
- Dikkat tutma: ilk 3 s olay yoğunluğu, altyazı grup süresi, sessizlik/boşluk anları:
- Döngü / paylaşım tetikleyicisi:

## 3. Hook (0–3 s)
- İlk karede ne görünüyor, ilk ses ne:
- İlk metin / ilk cümle (kelimesi kelimesine):
- İlk 3 sn'de kesim sayısı, hareket yoğunluğu, ses vurgusu:
- İzleyicide açılan soru (merak boşluğu):

## 4. Anlatı akışı
| # | Zaman (s / kare) | Beat | Amaç (kur / tırmandır / ters köşe / ödül / döngü) |
|---|---|---|---|

## 5. Shot tablosu
| # | Başlangıç–bitiş (s) | Kareler | İçerik | Kamera (açı, lens hissi, hareket, easing) | Geçiş | Ekran metni | Ses olayı |
|---|---|---|---|---|---|---|---|

Kamera hareketlerini şöyle yaz: "alçak açı, geniş lens hissi, 1.37→1.74 s ease-out geri ve yukarı çekiliş, hareket bulanıklığı var".

## 6. Ritim
- Shot süreleri: ortalama / medyan / en kısa / en uzun
- Saniye başına kesim, en yoğun bölüm:
- Kesimlerin beat'e oturma oranı:
- Enerji eğrisi (giriş, tepe noktaları, kapanış):

## 7. Altyazı ve ekran metni
- Font (aday 1–3), ağırlık, boyut (piksel ve ekran yüksekliğine oran), satır başı kelime sayısı:
- Renk, kontur kalınlığı, gölge, vurgu rengi ve hangi kelimeler vurgulanıyor:
- Konum (taban çizgisi y oranı), güvenli alan uyumu:
- Animasyon (pop, kelime kelime, fade), giriş/çıkış süresi kare olarak:
- Her metin grubu ve tam değişim karesi listesi (ayrı tablo veya `onscreen_text.json` referansı).

## 8. Görsel stil
- Palet (hex + yaklaşık oran), sahne bazında:
- Işık (güneş yönü, sert/yumuşak gölge, ortam), malzeme dili (düz, PBR, toon):
- Karakter tasarımı (oran, yüz detayı, animasyon kalitesi):
- Çevre (zemin, ızgara, gökyüzü, sis), derinlik alanı, hareket bulanıklığı:
- Kalabalık / tekrar eden öğeler ve yaklaşık sayıları:

## 9. Ses
- Konuşma: ses tipi (yaş, cinsiyet hissi, enerji), hız (kelime/dk), TTS mi insan mı [tahmin]:
- Müzik: tür, BPM, giriş/çıkış, drop anı:
- Efektler: zaman listesi ve türleri (whoosh, impact, riser, pop):
- Miks: konuşma/müzik dengesi, LUFS:

## 10. Yeniden kurma planı
- Seçilen motor ve gerekçe:
- Katman/kaynak tablosu: her öğe için "kodla kurulacak / hazır asset / yeni üretilecek / orijinal ses".
- Eksik asset'ler ve yerine ne konacak:
- En zor 3 an ve yaklaşım:
- Önizleme planı: hangi zamanlarda 540p still, hangi aralık kısa test render.

## 11. Şablonlaştırılabilir kalıp
Aynı tarzda yeni bölüm üretmek için konudan bağımsız kalıp: hook şekli, beat sayısı ve süreleri, tekrar eden kamera hareketleri, altyazı stili, ses tasarımı kuralları.

## 12. İçerik bayrakları
| Bayrak | Durum (yok / var + ayrıntı) | Not |
|---|---|---|
| Gerçek kişi benzerliği (yüz, ses, isim) | | Yeni üretimde onay/sakınca |
| Marka / logo / ürün (ör. araç markası) | | |
| Telifli müzik / ses (tanınan şarkı, stok bile olsa lisans) | | |
| Çocuk / hassas konu | | |
`ayni-tarzda-uret` bu tabloyu okur; kullanıcıyla netleşmeden bayraklı öğe kullanılmaz.

## 13. Açık sorular ve sınırlar
Ölçülemeyen, emin olunmayan veya kullanıcıya sorulması gereken noktalar.

---

# style.json şeması

```json
{
  "source": "jobs/<is>/source.mp4",
  "format": {"width": 1080, "height": 1920, "fps": "30000/1001", "duration_s": 22.155},
  "engine_guess": {"value": "threejs", "confidence": "orta", "reason": "..."},
  "hook": {"duration_s": 3.0, "first_text": "...", "question": "..."},
  "beats": [{"start_s": 0.0, "end_s": 1.37, "role": "kur", "summary": "..."}],
  "rhythm": {"mean_shot_s": 1.8, "median_shot_s": 1.4, "cuts_per_s": 0.55, "beat_aligned_ratio": 0.7},
  "palette": [{"hex": "#2EC4B6", "share": 0.34, "where": "zemin"}],
  "captions": {"font_candidates": ["Verdana Bold"], "size_ratio": 0.045, "baseline_y_ratio": 0.62,
               "fill": "#FFFFFF", "stroke": "#000000", "stroke_px": 6, "shadow": true,
               "words_per_group": 3, "animation": "pop 3 kare"},
  "camera": ["alçak açı ileri itiş", "hızlı geri çekiliş ease-out", "orbit"],
  "audio": {"voice": "erkek, hızlı, TTS [tahmin]", "language": "en", "music_bpm": 120, "lufs": -14.2, "true_peak_dbtp": -1.1,
            "sfx": [{"t": 1.37, "type": "whoosh"}]},
  "content_flags": {"real_person_likeness": "yok|var: <kim, nasıl>", "brands_logos": ["Tesla Cybertruck"],
                    "copyrighted_music": "yok|var|bilinmiyor", "notes": "..."},
  "measurements_source": {"scenes": "scenes.json + gözle doğrulama", "palette": "kare örnekleme"}
}
```
