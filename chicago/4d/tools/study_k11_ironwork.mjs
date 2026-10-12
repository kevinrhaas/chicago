#!/usr/bin/env node
/**
 * The K11 ironwork kit's study (T-2318): every variant of the specimen GLB seen in the
 * browser, through the vendored three.js the walkthrough draws with, near (2-5 m) and at
 * walking distance (8 m, where a bar too thin to hold a pixel would shimmer), in raking
 * and diffuse light. Adapted from tools/study_k10_cornices.mjs (T-2316), the same rig and
 * the same lights, with the 5 m square-on row moved out to 8 m.
 *
 *   node tools/study_k11_ironwork.mjs
 *
 * writes docs/RESEARCH/k11-ironwork-kit/study.jpg (one column per variant, four rows:
 * 2 m in a raking sun, 3.5 m oblique under a diffuse sky, 8 m square-on under the same
 * sky, 4 m from above) and costs.json (per variant: triangles, vertices, draw calls; for the whole
 * board: bytes, draw calls and frame time at 1280x800 and 390x780).
 *
 * It writes only those two files and is run by hand after the generator; no gate step
 * runs it (tools/check_ironwork_kit.py is the gate). A study of the kit, not the scene:
 * the scene's first K11 fence is T-2319's.
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
const OUT = path.join(ROOT, 'docs', 'RESEARCH', 'k11-ironwork-kit');
const GLB = '/docs/RESEARCH/k11-ironwork-kit/k11_ironwork_kit.glb';
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
const nodes = gltf.scene.children;
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

// the variant's own frame: the node's origin is its base socket, its focus the feature studied
function target(n) {
  const o = n.userData.origin, f = n.userData.focus;
  return { x: o[0] + f[0], y: o[1] + f[1], z: o[2] + f[2] };
}
nodes.forEach((n) => { n.userData.origin = n.userData.origin || [0, 0, 0]; });

const ROWS = [
  { name: '2 m, raking sun', dist: 2.0, yaw: 22, pitch: 0, light: 'raking' },
  { name: '3.5 m, oblique, diffuse', dist: 3.5, yaw: 40, pitch: 0, light: 'diffuse' },
  { name: '8 m, walking distance, diffuse', dist: 8.0, yaw: 0, pitch: 0, light: 'diffuse' },
  { name: '4 m, from above, diffuse', dist: 4.0, yaw: 30, pitch: 40, light: 'diffuse' },
];
const W = nodes.length * TILE, H = ROWS.length * TILE;
renderer.setSize(W, H, false);
renderer.setScissorTest(true);
const cam = new THREE.PerspectiveCamera(50, 1, 0.05, 100);

function setLight(kind, t) {
  if (kind === 'raking') {
    // a low sun from the left, 12 degrees off the wall plane: it finds every reveal and rail
    const a = THREE.MathUtils.degToRad(12);
    sun.position.set(t.x - 6 * Math.cos(a), t.y + 3.2, t.z + 6 * Math.sin(a));
    sun.target.position.set(t.x, t.y, t.z);
    sun.intensity = 3.2; hemi.intensity = 0.55; scene.environmentIntensity = 0.5;
    const sc = sun.shadow.camera; sc.left = -3; sc.right = 3; sc.top = 3; sc.bottom = -3; sc.near = 0.5; sc.far = 20;
    sc.updateProjectionMatrix();
  } else {
    sun.intensity = 0.0; hemi.intensity = 2.2; scene.environmentIntensity = 1.0;
  }
}

ROWS.forEach((row, r) => {
  nodes.forEach((n, c) => {
    const t = target(n);
    setLight(row.light, t);
    const yaw = THREE.MathUtils.degToRad(row.yaw), pit = THREE.MathUtils.degToRad(row.pitch);
    const h = row.dist * Math.cos(pit);
    cam.position.set(t.x + h * Math.sin(yaw), Math.max(t.y + row.dist * Math.sin(pit), 0.9), t.z + h * Math.cos(yaw));
    cam.lookAt(t.x, t.y, t.z);
    cam.fov = row.dist <= 2 ? 62 : row.dist >= 8 ? 50 : 46;
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
nodes.forEach((n, c) => g.fillText(n.userData.component_id.replace(/^k11\./, ''), c * TILE + 8, 19));
g.font = '12px sans-serif'; g.fillStyle = 'rgba(255,255,255,0.85)';
ROWS.forEach((row, r) => g.fillText(row.name, 8, 28 + r * TILE + 18));
document.body.appendChild(out);
out.id = 'study';

// costs: per variant from the file, for the board from the renderer
const per = nodes.map((n) => {
  let tris = 0, verts = 0, calls = 0;
  n.traverse((o) => {
    if (!o.isMesh) return;
    calls += 1;
    verts += o.geometry.attributes.position.count;
    tris += o.geometry.index.count / 3;
  });
  return { id: n.userData.component_id, triangles_trim: n.userData.triangles_trim, pieces: n.userData.pieces,
           triangles_with_board: tris, vertices_with_board: verts, draw_calls: calls };
});
async function frameCost(w, h) {
  renderer.setScissorTest(false);
  renderer.setSize(w, h, false);
  renderer.setViewport(0, 0, w, h);
  cam.aspect = w / h; cam.fov = 50; cam.updateProjectionMatrix();
  const bb = new THREE.Box3().setFromObject(gltf.scene);
  const cx = (bb.min.x + bb.max.x) / 2;
  cam.position.set(cx, 1.4, 0.75 * (bb.max.x - bb.min.x) / Math.tan(THREE.MathUtils.degToRad(25)) / Math.max(1, w / h));
  cam.lookAt(cx, 1.0, 0);
  setLight('diffuse', { x: cx, y: 1, z: 0 });
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
  if (url === '/__k11_study.html') {
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
  await page.goto(`http://127.0.0.1:${port}/__k11_study.html`);
  await page.waitForFunction(() => window.__study, null, { timeout: 240_000 });
  if (errors.length) throw new Error(`page errors: ${errors.join('; ')}`);
  const shot = await page.locator('#study').screenshot({ type: 'jpeg', quality: 86 });
  fs.writeFileSync(path.join(OUT, 'study.jpg'), shot);
  const { per, board } = await page.evaluate(() => window.__study);
  const glbBytes = fs.statSync(path.join(ROOT, GLB)).size;
  const costs = {
    _doc: 'Measured by tools/study_k11_ironwork.mjs on the specimen GLB. Triangles and draw calls are exact; frame_ms is headless Chromium on a software rasteriser (SwiftShader), a relative figure for comparing kit revisions, not a device frame time.',
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
