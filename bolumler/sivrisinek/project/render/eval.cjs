const {open}=require('./harness.cjs');
(async()=>{const c=await open({w:270,h:480,samples:1});const r=await c.page.evaluate(process.argv[2]);console.log(JSON.stringify(r,null,0));await c.close();})().catch(e=>{console.error(e);process.exit(1)});
