# Varlık kaynakları ve lisanslar (sivrisinek bölümü, hook sahnesi)

Bu klasör `cybertruck-threejs-study/project` kopyasından türetildi (orijinale dokunulmadı; eski kayıt `ASSETS.cybertruck.md`). `node_modules` (three r187, playwright) cybertruck depo kökünden, `ffmpeg.exe` social-studio `bin/` klasöründen kullanılır (`render/harness.cjs`, `render/video.cjs` içindeki mutlak yollar).

| Dosya | Kullanım | Kaynak | Lisans |
|---|---|---|---|
| `assets/Xbot.glb` | Kanal karakterinin iskeleti (kemik isimleri/klip kaynağı) | three.js r187 örnekleri | Mixamo türevi, three.js örnekleriyle dağıtılır; render içinde kullanım serbest, ham model ayrıca dağıtılmamalı |
| `assets/mh_guy.json` | Kanal karakteri gövdesi (genç erkek, 1.80 m) | MakeHuman `base.obj` + `caucasian-male-young` (1.0) + `universal-male-young-maxmuscle-averageweight` (0.35), `../scripts/build_mh.mjs` ile üretildi (kaynak: `cybertruck-threejs-study/assets/makehuman/`) | CC0 1.0 |
| `assets/mh_baby.json`, `mh_man.json`, `LeePerrySmith.glb`, `Map-COL.jpg`, `Infinite-Level_02_Tangent_SmoothUV.jpg`, `ref_*.png` | Kopyadan kalan Cybertruck varlıkları; **bu sahnede görünmüyor** (`ref_*` yalnız shader uniform'u olarak yükleniyor) | bkz. `ASSETS.cybertruck.md` | — |
| `C:/Windows/Fonts/verdanab.ttf` | Altyazı (çalışma anında okunur) | Windows | Microsoft font lisansı |
| `assets/guy2.json` (v2 karakter, **kullanılan**) | UV'li gövde + oturtulmuş giysi/saç/kaş/kirpik + morph hedefleri (göz kapama sol/sağ, kaş kaldırma, ağız açma, "kurutma" = genç/kaslı → yaşlı/zayıf) | `../scripts/build_guy.mjs`: MakeHuman `base.obj` + aynı makro hedefler; giysiler `.mhclo` barisentrik bağlarıyla (ofset × eksen ölçeği) oturtuldu, `delete_verts` ile altta kalan deri silindi, ağırlıklar helper-tights/hair dahil geometrik + komşuluk yumuşatma | CC0 1.0 |
| `assets/guy/clothes_*.jpg` | Tişört + kot (diffuse/normal/AO) | MakeHuman sistem varlıkları `clothes/male_casualsuit06` (**CC0**, "explicitly released as CC0 in september 2020", Data Collection AB / J. Palmius / J. Hauquier). Tişörtteki MakeHuman logosu ve köşe filigranı silindi, tişört turuncuya boyandı (`../scripts/prep_textures.py`) | CC0 1.0 |
| `assets/guy/skin_diffuse.jpg` | Yüz/deri dokusu | MakeHuman `skins/young_caucasian_male` (young_lightskinned_male_diffuse) | CC0 1.0 |
| `assets/guy/hair_*` , `eyebrow.png`, `eyelashes.png`, `eye_brown.jpg` | Saç (short02, alphaHash kartlar), kaş (eyebrow001), kirpik (eyelashes01), göz (brown) | MakeHuman sistem varlıkları | CC0 1.0 |
| `../_dl/mh_targets/*.target` | eye-left/right-closure, eyebrows-*-inner-up, mouth-open, caucasian-male-old, universal-male-old-minmuscle-minweight | github.com/makehumancommunity/makehuman `data/targets` | CC0 1.0 |

Kaynak paket: `https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip` (280 MB, `../_dl/mh_cc0/`, git dışı; yalnız kullanılan dosyalar `x/` altına açıldı).

## Kodda üretilenler (dış varlık yok)
- `src/mosquito.js` — prosedürel Aedes tipi dişi sivrisinek: eklemli konik tüp bacaklar (koksa-femur-tibia-5 tarsus, beyaz halkalar, pençe, pullar), çizgili segmentli karın, lir desenli kambur toraks, petek bump'lı iridesan bileşik gözler, hortum, palp, tüylü antenler, damarlı/saçaklı yarı saydam kanatlar (canvas dokusu + iridesans), halter. Kafa ayrı pivotta (eğilebilir).
- `src/skin.js` — makro kol derisi: 720×220 segmentli silindir, prosedürel PBR deri (kırışık ağı, gözenek, lekelenme, çil, ince damar, pürüzlülük, sheen, ucuz SSS), instanced kıl (koyu + ayva tüyü).
- `src/room.js` — yatak odası (parke, boyalı duvarlar, pencere, yatak, yastık, komodin+lamba, halı, ay); yorgan karakterin pozlanmış gövdesinden çıkarılan yükseklik alanıyla örtülür (`shots.js: bodyHeightField`).
- `src/track.js` — koşu pisti/çim zemini (metin v1 için; v2'de kullanılmıyor).
- v2 eklemeleri: `mosquito.js` (ayrı karın pivotu → kırmızı balon, yeniden kurulabilen bacak çizgileri → makarna gibi bükülme/kırılma/çökme, kadifemsi kitin + 13 bin instanced pul kartı, x-ray kabuğu, trake boruları + oksijen parçacıkları), `vessels.js` (iskeletten x-ray damar ağı, akış + boşalma cephesi), `section.js` (yorgan kumaşı + deri katmanları + damar kesiti, hortumun labium/fasikül delişi), `room.js` (kapı, çekilebilen/titreyen dökümlü yorgan), `shots.js` (25 çekim, tüm zamanlar kelime zamanlarından).

## Aranan ama kullanılmayan hazır sivrisinek modeli
- **KhronosGroup glTF-Sample-Assets `MosquitoInAmber`** (Loïc Norgeot; sivrisinek taraması Geoffrey Marchal / Sketchfab, **CC BY 4.0**, doğrudan indirilebilir). İndirilip render edildi (`../inspect/probe/sheet.jpg`): kehribardaki kurumuş örneğin fotogrametrisi; kalın kahverengi bacaklar, kırık kanatlar, hortum yok, sivrisinekten çok sinek gibi okunuyor. Uymadığı için **kullanılmadı**, projeden silindi.
- Poly Pizza / Poly Haven / Kenney / Quaternius / Smithsonian 3D'de gerçekçi, doğrudan indirilebilir CC0 sivrisinek bulunamadı (bulunanlar low-poly ya da CGTrader/Sketchfab gibi hesap/ücret isteyen kaynaklar). Bu yüzden prosedürel model kuruldu.
