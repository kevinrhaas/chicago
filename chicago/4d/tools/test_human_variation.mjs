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
const faceAxes = kit.axes.filter(a => a.scope === 'face' && !a.drive && !a.rest);   // a rest axis is never drawn (T-3434)

// The PRNG and a person's values are pure functions of the id.
{ const a = V.seededRandom('x'), b = V.seededRandom('x'), c = V.seededRandom('y');
  const sa = [a(), a(), a()]; assert.deepEqual(sa, [b(), b(), b()]); assert.notDeepEqual(sa, [c(), c(), c()]);
  const p = V.personVariation({ kit, key: 'someone', assetId: 'bardwell_otis_1835' });
  assert.deepEqual(p, V.personVariation({ kit, key: 'someone', assetId: 'bardwell_otis_1835' }));
  assert.equal(p.grade, 'reconstructed');
  for (const a of kit.axes) if (!a.drive) assert(Math.abs(p.values[a.id]) <= header.limit + 1e-12, `${a.id} within the limit`);
  assert(Math.abs(p.height - 1) <= header.height.limit + 1e-12); }

// A body's face_bias (T-3434) leans every draw of a person wearing it, and a rest axis takes only
// the bias: the women's bodies get a resting mouth, a man's none, and nobody else's draws move.
{ const bias = header.assets.williamson_mattie_1904_cook_study.face_bias;
  assert(bias && bias.mouth_corners > 0, 'the 1904 woman carries a face bias with a resting mouth');
  const woman = V.personVariation({ kit, key: 'someone', assetId: 'williamson_mattie_1904_cook_study' });
  const man = V.personVariation({ kit, key: 'someone', assetId: 'bardwell_otis_1835' });
  assert.equal(man.values.mouth_corners, 0, 'a man draws no resting mouth');
  assert.equal(woman.values.mouth_corners, bias.mouth_corners);
  // Her body also damps the seeded face and head outline (face_draw_scale) and allows only the
  // softer head outlines (one_of_allow); a man's draw is the undamped one.
  const asset = header.assets.williamson_mattie_1904_cook_study, scale = asset.face_draw_scale;
  assert(scale > 0 && scale < 1, 'the women damp their seeded faces');
  const damped = a => (a.scope === 'face' || a.id === 'head_shape') ? scale : 1;
  const axis = id => kit.axes.find(a => a.id === id);
  for (const [k, v] of Object.entries(bias)) if (k !== 'mouth_corners')
    assert(Math.abs(woman.values[k] - Math.max(-header.limit, Math.min(header.limit, man.values[k] * damped(axis(k)) + v))) < 1e-12, `${k} leans by its bias`);
  for (const a of kit.axes) if (!a.drive && !(a.id in bias) && !(a.draw_as in bias) && a.sex !== 'female' && a.sex !== 'male')
    assert(Math.abs(woman.values[a.id] - man.values[a.id] * damped(a)) < 1e-12, `${a.id} unmoved by the bias`);
  const allow = asset.one_of_allow.head_shape;
  for (let i = 0; i < 200; i++) {
    const w = V.personVariation({ kit, key: `woman_${i}`, assetId: 'williamson_mattie_1904_cook_study' });
    assert(allow.includes(w.option.head_shape), `a woman's head outline is one of ${allow}`);
  }
  const men = new Set(Array.from({ length: 200 }, (_, i) => V.personVariation({ kit, key: `woman_${i}`, assetId: 'bardwell_otis_1835' }).option.head_shape));
  assert(men.has(2) || men.has(3), 'a man may still draw a square or rectangular head'); }

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
  // T-3553: the key the figure was drawn by is left on its root, for the layers that are told no name (an unnamed figure's teeth).
  assert.equal(scene.userData.chiVariationKey, 'pa1904_otis_f_r_c1900_hans_johnson');
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

// T-3423: a woman on foot takes the female build axes, never the male ones, and a female
// axis shares its male twin's draw: nobody's values move because the female targets exist.
{ const female = kit.axes.filter(a => a.sex === 'female');
  assert(female.length >= 3 && female.every(a => a.draw_as && kit.axes.some(b => b.id === a.draw_as && b.sex === 'male')), 'each female axis names its male twin');
  const p = V.personVariation({ kit, key: 'crowd_3', assetId: 'flynn_mary_1835_dress_study' });
  assert.equal(p.sex, 'female');
  for (const a of female) if (!a.drive) assert.equal(p.values[a.id], p.values[a.draw_as], `${a.id} takes ${a.draw_as}'s draw`);
  const dense = V.denseDelta(kit, p, 'full'), male = V.denseDelta(kit, { ...p, sex: 'male' }, 'full');
  let differ = 0; for (let i = 0; i < dense.length; i++) if (Math.abs(dense[i] - male[i]) > 1e-6) differ++;
  assert(differ > 1000, `the female build moves the body differently from the male (${differ} components)`);
  for (const lod of [0, 3]) {
    const scene = await figure('flynn_mary_1835_dress_study', lod), before = snapshot(scene);
    const r = V.applyVariation(scene, kit, p, { scope: 'full' });
    assert(r.meshes >= 4, `woman lod${lod}: body and dress varied`);
    scene.scale.setScalar(1);
    const after = snapshot(scene);
    const minY = a => { let m = Infinity; for (let i = 1; i < a.length; i += 3) m = Math.min(m, a[i]); return m; };
    const shoesB = [...before.values()].find(m => m.slot === 'footwear'), shoesA = [...after.values()].find(m => m.slot === 'footwear');
    assert(Math.abs(minY(shoesA.pos) - minY(shoesB.pos)) < 0.005, `woman lod${lod}: soles stay down`);
  }
}

// T-3553: a standing collar worn lower (`dress.collar`, Sarah Grey: "her clothing is going over
// her chin, it should just be her neck"): its top comes down by what it names, it stays outside
// the skin, and a figure without one keeps the body's collar where it was.
{ const key = 'pa1904_grey_mrs_w_l', rec = persons[key], collar = rec?.dress?.collar;
  assert(collar?.piece === 'lady_shirtwaist_collar' && collar.lower_cm > 0, `${key} wears her collar lowered`);
  const top = a => { let m = -Infinity; for (let i = 1; i < a.length; i += 3) m = Math.max(m, a[i]); return m; };
  for (const lod of [0, 3]) {
    const tops = [];
    for (const r of [rec, { ...rec, dress: { ...rec.dress, collar: undefined } }]) {
      const scene = await figure('glessner_frances_m_1904', lod), before = snapshot(scene);
      V.applyVariation(scene, kit, V.personVariation({ kit, key, record: r, assetId: 'glessner_frances_m_1904' }), { scope: 'full' });
      scene.scale.setScalar(1);
      const after = snapshot(scene), name = [...after.keys()].find(n => /shirtwaist_collar/.test(after.get(n).mesh.name));
      assert(name, `lod${lod}: the lady's body has its collar`);
      const bodyA = [...after.values()].find(m => m.slot === 'skin'), s1 = inside(bodyA, after.get(name).pos);
      const sunk = s1.filter(x => x < -0.002).length;
      // (the body's own collar, under her chin, is what sank: only the lowered one is held to it)
      if (r === rec) assert(sunk <= Math.max(3, s1.length * 0.003), `lod${lod}: ${sunk} collar vertices sank into the neck`);
      tops.push(top(after.get(name).pos) - top(before.get(name).pos));
    }
    assert(tops[0] < tops[1] - collar.lower_cm / 100 * 0.6, `lod${lod}: the collar's top comes down (${tops.map(t => t.toFixed(4))})`);
  }
}

// T-3553: a smile the face moves into (`skin.smile`: William Grey's from his sheet's front
// picture, Sarah Grey's from a picture of her own smile). At a level whose face moves it is one
// more morph target of the body after the body's own, each vertex its kit vertex's move, named
// on the mesh and resting; the source's targets are not touched; a far level, and anyone
// without a smile, gets none.
for (const [key, asset] of [['pa1904_grey_w_l', 'glessner_john_j_1904'], ['pa1904_grey_mrs_w_l', 'glessner_frances_m_1904']]) {
  const rec = persons[key], sm = rec?.skin?.smile;
  assert(sm?.vertices?.length > 100 && sm.delta.length === sm.vertices.length * 3, `${key} has a smile`);
  const sheets = { ...kit, base: 'http://localhost/assets/humans/web/hm08_variation_kit.json' };   // a kit read from a URL (likenessSkin)
  let most = 0;
  for (let j = 0; j < sm.delta.length; j += 3) most = Math.max(most, Math.hypot(sm.delta[j], sm.delta[j + 1], sm.delta[j + 2]) * kit.unit);
  const skinOf = scene => { let m = null; scene.traverse(o => { if (o.isSkinnedMesh && o.material.name.split('__')[0] === 'skin') m = o; }); return m; };
  for (const lod of [0, 1, 3]) {
    const scene = await figure(asset, lod), body = skinOf(scene), src = body.geometry;
    const had = Object.keys(body.morphTargetDictionary ?? {}).length, own = src.morphAttributes.position?.slice() ?? [];
    V.applyVariation(scene, sheets, V.personVariation({ kit, key, record: rec, assetId: asset }), { scope: 'full' });
    const g = body.geometry, at = body.morphTargetDictionary?.[V.SMILE];
    if (!had) { assert.equal(at, undefined, `lod${lod}: a face that does not move gets no smile`); continue; }
    assert.equal(at, had, `lod${lod}: the smile follows the body's own targets`);
    assert.equal(body.morphTargetInfluences.length, had + 1);
    assert.equal(body.morphTargetInfluences[at], 0, 'and rests');
    assert.equal(g.morphAttributes.position.length, had + 1);
    assert.equal(g.morphAttributes.normal?.length ?? had + 1, had + 1, 'a normal for every target');
    assert.deepEqual(src.morphAttributes.position, own, "the source's own targets are as they were");
    const t = g.morphAttributes.position[at], sk = body.skeleton;
    assert.equal(t.count, g.attributes.position.count);
    const scale = new THREE.Matrix4().multiplyMatrices(sk.bones[0].matrixWorld, sk.boneInverses[0]).multiply(body.bindMatrix).elements[0] / scene.scale.x;
    let far = 0, movers = 0;
    for (let i = 0; i < t.count; i++) { const d = Math.hypot(t.getX(i), t.getY(i), t.getZ(i)) * scale; far = Math.max(far, d); if (d > 1e-5) movers++; }
    // A simplified level has fewer of the lips' vertices, but its furthest is one of the record's.
    assert(far <= most * 1.001 && far > most * (lod ? .5 : .999), `lod${lod}: the furthest move is the record's (${far.toFixed(5)} of ${most.toFixed(5)} m)`);
    assert(movers > 100 && movers < t.count * .25, `lod${lod}: only the face round the mouth moves (${movers} of ${t.count})`);
    // Its second figure shares the geometry and is named the same way.
    const again = await figure(asset, lod), twin = skinOf(again);
    twin.geometry = src;
    V.applyVariation(again, sheets, V.personVariation({ kit, key, record: rec, assetId: asset }), { scope: 'full' });
    assert(twin.geometry === g && twin.morphTargetDictionary[V.SMILE] === at && twin.morphTargetInfluences.length === had + 1, `lod${lod}: a second figure of ${key} smiles the same way`);
  }
  assert(!persons.pa1904_field_marshall.skin?.smile, 'a neighbour whose face is fitted and has no smile');
  for (const [who, k, r] of [['someone of the crowd', 'crowd_3', null], ['a neighbour with a fitted face', 'pa1904_field_marshall', persons.pa1904_field_marshall]]) {
    const scene = await figure(asset, 0), body = skinOf(scene);
    V.applyVariation(scene, sheets, V.personVariation({ kit, key: k, record: r, assetId: asset }), { scope: 'full' });
    assert.equal(body.morphTargetDictionary[V.SMILE], undefined, `${who} has no smile`);
    assert.equal(body.geometry.morphAttributes.position.length, 3);
  }
}

let faceCensus = '';
// T-3553: a face from the library (libraryFace; the kit's `faces`, tools/face_library.py). A
// person with no pictures of their own takes one face of their own sex, of their age's third
// or a younger one, nearer their tone likelier, the body's own skin one of the draw; seeded by
// their id; never one for a face fitted to pictures, a body the library does not know, or a
// kit that was not read from an address.
{ const F = header.faces, based = { ...kit, base: 'http://example.invalid/humans/hm08_variation_kit.json' };
  assert(F && F.faces.length >= 20 && F.faces.length <= F.cols * Math.floor(F.size_px[1] / F.tile_px) && F.size_px[0] === F.cols * F.tile_px, 'the kit carries the library, every face on the sheet');
  for (const sex of ['female', 'male']) for (const age of ['young', 'middle', 'old']) assert(F.faces.some(f => f.sex === sex && f.age === age), `a ${age} ${sex} face`);
  assert(F.faces.every(f => f.tone > 0.1 && f.tone < 0.7 && /^[a-z0-9_]+$/.test(f.id)) && new Set(F.faces.map(f => f.id)).size === F.faces.length);
  assert(Object.keys(F.bodies).length >= 35 && Object.values(F.bodies).every(b => b.gain.length === 3 && b.gain.every(g => g > 0.8 && g < 3) && b.tone_rgb.length === 3), 'every body has its gain');
  assert(F.younger_likelier > 0 && F.younger_likelier < 1 && F.lines.young === 1 && F.lines.middle < 1 && F.lines.old < F.lines.middle && F.lines.old > 0);
  // A person's tone is read from the skin most bodies of their sex wear (a body recorded as
  // neither sex is counted for neither), not from the body they happen to be drawn on.
  { const most = (sex) => { const n = new Map();
      for (const [id, b] of Object.entries(F.bodies)) if ((header.assets[id]?.sex ?? 'male') === sex) n.set(String(b.tone_rgb), (n.get(String(b.tone_rgb)) ?? 0) + 1);
      const [first, second] = [...n].sort((a, b) => b[1] - a[1]);
      assert(first && (!second || first[1] > second[1]), `one skin is worn by most ${sex} bodies`);
      return first[0]; };
    assert.deepEqual(Object.keys(F.person_tone_rgb).sort(), ['female', 'male']);
    for (const sex of ['female', 'male']) assert.equal(String(F.person_tone_rgb[sex]), most(sex), `a ${sex} person's tone is the skin most ${sex} bodies wear`);
    assert.notEqual(String(F.person_tone_rgb.male), String(F.person_tone_rgb.female)); }
  const thirds = ['young', 'middle', 'old'];
  const crowd = (over, n = 600) => Array.from({ length: n }, (_, k) => V.libraryFace(based, { key: `face_${k}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair', ...over }));
  const count = (list, test) => list.filter(f => f && test(F.faces[f.index])).length;
  // Pure, and what the shader is handed.
  const one = crowd({}).find(Boolean);
  assert.deepEqual(crowd({}), crowd({}), 'the same people, the same faces');
  assert.equal(one.url, 'http://example.invalid/humans/faces/hm08_faces.jpg');
  assert.deepEqual([one.cols, one.size_px, one.tile_px, one.gain, one.id], [F.cols, F.size_px, F.tile_px, F.bodies.bardwell_otis_1835.gain, F.faces[one.index].id]);
  assert.notEqual(one.gain, F.bodies.bardwell_otis_1835.gain, 'its own copy of the gain');
  // A young man: a young man's face or his body's own; several faces among a crowd.
  const young = crowd({});
  assert(young.every(f => f === null || (F.faces[f.index].sex === 'male' && F.faces[f.index].age === 'young' && f.lines === 1)), 'a young man takes a young man\'s face');
  assert(young.filter(f => f === null).length > 30 && new Set(young.filter(Boolean).map(f => f.index)).size >= 3, 'some keep the body\'s own skin, the rest wear several faces');
  // Middle-aged: his own third's or a younger one's, the younger less often for each one there is; never an old face.
  const middle = crowd({ age: 45 });
  assert(middle.every(f => f === null || (F.faces[f.index].sex === 'male' && F.faces[f.index].age !== 'old' && f.lines === F.lines[F.faces[f.index].age])), 'a middle-aged man takes no old face, and keeps the lines his face\'s age keeps');
  const per = (list, age) => count(list, f => f.age === age) / F.faces.filter(f => f.sex === 'male' && f.age === age && !f.light_only).length;
  assert(count(middle, f => f.age === 'middle') > 0 && count(middle, f => f.age === 'young') > 0 && per(middle, 'young') < per(middle, 'middle'), 'a younger face is the less likely one');
  const old = crowd({ age: 70 });
  for (const age of thirds) assert(count(old, f => f.age === age) > 0, `an old man may wear a ${age} face`);
  assert(old.every(f => f === null || F.faces[f.index].sex === 'male'));
  // A woman a woman's; a child of either sex a young woman's; an age unknown is taken as young.
  assert(crowd({ sex: 'female', assetId: 'glessner_frances_m_1904' }).every(f => f === null || (F.faces[f.index].sex === 'female' && F.faces[f.index].age === 'young')));
  for (const sex of ['male', 'female', 'either']) assert(crowd({ sex, age: 8, assetId: 'child_boy_1904' }, 200).every(f => f === null || (F.faces[f.index].sex === 'female' && F.faces[f.index].age === 'young')), 'a child wears a young woman\'s face');
  assert(crowd({ age: null }, 200).every(f => f === null || F.faces[f.index].age === 'young'));
  for (const age of [null, undefined, NaN]) assert(crowd({ age }, 200).every(f => f === null || F.faces[f.index].sex === 'male'), 'a man of no known age is a young man, not a child: he wears a man\'s face');
  // A person with no recorded complexion is read under no tint: whatever the named ones are.
  { const tinted = { ...based, header: { ...header, faces: { ...F, complexions: Object.fromEntries(Object.keys(F.complexions).map(k => [k, [0.3, 0.3, 0.3]])) } } };
    const worn = (k, complexion) => Array.from({ length: 400 }, (_, i) => V.libraryFace(k, { key: `untinted_${i}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion })?.id ?? null);
    assert.deepEqual(worn(tinted, null), worn(based, null), 'no complexion recorded: no tint');
    assert.notDeepEqual(worn(tinted, 'fair'), worn(based, 'fair')); }
  // The thirds turn at the kit's own ages, to the day: a child until thirteen, young until
  // thirty-six, old from sixty; and a grown person recorded as neither sex wears a woman's.
  assert.deepEqual(F.ages, { middle_from: 36, old_from: 60, child_under: 13 });
  const ages = (age, over = {}) => new Set(crowd({ age, ...over }, 400).filter(Boolean).map(f => `${F.faces[f.index].sex} ${F.faces[f.index].age}`));
  assert.deepEqual([...ages(12.99)], ['female young'], 'a boy the day before thirteen wears a young woman\'s face');
  assert.deepEqual([...ages(13)], ['male young'], 'at thirteen a young man\'s');
  assert.deepEqual([...ages(35.99)], ['male young']);
  assert.deepEqual([...ages(36)].sort(), ['male middle', 'male young'], 'at thirty-six a middle-aged face may be his');
  assert.deepEqual([...ages(59.99)].sort(), ['male middle', 'male young']);
  assert.deepEqual([...ages(60)].sort(), ['male middle', 'male old', 'male young'], 'at sixty an old one');
  assert.deepEqual([...ages(45, { sex: 'either' })].sort(), ['female middle', 'female young'], 'a grown person recorded as neither wears a woman\'s face');
  // The same person, the same face, on any day: these are pinned, so a change to the seed, to
  // the rule or to the library's faces is seen here (a face added changes who wears which).
  for (const [key, ask, id] of [
    ['face_0', { assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair' }, 'toigo_ginger_male'],
    ['face_1', { assetId: 'bardwell_otis_1835', sex: 'male', age: 45, complexion: 'copper' }, 'middleage_lightskinned_male'],
    ['face_2', { assetId: 'potawatomi_woman_1812', sex: 'female', age: 70, complexion: 'tan' }, 'onlytheghosts_old_female'],
    ['face_3', { assetId: 'glessner_frances_m_1904', sex: 'female', age: 22, complexion: 'ruddy' }, 'cutoff3d_female'],
    ['face_4', { assetId: 'child_boy_1904', sex: 'male', age: 8, complexion: 'light' }, 'young_lightskinned_female_2'],
    ['face_5', { assetId: 'bardwell_otis_1835', sex: 'male', age: 64, complexion: null }, 'onlytheghosts_old_male']])
    assert.equal(V.libraryFace(based, { key, ...ask })?.id ?? null, id, `${key}: the face this person has always had`);
  // The body's own skin is one of the draw, as likely as the person's tone is near itself
  // under their complexion: by the person's tone (the skin most bodies of their sex wear), so
  // the share is the same on a body of that skin and on one of another.
  { const luma = (rgb, tint = [1, 1, 1]) => 0.2126 * rgb[0] * tint[0] + 0.7152 * rgb[1] * tint[1] + 0.0722 * rgb[2] * tint[2];
    const bell = d => Math.exp(-d * d / (2 * F.nearer_tone_likelier ** 2));
    for (const [sex, usual, other] of [['male', 'bardwell_otis_1835', 'nelson_charles_1904_coachman'], ['female', 'potawatomi_woman_1812', 'flynn_mary_1835_dress_study']]) {
      const skin = F.person_tone_rgb[sex];
      assert.deepEqual(F.bodies[usual].tone_rgb, skin);
      assert.notDeepEqual(F.bodies[other].tone_rgb, skin, `a ${sex} body of another skin than most`);
      for (const complexion of ['fair', 'copper', null]) {
        const tone = luma(skin, F.complexions[complexion]), own = bell(Math.log2(luma(skin) / tone));
        const worn = F.faces.filter(f => f.sex === sex && f.age === 'young' && Math.log2(f.tone / tone) >= -F.never_darker_than && (!f.light_only || F.light_only_for.includes(complexion)));
        const want = own / (own + worn.reduce((a, f) => a + bell(Math.log2(f.tone / tone)), 0)), n = 3000;
        for (const assetId of [usual, other]) {
          const got = crowd({ sex, complexion, assetId }, n).filter(f => f === null).length / n;
          assert(want > 0.1 && want < 0.5 && Math.abs(got - want) < 0.03, `a ${sex}, ${complexion}, on ${assetId}: ${(got * 100).toFixed(1)}% keep the body's own skin, the draw says ${(want * 100).toFixed(1)}%`);
        }
      }
    } }
  // Whose skin a person's tone is read from: a man's and a boy's from the men's, everybody
  // else's (a woman, a girl, a person recorded as neither sex) from the women's. Shown by
  // darkening one sex's tone in a copy of the kit and seeing whose faces move with it: a boy
  // under thirteen wears a young woman's face and is still read by the men's skin.
  { const darker = (which) => ({ ...based, header: { ...header, faces: { ...F, person_tone_rgb: { ...F.person_tone_rgb, [which]: F.person_tone_rgb[which].map(x => x * 0.45) } } } });
    const faces = (k, ask) => Array.from({ length: 400 }, (_, i) => V.libraryFace(k, { key: `whose_${i}`, complexion: 'fair', ...ask })?.id ?? null);
    for (const [who, ask, reads] of [
      ['a man', { sex: 'male', age: 30, assetId: 'bardwell_otis_1835' }, 'male'],
      ['a boy under thirteen', { sex: 'male', age: 8, assetId: 'child_boy_1904' }, 'male'],
      ['a woman', { sex: 'female', age: 30, assetId: 'potawatomi_woman_1812' }, 'female'],
      ['a girl', { sex: 'female', age: 8, assetId: 'child_girl_1904' }, 'female'],
      ['a grown person recorded as neither sex', { sex: 'either', age: 30, assetId: 'potawatomi_woman_1812' }, 'female'],
      ['a child recorded as neither sex', { sex: 'either', age: 3, assetId: 'child_toddler_1904' }, 'female']]) {
      const as = faces(based, ask);
      assert(as.filter(Boolean).length > 100, `${who}: the library knows the body`);
      for (const which of ['male', 'female']) {
        const moved = faces(darker(which), ask).filter((id, i) => id !== as[i]).length;
        if (which === reads) assert(moved > 40, `${who} is read by the ${which} skin (${moved} of 400 faces move with it)`);
        else assert.equal(moved, 0, `${who} is not read by the ${which} skin`);
      }
    } }
  // How much less likely a younger face is: each third younger `younger_likelier` (a half) as
  // likely. A middle-aged man's share of young faces, and an old man's of young and of
  // middle-aged ones, are the draw's own figures.
  // ...and both that figure and the width of the bell of tone are the kit's own, as the bar on
  // darker faces is: a kit that says a quarter, or a bell half as wide, is drawn by what it
  // says, and one that does not say how likely a younger face is hands out none.
  { const luma = (rgb, tint = [1, 1, 1]) => 0.2126 * rgb[0] * tint[0] + 0.7152 * rgb[1] * tint[1] + 0.0722 * rgb[2] * tint[2];
    assert.deepEqual([F.younger_likelier, F.nearer_tone_likelier], [0.5, 1]);
    for (const [what, G] of [['the kit as built', F], ['a kit where a younger face is a quarter as likely', { ...F, younger_likelier: 0.25 }],
      ['a kit that does not say how likely a younger face is', { ...F, younger_likelier: undefined }], ['a kit whose bell of tone is half as wide', { ...F, nearer_tone_likelier: 0.5 }]]) {
      const of_kit = G === F ? based : { ...based, header: { ...header, faces: G } };
      const bell = d => Math.exp(-d * d / (2 * G.nearer_tone_likelier ** 2));
      for (const [age, third] of [[45, 1], [70, 2]]) for (const complexion of ['copper', null]) {
        const tone = luma(G.person_tone_rgb.male, G.complexions[complexion]);
        const may = G.faces.filter(f => f.sex === 'male' && thirds.indexOf(f.age) <= third && Math.log2(f.tone / tone) >= -G.never_darker_than && (!f.light_only || G.light_only_for.includes(complexion)));
        const weight = f => bell(Math.log2(f.tone / tone)) * (G.younger_likelier ?? 0) ** (third - thirds.indexOf(f.age));
        const all = may.reduce((a, f) => a + weight(f), 0);
        const got = Array.from({ length: 4000 }, (_, k) => V.libraryFace(of_kit, { key: `face_${k}`, assetId: 'bardwell_otis_1835', sex: 'male', age, complexion })).filter(Boolean);
        for (const of of thirds.slice(0, third + 1)) {
          const want = may.filter(f => f.age === of).reduce((a, f) => a + weight(f), 0) / all, share = count(got, f => f.age === of) / got.length;
          assert((G !== F || want > 0.05) && Math.abs(share - want) < 0.03, `${what}: a man of ${age}, ${complexion}: ${(share * 100).toFixed(1)}% of the faces worn are ${of}, the draw says ${(want * 100).toFixed(1)}%`);
        }
        // Within a third, too, the nearer tone is the likelier, by the bell's own width.
        const [near, far] = may.filter(f => thirds.indexOf(f.age) === third).sort((a, b) => weight(b) - weight(a)).filter((f, i, l) => i === 0 || i === l.length - 1);
        if (far && weight(near) / all > 0.08) {
          const share = count(got, f => f.id === near.id) / got.length;
          assert(Math.abs(share - weight(near) / all) < 0.03, `${what}: a man of ${age}, ${complexion}: ${(share * 100).toFixed(1)}% wear ${near.id}, the nearest in tone, the draw says ${(weight(near) / all * 100).toFixed(1)}%`);
        }
      }
    } }
  // One person, one face, on every body they are drawn as: the three 1904 coachmen sit a box
  // on one body and stand at their door on another of another skin. The face is the same; the
  // gain that brings it to the skin around it is each body's own.
  { const tones = new Map();
    for (const [id, b] of Object.entries(F.bodies)) if (header.assets[id]?.sex === 'male' && !tones.has(String(b.tone_rgb))) tones.set(String(b.tone_rgb), id);
    assert(tones.size >= 2, 'men are drawn on bodies of more than one skin');
    assert.notDeepEqual(F.bodies.anonymous_working_driver_1904.tone_rgb, F.bodies.nelson_charles_1904_coachman.tone_rgb);
    assert.notDeepEqual(F.bodies.anonymous_working_driver_1904.gain, F.bodies.nelson_charles_1904_coachman.gain);
    let asked = 0, wearing = 0;
    for (const complexion of [...Object.keys(F.complexions), null]) for (const age of [20, 34, 42, 50, 70]) for (let k = 0; k < 60; k++) {
      const on = (assetId) => V.libraryFace(based, { key: `two_bodies_${k}`, assetId, sex: 'male', age, complexion });
      const box = on('anonymous_working_driver_1904'), door = on('nelson_charles_1904_coachman');
      asked++;
      assert.equal(box?.id ?? null, door?.id ?? null, `two_bodies_${k}, ${age}, ${complexion}: one face on the box and at the door`);
      if (!box) continue;
      wearing++;
      assert.deepEqual([box.gain, door.gain], [F.bodies.anonymous_working_driver_1904.gain, F.bodies.nelson_charles_1904_coachman.gain], 'each body its own gain');
    }
    assert(wearing > asked / 2);
    // A kit made before the person's tone was recorded reads the body's skin, as it then did:
    // it still hands faces out, and there the two bodies may differ.
    // (For a man and for a woman; a tone that is not a list of three numbers is no tone.)
    const short = [0.6, 0.3], holed = [0.6, NaN, 0.1];
    for (const without of [undefined, null, {}, { male: short, female: short }, { male: holed, female: holed }, { male: 'abc', female: 'abc' }]) {
      const older = { ...based, header: { ...header, faces: { ...F, person_tone_rgb: without } } };
      for (const [sex, usual, other] of [['male', 'anonymous_working_driver_1904', 'nelson_charles_1904_coachman'], ['female', 'potawatomi_woman_1812', 'flynn_mary_1835_dress_study']]) {
        const on = (assetId, k) => V.libraryFace(older, { key: `two_bodies_${k}`, assetId, sex, age: 42, complexion: 'ruddy' })?.id ?? null;
        const pairs = Array.from({ length: 400 }, (_, k) => [on(usual, k), on(other, k)]);
        assert(pairs.filter(([a]) => a).length > 200, `a kit with no person's tone still hands a ${sex} person faces out`);
        assert(pairs.some(([a, b]) => a !== b), 'and reads the body\'s own skin, so two bodies may differ');
      }
    } }
  // Tone: a freckled face only for the complexions the record names (fair, light, ruddy), not
  // by nearness of tone: a tan or olive person is near those faces and still takes none, and
  // a person with no complexion recorded takes none.
  const freckled = f => f.light_only === true;
  assert.deepEqual(F.light_only_for, ['fair', 'light', 'ruddy']);
  assert(F.faces.filter(freckled).length >= 4 && F.faces.filter(freckled).every(f => f.age === 'young'));
  for (const sex of ['male', 'female']) {
    const of = (complexion) => count(crowd({ sex, complexion, assetId: sex === 'male' ? 'bardwell_otis_1835' : 'potawatomi_woman_1812' }), freckled);
    for (const complexion of F.light_only_for) assert(of(complexion) > 0, `a ${complexion} ${sex} may be freckled`);
    for (const complexion of [...Object.keys(F.complexions).filter(c => !F.light_only_for.includes(c)), null, undefined, 'no_such_complexion'])
      assert.equal(of(complexion), 0, `a ${sex} of ${complexion ?? 'no'} complexion is never freckled`);
  }
  for (const without of [undefined, null, 'fair', {}])
    assert.equal(count(Array.from({ length: 300 }, (_, k) => V.libraryFace({ ...based, header: { ...header, faces: { ...F, light_only_for: without } } }, { key: `face_${k}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair' })), freckled), 0,
      'a kit that does not list who may be freckled hands out no freckled face');
  const darkest = F.faces.filter(f => f.sex === 'female' && f.age === 'young').sort((a, b) => a.tone - b.tone)[0];
  const share = (list) => count(list, f => f.id === darkest.id) / Math.max(1, list.filter(Boolean).length);
  assert(share(crowd({ sex: 'female', assetId: 'potawatomi_woman_1812', complexion: 'deep_brown' })) > share(crowd({ sex: 'female', assetId: 'potawatomi_woman_1812', complexion: 'fair' })), 'the nearer tone is the likelier');
  // A face much darker than the person is never theirs (a library with one such face added).
  { const more = { ...based, header: { ...header, faces: { ...F, faces: [...F.faces, { id: 'far_darker', sex: 'male', age: 'young', tone: 0.08 }] } } };
    const any = Array.from({ length: 600 }, (_, k) => V.libraryFace(more, { key: `face_${k}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair' }));
    assert(any.every(f => f?.id !== 'far_darker'), 'a fair man never takes a face far darker than he is');
    assert(Array.from({ length: 600 }, (_, k) => V.libraryFace(more, { key: `face_${k}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'deep_brown' })).some(f => f?.id === 'far_darker'), 'a man of deep brown complexion may'); }
  // The bar stands at the kit's `never_darker_than` doublings of light (one), to half a
  // hundredth of a doubling: of two faces added, one that little under the bar from a fair man
  // and one that little over, he may take the first and never the second. And it is the kit's
  // own figure that is read: with the bar set at two doublings, a face one and a half darker
  // may be his and one a little over two never.
  { const tone = [0.2126, 0.7152, 0.0722].reduce((a, w, k) => a + w * F.person_tone_rgb.male[k] * F.complexions.fair[k], 0);
    assert.equal(F.never_darker_than, 1);
    const added = (bar, list) => ({ ...based, header: { ...header, faces: { ...F, never_darker_than: bar,
      faces: [...F.faces, ...list.map(([id, darker]) => ({ id, sex: 'male', age: 'young', tone: tone * 2 ** -darker }))] } } });
    const worn = (k) => Array.from({ length: 1500 }, (_, i) => V.libraryFace(k, { key: `face_${i}`, assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair' })?.id);
    const any = worn(added(1, [['just_within', 0.995], ['just_beyond', 1.005]]));
    assert(any.includes('just_within'), 'a face a little under one doubling darker may be his');
    assert(!any.includes('just_beyond'), 'a face a little over one doubling darker never is');
    const wider = worn(added(2, [['half_past', 1.5], ['past_two', 2.005]]));
    assert(wider.includes('half_past') && !wider.includes('past_two'), 'the bar is the kit\'s own figure, not a fixed one'); }
  // None: a face fitted to pictures, a body the library does not know, a kit with no address or no library.
  const ask = { key: 'face_1', assetId: 'bardwell_otis_1835', sex: 'male', age: 30, complexion: 'fair' };
  for (const [why, k, over] of [['a face of its own', based, { own: true }], ['an unknown body', based, { assetId: 'c4d_fixture' }], ['a kit with no address', kit, {}],
    ['a kit with no library', { ...based, header: { ...header, faces: undefined } }, {}]])
    assert.equal(Array.from({ length: 50 }, (_, j) => V.libraryFace(k, { ...ask, key: `face_${j}`, ...over })).filter(Boolean).length, 0, `${why}: no face from the library`);
  // A person's variation carries it: by their record's sex, age and complexion; never for a
  // face fitted to pictures (the Greys' and the rest of the fitted); and applyVariation leaves
  // it on the figure for the skin (human-skin.js), a sheet of the person's own in its place.
  const drawn = Object.entries(persons).filter(([, r]) => !r.face?.values && !r.skin).slice(0, 300);
  const given = drawn.map(([key, record]) => [key, record, V.personVariation({ kit: based, key, record, assetId: 'bardwell_otis_1835' })]);
  assert(given.filter(([, , v]) => v.lib).length > given.length / 2, 'most people with no pictures take a face from the library');
  for (const [key, record, v] of given.slice(0, 40))
    assert.deepEqual(v.lib, V.libraryFace(based, { key, assetId: 'bardwell_otis_1835', sex: record.sex ?? 'male', age: v.age, complexion: record.looks?.complexion?.drawn ?? null }), `${key}: by the record`);
  const fitted = Object.entries(persons).filter(([, r]) => r.face?.values);
  assert(fitted.length >= 20 && fitted.some(([k]) => k === 'pa1904_grey_w_l'));
  for (const [key, record] of fitted) assert.equal(V.personVariation({ kit: based, key, record, assetId: 'glessner_john_j_1904' }).lib, null, `${key}: a face fitted to pictures keeps its own skin`);
  assert.equal(V.personVariation({ kit, key: given[0][0], record: given[0][1], assetId: 'bardwell_otis_1835' }).lib, null, 'a kit with no address hands out none');
  { const [key, record, v] = given.find(([, , x]) => x.lib), scene = await figure('bardwell_otis_1835', 2);
    V.applyVariation(scene, based, v, { scope: 'full' });
    assert.deepEqual(scene.userData.chiFaceSkin, v.lib, `${key}: the figure carries its face`);
    assert.equal(scene.userData.chiLikenessSkin, undefined);
    const [k2, , v2] = given.find(([, , x]) => !x.lib), plain = await figure('bardwell_otis_1835', 2);
    V.applyVariation(plain, based, v2, { scope: 'full' });
    assert.equal(plain.userData.chiFaceSkin, undefined, `${k2}: a person who keeps the body's own skin carries none`);
    const grey = await figure('glessner_john_j_1904', 2), gv = V.personVariation({ kit: based, key: 'pa1904_grey_w_l', record: persons.pa1904_grey_w_l, assetId: 'glessner_john_j_1904' });
    V.applyVariation(grey, based, gv, { scope: 'full' });
    assert(grey.userData.chiLikenessSkin?.url && grey.userData.chiFaceSkin === undefined, 'a person with a sheet of their own wears it, and no face from the library'); }
  // What the draw reads of the body: nothing of its skin, but the person's sex and age where
  // their record has none (the record's first, then the body's; a body the kit does not list
  // is a man's). So a person with no recorded sex wears a woman's face on a woman's body and a
  // man's on a man's, and one with no recorded age is a child on a child's body. One face on
  // every body a person is drawn as is held by the census below, over the rows there are.
  { const of = (record, assetId, n = 300) => Array.from({ length: n }, (_, k) => V.personVariation({ kit: based, key: `reads_${k}`, record, assetId }));
    const sexes = (record, assetId) => { const worn = of(record, assetId).filter(v => v.lib).map(v => F.faces[v.lib.index].sex);
      assert(worn.length > 100); return [...new Set(worn)].join(); };
    const grown = { age: { years: 30 } };
    assert.equal(sexes({ ...grown, sex: 'female' }, 'bardwell_otis_1835'), 'female', 'the record\'s sex is read before the body\'s');
    assert.equal(sexes({ ...grown, sex: 'male' }, 'potawatomi_woman_1812'), 'male', 'the record\'s sex is read before the body\'s');
    assert.equal(sexes(grown, 'potawatomi_woman_1812'), 'female', 'no sex recorded: the body\'s');
    assert.equal(sexes(grown, 'bardwell_otis_1835'), 'male', 'no sex recorded: the body\'s');
    assert.equal(sexes({ ...grown, sex: 'male' }, 'child_toddler_1904'), 'male', 'the record\'s sex is read before that of a body for either sex');
    assert.equal(header.assets.glessner_john_j_1904, undefined, 'the one body of the library the kit does not list (if it is listed now, say so in liberty L-face-library-3553, whose second Revised line counts the people it stands for)');
    assert.equal(sexes(grown, 'glessner_john_j_1904'), 'male', 'no sex recorded, on a body the kit does not list: a man\'s');
    const [from, to] = header.age.default_band_years, boy = header.assets.child_boy_1904.base_age_years;
    assert(boy < F.ages.child_under && from >= F.ages.child_under);
    assert(of({ sex: 'male' }, 'bardwell_otis_1835').every(v => v.age >= from && v.age <= to), 'no age recorded, on a grown body: an age of the kit\'s band');
    const small = of({ sex: 'male' }, 'child_boy_1904');
    assert(small.every(v => v.age === boy) && small.filter(v => v.lib).length > 100 && small.every(v => !v.lib || (F.faces[v.lib.index].sex === 'female' && F.faces[v.lib.index].age === 'young')),
      'no age recorded, on a child\'s body: a child, who wears a young woman\'s face');
    assert(of({ sex: 'male', age: { years: 41 } }, 'child_boy_1904').every(v => v.age === 41 && (!v.lib || F.faces[v.lib.index].sex === 'male')), 'the record\'s age is read before the body\'s');
    assert(of({ sex: 'male', age: { band: [14, 14] } }, 'child_boy_1904').every(v => v.age === 14 && (!v.lib || F.faces[v.lib.index].sex === 'male')), 'and so is a recorded span of ages');
    // An age inside a recorded span is the person's own draw over the whole of it; the face
    // goes by the age as it is, not rounded; a stand-in drawn at another age wears that age's.
    const span = of({ sex: 'male', age: { band: [20, 60] } }, 'bardwell_otis_1835').map(v => v.age);
    assert(span.every(a => a >= 20 && a <= 60) && Math.min(...span) < 24 && Math.max(...span) > 56 && new Set(span).size > 250, 'an age is drawn over the whole of a recorded span');
    assert(of({ sex: 'male', age: { years: F.ages.middle_from - 0.4 } }, 'bardwell_otis_1835').every(v => !v.lib || F.faces[v.lib.index].age === 'young'), 'a man some months short of the middle third wears no middle-aged face');
    assert(of({ sex: 'male', age: { years: 70 }, looks: { drawn_age: { years: 30 } } }, 'bardwell_otis_1835').every(v => v.age === 30 && (!v.lib || F.faces[v.lib.index].age === 'young')), 'a stand-in drawn at thirty wears a young face, whatever his own age');
    // No sex recorded, on a body for either sex: not a man. Their tone is the women's skin.
    assert.equal(header.assets.child_toddler_1904.sex, 'either');
    const worn = (k) => Array.from({ length: 400 }, (_, i) => V.personVariation({ kit: k, key: `either_${i}`, record: { looks: { complexion: { drawn: 'fair' } } }, assetId: 'child_toddler_1904' }).lib?.id ?? null);
    const dark = (which) => ({ ...based, header: { ...header, faces: { ...F, person_tone_rgb: { ...F.person_tone_rgb, [which]: F.person_tone_rgb[which].map(x => x * 0.45) } } } });
    const as_is = worn(based);
    assert(as_is.filter(Boolean).length > 100);
    assert.equal(worn(dark('male')).filter((id, i) => id !== as_is[i]).length, 0, 'no sex recorded, on a body for either sex: not read by the men\'s skin');
    assert(worn(dark('female')).filter((id, i) => id !== as_is[i]).length > 40, 'no sex recorded, on a body for either sex: read by the women\'s skin'); }
  // Everybody the scenes draw, on every body they are drawn as (a row of a household file, a
  // figure of their own, or the driver of a carriage or wagon): nobody recorded a man or a
  // woman wears the other's face, nobody a face older than they are, a child a young woman's,
  // a freckled face only a fair, light or ruddy person; and a person drawn on two bodies wears
  // one face on both.
  { const docs = new Map(), read = async (file) => { if (!docs.has(file)) docs.set(file, JSON.parse(await fs.readFile(new URL(file, here)))); return docs.get(file); };
    const bodyOf = (doc, row) => row == null ? doc.appearance?.asset_id : doc.people?.find(p => p.person === row)?.asset_id ?? doc.rows?.find(r => r.id === row && r.driver_asset)?.driver_asset;
    let seen = 0, wear = 0, twice = 0, apart = 0, own = 0, plain = 0;
    const drawnOn = new Map(), wornBy = new Map();
    for (const [key, record] of Object.entries(persons)) {
      const worn = [], on = [];
      for (const at of record.drawn_as ?? []) {
        const [file, row] = at.split('#'), assetId = bodyOf(await read(file), row);
        assert(assetId && F.bodies[assetId], `${key}: ${at} names a body the library knows`);
        if (file.endsWith('loops.json')) assert.equal((await read(file)).rows.find(r => r.id === row).person_id, key, `${at} is driven by ${key}`);
        const v = V.personVariation({ kit: based, key, record, assetId, sceneYear: Number(record.scene) || null });
        worn.push(v.lib?.id ?? null); on.push(assetId);
        if (!v.lib) continue;
        const f = F.faces[v.lib.index], sex = record.sex ?? header.assets[assetId]?.sex ?? 'male', complexion = record.looks?.complexion?.drawn ?? null;
        assert(!record.face?.values && !record.skin, `${key}: a person with a face or a sheet of their own takes none`);
        assert.deepEqual(v.lib.gain, F.bodies[assetId].gain, `${key}: the gain of the body they are drawn on`);
        const third = !Number.isFinite(v.age) || v.age < F.ages.middle_from ? 0 : v.age < F.ages.old_from ? 1 : 2;
        assert(thirds.indexOf(f.age) <= third, `${key}, ${v.age}, wears a face older than they are (${f.id})`);
        if (v.age < F.ages.child_under) assert(f.sex === 'female' && f.age === 'young', `${key}, a child, wears ${f.id}`);
        else if (sex === 'male' || sex === 'female') assert.equal(f.sex, sex, `${key}, ${record.sex ? 'recorded' : 'drawn on the body of a'} ${sex}, wears ${f.id}`);
        if (f.light_only) assert(F.light_only_for.includes(complexion), `${key}, of ${complexion ?? 'no'} complexion, wears the freckled ${f.id}`);
      }
      if (!worn.length) continue;
      assert.equal(new Set(worn).size, 1, `${key} wears one face on every body they are drawn as (${worn.join(', ')})`);
      seen++;
      if (worn.length > 1) twice++;
      if (new Set(on).size > 1) apart++;
      drawnOn.set(key, on); wornBy.set(key, worn);
      if (worn[0]) wear++; else if (record.face?.values || record.skin) own++; else plain++;
    }
    for (const key of ['pa1904_armour_mrs_philip_d_c1900_joseph_daniels', 'pa1904_otis_f_r_c1900_hans_johnson', 'pa1904_pullman_mrs_george_m_c1900_henry_windish'])
      assert.deepEqual([...drawnOn.get(key)].sort(), ['anonymous_working_driver_1904', 'nelson_charles_1904_coachman'], `${key}, a coachman, is drawn on the box and at his door, on two bodies`);
    // (The others drawn twice stand on one body both times: a figure of their own and the
    // wagon's driver that takes its place.)
    assert(twice >= 6 && apart >= 3, `${twice} people are drawn twice, ${apart} of them on two bodies`);
    // The four people the one-face rule moved, each by name and face, as the liberty's second
    // Revised line tells it (a face added to the library, or a change to the draw, moves
    // people: then the liberty wants another line, and these the new names).
    for (const [key, id] of [['pa1904_armour_mrs_philip_d_c1900_joseph_daniels', 'middleage_lightskinned_male'], ['pa1904_buckingham_clarence', null],
      ['pa1904_mcbirney_george_d', null], ['pa1904_lowden_frank_orren_c1900_clarence_clough', 'young_lightskinned_male']])
      assert.deepEqual([...new Set(wornBy.get(key))], [id], `${key} wears ${id ?? 'the skin of the body they are drawn on'}, as liberty L-face-library-3553 says`);
    assert(seen > 1000 && wear / seen > 0.6 && wear / seen < 0.85, `${wear} of ${seen} people drawn wear a face from the library`);
    faceCensus = `${wear} of ${seen} drawn people wear a library face, ${plain} keep their body's own skin by the draw, ${own} have a face or a sheet of their own; ${twice} are drawn twice, ${apart} of them on two different bodies`; }
}

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

// T-3572: the fit a source keeps for all its wearers, and the bounded search for where a
// garment sits on the varied body, give exactly what a first fit gives: a person built on a
// source two others have worn is, to the bit, the same person built on a freshly parsed one.
for (const [asset, lod] of [['potawatomi_man_1812', 2], ['flynn_mary_1835_dress_study', 0], ['private_first_infantry_1812', 3]]) {
  const worn = await figure(asset, lod);
  for (const key of ['t3572_a', 't3572_b']) V.applyVariation(SK.clone(worn), kit, V.personVariation({ kit, key, assetId: asset }));
  const p = V.personVariation({ kit, key: 't3572_c', assetId: asset });
  const again = SK.clone(worn), fresh = await figure(asset, lod);
  V.applyVariation(again, kit, p); V.applyVariation(fresh, kit, p);
  const geoms = (scene) => { const g = []; scene.traverse((o) => { if (o.isSkinnedMesh) g.push(o.geometry); }); return g; };
  const ga = geoms(again), gb = geoms(fresh);
  assert.equal(ga.length, gb.length);
  ga.forEach((g, i) => { for (const att of ['position', 'normal']) assert.deepEqual(g.attributes[att].array, gb[i].attributes[att].array, `${asset} lod${lod}: ${att} of mesh ${i} as a first fit gives`); });
  assert.equal(again.scale.x, fresh.scale.x);
}
// ...and nearestBounded is nearest, ties included, on a lattice with doubled points.
{ const rand = V.seededRandom('t3572'), lattice = () => Math.round((rand() - 0.5) * 60) * 0.004;
  const pts = new Float32Array(3000 * 3);
  for (let i = 0; i < pts.length; i++) pts[i] = lattice();
  for (let i = 0; i < 300; i++) pts.copyWithin((2700 + i) * 3, i * 3, i * 3 + 3);   // seam twins
  const grid = V.pointGrid(pts, 3, 0.03), q = new Float32Array(2000 * 3);
  for (let i = 0; i < q.length; i++) q[i] = lattice() * (i % 7 ? 1 : 4);
  const bound2 = new Float64Array(2000);
  for (let k = 0; k < 2000; k++) {
    const j = Math.floor(rand() * 3000); let b = 0;
    for (let c = 0; c < 3; c++) b += (pts[j * 3 + c] - q[k * 3 + c]) ** 2;
    bound2[k] = k % 11 ? b : Infinity;
  }
  assert.deepEqual(V.nearestBounded(grid, q, bound2), V.nearest(grid, q), 'the bounded search finds what the full one finds'); }

// Not an hm08 body (the CI fixture): left as drawn.
{ const scene = await figure('c4d_fixture', 0);
  assert.equal(V.applyVariation(scene, kit, V.personVariation({ kit, key: 'x' })), null); }

console.log(`ok human variation: ${kit.axes.length} axes, no two of 400 alike, seated face only, clothes outside the skin, LODs agree; ${faceCensus}`);

// T-3550: juvenile proportions stay on the approved bodies; only their face and
// reconstructed stature vary, and the adult aging model cannot be applied to them.
for (const assetId of ['child_boy_1904', 'child_girl_1904', 'child_toddler_1904', 'teen_boy_1904', 'teen_girl_1904']) {
  assert.equal(header.assets[assetId].body_draw_scale, 0);
  for (const key of ['young_1', 'young_2', 'young_3']) {
    const p = V.personVariation({ kit, key, assetId });
    for (const a of kit.axes) if (a.drive === 'age' || (a.scope === 'full' && a.id !== 'head_shape')) assert.equal(p.values[a.id], 0, `${assetId}: ${a.id} leaves the approved proportions intact`);
    assert(faceAxes.some(a => Math.abs(p.values[a.id]) > .001), 'individual faces still vary');
  }
}
