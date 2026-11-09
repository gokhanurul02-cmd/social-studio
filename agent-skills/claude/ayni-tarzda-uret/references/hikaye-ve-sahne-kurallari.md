# Hikâye, sahne ve kontrol kuralları (kanıtlanmış animasyon sistemi)

Kaynak: kullanıcının "Claude Animasyon Sistemi" rehberi (`jobs/referans-kutuphanesi/Claude Animasyon Sistemi.md`) ve aynı yöntemle yapılmış 4 tutmuş video (`jobs/referans-kutuphanesi/01..04/`, her birinde ölçülmüş `analysis/` + `ANALIZ.md`). Yeni bölüm üretmeden önce bu dosyayı ve kalıba en yakın referansın ANALIZ.md'sini oku.

## 1. Hikâye önce gelir
Videoyu izleten animasyon değil anlatımdır. Güzel çizilmiş yarım hikâye izlenmez.

- **İlk cümle:** herkesin anlayacağı somut bir çelişki ya da merak; açıklama değil. Önce 5 farklı ilk cümle yaz, en güçlüsünü seç (otomatik modda gerekçesini yaz, aksi hâlde kullanıcıya seçtir).
- **Gövde:** tek konu, baştan sona; izleyiciden ön bilgi bekleme; bağlam isteyen karşılıklı konuşmadan kaçın. Ortada bir dönüş: "Nasıl mı?", "Değil.", "Yok."
- **Son:** son cümle ilk cümleyi kapatır; sonra en çok bir cümle çağrı.
- **Ölçü (Türkçe):** 40–55 sn için 70–100 kelime, ≈2 kelime/sn. 120 kelimeyi geçerse kısalt; sesi hızlandırarak sığdırma. Konuşma süresi videonun %60–75'i; kalan nefes/duraklama, görüntü orada konuşur. Ölçü rehberdir, hedef değil.
- **Gerçek olay:** ekranda/seste geçen her isim, tarih, rakam için kaynak; emin olmadığını yazma, kurgu sahneyi kurgu diye belirt. Uydurma rakam, sahte yorum yok.

### Dört kalıp
| Kalıp | Sıra | Referans |
|---|---|---|
| Masal | iki karakter, iddia, ters köşe, tek cümle ders, izleyiciye soru | 01 Keskin balta |
| Bu neden var? | nesne + soru, yaygın yanlış inanış, "Değil.", katman katman açıklama, ilk kareye dönüş | 02 Uçak camındaki delik |
| Gerçek olay | tuhaf sonuç, kim/nerede/ne zaman, "Nasıl mı?", açıklama, tek cümle ders | 03 99 telefonla sahte trafik |
| Sen karar ver | "sen" dili, yükselen gerilim (sayaçlar), iki seçenek, yorum çağrısı | 04 Gece 3'te gelen telefon |

Aynı kalıbı her konuya giydirme: izleyen aynı videoyu görür. Kalıbı değil **işçiliği** al: nasıl başlıyor, nerede duruyor, kamera nasıl süzülüyor.

## 2. Sahne planı (kod yazmadan önce)
Her cümle için tek soru: **bu cümle söylenirken ekranda ne var?** Tabloyu yaz, onaylanmadan (veya otomatik modda kendi kontrolünden geçmeden) kod yazma.

1. Her an ekranda tek fikir; söylenmeyen hiçbir şey ekranda olmasın.
2. Görüntü konudan çıksın: "Bu kare başka bir videoda da olabilir miydi?" Evet ise baştan düşün.
3. Sahneler nesneyle bağlansın (kamera nesnenin içine girer, nesne başka şeye dönüşür). Hazır sayfa çevirme geçişleri bu formatta kullanılmaz. (Not: Cybertruck tarzında 3D kart çevirme stilin parçasıdır; hangi formatın geçerli olduğunu referansın `transitions.json`'u söyler.)
4. Karakterler oynasın: yürür, eğilir, eşyayı tutar, yüzü cümleyle değişir; kart gibi kaymaz. Durağan görsel + oynayan ağız animasyon değildir.
5. Az yazı: dev yazı yalnız ilk cümlede ve derste; etiket işini bitirince gider.
6. Durmak serbest: önemli anda 1–2 sn neredeyse hiçbir şey oynamasın; tam donuk an 3 sn'yi geçmesin.
7. Daha çok hareket videoyu iyileştirmez, kalabalıklaştırır; en çok beğenilenler sakin olanlar.

## 3. Zamanlama kuralları
- **Elle saniye yazma.** Her sahne anı kelime zamanından gelsin (`an(satir, kelime)`); metin değişince sahneler kendiliğinden kayar. Kelime zamanları TTS hizalamasından (ElevenLabs with-timestamps, Edge TTS WordBoundary) veya `transcript.json` kelimelerinden.
- **Kamera yavaş süzülsün:** hareket ≥0.7 sn, yumuşak giriş-çıkış (ör. bezier 0.45,0,0.55,1). Sert kesme yerine sonraki ana süzül (Cybertruck gibi hızlı geçişli stillerde referansın ölçümü önceliklidir).
- **Eylem kelimeyle gelsin:** hareket kelimeden 0–3 kare önce başlar.
- Altyazı kelime kelime açılabilir; söylenen kelime vurgu rengi (örn. #ffd84a); görünmeyen kelime yer tutar, satır zıplamaz. Altyazı ≥50 px, güvenli alanda (1080×1920'de y≈230–1560).

## 4. Ses
- 3–4 sesi aynı metinle dene; hikâye anlatan, acele etmeyen ses bu formata oturur.
- Sayı/kısaltmayı yazıyla okut; ekranda rakam, seste yazı (`12.500|on_iki_bin_beş_yüz` kalıbı).
- Tek üretim ≤800–900 karakter. Kötü çıkan sesi yeniden üret. Ücretli TTS (ElevenLabs) kullanıcı onayı ve kendi anahtarıyla; anahtar ortam değişkeninde, koda/sohbete yazılmaz. Onay yoksa ücretsiz/yerel TTS.
- Üretilen sesi yazıya çevirip metinle karşılaştır; ama tonu duyamazsın: "sesli kontrol ettim" deme, kullanıcıya dinletmeyi iste.

## 5. Kontrol listesi (her render sonrası)
48 karelik pano: `ffmpeg -i video.mp4 -vf "fps=48/SURE,scale=240:-2,tile=8x6" -frames:v 1 pano.jpg`, sonra `social analyze` + `social stylecheck`.
- [ ] İlk kare dolu, ilk 2 sn'de ilk cümle okunuyor.
- [ ] Son kare dolu, video ortada kesilmiyor.
- [ ] Ses kapalı pano okununca hikâye anlaşılıyor.
- [ ] Yazı kırpılmıyor, altyazı bir şeyin üstüne binmiyor (composition.json edge_cut / flat_fill uyarıları).
- [ ] Hiçbir kare "başka videodan alınmış" gibi değil.
- [ ] Söylenmeyen gereksiz şey yok.
- [ ] Gerçek bilgilerin kaynağı var.
- [ ] Ses/görüntü uyumu karede görünmez: kullanıcıya sesli izlet.

## 6. Yaşanmış hatalar (tekrarlama)
Durağan görsel + oynayan ağız · yarım hikâye · tek örnek görmeden toplu üretim · çok kelime/hızlı konuşma · daha çok hareket · ölçü tutsun diye iyi kareyi bozmak · aynı kalıbı her konuya giydirmek · rapora güvenip kareleri açmamak · kaynaksız rakam · başkasının yüzü, sesi, logosu, videosu.

**Beğenmeden çoğaltma.** Önce tek videoyu bitir, kullanıcı izlesin; sonra seri üretim.
