// node debug.cjs OUT.jpg w h '<json DBG list>'  -> renders each DBG config, hstacks them
const fs=require('fs');const {open}=require('./harness.cjs');
(async()=>{const [out,w,h,json]=process.argv.slice(2);const list=JSON.parse(json);
const c=await open({w:+w,h:+h,samples:2});const bufs=[];
for(const d of list){const url=await c.page.evaluate((d)=>{window.DBG=d;return window.renderShotDebug(d.time||0)},d);bufs.push(Buffer.from(url.split(',')[1],'base64'));}
bufs.forEach((b,i)=>fs.writeFileSync(out.replace('.jpg',`_${i}.jpg`),b));await c.close();})().catch(e=>{console.error(e);process.exit(1)});
