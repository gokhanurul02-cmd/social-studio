// Asset probe: loads catalog entries with crowd.js, measures them and renders check views
// (side / front / 3-4 hero via Actor.seek, and a VAT crowd) so scale, facing and baking can be verified by eye.
import * as THREE from 'three';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { loadCatalog, loadCharacter, Actor, bakeVAT, VATCrowd, findClip, measure } from '/crowd/crowd.js';

const qs = new URLSearchParams(location.search);
const W = +(qs.get('w') || 640), H = +(qs.get('h') || 640);
async function boot() {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.shadowMap.enabled = true; renderer.toneMapping = THREE.ACESFilmicToneMapping;
  document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x7fc8ee);
  const cat = await loadCatalog('/assets/catalog.json');
  const hdr = cat.assets.find(a => a.kind === 'hdri');
  if (hdr) { const t = await new RGBELoader().loadAsync(cat.url(hdr.id).replace('/assets/', '/assets/')); t.mapping = THREE.EquirectangularReflectionMapping; scene.environment = t; }
  const sun = new THREE.DirectionalLight(0xffffff, 2.5); sun.position.set(4, 8, 5); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6 }); scene.add(sun);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x2ab0e8, roughness: 0.85 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  scene.add(new THREE.GridHelper(40, 40, 0xffffff, 0xffffff));
  const camera = new THREE.PerspectiveCamera(30, W / H, 0.01, 500);

  const ids = (qs.get('ids') || cat.assets.filter(a => a.kind !== 'hdri').map(a => a.id).join(',')).split(',');
  const views = [], info = [];
  for (const id of ids) {
    const e = { ...cat.byId[id], ...JSON.parse(qs.get('override') || '{}') };
    const tpl = await loadCharacter(cat.url(id), e);
    const walk = e.clips?.walk || (findClip(tpl.clips, 'Walk') ? 'Walk' : null);
    const rec = { id, scale: +tpl.scale.toPrecision(4), size: tpl.size.toArray().map(v => +v.toFixed(3)), tris: tpl.tris,
      clips: tpl.clips.map(c => [c.name, +c.duration.toFixed(3)]) };
    let actor = null, vat = null, crowd = null;
    if (walk) {
      actor = new Actor(tpl, { clip: walk });
      // foot height + bounds over the walk cycle
      let minY = 1e9, maxY = -1e9; const d = findClip(tpl.clips, walk).duration;
      for (let k = 0; k < 12; k++) { actor.seek(d * k / 12); const b = measure(actor.root); minY = Math.min(minY, b.min.y); maxY = Math.max(maxY, b.max.y); }
      rec.walk = { clip: findClip(tpl.clips, walk).name, duration: +d.toFixed(3), minY: +minY.toFixed(3), maxY: +maxY.toFixed(3) };
      const t0 = performance.now(); vat = bakeVAT(tpl, walk, { frames: 32 }); rec.vat = { verts: vat.vertexCount, ms: Math.round(performance.now() - t0), rows: vat.rows };
      crowd = new VATCrowd(vat, 64, { materials: e.materials || {} });
    } else { actor = { root: tpl.root.clone(), seek() {} }; }
    info.push(rec);
    const s = Math.max(...tpl.size.toArray());
    const c = new THREE.Vector3(0, tpl.size.y * 0.5, 0);
    const views_ = [['side', new THREE.Vector3(s * 2.6, tpl.size.y * 0.6, 0), 0.0], ['front', new THREE.Vector3(0, tpl.size.y * 0.6, s * 2.6), 0.25],
      ['34', new THREE.Vector3(s * 1.8, tpl.size.y * 1.2, s * 1.8), 0.5]];
    if (qs.get('head')) views_.push(['head', new THREE.Vector3(s * 0.5, tpl.size.y * 1.0, s * 1.3), 0.1, new THREE.Vector3(0, tpl.size.y * 0.75, s * 0.3)]);
    for (const [name, pos, ph, look] of views_) views.push({ id, name, pos, c: look || c, ph, actor, d: rec.walk?.duration || 1 });
    if (crowd) views.push({ id, name: 'vat', pos: new THREE.Vector3(s * 4, s * 2.2, s * 5), c: new THREE.Vector3(0, 0, -s), crowd, s });
  }
  let current = null;
  window.renderFrame = (i, q = 0.92) => {
    const v = views[i];
    if (current) scene.remove(current);
    if (v.crowd) {
      v.crowd.begin();
      for (let k = 0; k < 25; k++) v.crowd.add(k * 0.137, new THREE.Vector3((k % 5 - 2) * v.s * 0.8, 0, -Math.floor(k / 5) * v.s * 1.1), 0, 1, [0xffffff, 0xe0782c, 0x8d929a, 0x2a2a2e, 0xe9d3a8][k % 5]);
      v.crowd.end(); current = v.crowd.mesh;
    } else { v.actor.seek(v.ph * v.d); current = v.actor.root; }
    scene.add(current);
    camera.position.copy(v.pos); camera.lookAt(v.c); camera.updateMatrixWorld();
    renderer.render(scene, camera);
    return renderer.domElement.toDataURL('image/jpeg', q);
  };
  window.INFO = { info, views: views.map(v => v.id + ':' + v.name), frames: views.length };
  window.READY = true;
}
boot().catch(e => { console.error('[cy] probe failed', e.stack || e); window.FAILED = String(e.stack || e); });
