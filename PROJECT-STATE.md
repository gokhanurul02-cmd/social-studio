# Kaldığımız yer

7 Kasım 2026 itibarıyla Social Studio, yerel analiz ve kodla video üretim araçlarını içeriyor. Cybertruck çalışmasının güncel sürümü v5. Kaynak kodu hem bu depoda hem özel `gokhanurul02-cmd/cybertruck-threejs-study` deposunda korunur.

Hedef, referanslardan görsel dil ve kurgu öğrenerek özgün konularda günlük bir 3D bölüm üretebilmek. Her bölümde konuya uygun tanınabilir bir ünlü karakter isteniyor. Türkçe ve İngilizce kanallar değerlendiriliyor. Bolt ve tribün dalgası pilot önerisi, henüz üretilmedi. Yeni 3–4 referans bekleniyor. Günlük otomasyon ve hesaplara yayın henüz kurulmadı.

Kullanıcı genel 3D görüntüyü beğendi. Dwayne yüz benzerliği ve özellikle anakondanın yutması geliştirilmesi gereken yerler. Yutma sahnesi başarılı bir hareket örneği olarak kullanılmamalı. Yeni referansın kritik birkaç saniyesi önce karşılaştırılmalı.

Final hedefi 1080×1920. Denemeler 540p/720p ve kısa olmalı. Mevcut analizleri tekrar kullan. Kullanıcı uzun bağlam, gereksiz ajan ve tekrarlanan tam render maliyetini azaltmak istiyor.

## Geri yükleme

Bu depoda analiz kodu, kullanım talimatları, referans analizi, 3D kaynak ve yerel ajan becerilerinin kopyaları bulunur. `README.md` ile kurulumu yap. `agent-skills/` altındaki becerilerin kayıtlı kurulum yollarını yeni depo yoluna uyarlayarak Codex veya Claude'a kurabilirsin.

Cybertruck'un referans MP4'ü, v5 master ve önizlemesi ile proje içindeki Xbot rig dosyası, özel Cybertruck deposunun `cybertruck-v5-backup` sürümündeki `cybertruck-v5-media.zip` paketinde tutulur. Sürümdeki `backup-manifest.json`, dosyaların SHA-256 ve boyut bilgilerini içerir. Ayrı deponun README'sindeki geri yükleme adımlarını kullan.

Ana sistem için `social-studio-backup-2026-11-07` etiketi, Cybertruck için `cybertruck-v5-backup` etiketi sabit geri dönüş noktalarıdır.

## 9 Kasım 2026 — ölçümlü analiz geliştirmeleri

İstenen yedi adım ayrı commitlerle tamamlandı: taşınabilir Python paketi ve araç keşfi; zamanlı OCR; ses enerjisi/loudness/ritim; hareket/renk/kesim ölçümleri; kaynak-yöntem-güven içeren özet; SSIM, ses ve zamanlama karşılaştırması; performans verilerini özet ölçümlerine bağlayan analitik. Kılavuz ve ilgili Codex/Claude becerileri güncellendi. GitHub dalı: `analiz-uretim-iyilestirme` (main'e birleştirilmedi).

OCR motorları, librosa ve LPIPS/CLIP isteğe bağlıdır. Yerel analiz varsayılan olarak model indirmez; Whisper için açık `--allow-model-download` gerekir. Eksik motor/model atlama sebebiyle kaydedilir; BPM, konuşma veya tutma oranı uydurulmaz. Ağsız ve motorsuz analiz testi eklendi. Kamera/konuşma-müzik tahminleri kalibre olasılık değildir; 4 fps OCR kısa yazıları kaçırabilir. SSIM/LPIPS/CLIP benzerlik yüzdesi değildir. Pearson korelasyonu örnek sayısıyla gelir, nedensellik göstermez.

Windows, Linux ve macOS CI doğrulaması: 20 temel test + 43 ek test; ek pakette açıkça etkinleştirilmeyen gerçek OCR testi atlanır. Başarılı koşu: https://github.com/gokhanurul02-cmd/social-studio/actions/runs/42608360693 . Doctor çekirdek araçları hazır buldu. Yeni üç saniyelik sesli Cybertruck örneğinde 5 OCR kaydı, 30 RMS ve 29 loudness noktasıyla tüm yeni raporlar üretildi: `jobs/upgrade-av-example-20261109-142336-528028/analysis`. Konuşma bu kısa örnekte kapalıydı. Eski `cybertruck-rebuild-v1/analysis` ve `comparison-v5` dosyaları değişmedi.

Aynı çalışma ağacındaki diğer oturumun kompozisyon/Türkçe OCR/şablon geliştirmeleri korunmuştur; bu teslimin commitlerine dahil edilmeyen değişiklikleri ayrıca gözden geçirin. Kurtarırken dalı seçin, önce WORKFLOWS.md ölçümlü analiz bölümünü okuyun.
