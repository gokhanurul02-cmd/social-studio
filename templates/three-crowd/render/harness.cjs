// Shared render harness for Three.js projects that use templates/three-crowd.
// Local static server + headless GPU Chrome. URL map:
//   /three/...   -> node_modules/three           (importmap: "three", "three/addons/")
//   /assets/...  -> <repo>/assets                (catalog.json, glb, hdr)
//   /crowd/...   -> <repo>/templates/three-crowd (crowd.js)
//   /fonts/...   -> C:/Windows/Fonts             (render-only system fonts)
//   /...         -> the project folder
// The page must set window.READY = true (or window.FAILED = msg) and expose window.renderFrame(i, q) -> dataURL.
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');
const TOOL_ROOT = path.resolve(__dirname, '..', '..', '..');
const { chromium } = require(path.join(TOOL_ROOT, 'node_modules', 'playwright'));
const ROUTES = {
  '/three/': path.join(TOOL_ROOT, 'node_modules', 'three'),
  '/assets/': path.join(TOOL_ROOT, 'assets'),
  '/crowd/': path.join(TOOL_ROOT, 'templates', 'three-crowd'),
  '/fonts/': 'C:/Windows/Fonts',
};
const HYPERFRAMES_BROWSER = path.join(os.homedir(), '.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe');
const BROWSER = process.env.SOCIAL_CHROME_PATH || (fs.existsSync(HYPERFRAMES_BROWSER) ? HYPERFRAMES_BROWSER : undefined);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.bin': 'application/octet-stream', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.hdr': 'application/octet-stream', '.ttf': 'font/ttf' };

function serve(project) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let base = project, rel = url === '/' ? 'index.html' : url.slice(1);
    for (const [prefix, dir] of Object.entries(ROUTES)) if (url.startsWith(prefix)) { base = dir; rel = url.slice(prefix.length); break; }
    const file = path.resolve(base, rel);
    if (!file.startsWith(path.resolve(base)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

async function open({ project, page: pageName = '', w = 1080, h = 1920, samples = 8, extra = '' } = {}) {
  const server = await serve(project);
  const browser = await chromium.launch({ headless: true, executablePath: BROWSER,
    args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader=false', '--force-gpu-mem-available-mb=8000'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  const errors = [];
  page.on('pageerror', e => { errors.push(e.message); console.error('[pageerror]', e.message); });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning' || m.text().startsWith('[cy]')) console.error('[console]', m.text()); });
  await page.goto(`http://127.0.0.1:${server.address().port}/${pageName}?w=${w}&h=${h}&samples=${samples}${extra}`);
  await page.waitForFunction(() => window.READY === true || window.FAILED, null, { timeout: 300000 });
  const failed = await page.evaluate(() => window.FAILED);
  if (failed) { await browser.close(); server.close(); throw new Error('page failed: ' + failed); }
  const info = await page.evaluate(() => window.INFO);
  return { server, browser, page, errors, info,
    async frame(i, quality = 0.95) {
      const dataUrl = await page.evaluate(([i, q]) => window.renderFrame(i, q), [i, quality]);
      return Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');
    },
    async close() { await browser.close(); await new Promise(r => server.close(r)); } };
}
module.exports = { open, TOOL_ROOT, ROUTES };
