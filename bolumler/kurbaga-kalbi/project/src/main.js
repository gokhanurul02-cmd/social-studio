// Entry: builds the world, exposes window.renderFrame(frame) for deterministic seek-driven export.
import * as THREE from 'three';
import { FPS, NFRAMES, DURATION, halton, clamp, smooth, range, easeInOutCubic, easeInCubic, easeOutCubic } from './util.js';
import { buildEnvironment } from './env.js';
import { loadRig, loadMakeHuman } from './characters.js';
import { World, TIMELINE, subtitleAt, SHOT_SAMPLES } from './shots.js';

const qs = new URLSearchParams(location.search);
const W = +(qs.get('w') || 1080), H = +(qs.get('h') || 1920);
const SAMPLES = +(qs.get('samples') || 8);
const SHUTTER = 0.5; // fraction of a frame interval the shutter is open

async function boot() {
  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance', alpha: false });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.localClippingEnabled = true; // per-baby mouth clipping planes
  renderer.autoClear = false; // accumulation passes must not clear; targets are cleared explicitly
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.style.width = '540px'; renderer.domElement.style.height = '960px';
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const env = buildEnvironment(renderer, scene);
  await loadRig(); await loadMakeHuman();
  const world = new World(scene, env); window.WORLD = world;
  const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 5000);

  const rtOpts = { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: true };
  const sampleRT = new THREE.WebGLRenderTarget(W, H, rtOpts);
  const accum = [new THREE.WebGLRenderTarget(W, H, { ...rtOpts, depthBuffer: false }), new THREE.WebGLRenderTarget(W, H, { ...rtOpts, depthBuffer: false })];

  const quadGeo = new THREE.BufferGeometry();
  quadGeo.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const VS = 'varying vec2 vUv; void main(){ vUv = position.xy*0.5+0.5; gl_Position = vec4(position.xy,0.,1.); }';
  const accMat = new THREE.ShaderMaterial({ uniforms: { tex: { value: null }, wgt: { value: 1 } }, vertexShader: VS,
    fragmentShader: 'uniform sampler2D tex; uniform float wgt; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(tex, vUv).rgb*wgt, 1.0); }',
    blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, depthTest: false, depthWrite: false });
  const accScene = new THREE.Scene(); const accQuad = new THREE.Mesh(quadGeo, accMat); accQuad.frustumCulled = false; accScene.add(accQuad);

  const finalMat = new THREE.ShaderMaterial({
    uniforms: { texA: { value: null }, texB: { value: null }, mode: { value: 0 }, prog: { value: 0 }, angles: { value: new Array(8).fill(0) },
      flipFrom: { value: 0 }, exposure: { value: 1 }, aspect: { value: W / H }, blurA: { value: 0 }, blurB: { value: 0 }, mixAB: { value: 0 } },
    vertexShader: VS,
    fragmentShader: /* glsl */`
      uniform sampler2D texA, texB; uniform float mode, prog, exposure, aspect, blurA, blurB, mixAB; uniform float angles[8];
      varying vec2 vUv;
      vec3 aces(vec3 x){ const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.,1.); }
      vec3 toSRGB(vec3 c){ return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4))-0.055, step(0.0031308, c)); }
      vec3 grade(vec3 c){ c *= exposure*0.8; c = aces(c*0.92); float l = dot(c, vec3(0.2126,0.7152,0.0722)); c = mix(vec3(l), c, 1.12); c.r = c.r + 0.012*(1.0-c.r)*step(0.002, l); c.g *= 0.955; return clamp(c,0.,1.); }
      vec3 zoomBlur(sampler2D t, vec2 uv, float s){
        if (s < 0.001) return texture2D(t, uv).rgb;
        vec3 acc = vec3(0.); vec2 c = vec2(0.5, 0.5);
        for (int i = 0; i < 24; i++){ float k = float(i)/23.0; acc += texture2D(t, c + (uv-c)*(1.0 - s*k)).rgb; }
        return acc/24.0;
      }
      // card rotating about its vertical centre axis, seen by a 45deg camera
      vec3 card(sampler2D t, vec2 uv, float ang){
        float th = tan(radians(45.0)); vec3 d = normalize(vec3((uv.x*2.-1.)*th*aspect, (uv.y*2.-1.)*th, -1.0));
        float D = 1.0; vec3 C = vec3(0.,0.,-D); vec3 n = vec3(sin(ang), 0., cos(ang)); vec3 ex = vec3(cos(ang), 0., -sin(ang));
        float tt = dot(C, n)/dot(d, n); if (tt <= 0.) return vec3(0.);
        vec3 p = d*tt - C; float lx = dot(p, ex)/(th*aspect*D), ly = p.y/(th*D);
        vec2 q = vec2(lx, ly)*0.5+0.5;
        if (q.x < 0. || q.x > 1. || q.y < 0. || q.y > 1.) return vec3(0.);
        return texture2D(t, q).rgb;
      }
      void main(){
        vec3 col;
        if (mode < 0.5) col = grade(texture2D(texA, vUv).rgb);
        else if (mode < 1.5) {
          vec3 acc = vec3(0.);
          for (int i = 0; i < 8; i++){ float a = angles[i];
            vec3 c = a >= 0.0 ? card(texA, vUv, a) : card(texB, vUv, -a - 0.01);
            acc += c; }
          col = grade(acc/8.0);
          // grade() applied to black outside the card keeps black
        } else {
          vec3 a = zoomBlur(texA, vUv, blurA), b = zoomBlur(texB, vUv, blurB);
          col = grade(mix(a, b, mixAB));
        }
        gl_FragColor = vec4(toSRGB(col), 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });
  const finalScene = new THREE.Scene(); const finalQuad = new THREE.Mesh(quadGeo, finalMat); finalQuad.frustumCulled = false; finalScene.add(finalQuad);

  // overlay canvas for subtitles
  const out = document.createElement('canvas'); out.width = W; out.height = H;
  const ctx = out.getContext('2d');
  const font = new FontFace('SubFont', 'url(/fonts/verdanab.ttf)'); await font.load(); document.fonts.add(font);
  // calibrate font size: reference ink width of "of the giant snakes" is ~1432px of 2160 (incl. outline)
  ctx.font = `100px SubFont`;
  const w100 = ctx.measureText('of the giant snakes').width;
  const FS = Math.round(100 * (1432 - 0.06 * 160) / w100 * (W / 2160) * 100) / 100;
  const BASE = 0.72 * H; // Turkish channel: baseline 0.72 (keeps clear of the bottom 20% UI zone)

  function drawSubtitle(text) {
    if (!text) return;
    ctx.font = `${FS}px SubFont`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.lineJoin = 'round';
    const x = W / 2, y = BASE, o = FS * 0.045;
    ctx.fillStyle = 'rgba(0,0,0,0.92)'; ctx.strokeStyle = 'rgba(0,0,0,0.92)'; ctx.lineWidth = FS * 0.07;
    ctx.save(); ctx.filter = `blur(${(FS * 0.012).toFixed(1)}px)`;
    ctx.strokeText(text, x + o, y + o); ctx.fillText(text, x + o, y + o); ctx.restore();
    ctx.strokeStyle = '#000'; ctx.lineWidth = FS * 0.06; ctx.strokeText(text, x, y);
    ctx.fillStyle = '#fff'; ctx.fillText(text, x, y);
  }

  const lensDir = new THREE.Vector3(), right = new THREE.Vector3(), up = new THREE.Vector3(), fwd = new THREE.Vector3();
  function setCamera(st, sampleIdx) {
    camera.fov = st.fov; camera.aspect = W / H; camera.near = st.near ?? 0.05; camera.far = st.far ?? 5000; camera.updateProjectionMatrix();
    camera.position.copy(st.pos); camera.up.set(0, 1, 0); camera.lookAt(st.target);
    if (st.roll) camera.rotateZ(st.roll);
    // thin-lens depth of field: move the eye on the aperture disc while keeping the focus plane fixed
    if (st.aperture > 0 && st.focus) {
      fwd.set(0, 0, -1).applyQuaternion(camera.quaternion); right.set(1, 0, 0).applyQuaternion(camera.quaternion); up.set(0, 1, 0).applyQuaternion(camera.quaternion);
      const r = Math.sqrt(halton(sampleIdx + 1, 5)) * st.aperture, a = halton(sampleIdx + 1, 7) * Math.PI * 2;
      const focusPt = camera.position.clone().addScaledVector(fwd, st.focus);
      camera.position.addScaledVector(right, Math.cos(a) * r).addScaledVector(up, Math.sin(a) * r);
      camera.up.copy(up); camera.lookAt(focusPt);
      if (st.roll) {} // roll already baked into up vector
    }
    camera.updateMatrixWorld(true);
    // sub-pixel jitter for anti-aliasing
    const jx = (halton(sampleIdx + 1, 2) - 0.5) * 2 / W, jy = (halton(sampleIdx + 1, 3) - 0.5) * 2 / H;
    camera.projectionMatrix.elements[8] += jx; camera.projectionMatrix.elements[9] += jy;
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
  }

  // render shot `id` at time t into accumulation target `slot`, motion-blurred over the shutter interval
  function renderShot(id, t, slot, n = SAMPLES) {
    renderer.setRenderTarget(accum[slot]); renderer.setClearColor(0x000000, 1); renderer.clear(true, false, false);
    let exposure = 1;
    for (let i = 0; i < n; i++) {
      const ts = t + ((i + 0.5) / n - 0.5) * SHUTTER / FPS;
      world.sampleIdx = i; const st = world.apply(id, ts);
      exposure = st.exposure;
      env.sky.position.copy(st.pos);
      setCamera(st, i);
      renderer.setRenderTarget(sampleRT); renderer.setClearColor(0x000000, 1); renderer.clear();
      renderer.render(scene, camera);
      accMat.uniforms.tex.value = sampleRT.texture; accMat.uniforms.wgt.value = 1 / n;
      renderer.setRenderTarget(accum[slot]); renderer.render(accScene, fsCam);
    }
    return exposure;
  }

  function shotAt(t) { return TIMELINE.shots.find(s => t >= s.a && t < s.b) || TIMELINE.shots[TIMELINE.shots.length - 1]; }

  function renderTime(t) {
    const flip = TIMELINE.flips.find(f => t >= f.a && t < f.b);
    const wh = TIMELINE.whoosh.find(f => t >= f.a && t < f.b);
    const U = finalMat.uniforms;
    if (flip) {
      const mid = flip.mid;
      // which sources are needed during this frame's shutter
      const angs = [];
      for (let i = 0; i < 8; i++) {
        const ts = t + ((i + 0.5) / 8 - 0.5) * SHUTTER / FPS;
        if (ts < mid) angs.push(Math.PI / 2 * Math.pow(range(ts, flip.a, mid), 1.25));
        else angs.push(-(Math.PI / 2 * (1 - easeOutCubic(range(ts, mid, flip.b)))) - 0.01);
      }
      U.exposure.value = renderShot(flip.from, Math.min(t, mid), 0, Math.max(2, SAMPLES >> 1));
      renderShot(flip.to, Math.max(t, mid), 1, Math.max(2, SAMPLES >> 1));
      U.texA.value = accum[0].texture; U.texB.value = accum[1].texture; U.mode.value = 1; U.angles.value = angs;
    } else if (wh) {
      const u = range(t, wh.a, wh.b);
      U.exposure.value = renderShot(wh.from, t, 0, SAMPLES);
      renderShot(wh.to, t, 1, SAMPLES);
      U.texA.value = accum[0].texture; U.texB.value = accum[1].texture; U.mode.value = 2;
      U.blurA.value = 0.55 * easeInCubic(range(u, 0.0, 0.45));
      U.blurB.value = 0.5 * (1 - easeOutCubic(range(u, 0.25, 1.0)));
      U.mixAB.value = smooth(range(u, 0.22, 0.45));
    } else {
      const s = shotAt(t);
      U.exposure.value = renderShot(s.id, t, 0, Math.round(SAMPLES * (SHOT_SAMPLES[s.id] || 1)));
      U.texA.value = accum[0].texture; U.mode.value = 0;
    }
    renderer.setRenderTarget(null); renderer.render(finalScene, fsCam);
  }

  window.renderFrame = (frame, quality = 0.95) => {
    const t = frame / FPS;
    renderTime(t);
    ctx.clearRect(0, 0, W, H);
    ctx.drawImage(renderer.domElement, 0, 0);
    drawSubtitle(subtitleAt(frame));
    return out.toDataURL('image/jpeg', quality);
  };
  window.seek = window.renderFrame;
  window.renderShotDebug = (t) => { finalMat.uniforms.exposure.value = renderShot("debug", t, 0, 2); finalMat.uniforms.texA.value = accum[0].texture; finalMat.uniforms.mode.value = 0; renderer.setRenderTarget(null); renderer.render(finalScene, fsCam); ctx.clearRect(0,0,W,H); ctx.drawImage(renderer.domElement,0,0); return out.toDataURL("image/jpeg",0.9); };
  const gl = renderer.getContext(), dbg = gl.getExtension('WEBGL_debug_renderer_info');
  window.INFO = { W, H, SAMPLES, FS, revision: THREE.REVISION, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '?', frames: Math.ceil(TIMELINE.duration * FPS), fps: FPS, duration: TIMELINE.duration };
  window.TL = { shots: TIMELINE.shots, whoosh: TIMELINE.whoosh, flips: TIMELINE.flips, duration: TIMELINE.duration };
  window.READY = true;
}
boot().catch(e => { console.error('[cy] boot failed', e.stack || e); window.FAILED = String(e.stack || e); });
