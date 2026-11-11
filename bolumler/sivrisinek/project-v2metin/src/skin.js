// Macro forearm: high-resolution skin cylinder with procedural PBR skin (micro-relief crease network,
// pores, mottling, faint veins, oily/rough variation, sheen for vellus fuzz, wrap/SSS tint) + instanced hairs.
// Units: millimetres. Arm axis = X, top of the skin at y = 0 (cylinder centre at y = -R).
import * as THREE from 'three';
import { BUMP_GLSL } from './mosquito.js';
import { mulberry } from './util.js';

export const ARM_R = 38;

export function makeSkinMaterial({ base = 0xd9a487, scale = 1 } = {}) {
  const mat = new THREE.MeshPhysicalMaterial({ color: base, roughness: 0.5, metalness: 0, sheen: 0.5, sheenRoughness: 0.6,
    sheenColor: new THREE.Color(0.9, 0.7, 0.6), clearcoat: 0.12, clearcoatRoughness: 0.45, specularIntensity: 0.55 });
  const u = { uScale: { value: scale } };
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvObj = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vObj; uniform float uScale;\n' + BUMP_GLSL + `
      float skinH(vec3 p, out float pore, out float crease){
        // rhombic crease network (~0.7 mm cells, stretched along the arm)
        vec3 q = p * vec3(1.25, 1.6, 1.6);
        vec2 v = voro3(q * 1.0);
        crease = 1.0 - smoothstep(0.0, 0.09, v.y - v.x);
        vec2 v2 = voro3(q * 2.7 + 13.1);
        float fine = 1.0 - smoothstep(0.0, 0.08, v2.y - v2.x);
        // pores at random cell centres
        vec2 pv = voro3(p * 2.2 + 7.0);
        pore = (1.0 - smoothstep(0.035, 0.075, pv.x)) * step(0.55, _h3(floor(p*2.2+7.0)).y);
        float n = vnoise3(p * 6.0) * 0.5 + vnoise3(p * 17.0) * 0.25;
        return -crease * 0.045 - fine * 0.015 - pore * 0.05 + n * 0.015 + vnoise3(p*0.6)*0.02;
      }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float _pore, _crease; float _H = skinH(vObj * uScale, _pore, _crease);
        float mott = vnoise3(vObj * uScale * 0.35) * 0.6 + vnoise3(vObj * uScale * 1.3) * 0.4;
        diffuseColor.rgb *= mix(vec3(1.0), vec3(1.03, 0.95, 0.93), smoothstep(0.4, 0.85, mott));   // redness blotches
        diffuseColor.rgb *= 1.0 - 0.10 * _crease - 0.18 * _pore;
        float fr = smoothstep(0.82, 0.9, vnoise3(vObj * uScale * 2.4 + 4.0));
        diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.78, 0.62, 0.52), fr * 0.5); // freckles
        float vein = 1.0 - smoothstep(0.0, 0.5, abs(vObj.z * uScale * 0.18 + 1.6 * sin(vObj.x * uScale * 0.07) - 0.5));
        diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.86, 0.9, 1.04), vein * 0.25);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        normal = bumpN(-vViewPosition, normal, _H / uScale, faceDirection);`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
        roughnessFactor = clamp(0.42 + 0.22 * _crease + 0.15 * vnoise3(vObj * uScale * 0.9) - 0.1 * smoothstep(0.5, 0.9, vnoise3(vObj*uScale*0.2)), 0.25, 0.85);`)
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
        // cheap subsurface: reddish wrap light in the terminator / shadowed areas
        reflectedLight.indirectDiffuse += reflectedLight.directDiffuse * vec3(0.22, 0.05, 0.02) + reflectedLight.indirectDiffuse * vec3(0.12, 0.02, 0.0);`);
  };
  mat.customProgramCacheKey = () => 'skin-' + scale;
  return mat;
}

export function makeForearm({ hairCount = 260, vellus = 1800, patch = 30 } = {}) {
  const g = new THREE.CylinderGeometry(ARM_R, ARM_R * 0.92, 260, 720, 220, true);
  g.rotateZ(Math.PI / 2); g.translate(0, -ARM_R, 0);
  const mesh = new THREE.Mesh(g, makeSkinMaterial());
  mesh.receiveShadow = true; mesh.castShadow = true;
  const group = new THREE.Group(); group.add(mesh);
  // hairs: forearm terminal hairs lie low, pointing towards the wrist (+X); emerge near the surface
  const rnd = mulberry(9);
  const mk = (n, lenA, lenB, r0, col, rough) => {
    const geo = new THREE.CylinderGeometry(r0 * 0.25, r0, 1, 5, 6, false); geo.translate(0, 0.5, 0);
    // bend each hair: curve along +x of its local frame
    const P = geo.attributes.position; for (let i = 0; i < P.count; i++) { const y = P.getY(i); P.setZ(i, P.getZ(i) + 0.35 * y * y); }
    geo.computeVertexNormals();
    const m = new THREE.InstancedMesh(geo, new THREE.MeshPhysicalMaterial({ color: col, roughness: rough, sheen: 0.6, sheenColor: new THREE.Color(0.6, 0.5, 0.4), clearcoat: 0.3 }), n);
    const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
    for (let i = 0; i < n; i++) {
      const x = (rnd() - 0.5) * patch * 2.2, a = (rnd() - 0.5) * (patch / ARM_R) * 1.6;
      const nrm = new THREE.Vector3(0, Math.cos(a), Math.sin(a));
      const p = new THREE.Vector3(x, -ARM_R, 0).addScaledVector(nrm, ARM_R - 0.02);
      // keep the landing spot clear-ish (mosquito sits at the origin)
      if (Math.abs(p.x) < 2.5 && Math.abs(p.z) < 2.0 && rnd() < 0.7) continue;
      const len = lenA + rnd() * (lenB - lenA);
      // direction: mostly along +x, lying at 12-30 deg from the skin
      const elev = (0.2 + rnd() * 0.32), yaw = (rnd() - 0.5) * 0.7;
      const tang = new THREE.Vector3(Math.cos(yaw), 0, Math.sin(yaw)).projectOnPlane(nrm).normalize();
      const dir = tang.clone().multiplyScalar(Math.cos(elev)).addScaledVector(nrm, Math.sin(elev)).normalize();
      q.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      // roll so the curve bends towards the skin
      const roll = new THREE.Quaternion().setFromAxisAngle(dir, rnd() * 0.6 - 0.3 + Math.PI);
      q.premultiply(roll);
      M.compose(p, q, new THREE.Vector3(1, len, 1)); m.setMatrixAt(i, M);
    }
    m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; return m;
  };
  group.add(mk(hairCount, 2.0, 4.5, 0.03, 0x4a3020, 0.4));   // terminal hairs (dark brown)
  group.add(mk(vellus, 0.6, 1.6, 0.012, 0xc7a184, 0.5));        // vellus fuzz (light)
  return { group, mesh };
}
