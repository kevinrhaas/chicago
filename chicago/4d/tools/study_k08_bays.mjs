#!/usr/bin/env node
/**
 * The K08 bay kit's study (T-2307): every variant of the specimen GLB seen in the
 * browser, through the vendored three.js the walkthrough draws with, at the distances
 * the ticket names (2-5 m) and in a raking and a diffuse light, with the whole
 * elevation and the light tier from further off.
 *
 *   node tools/study_k08_bays.mjs
 *
 * writes docs/RESEARCH/k08-bay-kit/study.jpg (one column per variant, four rows:
 * 2.5 m at the front window in a raking sun, 5 m oblique under a diffuse sky, the
 * whole elevation at 16 m in a raking sun, and the light tier at 16 m oblique) and
 * costs.json (per variant and tier: triangles, vertices, draw calls; for the whole
 * board: bytes, draw calls and frame time at 1280x800 and 390x780).
 *
 * It writes only those two files and is run by hand after the generator; no gate step
 * runs it (tools/check_bay_kit.py is the gate). A study of the kit, not the scene: the
 * scene's first K08 bays are T-2308's.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(ROOT, 'docs', 'RESEARCH', 'k08-bay-kit');
const GLB = '/docs/RESEARCH/k08-bay-kit/k08_bay_kit.glb';
const THREE = '/renderers/web/vendor/three-0.185.1';
const TILE = 300;

const PAGE = `<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{"imports":{"three":"${THREE}/three.module.js"}}</script>
<style>html,body{margin:0;background:#111}canvas{display:block}</style></head><body>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from '${THREE}/addons/loaders/GLTFLoader.js';
const TILE = ${TILE};
const gltf = await new GLTFLoader().loadAsync('${GLB}');
const all = gltf.scene.children;
const nodes = all.filter((n) => n.userData.tier === 'full');
const light = all.filter((n) => n.userData.tier === 'light');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

// a sky to reflect: a gradient sphere baked to a PMREM, so glass shows a sky, not black
function skyScene() {
  const s = new THREE.Scene();
  const g = new THREE.SphereGeometry(50, 32, 16);
  const c = [];
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const t = THREE.MathUtils.clamp(p.getY(i) / 50, -1, 1);
    const col = t > 0 ? new THREE.Color(0.80, 0.86, 0.95).lerp(new THREE.Color(0.35, 0.52, 0.80), t)
                      : new THREE.Color(0.80, 0.86, 0.95).lerp(new THREE.Color(0.28, 0.25, 0.21), -t * 3);
    c.push(col.r, col.g, col.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
  s.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  return s;
}
const pmrem = new THREE.PMREMGenerator(renderer);
const env = pmrem.fromScene(skyScene(), 0.02).texture;

const scene = new THREE.Scene();
scene.add(gltf.scene);
scene.environment = env;
scene.background = new THREE.Color(0.62, 0.70, 0.80);
gltf.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

const sun = new THREE.DirectionalLight(0xfff1dc, 3.2);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.01;
const hemi = new THREE.HemisphereLight(0xdfe8f5, 0x4a4238, 1.6);
scene.add(sun, sun.target, hemi);

// a variant's own frame: the node's translation, its plan's reach and its eave
function frameOf(n) {
  const s = n.userData.sockets;
  const x = n.position.x + (s.junction_left[0] + s.junction_right[0]) / 2;
  const reach = n.userData.plan.projection_m;
  return { x, reach, base: s.base[1], eave: s.eave[1], top: n.userData.measured.roof.apex ? n.userData.measured.roof.apex[1] : s.eave[1] + 1.5 };
}

const ROWS = [
  { name: '2.5 m, front window, raking sun', light: 'raking', set: 'full',
    cam: (f) => ({ dist: 2.5, yaw: 24, ty: f.base + 0.1 + (f.base > 0 ? 1.7 : 2.0), tz: f.reach, fov: 64 }) },
  { name: '5 m, oblique, diffuse', light: 'diffuse', set: 'full',
    cam: (f) => ({ dist: 5.0, yaw: 38, ty: f.base + 2.6, tz: f.reach * 0.6, fov: 72 }) },
  { name: 'whole, 16 m, raking sun', light: 'raking', set: 'full',
    cam: (f) => ({ dist: 16.0, yaw: 18, ty: (f.base + f.top) / 2 - 0.5, tz: 0, fov: 52 }) },
  { name: 'light tier, 16 m, diffuse', light: 'diffuse', set: 'light',
    cam: (f) => ({ dist: 16.0, yaw: 18, ty: (f.base + f.top) / 2 - 0.5, tz: 0, fov: 52 }) },
];
const W = nodes.length * TILE, H = ROWS.length * TILE;
renderer.setSize(W, H, false);
renderer.setScissorTest(true);
const cam = new THREE.PerspectiveCamera(50, 1, 0.05, 200);

function setLight(kind, t) {
  if (kind === 'raking') {
    // a low sun from the left, 14 degrees off the wall plane: it finds every reveal, band and course
    const a = THREE.MathUtils.degToRad(14);
    sun.position.set(t.x - 14 * Math.cos(a), t.y + 7, 14 * Math.sin(a) + t.z);
    sun.target.position.set(t.x, t.y, t.z);
    sun.intensity = 3.2; hemi.intensity = 0.55; scene.environmentIntensity = 0.5;
    const sc = sun.shadow.camera; sc.left = -9; sc.right = 9; sc.top = 9; sc.bottom = -9; sc.near = 0.5; sc.far = 50;
    sc.updateProjectionMatrix();
  } else {
    sun.intensity = 0.0; hemi.intensity = 2.2; scene.environmentIntensity = 1.0;
  }
}

ROWS.forEach((row, r) => {
  const set = row.set === 'full' ? nodes : light;
  set.forEach((n, c) => {
    const f = frameOf(n);
    const k = row.cam(f);
    const t = { x: f.x, y: k.ty, z: k.tz };
    setLight(row.light, t);
    const yaw = THREE.MathUtils.degToRad(k.yaw);
    cam.position.set(t.x + k.dist * Math.sin(yaw), Math.max(k.ty, 1.0), t.z + k.dist * Math.cos(yaw));
    cam.lookAt(t.x, t.y, t.z);
    cam.fov = k.fov;
    cam.updateProjectionMatrix();
    const vy = H - (r + 1) * TILE;
    renderer.setViewport(c * TILE, vy, TILE, TILE);
    renderer.setScissor(c * TILE, vy, TILE, TILE);
    renderer.render(scene, cam);
  });
});

const out = document.createElement('canvas');
out.width = W; out.height = H + 28;
const g = out.getContext('2d');
g.fillStyle = '#16181b'; g.fillRect(0, 0, out.width, out.height);
g.drawImage(renderer.domElement, 0, 28);
g.font = '600 13px sans-serif'; g.fillStyle = '#e9e4da';
nodes.forEach((n, c) => g.fillText(n.userData.component_id.replace('k08.', ''), c * TILE + 8, 19));
g.font = '12px sans-serif'; g.fillStyle = 'rgba(255,255,255,0.85)';
ROWS.forEach((row, r) => g.fillText(row.name, 8, 28 + r * TILE + 18));
document.body.appendChild(out);
out.id = 'study';

// costs: per opening from the file, for the board from the renderer
const per = all.map((n) => {
  let tris = 0, verts = 0, calls = 0;
  n.traverse((o) => {
    if (!o.isMesh) return;
    calls += 1;
    verts += o.geometry.attributes.position.count;
    tris += o.geometry.index.count / 3;
  });
  return { id: n.userData.component_id, tier: n.userData.tier, triangles: n.userData.triangles,
           triangles_with_board: tris, vertices_with_board: verts, draw_calls: calls, windows: n.userData.windows };
});
async function frameCost(w, h) {
  renderer.setScissorTest(false);
  renderer.setSize(w, h, false);
  renderer.setViewport(0, 0, w, h);
  cam.aspect = w / h; cam.fov = 50; cam.updateProjectionMatrix();
  const bb = new THREE.Box3();
  nodes.forEach((n) => bb.expandByObject(n));
  light.forEach((n) => { n.visible = false; });
  const cx = (bb.min.x + bb.max.x) / 2;
  cam.position.set(cx, 6, 0.55 * (bb.max.x - bb.min.x) / Math.tan(THREE.MathUtils.degToRad(25)) / Math.max(1, w / h));
  cam.lookAt(cx, 5, 0);
  setLight('diffuse', { x: cx, y: 5, z: 0 });
  renderer.info.autoReset = true;
  const times = [];
  for (let i = 0; i < 24; i++) {
    const t0 = performance.now();
    renderer.render(scene, cam);
    renderer.getContext().finish();
    times.push(performance.now() - t0);
  }
  times.sort((a, b) => a - b);
  return { viewport: [w, h], draw_calls: renderer.info.render.calls, triangles: renderer.info.render.triangles,
           frame_ms_median: +times[12].toFixed(2), geometries: renderer.info.memory.geometries };
}
const board = { desktop: await frameCost(1280, 800), mobile: await frameCost(390, 780) };
window.__study = { per, board };
</script></body></html>`;

const TYPES = { '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.html': 'text/html' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (url === '/__k08_study.html') {
    res.writeHead(200, { 'content-type': 'text/html' }).end(PAGE);
    return;
  }
  const file = path.join(ROOT, url);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${port}/__k08_study.html`);
  await page.waitForFunction(() => window.__study, null, { timeout: 240_000 });
  if (errors.length) throw new Error(`page errors: ${errors.join('; ')}`);
  const shot = await page.locator('#study').screenshot({ type: 'jpeg', quality: 86 });
  fs.writeFileSync(path.join(OUT, 'study.jpg'), shot);
  const { per, board } = await page.evaluate(() => window.__study);
  const glbBytes = fs.statSync(path.join(ROOT, GLB)).size;
  const costs = {
    _doc: 'Measured by tools/study_k08_bays.mjs on the specimen GLB; board = the full tier only, the light tier hidden. Triangles and draw calls are exact; frame_ms is headless Chromium on a software rasteriser (SwiftShader), a relative figure for comparing kit revisions, not a device frame time.',
    specimen_bytes: glbBytes,
    variants: per,
    board,
  };
  fs.writeFileSync(path.join(OUT, 'costs.json'), JSON.stringify(costs, null, 2) + '\n');
  console.log(`wrote study.jpg (${shot.length} B) and costs.json; board desktop ${JSON.stringify(board.desktop)}`);
} finally {
  await browser.close();
  server.close();
}
