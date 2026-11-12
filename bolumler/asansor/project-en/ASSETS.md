# Varlık kaynakları ve lisanslar ("Asansörün halatı kopsaydı?")

Bu klasör `jobs/20261109-zdf-kurbaga-kalbi/project` kopyasıdır (o bölüm de `cybertruck-threejs-study/project`'ten türedi). Orijinallere dokunulmadı.
`node_modules` (three r187, playwright) cybertruck depo kökünden, `ffmpeg.exe` social-studio `bin/` klasöründen kullanılır (`render/harness.cjs`, `render/video.cjs`).

## Dış varlıklar (yalnız kanal karakteri)
| Dosya | Kullanım | Kaynak | Lisans |
|---|---|---|---|
| `assets/guy2.json` + `assets/guy/*` | Kanal karakteri: MakeHuman gövde, turuncu tişört + kot (`male_casualsuit06`, logo/filigran silinmiş), deri, saç short02, kaş, kirpik, kahverengi göz, yüz morph'ları (göz kapama, kaş kaldırma, ağız açma) | MakeHuman sistem varlıkları + `data/targets` (kurbağa bölümünün `ASSETS.md`'sinde ayrıntılı) | CC0 1.0 |
| `assets/mh_guy.json` | Karakter gövde iskelet oranları | MakeHuman `base.obj` + makro hedefler | CC0 1.0 |
| `assets/Xbot.glb` | İskelet/kemik isimleri + koşu/yürüme klipleri | three.js r187 örnekleri (Mixamo türevi) | three.js örnekleriyle dağıtılır; render içinde kullanım |
| `assets/mh_baby.json`, `mh_man.json`, `LeePerrySmith.glb`, `Map-COL.jpg`, `Infinite-Level_02_Tangent_SmoothUV.jpg`, `ref_*.png` | Kopyadan kalan; **bu bölümde görünmüyor** (`ref_*` yalnız eski shader uniform'u olarak yükleniyor) | bkz. kurbağa/cybertruck `ASSETS.md` | — |
| `C:/Windows/Fonts/verdanab.ttf` | Altyazı + etiketler | Windows | Microsoft font lisansı |
| Sistem fontu "Segoe UI" | Telefon ekranı arayüz metni (canvas) | Windows | Microsoft font lisansı |

## Kodda üretilenler (dış doku/model YOK, hepsi prosedürel PBR)
- `src/mats.js` — fırçalanmış paslanmaz (canvas tel-çizik dokusu → roughness/bump + anizotropi), boyalı çelik (aşınma), galvaniz (spangle), işlenmiş çelik, beton (kalıp panel izleri, tij delikleri, gözenek, leke; kesit yüzü ayrı ton), granit zemin, çelik halat shader'ı (8 helis demet + tel yönü, gres), her kare yeniden biçimlenen paralel-taşıma tüpü (`Tube`).
- `src/cabin.js` — kabin içi: dikey taneli paslanmaz paneller + derzler, süpürgelik, arka duvarda **gerçek düzlemsel ayna** (`three/addons Reflector`), paslanmaz tutunma barları, koyu tavan çerçevesi + 2 LED difüzör panel (`RectAreaLight`) + havalandırma yarıkları, ortadan açılır kapılar + **kapı aralığı** + oluklu eşik, kat butonlu kabin panosu (buton yüzleri canvas, alarm butonu) ve **iki nokta-matris kat göstergesi** (pano + kapı üstü; "20" → "19" → "18", yön oku). Kabin için ayrı IBL (`cabinEnvironment`).
- `src/shaft.js` — yarı kesik bina: beton kuyu (kesit yüzleri açık ton), 21 kat döşemesi + koridor duvarları + kesik eşikler, boyalı kat numaraları, kuyu lambaları, kuyu dibi + tamponlar; **iki T89 kılavuz ray** (işlenmiş bıçak + boyalı flanş, galvaniz braketler) + karşı ağırlık rayları; kabin (galvaniz sac + nervürler, paslanmaz kapılar, kapı operatörü), **askı çerçevesi** (U-profil dikmeler, üst/alt kirişler), kılavuz pabuçları, sarı kabin üstü korkuluğu, **6 halat bağlantısı** (dişli çubuk + yay + somun + soket), güvenlik kolu; **progresif güvenlik freni** (açık gövde, iki tırtıklı kama; `setGear(k)` ile kamalar yukarı-içe kayıp raya kenetlenir; rayda kızgın sürtünme izi shader'ı); karşı ağırlık (çerçeve + 26 dolgu bloğu); makine dairesi (6 oluklu tahrik kasnağı, kanatlı motor, fren tamburu + pabuçlar, şase); **hız regülatörü** (oluklu kasnak, cırcır dişleri, iki merkezkaç ağırlık, ayak, şalter, halat çenesi) + ayrı regülatör halatı; 6 askı halatı + kopuk uçlar (`update()` her kare). Kuyu için nötr IBL (`shaftEnvironment`, metallerin mavi gökyüzü yansıtmasını engeller).
- `src/ropesnap.js` — makro halat: 8 demet × 7 tel + 7 telli çekirdek (126 tel tüpü); teller tek tek kopar, uçlar açılır, parlak kırılma uçları, üst yarı geri teper.
- `src/phone.js` — markasız telefon (alüminyum çerçeve, cam arka, kamera adası, delik ön kamera); ekran canvas: mesajlaşma ("Anne", önceki mesajlar, yazılan "anne seni çok seviyorum" + imleç + Türkçe Q klavye, gönderilen balon + kalp + çift tik) ve kilit ekranı ("Anne — 37 cevapsız arama", sayaç 1→37). Gerçek marka/logo yok.
- `src/organs.js` — x-ray mide (J şekli), yemek borusu, bağırsak kıvrımları; `lift` ile mide boğaza kalkar. Mevcut `vessels.js` + `props.js: makeRibcage` ile.
- `src/fx.js` — deterministik kıvılcım sağanakları (balistik, soğuyan renk), parlama sprite'ı, "bonk" yıldızları (bevelli 3D), hız okları + etiketler.
- `src/characters.js` (eklemeler) — pozlar `phone`, `float`, `squat`, `jumpUp`; `curlFingers` (telefonu kavrayan parmaklar, yerel Z ekseni).

## Hız karşılaştırması
Etiketlerde sayı YOK (koordinatör kararı: kaynaksız km/sa kaldırıldı); yalnız "DÜŞÜŞ" / "ZIPLAMA" ve okların boy farkı (2,4 m'ye 0,22 m ≈ 11:1, kaba fizik oranı: 60 m düşüş ≈34 m/s, 0,5 m sıçrama ≈3 m/s).

## Devre dışı (kurbağa bölümüne özgü)
`src/_kurbaga/` altında, hiçbir yerden import edilmiyor: `frog.js`, `hearts.js`, `track.js`, `shots.kurbaga.js`. `mosquito.js` (yalnız `BUMP_GLSL`), `props.js` (`makeRibcage`), `sdf.js` kütüphane olarak duruyor.
