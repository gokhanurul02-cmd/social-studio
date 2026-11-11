// Render selected frames to JPEG for inspection.
// usage: node stills.cjs OUTDIR w h samples LIST
//   LIST: frame numbers / t<seconds>, comma separated; or "shots" (middle of every shot, named by shot id);
//         or "pano<N>" (N evenly spaced frames over the whole film) -> also writes OUTDIR/pano.jpg (8 columns)
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const { open } = require('./harness.cjs');
const FF = 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/bin/ffmpeg.exe';
(async () => {
  const [out, w, h, samples, list] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const fps = 30000 / 1001;
  const ctx = await open({ w: +w, h: +h, samples: +samples });
  console.log(JSON.stringify(ctx.info));
  const TL = await ctx.page.evaluate(() => window.TL);
  let jobs;
  if (list === 'shots') jobs = TL.shots.map((s, i) => ({ f: Math.round(((s.a + Math.min(s.b, TL.duration)) / 2) * fps), name: `s${String(i + 1).padStart(2, '0')}_${s.id}` }));
  else if (list.startsWith('pano')) { const n = +list.slice(4) || 48, N = ctx.info.frames; jobs = Array.from({ length: n }, (_, i) => ({ f: Math.min(N - 1, Math.round((i + 0.5) * N / n)), name: `p${String(i).padStart(2, '0')}` })); }
  else jobs = list.split(',').map(s => ({ f: s.startsWith('t') ? Math.round(parseFloat(s.slice(1)) * fps) : parseInt(s) })).map(j => ({ ...j, name: `f${String(j.f).padStart(4, '0')}` }));
  for (const j of (process.env.SHEET_ONLY ? [] : jobs)) {
    const t0 = Date.now();
    const buf = await ctx.frame(j.f, 0.92);
    fs.writeFileSync(path.join(out, j.name + '.jpg'), buf);
    console.log(j.name, 'frame', j.f, (j.f / fps).toFixed(3) + 's', Date.now() - t0, 'ms');
  }
  await ctx.close();
  if (list.startsWith('pano') || list === 'shots') {
    const files = jobs.map(j => path.join(out, j.name + '.jpg'));
    const cols = 8, rows = Math.ceil(files.length / cols), tw = 180, th = 320;
    const args = ['-y', '-loglevel', 'error'];
    files.forEach(f => args.push('-i', f));
    let fc = files.map((f, i) => `[${i}]scale=${tw}:${th},drawtext=fontfile=verdanab.ttf:text=${list === 'shots' ? jobs[i].name.replace(/^s\d+_/, '') : (jobs[i].f / fps).toFixed(1).replace('.', 's')}:x=6:y=6:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6[t${i}]`).join(';');
    const pads = []; for (let i = files.length; i < rows * cols; i++) { fc += `;color=c=black:s=${tw}x${th}:d=1[t${i}]`; }
    for (let r = 0; r < rows; r++) fc += `;${Array.from({ length: cols }, (_, c) => `[t${r * cols + c}]`).join('')}hstack=${cols}[r${r}]`;
    fc += `;${Array.from({ length: rows }, (_, r) => `[r${r}]`).join('')}vstack=${rows}[v]`;
    args.push('-filter_complex', fc, '-map', '[v]', '-frames:v', '1', '-q:v', '3', path.join(out, list === 'shots' ? 'shots.jpg' : 'pano.jpg'));
    fs.copyFileSync('C:/Windows/Fonts/verdanab.ttf', path.join(out, 'verdanab.ttf')); execFileSync(FF, args.map(a => /\.jpg$/.test(a) ? path.basename(a) : a), { stdio: 'ignore', cwd: out });
    console.log('sheet written');
  }
})().catch(e => { console.error(e); process.exit(1); });
