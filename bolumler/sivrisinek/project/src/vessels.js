// X-ray blood vessel network built from the posed guy's joints (world space), with flow pulses running
// towards the puncture point and a drain front that empties the vessels from the extremities inwards.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { mulberry } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildVessels(rig, puncture, front) {
  const rnd = mulberry(1234);
  const J = n => rig.bones[n].getWorldPosition(V(0, 0, 0));
  const up = front.clone().normalize();               // world direction of the chest's front
  const heart = J('Spine2').lerp(J('Spine1'), 0.5).addScaledVector(up, 0.03);
  heart.add(J('LeftShoulder').sub(J('RightShoulder')).normalize().multiplyScalar(0.035));
  const chains = [];
  const tip = (h, f) => J(h + 'Hand' + f + '4');
  const add = (pts, r0, r1, branches = 3, lvl = 0) => {
    chains.push({ pts, r0, r1 });
    if (lvl > 1) return;
    const crv = new THREE.CatmullRomCurve3(pts);
    for (let i = 0; i < branches; i++) {
      const u = 0.15 + 0.75 * rnd(), p = crv.getPointAt(u), tan = crv.getTangentAt(u);
      const side = V(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).cross(tan).normalize();
      const len = (0.05 + 0.1 * rnd()) * (lvl ? 0.6 : 1);
      const q1 = p.clone().addScaledVector(side, len * 0.5).addScaledVector(tan, len * 0.4);
      const q2 = p.clone().addScaledVector(side, len).addScaledVector(tan, len * 0.9).add(V(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).multiplyScalar(len * 0.3));
      const rr = (r0 + (r1 - r0) * u) * 0.45;
      add([p, q1, q2], rr, rr * 0.4, lvl ? 0 : 2, lvl + 1);
    }
  };
  // aorta arch + carotids + head
  const neck = J('Neck'), head = J('Head'), top = J('HeadTop_End');
  for (const s of [-1, 1]) {
    const off = J('LeftShoulder').sub(J('RightShoulder')).normalize().multiplyScalar(0.025 * s);
    add([heart, neck.clone().add(off), head.clone().add(off).addScaledVector(up, 0.02), top.clone().add(off.clone().multiplyScalar(2)).addScaledVector(up, 0.04)], 0.007, 0.003, 5);
  }
  // arms
  for (const S of ['Left', 'Right']) {
    const sh = J(S + 'Shoulder'), ar = J(S + 'Arm'), fa = J(S + 'ForeArm'), ha = J(S + 'Hand');
    add([heart, sh.clone().lerp(heart, 0.3).addScaledVector(up, 0.03), ar, ar.clone().lerp(fa, 0.5), fa, fa.clone().lerp(ha, 0.5), ha], 0.009, 0.004, 6);
    for (const f of ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']) add([ha, J(S + 'Hand' + f + '1'), J(S + 'Hand' + f + '2'), tip(S, f)], 0.0028, 0.0012, 0);
  }
  // descending aorta, legs
  const sp1 = J('Spine1'), sp = J('Spine'), hips = J('Hips');
  add([heart, sp1.clone().addScaledVector(up, 0.02), sp.clone().addScaledVector(up, 0.02), hips.clone().addScaledVector(up, 0.02)], 0.012, 0.01, 6);
  for (const S of ['Left', 'Right']) {
    const ul = J(S + 'UpLeg'), lg = J(S + 'Leg'), ft = J(S + 'Foot'), toe = J(S + 'ToeBase'), te = J(S + 'Toe_End');
    add([hips.clone().addScaledVector(up, 0.02), ul, ul.clone().lerp(lg, 0.5), lg, lg.clone().lerp(ft, 0.5), ft, toe, te], 0.009, 0.004, 7);
  }
  // organs: a few loops in the belly/chest
  for (let i = 0; i < 6; i++) {
    const c = sp.clone().lerp(sp1, rnd()).addScaledVector(up, 0.03);
    const a = c.clone().add(V(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).multiplyScalar(0.16)), b = c.clone().add(V(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).multiplyScalar(0.16));
    add([c, a, b], 0.004, 0.002, 2, 1);
  }
  // the vein that feeds the proboscis: from the elbow to the puncture point
  add([J('RightForeArm'), puncture.clone().lerp(J('RightForeArm'), 0.5), puncture], 0.006, 0.006, 0, 2);

  const geos = [];
  for (const c of chains) {
    const crv = new THREE.CatmullRomCurve3(c.pts, false, 'centripetal');
    const seg = Math.max(8, Math.round(crv.getLength() * 160)), rad = 8, RK = 1.8;
    const g = new THREE.TubeGeometry(crv, seg, 1, rad, false);
    const P = g.attributes.position, D = new Float32Array(P.count), p = V(0, 0, 0);
    for (let i = 0; i <= seg; i++) {
      const u = i / seg, cp = crv.getPointAt(u), r = (c.r0 + (c.r1 - c.r0) * u) * RK;
      for (let j = 0; j <= rad; j++) { const k = i * (rad + 1) + j; p.set(P.getX(k), P.getY(k), P.getZ(k)).sub(cp).multiplyScalar(r).add(cp); P.setXYZ(k, p.x, p.y, p.z); D[k] = cp.distanceTo(puncture); }
    }
    g.setAttribute('dist', new THREE.BufferAttribute(D, 1));
    g.deleteAttribute('uv'); g.computeVertexNormals();
    geos.push(g.index ? g.toNonIndexed() : g);
  }
  const geo = mergeGeometries(geos, false);
  let maxD = 0; for (const d of geo.attributes.dist.array) maxD = Math.max(maxD, d);
  const u = { uT: { value: 0 }, uDrain: { value: 0 }, uMax: { value: maxD }, uK: { value: 1 } };
  const mat = new THREE.MeshStandardMaterial({ color: 0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float dist; varying float vDist;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvDist = dist;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform float uT, uDrain, uMax, uK; varying float vDist;')
      .replace('#include <dithering_fragment>', `#include <dithering_fragment>
        { float f = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition)));
          float front = (1.0 - uDrain) * uMax;
          float full = 1.0 - smoothstep(front - 0.04, front + 0.02, vDist);
          float pulse = 0.65 + 0.35 * sin(vDist * 70.0 + uT * 26.0);
          vec3 blood = vec3(1.0, 0.08, 0.05) * (0.9 + 1.2 * f) * pulse;
          vec3 empty = vec3(0.35, 0.12, 0.2) * pow(f, 2.0) * 0.6;
          gl_FragColor = vec4(mix(empty, blood, full) * uK, 1.0); }`);
  };
  mat.customProgramCacheKey = () => 'vessels';
  const mesh = new THREE.Mesh(geo, mat); mesh.renderOrder = 5; mesh.frustumCulled = false;
  // blood particles streaming along the forearm vein into the proboscis
  const NP = 140, pm = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshBasicMaterial({ color: 0xff2a1a, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }), NP);
  pm.frustumCulled = false; pm.renderOrder = 6;
  const group = new THREE.Group(); group.add(mesh, pm);
  const m4 = new THREE.Matrix4();
  let stream = null;
  function setStream(curve) { stream = curve; }
  function update(t, drain, flow = 1, k = 1) {
    u.uT.value = t; u.uDrain.value = drain; u.uK.value = k;
    pm.visible = !!stream && flow > 0;
    if (stream) for (let i = 0; i < NP; i++) {
      const ph = (i / NP + t * 1.6 * flow) % 1, p = stream.getPointAt(ph);
      const r = 0.0035 * (0.6 + 0.4 * Math.sin(i * 7.3)) * Math.min(1, flow * 2);
      m4.makeScale(r, r, r).setPosition(p.x + Math.sin(i * 3.1) * 0.002, p.y + Math.cos(i * 5.7) * 0.002, p.z + Math.sin(i * 1.3) * 0.002); pm.setMatrixAt(i, m4);
    }
    pm.instanceMatrix.needsUpdate = true;
  }
  return { group, mesh, update, setStream, maxD, heart };
}
