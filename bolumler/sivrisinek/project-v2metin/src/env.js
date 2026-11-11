// Sky dome with procedural clouds, turquoise grid ground, sun + image-based lighting.
import * as THREE from 'three';

export const PALETTE = {
  zenith: 0x10a8f2, upper: 0x4cb8f2, horizon: 0xcbe5f6, haze: 0xdfe3f4,
  ground: 0x26b4f0, line: 0xf2fbff, centre: 0xffffff,
};

const NOISE = /* glsl */`
float h21(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
float vnoise(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),u.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),u.x), u.y); }
float fbm(vec2 p){ float a=.5, s=0.; mat2 r=mat2(.8,-.6,.6,.8); for(int i=0;i<6;i++){ s+=a*vnoise(p); p=r*p*2.03+11.7; a*=.5; } return s; }
`;

export function makeSkyMaterial({ forEnv = false } = {}) {
  return new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, depthTest: false, fog: false,
    uniforms: {
      zenith: { value: new THREE.Color(PALETTE.zenith) }, upper: { value: new THREE.Color(PALETTE.upper) },
      horizon: { value: new THREE.Color(PALETTE.horizon) }, haze: { value: new THREE.Color(PALETTE.haze) },
      groundCol: { value: new THREE.Color(PALETTE.ground) }, forEnv: { value: forEnv ? 1 : 0 },
      cloudShift: { value: new THREE.Vector2(3.7, 1.3) }, cloudAmount: { value: 1.0 },
      sunDir: { value: new THREE.Vector3(.55, .62, .55).normalize() },
    },
    vertexShader: /* glsl */`varying vec3 vDir; void main(){ vDir = normalize((modelMatrix*vec4(position,0.)).xyz);
      vec4 p = projectionMatrix*viewMatrix*vec4((modelMatrix*vec4(position,1.)).xyz,1.); gl_Position = p.xyww; }`,
    fragmentShader: /* glsl */`
      uniform vec3 zenith, upper, horizon, haze, groundCol, sunDir; uniform float forEnv, cloudAmount; uniform vec2 cloudShift;
      varying vec3 vDir;
      ${NOISE}
      void main(){
        vec3 d = normalize(vDir);
        float y = d.y;
        vec3 col;
        if (y < 0.0) {
          col = mix(horizon, groundCol*0.9, smoothstep(0.0, -0.08, y));
        } else {
          col = mix(horizon, upper, smoothstep(0.0, 0.07, y));
          col = mix(col, zenith, smoothstep(0.1, 0.6, y));
          col = mix(col, haze, (1.0-smoothstep(0.0, 0.025, y))*0.6);
          // clouds projected onto a high plane
          vec2 uv = d.xz/(y+0.12)*0.8 + cloudShift;
          float n = fbm(uv*0.9);
          float detail = fbm(uv*3.1+7.0);
          float c = smoothstep(0.53, 0.78, n + 0.2*(detail-0.5)) * cloudAmount;
          c *= smoothstep(0.004, 0.04, y);
          float shade = smoothstep(0.30, 0.85, detail*0.7 + n*0.5);
          vec3 cloudCol = mix(vec3(0.55,0.68,0.88), vec3(1.0,1.0,1.03), shade);
          cloudCol = mix(cloudCol, horizon*1.02, (1.0-smoothstep(0.0, 0.08, y))*0.6);
          col = mix(col, cloudCol, c*0.92);
          if (forEnv > 0.5) {
            float s = max(dot(d, sunDir), 0.0);
            col += vec3(1.0,0.95,0.88)*pow(s, 400.0)*40.0 + vec3(1.0,0.9,0.8)*pow(s,12.0)*0.6;
            // pink/magenta band that the chrome trucks pick up in the reference
            col = mix(col, vec3(0.95,0.55,0.95), smoothstep(0.0,0.1,y)*(1.0-smoothstep(0.12,0.4,y))*0.6);
          }
        }
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
}

export function makeGroundMaterial({ cell = 0.5, line = 0.028, centre = 0.16 } = {}) {
  const mat = new THREE.MeshStandardMaterial({ color: PALETTE.ground, roughness: 0.82, metalness: 0.0, envMapIntensity: 1.0 });
  mat.userData.uniforms = {
    gCell: { value: cell }, gLine: { value: line }, gCentre: { value: centre },
    gLineCol: { value: new THREE.Color(PALETTE.line) }, gCentreCol: { value: new THREE.Color(PALETTE.centre) },
    gCentreOn: { value: 1.0 }, gLineAlpha: { value: 0.92 }, gCentreX: { value: 0.0 }, gCrowd: { value: 0.0 },
  };
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, mat.userData.uniforms);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec2 vGP;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvGP = (modelMatrix*vec4(transformed,1.0)).xz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
      varying vec2 vGP; uniform float gCell, gLine, gCentre, gCentreOn, gLineAlpha, gCentreX, gCrowd; uniform vec3 gLineCol, gCentreCol;
      float lineCov(float x, float w, float fw, float period){
        float d = abs(fract(x/period+0.5)-0.5)*period;
        float c = clamp((w*0.5-d)/max(fw,1e-5)+0.5, 0.0, 1.0);
        return mix(c, w/period, smoothstep(w*0.6, period*0.45, fw));
      }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
      {
        vec2 fw = fwidth(vGP);
        float lx = lineCov(vGP.x, gLine, fw.x, gCell);
        float lz = lineCov(vGP.y, gLine, fw.y, gCell);
        float l = max(lx, lz) * gLineAlpha;
        float cx = vGP.x - gCentreX;
        float cc = clamp((gCentre*0.5-abs(cx))/max(fw.x,1e-5)+0.5,0.0,1.0) * gCentreOn;
        diffuseColor.rgb = mix(diffuseColor.rgb, gLineCol, l);
        diffuseColor.rgb = mix(diffuseColor.rgb, gCentreCol, cc);
        if (gCrowd > 0.5) { // contact shadowing under the dense baby crowd (5000 small occluders)
          float hw = 1.9 + (vGP.y - 1.45)*0.21;
          float inside = smoothstep(1.0, 1.6, vGP.y) * (1.0 - smoothstep(hw - 0.2, hw + 0.4, abs(vGP.x)));
          diffuseColor.rgb *= mix(vec3(1.0), vec3(0.32, 0.36, 0.78), inside);
        }
      }`);
  };
  return mat;
}

export function buildEnvironment(renderer, scene) {
  const sky = new THREE.Mesh(new THREE.SphereGeometry(4000, 64, 32), makeSkyMaterial());
  sky.renderOrder = -10; sky.frustumCulled = false;
  scene.add(sky);

  const groundMat = makeGroundMaterial();
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000, 1, 1), groundMat);
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
  scene.add(ground);

  scene.fog = new THREE.Fog(PALETTE.horizon, 260, 1800);

  // image based lighting: sky + plain ground rendered into a PMREM
  const envScene = new THREE.Scene();
  envScene.add(new THREE.Mesh(new THREE.SphereGeometry(500, 64, 32), makeSkyMaterial({ forEnv: true })));
  const eg = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), new THREE.MeshBasicMaterial({ color: 0x7fd3f2 }));
  eg.rotation.x = -Math.PI / 2; eg.position.y = -1.0; envScene.add(eg);
  // a few soft white "grid glow" stripes on the env ground so lower panels pick up lines
  for (let i = -6; i <= 6; i++) {
    const s = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 4000), new THREE.MeshBasicMaterial({ color: 0xbfefff }));
    s.rotation.x = -Math.PI / 2; s.position.set(i * 6, -0.99, 0); envScene.add(s);
  }
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(envScene, 0, 0.1, 2000);
  scene.environment = envRT.texture;
  scene.environmentIntensity = 1.0;

  const sun = new THREE.DirectionalLight(0xfff4e6, 2.6);
  sun.position.set(30, 42, 26); sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  const sc = sun.shadow.camera; sc.near = 1; sc.far = 200; sc.left = -12; sc.right = 12; sc.top = 12; sc.bottom = -12;
  scene.add(sun); scene.add(sun.target);

  const hemi = new THREE.HemisphereLight(0x9ad8ff, 0x1a8fc4, 0.35);
  scene.add(hemi);

  const sunOffset = new THREE.Vector3(30, 42, 26);
  function setShadowArea(center, size) {
    sun.target.position.copy(center);
    sun.position.copy(center).add(sunOffset);
    sc.left = -size; sc.right = size; sc.top = size; sc.bottom = -size; sc.far = 140 + size * 2;
    sc.updateProjectionMatrix();
  }
  return { sky, ground, groundMat, sun, hemi, setShadowArea };
}
