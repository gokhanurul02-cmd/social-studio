// Characters built on the Xbot (Mixamo-derived) rig from the three.js examples.
// Baby: bone-scaled proportions + procedural crawl/stand poses.
// Strongman: muscle-bulked rig driven by the walk/idle clips with procedural overrides.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import { SimplifyModifier } from 'three/addons/modifiers/SimplifyModifier.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';

let GLTF = null;
const MH = {}; const FACE = { tex: null, tat: null, logo: null };
export async function loadMakeHuman() {
  for (const n of ['baby', 'man']) MH[n] = await (await fetch(`./assets/mh_${n}.json`)).json();
  FACE.tex = await new THREE.TextureLoader().loadAsync('./assets/ref_face_strongman_detail.png'); FACE.tex.colorSpace = THREE.SRGBColorSpace;
  FACE.tat = await new THREE.TextureLoader().loadAsync('./assets/ref_tattoo_mask.png');
  FACE.logo = await new THREE.TextureLoader().loadAsync('./assets/ref_logo_mask.png');
  return MH;
}
export async function loadRig() { GLTF = await new GLTFLoader().loadAsync('./assets/Xbot.glb'); return GLTF; }

const Q = (x = 0, y = 0, z = 0) => new THREE.Quaternion().setFromEuler(new THREE.Euler(x, y, z, 'XYZ'));
const DEG = Math.PI / 180;

// ---------------------------------------------------------------- materials
const MASK_COMMON = /* glsl */`
  varying vec3 vBind;
  uniform float uHarness; uniform float uKind; uniform float uHideHead; uniform vec3 uSkin;
  float h3(vec3 p){ p = fract(p*0.3183099+.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
  float n3(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.-2.*f);
    return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z); }
  float band(float v, float a, float b, float s){ return smoothstep(a-s,a+s,v)*(1.0-smoothstep(b-s,b+s,v)); }
`;
// returns: rgb, roughness in a vec4
const MASK_FN = /* glsl */`
  uniform vec4 uL1, uL2, uL3, uL4; uniform float uH;
  uniform sampler2D uFace; uniform float uFaceOn; uniform vec4 uFaceA; uniform vec4 uFaceM; uniform vec2 uFaceSize; uniform float uFaceSy; uniform sampler2D uTat; uniform sampler2D uLogo; uniform float uTatOn;
  // uL1 = legY, hipsY, spineY, chestY ; uL2 = neckY, kneeY, ankleY, shoulderX
  // uL3 = elbowX, handX, armY, eyeY   ; uL4 = eyeX, eyeZ, mouthY, mouthZ   (metres, T-pose bind space)
  vec4 charSurface(vec3 b){
    vec3 col = uSkin; float rough = 0.5;
    float ax = abs(b.x), H = uH;
    float legY = uL1.x, hipsY = uL1.y, spineY = uL1.z, chestY = uL1.w;
    float neckY = uL2.x, kneeY = uL2.y, ankleY = uL2.z, shX = uL2.w;
    float elX = uL3.x, haX = uL3.y, armY = uL3.z, eyeY = uL3.w;
    float eyeX = uL4.x, eyeZ = uL4.y;
    bool arm = ax > shX * 1.05 && b.y > chestY - 0.04 * H;
    float s = 0.0025 * H;
    // eyebrows (both characters): thin dark band above each eye on the front of the face
    float brow = band(b.y, eyeY + eyeX * 0.62, eyeY + eyeX * 0.92, s * 0.5) * band(ax, eyeX * 0.25, eyeX * 2.0, s)
               * step(eyeZ - eyeX * 0.6, b.z) * step(b.y, neckY + 0.5 * H);
    if (uKind < 0.5) {
      // ---- baby: disposable diaper + red climbing harness
      float dTop = hipsY + 0.55 * (spineY - hipsY), dBot = legY - 0.28 * (legY - kneeY);
      float diaper = band(b.y, dBot, dTop, s) * (arm ? 0.0 : 1.0);
      col = mix(col, vec3(0.94, 0.95, 0.98), diaper); rough = mix(rough, 0.78, diaper);
      float tab = diaper * band(b.y, dTop - 0.05 * (dTop - dBot), dTop, s) * band(ax, 0.3 * shX, 0.65 * shX, s);
      col = mix(col, vec3(0.6, 0.78, 0.96), tab * 0.8);
      if (uHarness > 0.5 && !arm) {
        float t = 0.022 * H; float h = 0.0;
        float wy = spineY + 0.35 * (chestY - spineY);
        h = max(h, band(b.y, wy - t * 0.5, wy + t * 0.5, s));                                   // waist belt
        h = max(h, band(b.y, chestY - t * 0.3, chestY + t * 0.7, s) * step(ax, shX * 0.95));     // chest strap
        h = max(h, band(ax, 0.38 * shX, 0.38 * shX + t, s) * band(b.y, wy, neckY + 0.01 * H, s)); // shoulder straps
        float ly = legY - 0.16 * (legY - kneeY);
        h = max(h, band(b.y, ly - t * 0.45, ly + t * 0.45, s) * step(0.01 * H, ax));            // leg loops
        col = mix(col, vec3(0.86, 0.06, 0.04), h); rough = mix(rough, 0.35, h);
        float buckle = band(b.y, wy - t * 0.7, wy + t * 0.7, s) * band(ax, 0.0, 0.025 * H, s) * step(0.0, b.z);
        col = mix(col, vec3(0.22, 0.02, 0.02), buckle);
      }
      col = mix(col, vec3(0.62, 0.42, 0.32), brow * 0.6);
    } else {
      // ---- strongman: black trunks, knee pads, boots, elbow sleeves, wrist tape, left-shoulder tattoo
      float tTop = hipsY + 0.42 * (spineY - hipsY), tBot = legY - 0.22 * (legY - kneeY);
      float trunks = band(b.y, tBot, tTop, s) * (arm ? 0.0 : 1.0);
      float knee = band(b.y, kneeY - 0.045 * H, kneeY + 0.04 * H, s) * step(b.y, legY);
      float boot = 1.0 - smoothstep(ankleY + 0.42 * (kneeY - ankleY) - s, ankleY + 0.42 * (kneeY - ankleY) + s, b.y);
      float sleeve = band(ax, elX - 0.04 * H, elX + 0.012 * H, s) * (arm ? 1.0 : 0.0);
      float wrist = band(ax, haX - 0.05 * H, haX - 0.022 * H, s) * (arm ? 1.0 : 0.0);
      float black = max(max(trunks, knee), max(boot, max(sleeve, wrist)));
      float letters = trunks * band(b.y, tBot + 0.45 * (tTop - tBot), tBot + 0.8 * (tTop - tBot), s) * step(0.0, b.z)
                    * step(ax, 0.06 * H) * step(0.45, n3(b * vec3(90.0, 60.0, 90.0)));
      // tattoo: character's left (+x) pec, shoulder cap and upper arm
      float tatRegion = smoothstep(0.015 * H, 0.04 * H, b.x) * step(b.x, elX - 0.05 * H)
                      * band(b.y, chestY - 0.05 * H, armY + 0.045 * H, 0.01 * H) * step(-0.03 * H, b.z);
      vec2 tc = vec2(b.x - shX, b.y - armY);
      float pat = abs(fract(length(tc) * 38.0 + n3(b * 40.0) * 0.7) - 0.5);
      float tat = tatRegion * smoothstep(0.22, 0.1, pat) * step(0.32, n3(b * 26.0));
      if (uTatOn > 0.5) {
        tat = 0.0;
        // reference tattoo mask (crop of the 18.3 s frame, origin 300,150 in a 900x1100 torso crop):
        // midline x=337 px -> bind x=0; pec base row 645 px -> y=1.33; 950 px/m across, 1450 px/m down
        vec2 tp = vec2(337.0 + b.x * 950.0 - 300.0, 645.0 - (b.y - 1.33) * 1450.0 - 150.0);
        if (b.z > -0.03 * H && tp.x > 0.0 && tp.x < 420.0 && tp.y > 0.0 && tp.y < 550.0 && !(ax > shX * 1.25))
          tat = smoothstep(0.12, 0.5, texture2D(uTat, vec2(tp.x / 420.0, 1.0 - tp.y / 550.0)).r);
      }
      col = mix(col, vec3(0.045, 0.032, 0.03), tat * 0.92);
      col = mix(col, vec3(0.03, 0.03, 0.035), black); rough = mix(rough, boot > 0.5 ? 0.22 : 0.4, black);
      if (uTatOn > 0.5) {
        // "THE ROCK" trunk logo mask from the same crop (origin 185,815; 285x130), 1180 px/m, centred at x=-0.021, y=1.0
        vec2 lp = vec2(142.0 + (b.x + 0.021) * 1180.0, 65.0 - (b.y - 1.0) * 1180.0);
        letters = 0.0;
        if (b.z > 0.0 && trunks > 0.5 && lp.x > 0.0 && lp.x < 285.0 && lp.y > 0.0 && lp.y < 130.0)
          letters = texture2D(uLogo, vec2(lp.x / 285.0, 1.0 - lp.y / 130.0)).r;
      }
      col = mix(col, vec3(0.88, 0.88, 0.9), letters * 0.95);
      // reference face crop projected onto the front of the head (planar, registered on the eyes)
      float fw = 0.0;
      if (uFaceOn > 0.5 && b.y > neckY) {
        vec2 px = vec2(uFaceA.x + b.x * uFaceA.z, uFaceA.y - (b.y - uFaceA.w) * uFaceSy);
        float e = length((px - uFaceM.xy) / uFaceM.zw);
        fw = (1.0 - smoothstep(0.55, 1.0, e)) * smoothstep(eyeZ - 0.09, eyeZ - 0.04, b.z);
        vec3 fc = texture2D(uFace, vec2(px.x / uFaceSize.x, 1.0 - px.y / uFaceSize.y)).rgb;
        col = mix(col, fc * 1.0, fw); rough = mix(rough, 0.45, fw);
      }
      col = mix(col, vec3(0.08, 0.05, 0.04), brow * 0.85 * (1.0 - uFaceOn));
    }
    return vec4(col, rough);
  }
`;

export function makeCharMaterial(kind, skinHex) {
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.0 });
  const u = { uTat: { value: FACE.tat }, uLogo: { value: FACE.logo }, uTatOn: { value: 0 }, uFace: { value: FACE.tex }, uFaceOn: { value: 0 }, uFaceA: { value: new THREE.Vector4() }, uFaceM: { value: new THREE.Vector4() }, uFaceSize: { value: new THREE.Vector2(320, 380) }, uFaceSy: { value: 1 }, uL1: { value: new THREE.Vector4() }, uL2: { value: new THREE.Vector4() }, uL3: { value: new THREE.Vector4() }, uL4: { value: new THREE.Vector4() }, uH: { value: 1 }, uHideHead: { value: 0 }, uHarness: { value: 1 }, uKind: { value: kind === 'baby' ? 0 : 1 }, uSkin: { value: new THREE.Color(skinHex) } };
  mat.userData.u = u;
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 bindPos;\nvarying vec3 vBind;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBind = bindPos;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + MASK_COMMON + MASK_FN)
      .replace('#include <color_fragment>', '#include <color_fragment>\nif (uHideHead > 0.5 && vBind.y > 1.553 && abs(vBind.x) < 0.14) discard;\nvec4 cs = charSurface(vBind); diffuseColor.rgb = cs.rgb;')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = cs.a;');
  };
  mat.customProgramCacheKey = () => 'char-' + kind;
  return mat;
}

// ---------------------------------------------------------------- rig wrapper
class Rig {
  constructor(kind, skinHex, mh = null) {
    this.root = SkeletonUtils.clone(GLTF.scene);
    this.kind = kind;
    this.material = makeCharMaterial(kind, skinHex);
    this.meshes = [];
    this.bones = {};
    this.boneList = [];
    this.root.traverse(o => { if (o.isBone) { this.bones[o.name.replace('mixamorig', '')] = o; this.boneList.push(o); } });
    this.armature = this.root.getObjectByName('Armature');
    if (mh) this.buildMakeHuman(mh);
    else this.root.traverse(o => {
      if (o.isSkinnedMesh) {
        if (!o.geometry.attributes.bindPos) o.geometry.setAttribute('bindPos', o.geometry.attributes.position.clone());
        o.material = this.material; o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
        this.meshes.push(o);
      }
    });
    this.bindLocal = this.boneList.map(b => b.quaternion.clone());
    this.bindPos = this.boneList.map(b => b.position.clone());
    { const m = new Map(); this.bindModel = this.boneList.map(b => { const p = b.parent.isBone ? m.get(b.parent) : this.armature.quaternion; const w = p.clone().multiply(b.quaternion); m.set(b, w); return w; }); }
    // bind-pose bone directions (bone -> first child) in rig model space
    {
      this.root.updateMatrixWorld(true);
      const inv = new THREE.Matrix4().copy(this.root.matrixWorld).invert();
      const P = b => new THREE.Vector3().setFromMatrixPosition(new THREE.Matrix4().multiplyMatrices(inv, b.matrixWorld));
      const prefer = { Hand: 'Middle1', Hips: 'Spine', Spine2: 'Neck', Foot: 'ToeBase' };
      this.bindDir = this.boneList.map(b => {
        const kids = b.children.filter(c => c.isBone);
        const key = Object.keys(prefer).find(k => b.name.endsWith(k));
        const child = (key && kids.find(c => c.name.endsWith(prefer[key]))) || kids[0];
        if (!child) return new THREE.Vector3(0, 1, 0);
        return P(child).sub(P(b)).normalize();
      });
    }
    this.mixer = new THREE.AnimationMixer(this.root);
    this.actions = {};
    for (const clip of (mh ? this.mhClips : GLTF.animations)) this.actions[clip.name] = this.mixer.clipAction(clip);
    this.group = new THREE.Group(); this.group.add(this.root);
  }
  // Move the Xbot bones onto the MakeHuman joint centres (rest rotations kept, so clips/aims still apply),
  // then bind the continuous body to that skeleton with the precomputed weights.
  buildMakeHuman(mh) {
    for (const o of [...this.root.children]) o.traverse(m => { if (m.isSkinnedMesh) m.visible = false; });
    this.root.traverse(m => { if (m.isSkinnedMesh) m.parent && (m.visible = false); });
    const oldHips = this.bones.Hips.getWorldPosition(new THREE.Vector3()).y;
    this.root.updateMatrixWorld(true);
    for (const b of this.boneList) {
      const n = b.name.replace('mixamorig', ''); const j = mh.joints[n];
      if (j) { const inv = new THREE.Matrix4().copy(b.parent.matrixWorld).invert(); b.position.copy(new THREE.Vector3(...j).applyMatrix4(inv)); }
      b.updateMatrixWorld(true);
    }
    const N = mh.pos.length / 3;
    const g = new THREE.BufferGeometry();
    const pos = new THREE.Float32BufferAttribute(mh.pos, 3);
    g.setAttribute('position', pos); g.setAttribute('bindPos', pos.clone());
    g.setAttribute('color', new THREE.Float32BufferAttribute(mh.eyeCol, 3));
    const map = mh.bones.map(n => this.boneList.indexOf(this.bones[n]));
    const si = new Uint16Array(N * 4); for (let i = 0; i < N * 4; i++) si[i] = map[mh.skinIdx[i]];
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(mh.skinW, 4));
    g.setIndex([...mh.body, ...mh.eyes]);
    g.addGroup(0, mh.body.length, 0); g.addGroup(mh.body.length, mh.eyes.length, 1);
    g.computeVertexNormals();
    const eyeMat = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.12, clearcoat: 1.0 });
    const mesh = new THREE.SkinnedMesh(g, [this.material, eyeMat]);
    mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false;
    this.root.add(mesh); this.root.updateMatrixWorld(true);
    mesh.bind(new THREE.Skeleton(this.boneList));
    this.meshes = [mesh]; this.mh = mh;
    const L = mh.landmarks, u = this.material.userData.u;
    u.uL1.value.set(L.legY, L.hipsY, L.spineY, L.chestY); u.uL2.value.set(L.neckY, L.kneeY, L.ankleY, L.shoulderX);
    u.uL3.value.set(L.elbowX, L.handX, L.armY, L.eyeY); u.uL4.value.set(L.eyeX, L.eyeZ, L.mouthY, L.mouthZ); u.uH.value = L.height;
    // clips: rotations only (Xbot position/scale tracks would restore Xbot proportions); Hips height rescaled
    const k = L.hipsY / oldHips;
    this.mhClips = GLTF.animations.map(c => {
      const tracks = c.tracks.filter(t => t.name.endsWith('.quaternion') || /Hips\.position$/.test(t.name)).map(t => {
        if (!t.name.endsWith('.position')) return t;
        const t2 = t.clone(); for (let i = 0; i < t2.values.length; i++) t2.values[i] *= k; return t2;
      });
      return new THREE.AnimationClip(c.name, c.duration, tracks);
    });
  }
  resetBind() { this.boneList.forEach((b, i) => { b.quaternion.copy(this.bindLocal[i]); b.position.copy(this.bindPos[i]); }); }
  // set clip weights at absolute clip times: [{name, time, weight}]
  playClips(list) {
    this.mixer.stopAllAction();
    for (const c of list) { const a = this.actions[c.name]; a.reset(); a.play(); a.setEffectiveWeight(c.weight ?? 1); a.time = c.time % a.getClip().duration; a.paused = true; }
    this.mixer.update(0);
  }
  // model-space rotation deltas. mode 'rel': applied on top of the current (clip) pose.
  // mode 'abs': bone model rotation = delta * bindModelRotation (children without deltas inherit).
  applyDeltas(deltas, mode = 'rel') {
    const newW = new Map();
    const aq = this.armature.quaternion;
    this.boneList.forEach((b, i) => {
      const parentW = b.parent.isBone ? newW.get(b.parent) : aq;
      const cur = parentW.clone().multiply(b.quaternion);
      const d = deltas[b.name.replace('mixamorig', '')];
      let w = cur;
      if (d && d.aim) {
        // aim the bone (bind direction -> requested model-space direction), optional extra twist/tilt quaternion
        const q = new THREE.Quaternion().setFromUnitVectors(this.bindDir[i], d.aim.clone().normalize());
        if (d.pre) q.multiply(d.pre);
        w = q.multiply(this.bindModel[i]);
      } else if (d) w = mode === 'abs' ? d.clone().multiply(this.bindModel[i]) : d.clone().multiply(cur);
      if (d) b.quaternion.copy(parentW.clone().invert().multiply(w));
      newW.set(b, w);
    });
  }
  setNetScales(nets) {
    // nets: {Bone:[x,y,z]} desired accumulated scale; children compensate parents (aligned-axes approximation)
    // spec per bone: [radial1, along-bone, radial2]; resolved to the bone's local axes, with the parent's
    // accumulated scale re-expressed in the child frame (bind rotations are close to axis permutations)
    const netOf = new Map();
    this.boneList.forEach((b, i) => {
      const pnP = b.parent.isBone ? netOf.get(b.parent) : [1, 1, 1];
      const q = this.bindLocal[i];
      const pnc = [0, 1, 2].map(ax => {
        const e = new THREE.Vector3(ax === 0 ? 1 : 0, ax === 1 ? 1 : 0, ax === 2 ? 1 : 0).applyQuaternion(q);
        const a = [Math.abs(e.x), Math.abs(e.y), Math.abs(e.z)]; return pnP[a.indexOf(Math.max(...a))];
      });
      const want = nets[b.name.replace('mixamorig', '')];
      let n = pnc;
      if (want) {
        const kid = b.children.find(c => c.isBone);
        let al = 1;
        if (kid) { const p = kid.position; const a = [Math.abs(p.x), Math.abs(p.y), Math.abs(p.z)]; al = a.indexOf(Math.max(...a)); }
        const rest = [0, 1, 2].filter(x => x !== al);
        n = [0, 0, 0]; n[al] = want[1]; n[rest[0]] = want[0]; n[rest[1]] = want[2];
      }
      b.scale.set(n[0] / pnc[0], n[1] / pnc[1], n[2] / pnc[2]);
      netOf.set(b, n);
    });
  }
  // attach an object to a bone, specified in bind-pose model space (metres)
  attach(boneName, obj, pos, quat = new THREE.Quaternion(), scl = new THREE.Vector3(1, 1, 1)) {
    const bone = this.bones[boneName];
    this.resetBind(); this.root.updateMatrixWorld(true);
    const want = new THREE.Matrix4().compose(pos, quat, scl);
    const rootInv = new THREE.Matrix4().copy(this.root.matrixWorld).invert();
    const boneModel = new THREE.Matrix4().multiplyMatrices(rootInv, bone.matrixWorld);
    const local = new THREE.Matrix4().copy(boneModel).invert().multiply(want);
    local.decompose(obj.position, obj.quaternion, obj.scale);
    bone.add(obj);
    return obj;
  }
  worldOf(boneName, target = new THREE.Vector3()) { return this.bones[boneName].getWorldPosition(target); }
}

// ---------------------------------------------------------------- heads (replace the mannequin head)
let LPS = null;
export async function loadHeadScan() {
  const g = await new GLTFLoader().loadAsync('./assets/LeePerrySmith.glb');
  const tl = new THREE.TextureLoader();
  const map = await tl.loadAsync('./assets/Map-COL.jpg'); map.colorSpace = THREE.SRGBColorSpace; map.flipY = false;
  const nrm = await tl.loadAsync('./assets/Infinite-Level_02_Tangent_SmoothUV.jpg'); nrm.flipY = false;
  let mesh = null; g.scene.traverse(o => { if (o.isMesh) mesh = o; });
  mesh.updateMatrixWorld(true);
  const geo = mesh.geometry.clone().applyMatrix4(mesh.matrixWorld);
  geo.computeBoundingBox();
  LPS = { geo, map, nrm };
  return LPS;
}
function babyHead(rig) {
  const skinM = new THREE.MeshStandardMaterial({ color: BABY_SKIN, roughness: 0.55 });
  const whiteM = new THREE.MeshStandardMaterial({ color: 0xf4f0ea, roughness: 0.25 });
  const irisM = new THREE.MeshStandardMaterial({ color: 0x3a2416, roughness: 0.15 });
  const browM = new THREE.MeshStandardMaterial({ color: 0x9c7150, roughness: 0.8 });
  const lipM = new THREE.MeshStandardMaterial({ color: 0xc8786a, roughness: 0.45 });
  const HC = new THREE.Vector3(0, 1.665, 0.012), r = 0.096;
  const parts = [];
  const sph = (rad, m, p, s = [1, 1, 1], seg = 32) => { const o = new THREE.Mesh(new THREE.SphereGeometry(rad, seg, Math.round(seg * 0.7)), m); parts.push([o, HC.clone().add(new THREE.Vector3(...p)), new THREE.Vector3(...s)]); return o; };
  sph(r, skinM, [0, 0.012, -0.006], [1.0, 1.0, 1.06], 48);                 // cranium
  sph(r * 0.62, skinM, [0, -0.045, 0.028], [1.25, 0.95, 1.05]);           // jaw / lower face
  for (const s of [-1, 1]) {
    sph(r * 0.4, skinM, [s * 0.046, -0.038, 0.055], [1, 0.9, 0.85]);       // chubby cheeks
    sph(r * 0.16, whiteM, [s * 0.034, 0.004, 0.079], [1.25, 0.85, 0.6], 16); // eyes
    sph(r * 0.095, irisM, [s * 0.034, 0.004, 0.087], [1, 1, 0.55], 12);
    sph(r * 0.26, skinM, [s * 0.094, -0.008, 0.0], [0.42, 1.0, 0.75], 16); // ears
    const br = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.005, 0.008), browM); br.rotation.z = -s * 0.12;
    parts.push([br, HC.clone().add(new THREE.Vector3(s * 0.035, 0.027, 0.086)), new THREE.Vector3(1, 1, 1)]);
  }
  sph(r * 0.15, skinM, [0, -0.018, 0.094], [1.2, 0.95, 1.0], 16);         // nose
  sph(r * 0.11, lipM, [0, -0.052, 0.083], [2.0, 0.55, 0.6], 16);         // mouth
  for (const [o, p, s] of parts) { o.castShadow = true; rig.attach('Head', o, p, o.quaternion.clone(), s); }
}
function scanHead(rig) {
  const { geo, map, nrm } = LPS;
  const bb = geo.boundingBox, size = new THREE.Vector3(); bb.getSize(size);
  const k = 0.255 / size.y;
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map, normalMap: nrm, color: 0xd09470, roughness: 0.45 }));
  m.castShadow = true;
  const holder = new THREE.Group();
  const c = new THREE.Vector3(); bb.getCenter(c);
  m.position.set(-c.x, -bb.min.y, -c.z); holder.add(m);
  rig.attach('Head', holder, new THREE.Vector3(0, 1.462, 0.0), new THREE.Quaternion(), new THREE.Vector3(k * 1.12, k, k * 1.05));
  rig.headScan = holder;
}

// ---------------------------------------------------------------- baby
const BABY_NETS = {
  Hips: [1.18, 1.0, 1.22], Spine: [1.28, 0.8, 1.35], Spine1: [1.22, 0.8, 1.28], Spine2: [1.08, 0.78, 1.12],
  Neck: [0.72, 0.72, 0.72], Head: [1.32, 1.32, 1.32],
  LeftShoulder: [0.8, 0.7, 0.8], RightShoulder: [0.8, 0.7, 0.8],
  LeftArm: [1.45, 0.62, 1.45], RightArm: [1.45, 0.62, 1.45], LeftForeArm: [1.35, 0.6, 1.35], RightForeArm: [1.35, 0.6, 1.35],
  LeftHand: [0.9, 0.9, 0.9], RightHand: [0.9, 0.9, 0.9],
  LeftUpLeg: [1.16, 0.6, 1.16], RightUpLeg: [1.16, 0.6, 1.16], LeftLeg: [1.1, 0.58, 1.1], RightLeg: [1.1, 0.58, 1.1],
  LeftFoot: [0.95, 0.95, 0.95], RightFoot: [0.95, 0.95, 0.95],
};
// stubby baby fingers
for (const side of ['Left', 'Right']) for (const f of ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']) for (const k of [1, 2, 3, 4]) BABY_NETS[side + 'Hand' + f + k] = [0.62, 0.62, 0.62];
export const BABY_SCALE = 0.66;
export const BABY_SKIN = 0xeaa886;

export function makeBaby() {
  const rig = new Rig('baby', BABY_SKIN, MH.baby);
  rig.pose = (name, t, opts = {}) => babyPose(rig, name, t, opts);
  return rig;
}

// baby poses: bone directions (aims) in rig model space; character faces +Z, its left is +X ----------
const A = (x, y, z, pre) => ({ aim: new THREE.Vector3(x, y, z), pre });
function groundRig(rig, clearance) {
  const r = rig.root; r.position.y = 0; rig.group.updateMatrixWorld(true);
  const v = new THREE.Vector3(); let lo = 1e9;
  for (const n of ['LeftHand', 'RightHand', 'LeftLeg', 'RightLeg', 'LeftToeBase', 'RightToeBase', 'LeftFoot', 'RightFoot', 'LeftHandMiddle2', 'RightHandMiddle2']) {
    if (!rig.bones[n]) continue;
    rig.bones[n].getWorldPosition(v); rig.group.worldToLocal(v); lo = Math.min(lo, v.y);
  }
  r.position.y = clearance - lo;
}
function babyPose(rig, name, t, o) {
  rig.resetBind();
  const d = {};
  if (name === 'stand') {
    const rub = o.rub ?? 0, spread = o.spread ?? 0, look = o.look ?? 0, sway = Math.sin(t * 5.0) * 0.04;
    d.Hips = Q(0, look * 0.1, sway * 0.4);
    d.Spine = Q(-0.06, look * 0.15, sway * 0.4);
    d.Neck = Q(0.05, look * 0.3, 0);
    d.Head = Q(0.04 + rub * 0.1, look * 0.95, -rub * 0.15);
    const lerpV = (a, b, u) => a.map((x, i) => x + (b[i] - x) * u);
    // left arm: hanging -> spread out for balance
    const la = lerpV([0.32, -0.94, 0.12], [0.92, -0.35, 0.18], spread), lf = lerpV([0.18, -0.95, 0.35], [0.85, -0.3, 0.42], spread);
    d.LeftArm = A(...la); d.LeftForeArm = A(...lf); d.LeftHand = A(lf[0], lf[1] - 0.2, lf[2] + 0.3);
    // right arm: rubbing the eye -> spread
    const raR = [-0.3, -0.8, 0.55], rfR = [0.55, 0.72, 0.42];
    const raS = [-0.92, -0.35, 0.18], rfS = [-0.85, -0.3, 0.42], raH = [-0.32, -0.94, 0.12], rfH = [-0.18, -0.95, 0.35];
    const ra = rub > 0 ? lerpV(lerpV(raH, raS, spread), raR, rub) : lerpV(raH, raS, spread);
    const rf = rub > 0 ? lerpV(lerpV(rfH, rfS, spread), rfR, rub) : lerpV(rfH, rfS, spread);
    d.RightArm = A(...ra); d.RightForeArm = A(...rf); d.RightHand = A(rf[0] + 0.2 * rub, rf[1], rf[2] + 0.4);
    d.LeftUpLeg = A(0.1, -1, 0.02); d.RightUpLeg = A(-0.1, -1, 0.02);
    d.LeftLeg = A(0.03, -1, -0.03); d.RightLeg = A(-0.03, -1, -0.03);
    rig.applyDeltas(d, 'abs');
    groundRig(rig, 0.0);
  } else if (name === 'crawl') {
    const p = t * (o.rate ?? 1.6) * Math.PI * 2 + (o.phase ?? 0);
    const a = Math.sin(p), b = -a, c = Math.cos(p);
    const strain = o.strain ?? 0.6;
    d.Hips = A(0, 0.32, 1, Q(0, 0, a * 0.05));
    d.Spine = A(0, 0.12, 1); d.Spine1 = A(0, 0.1, 1); d.Spine2 = A(0, 0.1 + 0.05 * strain, 1);
    d.Neck = A(0, 0.75, 0.75 - 0.3 * strain);
    d.Head = A(0, 1, 0.25 - 0.25 * strain, Q(0, a * 0.06, 0));
    const sw = 0.32;
    d.LeftArm = A(0.2, -1, 0.15 + a * sw); d.LeftForeArm = A(0.06, -1, 0.2 + a * sw * 0.6); d.LeftHand = A(0.05, -0.15, 1);
    d.RightArm = A(-0.2, -1, 0.15 + b * sw); d.RightForeArm = A(-0.06, -1, 0.2 + b * sw * 0.6); d.RightHand = A(-0.05, -0.15, 1);
    d.LeftUpLeg = A(0.16, -1, -0.12 + b * 0.3); d.RightUpLeg = A(-0.16, -1, -0.12 + a * 0.3);
    d.LeftLeg = A(0.04, -0.12 - Math.max(0, b) * 0.2, -1); d.RightLeg = A(-0.04, -0.12 - Math.max(0, a) * 0.2, -1);
    d.LeftFoot = A(0, 0.25, -1); d.RightFoot = A(0, 0.25, -1);
    rig.applyDeltas(d, 'abs');
    groundRig(rig, 0.03 + Math.max(0, c) * 0.012);
  }
}

// ---------------------------------------------------------------- strongman
const MAN_NETS = {
  Hips: [1.15, 1.0, 1.2], Spine: [1.15, 1.0, 1.25], Spine1: [1.28, 1.0, 1.38], Spine2: [1.42, 1.02, 1.45],
  Neck: [1.7, 0.75, 1.7], Head: [1.0, 1.0, 1.0],
  LeftShoulder: [1.35, 1.15, 1.35], RightShoulder: [1.35, 1.15, 1.35],
  LeftArm: [1.75, 1.0, 1.75], RightArm: [1.75, 1.0, 1.75], LeftForeArm: [1.5, 1.0, 1.5], RightForeArm: [1.5, 1.0, 1.5],
  LeftHand: [1.25, 1.25, 1.25], RightHand: [1.25, 1.25, 1.25],
  LeftUpLeg: [1.5, 1.0, 1.5], RightUpLeg: [1.5, 1.0, 1.5], LeftLeg: [1.42, 1.0, 1.42], RightLeg: [1.42, 1.0, 1.42],
  LeftFoot: [1.15, 1.15, 1.15], RightFoot: [1.15, 1.15, 1.15],
};
export const MAN_SKIN = 0xc8805a;

export function makeStrongman({ half = false } = {}) {
  const rig = new Rig('man', MAN_SKIN, MH.man);
  const L = MH.man.landmarks, cutY = L.hipsY + 0.5 * (L.spineY - L.hipsY);
  rig.material.userData.u.uTatOn.value = 1;
  if (!half) {
    // crop registration (px in ref_face_strongman.png): eyes (102,187)/(200,192), 98 px apart
    const uu = rig.material.userData.u, S = 98 / (2 * L.eyeX);
    uu.uTatOn.value = 1; uu.uFaceOn.value = 1; uu.uFaceA.value.set(151, 189.5, S, L.eyeY); uu.uFaceSy.value = 116 / 0.09; uu.uFaceM.value.set(150, 238, 88, 150);
    rig.meshes[0].material[1].visible = false; // the crop provides the eyes
  }
  if (half) {
    // lower half only: shader discards everything above the waist cut, a flesh cap closes the cut
    const u = rig.material.userData.u; u.uCut = { value: cutY };
    const prev = rig.material.onBeforeCompile;
    rig.material.onBeforeCompile = sh => { prev(sh); sh.uniforms.uCut = u.uCut;
      sh.fragmentShader = sh.fragmentShader.replace('uniform float uHarness;', 'uniform float uHarness; uniform float uCut;')
        .replace('vec4 cs = charSurface(vBind);', 'if (vBind.y > uCut) discard; vec4 cs = charSurface(vBind);'); };
    rig.material.customProgramCacheKey = () => 'char-half';
    rig.material.side = THREE.DoubleSide;
    const cap = new THREE.Group();
    const flesh = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.03, 28), new THREE.MeshStandardMaterial({ color: 0xc94b50, roughness: 0.35 }));
    flesh.scale.set(1.0, 1, 0.72); cap.add(flesh);
    const inner = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.13, 0.05, 24), new THREE.MeshStandardMaterial({ color: 0xe8c7bc, roughness: 0.5 }));
    inner.scale.set(1, 1, 0.7); inner.position.y = 0.012; cap.add(inner);
    const bone = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.03, 0.12, 12), new THREE.MeshStandardMaterial({ color: 0xf3efe6, roughness: 0.4 }));
    bone.position.set(0, 0.05, -0.05); cap.add(bone);
    const goo = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), new THREE.MeshStandardMaterial({ color: 0x8a0d12, roughness: 0.2 }));
    goo.position.set(0.06, 0.02, 0.04); goo.scale.set(1.3, 0.5, 1); cap.add(goo);
    cap.traverse(o => { if (o.isMesh) o.castShadow = true; });
    rig.attach('Spine', cap, new THREE.Vector3(0, cutY, 0.0));
    rig.cap = cap;
  }
  rig.pose = (name, t, o = {}) => manPose(rig, name, t, o);
  return rig;
}

function capturePose(rig) { return { q: rig.boneList.map(b => b.quaternion.clone()), p: rig.boneList.map(b => b.position.clone()) }; }
function blendPose(rig, A0, B0, u) { rig.boneList.forEach((b, i) => { b.quaternion.slerpQuaternions(A0.q[i], B0.q[i], u); b.position.lerpVectors(A0.p[i], B0.p[i], u); }); }
function manPose(rig, name, t, o) {
  rig.resetBind();
  const d = {};
  if (name === 'idle') {
    rig.playClips([{ name: 'idle', time: t }]);
    d.LeftArm = Q(0, 0, 0.18); d.RightArm = Q(0, 0, -0.18);
  } else if (name === 'point') {
    rig.playClips([{ name: 'run', time: t * 0.7 }]);
    const r = o.reach ?? 1;
    d.Spine1 = Q(0.22 * r, 0.3 * r, 0);
    if (r > 0.02) { d.RightArm = A(-0.25 * r - 0.3 * (1 - r), 0.12 * r - 0.9 * (1 - r), 1 * r + 0.1); d.RightForeArm = A(-0.12 * r - 0.2 * (1 - r), 0.16 * r - 0.9 * (1 - r), 1 * r + 0.15); d.RightHand = A(-0.1, 0.12 * r - 0.9 * (1 - r), 1); }
  } else if (name === 'bend') {
    // hip hinge + knee bend, back rounded, arms hanging straight to the snakes on the ground
    const k = o.amount ?? 1;
    rig.playClips([{ name: 'idle', time: t }]);
    if (k < 0.999) { rig.applyDeltas({}, 'rel'); }
    const A0 = k < 0.999 ? capturePose(rig) : null;
    rig.resetBind(); rig.playClips([{ name: 'idle', time: t }]);
    const B = {
      Hips: A(0, 0.55, 0.85), Spine: A(0, 0.35, 1), Spine1: A(0, 0.22, 1), Spine2: A(0, 0.1, 1),
      Neck: A(0, 0.15, 1), Head: A(0, -0.25, 1),
      LeftShoulder: A(1, -0.25, 0.25), RightShoulder: A(-1, -0.25, 0.25),
      LeftArm: A(0.18, -1, 0.28), RightArm: A(-0.18, -1, 0.28), LeftForeArm: A(0.06, -1, 0.18), RightForeArm: A(-0.06, -1, 0.18),
      LeftHand: A(0.02, -1, 0.3), RightHand: A(-0.02, -1, 0.3),
      LeftUpLeg: A(0.14, -0.62, 0.78), RightUpLeg: A(-0.14, -0.62, 0.78), LeftLeg: A(0.05, -0.96, -0.28), RightLeg: A(-0.05, -0.96, -0.28),
      LeftFoot: A(0.05, -0.55, 0.85), RightFoot: A(-0.05, -0.55, 0.85),
    };
    rig.applyDeltas(B, 'abs');
    if (A0) { const B0 = capturePose(rig); blendPose(rig, A0, B0, k); }
    groundRig(rig, 0.0);
    return;
  } else if (name === 'pull') {
    rig.playClips([{ name: 'walk', time: t * (o.rate ?? 0.8) }]);
    const lean = o.lean ?? 0.25, g = o.grip ?? 1;
    d.Spine = Q(lean * 0.4, 0, 0); d.Spine1 = Q(lean * 0.3, 0, 0); d.Spine2 = Q(lean * 0.3, 0, 0);
    d.Neck = Q(-lean * 0.6, 0, 0); d.Head = Q(-lean * 0.3, o.lookY ?? 0, 0);
    if (g > 0.5) {
      const sw = Math.sin(t * (o.rate ?? 0.8) / 0.9667 * Math.PI * 2) * 0.08;
      d.LeftArm = A(0.32, -0.85, 0.42 + sw); d.RightArm = A(-0.32, -0.85, 0.42 - sw);
      d.LeftForeArm = A(0.12, -0.55, 0.85 + sw); d.RightForeArm = A(-0.12, -0.55, 0.85 - sw);
      d.LeftHand = A(0.05, -0.5, 0.85); d.RightHand = A(-0.05, -0.5, 0.85);
    }
  }
  rig.applyDeltas(d, 'rel');
  groundRig(rig, 0.0);
}

// ---------------------------------------------------------------- crowd baby (baked)
function babyColorJS(x, y, z) {
  const L = MH.baby.landmarks, H = L.height, ax = Math.abs(x);
  const arm = ax > L.shoulderX * 1.05 && y > L.chestY - 0.04 * H;
  const band = (v, a, b) => v >= a && v <= b, t = 0.022 * H;
  const wy = L.spineY + 0.35 * (L.chestY - L.spineY);
  if (!arm) {
    if (band(y, wy - t * 0.5, wy + t * 0.5) || band(y, L.chestY - t * 0.3, L.chestY + t * 0.7) || (band(ax, 0.38 * L.shoulderX, 0.38 * L.shoulderX + t) && band(y, wy, L.neckY))) return [0.86, 0.06, 0.04];
    if (band(y, L.legY - 0.28 * (L.legY - L.kneeY), L.hipsY + 0.55 * (L.spineY - L.hipsY))) return [0.94, 0.95, 0.98];
  }
  const c = new THREE.Color(BABY_SKIN); return [c.r, c.g, c.b];
}

export async function bakeCrowdBabies(phases = 4, targetVerts = 1100) {
  const rig = makeBaby();
  const surf = rig.meshes.find(m => m.name.includes('Surface')) || rig.meshes[0];
  const out = [];
  const simp = new SimplifyModifier();
  // simplify the bind geometry once (positions + bindPos via color channel trick)
  const base = surf.geometry.clone();
  base.deleteAttribute('uv'); base.deleteAttribute('normal');
  const merged = mergeVertices(base, 1e-4);
  const removeCount = Math.max(0, merged.attributes.position.count - targetVerts);
  // SimplifyModifier only keeps position/normal/uv/color/tangent; stash skin data so we can remap
  const simpIn = new THREE.BufferGeometry();
  simpIn.setAttribute('position', merged.attributes.position.clone());
  simpIn.setIndex(merged.index.clone());
  const simplified = await simp.modify(simpIn, removeCount);
  if (!simplified || !simplified.attributes || !simplified.attributes.position) throw new Error('simplify failed: ' + Object.keys(simplified || {}));
  // remap each simplified vertex to the nearest original vertex to fetch skin indices/weights
  const P = merged.attributes.position, S = simplified.attributes.position;
  const grid = new Map(), key = (x, y, z) => `${Math.floor(x * 50)},${Math.floor(y * 50)},${Math.floor(z * 50)}`;
  for (let i = 0; i < P.count; i++) { const k = key(P.getX(i), P.getY(i), P.getZ(i)); if (!grid.has(k)) grid.set(k, []); grid.get(k).push(i); }
  const near = new Int32Array(S.count);
  for (let i = 0; i < S.count; i++) {
    const x = S.getX(i), y = S.getY(i), z = S.getZ(i);
    let best = 0, bd = 1e9;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
      const k = `${Math.floor(x * 50) + dx},${Math.floor(y * 50) + dy},${Math.floor(z * 50) + dz}`;
      const l = grid.get(k); if (!l) continue;
      for (const j of l) { const dd = (P.getX(j) - x) ** 2 + (P.getY(j) - y) ** 2 + (P.getZ(j) - z) ** 2; if (dd < bd) { bd = dd; best = j; } }
    }
    near[i] = best;
  }
  const SI = merged.attributes.skinIndex, SW = merged.attributes.skinWeight;
  const proxy = new THREE.BufferGeometry();
  proxy.setAttribute('position', S.clone());
  const si = new THREE.Uint16BufferAttribute(S.count * 4, 4), sw = new THREE.Float32BufferAttribute(S.count * 4, 4);
  for (let i = 0; i < S.count; i++) { const j = near[i]; si.setXYZW(i, SI.getX(j), SI.getY(j), SI.getZ(j), SI.getW(j)); sw.setXYZW(i, SW.getX(j), SW.getY(j), SW.getZ(j), SW.getW(j)); }
  proxy.setAttribute('skinIndex', si); proxy.setAttribute('skinWeight', sw);
  proxy.setIndex(simplified.index ? simplified.index.clone() : null);
  const pm = new THREE.SkinnedMesh(proxy, new THREE.MeshBasicMaterial());
  pm.bind(surf.skeleton, surf.bindMatrix);
  surf.parent.add(pm);
  const colors = new Float32Array(S.count * 3);
  for (let i = 0; i < S.count; i++) colors.set(babyColorJS(S.getX(i), S.getY(i), S.getZ(i)), i * 3);
  const v = new THREE.Vector3();
  for (let k = 0; k < phases; k++) {
    rig.pose('crawl', k / phases / 1.6, { strain: 0.5, rate: 1.6 });
    rig.root.updateMatrixWorld(true);
    pm.skeleton.update();
    const pos = new Float32Array(S.count * 3);
    const toGroup = new THREE.Matrix4().copy(rig.group.matrixWorld).invert().multiply(pm.matrixWorld);
    for (let i = 0; i < S.count; i++) { pm.getVertexPosition(i, v); v.applyMatrix4(toGroup); pos.set([v.x, v.y, v.z], i * 3); }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    g.setIndex(proxy.index.clone());
    g.computeVertexNormals();
    out.push(g);
  }
  return out;
}
