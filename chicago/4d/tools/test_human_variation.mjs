// SPDX-License-Identifier: GPL-3.0-or-later
// T-3412: every person's own body and face (renderers/web/js/human-variation.js) on the real
// web exports, on the CPU (no WebGL). It must: be a pure function of the person; give no two
// people of a crowd the same face; take a recorded age; move a seated driver's face and
// nothing he sits on or holds; keep shoes on the ground, eyes whole and clothes outside the
// skin they were fitted over; agree between LODs; and reuse one variant per person and LOD.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
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
const V = await import(data((await fs.readFile(new URL('renderers/web/js/human-variation.js', here), 'utf8')).replace("from 'three'", `from '${three}'`)));

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

const header = JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_kit.json', here)));
const binBytes = await fs.readFile(new URL('assets/humans/web/hm08_variation_kit.bin', here));
const kit = V.parseVariationKit(header, binBytes.buffer.slice(binBytes.byteOffset, binBytes.byteOffset + binBytes.byteLength));
const persons = JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json', here))).persons;
const faceAxes = kit.axes.filter(a => a.scope === 'face' && !a.drive);

// The PRNG and a person's values are pure functions of the id.
{ const a = V.seededRandom('x'), b = V.seededRandom('x'), c = V.seededRandom('y');
  const sa = [a(), a(), a()]; assert.deepEqual(sa, [b(), b(), b()]); assert.notDeepEqual(sa, [c(), c(), c()]);
  const p = V.personVariation({ kit, key: 'someone', assetId: 'bardwell_otis_1835' });
  assert.deepEqual(p, V.personVariation({ kit, key: 'someone', assetId: 'bardwell_otis_1835' }));
  assert.equal(p.grade, 'reconstructed');
  for (const a of kit.axes) if (!a.drive) assert(Math.abs(p.values[a.id]) <= header.limit + 1e-12, `${a.id} within the limit`);
  assert(Math.abs(p.height - 1) <= header.height.limit + 1e-12); }

// No two alike: across a crowd of 400 ids, the closest pair of faces still differ by at least
// one axis's own spread, measured in units of each axis's spread.
{ const faces = Array.from({ length: 400 }, (_, i) => V.personVariation({ kit, key: `crowd_${i}`, assetId: 'bardwell_otis_1835' }));
  let closest = Infinity;
  for (let i = 0; i < faces.length; i++) for (let j = i + 1; j < faces.length; j++) {
    let s = 0; for (const a of faceAxes) s += ((faces[i].values[a.id] - faces[j].values[a.id]) / a.spread) ** 2;
    closest = Math.min(closest, Math.sqrt(s));
  }
  assert(closest > 1.5, `closest pair of 400 faces differ by ${closest.toFixed(2)} spreads, want > 1.5`);
  const hs = faces.map(f => f.height); assert(Math.max(...hs) - Math.min(...hs) > 0.08, 'heights spread'); }

// A recorded age is used; a band is drawn inside; the face and body age with it.
{ const hans = persons.pa1904_otis_f_r_c1900_hans_johnson, otis = persons.rc_bardwell_otis;
  assert.equal(hans.age.years, 34); assert.deepEqual(hans.age.sources, ['census_1900_chicago_t623_roll245']);
  const h = V.personVariation({ kit, key: 'pa1904_otis_f_r_c1900_hans_johnson', record: hans, assetId: 'anonymous_working_driver_1904' });
  assert.equal(h.age, 34);
  const o = V.personVariation({ kit, key: 'rc_bardwell_otis', record: otis, assetId: 'bardwell_otis_1835' });
  assert(o.age >= 20 && o.age <= 29, `Otis ${o.age} in his band`);
  const old = V.personVariation({ kit, key: 'x', record: { age: { years: 70 } }, assetId: 'bardwell_otis_1835' });
  assert(old.values.face_age > 0.5 && old.values.body_age > 0.4 && o.values.face_age < 0); }

async function figure(asset, lod) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  return gltf.scene;
}
const SK = await import(utils.SkeletonUtils);
function snapshot(scene) {
  scene.updateMatrixWorld(true);
  const out = new Map();
  scene.traverse(o => {
    if (!o.isSkinnedMesh) return;
    const sk = o.skeleton, M = new THREE.Matrix4().multiplyMatrices(sk.bones[0].matrixWorld, sk.boneInverses[0]).multiply(o.bindMatrix);
    const p = o.geometry.attributes.position, a = new Float32Array(p.count * 3), v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) v.fromBufferAttribute(p, i).applyMatrix4(M).toArray(a, i * 3);
    out.set(o.name.replace(/^.*?_(?=[a-z]+(_\d)?_lod\d$|short04|eyes|closed)/, ''), { mesh: o, pos: a, slot: o.material.name.split('__')[0] });
  });
  return out;
}

// A seated driver: his face changes; nothing below his chin moves (seat, reins, livery).
for (const lod of [0, 3]) {
  const scene = await figure('anonymous_working_driver_1904', lod), before = snapshot(scene);
  const p = V.personVariation({ kit, key: 'pa1904_otis_f_r_c1900_hans_johnson', record: persons.pa1904_otis_f_r_c1900_hans_johnson, assetId: 'anonymous_working_driver_1904' });
  const r = V.applyVariation(scene, kit, p, { scope: 'face' });
  assert(r && r.height === 1 && scene.scale.x === 1);
  const after = snapshot(scene);
  let faceMove = 0;
  for (const [name, b] of before) {
    const a = after.get(name).pos;
    for (let i = 0; i < a.length; i += 3) {
      const d = Math.hypot(a[i] - b.pos[i], a[i + 1] - b.pos[i + 1], a[i + 2] - b.pos[i + 2]);
      if (b.pos[i + 1] < 1.40) assert(d < 1e-4, `lod${lod} ${name}: a seated driver moved ${d} m below his chin at y ${b.pos[i + 1]}`);
      else if (b.slot === 'skin') faceMove = Math.max(faceMove, d);
    }
  }
  assert(faceMove > 0.002, `lod${lod}: his face changed (${faceMove})`);
}

function inside(body, pts, skip) {
  // signed clearance of each point from its nearest body vertex, along that vertex's normal
  const n = body.pos.length / 3, idx = body.mesh.geometry.index.array, N = new Float32Array(n * 3);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  for (let f = 0; f < idx.length; f += 3) {
    a.fromArray(body.pos, idx[f] * 3); b.fromArray(body.pos, idx[f + 1] * 3); c.fromArray(body.pos, idx[f + 2] * 3);
    const fn = b.sub(a).cross(c.sub(a));
    for (const v of [idx[f], idx[f + 1], idx[f + 2]]) { N[v * 3] += fn.x; N[v * 3 + 1] += fn.y; N[v * 3 + 2] += fn.z; }
  }
  const grid = V.pointGrid(body.pos, 3, 0.03), near = V.nearest(grid, pts);
  return Array.from(near, (j, i) => {
    const l = Math.hypot(N[j * 3], N[j * 3 + 1], N[j * 3 + 2]) || 1;
    return ((pts[i * 3] - body.pos[j * 3]) * N[j * 3] + (pts[i * 3 + 1] - body.pos[j * 3 + 1]) * N[j * 3 + 1] + (pts[i * 3 + 2] - body.pos[j * 3 + 2]) * N[j * 3 + 2]) / l;
  });
}

// A person on foot: a whole body, at every LOD, for a handful of people.
const summary = {};
for (const lod of [0, 1, 2, 3]) for (const key of ['rc_bardwell_otis', 'crowd_3', 'crowd_17', 'crowd_250']) {
  const scene = await figure('bardwell_otis_1835', lod), before = snapshot(scene);
  const p = V.personVariation({ kit, key, record: persons[key] ?? null, assetId: 'bardwell_otis_1835' });
  const r = V.applyVariation(scene, kit, p, { scope: 'full' });
  assert(r.meshes >= 4, `lod${lod} ${key}: body and clothes varied`);
  assert.equal(scene.scale.x, p.height);
  scene.scale.setScalar(1);   // compare shapes before the height
  const after = snapshot(scene);
  const bodyB = [...before.values()].find(m => m.slot === 'skin'), bodyA = [...after.values()].find(m => m.slot === 'skin');
  // shoes stay on the ground (the soles' lowest point moves under 5 mm)
  const shoesB = [...before.values()].find(m => m.slot === 'footwear'), shoesA = [...after.values()].find(m => m.slot === 'footwear');
  const minY = a => { let m = Infinity; for (let i = 1; i < a.length; i += 3) m = Math.min(m, a[i]); return m; };
  assert(Math.abs(minY(shoesA.pos) - minY(shoesB.pos)) < 0.005, `lod${lod} ${key}: soles stay down`);
  // eyes move whole
  for (const [name, b] of before) {
    if (b.slot !== 'eyes') continue;
    const a = after.get(name).pos; const side = { l: [], r: [] };
    for (let i = 0; i < a.length; i += 3) (b.pos[i] >= 0 ? side.l : side.r).push([a[i] - b.pos[i], a[i + 1] - b.pos[i + 1], a[i + 2] - b.pos[i + 2]]);
    for (const s of Object.values(side)) for (const d of s) assert(Math.hypot(d[0] - s[0][0], d[1] - s[0][1], d[2] - s[0][2]) < 2e-4, `lod${lod} ${key} ${name}: an eye moved whole`);
  }
  // clothes stay outside the skin: no garment vertex that cleared the body by 1.5 mm before
  // is inside it after (a few at seams and hems may graze; none sinks 2 mm)
  for (const [name, b] of before) {
    if (!/^garment/.test(b.slot)) continue;
    const s0 = inside(bodyB, b.pos), s1 = inside(bodyA, after.get(name).pos);
    let sunk = 0, worst = 0;
    s0.forEach((s, i) => { if (s >= 0.0015 && s1[i] < 0) { sunk++; worst = Math.min(worst, s1[i]); } });
    assert(sunk <= Math.max(3, s0.length * 0.003) && worst > -0.002, `lod${lod} ${key} ${name}: ${sunk} vertices sank into the skin (worst ${worst.toFixed(4)} m)`);
  }
  // the shape: shoulder breadth and the face's change agree between LODs within 1.5 cm (LOD3 samples the shoulder coarsely)
  const breadth = a => { let lo = Infinity, hi = -Infinity; for (let i = 0; i < a.length; i += 3) if (a[i + 1] > 1.30 && a[i + 1] < 1.45 && Math.abs(a[i]) < 0.3) { lo = Math.min(lo, a[i]); hi = Math.max(hi, a[i]); } return hi - lo; };
  (summary[key] ??= []).push(breadth(bodyA.pos) - breadth(bodyB.pos));
}
for (const [key, d] of Object.entries(summary)) assert(Math.max(...d) - Math.min(...d) < 0.015, `${key}: build agrees between LODs (${d.map(x => x.toFixed(4))})`);

// One variant per person and LOD: a second figure reuses it; freeing the source frees it.
{ const s1 = await figure('bardwell_otis_1835', 2);
  const clone = SK.clone(s1), sources = new Set(); clone.traverse(o => { if (o.isSkinnedMesh) sources.add(o.geometry); });
  const p = V.personVariation({ kit, key: 'crowd_9', assetId: 'bardwell_otis_1835' });
  V.applyVariation(s1, kit, p);
  const g1 = []; s1.traverse(o => { if (o.isSkinnedMesh) g1.push(o.geometry); });
  V.applyVariation(clone, kit, p);
  const g2 = []; clone.traverse(o => { if (o.isSkinnedMesh) g2.push(o.geometry); });
  assert.deepEqual(g1, g2, 'the second figure reuses the first one\'s variant geometry');
  let disposed = 0; for (const g of g2) if (!sources.has(g)) g.addEventListener('dispose', () => disposed++);
  V.disposeVariants(sources);
  assert(disposed >= 4, 'disposeVariants frees them with their source'); }

// Not an hm08 body (the CI fixture): left as drawn.
{ const scene = await figure('c4d_fixture', 0);
  assert.equal(V.applyVariation(scene, kit, V.personVariation({ kit, key: 'x' })), null); }

console.log(`ok human variation: ${kit.axes.length} axes, no two of 400 alike, seated face only, clothes outside the skin, LODs agree`);
