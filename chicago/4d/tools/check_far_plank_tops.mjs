/** T-2037: exact top-face handover after the furniture reach culls a walk.
 * node tools/check_far_plank_tops.mjs [--json]
 * CPU geometry/material/state checks only. Published pixels and tier budgets
 * remain browser gates; the reported candidate cost is not a frame-cost claim.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/frontage.js'), 'utf8');
const moduleURL = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const mod = await import(moduleURL(source.replace("from 'three'", `from '${threeURL}'`)
  .replace("import { resolveBases } from './scene-loader.js';",
    "const resolveBases=()=>({assetBase:new URL('file:///tmp/t2037-no-assets/')});")
  .replace("from './gates.js'", `from '${pathToFileURL(path.join(web, 'js/gates.js')).href}'`)
  + '\nexport { timberBuf, plainTimber, inWalkTone, laySegment, pushBox, plankGapAttribute, createFarWalkTops };'));
const checks = [];
function check(name, run) { run(); checks.push(name); }
const material = new THREE.MeshStandardMaterial({ transparent: true, vertexColors: true });
const group = new THREE.Group();
function fixture(name, x, z, level = 1) {
  const buf = mod.timberBuf();
  // Two real deck runs with a deliberate two-metre opening between them.
  for (const [a, b] of [[0, 2], [4, 6]]) {
    mod.inWalkTone(buf, { id: name, kind: 'plank_walk' }, () =>
      mod.laySegment(buf, {}, x + a, -z, x + b, -z, { surfaceHeight: () => 1 }, level));
  }
  // A top face of standing furniture in the same buffer must not become deck.
  mod.inWalkTone(buf, { belongs_to: name }, () =>
    mod.pushBox(buf, x + 3, 4, z, 1, 0, .2, .2, .5, level));
  mod.plainTimber(buf);
  const geo = new THREE.BufferGeometry();
  for (const [name, stream, size] of [['position', 'pos', 3], ['normal', 'nrm', 3],
    ['_confidence', 'conf', 1], ['color', 'col', 3], ['uv', 'uv', 2]]) {
    geo.setAttribute(name, new THREE.Float32BufferAttribute(buf[stream], size));
  }
  geo.setAttribute('aChiPlankGap', mod.plankGapAttribute(buf.seam));
  geo.computeBoundingSphere();
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = name;
  group.add(mesh);
  return { mesh, ranges: buf.walkTopRanges };
}
const sources = [fixture('near', -3, 0), fixture('far', -3, -3, .5),
  fixture('cross', -3, -6), fixture('behind', -3, 100), fixture('merged', -3, -9)];
sources[0].mesh.visible = true;
for (const entry of sources.slice(1)) entry.mesh.visible = false;
for (const entry of sources.slice(1, 4)) entry.mesh.userData.reachCulled = true;
sources[2].mesh.userData.crossStreet = true;
const snapshots = sources.map(({ mesh }) => Object.fromEntries(Object.entries(mesh.geometry.attributes)
  .map(([name, attribute]) => [name, attribute.array.slice()])));
const batch = mod.createFarWalkTops(group, sources, material);
check('all proxy attributes copy actual top vertices exactly; no furniture tops or invented gaps', () => {
  let vertex = 0;
  for (const { mesh, ranges } of sources) {
    const attrs = mesh.geometry.attributes;
    for (const { from, to } of ranges) for (let i = from; i < to; i += 3) {
      if (attrs.normal.getY(i) < .99) continue;
      for (let j = 0; j < 3; j++, vertex++) for (const [name, original] of Object.entries(attrs)) {
        const copy = batch.mesh.geometry.getAttribute(name);
        assert.equal(copy.itemSize, original.itemSize);
        assert.equal(copy.normalized, original.normalized);
        assert.equal(copy.array.constructor, original.array.constructor);
        for (let k = 0; k < original.itemSize; k++) {
          assert.equal(copy.array[vertex * copy.itemSize + k], original.array[(i + j) * original.itemSize + k]);
        }
      }
    }
  }
  assert.equal(batch.mesh.geometry.getAttribute('position').count, vertex);
  assert.equal(batch.state.candidateTriangles, vertex / 3);
});
check('proxy shares the gap-filter material and normal occlusion; adds at most one noncasting draw', () => {
  assert.equal(batch.mesh.material, material);
  assert.equal(material.depthTest, true); assert.equal(material.depthWrite, true);
  assert.equal(material.polygonOffset, false); assert.equal(batch.mesh.castShadow, false);
  assert.equal(batch.mesh.renderOrder, 1); assert.equal(batch.mesh.userData.farWalkTops, true);
  assert.equal(batch.mesh.visible, false);
});
const camera = new THREE.PerspectiveCamera(62, 1.6, .1, 2000);
camera.position.set(0, 20, 30); camera.lookAt(0, 0, 0);
batch.update(camera, false);
check('reach, tier exclusion, frustum and far-merge hiding compose without resurrection', () => {
  assert.equal(batch.state.activeChunks, 1); // only far, never near/cross/behind/merged
  assert.equal(batch.state.drawCalls, 1);
  assert.equal(batch.mesh.geometry.drawRange.count, batch.state.triangles * 3);
});
const steadyUpdates = batch.state.indexUpdates;
batch.update(camera, false);
check('a stationary selected set reuses its index without another upload', () => {
  assert.equal(batch.state.indexUpdates, steadyUpdates);
});
batch.update(camera, true);
check('enabling cross-street walks adds only their culled tops', () => {
  assert.equal(batch.state.activeChunks, 2);
  assert.equal(batch.state.drawCalls, 1);
});
for (const { mesh } of sources) { mesh.userData.reachCulled = false; mesh.visible = true; }
batch.update(camera, true);
check('returning inside reach removes every proxy before the detailed surface draws', () => {
  assert.equal(batch.state.activeChunks, 0); assert.equal(batch.state.triangles, 0);
  assert.equal(batch.state.drawCalls, 0); assert.equal(batch.mesh.visible, false);
  assert.equal(batch.mesh.geometry.drawRange.count, 0);
});
sources[1].mesh.userData.reachCulled = true;
// A stale flag alone must not draw a coincident duplicate of a visible source.
batch.update(camera, true);
check('a visible source cannot draw with its far replacement', () => {
  assert.equal(batch.state.activeChunks, 0);
});
sources[1].mesh.visible = false;
batch.update(camera, false);
check('moving out again restores the exact same selection without mutating source attributes', () => {
  assert.equal(batch.state.activeChunks, 1);
  sources.forEach(({ mesh }, i) => {
    for (const [name, attribute] of Object.entries(mesh.geometry.attributes)) {
      assert.deepEqual(attribute.array, snapshots[i][name]);
    }
  });
});
batch.dispose(); sources.forEach(({ mesh }) => mesh.geometry.dispose()); material.dispose();

// Price the real emitted layer and exercise its production capture wiring.
const terrainSource = await readFile(path.join(web, 'js/terrain.js'), 'utf8');
const from = terrainSource.indexOf('export class Heightfield');
const to = terrainSource.indexOf('\n/**\n * Load the terrain', from);
const Heightfield = new Function('THREE', terrainSource.slice(from, to)
  .replace('export class', 'class') + '\nreturn Heightfield;')(THREE);
const dir = path.join(root, 'data/terrain/epochs/e1834_harbor_cut');
const metadata = JSON.parse(await readFile(path.join(dir, 'heightfield.json')));
const bytes = await readFile(path.join(dir, metadata.bin));
const hf = new Heightfield().adopt(metadata, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
globalThis.fetch = async url => {
  const file = fileURLToPath(url);
  if (!file.startsWith(path.join(root, 'data/'))) return { ok: false, status: 404 };
  return { ok: true, json: async () => JSON.parse(await readFile(file, 'utf8')) };
};
globalThis.document = { createElement: () => ({ getContext: () => null }) };
const layer = await mod.createFrontage({ dataBase: pathToFileURL(path.join(root, 'data/')),
  terrain: { surfaceHeight: (e, n) => hf.sample(e, n), isWater: (e, n) => hf.sample(e, n) < .015 } });
layer.updateFarWalks(camera, false);
check('production frontage exposes an inert exact-top batch before any reach cull', () => {
  assert.ok(layer.farWalkTops.candidateTriangles > 0);
  assert.ok(layer.farWalkTops.eligibleTriangles < layer.farWalkTops.candidateTriangles);
  assert.equal(layer.farWalkTops.triangles, 0);
  const meshes = layer.group.children.filter(o => o.isMesh && o.material.name === 'frontage-timber');
  assert.equal(new Set(meshes.map(o => o.material)).size, 1);
});
const cost = { ...layer.farWalkTops };
layer.dispose();
const report = { scope: 'CPU exact geometry/material/handover checks; published visibility, motion and frame budgets require browser validation.',
  checks, cost };
if (process.argv.includes('--json')) console.log(JSON.stringify(report, null, 2));
else {
  checks.forEach(name => console.log(`PASS ${name}`));
  console.log(`PASS ${checks.length} far-plank checks; ${cost.candidateTriangles} total / ${cost.eligibleTriangles} light-eligible candidate triangles; at most one added draw`);
}
