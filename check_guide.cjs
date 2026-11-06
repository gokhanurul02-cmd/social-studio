const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require('playwright');

(async () => {
  const doctor = JSON.parse(fs.readFileSync(path.join(__dirname,'doctor.json'),'utf8'));
  const detail = doctor.hyperframes.checks.find(c=>c.name==='Chrome').detail;
  const cache = path.join(process.env.USERPROFILE,'.cache','hyperframes','chrome','chrome-headless-shell');
  const revision = fs.readdirSync(cache).find(x=>x.startsWith('win64-'));
  const executablePath = path.join(cache,revision,'chrome-headless-shell-win64','chrome-headless-shell.exe');
  const browser = await chromium.launch({executablePath, headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors = [];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(__dirname,'KULLANIM-KILAVUZU.html')).href);
  await page.screenshot({path:path.join(__dirname,'guide-desktop.png')});
  const headings = await page.locator('h2').count();
  const navigation = await page.locator('#toc a').count();
  if(headings<10 || headings!==navigation) throw new Error('Incomplete guide navigation');
  await page.locator('#search').fill('Postiz');
  const visible = await page.locator('h2:not(.hidden)').count();
  if(visible<1 || visible>=headings) throw new Error('Search did not filter sections');
  await page.locator('#search').fill('');
  // Capture clipboard calls in this isolated headless page; do not change the OS clipboard.
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,
    value:{writeText:async value=>{window.__testCopied=value;}}}));
  await page.locator('button.copy').first().click();
  const copied = await page.evaluate(()=>window.__testCopied);
  if(!copied || !copied.includes('$social-rebuild')) throw new Error('Copy button failed');
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(__dirname,'guide-mobile.png'),fullPage:false});
  const dimensions = await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  if(dimensions.scroll>dimensions.width) throw new Error('Mobile horizontal overflow '+JSON.stringify(dimensions));
  if(errors.length) throw new Error(errors.join('\n'));
  fs.writeFileSync(path.join(__dirname,'guide-verification.json'),JSON.stringify({
    headings,navigation,search_visible_headings:visible,copy_test:true,mobile:dimensions,errors},null,2));
  await browser.close();
  console.log('Guide navigation, search, copy, desktop and mobile checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
