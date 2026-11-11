// Passenger elevator cabin interior (local: floor y=0, interior x,z in [-0.75, 0.75], ceiling 2.35, doors at +z).
// Brushed stainless panels with seams, mirror (real planar reflection), stainless handrails, LED ceiling with area lights,
// granite floor, car operating panel with a dot-matrix floor indicator, centre-opening doors with a gap.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { brushedSteel, granite, blackGloss, machinedSteel, rubber, canvasTex, proc } from './mats.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const CAB = { W: 1.5, D: 1.5, H: 2.35 };

function box(w, h, d, mat, x, y, z, parent, { r = 0, cast = true } = {}) {
  const g = r > 0 ? new RoundedBoxGeometry(w, h, d, 3, r) : new THREE.BoxGeometry(w, h, d);
  const m = new THREE.Mesh(g, mat); m.position.set(x, y, z); m.castShadow = cast; m.receiveShadow = true; parent.add(m); return m;
}

// dot-matrix LED floor indicator
function drawDisplay(g, w, h, n, dir) {
  g.fillStyle = '#020202'; g.fillRect(0, 0, w, h);
  const txt = String(n), cols = 5, rows = 7, cell = 9, gap = 2, dw = cols * (cell + gap) + 10;
  const FONT = { '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], '3': ['11111', '00010', '00100', '00010', '00001', '10001', '01110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    'v': ['00000', '00100', '00100', '00100', '10101', '01110', '00100'], '^': ['00100', '01110', '10101', '00100', '00100', '00100', '00000'], ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'] };
  const glyphs = [dir > 0 ? '^' : dir < 0 ? 'v' : ' ', ...txt.split('')];
  const total = glyphs.length * dw, x0 = (w - total) / 2 + 5, y0 = (h - rows * (cell + gap)) / 2;
  glyphs.forEach((ch, gi) => {
    const f = FONT[ch] || FONT[' '];
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const on = f[r][c] === '1', x = x0 + gi * dw + c * (cell + gap) + cell / 2, y = y0 + r * (cell + gap) + cell / 2;
      g.beginPath(); g.arc(x, y, cell / 2, 0, Math.PI * 2);
      g.fillStyle = on ? (gi === 0 ? '#ffb020' : '#ff3a14') : 'rgba(60,12,6,0.55)'; g.fill();
    }
  });
}

function buttonFace(label, lit) {
  return canvasTex(128, 128, (g, w, h) => {
    const gr = g.createRadialGradient(64, 58, 10, 64, 64, 64); gr.addColorStop(0, '#d9dadc'); gr.addColorStop(1, '#8d9094');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.strokeStyle = lit ? '#ffb347' : '#5d6064'; g.lineWidth = 8; g.beginPath(); g.arc(64, 64, 54, 0, Math.PI * 2); g.stroke();
    g.fillStyle = '#26282b'; g.font = 'bold 54px Verdana'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(label, 64, 68);
  });
}

export function cabinEnvironment(renderer) {
  // approximate interior radiance for IBL (stainless reflects a bright ceiling, warm walls, dark floor)
  const s = new THREE.Scene();
  const mk = (w, h, d, c, x, y, z) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshBasicMaterial({ color: c, side: THREE.BackSide })); m.position.set(x, y, z); s.add(m); return m; };
  mk(1.6, 2.4, 1.6, new THREE.Color(0.045, 0.044, 0.042), 0, 1.2, 0);
  // bright reflected band under the ceiling, mid band, a person-sized orange/blue blob (reflections of the passenger)
  mk(1.58, 0.45, 1.58, new THREE.Color(0.42, 0.41, 0.39), 0, 2.12, 0);
  mk(1.57, 0.7, 1.57, new THREE.Color(0.12, 0.118, 0.112), 0, 1.45, 0);
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(0.45, 0.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.35, 0.09, 0.02) })); blob.position.set(0, 1.3, -0.7); s.add(blob);
  const blob2 = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.8), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.03, 0.05, 0.1) })); blob2.position.set(0, 0.55, -0.7); s.add(blob2);
  const lit = (w, d, x, z, k) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ color: new THREE.Color(k, k * 0.98, k * 0.94) })); m.rotation.x = Math.PI / 2; m.position.set(x, 2.38, z); s.add(m); };
  lit(1.1, 0.42, 0, -0.32, 9); lit(1.1, 0.42, 0, 0.32, 9);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.03, 0.03, 0.03) })); fl.rotation.x = -Math.PI / 2; fl.position.y = 0.01; s.add(fl);
  for (let i = -2; i <= 2; i++) for (const sgn of [-1, 1]) { const st = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 2.3), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.02, 0.02, 0.02) })); st.position.set(sgn * 0.79, 1.2, i * 0.3); st.rotation.y = -sgn * Math.PI / 2; s.add(st); }
  const pm = new THREE.PMREMGenerator(renderer);
  const rt = pm.fromScene(s, 0.02, 0.05, 20, { position: V(0, 1.4, 0.2) });
  return rt.texture;
}

export function buildCabin() {
  RectAreaLightUniformsLib.init();
  const { W, D, H } = CAB, hw = W / 2, hd = D / 2;
  const group = new THREE.Group(); group.name = 'cabin';
  const steelV = brushedSteel({ repeat: [1.2, 1.2], rot: Math.PI / 2, rough: 0.3 });     // vertical grain (walls)
  const steelH = brushedSteel({ repeat: [1.5, 1.5], rot: 0, rough: 0.28 });
  const steelDark = brushedSteel({ color: 0x8a8d91, repeat: [2, 2], rot: 0, rough: 0.36 });
  const seam = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.8 });
  // floor
  const floor = box(W, 0.04, D, granite(), 0, -0.02, 0, group, { cast: false });
  // wall shell behind panels (dark, fills seams)
  box(W + 0.06, H, 0.02, seam, 0, H / 2, -hd - 0.03, group, { cast: false });
  box(0.02, H, D + 0.06, seam, -hw - 0.03, H / 2, 0, group, { cast: false });
  box(0.02, H, D + 0.06, seam, hw + 0.03, H / 2, 0, group, { cast: false });
  // side walls: 3 panels each, 4 mm seams, kick plate
  const pw = (D - 0.008 * 2) / 3;
  for (const sx of [-1, 1]) for (let i = 0; i < 3; i++) {
    const z = -hd + pw / 2 + i * (pw + 0.008);
    box(0.012, H - 0.14, pw, steelV, sx * (hw + 0.006), 0.1 + (H - 0.14) / 2, z, group);
    box(0.016, 0.1, pw, steelDark, sx * (hw + 0.004), 0.05, z, group);
  }
  // back wall: lower panels, mirror with steel frame, upper panels
  const bw = (W - 0.008 * 2) / 3;
  for (let i = 0; i < 3; i++) { const x = -hw + bw / 2 + i * (bw + 0.008); box(bw, 0.86, 0.012, steelV, x, 0.1 + 0.43, -hd - 0.006, group); box(bw, 0.1, 0.016, steelDark, x, 0.05, -hd - 0.004, group); box(bw, 0.2, 0.012, steelV, x, H - 0.1, -hd - 0.006, group); }
  const MW = W - 0.08, MH = H - 0.2 - 0.97, MY = 0.97 + MH / 2;
  box(W, 0.03, 0.03, steelH, 0, 0.965, -hd + 0.004, group);
  box(W, 0.03, 0.03, steelH, 0, H - 0.2 + 0.005, -hd + 0.004, group);
  const mirror = new Reflector(new THREE.PlaneGeometry(MW, MH), { textureWidth: 1024, textureHeight: 900, clipBias: 0.002, multisample: 0 });
  mirror.material.fragmentShader = mirror.material.fragmentShader.replace('gl_FragColor = vec4( blendOverlay( base.rgb, color ), 1.0 );', 'gl_FragColor = vec4( base.rgb * vec3(0.86, 0.88, 0.89), 1.0 );');
  mirror.position.set(0, MY, -hd + 0.001); group.add(mirror);
  // handrails (back + both sides), round tube with brackets and returns
  const railMat = brushedSteel({ repeat: [6, 0.3], rot: 0, rough: 0.22 });
  const rail = (pts) => { const c = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.05); const m = new THREE.Mesh(new THREE.TubeGeometry(c, 80, 0.019, 20, false), railMat); m.castShadow = true; m.receiveShadow = true; group.add(m); return m; };
  const RY = 0.9, off = 0.07;
  rail([V(-hw + 0.12, RY, -hd), V(-hw + 0.16, RY, -hd + off), V(0, RY, -hd + off), V(hw - 0.16, RY, -hd + off), V(hw - 0.12, RY, -hd)]);
  for (const sx of [-1, 1]) rail([V(sx * hw, RY, -hd + 0.2), V(sx * (hw - off), RY, -hd + 0.25), V(sx * (hw - off), RY, 0.1), V(sx * (hw - off), RY, hd - 0.42), V(sx * hw, RY, hd - 0.36)]);
  for (const [x, z, rx] of [[-0.35, -hd + 0.035, 1], [0.35, -hd + 0.035, 1], [-hw + 0.035, -0.2, 0], [hw - 0.035, -0.2, 0], [-hw + 0.035, 0.2, 0], [hw - 0.035, 0.2, 0]]) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, 0.07, 12), railMat); b.position.set(x, RY - 0.005, z); b.rotation.set(rx ? Math.PI / 2 : 0, 0, rx ? 0 : Math.PI / 2); group.add(b);
  }
  // ceiling: dark steel frame + two LED diffuser panels + downlights
  const ceil = new THREE.Group(); ceil.position.y = H; group.add(ceil);
  box(W + 0.04, 0.03, D + 0.04, steelDark, 0, 0.015, 0, ceil, { cast: false });
  const ledMat = proc(new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xfff6ea, emissiveIntensity: 7.0, roughness: 0.6 }), 'led', {
    color: '{ }', height: '',
  });
  const panels = [];
  for (const z of [-0.33, 0.33]) {
    box(1.16, 0.012, 0.5, steelDark, 0, -0.006, z, ceil, { cast: false });
    const p = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.44), ledMat); p.rotation.x = Math.PI / 2; p.position.set(0, -0.0125, z); ceil.add(p); panels.push(p);
    const L = new THREE.RectAreaLight(0xfff3e6, 9, 1.1, 0.44); L.position.set(0, H - 0.02, z); L.lookAt(0, 0, z); group.add(L); panels.push(L);
  }
  // ventilation slots along the ceiling edge
  for (let i = 0; i < 18; i++) box(0.05, 0.004, 0.012, seam, -0.6 + i * 0.07, H - 0.02, 0, group, { cast: false });
  // front wall: door jambs, header, centre-opening doors with a gap, sill
  const doorW = 0.9, dh = 2.1, jamb = (W - doorW) / 2;
  for (const sx of [-1, 1]) box(jamb, H, 0.03, steelV, sx * (hw - jamb / 2), H / 2, hd + 0.015, group);
  box(doorW, H - dh, 0.03, steelV, 0, dh + (H - dh) / 2, hd + 0.015, group);
  const doors = [];
  for (const sx of [-1, 1]) { const d = box(doorW / 2 - 0.006, dh, 0.025, steelV, sx * (doorW / 4 + 0.003), dh / 2, hd + 0.045, group); doors.push(d); }
  const sill = proc(new THREE.MeshStandardMaterial({ color: 0xbfc3c8, metalness: 1, roughness: 0.35 }), 'sill', { color: '{ float g = step(0.5, fract(vO.z * 90.0)); diffuseColor.rgb *= 0.55 + 0.45 * g; _H = g * 0.0006; }' });
  box(W, 0.012, 0.09, sill, 0, 0.006, hd + 0.03, group, { cast: false });
  // what is behind the door gap: dark shaft with a faint passing light
  const behind = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.4), new THREE.MeshBasicMaterial({ color: 0x050607 })); behind.position.set(0, 1.2, hd + 0.2); behind.rotation.y = Math.PI; group.add(behind);
  // car operating panel (right wall near the door) with indicator + buttons
  const cop = new THREE.Group(); cop.position.set(hw - 0.012, 0, hd - 0.3); cop.rotation.y = -Math.PI / 2; group.add(cop);
  box(0.26, 1.25, 0.012, steelH, 0, 0.85 + 0.625, 0, cop, { r: 0.004 });
  const disp = canvasTex(256, 112, (g, w, h) => drawDisplay(g, w, h, 20, 0));
  const dispMat = new THREE.MeshPhysicalMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: disp, emissiveIntensity: 6, roughness: 0.05, clearcoat: 1, clearcoatRoughness: 0.02 });
  const dm = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.0875), dispMat); dm.position.set(0, 1.93, 0.0075); cop.add(dm);
  box(0.215, 0.1, 0.004, blackGloss(), 0, 1.93, 0.0045, cop, { cast: false });
  // second indicator above the doors (inside face of the header)
  const hdisp = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.114), dispMat); hdisp.position.set(0, 2.225, hd - 0.0045); hdisp.rotation.y = Math.PI; group.add(hdisp);
  box(0.28, 0.13, 0.006, blackGloss(), 0, 2.225, hd - 0.0005, group, { cast: false });
  const btnFrame = machinedSteel(0xc8cbd0, 0.18);
  const labels = ['21', '20', '19', '18', '17', '16', '15', '14', '13', '12', '11', '10', '9', '8', '7', '6'];
  labels.forEach((l, i) => {
    const x = (i % 2 ? 0.05 : -0.05), y = 1.78 - Math.floor(i / 2) * 0.075;
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.024, 0.008, 32), btnFrame); ring.rotation.x = Math.PI / 2; ring.position.set(x, y, 0.01); cop.add(ring);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.019, 32), new THREE.MeshStandardMaterial({ map: buttonFace(l, l === '20'), metalness: 0.8, roughness: 0.3, emissive: l === '20' ? 0x553000 : 0x000000 }));
    face.position.set(x, y, 0.0145); cop.add(face);
  });
  const alarm = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.01, 32), new THREE.MeshPhysicalMaterial({ color: 0xffc400, roughness: 0.25, clearcoat: 1 })); alarm.rotation.x = Math.PI / 2; alarm.position.set(0, 1.12, 0.012); cop.add(alarm);
  // small emergency phone grille
  for (let i = 0; i < 5; i++) box(0.09, 0.004, 0.003, seam, 0, 1.0 - i * 0.012, 0.0075, cop, { cast: false });

  let shown = null;
  function setDisplay(n, dir = 0) {
    const k = n + ':' + dir; if (k === shown) return; shown = k;
    const { g, canvas } = disp.userData; drawDisplay(g, canvas.width, canvas.height, n, dir); disp.needsUpdate = true;
  }
  function setLights(k) { ledMat.emissiveIntensity = 7.0 * k; for (const p of panels) if (p.isLight) p.intensity = 9 * k; }
  function setDoorGap(g) { doors[0].position.x = -(0.9 / 4 + 0.003 + g / 2); doors[1].position.x = 0.9 / 4 + 0.003 + g / 2; }
  setDoorGap(0.012);
  return { group, mirror, setDisplay, setLights, setDoorGap, ceil, cop, H, panels, floor };
}
