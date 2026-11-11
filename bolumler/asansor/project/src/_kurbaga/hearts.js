// Frog hearts (SDF): small glossy heart (single ventricle, two atria, truncus arteriosus), an instanced
// swarm of beating hearts, and a three-chamber cutaway with red/blue blood mixing in the ventricle.
// Units: centimetres (heart ~1.4 cm tall).
import * as THREE from 'three';
import { smin, smax, ellipsoid, sphere, cone, chain, polygonize } from './sdf.js';
import { BUMP_GLSL } from './mosquito.js';
import { mulberry } from './util.js';

function heartOuter(x, y, z) {
  let d = ellipsoid(x, y, z, 0, -0.12, 0, 0.5, 0.58, 0.44);
  d = smin(d, cone(x, y, z, [0, -0.2, 0], [0.03, -0.72, 0.02], 0.36, 0.06), 0.25);
  d = smin(d, ellipsoid(x, y, z, -0.33, 0.42, -0.05, 0.36, 0.3, 0.33), 0.16);
  d = smin(d, ellipsoid(x, y, z, 0.32, 0.43, -0.07, 0.33, 0.28, 0.31), 0.16);
  d = smin(d, chain(x, y, z, [[0.05, 0.05, 0.28], [0.05, 0.55, 0.3], [0.08, 0.85, 0.15]], [0.15, 0.14, 0.13]), 0.1);
  for (const s of [-1, 1]) d = smin(d, chain(x, y, z, [[0.08, 0.85, 0.15], [s * 0.35, 1.0, 0.05], [s * 0.6, 0.95, -0.05]], [0.12, 0.09, 0.08]), 0.06);
  d = smin(d, chain(x, y, z, [[-0.4, 0.55, -0.15], [-0.55, 0.85, -0.25]], [0.12, 0.09]), 0.06);
  return d;
}
let HEART_GEO = null;
export function heartGeometry() {
  if (!HEART_GEO) HEART_GEO = polygonize(heartOuter, [-0.85, -0.85, -0.6], [0.85, 1.15, 0.6], 0.028);
  return HEART_GEO;
}

export function heartMaterial() {
  const u = { uIce: { value: 0 }, uGlow: { value: 0 } };
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.08, sheen: 0.5, sheenColor: new THREE.Color(1, 0.5, 0.5) });
  m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; uniform float uIce, uGlow;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float _H;
        { vec3 p = vO * 4.0;
          vec2 v = voro3(p * 1.3 + 2.0);
          float vein = 1.0 - smoothstep(0.0, 0.07, v.y - v.x);
          float n = vnoise3(p * 2.0), n2 = vnoise3(p * 8.0);
          vec3 col = mix(vec3(0.42, 0.02, 0.025), vec3(0.62, 0.06, 0.05), n) * (0.85 + 0.25 * n2);
          col = mix(col, vec3(0.16, 0.02, 0.06), vein * 0.75 * smoothstep(-0.6, 0.2, vO.y));
          col = mix(col, vec3(0.55, 0.12, 0.10), smoothstep(0.5, 0.9, vO.y) * 0.5);
          col = mix(col, vec3(0.6, 0.78, 0.95) * (0.8 + 0.3 * n2), uIce * 0.85);
          diffuseColor.rgb = col;
          _H = (n2 * 0.6 - vein * 0.5) * 0.00006; }`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.08, 0.05) * uGlow;');
  };
  m.customProgramCacheKey = () => 'frog-heart';
  return m;
}

// glowing red heart for x-ray scenes (additive fresnel)
export function heartXrayMaterial(col = 0xff2a1a) {
  const m = new THREE.MeshBasicMaterial({ color: 0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const u = { uCol: { value: new THREE.Color(col) }, uK: { value: 1 } }; m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vN2; varying vec3 vV2;')
      .replace('#include <project_vertex>', `#include <project_vertex>\nvec3 nn = normal;
#ifdef USE_INSTANCING
nn = mat3(instanceMatrix) * nn;
#endif
vN2 = normalize(normalMatrix * nn); vV2 = -mvPosition.xyz;`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vN2; varying vec3 vV2; uniform vec3 uCol; uniform float uK;')
      .replace('#include <dithering_fragment>', '#include <dithering_fragment>\n{ float f = 1.0 - abs(dot(normalize(vN2), normalize(vV2))); gl_FragColor = vec4(uCol * (0.35 + 1.6 * pow(f, 1.6)) * uK, 1.0); }');
  };
  m.customProgramCacheKey = () => 'heart-xray';
  return m;
}

// beat curve: quick double thump per cycle (0..1 scale add)
export function beat(ph) { const f = ph - Math.floor(ph); return Math.exp(-Math.pow((f - 0.08) / 0.05, 2)) * 0.9 + Math.exp(-Math.pow((f - 0.28) / 0.06, 2)) * 0.5; }

export class HeartSwarm {
  constructor(n, mat, seed = 5) {
    this.n = n; this.mesh = new THREE.InstancedMesh(heartGeometry(), mat, n);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true; this.mesh.frustumCulled = false;
    const r = mulberry(seed);
    this.ph = Array.from({ length: n }, () => r()); this.rate = Array.from({ length: n }, () => 1.6 + 1.4 * r());
    this.rot = Array.from({ length: n }, () => new THREE.Quaternion().setFromEuler(new THREE.Euler((r() - 0.5) * 1.6, r() * 6.28, (r() - 0.5) * 1.6)));
    this.rnd = Array.from({ length: n }, () => [r(), r(), r(), r()]);
    this.m4 = new THREE.Matrix4(); this.s = new THREE.Vector3();
  }
  set(i, pos, scale, t, q = null, amp = 0.16) {
    const b = 1 + amp * beat(t * this.rate[i] + this.ph[i]);
    this.s.set(scale * b, scale * (1 + (b - 1) * 0.7), scale * b);
    this.m4.compose(pos, q || this.rot[i], this.s); this.mesh.setMatrixAt(i, this.m4);
  }
  hide(i) { this.m4.makeScale(0, 0, 0); this.mesh.setMatrixAt(i, this.m4); }
  done(count = this.n) { this.mesh.count = count; this.mesh.instanceMatrix.needsUpdate = true; }
}

// ---------------------------------------------------------------- three-chamber cutaway
const CH = { RA: [-0.3, 0.42, 0.25, 0.2], LA: [0.3, 0.43, 0.23, 0.19], V: [0.0, -0.15, 0.3, 0.38] };   // x, y, rx, ry (slice at the cut)
function cutSDF(x, y, z) {
  const S = 1.6; x /= S; y /= S; z /= S;
  let d = heartOuter(x, y, z);
  d = smax(d, z - 0.0, 0.01);
  let cav = ellipsoid(x, y, z, -0.3, 0.42, 0.0, 0.25, 0.2, 0.22);
  cav = Math.min(cav, ellipsoid(x, y, z, 0.3, 0.43, 0.0, 0.23, 0.19, 0.2));
  cav = Math.min(cav, ellipsoid(x, y, z, 0.0, -0.15, 0.0, 0.3, 0.38, 0.27));
  cav = smin(cav, cone(x, y, z, [-0.22, 0.32, 0], [-0.1, 0.1, 0], 0.08, 0.07), 0.05);
  cav = smin(cav, cone(x, y, z, [0.22, 0.32, 0], [0.1, 0.1, 0], 0.08, 0.07), 0.05);
  cav = smin(cav, cone(x, y, z, [0.03, 0.05, 0.0], [0.06, 0.8, 0.08], 0.07, 0.07), 0.05);
  d = smax(d, -cav, 0.03);
  return d * S;
}
export function buildCutaway() {
  const g = new THREE.Group();
  const geo = polygonize(cutSDF, [-1.4, -1.35, -1.0], [1.4, 1.8, 0.06], 0.02);
  const u = { uT: { value: 0 } };
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.35, clearcoat: 0.8, clearcoatRoughness: 0.12, sheen: 0.4, sheenColor: new THREE.Color(1, 0.6, 0.6), side: THREE.DoubleSide });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vON;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position; vON = normal;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vON;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float _H;
        { vec3 p = vO * 3.0; float n = vnoise3(p * 3.0), n2 = vnoise3(p * 12.0);
          float cutF = smoothstep(-0.03, -0.005, vO.z) * smoothstep(0.6, 0.9, vON.z);
          vec2 v = voro3(p * 2.0);
          float vein = 1.0 - smoothstep(0.0, 0.06, v.y - v.x);
          vec3 outer = mix(vec3(0.42, 0.02, 0.025), vec3(0.62, 0.06, 0.05), n) * (0.85 + 0.25 * n2);
          outer = mix(outer, vec3(0.16, 0.02, 0.06), vein * 0.7);
          float fib = 0.5 + 0.5 * sin(vO.x * 60.0 + vO.y * 25.0 + n * 6.0);
          vec3 cut = mix(vec3(0.72, 0.22, 0.22), vec3(0.85, 0.36, 0.34), fib * 0.6 + n2 * 0.3);
          diffuseColor.rgb = mix(outer, cut, cutF);
          _H = (n2 * 0.5 + fib * 0.3 * cutF) * 0.00025; }`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
  };
  m.customProgramCacheKey = () => 'heart-cut';
  const mesh = new THREE.Mesh(geo, m); mesh.castShadow = true; mesh.receiveShadow = true; g.add(mesh);
  // blood inside the chambers, seen through the cut (z slightly behind the cut plane)
  const S = 1.6, bu = { uT: { value: 0 }, uMix: { value: 0 }, uHi: { value: new THREE.Vector3() }, uFlow: { value: 1 } };
  const bm = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.03 });
  bm.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, bu);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; uniform float uT, uMix, uFlow; uniform vec3 uHi;\n' + BUMP_GLSL + `
      float ell(vec2 p, vec4 e){ return length((p - e.xy) / e.zw); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 _E;
        { vec2 p = vO.xy / ${S.toFixed(2)};
          float ra = ell(p, vec4(${CH.RA.join(',')})), la = ell(p, vec4(${CH.LA.join(',')})), ve = ell(p, vec4(${CH.V.join(',')}));
          float av1 = length((p - vec2(-0.16, 0.22)) / vec2(0.09, 0.14)), av2 = length((p - vec2(0.16, 0.22)) / vec2(0.09, 0.14));
          float tr = length((p - vec2(0.05, 0.45)) / vec2(0.07, 0.4));
          float inside = min(min(min(ra, la), min(ve, av1)), min(av2, tr));
          if (inside > 1.02) discard;
          vec3 red = vec3(0.65, 0.01, 0.015), blue = vec3(0.06, 0.08, 0.42), purple = vec3(0.32, 0.03, 0.26);
          vec2 q = p * 6.0; float tt = uT * uFlow;
          float sw = vnoise3(vec3(q.x + 1.5 * sin(q.y * 0.8 + tt * 1.3), q.y - tt * 1.6, tt * 0.4)) ;
          float sw2 = vnoise3(vec3(q * 2.3 + vec2(tt, -tt * 1.2), tt * 0.7));
          float side = smoothstep(-0.25, 0.25, p.x + 0.35 * (sw - 0.5) + 0.2 * (sw2 - 0.5));
          vec3 vcol = mix(mix(blue, red, side), purple, uMix * smoothstep(0.15, 0.85, 1.0 - abs(side - 0.5) * 2.0 + uMix * 0.6));
          vec3 col = ra < 1.0 || av1 < 1.0 && p.x < -0.1 ? blue : la < 1.0 || av2 < 1.0 && p.x > 0.1 ? red : vcol;
          col *= 0.75 + 0.5 * sw2;
          _E = col * 0.35 + vec3(1.0, 0.35, 0.3) * (uHi.x * step(ra, 1.0) + uHi.y * step(la, 1.0) + uHi.z * step(ve, 1.0)) * 0.5;
          diffuseColor.rgb = col; }`)
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += _E;');
  };
  bm.customProgramCacheKey = () => 'heart-blood';
  const blood = new THREE.Mesh(new THREE.PlaneGeometry(3, 3.4), bm); blood.position.set(0, 0.2, -0.12); g.add(blood);
  // flowing particles: blue from the right atrium, red from the left, merging (purple) in the ventricle
  const NP = 70, pm = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 14, 10), new THREE.MeshPhysicalMaterial({ roughness: 0.15, clearcoat: 1 }), NP);
  pm.castShadow = false; g.add(pm);
  const r = mulberry(31);
  const pathA = new THREE.CatmullRomCurve3([[-0.42, 0.5], [-0.28, 0.4], [-0.16, 0.22], [-0.08, -0.05], [-0.05, -0.3], [0.02, -0.15], [0.05, 0.2], [0.07, 0.7], [0.1, 1.2]].map(([x, y]) => new THREE.Vector3(x * S, y * S, -0.07)));
  const pathB = new THREE.CatmullRomCurve3([[0.42, 0.5], [0.28, 0.4], [0.16, 0.22], [0.08, -0.05], [0.05, -0.3], [0.0, -0.15], [0.04, 0.2], [0.07, 0.7], [0.1, 1.2]].map(([x, y]) => new THREE.Vector3(x * S, y * S, -0.07)));
  const prt = Array.from({ length: NP }, (_, i) => ({ ph: r(), side: i % 2, off: [(r() - 0.5) * 0.12, (r() - 0.5) * 0.12], s: 0.035 + 0.03 * r() }));
  const m4 = new THREE.Matrix4(), c = new THREE.Color(), cR = new THREE.Color(0.75, 0.02, 0.02), cB = new THREE.Color(0.08, 0.1, 0.55), cP = new THREE.Color(0.45, 0.04, 0.38);
  function update(t, { mix = 0, hi = [0, 0, 0], flow = 1, particles = 1 } = {}) {
    bu.uT.value = t; bu.uMix.value = mix; bu.uHi.value.set(...hi); bu.uFlow.value = flow;
    pm.visible = particles > 0.01;
    prt.forEach((q, i) => {
      const u = (q.ph + t * 0.28 * flow) % 1, P = (q.side ? pathB : pathA).getPointAt(u);
      const k = particles * Math.min(1, u * 8) * Math.min(1, (1 - u) * 8);
      m4.makeScale(q.s * k, q.s * k, q.s * 0.5 * k).setPosition(P.x + q.off[0], P.y + q.off[1], P.z); pm.setMatrixAt(i, m4);
      const mixU = THREE.MathUtils.smoothstep(u, 0.35, 0.6) * mix;
      c.copy(q.side ? cR : cB).lerp(cP, mixU); pm.setColorAt(i, c);
    });
    pm.instanceMatrix.needsUpdate = true; if (pm.instanceColor) pm.instanceColor.needsUpdate = true;
  }
  update(0);
  return { group: g, mesh, blood, update };
}
