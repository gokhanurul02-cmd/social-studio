# Claude ile Animasyon Video Sistemi

Kısa dikey animasyon videoları (30-60 saniye) nasıl yapılır? Bu dosya yöntemi baştan sona anlatıyor. Yanındaki `ornekler` klasöründe bu yöntemle yapılmış 4 video var.

**Fikrin özeti:** Yapay zeka yalnız seste kullanılıyor. Görüntülerin tamamı kod: Claude, sahneleri SVG ile çizip React ile oynatıyor. Görsel üretim modeli de video modeli de yok.

Bunun üç faydası var:

- **Tutarlılık:** Karakter her sahnede aynı karakter.
- **Ucuz düzeltme:** "Elini biraz sağa al" tek satır. Yeniden üretim, kredi, bekleme yok.
- **Düşük maliyet:** Video başına tek ek masraf ses, 500-900 karakter.

---

## Örnek videolar

Boyut küçük kalsın diye 720p'ye sıkıştırıldı. Asılları 1080x1920.

| Dosya | Kalıp | Neye bak |
|---|---|---|
| `01 - Keskin balta` | Masal | Tek dünya, kamera süzülüyor, dev yazı yalnız başta ve sonda |
| `02 - Ucak camindaki delik` | "Bu neden var?" | Tek nesne, katman katman açılıyor, sonda ilk kareye dönüyor |
| `03 - 99 telefonla sahte trafik` | Gerçek olay | Önce tuhaf sonuç, sonra açıklama, son cümle her şeyi kapatıyor |
| `04 - Gece 3te gelen telefon` | Sen karar ver | "Sen" dili, gerilim sayaçları, sonda izleyiciye seçim |

Sesler ElevenLabs kütüphanesinden. Hepsi aynı sistem, ama her biri kendi konusundan çıkan ayrı bir görsel dünya.

---

## Neye ihtiyacın var

- **Claude Code:** Kodu yazan ve kontrol eden taraf.
- **Remotion:** React ile video üreten kütüphane. Şirketler için ayrı lisans koşulları var, ticari kullanmadan önce kendi durumuna bak.
- **Node.js, Python 3, ffmpeg:** Çalıştırmak ve videoyu kontrol etmek için.
- **ElevenLabs hesabı ve API anahtarı:** Ses için.

API anahtarını koda ya da sohbete yazma. Ortam değişkeninde tut, kimseyle paylaşma.

---

## Akış

1. **Hikâye:** Metni yaz. En önemli adım bu.
2. **Ses:** Metinden sesi ve kelime zamanlarını üret.
3. **Sahne planı:** Her cümle için "ekranda ne var?" sorusunu cevapla.
4. **Kod:** Önce tek sahne, onay, sonra tamamı.
5. **Kontrol:** Kareleri aç, sesli izle, düzelt.

**Beğenmeden çoğaltma.** Önce tek videoyu bitir, izle. Toplu üretip sonra beğenmemek en pahalı hatadır.

---

## 1. Hikâye

Videoyu izleten şey animasyon değil, anlatımdır. Güzel çizilmiş yarım hikâye izlenmez.

**İlk cümle:** Herkesin anlayacağı somut bir çelişki ya da merak olsun, açıklama olmasın.

- "Hiç durmamış, yine de kaybetmiş."
- "Uçak camının altındaki bu delik neden var?"
- "Bu adam el arabasıyla trafik yarattı."
- "Gece 3. Telefonun çalıyor. Arayan, ortağın."

**Gövde:** Tek konu, baştan sona. Ortasından başlama, izleyiciden ön bilgi bekleme. Bağlam isteyen karşılıklı konuşmalardan kaçın, izleyici kaybolur. Ortada bir dönüş olsun: "Nasıl mı?", "Değil.", "Yok."

**Son:** Son cümle ilk cümleyi kapatsın. "Hiç durmamış, yine de kaybetmiş" diye başlayan video, "Baltayı bilemek, vakit kaybı değildir" diye biter. Sonrasında en çok bir cümle çağrı.

**Ölçü:**

- Türkçe 40-55 saniyelik video için 70-100 kelime. Saniyede yaklaşık 2 kelime.
- 120 kelimeyi geçtiysen kısalt. Sesi hızlandırarak sığdırma.
- Konuşma süresi videonun yaklaşık yüzde 60-75'i olsun. Geri kalan nefes ve duraklama, görüntü orada konuşur.

**Dört hazır kalıp:**

| Kalıp | Sıra |
|---|---|
| Masal | İki karakter, iddia, ters köşe, tek cümle ders, izleyiciye soru |
| Bu neden var? | Nesne ve soru, yaygın yanlış inanış, "Değil.", katman katman açıklama, ilk kareye dönüş |
| Gerçek olay | Tuhaf sonuç, kim nerede ne zaman, "Nasıl mı?", açıklama, tek cümle ders |
| Sen karar ver | "Sen" dili, gerilim yükselir, iki seçenek, yorum çağrısı |

**Gerçek olay anlatıyorsan:** Ekranda ve seste geçen her isim, tarih ve rakamın kaynağını aç. Emin olmadığını yazma. Kurgu sahneleri ekranda kurgu diye belirt. Uydurma rakam, sahte müşteri yorumu kullanma.

---

## 2. Ses

**Ses seçimi:** Kütüphaneden 3-4 sesi aynı metinle dene, kulağınla seç. Hikâye anlatan, acele etmeyen sesler bu formata iyi oturuyor. Kendi klonladığın sesi de aynı şekilde kullanabilirsin.

**Kelime zamanları:** ElevenLabs'in zaman damgalı uç noktası sesle birlikte her harfin zamanını veriyor. Ayrıca yazıya çevirme aracı gerekmiyor. Sahneler bu zamanlara bağlanacak.

**Tonlama:** Bu rehber yazılırken (Kasım 2026) belgelerin önerdiği model `eleven_v4`. Model adları değişiyor, güncel belgeye bak. Aynı metni eski ve yeni modelde üretip dinle, karar kulağının. Örnek videolar bir önceki modelle üretildi.

Yeni modelde tonu şunlarla verirsin:

- **Köşeli parantez:** Okunmaz, tonu yönlendirir. İngilizce yaz: `[calm, warm storyteller, unhurried]`, `[slowly]`, `[pause]`, `[softly]`. Etkisi sonraki cümlelere de geçer, bu yüzden yalnız ton değişeceği yerde kullan.
- **Noktalama:** Üç nokta ağırlık ve duraklama katar. Normal noktalama ritmi verir.
- **Stability:** Düşürünce ifade artar, yükseltince tekdüzeleşir. 0,3 ile başla.
- **Yazı stili:** Doğal konuşma cümleleri yaz. Model bağlamdan da ton çıkarır.

**Dikkat:**

- Sayıları ve kısaltmaları yazıyla yaz. Ekranda "12.500" görünsün ama ses "on iki bin beş yüz" okusun istiyorsan aşağıdaki betikte `12.500|on_iki_bin_beş_yüz` yaz.
- Tek üretimi 800-900 karakterin altında tut.
- Üretilen sesi yazıya çevirip metinle karşılaştır, ama kulakla da dinle. Yazıya çevirme tonu duymaz.
- Her üretim biraz farklı çıkar. Kötü çıkan sesi yeniden üret.

**Betik:** `ses.py`

```python
#!/usr/bin/env python3
"""Metinden ses ve kelime zamanları üretir. Anahtar ortam değişkeninden okunur, koda yazılmaz.
Kullanım: python3 ses.py public/ilk-video <ses_id>
Girdi metin.txt: her satır bir cümle grubu. [yönlendirme] okunmaz, gosterim|okunus ekranda ilkini gösterir, ikincisini okutur."""
import base64, json, os, re, ssl, sys, urllib.request

try:
    import certifi
    baglam = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    baglam = ssl.create_default_context()

klasor, ses = sys.argv[1], sys.argv[2]
satirlar = [x.strip() for x in open(f"{klasor}/metin.txt", encoding="utf-8") if x.strip()]
metin, kelimeler = "", []
for c, satir in enumerate(satirlar):
    for parca in re.findall(r"\[[^\]]*\]|\S+", satir):
        if metin:
            metin += " "
        if parca.startswith("["):
            metin += parca
            continue
        gor, oku = parca.split("|", 1) if "|" in parca else (parca, parca)
        oku = oku.replace("_", " ")
        kelimeler.append({"w": gor, "a": len(metin), "b": len(metin) + len(oku), "c": c})
        metin += oku

istek = urllib.request.Request(
    f"https://api.elevenlabs.io/v1/text-to-speech/{ses}/with-timestamps?output_format=mp3_44100_128",
    data=json.dumps({"text": metin, "model_id": "eleven_v4", "language_code": "tr", "voice_settings": {"stability": 0.3, "similarity_boost": 0.75}}).encode(),
    headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
)
with urllib.request.urlopen(istek, timeout=240, context=baglam) as yanit:
    sonuc = json.load(yanit)

open(f"{klasor}/ses.mp3", "wb").write(base64.b64decode(sonuc["audio_base64"]))
h = sonuc["alignment"]
cikti = [{"w": k["w"], "s": h["character_start_times_seconds"][k["a"]], "e": h["character_end_times_seconds"][k["b"] - 1], "c": k["c"]} for k in kelimeler]
json.dump(cikti, open(f"{klasor}/kelimeler.json", "w", encoding="utf-8"), ensure_ascii=False)
print("süre", round(cikti[-1]["e"], 1), "sn,", len(cikti), "kelime,", len(metin), "karakter")
```

Örnek `metin.txt`:

```text
[calm, warm storyteller, unhurried] Adam altı ay kuyu kazmış. Su çıkmamış.
[pause] Çünkü suyu aşağıda değil, yanında aramalıydı.
```

---

## 3. Sahne planı

Kod yazmadan önce her satıra tek soruyu sor: **Bu cümle söylenirken ekranda ne var?**

| Satır | Ekranda |
|---|---|
| "İki oduncu iddiaya girmiş." | İki adam yan yana, ellerinde balta |
| "Akşama kadar kim çok keserse, o kazanacak." | Gökyüzünde güneşin sabahtan akşama yolu çizilir |
| "Hiç durmayan: 36." | Gökyüzünde iki sayaç, birincisi 36'da durur, önündeki yığın küçük |
| "Oturan: 78." | İkinci sayaç 78'e çıkar, yığın kocamandır, hiç durmayanın yüzü değişir |

**Kurallar:**

1. **Her an ekranda tek fikir.** Söylenmeyen hiçbir şey ekranda olmasın.
2. **Görüntü konudan çıksın.** Her kareye sor: "Bu kare başka bir videoda da olabilir miydi?" Olabilirse baştan düşün.
3. **Sahneler nesneyle bağlansın.** Kamera nesnenin içine girer, nesne başka şeye dönüşür, sayfa çevirme gibi hazır geçişler olmaz.
4. **Karakterler oynasın.** Yürür, eğilir, eşyayı eliyle tutar, yüzü cümleyle değişir. Kart gibi ekranda kaymaz.
5. **Az yazı.** Dev yazı yalnız ilk cümlede ve derste. Etiket işini bitirince gider.
6. **Durmak serbest.** Önemli anda bir iki saniye neredeyse hiçbir şey oynamasın. Tam donuk an 3 saniyeyi geçmesin yeter.

**Beğendiğin videoyu kopyalama.** Masal videosunda oduncuyu çıkarıp yerine başka hayvan koymak işe yaramaz. O videoyu iyi yapan balta değil, anlatımı ve animasyon işçiliğidir. Kalıp yerine işçiliği al: nasıl başlıyor, nerede duruyor, kamera nasıl süzülüyor?

---

## 4. Kod

**Klasör yapısı:**

```text
proje/
  ses.py
  public/ilk-video/   metin.txt, ses.mp3, kelimeler.json
  src/ilk-video/      index.ts, Video.tsx
```

**Üç kural:**

- **Elle saniye yazma.** Her sahne anı kelimeden gelsin: `an(1, 3)` ikinci satırın dördüncü kelimesi. Metin değişince sahneler kendiliğinden kayar.
- **Kamera yavaş süzülsün.** Kamera hareketi en az 0,7 saniye, yumuşak giriş ve çıkış. Sert kesme yerine sonraki ana süzül.
- **Eylem kelimeyle gelsin.** Hareket kelimeden 0-3 kare önce başlasın.

Aşağıdaki iskelet çalışır durumda ama yalnız zaman mantığını gösteriyor: bir kuyu, bir adam, kelimeye bağlı altyazı. Görsel kaliteyi Claude'a sahne planıyla çizdirdiğin katmanlar, dokular ve karakterler getirir.

`src/ilk-video/index.ts`

```ts
import {registerRoot} from 'remotion';
import {Root} from './Video';

registerRoot(Root);
```

`src/ilk-video/Video.tsx`

```tsx
// src/ilk-video/Video.tsx: tek sahnelik iskelet. Çizimi kendi konuna göre değiştir, zaman mantığı aynı kalır.
import React from 'react';
import {AbsoluteFill, Audio, Composition, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';
import veri from '../../public/ilk-video/kelimeler.json';

type Kelime = {w: string; s: number; e: number; c: number};
const K = veri as Kelime[];
const FPS = 30;

// Sahne anı kelimeden gelir, elle saniye yazılmaz: an(1, 3) ikinci satırın dördüncü kelimesi.
const an = (satir: number, kelime = 0) => K.filter((k) => k.c === satir)[kelime].s;
// t0'dan başlayıp 0'dan 1'e yumuşakça gider. Kamera ve bütün hareketler bununla yapılır.
const gir = (t: number, t0: number, sure = 0.8) =>
  interpolate(t, [t0, t0 + sure], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.45, 0, 0.55, 1)});
const karis = (a: number, b: number, u: number) => a + (b - a) * u;

// Altyazı: satır kelime kelime açılır, söylenen kelime sarıdır. Görünmeyen kelime yer tutar, satır zıplamaz.
const Altyazi: React.FC<{t: number}> = ({t}) => {
  const aktif = K.filter((k) => k.s - 0.04 <= t).pop();
  if (!aktif) return null;
  return (
    <div style={{position: 'absolute', left: 70, right: 70, top: 1380, textAlign: 'center', fontFamily: 'Georgia, serif', fontWeight: 700, fontSize: 58, lineHeight: 1.25}}>
      {K.filter((k) => k.c === aktif.c).map((k, i) => (
        <span key={i} style={{opacity: t >= k.s - 0.04 ? 1 : 0, color: k === aktif ? '#ffd84a' : '#fff', textShadow: '0 3px 10px rgba(0,0,0,.85)'}}>
          {k.w}{' '}
        </span>
      ))}
    </div>
  );
};

const Video: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const kaz = gir(t, an(0, 0), an(0, 5) - an(0, 0)); // kuyu cümle boyunca derinleşir
  const don = gir(t, an(1, 0), 1.2); // ikinci satırda kamera yana süzülür
  const su = gir(t, an(1, 4), 0.6); // "yanında" kelimesinde su belirir
  const nefes = Math.sin(t * 1.2) * 4; // adam hiç tam durmaz
  return (
    <AbsoluteFill style={{background: '#d9c8a0'}}>
      <Audio src={staticFile('ilk-video/ses.mp3')} />
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <g transform={`translate(${karis(0, -520, don)},${karis(0, -180, kaz) * (1 - don)})`}>
          <rect x={-600} y={760} width={2800} height={1500} fill="#8a6a43" />
          <rect x={440} y={760} width={200} height={karis(40, 560, kaz)} fill="#2d2118" />
          <rect x={1040} y={1010} width={500} height={120} rx={60} fill="#4aa3d8" opacity={su} />
          <g transform={`translate(540,${karis(680, 1240, kaz) + nefes})`} fill="none" stroke="#f3e6c8" strokeWidth={12} strokeLinecap="round">
            <circle cy={-40} r={36} fill="#f3e6c8" />
            <path d="M 0 0 L 0 70 M 0 20 L -40 50 M 0 20 L 40 50" />
          </g>
        </g>
      </svg>
      <Altyazi t={t} />
    </AbsoluteFill>
  );
};

const sure = Math.ceil((K[K.length - 1].e + 1.2) * FPS);
export const Root: React.FC = () => <Composition id="Video" component={Video} durationInFrames={sure} fps={FPS} width={1080} height={1920} />;
```

**Çalıştır:**

```bash
export ELEVENLABS_API_KEY=...          # kendi anahtarın
python3 ses.py public/ilk-video SES_ID
npx remotion render src/ilk-video/index.ts Video cikti/ilk-video.mp4 --concurrency=2
```

**Görüntü kalitesi için:**

- Kağıt dokusu, gren, vinyet gibi ince katmanlar düz çizimi canlandırır. Ama görüntüyü soldurmasın.
- Çizgi kalınlığı, renk paleti ve karakter ölçüsü bütün videoda aynı kalsın.
- Altyazı en az 50 piksel, üstten ve alttan güvenli alanda (yaklaşık y 230 ile 1560 arası). Hiçbir şey yazının altından geçip okunmasını zorlaştırmasın.

**Bilgisayarı yorma:** Remotion kareleri tarayıcıda çizer, belleği hızlı doldurur. Aynı anda tek render al, `--concurrency=2` yeterli. Aynı anda en çok 3 video üzerinde çalış.

---

## 5. Kontrol

**Kare panosu çıkar.** 48 kareyi tek resimde görürsün, sorunların çoğu burada yakalanır. `SURE` yerine videonun saniyesini yaz:

```bash
ffmpeg -i video.mp4 -vf "fps=48/SURE,scale=240:-2,tile=8x6" -frames:v 1 pano.jpg
```

**Şunlara bak:**

- [ ] İlk kare dolu mu, ilk 2 saniyede ilk cümle okunuyor mu?
- [ ] Son kare dolu mu, video ortada kesilmiyor mu?
- [ ] Hikâye baştan sona anlaşılıyor mu? Sesi kapatıp panoyu oku.
- [ ] Yazılar kırpılıyor mu, altyazı bir şeyin üstüne biniyor mu?
- [ ] Bir kare başka videodan alınmış gibi duruyor mu?
- [ ] Ekranda söylenmeyen, gereksiz bir şey var mı?
- [ ] Gerçek bilgilerin kaynağı var mı?

**Sonra sesli izle.** Ses ve görüntü uyumu karede görünmez. Bunu senin yerine kimse yapamaz, Claude da videoyu duyamaz.

---

## Hazır istemler

Sırayla Claude Code'a ver. Her adımda sonucu görmeden sonrakine geçme.

**Kurulum**

```text
Bu klasörde boş bir Remotion projesi kur. 1080x1920, 30 fps dikey video yapacağız.
Görsel ya da video modeli kullanmayacağız, her şeyi React ve SVG ile çizeceğiz.
Rehberdeki ses.py, index.ts ve Video.tsx dosyalarını yerine koy.
Yeni paket kurman gerekirse önce bana sor.
```

**Hikâye**

```text
Konu: [KONU]. İzleyen: [KİM].
Dikey animasyon video için metin yaz.
- 70-100 kelime, kısa konuşma cümleleri, her satırda tek fikir.
- İlk cümle herkesin anlayacağı somut bir çelişki ya da merak.
- Tek konu, baştan sona. İzleyiciden ön bilgi bekleme.
- Ortada bir dönüş olsun. Son cümle ilk cümleyi kapatsın, sonra en çok bir cümle çağrı.
- Gerçek olaysa her isim ve rakam için kaynak göster. Uydurma rakam, sahte tanıklık yok.
Önce 5 farklı ilk cümle yaz. Ben seçeyim, sonra metnin tamamını yaz.
```

**Sahne planı**

```text
Bu metnin her satırı için sahne planı yaz: o cümle söylenirken ekranda ne var?
- Her an tek fikir. Söylenmeyen hiçbir şey ekranda olmasın.
- Görüntü fikri bu konunun kendi nesnelerinden çıksın. Her kareye sor: başka bir videoda da olabilir miydi?
- Tek dünya. Sahneler birbirine bir nesne üzerinden bağlansın.
- Karakterler oynasın: yürür, eğilir, eşyayı tutar, yüzü cümleyle değişir.
- Dev yazı yalnız ilk cümlede ve derste.
Planı göster, onaylamadan kod yazma.
```

**Tek sahne**

```text
Plandaki ilk iki satırı kodla. Sahne anlarını kelime zamanlarından al, elle saniye yazma.
3 kare çıkar ve göster. Çizim dilini onaylamadan devam etme.
```

**Tamamı ve kontrol**

```text
Bütün videoyu kur ve render al. 48 karelik pano çıkar, kendin aç ve rehberdeki kontrol listesiyle bak.
Fazla olan her şeyi çıkar, en az iki tur düzelt.
Raporda yaz: metinde olmayan ekran yazıları, bildiğin kusurlar, kararsız kaldığın yerler.
Videoyu duyamadığını unutma, duymadığın şeyi kontrol ettim deme.
```

---

## Yaptığımız hatalar

Bunların hepsini yaşadık, aynısını yapma.

- **Durağan görsel ve oynayan ağız.** Üretilmiş görsele ağız yaması koymak animasyon değil. İzleyen hemen anlıyor.
- **Yarım hikâye.** Güzel bir 9 saniyelik deneme, hikâyesi yoksa hiçbir şey anlatmaz.
- **Tek örnek görmeden toplu üretim.** İki kez topluca üretip hepsini baştan yaptık.
- **Çok kelime.** Daha çok bilgi sığdırmak için konuşma hızlanıyor, görüntü nefes alamıyor.
- **Daha çok hareket.** Hareketi artırmak videoyu iyileştirmedi, kalabalıklaştırdı. En çok beğendiğimiz videolar sakin olanlardı.
- **Sayıya göre görüntü bozmak.** Ölçü tutsun diye çarpıcı bir yakın planı küçültmek, görüntüye soluk katman atmak. Ölçü rehberdir, hedef değil.
- **Aynı kalıbı her konuya giydirmek.** İzleyen aynı videoyu görür.
- **Rapora güvenmek.** Claude "bitti" dediğinde kareleri kendin aç. Elin yüzüne binmesi, yazının kırpılması raporda çıkmaz.
- **Kaynağa bakmadan rakam.** Ekranda yazan her şey senin sözün sayılır. Doğrulayamadığın rakamı "söylüyor" diye atfet ya da çıkar.
- **Başkasının yüzü, sesi, logosu, videosu.** Gerçek kişiye benzeyen karakter, izinsiz ses klonu, marka logosu ve başkasının görüntüsünü kullanma. Örnek videoları ilham için izle, kopyalayıp yayınlama.

---

## Süre ve maliyet

- **Ses:** Video başına 500-900 karakter. Fiyatlar değişiyor, kendi planına bak.
- **Görüntü:** Görsel üretim ücreti yok, yalnız Claude kullanımın.
- **Süre:** Bir videonun kodu ve düzeltme turları Claude için yaklaşık 30-90 dakika. Render 1-2 dakika.
