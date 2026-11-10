// SPDX-License-Identifier: GPL-3.0-or-later
// Actual hash-bound source meshes and Three material ownership; no WebGL,
// decoded image, ordinary-world contact or photographic acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { register } from 'node:module';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { applyHorseAppearance, horseIdentity, prepareHorseTemplate,
  validateHorseRecipe } from '../renderers/web/js/horse-appearance.js';
const root = new URL('../', import.meta.url);
const read = file => fs.readFileSync(new URL(file, root));
const json = file => JSON.parse(read(file));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const recipe = validateHorseRecipe(json('data/transport/horse-coats.json'));
assert.equal(sha(read('data/transport/horse-coats.recipe.json')), recipe.recipe_sha256, 'authored recipe changes must reach the runtime contract');
assert.equal(sha(read(recipe.foot_reference)), recipe.foot_reference_sha256, 'real foot reference remains bound');
assert.deepEqual(Object.fromEntries(Object.entries(json(recipe.foot_reference).contacts).map(([limb, contact]) => [limb, contact.minimum_vertex_canonical_m])), recipe.foot_centres_m);
const clone = value => structuredClone(value);
// Prove the normal authoring path cannot leave a stale runtime recipe green.
// Copy only the two JSON controls to a tempdir; source meshes remain real inputs.
const temporary = fs.mkdtempSync(path.join(tmpdir(), 'c4d-coat-stale-'));
try {
  const input = path.join(temporary, 'recipe.json'), output = path.join(temporary, 'runtime.json');
  const authored = json('data/transport/horse-coats.recipe.json');
  authored.palettes[0].linear_rgb[0] += .001;
  fs.writeFileSync(input, JSON.stringify(authored)); fs.writeFileSync(output, read('data/transport/horse-coats.json'));
  const before = sha(fs.readFileSync(output));
  const result = spawnSync('python3', [fileURLToPath(new URL('tools/derive_horse_coats.py', root)), '--check',
    '--source-root', fileURLToPath(root), '--recipe', input, '--output', output], { encoding: 'utf8' });
  assert.equal(result.error, undefined); assert.notEqual(result.status, 0);
  assert.match(result.stderr, /canonical output is stale/);
  assert.equal(sha(fs.readFileSync(output)), before, 'rejected check never rewrites output');
} finally { fs.rmSync(temporary, { recursive: true, force: true }); }

const loops = json('data/transport/driven/loops.json');
const standing = json('data/transport/parked/standing-horses.json');
const parked = json('data/transport/parked/placements.json');
const individuals = loops.rows.flatMap(row => ['left', 'right'].map(individual => ({ scene: row.scene, row: row.id, individual })));
for (const [scene, rows] of Object.entries(standing.scenes)) for (const row of rows) individuals.push({ scene, row: row.id, individual: 'single' });
for (const [scene, rows] of Object.entries(parked.scenes)) for (const row of rows) if (row.stationary_team) {
  assert.equal(row.stationary_team.horse_appearance.scene, scene);
  for (const individual of ['left', 'right']) individuals.push({ scene, row: row.id, individual });
}
assert.equal(loops.horse_appearance.recipe_file, 'transport/horse-coats.json');
assert.equal(standing.horse_appearance.recipe_file, 'transport/horse-coats.json');
assert.deepEqual(Object.fromEntries(recipe.scenes.map(scene => [scene, individuals.filter(i => i.scene === scene).length])), { 1812: 4, 1835: 3, 1904: 4 });
const identities = individuals.map(i => horseIdentity(recipe, i));
assert.equal(new Set(identities.map(i => i.key)).size, 11);
for (let n = 0; n < identities.length; n++) {
  assert.deepEqual(horseIdentity(clone(recipe), individuals[n]), identities[n], 'reload changes no marking');
  assert.equal(identities[n].historical_individual, false);
  assert(identities[n].socks_m.every(h => h >= .16 && h <= .56));
}
for (const scene of recipe.scenes) assert(new Set(identities.filter(i => i.key.startsWith(scene+':')).map(i => i.palette)).size >= 2, 'each era has coat diversity');
for (const row of loops.rows) {
  const pair = identities.filter(i => i.key.startsWith(row.scene+':'+row.id+':'));
  assert.equal(pair[0].palette, pair[1].palette, 'matched team palette');
  assert.notDeepEqual(pair[0].phase, pair[1].phase, 'individual pattern differs');
  assert.notDeepEqual([pair[0].socks_m, pair[0].blaze], [pair[1].socks_m, pair[1].blaze]);
}
for (const mutate of [r => r.grade = 'attested', r => r.body_material = 'renamed',
  r => r.source_contract[0].sha256 = '0'.repeat(64), r => r.foot_centres_m.fore_l[0] = NaN,
  r => r.mask_choices.sock_top_range_m.reverse(), r => r.mask_choices.dapple_pitch_m = 0,
  r => r.group_palettes[Object.keys(r.group_palettes)[0]] = 'unknown', r => r.seed_contract.algorithm = 'random']) {
  const bad = clone(recipe); mutate(bad); assert.throws(() => validateHorseRecipe(bad), /horse appearance:/);
}
assert.throws(() => horseIdentity(recipe, { scene: '2000', row: 'row', individual: 'left' }), /stable scene/);
console.log('Coat identities PASS: 11 source-routed individuals, three eras, stable matched palettes/distinct markings; invalid contracts refused');

const vendor = new URL('renderers/web/vendor/three-0.185.1/', root).href;
register(`data:text/javascript,${encodeURIComponent(`export async function resolve(s,c,n){
if(s==='three')return{url:${JSON.stringify(vendor+'three.module.js')},shortCircuit:true};
if(s.startsWith('three/addons/'))return{url:${JSON.stringify(vendor)}+'addons/'+s.slice(13),shortCircuit:true};return n(s,c);}`)}`);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { clone: cloneSkinned } = await import('three/addons/utils/SkeletonUtils.js');
const { createConfidenceView } = await import('../renderers/web/js/confidence.js');
// Remove texture connections only for Node's lack of image decoding. Source
// image payloads are independently checked against the generated contract.
function sourceDocument(raw) { const size = raw.readUInt32LE(12); return { doc: JSON.parse(raw.subarray(20, 20+size)), bin: raw.subarray(28+size) }; }
function geometryOnly(raw) {
  const { doc, bin } = sourceDocument(raw);
  function strip(value) { for (const key of Object.keys(value)) {
    if (/Texture$/.test(key)) delete value[key];
    else if (value[key] && typeof value[key] === 'object') strip(value[key]);
  } }
  doc.materials.forEach(strip); delete doc.images; delete doc.textures;
  const text = Buffer.from(JSON.stringify(doc));
  const encoded = Buffer.concat([text, Buffer.alloc(-text.length & 3, 32)]), out = Buffer.alloc(28+encoded.length+bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(encoded.length, 12); out.writeUInt32LE(0x4e4f534a, 16); encoded.copy(out, 20);
  out.writeUInt32LE(bin.length, 20+encoded.length); out.writeUInt32LE(0x004e4942, 24+encoded.length); bin.copy(out, 28+encoded.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset+out.byteLength);
}
function bodyOf(root) { const found = []; root.traverse(n => { if (n.isMesh && n.material.name === recipe.body_material) found.push(n); }); assert.equal(found.length, 1); return found[0]; }
for (const source of recipe.source_contract) {
  const raw = read(source.file), { doc, bin } = sourceDocument(raw);
  assert.equal(sha(raw), source.sha256, 'immutable selected source');
  assert.deepEqual(doc.skins[0].joints.map(i => doc.nodes[i].name), source.joint_names);
  assert.deepEqual(doc.images.map(image => { const v = doc.bufferViews[image.bufferView]; return sha(bin.subarray(v.byteOffset ?? 0, (v.byteOffset ?? 0)+v.byteLength)); }), source.image_payload_sha256);
  const asset = await new GLTFLoader().parseAsync(geometryOnly(raw), '');
  prepareHorseTemplate(asset, 'organic_dielectric_v1');
  const sourceBody = bodyOf(asset.scene), originalMaterial = sourceBody.material;
  const positions = sourceBody.geometry.attributes.position;
  assert.equal(positions.count, 5595); assert.equal(sourceBody.skeleton.bones.length, 26);
  const rigBefore = JSON.stringify({ inverses: sourceBody.skeleton.boneInverses.map(m => m.toArray()), clips: asset.animations.map(a => THREE.AnimationClip.toJSON(a)) });
  const indexBefore = sha(Buffer.from(sourceBody.geometry.index.array.buffer));
  const attributeHashes = Object.fromEntries(Object.entries(sourceBody.geometry.attributes).map(([key, a]) => [key, sha(Buffer.from(a.array.buffer, a.array.byteOffset, a.array.byteLength))]));
  const a = cloneSkinned(asset.scene), b = cloneSkinned(asset.scene), confidence = createConfidenceView();
  let sourceDisposed = 0, ownedDisposed = 0;
  originalMaterial.addEventListener('dispose', () => sourceDisposed++);
  const params = { recipe, sourceSha: source.sha256, scene: '1835', row: 'western_hotel_driven_wagon_loop_1835', confidence };
  const first = applyHorseAppearance(a, { ...params, individual: 'left' });
  const second = applyHorseAppearance(b, { ...params, individual: 'right' });
  assert.equal(applyHorseAppearance(a, { ...params, individual: 'left' }), first, 'same root decoration is idempotent');
  assert.throws(() => applyHorseAppearance(a, { ...params, individual: 'different' }), /another individual/);
  assert.throws(() => applyHorseAppearance(cloneSkinned(asset.scene), { ...params, sourceSha: '0'.repeat(64), individual: 'left' }), /unbound source/);
  const firstBody = bodyOf(a), secondBody = bodyOf(b);
  assert.equal(firstBody.material.name, originalMaterial.name, 'hoof/tack classifier material name remains exact');
  assert.notEqual(firstBody.material, secondBody.material); assert.notEqual(firstBody.material, originalMaterial);
  assert.equal(firstBody.geometry, sourceBody.geometry); assert.equal(secondBody.geometry, sourceBody.geometry);
  assert.equal(firstBody.material.metalness, 0); assert.equal(originalMaterial.userData.chicagoHorseCoat, undefined);
  for (const horse of [a, b]) horse.traverse(n => {
    if (!n.isMesh) return;
    if (n.material.name === recipe.eye_material) assert.equal(n.material.userData.chicagoHorseCoat, undefined);
    if (n.material.userData.chicagoHorseCoat) n.material.addEventListener('dispose', () => ownedDisposed++);
  });
  const program = firstBody.material.customProgramCacheKey();
  assert.equal(program, secondBody.material.customProgramCacheKey(), 'different individuals share one shader program');
  const shader = { vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader, uniforms: {} };
  firstBody.material.onBeforeCompile(shader);
  assert(shader.vertexShader.includes('vChiHorseP=position;')); assert(shader.vertexShader.includes('vConfidence'));
  assert(shader.fragmentShader.includes('chiHorseSocks')); assert(shader.fragmentShader.includes('vConfidence'));
  confidence.patch(firstBody.material); assert.equal(firstBody.material.customProgramCacheKey(), program, 'later confidence application preserves coat hook');
  assert.equal(shader.uniforms.chiHorseColor.value.length, 4);
  first.dispose(); first.dispose(); assert.equal(sourceDisposed, 0); assert.equal(ownedDisposed, 2, 'only BODY and chestnut HAIR owned by this individual');
  assert.equal(bodyOf(a).material, originalMaterial); assert.notEqual(bodyOf(b).material, originalMaterial, 'other live horse remains varied');
  second.dispose(); assert.equal(ownedDisposed, 4); assert.equal(sourceDisposed, 0);
  for (const [key, a] of Object.entries(sourceBody.geometry.attributes)) assert.equal(sha(Buffer.from(a.array.buffer, a.array.byteOffset, a.array.byteLength)), attributeHashes[key]);
  assert.equal(sha(Buffer.from(sourceBody.geometry.index.array.buffer)), indexBefore);
  assert.equal(JSON.stringify({ inverses: sourceBody.skeleton.boneInverses.map(m => m.toArray()), clips: asset.animations.map(a => THREE.AnimationClip.toJSON(a)) }), rigBefore, 'source bind matrices and clips unchanged');
  assert.equal(sha(read(source.file)), source.sha256, 'source file unchanged');
  const privateRoot = cloneSkinned(asset.scene), privateMaterials = new Set();
  privateRoot.traverse(n => { if (n.isMesh) { n.material = n.material.clone(); privateMaterials.add(n.material); confidence.patch(n.material); } });
  const privateBody = bodyOf(privateRoot).material; let privateDisposed = 0;
  privateBody.addEventListener('dispose', () => privateDisposed++);
  const privateOwner = applyHorseAppearance(privateRoot, { ...params, row: 'western_hotel_yard_standing_horse_01', individual: 'single', ownedMaterials: privateMaterials });
  assert.equal(bodyOf(privateRoot).material, privateBody, 'standing reuses its already-owned material without another clone');
  privateOwner.dispose(); assert.equal(privateDisposed, 0, 'standing owner, not coat layer, disposes private materials');
  for (const material of privateMaterials) material.dispose(); assert.equal(privateDisposed, 1);
  const privateSkeletons = new Set(); privateRoot.traverse(n => { if (n.isSkinnedMesh) privateSkeletons.add(n.skeleton); });
  for (const skeleton of privateSkeletons) skeleton.dispose();
  for (const tree of [a, b, asset.scene]) { const skeletons = new Set(); tree.traverse(n => { if (n.isSkinnedMesh) skeletons.add(n.skeleton); }); for (const skeleton of skeletons) skeleton.dispose(); }
}
console.log('Actual source/material guards PASS: geometry/joints/maps bound, names preserved, independent owned clones cleaned; GLSL compilation, images and all-era street/phone acceptance UNRUN');
