// T-3747: render real standard materials. Backlighting must be shadowed,
// disabled on wood and absent with no light. Exercise both shader variants.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = path.resolve(new URL('..', import.meta.url).pathname);
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<link rel="icon" href="data:,"><script type="importmap">{"imports":{"three":"/vendor/three-0.185.1/three.module.js","three/addons/":"/vendor/three-0.185.1/addons/"}}</script>`);
    return;
  }
  const file = path.join(root, 'renderers/web', req.url.split('?')[0]);
  if (!fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  const rows = await page.evaluate(async () => {
    const THREE = await import('three');
    const { patchLeafLight } = await import('/js/leaf-light.js');
    const { LEAF_SKY } = await import('/js/time-of-day.js');
    const { buildTreeTemplate } = await import('/js/tree-model.js');
    const { TreeInstances } = await import('/js/tree-instances.js');
    const geometry = [];
    const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
    const identical = (a, b) => ['wood', 'leaves'].every(k =>
      same(a[k].index.array, b[k].index.array)
      && Object.keys(a[k].attributes).every(n => same(a[k].attributes[n].array, b[k].attributes[n].array)));
    for (const speciesId of ['ulmus_americana', 'quercus_alba', 'salix_nigra', 'populus_deltoides', 'fraxinus_pennsylvanica', 'acer_saccharinum', 'ulmus_americana_vase']) {
      const spec = { speciesId, arch: speciesId, form: 'open', h: [16, 16] };
      const base = buildTreeTemplate(spec, 3747, 'near');
      const full = buildTreeTemplate(spec, 3747, 'near', { fullSprays: true });
      const coarse = buildTreeTemplate(spec, 3747, 'mid', { coarse: true });
      const coarseFull = buildTreeTemplate(spec, 3747, 'mid', { coarse: true, fullSprays: true });
      const bare = buildTreeTemplate(spec, 3747, 'near', { leafCover: 0 });
      const bareFull = buildTreeTemplate(spec, 3747, 'near', { leafCover: 0, fullSprays: true });
      geometry.push({ speciesId, coarseUnchanged: identical(coarse, coarseFull), bareUnchanged: identical(bare, bareFull),
        heightUnchanged: base.height === full.height && base.crownR === full.crownR && base.trunkR === full.trunkR,
        baseTriangles: (base.wood.index.count + base.leaves.index.count) / 3,
        fullTriangles: (full.wood.index.count + full.leaves.index.count) / 3 });
      for (const t of [base, full, coarse, coarseFull, bare, bareFull]) { t.wood.dispose(); t.leaves.dispose(); }
    }
    const instances = new TreeInstances({ level: 'full', variants: () => 1 });
    instances.add({ speciesId: 'quercus_alba', form: 'open', h: [6, 6] }, 0, 0, 0);
    const woodMat = new THREE.MeshStandardMaterial(), leafMat = woodMat.clone();
    const rig = await instances.build({ woodMat, leafMat });
    rig.update(new THREE.Vector3(5, 1.7, 0));
    const closeTriangles = rig.stats.triangles;
    rig.update(new THREE.Vector3(20, 1.7, 0));
    const transitioning = rig.stats.fading;
    rig.settle();
    const nearTriangles = rig.stats.triangles;
    rig.update(new THREE.Vector3(60, 1.7, 0));
    rig.settle();
    const midTriangles = rig.stats.triangles;
    const ranges = { closeTriangles, nearTriangles, midTriangles, transitioning, settled: rig.stats.fading, draws: rig.stats.drawCalls };
    rig.dispose(); woodMat.dispose(); leafMat.dispose();
    const renderer = new THREE.WebGLRenderer();
    renderer.shadowMap.enabled = true;
    renderer.setSize(64, 64);
    const target = new THREE.WebGLRenderTarget(64, 64);
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 20);
    camera.position.z = 3;
    const scene = new THREE.Scene();
    const light = new THREE.DirectionalLight(0xffffff, 2);
    light.castShadow = true;
    Object.assign(light.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2, near: 0.1, far: 10 });
    light.shadow.bias = -0.0001;
    scene.add(light);
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
    plane.receiveShadow = true;
    scene.add(plane);
    const blocker = new THREE.Mesh(new THREE.PlaneGeometry(2, 2),
      new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
    blocker.position.z = -1;
    blocker.castShadow = true;
    scene.add(blocker);
    const pixels = new Uint8Array(64 * 64 * 4);
    function read() {
      renderer.setRenderTarget(target);
      renderer.render(scene, camera);
      renderer.readRenderTargetPixels(target, 0, 0, 64, 64, pixels);
      let green = 0;
      for (let y = 24; y < 40; y++) for (let x = 24; x < 40; x++) green += pixels[(y * 64 + x) * 4 + 1];
      return green / 256;
    }
    const rows = [];
    for (const lowSpec of [true, false]) {
      let hooks = 0;
      const material = new THREE.MeshStandardMaterial({ color: 0x80cc40, side: THREE.DoubleSide });
      material.onBeforeCompile = () => { hooks++; };
      patchLeafLight(material, { lowSpec });
      plane.material = material;
      LEAF_SKY.value = 0;
      blocker.visible = false;
      light.position.set(0, 0, 4);
      light.intensity = 2;
      const front = read();
      light.position.z = -4;
      const back = read();
      blocker.visible = true;
      const shadow = read();
      blocker.visible = false;
      const wood = new THREE.MeshStandardMaterial({ color: 0x80cc40, side: THREE.DoubleSide });
      patchLeafLight(wood, { lowSpec, mask: '0.0' });
      plane.material = wood;
      const masked = read();
      plane.material = material;
      light.intensity = 0;
      const night = read();
      LEAF_SKY.value = 0.22;
      const sky = read();
      rows.push({ lowSpec, front, back, shadow, masked, night, sky, hooks });
      material.dispose(); wood.dispose();
    }
    LEAF_SKY.value = 0.22;
    const runnable = renderer.info.programs.every(p => p.diagnostics?.runnable !== false);
    renderer.dispose(); target.dispose();
    return { rows, runnable, geometry, ranges };
  });
  for (const row of rows.rows) {
    assert(row.front > row.back && row.back > 2, 'front-lit and transmitted surfaces differ');
    assert(row.shadow < row.back * 0.1, 'an occluder stops direct transmission');
    assert(row.masked < 1, 'wood does not transmit');
    assert(row.night === 0 && row.sky > 2, 'no unlit glow; sky is independently bounded');
    assert(row.hooks > 0, 'the existing shader hook still runs');
  }
  assert(rows.runnable && !errors.length, errors.join('\n'));
  for (const g of rows.geometry) {
    assert(g.coarseUnchanged && g.bareUnchanged && g.heightUnchanged, JSON.stringify(g));
    assert(g.fullTriangles > g.baseTriangles, 'Full carries additional close sprays');
  }
  assert(rows.ranges.closeTriangles > rows.ranges.nearTriangles && rows.ranges.nearTriangles > rows.ranges.midTriangles);
  assert(rows.ranges.draws === 4, 'the close level uses the existing batches');
  assert(rows.ranges.transitioning > 0 && rows.ranges.settled === 0, 'the new close boundary dissolves and settles');
  console.log('LEAF LIGHT PASS — Light and detailed shaders; shadowed backlight, wood mask, night, sky, hook composition', JSON.stringify(rows.rows));
  console.log('TREE DETAIL PASS — seven species/habits, Full close foliage, unchanged coarse and bare templates and tree dimensions', JSON.stringify(rows.geometry));
  console.log('TREE RANGES PASS — extra detail confined to the close ring', JSON.stringify(rows.ranges));
} finally {
  await browser.close();
  server.close();
}
