// Side-by-side: top row reference hook frames, bottom row our stills (all scaled to 270x480 tiles).
// usage: node render/yanyana.cjs <ours_dir> <out.jpg>
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const FF = 'C:/Users/birlik grup/Documents/Codex/tools/social-studio/bin/ffmpeg.exe';
const REF = path.resolve(__dirname, '../../inspect/ref');
const [oursDir, out] = process.argv.slice(2);
const refs = ['hb_0', 'hb_30', 'hb_60', 'hb_90', 'bv_0', 'bv_15', 'bv_45'].map(n => path.join(REF, n + '.jpg'));
const ours = fs.readdirSync(oursDir).filter(f => /^f\d+\.jpg$/.test(f)).sort().map(f => path.join(oursDir, f));
const n = Math.max(refs.length, ours.length);
const args = ['-y', '-loglevel', 'error'];
const all = [...refs, ...ours];
for (const f of all) args.push('-i', f);
let fc = '';
all.forEach((f, i) => { fc += `[${i}]scale=270:480,setsar=1[s${i}];`; });
const pad = (k, row) => { let s = ''; for (let i = row.length; i < n; i++) { s += `color=c=0x202020:s=270x480:d=1[p${k}${i}];`; row.push(`[p${k}${i}]`); } return s; };
const top = refs.map((_, i) => `[s${i}]`), bot = ours.map((_, i) => `[s${refs.length + i}]`);
fc += pad('a', top) + pad('b', bot);
fc += `${top.join('')}hstack=${n}[top];${bot.join('')}hstack=${n}[bot];[top][bot]vstack[v]`;
args.push('-filter_complex', fc, '-map', '[v]', '-frames:v', '1', '-q:v', '3', out);
execFileSync(FF, args, { stdio: 'inherit' });
console.log('wrote', out, 'ref', refs.length, 'ours', ours.length);
