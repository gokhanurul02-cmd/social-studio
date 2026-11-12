// X-ray stomach + oesophagus + a few intestine loops, positioned from the posed guy's bones (world space).
// lift 0..1 pushes the stomach up towards the throat ("midenin ağzına gelmesi"); the oesophagus shortens/bulges.
import * as THREE from 'three';
import { Tube } from './mats.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function xrayOrganMaterial(col = 0xff8a3d, key = 'organ-xr') {
  const m = new THREE.MeshStandardMaterial({ color: 0x000000, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const u = { uCol: { value: new THREE.Color(col) }, uK: { value: 1 }, uT: { value: 0 } };
  m.userData.u = u;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vOP;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 uCol; uniform float uK, uT; varying vec3 vOP;')
      .replace('#include <dithering_fragment>', `#include <dithering_fragment>
        { float f = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition)));
          float rug = 0.75 + 0.25 * sin(vOP.y * 260.0 + sin(vOP.x * 180.0) * 2.0 + uT * 3.0);
          gl_FragColor = vec4(uCol * (0.12 + 1.6 * pow(f, 2.0)) * rug * uK, 1.0); }`);
  };
  m.customProgramCacheKey = () => key;
  return m;
}

export function buildStomach(rig) {
  const J = n => rig.bones[n].getWorldPosition(V(0, 0, 0));
  const sp = J('Spine'), sp1 = J('Spine1'), sp2 = J('Spine2'), nk = J('Neck');
  const right = J('LeftShoulder').sub(J('RightShoulder')).setY(0).normalize();   // character's left (+x)
  const fwd = V(0, 1, 0).cross(right).normalize();
  const base = sp1.clone().lerp(sp, 0.35).addScaledVector(fwd, 0.06);
  const group = new THREE.Group();
  const mat = xrayOrganMaterial(0xff8a3d);
  const gut = xrayOrganMaterial(0xffc06a, 'gut-xr');
  const st = new Tube(48, 24, 0.04, true); const stM = new THREE.Mesh(st.geo, mat); stM.renderOrder = 6; stM.frustumCulled = false; group.add(stM);
  const oe = new Tube(32, 14, 0.011, true); const oeM = new THREE.Mesh(oe.geo, mat); oeM.renderOrder = 6; oeM.frustumCulled = false; group.add(oeM);
  // intestine loops (static, lower belly)
  const r = mulberry(9); const loops = [];
  for (let i = 0; i < 5; i++) {
    const c = sp.clone().addScaledVector(fwd, 0.07).add(V(0, -0.05 - 0.035 * i, 0));
    const pts = []; for (let k = 0; k < 40; k++) { const a = k / 39 * Math.PI * 2 * 1.5 + i; pts.push(c.clone().addScaledVector(right, Math.cos(a) * (0.06 + 0.04 * r())).addScaledVector(fwd, Math.sin(a) * 0.03).add(V(0, Math.sin(a * 1.7) * 0.015, 0))); }
    const t = new Tube(40, 10, 0.012, true); t.update(pts); const m = new THREE.Mesh(t.geo, gut); m.renderOrder = 6; m.frustumCulled = false; group.add(m); loops.push(m);
  }
  function update(lift, t = 0) {
    mat.userData.u.uT.value = t; gut.userData.u.uT.value = t;
    const up = V(0, 0.15 * lift, 0);
    // J-shaped stomach: fundus (char's left, high) -> body -> antrum -> pylorus (char's right)
    const P = (x, y, z) => base.clone().addScaledVector(right, x).add(V(0, y, 0)).addScaledVector(fwd, z).add(up);
    const ctrl = [P(0.02, 0.07, 0.0), P(0.06, 0.06, 0.01), P(0.075, 0.02, 0.015), P(0.065, -0.03, 0.02), P(0.03, -0.06, 0.025), P(-0.02, -0.055, 0.02), P(-0.05, -0.03, 0.01), P(-0.06, -0.005, 0.0)];
    const crv = new THREE.CatmullRomCurve3(ctrl, false, 'centripetal');
    const pts = crv.getSpacedPoints(47);
    const wob = 1 + 0.06 * Math.sin(t * 9) * lift;
    st.update(pts, i => { const u = i / 47; return (0.012 + 0.048 * Math.sin(Math.PI * Math.min(1, u * 1.15 + 0.08)) * (1 - 0.45 * u)) * wob * (1 + 0.15 * lift); });
    // oesophagus from the throat to the cardia (top of the stomach)
    const top = nk.clone().addScaledVector(fwd, 0.03).add(V(0, -0.02, 0)), car = pts[0].clone();
    const op = []; for (let k = 0; k < 32; k++) { const u = k / 31; op.push(top.clone().lerp(car, u).addScaledVector(fwd, 0.015 * Math.sin(Math.PI * u))); }
    oe.update(op, i => 0.008 + 0.006 * lift * Math.exp(-Math.pow((i / 31 - 0.75) / 0.2, 2)));
  }
  update(0, 0);
  return { group, update, mat };
}
