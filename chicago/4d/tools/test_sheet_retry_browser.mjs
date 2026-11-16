#!/usr/bin/env node
/**
 * T-3617 — a house whose shared texture sheet is dropped still gets its picture.
 *
 *     node tools/test_sheet_retry_browser.mjs [--out DIR]
 *
 * The real loader in real Chromium (SwiftShader WebGL, the real KTX2 transcoder):
 * `loadScene` over a one-house fixture whose GLB names its picture as an external
 * `sheets/<hash>.ktx2` buffer, as every published Prairie Avenue house does since
 * T-3232, served by a local server that refuses the sheet's first N requests.
 *
 *   drop 0 ......... textured, no retry, no problem line
 *   drop 2 ......... textured on the sheet's third ask, inside one read
 *                    (published-assets.js fetchSheetBytes)
 *   drop 5 ......... the first read's four asks all fail; the house is read again
 *                    and textured (scene-loader.js TEXTURE_REREADS_MS), and the
 *                    problem list says it took a second read
 *   drop all ....... untextured after every read: `texturesLost` names the sheet
 *                    and the problem list says the surface draws untextured
 *
 * Before T-3617 every case but `drop 0` drew the house white with no problem line:
 * GLTFLoader catches a texture that fails and builds the material without it.
 * Not a check.sh step (a browser, about a minute); run it when touching
 * published-assets.js or scene-loader.js's texture path. `--out` writes a picture.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const args = process.argv.slice(2);
const out = args.includes('--out') ? path.resolve(args[args.indexOf('--out') + 1]) : null;
const sha = (b) => createHash('sha256').update(b).digest('hex');
const sheet = fs.readFileSync(path.join(ROOT,
  'assets/textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor.ktx2'));
const sheetName = `${sha(sheet).slice(0, 16)}.ktx2`;

function house() {
  const geometry = Buffer.from(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, -1, 0, 1, 1, 0, -1, 1, 0,
    0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0]).buffer);
  const json = { asset: { version: '2.0' }, extensionsUsed: ['KHR_texture_basisu'], extensionsRequired: ['KHR_texture_basisu'],
    buffers: [{ byteLength: geometry.length }, { uri: `sheets/${sheetName}`, byteLength: sheet.length }],
    bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 72 }, { buffer: 0, byteOffset: 72, byteLength: 48 },
      { buffer: 1, byteOffset: 0, byteLength: sheet.length }],
    accessors: [{ bufferView: 0, componentType: 5126, count: 6, type: 'VEC3', min: [-1, -1, 0], max: [1, 1, 0] },
      { bufferView: 1, componentType: 5126, count: 6, type: 'VEC2' }],
    images: [{ bufferView: 2, mimeType: 'image/ktx2', name: 'limestone_basecolor' }],
    textures: [{ extensions: { KHR_texture_basisu: { source: 0 } } }],
    materials: [{ name: 'limestone', pbrMetallicRoughness: { baseColorTexture: { index: 0 }, metallicFactor: 0, roughnessFactor: 1 } }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, TEXCOORD_0: 1 }, material: 0 }] }],
    nodes: [{ mesh: 0 }], scenes: [{ nodes: [0] }], scene: 0 };
  let j = Buffer.from(JSON.stringify(json)); j = Buffer.concat([j, Buffer.alloc((4 - j.length % 4) % 4, 32)]);
  const h = Buffer.alloc(20); h.writeUInt32LE(0x46546c67); h.writeUInt32LE(2, 4);
  h.writeUInt32LE(28 + j.length + geometry.length, 8); h.writeUInt32LE(j.length, 12); h.writeUInt32LE(0x4e4f534a, 16);
  const b = Buffer.alloc(8); b.writeUInt32LE(geometry.length); b.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([h, j, b, geometry]);
}

const site = fs.mkdtempSync(path.join(os.tmpdir(), 'sheet-retry-'));
const put = (rel, bytes) => { const f = path.join(site, rel); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, bytes); };
fs.cpSync(path.join(ROOT, 'renderers/web/js'), path.join(site, 'walk/js'), { recursive: true });
fs.cpSync(path.join(ROOT, 'renderers/web/vendor/three-0.185.1'), path.join(site, 'walk/vendor/three-0.185.1'), { recursive: true });
put('data/gltf/house.glb', house());
put(`data/gltf/sheets/${sheetName}`, sheet);
put('data/scenes/1904.json', JSON.stringify({ id: '1904' }));
put('data/datum.json', '{}');
put('data/sidecars/1904/index.json', JSON.stringify({ structures: ['fixture_house'] }));
put('data/sidecars/1904/fixture_house.json', JSON.stringify({ id: 'fixture_house', asset: 'gltf/house.glb' }));
put('walk/index.html', `<!doctype html><html><head>
<script type="importmap">{"imports":{"three":"./vendor/three-0.185.1/three.module.js","three/addons/":"./vendor/three-0.185.1/addons/"}}</script>
</head><body style="margin:0;background:#202020"><script type="module">
import * as THREE from 'three';
import { initKTX2 } from './js/ktx2.js';
import { loadScene } from './js/scene-loader.js';
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setSize(200, 200); document.body.append(renderer.domElement);
initKTX2(renderer, { textures: 'full' });
const bases = { dataBase: new URL('../data/', location.href), assetBase: new URL('../data/', location.href), sourceAssetLayout: false };
window.run = async () => {
  const t0 = performance.now();
  const loaded = await loadScene('1904', bases, { detail: 'full', keepAssetBytes: false });
  const row = loaded.registry.get('fixture_house');
  const material = row.gltf?.scene.children[0].material;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x202020);
  scene.add(row.gltf.scene); scene.add(new THREE.AmbientLight(0xffffff, 3));
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 10); camera.position.z = 2.6; renderer.render(scene, camera);
  return { textured: !!material?.map, texturesLost: row.texturesLost, problems: loaded.problems,
    sheetRetries: loaded.sheetRetries, seconds: +((performance.now() - t0) / 1000).toFixed(1) };
};
window.ready = true;
</script></body></html>`);

let refuse = 0;
let asked = 0;
const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  if (u.pathname.includes('/sheets/')) { asked++; if (refuse > 0) { refuse--; res.writeHead(503); res.end(); return; } }
  const file = path.join(site, decodeURIComponent(u.pathname));
  if (!file.startsWith(site) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  const type = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.wasm': 'application/wasm' }[path.extname(file)];
  res.writeHead(200, { 'Content-Type': type ?? 'application/octet-stream', 'Cache-Control': 'no-store' });
  res.end(fs.readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const fail = [];
const ok = (cond, label, got) => { console.log(`${cond ? '   ok  ' : '  FAIL '} ${label}`); if (!cond) fail.push(`${label}: ${JSON.stringify(got)}`); };
try {
  const cases = [['drop 0', 0], ['drop 2', 2], ['drop 5', 5], ['drop all', 1e9]];
  for (const [label, n] of cases) {
    const page = await browser.newPage({ viewport: { width: 200, height: 200 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`${origin}/walk/index.html`);
    await page.waitForFunction(() => window.ready === true);
    refuse = n; asked = 0;
    const got = await page.evaluate(() => window.run());
    refuse = 0;
    const lines = got.problems.filter((p) => p.startsWith('fixture_house:'));
    console.log(`${label}: ${JSON.stringify({ ...got, problems: lines, asked })}`);
    ok(errors.length === 0, `${label}: no page errors`, errors);
    if (label === 'drop all') {
      ok(!got.textured && got.texturesLost?.[0] === 'limestone_basecolor', `${label}: the house is flagged with the picture it lacks`, got);
      ok(lines.some((p) => /1 of its pictures did not arrive after 3 reads \(limestone_basecolor\)/.test(p)), `${label}: the problem list names it`, lines);
      ok(asked === 12, `${label}: three reads of four asks, then it stops`, asked);
    } else {
      ok(got.textured && got.texturesLost === null, `${label}: the house is textured`, got);
      ok(label === 'drop 5' ? lines.some((p) => /did on read 2/.test(p)) : lines.length === 0,
        `${label}: ${label === 'drop 5' ? 'the second read is reported' : 'no problem line'}`, lines);
    }
    if (out) {
      fs.mkdirSync(out, { recursive: true });
      await page.screenshot({ path: path.join(out, `fixture-${label.replace(' ', '-')}.png`) });
    }
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
  fs.rmSync(site, { recursive: true, force: true });
}
if (fail.length) { for (const f of fail) console.error(`test_sheet_retry_browser FAIL: ${f}`); process.exit(1); }
console.log('test_sheet_retry_browser: ok (a dropped sheet is asked again, a house is read again, a lost picture is named)');
