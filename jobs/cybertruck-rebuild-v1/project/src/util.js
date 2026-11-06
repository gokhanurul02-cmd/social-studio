import * as THREE from 'three';

export const FPS = 30000 / 1001;
export const NFRAMES = 664;
export const DURATION = 22.155467;

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
export const smoother = t => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
export const easeOutCubic = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeInCubic = t => Math.pow(clamp(t), 3);
export const easeInOutCubic = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOutExpo = t => { t = clamp(t); return t === 1 ? 1 : 1 - Math.pow(2, -9 * t); };
export const easeInOutSine = t => -(Math.cos(Math.PI * clamp(t)) - 1) / 2;
export const range = (t, a, b) => clamp((t - a) / (b - a));

export const EASE = { linear: t => clamp(t), smooth, smoother, outCubic: easeOutCubic, inCubic: easeInCubic,
  inOutCubic: easeInOutCubic, outExpo: easeOutExpo, inOutSine: easeInOutSine,
  outQuart: t => 1 - Math.pow(1 - clamp(t), 4), inOutQuart: t => { t = clamp(t); return t < .5 ? 8 * t ** 4 : 1 - Math.pow(-2 * t + 2, 4) / 2; } };

// Keyframe track: [{t, v:[...numbers], e:'easeName'}] — the ease of key i applies to segment i-1 -> i.
export function track(keys) {
  return t => {
    if (t <= keys[0].t) return keys[0].v.slice();
    for (let i = 1; i < keys.length; i++) {
      const k0 = keys[i - 1], k1 = keys[i];
      if (t <= k1.t) {
        const u = (EASE[k1.e || 'inOutCubic'])((t - k0.t) / (k1.t - k0.t));
        return k0.v.map((a, j) => lerp(a, k1.v[j], u));
      }
    }
    return keys[keys.length - 1].v.slice();
  };
}

export function mulberry(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

export function halton(i, b) { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; }

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(), _up = new THREE.Vector3(0, 1, 0), _d = new THREE.Vector3(), _mid = new THREE.Vector3();
// matrix for unit cylinder (height 1 along Y, centred) stretched between a and b with radius r
export function segmentMatrix(a, b, r, out = _m) {
  _d.subVectors(b, a); const len = _d.length();
  if (len < 1e-6) return out.makeScale(0, 0, 0);
  _d.divideScalar(len);
  _q.setFromUnitVectors(_up, _d);
  _mid.addVectors(a, b).multiplyScalar(.5);
  _s.set(r, len, r);
  return out.compose(_mid, _q, _s);
}

export function srgb(hex) { return new THREE.Color(hex); }
