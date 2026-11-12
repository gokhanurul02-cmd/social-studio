// Athletics track + grass ground (Zack D. style: blue track, white lane lines, saturated green grass).
import * as THREE from 'three';
import { BUMP_GLSL } from './mosquito.js';

export function makeTrackGround() {
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, metalness: 0 });
  mat.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvW = (modelMatrix*vec4(transformed,1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vW;\n' + BUMP_GLSL + `
      float lineAA(float d, float w){ float fw = fwidth(d); return clamp((w*0.5 - abs(d))/max(fw,1e-5) + 0.5, 0.0, 1.0); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float z = vW.z, x = vW.x;
        float zA = -5.2, zB = 2.4;                      // track band (lanes run along X)
        float onTrack = smoothstep(zA - 0.02, zA + 0.02, z) * (1.0 - smoothstep(zB - 0.02, zB + 0.02, z));
        float rub = vnoise3(vec3(vW.xz * 90.0, 0.0)) * 0.5 + vnoise3(vec3(vW.xz * 23.0, 3.0)) * 0.5;
        vec3 track = vec3(0.10, 0.30, 0.78) * (0.88 + 0.22 * rub) * (0.94 + 0.12 * vnoise3(vec3(vW.xz*0.8, 1.0)));
        float lane = 0.0; for (int i = 0; i <= 6; i++) lane = max(lane, lineAA(z - (zA + float(i) * 1.266), 0.05));
        track = mix(track, vec3(0.93, 0.95, 0.97), lane * 0.95);
        float blade = vnoise3(vec3(vW.xz * vec2(160.0, 40.0), 0.0));
        float clump = vnoise3(vec3(vW.xz * 2.0, 5.0)) * 0.6 + vnoise3(vec3(vW.xz * 9.0, 7.0)) * 0.4;
        vec3 grass = mix(vec3(0.17, 0.42, 0.05), vec3(0.33, 0.62, 0.10), clump) * (0.8 + 0.35 * blade);
        // mowing stripes
        grass *= 0.93 + 0.08 * step(0.5, fract(x * 0.12));
        diffuseColor.rgb = mix(grass, track, onTrack);
        float _H = mix(blade * 0.0015, rub * 0.0006, onTrack);`)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nnormal = bumpN(-vViewPosition, normal, _H, faceDirection);')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(0.95, 0.82, onTrack);');
  };
  const m = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), mat);
  m.rotation.x = -Math.PI / 2; m.receiveShadow = true;
  return m;
}

// distant stadium fence / stands strip (soft, low detail; seen out of focus)
export function makeStadium() {
  const g = new THREE.Group();
  const rail = new THREE.MeshStandardMaterial({ color: 0xc9d3dc, roughness: 0.35, metalness: 0.6 });
  const wall = new THREE.MeshStandardMaterial({ color: 0x1d3a2a, roughness: 0.8 });
  const w = new THREE.Mesh(new THREE.BoxGeometry(400, 1.1, 0.3), wall); w.position.set(0, 0.55, -12); w.castShadow = true; g.add(w);
  for (let i = -80; i <= 80; i++) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.1, 10), rail); p.position.set(i * 2.5, 0.55, -6.2); p.castShadow = true; g.add(p); }
  for (const y of [0.55, 1.08]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 400, 10), rail); r.rotation.z = Math.PI / 2; r.position.set(0, y, -6.2); g.add(r); }
  const stands = new THREE.MeshStandardMaterial({ color: 0x2c5fa8, roughness: 0.7 });
  for (let k = 0; k < 8; k++) { const s = new THREE.Mesh(new THREE.BoxGeometry(400, 0.5, 0.8), stands); s.position.set(0, 1.4 + k * 0.5, -13 - k * 0.8); g.add(s); }
  return g;
}
