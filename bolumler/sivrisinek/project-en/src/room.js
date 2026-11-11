// Clean bright bedroom (Zack D. style: simple shapes, realistic PBR materials): wood floor, painted walls,
// window with sky/moon, bed (frame, mattress, sheet, pillows, draped blanket), nightstand with lamp.
// Layout (metres): bed head at x = -1.1, foot at x = +1.05, width z in [-0.8, 0.8], mattress top y = 0.6.
// Walls: x = -1.35 (behind the headboard) and z = -1.6 (window wall).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { BUMP_GLSL } from './mosquito.js';

export const MATTRESS_TOP = 0.6;

function withShader(mat, key, colorCode, heightCode = '0.0', roughCode = null) {
  mat.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix*vec4(transformed,1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', '#include <color_fragment>\n' + colorCode + `\nfloat _H = ${heightCode};`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
    if (roughCode) sh.fragmentShader = sh.fragmentShader.replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n' + roughCode);
  };
  mat.customProgramCacheKey = () => key;
  // worldpos_vertex is only emitted for some features; force it
  mat.defines = { ...(mat.defines || {}), USE_SHADOWMAP_WORLDPOS: '' };
  return mat;
}

function woodMat(key, base, plank = 0.18) {
  return withShader(new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.45, clearcoat: 0.35, clearcoatRoughness: 0.25 }), key, `
    vec2 q = vW.xz; float row = floor(q.y / ${plank.toFixed(3)});
    float off = fract(sin(row * 12.9898) * 43758.5453) * 2.0;
    float plankId = floor((q.x + off) / 1.2) + row * 17.0;
    float grain = vnoise3(vec3(q.x * 3.0, q.y * 140.0 + plankId, plankId)) * 0.6 + vnoise3(vec3(q.x * 40.0, q.y * 400.0, plankId)) * 0.4;
    vec3 c = ${base} * (0.78 + 0.32 * grain) * (0.88 + 0.2 * fract(sin(plankId * 3.7) * 1000.0));
    float gapZ = abs(fract(q.y / ${plank.toFixed(3)}) - 0.5) * ${plank.toFixed(3)};
    float gapX = abs(fract((q.x + off) / 1.2) - 0.5) * 1.2;
    float gap = max(smoothstep(${(plank / 2 - 0.002).toFixed(4)}, ${(plank / 2).toFixed(4)}, gapZ), smoothstep(0.598, 0.6, gapX));
    diffuseColor.rgb = mix(c, c * 0.35, gap);`, '-gap * 0.0015 + grain * 0.0003');
}
function paintMat(key, hex) {
  return withShader(new THREE.MeshStandardMaterial({ color: hex, roughness: 0.88 }), key,
    'diffuseColor.rgb *= 0.97 + 0.05 * vnoise3(vW * 3.0);', 'vnoise3(vW * 260.0) * 0.00025');
}
function fabricMat(key, hex, weave = 900, sheen = 0.8) {
  const m = new THREE.MeshPhysicalMaterial({ color: hex, roughness: 0.85, sheen, sheenRoughness: 0.6, sheenColor: new THREE.Color(0.9, 0.9, 0.95) });
  return withShader(m, key, `float wv = sin(vW.x * ${weave.toFixed(1)}) * sin(vW.z * ${weave.toFixed(1)} + vW.y * ${weave.toFixed(1)});
    diffuseColor.rgb *= 0.96 + 0.05 * wv + 0.04 * vnoise3(vW * 20.0);`, `wv * 0.00012 + vnoise3(vW * 35.0) * 0.0009`);
}

export function makeBedroom() {
  const g = new THREE.Group();
  const add = (geo, mat, x, y, z, cast = true) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = cast; m.receiveShadow = true; g.add(m); return m; };
  // floor
  add(new THREE.PlaneGeometry(6, 6), woodMat('floor', 'vec3(0.62, 0.40, 0.24)'), 1.6, 0, 1.35, false).rotation.x = -Math.PI / 2;
  // walls (with a window opening in the z = -1.6 wall: x in [-0.55, 0.75], y in [0.95, 2.15])
  const wall = paintMat('wall', 0xe9e4da), wall2 = paintMat('wall2', 0xb8cbdc);
  const H = 2.7;
  add(new THREE.BoxGeometry(0.1, H, 9), wall2, -1.4, H / 2, 2.4);                    // behind the headboard (accent blue)
  const WZ = -1.65, x0 = -0.55, x1 = 0.75, y0 = 0.95, y1 = 2.15;
  add(new THREE.BoxGeometry(x0 + 1.45, H, 0.1), wall, (-1.45 + x0) / 2, H / 2, WZ);
  // door opening in the same wall: x in [DX0, DX1], height DH
  const DX0 = 1.95, DX1 = 2.85, DH = 2.05;
  add(new THREE.BoxGeometry(DX0 - x1, H, 0.1), wall, (x1 + DX0) / 2, H / 2, WZ);
  add(new THREE.BoxGeometry(5.5 - DX1, H, 0.1), wall, (DX1 + 5.5) / 2, H / 2, WZ);
  add(new THREE.BoxGeometry(DX1 - DX0, H - DH, 0.1), wall, (DX0 + DX1) / 2, (H + DH) / 2, WZ);
  add(new THREE.BoxGeometry(x1 - x0, y0, 0.1), wall, (x0 + x1) / 2, y0 / 2, WZ);
  add(new THREE.BoxGeometry(x1 - x0, H - y1, 0.1), wall, (x0 + x1) / 2, (H + y1) / 2, WZ);
  add(new THREE.PlaneGeometry(9, 9), paintMat('ceil', 0xf4f2ee), 1.5, H, 1.5, false).rotation.x = Math.PI / 2;
  // window frame + sill + mullions
  const white = new THREE.MeshPhysicalMaterial({ color: 0xf7f7f5, roughness: 0.35, clearcoat: 0.4 });
  const fr = 0.06;
  add(new THREE.BoxGeometry(x1 - x0 + 2 * fr, fr, 0.16), white, (x0 + x1) / 2, y1 + fr / 2, WZ);
  add(new THREE.BoxGeometry(x1 - x0 + 0.3, 0.04, 0.26), white, (x0 + x1) / 2, y0 - 0.02, WZ + 0.06);
  for (const x of [x0 - fr / 2, x1 + fr / 2, (x0 + x1) / 2]) add(new THREE.BoxGeometry(x === (x0 + x1) / 2 ? 0.035 : fr, y1 - y0, 0.12), white, x, (y0 + y1) / 2, WZ);
  add(new THREE.BoxGeometry(x1 - x0, 0.035, 0.12), white, (x0 + x1) / 2, (y0 + y1) / 2 + 0.15, WZ);
  // door: panelled leaf, casing, lever handle
  {
    const doorMat = withShader(new THREE.MeshPhysicalMaterial({ color: 0xf3efe6, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.4 }), 'door', `
      vec2 q = vec2(vW.x - ${((DX0 + DX1) / 2).toFixed(3)}, vW.y);
      float cx = abs(abs(q.x) - 0.2);
      float p1 = abs(q.y - 1.48), p2 = abs(q.y - 0.6);
      float inX = step(cx, 0.15), in1 = step(p1, 0.45), in2 = step(p2, 0.38);
      float groove = clamp(smoothstep(0.012, 0.0, abs(cx - 0.15)) * (in1 + in2) + (smoothstep(0.012, 0.0, abs(p1 - 0.45)) + smoothstep(0.012, 0.0, abs(p2 - 0.38))) * inX, 0.0, 1.0);
      diffuseColor.rgb *= (1.0 - 0.18 * groove) * (0.97 + 0.04 * vnoise3(vW * 8.0));`, '-groove * 0.002 + vnoise3(vW * 300.0) * 0.00005');
    add(new THREE.BoxGeometry(DX1 - DX0 - 0.02, DH - 0.01, 0.045), doorMat, (DX0 + DX1) / 2, DH / 2, WZ + 0.03);
    const cas = 0.07;
    add(new THREE.BoxGeometry(cas, DH + cas, 0.03), white, DX0 - cas / 2, (DH + cas) / 2, WZ + 0.065);
    add(new THREE.BoxGeometry(cas, DH + cas, 0.03), white, DX1 + cas / 2, (DH + cas) / 2, WZ + 0.065);
    add(new THREE.BoxGeometry(DX1 - DX0 + 2 * cas, cas, 0.03), white, (DX0 + DX1) / 2, DH + cas / 2, WZ + 0.065);
    const brass = new THREE.MeshStandardMaterial({ color: 0xc9a46a, metalness: 1, roughness: 0.25 });
    add(new THREE.CylinderGeometry(0.03, 0.03, 0.02, 24), brass, DX1 - 0.1, 1.0, WZ + 0.06).rotation.x = Math.PI / 2;
    const lever = add(new THREE.CapsuleGeometry(0.011, 0.11, 4, 12), brass, DX1 - 0.15, 1.0, WZ + 0.09); lever.rotation.z = Math.PI / 2;
  }
  // baseboards
  add(new THREE.BoxGeometry(9, 0.1, 0.02), white, 2.4, 0.05, WZ + 0.06, false);
  add(new THREE.BoxGeometry(0.02, 0.1, 9), white, -1.34, 0.05, 2.4, false);

  // bed
  const wood = woodMat('bedwood', 'vec3(0.42, 0.26, 0.15)', 0.5);
  add(new RoundedBoxGeometry(2.25, 0.32, 1.7, 4, 0.03), wood, -0.02, 0.22, 0);                  // frame
  add(new RoundedBoxGeometry(0.08, 1.15, 1.75, 4, 0.03), wood, -1.17, 0.58, 0);                // headboard
  add(new RoundedBoxGeometry(0.06, 0.62, 1.75, 4, 0.025), wood, 1.12, 0.31, 0);                // footboard
  for (const [x, z] of [[-1.1, -0.8], [-1.1, 0.8], [1.08, -0.8], [1.08, 0.8]]) add(new THREE.BoxGeometry(0.07, 0.12, 0.07), wood, x, 0.06, z);
  const sheet = fabricMat('sheet', 0xf3f4f6, 1100, 0.6);
  add(new RoundedBoxGeometry(2.12, 0.24, 1.6, 6, 0.08), sheet, -0.03, MATTRESS_TOP - 0.12, 0);   // mattress in fitted sheet
  // pillows
  const pillowGeo = new THREE.SphereGeometry(1, 64, 32); { const P = pillowGeo.attributes.position; for (let i = 0; i < P.count; i++) { const x = P.getX(i), y = P.getY(i), z = P.getZ(i); const k = Math.pow(Math.abs(x) ** 3 + Math.abs(z) ** 3, 1 / 3) || 1; const sq = 1 / Math.max(k, 0.0001); P.setXYZ(i, x * Math.min(sq, 1.25) * 0.24, y * 0.085, z * Math.min(sq, 1.25) * 0.36); } pillowGeo.computeVertexNormals(); }
  const pillowMat = fabricMat('pillow', 0xffffff, 1200, 0.7);
  add(pillowGeo, pillowMat, -0.88, MATTRESS_TOP + 0.075, -0.36); add(pillowGeo, pillowMat, -0.88, MATTRESS_TOP + 0.075, 0.38).rotation.y = 0.06;
  // nightstand + lamp
  const stand = add(new RoundedBoxGeometry(0.45, 0.55, 0.42, 4, 0.02), woodMat('stand', 'vec3(0.55, 0.36, 0.22)', 0.6), -0.95, 0.275, 1.15);
  add(new THREE.BoxGeometry(0.3, 0.015, 0.012), new THREE.MeshStandardMaterial({ color: 0xc9a46a, metalness: 1, roughness: 0.3 }), -0.95, 0.42, 1.365);
  add(new THREE.CylinderGeometry(0.06, 0.08, 0.04, 32), white, -0.95, 0.57, 1.15);
  add(new THREE.CylinderGeometry(0.012, 0.012, 0.28, 12), new THREE.MeshStandardMaterial({ color: 0xc9a46a, metalness: 1, roughness: 0.3 }), -0.95, 0.71, 1.15);
  const shadeMat = new THREE.MeshPhysicalMaterial({ color: 0xf2e6d0, roughness: 0.8, side: THREE.DoubleSide, emissive: 0xffc988, emissiveIntensity: 0 });
  add(new THREE.CylinderGeometry(0.11, 0.16, 0.2, 48, 1, true), shadeMat, -0.95, 0.9, 1.15);
  // rug
  add(new RoundedBoxGeometry(1.6, 0.012, 2.2, 2, 0.006), fabricMat('rug', 0x8aa6c2, 400, 1.0), 1.85, 0.006, 0.0, false);

  // moon (outside the window, only lit at night)
  const moon = new THREE.Mesh(new THREE.SphereGeometry(4, 32, 16), new THREE.MeshBasicMaterial({ color: 0xf2f4ff }));
  moon.position.set(-6, 22, -60); g.add(moon);
  return { group: g, moon, shadeMat, door: { x: 2.4, z: WZ, x0: 1.95, x1: 2.85 } };
}

// Draped blanket over the sleeper. The grid spans [edge .. foot] along x so the top hem can be pulled
// up over the head (edge -> -1.05); heights follow the body height field (+ head cover), with soft folds,
// hanging side folds and an optional tremble. update() rebuilds positions + normals.
export function makeBlanket(bodyH = null) {
  const nx = 240, nz = 150, X1 = 1.12, Z0 = -1.02, Z1 = 1.02;
  const geo = new THREE.PlaneGeometry(1, Z1 - Z0, nx, nz); geo.rotateX(-Math.PI / 2);
  const P = geo.attributes.position, N = P.count;
  const gu = new Float32Array(N), gz = new Float32Array(N);
  for (let i = 0; i < N; i++) { gu[i] = P.getX(i) + 0.5; gz[i] = P.getZ(i); }   // u: 0 = edge, 1 = foot
  const HEAD = { x: -0.86, z: -0.02 };
  const head = (x, z, k) => k <= 0 ? 0 : k * 0.2 * Math.exp(-(((x - HEAD.x) / 0.16) ** 2) - (((z - HEAD.z) / 0.13) ** 2));
  const shoulders = (x, z, k) => k <= 0 ? 0 : k * 0.16 * Math.exp(-(((x + 0.55) / 0.18) ** 2) - ((z / 0.26) ** 4));
  let lastKey = '';
  function update(o = {}) {
    const { edge = -0.36, cover = 0, tremble = 0, t = 0, lift = 0, hf = null } = o;
    const key = [edge, cover, tremble, tremble ? t : 0, lift, hf ? 1 : 0].map(x => +(+x).toFixed(4)).join(','); if (key === lastKey) return; lastKey = key;
    const BH = hf || bodyH;
    for (let i = 0; i < N; i++) {
      const x = edge + (X1 - edge) * gu[i], z = gz[i];
      let h = MATTRESS_TOP + 0.02;
      if (BH) h = Math.max(h, BH(x, z) + 0.06);
      h = Math.max(h, MATTRESS_TOP + 0.075 + head(x, z, cover) + (x < -0.66 ? 0.09 * cover : 0), MATTRESS_TOP + 0.02 + shoulders(x, z, cover));
      // pillow under the head end
      if (x < -0.62) h = Math.max(h, MATTRESS_TOP + 0.16 * Math.exp(-((Math.abs(z) > 0.0 ? ((Math.abs(z) - 0.37) / 0.4) : 0) ** 4)) * Math.min(1, (-0.62 - x) / 0.12));
      // drape over side and foot edges, hanging folds
      const over = Math.max(0, Math.abs(z) - 0.8), overX = Math.max(0, x - 1.05);
      h -= Math.min(0.44, (over * 4.0) ** 1.4 * 0.5) + Math.min(0.42, (overX * 6.0) ** 1.2 * 0.5);
      const hang = Math.min(1, over * 6 + overX * 8);
      let zz = Math.abs(z) > 0.8 ? Math.sign(z) * (0.81 + (Math.abs(z) - 0.8) * 0.12) : z;
      let xx = x > 1.05 ? 1.06 + (x - 1.05) * 0.1 : x;
      const fold = Math.sin(x * 15 + 1.3 * Math.sin(z * 4)) * 0.6 + Math.sin(x * 7.3 - z * 3.1) * 0.4;
      zz += Math.sign(z) * hang * 0.028 * fold; xx += hang * 0.02 * Math.sin(z * 17);
      // soft folds on top (diagonal wrinkles radiating from the body), quilt puff
      const top = 1 - hang;
      h += top * (0.011 * Math.sin(x * 19 + Math.sin(z * 8) * 2.2) * (0.5 + 0.5 * Math.sin(z * 6.0 + x * 2)) + 0.007 * Math.sin(z * 27 + x * 9) + 0.006 * Math.sin((x + z) * 11));
      h += top * 0.006 * (Math.cos(x * 25.13) * Math.cos(z * 25.13));
      // turned-down hem near the edge
      const eu = gu[i] * (X1 - edge);
      h += 0.018 * Math.exp(-(((eu - 0.05) / 0.035) ** 2));
      if (tremble > 0) h += tremble * 0.007 * Math.sin(t * 47 + x * 21 + z * 13) * Math.exp(-(((x + 0.5) / 0.6) ** 2));
      h += lift * Math.exp(-(((x + 0.2) / 0.5) ** 2)) * 0.05;
      P.setXYZ(i, xx, h, zz);
    }
    P.needsUpdate = true; geo.computeVertexNormals(); geo.computeBoundingSphere();
  }
  update();
  const mat = new THREE.MeshPhysicalMaterial({ color: 0x9fbad3, roughness: 0.9, sheen: 1, sheenRoughness: 0.5, sheenColor: new THREE.Color(0.85, 0.9, 1.0), side: THREE.DoubleSide });
  withShader(mat, 'blanket', `float q = sin(vW.x * 1300.0) * sin(vW.z * 1300.0);
    float quilt = smoothstep(0.004, 0.0, abs(fract(vW.x * 4.0) - 0.5) - 0.49) + smoothstep(0.004, 0.0, abs(fract(vW.z * 4.0) - 0.5) - 0.49);
    diffuseColor.rgb *= (0.95 + 0.05 * q) * (1.0 - 0.18 * quilt) * (0.96 + 0.06 * vnoise3(vW * 12.0));`, 'q * 0.0001 - quilt * 0.002 + vnoise3(vW * 30.0) * 0.0008');
  const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true;
  m.update = update;
  return m;
}
