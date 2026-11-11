// Macro steel wire rope that snaps wire by wire: 8 helical strands of 7 wires around a 7-wire core strand.
// Local frame: rope axis along +Y, break plane at y = 0, visible length +-L.  update(u, sep, t):
//   u   0..1 snap progress (wires part one by one, the torn ends curl outwards)
//   sep 0..1 the upper half recoils upwards (the rope is under tension)
import * as THREE from 'three';
import { Tube, proc } from './mats.js';
import { mulberry, smooth, clamp } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildRopeSnap({ L = 0.16, n = 46, lay = 0.09, seed = 5, Rr = 0.0065 } = {}) {
  const group = new THREE.Group();
  const mat = proc(new THREE.MeshPhysicalMaterial({ color: 0x9a9da1, metalness: 1, roughness: 0.32 }), 'wire', {
    ropeAttr: true,
    color: '{ float g = vnoise3(vec3(vRU.x * 900.0, vRU.y * 3.0, 0.0)); float d = vnoise3(vec3(vRU.x * 40.0, 0.0, 3.0)); diffuseColor.rgb *= (0.7 + 0.35 * g) * (0.75 + 0.3 * d); _H = g * 0.00002; }',
    rough: 'roughnessFactor = 0.25 + 0.3 * vnoise3(vec3(vRU.x * 60.0, vRU.y * 2.0, 7.0));',
  });
  const tipMat = new THREE.MeshPhysicalMaterial({ color: 0xe8e6e0, metalness: 1, roughness: 0.15 });
  const rnd = mulberry(seed);
  const Rs = Rr * 0.68, rs = Rr * 0.3, rw = rs * 0.34, off = rs - rw;
  const wires = [];
  for (let k = 0; k <= 8; k++) for (let j = 0; j < 7; j++) {
    const core = k === 8;
    const W = { k, j, core, bt: core ? 0.75 + 0.2 * rnd() : 0.05 + 0.85 * rnd(), amp: 0.6 + 0.8 * rnd(), side: rnd() - 0.5, curl: rnd(), halves: [] };
    for (const sg of [-1, 1]) {
      const t = new Tube(n, 8, rw * (j === 0 ? 1.15 : 1.12), true);
      const m = new THREE.Mesh(t.geo, mat); m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; group.add(m);
      W.halves.push({ sg, t, m });
    }
    wires.push(W);
  }
  // bright fresh fracture caps at the torn ends (tiny spheres)
  const caps = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), tipMat, wires.length * 2); caps.frustumCulled = false; group.add(caps);
  const m4 = new THREE.Matrix4();
  function centre(W, y) {
    const phi = (W.core ? 0 : W.k / 8 * Math.PI * 2) + y / lay * Math.PI * 2 * (W.core ? 0 : 1);
    const R = W.core ? 0 : Rs;
    const er = V(Math.cos(phi), 0, Math.sin(phi)), et = V(-Math.sin(phi), 0, Math.cos(phi));
    const psi = W.j / 6 * Math.PI * 2 - y / (lay * 0.38) * Math.PI * 2;
    const o = W.j === 0 ? 0 : off;
    const c = er.clone().multiplyScalar(R).addScaledVector(er, o * Math.cos(psi)).addScaledVector(et, o * Math.sin(psi) * 0.95).add(V(0, y, 0));
    return { c, er, et };
  }
  function update(u, sep = 0, t = 0) {
    let ci = 0;
    for (const W of wires) {
      const b = smooth(clamp((u - W.bt) / 0.06));
      for (const H of W.halves) {
        const pts = [];
        const recoil = H.sg > 0 ? sep : 0;
        for (let i = 0; i < n; i++) {
          const d = (i / (n - 1)) * L, y = H.sg * d;      // d: distance from the break plane
          const { c, er, et } = centre(W, y);
          // unravel near the break once the strand has lost its neighbours
          const loose = b * Math.exp(-d / 0.009) * W.amp;
          c.addScaledVector(er, 0.0055 * loose * (W.core ? 0.5 : 1)).addScaledVector(et, 0.003 * loose * W.side);
          c.y += H.sg * (0.0012 * b + 0.003 * loose * W.curl);
          // whole-rope opening (strands spread as more wires fail)
          c.addScaledVector(er, 0.0012 * smooth(u) * Math.exp(-d / 0.025));
          if (recoil > 0) { c.y += recoil * 0.45; c.x += Math.sin(t * 31 + d * 40) * 0.006 * recoil * (1 - d / L); }
          pts.push(c);
        }
        H.t.update(pts);
        // fracture cap at the torn end
        const p = pts[0]; const r = b > 0.02 ? rw * 1.05 : 0;
        m4.makeScale(r, r, r).setPosition(p.x, p.y, p.z); caps.setMatrixAt(ci++, m4);
      }
    }
    caps.instanceMatrix.needsUpdate = true;
  }
  update(0, 0, 0);
  return { group, update, wires, L };
}
