// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-hats.js — a person's own hat, laid on their own head (T-3522).
 *
 * The owner, 2026-11-08, of three 1812 townsmen standing on the prairie: *"all of these guys wear
 * the same hat and clothing"*. Every man of a role wore the one hat modelled into his dressed
 * body, and a hat is the first thing that tells one figure from another across a field: its
 * outline shows where a cloth colour does not. So a person whose dress names a `hat` gets one
 * made for his head at load, and the body's own hat is hidden (the dress's `hide` list):
 *
 *   round   a felt round hat: crown height, taper, brim width, the brim's roll at the sides and
 *           its droop before and behind are his own (a tall-crowned town hat, a low-crowned
 *           wide-brimmed country one, an old soft one gone down at the front);
 *   straw   the same lathe, low in the crown and wide, in straw with a dark band (Lambert's
 *           summer straw of Lower Canada, Wau-Bun's mitiff of 1830, the settler reading's
 *           "wide-brimmed felt or straw hat");
 *   knit    a knitted cap close over the crown with its top falling back (the voyageur's tuque
 *           or bonnet rouge), for a man whose body has none;
 *
 * T-3553 adds the ladies' hats of 1904 (the owner, 2026-11-14: "they are very fancy and lots of
 * details"), after the Met's hats of 1900–1905 (docs/RESEARCH/finery-3553/):
 *
 *   picture  a wide brim and a low crown, perched high on the dressed hair and tipped forward,
 *            one side turned up (`cock`), the brim's edge waved;
 *   sailor   the straw sailor: a flat-topped straight crown, a flat brim, a ribbon round it;
 *   toque    no brim: a low, wide, ruched crown of silk or velvet, close over the hair;
 *
 * each with its own `trim`: ostrich plumes curling from the band over the crown and brim, a
 * cluster of silk flowers with their leaves, a ribbon bow's two loops. The trimming is its own
 * small mesh (vertex-coloured, one material), named `accessory__…` as the body's own plumes
 * are, so the hair's cut and the greeting's brim see only the hat.
 *
 * The lathe is fitted to the head it sits on: its band follows this body's own cap and brow (as
 * human-hair.js lays its headcloth), a few millimetres out over the hair, set level a little
 * above the brow in front and lower behind. Rigid on the head bone, built at every level (so it
 * reads far off), one small geometry a person, freed with the cap it was laid on. Its material
 * is named `headwear__…`, so the strand hair is cut under it (human-hair.js) and the hat-tip
 * greeting finds its brim (human-actions.js) as they do a hat modelled into the body.
 */
import * as THREE from 'three';
import { headFrame, metricSurface } from './human-hair.js';

/** Bearings round the head, by level: a far level needs fewer. */
const SEGMENTS = [32, 28, 20, 14];

const made = new WeakMap();   // cap geometry -> Map(person|kind -> { geometry, R })

/** The head's points about its centre (the cap, and the brow's skin), in the face's frame. */
function headPoints(hair, skin, root, f) {
  const pts = [];
  const take = (P, near) => {
    const v = new THREE.Vector3();
    for (let i = 0; i < P.length / 3; i++) {
      v.set(P[3 * i], P[3 * i + 1], P[3 * i + 2]).sub(f.o);
      const x = v.dot(f.x), y = v.dot(f.y), z = v.dot(f.z);
      if (y < -.01 || y > .17 || Math.hypot(x, z + .08) > near) continue;
      pts.push([x, y, z]);
    }
  };
  take(metricSurface(hair, root).P, .16);
  if (skin) take(metricSurface(skin, root).P, .13);
  return pts;
}

/** The head's radius about (0, cz) at a height and a bearing (0 ahead, +pi/2 the body's left). */
function radiusAt(pts, y, th, cz, seg) {
  let r = 0;
  for (const [x, py, z] of pts) {
    if (Math.abs(py - y) > .012) continue;
    const a = Math.atan2(x, z - cz);
    let da = Math.abs(a - th); if (da > Math.PI) da = 2 * Math.PI - da;
    if (da > Math.PI / seg * 1.6) continue;
    r = Math.max(r, Math.hypot(x, z - cz));
  }
  return r;
}

/** Fill bearings the points missed from their neighbours, then smooth the ring twice. */
function smoothRing(row, fallback) {
  const n = row.length;
  for (let k = 0; k < n; k++) if (!row[k]) row[k] = Math.max(row[(k + n - 1) % n], row[(k + 1) % n]) || fallback;
  for (let pass = 0; pass < 2; pass++) {
    const prev = row.slice();
    for (let k = 0; k < n; k++) row[k] = (prev[(k + n - 1) % n] + 2 * prev[k] + prev[(k + 1) % n]) / 4;
  }
  return row;
}

/** The ladies' kinds of 1904 (T-3553). */
export const LADY_HATS = Object.freeze(['picture', 'sailor', 'toque']);
const rgb3 = (a) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? a : null);

/** A hat's trimming, held to a few plumes, a few flowers and one bow; null where it names none. */
function trimSpec(t, clamp) {
  if (!t || typeof t !== 'object') return null;
  const plumes = t.plumes && rgb3(t.plumes.rgb) ? { n: Math.round(clamp(t.plumes.n, 1, 3, 2)), rgb: rgb3(t.plumes.rgb), length: clamp(t.plumes.length_m, .12, .34, .24), side: clamp(t.plumes.side, -1, 1, 1) } : null;
  const flowers = t.flowers && rgb3(t.flowers.rgb) ? { n: Math.round(clamp(t.flowers.n, 3, 14, 7)), rgb: rgb3(t.flowers.rgb), rgb2: rgb3(t.flowers.rgb2) ?? rgb3(t.flowers.rgb), leaf: rgb3(t.flowers.leaf) ?? [.05, .1, .035], size: clamp(t.flowers.size_m, .012, .04, .022), side: clamp(t.flowers.side, -1, 1, -1), spread: clamp(t.flowers.spread, .3, 3.2, 1.2) } : null;
  const bow = t.bow && rgb3(t.bow.rgb) ? { rgb: rgb3(t.bow.rgb), side: clamp(t.bow.side, -1, 1, 1), size: clamp(t.bow.size_m, .03, .09, .05) } : null;
  return plumes || flowers || bow ? { plumes, flowers, bow } : null;
}

/** A hat's spec, with its numbers held to what a hat of 1812 (or a lady's of 1904) could be. */
export function hatSpec(hat) {
  if (!hat || typeof hat !== 'object') return null;
  const kind = ['round', 'straw', 'knit', ...LADY_HATS].includes(hat.kind) ? hat.kind : null;
  if (!kind || !Array.isArray(hat.rgb) || hat.rgb.length !== 3) return null;
  const clamp = (v, lo, hi, d) => (Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d);
  const lady = LADY_HATS.includes(kind);
  return {
    kind, rgb: hat.rgb, band: Array.isArray(hat.band) && hat.band.length === 3 ? hat.band : null,
    crown: lady ? clamp(hat.crown_m, .03, .12, { picture: .065, sailor: .07, toque: .085 }[kind]) : clamp(hat.crown_m, .04, .19, kind === 'straw' ? .085 : .13),
    brim: kind === 'toque' ? 0 : lady ? clamp(hat.brim_m, .03, .17, kind === 'sailor' ? .065 : .12) : clamp(hat.brim_m, 0, .13, kind === 'straw' ? .085 : .06),
    taper: clamp(hat.taper, .78, 1.12, kind === 'sailor' ? 1 : .94),
    roll: clamp(hat.roll, 0, 1, 0),
    droop: clamp(hat.droop, -.4, .6, 0),
    tilt: clamp(hat.tilt, -.03, .03, 0),
    tail: clamp(hat.tail_m, 0, .2, .09),
    // T-3553: how high above the brow a lady's hat is perched on her dressed hair, how far one
    // side of the brim is turned up (+ her left, - her right), how wide a toque puffs out.
    perch: lady ? clamp(hat.perch_m, 0, .06, .03) : 0,
    cock: lady ? clamp(hat.cock, -1, 1, 0) : 0,
    puff: kind === 'toque' ? clamp(hat.puff, 0, .5, .25) : 0,
    finish: lady ? clamp(hat.finish, .3, 1, kind === 'sailor' ? .7 : kind === 'toque' ? .55 : .8) : null,
    trim: lady ? trimSpec(hat.trim, clamp) : null,
  };
}

/**
 * The hat's geometry in metres, in the face's frame carried to the cap's bind pose by R (as
 * the headcloth's). Rings of (x, y, z) about the head's vertical axis, closed at the crown,
 * with the brim outward from the band; two groups when the hat has a band of another colour.
 */
function lathe(spec, pts, f, seg) {
  const cz = -.08;
  // The band: level a little above the brow before, lower behind (as a hat sits), its radius
  // the head's there plus the hair's thickness under it.
  const front = .046 + spec.tilt + spec.perch, back = .022 + spec.tilt + spec.perch * 1.3;
  const bearings = Array.from({ length: seg }, (_, k) => -Math.PI + 2 * Math.PI * k / seg);
  const bandY = th => back + (front - back) * (1 + Math.cos(th)) / 2;
  const clear = spec.kind === 'knit' ? .006 : .009;
  const ring0 = smoothRing(bearings.map(th => radiusAt(pts, bandY(th), th, cz, seg)), .085).map(r => r + clear);
  const position = [], index = [], groupsAt = [];
  const P = (x, y, z) => { const p = f.o.clone().addScaledVector(f.x, x).addScaledVector(f.y, y).addScaledVector(f.z, z); position.push(p.x, p.y, p.z); return position.length / 3 - 1; };
  const ringAt = (fn) => bearings.map((th, k) => { const [r, y, dz = 0, dy = 0] = fn(th, k); return P(Math.sin(th) * r, y + dy, cz + dz + Math.cos(th) * r); });
  const strip = (a, b) => { for (let k = 0; k < seg; k++) { const k1 = (k + 1) % seg; index.push(a[k], b[k], a[k1], a[k1], b[k], b[k1]); } };
  const fan = (ring, c) => { for (let k = 0; k < seg; k++) index.push(ring[k], ring[(k + 1) % seg], c); };

  if (spec.kind === 'knit') {
    // Close over the crown: rings at the head's own radius, then a soft top falling back.
    const top = Math.max(.1, ...pts.filter(([x, , z]) => Math.hypot(x, z - cz) < .03).map(([, y]) => y));
    const rows = [];
    const heights = [0, .25, .5, .7, .85];
    rows.push(ringAt((th, k) => [ring0[k], bandY(th)]));
    for (const t of heights.slice(1)) {
      rows.push(ringAt((th, k) => {
        const y = bandY(th) + (top + .012 - bandY(th)) * t;
        const r = (radiusAt(pts, y, th, cz, seg) || ring0[k] * (1 - t * t)) + clear;
        return [Math.max(.02, r), y];
      }));
    }
    for (let j = 0; j + 1 < rows.length; j++) strip(rows[j], rows[j + 1]);
    // The fall: a tube from the crown back and down, narrowing to its end, each ring square
    // to the way the tube runs.
    const tail = spec.tail, steps = 5;
    const r1 = ring0.reduce((a, b) => a + b, 0) / seg * .5;
    const spine = u => [top + .006 + tail * (.32 * Math.sin(u * Math.PI * .75) - .45 * u * u), -tail * Math.sin(u * 1.35)];
    let prev = rows[rows.length - 1];
    for (let s = 1; s <= steps; s++) {
      const u = s / steps, [y, dz] = spine(u), [ya, za] = spine(u - .05), [yb, zb] = spine(Math.min(1, u + .05));
      const ty = yb - ya, tz = zb - za, tl = Math.hypot(ty, tz) || 1, ny = -tz / tl, nz = ty / tl;
      const r = r1 * (1 - .8 * u) + .004;
      const row = bearings.map(th => P(Math.sin(th) * r, y + Math.cos(th) * r * ny, cz + dz + Math.cos(th) * r * nz));
      strip(prev, row);
      prev = row;
    }
    const [ye, ze] = spine(1);
    fan(prev, P(0, ye - .004, cz + ze - .006));
    groupsAt.push(index.length);
  } else {
    const H = spec.crown;
    // The brim, from the band out; the roll lifts it at the sides, the droop lowers it before
    // and behind (a negative droop cocks it up there).
    const brimRows = [];
    const steps = spec.brim > .01 ? 4 : 0;
    for (let s = steps; s >= 0; s--) {
      const u = s / Math.max(1, steps);
      brimRows.push(ringAt((th, k) => {
        const side = Math.sin(th) ** 2, ends = Math.cos(th) ** 2;
        const out = spec.brim * u * (1 - .12 * ends * (spec.kind === 'straw' ? 0 : 1));
        let lift = spec.roll * spec.brim * .55 * side * u * u - spec.droop * spec.brim * .5 * ends * u ** 1.5;
        // T-3553: a picture hat's one side turned up, and its edge gently waved.
        if (spec.cock) lift += Math.abs(spec.cock) * spec.brim * .75 * Math.max(0, Math.sign(spec.cock) * Math.sin(th)) ** 2 * u ** 1.5;
        if (spec.kind === 'picture') lift += .006 * Math.sin(th * 5 + 1) * u * u;
        return [ring0[k] + out, bandY(th) - .002 + lift];
      }));
    }
    for (let j = 0; j + 1 < brimRows.length; j++) strip(brimRows[j], brimRows[j + 1]);
    // The band, then the crown up to its top: the felt's sides rise near straight and draw in
    // or flare by the taper; a straw crown rounds a little at its top.
    const bandH = Math.min(.03, H * .32);
    const base = brimRows[brimRows.length - 1];
    const bandTop = ringAt((th, k) => [ring0[k] * (1 + (spec.taper - 1) * bandH / H), bandY(th) + bandH]);
    if (spec.band) {
      groupsAt.push(index.length);
      strip(base, bandTop);
      groupsAt.push(index.length);
    } else strip(base, bandTop);
    const crownRows = [bandTop];
    const crownSteps = spec.kind === 'toque' ? [.2, .4, .6, .78, .92, 1] : [.55, .85, 1];
    for (const t of crownSteps) {
      crownRows.push(ringAt((th, k) => {
        const y = bandY(th) + bandH + (H - bandH) * t;
        if (spec.kind === 'toque') {
          // Ruched silk puffed out round the hair and drawn in over the top.
          const puff = 1 + spec.puff * Math.sin(Math.PI * Math.min(1, t * 1.15)) + .03 * Math.sin(th * 9 + t * 7);
          return [ring0[k] * puff * (t === 1 ? .55 : 1), y - (t === 1 ? (H - bandH) * .05 : 0)];
        }
        const shoulder = spec.kind === 'straw' && t === 1 ? .9 : spec.kind === 'sailor' && t === 1 ? .97 : t === 1 ? .985 : 1;
        return [ring0[k] * (1 + (spec.taper - 1) * (bandH + (H - bandH) * t) / H) * shoulder, y];
      }));
    }
    for (let j = 0; j + 1 < crownRows.length; j++) strip(crownRows[j], crownRows[j + 1]);
    const topY = (front + back) / 2 + H + (spec.kind === 'straw' ? .008 : spec.kind === 'sailor' ? 0 : .003);
    fan(crownRows[crownRows.length - 1], P(0, topY, cz - .003));
    if (!spec.band) groupsAt.push(index.length);
  }
  // T-3553: the trimming, as its own small mesh laid on the band and crown.
  const trim = spec.trim ? trimming(spec, { ring0, bandY, bearings, cz, H: spec.crown, f, seg }) : null;
  // The band is its own mesh on the same points: one material a mesh, as every reader of a
  // worn hat (the hair's cut, the greeting's brim) takes a mesh's material by its name.
  const pos = new THREE.Float32BufferAttribute(position, 3);
  const make = (ix) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', pos); g.setIndex(ix); g.computeVertexNormals(); return g; };
  if (spec.band && spec.kind !== 'knit') {
    const [b0, b1] = groupsAt;
    return { hat: make([...index.slice(0, b0), ...index.slice(b1)]), band: make(index.slice(b0, b1)), trim };
  }
  return { hat: make(index), band: null, trim };
}

/** The ring's radius at bearing th, from the band's samples (linear between bearings). */
function ringRadius(ring0, th, seg) {
  const u = ((th + Math.PI) / (2 * Math.PI)) * seg;
  const k = Math.floor(u), t = u - k;
  return ring0[((k % seg) + seg) % seg] * (1 - t) + ring0[(((k + 1) % seg) + seg) % seg] * t;
}

/**
 * T-3553: a lady's hat's trimming, vertex-coloured, in the face's frame: ostrich plumes (a
 * curled, tapering vane with a waved edge, laid from the band over the crown and down behind),
 * silk flowers (cupped petals round a centre, with two leaves) clustered on one side, a ribbon
 * bow's two loops and its knot.
 */
function trimming(spec, { ring0, bandY, cz, H, f, seg }) {
  const position = [], color = [], index = [];
  const P = (x, y, z, rgb) => {
    const p = f.o.clone().addScaledVector(f.x, x).addScaledVector(f.y, y).addScaledVector(f.z, z);
    position.push(p.x, p.y, p.z); color.push(...rgb); return position.length / 3 - 1;
  };
  const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const at = (th, up = 0, out = 0) => {
    const r = ringRadius(ring0, th, seg) + out;
    return [Math.sin(th) * r, bandY(th) + up, cz + Math.cos(th) * r];
  };
  const t = spec.trim;
  if (t.plumes) {
    // Each plume lies round the crown from one side of the front toward the back, rising off
    // the band and curling down over the brim behind: a soft, full body of fluffed barbs
    // (a flattened tube, puffed and tapering), its colour stippled as a plume's barbs catch light.
    const up = new THREE.Vector3(0, 1, 0), RING = 8;
    for (let j = 0; j < t.plumes.n; j++) {
      const sgn = t.plumes.side >= 0 ? 1 : -1;
      const th0 = sgn * (.3 + .45 * j), L = t.plumes.length * (1 - .12 * j), N = 18, w0 = .032 * (1 - .1 * j);
      const span = L / Math.max(.06, ringRadius(ring0, th0, seg) * 1.15);
      const spine = (u) => {
        const th = th0 + sgn * span * u;
        const w = w0 * Math.sin(Math.PI * Math.min(1, .1 + u * .92)) ** .5;
        const r = ringRadius(ring0, th, seg) * (1 + (spec.taper - 1) * .7) + w * .6 + .004;
        const y = bandY(th) + H * (.35 + .55 * Math.sin(Math.PI * Math.min(1, u * .9))) - H * 1.2 * u ** 3 + w * .5;
        return { th, w, p: new THREE.Vector3(Math.sin(th) * r, y, cz + Math.cos(th) * r) };
      };
      let prev = null;
      for (let i = 0; i <= N; i++) {
        const u = i / N, { th, w, p } = spine(u);
        const radial = new THREE.Vector3(Math.sin(th), 0, Math.cos(th));
        const across = radial.clone().multiplyScalar(.8).addScaledVector(up, .6).normalize();
        const thick = across.clone().cross(new THREE.Vector3(Math.cos(th), 0, -Math.sin(th))).normalize();
        const row = [];
        for (let k = 0; k < RING; k++) {
          const a = (k / RING) * Math.PI * 2;
          const fluff = 1 + .18 * Math.sin(a * 3 + i * 1.7 + j);
          const q = p.clone().addScaledVector(across, Math.cos(a) * w * fluff).addScaledVector(thick, Math.sin(a) * w * .45 * fluff)
            .addScaledVector(up, -Math.abs(Math.cos(a)) * w * .25);
          const tone = .8 + .35 * rnd(i * RING + k + 97 * j) + .1 * Math.sin(a);
          row.push(P(q.x, q.y, q.z, t.plumes.rgb.map((c) => Math.min(1, c * tone))));
        }
        if (prev) for (let k = 0; k < RING; k++) { const k1 = (k + 1) % RING; index.push(prev[k], row[k], prev[k1], prev[k1], row[k], row[k1]); }
        else { const c = P(p.x, p.y, p.z, t.plumes.rgb); for (let k = 0; k < RING; k++) index.push(c, row[(k + 1) % RING], row[k]); }
        prev = row;
      }
      const end = spine(1).p, c = P(end.x, end.y, end.z, t.plumes.rgb);
      for (let k = 0; k < RING; k++) index.push(prev[k], c, prev[(k + 1) % RING]);
    }
  }
  if (t.flowers) {
    const { n, size, side, spread } = t.flowers;
    for (let j = 0; j < n; j++) {
      const th = side * (spread * .5 + (j / Math.max(1, n - 1) - .5) * spread * .6) + (rnd(j) - .5) * .25;
      const [cx, cy, cz2] = at(th, .006 + rnd(j + 7) * .02, .012);
      const nrm = new THREE.Vector3(Math.sin(th), .7, Math.cos(th)).normalize();
      const a = new THREE.Vector3(0, 1, 0).cross(nrm).normalize();
      if (a.lengthSq() < .1) a.set(1, 0, 0);
      const b = nrm.clone().cross(a).normalize();
      const r = size * (.75 + .5 * rnd(j + 3)), rgb = j % 3 === 2 ? t.flowers.rgb2 : t.flowers.rgb;
      // Two leaves under it.
      for (const lsign of [1, -1]) {
        const lt = new THREE.Vector3(cx, cy, cz2).addScaledVector(a, lsign * r * 1.5).addScaledVector(nrm, -.004);
        const q0 = P(cx, cy, cz2, t.flowers.leaf);
        const q1 = P(...lt.clone().addScaledVector(b, r * .45).toArray(), t.flowers.leaf);
        const q2 = P(...lt.clone().addScaledVector(a, lsign * r * .6).toArray(), t.flowers.leaf);
        const q3 = P(...lt.clone().addScaledVector(b, -r * .45).toArray(), t.flowers.leaf);
        index.push(q0, q1, q2, q0, q2, q3);
      }
      const centre = P(...new THREE.Vector3(cx, cy, cz2).addScaledVector(nrm, r * .25).toArray(), rgb.map((c) => c * .55));
      const petals = 10, rim = [];
      for (let k = 0; k < petals; k++) {
        const ang = (k / petals) * Math.PI * 2;
        const rr = r * (.7 + .3 * Math.abs(Math.cos(ang * 2.5)));
        const pt = new THREE.Vector3(cx, cy, cz2).addScaledVector(a, Math.cos(ang) * rr).addScaledVector(b, Math.sin(ang) * rr).addScaledVector(nrm, r * .35);
        rim.push(P(pt.x, pt.y, pt.z, rgb.map((c) => Math.min(1, c * (1.05 + .2 * (k % 2))))));
      }
      for (let k = 0; k < petals; k++) index.push(centre, rim[k], rim[(k + 1) % petals]);
    }
  }
  if (t.bow) {
    const { side, size } = t.bow;
    const th = side * 1.25;
    const [cx, cy, cz2] = at(th, .012, .006);
    const out = new THREE.Vector3(Math.sin(th), 0, Math.cos(th));
    const along = new THREE.Vector3(Math.cos(th), 0, -Math.sin(th));
    // Two loops, front and back of the knot, each a flattened ribbon ring.
    for (const dir of [1, -1]) {
      const N = 12, w = size * .45, ring = [];
      for (let i = 0; i <= N; i++) {
        const a = (i / N) * Math.PI * 2;
        const c = new THREE.Vector3(cx, cy, cz2).addScaledVector(along, dir * size * (.5 - .5 * Math.cos(a))).addScaledVector(new THREE.Vector3(0, 1, 0), size * .35 * Math.sin(a)).addScaledVector(out, .004);
        ring.push([P(...c.clone().addScaledVector(out, w * .5).toArray(), t.bow.rgb), P(...c.clone().addScaledVector(out, -w * .5).toArray(), t.bow.rgb.map((v) => v * .8))]);
      }
      for (let i = 0; i < N; i++) index.push(ring[i][0], ring[i][1], ring[i + 1][0], ring[i + 1][0], ring[i][1], ring[i + 1][1]);
    }
  }
  if (!index.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(position, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(color, 3));
  g.setIndex(index);
  g.computeVertexNormals();
  return g;
}

/** The finish of each kind's material: felt is matte, straw a little glossier. */
const FINISH = { round: .9, straw: .72, knit: .97, picture: .8, sailor: .7, toque: .55 };

/**
 * Put `hat` (a dress record's spec) on the figure at `root`. Returns { mesh, materials } or null
 * where nothing can be built (no cap, no head bone, an unknown kind).
 */
export function dressHat(root, hat, { person = null, lod = 0 } = {}) {
  const spec = hatSpec(hat);
  if (!root || !spec) return null;
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
  let cache = made.get(hair.geometry);
  if (!cache) {
    cache = new Map();
    made.set(hair.geometry, cache);
    hair.geometry.addEventListener('dispose', () => { for (const e of cache.values()) { e.geometry.dispose(); e.band?.dispose(); e.trim?.dispose(); } cache.clear(); });
  }
  const seg = SEGMENTS[Math.min(SEGMENTS.length - 1, Math.max(0, lod | 0))];
  const key = `${person ?? 'anon'}|${JSON.stringify(spec)}|${seg}`;
  let entry = cache.get(key);
  if (!entry) {
    const f = headFrame(hair, root);
    if (!f) return null;
    const pts = headPoints(hair, skin?.skeleton ? skin : null, root, f);
    if (pts.length < 30) return null;
    const { hat: geometry, band, trim } = lathe(spec, pts, f, seg);
    const rigid = (g) => {
      const n = g.attributes.position.count;
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Uint16Array(n * 4).map((_, i) => (i % 4 ? 0 : headBone)), 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(new Float32Array(n * 4).map((_, i) => (i % 4 ? 0 : 1)), 4));
    };
    const n = geometry.attributes.position.count;
    const skinIndex = new THREE.Uint16BufferAttribute(new Uint16Array(n * 4).map((_, i) => (i % 4 ? 0 : headBone)), 4);
    const skinWeight = new THREE.Float32BufferAttribute(new Float32Array(n * 4).map((_, i) => (i % 4 ? 0 : 1)), 4);
    for (const g of [geometry, band]) if (g) { g.setAttribute('skinIndex', skinIndex); g.setAttribute('skinWeight', skinWeight); }
    if (trim) rigid(trim);
    entry = { geometry, band, trim, R: metricSurface(hair, root).R };
    cache.set(key, entry);
  }
  const bind = hair.bindMatrix.clone().multiply(entry.R.clone().invert());
  const wear = (geometry, material) => {
    const m = new THREE.SkinnedMesh(geometry, material);
    m.name = material.name.replace(/^headwear__/, 'headwear_');
    m.frustumCulled = false;
    m.castShadow = true;
    m.receiveShadow = hair.receiveShadow;
    m.bind(hair.skeleton, bind);
    hair.parent.add(m);
    return m;
  };
  const materials = [new THREE.MeshStandardMaterial({ name: `headwear__${spec.kind}_hat_t3522`,
    color: new THREE.Color().setRGB(...spec.rgb, THREE.LinearSRGBColorSpace), roughness: spec.finish ?? FINISH[spec.kind], metalness: 0, side: THREE.DoubleSide })];
  const m = wear(entry.geometry, materials[0]);
  // The band is named so the hair's cut passes over it (human-hair.js skips /band/): the crown is the hat.
  if (entry.band) {
    materials.push(new THREE.MeshStandardMaterial({ name: `headwear__${spec.kind}_hat_band_t3522`,
      color: new THREE.Color().setRGB(...spec.band, THREE.LinearSRGBColorSpace), roughness: .6, metalness: 0, side: THREE.DoubleSide }));
    wear(entry.band, materials[1]);
  }
  // T-3553: plumes, flowers and bow, in their own colours on one material.
  if (entry.trim) {
    materials.push(new THREE.MeshStandardMaterial({ name: `accessory__${spec.kind}_hat_trim_t3553`,
      vertexColors: true, roughness: .78, metalness: 0, side: THREE.DoubleSide }));
    wear(entry.trim, materials[materials.length - 1]);
  }
  return { mesh: m, materials };
}
