// Macro cutaway (units: millimetres): quilted blanket fabric above the skin, skin layers (epidermis, dermis,
// fat) with a blood vessel, cut open on the z = 0 plane; the mosquito's fascicle pierces fabric -> skin -> vessel
// while the labium sheath bows back. Built at the world origin; shots place/hide it.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { BUMP_GLSL } from './mosquito.js';
import { makeSkinMaterial } from './skin.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const SEC = { W: 14, D: 8, EPI: 0.25, DERM: 1.6, FAT: 2.4, VES_Y: -1.25, VES_R: 0.42, FAB_Y0: 1.1, FAB_Y1: 2.6 };

function layerMat() {
  // colour by depth below the skin surface (y = 0), cut face shows the layer bands
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.55, sheen: 0.4, sheenColor: new THREE.Color(1, 0.8, 0.8), clearcoat: 0.3, clearcoatRoughness: 0.4 });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float d = -vO.y;
        vec3 epi = vec3(0.55, 0.3, 0.2), derm = vec3(0.62, 0.13, 0.13), fat = vec3(0.8, 0.52, 0.1);
        float n = vnoise3(vO * 6.0), n2 = vnoise3(vO * 22.0);
        vec3 c = d < ${SEC.EPI.toFixed(2)} ? epi * (0.9 + 0.15 * n2) : d < ${SEC.DERM.toFixed(2)} ? derm * (0.82 + 0.25 * n) * (0.92 + 0.12 * n2) : fat;
        if (d >= ${SEC.DERM.toFixed(2)}) { vec2 lob = voro3(vO * 2.2).xy; c *= 0.82 + 0.25 * smoothstep(0.0, 0.25, lob.y - lob.x); }
        // collagen fibres in the dermis
        if (d >= ${SEC.EPI.toFixed(2)} && d < ${SEC.DERM.toFixed(2)}) c *= 0.9 + 0.12 * sin(vO.x * 9.0 + n * 6.0) * sin(vO.y * 14.0 + n * 3.0);
        c = mix(c, c * 0.75, smoothstep(0.03, 0.0, abs(d - ${SEC.EPI.toFixed(2)})) + smoothstep(0.04, 0.0, abs(d - ${SEC.DERM.toFixed(2)})) * 0.6);
        diffuseColor.rgb = c;
        float _H = (d < ${SEC.DERM.toFixed(2)} ? n2 * 0.004 : 0.0);`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
  };
  m.customProgramCacheKey = () => 'sec-layers';
  return m;
}

export function buildSection() {
  const g = new THREE.Group();
  const rnd = mulberry(99);
  const { W, D } = SEC;
  // skin block below y = 0 (cut face at z = 0, block extends to -D)
  const block = new THREE.Mesh(new THREE.BoxGeometry(W, SEC.FAT + SEC.DERM, D, 140, 40, 60), layerMat());
  block.position.set(0, -(SEC.FAT + SEC.DERM) / 2, -D / 2); block.receiveShadow = true; block.castShadow = true; g.add(block);
  // real skin surface on top (crease network, pores)
  const top = new THREE.Mesh(new THREE.PlaneGeometry(W, D, 280, 160), makeSkinMaterial({ base: 0xd9a487, scale: 6 }));
  top.rotation.x = -Math.PI / 2; top.position.set(0, 0.002, -D / 2); top.receiveShadow = true; g.add(top);
  // vessel: dark red tube along z, cut open at z = 0 showing the blood
  const vMat = new THREE.MeshPhysicalMaterial({ color: 0x8a0e12, roughness: 0.25, clearcoat: 0.6, sheen: 0.4, sheenColor: new THREE.Color(1, 0.4, 0.4) });
  const ves = new THREE.Mesh(new THREE.CylinderGeometry(SEC.VES_R, SEC.VES_R, D, 64, 1, true), vMat); ves.rotation.x = Math.PI / 2; ves.position.set(0.6, SEC.VES_Y, -D / 2); g.add(ves);
  const bloodMat = new THREE.MeshPhysicalMaterial({ color: 0xb0080c, roughness: 0.15, clearcoat: 1, emissive: 0x400000 });
  const cap = new THREE.Mesh(new THREE.CircleGeometry(SEC.VES_R * 0.94, 48), bloodMat); cap.position.set(0.6, SEC.VES_Y, 0.004); g.add(cap);
  const wall = new THREE.Mesh(new THREE.RingGeometry(SEC.VES_R * 0.94, SEC.VES_R * 1.12, 48), new THREE.MeshStandardMaterial({ color: 0xd0606a, roughness: 0.5 })); wall.position.set(0.6, SEC.VES_Y, 0.003); g.add(wall);
  // small capillaries in the dermis
  const caps = [];
  for (let i = 0; i < 18; i++) {
    const x = (rnd() - 0.5) * W * 0.9, z = -rnd() * D * 0.9;
    const pts = [V(x, -SEC.DERM + 0.1, z), V(x + (rnd() - 0.5), -0.7, z + (rnd() - 0.5) * 0.5), V(x + (rnd() - 0.5) * 1.5, -0.35, z), V(x + (rnd() - 0.5) * 2, -SEC.DERM + 0.2, z - rnd())];
    caps.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.05, 6, false));
  }
  const capM = new THREE.Mesh(mergeGeometries(caps), new THREE.MeshStandardMaterial({ color: 0xa01418, roughness: 0.4, clippingPlanes: [new THREE.Plane(V(0, 0, -1), 0)] }));
  g.add(capM);

  // blanket fabric: woven top + bottom sheets (thread cylinders) and fluffy fill fibres between, cut at z = 0
  const thread = new THREE.CylinderGeometry(0.11, 0.11, 1, 10, 1, false);
  const fabM = new THREE.MeshPhysicalMaterial({ color: 0x9fbad3, roughness: 0.85, sheen: 1, sheenRoughness: 0.5, sheenColor: new THREE.Color(0.85, 0.9, 1.0) });
  const nWarp = Math.ceil(W / 0.24), nWeft = Math.ceil(D / 0.24);
  const fab = new THREE.InstancedMesh(thread, fabM, 2 * (nWarp + nWeft));
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(); let k = 0;
  for (const y of [SEC.FAB_Y0, SEC.FAB_Y1]) {
    for (let i = 0; i < nWarp; i++) { const x = -W / 2 + (i + 0.5) * 0.24; m4.compose(V(x, y + (i % 2 ? 0.06 : -0.06), -D / 2), q.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)), V(1, D, 1)); fab.setMatrixAt(k++, m4); }
    for (let i = 0; i < nWeft; i++) { const z = -(i + 0.5) * 0.24; m4.compose(V(0, y + (i % 2 ? -0.06 : 0.06), z), q.setFromEuler(new THREE.Euler(0, 0, Math.PI / 2)), V(1, W, 1)); fab.setMatrixAt(k++, m4); }
  }
  fab.castShadow = true; fab.receiveShadow = true; g.add(fab);
  const fibres = [];
  for (let i = 0; i < 420; i++) {
    const x = (rnd() - 0.5) * W, z = -rnd() * D, y = SEC.FAB_Y0 + 0.15 + rnd() * (SEC.FAB_Y1 - SEC.FAB_Y0 - 0.3);
    const pts = []; let p = V(x, y, z); for (let s = 0; s < 4; s++) { pts.push(p.clone()); p = p.clone().add(V((rnd() - 0.5) * 1.2, (rnd() - 0.5) * 0.4, (rnd() - 0.5) * 1.2)); p.y = Math.min(SEC.FAB_Y1 - 0.1, Math.max(SEC.FAB_Y0 + 0.1, p.y)); p.z = Math.min(-0.02, p.z); }
    fibres.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, 0.025, 5, false));
  }
  const fibM = new THREE.Mesh(mergeGeometries(fibres), new THREE.MeshPhysicalMaterial({ color: 0xeef3fa, roughness: 0.7, sheen: 1, sheenColor: new THREE.Color(1, 1, 1) }));
  fibM.castShadow = true; g.add(fibM);

  // proboscis: labium sheath (bows back when the tip touches) + fascicle (pierces)
  const probe = new THREE.Group(); g.add(probe);
  const chit = new THREE.MeshPhysicalMaterial({ color: 0x0c0a09, roughness: 0.55, sheen: 0.8, sheenColor: new THREE.Color(0.5, 0.45, 0.42) });
  const labium = new THREE.Mesh(new THREE.BufferGeometry(), chit); labium.castShadow = true; probe.add(labium);
  const fasM = new THREE.MeshPhysicalMaterial({ color: 0x3a2a22, roughness: 0.35, clearcoat: 0.5, emissive: 0x000000 });
  const fascicle = new THREE.Mesh(new THREE.BufferGeometry(), fasM); fascicle.castShadow = true; probe.add(fascicle);
  // blood column rising inside the fascicle (rendered slightly outside so it reads)
  const column = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0xff2015, transparent: true, opacity: 0.85, depthWrite: false, blending: THREE.AdditiveBlending }));
  probe.add(column);
  const X = 0.6, TOP = 9;
  // tipY: fascicle tip height (TOP .. VES_Y); bow: labium bowing 0..1; blood: 0..1 column height
  function set(tipY, bow, blood = 0) {
    const sheathEnd = Math.max(SEC.FAB_Y1 + 0.15, tipY);
    const bowPts = [V(X, TOP, 0.0), V(X - 0.15 - 1.4 * bow, (TOP + sheathEnd) / 2 + 0.3, 0.05), V(X - 0.05 - 0.2 * bow, sheathEnd + 0.15, 0.02)];
    labium.geometry.dispose(); labium.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(bowPts), 40, 0.24, 14, false);
    const fasPts = [V(X, TOP, 0.0), V(X, (TOP + tipY) / 2, 0.0), V(X, tipY, 0.0)];
    const fg = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(fasPts), 60, 0.09, 10, false);
    // serrated, pointed tip
    const P = fg.attributes.position; for (let i = 0; i < P.count; i++) { const y = P.getY(i); const u = (y - tipY) / 0.6; if (u < 1) { const k = Math.max(0.05, u) * (1 + 0.25 * Math.sin(y * 40)); P.setX(i, X + (P.getX(i) - X) * Math.min(1, k)); P.setZ(i, P.getZ(i) * Math.min(1, k)); } }
    fg.computeVertexNormals(); fascicle.geometry.dispose(); fascicle.geometry = fg;
    const by = tipY + (TOP - tipY) * blood;
    column.visible = blood > 0.01;
    if (column.visible) { column.geometry.dispose(); column.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(X, tipY + 0.1, 0.0), V(X, by, 0.0)]), 20, 0.1, 10, false); }
  }
  set(TOP - 1, 0);
  // fabric threads/fibres near the path part when pierced: simple shader-free approach (fibres stay; thread gap)
  return { group: g, set, X, TOP, fasM };
}
