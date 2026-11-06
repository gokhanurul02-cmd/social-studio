# Mevcut Postiz ile bağlantı notu

Önerilen görev dağılımı: Social Studio içerik üretir; Ömer'in geliştirdiği mevcut Postiz
kurulumu hesapları, platform izinlerini, yayınları ve paylaşım sonuçlarını yönetir.
İkinci bir Postiz sunucusu veya rakip yayın kuyruğu kurulmadı. Bu not kimseye gönderilmedi.

## Ömer'e iletilebilecek kısa metin

> Video, kapak, açıklama ve planlanan zamanı hazırlayan yerel üretim sistemi kuruldu.
> Senin geliştirdiğin Postiz'e bağlamak istiyoruz. Mevcut sunucunun adresini ve sürümünü,
> standart Postiz public API'sinin kullanılıp kullanılmadığını, dosya yükleme / taslak oluşturma /
> hesap listesi / analiz uçlarının şemasını paylaşabilir misin? Önce test hesabında yalnız
> taslak aktarımını doğrulayalım. Erişim anahtarı sohbetten değil yerel/güvenli kanaldan tanımlansın.

## Gereken bağlantı bilgileri

1. Kullanılacak sunucu adresi ve geliştirme/test/canlı ayrımı.
2. Sürüm/commit ve standart public API'den değiştirilmiş uçlar varsa onların şeması.
3. Giriş yöntemi: mevcut sunucuya ait API anahtarı veya o sunucunun desteklediği OAuth akışı.
4. Test için kullanılacak gerçek integration/account ID ve platform ayarları.

API anahtarı değerini bu nota veya sürüm kontrolüne eklemeyin. Ömer'in sistemine erişim
sağlandıktan sonra uygun kimlik bilgisi yerelde tanımlanır. Kurulu Postiz CLI OAuth girişi
varsayılan olarak cli-auth.postiz.com kullanır; POSTIZ_API_URL ayarı tek başına OAuth sunucusunu değiştirmez.

## Hazır aktarım sözleşmesi

`social handoff VIDEO --caption-file METIN --out PAKET` bir klasör ve ZIP oluşturur:

- `media/video.mp4`: asıl dosyanın byte düzeyinde korunmuş kopyası (girdi uzantısı korunur).
- `media/cover.jpg`: otomatik seçilen kare; nihai tasarım kapağı gerekirse değiştirilir.
- `caption.txt`: UTF-8 açıklama.
- `publication.json`: `social-studio.handoff.v1`, draft durumu, marka/platform, metin,
  saat dilimli scheduled_at veya null, platform_settings, video bilgileri, göreli dosya
  yolları, boyutlar ve SHA-256 kayıtları.

Bu şema resmî Postiz POST gövdesi değildir. Entegrasyon dosya hash'lerini doğrular, videoyu
mevcut medya yükleme ucuna aktarır, dönen gerçek medya ID/yollarını kullanır ve taslak oluşturur.
Gerçek yayın/zamanlama, kullanıcının belirttiği hedef/tarihle mevcut sistemden yürütülür.
İlk canlı bağlantıda önce salt okunur hesap listesi ve bir test taslağı doğrulanmalıdır.
