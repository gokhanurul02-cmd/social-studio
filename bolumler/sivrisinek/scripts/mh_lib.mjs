// MakeHuman base.obj + .target reader (CC0 assets). Keeps original vertex indices.
import fs from 'fs';
export function readObj(path) {
  const v = [], faces = [], groups = new Map();
  let g = 'default';
  for (const line of fs.readFileSync(path, 'utf8').split('\n')) {
    if (line.startsWith('v ')) { const p = line.trim().split(/\s+/); v.push(+p[1], +p[2], +p[3]); }
    else if (line.startsWith('g ')) g = line.trim().slice(2);
    else if (line.startsWith('f ')) {
      const idx = line.trim().split(/\s+/).slice(1).map(t => parseInt(t.split('/')[0]) - 1);
      faces.push({ g, idx });
      if (!groups.has(g)) groups.set(g, new Set());
      for (const i of idx) groups.get(g).add(i);
    }
  }
  return { v: Float64Array.from(v), faces, groups };
}
export function applyTarget(v, path, w = 1) {
  for (const line of fs.readFileSync(path, 'utf8').split('\n')) {
    if (!line || line[0] === '#') continue;
    const p = line.trim().split(/\s+/); if (p.length < 4) continue;
    const i = +p[0]; v[i * 3] += w * +p[1]; v[i * 3 + 1] += w * +p[2]; v[i * 3 + 2] += w * +p[3];
  }
}
export function centroid(v, set) {
  let x = 0, y = 0, z = 0, n = 0;
  for (const i of set) { x += v[i * 3]; y += v[i * 3 + 1]; z += v[i * 3 + 2]; n++; }
  return [x / n, y / n, z / n];
}
export function joints(obj, v) {
  const J = {};
  for (const [g, s] of obj.groups) if (g.startsWith('joint-')) J[g.slice(6)] = centroid(v, s);
  return J;
}
