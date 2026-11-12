---
name: zdf-analiz
description: Zack D. Films tarzı (3D, "what if" / "how it works", hızlı altyazılı) bir veya birkaç kısa videoyu saniye saniye, kareden doğrulanmış şekilde analiz eder; her videoya ANALIZ.md ve birden fazla video için kanal kalıbı çıkarır. Kullanıcı bu tarzda video atıp "analiz et" dediğinde veya rakip/ilham kanalını incelemek istediğinde kullan. Genel referans analizi için video-analiz skill'i de geçerli; bu skill o formatın özel ayrıntılarını ve aracın bu formatta yaptığı hataları ekler.
---

# Zack D. Films formatı analizi

Kullanıcı yüzeysel ölçüm dökümünden rahatsız oluyor. Hedef: videoyu **izlemeden anlatan** bir analiz: her altyazı grubunda ne söylendiği, ekranda somut olarak ne olduğu, kameranın/geçişin ne yaptığı ve o anın amacı. Örnek kalite: `references/` içindeki örnekler ve `zdf-video-uret/references/ornek-analizler/` (8 video).

Araç kökü: `C:\Users\birlik grup\Documents\Codex\tools\social-studio`. Kullanıcının videoları genelde `C:\Users\birlik grup\Downloads` veya Claude yüklemeleri (`.claude\uploads\...`) altında; proje kütüphanesindeki 25 MB üstü dosyalar okunamıyor, önce yerelde ara.

## 1. Ölç
```
social.cmd analyze "<video>" --out "jobs\zdf\<kısa-ad>\analysis" --language auto
```
Birden çok video varsa sırayla tek PowerShell döngüsünde, arka planda çalıştır (log klasörünü önce oluştur). Video başına 1.5–2.5 dk.

## 2. Gözle doğrula (atlanamaz)
Proxy'den her 10. karenin numaralı tile'ı:
```
bin\ffmpeg.exe -v error -y -i analysis\proxy-540p.mp4 -vf "select='not(mod(n\,10))*between(n\,A\,B)',scale=180:-2,drawtext=text='%{n}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=8x7" -frames:v 1 -fps_mode passthrough inspect\partN.jpg
```
A..B = 560 karelik dilimler; tile k = kare A+10k; zaman = kare / fps. Belirsiz anlarda (geçiş, ters köşe) 2–3 karede bir yoğun tile çek. Bu formatta aracın bilinen hataları (`references/arac-hatalari.md`): geçişleri ~2 kat fazla sayar, whip/zoom burst içine saklanmış kesmeleri kaçırır, makroda çekim tipini "crowd" der.

## 3. Yaz: `jobs\zdf\<ad>\ANALIZ.md`
Bölümler (örnek: `zdf-video-uret/references/ornek-analizler/00-hummingbird.md`):
1. Kısa özet / formül (alt tür: ya şöyle olsaydı / süreç)
2. Teknik kimlik (süre, kelime, kelime/dk, duraklama, LUFS/TP, gerçek sahne sınırı, altyazı grubu ve süresi)
3. **Saniye saniye tablo**: zaman · kare · söylenen · ekranda (somut) · kamera/geçiş · amaç
4. Altyazı · 5. Görsel dil (dünyalar, karakter, palet, kamera imzası) · 6. Ses
7. Neden işe yarıyor (hook, ters köşe(ler), doruklar, son — zaman damgalı)
8. Aynı tarzda yapmak için kalıp · 9. İçerik bayrakları · 10. Ölçüm sınırları (aracın yanıldığı yerler kareden düzeltilmiş)
Her iddiada [ö] ölçüm / [g] gözle / [t] tahmin.

## 4. Birden çok video: kanal kalıbı
`jobs\zdf\KANAL-KALIBI.md`'yi güncelle: ölçüm tablosuna yeni satır, ortak iskelette değişen/teyit edilen maddeler, alt tür ataması. Mevcut kalıp: `references/kanal-kalibi.md`.

## 5. Teslim
Kullanıcıya 5–7 maddelik formül özeti + dosyalar (tek videoda ANALIZ.md, çoklu videoda kalıp + zip). Aracın yanıldığı yerleri dürüstçe söyle. Paralel iş gerekiyorsa (≥3 video) videoları ikişer ikişer Sonnet alt agent'larına dağıt; brief'e örnek analizin yolunu ve tile yöntemini koy.
