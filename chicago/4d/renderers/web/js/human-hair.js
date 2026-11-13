// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Strand-card hair, beards and moustaches for every portable human (T-3414).
 *
 * Kevin, 2026-11-06, of Hans: "he looks too smooth and not real". Since T-3400 the hair cap
 * catches a strand sheen, but it is still one smooth shell. This grows real-looking hair over
 * it at load, from each body's OWN scalp and face, in its bind pose in metres:
 *
 *  - Cards: narrow ribbons, rooted at random points over the hair cap (area-weighted, seeded
 *    by the person, so a person's hair is the same every load), combed by the person's cut
 *    (human-hair-styles.js) and laid over the cap a few millimetres off it, rising toward
 *    the tips. Beards, moustaches and whiskers are grown the same way from the face's skin.
 *  - Strands: a card carries no texture. Its shader cuts it into strands, each of its own
 *    length, tapering to a tip, so the edge of the hair breaks up; strands too fine for a
 *    pixel give way to their mean coverage, and coverage goes to a hashed alpha (no sorting).
 *  - Light: the cards take the cap's two Kajiya-Kay lobes (human-skin.js), along the card's
 *    own strand direction, and the scalp's normal, so the hair shades as one mass.
 *  - Skinning: each card is bound to the body's own skeleton with the weights of the cap or
 *    skin vertex nearest its root, so it moves with the head (and a beard with the jaw).
 *  - Hats: a headwear piece put on the body later (driver-livery.js) is found by name, and
 *    strands above its band are cut away, so no hair shows through a hat.
 *
 * Near levels only (LOD0, LOD1); further away the cap alone draws. One extra draw per near
 * figure. The cards are geometry made at load, no file and no texture, freed with the
 * geometry they were grown from. Every value is a reconstructed rendering choice (liberty
 * L418, its hair supplement); no likeness of anyone's hair is claimed.
 */
import * as THREE from 'three';
import { restMatrix, boneRest, STRAND_GLSL, chainPatch, HAIR, headFrame, lidEdges } from './human-skin.js';

export { headFrame };
import { HAIR_CUTS, FACIAL_HAIR, HAIR_COLOURS, hairFor } from './human-hair-styles.js';

/** How much hair a near level grows. */
export const CARDS = Object.freeze({
  lods: Object.freeze({
    0: Object.freeze({ scalp: 2400, segments: 5, width_mm: 8, facial: 1 }),
    1: Object.freeze({ scalp: 900, segments: 3, width_mm: 12, facial: .55 }),
    // T-3506: at the middle level, only a tied tail, where the person's cut has one: the cap
    // is the same short hair on every 1812 body there, and the tail is what tells them apart.
    2: Object.freeze({ scalp: 0, segments: 3, width_mm: 18, facial: 0, tail: 24, tail_only: true }),
  }),
  strands: 9,            // strands across one card
  cover: 2.6,            // card layers over any point of the cap
  shell_reach_m: .016,   // further than this from the cap, a strand hangs free
  cap_alpha_test: .25,   // the cap beneath the cards keeps its texture's faintest strands
  sheen: .5,            // the cap's strand lobes, scaled: cards lie in layers, the cap is one sheet
});

const KEY = 'chicago-strands-v1';
const NO_CLIP = 1e6;

/** A small seeded random of a string (FNV-1a into mulberry32). */
export function seeded(key) {
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

/** A mesh's vertices and triangles in its bind pose, in metres from `root`. */
export function metricSurface(mesh, root) {
  const g = mesh.geometry, p = g.attributes.position, n = g.attributes.normal;
  const R = restMatrix(mesh, root), Rn = new THREE.Matrix3().getNormalMatrix(R);
  const P = new Float32Array(p.count * 3), N = new Float32Array(p.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(R); P[3 * i] = v.x; P[3 * i + 1] = v.y; P[3 * i + 2] = v.z;
    if (n) v.fromBufferAttribute(n, i).applyMatrix3(Rn).normalize(); else v.set(0, 1, 0);
    N[3 * i] = v.x; N[3 * i + 1] = v.y; N[3 * i + 2] = v.z;
  }
  const index = g.index ? Array.from(g.index.array) : Array.from({ length: p.count }, (_, i) => i);
  return { mesh, R, P, N, index, count: p.count };
}

/** Nearest vertex, by a 2 cm grid. */
function grid(P, cell = .02) {
  const cells = new Map(), key = (x, y, z) => `${x},${y},${z}`;
  for (let i = 0; i < P.length / 3; i++) {
    const k = key(Math.floor(P[3 * i] / cell), Math.floor(P[3 * i + 1] / cell), Math.floor(P[3 * i + 2] / cell));
    if (!cells.has(k)) cells.set(k, []);
    cells.get(k).push(i);
  }
  return (x, y, z) => {
    const cx = Math.floor(x / cell), cy = Math.floor(y / cell), cz = Math.floor(z / cell);
    let best = -1, bd = Infinity;
    for (let r = 1; r <= 3 && best < 0; r++) {
      for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) for (let k = -r; k <= r; k++) {
        for (const vi of cells.get(key(cx + i, cy + j, cz + k)) ?? []) {
          const dx = P[3 * vi] - x, dy = P[3 * vi + 1] - y, dz = P[3 * vi + 2] - z, d = dx * dx + dy * dy + dz * dz;
          if (d < bd) { bd = d; best = vi; }
        }
      }
    }
    return best;
  };
}

/**
 * Where the cap's own texture is hair (its alpha, at 128 px), so no card roots on the bare
 * skin a masked cap's mesh also covers. Null where the picture cannot be read (no DOM).
 */
const masks = new WeakMap();
export function capMask(material) {
  const image = material?.map?.image;
  if (!image) return null;
  if (masks.has(image)) return masks.get(image);
  let mask = null;
  try {
    const S = 128;
    const canvas = typeof OffscreenCanvas === 'function' ? new OffscreenCanvas(S, S) : document.createElement('canvas');
    canvas.width = canvas.height = S;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(image, 0, 0, S, S);
    const a = ctx.getImageData(0, 0, S, S).data, flip = material.map.flipY;
    mask = (u, v) => {
      const x = Math.min(S - 1, Math.max(0, Math.floor(u * S))), y = Math.min(S - 1, Math.max(0, Math.floor((flip ? 1 - v : v) * S)));
      return a[4 * (y * S + x) + 3] / 255;
    };
  } catch { mask = null; }
  masks.set(image, mask);
  return mask;
}

/**
 * Where a cut with a bald crown (`cut.bald`, T-3440) keeps hair: below a line `side_cm` above
 * the eyes at the temples, rising to `back_cm` behind the head, and nothing forward of
 * `front_z_cm`. Centimetres in the face's frame. True everywhere for a cut with no `bald`.
 */
export function keepsHair(cut, f, p) {
  const b = cut?.bald;
  if (!b) return true;
  const l = p.clone().sub(f.o), y = l.dot(f.y) * 100, z = l.dot(f.z) * 100;
  if (z > b.front_z_cm) return false;
  const behind = Math.min(1, Math.max(0, (-z - 4) / 8));
  return y < b.side_cm + (b.back_cm - b.side_cm) * behind;
}

/** Area-weighted random points over the triangles `keep` lets through. */
function sampler(surface, keep, rand) {
  const { P, N, index } = surface, tris = [], cum = [];
  let total = 0;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  for (let t = 0; t < index.length; t += 3) {
    const i = index[t], j = index[t + 1], k = index[t + 2];
    a.fromArray(P, 3 * i); b.fromArray(P, 3 * j); c.fromArray(P, 3 * k);
    const nx = (N[3 * i] + N[3 * j] + N[3 * k]) / 3, ny = (N[3 * i + 1] + N[3 * j + 1] + N[3 * k + 1]) / 3, nz = (N[3 * i + 2] + N[3 * j + 2] + N[3 * k + 2]) / 3;
    const centre = a.clone().add(b).add(c).divideScalar(3);
    if (keep && !keep(centre, new THREE.Vector3(nx, ny, nz).normalize(), [i, j, k])) continue;
    const area = b.clone().sub(a).cross(c.clone().sub(a)).length() / 2;
    if (!(area > 0)) continue;
    total += area; tris.push([i, j, k]); cum.push(total);
  }
  return {
    area: total,
    draw() {
      if (!tris.length) return null;
      const r = rand() * total;
      let lo = 0, hi = cum.length - 1;
      while (lo < hi) { const m = (lo + hi) >> 1; if (cum[m] < r) lo = m + 1; else hi = m; }
      const [i, j, k] = tris[lo];
      let u = rand(), v = rand();
      if (u + v > 1) { u = 1 - u; v = 1 - v; }
      const w = 1 - u - v;
      const p = new THREE.Vector3(P[3 * i] * w + P[3 * j] * u + P[3 * k] * v, P[3 * i + 1] * w + P[3 * j + 1] * u + P[3 * k + 1] * v, P[3 * i + 2] * w + P[3 * j + 2] * u + P[3 * k + 2] * v);
      const n = new THREE.Vector3(N[3 * i] * w + N[3 * j] * u + N[3 * k] * v, N[3 * i + 1] * w + N[3 * j + 1] * u + N[3 * k + 1] * v, N[3 * i + 2] * w + N[3 * j + 2] * u + N[3 * k + 2] * v).normalize();
      return { p, n, vertex: w >= u && w >= v ? i : u >= v ? j : k };
    },
  };
}

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

/** The way a cut combs the hair at `p` (normal `n`), in the head's frame. Not yet on the tangent plane. */
function combed(cut, f, p, n) {
  const l = p.clone().sub(f.o), lx = l.dot(f.x);
  const top = smooth(.25, .75, n.dot(f.y));
  const down = f.y.clone().negate();
  if (cut.flow === 'side_part') {
    const part = cut.part_cm / 100;
    // On top: across from the part, the long side over the crown, and a little back.
    // At the front hairline it is combed back off the brow, never across it.
    const front = smooth(.2, .6, n.dot(f.z));
    const across = f.x.clone().multiplyScalar((lx >= part ? 1 : -1) * (1 - .75 * front));
    const onTop = across.addScaledVector(f.z, -(.55 + front)).normalize();
    // At the sides and back: down, and back off the brow and temples.
    const sides = down.clone().addScaledVector(f.z, -.45).normalize();
    return onTop.multiplyScalar(top).add(sides.multiplyScalar(1 - top));
  }
  if (cut.flow === 'centre_part_back') {
    // Parted in the middle and drawn smooth to either side, over the tops of the ears and
    // back to a knot behind the head (T-3423): toward the knot everywhere off the parting.
    const knot = f.o.clone().addScaledVector(f.y, cut.knot_cm.up / 100).addScaledVector(f.z, -cut.knot_cm.back / 100);
    const toKnot = knot.sub(p).normalize();
    const across = f.x.clone().multiplyScalar(lx >= 0 ? 1 : -1);
    const onTop = across.addScaledVector(f.z, -.35).normalize();
    return onTop.multiplyScalar(top).add(toKnot.multiplyScalar(1 - top)).normalize();
  }
  if (cut.flow === 'centre_part_down') {
    // T-3520: parted in the middle and worn loose: on top combed to either side of the parting,
    // over the ears and at the back falling straight down (a girl's hair to the neck or shoulders).
    const across = f.x.clone().multiplyScalar(lx >= 0 ? 1 : -1);
    const onTop = across.addScaledVector(f.z, -.25).normalize();
    const sides = down.clone().addScaledVector(f.z, -.12).addScaledVector(f.x, (lx >= 0 ? 1 : -1) * .08).normalize();
    return onTop.multiplyScalar(top).add(sides.multiplyScalar(1 - top)).normalize();
  }
  if (cut.flow === 'swept_back') {
    // T-3553: swept straight back off the brow with no parting, a little out to either side on
    // top, and down and back over the ears and at the nape (hair worn long to the collar).
    const onTop = f.z.clone().negate().addScaledVector(f.x, (lx >= 0 ? 1 : -1) * .18).normalize();
    const sides = down.clone().addScaledVector(f.z, -.55).addScaledVector(f.x, (lx >= 0 ? 1 : -1) * .1).normalize();
    return onTop.multiplyScalar(top).add(sides.multiplyScalar(1 - top)).normalize();
  }
  if (cut.flow === 'swept_up') {
    // Drawn up and back from the face all round to a knot high on the crown (the 1900s,
    // T-3423): every strand runs toward the knot, with no parting.
    const knot = f.o.clone().addScaledVector(f.y, cut.knot_cm.up / 100).addScaledVector(f.z, -cut.knot_cm.back / 100);
    return knot.sub(p).normalize();
  }
  // Brushed forward: out from a crown behind the top, toward the brow, and forward at the temples.
  const crown = f.o.clone().addScaledVector(f.y, .1).addScaledVector(f.z, -.075);
  const out = p.clone().sub(crown);
  out.addScaledVector(f.z, .06 + .05 * (1 - top));
  return out.normalize().addScaledVector(down, .35 * (1 - top)).normalize();
}

/** Lay one card: a ribbon from `root` along the comb, a few millimetres off the surface. */
function layCard(out, { start, n0, length, segments, width, lift, dir, surface, nearest, reach, rand, curl, weights, seed, layer, hang = false }) {
  const p = start.clone().addScaledVector(n0, lift.root), n = n0.clone();
  const step = length / segments, wob = (rand() - .5) * 2 * curl;
  const pts = [], nrm = [], tan = [];
  let d = dir(p, n);
  for (let s = 0; s <= segments; s++) {
    d.addScaledVector(n, -d.dot(n));
    if (d.lengthSq() < 1e-10) d.set(0, -1, 0).addScaledVector(n, -n.y);
    d.normalize();
    // The sheen runs along the comb itself, not each card's own wander, so neighbours shine together.
    const t = dir(p, n); t.addScaledVector(n, -t.dot(n));
    pts.push(p.clone()); nrm.push(n.clone()); tan.push(t.lengthSq() > 1e-10 ? t.normalize() : d.clone());
    if (s === segments) break;
    // Turn a little about the normal (a curl), then step and settle back over the surface.
    d.applyAxisAngle(n, wob * (1 + s * .3)).normalize();
    p.addScaledVector(d, step);
    const vi = nearest(p.x, p.y, p.z);
    if (vi >= 0) {
      const q = new THREE.Vector3().fromArray(surface.P, 3 * vi), nq = new THREE.Vector3().fromArray(surface.N, 3 * vi);
      const off = p.clone().sub(q), h = off.dot(nq), side = off.addScaledVector(nq, -h).length();
      const want = lift.root + (lift.tip - lift.root) * (s + 1) / segments;
      if (side < reach && (!surface.bare || !surface.bare[vi])) { p.addScaledVector(nq, want - h); n.copy(nq).lerp(n, .35).normalize(); }
      else if (hang) p.y -= step * .25;   // past the cap's edge: a long strand hangs,
      else p.addScaledVector(d, -step);   // a short one ends there
    }
    d = dir(p, n).lerp(d, .5);
  }
  const base = out.position.length / 3;
  for (let s = 0; s <= segments; s++) {
    const b = new THREE.Vector3().crossVectors(nrm[s], tan[s]).normalize();
    const w = width * (1 - .55 * s / segments) / 2;
    for (const side of [-1, 1]) {
      const v = pts[s].clone().addScaledVector(b, side * w);
      out.position.push(v.x, v.y, v.z);
      out.normal.push(nrm[s].x, nrm[s].y, nrm[s].z);
      out.strand.push(tan[s].x, tan[s].y, tan[s].z);
      out.card.push(side < 0 ? 0 : 1, s / segments, seed, layer);
      out.skinIndex.push(...weights.index); out.skinWeight.push(...weights.weight);
    }
    if (s < segments) {
      const i = base + 2 * s;
      out.index.push(i, i + 2, i + 1, i + 1, i + 2, i + 3);
    }
  }
}

/**
 * A lash card's layer (chiCard.w): below the 0..1 of every other card, so the strand shader's
 * `mix( 0.8, 1.1, layer )` draws it at under half the brows' tone, the two sharing one colour.
 */
const LASH_LAYER = -1.3;

/** For a point on a lid's inner margin, the foremost skin just above it (its front rim). */
function rimFinder(face, f) {
  const n = face.count, L = new Float32Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromArray(face.P, 3 * i).sub(f.o); L[3 * i] = v.dot(f.x); L[3 * i + 1] = v.dot(f.y); L[3 * i + 2] = v.dot(f.z); }
  return (p, fallback) => {
    v.copy(p).sub(f.o);
    const x = v.dot(f.x), y = v.dot(f.y);
    let best = fallback, bz = -Infinity;
    for (let i = 0; i < n; i++) {
      if (Math.abs(L[3 * i] - x) > .0025 || L[3 * i + 1] < y - .001 || L[3 * i + 1] > y + .0015) continue;
      if (L[3 * i + 2] > bz) { bz = L[3 * i + 2]; best = i; }
    }
    const q = new THREE.Vector3().fromArray(face.P, 3 * best);
    // Across the lid as the margin point is, at the rim's height and depth.
    const root = f.o.clone().addScaledVector(f.x, x).addScaledVector(f.y, q.clone().sub(f.o).dot(f.y)).addScaledVector(f.z, q.clone().sub(f.o).dot(f.z));
    return { root, vertex: best };
  };
}

/**
 * One lash (T-3493): a card that leaves the lid's edge forward and curls up, free of the skin.
 * Its width runs along the lid, so from the front it reads as the fine dark line of a lash.
 */
function layLash(out, { root, along, f, side, length, width, rise, splay, segments, weights, seed, layer }) {
  const base = out.position.length / 3;
  const across = f.x.clone().multiplyScalar(side);
  const p = root.clone();
  for (let s = 0; s <= segments; s++) {
    const u = s / segments;
    // From a little below level at the root to `rise` radians up at the tip.
    const th = -.15 + (rise + .15) * u;
    const t = f.z.clone().multiplyScalar(Math.cos(th)).addScaledVector(f.y, Math.sin(th)).addScaledVector(across, splay).normalize();
    const nrm = new THREE.Vector3().crossVectors(along, t).normalize();
    if (nrm.dot(f.z) < 0 && nrm.dot(f.y) < 0) nrm.negate();
    if (s) p.addScaledVector(t, length / segments);
    const w = width * (1 - .7 * u) / 2;
    for (const k of [-1, 1]) {
      const v = p.clone().addScaledVector(along, k * w);
      out.position.push(v.x, v.y, v.z);
      out.normal.push(nrm.x, nrm.y, nrm.z);
      out.strand.push(t.x, t.y, t.z);
      out.card.push(k < 0 ? 0 : 1, u, seed, layer);
      out.skinIndex.push(...weights.index); out.skinWeight.push(...weights.weight);
    }
    if (s < segments) { const i = base + 2 * s; out.index.push(i, i + 2, i + 1, i + 1, i + 2, i + 3); }
  }
}

function weightsOf(mesh, vi, toBones) {
  const j = mesh.geometry.attributes.skinIndex, w = mesh.geometry.attributes.skinWeight;
  const index = [0, 0, 0, 0], weight = [0, 0, 0, 0];
  if (!j || !w || vi < 0) return { index, weight: [1, 0, 0, 0] };
  for (let k = 0; k < 4; k++) { index[k] = toBones(j.getComponent(vi, k)); weight[k] = w.getComponent(vi, k); }
  const sum = weight.reduce((a, b) => a + b, 0) || 1;
  return { index, weight: weight.map(x => x / sum) };
}

/**
 * Grow one person's cards. Pure apart from three's maths: `hair` and `skin` are the body's
 * cap and skin meshes (skin may be null), `root` the cloned figure. Returns the geometry's
 * arrays, in the cap's bind pose in metres, and what was grown.
 */
export function growHair({ hair, skin = null, root, style, lod, seed = 'person' }) {
  const level = CARDS.lods[lod];
  const cut = HAIR_CUTS[style?.cut];
  if (!level || !cut || !hair) return null;
  if (level.tail_only && !(style.tail_cm > 0 && cut.knot_cm)) return null;   // T-3506: the middle level grows a tail or nothing
  const rand = seeded(`${seed}|${style.cut}|${lod}`);
  const scalp = metricSurface(hair, root);
  const f = headFrame(hair, root);
  if (!f) return null;
  const out = { position: [], normal: [], strand: [], card: [], skinIndex: [], skinWeight: [], index: [], cards: [], facialFrom: -1 };
  const grown = { scalp: 0, facial: {} };
  const nearScalp = grid(scalp.P);
  const mask = capMask(hair.material), uv = hair.geometry.attributes.uv;
  const onHair = mask && uv ? (c, n, tri) => {
    let u = 0, v = 0;
    for (const i of tri) { u += uv.getX(i) / 3; v += uv.getY(i) / 3; }
    return mask(u, v) > .5;
  } : null;
  const bald = cut.bald ? (c) => keepsHair(cut, f, c) : null;
  const area = sampler(scalp, bald ? (c, n, tri) => bald(c) && (!onHair || onHair(c, n, tri)) : onHair, rand);
  // Cap vertices over bare skin: a strand combed onto them ends there (a long one hangs).
  if (mask && uv) scalp.bare = Uint8Array.from({ length: scalp.count }, (_, i) => mask(uv.getX(i), uv.getY(i)) < .25 ? 1 : 0);
  // A bald crown (T-3440) is bare skin too: a strand combed up onto it ends there.
  if (bald) {
    scalp.bare ??= new Uint8Array(scalp.count);
    const q = new THREE.Vector3();
    for (let i = 0; i < scalp.count; i++) if (!bald(q.fromArray(scalp.P, 3 * i))) scalp.bare[i] = 1;
  }
  // Cards until they cover the cap `cover` times over (or the level's most): short cards at the
  // sides take more of them than the long ones on top.
  // A cut whose cap carries its own fine strands (a cleared bun hair, T-3434) grows none here.
  const want = cut.scalp_cards === false ? 0 : CARDS.cover * cut.density * area.area;
  let laid = 0;
  const same = i => i;
  for (let c = 0; c < level.scalp && laid < want; c++) {
    const s = area.draw();
    if (!s) break;
    const top = smooth(.25, .75, s.n.dot(f.y)), back = smooth(.2, .7, -s.n.dot(f.z)) * (1 - top);
    const side = Math.max(0, 1 - top - back);
    const len = Math.max(.006, (cut.lengths_cm.top * top + cut.lengths_cm.back * back + cut.lengths_cm.side * side) / 100 * (.8 + .35 * rand()));
    // A card is a stroke: never wider than about a third of its length.
    // A cut may ask for finer cards (`card_mm`, T-3440: an old man's thin, soft fringe).
    const width = Math.max(.002, Math.min((cut.card_mm ?? level.width_mm) / 1000, level.width_mm / 1000, len * .35)) * (.8 + .4 * rand());
    laid += len * width * .8;
    layCard(out, {
      start: s.p, n0: s.n, length: len, segments: Math.max(2, Math.min(level.segments, Math.round(len / .01) + 1)), width,
      lift: { root: cut.lift_mm.root / 1000 * (.6 + .8 * rand()), tip: cut.lift_mm.tip / 1000 * (.6 + .8 * rand()) },
      dir: (p, n) => combed(cut, f, p, n), surface: scalp, nearest: nearScalp, reach: CARDS.shell_reach_m, rand, curl: cut.curl, hang: !!cut.hang && s.n.dot(f.z) < .25,  // never down over the brow
      weights: weightsOf(hair, s.vertex, same), seed: rand(), layer: rand(),
    });
    grown.scalp++;
  }
  // T-3506: the tail or club below a tie, `style.tail_cm` long: a bundle of cards from the tie
  // behind the head, hanging free of the scalp, down and a little back. Bound as the tie's
  // nearest cap vertex, so it moves with the head.
  if (style.tail_cm > 0 && cut.knot_cm) {
    const knot = f.o.clone().addScaledVector(f.y, cut.knot_cm.up / 100).addScaledVector(f.z, -cut.knot_cm.back / 100);
    const vi = nearScalp(knot.x, knot.y, knot.z);
    if (vi >= 0) {
      // On the cap's surface behind the tie, a few millimetres out.
      knot.fromArray(scalp.P, 3 * vi).addScaledVector(new THREE.Vector3().fromArray(scalp.N, 3 * vi), .004);
      const weights = weightsOf(hair, vi, same), down = f.y.clone().negate().addScaledVector(f.z, -.16).normalize();
      const free = () => -1, count = level.tail ?? Math.round(level.scalp * .05), long = style.tail_cm / 100;
      for (let c = 0; c < count; c++) {
        const a = rand() * Math.PI * 2, r = .016 * Math.sqrt(rand());
        const start = knot.clone().addScaledVector(f.x, Math.cos(a) * r).addScaledVector(f.y, Math.sin(a) * r * .6);
        // Cards turned about the tail's own axis, so the bundle reads round from any side.
        const n0 = f.z.clone().negate().applyAxisAngle(down, (rand() - .5) * 2.4).normalize();
        const len = long * (.75 + .3 * rand()), width = Math.max(.002, level.width_mm / 1000 * (.6 + .3 * rand()));
        const lean = down.clone().addScaledVector(f.x, Math.cos(a) * .05);
        layCard(out, {
          start, n0, length: len, segments: Math.max(2, Math.min(level.segments, Math.round(len / .03) + 1)), width,
          lift: { root: 0, tip: 0 }, dir: () => lean.clone(), surface: scalp, nearest: free, reach: 0, rand, curl: .015,
          weights, seed: rand(), layer: rand(),
        });
      }
      grown.tail = count;
    }
  }
  // Beards, moustaches and whiskers, from the face's own skin.
  if (skin && style.facial?.length && !level.tail_only) {
    const face = metricSurface(skin, root), nearFace = grid(face.P, .01);
    const names = hair.skeleton.bones.map(b => b.name), skinBones = skin.skeleton.bones;
    const toBones = i => Math.max(0, names.indexOf(skinBones[i]?.name));
    out.facialFrom = out.position.length / 3;
    out.facialIndexFrom = out.index.length;
    out.faceR = face.R;
    for (const name of style.facial) {
      const piece = FACIAL_HAIR[name];
      if (!piece) continue;
      // Lashes on the upper lids' own edges (T-3493), free of the skin, rather than combed over it.
      if (piece.lid === 'upper') {
        const edges = lidEdges(face, f).filter(e => e.upper), total = edges.reduce((a, e) => a + e.length, 0);
        // The lid's edge in the skin is its inner margin, against the eyeball; the lid stands
        // a few millimetres thick in front of it. A lash roots at its front rim: the foremost
        // skin a little above the margin at that point.
        const rim = rimFinder(face, f);
        const want = Math.round(level.facial * piece.per_cm * total * 100);
        for (let c = 0; c < want && total > 0; c++) {
          let r = rand() * total, e = edges[0];
          for (const q of edges) { e = q; if ((r -= q.length) <= 0) break; }
          const t = rand(), { root, vertex: vi } = rim(e.pa.clone().lerp(e.pb, t), t < .5 ? e.a : e.b);
          const along = e.pb.clone().sub(e.pa).normalize();
          const at = Math.min(1, Math.max(0, e.across + (t - .5) * e.length * 100 / 2.4));
          // Longest a little outside the middle, short at the inner corner; swept out at the outer.
          const shape = .45 + .55 * Math.sin(Math.PI * Math.min(1, .15 + at * .95));
          const first = out.position.length / 3;
          layLash(out, { root, along, f, side: e.side, length: piece.length_cm / 100 * shape * (.8 + .4 * rand()),
            width: piece.width_mm / 1000 * (.8 + .4 * rand()), rise: piece.rise * (.8 + .4 * rand()), splay: piece.splay * (at - .25),
            segments: Math.max(2, level.segments - 2), weights: weightsOf(skin, vi, toBones), seed: rand(), layer: LASH_LAYER });
          out.cards.push({ first, last: out.position.length / 3, vertex: vi, root, lash: true });
          grown.facial[name] = (grown.facial[name] ?? 0) + 1;
        }
        continue;
      }
      const r = piece.region_cm;
      // T-3553: \`top\` ([[x, y], …] cm, x rising) is a line the piece's roots stay below, run
      // straight between its points: a beard's line up the cheek from the moustache's ends, or
      // the bare skin it leaves under the lower lip.
      const topAt = x => {
        const T = r.top;
        if (!T) return Infinity;
        if (x <= T[0][0]) return T[0][1];
        for (let k = 1; k < T.length; k++) if (x <= T[k][0]) return T[k - 1][1] + (T[k][1] - T[k - 1][1]) * (x - T[k - 1][0]) / (T[k][0] - T[k - 1][0]);
        return T[T.length - 1][1];
      };
      const keep = (c, n, _tri, m = 0) => {
        const l = c.clone().sub(f.o), x = Math.abs(l.dot(f.x)) * 100, y = l.dot(f.y) * 100, z = l.dot(f.z) * 100;
        if (x < r.x[0] - m || x > r.x[1] + m || z < r.z_min - m || z > (r.z_max ?? Infinity)) return false;
        // The band narrows toward its ends, and droops there by \`droop\` cm.
        const t = Math.min(1, Math.max(0, (x - r.x[0]) / (r.x[1] - r.x[0]))), mid = (r.y[0] + r.y[1]) / 2 - (r.droop ?? 0) * t * t;
        const half = (r.y[1] - r.y[0]) / 2 * Math.sqrt(Math.max(0, 1 - t * t * .75));
        if (Math.abs(y - mid) > half + m || y > topAt(x) + m) return false;
        return piece.facing === 'front' ? n.dot(f.z) > .35 : Math.abs(n.dot(f.x)) > .3 && n.dot(f.z) > -.3;
      };
      // An exact piece (T-3456) is kept point by point, not by whole triangles: a band a few
      // millimetres tall otherwise takes only the few skin triangles whose centres fall in it,
      // and its hairs bunch over those triangles in clumps with bare skin between.
      let region = sampler(face, piece.exact ? (c, n, tri) => keep(c, n, tri, .9) : keep, rand);
      if (piece.exact && region.area > 0) {
        const loose = region, trials = 600;
        let hit = 0;
        for (let k = 0; k < trials; k++) { const s = loose.draw(); if (s && keep(s.p, s.n)) hit++; }
        region = { area: loose.area * hit / trials, draw() { for (let k = 0; k < 400; k++) { const s = loose.draw(); if (s && keep(s.p, s.n)) return s; } return null; } };
      }
      const width = piece.width_mm / 1000, len = piece.length_cm / 100;
      const want = Math.round(level.facial * piece.cover * region.area / (width * len));
      // An even piece (T-3456, owner 2026-11-07: brows "super clumpy bunchy") spaces its roots
      // apart, a few tries each, so the hairs lie as a smooth band, not in random clumps.
      const spacing = piece.even ? piece.even * Math.sqrt(region.area / Math.max(1, want)) : 0, roots = [];
      for (let c = 0; c < want; c++) {
        let s = region.draw();
        for (let k = 0; spacing && s && k < 12 && roots.some(q => q.distanceToSquared(s.p) < spacing * spacing); k++) s = region.draw();
        if (!s) break;
        // T-3553: a feathered piece (`feather_cm`: its top, bottom and outer edges) thins and
        // shortens toward them, so a beard dies away up the cheek as stubble, not at a line.
        let edge = 1;
        if (piece.feather_cm) {
          const l = s.p.clone().sub(f.o), x = Math.abs(l.dot(f.x)) * 100, y = l.dot(f.y) * 100, fc = piece.feather_cm;
          const t = Math.min(1, Math.max(0, (x - r.x[0]) / (r.x[1] - r.x[0]))), mid = (r.y[0] + r.y[1]) / 2 - (r.droop ?? 0) * t * t;
          const half = (r.y[1] - r.y[0]) / 2 * Math.sqrt(Math.max(0, 1 - t * t * .75));
          edge = Math.max(0, Math.min(1, fc.top ? (Math.min(mid + half, topAt(x)) - y) / fc.top : 1, fc.bottom ? (y - mid + half) / fc.bottom : 1, fc.out ? (r.x[1] - x) / fc.out : 1));
          if (rand() > Math.pow(edge, 1.6)) continue;
        }
        if (spacing) roots.push(s.p);
        const across = s.p.clone().sub(f.o).dot(f.x);
        const out_ = f.x.clone().multiplyScalar(Math.sign(across) * piece.outward);
        // `fall_ends` turns the hairs along the band: a brow's rise up from the nose, its tail down.
        const t = Math.min(1, Math.max(0, (Math.abs(across) * 100 - r.x[0]) / (r.x[1] - r.x[0])));
        const fall = f.y.clone().multiplyScalar(-(piece.fall_ends ? piece.fall_ends[0] + (piece.fall_ends[1] - piece.fall_ends[0]) * t : piece.fall));
        const taper = piece.taper ? 1 - piece.taper * t : 1;
        const first = out.position.length / 3;
        // T-3553: `jitter_deg` turns each hair its own way about the skin's normal (a beard's
        // hairs do not all lie one way), `loft` stands some further off the skin (its volume),
        // and `grey` is the share of the hairs that have gone grey.
        const way = fall.clone().add(out_);
        if (piece.jitter_deg) way.applyAxisAngle(s.n, (rand() - .5) * 2 * piece.jitter_deg * Math.PI / 180);
        const loft = piece.loft ? 1 + piece.loft * rand() : 1, grey = piece.grey && rand() < piece.grey ? 2 : 0;
        layCard(out, {
          start: s.p, n0: s.n, length: len * taper * (.3 + .7 * edge) * (1 - (piece.spread ?? .3) / 2 + (piece.spread ?? .3) * rand()), segments: Math.max(2, level.segments - 2), width: width * (.8 + .4 * rand()),
          lift: { root: piece.lift_mm.root / 1000, tip: piece.lift_mm.tip / 1000 * loft }, dir: () => way.clone(),
          surface: face, nearest: nearFace, reach: .01, rand, curl: piece.curl ?? .12, weights: weightsOf(skin, s.vertex, toBones), seed: rand(), layer: grey + rand(),
        });
        out.cards.push({ first, last: out.position.length / 3, vertex: s.vertex, root: s.p });
        grown.facial[name] = (grown.facial[name] ?? 0) + 1;
      }
    }
  }
  // The face's own morphs (T-3493: "her eyelashes dont move"): each facial card moves with the
  // skin under its root (a blink, the jaw), and a lash's tip turns down as its lid shuts.
  const morph = skin && out.cards.length ? facialMorphs(out, skin, f, out.faceR) : null;
  // Where a bald cut's fringe grows (T-3440): the cap's triangles wholly on hair and below the
  // bald line, for the undercoat dressHair lays beneath the cards.
  let undercoat = null;
  if (bald) {
    undercoat = [];
    const q = new THREE.Vector3(), I = scalp.index;
    for (let t = 0; t < I.length; t += 3) {
      const tri = [I[t], I[t + 1], I[t + 2]];
      if (tri.some(i => scalp.bare?.[i])) continue;
      const c = q.set(0, 0, 0);
      for (const i of tri) c.add(new THREE.Vector3().fromArray(scalp.P, 3 * i));
      c.divideScalar(3);
      if (onHair && !onHair(c, null, tri)) continue;
      undercoat.push(...tri);
    }
  }
  return { ...out, grown, frame: f, scalp, undercoat, morph };
}

/**
 * Facial cards' morph targets (T-3493), named as the skin's: the delta of each card's root
 * vertex, in the cards' metric bind pose, for every vertex of the card; for a lash, also the
 * card mirrored about the level through its root, by how far that lid closes against the
 * furthest any lid edge does, so its tip points down when the eye is shut. Only targets that
 * move some card are kept, over the facial vertices only (the scalp's cards take none).
 */
function facialMorphs(out, skin, f, R) {
  const targets = skin.geometry.morphAttributes?.position, dict = skin.morphTargetDictionary;
  // glTF's targets are deltas (morphTargetsRelative); absolute targets are not read.
  if (!targets?.length || !dict || !skin.geometry.morphTargetsRelative) return null;
  const R3 = new THREE.Matrix3().setFromMatrix4(R);
  const from = out.facialFrom, count = out.position.length / 3 - from, d = new THREE.Vector3(), o = new THREE.Vector3();
  const kept = [];
  for (const [name, ti] of Object.entries(dict)) {
    const attr = targets[ti];
    if (!attr) continue;
    const delta = c => d.fromBufferAttribute(attr, c.vertex).applyMatrix3(R3);
    let most = 0;
    for (const c of out.cards) if (c.lash) most = Math.max(most, Math.abs(delta(c).dot(f.y)));
    const D = new Float32Array(count * 3);
    let moves = false;
    for (const c of out.cards) {
      const dv = delta(c).clone();
      if (dv.lengthSq() < 1e-12) continue;
      moves = true;
      const shut = c.lash && most > 0 && dv.dot(f.y) < 0 ? Math.min(1, -dv.dot(f.y) / most) : 0;
      for (let v = c.first; v < c.last; v++) {
        o.fromArray(out.position, 3 * v).sub(c.root);
        const m = dv.clone().addScaledVector(f.y, -2 * o.dot(f.y) * shut);
        D.set([m.x, m.y, m.z], 3 * (v - from));
      }
    }
    if (moves) kept.push({ name, D });
  }
  return kept.length ? { from, targets: kept } : null;
}

const STRAND_VERTEX_DECLARE = `
attribute vec3 chiStrandT;
attribute vec4 chiCard;
varying vec4 vChiCard;
varying vec3 vChiHairT;
`;
const STRAND_VERTEX = `
  vChiCard = chiCard;
  {
    vec3 tObj = chiStrandT;
    #ifdef USE_SKINNING
      tObj = ( skinMatrix * vec4( tObj, 0.0 ) ).xyz;
    #endif
    vChiHairT = ( modelViewMatrix * vec4( tObj, 0.0 ) ).xyz;
  }`;
const STRAND_DECLARE = `
uniform vec3 chiCards; // strands per card, opacity, hat band (bind-pose height, m)
varying vec4 vChiCard;
`;
// Cut the card into strands: each its own length, tapering to its tip; under a pixel, its mean.
const STRAND_COLOR = `
  {
    if ( vChiSkinP.y > chiCards.z ) discard;
    float s = vChiCard.x * chiCards.x;
    float id = floor( s );
    float h = chiSkinHash( vec3( id + 0.5, vChiCard.z * 97.0, 3.7 ) );
    float h2 = chiSkinHash( vec3( id + 11.5, vChiCard.z * 53.0, 1.3 ) );
    float tipAt = 1.0 - h * 0.45;
    float along = vChiCard.y / tipAt;
    float wave = ( chiSkinNoise( vec3( id * 1.7, vChiCard.y * 5.0, vChiCard.z * 31.0 ) ) - 0.5 ) * 0.7 * vChiCard.y;
    float f = abs( fract( s + wave ) - 0.5 ) * 2.0;
    // A solid core; the strands part toward the tip and the card's two edges.
    float edgeX = 1.0 - abs( vChiCard.x * 2.0 - 1.0 );
    // ...and at the root, so a card grows out of the skin or cap with no edge to it.
    float thin = smoothstep( 0.5, 1.0, along ) * ( 1.6 - edgeX ) + 1.0 - smoothstep( 0.0, 0.18, vChiCard.y );
    float w = clamp( 1.08 - thin * 0.8, 0.18, 1.08 );
    float rate = fwidth( s );
    float aa = clamp( rate * 1.5, 0.04, 1.0 );
    float cov = ( 1.0 - smoothstep( w - aa, w + aa, f ) ) * ( 1.0 - smoothstep( 0.97, 1.0, along ) );
    float mean = clamp( w, 0.0, 1.0 ) * ( 1.0 - smoothstep( 0.7, 1.0, along ) );
    cov = mix( cov, mean, smoothstep( 0.5, 1.5, rate ) );
    diffuseColor.a *= cov * chiCards.y;
    // Darker at the roots and in the lower layers, lighter strand to strand.
    float root = mix( 0.5, 1.0, smoothstep( 0.0, 0.55, vChiCard.y ) );
    float streak = chiSkinNoise( vec3( s * 1.3, vChiCard.y * 3.0, vChiCard.z * 17.0 ) );
    // A layer of 2 or more (T-3553) is a grey hair: the same card, its colour gone to grey.
    float greyHair = step( 1.5, vChiCard.w );
    diffuseColor.rgb *= ( 0.8 + 0.3 * h2 + 0.25 * streak ) * root * mix( 0.8, 1.1, vChiCard.w - 2.0 * greyHair );
    diffuseColor.rgb = mix( diffuseColor.rgb, vec3( 1.0, 0.93, 0.84 ) * ( dot( diffuseColor.rgb, vec3( 0.3, 0.59, 0.11 ) ) * 1.7 + 0.03 ), greyHair * 0.75 );
  }`;
// A card is lit as the scalp under it: both faces take its outward normal.
const STRAND_NORMAL = `
  normal = normalize( normal * faceDirection );`;

const materials = new Map();
function strandMaterial(colour, personKey) {
  const key = `${personKey}|${colour.join(',')}`;
  if (materials.has(key)) return materials.get(key);
  const m = new THREE.MeshStandardMaterial({ name: 'hair_cards', color: new THREE.Color().setRGB(...colour, THREE.LinearSRGBColorSpace),
    roughness: .62, metalness: 0, side: THREE.DoubleSide, alphaTest: .5, alphaToCoverage: false });
  const G = STRAND_GLSL;
  const uniforms = {
    chiSkinRest: { value: new THREE.Matrix4() },
    chiHair: { value: new THREE.Vector4(HAIR.primary * CARDS.sheen, HAIR.secondary * CARDS.sheen, HAIR.shift, HAIR.roughness_floor) },
    chiCards: { value: new THREE.Vector3(CARDS.strands, 1, NO_CLIP) },
  };
  chainPatch(m, KEY, uniforms, shader => {
    shader.vertexShader = G.VERTEX_DECLARE + STRAND_VERTEX_DECLARE + shader.vertexShader
      .replace('#include <begin_vertex>', `#include <begin_vertex>${G.VERTEX}${STRAND_VERTEX}`);
    shader.fragmentShader = G.HAIR_DECLARE + STRAND_DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${STRAND_COLOR}${G.HAIR_COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${G.HAIR_ROUGHNESS}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>${STRAND_NORMAL}${G.HAIR_NORMAL}`)
      .replace(G.PHYSICAL, `${G.PHYSICAL}${G.HAIR_LIGHT}`);
  });
  m.userData.chiCards = uniforms.chiCards;
  materials.set(key, m);
  return m;
}

/**
 * The height (the cap's bind pose, metres from the root) of the lowest part of a hat that
 * sits on this head. The hat is skinned with its own inverse binds (driver-livery.js), so its
 * vertices are carried into the cap's bind pose through the head bone both share.
 */
function hatBand(hat, hair, root, frame) {
  const hi = hat.skeleton?.bones.findIndex(b => b.name === 'head') ?? -1, bi = hair.skeleton.bones.findIndex(b => b.name === 'head');
  const p = hat.geometry?.attributes?.position;
  if (hi < 0 || bi < 0 || !p) return NO_CLIP;
  root.updateMatrixWorld(true);
  const s = hair.skeleton;
  const M = new THREE.Matrix4().copy(root.matrixWorld).invert().multiply(s.bones[0].matrixWorld).multiply(s.boneInverses[0])
    .multiply(s.boneInverses[bi].clone().invert()).multiply(hat.skeleton.boneInverses[hi]).multiply(hat.bindMatrix);
  const v = new THREE.Vector3(), cz = (frame.head.z + frame.o.z) / 2;
  let low = Infinity;
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(M);
    const dx = v.x - frame.head.x, dz = v.z - cz;
    if (dx * dx + dz * dz < .11 * .11) low = Math.min(low, v.y);
  }
  return Number.isFinite(low) ? low : NO_CLIP;
}

// The hair_bun cap's texture: where clean hair lies (uv centre) and how much of it a radian
// round the head takes (T-3553, the place a bun turned to the crown left behind).
const BUN_PATCH_UV = Object.freeze({ u: .74, v: .29, span: .09 });
const turnedBuns = new WeakMap();

/** A geometry of `src`'s triangles `tris` (indices into src) alone; `from` maps its points back to src's. */
function sub(src, tris) {
  const from = [...new Set(tris)], at = new Map(from.map((i, k) => [i, k]));
  const geometry = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(src.attributes)) {
    const out = new attr.array.constructor(from.length * attr.itemSize);
    from.forEach((i, k) => { for (let c = 0; c < attr.itemSize; c++) out[k * attr.itemSize + c] = attr.array[i * attr.itemSize + c]; });
    geometry.setAttribute(name, new THREE.BufferAttribute(out, attr.itemSize, attr.normalized));
  }
  geometry.setIndex(tris.map(i => at.get(i)));
  return { geometry, from };
}   // source cap geometry -> Map(degrees -> { cap, knot })

/**
 * T-3553: wear the hair cap's own bun high on the crown, where a portrait shows a top knot.
 * The bun is the cap beyond 11 cm from the middle of the head (the skull's own hair lies inside
 * that). Its triangles are copied whole into a knot of their own, turned rigidly by `deg` about
 * the face's x axis through the middle of the head, up over the back to the crown; in the cap's
 * copy the bun's points are laid down on the skull, so no second knot stays behind. Both copies
 * share the cap's skeleton, material and texture, and are shared by every figure wearing that
 * cap and turn.
 */
function bunToCrown(root, deg, knot = 1) {
  const caps = [];
  root.traverse(o => { if (o.isSkinnedMesh && /^hair($|__)/.test(o.material?.name ?? '')) caps.push(o); });
  for (const o of caps) {
    const src = o.geometry;
    let byDeg = turnedBuns.get(src);
    if (!byDeg) { byDeg = new Map(); turnedBuns.set(src, byDeg); }
    let made = byDeg.get(`${deg}/${knot}`);
    if (!made) {
      const f = headFrame(o, root);
      if (!f) continue;
      const R = restMatrix(o, root), Ri = R.clone().invert(), Rn = new THREE.Matrix3().getNormalMatrix(R), Rni = new THREE.Matrix3().getNormalMatrix(Ri);
      const mid = f.o.clone().addScaledVector(f.y, .03).addScaledVector(f.z, -.085);
      const p = src.attributes.position, v = new THREE.Vector3();
      // The bun is the hair within 38 degrees of its own axis, seen from the middle of the head
      // (the axis runs to the middle of the hair standing more than 8.5 cm out behind): its
      // coil and the foot it is pinned to the skull by. The cap has no hair of its own under
      // it. The scalp is the skin's points round the head.
      let skin = null;
      root.traverse(m => { if (!skin && m.isSkinnedMesh && /^skin($|__)/.test(m.material?.name ?? '')) skin = m; });
      if (!skin) continue;
      const Rs = restMatrix(skin, root), sp = skin.geometry.attributes.position, scalp = [];
      for (let i = 0; i < sp.count; i++) {
        v.fromBufferAttribute(sp, i).applyMatrix4(Rs);
        if (v.distanceTo(mid) < .13 && v.clone().sub(mid).dot(f.y) > -.07) scalp.push(v.x, v.y, v.z);
      }
      const near = new Int32Array(p.count), inBun = new Uint8Array(p.count);
      const axis = new THREE.Vector3();
      for (let i = 0; i < p.count; i++) {
        const d = v.fromBufferAttribute(p, i).applyMatrix4(R).sub(mid);
        if (d.length() > .085 && d.dot(f.z) < -.035) axis.add(d);
      }
      if (!axis.lengthSq()) { byDeg.set(`${deg}/${knot}`, null); continue; }
      axis.normalize();
      const cone = Math.cos(38 * Math.PI / 180);
      for (let i = 0; i < p.count; i++) {
        const d = v.fromBufferAttribute(p, i).applyMatrix4(R).sub(mid);
        inBun[i] = d.dot(axis) > cone * d.length() ? 1 : 0;
        if (!inBun[i]) continue;
        d.add(mid);
        let best = Infinity;
        for (let k = 0; k < scalp.length; k += 3) {
          const dx = scalp[k] - d.x, dy = scalp[k + 1] - d.y, dz = scalp[k + 2] - d.z, d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < best) { best = d2; near[i] = k; }
        }
      }
      const I = src.index ? src.index.array : Uint32Array.from({ length: p.count }, (_, i) => i);
      const tris = [];
      for (let t = 0; t < I.length; t += 3) if (inBun[I[t]] && inBun[I[t + 1]] && inBun[I[t + 2]]) tris.push(I[t], I[t + 1], I[t + 2]);
      if (!tris.length) { byDeg.set(`${deg}/${knot}`, null); continue; }
      const q = new THREE.Quaternion().setFromAxisAngle(f.x, deg * Math.PI / 180);
      // The bun's own middle; the knot is drawn smaller than the low bun, and sits that much
      // nearer the skull.
      const c = new THREE.Vector3(); let nc = 0;
      for (let i = 0; i < p.count; i++) if (inBun[i]) { c.add(v.fromBufferAttribute(p, i).applyMatrix4(R)); nc++; }
      c.multiplyScalar(1 / nc);
      const toC = c.clone().sub(mid), scale = knot ?? 1, inward = 1 - (1 - scale) * .45;
      // The knot: the bun's triangles, turned whole.
      const geo = sub(src, tris).geometry;
      const kp = geo.attributes.position, kn = geo.attributes.normal;
      for (let k = 0; k < kp.count; k++) {
        v.fromBufferAttribute(kp, k).applyMatrix4(R).sub(c).multiplyScalar(scale).addScaledVector(toC, inward).applyQuaternion(q).add(mid).applyMatrix4(Ri);
        kp.setXYZ(k, v.x, v.y, v.z);
        if (kn) { v.fromBufferAttribute(kn, k).applyMatrix3(Rn).applyQuaternion(q).applyMatrix3(Rni).normalize(); kn.setXYZ(k, v.x, v.y, v.z); }
      }
      geo.computeBoundingSphere();
      // Where the bun stood, out to 50 degrees from its axis, the cap's texture is dark with the
      // hair running into the bun's foot. The cap leaves those triangles out; a patch of its own
      // takes them, the bun's points laid down on the scalp 7 mm off its nearest point, worn as
      // plain hair drawn up to the knot: a piece of the cap's texture (BUN_PATCH_UV, clean hair
      // on the cap's right half) laid flat across the back of the head.
      const wide = Math.cos(50 * Math.PI / 180), side = f.x, upward = axis.clone().cross(f.x).normalize();
      if (upward.dot(f.y) < 0) upward.negate();
      const inPatch = new Uint8Array(p.count);
      for (let i = 0; i < p.count; i++) { const d = v.fromBufferAttribute(p, i).applyMatrix4(R).sub(mid); inPatch[i] = d.dot(axis) > wide * d.length() ? 1 : 0; }
      const capTris = [], patchTris = [];
      for (let t = 0; t < I.length; t += 3) (inPatch[I[t]] || inPatch[I[t + 1]] || inPatch[I[t + 2]] ? patchTris : capTris).push(I[t], I[t + 1], I[t + 2]);
      const cap = src.clone();
      cap.setIndex(capTris);
      const patch = sub(src, patchTris), pp = patch.geometry.attributes.position, pu = patch.geometry.attributes.uv, pn = patch.geometry.attributes.normal, s = new THREE.Vector3();
      patch.from.forEach((i, k) => {
        const d = v.fromBufferAttribute(p, i).applyMatrix4(R).sub(mid).normalize();
        if (pu) pu.setXY(k, BUN_PATCH_UV.u + d.dot(side) * BUN_PATCH_UV.span, BUN_PATCH_UV.v - d.dot(upward) * BUN_PATCH_UV.span);
        if (!inBun[i]) return;
        s.fromArray(scalp, near[i]);
        v.copy(s).sub(mid).setLength(.007).add(s).applyMatrix4(Ri);
        pp.setXYZ(k, v.x, v.y, v.z);
        if (pn) { v.copy(s).sub(mid).applyMatrix3(Rni).normalize(); pn.setXYZ(k, v.x, v.y, v.z); }
      });
      // Every laid-down triangle faces out (a bun's inner coil, laid flat, would show its back,
      // and a double-sided back face is lit dark).
      const pi = patch.geometry.index.array, A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
      for (let t = 0; t < pi.length; t += 3) {
        A.fromBufferAttribute(pp, pi[t]).applyMatrix4(R); B.fromBufferAttribute(pp, pi[t + 1]).applyMatrix4(R); C.fromBufferAttribute(pp, pi[t + 2]).applyMatrix4(R);
        const out = A.clone().add(B).add(C).multiplyScalar(1 / 3).sub(mid);
        if (B.sub(A).cross(C.sub(A)).dot(out) < 0) { const x = pi[t + 1]; pi[t + 1] = pi[t + 2]; pi[t + 2] = x; }
      }
      patch.geometry.computeBoundingSphere();
      cap.computeBoundingSphere();
      made = { cap, knot: geo, patch: patch.geometry };
      byDeg.set(`${deg}/${knot}`, made);
    }
    if (!made) continue;
    o.geometry = made.cap;
    for (const [g, name] of [[made.knot, 'top_knot'], [made.patch, 'bun_patch']]) {
      const k = new THREE.SkinnedMesh(g, o.material);
      k.name = `${o.name}_${name}`;
      k.bind(o.skeleton, o.bindMatrix);
      k.frustumCulled = o.frustumCulled;
      o.parent.add(k);
    }
  }
}

const built = new WeakMap();   // source geometry -> Map(person key -> geometry)

/**
 * Give one cloned figure its strand cards. Call after the body is cloned (and varied).
 * `person` keys the seed and the material; `year` picks an era default; `style` overrides both (tests).
 * Returns { mesh, grown } or null where nothing is grown (a far level, no cap, no style).
 */
export function dressHair(root, { lod = 0, person = null, year = null, style: given = null } = {}) {
  if (!root) return null;
  const style = given ?? hairFor(person, year);
  if (!style) return null;
  // A bald crown (T-3440): the cap, a full head of hair in its own texture, is never drawn;
  // the fringe is cards over the skin (near levels), and far off the head reads bare.
  if (HAIR_CUTS[style.cut]?.bald) root.traverse(o => { if (o.isMesh && /^hair($|__)/.test(o.material?.name ?? '')) o.visible = false; });
  // T-3553: a cut that wears the cap's own bun high on the crown (`bun_to_crown_deg`, Sarah
  // Grey's top knot) turns the bun up over the back of the head, at every level.
  if (HAIR_CUTS[style.cut]?.bun_to_crown_deg) bunToCrown(root, HAIR_CUTS[style.cut].bun_to_crown_deg, HAIR_CUTS[style.cut].bun_knot_scale ?? 1);
  if (!CARDS.lods[lod] || (CARDS.lods[lod].tail_only && !(style.tail_cm > 0 && HAIR_CUTS[style.cut]?.knot_cm))) return null;
  let hair = null, skin = null;
  root.traverse(o => {
    if (!o.isSkinnedMesh) return;
    // The scalp cap is the largest hair mesh: a bun or other worn-up piece shares its
    // material and is never the surface strands grow from (T-3423).
    if (/^hair($|__)/.test(o.material?.name ?? '')) {
      if (!hair || o.geometry.attributes.position.count > hair.geometry.attributes.position.count) hair = o;
    }
    else if (/^skin($|__)/.test(o.material?.name ?? '')) skin ??= o;
  });
  if (!hair?.skeleton || !hair.parent) return null;
  const key = `${person ?? 'anon'}|${lod}|${style.cut}|${(style.facial ?? []).join('+')}|${style.tail_cm ?? 0}`;
  let cache = built.get(hair.geometry);
  if (!cache) {
    cache = new Map();
    built.set(hair.geometry, cache);
    hair.geometry.addEventListener('dispose', () => { for (const g of cache.values()) { g.geometry?.dispose(); g.face?.dispose(); } cache.clear(); });
  }
  let entry = cache.get(key);
  if (!entry) {
    const grown = growHair({ hair, skin: skin?.skeleton ? skin : null, root, style, lod, seed: person ?? 'anon' });
    if (!grown || !grown.index.length) return null;
    // The face's cards are their own mesh (T-3493) where they move with the face's morphs or
    // take a colour of their own: the scalp's cards then carry no morph data.
    const N = grown.position.length / 3, split = grown.facialFrom >= 0 && !!(grown.morph || style.brow_colour);
    const part = (from, to, i0, i1, morph) => {
      if (i1 <= i0) return null;
      const g = new THREE.BufferGeometry(), at = (a, k) => a.slice(from * k, to * k);
      g.setAttribute('position', new THREE.Float32BufferAttribute(at(grown.position, 3), 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(at(grown.normal, 3), 3));
      g.setAttribute('chiStrandT', new THREE.Float32BufferAttribute(at(grown.strand, 3), 3));
      g.setAttribute('chiCard', new THREE.Float32BufferAttribute(at(grown.card, 4), 4));
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(at(grown.skinIndex, 4), 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(at(grown.skinWeight, 4), 4));
      g.setIndex(grown.index.slice(i0, i1).map(i => i - from));
      if (morph) {
        g.morphAttributes.position = morph.targets.map(t => Object.assign(new THREE.Float32BufferAttribute(t.D, 3), { name: t.name }));
        g.morphTargetsRelative = true;
      }
      return g;
    };
    const geometry = split ? part(0, grown.facialFrom, 0, grown.facialIndexFrom, null) : part(0, N, 0, grown.index.length, null);
    const face = split ? part(grown.facialFrom, N, grown.facialIndexFrom, grown.index.length, grown.morph) : null;
    entry = { geometry, face, grown: grown.grown, frame: grown.frame, R: grown.scalp.R };
    // A bald crown's undercoat (T-3440): the cap's own triangles where the fringe grows, in the
    // hair's colour, so the fringe reads as one band of hair rather than flakes over skin.
    if (grown.undercoat?.length) {
      const u = new THREE.BufferGeometry(), src = hair.geometry.attributes;
      for (const name of ['position', 'normal', 'skinIndex', 'skinWeight']) if (src[name]) u.setAttribute(name, src[name]);
      u.setIndex(grown.undercoat);
      entry.undercoat = u;
    }
    cache.set(key, entry);
  }
  if (entry.undercoat) {
    const c = HAIR_COLOURS[style.colour] ?? HAIR_COLOURS.dark_brown;
    const under = new THREE.SkinnedMesh(entry.undercoat, new THREE.MeshStandardMaterial({ name: 'hair_undercoat',
      color: new THREE.Color().setRGB(c[0] * .62, c[1] * .6, c[2] * .58, THREE.LinearSRGBColorSpace), roughness: .85, metalness: 0 }));
    under.name = 'hair_undercoat';
    under.frustumCulled = false;
    under.receiveShadow = hair.receiveShadow;
    under.bind(hair.skeleton, hair.bindMatrix);
    hair.parent.add(under);
  }
  const colour = HAIR_COLOURS[style.colour] ?? HAIR_COLOURS.dark_brown;
  const bind = hair.bindMatrix.clone().multiply(entry.R.clone().invert());
  const cards = (geometry, material, name) => {
    const m = new THREE.SkinnedMesh(geometry, material);
    m.name = name;
    m.frustumCulled = false;
    m.castShadow = false;
    m.receiveShadow = hair.receiveShadow;
    // The cards are in metres; the cap's bind matrix takes its own (quantised) positions.
    // Bound through the cap's rest matrix, they skin exactly as the cap does.
    m.bind(hair.skeleton, bind);
    hair.parent.add(m);
    return m;
  };
  const material = strandMaterial(colour, person ?? 'anon');
  const mesh = entry.geometry ? cards(entry.geometry, material, 'hair_cards') : null;
  // Brows and lashes (T-3493) may take a colour of their own, nearer a cap's own texture.
  const faceMaterial = entry.face ? strandMaterial(HAIR_COLOURS[style.brow_colour] ?? colour, person ?? 'anon') : null;
  const face = entry.face ? cards(entry.face, faceMaterial, 'hair_cards_face') : null;
  // Under the cards the cap is the scalp's colour: solid, not its own masked strands, so no
  // skin shows between the cards. (The far levels keep the cap as it was, alone.)
  if (entry.grown.scalp && hair.material?.alphaTest > CARDS.cap_alpha_test) hair.material.alphaTest = CARDS.cap_alpha_test;
  // T-3553: a cut over a body whose cap is darker than its own hair (`cap_tint`: William Grey's
  // sandy hair on the gentleman's dark cap; Sarah's greying light brown, worn as the cap itself)
  // lightens the cap toward the hair's colour (a number: that many times the colour; three numbers:
  // the cap's own texture multiplied by them), so no dark cap shows between the cards. Its own material, so the body's other wearers keep theirs.
  const tint = HAIR_CUTS[style.cut]?.cap_tint;
  if (tint && (entry.grown.scalp || HAIR_CUTS[style.cut].scalp_cards === false) && hair.material && !hair.userData.capTinted) {
    // The cap's own top knot and the patch a turned bun leaves (bunToCrown) share its material.
    const was = hair.material, tinted = was.clone();
    tinted.color.setRGB(...(Array.isArray(tint) ? tint : colour.map(c => c * tint)), THREE.LinearSRGBColorSpace);
    hair.parent.traverse(o => { if (o.isMesh && o.material === was) o.material = tinted; });
    hair.userData.capTinted = true;
  }
  // A hat put on later (driver-livery.js) cuts the strands above its band.
  let frame = 0, seen = null;
  const watch = mesh ?? face;
  watch.onBeforeRender = () => {
    if (frame++ % 30) return;
    // Only a hat that is worn: one left off (a bareheaded still, T-3440) cuts nothing.
    const hat = watch.parent?.children.find(o => o.isSkinnedMesh && o.visible && /^headwear/.test(o.material?.name ?? '') && !/band/.test(o.material.name)) ?? null;
    if (hat === seen) return;
    seen = hat;
    const z = hat ? hatBand(hat, hair, root, entry.frame) : NO_CLIP;
    material.userData.chiCards.value.z = z;
    if (faceMaterial) faceMaterial.userData.chiCards.value.z = z;
  };
  return { mesh: mesh ?? face, face, grown: entry.grown, style };
}

const cloths = new WeakMap();   // cap geometry -> Map(person -> { geometry, R })

/**
 * T-3506: a handkerchief tied round the head (a minority of the 1812 Potawatomi men and a few
 * women; the full cloth turbans of the 1830s portraits are later): a band of cloth from the
 * brow up over the crown's edge, laid a few millimetres out from this body's own cap and
 * forehead, rolled in at its top. Rigid on the head bone. Built at every level, so it reads
 * far off; geometry made at load, freed with the cap it was laid on. `rgb` is linear.
 */
export function dressHeadcloth(root, rgb, { person = null } = {}) {
  if (!root || !Array.isArray(rgb)) return null;
  let hair = null, skin = null;
  root.traverse(o => {
    if (!o.isSkinnedMesh) return;
    if (/^hair($|__)/.test(o.material?.name ?? '')) {
      if (!hair || o.geometry.attributes.position.count > hair.geometry.attributes.position.count) hair = o;
    } else if (/^skin($|__)/.test(o.material?.name ?? '')) skin ??= o;
  });
  if (!hair?.skeleton || !hair.parent) return null;
  const headBone = hair.skeleton.bones.findIndex(b => b.name === 'head');
  if (headBone < 0) return null;
  let cache = cloths.get(hair.geometry);
  if (!cache) {
    cache = new Map();
    cloths.set(hair.geometry, cache);
    hair.geometry.addEventListener('dispose', () => { for (const e of cache.values()) e.geometry.dispose(); cache.clear(); });
  }
  const key = person ?? 'anon';
  let entry = cache.get(key);
  if (!entry) {
    const f = headFrame(hair, root);
    if (!f) return null;
    const cap = metricSurface(hair, root);
    // The head's points: the cap, and the forehead's skin where the band crosses the brow.
    const pts = [];
    const take = (P, near) => {
      for (let i = 0; i < P.length / 3; i++) {
        const v = new THREE.Vector3(P[3 * i], P[3 * i + 1], P[3 * i + 2]).sub(f.o);
        const x = v.dot(f.x), y = v.dot(f.y), z = v.dot(f.z);
        if (y < .005 || y > .14 || Math.hypot(x, z + .08) > near) continue;
        pts.push([x, y, z]);
      }
    };
    take(cap.P, .16);
    if (skin) {
      const face = metricSurface(skin, root);
      // Body skin is the whole figure: the height and reach above keep only the head's.
      take(face.P, .13);
    }
    if (pts.length < 30) return null;
    const cz = -.08, SEG = 28;
    // The head's radius at a height and a bearing about its centre, from the points near both.
    const radius = (y, th) => {
      let r = 0;
      for (const [x, py, z] of pts) {
        if (Math.abs(py - y) > .012) continue;
        const a = Math.atan2(x, z - cz);
        let da = Math.abs(a - th); if (da > Math.PI) da = 2 * Math.PI - da;
        if (da > Math.PI / SEG * 1.6) continue;
        r = Math.max(r, Math.hypot(x, z - cz));
      }
      return r;
    };
    // Rings from the brow up: out from the head, and at the top rolled in over the hair.
    const rings = [[.024, 1, .006], [.045, 1, .008], [.07, 1, .009], [.09, .93, .008], [.102, .78, .004]];
    const position = [], index = [];
    const base = rings.map(([y]) => Array.from({ length: SEG }, (_, k) => radius(y, -Math.PI + 2 * Math.PI * k / SEG)));
    // A bearing the points miss takes its neighbours' radius.
    for (const row of base) for (let k = 0; k < SEG; k++) if (!row[k]) row[k] = Math.max(row[(k + SEG - 1) % SEG], row[(k + 1) % SEG], .07);
    rings.forEach(([y, inset, out], j) => {
      for (let k = 0; k < SEG; k++) {
        const th = -Math.PI + 2 * Math.PI * k / SEG, r = base[Math.min(j, 3)][k] * inset + out;
        const p = f.o.clone().addScaledVector(f.y, y).addScaledVector(f.x, Math.sin(th) * r).addScaledVector(f.z, cz + Math.cos(th) * r);
        position.push(p.x, p.y, p.z);
      }
    });
    for (let j = 0; j + 1 < rings.length; j++) for (let k = 0; k < SEG; k++) {
      const a = j * SEG + k, b = j * SEG + (k + 1) % SEG, c = a + SEG, d = b + SEG;
      index.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(position, 3));
    const n = position.length / 3;
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(n).fill(0).flatMap(() => [headBone, 0, 0, 0]), 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(new Array(n).fill(0).flatMap(() => [1, 0, 0, 0]), 4));
    g.setIndex(index);
    g.computeVertexNormals();
    entry = { geometry: g, R: cap.R };
    cache.set(key, entry);
  }
  const material = new THREE.MeshStandardMaterial({ name: 'cloth__headcloth_1812', color: new THREE.Color().setRGB(...rgb, THREE.LinearSRGBColorSpace),
    roughness: .88, metalness: 0, side: THREE.DoubleSide });
  const m = new THREE.SkinnedMesh(entry.geometry, material);
  m.name = 'headcloth';
  m.frustumCulled = false;
  m.castShadow = hair.castShadow;
  m.receiveShadow = hair.receiveShadow;
  m.bind(hair.skeleton, hair.bindMatrix.clone().multiply(entry.R.clone().invert()));
  hair.parent.add(m);
  return { mesh: m, material };
}
