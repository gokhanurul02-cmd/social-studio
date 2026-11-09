---
name: social-rebuild
description: "Recreate a reference video as editable code and a finished MP4, with measured comparison. Redirects to videoyu-kopyala."
---

# social-rebuild → videoyu-kopyala

Bu beceri artık yalnızca bir yönlendirmedir. Belirli bir referans videonun aynısını kurmak için
`agent-skills/codex/videoyu-kopyala/SKILL.md` adımlarını uygula (analiz → temsilî sahne → 540p önizleme
döngüsü → render → `social compare` + `social analyze` + `social stylecheck` → düzeltme → REVIEW.md).

Analiz yoksa önce `video-analiz` (agent-skills/claude/video-analiz). Araç: `./social.cmd`.
Kanıtsız bağlantı, render veya sadakat iddiası yok.

Ölçümlü analizde önce `summary.json`/`summary.md`, sonra `onscreen_text.json`,
`audio_analysis.json`, `visual_analysis.json` okuyun. `analysis.json` içindeki skipped
sebeplerini aktarın; eksik ölçümü sıfır veya başarı saymayın. `--max-frames` varsayılanı 120,
OCR taraması `--ocr-fps 4`; yerel analiz varsayılan olarak ağırlık indirmez.
Karşılaştırmada `--source-analysis` / `--render-analysis` ile mevcut analizleri kullanın.
SSIM/LPIPS/CLIP benzerlik yüzdesi değildir; sahne tablosu, ses gecikmesi ve kesim/metin
sapmalarını inceleyin. Yeni sürüm klasörü kullanın. Ayrıntılar: WORKFLOWS.md ölçümlü analiz bölümü.
