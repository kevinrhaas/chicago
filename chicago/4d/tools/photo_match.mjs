// T-2366: render a structure's committed GLB from the camera its reference photograph was
// taken from, and put the two side by side, so a house is judged against the picture it is
// built from rather than against itself.
//
//   node tools/photo_match.mjs data/reference_views/<structure_id>/<view>.json [--glb <path>] [--out <dir>]
//
// <view>.json (one per reference view: data/reference_views/README.md, T-2368) holds:
//   structure_id   the record the GLB is built for
//   source_id      the picture's record in data/sources/ (and/or library_image, its Prairie
//                  library id)
//   photo          the photograph or drawing, relative to the camera file
//   image_px       [width, height] of that photograph
//   principal_px   [x, y] of its principal point (a view camera's rising front puts it far
//                  off centre; verticals stay vertical, so the camera is not pitched)
//   focal_px       the focal length in the photograph's own pixels (vertical, when
//                  pixel_aspect is given)
//   pixel_aspect   optional (default 1): horizontal over vertical focal length, for a copy
//                  whose width was resampled apart from its height; the solve says what
//                  measured it
//   eye            [u, v, y] in the structure's footprint frame (u east toward the street,
//                  v north, y metres above its grade)
//   yaw_deg        the heading, degrees clockwise from north (90 looks due east)
//   basis_right_up_forward optional: three orthonormal [east,north,up] vectors for
//                  inclined or rolled photographs; overrides yaw orientation
//   sun_uvy        optional: the direction the photograph's sunlight comes from, [u, v, y]
//                  in the same frame (T-2369: which walls are lit and where shadows fall is
//                  part of what is compared); the review render's default east-north-east sun
//                  otherwise
//   near_m         optional near depth (>0, <500 m); distant drawing cameras need
//                  a near plane close to their subject to resolve millimetre layers
//   clip_planes    optional section cuts: {normal:[east,north,up],constant:metres};
//                  keeps normal.dot(point)+constant >= 0; source cut stated in solve
//   solve          how the camera was fitted, in words and numbers (never read here)
// Writes <out>/<name>-side-by-side.jpg (photograph | render, the render the GLB alone at the
// photograph's size and framing; the bare render goes to a temp file), <out> defaulting to
// docs/RESEARCH/photo-match/<structure_id>/. The render is a neutral daylight review render,
// not the app: no terrain, no neighbours, no fog.
//
// THE MATCH RECORD (the image gate, tools/image_gate.mjs). Beside the camera it writes
// <view>.match.json: the GLB and camera it was made from (sha256), the side-by-side, and the
// builder's verdict and differences. A rerun on the same GLB and camera keeps them; a rerun on
// a changed GLB or camera keeps the differences but sets the verdict back to "unreviewed",
// because a building is only said to match the picture someone has looked at.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import {createRequire} from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const {chromium} = require('playwright');
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const camFile = args.find(a => a.endsWith('.json'));
if (!camFile) { console.error('usage: node tools/photo_match.mjs <camera.json> [--glb <path>] [--out <dir>]'); process.exit(2); }
const cam = JSON.parse(fs.readFileSync(camFile, 'utf8'));
if (cam.pixel_aspect !== undefined && (!Number.isFinite(cam.pixel_aspect) || cam.pixel_aspect<=0.5 || cam.pixel_aspect>=2)) throw Error('pixel_aspect must be finite and between 0.5 and 2');
if (cam.near_m !== undefined && (!Number.isFinite(cam.near_m) || cam.near_m<=0 || cam.near_m>=500)) throw Error('near_m must be finite and between 0 and the 500 m far plane');
if (cam.clip_planes !== undefined && (!Array.isArray(cam.clip_planes) || cam.clip_planes.some(p => !p || !Array.isArray(p.normal) || p.normal.length !== 3 || !p.normal.every(Number.isFinite) || Math.abs(Math.hypot(...p.normal)-1)>1e-6 || !Number.isFinite(p.constant)))) throw Error('clip_planes requires finite unit [east,north,up] normals and constants in metres');
const glb = opt('--glb') || (() => {
  const m = JSON.parse(fs.readFileSync(path.join(root, 'assets/manifest.json'), 'utf8'));
  const hit = Object.entries(m.assets || m).find(([k, v]) => v && v.structure_id === cam.structure_id && !/coach_house/.test(k));
  if (!hit) throw Error(`no GLB for ${cam.structure_id} in assets/manifest.json`);
  return path.join('assets/gltf', hit[0]);
})();
const out = opt('--out') || path.join('docs/RESEARCH/photo-match', cam.structure_id);
const name = path.basename(camFile, '.json');
const photo = path.resolve(path.dirname(camFile), cam.photo);
fs.mkdirSync(out, {recursive: true});
const [W, H] = cam.image_px, [cx, cy] = cam.principal_px, f = cam.focal_px;
const page_html = `<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#fff}canvas{display:block}</style>
<script type=importmap>{"imports":{"three":"/renderers/web/vendor/three-0.185.1/three.module.js","three/addons/":"/renderers/web/vendor/three-0.185.1/addons/"}}</script>
<script type=module>
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {KTX2Loader} from 'three/addons/loaders/KTX2Loader.js';
import {tintKeithStone} from '/renderers/web/js/keith-stone.js';
const c=${JSON.stringify({W, H, cx, cy, f, aspect: cam.pixel_aspect ?? 1, eye: cam.eye, yaw: cam.yaw_deg, basis: cam.basis_right_up_forward || null, near: cam.near_m ?? 0.1, sun: cam.sun_uvy || null, clips: cam.clip_planes || [], glb: '/' + glb.replace(/\\/g, '/')})};
const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setPixelRatio(1);r.setSize(c.W,c.H);
r.outputColorSpace=THREE.SRGBColorSpace;r.toneMapping=THREE.ACESFilmicToneMapping;r.shadowMap.enabled=true;
r.clippingPlanes=c.clips.map(p=>new THREE.Plane(new THREE.Vector3(p.normal[0],p.normal[2],-p.normal[1]),p.constant));
document.body.appendChild(r.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0xe8ecef);
s.add(new THREE.HemisphereLight(0xdfe8f0,0x8a8070,1.1));
const sun=new THREE.DirectionalLight(0xfff4e0,2.4);sun.castShadow=true;
if(c.sun){const k=75/Math.hypot(...c.sun);sun.position.set(c.sun[0]*k,c.sun[2]*k,-c.sun[1]*k);}else sun.position.set(60,45,-20);
Object.assign(sun.shadow.camera,{left:-40,right:40,top:40,bottom:-40,near:1,far:200});sun.shadow.mapSize.set(4096,4096);sun.shadow.bias=-0.0004;
s.add(sun);
const g=new THREE.Mesh(new THREE.PlaneGeometry(400,400),new THREE.MeshStandardMaterial({color:0x9a9686,roughness:1}));
g.rotation.x=-Math.PI/2;g.position.y=-0.01;g.receiveShadow=true;s.add(g);
// a camera whose principal point is off centre: frame a larger symmetric view about it and
// cut the photograph's window out of it (THREE's view offset)
const FW=2*Math.max(c.cx,c.W-c.cx),FH=2*Math.max(c.cy,c.H-c.cy);
const cam=new THREE.PerspectiveCamera(2*Math.atan(FH/2/c.f)*180/Math.PI,FW/FH,c.near,500);
cam.setViewOffset(FW,FH,FW/2-c.cx,FH/2-c.cy,c.W,c.H);
// setViewOffset sets aspect to FW/FH; a resampled copy's pixels are not square
if(c.aspect!==1){cam.aspect=FW/FH/c.aspect;cam.updateProjectionMatrix();}
// footprint frame (u, v, y) -> glTF (x = u, y, z = -v); yaw clockwise from north
const [u,v,y]=c.eye,t=c.yaw*Math.PI/180;
cam.position.set(u,y,-v);cam.lookAt(u+Math.sin(t),y,-v-Math.cos(t));
if(c.basis){
 const [right,up,forward]=c.basis.map(([x,n,z])=>new THREE.Vector3(x,z,-n));
 cam.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(right,up,forward.negate()));
}
const l=new GLTFLoader();l.setMeshoptDecoder(MeshoptDecoder);
// a web derivative's textures are KTX2 (T-2595); a master's stay PNG/JPEG and never reach this
l.setKTX2Loader(new KTX2Loader().detectSupport(r));
l.load(c.glb,x=>{x.scene.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;for(const m of (Array.isArray(o.material)?o.material:[o.material]))tintKeithStone(m,{id:${JSON.stringify(cam.structure_id)}});}});s.add(x.scene);
r.render(s,cam);window.__done=true;},undefined,e=>{window.__error=String(e);});
</script>`;
const types = {'.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ktx2': 'image/ktx2', '.webp': 'image/webp'};
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/__photo_match.html') { res.writeHead(200, {'Content-Type': 'text/html'}); return res.end(page_html); }
  if (u === '/__photo') { res.writeHead(200, {'Content-Type': 'image/jpeg'}); return fs.createReadStream(photo).pipe(res); }
  const p = path.join(root, u);
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'Content-Type': types[path.extname(p)] || 'application/octet-stream'});
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader']});
try {
  const page = await browser.newPage({viewport: {width: W, height: H}, deviceScaleFactor: 1});
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(base + '/__photo_match.html', {waitUntil: 'domcontentloaded', timeout: 180000});
  await page.waitForFunction(() => window.__done || window.__error, null, {timeout: 300000, polling: 500});
  const err = await page.evaluate(() => window.__error);
  if (err || errors.length) throw Error(err || errors.join('\n'));
  const render = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'photo-match-')), `${name}-render.png`);
  // The viewport is exactly this static canvas. Rendering readiness and errors
  // were checked above; waiting for two layout-stability frames can time out
  // behind Glessner's software-rendered GPU work. Capture the same pixels
  // directly, allowing the large reference render time to finish its readback.
  await page.screenshot({path: render, timeout: 180000});
  // photograph | render, side by side, the render at the photograph's own size
  const side = path.join(out, `${name}-side-by-side.jpg`);
  const png = fs.readFileSync(render).toString('base64');
  await page.setViewportSize({width: 2 * W + 24, height: H});
  await page.setContent(`<body style="margin:0;background:#fff;display:flex;gap:24px"><img src="${base}/__photo" style="width:${W}px;height:${H}px"><img src="data:image/png;base64,${png}" style="width:${W}px;height:${H}px"></body>`);
  await page.waitForFunction(() => [...document.images].every(i => i.complete && i.naturalWidth));
  await page.screenshot({path: side, type: 'jpeg', quality: 82});
  // the match record the image gate reads (T-2368)
  const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  const matchFile = camFile.replace(/\.json$/, '.match.json');
  const was = fs.existsSync(matchFile) ? JSON.parse(fs.readFileSync(matchFile, 'utf8')) : {};
  const glbSha = sha(glb), camSha = sha(camFile);
  const same = was.glb_sha256 === glbSha && was.camera_sha256 === camSha;
  const rec = {
    structure_id: cam.structure_id, view: name, glb: glb.replace(/\\/g, '/'), glb_sha256: glbSha, camera_sha256: camSha,
    side_by_side: path.relative(root, side).replace(/\\/g, '/'),
    verdict: same && was.verdict ? was.verdict : 'unreviewed',
    differences: Array.isArray(was.differences) ? was.differences : [],
    _how: 'verdict is unreviewed | differs | matches, set by whoever compared the side-by-side with the picture; each difference is {what, status: open | fixed | not shown}. A ticket whose ## Image gate names this building does not close while it is not "matches" (tools/image_gate.mjs).',
  };
  fs.writeFileSync(matchFile, JSON.stringify(rec, null, 2) + '\n');
  console.log(`photo_match: ${glb}\n  ${render}\n  ${side}\n  ${matchFile} (${rec.verdict}${same ? '' : was.verdict ? ' — the GLB or camera changed; look again' : ''})`);
} finally { await browser.close(); server.close(); }
