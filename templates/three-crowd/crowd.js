// Reusable crowd toolkit for deterministic Three.js renders (r160+; tested with r187).
//
//   loadCharacter(url, entry)      -> CharacterTemplate (normalised: feet on y=0, faces +Z, size from catalog)
//   new Actor(template, opts)      -> hero character: SkeletonUtils.clone + AnimationMixer, actor.seek(t) is
//                                     a pure function of t (AnimationMixer.setTime), safe for frame-by-frame export
//   bakeVAT(template, clip, opts)  -> vertex animation texture (positions + normals for N frames of one clip)
//   new VATCrowd(vat, max, opts)   -> ONE InstancedMesh per material group, every instance has its own phase,
//                                     tint and transform; GPU interpolates the baked frames (continuous phase)
//
// No time source other than the t you pass in is used anywhere: renders are reproducible frame by frame.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const FORWARD_YAW = { '+z': 0, '-z': Math.PI, '+x': -Math.PI / 2, '-x': Math.PI / 2 };

// ---------------------------------------------------------------- proportion tweaks
// Post-animation bone offsets, applied after every mixer update (hero, bake and measuring alike):
//   { "Head": { "scale": [1, 0.8, 1] }, "Tail1": { "rot": [-0.6, 0, 0] } }   (rot = extra local XYZ Euler, radians)
// Lets one rig stand in for a related species (e.g. short muzzle + raised tail) without editing the file.
const _tq = new THREE.Quaternion(), _te = new THREE.Euler();
export function applyBoneTweaks(root, tweaks) {
  if (!tweaks) return;
  root.traverse(o => {
    const t = o.isBone && tweaks[o.name];
    if (!t) return;
    if (t.scale) o.scale.multiply(new THREE.Vector3(...t.scale));
    if (t.rot) o.quaternion.multiply(_tq.setFromEuler(_te.set(...t.rot)));
    if (t.pos) o.position.add(new THREE.Vector3(...t.pos));
  });
  root.updateMatrixWorld(true);
}
function snapshotBones(root) { const s = []; root.traverse(o => { if (o.isBone) s.push([o, o.position.clone(), o.quaternion.clone(), o.scale.clone()]); }); return s; }
function restoreBones(s) { for (const [o, p, q, sc] of s) { o.position.copy(p); o.quaternion.copy(q); o.scale.copy(sc); } }

// ---------------------------------------------------------------- clip lookup
export function findClip(clips, name) {
  if (!name) return clips[0] || null;
  const n = name.toLowerCase();
  const exact = clips.find(c => c.name.toLowerCase() === n);
  if (exact) return exact;
  const tail = clips.filter(c => c.name.toLowerCase().split('|').pop() === n);
  if (tail.length) return tail.sort((a, b) => a.name.length - b.name.length)[0];
  const part = clips.filter(c => c.name.toLowerCase().includes(n));
  return part.sort((a, b) => a.name.length - b.name.length)[0] || null;
}

// ---------------------------------------------------------------- loading + normalising
// entry: a catalog.json item (or a subset): { file, forward:'+z'|'-z'|'+x'|'-x', target:{height|length|width: metres},
//   rest_clip, materials:{ <name>: {tint:'replace'|'multiply'|'none', color, roughness, metalness} } }
// `url` is the URL the page can fetch (catalog paths are repo-relative; the harness maps /assets/).
export async function loadCharacter(url, entry = {}, loader = new GLTFLoader()) {
  const gltf = await loader.loadAsync(url);
  const inner = gltf.scene;
  inner.rotation.y = FORWARD_YAW[entry.forward || '+z'] ?? 0;
  const root = new THREE.Group(); root.name = entry.id || url; root.add(inner);
  root.traverse(o => {
    if (o.isMesh) {
      o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
      const conf = entry.materials?.[o.material.name];
      if (conf) {
        o.material = o.material.clone();
        if (conf.color !== undefined) o.material.color.set(conf.color);
        if (conf.roughness !== undefined) o.material.roughness = conf.roughness;
        if (conf.metalness !== undefined) o.material.metalness = conf.metalness;
      }
    }
  });
  // measure in the rest pose (first frame of rest_clip if given, else bind pose)
  const rest = findClip(gltf.animations, entry.rest_clip);
  if (rest && entry.rest_clip) { const m = new THREE.AnimationMixer(root); m.clipAction(rest).play(); m.setTime(0); }
  const bind = snapshotBones(root);
  applyBoneTweaks(root, entry.bone_tweaks);
  const box = measure(root);
  const size = box.getSize(new THREE.Vector3());
  const t = entry.target || {};
  let s = 1;
  if (t.height) s = t.height / size.y; else if (t.length) s = t.length / size.z; else if (t.width) s = t.width / size.x;
  inner.scale.multiplyScalar(s);
  const box2 = measure(root);
  const c = box2.getCenter(new THREE.Vector3());
  inner.position.x -= c.x; inner.position.z -= c.z; inner.position.y -= box2.min.y;
  root.updateMatrixWorld(true);
  const final = measure(root);
  restoreBones(bind); root.updateMatrixWorld(true);
  let tris = 0; root.traverse(o => { if (o.isMesh) tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; });
  return { root, clips: gltf.animations, entry, scale: s, box: final, size: final.getSize(new THREE.Vector3()), tris, gltf };
}

export function measure(root) {
  root.updateMatrixWorld(true);
  root.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
  return new THREE.Box3().setFromObject(root, true);
}

// Parent an extra object (prop, harness, replacement head, tow marker) to a bone of the template so it follows
// the animation in Actors AND gets baked into VATs. `object` is given in template space (normalised metres,
// feet on y=0, facing +Z) and keeps that placement in the template's bind/rest pose.
export function attachToBone(template, boneName, object) {
  let bone = null; template.root.traverse(o => { if (o.isBone && o.name === boneName && !bone) bone = o; });
  if (!bone) throw new Error(`attachToBone: bone ${boneName} not found`);
  template.root.updateMatrixWorld(true);
  template.root.add(object); object.updateMatrixWorld(true);
  bone.attach(object);
  object.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
  return object;
}
export function findBone(root, name) { let b = null; root.traverse(o => { if (!b && o.isBone && o.name === name) b = o; }); return b; }

// ---------------------------------------------------------------- hero actors
export class Actor {
  constructor(template, { clip = null, rate = 1, offset = 0 } = {}) {
    this.template = template;
    this.root = SkeletonUtils.clone(template.root);
    this.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
    this.mixer = new THREE.AnimationMixer(this.root);
    this.actions = new Map();
    this.rate = rate; this.offset = offset;
    this.tweaks = template.entry.bone_tweaks; this.bind = snapshotBones(this.root);
    if (clip) this.play(clip);
  }
  action(name) {
    if (!this.actions.has(name)) {
      const c = findClip(this.template.clips, name);
      if (!c) throw new Error(`clip "${name}" not in ${this.template.entry.id}: ${this.template.clips.map(c => c.name).join(', ')}`);
      this.actions.set(name, this.mixer.clipAction(c));
    }
    return this.actions.get(name);
  }
  // single clip at full weight
  play(name) { this.mix([[name, 1]]); return this; }
  // weighted blend, e.g. [['Walk', 0.7], ['Run', 0.3]]; all clips share the actor's clock
  mix(list) {
    for (const a of this.actions.values()) { a.enabled = false; a.stop(); }
    for (const [name, w] of list) { const a = this.action(name); a.reset(); a.enabled = true; a.setEffectiveWeight(w); a.play(); }
    return this;
  }
  // deterministic: same t -> same pose, independent of call order
  seek(t) {
    restoreBones(this.bind);
    this.mixer.setTime(this.offset + t * this.rate);
    applyBoneTweaks(this.root, this.tweaks);
    this.root.updateMatrixWorld(true); return this;
  }
}

// ---------------------------------------------------------------- vertex animation textures
// Bakes `clip` of `template` into float textures. Layout: vertex i of frame f lives at
// (i % W, floor(i / W) + f * rows). Normals are recomputed per frame from the skinned positions.
export function bakeVAT(template, clipName, { frames = 32, width = 1024 } = {}) {
  const clip = findClip(template.clips, clipName);
  if (!clip) throw new Error(`bakeVAT: clip ${clipName} missing`);
  const root = SkeletonUtils.clone(template.root);
  const mixer = new THREE.AnimationMixer(root);
  mixer.clipAction(clip).play();
  const bind = snapshotBones(root);
  const meshes = []; root.traverse(o => { if (o.isMesh) meshes.push(o); });
  root.updateMatrixWorld(true);
  // merged static geometry (index, uv, groups per source mesh)
  let nv = 0; const offs = [];
  for (const m of meshes) { offs.push(nv); nv += m.geometry.attributes.position.count; }
  const index = [], uv = new Float32Array(nv * 2), groups = [], materials = [];
  const hasColor = meshes.some(m => m.geometry.attributes.color), col = hasColor ? new Float32Array(nv * 3).fill(1) : null;
  meshes.forEach((m, k) => {
    const g = m.geometry, start = index.length;
    const idx = g.index ? g.index.array : [...Array(g.attributes.position.count).keys()];
    for (let i = 0; i < idx.length; i++) index.push(idx[i] + offs[k]);
    if (col && g.attributes.color) for (let i = 0; i < g.attributes.color.count; i++) col.set([g.attributes.color.getX(i), g.attributes.color.getY(i), g.attributes.color.getZ(i)], (offs[k] + i) * 3);
    if (g.attributes.uv) for (let i = 0; i < g.attributes.uv.count; i++) { uv[(offs[k] + i) * 2] = g.attributes.uv.getX(i); uv[(offs[k] + i) * 2 + 1] = g.attributes.uv.getY(i); }
    let mi = materials.indexOf(m.material); if (mi < 0) { materials.push(m.material); mi = materials.length - 1; }
    groups.push({ start, count: idx.length, materialIndex: mi });
  });
  const rows = Math.ceil(nv / width), H = rows * frames;
  const pos = new Float32Array(width * H * 4), nrm = new Float32Array(width * H * 4);
  const tmpGeo = new THREE.BufferGeometry(); tmpGeo.setIndex(index);
  const p = new Float32Array(nv * 3); tmpGeo.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const v = new THREE.Vector3(), inv = new THREE.Matrix4().copy(root.matrixWorld).invert(), rel = new THREE.Matrix4();
  const box = new THREE.Box3();
  for (let f = 0; f < frames; f++) {
    restoreBones(bind);
    mixer.setTime(clip.duration * f / frames);
    applyBoneTweaks(root, template.entry.bone_tweaks);
    root.updateMatrixWorld(true);
    meshes.forEach((m, k) => {
      if (m.isSkinnedMesh) m.skeleton.update();
      rel.multiplyMatrices(inv, m.matrixWorld);
      for (let i = 0; i < m.geometry.attributes.position.count; i++) {
        m.getVertexPosition(i, v); v.applyMatrix4(rel);
        p.set([v.x, v.y, v.z], (offs[k] + i) * 3); box.expandByPoint(v);
      }
    });
    tmpGeo.attributes.position.needsUpdate = true; tmpGeo.computeVertexNormals();
    const n = tmpGeo.attributes.normal.array;
    for (let i = 0; i < nv; i++) {
      const o = ((f * rows + Math.floor(i / width)) * width + (i % width)) * 4;
      pos[o] = p[i * 3]; pos[o + 1] = p[i * 3 + 1]; pos[o + 2] = p[i * 3 + 2]; pos[o + 3] = 1;
      nrm[o] = n[i * 3]; nrm[o + 1] = n[i * 3 + 1]; nrm[o + 2] = n[i * 3 + 2]; nrm[o + 3] = 0;
    }
  }
  const tex = a => { const t = new THREE.DataTexture(a, width, H, THREE.RGBAFormat, THREE.FloatType); t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t; };
  const geometry = new THREE.BufferGeometry();
  geometry.setIndex(index);
  geometry.setAttribute('position', new THREE.BufferAttribute(p.slice(), 3)); // last frame, only for bounds/fallback
  geometry.setAttribute('normal', new THREE.BufferAttribute(tmpGeo.attributes.normal.array.slice(), 3));
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  if (col) geometry.setAttribute('color', new THREE.BufferAttribute(col, 3));
  for (const g of groups) geometry.addGroup(g.start, g.count, g.materialIndex);
  geometry.boundingSphere = box.getBoundingSphere(new THREE.Sphere());
  return { geometry, materials, posTex: tex(pos), nrmTex: tex(nrm), width, rows, frames, duration: clip.duration, clip: clip.name, vertexCount: nv, box };
}

const VAT_PARS = /* glsl */`
uniform sampler2D vatPos; uniform sampler2D vatNrm; uniform vec3 vatInfo; // width, rows, frames
attribute float aPhase;
vec3 vatFetch(sampler2D t, float fr){
  int W = int(vatInfo.x), R = int(vatInfo.y), F = int(vatInfo.z);
  int f = int(mod(fr, float(F)));
  int id = gl_VertexID;
  return texelFetch(t, ivec2(id % W, id / W + f * R), 0).xyz;
}
vec3 vatSample(sampler2D t){
  float fr = fract(aPhase) * vatInfo.z; float f0 = floor(fr);
  return mix(vatFetch(t, f0), vatFetch(t, f0 + 1.0), fr - f0);
}`;

function patchVAT(material, vat, tint) {
  const uniforms = { vatPos: { value: vat.posTex }, vatNrm: { value: vat.nrmTex }, vatInfo: { value: new THREE.Vector3(vat.width, vat.rows, vat.frames) }, vatTint: { value: tint } };
  material.userData.vat = uniforms;
  material.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\n' + VAT_PARS + '\nuniform float vatTint;')
      .replace('#include <beginnormal_vertex>', 'vec3 objectNormal = normalize(vatSample(vatNrm));\n#ifdef USE_TANGENT\nvec3 objectTangent = vec3( tangent.xyz );\n#endif')
      .replace('#include <begin_vertex>', 'vec3 transformed = vatSample(vatPos);')
      .replace('#include <color_vertex>', `
        #if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR )
          vColor = vec4( 1.0 );
        #endif
        #ifdef USE_COLOR
          vColor.rgb *= color;
        #endif
        #ifdef USE_INSTANCING_COLOR
          vColor.rgb *= mix( vec3( 1.0 ), instanceColor.rgb, vatTint );
        #endif`);
  };
  material.customProgramCacheKey = () => 'vat-' + vat.vertexCount + '-' + vat.frames;
  return material;
}

function depthVAT(vat) {
  const m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const uniforms = { vatPos: { value: vat.posTex }, vatNrm: { value: vat.nrmTex }, vatInfo: { value: new THREE.Vector3(vat.width, vat.rows, vat.frames) } };
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + VAT_PARS)
      .replace('#include <begin_vertex>', 'vec3 transformed = vatSample(vatPos);');
  };
  m.customProgramCacheKey = () => 'vatdepth-' + vat.vertexCount;
  return m;
}

// Instanced crowd driven by a baked VAT. API mirrors a simple immediate-mode list:
//   crowd.begin(); crowd.add(phase, pos, yaw, scale, color); ...; crowd.end();
// `phase` is in clip cycles (any real number; only the fractional part is used).
// materials: { <materialName>: { tint: 'replace'|'multiply'|'none', color, roughness } } — 'replace' sets the
// base colour to white so the instance colour becomes the coat colour; 'multiply' keeps the texture/colour.
export class VATCrowd {
  constructor(vat, max, { materials = {}, castShadow = true, receiveShadow = true, envMapIntensity = 1 } = {}) {
    this.vat = vat; this.max = max;
    const geo = vat.geometry.clone();
    this.phase = new THREE.InstancedBufferAttribute(new Float32Array(max), 1); this.phase.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aPhase', this.phase);
    const mats = vat.materials.map(src => {
      const conf = materials[src.name] || materials['*'] || { tint: 'none' };
      const m = src.clone();
      if (conf.color !== undefined) m.color.set(conf.color);
      if (conf.tint === 'replace') m.color.set(0xffffff);
      if (conf.roughness !== undefined) m.roughness = conf.roughness;
      if (conf.metalness !== undefined) m.metalness = conf.metalness;
      m.envMapIntensity = envMapIntensity;
      return patchVAT(m, vat, conf.tint && conf.tint !== 'none' ? 1 : 0);
    });
    this.mesh = new THREE.InstancedMesh(geo, mats, max);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.setColorAt(0, new THREE.Color(1, 1, 1));
    this.mesh.customDepthMaterial = depthVAT(vat);
    this.mesh.castShadow = castShadow; this.mesh.receiveShadow = receiveShadow; this.mesh.frustumCulled = false;
    this.n = 0; this._m = new THREE.Matrix4(); this._q = new THREE.Quaternion(); this._s = new THREE.Vector3(); this._c = new THREE.Color(); this._y = new THREE.Vector3(0, 1, 0);
  }
  begin() { this.n = 0; }
  add(phase, pos, yaw = 0, scale = 1, color = 0xffffff) {
    if (this.n >= this.max) return;
    const i = this.n++;
    this._q.setFromAxisAngle(this._y, yaw);
    this.mesh.setMatrixAt(i, this._m.compose(pos, this._q, this._s.setScalar(scale)));
    this.mesh.setColorAt(i, this._c.set(color));
    this.phase.array[i] = ((phase % 1) + 1) % 1;
  }
  end() {
    this.mesh.count = this.n;
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
    this.phase.needsUpdate = true;
  }
  set visible(v) { this.mesh.visible = v; }
  get visible() { return this.mesh.visible; }
}

// Cheap LOD for very distant instances: a 1-frame VAT (frozen first pose) — same VATCrowd API, ~1/32 the memory.
export function bakeStaticPose(template, clipName) { return bakeVAT(template, clipName, { frames: 1 }); }

// Load a catalog.json and resolve entries by id. `base` is the URL prefix that maps to the repo's assets/ folder.
export async function loadCatalog(url = '/assets/catalog.json') {
  const cat = await (await fetch(url)).json();
  const byId = Object.fromEntries(cat.assets.map(a => [a.id, a]));
  return { ...cat, byId, url: id => '/' + byId[id].file.replace(/^\/+/, '') };
}
