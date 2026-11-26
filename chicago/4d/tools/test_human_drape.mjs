// SPDX-License-Identifier: GPL-3.0-or-later
// Clothes hung, faired and trimmed as cloth at load (renderers/web/js/human-drape.js,
// human-fair.js, human-trim.js; T-3553 round 5, the owner 2026-11-26: "the men are very bad ...
// ragged at points and peek through when they move and hugs their bodies unnaturally"; on four
// close-ups: the coachman's collar and close coat, the maid's jagged collar, John Glessner's
// lapels, missing seams and buttons and the lump at his shoulder, Frances Glessner's collar over
// her chin). On the real exports, on the CPU, run in humans.js's order.
//
// For the bodies in BODIES at the levels given, against the same body dressed without round 5
// (the fittings only, as before it):
//  - what is under shows through no more: at bind and in two strides, the points of the skin
//    and each inner layer with an outer layer's cloth inside them (between them and the body)
//    within 25 mm, summed, at most POKE_KEEP of before plus POKE_SLACK;
//  - every drawn vertex's skin row sums to one (whole 1/255 steps) on bones of its skeleton, and
//    no position or normal is lost (NaN);
//  - each step of the passes is short (STEP_MS at most, here; humans.js runs them a slice at a
//    time on the main thread);
// and on the four close-ups:
//  - John J. Glessner (every level): his lapels are cut again on his coat (within LAPEL_ON_M of
//    its cloth), none of them over the top of the shoulder; three front buttons and the back
//    collar at the two near levels, seams at the nearest;
//  - Frances M. Glessner: her collar's top under her chin in front, by half CHIN.clear at least;
//  - Charles Nelson, coachman: his coat's skirt as cut (the fairing opened its fronts once):
//    at least SKIRT_KEEP of its points unmoved by the fairing;
//  - Mary Reynolds, maid: her collar cut again as a band; her apron's shoulder frills gathered
//    again (T-3553 round 6, the owner 2026-11-26 "keep going on the rest");
//  - Charles Nelson: a shirt front in his coat's V, his collar's front corners no farther
//    forward than its front line (LIVERY.burr and 3 mm);
//  - John J. Glessner: both armholes seamed at the nearest level; his waistcoat closed at the far
//    levels (the skin showed through it under the lapels cut again).
// and an 1812 working woman's short gown's skirt left under her apron by the fairing (APRON_KEEP
// of the points under it before).
// T-3553 round 7 (the owner 2026-11-26: "sweep all of the people and clothing and remove these
// ragged collars and edges and holes in clothing", "Armpit is bad"; human-layover.js,
// human-pits.js): every body level's garment outlines evened; the coachman's armpits tucked in,
// the skin with them, and no more sharp folds there in his walk; John Glessner's waistcoat,
// shirt and tie bound to his coat at the farthest level, and his waistcoat's band under the
// coat left out at the far levels; braces under a waistcoat, belts over a coat.
// Wired into humans.js's parse, after the fittings.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => { const name = Object.keys(utils).find((k) => spec.endsWith(`/${k}.js`)); return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`; });
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
// Modules from data: URLs, their own relative imports rewritten the same way.
const modCache = new Map();
async function modURL(file) {
  if (modCache.has(String(file))) return modCache.get(String(file));
  let src = (await fs.readFile(file, 'utf8')).replace(/from 'three'/g, `from '${three}'`);
  for (const d of new Set([...src.matchAll(/from '\.\/([\w.-]+\.js)'/g)].map((m) => m[1]))) src = src.split(`from './${d}'`).join(`from '${await modURL(new URL(`renderers/web/js/${d}`, here))}'`);
  const u = data(src); modCache.set(String(file), u); return u;
}
const js = async (name) => import(await modURL(new URL(`renderers/web/js/${name}`, here)));
const D = await js('human-drape.js'), F = await js('human-fair.js'), T = await js('human-trim.js'), L = await js('human-layover.js'), PT = await js('human-pits.js');
const FITS = [];
for (const [file, fn] of [['human-collar.js', 'dressCollars'], ['human-seat.js', 'easeSeats'], ['human-coat.js', 'fitCoats'], ['human-sleeve.js', 'fitSleeves'], ['human-tailor-1835.js', 'tailor1835'], ['human-regulars.js', 'fitRegulars'], ['human-frockcoat.js', 'fitFrockCoat'], ['human-gown.js', 'fitGown'], ['human-waist.js', 'fitWaist'], ['human-silver.js', 'engraveSilver']]) FITS.push((await js(file))[fn]);

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
const clipsOf = new WeakMap();
async function load(asset, lod) {
  const bytes = geometryOnly(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here)));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes, '');
  gltf.scene.updateMatrixWorld(true);
  clipsOf.set(gltf.scene, gltf.animations ?? []);
  return gltf.scene;
}
const sceneOf = (asset) => (/_1812/.test(asset) ? '1812' : /_1835/.test(asset) ? '1835' : '1904');
/** Dress as humans.js does; `round5` false: the fittings only. Returns the longest step (ms). */
function dress(scene, asset, round5) {
  let longest = 0;
  const run = (gen) => { for (;;) { const t = performance.now(), n = gen.next(), d = performance.now() - t; if (d > longest) longest = d; if (n.done) return n.value; } };
  if (round5) run(D.drapeGarmentsSteps(scene));
  for (const fit of FITS) fit(scene, { sceneId: sceneOf(asset) });
  if (round5) {
    run(F.fairOuterSteps(scene));
    run(T.refineTrimsSteps(scene));
    run(D.settleOnBodySteps(scene)); run(L.layOverSteps(scene)); run(PT.tuckPitsSteps(scene, clipsOf.get(scene), THREE));
    run(D.bindLayersSteps(scene)); run(D.cullHiddenSteps(scene));
  }
  return longest;
}

export const BODIES = [
  ['glessner_john_j_1904', [0, 1, 2, 3]], ['glessner_frances_m_1904', [0, 2]], ['nelson_charles_1904_coachman', [0, 2]], ['reynolds_mary_1904_maid', [0, 2]],
  ['anonymous_working_driver_1904', [0]], ['bardwell_otis_1835', [0]],
];
export const POKE_KEEP = 1.0, POKE_SLACK = 40, STEP_MS = Number(process.env.DRAPE_STEP_MS ?? 300), LAPEL_ON_M = 0.012, SKIRT_KEEP = 0.9, APRON_KEEP = 0.95;

const meshesOf = (scene) => { const out = []; scene.traverse((o) => { if (o.isSkinnedMesh && o.geometry.index) out.push(o); }); return out; };
const short = (m, asset) => m.name.replace(`${asset}_`, '').replace(/_lod\d+$/, '');
function bindPos(mesh) {
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function posed(mesh) {
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { mesh.getVertexPosition(i, v); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function joints(mesh) {
  const out = {}, M = new THREE.Matrix4(), v = new THREE.Vector3();
  mesh.skeleton.bones.forEach((b, i) => { M.copy(mesh.skeleton.boneInverses[i]).invert(); out[b.name] = v.setFromMatrixPosition(M).toArray(); });
  return out;
}
// ---- the test's own geometry (nothing shared with the modules) ----
const CELL = 0.03;
function rayGrid(P, idx) {
  const H = new Map(), key = (x, y, z) => `${x},${y},${z}`;
  for (let t = 0; t < idx.length; t += 3) {
    const lo = [0, 1, 2].map((d) => Math.floor(Math.min(P[idx[t] * 3 + d], P[idx[t + 1] * 3 + d], P[idx[t + 2] * 3 + d]) / CELL)), hi = [0, 1, 2].map((d) => Math.floor(Math.max(P[idx[t] * 3 + d], P[idx[t + 1] * 3 + d], P[idx[t + 2] * 3 + d]) / CELL));
    for (let x = lo[0]; x <= hi[0]; x++) for (let y = lo[1]; y <= hi[1]; y++) for (let z = lo[2]; z <= hi[2]; z++) { const k = key(x, y, z); (H.get(k) ?? H.set(k, []).get(k)).push(t); }
  }
  return (o, d, far) => {
    const e = [0, 1, 2].map((k) => o[k] + d[k] * far), seen = new Set(); let best = Infinity;
    for (let x = Math.floor(Math.min(o[0], e[0]) / CELL); x <= Math.floor(Math.max(o[0], e[0]) / CELL); x++) for (let y = Math.floor(Math.min(o[1], e[1]) / CELL); y <= Math.floor(Math.max(o[1], e[1]) / CELL); y++) for (let z = Math.floor(Math.min(o[2], e[2]) / CELL); z <= Math.floor(Math.max(o[2], e[2]) / CELL); z++) {
      for (const t of H.get(key(x, y, z)) ?? []) {
        if (seen.has(t)) continue; seen.add(t);
        const a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3, e1 = [P[b] - P[a], P[b + 1] - P[a + 1], P[b + 2] - P[a + 2]], e2 = [P[c] - P[a], P[c + 1] - P[a + 1], P[c + 2] - P[a + 2]];
        const p = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]], det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2];
        if (Math.abs(det) < 1e-12) continue;
        const s = [o[0] - P[a], o[1] - P[a + 1], o[2] - P[a + 2]], u = (s[0] * p[0] + s[1] * p[1] + s[2] * p[2]) / det; if (u < 0 || u > 1) continue;
        const q = [s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0]], v = (d[0] * q[0] + d[1] * q[1] + d[2] * q[2]) / det; if (v < 0 || u + v > 1) continue;
        const h = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) / det; if (h > 1e-5 && h < far && h < best) best = h;
      }
    }
    return best;
  };
}
function vertexNormals(P, idx) {
  const n = P.length / 3, N = new Float64Array(n * 3), M = new Map();
  for (let t = 0; t < idx.length; t += 3) {
    const a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3, u = [P[b] - P[a], P[b + 1] - P[a + 1], P[b + 2] - P[a + 2]], v = [P[c] - P[a], P[c + 1] - P[a + 1], P[c + 2] - P[a + 2]];
    const f = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    for (const k of [a, b, c]) for (let d = 0; d < 3; d++) N[k + d] += f[d];
  }
  // Welded over the body's own seams.
  for (let i = 0; i < n; i++) { const k = `${Math.round(P[i * 3] * 1e4)},${Math.round(P[i * 3 + 1] * 1e4)},${Math.round(P[i * 3 + 2] * 1e4)}`; const s = M.get(k) ?? M.set(k, [0, 0, 0, []]).get(k); for (let d = 0; d < 3; d++) s[d] += N[i * 3 + d]; s[3].push(i); }
  for (const s of M.values()) { const l = Math.hypot(s[0], s[1], s[2]) || 1; for (const i of s[3]) for (let d = 0; d < 3; d++) N[i * 3 + d] = s[d] / l; }
  return N;
}
/** The rank of a piece by its material (skin 0, under 1, lower 2, waistcoat 3, coat-like 4). */
const rank = (m) => D.layerRank(m);
const STRIDES = [0, 1, -1];
function pose(bones, rest, s) {
  for (const [b, r] of rest) b.quaternion.copy(r);
  if (!s) return;
  const q = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...ax), deg * Math.PI / 180);
  const set = (n, ax, d) => bones[n]?.quaternion.multiply(q(ax, d));
  set('upperarm_l', [1, 0, 0], 25 * s); set('upperarm_r', [1, 0, 0], -25 * s); set('upperarm_l', [0, 0, 1], 12); set('upperarm_r', [0, 0, 1], -12);
  set('lowerarm_l', [1, 0, 0], 20); set('lowerarm_r', [1, 0, 0], 20);
  set('thigh_l', [1, 0, 0], 28 * s); set('thigh_r', [1, 0, 0], -28 * s); set('calf_l', [1, 0, 0], -25); set('calf_r', [1, 0, 0], -10);
  set('spine_02', [0, 1, 0], 8 * s); set('spine_03', [0, 1, 0], 6 * s);
}
/** Points of the skin and every inner layer with an outer layer's cloth inside them within 25 mm. */
function pokes(scene) {
  const all = meshesOf(scene), body = all.find((m) => m.material?.name === 'skin'), worn = all.filter((m) => /^(garment|accessory|footwear)/.test(m.material?.name ?? '') && m.geometry.index.count);
  const bones = Object.fromEntries(body.skeleton.bones.map((b) => [b.name, b])), rest = new Map(body.skeleton.bones.map((b) => [b, b.quaternion.clone()]));
  let total = 0;
  for (const s of STRIDES) {
    pose(bones, rest, s); scene.updateMatrixWorld(true); for (const m of [body, ...worn]) m.skeleton.update();
    const BP = posed(body), BN = vertexNormals(BP, body.geometry.index.array), near = new Map();
    for (let i = 0; i < BP.length / 3; i++) { const k = `${Math.floor(BP[i * 3] / CELL)},${Math.floor(BP[i * 3 + 1] / CELL)},${Math.floor(BP[i * 3 + 2] / CELL)}`; (near.get(k) ?? near.set(k, []).get(k)).push(i); }
    const nearest = (x, y, z) => { let best = Infinity, bi = -1; const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL), cz = Math.floor(z / CELL); for (let r = 1; r <= 3 && bi < 0; r++) for (let a = -r; a <= r; a++) for (let b = -r; b <= r; b++) for (let c = -r; c <= r; c++) for (const i of near.get(`${cx + a},${cy + b},${cz + c}`) ?? []) { const d = (BP[i * 3] - x) ** 2 + (BP[i * 3 + 1] - y) ** 2 + (BP[i * 3 + 2] - z) ** 2; if (d < best) { best = d; bi = i; } } return bi; };
    const layers = [{ m: body, P: BP }, ...worn.map((m) => ({ m, P: posed(m) }))];
    for (const L of layers) { L.used = new Uint8Array(L.P.length / 3); for (const i of L.m.geometry.index.array) L.used[i] = 1; L.grid = rayGrid(L.P, L.m.geometry.index.array); }
    for (const inner of layers) for (const outer of layers.slice(1)) {
      if (outer === inner || rank(outer.m) <= rank(inner.m)) continue;
      for (let i = 0; i < inner.P.length / 3; i++) {
        if (!inner.used[i]) continue;
        const x = inner.P[i * 3], y = inner.P[i * 3 + 1], z = inner.P[i * 3 + 2], b = inner.m === body ? i : nearest(x, y, z); if (b < 0) continue;
        const n = [BN[b * 3], BN[b * 3 + 1], BN[b * 3 + 2]];
        if (Number.isFinite(outer.grid([x + n[0] * 0.0005, y + n[1] * 0.0005, z + n[2] * 0.0005], [-n[0], -n[1], -n[2]], 0.025))) total++;
      }
    }
  }
  pose(bones, rest, 0); scene.updateMatrixWorld(true);
  return total;
}

/** Sharp folds in the pit of each arm in the body's own walk: edges of the outer coat within
 * PIT_FOLD.reach of a shoulder joint whose two triangles close past PIT_FOLD.cos, over
 * PIT_FOLD.times points of the clip (T-3553 round 7: the coachman's torn notch). */
export const PIT_FOLD = { reach: 0.13, cos: -0.5, times: [0.1, 0.35, 0.6, 0.85] };
function pitFolds(scene, coatName) {
  const coat = meshesOf(scene).find((m) => coatName.test(m.name)), clip = (clipsOf.get(scene) ?? []).find((c) => /walk/i.test(c.name));
  if (!coat || !clip) return null;
  const mixer = new THREE.AnimationMixer(scene), idx = coat.geometry.index.array, W = D.kit.weldMeshes([coat]), gid = W.parts[0].group;
  const edges = new Map();
  for (let t = 0; t < idx.length; t += 3) for (let k = 0; k < 3; k++) { const a = gid[idx[t + k]], b = gid[idx[t + (k + 1) % 3]]; if (a === b) continue; const e = a < b ? a * W.G + b : b * W.G + a; (edges.get(e) ?? edges.set(e, []).get(e)).push(t); }
  const pairs = [...edges.values()].filter((l) => l.length === 2);
  mixer.clipAction(clip).play();
  let folds = 0;
  for (const f of PIT_FOLD.times) {
    mixer.setTime(f * clip.duration); scene.updateMatrixWorld(true); coat.skeleton.update();
    const P = posed(coat), J = ['upperarm_l', 'upperarm_r'].map((n) => new THREE.Vector3().setFromMatrixPosition(coat.skeleton.bones.find((b) => b.name === n).matrixWorld));
    const nrm = (t) => { const a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3, u = [P[b] - P[a], P[b + 1] - P[a + 1], P[b + 2] - P[a + 2]], v = [P[c] - P[a], P[c + 1] - P[a + 1], P[c + 2] - P[a + 2]], n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]], l = Math.hypot(...n) || 1; return n.map((x) => x / l); };
    for (const [t0, t1] of pairs) {
      const i = idx[t0], x = P[i * 3], y = P[i * 3 + 1], z = P[i * 3 + 2];
      if (!J.some((j) => Math.hypot(j.x - x, j.y - y, j.z - z) < PIT_FOLD.reach)) continue;
      const a = nrm(t0), b = nrm(t1);
      if (a[0] * b[0] + a[1] * b[1] + a[2] * b[2] < PIT_FOLD.cos) folds++;
    }
  }
  mixer.stopAllAction(); mixer.uncacheRoot(scene);
  for (const m of meshesOf(scene)) m.skeleton.pose();
  scene.updateMatrixWorld(true);
  return folds;
}

const lines = [];
let measured = 0;
for (const [asset, lods] of BODIES) for (const lod of lods) {
  const before = await load(asset, lod); dress(before, asset, false);
  const after = await load(asset, lod);
  const longest = dress(after, asset, true);
  const tag = `${asset} lod${lod}`, trim = after.userData.chicagoTrim ?? {};
  // Rows and positions whole.
  for (const m of meshesOf(after)) {
    const sw = m.geometry.attributes.skinWeight, si = m.geometry.attributes.skinIndex, pos = m.geometry.attributes.position, nrm = m.geometry.attributes.normal, nb = m.skeleton.bones.length;
    for (const i of m.geometry.index.array) {
      let sum = 0; for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); sum += w; assert(w === 0 || si.getComponent(i, k) < nb, `${tag} ${short(m, asset)}: bone in range`); }
      assert(Math.abs(sum - 1) < 2.5 / 255, `${tag} ${short(m, asset)}: vertex ${i} weights sum to ${sum}`);
      assert(Number.isFinite(pos.getX(i) + pos.getY(i) + pos.getZ(i)) && (!nrm || Number.isFinite(nrm.getX(i) + nrm.getY(i) + nrm.getZ(i))), `${tag} ${short(m, asset)}: vertex ${i} whole`);
    }
  }
  assert(longest <= STEP_MS, `${tag}: longest step ${longest.toFixed(0)} ms (at most ${STEP_MS})`);
  assert((after.userData.chicagoLayover?.evened ?? []).length > 0, `${tag}: garment outlines evened`);
  const p0 = pokes(before), p1 = pokes(after);
  assert(p1 <= p0 * POKE_KEEP + POKE_SLACK, `${tag}: shows through at ${p1} points in three poses (before: ${p0})`);
  let note = '';
  if (/glessner_john_j_1904/.test(asset)) {
    const body = meshesOf(after).find((m) => m.material?.name === 'skin'), J = joints(body), coat = meshesOf(after).find((m) => /frock_coat_body_lod\d+$/.test(m.name)), silk = meshesOf(after).find((m) => /four_in_hand_tie_lod\d+$/.test(m.name));
    const cut = (trim.lapels ?? []).find((r) => r.mesh === silk.name);
    assert(cut && cut.points > 0, `${tag}: lapels cut again`);
    // The new lapels: the silk's last points before the buttons (at the near levels) and seams; on the coat's cloth.
    const Pc = bindPos(coat), Ps = bindPos(silk), n = Ps.length / 3, buttons = (trim.buttoned ?? []).find((r) => r.mesh === silk.name)?.points ?? 0;
    const half = 0.25 * Math.abs(J.upperarm_l[0] - J.upperarm_r[0]), top = J.clavicle_l[1] + 0.01;
    let off = 0, over = 0;
    const onCoat = rayGrid(Pc, coat.geometry.index.array);
    const cols = T.LAPEL.across.length, rolled = T.LAPEL.across.filter(([v]) => v < 0.05).length;
    for (let i = n - buttons - cut.points; i < n - buttons; i++) {
      // From in front, straight in: the coat's cloth within LAPEL_ON_M of the lapel's point
      // (all but the rolled front edge, which turns over the coat's own edge).
      if ((i - (n - buttons - cut.points)) % cols < rolled) continue;
      const h = onCoat([Ps[i * 3], Ps[i * 3 + 1], Ps[i * 3 + 2] + 0.05], [0, 0, -1], 0.1);
      if (!(Math.abs(h - 0.05) <= LAPEL_ON_M)) off++;
      if (Math.abs(Ps[i * 3]) > half && Ps[i * 3 + 1] > top) over++;
    }
    assert(off <= cut.points * 0.02, `${tag}: ${off} of ${cut.points} lapel points off the coat`);
    assert(over === 0, `${tag}: ${over} lapel points over the shoulder`);
    if (lod <= 1) assert((trim.buttoned ?? []).some((r) => r.buttons === 3) && (trim.collared ?? []).length === 1, `${tag}: buttons and collar`);
    if (lod === 0) assert((trim.seamed ?? []).some((r) => r.seams >= 7), `${tag}: seams (five, and both armholes)`);
    if (lod >= T.FAR_WAISTCOAT.from) assert((trim.waistcoatClosed ?? []).length === 1, `${tag}: waistcoat closed under the lapels`);
    // T-3553 round 7: at the farthest level his waistcoat, shirt and tie move with the coat over
    // them; at the far levels the waistcoat under the coat keeps no band; nearer, as before.
    const bound = (after.userData.chicagoBind?.bound ?? []).map((r) => short({ name: r.mesh }, asset));
    const all3 = ['waistcoat_high_cut', 'four_in_hand_tie', 'shirt_standing_collar'].every((n) => bound.includes(n));
    assert(all3 === lod >= D.BIND_ALL_LOD, `${tag}: waistcoat, tie and shirt bound to the coat at the farthest level only (${bound})`);
    if (lod >= D.FAR_WAISTCOAT_LOD) {
      const cut = (after.userData.chicagoCull?.culled ?? []).find((r) => /waistcoat_high_cut/.test(r.mesh));
      assert(cut && cut.after < cut.before * 0.8, `${tag}: the waistcoat under the coat left out (${JSON.stringify(cut)})`);
    }
    note = `lapels ${cut.points} points, ${buttons ? 'buttons, ' : ''}${(trim.collared ?? []).length ? 'collar' : ''}${lod === 0 ? ', seams and armholes' : ''}${lod >= T.FAR_WAISTCOAT.from ? ', waistcoat closed' : ''}`;
  }
  if (/glessner_frances_m_1904/.test(asset)) {
    const body = meshesOf(after).find((m) => m.material?.name === 'skin'), J = joints(body), col = meshesOf(after).find((m) => /lady_shirtwaist_collar_lod\d+$/.test(m.name));
    const B = bindPos(body), si = body.geometry.attributes.skinIndex, sw = body.geometry.attributes.skinWeight, nk = J.neck_01, S = T.CHIN.sectors, low = new Array(S).fill(Infinity);
    const sec = (x, z) => Math.floor(((Math.atan2(x - nk[0], z - nk[2]) + Math.PI) / (2 * Math.PI)) * S) % S;
    for (let i = 0; i < B.length / 3; i++) { let best = 0, bw = -1; for (let k = 0; k < 4; k++) if (sw.getComponent(i, k) > bw) { bw = sw.getComponent(i, k); best = si.getComponent(i, k); } if (!/^(head|jaw)/.test(body.skeleton.bones[best]?.name ?? '') || Math.hypot(B[i * 3] - nk[0], B[i * 3 + 2] - nk[2]) > 0.11) continue; const k = sec(B[i * 3], B[i * 3 + 2]); low[k] = Math.min(low[k], B[i * 3 + 1]); }
    // In front (where the chin is): the collar's top under it.
    const Pc = bindPos(col); let worst = -Infinity;
    for (const i of col.geometry.index.array) { const k = sec(Pc[i * 3], Pc[i * 3 + 2]); if (Pc[i * 3 + 2] - nk[2] < 0.03 || !Number.isFinite(low[k])) continue; worst = Math.max(worst, Pc[i * 3 + 1] - (low[k] - T.CHIN.clear)); }
    // Half the clearance kept at least (the line here is the plain lowest skin per direction;
    // the module evens it round the neck, and the settling after may lift a point a little).
    const under = T.CHIN.clear - worst;
    assert(under >= T.CHIN.clear / 2, `${tag}: collar top ${(under * 1000).toFixed(1)} mm under the chin`);
    note = `collar top ${(under * 1000).toFixed(1)} mm under the chin`;
  }
  if (/reynolds_mary_1904_maid/.test(asset)) {
    assert((trim.rebuilt ?? []).some((r) => /collar/.test(r.mesh)), `${tag}: collar cut again`);
    const ruff = (trim.ruffled ?? [])[0];
    assert(ruff && ruff.points >= 2 * (T.RUFFLE.K[Math.min(lod, 3)] + 1) * (T.RUFFLE.rows[Math.min(lod, 3)] + 1), `${tag}: apron frills gathered again`);
    note = `collar cut again, frills gathered (${ruff.points} points)`;
  }
  if (/nelson_charles_1904_coachman/.test(asset)) {
    assert((trim.shirtFront ?? []).length === 1, `${tag}: shirt front in the coat's V`);
    // The collar's front no farther forward than the line of its front edge (the hooks gone).
    const coat = meshesOf(after).find((m) => T.LIVERY.coat.test(m.name)), W = D.kit.weldMeshes([coat]), loops = D.kit.loopsOf(W);
    const mean = (l) => l.reduce((a, g) => a + W.P[g * 3 + 1], 0) / l.length, top = loops.reduce((a, l) => (mean(l) > mean(a) ? l : a));
    const fz = top.filter((g) => Math.abs(W.P[g * 3]) < 0.07 && W.P[g * 3 + 2] > 0.04).map((g) => W.P[g * 3 + 2]).sort((a, b) => a - b);
    const stand = fz.at(-1) - fz[Math.floor(fz.length / 3)];
    assert(stand <= T.LIVERY.burr + 0.003, `${tag}: collar front stands ${(stand * 1000).toFixed(1)} mm forward`);
    const f0 = pitFolds(before, /livery_coat_body_lod\d+$/), f1 = pitFolds(after, /livery_coat_body_lod\d+$/);
    // T-3553 round 7: the cloth in the pit of each arm folded in under the arm, the skin with it.
    const pits = after.userData.chicagoPits?.tucked ?? [], coatPit = pits.find((r) => T.LIVERY.coat.test(r.mesh));
    assert(coatPit && coatPit.points >= (lod ? 30 : 100) && coatPit.max <= PT.PIT.tuck * 1.5, `${tag}: the coat's armpits tucked in (${JSON.stringify(coatPit)})`);
    assert(pits.some((r) => /body/.test(r.mesh)), `${tag}: the skin under the sleeves tucked in with the coat`);
    assert(f1 <= f0, `${tag}: ${f1} sharp folds at the armpits in the walk (before ${f0})`);
    note = `shirt front, collar front within ${(stand * 1000).toFixed(1)} mm of its line, pit folds ${f1} (before ${f0})`;
  }
  measured++;
  lines.push(`  ${tag.padEnd(40)} shows through ${String(p1).padStart(5)} (before ${String(p0).padStart(5)}), longest step ${longest.toFixed(0)} ms${note ? `, ${note}` : ''}`);
}
// The coachman's skirt, the fairing alone: points of a piece that is not the faired kind keep their cut.
{
  const sc = await load('nelson_charles_1904_coachman', 0);
  D.drapeGarments(sc); for (const fit of FITS) fit(sc, { sceneId: '1904' });
  const sk = meshesOf(sc).find((m) => /livery_coat_skirt_lod0$/.test(m.name)), P0 = bindPos(sk);
  F.fairOuter(sc);
  const P1 = bindPos(sk); let kept = 0; for (let i = 0; i < P1.length / 3; i++) if (Math.hypot(P1[i * 3] - P0[i * 3], P1[i * 3 + 1] - P0[i * 3 + 1], P1[i * 3 + 2] - P0[i * 3 + 2]) < 1e-6) kept++;
  assert(kept >= SKIRT_KEEP * (P1.length / 3), `coachman's skirt: ${kept} of ${P1.length / 3} points as cut`);
  lines.push(`  coachman's skirt: ${kept} of ${P1.length / 3} points as cut by the fairing`);
}
// An 1812 working woman's apron, the fairing alone: her short gown's skirt is not pushed out over
// it (the apron counted as cloth under the gown once, and the gown's skirt came out through it).
{
  const sc = await load('woman_working_1812', 0);
  D.drapeGarments(sc); for (const fit of FITS) fit(sc, { sceneId: '1812' });
  const ms = meshesOf(sc), sk = ms.find((m) => /short_gown_skirt_lod0$/.test(m.name)), ap = ms.find((m) => /_apron_lod0$/.test(m.name));
  // Skirt points the apron covers: a ray out from the point, level and away from the body's axis, meets the apron.
  const covered = () => {
    const A = bindPos(ap), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(Float32Array.from(A), 3)); g.setIndex(new THREE.BufferAttribute(ap.geometry.index.array, 1));
    const apron = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })), ray = new THREE.Raycaster(), P = bindPos(sk);
    let n = 0; for (let i = 0; i < P.length / 3; i++) { const o = new THREE.Vector3(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]), d = new THREE.Vector3(o.x, 0, o.z).normalize(); ray.set(o, d); ray.far = 0.08; if (ray.intersectObject(apron).length) n++; }
    return n;
  };
  const c0 = covered(); F.fairOuter(sc); const c1 = covered();
  assert(c0 > 50 && c1 >= APRON_KEEP * c0, `short gown's skirt under the apron: ${c1} of ${c0} points still under it after the fairing`);
  lines.push(`  short gown's skirt under the apron: ${c1} of ${c0} points still under it after the fairing`);
}
// The order pieces lie in (T-3553 round 7): braces over the shirt, under the waistcoat (lifted
// over it once, they came out through an 1835 waistcoat at the shoulder); belts over the coat.
{
  const piece = (name, cloth) => ({ name: `x_${name}_lod0`, material: { name: cloth } });
  const shirt = L.overRank(piece('shirt_full_sleeves', 'garment_upper__linen')), braces = L.overRank(piece('braces', 'garment_lower__leather'));
  const waistcoat = L.overRank(piece('waistcoat_open', 'garment_upper__wool')), coat = L.overRank(piece('frock_coat_body', 'garment_outer__wool'));
  const belt = L.overRank(piece('cross_belts', 'accessory__buff'));
  assert(shirt < braces && braces < waistcoat && waistcoat < coat && coat < belt, `ranks: shirt ${shirt} < braces ${braces} < waistcoat ${waistcoat} < coat ${coat} < crossbelts ${belt}`);
  lines.push(`  laid in order: shirt ${shirt} < braces ${braces} < waistcoat ${waistcoat} < coat ${coat} < crossbelts ${belt}`);
}
// Wired into humans.js's parse, after the fittings.
{
  const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fairOuterSteps \} from '\.\/human-fair\.js';/.test(humans) && /import \{ refineTrimsSteps \} from '\.\/human-trim\.js';/.test(humans), 'humans.js imports the passes');
  assert(/engraveSilver\(gltf\.scene\);\s*if \(!globalThis\.CHICAGO_NO_DRAPE\) \{\s*await sliced\(fairOuterSteps\(gltf\.scene\)\);\s*await sliced\(refineTrimsSteps\(gltf\.scene\)\);\s*await sliced\(settleOnBodySteps\(gltf\.scene\)\);\s*await sliced\(layOverSteps\(gltf\.scene\)\);\s*await sliced\(tuckPitsSteps\(gltf\.scene, gltf\.animations, THREE\)\);\s*await sliced\(bindLayersSteps\(gltf\.scene\)\);\s*await sliced\(cullHiddenSteps\(gltf\.scene\)\);\s*\}\s*return gltf;/.test(humans), 'parse() dresses the shared source after the fittings, a slice at a time');
}
for (const l of lines) console.log(l);
console.log(`human-drape: ${measured} body levels hung, faired and trimmed; nothing shows through more, rows whole, steps short; lapels, buttons, collar and seams on John Glessner's coat; Frances Glessner's collar under her chin: PASS`);
