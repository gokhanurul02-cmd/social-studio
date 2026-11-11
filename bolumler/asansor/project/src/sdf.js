// Signed-distance modelling + surface-nets polygoniser (smooth organic props: frog, hearts, gloves).
// Shapes are written as JS distance functions f(x, y, z) -> distance (negative inside).
import * as THREE from 'three';

export const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
export const smax = (a, b, k) => -smin(-a, -b, k);
export const sphere = (x, y, z, cx, cy, cz, r) => Math.hypot(x - cx, y - cy, z - cz) - r;
// axis-aligned ellipsoid (good-enough bound distance)
export function ellipsoid(x, y, z, cx, cy, cz, rx, ry, rz) {
  const px = (x - cx) / rx, py = (y - cy) / ry, pz = (z - cz) / rz;
  const k0 = Math.hypot(px, py, pz), k1 = Math.hypot(px / rx, py / ry, pz / rz);
  return k1 < 1e-9 ? -Math.min(rx, ry, rz) : k0 * (k0 - 1) / k1;
}
// capsule / round cone between a and b with radii ra, rb
export function cone(x, y, z, a, b, ra, rb) {
  const bx = b[0] - a[0], by = b[1] - a[1], bz = b[2] - a[2];
  const px = x - a[0], py = y - a[1], pz = z - a[2];
  const l2 = bx * bx + by * by + bz * bz;
  const h = Math.max(0, Math.min(1, (px * bx + py * by + pz * bz) / l2));
  return Math.hypot(px - bx * h, py - by * h, pz - bz * h) - (ra + (rb - ra) * h);
}
// chain of round cones through points with radii
export function chain(x, y, z, pts, rs, k = 0) {
  let d = 1e9;
  for (let i = 0; i + 1 < pts.length; i++) { const e = cone(x, y, z, pts[i], pts[i + 1], rs[i], rs[i + 1]); d = k ? smin(d, e, k) : Math.min(d, e); }
  return d;
}

// Surface nets over the box [min, max] with cell size h. Returns indexed BufferGeometry with gradient normals.
export function polygonize(f, min, max, h, { relax = 2 } = {}) {
  const nx = Math.ceil((max[0] - min[0]) / h) + 1, ny = Math.ceil((max[1] - min[1]) / h) + 1, nz = Math.ceil((max[2] - min[2]) / h) + 1;
  const V = new Float32Array(nx * ny * nz);
  const id = (i, j, k) => (k * ny + j) * nx + i;
  for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) V[id(i, j, k)] = f(min[0] + i * h, min[1] + j * h, min[2] + k * h);
  const cell = new Int32Array(nx * ny * nz).fill(-1);
  const pos = [];
  const E = [[0, 0, 0, 1, 0, 0], [0, 1, 0, 1, 1, 0], [0, 0, 1, 1, 0, 1], [0, 1, 1, 1, 1, 1], [0, 0, 0, 0, 1, 0], [1, 0, 0, 1, 1, 0], [0, 0, 1, 0, 1, 1], [1, 0, 1, 1, 1, 1], [0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 1], [0, 1, 0, 0, 1, 1], [1, 1, 0, 1, 1, 1]];
  for (let k = 0; k < nz - 1; k++) for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
    let sx = 0, sy = 0, sz = 0, n = 0, neg = 0;
    for (let c = 0; c < 8; c++) if (V[id(i + (c & 1), j + ((c >> 1) & 1), k + (c >> 2))] < 0) neg++;
    if (neg === 0 || neg === 8) continue;
    for (const e of E) {
      const a = V[id(i + e[0], j + e[1], k + e[2])], b = V[id(i + e[3], j + e[4], k + e[5])];
      if ((a < 0) === (b < 0)) continue;
      const t = a / (a - b);
      sx += e[0] + (e[3] - e[0]) * t; sy += e[1] + (e[4] - e[1]) * t; sz += e[2] + (e[5] - e[2]) * t; n++;
    }
    cell[id(i, j, k)] = pos.length / 3;
    pos.push(min[0] + (i + sx / n) * h, min[1] + (j + sy / n) * h, min[2] + (k + sz / n) * h);
  }
  const idx = [];
  const quad = (a, b, c, d, flip) => { if (a < 0 || b < 0 || c < 0 || d < 0) return; if (flip) idx.push(a, c, b, a, d, c); else idx.push(a, b, c, a, c, d); };
  for (let k = 1; k < nz - 1; k++) for (let j = 1; j < ny - 1; j++) for (let i = 1; i < nx - 1; i++) {
    const v0 = V[id(i, j, k)] < 0;
    if (i < nx - 1 && v0 !== (V[id(i + 1, j, k)] < 0)) quad(cell[id(i, j - 1, k - 1)], cell[id(i, j, k - 1)], cell[id(i, j, k)], cell[id(i, j - 1, k)], !v0);
    if (j < ny - 1 && v0 !== (V[id(i, j + 1, k)] < 0)) quad(cell[id(i - 1, j, k - 1)], cell[id(i - 1, j, k)], cell[id(i, j, k)], cell[id(i, j, k - 1)], !v0);
    if (k < nz - 1 && v0 !== (V[id(i, j, k + 1)] < 0)) quad(cell[id(i - 1, j - 1, k)], cell[id(i, j - 1, k)], cell[id(i, j, k)], cell[id(i - 1, j, k)], !v0);
  }
  // project onto the surface + gradient normals
  const nrm = new Float32Array(pos.length), e = h * 0.5;
  for (let v = 0; v < pos.length; v += 3) {
    let x = pos[v], y = pos[v + 1], z = pos[v + 2];
    for (let it = 0; it < relax + 1; it++) {
      const d = f(x, y, z);
      let gx = f(x + e, y, z) - f(x - e, y, z), gy = f(x, y + e, z) - f(x, y - e, z), gz = f(x, y, z + e) - f(x, y, z - e);
      const gl = Math.hypot(gx, gy, gz) || 1; gx /= gl; gy /= gl; gz /= gl;
      if (it < relax) { const s = Math.max(-h, Math.min(h, d)); x -= gx * s; y -= gy * s; z -= gz * s; }
      else { nrm[v] = gx; nrm[v + 1] = gy; nrm[v + 2] = gz; }
    }
    pos[v] = x; pos[v + 1] = y; pos[v + 2] = z;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setIndex(idx);
  return g;
}
