---
name: videoyu-kopyala
description: Verilen referans videoyu Social Studio ile düzenlenebilir kod olarak (Three.js, Remotion, HyperFrames/GSAP) aynı kompozisyon, hareket, zamanlama ve sesle yeniden kurar ve ölçülmüş bir MP4 teslim eder. Belirli bir videonun aynısını yapma isteği için kullan; genel bir brief'ten yeni video için değil.
---

# Referans videoyu yeniden kur

Başarı ölçütü referansa sadakattir. Genel bir tanıtım videosu, "ondan ilham alan" bir tasarım veya araç demosu başarı değildir. Eski Social Studio demosu reddedildi, görsel referans olarak kullanma.

## 1. Analiz

- `jobs/<is>/ANALIZ.md`, `SPEC.md` ve `style.json` yoksa önce `video-analiz` skill'ini baştan sona uygula. Varsa yeniden analiz etme, onları kullan.
- Referansla birlikte kaynak proje veya repo verildiyse önce onu incele ve asset'lerini kullan. Piksellerden tahmin, son çare.

## 2. Motor ve proje

- Motoru ANALIZ.md'deki üretim motoru tahminine göre seç. Kurulu diye bir şablonu seçme.
  - 3D sahne, kalabalık, kamera uçuşu → Three.js r187 (`three@0.187.0`, araç kökündeki `node_modules`).
  - Tipografi ve kart ağırlıklı motion graphics → HyperFrames/GSAP (`social hf init "jobs/<is>/project" --skip-skills --non-interactive`) veya Remotion.
  - Gerçek çekim → orijinal ya da yeni çekilmiş görüntü gerekir. Kullanıcıya hangi görüntülerin eksik olduğunu söyle.
- Proje kuralları:
  - Bütün sahne, kamera ve animasyon durumu `seek(zaman)` ile hesaplanır, saat tabanlı animasyon yok.
  - Shot zamanları ve kamera anahtarları tek bir dosyada (ör. `src/shots.js`) tablo olarak durur, SPEC.md'deki shot tablosuyla birebir eşleşir.
  - Fontlar, GSAP ve modeller yerel dosya. Render sırasında CDN'e bağımlılık yok.
  - Örnek yapı: `jobs/cybertruck-rebuild-v1/project` (main.js, shots.js, render/stills.cjs, render/video.cjs). Daha küçük ve temiz iskelet (prosedürel karakter, instanced kalabalık, kart çevirme + whip shader'ı, style.json'dan okunan altyazı stili, `video.cjs OUT AUDIO`): `jobs/20261109-agent5-style-test/project`.
  - Altyazı stilini koda gömme: `data/caption-style.json` style.json'dan birebir (font, `size_ratio`, `baseline_y_ratio`, dolgu, kontur, gölge); zamanlar `data/captions.json`.

## 2b. Karakter ve asset kütüphanesi (rig'li karakter, kalabalık)

Prosedürel primitif karakterler (küre/silindir hayvan, çubuk bacak) referanstaki rig'li, animasyonlu karakterlerin çok altında kalır. Önce kütüphaneye bak:

1. **Seç:** `assets/catalog.json` (id, dosya, lisans, `animations`, `target` ölçek, `forward`, `foot_height_m`, `tris`, `crowd_lod`). Binary'ler git'te yok: `.venv\Scripts\python.exe assets\fetch_assets.py` (URL + sha256 ile indirir/doğrular). Mevcut: at (Quaternius, 2 renk + atlas), kedi (voxel/toon + `cat_shiba_kitbash`: Shiba rig'i + koddan kedi başı), Shiba köpek, insan (generic), kamyon, okul otobüsü (CC BY 3.0 — atıf zorunlu), Poly Haven gökyüzü HDRI.
2. **Eksik asset:** yalnızca açık lisans — CC0 tercih (Quaternius/Poly Pizza, Kenney, Poly Haven, KhronosGroup glTF-Sample-Assets), CC BY ancak atıf satırıyla. Mixamo, hesap isteyen siteler, lisansı belirsiz modeller (ör. three.js örneklerindeki ro.me Horse/Flamingo, Mixamo kaynaklı Xbot/Soldier) yok. Yalnızca doğrudan `.glb/.gltf/.png/.hdr` indir; arşiv açma, çalıştırılabilir yok. Sayfadaki lisansı/yazarı kontrol et → `catalog.json` girdisi (url, sha256, license, attribution) + `assets/LICENSES.md` satırı → `fetch_assets.py` → `node templates/three-crowd/probe/probe.cjs <out> <id>` ile yan/ön/VAT karelerini gözle kontrol et, ölçülen alanları (`size_m`, `foot_height_m`, `tris`, `animations`) kataloğa yaz → `python -m unittest tests.test_assets_catalog`.
3. **Kullan:** `templates/three-crowd/` (README'yi oku). Proje `render/harness.cjs` dosyası şablon harness'ını sarar (`/assets/`, `/crowd/`, `/three/` rotaları). `loadCharacter` (ayak y=0, +Z yön, katalog boyu) → kahramanlar `new Actor(tpl).play('Walk').seek(t)` (SkeletonUtils.clone + `AnimationMixer.setTime`, deterministik), kalabalık `bakeVAT(tpl,'Walk')` + `VATCrowd` (tek InstancedMesh, örnek başına faz/renk/ölçek; `tint: replace|multiply|none`). Koşum, ip bağlantı noktası, yedek kafa gibi ekler `attachToBone` ile — hem kahramanda hem VAT'ta hareket eder; tür uyarlama `bone_tweaks` ile. Çalışan örnek: `jobs/20261109-agent5-style-test/project-v4` (`src/characters.js`, v4/v5).
4. Uygun rig'li karakter yoksa (ör. CC0 gerçekçi kedi bulunamadı) bunu REVIEW.md'de kalan fark olarak yaz; asset uydurma, telifli/hesap gerektiren kaynağa geçme.

## 3. Temsilî sahne önce

1. En karakteristik tek sahneyi seç (genelde hook).
2. Onu kur, 540p still al: `node render/stills.cjs ../preview 540 960 2 t<zaman>,...` veya `social hf snapshot "<proje>" --at ...`.
3. Aynı anların referans karelerini yan yana koy. Kompozisyon, renk, ışık, kamera yüksekliği, lens hissi ve altyazı konumunu karşılaştır. Farkları düzelt.
4. Bu sahne tutmadan diğer sahnelere geçme.

## 4. Filmi tamamla

- Shot tablosunu sırayla kur. Her shot bitince o aralığın 540p kısa test render'ını al ve referansla karşılaştır.
- Altyazılar referansla aynı karede değişmeli, font, boyut, kontur ve konum style.json'a uymalı.
- Aynısı isteniyorsa referans sesini tek, zamanlanmış bir ses kaynağı olarak koru. Anlatım, müzik, başlık, marka veya CTA uydurma.
- Eksik asset'leri (karakter, model, doku) açıkça belirle. Yerine koyduğun her şeyi `ASSETS.md` dosyasına kaynağı ve lisansıyla yaz.
- Orijinal videoyu tam kare arka plan yapıp "yeniden kuruldu" deme.

## 5. Render ve ölçüm

```
node render/video.cjs ../renders/<ad>-v<N>.mp4          (Three.js)
social render "<proje>" --out "jobs/<is>/final-v<N>.mp4"  (HyperFrames)
social compare "<referans>" "<render>" --out "jobs/<is>/comparison-v<N>"
social check "<render>"
```

- Stil metriklerini ölç (piksel farkından bağımsız): `social analyze "<render>" --out "jobs/<is>/analysis-v<N>"` sonra `social stylecheck "jobs/<is>/style.json" "jobs/<is>/analysis-v<N>" [önceki sürümler...] --out "jobs/<is>/stylecheck-v<N>"`. Rapor altyazı konum/boyut/renk, grup süresi, geçiş/s ve türleri, kamera aileleri, palet ΔE, LUFS/true peak ve konuşma temposunu metrik bazında PASS/FAIL verir; benzerlik yüzdesi yoktur. `style.json` yanında `analysis/` dursun ki iki taraf aynı otomatik ölçümle karşılaştırılsın.
- Yeniden kurmada loudness referansla aynı olmalıysa referans sesi korunur; ama referans clip ediyorsa (ör. +1.5 dBTP) stylecheck'in teslim hedefi satırı FAIL verir — bunu REVIEW.md'de bilinçli fark olarak yaz.
- `comparison/index.html` dosyasındaki en kötü anları ve bütün geçişleri kare kare incele. MAE tek başına benzerlik kanıtı değil. Araç güncelse SSIM, ses gecikmesi ve kesim/metin zaman sapmasına da bak.
- Görülen farkları düzelt, `v<N+1>` olarak yeniden render et. Hiçbir sürümün üzerine yazma.
- Final varsayılan olarak 1080×1920. 4K sadece kullanıcı isterse. Tam render'ı gereksiz tekrarlama, önce değişen aralıkları kısa render et.

## Sık hatalar

- Tam render'dan önce 540p still + contact sheet döngüsü atlanırsa kadraj hataları (kamera kalabalığın içinde, özne kesik) ancak 1080p'de görülür.
- Tek ease-out ile çok uzun geri çekiliş analizciye fazladan `zoom_burst` olarak görünür; referansta yoksa ara kamera anahtarı ekle.
- Büyük düz renk alanı kadrajı doldurursa geçiş detektörü yanlış "wipe" verir; stylecheck "referansta yok" notuyla gösterir.
- Yeni anlatım gerekiyorsa (uyarlama): Edge TTS + kelime sınırları (`jobs/20261109-agent5-style-test/project/tools/tts.py`), ücretli sağlayıcı yalnız kullanıcı isterse.

## 6. Teslim

`video-analiz` skill'inin `references/kalite-kontrol.md` dosyasındaki "Yeniden kurma" listesini işaretle. `REVIEW.md` yaz: neyin birebir eşleştiği, neyin yaklaşık olduğu, kalan farklar ve sebepleri, karşılaştırma sayıları ve sürüm sürüm STYLECHECK.md sonucu.

Kullanıcıya oynatılabilir MP4'ü, düzenlenebilir projenin yolunu ve kalan farkların kısa listesini ver. Bağımlılık kontrolü, genel bir demo veya başarılı bir export, videonun yeniden kurulduğunu kanıtlamaz.
