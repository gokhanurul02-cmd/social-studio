// Procedural, faceted Cybertruck-style pickup built from cross-section stations.
// Origin: ground level, centre of footprint; front faces +Z. Length 5.68 m, width 2.0 m.
import * as THREE from 'three';

const L2 = 2.84;
const APEX_Z = 0.25, APEX_Y = 1.80, NOSE_Y = 1.08, TAIL_Y = 1.30;
const yTop = z => z >= APEX_Z ? THREE.MathUtils.lerp(APEX_Y, NOSE_Y, (z - APEX_Z) / (L2 - APEX_Z))
                              : THREE.MathUtils.lerp(APEX_Y, TAIL_Y, (APEX_Z - z) / (L2 + APEX_Z));
const yShoulder = z => Math.min(yTop(z) - 0.035, THREE.MathUtils.lerp(1.24, 1.03, (z + L2) / (2 * L2)));
const wTop = z => {
  if (z > 1.45) return THREE.MathUtils.lerp(0.74, 0.68, (z - 1.45) / (L2 - 1.45));
  if (z > APEX_Z) return THREE.MathUtils.lerp(0.60, 0.80, (z - APEX_Z) / (1.45 - APEX_Z));
  if (z > -0.95) return THREE.MathUtils.lerp(0.60, 0.74, (APEX_Z - z) / (APEX_Z + 0.95));
  return 0.78;
};
export const FRONT_AXLE = 1.66, REAR_AXLE = -2.15, WHEEL_R = 0.46, TRACK = 0.84;

export function makeMaterials(scene) {
  return {
    steel: new THREE.MeshPhysicalMaterial({ color: 0xf2f0f6, metalness: 1.0, roughness: 0.2, envMapIntensity: 2.2, clearcoat: 0.3, clearcoatRoughness: 0.1 }),
    glass: new THREE.MeshPhysicalMaterial({ color: 0x050608, metalness: 0.0, roughness: 0.06, envMapIntensity: 0.55, clearcoat: 0.6 }),
    clad: new THREE.MeshStandardMaterial({ color: 0x1c1d21, metalness: 0.1, roughness: 0.65 }),
    under: new THREE.MeshStandardMaterial({ color: 0x0e0f12, roughness: 0.9 }),
    light: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 3.0 }),
    redLight: new THREE.MeshStandardMaterial({ color: 0x400000, emissive: 0xff1a10, emissiveIntensity: 2.0 }),
    tire: new THREE.MeshStandardMaterial({ color: 0x2a2622, roughness: 0.92 }),
    hub: new THREE.MeshStandardMaterial({ color: 0x34363b, metalness: 0.6, roughness: 0.35 }),
  };
}

function bodyGeometry() {
  // stations: z, yBot (lower edge of side band; raised over wheels to make the arches)
  const fa = FRONT_AXLE, ra = REAR_AXLE, aw = 0.60;
  const st = [
    [L2, 0.80], [fa + aw + 0.12, 0.62], [fa + aw, 0.98], [fa + 0.2, 1.00], [fa - 0.2, 1.00], [fa - aw, 0.98], [fa - aw - 0.12, 0.50],
    [1.45, 0.50], [APEX_Z, 0.50], [-0.95, 0.50],
    [ra + aw + 0.12, 0.50], [ra + aw, 0.98], [ra + 0.2, 1.00], [ra - 0.2, 1.00], [ra - aw, 0.98], [-L2 + 0.02, 0.62], [-L2, 0.62],
  ].sort((a, b) => b[0] - a[0]);
  // material index by segment: 0 top, 1 upper side, 2 side, 3 cladding
  const segMat = z => {
    const cabin = z < 1.45 && z > -0.95;
    return [cabin ? 1 : 0, cabin ? 1 : 0, 0, 2];
  };
  const ring = (z, yb) => {
    const yt = yTop(z), ys = yShoulder(z), wt = wTop(z);
    const wSide = 1.0 - Math.max(0, z - 2.3) * 0.12; // nose tucks in a little
    const clad = Math.min(yb + 0.3, ys - 0.05);
    return [[0, yt], [wt, yt], [wSide, ys], [wSide - 0.005, clad], [wSide - 0.03, yb]];
  };
  const pos = [], groups = [[], [], [], []]; // per material triangle lists
  const pushQuad = (m, a, b, c, d) => { groups[m].push(a, b, c, a, c, d); };
  for (let i = 0; i < st.length - 1; i++) {
    const [z0, b0] = st[i], [z1, b1] = st[i + 1];
    const r0 = ring(z0, b0), r1 = ring(z1, b1);
    const mats = segMat((z0 + z1) / 2);
    for (let s = 0; s < r0.length - 1; s++) {
      for (const side of [1, -1]) {
        const A = [side * r0[s][0], r0[s][1], z0], B = [side * r0[s + 1][0], r0[s + 1][1], z0];
        const C = [side * r1[s + 1][0], r1[s + 1][1], z1], D = [side * r1[s][0], r1[s][1], z1];
        if (side > 0) pushQuad(mats[s], A, B, C, D); else pushQuad(mats[s], A, D, C, B);
      }
    }
  }
  // end caps (front fascia & tailgate) as fans
  for (const [z, yb, flip] of [[L2, 0.80, 1], [-L2, 0.62, -1]]) {
    const r = ring(z, yb);
    const pts = [...r.map(p => [p[0], p[1], z]), ...r.slice().reverse().map(p => [-p[0], p[1], z])];
    const c = [0, (r[0][1] + yb) / 2, z];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1];
      if (flip > 0) groups[0].push(c, b, a); else groups[0].push(c, a, b);
    }
  }
  const g = new THREE.BufferGeometry();
  let off = 0;
  for (let m = 0; m < groups.length; m++) {
    for (const p of groups[m]) pos.push(...p);
    g.addGroup(off, groups[m].length, m); off += groups[m].length;
  }
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

function tireTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const x = c.getContext('2d'); x.fillStyle = '#777'; x.fillRect(0, 0, 512, 64);
  x.fillStyle = '#222';
  for (let i = 0; i < 48; i++) { const px = i * 512 / 48; x.fillRect(px, 0, 4, 64); x.fillRect(px + 5, (i % 2) * 32, 3, 32); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}

let _bodyGeo = null, _tireTex = null;
export function makeTruck(M) {
  if (!_bodyGeo) _bodyGeo = bodyGeometry();
  if (!_tireTex) _tireTex = tireTexture();
  const g = new THREE.Group();
  const body = new THREE.Mesh(_bodyGeo, [M.steel, M.glass, M.clad, M.clad]);
  body.castShadow = true; body.receiveShadow = true; g.add(body);
  // chassis / underbody block filling the arches
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.42, 5.3), M.under);
  chassis.position.set(0, 0.62, 0); chassis.castShadow = true; g.add(chassis);
  // front bumper + lower grille slots
  const bumper = new THREE.Mesh(new THREE.BoxGeometry(1.36, 0.2, 0.26), M.clad);
  bumper.position.set(0, 0.72, L2 - 0.1); bumper.castShadow = true; g.add(bumper);
  for (let i = -3; i <= 3; i++) {
    const slot = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.05, 0.02), M.under);
    slot.position.set(i * 0.17, 0.72, L2 + 0.035); g.add(slot);
  }
  // full-width light bar at the nose crest, and the tail light bar
  const bar = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.022, 0.03), M.light);
  bar.position.set(0, NOSE_Y - 0.03, L2 + 0.006); g.add(bar);
  const tail = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.03, 0.03), M.redLight);
  tail.position.set(0, TAIL_Y - 0.06, -L2 - 0.01); g.add(tail);
  // wheels
  const tireGeo = new THREE.CylinderGeometry(WHEEL_R, WHEEL_R, 0.37, 48, 1);
  tireGeo.rotateZ(Math.PI / 2);
  const tireMat = M.tire.clone(); tireMat.bumpMap = _tireTex; tireMat.bumpScale = 3; _tireTex.repeat.set(2, 1);
  const hubGeo = new THREE.CylinderGeometry(0.29, 0.29, 0.35, 12); hubGeo.rotateZ(Math.PI / 2);
  g.userData.wheels = [];
  for (const z of [FRONT_AXLE, REAR_AXLE]) for (const s of [1, -1]) {
    const w = new THREE.Group(); w.position.set(s * TRACK, WHEEL_R, z);
    const t = new THREE.Mesh(tireGeo, tireMat); t.castShadow = true; w.add(t);
    const h = new THREE.Mesh(hubGeo, M.hub); w.add(h);
    g.add(w); g.userData.wheels.push(w);
  }
  return g;
}

// tow points (local) at the nose corners
export const HOOKS = [new THREE.Vector3(-0.72, 0.5, L2 + 0.1), new THREE.Vector3(0.72, 0.5, L2 + 0.1)];
export const TRUCK_HALF_LEN = L2;
