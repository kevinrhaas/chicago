// SPDX-License-Identifier: GPL-3.0-or-later
// The 1835 merchant's strapped trousers and the labourer's white, gathered shirt sleeves
// (renderers/web/js/human-tailor-1835.js, T-3553; the people-match catalogue review of
// 2026-11-17, data/people_match/subjects/peck_philip_1835 and mahoney_patrick_1835). On the
// real exports, on the CPU, both bodies at every level, after the parse's other passes in
// humans.js's order (dressCollars, easeSeats, fitCoats, fitSleeves, then this, fitWaist,
// engraveSilver), against the same passes without it. It must:
//
//   Peck (peck_philip_1835):
//     - taper: each leg's section a little above the ankle at most TAPER_MAX of its width just
//       under the knee (the asset drew a straight tube, about 1.0);
//     - fullness: the front of the thighs under the waistcoat's hem stands out FULL_MIN_M more
//       (by level; round 4 raised it past round 3's 17 mm);
//     - pleats (LOD0, LOD1): folds on the front of each thigh, a relief of at least
//       PLEAT_RELIEF_M across it under the waistcoat's hem (the asset's cloth: its facets, 4 mm;
//       round 3's faint pleats, 8 mm);
//     - straps (every level): STRAP_W_MIN_M wide under the foot and STRAP_T_MIN_M thick, of the
//       trousers' cloth in their mesh (or the shoes' with STRAP_LEATHER), under each shoe,
//       showing below the hem on both sides of the foot,
//       through under the sole, on the foot bone below the hem; on the shoe at every pose of the
//       walk and idle; a garment on the leg to the skirt rig (never driven with the tails);
//     - nothing comes through: not the shin or the shoe through the drawn-in trousers, not the
//       strap's top through the hem, not the fuller cloth or the pleats through the waistcoat,
//       the tails or the coat, standing, at idle and through the walk;
//   Mahoney (mahoney_patrick_1835):
//     - the shirt is white linen (sRGB at least WHITE_MIN in every channel, red over blue, blue
//       at least WARM_MIN of red: not a blue-white); the picture it is drawn on is pinned; a
//       townsman's own shirt colour (human-looks.js dressCloth) still replaces it;
//     - a wristband on each wrist (every level): a band at least BAND_MIN_M long, of one width
//       along it (within BAND_SPREAD_M), over the sleeve's end, the sleeve inside it;
//     - gathers (LOD0, LOD1): above the band the sleeve blouses out (PUFF_MIN times the band)
//       and is drawn into it in folds (a relief of at least GATHER_RELIEF_M round the arm; the
//       asset's sleeve: its facets, under 2 mm);
//     - nothing comes through: the sleeve not through the gathers or the band, the wrist not
//       through the band, in the walk's and idle's arm poses;
//   both: every added piece is appended to its garment's own mesh, so each level draws as
//   many meshes as its export (T-3555: no draw call more per figure), and faces out (its
//   winding agrees with its normals); the drawn garments keep their vertices, triangles, UVs
//   and skin weights first, in order; nothing else on the body moves; any other
//   body is left alone; it runs once per loaded body; humans.js wires it into parse() after
//   fitSleeves and before fitWaist.
//
// TAILOR_BASELINE=1 runs every measure with the pass left out (the code before it): it fails.
// TAILOR_JS=<an earlier human-tailor-1835.js> runs it on that module (round 3's: it fails).
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const threeURL = new URL('three.module.js', vendor).href;
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${threeURL}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find((k) => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? threeURL : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = (name) => import(new URL(`renderers/web/js/${name}`, here));
const { dressCollars } = await js('human-collar.js');
const { easeSeats } = await js('human-seat.js');
const { fitCoats } = await js('human-coat.js');
const { fitSleeves } = await js('human-sleeve.js');
const { fitWaist } = await js('human-waist.js');
const { engraveSilver } = await js('human-silver.js');
const { garmentKind } = await js('human-skirt.js');
const { dressCloth } = await js('human-looks.js');
// TAILOR_JS=<path>: another version of the module (the code before a change).
const T = process.env.TAILOR_JS ? await import(new URL(`file://${process.env.TAILOR_JS}`).href) : await js('human-tailor-1835.js');
const BASELINE = process.env.TAILOR_BASELINE === '1';
const tailor = BASELINE ? () => [] : T.tailor1835;

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
const glb = (asset, lod) => fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
/** The parse as humans.js makes it, with (mine) or without this pass. */
async function prepared(asset, lod, mine) {
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(await glb(asset, lod)), '');
  const s = gltf.scene, exported = meshCount(s);
  dressCollars(s); easeSeats(s); fitCoats(s); fitSleeves(s);
  const report = mine ? tailor(s) : null;
  fitWaist(s); engraveSilver(s);
  s.updateMatrixWorld(true);
  return { gltf, scene: s, report, exported };
}
/** Meshes drawn (each a draw call per figure, T-3555). */
function meshCount(scene) { let n = 0; scene.traverse((o) => { if (o.isMesh) n++; }); return n; }
/** A view of part of a tailored garment: its drawn vertices and triangles ('drawn'), or one
 * piece the pass appended to it ('pleats', 'straps', 'wristbands', 'gathers'), as a skinned
 * mesh of its own on the garment's skeleton (not in the scene), or null. */
function partOf(host, key) {
  const rec = host?.userData.chicagoTailor1835;
  const g = host?.geometry, all = g?.attributes.position.count;
  const r = key === 'drawn' ? { start: 0, count: rec ? rec.drawn.vertices : all, indexStart: 0, indexCount: rec ? rec.drawn.indices : g.index.count } : rec?.parts[key];
  if (!r) return null;
  const geo = new THREE.BufferGeometry();
  for (const [k, a] of Object.entries(g.attributes)) {
    const out = new THREE.BufferAttribute(new a.array.constructor(r.count * a.itemSize), a.itemSize, a.normalized);
    for (let i = 0; i < r.count; i++) for (let c = 0; c < a.itemSize; c++) out.setComponent(i, c, a.getComponent(r.start + i, c));
    geo.setAttribute(k, out);
  }
  const idx = new Uint32Array(r.indexCount);
  for (let i = 0; i < r.indexCount; i++) idx[i] = g.index.getX(r.indexStart + i) - r.start;
  assert(idx.every((i) => i < r.count), `${host.name} ${key}: its triangles are its own`);
  geo.setIndex(new THREE.BufferAttribute(idx, 1));
  const m = new THREE.SkinnedMesh(geo, host.material);
  m.name = host.name.replace(/_lod(\d+)$/, `__${key}_lod$1`);
  m.bind(host.skeleton, host.bindMatrix);
  m.matrixWorld = host.matrixWorld;   // the garment's own place, as the scene poses it
  return m;
}
const meshOf = (scene, piece) => { let m = null; scene.traverse((o) => { if (o.isSkinnedMesh && new RegExp(`_${piece}_lod\\d+$`).test(o.name)) m = o; }); return m; };
const bonesOf = (scene) => { const b = {}; scene.traverse((o) => { if (o.isBone) b[o.name] = o; }); return b; };
const wpos = (o) => o.getWorldPosition(new THREE.Vector3());
/** Posed world points of a mesh. */
function posed(m) {
  const p = m.geometry.attributes.position, out = new Array(p.count), v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) { m.getVertexPosition(i, v); out[i] = v.clone().applyMatrix4(m.matrixWorld); }
  return out;
}
const trisOf = (m) => { const idx = m.geometry.index, out = []; for (let t = 0; t < idx.count / 3; t++) out.push([idx.getX(t * 3), idx.getX(t * 3 + 1), idx.getX(t * 3 + 2)]); return out; };
/** All hits of a ray on triangles, distances along it. */
function hits(o, d, tris, P, maxT = 0.4) {
  const out = [], e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), p = new THREE.Vector3(), q = new THREE.Vector3(), s = new THREE.Vector3();
  for (const tr of tris) {
    const a = P[tr[0]], b = P[tr[1]], c = P[tr[2]];
    e1.subVectors(b, a); e2.subVectors(c, a); p.crossVectors(d, e2);
    const det = e1.dot(p); if (Math.abs(det) < 1e-12) continue;
    const inv = 1 / det; s.subVectors(o, a);
    const u = s.dot(p) * inv; if (u < 0 || u > 1) continue;
    q.crossVectors(s, e1);
    const v = d.dot(q) * inv; if (v < 0 || u + v > 1) continue;
    const t = e2.dot(q) * inv; if (t > 1e-5 && t < maxT) out.push(t);
  }
  return out;
}
/** Triangles with a corner within `r` of the segment a-b (a quick cull). */
function near(tris, P, a, b, r) {
  const ab = b.clone().sub(a), l2 = ab.lengthSq(), d = new THREE.Vector3();
  const close = (p) => { const t = Math.min(1, Math.max(0, d.subVectors(p, a).dot(ab) / l2)); return d.copy(a).addScaledVector(ab, t).distanceTo(p) < r; };
  return tris.filter((tr) => tr.some((i) => close(P[i])));
}
/** The poses measured: as bound, idle, and six of the walk. */
function poses(g) {
  const mixer = new THREE.AnimationMixer(g.scene), out = [['bind', () => { g.scene.traverse((o) => { if (o.isBone && o.userData.q0) { o.quaternion.copy(o.userData.q0); o.position.copy(o.userData.p0); } }); g.scene.updateMatrixWorld(true); }]];
  g.scene.traverse((o) => { if (o.isBone) { o.userData.q0 = o.quaternion.clone(); o.userData.p0 = o.position.clone(); } });
  const clip = (n) => g.gltf.animations.find((a) => a.name === n);
  const at = (c, t) => () => { mixer.stopAllAction(); const a = mixer.clipAction(c); a.reset().play(); mixer.setTime(t); g.scene.updateMatrixWorld(true); };
  const idle = clip('idle'), walk = clip('walk');
  if (idle) out.push(['idle', at(idle, idle.duration * 0.5)]);
  if (walk) for (let k = 0; k < 6; k++) out.push([`walk ${k}/6`, at(walk, (walk.duration * k) / 6)]);
  return out;
}
/** Every one-sided-or-not added piece is wound to face out (garrison's facesOut). */
function facesOut(o) {
  const pos = o.geometry.attributes.position, nor = o.geometry.attributes.normal, idx = o.geometry.index.array;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
  let agree = 0, total = 0;
  for (let i = 0; i < idx.length; i += 3) {
    a.fromBufferAttribute(pos, idx[i]); b.fromBufferAttribute(pos, idx[i + 1]); c.fromBufferAttribute(pos, idx[i + 2]);
    const f = b.sub(a).cross(c.sub(a)); if (f.lengthSq() < 1e-14) continue;
    n.fromBufferAttribute(nor, idx[i]).add(c.fromBufferAttribute(nor, idx[i + 1])).add(c.fromBufferAttribute(nor, idx[i + 2]));
    total++; if (f.dot(n) > 0) agree++;
  }
  const share = agree / Math.max(1, total);
  assert(share > 0.97, `${o.name}: faces out (${(share * 100).toFixed(1)}% of ${total} triangles)`);
  return share;
}
function keptGarments(before, after, asset, lod, allowMove, appendTo = []) {
  const piece = (m) => m.name.replace(`${asset}_`, '').replace(/_lod\d+$/, '');
  const bm = new Map(); before.scene.traverse((o) => { if (o.isSkinnedMesh) bm.set(o.name, o); });
  // No mesh more: the pieces go into the garments' own meshes (one draw call each, T-3555).
  const n0 = meshCount(before.scene), n1 = meshCount(after.scene);
  assert.equal(n1, n0, `${asset} LOD${lod}: ${n1} meshes drawn, ${n0} before this pass: the pieces go into the garment's own mesh`);
  assert.equal(n1, after.exported, `${asset} LOD${lod}: ${n1} meshes drawn, the export has ${after.exported}`);
  const prefix = (a, n) => a.array.length === n * a.itemSize ? a.array : a.array.subarray(0, n * a.itemSize);
  let tailored = 0;
  after.scene.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    const b = bm.get(o.name);
    assert(b, `${asset} LOD${lod}: ${o.name} is new`);
    const ga = o.geometry, gb = b.geometry, rec = o.userData.chicagoTailor1835;
    if (rec) {
      tailored++;
      assert(allowMove.includes(piece(o)) || appendTo.includes(piece(o)), `${asset} LOD${lod} ${o.name}: pieces appended to a garment not tailored`);
      assert.equal(rec.drawn.vertices, gb.attributes.position.count, `${asset} LOD${lod} ${o.name}: its drawn vertices first`);
      assert.equal(rec.drawn.indices, gb.index.count, `${asset} LOD${lod} ${o.name}: its drawn triangles first`);
      assert.equal(o.material.name, b.material.name, `${asset} LOD${lod} ${o.name}: its own material`);
    } else assert.equal(ga.attributes.position.count, gb.attributes.position.count, `${asset} LOD${lod} ${o.name}: nothing appended`);
    const nv = gb.attributes.position.count;
    for (const k of ['uv', 'skinIndex', 'skinWeight']) if (gb.attributes[k]) assert.deepEqual(prefix(ga.attributes[k], nv), gb.attributes[k].array, `${asset} LOD${lod} ${o.name}: ${k} kept`);
    if (gb.index) assert.deepEqual(Array.from(ga.index.array.subarray(0, gb.index.count)), Array.from(gb.index.array), `${asset} LOD${lod} ${o.name}: topology kept`);
    if (!allowMove.includes(piece(o))) {
      const pa = ga.attributes.position, pb = gb.attributes.position;
      if (pa.count === pb.count) assert.deepEqual(pa.array, pb.array, `${asset} LOD${lod} ${o.name}: not moved`);
      else for (let i = 0; i < nv; i++) assert(pa.getX(i) === pb.getX(i) && pa.getY(i) === pb.getY(i) && pa.getZ(i) === pb.getZ(i), `${asset} LOD${lod} ${o.name}: not moved (vertex ${i})`);
    }
  });
  return { meshes: n1, exported: after.exported, tailored };
}

/** Which leg each vertex is carried by (its thigh, calf, foot and ball weights), or null; with
 * `shinOnly`, only a vertex carried by its calf at least that much (the shin, the ankle, a shoe's
 * collar: never the foot in front, which leaves by the hem's open end, not through the cloth). */
function legSides(m, shinOnly = 0) {
  const names = m.skeleton.bones.map((b) => b.name), si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, out = [];
  for (let i = 0; i < si.count; i++) {
    let l = 0, r = 0, calf = 0;
    for (let k = 0; k < 4; k++) { const n = names[si.getComponent(i, k)], w = sw.getComponent(i, k); if (/^(thigh|calf|foot|ball)_l$/.test(n)) l += w; else if (/^(thigh|calf|foot|ball)_r$/.test(n)) r += w; if (/^calf_/.test(n)) calf += w; }
    out.push(calf < shinOnly ? null : l > 0.5 ? 'l' : r > 0.5 ? 'r' : null);
  }
  return out;
}
// ---- Peck ------------------------------------------------------------------------------------
// Round 4 (the catalogue: "his pleats read only as faint creases at 3 m and the fullness is less
// than the Met c.1833 pair's; the straps ... thin pale bands, hard to see from the front"):
// fullness at least FULL_MIN_M by level (round 3 drew 16.8, 15.7, 13.2 and 7.3 mm), pleat relief
// at least PLEAT_RELIEF_M (round 3: 7.8 mm), straps at least STRAP_W_MIN_M wide under the foot
// (round 3: 21 mm as measured) and at least STRAP_T_MIN_M thick (round 3: 2 mm). The lead asked for
// a dark strap too; one of the shoes' black (STRAP_LEATHER) was built and shot and could not be
// seen on the black shoe, so the strap stays the trousers' cloth (see the module).
export const TAPER_MAX = 0.86, TAPER_FAR_MAX = 0.92, FULL_MIN_M = Object.freeze([0.024, 0.024, 0.018, 0.01]), PLEAT_RELIEF_M = 0.011, GATHER_RELIEF_M = 0.0024, STRAP_SHOWS_M = 0.02, STRAP_ON_SHOE_M = 0.006, THROUGH_M = 0.002;
export const STRAP_W_MIN_M = 0.026, STRAP_T_MIN_M = 0.0028;
const lines = [], faults = [];
const check = (ok, msg) => { if (!ok) faults.push(msg); };
let strapW = Infinity;
/** A leg's outline radius (mean over angles of the outermost cloth) about its axis at height h above the ankle. */
function legGirth(points, A, K, sideX, h) {
  const axis = K.clone().sub(A).normalize(), bins = new Map();
  for (const p of points) {
    if (Math.sign(p.x) !== sideX) continue;
    const d = p.clone().sub(A), hh = d.dot(axis); if (Math.abs(hh - h) > 0.015) continue;
    d.addScaledVector(axis, -hh); const k = Math.round(Math.atan2(d.x, d.z) / (Math.PI / 12));
    bins.set(k, Math.max(bins.get(k) ?? 0, d.length()));
  }
  const v = [...bins.values()]; return v.reduce((s, x) => s + x, 0) / Math.max(1, v.length);
}
async function peck(lod) {
  strapW = Infinity;
  const asset = 'peck_philip_1835';
  const before = await prepared(asset, lod, false), after = await prepared(asset, lod, true);
  const report = after.report;
  if (!BASELINE) assert(report.length === 1 && report[0].kind === 'trousers', `${asset} LOD${lod}: the trousers are tailored (${JSON.stringify(report)})`);
  const kept = keptGarments(before, after, asset, lod, ['full_trousers'], ['closed_shoes']);
  const tb = meshOf(before.scene, 'full_trousers'), host = meshOf(after.scene, 'full_trousers'), ta = partOf(host, 'drawn');
  if (!BASELINE) assert(kept.tailored >= 1, `${asset} LOD${lod}: the pieces are in the garments' own meshes`);
  const bones = bonesOf(after.scene), A = { l: wpos(bones.foot_l), r: wpos(bones.foot_r) }, K = { l: wpos(bones.calf_l), r: wpos(bones.calf_r) };
  const H = { l: wpos(bones.thigh_l), r: wpos(bones.thigh_r) }, O = H.l.clone().add(H.r).multiplyScalar(0.5);
  const Pb = posed(tb), Pa = posed(ta);
  // Taper.
  const ratio = (P) => Math.max(...['l', 'r'].map((s) => { const sx = Math.sign(H[s].x), hk = K[s].distanceTo(A[s]); return legGirth(P, A[s], K[s], sx, 0.07) / legGirth(P, A[s], K[s], sx, hk - 0.03); }));
  const r0 = ratio(Pb), r1 = ratio(Pa);
  assert(r1 <= (lod >= 3 ? TAPER_FAR_MAX : TAPER_MAX), `${asset} LOD${lod}: the leg 7 cm above the ankle is ${(r1 * 100).toFixed(0)}% of its width under the knee (drawn ${(r0 * 100).toFixed(0)}%), not tapered`);
  // Fullness: the front of the thighs, under the waistcoat's hem.
  const front = (P) => Math.min(...['l', 'r'].map((s) => Math.max(...P.filter((p) => Math.abs(p.x - H[s].x) < (lod >= 2 ? 0.06 : 0.03) && p.y < O.y - 0.01 && p.y > O.y - (lod >= 2 ? 0.12 : 0.07)).map((p) => p.z))));
  const f0 = front(Pb), f1 = front(Pa);
  check(f1 - f0 >= FULL_MIN_M[lod], `${asset} LOD${lod}: the front of the thighs stands out ${((f1 - f0) * 1000).toFixed(1)} mm (at least ${(FULL_MIN_M[lod] * 1000).toFixed(0)}), not full`);
  // Pleats: relief across the front of each thigh, a hand under the waistcoat's hem.
  const pl = partOf(host, 'pleats');
  let relief0 = 0, relief1 = 0;
  if (lod <= 1) {
    assert(pl, `${asset} LOD${lod}: pleats`);
    const reliefOf = (meshes) => {
      const parts = meshes.filter(Boolean).map((m) => ({ P: posed(m), T: trisOf(m) }));
      let worst = Infinity;
      for (const s of ['l', 'r']) {
        const y = O.y - 0.035, sx = Math.sign(H[s].x), o = new THREE.Vector3(H[s].x * 0.6, y, H[s].z);
        const rs = [];
        for (let a = -60; a <= 25; a += 2) {
          const d = new THREE.Vector3(sx * Math.sin(a * Math.PI / 180), 0, Math.cos(a * Math.PI / 180));
          let r = 0; for (const { P, T: tr } of parts) for (const t of hits(o, d, tr, P)) r = Math.max(r, t);
          rs.push(r);
        }
        let rel = 0;
        for (let i = 3; i < rs.length - 3; i++) { const avg = (rs[i - 3] + rs[i - 2] + rs[i + 2] + rs[i + 3]) / 4; if (rs[i] && rs.slice(i - 3, i + 4).every(Boolean)) rel = Math.max(rel, rs[i] - avg); }
        worst = Math.min(worst, rel);
      }
      return worst;
    };
    relief0 = reliefOf([tb]); relief1 = reliefOf([ta, pl]);
    check(relief1 >= PLEAT_RELIEF_M, `${asset} LOD${lod}: the front of the thighs has a relief of ${(relief1 * 1000).toFixed(1)} mm (at least ${PLEAT_RELIEF_M * 1000}; drawn ${(relief0 * 1000).toFixed(1)}), pleats too faint`);
    assert.equal(pl.geometry.attributes.position.count, 2 * T.PLEATS * 5 * (lod === 0 ? 14 : 9), `${asset} LOD${lod}: ${2 * T.PLEATS} pleats`);
    facesOut(pl);
  } else assert(!pl, `${asset} LOD${lod}: no pleats this far`);
  // Straps.
  const shoes = meshOf(after.scene, 'closed_shoes'), st = partOf(shoes, 'straps') ?? partOf(host, 'straps');
  assert(st, `${asset} LOD${lod}: straps under the shoes`);
  facesOut(st);
  // Of the trousers' own cloth, in their mesh (a townsman's own trouser colour reaches it), or
  // with T.STRAP_LEATHER of the shoes' black in theirs; the shoes stay shoes to the skirt rig.
  { const inShoes = !!partOf(shoes, 'straps');
    assert.equal(inShoes, !!T.STRAP_LEATHER, `${asset} LOD${lod}: the strap is in the ${T.STRAP_LEATHER ? 'shoes' : 'trousers'}' mesh`);
    if (!BASELINE) assert.equal(garmentKind(shoes, asset).kind, garmentKind(meshOf(before.scene, 'closed_shoes'), asset).kind, `${asset} LOD${lod}: the shoes are still shoes to the skirt rig`); }
  // Thick enough to stand off the shoe and catch the light: its band at least STRAP_T_MIN_M through.
  check(T.STRAP_T_M >= STRAP_T_MIN_M, `${asset} LOD${lod}: the strap is ${T.STRAP_T_M * 1000} mm thick (at least ${STRAP_T_MIN_M * 1000})`);
  const names = st.skeleton.bones.map((b) => b.name), si = st.geometry.attributes.skinIndex, sw = st.geometry.attributes.skinWeight;
  {
    const P = posed(st), sole = Math.min(...posed(partOf(shoes, "drawn")).map((p) => p.y));
    for (const s of ['l', 'r']) {
      const sx = Math.sign(H[s].x), mine = P.map((p, i) => [p, i]).filter(([p]) => Math.sign(p.x) === sx);
      const hem = Math.min(...Pa.filter((p) => Math.sign(p.x) === sx && Math.abs(p.z - A[s].z - 0.03) < 0.03).map((p) => p.y));
      for (const side of [1, -1]) {
        const shown = mine.filter(([p]) => (p.x - A[s].x) * sx * side > 0.02 && p.y < hem - STRAP_SHOWS_M);
        assert(shown.length >= 4, `${asset} LOD${lod} ${s}: the strap shows ${STRAP_SHOWS_M * 100} cm below the hem on the ${side > 0 ? 'outer' : 'inner'} side of the foot`);
      }
      assert(Math.min(...mine.map(([p]) => p.y)) < sole + 0.01, `${asset} LOD${lod} ${s}: the strap goes under the sole`);
      // Wide along the foot, under the sole, between the ankle and the ball.
      const low = mine.filter(([p]) => p.y < sole + 0.012).map(([p]) => p.z);
      const wide = Math.max(...low) - Math.min(...low);
      check(wide >= STRAP_W_MIN_M, `${asset} LOD${lod} ${s}: the strap is ${(wide * 1000).toFixed(0)} mm wide under the foot (at least ${STRAP_W_MIN_M * 1000})`);
      strapW = Math.min(strapW, wide);
      for (const [p, i] of mine) if (p.y < hem - 0.006) {
        let foot = 0; for (let k = 0; k < 4; k++) if (names[si.getComponent(i, k)] === `foot_${s}`) foot += sw.getComponent(i, k);
        assert(foot > 0.999, `${asset} LOD${lod} ${s}: below the hem the strap rides the foot bone (${foot.toFixed(3)})`);
      }
    }
  }
  // In every pose: the strap on the shoe, nothing through the trousers, nothing through what is worn over them.
  const over = ['waistcoat_buff', 'tailcoat_body', 'tailcoat_tails'].map((p) => meshOf(after.scene, p)).filter(Boolean);
  const body = meshOf(after.scene, 'body_0'), bodyB = meshOf(before.scene, 'body_0'), shoesB = meshOf(before.scene, 'closed_shoes');
  const posesA = poses(after), posesB = poses(before);
  // The shoes as drawn (the straps appended to their mesh are measured against them, not themselves).
  const sd = partOf(shoes, 'drawn');
  const sideBody = legSides(body, 0.5), sideShoes = legSides(sd, 0.3), sideStrap = legSides(st);
  const T_tr = trisOf(ta), T_sh = trisOf(sd), T_over = over.map(trisOf);
  let worstStrap = 0, through0 = 0, through1 = 0, deep1 = 0, cover1 = 0, strapOut = 0;
  for (let k = 0; k < posesA.length; k++) {
    posesA[k][1](); posesB[k][1]();
    const Ptr = posed(ta), Psh = posed(sd), Pst = posed(st), Pb2 = posed(tb), Pbd = posed(body), Pbd0 = posed(bodyB), Psh0 = posed(shoesB);
    const bn = bonesOf(after.scene), bn0 = bonesOf(before.scene);
    // The strap below the hem lies on the shoe: within STRAP_ON_SHOE_M of its surface.
    const shoeTris = T_sh.map((t) => t.map((i) => Psh[i]));
    const closest = new THREE.Vector3(), tri = new THREE.Triangle();
    for (const s of ['l', 'r']) {
      const ankle = wpos(bn[`foot_${s}`]);
      // Its face toward the shoe: every point of the band, less the band's own thickness.
      for (let i = 0; i < Pst.length; i += 2) {
        const p = Pst[i]; if (p.distanceTo(ankle) > 0.25) continue;
        let d = Infinity;
        for (const [a, b, c] of shoeTris) { if (a.distanceToSquared(p) > 0.04) continue; tri.set(a, b, c).closestPointToPoint(p, closest); d = Math.min(d, closest.distanceTo(p)); }
        if (d < 0.1) { if (process.env.TAILOR_DEBUG && d - T.STRAP_T_M > 0.005) console.log('strap off', (d * 1000).toFixed(1), lod, posesA[k][0], s, i, (p.y * 1000).toFixed(0), (ankle.y * 1000).toFixed(0)); worstStrap = Math.max(worstStrap, d - T.STRAP_T_M); }
      }
    }
    // The shin, ankle and shoe through the trousers (rays from the shin's axis), before and after.
    const legThrough = (Ptrous, Tt, pts, bnx, sides) => {
      let n = 0, deep = 0;
      for (const s of ['l', 'r']) {
        const a = wpos(bnx[`foot_${s}`]), kk = wpos(bnx[`calf_${s}`]), axis = kk.clone().sub(a), len = axis.length(); axis.normalize();
        const tris = near(Tt, Ptrous, a.clone().addScaledVector(axis, -0.05), kk, 0.16);
        for (let i = 0; i < pts.length; i += 2) {
          if (sides[i] !== s) continue;
          const p = pts[i], d = p.clone().sub(a), h = d.dot(axis);
          if (h < 0.02 || h > len - 0.06) continue;
          d.addScaledVector(axis, -h); const r = d.length(); if (r > 0.16 || r < 0.01) continue;
          const o = a.clone().addScaledVector(axis, h), hs = hits(o, d.normalize(), tris, Ptrous, 0.3);
          if (!hs.length) continue;
          const far = Math.max(...hs);
          if (r > far + THROUGH_M) { n++; deep = Math.max(deep, r - far); if (process.env.TAILOR_DEBUG) console.log('through', s, (h * 100).toFixed(1), (r * 100).toFixed(1), (far * 100).toFixed(1), hs.length); }
        }
      }
      return { n, deep };
    };
    const tb0 = legThrough(Pb2, T_tr, [...Pbd0, ...Psh0], bn0, [...sideBody, ...sideShoes]), tb1 = legThrough(Ptr, T_tr, [...Pbd, ...Psh], bn, [...sideBody, ...sideShoes]);
    through0 += tb0.n; through1 += tb1.n; deep1 = Math.max(deep1, tb1.deep);
    // The strap's top, sewn inside the hem, never out through it.
    strapOut += legThrough(Ptr, T_tr, Pst, bn, sideStrap).n;
    // The fuller cloth and the pleats under what is worn over them: rays out from the hips'
    // axis through each moved point; a garment that was outside the cloth drawn stays outside.
    const Pover = over.map(posed), mid = wpos(bn.thigh_l).add(wpos(bn.thigh_r)).multiplyScalar(0.5);
    const check = (Pnew, Pold) => {
      for (let i = 0; i < Pnew.length; i += 3) {
        const p = Pnew[i], q = Pold ? Pold[i] : null;
        if (q && p.distanceTo(q) < 5e-4) continue;
        if (p.y < mid.y - 0.45) continue;
        const o = new THREE.Vector3(mid.x, p.y, mid.z), d = p.clone().sub(o); d.y = 0; const r = d.length(); d.normalize();
        const r0q = q ? (() => { const e = q.clone().sub(o); e.y = 0; return e.length(); })() : r - T.PLEAT_M - 0.002;
        for (let m = 0; m < over.length; m++) {
          const hs = hits(o, d, near(T_over[m], Pover[m], p.clone().setY(p.y - 0.05), p.clone().setY(p.y + 0.05), 0.12), Pover[m], 0.5).filter((t) => t > r0q + 1e-3);
          if (hs.length && Math.min(...hs) < r - 5e-4) cover1++;
        }
      }
    };
    check(Ptr, Pb2.length === Ptr.length ? Pb2 : null);
    if (pl) check(posed(pl), null);
  }
  assert(worstStrap <= STRAP_ON_SHOE_M, `${asset} LOD${lod}: the strap stands ${(worstStrap * 1000).toFixed(1)} mm off the shoe in some pose`);
  assert(through1 <= through0, `${asset} LOD${lod}: the shin or shoe comes through the trousers at ${through1} points over the poses (drawn ${through0}), up to ${(deep1 * 1000).toFixed(1)} mm`);
  assert.equal(strapOut, 0, `${asset} LOD${lod}: the strap's top comes out through the hem at ${strapOut} points`);
  assert.equal(cover1, 0, `${asset} LOD${lod}: the trousers or pleats come through the waistcoat, tails or coat at ${cover1} points`);
  lines.push(`${asset} LOD${lod}: taper ${(r0 * 100).toFixed(0)}→${(r1 * 100).toFixed(0)}%, thigh front +${((f1 - f0) * 1000).toFixed(1)} mm, pleat relief ${(relief0 * 1000).toFixed(1)}→${(relief1 * 1000).toFixed(1)} mm, strap ${(strapW * 1000).toFixed(0)} mm wide in ${st.material.name}, ≤${(worstStrap * 1000).toFixed(1)} mm off the shoe, through ${through0}→${through1} (≤${(deep1 * 1000).toFixed(1)} mm), cover 0; meshes ${kept.exported}→${kept.meshes}, trousers ${tb.geometry.attributes.position.count}→${host.geometry.attributes.position.count} vertices`);
  return after;
}

/** Which forearm each vertex is carried by (its forearm and hand weights at least half), or null. */
function foreSides(m) {
  const names = m.skeleton.bones.map((b) => b.name), si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, out = [];
  for (let i = 0; i < si.count; i++) {
    let l = 0, r = 0;
    for (let k = 0; k < 4; k++) { const n = names[si.getComponent(i, k)], w = sw.getComponent(i, k), m2 = n.match(/^(lowerarm|hand|thumb|index|middle|ring|pinky)(_\d+)?_([lr])$/); if (m2) { if (m2[3] === 'l') l += w; else r += w; } }
    out.push(l > 0.5 ? 'l' : r > 0.5 ? 'r' : null);
  }
  return out;
}
// ---- Mahoney ---------------------------------------------------------------------------------
export const WHITE_MIN = 210, WARM_MIN = 0.86, BAND_MIN_M = 0.03, BAND_SPREAD_M = 0.003, PUFF_MIN = 1.25;
/** The shirt's picture SHIRT_PICTURE_SRGB was measured from (one flat colour, 256 x 256 JPEG). */
const PICTURE_SHA = 'd392eb4c3bc6b9414b4d1ea0579f2a291b6219a4416b9327da12b39020169775';
async function shirtPicture(lod) {
  const b = await glb('mahoney_patrick_1835', lod), n = b.readUInt32LE(12), doc = JSON.parse(b.subarray(20, 20 + n));
  const m = doc.materials.find((x) => x.name === 'garment_upper__shirt_unbleached_1835');
  const im = doc.images[doc.textures[m.pbrMetallicRoughness.baseColorTexture.index].source], bv = doc.bufferViews[im.bufferView];
  const bytes = b.subarray(28 + n).subarray(bv.byteOffset ?? 0, (bv.byteOffset ?? 0) + bv.byteLength);
  return crypto.createHash('sha256').update(bytes).digest('hex');
}
const toSrgb = (c) => Math.round(255 * (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055));
async function mahoney(lod) {
  const asset = 'mahoney_patrick_1835';
  const before = await prepared(asset, lod, false), after = await prepared(asset, lod, true);
  const report = after.report;
  if (!BASELINE) assert(report.length === 1 && report[0].kind === 'shirt', `${asset} LOD${lod}: the shirt is tailored (${JSON.stringify(report)})`);
  const kept = keptGarments(before, after, asset, lod, ['shirt_full_sleeves']);
  if (!BASELINE) assert.equal(kept.tailored, 1, `${asset} LOD${lod}: the pieces are in the shirt's own mesh`);
  // Colour. The picture (flat sRGB 158, 147, 125, as SHIRT_PICTURE_SRGB says) is pinned.
  assert.equal(await shirtPicture(lod), PICTURE_SHA, `${asset} LOD${lod}: the shirt's picture is the one SHIRT_PICTURE_SRGB was measured from`);
  const host = meshOf(after.scene, 'shirt_full_sleeves'), sa = partOf(host, 'drawn'), sb = meshOf(before.scene, 'shirt_full_sleeves');
  const lin = (rgb) => rgb.map((c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; });
  const drawn = (mat, withMap) => { const pic = lin(T.SHIRT_PICTURE_SRGB); const c = [mat.color.r, mat.color.g, mat.color.b]; return (withMap ? c.map((x, k) => x * pic[k]) : c).map(toSrgb); };
  const c0 = drawn(sb.material, true);   // the asset draws its picture under a white colour
  // As this test parses it (no picture: the colour alone) and as the town draws it (the
  // picture under the colour, the same white).
  const c1 = drawn(sa.material, false);
  const withMap = new THREE.MeshStandardMaterial({ name: sa.material.name, map: new THREE.Texture() });
  if (!BASELINE) T.whitenShirt(withMap);
  const c2 = drawn(withMap, true);
  const okWhite = (c) => Math.min(...c) >= WHITE_MIN && c[0] >= c[1] && c[1] >= c[2] && c[2] >= WARM_MIN * c[0];
  assert(okWhite(c2), `${asset} LOD${lod}: the shirt is drawn sRGB ${c2.join(', ')} (was ${c0.join(', ')}): not a warm white linen`);
  assert(c2.every((x, k) => Math.abs(x - c1[k]) <= 1), `${asset} LOD${lod}: without its picture the shirt is drawn sRGB ${c1.join(', ')}, not ${c2.join(', ')}`);
  // A townsman wearing this body with his own shirt colour keeps it.
  {
    const own = [0.15, 0.2, 0.3], fig = after.scene.clone();
    dressCloth(fig, { colours: { [sa.material.name]: own } });
    let got = null; fig.traverse((o) => { if (/shirt_full_sleeves/.test(o.name)) got = o.material.color.toArray(); });
    assert.deepEqual(got.map((x) => +x.toFixed(4)), own, `${asset} LOD${lod}: a townsman's own shirt colour replaces the white`);
  }
  // The band and the gathers about each forearm, at bind.
  const band = partOf(host, 'wristbands'), gat = partOf(host, 'gathers');
  assert(band, `${asset} LOD${lod}: wristbands`);
  facesOut(band); if (gat) facesOut(gat);
  { const k = garmentKind(host, asset), k0 = garmentKind(sb, asset); assert(k.kind === k0.kind && k.count === k0.count && Math.abs(k.low - k0.low) < 1e-6, `${asset} LOD${lod} ${host.name}: with its band and gathers the same garment to the skirt rig (${k.kind}, ${k.count} low points; drawn ${k0.kind}, ${k0.count})`); }
  if (lod <= 1) assert(gat, `${asset} LOD${lod}: gathers`);
  const bones = bonesOf(after.scene);
  const forearm = (s, bn = bones) => { const E = wpos(bn[`lowerarm_${s}`]), W = wpos(bn[`hand_${s}`]); return { E, W, fore: W.clone().sub(E).normalize(), len: E.distanceTo(W) }; };
  const polar = (a, p) => { const d = p.clone().sub(a.E), t = d.dot(a.fore); d.addScaledVector(a.fore, -t); return { t, r: d.length(), d }; };
  const lineParts = [];
  let relief0 = Infinity, relief1 = Infinity, puff1 = Infinity, spread = 0, blen = Infinity;
  for (const s of ['l', 'r']) {
    const a = forearm(s), side = (p) => polar(a, p).t > -0.05 && polar(a, p).t < a.len + 0.05 && polar(a, p).r < 0.15;
    const PB = posed(band).filter(side), PS = posed(sa).filter(side);
    const tb = PB.map((p) => polar(a, p).t), t0 = Math.min(...tb), t1 = Math.max(...tb);
    blen = Math.min(blen, t1 - t0);
    // One width along the band: the mean radius of its outer face, in slices along it.
    const outer = PB.filter((p) => { const q = polar(a, p); return q.t > t0 + 0.004 && q.t < t1 - 0.004; });
    // (its outer face's two edges, near its foot and its top, as the arm holds them)
    const rings = [t0 + 0.002, t1 - 0.002].map((tt) => { const ring = outer.concat(PB).filter((p) => Math.abs(polar(a, p).t - tt) < 0.0015).map((p) => polar(a, p).r); return ring.reduce((x, y) => x + y, 0) / ring.length; });
    spread = Math.max(spread, Math.max(...rings) - Math.min(...rings));
    const bandR = Math.min(...rings);
    // The sleeve's end is inside the band.
    const sEnd = Math.max(...PS.map((p) => polar(a, p).t));
    assert(sEnd <= t1 + 1e-4, `${asset} LOD${lod} ${s}: the sleeve's end (${(sEnd * 100).toFixed(1)} cm) is past the band (${(t1 * 100).toFixed(1)})`);
    // Relief round the arm and the puff over the band.
    const relief = (meshes, t) => {
      const parts = meshes.filter(Boolean).map((m) => ({ P: posed(m), T: trisOf(m) }));
      const u = new THREE.Vector3(0, 1, 0).addScaledVector(a.fore, -a.fore.y).normalize(), w = new THREE.Vector3().crossVectors(a.fore, u);
      const o = a.E.clone().addScaledVector(a.fore, t), rs = [];
      for (let k = 0; k < 90; k++) {
        const th = (k / 90) * Math.PI * 2, d = u.clone().multiplyScalar(Math.cos(th)).addScaledVector(w, Math.sin(th));
        let r = 0; for (const { P, T: tr } of parts) for (const x of hits(o, d, tr, P, 0.2)) r = Math.max(r, x);
        rs.push(r);
      }
      let rel = 0;
      for (let i = 0; i < 90; i++) { const avg = (rs[(i + 86) % 90] + rs[(i + 87) % 90] + rs[(i + 3) % 90] + rs[(i + 4) % 90]) / 4; rel = Math.max(rel, rs[i] - avg); }
      return { rel, mean: rs.reduce((x, y) => x + y, 0) / 90 };
    };
    const tUp = t0 - 0.03;
    const r0 = relief([sb], tUp), r1 = relief([sa, gat], tUp);
    relief0 = Math.min(relief0, r0.rel); relief1 = Math.min(relief1, r1.rel);
    puff1 = Math.min(puff1, r1.mean / bandR);
    lineParts.push(`${s}: band ${((t1 - t0) * 100).toFixed(1)} cm r ${(bandR * 100).toFixed(1)} cm, puff ×${(r1.mean / bandR).toFixed(2)}, relief ${(r0.rel * 1000).toFixed(1)}→${(r1.rel * 1000).toFixed(1)} mm`);
  }
  assert(blen >= BAND_MIN_M, `${asset} LOD${lod}: the wristband is ${(blen * 100).toFixed(1)} cm long`);
  assert(spread <= BAND_SPREAD_M, `${asset} LOD${lod}: the wristband's width varies ${(spread * 1000).toFixed(1)} mm along it`);
  if (lod <= 1) {
    assert(puff1 >= PUFF_MIN, `${asset} LOD${lod}: above the band the sleeve is ×${puff1.toFixed(2)} the band: not bloused over it`);
    assert(relief1 >= GATHER_RELIEF_M, `${asset} LOD${lod}: the sleeve above the band has a relief of ${(relief1 * 1000).toFixed(1)} mm (drawn ${(relief0 * 1000).toFixed(1)}): not gathered`);
  }
  // In every pose: the sleeve not through the gathers or band, the wrist not through the band.
  const body = meshOf(after.scene, 'body_0'), outerMeshes = [band, gat].filter(Boolean);
  const T_out = outerMeshes.map(trisOf), T_s = trisOf(sa);
  let sleeveOut = 0, wristOut = 0, deepest = 0;
  const foreS = foreSides(sa), foreB = foreSides(body);
  for (const [, set] of poses(after)) {
    set();
    const bn = bonesOf(after.scene), Pout = outerMeshes.map(posed), Ps = posed(sa), Pbd = posed(body);
    for (const s of ['l', 'r']) {
      const a = forearm(s, bn);
      const tb = Pout[0].map((p) => polar(a, p)).filter((q) => q.r < 0.12 && q.t > 0 && q.t < a.len + 0.05).map((q) => q.t);
      const tBand = Math.min(...tb), tTop = T.FOLD_TOP_M;
      const trisNear = Pout.map((P, m) => near(T_out[m], P, a.E.clone().addScaledVector(a.fore, tTop - 0.02), a.W.clone().addScaledVector(a.fore, 0.04), 0.14));
      const outR = (o, d) => { let r = 0; Pout.forEach((P, m) => { for (const x of hits(o, d, trisNear[m], P, 0.2)) r = Math.max(r, x); }); return r; };
      for (let i = 0; i < Ps.length; i += 2) {
        if (foreS[i] !== s) continue;
        const q = polar(a, Ps[i]); if (q.t < tTop + 0.01 || q.t > a.len + 0.05 || q.r > 0.14 || q.r < 0.005) continue;
        const o = a.E.clone().addScaledVector(a.fore, q.t), R = outR(o, q.d.clone().normalize());
        if (R && q.r > R + THROUGH_M) { sleeveOut++; deepest = Math.max(deepest, q.r - R); if (process.env.TAILOR_DEBUG) console.log('sleeve', s, (q.t * 100).toFixed(1), (q.r * 100).toFixed(1), (R * 100).toFixed(1)); }
      }
      const sTris = near(T_s, Ps, a.E.clone().addScaledVector(a.fore, tBand - 0.01), a.W.clone().addScaledVector(a.fore, 0.04), 0.12);
      for (let i = 0; i < Pbd.length; i++) {
        if (foreB[i] !== s) continue;
        const q = polar(a, Pbd[i]); if (q.t < tBand || q.t > tBand + T.BAND_M - 0.004 || q.r > 0.08) continue;
        const o = a.E.clone().addScaledVector(a.fore, q.t), d = q.d.clone().normalize(), R = outR(o, d);
        let Rs = 0; for (const x of hits(o, d, sTris, Ps, 0.2)) Rs = Math.max(Rs, x);
        if ((R && q.r > R + THROUGH_M) || (Rs && q.r > Rs + THROUGH_M)) wristOut++;
      }
    }
  }
  assert.equal(sleeveOut, 0, `${asset} LOD${lod}: the sleeve comes through the gathers or band at ${sleeveOut} points, up to ${(deepest * 1000).toFixed(1)} mm`);
  assert.equal(wristOut, 0, `${asset} LOD${lod}: the wrist comes through the band or the sleeve under it at ${wristOut} points`);
  lines.push(`${asset} LOD${lod}: shirt sRGB ${c0.join(',')}→${c1.join(',')}; ${lineParts.join('; ')}; through 0; meshes ${kept.exported}→${kept.meshes}, shirt ${sb.geometry.attributes.position.count}→${host.geometry.attributes.position.count} vertices`);
  return after;
}

const done = [];
const only = process.env.TAILOR_ONLY ?? '';   // 'peck' or 'mahoney': one body's measures (to see each fail on the old code)
if (only !== 'mahoney') for (const lod of [0, 1, 2, 3]) done.push(await peck(lod));
if (only !== 'peck') for (const lod of [0, 1, 2, 3]) done.push(await mahoney(lod));
// Once per loaded body: a second call returns the first report and adds and moves nothing.
for (const g of done) {
  const count = () => { let n = 0; g.scene.traverse(() => n++); return n; }, n0 = count();
  const held = []; g.scene.traverse((o) => { if (o.isSkinnedMesh) held.push([o, o.geometry.attributes.position.array.slice()]); });
  assert.equal(tailor(g.scene), g.report, 'the second call returns the first report');
  assert.equal(count(), n0, 'a second call adds nothing');
  for (const [o, a] of held) assert.deepEqual(o.geometry.attributes.position.array, a, `${o.name}: a second call moved it`);
}
// Any other body is left alone (those who share these bodies' cloth names do not exist; the
// 1835 labourer, the dress study and an 1812 settler as the nearest kinds).
for (const asset of ['bardwell_otis_1835', 'flynn_mary_1835_dress_study', 'settler_1812']) {
  const a = await prepared(asset, 0, true), b = await prepared(asset, 0, false);
  assert.deepEqual(a.report, [], `${asset}: not tailored`);
  keptGarments(b, a, asset, 0, []);
  const colours = (g) => { const c = []; g.scene.traverse((o) => { if (o.material?.color) c.push(o.material.color.getHexString()); }); return c; };
  assert.deepEqual(colours(a), colours(b), `${asset}: no colour changed`);
}
// Wired into humans.js's parse, after the sleeve hems and before the waist, before any clone.
{
  const humans = await fs.readFile(process.env.HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ tailor1835 \} from '\.\/human-tailor-1835\.js';/.test(humans), 'humans.js imports tailor1835');
  assert(/const gltf = await loader\.parseAsync\(.*\);[\s\S]{0,1400}fitSleeves\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,200}tailor1835\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,200}fitWaist\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,400}return gltf;/.test(humans), 'parse() tailors the shared source after fitSleeves, before fitWaist (another pass may stand between)');
}
console.log(lines.join('\n'));
if (faults.length) { for (const f of faults) console.log(`FAIL ${f}`); assert.fail(`${faults.length} faults${process.env.TAILOR_JS ? ` (TAILOR_JS=${process.env.TAILOR_JS})` : ''}`); }
console.log(`peck_philip_1835 and mahoney_patrick_1835, LOD0-3: tapered, full (fuller at the hips), deeply pleated and strapped (wide) trousers; a white linen shirt gathered into wristbands; nothing through, nothing else moved: PASS`);
