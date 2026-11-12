// Shared harness: local static server + headless GPU Chrome page running the Three.js project.
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');
const TOOL_ROOT = 'C:/Users/birlik grup/Documents/Codex/tools/cybertruck-threejs-study';
const { chromium } = require(path.join(TOOL_ROOT, 'node_modules', 'playwright'));
const PROJECT = path.resolve(__dirname, '..');
const THREE_ROOT = path.join(TOOL_ROOT, 'node_modules', 'three');
const FONT_DIR = 'C:/Windows/Fonts';
const HYPERFRAMES_BROWSER = path.join(os.homedir(), '.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe');
const BROWSER = process.env.SOCIAL_CHROME_PATH || (fs.existsSync(HYPERFRAMES_BROWSER) ? HYPERFRAMES_BROWSER : undefined);

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.wav': 'audio/wav' };

function serve() {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let base, rel;
    if (url.startsWith('/three/')) { base = THREE_ROOT; rel = url.slice(7); }
    else if (url.startsWith('/fonts/')) { base = FONT_DIR; rel = url.slice(7); }
    else if (url.startsWith('/job/')) { base = path.resolve(PROJECT, '..'); rel = url.slice(5); }
    else { base = PROJECT; rel = url === '/' ? 'index.html' : url.slice(1); }
    const file = path.resolve(base, rel);
    if (!file.startsWith(path.resolve(base)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

async function open({ w = 1080, h = 1920, samples = 8, extra = '', pageName = '' } = {}) {
  const server = await serve();
  const browser = await chromium.launch({ headless: true, executablePath: BROWSER,
    args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader=false', '--force-gpu-mem-available-mb=8000'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  const errors = [];
  page.on('pageerror', e => { errors.push(e.message); console.error('[pageerror]', e.message); page.evaluate(m => { window.FAILED = window.FAILED || m; }, e.message).catch(() => {}); });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning' || m.text().startsWith('[cy]')) console.error('[console]', m.text()); });
  await page.goto(`http://127.0.0.1:${server.address().port}/${pageName}?w=${w}&h=${h}&samples=${samples}${extra}${process.env.DBG ? '&dbg=1' : ''}`);
  await page.waitForFunction(() => window.READY === true || window.FAILED, null, { timeout: 180000 });
  const failed = await page.evaluate(() => window.FAILED);
  if (failed) throw new Error('page failed: ' + failed);
  const info = await page.evaluate(() => window.INFO);
  return { server, browser, page, errors, info,
    async frame(i, quality = 0.95) {
      const dataUrl = await page.evaluate(([i, q]) => window.renderFrame(i, q), [i, quality]);
      return Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');
    },
    async close() { await browser.close(); await new Promise(r => server.close(r)); } };
}
module.exports = { open, PROJECT, TOOL_ROOT };
