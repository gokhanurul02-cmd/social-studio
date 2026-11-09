# Kalite kontrol listeleri

## Analiz
- [ ] Analiz klasöründe `summary.json` ve `timeline.json`/`TIMELINE.md` vardı (yoksa yeniden analiz edildi) ve ilk iş `TIMELINE.md` okundu.
- [ ] Çözünürlük, rasyonel fps, süre, kare sayısı ve ses formatı probe'dan alındı.
- [ ] Her kesim adayı ardışık karelerle gözle doğrulandı, kaçan geçişler eklendi.
- [ ] İlk 3 saniye kare kare incelendi, hook yazıldı.
- [ ] Her altyazı/metin değişimi kare numarasıyla yazıldı.
- [ ] Font adayları, boyut oranı, konum, kontur ve animasyon ölçüldü.
- [ ] Palet hex olarak sahne bazında çıkarıldı.
- [ ] Her shot için kamera açısı, hareket yönü ve easing yazıldı.
- [ ] Müzik, efekt ve konuşma olayları zamanlarıyla listelendi.
- [ ] Entegre LUFS ve true peak (dBTP) ayrı ayrı ölçüldü ve yazıldı (summary.json veya ebur128).
- [ ] Dedektör 0/az geçiş verdiyse tüm video 10 fps zaman damgalı şeritlerle tarandı.
- [ ] `TIMELINE.md`'deki "—" ve `missing` girdileri elle ölçüldü veya sınırlara yazıldı.
- [ ] "Neden işe yarıyor" bölümü her iddiayı bir ölçüme bağladı ve `[tahmin]` etiketi taşıyor.
- [ ] İçerik bayrakları (gerçek kişi benzerliği, marka/logo, telifli müzik) dolduruldu, style.json `content_flags` var.
- [ ] Konuşma dili tespit edildi/verildi ve yazıldı.
- [ ] Üretim motoru tahmini gerekçeli.
- [ ] Ölçüm ve tahmin her satırda ayrıldı.
- [ ] SPEC.md ve style.json üretildi, ANALIZ.md'nin bütün bölümleri dolu.

## Yeniden kurma
- [ ] Önce tek temsilî sahne referansa eşlendi, sonra filme yayıldı.
- [ ] Bütün sahne ve kamera durumu `seek(zaman)` ile belirleniyor, aynı kare iki kez aynı çıkıyor.
- [ ] Orijinal video arka plan katmanı olarak kullanılmadı.
- [ ] Format (boyut, fps, süre) ve ses referansla aynı ya da kullanıcının istediği şekilde değiştirildi.
- [ ] Altyazılar referansla aynı karede değişiyor (en fazla 1 kare sapma).
- [ ] `social compare` çalıştırıldı, en kötü anlar ve geçişler gözle incelendi.
- [ ] Görülen farklar düzeltildi, yeni sürüm render edildi (v1, v2, ... üzerine yazmadan).
- [ ] Kalan farklar ve yerine konan asset'ler REVIEW.md'de dürüstçe yazıldı.

## Özgün bölüm
- [ ] Konu, senaryo ve sahneler özgün. Referansın metni, karakteri veya sahnesi kopyalanmadı.
- [ ] Hook süresi, beat yapısı, ritim ve altyazı stili style.json ile uyumlu.
- [ ] Gerçek kişi benzerliği, marka ve logo kullanımı kullanıcıyla netleştirildi.
- [ ] Ses -16 LUFS / -1.5 dBTP civarında, `social check` geçti.
- [ ] 1080p finalden önce değişen sahnelerin 540p/720p kısa önizlemeleri alınıp kontrol edildi.
