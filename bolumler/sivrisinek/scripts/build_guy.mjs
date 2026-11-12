// Build continuous MakeHuman (CC0) bodies for the rig:
// targets -> T-pose matching the Xbot rest pose -> geometric skin weights on Xbot bone names -> JSON.
// usage: node scripts/build_mh.mjs
import fs from 'fs';
import { readObj, applyTarget, joints as getJoints } from './mh_lib.mjs';

const D = 'C:/Users/birlik grup/Documents/Codex/tools/cybertruck-threejs-study/assets/makehuman/';
const OUT = 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/jobs/20261109-zdf-sivrisinek/project/assets/';
const CHARS = {
  guy: { targets: [['caucasian-male-young', 1], ['universal-male-young-maxmuscle-averageweight', 0.35]], height: 1.80 },
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

// ======================================================================================
// v2 builder: skin UVs, MakeHuman CC0 proxies (tee+jeans, hair, eyebrows, eyelashes) fitted with their
// .mhclo barycentric bindings, expression/shrivel morph targets. Output: project/assets/guy2.json
// usage: node scripts/build_guy.mjs
const X = 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/jobs/20261109-zdf-sivrisinek/_dl/';
const PROXIES = [
  { name: 'clothes', dir: 'mh_cc0/x/clothes/male_casualsuit06/', file: 'male_casualsuit06', morphK: 0.35 },
  { name: 'hair', dir: 'mh_cc0/x/hair/short02/', file: 'short02', morphK: 1 },
  { name: 'brows', dir: 'mh_cc0/x/eyebrows/eyebrow001/', file: 'eyebrow001', morphK: 1 },
  { name: 'lashes', dir: 'mh_cc0/x/eyelashes/eyelashes01/', file: 'eyelashes01', morphK: 1 },
];
const MORPHS = { // name -> [[target file, weight]] (deltas relative to the built shape)
  blinkL: [['mh_targets/eye-left-closure', 1]], blinkR: [['mh_targets/eye-right-closure', 1]],
  worry: [['mh_targets/eyebrows-left-inner-up', 1], ['mh_targets/eyebrows-right-inner-up', 1]],
  mouthOpen: [['mh_targets/mouth-open', 1]],
  // shrivel: young/muscular -> old/min-muscle/min-weight
  shrivel: [['@caucasian-male-young', -1], ['@universal-male-young-maxmuscle-averageweight', -0.35], ['mh_targets/caucasian-male-old', 1], ['mh_targets/universal-male-old-minmuscle-minweight', 1]],
};
function readObjUV(path) {
  const v = [], vt = [], faces = []; let g = 'default';
  for (const line of fs.readFileSync(path, 'utf8').split('\n')) {
    if (line.startsWith('v ')) { const p = line.trim().split(/\s+/); v.push(+p[1], +p[2], +p[3]); }
    else if (line.startsWith('vt ')) { const p = line.trim().split(/\s+/); vt.push(+p[1], +p[2]); }
    else if (line.startsWith('g ')) g = line.trim().slice(2);
    else if (line.startsWith('f ')) {
      const t = line.trim().split(/\s+/).slice(1);
      faces.push({ g, idx: t.map(s => parseInt(s.split('/')[0]) - 1), tidx: t.map(s => { const q = s.split('/')[1]; return q ? parseInt(q) - 1 : -1; }) });
    }
  }
  return { v, vt, faces };
}
function readMhclo(path) {
  const r = { verts: [], del: new Set(), scale: {} }; let mode = '';
  for (const raw of fs.readFileSync(path, 'utf8').split('\n')) {
    const line = raw.trim(); if (!line || line[0] === '#') continue;
    const p = line.split(/\s+/);
    if (/^[xyz]_scale$/.test(p[0])) { r.scale[p[0][0]] = [+p[1], +p[2], +p[3]]; continue; }
    if (p[0] === 'verts') { mode = 'v'; continue; }
    if (p[0] === 'delete_verts') { mode = 'd'; continue; }
    if (!/^-?\d/.test(p[0])) { mode = ''; continue; }
    if (mode === 'v') {
      if (p.length === 1) r.verts.push({ i: [+p[0], +p[0], +p[0]], w: [1, 0, 0], d: [0, 0, 0] });
      else r.verts.push({ i: [+p[0], +p[1], +p[2]], w: [+p[3], +p[4], +p[5]], d: [+p[6], +p[7], +p[8]] });
    } else if (mode === 'd') {
      for (let k = 0; k < p.length; k++) {
        if (p[k + 1] === '-') { for (let a = +p[k]; a <= +p[k + 2]; a++) r.del.add(a); k += 2; } else r.del.add(+p[k]);
      }
    }
  }
  return r;
}
function targetDelta(nv, list) {
  const dlt = new Float64Array(nv * 3);
  for (const [t, w] of list) applyTarget(dlt, t.startsWith('@') ? D + t.slice(1) + '.target' : X + t + '.target', w);
  return dlt;
}

function build(name, cfg) {
  const obj = readObjUV(D + 'base.obj');
  const NV = obj.v.length / 3;
  const v = Float64Array.from(obj.v);
  for (const [t, w] of cfg.targets) applyTarget(v, D + t + '.target', w);
  const objG = readObj(D + 'base.obj');
  const J = getJoints(objG, v);
  J['@hips'] = [0, (J['l-upper-leg'][1] + J['pelvis'][1]) / 2 - 0.15 * (J['pelvis'][1] - J['l-knee'][1]) * 0.3, J['pelvis'][2]];
  const P = i => [v[i * 3], v[i * 3 + 1], v[i * 3 + 2]];
  const H = J['head-2'][1] - J['ground'][1];

  // ---- proxies (read first: their delete_verts hide body faces)
  const prox = PROXIES.map(p => ({ ...p, clo: readMhclo(X + p.dir + p.file + '.mhclo'), obj: readObjUV(X + p.dir + p.file + '.obj') }));
  const del = new Set(); for (const p of prox) for (const i of p.clo.del) del.add(i);

  const bodyFaces = obj.faces.filter(f => f.g === 'body' && !f.idx.some(i => del.has(i)));
  const eyeFaces = obj.faces.filter(f => f.g === 'helper-l-eye' || f.g === 'helper-r-eye');
  const WG = new Set(['body', 'helper-tights', 'helper-skirt', 'helper-hair']);
  const bodyVerts = new Set(); for (const f of obj.faces) if (WG.has(f.g)) f.idx.forEach(i => bodyVerts.add(i));
  const eyeVerts = new Set(); for (const f of eyeFaces) f.idx.forEach(i => eyeVerts.add(i));

  // ---- skin weights per base vertex (same geometric method as v1), body + eyes
  const B = boneTable(); const names = Object.keys(B);
  const segs = names.map(n => [J[B[n][0]], J[B[n][1]]]);
  const bodyList = [...bodyVerts];
  const nearest = new Map();
  for (const i of bodyList) { const p = P(i); let best = 0, bd = 1e9; for (let b = 0; b < names.length; b++) { const d = segDist(p, ...segs[b]); if (d < bd) { bd = d; best = b; } } nearest.set(i, best); }
  const radius = names.map((n, b) => { const ds = []; for (const i of bodyList) if (nearest.get(i) === b) ds.push(segDist(P(i), ...segs[b])); ds.sort((a, c) => a - c); return Math.max(0.012 * H, ds.length ? ds[Math.floor(ds.length * 0.6)] : 0.03 * H); });
  const Wt = new Map();
  for (const i of bodyList) {
    const p = P(i), r = new Float64Array(names.length);
    for (let b = 0; b < names.length; b++) {
      const n = names[b];
      if (n.startsWith('Left') && p[0] < -0.02 * H) continue;
      if (n.startsWith('Right') && p[0] > 0.02 * H) continue;
      r[b] = Math.pow(1 / Math.max(segDist(p, ...segs[b]) / radius[b], 0.15), 6);
    }
    Wt.set(i, r);
  }
  const normRow = r => { let s = 0; for (const x of r) s += x; if (s > 0) for (let i = 0; i < r.length; i++) r[i] /= s; };
  for (const r of Wt.values()) normRow(r);
  const adj = new Map(bodyList.map(i => [i, new Set()]));
  for (const f of obj.faces) if (WG.has(f.g)) for (const a of f.idx) for (const b of f.idx) if (a !== b) adj.get(a).add(b);
  for (let it = 0; it < 4; it++) {
    const W2 = new Map();
    for (const i of bodyList) { const r = Float64Array.from(Wt.get(i)); for (const j of adj.get(i)) { const q = Wt.get(j); for (let b = 0; b < names.length; b++) r[b] += q[b]; } normRow(r); W2.set(i, r); }
    for (const [i, r] of W2) Wt.set(i, r);
  }
  const headRow = new Float64Array(names.length); headRow[names.indexOf('Head')] = 1;
  for (const i of eyeVerts) Wt.set(i, headRow);
  const rowOf = i => Wt.get(i) || headRow;

  // ---- A-pose -> T-pose chain transforms (as v1)
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
  const scale = cfg.height / H, g0 = J['ground'][1];
  const toM = p => [p[0] * scale, (p[1] - g0) * scale, p[2] * scale];
  const top4 = r => { const top = [...r.keys()].sort((a, b) => r[b] - r[a]).slice(0, 4); let s = 0; for (const b of top) s += r[b]; return top.map(b => [b, r[b] / s]); };
  const lbs = (p, w4) => { let q = [0, 0, 0]; for (const [b, w] of w4) { const r = xf(T[names[b]], p); q = add(q, [r[0] * w, r[1] * w, r[2] * w]); } return toM(q); };
  const lbsVec = (d, w4) => { let q = [0, 0, 0]; for (const [b, w] of w4) { const r = mulMV(T[names[b]].R, d); q = add(q, [r[0] * w, r[1] * w, r[2] * w]); } return [q[0] * scale, q[1] * scale, q[2] * scale]; };
  const morphD = Object.fromEntries(Object.entries(MORPHS).map(([k, l]) => [k, targetDelta(NV, l)]));
  const MD = (k, i) => [morphD[k][i * 3], morphD[k][i * 3 + 1], morphD[k][i * 3 + 2]];

  function emit(partName, faces, vertFn, uvOf) {
    const map = new Map(), pos = [], uv = [], si = [], sw = [], idx = [], src = [];
    const morph = Object.fromEntries(Object.keys(MORPHS).map(k => [k, []]));
    const take = (vi, ti) => {
      const key = vi + '/' + ti; if (map.has(key)) return map.get(key);
      const V = vertFn(vi); const k = pos.length / 3; map.set(key, k);
      pos.push(...lbs(V.p, V.w4).map(x => +x.toFixed(5)));
      const t = uvOf(ti); uv.push(+t[0].toFixed(5), +t[1].toFixed(5));
      for (let j = 0; j < 4; j++) { si.push(V.w4[j] ? V.w4[j][0] : 0); sw.push(V.w4[j] ? +V.w4[j][1].toFixed(4) : 0); }
      for (const m of Object.keys(MORPHS)) morph[m].push(...lbsVec(V.md(m), V.w4).map(x => +x.toFixed(5)));
      src.push(vi);
      return k;
    };
    for (const f of faces) { const q = f.idx.map((vi, j) => take(vi, f.tidx[j])); for (let k = 1; k < q.length - 1; k++) idx.push(q[0], q[k], q[k + 1]); }
    for (const m of Object.keys(morph)) if (!morph[m].some(x => x !== 0)) delete morph[m];
    console.log(partName, 'verts', pos.length / 3, 'tris', idx.length / 3, 'morphs', Object.keys(morph).join(','));
    return { name: partName, pos, uv, idx, skinIdx: si, skinW: sw, morph, src };
  }
  const baseVert = i => ({ p: P(i), w4: top4(rowOf(i)), md: m => MD(m, i) });
  const baseUV = ti => ti >= 0 ? [obj.vt[ti * 2], obj.vt[ti * 2 + 1]] : [0, 0];
  const parts = [emit('body', bodyFaces, baseVert, baseUV), emit('eyes', eyeFaces, baseVert, baseUV)];
  // eyes: planar-projected UVs onto the MakeHuman brown eye texture (iris centres at (0.707,0.703) / (0.293,0.293))
  {
    const e = parts[1], n = e.pos.length / 3, c = { l: [0, 0, 0, 0], r: [0, 0, 0, 0] };
    for (let i = 0; i < n; i++) { const k = e.pos[i * 3] > 0 ? c.l : c.r; k[0] += e.pos[i * 3]; k[1] += e.pos[i * 3 + 1]; k[2] += e.pos[i * 3 + 2]; k[3]++; }
    for (const k of [c.l, c.r]) { k[0] /= k[3]; k[1] /= k[3]; k[2] /= k[3]; }
    let rad = 0; for (let i = 0; i < n; i++) { const k = e.pos[i * 3] > 0 ? c.l : c.r; rad = Math.max(rad, Math.hypot(e.pos[i * 3] - k[0], e.pos[i * 3 + 1] - k[1], e.pos[i * 3 + 2] - k[2])); }
    for (let i = 0; i < n; i++) {
      const L = e.pos[i * 3] > 0, k = L ? c.l : c.r, cu = L ? [0.707, 0.703] : [0.293, 0.293];
      const dx = (e.pos[i * 3] - k[0]) / rad, dy = (e.pos[i * 3 + 1] - k[1]) / rad, dz = (e.pos[i * 3 + 2] - k[2]) / rad;
      const r = Math.hypot(dx, dy), s = dz > 0 ? 1 : Math.min(1.08, 2 - r) / Math.max(r, 1e-4) * r; 
      const f = dz > 0 ? 0.23 : 0.23 * (1 + (1 - Math.max(0, dz + 1)) * 0.0);
      e.uv[i * 2] = +(cu[0] + dx * (dz > 0 ? 0.31 : 0.31 / Math.max(r, 0.3))).toFixed(5); e.uv[i * 2 + 1] = +(cu[1] + dy * (dz > 0 ? 0.31 : 0.31 / Math.max(r, 0.3))).toFixed(5);
    }
    console.log('eye radius', rad.toFixed(4), 'centres', c.l.slice(0, 3).map(x => x.toFixed(3)), c.r.slice(0, 3).map(x => x.toFixed(3)));
  }

  // proxies: position = sum w_i V_i + offset * axis scale (measured on the targeted mesh)
  const axisScale = (clo, ax, k) => { const [a, b, den] = clo.scale[ax]; return Math.abs(v[a * 3 + k] - v[b * 3 + k]) / den; };
  for (const p of prox) {
    const s = [axisScale(p.clo, 'x', 0), axisScale(p.clo, 'y', 1), axisScale(p.clo, 'z', 2)];
    const vf = vi => {
      const c = p.clo.verts[vi]; let q = [0, 0, 0]; const r = new Float64Array(names.length);
      for (let j = 0; j < 3; j++) { const pj = P(c.i[j]); q = add(q, [pj[0] * c.w[j], pj[1] * c.w[j], pj[2] * c.w[j]]); const rw = rowOf(c.i[j]); for (let b = 0; b < names.length; b++) r[b] += rw[b] * c.w[j]; }
      q = add(q, [c.d[0] * s[0], c.d[1] * s[1], c.d[2] * s[2]]);
      return { p: q, w4: top4(r), md: m => { let d = [0, 0, 0]; for (let j = 0; j < 3; j++) { const x = MD(m, c.i[j]); d = add(d, [x[0] * c.w[j], x[1] * c.w[j], x[2] * c.w[j]]); } const k = m === 'shrivel' ? p.morphK : 1; return [d[0] * k, d[1] * k, d[2] * k]; } };
    };
    const ouv = ti => ti >= 0 ? [p.obj.vt[ti * 2], p.obj.vt[ti * 2 + 1]] : [0, 0];
    parts.push(emit(p.name, p.obj.faces, vf, ouv));
  }

  const jointsOut = {};
  for (const n of names) jointsOut[n] = toM(xf(T[n], J[B[n][0]]));
  const E = endJoints();
  for (const [n, j] of Object.entries(E)) { const owner = names.find(m => B[m][1] === j); jointsOut[n] = toM(xf(owner ? T[owner] : { R: I3, t: [0, 0, 0] }, J[j])); }
  const lm = {
    height: cfg.height, legY: jointsOut.LeftUpLeg[1], hipsY: jointsOut.Hips[1], spineY: jointsOut.Spine[1],
    chestY: jointsOut.Spine2[1], neckY: jointsOut.Neck[1], headY: jointsOut.Head[1], kneeY: jointsOut.LeftLeg[1],
    ankleY: jointsOut.LeftFoot[1], shoulderX: jointsOut.LeftArm[0], elbowX: jointsOut.LeftForeArm[0], handX: jointsOut.LeftHand[0],
    armY: jointsOut.LeftArm[1], eyeY: jointsOut.LeftEye[1], eyeX: jointsOut.LeftEye[0], eyeZ: jointsOut.LeftEye[2],
    mouthY: toM(J['mouth'])[1], mouthZ: toM(J['mouth'])[2],
  };
  const out = { name, bones: names, parts, joints: jointsOut, landmarks: lm,
    source: 'MakeHuman CC0: base.obj + ' + cfg.targets.map(t => t[0]).join(', ') + '; proxies ' + PROXIES.map(p => p.file).join(', ') + '; targets ' + Object.keys(MORPHS).join(', ') };
  fs.writeFileSync(OUT + `${name}2.json`, JSON.stringify(out));
  console.log('wrote', OUT + `${name}2.json`, (fs.statSync(OUT + `${name}2.json`).size / 1e6).toFixed(1), 'MB');
}
for (const [n, c] of Object.entries(CHARS)) build(n, c);
