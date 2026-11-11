// "Asansörün halatı kopsaydı?" (METIN.md v1, 10 cumle) — full film.
// Every shot boundary, camera beat and event comes from the narration word timings:
//   an(c, w) = start of word w (1-based) of sentence c, en(c, w) = its end.  Files named in project/voice.json.
// SIMDILIK voice.json -> ses/gecici/kelimeler.json (hece tahmini). Kullanici kaydi gelince yalniz voice.json degisir.
import * as THREE from 'three';
import { clamp, lerp, range, smooth, easeInOutCubic, easeOutCubic, easeInCubic, halton, FPS } from './util.js';
import { makeGuy, guyXrayMaterial } from './characters.js';
import { buildVessels } from './vessels.js';
import { makeRibcage } from './props.js';
import { buildCabin, cabinEnvironment } from './cabin.js';
import { buildShaft, shaftEnvironment, floorY, YM, ROPE_X, CAR, RAIL_X, GOV } from './shaft.js';
import { buildRopeSnap } from './ropesnap.js';
import { buildPhone } from './phone.js';
import { buildStomach } from './organs.js';
import { Sparks, makeGlow, makeStars, makeArrow, makeLabel } from './fx.js';

// ------------------------------------------------------------------ narration timing
const VOICE = await (await fetch('./voice.json')).json();
const WORDS = await (await fetch('/job/' + VOICE.words)).json();
const SENT = {}; for (const w of WORDS) (SENT[w.c] = SENT[w.c] || []).push(w);
export const an = (c, w) => SENT[c][w - 1].s;
export const en = (c, w) => SENT[c][w - 1].e;
const LAST = WORDS[WORDS.length - 1].e;
export const DURATION = LAST + 0.6;

const V = (x, y, z) => new THREE.Vector3(x, y, z);

// METIN v1 (10 satir):
// 1 Yirminci kattasın ve asansörün halatı bir anda kopuyor. | 2 Asansör boşluğa düşerken midenin ağzına geldiğini hissedersin.
// 3 Telefonunu çıkarıp annene veda mesajı yazarsın, | 4 ve tam yere çarpacakken zıplamak için dizlerini kırarsın.
// 5 Ama asansör birkaç metre sonra kendiliğinden durur, | 6 sen de boş yere havaya zıplayıp kafanı tavana çarparsın.
// 7 Çünkü asansörler hızlandığını fark ettiği an, raylara kenetlenen bir acil frene sahiptir.
// 8 Zaten tek bir halatla değil, her biri asansörü tek başına taşıyabilen birkaç halatla asılıdır.
// 9 Son anda zıplamak da hızını neredeyse hiç azaltmaz. | 10 Yani en büyük tehlike, annene attığın o mesajdır.
export const T = {
  snap: an(1, 4), kop: an(1, 8),
  fall: an(2, 1), xst: an(2, 4),
  phone: an(3, 1), typeA: an(3, 3), sendT: an(3, 6),
  crouchA: an(4, 1), crouchB: an(4, 5), kir: an(4, 8),
  stop: an(5, 1), durur: an(5, 7),
  jump: an(6, 1), launch: an(6, 6), bonk: an(6, 7), hit: an(6, 8),
  gov: an(7, 1), trip: an(7, 6), clamp: an(7, 7), kenet: an(7, 8),
  final: an(7, 12), durdur: an(7, 18),
};
export const TIMELINE = {
  duration: DURATION,
  shots: [
    ['cabin20', 0], ['snap', T.snap], ['drop0', T.kop],                       // 1
    ['fall', T.fall], ['xstom', T.xst],                                       // 2
    ['phone', T.phone],                                                       // 3
    ['crouchA', T.crouchA], ['crouchB', T.crouchB],                           // 4
    ['stop', T.stop],                                                         // 5 (Ama: kart cevirme)
    ['jump', T.jump], ['bonk', T.bonk],                                       // 6
    ['gov', T.gov], ['clamp', T.clamp], ['final', T.final],                   // 7 (doruk + sert son)
  ].map(([id, a], i, arr) => ({ id, a, b: i + 1 < arr.length ? arr[i + 1][1] : 999 })),
  whoosh: [], flips: [],
};
{
  const at = id => TIMELINE.shots.find(s => s.id === id);
  const prev = id => TIMELINE.shots[TIMELINE.shots.indexOf(at(id)) - 1].id;
  const W = (id, pre = 0.14, post = 0.18) => TIMELINE.whoosh.push({ a: at(id).a - pre, b: at(id).a + post, from: prev(id), to: id });
  const F = (id, pre = 0.2, post = 0.26) => TIMELINE.flips.push({ a: at(id).a - pre, mid: at(id).a, b: at(id).a + post, from: prev(id), to: id });
  W('snap'); W('drop0', 0.1, 0.14); W('fall', 0.1, 0.14); W('xstom'); W('phone'); W('crouchB', 0.1, 0.14);
  W('bonk', 0.1, 0.14); W('clamp', 0.12, 0.16); W('final', 0.1, 0.14);
  F('stop'); F('gov');
}
export const SHOT_SAMPLES = { snap: 2, clamp: 1.5, gov: 1.5, bonk: 1.5 };

// ------------------------------------------------------------------ ENGLISH subtitles: [EN sentence, EN firstWord, text]
// Locked to the English narration words (VOICE.words_en). Scene timing above uses an(c,w) on the TR-indexed map.
const WORDS_EN = await (await fetch('/job/' + VOICE.words_en)).json();
const SENT_EN = {}; for (const w of WORDS_EN) (SENT_EN[w.c] = SENT_EN[w.c] || []).push(w);
const ae = (c, w) => SENT_EN[c][w - 1].s;
const SUBS = [
  [1, 1, "You're on"], [1, 3, "the 20th floor"], [1, 6, "when the elevator"], [1, 9, "cable"], [1, 10, "suddenly snaps."],
  [2, 1, "As the elevator"], [2, 4, "drops down"], [2, 6, "the shaft,"], [2, 8, "you feel"], [2, 10, "your stomach"], [2, 12, "jump into"], [2, 14, "your throat."],
  [3, 1, "You pull out"], [3, 4, "your phone"], [3, 6, "and text"], [3, 8, "your mom"], [3, 10, "goodbye,"],
  [4, 1, "and right before"], [4, 4, "you hit"], [4, 6, "the ground,"], [4, 8, "you bend"], [4, 10, "your knees"], [4, 12, "to jump."],
  [5, 1, "But after"], [5, 3, "just a few feet,"], [5, 7, "the elevator"], [5, 9, "stops"], [5, 10, "on its own,"],
  [6, 1, "and you jump"], [6, 4, "for nothing"], [6, 6, "and smack"], [6, 8, "your head"], [6, 10, "on the ceiling."],
  [7, 1, "That's because"], [7, 3, "every elevator"], [7, 5, "has a brake"], [7, 8, "underneath"], [7, 9, "that clamps"], [7, 11, "onto the rails"], [7, 14, "if it goes"], [7, 17, "too fast,"], [7, 19, "and that brake"], [7, 22, "would always"], [7, 24, "stop you."]
].map(([c, w, s]) => ({ t: ae(c, w) - 0.02, s, c, w }));
{
  const DISPLAY = {"20th": "twentieth"};   // on-screen numerals -> spoken words
  const said_ = x => { let y = x; for (const [k, v] of Object.entries(DISPLAY)) y = y.split(k).join(v); return y; };
  const norm = x => x.toLowerCase().replace(/[.,;:!?]/g, '');
  const flat = SUBS.map(g => said_(g.s).split(' ')).flat().map(norm), said = WORDS_EN.map(w => norm(w.w));
  if (flat.join(' ') !== said.join(' ')) throw new Error('subtitle text != narration: ' + flat.join(' ') + ' ||| ' + said.join(' '));
  for (const g of SUBS) { const ws = SENT_EN[g.c]; if (!ws[g.w - 1] || norm(ws[g.w - 1].w) !== norm(said_(g.s).split(' ')[0])) throw new Error('subtitle anchor mismatch ' + g.s); }
}
export const SUBTITLE_LIST = SUBS;
export function subtitleAt(frame) {
  const t = frame / FPS; let cur = null;
  for (const g of SUBS) if (t >= g.t) cur = g.s;
  return t < SUBS[0].t ? null : cur;
}

const LOOKS = {
  cabin: { sun: 0xfff4e6, sunI: 1.4, dir: V(0.12, 1, 0.22), hemiS: 0xfff1e0, hemiG: 0x30302e, hemiI: 0.35, env: 0.9, exp: 1.0, envMap: 'cabin',
    sky: [0x050505, 0x050505, 0x050505, 0x050505], ground: 0x050505, clouds: 0 },
  shaft: { sun: 0xfff3e2, sunI: 3.3, dir: V(-0.35, 0.75, 0.6), hemiS: 0xcfe6ff, hemiG: 0x6a6258, hemiI: 0.7, env: 0.9, exp: 1.0, envMap: 'shaft',
    sky: [0x0b9ff0, 0x37bdf6, 0xb8ecfc, 0xd5f4fc], ground: 0x8a8f96, clouds: 0.35 },
  machine: { sun: 0xfff1de, sunI: 2.6, dir: V(-0.45, 0.8, 0.5), hemiS: 0xd4e6ff, hemiG: 0x50483f, hemiI: 0.6, env: 0.85, exp: 1.05, envMap: 'shaft',
    sky: [0x0b9ff0, 0x37bdf6, 0xb8ecfc, 0xd5f4fc], ground: 0x8a8f96, clouds: 0.35 },
  xray: { sun: 0x9ab8ff, sunI: 0.2, dir: V(0.3, 0.8, 0.4), hemiS: 0x1a2a50, hemiG: 0x050810, hemiI: 0.2, env: 0.05, exp: 1.25,
    sky: [0x01030a, 0x040b1c, 0x0a1834, 0x0a1834], ground: 0x01030a, clouds: 0 },
};

const CABP = V(40, 0, 0);                 // cabin interior world origin (floor centre)
const GUYP = CABP.clone().add(V(0.05, 0, -0.12));
const XR = V(80, 0, 0);
const Y20 = floorY(20);
const HERO = 5;                           // rope that gets the wire-level macro (front-right from the camera)
const BROKE = (o = {}) => ROPE_X.map(() => ({ y: Y20 + CAR.top + 0.92, up: 9, flail: 0.5, stub: 0.42, stubFlail: 0.6, ...o }));

export class World {
  constructor(scene, env) {
    this.scene = scene; this.env = env; this.sampleIdx = 0;
    env.ground.visible = false; scene.fog = null;
    this.skyEnv = scene.environment; this.cabEnv = cabinEnvironment(env.renderer); this.shEnv = shaftEnvironment(env.renderer);
    this.all = [];
    const add = o => { scene.add(o); this.all.push(o); return o; };
    this.guy = makeGuy(); add(this.guy.group);
    this.X = this.guy.mats.body.userData.X;
    // worlds
    this.cab = buildCabin(); add(this.cab.group); this.cab.group.position.copy(CABP);
    this.sh = buildShaft(); add(this.sh.group);
    this.snapR = buildRopeSnap(); add(this.snapR.group);
    this.phone = buildPhone(); add(this.phone.group);
    this.phoneLight = add(new THREE.PointLight(0xbfd8ff, 0, 0.6, 2));
    this.sparks = new Sparks(700, 3); add(this.sparks.mesh); this.sparks2 = new Sparks(700, 8); add(this.sparks2.mesh);
    this.glow = add(makeGlow()); this.glow2 = add(makeGlow());
    this.sparkLight = add(new THREE.PointLight(0xffa040, 0, 3, 2));
    this.stars = makeStars(5); add(this.stars.group);
    // x-ray rig + vessels + ribcage + stomach at XR
    this.placeGuy(this.guy, XR, 0, 'stand', 0);
    const hc = this.guy.bones.Spine2.getWorldPosition(V(0, 0, 0)).lerp(this.guy.bones.Spine1.getWorldPosition(V(0, 0, 0)), 0.3).add(V(0.025, 0, 0.05));
    this.ves = buildVessels(this.guy, hc, V(0, 0, 1)); add(this.ves.group);
    this.ribs = add(makeRibcage(this.guy, guyXrayMaterial(0xbfe2ff)));
    this.stom = buildStomach(this.guy); add(this.stom.group);
    // speed arrows + labels
    this.arrowDown = add(makeArrow(0xe5322d, 2.4, 0.34)); this.arrowUp = add(makeArrow(0x2fbf4a, 0.22, 0.34));
    this.labDown = add(makeLabel(['FALL'], { color: '#ff5a4a' })); this.labUp = add(makeLabel(['JUMP'], { color: '#5cff7a' }));
    this.camQ = new THREE.Quaternion();
  }

  // ---------------------------------------------------------------- helpers
  placeGuy(rig, pos, yaw, pose, t, o = {}) {
    rig.group.visible = true; rig.pose(pose, t, o);
    rig.group.position.copy(pos); rig.group.quaternion.setFromEuler(new THREE.Euler(0, yaw, 0)); rig.group.updateMatrixWorld(true);
  }
  face(rig, o = {}) { rig.setMorph('blinkL', o.blink ?? 0); rig.setMorph('blinkR', o.blink ?? 0); rig.setMorph('worry', o.worry ?? 0); rig.setMorph('mouthOpen', o.mouth ?? 0); }
  hideAll() {
    for (const o of this.all) o.visible = false;
    this.guy.setXray(false); this.face(this.guy, {}); this.X.uFrost.value = 0; this.X.uPurple.value = 0; this.X.uHoleOn.value = 0;
    this.phoneLight.intensity = 0; this.sparkLight.intensity = 0;
    this.sh.railU.uK.value = 0; this.sh.setGear(0); this.cab.setLights(1);
  }
  look(name) {
    const L = LOOKS[name], E = this.env;
    E.sun.color.set(L.sun); E.sun.intensity = L.sunI;
    E.hemi.color.set(L.hemiS); E.hemi.groundColor.set(L.hemiG); E.hemi.intensity = L.hemiI;
    this.scene.environment = L.envMap === 'cabin' ? this.cabEnv : L.envMap === 'shaft' ? this.shEnv : this.skyEnv;
    this.scene.environmentIntensity = L.env;
    const U = E.sky.material.uniforms; U.zenith.value.set(L.sky[0]); U.upper.value.set(L.sky[1]); U.horizon.value.set(L.sky[2]); U.haze.value.set(L.sky[3]); U.groundCol.value.set(L.ground);
    U.cloudAmount.value = L.clouds;
    return L;
  }
  sun(c, size, dist, dir, bias, nbias, ang = 0.035) {
    const s = this.env.sun, sc = s.shadow.camera, i = this.sampleIdx + 1;
    const d = dir.clone().normalize();
    const u = Math.abs(d.y) > 0.99 ? V(1, 0, 0) : V(0, 1, 0).cross(d).normalize(), v = d.clone().cross(u);
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
  shake(st, t, k, f = 23) {
    if (k <= 0) return;
    const o = V(Math.sin(t * f) + 0.5 * Math.sin(t * f * 2.3 + 1), Math.sin(t * f * 1.3 + 2) + 0.5 * Math.sin(t * f * 2.9), Math.sin(t * f * 0.9 + 4) * 0.5).multiplyScalar(k);
    st.pos = st.pos.clone().add(o); st.target = st.target.clone().add(o.multiplyScalar(0.6));
  }

  // ---------------------------------------------------------------- worlds
  cabinWorld(L, { lights = 1, disp = 20, dir = 0 } = {}) {
    this.cab.group.visible = true; this.cab.setLights(lights); this.cab.setDisplay(disp, dir);
    this.sun(CABP.clone().add(V(0, 1.0, 0)), 1.0, 2.2, L.dir, -0.0002, 0.004, 0.25);
    this.env.sun.intensity = L.sunI * lights;
  }
  head() { return this.guy.bones.Head.getWorldPosition(V(0, 0, 0)); }
  eyes() { const h = this.head(); return h.add(V(0, 0.075, 0.09).applyQuaternion(this.guy.group.quaternion)); }
  // phone in the right hand, screen turned towards the eyes
  holdPhone(screen = ['chat', 0, 0], bright = 1) {
    const g = this.guy, P = this.phone.group; P.visible = true;
    const hand = g.bones.RightHand.getWorldPosition(V(0, 0, 0)), mid = g.bones.RightHandMiddle1.getWorldPosition(V(0, 0, 0));
    const fwd = V(0, 0, 1).applyQuaternion(g.group.quaternion), left = V(1, 0, 0).applyQuaternion(g.group.quaternion);
    const p = hand.clone().lerp(mid, 0.7).addScaledVector(fwd, 0.015).add(V(0, 0.035, 0)).addScaledVector(left, 0.02);
    const n = this.eyes().sub(p).normalize();
    const up = fwd.clone().addScaledVector(n, -fwd.dot(n)).normalize(), x = up.clone().cross(n).normalize();
    P.matrix.makeBasis(x, up, n).setPosition(p); P.matrix.decompose(P.position, P.quaternion, P.scale); P.updateMatrixWorld(true);
    this.phone.setScreen(screen[0], screen[1], screen[2], bright);
    this.phoneLight.intensity = 0.35 * bright; this.phoneLight.position.copy(p).addScaledVector(n, 0.06);
    return { p, n, up };
  }
  shaftWorld(L, st) { this.sh.group.visible = true; this.sh.update(st); }
  sparkFx(S, t, o, glow, light = true) {
    const alive = S.update(t, o); S.mesh.visible = alive > 0;
    const age = t - o.t0, on = age >= 0 && age < (o.dur ?? 0.6) + 0.05;
    if (!glow) return;
    glow.visible = on;
    if (on) { const org = typeof o.origin === 'function' ? o.origin(t) : o.origin; glow.position.copy(org); glow.scale.setScalar((o.glowSize ?? 0.12) * (0.8 + 0.4 * Math.sin(t * 90))); }
    if (light && on) { this.sparkLight.position.copy(glow.position); this.sparkLight.intensity = (o.lightK ?? 2.5) * (0.7 + 0.3 * Math.sin(t * 70)); this.sparkLight.distance = o.lightD ?? 2.5; }
  }

  // ================================================================= 1. cabin at the 20th floor: phone, indicator "20"
  shot_cabin20(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 20 });
    this.placeGuy(this.guy, GUYP, 0, 'phone', t, { k: 1, curl: 0.6 }); this.face(this.guy, { worry: 0.05 });
    this.holdPhone(['chat', 0, 0], 1);
    // over-the-shoulder towards the doors and the floor indicator, slow push-in, a tiny jolt right before the cut
    const p = easeInOutCubic(range(t, 0, T.snap + 0.1));
    const door = CABP.clone().add(V(0.02, 1.62, 0.75));
    this.cam(st, CABP.clone().add(V(lerp(-0.4, -0.34, p), lerp(1.9, 1.84, p), lerp(-0.66, -0.58, p))), door.clone().add(V(0.16, lerp(-0.02, -0.1, p), 0)), 62, this.phone.group.position, 0.003);
    this.shake(st, t, 0.004 * smooth(range(t, T.snap - 0.25, T.snap)), 31);
    st.near = 0.01; st.exposure = L.exp;
  }
  // ================================================================= 2. macro: the hoist rope parts wire by wire
  shot_snap(t, st) {
    const L = this.look('shaft');
    const u = range(t, T.snap + 0.05, T.kop + 0.12), sep = easeInCubic(range(t, T.kop + 0.1, T.kop + 0.6));
    const carY = Y20, hitch = carY + CAR.top + 0.5, yb = hitch + 0.42;
    const broken = ROPE_X.map((x, i) => i === HERO ? null : (u > 0.55 + 0.07 * i ? { y: yb - 0.01 * i, up: 0.6 * easeInCubic(range(u, 0.55 + 0.07 * i, 1.4)), flail: 0.6, stub: yb - hitch, stubFlail: 0.4 } : null));
    this.shaftWorld(L, { carY, cwY: Y20 - 30, broken, t });
    this.sh.ropes[HERO].m.visible = false; this.sh.stubs[HERO].m.visible = false;
    const R = this.snapR; R.group.visible = true; R.group.position.set(ROPE_X[HERO], yb, 0); R.update(u, sep, t);
    const org = V(ROPE_X[HERO], yb, 0);
    this.sparkFx(this.sparks, t, { t0: T.snap + 0.3, dur: T.kop - T.snap, origin: org, dir: V(0.3, 0.2, 1), spread: 1.3, speed: 1.6, life: 0.35, width: 0.0006, count: 220, k: 1.2, glowSize: 0.03, lightK: 0.6, lightD: 0.6 }, this.glow);
    const p = easeInOutCubic(range(t, T.snap, T.kop + 0.3));
    this.cam(st, org.clone().add(V(lerp(0.07, 0.05, p), lerp(-0.035, -0.015, p), lerp(0.13, 0.1, p))), org.clone().add(V(-0.004, 0.006, 0)), 40, org, 0.0016);
    this.shake(st, t, 0.0015 * smooth(range(t, T.kop, T.kop + 0.1)), 40);
    st.near = 0.004; st.far = 120; st.exposure = L.exp; this.sun(org, 0.4, 4, L.dir, -0.0001, 0.001, 0.03);
  }
  // ================================================================= 3. wide: ropes whip up, the car drops
  shot_drop0(t, st) {
    const L = this.look('shaft');
    const tt = range(t, T.kop - 0.05, T.fall), d = Math.min(2, 2.4 * Math.pow(Math.max(0, t - T.kop), 2)), carY = Y20 - d;
    this.shaftWorld(L, { carY, cwY: Y20 - 30 + 4 * tt, broken: BROKE({ up: 1.5 + 6 * tt * tt, flail: 1, stubFlail: 1 }), t });
    const c = V(0, carY + 2.2, 0);
    const p = easeOutCubic(tt);
    this.cam(st, c.clone().add(V(lerp(1.6, 2.0, p), lerp(1.4, 1.8, p), lerp(5.6, 6.6, p))), c.clone().add(V(0, 0.7, 0)), 46, c, 0.01);
    this.shake(st, t, 0.03 * (1 - p), 28);
    st.exposure = L.exp; this.sun(c, 5, 20, L.dir, -0.0004, 0.02, 0.02);
  }
  // ================================================================= 4. fall: floor numbers rush past
  shot_fall(t, st) {
    const L = this.look('shaft');
    const u = range(t, T.fall, T.xst), carY = Y20 - (1.4 + 4.2 * u);
    this.shaftWorld(L, { carY, cwY: Y20 - 24, broken: BROKE({ flail: 1, stubFlail: 1 }), t });
    const c = V(0, carY + 1.3, 0);
    this.cam(st, V(lerp(2.2, 1.8, u), carY - 0.3 + 0.5 * Math.sin(u * 2), lerp(4.4, 4.0, u)), c.clone().add(V(-0.2, 0.3, 0)), 50, c, 0.008);
    this.shake(st, t, 0.02, 33);
    st.exposure = L.exp; this.sun(c, 5, 20, L.dir, -0.0004, 0.02, 0.02);
  }
  // ================================================================= 5. x-ray: the stomach lifts towards the throat
  shot_xstom(t, st) {
    const L = this.look('xray');
    const lift = smooth(range(t, T.xst - 0.05, T.xst + 0.6)), fl = 0.05 * smooth(range(t, T.xst, T.phone));
    this.placeGuy(this.guy, XR.clone().add(V(0, fl, 0)), 0, 'stand', 0); this.guy.setXray(true);
    this.ves.group.visible = true; this.ves.update(t, 0.0, 0, 0.55); this.ves.group.position.y = fl;
    this.ribs.visible = true; this.ribs.material.userData.u.uK.value = 0.45; this.ribs.position.y = fl;
    this.stom.group.visible = true; this.stom.group.position.y = fl; this.stom.update(lift * (0.92 + 0.08 * Math.sin(t * 7)), t);
    const c = XR.clone().add(V(0, 1.28 + fl, 0));
    const p = easeInOutCubic(range(t, T.xst, T.phone));
    this.cam(st, c.clone().add(V(lerp(0.32, 0.2, p), lerp(-0.05, 0.02, p), lerp(1.05, 0.82, p))), c.clone().add(V(0, lerp(-0.04, 0.03, p), 0)), 40);
    st.roll = 0.03 * Math.sin(t * 2.3); st.exposure = L.exp;
  }
  // ================================================================= 6. phone close-up: the goodbye message
  shot_phone(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 19, dir: -1, lights: 0.85 + 0.15 * Math.sin(t * 37) * Math.sin(t * 11) });
    const k = smooth(range(t, T.phone - 0.1, T.phone + 0.35));
    this.placeGuy(this.guy, GUYP, 0, 'phone', t, { k: lerp(0.4, 1, k), curl: 0.6 }); this.face(this.guy, { worry: 0.8, mouth: 0.1 });
    const typed = range(t, T.typeA, T.sendT - 0.05), sent = smooth(range(t, T.sendT, T.sendT + 0.25));
    const H = this.holdPhone(['chat', typed, sent], 1.0);
    const p = easeInOutCubic(range(t, T.phone, T.crouchA));
    const camP = H.p.clone().addScaledVector(H.n, lerp(0.3, 0.24, p)).addScaledVector(H.up, lerp(-0.03, 0.0, p)).add(V(lerp(0.03, 0.01, p), 0, 0));
    this.cam(st, camP, H.p.clone().addScaledVector(H.up, 0.005), 36, H.p, 0.0025);
    this.shake(st, t, 0.0015, 29);
    st.near = 0.01; st.exposure = L.exp;
  }
  // ================================================================= 7. crouch to jump (wide, low), then the squinting face
  crouchPose(t) {
    const k = smooth(range(t, T.crouchA + 0.05, T.crouchA + 0.7));
    if (k < 0.3) this.placeGuy(this.guy, GUYP, 0, 'phone', t, { k: 1 - k / 0.3, curl: 0.4 });
    else this.placeGuy(this.guy, GUYP, 0, 'squat', t, { k: range(k, 0.3, 1) });
    return k;
  }
  shot_crouchA(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 19, dir: -1, lights: 0.8 + 0.2 * Math.sin(t * 41) * Math.sin(t * 13) });
    const k = this.crouchPose(t); this.face(this.guy, { worry: 0.9, mouth: 0.15, blink: 0.25 * k });
    if (k < 0.3) this.holdPhone(['chat', 1, 1], 1);
    const p = easeInOutCubic(range(t, T.crouchA, T.crouchB));
    const c = GUYP.clone().add(V(0, lerp(1.0, 0.72, p), 0.05));
    this.cam(st, CABP.clone().add(V(lerp(0.66, 0.6, p), lerp(1.75, 1.6, p), lerp(0.66, 0.6, p))), c, 64, c, 0.003);
    this.shake(st, t, 0.006, 27);
    st.near = 0.01; st.exposure = L.exp;
  }
  shot_crouchB(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 18, dir: -1, lights: 0.8 + 0.2 * Math.sin(t * 41) * Math.sin(t * 13) });
    this.placeGuy(this.guy, GUYP, 0, 'squat', t, { k: 1 });
    const sq = smooth(range(t, T.crouchB, T.kir));
    this.face(this.guy, { worry: 1, mouth: 0.12 + 0.1 * sq, blink: 0.35 + 0.5 * sq });
    const H = this.head().add(V(0, 0.03, 0));
    const p = easeInOutCubic(range(t, T.crouchB, T.stop));
    this.cam(st, H.clone().add(V(lerp(0.22, 0.14, p), lerp(-0.07, -0.04, p), lerp(0.5, 0.36, p))), H.clone().add(V(0, -0.01, 0)), 38, H, 0.003);
    this.shake(st, t, 0.004, 27);
    st.near = 0.01; st.exposure = L.exp;
  }
  // ================================================================= 8. "Ama": the car stops by itself (safety gear sparks)
  stopY(te) {   // car floor height: falling at v0, braking uniformly from ts to tStop, resting a few metres below floor 20
    const ts = T.stop + 0.2, tStop = T.durur + 0.05, v0 = 3.2, dec = v0 / Math.max(0.2, tStop - ts), rest = floorY(18) + 0.7;
    const rem = te < ts ? 0.5 * v0 * (tStop - ts) + v0 * (ts - te) : te < tStop ? 0.5 * dec * Math.pow(tStop - te, 2) : 0;
    return rest + rem;
  }
  shot_stop(t, st) {
    const L = this.look('shaft');
    const ts = T.stop + 0.2, tStop = T.durur + 0.05, carY = this.stopY(t);
    this.shaftWorld(L, { carY, cwY: Y20 - 24, broken: BROKE({ flail: 0.4, stubFlail: t < tStop ? 0.8 : 0.3 }), t });
    const clampK = smooth(range(t, ts - 0.05, ts + 0.1)); this.sh.setGear(clampK);
    this.sh.railU.uY0.value = carY - 0.42 - 0.1; this.sh.railU.uY1.value = this.stopY(ts) - 0.42 + 0.1; this.sh.railU.uK.value = clampK;
    for (const [S, G, s] of [[this.sparks, this.glow, -1], [this.sparks2, this.glow2, 1]])
      this.sparkFx(S, t, { t0: ts, dur: tStop - ts, origin: te => V(s * (RAIL_X - 0.03), this.stopY(te) - 0.45, 0.03), dir: V(-s * 0.4, -0.7, 0.6), spread: 0.9, speed: 3.5, life: 0.5, width: 0.0028, count: 400, glowSize: 0.25, lightK: 4, lightD: 4 }, G);
    const c = V(0, carY + 1.0, 0), p = easeInOutCubic(range(t, T.stop, T.jump));
    this.cam(st, c.clone().add(V(lerp(2.4, 1.4, p), lerp(1.0, -0.2, p), lerp(5.6, 4.5, p))), c.clone().add(V(lerp(-0.1, -0.3, p), lerp(0.3, -0.35, p), 0)), lerp(52, 48, p), c.clone().add(V(-0.3, -0.5, 0)), 0.008);
    this.shake(st, t, t > tStop ? 0.06 * Math.exp(-(t - tStop) * 6) : 0.015, 30);
    st.exposure = L.exp; this.sun(c, 5, 20, L.dir, -0.0004, 0.02, 0.02);
  }
  // ================================================================= 9. jump for nothing, head into the ceiling
  jumpPose(t) {
    const tl = T.launch, th = T.hit;
    if (t < tl - 0.08) { this.placeGuy(this.guy, GUYP, 0, 'squat', t, { k: smooth(range(t, T.jump, T.jump + 0.4)) * 0.9 }); return 0; }
    const ext = smooth(range(t, tl - 0.08, tl + 0.12));
    this.placeGuy(this.guy, GUYP, 0, 'jumpUp', t, { k: ext });
    const top = this.head().y - GUYP.y + 0.13, need = 2.34 - top;      // lift that puts the crown on the ceiling
    let h;
    if (t < tl) h = 0; else if (t < th) h = need * (1 - Math.pow(1 - range(t, tl, th), 2)); else { const dn = t - th; h = Math.max(0, need - 4.9 * dn * dn - 0.4 * dn); }
    this.guy.group.position.y += h; this.guy.group.updateMatrixWorld(true);
    return h;
  }
  shot_jump(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 18, dir: 0 });
    this.jumpPose(t); this.face(this.guy, { worry: 0.6, mouth: 0.3, blink: t > T.launch ? 0.6 : 0.2 });
    const p = easeInOutCubic(range(t, T.jump, T.bonk));
    const c = GUYP.clone().add(V(0, 1.2, 0));
    this.cam(st, CABP.clone().add(V(lerp(-0.55, -0.6, p), lerp(0.9, 1.0, p), 0.66)), c.clone().add(V(0.05, 0.1 + 0.3 * p, 0)), 66, c, 0.003);
    st.near = 0.01; st.exposure = L.exp;
  }
  shot_bonk(t, st) {
    const L = this.look('cabin'); this.cabinWorld(L, { disp: 18, dir: 0, lights: t > T.hit ? 0.75 + 0.25 * Math.cos((t - T.hit) * 50) : 1 });
    this.jumpPose(t);
    const hit = smooth(range(t, T.hit - 0.03, T.hit + 0.02));
    this.face(this.guy, { worry: 0.4 + 0.6 * hit, mouth: 0.25 + 0.35 * hit, blink: lerp(0.4, 1, hit) });
    const H = this.head().add(V(0, 0.12, 0));
    this.stars.update(t, H.clone().add(V(0, 0.02, 0)), smooth(range(t, T.hit, T.hit + 0.15)));
    const c = H.clone().add(V(0, -0.05, 0));
    const p = easeOutCubic(range(t, T.bonk, T.gov));
    this.cam(st, c.clone().add(V(lerp(-0.4, -0.34, p), lerp(-0.12, -0.08, p), lerp(0.62, 0.55, p))), c.clone().add(V(0, 0.08, 0)), 50, c, 0.003);
    this.shake(st, t, t > T.hit ? 0.012 * Math.exp(-(t - T.hit) * 7) : 0, 35);
    st.near = 0.01; st.exposure = L.exp;
  }
  // ================================================================= 10. governor macro: spins, flyweights trip, rope jaw bites
  shot_gov(t, st) {
    const L = this.look('machine');
    this.shaftWorld(L, { carY: Y20 - 2.0, cwY: Y20 - 24, t, sheaveA: 0 });
    const w = lerp(8, 26, smooth(range(t, T.gov, T.trip))), trip = smooth(range(t, T.trip, T.trip + 0.12));
    this.sh.setGovernor(t * w * (1 - 0.85 * trip) + trip * 0.5, smooth(range(t, T.trip - 0.35, T.trip + 0.05)), trip);
    const G = V(GOV.x + GOV.R, YM + 0.62, GOV.z);
    this.sparkFx(this.sparks, t, { t0: T.trip + 0.03, dur: 0.25, origin: G.clone().add(V(-GOV.R - 0.03, -0.12, 0.02)), dir: V(-0.3, 0.6, 0.8), spread: 1.0, speed: 1.8, life: 0.3, width: 0.0012, count: 120, glowSize: 0.06, lightK: 1.2, lightD: 1 }, this.glow);
    const p = easeInOutCubic(range(t, T.gov, T.clamp));
    this.cam(st, G.clone().add(V(lerp(0.55, 0.38, p), lerp(0.22, 0.12, p), lerp(0.85, 0.7, p))), G.clone().add(V(-0.08, -0.12, 0)), 44, G, 0.004);
    this.shake(st, t, t > T.trip ? 0.004 * Math.exp(-(t - T.trip) * 5) : 0, 40);
    st.near = 0.01; st.exposure = L.exp; this.sun(G, 1.5, 6, L.dir, -0.0002, 0.004, 0.03);
  }
  // ================================================================= 11. safety gear macro: wedges clamp the rail, sparks (peak)
  shot_clamp(t, st) {
    const L = this.look('shaft');
    const tc = T.kenet, tEnd = T.final - 0.15, v0 = 2.4, dec = v0 / Math.max(0.3, tEnd - tc), base = Y20 - 2.0;
    const Y = te => base - (te < tc ? v0 * (te - tc) : v0 * (Math.min(te, tEnd) - tc) - 0.5 * dec * Math.pow(Math.min(te, tEnd) - tc, 2));
    const carY = Y(t);
    this.shaftWorld(L, { carY, cwY: Y20 - 24, t, broken: BROKE({ flail: 0.3, stubFlail: 0.4 }) });
    const k = smooth(range(t, tc - 0.12, tc + 0.05)); this.sh.setGear(k);
    this.sh.railU.uY0.value = carY - 0.42 - 0.12; this.sh.railU.uY1.value = base - 0.42 + 0.1; this.sh.railU.uK.value = k;
    // contact = bottom edge of the front wedge on the blade's +z face (and the rear wedge on -z)
    const cy = te => Y(te) - 0.42 - 0.02 + 0.05 * k - 0.07;
    this.sparkFx(this.sparks, t, { t0: tc, dur: tEnd - tc, origin: te => V(-RAIL_X - 0.01, cy(te), 0.01), dir: V(-0.35, -0.55, 0.75), spread: 0.75, speed: 3.0, life: 0.6, width: 0.0011, count: 700, glowSize: 0.12, lightK: 2.2, lightD: 0.8, k: 1.3 }, this.glow);
    this.sparkFx(this.sparks2, t, { t0: tc + 0.02, dur: tEnd - tc, origin: te => V(-RAIL_X - 0.01, cy(te), -0.01), dir: V(-0.5, -0.5, -0.6), spread: 0.8, speed: 2.6, life: 0.5, width: 0.001, count: 450, glowSize: 0.05 }, this.glow2, false);
    const G = V(-RAIL_X, carY - 0.42, 0);
    const p = easeInOutCubic(range(t, T.clamp, T.final));
    // from below the car, looking up the rail: blade between the two wedges, gear hanging from the stile, sparks raining at the lens
    this.cam(st, G.clone().add(V(lerp(0.3, 0.22, p), lerp(-0.42, -0.34, p), lerp(0.36, 0.28, p))), G.clone().add(V(0.0, lerp(0.02, -0.02, p), 0.0)), 50, G.clone().add(V(0, -0.07, 0)), 0.003);
    this.shake(st, t, 0.006 * k * (t < tEnd ? 1 : Math.exp(-(t - tEnd) * 6)), 37);
    st.near = 0.01; st.exposure = L.exp; this.sun(G, 1.2, 6, L.dir, -0.0002, 0.004, 0.03);
  }
  // ================================================================= 12. hard end: the car hangs on the clamped rails
  shot_final(t, st) {
    const L = this.look('shaft');
    const tc = T.kenet, tEnd = T.final - 0.15, v0 = 2.4, base = Y20 - 2.0;
    const carY = base - (v0 * (tEnd - tc) - 0.5 * (v0 / Math.max(0.3, tEnd - tc)) * Math.pow(tEnd - tc, 2));
    this.shaftWorld(L, { carY, cwY: Y20 - 24, t, broken: BROKE({ flail: 0.15, stubFlail: 0.15 }) });
    this.sh.setGear(1);
    const cool = Math.exp(-Math.max(0, t - T.final) * 0.9);
    this.sh.railU.uY0.value = carY - 0.42 - 0.12; this.sh.railU.uY1.value = base - 0.42 + 0.1; this.sh.railU.uK.value = cool;
    for (const [S, s] of [[this.sparks, -1], [this.sparks2, 1]])
      this.sparkFx(S, t, { t0: T.final - 0.6, dur: 0.75, origin: V(s * (RAIL_X + 0.01), carY - 0.52, 0.01), dir: V(-s * 0.3, -0.8, 0.5), spread: 0.8, speed: 1.6, life: 0.5, width: 0.0018, count: 160, k: 0.8 }, null);
    const c = V(0, carY + 1.0, 0), p = easeInOutCubic(range(t, T.final, DURATION));
    this.cam(st, c.clone().add(V(lerp(-0.9, 1.3, p), lerp(-1.3, 0.3, p), lerp(1.9, 5.2, p))), c.clone().add(V(lerp(-0.6, 0, p), lerp(-1.25, 0.1, p), 0)), lerp(46, 50, p), c.clone().add(V(-0.3, -0.6, 0)), 0.008);
    this.shake(st, t, t > T.durdur ? 0.03 * Math.exp(-(t - T.durdur) * 8) : 0, 30);
    st.exposure = L.exp; this.sun(c, 5, 20, L.dir, -0.0004, 0.02, 0.02);
  }

}
