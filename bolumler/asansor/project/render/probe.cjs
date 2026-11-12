const {open}=require('./harness.cjs');
(async()=>{const c=await open({pageName:'probe.html'});console.log(JSON.stringify(c.info,null,1));await c.close();})().catch(e=>{console.error(e);process.exit(1)});
