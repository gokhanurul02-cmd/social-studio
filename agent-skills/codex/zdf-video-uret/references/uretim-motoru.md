# Üretim motoru: cybertruck-threejs-study

Depo: `C:\Users\birlik grup\Documents\Codex\tools\cybertruck-threejs-study` (GitHub: gokhanurul02-cmd/cybertruck-threejs-study). Zack D. Films Cybertruck videosunun kodla yeniden kurulumu; **kullanıcı v5'in genel görsel kalitesini beğendi**. `README.md`, `AGENTS.md`, `REVIEW.md` (v3→v5 ne işe yaradı, ne yaklaşık kaldı) ve `project/README.md`'yi oku.

## Dosya haritası (`project/`)
| Dosya | İş | Yeni bölümde |
|---|---|---|
| `src/main.js` | renderer, alt-kare birikimi (8 örnek: hareket bulanıklığı + DOF + AA), **kart çevirme ve zoom-whoosh** kompozitleme, ACES grade, altyazı katmanı | olduğu gibi kullan; altyazı stilini koru |
| `src/shots.js` | zaman çizelgesi, kamera anahtarları `[t, px,py,pz, tx,ty,tz, fov, aperture, roll]` (Catmull-Rom spline), sahne kurulumu, altyazı tablosu | **ana düzenleme noktası**; zamanları kelime zamanlarından üret |
| `src/env.js` | gökyüzü/bulut shader, ızgara zemin, güneş + IBL | yeni dünyalar burada (pist, laboratuvar, x-ray boşluğu) |
| `src/characters.js` | Xbot iskeleti + **MakeHuman CC0 sürekli gövdeler** (bebek, genç erkek, kaslı), kemik oranları, poz, shader ile boyanan giysi | kanal karakterini buradan kur (kendi tişört rengi/logosu) |
| `src/props.js` | instanced kalabalık, ipler, yılanlar, kan | kalabalık patlaması için instancing örneği |
| `render/stills.cjs` | seçili kareleri çiz: `node render/stills.cjs OUT 540 960 8 t1.9,t12.5` | kalite kapısı 1 |
| `render/video.cjs` | tüm film → MP4: `node render/video.cjs OUT.mp4 [w h samples]` | ses yolunu yeni bölümün sesine çevir (şu an `reference-source.mp4`'ü muxluyor) |
| `../scripts/build_mh.mjs` | MakeHuman hedeflerinden gövde JSON'u | yeni gövde tipi için |

## Yeni bölüm nasıl kurulur
1. `jobs/<tarih>-<konu>/project` altına `project/` klasörünü kopyala (orijinale dokunma). `node_modules` ve `bin/ffmpeg.exe` depo kökünden kullanılır; gerekirse `npm ci` + `npx playwright install chromium` (README).
2. `shots.js`'i sıfırdan kur: `TIMELINE`'ı kelime zamanlarından (`kelimeler.json` / transcript) üret; elle saniye yazma.
3. Dünyaları kur: gündelik sahne (env.js), x-ray anatomi (karanlık zemin + fresnel/emissive damar shader'ı), iç kesit (clipping plane ile deri/kas/kemik katmanları — `renderer.localClippingEnabled` hazır).
4. Geçiş: ters köşede `main.js`'teki kart çevirme; dalışlarda zoom-whoosh.
5. Altyazı: Verdana Bold (Windows), beyaz + siyah kontur, 1–4 kelime, kesme; taban çizgisi y≈0.72–0.79 (0.79 referans ama alt %20 güvenli alanı ihlal ediyor, Türkçe kanalda 0.72 öner).
6. Ses: Edge TTS çıktısını `video.cjs`'e mux et.

## Ne işe yaradı / ne yaramadı (REVIEW.md'den)
- ✓ Seek tabanlı deterministik render, gerçek hareket bulanıklığı, DOF, kart çevirme, ölçülmüş renkler, kare doğruluğunda altyazı.
- ✓ v4: Xbot "manken" yüzeyi yerine MakeHuman CC0 sürekli gövdeler → belirgin kalite artışı.
- ✗ Prosedürel kafalar/yüzler yapay duruyor; ifade için yüz detayı gerekiyor (v5'te projeksiyon dokusu kullanıldı — yeni bölümde başka kanalın karesinden doku alma, kendi CC0 kaynağını kullan).
- ✗ Prosedürel pozlar (eğilme, çekme) referans animasyondan cansız; mümkünse CC0 mocap klibi.
- ✗ social-studio'daki kedi/at denemesi (low-poly Quaternius) ve SVG bölümü bu formatın çok altında kaldı: low-poly/flat stil kullanma.

## Süre
Cybertruck 22 s, 4K'da ~2 dk render; 1080p 35 s bir bölüm birkaç dakika. Asıl süre sahne kurulumunda: sahne başına bir oturum planla, önce hook sahnesini referans seviyesine getir.
