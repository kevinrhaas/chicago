// Controlled diagnostic of the real grown-tree pipeline, without town geometry.
// QA_OUT=/path QA_TAG=before|after QA_BEFORE=/path/to/old/js QA_DETAIL=full|balanced|light
// This fixture is not a historical scene or a hardware FPS benchmark.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url), { chromium } = require('playwright');
const root = path.resolve(new URL('..', import.meta.url).pathname);
const out = process.env.QA_OUT, tag = process.env.QA_TAG || 'after', detail = process.env.QA_DETAIL || 'full';
const season = process.env.QA_SEASON || 'summer';
if (!out) throw Error('QA_OUT required');
fs.mkdirSync(out, { recursive: true });
const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<style>body{margin:0;background:#b4cadb}canvas{display:block}</style><link rel="icon" href="data:,"><script type="importmap">{"imports":{"three":"/vendor/three-0.185.1/three.module.js","three/addons/":"/vendor/three-0.185.1/addons/"}}</script>`);
    return;
  }
  let file = req.url.startsWith('/assets/') ? path.join(root, req.url)
    : path.join(root, 'renderers/web', req.url);
  if (process.env.QA_BEFORE && /\/js\/[^/]+\.js$/.test(file)) {
    const old = path.join(process.env.QA_BEFORE, path.basename(file));
    if (fs.existsSync(old)) file = old;
  }
  if (!fs.existsSync(file)) { res.writeHead(404); res.end('missing'); return; }
  res.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const results = [];
try {
  const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  for (const speciesId of (process.env.QA_SPECIES || 'ulmus_americana_vase,quercus_alba,salix_nigra').split(',')) {
    const result = await page.evaluate(async ({ speciesId, detail, season }) => {
      const THREE = await import('three');
      const { TreeInstances, createGrownTreeMaterials } = await import('/js/tree-instances.js');
      const { patchTreeWind } = await import('/js/tree-surface.js');
      const { EVERGREEN_BELOW_V } = await import('/js/tree-model.js');
      const { applySeasonLook, patchFoliage, patchSeason, SEASON_CROWN } = await import('/js/season.js');
      applySeasonLook(season);
      const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
      renderer.setSize(1000, 800); renderer.shadowMap.enabled = true;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      document.body.replaceChildren(renderer.domElement);
      const scene = new THREE.Scene(); scene.background = new THREE.Color(0xb4cadb);
      scene.add(new THREE.HemisphereLight(0xdcecff, 0x5b6549, 2.2));
      const sun = new THREE.DirectionalLight(0xfff2d6, 3.0);
      sun.position.set(-12, 20, -8); sun.castShadow = true;
      Object.assign(sun.shadow.camera, { left: -18, right: 18, top: 20, bottom: -20, near: 0.1, far: 80 });
      sun.shadow.mapSize.set(1024, 1024); sun.shadow.normalBias = 0.025;
      scene.add(sun);
      const ground = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), new THREE.MeshStandardMaterial({ color: 0x69794f, roughness: 1 }));
      ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
      if (season !== 'summer') patchSeason(ground.material, 1);
      const camera = new THREE.PerspectiveCamera(74, 1.25, 0.1, 120);
      camera.position.set(7, 3, 10); camera.lookAt(0, 9, 0);
      const mats = await createGrownTreeMaterials({ assetBase: new URL('/assets/', location.href),
        uWind: { value: 0 }, patchWind: patchTreeWind, lowSpec: detail === 'light' });
      if (season !== 'summer') patchFoliage(mats.leafMat, 0, { evergreenBelowV: EVERGREEN_BELOW_V ?? 0.2 });
      const trees = new TreeInstances({ level: detail, variants: () => 1 });
      trees.add({ speciesId, arch: speciesId, common: speciesId, form: 'open', h: [16, 16], dbh: [0.45, 0.45],
        crownW: [11, 11], dark: 0x345028, light: 0x738c4b, bark: 0x554837,
        evergreen: /juniperus|thuja|pinus|picea/.test(speciesId) }, 0, 0, 0, 1, { yaw: 0, variant: 0 });
      const rig = await trees.build({ ...mats, season: SEASON_CROWN[season] }); scene.add(rig.group); rig.update(camera.position); rig.settle();
      const times = [], gl = renderer.getContext();
      for (let i = 0; i < 9; i++) {
        renderer.info.reset(); const t = performance.now(); renderer.render(scene, camera); gl.finish();
        if (i > 1) times.push(performance.now() - t);
      }
      times.sort((a, b) => a - b);
      const buffers = new Set();
      scene.traverse(o => {
        if (!o.geometry) return;
        for (const a of Object.values(o.geometry.attributes)) if (a.array) buffers.add(a.array.buffer);
        if (o.geometry.index?.array) buffers.add(o.geometry.index.array.buffer);
      });
      const row = { speciesId, detail, season, triangles: renderer.info.render.triangles, calls: renderer.info.render.calls,
        memory: { ...renderer.info.memory }, frameMs: times[Math.floor(times.length / 2)], treeStats: rig.stats };
      row.geometryBytes = [...buffers].reduce((n, b) => n + b.byteLength, 0);
      window.galleryDispose = () => { rig.dispose(); mats.dispose(); ground.geometry.dispose(); ground.material.dispose(); renderer.dispose(); };
      return row;
    }, { speciesId, detail, season });
    result.image = `${tag}-gallery-${speciesId}-${detail}-${season}.jpg`;
    console.log('rendered', JSON.stringify(result));
    await page.screenshot({ path: path.join(out, result.image), type: 'jpeg', quality: 92, timeout: 400000 });
    await page.evaluate(() => window.galleryDispose());
    results.push(result); console.log(JSON.stringify(result));
  }
  if (errors.length) throw Error(errors.join('\n').slice(0, 6000));
  fs.writeFileSync(path.join(out, `${tag}-gallery-${detail}-${season}.json`), JSON.stringify(results, null, 2));
} finally { await browser.close(); server.close(); }
