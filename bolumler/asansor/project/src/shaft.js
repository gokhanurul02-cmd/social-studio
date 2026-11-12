// Half-cut building with an elevator shaft (front cut plane z = +1.0, viewer at +z):
// concrete shaft + floor slabs with cut faces and painted floor numbers, two T-profile car guide rails (+ counterweight
// rails), car with sling frame (stiles, crosshead, plank), car-top balustrade, rope hitch with springs, progressive
// safety gears (wedges) at the bottom of the stiles, counterweight with filler blocks, 6 steel wire ropes over a grooved
// traction sheave in the machine room, overspeed governor with its own rope down to the car's safety linkage, pit buffers.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { concrete, paintedSteel, galvanised, machinedSteel, brushedSteel, ropeMaterial, Tube, proc, canvasTex, rubber, blackGloss } from './mats.js';
import { clamp } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const FH = 3.2, NF = 21;
export const floorY = i => (i - 1) * FH;
export const YM = floorY(NF) + FH;                 // machine room slab top
export const SHEAVE = { y: YM + 0.95, z: -0.56, R: 0.56 };
export const ROPE_X = [-0.1, -0.06, -0.02, 0.02, 0.06, 0.1];
export const CAR = { W: 1.6, D: 1.4, H: 2.5, top: 2.95 };   // top = crosshead hitch height above car floor
export const RAIL_X = 1.03;                        // blade centre line
export const CW = { z: -1.12, H: 2.4 };
export const GOV = { x: -0.86, z: 0.5, R: 0.17 };

function mesh(geo, mat, parent, { cast = true, recv = true } = {}) { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; m.receiveShadow = recv; parent.add(m); return m; }
function boxAt(w, h, d, x, y, z) { const g = new THREE.BoxGeometry(w, h, d); g.translate(x, y, z); return g; }
const merge = gs => mergeGeometries(gs.map(g => { const n = g.index ? g.toNonIndexed() : g; for (const k of Object.keys(n.attributes)) if (!['position', 'normal', 'uv'].includes(k)) n.deleteAttribute(k); if (!n.attributes.uv) n.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(n.attributes.position.count * 2), 2)); return n; }), false);

// C-channel along Y (web in the x-z plane facing `dir`)
function channel(len, w = 0.1, d = 0.05, t = 0.007) {
  return merge([boxAt(w, len, t, 0, len / 2, -d / 2 + t / 2), boxAt(t, len, d, -w / 2 + t / 2, len / 2, 0), boxAt(t, len, d, w / 2 - t / 2, len / 2, 0)]);
}
function helixSpring(r, len, turns, wire) {
  const pts = []; for (let i = 0; i <= turns * 24; i++) { const a = i / 24 * Math.PI * 2; pts.push(V(Math.cos(a) * r, i / (turns * 24) * len, Math.sin(a) * r)); }
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), turns * 24, wire, 8, false);
}
function floorNumberTex(n) {
  return canvasTex(256, 256, (g, w, h) => {
    g.clearRect(0, 0, w, h); g.font = 'bold 170px Verdana'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillStyle = 'rgba(250,250,245,0.92)'; g.fillText(String(n), w / 2, h / 2 + 8);
  });
}

export function buildShaft() {
  const group = new THREE.Group(); group.name = 'shaft';
  const conc = concrete(0xa29d93, { key: 'conc-shaft' });
  const concCut = concrete(0xd8d2c6, { key: 'conc-cut', cut: true });
  const slabMat = concrete(0xb7b1a6, { key: 'conc-slab', scale: 1 });
  const top = YM + 2.6, bot = -1.6;
  // shaft walls (back, left, right) with cut faces at z = +1.0
  const Wx = 1.45, Wz = -1.45, T = 0.25, Z1 = 1.0;
  mesh(boxAt(2 * Wx + 2 * T, top - bot, T, 0, (top + bot) / 2, Wz - T / 2), conc, group);
  for (const s of [-1, 1]) {
    mesh(boxAt(T, top - bot, Z1 - Wz + T, s * (Wx + T / 2), (top + bot) / 2, (Z1 + Wz - T) / 2), conc, group);
    mesh(boxAt(T + 0.002, top - bot, 0.004, s * (Wx + T / 2), (top + bot) / 2, Z1 + 0.002), concCut, group, { cast: false });
  }
  // pit floor
  mesh(boxAt(2 * Wx + 2 * T, 0.4, Z1 - Wz + T, 0, bot - 0.2, (Z1 + Wz - T) / 2), conc, group);
  // floor slabs outside the shaft (cut), corridor walls, landing sills on the cut line, painted floor numbers + shaft lights
  const slabs = [], cuts = [];
  const numMats = [];
  const lampMat = new THREE.MeshStandardMaterial({ color: 0x222222, emissive: 0xfff0d8, emissiveIntensity: 4 });
  const lampG = [];
  for (let i = 1; i <= NF + 1; i++) {
    const y = floorY(i);
    for (const s of [-1, 1]) {
      slabs.push(boxAt(3.2, 0.26, 3.4, s * (Wx + T + 1.6), y - 0.13, -0.7));
      cuts.push(boxAt(3.2, 0.262, 0.004, s * (Wx + T + 1.6), y - 0.13, Z1 + 0.002));
      // corridor back wall + a door frame hint
      slabs.push(boxAt(3.2, FH - 0.26, 0.15, s * (Wx + T + 1.6), y + (FH - 0.26) / 2, -2.35));
    }
    if (i <= NF) {
      // floor number on the back wall, left and right of the counterweight
      if (!numMats[i]) numMats[i] = new THREE.MeshStandardMaterial({ map: floorNumberTex(i), transparent: true, roughness: 0.9, depthWrite: false });
      for (const x of [-1.08, 1.08]) { const p = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.62), numMats[i]); p.position.set(x, y + 1.55, Wz + 0.003); p.renderOrder = 2; group.add(p); }
      if (i % 2 === 0) lampG.push(boxAt(0.22, 0.06, 0.05, -1.08, y + 2.55, Wz + 0.03), boxAt(0.22, 0.06, 0.05, 1.08, y + 2.55, Wz + 0.03));
      // landing door sill + header cut in half on the front line (stainless)
      cuts.push(boxAt(1.1, 0.04, 0.12, 0, y - 0.02, Z1 + 0.05));
    }
  }
  mesh(merge(slabs), slabMat, group);
  mesh(merge(cuts), concCut, group, { cast: false });
  const lamps = mesh(merge(lampG), lampMat, group, { cast: false });
  // machine room slab with rope holes (just a slab with a slot), machine room walls (cut)
  const slabW = 2 * Wx + 2 * T, zs = [[Wz - T, -1.19], [-1.05, -0.05], [0.05, Z1]];
  mesh(merge(zs.map(([a, b]) => boxAt(slabW, 0.3, b - a, 0, YM - 0.15, (a + b) / 2))), slabMat, group);
  mesh(boxAt(2 * Wx + 2 * T + 0.004, 0.302, 0.004, 0, YM - 0.15, Z1 + 0.002), concCut, group, { cast: false });

  // ---------------------------------------------------------------- guide rails (T89) + brackets
  const bladeMat = machinedSteel(0xc4c7cb, 0.2);
  const railU = { uY0: { value: -100 }, uY1: { value: -100 }, uK: { value: 0 } };
  proc(bladeMat, 'blade-glow', {
    uniforms: railU,
    pars: 'uniform float uY0, uY1, uK;',
    color: `{ float n = vnoise3(vO * vec3(4.0, 260.0, 4.0)); diffuseColor.rgb *= 0.9 + 0.14 * n; _H = n * 0.00003;
      float sc = step(uY0, vO.y) * step(vO.y, uY1) * uK; float streak = smoothstep(0.25, 0.75, vnoise3(vec3((vO.x + vO.z) * 260.0, vO.y * 1.5, 1.0)));
      float age = clamp((vO.y - uY0) / max(uY1 - uY0, 0.001), 0.0, 1.0);
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.25, 0.22, 0.2), sc * streak * 0.6); _scr = sc * streak * (1.0 - age); }`,
  });
  bladeMat.onBeforeCompile = (orig => sh => { orig(sh); sh.fragmentShader = sh.fragmentShader.replace('float _H = 0.0;', 'float _H = 0.0; float _scr = 0.0;')
    .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(4.0, 1.1, 0.25) * _scr * _scr * 3.0;'); })(bladeMat.onBeforeCompile);
  bladeMat.customProgramCacheKey = () => 'blade-glow2';
  const flangeMat = paintedSteel(0x2a2c2e, { rough: 0.55, wear: 0.4, key: 'flange' });
  const bracketMat = galvanised();
  const rails = new THREE.Group(); group.add(rails);
  const RL = top - bot;
  for (const s of [-1, 1]) {
    // blade: 62 mm deep (x), 16 mm thick (z); flange 89 mm wide (z), 10 mm (x)
    mesh(boxAt(0.062, RL, 0.016, s * (RAIL_X), (top + bot) / 2, 0), bladeMat, rails);
    mesh(boxAt(0.01, RL, 0.089, s * (RAIL_X + 0.036), (top + bot) / 2, 0), flangeMat, rails);
    // counterweight rails (smaller) at z = CW.z, blades along x
    mesh(boxAt(0.045, RL, 0.01, s * 0.7, (top + bot) / 2, CW.z), bladeMat, rails);
    mesh(boxAt(0.008, RL, 0.06, s * 0.726, (top + bot) / 2, CW.z), flangeMat, rails);
    const br = [];
    for (let y = bot + 1.2; y < top - 1; y += 2.4) {
      br.push(boxAt(Wx - RAIL_X - 0.04, 0.12, 0.01, s * ((Wx + RAIL_X + 0.04) / 2), y, 0.06), boxAt(Wx - RAIL_X - 0.04, 0.12, 0.01, s * ((Wx + RAIL_X + 0.04) / 2), y, -0.06));
      br.push(boxAt(0.012, 0.12, 0.13, s * (RAIL_X + 0.047), y, 0));
      br.push(boxAt(0.01, 0.12, 0.24, s * (Wx - 0.005), y, 0));
      br.push(boxAt(Wx - 0.75, 0.1, 0.01, s * ((Wx + 0.75) / 2), y + 0.6, CW.z));
    }
    mesh(merge(br), bracketMat, rails);
  }

  // ---------------------------------------------------------------- car (sling + cabin body)
  const car = new THREE.Group(); car.name = 'car'; group.add(car);
  const carPaint = paintedSteel(0x8e969e, { rough: 0.42, wear: 0.15, key: 'carpaint' });
  const frameMat = paintedSteel(0x1d3b5c, { rough: 0.45, wear: 0.35, key: 'frame' });
  const yellow = paintedSteel(0xf2b705, { rough: 0.38, wear: 0.3, key: 'yellow' });
  const dark = paintedSteel(0x25272a, { rough: 0.5, wear: 0.3, key: 'dark' });
  const hw = CAR.W / 2, hd = CAR.D / 2;
  // body panels with vertical stiffener ribs
  const body = [boxAt(CAR.W, CAR.H, 0.02, 0, CAR.H / 2, -hd + 0.01), boxAt(0.02, CAR.H, CAR.D, -hw + 0.01, CAR.H / 2, 0), boxAt(0.02, CAR.H, CAR.D, hw - 0.01, CAR.H / 2, 0),
    boxAt(CAR.W, 0.04, CAR.D, 0, CAR.H + 0.02, 0), boxAt(CAR.W + 0.04, 0.12, CAR.D + 0.04, 0, 0.0, 0)];
  for (let i = 1; i < 6; i++) { const z = -hd + i * CAR.D / 6; body.push(boxAt(0.035, CAR.H - 0.1, 0.03, -hw - 0.017, CAR.H / 2, z), boxAt(0.035, CAR.H - 0.1, 0.03, hw + 0.017, CAR.H / 2, z)); }
  for (let i = 1; i < 7; i++) { const x = -hw + i * CAR.W / 7; body.push(boxAt(0.03, CAR.H - 0.1, 0.035, x, CAR.H / 2, -hd - 0.017)); }
  mesh(merge(body), carPaint, car);
  // front: car doors (brushed) + door operator header, light gap between doors
  const doorSteel = new THREE.MeshPhysicalMaterial({ color: 0x7d8288, metalness: 0.75, roughness: 0.48, envMapIntensity: 0.5 });
  for (const s of [-1, 1]) mesh(boxAt(0.45, 2.1, 0.025, s * 0.228, 1.05 + 0.06, hd + 0.02), doorSteel, car);
  mesh(merge([boxAt(0.35, 2.1, 0.02, -0.62, 1.11, hd), boxAt(0.35, 2.1, 0.02, 0.62, 1.11, hd), boxAt(CAR.W, CAR.H - 2.16, 0.02, 0, 2.16 + (CAR.H - 2.16) / 2, hd)]), carPaint, car);
  mesh(boxAt(1.3, 0.22, 0.16, 0, CAR.H + 0.13, hd - 0.05), dark, car);
  mesh(boxAt(1.32, 0.012, 0.03, 0, CAR.H + 0.02, hd + 0.06), machinedSteel(), car);
  // stiles + crosshead + plank
  for (const s of [-1, 1]) { const st = mesh(channel(CAR.top + 0.72, 0.1, 0.06), frameMat, car); st.position.set(s * (hw + 0.1), -0.52, 0); st.rotation.y = s > 0 ? Math.PI / 2 : -Math.PI / 2; }
  mesh(merge([boxAt(CAR.W + 0.32, 0.16, 0.06, 0, CAR.top - 0.08, 0.06), boxAt(CAR.W + 0.32, 0.16, 0.06, 0, CAR.top - 0.08, -0.06)]), frameMat, car);
  mesh(merge([boxAt(CAR.W + 0.32, 0.18, 0.07, 0, -0.2, 0.08), boxAt(CAR.W + 0.32, 0.18, 0.07, 0, -0.2, -0.08)]), frameMat, car);
  // guide shoes (top and bottom) hugging the blades
  const shoes = [];
  for (const s of [-1, 1]) for (const y of [-0.22, CAR.top - 0.1]) shoes.push(boxAt(0.1, 0.12, 0.012, s * (RAIL_X - 0.02), y, 0.017), boxAt(0.1, 0.12, 0.012, s * (RAIL_X - 0.02), y, -0.017), boxAt(0.02, 0.12, 0.05, s * (RAIL_X - 0.075), y, 0));
  mesh(merge(shoes), dark, car);
  // car-top balustrade (yellow) + toe boards
  const bal = [];
  for (const [x, z] of [[-hw + 0.04, -hd + 0.04], [hw - 0.04, -hd + 0.04], [-hw + 0.04, hd - 0.25], [hw - 0.04, hd - 0.25], [0, -hd + 0.04]]) bal.push(boxAt(0.035, 1.1, 0.035, x, CAR.H + 0.55, z));
  bal.push(boxAt(CAR.W - 0.06, 0.035, 0.035, 0, CAR.H + 1.08, -hd + 0.04), boxAt(CAR.W - 0.06, 0.035, 0.035, 0, CAR.H + 0.6, -hd + 0.04));
  for (const s of [-1, 1]) bal.push(boxAt(0.035, 0.035, CAR.D - 0.3, s * (hw - 0.04), CAR.H + 1.08, -0.1), boxAt(0.035, 0.035, CAR.D - 0.3, s * (hw - 0.04), CAR.H + 0.6, -0.1));
  mesh(merge(bal), yellow, car);
  // rope hitch: plate on crosshead, 6 threaded rods + compression springs + nuts
  const hitchMat = galvanised(0xb8bcc0);
  const hitch = [boxAt(0.36, 0.03, 0.16, 0, CAR.top + 0.015, 0)];
  const springs = [];
  for (const x of ROPE_X) {
    hitch.push(new THREE.CylinderGeometry(0.008, 0.008, 0.42, 10).translate(x, CAR.top + 0.18, 0));
    springs.push(helixSpring(0.016, 0.16, 7, 0.0035).translate(x, CAR.top - 0.17, 0));
    hitch.push(new THREE.CylinderGeometry(0.014, 0.014, 0.018, 6).translate(x, CAR.top - 0.19, 0));
    hitch.push(new THREE.CylinderGeometry(0.011, 0.007, 0.13, 12).translate(x, CAR.top + 0.43, 0));   // rope socket
  }
  mesh(merge(hitch), hitchMat, car);
  mesh(merge(springs), paintedSteel(0xc0392b, { rough: 0.4, wear: 0.2, key: 'spring' }), car);
  // safety linkage: lever on the crosshead + lift rods down the stiles
  const link = [boxAt(0.6, 0.03, 0.03, -hw + 0.1, CAR.top + 0.05, 0.12)];
  for (const s of [-1, 1]) link.push(new THREE.CylinderGeometry(0.008, 0.008, CAR.top + 0.42, 10).translate(s * (hw + 0.17), (CAR.top - 0.36) / 2 - 0.05, 0.09), boxAt(0.012, 0.012, 0.05, s * (hw + 0.17), -0.36, 0.065));
  link.push(boxAt(CAR.W + 0.36, 0.02, 0.02, 0, -0.1, 0.11));
  mesh(merge(link), yellow, car);

  // progressive safety gears at the bottom of the stiles: open housing, two serrated wedges either side of the blade
  const gearMat = paintedSteel(0x3c3f44, { rough: 0.5, wear: 0.3, key: 'gear' });
  const wedgeMat = machinedSteel(0x6f7378, 0.4);
  proc(wedgeMat, 'wedge', { color: '{ float k = step(0.5, fract(vO.y * 260.0)); diffuseColor.rgb *= 0.65 + 0.35 * k; _H = k * 0.0003; }', rough: 'roughnessFactor = 0.35;' });
  const gears = [];
  for (const s of [-1, 1]) {
    const G = new THREE.Group(); G.position.set(s * RAIL_X, -0.42, 0); car.add(G);
    // housing: back plate (toward car), top/bottom caps, side cheeks (z) with a window
    const hs = [boxAt(0.04, 0.26, 0.15, -s * 0.07, 0, 0), boxAt(0.12, 0.03, 0.15, -s * 0.02, 0.13, 0)];   // open bottom: wedges + blade visible from below
    for (const z of [-0.065, 0.065]) { hs.push(boxAt(0.12, 0.05, 0.02, -s * 0.02, 0.105, z), boxAt(0.12, 0.05, 0.02, -s * 0.02, -0.105, z), boxAt(0.03, 0.26, 0.02, s * 0.025, 0, z)); }
    mesh(merge(hs), gearMat, G);
    // bolts
    const bolts = []; for (const y of [-0.1, 0.1]) for (const z of [-0.05, 0.05]) bolts.push(new THREE.CylinderGeometry(0.009, 0.009, 0.012, 6).rotateZ(Math.PI / 2).translate(-s * 0.096, y, z));
    mesh(merge(bolts), machinedSteel(0xa0a4a8, 0.3), G);
    // mounting cheeks bolted to the stile (the gear hangs from the car frame)
    const mc = []; for (const z of [-0.082, 0.082]) mc.push(boxAt(0.16, 0.34, 0.012, -s * 0.11, 0.06, z));
    mesh(merge(mc), frameMat, G);
    const mb = []; for (const z of [-0.09, 0.09]) for (const [x, y] of [[-0.06, 0.18], [-0.16, 0.18], [-0.06, -0.04], [-0.16, -0.04]]) mb.push(new THREE.CylinderGeometry(0.008, 0.008, 0.01, 6).rotateX(Math.PI / 2).translate(s * x, y, z));
    mesh(merge(mb), machinedSteel(0xa0a4a8, 0.3), G);
    const W = [];
    for (const z of [-1, 1]) {
      const wg = new THREE.Group(); G.add(wg);
      // tapered wedge: thicker at the bottom
      const sh = new THREE.Shape(); sh.moveTo(0, -0.07); sh.lineTo(0.022, -0.07); sh.lineTo(0.012, 0.07); sh.lineTo(0, 0.07); sh.closePath();
      const eg = new THREE.ExtrudeGeometry(sh, { depth: 0.07, bevelEnabled: true, bevelThickness: 0.002, bevelSize: 0.002, bevelSegments: 2 });
      eg.translate(0, 0, -0.035); eg.rotateY(Math.PI / 2);   // thickness along +z now along... x
      const m = mesh(eg, wedgeMat, wg); m.rotation.y = z > 0 ? 0 : Math.PI; m.position.set(0, 0, 0);
      W.push({ g: wg, z });
    }
    gears.push({ G, W, s });
  }
  function setGear(k) {   // 0 open .. 1 clamped (wedges pulled up and onto the blade)
    for (const { W } of gears) for (const w of W) { w.g.position.set(0, -0.02 + 0.05 * k, w.z * (0.0425 - 0.0335 * k)); }
  }
  setGear(0);

  // ---------------------------------------------------------------- counterweight
  const cw = new THREE.Group(); cw.name = 'cw'; group.add(cw);
  const cwFrame = paintedSteel(0x1d3b5c, { rough: 0.45, wear: 0.35, key: 'frame' });
  mesh(merge([boxAt(0.08, CW.H, 0.12, -0.62, CW.H / 2, 0), boxAt(0.08, CW.H, 0.12, 0.62, CW.H / 2, 0), boxAt(1.32, 0.14, 0.14, 0, CW.H - 0.07, 0), boxAt(1.32, 0.14, 0.14, 0, 0.07, 0)]), cwFrame, cw);
  const fill = []; const fg = new RoundedBoxGeometry(1.14, 0.075, 0.1, 2, 0.008);
  for (let i = 0; i < 26; i++) fill.push(fg.clone().translate(0, 0.18 + i * 0.079, 0));
  mesh(merge(fill), paintedSteel(0x2f3133, { rough: 0.7, wear: 0.5, key: 'fill' }), cw);
  const cwh = []; for (const x of ROPE_X) { cwh.push(new THREE.CylinderGeometry(0.008, 0.008, 0.3, 10).translate(x, CW.H + 0.15, 0)); cwh.push(helixSpring(0.015, 0.14, 6, 0.0032).translate(x, CW.H - 0.02, 0)); }
  mesh(merge(cwh), hitchMat, cw);
  cw.position.set(0, 0, CW.z);

  // ---------------------------------------------------------------- machine room: grooved traction sheave, motor, brake, bedplate
  const mr = new THREE.Group(); mr.name = 'machine'; group.add(mr);
  const shProf = []; const R = SHEAVE.R, half = 0.17;
  shProf.push(new THREE.Vector2(0.05, -half));
  shProf.push(new THREE.Vector2(R + 0.03, -half));
  for (let i = 0; i < 6; i++) {
    const x0 = -0.1 + i * 0.04;
    shProf.push(new THREE.Vector2(R + 0.012, x0 - 0.012), new THREE.Vector2(R - 0.004, x0 - 0.004), new THREE.Vector2(R - 0.008, x0), new THREE.Vector2(R - 0.004, x0 + 0.004), new THREE.Vector2(R + 0.012, x0 + 0.012));
  }
  shProf.push(new THREE.Vector2(R + 0.03, half), new THREE.Vector2(0.05, half));
  const shG = new THREE.LatheGeometry(shProf.map(p => new THREE.Vector2(p.x, p.y)), 128); shG.rotateZ(Math.PI / 2);   // axis along x
  const sheave = new THREE.Group(); sheave.position.set(0, SHEAVE.y, SHEAVE.z); mr.add(sheave);
  const shMat = machinedSteel(0x8e9399, 0.28); shMat.side = THREE.DoubleSide; mesh(shG, shMat, sheave);
  // spokes/web so the rotation reads
  const web = []; for (let i = 0; i < 6; i++) { const b = boxAt(0.03, R * 0.85, 0.06, 0, R * 0.45, 0); b.rotateX(i * Math.PI / 3); web.push(b); }
  web.push(new THREE.CylinderGeometry(0.11, 0.11, 0.4, 32).rotateZ(Math.PI / 2));
  mesh(merge(web), paintedSteel(0x2b5f8a, { rough: 0.4, wear: 0.2, key: 'sheaveweb' }), sheave);
  // motor + brake + bedplate
  const mPaint = paintedSteel(0x2b5f8a, { rough: 0.38, wear: 0.15, key: 'motor' });
  mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.7, 64).rotateZ(Math.PI / 2).translate(0.62, SHEAVE.y, SHEAVE.z), mPaint, mr);
  const fins = []; for (let i = 0; i < 14; i++) fins.push(new THREE.CylinderGeometry(0.445, 0.445, 0.015, 64).rotateZ(Math.PI / 2).translate(0.32 + i * 0.045, SHEAVE.y, SHEAVE.z));
  mesh(merge(fins), mPaint, mr);
  mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.12, 48).rotateZ(Math.PI / 2).translate(-0.3, SHEAVE.y, SHEAVE.z), machinedSteel(0xa6aaae, 0.35), mr);
  mesh(merge([boxAt(0.1, 0.5, 0.08, -0.3, SHEAVE.y - 0.1, SHEAVE.z + 0.33), boxAt(0.1, 0.5, 0.08, -0.3, SHEAVE.y - 0.1, SHEAVE.z - 0.33)]), yellow, mr);
  mesh(boxAt(1.9, 0.12, 1.0, 0.2, YM + 0.06, SHEAVE.z), dark, mr);
  mesh(merge([boxAt(0.12, SHEAVE.y - YM - 0.1, 0.5, -0.24, (SHEAVE.y + YM) / 2, SHEAVE.z), boxAt(0.12, SHEAVE.y - YM - 0.1, 0.5, 0.24, (SHEAVE.y + YM) / 2, SHEAVE.z)]), dark, mr);

  // ---------------------------------------------------------------- overspeed governor (machine room, left front)
  const gov = new THREE.Group(); gov.name = 'governor'; gov.position.set(GOV.x + GOV.R, YM + 0.62, GOV.z); mr.add(gov);
  const govRot = new THREE.Group(); gov.add(govRot);
  const gp = [new THREE.Vector2(0.03, -0.03), new THREE.Vector2(GOV.R + 0.02, -0.03), new THREE.Vector2(GOV.R + 0.02, -0.012), new THREE.Vector2(GOV.R - 0.008, 0), new THREE.Vector2(GOV.R + 0.02, 0.012), new THREE.Vector2(GOV.R + 0.02, 0.03), new THREE.Vector2(0.03, 0.03)];
  const gG = new THREE.LatheGeometry(gp, 96); gG.rotateX(Math.PI / 2);   // axis along z
  const gMat = machinedSteel(0xaeb2b6, 0.24); gMat.side = THREE.DoubleSide; mesh(gG, gMat, govRot);
  // ratchet teeth rim on the face + flyweights
  const teeth = []; for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; const b = boxAt(0.02, 0.012, 0.012, 0, 0, 0); b.rotateZ(a + 0.4); b.translate(Math.cos(a) * (GOV.R - 0.035), Math.sin(a) * (GOV.R - 0.035), 0.036); teeth.push(b); }
  mesh(merge(teeth), machinedSteel(0x8f9398, 0.3), govRot);
  mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.09, 24).rotateX(Math.PI / 2), paintedSteel(0xd12b1f, { rough: 0.35, wear: 0.1, key: 'govhub' }), govRot);
  const fly = [];
  for (let i = 0; i < 2; i++) {
    const piv = new THREE.Group(); piv.rotation.z = i * Math.PI; govRot.add(piv);
    const arm = new THREE.Group(); arm.position.set(0.035, 0.0, 0.05); piv.add(arm);
    const sh = new THREE.Shape(); sh.absarc(0, 0, 0.1, -0.25, 1.35, false); sh.absarc(0, 0, 0.075, 1.35, -0.25, true);
    const eg = new THREE.ExtrudeGeometry(sh, { depth: 0.018, bevelEnabled: true, bevelThickness: 0.003, bevelSize: 0.003, bevelSegments: 2 });
    mesh(eg, paintedSteel(0xd12b1f, { rough: 0.35, wear: 0.15, key: 'govhub' }), arm);
    mesh(new THREE.SphereGeometry(0.022, 20, 14).translate(0.087 * Math.cos(1.25), 0.087 * Math.sin(1.25), 0.01), machinedSteel(0x9fa3a8, 0.25), arm);
    fly.push(arm);
  }
  // stand + trip switch + rope jaw
  mesh(merge([boxAt(0.06, 0.62, 0.04, 0, -0.31, -0.07), boxAt(0.3, 0.05, 0.2, 0, -0.6, -0.04)]), paintedSteel(0x34383d, { rough: 0.5, wear: 0.3, key: 'govstand' }), gov);
  mesh(boxAt(0.07, 0.09, 0.05, 0.2, 0.12, -0.03), yellow, gov);
  const jaw = mesh(boxAt(0.06, 0.05, 0.05, -GOV.R - 0.045, -0.12, 0), dark, gov);
  function setGovernor(angle, open, trip) {
    govRot.rotation.z = -angle;
    fly.forEach(a => { a.rotation.z = 0.45 * open; });
    jaw.position.x = -GOV.R - 0.045 + 0.03 * trip;
  }

  // ---------------------------------------------------------------- pit buffers
  const buf = [];
  for (const [x, z] of [[-0.4, 0], [0.4, 0], [0, CW.z]]) { buf.push(new THREE.CylinderGeometry(0.09, 0.11, 0.25, 24).translate(x, bot + 0.12, z)); buf.push(new THREE.CylinderGeometry(0.05, 0.05, 0.5, 20).translate(x, bot + 0.5, z)); }
  mesh(merge(buf), yellow, group);

  // ---------------------------------------------------------------- ropes (6 hoist ropes + governor rope), reshaped every frame
  const rmat = ropeMaterial();
  const ropes = ROPE_X.map(() => { const t = new Tube(64, 12, 0.0065); const m = mesh(t.geo, rmat, group); m.frustumCulled = false; return { t, m }; });
  const stubs = ROPE_X.map(() => { const t = new Tube(24, 12, 0.0065); const m = mesh(t.geo, rmat, group); m.frustumCulled = false; m.visible = false; return { t, m }; });
  const govRope = new Tube(40, 8, 0.0045); const govRopeM = mesh(govRope.geo, ropeMaterial({ key: 'govrope', lay: 0.06 }), group); govRopeM.frustumCulled = false;

  // state: carY (car floor), cwY (counterweight bottom), sheave angle; opts.broken[i] = {y: break height, up: recoil, flail}
  function update(st) {
    const { carY, cwY, broken = [], t = 0 } = st;
    car.position.y = carY; cw.position.y = cwY;
    sheave.rotation.x = st.sheaveA ?? (-(carY) / SHEAVE.R);
    ROPE_X.forEach((x, i) => {
      const b = broken[i], hY = carY + CAR.top + 0.5;
      const pts = [];
      const top0 = V(x, SHEAVE.y, 0), cwTop = V(x, cwY + CW.H + 0.3, CW.z);
      if (!b) {
        for (let k = 0; k < 16; k++) pts.push(V(x, hY + (top0.y - hY) * k / 15, 0));
        for (let k = 1; k < 32; k++) { const a = k / 32 * Math.PI; pts.push(V(x, SHEAVE.y + Math.sin(a) * SHEAVE.R, SHEAVE.z + Math.cos(a) * SHEAVE.R)); }
        for (let k = 0; k < 17; k++) pts.push(V(x, SHEAVE.y + (cwTop.y - SHEAVE.y) * k / 16, CW.z));
        stubs[i].m.visible = false;
      } else {
        // upper part: from the torn end (rising) over the sheave to the counterweight
        const endY = Math.min(b.y + b.up, SHEAVE.y - 0.05);
        const fl = b.flail || 0;
        for (let k = 0; k < 16; k++) { const u = k / 15, w = (1 - u) * (1 - u) * fl; pts.push(V(x + Math.sin(t * 23 + i * 2 + u * 5) * 0.05 * w, endY + (top0.y - endY) * u, Math.cos(t * 19 + i + u * 4) * 0.08 * w)); }
        for (let k = 1; k < 32; k++) { const a = k / 32 * Math.PI; pts.push(V(x, SHEAVE.y + Math.sin(a) * SHEAVE.R, SHEAVE.z + Math.cos(a) * SHEAVE.R)); }
        for (let k = 0; k < 17; k++) pts.push(V(x, SHEAVE.y + (cwTop.y - SHEAVE.y) * k / 16, CW.z));
        // stub on the car hitch
        const sp = [], sl = Math.max(0.05, b.stub ?? 0.35), sf = b.stubFlail ?? 0.5;
        for (let k = 0; k < 24; k++) { const u = k / 23; sp.push(V(x + Math.sin(t * 17 + i * 3 + u * 3) * 0.06 * u * u * sf, hY + sl * u, Math.cos(t * 13 + i) * 0.05 * u * u * sf + 0.02 * u * u)); }
        stubs[i].t.update(sp); stubs[i].m.visible = true;
      }
      ropes[i].t.update(pts);
    });
    // governor rope: down from the governor sheave's left side to the car linkage, and from the right side to the pit
    const gx = GOV.x, gy = YM + 0.62, attach = V(gx, carY + CAR.top + 0.05, GOV.z);
    const gp = [];
    for (let k = 0; k < 12; k++) gp.push(V(gx, gy + (attach.y - gy) * (1 - k / 11), GOV.z).setY(attach.y + (gy - attach.y) * (k / 11)));
    for (let k = 1; k < 16; k++) { const a = Math.PI - k / 16 * Math.PI; gp.push(V(gx + GOV.R + Math.cos(a) * GOV.R, gy + Math.sin(a) * GOV.R, GOV.z)); }
    for (let k = 0; k < 13; k++) gp.push(V(gx + 2 * GOV.R, gy - (gy - bot - 0.3) * k / 12, GOV.z));
    govRope.update(gp);
  }
  return { group, car, cw, sheave, gov, setGovernor, setGear, update, railU, lamps, ropes, stubs, gears, mr, numMats };
}

// neutral IBL for the inside of the half-cut shaft: grey concrete box, the open (cut) front is bright daylight,
// warm lamp strips on the back wall -> metals read as steel instead of mirroring the blue sky
export function shaftEnvironment(renderer) {
  const s = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.BoxGeometry(4, 10, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.16, 0.155, 0.15), side: THREE.BackSide })); s.add(room);
  const open = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 9.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.5, 1.55, 1.65) })); open.position.z = 1.98; open.rotation.y = Math.PI; s.add(open);
  for (let i = -2; i <= 2; i++) { const l = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.12), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 4.4, 3.6) })); l.position.set(i % 2 ? -1 : 1, i * 1.9, -1.98); s.add(l); }
  const top = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 3.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 0.9, 0.92) })); top.rotation.x = Math.PI / 2; top.position.y = 4.95; s.add(top);
  const pm = new THREE.PMREMGenerator(renderer);
  return pm.fromScene(s, 0.02, 0.05, 30).texture;
}
