// T-3385: a material-id pass from a reference view's own camera (data/reference_views/README.md),
// so the tone reading (tone_read.py) measures the photograph inside the build's own brick, stone,
// slate and paint, rather than in hand-placed boxes. Same camera arithmetic as tools/photo_match.mjs.
//
//   node docs/RESEARCH/face-brick-1904-T-3385/idpass.mjs <camera.json> <out-prefix>
// Writes <out-prefix>.png (R,G = material index + 1, B = face: 1 street front, 2 side, 3 rear,
// 4 up, 0 another member) and <out-prefix>.json (index -> material name).
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
import {renderGroup} from '../../../tools/photo_match_group.mjs';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..');
const require = createRequire(import.meta.url);
let chromium;
try { ({chromium} = require('playwright')); } catch { ({chromium} = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }
const [camFile, outPrefix] = process.argv.slice(2);
const cam = JSON.parse(fs.readFileSync(camFile, 'utf8'));
const members = renderGroup(root, cam, {});
const [W, H] = cam.image_px, [cx, cy] = cam.principal_px, f = cam.focal_px;
const html = `<!doctype html><meta charset=utf-8><style>html,body{margin:0}canvas{display:block}</style>
<script type=importmap>{"imports":{"three":"/renderers/web/vendor/three-0.185.1/three.module.js","three/addons/":"/renderers/web/vendor/three-0.185.1/addons/"}}</script>
<script type=module>
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
const c=${JSON.stringify({W, H, cx, cy, f, aspect: cam.pixel_aspect ?? 1, eye: cam.eye, yaw: cam.yaw_deg, basis: cam.basis_right_up_forward || null, near: cam.near_m ?? 0.1, members: members.map(m => ({...m, glb: '/' + m.glb}))})};
const r=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});r.setPixelRatio(1);r.setSize(c.W,c.H);
r.outputColorSpace=THREE.LinearSRGBColorSpace;r.toneMapping=THREE.NoToneMapping;
document.body.appendChild(r.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0,0,0);
const FW=2*Math.max(c.cx,c.W-c.cx),FH=2*Math.max(c.cy,c.H-c.cy);
const cam=new THREE.PerspectiveCamera(2*Math.atan(FH/2/c.f)*180/Math.PI,FW/FH,c.near,500);
cam.setViewOffset(FW,FH,FW/2-c.cx,FH/2-c.cy,c.W,c.H);
if(c.aspect!==1){cam.aspect=FW/FH/c.aspect;cam.updateProjectionMatrix();}
const [u,v,y]=c.eye,t=c.yaw*Math.PI/180;
cam.position.set(u,y,-v);cam.lookAt(u+Math.sin(t),y,-v-Math.cos(t));
if(c.basis){const [right,up,forward]=c.basis.map(([x,n,z])=>new THREE.Vector3(x,z,-n));
 cam.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(right,up,forward.negate()));}
const names=[];const idx=n=>{let i=names.indexOf(n);if(i<0){names.push(n);i=names.length-1;}return i+1;};
const mk=(id,member)=>new THREE.ShaderMaterial({side:THREE.DoubleSide,uniforms:{id:{value:id},member:{value:member}},
 vertexShader:'varying vec3 vN;void main(){vN=normal;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
 fragmentShader:'uniform float id;uniform float member;varying vec3 vN;void main(){vec3 n=normalize(vN);float face=0.0;'+
 'if(member<0.5){if(n.y>0.5)face=4.0;else if(n.x>0.7)face=1.0;else if(n.x<-0.7)face=3.0;else face=2.0;}'+
 'gl_FragColor=vec4(mod(id,256.0)/255.0,floor(id/256.0)/255.0,face/255.0,1.0);}'});
const l=new GLTFLoader();l.setMeshoptDecoder(MeshoptDecoder);
Promise.all(c.members.map(async (m,mi)=>{const x=await l.loadAsync(m.glb);
 x.scene.traverse(o=>{if(o.isMesh){const ms=Array.isArray(o.material)?o.material:[o.material];
  const out=ms.map(mm=>mk(mi===0?idx(mm.name||'?'):0,mi));o.material=Array.isArray(o.material)?out:out[0];}});
 const g=new THREE.Group();g.position.fromArray(m.position);g.rotation.y=m.rotation_y;g.add(x.scene);return g;}))
.then(gs=>{for(const g of gs)s.add(g);r.render(s,cam);window.__names=names;window.__done=true;})
.catch(e=>{window.__error=String(e);});
</script>`;
const types = {'.js': 'text/javascript', '.glb': 'model/gltf-binary'};
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/p.html') { res.writeHead(200, {'Content-Type': 'text/html'}); return res.end(html); }
  const p = path.join(root, u);
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'Content-Type': types[path.extname(p)] || 'application/octet-stream'});
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader']});
try {
  const page = await browser.newPage({viewport: {width: W, height: H}, deviceScaleFactor: 1});
  await page.goto(`http://127.0.0.1:${server.address().port}/p.html`);
  await page.waitForFunction(() => window.__done || window.__error, null, {timeout: 300000, polling: 500});
  const err = await page.evaluate(() => window.__error);
  if (err) throw Error(err);
  await page.screenshot({path: outPrefix + '.png', timeout: 180000});
  fs.writeFileSync(outPrefix + '.json', JSON.stringify({camera: camFile, photo: path.resolve(path.dirname(camFile), cam.photo), mirrored: !!cam.mirrored, names: await page.evaluate(() => window.__names)}, null, 1));
  console.log('idpass', outPrefix);
} finally { await browser.close(); server.close(); }
