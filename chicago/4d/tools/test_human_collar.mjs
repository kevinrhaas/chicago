// SPDX-License-Identifier: GPL-3.0-or-later
// A collar, a strap or a belt lies over the cloth it is worn on, with a clean edge
// (renderers/web/js/human-collar.js, T-3553: "Collars read as shirt collars at conversation
// distance: neckline and coat junction reshaped on the existing garments", "No clothing breaks
// through in motion"). On the real exports, on the CPU, every body that wears one, at every
// level, standing (the head ahead and turned 30 degrees either way) and at four moments of the
// walk (the arms swung 20 degrees), before and after:
//   - the cut edge: a collar, strap or belt cut out of a garment's faces had a stair for an edge
//     (risers a centimetre high, square to the edge, that the cloth beneath showed through as a
//     sawtooth). Counted as the length of the edge's risers: on the full body each faired piece
//     keeps at most RISER_KEEP of it (and never more than drawn on the far levels);
//   - the layers: where one garment is worn over another (the maid's and the cook's collars and
//     aprons over their dresses, the crossbelts over the private's coat, a standing collar over
//     its coat's neckline, the trader's waistcoat over his neckcloth, the children's collars
//     over their jackets and frocks), the share of the over cloth the under
//     cloth comes through, looking in from outside the body: at most SHOWN_MAX on the full body
//     in every pose, and never more than drawn on the far levels;
//   - round 4, the maid's and the cook's white collars: at the two near levels each lies over
//     at least COVER_MIN of its dress's black stand (12 to 25 mm below the stand's top; drawn,
//     a white sliver at the top edge with the stand showing below it), never less than drawn
//     further out (left as drawn there);
//   - round 4, the 1904 children's collars: at the two near levels the slit down the front is
//     at most SLIT_MAX_M wide (drawn 16 to 30 mm, the jacket's placket showing through it), and
//     the jacket's or frock's own neckline shows, more than NECK_SHOW_M wide between neck and
//     collar, at most NECK_SHOW_MAX of the way round off the front (drawn, a dark band above
//     the collar a quarter to a half of the way round); never worse than drawn further out;
// and: nothing but the listed pieces moves; no point moves further than the module's bounds;
// topology and UVs are kept, and skin weights except on the pieces listed to follow the garment
// beneath (whose weights still sum to one); it runs once per loaded body; and it is wired into
// humans.js's parse() before any figure is cloned (before easeSeats, so the seat's cover test
// reads the dress as it is drawn). COLLAR_MODULE=<path> measures another copy of the module
// (the old code: one whose dressCollars moves nothing); HUMANS_JS=<path> checks another
// humans.js for the wiring.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
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
const SkeletonUtils = await import(utils.SkeletonUtils);
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
// COLLAR_MODULE=<path> runs the same measurements against another copy (the old code: an empty
// module that moves nothing must fail them).
const modURL = process.env.COLLAR_MODULE ? new URL(process.env.COLLAR_MODULE, `file://${process.cwd()}/`) : new URL('renderers/web/js/human-collar.js', here);
const { dressCollars, LAYERS, FAIR, FAIR_NECK, FAIR_MAX_M, MAX_M, SETTLE_MAX_M = 0, HUG = { maxIn: 0, rise: 0 }, FRILL = { lift: 0 } } = await import(modURL);

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
const load = async (asset, lod) => {
  const g = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))), '');
  g.scene.updateMatrixWorld(true);
  return g;
};
const matName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const piece = (m, asset) => m.name.replace(`${asset}_`, '').replace(/_lod\d*$/, '');

export const RISER_KEEP = 0.35, SHOWN_MAX = 0.01, EPS_M = 0.0003;
// Round 4: a white collar's share of its dress's stand (12 to 25 mm below the stand's top) that
// it lies over; a child's collar's front slit; and the share of the way round a child's neck
// (off the front) where the jacket's or frock's own neckline shows inside the collar's opening.
export const COVER_MIN = 0.9, SLIT_MAX_M = 0.003, NECK_SHOW_M = 0.004, NECK_SHOW_MAX = 0.15;
// how far the round-4 passes may carry a point, on top of the module's other bounds: a collar
// drawn down over the stand; a child's collar's halves brought across (an edge within 3 cm of
// the middle) and drawn in; a frill stood off
const COVER_MAX_M = 0.06, HUG_MAX_M = 0.03 + HUG.maxIn + HUG.rise;

// ---- the cut edge ------------------------------------------------------------------------
/** Boundary loops of a mesh at bind (welded), and the length of their risers: boundary steps
 * longer than 3 mm running more than 60 degrees off the edge's own course (its direction
 * smoothed over 1.5 cm either side). A straight or gently curved edge has none; a corner has
 * one or two; a stair has one per tooth. */
function risers(mesh) {
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3(), P = [], key = new Map(), gof = new Int32Array(pos.count);
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix);
    const k = `${Math.round(v.x * 2e4)},${Math.round(v.y * 2e4)},${Math.round(v.z * 2e4)}`;
    let g = key.get(k); if (g === undefined) { g = P.length; key.set(k, g); P.push(v.toArray()); } gof[i] = g;
  }
  const idx = mesh.geometry.index.array, count = new Map();
  for (let t = 0; t < idx.length / 3; t++) for (let c = 0; c < 3; c++) {
    const a = gof[idx[t * 3 + c]], b = gof[idx[t * 3 + (c + 1) % 3]]; if (a === b) continue;
    const k = a < b ? `${a},${b}` : `${b},${a}`; count.set(k, (count.get(k) ?? 0) + 1);
  }
  const adj = new Map();
  for (const [k, c] of count) if (c === 1) { const [a, b] = k.split(',').map(Number); for (const [x, y] of [[a, b], [b, a]]) { if (!adj.has(x)) adj.set(x, []); adj.get(x).push(y); } }
  const seen = new Set();
  let total = 0, n = 0;
  for (const s0 of adj.keys()) {
    if (seen.has(s0) || adj.get(s0).length !== 2) continue;
    const loop = [s0]; seen.add(s0); let prev = -1, cur = s0, closed = false;
    for (;;) { const nx = adj.get(cur).find((x) => x !== prev); if (adj.get(cur).length !== 2) break; if (nx === s0) { closed = true; break; } if (seen.has(nx) || adj.get(nx)?.length !== 2) break; loop.push(nx); seen.add(nx); prev = cur; cur = nx; }
    if (!closed || loop.length < 6) continue;
    const m = loop.length, seg = loop.map((g, i) => { const a = P[g], b = P[loop[(i + 1) % m]]; return [b[0] - a[0], b[1] - a[1], b[2] - a[2]]; });
    const len = seg.map((d) => Math.hypot(...d));
    for (let i = 0; i < m; i++) {
      if (len[i] < 0.003) continue;
      // the edge's course on either side of the step, over 1.5 cm
      const fore = [0, 0, 0], aft = [0, 0, 0]; let s = 0;
      for (let k = 1; k < m && s < 0.015; k++) { const j = (i + k) % m; for (let c = 0; c < 3; c++) fore[c] += seg[j][c]; s += len[j]; }
      s = 0;
      for (let k = 1; k < m && s < 0.015; k++) { const j = (i - k + m) % m; for (let c = 0; c < 3; c++) aft[c] += seg[j][c]; s += len[j]; }
      const fl = Math.hypot(...fore), al = Math.hypot(...aft); if (fl < 1e-6 || al < 1e-6) continue;
      // a corner turns the course; a step leaves it running on as before
      if ((fore[0] * aft[0] + fore[1] * aft[1] + fore[2] * aft[2]) / (fl * al) < Math.cos(40 * Math.PI / 180)) continue;
      const course = [fore[0] / fl + aft[0] / al, fore[1] / fl + aft[1] / al, fore[2] / fl + aft[2] / al], cl = Math.hypot(...course);
      const cos = (seg[i][0] * course[0] + seg[i][1] * course[1] + seg[i][2] * course[2]) / (len[i] * cl);
      if (Math.abs(cos) < Math.cos(60 * Math.PI / 180)) { total += len[i]; n++; }
    }
  }
  return { total, n };
}

// ---- the layers --------------------------------------------------------------------------
function posed(m) {
  const p = m.geometry.attributes.position, out = new Float64Array(p.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); m.applyBoneTransform(i, v); v.applyMatrix4(m.matrixWorld); out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z; }
  return out;
}
const tris = (m) => m.geometry.index.array;
function grid(P, T, cell) {
  const map = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let t = 0; t < T.length / 3; t++) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let c = 0; c < 3; c++) for (let k = 0; k < 3; k++) { const x = P[T[t * 3 + c] * 3 + k]; lo[k] = Math.min(lo[k], x); hi[k] = Math.max(hi[k], x); }
    for (let a = Math.floor(lo[0] / cell); a <= Math.floor(hi[0] / cell); a++) for (let b = Math.floor(lo[1] / cell); b <= Math.floor(hi[1] / cell); b++) for (let c = Math.floor(lo[2] / cell); c <= Math.floor(hi[2] / cell); c++) {
      const k = key(a, b, c); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(t);
    }
  }
  return { map, key, cell, P, T };
}
function hits(g, o, d, L) {
  const seen = new Set(), out = [], steps = Math.ceil((2 * L) / (g.cell * 0.5));
  for (let s = 0; s <= steps; s++) {
    const t = -L + (2 * L * s) / steps, l = g.map.get(g.key(Math.floor((o[0] + d[0] * t) / g.cell), Math.floor((o[1] + d[1] * t) / g.cell), Math.floor((o[2] + d[2] * t) / g.cell)));
    if (!l) continue;
    for (const tri of l) {
      if (seen.has(tri)) continue; seen.add(tri);
      const { P, T } = g, a = T[tri * 3] * 3, b = T[tri * 3 + 1] * 3, c = T[tri * 3 + 2] * 3;
      const e1 = [P[b] - P[a], P[b + 1] - P[a + 1], P[b + 2] - P[a + 2]], e2 = [P[c] - P[a], P[c + 1] - P[a + 1], P[c + 2] - P[a + 2]];
      const p = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]], det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2];
      if (Math.abs(det) < 1e-14) continue;
      const sv = [o[0] - P[a], o[1] - P[a + 1], o[2] - P[a + 2]], u = (sv[0] * p[0] + sv[1] * p[1] + sv[2] * p[2]) / det; if (u < 0 || u > 1) continue;
      const q = [sv[1] * e1[2] - sv[2] * e1[1], sv[2] * e1[0] - sv[0] * e1[2], sv[0] * e1[1] - sv[1] * e1[0]], vv = (d[0] * q[0] + d[1] * q[1] + d[2] * q[2]) / det; if (vv < 0 || u + vv > 1) continue;
      const r = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) / det;
      if (r >= -L && r <= L) out.push(r);
    }
  }
  return out;
}
/** Nearest posed skin vertex, for the outward direction at a point of cloth: of the skin no higher
 * than the point (round 4: a collar drawn down to the base of the throat has the chin nearer
 * than the neck it lies on, and the chin's way out is down, into the dress below the collar). */
function skinNear(body) {
  const P = posed(body), cell = 0.03, map = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let i = 0; i < P.length; i += 3) { const k = key(Math.floor(P[i] / cell), Math.floor(P[i + 1] / cell), Math.floor(P[i + 2] / cell)); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(i); }
  return (o) => {
    let best = Infinity, bi = -1; const a = Math.floor(o[0] / cell), b = Math.floor(o[1] / cell), c = Math.floor(o[2] / cell);
    for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) for (let z = -2; z <= 2; z++) { const l = map.get(key(a + x, b + y, c + z)); if (!l) continue; for (const i of l) { if (P[i + 1] > o[1]) continue; const d = (P[i] - o[0]) ** 2 + (P[i + 1] - o[1]) ** 2 + (P[i + 2] - o[2]) ** 2; if (d < best) { best = d; bi = i; } } }
    return bi < 0 ? null : [P[bi], P[bi + 1], P[bi + 2]];
  };
}
/** The share of the over cloth's area (posed) that the under cloth comes through: across each
 * triangle of the over cloth, looking in along the outward direction from the body, the under
 * cloth's nearest surface within 1.5 cm lies outside it by more than EPS_M. */
function shown(over, under, near) {
  const Po = posed(over), To = tris(over), Pu = posed(under), g = grid(Pu, tris(under), 0.01);
  let area = 0, out = 0, deepest = 0;
  for (let t = 0; t < To.length / 3; t++) {
    const a = To[t * 3] * 3, b = To[t * 3 + 1] * 3, c = To[t * 3 + 2] * 3;
    const e1 = [Po[b] - Po[a], Po[b + 1] - Po[a + 1], Po[b + 2] - Po[a + 2]], e2 = [Po[c] - Po[a], Po[c + 1] - Po[a + 1], Po[c + 2] - Po[a + 2]];
    const ar = 0.5 * Math.hypot(e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]) / 6;
    for (let i = 0; i <= 2; i++) for (let j = 0; j <= 2 - i; j++) {
      const u = (i + 0.333) / 3, v = (j + 0.333) / 3, w = 1 - u - v; if (w < 0) continue;
      const o = [0, 1, 2].map((k) => Po[a + k] * u + Po[b + k] * v + Po[c + k] * w), q = near(o);
      if (!q) continue;
      let d = [o[0] - q[0], o[1] - q[1], o[2] - q[2]]; const l = Math.hypot(...d); if (l < 1e-4) continue; d = d.map((x) => x / l);
      const h = hits(g, o, d, 0.015);
      if (!h.length) continue;
      area += ar;
      let best = h[0]; for (const x of h) if (Math.abs(x) < Math.abs(best)) best = x;
      if (best > EPS_M) { out += ar; deepest = Math.max(deepest, best); }
    }
  }
  return { area, out, deepest };
}
// ---- round 4: the white collar's cover, the children's necklines -------------------------
function bindOf(m) {
  const p = m.geometry.attributes.position, v = new THREE.Vector3(), out = new Float64Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(m.bindMatrix); out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z; }
  return out;
}
function neckAt(m) {
  const k = m.skeleton.bones.findIndex((b) => b.name === 'neck_01');
  return k < 0 ? null : new THREE.Vector3().setFromMatrixPosition(m.skeleton.boneInverses[k].clone().invert());
}
/** The share of a dress's stand (its points 12 to 25 mm below the stand's top, in 10-degree
 * sectors round the neck) that the collar lies over: straight out from the neck, the collar's
 * surface within 3 cm outside the dress's. */
function coverShare(collar, dress) {
  const ax = neckAt(dress); if (!ax) return NaN;
  const D = bindOf(dress), C = bindOf(collar), g = grid(C, tris(collar), 0.01), top = new Float64Array(36).fill(-Infinity), pts = [];
  for (let i = 0; i < D.length / 3; i++) {
    const x = D[i * 3] - ax.x, y = D[i * 3 + 1], z = D[i * 3 + 2] - ax.z, r = Math.hypot(x, z);
    if (r > 0.14 || y < ax.y - 0.1) continue;
    const b = Math.floor(((Math.atan2(x, z) + Math.PI) / (2 * Math.PI)) * 36) % 36;
    top[b] = Math.max(top[b], y); pts.push([i, b, x / r, y, z / r]);
  }
  let n = 0, over = 0;
  for (const [i, b, dx, y, dz] of pts) {
    if (y < top[b] - 0.025 || y > top[b] - 0.012) continue;
    n++;
    if (hits(g, [D[i * 3], y, D[i * 3 + 2]], [dx, 0, dz], 0.03).some((h) => h > EPS_M)) over++;
  }
  return n ? over / n : NaN;
}
/** A child's collar: the width of its front slit (the nearest of each half to the middle, among
 * its points in front of the neck), and the share of the way round, 25 degrees or more off the
 * front, where the garment beneath shows more than NECK_SHOW_M wide between the neck and the
 * collar's inner edge (its points outside the skin and inside the collar's opening, from 2 cm
 * below the collar's inner edge to 3 cm above). */
function neckline(collar, garment, skin) {
  const ax = neckAt(collar); if (!ax) return null;
  const C = bindOf(collar), G = bindOf(garment), K = bindOf(skin), B = 72;
  const bin = (x, z) => Math.floor(((Math.atan2(x - ax.x, z - ax.z) + Math.PI) / (2 * Math.PI)) * B) % B;
  let rMean = 0; for (let i = 0; i < C.length / 3; i++) rMean += Math.hypot(C[i * 3] - ax.x, C[i * 3 + 2] - ax.z) / (C.length / 3);
  const e = { 1: Infinity, [-1]: Infinity };
  for (let i = 0; i < C.length / 3; i++) { if (C[i * 3 + 2] - ax.z <= 0.5 * rMean) continue; const x = C[i * 3] - ax.x, sd = Math.sign(x) || 1; e[sd] = Math.min(e[sd], Math.abs(x)); }
  const inner = new Float64Array(B).fill(Infinity), iy = new Float64Array(B), neckR = new Float64Array(B), show = new Float64Array(B);
  for (let i = 0; i < C.length / 3; i++) { const b = bin(C[i * 3], C[i * 3 + 2]), r = Math.hypot(C[i * 3] - ax.x, C[i * 3 + 2] - ax.z); if (r < inner[b]) { inner[b] = r; iy[b] = C[i * 3 + 1]; } }
  for (let i = 0; i < K.length / 3; i++) { const b = bin(K[i * 3], K[i * 3 + 2]), r = Math.hypot(K[i * 3] - ax.x, K[i * 3 + 2] - ax.z); if (Number.isFinite(inner[b]) && Math.abs(K[i * 3 + 1] - iy[b]) <= 0.01 && r <= inner[b]) neckR[b] = Math.max(neckR[b], r); }
  for (let i = 0; i < G.length / 3; i++) {
    const b = bin(G[i * 3], G[i * 3 + 2]), r = Math.hypot(G[i * 3] - ax.x, G[i * 3 + 2] - ax.z), y = G[i * 3 + 1];
    if (!Number.isFinite(inner[b]) || y < iy[b] - 0.02 || y > iy[b] + 0.03 || r >= inner[b] || r <= neckR[b]) continue;
    show[b] = Math.max(show[b], inner[b] - r);
  }
  let n = 0, shows = 0;
  for (let b = 0; b < B; b++) { if (Math.abs(((b + 0.5) / B) * 360 - 180) < 25) continue; n++; if (show[b] > NECK_SHOW_M) shows++; }
  return { slit: (Number.isFinite(e[1]) ? e[1] : 0) + (Number.isFinite(e[-1]) ? e[-1] : 0), share: shows / n };
}
function figure(g) {
  const sc = SkeletonUtils.clone(g.scene), root = new THREE.Group(); root.add(sc);
  const mixer = new THREE.AnimationMixer(sc), meshes = [], bones = {};
  sc.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones[o.name] = o; });
  // On top of the clip, as human-life.js and the gait do: the head turned and the arms swung.
  const turn = (b, axis, deg) => {
    if (!b) return;
    b.parent.updateWorldMatrix(true, false);
    const pq = b.parent.getWorldQuaternion(new THREE.Quaternion()), wq = pq.clone().multiply(b.quaternion);
    b.quaternion.copy(pq.invert().multiply(new THREE.Quaternion().setFromAxisAngle(axis, deg * Math.PI / 180).multiply(wq)));
  };
  return {
    meshes,
    pose(clip, f, head = 0, arms = 0) {
      mixer.stopAllAction(); const c = g.animations.find((x) => x.name === clip); mixer.clipAction(c).play(); mixer.setTime(f * c.duration);
      root.updateMatrixWorld(true);
      const up = new THREE.Vector3(0, 1, 0), side = new THREE.Vector3(1, 0, 0);
      if (head) { turn(bones.neck_01, up, head * 0.4); turn(bones.head, up, head * 0.6); }
      if (arms) { turn(bones.upperarm_l, side, arms); turn(bones.upperarm_r, side, -arms); }
      root.updateMatrixWorld(true);
    },
  };
}
const POSES = [['idle', 0, 0, 0], ['idle', 0, 30, 0], ['idle', 0, -30, 0], ['walk', 0, 0, 20], ['walk', 0.25, 0, 0], ['walk', 0.5, 0, -20], ['walk', 0.75, 20, 0]];

const ASSETS = (await fs.readdir(new URL('assets/humans/web/', here))).filter((f) => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map((f) => f.replace('.lod0.glb', '')).sort();
const lines = [];
let bodies = 0, pairs = 0, faired = 0, covers = 0, necks = 0;
const fails = [];
const check = (ok, msg) => { if (!ok) fails.push(msg); };
for (const asset of ASSETS) for (const lod of [0, 1, 2, 3]) {
  const before = await load(asset, lod), after = await load(asset, lod);
  const meshes = (g) => { const out = []; g.scene.traverse((o) => { if (o.isSkinnedMesh) out.push(o); }); return out; };
  const mb = meshes(before), ma = meshes(after);
  const names = ma.map((m) => piece(m, asset));
  const listed = (n) => FAIR.test(n) || FAIR_NECK.test(n) || LAYERS.some((L) => L.over.test(n) || L.under.test(n));
  const layerPairs = [];
  for (const L of LAYERS) for (let i = 0; i < ma.length; i++) for (let j = 0; j < ma.length; j++) if (i !== j && L.over.test(names[i]) && L.under.test(names[j])) layerPairs.push([i, j]);
  const fairs = names.map((n, i) => (FAIR.test(n) ? i : -1)).filter((i) => i >= 0);
  if (!layerPairs.length && !fairs.length) {
    // a body with none of them is left exactly as drawn
    if (lod === 0) {
      const p0 = ma.map((m) => m.geometry.attributes.position.array.slice());
      dressCollars(after.scene);
      ma.forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, p0[k], `${asset}: a body with no collar, strap or belt listed is not moved`));
    }
    continue;
  }
  if (lod === 0) bodies++;
  const snap = ma.map((m) => ({ pos: m.geometry.attributes.position.clone(), uv: m.geometry.attributes.uv?.array.slice(), si: m.geometry.attributes.skinIndex?.array.slice(), sw: m.geometry.attributes.skinWeight?.array.slice(), idx: m.geometry.index?.array.slice() }));
  const t0 = performance.now();
  const report = dressCollars(after.scene);
  const ms = performance.now() - t0;
  after.scene.updateMatrixWorld(true);
  for (let k = 0; k < ma.length; k++) {
    const m = ma[k], s = snap[k], g = m.geometry;
    // a piece listed to follow the garment beneath it is reweighted as that garment (weights
    // still summing to one); every other piece keeps its weights
    const follows = LAYERS.some((L) => L.follow && L.over.test(names[k]) && names.some((n) => L.under.test(n)));
    if (s.sw && !follows) assert.deepEqual(g.attributes.skinWeight.array, s.sw, `${asset} LOD${lod} ${m.name}: skin weights kept`);
    if (s.si && !follows) assert.deepEqual(g.attributes.skinIndex.array, s.si, `${asset} LOD${lod} ${m.name}: skin indices kept`);
    if (follows) for (let i = 0; i < g.attributes.skinWeight.count; i++) { let t = 0; for (let c = 0; c < 4; c++) t += g.attributes.skinWeight.getComponent(i, c); assert(Math.abs(t - 1) < 0.01, `${asset} LOD${lod} ${m.name}: weights of ${i} sum to ${t}`); }
    if (s.uv) assert.deepEqual(g.attributes.uv.array, s.uv, `${asset} LOD${lod} ${m.name}: UVs kept`);
    if (s.idx) assert.deepEqual(g.index.array, s.idx, `${asset} LOD${lod} ${m.name}: topology kept`);
    // only listed pieces move, and none further than the module's bounds
    const pa = g.attributes.position, va = new THREE.Vector3(), vb = new THREE.Vector3();
    let most = 0;
    for (let i = 0; i < pa.count; i++) { va.fromBufferAttribute(pa, i).applyMatrix4(m.bindMatrix); vb.fromBufferAttribute(s.pos, i).applyMatrix4(m.bindMatrix); most = Math.max(most, va.distanceTo(vb)); }
    if (!listed(names[k])) assert.equal(most, 0, `${asset} LOD${lod} ${m.name}: not listed, moved ${(most * 1000).toFixed(1)} mm`);
    const extra = (LAYERS.some((L) => L.cover && L.over.test(names[k])) ? COVER_MAX_M : 0) + (LAYERS.some((L) => L.hug && L.over.test(names[k])) ? HUG_MAX_M : 0) + (names[k] === 'apron_strap_frills' ? FRILL.lift : 0);
    const bound = Math.max(FAIR_MAX_M + Math.max(MAX_M, ...LAYERS.map((L) => L.max ?? 0)), SETTLE_MAX_M) + extra + 0.002;
    assert(most <= bound, `${asset} LOD${lod} ${m.name}: moved ${(most * 1000).toFixed(1)} mm (bound ${(bound * 1000).toFixed(0)})`);
  }
  // the cut edges
  const res = [];
  for (const k of fairs) {
    const r0 = risers(mb[k]), r1 = risers(ma[k]);
    if (lod === 0) check(r1.total <= RISER_KEEP * r0.total + 0.01, `${asset} LOD0 ${names[k]}: the cut edge keeps ${(r1.total * 100).toFixed(1)} cm of risers (drawn ${(r0.total * 100).toFixed(1)})`);
    else check(r1.total <= r0.total + 0.005, `${asset} LOD${lod} ${names[k]}: more risers than drawn (${(r1.total * 100).toFixed(1)} cm, drawn ${(r0.total * 100).toFixed(1)})`);
    if (lod === 0) res.push(`${names[k]} edge ${(r0.total * 100).toFixed(0)}→${(r1.total * 100).toFixed(0)} cm`);
    faired++;
  }
  // round 4: the white collar over its dress's stand (the two near levels; never less than
  // drawn further out), and a child's collar closed at the front and round the neck
  const near2 = lod <= 1;
  for (let i = 0; i < ma.length; i++) for (let j = 0; j < ma.length; j++) {
    if (i === j) continue;
    if (/^(white_collar|standing_collar)$/.test(names[i]) && /^(maid_bodice|plain_closed_bodice)$/.test(names[j])) {
      const c0 = coverShare(mb[i], mb[j]), c1 = coverShare(ma[i], ma[j]);
      if (near2) check(c1 >= COVER_MIN, `${asset} LOD${lod} ${names[i]}: lies over ${(c1 * 100).toFixed(0)}% of the dress's stand (drawn ${(c0 * 100).toFixed(0)}%)`);
      else check(!(c1 < c0 - 0.02), `${asset} LOD${lod} ${names[i]}: lies over less of the stand than drawn (${(c1 * 100).toFixed(0)}%, drawn ${(c0 * 100).toFixed(0)}%)`);
      if (near2) res.push(`L${lod} ${names[i]} over the stand ${(c0 * 100).toFixed(0)}→${(c1 * 100).toFixed(0)}%`);
      covers++;
    }
    if (names[i] === 'child_collar' && /^(child_jacket|frock_bodice)$/.test(names[j])) {
      const skB = mb.find((m) => matName(m) === 'skin'), skA = ma.find((m) => matName(m) === 'skin');
      const n0 = neckline(mb[i], mb[j], skB), n1 = neckline(ma[i], ma[j], skA);
      if (near2) {
        check(n1.slit <= SLIT_MAX_M, `${asset} LOD${lod} child_collar: a slit ${(n1.slit * 1000).toFixed(1)} mm wide down the front (drawn ${(n0.slit * 1000).toFixed(1)})`);
        check(n1.share <= NECK_SHOW_MAX, `${asset} LOD${lod} child_collar: ${names[j]}'s neckline shows inside it ${(n1.share * 100).toFixed(0)}% of the way round (drawn ${(n0.share * 100).toFixed(0)}%)`);
      } else {
        check(n1.slit <= n0.slit + 0.004, `${asset} LOD${lod} child_collar: the slit wider than drawn (${(n1.slit * 1000).toFixed(1)} mm, drawn ${(n0.slit * 1000).toFixed(1)})`);
        check(n1.share <= Math.max(NECK_SHOW_MAX, n0.share) + 0.04, `${asset} LOD${lod} child_collar: ${names[j]}'s neckline shows more than drawn (${(n1.share * 100).toFixed(0)}%, drawn ${(n0.share * 100).toFixed(0)}%)`);
      }
      res.push(`L${lod} slit ${(n0.slit * 1000).toFixed(0)}→${(n1.slit * 1000).toFixed(0)} mm, neckline shows ${(n0.share * 100).toFixed(0)}→${(n1.share * 100).toFixed(0)}%`);
      necks++;
    }
  }
  // the layers, standing and walking (LOD0..2; the far level is a few dozen pixels high)
  if (lod <= 2) {
    const fb = figure(before), fa = figure(after);
    const skinB = fb.meshes.find((m) => matName(m) === 'skin'), skinA = fa.meshes.find((m) => matName(m) === 'skin');
    const worst = layerPairs.map(() => [0, 0, 0, 0]);
    for (const [clip, f, head, arms] of POSES) {
      fb.pose(clip, f, head, arms); fa.pose(clip, f, head, arms);
      const nb = skinNear(skinB), na = skinNear(skinA);
      layerPairs.forEach(([i, j], q) => {
        const s0 = shown(fb.meshes[i], fb.meshes[j], nb), s1 = shown(fa.meshes[i], fa.meshes[j], na);
        const w = worst[q];
        w[0] = Math.max(w[0], s0.area ? s0.out / s0.area : 0); w[1] = Math.max(w[1], s1.area ? s1.out / s1.area : 0);
        w[2] = Math.max(w[2], s0.deepest); w[3] = Math.max(w[3], s1.deepest);
      });
    }
    layerPairs.forEach(([i, j], q) => {
      const [f0, f1, d0, d1] = worst[q], label = `${names[i]} over ${names[j]}`;
      if (LAYERS.find((L) => L.over.test(names[i]) && L.under.test(names[j]))?.byEye) { if (lod === 0) res.push(`${label} (by eye) ${(f0 * 100).toFixed(1)}→${(f1 * 100).toFixed(1)}%`); return; }
      if (lod === 0) check(f1 <= SHOWN_MAX, `${asset} LOD0 ${label}: the under cloth comes through ${(f1 * 100).toFixed(2)}% of it (drawn ${(f0 * 100).toFixed(2)}%), ${(d1 * 1000).toFixed(1)} mm deep`);
      else check(f1 <= Math.max(SHOWN_MAX, f0 + 0.002), `${asset} LOD${lod} ${label}: comes through ${(f1 * 100).toFixed(2)}%, more than drawn (${(f0 * 100).toFixed(2)}%)`);
      if (lod === 0) res.push(`${label} ${(f0 * 100).toFixed(1)}→${(f1 * 100).toFixed(2)}%`);
      pairs++;
    });
  }
  // once per loaded body
  const held = ma.map((m) => m.geometry.attributes.position.array.slice());
  assert.equal(dressCollars(after.scene), report, `${asset} LOD${lod}: the second call returns the first report`);
  ma.forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, held[k], `${asset} LOD${lod} ${m.name}: a second call moved it`));
  if (lod === 0) lines.push(`${asset} (${ms.toFixed(0)} ms): ${res.join('; ')}`);
  else if (res.length) lines.push(`${asset} LOD${lod}: ${res.join('; ')}`);
}
for (const l of lines) console.log(l);
if (fails.length) { for (const f of fails) console.log(`FAIL ${f}`); }
assert(bodies >= 10, `bodies with a collar, strap or belt: ${bodies}`);
assert(covers >= 8 && necks >= 20, `white collars over a stand measured: ${covers}; children's collars: ${necks}`);
assert.equal(fails.length, 0, `${fails.length} collar, strap or belt checks failed`);
// Wired into humans.js's parse, before any figure is cloned, ahead of the seat's cover test.
{
  const humans = await fs.readFile(process.env.HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ dressCollars \} from '\.\/human-collar\.js';/.test(humans), 'humans.js imports dressCollars');
  assert(/const gltf = await loader\.parseAsync\(.*\);[\s\S]{0,1200}dressCollars\(gltf\.scene\);\s*easeSeats\(gltf\.scene\);/.test(humans), 'parse() dresses the collars of the shared source, before the seats');
}
console.log(`${bodies} bodies, ${faired} faired edges, ${pairs} layer pairs, ${covers} white collars over the stand and ${necks} children's collars closed, over every level: edges clean, nothing through: PASS`);
