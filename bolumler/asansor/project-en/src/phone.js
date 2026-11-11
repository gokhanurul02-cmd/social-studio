// Generic smartphone (no brand / logo): rounded aluminium frame, glass back, punch-hole camera, emissive screen
// drawn on a canvas. Screen states: chat with "Anne" (typing progress, sent bubble) and lock screen with missed calls.
// Local frame: screen faces +Z, long axis +Y, centre at the origin. Size 0.072 x 0.152 x 0.008 m.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { canvasTex } from './mats.js';

const PW = 0.0715, PH = 0.152, PD = 0.0082;
const SW = 720, SH = 1530;
const FONT = '"Segoe UI", "Helvetica Neue", Arial, sans-serif';

function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function heart(g, x, y, s) { g.beginPath(); g.moveTo(x, y + s * 0.3); g.bezierCurveTo(x, y, x - s * 0.5, y, x - s * 0.5, y + s * 0.3); g.bezierCurveTo(x - s * 0.5, y + s * 0.6, x, y + s * 0.8, x, y + s); g.bezierCurveTo(x, y + s * 0.8, x + s * 0.5, y + s * 0.6, x + s * 0.5, y + s * 0.3); g.bezierCurveTo(x + s * 0.5, y, x, y, x, y + s * 0.3); g.fill(); }
function statusBar(g, time, dark = false) {
  g.fillStyle = dark ? '#fff' : '#111'; g.font = `600 34px ${FONT}`; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(time, 54, 48);
  g.textAlign = 'right'; g.fillRect(SW - 110, 36, 54, 24); g.fillRect(SW - 54, 42, 5, 12);
  for (let i = 0; i < 4; i++) g.fillRect(SW - 200 + i * 14, 58 - i * 7 - 8, 9, 8 + i * 7);
}
// chat screen: typed 0..1 of the message, sent 0..1 (bubble pops in), keyboard visible while typing
export function drawChat(g, typed, sent) {
  const msg = 'mom I love you';
  g.fillStyle = '#ece5dd'; g.fillRect(0, 0, SW, SH);
  // subtle wallpaper dots
  g.fillStyle = 'rgba(0,0,0,0.035)'; for (let y = 140; y < SH; y += 46) for (let x = (y / 46) % 2 ? 20 : 43; x < SW; x += 46) { g.beginPath(); g.arc(x, y, 5, 0, 7); g.fill(); }
  // header
  g.fillStyle = '#1f6f5c'; g.fillRect(0, 0, SW, 210); statusBar(g, '9:47', true);
  g.fillStyle = '#fff'; g.font = `600 52px ${FONT}`; g.textAlign = 'left'; g.fillText('‹', 26, 146);
  g.fillStyle = '#d7b19a'; g.beginPath(); g.arc(120, 146, 42, 0, 7); g.fill();
  g.fillStyle = '#fff'; g.font = `700 40px ${FONT}`; g.textAlign = 'center'; g.fillText('M', 120, 148);
  g.textAlign = 'left'; g.font = `700 42px ${FONT}`; g.fillText('Mom', 182, 128); g.font = `400 28px ${FONT}`; g.fillStyle = 'rgba(255,255,255,0.8)'; g.fillText('online', 182, 170);
  // earlier messages
  const bubble = (txt, right, y, time) => {
    g.font = `400 36px ${FONT}`; const w = Math.min(520, g.measureText(txt).width + 150), x = right ? SW - 30 - w : 30;
    g.fillStyle = right ? '#d9fdd3' : '#ffffff'; g.shadowColor = 'rgba(0,0,0,0.12)'; g.shadowBlur = 4; g.shadowOffsetY = 2; rr(g, x, y, w, 78, 22); g.fill(); g.shadowColor = 'transparent';
    g.fillStyle = '#111'; g.textAlign = 'left'; g.fillText(txt, x + 24, y + 40);
    g.fillStyle = '#7b8a85'; g.font = `400 22px ${FONT}`; g.textAlign = 'right'; g.fillText(time, x + w - (right ? 52 : 18), y + 58);
    if (right) { g.strokeStyle = '#34b7f1'; g.lineWidth = 3.5; for (const dx of [0, 10]) { g.beginPath(); g.moveTo(x + w - 46 + dx, y + 52); g.lineTo(x + w - 40 + dx, y + 58); g.lineTo(x + w - 28 + dx, y + 46); g.stroke(); } }
    return x + w;
  };
  bubble('Coming home soon?', false, 300, '9:31');
  bubble('In the elevator, omw', true, 400, '9:44');
  const kb = typed > 0 && sent < 0.5;
  const inputY = kb ? SH - 560 - 100 : SH - 120;
  if (sent > 0) {
    const s = Math.min(1, sent * 1.6), y = 510 + (1 - s) * 40;
    g.save(); g.globalAlpha = Math.min(1, sent * 3); const xe = bubble(msg + '     ', true, y, '9:47'); g.fillStyle = '#e53935'; heart(g, xe - 104, y + 22, 30); g.restore();
  }
  // input bar
  g.fillStyle = '#fff'; rr(g, 20, inputY, SW - 150, 86, 43); g.fill();
  g.fillStyle = '#1f6f5c'; g.beginPath(); g.arc(SW - 66, inputY + 43, 43, 0, 7); g.fill();
  g.fillStyle = '#fff'; g.beginPath(); g.moveTo(SW - 84, inputY + 24); g.lineTo(SW - 44, inputY + 43); g.lineTo(SW - 84, inputY + 62); g.lineTo(SW - 78, inputY + 43); g.closePath(); g.fill();
  const shown = sent > 0.5 ? '' : msg.slice(0, Math.round(msg.length * Math.min(1, typed)));
  g.fillStyle = shown ? '#111' : '#9aa'; g.font = `400 36px ${FONT}`; g.textAlign = 'left'; g.fillText(shown || 'Message', 56, inputY + 45);
  if (shown && sent < 0.5) { const w = g.measureText(shown).width; g.fillStyle = '#1f6f5c'; g.fillRect(58 + w, inputY + 22, 4, 44); }
  if (kb) {
    g.fillStyle = '#d1d4d9'; g.fillRect(0, SH - 560, SW, 560);
    const rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'];
    const last = msg[Math.max(0, Math.round(msg.length * typed) - 1)];
    rows.forEach((r, ri) => {
      const kw = 62, gap = 8, tot = r.length * (kw + gap), x0 = (SW - tot) / 2;
      r.split('').forEach((ch, ci) => {
        const x = x0 + ci * (kw + gap), y = SH - 530 + ri * 112, hot = ch === (last || '').toLowerCase();
        g.fillStyle = hot ? '#9aa3ad' : '#fff'; g.shadowColor = 'rgba(0,0,0,0.25)'; g.shadowOffsetY = 2; rr(g, x, y, kw, 92, 10); g.fill(); g.shadowColor = 'transparent';
        g.fillStyle = '#111'; g.font = `400 38px ${FONT}`; g.textAlign = 'center'; g.fillText(ch, x + kw / 2, y + 48);
      });
    });
    g.fillStyle = '#fff'; rr(g, 160, SH - 190, 400, 92, 10); g.fill(); g.fillStyle = '#555'; g.font = `400 30px ${FONT}`; g.textAlign = 'center'; g.fillText('space', 360, SH - 142);
  }
}
// lock screen with missed calls
export function drawCalls(g, k) {
  const gr = g.createLinearGradient(0, 0, 0, SH); gr.addColorStop(0, '#1b2a4a'); gr.addColorStop(1, '#4a2f5e'); g.fillStyle = gr; g.fillRect(0, 0, SW, SH);
  statusBar(g, '10:05', true);
  g.fillStyle = '#fff'; g.textAlign = 'center'; g.font = `200 200px ${FONT}`; g.fillText('10:05', SW / 2, 330);
  g.font = `400 36px ${FONT}`; g.fillText('Tuesday, November 11', SW / 2, 450);
  const y = 620;
  g.fillStyle = 'rgba(255,255,255,0.88)'; rr(g, 34, y, SW - 68, 230, 40); g.fill();
  g.fillStyle = '#e53935'; g.beginPath(); g.arc(110, y + 80, 40, 0, 7); g.fill();
  // handset glyph
  g.save(); g.translate(110, y + 80); g.rotate(-0.6); g.fillStyle = '#fff'; rr(g, -22, -8, 44, 16, 8); g.fill(); g.fillRect(-24, -8, 10, 20); g.fillRect(14, -8, 10, 20); g.restore();
  g.fillStyle = '#111'; g.textAlign = 'left'; g.font = `700 40px ${FONT}`; g.fillText('Mom', 172, y + 66);
  g.fillStyle = '#d32f2f'; g.font = `700 46px ${FONT}`; g.fillText(`${Math.max(1, Math.round(37 * k))} missed calls`, 172, y + 126);
  g.fillStyle = '#555'; g.font = `400 28px ${FONT}`; g.fillText('now', 172, y + 178);
  g.textAlign = 'right'; g.fillStyle = '#777'; g.fillText('phone', SW - 70, y + 66);
  g.fillStyle = 'rgba(255,255,255,0.6)'; g.textAlign = 'center'; g.font = `400 30px ${FONT}`; g.fillText('Swipe up to open', SW / 2, SH - 90);
}

export function buildPhone() {
  const group = new THREE.Group();
  const frameMat = new THREE.MeshPhysicalMaterial({ color: 0x4a4d52, metalness: 1, roughness: 0.28, clearcoat: 0.3 });
  const body = new THREE.Mesh(new RoundedBoxGeometry(PW, PH, PD, 6, 0.0085), frameMat); body.castShadow = true; group.add(body);
  const back = new THREE.Mesh(new RoundedBoxGeometry(PW - 0.002, PH - 0.002, 0.001, 4, 0.008), new THREE.MeshPhysicalMaterial({ color: 0x20304a, roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.05 }));
  back.position.z = -PD / 2 - 0.0002; group.add(back);
  const cam = new THREE.Mesh(new RoundedBoxGeometry(0.028, 0.028, 0.002, 3, 0.006), new THREE.MeshPhysicalMaterial({ color: 0x181a1d, roughness: 0.2, clearcoat: 1 })); cam.position.set(-0.015, 0.055, -PD / 2 - 0.0012); group.add(cam);
  for (const [x, y] of [[-0.021, 0.061], [-0.009, 0.049]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.0045, 0.0045, 0.0015, 24).rotateX(Math.PI / 2), new THREE.MeshPhysicalMaterial({ color: 0x050505, roughness: 0.05, clearcoat: 1 })); l.position.set(x, y, -PD / 2 - 0.0025); group.add(l); }
  // black bezel glass + screen
  const glass = new THREE.Mesh(new RoundedBoxGeometry(PW - 0.0012, PH - 0.0012, 0.0008, 4, 0.0082), new THREE.MeshPhysicalMaterial({ color: 0x020202, roughness: 0.05, clearcoat: 1, clearcoatRoughness: 0.02 }));
  glass.position.z = PD / 2; group.add(glass);
  const tex = canvasTex(SW, SH, (g) => drawChat(g, 0, 0));
  const scrW = PW - 0.0045, scrH = scrW * SH / SW;
  const scrMat = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false });
  const scr = new THREE.Mesh(roundedPlane(scrW, scrH, 0.0065), scrMat); scr.position.z = PD / 2 + 0.00045; group.add(scr);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.0018, 24), new THREE.MeshBasicMaterial({ color: 0x000000 })); hole.position.set(0, scrH / 2 - 0.006, PD / 2 + 0.0005); group.add(hole);
  // reflective top coat on the glass (catches the cabin lights)
  const coat = new THREE.Mesh(roundedPlane(PW - 0.0012, PH - 0.0012, 0.0082), new THREE.MeshPhysicalMaterial({ color: 0x000000, roughness: 0.04, metalness: 0, transparent: true, opacity: 1, transmission: 0, clearcoat: 1, envMapIntensity: 0.25, blending: THREE.AdditiveBlending, depthWrite: false }));
  coat.position.z = PD / 2 + 0.0007; coat.visible = false; group.add(coat);
  let key = '';
  function setScreen(mode, a = 0, b = 0, bright = 1.0) {
    scrMat.color.setScalar(0.8 * bright);
    const k = mode + ':' + a.toFixed(3) + ':' + b.toFixed(3); if (k === key) return; key = k;
    const { g } = tex.userData; if (mode === 'chat') drawChat(g, a, b); else drawCalls(g, a); tex.needsUpdate = true;
  }
  return { group, setScreen, size: [PW, PH, PD] };
}
function roundedPlane(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r); s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  const g = new THREE.ShapeGeometry(s, 8); const uv = g.attributes.uv, p = g.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, (p.getX(i) - x) / w, (p.getY(i) - y) / h);
  return g;
}
