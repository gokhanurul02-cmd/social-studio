// Procedural Aedes-type mosquito (female, landed / biting pose). Units: millimetres, forward +Z, up +Y.
// Built for macro close-ups: high segment counts, tapered jointed legs with white tarsal rings,
// banded abdomen, lyre-marked thorax, faceted compound eyes, translucent veined wings with fringe.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const BLACK = new THREE.Color(0.026, 0.022, 0.02), WHITE = new THREE.Color(0.86, 0.88, 0.9), BROWN = new THREE.Color(0.05, 0.035, 0.028);

// ---- GLSL: procedural micro bump (screen-derivative bump mapping on a height field in object space)
export const BUMP_GLSL = /* glsl */`
  vec3 _h3(vec3 p){ p = fract(p*vec3(.1031,.1030,.0973)); p += dot(p, p.yxz+33.33); return fract((p.xxy+p.yxx)*p.zyx); }
  float vnoise3(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.-2.*f);
    float a=_h3(i).x, b=_h3(i+vec3(1,0,0)).x, c=_h3(i+vec3(0,1,0)).x, d=_h3(i+vec3(1,1,0)).x;
    float e=_h3(i+vec3(0,0,1)).x, f1=_h3(i+vec3(1,0,1)).x, g=_h3(i+vec3(0,1,1)).x, h=_h3(i+vec3(1,1,1)).x;
    return mix(mix(mix(a,b,f.x),mix(c,d,f.x),f.y), mix(mix(e,f1,f.x),mix(g,h,f.x),f.y), f.z); }
  // F1, F2 voronoi distances
  vec2 voro3(vec3 x){ vec3 p=floor(x), f=fract(x); float d1=8., d2=8.;
    for(int k=-1;k<=1;k++) for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++){ vec3 b=vec3(i,j,k); vec3 r=b-f+_h3(p+b); float d=dot(r,r);
      if(d<d1){ d2=d1; d1=d; } else if(d<d2) d2=d; }
    return vec2(sqrt(d1), sqrt(d2)); }
  vec3 bumpN(vec3 surf_pos, vec3 surf_norm, float H, float faceDirection){
    vec2 dHdxy = vec2(dFdx(H), dFdy(H));
    vec3 vSigmaX = normalize(dFdx(surf_pos)), vSigmaY = normalize(dFdy(surf_pos)), vN = surf_norm;
    vec3 R1 = cross(vSigmaY, vN), R2 = cross(vN, vSigmaX);
    float fDet = dot(vSigmaX, R1) * faceDirection;
    vec3 vGrad = sign(fDet) * (dHdxy.x * R1 + dHdxy.y * R2);
    return normalize(abs(fDet) * surf_norm - vGrad);
  }
`;

// tapered tube through points; r(u) radius function along normalised length
function taper(points, r, tub = 48, rad = 14, closed = false) {
  const curve = new THREE.CatmullRomCurve3(points, closed, 'centripetal');
  const g = new THREE.TubeGeometry(curve, tub, 1, rad, closed);
  const P = g.attributes.position, u = new Float32Array(P.count);
  for (let i = 0; i <= tub; i++) {
    const t = i / tub, c = curve.getPointAt(t), R = r(t);
    for (let j = 0; j <= rad; j++) {
      const k = i * (rad + 1) + j; const p = V(P.getX(k), P.getY(k), P.getZ(k)).sub(c).multiplyScalar(R).add(c);
      P.setXYZ(k, p.x, p.y, p.z); u[k] = t;
    }
  }
  g.setAttribute('ut', new THREE.BufferAttribute(u, 1));
  g.computeVertexNormals();
  // end caps (small spheres)
  return { g, curve };
}
function paint(g, fn) { // fn(i, pos, ut) -> Color
  const P = g.attributes.position, U = g.attributes.ut, c = new Float32Array(P.count * 3), p = V(0, 0, 0);
  for (let i = 0; i < P.count; i++) { p.set(P.getX(i), P.getY(i), P.getZ(i)); const col = fn(i, p, U ? U.getX(i) : 0); c.set([col.r, col.g, col.b], i * 3); }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  return g;
}
function strip(g) { // keep only attributes shared by every part (for merging)
  for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'color'].includes(k)) g.deleteAttribute(k);
  if (!g.attributes.color) paint(g, () => BLACK);
  return g.index ? g.toNonIndexed() : g;
}
function sphere(r, c, scl, segW = 48, segH = 32, col = BLACK) {
  const g = new THREE.SphereGeometry(r, segW, segH); g.scale(scl[0], scl[1], scl[2]); g.translate(c.x, c.y, c.z);
  return paint(g, () => col);
}

// thin hairs: tapered 3-sided cones from base along direction
function hairs(list, colFn) {
  const parts = [];
  for (const h of list) {
    const g = new THREE.ConeGeometry(h.r, h.len, 4, 1, true);
    g.translate(0, h.len / 2, 0);
    const q = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), h.dir.clone().normalize());
    g.applyQuaternion(q); g.translate(h.p.x, h.p.y, h.p.z);
    paint(g, () => colFn ? colFn(h) : BROWN); parts.push(strip(g));
  }
  return parts;
}

// ---------------------------------------------------------------- wing texture (canvas)
function wingTexture() {
  const W = 1024, H = 256, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const x = cv.getContext('2d');
  // outline: base at left (x=0), tip at right. y: leading edge top.
  const outline = (ctx) => { ctx.beginPath(); ctx.moveTo(10, 120); ctx.bezierCurveTo(120, 40, 600, 30, 1000, 95); ctx.bezierCurveTo(1030, 120, 1010, 150, 960, 170);
    ctx.bezierCurveTo(700, 225, 300, 225, 120, 185); ctx.bezierCurveTo(60, 170, 20, 150, 10, 120); ctx.closePath(); };
  x.clearRect(0, 0, W, H);
  // membrane
  outline(x); const gr = x.createLinearGradient(0, 0, W, 0); gr.addColorStop(0, 'rgba(95,85,80,0.62)'); gr.addColorStop(1, 'rgba(150,150,160,0.42)');
  x.fillStyle = gr; x.fill();
  // fringe hairs on trailing edge
  x.save(); x.strokeStyle = 'rgba(40,32,28,0.55)'; x.lineWidth = 1.4;
  for (let i = 0; i < 260; i++) { const t = i / 259; const px = 120 + t * 860, py = 185 + Math.sin(t * Math.PI) * 35 - t * 15;
    x.beginPath(); x.moveTo(px, py - 4); x.lineTo(px + 10, py + 16 + 6 * Math.sin(i * 7.1)); x.stroke(); }
  x.restore();
  // veins (dark, with scale texture)
  const vein = (pts, w) => { x.beginPath(); x.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) x.lineTo(pts[i][0], pts[i][1]); x.lineWidth = w; x.stroke(); };
  x.strokeStyle = 'rgba(28,22,20,0.95)'; x.lineCap = 'round'; x.lineJoin = 'round';
  vein([[12, 118], [140, 58], [500, 42], [990, 92]], 7);            // costa
  vein([[20, 122], [200, 72], [520, 62]], 4);                         // subcosta
  vein([[22, 126], [260, 88], [700, 78], [1000, 104]], 4);            // R1
  vein([[260, 92], [520, 100], [760, 110], [1000, 125]], 3);          // R2+3 stem
  vein([[600, 104], [990, 145]], 2.6);                                 // R3 fork
  vein([[240, 98], [560, 128], [980, 158]], 3);                        // R4+5
  vein([[24, 130], [300, 126], [560, 150], [900, 182]], 3);            // M
  vein([[560, 150], [760, 196]], 2.4);                                 // M fork
  vein([[26, 136], [260, 150], [520, 192]], 3);                        // Cu
  vein([[260, 150], [380, 205]], 2.2);                                 // Cu fork
  vein([[30, 142], [180, 175], [290, 200]], 2.4);                      // anal
  // cross veins
  vein([[420, 82], [430, 112]], 1.8); vein([[520, 118], [520, 146]], 1.8); vein([[470, 146], [470, 172]], 1.6);
  // scales along veins: tiny dark flecks
  const rnd = mulberry(5);
  x.fillStyle = 'rgba(20,16,14,0.6)';
  for (let i = 0; i < 1800; i++) { const px = 30 + rnd() * 960, py = 60 + rnd() * 140; const a = x.getImageData(px | 0, py | 0, 1, 1).data[3]; if (a > 200) x.fillRect(px - 2, py - 1, 4 + rnd() * 3, 2); }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return tex;
}
function wingGeometry() {
  // plane spanning the texture: x in [0, 2.9] mm (base->tip), z (chord) in [-0.36, 0.36]
  const g = new THREE.PlaneGeometry(2.9, 0.725, 64, 16);
  g.translate(1.45, 0, 0); g.rotateX(-Math.PI / 2);
  // slight camber
  const P = g.attributes.position; for (let i = 0; i < P.count; i++) { const zz = P.getZ(i); P.setY(i, 0.04 * (1 - (zz / 0.36) ** 2) * Math.min(1, P.getX(i) / 0.4)); }
  g.computeVertexNormals();
  return g;
}

// ---------------------------------------------------------------- build
// opts.curvR: radius of the cylinder the mosquito stands on (mm), measured across its body (x); Infinity = flat ground

// ---------------------------------------------------------------------------------------------
// v2 structure: thorax/head (static), abdomen (own pivot: swells into a red balloon), legs (rebuilt from a
// deformable control polyline: noodle bending, collapse, kinks), velvet body + instanced scale cards,
// x-ray mode (fresnel shell) and an optional tracheal system with oxygen particles.
const XRAY_SHELL = (col) => {
  const m = new THREE.MeshStandardMaterial({ color: 0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const u = { uCol: { value: new THREE.Color(col) }, uK: { value: 1 } }; m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 uCol; uniform float uK;')
      .replace('#include <dithering_fragment>', `#include <dithering_fragment>
        { float f = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition))); gl_FragColor = vec4(uCol * (0.04 + 1.2 * pow(f, 2.4)) * uK, 1.0); }`);
  };
  m.customProgramCacheKey = () => 'mq-xray';
  return m;
};

function scaleCards(geos, count, rnd, mat, lift = 0.006) {
  // area-weighted surface samples of (non-indexed, vertex-coloured) geometries -> flat leaf cards pointing backwards
  const tris = []; let total = 0;
  for (const g of geos) {
    const P = g.attributes.position, C = g.attributes.color;
    for (let i = 0; i < P.count; i += 3) {
      const a = V(P.getX(i), P.getY(i), P.getZ(i)), b = V(P.getX(i + 1), P.getY(i + 1), P.getZ(i + 1)), c = V(P.getX(i + 2), P.getY(i + 2), P.getZ(i + 2));
      const ar = b.clone().sub(a).cross(c.clone().sub(a)).length() / 2; if (ar <= 0) continue;
      total += ar; tris.push({ a, b, c, ar, acc: total, col: new THREE.Color(C.getX(i), C.getY(i), C.getZ(i)) });
    }
  }
  const card = new THREE.BufferGeometry();
  card.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0.5, -0.5, 0.02, 0, 0, 0.04, -0.5, 0.5, 0.02, 0], 3));
  card.setIndex([0, 1, 2, 0, 2, 3]); card.computeVertexNormals();
  const im = new THREE.InstancedMesh(card, mat, count);
  const m4 = new THREE.Matrix4(), back = V(0, 0, -1);
  for (let k = 0; k < count; k++) {
    const r = rnd() * total; let lo = 0, hi = tris.length - 1; while (lo < hi) { const mid = (lo + hi) >> 1; if (tris[mid].acc < r) lo = mid + 1; else hi = mid; }
    const T = tris[lo]; let u = rnd(), v = rnd(); if (u + v > 1) { u = 1 - u; v = 1 - v; }
    const p = T.a.clone().add(T.b.clone().sub(T.a).multiplyScalar(u)).add(T.c.clone().sub(T.a).multiplyScalar(v));
    const n = T.b.clone().sub(T.a).cross(T.c.clone().sub(T.a)).normalize();
    let t = back.clone().addScaledVector(n, -n.dot(back)); if (t.lengthSq() < 1e-4) t = V(1, 0, 0); t.normalize();
    t.addScaledVector(n, 0.25).normalize();                              // free end lifted a little
    const bx = n.clone().cross(t).normalize(), ny = t.clone().cross(bx).normalize();
    const sc = 0.022 + rnd() * 0.02;
    m4.makeBasis(bx.multiplyScalar(sc * 0.42), ny.multiplyScalar(sc), t.multiplyScalar(sc)).setPosition(p.addScaledVector(n, lift));
    im.setMatrixAt(k, m4);
    const w = T.col.r > 0.3 ? 1 : 0;
    const base = w ? new THREE.Color(0.75, 0.76, 0.78) : new THREE.Color(0.05, 0.045, 0.04);
    im.setColorAt(k, base.multiplyScalar(0.75 + rnd() * 0.5));
  }
  im.castShadow = false; im.receiveShadow = true;
  return im;
}

// leg control points -> tubes (femur, tibia, 5-part tarsus with white rings), joints and claws
const LEG_SPEC = (FOOT, hindUp) => [
  { fore: true, base: V(0.15, -0.25, 0.85), knee: V(0.6, 0.38, 2.55), ank: V(0.9, FOOT + 0.6, 4.4), foot: [V(1.0, FOOT + 0.06, 5.2), V(1.06, FOOT, 5.9), V(1.1, FOOT, 6.4)] },
  { base: V(0.22, -0.3, 0.5), knee: V(1.55, 0.42, 0.25), ank: V(2.55, FOOT + 0.6, -0.55), foot: [V(2.95, FOOT + 0.06, -1.15), V(3.25, FOOT, -1.9), V(3.4, FOOT, -2.45)] },
  { base: V(0.2, -0.28, 0.22), knee: V(1.0, 0.3, -1.7), ank: V(1.35, 0.3 + 0.8 * hindUp, -3.55), foot: [V(1.42, 0.3 + 1.6 * hindUp, -4.5), V(1.32, 0.3 + 2.15 * hindUp, -5.15), V(1.12, 0.3 + 2.4 * hindUp, -5.45)], hind: true },
];
function legGeometry(pts, s, hind, detailHairs, rnd) {
  // pts: [base, kneeMid, knee, tibMid1, tibMid2, ank, foot...]
  const [base, kneeMid, knee, t1, t2, ank, ...foot] = pts;
  const parts = [];
  const fem = taper([base, kneeMid, knee], u => 0.058 - 0.014 * u + 0.008 * Math.sin(u * Math.PI), 48, 12);
  const tib = taper([knee, t1, t2, ank], u => 0.044 - 0.008 * u, 64, 10);
  const tar = taper([ank, ...foot], u => 0.034 * (1 - 0.62 * u), 96, 8);
  parts.push(strip(paint(fem.g, () => BLACK)), strip(paint(tib.g, (i, p, u) => u > 0.94 ? WHITE.clone().multiplyScalar(0.7) : BLACK)));
  const bounds = [0, 0.36, 0.58, 0.74, 0.87, 1.0];
  parts.push(strip(paint(tar.g, (i, p, u) => {
    let k = 0; while (k < 4 && u > bounds[k + 1]) k++;
    const f = (u - bounds[k]) / (bounds[k + 1] - bounds[k]);
    if (hind && k === 4) return WHITE;
    return f < 0.22 ? WHITE : BLACK;
  })));
  for (const j of [base, knee, ank]) parts.push(strip(sphere(j === base ? 0.1 : 0.05, j, [1, 1, 1], 16, 10, BLACK)));
  const end = foot[foot.length - 1], dir = end.clone().sub(foot[foot.length - 2]).normalize();
  parts.push(...hairs([{ p: end, dir: dir.clone().add(V(0, -0.5, 0)), len: 0.07, r: 0.008 }, { p: end, dir: dir.clone().add(V(s * 0.4, -0.5, 0)), len: 0.07, r: 0.008 }]));
  if (detailHairs) {
    const hl = [];
    for (const [crv, n, len] of [[fem.curve, 26, 0.07], [tib.curve, 30, 0.08], [tar.curve, 34, 0.06]]) for (let i = 0; i < n; i++) {
      const t = (i + rnd()) / n, c = crv.getPointAt(t), tan = crv.getTangentAt(t);
      const a = rnd() * Math.PI * 2; const side = V(Math.cos(a), Math.sin(a), 0.3).cross(tan).normalize();
      hl.push({ p: c.clone().addScaledVector(side, 0.025), dir: tan.clone().multiplyScalar(2.0).add(side), len: len * 0.55 * (0.6 + rnd() * 0.8), r: 0.004 });
    }
    parts.push(...hairs(hl));
  }
  return mergeGeometries(parts, false);
}

export function buildMosquito({ curvR = Infinity, hindUp = 1.0, detail = 1, bite = true, legSpread = 1, reach = 1, cards = true, trachea = false } = {}) {
  const thoraxParts = [], headParts = [], abdParts = [];
  let parts = thoraxParts;
  const rnd = mulberry(77);
  const dropAt = x => isFinite(curvR) ? (x * x) / (2 * curvR) : 0;
  const FOOT = -2.0;

  // ---- thorax: humped ellipsoid, lyre pattern
  let thoraxGeo;
  {
    const g = new THREE.SphereGeometry(1, 128, 96);
    const P = g.attributes.position;
    for (let i = 0; i < P.count; i++) {
      let x = P.getX(i), y = P.getY(i), z = P.getZ(i);
      const hump = 1 + 0.18 * Math.max(0, y) * (1 - Math.abs(z));
      x *= 0.46; y *= 0.52 * hump; z *= 0.72; z += 0.06 * y;
      P.setXYZ(i, x, y + 0.25, z + 0.55);
    }
    g.computeVertexNormals();
    paint(g, (i, p) => {
      const lx = p.x, ly = p.y - 0.25, lz = p.z - 0.55;
      let w = 0;
      if (ly > 0.18) {
        const cx = 0.20 + 0.10 * Math.cos((lz + 0.1) * 2.6);
        w = Math.max(w, Math.exp(-(((Math.abs(lx) - cx) / 0.028) ** 2)) * (lz > -0.45 && lz < 0.55 ? 1 : 0));
        w = Math.max(w, Math.exp(-(((Math.abs(lx) - 0.045) / 0.014) ** 2)) * (lz > -0.5 && lz < 0.25 ? 0.9 : 0));
      }
      if (Math.abs(lx) > 0.3 && ly < 0.25 && ly > -0.35) {
        const s1 = Math.exp(-(((ly - 0.05) / 0.09) ** 2 + ((lz - 0.25) / 0.14) ** 2));
        const s2 = Math.exp(-(((ly + 0.2) / 0.08) ** 2 + ((lz + 0.15) / 0.12) ** 2));
        w = Math.max(w, s1, s2 * 0.9);
      }
      return BLACK.clone().lerp(WHITE, Math.min(1, w));
    });
    thoraxGeo = strip(g);
    parts.push(thoraxGeo);
    parts.push(strip(sphere(0.16, V(0, 0.52, -0.12), [1.6, 0.6, 0.9], 32, 20, BLACK)));
  }
  // ---- head
  parts = headParts;
  const HEAD = V(0, 0.22, 1.33);
  parts.push(strip(sphere(0.26, HEAD, [1, 0.95, 0.9], 48, 32, BLACK)));
  { const { g } = taper([V(0, 0.22, 1.05), V(0, 0.21, 1.15), V(0, 0.22, 1.25)], () => 0.13, 8, 16); parts.push(strip(paint(g, () => BLACK))); }
  parts.push(strip(sphere(0.09, V(0, 0.44, 1.32), [1.2, 0.5, 1.0], 24, 16, WHITE)));
  {
    const tip = V(0, FOOT - 0.05, 2.25);
    const ppts = bite ? [V(0, 0.08, 1.52), V(0, -0.05, 1.85), V(0, -0.45, 2.15), V(0, -0.95, 2.26), tip] : [V(0, 0.08, 1.52), V(0, -0.06, 1.95), V(0, -0.3, 2.5), V(0, -0.62, 3.1), V(0, -0.85, 3.45)];
    const { g } = taper(ppts, u => 0.042 * (1 - 0.55 * u) + 0.012 * Math.exp(-(((u - 0.7) / 0.08) ** 2)), 64, 12);
    parts.push(strip(paint(g, () => BLACK)));
  }
  for (const s of [-1, 1]) {
    const { g } = taper([V(s * 0.05, 0.12, 1.52), V(s * 0.09, 0.02, 1.7), V(s * 0.11, -0.1, 1.83)], u => 0.035 * (1 - 0.3 * u), 16, 10);
    parts.push(strip(paint(g, (i, p, u) => u > 0.75 ? WHITE : BLACK)));
  }
  for (const s of [-1, 1]) {
    const pts = [V(s * 0.05, 0.3, 1.55), V(s * 0.22, 0.55, 1.95), V(s * 0.38, 0.75, 2.35), V(s * 0.5, 0.88, 2.75)];
    const { g, curve } = taper(pts, u => 0.022 * (1 - 0.5 * u), 48, 8);
    parts.push(strip(paint(g, () => BROWN)));
    parts.push(strip(sphere(0.07, pts[0], [1, 1, 1], 16, 12, BROWN)));
    const hl = [];
    for (let w = 1; w < 13; w++) {
      const t = w / 13, c = curve.getPointAt(t), tan = curve.getTangentAt(t);
      const a = V(1, 0, 0).cross(tan).normalize(), b = tan.clone().cross(a).normalize();
      for (let k = 0; k < 6; k++) { const ang = k / 6 * Math.PI * 2 + w; const d = a.clone().multiplyScalar(Math.cos(ang)).add(b.clone().multiplyScalar(Math.sin(ang))).add(tan.clone().multiplyScalar(0.6));
        hl.push({ p: c, dir: d, len: 0.16 * (1 - t * 0.4), r: 0.004 }); }
    }
    parts.push(...hairs(hl));
  }
  // ---- abdomen (own pivot at the waist)
  parts = abdParts;
  const ABD = V(0, 0.18, -0.02), L = 2.7, NSEG = 8;
  const abdR = t => 0.3 * Math.pow(Math.sin(Math.PI * Math.min(1, t * 1.15 + 0.08)), 0.6) * (1 - 0.55 * t) + 0.02;
  let abdGeo;
  {
    const prof = [];
    for (let i = 0; i <= 160; i++) {
      const t = i / 160, seg = t * NSEG, f = seg - Math.floor(seg);
      const r = abdR(t) * (1 - 0.08 * Math.exp(-(((f - 0.02) / 0.06) ** 2)));
      prof.push(new THREE.Vector2(Math.max(0.001, r), -t * L));
    }
    const g = new THREE.LatheGeometry(prof, 96);
    g.rotateX(-Math.PI / 2);
    const P = g.attributes.position;
    for (let i = 0; i < P.count; i++) {
      let x = P.getX(i), y = P.getY(i), z = P.getZ(i);
      const t = Math.abs(z) / L; z = -Math.abs(z);
      y = y * 0.82 - 0.35 * t * t + 0.1 * t;
      P.setXYZ(i, x, y, z);  // relative to the waist pivot
    }
    g.computeVertexNormals();
    paint(g, (i, p) => {
      const t = Math.abs(p.z) / L, seg = t * NSEG, f = seg - Math.floor(seg);
      const dors = p.y > 0.02 ? 1 : 0;
      let w = 0;
      if (seg > 0.8 && seg < 7.5) {
        w = Math.max(w, (f < 0.16 ? 1 : 0) * dors * 0.95);
        const lat = Math.abs(p.x) > 0.6 * 0.3 * (1 - 0.5 * t) && p.y < 0.08 && p.y > -0.2;
        w = Math.max(w, (lat && f < 0.35) ? 1 : 0);
      }
      return BLACK.clone().lerp(WHITE, w);
    });
    abdGeo = strip(g);
    parts.push(abdGeo);
    const hl = [];
    for (let i = 0; i < 200 * detail; i++) {
      const t = rnd(), a = rnd() * Math.PI * 2, r = abdR(t) * 0.95;
      const p = V(Math.cos(a) * r, Math.sin(a) * r * 0.82 - 0.35 * t * t + 0.1 * t, -t * L);
      hl.push({ p, dir: V(Math.cos(a), Math.sin(a), -2.2), len: 0.05 + rnd() * 0.08, r: 0.005 });
    }
    parts.push(...hairs(hl, () => new THREE.Color(0.35, 0.3, 0.26)));
  }
  // ---- thorax bristles, halteres
  parts = thoraxParts;
  {
    const hl = [];
    for (let i = 0; i < 110 * detail; i++) {
      const u = rnd() * Math.PI * 2, v = rnd() * Math.PI * 0.6;
      const n = V(Math.sin(v) * Math.cos(u), Math.cos(v), Math.sin(v) * Math.sin(u));
      const p = V(n.x * 0.46, n.y * 0.6 + 0.25, n.z * 0.72 + 0.55);
      hl.push({ p, dir: n.clone().add(V(0, 0, -0.9)), len: 0.04 + rnd() * 0.08, r: 0.004 });
    }
    parts.push(...hairs(hl, () => new THREE.Color(0.35, 0.3, 0.26)));
  }
  for (const s of [-1, 1]) { const { g } = taper([V(s * 0.3, 0.3, 0.05), V(s * 0.5, 0.35, -0.1)], () => 0.018, 8, 8); parts.push(strip(paint(g, () => BROWN)), strip(sphere(0.06, V(s * 0.52, 0.35, -0.12), [1, 0.8, 1], 16, 12, new THREE.Color(0.5, 0.45, 0.4)))); }

  // ---- materials: velvet (rough + sheen) chitin, scales on top
  const mkBodyMat = (key, fill) => {
    const m = new THREE.MeshPhysicalMaterial({ vertexColors: true, color: 0xffffff, roughness: 0.78, metalness: 0.0,
      sheen: 1.0, sheenRoughness: 0.35, sheenColor: new THREE.Color(0.5, 0.47, 0.44), clearcoat: 0.0, specularIntensity: 0.55 });
    const u = { uFill: { value: 0 } }; m.userData.u = u;
    m.onBeforeCompile = sh => {
      Object.assign(sh.uniforms, u);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvObj = position;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj; uniform float uFill;\n' + BUMP_GLSL)
        .replace('#include <color_fragment>', `#include <color_fragment>
          ${fill ? `{ float band = vColor.r; vec3 blood = mix(vec3(0.55, 0.02, 0.025), vec3(0.95, 0.75, 0.72), band * 0.6);
            diffuseColor.rgb = mix(diffuseColor.rgb * (1.0 + 0.6 * vnoise3(vObj * 20.0)), blood, uFill); }` : 'diffuseColor.rgb *= 1.0 + 0.6 * vnoise3(vObj * 20.0);'}`)
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          { vec2 vo = voro3(vObj * 38.0); float H = ((vo.y - vo.x) * 0.006 + vnoise3(vObj * 90.0) * 0.003) * (1.0 - uFill); normal = bumpN(-vViewPosition, normal, H, faceDirection); }`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(mix(0.62, 0.88, vnoise3(vObj*55.0)) + (vColor.r > 0.4 ? -0.15 : 0.0), 0.18, uFill);')
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          ${fill ? 'totalEmissiveRadiance += vec3(0.9, 0.04, 0.03) * uFill * uFill * 0.55;' : ''}`);
    };
    m.customProgramCacheKey = () => key;
    return m;
  };
  const bodyMat = mkBodyMat('mosq-body2', false), abdMat = mkBodyMat('mosq-abd2', true);
  const cardMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.42, sheen: 0.8, sheenRoughness: 0.3, sheenColor: new THREE.Color(0.6, 0.58, 0.55), iridescence: 0.35, iridescenceIOR: 1.4, side: THREE.DoubleSide });
  const abdCardMat = cardMat.clone();

  const body = new THREE.Mesh(mergeGeometries(thoraxParts, false), bodyMat); body.castShadow = true; body.receiveShadow = true;
  const NECK = V(0, 0.22, 1.12);
  const headGeo = mergeGeometries(headParts, false); headGeo.translate(-NECK.x, -NECK.y, -NECK.z);
  const head = new THREE.Mesh(headGeo, bodyMat); head.castShadow = true; head.receiveShadow = true;
  const headPivot = new THREE.Group(); headPivot.position.copy(NECK); headPivot.add(head);
  const abdomen = new THREE.Group(); abdomen.position.copy(ABD);
  const abdMesh = new THREE.Mesh(mergeGeometries(abdParts, false), abdMat); abdMesh.castShadow = true; abdMesh.receiveShadow = true;
  abdomen.add(abdMesh);
  // blood glow core (seen in x-ray and through the stretched cuticle)
  const core = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), new THREE.MeshBasicMaterial({ color: 0xff1a10, transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending }));
  core.visible = false; abdomen.add(core);

  const cardMeshes = [];
  if (cards) {
    const tc = scaleCards([thoraxGeo], Math.round(6000 * detail), rnd, cardMat); body.add(tc); cardMeshes.push(tc);
    const ac = scaleCards([abdGeo], Math.round(7000 * detail), rnd, abdCardMat, 0.005); abdomen.add(ac); cardMeshes.push(ac);
  }

  // compound eyes
  const eyeMat = new THREE.MeshPhysicalMaterial({ color: 0x241810, roughness: 0.42, metalness: 0.0, clearcoat: 0.25, clearcoatRoughness: 0.35, iridescence: 0.5, iridescenceIOR: 1.6, sheen: 0.6, sheenColor: new THREE.Color(0.35, 0.28, 0.2) });
  eyeMat.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvObj = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;\n' + BUMP_GLSL)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        { vec2 vo = voro3(normalize(vObj) * 26.0); float H = -vo.x * vo.x * 0.012; normal = bumpN(-vViewPosition, normal, H, faceDirection); }`);
  };
  eyeMat.customProgramCacheKey = () => 'mosq-eye2';
  const eyes = new THREE.Group();
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.24, 64, 48), eyeMat); e.position.set(s * 0.14, 0.22 - NECK.y, 1.42 - NECK.z); e.scale.set(0.8, 1.05, 0.95); e.castShadow = true; eyes.add(e); }
  headPivot.add(eyes);

  // wings
  const wingMat = new THREE.MeshPhysicalMaterial({ map: wingTexture(), transparent: true, side: THREE.DoubleSide, depthWrite: false,
    roughness: 0.12, metalness: 0.0, iridescence: 1.0, iridescenceIOR: 1.33, specularIntensity: 1.0 });
  const wings = []; const wg = wingGeometry();
  for (const s of [-1, 1]) {
    const piv = new THREE.Group(); piv.position.set(s * 0.3, 0.62, 0.3);
    const w = new THREE.Mesh(wg, wingMat); w.renderOrder = 2; w.castShadow = true;
    if (s > 0) w.scale.set(1, 1, -1);
    piv.add(w); wings.push(piv);
  }

  // legs: control polylines in body space
  const legMeshes = [], legDefs = [];
  for (const Ls of LEG_SPEC(FOOT, hindUp)) for (const s of [-1, 1]) {
    const fz = Ls.fore ? reach : 1;
    const m = p => V(p.x * s * (p === Ls.base ? 1 : legSpread), p.y - (p.y < FOOT + 0.06 ? dropAt(p.x) : 0), p === Ls.base ? p.z : Ls.base.z + (p.z - Ls.base.z) * fz);
    const base = m(Ls.base), knee = m(Ls.knee), ank = m(Ls.ank), foot = Ls.foot.map(m);
    const kneeMid = base.clone().lerp(knee, 0.5).add(V(0, 0.12, 0));
    const t1 = knee.clone().lerp(ank, 0.33).add(V(s * 0.06, 0.04, 0)), t2 = knee.clone().lerp(ank, 0.66).add(V(s * 0.06, 0.03, 0));
    const pts = [base, kneeMid, knee, t1, t2, ank, ...foot];
    const lens = [0]; for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + pts[i].distanceTo(pts[i - 1]));
    const us = lens.map(l => l / lens[lens.length - 1]);
    legDefs.push({ pts, us, s, hind: !!Ls.hind, fore: !!Ls.fore });
    const mesh = new THREE.Mesh(legGeometry(pts, s, !!Ls.hind, detail > 0.5, rnd), bodyMat); mesh.castShadow = true; mesh.receiveShadow = true;
    legMeshes.push(mesh);
  }
  let legKey = 'rest';
  // st: {drop (body-space units the body sinks), wob (noodle amplitude), kink (0..1 per leg array or number), phase, splay}
  function setLegs(st = null) {
    const key = st ? JSON.stringify(st, (k, v) => typeof v === 'number' ? +v.toFixed(3) : v) : 'rest';
    if (key === legKey) return; legKey = key;
    legDefs.forEach((d, li) => {
      let pts = d.pts;
      if (st) {
        const baseY = d.pts[0].y, drop = st.drop || 0, f = Math.max(0.05, 1 - drop / (baseY - FOOT));
        const kink = Array.isArray(st.kink) ? st.kink[li] : (st.kink || 0);
        const wob = (st.wob || 0) * (Array.isArray(st.wobK) ? st.wobK[li] : 1);
        pts = d.pts.map((p, i) => {
          const u = d.us[i], q = p.clone();
          q.y = baseY + (p.y - baseY) * (d.hind ? 1 - (1 - f) * 0.5 : f);
          const bul = Math.sin(Math.PI * Math.min(1, u * 1.3)) * (1 - f) * 1.1 * (1 + (st.splay || 0));
          q.x += d.s * bul;
          const ph = (st.phase || 0) + li * 1.7;
          const w = wob * Math.sin(u * Math.PI * 4.0 + ph) * Math.sin(Math.PI * u);
          q.y += w * 1.4; q.x += d.s * w * 0.9; q.z += w * 0.5 * Math.cos(u * Math.PI * 3.0 + ph);
          q.y -= kink * 0.9 * Math.max(0, 1 - Math.abs(u - 0.42) / 0.16) * (baseY - FOOT);
          if (!d.hind && u > 0.55) q.y = Math.max(q.y, FOOT + drop + 0.03 + (u > 0.9 ? 0 : 0.02));
          if (i === 0) q.copy(p);
          return q;
        });
        // a kinked tibia gets an extra sharp corner point
      }
      const m = legMeshes[li]; m.geometry.dispose(); m.geometry = legGeometry(pts, d.s, d.hind, detail > 0.5 && !st, rnd);
    });
  }

  // ---- tracheae + oxygen particles (x-ray facts scene)
  let tracheaGroup = null, o2 = null;
  if (trachea) {
    tracheaGroup = new THREE.Group();
    const curves = [];
    const trunkL = [], trunkR = [];
    for (let i = 0; i <= 10; i++) { const z = 1.25 - i * 0.37; const t = Math.max(0, -z / L); trunkL.push(V(0.16, 0.22 - 0.25 * t * t, z)); trunkR.push(V(-0.16, 0.22 - 0.25 * t * t, z)); }
    const spir = [];
    for (const s of [-1, 1]) {
      spir.push(V(s * 0.43, 0.24, 0.78), V(s * 0.43, 0.08, 0.2));
      for (let k = 1; k <= 7; k++) { const t = (k + 0.3) / NSEG, z = -t * L + ABD.z; spir.push(V(s * abdR(t) * 0.92, ABD.y - 0.35 * t * t + 0.1 * t + 0.02, z)); }
    }
    const trunkCurveL = new THREE.CatmullRomCurve3(trunkL), trunkCurveR = new THREE.CatmullRomCurve3(trunkR);
    const tubes = [];
    const addTube = (pts, r0, r1, d0, d1) => { const c = new THREE.CatmullRomCurve3(pts); const { g } = taper(pts, u => r0 + (r1 - r0) * u, Math.max(8, pts.length * 10), 8);
      const U = g.attributes.ut, D = new Float32Array(U.count); for (let i = 0; i < U.count; i++) D[i] = d0 + (d1 - d0) * U.getX(i); g.setAttribute('depth', new THREE.BufferAttribute(D, 1)); tubes.push(g); curves.push({ c, d0, d1 }); return c; };
    // trunks (depth ~1 in the middle), spiracle connectives, fine branches into muscles, head, legs
    addTube(trunkL, 0.035, 0.03, 1.0, 1.0); addTube(trunkR, 0.035, 0.03, 1.0, 1.0);
    for (const sp of spir) {
      const tc = sp.x > 0 ? trunkCurveL : trunkCurveR;
      let best = 0, bd = 9; for (let i = 0; i <= 40; i++) { const d = tc.getPoint(i / 40).distanceTo(sp); if (d < bd) { bd = d; best = i / 40; } }
      const tp = tc.getPoint(best);
      addTube([sp, sp.clone().lerp(tp, 0.5).add(V(0, 0.03, 0)), tp], 0.03, 0.026, 0, 0.55);
      for (let k = 0; k < 5; k++) {
        const a = tp.clone(), b = a.clone().add(V((rnd() - 0.5) * 0.4, (rnd() - 0.5) * 0.35, (rnd() - 0.5) * 0.5));
        b.x = THREE.MathUtils.clamp(b.x, -0.38, 0.38);
        addTube([a, a.clone().lerp(b, 0.5).add(V(0, 0.04, 0)), b], 0.016, 0.006, 0.6, 1.0);
      }
    }
    for (const s of [-1, 1]) addTube([V(s * 0.16, 0.22, 1.2), V(s * 0.1, 0.24, 1.3), V(s * 0.08, 0.22, 1.42)], 0.02, 0.01, 0.9, 1.0);
    for (const d of legDefs) addTube([V(d.s * 0.16, 0.12, d.pts[0].z), d.pts[0], d.pts[1], d.pts[2]], 0.014, 0.008, 0.85, 1.0);
    const tMat = new THREE.MeshStandardMaterial({ color: 0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
    const tu = { uReach: { value: 2 } }; tMat.userData.u = tu;
    tMat.onBeforeCompile = sh => {
      Object.assign(sh.uniforms, tu);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float depth; varying float vDepth;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvDepth = depth;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform float uReach; varying float vDepth;')
        .replace('#include <dithering_fragment>', `#include <dithering_fragment>
          { float f = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition)));
            float ox = 1.0 - smoothstep(uReach - 0.08, uReach + 0.04, vDepth);
            vec3 c = mix(vec3(0.75, 0.22, 0.32), vec3(0.85, 0.95, 1.0), ox);
            gl_FragColor = vec4(c * (0.25 + 1.1 * pow(f, 1.5)), 1.0); }`);
    };
    tMat.customProgramCacheKey = () => 'mq-trachea';
    const tm = new THREE.Mesh(mergeGeometries(tubes.map(g => { for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'depth'].includes(k)) g.deleteAttribute(k); return g.index ? g.toNonIndexed() : g; }), false), tMat);
    tm.renderOrder = 3; tracheaGroup.add(tm);
    // oxygen particles: travel from depth 0 (spiracle) inwards along connective + branch paths
    const N = 900, pm = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }), N);
    pm.renderOrder = 4; pm.frustumCulled = false;
    const paths = curves.filter(c => c.d0 < 0.7);
    const P0 = Array.from({ length: N }, () => ({ c: paths[Math.floor(rnd() * paths.length)], ph: rnd(), sp: 0.5 + rnd() * 0.5, r: 0.012 + rnd() * 0.01 }));
    tracheaGroup.add(pm);
    const m4 = new THREE.Matrix4(), col = new THREE.Color();
    o2 = (t, reach) => {
      tu.uReach.value = reach;
      P0.forEach((p, i) => {
        const u = (p.ph + t * 0.9 * p.sp) % 1, d = p.c.d0 + (p.c.d1 - p.c.d0) * u;
        const a = 1 - THREE.MathUtils.smoothstep(d, reach - 0.12, reach);
        const pos = p.c.c.getPointAt(u);
        m4.makeScale(p.r * (0.3 + 0.7 * a), p.r * (0.3 + 0.7 * a), p.r * (0.3 + 0.7 * a)).setPosition(pos); pm.setMatrixAt(i, m4);
        pm.setColorAt(i, col.setRGB(0.3 * a, 0.95 * a, 1.0 * a));
      });
      pm.instanceMatrix.needsUpdate = true; if (pm.instanceColor) pm.instanceColor.needsUpdate = true;
    };
    o2(0, 2);
    tracheaGroup.visible = false;
  }

  const root = new THREE.Group(); root.add(body, headPivot, abdomen, ...wings, ...legMeshes);
  if (tracheaGroup) root.add(tracheaGroup);
  const group = new THREE.Group(); group.add(root);

  function setWings(t, flap = 0, spread = 0, droop = 0) {
    for (let i = 0; i < 2; i++) {
      const s = i === 0 ? -1 : 1, w = wings[i];
      const beat = flap * Math.sin(t * 2 * Math.PI * 9);
      w.rotation.set(-droop * 0.0, Math.PI / 2 - s * (0.42 + spread), 0.2 + beat * 0.9 - droop * 0.5);
    }
  }
  setWings(0);
  // blood meal: 0..1 -> abdomen inflates into a glossy red balloon
  function setFill(f, glow = 0) {
    abdMat.userData.u.uFill.value = f;
    abdomen.scale.set(1 + 1.9 * f, 1 + 2.1 * f, 1 + 0.35 * f);
    abdomen.rotation.x = 0.12 * f;
    for (const c of cardMeshes) if (c.parent === abdomen) c.visible = !xray && f < 0.35;
    core.visible = glow > 0.01; core.material.opacity = glow;
    core.position.set(0, -0.1, -1.2); core.scale.set(0.24 * (0.4 + 0.6 * f), 0.22 * (0.4 + 0.6 * f), 1.0 * (0.4 + 0.6 * f));
  }
  // x-ray: fresnel shell on every surface, wings/cards hidden, optional trachea
  const xMat = XRAY_SHELL(0x6fc4ff);
  const solid = new Map(); [body, head, abdMesh, ...legMeshes, ...eyes.children].forEach(m => solid.set(m, m.material));
  let xray = false;
  function setXray(on, col = 0x6fc4ff, k = 1) {
    xray = on; xMat.userData.u.uCol.value.set(col); xMat.userData.u.uK.value = k;
    for (const [m, mat] of solid) m.material = on ? xMat : mat;
    for (const w of wings) w.visible = !on;
    for (const c of cardMeshes) c.visible = !on && !(c.parent === abdomen && abdMat.userData.u.uFill.value >= 0.35);
  }
  return { group, root, body, head: headPivot, abdomen, wings, legs: legMeshes, setWings, setLegs, setFill, setXray, trachea: tracheaGroup, o2, tips: legDefs.map(d => d.pts[d.pts.length - 1]), FOOT, mat: bodyMat, abdMat, core, L, ABD };
}
