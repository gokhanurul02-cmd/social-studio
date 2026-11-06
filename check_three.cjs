// Internal installation check; no external assets or creative video output.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=__dirname,packageRoot=path.join(root,'node_modules','three');
const out=path.join(root,'jobs','three-install-check');
const html=`<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}</style>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
</head><body><script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(45,1,.1,100);camera.position.z=3;
const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshNormalMaterial());scene.add(mesh);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(320,320);renderer.setClearColor(0x000000);document.body.append(renderer.domElement);
window.seek=t=>{mesh.rotation.set(t*.6,t*.9,0);renderer.render(scene,camera)};window.seek(0);
const gl=renderer.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info'),pixel=new Uint8Array(4);
gl.readPixels(160,160,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
window.proof={revision:THREE.REVISION,webgl2:gl instanceof WebGL2RenderingContext,
draw_calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,center_pixel:Array.from(pixel),
addons_loaded:!!GLTFLoader&&!!OrbitControls,
renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)};
</script></body></html>`;
(async()=>{
fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
if(req.url==='/'){res.writeHead(200,{'Content-Type':'text/html'});res.end(html);return;}
if(!req.url.startsWith('/three/')){res.writeHead(404);res.end();return;}
const file=path.resolve(packageRoot,decodeURIComponent(req.url.slice(7).split('?')[0]));
if(!file.startsWith(packageRoot+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
res.writeHead(200,{'Content-Type':'text/javascript'});fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));let browser;
try{
const cache=path.join(process.env.USERPROFILE,'.cache','hyperframes','chrome','chrome-headless-shell');
const rev=fs.readdirSync(cache).find(x=>x.startsWith('win64-'));
browser=await chromium.launch({headless:true,executablePath:path.join(cache,rev,'chrome-headless-shell-win64','chrome-headless-shell.exe'),
args:process.platform==='win32'?['--use-angle=d3d11','--enable-gpu','--ignore-gpu-blocklist']:[]});
const page=await browser.newPage({viewport:{width:320,height:320}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+server.address().port+'/');
await page.waitForFunction(()=>!!window.proof);const proof=await page.evaluate(()=>window.proof);
const first=await page.screenshot({path:path.join(out,'frame-0.png')});await page.evaluate(()=>window.seek(1));
const second=await page.screenshot({path:path.join(out,'frame-1.png')});
assert.equal(proof.revision,'187');assert.equal(proof.webgl2,true);assert.equal(proof.addons_loaded,true);
assert.ok(proof.draw_calls>0);assert.ok(proof.center_pixel.slice(0,3).some(x=>x>0));
assert.ok(!first.equals(second));assert.deepEqual(errors,[]);
fs.writeFileSync(path.join(root,'three-verification.json'),JSON.stringify({package:'three',version:'0.187.0',
repository:'https://github.com/mrdoob/three.js',checked_at:new Date().toISOString(),...proof,seek_changes_frame:true,errors},null,2));
console.log(JSON.stringify({revision:proof.revision,webgl2:proof.webgl2,addons:proof.addons_loaded,
renderer:proof.renderer,seek_changes_frame:true}));
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1});
