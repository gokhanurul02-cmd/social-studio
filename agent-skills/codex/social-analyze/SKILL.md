---
name: social-analyze
description: "Analyze a supplied reference video or URL: shots, timing, speech, visual style and audio. Delegates to video-analiz."
---

# social-analyze

Bu beceri `video-analiz` becerisine yönlendirir. Referans video veya URL analizi için `video-analiz` becerisini kullan
(`agent-skills/codex/video-analiz/SKILL.md`): önce `social analyze`, sonra `TIMELINE.md` okuma, gözle doğrulama,
ANALIZ.md + SPEC.md + style.json üretimi.

Araç: `./social.cmd` (tam yolu tırnakla çağır).
Onaylı marka varlıklarını koru, sürümlü iş klasörü kullan, kanıtsız render/sadakat iddiası yazma.

Ölçümlü analizde önce `summary.json`/`summary.md`, sonra `onscreen_text.json`,
`audio_analysis.json`, `visual_analysis.json` okuyun. `analysis.json` içindeki skipped
sebeplerini aktarın; eksik ölçümü sıfır veya başarı saymayın. `--max-frames` varsayılanı 120,
OCR taraması `--ocr-fps 4`; yerel analiz varsayılan olarak ağırlık indirmez.
Karşılaştırmada `--source-analysis` / `--render-analysis` ile mevcut analizleri kullanın.
SSIM/LPIPS/CLIP benzerlik yüzdesi değildir; sahne tablosu, ses gecikmesi ve kesim/metin
sapmalarını inceleyin. Yeni sürüm klasörü kullanın. Ayrıntılar: WORKFLOWS.md ölçümlü analiz bölümü.
