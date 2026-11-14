// SPDX-License-Identifier: GPL-3.0-or-later
// human-fine.js — a body's skin drawn finer where a person's hair stands out of it (T-3553).
//
// A person who wears their own skin sheet (human-skin.js) has hair that is the skin itself,
// pushed out as far as the sheet's mask says. The body's scalp is drawn in triangles up to
// four centimetres on a side: a top knot or a curl is smaller than one of them, and a vertex
// either catches it whole or misses it. So where the person's record says the hair stands out
// (cells of the sheet, tools/bake_likeness_skin.py `texture.grow.fine`) the triangles are split
// at the middles of their edges until none is longer than the record's `edge_m`, as the bake
// split its own copy of the head to measure the hair.
//
// What a caller may rely on:
//   - the first rows of every attribute are the source's own, in its order, so whatever reads a
//     vertex by its number (the variation kit's map, a landmark) reads the same vertex;
//   - a new vertex is the middle of one edge in every attribute and every morph target; its
//     bones are its two ends' together (the strongest four, summing to one);
//   - an edge is split for every triangle that lies along it, on both sides of a seam in the
//     texture coordinates too, so the surface stays closed;
//   - a geometry with nothing to split comes back as null, and the source is never changed.
import * as THREE from 'three';

export const FINE = Object.freeze({ rounds: 4, weld_m: 1e-5 });

/**
 * The cells of a sheet where the hair stands out, from a record's `grow.fine` block
 * ({ cell_px, edge_m, cells }: rows of cells `cell_px` wide, a bit a cell, the first cell a
 * byte's high bit, base64) and the sheet's size. Null where the block does not parse or is empty.
 */
export function fineCells(fine, size_px) {
  const [W, H] = size_px ?? [], px = fine?.cell_px, edge = fine?.edge_m;
  if (!(W > 0) || !(H > 0) || !(px > 0) || !(edge > 0) || typeof fine.cells !== 'string') return null;
  const cols = Math.floor(W / px), rows = Math.floor(H / px);
  let bits;
  try { bits = Uint8Array.from(atob(fine.cells), c => c.charCodeAt(0)); } catch { return null; }
  if (!cols || !rows || bits.length !== Math.ceil(cols * rows / 8) || !bits.some(b => b)) return null;
  return { cols, rows, bits, edge_m: edge, sx: W / px, sy: H / px };
}

const cellAt = (cells, x, y) => { const i = y * cells.cols + x; return (cells.bits[i >> 3] >> (7 - (i & 7))) & 1; };

/** An attribute's own numbers: its array, how many a vertex is apart in it, and where its first is. */
export function rawView(attr) {
  return attr.isInterleavedBufferAttribute
    ? { array: attr.data.array, stride: attr.data.stride, offset: attr.offset }
    : { array: attr.array, stride: attr.itemSize, offset: 0 };
}
export const isWhole = array => !(array instanceof Float32Array || array instanceof Float64Array);
export const fullOf = array => (array instanceof Int8Array ? 127 : array instanceof Uint8Array ? 255 : array instanceof Int16Array ? 32767 : array instanceof Uint16Array ? 65535 : 1);

/** `attr` with a row more for each pair in `ends`: the middle of those two rows (a direction keeps its length). */
function grown(attr, n0, ends, direction = false) {
  const { array, stride, offset } = rawView(attr), k = attr.itemSize, out = new array.constructor((n0 + ends.length / 2) * k);
  const whole = isWhole(out), unit = attr.normalized || !whole ? fullOf(out) : 0;
  for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) out[i * k + c] = array[i * stride + offset + c];
  for (let j = 0, i = n0; j < ends.length; j += 2, i++) {
    const a = ends[j] * k, b = ends[j + 1] * k;
    let s = 1;
    if (direction && unit) {
      let len = 0;
      for (let c = 0; c < 3; c++) len += ((out[a + c] + out[b + c]) / 2) ** 2;
      if (len > 0) s = unit / Math.sqrt(len);
    }
    for (let c = 0; c < k; c++) {
      // A tangent's fourth number is a side, not a length: the first end's.
      const v = direction && c === 3 ? out[a + c] : (out[a + c] + out[b + c]) / 2 * (direction ? s : 1);
      out[i * k + c] = whole ? Math.round(v) : v;
    }
  }
  const made = new THREE.BufferAttribute(out, k, attr.normalized);
  made.name = attr.name;
  return made;
}

/** The bones of each new vertex: its two ends' weights together, the strongest four, summing to one. */
function grownSkin(index, weight, n0, ends) {
  const I = rawView(index), W = rawView(weight), n = n0 + ends.length / 2, k = index.itemSize;
  const oi = new I.array.constructor(n * k), ow = new W.array.constructor(n * k);
  const whole = isWhole(ow), full = weight.normalized && whole ? fullOf(ow) : 1;
  for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) {
    oi[i * k + c] = I.array[i * I.stride + I.offset + c];
    ow[i * k + c] = W.array[i * W.stride + W.offset + c];
  }
  for (let j = 0, i = n0; j < ends.length; j += 2, i++) {
    const sum = new Map();
    for (const p of [ends[j], ends[j + 1]]) for (let c = 0; c < k; c++) {
      const w = ow[p * k + c];
      if (w > 0) sum.set(oi[p * k + c], (sum.get(oi[p * k + c]) ?? 0) + w);
    }
    const top = [...sum].sort((x, y) => y[1] - x[1] || x[0] - y[0]).slice(0, k);
    const total = top.reduce((s, t) => s + t[1], 0) || 1;
    const share = top.map(t => (whole ? Math.round(t[1] / total * full) : t[1] / total * full));
    if (whole && share.length) share[0] += full - share.reduce((s, v) => s + v, 0);   // rounding goes to the strongest
    for (let c = 0; c < k; c++) { oi[i * k + c] = top[c]?.[0] ?? 0; ow[i * k + c] = share[c] ?? 0; }
  }
  return [Object.assign(new THREE.BufferAttribute(oi, k, index.normalized), { name: index.name }),
    Object.assign(new THREE.BufferAttribute(ow, k, weight.normalized), { name: weight.name })];
}

/**
 * `src` with its triangles split where the hair stands out: a new geometry, or null where
 * nothing was split (no cells under it, every edge short enough already, a geometry with no
 * index or drawn in groups).
 *
 *   metres   the matrix taking `src`'s positions to metres (human-skin.js restMatrix)
 *   layout   the sheet's rectangles as human-skin.js likenessLayout returns them:
 *            { uv: [[u0, v0, u1, v1]], map: [[sx, sy, ox, oy]] }, a texture coordinate inside
 *            `uv[k]` lying at (u * sx + ox, v * sy + oy) of the sheet
 *   cells    fineCells(...)
 */
export function fineGeometry(src, { metres, layout, cells, rounds = FINE.rounds } = {}) {
  const pos = src?.attributes?.position, tex = src?.attributes?.uv;
  if (!pos || !tex || !src.index || src.groups?.length || !cells || !layout?.uv?.length || !metres) return null;
  const n0 = pos.count, v = new THREE.Vector3();
  // Each vertex: where it is (metres), which place it shares with others (a seam's two sides),
  // and which cell of the sheet it lies in (NaN: on none of the sheet's rectangles).
  const P = [], G = [], U = [], C = [];
  const cellOf = (u, w) => {
    for (let k = 0; k < layout.uv.length; k++) {
      const r = layout.uv[k], m = layout.map[k];
      if (u >= r[0] && u <= r[2] && w >= r[1] && w <= r[3]) return [(u * m[0] + m[2]) * cells.sx, (w * m[1] + m[3]) * cells.sy];
    }
    return [NaN, NaN];
  };
  const places = new Map();
  for (let i = 0; i < n0; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(metres);
    P.push(v.x, v.y, v.z);
    const key = `${Math.round(v.x / FINE.weld_m)},${Math.round(v.y / FINE.weld_m)},${Math.round(v.z / FINE.weld_m)}`;
    let g = places.get(key);
    if (g === undefined) places.set(key, (g = places.size));
    G.push(g);
    const u = tex.getX(i), w = tex.getY(i);
    U.push(u, w); C.push(...cellOf(u, w));
  }
  let groups = places.size;
  const K = 2 ** 26;
  const pair = (a, b) => (a < b ? a * K + b : b * K + a);
  const long = (a, b) => Math.hypot(P[3 * a] - P[3 * b], P[3 * a + 1] - P[3 * b + 1], P[3 * a + 2] - P[3 * b + 2]) > cells.edge_m;
  // A triangle counts where the box round its corners on the sheet touches a cell of hair.
  const hairy = (a, b, c) => {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const i of [a, b, c]) {
      const x = C[2 * i], y = C[2 * i + 1];
      if (!(x === x)) continue;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    if (x1 < x0) return false;
    const cx1 = Math.min(cells.cols - 1, Math.floor(x1)), cy1 = Math.min(cells.rows - 1, Math.floor(y1));
    for (let y = Math.max(0, Math.floor(y0)); y <= cy1; y++) for (let x = Math.max(0, Math.floor(x0)); x <= cx1; x++) if (cellAt(cells, x, y)) return true;
    return false;
  };
  let tri = Array.from(src.index.array);
  const ends = [];
  for (let round = 0; round < rounds; round++) {
    // The edges to split, by place: every edge of a triangle of hair that has one too long.
    const marked = new Set();
    for (let t = 0; t < tri.length; t += 3) {
      const a = tri[t], b = tri[t + 1], c = tri[t + 2];
      if (!(long(a, b) || long(b, c) || long(c, a)) || !hairy(a, b, c)) continue;
      marked.add(pair(G[a], G[b])); marked.add(pair(G[b], G[c])); marked.add(pair(G[c], G[a]));
    }
    if (!marked.size) break;
    const made = new Map(), placed = new Map();
    const mid = (a, b) => {
      const gk = pair(G[a], G[b]);
      if (!marked.has(gk)) return -1;
      const vk = pair(a, b);
      let m = made.get(vk);
      if (m !== undefined) return m;
      m = P.length / 3;
      made.set(vk, m);
      for (let c = 0; c < 3; c++) P.push((P[3 * a + c] + P[3 * b + c]) / 2);
      let g = placed.get(gk);
      if (g === undefined) placed.set(gk, (g = groups++));
      G.push(g);
      const u = (U[2 * a] + U[2 * b]) / 2, w = (U[2 * a + 1] + U[2 * b + 1]) / 2;
      U.push(u, w); C.push(...cellOf(u, w));
      ends.push(a, b);
      return m;
    };
    const out = [];
    for (let t = 0; t < tri.length; t += 3) {
      const q = [tri[t], tri[t + 1], tri[t + 2]], m = [mid(q[0], q[1]), mid(q[1], q[2]), mid(q[2], q[0])];
      const n = (m[0] >= 0) + (m[1] >= 0) + (m[2] >= 0);
      if (n === 0) out.push(q[0], q[1], q[2]);
      else if (n === 3) out.push(q[0], m[0], m[2], m[0], q[1], m[1], m[2], m[1], q[2], m[0], m[1], m[2]);
      else {
        // One edge split: two triangles on it. Two: the corner between them cut off, and the rest in two.
        const k = n === 1 ? m.findIndex(x => x >= 0) : m.findIndex(x => x < 0);
        const a = q[k], b = q[(k + 1) % 3], c = q[(k + 2) % 3];
        if (n === 1) out.push(a, m[k], c, m[k], b, c);
        else { const mb = m[(k + 1) % 3], mc = m[(k + 2) % 3]; out.push(c, mc, mb, mc, a, b, mc, b, mb); }
      }
    }
    tri = out;
  }
  if (!ends.length) return null;
  const n = n0 + ends.length / 2, g = new THREE.BufferGeometry();
  g.name = `${src.name || 'skin'}~fine`;
  g.setIndex(new THREE.BufferAttribute(n > 65535 ? Uint32Array.from(tri) : Uint16Array.from(tri), 1));
  const { skinIndex, skinWeight } = src.attributes;
  for (const [name, a] of Object.entries(src.attributes)) {
    if (skinIndex && skinWeight && (a === skinIndex || a === skinWeight)) continue;
    g.setAttribute(name, grown(a, n0, ends, name === 'normal' || name === 'tangent'));
  }
  if (skinIndex && skinWeight) {
    const [i, w] = grownSkin(skinIndex, skinWeight, n0, ends);
    g.setAttribute('skinIndex', i); g.setAttribute('skinWeight', w);
  }
  for (const [name, list] of Object.entries(src.morphAttributes ?? {})) g.morphAttributes[name] = list.map(a => a && grown(a, n0, ends));
  g.morphTargetsRelative = src.morphTargetsRelative;
  // A middle lies between its ends: the source's bounds hold.
  g.boundingBox = src.boundingBox; g.boundingSphere = src.boundingSphere;
  g.userData = { ...src.userData, chiFine: { of: n0, added: ends.length / 2 } };
  return g;
}

const kept = new WeakMap();   // source geometry -> Map(key -> fine geometry or null)

/**
 * fineGeometry, once for each source and `key` (a person's sheet), freed when its source is.
 * A geometry that is already a fine one is handed back as it is.
 */
export function fineOf(src, key, opts) {
  if (!src || src.userData?.chiFine) return src ?? null;
  let own = kept.get(src);
  if (!own) {
    kept.set(src, (own = new Map()));
    src.addEventListener('dispose', () => { for (const g of own.values()) g?.dispose(); own.clear(); });
  }
  if (!own.has(key)) own.set(key, fineGeometry(src, opts));
  return own.get(key) ?? src;
}
