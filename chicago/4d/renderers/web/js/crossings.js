/**
 * crossings.js — the 1812 river's boats, and Cross (T-3510).
 *
 * The owner, 2026-11-08: *"In 1812 there are no bridges so can you in all scenes and areas
 * where we might want to cross ... provide a small period appropriate boat or canoe that
 * looks photographic correct and allow me to walk up to the boat and interact is board and
 * cross river and you run that sequence, hop in the boat and then you rows across the river
 * and then you hop out of the boat. The boats should look a bit different, different wood
 * weathering and slightly different shape"*, and *"Don't add a bunch of docks, in most cases
 * you should board from the bank other than maybe around the fort"*.
 *
 * WHAT IT DRAWS. The boats `tools/lay_crossing_boats_1812.py` lays in
 * `data/boats/crossings_1812.json`: dugouts (the pirogues of the trade), elm-bark canoes and
 * small plank skiffs, each drawn up on a bank with its bow on the ground and its stern afloat
 * (one rides at the fort's wharf). Every hull is lofted here from its own figures — length,
 * beam, depth, sheer, rocker, fullness, the turn of its ends — so no two are alike, and
 * coloured by its own `look`: the wood's tone, how far it has silvered, the wet band at its
 * waterline, a green cast in the bilge, and a seeded run of small differences plank by plank.
 *
 * WHAT IT WEARS, AND WHY IT ADDS NO TEXTURE. 1812's phone memory is the tightest in the
 * town. The wood is the hewn-log face the log houses' walls already hold on the GPU
 * (wall-relief.js `loadedSubstrate`): its normal and its packed `orl` (occlusion, roughness,
 * and the albedo's luminance over its mean), with the colour on the vertex — the walls' own
 * recipe, so a dugout's adze facets and checks are the same wood the cabins are built of.
 * The bark is the camp's elm bark (camp-surfaces.js `campSheet`), the lodges' own sheets.
 * Where either is not loaded the hull keeps its vertex colour alone, never white.
 *
 * CROSS. Each boat is an Interact thing (interact.js) with two states, the two banks. Its
 * one action is a sequence: step in, push off, paddle (or row) across, run ashore, step
 * out — and the boat stays on the bank it was taken to, so it can take you back. While it
 * runs the visitor is IN the boat: `holdVisitor(walker)`, called by main.js after the walk
 * step, puts the eye on the seat every frame; the visitor may look round freely. The boat
 * rides the 1812 water plane (Z = 0) at its own draft, rolls a little with each stroke,
 * and the paddle (or the oars) work at the side where a visitor sees them.
 *
 * DRAW. Boats at rest are merged into one mesh per material per neighbourhood (the fort,
 * the creek mouth, the forks, Lee's Place …), frustum-culled and dropped past DRAW_M; the
 * boat being crossed in is drawn on its own. A boat answers a pick with a card built from
 * its own record.
 */

import * as THREE from 'three';
import { enuToWorld } from './terrain.js';
import { bearingToYaw } from './angles.js';
import { loadedSubstrate } from './wall-relief.js';
import { campSheet } from './camp-surfaces.js';

const DEG = Math.PI / 180;
/** The 1812 water surface (the heightfield's zero). */
const WATER_Y = 0;
/** Boats further than this from the eye are not drawn (they are a few pixels long there). */
const DRAW_M = { full: 650, balanced: 500, light: 320 };
/** Neighbourhoods: boats at rest within this of each other share a mesh. */
/** The trodden landing around a drawn-up boat: metres past its ends, and to each side. */
const LANDING_PAD_M = 1.2;
const LANDING_SIDE_M = 1.6;
const CLUSTER_M = 220;
/** attested · inferred · reconstructed, as the confidence view reads them. A boat whose
 *  existence a source states but no picture shows is graded inferred (AGENTS.md rule 12). */
const GRADE = { attested: 0.5, inferred: 0.5, reconstructed: 1 };

/** Seconds a step takes. The crossing itself takes its own path over the record's speed. */
const STEP_S = { in: 1.7, off: 3.2, ashore: 2.8, out: 1.7 };
/** The visitor's eye above the keel when seated (kneeling in a canoe or pirogue, on a thwart in a skiff). */
const SEAT_EYE_M = { dugout: 0.92, bark_canoe: 0.9, skiff: 1.08 };
/** Where the visitor sits, as a share of the half-length from midships (negative = aft). */
const SEAT_AT = { dugout: -0.5, bark_canoe: -0.52, skiff: -0.12 };
/** One stroke, seconds. */
const STROKE_S = { dugout: 1.7, bark_canoe: 1.5, skiff: 2.2 };

/* -------------------------------------------------------------------------- */
/* small numbers                                                               */
/* -------------------------------------------------------------------------- */

/** A seeded run of numbers in [0, 1): the same boat looks the same on every load. */
function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => t * t * (3 - 2 * t);
/** Shortest turn from bearing a to bearing b, degrees. */
const turn = (a, b) => ((b - a + 540) % 360) - 180;

/** sRGB 0-1 triple to linear. */
function linear([r, g, b]) {
  const c = new THREE.Color().setRGB(r, g, b, THREE.SRGBColorSpace);
  return [c.r, c.g, c.b];
}

/* -------------------------------------------------------------------------- */
/* the hull                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * The hull's lines, in the boat's frame: x forward (bow +L/2), y up (the keel at midships
 * is y = 0), z to starboard. `t` runs -1 (stern) to 1 (bow).
 */
function linesFor(kind, h) {
  const L = h.length_m, B = h.beam_m, D = h.depth_m;
  const sheer = h.sheer_m ?? 0.08, rocker = h.rocker_m ?? 0.05;
  if (kind === 'dugout') {
    const p = h.fullness ?? 3.5;
    const endFrac = clamp((h.end_m ?? 0.3) / B, 0.15, 0.7);
    return {
      L, B, D, kind,
      half: (t) => (B / 2) * (endFrac + (1 - endFrac) * Math.pow(Math.max(0, 1 - Math.abs(t) ** p), 0.5)),
      keel: (t) => rocker * Math.abs(t) ** 3 + 0.22 * D * Math.max(0, (Math.abs(t) - 0.82) / 0.18) ** 2,
      gun: (t) => D + sheer * t * t,
      // A log's section: a round bottom flattening a little under the floor.
      section: (u) => [Math.sin(u), 1 - Math.cos(u) ** 0.9],
      rake: 0.07,
      inner: 0.86,
      floor: Math.max(0.07, (h.thick_m ?? 0.05) * 1.6),
    };
  }
  if (kind === 'bark_canoe') {
    const p = h.fullness ?? 1.6;
    const up = h.upturn_m ?? 0.22;
    return {
      L, B, D, kind,
      half: (t) => (B / 2) * Math.pow(Math.max(0, 1 - Math.abs(t) ** (p + 0.6)), 0.62),
      keel: (t) => rocker * t * t + 0.5 * D * Math.max(0, (Math.abs(t) - 0.78) / 0.22) ** 2.2,
      gun: (t) => D + sheer * t * t + up * Math.max(0, (Math.abs(t) - 0.66) / 0.34) ** 2.4,
      // Bark sheet over a frame: a flattish floor and full, slightly rounded sides.
      section: (u) => [Math.sign(u) * Math.abs(Math.sin(u)) ** 0.75, (1 - Math.cos(u)) ** 1.25],
      rake: 0.03,
      inner: 0.965,
      floor: h.thick_m ?? 0.012,
    };
  }
  // The skiff: flat bottom, a hard chine, flared straight sides, a pointed bow, a transom.
  const tr = h.transom ?? 0.6;
  const flare = h.flare ?? 0.25;
  return {
    L, B, D, kind,
    half: (t) => (t >= 0
      ? (B / 2) * Math.pow(Math.max(0, 1 - t ** 1.9), 0.55)
      : (B / 2) * (1 - (1 - tr) * Math.abs(t) ** 2.2)),
    keel: (t) => (t >= 0 ? 0.42 * D * Math.max(0, (t - 0.55) / 0.45) ** 1.8 : rocker * t * t),
    gun: (t) => D + sheer * (t >= 0 ? t * t * 1.15 : t * t * 0.6),
    chine: 1 - flare,
    rake: 0.0,
    inner: 1,
    floor: h.thick_m ?? 0.03,
  };
}

/** A growable attribute buffer for one material's triangles. */
function buffer() {
  return { pos: [], nrm: [], uv: [], col: [], conf: [] };
}

function pushTri(buf, a, b, c, ca, cb, cc, uva, uvb, uvc, level) {
  const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  let nx = e1[1] * e2[2] - e1[2] * e2[1];
  let ny = e1[2] * e2[0] - e1[0] * e2[2];
  let nz = e1[0] * e2[1] - e1[1] * e2[0];
  const l = Math.hypot(nx, ny, nz);
  if (l < 1e-10) return;
  nx /= l; ny /= l; nz /= l;
  buf.pos.push(...a, ...b, ...c);
  buf.nrm.push(nx, ny, nz, nx, ny, nz, nx, ny, nz);
  buf.uv.push(...uva, ...uvb, ...uvc);
  buf.col.push(...ca, ...cb, ...cc);
  buf.conf.push(level, level, level);
}

/**
 * A grid of points rows x cols, quads between neighbours. `P(i, j)` -> [x, y, z],
 * `C(i, j)` -> colour, `UV(i, j)` -> [u, v]. Smooth normals are made later by the
 * caller's geometry (we keep flat normals for the skiff's planking, smooth for the rest).
 */
function pushGrid(buf, rows, cols, P, C, UV, level, flip = false) {
  for (let i = 0; i < rows - 1; i++) {
    for (let j = 0; j < cols - 1; j++) {
      const a = P(i, j), b = P(i + 1, j), c = P(i + 1, j + 1), d = P(i, j + 1);
      const ca = C(i, j), cb = C(i + 1, j), cc = C(i + 1, j + 1), cd = C(i, j + 1);
      const ua = UV(i, j), ub = UV(i + 1, j), uc = UV(i + 1, j + 1), ud = UV(i, j + 1);
      if (flip) {
        pushTri(buf, a, c, b, ca, cc, cb, ua, uc, ub, level);
        pushTri(buf, a, d, c, ca, cd, cc, ua, ud, uc, level);
      } else {
        pushTri(buf, a, b, c, ca, cb, cc, ua, ub, uc, level);
        pushTri(buf, a, c, d, ca, cc, cd, ua, uc, ud, level);
      }
    }
  }
}

/** A box in the boat's frame: centre, half-sizes, turned `yaw` about y. Wood-grained along its long axis. */
function pushBox(buf, cx, cy, cz, hx, hy, hz, col, level, tileM, yaw = 0) {
  const cs = Math.cos(yaw), sn = Math.sin(yaw);
  const P = (sx, sy, sz) => {
    const x = sx * hx, z = sz * hz;
    return [cx + x * cs - z * sn, cy + sy * hy, cz + x * sn + z * cs];
  };
  const faces = [
    [[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]],
    [[-1, -1, 1], [-1, 1, 1], [-1, 1, -1], [-1, -1, -1]],
    [[-1, 1, -1], [-1, 1, 1], [1, 1, 1], [1, 1, -1]],
    [[-1, -1, 1], [-1, -1, -1], [1, -1, -1], [1, -1, 1]],
    [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
    [[1, -1, -1], [-1, -1, -1], [-1, 1, -1], [1, 1, -1]],
  ];
  const long = hx >= hz ? 0 : 2;
  for (const f of faces) {
    const pts = f.map(([a, b, c]) => P(a, b, c));
    const uv = f.map(([a, b, c]) => {
      const along = long === 0 ? a * hx : c * hz;
      const across = b * hy + (long === 0 ? c * hz : a * hx);
      return [along / tileM, across / tileM];
    });
    pushTri(buf, pts[0], pts[1], pts[2], col, col, col, uv[0], uv[1], uv[2], level);
    pushTri(buf, pts[0], pts[2], pts[3], col, col, col, uv[0], uv[2], uv[3], level);
  }
}

/** A round pole along a polyline of [x, y, z] points (gunwales, paddle shafts). */
function pushPole(buf, pts, r, col, level, tileM, sides = 6) {
  for (let k = 0; k < pts.length - 1; k++) {
    const a = pts[k], b = pts[k + 1];
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const len = Math.hypot(...d) || 1;
    const t = d.map((v) => v / len);
    const ref = Math.abs(t[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    let u = [t[1] * ref[2] - t[2] * ref[1], t[2] * ref[0] - t[0] * ref[2], t[0] * ref[1] - t[1] * ref[0]];
    const ul = Math.hypot(...u); u = u.map((v) => v / ul);
    const w = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]];
    const ring = (p, s) => {
      const ang = (s / sides) * Math.PI * 2;
      const c = Math.cos(ang) * r, sn = Math.sin(ang) * r;
      return [p[0] + u[0] * c + w[0] * sn, p[1] + u[1] * c + w[1] * sn, p[2] + u[2] * c + w[2] * sn];
    };
    const u0 = (k * len) / tileM, u1 = ((k + 1) * len) / tileM;
    for (let s = 0; s < sides; s++) {
      const p0 = ring(a, s), p1 = ring(b, s), p2 = ring(b, s + 1), p3 = ring(a, s + 1);
      const v0 = (s * r * 1.05) / tileM, v1 = ((s + 1) * r * 1.05) / tileM;
      pushTri(buf, p0, p1, p2, col, col, col, [u0, v0], [u1, v0], [u1, v1], level);
      pushTri(buf, p0, p2, p3, col, col, col, [u0, v0], [u1, v1], [u0, v1], level);
    }
  }
}

/**
 * The boat's colours: `look.tone` silvered by `grey`, wet-dark at the waterline by `dark`,
 * green in the bilge by `moss`, and each plank-or-station a little different by `seed`.
 * For a bark hull the colour MULTIPLIES the bark's own sheet, so it is a tint near white.
 */
function palette(look, kind, tinted) {
  const tone = linear(look.tone ?? [0.45, 0.4, 0.33]);
  const grey = linear([0.5, 0.48, 0.45]);
  const g = clamp(look.grey ?? 0.4, 0, 1);
  const base = tone.map((v, i) => lerp(v, grey[i], g * 0.75));
  const barkRef = linear([0.36, 0.31, 0.26]);
  const r = rng((look.seed ?? 1) * 7919);
  const jitter = Array.from({ length: 64 }, () => 0.86 + r() * 0.28);
  const wet = clamp(look.dark ?? 0.5, 0, 1);
  const moss = clamp(look.moss ?? 0, 0, 1);
  const mossC = linear([0.27, 0.31, 0.2]);
  /**
   * @param k   which plank or station (an index into the jitter run)
   * @param y   height in the boat's frame
   * @param inside  the inner face (the bilge)
   */
  return (k, y, inside = false, draftY = 0.15) => {
    let c = base.slice();
    if (tinted) c = c.map((v, i) => clamp(v / barkRef[i], 0.55, 1.6));
    const j = jitter[((k % 64) + 64) % 64];
    c = c.map((v) => v * j);
    if (!inside && y < draftY + 0.06) {
      const f = wet * clamp(1 - (y - draftY + 0.06) / 0.12, 0, 1);
      c = c.map((v) => v * (1 - 0.45 * f));
    }
    if (inside && y < 0.12 && moss > 0) {
      const f = moss * clamp(1 - y / 0.12, 0, 1) * 0.6;
      c = c.map((v, i) => lerp(v, mossC[i] * (tinted ? 1 / barkRef[i] : 1), f));
    }
    if (inside) c = c.map((v) => v * (kind === 'bark_canoe' ? 1.12 : 0.9));
    return c;
  };
}

/**
 * Build one boat in its own frame. Returns `{ wood, bark, seat, paddles, extent }` where
 * `wood`/`bark` are attribute buffers (bark only for a bark canoe), `seat` the eye's
 * point, and `paddles` the geometry of what is worked while crossing (built separately so
 * it can move).
 */
export function buildBoat(boat, { tileWood = 4.08, tileBark = 1.2, coarse = false } = {}) {
  const h = boat.hull;
  const kind = boat.kind;
  const lines = linesFor(kind, h);
  const { L } = lines;
  const level = GRADE[boat.existence?.confidence] ?? 1;
  const bark = kind === 'bark_canoe';
  const outerBuf = bark ? buffer() : null;
  const wood = buffer();
  const hullBuf = bark ? outerBuf : wood;
  const colourHull = palette(boat.look ?? {}, kind, bark);
  const colourWood = palette({ ...(boat.look ?? {}), tone: bark ? [0.5, 0.42, 0.32] : boat.look?.tone }, kind, false);
  const tile = bark ? tileBark : tileWood;
  const draftY = h.draft_m ?? 0.15;
  const thick = h.thick_m ?? 0.04;

  const S = coarse ? 20 : 34;                 // stations stern to bow
  const K = coarse ? 6 : 10;                  // points from keel to one gunwale

  // Station t values, crowded toward the ends where the lines turn.
  const ts = Array.from({ length: S + 1 }, (_, i) => {
    const a = -1 + (2 * i) / S;
    return Math.sign(a) * (1 - (1 - Math.abs(a)) ** 1.25);
  });

  /** A point of the hull: station t, girth u (-pi/2 port gunwale .. +pi/2 starboard), offset in. */
  const point = (t, u, inset = 0) => {
    const hb = Math.max(0, lines.half(t) - inset);
    const yk = lines.keel(t) + (inset > 0 ? lines.floor : 0);
    const yg = lines.gun(t);
    let z, y;
    if (kind === 'skiff') {
      // Flat floor to the chine at |u| = 0.45 pi, then the flared side up to the gunwale.
      const cb = hb * lines.chine;
      const au = Math.abs(u), su = Math.sign(u);
      if (au <= 0.45 * Math.PI) { z = su * cb * (au / (0.45 * Math.PI)); y = yk; } else {
        const f = (au - 0.45 * Math.PI) / (0.55 * Math.PI);
        z = su * lerp(cb, hb, f); y = lerp(yk, yg, f);
      }
    } else {
      const [sz, sy] = lines.section(u);
      z = hb * sz; y = yk + (yg - yk) * Math.min(1, sy);
    }
    const v = clamp((y - lines.keel(t)) / Math.max(0.01, yg - lines.keel(t)), 0, 1);
    const x = t * (L / 2) * (1 - lines.rake * (1 - v) * Math.abs(t) ** 4);
    return [x, y, z];
  };
  const us = Array.from({ length: 2 * K + 1 }, (_, j) => -Math.PI / 2 + (Math.PI * j) / (2 * K));
  /** Girth in metres from the port gunwale, for the v of the uv. */
  const girth = (pts) => {
    const g = [0];
    for (let j = 1; j < pts.length; j++) g.push(g[j - 1] + Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1], pts[j][2] - pts[j - 1][2]));
    return g;
  };

  // --- outer skin ------------------------------------------------------------------
  const outer = ts.map((t) => us.map((u) => point(t, u)));
  const outerG = outer.map(girth);
  // A skiff's planks run in strakes: the colour steps every plank width up the side.
  const strake = (i, j) => (kind === 'skiff' ? Math.floor(Math.abs(j - K) / Math.max(1, K / 4)) : Math.floor(i / 3));
  pushGrid(hullBuf, S + 1, 2 * K + 1,
    (i, j) => outer[i][j],
    (i, j) => colourHull(strake(i, j) + (j < K ? 17 : 0), outer[i][j][1], false, draftY),
    (i, j) => [outer[i][j][0] / tile, outerG[i][j] / tile],
    level, true);

  // --- inner skin, ends and rim -----------------------------------------------------
  const tIn = kind === 'skiff' ? 0.985 : lines.inner;
  const inTs = ts.filter((t) => Math.abs(t) <= tIn);
  if (inTs[0] > -tIn) inTs.unshift(-tIn);
  if (inTs[inTs.length - 1] < tIn) inTs.push(tIn);
  const innerT = inTs;
  const inner = innerT.map((t) => us.map((u) => point(t, u, thick)));
  const innerG = inner.map(girth);
  pushGrid(hullBuf, innerT.length, 2 * K + 1,
    (i, j) => inner[i][j],
    (i, j) => colourHull(strake(i, j) + 31, inner[i][j][1], true, draftY),
    (i, j) => [inner[i][j][0] / tile, innerG[i][j] / tile],
    level, false);

  // Rim: the top edge, outer gunwale to inner, both sides, along the inner run.
  const gunOuter = (t, side) => point(t, side * Math.PI / 2);
  const gunInner = (t, side) => point(t, side * Math.PI / 2, thick);
  for (const side of [-1, 1]) {
    pushGrid(hullBuf, innerT.length, 2,
      (i, j) => (j === 0 ? gunOuter(innerT[i], side) : gunInner(innerT[i], side)),
      (i) => colourHull(i + 5, 1, false, draftY),
      (i, j) => [gunOuter(innerT[i], side)[0] / tile, (j * thick) / tile],
      level, side > 0);
  }
  // The solid ends: a deck from port to starboard gunwale over each end beyond the inner run,
  // and the inner end wall closing the hollow.
  for (const end of [-1, 1]) {
    const tsEnd = ts.filter((t) => (end > 0 ? t >= tIn : t <= -tIn));
    const run = end > 0 ? [tIn, ...tsEnd] : [...tsEnd, -tIn];
    if (run.length >= 2) {
      pushGrid(hullBuf, run.length, 2,
        (i, j) => gunOuter(run[i], j === 0 ? -1 : 1),
        (i) => colourHull(i + 41, 1, false, draftY),
        (i, j) => [gunOuter(run[i], 1)[0] / tile, (j * lines.half(run[i]) * 2) / tile],
        level, end < 0);
    }
    // End wall: the inner section at t = end * tIn, fanned to its top centre.
    const t = end * tIn;
    const sec = us.map((u) => point(t, u, thick));
    const top = [sec[0][0], lines.gun(t), 0];
    for (let j = 0; j < sec.length - 1; j++) {
      const c = colourHull(j + 51, sec[j][1], true, draftY);
      const uvA = [sec[j][2] / tile, sec[j][1] / tile], uvB = [sec[j + 1][2] / tile, sec[j + 1][1] / tile];
      if (end > 0) pushTri(hullBuf, top, sec[j], sec[j + 1], c, c, c, [0, top[1] / tile], uvA, uvB, level);
      else pushTri(hullBuf, top, sec[j + 1], sec[j], c, c, c, [0, top[1] / tile], uvB, uvA, level);
    }
    // And where the outer skin does not close (a dugout's blunt end, the skiff's transom):
    const tt = end;
    const osec = us.map((u) => point(tt, u));
    const w = lines.half(tt);
    if (w > 0.02) {
      const otop = [osec[0][0], lines.gun(tt), 0];
      for (let j = 0; j < osec.length - 1; j++) {
        const c = colourHull(j + 61, osec[j][1], false, draftY);
        const uvA = [osec[j][2] / tile, osec[j][1] / tile], uvB = [osec[j + 1][2] / tile, osec[j + 1][1] / tile];
        if (end > 0) pushTri(hullBuf, otop, osec[j + 1], osec[j], c, c, c, [0, otop[1] / tile], uvB, uvA, level);
        else pushTri(hullBuf, otop, osec[j], osec[j + 1], c, c, c, [0, otop[1] / tile], uvA, uvB, level);
      }
    }
  }

  // --- fittings -----------------------------------------------------------------------
  const wc = (k, y) => colourWood(k, y, true, draftY);
  if (kind === 'bark_canoe') {
    // Gunwale poles, lashed outside the bark's top edge; thwarts; ribs inside.
    for (const side of [-1, 1]) {
      const pts = [];
      for (let i = 0; i <= 24; i++) {
        const t = -0.97 + (1.94 * i) / 24;
        const p = gunOuter(t, side);
        pts.push([p[0], p[1] - 0.012, p[2] + side * 0.012]);
      }
      pushPole(wood, pts, 0.022, wc(7 + side, 0.3), level, tileWood, 5);
    }
    for (const t of [-0.42, 0, 0.42]) {
      const hb = lines.half(t);
      pushBox(wood, t * L / 2, lines.gun(t) - 0.035, 0, 0.03, 0.012, hb - 0.01, wc(Math.round(t * 10) + 70, 0.3), level, tileWood, 0);
    }
    const ribs = coarse ? 7 : 13;
    for (let r = 0; r < ribs; r++) {
      const t = -0.8 + (1.6 * r) / (ribs - 1);
      const pts = us.map((u) => {
        const p = point(t, u, thick + 0.004);
        return p;
      });
      pushPole(wood, pts, 0.012, wc(r + 80, 0.1), level, tileWood, 4);
    }
  } else if (kind === 'dugout') {
    // A seat block across the stern quarter where the steersman kneels, and one forward.
    for (const t of [SEAT_AT.dugout - 0.04, 0.38]) {
      const hb = lines.half(t) - thick;
      pushBox(wood, t * L / 2, lines.keel(t) + lines.floor + 0.12, 0, 0.11, 0.025, hb - 0.02, wc(Math.round(t * 10) + 90, 0.2), level, tileWood, 0);
    }
  } else {
    // Thwarts, a stem post, a stern knee and two pairs of thole pins.
    for (const t of [SEAT_AT.skiff, 0.42, -0.72]) {
      const hb = lines.half(t) - thick;
      pushBox(wood, t * L / 2, lines.keel(t) + 0.34, 0, 0.12, 0.018, hb - 0.01, wc(Math.round(t * 10) + 100, 0.3), level, tileWood, 0);
    }
    const stemTop = point(1, 0);
    pushBox(wood, stemTop[0] - 0.03, (lines.keel(1) + lines.gun(1)) / 2 + 0.02, 0, 0.04, (lines.gun(1) - lines.keel(1)) / 2 + 0.03, 0.04, wc(110, 0.3), level, tileWood, 0);
    for (const side of [-1, 1]) {
      for (const dx of [-0.07, 0.07]) {
        const t = SEAT_AT.skiff + 0.18;
        const g = gunOuter(t, side);
        pushBox(wood, g[0] + dx, g[1] + 0.07, g[2] - side * 0.02, 0.012, 0.07, 0.012, wc(120, 0.4), level, tileWood, 0);
      }
    }
  }

  // --- what is worked: paddle (or oars), drawn on its own so it can move ---------------
  const paddle = buffer();
  const seatT = SEAT_AT[kind];
  const seatX = seatT * L / 2;
  const floorAtSeat = lines.keel(seatT) + lines.floor;
  if (kind === 'skiff') {
    // One oar along +x from its loom at the origin: the runtime pivots a copy at each thole.
    const len = Math.max(2.3, h.beam_m * 1.85);
    pushPole(paddle, [[-0.55, 0, 0], [len - 0.55 - 0.55, 0, 0]], 0.022, wc(130, 0.3), level, tileWood, 6);
    pushBox(paddle, len - 0.55 - 0.3, 0, 0, 0.3, 0.07, 0.008, wc(131, 0.3), level, tileWood, 0);
  } else {
    // A paddle along -y from its grip at the origin: shaft, then a long blade.
    const len = kind === 'dugout' ? 1.65 : 1.55;
    pushBox(paddle, 0, -0.01, 0, 0.06, 0.012, 0.02, wc(132, 0.3), level, tileWood, 0);
    pushPole(paddle, [[0, 0, 0], [0, -(len - 0.6), 0]], 0.016, wc(133, 0.3), level, tileWood, 6);
    pushBox(paddle, 0, -(len - 0.3), 0, 0.075, 0.3, 0.01, wc(134, 0.3), level, tileWood, 0);
  }
  // At rest the paddle (or the oars) lies in the boat; it is part of the hull's own wood then.
  const restPaddle = (buf) => {
    const m = new THREE.Matrix4();
    if (kind === 'skiff') {
      const y = lines.keel(SEAT_AT.skiff) + 0.37;
      for (const z of [-0.22, 0.24]) {
        m.makeRotationY(z > 0 ? 0.04 : -0.03).setPosition(-L * 0.18, y, z);
        appendTransformed(buf, paddle, m);
      }
      return;
    }
    // The paddle's length runs down its own -y: turn it to lie along the floor, blade aft.
    m.makeRotationFromEuler(new THREE.Euler(0, 0.06, -Math.PI / 2, 'YXZ'))
      .setPosition(seatX + 0.9, floorAtSeat + 0.05, 0.1);
    appendTransformed(buf, paddle, m);
  };

  return {
    wood, bark: outerBuf, paddle, restPaddle,
    seat: [seatX, floorAtSeat + (SEAT_EYE_M[kind] - 0.05), 0],
    lines,
    extent: { L, B: lines.B, keelUnder: 0 },
    strokeSide: kind === 'skiff' ? 0 : 1,
  };
}

/* -------------------------------------------------------------------------- */
/* materials                                                                   */
/* -------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------- */
/* the wharf's deck                                                            */
/* -------------------------------------------------------------------------- */

/** Puncheon widths, the gap between them, and how far each stands proud of the crib top. */
const PUNCHEON = { wMin: 0.26, wMax: 0.38, gapMin: 0.012, gapMax: 0.035, proud: 0.03, thick: 0.085, stations: 8 };

/**
 * The deck the skiff's passengers step down from: split-log puncheons laid side by
 * side across the crib, flat face up, from the bank out over the water, their river
 * ends ragged where each was cut. Built in local ENU from the wharf row that
 * tools/lay_crossing_boats_1812.py copies off the structure record, so it sits on
 * that crib and nowhere else. The crib top below shows through the gaps.
 */
export function buildWharfDeck(wharf, { tileWood = 4.08, coarse = false } = {}) {
  const buf = buffer();
  const th = (wharf.rotation_deg ?? 0) * DEG;
  const c = Math.cos(th), sn = Math.sin(th);
  const [u0, u1] = wharf.u, [v0, v1] = wharf.v;
  const deck = wharf.deck_m;
  // Wharf frame (u along the bank, v out over the water, h up) to world.
  const W = (u, v, h) => [wharf.e + u * c + v * sn, h, -(wharf.n - u * sn + v * c)];
  const rand = rng(wharf.seed ?? 3510);
  const stations = coarse ? 3 : PUNCHEON.stations;
  let u = u0 + 0.02;
  let k = 0;
  while (u < u1 - 0.1) {
    const w = Math.min(lerp(PUNCHEON.wMin, PUNCHEON.wMax, rand()), u1 - u - 0.02);
    if (w < 0.12) break;
    const a = u, b = u + w;
    // Each split its own grey: the bank end drier and paler, the river end darker.
    const tone = [lerp(0.44, 0.55, rand()), 0, 0];
    tone[1] = tone[0] * lerp(0.9, 0.95, rand());
    tone[2] = tone[0] * lerp(0.78, 0.86, rand());
    const vStart = v0 + rand() * 0.06;
    const vEnd = v1 + lerp(0.03, 0.16, rand());
    const twist = (rand() - 0.5) * 0.012;
    const crown = lerp(0.004, 0.012, rand());
    const uvOff = rand() * 7;
    const top = (i, x) => {
      const t = i / (stations - 1);
      const across = (x - 0.5) * 2;
      return deck + PUNCHEON.proud + crown * (1 - across * across) + twist * across * (t - 0.5) * 2
        + Math.sin((t * 3.1 + k) * 2.3) * 0.003;
    };
    const colAt = (i, x, shade = 1) => {
      const t = i / (stations - 1);
      const wet = smooth(clamp((t - 0.7) / 0.3, 0, 1)) * 0.22;
      const edge = (x <= 0 || x >= 1) ? 0.82 : 1;
      return linear(tone.map((ch) => ch * (1 - wet) * edge * shade));
    };
    const vAt = (i) => lerp(vStart, vEnd, i / (stations - 1));
    // Across the face: edge, chamfer, flat, chamfer, edge (x 0..1 of the width).
    const xs = [0, 0.1, 0.5, 0.9, 1];
    const hAt = (i, j) => (j === 0 || j === xs.length - 1 ? top(i, xs[j]) - 0.03 : top(i, xs[j]));
    const levelOne = 1;
    pushGrid(buf, stations, xs.length,
      (i, j) => W(lerp(a, b, xs[j]), vAt(i), hAt(i, j)),
      (i, j) => colAt(i, xs[j]),
      (i, j) => [vAt(i) / tileWood, (uvOff + xs[j] * w) / tileWood],
      levelOne, true);
    // The two split sides, down into the crib.
    for (const [x, flip] of [[0, false], [1, true]]) {
      const j = x === 0 ? 0 : xs.length - 1;
      pushGrid(buf, stations, 2,
        (i, m) => W(lerp(a, b, x), vAt(i), m === 0 ? hAt(i, j) : deck + PUNCHEON.proud - PUNCHEON.thick),
        (i) => colAt(i, x, 0.7),
        (i, m) => [vAt(i) / tileWood, (uvOff + m * 0.08) / tileWood],
        levelOne, flip);
    }
    // The ends: the river end's sawn face shows.
    for (const [i, flip] of [[0, true], [stations - 1, false]]) {
      pushGrid(buf, 2, xs.length,
        (m, j) => W(lerp(a, b, xs[j]), vAt(i), m === 0 ? hAt(i, j) : deck + PUNCHEON.proud - PUNCHEON.thick),
        (m, j) => colAt(i, xs[j], 0.62),
        (m, j) => [(uvOff + xs[j] * w) / tileWood, m * 0.08 / tileWood],
        levelOne, flip);
    }
    u = b + lerp(PUNCHEON.gapMin, PUNCHEON.gapMax, rand());
    k += 1;
  }
  return buf;
}

function woodMaterial(relief, confidence, coarse) {
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, vertexColors: true, roughness: 0.9, metalness: 0, side: THREE.DoubleSide,
  });
  mat.name = 'crossing-boat-wood';
  if (relief) {
    mat.normalMap = relief.normal;
    mat.normalScale = new THREE.Vector2(coarse ? 0.8 : 1, coarse ? 0.8 : 1);
    mat.roughnessMap = relief.orl;
    mat.aoMap = relief.orl;
    mat.aoMapIntensity = 0.8;
    mat.roughness = 1;
    const mean = relief.meanRough || 0.9;
    mat.onBeforeCompile = (shader) => {
      shader.uniforms.chiBoatMeanRough = { value: mean };
      shader.fragmentShader = 'uniform float chiBoatMeanRough;\n' + shader.fragmentShader
        .replace('#include <color_fragment>', `#include <color_fragment>
  diffuseColor.rgb *= 2.0 * texture2D( roughnessMap, vRoughnessMapUv ).b;`)
        .replace('#include <roughnessmap_fragment>', `float roughnessFactor = 0.9
    * clamp( texture2D( roughnessMap, vRoughnessMapUv ).g / chiBoatMeanRough, 0.0, 1.1 );`);
    };
    mat.customProgramCacheKey = () => 'chicago4d-crossing-wood-relief';
  } else {
    mat.customProgramCacheKey = () => 'chicago4d-crossing-wood-flat';
  }
  confidence?.patch(mat);
  return mat;
}

function barkMaterial(sheet, confidence) {
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, vertexColors: true, roughness: sheet ? 1 : 0.93, metalness: 0, side: THREE.DoubleSide,
  });
  mat.name = 'crossing-boat-bark';
  if (sheet) {
    mat.map = sheet.map;
    mat.normalMap = sheet.normalMap;
    mat.roughnessMap = sheet.orm;
    mat.aoMap = sheet.orm;
    mat.aoMapIntensity = 0.8;
  }
  mat.customProgramCacheKey = () => (sheet ? 'chicago4d-crossing-bark' : 'chicago4d-crossing-bark-flat');
  confidence?.patch(mat);
  return mat;
}

/* -------------------------------------------------------------------------- */
/* geometry                                                                    */
/* -------------------------------------------------------------------------- */

function geometryOf(buf, smoothNormals) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(buf.uv, 2));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(buf.col, 3));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  if (smoothNormals) smoothAcross(geo);
  geo.computeBoundingSphere();
  return geo;
}

/**
 * Smooth the normals of coincident vertices whose faces turn by less than ~50 degrees:
 * the round of a log or a canoe's bilge reads round, while the skiff's chine, a rim's
 * edge and a box's corners stay crisp.
 */
function smoothAcross(geo) {
  const pos = geo.getAttribute('position');
  const nrm = geo.getAttribute('normal');
  const key = (i) => `${Math.round(pos.getX(i) * 2000)},${Math.round(pos.getY(i) * 2000)},${Math.round(pos.getZ(i) * 2000)}`;
  const groups = new Map();
  for (let i = 0; i < pos.count; i++) {
    const k = key(i);
    let g = groups.get(k);
    if (!g) { g = []; groups.set(k, g); }
    g.push(i);
  }
  const out = new Float32Array(nrm.array.length);
  const cosMax = Math.cos(50 * DEG);
  for (const g of groups.values()) {
    for (const i of g) {
      const ni = [nrm.getX(i), nrm.getY(i), nrm.getZ(i)];
      let sx = 0, sy = 0, sz = 0;
      for (const j of g) {
        const nj = [nrm.getX(j), nrm.getY(j), nrm.getZ(j)];
        const dot = ni[0] * nj[0] + ni[1] * nj[1] + ni[2] * nj[2];
        if (dot >= cosMax) { sx += nj[0]; sy += nj[1]; sz += nj[2]; }
      }
      const l = Math.hypot(sx, sy, sz) || 1;
      out[i * 3] = sx / l; out[i * 3 + 1] = sy / l; out[i * 3 + 2] = sz / l;
    }
  }
  nrm.array.set(out);
  nrm.needsUpdate = true;
}

/** Append `src` transformed by `m` (Matrix4) into `dst` (a buffer). */
function appendTransformed(dst, src, m) {
  const v = new THREE.Vector3();
  const nm = new THREE.Matrix3().getNormalMatrix(m);
  for (let k = 0; k < src.pos.length; k += 3) {
    v.set(src.pos[k], src.pos[k + 1], src.pos[k + 2]).applyMatrix4(m);
    dst.pos.push(v.x, v.y, v.z);
    v.set(src.nrm[k], src.nrm[k + 1], src.nrm[k + 2]).applyMatrix3(nm).normalize();
    dst.nrm.push(v.x, v.y, v.z);
  }
  for (const x of src.uv) dst.uv.push(x);
  for (const x of src.col) dst.col.push(x);
  for (const x of src.conf) dst.conf.push(x);
}

/* -------------------------------------------------------------------------- */
/* poses                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * A boat's pose: where its midships keel point is (e, n, y), the bearing of its bow, and
 * its pitch (bow up, radians) and roll (to starboard, radians).
 */
function matrixFor(pose, out = new THREE.Matrix4()) {
  const p = enuToWorld(pose.e, pose.n, pose.y, new THREE.Vector3());
  const q = new THREE.Quaternion().setFromEuler(
    new THREE.Euler(pose.roll ?? 0, (90 - pose.bearing) * DEG, pose.pitch ?? 0, 'YZX'));
  return out.compose(p, q, new THREE.Vector3(1, 1, 1));
}

/** The pose of a boat at rest on a bank: bow on the ground, stern afloat, a little heeled. */
function restPose(boat, rest, terrain) {
  const draft = boat.hull.draft_m ?? 0.15;
  if (rest.afloat) return { e: rest.e, n: rest.n, y: WATER_Y - draft, bearing: rest.bearing, pitch: 0, roll: 0 };
  const L = boat.hull.length_m;
  const b = rest.bearing * DEG;
  const de = Math.sin(b), dn = Math.cos(b);
  const reach = 0.4 * L;
  const ground = (e, n) => terrain.surfaceHeight(e, n);
  const yB = Math.max(ground(rest.e + de * reach, rest.n + dn * reach), WATER_Y - draft);
  const yS = Math.max(ground(rest.e - de * reach, rest.n - dn * reach), WATER_Y - draft);
  const pitch = Math.atan2(yB - yS, 2 * reach);
  const r = rng((boat.look?.seed ?? 1) * 104729);
  const heel = (r() < 0.5 ? -1 : 1) * (1.5 + r() * 3.5) * DEG;
  // Sunk a couple of centimetres into the soft bank so it sits rather than perches.
  return { e: rest.e, n: rest.n, y: (yB + yS) / 2 - 0.025, bearing: rest.bearing, pitch, roll: yB > WATER_Y ? heel : 0 };
}

/** The pose afloat at a launch point, bow toward `bearing`. */
function afloatPose(boat, [e, n], bearing) {
  return { e, n, y: WATER_Y - (boat.hull.draft_m ?? 0.15), bearing, pitch: 0, roll: 0 };
}

function mixPose(a, b, t) {
  return {
    e: lerp(a.e, b.e, t), n: lerp(a.n, b.n, t), y: lerp(a.y, b.y, t),
    bearing: (a.bearing + turn(a.bearing, b.bearing) * t + 360) % 360,
    pitch: lerp(a.pitch ?? 0, b.pitch ?? 0, t), roll: lerp(a.roll ?? 0, b.roll ?? 0, t),
  };
}

/* -------------------------------------------------------------------------- */
/* the card                                                                    */
/* -------------------------------------------------------------------------- */

function cardRecordFor(boat, pose, bank) {
  const h = boat.hull;
  const ex = boat.existence ?? {};
  const words = {
    dugout: 'A dugout canoe, the pirogue of the river trade: one log hollowed by adze and fire.',
    bark_canoe: 'A canoe of elm bark sewn over a light frame of ribs and gunwale poles.',
    skiff: 'A small flat-bottomed boat of sawn plank, rowed with a pair of oars.',
  }[boat.kind] ?? '';
  const rec = (value, note, confidence = 'reconstructed', sources = []) => ({ value, confidence, sources, note });
  return {
    id: boat.id,
    sidecar: {
      name: boat.name,
      phase: null,
      placement: {
        local_e: pose.e,
        local_n: pose.n,
        symbolic_location: `Drawn up at ${bank.name}`,
        position_confidence: 'reconstructed',
        position_sources: [],
        position_note: 'Where it lies is ours: laid by tools/lay_crossing_boats_1812.py on the 1812 ground. Cross takes it to the other bank, and it stays there.',
        vertical_anchor: 'terrain',
      },
      attributes: {
        kind: rec(boat.kind_words, words, ex.confidence === 'attested' ? 'attested' : 'reconstructed', ex.confidence === 'attested' ? ex.sources ?? [] : []),
        existence: rec(ex.confidence === 'attested' ? 'recorded' : 'reconstructed', ex.note ?? '', ex.confidence ?? 'reconstructed', ex.sources ?? []),
        length_m: rec(h.length_m, 'Reconstructed within the run of its kind.'),
        beam_m: rec(h.beam_m, 'Reconstructed within the run of its kind.'),
        depth_m: rec(h.depth_m, 'Reconstructed.'),
      },
      citations: [],
      research_note: `${words} ${ex.note ?? ''}${ex.standing_constraint_note ? ` ${ex.standing_constraint_note}` : ''}`
        + ` Its shape and weathering are reconstructed; see ${boat.liberty}. Walk up to it and Interact to cross.`,
    },
  };
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * @param {object} o
 *   dataBase (data/ root) · terrain · confidence · problems · detail ('full'|'balanced'|'light')
 *   coarse (a phone) · walkEye () => the standing eye height · onRide (boat, on) — told when a
 *   crossing starts and ends, so main.js can stop a Go-to or a Follow
 */
export async function createCrossings({
  dataBase, terrain, confidence = null, problems = [], detail = 'full', coarse = false,
  walkEye = () => 1.6, onRide = () => {}, lowSpec = false,
} = {}) {
  const group = new THREE.Group();
  group.name = 'crossings';
  const out = {
    group, boats: [], things: [], keepOut: [], riding: null,
    census: { boats: 0, dugout: 0, bark_canoe: 0, skiff: 0, refused: 0 },
    pickAt: () => null, update: () => {}, holdVisitor: () => false, dispose: () => {},
  };
  if (!dataBase || !terrain) return out;
  let doc;
  try {
    const res = await fetch(new URL('boats/crossings_1812.json', dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} — boats/crossings_1812.json`);
    doc = await res.json();
  } catch (err) {
    problems.push(`crossings: ${err.message} — no boat is drawn`);
    return out;
  }

  const relief = globalThis.window ? await loadedSubstrate('hewn_log', { lowSpec }) : null;
  const barkSheet = campSheet('camp_elm_bark');
  const woodMat = woodMaterial(relief, confidence, coarse);
  const barkMat = barkMaterial(barkSheet, confidence);
  const tileWood = relief?.tileM ?? 4.08;
  const tileBark = barkSheet?.spanM ?? 1.2;
  const speed = Number(doc.speed_m_s) || 1.6;
  const drawM = DRAW_M[detail] ?? DRAW_M.full;

  // Build every boat in its own frame once.
  for (const boat of doc.boats ?? []) {
    try {
      const built = buildBoat(boat, { tileWood, tileBark, coarse });
      const rest = { a: restPose(boat, boat.banks.a.rest, terrain), b: restPose(boat, boat.banks.b.rest, terrain) };
      const entry = { boat, built, rest, bank: boat.starts ?? 'a', pose: null, cluster: null };
      entry.pose = rest[entry.bank];
      out.boats.push(entry);
      out.census.boats += 1;
      out.census[boat.kind] = (out.census[boat.kind] ?? 0) + 1;
    } catch (err) {
      out.census.refused += 1;
      problems.push(`crossings: ${boat.id} not drawn — ${err.message}`);
    }
  }

  /* --- the boats at rest, merged by neighbourhood -------------------------------- */
  const clusters = [];
  const m4 = new THREE.Matrix4();
  function rebuildClusters() {
    for (const c of clusters) {
      group.remove(c.group);
      c.meshes.forEach((m) => m.geometry.dispose());
    }
    clusters.length = 0;
    for (const entry of out.boats) {
      if (out.riding === entry) continue;
      const { e, n } = entry.pose;
      let c = clusters.find((k) => Math.hypot(k.e - e, k.n - n) < CLUSTER_M);
      if (!c) { c = { e, n, members: [] }; clusters.push(c); }
      c.members.push(entry);
    }
    for (const c of clusters) {
      const wood = buffer(), bark = buffer();
      c.spans = [];
      for (const entry of c.members) {
        matrixFor(entry.pose, m4);
        const w0 = wood.pos.length / 9, b0 = bark.pos.length / 9;
        appendTransformed(wood, entry.built.wood, m4);
        const lying = buffer();
        entry.built.restPaddle(lying);
        appendTransformed(wood, lying, m4);
        if (entry.built.bark) appendTransformed(bark, entry.built.bark, m4);
        c.spans.push({ entry, wood: [w0, wood.pos.length / 9], bark: [b0, bark.pos.length / 9] });
      }
      c.group = new THREE.Group();
      c.group.name = 'crossings-rest';
      c.meshes = [];
      const add = (buf, mat, name) => {
        if (!buf.pos.length) return;
        const mesh = new THREE.Mesh(geometryOf(buf, false), mat);
        mesh.name = name;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        c.group.add(mesh);
        c.meshes.push(mesh);
      };
      add(wood, woodMat, 'crossings-wood');
      add(bark, barkMat, 'crossings-bark');
      group.add(c.group);
    }
  }
  // Each boat's own normals are smoothed once in its frame (the merge only transforms them).
  // Each is then held as float32, not as a list of doubles: the page keeps these for
  // as long as the boat can be moved, and a phone pays for every byte of them.
  for (const entry of out.boats) {
    for (const key of ['wood', 'bark', 'paddle']) {
      const buf = entry.built[key];
      if (!buf?.pos.length) continue;
      if (key !== 'paddle') {
        const g = geometryOf(buf, entry.boat.kind !== 'skiff');
        buf.nrm = g.getAttribute('normal').array;
        g.dispose();
      }
      for (const a of ['pos', 'nrm', 'uv', 'col', 'conf']) {
        if (!(buf[a] instanceof Float32Array)) buf[a] = Float32Array.from(buf[a]);
      }
    }
  }
  rebuildClusters();

  /* --- the fort wharf's deck, where the skiff is boarded ------------------------- */
  for (const wharf of doc.wharves ?? []) {
    const buf = buildWharfDeck(wharf, { tileWood, coarse });
    if (!buf.pos.length) continue;
    const mesh = new THREE.Mesh(geometryOf(buf, false), woodMat);
    mesh.name = `crossings-deck-${wharf.id}`;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
    out.census.decks = (out.census.decks ?? 0) + 1;
  }

  /* --- the boat being crossed in --------------------------------------------------- */
  let ride = null;   // { entry, from, to, group, oar meshes, paddle mesh, t0 … }

  function riderGroup(entry) {
    const g = new THREE.Group();
    g.name = `crossing-${entry.boat.id}`;
    const add = (buf, mat, smoothN) => {
      if (!buf?.pos.length) return null;
      const mesh = new THREE.Mesh(geometryOf(buf, smoothN), mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      g.add(mesh);
      return mesh;
    };
    add(entry.built.wood, woodMat, false);
    add(entry.built.bark, barkMat, false);
    const tools = [];
    const pg = geometryOf(entry.built.paddle, false);
    const count = entry.boat.kind === 'skiff' ? 2 : 1;
    for (let k = 0; k < count; k++) {
      const m = new THREE.Mesh(pg, woodMat);
      m.castShadow = true;
      g.add(m);
      tools.push(m);
    }
    return { group: g, tools };
  }

  /** The seat's eye point in local ENU, and the boat's world matrix, for a pose. */
  const seatV = new THREE.Vector3();
  function seatOf(entry, pose) {
    matrixFor(pose, m4);
    seatV.set(...entry.built.seat).applyMatrix4(m4);
    return { e: seatV.x, n: -seatV.z, y: seatV.y };
  }

  /** Lay the paddle or oars for stroke phase `ph` (0..1), working on `side` (+1 starboard). */
  const qTmp = new THREE.Quaternion();
  function workTools(entry, tools, ph, side, working) {
    const { kind } = entry.boat;
    const L = entry.boat.hull.length_m;
    const seat = entry.built.seat;
    if (kind === 'skiff') {
      const t = SEAT_AT.skiff + 0.18;
      const lines = entry.built.lines;
      const hb = lines.half(t);
      const gy = lines.gun(t) + 0.1;
      // The drive pulls the blades aft through the water; the recovery lifts and swings them forward.
      const sweep = working ? Math.cos(ph * Math.PI * 2) * 0.5 : -0.9;
      const dip = working ? (ph < 0.5 ? 0.28 : -0.06) : -0.02;
      tools.forEach((m, k) => {
        const s = k === 0 ? 1 : -1;
        m.position.set(t * L / 2, gy, s * (hb + 0.02));
        // The oar's +x runs outboard from its thole: out over its own side, swept fore and aft,
        // its blade dipped below the loom.
        m.quaternion.setFromEuler(new THREE.Euler(0, s > 0 ? -Math.PI / 2 + sweep : Math.PI / 2 - sweep, 0, 'YXZ'));
        m.rotateZ(-dip);
      });
      return;
    }
    const m = tools[0];
    // A paddle stroke: catch forward, pull aft through the water, lift and swing forward.
    const reachX = 0.55, endX = -0.35;
    let x, depth, lean;
    if (!working) { x = 0.2; depth = 0.35; lean = 0.5; } else if (ph < 0.55) {
      const f = smooth(ph / 0.55);
      x = lerp(reachX, endX, f); depth = 0.95; lean = lerp(0.35, -0.25, f);
    } else {
      const f = smooth((ph - 0.55) / 0.45);
      x = lerp(endX, reachX, f); depth = 0.55 + 0.3 * Math.cos(f * Math.PI) * -0.0; lean = lerp(-0.25, 0.35, f);
      depth = 0.45;
    }
    const hb = entry.built.lines.half(SEAT_AT[kind] + 0.12);
    // The grip rides above the gunwale, the blade at the boat's side, down into the water.
    m.position.set(seat[0] + 0.45 + x * 0.5, seat[1] - 0.3 + (depth < 0.6 ? 0.18 : 0), side * (hb + 0.1));
    m.quaternion.setFromEuler(new THREE.Euler(side * 0.18, 0, lean, 'XYZ'));
  }

  /** Begin a crossing from bank `from` to `to`. */
  function start(entry, from, to) {
    const boat = entry.boat;
    const d = boat.crossing.bearing;
    const outBearing = from === 'a' ? d : (d + 180) % 360;
    const ra = entry.rest[from], rb = entry.rest[to];
    const la = afloatPose(boat, boat.banks[from].launch, outBearing);
    const lb = afloatPose(boat, boat.banks[to].launch, outBearing);
    // Pushing off: back the hull straight off the bank first, then swing it round.
    const backDir = ra.bearing * DEG;
    const backed = { ...afloatPose(boat, [ra.e - Math.sin(backDir) * boat.hull.length_m * 0.45, ra.n - Math.cos(backDir) * boat.hull.length_m * 0.45], ra.bearing) };
    if (boat.banks[from].rest.afloat) {
      backed.e = ra.e + Math.sin(outBearing * DEG) * 1.2;
      backed.n = ra.n + Math.cos(outBearing * DEG) * 1.2;
    }
    const { group: g, tools } = riderGroup(entry);
    group.add(g);
    out.riding = entry;
    rebuildClusters();
    const pathM = Math.hypot(lb.e - la.e, lb.n - la.n);
    ride = {
      entry, from, to, g, tools, ra, rb, la, lb, backed, pathM,
      pose: { ...ra }, visitor: null, eyeFrom: null, yawFrom: null, yawTo: outBearing,
      stroke: 0, side: 1, strokes: 0, working: false,
    };
    onRide(entry, true);
    placeRide();
  }

  function placeRide() {
    if (!ride) return;
    matrixFor(ride.pose, ride.g.matrix);
    ride.g.matrix.decompose(ride.g.position, ride.g.quaternion, ride.g.scale);
    ride.entry.pose = ride.pose;
  }

  function finish() {
    if (!ride) return;
    const { entry, to, g } = ride;
    entry.bank = to;
    entry.pose = entry.rest[to];
    group.remove(g);
    g.children.forEach((m) => m.geometry.dispose());
    out.riding = null;
    ride = null;
    rebuildClusters();
    onRide(entry, false);
  }

  /** The eye's place while a step runs (null: the walker has it). */
  let eye = null;     // { e, n, y, yaw? }

  function crossAction(entry, from, to) {
    const boat = entry.boat;
    const verb = boat.kind === 'skiff' ? 'Rowing' : 'Paddling';
    const seconds = Math.max(8, boat.crossing.seconds ?? (boat.crossing.path_m / speed));
    const standTo = boat.banks[to].stand;
    return {
      id: 'cross',
      label: `Cross to ${boat.banks[to].name}`,
      to,
      said: () => `Across: ${boat.banks[to].name}`,
      refuse: () => (out.riding && out.riding !== entry ? 'Already in a boat' : null),
      steps: [
        {
          label: 'Stepping in', seconds: STEP_S.in,
          run: (t) => {
            if (t === 0 && !ride) {
              start(entry, from, to);
              const v = visitorNow?.();
              ride.eyeFrom = v ? { e: v.e, n: v.n, y: v.y } : seatOf(entry, ride.pose);
              ride.yawFrom = v?.bearing ?? ride.yawTo;
            }
            if (!ride) return;
            const seat = seatOf(entry, ride.pose);
            const f = smooth(t);
            // Over the gunwale: up a little, then down onto the seat.
            eye = {
              e: lerp(ride.eyeFrom.e, seat.e, f), n: lerp(ride.eyeFrom.n, seat.n, f),
              y: lerp(ride.eyeFrom.y, seat.y, f) + Math.sin(f * Math.PI) * 0.12,
              bearing: (ride.yawFrom + turn(ride.yawFrom, ride.yawTo) * f + 360) % 360,
            };
            ride.pose = { ...ride.ra, roll: (ride.ra.roll ?? 0) + Math.sin(f * Math.PI) * 2.5 * DEG };
            placeRide();
          },
        },
        {
          label: 'Pushing off', seconds: STEP_S.off,
          run: (t) => {
            if (!ride) return;
            const f = smooth(t);
            const back = smooth(clamp(t / 0.55, 0, 1));
            const swing = smooth(clamp((t - 0.3) / 0.7, 0, 1));
            const p1 = mixPose(ride.ra, ride.backed, back);
            const p2 = mixPose(p1, ride.la, swing);
            p2.roll = Math.sin(f * Math.PI * 2) * 1.5 * DEG;
            ride.pose = p2;
            placeRide();
            workTools(entry, ride.tools, (t * 2) % 1, ride.side, t > 0.35);
            eye = { ...seatOf(entry, ride.pose), bearing: null };
          },
        },
        {
          label: `${verb} across`, seconds,
          run: (t) => {
            if (!ride) return;
            // Ease in over the first strokes and out as the far bank comes up.
            const ease = (x) => {
              const a = 0.08;
              if (x < a) return (x * x) / (2 * a * (1 - a));
              if (x > 1 - a) return 1 - ((1 - x) * (1 - x)) / (2 * a * (1 - a));
              return (x - a / 2) / (1 - a);
            };
            const f = clamp(ease(t), 0, 1);
            const p = mixPose(ride.la, ride.lb, f);
            const strokeS = STROKE_S[boat.kind];
            const time = t * seconds;
            const ph = (time / strokeS) % 1;
            const n = Math.floor(time / strokeS);
            // A paddler changes sides every few strokes; the bow swings a little each stroke.
            ride.side = boat.kind === 'skiff' ? 1 : (Math.floor(n / 4) % 2 === 0 ? 1 : -1);
            p.bearing = (p.bearing + Math.sin(ph * Math.PI * 2) * (boat.kind === 'skiff' ? 0.4 : 1.6) * -ride.side + 360) % 360;
            p.roll = Math.sin(ph * Math.PI * 2) * (boat.kind === 'skiff' ? 0.6 : 1.4) * DEG * ride.side;
            p.y += Math.sin(time * 2.1) * 0.012;
            p.pitch = Math.sin(time * 1.3) * 0.5 * DEG;
            ride.pose = p;
            placeRide();
            workTools(entry, ride.tools, ph, ride.side, t < 0.985);
            eye = { ...seatOf(entry, ride.pose), bearing: null };
          },
        },
        {
          label: 'Running ashore', seconds: STEP_S.ashore,
          run: (t) => {
            if (!ride) return;
            const f = smooth(t);
            const p = mixPose(ride.lb, ride.rb, f);
            ride.pose = p;
            placeRide();
            workTools(entry, ride.tools, 0, ride.side, false);
            eye = { ...seatOf(entry, ride.pose), bearing: null };
          },
        },
        {
          label: 'Stepping out', seconds: STEP_S.out,
          run: (t) => {
            if (!ride) return;
            const seat = seatOf(entry, ride.pose);
            const groundY = terrain.surfaceHeight(standTo[0], standTo[1]);
            const f = smooth(t);
            eye = {
              e: lerp(seat.e, standTo[0], f), n: lerp(seat.n, standTo[1], f),
              y: lerp(seat.y, groundY + walkEye(), f) + Math.sin(f * Math.PI) * 0.15,
              bearing: null,
            };
            if (t >= 1) {
              landing = { e: standTo[0], n: standTo[1] };
              finish();
              thingOf(entry).at = [...boat.banks[to].stand];
            }
          },
        },
      ],
    };
  }

  let visitorNow = null;   // () => { e, n, y, bearing } — set by holdVisitor's first call
  let landing = null;      // where to put the walker down once a crossing ends

  const thingFor = new Map();
  const thingOf = (entry) => thingFor.get(entry);
  for (const entry of out.boats) {
    const { boat } = entry;
    const thing = {
      id: `boat:${boat.id}`,
      name: boat.name,
      kind: 'boat',
      states: ['a', 'b'],
      state: entry.bank,
      at: [...boat.banks[entry.bank].stand],
      reach: Math.max(4.5, boat.hull.length_m / 2 + 2.5),
      actions: {
        a: [crossAction(entry, 'a', 'b')],
        b: [crossAction(entry, 'b', 'a')],
      },
    };
    // Reach is measured from the boat's bow end, between the stand and the hull.
    const bowAt = (bank) => {
      const r = boat.banks[bank].rest;
      const b = r.bearing * DEG;
      return [r.e + Math.sin(b) * boat.hull.length_m * 0.3, r.n + Math.cos(b) * boat.hull.length_m * 0.3];
    };
    thing.at = bowAt(entry.bank);
    thing.reach = 4.5;
    entry.bowAt = bowAt;
    thingFor.set(entry, thing);
    out.things.push(thing);
    // Planting keep-out: a worn landing. Nothing grows up through a drawn-up
    // hull, and the reeds at the waterline are trodden and dragged flat from
    // where the visitor stands, past the stern, out to where the boat floats:
    // the reed bed otherwise stands taller than the hull and hides it.
    for (const bank of ['a', 'b']) {
      const side = boat.banks[bank];
      const r = side.rest;
      if (r.afloat) continue;
      const b = r.bearing * DEG;
      const ue = Math.sin(b), un = Math.cos(b);
      // The boat's own frame: x along the bow, z to starboard.
      const along = (p) => (p[0] - r.e) * ue + (p[1] - r.n) * un;
      const half = boat.hull.length_m / 2;
      const x1 = Math.max(half + LANDING_PAD_M, along(side.stand) + LANDING_PAD_M);
      const x0 = Math.min(-half - LANDING_PAD_M, along(side.launch) - LANDING_PAD_M);
      const hw = boat.hull.beam_m / 2 + LANDING_SIDE_M;
      out.keepOut.push({
        id: `${boat.id}__${bank}`,
        pts: [[x0, -hw], [x1, -hw], [x1, hw], [x0, hw]].map(([x, z]) => [r.e + ue * x + un * z, r.n + un * x - ue * z]),
      });
    }
  }

  /** Draw only what is near enough to see. */
  out.update = (dt, camera) => {
    if (!camera) return;
    const ce = camera.position.x, cn = -camera.position.z;
    for (const c of clusters) c.group.visible = Math.hypot(c.e - ce, c.n - cn) < drawM + CLUSTER_M;
    for (const entry of out.boats) {
      const t = thingOf(entry);
      if (out.riding === entry && ride) t.at = [ride.pose.e, ride.pose.n];
      else t.at = entry.bowAt(entry.bank);
    }
  };

  /**
   * Called by main.js after the walk step: while a crossing runs, the eye is on the seat.
   * Returns true while it holds the visitor.
   */
  out.holdVisitor = (walker, WALK) => {
    if (!visitorNow) {
      visitorNow = () => ({ e: walker.state.e, n: walker.state.n, y: walker.state.eyeY, bearing: walker.bearingDeg });
    }
    if (landing) {
      const l = landing;
      landing = null;
      eye = null;
      walker.teleport({ local_e: l.e, local_n: l.n, yaw_deg: walker.bearingDeg, pitch_deg: walker.state.pitch / DEG });
      return false;
    }
    if (!ride || !eye) return false;
    const s = walker.state;
    s.e = eye.e;
    s.n = eye.n;
    s.eyeY = eye.y;
    s.groundY = eye.y - (WALK?.eyeHeight ?? 1.6);
    s.altitude = 0;
    s.stepEase = 0;
    s.bob = 0;
    if (eye.bearing !== null && eye.bearing !== undefined) s.yaw = bearingToYaw(eye.bearing);
    walker.apply();
    return true;
  };

  const raycaster = new THREE.Raycaster();
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = 200;
    let best = null;
    for (const c of clusters) {
      if (!c.group.visible) continue;
      for (const mesh of c.meshes) {
        const hits = raycaster.intersectObject(mesh, false);
        if (!hits.length || (best && hits[0].distance >= best.distance)) continue;
        const key = mesh.name === 'crossings-bark' ? 'bark' : 'wood';
        const span = c.spans.find((sp) => hits[0].faceIndex >= sp[key][0] && hits[0].faceIndex < sp[key][1]);
        if (span) best = { entry: span.entry, distance: hits[0].distance, point: hits[0].point.clone() };
      }
    }
    if (!best) return null;
    const { entry } = best;
    return {
      id: entry.boat.id,
      record: cardRecordFor(entry.boat, entry.pose, entry.boat.banks[entry.bank]),
      point: best.point,
      distance: best.distance,
    };
  };

  out.dispose = () => {
    for (const c of clusters) c.meshes.forEach((m) => m.geometry.dispose());
    woodMat.dispose();
    barkMat.dispose();
  };
  group.userData.census = out.census;
  return out;
}
