---
name: zdf-video-uret
description: Zack D. Films tarzında (foto-gerçekçi 3D, "ya şöyle olsaydı?" / "nasıl çalışır?", "sen" dili, ters köşe, iç kesitler, hızlı altyazı) özgün TÜRKÇE dikey kısa video üretir. Konu seçimi, metin, sahne planı, Three.js + MakeHuman üretimi (cybertruck-threejs-study motoru), ses ve kalite kapısını kapsar. Kullanıcı "Zack D tarzı video yap", "kanal için bölüm üret", "şu konuyu bu formatta yap" dediğinde kullan.
---

# Zack D. Films tarzı Türkçe bölüm üret

Hedef: 7 Zack D. Films videosunun ve Cybertruck videosunun ölçülmüş kalıbını taşıyan, **konusu, metni ve karakteri özgün** Türkçe bir dikey video. Referansların metnini, sahnelerini, karakterini veya logosunu kopyalama.

**Kalite çıtası referans videolardır, "çalışan bir video" değil.** Daha önce SVG/düz şekillerle yapılan bir bölüm kullanıcı tarafından "çok kötü" bulunup reddedildi. Foto-gerçekçi 3D (PBR deri, x-ray/neon damar shader'ı, makro DOF, hareket bulanıklığı) olmadan bu format olmaz. Kullanıcı Cybertruck v5'in görsel kalitesini beğendi: alt sınır odur.

Önce oku:
- `references/kanal-kalibi.md` — 7 videonun ortak iskeleti, sayılar, iki alt tür.
- `references/metin-kurallari.md` — Türkçe metin ölçüleri ve kalıplar.
- `references/uretim-motoru.md` — Three.js motoru, dosya haritası, render komutları, neyin işe yaradığı.
- `references/kalite-kapisi.md` — her aşamanın geçme şartı.
- Konuya en yakın alt türdeki `references/ornek-analizler/*.md` (saniye saniye tablolarıyla).

Araç kökleri: `C:\Users\birlik grup\Documents\Codex\tools\social-studio` (analiz, stylecheck, TTS, ffmpeg) ve `C:\Users\birlik grup\Documents\Codex\tools\cybertruck-threejs-study` (3D motor, rig, MakeHuman gövdeler, render harness).

## 1. Konu (kullanıcıyla)
- Alt türü seç: **A. Ya şöyle olsaydı / ters köşe** (karakterli, hızlı, mizahlı) veya **B. Süreç / mekanizma** (karaktersiz, makro, sakin).
- Şart: sonuç **içine girilebilir bir nesneyle** gösterilebilmeli (vücut, alet, tarihî nesne). Gösterilemeyen soyut konu bu formata uymaz.
- 3–5 konu öner; her biri için Türkçe ilk cümle + ters köşe cümlesi + iki görsel doruk. Kullanıcı seçsin (otomatik mod istenmişse en güçlüsünü gerekçesiyle seç).
- Bilimsel/tarihî iddiaların kaynağını bul ve `KAYNAKLAR.md`'ye yaz. Doğrulanamayan sayı yok.

## 2. Metin
`references/metin-kurallari.md`'ye göre yaz; `METIN.md`: satır başına bir altyazı grubu (1–4 kelime) ve her satırın yanında **o an ekranda ne olacağı**. Kontrol: ilk 2 sn'de eylem, "sen" dili, ≤19. sn'de "Ama…" ters köşesi, iki doruk, sayı ile mühür, sert son, CTA yok.

## 3. Ses
- Varsayılan ücretsiz: Edge TTS (`social.cmd voice --provider edge`, ses `tr-TR-AhmetNeural`), kelime zamanları WordBoundary'den. ElevenLabs: kullanıcının ücretsiz planı kütüphane seslerine API'den izin vermiyor; ücretli plan önerme.
- Duraklamasız ya da ≤0.3 s nefes; cümleleri ayrı sentezleyip boşlukları kırp. Hedef tempo `metin-kurallari.md`'de.
- Ses -14 LUFS / ≤-1 dBTP (referanslar -12 ve clip'li; clip'i kopyalama).

## 4. Sahne planı (`SAHNE-PLANI.md`)
- Her altyazı grubu için: dünya (gündelik sahne / x-ray anatomi / iç kesit / laboratuvar), kamera hareketi, geçiş, karakter eylemi.
- Ters köşede dünya değişsin (3D kart çevirme ya da kesite dalış). 2–3 dünya, sabit kanal karakteri (kendi karakterin, Zack D tişörtü/logosu değil).
- 2.5 sn'den uzun sabit kadraj yok (referanslardaki zayıf anlar: dikiş 7–10 s, testere 25–30 s).

## 5. Üretim (3D)
`references/uretim-motoru.md`'yi izle: cybertruck-threejs-study projesini yeni bir iş klasörüne kopyala, `shots.js`'te zaman çizelgesini ve kameraları kelime zamanlarına bağla. Eksik asset için yalnız lisanslı kaynak (CC0 MakeHuman, Quaternius, Poly Haven, social-studio `assets/catalog.json`); kaynağı `ASSETS.md`'ye yaz.

## 6. Kalite kapısı (atlanamaz, `kalite-kapisi.md`)
1. **Tek sahne önce:** hook (0–2 s) ve ilk doruk anından 540p still çıkar, aynı türdeki referans videonun karşılık gelen karesiyle **yan yana** koy, kullanıcıya göster. Onay yoksa tam render yok.
2. 720p kısa önizleme → kullanıcı sesli izler.
3. 1080p final → `social.cmd analyze` + `social.cmd stylecheck <ref analiz> <yeni analiz>` + 48 karelik pano. Ölçüm ve gözle farkları `REVIEW.md`'ye dürüstçe yaz.

## 7. Teslim
Final MP4 (<20 MB ise doğrudan gönder), referansla yan yana 4–6 kare, `REVIEW.md` özeti: neyin referans seviyesinde olduğu, neyin altında kaldığı. "Aynı kalite" iddiası yalnız yan yana karelerle yapılır. Videoyu duyamadığını unutma: ses/görüntü uyumunu kullanıcı onaylar.
