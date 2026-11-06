// SPDX-License-Identifier: GPL-3.0-or-later
// T-3398: the 1904 driver's draped livery (box coat, cape, buttons, top hat), as the
// renderer binds it (renderers/web/js/driver-livery.js) to the REAL exported driver.
// It must: be the file the driven row binds by sha256, draped on the body master the
// row names; bind by bone name on the web LOD0 and LOD3 the town loads; reproduce,
// through three's own skinning in the seated clip, the posed points the producer
// recorded (tools/human_driver_livery_1904.py); dye only the garments it declares;
// and undo cleanly, leaving the body exactly as it was.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const liverySource = (await fs.readFile(new URL('renderers/web/js/driver-livery.js', here), 'utf8')).replace("from 'three'", `from '${three}'`);
const { parseLivery, dressInLivery, loadLivery } = await import(data(liverySource));

function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
  }
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
const sha = b => crypto.createHash('sha256').update(b).digest('hex');

// The driven row binds this exact file, draped on this exact body master.
const loops = JSON.parse(await fs.readFile(new URL('data/transport/driven/loops.json', here), 'utf8'));
const row = loops.rows.find(r => r.driver_livery_file);
assert(row, 'a driven row wears a livery');
const file = new URL(`renderers/web/${row.driver_livery_file}`, here);
const bytes = await fs.readFile(file);
assert.equal(sha(bytes), row.driver_livery_sha256, 'the row binds the committed livery by its bytes');
const master = await fs.readFile(new URL('assets/humans/anonymous_working_driver_1904.lod0.glb', here));
const livery = parseLivery(bytes.toString('utf8'));
assert.equal(livery.asset_id, row.driver_asset);
assert.equal(livery.body_master_sha256, sha(master), 'draped on the committed body master');
assert.equal(row.driver_livery_body_sha256, livery.body_master_sha256);
// The renderer's fetch path refuses a file that is not the bound one.
await assert.rejects(loadLivery('x', '0'.repeat(64), async () => ({ ok: true, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) })), /differs from its binding/);
assert.equal((await loadLivery('x', row.driver_livery_sha256, async () => ({ ok: true, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) }))).parts.length, livery.parts.length);

// Draws: one per material.
assert.equal(new Set(livery.parts.map(p => p.material)).size, livery.parts.length, 'one mesh per material');
const coat = livery.parts.find(p => p.material === 'garment_outer__box_coat_wool');
assert(coat && /wool|coat/.test(coat.material), 'the coat is wool for fabric.js');

for (const lod of [0, 3]) {
  const glb = await fs.readFile(new URL(`assets/humans/web/anonymous_working_driver_1904.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(glb), '');
  const scene = gltf.scene;
  const meshes = []; scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
  const body = { scene, meshes: [...meshes] };
  const trousers = meshes.find(m => m.material.name === 'garment_lower__highwaist_pantaloons');
  const before = trousers.material.color.clone(), others = meshes.filter(m => m !== trousers).map(m => [m.material, m.material.color.clone()]);
  const mixer = new THREE.AnimationMixer(scene);
  mixer.clipAction(gltf.animations.find(a => a.name === 'sit_drive')).play(); mixer.setTime(0);
  scene.updateMatrixWorld(true);
  const undo = dressInLivery(body, livery);
  scene.updateMatrixWorld(true);
  const added = body.meshes.slice(meshes.length);
  assert.equal(added.length, livery.parts.length, `LOD${lod}: every piece added`);
  assert(added.every(m => m.isSkinnedMesh && m.parent && m.skeleton.bones.every(b => b.isBone)), `LOD${lod}: skinned to the body's bones`);
  assert(added.every(m => m.skeleton.bones.every(b => meshes[0].skeleton.bones.includes(b))), `LOD${lod}: the body's own bone objects`);
  assert.notDeepEqual(trousers.material.color.toArray(), before.toArray(), `LOD${lod}: livery trousers dyed`);
  for (const [m, c] of others) assert(m.color.equals(c), `LOD${lod}: no other garment dyed`);
  let worst = 0;
  for (const mesh of added) mesh.skeleton.update();
  for (const probe of livery.probes) {
    const mesh = added.find(m => m.name === `livery:${probe.part}`);
    const v = mesh.getVertexPosition(probe.index, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld);
    worst = Math.max(worst, v.distanceTo(new THREE.Vector3(...probe.posed_m)));
  }
  assert(worst < 1e-3, `LOD${lod}: three's skinning puts the livery where it was draped (worst ${(worst * 1000).toFixed(2)} mm)`);
  undo();
  assert.equal(body.meshes.length, meshes.length, `LOD${lod}: undo removes every piece`);
  assert(added.every(m => !m.parent), `LOD${lod}: undo detaches every piece`);
  assert(trousers.material.color.equals(before), `LOD${lod}: undo restores the trousers`);
  console.log(`LOD${lod}: ${added.length} livery meshes bound by name, seated skinning within ${(worst * 1000).toFixed(2)} mm of the drape`);
}
console.log('driver livery: bound by bytes and body, bound by bone name on LOD0 and LOD3, skinned where draped, dyes only the trousers, undoes cleanly: PASS');
