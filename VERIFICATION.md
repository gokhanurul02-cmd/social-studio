# Kurulum ve doğrulama raporu

Kontrol zamanı: 2026-11-05T13:48:21.558242+03:00

Yerel araçların doğrulaması: **GEÇTİ**.

Tam hesap entegrasyonu ayrı değerlendirilir. Claude Code ve Postiz oturumları aşağıda gösterilen durumdadır; bağlı değillerse bu uygulamalardan model/yayın işlemi yapılmış sayılmaz.

| Gereksinim | Güncel kanıt | Sonuç |
|---|---|---|
| Aktif GitHub projelerini bulma | `repositories.json`, GitHub REST son push/arşiv/lisans kayıtları; `REPOSITORIES.md` | 13 repo araştırıldı; seçilen kurulumlar ayrı işaretlendi |
| HTML/koddan video | HyperFrames 0.9.15; `jobs/demo/index.html` ve dört ayrı `compositions/*.html` | Gerçek MP4 renderı alındı |
| React alternatif motoru | Remotion / CLI / renderer 4.0.540; `jobs/remotion-smoke/render.log` | Bağımsız JSX kaynağından 60 kare MP4 üretildi |
| Yerel video ve URL girdisi | Yerel HTTP sunucusundan gerçek MP4 indirme dahil `test_studio.py` | Dosya/URL yolu test edildi; her sosyal site için giriş erişimi garanti edilmez |
| İçerik ve sahne analizi | `jobs/demo-analysis-final/analysis.json`, `scenes.json`, kareler, konuşma JSON/SRT | Dört sahne doğru bulundu; eşikler kayda alındı |
| Türkçe konuşma çözümü | `jobs/demo-analysis-final/transcript.json`, model large-v3-turbo / CPU int8 | Tam deneme cümlesi doğru; düşük güvenli kelime yok |
| Seslendirme | `jobs/demo/assets/voice.mp3` ve cümle SRT; Edge TTS Emel | Gerçek çevrimiçi ses üretimi yapıldı |
| Efekt ve miks | Earshot glide/zing WAV ve ölçüm kayıtları; `jobs/demo/earshot-measure.json` | Efektler hareket vurgu zamanlarına yerleştirildi |
| Mastering | `jobs/demo/social-studio-final.quality.json` ve Earshot ölçümü | −16.0 LUFS, −3.4 dBTP, sıfır clipped sample |
| Video karelerini mastering sırasında koruma | `jobs/demo/master-comparison/comparison.json` | 330/330 kare, MAE 0, ölçü/fps/süre aynı |
| Referans karşılaştırma aracı | Aynı video ve bilerek farklı ölçü/fps/renk/süreli video testleri | Farkları yakaladı; MAE/PSNR estetik benzerlik garantisi değildir |
| Planlama | `social plan`, tarih/saat dilimi ve mevcut takvimi koruma testleri; social-plan becerisi | Agentin dolduracağı taslak CLI ve doldurma yönergeleri hazır |
| Performans analizi | CSV/JSON hesaplayıcı; eksik ve sıfır payda/negatif veri testleri | Yerel veri işleme hazır; canlı hesap bağlantısı ayrıca gerekir |
| Gelen video klasörü | Gerçek dosyayla inbox ve tekrar işlememe testi | Bir kez analiz eder; izleyici kuruludur ama arka planda çalıştırılmadı |
| Codex becerileri | `.agents/skills/social*`, 11 becerinin frontmatter ve giriş yolları kontrol edildi | Hazır; Codex CLI hesabı açık |
| Claude Code becerileri | `.claude/skills/social*`, aynı 11 beceri ve resmî video becerileri | Hazır; Claude abonelik oturumu doğrulandı |
| Ömer’in mevcut Postiz sistemine aktarım | `jobs/omer-handoff-demo.zip`, publication.json ve dosya hash testleri | Çevrimdışı video/kapak/metin/tarih paketi hazır; sunucu bağlantısı bekliyor |
| Terminal | `.local/bin/social.cmd`, `studio.py`, gerçek render/analiz komutları | Hazır; yeni terminalde `social --help` |
| Kullanım kılavuzu | HTML ve Markdown; `guide-verification.json`, masaüstü/mobil ekran görüntüleri | İçindekiler, arama, kopyalama ve mobil taşma testi geçti |
| Python bağımlılıkları | `pip check`, `installed-requirements.txt` | Bağımlılık çakışması yok; faster-whisper için PyAV 16.1.0 sabitlendi |
| Sürüm uyumu | `package-lock.json`, `remotion-versions.txt`; izole Node ve binary SHA-256 kayıtları | Remotion sürümleri eşit; Postiz kendi Node 22.23.4 sürümünü kullanır |
| Resmî becerilerin keşfi | HyperFrames doctor: skillsOutdated=0, skillsMissing=0 | Tek canonical `.agents/skills` yolu; eski kopyalar taranmayan yedek klasöründe korundu |

## Hesaplar ve kalan kullanıcı adımları

| Hesap | Gerçek kontrol sonucu | Gereken adım |
|---|---|---|
| Codex | Giriş yapılmış | ChatGPT hesabıyla giriş mevcut |
| Claude Code | Giriş yapılmış | Yok; claude.ai abonelik OAuth girişi doğrulandı |
| Postiz | Bağlı değil | Ömer’in mevcut sunucu adresi, API sürümü ve erişim yöntemi |
| ElevenLabs | SDK kurulu, bu oturumda API anahtarı yok | İstenirse kendi `ELEVENLABS_API_KEY` anahtarı; ücretli üretim yapılmadı |

## Testler ve sınırlar

12 işlevsel test geçti (`verification-tests.log`). Bunlar gerçek medya işleme, dosya koruma, sahne kesmeleri, karşılaştırma, veri hesapları ve yerel entegrasyon davranışını kapsar. Codex/Claude modelinin herhangi bir videoyu tek seferde kusursuz yeniden kurduğunu ispatlayan genel bir test değildir.

Demo, bu kurulum için kodla tasarlanmış özgün bir videodur. Yeniden analiz edilmesi gerçek video girişinden sahne/kare/ses/konuşma çıkarma akışını doğrular. Önceki onaylı ProAsistan videosu ayrıca analiz edildi; özgün dosya ve marka kaynakları değiştirilmedi.

Her referans için aynı ölçü, fps ve süreyle düzenlenebilir katmanlar oluşturma, render alma, en farklı kareleri inceleme ve düzeltme akışı becerilere yazıldı. Kaynak görüntü, font veya özel çekim yoksa kalan farklar raporlanır. Orijinal videoyu tam ekran oynatıp katmanları yeniden kurmuş gibi gösteren bir kısayol kullanılmaz.

ComfyUI ve stable-audio-tools araştırıldı, çekirdek kuruluma dahil edilmedi. Docker, kendi Postiz sunucusu ve HyperFrames Pro aboneliği kurulmuş/bağlanmış gibi gösterilmez. Gerçek yayın ve canlı hesap analizi, gerekli kullanıcı girişleri tamamlanmadan doğrulanamaz.

## Dosyalar

- `verification.json`: bu raporun makine okunur kanıt dizini.
- `jobs/demo/social-studio-final.mp4`: teslim edilen örnek video.
- `jobs/demo/index.html`: düzenlenebilir HyperFrames kaynak projesi.
- `jobs/remotion-smoke/proof.mp4`: ikinci motorun gerçek render çıktısı.
- `KULLANIM-KILAVUZU.html`: çevrimdışı aranabilir kullanım kılavuzu.
- `KULLANIM-KILAVUZU.md`: kılavuzun metin sürümü.
- `REPOSITORIES.md`: araştırma ve kurulum durumları.
- `skill-consolidation.json`: resmî beceri konumları ve korunan yedekler.
- `POSTIZ-OMER-NOTU.md`: mevcut sisteme bağlantı için paylaşılabilir teknik not.
- `jobs/omer-handoff-demo.zip`: gerçek örnek videodan hazırlanan taşınabilir taslak paket.
