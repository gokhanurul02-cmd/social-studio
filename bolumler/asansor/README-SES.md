# Ses gelince (tek adım)

Kaydı (Orçun Togan, METIN.md v1'in 10 cümlesi, tek dosya) `jobs\20261111-zdf-asansor\ses\kullanici-orcun.mp3` olarak koy
(başka ad/uzantıysa aşağıdaki ilk satırdaki yolu değiştir). Sonra social-studio kökünde (`C:\Users\birlik grup\Documents\Codex\tools\social-studio`) PowerShell:

```powershell
$J = "jobs\20261111-zdf-asansor"
.venv\Scripts\python.exe -X utf8 $J\scripts\kullanici_ses_hazirla.py ses\kullanici-orcun.mp3   # loudnorm -14 LUFS + Whisper kelime zamanları -> ses\kullanici\kelimeler.json, project\voice.json
.venv\Scripts\python.exe -X utf8 $J\scripts\sfx_miks.py                                        # efektler shots.js ile aynı an(c,w) zamanlarında -> ses\kullanici\miks.wav, SFX.md
cd $J\project; node render\stills.cjs ..\inspect\ses-kontrol 540 960 8 pano48; cd ..\..\..    # (önerilir) yeni zamanlarla 48'lik pano: ..\inspect\ses-kontrol\pano.jpg
cd $J\project; node render\video.cjs ..\renders\v1-1080p.mp4; cd ..\..\..                     # 1080x1920 tam render + miks
.venv\Scripts\python.exe -X utf8 $J\scripts\dogrula.py renders\v1-1080p.mp4                    # transkript == kayıt, zaman sapması, LUFS/TP
```

Ne olur:
1. **kullanici_ses_hazirla.py** — kaydı hızlandırmaz/kesmez; yalnız iki geçişli loudnorm (linear) → `ses\kullanici\ses.wav`.
   faster-whisper (large-v3-turbo, yerel) kelime damgaları METIN'in 87 kelimesine hizalanır (kaçırılan kelime komşudan enterpole edilir; çıktıda listelenir).
   `project\voice.json` geçici hece tahmininden (`ses\gecici\kelimeler.json`) bu kayda geçer.
2. **shots zamanları** — elle bir şey yazılmaz: `src\shots.js`'teki her çekim sınırı, kamera vuruşu, olay ve altyazı `an(cümle, kelime)` ile voice.json'daki kelimelere bağlı.
   Açılışta altyazı metni == anlatı kontrolü çalışır; kayıt METIN'den farklı okunduysa sayfa hata verir (hata mesajı iki metni yan yana basar) → METIN/CUMLELER (`scripts\gecici_zaman.py`) ve `SUBS` güncellenir.
3. **sfx_miks.py** — tel kopma tingleri, halat kırbacı, düşüş gürültüsü, fren ciyaklaması + kıvılcım, klank, bonk, ekran tıkları, titreşim, whoosh/flip swish'leri; her efekt konuşmanın ≥14 dB altında, müzik yok → `ses\kullanici\miks.wav` (-14 LUFS, ≤-1.5 dBTP) + `SFX.md`.
4. **video.cjs** — voice.json'daki `mix` ile mux eder (voice.json'da ses yokken çalışmayı reddeder).
5. **dogrula.py** — MP4 sesinden Whisper transkripti, kayıtla eşleşme ve LUFS/TP raporu (`inspect\dogrula.json`).

Notlar:
- Whisper önbelleği `ses\kelimeler-whisper.json`; kaydı değiştirirsen bu dosyayı sil.
- Kalite kapısı: video.cjs'den önce panoyu gözle kontrol et (gerçek kayıtta cümle süreleri değişir; 2,5 s'den uzun sabit kadraj kalmamalı — `cutone` artık `cutone` + `hold` olarak bölündü, `stop` kamera hareketli).
- 720p önizleme için: `node render\video.cjs ..\renders\onizleme-720.mp4 720 1280 6`.
