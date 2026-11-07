// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3412: no two people alike. Every drawn person shares one hm08 body, so until this they
 * shared one face, one height and one build. This module gives each person their own, drawn
 * from a seed of their id along the axes of the shared MakeHuman delta kit
 * (assets/humans/web/hm08_variation_kit.*, written by tools/human_variation_kit.py from pinned
 * CC0 MakeHuman targets).
 *
 *   personVariation(...)  the person's values: one per axis, height, age. Pure; same id, same
 *                         person, in every year file, every LOD and every machine.
 *   applyVariation(...)   adds them to a cloned figure: the body, and its garments, hair and
 *                         eyes carried by the nearest body vertex, so clothes follow the build.
 *
 * What it changes is positions and normals in a copy of each touched attribute (same int16
 * quantisation as the file), never a texture, so a person costs about 0.3 MB at LOD0 and the
 * kit is shared. The variant geometry is cached on the source geometry, so a LOD swap back
 * reuses it, and freed with the source (disposeVariants, from humans.js).
 *
 * Scope. `full` (a person on foot) uses every axis and a height. `face` (a seated driver,
 * whose clothes, seat and reins were fitted to the engineering body) moves only the face, so
 * nothing he sits on or holds moves. A person keeps the same face in both.
 *
 * Grades. Every drawn value is reconstructed (liberty L-human-variation-3412). An age comes
 * from the person's own record where it has one. A face fitted to a picture of the person
 * (data/humans/variation/fits/) replaces the drawn face values and carries the picture's grade.
 */
import * as THREE from 'three';

export const KIT_JSON = 'hm08_variation_kit.json';

/** A deterministic PRNG of a string: FNV-1a into mulberry32. */
export function seededRandom(key) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < key.length; i++) { h ^= key.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  let a = h || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gauss(rand) {
  const u = Math.max(rand(), 1e-12), v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
const clip = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

/** Parse a kit from its table of contents and binary. */
export function parseVariationKit(header, bin) {
  if (header?.format !== 'chicago4d_human_variation_kit_v1') throw new Error('human variation: unknown kit format');
  if (bin.byteLength !== header.bin_bytes) throw new Error('human variation: kit binary is the wrong size');
  const N = header.vertex_count;
  const refsQ = new Int16Array(bin, header.refs.offset, N * 3);
  const refs = new Float32Array(N * 3);
  for (let i = 0; i < refs.length; i++) refs[i] = refsQ[i] * header.ref_unit_m;
  const uvQ = new Uint16Array(bin, header.uvs.offset, N * 2);
  const uvs = new Float32Array(N * 2);
  for (let i = 0; i < uvs.length; i++) uvs[i] = uvQ[i] / 65535;
  const half = (h) => h && { count: h.count, index: new Uint16Array(bin, h.index, h.count), delta: new Int16Array(bin, h.delta, h.count * 3) };
  const axes = header.axes.map((a) => ({ ...a, pos: half(a.pos), neg: half(a.neg), options: a.options?.map(half) }));
  return { header, N, refs, uvs, axes, unit: header.delta_unit_m, uvGrid: null };
}

/** Fetch and parse the kit beside the human GLBs. Resolves null (no variation) on failure. */
export async function loadVariationKit(base, fetchImpl = fetch) {
  try {
    const jsonURL = new URL(KIT_JSON, base);
    const res = await fetchImpl(jsonURL);
    if (!res.ok) return null;
    const header = await res.json();
    const bres = await fetchImpl(new URL(header.bin, jsonURL));
    if (!bres.ok) return null;
    return parseVariationKit(header, await bres.arrayBuffer());
  } catch { return null; }
}

/**
 * A person's values. `key` is the person id (or an instance id for someone unnamed);
 * `record` is their persons.json row (age, a fitted face), `assetId` the body they wear.
 */
export function personVariation({ kit, key, record = null, assetId = null, sceneYear = null }) {
  const rand = seededRandom(`chicago4d:human-variation:v1:${key}`);
  const asset = kit.header.assets?.[assetId] ?? { base_age_years: 35, sex: 'male' };
  const values = {}, option = {}, L = kit.header.limit ?? 0.6;
  // Every axis draws in order whatever the scope, so a person's face is the same seated or on foot.
  for (const a of kit.axes) {
    // A sex's own targets for an axis another sex already draws (T-3423) take that axis's
    // draw and consume none, so adding them moves nobody's face, build, height or age.
    // A `rest` axis is never drawn (T-3434): it takes only its body's face_bias, below.
    if (a.rest) { values[a.id] = 0; continue; }
    if (a.draw_as) continue;
    const g = gauss(rand), u = rand();
    if (a.drive) continue;
    if (a.kind === 'one_of') {
      // A body may allow only some of the options (T-3434: the women's heads are never square
      // or rectangular); the same draw picks among those, so no one else's choice moves.
      const allow = asset.one_of_allow?.[a.id];
      option[a.id] = allow ? allow[Math.min(allow.length - 1, Math.floor(u * allow.length))] : Math.min(a.options.length - 1, Math.floor(u * a.options.length));
      values[a.id] = clip(Math.abs(g) * a.spread, 0, L);
    }
    else if (a.kind === 'positive') values[a.id] = clip(Math.abs(g) * a.spread, 0, L);
    else values[a.id] = clip(g * a.spread, -L, L);
  }
  // A body may damp the seeded face (T-3434: a woman's draw at full spread can land a long,
  // square, heavy-chinned face that reads as a man's): its face axes and head outline only.
  const damp = asset.face_draw_scale;
  if (damp != null) for (const a of kit.axes) if ((a.scope === 'face' || a.id === 'head_shape') && !a.drive && !a.draw_as && a.id in values) values[a.id] *= damp;
  for (const a of kit.axes) if (a.draw_as && !a.drive && a.draw_as in values) values[a.id] = values[a.draw_as];
  // The body's own lean (T-3434: the women's bodies toward MakeHuman's feminine face and a
  // resting mouth), added to the draw; a fitted face below still overrides it.
  for (const [k, v] of Object.entries(asset.face_bias ?? {})) {
    values[k] = clip((values[k] ?? 0) + v, -L, L);
    for (const a of kit.axes) if (a.draw_as === k && !a.drive) values[a.id] = values[k];
  }
  const hs = kit.header.height;
  let height = 1 + clip(gauss(rand) * hs.spread, -hs.limit, hs.limit);
  const ageBand = record?.age?.band ?? kit.header.age.default_band_years;
  const ageDraw = rand();
  const age = Number.isFinite(record?.age?.years) ? record.age.years : ageBand[0] + ageDraw * (ageBand[1] - ageBand[0]);
  const base = asset.base_age_years ?? 35;
  for (const a of kit.axes) {
    if (a.drive !== 'age') continue;
    // MakeHuman ages its targets between 25 and 90; the face pair is a -1..1 slider over that span.
    values[a.id] = a.kind === 'age_macro' ? clip((age - base) * kit.header.age.per_year, -0.5, 1)
      : clip(age >= base ? (age - base) / (90 - base) : (age - base) / (base - 25), -0.5, 1);
  }
  const face = record?.face;
  if (face?.values) {
    for (const [k, v] of Object.entries(face.values)) {
      if (k === 'height') height = v;
      else if (k.endsWith('.option')) option[k.slice(0, -7)] = v;
      else values[k] = v;
    }
  }
  return { key, assetId, sex: record?.sex ?? asset.sex ?? 'male', age, height, values, option,
    grade: face?.grade ?? 'reconstructed', sceneYear };
}

/** The axes a scope may use. */
const inScope = (a, scope, sex) => (scope === 'full' || a.scope === 'face') && (!a.sex || a.sex === sex);

/** One dense Float32 delta field over the kit's reference vertices, metres. */
export function denseDelta(kit, variation, scope = 'full') {
  const D = new Float32Array(kit.N * 3), u = kit.unit;
  const add = (h, w) => {
    if (!h || !w) return;
    for (let j = 0; j < h.count; j++) {
      const i = h.index[j] * 3, k = j * 3;
      D[i] += w * h.delta[k] * u; D[i + 1] += w * h.delta[k + 1] * u; D[i + 2] += w * h.delta[k + 2] * u;
    }
  };
  for (const a of kit.axes) {
    if (!inScope(a, scope, variation.sex)) continue;
    const v = variation.values[a.id] ?? 0;
    if (!v) continue;
    if (a.kind === 'one_of') add(a.options[variation.option[a.id] ?? 0], v);
    else if (v > 0 || !a.neg) add(a.pos, v);
    else add(a.neg, -v);
  }
  return D;
}

/**
 * Cell coordinates to one number (T-3439): a cell is at most 32,767 cells from the origin on
 * any axis, which at the 1 cm and 3 cm cells used here is hundreds of metres. A string key
 * (`c.join(',')`) cost a garment's first fit seconds of the main thread.
 */
const KEY_SPAN = 65536, KEY_MID = 32768;
function cellKey(c) {
  let k = 0;
  for (let d = 0; d < c.length; d++) k = k * KEY_SPAN + (c[d] + KEY_MID);
  return k;
}

/** A uniform hash grid over `dim`-dimensional points, for nearest-point queries. */
export function pointGrid(points, dim, cell) {
  const map = new Map(), n = points.length / dim;
  const c = new Array(dim);
  for (let i = 0; i < n; i++) {
    for (let d = 0; d < dim; d++) c[d] = Math.floor(points[i * dim + d] / cell);
    const k = cellKey(c); let list = map.get(k); if (!list) map.set(k, (list = [])); list.push(i);
  }
  return { points, dim, cell, map, key: cellKey };
}

/**
 * Index of the nearest grid point to each query point (the search widens until it finds one).
 *
 * T-3439: the shells are walked in the same order as ever (the cube of each ring in
 * lexicographic order, only its surface read; strictly nearer wins, so ties go to the first
 * seen), with numeric keys and no allocation per cell. It used to build a key string and two
 * arrays for every cell of the cube, surface or not: 2.2 of a 1904 cook's 3.7 s first fit.
 */
export function nearest(grid, query) {
  const { points, dim, cell, map } = grid, n = query.length / dim;
  const out = new Uint32Array(n), c = new Array(dim), o = new Array(dim);
  let p = 0, best = -1, bd = Infinity;
  const read = (k) => {
    const list = map.get(k);
    if (!list) return;
    for (let li = 0; li < list.length; li++) {
      const v = list[li];
      let s = 0; for (let e = 0; e < dim; e++) { const z = points[v * dim + e] - query[p * dim + e]; s += z * z; }
      if (s < bd) { bd = s; best = v; }
    }
  };
  // The cube of side 2 ring + 1 about cell c, lexicographic, reading only the cells on its surface.
  const shell = (ring) => {
    if (dim === 2) {
      for (let x = -ring; x <= ring; x++) {
        const edge = x === -ring || x === ring, kx = (c[0] + x + KEY_MID) * KEY_SPAN;
        for (let y = -ring; y <= ring; y++) {
          if (!edge && y !== -ring && y !== ring) continue;
          read(kx + (c[1] + y + KEY_MID));
        }
      }
      return;
    }
    if (dim === 3) {
      for (let x = -ring; x <= ring; x++) {
        const ex = x === -ring || x === ring, kx = (c[0] + x + KEY_MID) * KEY_SPAN;
        for (let y = -ring; y <= ring; y++) {
          const exy = ex || y === -ring || y === ring, kxy = (kx + (c[1] + y + KEY_MID)) * KEY_SPAN;
          if (exy) { for (let z = -ring; z <= ring; z++) read(kxy + (c[2] + z + KEY_MID)); }
          else { read(kxy + (c[2] - ring + KEY_MID)); if (ring) read(kxy + (c[2] + ring + KEY_MID)); }
        }
      }
      return;
    }
    const visit = (d) => {
      if (d === dim) {
        let m = 0; for (let e = 0; e < dim; e++) m = Math.max(m, Math.abs(o[e]));
        if (m !== ring) return;
        for (let e = 0; e < dim; e++) o[e] += c[e];
        read(cellKey(o));
        for (let e = 0; e < dim; e++) o[e] -= c[e];
        return;
      }
      for (let x = -ring; x <= ring; x++) { o[d] = x; visit(d + 1); }
    };
    visit(0);
  };
  for (p = 0; p < n; p++) {
    for (let d = 0; d < dim; d++) c[d] = Math.floor(query[p * dim + d] / cell);
    best = -1; bd = Infinity;
    for (let ring = 0; ring <= 6 && (best < 0 || (ring - 1) * cell <= Math.sqrt(bd)); ring++) shell(ring);
    if (best < 0) {
      // Nothing within six cells: look at every point (rare, and never in a loop of shells).
      for (let v = 0; v < points.length / dim; v++) {
        let s = 0; for (let e = 0; e < dim; e++) { const z = points[v * dim + e] - query[p * dim + e]; s += z * z; }
        if (s < bd) { bd = s; best = v; }
      }
    }
    out[p] = best < 0 ? 0 : best;
  }
  return out;
}

/** The quantisation map of a skinned mesh: bind position = M * attribute value. */
function dequant(mesh) {
  const sk = mesh.skeleton;
  if (!sk?.bones?.length) return null;
  // Relative to the figure's own root, so where the figure stands does not enter it.
  let top = mesh; while (top.parent) top = top.parent;
  const M = new THREE.Matrix4().copy(top.matrixWorld).invert()
    .multiply(sk.bones[0].matrixWorld).multiply(sk.boneInverses[0]).multiply(mesh.bindMatrix);
  const e = M.elements;
  // Only a uniform scale and offset is a quantisation; anything else and the figure is posed.
  if (Math.abs(e[0] - e[5]) > 1e-4 || Math.abs(e[0] - e[10]) > 1e-4 || Math.abs(e[1]) + Math.abs(e[2]) + Math.abs(e[4]) + Math.abs(e[6]) + Math.abs(e[8]) + Math.abs(e[9]) > 1e-4) return null;
  return { s: e[0], t: [e[12], e[13], e[14]] };
}

function vertexNormals(pos, index, n) {
  const N = new Float32Array(n * 3);
  const tri = index ? index.length / 3 : n / 3;
  for (let f = 0; f < tri; f++) {
    const a = index ? index[f * 3] : f * 3, b = index ? index[f * 3 + 1] : f * 3 + 1, c = index ? index[f * 3 + 2] : f * 3 + 2;
    const ax = pos[a * 3], ay = pos[a * 3 + 1], az = pos[a * 3 + 2];
    const ux = pos[b * 3] - ax, uy = pos[b * 3 + 1] - ay, uz = pos[b * 3 + 2] - az;
    const vx = pos[c * 3] - ax, vy = pos[c * 3 + 1] - ay, vz = pos[c * 3 + 2] - az;
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    for (const v of [a, b, c]) { N[v * 3] += nx; N[v * 3 + 1] += ny; N[v * 3 + 2] += nz; }
  }
  for (let v = 0; v < n; v++) {
    const l = Math.hypot(N[v * 3], N[v * 3 + 1], N[v * 3 + 2]) || 1;
    N[v * 3] /= l; N[v * 3 + 1] /= l; N[v * 3 + 2] /= l;
  }
  return N;
}

function quantised(attr, values) {
  const A = attr.array, out = new A.constructor(values.length);
  let span = 0; for (let i = 0; i < values.length; i++) span = Math.max(span, Math.abs(values[i]));
  // A body grown past the file's quantised range (a taller crown, a broader hand) is kept in
  // floats rather than clamped flat.
  if (attr.normalized && span <= 1) {
    const max = A instanceof Int16Array ? 32767 : A instanceof Int8Array ? 127 : A instanceof Uint16Array ? 65535 : A instanceof Uint8Array ? 255 : 0;
    const lo = A instanceof Int16Array || A instanceof Int8Array ? -max : 0;
    if (!max) return new THREE.BufferAttribute(Float32Array.from(values), attr.itemSize);
    for (let i = 0; i < values.length; i++) out[i] = clip(Math.round(values[i] * max), lo, max);
    return new THREE.BufferAttribute(out, attr.itemSize, true);
  }
  if (A instanceof Float32Array) return new THREE.BufferAttribute(Float32Array.from(values), attr.itemSize);
  return new THREE.BufferAttribute(Float32Array.from(values), attr.itemSize);
}

const variants = new WeakMap();   // source geometry -> Map(variation key -> variant geometry)

/** Free every variant made of these source geometries (call before disposing the source). */
export function disposeVariants(geometries) {
  for (const g of geometries) {
    const m = variants.get(g); if (!m) continue;
    for (const v of m.values()) { v.dispose?.(); }
    variants.delete(g);
  }
}

/** A mesh's quantised and bind-space positions. */
function meshPositions(mesh) {
  const q = dequant(mesh), pos = mesh.geometry.attributes.position;
  if (!q || !pos) return null;
  const n = pos.count, bind = new Float32Array(n * 3), raw = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) for (let c = 0; c < 3; c++) {
    const v = pos.getComponent(i, c); raw[i * 3 + c] = v; bind[i * 3 + c] = v * q.s + q.t[c];
  }
  return { q, n, raw, bind };
}

/** The body: each vertex is the kit vertex with its texture coordinate (unique on hm08). */
function bodyMap(kit, mesh) {
  const uv = mesh.geometry.attributes.uv;
  if (!uv) return null;
  kit.uvGrid ??= pointGrid(kit.uvs, 2, 0.01);
  const query = new Float32Array(uv.count * 2);
  for (let i = 0; i < uv.count; i++) { query[i * 2] = uv.getX(i); query[i * 2 + 1] = uv.getY(i); }
  const map = nearest(kit.uvGrid, query);
  // An hm08 body's texture coordinates are the kit's own (a simplified LOD's within a few
  // thousandths); any other body is not one this kit can shape, and is left as drawn.
  let off = 0;
  for (let i = 0; i < uv.count; i++) off += Math.hypot(query[i * 2] - kit.uvs[map[i] * 2], query[i * 2 + 1] - kit.uvs[map[i] * 2 + 1]) > 0.02 ? 1 : 0;
  return off > uv.count * 0.01 ? null : map;
}

/** A geometry like `src` with these positions (and its normals turned to match). */
function variantGeometry(src, mesh, cacheKey, raw, out) {
  const n = raw.length / 3, pos = src.attributes.position;
  const g = new THREE.BufferGeometry();
  g.name = `${src.name || mesh.name}~${cacheKey}`;
  g.setIndex(src.index);
  for (const [k, a] of Object.entries(src.attributes)) g.setAttribute(k, a);
  g.morphAttributes = src.morphAttributes;
  g.morphTargetsRelative = src.morphTargetsRelative;
  for (const grp of src.groups) g.addGroup(grp.start, grp.count, grp.materialIndex);
  g.setAttribute('position', quantised(pos, out));
  const nrm = src.attributes.normal;
  if (nrm) {
    // The authored normals keep their seams and creases; each is turned by the turn its
    // surface made (the shortest rotation from its computed normal before to after).
    const idx = src.index?.array ?? null;
    const before = vertexNormals(raw, idx, n), after = vertexNormals(out, idx, n);
    const nv = new Float32Array(n * 3), a = new THREE.Vector3(), b = new THREE.Vector3(), turn = new THREE.Quaternion(), v = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      a.fromArray(before, i * 3); b.fromArray(after, i * 3);
      v.set(nrm.getX(i), nrm.getY(i), nrm.getZ(i)).normalize();
      if (a.lengthSq() > 0.5 && b.lengthSq() > 0.5) v.applyQuaternion(turn.setFromUnitVectors(a, b));
      v.toArray(nv, i * 3);
    }
    g.setAttribute('normal', quantised(nrm, nv));
  }
  g.boundingBox = src.boundingBox; g.boundingSphere = src.boundingSphere;
  return g;
}

function cached(src, key) { return variants.get(src)?.get(key); }
function remember(src, key, g) {
  let m = variants.get(src); if (!m) variants.set(src, (m = new Map()));
  m.set(key, g);
}

/** Bind-space positions held by an attribute, through a mesh's quantisation map. */
function bindOf(attr, q) {
  const n = attr.count, out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) for (let c = 0; c < 3; c++) out[i * 3 + c] = attr.getComponent(i, c) * q.s + q.t[c];
  return out;
}

const CLEAR_MIN_M = 0.0015, CLEAR_MAX_M = 0.03, CARRY_M = 0.025;

/** The body's delta under a point, weighted over the skin within CARRY_M (a cloth hem does not ripple with the vertices it happens to sit nearest). */
function carriedDelta(grid, ref, d, x, y, z, nearestIdx, out) {
  const { points, cell, map } = grid, r = Math.ceil(CARRY_M / cell);
  const cx = Math.floor(x / cell), cy = Math.floor(y / cell), cz = Math.floor(z / cell);
  const sig2 = (CARRY_M / 2) ** 2;
  let w = 0; out[0] = out[1] = out[2] = 0;
  for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) for (let k = -r; k <= r; k++) {
    const list = map.get(((cx + i + KEY_MID) * KEY_SPAN + (cy + j + KEY_MID)) * KEY_SPAN + (cz + k + KEY_MID));
    if (!list) continue;
    for (const v of list) {
      const dx = points[v * 3] - x, dy = points[v * 3 + 1] - y, dz = points[v * 3 + 2] - z, s = dx * dx + dy * dy + dz * dz;
      if (s > CARRY_M * CARRY_M) continue;
      const wv = Math.exp(-s / sig2), m = ref[v] * 3;
      out[0] += wv * d[m]; out[1] += wv * d[m + 1]; out[2] += wv * d[m + 2]; w += wv;
    }
  }
  if (w > 0) { out[0] /= w; out[1] /= w; out[2] /= w; return; }
  const m = ref[nearestIdx] * 3; out[0] = d[m]; out[1] = d[m + 1]; out[2] = d[m + 2];
}

/**
 * Give a freshly cloned figure (bones still at rest) this person's body and face.
 * Returns { meshes, height, grade } or null where the figure is not an hm08 body.
 *
 * The body is matched to the kit by texture coordinate and moved by the person's delta.
 * Everything it wears takes the delta of its nearest body vertex, and then keeps at least the
 * clearance it had from the body (1.5 mm to 3 cm): where the skin under a collar or a sleeve
 * swelled past what that one vertex did, the cloth is pushed out along the skin's normal
 * instead of letting the skin through. An eye moves whole, by the mean of its socket.
 */
export function applyVariation(scene, kit, variation, { scope = 'full' } = {}) {
  if (!kit || !variation || scope === 'none') return null;
  scene.updateMatrixWorld(true);
  const key = `${variation.key}|${scope}|${kit.header.bin_sha256.slice(0, 12)}`;
  const skinned = [];
  scene.traverse((o) => { if (o.isSkinnedMesh) skinned.push(o); });
  const isBody = (m) => (m.material?.name ?? '').split('__')[0] === 'skin';
  const bodies = skinned.filter(isBody);
  if (!bodies.length) return null;
  let D = null;
  const delta = () => (D ??= denseDelta(kit, variation, scope));
  let touched = 0;
  const assign = (mesh, g) => { if (g) { mesh.geometry = g; touched++; } };
  // 1. The body, and its shape before and after for what it wears.
  const pre = { pts: [], nrm: [], ref: [] }, post = { pts: [], nrm: [] };
  for (const mesh of bodies) {
    const src = mesh.geometry, at = meshPositions(mesh);
    if (!at) return null;
    const map = bodyMap(kit, mesh);
    if (!map) return null;
    let g = cached(src, key);
    if (g === undefined) {
      const d = delta(), out = new Float32Array(at.n * 3);
      let moved = false;
      for (let i = 0; i < at.n; i++) for (let c = 0; c < 3; c++) {
        const v = d[map[i] * 3 + c]; if (v) moved = true;
        out[i * 3 + c] = at.raw[i * 3 + c] + v / at.q.s;
      }
      g = moved ? variantGeometry(src, mesh, key, at.raw, out) : null;
      remember(src, key, g);
    }
    assign(mesh, g);
    const idx = src.index?.array ?? null;
    const after = g ? bindOf(g.attributes.position, at.q) : at.bind;
    const nb = vertexNormals(at.bind, idx, at.n), na = vertexNormals(after, idx, at.n);
    for (let i = 0; i < at.n * 3; i++) { pre.pts.push(at.bind[i]); pre.nrm.push(nb[i]); post.pts.push(after[i]); post.nrm.push(na[i]); }
    for (let i = 0; i < at.n; i++) pre.ref.push(map[i]);
  }
  const preGrid = pointGrid(Float32Array.from(pre.pts), 3, 0.03);
  let postGrid = null;
  // 2. What it wears.
  for (const mesh of skinned) {
    if (isBody(mesh)) continue;
    const src = mesh.geometry;
    const hit = cached(src, key);
    if (hit !== undefined) { assign(mesh, hit); continue; }
    const at = meshPositions(mesh);
    if (!at) continue;
    const d = delta(), near = nearest(preGrid, at.bind), out = new Float32Array(at.n * 3);
    const eyes = /^eyes(__|$)/.test(mesh.material?.name ?? '');
    let moved = false;
    if (eyes) {
      const sum = { l: [0, 0, 0, 0], r: [0, 0, 0, 0] };
      for (let i = 0; i < at.n; i++) {
        const s = at.bind[i * 3] >= 0 ? sum.l : sum.r, m = pre.ref[near[i]];
        for (let c = 0; c < 3; c++) s[c] += d[m * 3 + c]; s[3]++;
      }
      for (let i = 0; i < at.n; i++) {
        const s = at.bind[i * 3] >= 0 ? sum.l : sum.r;
        for (let c = 0; c < 3; c++) { const v = s[c] / Math.max(1, s[3]); if (v) moved = true; out[i * 3 + c] = at.raw[i * 3 + c] + v / at.q.s; }
      }
    } else {
      const moving = [], dv = [0, 0, 0];
      for (let i = 0; i < at.n; i++) {
        carriedDelta(preGrid, pre.ref, d, at.bind[i * 3], at.bind[i * 3 + 1], at.bind[i * 3 + 2], near[i], dv);
        let any = false;
        for (let c = 0; c < 3; c++) { const v = dv[c]; if (v) any = true; out[i * 3 + c] = at.raw[i * 3 + c] + v / at.q.s; }
        if (any) { moved = true; moving.push(i); }
      }
      if (moving.length) {
        postGrid ??= pointGrid(Float32Array.from(post.pts), 3, 0.03);
        const P = pre.pts, PN = pre.nrm, Q = post.pts, QN = post.nrm;
        const g2 = new Float32Array(moving.length * 3);
        moving.forEach((i, k) => { for (let c = 0; c < 3; c++) g2[k * 3 + c] = out[i * 3 + c] * at.q.s + at.q.t[c]; });
        const nearPost = nearest(postGrid, g2);
        moving.forEach((i, k) => {
          const j0 = near[i], j1 = nearPost[k];
          let s0 = 0, s1 = 0;
          for (let c = 0; c < 3; c++) {
            s0 += (at.bind[i * 3 + c] - P[j0 * 3 + c]) * PN[j0 * 3 + c];
            s1 += (g2[k * 3 + c] - Q[j1 * 3 + c]) * QN[j1 * 3 + c];
          }
          if (s0 < 0) return;   // already inside before (a tuck, a fold): left as authored
          const want = Math.min(CLEAR_MAX_M, Math.max(CLEAR_MIN_M, s0));
          if (s1 >= want) return;
          for (let c = 0; c < 3; c++) out[i * 3 + c] += (want - s1) * QN[j1 * 3 + c] / at.q.s;
        });
      }
    }
    const g = moved ? variantGeometry(src, mesh, key, at.raw, out) : null;
    remember(src, key, g);
    assign(mesh, g);
  }
  const height = scope === 'full' ? variation.height : 1;
  if (height !== 1) { scene.scale.setScalar(height); scene.updateMatrixWorld(true); }
  return { meshes: touched, height, grade: variation.grade };
}
