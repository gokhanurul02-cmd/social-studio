# social analyze — Zack D. Films formatında bilinen hatalar (7 videoda doğrulandı, 2026-11-09)

| Ölçüm | Hata | Nasıl düzelt |
|---|---|---|
| `transitions.json` | Gerçek sahne sınırının ~2 katı geçiş raporlar: kesintisiz pan (Blood Vessels 24.5–25 s), renk değişen doku (Stitches 4 "dissolve"), elektrik arkı/parlama (Saws 3 "dissolve") yanlış alarm | Tile'dan gerçek kurgu sınırlarını say; tabloda "araç X, gerçek Y" yaz |
| `transitions.json` | Whip/zoom burst içine saklanmış gerçek kesmeleri `content_change=false` ile kamera içi sayar (Armor 19.6/21.9/25.7 s, Bells 19.7/29.0/31.7 s) | Geçişten önceki ve sonraki kareyi karşılaştır; mekân değiştiyse kesme |
| `transitions.json` | İris (daire maske) geçişini "flip" sanar | Kareye bak |
| `composition.json` | Makro/kesit görüntülerde tekrar eden dokuyu "crowd" sanar (Stitches %77, Saws %58) | Çekim tipini gözle yaz |
| `onscreen_text.json` | Kalın beyaz altyazıyı %90+ doğru okur; birkaç grupta harf bozulması ("And wa batrng") | transcript.json ile düzelt |
| `audio_analysis.json` | Konuşma baskın miksde müzik/efekt tespiti güvenilmez; "yok" çıkması yok demek değil | Kulakla doğrulanmadı diye işaretle |
| Kamera segmentleri | Hızlı 3D kamerada çok parçalı, düşük güvenli segmentler | Ana hareketleri gözle özetle (dalış, geri çekiliş, takip) |
