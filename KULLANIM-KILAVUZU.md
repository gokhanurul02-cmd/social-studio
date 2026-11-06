# Social Studio · Kullanım kılavuzu

Kurulum: **5 Kasım 2026**. Bilgisayarınızdaki Codex, Claude Code ve terminal için ortak sosyal medya üretim sistemi.

**Güncel öncelik:** insanların Claude Code ile yaptığı belirli videoları referansa sadık
biçimde yeniden oluşturmak. Claude Code'da `/videoyu-kopyala` komutunun arkasına videonun
yolunu veya bağlantısını yazın. Önceki tanıtım demosu kullanıcı tarafından beğenilmedi;
onaylı stil ya da referans eşleştirme başarısının kanıtı değildir. Bu aşamada Postiz ve içerik
takvimi bağlantıları beklenmez; ilk gerekli girdi, yeniden yapılacak gerçek videodur.

## Hemen başla

Codex'te yeni bir mesajda videoyu ekleyip şunu yazın:

```text
$social-rebuild Bu videoyu aynı ölçü, ritim ve görsel dille düzenlenebilir kod olarak yeniden kur. MP4'ü üret, referansla karşılaştır ve görünen farkları düzelt.
```

Claude Code içinde aynı işlem:

```text
/social-rebuild C:/Videolar/referans.mp4 — aynı ölçü, ritim ve görsel dille yeniden kur; bitmiş MP4 ve düzenlenebilir proje ver.
```

Terminalden doğrudan referansla bir Codex oturumu açmak için:

```powershell
social launch codex --source 'C:/Videolar/referans.mp4'
```

Claude Code için:

```powershell
social launch claude --source 'C:/Videolar/referans.mp4'
```

Bu iki komut yerel asistanı normal giriş ve izin ayarlarıyla açar. Kullanıcı hesabınızla çalışır;
ayrı bir API anahtarı gerekmez. Normal Codex/Claude kullanım kotanız geçerlidir.

## Komutları nerede yazacağım?

**Codex sohbeti:** `$social-rebuild` gibi beceri adını yazın. `/skills` menüsünden de seçebilirsiniz.
Codex'in özel beceriler için kullandığı çağrı biçimi `$isim`dir; Claude'daki her `/isim`
kısayolunun Codex'te aynı şekilde çalıştığını varsaymayın.

**Claude Code:** `/social-rebuild` gibi slash komutlarını kullanın. Bunlar bilgisayardaki Claude Code
oturumları içindir. claude.ai web sitesi veya uzak Cowork'a otomatik yüklenmez.

**PowerShell / CMD:** `social analyze ...` gibi terminal komutlarını yazın. Sohbetteki `$social-...`
ifadelerini PowerShell'e yapıştırmayın; PowerShell bunları değişken sanır.

Beceriler yeni oturumda/yeni turda görünür. Menü yenilenmezse Codex veya Claude Code'u yeniden açın.

## Codex ve Claude hesap girişi

Son kontrolde **Codex CLI ChatGPT hesabıyla**, **Claude Code da Claude aboneliğiyle** giriş
yapmış durumda. İki uygulamanın beceri dosyaları kuruldu. Oturum durumunu `claude auth status`
ve `codex login status` ile kontrol edebilirsiniz. Claude Code'da [abonelik veya API/kurumsal giriş](https://code.claude.com/docs/en/authentication)
kullanılabilir; tarayıcıdaki hesabınız terminal oturumuna otomatik yansımayabilir.

Gerekirse aboneliğinizle yeniden giriş:

```powershell
claude auth login
claude auth status
```

Girişten sonra örneğin:

```powershell
social launch claude --prompt 'ProAsistan için onaylı marka stilinde 20 saniyelik Reels oluştur.'
```

API anahtarı kullanacaksanız anahtarı sohbete veya komut geçmişine yazmak yerine bu terminal
oturumuna maskeli girişle aktarabilirsiniz:

```powershell
$env:ANTHROPIC_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Anthropic API anahtarınız' -AsSecureString)).Password
social launch claude
```

Bu yöntem API kullanımını kendi API hesabınızdan ücretlendirir. Anahtar yalnız bu terminal
oturumuna eklenir. Claude ilk kullanımda bu anahtarı kullanmayı onaylamanızı isteyebilir.
Codex oturumunu gerektiğinde `codex login status` ile kontrol edebilirsiniz.

## Sohbet komutları

Tablodaki Claude sütununda `/`, Codex sütununda `$` kullanılır. Arkasına doğal Türkçe talebinizi ekleyin.

| Yapılacak iş | Codex | Claude Code | Çıktı |
|---|---|---|---|
| Genel yönlendirme | `$social` | `/social` | Talebe uygun iş akışı |
| Referans inceleme | `$social-analyze` | `/social-analyze` | Sahne, metin, ritim, hareket ve ses çözümlemesi |
| Videoyu yeniden kurma | `$social-rebuild` | `/social-rebuild` | Düzenlenebilir kaynak, MP4, fark raporu |
| Konudan video oluşturma | `$social-create` | `/social-create` | Senaryo, sahneler, ses isteniyorsa seslendirme, bitmiş video |
| İçerik takvimi | `$social-plan` | `/social-plan` | Doldurulmuş kanca, senaryo, açıklama ve CTA |
| Seslendirme | `$social-voice` | `/social-voice` | Türkçe ses dosyası ve zamanlama |
| Efekt ve miks | `$social-sfx` | `/social-sfx` | Harekete yerleştirilmiş efektler ve miks kontrolü |
| Video kontrolü | `$social-check` | `/social-check` | Zaman kodlu sorunlar, teknik/ses ölçümleri |
| Performans analizi | `$social-analytics` | `/social-analytics` | Gerçek veriden içerik önerileri |
| Paylaşım / zamanlama | `$social-publish` | `/social-publish` | Postiz taslağı veya istenen yayın/zamanlama |
| Gelen video klasörü | `$social-inbox` | `/social-inbox` | Gelen referansın analizi veya istenirse yeniden üretimi |

## Hazır kullanım cümleleri

```text
$social-create ProAsistan için güzellik salonlarına yönelik 20 saniyelik bir Reels yap. Onaylı beyaz-mavi stili ve büyük yazıları kullan. Türkçe seslendir, seçili hareketlere hafif efekt ekle, bitmiş MP4 ver.
```

```text
$social-rebuild Bu referansın sahne geçişlerini ve yazı hareketlerini koru; metinleri Bursa VIP Acil Kurye için değiştir. Önceki onaylı marka stilini de dikkate al. Tek akışta bitir.
```

```text
$social-plan Voyago için 30 günlük Instagram planı hazırla. Her güne kanca, video senaryosu, sahne fikri, paylaşım açıklaması ve CTA yaz. Verisi olmayan en iyi saat veya performans rakamı uydurma.
```

```text
$social-voice Bu metni Emel sesiyle Türkçe oku. Kelime zamanlarını da çıkar. Mevcut onaylı ses varsa onu yeniden üretme.
```

```text
$social-sfx Bu projede kart girişlerine yumuşak kayma, ana geçişlere kısa whoosh, kapanışa tek vurgu yerleştir. Konuşmanın altında tut ve son MP4'ün ses seviyesini ölç.
```

```text
$social-analytics Ekteki Instagram dışa aktarımını incele. İçerik türü bazında kaydetme ve paylaşım performansını karşılaştır; sonraki 10 içerik için test öner.
```

Claude Code'da bu örneklerin başındaki `$` işaretini `/` olarak değiştirin.

## Terminal: temel işlemler

`social` kısayolu `C:/Users/birlik grup/.local/bin/social.cmd` içine kuruldu. Komut tanınmazsa
yeni terminal açın veya aşağıdaki tam yollu çağrıyı kullanın:

```powershell
& 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/social.cmd' --help
```

Bağımlılıkları denetleyin:

```powershell
social doctor
```

`core_ready: true` çekirdek akışın hazır olduğunu gösterir. HyperFrames'in kendi raporundaki
Docker, Kokoro ve MusicGen gibi alternatifler eksik olabilir; bu kurulumda onların yerine
yerel Whisper, Edge TTS ve Earshot kullanılır. Seslendirme için internet gerekir.

Video veya desteklenen URL'yi analiz edin:

```powershell
social analyze 'C:/Videolar/referans.mp4' --out 'C:/Videolar/is-01/analiz'
```

```powershell
social analyze 'https://www.youtube.com/watch?v=VIDEO_ID' --out 'C:/Videolar/is-02/analiz'
```

Varsayılan konuşma modeli **large-v3-turbo**: bilgisayara indirildi ve Türkçe örnekle sınandı.
Daha hızlı taslak için `--model small`, başka dil için `--language auto`, sessiz görüntü için
`--no-speech` ekleyin. URL indirme desteği siteye, oturuma ve kaynak erişimine bağlıdır;
ulaşılamayan bağlantı yerine indirilen yerel dosya kullanılabilir.

Önceki analiz dosyalarını korumak için `--out` klasörü boş olmalıdır; her iş/sürüm için yeni
klasör seçin. Takvim iskeleti de mevcut `calendar.json`/`calendar.csv` dosyalarının üzerine yazılmaz.

Sahne algılama aynı zemini paylaşan hareketli yazı videolarına göre ayarlandı. Çok fazla kesme
çıkarırsa `--scene-threshold 8` gibi daha yüksek eşik deneyebilirsiniz. En kısa sahne süresi
`--min-scene 0.3` ile belirlenir. Kesme listesi yine de görsel incelemeyle doğrulanır.

Analiz klasörü şunları içerir:

| Dosya | İşlevi |
|---|---|
| `analysis.json`, `probe.json` | Ölçü, fps, süre ve medya bilgileri |
| `scenes.json` | Algılanan sahne sınırları |
| `contact-sheet.jpg` | Toplu referans kareleri |
| `frames/`, `frames.json` | Kesme çevresindeki ardışık kareler ve zamanları |
| `audio.wav` | Analiz için çıkarılmış ses |
| `transcript.json` | Konuşma, kelime zamanları ve güven puanları |
| `transcript.txt`, `captions.srt` | Metin ve altyazı |
| `REBUILD.md` | Agent için yeniden kurma başlangıcı |

Terminalde `analyze` analiz paketini hazırlar. Tam video üretimi için Codex/Claude'daki
`social-rebuild` becerisi bu paketi okuyup kaynak kodu oluşturur ve renderı tamamlar.

## Seslendirme ve efekt

Kadın sesi:

```powershell
social voice --text 'Hikâyeni birlikte oluşturalım.' --voice tr-TR-EmelNeural --out 'C:/Videolar/is-01/ses.mp3'
```

Erkek sesi ve dosyadan metin:

```powershell
social voice --file 'C:/Videolar/is-01/metin.txt' --voice tr-TR-AhmetNeural --out 'C:/Videolar/is-01/ses-erkek.mp3'
```

Hız ayarı örneği: `--rate '+10%'`. Mevcut bir ses dosyasının üzerine yazılmaz; yeni sürüm adı seçin.
Edge TTS metni Microsoft'un çevrimiçi servisine gönderir. Ürettiği SRT cümle düzeyindedir.
Kelime düzeyi zamanları ayrıca çıkarın:

```powershell
social transcribe 'C:/Videolar/is-01/ses.mp3' --out 'C:/Videolar/is-01/konusma'
```

Whisper zamanları tahmindir. Düşük güvenli kelimeler `low_confidence_words` içinde işaretlenir;
marka/özel adları ve ilk cümleyi gözden geçirin.

Efektleri listeleyin ve oluşturun:

```powershell
social sfx sfx list --kind whoosh
social sfx sfx render swipe/glide -o 'C:/Videolar/is-01/kayma.wav' --dur 0.5 --apex 0.16 --peak -16
social sfx sfx check 'C:/Videolar/is-01/kayma.wav'
```

Efektin dosya başlangıcını değil, ölçülen tepe zamanını hareketin vurgusuna denk getirin.
Örnek: görsel vurgu 3.00s, efekt tepesi 0.16s ise ses 2.84s'de başlar.
Efekt dosyasını oluşturmak onu videoya eklemez; agent ses katmanı olarak projeye yerleştirir.

Premium ElevenLabs SDK'sı da kurulu. Kendi hesabınızdan `ELEVENLABS_API_KEY` ortam değişkenini
ayarladığınızda `--provider elevenlabs --voice VOICE_ID` kullanılabilir. Bu kurulumda ücretli
ses/efekt üretimi yapılmadı. Anahtarı kılavuza veya herkese açık proje dosyasına yazmayın.

## Kodla video, önizleme ve render

Yeni HyperFrames projesi:

```powershell
social hf init 'C:/Videolar/is-01/proje' --skip-skills --non-interactive --resolution portrait
```

Agent HTML/GSAP sahnelerini doldurduktan sonra:

```powershell
social hf check 'C:/Videolar/is-01/proje' --json
social hf snapshot 'C:/Videolar/is-01/proje' --at 1,3,5
social hf preview 'C:/Videolar/is-01/proje' --background
social render 'C:/Videolar/is-01/proje' --out 'C:/Videolar/is-01/final-v1.mp4'
```

Önizleme komutu gerçek bağlantıyı yazar. Tarayıcıda zaman çizelgesi ve düzenlenebilir sahneler
açılır. İsterseniz [HyperFrames masaüstü uygulamasında](https://hyperframes.studio/) düzenlemeye
devam edebilirsiniz. Yerel render için Pro abonelik gerekmez; sağlayıcının ücretli medya ve
hazır reverse/style servisleri ayrı özelliklerdir.

Alternatif React motoru Remotion da kurulu; resmî beceri Codex ve Claude'ya eklendi:

```powershell
social remotion versions
social remotion compositions 'C:/Videolar/react-proje/src/index.jsx'
```

Remotion paketleri aynı **4.0.540** sürümüne sabitlendi. Kendi kullanımınıza uyan Remotion lisans
koşullarını [projenin lisans sayfasında](https://www.remotion.dev/license) kontrol edebilirsiniz.

## Son kontrol ve referansla karşılaştırma

```powershell
social check 'C:/Videolar/is-01/final-v1.mp4'
social master 'C:/Videolar/is-01/final-v1.mp4' --out 'C:/Videolar/is-01/final-master.mp4'
social compare 'C:/Videolar/referans.mp4' 'C:/Videolar/is-01/final-master.mp4' --out 'C:/Videolar/is-01/karsilastirma'
```

`check`: dosyanın baştan sona açılması, codec/süre ve ses ölçümü.
`master`: iki geçişli -16 LUFS / -1.5dBTP hedefi; video görüntüsü tekrar kodlanmaz.
`compare`: örtüşen zaman aralığındaki bütün çözülebilen kareler, 320px analiz genişliğinde
karşılaştırılır. Ölçü/fps/süre farkları ayrıca kaydedilir. En farklı anlar kaynak / çıktı / fark
olarak `index.html` içinde gösterilir. Bu, “yüzde kaç aynı” estetik puanı değildir;
ses senkronunu, kaynak görüntü kalitesini ve katmanların düzenlenebilirliğini ayrıca inceleriz.

Her video için ilk denemede %100 birebir eşleşme garantisi verilemez. Kaynak görüntü, font,
özel çekim ve model üretimi farklı olabilir. Sistem tek talepte analiz → kurma → render →
karşılaştırma → düzeltme döngüsünü yürütmek için hazırlandı; kalan farklar açıkça raporlanır.

## Planlama ve performans verileri

Agent için tamamlanmış takvim isteği: `$social-plan` / `/social-plan`.
Terminalde yalnızca takvim iskeleti:

```powershell
social plan --brand 'Voyago' --days 30 --start 2026-11-06 --out 'C:/Videolar/voyago-plan'
```

`calendar.json` ve `calendar.csv` taslaktır. Agent marka/hedef kitleye göre kanca, metin ve
açıklamaları doldurur. 19:00 başlangıç varsayımıdır; hesabınızın kanıtlanmış en iyi saati değildir.

Performans dışa aktarımınızı aşağıdaki alanlarla normalize edin veya agentten bunu yapmasını isteyin:

```text
id,platform,date,format,topic,views,reach,likes,comments,shares,saves
```

```powershell
social analytics 'C:/Videolar/performans.csv' --out 'C:/Videolar/performans-raporu.json'
```

JSON dizi de desteklenir. Sayıları binlik ayırıcı olmadan yazın. Etkileşim beğeni + yorum +
paylaşım + kaydetme toplamıdır; oran erişim varsa erişime, yoksa görüntülemeye bölünür.
Eksikler işaretlenir. Farklı platform/paydalı oranları aynı listede körlemesine kıyaslamayın.
Canlı hesap verisi için bağlı Postiz hesabı kullanılabilir; veri yokken gerçek performans iddiası üretilmez.

## Paylaşım ve hesap bağlantısı

Ofisteki mevcut Postiz kurulumunu **Ömer geliştiriyor**. O sistemi yayın merkezi olarak
koruyoruz; ayrı bir kurulum veya varsayılan bulut hesabı açılmadı. Sunucu adresi ve API uyumu
öğrenilene kadar içerikleri çevrimdışı aktarım paketi olarak hazırlayabilirsiniz:

```powershell
social handoff 'C:/Videolar/is-01/final-master.mp4' --caption-file 'C:/Videolar/is-01/aciklama.txt' --brand 'Voyago' --platform instagram --out 'C:/Videolar/is-01/omer-paketi'
```

ZIP içinde video, otomatik seçilmiş kapak, açıklama ve `publication.json` bulunur. Tarih
eklemek için `--scheduled-at '2026-11-06T19:00:00+03:00'` kullanın. Komut yayın/zamanlama
yapmaz; paketi taslak olarak hazırlar. JSON, mevcut sunucunun şemasına eşlenecek ortak bir
sözleşmedir; doğrudan Postiz API isteği değildir.

Ömer'den gereken bilgiler ve aktarım sözleşmesi: [POSTIZ-OMER-NOTU.md](POSTIZ-OMER-NOTU.md).
Mevcut sunucu ve giriş yöntemi belirlendikten sonra bağlantı yapılır. Aşağıdaki giriş komutu
istemcinin varsayılan OAuth sunucusunu kullanır; Ömer'in kurulumuna otomatik bağlandığı varsayılmaz:

```powershell
social postiz auth:login
social postiz auth:status
social postiz integrations:list
```

Hesap girişini tarayıcıda kendiniz tamamlarsınız. API anahtarı yöntemi de desteklenir:
`POSTIZ_API_KEY` ortam değişkeni. Kendi sunucunuzu kullanıyorsanız Postiz'in belgelerindeki
sunucu adresini de ayarlayın. Docker veya Postiz sunucusu bu bilgisayara kurulmadı.

Medya ve taslak hazırlama komutları:

```powershell
social postiz upload 'C:/Videolar/is-01/final-master.mp4'
social postiz integrations:settings GERCEK_INTEGRATION_ID
social postiz posts:create --help
```

Yüklemenin döndürdüğü gerçek medya yolu/ID ve platform ayarlarını kullanın. Örnek taslak metni:

```powershell
social postiz posts:create -c 'Onaylı paylaşım metni' -s '2026-11-06T19:00:00+03:00' -t draft -i GERCEK_INTEGRATION_ID
```

Video paylaşımı için `upload` sonucunun medya alanını da eklemek gerekir; agent bunu mevcut
CLI şemasına göre yapar. `-t schedule` gerçek zamanlama oluşturur. Bir video oluşturma isteği
tek başına yayınlama isteği sayılmaz. Yayın/zamanlama istediğinizde hedef hesap ve tarih
belirli olmalı; işlemden sonra dönen durum ve zaman kontrol edilir.

Postiz için gerekli Node **22.23.4** ayrı kuruldu. Ana Node **24.19.0** değiştirilmedi.

## Bir klasöre video bırakarak çalışma

Hazır gelen kutusu:

```text
C:/Users/birlik grup/Documents/Codex/tools/social-studio/inbox
```

Klasördeki videoları bir kez analiz edin:

```powershell
social inbox
```

Kendi klasörünüzü izleyin:

```powershell
social inbox 'C:/Videolar/Gelenler' --watch
```

Komut terminal açıkken her 5 saniyede kontrol eder. Kopyalanması devam eden dosyayı bekler;
tamamlanan analizleri günlükte tutar. **Ctrl+C** ile durur. Kurulum arka planda sürekli bir
izleyici başlatmadı. Analizden sonra sohbette “`$social-rebuild` en son gelen videoyu tamamla”
veya Claude'da “`/social-rebuild` en son gelen videoyu tamamla” yazabilirsiniz.

## Kurulanlar ve dosyalar

Ana klasör:

```text
C:/Users/birlik grup/Documents/Codex/tools/social-studio
```

HyperFrames, GSAP, Remotion/React, faster-whisper, PySceneDetect/OpenCV, yt-dlp, Edge TTS,
ElevenLabs SDK, Postiz CLI, izole Python ortamı, FFmpeg/FFprobe 9.0.2 ve Postiz için ayrı Node.
Önceden çalışan Earshot kurulumu ortak efekt ve analiz aracı olarak bağlandı.

Codex özel becerileri: `C:/Users/birlik grup/.agents/skills/social-*`.
Claude özel becerileri: `C:/Users/birlik grup/.claude/skills/social-*`.
HyperFrames çekirdek ve Remotion resmî becerileri de kuruldu.
ProAsistan, Bursa VIP, Mika ve psikoloji serisinin önceki onaylı kaynakları korundu.

ComfyUI ve stable-audio-tools araştırıldı; model/VRAM/lisans seçimi gerektiren ayrı üretim
altyapıları oldukları için çekirdek kuruluma eklenmedi. HyperFrames Pro, ElevenLabs hesabı,
Postiz hesabı ve platform izinleri satın alınmış/bağlanmış gibi gösterilmez.

Araştırmanın son push/arşiv/lisans kayıtları: [REPOSITORIES.md](REPOSITORIES.md).
Tam ham kayıt: `repositories.json`. Her repo için durum açıkça yazılıdır.
Kurulu sürümler: `package-lock.json`, `installed-requirements.txt`.
İş akışı ayrıntıları: `WORKFLOWS.md`. Son doğrulama: `VERIFICATION.md`.

## Örnek üretim ve bakım

Hazır örnek: `jobs/demo/social-studio-final.mp4`.
Düzenlenebilir kaynak: `jobs/demo/index.html` ve `jobs/demo/compositions/`.
Örnek: 11 saniye, 1080×1920, 30fps; Türkçe ses, yerel efektler ve kodla animasyon.

```powershell
social hf preview 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/jobs/demo' --background --port 4317
```

Paket sürümleri birlikte sınandı. Güncellemeden önce eski kilit dosyalarını saklayın;
Remotion paketlerinin sürümlerini birbirinden ayırmayın. FFmpeg ve Node binarylerinin kaynak
URL ve SHA-256 kayıtları `bin/` ve `runtimes/node22/` içinde. `social doctor` bir sorun gösterirse
`doctor.json` ve ilgili işin logları teşhise yeterli başlangıç sağlar.

## Resmî kaynaklar

- [HyperFrames](https://github.com/heygen-com/hyperframes)
- [Remotion](https://github.com/remotion-dev/remotion)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect)
- [Edge TTS](https://github.com/rany2/edge-tts)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Earshot](https://github.com/Leonxlnx/earshot)
- [Postiz agent](https://github.com/gitroomhq/postiz-agent)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [Codex becerileri](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code becerileri](https://code.claude.com/docs/en/skills)
