// Props for the frog-heart episode (metres unless noted): blue nitrile glove hand (SDF, cm), tweezers,
// chest "porthole" cavity, x-ray ribcage, pea, ice block, hurdles, snow, fog puffs, fridge + kitchen.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { smin, ellipsoid, cone, chain, polygonize } from './sdf.js';
import { BUMP_GLSL } from './mosquito.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

function bumpMat(mat, key, colorCode, H = '0.0', extra = '') {
  mat.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vW2;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvW2 = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vW2;\n' + BUMP_GLSL + extra)
      .replace('#include <color_fragment>', '#include <color_fragment>\nfloat _H = 0.0;\n{ ' + colorCode + '\n _H = ' + H + '; }')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
    if (mat.userData.u) Object.assign(sh.uniforms, mat.userData.u);
  };
  mat.customProgramCacheKey = () => key;
  return mat;
}

// ---------------------------------------------------------------- glove hand (cm; wrist at origin, fingers +z, palm down -y)
let HAND_GEO = null;
export const PINCH = V(-1.25, -1.9, 10.4);   // where index and thumb pads meet (tweezer grip)
function handSDF(x, y, z) {
  let d = ellipsoid(x, y, z, 0, 0, 4.2, 4.0, 1.35, 4.0);
  d = smin(d, cone(x, y, z, [0, 0.1, 0.5], [0, 0.4, -12], 2.5, 3.3), 1.5);
  const F = [
    [[[-2.4, 0.2, 7.4], [-2.3, -0.3, 9.9], [-1.8, -1.2, 11.1], [-1.3, -1.8, 10.6]], [0.95, 0.85, 0.76, 0.7]],
    [[[-0.6, 0.3, 7.9], [-0.5, -0.6, 10.5], [-0.4, -2.0, 10.8], [-0.3, -2.5, 9.6]], [0.98, 0.88, 0.78, 0.72]],
    [[[1.2, 0.2, 7.6], [1.2, -0.8, 9.8], [1.1, -2.0, 9.7], [1.0, -2.3, 8.7]], [0.93, 0.84, 0.75, 0.7]],
    [[[2.8, 0.0, 6.9], [2.95, -0.9, 8.6], [2.85, -1.8, 8.6], [2.6, -2.1, 7.8]], [0.8, 0.72, 0.65, 0.6]],
    [[[-3.1, -0.6, 2.5], [-4.4, -1.6, 5.5], [-3.4, -2.3, 8.3], [-1.8, -2.1, 10.0]], [1.4, 1.05, 0.9, 0.78]],
  ];
  for (const [p, r] of F) d = smin(d, chain(x, y, z, p, r, 0.25), 0.5);
  return d;
}
export function makeGlove() {
  if (!HAND_GEO) HAND_GEO = polygonize(handSDF, [-6.5, -4.2, -12.5], [5.0, 3.0, 12.6], 0.13);
  const m = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0x46b2f2, roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.35, sheen: 0.6, sheenColor: new THREE.Color(0.7, 0.85, 1.0) }), 'glove',
    'float n = vnoise3(vO * 1.3) * 0.6 + vnoise3(vO * 5.0) * 0.4; diffuseColor.rgb *= 0.92 + 0.12 * n;',
    '(vnoise3(vO * vec3(2.0, 6.0, 1.2)) * 0.6 + vnoise3(vO * 14.0) * 0.4) * 0.00035');
  const mesh = new THREE.Mesh(HAND_GEO, m); mesh.castShadow = true; mesh.receiveShadow = true;
  const g = new THREE.Group(); g.add(mesh); g.scale.setScalar(0.01);
  return g;
}

// ---------------------------------------------------------------- tweezers (cm; hinge at origin, tips along +z, length 12.5)
export function makeTweezers() {
  const g = new THREE.Group();
  const metal = new THREE.MeshPhysicalMaterial({ color: 0xc4c9cf, metalness: 0.85, roughness: 0.3, envMapIntensity: 0.5, clearcoat: 0.3 });
  const blades = [];
  for (const s of [-1, 1]) {
    const geo = new THREE.BoxGeometry(1, 0.11, 12.5, 1, 1, 40); geo.translate(0, 0, 6.25);
    const P = geo.attributes.position;
    for (let i = 0; i < P.count; i++) { const z = P.getZ(i), u = z / 12.5; const w = 1.05 * (1 - u) + 0.2 * u; P.setX(i, P.getX(i) * w); P.setY(i, P.getY(i) + s * (0.06 + 0.5 * Math.sin(Math.PI * Math.min(1, u * 1.15)) * (1 - u * 0.6))); }
    geo.computeVertexNormals();
    const piv = new THREE.Group(); const b = new THREE.Mesh(geo, metal); b.castShadow = true; piv.add(b); g.add(piv); blades.push({ piv, s });
  }
  const hinge = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.5, 0.8), metal); hinge.position.z = -0.2; hinge.castShadow = true; g.add(hinge);
  g.scale.setScalar(0.01);
  return { group: g, setOpen(o) { for (const b of blades) b.piv.rotation.x = b.s * (0.012 + 0.05 * o) - b.s * 0.045; } };
}

// ---------------------------------------------------------------- chest porthole (local: opening at z=0 facing +z, cavity to -z)
export function makeChestHole(R = 0.075, D = 0.13) {
  const g = new THREE.Group();
  const u = { uRim: { value: new Array(32).fill(0.0) } };
  const wallM = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.4, clearcoat: 0.6, clearcoatRoughness: 0.2, side: THREE.BackSide });
  wallM.userData.u = u;
  bumpMat(wallM, 'chest-wall', `
    float a = atan(vO.y, vO.x); float k = (a / 6.2831853 + 0.5) * 32.0; int i0 = int(floor(k)) % 32; int i1 = (i0 + 1) % 32;
    float rim = mix(uRim[i0], uRim[i1], fract(k));
    if (vO.z > rim) discard;
    float dep = rim - vO.z; float n = vnoise3(vO * 400.0), n2 = vnoise3(vO * 90.0);
    vec3 skin = vec3(0.78, 0.48, 0.36), fat = vec3(0.92, 0.75, 0.32) * (0.85 + 0.25 * n), musc = vec3(0.55, 0.06, 0.06) * (0.75 + 0.35 * n2) * (0.85 + 0.2 * sin(vO.z * 700.0 + n * 4.0));
    vec3 c = dep < 0.004 ? skin : dep < 0.014 ? fat : musc;
    c *= 1.0 - 0.45 * smoothstep(0.02, ${D.toFixed(3)}, dep);
    diffuseColor.rgb = c;`, '(vnoise3(vO * 300.0)) * 0.0004', 'uniform float uRim[32];');
  const wg = new THREE.CylinderGeometry(R, R * 0.9, D + 0.09, 64, 30, true); wg.rotateX(Math.PI / 2); wg.translate(0, 0, 0.06 - (D + 0.09) / 2);
  const wall = new THREE.Mesh(wg, wallM); wall.receiveShadow = true; g.add(wall);
  const backM = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.35, clearcoat: 0.7 }), 'chest-back',
    'float n = vnoise3(vO * 120.0), n2 = vnoise3(vO * 400.0); diffuseColor.rgb = vec3(0.32, 0.03, 0.04) * (0.7 + 0.5 * n) * (0.9 + 0.2 * n2);', 'vnoise3(vO * 160.0) * 0.0012');
  const back = new THREE.Mesh(new THREE.CircleGeometry(R * 0.95, 48), backM); back.position.z = -D; back.receiveShadow = true; g.add(back);
  const boneM = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.55, clearcoat: 0.2, envMapIntensity: 0.4 }), 'bone',
    'float n = vnoise3(vO * 300.0); diffuseColor.rgb = vec3(0.86, 0.80, 0.68) * (0.88 + 0.16 * n);', 'vnoise3(vO * 500.0) * 0.0002');
  for (const y of [-0.62, 0.0, 0.62]) {
    const rib = new THREE.Mesh(new THREE.CapsuleGeometry(0.0085, R * 2.2, 8, 24), boneM);
    rib.rotation.z = Math.PI / 2 + 0.12; rib.position.set(0, y * R, -D * 0.72); rib.castShadow = true; rib.receiveShadow = true; g.add(rib);
  }
  return { group: g, R, D, u };
}

// ---------------------------------------------------------------- x-ray ribcage + spine from the posed rig (world space)
export function makeRibcage(rig, mat) {
  const J = n => rig.bones[n].getWorldPosition(V(0, 0, 0));
  const s1 = J('Spine1'), s2 = J('Spine2'), nk = J('Neck');
  const right = J('LeftShoulder').sub(J('RightShoulder')).setY(0).normalize();
  const fwd = V(0, 1, 0).cross(right).normalize();
  const geos = [];
  const back = s1.clone().addScaledVector(fwd, -0.05);
  for (let i = 0; i < 10; i++) {
    const y = nk.y - 0.06 - i * 0.032, w = 0.105 + 0.045 * Math.sin(Math.PI * Math.min(1, (i + 2) / 11)), dz = 0.1 + 0.012 * Math.sin(i * 0.4);
    for (const s of [-1, 1]) {
      const pts = [];
      for (let k = 0; k <= 12; k++) {
        const a = -Math.PI / 2 + (k / 12) * Math.PI * 0.86;
        const p = V(back.x, y - 0.04 * (k / 12), back.z).addScaledVector(right, s * w * Math.cos(a)).addScaledVector(fwd, dz * (Math.sin(a) + 1) * 0.5 + 0.0);
        pts.push(p);
      }
      geos.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, 0.0065, 8, false));
    }
  }
  for (let i = 0; i < 22; i++) {
    const y = nk.y + 0.04 - i * 0.026;
    const c = V(back.x, y, back.z).addScaledVector(fwd, -0.01);
    const cyl = new THREE.CylinderGeometry(0.016, 0.016, 0.018, 16); cyl.translate(c.x, c.y, c.z); geos.push(cyl);
  }
  const st = new THREE.BoxGeometry(0.03, 0.17, 0.012); const sc = V(back.x, nk.y - 0.15, back.z).addScaledVector(fwd, 0.1); st.translate(sc.x, sc.y, sc.z); geos.push(st);
  const mesh = new THREE.Mesh(mergeGeometries(geos.map(g => g.index ? g.toNonIndexed() : g).map(g => { g.deleteAttribute('uv'); return g; })), mat);
  mesh.renderOrder = 4; mesh.frustumCulled = false;
  return mesh;
}

// ---------------------------------------------------------------- pea
export function makePea() {
  const m = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.35, clearcoat: 0.6 }), 'pea',
    'float n = vnoise3(vO * 900.0); diffuseColor.rgb = vec3(0.18, 0.46, 0.05) * (0.85 + 0.25 * n);', 'vnoise3(vO * 500.0) * 0.0003');
  const p = new THREE.Mesh(new THREE.SphereGeometry(0.0045, 32, 24), m); p.castShadow = true; return p;
}

// ---------------------------------------------------------------- ice block
export function makeIceBlock(w = 0.95, h = 2.05, d = 0.85) {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xe8f7ff, transmission: 1, thickness: 0.6, roughness: 0.1, ior: 1.31, attenuationColor: new THREE.Color(0.6, 0.85, 1.0), attenuationDistance: 1.2, clearcoat: 1, clearcoatRoughness: 0.15, specularIntensity: 1 });
  bumpMat(m, 'ice', 'float n = vnoise3(vO * 6.0); vec2 v = voro3(vO * 4.0); float cr = 1.0 - smoothstep(0.0, 0.03, v.y - v.x); diffuseColor.rgb = mix(vec3(0.92, 0.98, 1.0), vec3(1.0), cr * 0.6);',
    '(vnoise3(vO * 9.0) * 0.6 + vnoise3(vO * 30.0) * 0.4) * 0.0025');
  const mesh = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 6, 0.06), m); mesh.position.y = h / 2; mesh.castShadow = true;
  const frostM = bumpMat(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.8, transparent: true, opacity: 1, depthWrite: false }), 'icefrost',
    'float n = vnoise3(vO * 5.0) * 0.6 + vnoise3(vO * 20.0) * 0.4; float a = smoothstep(0.45, 0.8, n) * 0.55 + smoothstep(0.0, 0.25, -vO.y + ' + (-h / 2 + 0.25).toFixed(3) + ') * 0.4; diffuseColor = vec4(vec3(0.93, 0.97, 1.0), a);',
    'vnoise3(vO * 40.0) * 0.001');
  const frost = new THREE.Mesh(new RoundedBoxGeometry(w + 0.01, h + 0.01, d + 0.01, 6, 0.065), frostM); frost.position.y = h / 2; frost.renderOrder = 3;
  const g = new THREE.Group(); g.add(mesh, frost); return g;
}

// ---------------------------------------------------------------- hurdle (track along +x; bar across z)
export function makeHurdle(width = 1.2, height = 0.92) {
  const g = new THREE.Group();
  const white = new THREE.MeshPhysicalMaterial({ color: 0xf4f4f4, roughness: 0.35, clearcoat: 0.5 });
  const black = new THREE.MeshPhysicalMaterial({ color: 0x151515, roughness: 0.4 });
  const barM = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.3, clearcoat: 0.6 }), 'hurdlebar',
    'float s = step(0.5, fract(vO.z * 4.2 + 0.25)); diffuseColor.rgb = mix(vec3(0.95), vec3(0.04), s);');
  const bar = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.12, width), barM); bar.position.y = height - 0.06; g.add(bar);
  for (const s of [-1, 1]) {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, height, 12), white); post.position.set(0, height / 2, s * width / 2); g.add(post);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.03, 0.04), black); foot.position.set(-0.3, 0.015, s * width / 2); g.add(foot);
  }
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

// ---------------------------------------------------------------- snow flakes (instanced, deterministic)
export function makeSnow(n = 1400, box = [8, 5, 8]) {
  const r = mulberry(77);
  const mesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6, emissive: 0x9aa4b0, emissiveIntensity: 0.5 }), n);
  mesh.frustumCulled = false;
  const P = Array.from({ length: n }, () => [r(), r(), r(), 0.004 + 0.006 * r(), r()]);
  const m4 = new THREE.Matrix4();
  function update(t, c, scale = 1) {
    P.forEach(([x, y, z, s, ph], i) => {
      const yy = ((y - t * (0.12 + 0.06 * ph)) % 1 + 1) % 1;
      m4.makeScale(s * scale, s * scale, s * scale).setPosition(c.x + (x - 0.5) * box[0] * scale + 0.15 * scale * Math.sin(t * 1.3 + ph * 9), c.y + (yy - 0.3) * box[1] * scale, c.z + (z - 0.5) * box[2] * scale);
      mesh.setMatrixAt(i, m4);
    });
    mesh.instanceMatrix.needsUpdate = true;
  }
  return { mesh, update };
}

// ---------------------------------------------------------------- fog/steam puffs (billboards)
export function makeFog(n = 70) {
  const r = mulberry(13);
  const u = { uA: { value: 1 } };
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: u,
    vertexShader: 'attribute float aA; varying vec2 vUv; varying float vA; void main(){ vUv = uv; vA = aA; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform float uA; varying vec2 vUv; varying float vA;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      float n2(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f); return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
      void main(){ vec2 q = vUv - 0.5; float d = length(q) * 2.0; float n = n2(vUv * 5.0 + vA * 10.0) * 0.6 + n2(vUv * 11.0 - vA * 7.0) * 0.4;
        float a = (1.0 - smoothstep(0.2, 1.0, d + 0.35 * (n - 0.5))) * vA * uA * 0.55; gl_FragColor = vec4(vec3(0.93, 0.96, 1.0) * 1.15, a); }` });
  const geo = new THREE.PlaneGeometry(1, 1);
  const mesh = new THREE.InstancedMesh(geo, m, n); mesh.frustumCulled = false; mesh.renderOrder = 8;
  const aA = new Float32Array(n); geo.setAttribute('aA', new THREE.InstancedBufferAttribute(aA, 1));
  const P = Array.from({ length: n }, () => [r(), r(), r(), r()]);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = V(1, 1, 1), p = V(0, 0, 0);
  // origin: fridge opening centre; dir: outwards; k: 0..1 release progress
  function update(t, origin, dir, k, camQ, amount = 1) {
    P.forEach(([a, b, c, d], i) => {
      const age = Math.max(0, k * 1.4 - a * 0.6);
      const out = 0.15 + age * (0.5 + 0.6 * b), fall = Math.min(1, age * 0.9);
      p.copy(origin).addScaledVector(dir, out).add(V((c - 0.5) * 0.9 + 0.2 * Math.sin(t + i), lerpN(0.9 * (d - 0.5) * 2, -0.85, fall), (b - 0.5) * 0.5));
      const sz = (0.35 + 0.5 * d) * (0.6 + age * 0.8);
      q.copy(camQ).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), d * 6.28 + t * 0.2 * (c - 0.5)));
      s.set(sz, sz, sz); m4.compose(p, q, s); mesh.setMatrixAt(i, m4);
      aA[i] = amount * Math.min(1, age * 3) * Math.max(0, 1 - age * 0.45) * (0.5 + 0.5 * a);
    });
    mesh.instanceMatrix.needsUpdate = true; geo.attributes.aA.needsUpdate = true;
  }
  return { mesh, update };
}
const lerpN = (a, b, t) => a + (b - a) * t;

// ---------------------------------------------------------------- fridge + kitchen (fridge faces +z, centred at x=0, floor y=0)
export function makeFridge() {
  const W = 1.0, H = 2.1, D = 0.82, T = 0.06;
  const g = new THREE.Group();
  const shell = new THREE.MeshPhysicalMaterial({ color: 0xf2f4f5, roughness: 0.25, clearcoat: 0.8, clearcoatRoughness: 0.1 });
  const u = { uFrost: { value: 1 } };
  const liner = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.4, clearcoat: 0.4 }); liner.userData.u = u;
  bumpMat(liner, 'fridge-liner', 'float n = vnoise3(vW2 * 9.0) * 0.6 + vnoise3(vW2 * 35.0) * 0.4; float f = uFrost * smoothstep(0.35, 0.75, n); diffuseColor.rgb = mix(vec3(0.93, 0.95, 0.96), vec3(0.85, 0.93, 1.0), f);',
    'uFrost * vnoise3(vW2 * 60.0) * 0.0015', 'uniform float uFrost;');
  const box = (w, h, d, x, y, z, m) => { const b = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 3, 0.012), m); b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; g.add(b); return b; };
  box(W, H, T, 0, H / 2, -D / 2 + T / 2, shell); box(T, H, D, -W / 2 + T / 2, H / 2, 0, shell); box(T, H, D, W / 2 - T / 2, H / 2, 0, shell);
  box(W, T, D, 0, H - T / 2, 0, shell); box(W, T * 2, D, 0, T, 0, shell);
  box(W - 2 * T - 0.004, H - 3 * T, 0.01, 0, H / 2 + 0.02, -D / 2 + T + 0.006, liner); box(0.01, H - 3 * T, D - T, -W / 2 + T + 0.006, H / 2, 0.02, liner); box(0.01, H - 3 * T, D - T, W / 2 - T - 0.006, H / 2, 0.02, liner);
  box(W - 2 * T, 0.01, D - T, 0, H - T - 0.006, 0.02, liner); box(W - 2 * T, 0.01, D - T, 0, 2 * T + 0.006, 0.02, liner);
  // door (hinge on the +x side)
  const hinge = new THREE.Group(); hinge.position.set(W / 2, 0, D / 2); g.add(hinge);
  const door = new THREE.Mesh(new RoundedBoxGeometry(W, H, 0.08, 3, 0.02), shell); door.position.set(-W / 2, H / 2, 0.04); door.castShadow = true; door.receiveShadow = true; hinge.add(door);
  const inner = new THREE.Mesh(new RoundedBoxGeometry(W - 0.12, H - 0.14, 0.03, 2, 0.01), liner); inner.position.set(-W / 2, H / 2, -0.005); hinge.add(inner);
  const steel = new THREE.MeshPhysicalMaterial({ color: 0xcfd3d6, metalness: 1, roughness: 0.25 });
  const handle = new THREE.Mesh(new THREE.CapsuleGeometry(0.014, 0.55, 6, 12), steel); handle.position.set(-W + 0.08, H * 0.62, 0.13); handle.castShadow = true; hinge.add(handle);
  for (const y of [0.55, 1.05, 1.5]) {
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(W - 0.16, 0.012, 0.1), new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.1, transmission: 0.0, transparent: true, opacity: 0.5 })); shelf.position.set(-W / 2, y, -0.07); hinge.add(shelf);
    const cols = [0xe23b2a, 0x2f9c3a, 0xf2c230, 0x2a6fd6];
    for (let k = 0; k < 4; k++) { const bt = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.2, 16), new THREE.MeshPhysicalMaterial({ color: cols[(k + Math.round(y * 3)) % 4], roughness: 0.2, clearcoat: 1 })); bt.position.set(-W / 2 - 0.3 + k * 0.2, y + 0.106, -0.07); bt.castShadow = true; hinge.add(bt); }
  }
  const light = new THREE.PointLight(0xdff0ff, 0, 3.5, 1.5); light.position.set(0, H - 0.2, 0.1); g.add(light);
  return { group: g, hinge, light, u, W, H, D };
}
export function makeKitchen() {
  const g = new THREE.Group();
  const floor = bumpMat(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.3, clearcoat: 0.5 }), 'kfloor',
    'vec2 q = vW2.xz / 0.45; vec2 f = abs(fract(q) - 0.5); float grout = 1.0 - smoothstep(0.47, 0.485, max(f.x, f.y)); float n = vnoise3(vW2 * 4.0); float ch = mod(floor(q.x) + floor(q.y), 2.0);' +
    'diffuseColor.rgb = mix(vec3(0.55, 0.55, 0.57), mix(vec3(0.86, 0.85, 0.82), vec3(0.78, 0.8, 0.82), ch) * (0.92 + 0.1 * n), grout);', '0.0');
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), floor); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; g.add(fl);
  const wallM = bumpMat(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.85 }), 'kwall', 'diffuseColor.rgb = vec3(0.62, 0.78, 0.86) * (0.95 + 0.06 * vnoise3(vW2 * 3.0));');
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(30, 8), wallM); wall.position.set(0, 4, -0.5); wall.receiveShadow = true; g.add(wall);
  const cab = new THREE.MeshPhysicalMaterial({ color: 0xf6f3ee, roughness: 0.4, clearcoat: 0.3 });
  const top = new THREE.MeshPhysicalMaterial({ color: 0x3b3f44, roughness: 0.25, clearcoat: 0.8 });
  for (const s of [-1, 1]) {
    const c = new THREE.Mesh(new RoundedBoxGeometry(1.8, 0.9, 0.62, 3, 0.01), cab); c.position.set(s * 1.55, 0.45, -0.18); c.castShadow = true; c.receiveShadow = true; g.add(c);
    const t2 = new THREE.Mesh(new RoundedBoxGeometry(1.84, 0.04, 0.66, 3, 0.01), top); t2.position.set(s * 1.55, 0.92, -0.16); t2.castShadow = true; g.add(t2);
  }
  return g;
}
