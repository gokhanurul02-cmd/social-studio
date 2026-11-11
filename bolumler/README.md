# Zack D. tarzı bölümler (Türkçe + İngilizce)

Bu klasör, Claude ile üretilen bölümlerin **yeniden render edilebilir kaynaklarını** saklar: 3D sahne kodu (Three.js), metinler, kullanıcının ElevenLabs kayıtları (Orçun Togan), kelime zamanları, ses efekti betikleri. Final MP4'ler, wav miksleri ve still'ler burada yok (büyük dosyalar); onlar `jobs/` altında yerel olarak ve Claude projesinin dosya kütüphanesinde duruyor.

| Bölüm | Klasör | Türkçe proje | İngilizce proje |
|---|---|---|---|
| Ya bir sivrisinek senin boyunda olsaydı? | `sivrisinek/` | `project-v2metin/` (final: yorganlı sürüm, ses `ses/kullanici-v2/kayit.mp3`) | `project-en/` (ses `ses/en/kayit.mp3`) |
| Ya bir kurbağanın kalbi sana takılsaydı? | `kurbaga-kalbi/` | `project/` (ses `ses/kullanici-orcun.mp3`) | `project-en/` |
| Asansörün halatı kopsaydı? | `asansor/` | `project/` (ses `ses/kullanici-orcun.mp3`) | `project-en/` |

`sivrisinek/project/` eski (ilk kayıt metnine göre kurulmuş) sürümdür; final değil.

## Başka bir Claude / yeni bilgisayarda kullanmak

1. Bu depoyu (`gokhanurul02-cmd/social-studio`) ve motor deposunu (`gokhanurul02-cmd/cybertruck-threejs-study`) klonla. Kurulum: her iki deponun README'si (Node.js, `npm ci`, `npx playwright install chromium`, Python venv, ffmpeg).
2. Claude'a şunu söyle: *"social-studio deposundaki `bolumler/README.md`, `agent-skills/claude/zdf-video-uret` ve `zdf-analiz` skill'lerini oku."* Skill'leri yerel Claude'a kurmak için `agent-skills/claude/*` klasörlerini `%USERPROFILE%\.claude\skills\` altına kopyala.
3. **Dikkat — mutlak yollar:** her projenin `render/harness.cjs` dosyasındaki `TOOL_ROOT` bu bilgisayardaki `C:\Users\birlik grup\Documents\Codex\tools\cybertruck-threejs-study` yolunu gösterir (node_modules/three oradan). Başka makinede bu satırı kendi klon yoluna çevir. ffmpeg yolu social-studio `bin\ffmpeg.exe`.
4. Render (proje klasöründen): `node render/stills.cjs <out> 540 960 8 <kareler>` ve `node render/video.cjs <out.mp4>`; ses/efekt adımları her bölümün `README-SES.md` / `scripts/` dosyalarında. İngilizce için ortak betikler `jobs/_en_ortak/` (yerel).

## Yeni bölüm için kurallar (kullanıcı tercihleri)
- **Ses:** kullanıcı ElevenLabs'te Orçun Togan sesiyle kendisi kaydeder ve gönderir. Videoda yalnız o kayıt kullanılır (hızlandırma/kesme yok, TTS asla). Metin değişse bile görüntü kayda uyarlanır.
- **Metin:** absürt senaryo önce, gerçekler sonda kısa; kısa ve net son. Bkz. `agent-skills/claude/zdf-video-uret/references/metin-kurallari.md`.
- **Ses efektleri** her bölümde var (Earshot + numpy sentez), konuşmanın ≥14 dB altında, müzik yok, -14 LUFS.
- Teslimden önce: MP4'ten Whisper transkripti = kullanıcı kaydı doğrulaması.
