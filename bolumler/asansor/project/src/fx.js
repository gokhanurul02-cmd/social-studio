// Effects: deterministic spark showers, comic "bonk" stars, speed arrows with labels, soft glow sprite.
import * as THREE from 'three';
import { mulberry, clamp } from './util.js';
import { canvasTex } from './mats.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export class Sparks {
  constructor(n = 600, seed = 3) {
    this.n = n;
    const g = new THREE.CylinderGeometry(0.5, 0.5, 1, 5, 1); g.translate(0, -0.5, 0);   // streak hangs behind its head
    const m = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    this.mesh = new THREE.InstancedMesh(g, m, n); this.mesh.frustumCulled = false; this.mesh.renderOrder = 9;
    this.mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(n * 3), 3);
    const r = mulberry(seed);
    this.p = Array.from({ length: n }, () => ({ a: r(), u: r(), v: r(), w: r(), s: r(), l: r() }));
    this.m4 = new THREE.Matrix4(); this.q = new THREE.Quaternion(); this.c = new THREE.Color();
    this.glow = makeGlow(); this.glow.visible = false;
  }
  // o: { t0, dur, origin (Vector3 | fn(te)->Vector3), dir (Vector3), spread (rad), speed, gravity, life, width, k, count }
  update(t, o) {
    const { t0, dur = 0.6, dir = V(0, 1, 0), spread = 0.8, speed = 4, gravity = -9.8, life = 0.5, width = 0.0025, k = 1, count = this.n, base = V(0, 0, 0) } = o;
    const D = dir.clone().normalize(), U = Math.abs(D.y) < 0.9 ? V(0, 1, 0).cross(D).normalize() : V(1, 0, 0).cross(D).normalize(), W = D.clone().cross(U);
    const up = V(0, 1, 0); let alive = 0; const glowAt = V(0, 0, 0);
    for (let i = 0; i < this.n; i++) {
      const P = this.p[i], te = t0 + P.a * dur, age = t - te, L = life * (0.4 + 0.9 * P.l);
      if (i >= count || age < 0 || age > L) { this.m4.makeScale(0, 0, 0); this.mesh.setMatrixAt(i, this.m4); continue; }
      const org = typeof o.origin === 'function' ? o.origin(te) : o.origin;
      const th = spread * Math.sqrt(P.u), ph = P.v * Math.PI * 2, sp = speed * (0.35 + 0.9 * P.s);
      const vd = D.clone().multiplyScalar(Math.cos(th)).addScaledVector(U, Math.sin(th) * Math.cos(ph)).addScaledVector(W, Math.sin(th) * Math.sin(ph)).multiplyScalar(sp).add(base);
      const pos = org.clone().addScaledVector(vd, age); pos.y += 0.5 * gravity * age * age;
      const vel = vd.clone(); vel.y += gravity * age;
      const len = clamp(vel.length() * 0.012, 0.004, 0.09) * (0.6 + 0.6 * P.w);
      this.q.setFromUnitVectors(up, vel.clone().normalize().negate());
      const wd = width * (0.4 + 0.6 * P.w);
      this.m4.compose(pos, this.q, V(wd, len, wd)); this.mesh.setMatrixAt(i, this.m4);
      const f = age / L, heat = 1 - f;
      this.c.setRGB(1.0, 0.28 + 0.42 * heat * heat * heat, 0.03 + 0.3 * Math.pow(heat, 6)).multiplyScalar((1.4 + 4.0 * heat * heat) * k * (0.6 + 0.8 * P.l));
      this.mesh.setColorAt(i, this.c); alive++;
      if (age < 0.05) glowAt.copy(org);
    }
    this.mesh.instanceMatrix.needsUpdate = true; this.mesh.instanceColor.needsUpdate = true;
    this.mesh.visible = alive > 0;
    return alive;
  }
}

export function makeGlow(col = 0xffa040) {
  const tex = canvasTex(128, 128, (g, w, h) => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.15, 'rgba(255,220,160,0.8)'); gr.addColorStop(0.5, 'rgba(255,140,40,0.18)'); gr.addColorStop(1, 'rgba(255,100,20,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, color: col, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  s.renderOrder = 10; return s;
}

// 5-point star, extruded + bevelled, glossy yellow
export function makeStars(n = 5) {
  const sh = new THREE.Shape();
  for (let i = 0; i < 10; i++) { const a = Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 0.42 : 1; const x = Math.cos(a) * r, y = Math.sin(a) * r; i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
  sh.closePath();
  const g = new THREE.ExtrudeGeometry(sh, { depth: 0.25, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.1, bevelSegments: 4 }); g.center();
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffd21a, emissive: 0xff9a00, emissiveIntensity: 0.35, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.08 });
  const group = new THREE.Group(); const stars = [];
  for (let i = 0; i < n; i++) { const s = new THREE.Mesh(g, m); s.castShadow = false; group.add(s); stars.push(s); }
  function update(t, center, k, R = 0.17, size = 0.032) {
    group.visible = k > 0.01;
    stars.forEach((s, i) => {
      const a = t * 5.5 + i * Math.PI * 2 / n;
      s.position.set(center.x + Math.cos(a) * R, center.y + 0.05 * Math.sin(a * 2 + i), center.z + Math.sin(a) * R * 0.75);
      s.rotation.set(0.3, -a + Math.PI / 2, t * 3 + i); s.scale.setScalar(size * k * (0.85 + 0.25 * Math.sin(i * 1.7)));
    });
  }
  return { group, update };
}

// big arrow (+Y direction, base at origin) with a text label plate
export function makeArrow(color, len, width = 0.22) {
  const hw = width / 2, hl = Math.min(len * 0.45, width * 1.25), sh = new THREE.Shape();
  sh.moveTo(-hw * 0.55, 0); sh.lineTo(hw * 0.55, 0); sh.lineTo(hw * 0.55, len - hl); sh.lineTo(hw, len - hl); sh.lineTo(0, len); sh.lineTo(-hw, len - hl); sh.lineTo(-hw * 0.55, len - hl); sh.closePath();
  const g = new THREE.ExtrudeGeometry(sh, { depth: width * 0.25, bevelEnabled: true, bevelThickness: width * 0.06, bevelSize: width * 0.05, bevelSegments: 5 });
  g.translate(0, 0, -width * 0.125);
  const m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.05, emissive: color, emissiveIntensity: 0.12 });
  const mesh = new THREE.Mesh(g, m); mesh.castShadow = true; return mesh;
}
export function makeLabel(lines, { w = 1024, h = 256, size = 92, color = '#ffffff' } = {}) {
  const tex = canvasTex(w, h, (g) => {
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
    lines.forEach((L, i) => {
      const fs = i === 0 ? size : size * 0.72, y = h / 2 + (i - (lines.length - 1) / 2) * size * 1.05;
      g.font = `bold ${fs}px Verdana`; g.lineWidth = fs * 0.16; g.strokeStyle = 'rgba(0,0,0,0.95)'; g.strokeText(L, w / 2, y); g.fillStyle = i === 0 ? color : '#ffffff'; g.fillText(L, w / 2, y);
    });
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, h / w), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false }));
  m.renderOrder = 11; return m;
}
