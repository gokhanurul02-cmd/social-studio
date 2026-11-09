// usage: node templates/three-crowd/probe/probe.cjs OUTDIR [ids,comma,separated]
// Writes OUTDIR/NNN.jpg (views listed in probe.json), OUTDIR/probe.json and OUTDIR/sheet.jpg (4 tiles per asset row).
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const { open, TOOL_ROOT } = require('../render/harness.cjs');
(async () => {
  const [out, ids] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const ctx = await open({ project: __dirname, w: 480, h: 480, extra: ids ? `&ids=${ids}` : '' });
  for (let i = 0; i < ctx.info.frames; i++) fs.writeFileSync(path.join(out, `${String(i).padStart(3, '0')}.jpg`), await ctx.frame(i));
  await ctx.close();
  fs.writeFileSync(path.join(out, 'probe.json'), JSON.stringify({ views: ctx.info.views, assets: ctx.info.info }, null, 1));
  const rows = Math.ceil(ctx.info.frames / 4);
  execFileSync(path.join(TOOL_ROOT, 'bin', 'ffmpeg.exe'), ['-y', '-loglevel', 'error', '-framerate', '1', '-i', path.join(out, '%03d.jpg'),
    '-vf', `scale=240:240,tile=4x${rows}`, '-frames:v', '1', path.join(out, 'sheet.jpg')]);
  console.log(JSON.stringify(ctx.info.info));
})().catch(e => { console.error(e); process.exit(1); });
