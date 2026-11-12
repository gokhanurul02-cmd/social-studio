// "Ya bir kurbağanın kalbi sana takılsaydı?" (METIN v4, kullanicinin kendi kaydi) — full film.
// Every shot boundary, camera beat and event comes from the narration word timings:
//   an(c, w) = start of word w (1-based) of sentence c, en(c, w) = its end.  Files named in project/voice.json.
import * as THREE from 'three';
import { clamp, lerp, range, smooth, easeInOutCubic, easeOutCubic, easeInCubic, halton, mulberry, FPS } from './util.js';
import { makeGuy, guyXrayMaterial } from './characters.js';
import { buildVessels } from './vessels.js';
import { buildFrog } from './frog.js';
import { heartGeometry, heartMaterial, heartXrayMaterial, HeartSwarm, beat, buildCutaway } from './hearts.js';
import { makeGlove, makeTweezers, PINCH, makeChestHole, makeRibcage, makePea, makeIceBlock, makeHurdle, makeSnow, makeFog, makeFridge, makeKitchen } from './props.js';
import { makeTrackGround, makeStadium } from './track.js';
import { BUMP_GLSL } from './mosquito.js';

// ------------------------------------------------------------------ narration timing
const VOICE = await (await fetch('./voice.json')).json();
const WORDS = await (await fetch('/job/' + VOICE.words)).json();
const SENT = {}; for (const w of WORDS) (SENT[w.c] = SENT[w.c] || []).push(w);
export const an = (c, w) => SENT[c][w - 1].s;
export const en = (c, w) => SENT[c][w - 1].e;
const LAST = WORDS[WORDS.length - 1].e;
export const DURATION = LAST + 0.6;

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const CM = 0.01;

// METIN v4 (9 satir):
// 1 Bir kurbağanın kalbi çıkarılıp senin göğsüne takılsaydı, | 2 bezelye kadar bu kalp vücuduna kan yetiştiremez, yüzün mosmor olurdu.
// 3 Bu yüzden göğsüne 100 tane kurbağa kalbi doldururlar. | 4 100 kalp birden pompalayınca, pistte herkesi geride bırakır,
// 5 engelleri kurbağa gibi 3 metre zıplayarak geçerdin. | 6 Ama kış gelince yarış biterdi.
// 7 Çünkü kurbağa kalbinin 3 odası var. Temiz ve kirli kan karışır. | 8 Bazı kurbağalar da kışın donar, kalpleri durur ve baharda yeniden atar.
// 9 Yani kışı buzdolabında geçirir, baharda yarışa kaldığın yerden devam ederdin.
export const T = {
  grab: an(1, 3), pull: an(1, 4), implant: an(1, 5), sec1: an(1, 7),
  xpea: an(2, 1), xflow: an(2, 5), purple: an(2, 8), mosmor: an(2, 9),
  rain: an(3, 1), fill: an(3, 6), dold: an(3, 8),
  pump: an(4, 1), race1: an(4, 5), race2: an(4, 7),
  hurdle: an(5, 1), jump: an(5, 4), zipla: an(5, 6),
  winter: an(6, 1),
  heartA: an(7, 1), heartB: an(7, 4), mix: an(7, 7), karisir: an(7, 11),
  frogsnow: an(8, 1), donar: an(8, 5), frozenx: an(8, 6), restart: an(8, 9), atar: an(8, 11),
  fridge: an(9, 1), out: an(9, 5), spring: an(9, 8),
};
export const TIMELINE = {
  duration: DURATION,
  shots: [
    ['frog', 0], ['implant', T.implant], ['sec1', T.sec1],                         // 1
    ['xpea', T.xpea], ['xflow', T.xflow], ['purple', T.purple],                    // 2
    ['rain', T.rain], ['fill', T.fill],                                           // 3
    ['pump', T.pump], ['race1', T.race1], ['race2', T.race2],                      // 4
    ['hurdle', T.hurdle], ['jump', T.jump],                                        // 5
    ['winter', T.winter],                                                          // 6
    ['heartA', T.heartA], ['heartB', T.heartB], ['mix', T.mix],                    // 7
    ['frogsnow', T.frogsnow], ['frozenx', T.frozenx], ['restart', T.restart],      // 8
    ['fridge', T.fridge], ['out', T.out], ['spring', T.spring],                    // 9
  ].map(([id, a], i, arr) => ({ id, a, b: i + 1 < arr.length ? arr[i + 1][1] : 999 })),
  whoosh: [], flips: [],
};
{
  const at = id => TIMELINE.shots.find(s => s.id === id);
  const prev = id => TIMELINE.shots[TIMELINE.shots.indexOf(at(id)) - 1].id;
  const W = (id, pre = 0.14, post = 0.18) => TIMELINE.whoosh.push({ a: at(id).a - pre, b: at(id).a + post, from: prev(id), to: id });
  const F = (id, pre = 0.2, post = 0.26) => TIMELINE.flips.push({ a: at(id).a - pre, mid: at(id).a, b: at(id).a + post, from: prev(id), to: id });
  W('implant'); W('sec1', 0.12, 0.16); W('xpea'); W('purple', 0.1, 0.14); W('rain'); W('fill', 0.12, 0.16); W('pump'); W('race1', 0.1, 0.14);
  W('hurdle', 0.1, 0.14); W('heartA'); W('frogsnow'); W('frozenx', 0.1, 0.14); W('out', 0.1, 0.14); W('spring');
  F('winter'); F('fridge');
}
export const SHOT_SAMPLES = { frog: 3, sec1: 2, fill: 1.5, frogsnow: 2, heartA: 1.5 };

// ------------------------------------------------------------------ subtitles: [sentence, firstWord, text]
const SUBS = [
  [1, 1, 'Bir kurbağanın'], [1, 3, 'kalbi çıkarılıp'], [1, 5, 'senin göğsüne'], [1, 7, 'takılsaydı,'],
  [2, 1, 'bezelye kadar'], [2, 3, 'bu kalp'], [2, 5, 'vücuduna kan'], [2, 7, 'yetiştiremez,'], [2, 8, 'yüzün mosmor'], [2, 10, 'olurdu.'],
  [3, 1, 'Bu yüzden'], [3, 3, 'göğsüne'], [3, 4, '100 tane'], [3, 6, 'kurbağa kalbi'], [3, 8, 'doldururlar.'],
  [4, 1, '100 kalp birden'], [4, 4, 'pompalayınca,'], [4, 5, 'pistte herkesi'], [4, 7, 'geride bırakır,'],
  [5, 1, 'engelleri'], [5, 2, 'kurbağa gibi'], [5, 4, '3 metre'], [5, 6, 'zıplayarak'], [5, 7, 'geçerdin.'],
  [6, 1, 'Ama kış gelince'], [6, 4, 'yarış biterdi.'],
  [7, 1, 'Çünkü'], [7, 2, 'kurbağa kalbinin'], [7, 4, '3 odası var.'], [7, 7, 'Temiz ve kirli'], [7, 10, 'kan karışır.'],
  [8, 1, 'Bazı kurbağalar da'], [8, 4, 'kışın donar,'], [8, 6, 'kalpleri durur'], [8, 8, 've baharda'], [8, 10, 'yeniden atar.'],
  [9, 1, 'Yani kışı'], [9, 3, 'buzdolabında'], [9, 4, 'geçirir,'], [9, 5, 'baharda yarışa'], [9, 7, 'kaldığın yerden'], [9, 9, 'devam ederdin.'],
].map(([c, w, s]) => ({ t: an(c, w) - 0.02, s, c, w }));
{
  const norm = x => x.toLocaleLowerCase('tr').replace(/[.,]/g, '');
  const flat = SUBS.map(g => g.s.split(' ')).flat().map(norm), said = WORDS.map(w => norm(w.w));
  if (flat.join(' ') !== said.join(' ')) throw new Error('subtitle text != narration:\n' + flat.join(' ') + '\n' + said.join(' '));
  for (const g of SUBS) { const ws = SENT[g.c]; if (!ws[g.w - 1] || norm(ws[g.w - 1].w) !== norm(g.s.split(' ')[0])) throw new Error('subtitle anchor mismatch ' + g.s); }
}
export const SUBTITLE_LIST = SUBS;
export function subtitleAt(frame) {
  const t = frame / FPS; let cur = null;
  for (const g of SUBS) if (t >= g.t) cur = g.s;
  return t < SUBS[0].t ? null : cur;
}

const LOOKS = {
  lab: { sun: 0xffffff, sunI: 3.6, dir: V(0.55, 0.75, 0.35), hemiS: 0xd8d6ff, hemiG: 0x3a3470, hemiI: 0.4, env: 0.55, exp: 1.0,
    sky: [0x5c5cc0, 0x7b78d2, 0xaeaaea, 0xbdb8ee], ground: 0x6a66c0, clouds: 0 },
  track: { sun: 0xfff3e2, sunI: 3.4, dir: V(0.45, 0.75, 0.5), hemiS: 0xcfeaff, hemiG: 0x3f7a2a, hemiI: 0.6, env: 0.8, exp: 1.0,
    sky: [0x0b9ff0, 0x37bdf6, 0xb8ecfc, 0xd5f4fc], ground: 0x5a9a3a, clouds: 0.38 },
  spring: { sun: 0xfff1d8, sunI: 3.6, dir: V(0.4, 0.7, 0.55), hemiS: 0xd6f0ff, hemiG: 0x4f8a2a, hemiI: 0.65, env: 0.85, exp: 1.02,
    sky: [0x0c9cf0, 0x3dbff6, 0xc4f0fc, 0xe0f7fc], ground: 0x5a9a3a, clouds: 0.5 },
  winter: { sun: 0xdfe9ff, sunI: 1.5, dir: V(0.3, 0.7, 0.6), hemiS: 0xdde7f2, hemiG: 0x9aa8b8, hemiI: 1.1, env: 0.9, exp: 1.05,
    sky: [0x5f7896, 0x8199b4, 0xc5d1dd, 0xd8e0e8], ground: 0xc8d2dc, clouds: 0.85 },
  xray: { sun: 0x9ab8ff, sunI: 0.2, dir: V(0.3, 0.8, 0.4), hemiS: 0x1a2a50, hemiG: 0x050810, hemiI: 0.2, env: 0.05, exp: 1.25,
    sky: [0x01030a, 0x040b1c, 0x0a1834, 0x0a1834], ground: 0x01030a, clouds: 0 },
  heart: { sun: 0xffffff, sunI: 3.2, dir: V(0.4, 0.8, 0.6), hemiS: 0xbfd6ff, hemiG: 0x1a2a50, hemiI: 0.6, env: 0.6, exp: 1.0,
    sky: [0x071430, 0x0f2a58, 0x23477e, 0x2c5590], ground: 0x0a1834, clouds: 0 },
  kitchen: { sun: 0xfff6ea, sunI: 2.6, dir: V(0.45, 0.8, 0.6), hemiS: 0xe9f2ff, hemiG: 0x8a8070, hemiI: 0.85, env: 0.7, exp: 1.0,
    sky: [0x7db8e0, 0x9ccbea, 0xd9ecf6, 0xe4f1f8], ground: 0xb0b0b0, clouds: 0.2 },
};

const LAB_TABLE_Y = 1.0;
const FROG_POS = V(0, LAB_TABLE_Y + 0.0335, 0);
const LAB_GUY = V(0, 0, -3.0);
const XR_GUY = V(40, 0, 0);
const TRACK_Z = { guy: -0.2, r1: -1.466, r2: 1.066 };
const FRIDGE_POS = V(-30, 0, 0);

function tableMat() {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.75, sheen: 0.5, sheenColor: new THREE.Color(0.7, 0.7, 1.0) });
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;\n' + BUMP_GLSL)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float _H; { float n = vnoise3(vO * 30.0), w = 0.5 + 0.5 * sin(vO.x * 2400.0) * sin(vO.y * 2400.0);
        diffuseColor.rgb = vec3(0.2, 0.2, 0.56) * (0.9 + 0.12 * n) * (0.96 + 0.05 * w); _H = (n * 0.6 + w * 0.2) * 0.00012; }`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);');
  };
  m.customProgramCacheKey = () => 'labtable';
  return m;
}

export class World {
  constructor(scene, env) {
    this.scene = scene; this.env = env; this.sampleIdx = 0;
    env.ground.visible = false; scene.fog = null;
    this.all = [];
    const add = o => { scene.add(o); this.all.push(o); return o; };
    // characters
    this.guy = makeGuy(); add(this.guy.group);
    this.r1 = makeGuy(); add(this.r1.group); this.r2 = makeGuy(); add(this.r2.group);
    const tee = (rig, hex) => { const X = rig.mats.clothes.userData.X; X.uTeeOn.value = 1; X.uTee.value.set(hex); };
    tee(this.r1, 0xe8e8ea); tee(this.r2, 0x1f4fd0);
    this.X = this.guy.mats.body.userData.X;
    // lab: table + frogs + hands
    this.table = add(new THREE.Mesh(new THREE.PlaneGeometry(3, 3), tableMat())); this.table.rotation.x = -Math.PI / 2; this.table.position.y = LAB_TABLE_Y; this.table.receiveShadow = true;
    this.frog = buildFrog('sit', { incision: true }); add(this.frog.group);
    this.frog.group.scale.setScalar(CM); this.frog.group.position.set(0, LAB_TABLE_Y + 0.001, 0); this.frog.group.rotation.set(0, 0.25, 0); this.frog.group.updateMatrixWorld(true);
    this.INC = this.frog.group.localToWorld(V(0, 3.05, 0.2));
    this.frogSit = buildFrog('sit'); add(this.frogSit.group); this.frogSit.group.scale.setScalar(CM);
    this.frogXr = new THREE.Mesh(this.frogSit.geo, guyXrayMaterial(0x6fc4ff)); this.frogXr.renderOrder = 5; this.frogXr.scale.setScalar(CM); add(this.frogXr);
    this.heartMat = heartMaterial();
    this.heart = add(new THREE.Mesh(heartGeometry(), this.heartMat)); this.heart.castShadow = true;
    this.heartXr = add(new THREE.Mesh(heartGeometry(), heartXrayMaterial())); this.heartXr.renderOrder = 7;
    this.glove = makeGlove(); add(this.glove); this.glove2 = makeGlove(); add(this.glove2);
    this.tw = makeTweezers(); add(this.tw.group);
    // chest porthole, measured on the standing pose (travels with the guy via placeHole)
    this.hole = makeChestHole(0.075, 0.13); add(this.hole.group);
    this.placeGuy(this.guy, LAB_GUY, 0, 'stand', 0);
    this.holeLocal = this.computeHole();
    // swarm of 110 hearts
    this.swarm = new HeartSwarm(110, heartMaterial(), 9); add(this.swarm.mesh);
    this.swarmXr = new HeartSwarm(110, heartXrayMaterial(), 9); add(this.swarmXr.mesh); this.swarmXr.mesh.renderOrder = 7; this.swarmXr.mesh.castShadow = false;
    const r = mulberry(4);
    this.slots = Array.from({ length: 110 }, (_, i) => { const a = i * 2.39996, rr = Math.sqrt((i % 55 + 0.5) / 55) * 0.058; return V(Math.cos(a) * rr, Math.sin(a) * rr, -0.085 + (i >= 55 ? 0.03 : 0) + (r() - 0.5) * 0.01); });
    this.fly = Array.from({ length: 110 }, () => ({ a: r(), from: V((r() - 0.5) * 3, 2.2 + r() * 2.5, 1.0 + r() * 2.5), spin: r() * 6.28 }));
    // x-ray rig + vessels + ribcage at XR_GUY
    this.placeGuy(this.guy, XR_GUY, 0, 'stand', 0);
    const hc = this.guy.bones.Spine2.getWorldPosition(V(0, 0, 0)).lerp(this.guy.bones.Spine1.getWorldPosition(V(0, 0, 0)), 0.3).add(V(0.025, 0, 0.05));
    this.xrHeart = hc;
    this.ves = buildVessels(this.guy, hc, V(0, 0, 1)); add(this.ves.group);
    this.ribs = add(makeRibcage(this.guy, guyXrayMaterial(0xbfe2ff)));
    this.peaXr = add(new THREE.Mesh(new THREE.SphereGeometry(0.0045, 24, 16), heartXrayMaterial(0x7dff5a))); this.peaXr.renderOrder = 7;
    // track world
    this.trackG = add(makeTrackGround()); this.stadium = add(makeStadium());
    this.hurdles = []; for (let i = 0; i < 4; i++) for (const z of [TRACK_Z.r1, TRACK_Z.guy, TRACK_Z.r2]) { const h = makeHurdle(1.1, 0.95); h.position.set(30 + i * 9, 0, z); this.hurdles.push(add(h)); }
    this.ice = add(makeIceBlock(0.95, 2.05, 0.95));
    this.snow = makeSnow(); add(this.snow.mesh);
    // heart cutaway
    this.cut = buildCutaway(); add(this.cut.group); this.cut.group.position.set(0, 50, 0);
    // kitchen + fridge
    this.kitchen = add(makeKitchen()); this.kitchen.position.copy(FRIDGE_POS);
    this.fridge = makeFridge(); add(this.fridge.group); this.fridge.group.position.copy(FRIDGE_POS);
    this.fog = makeFog(); add(this.fog.mesh);
    this.camQ = new THREE.Quaternion();
  }

  // ---------------------------------------------------------------- helpers
  placeGuy(rig, pos, yaw, pose, t, o = {}) {
    rig.group.visible = true; rig.pose(pose, t, o);
    rig.group.position.copy(pos); rig.group.quaternion.setFromEuler(new THREE.Euler(0, yaw, 0)); rig.group.updateMatrixWorld(true);
  }
  face(rig, o = {}) { rig.setMorph('blinkL', o.blink ?? 0); rig.setMorph('blinkR', o.blink ?? 0); rig.setMorph('worry', o.worry ?? 0); rig.setMorph('mouthOpen', o.mouth ?? 0); }
  computeHole() {
    const g = this.guy; g.group.updateMatrixWorld(true);
    const C = g.bones.Spine2.getWorldPosition(V(0, 0, 0)).add(V(0.035, -0.045, 0));
    const R = this.hole.R, rim = new Array(32).fill(-1), v = V(0, 0, 0);
    for (const part of ['clothes', 'body']) {
      const mesh = g.parts[part]; mesh.skeleton.update();
      const n = mesh.geometry.attributes.position.count;
      for (let i = 0; i < n; i++) {
        mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld);
        const d = v.clone().sub(C), al = d.z; if (al < 0) continue;
        const rr = Math.hypot(d.x, d.y); if (Math.abs(rr - R) > 0.012) continue;
        const k = Math.floor(((Math.atan2(d.y, d.x) / (2 * Math.PI) + 0.5) * 32)) % 32;
        rim[k] = Math.max(rim[k], al);
      }
    }
    for (let i = 0; i < 32; i++) if (rim[i] < 0) rim[i] = rim[(i + 31) % 32] > 0 ? rim[(i + 31) % 32] : 0.1;
    const zf = Math.min(...rim) - 0.004;
    const inv = new THREE.Matrix4().copy(g.group.matrixWorld).invert();
    window.HOLE = { rim, zf };
    return { C: C.applyMatrix4(inv), zf, rim: rim.map(x => x - zf) };
  }
  placeHole(radius = 1) {
    const g = this.guy, H = this.holeLocal, X = this.X;
    const C = H.C.clone().applyMatrix4(g.group.matrixWorld), N = V(0, 0, 1).applyQuaternion(g.group.quaternion);
    X.uHoleOn.value = radius > 0.001 ? 1 : 0; X.uHoleC.value.copy(C); X.uHoleN.value.copy(N); X.uHoleR.value = this.hole.R * radius;
    const o = C.clone().addScaledVector(N, H.zf);
    this.hole.group.visible = radius > 0.001; this.hole.group.position.copy(o); this.hole.group.quaternion.copy(g.group.quaternion);
    this.hole.group.scale.set(Math.max(radius, 0.001), Math.max(radius, 0.001), 1); this.hole.u.uRim.value = H.rim; this.hole.group.updateMatrixWorld(true);
    return { o, N, q: g.group.quaternion.clone(), local: p => this.hole.group.localToWorld(p.clone()) };
  }
  hideAll() {
    for (const o of this.all) o.visible = false;
    for (const r of [this.guy, this.r1, this.r2]) { r.setXray(false); this.face(r, {}); const X = r.mats.body.userData.X; X.uFrost.value = 0; X.uPurple.value = 0; X.uHoleOn.value = 0; }
    this.frog.mat.userData.u.uFrost.value = 0; this.frogSit.mat.userData.u.uFrost.value = 0; this.frogSit.eyeMat.userData.u.uFrost.value = 0;
    this.heartMat.userData.u.uIce.value = 0; this.heartMat.userData.u.uGlow.value = 0;
    this.heartXr.material.userData.u.uCol.value.set(0xff2a1a); this.heartXr.material.userData.u.uK.value = 1;
    this.trackG.material.userData.u.uSnow.value = 0;
    this.fridge.light.intensity = 0;
  }
  look(name) {
    const L = LOOKS[name], E = this.env;
    E.sun.color.set(L.sun); E.sun.intensity = L.sunI;
    E.hemi.color.set(L.hemiS); E.hemi.groundColor.set(L.hemiG); E.hemi.intensity = L.hemiI;
    this.scene.environmentIntensity = L.env;
    const U = E.sky.material.uniforms; U.zenith.value.set(L.sky[0]); U.upper.value.set(L.sky[1]); U.horizon.value.set(L.sky[2]); U.haze.value.set(L.sky[3]); U.groundCol.value.set(L.ground);
    U.cloudAmount.value = L.clouds;
    return L;
  }
  sun(c, size, dist, dir, bias, nbias, ang = 0.035) {
    const s = this.env.sun, sc = s.shadow.camera, i = this.sampleIdx + 1;
    const d = dir.clone().normalize();
    const u = V(0, 1, 0).cross(d).normalize(), v = d.clone().cross(u);
    const r = Math.sqrt(halton(i, 2)) * ang, a = halton(i, 3) * Math.PI * 2;
    const jd = d.clone().addScaledVector(u, Math.cos(a) * r).addScaledVector(v, Math.sin(a) * r).normalize();
    s.target.position.copy(c); s.position.copy(c).addScaledVector(jd, dist);
    sc.left = -size; sc.right = size; sc.top = size; sc.bottom = -size; sc.near = dist * 0.05; sc.far = dist * 2; sc.updateProjectionMatrix();
    s.shadow.bias = bias; s.shadow.normalBias = nbias;
    s.target.updateMatrixWorld(); s.updateMatrixWorld();
  }
  apply(shot, t) {
    this.hideAll();
    const st = { pos: V(0, 1, 5), target: V(0, 1, 0), fov: 40, aperture: 0, roll: 0, exposure: 1, near: 0.02, far: 300 };
    this['shot_' + shot](t, st);
    return st;
  }
  cam(st, pos, target, fov, focusPt = null, aperture = 0) { st.pos = pos; st.target = target; st.fov = fov; if (focusPt) { st.focus = pos.distanceTo(focusPt); st.aperture = aperture; } }
  camQuat(st) { const m = new THREE.Matrix4().lookAt(st.pos, st.target, V(0, 1, 0)); return this.camQ.setFromRotationMatrix(m); }
  // tweezers: tip at `tip`, hand towards `from` (unit, tip->hand), open 0..1; the glove holds them
  tweezers(tip, from, open, roll = 0) {
    const d = from.clone().normalize().negate();
    const q = new THREE.Quaternion().setFromUnitVectors(V(0, 0, 1), d);
    q.multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), roll));
    const tg = this.tw.group; tg.visible = true; tg.quaternion.copy(q); tg.position.copy(tip).addScaledVector(d, -0.125); this.tw.setOpen(open);
    const grip = tip.clone().addScaledVector(d, -0.125 + 0.045);
    const gq = q.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.15, 0, 0.35)));
    const G = this.glove; G.visible = true; G.quaternion.copy(gq); G.scale.setScalar(CM);
    G.position.copy(grip).sub(PINCH.clone().multiplyScalar(CM).applyQuaternion(gq));
    tg.updateMatrixWorld(true); G.updateMatrixWorld(true);
  }
  heartAt(mesh, pos, s, t, rate = 0, q = null, amp = 0.18) {
    mesh.visible = true; const b = rate ? 1 + amp * beat(t * rate) : 1;
    mesh.position.copy(pos); mesh.scale.set(s * b, s * (1 + (b - 1) * 0.7), s * b); if (q) mesh.quaternion.copy(q); else mesh.rotation.set(0, 0, 0); mesh.updateMatrixWorld(true);
  }
  labSun(L, c, size = 0.4) { this.sun(c, size, 3, L.dir, -0.00005, 0.0004, 0.03); }

  // ================================================================= 1. frog macro: tweezers pull the tiny heart out
  shot_frog(t, st) {
    const L = this.look('lab');
    this.table.visible = true; this.frog.group.visible = true;
    const inc = this.INC.clone();
    const lift = easeInOutCubic(range(t, T.pull - 0.05, T.implant + 0.1));
    const down = easeOutCubic(range(t, 0, T.grab + 0.1));
    const hp = inc.clone().add(V(0, 0.001 + 0.045 * lift, 0.01 * lift));
    this.heartAt(this.heart, hp, 0.55 * CM, t, 3.2, new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.4 - 0.6 * lift, 0.3, 0.2 * lift)), 0.2);
    const from = V(0.55, 0.75, 0.35);
    const tip = lift > 0 ? hp.clone().add(V(0, 0.004, 0)) : inc.clone().add(V(0, 0.002 + 0.03 * (1 - down), 0.005));
    const open = t < T.grab ? 0.9 : 0.9 * (1 - smooth(range(t, T.grab, T.grab + 0.25)));
    this.tweezers(tip, from, open, 0.2);
    const p = easeInOutCubic(range(t, 0, T.implant));
    const pos = inc.clone().add(V(lerp(-0.05, -0.03, p), lerp(0.2, 0.16, p) + 0.025 * lift, lerp(0.2, 0.16, p)));
    this.cam(st, pos, inc.clone().add(V(0, -0.008 + 0.022 * lift, 0.006)), 38, hp, 0.0012);
    st.near = 0.005; st.far = 50; st.exposure = L.exp;
    this.labSun(L, inc, 0.18);
  }
  // ================================================================= 2. the heart goes to your chest (lab)
  shot_implant(t, st) {
    const L = this.look('lab');
    this.placeGuy(this.guy, LAB_GUY, 0, 'stand', t, { look: 0.1 }); this.face(this.guy, { worry: 0.3 });
    const open = smooth(range(t, T.implant - 0.05, T.implant + 0.3));
    const H = this.placeHole(open);
    const p = easeInOutCubic(range(t, T.implant - 0.1, T.sec1 + 0.1));
    const target = H.local(V(0, 0, 0.02));
    const hp = target.clone().add(V(lerp(0.28, 0.03, p), lerp(0.1, 0.0, p), lerp(0.22, 0.05, p)));
    this.heartAt(this.heart, hp, 0.9 * CM, t, 3.2, new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.6, 0.4, 0.3)));
    this.tweezers(hp.clone().add(V(0.004, 0.006, 0)), V(0.85, 0.2, 0.45), 0.15, -0.3);
    const c = H.o.clone().add(V(0.02, 0.03, 0));
    this.cam(st, c.clone().add(V(lerp(0.45, 0.3, p), lerp(0.02, 0.0, p), lerp(1.15, 0.8, p))), c.clone().add(V(0, 0.12, 0)), 40, c, 0.004);
    st.exposure = L.exp; this.labSun(L, c, 0.8);
  }
  shot_sec1(t, st) {
    const L = this.look('lab');
    this.placeGuy(this.guy, LAB_GUY, 0, 'stand', t, {}); this.face(this.guy, { worry: 0.3 });
    const H = this.placeHole(1);
    const p = easeInOutCubic(range(t, T.sec1 - 0.1, T.sec1 + 0.5));
    const rest = H.local(V(0.008, -0.004, -0.06)), entry = H.local(V(0.03, 0.01, 0.05));
    const hp = entry.clone().lerp(rest, p);
    const beating = t > T.sec1 + 0.45 ? 4.2 : 0;
    this.heartAt(this.heart, hp, 0.9 * CM, t, beating, new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.3, 0.4, 0.15)), 0.22);
    const away = easeInCubic(range(t, T.sec1 + 0.5, T.xpea));
    this.tweezers(hp.clone().add(V(0.004 + 0.1 * away, 0.006 + 0.05 * away, 0.1 * away)), V(0.5, 0.35, 0.8), 0.15 + 0.6 * smooth(range(t, T.sec1 + 0.42, T.sec1 + 0.55)), -0.3);
    const q = range(t, T.sec1, T.xpea);
    const c = H.local(V(0, 0, -0.05));
    this.cam(st, H.local(V(lerp(0.05, 0.03, q), lerp(0.07, 0.05, q), lerp(0.27, 0.19, q))), c, 42, hp, 0.0025);
    st.near = 0.01; st.exposure = L.exp; this.labSun(L, H.o, 0.4);
  }
  // ================================================================= 3–5. x-ray: tiny heart, blood falls short, purple face
  xray(t, drain, k = 1) {
    const L = this.look('xray');
    this.placeGuy(this.guy, XR_GUY, 0, 'stand', 0); this.guy.setXray(true);
    this.ves.group.visible = true; this.ves.update(t, drain, 0, k); this.ribs.visible = true; this.ribs.material.userData.u.uK.value = 0.45;
    return L;
  }
  shot_xpea(t, st) {
    const L = this.xray(t, 0.62 + 0.04 * Math.sin(t * 9));
    const hc = this.xrHeart;
    this.heartAt(this.heartXr, hc, 0.75 * CM, t, 4.5, new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.3, 0.3, 0.2)), 0.25);
    const pp = smooth(range(t, T.xpea + 0.1, T.xpea + 0.35));
    this.peaXr.visible = pp > 0.01; this.peaXr.scale.setScalar(Math.max(pp, 0.001) * 1.4); this.peaXr.position.copy(hc).add(V(-0.022, 0.004, 0.012));
    const p = easeInOutCubic(range(t, T.xpea, T.xflow));
    this.cam(st, hc.clone().add(V(lerp(0.2, 0.05, p), lerp(0.08, 0.04, p), lerp(1.0, 0.85, p))), hc.clone().add(V(-0.01, 0, 0)), 40);
    st.exposure = L.exp;
  }
  shot_xflow(t, st) {
    const stall = smooth(range(t, T.xflow, an(2, 7)));
    const L = this.xray(t, lerp(0.95, 0.55, stall) + 0.03 * Math.sin(t * 11) * stall);
    this.heartAt(this.heartXr, this.xrHeart, 0.75 * CM, t, 4.5, null, 0.25);
    const p = easeInOutCubic(range(t, T.xflow, T.purple));
    const c = XR_GUY.clone().add(V(0, lerp(1.15, 1.0, p), 0));
    this.cam(st, c.clone().add(V(lerp(0.5, 0.75, p), lerp(0.2, 0.15, p), lerp(1.9, 2.4, p))), c, 46);
    st.exposure = L.exp;
  }
  shot_purple(t, st) {
    const L = this.look('lab');
    this.placeGuy(this.guy, LAB_GUY, 0, 'stand', t, { look: 0.1 });
    const k = smooth(range(t, T.purple + 0.1, T.mosmor + 0.45));
    this.X.uPurple.value = 0.85 * k; this.face(this.guy, { worry: 0.5 + 0.5 * k, mouth: 0.08 + 0.17 * k * (0.8 + 0.2 * Math.sin(t * 9)), blink: 0.15 * k });
    const H = this.guy.bones.Head.getWorldPosition(V(0, 0, 0)).add(V(0, 0.04, 0));
    const p = easeInOutCubic(range(t, T.purple, T.rain));
    this.cam(st, H.clone().add(V(lerp(0.2, 0.12, p), lerp(0.04, 0.02, p), lerp(0.62, 0.48, p))), H.clone().add(V(0, -0.01, 0)), 34, H, 0.003);
    st.roll = 0.015 * Math.sin(t * 13) * k;
    st.exposure = L.exp; this.labSun(L, H, 0.6);
  }
  // ================================================================= 6–7. 100 hearts fly in and fill the chest (peak 1)
  trackWorld(snow = 0) { this.trackG.visible = true; this.stadium.visible = true; this.trackG.material.userData.u.uSnow.value = snow; }
  swarmFlight(t, H, t0, t1, flyScale) {
    const S = this.swarm; S.mesh.visible = true;
    for (let i = 0; i < S.n; i++) {
      const f = this.fly[i], ta = lerp(t0, t1, f.a), u = range(t, ta - 0.9, ta);
      if (t < ta - 0.9) { S.hide(i); continue; }
      const slot = H.local(this.slots[i]);
      if (u < 1) {
        const e = easeInCubic(u) * 0.6 + u * 0.4;
        const p = H.o.clone().add(f.from.clone().applyQuaternion(H.q)).lerp(slot, e).add(V(0, 0.3 * Math.sin(Math.PI * u), 0));
        S.set(i, p, lerp(flyScale, 1.15, u) * CM, t, new THREE.Quaternion().setFromEuler(new THREE.Euler(f.spin + t * 5, f.spin * 2 + t * 3, 0)), 0.1);
      } else S.set(i, slot, 1.15 * CM * (1 + 0.15 * Math.max(0, 1 - (t - ta) * 4)), t, null, 0.2);
    }
    S.done();
  }
  shot_rain(t, st) {
    const L = this.look('track'); this.trackWorld();
    const pos = V(4, 0, TRACK_Z.guy);
    this.placeGuy(this.guy, pos, 0.5, 'stand', t, { look: -0.2, surprise: 0.2 * smooth(range(t, T.rain + 0.4, T.rain + 0.9)) });
    this.face(this.guy, { worry: 0.4, mouth: 0.25 });
    const H = this.placeHole(1);
    this.swarmFlight(t, H, T.rain + 0.6, T.dold + 0.3, 9);
    const p = easeInOutCubic(range(t, T.rain, T.fill));
    const c = pos.clone().add(V(0, lerp(1.25, 1.35, p), 0));
    this.cam(st, c.clone().add(V(lerp(1.3, 0.95, p), lerp(-0.6, -0.45, p), lerp(2.2, 1.7, p))), c.clone().add(V(0, 0.35, 0)), 46, c, 0.008);
    st.exposure = L.exp; this.sun(pos.clone().add(V(0, 1, 0)), 3, 12, L.dir, -0.0003, 0.01, 0.02);
  }
  shot_fill(t, st) {
    const L = this.look('track'); this.trackWorld();
    const pos = V(4, 0, TRACK_Z.guy);
    this.placeGuy(this.guy, pos, 0.5, 'stand', t, { look: -0.2, surprise: 0.2 }); this.face(this.guy, { worry: 0.4, mouth: 0.25 });
    const H = this.placeHole(1);
    this.swarmFlight(t, H, T.rain + 0.6, T.dold + 0.3, 9);
    const p = easeInOutCubic(range(t, T.fill, T.pump + 0.1));
    const c = H.local(V(0, 0, -0.05));
    this.cam(st, H.local(V(lerp(0.12, 0.05, p), lerp(0.16, 0.08, p), lerp(0.42, 0.24, p))), c, 42, c, 0.003);
    st.near = 0.01; st.exposure = L.exp; this.sun(H.o, 0.6, 6, L.dir, -0.0001, 0.002, 0.02);
  }
  shot_pump(t, st) {
    const L = this.xray(t * 1.8, 0, 1.25);
    const S = this.swarmXr; S.mesh.visible = true;
    for (let i = 0; i < S.n; i++) { const s = this.slots[i]; S.set(i, this.xrHeart.clone().add(V(s.x * 1.25, s.y * 1.35, (s.z + 0.07) * 0.9)), 0.95 * CM, t * 1.4, null, 0.25); }
    S.done();
    const p = easeInOutCubic(range(t, T.pump, T.race1));
    const c = this.xrHeart.clone().add(V(0, lerp(0.0, -0.15, p), 0));
    this.cam(st, c.clone().add(V(lerp(-0.25, 0.35, p), lerp(0.08, 0.1, p), lerp(0.55, 1.1, p))), c, 44);
    st.exposure = L.exp;
  }
  // ================================================================= 8–11. the race and the frog jump (peak 2)
  runners(t, gx, { r1x, r2x, lean = 0.15 } = {}) {
    this.placeGuy(this.guy, V(gx, 0, TRACK_Z.guy), Math.PI / 2, 'run', t * 1.25, { lean });
    this.face(this.guy, { worry: 0.1, mouth: 0.2 });
    if (r1x !== undefined) { this.placeGuy(this.r1, V(r1x, 0, TRACK_Z.r1), Math.PI / 2, 'run', t * 1.1 + 0.3, { lean: 0.1 }); this.face(this.r1, { worry: 0.6, mouth: 0.4 }); }
    if (r2x !== undefined) { this.placeGuy(this.r2, V(r2x, 0, TRACK_Z.r2), Math.PI / 2, 'run', t * 1.1 + 0.55, { lean: 0.1 }); this.face(this.r2, { worry: 0.6, mouth: 0.4 }); }
  }
  gx(t) { return -20 + 8.2 * (t - T.race1); }
  shot_race1(t, st) {
    const L = this.look('track'); this.trackWorld();
    const g = this.gx(t), rr = -17.5 + 6.3 * (t - T.race1);
    this.runners(t, g, { r1x: rr, r2x: rr - 0.4 });
    const p = range(t, T.race1, T.race2);
    const c = V(g - 0.4, 1.05, TRACK_Z.guy);
    this.cam(st, c.clone().add(V(lerp(-1.2, 0.6, p), lerp(-0.2, 0.0, p), 4.6)), c.clone().add(V(0.4, 0, -0.3)), 48, c, 0.01);
    st.exposure = L.exp; this.sun(c, 6, 20, L.dir, -0.0004, 0.02, 0.015);
  }
  shot_race2(t, st) {
    const L = this.look('track'); this.trackWorld();
    const g = this.gx(t), rr = -17.5 + 6.3 * (t - T.race1);
    this.runners(t, g, { r1x: rr, r2x: rr - 0.4 });
    const p = range(t, T.race2, T.hurdle);
    const c = V(g + 0.2, 0.95, TRACK_Z.guy);
    this.cam(st, c.clone().add(V(lerp(2.6, 3.0, p), lerp(-0.45, -0.5, p), lerp(-1.3, -1.6, p))), c.clone().add(V(-1.5, 0.15, 0.3)), 44, c, 0.012);
    st.exposure = L.exp; this.sun(c.clone().add(V(-3, 0, 0)), 8, 20, L.dir, -0.0004, 0.02, 0.015);
  }
  get HX() { return 30; }
  jumpX(t) { const t0 = T.jump, t1 = T.winter - 0.28; if (t < t0) return this.HX - 3.0 - 6.5 * (t0 - t); const u = range(t, t0, t1); return this.HX - 3.0 + 6.0 * u + (t > t1 ? 4 * (t - t1) : 0); }
  shot_hurdle(t, st) {
    const L = this.look('track'); this.trackWorld(); for (const h of this.hurdles) h.visible = true;
    const g = this.jumpX(t), rr = g - 4.5 - 0.5 * (t - T.hurdle);
    const crouch = smooth(range(t, T.jump - 0.25, T.jump));
    if (crouch > 0.5) { this.placeGuy(this.guy, V(g, 0, TRACK_Z.guy), Math.PI / 2, 'jump', 0.0); this.face(this.guy, { mouth: 0.3 }); }
    else this.runners(t, g, {});
    this.placeGuy(this.r1, V(rr, 0, TRACK_Z.r1), Math.PI / 2, 'run', t * 1.1 + 0.3, { lean: 0.1 }); this.face(this.r1, { worry: 0.6, mouth: 0.4 });
    const p = range(t, T.hurdle, T.jump);
    const c = V(g + 0.8, 0.8, TRACK_Z.guy);
    this.cam(st, c.clone().add(V(lerp(3.5, 2.6, p), -0.55, lerp(2.2, 2.8, p))), c.clone().add(V(-0.4, 0.15, 0)), 46, c, 0.01);
    st.exposure = L.exp; this.sun(c, 7, 20, L.dir, -0.0004, 0.02, 0.015);
  }
  shot_jump(t, st) {
    const L = this.look('track'); this.trackWorld(); for (const h of this.hurdles) h.visible = true;
    const t0 = T.jump, t1 = T.winter - 0.28;
    const u = range(t, t0, t1);
    const g = this.jumpX(t);
    const air = smooth(range(u, 0.12, 0.2)) * (1 - smooth(range(u, 0.86, 0.95)));
    const h = 2.6 * Math.sin(Math.PI * clamp((u - 0.15) / 0.75)) * air;
    if (t < t1) { this.placeGuy(this.guy, V(g, 0, TRACK_Z.guy), Math.PI / 2, 'jump', u); this.guy.group.position.y += h; }
    else this.runners(t, g, {});
    this.guy.group.updateMatrixWorld(true);
    this.face(this.guy, { mouth: 0.45, worry: 0.1 });
    const rr = this.HX - 8 + 5.8 * (t - t0);
    this.placeGuy(this.r1, V(rr, 0, TRACK_Z.r1), Math.PI / 2, 'run', t * 1.1 + 0.3, { lean: 0.1 }); this.face(this.r1, { worry: 0.8, mouth: 0.6 });
    const p = easeInOutCubic(range(t, t0, T.winter));
    const c = V(g, 0.9 + h * 0.8, TRACK_Z.guy);
    this.cam(st, V(this.HX + lerp(-0.5, 1.5, p), 0.45, TRACK_Z.guy + lerp(7.5, 6.8, p)), V(g, 1.0 + h * 0.6, TRACK_Z.guy), 36, c, 0.006);
    st.exposure = L.exp; this.sun(V(this.HX, 1.5, TRACK_Z.guy), 7, 20, L.dir, -0.0004, 0.02, 0.015);
  }
  // ================================================================= 12. winter: frozen in an ice block (twist)
  shot_winter(t, st) {
    const L = this.look('winter'); this.trackWorld(1.0);
    const pos = V(6, 0, TRACK_Z.guy);
    this.placeGuy(this.guy, pos, Math.PI / 2, 'run', 0.21, { lean: 0.15 }); this.X.uFrost.value = 0.9; this.face(this.guy, { worry: 0.9, mouth: 0.35, blink: 0.1 });
    this.ice.visible = true; this.ice.position.copy(pos).add(V(0.12, 0, 0)); this.ice.rotation.y = 0.05; this.ice.updateMatrixWorld(true);
    this.snow.mesh.visible = true; this.snow.update(t, pos.clone().add(V(0, 1.5, 0)));
    const p = easeInOutCubic(range(t, T.winter, T.heartA));
    const c = pos.clone().add(V(0.1, 1.05, 0));
    const a = lerp(0.45, 1.05, p), r = lerp(3.6, 3.0, p);
    this.cam(st, c.clone().add(V(Math.sin(a) * r, lerp(0.15, 0.35, p), Math.cos(a) * r)), c, 46, c, 0.01);
    st.exposure = L.exp; this.sun(c, 3, 12, L.dir, -0.0003, 0.01, 0.03);
  }
  // ================================================================= 13–15. how: the three-chamber frog heart
  shot_heartA(t, st) {
    const L = this.look('heart');
    const c = V(0, 50, 0);
    this.heartAt(this.heart, c, 4.0 * CM, t, 1.6, new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, t * 0.6 - 0.4, 0.05)), 0.12);
    const p = easeInOutCubic(range(t, T.heartA, T.heartB));
    const cc = c.clone().add(V(0, 0.01, 0));
    this.cam(st, cc.clone().add(V(lerp(0.05, -0.04, p), lerp(0.02, 0.03, p), lerp(0.34, 0.24, p))), cc, 36, cc, 0.002);
    st.near = 0.01; st.exposure = L.exp; this.sun(c, 0.3, 3, L.dir, -0.0001, 0.001, 0.05);
  }
  cutBase(t, o) {
    const C = this.cut; C.group.visible = true; C.group.scale.setScalar(4.0 * CM);
    C.group.position.set(0, 50, 0); C.group.rotation.set(0, 0, 0); C.group.updateMatrixWorld(true);
    C.update(t, o);
  }
  shot_heartB(t, st) {
    const L = this.look('heart');
    const hi = [an(7, 4), an(7, 5), an(7, 6)].map(ta => smooth(range(t, ta - 0.02, ta + 0.08)) * (1 - 0.6 * smooth(range(t, ta + 0.25, ta + 0.6))));
    this.cutBase(t, { mix: 0, hi, flow: 0.6, particles: 0.0 });
    const p = easeInOutCubic(range(t, T.heartB, T.mix));
    const c = V(0, 50.008, 0);
    this.cam(st, c.clone().add(V(lerp(-0.08, -0.03, p), lerp(0.03, 0.01, p), lerp(0.3, 0.26, p))), c, 38);
    st.near = 0.01; st.exposure = L.exp; this.sun(c, 0.3, 3, V(0.2, 0.6, 0.8), -0.0001, 0.001, 0.05);
  }
  shot_mix(t, st) {
    const L = this.look('heart');
    const mix = smooth(range(t, an(7, 9), T.karisir + 0.3));
    this.cutBase(t, { mix, flow: 1, particles: smooth(range(t, T.mix, T.mix + 0.3)) });
    const p = easeInOutCubic(range(t, T.mix, T.frogsnow));
    const c = V(0, 50 - 0.004 - 0.004 * p, 0);
    this.cam(st, c.clone().add(V(lerp(0.03, 0.01, p), lerp(0.0, -0.01, p), lerp(0.18, 0.12, p))), c, 38);
    st.near = 0.005; st.exposure = L.exp; this.sun(c, 0.3, 3, V(0.2, 0.6, 0.8), -0.0001, 0.001, 0.05);
  }
  // ================================================================= 16–18. frogs freeze, hearts stop, restart in spring
  shot_frogsnow(t, st) {
    const L = this.look('winter'); this.trackWorld(1.0);
    const P = V(12, 0.0, 6.0);
    const F = this.frogSit; F.group.visible = true; F.group.position.copy(P).add(V(0, -0.002, 0)); F.group.rotation.set(0, -0.5, 0); F.group.updateMatrixWorld(true);
    const fr = 0.8 * smooth(range(t, an(8, 4), T.donar + 0.3));
    F.mat.userData.u.uFrost.value = fr; F.eyeMat.userData.u.uFrost.value = fr;
    this.snow.mesh.visible = true; this.snow.update(t * 0.6, P.clone().add(V(0, 0.08, 0)), 0.05);
    const p = easeInOutCubic(range(t, T.frogsnow, T.frozenx));
    const c = P.clone().add(V(0, 0.025, 0));
    this.cam(st, c.clone().add(V(lerp(0.16, 0.1, p), lerp(0.05, 0.035, p), lerp(0.2, 0.14, p))), c, 38, c, 0.0018);
    st.near = 0.004; st.exposure = L.exp; this.sun(c, 0.25, 3, L.dir, -0.00005, 0.0004, 0.04);
  }
  frogXray(t, ice) {
    const L = this.look('xray');
    const P = V(40, 20, 0);
    this.frogXr.visible = true; this.frogXr.position.copy(P); this.frogXr.rotation.set(0, -0.5, 0); this.frogXr.updateMatrixWorld(true);
    this.frogXr.material.userData.u.uCol.value.set(0x6fc4ff).lerp(new THREE.Color(0xd8f4ff), ice);
    const hc = this.frogXr.localToWorld(V(0, 1.3, 0.9));
    return { L, hc };
  }
  shot_frozenx(t, st) {
    const { L, hc } = this.frogXray(t, 1);
    this.heartAt(this.heartXr, hc, 0.55 * CM, t, 0, null);
    this.heartXr.material.userData.u.uCol.value.set(0x7fd8ff); this.heartXr.material.userData.u.uK.value = 0.7;
    const p = easeInOutCubic(range(t, T.frozenx, T.restart));
    this.cam(st, hc.clone().add(V(lerp(0.16, 0.12, p), lerp(0.1, 0.08, p), lerp(0.2, 0.16, p))), hc.clone().add(V(0, 0.003, 0)), 40);
    st.near = 0.004; st.exposure = L.exp;
  }
  shot_restart(t, st) {
    const warm = smooth(range(t, T.restart, T.atar));
    const { L, hc } = this.frogXray(t, 1 - warm);
    const th = range(t, T.atar - 0.02, T.atar + 0.25);
    const kick = t > T.atar - 0.02 ? Math.exp(-Math.pow((th - 0.15) / 0.12, 2)) : 0;
    const later = t > T.atar + 0.25 ? beat((t - T.atar) * 1.8) : 0;
    this.heartAt(this.heartXr, hc, 0.55 * CM * (1 + 0.35 * kick + 0.15 * later), t, 0, null);
    this.heartXr.material.userData.u.uCol.value.set(0x7fd8ff).lerp(new THREE.Color(0xff2a1a), warm);
    this.heartXr.material.userData.u.uK.value = 0.7 + 1.6 * kick + 0.4 * warm;
    const p = easeInOutCubic(range(t, T.restart, T.fridge));
    this.cam(st, hc.clone().add(V(lerp(0.12, 0.07, p), lerp(0.08, 0.05, p), lerp(0.16, 0.1, p))), hc.clone().add(V(0, 0.003, 0)), 40);
    st.roll = 0.02 * kick;
    st.near = 0.004; st.exposure = L.exp;
  }
  // ================================================================= 19–21. winter in the fridge, spring back on the track
  kitchenWorld(light = 1) {
    this.kitchen.visible = true; this.fridge.group.visible = true;
    this.fridge.hinge.rotation.y = 1.75; this.fridge.light.intensity = 3.5 * light; this.fridge.u.uFrost.value = light;
  }
  shot_fridge(t, st) {
    const L = this.look('kitchen'); this.kitchenWorld(1);
    const pos = FRIDGE_POS.clone().add(V(0, 0.13, -0.02));
    this.placeGuy(this.guy, pos, 0, 'stand', 0, { look: 0 }); this.X.uFrost.value = 0.85; this.face(this.guy, { blink: 1, worry: 0.2 });
    this.fog.mesh.visible = true;
    const p = easeInOutCubic(range(t, T.fridge, T.out));
    const c = FRIDGE_POS.clone().add(V(0, 1.15, 0));
    this.cam(st, c.clone().add(V(lerp(-0.9, -0.5, p), lerp(0.25, 0.1, p), lerp(3.1, 2.3, p))), c.clone().add(V(0, 0.05, 0)), 44, c.clone().add(V(0, 0, 0.1)), 0.008);
    this.fog.update(t, FRIDGE_POS.clone().add(V(0, 0.9, 0.35)), V(0, 0, 1), 0.25 + 0.25 * p, this.camQuat(st), 0.6);
    st.exposure = L.exp; this.sun(c, 3, 12, L.dir, -0.0003, 0.01, 0.03);
  }
  shot_out(t, st) {
    const L = this.look('kitchen'); this.kitchenWorld(1);
    const u = range(t, T.out + 0.05, T.spring + 0.3);
    const thaw = smooth(range(t, T.out, T.out + 0.6));
    const pos = FRIDGE_POS.clone().add(V(0, 0.13 * (1 - smooth(range(u, 0.1, 0.4))), -0.02 + 1.5 * easeInCubic(u)));
    if (u < 0.12) this.placeGuy(this.guy, pos, 0, 'stand', t, { look: 0, surprise: 0.4 * thaw });
    else this.placeGuy(this.guy, pos, 0, 'walk', (t - T.out) * 1.2 + 0.2, {});
    this.X.uFrost.value = 0.85 * (1 - thaw); this.face(this.guy, { blink: 1 - thaw, worry: 0.2, mouth: 0.15 * thaw });
    this.fog.mesh.visible = true;
    const p = easeInOutCubic(range(t, T.out, T.spring));
    const c = FRIDGE_POS.clone().add(V(0, 1.1, 0.4 + 0.6 * p));
    this.cam(st, c.clone().add(V(lerp(0.9, 1.2, p), lerp(0.0, 0.05, p), lerp(2.1, 2.4, p))), c, 46, pos.clone().add(V(0, 1.2, 0)), 0.008);
    this.fog.update(t, FRIDGE_POS.clone().add(V(0, 0.9, 0.35)), V(0, 0, 1), 0.5 + range(t, T.out, T.spring) * 0.8, this.camQuat(st), 1.0);
    st.exposure = L.exp; this.sun(c, 3, 12, L.dir, -0.0003, 0.01, 0.03);
  }
  shot_spring(t, st) {
    const L = this.look('spring'); this.trackWorld(0);
    const g = -5 + 7.8 * (t - T.spring), rr = -6 + 6.0 * (t - T.spring);
    this.runners(t, g, { r1x: rr, r2x: rr - 0.6, lean: 0.2 });
    const p = easeOutCubic(range(t, T.spring, DURATION));
    const c = V(g + 0.3, 1.0, TRACK_Z.guy);
    this.cam(st, c.clone().add(V(lerp(3.2, 2.6, p), lerp(-0.4, -0.3, p), lerp(1.6, 1.3, p))), c.clone().add(V(-0.6, 0.15, 0)), 46, c, 0.01);
    st.exposure = L.exp; this.sun(c, 7, 20, L.dir, -0.0004, 0.02, 0.015);
  }
}
