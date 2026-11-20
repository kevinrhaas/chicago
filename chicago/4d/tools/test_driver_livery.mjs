// SPDX-License-Identifier: GPL-3.0-or-later
// T-3398, T-3409: each driver's wardrobe (the 1904 coachman's box coat, cape and top hat;
// the 1835 wagon driver's round jacket and felt hat), as the renderer binds it
// (renderers/web/js/driver-livery.js) to the REAL exported driver. Each must: be the
// file its driven row binds by sha256, dressed on the body master the row names;
// bind by bone name on the web LOD0 and LOD3 the town loads; reproduce, through
// three's own skinning in the seated clip, the posed points the wardrobe kit
// recorded (tools/human_wardrobe.py); dye only the garments it declares; swing its
// spring tails behind the body's motion, within their limits, and settle back to the
// drape at rest; and undo cleanly, leaving the body exactly as it was.
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

const loops = JSON.parse(await fs.readFile(new URL('data/transport/driven/loops.json', here), 'utf8'));
const rows = loops.rows.filter(r => r.driver_livery_file);
assert(rows.length >= 2, 'both driven rows wear a wardrobe');
let swung = 0;
for (const row of rows) {
  const tag = row.driver_asset;
  // The driven row binds this exact file, dressed on this exact body master.
  const bytes = await fs.readFile(new URL(`renderers/web/${row.driver_livery_file}`, here));
  assert.equal(sha(bytes), row.driver_livery_sha256, `${tag}: the row binds the committed wardrobe by its bytes`);
  const master = await fs.readFile(new URL(`assets/humans/${row.driver_asset}.lod0.glb`, here));
  const livery = parseLivery(bytes.toString('utf8'));
  assert.equal(livery.asset_id, row.driver_asset);
  assert.equal(livery.body_master_sha256, sha(master), `${tag}: dressed on the committed body master`);
  assert.equal(row.driver_livery_body_sha256, livery.body_master_sha256);
  assert(livery.garments.length && livery.garments.every(g => g.liberty || g.source_ids?.length), `${tag}: every garment has its source or liberty`);
  // The renderer's fetch path refuses a file that is not the bound one.
  const fetched = async () => ({ ok: true, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) });
  await assert.rejects(loadLivery('x', '0'.repeat(64), fetched), /differs from its binding/);
  assert.equal((await loadLivery('x', row.driver_livery_sha256, fetched)).parts.length, livery.parts.length);
  // Draws: one per material.
  assert.equal(new Set(livery.parts.map(p => p.material)).size, livery.parts.length, `${tag}: one mesh per material`);
  assert(livery.parts.some(p => /wool/.test(p.material)), `${tag}: an outer garment is wool for fabric.js`);
  const recolor = Object.keys(livery.recolor_body_materials ?? {});

  for (const lod of [0, 3]) {
    const glb = await fs.readFile(new URL(`assets/humans/web/${row.driver_asset}.lod${lod}.glb`, here));
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(glb), '');
    const scene = gltf.scene;
    const meshes = []; scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
    const body = { scene, meshes: [...meshes] };
    const colours = meshes.map(m => [m, m.material.color.clone()]);
    const mixer = new THREE.AnimationMixer(scene);
    mixer.clipAction(gltf.animations.find(a => a.name === livery.clip_posed)).play(); mixer.setTime(0);
    scene.updateMatrixWorld(true);
    const bonesBefore = []; scene.traverse(o => { if (o.isBone) bonesBefore.push(o); });
    const undo = dressInLivery(body, livery);
    scene.updateMatrixWorld(true);
    const added = body.meshes.slice(meshes.length);
    assert.equal(added.length, livery.parts.length, `${tag} LOD${lod}: every piece added`);
    assert(added.every(m => m.isSkinnedMesh && m.parent && m.skeleton.bones.every(b => b.isBone)), `${tag} LOD${lod}: skinned to bones`);
    const tailBones = new Set(undo.tails.map(t => t.bone));
    assert.equal(undo.tails.length, (livery.tails ?? []).length, `${tag} LOD${lod}: every spring tail made`);
    assert(added.every(m => m.skeleton.bones.every(b => meshes[0].skeleton.bones.includes(b) || tailBones.has(b))), `${tag} LOD${lod}: the body's own bone objects, or its tails`);
    assert(undo.tails.every(t => meshes[0].skeleton.bones.includes(t.parent)), `${tag} LOD${lod}: each tail hangs from the body's own bone`);
    for (const [m, c] of colours) {
      if (recolor.includes(m.material.name)) assert(!m.material.color.equals(c), `${tag} LOD${lod}: ${m.material.name} dyed`);
      else assert(m.material.color.equals(c), `${tag} LOD${lod}: ${m.material.name} not dyed`);
    }
    const worstProbe = () => {
      let worst = 0;
      scene.updateMatrixWorld(true);
      for (const mesh of added) mesh.skeleton.update();
      for (const probe of livery.probes) {
        const mesh = added.find(m => m.name === `livery:${probe.part}`);
        const v = mesh.getVertexPosition(probe.index, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld);
        worst = Math.max(worst, v.distanceTo(new THREE.Vector3(...probe.posed_m).applyMatrix4(scene.matrixWorld)));
      }
      return worst;
    };
    const worst = worstProbe();
    assert(worst < 1e-3, `${tag} LOD${lod}: three's skinning puts the wardrobe where it was draped (worst ${(worst * 1000).toFixed(2)} mm)`);
    let note = '';
    if (undo.tails.length) {
      // At rest the tails stay at rest, and so does the drape.
      for (let i = 0; i < 30; i++) undo.update(1 / 60);
      assert(undo.tails.every(t => t.angle < 1e-4), `${tag} LOD${lod}: tails at rest stay at rest`);
      assert(worstProbe() < 1e-3, `${tag} LOD${lod}: resting tails leave the drape where it was`);
      // Jolted sideways (+x, 5 m/s/s for 0.3 s, then held at speed) the tails lag behind, within their limits.
      let v = 0, peak = 0, lag = 0;
      for (let i = 0; i < 60; i++) {
        const dt = 1 / 60; if (i < 18) v += 5 * dt;
        scene.position.x += v * dt; undo.update(dt);
        peak = Math.max(peak, ...undo.tails.map(t => t.angle));
        if (i === 17) {
          const t = undo.tails[0], W = new THREE.Matrix4().multiplyMatrices(t.parent.matrixWorld, t.rest);
          const rest = t.tipLocal.clone().applyMatrix4(W).sub(new THREE.Vector3().setFromMatrixPosition(W));
          lag = t.r.x - rest.x;
        }
      }
      assert(peak > THREE.MathUtils.degToRad(.5), `${tag} LOD${lod}: a jolt swings the tails (peak ${THREE.MathUtils.radToDeg(peak).toFixed(2)} deg)`);
      assert(undo.tails.every(t => t.angle <= t.max + 1e-6), `${tag} LOD${lod}: no tail past its limit`);
      assert(lag < 0, `${tag} LOD${lod}: the cloth trails the jolt`);
      // ...and settle back to the drape once the body moves steadily.
      for (let i = 0; i < 600; i++) { scene.position.x += v / 60; undo.update(1 / 60); }
      const settled = Math.max(...undo.tails.map(t => t.angle));
      assert(settled < THREE.MathUtils.degToRad(.05), `${tag} LOD${lod}: tails settle (${THREE.MathUtils.radToDeg(settled).toFixed(3)} deg)`);
      assert(worstProbe() < 1e-3, `${tag} LOD${lod}: settled tails give back the drape`);
      // A teleport restarts the tails at rest instead of flinging them.
      scene.position.x += 50; undo.update(1 / 60);
      assert(undo.tails.every(t => t.angle < 1e-4), `${tag} LOD${lod}: a jump restarts the tails at rest`);
      note = `, ${undo.tails.length} spring tails swing to ${THREE.MathUtils.radToDeg(peak).toFixed(1)} deg on a jolt and settle`;
      swung++;
    }
    undo();
    assert.equal(body.meshes.length, meshes.length, `${tag} LOD${lod}: undo removes every piece`);
    assert(added.every(m => !m.parent), `${tag} LOD${lod}: undo detaches every piece`);
    const bonesAfter = []; scene.traverse(o => { if (o.isBone) bonesAfter.push(o); });
    assert.deepEqual(bonesAfter, bonesBefore, `${tag} LOD${lod}: undo removes every tail bone`);
    for (const [m, c] of colours) assert(m.material.color.equals(c), `${tag} LOD${lod}: undo restores ${m.material.name}`);
    // Kevin, 2026-11-13: each coachman his own house colours on the same draped file. The dye
    // reaches his own pieces and his own copy of the re-dyed garment, never the shared material.
    if (row.driver_livery_colours) {
      const shared = new Map(meshes.map(m => [m, m.material]));
      const own = dressInLivery(body, livery, { colours: row.driver_livery_colours });
      const pieces = body.meshes.slice(meshes.length);
      const linear = rgb => new THREE.Color().setRGB(...rgb, THREE.LinearSRGBColorSpace);
      for (const [name, rgb] of Object.entries(row.driver_livery_colours)) {
        const worn = [...pieces, ...meshes].filter(m => m.material.name === name);
        assert(worn.length, `${row.id} LOD${lod}: ${name} is worn`);
        assert(worn.every(m => m.material.color.equals(linear(rgb))), `${row.id} LOD${lod}: ${name} in his own colour`);
      }
      for (const [m, material] of shared) {
        if (row.driver_livery_colours[material.name]) assert(m.material !== material, `${row.id} LOD${lod}: his own copy of ${material.name}`);
      }
      for (const [m, c] of colours) assert(shared.get(m).color.equals(c), `${row.id} LOD${lod}: the shared ${m.material.name} is untouched`);
      own();
      for (const [m, material] of shared) assert.equal(m.material, material, `${row.id} LOD${lod}: undo gives back the shared material`);
      assert.throws(() => dressInLivery(body, livery, { colours: { no_such_material: [0, 0, 0] } }), /no material/);
      assert.throws(() => dressInLivery(body, livery, { colours: { garment_outer__box_coat_wool: [2, 0, 0] } }), /linear channels/);
      console.log(`${row.id} LOD${lod}: his own colours on ${Object.keys(row.driver_livery_colours).length} materials, the shared body untouched, undone cleanly`);
    }
    console.log(`${tag} LOD${lod}: ${added.length} meshes bound by name, seated skinning within ${(worst * 1000).toFixed(2)} mm of the drape${note}`);
  }
}
assert(swung > 0, 'a wardrobe swings spring tails');
console.log('driver wardrobes: bound by bytes and body, every garment sourced or a liberty, bound by bone name on LOD0 and LOD3, skinned where draped, spring tails lag and settle, dye only what they declare, undo cleanly: PASS');
