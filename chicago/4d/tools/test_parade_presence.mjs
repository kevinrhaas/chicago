#!/usr/bin/env node
/** Actual building batching distinguishes loaded delegated parade ground from a missing host. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next) {
  if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};
  if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};
  return next(s,c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
const { createBuildings } = await import('../renderers/web/js/buildings.js');
const { createConfidenceView } = await import('../renderers/web/js/confidence.js');
const { PARADE_GROUNDS, paradeGroundOwner } = await import('../renderers/web/js/fort-gates.js');
const ROOT = new URL('../', import.meta.url);

// This Node test batches actual GLBs without a WebGL context. Supply only the
// texture-loader boundary; all geometry, placement, material roles and presence
// accounting run through the production createBuildings implementation.
const saved = { window: globalThis.window, location: globalThis.location, fetch: globalThis.fetch,
  load: THREE.TextureLoader.prototype.loadAsync };
globalThis.window = { location: { href: 'http://fixture.invalid/4d/walk/', search: '?walls=flat' } };
globalThis.location = globalThis.window.location;
globalThis.fetch = async () => ({ ok: true, json: async () => ({ id: 'node-fixture', span_m: 1 }) });
THREE.TextureLoader.prototype.loadAsync = async () => new THREE.Texture();
const flat = { surfaceHeight: () => 0, walkHeight: () => 0, isWater: () => false };
const models = [];
const meshes = (record) => {
  const out = [];
  record.gltf?.scene.traverse((node) => { if (node.isMesh) out.push(node); });
  return out;
};
async function record(year, id) {
  const sidecar = JSON.parse(fs.readFileSync(new URL(`data/sidecars/${year}/${id}.json`, ROOT)));
  const bytes = fs.readFileSync(new URL(`assets/web/${sidecar.asset.split('/').at(-1)}`, ROOT));
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const gltf = await new Promise((resolve, reject) => new GLTFLoader()
    .setMeshoptDecoder(MeshoptDecoder).parse(data, '', resolve, reject));
  return { id, sidecar, gltf };
}
async function build(...records) {
  const layer = await createBuildings({ registry: new Map(records.map((r) => [r.id, r])),
    terrain: flat, confidence: createConfidenceView() });
  models.push(layer);
  return layer;
}
function missing(layer, id) {
  assert(layer.missing.has(id), `${id}: a failed/empty/nondelegated host must remain missing`);
  assert(layer.roll.missing.includes(id));
  assert.equal(layer.roll.expected, 1);
  assert.equal(layer.roll.standing, 0);
  assert.equal(layer.instanceBounds()[id], undefined);
  assert.equal(layer.roll.delegatedGround[id], undefined);
}

try {
  for (const [id, owner] of Object.entries(PARADE_GROUNDS)) {
    const dir = owner.scene === '1812' ? 'enclosures/1812/' : 'enclosures/';
    const index = JSON.parse(fs.readFileSync(new URL(`data/${dir}index.json`, ROOT)));
    assert(index.enclosures.some((entry) => entry.id === owner.id && entry.file === `${owner.id}.json`),
      'the actual scene loads this exact ground owner');
    const ground = JSON.parse(fs.readFileSync(new URL(`data/${dir}${owner.id}.json`, ROOT)));
    assert.equal(ground.structure_id, id);
    assert.equal(ground.ground.treatment, 'trodden_earth');
    assert(ground.ground.interior_local_enu_m.length >= 3);
    assert.equal(paradeGroundOwner(await record(owner.scene, id)), owner.id);
  }
  const firstId = 'first_fort_dearborn_parade';
  const first = await record('1812', firstId);
  const loaded = await build(first);
  assert.equal(first.node.userData.structure_id, firstId);
  assert.equal(loaded.roll.delegatedGround[firstId], 'first_fort_dearborn_parade_ground');
  assert.equal(loaded.roll.expected, 0, 'delegated ground is not a claimed building batch');
  assert.equal(loaded.roll.standing, 0, 'no invented standing building or box');
  assert.equal(loaded.missing.size, 0);
  assert.equal(loaded.instanceBounds()[firstId], undefined);

  const failed = await record('1812', firstId); failed.gltf = null;
  missing(await build(failed), firstId);
  const wrongPhase = await record('1812', firstId);
  wrongPhase.gltf.scene.traverse((node) => {
    if (node.userData.structure_id === firstId) node.userData.phase_id = 'wrong_phase';
  });
  missing(await build(wrongPhase), firstId);
  const emptyGroup = await record('1812', firstId); emptyGroup.gltf.scene = new THREE.Group();
  missing(await build(emptyGroup), firstId);
  const emptyMesh = await record('1812', firstId);
  meshes(emptyMesh)[0].geometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
  meshes(emptyMesh)[0].geometry.setIndex([]);
  missing(await build(emptyMesh), firstId);
  const emptyIndices = await record('1812', firstId); meshes(emptyIndices)[0].geometry.setIndex([]);
  missing(await build(emptyIndices), firstId);
  const invalidIndex = await record('1812', firstId);
  meshes(invalidIndex)[0].geometry.getIndex().setX(0, 65535);
  missing(await build(invalidIndex), firstId);
  const malformed = await record('1812', firstId);
  meshes(malformed)[0].geometry.getAttribute('position').setX(0, NaN);
  missing(await build(malformed), firstId);
  const malformedTransform = await record('1812', firstId);
  meshes(malformedTransform)[0].position.x = NaN;
  missing(await build(malformedTransform), firstId);
  const degenerate = await record('1812', firstId);
  meshes(degenerate)[0].geometry.getAttribute('position').array.fill(0);
  missing(await build(degenerate), firstId);
  const mixedMaterial = await record('1812', firstId);
  meshes(mixedMaterial)[0].material = [meshes(mixedMaterial)[0].material,
    new THREE.MeshStandardMaterial({ name: 'metal' })];
  missing(await build(mixedMaterial), firstId);

  const secondId = 'fort_dearborn_parade';
  const second = await build(await record('1835', secondId));
  assert.equal(second.roll.delegatedGround[secondId], undefined);
  assert.equal(second.roll.expected, 1);
  assert.equal(second.roll.standing, 1);
  assert(second.instanceBounds()[secondId], 'the second fort’s sundial actually batches');
  const brokenDial = await record('1835', secondId);
  for (const mesh of meshes(brokenDial)) if (mesh.material.name !== 'earth') mesh.geometry.deleteAttribute('position');
  missing(await build(brokenDial), secondId);

  const ordinary = await record('1812', firstId);
  ordinary.id = ordinary.sidecar.id = 'ordinary_earth_model';
  ordinary.gltf.scene.traverse((node) => {
    if (node.userData.structure_id) node.userData.structure_id = ordinary.id;
  });
  const ordinaryLayer = await build(ordinary);
  assert.equal(ordinaryLayer.roll.expected, 1);
  assert.equal(ordinaryLayer.roll.standing, 1);
  assert(ordinaryLayer.instanceBounds()[ordinary.id], 'an unowned parade kind retains its own geometry');

  const ordinaryKind = await record('1812', firstId);
  ordinaryKind.sidecar.attributes.kind.value = 'yard';
  const ordinaryKindLayer = await build(ordinaryKind);
  assert.equal(ordinaryKindLayer.roll.expected, 1);
  assert.equal(ordinaryKindLayer.roll.standing, 1);
  assert(ordinaryKindLayer.instanceBounds()[firstId], 'non-parade earth retains its own geometry');

  const before = await record('1812', firstId), after = await record('1812', firstId);
  before.id = before.sidecar.id = 'shared_earth_model';
  before.gltf.scene.traverse((node) => {
    if (node.userData.structure_id) node.userData.structure_id = before.id;
  });
  meshes(after)[0].material = meshes(before)[0].material;
  const shared = await build(before, after);
  assert(shared.instanceBounds()[before.id]);
  assert.equal(shared.roll.delegatedGround[firstId], 'first_fort_dearborn_parade_ground',
    'original material roles survive an earlier batch whitening the shared material');
  assert.equal(shared.missing.size, 0);
  console.log('PARADE PRESENCE PASS — actual loaded ground delegation, failed/empty/malformed assets, mixed sundial, unknown owner and shared material roles');
} finally {
  for (const layer of models) layer.dispose();
  globalThis.window = saved.window; globalThis.location = saved.location; globalThis.fetch = saved.fetch;
  THREE.TextureLoader.prototype.loadAsync = saved.load;
}
