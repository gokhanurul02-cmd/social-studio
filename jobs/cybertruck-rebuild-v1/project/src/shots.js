// Shot list and per-time scene state. Everything here is a pure function of time t (seconds).
import * as THREE from 'three';
import { clamp, lerp, range, smooth, smoother, easeInOutCubic, easeOutCubic, mulberry } from './util.js';
import { makeTruck, makeMaterials, HOOKS, TRUCK_HALF_LEN } from './truck.js';
import { makeBaby, makeStrongman, bakeCrowdBabies } from './characters.js';
import { SnakeHerd, RopeSnake, Ropes, makeSplats, snakeCenter, snakeHeading, snakeProfile } from './props.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

// time-keyed non-uniform Catmull-Rom (cubic Hermite) for arrays of numbers
export function spline(keys) {
  const n = keys.length;
  const tang = keys.map((k, i) => {
    if (k.hold) return k.v.map(() => 0);
    const a = keys[Math.max(0, i - 1)], b = keys[Math.min(n - 1, i + 1)];
    if (i === 0 || i === n - 1) return k.v.map(() => 0);
    return k.v.map((_, j) => (b.v[j] - a.v[j]) / (b.t - a.t));
  });
  return t => {
    if (t <= keys[0].t) return keys[0].v.slice();
    if (t >= keys[n - 1].t) return keys[n - 1].v.slice();
    let i = 0; while (t > keys[i + 1].t) i++;
    const k0 = keys[i], k1 = keys[i + 1], h = k1.t - k0.t;
    let u = (t - k0.t) / h;
    if (k1.ease) u = k1.ease(u);
    const u2 = u * u, u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
    return k0.v.map((a, j) => h00 * a + h10 * h * tang[i][j] + h01 * k1.v[j] + h11 * h * tang[i + 1][j]);
  };
}
// camera keys: [t, px,py,pz, tx,ty,tz, fov, aperture, roll]
function camSpline(rows) { return spline(rows.map(r => ({ t: r[0], v: r.slice(1, 10), hold: r[10] === 'hold', ease: r[11] }))); }

export const AMBUSH_ORIGIN = V(1000, 0, 0);

export class World {
  constructor(scene, env) {
    this.scene = scene; this.env = env;
    const M = makeMaterials();
    this.trucks = new THREE.Group();
    this.truckL = makeTruck(M); this.truckR = makeTruck(M);
    this.truckL.position.set(-1.12, 0, -TRUCK_HALF_LEN); this.truckR.position.set(1.12, 0, -TRUCK_HALF_LEN);
    this.trucks.add(this.truckL, this.truckR); scene.add(this.trucks);

    this.baby = makeBaby(); scene.add(this.baby.group);
    this.ambushBabies = [];
    for (let i = 0; i < 7; i++) { const b = makeBaby(); scene.add(b.group); this.ambushBabies.push(b); }

    // crowd: 4 baked crawl phases, instanced
    const phases = this._phases;
    const crowdMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55 });
    this.crowdMeshes = phases.map(g => { const m = new THREE.InstancedMesh(g, crowdMat, 5200); m.frustumCulled = false; m.castShadow = true; m.receiveShadow = true; scene.add(m); return m; });
    this.crowd = this.layoutCrowd();

    this.ropes = new Ropes(5600); scene.add(this.ropes.mesh);
    this.herd = new SnakeHerd(180); scene.add(this.herd.group);
    this.herdLayout = this.layoutHerd();
    this.ambushHerd = new SnakeHerd(8); scene.add(this.ambushHerd.group);

    this.man = makeStrongman(); scene.add(this.man.group);
    this.half = makeStrongman({ half: true }); scene.add(this.half.group);
    this.ropeSnakes = [0, 1, 2, 3].map(() => { const r = new RopeSnake(0.075); scene.add(r.group); return r; });
    this.splats = makeSplats(40); scene.add(this.splats);
    this.cams = this.defineCameras();
  }

  hideAll() {
    for (const o of [this.trucks, this.baby.group, ...this.ambushBabies.map(b => b.group), ...this.crowdMeshes, this.ropes.mesh,
      this.herd.group, this.ambushHerd.group, this.man.group, this.half.group, ...this.ropeSnakes.map(r => r.group), this.splats]) o.visible = false;
    this.env.groundMat.userData.uniforms.gCentreOn.value = 1;
    this.env.groundMat.color.set(0x26b4f0); this.env.groundMat.userData.uniforms.gLineAlpha.value = 0.92; this.env.groundMat.userData.uniforms.gCell.value = 0.5; this.env.groundMat.userData.uniforms.gLine.value = 0.028; this.env.groundMat.userData.uniforms.gCrowd.value = 0;
  }

  // ------------------------------------------------------------ layouts
  layoutCrowd() {
    const rnd = mulberry(11), out = [];
    const sp = 0.66;
    for (let row = 0; out.length < 4999; row++) {
      const z = 1.45 + row * sp * 0.92;
      const half = 1.9 + (z - 1.45) * 0.21;
      const n = Math.max(1, Math.round(half * 2 / sp));
      for (let i = 0; i < n && out.length < 4999; i++) {
        const x = -half + (i + 0.5) * (2 * half / n) + (rnd() - 0.5) * 0.12;
        if (row === 0 && Math.abs(x) < 0.45) continue; // hero baby slot
        out.push({ x, z: z + (rnd() - 0.5) * 0.12, yaw: (rnd() - 0.5) * 0.3, ph: rnd(), hook: x < 0 ? (x < -1.1 ? 0 : 1) : (x > 1.1 ? 3 : 2) });
      }
    }
    return out; // + hero = 5000
  }
  layoutHerd() {
    const rnd = mulberry(23), out = [];
    out.push({ x: 0, head: 3.6 });
    for (let row = 1; out.length < 160; row++) {
      const z = 19.5 + (row - 1) * 6.4;
      const half = 1.2 + z * 0.36;
      const n = Math.max(2, Math.round(half * 2 / 2.9));
      for (let i = 0; i < n && out.length < 160; i++) out.push({ x: -half + (i + 0.5) * 2 * half / n + (rnd() - .5) * 0.8, head: z + (rnd() - .5) * 2.0 });
    }
    return out.map((o, i) => ({ ...o, ph: rnd() * 6.28, A: 0.55 + rnd() * 0.25, k: 1.5 + rnd() * 0.3 }));
  }

  // hooks in world space (trucks may roll forward)
  hook(i) {
    const tr = i < 2 ? this.truckL : this.truckR;
    const local = (i % 2 === 0) ? HOOKS[0] : HOOKS[1];
    return tr.localToWorld(local.clone());
  }

  // ------------------------------------------------------------ cameras
  defineCameras() {
    return {
      // [t, px,py,pz, tx,ty,tz, fov, aperture, roll]
      baby: camSpline([
        [0.00, 0, 0.62, 6.55, 0, 0.50, 3.2, 30, 0.06, 0],
        [1.37, 0, 0.61, 6.40, 0, 0.50, 3.2, 30, 0.06, 0, 'hold'],
        [1.74, 0, 2.6, 12.6, 0, 0.95, 0.0, 40, 0.0, 0, 'hold', t => 1 - Math.pow(1 - t, 2.2)],
        [2.30, 0, 2.55, 12.3, 0, 0.95, 0.0, 40, 0.0, 0, 'hold'],
        [2.64, 0, 0.22, 3.75, 0, 0.32, 0.0, 46, 0.012, 0, 'hold', easeInOutCubic],
        [4.05, 0, 0.22, 3.65, 0, 0.33, 0.0, 46, 0.012, 0],
      ]),
      crowd: camSpline([
        [4.05, 0, 0.22, 3.65, 0, 0.33, 0.0, 46, 0.012, 0],
        [4.40, 0.2, 0.7, 6.6, 0, 0.45, 0.0, 50, 0.0, 0.0],
        [5.00, 0.0, 3.0, 20.5, 0, 0.25, 0.0, 48, 0, 0],
        [6.00, 0.6, 8.2, 47, 0, 0.0, 4.0, 46, 0, -0.02],
        [7.40, 6.5, 14.5, 98, -1.0, 0.0, 14, 44, 0, -0.06],
        [8.00, 7.0, 15.0, 102, -1.2, 0.0, 15, 44, 0, -0.07],
      ]),
      ambush: camSpline([
        [7.80, -0.9, 1.30, 2.9, 0.5, 0.10, -0.7, 50, 0, 0.0],
        [8.55, -0.1, 1.05, 2.5, 1.3, 0.25, -0.8, 50, 0, 0.0],
        [9.20, 1.6, 0.62, 2.7, 3.0, 0.40, -1.0, 52, 0, 0.0],
        [10.60, 4.6, 0.72, 3.0, 6.2, 0.35, -1.6, 52, 0, 0.0],
      ]),
      snakes: camSpline([
        [10.25, 0, 3.0, 17.2, 0, 0.6, 2.0, 36, 0, 0],
        [11.25, 0, 2.95, 16.8, 0, 0.6, 2.0, 36, 0, 0, 'hold'],
        [12.50, 0, 5.6, 35, 0, 0.0, 5, 44, 0, 0],
        [14.80, 0, 10.0, 66, 0, 0.0, 10, 44, 0, 0.0],
        [15.40, 0.3, 11.2, 73, 0, 0.0, 12, 44, 0, 0.03],
        [15.75, 0.3, 9.0, 55, 0, 0.0, 6, 50, 0, 0.05],
      ]),
      rock: camSpline([
        [15.45, 0.25, 1.62, 4.55, 0.05, 1.42, 3.3, 52, 0, 0],
        [16.12, 0.15, 1.62, 4.75, 0.0, 1.40, 3.3, 52, 0, 0, 'hold'],
        [16.45, 0.0, 1.68, 5.25, 0.0, 0.95, 1.1, 50, 0, 0, 'hold', easeOutCubic],
        [17.55, 0.0, 1.66, 5.15, 0.0, 0.92, 1.1, 50, 0, 0, 'hold'],
        [19.05, 0.15, 1.56, 5.75, 0.0, 0.96, 1.9, 50, 0, 0],
        [19.50, -3.1, 2.55, 7.6, -0.5, 0.75, 2.3, 50, 0, 0, 'hold', easeInOutCubic],
        [22.20, -3.0, 2.45, 8.6, -0.6, 0.70, 3.5, 50, 0, 0],
      ]),
    };
  }

  // ------------------------------------------------------------ shot application
  // returns camera state; sets visibility/poses
  apply(shot, t) {
    this.hideAll();
    const cam = this.cams[shot] ? this.cams[shot](t) : [0, 1, 5, 0, 0, 0, 40, 0, 0];
    const state = { pos: V(cam[0], cam[1], cam[2]), target: V(cam[3], cam[4], cam[5]), fov: cam[6], aperture: cam[7], roll: cam[8], exposure: 1.0 };
    this['shot_' + shot](t, state);
    return state;
  }

  setTrucks(dz) { this.trucks.visible = true; this.trucks.position.set(0, 0, dz); for (const tr of [this.truckL, this.truckR]) for (const w of tr.userData.wheels) w.rotation.x = dz / 0.445; this.trucks.updateMatrixWorld(true); }

  heroBabyRopes(baby, extraSlack = 0) {
    const sp = baby.bones.Spine1.getWorldPosition(V(0, 0, 0));
    const a = sp.clone(); a.y = Math.max(a.y, 0.12);
    this.ropes.addSag(a, this.hook(0), 0.011, extraSlack, 4);
    this.ropes.addSag(a, this.hook(3), 0.011, extraSlack, 4);
  }

  shot_baby(t, st) {
    this.setTrucks(0);
    const b = this.baby; b.group.visible = true;
    const bz = t < 2.47 ? 3.2 : 1.45;
    b.group.position.set(0, 0, bz); b.group.rotation.set(0, 0, 0);
    b.material.userData.u.uHarness.value = t >= 0.30 ? 1 : 0;
    if (t < 1.40) {
      const rub = 1 - smooth(range(t, 0.22, 0.40));
      const spread = smooth(range(t, 0.30, 0.55)) * (1 - smooth(range(t, 0.95, 1.25)) * 0.6);
      const look = smooth(range(t, 0.95, 1.25));
      b.pose('stand', t, { rub, spread, look });
    } else if (t < 1.62) {
      const u = smooth(range(t, 1.40, 1.62));
      b.pose('stand', t, { look: 1 - u }); const A = capture(b);
      b.pose('crawl', t, { strain: 0.2 }); const B = capture(b);
      blend(b, A, B, u);
    } else {
      b.pose('crawl', t * 0.9, { strain: t > 2.4 ? 0.9 : 0.3, rate: 1.3 });
      b.group.position.z = bz + (t > 2.6 ? (t - 2.6) * 0.04 : 0);
    }
    b.group.updateMatrixWorld(true);
    this.ropes.mesh.visible = t >= 0.88; this.ropes.begin();
    if (t >= 0.88) this.heroBabyRopes(b, t < 1.0 ? 0.25 * (1 - range(t, 0.88, 1.0)) : 0);
    this.ropes.end();
    st.focus = st.pos.distanceTo(V(0, 0.45, b.group.position.z));
    this.env.setShadowArea(V(0, 0, 1), 9);
  }

  shot_crowd(t, st) {
    this.setTrucks(0);
    const b = this.baby; b.group.visible = true; b.group.position.set(0, 0, 1.45 + (t - 2.6) * 0.04);
    b.material.userData.u.uHarness.value = 1;
    b.pose('crawl', t * 0.9, { strain: 0.9, rate: 1.3 });
    b.group.updateMatrixWorld(true);
    const reveal = 1; // the crowd is behind the camera at the start of the pull-back
    const per = this.crowdMeshes.map(() => 0);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = V(1, 1, 1), p = V(0, 0, 0), up = V(0, 1, 0);
    const ropes = this.ropes; ropes.mesh.visible = true; ropes.begin();
    this.heroBabyRopes(b);
    const hooks = [0, 1, 2, 3].map(i => this.hook(i));
    const back = V(0, 0, 0);
    for (const c of this.crowd) {
      const ph = (t * 1.3 + c.ph) % 1;
      const k = Math.floor(ph * 4) % 4;
      const bob = 0.015 * Math.sin(ph * Math.PI * 2);
      p.set(c.x, bob, c.z + (t - 2.6) * 0.04);
      q.setFromAxisAngle(up, c.yaw);
      m.compose(p, q, s);
      this.crowdMeshes[k].setMatrixAt(per[k]++, m);
      back.set(c.x, 0.30, p.z - 0.12);
      ropes.add(back, hooks[c.hook], 0.0062);
    }
    ropes.end();
    this.crowdMeshes.forEach((mm, i) => { mm.visible = true; mm.count = per[i]; mm.instanceMatrix.needsUpdate = true; });
    this.env.setShadowArea(V(0, 0, 12), 30);
    this.env.groundMat.userData.uniforms.gCrowd.value = 1;
    st.focus = 6;
  }

  shot_ambush(t, st) {
    // Babies crawl toward the oncoming anacondas (ropes trail back to the trucks). Each hunting snake
    // slows on contact, gapes, and slides forward over its baby head-first: every part of the baby that is
    // behind the moving mouth plane is clipped (colour + shadow), against a dark throat, then the jaw closes
    // and a bulge travels down the body. Stylised, non-graphic: no wounds, no blood.
    const O = AMBUSH_ORIGIN;
    this.env.groundMat.userData.uniforms.gCentreOn.value = 0;
    const UP = V(0, 1, 0);
    const dir = V(1, 0, 0.32).normalize();              // snakes travel +dir (screen right, slightly toward camera)
    const yaw = Math.atan2(-dir.z, dir.x);
    const ropeEnd = O.clone().add(dir.clone().multiplyScalar(80)).add(V(0, 0.5, 0));
    const L = 8, MOUTH_X = 1.7, MOUTH_Y = -0.12;        // mouth plane in head-local units (hr)
    const SW = 0.85;                                   // swallow duration (s) during which the snake slows
    // hunting snakes: lane offset (along, lateral) relative to O at t=7.8, speeds, contact time te
    const hunters = [
      { o: [-13.5, 1.35], v0: 5.0, R: 0.42, A: 0.35, k: 1.0, ph: 0.4, te: null },  // huge foreground pass
      { o: [-9.0, 0.0], v0: 3.0, R: 0.27, A: 0.30, k: 1.3, ph: 0.0, te: 8.42 },
      { o: [-9.4, -1.0], v0: 3.0, R: 0.25, A: 0.28, k: 1.3, ph: 1.0, te: 9.55 },
      { o: [-8.6, -2.6], v0: 3.1, R: 0.24, A: 0.28, k: 1.4, ph: 2.0, te: 9.95 },
      { o: [-7.4, -3.6], v0: 3.0, R: 0.24, A: 0.28, k: 1.4, ph: 2.5, te: 10.25 },
    ];
    const travelOf = (h, tt) => h.v0 * (tt - 7.8) - (h.te ? (h.v0 - 0.8) * clamp(tt - h.te, 0, SW) : 0);
    const herd = this.ambushHerd; herd.group.visible = true; herd.lanes.length = 0;
    const laneOrigin = h => O.clone().add(dir.clone().multiplyScalar(h.o[0])).add(V(-dir.z, 0, dir.x).multiplyScalar(h.o[1]));
    // mouth frame of a lane at time tt (world): centre point and forward axis
    const mouthAt = (h, tt) => {
      const p = { L, A: h.A, k: h.k, ph: h.ph, R: h.R }, tr = travelOf(h, tt);
      const c = snakeCenter(p, tr, 1, V(0, 0, 0));
      const op = h.te ? smooth(range(tt, h.te - 0.45, h.te - 0.05)) * (1 - smooth(range(tt, h.te + SW - 0.05, h.te + SW + 0.3))) : 0;
      c.y = h.R * 0.92 + 0.13 * op;
      const hd = snakeHeading(p, tr, 1), hr = h.R * snakeProfile(1) * 1.05;
      const q = new THREE.Quaternion().setFromAxisAngle(UP, yaw).multiply(new THREE.Quaternion().setFromAxisAngle(UP, -hd)).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), -0.12 * op));
      const fwd = V(1, 0, 0).applyQuaternion(q);
      const pos = c.applyAxisAngle(UP, yaw).add(laneOrigin(h)).add(V(MOUTH_X * hr, MOUTH_Y * hr, 0).applyQuaternion(q));
      return { pos, fwd, hr };
    };
    hunters.forEach(h => {
      const lane = { origin: laneOrigin(h), yaw, p: { L, A: h.A, k: h.k, ph: h.ph, R: h.R }, travel: travelOf(h, t), jaw: 0.06, bulge: [0, 0] };
      if (h.te) {
        const open = smooth(range(t, h.te - 0.45, h.te - 0.05)), close = smooth(range(t, h.te + SW - 0.05, h.te + SW + 0.3));
        lane.lift = 0.13 * open * (1 - close); lane.pitch = -0.12 * open * (1 - close);
        lane.jaw = 0.06 + 0.84 * open * (1 - close) + 0.12 * close * (1 - smooth(range(t, h.te + SW + 0.3, h.te + SW + 0.8)));
        const prog = t - h.te;
        lane.bulge = [1 - (0.75 + 0.18 * Math.max(0, prog)) / L, 0.42 * smooth(range(prog, 0.25, SW))];
      }
      herd.lanes.push(lane);
    });
    herd.update();

    // babies: hunted ones are placed so the hunter's mouth reaches the baby's head exactly at te
    const crawlSpeed = 0.3;
    const others = [V(-3.5, 0, -5.5), V(6.5, 0, -6.0)];
    this.ropes.mesh.visible = true; this.ropes.begin();
    const babyFace = dir.clone().negate();
    const faceYaw = Math.atan2(babyFace.x, babyFace.z);
    let bi = 0;
    const place = (rig, root, caughtBy, idx) => {
      rig.group.visible = true; rig.material.userData.u.uHarness.value = 1;
      rig.group.position.copy(root); rig.group.rotation.set(0, faceYaw, 0);
      const plane = rig.clip || (rig.clip = new THREE.Plane(V(1, 0, 0), 1e6));
      for (const m of [].concat(rig.meshes[0].material)) { m.clippingPlanes = [plane]; m.clipShadows = true; }
      if (caughtBy) {
        const h = caughtBy, m = mouthAt(h, t);
        // keep points in front of the mouth (three.js clips where n·x + c < 0), n = forward
        plane.normal.copy(m.fwd); plane.constant = -plane.normal.dot(m.pos);
        const struggle = t >= h.te ? 0.35 : 1;
        rig.pose('crawl', t * struggle + idx * 0.37, { strain: t >= h.te ? 0.9 : 0.4, rate: 1.4 });
        rig.group.updateMatrixWorld(true);
        if (t > h.te + SW + 0.05) rig.group.visible = false;   // fully inside: nothing left to draw
      } else {
        plane.normal.set(1, 0, 0); plane.constant = 1e6;
        rig.pose('crawl', t + idx * 0.37, { strain: 0.4, rate: 1.4 });
        rig.group.updateMatrixWorld(true);
      }
      const a = rig.bones.Spine1.getWorldPosition(V(0, 0, 0));
      if (caughtBy && plane.distanceToPoint(a) < 0) a.copy(mouthAt(caughtBy, t).pos); // rope now trails out of the mouth
      if (rig.group.visible || caughtBy) this.ropes.add(a, ropeEnd, 0.012);
    };
    hunters.forEach(h => {
      if (!h.te) return;
      const rig = this.ambushBabies[bi]; const cap = mouthAt(h, h.te);
      const headOff = 0.3;                              // baby root is behind its head (away from the snake)
      const rootCap = cap.pos.clone().addScaledVector(dir, headOff); rootCap.y = 0;
      const root = t < h.te ? rootCap.clone().addScaledVector(dir, crawlSpeed * (h.te - t)) : rootCap;
      place(rig, root, h, bi); bi++;
    });
    others.forEach(p => { const rig = this.ambushBabies[bi]; const root = O.clone().add(p).addScaledVector(babyFace, crawlSpeed * (t - 7.8)); place(rig, root, null, bi); bi++; });
    for (; bi < this.ambushBabies.length; bi++) this.ambushBabies[bi].group.visible = false;
    this.ropes.end();
    // camera anchored on the two hero captures (keeps the reference composition when lanes are retimed)
    const B0 = mouthAt(hunters[1], hunters[1].te).pos.setY(0), B1 = mouthAt(hunters[2], hunters[2].te).pos.setY(0);
    const perp = V(-dir.z, 0, dir.x);                    // toward the camera side
    const key = (B, a, side, h, ta, th) => ({ p: B.clone().addScaledVector(dir, a).addScaledVector(perp, side).add(V(0, h, 0)), t: B.clone().addScaledVector(dir, ta).add(V(0, th, 0)) });
    const K = [
      [7.8, key(B0, 0.35, 2.3, 1.55, 0.25, 0.15)],
      [8.45, key(B0, -0.05, 1.8, 1.12, 0.1, 0.25)],
      [8.95, key(B0, 0.55, 1.45, 0.8, 0.6, 0.3)],
      [9.35, key(B1, -0.7, 3.05, 1.12, 0.25, 0.28)],
      [10.6, key(B1, 1.0, 2.95, 1.08, 1.3, 0.3)],
    ];
    let k = 0; while (k < K.length - 2 && t > K[k + 1][0]) k++;
    const u = easeInOutCubic(range(t, K[k][0], K[k + 1][0]));
    st.pos.lerpVectors(K[k][1].p, K[k + 1][1].p, u); st.target.lerpVectors(K[k][1].t, K[k + 1][1].t, u);
    st.fov = 52; st.aperture = 0; st.roll = 0;
    this.env.setShadowArea(B0.clone().addScaledVector(dir, 1.5), 14);
    st.focus = 3;
  }

  shot_snakes(t, st) {
    const roll = t > 15.3 ? (t - 15.3) * 0.3 : 0;
    this.setTrucks(0);
    const herd = this.herd; herd.group.visible = true; herd.lanes.length = 0;
    const yaw = -Math.PI / 2; // lane +x -> world +z
    const L = 6.5, speed = 0.55;
    for (const h of this.herdLayout) {
      const travel = (t - 10.3) * speed;
      const tailZ = h.head - L; // at t = 10.3
      herd.lanes.push({ origin: V(h.x, 0, tailZ), yaw, p: { L, A: h.A * 0.8, k: h.k * 1.15, ph: h.ph, R: 0.13 }, travel, jaw: 0.08 });
    }
    herd.update();
    const ropes = this.ropes; ropes.mesh.visible = true; ropes.begin();
    const hooks = [0, 1, 2, 3].map(i => this.hook(i));
    const nk = V(0, 0, 0);
    herd.lanes.forEach((ln, i) => {
      herd.pointWorld(i, 0.86, nk);
      const hk = hooks[ln.origin.x < -1.3 ? 0 : ln.origin.x < 0 ? 1 : ln.origin.x < 1.3 ? 2 : 3];
      ropes.add(nk, hk, i === 0 ? 0.01 : 0.009);
    });
    ropes.end();
    this.env.setShadowArea(V(0, 0, 18), 36);
    st.focus = 10;
  }

  shot_rock(t, st) {
    const roll = Math.max(0, t - 17.75);
    const truckDz = roll * roll * 0.12 + roll * 0.15; // trucks start rolling once he pulls
    this.setTrucks(truckDz);
    const man = this.man; man.group.visible = true;
    const Z0 = 1.35;
    if (!this._restEnds) { // where the hands reach the ground at the deepest bend: the snake heads lie there
      man.pose('bend', 17.1, { amount: 1 }); man.group.position.set(0, 0, Z0); man.group.updateMatrixWorld(true);
      this._restEnds = [man.bones.LeftHand, man.bones.RightHand].map(b => { const p = b.getWorldPosition(V(0, 0, 0)); p.y = 0.07; p.z += 0.08; return p; });
    }
    let z = Z0, x = 0;
    if (t < 16.1) { man.pose('point', t, { reach: 1 }); z = 3.55; }
    else if (t < 16.45) {
      const u = smooth(range(t, 16.1, 16.45));
      man.pose('point', t, { reach: 1 - u }); const A = capture(man);
      man.pose('idle', t); const B = capture(man); blend(man, A, B, u);
      z = lerp(3.55, Z0, u);
    } else if (t < 16.95) man.pose('idle', t);
    else if (t < 17.62) {
      const k = smooth(range(t, 16.86, 17.02)) * (1 - smooth(range(t, 17.3, 17.5)));
      man.pose('bend', t, { amount: k });
      if (t > 17.3) { const A = capture(man); man.pose('pull', t - 17.38, { lean: 0.3, grip: 1 }); const B = capture(man); blend(man, A, B, smooth(range(t, 17.3, 17.55))); }
    } else {
      man.pose('pull', t - 17.38, { lean: 0.32, grip: 1, lookY: t > 19.3 ? 0.25 : 0 });
      const w = t - 17.62; z = Z0 + w * 0.55;
    }
    man.group.position.set(x, 0, z); man.group.rotation.set(0, 0, 0); man.group.updateMatrixWorld(true);

    // half figure appears for "and a half of him"
    const halfOn = t >= 19.25;
    if (halfOn) {
      const h = this.half; h.group.visible = true;
      h.pose('pull', t - 17.0, { lean: 0.0, grip: 0 });
      h.group.position.set(-0.95, 0, z - 0.25); h.group.updateMatrixWorld(true);
    }
    // snake tow ropes from the trucks to his hands (lying on the ground before the pick-up)
    const hands = [man.bones.LeftHand, man.bones.RightHand].map(b => b.getWorldPosition(V(0, 0, 0)));
    const picked = t > 17.12;
    const hookIdx = [3, 0];
    for (let i = 0; i < 2; i++) {
      const rs = this.ropeSnakes[i]; rs.group.visible = true;
      const hk = this.hook(hookIdx[i]); hk.y = 0.5;
      const restEnd = this._restEnds[i].clone();
      const end = picked ? hands[i].clone().add(V(0, -0.02, 0.12)) : restEnd;
      const mid1 = hk.clone().lerp(end, 0.35); mid1.y = 0.08;
      const mid2 = hk.clone().lerp(end, 0.7); mid2.y = Math.min(0.1, end.y * 0.5);
      mid1.x += (i === 0 ? 0.2 : -0.2);
      rs.set([hk, mid1, mid2, end]);
    }
    if (halfOn) {
      const waist = this.half.bones.Spine.getWorldPosition(V(0, 0, 0));
      for (let i = 2; i < 4; i++) {
        const rs = this.ropeSnakes[i]; rs.group.visible = true;
        const hk = this.hook(i === 2 ? 1 : 0); hk.y = 0.5;
        const end = waist.clone().add(V(i === 2 ? 0.16 : -0.16, -0.05, 0.05));
        const m1 = hk.clone().lerp(end, 0.4); m1.y = 0.1;
        const m2 = hk.clone().lerp(end, 0.8); m2.y = end.y * 0.6;
        rs.set([hk, m1, m2, end], false);
      }
      // blood drips trail
      const sp = this.splats; sp.visible = true;
      const m = new THREE.Matrix4(), q = new THREE.Quaternion(); let n = 0;
      sp.userData.rnd.forEach((r, i) => {
        const tz = 19.3 + i * 0.07;
        if (t < tz) return;
        const zz = 1.35 + (tz - 17.62) * 0.55 - 0.25 - 0.1;
        const pos = V(-0.95 + (r[0] - 0.5) * 0.35, 0.004, zz - r[1] * 0.3);
        q.setFromAxisAngle(V(0, 1, 0), r[2] * 6.28);
        const sz = 0.025 + r[3] * 0.06 * smooth(range(t, tz, tz + 0.2));
        m.compose(pos, q, V(sz * (1.0 + r[1]), 1, sz));
        sp.setMatrixAt(n++, m);
      });
      sp.count = n; sp.instanceMatrix.needsUpdate = true;
    }
    this.env.setShadowArea(V(0, 0, 2), 8);
    this.env.groundMat.color.set(0x8ad6f0); this.env.groundMat.userData.uniforms.gLineAlpha.value = 0.85; this.env.groundMat.userData.uniforms.gCell.value = 0.34; this.env.groundMat.userData.uniforms.gLine.value = 0.02;
    st.focus = st.pos.distanceTo(V(0, 1.3, z));
    st.exposure = 1.05;
  }
}

// pose capture / blend helpers
function capture(rig) { return { q: rig.boneList.map(b => b.quaternion.clone()), p: rig.boneList.map(b => b.position.clone()), root: rig.root.position.clone() }; }
function blend(rig, A, B, u) {
  rig.boneList.forEach((b, i) => { b.quaternion.slerpQuaternions(A.q[i], B.q[i], u); b.position.lerpVectors(A.p[i], B.p[i], u); });
  rig.root.position.lerpVectors(A.root, B.root, u);
}

// ------------------------------------------------------------ timeline
// shots and transitions (times in seconds)
export const TIMELINE = {
  shots: [
    { id: 'baby', a: 0, b: 4.05 },
    { id: 'crowd', a: 4.05, b: 7.905 },
    { id: 'ambush', a: 7.905, b: 10.41 },
    { id: 'snakes', a: 10.41, b: 15.58 },
    { id: 'rock', a: 15.58, b: 99 },
  ],
  flips: [{ a: 7.785, mid: 7.905, b: 8.09, from: 'crowd', to: 'ambush' }, { a: 10.29, mid: 10.41, b: 10.60, from: 'ambush', to: 'snakes' }],
  whoosh: [{ a: 15.40, b: 15.78, from: 'snakes', to: 'rock' }],
};

export const SUBTITLES = [
  [1, 'If you'], [9, 'strapped a'], [27, 'baby'], [41, 'to a pair of'], [57, 'Cybertrucks'], [85, 'to pull them'],
  [109, 'you would need'], [128, '5000 of them'], [174, 'just to'], [189, 'make them move'], [224, 'Now if you did'],
  [244, 'the same thing'], [270, 'with anacondas'], [306, 'it would take'], [326, 'at least'], [337, '160'],
  [375, 'of the giant snakes'], [410, 'to pull the truck'], [447, 'But if you got'], [466, 'Dwayne the Rock'],
  [493, 'Johnson'], [509, 'to tow the trucks'], [546, 'you would need'], [563, 'just one'], [581, 'and a half of him'],
  [611, 'to get them'], [631, 'rolling'], [647, null],
];
export function subtitleAt(frame) {
  let cur = null;
  for (const [f, s] of SUBTITLES) if (frame >= f) cur = s;
  return frame < 1 ? null : cur;
}

// debug staging: window.DBG = {rig:'baby'|'man'|'half', pose, t, opts, cam:[px,py,pz,tx,ty,tz,fov]}
World.prototype.shot_debug = function (t, st) {
  const d = window.DBG || {};
  const rig = d.rig === 'man' ? this.man : d.rig === 'half' ? this.half : this.baby;
  rig.group.visible = true; rig.group.position.set(0, 0, 0); rig.group.rotation.set(0, d.yaw || 0, 0);
  if (rig.material.userData.u.uHarness) rig.material.userData.u.uHarness.value = 1;
  if (d.pose) rig.pose(d.pose, d.t ?? t, d.opts || {}); else rig.resetBind();
  rig.group.updateMatrixWorld(true);
  if (d.trucks) this.setTrucks(0);
  const c = d.cam || [2.5, 0.6, 0, 0, 0.4, 0, 40];
  st.pos.set(c[0], c[1], c[2]); st.target.set(c[3], c[4], c[5]); st.fov = c[6]; st.aperture = 0; st.roll = 0;
  this.env.setShadowArea(new THREE.Vector3(0, 0, 0), 4);
};
