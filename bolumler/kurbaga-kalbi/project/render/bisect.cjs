const fs=require('fs');const {open}=require('./harness.cjs');
(async()=>{const c=await open({w:270,h:480,samples:1});
const tests=JSON.parse(process.argv[3]);let i=0;
for(const hide of tests){const url=await c.page.evaluate(([hide])=>{const W=window.WORLD;const orig=W.apply.bind(W);
 W.apply=(shot,t)=>{const st=orig(shot,t);for(const k of hide){const o=k.split('.').reduce((a,b)=>a[b],W);(o.group||o.mesh||o).visible=false;} if(hide.includes('fog'))W.scene.fog=null; return st;};
 const r=window.renderFrame(330,0.9);W.apply=orig;return r;},[hide]);fs.writeFileSync(process.argv[2]+'_'+(i++)+'.jpg',Buffer.from(url.split(',')[1],'base64'));}
await c.close();})().catch(e=>{console.error(e);process.exit(1)});
