// T-2366: render a structure's committed GLB from the camera its reference photograph was
// taken from, and put the two side by side, so a house is judged against the picture it is
// built from rather than against itself.
//
//   node tools/photo_match.mjs data/reference_views/<structure_id>/<view>.json [--glb <path>] [--out <dir>]
//
// <view>.json (one per reference view: data/reference_views/README.md, T-2368) holds:
//   structure_id   the record the GLB is built for
//   also_render    optional ids of context structures, all required in `scene`;
//                  scene sidecars select phases and place them in the anchor frame.
//                  The review uses a common grade plane, not the app terrain.
//   enclosures     optional native enclosure ids belonging to the anchor in `scene`;
//                  app geometry on that same plane, with source/renderer freshness.
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
//   mirrored       optional (default false): the print is laterally reversed; the pixels
//                  above are the picture's turned back, and the side-by-side turns it back
//   sun_uvy        optional: the direction the photograph's sunlight comes from, [u, v, y]
//                  in the same frame (T-2369: which walls are lit and where shadows fall is
//                  part of what is compared); the review render's default east-north-east sun
//                  otherwise
//   sky            optional: "sun" (default) or "overcast" (T-2848) — a picture with no cast
//                  shadow anywhere in it (wet street, flat walls, lamp posts throwing nothing)
//                  was taken under a sky, not a sun: the render then lights from a soft
//                  key at sun_uvy (straight overhead when absent) that casts no shadow, and
//                  lets the sky do most of the work, so a face the picture shows unlit is not
//                  raked by the review sun
//   flora          optional planting drawn with the app's own grown plants (T-1881): lots of
//                  the scene's front yards and the parkway trees near the anchor, in the
//                  picture's season (tools/photo_match_flora.mjs)
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
import {renderGroup, groupReview} from './photo_match_group.mjs';
import {enclosureReview} from './photo_match_enclosures.mjs';
import {floraReview} from './photo_match_flora.mjs';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const {chromium} = require('playwright');
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const camFile = args.find(a => a.endsWith('.json'));
if (!camFile) { console.error('usage: node tools/photo_match.mjs <camera.json> [--glb <path>] [--out <dir>]'); process.exit(2); }
const cam = JSON.parse(fs.readFileSync(camFile, 'utf8'));
if (cam.pixel_aspect !== undefined && (!Number.isFinite(cam.pixel_aspect) || cam.pixel_aspect<=0.5 || cam.pixel_aspect>=2)) throw Error('pixel_aspect must be finite and between 0.5 and 2');
// T-1888: a print laterally reversed (1834's, its camera only fits the 1911 sheet turned the
// right way round): the camera's pixels are the corrected picture's, and the side-by-side shows
// the committed copy, unaltered, turned back
if (cam.mirrored !== undefined && typeof cam.mirrored !== 'boolean') throw Error('mirrored must be true or false');
if (cam.sky !== undefined && !['sun', 'overcast'].includes(cam.sky)) throw Error('sky must be "sun" or "overcast"');
if (cam.near_m !== undefined && (!Number.isFinite(cam.near_m) || cam.near_m<=0 || cam.near_m>=500)) throw Error('near_m must be finite and between 0 and the 500 m far plane');
if (cam.clip_planes !== undefined && (!Array.isArray(cam.clip_planes) || cam.clip_planes.some(p => !p || !Array.isArray(p.normal) || p.normal.length !== 3 || !p.normal.every(Number.isFinite) || Math.abs(Math.hypot(...p.normal)-1)>1e-6 || !Number.isFinite(p.constant)))) throw Error('clip_planes requires finite unit [east,north,up] normals and constants in metres');
const members = renderGroup(root, cam, {glb: opt('--glb')});
const glb = members[0].glb;
const group = members.length > 1 ? groupReview(root, members) : null;
const enclosures = enclosureReview(root, cam);
const flora = floraReview(root, cam);
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
const c=${JSON.stringify({W, H, cx, cy, f, aspect: cam.pixel_aspect ?? 1, eye: cam.eye, yaw: cam.yaw_deg, basis: cam.basis_right_up_forward || null, near: cam.near_m ?? 0.1, sun: cam.sun_uvy || null, overcast: cam.sky === 'overcast', clips: cam.clip_planes || [], enclosures: enclosures ? {anchor: enclosures.anchor, ids: cam.enclosures} : null, flora: flora ? {anchor: flora.anchor, scene: cam.scene, season: flora.season, yards: !!flora.docs.front_yards, street: !!flora.docs.street_trees} : null, members: members.map(m => ({...m, glb: '/' + m.glb.replace(/\\/g, '/')}))})};
const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setPixelRatio(1);r.setSize(c.W,c.H);
r.outputColorSpace=THREE.SRGBColorSpace;r.toneMapping=THREE.ACESFilmicToneMapping;r.shadowMap.enabled=true;
r.clippingPlanes=c.clips.map(p=>new THREE.Plane(new THREE.Vector3(p.normal[0],p.normal[2],-p.normal[1]),p.constant));
document.body.appendChild(r.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0xe8ecef);
s.add(new THREE.HemisphereLight(0xdfe8f0,0x8a8070,c.overcast?2.6:1.1));
const sun=new THREE.DirectionalLight(c.overcast?0xf2f2f0:0xfff4e0,c.overcast?0.9:2.4);sun.castShadow=!c.overcast;
if(c.sun){const k=75/Math.hypot(...c.sun);sun.position.set(c.sun[0]*k,c.sun[2]*k,-c.sun[1]*k);}else if(c.overcast)sun.position.set(0,75,0);else sun.position.set(60,45,-20);
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
Promise.all(c.members.map(async member=>{
 const x=await l.loadAsync(member.glb);
 x.scene.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;for(const m of (Array.isArray(o.material)?o.material:[o.material]))tintKeithStone(m,{id:member.structure_id});}});
 const placed=new THREE.Group();placed.position.fromArray(member.position);placed.rotation.y=member.rotation_y;
 placed.add(x.scene);return placed;
})).then(async placed=>{
 for(const object of placed)s.add(object);
 if(c.enclosures){
  const {createEnclosures}=await import('/renderers/web/js/enclosures.js');
  const problems=[];
  const layer=await createEnclosures({dataBase:new URL('/__photo_enclosures/',location.href),
   terrain:{surfaceHeight:()=>0,isWater:()=>false},problems,detail:'full'});
  if(problems.length||layer.records.length!==c.enclosures.ids.length||!layer.census.posts)
   throw Error('native enclosure review failed: '+problems.join('; '));
  const anchor=c.enclosures.anchor, frame=new THREE.Group();
  frame.rotation.y=anchor.rotation_deg*Math.PI/180;
  layer.group.position.set(-anchor.local_e,0,anchor.local_n);
  frame.add(layer.group);s.add(frame);
 }
 if(c.flora){
  // the app's own grown plants, in the anchor's frame as the enclosures are; their levels
  // are dealt from the eye as it stands in the plants' own frame
  const a=c.flora.anchor,frame=new THREE.Group(),inner=new THREE.Group();
  frame.rotation.y=a.rotation_deg*Math.PI/180;inner.position.set(-a.local_e,0,a.local_n);frame.add(inner);s.add(frame);
  const problems=[],terrain={surfaceHeight:()=>0,isWater:()=>false},base=new URL('/__photo_flora/',location.href);
  let mats=null;
  const layers=[];
  if(c.flora.street){
   const {createStreetTrees}=await import('/renderers/web/js/street-trees.js');
   const st=await createStreetTrees({dataBase:base,sceneId:c.flora.scene,terrain,problems,mode:c.flora.season});
   if(!st.stats.trees)throw Error('flora: no parkway tree drawn: '+problems.join('; '));
   mats=st.materials??null;layers.push(st);
  }
  if(c.flora.yards){
   const {createFrontYards}=await import('/renderers/web/js/front-yards.js');
   const fy=await createFrontYards({dataBase:base,sceneId:c.flora.scene,terrain,problems,mode:c.flora.season,grownMaterials:mats});
   if(!fy.stats.lots)throw Error('flora: no front yard drawn: '+problems.join('; '));
   layers.push(fy);
  }
  if(problems.length)throw Error('flora review failed: '+problems.join('; '));
  s.updateMatrixWorld(true);cam.updateMatrixWorld(true);
  const eye={position:inner.worldToLocal(cam.getWorldPosition(new THREE.Vector3()))};
  for(const l of layers){inner.add(l.group);l.update(0,eye);l.settle(eye);}
  s.traverse(o=>{if(o.isMesh||o.isInstancedMesh)o.castShadow=o.receiveShadow=true;});
 }
 r.render(s,cam);window.__done=true;
})
 .catch(e=>{window.__error=String(e);});
</script>`;
const types = {'.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ktx2': 'image/ktx2', '.webp': 'image/webp'};
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/__photo_match.html') { res.writeHead(200, {'Content-Type': 'text/html'}); return res.end(page_html); }
  if (u === '/__photo') { res.writeHead(200, {'Content-Type': 'image/jpeg'}); return fs.createReadStream(photo).pipe(res); }
  if (flora && u.startsWith('/__photo_flora/')) {
    const m = /^\/__photo_flora\/(front_yards|street_trees)\/([a-z0-9_]+)\.json$/.exec(u);
    if (!m || m[2] !== cam.scene || !flora.docs[m[1]]) { res.writeHead(404); return res.end(); }
    res.writeHead(200, {'Content-Type': 'application/json'});
    return res.end(JSON.stringify(flora.docs[m[1]]));
  }
  if (enclosures && u.startsWith('/__photo_enclosures/enclosures/')) {
    const file = u.slice('/__photo_enclosures/enclosures/'.length);
    if (file === 'index.json') {
      res.writeHead(200, {'Content-Type': 'application/json'});
      return res.end(JSON.stringify(enclosures.index));
    }
    const record = enclosures.records.find(value => path.basename(value.file) === file);
    if (!record) { res.writeHead(404); return res.end(); }
    res.writeHead(200, {'Content-Type': 'application/json'});
    return fs.createReadStream(path.join(root, record.file)).pipe(res);
  }
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
  await page.goto(base + '/__photo_match.html?assets=/assets/', {waitUntil: 'domcontentloaded', timeout: 180000});
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
  await page.setContent(`<body style="margin:0;background:#fff;display:flex;gap:24px"><img src="${base}/__photo" style="width:${W}px;height:${H}px${cam.mirrored ? ';transform:scaleX(-1)' : ''}"><img src="data:image/png;base64,${png}" style="width:${W}px;height:${H}px"></body>`);
  await page.waitForFunction(() => [...document.images].every(i => i.complete && i.naturalWidth));
  await page.screenshot({path: side, type: 'jpeg', quality: 82});
  // the match record the image gate reads (T-2368)
  const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  const matchFile = camFile.replace(/\.json$/, '.match.json');
  const was = fs.existsSync(matchFile) ? JSON.parse(fs.readFileSync(matchFile, 'utf8')) : {};
  const glbSha = sha(glb), camSha = sha(camFile), photoSha = sha(photo);
  const same = was.glb_sha256 === glbSha && was.camera_sha256 === camSha
    && was.photo_sha256 === photoSha && (!group || was.group_sha256 === group.group_sha256)
    && (!enclosures || was.enclosures_sha256 === enclosures.review.enclosures_sha256)
    && (!flora || was.flora_sha256 === flora.review.flora_sha256);
  const rec = {
    structure_id: cam.structure_id, view: name, glb: glb.replace(/\\/g, '/'), glb_sha256: glbSha, camera_sha256: camSha,
    photo_sha256: photoSha,
    ...(group || {}),
    ...(enclosures?.review || {}),
    ...(flora?.review || {}),
    side_by_side: path.relative(root, side).replace(/\\/g, '/'),
    verdict: same && was.verdict ? was.verdict : 'unreviewed',
    differences: Array.isArray(was.differences) ? was.differences : [],
    _how: 'verdict is unreviewed | differs | matches, set by whoever compared the side-by-side with the picture; each difference is {what, status: open | fixed | not shown | within tolerance | owner ruling} — open only if a street visitor would notice it (over about 1 ft, missing, mis-shaped, miscounted, wrong material or colour), else within tolerance (T-3153); owner ruling where the owner asked the build to depart from the picture (T-3236). A ticket whose ## Image gate names this building does not close while it is not "matches" (tools/image_gate.mjs).',
  };
  fs.writeFileSync(matchFile, JSON.stringify(rec, null, 2) + '\n');
  console.log(`photo_match: ${glb}\n  ${render}\n  ${side}\n  ${matchFile} (${rec.verdict}${same ? '' : was.verdict ? ' — a rendered input changed; look again' : ''})`);
} finally { await browser.close(); server.close(); }
