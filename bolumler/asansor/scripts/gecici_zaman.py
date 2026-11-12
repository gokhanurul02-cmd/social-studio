# GECICI kelime zamanlari (ses YOK): METIN.md'nin 10 cumlesinden hece sayisina gore tahmini zaman cizelgesi.
# Yalniz still/sahne hazirligi icin. Kullanici kaydi (Orcun Togan) gelince kullanici_ses_hazirla.py bunu Whisper
# zamanlariyla degistirir ve project/voice.json'u ses/kullanici/kelimeler.json'a cevirir.
#   .venv\Scripts\python.exe -X utf8 jobs\20261111-zdf-asansor\scripts\gecici_zaman.py
import json, re
from pathlib import Path

JOB = Path(__file__).resolve().parents[1]
CUMLELER = [   # METIN.md v3 FINAL (kullanici kaydi ile ayni)
    '20. kattasın ve asansörün halatı bir anda kopuyor.',
    'Asansör boşluğa düşerken midenin ağzına geldiğini hissedersin.',
    'Telefonunu çıkarıp annene veda mesajı yazarsın,',
    've tam yere çarpacakken zıplamak için dizlerini kırarsın.',
    'Ama asansör birkaç metre sonra kendiliğinden durur,',
    'sen de boş yere havaya zıplayıp kafanı tavana çarparsın.',
    'Çünkü her asansörün altında, hız aşılınca raylara kenetlenen bir fren var ve o fren seni her zaman durdururdu.',
]
HEDEF = 35.0          # s, metin-kurallari: 30-38 s
NEFES = 0.12          # cumle arasi
hece = lambda w: max(1, len(re.findall(r'[aeıioöuüAEIİOÖUÜ]', w)))


def main():
    words = [(c, w) for c, s in enumerate(CUMLELER, 1) for w in s.split()]
    tot_h = sum(hece(w) + 0.6 for _, w in words)
    k = (HEDEF - 0.25 - NEFES * (len(CUMLELER) - 1) - 0.6) / tot_h
    t, out, prev = 0.25, [], 1
    for c, w in words:
        if c != prev: t += NEFES; prev = c
        d = (hece(w) + 0.6) * k
        out.append({'w': w, 's': round(t, 3), 'e': round(t + d - 0.03, 3), 'c': c}); t += d
    p = JOB / 'ses' / 'gecici' / 'kelimeler.json'; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    (JOB / 'project' / 'voice.json').write_text(json.dumps({
        'words': 'ses/gecici/kelimeler.json', 'audio': None, 'mix': None,
        'source': 'GECICI hece tahmini (ses yok). Kullanici kaydi gelince scripts/kullanici_ses_hazirla.py calistir.',
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(len(out), 'kelime, son', out[-1]['e'], 's')
    for c in range(1, len(CUMLELER) + 1):
        ws = [x for x in out if x['c'] == c]; print(c, len(ws), f"{ws[0]['s']:.2f}-{ws[-1]['e']:.2f}")


if __name__ == '__main__':
    main()
