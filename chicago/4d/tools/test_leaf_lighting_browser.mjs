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
    const { patchLeafLight, patchVineLeafLight } = await import('/js/leaf-light.js');
    const { patchFoliage, patchDeciduousSprays, applySeasonLook, FOLIAGE } = await import('/js/season.js');
    const { patchTreeWind } = await import('/js/tree-surface.js');
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
      if(!patchLeafLight(material, { lowSpec }) || patchLeafLight(material, { lowSpec })) throw Error('leaf hook must apply exactly once');
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
    // Real vine atlas classification is taken before fall recolours its leaves.
    const atlas=new THREE.DataTexture(new Uint8Array([70,155,35,255,110,65,25,255]),2,1);
    atlas.name='fixture-vine-atlas';atlas.needsUpdate=true;atlas.magFilter=THREE.NearestFilter;
    atlas.minFilter=THREE.NearestFilter;
    const vine=new THREE.MeshStandardMaterial({map:atlas,side:THREE.DoubleSide});
    if(!patchVineLeafLight(vine) || patchVineLeafLight(vine))throw Error('vine hook must apply exactly once');
    patchFoliage(vine,FOLIAGE.vine);applySeasonLook('fall');
    plane.material=vine;light.intensity=2;light.position.z=-4;LEAF_SKY.value=0;blocker.visible=false;
    const vinePixels=()=>{
      read();
      // Average a patch: fall's existing atlas thinning may discard one pixel.
      const sample=cx=>{
        const rgb=[0,0,0];
        for(let y=27;y<38;y++)for(let x=cx-3;x<=cx+3;x++)for(let c=0;c<3;c++)rgb[c]+=pixels[(y*64+x)*4+c]/77;
        return rgb;
      };
      return {leaf:sample(25),stem:sample(39)};
    };
    const vineBack=vinePixels();blocker.visible=true;const vineShadow=vinePixels();blocker.visible=false;
    light.intensity=0;const vineNight=vinePixels();
    applySeasonLook('summer');vine.dispose();atlas.dispose();
    // The legacy mixed wood/leaf batch must lose the leaf's colour AND both
    // types of shadow in winter, without losing the woody part of the batch.
    const woodyScene = new THREE.Scene(); woodyScene.background = new THREE.Color(0);
    const woodyCamera = new THREE.OrthographicCamera(-2, 2, 2, -2, .1, 20);
    woodyCamera.position.z = 5; woodyCamera.lookAt(0, 0, 0);
    const woodySun = new THREE.DirectionalLight(0xffffff, 3);
    woodySun.position.z = 4; woodySun.castShadow = true;
    Object.assign(woodySun.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2, near: .1, far: 10 });
    woodySun.shadow.mapSize.set(256, 256); woodyScene.add(woodySun);
    const woodyPoint = new THREE.PointLight(0xffffff, 70, 10);
    woodyPoint.position.z = 4; woodyPoint.castShadow = true; woodyPoint.visible = false;
    woodyPoint.shadow.camera.near = .1; woodyPoint.shadow.camera.far = 10;
    woodyPoint.shadow.mapSize.set(256, 256); woodyScene.add(woodyPoint);
    const woodyMat = new THREE.MeshStandardMaterial({ color: 0xffffff, side: THREE.DoubleSide });
    const woodyDepth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide });
    const woodyDistance = new THREE.MeshDistanceMaterial({ side: THREE.DoubleSide });
    const woodyWind = { value: 0 };
    patchTreeWind(woodyMat, woodyWind, { surface: true });
    patchTreeWind(woodyDepth, woodyWind); patchTreeWind(woodyDistance, woodyWind);
    for (const m of [woodyMat, woodyDepth, woodyDistance]) {
      if (!patchDeciduousSprays(m) || patchDeciduousSprays(m)) throw Error('one deciduous patch per material');
    }
    const woodyCards = [];
    for (const [x, leaf] of [[-.6, 0], [.6, 1]]) {
      const g = new THREE.PlaneGeometry(.6, .6);
      g.setAttribute('aLeaf', new THREE.Float32BufferAttribute(new Float32Array(4).fill(leaf), 1));
      g.setAttribute('aFlex', new THREE.Float32BufferAttribute(new Float32Array(4), 1));
      const m = new THREE.Mesh(g, woodyMat); m.position.set(x, 0, 1); m.castShadow = true;
      m.customDepthMaterial = woodyDepth; m.customDistanceMaterial = woodyDistance;
      woodyCards.push(m); woodyScene.add(m);
    }
    const woodyFloor = new THREE.Mesh(new THREE.PlaneGeometry(4, 4),
      new THREE.MeshStandardMaterial({ color: 0xffffff, side: THREE.DoubleSide }));
    woodyFloor.receiveShadow = true; woodyFloor.visible = false; woodyScene.add(woodyFloor);
    const woodyRead = (season, x) => {
      applySeasonLook(season);
      renderer.setRenderTarget(target); renderer.render(woodyScene, woodyCamera);
      renderer.readRenderTargetPixels(target, 0, 0, 64, 64, pixels);
      const sample = at => {
        const px = Math.round((at + 2) * 16); let sum = 0;
        for (let y = 30; y <= 33; y++) for (let i = px - 1; i <= px + 1; i++) sum += pixels[(y * 64 + i) * 4 + 1];
        return sum / 12;
      };
      return { wood: sample(-x), leaf: sample(x) };
    };
    const woodyColour = { summer: woodyRead('summer', .6), winter: woodyRead('winter', .6) };
    woodyFloor.visible = true; woodyMat.colorWrite = false; woodyMat.depthWrite = false;
    const woodyDirectional = { summer: woodyRead('summer', .6), winter: woodyRead('winter', .6) };
    woodySun.visible = false; woodyPoint.visible = true;
    const woodyPointShadow = { summer: woodyRead('summer', .8), winter: woodyRead('winter', .8) };
    for (const m of woodyCards) m.geometry.dispose();
    woodyMat.dispose(); woodyDepth.dispose(); woodyDistance.dispose();
    woodyFloor.geometry.dispose(); woodyFloor.material.dispose();
    woodySun.shadow.map?.dispose(); woodyPoint.shadow.map?.dispose();
    applySeasonLook('summer');
    LEAF_SKY.value = 0.22;
    const runnable = renderer.info.programs.every(p => p.diagnostics?.runnable !== false);
    renderer.dispose(); target.dispose();
    return { rows, runnable, geometry, ranges, vineBack, vineShadow, vineNight,
      woodyColour, woodyDirectional, woodyPointShadow };
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
  assert(Math.max(...rows.vineBack.leaf)>2,'fall ivy still transmits through its originally green leaves');
  assert(Math.max(...rows.vineBack.stem)<1,'the same vine material does not transmit through brown stems');
  assert(Math.max(...rows.vineShadow.leaf)<1&&Math.max(...rows.vineNight.leaf)<1,'vine backlight follows shadows and night');
  assert(rows.woodyColour.summer.leaf > 2 && rows.woodyColour.winter.leaf === 0,
    `winter clips the deciduous card's visible surface: ${JSON.stringify(rows.woodyColour)}`);
  assert(rows.woodyColour.winter.wood > 2, 'the mixed batch retains its woody surface');
  for (const result of [rows.woodyDirectional, rows.woodyPointShadow]) {
    assert(result.winter.leaf > result.summer.leaf + 20, `winter removes the leaf shadow: ${JSON.stringify(result)}`);
    assert(Math.abs(result.winter.wood - result.summer.wood) < 3, 'wood keeps its shadow');
  }
  console.log('LEAF LIGHT PASS — Light and detailed shaders; shadowed backlight, wood mask, night, sky, hook composition', JSON.stringify(rows.rows));
  console.log('TREE DETAIL PASS — seven species/habits, Full close foliage, unchanged coarse and bare templates and tree dimensions', JSON.stringify(rows.geometry));
  console.log('TREE RANGES PASS — extra detail confined to the close ring', JSON.stringify(rows.ranges));
  console.log('VINE LIGHT PASS — one patch, pre-season leaf mask, opaque brown stems, shadow and night',JSON.stringify({back:rows.vineBack,shadow:rows.vineShadow,night:rows.vineNight}));
  console.log('DECIDUOUS SPRAYS PASS — winter removes tagged leaf colour and directional/point shadows, preserving wood',
    JSON.stringify({colour:rows.woodyColour,directional:rows.woodyDirectional,point:rows.woodyPointShadow}));
} finally {
  await browser.close();
  server.close();
}
