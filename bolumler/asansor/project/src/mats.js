// Procedural PBR materials (no external textures): brushed stainless, painted / galvanised steel, machined steel,
// concrete, granite floor, steel wire rope (helical strands + wires), plus a parallel-transport tube that can be
// re-shaped every frame (ropes, wires).
import * as THREE from 'three';
import { BUMP_GLSL } from './mosquito.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

// inject object-space procedural colour / roughness / metalness / height into a standard material
// GLSL snippets see: vO (object position), vNo (object normal), vRU (custom 'rope' attribute or uv), _H (height out)
export function proc(mat, key, { pars = '', color = '', rough = '', metal = '', height = '', ropeAttr = false, uniforms = null } = {}) {
  mat.onBeforeCompile = sh => {
    if (uniforms) Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>\nvarying vec3 vO; varying vec3 vNo; varying vec2 vRU;${ropeAttr ? '\nattribute vec2 rope;' : ''}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\nvO = position; vNo = normal; vRU = ${ropeAttr ? 'rope' : 'vec2(0.0)'};`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; varying vec3 vNo; varying vec2 vRU;\n' + BUMP_GLSL + pars)
      .replace('#include <color_fragment>', '#include <color_fragment>\nfloat _H = 0.0;\n' + color + '\n' + height)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n' + rough)
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\n' + metal)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
  };
  mat.customProgramCacheKey = () => key;
  if (uniforms) mat.userData.u = uniforms;
  return mat;
}

// ------------------------------------------------------------------ brushed stainless (canvas grain texture)
let GRAIN = null;
function grainTex() {
  if (GRAIN) return GRAIN;
  const S = 1024, c = document.createElement('canvas'); c.width = c.height = S; const g = c.getContext('2d');
  g.fillStyle = 'rgb(128,128,128)'; g.fillRect(0, 0, S, S);
  const r = mulberry(7);
  for (let i = 0; i < 9000; i++) {
    const y = r() * S, len = 60 + r() * 900, x = r() * S, v = Math.floor(90 + r() * 80), a = 0.05 + r() * 0.25;
    g.strokeStyle = `rgba(${v},${v},${v},${a})`; g.lineWidth = 0.5 + r() * 1.3;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + len, y + (r() - 0.5) * 1.2); g.stroke();
    if (x + len > S) { g.beginPath(); g.moveTo(x - S, y); g.lineTo(x + len - S, y); g.stroke(); }
  }
  // a few long blotches (handling marks)
  for (let i = 0; i < 40; i++) { const x = r() * S, y = r() * S; const gr = g.createRadialGradient(x, y, 0, x, y, 40 + r() * 120);
    gr.addColorStop(0, `rgba(${r() > 0.5 ? 170 : 95},128,128,0.10)`); gr.addColorStop(1, 'rgba(128,128,128,0)'); g.fillStyle = gr; g.fillRect(0, 0, S, S); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; t.colorSpace = THREE.NoColorSpace;
  GRAIN = t; return t;
}
export function brushedSteel({ color = 0xc9ccd0, rough = 0.32, repeat = [2, 2], rot = 0, aniso = 0.75, env = 1.0 } = {}) {
  const tex = grainTex().clone(); tex.needsUpdate = true; tex.repeat.set(...repeat); tex.rotation = rot;
  const m = new THREE.MeshPhysicalMaterial({ color, metalness: 1.0, roughness: rough, roughnessMap: tex, bumpMap: tex, bumpScale: 0.6,
    anisotropy: aniso, anisotropyRotation: rot, envMapIntensity: env, clearcoat: 0.0 });
  return m;
}

// ------------------------------------------------------------------ painted steel / galvanised / machined
export function paintedSteel(color = 0x5d6670, { rough = 0.48, wear = 0.25, key = 'paint' } = {}) {
  const m = new THREE.MeshPhysicalMaterial({ color, metalness: 0.15, roughness: rough, clearcoat: 0.25, clearcoatRoughness: 0.35 });
  return proc(m, key + wear, {
    color: `{ float n = vnoise3(vO * 9.0) * 0.6 + vnoise3(vO * 41.0) * 0.4; float sc = smoothstep(0.78, 0.86, vnoise3(vO * 23.0 + 3.1)) * ${wear.toFixed(3)};
      diffuseColor.rgb *= 0.9 + 0.16 * n; diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.42, 0.42, 0.43), sc); _H = n * 0.0004 - sc * 0.0003; }`,
    rough: 'roughnessFactor = clamp(roughnessFactor + 0.12 * (vnoise3(vO * 17.0) - 0.5), 0.05, 1.0);',
  });
}
export function galvanised(color = 0xa7acb2) {
  const m = new THREE.MeshStandardMaterial({ color, metalness: 0.9, roughness: 0.42 });
  return proc(m, 'galv', {
    color: `{ vec2 v = voro3(vO * 26.0); float sp = fract(sin(dot(floor(vO * 26.0), vec3(12.9, 78.2, 37.7))) * 4375.5);
      diffuseColor.rgb *= 0.86 + 0.2 * smoothstep(0.0, 0.12, v.y - v.x) * (0.6 + 0.4 * vnoise3(vO * 26.0 + 9.0)); _H = (v.y - v.x) * 0.0003; }`,
    rough: 'roughnessFactor = 0.3 + 0.25 * vnoise3(vO * 26.0 + 4.0);',
  });
}
export function machinedSteel(color = 0xb9bdc2, rough = 0.22) {
  const m = new THREE.MeshPhysicalMaterial({ color, metalness: 1.0, roughness: rough, clearcoat: 0.1 });
  return proc(m, 'mach' + rough, {
    color: `{ float n = vnoise3(vO * vec3(4.0, 220.0, 4.0)); diffuseColor.rgb *= 0.92 + 0.12 * n; _H = n * 0.00003; }`,
    rough: 'roughnessFactor = clamp(roughnessFactor + 0.15 * (vnoise3(vO * 30.0) - 0.4), 0.05, 1.0);',
  });
}
export function blackGloss(color = 0x050505, rough = 0.08) { return new THREE.MeshPhysicalMaterial({ color, metalness: 0.0, roughness: rough, clearcoat: 1.0, clearcoatRoughness: 0.03 }); }
export function rubber(color = 0x161616) {
  return proc(new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0 }), 'rubber', { color: '{ float n = vnoise3(vO * 120.0); diffuseColor.rgb *= 0.85 + 0.25 * n; _H = n * 0.00006; }' });
}

// ------------------------------------------------------------------ concrete (formwork panels, tie holes, stains)
export function concrete(color = 0x9b9890, { scale = 1, key = 'concrete', cut = false } = {}) {
  const m = new THREE.MeshStandardMaterial({ color, roughness: 0.92, metalness: 0 });
  return proc(m, key, {
    pars: `float fbm3(vec3 p){ float s=0., a=.5; for(int i=0;i<5;i++){ s+=a*vnoise3(p); p=p*2.03+7.1; a*=.5; } return s; }`,
    color: `{ vec3 P = vO * ${scale.toFixed(3)}; vec3 an = abs(normalize(vNo));
      vec2 q = an.x > 0.5 ? P.zy : (an.y > 0.5 ? P.xz : P.xy);
      float n = fbm3(P * 3.0), f = fbm3(P * 18.0), s = fbm3(P * 0.6 + 4.0);
      vec2 pnl = abs(fract(q / vec2(1.2, 0.6) + 0.5) - 0.5) * vec2(1.2, 0.6);
      float seam = ${cut ? '0.0' : '1.0 - smoothstep(0.004, 0.012, min(pnl.x, pnl.y))'};
      vec2 th = abs(fract(q / vec2(0.6, 0.6) + vec2(0.0, 0.0)) - 0.5) * 0.6; float tie = ${cut ? '0.0' : '1.0 - smoothstep(0.010, 0.016, length(th))'};
      float pore = smoothstep(0.62, 0.7, vnoise3(P * 70.0)) * 0.5;
      diffuseColor.rgb *= (0.78 + 0.3 * n) * (0.94 + 0.1 * f) * (1.0 - 0.25 * smoothstep(0.45, 0.8, s)) * (1.0 - 0.35 * seam) * (1.0 - 0.55 * tie) * (1.0 - 0.3 * pore);
      _H = (f * 0.0015 - pore * 0.002 - tie * 0.004 - seam * 0.0015); }`,
    rough: 'roughnessFactor = 0.85 + 0.1 * vnoise3(vO * 30.0);',
  });
}
// polished granite floor tiles (cabin)
export function granite() {
  const m = new THREE.MeshPhysicalMaterial({ color: 0x2b2a2a, roughness: 0.25, metalness: 0, clearcoat: 0.6, clearcoatRoughness: 0.12 });
  return proc(m, 'granite', {
    color: `{ vec2 v = voro3(vO * 140.0); float spk = step(0.82, fract(sin(dot(floor(vO * 140.0), vec3(12.9, 78.2, 37.7))) * 4375.5));
      float sp2 = smoothstep(0.7, 0.9, vnoise3(vO * 260.0)); vec3 c = vec3(0.07, 0.068, 0.066) * (0.8 + 0.4 * vnoise3(vO * 30.0));
      c = mix(c, vec3(0.42, 0.40, 0.38), spk * smoothstep(0.0, 0.3, v.x) * 0.7); c = mix(c, vec3(0.6, 0.58, 0.55), sp2 * 0.35);
      vec2 tl = abs(fract(vO.xz / 0.5 + 0.5) - 0.5) * 0.5; float seam = 1.0 - smoothstep(0.0015, 0.003, min(tl.x, tl.y));
      diffuseColor.rgb = c * (1.0 - 0.6 * seam); _H = -seam * 0.0008; }`,
    rough: 'roughnessFactor = 0.18 + 0.15 * vnoise3(vO * 9.0);',
  });
}

// ------------------------------------------------------------------ steel wire rope: 8 helical strands, wires per strand
export function ropeMaterial({ lay = 0.095, strands = 8, key = 'rope', tint = 0x8a8d90 } = {}) {
  const m = new THREE.MeshPhysicalMaterial({ color: tint, metalness: 0.95, roughness: 0.38 });
  return proc(m, key, {
    ropeAttr: true,
    color: `{ float A = vRU.y * ${strands.toFixed(1)} + vRU.x / ${lay.toFixed(4)};
      float s = fract(A); float st = sqrt(max(s * (1.0 - s), 0.0)) * 2.0;
      float W = fract(vRU.y * ${(strands * 9).toFixed(1)} - vRU.x / ${(lay * 0.34).toFixed(4)});
      float wi = sqrt(max(W * (1.0 - W), 0.0)) * 2.0;
      float groove = smoothstep(0.0, 0.35, st);
      float grease = vnoise3(vec3(vRU.x * 30.0, vRU.y * 8.0, 0.0));
      diffuseColor.rgb *= mix(0.18, 1.0, groove) * (0.85 + 0.25 * wi) * (0.8 + 0.3 * grease);
      _H = (st * 0.75 + wi * 0.25) * 0.0011; }`,
    rough: 'roughnessFactor = 0.3 + 0.25 * (1.0 - smoothstep(0.0, 0.5, fract(vRU.y * 8.0 + vRU.x / 0.095))) + 0.1 * vnoise3(vec3(vRU.x * 30.0, vRU.y * 8.0, 2.0));',
  });
}

// ------------------------------------------------------------------ re-shapeable tube along a polyline (parallel transport)
export class Tube {
  constructor(nPts, radial = 10, radius = 0.0065, closedEnds = true) {
    this.n = nPts; this.rad = radial; this.r = radius;
    const nv = nPts * (radial + 1) + (closedEnds ? 2 : 0);
    const g = new THREE.BufferGeometry();
    this.pos = new Float32Array(nv * 3); this.nor = new Float32Array(nv * 3); this.ru = new Float32Array(nv * 2);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(this.nor, 3));
    g.setAttribute('rope', new THREE.BufferAttribute(this.ru, 2));
    const idx = [];
    for (let i = 0; i < nPts - 1; i++) for (let j = 0; j < radial; j++) {
      const a = i * (radial + 1) + j, b = a + radial + 1; idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
    if (closedEnds) {
      const c0 = nPts * (radial + 1), c1 = c0 + 1;
      for (let j = 0; j < radial; j++) { idx.push(c0, j + 1, j); const L = (nPts - 1) * (radial + 1); idx.push(c1, L + j, L + j + 1); }
    }
    this.closed = closedEnds;
    g.setIndex(idx); this.geo = g;
  }
  // pts: array of Vector3 (length n); radius: number or function(i)
  update(pts, radius = this.r, along0 = 0) {
    const n = this.n, R = this.rad, P = this.pos, N = this.nor, U = this.ru;
    const T = [], tmp = V(0, 0, 0);
    for (let i = 0; i < n; i++) { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)]; T.push(b.clone().sub(a).normalize()); }
    let nrm = Math.abs(T[0].y) < 0.9 ? V(0, 1, 0).cross(T[0]).normalize() : V(1, 0, 0).cross(T[0]).normalize();
    let along = along0;
    for (let i = 0; i < n; i++) {
      if (i > 0) {
        along += pts[i].distanceTo(pts[i - 1]);
        const ax = T[i - 1].clone().cross(T[i]); const s = ax.length();
        if (s > 1e-6) { ax.divideScalar(s); nrm.applyAxisAngle(ax, Math.atan2(s, T[i - 1].dot(T[i]))); }
      }
      const bin = T[i].clone().cross(nrm).normalize(); nrm = bin.clone().cross(T[i]).normalize();
      const r = typeof radius === 'function' ? radius(i) : radius;
      for (let j = 0; j <= R; j++) {
        const a = j / R * Math.PI * 2, c = Math.cos(a), s = Math.sin(a), k = i * (R + 1) + j;
        tmp.set(nrm.x * c + bin.x * s, nrm.y * c + bin.y * s, nrm.z * c + bin.z * s);
        P[k * 3] = pts[i].x + tmp.x * r; P[k * 3 + 1] = pts[i].y + tmp.y * r; P[k * 3 + 2] = pts[i].z + tmp.z * r;
        N[k * 3] = tmp.x; N[k * 3 + 1] = tmp.y; N[k * 3 + 2] = tmp.z; U[k * 2] = along; U[k * 2 + 1] = j / R;
      }
    }
    if (this.closed) {
      const c0 = n * (R + 1);
      for (const [k, i, sg] of [[c0, 0, -1], [c0 + 1, n - 1, 1]]) { P[k * 3] = pts[i].x; P[k * 3 + 1] = pts[i].y; P[k * 3 + 2] = pts[i].z; N[k * 3] = T[i].x * sg; N[k * 3 + 1] = T[i].y * sg; N[k * 3 + 2] = T[i].z * sg; }
    }
    this.geo.attributes.position.needsUpdate = true; this.geo.attributes.normal.needsUpdate = true; this.geo.attributes.rope.needsUpdate = true;
    this.geo.computeBoundingSphere();
  }
}

// canvas -> texture helper (sRGB)
export function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { canvas: c, g };
  return t;
}
