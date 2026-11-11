// Render the complete film: every frame seeks the scene, JPEG frames are piped to FFmpeg,
// and the untouched reference audio is muxed in (re-encoded to AAC for MP4 players).
// usage: node video.cjs OUT.mp4 [w h samples] [startFrame endFrame]
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const { open, TOOL_ROOT } = require('./harness.cjs');
const FFMPEG = 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/bin/ffmpeg.exe';
const VOICE = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', 'voice.json'), 'utf8'));
const AUDIO = path.resolve(__dirname, '..', '..', VOICE.mix || VOICE.audio);   // narration (+SFX mix) named in project/voice.json only
(async () => {
  let [out, w = 1080, h = 1920, samples = 8, a = 0, b] = process.argv.slice(2);
  const ctx = await open({ w: +w, h: +h, samples: +samples });
  console.log(JSON.stringify(ctx.info));
  if (b === undefined) b = ctx.info.frames;
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30000/1001', '-c:v', 'mjpeg', '-i', '-',
    '-i', AUDIO, '-map', '0:v:0', '-map', '1:a:0', '-vf', 'scale=in_range=pc:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', String(process.env.CRF || 16), '-pix_fmt', 'yuv420p',
    '-r', '30000/1001', '-c:a', 'aac', '-b:a', String(process.env.ABR || '192k'), '-ar', '48000', '-ac', '2',
    '-frames:v', String(+b - +a), '-t', String((+b - +a) * 1001 / 30000), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = +a; f < +b; f++) {
    const buf = await ctx.frame(f, 0.96);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 20 === 0) console.log(`frame ${f}/${b}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await ctx.close();
  console.log('done', out, ((Date.now() - t0) / 1000).toFixed(0) + 's');
})().catch(e => { console.error(e); process.exit(1); });
