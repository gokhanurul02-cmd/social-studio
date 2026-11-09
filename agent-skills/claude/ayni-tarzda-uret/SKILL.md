---
name: ayni-tarzda-uret
description: Analiz edilmiş bir veya birkaç referans videonun stilini (hook yapısı, ritim, kamera dili, altyazı, ses tasarımı) kullanarak özgün bir konuda yeni bir dikey kısa video üretir ve stil uyumunu `social stylecheck` ile ölçer. Kullanıcı "bu tarzda yeni bir video yap", "günlük bölüm üret", "şu konuyu bu formatta anlat" dediğinde kullan.
---

# Aynı tarzda özgün bölüm üret

Hedef, referansların **formülünü ve kalitesini** taşıyan ama konusu, senaryosu, karakterleri ve sahneleri özgün bir video. Referansın metnini, sahnelerini veya karakterlerini kopyalama. "Aynı kalite" iddiası ancak `social stylecheck` raporu + kare incelemesiyle yapılır.

Araç kökü: `C:/Users/birlik grup/Documents/Codex/tools/social-studio` (`social.cmd`, `.venv\Scripts\python.exe`, `bin\ffmpeg.exe`, `node_modules` içinde three@0.187.0 + playwright). Çalışan örnek: `jobs/20261109-agent5-style-test/` (kedi/at/otobüs, Three.js, v1→v3, stylecheck PASS; `README.md`, `REVIEW.md`).

## 0. Önce kurallar ve kanıtlanmış referanslar

`references/hikaye-ve-sahne-kurallari.md` dosyasını oku (hikâye kalıpları, kelime/süre ölçüsü, sahne planı, kelimeye kilitli zamanlama, kontrol listesi, yaşanmış hatalar). Konu bir anlatı/animasyon videosuysa `jobs/referans-kutuphanesi/` altındaki 4 tutmuş videodan kalıba en yakın olanın `ANALIZ.md` + `analysis/` klasörünü stil kaynağı olarak kullan ve stylecheck'i ona karşı çalıştır. Hikâye ve sahne planı tablosu hazır olmadan kod yazma.

## 1. Stil kaynağı

- Referansın `jobs/<is>/style.json`, `ANALIZ.md` ve `analysis/` klasörü gerekir. Yoksa önce `video-analiz` skill'ini çalıştır.
- `style.json` yanında `analysis/` klasörü dursun: stylecheck palet, geçiş, altyazı gibi metrikleri **aynı otomatik ölçümle** iki tarafta karşılaştırır (elle ölçülmüş değer otomatik ölçümle karşılaştırılmaz).
- Birden fazla referans varsa `jobs/_stil/<stil-adi>/style.json` birleşik dosyası çıkar: ortak kalıplar kalsın, tek videoya özgü olanlar çıksın. Onaylanmış stil dosyasını değiştirme.

## 2. Konu ve senaryo

1. Konu yoksa 3 özgün konu öner (tek cümle hook + neden izlenir). Otomatik ilerleme istendiyse en güçlüsünü seç, gerekçesini yaz.
2. Senaryoyu stil dosyasındaki beat yapısına oturt (`SCRIPT.md` veya `script-vN.json`): her beat için süre, görsel, ekran metni, anlatım, ses olayı.
3. Altyazı gruplarını senaryoda **önceden** belirle: grup başına kelime referans aralığında (ör. 1–4), sayılar kendi grubunda ("2400", "12").
4. Gerçek kişi benzerliği, marka, logo, telifli karakter → önce kullanıcıyla netleştir. Varsayılan: jenerik/prosedürel.
5. Önce 8–12 sn'lik bir kesit (bir tam tur + bir geçiş + ikinci turun başı) üret ve ölç; tam bölüme sonra geç.

## 3. Proje (Three.js örneği)

- Motor stil dosyasından. 3D "kaç tane gerekir" formatı için `jobs/20261109-agent5-style-test/project` iskeletini yeni işe kopyala:
  - `render/harness.cjs` (yerel sunucu + headless GPU Chrome; `/three/` ve `/fonts/` yollarını servis eder), `render/stills.cjs`, `render/video.cjs OUT.mp4 AUDIO.wav [w h samples]`.
  - `src/main.js`: alt-kare örnekleme (motion blur + DOF + AA), 3D kart çevirme ve zoom-burst/whip geçiş shader'ı, 2D altyazı katmanı (çevirmede dönmez).
  - `src/shots.js`: `TIMELINE` (shots / flips / whoosh / sayı anları) + kamera anahtar tabloları; tek düzenleme noktası.
  - `src/env.js`: ızgara zemin + gökyüzü + IBL. `src/animals.js`: primitiflerden hayvan, gait fazı fonksiyonu, instancing için faz bake. `src/bus.js`: jenerik araç.
- Her şey `seek(t)` / `renderFrame(frame)` ile hesaplanır; saat tabanlı animasyon yok. Kalabalık = faz başına `InstancedMesh`.
- Altyazı stilini elle ayarlama: `data/caption-style.json` style.json'dan birebir kopyalanır (font dosyası, `size_ratio·H`, `baseline_y_ratio·H`, dolgu, kontur px@1080, gölge).

## 3b. Karakter ve asset kütüphanesi (rig'li karakter, kalabalık)

Prosedürel primitif karakterler (küre/silindir hayvan, çubuk bacak) referanstaki rig'li, animasyonlu karakterlerin çok altında kalır. Önce kütüphaneye bak:

1. **Seç:** `assets/catalog.json` (id, dosya, lisans, `animations`, `target` ölçek, `forward`, `foot_height_m`, `tris`, `crowd_lod`). Binary'ler git'te yok: `.venv\Scripts\python.exe assets\fetch_assets.py` (URL + sha256 ile indirir/doğrular). Mevcut: at (Quaternius, 2 renk + atlas), kedi (voxel/toon + `cat_shiba_kitbash`: Shiba rig'i + koddan kedi başı), Shiba köpek, insan (generic), kamyon, okul otobüsü (CC BY 3.0 — atıf zorunlu), Poly Haven gökyüzü HDRI.
2. **Eksik asset:** yalnızca açık lisans — CC0 tercih (Quaternius/Poly Pizza, Kenney, Poly Haven, KhronosGroup glTF-Sample-Assets), CC BY ancak atıf satırıyla. Mixamo, hesap isteyen siteler, lisansı belirsiz modeller (ör. three.js örneklerindeki ro.me Horse/Flamingo, Mixamo kaynaklı Xbot/Soldier) yok. Yalnızca doğrudan `.glb/.gltf/.png/.hdr` indir; arşiv açma, çalıştırılabilir yok. Sayfadaki lisansı/yazarı kontrol et → `catalog.json` girdisi (url, sha256, license, attribution) + `assets/LICENSES.md` satırı → `fetch_assets.py` → `node templates/three-crowd/probe/probe.cjs <out> <id>` ile yan/ön/VAT karelerini gözle kontrol et, ölçülen alanları (`size_m`, `foot_height_m`, `tris`, `animations`) kataloğa yaz → `python -m unittest tests.test_assets_catalog`.
3. **Kullan:** `templates/three-crowd/` (README'yi oku). Proje `render/harness.cjs` dosyası şablon harness'ını sarar (`/assets/`, `/crowd/`, `/three/` rotaları). `loadCharacter` (ayak y=0, +Z yön, katalog boyu) → kahramanlar `new Actor(tpl).play('Walk').seek(t)` (SkeletonUtils.clone + `AnimationMixer.setTime`, deterministik), kalabalık `bakeVAT(tpl,'Walk')` + `VATCrowd` (tek InstancedMesh, örnek başına faz/renk/ölçek; `tint: replace|multiply|none`). Koşum, ip bağlantı noktası, yedek kafa gibi ekler `attachToBone` ile — hem kahramanda hem VAT'ta hareket eder; tür uyarlama `bone_tweaks` ile. Çalışan örnek: `jobs/20261109-agent5-style-test/project-v4` (`src/characters.js`, v4/v5).
4. Uygun rig'li karakter yoksa (ör. CC0 gerçekçi kedi bulunamadı) bunu REVIEW.md'de kalan fark olarak yaz; asset uydurma, telifli/hesap gerektiren kaynağa geçme.

## 4. Ses (ücretsiz/yerel)

- **Anlatım:** Edge TTS (anahtarsız; metin Microsoft servisine gider). `social voice` yalnız cümle sınırı verir; altyazıyı kelimeye kilitlemek için örnek projedeki `tools/tts.py` kullan: `WordBoundary` olaylarından `words.json` + `captions.json` üretir, gruplar konuşulan kelimelerle eşleşmezse durur. Whisper yeniden çözümü gerekmez.
  - Erkek enerjik ses: `tr-TR-AhmetNeural`, hız `+25…+30%`. Kadın: `tr-TR-EmelNeural`.
  - Tek çağrıda nokta sonrası ~0.8 s sessizlik olur. Referans turlar arasında konuşmayı kesmiyorsa cümleleri `chunks` ile ayrı sentezle, `gap_before` ≈ 0.2 s ver.
  - ElevenLabs yalnız kullanıcı açıkça isterse ve anahtarı tanımlıysa; varsayılan değil.
  - Onaylanmış sesi görsel düzenleme için yeniden üretme; her ses yeni klasöre (`audio/vN`).
- **Müzik yatağı:** lisans sorunu olmasın diye `tools/mix.py` içinde sentezlenir; konuşmanın ≈12 dB altında, sonda söner.
- **Efekt:** `social sfx sfx render <id> -o x.wav --dur D --peak -16`; dosya başı değil **tepe noktası** vuruşa hizalanır (`accent - peak_s`). Whoosh: whip/burst/flip; pop: sayı ve koşum belirmesi.
- **Loudness:** teslim hedefi -16…-14 LUFS, ≤ -1 dBTP (iki geçişli loudnorm, `mix.py` veya `social master --lufs -15`). Referans miksi (ör. -8 LUFS / +1.5 dBTP clip) **kopyalanmaz**.

## 5. Önizleme döngüsü (tam render'dan önce)

1. 540p, 2–4 sample still: `node render/stills.cjs ../preview/sN 540 960 4 t0.2,t1.0,...` (hook, her geçişin ortası, sayı anı, çekilişin ortası ve sonu).
2. `python tools/sheet.py OUT.jpg 6 <jpg...>` ile tek sayfada gör ve dosyayı gerçekten aç. Kontrol: kadraj (karakter kesiliyor mu, kamera kalabalığın içinde mi), altyazının altında kalan özne, büyük düz renk alanları, aşırı bulanıklık.
3. Düzelt → tekrar still. 1080p tam render ancak bundan sonra (bu iskelette 10 sn ≈ 40 s).

## 6. Ölç ve düzelt (en az 2 iterasyon)

```
social analyze    "jobs/<is>/renders/vN.mp4" --out "jobs/<is>/analysis-vN"
social stylecheck "jobs/<ref>/style.json" "jobs/<is>/analysis-v1" "jobs/<is>/analysis-v2" --out "jobs/<is>/stylecheck-vN"
```

- Rapor metrik bazındadır (referans / yeni / fark / kural / PASS-FAIL-INFO-SKIP); benzerlik yüzdesi yoktur. Eşikler raporda yazılı, `--thresholds dosya.json` ile değişir, `--strict` FAIL'de çıkış kodu 1 verir. Birden çok aday yan yana sütunlanır.
- Metrikler: format/fps, altyazı taban çizgisi/boyu/rengi/kontur/gölge/animasyon, grup başına kelime, grup süresi, altyazı değişim hızı, ilk altyazı, geçiş/s ve türleri (bitişik whip/burst parçaları tek sayılır), kamera aileleri, palet ΔE, LUFS/true peak (teslim hedefi), kelime/dk, hece/s, en uzun konuşma boşluğu.
- Kesit (aday < referansın %80'i) için geçiş yoğunluğu referansın aynı uzunluktaki açılış penceresiyle karşılaştırılır.
- FAIL'leri düzelt, yeni `vN+1` render et (üzerine yazma), tekrar ölç. Sonra **kareleri gözle** incele (`ffmpeg -ss t -frames:v 1` + sheet): stylecheck kompozisyonu, karakter kalitesini ve anlamı ölçmez.
- `social analyze` başka bir iş yüzünden geçici bozuksa birkaç dakika sonra tekrar dene; stylecheck eksik dosyada SKIP verir, LUFS ve geçişleri gerekirse kendisi ölçer (`--no-measure` kapatır).

## 7. Sık hatalar (gerçek denemeden)

- Kamera geri çekilişini tek ease-out ile 10× mesafeye götürmek → log-ölçek hız patlar, analizci fazladan `zoom_burst` sayar, geçiş/s FAIL. Ara anahtarlarla (her adım ≈ ≤1 log birimi/s) çek, flip'e kadar sabit tut.
- Kalabalık sahnesini kamera kalabalığın içindeyken başlatmak (öndeki figür objektifi kapatır).
- Açılışta büyük düz renkli yüzey kadrajı doldurursa analizci "wipe" yanlış pozitifi verir; özneyi arka plandan uzaklaştır, gökyüzü görünsün.
- Turlar arası uzun sessizlik (tek TTS çağrısı) → "en uzun konuşma boşluğu" FAIL.
- Kelime/dk diller arası karşılaştırılamaz (Türkçe kelimeler uzun): farklı dilde wpm ve hece/s INFO'dur; tempoyu boşluk metriği + kulakla değerlendir. Edge Ahmet +28% ≈ 160 kelime/dk ≈ 7 hece/s.
- OCR ince (≈2 px) konturu bazen görmez → kontur satırı INFO; 1080p kareyi yakından incele.
- Her ses/miks/render yeni sürüm adıyla; eski sürümleri silme.

## 8. Teslim

`REVIEW.md` (sürüm tablosu: değişiklik + stylecheck sonucu, kalan farklar) ve `README.md` (yeniden üretim komutları, asset/lisans) yaz. `video-analiz/references/kalite-kontrol.md` içindeki "Özgün bölüm" listesini işaretle. Kullanıcıya MP4 yolu, STYLECHECK.md tablosu, kalan farklar, kapak karesi önerisi ve açıklama taslağı ver. Yayın yalnız istenirse (`social handoff` paketi hazırlar, yayın yapmaz).
