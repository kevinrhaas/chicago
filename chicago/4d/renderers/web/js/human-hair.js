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
import { restMatrix, boneRest, STRAND_GLSL, chainPatch, HAIR } from './human-skin.js';
import { HAIR_CUTS, FACIAL_HAIR, HAIR_COLOURS, hairFor } from './human-hair-styles.js';

/** How much hair a near level grows. */
export const CARDS = Object.freeze({
  lods: Object.freeze({
    0: Object.freeze({ scalp: 2400, segments: 5, width_mm: 8, facial: 1 }),
    1: Object.freeze({ scalp: 900, segments: 3, width_mm: 12, facial: .55 }),
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

/** The face's frame in metres: origin between the eyes, x to the body's left, y up, z forward. */
export function headFrame(mesh, root) {
  const bones = mesh.skeleton?.bones ?? [];
  const at = name => { const i = bones.findIndex(b => b.name === name); return i < 0 ? null : boneRest(mesh, root, i); };
  const head = at('head'), l = at('eye_l'), r = at('eye_r');
  if (!head || !l || !r) return null;
  const o = l.clone().add(r).multiplyScalar(.5);
  const x = l.clone().sub(r).normalize(), y = new THREE.Vector3(0, 1, 0);
  y.addScaledVector(x, -x.dot(y)).normalize();
  const z = new THREE.Vector3().crossVectors(x, y);
  if (z.dot(o.clone().sub(head)) < 0) z.negate();
  return { o, x, y, z, head };
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
  const rand = seeded(`${seed}|${style.cut}|${lod}`);
  const scalp = metricSurface(hair, root);
  const f = headFrame(hair, root);
  if (!f) return null;
  const out = { position: [], normal: [], strand: [], card: [], skinIndex: [], skinWeight: [], index: [] };
  const grown = { scalp: 0, facial: {} };
  const nearScalp = grid(scalp.P);
  const mask = capMask(hair.material), uv = hair.geometry.attributes.uv;
  const onHair = mask && uv ? (c, n, tri) => {
    let u = 0, v = 0;
    for (const i of tri) { u += uv.getX(i) / 3; v += uv.getY(i) / 3; }
    return mask(u, v) > .5;
  } : null;
  const area = sampler(scalp, onHair, rand);
  // Cap vertices over bare skin: a strand combed onto them ends there (a long one hangs).
  if (mask && uv) scalp.bare = Uint8Array.from({ length: scalp.count }, (_, i) => mask(uv.getX(i), uv.getY(i)) < .25 ? 1 : 0);
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
    const width = Math.max(.003, Math.min(level.width_mm / 1000, len * .35)) * (.8 + .4 * rand());
    laid += len * width * .8;
    layCard(out, {
      start: s.p, n0: s.n, length: len, segments: Math.max(2, Math.min(level.segments, Math.round(len / .01) + 1)), width,
      lift: { root: cut.lift_mm.root / 1000 * (.6 + .8 * rand()), tip: cut.lift_mm.tip / 1000 * (.6 + .8 * rand()) },
      dir: (p, n) => combed(cut, f, p, n), surface: scalp, nearest: nearScalp, reach: CARDS.shell_reach_m, rand, curl: cut.curl, hang: !!cut.hang && s.n.dot(f.z) < .25,  // never down over the brow
      weights: weightsOf(hair, s.vertex, same), seed: rand(), layer: rand(),
    });
    grown.scalp++;
  }
  // Beards, moustaches and whiskers, from the face's own skin.
  if (skin && style.facial?.length) {
    const face = metricSurface(skin, root), nearFace = grid(face.P, .01);
    const names = hair.skeleton.bones.map(b => b.name), skinBones = skin.skeleton.bones;
    const toBones = i => Math.max(0, names.indexOf(skinBones[i]?.name));
    for (const name of style.facial) {
      const piece = FACIAL_HAIR[name];
      if (!piece) continue;
      const r = piece.region_cm;
      const keep = (c, n) => {
        const l = c.clone().sub(f.o), x = Math.abs(l.dot(f.x)) * 100, y = l.dot(f.y) * 100, z = l.dot(f.z) * 100;
        if (x < r.x[0] || x > r.x[1] || z < r.z_min || z > (r.z_max ?? Infinity)) return false;
        // The band narrows toward its ends, and droops there by \`droop\` cm.
        const t = (x - r.x[0]) / (r.x[1] - r.x[0]), mid = (r.y[0] + r.y[1]) / 2 - (r.droop ?? 0) * t * t;
        const half = (r.y[1] - r.y[0]) / 2 * Math.sqrt(Math.max(0, 1 - t * t * .75));
        if (Math.abs(y - mid) > half) return false;
        return piece.facing === 'front' ? n.dot(f.z) > .35 : Math.abs(n.dot(f.x)) > .3 && n.dot(f.z) > -.3;
      };
      const region = sampler(face, keep, rand);
      const width = piece.width_mm / 1000, len = piece.length_cm / 100;
      const want = Math.round(level.facial * piece.cover * region.area / (width * len));
      for (let c = 0; c < want; c++) {
        const s = region.draw();
        if (!s) break;
        const out_ = f.x.clone().multiplyScalar(Math.sign(s.p.clone().sub(f.o).dot(f.x)) * piece.outward);
        const fall = f.y.clone().multiplyScalar(-piece.fall);
        layCard(out, {
          start: s.p, n0: s.n, length: len * (1 - (piece.spread ?? .3) / 2 + (piece.spread ?? .3) * rand()), segments: Math.max(2, level.segments - 2), width: width * (.8 + .4 * rand()),
          lift: { root: piece.lift_mm.root / 1000, tip: piece.lift_mm.tip / 1000 }, dir: () => fall.clone().add(out_),
          surface: face, nearest: nearFace, reach: .01, rand, curl: .12, weights: weightsOf(skin, s.vertex, toBones), seed: rand(), layer: rand(),
        });
        grown.facial[name] = (grown.facial[name] ?? 0) + 1;
      }
    }
  }
  return { ...out, grown, frame: f, scalp };
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
    diffuseColor.rgb *= ( 0.8 + 0.3 * h2 + 0.25 * streak ) * root * mix( 0.8, 1.1, vChiCard.w );
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

const built = new WeakMap();   // source geometry -> Map(person key -> geometry)

/**
 * Give one cloned figure its strand cards. Call after the body is cloned (and varied).
 * `person` keys the seed and the material; `year` picks an era default; `style` overrides both (tests).
 * Returns { mesh, grown } or null where nothing is grown (a far level, no cap, no style).
 */
export function dressHair(root, { lod = 0, person = null, year = null, style: given = null } = {}) {
  if (!root || !CARDS.lods[lod]) return null;
  const style = given ?? hairFor(person, year);
  if (!style) return null;
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
  const key = `${person ?? 'anon'}|${lod}|${style.cut}|${(style.facial ?? []).join('+')}`;
  let cache = built.get(hair.geometry);
  if (!cache) {
    cache = new Map();
    built.set(hair.geometry, cache);
    hair.geometry.addEventListener('dispose', () => { for (const g of cache.values()) g.geometry.dispose(); cache.clear(); });
  }
  let entry = cache.get(key);
  if (!entry) {
    const grown = growHair({ hair, skin: skin?.skeleton ? skin : null, root, style, lod, seed: person ?? 'anon' });
    if (!grown || !grown.index.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(grown.position, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(grown.normal, 3));
    g.setAttribute('chiStrandT', new THREE.Float32BufferAttribute(grown.strand, 3));
    g.setAttribute('chiCard', new THREE.Float32BufferAttribute(grown.card, 4));
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(grown.skinIndex, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(grown.skinWeight, 4));
    g.setIndex(grown.index);
    entry = { geometry: g, grown: grown.grown, frame: grown.frame, R: grown.scalp.R };
    cache.set(key, entry);
  }
  const material = strandMaterial(HAIR_COLOURS[style.colour] ?? HAIR_COLOURS.dark_brown, person ?? 'anon');
  const mesh = new THREE.SkinnedMesh(entry.geometry, material);
  mesh.name = 'hair_cards';
  mesh.frustumCulled = false;
  mesh.castShadow = false;
  mesh.receiveShadow = hair.receiveShadow;
  // The cards are in metres; the cap's bind matrix takes its own (quantised) positions.
  // Bound through the cap's rest matrix, they skin exactly as the cap does.
  mesh.bind(hair.skeleton, hair.bindMatrix.clone().multiply(entry.R.clone().invert()));
  hair.parent.add(mesh);
  // Under the cards the cap is the scalp's colour: solid, not its own masked strands, so no
  // skin shows between the cards. (The far levels keep the cap as it was, alone.)
  if (entry.grown.scalp && hair.material?.alphaTest > CARDS.cap_alpha_test) hair.material.alphaTest = CARDS.cap_alpha_test;
  // A hat put on later (driver-livery.js) cuts the strands above its band.
  let frame = 0, seen = null;
  mesh.onBeforeRender = () => {
    if (frame++ % 30) return;
    const hat = mesh.parent?.children.find(o => o.isSkinnedMesh && /^headwear/.test(o.material?.name ?? '') && !/band/.test(o.material.name)) ?? null;
    if (hat === seen) return;
    seen = hat;
    material.userData.chiCards.value.z = hat ? hatBand(hat, hair, root, entry.frame) : NO_CLIP;
  };
  return { mesh, grown: entry.grown, style };
}
