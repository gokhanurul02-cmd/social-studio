# Social Studio

Terminalden video analizi, seslendirme ve düzenlenebilir 3D video üretimi için yerel araçlar. İlk Three.js projesi `jobs/cybertruck-rebuild-v1/project` altında. Kurgu ve kamera `src/shots.js` üzerinden düzenlenir. Dikey final çözünürlüğü 1080×1920.

Windows'ta Python 3.12 ve Node.js 24 ile depo kökünde çalıştır:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npx playwright install chromium
& .\.venv\Scripts\python.exe install_ffmpeg.py
.\social.cmd --help
```

Cybertruck projesi, `project/assets/Xbot.glb` konumunda Three.js r187 örneklerinden [Xbot rig dosyasını](https://github.com/mrdoob/three.js/blob/r187/examples/models/gltf/Xbot.glb) kullanır. Tam render için kendi referans MP4 kopyanı iş klasöründe `reference-source.mp4` adıyla bulundur. Render bu dosyadan ses alır. `SOCIAL_CHROME_PATH` ile kendi Chromium yolunu seçebilirsin.

```powershell
Set-Location jobs/cybertruck-rebuild-v1/project
New-Item -ItemType Directory -Force ../preview, ../renders | Out-Null
node render/stills.cjs ../preview 540 960 2 t8.5,t16.7
node render/video.cjs ../renders/cybertruck-1080p.mp4
```

[Kullanım kılavuzu](KULLANIM-KILAVUZU.md) ve [üretim akışı](WORKFLOWS.md), bu bilgisayardaki mevcut kurulum ve isteğe bağlı entegrasyonlar hakkında ayrıntı içerir.

## Yedekler ve devam etme

[Kaldığımız yer](PROJECT-STATE.md) dosyası kararları, hedefleri ve sonraki işleri içerir. `agent-skills/` altında Codex ve Claude becerilerimizin kopyaları vardır. Cybertruck referansının analiz ve karşılaştırma çıktıları iş klasöründe saklanır.

Çalışmanın bağımsız özel deposu [cybertruck-threejs-study](https://github.com/gokhanurul02-cmd/cybertruck-threejs-study). Bu deponun `cybertruck-v5-backup` sürümünde referans, son master, önizleme ve rig dosyası için doğrulanabilir medya yedeği bulunur. Geri yükleme komutları o deponun README'sinde yer alır.
