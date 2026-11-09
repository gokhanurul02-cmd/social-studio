---
name: social-check
description: "Review a finished video for technical, visual and audio defects or reference differences."
---

# social-check

This is the local social-studio integration.

Read `WORKFLOWS.md` and only its relevant workflow sections.
Tool entrypoint: `./social.cmd`. Quote its full path in PowerShell.

Run check, inspect representative decoded frames, inspect audio measurements and compare if a reference exists. Report real defects with timestamps and fix them if requested. Do not equate a decode pass with artistic quality.

Use the actual user request and attached files as inputs. Preserve approved brand assets and create versioned job outputs. Do not claim account connection, a successful render, or reference fidelity without evidence.

Ölçümlü analizde önce `summary.json`/`summary.md`, sonra `onscreen_text.json`,
`audio_analysis.json`, `visual_analysis.json` okuyun. `analysis.json` içindeki skipped
sebeplerini aktarın; eksik ölçümü sıfır veya başarı saymayın. `--max-frames` varsayılanı 120,
OCR taraması `--ocr-fps 4`; yerel analiz varsayılan olarak ağırlık indirmez.
Karşılaştırmada `--source-analysis` / `--render-analysis` ile mevcut analizleri kullanın.
SSIM/LPIPS/CLIP benzerlik yüzdesi değildir; sahne tablosu, ses gecikmesi ve kesim/metin
sapmalarını inceleyin. Yeni sürüm klasörü kullanın. Ayrıntılar: WORKFLOWS.md ölçümlü analiz bölümü.
