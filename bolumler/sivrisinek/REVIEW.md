# REVIEW — "Ya bir sivrisinek senin boyunda olsaydı?" önizleme v1 (2026-11-09)

Teslim: `renders/onizleme-v1.mp4` — 720×1280, 29.97 fps, 37.90 s, 12.1 MB, **geçici Edge TTS** sesi muxlu (`tr-TR-AhmetNeural`, +15 %).
Pano: `inspect/pano48-onizleme-v1.jpg` (videodan 48 kare) · çekim başına 540p still: `inspect/onizleme-v1-stills/` (+ `shots.jpg`) · hook yan yana: `inspect/hook-yanyana-v3.jpg` (üst referans, alt bizim).
Ölçüm: `analysis-onizleme-v1/` (`social.cmd analyze`), `stylecheck-onizleme-v1.md` (Hummingbird referansına karşı).

## 1. Sahne listesi (hepsi `shots.js`'te `an(cümle, kelime)` ile kelime zamanlarından)

| # | Çekim | Başlangıç (s) | Süre | Bağlantı | Ekranda |
|---|---|---|---|---|---|
| 1 | macro | 0.00 | 1.46 | 0 | gece, kolda makro sivrisinek (pullu kadife gövde), "senin" ile büyümeye başlar |
| 2 | night | 1.46 | 1.48 | an(1,5) + zoom-whoosh | yatak odası, insan boyuna büyür |
| 3 | wake | 2.94 | 1.61 | an(2,1) + whoosh | yüz yakın plan, "gözünü"de gözler açılır (MakeHuman göz kapama morph'u) |
| 4 | reveal | 4.55 | 1.01 | an(2,4) + whoosh | "100 kiloluk": yatağın ucunda sivrisinek, 3/4 yakın |
| 5 | ots | 5.56 | 1.80 | an(2,8) | karakterin omzu üstünden, sivrisinek başını yana eğer |
| 6 | pull | 7.36 | 1.71 | an(3,1) | yorgan kafaya çekilir, sonra titrer |
| 7 | probe | 9.07 | 0.74 | an(3,4) | "ama o": kafa + hortum yorgandaki tümseğe iner |
| 8 | pierce | 9.81 | 1.67 | an(3,7) + whoosh | kesit makro: yorgan kumaşı (iplik + elyaf) → epidermis/dermis/yağ → damar, labium bükülür, fasikül girer, kan yükselir |
| 9 | xray1 | 11.48 | 1.10 | an(4,1) + whoosh | x-ray gövde + kırmızı damar ağı, akış kola doğru |
| 10 | xray2 | 12.58 | 1.36 | an(4,4) | "pipetle": hortumun içinden kan parçacıkları yukarı |
| 11 | xray3 | 13.93 | 1.15 | an(4,9) | "tek seferde": damarlar uçlardan kola doğru boşalır |
| 12 | dry | 15.08 | 2.30 | an(5,1) + whoosh | karakter kurur: deri sararır/kırışır, "yaşlı-zayıf" morph, tişört bollaşır |
| 13 | balloon | 17.39 | 1.49 | an(5,7) | karın kırmızı, parlak balon gibi şişer |
| 14 | door | 18.88 | 1.81 | an(6,1) + **3D kart çevirme** | ters köşe: şişko sivrisinek kapıya yürür |
| 15 | legsA | 20.69 | 0.70 | an(7,1) | ilk adım, bacaklar sallanır |
| 16 | legsB | 21.39 | 1.67 | an(7,3) | bacaklar makarna gibi bükülür, "kırılır"da kırık açı |
| 17 | fall | 23.06 | 1.44 | an(7,7) | yere yığılır, sekme + nefes nefese karın pompası, kanat çırpması |
| 18 | tr1 | 24.50 | 1.85 | an(8,1) + **3D kart çevirme** | gerçeklere geçiş: x-ray sivrisinek, trake boruları |
| 19 | tr2 | 26.35 | 1.32 | an(8,5) | yakın: delikten giren oksijen parçacıkları |
| 20 | tr3 | 27.67 | 2.06 | an(8,10) | parçacıklar yolun yarısında söner, gövde kırmızıya döner |
| 21 | sc1 | 29.73 | 1.45 | an(9,1) + whoosh | stüdyo ızgarası: karakterin yanında küçük → dev sivrisinek |
| 22 | sc2 | 31.18 | 1.71 | an(9,6) | "milyonlarca kat": kırmızı ağırlık oku, bacaklar çöker |
| 23 | sc3 | 32.88 | 1.86 | an(9,10) + whoosh | bacak kesiti (kütikül halkası), "güçlenmez"de kırmızı çatlak yürür |
| 24 | fin1 | 34.74 | 1.37 | an(10,1) + whoosh | kapının önünde yatan sivrisinek, arkada kapı |
| 25 | fin2 | 36.11 | 1.79 | an(10,4) | büzüşmüş karakter, "varamaz"da tek gözünü açar; sert son |

En uzun çekim 2.30 s (dry, kamera hareketli); 2.5 s'den uzun sabit kadraj yok. Her altyazı grubunda görsel değişim var.

## 2. Ölçüm — referans kalıbıyla (kanal-kalibi.md, Hummingbird analizi)

| Ölçüm | Bizim (araç) | Referans | Değerlendirme |
|---|---|---|---|
| Süre / kelime | 37.9 s / 101 | ≈33 s / ≈89 (Hummingbird 37.3 s / 111) | aralıkta |
| Kelime/dk | 158 (araç, Whisper) · 162 (TTS sınırları) | 145–180, ort. 159 | **referans seviyesinde** (Türkçe hece hızı 6.6/s, İngilizce 4.4/s → kulakla kontrol) |
| Cümle arası boşluk | 0.06 s sessizlik (kelime sınırı 0.15 s) | yok/≤0.3 | tamam; araç Whisper ile en uzun boşluğu 0.38 s ölçtü (virgül sonrası, TTS kaynaklı) → stylecheck FAIL |
| Altyazı grubu | 56 grup, ort. 0.68 s, 1–3 kelime | 0.80–0.91 s, 2.2–2.6 kelime | biraz hızlı (stylecheck ±25 % içinde PASS) |
| Altyazı stili | Verdana Bold, beyaz + siyah kontur, kesme, y = 0.72 | y ≈ 0.79 | kasıtlı fark (alt %20 güvenli alan); stylecheck FAIL bu yüzden |
| Geçiş/s (araç) | 0.74–0.77 | Hummingbird 0.91–1.07 | biraz altında (stylecheck FAIL, fark 0.17 > 0.15) |
| Gerçek sahne sınırı (gözle) | 24 sınır (9 whoosh, 2 kart çevirme, 13 kesme) → 0.63/s | 0–12 / 30–39 s (≤0.32/s) | **referanstan ~2 kat sık kesme** (2.5 s kuralı yüzünden); düzgün ama "hızlı kurgu" hissi verebilir |
| LUFS / TP | -14.1 / -4.5 dBTP | teslim hedefi -14 / ≤-1 (ref -9.6, clip'li) | PASS |
| Palet | koyu (x-ray dünyası %25 süre) | açık mavi/ten | FAIL (ΔE 16.8) — x-ray ve trake sahneleri siyah zeminli; referansta x-ray yok |

## 3. Gözle değerlendirme (dürüst)

**Referans seviyesinde ya da yakın:**
- Makro hook (pullu, kadifemsi sivrisinek + deri), x-ray trake sahnesi, kırmızı balon karın, altyazı zamanlaması (kelimeye kilitli, kesme), geçiş dili (zoom-whoosh + 3D kart çevirme ters köşede ve gerçeklere geçişte).
- Karakter: düz boyalı kıyafet yerine MakeHuman CC0 tişört + kot (normal + AO haritalı gerçek kumaş kıvrımı), CC0 deri dokusu, kaş/kirpik kartları, gerçek saç kartları (kask görünümü yok), göz kapama/kaş/ağız morph'ları. Yüz yakın planları v2'ye göre belirgin iyi (hook-yanyana-v3).
- Geniş planda sivrisinek artık parlak siyah top değil: pürüzlü kitin + sheen + ~13 bin pul kartı.

**Referansın altında:**
1. **Karakter animasyonu:** pozlar prosedürel (yatarken yorgan çekme el hareketi yok, yorgan "kendi kendine" kayıyor); mocap yok. Kuruma görünümü çizgi-film değil, yeşilimsi/zombi tonuna kayıyor; açık ağız içi boş (diş/dil yok, ağız 0.15'te tutuldu).
2. **Bacak kırılması ve çöküş:** bükülme ve kırık açı var ama Zack D.'deki kadar okunur değil (kırık noktasında kopma/kıymık yok, bacaklar hâlâ kalın tüp). Bacak kesiti (sc3) bağlam olmadan "kablo" gibi okunabiliyor.
3. **Kesit (pierce) ve x-ray sahneleri** referans 3D anatomi kalitesinin altında: deri katmanları düz renk bantları, x-ray'de damar ağı prosedürel ve ince; palet ölçümü de bu yüzden kalıyor.
4. Geçici ses TTS (robotik tını); ses efekti ve müzik yok. Kulakla kontrol edilmedi (ben duyamam).
5. Geçiş sayısı (gözle) referansın ~2 katı: 25 çekim/38 s.

## 4. Yeniden üretim
- Ses: `.venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\gecici_ses.py`
- Karakter: `node jobs\20261109-zdf-sivrisinek\scripts\build_guy.mjs` (MakeHuman CC0 paketi `_dl/mh_cc0/`, hedefler `_dl/mh_targets/`), dokular `scripts\prep_textures.py`
- Still/pano: `cd project && node render/stills.cjs ../inspect/X 540 960 8 shots|pano48|t1.2,t5.0`
- Video: `cd project && set CRF=21 && node render/video.cjs ../renders/onizleme-v1.mp4 720 1280 8` (RTX 2080 Ti'de 77 s)
- **ElevenLabs kaydı gelince tek adım** (social-studio kökünden): `.venv\Scripts\python.exe -X utf8 jobs\20261109-zdf-sivrisinek\scripts\elevenlabs_hazirla.py <kayit.mp3> --render` → ses `-14 LUFS`, Whisper kelime zamanları METIN'e hizalanır (`ses/elevenlabs/kelimeler.json`), `project/voice.json` güncellenir, `renders/onizleme-v2.mp4` çıkar. (Geçici sesle test: 101 kelimenin 97'si eşleşti, ortalama sapma 43 ms.)

---
# v2 (2026-11-09) — kullanıcının kendi kaydı + ses efektleri
Teslim: `renders/v2-1080p.mp4` (1080×1920, 29.97 fps, 37.3 s, 18.4 MB). Ses: `ses/kullanici-orcun.mp3` (Orçun Togan, ElevenLabs) hızlandırılmadan, yalnız normalize; + 27 efekt (`SFX.md`). Edge TTS sesi YOK.
Metin: `METIN.md` v3 (12 cümle). Pano: `inspect/pano48-v2.jpg` (videodan 48 kare), çekim stilleri `inspect/v2-stills/shots.jpg`.
Doğrulama: muxlu dosyadan Whisper large-v3-turbo transkripti kayıt metniyle 90/90 kelime (bir koşuda "milyonlarca"→"nilyonlarca" ASR hatası); ebur128 -14.2 LUFS, TP -4.4 dBTP; aktif konuşma pencerelerinde konuşma–SFX farkı min 14.5 dB, medyan 21.7 dB.
Değişenler: shots.js zaman çizelgesi (24 çekim, `T` tablosu), altyazı grupları (anlatıyla birebir eşleşme kontrolü kodda), section.js kumaş katmanı kapatılabilir, kuruma teni solgun gri-bej, ayakta "eğilme" pozu (bow), yeni çekimler xrayW / tr1b / trBig / fin1-fin2 (ayakta karakter yerde yatan sivrisineğe bakar).
Yeniden üretim: `scripts/kullanici_ses_hazirla.py` → `scripts/sfx_miks.py` → `cd project && set CRF=22 && node render/video.cjs ../renders/v2-1080p.mp4 1080 1920 8`.
