# Asset lisansları

Bu klasördeki ikili dosyalar (glb/hdr) git'e girmez; `python assets/fetch_assets.py` ile `catalog.json`
içindeki URL'den indirilir ve sha256 ile doğrulanır. Yalnızca veri dosyaları (glb/gltf/bin/png/jpg/hdr/exr)
kabul edilir; arşiv açılmaz, çalıştırılabilir dosya indirilmez. Kontrol tarihi: 2026-11-09.

| id | Dosya | Kaynak (sayfa) | İndirme URL'si | Yazar | Lisans | Atıf | Boyut |
|---|---|---|---|---|---|---|---|
| horse_brown_quaternius | characters/horse_brown_quaternius.glb | https://poly.pizza/m/qvTrSG9pZF | https://static.poly.pizza/d37dbc87-ca61-4b2c-a2da-d2f0c4240bef.glb | Quaternius | CC0 1.0 | gerekmez | 1 108 124 B |
| horse_white_quaternius | characters/horse_white_quaternius.glb | https://poly.pizza/m/bEdE4rmZy9 | https://static.poly.pizza/3edc2bd9-3378-4b43-a50d-d5e1f858562b.glb | Quaternius | CC0 1.0 | gerekmez | 1 109 444 B |
| horse_atlas_quaternius | characters/horse_atlas_quaternius.glb | https://poly.pizza/m/D3hAeqeDBE | https://static.poly.pizza/52b9bf67-bf41-4aec-a4ff-e93e630289f2.glb | Quaternius | CC0 1.0 | gerekmez | 237 360 B |
| cat_atlas_quaternius | characters/cat_atlas_quaternius.glb | https://poly.pizza/m/qKICY6xla2 | https://static.poly.pizza/67f5e3fe-37ee-4c86-95c8-d269d8c9f8ba.glb | Quaternius | CC0 1.0 | gerekmez | 238 672 B |
| cat_toon_quaternius | characters/cat_toon_quaternius.glb | https://poly.pizza/m/2f54vbV0In | https://static.poly.pizza/7ccb71fe-dabb-4a6f-a98a-8992bb5e6bc7.glb | Quaternius | CC0 1.0 | gerekmez | 111 948 B |
| dog_shiba_quaternius (+ cat_shiba_kitbash) | characters/dog_shiba_quaternius.glb | https://poly.pizza/m/y4wdQpg767 | https://static.poly.pizza/ba6d0ee3-bcc0-4ef0-9d3c-a3e245b41c77.glb | Quaternius | CC0 1.0 | gerekmez | 851 196 B |
| human_quaternius | characters/human_quaternius.glb | https://poly.pizza/m/c3Ibh9I3udk | https://static.poly.pizza/170235d2-cdeb-4cb2-a82f-4828585138fe.glb | Quaternius | CC0 1.0 | gerekmez | 698 560 B |
| adventurer_quaternius | characters/adventurer_quaternius.glb | https://poly.pizza/m/5EGWBMpuXq | https://static.poly.pizza/bbe369ee-a686-42c7-adad-14356f5f2f15.glb | Quaternius | CC0 1.0 | gerekmez | 1 944 116 B |
| truck_quaternius | vehicles/truck_quaternius.glb | https://poly.pizza/m/cXw6oiFtZ8 | https://static.poly.pizza/f4b28921-b45e-4653-b54c-c3976e4ea0fe.glb | Quaternius | CC0 1.0 | gerekmez | 326 828 B |
| schoolbus_polygoogle | vehicles/schoolbus_polygoogle.glb | https://poly.pizza/m/8xacyNqdJ3t | https://static.poly.pizza/b79bb5fb-28e1-43cb-b821-75a7dcecd89c.glb | Poly by Google | **CC BY 3.0** | **gerekir** | 236 852 B |
| sky_kloofendal_puresky_1k | env/kloofendal_48d_partly_cloudy_puresky_1k.hdr | https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky | https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/kloofendal_48d_partly_cloudy_puresky_1k.hdr | Greg Zaal, Jarod Guest / Poly Haven | CC0 1.0 | gerekmez | 1 435 119 B |

Notlar
- Quaternius modelleri Poly Pizza üzerinden dağıtılıyor; model sayfası lisansı "CC0 1.0" olarak gösteriyor
  (Quaternius'un tüm paketleri CC0). Atıf zorunlu değil; açıklamada "3D modeller: Quaternius (CC0)" yazmak iyi uygulama.
- **schoolbus_polygoogle CC BY 3.0**: kullanılırsa video açıklamasına/künyesine şu satır eklenmeli:
  `Schoolbus by Poly by Google [CC-BY 3.0] via Poly Pizza (https://poly.pizza/m/8xacyNqdJ3t)`.
  20261109-agent5-style-test v4/v5'te kullanılmadı (otobüs prosedürel).
- `cat_shiba_kitbash` ayrı bir dosya değil: Shiba Inu (CC0) rig'i + kodla üretilmiş kedi başı (bizim kodumuz).
- Değerlendirilip **alınmayanlar**: three.js örnek modelleri Horse/Flamingo/Parrot/Stork (ro.me projesi, lisans
  repo'da açıkça belirtilmemiş), Soldier.glb ve Xbot.glb (Mixamo kaynaklı; Mixamo lisansı yeniden dağıtıma izin
  vermiyor, hesap gerektiriyor), J-Toastie "Cat" (CC BY 3.0 ama yalnızca Idle animasyonu var), German Shepard (CC BY 3.0).
- Yeni asset eklerken: yalnızca CC0 (tercih) veya CC BY; sayfadaki lisansı ve yazarı bu tabloya ve catalog.json'a
  yaz, sha256'yı `fetch_assets.py` ile doğrula, testleri çalıştır (`tests/test_assets_catalog.py`).
