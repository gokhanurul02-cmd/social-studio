// node render/try.cjs OUT.jpg "<js before render>" t1,t2 [w h samples]
const fs=require('fs');const {open}=require('./harness.cjs');
(async()=>{const [out,js,ts,w=540,h=960,s=4]=process.argv.slice(2);const c=await open({w:+w,h:+h,samples:+s});
await c.page.evaluate(js);const fps=30000/1001;let i=0;
for(const t of ts.split(',')){const b=await c.frame(Math.round(parseFloat(t)*fps),0.92);fs.writeFileSync(out.replace('.jpg',`_${i++}.jpg`),b);}
await c.close();})().catch(e=>{console.error(e);process.exit(1)});
