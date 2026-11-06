// Build continuous MakeHuman (CC0) bodies for the rig:
// targets -> T-pose matching the Xbot rest pose -> geometric skin weights on Xbot bone names -> JSON.
// usage: node scripts/build_mh.mjs
import fs from 'fs';
import { readObj, applyTarget, joints as getJoints } from './mh_lib.mjs';

const D = 'assets/makehuman/';
const OUT = 'project/assets/';
const CHARS = {
  baby: { targets: [['caucasian-male-baby', 1], ['universal-male-baby-averagemuscle-maxweight', 1]], height: 0.80 },
  man: { targets: [['caucasian-male-young', 1], ['universal-male-young-maxmuscle-averageweight', 1.6]], height: 1.93,
    bulk: { Arm: 0.028, ForeArm: 0.014, Shoulder: 0.026, Spine2: 0.022, Spine1: 0.011, Neck: 0.009, UpLeg: 0.015, Leg: 0.01, Foot: 0.008 }, head: true },
};

// ---------- small vector helpers
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const len = a => Math.hypot(a[0], a[1], a[2]);
const nrm = a => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
function rotBetween(a, b) { // rotation matrix (row-major 3x3) taking unit a to unit b
  a = nrm(a); b = nrm(b); const v = cross(a, b), c = dot(a, b);
  if (c < -0.9999) return [-1, 0, 0, 0, 1, 0, 0, 0, -1];
  const k = 1 / (1 + c);
  return [v[0] * v[0] * k + c, v[0] * v[1] * k - v[2], v[0] * v[2] * k + v[1],
          v[1] * v[0] * k + v[2], v[1] * v[1] * k + c, v[1] * v[2] * k - v[0],
          v[2] * v[0] * k - v[1], v[2] * v[1] * k + v[0], v[2] * v[2] * k + c];
}
const mulMV = (m, p) => [m[0] * p[0] + m[1] * p[1] + m[2] * p[2], m[3] * p[0] + m[4] * p[1] + m[5] * p[2], m[6] * p[0] + m[7] * p[1] + m[8] * p[2]];
const mulMM = (a, b) => { const r = []; for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) r.push(a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j]); return r; };
const I3 = [1, 0, 0, 0, 1, 0, 0, 0, 1];
// rigid transform {R, t}: p -> R p + t
const xf = (T, p) => add(mulMV(T.R, p), T.t);
const about = (R, pivot) => ({ R, t: sub(pivot, mulMV(R, pivot)) });
const compose = (A, B) => ({ R: mulMM(A.R, B.R), t: add(mulMV(A.R, B.t), A.t) }); // A after B

// ---------- bone table: Xbot name -> [MH head joint, MH tail joint]
function boneTable() {
  const B = {
    Hips: ['@hips', 'spine-3'], Spine: ['spine-3', 'spine-2'], Spine1: ['spine-2', 'spine-1'], Spine2: ['spine-1', 'neck'],
    Neck: ['neck', 'head'], Head: ['head', 'head-2'],
  };
  for (const [S, s] of [['Left', 'l'], ['Right', 'r']]) {
    Object.assign(B, {
      [S + 'Shoulder']: [s + '-clavicle', s + '-shoulder'], [S + 'Arm']: [s + '-shoulder', s + '-elbow'],
      [S + 'ForeArm']: [s + '-elbow', s + '-hand'], [S + 'Hand']: [s + '-hand', s + '-finger-3-1'],
      [S + 'UpLeg']: [s + '-upper-leg', s + '-knee'], [S + 'Leg']: [s + '-knee', s + '-ankle'],
      [S + 'Foot']: [s + '-ankle', s + '-foot-1'], [S + 'ToeBase']: [s + '-foot-1', s + '-foot-2'],
    });
    const fn = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
    fn.forEach((f, k) => { for (let i = 1; i <= 3; i++) B[S + 'Hand' + f + i] = [`${s}-finger-${k + 1}-${i}`, `${s}-finger-${k + 1}-${i + 1}`]; });
  }
  return B;
}
// end bones (positions only, no weights)
function endJoints() {
  const E = { HeadTop_End: 'head-2', LeftEye: 'l-eye', RightEye: 'r-eye' };
  for (const [S, s] of [['Left', 'l'], ['Right', 'r']]) {
    E[S + 'Toe_End'] = s + '-foot-2';
    ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'].forEach((f, k) => { E[S + 'Hand' + f + '4'] = `${s}-finger-${k + 1}-4`; });
  }
  return E;
}
const chainOf = name => {
  const side = name.startsWith('Left') ? 'L' : name.startsWith('Right') ? 'R' : 'C';
  if (/Hand|ForeArm/.test(name)) return side + 'fore';
  if (/Arm$/.test(name)) return side + 'arm';
  if (/UpLeg/.test(name)) return side + 'thigh';
  if (/Leg$|Foot|Toe/.test(name)) return side + 'shin';
  return 'C';
};

function segDist(p, a, b) {
  const ab = sub(b, a), t = Math.max(0, Math.min(1, dot(sub(p, a), ab) / Math.max(1e-9, dot(ab, ab))));
  return len(sub(p, add(a, [ab[0] * t, ab[1] * t, ab[2] * t])));
}

function build(name, cfg) {
  const obj = readObj(D + 'base.obj');
  const v = Float64Array.from(obj.v);
  for (const [t, w] of cfg.targets) applyTarget(v, D + t + '.target', w);
  const J = getJoints(obj, v);
  J['@hips'] = [0, (J['l-upper-leg'][1] + J['pelvis'][1]) / 2 - 0.15 * (J['pelvis'][1] - J['l-knee'][1]) * 0.3, J['pelvis'][2]];
  const P = i => [v[i * 3], v[i * 3 + 1], v[i * 3 + 2]];

  // render groups: body (skin) + eyes
  const bodyFaces = obj.faces.filter(f => f.g === 'body');
  const eyeFaces = obj.faces.filter(f => f.g === 'helper-l-eye' || f.g === 'helper-r-eye');
  const used = new Map(); const order = [];
  const take = i => { if (!used.has(i)) { used.set(i, order.length); order.push(i); } return used.get(i); };
  const tri = (faces) => { const out = []; for (const f of faces) { const q = f.idx.map(take); for (let k = 1; k < q.length - 1; k++) out.push(q[0], q[k], q[k + 1]); } return out; };
  const bodyIdx = tri(bodyFaces); const nBody = order.length;
  const eyeIdx = tri(eyeFaces);
  const N = order.length;

  // ---- weights (in the original A-pose)
  const B = boneTable();
  const names = Object.keys(B);
  const segs = names.map(n => [J[B[n][0]], J[B[n][1]]]);
  const H = J['head-2'][1] - J['ground'][1];
  // bone radii: estimated from vertices nearest to each segment
  const rawNearest = new Int32Array(N);
  for (let k = 0; k < N; k++) {
    const p = P(order[k]); let best = 0, bd = 1e9;
    for (let b = 0; b < names.length; b++) { const d = segDist(p, ...segs[b]); if (d < bd) { bd = d; best = b; } }
    rawNearest[k] = best;
  }
  const radius = names.map((n, b) => {
    const ds = []; for (let k = 0; k < nBody; k++) if (rawNearest[k] === b) ds.push(segDist(P(order[k]), ...segs[b]));
    ds.sort((a, c) => a - c); return Math.max(0.012 * H, ds.length ? ds[Math.floor(ds.length * 0.6)] : 0.03 * H);
  });
  let W = Array.from({ length: N }, () => new Float64Array(names.length));
  for (let k = 0; k < N; k++) {
    const p = P(order[k]);
    if (k >= nBody) { W[k][names.indexOf('Head')] = 1; continue; } // eyes ride on the head
    for (let b = 0; b < names.length; b++) {
      const n = names[b];
      if (n.startsWith('Left') && p[0] < -0.02 * H) continue;
      if (n.startsWith('Right') && p[0] > 0.02 * H) continue;
      const d = segDist(p, ...segs[b]) / radius[b];
      W[k][b] = Math.pow(1 / Math.max(d, 0.15), 6);
    }
  }
  // smooth across mesh adjacency to remove seams
  const adj = Array.from({ length: nBody }, () => new Set());
  for (let i = 0; i < bodyIdx.length; i += 3) { const a = bodyIdx[i], b = bodyIdx[i + 1], c = bodyIdx[i + 2]; adj[a].add(b).add(c); adj[b].add(a).add(c); adj[c].add(a).add(b); }
  const normRow = r => { let s = 0; for (const x of r) s += x; if (s > 0) for (let i = 0; i < r.length; i++) r[i] /= s; };
  W.forEach(normRow);
  for (let it = 0; it < 4; it++) {
    const W2 = W.map(r => Float64Array.from(r));
    for (let k = 0; k < nBody; k++) { for (const j of adj[k]) for (let b = 0; b < names.length; b++) W2[k][b] += W[j][b]; normRow(W2[k]); }
    W = W2;
  }
  // keep top 4
  const skinIdx = new Uint16Array(N * 4), skinW = new Float32Array(N * 4);
  for (let k = 0; k < N; k++) {
    const top = [...W[k].keys()].sort((a, b) => W[k][b] - W[k][a]).slice(0, 4);
    let s = 0; for (const b of top) s += W[k][b];
    top.forEach((b, i) => { skinIdx[k * 4 + i] = b; skinW[k * 4 + i] = W[k][b] / s; });
  }

  // ---- optional muscle bulk: push the surface out along its normal, weighted by bone
  if (cfg.bulk) {
    const nx = new Float64Array(N * 3);
    for (let i = 0; i < bodyIdx.length; i += 3) {
      const [a, b2, c] = [bodyIdx[i], bodyIdx[i + 1], bodyIdx[i + 2]];
      const n = cross(sub(P(order[b2]), P(order[a])), sub(P(order[c]), P(order[a])));
      for (const k of [a, b2, c]) { nx[k * 3] += n[0]; nx[k * 3 + 1] += n[1]; nx[k * 3 + 2] += n[2]; }
    }
    for (let k = 0; k < nBody; k++) {
      let amt = 0; for (let i = 0; i < 4; i++) amt += skinW[k * 4 + i] * (cfg.bulk[names[skinIdx[k * 4 + i]].replace(/^(Left|Right)/, '')] || 0);
      const n = nrm([nx[k * 3], nx[k * 3 + 1], nx[k * 3 + 2]]), o = order[k];
      v[o * 3] += n[0] * amt * H; v[o * 3 + 1] += n[1] * amt * H; v[o * 3 + 2] += n[2] * amt * H;
    }
  }
  // ---- strongman head shaping (continuous: weighted by the Head skin weight and smooth regional falloffs)
  if (cfg.head) {
    const hb = names.indexOf('Head'), ey = J['l-eye'][1], ez = J['l-eye'][2], hj = J['head'];
    const ss = (a0, b0, x) => { const t = Math.min(1, Math.max(0, (x - a0) / (b0 - a0))); return t * t * (3 - 2 * t); };
    for (let k = 0; k < N; k++) {
      let wh = 0; for (let i = 0; i < 4; i++) if (skinIdx[k * 4 + i] === hb) wh += skinW[k * 4 + i];
      if (k >= nBody) wh = 1;
      if (wh <= 0) continue;
      const o = order[k]; let x = v[o * 3], y = v[o * 3 + 1], z = v[o * 3 + 2];
      // overall head enlargement about the head joint
      x = hj[0] + (x - hj[0]) * (1 + 0.05 * wh); y = hj[1] + (y - hj[1]) * (1 + 0.05 * wh); z = hj[2] + (z - hj[2]) * (1 + 0.05 * wh);
      const jaw = ss(ey - 0.45, ey - 1.25, y) * wh;                       // lower face
      x *= 1 + 0.16 * jaw;                                                 // broad square jaw
      z += 0.10 * jaw * ss(0.2, 1.0, z);                                   // chin/jaw forward
      const brow = Math.exp(-(((y - (ey + 0.28)) / 0.18) ** 2)) * ss(ez - 0.5, ez + 0.1, z) * ss(0.85, 0.15, Math.abs(x)) * wh;
      z += 0.09 * brow;                                                    // heavy brow ridge
      const nose = Math.exp(-(((y - (ey - 0.45)) / 0.3) ** 2)) * ss(0.42, 0.05, Math.abs(x)) * ss(ez - 0.1, ez + 0.3, z) * wh;
      x *= 1 + 0.32 * nose;                                                // broad nose
      v[o * 3] = x; v[o * 3 + 1] = y; v[o * 3 + 2] = z;
    }
  }
  // ---- A-pose -> T-pose (arms horizontal along ±x, legs vertical), linear blend skinning with the weights
  const T = {}; names.forEach(n => T[n] = { R: I3, t: [0, 0, 0] });
  for (const [S, s, sx] of [['Left', 'l', 1], ['Right', 'r', -1]]) {
    const sh = J[s + '-shoulder'], el = J[s + '-elbow'], ha = J[s + '-hand'];
    const A1 = about(rotBetween(sub(el, sh), [sx, 0, 0]), sh);
    const el2 = xf(A1, el), ha1 = xf(A1, ha);
    const A2 = compose(about(rotBetween(sub(ha1, el2), [sx, 0, 0]), el2), A1);
    const up = J[s + '-upper-leg'], kn = J[s + '-knee'], an = J[s + '-ankle'];
    const L1 = about(rotBetween(sub(kn, up), [0, -1, 0]), up);
    const kn2 = xf(L1, kn), an1 = xf(L1, an);
    const L2 = compose(about(rotBetween(sub(an1, kn2), [0, -1, 0]), kn2), L1);
    for (const n of names) {
      if (!n.startsWith(S)) continue;
      const c = chainOf(n).slice(1);
      if (c === 'arm') T[n] = A1; else if (c === 'fore') T[n] = A2; else if (c === 'thigh') T[n] = L1; else if (c === 'shin') T[n] = L2;
    }
  }
  const scale = cfg.height / H * 1.0; // decimetres -> metres at the requested height
  const g0 = J['ground'][1];
  const toM = p => [p[0] * scale, (p[1] - g0) * scale, p[2] * scale];
  const pos = new Float32Array(N * 3);
  for (let k = 0; k < N; k++) {
    const p = P(order[k]); let q = [0, 0, 0];
    for (let i = 0; i < 4; i++) { const w = skinW[k * 4 + i]; if (!w) continue; const r = xf(T[names[skinIdx[k * 4 + i]]], p); q = add(q, [r[0] * w, r[1] * w, r[2] * w]); }
    pos.set(toM(q), k * 3);
  }
  // joint (bone head) positions after T-posing: bone head moves with its parent chain
  // bone head moves with the bone's own chain transform (chain pivots are fixed points of their transform)
  const jointsOut = {};
  for (const n of names) jointsOut[n] = toM(xf(T[n], J[B[n][0]]));
  const E = endJoints();
  for (const [n, j] of Object.entries(E)) {
    const owner = names.find(m => B[m][1] === j);
    jointsOut[n] = toM(xf(owner ? T[owner] : { R: I3, t: [0, 0, 0] }, J[j]));
  }
  // landmarks for clothing masks (metres, T-pose)
  const lm = {
    height: cfg.height, legY: jointsOut.LeftUpLeg[1], hipsY: jointsOut.Hips[1], spineY: jointsOut.Spine[1],
    chestY: jointsOut.Spine2[1], neckY: jointsOut.Neck[1], headY: jointsOut.Head[1], kneeY: jointsOut.LeftLeg[1],
    ankleY: jointsOut.LeftFoot[1], shoulderX: jointsOut.LeftArm[0], elbowX: jointsOut.LeftForeArm[0], handX: jointsOut.LeftHand[0],
    armY: jointsOut.LeftArm[1], eyeY: jointsOut.LeftEye[1], eyeX: jointsOut.LeftEye[0], eyeZ: jointsOut.LeftEye[2],
    mouthY: toM(J['mouth'])[1], mouthZ: toM(J['mouth'])[2],
  };
  // eye vertex colours (sclera / iris / pupil by direction from each eye centre)
  const eyeCol = new Float32Array(N * 3).fill(1);
  const ec = { l: toM(J['l-eye']), r: toM(J['r-eye']) };
  for (let k = nBody; k < N; k++) {
    const p = [pos[k * 3], pos[k * 3 + 1], pos[k * 3 + 2]];
    const c = p[0] > 0 ? ec.l : ec.r; const d = nrm(sub(p, c));
    const col = d[2] > 0.955 ? [0.03, 0.02, 0.02] : d[2] > 0.86 ? (name === 'baby' ? [0.32, 0.2, 0.12] : [0.18, 0.1, 0.06]) : [0.92, 0.9, 0.87];
    eyeCol.set(col, k * 3);
  }
  const out = { name, bones: names, nBody, pos: Array.from(pos, x => +x.toFixed(5)), body: bodyIdx, eyes: eyeIdx,
    skinIdx: Array.from(skinIdx), skinW: Array.from(skinW, x => +x.toFixed(4)), eyeCol: Array.from(eyeCol, x => +x.toFixed(3)),
    joints: jointsOut, landmarks: lm, source: 'MakeHuman base.obj + targets (CC0): ' + cfg.targets.map(t => t[0]).join(', ') };
  fs.writeFileSync(OUT + `mh_${name}.json`, JSON.stringify(out));
  console.log(name, 'verts', N, 'body tris', bodyIdx.length / 3, 'eye tris', eyeIdx.length / 3, JSON.stringify(lm));
}
for (const [n, c] of Object.entries(CHARS)) build(n, c);
