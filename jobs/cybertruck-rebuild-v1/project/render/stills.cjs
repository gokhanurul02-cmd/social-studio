// Render selected frames to JPEG for inspection.
// usage: node stills.cjs OUTDIR w h samples frame1,frame2,...   (frames may be given as t=seconds)
const fs = require('fs'), path = require('path');
const { open } = require('./harness.cjs');
(async () => {
  const [out, w, h, samples, list] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const fps = 30000 / 1001;
  const frames = list.split(',').map(s => s.startsWith('t') ? Math.round(parseFloat(s.slice(1)) * fps) : parseInt(s));
  const ctx = await open({ w: +w, h: +h, samples: +samples });
  console.log(JSON.stringify(ctx.info));
  for (const f of frames) {
    const t0 = Date.now();
    const buf = await ctx.frame(f, 0.92);
    fs.writeFileSync(path.join(out, `f${String(f).padStart(4, '0')}.jpg`), buf);
    console.log('frame', f, (f / fps).toFixed(3) + 's', Date.now() - t0, 'ms');
  }
  await ctx.close();
})().catch(e => { console.error(e); process.exit(1); });
