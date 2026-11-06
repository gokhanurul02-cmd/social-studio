"""Save primary-source repository activity and selection rationale; no credentials required."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
REPOS = [
    ('heygen-com/hyperframes', 'Kurulu', 'HTML, GSAP, video render ve düzenlenebilir hareketli grafikler.'),
    ('remotion-dev/remotion', 'Kurulu', 'React tabanlı alternatif video motoru; lisansı kullanım şekline göre inceleyin.'),
    ('remotion-dev/skills', 'Beceri', 'Resmî Remotion agent yönergeleri.'),
    ('SYSTRAN/faster-whisper', 'Kurulu', 'Yerel, kelime zamanlı konuşma çözümü; CPU int8 varsayılan.'),
    ('Breakthrough/PySceneDetect', 'Kurulu', 'Sahne kesme analizi; yumuşak geçişleri gözle de inceleyin.'),
    ('rany2/edge-tts', 'Kurulu', 'Çevrimiçi Türkçe seslendirme; model yerel değildir, internet gerekir.'),
    ('elevenlabs/elevenlabs-python', 'SDK kurulu / anahtar gerekli', 'Premium ses ve efekt servisleri; bu kurulum ücretli üretim çağırmaz.'),
    ('yt-dlp/yt-dlp', 'Kurulu', 'Desteklenen video URL kaynaklarını içeri alma; her site/oturum garantilenmez.'),
    ('Leonxlnx/earshot', 'Mevcut kurulum bağlandı', 'Yerel efekt sentezi, ses seviyesi ve miks kontrolü.'),
    ('gitroomhq/postiz-agent', 'CLI kurulu / hesap gerekli', 'Hesap bağlantısı, dosya yükleme, paylaşım ve analiz.'),
    ('gitroomhq/postiz-app', 'Araştırıldı / sunucu kurulmadı', 'Kendi sunucunda sosyal medya yönetimi. Docker yok; CLI istemcisi hazır.'),
    ('Comfy-Org/ComfyUI', 'Araştırıldı / kurulu değil', 'Model tabanlı görsel/video üretimi; seçili model ve VRAM gerektirir. Çekirdek iş akışı için zorunlu değil.'),
    ('Stability-AI/stable-audio-tools', 'Araştırıldı / kurulu değil', 'Üretken ses model altyapısı; ağırlık erişimi ve model lisansı ayrıca gerekir.'),
]

rows = []
for repo, status, reason in REPOS:
    row = {'repo': repo, 'url': f'https://github.com/{repo}', 'status': status, 'reason': reason}
    try:
        req = Request(f'https://api.github.com/repos/{repo}', headers={'User-Agent': 'social-studio-local',
                       'Accept': 'application/vnd.github+json'})
        with urlopen(req, timeout=20) as response:
            d = json.load(response)
        row.update({k: d.get(k) for k in ['archived', 'pushed_at', 'updated_at', 'stargazers_count', 'default_branch']})
        row['license'] = (d.get('license') or {}).get('spdx_id', 'Bilinmiyor')
    except Exception as e:
        row['verification_error'] = str(e)
    rows.append(row)
    print(repo, row.get('pushed_at', row.get('verification_error')), flush=True)

data = {'verified_at': datetime.now(timezone.utc).isoformat(), 'source': 'GitHub REST API /repos/{owner}/{repo}',
        'selection': 'İş akışına uygunluk, bakım faaliyeti, yerel kurulabilirlik, agent desteği ve lisans. Evrensel en iyi sıralaması değildir.',
        'repositories': rows}
(ROOT/'repositories.json').write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
lines = ['# GitHub araştırması', '', data['selection'], '', f'Kontrol: {data["verified_at"]}', '',
         '| Repo | Son push (UTC) | Arşiv | Lisans | Bu bilgisayarda | Seçim nedeni |', '|---|---|---|---|---|---|']
for r in rows:
    lines.append(f'| [{r["repo"]}]({r["url"]}) | {r.get("pushed_at", "Doğrulanamadı")} | '
                 f'{r.get("archived", "?")} | {r.get("license", "?")} | {r["status"]} | {r["reason"]} |')
(ROOT/'REPOSITORIES.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
