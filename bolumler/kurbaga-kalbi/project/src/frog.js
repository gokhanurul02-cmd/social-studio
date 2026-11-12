// Procedural leopard frog (SDF -> surface nets): wet glossy skin, dark ringed spots, cream belly, warts,
// gold eyes with horizontal pupils. Units: centimetres (scale the group by 0.01 for metres).
// Poses: 'sit' (natural) and 'splay' (dissection, legs spread; flip the group to show the belly).
import * as THREE from 'three';
import { smin, smax, ellipsoid, sphere, chain, polygonize } from './sdf.js';
import { BUMP_GLSL } from './mosquito.js';

function legs(x, y, z, pose, s) {
  let d = 1e9;
  const P = (a, b, c) => [s * a, b, c];
  if (pose === 'sit') {
    d = Math.min(d, chain(x, y, z, [P(1.4, 1.6, 1.3), P(2.15, 0.75, 1.55), P(1.85, 0.3, 2.85)], [0.6, 0.4, 0.3], 0.3));
    for (const [dx, dz] of [[-0.55, 0.75], [-0.1, 0.95], [0.35, 0.85], [0.75, 0.5]]) d = smin(d, chain(x, y, z, [P(1.85, 0.3, 2.85), P(1.85 + dx * 0.6, 0.18, 2.85 + dz * 0.6), P(1.85 + dx, 0.14, 2.85 + dz)], [0.2, 0.12, 0.16], 0.12), 0.15);
    d = smin(d, chain(x, y, z, [P(1.5, 1.4, -2.3), P(3.15, 1.25, -0.5), P(2.25, 0.5, -3.1)], [0.95, 0.62, 0.38]), 0.6);
    d = smin(d, chain(x, y, z, [P(2.25, 0.5, -3.1), P(3.25, 0.25, -1.3)], [0.36, 0.24]), 0.2);
    for (const [dx, dz, L] of [[-0.6, 1, 1.3], [-0.15, 1, 1.7], [0.35, 1, 2.1], [0.8, 0.9, 1.6], [1.15, 0.5, 1.1]]) {
      const n = Math.hypot(dx, dz);
      d = smin(d, chain(x, y, z, [P(3.25, 0.25, -1.3), P(3.25 + dx / n * L, 0.13, -1.3 + dz / n * L)], [0.18, 0.11]), 0.25);
    }
  } else {
    d = Math.min(d, chain(x, y, z, [P(1.4, 2.0, 1.3), P(3.0, 2.85, 2.4), P(3.6, 3.1, 3.6)], [0.6, 0.4, 0.3], 0.3));
    for (const [dx, dz] of [[-0.3, 1.0], [0.25, 1.0], [0.75, 0.7], [1.0, 0.15]]) d = smin(d, chain(x, y, z, [P(3.6, 3.1, 3.6), P(3.6 + dx, 3.15, 3.6 + dz)], [0.2, 0.13]), 0.15);
    d = smin(d, chain(x, y, z, [P(1.5, 1.9, -2.3), P(4.1, 2.8, -4.0), P(4.9, 3.1, -7.0), P(5.4, 3.15, -8.6)], [0.95, 0.62, 0.36, 0.25]), 0.6);
    for (const [dx, dz, L] of [[-0.35, -1, 1.4], [0.0, -1, 1.9], [0.35, -1, 2.3], [0.7, -0.9, 1.8], [1.0, -0.5, 1.2]]) {
      const n = Math.hypot(dx, dz);
      d = smin(d, chain(x, y, z, [P(5.4, 3.15, -8.6), P(5.4 + dx / n * L, 3.2, -8.6 + dz / n * L)], [0.18, 0.11]), 0.25);
    }
  }
  return d;
}

export function frogSDF(pose, incision = false) {
  const tilt = pose === 'sit' ? -0.3 : 0.0, ct = Math.cos(tilt), st = Math.sin(tilt);
  return (x, y, z) => {
    // body (pitched up at the front when sitting)
    const by = 1.9, bz = -0.6; const ry = (y - by) * ct - (z - bz) * st + by, rz = (y - by) * st + (z - bz) * ct + bz;
    let d = ellipsoid(x, ry, rz, 0, 1.9, -0.6, 2.25, 1.45, 3.0);
    const hy = pose === 'sit' ? 2.55 : 2.05;
    d = smin(d, ellipsoid(x, y, z, 0, hy, 2.0, 2.1, 1.2, 1.9), 1.1);
    d = smin(d, ellipsoid(x, y, z, 0, hy - 0.35, 3.3, 1.5, 0.78, 1.05), 0.6);
    d = smin(d, ellipsoid(x, y, z, 0, 1.25 + (hy - 2.05) * 0.5, 0.8, 1.75, 0.9, 2.1), 0.8);
    for (const s of [-1, 1]) d = smin(d, sphere(x, y, z, s * 1.22, hy + 0.78, 2.25, 0.7), 0.45);
    d = smin(d, legs(x, y, z, pose, 1), 0.35); d = smin(d, legs(x, y, z, pose, -1), 0.35);
    // mouth groove
    d = smax(d, -ellipsoid(x, y, z, 0, hy - 0.62, 3.0, 1.7, 0.05, 1.5), 0.05);
    if (incision) d = smax(d, -ellipsoid(x, y, z, 0, 3.45, 0.2, 0.8, 0.75, 1.15), 0.12);
    return d;
  };
}

export const FROG_EYES = pose => { const hy = pose === 'sit' ? 2.55 : 2.05; return [[-1.22, hy + 0.78, 2.25], [1.22, hy + 0.78, 2.25]]; };

export function frogMaterial() {
  const u = { uFrost: { value: 0 }, uWet: { value: 1 }, uInc: { value: 0 } };
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.38, clearcoat: 1, clearcoatRoughness: 0.06, sheen: 0.3, sheenColor: new THREE.Color(0.6, 0.9, 0.5), specularIntensity: 0.8 });
  m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vON;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position; vON = normal;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vON; uniform float uFrost, uWet, uInc;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float fr, _H;
        { vec3 p = vO;
        float dors = smoothstep(-0.35, 0.25, vON.y + 0.25 * smoothstep(1.2, 2.5, p.y));
        float n1 = vnoise3(p * 1.3), n2 = vnoise3(p * 4.0), n3 = vnoise3(p * 11.0);
        vec3 green = mix(vec3(0.06, 0.2, 0.025), vec3(0.22, 0.38, 0.06), n1) * (0.8 + 0.3 * n2) * (0.9 + 0.2 * n3);
        green = mix(green, vec3(0.16, 0.2, 0.05), smoothstep(0.55, 0.8, vnoise3(p * 0.7 + 9.0)) * 0.5);
        green = mix(green, vec3(0.30, 0.42, 0.07), smoothstep(2.2, 3.4, p.z) * 0.45);
        vec2 v = voro3(p * vec3(1.35, 1.35, 1.1) + 3.0 + 0.35 * vec3(n2));
        float rad = 0.1 + 0.16 * _h3(floor(p * vec3(1.35, 1.35, 1.1) + 3.0)).y;
        float spot = 1.0 - smoothstep(rad - 0.03, rad + 0.02, v.x);
        float rim = (1.0 - smoothstep(rad + 0.03, rad + 0.1, v.x)) * (1.0 - spot);
        vec3 back = mix(green, vec3(0.03, 0.055, 0.015), spot * 0.92);
        back = mix(back, green * 1.45 + vec3(0.04, 0.05, 0.0), rim * 0.6);
        vec3 belly = vec3(0.78, 0.72, 0.48) * (0.85 + 0.2 * n2) * (0.9 + 0.1 * n3);
        belly = mix(belly, vec3(0.62, 0.62, 0.35), smoothstep(0.4, 0.8, n1) * 0.3);
        vec3 col = mix(belly, back, dors);
        // pale lip stripe and dark tympanum
        col = mix(col, vec3(0.75, 0.75, 0.45), smoothstep(0.08, 0.0, abs(p.y - 1.95 - 0.04 * p.z)) * smoothstep(1.5, 2.6, p.z) * step(1.0, abs(p.x)) * 0.6);
        float inc = uInc * (1.0 - smoothstep(0.0, 0.25, length((p - vec3(0.0, 3.3, 0.2)) / vec3(0.9, 0.85, 1.3)) - 0.9));
        col = mix(col, vec3(0.28, 0.02, 0.02) * (0.7 + 0.5 * n3), inc);
        // frost: white-blue rime, rough
        fr = uFrost * smoothstep(0.2, 0.8, n2 * 0.6 + n3 * 0.5 + uFrost * 0.6);
        col = mix(col, vec3(0.80, 0.88, 0.96) * (0.85 + 0.3 * n3), fr);
        diffuseColor.rgb = col;
        _H = (vnoise3(p * 7.0) * 0.6 + (1.0 - v.x) * 0.25 * dors) * 0.00025 + fr * vnoise3(p * 30.0) * 0.0004; }`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.85, fr);')
      .replace('#include <lights_physical_fragment>', '#include <lights_physical_fragment>\nmaterial.clearcoat *= (1.0 - fr) * uWet;');
  };
  m.customProgramCacheKey = () => 'frog-skin';
  return m;
}

export function eyeMaterial() {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.02 });
  const u = { uFrost: { value: 0 } }; m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; uniform float uFrost;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 q = normalize(vO);
        float iris = smoothstep(0.25, 0.35, q.z);
        float pup = 1.0 - smoothstep(0.9, 1.05, length(vec2(q.x / 0.42, q.y / 0.2)));
        vec3 gold = mix(vec3(0.55, 0.36, 0.05), vec3(0.85, 0.65, 0.2), vnoise3(vO * 9.0)) * (0.7 + 0.4 * vnoise3(vO * 25.0));
        vec3 col = mix(vec3(0.08, 0.1, 0.03), gold, iris);
        col = mix(col, vec3(0.005), pup * iris);
        col = mix(col, vec3(0.75, 0.82, 0.9), uFrost * 0.5);
        diffuseColor.rgb = col;`);
  };
  m.customProgramCacheKey = () => 'frog-eye';
  return m;
}

export function buildFrog(pose, { incision = false, res = 0.075 } = {}) {
  const g = new THREE.Group();
  const box = pose === 'sit' ? [[-5.2, -0.4, -4.6], [5.2, 4.4, 4.9]] : [[-7.6, -0.4, -11.3], [7.6, 4.0, 5.2]];
  const geo = polygonize(frogSDF(pose, incision), box[0], box[1], res);
  const mat = frogMaterial(); mat.userData.u.uInc.value = incision ? 1 : 0;
  const body = new THREE.Mesh(geo, mat); body.castShadow = true; body.receiveShadow = true; g.add(body);
  const em = eyeMaterial();
  const eyes = [];
  for (const [x, y, z] of FROG_EYES(pose)) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.6, 40, 28), em);
    e.position.set(x * 1.06, y + 0.12, z + 0.05);
    e.lookAt(e.position.clone().add(new THREE.Vector3(Math.sign(x) * 0.85, 0.3, 0.55)));
    e.castShadow = true; g.add(e); eyes.push(e);
  }
  return { group: g, body, mat, eyeMat: em, eyes, geo };
}
