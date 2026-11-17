// SPDX-License-Identifier: GPL-3.0-or-later
// The 1812 private wears the regulars' coat, not the coatee (renderers/web/js/human-regulars.js,
// T-3553; Kevin, 2026-11-17: "i think against the regulars? they are probably closer to a
// regular and would have been outfitted with uniform?"). On the real exports, on the CPU, at
// every level, after the passes humans.js runs before it (dressCollars, easeSeats, fitCoats,
// fitSleeves): the tails' hem sits HEM_ABOVE_KNEE_M above the knee joint, not at mid-thigh
// (moved straight down only, below the pivot, so the vent fitCoats lapped stays lapped, and
// the tails stay over the overalls standing and walking with human-skirt.js); every breast
// button has a tape loop on the coat beside it toward the wearer's left, within 2.5 mm of
// the cloth, under the crossbelts where they cross it, and still on the cloth
// when the figure walks; topology, UVs and skin weights of everything else are kept, the
// crossbelts' own vertices untouched; it runs once per parse; a scene dated 1813 or later
// (the 1835 garrison wears this asset recoloured) and every other body are left as drawn.
//   node tools/test_human_regulars.mjs          the tree (must PASS)
//   REGULARS_OLD=1 node tools/test_human_regulars.mjs   the exports as drawn (must FAIL)
//   HUMANS_JS=<path> ...                         read the wiring from another humans.js
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
const SkeletonUtils = await import(utils.SkeletonUtils);
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
// Each module with its own relative imports resolved to the tree.
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8'))
  .replace(/from '\.\/([^']+)'/g, (_, f) => `from '${new URL(`renderers/web/js/${f}`, here).href}'`).replace("from 'three'", `from '${three}'`);
const mod = async (name) => import(data(await js(name)));
const { dressCollars } = await mod('human-collar.js');
const { easeSeats } = await mod('human-seat.js');
const { fitCoats } = await mod('human-coat.js');
const { fitSleeves } = await mod('human-sleeve.js');
const { createHumanSkirt } = await mod('human-skirt.js');
const R = await mod('human-regulars.js');
const OLD = process.env.REGULARS_OLD === '1';
const fitRegulars = OLD ? () => null : R.fitRegulars;
const ASSET = 'private_first_infantry_1812';

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
async function load(asset, lod) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  gltf.scene.updateMatrixWorld(true);
  return gltf;
}
/** What humans.js parse() runs before this pass. */
function before(scene) { dressCollars(scene); easeSeats(scene); fitCoats(scene); fitSleeves(scene); }
const meshesOf = (scene) => { const out = []; scene.traverse((o) => o.isSkinnedMesh && out.push(o)); return out; };
const pieceOf = (scene, piece) => meshesOf(scene).find((m) => m.name === `${ASSET}_${piece}_lod${m.name.slice(-1)}`);
function bindPos(mesh) {
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function posed(mesh) {
  mesh.skeleton.update();
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
const joint = (mesh, name) => new THREE.Vector3().setFromMatrixPosition(mesh.skeleton.boneInverses[mesh.skeleton.bones.findIndex((b) => b.name === name)].clone().invert());
const attrs = (m) => Object.fromEntries(Object.entries(m.geometry.attributes).map(([k, a]) => [k, Array.from({ length: a.count * a.itemSize }, (_, i) => a[['getX', 'getY', 'getZ', 'getW'][i % a.itemSize]](Math.floor(i / a.itemSize)))]));

/** Every hit of a horizontal ray toward the axis (0, y, cz) from angle `a` (0 ahead, + toward +x): distances from far outside. */
function hits(P, idx, cz, a, y) {
  const dir = new THREE.Vector3(-Math.sin(a), 0, -Math.cos(a)), o = new THREE.Vector3(0, y, cz).addScaledVector(dir, -1), out = [];
  const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), p = new THREE.Vector3(), t = new THREE.Vector3(), q = new THREE.Vector3();
  for (let k = 0; k < idx.length; k += 3) {
    A.fromArray(P, idx[k] * 3); B.fromArray(P, idx[k + 1] * 3); C.fromArray(P, idx[k + 2] * 3);
    if (Math.min(A.y, B.y, C.y) > y || Math.max(A.y, B.y, C.y) < y) continue;
    e1.subVectors(B, A); e2.subVectors(C, A); p.crossVectors(dir, e2); const det = e1.dot(p); if (Math.abs(det) < 1e-12) continue;
    t.subVectors(o, A); const u = t.dot(p) / det; if (u < 0 || u > 1) continue; q.crossVectors(t, e1); const v = dir.dot(q) / det; if (v < 0 || u + v > 1) continue;
    const d = e2.dot(q) / det; if (d > 0) out.push(d);
  }
  return out.sort((x, y) => x - y);
}

const failures = [], lines = [];
const check = (ok, msg) => { if (!ok) failures.push(msg); };
let tapeCount = 0;
for (const lod of [0, 1, 2, 3]) {
  const drawn = await load(ASSET, lod); before(drawn.scene);
  const gltf = await load(ASSET, lod); before(gltf.scene);
  const snap = new Map(meshesOf(gltf.scene).map((m) => [m.name, { a: attrs(m), idx: Array.from(m.geometry.index.array) }]));
  const report = fitRegulars(gltf.scene, { sceneId: '1812' });
  const tails = pieceOf(gltf.scene, 'coat_tails'), coat = pieceOf(gltf.scene, 'coat_body'), belts = pieceOf(gltf.scene, 'crossbelts');
  const buttons = pieceOf(gltf.scene, 'coat_buttons'), overalls = pieceOf(gltf.scene, 'linen_overalls');
  const sole = Math.min(...bindPos(pieceOf(gltf.scene, 'closed_shoes')).filter((_, i) => i % 3 === 1));
  const knee = (joint(tails, 'calf_l').y + joint(tails, 'calf_r').y) / 2 - sole, hip = (joint(tails, 'thigh_l').y + joint(tails, 'thigh_r').y) / 2;

  // Everything but the tails' positions and the crossbelts' added loops is as it was.
  for (const m of meshesOf(gltf.scene)) {
    const s = snap.get(m.name), a = attrs(m), n0 = s.a.position.length / 3;
    for (const k of Object.keys(s.a)) {
      if (m === tails && (k === 'position' || k === 'normal')) continue;
      const kept = m === belts ? a[k].slice(0, s.a[k].length) : a[k];
      assert.deepEqual(kept, s.a[k], `LOD${lod} ${m.name}: ${k} kept`);
    }
    const idx = Array.from(m.geometry.index.array);
    assert.deepEqual(m === belts ? idx.slice(0, s.idx.length) : idx, s.idx, `LOD${lod} ${m.name}: topology kept`);
    if (m !== belts) assert.equal(a.position.length / 3, n0, `LOD${lod} ${m.name}: no vertex added`);
  }
  // The tails: moved straight down only, below the pivot, so the vent's lap and the cut stay.
  const T0 = bindPos(pieceOf(drawn.scene, 'coat_tails')), T1 = bindPos(tails);
  for (let i = 0; i < T0.length / 3; i++) {
    assert(Math.abs(T1[i * 3] - T0[i * 3]) < 1e-6 && Math.abs(T1[i * 3 + 2] - T0[i * 3 + 2]) < 1e-6, `LOD${lod} tails: a vertex moved other than down`);
    assert(T1[i * 3 + 1] <= T0[i * 3 + 1] + 1e-6, `LOD${lod} tails: a vertex moved up`);
    if (T0[i * 3 + 1] >= hip - R.PIVOT_BELOW_HIP_M) assert(Math.abs(T1[i * 3 + 1] - T0[i * 3 + 1]) < 1e-6, `LOD${lod} tails: moved above the pivot`);
  }
  const hem0 = Math.min(...T0.filter((_, i) => i % 3 === 1)) - sole, hem1 = Math.min(...T1.filter((_, i) => i % 3 === 1)) - sole;
  check(hem1 <= knee + R.HEM_ABOVE_KNEE_M + 0.005 && hem1 >= knee, `LOD${lod} tails: hem ${hem1.toFixed(3)} m off the ground (the knee joint at ${knee.toFixed(3)}; the coatee's mid-thigh is ${hem0.toFixed(3)})`);
  // Over the overalls at rest: every tails vertex behind the overalls at its height and side.
  const O = bindPos(overalls); let close = Infinity;
  for (let i = 0; i < T1.length / 3; i++) {
    const x = T1[i * 3], y = T1[i * 3 + 1], z = T1[i * 3 + 2];
    for (let j = 0; j < O.length / 3; j++) if (Math.abs(O[j * 3 + 1] - y) < 0.012 && Math.abs(O[j * 3] - x) < 0.012) close = Math.min(close, O[j * 3 + 2] - z);
  }
  check(close > 0.004, `LOD${lod} tails: within ${(close * 1000).toFixed(1)} mm of the overalls at rest`);

  // The tape: one loop a button, on the cloth, under the belts.
  const C = bindPos(coat), Ci = coat.geometry.index.array, B = bindPos(belts), Bi = belts.geometry.index.array;
  const cz = (joint(coat, 'spine_02').z + joint(coat, 'spine_03').z) / 2;
  const Bp = bindPos(buttons), ys = [];
  for (const y of Array.from({ length: Bp.length / 3 }, (_, i) => Bp[i * 3 + 1]).sort((a, b) => a - b)) if (!ys.length || y - ys.at(-1).top > 0.012) ys.push({ sum: y, n: 1, top: y }); else { const g = ys.at(-1); g.sum += y; g.n++; g.top = y; }
  let loops = 0, under = 0, belt = Infinity;
  for (const g of ys) {
    const y = g.sum / g.n; let on = 0, n = 0;
    for (const f of [0.25, 0.45, 0.65, 0.85]) {
      const a = f * 0.075 / 0.17;
      const c = hits(C, Ci, cz, a, y)[0]; if (c === undefined) continue; n++;
      const off = hits(B, Bi, cz, a, y).map((d) => c - d).filter((d) => d > -0.0005);
      const tape = off.find((d) => d >= 0.0003 && d <= 0.0025);
      if (tape !== undefined) { on++; const over = off.filter((d) => d > tape + 1e-4); if (over.length) { under++; belt = Math.min(belt, Math.min(...over) - tape); } }
    }
    if (n && on >= n - 1) loops++;
  }
  // The belt and the tape are the one white material, so a near tie would not show; it may never cross.
  check(belt >= 0.0005, `LOD${lod}: a crossbelt lies ${(belt * 1000).toFixed(2)} mm over the tape (at least 0.5 mm)`);
  check(loops === ys.length, `LOD${lod}: ${loops} of ${ys.length} breast button holes have a tape loop on the cloth beside them`);
  tapeCount += loops;

  // Walking (and standing first) with the hanging cloth driven as the town drives it: the tape
  // stays on the coat, and no leg comes out behind the lengthened tails.
  const n0 = snap.get(belts.name).a.position.length / 3, nb = B.length / 3, near = [];
  // Each loop vertex's nearest point on the coat's surface (a triangle and where on it), and how far.
  { const tri = new THREE.Triangle(), p = new THREE.Vector3(), cp = new THREE.Vector3(), bc = new THREE.Vector3();
    for (let i = n0; i < nb; i++) {
      p.fromArray(B, i * 3); let best = null, bd = Infinity;
      for (let k = 0; k < Ci.length; k += 3) {
        tri.a.fromArray(C, Ci[k] * 3); tri.b.fromArray(C, Ci[k + 1] * 3); tri.c.fromArray(C, Ci[k + 2] * 3);
        tri.closestPointToPoint(p, cp); const d = cp.distanceTo(p);
        if (d < bd) { bd = d; tri.getBarycoord(cp, bc); best = [Ci[k], Ci[k + 1], Ci[k + 2], bc.x, bc.y, bc.z]; }
      }
      near.push([i, best, bd]);
    } }
  const scene = SkeletonUtils.clone(gltf.scene), root = new THREE.Group(); root.add(scene); root.updateMatrixWorld(true);
  const mixer = new THREE.AnimationMixer(scene); mixer.clipAction(gltf.animations.find((a) => a.name === 'walk')).play(); mixer.update(0);
  const sk = createHumanSkirt({ id: 'regulars-test', scene });
  const ms = meshesOf(scene), pt = ms.find((m) => m.name === tails.name), pc = ms.find((m) => m.name === coat.name), pb = ms.find((m) => m.name === belts.name), legs = ms.filter((m) => /linen_overalls|body_0/.test(m.name));
  let drift = 0, poke = 0, pokeAt = '';
  for (let f = 0; f < 66; f++) {
    const standing = f < 12;
    if (!standing) mixer.update(1 / 30);
    sk?.apply(1 / 30, { state: standing ? 'standing' : 'walking', root }); root.updateMatrixWorld(true);
    if (f % 6 !== 5) continue;
    const PB = posed(pb), PC = posed(pc);
    for (const [i, [a, b, c, u, v2, w2], d0] of near) {
      const x = PC[a * 3] * u + PC[b * 3] * v2 + PC[c * 3] * w2, y = PC[a * 3 + 1] * u + PC[b * 3 + 1] * v2 + PC[c * 3 + 1] * w2, z = PC[a * 3 + 2] * u + PC[b * 3 + 2] * v2 + PC[c * 3 + 2] * w2;
      drift = Math.max(drift, Math.abs(Math.hypot(PB[i * 3] - x, PB[i * 3 + 1] - y, PB[i * 3 + 2] - z) - d0));
    }
    // The pelvis frame; the tails' sheet as a map over (left, up), its front-most depth per 1 cm cell.
    const w = (nm) => scene.getObjectByName(nm).getWorldPosition(new THREE.Vector3());
    const Og = w('thigh_l').add(w('thigh_r')).multiplyScalar(0.5), U = Og.clone().sub(w('foot_l').add(w('foot_r')).multiplyScalar(0.5)).normalize();
    const L = w('thigh_l').sub(w('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize(); const F = new THREE.Vector3().crossVectors(L, U).normalize();
    const cell = 0.01, map = new Map(), v = new THREE.Vector3(), key = (l, u) => `${Math.floor(l / cell)},${Math.floor(u / cell)}`;
    const PT = posed(pt), idx = pt.geometry.index.array;
    // Sample the sheet's triangles densely enough for 1 cm cells.
    for (let k = 0; k < idx.length; k += 3) for (let s = 0; s <= 6; s++) for (let r = 0; r <= 6 - s; r++) {
      const a = idx[k], b = idx[k + 1], c = idx[k + 2], wa = 1 - (s + r) / 6, wb = s / 6, wc = r / 6;
      v.set(PT[a * 3] * wa + PT[b * 3] * wb + PT[c * 3] * wc, PT[a * 3 + 1] * wa + PT[b * 3 + 1] * wb + PT[c * 3 + 1] * wc, PT[a * 3 + 2] * wa + PT[b * 3 + 2] * wb + PT[c * 3 + 2] * wc).sub(Og);
      const l = v.dot(L), u = v.dot(U), d = v.dot(F); if (u > -0.05) continue; // below the seat
      const kk = key(l, u); map.set(kk, Math.max(map.get(kk) ?? -Infinity, d));
    }
    const inner = (kk) => { const [l, u] = kk.split(',').map(Number); for (let dl = -1; dl <= 1; dl++) for (let du = -1; du <= 1; du++) if (!map.has(`${l + dl},${u + du}`)) return false; return true; };
    for (const m of legs) {
      const P = posed(m);
      for (let i = 0; i < P.length / 3; i++) {
        v.set(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]).sub(Og);
        const kk = key(v.dot(L), v.dot(U)); if (!map.has(kk) || !inner(kk)) continue;
        const depth = map.get(kk) - v.dot(F); // > 0: the leg is further back than the cloth
        if (depth > poke) { poke = depth; pokeAt = `${standing ? 'standing' : `walking ${(f / 30).toFixed(1)} s`} ${m.name.replace(`${ASSET}_`, '')}`; }
      }
    }
  }
  // The far levels' coarser coat bends between its corners; a few millimetres there is under a pixel.
  if (!OLD) check(drift <= (lod <= 1 ? 0.003 : 0.006), `LOD${lod}: the tape drifts ${(drift * 1000).toFixed(1)} mm off the coat walking`);
  check(poke <= (lod <= 1 ? 0.006 : 0.012), `LOD${lod}: a leg comes ${(poke * 1000).toFixed(1)} mm out behind the tails (${pokeAt})`);
  lines.push(`LOD${lod}: hem ${hem0.toFixed(3)} → ${hem1.toFixed(3)} m (knee ${knee.toFixed(3)}), over the overalls by ${(close * 1000).toFixed(0)} mm at rest, legs out behind ${(poke * 1000).toFixed(1)} mm walking; tape ${loops}/${ys.length} loops (${under} samples under a belt, ${(belt * 1000).toFixed(1)} mm under it at least), drift ${(drift * 1000).toFixed(1)} mm`);

  if (!OLD) {
    // Once per parse.
    const held = meshesOf(gltf.scene).map((m) => [m.geometry.attributes.position.count, m.geometry.attributes.position.array.slice()]);
    assert.equal(R.fitRegulars(gltf.scene, { sceneId: '1812' }), null, `LOD${lod}: a second call does nothing`);
    meshesOf(gltf.scene).forEach((m, k) => { assert.equal(m.geometry.attributes.position.count, held[k][0]); assert.deepEqual(m.geometry.attributes.position.array, held[k][1], `LOD${lod} ${m.name}: a second call moved it`); });
    assert(report && report.loops === ys.length && report.tails > 0.1, `LOD${lod}: report ${JSON.stringify(report)}`);
    // The 1835 garrison keeps the coatee; a store with no scene dresses the 1812 private.
    for (const [sceneId, applies] of [['1835', false], ['1904', false], ['1812', true], [null, true]]) {
      const g = await load(ASSET, lod); before(g.scene);
      const counts = meshesOf(g.scene).map((m) => m.geometry.attributes.position.count);
      const r = R.fitRegulars(g.scene, { sceneId });
      assert.equal(!!r, applies, `LOD${lod} scene ${sceneId}: ${applies ? 'dressed' : 'left as drawn'}`);
      if (!applies) assert.deepEqual(meshesOf(g.scene).map((m) => m.geometry.attributes.position.count), counts);
    }
  }
}
// No other body is touched.
if (!OLD) {
  const others = (await fs.readdir(new URL('assets/humans/web/', here))).filter((f) => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture') && !f.startsWith(`${ASSET}.`)).map((f) => f.replace('.lod0.glb', ''));
  for (const a of others) {
    const g = await load(a, 0);
    const held = meshesOf(g.scene).map((m) => m.geometry.attributes.position.array.slice());
    assert.equal(R.fitRegulars(g.scene, { sceneId: '1812' }), null, `${a}: not a regular`);
    meshesOf(g.scene).forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, held[k], `${a} ${m.name}: touched`));
  }
  lines.push(`${others.length} other bodies left as drawn`);
}
for (const l of lines) console.log(l);
if (failures.length) {
  for (const f of failures) console.log(`FAIL ${f}`);
  assert.fail(`${failures.length} faults${OLD ? ' (the exports as drawn, REGULARS_OLD=1)' : ''}`);
}
assert.equal(tapeCount, 32, 'eight loops at each of four levels');
// Wired into humans.js's parse with the store's scene: after the sleeves, before the waist.
{
  const humans = await fs.readFile(process.env.HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fitRegulars \} from '\.\/human-regulars\.js';/.test(humans), 'humans.js imports fitRegulars');
  assert(/fitSleeves\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,200}fitRegulars\(gltf\.scene, \{ sceneId \}\);(?:(?!return gltf)[\s\S]){0,200}fitWaist\(gltf\.scene\);/.test(humans), 'parse() dresses the regulars after the sleeves and before the waist, with the scene (another pass may stand between)');
}
console.log('human-regulars: the private\'s tails to above the knee and tape on his breast button holes, at every level, standing and walking; the 1835 garrison and every other body as drawn: PASS');
