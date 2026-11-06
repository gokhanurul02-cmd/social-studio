// Snakes (instanced, vertex-shader slither), snake-ropes (CPU tubes), red ropes (instanced cylinders), blood splats.
import * as THREE from 'three';
import { segmentMatrix, mulberry } from './util.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ------------------------------------------------------------------ textures
function bodySkinTexture() {
  const W = 1024, H = 512, c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d');
  // v: 0 = belly (bottom), 0.5 = back (top)
  const g = x.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#c9b24a'); g.addColorStop(0.16, '#3d3a1c'); g.addColorStop(0.26, '#141310');
  g.addColorStop(0.5, '#0f0e0c'); g.addColorStop(0.74, '#141310'); g.addColorStop(0.84, '#3d3a1c'); g.addColorStop(1, '#c9b24a');
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  const rnd = mulberry(7);
  // scale texture
  x.globalAlpha = 0.12; x.strokeStyle = '#000';
  for (let i = 0; i < W; i += 10) for (let j = 0; j < H; j += 10) { x.beginPath(); x.arc(i + (j % 20 ? 5 : 0), j, 5, 0, Math.PI); x.stroke(); }
  x.globalAlpha = 1;
  // sparse large yellow ovals on the flanks, a few small ones near the belly line
  const spot = (cx, cy, rx, ry, col) => { for (const ox of [-W, 0, W]) { x.beginPath(); x.ellipse(cx + ox, cy, rx, ry, 0, 0, Math.PI * 2); x.fillStyle = col; x.fill(); } };
  for (let i = 0; i < 4; i++) {
    const u = (i + 0.5) / 4 * W;
    spot(u + rnd() * 30, 0.36 * H, 46 + rnd() * 12, 30 + rnd() * 8, '#dcc63a');
    spot(u + W / 8 + rnd() * 30, 0.64 * H, 46 + rnd() * 12, 30 + rnd() * 8, '#dcc63a');
    spot(u + W / 16, 0.5 * H, 22, 16, '#c8b236');
  }
  const t = new THREE.CanvasTexture(c); t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
function headSkinTexture() {
  const W = 512, H = 256, c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d');
  x.fillStyle = '#8e8a3a'; x.fillRect(0, 0, W, H);
  const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(210,200,90,0.8)'); g.addColorStop(0.5, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(210,200,90,0.8)');
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  const rnd = mulberry(3);
  for (let i = 0; i < 16; i++) { // black blotches with yellow centres (ocelli) on the crown and sides
    const cx = rnd() * W * 0.55, cy = H * (0.25 + rnd() * 0.5), r = 10 + rnd() * 16;
    x.beginPath(); x.ellipse(cx, cy, r * 1.2, r, 0, 0, 7); x.fillStyle = '#0d0c08'; x.fill();
    x.beginPath(); x.ellipse(cx, cy, r * 0.55, r * 0.5, 0, 0, 7); x.fillStyle = '#e1cd3d'; x.fill();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

// ------------------------------------------------------------------ instanced slithering snakes
const PROFILE_GLSL = /* glsl */`
float snakeProfile(float s){ return mix(0.12, 1.0, smoothstep(0.0, 0.42, s)) * (1.0 - 0.18*smoothstep(0.86, 0.97, s) - 0.45*smoothstep(0.97, 1.0, s)); }
`;
export function snakeProfile(s) { const sm = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
  return (0.12 + 0.88 * sm(0, 0.42, s)) * (1 - 0.18 * sm(0.86, 0.97, s) - 0.45 * sm(0.97, 1, s)); }

// snake centre-line in its lane frame: x forward, z lateral. stationary wave in lane space.
export function snakeCenter(p, travel, s, out = new THREE.Vector3()) {
  const X = s * p.L + travel;
  const env = 1 - 0.7 * smoothstepJS(0.82, 1, s);
  out.set(X, p.R, p.A * env * Math.sin(p.k * X + p.ph));
  return out;
}
export function snakeHeading(p, travel, s) {
  const X = s * p.L + travel; const env = 1 - 0.7 * smoothstepJS(0.82, 1, s);
  const dz = p.A * env * p.k * Math.cos(p.k * X + p.ph);
  return Math.atan2(dz, 1);
}
function smoothstepJS(a, b, v) { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); }

export class SnakeHerd {
  constructor(capacity, { L = 8, tile = 1.5 } = {}) {
    this.capacity = capacity; this.L = L;
    const SEG = 220, RAD = 18;
    const pos = [], uv = [], idx = [];
    for (let i = 0; i <= SEG; i++) {
      const s = i / SEG;
      for (let j = 0; j <= RAD; j++) {
        const th = j / RAD * Math.PI * 2;
        pos.push(s, -Math.cos(th), Math.sin(th)); // y=-cos so v=0 is the belly
        uv.push(s * L / tile, j / RAD);
      }
    }
    for (let i = 0; i < SEG; i++) for (let j = 0; j < RAD; j++) {
      const a = i * (RAD + 1) + j, b = a + RAD + 1;
      idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
    const g = new THREE.InstancedBufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    this.params = new Float32Array(capacity * 4);   // L, A, k, phase
    this.extra = new Float32Array(capacity * 2);    // travel, radius
    g.setAttribute('iParams', new THREE.InstancedBufferAttribute(this.params, 4));
    g.setAttribute('iExtra', new THREE.InstancedBufferAttribute(this.extra, 2));
    this.bulge = new Float32Array(capacity * 2);    // prey bulge: centre s, amount (fraction of radius)
    g.setAttribute('iBulge', new THREE.InstancedBufferAttribute(this.bulge, 2));
    const mat = new THREE.MeshStandardMaterial({ map: bodySkinTexture(), roughness: 0.42, metalness: 0.0 });
    mat.onBeforeCompile = sh => {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec4 iParams; attribute vec2 iExtra; attribute vec2 iBulge;\n' + PROFILE_GLSL)
        .replace('#include <beginnormal_vertex>', `
          float sS = position.x; float sL = iParams.x, sA = iParams.y, sK = iParams.z, sPh = iParams.w; float sTr = iExtra.x, sR = iExtra.y;
          float sX = sS*sL + sTr;
          float sEnv = 1.0 - 0.7*smoothstep(0.82, 1.0, sS);
          float sZ = sA*sEnv*sin(sK*sX + sPh);
          float sDz = sA*sEnv*sK*cos(sK*sX + sPh);
          vec2 sT = normalize(vec2(1.0, sDz)); vec2 sN = vec2(-sT.y, sT.x);
          float sr = sR*snakeProfile(sS);
          float sbd = (sS - iBulge.x) * sL / 0.42;
          sr *= 1.0 + iBulge.y * exp(-sbd*sbd);
          vec3 objectNormal = normalize(vec3(sN.x*position.z, position.y*1.15, sN.y*position.z));
          #ifdef USE_TANGENT
          vec3 objectTangent = vec3(sT.x, 0.0, sT.y);
          #endif`)
        .replace('#include <begin_vertex>', `vec3 transformed = vec3(sX, sR*0.92, sZ) + vec3(sN.x*position.z*sr, position.y*sr*0.86, sN.y*position.z*sr);`);
    };
    mat.customProgramCacheKey = () => 'snake-body';
    this.body = new THREE.InstancedMesh(g, mat, capacity);
    this.body.frustumCulled = false; this.body.castShadow = true; this.body.receiveShadow = true;
    // heads: upper skull + lower jaw
    const headTex = headSkinTexture();
    const hemi = (up, w, h, d, x, y) => { const gg = new THREE.SphereGeometry(1, 36, 14, 0, Math.PI * 2, up ? 0 : Math.PI / 2, Math.PI / 2); gg.scale(w, h, d); gg.translate(x, y, 0); return gg; };
    const skullG = hemi(true, 1.75, 0.66, 0.95, 0.78, 0.0);
    const jawG = hemi(false, 1.62, 0.44, 0.88, 0.74, 0.0);
    const palateG = hemi(false, 1.68, 0.09, 0.9, 0.78, 0.002);          // roof of the mouth closes the skull
    const tongueG = hemi(true, 1.55, 0.08, 0.82, 0.74, -0.002);           // floor of the mouth closes the jaw
    const throatG = new THREE.SphereGeometry(1, 24, 12); throatG.scale(0.95, 0.5, 0.72); throatG.translate(0.05, -0.05, 0);
    const teeth = (sign) => { const parts = []; for (let i = 0; i < 11; i++) { const x = 0.45 + i * 0.17, zz = 0.8 * Math.sqrt(Math.max(0, 1 - ((x - 0.95) / 1.55) ** 2));
      for (const sz of [1, -1]) { const c = new THREE.ConeGeometry(0.035, 0.13, 6); if (sign > 0) c.rotateX(Math.PI); c.translate(x, sign * -0.06, sz * zz * 0.97); parts.push(c); } } return mergeGeometries(parts); };
    this.skull = new THREE.InstancedMesh(skullG, new THREE.MeshStandardMaterial({ map: headTex, roughness: 0.4 }), capacity);
    this.jaw = new THREE.InstancedMesh(jawG, new THREE.MeshStandardMaterial({ map: headTex, roughness: 0.45 }), capacity);
    const oral = new THREE.MeshStandardMaterial({ color: 0xa8464f, roughness: 0.35 });
    this.palate = new THREE.InstancedMesh(palateG, oral, capacity);
    this.mouth = new THREE.InstancedMesh(tongueG, oral, capacity);
    this.throat = new THREE.InstancedMesh(throatG, new THREE.MeshStandardMaterial({ color: 0x1c0607, roughness: 0.8 }), capacity);
    const toothM = new THREE.MeshStandardMaterial({ color: 0xf2eee2, roughness: 0.3 });
    this.teethU = new THREE.InstancedMesh(teeth(1), toothM, capacity);
    this.teethL = new THREE.InstancedMesh(teeth(-1), toothM, capacity);
    const eyeG = new THREE.SphereGeometry(1, 12, 8);
    this.eyes = new THREE.InstancedMesh(eyeG, new THREE.MeshStandardMaterial({ color: 0x6fb3a8, roughness: 0.1, emissive: 0x0a1a18 }), capacity * 2);
    this.heads = [this.skull, this.jaw, this.palate, this.mouth, this.throat, this.teethU, this.teethL, this.eyes];
    for (const m of this.heads) { m.frustumCulled = false; m.castShadow = true; }
    this.group = new THREE.Group();
    this.group.add(this.body, ...this.heads);
    this.lanes = []; // per snake: {origin: Vector3, yaw, p:{L,A,k,ph,R}, travel, jaw}
  }
  // write instance data for the current lanes
  update() {
    const n = this.lanes.length;
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), c = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    const laneM = new THREE.Matrix4(), headM = new THREE.Matrix4(), tmp = new THREE.Matrix4();
    for (let i = 0; i < n; i++) {
      const ln = this.lanes[i], p = ln.p;
      this.params.set([p.L, p.A, p.k, p.ph], i * 4);
      this.extra.set([ln.travel, p.R], i * 2);
      laneM.compose(ln.origin, q.setFromAxisAngle(up, ln.yaw), s.set(1, 1, 1));
      this.body.setMatrixAt(i, laneM);
      // head frame at s=1
      snakeCenter(p, ln.travel, 1, c);
      const hd = snakeHeading(p, ln.travel, 1);
      const hr = p.R * snakeProfile(1) * 1.05;
      headM.compose(c.setY(p.R * 0.92 + (ln.lift || 0)), q.setFromAxisAngle(up, -hd).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), ln.pitch || 0)), s.set(hr, hr, hr));
      tmp.multiplyMatrices(laneM, headM);
      this.skull.setMatrixAt(i, tmp);
      const jaw = ln.jaw || 0;
      const jm = new THREE.Matrix4().makeRotationZ(-jaw);
      const jt = new THREE.Matrix4().multiplyMatrices(tmp, jm);
      this.jaw.setMatrixAt(i, jt);
      const open = jaw > 0.04, zero = new THREE.Matrix4().makeScale(0, 0, 0);
      this.palate.setMatrixAt(i, tmp); this.mouth.setMatrixAt(i, jt);
      this.throat.setMatrixAt(i, open ? tmp : zero);
      this.teethU.setMatrixAt(i, open ? tmp : zero); this.teethL.setMatrixAt(i, open ? jt : zero);
      this.bulge.set(ln.bulge || [0, 0], i * 2);
      for (const e of [0, 1]) {
        const em = new THREE.Matrix4().compose(new THREE.Vector3(1.45, 0.38, (e ? 1 : -1) * 0.55), new THREE.Quaternion(), new THREE.Vector3(0.14, 0.14, 0.14));
        this.eyes.setMatrixAt(i * 2 + e, new THREE.Matrix4().multiplyMatrices(tmp, em));
      }
      ln._head = tmp.clone();
    }
    this.body.count = n; for (const mm of this.heads) mm.count = n; this.eyes.count = n * 2;
    for (const mm of [this.body, ...this.heads]) mm.instanceMatrix.needsUpdate = true;
    const ga = this.body.geometry.attributes; ga.iParams.needsUpdate = true; ga.iExtra.needsUpdate = true; ga.iBulge.needsUpdate = true;
  }
  // world position of the body centre at s for lane i
  pointWorld(i, s, out = new THREE.Vector3()) {
    const ln = this.lanes[i];
    snakeCenter(ln.p, ln.travel, s, out); out.y = ln.p.R * 0.9;
    out.applyAxisAngle(new THREE.Vector3(0, 1, 0), ln.yaw).add(ln.origin);
    return this.group.localToWorld(out);
  }
}

// ------------------------------------------------------------------ snake used as a tow rope (CPU tube)
export class RopeSnake {
  constructor(radius = 0.07) {
    this.radius = radius;
    this.mat = new THREE.MeshStandardMaterial({ map: bodySkinTexture(), roughness: 0.42 });
    this.mat.map.repeat.set(1, 1);
    this.mesh = new THREE.Mesh(new THREE.BufferGeometry(), this.mat);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true; this.mesh.frustumCulled = false;
    const headTex = headSkinTexture();
    const skullG = new THREE.SphereGeometry(1, 24, 16); skullG.scale(1.55, 0.62, 0.92); skullG.translate(0.95, 0.05, 0);
    this.head = new THREE.Mesh(skullG, new THREE.MeshStandardMaterial({ map: headTex, roughness: 0.4 }));
    this.head.castShadow = true;
    this.group = new THREE.Group(); this.group.add(this.mesh, this.head);
  }
  // pts: array of Vector3 tail->head, headDir: vector the head points along
  set(pts, headVisible = true) {
    const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
    const len = curve.getLength();
    const g = new THREE.TubeGeometry(curve, Math.max(24, Math.round(len * 18)), this.radius, 12, false);
    // taper toward tail
    const P = g.attributes.position, n = P.count, segs = g.parameters.tubularSegments, rad = g.parameters.radialSegments;
    const cp = new THREE.Vector3();
    for (let i = 0; i <= segs; i++) {
      const u = i / segs; curve.getPointAt(u, cp);
      const k = 0.35 + 0.65 * Math.min(1, u * 4);
      for (let j = 0; j <= rad; j++) { const id = i * (rad + 1) + j; P.setXYZ(id, cp.x + (P.getX(id) - cp.x) * k, cp.y + (P.getY(id) - cp.y) * k, cp.z + (P.getZ(id) - cp.z) * k); }
    }
    const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * len / 0.55, uv.getY(i) + 0.25);
    this.mesh.geometry.dispose(); this.mesh.geometry = g;
    const end = curve.getPointAt(1), tan = curve.getTangentAt(1);
    this.head.visible = headVisible;
    this.head.position.copy(end);
    this.head.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), tan.normalize());
    this.head.scale.setScalar(this.radius * 1.15);
    this.length = len;
  }
}

// ------------------------------------------------------------------ red ropes
export class Ropes {
  constructor(capacity, color = 0xc81a2c) {
    const g = new THREE.CylinderGeometry(1, 1, 1, 6, 1, true);
    this.mat = new THREE.MeshStandardMaterial({ color, roughness: 0.5, emissive: 0x200204 });
    this.mesh = new THREE.InstancedMesh(g, this.mat, capacity);
    this.mesh.frustumCulled = false; this.n = 0; this.capacity = capacity;
  }
  begin() { this.n = 0; }
  add(a, b, r) { if (this.n >= this.capacity) return; this.mesh.setMatrixAt(this.n++, segmentMatrix(a, b, r)); }
  // a sagging rope made of several segments
  addSag(a, b, r, sag = 0.0, segs = 6) {
    const p0 = new THREE.Vector3(), p1 = new THREE.Vector3();
    for (let i = 0; i < segs; i++) {
      const u0 = i / segs, u1 = (i + 1) / segs;
      p0.lerpVectors(a, b, u0); p0.y -= sag * 4 * u0 * (1 - u0);
      p1.lerpVectors(a, b, u1); p1.y -= sag * 4 * u1 * (1 - u1);
      this.add(p0, p1, r);
    }
  }
  end() { this.mesh.count = this.n; this.mesh.instanceMatrix.needsUpdate = true; }
}

// ------------------------------------------------------------------ blood drips (flat splats on the ground)
export function makeSplats(count, seed = 5) {
  const rnd = mulberry(seed);
  const g = new THREE.CircleGeometry(1, 14); g.rotateX(-Math.PI / 2);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const k = 0.8 + rnd() * 0.4; p.setXYZ(i, p.getX(i) * k, 0, p.getZ(i) * k); }
  const m = new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ color: 0x6e0a10, roughness: 0.15, metalness: 0.0, polygonOffset: true, polygonOffsetFactor: -2 }), count);
  m.frustumCulled = false; m.receiveShadow = true;
  m.userData.rnd = Array.from({ length: count }, () => [rnd(), rnd(), rnd(), rnd()]);
  return m;
}
