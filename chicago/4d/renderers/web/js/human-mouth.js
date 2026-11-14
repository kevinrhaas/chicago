// SPDX-License-Identifier: GPL-3.0-or-later
// human-mouth.js — a mouth that opens: the teeth behind the lips, and what plays the smile (T-3553).
//
// The owner, 2026-11-13, of the Greys' stand-in likenesses: "add what is needed to the face
// model to make it work and eventually speak, i want them photographic matched". A person
// whose front picture grins (or who has a picture of their smile of its own) rests with their
// mouth shut, as their other pictures show it, and moves into the grin: human-variation.js gives their body a morph target for it (SMILE), from
// the smile their record fitted to that picture (tools/bake_likeness_skin.py). Two things here:
//
// The teeth. Between parted lips something has to stand. The record (`texture.teeth`) gives a
// strip of points behind the lips: where each stands (metres, the body's rest frame) and where
// on the body's own map its colour is, a patch of their skin sheet that holds the front
// picture's teeth. The strip is added to the body's skin geometry as rows of its own, carried
// whole by one bone (the head's), so it is drawn by the skin's own material in the skin's own
// draw call, at every level of detail. With the mouth shut the lips stand in front of it, and
// what shows between lips that do not seal is in their shade (human-skin.js MOUTH_SHADE: the
// strip takes the light as the face moves into its smile).
//
// What a caller may rely on:
//   - the first rows of every attribute are the source's own, in its order;
//   - the strip's rows follow: `cols` across by `rows` down, a row of the record at a time,
//     two triangles a cell, facing out of the mouth;
//   - every morph target leaves the strip where it stands;
//   - rows apart (`apart`: drawn teeth) are the strips' rows alone, with none of the source's
//     before them, and as many morph targets as the source has, none of which moves them;
//   - a geometry drawn in groups, or with no index, comes back as null, and the source is
//     never changed.
//
// The mouth's play (createMouth). A person with a smile gives it to a visitor who stands near
// in front of them, and with a greeting; talking, they keep some of it and their jaw moves
// with the talk (the skeleton's `jaw` bone turned about its hinge in an uneven run of syllables,
// no words; the body's exported `jawOpen` target turns both lips together and opens nothing).
// human-skin.js leaves one on each figure whose face has the smile, or that has a jaw
// (`userData.chiMouth`), and human-actions.js, which knows when the person greets and talks,
// tells it each frame.
// `say(level)` is where a voice goes when one speaks for them: it takes the jaw outright, a
// level at a time, in place of that run. A person with no smile has a mouth all the same: they
// talk with their jaw, and smile at nobody.
// Reconstructed motion: liberties L-grey-smile-3553 and L-grey-sarah-smile-3553.
//
// Everyone's teeth. The owner, 2026-11-14: "to make everyone else speak can you fill in their
// teeth and structure now for that and we will add voices ... so if you want to render teeth
// sensibly now and put in whatever is needed later". A
// person with no picture of their teeth has drawn ones (drawnTeeth): two short rows of points
// behind their own lips, the upper carried by the head's bone and the lower by the jaw's, as a
// small mesh of its own in the person's skin material (36 vertices and one draw; rows added to
// the skin's own geometry, as a pictured strip is, would copy a whole body for every person).
// Its geometry has the skin's own count of morph targets, all still, so the two are drawn by
// one program and the material is not made over between them.
// Where the rows stand is read off the person's own face at that level: the lips' inner edge
// (LIP_RIM, its vertices by their place on the body's map, the same on every hm08 body), a
// curve through it, the rows set back behind it, and each row's height by its own lip's edge
// (LIP_ARCS). Their colour is no picture: their place on the map lies outside it (u from 2)
// and says which row, how far across and from gum to edge, and which of the drawn sets and
// tones, and human-skin.js draws the teeth there (TEETH_DRAWN). The mesh is made hidden, and
// the mouth's play draws it only while the jaw is open and a visitor stands near
// (MOUTH.teeth_deg, teeth_m), or for a still (`pose`): behind shut lips, and far off, it
// costs nothing. A level so far that the lips' edge has no vertex of one lip's own left has
// no rows (three girls' bodies at the fourth level, which is never drawn that near).
// Reconstructed: liberty L-everyone-teeth-3553.
import * as THREE from 'three';
import { rawView, isWhole, fullOf } from './human-fine.js';
import { SMILE, seededRandom } from './human-variation.js';

const JAW = 'jaw';

/** A record's `teeth` block as numbers ({ cols, rows, at, uv, bone, rect }), or null where it does not parse. */
export function teethStrip(teeth) {
  const [cols, rows] = teeth?.grid ?? [], n = cols * rows;
  if (!(cols >= 2) || !(rows >= 2) || !Number.isInteger(n) || typeof teeth.bone !== 'string') return null;
  const { at_m, uv } = teeth;
  if (!Array.isArray(at_m) || !Array.isArray(uv) || at_m.length !== n || uv.length !== n) return null;
  if (!at_m.every(p => p?.length === 3 && p.every(Number.isFinite)) || !uv.every(p => p?.length === 2 && p.every(Number.isFinite))) return null;
  // The strip's own part of the body's map, a hair wider than its points.
  const us = uv.map(p => p[0]), vs = uv.map(p => p[1]), e = 1e-4;
  return { cols, rows, at: Float32Array.from(at_m.flat()), uv: Float32Array.from(uv.flat()), bone: teeth.bone,
    rect: [Math.min(...us) - e, Math.min(...vs) - e, Math.max(...us) + e, Math.max(...vs) + e] };
}

/**
 * The lips' inner edge on the body's map (hm08: every body shares the layout): the vertices
 * where the lips turn in and the inner mouth's own island begins, each by its place on the map,
 * from the upper lip's middle round by one corner, along the lower lip and back by the other.
 * tools/test_human_mouth.mjs finds every one of them on every body. LIP_ARCS says which of them
 * are whose: the upper lip's edge is the first `upper` + 1 and the last `upper` + 1 (the head
 * carries them), the lower lip's those from `lower[0]` to `lower[1]` (the jaw carries them), and
 * the ones between are the mouth's two corners, which belong to both.
 */
export const LIP_RIM = Object.freeze([[.7783, .988], [.7802, .9863], [.7832, .9844], [.7866, .9817], [.789, .9797], [.7907, .978], [.7946, .9741],
  [.7973, .9705], [.8017, .9651], [.8029, .9619], [.8039, .9595], [.8049, .957], [.8059, .9556], [.8071, .9556], [.8081, .9556], [.811, .959],
  [.8149, .9624], [.8257, .9729], [.832, .9751], [.8408, .9751], [.8496, .9751], [.8557, .9729], [.8664, .9624], [.8703, .959], [.8733, .9556],
  [.8745, .9556], [.8755, .9556], [.8764, .957], [.8774, .9595], [.8786, .9619], [.8796, .9651], [.884, .9705], [.8869, .9741], [.8906, .978],
  [.8923, .9797], [.8948, .9817], [.8982, .9844], [.9011, .9863], [.9031, .988]].map(Object.freeze));
export const LIP_ARCS = Object.freeze({ upper: 9, lower: Object.freeze([15, 23]) });
/**
 * Drawn teeth, for a person with no picture of their own.
 *   within, least     a vertex is one of the lips' edge when its place on the map is within `within` of one of
 *                     LIP_RIM's; a level with fewer than `least` of them, or a mouth outside `wide_m`, has none
 *   cols              points across each row
 *   back_m, bite_m    the upper row stands this far behind every point of the lips' edge, the lower this much further
 *   past_m, gum_m     each reaches this far past the mouth's corners, and this far from its own lip's edge up into the lip
 *   lip_m             how far a lip hangs past its own inner edge, seen from the front: the upper lip below its edge,
 *                     the lower lip above its own (measured on the 35 bodies at the nearest level, within 8 mm of the
 *                     face's middle, the lip's lowest or highest point against its edge's mean height there:
 *                     1.2 to 1.7 mm, and 0.1 to 0.8 mm)
 *   upper_m, lower_m  how much of the upper teeth shows below the upper lip, and of the lower teeth above the lower
 *                     lip (hidden behind it, negative), at `ages[0]` years and at `ages[1]`: the young show their
 *                     upper teeth, the old their lower
 *   sets, tones       the drawn sets (the teeth's sizes and edges) and tones (ivory to stained), one of each for a person
 *   u0, v0, pad       on the map: u = u0 + set_u * set + (across, 0..1);
 *   set_u, tone_v,    v = v0 + tone_v * tone + row_v * (the lower row) + pad + (1 - 2 * pad) * (gum 0 .. edge 1).
 *   row_v             human-skin.js reads a place back by the same numbers.
 */
export const TEETH_DRAWN = Object.freeze({ within: .0015, least: 8, wide_m: Object.freeze([.015, .09]), cols: 9, back_m: .0025, bite_m: .0015, past_m: .002, gum_m: .006,
  lip_m: Object.freeze([.0015, .0003]), upper_m: Object.freeze([.0025, .0005]), lower_m: Object.freeze([-.0005, .0015]), ages: Object.freeze([25, 65]), sets: 8, tones: 4, u0: 2, v0: 2, set_u: 2, tone_v: 4, row_v: 2, pad: .05 });

const rims = new WeakMap();   // a map's coordinates (the attribute) -> { ids, at }: the lips' inner edge there
const NO_RIM = Object.freeze({ ids: new Uint32Array(0), at: new Uint8Array(0) });

/** The vertices of `uv` (a body's texture coordinates) that are the lips' inner edge (LIP_RIM). */
export function lipRim(uv) { return rimOf(uv).ids; }

/** ...and, beside them (`ids`), which of LIP_RIM's each one is (`at`). */
function rimOf(uv) {
  if (!uv?.count) return NO_RIM;
  let rim = rims.get(uv);
  if (rim) return rim;
  const D = TEETH_DRAWN, near = [];
  let u0 = Infinity, u1 = -Infinity, v0 = Infinity;
  for (const [u, v] of LIP_RIM) { u0 = Math.min(u0, u); u1 = Math.max(u1, u); v0 = Math.min(v0, v); }
  for (let i = 0; i < uv.count; i++) { const u = uv.getX(i), v = uv.getY(i); if (u > u0 - D.within && u < u1 + D.within && v > v0 - D.within && v <= 1) near.push(i); }
  const found = new Map();   // a vertex -> the first of LIP_RIM's it is (a far level's vertex may be nearest to two)
  LIP_RIM.forEach(([u, v], k) => {
    let best = -1, d = D.within;
    for (const i of near) { const e = Math.hypot(uv.getX(i) - u, uv.getY(i) - v); if (e < d) { d = e; best = i; } }
    if (best >= 0 && !found.has(best)) found.set(best, k);
  });
  rim = { ids: Uint32Array.from(found.keys()), at: Uint8Array.from(found.values()) };
  rims.set(uv, rim);
  return rim;
}

/**
 * Which drawn teeth a person has: { set, tone, upper, lower, key }. The same person, the same
 * teeth; `age` in years (40 where it is not known).
 */
export function drawnLook({ id = 'human', age = null } = {}) {
  const D = TEETH_DRAWN, rand = seededRandom(`teeth:${id}`);
  const t = Math.min(1, Math.max(0, ((Number.isFinite(age) ? age : 40) - D.ages[0]) / (D.ages[1] - D.ages[0])));
  const set = Math.min(D.sets - 1, Math.floor(rand() * D.sets));
  const tone = Math.min(D.tones - 1, Math.max(0, Math.round(t * (D.tones - 1.6) + rand() * 1.2 - .4)));
  const at = pair => Math.round((pair[0] + (pair[1] - pair[0]) * t) * 1e4) / 1e4;
  const upper = at(D.upper_m), lower = at(D.lower_m);
  return { set, tone, upper, lower, key: `drawn|${set}|${tone}|${upper}|${lower}` };
}

/**
 * A person's drawn teeth, from their own skin `geometry` at this level: two strips as
 * teethGeometry takes them ([{ strip, bone: 'head' }, { strip, bone: 'jaw' }]), or null where
 * the lips' edge is not found on it.
 *
 *   metres   the matrix taking the geometry's positions to metres (human-skin.js restMatrix)
 *   look     drawnLook(...)
 */
export function drawnTeeth(geometry, { metres, look } = {}) {
  const pos = geometry?.attributes?.position, tex = geometry?.attributes?.uv, D = TEETH_DRAWN;
  if (!pos || !tex || !metres || !look) return null;
  const { ids, at: which } = rimOf(tex), A = LIP_ARCS, last = LIP_RIM.length - 1;
  if (ids.length < D.least) return null;
  // The edge, metres: x across the face (the body's left), y up, z out of the face; and whose
  // each point is (the corners are both lips').
  const P = [], v = new THREE.Vector3();
  let xa = Infinity, xb = -Infinity, xm = 0;
  ids.forEach((i, j) => {
    v.fromBufferAttribute(pos, i).applyMatrix4(metres);
    const k = which[j], lower = k >= A.lower[0] && k <= A.lower[1], upper = k <= A.upper || k >= last - A.upper;
    P.push([v.x, v.y, v.z, !lower, !upper]);
    xa = Math.min(xa, v.x); xb = Math.max(xb, v.x); xm += v.x / ids.length;
  });
  if (!(xb - xa > D.wide_m[0] && xb - xa < D.wide_m[1]) || !P.some(p => !p[4]) || !P.some(p => !p[3])) return null;
  // The curve the lips make across the face, seen from above: z = a + b (x - xm)^2 by least
  // squares, back from the middle to the corners; and how far behind it the edge's deepest point lies.
  let s1 = 0, s2 = 0, t0 = 0, t1 = 0;
  for (const p of P) { const q = (p[0] - xm) ** 2; s1 += q; s2 += q * q; t0 += p[2]; t1 += q * p[2]; }
  const n = P.length, det = n * s2 - s1 * s1, b = Math.min(0, det > 1e-18 ? (n * t1 - s1 * t0) / det : 0), a = (t0 - b * s1) / n;
  let behind = 0;
  for (const p of P) behind = Math.max(behind, a + b * (p[0] - xm) ** 2 - p[2]);
  // Each lip's own edge: its height across the face (the corners are in both).
  const h = (xb - xa) / 8;
  const line = (x, lower) => { let w = 0, y = 0; for (const p of P) if (p[lower ? 4 : 3]) { const k = Math.exp(-(((p[0] - x) / h) ** 2)); w += k; y += k * p[1]; } return y / w; };
  const row = (lower) => {
    const at = new Float32Array(D.cols * 2 * 3), uv = new Float32Array(D.cols * 2 * 2);
    for (let c = 0; c < D.cols; c++) {
      const s = c / (D.cols - 1), x = xa - D.past_m + (xb - xa + 2 * D.past_m) * s, y = line(x, lower);
      const z = a + b * (x - xm) ** 2 - behind - D.back_m - (lower ? D.bite_m : 0);
      // Top row first: the upper teeth's gum, then their edge; the lower teeth's edge, then their gum.
      const ys = lower ? [y + D.lip_m[1] + look.lower, y - D.gum_m] : [y + D.gum_m, y - D.lip_m[0] - look.upper], along = lower ? [1, 0] : [0, 1];
      for (let r = 0; r < 2; r++) {
        at.set([x, ys[r], z], 3 * (r * D.cols + c));
        uv.set([D.u0 + D.set_u * look.set + s, D.v0 + D.tone_v * look.tone + (lower ? D.row_v : 0) + D.pad + (1 - 2 * D.pad) * along[r]], 2 * (r * D.cols + c));
      }
    }
    return { cols: D.cols, rows: 2, at, uv, bone: lower ? JAW : 'head', rect: null };
  };
  return [{ strip: row(false), bone: 'head' }, { strip: row(true), bone: JAW }];
}

/** `attr` with `added` rows more, each number of a new row given by `value(row, part)` in the attribute's own meaning. */
function withRows(attr, n0, added, value) {
  const { array, stride, offset } = rawView(attr), k = attr.itemSize, out = new array.constructor((n0 + added) * k);
  const whole = isWhole(out), full = whole && attr.normalized ? fullOf(out) : 1;
  const lo = whole ? (out instanceof Int8Array ? -127 : out instanceof Int16Array ? -32767 : 0) : -Infinity;
  const hi = whole ? (out instanceof Uint8Array ? 255 : out instanceof Int8Array ? 127 : out instanceof Uint16Array ? 65535 : out instanceof Int16Array ? 32767 : 4294967295) : Infinity;
  for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) out[i * k + c] = array[i * stride + offset + c];
  for (let j = 0; j < added; j++) for (let c = 0; c < k; c++) {
    const v = value(j, c) * full;
    out[(n0 + j) * k + c] = whole ? Math.min(hi, Math.max(lo, Math.round(v))) : v;
  }
  const made = new THREE.BufferAttribute(out, k, attr.normalized);
  made.name = attr.name;
  return made;
}

/** `added` rows of an attribute like `attr`, kept as plain numbers. */
function plainRows(attr, added, value) {
  const k = attr.itemSize, out = new Float32Array(added * k);
  for (let j = 0; j < added; j++) for (let c = 0; c < k; c++) out[j * k + c] = value(j, c);
  const made = new THREE.BufferAttribute(out, k);
  made.name = attr.name;
  return made;
}

/**
 * `src` with the strip of teeth added: a new geometry, or null where it cannot be (no strip, no
 * index, drawn in groups, no texture coordinates).
 *
 *   metres   the matrix taking `src`'s positions to metres (human-skin.js restMatrix)
 *   strip    teethStrip(...)
 *   bone     the number, in the mesh's skeleton, of the bone that carries the strip
 *   strips   in place of those two, several: [{ strip, bone }], their rows added in this order
 *   apart    the strips' rows alone, as a geometry of the source's own kind (the same attributes,
 *            kept the same way, and as many morph targets, which leave the rows where they
 *            stand), for a mesh of its own in the source's material: a renderer draws the two
 *            with one program. Their place on the map alone is kept as plain numbers: a body
 *            packs its own into whole numbers of 0..1, which cannot hold a place outside the
 *            map (drawn teeth).
 */
export function teethGeometry(src, { metres, strip, bone, strips = null, apart = false } = {}) {
  const pos = src?.attributes?.position, tex = src?.attributes?.uv;
  const list = strips ?? [{ strip, bone }];
  if (!pos || !tex || !src.index || src.groups?.length || !metres || !list.length || !list.every(s => s?.strip && s.bone >= 0)) return null;
  const added = list.reduce((n, s) => n + s.strip.cols * s.strip.rows, 0), n0 = apart ? 0 : pos.count;
  const back = new THREE.Matrix4().copy(metres).invert(), turn = new THREE.Matrix3().setFromMatrix4(metres).transpose();
  // Where each point stands in the geometry's own numbers, and which way its strip faces there.
  const P = new Float32Array(added * 3), N = new Float32Array(added * 3), UV = new Float32Array(added * 2), carried = new Uint16Array(added);
  const v = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3();
  const tri = apart ? [] : Array.from(src.index.array);
  let k = 0;
  for (const { strip: { cols, rows, at, uv }, bone: by } of list) {
    const point = (c, r, out) => out.fromArray(at, 3 * (Math.min(rows - 1, Math.max(0, r)) * cols + Math.min(cols - 1, Math.max(0, c))));
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const i = k + r * cols + c;
      v.fromArray(at, 3 * (r * cols + c)).applyMatrix4(back).toArray(P, 3 * i);
      // across (the body's left) by up: out of the mouth
      a.subVectors(point(c + 1, r, a), point(c - 1, r, v));
      b.subVectors(point(c, r - 1, b), point(c, r + 1, v));
      v.crossVectors(a, b).applyMatrix3(turn).normalize().toArray(N, 3 * i);
      UV[2 * i] = uv[2 * (r * cols + c)]; UV[2 * i + 1] = uv[2 * (r * cols + c) + 1];
      carried[i] = by;
    }
    for (let r = 0; r + 1 < rows; r++) for (let c = 0; c + 1 < cols; c++) {
      const i = n0 + k + r * cols + c;
      tri.push(i, i + cols, i + 1, i + 1, i + cols, i + cols + 1);
    }
    k += cols * rows;
  }
  const n = n0 + added, g = new THREE.BufferGeometry();
  g.name = `${src.name || 'skin'}~teeth`;
  g.setIndex(new THREE.BufferAttribute(n > 65535 ? Uint32Array.from(tri) : Uint16Array.from(tri), 1));
  for (const [name, attr] of Object.entries(src.attributes)) {
    const value = name === 'position' ? (j, c) => P[3 * j + c]
      : name === 'normal' ? (j, c) => N[3 * j + c]
        : /^uv\d*$/.test(name) ? (j, c) => UV[2 * j + c]
          : name === 'skinIndex' ? (j, c) => (c === 0 ? carried[j] : 0)
            : name === 'skinWeight' ? (j, c) => (c === 0 ? 1 : 0)
              : name === 'tangent' ? (j, c) => (c === 0 || c === 3 ? 1 : 0)
                : name === 'color' ? () => 1 : () => 0;
    g.setAttribute(name, apart && /^uv\d*$/.test(name) ? plainRows(attr, added, value) : withRows(attr, n0, added, value));
  }
  // A morph target that moves (the blink, a jaw) leaves the strip alone; one that states
  // positions outright states the strip's own. Rows apart keep the source's count of targets
  // for that alone: the same program draws them as draws the source.
  for (const [name, targets] of Object.entries(src.morphAttributes ?? {})) {
    g.morphAttributes[name] = targets.map(t => t && withRows(t, n0, added, src.morphTargetsRelative || name !== 'position' ? () => 0 : (j, c) => P[3 * j + c]));
  }
  g.morphTargetsRelative = src.morphTargetsRelative;
  // The strip stands inside the head: the source's bounds hold (rows apart have copies of
  // their own, so that nothing measuring the rows moves the body's).
  g.boundingBox = apart ? src.boundingBox?.clone() ?? null : src.boundingBox;
  g.boundingSphere = apart ? src.boundingSphere?.clone() ?? null : src.boundingSphere;
  g.userData = { ...src.userData, chiTeeth: { of: n0, added } };
  return g;
}

const kept = new WeakMap();   // source geometry -> Map(key -> geometry with teeth, or null)

/**
 * teethGeometry, once for each source and `key` (a person's sheet, or their drawn teeth), freed
 * when its source is. A geometry that already has its teeth is handed back as it is. `opts` may
 * be a function, called only when the geometry has to be made.
 */
export function teethOf(src, key, opts) {
  if (!src || src.userData?.chiTeeth) return src ?? null;
  let own = kept.get(src);
  if (!own) {
    kept.set(src, (own = new Map()));
    src.addEventListener('dispose', () => { for (const g of own.values()) g?.dispose(); own.clear(); });
  }
  if (!own.has(key)) own.set(key, teethGeometry(src, (typeof opts === 'function' ? opts() : opts) ?? undefined));
  return own.get(key) ?? src;
}

/**
 * The mouth's play, for a person whose body has the smile, or a jaw alone (who then talks with
 * it and smiles at nobody).
 *   within_m, front_deg   a visitor this near, and no further round from straight ahead, is smiled at
 *   in_s, out_s         how fast the smile comes and goes
 *   after_s             how long it stays after a greeting
 *   talk                how much of it a person keeps while talking
 *   jaw_deg, syllable_hz  talking: how far the jaw turns at a syllable's height, and their rate
 *   say_deg             a voice's level 1 turns the jaw this far
 *   teeth_m, teeth_deg  a figure's drawn teeth (a mesh of their own) are drawn for a visitor this near, and for a
 *                       still, while its jaw is this far open: behind shut lips they are not drawn at all
 */
export const MOUTH = Object.freeze({ within_m: 3.2, front_deg: 60, in_s: .3, out_s: .7, after_s: 2.2, talk: .4, jaw_deg: 7, syllable_hz: 3.6, say_deg: 12, teeth_m: 6, teeth_deg: .3 });
const DEG = Math.PI / 180;

export function createMouth({ id = 'human', scene = null } = {}) {
  const rand = seededRandom(`mouth:${id}`);
  let faces = [], jaw = null, teeth = [], shown = false, time = rand() * 40, smile = 0, after = 0, open = 0, said = null;
  const off = [rand() * 6.283, rand() * 6.283], turn = new THREE.Quaternion();
  // The jaw's bone is the clip's to pose: what it holds is taken as found each frame, unless it
  // is what this left there, and the opening is turned on over it.
  const turnJaw = () => {
    if (!jaw) return;
    const q = jaw.bone.quaternion;
    if (q.equals(jaw.out)) q.copy(jaw.base); else jaw.base.copy(q);
    if (open > 0) { q.premultiply(turn.setFromAxisAngle(jaw.axis, open * DEG)); jaw.out.copy(q); } else jaw.out.set(NaN, NaN, NaN, NaN);
  };
  const show = () => { for (const f of faces) f.mesh.morphTargetInfluences[f.smile] = smile; turnJaw(); for (const t of teeth) t.visible = shown && open > MOUTH.teeth_deg; };
  const api = {
    /** The meshes of `next` that take the smile, and its jaw; false where the figure has neither. */
    bind(next) {
      // A jaw this left turned (a level set aside while talking) goes back to the clip's first.
      if (jaw?.bone.quaternion.equals(jaw.out)) jaw.bone.quaternion.copy(jaw.base);
      faces = []; jaw = null; teeth = [];
      next?.traverse((o) => {
        if (o.userData?.chiTeeth === true) { teeth.push(o); return; }   // human-skin.js: this figure's drawn teeth (no face: its targets move nothing)
        const at = o.isMesh ? o.morphTargetDictionary?.[SMILE] : undefined;
        if (at !== undefined && o.morphTargetInfluences) faces.push({ mesh: o, smile: at });
        if (jaw || !o.isSkinnedMesh) return;
        // The hinge: the body's own left-to-right, as its jaw's parent bone holds it in the bind
        // pose, so it does not depend on how the head is turned when this is read.
        const bones = o.skeleton?.bones ?? [], k = bones.findIndex(b => b.name === JAW), p = k < 0 ? -1 : bones.indexOf(bones[k].parent);
        if (p < 0) return;
        const axis = new THREE.Vector3(1, 0, 0).transformDirection(new THREE.Matrix4().multiplyMatrices(o.skeleton.boneInverses[p], o.bindMatrix));
        jaw = { bone: bones[k], axis, base: bones[k].quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) };
      });
      show();
      return faces.length > 0 || jaw !== null;
    },
    get bound() { return faces.length > 0 || jaw !== null; },
    /** A voice's level now (0..1) turns the jaw in place of the talk's own run; null gives it back. */
    say(level) { said = Number.isFinite(level) ? Math.min(1, Math.max(0, level)) : null; return api; },
    /** Hold the face so (a still): `smile` 0..1 of the smile, `jaw` degrees open; its drawn teeth are in view where the jaw is open, until the next `apply`. */
    pose({ smile: s = smile, jaw: j = open } = {}) {
      smile = Math.min(1, Math.max(0, Number(s) || 0)); open = Math.max(0, Number(j) || 0); shown = true;
      show();
      return api;
    },
    /** Carry on from another mouth of the same person (the level drawn before this one). */
    follow(prev) {
      const s = prev?.state?.();
      if (s) { ({ time, smile, after, open, said, shown = false } = s); show(); }
      return api;
    },
    state() { return { time, smile, after, open, said, shown }; },
    /**
     * A frame of `dt` seconds. `greeting`: the person is greeting someone; `talk`: how much they
     * are talking (0..1); `viewer` (a world position) and `root` (the figure's own root, which
     * faces its +Z): where the visitor stands, or `facing` outright.
     */
    apply(dt, { greeting = false, talk = 0, viewer = null, root = null, facing = null } = {}) {
      if (!faces.length && !jaw) return;
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, .1) : 0;
      time += dt;
      shown = false;   // drawn teeth are for a visitor who stands near: with none told of, for nobody
      if (viewer && root) {
        const dx = viewer.x - root.position.x, dz = viewer.z - root.position.z, a = root.rotation.y;
        shown = Math.hypot(dx, dz) < MOUTH.teeth_m;
        if (facing === null) {
          // The visitor in the figure's own frame (turned back by its heading about the upright).
          const x = dx * Math.cos(a) - dz * Math.sin(a), z = dx * Math.sin(a) + dz * Math.cos(a);
          facing = Math.hypot(x, z) < MOUTH.within_m && Math.abs(Math.atan2(x, z)) < MOUTH.front_deg * DEG;
        }
      }
      facing = facing === true;
      after = greeting ? MOUTH.after_s : Math.max(0, after - dt);
      const talking = Math.min(1, Math.max(0, talk));
      // (A mouth with no smile to give keeps none: its jaw is all of it.)
      const want = !faces.length ? 0 : greeting || after > 0 || facing ? 1 : talking > .05 || said > 0 ? MOUTH.talk * (said > 0 ? 1 : talking) : 0;
      smile += (want - smile) * (1 - Math.exp(-dt / (want > smile ? MOUTH.in_s : MOUTH.out_s)));
      if (Math.abs(want - smile) < 1e-3) smile = want;
      // Talk with no words: syllables at about the rate of speech, uneven in height, with a
      // breath between phrases.
      let to = 0;
      if (said !== null) to = MOUTH.say_deg * said;
      else if (talking > 1e-3) {
        const beat = .5 - .5 * Math.cos(time * 2 * Math.PI * MOUTH.syllable_hz);
        const height = .6 + .4 * Math.sin(time * 1.9 + off[0]);
        const phrase = Math.min(1, Math.max(0, 1.6 + 2.2 * Math.sin(time * .7 + off[1])));
        to = MOUTH.jaw_deg * talking * beat * height * phrase;
      }
      open += (to - open) * (1 - Math.exp(-dt / .04));
      if (open < 1e-3 && to === 0) open = 0;
      show();
    },
    snapshot() { return { smile: +smile.toFixed(3), jaw_deg: +open.toFixed(3), faces: faces.length, said }; },
  };
  if (scene) api.bind(scene);
  return api;
}
