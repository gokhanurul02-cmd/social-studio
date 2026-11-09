# three-crowd — rig'li karakterlerle deterministik kalabalık (Three.js)

"X'i çekmek için kaç Y gerekir" türü bölümler için: birkaç kahraman karakter tam rig + animasyonla,
yüzlerce/binlerce uzak figür tek draw call'luk vertex-animation-texture (VAT) kalabalığıyla. Her şey
`t` (saniye) parametresinin saf fonksiyonu → kare kare export (Playwright + FFmpeg) tekrarlanabilir.

## Dosyalar
| Dosya | İş |
|---|---|
| `crowd.js` | `loadCatalog`, `loadCharacter`, `Actor`, `bakeVAT`, `VATCrowd`, `attachToBone`, `applyBoneTweaks`, `findClip`, `bakeStaticPose` |
| `render/harness.cjs` | yerel sunucu + headless GPU Chrome; `/three/`, `/assets/` (repo `assets/`), `/crowd/` (bu klasör), `/fonts/` rotaları |
| `probe/` | asset denetimi: `node templates/three-crowd/probe/probe.cjs OUTDIR [id,id]` → yan/ön/3-4 + VAT kalabalık kareleri, `probe.json` (boyut, ayak yüksekliği, klipler, VAT vertex sayısı) |

## Kullanım
```html
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
```
```js
import { loadCatalog, loadCharacter, Actor, bakeVAT, VATCrowd } from '/crowd/crowd.js';
const cat = await loadCatalog('/assets/catalog.json');
const horseT = await loadCharacter(cat.url('horse_brown_quaternius'), cat.byId.horse_brown_quaternius); // ayak y=0, +Z'ye bakar, target boyunda
const hero = new Actor(horseT, { clip: 'Walk' }); scene.add(hero.root);
const herd = new VATCrowd(bakeVAT(horseT, 'Walk', { frames: 32 }), 500,
  { materials: { Main: { tint: 'multiply', color: '#c8c8c8' } } });
scene.add(herd.mesh);

function apply(t) {                       // her alt-örnekte (motion blur) aynı t → aynı kare
  hero.seek(t * 1.0);                     // AnimationMixer.setTime: deterministik
  herd.begin();
  for (const h of layout) herd.add(h.phase + t * h.rate, h.pos, h.yaw, h.scale, h.coat); // phase = döngü sayısı
  herd.end();
}
```
Proje `render/harness.cjs` dosyası şablonu sarar:
```js
const T = require('<repo>/templates/three-crowd/render/harness.cjs');
module.exports = { open: o => T.open({ project: path.resolve(__dirname, '..'), ...o }), TOOL_ROOT: T.TOOL_ROOT };
```

## Teknik notlar
- **Kahraman**: `SkeletonUtils.clone` (iskelet kopyası) + kendi `AnimationMixer`'ı. `actor.play('Walk')` / `actor.mix([['Walk',.7],['Run',.3]])`,
  sonra `actor.seek(t)`. Klip zamanı `offset + t*rate`; çağrı sırasından bağımsız.
- **Uzak plan**: `bakeVAT` klibi N kareye (varsayılan 32) örnekler; konum + normal float dokuya yazılır (`texelFetch`, `gl_VertexID`).
  `VATCrowd` tek `InstancedMesh` (malzeme grubu başına bir alt çizim); her örneğin fazı ayrı (`aPhase`), GPU kareler arası
  doğrusal karıştırır → 8 sabit faz yerine sürekli faz. Gölge için `customDepthMaterial` de VAT ile yamalı.
- **Renk**: `materials: { Ad: { tint: 'replace' | 'multiply' | 'none', color } }`. `replace` taban rengi beyaza çeker, örnek
  rengi kürk/post rengi olur; göz/burun gibi malzemeler `none` kalır.
- **LOD**: kahraman ≤ ~6 `Actor`; geri kalanı VAT. Çok uzak (< ~6 px) figürler için `bakeStaticPose` (1 karelik VAT).
  Ölçüm (bu makine): 2400 kedi × ~2k üçgen + 12 at, 8 alt-örnek, 1080×1920 → 299 kare 32–36 s (~0.11 s/kare).
- **Tür uyarlama**: `catalog.json` girdisindeki `bone_tweaks` (ölçek/dönüş) animasyondan sonra uygulanır; `attachToBone`
  ile kemiğe eklenen nesneler (koşum, ip bağlantı noktası, yedek kafa) hem kahramanda hem VAT'ta hareket eder.
  Örnek: `cat_shiba_kitbash` = Shiba rig'i + kodla kedi başı (`jobs/20261109-agent5-style-test/project-v4/src/characters.js`).
- **Ölçek/yön**: `loadCharacter` kataloğun `forward` ve `target` alanlarını uygular; ölçümler skinned vertex'lerden
  (`Box3.setFromObject(root, true)`), dolayısıyla ölçüler rig pozuna göre doğrudur.

## Yeni asset
1. Yalnızca CC0 (tercih) ya da CC BY; Mixamo/hesap gerektiren kaynak yok. Doğrudan `.glb/.hdr` URL'si (arşiv açma yok).
2. `assets/catalog.json`'a girdi (url, sha256, lisans, yazar, atıf, forward, target) → `python assets/fetch_assets.py`.
3. `node templates/three-crowd/probe/probe.cjs <out> <id>` → kareleri gözle kontrol et, `probe.json`'dan `size_m`,
   `foot_height_m`, `tris`, `animations` alanlarını kataloğa yaz; `assets/LICENSES.md` tablosuna satır ekle.
4. `python -m unittest tests.test_assets_catalog`.
