// "Ya bir sivrisinek senin boyunda olsaydı?" (METIN v3, kullanicinin kendi kaydi) — full film.
// Every shot boundary, camera beat and event is derived from the narration word timings:
//   an(c, w) = start of word w (1-based) of sentence c, en(c, w) = its end.
// The narration files are named in ONE place: project/voice.json  ({ "words": ..., "audio": ... }, paths
// relative to the job folder). Swapping the temporary Edge TTS for the ElevenLabs take = replace those two files.
import * as THREE from 'three';
import { clamp, lerp, range, smooth, easeInOutCubic, easeOutCubic, easeInCubic, halton, FPS } from './util.js';
import { buildMosquito } from './mosquito.js';
import { makeForearm, ARM_R } from './skin.js';
import { makeGuy } from './characters.js';
import { makeBedroom, makeBlanket, MATTRESS_TOP } from './room.js';
import { buildVessels } from './vessels.js';
import { buildSection, SEC } from './section.js';

// ------------------------------------------------------------------ narration timing
const VOICE = await (await fetch('./voice.json')).json();
const WORDS = await (await fetch('/job/' + VOICE.words)).json();
const SENT = {}; for (const w of WORDS) (SENT[w.c] = SENT[w.c] || []).push(w);
export const an = (c, w) => SENT[c][w - 1].s;
export const en = (c, w) => SENT[c][w - 1].e;
const LAST = WORDS[WORDS.length - 1].e;
export const DURATION = LAST + 0.6;

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const MM = 0.001;
const GIANT_S = 0.28;                                   // metres per mosquito body unit
const GUY_POS = V(0.9, MATTRESS_TOP + 0.115, -0.02);
const GIANT_POS = V(0.98, MATTRESS_TOP + 0.13, 0.0);
const FLOOR_Y = 0.0;
const GUY_STAND = V(3.05, 0, -0.2), GUY_STAND_YAW = -Math.PI / 2 - 0.25;   // ending: standing next to the fallen mosquito

// ------------------------------------------------------------------ timeline (all from word times)
// METIN v3 (user's own recording, 12 sentences):
//  1 Bir sivrisinek bir anda senin boyuna gelseydi | 2 yaklaşık 100 kilo olurdu. | 3 Ve tek öğünde kendi ağırlığı kadar kan içebilirdi.
//  4 Senin vücudunda ise sadece 5 litre kan var. | 5 Yani seni birkaç saniyede kurutabilirdi. | 6 Ama ona o fırsat kalmazdı.
//  7 Çünkü sivrisineklerin akciğeri yok. | 8 Oksijen vücudundaki ince borulardan kendiliğinden süzülür.
//  9 Bu borular bu kadar büyük bir gövdeye oksijen yetiştiremez. | 10 Bacakları da ayrı dert.
// 11 Boyu 300 kat büyüyünce ağırlığı milyonlarca kat artar ama bacakları o kadar güçlenmez.
// 12 İlk adımında bacakları kırılır, nefessiz kalır ve yere yığılır. Ve sen hayatında ilk kez bir sivrisineğe acırsın.
export const T = {
  grow0: an(1, 5) - 0.32,
  night0: an(1, 5) + 0.04, grow1: an(1, 7) + 0.25,
  reveal0: an(2, 1),
  probe0: an(3, 1), pierce0: an(3, 3), bite: an(3, 5) - 0.05, balloon0: an(3, 7),
  x1: an(4, 1), xw: an(4, 4),
  x3: an(5, 1), dry0: an(5, 4),
  door0: an(6, 1),
  tr0: an(7, 1), tr1: an(8, 1), tr1b: an(8, 4), tr2a: an(9, 1), tr2: an(9, 5), o2out: an(9, 8),
  legsA: an(10, 1),
  sc0: an(11, 1), sc1: an(11, 5), sc2: an(11, 9),
  legsB: an(12, 1), crack: an(12, 4), fall0: an(12, 5), thud: an(12, 9),
  fin0: an(12, 10), fin1: an(12, 13),
};
export const TIMELINE = {
  duration: DURATION,
  shots: [
    ['macro', 0], ['night', T.night0],                                   // 1
    ['reveal', T.reveal0],                                               // 2
    ['probe', T.probe0], ['pierce', T.pierce0], ['balloon', T.balloon0], // 3
    ['xray1', T.x1], ['xrayW', T.xw],                                    // 4
    ['xray3', T.x3], ['dry', T.dry0],                                    // 5
    ['door', T.door0],                                                   // 6
    ['tr1', T.tr0],                                                      // 7
    ['tr2', T.tr1], ['tr1b', T.tr1b],                                    // 8
    ['trBig', T.tr2a], ['tr3', T.tr2],                                   // 9
    ['legsA', T.legsA],                                                  // 10
    ['sc1', T.sc0], ['sc2', T.sc1], ['sc3', T.sc2],                      // 11
    ['legsB', T.legsB], ['fall', T.fall0], ['fin1', T.fin0], ['fin2', T.fin1], // 12
  ].map(([id, a], i, arr) => ({ id, a, b: i + 1 < arr.length ? arr[i + 1][1] : 999 })),
  whoosh: [],
  flips: [],
};
{
  const at = id => TIMELINE.shots.find(s => s.id === id);
  const prev = id => TIMELINE.shots[TIMELINE.shots.indexOf(at(id)) - 1].id;
  const W = (id, pre = 0.14, post = 0.18) => TIMELINE.whoosh.push({ a: at(id).a - pre, b: at(id).a + post, from: prev(id), to: id });
  const F = (id, pre = 0.2, post = 0.26) => TIMELINE.flips.push({ a: at(id).a - pre, mid: at(id).a, b: at(id).a + post, from: prev(id), to: id });
  W('night', 0.16, 0.2); W('reveal', 0.12, 0.16); W('pierce'); W('xray1'); W('dry', 0.1, 0.14); W('tr2', 0.1, 0.14); W('legsA'); W('sc1'); W('sc3', 0.1, 0.14); W('legsB', 0.1, 0.14); W('fin1');
  F('door'); F('tr1');
}
export const SHOT_SAMPLES = { macro: 3, pierce: 2, sc3: 1.5 };   // sample multipliers (shallow DOF shots)

// ------------------------------------------------------------------ subtitles: [sentence, firstWord, text]
const SUBS = [
  [1, 1, 'Bir sivrisinek'], [1, 3, 'bir anda'], [1, 5, 'senin boyuna'], [1, 7, 'gelseydi'],
  [2, 1, 'yaklaşık'], [2, 2, '100 kilo'], [2, 4, 'olurdu.'],
  [3, 1, 'Ve tek öğünde'], [3, 4, 'kendi ağırlığı'], [3, 6, 'kadar kan'], [3, 8, 'içebilirdi.'],
  [4, 1, 'Senin vücudunda'], [4, 3, 'ise sadece'], [4, 5, '5 litre'], [4, 7, 'kan var.'],
  [5, 1, 'Yani seni'], [5, 3, 'birkaç saniyede'], [5, 5, 'kurutabilirdi.'],
  [6, 1, 'Ama ona'], [6, 3, 'o fırsat'], [6, 5, 'kalmazdı.'],
  [7, 1, 'Çünkü'], [7, 2, 'sivrisineklerin'], [7, 3, 'akciğeri yok.'],
  [8, 1, 'Oksijen'], [8, 2, 'vücudundaki'], [8, 3, 'ince borulardan'], [8, 5, 'kendiliğinden'], [8, 6, 'süzülür.'],
  [9, 1, 'Bu borular'], [9, 3, 'bu kadar büyük'], [9, 6, 'bir gövdeye'], [9, 8, 'oksijen'], [9, 9, 'yetiştiremez.'],
  [10, 1, 'Bacakları da'], [10, 3, 'ayrı dert.'],
  [11, 1, 'Boyu 300 kat'], [11, 4, 'büyüyünce'], [11, 5, 'ağırlığı'], [11, 6, 'milyonlarca kat'], [11, 8, 'artar'], [11, 9, 'ama bacakları'], [11, 11, 'o kadar'], [11, 13, 'güçlenmez.'],
  [12, 1, 'İlk adımında'], [12, 3, 'bacakları'], [12, 4, 'kırılır,'], [12, 5, 'nefessiz kalır'], [12, 7, 've yere'], [12, 9, 'yığılır.'],
  [12, 10, 'Ve sen'], [12, 12, 'hayatında'], [12, 13, 'ilk kez'], [12, 15, 'bir sivrisineğe'], [12, 17, 'acırsın.'],
].map(([c, w, s]) => ({ t: an(c, w) - 0.02, s, c, w }));
// every word of the narration must be covered by exactly one group, in order (fail loudly otherwise)
{
  const flat = SUBS.map(g => g.s.split(' ')).flat().map(x => x.toLocaleLowerCase('tr').replace(/[.,]/g, ''));
  const said = WORDS.map(w => w.w.toLocaleLowerCase('tr').replace(/[.,]/g, ''));
  if (flat.join(' ') !== said.join(' ')) throw new Error('subtitle text != narration:\n' + flat.join(' ') + '\n' + said.join(' '));
}
export const SUBTITLE_LIST = SUBS;
export function subtitleAt(frame) {
  const t = frame / FPS; let cur = null;
  for (const g of SUBS) if (t >= g.t) cur = g.s;
  return t < SUBS[0].t ? null : cur;
}

const LOOKS = {
  night: { sun: 0x8fb0ff, sunI: 1.5, dir: V(0.25, 0.75, -0.62), hemiS: 0x31477e, hemiG: 0x0d0f18, hemiI: 0.35, env: 0.10, exp: 1.85,
    sky: [0x020614, 0x07122c, 0x1a2c58, 0x1a2c58], ground: 0x070b16, clouds: 0 },
  morning: { sun: 0xfff1dc, sunI: 3.4, dir: V(0.3, 0.62, -0.72), hemiS: 0xcfe6ff, hemiG: 0x8a6a4a, hemiI: 0.55, env: 0.55, exp: 1.05,
    sky: [0x3c9be8, 0x6cc0f2, 0xcdeafa, 0xdcf0fa], ground: 0x6f9a52, clouds: 0.35 },
  xray: { sun: 0x9ab8ff, sunI: 0.2, dir: V(0.3, 0.8, 0.4), hemiS: 0x1a2a50, hemiG: 0x050810, hemiI: 0.2, env: 0.05, exp: 1.25,
    sky: [0x02040c, 0x050c1e, 0x0b1a3a, 0x0b1a3a], ground: 0x02040c, clouds: 0 },
  section: { sun: 0xfff3e6, sunI: 3.0, dir: V(0.35, 0.8, 0.5), hemiS: 0xdfe8ff, hemiG: 0x6a4a3a, hemiI: 0.6, env: 0.5, exp: 1.0,
    sky: [0x2a4f7a, 0x46719c, 0x9ab8d4, 0xb8cde0], ground: 0x3a4a5a, clouds: 0 },
  studio: { sun: 0xffffff, sunI: 3.1, dir: V(0.45, 0.75, 0.5), hemiS: 0xcfe9ff, hemiG: 0x2a90c0, hemiI: 0.6, env: 0.8, exp: 1.0,
    sky: [0x1f8fe8, 0x4fb4f6, 0xbfe6fb, 0xd8f1fc], ground: 0x26b4f0, clouds: 0.3 },
};

// body height field (torso + legs; arms optional) on a 2 cm grid, softened for the drape
function bodyHeightField(rig, withArms = false) {
  const d = rig.mh2, v = new THREE.Vector3();
  const skip = new Set(d.bones.map((n, i) => (withArms ? /^Head/ : /Arm|Hand|Head|Neck|Shoulder/).test(n) ? i : -1).filter(i => i >= 0));
  const X0 = -0.6, Z0 = -1.1, C = 0.02, NX = 110, NZ = 110, hf = new Float32Array(NX * NZ).fill(-1);
  for (const part of ['body', 'clothes']) {
    const mesh = rig.parts[part], p = d.parts.find(q => q.name === part);
    mesh.updateMatrixWorld(true); mesh.skeleton.update();
    const N = p.pos.length / 3;
    for (let i = 0; i < N; i++) {
      let wa = 0; for (let k = 0; k < 4; k++) if (skip.has(p.skinIdx[i * 4 + k])) wa += p.skinW[i * 4 + k]; if (wa > 0.15) continue;
      mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld);
      const gx = Math.floor((v.x - X0) / C), gz = Math.floor((v.z - Z0) / C);
      if (gx < 0 || gz < 0 || gx >= NX || gz >= NZ) continue;
      hf[gz * NX + gx] = Math.max(hf[gz * NX + gx], v.y);
    }
  }
  // smoothed raw peaks (dilate 3 cells, blur 3x) so toes never poke through but no sharp spikes either
  let raw = Float32Array.from(hf);
  for (let it = 0; it < 3; it++) { const b2 = new Float32Array(raw); for (let z = 1; z < NZ - 1; z++) for (let x = 1; x < NX - 1; x++) { let m = raw[z * NX + x]; for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) m = Math.max(m, raw[(z + dz) * NX + x + dx] - 0.012); b2[z * NX + x] = m; } raw = b2; }
  for (let it = 0; it < 3; it++) { const b2 = new Float32Array(raw); for (let z = 1; z < NZ - 1; z++) for (let x = 1; x < NX - 1; x++) { let s2 = 0; for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) s2 += raw[(z + dz) * NX + x + dx]; b2[z * NX + x] = s2 / 9; } raw = b2; }
  let a = hf;
  for (let it = 0; it < 9; it++) { const b = new Float32Array(a); for (let z = 1; z < NZ - 1; z++) for (let x = 1; x < NX - 1; x++) { let m = a[z * NX + x]; for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) m = Math.max(m, a[(z + dz) * NX + x + dx] - 0.022); b[z * NX + x] = m; } a = b; }
  for (let it = 0; it < 16; it++) { const b = new Float32Array(a); for (let z = 1; z < NZ - 1; z++) for (let x = 1; x < NX - 1; x++) { let s = 0; for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) s += a[(z + dz) * NX + x + dx]; b[z * NX + x] = s / 9; } a = b; }
  for (let i = 0; i < a.length; i++) a[i] = Math.max(a[i], raw[i] + 0.015);
  return (x, z) => { const fx = Math.min(NX - 1.001, Math.max(0, (x - X0) / C)), fz = Math.min(NZ - 1.001, Math.max(0, (z - Z0) / C)); const x0 = Math.floor(fx), z0 = Math.floor(fz), u = fx - x0, w = fz - z0;
    const A = a[z0 * NX + x0], B = a[z0 * NX + x0 + 1], Cc = a[(z0 + 1) * NX + x0], Dd = a[(z0 + 1) * NX + x0 + 1]; return (A * (1 - u) + B * u) * (1 - w) + (Cc * (1 - u) + Dd * u) * w; };
}

// leg cross-section prop for the scale shot (units: mosquito body units)
function makeLegSection() {
  const g = new THREE.Group();
  const shell = new THREE.MeshPhysicalMaterial({ color: 0x15110f, roughness: 0.7, sheen: 1, sheenColor: new THREE.Color(0.55, 0.5, 0.45), side: THREE.DoubleSide });
  const u = { uCrack: { value: 0 } };
  shell.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vO;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvO = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vO; uniform float uCrack;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        float ring = step(0.82, fract(vO.y * 0.55)); diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.8), ring * 0.8);`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        { float a = atan(vO.z, vO.x); float y = vO.y;
          float path = 0.35 * sin(y * 7.0) + 0.18 * sin(y * 19.0 + 1.0) + 0.08 * sin(y * 43.0);
          float d = abs(a - 0.6 - path);
          float reach = smoothstep(-1.0, 1.0, (uCrack * 2.6 - 1.3) * 3.0 - abs(y - 1.5));
          float c = (1.0 - smoothstep(0.0, 0.035, d)) * reach;
          diffuseColor.rgb *= 1.0 - c;
          totalEmissiveRadiance += vec3(1.0, 0.08, 0.04) * c * 2.5 + vec3(1.0, 0.1, 0.05) * (1.0 - smoothstep(0.0, 0.15, d)) * reach * 0.4; }`);
  };
  shell.customProgramCacheKey = () => 'legsec';
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 6, 96, 120, true), shell); tube.castShadow = true; g.add(tube);
  const cap = new THREE.Group(); cap.position.y = 3.0; cap.rotation.x = -Math.PI / 2; g.add(cap);
  cap.add(new THREE.Mesh(new THREE.RingGeometry(0.4, 0.5, 96), new THREE.MeshStandardMaterial({ color: 0x2a201a, roughness: 0.5 })));
  cap.add(new THREE.Mesh(new THREE.RingGeometry(0.36, 0.4, 96), new THREE.MeshStandardMaterial({ color: 0xc89a5a, roughness: 0.4 })));
  const inner = new THREE.Mesh(new THREE.CircleGeometry(0.36, 96), new THREE.MeshPhysicalMaterial({ color: 0x9a8a5a, roughness: 0.3, clearcoat: 1 })); inner.position.z = -0.002; cap.add(inner);
  for (let i = 0; i < 7; i++) { const a = i / 7 * Math.PI * 2; const m = new THREE.Mesh(new THREE.CircleGeometry(0.09, 32), new THREE.MeshStandardMaterial({ color: 0xb04848, roughness: 0.5 })); m.position.set(Math.cos(a) * 0.2, Math.sin(a) * 0.2, 0.001); cap.add(m); }
  return { group: g, u };
}
function makeArrow() {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xe0201a, roughness: 0.3, clearcoat: 0.8 });
  const g = new THREE.Group();
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.55, 48), m); sh.position.y = 0.42; g.add(sh);
  const hd = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.3, 48), m); hd.rotation.x = Math.PI; hd.position.y = 0.0; g.add(hd);
  g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return g;
}

export class World {
  constructor(scene, env) {
    this.scene = scene; this.env = env; this.sampleIdx = 0;
    env.ground.visible = false;
    scene.fog = null;
    this.room = makeBedroom(); scene.add(this.room.group);
    this.guy = makeGuy(); scene.add(this.guy.group);
    this.lieQ = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(V(0, 0, -1), V(-1, 0, 0), V(0, 1, 0)));
    this.placeGuy('sleep', 0, {});
    this.hfSleep = bodyHeightField(this.guy, false);
    this.hfCover = bodyHeightField(this.guy, true);
    this.blanket = makeBlanket(this.hfSleep); scene.add(this.blanket);
    const fa = this.guy.bones.RightForeArm.getWorldPosition(V(0, 0, 0)), ha = this.guy.bones.RightHand.getWorldPosition(V(0, 0, 0));
    const axis = ha.clone().sub(fa); axis.y = 0; axis.normalize();
    this.armYaw = Math.atan2(-axis.z, axis.x);
    this.MACRO = fa.clone().lerp(ha, 0.55).add(V(0, 0.032, 0));
    this.ves = buildVessels(this.guy, this.MACRO.clone().add(V(0, -0.015, 0)), V(0, 1, 0)); scene.add(this.ves.group);

    this.arm = makeForearm();
    this.arm.group.scale.setScalar(MM); this.arm.group.position.copy(this.MACRO); this.arm.group.rotation.y = this.armYaw; scene.add(this.arm.group);
    this.mq = buildMosquito({ curvR: ARM_R, hindUp: 1.0, detail: 1 }); scene.add(this.mq.group);
    this.giant = buildMosquito({ curvR: Infinity, hindUp: 0.85, detail: 1, bite: false, legSpread: 0.55, reach: 0.5 }); scene.add(this.giant.group);
    this.facts = buildMosquito({ curvR: Infinity, hindUp: 0.85, detail: 0.3, bite: false, legSpread: 0.55, reach: 0.5, cards: false, trachea: true }); scene.add(this.facts.group);
    this.facts.setXray(true, 0x6fc4ff, 0.8); this.facts.trachea.visible = true;
    this.sec = buildSection(); scene.add(this.sec.group); this.sec.setFabric(false);
    this.hfEmpty = Object.assign(() => -1, { id: 2 });
    this.legSec = makeLegSection(); scene.add(this.legSec.group);
    this.arrow = makeArrow(); scene.add(this.arrow);
    this.biteSolve = this.solveBite();
  }

  // ---------------------------------------------------------------- helpers
  placeGuy(pose, t, o) {
    const gu = this.guy; gu.pose(pose, t, o);
    gu.group.position.copy(GUY_POS); gu.group.quaternion.copy(this.lieQ); gu.group.scale.setScalar(1);
    gu.group.updateMatrixWorld(true);
  }
  placeGuyStanding(pos, yaw, t, o = {}) {
    const gu = this.guy; gu.pose('stand', t, o);
    gu.group.position.copy(pos); gu.group.quaternion.setFromEuler(new THREE.Euler(0, yaw, 0)); gu.group.updateMatrixWorld(true);
  }
  face(o = {}) { const g = this.guy; g.setMorph('blinkL', o.blinkL ?? o.blink ?? 0); g.setMorph('blinkR', o.blinkR ?? o.blink ?? 0); g.setMorph('worry', o.worry ?? 0); g.setMorph('mouthOpen', o.mouth ?? 0); g.setDry(o.dry ?? 0); }
  headW() { return this.guy.bones.Head.getWorldPosition(V(0, 0, 0)).add(V(0, 0.06, 0)); }
  hideAll() {
    for (const o of [this.arm.group, this.mq.group, this.giant.group, this.facts.group, this.guy.group, this.room.group, this.blanket, this.ves.group, this.sec.group, this.legSec.group, this.arrow]) o.visible = false;
    this.env.ground.visible = false; this.blanket.castShadow = true;
    this.guy.setXray(false); this.giant.setXray(false); this.giant.setFill(0, 0);
    this.face({});
  }
  look(name) {
    const L = LOOKS[name], E = this.env;
    E.sun.color.set(L.sun); E.sun.intensity = L.sunI;
    E.hemi.color.set(L.hemiS); E.hemi.groundColor.set(L.hemiG); E.hemi.intensity = L.hemiI;
    this.scene.environmentIntensity = L.env;
    const U = E.sky.material.uniforms; U.zenith.value.set(L.sky[0]); U.upper.value.set(L.sky[1]); U.horizon.value.set(L.sky[2]); U.haze.value.set(L.sky[3]); U.groundCol.value.set(L.ground);
    U.cloudAmount.value = L.clouds;
    this.room.moon.visible = name === 'night';
    return L;
  }
  sun(c, size, dist, dir, bias, nbias, ang = 0.035) {
    const s = this.env.sun, sc = s.shadow.camera, i = this.sampleIdx + 1;
    const d = dir.clone().normalize();
    const u = V(0, 1, 0).cross(d).normalize(), v = d.clone().cross(u);
    const r = Math.sqrt(halton(i, 2)) * ang, a = halton(i, 3) * Math.PI * 2;
    const jd = d.clone().addScaledVector(u, Math.cos(a) * r).addScaledVector(v, Math.sin(a) * r).normalize();
    s.target.position.copy(c); s.position.copy(c).addScaledVector(jd, dist);
    sc.left = -size; sc.right = size; sc.top = size; sc.bottom = -size; sc.near = dist * 0.2; sc.far = dist * 2; sc.updateProjectionMatrix();
    s.shadow.bias = bias; s.shadow.normalBias = nbias;
    s.target.updateMatrixWorld(); s.updateMatrixWorld();
  }
  roomSun(L, c = V(0.4, 0.8, 0)) { this.sun(c, 2.8, 6, L.dir, -0.0002, 0.006, 0.012); }
  apply(shot, t) {
    this.hideAll();
    const st = { pos: V(0, 1, 5), target: V(0, 1, 0), fov: 40, aperture: 0, roll: 0, exposure: 1, near: 0.02, far: 300 };
    this['shot_' + shot](t, st);
    return st;
  }
  cam(st, pos, target, fov, focusPt = null, aperture = 0) { st.pos = pos; st.target = target; st.fov = fov; if (focusPt) { st.focus = pos.distanceTo(focusPt); st.aperture = aperture; } }
  placeGiant(G, S, pos, yaw) {
    G.group.visible = true;
    G.group.scale.setScalar(S); G.group.position.copy(pos).add(V(0, -G.FOOT * S, 0));
    G.group.rotation.set(0, yaw, 0);
    G.group.updateMatrixWorld(true);
  }
  tipW(G) { G.group.updateMatrixWorld(true); return G.head.localToWorld(V(0, -1.07, 2.33)); }
  solveBite() {
    const G = this.giant, target = this.MACRO.clone().add(V(0, -0.012, 0));
    let pos = V(0.55, GIANT_POS.y, 0.62), pitch = 0.4, yaw = 0;
    G.root.position.set(0, 0, 0); G.root.rotation.set(0, 0, 0); G.root.scale.set(1, 1, 1);
    for (let it = 0; it < 40; it++) {
      const dir = target.clone().sub(pos); yaw = Math.atan2(dir.x, dir.z);
      G.head.rotation.set(pitch, 0, 0); this.placeGiant(G, GIANT_S, pos, yaw);
      const d = target.clone().sub(this.tipW(G));
      pos.x += d.x * 0.8; pos.z += d.z * 0.8; pitch = clamp(pitch - d.y * 1.6, -0.3, 1.3);
    }
    return { pos, yaw, pitch };
  }
  giantBite(fill = 0, glow = 0, pitchOff = 0) {
    const G = this.giant, B = this.biteSolve;
    G.root.position.set(0, 0, 0); G.root.rotation.set(0, 0, 0); G.root.scale.set(1, 1, 1);
    G.head.rotation.set(B.pitch + pitchOff, 0, 0);
    G.setWings(0, 0, 0.05); G.setFill(fill, glow); G.setLegs(null);
    this.placeGiant(G, GIANT_S, B.pos, B.yaw);
  }
  // ---------------------------------------------------------------- 1. macro: tiny mosquito biting, starts to grow
  growK(t) { const u = range(t, T.grow0, T.night0 + 0.25); return Math.pow(10, u * u * (1.4 - 0.4 * u)); }
  shot_macro(t, st) {
    const L = this.look('night');
    this.arm.group.visible = true; this.mq.group.visible = true; this.room.group.visible = true; this.blanket.visible = true;
    this.blanket.update({}); this.blanket.castShadow = false;   // the blanket must not shade the macro skin patch
    const k = this.growK(t), m = this.mq;
    const swell = 1 + 0.05 * smooth(range(t, 0.2, T.grow0));
    m.root.position.set(0, Math.sin(t * 9.0) * 0.012, 0); m.root.rotation.set(0, Math.PI / 2, 0); m.root.scale.set(swell, swell, 1);
    m.setWings(t, 0, 0.04 * Math.sin(t * 3.1));
    m.group.scale.setScalar(MM * k); m.group.rotation.set(0, this.armYaw, 0);
    m.group.position.copy(this.MACRO).add(V(0, -m.FOOT * MM * k, 0)); m.group.updateMatrixWorld(true);
    const push = easeInOutCubic(range(t, 0, T.grow0));
    const c0 = V(12.0 - 1.6 * push, 9.0 - 1.1 * push, 4.2 - 0.5 * push), look0 = V(-0.6, 1.8, 0.0);
    const g = range(t, T.grow0, T.night0 + 0.2), e = g * g;
    const pull = 1 + (k - 1) * 0.95 + 5 * e;
    const toW = p => p.clone().applyAxisAngle(V(0, 1, 0), this.armYaw).multiplyScalar(MM).add(this.MACRO);
    st.pos = toW(c0.clone().multiplyScalar(pull).add(V(0, 6 * e * k * 0.3, 0)));
    st.target = toW(look0.clone().multiplyScalar(k));
    st.fov = 34 + 8 * e; st.near = 0.0004 * pull; st.far = 300;
    st.focus = st.pos.distanceTo(toW(V(1.6, 2.2, 0).multiplyScalar(k)));
    st.aperture = 0.00016 * pull * (1 - 0.5 * e);
    st.exposure = L.exp;
    this.sun(this.MACRO.clone(), 0.03 * Math.max(1, k * 0.7), 0.6, L.dir, -0.00002, 0.00002, 0.03);
  }
  // ---------------------------------------------------------------- 2. night: grows to human size next to him
  shot_night(t, st) {
    const L = this.look('night');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true; this.blanket.update({});
    this.placeGuy('sleep', t, {}); this.face({ blink: 1 });
    const u = range(t, T.night0 - 0.1, T.grow1);
    const S = lerp(0.012, GIANT_S, easeOutCubic(u)) * (1 + 0.05 * Math.sin(range(t, T.grow1 - 0.25, T.grow1) * Math.PI));
    const G = this.giant;
    G.root.scale.set(1, 1, 1); G.root.position.set(0, 0, 0); G.root.rotation.set(0, 0, 0); G.head.rotation.set(0, 0, 0); G.setLegs(null);
    G.setWings(t, 0.3 * smooth(range(t, T.grow1 - 0.4, T.grow1 - 0.1)), 0.1);
    const base = this.MACRO.clone().lerp(GIANT_POS.clone().add(V(-0.35, 0.02, 0.05)), easeOutCubic(u));
    this.placeGiant(G, S, base, lerp(this.armYaw + Math.PI / 2, -Math.PI / 2 + 0.12, smooth(u)));
    const cu = easeOutCubic(range(t, T.night0 - 0.1, T.reveal0));
    const start = this.MACRO.clone().add(V(0.18, 0.14, 0.2)), end = V(1.55, 2.25, 2.25);
    this.cam(st, start.lerp(end, cu), this.MACRO.clone().lerp(V(0.35, 0.95, 0.0), cu), lerp(40, 48, cu), base.clone().add(V(0, 0.3 * S / GIANT_S, 0)), 0.004);
    st.exposure = L.exp; this.roomSun(L);
  }
  // ---------------------------------------------------------------- 3. morning: wakes up (face close-up)
  morningGiant(t, tilt = 0) {
    const G = this.giant;
    G.root.scale.set(1.04, 1.04, 1); G.root.position.set(0, Math.sin(t * 5.0) * 0.01, 0); G.root.rotation.set(0, 0, 0);
    G.head.rotation.set(0.12 + 0.1 * tilt, 0.15 * tilt, 0.42 * tilt);
    G.setWings(t, 0, 0.05); G.setLegs(null);
    this.placeGiant(G, GIANT_S, GIANT_POS, -Math.PI / 2 - 0.1);
  }
  shot_wake(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true; this.blanket.update({});
    const op = smooth(range(t, T.open - 0.1, T.open + 0.15));
    this.placeGuy('awake', t, { up: 0.15 * op, lookY: 0.2, roll: 0.12 });
    this.face({ blink: 1 - op * 0.95, worry: 0.3 * op });
    this.morningGiant(t);
    const H = this.headW(), p = range(t, T.wake0, T.reveal0);
    const pos = H.clone().add(V(lerp(0.2, 0.15, p), lerp(0.5, 0.4, p), lerp(0.16, 0.12, p)));
    this.cam(st, pos, H.clone().add(V(0.03, -0.03, 0)), 34, H, 0.003);
    st.exposure = L.exp; this.roomSun(L, H);
  }
  // ---------------------------------------------------------------- 4. reveal: 100 kg bug at the foot of the bed
  shot_reveal(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true; this.blanket.update({});
    this.placeGuy('awake', t, { up: 0.5, lookY: 0.0, roll: 0.05 }); this.face({ worry: 0.6 });
    this.morningGiant(t, 0.25 * smooth(range(t, T.reveal0, T.probe0)));
    const G = this.giant, hw = G.head.getWorldPosition(V(0, 0, 0));
    const p = easeInOutCubic(range(t, T.reveal0, T.probe0));
    const ang = lerp(0.55, 0.85, p), r = lerp(1.45, 1.25, p);
    const pos = hw.clone().add(V(-Math.cos(ang) * r, lerp(0.15, 0.25, p), Math.sin(ang) * r));
    this.cam(st, pos, hw.clone().add(V(0.3, -0.12, 0.02)), 40, hw, 0.006);
    st.exposure = L.exp; this.roomSun(L, hw);
  }
  // ---------------------------------------------------------------- 5. over the shoulder: it is watching you
  shot_ots(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true; this.blanket.update({});
    this.placeGuy('awake', t, { up: 0.75, lookY: 0.0, roll: 0.0 }); this.face({ worry: 1, mouth: 0.25 });
    const tilt = smooth(range(t, T.ots0 + 0.2, T.ots0 + 0.9));
    this.morningGiant(t, 0.5 + 0.5 * tilt);
    const H = this.headW(), hw = this.giant.head.getWorldPosition(V(0, 0, 0));
    const p = easeInOutCubic(range(t, T.ots0, T.pull0));
    const pos = H.clone().add(V(-0.22 - 0.05 * p, 0.2, 0.18 - 0.08 * p));
    this.cam(st, pos, hw.clone().lerp(H, 0.12), lerp(36, 30, p), hw, 0.007);
    st.exposure = L.exp; this.roomSun(L, hw);
  }
  // ---------------------------------------------------------------- 6. pulls the blanket over the head, trembles
  shot_pull(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true;
    const u = easeInOutCubic(range(t, T.pull0 + 0.05, an(3, 3) + 0.05));
    this.placeGuy('sleep', t, {}); this.face({ blink: 0.6, worry: 1 });
    this.blanket.update({ hf: this.hfCover, edge: lerp(-0.36, -1.08, u), cover: u, tremble: smooth(range(t, an(3, 3), an(3, 3) + 0.3)), t });
    this.morningGiant(t, 1);
    const p = range(t, T.pull0, T.probe0);
    this.cam(st, V(lerp(0.05, -0.1, p), lerp(1.45, 1.35, p), lerp(1.25, 1.1, p)), V(-0.62, 0.72, 0.0), 44, V(-0.62, 0.72, 0.0), 0.004);
    st.exposure = L.exp; this.roomSun(L);
  }
  // ---------------------------------------------------------------- 7. the proboscis aims down through the blanket
  shot_probe(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true;
    this.placeGuy('sleep', t, {}); this.face({ blink: 1 });
    this.blanket.update({});
    const p = easeInOutCubic(range(t, T.probe0, T.pierce0 + 0.1));
    this.giantBite(0, 0, lerp(-0.45, 0.0, p));
    const hw = this.giant.head.getWorldPosition(V(0, 0, 0)), tip = this.tipW(this.giant);
    const side = V(Math.cos(this.biteSolve.yaw), 0, -Math.sin(this.biteSolve.yaw)), fwd = V(Math.sin(this.biteSolve.yaw), 0, Math.cos(this.biteSolve.yaw));
    const pos = hw.clone().addScaledVector(fwd, 0.25 - 0.05 * p).addScaledVector(side, -0.8 + 0.1 * p).add(V(0, 0.22 - 0.05 * p, 0));
    this.cam(st, pos, hw.clone().lerp(tip, 0.4), 44, hw.clone().lerp(tip, 0.3), 0.004);
    st.exposure = L.exp; this.roomSun(L, hw);
  }
  // ---------------------------------------------------------------- 8. cutaway: fascicle pierces fabric -> skin -> vessel
  shot_pierce(t, st) {
    const L = this.look('section');
    this.sec.group.visible = true;
    const S = this.sec, u = range(t, T.pierce0 - 0.15, T.bite + 0.25);
    const tipY = lerp(S.TOP - 1.2, SEC.VES_Y + 0.05, easeInOutCubic(u));
    const bow = smooth(range(t, T.pierce0 + 0.15, T.bite));
    S.set(tipY, bow * 0.8, smooth(range(t, T.bite + 0.1, T.balloon0 + 0.05)) * 0.75);
    const p = easeInOutCubic(range(t, T.pierce0 - 0.15, T.balloon0));
    const focus = V(S.X, lerp(2.0, -0.6, p), 0);
    this.cam(st, V(S.X + lerp(3.2, 2.0, p), lerp(3.2, 0.4, p), lerp(11.5, 9.0, p)), focus, 40, focus, 0.25);
    st.near = 0.05; st.far = 400;
    st.exposure = L.exp;
    this.sun(V(0, 0, -2), 12, 30, L.dir, -0.002, 0.02, 0.02);
  }
  // ---------------------------------------------------------------- 9–11. x-ray: blood drained through the "straw"
  xrayBase(t, drain, fill) {
    const L = this.look('xray');
    this.guy.group.visible = true; this.placeGuy('sleep', t, {}); this.guy.setXray(true);
    this.giantBite(fill, 0.85 * fill); this.giant.setXray(true, 0x7fd0ff, 0.45);
    this.ves.group.visible = true;
    const tip = this.tipW(this.giant), hw = this.giant.head.getWorldPosition(V(0, 0, 0));
    if (!this.straw) this.straw = new THREE.CatmullRomCurve3([tip.clone(), tip.clone().lerp(hw, 0.5), hw.clone()]);
    this.ves.setStream(this.straw);
    this.ves.update(t, drain, 1);
    return L;
  }
  shot_xray1(t, st) {
    const p = range(t, T.x1, T.xw);
    const L = this.xrayBase(t, 0.12 * p, 0.12 + 0.15 * p);
    const c = this.MACRO.clone().lerp(V(-0.2, 0.75, 0), 0.5);
    this.cam(st, c.clone().add(V(lerp(0.55, 0.45, p), lerp(1.5, 1.3, p), lerp(1.0, 0.85, p))), c, 46);
    st.exposure = L.exp;
  }
  shot_xray2(t, st) {
    const p = range(t, T.x2, T.x3);
    const L = this.xrayBase(t, 0.12 + 0.1 * p, 0.27 + 0.25 * p);
    const tip = this.tipW(this.giant), hw = this.giant.head.getWorldPosition(V(0, 0, 0));
    const mid = tip.clone().lerp(hw, 0.3);
    this.cam(st, mid.clone().add(V(lerp(0.2, 0.12, p), lerp(0.1, 0.16, p), lerp(-0.32, -0.22, p))), tip.clone().lerp(hw, 0.4), 38);
    st.exposure = L.exp;
  }
  // sentence 4 "sadece 5 litre kan var": whole body + full vessel tree, seen from the feet
  shot_xrayW(t, st) {
    const p = range(t, T.xw, T.x3);
    const L = this.xrayBase(t, 0.12, 0.27);
    const c = V(lerp(-0.05, 0.0, p), 0.62, 0.0);
    this.cam(st, V(lerp(0.15, 0.1, p), lerp(2.75, 2.55, p), lerp(1.75, 1.6, p)), c, 50);
    st.exposure = L.exp;
  }
  shot_xray3(t, st) {
    const p = range(t, T.x3, T.dry0);
    const L = this.xrayBase(t, lerp(0.15, 1.0, easeInOutCubic(range(t, T.x3 - 0.05, T.dry0 + 0.05))), lerp(0.3, 0.85, p));
    const c = V(0.05, 0.68, 0.05);
    this.cam(st, V(lerp(-1.55, -1.8, p), lerp(1.95, 2.3, p), lerp(0.55, 0.7, p)), c, 48);
    st.exposure = L.exp;
  }
  // ---------------------------------------------------------------- 12. you shrivel like a dry leaf
  shot_dry(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true;
    this.placeGuy('sleep', t, {}); this.blanket.update({});
    const d = easeInOutCubic(range(t, T.dry0 + 0.05, an(5, 5) + 0.3));
    this.face({ dry: d, blink: 1 - 0.7 * smooth(range(t, T.dry0 + 0.3, T.dry0 + 0.5)) + 0.5 * d, worry: 1, mouth: 0.1 + 0.15 * d });
    const H = this.headW(), p = range(t, T.dry0, T.door0);
    const c = H.clone().lerp(this.guy.bones.Spine2.getWorldPosition(V(0, 0, 0)), 0.35);
    this.cam(st, c.clone().add(V(lerp(0.32, 0.42, p), lerp(0.55, 0.62, p), lerp(0.38, 0.28, p))), c, 40, H, 0.004);
    st.roll = 0.05 * Math.sin(t * 2);
    st.exposure = L.exp; this.roomSun(L, H);
  }
  // ---------------------------------------------------------------- 13. its belly swells like a red balloon
  shot_balloon(t, st) {
    const L = this.look('morning');
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true;
    this.placeGuy('sleep', t, {}); this.blanket.update({}); this.face({ blink: 1 });
    const f = lerp(0.3, 1.0, easeOutCubic(range(t, T.balloon0, an(3, 8) + 0.25)));
    this.giantBite(f, 0, -0.25);
    this.giant.abdomen.scale.multiplyScalar(1 + 0.03 * Math.sin(t * 22) * (1 - range(t, an(3, 8) + 0.2, an(3, 8) + 0.6)));
    const G = this.giant; G.group.updateMatrixWorld(true);
    const ab = G.abdomen.localToWorld(V(0, 0, -1.3)), hw = G.head.getWorldPosition(V(0, 0, 0));
    const p = easeInOutCubic(range(t, T.balloon0, T.x1));
    const side = V(Math.cos(this.biteSolve.yaw), 0, -Math.sin(this.biteSolve.yaw));
    const pos = ab.clone().addScaledVector(side, -lerp(0.75, 1.2, p)).add(V(0.25, lerp(0.15, 0.35, p), 0.35));
    this.cam(st, pos, ab.clone().lerp(hw, 0.2), 42, ab, 0.006);
    st.exposure = L.exp; this.roomSun(L, ab);
  }
  // ---------------------------------------------------------------- 14–17. heads for the door, legs fail
  doorGiant(t, s) {
    const G = this.giant, D = this.room.door;
    const start = V(2.25, FLOOR_Y, 1.35), end = V(D.x, FLOOR_Y, D.z + 1.0);
    const pos = start.clone().lerp(end, s.u ?? 0);
    const yaw = Math.atan2(end.x - start.x, end.z - start.z);
    G.root.position.set(0, -(s.drop || 0) + 0.04 * Math.sin(t * 7) * (s.sway ?? 1), 0);
    G.root.rotation.set(0.06 * Math.sin(t * 5) * (s.sway ?? 1) + (s.pitch || 0), 0, 0.08 * Math.sin(t * 3.5) * (s.sway ?? 1) + (s.roll || 0));
    G.head.rotation.set(0.25 + (s.headDown || 0), 0, 0);
    G.setFill(s.fill ?? 0, 0); G.setWings(t, s.flap || 0, 0.05 + (s.wspread || 0), 0);
    G.setLegs({ drop: s.drop || 0, wob: s.wob || 0, kink: s.kink || 0, phase: t * (s.rate ?? 6), splay: s.splay || 0 });
    this.placeGiant(G, GIANT_S, pos, yaw);
    return { pos, yaw };
  }
  roomOnly(t) {
    this.room.group.visible = true; this.blanket.visible = true; this.guy.group.visible = true;
    this.placeGuy('awake', t, { up: 0.6, lookY: 0.3, roll: 0.02 }); this.blanket.update({}); this.face({ worry: 0.7 });
  }
  roomEmpty() { this.room.group.visible = true; this.blanket.visible = true; this.blanket.update({ hf: this.hfEmpty }); }
  shot_door(t, st) {
    const L = this.look('morning'); this.roomOnly(t);
    const p = range(t, T.door0, T.tr0);
    const { pos, yaw } = this.doorGiant(t, { u: 0.5 * p, wob: 0.05, rate: 8 });
    const back = V(-Math.sin(yaw), 0, -Math.cos(yaw)), D = this.room.door;
    const cp = pos.clone().addScaledVector(back, lerp(1.7, 1.35, p)).add(V(0.45, lerp(0.85, 0.65, p), 0));
    this.cam(st, cp, V(D.x - 0.05, 0.75, D.z), 50, pos.clone().add(V(0, 0.5, 0)), 0.008);
    st.exposure = L.exp; this.roomSun(L, V(1.8, 0.5, -0.5));
  }
  shot_legsA(t, st) {
    const L = this.look('morning'); this.roomOnly(t);
    const p = range(t, T.legsA, T.sc0);
    const { pos, yaw } = this.doorGiant(t, { u: 0.5 + 0.15 * p, wob: lerp(0.08, 0.28, p), rate: 7, drop: 0.15 * p });
    const fwd = V(Math.sin(yaw), 0, Math.cos(yaw)), side = V(Math.cos(yaw), 0, -Math.sin(yaw));
    const c = pos.clone().add(V(0, 0.2, 0));
    this.cam(st, c.clone().addScaledVector(fwd, lerp(0.75, 0.6, p)).addScaledVector(side, -lerp(1.75, 1.5, p)).add(V(0, lerp(0.02, 0.08, p), 0)), c.clone().add(V(0, -0.06, 0)), 46, c, 0.006);
    st.exposure = L.exp; this.roomSun(L, pos);
  }
  shot_legsB(t, st) {
    const L = this.look('morning'); this.roomOnly(t);
    const p = range(t, T.legsB, T.fall0), k = smooth(range(t, T.crack - 0.12, T.crack + 0.12));
    const kinks = [0, 1, 0, 1, 0, 0].map((x, i) => x * k + (i === 2 || i === 4 ? 0.6 * smooth(range(t, T.crack, T.crack + 0.25)) : 0));
    const { pos, yaw } = this.doorGiant(t, { u: 0.68, wob: lerp(0.3, 0.55, p) * (1 - 0.6 * k), rate: 5, drop: lerp(0.2, 0.75, easeInCubic(p)) + 0.25 * k, kink: kinks, splay: 0.3 * k, sway: 0.6 });
    const fwd = V(Math.sin(yaw), 0, Math.cos(yaw));
    const side = V(Math.cos(yaw), 0, -Math.sin(yaw));
    const c = pos.clone().addScaledVector(fwd, 0.2).add(V(0, 0.05, 0));
    this.cam(st, c.clone().addScaledVector(fwd, lerp(1.45, 1.25, p)).addScaledVector(side, lerp(-0.85, -0.7, p)).add(V(0, lerp(0.02, 0.08, p), 0)), c, 48, c, 0.006);
    st.roll = 0.04 * k * Math.sin(t * 40) * (1 - range(t, T.crack + 0.1, T.crack + 0.4));
    st.exposure = L.exp; this.roomSun(L, pos);
  }
  shot_fall(t, st) {
    const L = this.look('morning'); this.roomOnly(t);
    const p = range(t, T.fall0, T.fin0);
    // "nefessiz kalır": sagging + panting on broken legs, then collapses on "yığılır"
    const sag = smooth(range(t, T.fall0, T.thud - 0.3));
    const f = easeInCubic(range(t, T.thud - 0.32, T.thud));
    const bounce = 0.08 * Math.max(0, Math.sin(range(t, T.thud, T.thud + 0.35) * Math.PI));
    const pant = 0.05 * Math.sin(t * 16) * (1 - 0.6 * smooth(range(t, T.thud, T.thud + 0.4)));
    const { pos, yaw } = this.doorGiant(t, { u: 0.72, drop: lerp(lerp(0.95, 1.08, sag), 1.42, f) - bounce, wob: 0.15 * (1 - f), rate: 2, kink: [0.4, 1, 0.8, 1, 0.5, 0.3], splay: lerp(0.5, 0.8, f), sway: 0.4 * (1 - f), pitch: 0.06 * f, roll: 0.12 * f, headDown: 0.1 + 0.15 * f, flap: 0.25 * smooth(range(t, T.thud + 0.1, T.thud + 0.3)) });
    this.giant.abdomen.scale.multiplyScalar(1 + pant);
    const fwd = V(Math.sin(yaw), 0, Math.cos(yaw));
    const hw = this.giant.head.getWorldPosition(V(0, 0, 0));
    this.cam(st, hw.clone().addScaledVector(fwd, lerp(0.8, 0.65, p)).add(V(lerp(0.55, 0.45, p), lerp(0.12, 0.2, p), 0)), hw.clone().addScaledVector(fwd, -0.35), 46, hw, 0.007);
    st.roll = t > T.thud ? 0.03 * Math.sin(t * 50) * (1 - range(t, T.thud, T.thud + 0.25)) : 0;
    st.exposure = L.exp; this.roomSun(L, pos);
  }
  // ---------------------------------------------------------------- facts: no lungs, tracheae run out of oxygen
  factsBase(t, reach, pose = 0) {
    const L = this.look('xray');
    const F = this.facts; F.group.visible = true;
    F.root.position.set(0, 0, 0); F.root.rotation.set(0, 0, 0); F.head.rotation.set(0.2, 0, 0);
    this.placeGiant(F, GIANT_S, V(0, 0, 0), 0.15 * pose);
    F.o2(t, reach);
    return L;
  }
  shot_tr1(t, st) {   // 7 "akciğeri yok"
    const p = range(t, T.tr0, T.tr1);
    const L = this.factsBase(t, 2.0, p);
    this.cam(st, V(lerp(1.0, 0.7, p), lerp(1.9, 1.7, p), lerp(1.7, 1.5, p)), V(0, 0.45, -0.1), 44);
    st.exposure = L.exp;
  }
  shot_tr2(t, st) {   // 8 "oksijen vücudundaki": close on a spiracle, particles enter
    const p = range(t, T.tr1, T.tr1b);
    const L = this.factsBase(t, 2.0, 1);
    const F = this.facts; F.group.updateMatrixWorld(true);
    const sp = F.root.localToWorld(V(0.3, 0.12, -0.9));
    this.cam(st, sp.clone().add(V(lerp(0.55, 0.42, p), lerp(0.25, 0.2, p), lerp(0.1, 0.05, p))), sp.clone().add(V(-0.08, 0.0, 0)), 40);
    st.exposure = L.exp;
  }
  shot_tr1b(t, st) {  // 8 "ince borulardan kendiliğinden süzülür": top view, oxygen flowing through the whole tree
    const p = range(t, T.tr1b, T.tr2a);
    const L = this.factsBase(t, 2.0, 1);
    this.cam(st, V(lerp(-0.35, -0.2, p), lerp(2.3, 2.1, p), lerp(0.55, 0.65, p)), V(0, 0.4, -0.15), 40);
    st.exposure = L.exp;
  }
  shot_trBig(t, st) { // 9 "bu borular bu kadar": low side view, the body looks huge
    const p = range(t, T.tr2a, T.tr2);
    const L = this.factsBase(t, 2.0, 1);
    this.cam(st, V(lerp(-1.6, -1.4, p), lerp(1.45, 1.35, p), lerp(1.05, 1.2, p)), V(0.1, 0.3, -0.15), lerp(46, 42, p));
    st.exposure = L.exp;
  }
  shot_tr3(t, st) {   // 9 "büyük bir gövdeye oksijen yetiştiremez": particles die halfway, body turns red
    const p = range(t, T.tr2, T.legsA);
    const reach = lerp(2.0, 0.55, easeInOutCubic(range(t, T.o2out - 0.3, an(9, 9) + 0.3)));
    const L = this.factsBase(t, reach, 1);
    this.facts.setXray(true, new THREE.Color(0x6fc4ff).lerp(new THREE.Color(0xff5a6a), smooth(range(t, an(9, 9), an(9, 9) + 0.4))).getHex(), 0.8);
    this.cam(st, V(lerp(0.8, 1.1, p), lerp(1.2, 2.0, p), lerp(0.9, 1.6, p)), V(0, 0.45, -0.15), 44);
    st.exposure = L.exp;
  }
  // ---------------------------------------------------------------- 11. square–cube law
  studio() { this.env.ground.visible = true; }
  shot_sc1(t, st) {
    const L = this.look('studio'); this.studio();
    const p = range(t, T.sc0, T.sc1);
    this.guy.group.visible = true; this.placeGuyStanding(V(-0.75, 0, 0.1), 0.35, t, { look: 0.6, surprise: 0.6 * smooth(range(t, T.sc0 + 0.6, T.sc0 + 0.9)) }); this.face({ worry: 0.6 });
    const G = this.giant; G.root.position.set(0, 0, 0); G.root.rotation.set(0, 0, 0); G.root.scale.set(1, 1, 1); G.head.rotation.set(0.1, 0, 0); G.setWings(t, 0, 0.05); G.setFill(0, 0); G.setLegs(null);
    const S = lerp(0.006, GIANT_S, easeOutCubic(range(t, T.sc0 + 0.05, an(11, 4) + 0.15)));
    this.placeGiant(G, S, V(0.35, 0, 0), -Math.PI / 2 - 0.6);
    const c = V(-0.2, lerp(0.45, 0.85, p), 0);
    this.cam(st, c.clone().add(V(lerp(0.5, 0.9, p), lerp(0.1, 0.4, p), lerp(2.2, 3.6, p))), c, 42);
    st.exposure = L.exp; this.sun(V(0, 0.6, 0), 2.5, 8, L.dir, -0.0003, 0.008, 0.02);
  }
  shot_sc2(t, st) {
    const L = this.look('studio'); this.studio();
    const p = range(t, T.sc1, T.sc2);
    const G = this.giant; G.root.position.set(0, 0, 0); G.root.rotation.set(0, 0, 0); G.head.rotation.set(0.1, 0, 0); G.setWings(t, 0, 0.05); G.setFill(0, 0);
    const press = smooth(range(t, an(11, 6), an(11, 8) + 0.2));
    G.setLegs({ drop: 0.35 * press, wob: 0.12 * press, phase: 1, splay: 0.2 * press });
    G.root.position.y = -0.35 * press;
    this.placeGiant(G, GIANT_S, V(0, 0, 0), -Math.PI / 2 - 0.6);
    this.arrow.visible = true;
    const ay = lerp(2.4, 1.0, easeOutCubic(range(t, T.sc1, an(11, 6) + 0.1))) - 0.08 * press;
    const ascale = lerp(0.6, 1.5, smooth(range(t, an(11, 6), an(11, 8))));
    this.arrow.position.set(-0.05, ay, 0.0); this.arrow.scale.setScalar(ascale); this.arrow.rotation.set(0, t * 0.6, 0);
    const c = V(0, lerp(0.7, 0.55, p), 0);
    this.cam(st, c.clone().add(V(lerp(1.1, 1.3, p), lerp(0.15, 0.05, p), lerp(1.9, 1.6, p))), c.clone().add(V(0, 0.15, 0)), 46);
    st.exposure = L.exp; this.sun(V(0, 0.6, 0), 2.5, 8, L.dir, -0.0003, 0.008, 0.02);
  }
  shot_sc3(t, st) {
    const L = this.look('studio');
    const p = range(t, T.sc2, T.legsB);
    const LS = this.legSec; LS.group.visible = true;
    LS.group.position.set(0, 50, 0); LS.group.rotation.set(0.35, 0, -0.25); LS.group.updateMatrixWorld(true);
    LS.u.uCrack.value = easeInOutCubic(range(t, an(11, 11), an(11, 13) + 0.35));
    const capW = LS.group.localToWorld(V(0, 3, 0));
    const pos = capW.clone().add(V(lerp(1.6, 1.25, p), lerp(1.5, 1.1, p), lerp(2.2, 2.0, p)));
    this.cam(st, pos, capW.clone().add(V(0, -1.2 * p, 0)), 40, capW.clone().add(V(0, -0.6, 0)), 0.03);
    st.exposure = L.exp; this.sun(capW.clone().add(V(0, -2, 0)), 5, 15, L.dir, -0.0005, 0.01, 0.02);
  }
  // ---------------------------------------------------------------- 12 end: it lies on the floor; you look down at it with pity
  lyingGiant(t) {
    const pant = 0.035 * Math.sin(t * 9) * (1 - smooth(range(t, T.fin0, DURATION - 0.6)) * 0.7);
    const r = this.doorGiant(t, { u: 0.72, drop: 1.42, wob: 0.0, kink: [0.4, 1, 0.8, 1, 0.5, 0.3], splay: 0.8, sway: 0, pitch: 0.06, roll: 0.12, headDown: 0.25, rate: 0 });
    this.giant.abdomen.scale.multiplyScalar(1 + pant);
    return r;
  }
  standGuy(t, bow) {
    const PIT = GUY_STAND.clone();
    this.guy.group.visible = true;
    this.placeGuyStanding(PIT, GUY_STAND_YAW, t, { bow, look: -0.15, tilt: 0.12 });
    return PIT;
  }
  shot_fin1(t, st) {
    const L = this.look('morning'); this.roomEmpty();
    const { pos } = this.lyingGiant(t);
    const bow = smooth(range(t, T.fin0 + 0.1, T.fin1));
    this.standGuy(t, 0.35 + 0.65 * bow); this.face({ worry: 0.6 + 0.4 * bow, mouth: 0.05 });
    const p = easeInOutCubic(range(t, T.fin0, T.fin1 + 0.1));
    const c = pos.clone().lerp(GUY_STAND, 0.55).add(V(0, 0.95, 0));
    this.cam(st, c.clone().add(V(lerp(-2.3, -2.0, p), lerp(0.25, 0.2, p), lerp(1.9, 1.7, p))), c, 46, c, 0.006);
    st.exposure = L.exp; this.roomSun(L, c);
  }
  shot_fin2(t, st) {
    const L = this.look('morning'); this.roomEmpty();
    this.lyingGiant(t);
    this.standGuy(t, 1); this.face({ worry: 1, mouth: 0.04, blink: 0.25 + 0.1 * smooth(range(t, an(12, 17), an(12, 17) + 0.3)) });
    const H = this.headW(), p = range(t, T.fin1, DURATION);
    const G = this.giant.head.getWorldPosition(V(0, 0, 0));
    // low, from just beside the lying mosquito's head, looking up at his sad face
    const pos = G.clone().lerp(H, 0.38).add(V(lerp(-0.1, -0.05, p), lerp(0.0, 0.05, p), lerp(0.55, 0.45, p)));
    this.cam(st, pos, H.clone().add(V(0, -0.05, 0)), lerp(36, 32, p), H, 0.004);
    st.exposure = L.exp; this.roomSun(L, H);
  }
}
