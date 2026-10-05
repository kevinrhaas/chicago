/**
 * yards.js — the ground INSIDE a fence.
 *
 * WHY THIS FILE EXISTS. The owner, 2026-08-18, verbatim: *"everplace that is
 * fenced in would have a different ground, the wagon yard would probably be
 * dirty dusty ground and fences around properties inside the fence would not be
 * wild prairie but curated lawn and garden or animal pens."* He was reading the
 * model correctly. `enclosures.js` had been building the town's fence lines
 * since T-0050 — a wagon yard, a pound, fifteen garden plots, a hotel's back
 * yard — and every one of them enclosed the same wild prairie sward the flora
 * layer plants over the whole town. Three of the four records said so IN THEIR
 * OWN `ground` BLOCK, in as many words, with `geometry: "absent"`: *"NOT DRAWN,
 * AND SAYING SO IS THE POINT."* A fence whose inside is identical to its outside
 * is a fence that says nothing about why it is there.
 *
 * WHAT THIS LAYER DOES, and the two halves are equally load-bearing:
 *
 *  1. **It suppresses the sward inside the fence.** `main.js` composes
 *     `suppressesSward` into the block-list `flora.js` already tests every
 *     station against (T-0124 hoisted that test above the wet early-return;
 *     this rides on it unchanged). Nothing else is blocked — the TREES are
 *     deliberately not, because the dooryard plantings (T-0074) and the
 *     Sauganash's own three stems stand INSIDE these fences by record, and a
 *     block that killed them would be this ticket undoing another one.
 *  2. **It lays a per-type ground treatment in the sward's place**, draped on
 *     the committed heightfield the way `streets.js` drapes a wagon track: every
 *     vertex samples `terrain.surfaceHeight()`, nothing here regrades anything,
 *     and nothing here is a collision surface.
 *
 * FOUR TREATMENTS, because a fence's ground is a statement about the fence:
 *
 *   `worn_earth`      A WORKING YARD. Bare, dusty, hoof- and wheel-worn dirt,
 *                     with sparse trampled grass surviving at the edges where
 *                     the wheels do not reach — the fringe is drawn as part of
 *                     the treatment rather than left to the sward, so there is
 *                     no seam at the fence line. The Western Hotel's wagon yard.
 *   `trodden_earth`   AN ANIMAL PEN. Bare trodden earth, darker, finer, and
 *                     without the ruts a wheel makes or much of a fringe: a
 *                     pound is trodden right up to its rails. The estray pen.
 *   `road_earth`      THE GROUND AT A DOOR (T-1984, T-2013). The town's own road
 *                     dirt — `streets.js`'s grit tile and worn-earth tones, laid
 *                     in world coordinates — so a door's path that meets the
 *                     street continues it with no seam in grain or colour, and
 *                     a soft edge into the grass. No canvas of its own.
 *   `dooryard_garden` A DOORYARD OR GARDEN. Curated ground: short green over the
 *                     whole plot, a bank of tilled beds in rows on the side away
 *                     from the gate, and a trodden path in from the gateway. The
 *                     town's fifteen picketed plots and the Sauganash's yard.
 *
 * WHAT IS EVIDENCE AND WHAT IS NOT. Nothing here is attested and this layer does
 * not pretend otherwise: every vertex carries `reconstructed`, so hiding that
 * tier takes the whole treatment away and leaves the ground as the sources leave
 * it. What bounds the invention is on the records: each enclosure's own `ground`
 * block states the treatment and (where its runs do not close a ring themselves)
 * the interior it covers, so WHICH ground gets WHICH treatment is a claim in the
 * dataset rather than a rule in a renderer. docs/LIBERTIES.md L158 claims the
 * scheme; the references it rests on are the Kinzie-view plate's fenced garden
 * plots and image 12 of the 2026-08-18 owner brief.
 *
 * WHAT IT WILL NOT DO. It refuses water (a treatment vertex whose foot is in the
 * river mask drops its whole cell, the way a fence post does), it never moves a
 * metre of terrain, and it casts no shadow — a ground treatment lying on the
 * ground has nothing to cast onto and would only fight its own drape.
 */

import * as THREE from 'three';
import { GRIT_TILE_M } from './ground-strip-mask.js';
import { DIRT_TONES, linearTone, roadGrit } from './streets.js';
import { swardTexture, swardUniforms } from './terrain.js';
import { ditherHash } from './lakeshore.js';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, inferred: 0.5, reconstructed: 1 };

/** The grid the treatment is laid on, in metres. Fine enough to drape a town
 *  that is nearly flat (the whole modelled box holds under two metres of relief
 *  across any of these yards), coarse enough that the whole layer is a few
 *  thousand triangles. */
const CELL_M = 1.0;

/** How far each layer of the treatment floats over the terrain it is draped on.
 *  The base is at the road ribbon's own lift; the beds and the path sit a few
 *  millimetres over it so the three cannot fight for the same depth. */
const LIFT_M = { base: 0.022, bed: 0.028, path: 0.034 };

/** How wide the trampled-grass fringe reaches in from a working yard's fence,
 *  and how far in a garden's mown border runs. Both are the same kind of
 *  invention as the treatment itself and are drawn in the vertex colour rather
 *  than in the map, because the fringe follows the FENCE and the map tiles. */
const FRINGE_M = { worn_earth: 1.3, trodden_earth: 0.45, road_earth: 0.6, dooryard_garden: 0.55 };

/**
 * T-2125 — UNFENCED GROUND FEATHERS OUT. A ground that states one outer ring and
 * no fence along it (the fort's apron, T-0097: `fringe_ring_local_enu_m`) used
 * to stop at that ring with a fringe under half a metre wide, so bare earth met
 * the sward along four ruled lines — the owner's "the edge ... between the fort
 * and prairie" (2026-10-05). It now carries on past the ring into a skirt this
 * many metres wide, its cover thinning along a line that wanders in and out
 * (`featherCover`), and the sward thins in across the same band at the same
 * share. A FENCED yard keeps its edge: a fence is a line, and the ground at it
 * changes there. Reconstructed — docs/LIBERTIES.md.
 */
const FEATHER_M = { worn_earth: 22, trodden_earth: 22 };

/** The beds in a dooryard, in metres: a bed, the walkway beside it, how many are
 *  laid at most, and how long a bed may run. The cap is what makes one rule work
 *  at two scales — it fills a 28 x 20 ft kitchen plot and leaves a hotel's back
 *  yard mostly dooryard green with a garden patch in the corner. */
const BED = { width: 0.9, walk: 0.45, most: 4, longest: 7.0, inset: 0.6 };

/* -------------------------------------------------------------------------- */
/* polygons                                                                    */
/* -------------------------------------------------------------------------- */

function pointInPolygon(pts, e, n) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i];
    const [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Distance from a point to the nearest edge of a polygon. Used for the fringe,
 *  which is a distance from the FENCE and not from anything the map knows. */
function edgeDistance(pts, e, n) {
  let best = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ax, ay] = pts[j];
    const [bx, by] = pts[i];
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy || 1;
    let t = ((e - ax) * dx + (n - ay) * dy) / len2;
    t = Math.min(Math.max(t, 0), 1);
    best = Math.min(best, Math.hypot(ax + dx * t - e, ay + dy * t - n));
  }
  return best;
}

/** Twice the signed area of a ring: positive when it runs anticlockwise. */
function signedArea2(pts) {
  let a = 0;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    a += pts[j][0] * pts[i][1] - pts[i][0] * pts[j][1];
  }
  return a;
}

/**
 * A CONVEX ring pushed out by `d` metres, corner for corner (each side moved
 * out along its normal, each corner where its two moved sides meet), or null
 * when the ring is not convex — the skirt below is only laid where this offset
 * is exact, and the one ring that asks for it (the fort's apron) is a square.
 */
function offsetConvexRing(pts, d) {
  const k = pts.length;
  if (k < 3) return null;
  const ccw = signedArea2(pts) > 0 ? 1 : -1;
  for (let i = 0; i < k; i++) {
    const a = pts[i]; const b = pts[(i + 1) % k]; const c = pts[(i + 2) % k];
    const cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]);
    if (cross * ccw < -1e-9) return null;
  }
  // The outward normal of side i (from vertex i to i + 1).
  const normals = pts.map((a, i) => {
    const b = pts[(i + 1) % k];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [ccw * (b[1] - a[1]) / len, -ccw * (b[0] - a[0]) / len];
  });
  return pts.map((p, i) => {
    const n0 = normals[(i + k - 1) % k];
    const n1 = normals[i];
    // The miter: along the bisector, far enough that both sides sit at d.
    const bx = n0[0] + n1[0];
    const by = n0[1] + n1[1];
    const dot = bx * n1[0] + by * n1[1] || 1;
    return [p[0] + (bx * d) / dot, p[1] + (by * d) / dot];
  });
}

/** The edge's wander for a feathered ground, about -1..+1: ~28 m, ~15 m and
 *  ~6 m waves at oblique angles, so a side of the fort's square shows several
 *  tongues of bare earth reaching into the grass and bays of grass between. */
function featherWander(e, n) {
  return 0.55 * Math.sin(0.211 * e + 0.137 * n + 0.4)
       + 0.30 * Math.sin(-0.173 * e + 0.389 * n + 1.9)
       + 0.15 * Math.sin(0.83 * e - 0.61 * n + 2.6);
}

/**
 * How much of a feathered ground covers (e, n), 0..1: all of it inside the
 * ring, none of it at the skirt's far edge, and between them a short ramp whose
 * middle wanders from the ring to four fifths of the way out. Never reaches the
 * skirt's own outer line, so the skirt has no edge of its own to show.
 */
function featherCover(ring, width, e, n) {
  const s = edgeDistance(ring, e, n) * (pointInPolygon(ring, e, n) ? -1 : 1);
  // A wandering middle and a fine fray, over a short ramp: worn tongues and
  // bays of grass with soft edges, not a veil of dust laid evenly over the band.
  const fray = Math.sin(1.93 * e + 0.71 * n + 0.3) * Math.sin(-0.57 * e + 2.11 * n + 1.1);
  const mid = width * (0.40 + 0.30 * featherWander(e, n) + 0.10 * fray);
  const ramp = width * 0.14;
  const t = Math.min(1, Math.max(0, (s - (mid - ramp)) / (2 * ramp)));
  return 1 - t * t * (3 - 2 * t);
}

/** A ring, with any repeated closing vertex dropped. */
function ring(path) {
  const pts = path.map((p) => [p[0], p[1]]);
  while (pts.length > 1
    && Math.abs(pts[0][0] - pts[pts.length - 1][0]) < 1e-6
    && Math.abs(pts[0][1] - pts[pts.length - 1][1]) < 1e-6) pts.pop();
  return pts;
}

/** Whether a run's own path closes a ring, which is what lets a record state an
 *  interior without stating a second set of coordinates. */
function closes(path) {
  return Array.isArray(path) && path.length >= 4
    && Math.abs(path[0][0] - path[path.length - 1][0]) < 1e-6
    && Math.abs(path[0][1] - path[path.length - 1][1]) < 1e-6;
}

function bboxOf(pts) {
  const b = { minE: Infinity, maxE: -Infinity, minN: Infinity, maxN: -Infinity };
  for (const [e, n] of pts) {
    if (e < b.minE) b.minE = e;
    if (e > b.maxE) b.maxE = e;
    if (n < b.minN) b.minN = n;
    if (n > b.maxN) b.maxN = n;
  }
  return b;
}

/**
 * Sutherland–Hodgman: clip a polygon to one axis-aligned half-plane. Four calls
 * clip it to a grid cell, which is how the treatment gets an EXACT boundary at
 * the fence line without a ragged edge and without T-junctions — two
 * neighbouring cells cut the same polygon edge at the same point, so their
 * vertices coincide and the drape cannot crack between them.
 */
function clipHalf(poly, axis, value, keepBelow) {
  const inside = (p) => (keepBelow ? p[axis] <= value + 1e-9 : p[axis] >= value - 1e-9);
  const out = [];
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[j];
    const b = poly[i];
    const ai = inside(a);
    const bi = inside(b);
    if (ai !== bi) {
      const t = (value - a[axis]) / ((b[axis] - a[axis]) || 1);
      out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    }
    if (bi) out.push(b);
  }
  return out;
}

/** Twice the signed area of a ring: positive counter-clockwise. */
function area2(pts) {
  let a = 0;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    a += pts[j][0] * pts[i][1] - pts[i][0] * pts[j][1];
  }
  return a;
}

/**
 * Ear clipping, on rings of at most a dozen vertices — the pieces a grid cell
 * cuts out of an interior. Returns index triples into `pts`. It is here rather
 * than a triangle fan because a cell that straddles a REFLEX corner clips to an
 * L, and a fan across an L lays a triangle where there is no ground.
 */
function earClip(pts) {
  const n = pts.length;
  if (n < 3) return [];
  if (n === 3) return [[0, 1, 2]];
  const ccw = area2(pts) > 0;
  const idx = [];
  for (let i = 0; i < n; i++) idx.push(i);
  const cross = (a, b, c) => (pts[b][0] - pts[a][0]) * (pts[c][1] - pts[a][1])
    - (pts[b][1] - pts[a][1]) * (pts[c][0] - pts[a][0]);
  const inTri = (a, b, c, p) => {
    const d1 = cross(a, b, p);
    const d2 = cross(b, c, p);
    const d3 = cross(c, a, p);
    const neg = d1 < -1e-12 || d2 < -1e-12 || d3 < -1e-12;
    const pos = d1 > 1e-12 || d2 > 1e-12 || d3 > 1e-12;
    return !(neg && pos);
  };
  const out = [];
  let guard = n * n + 8;
  while (idx.length > 3 && guard-- > 0) {
    let cut = false;
    for (let k = 0; k < idx.length; k++) {
      const a = idx[(k + idx.length - 1) % idx.length];
      const b = idx[k];
      const c = idx[(k + 1) % idx.length];
      const turn = cross(a, b, c);
      if ((ccw ? turn : -turn) <= 1e-12) continue;
      let clear = true;
      for (const m of idx) {
        if (m === a || m === b || m === c) continue;
        if (inTri(a, b, c, m)) { clear = false; break; }
      }
      if (!clear) continue;
      out.push([a, b, c]);
      idx.splice(k, 1);
      cut = true;
      break;
    }
    if (!cut) break;
  }
  if (idx.length === 3) out.push([idx[0], idx[1], idx[2]]);
  return out;
}

function clipToCell(poly, e0, e1, n0, n1) {
  let p = poly;
  p = clipHalf(p, 0, e0, false); if (p.length < 3) return null;
  p = clipHalf(p, 0, e1, true); if (p.length < 3) return null;
  p = clipHalf(p, 1, n0, false); if (p.length < 3) return null;
  p = clipHalf(p, 1, n1, true); if (p.length < 3) return null;
  return p;
}

/* -------------------------------------------------------------------------- */
/* the surfaces                                                                */
/* -------------------------------------------------------------------------- */

function hash(x, y) {
  let h = Math.imul(x + 17, 374761393) ^ Math.imul(y + 31, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

/**
 * The garden bed's drills, painted into a canvas — the one yard surface that
 * keeps one (T-2090). A bed's pattern belongs to the BED's own frame (the drills
 * run down its length), which world-space noise cannot know, so the drills and
 * the row of green standing up each are painted here; everything finer, the
 * grain and the relief, is the road's grit laid over them in world space by
 * `yardGround()`. The pattern varies ACROSS the bed (`v`) so the drills run
 * ALONG it, which is the axis the caller aligns with the bed's own length.
 *
 * The scale is one tile per `period` metres, set by the caller.
 */
function bedTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const image = ctx.createImageData(canvas.width, canvas.height);
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const v = y / (canvas.height - 1);
      // A tilled bed: dark worked earth with the drill rows in it, and a little
      // clumping in the crop so a row is plants and not a stripe.
      const clump = (hash(x >> 2, y >> 2) - 0.5) * 10;
      const drill = Math.abs(((v * 4) % 1) - 0.5) * 2;
      const crop = Math.exp(-(((drill - 0.0) / 0.30) ** 2));
      const rgb = [86 - drill * 8 + crop * (18 + clump),
        70 - drill * 6 + crop * (58 + clump * 2),
        52 - drill * 4 + crop * (16 + clump)];
      const i = (y * canvas.width + x) * 4;
      image.data[i] = Math.max(0, Math.min(255, rgb[0]));
      image.data[i + 1] = Math.max(0, Math.min(255, rgb[1]));
      image.data[i + 2] = Math.max(0, Math.min(255, rgb[2]));
      image.data[i + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = 'yard-garden_bed';
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.anisotropy = 4;
  return texture;
}

/**
 * T-2013 — THE ROAD'S DIRT, for the ground at the doors. The owner, on dev:
 * "that texture is not nearly as nice as the road texture ... make those areas
 * with dirt the same as where the road is". So `road_earth` has no canvas: it is
 * the road ribbon's fragment shading cut down to what a flat patch needs — the
 * same 256 px grit tile over the same 1.6 m, sampled in WORLD east/north as the
 * road samples it (so the grain runs straight on across the join), the same
 * worn-earth lane and between-lane tones mixed by the same kind of value noise,
 * the same 35 m broad tone, and the grit's relief as the normal. What it leaves
 * out is everything that belongs to a street's frame: lanes along an axis,
 * ruts, shoulders and sod islands.
 *
 * T-2090 — EVERY YARD SURFACE ON THE SHARED TILES. The owner, 2026-10-04: "the
 * road texture is beautiful I am thinking you can update and improve all the
 * other grass and land textures in the same way". The road_earth shading above
 * is now the shading of every earth in a yard, and the dooryard green is drawn
 * on T-2089's grass grain the same way:
 *
 *   `worn_earth`     the road's grit and its worn-earth tones, as road_earth,
 *                    with the two swinging wheel tracks the canvas used to
 *                    carry (in the yard's own frame, period 7 m) and hoof pocks
 *                    at ~0.2 m. So a wagon yard is the road's dirt, turned in.
 *   `trodden_earth`  the grit again, on the road's BETWEEN-lane earth darkened a
 *                    fifth (no wheel has been in a pound, so no lane is lighter
 *                    than the rest), poached in ~0.3 m patches.
 *   `garden_bed`     its drills stay a canvas (they run in the bed's frame); the
 *                    grit's grain and relief are laid over them in world space.
 *   `dooryard_green` the grass grain (grass-grain.js, 256 px over 1.6 m, the
 *                    terrain's own tile), a kept-green tone pair mixed by
 *                    0.5-2 m clumps, the 35 m broad tone, lit through the
 *                    grain's normal — the sward's surface, cropped short.
 *
 * Every grain is read over its tile's own mean, so `mix(1, grain, k)` averages
 * 1.0 and a surface's mean colour is its tone pair's. Nothing here adds a draw
 * call: each surface is still one mesh, and the canvases it replaces are gone.
 */
const YARD_HEAD = /* glsl */`
varying vec3 vYardWorld;
varying vec2 vYardUv;
uniform sampler2D uGrit;
uniform float uGritM;
uniform float uGritMean;
uniform vec3 uDirtLane;
uniform vec3 uDirtRest;
uniform sampler2D uSward;
uniform float uSwardM;
uniform float uSwardMean;
float yardHash(vec2 p) {
  vec3 q = fract(vec3(p.xyx) * 0.1031);
  q += dot(q, q.yzx + 33.33);
  return fract((q.x + q.y) * q.z);
}
float yardNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(yardHash(i), yardHash(i + vec2(1.0, 0.0)), u.x),
             mix(yardHash(i + vec2(0.0, 1.0)), yardHash(i + vec2(1.0, 1.0)), u.x), u.y);
}
`;

/** The road's dirt, per fragment: grit, lane/rest wear, broad tone. `extra` is
 *  spliced in before the grain is applied, to mark a yard's own use on it. */
const earthFragment = (extra = '') => /* glsl */`
  vec2 yardEN = vec2(vYardWorld.x, -vYardWorld.z);
  vec4 yardGrit = texture2D(uGrit, yardEN / uGritM);
  float yardGrain = yardGrit.r / max(uGritMean, 1e-6);
  float yardWear = 0.6 * yardNoise(yardEN / 3.0) + 0.4 * yardNoise(yardEN / 1.1 + 7.3);
  float yardBroad = 0.93 + 0.14 * yardNoise(yardEN / 35.0);
  vec3 yardDirt = mix(uDirtRest, uDirtLane, smoothstep(0.15, 0.75, yardWear)) * yardBroad;${extra}
  diffuseColor.rgb = min(yardDirt * mix(1.0, yardGrain, 0.65), vec3(1.0));
  vec2 yardXY = yardGrit.gb * 2.0 - 1.0;
`;

const YARD_FRAGMENT = {
  road_earth: earthFragment(),
  // A wagon yard: the canvas's two soft wheel tracks, deliberately not straight
  // (a yard is turned in, not driven down), and hoof pocks.
  worn_earth: earthFragment(`
  float yardU = fract(vYardUv.x);
  float yardSw = 0.05 * sin(fract(vYardUv.y) * 6.2832);
  float yardRut = exp(-pow((yardU - 0.32 - yardSw) / 0.075, 2.0))
                + exp(-pow((yardU - 0.74 + yardSw) / 0.075, 2.0));
  float yardHoof = smoothstep(0.70, 0.90, yardNoise(yardEN / 0.22 + 11.0));
  yardDirt *= (1.0 - 0.11 * yardRut) * (1.0 - 0.06 * yardHoof);`),
  // A pound: poached, not rutted.
  trodden_earth: earthFragment(`
  float yardPoach = smoothstep(0.62, 0.80, yardNoise(yardEN / 0.3 + 3.7));
  yardDirt *= 1.0 - 0.11 * yardPoach;`),
  // The bed's own canvas (map_fragment, kept), with the grit's grain over it.
  garden_bed: /* glsl */`
  #include <map_fragment>
  vec2 yardEN = vec2(vYardWorld.x, -vYardWorld.z);
  vec4 yardGrit = texture2D(uGrit, yardEN / uGritM);
  float yardGrain = yardGrit.r / max(uGritMean, 1e-6);
  diffuseColor.rgb = min(diffuseColor.rgb * mix(1.0, yardGrain, 0.5), vec3(1.0));
  vec2 yardXY = (yardGrit.gb * 2.0 - 1.0) * 0.8;
`,
  // Kept green: the grass grain, sheared by a 3 m noise so its 1.6 m repeat
  // never lines up into rows, over 0.5-2 m clumps of a light and a dark green.
  // Its relief is the sward's, a little flatter: this is grass kept down.
  dooryard_green: /* glsl */`
  vec2 yardEN = vec2(vYardWorld.x, -vYardWorld.z);
  vec4 yardSw = texture2D(uSward, yardEN / uSwardM + vec2(0.31, 0.23) * yardNoise(yardEN / 3.0 + 4.1));
  float yardGrain = yardSw.r / max(uSwardMean, 1e-6);
  float yardClump = 0.6 * yardNoise(yardEN / 1.4 + 2.9) + 0.4 * yardNoise(yardEN / 0.55 + 5.1);
  float yardBroad = 0.93 + 0.14 * yardNoise(yardEN / 35.0 + 1.7);
  vec3 yardGreen = mix(uDirtRest, uDirtLane, smoothstep(0.25, 0.75, yardClump)) * yardBroad;
  diffuseColor.rgb = min(yardGreen * mix(1.0, yardGrain, mix(0.25, 0.45, yardClump)), vec3(1.0));
  vec2 yardXY = (yardSw.gb * 2.0 - 1.0) * 0.7;
`,
};

const YARD_NORMAL = /* glsl */`
  vec3 yardTn = normalize(vec3(yardXY, 1.0));
  vec3 yardEastV = normalize((viewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
  vec3 yardT = normalize(yardEastV - normal * dot(yardEastV, normal));
  vec3 yardB = cross(normal, yardT);
  normal = normalize(yardT * yardTn.x + yardB * yardTn.y + normal * yardTn.z);
`;

/**
 * The tone pair each surface is mixed between (sRGB 0-255). The earths are the
 * road's own (`streets.js` DIRT_TONES); the pound's is the road's between-lane
 * earth and that earth a fifth darker. The green is this file's argued kept
 * green — the canvas's mean held, its clump range made the pair — because no
 * record states a dooryard's colour; the bed's tones live in its canvas.
 */
const WORN = DIRT_TONES.worn_earth;
const YARD_TONES = {
  road_earth: WORN,
  worn_earth: WORN,
  trodden_earth: { lane: WORN.rest, rest: WORN.rest.map((c) => Math.round(c * 0.82)) },
  garden_bed: WORN,
  dooryard_green: { lane: [104, 132, 66], rest: [92, 112, 58] },
};

/** A yard surface's material on the shared tiles (T-2013, T-2090). Set before
 *  `confidence.patch()`, which chains whatever `onBeforeCompile` it finds. */
function yardGround(mat, surface, tiles) {
  const tones = YARD_TONES[surface];
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, {
      uGrit: { value: tiles.grit.texture },
      uGritM: { value: GRIT_TILE_M },
      uGritMean: { value: tiles.grit.mean },
      uDirtLane: { value: linearTone(tones.lane) },
      uDirtRest: { value: linearTone(tones.rest) },
      ...swardUniforms(tiles.sward),
    });
    shader.vertexShader = `varying vec3 vYardWorld;\nvarying vec2 vYardUv;\n${shader.vertexShader}`.replace(
      '#include <begin_vertex>',
      '#include <begin_vertex>\n  vYardWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;\n  vYardUv = uv;');
    shader.fragmentShader = `${YARD_HEAD}\n${shader.fragmentShader}`
      .replace('#include <map_fragment>', YARD_FRAGMENT[surface])
      .replace('#include <normal_fragment_maps>', YARD_NORMAL);
  };
}

/** How big one tile of each surface is on the ground, in metres. */
const PERIOD_M = { worn_earth: 7.0, trodden_earth: 3.1, road_earth: 1.0, garden_bed: 1.8, dooryard_green: 2.4 };

/**
 * The three treatments, as the surfaces they are made of. `base` covers the
 * whole interior; `beds` and `path` are laid only where the geometry below
 * derives room for them, so a treatment with neither is simply its base.
 */
const TREATMENTS = {
  worn_earth: { base: 'worn_earth', fringe: [0.66, 0.86, 0.74], alpha: [0.96, 0.62] },
  trodden_earth: { base: 'trodden_earth', fringe: [0.80, 0.90, 0.84], alpha: [0.97, 0.78] },
  road_earth: { base: 'road_earth', fringe: [1, 1, 1], alpha: [1.0, 0.35] },
  dooryard_garden: {
    base: 'dooryard_green', beds: 'garden_bed', path: 'worn_earth',
    fringe: [1.0, 1.02, 0.94], alpha: [0.95, 0.72],
  },
};

/* -------------------------------------------------------------------------- */
/* laying one region                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Grid `poly`, clip every cell to it, drape the result on the terrain and push
 * it into `buf`. `frame` gives the (origin, u axis) the texture is laid in;
 * `fringeOf` returns the 0..1 "how far inside the fence am I" of a point, which
 * the vertex colour carries.
 *
 * A cell whose clipped piece has any foot in the river mask is dropped whole —
 * the same refusal the fence itself makes, for the same reason: a yard marching
 * into the water would be a claim about a shoreline this layer knows nothing of.
 */
function layRegion(buf, poly, terrain, o) {
  const { frame, period, lift, level, tint, alpha, fringeOf, coverOf = null } = o;
  const b = bboxOf(poly);
  const e0 = Math.floor(b.minE / CELL_M) * CELL_M;
  const n0 = Math.floor(b.minN / CELL_M) * CELL_M;
  let cells = 0;
  for (let ce = e0; ce < b.maxE; ce += CELL_M) {
    for (let cn = n0; cn < b.maxN; cn += CELL_M) {
      const cell = clipToCell(poly, ce, ce + CELL_M, cn, cn + CELL_M);
      if (!cell) continue;
      let wet = false;
      const verts = cell.map(([e, n]) => {
        if (terrain.isWater?.(e, n)) wet = true;
        const de = e - frame.e;
        const dn = n - frame.n;
        // The texture's own frame: `u` along the region's long axis, so a bed's
        // drills run down the bed rather than across the town.
        const u = (de * frame.ux + dn * frame.un) / period;
        const v = (-de * frame.un + dn * frame.ux) / period;
        const f = fringeOf(e, n);
        return {
          x: e, y: terrain.surfaceHeight(e, n) + lift, z: -n, u, v,
          r: tint[0] + (1 - tint[0]) * f,
          g: tint[1] + (1 - tint[1]) * f,
          bl: tint[2] + (1 - tint[2]) * f,
          a: (alpha[1] + (alpha[0] - alpha[1]) * f) * (coverOf ? coverOf(e, n) : 1),
        };
      });
      if (wet) continue;
      // Ear-clipped rather than fanned. A cell that holds a REFLEX corner of the
      // interior — the Western Hotel's yard has one where it wraps the hotel's
      // own south-east corner, the Sauganash's has one at Carpenter's shop —
      // clips to an L, and a fan from vertex zero lays a triangle of dirt
      // outside the fence. There are only two such corners in the whole town and
      // they would each have cost about a square metre, which is exactly the
      // kind of thing that is easier to do right than to notice.
      for (const [a, b, c] of earClip(cell)) {
        for (const p of [verts[a], verts[b], verts[c]]) {
          buf.pos.push(p.x, p.y, p.z);
          buf.uv.push(p.u, p.v);
          buf.col.push(p.r, p.g, p.bl, p.a);
          buf.conf.push(level);
        }
      }
      cells += 1;
    }
  }
  return cells;
}

/* -------------------------------------------------------------------------- */
/* deriving what a treatment covers                                            */
/* -------------------------------------------------------------------------- */

/**
 * The interiors an enclosure record encloses, with the treatment each carries.
 *
 * A record states the treatment in its own `ground.treatment`. WHERE the ground
 * is comes from one of two places and never from a guess:
 *
 *   * `ground.interior_local_enu_m` — an authored ring, which is what a yard
 *     whose fourth side is a BUILDING needs. The Western Hotel's yard is closed
 *     by the hotel and its stable, and the Sauganash's by the hotel and Philo
 *     Carpenter's shop; a fence line alone cannot say where that ground stops.
 *     T-0097 lets that field carry an ARRAY OF RINGS as well as one ring, because
 *     the ground a record covers is not always simply connected: the fort's apron
 *     is the band OUTSIDE its walls, which is a frame of four bands and not a
 *     disc, and a record that could only state one ring would have had to claim
 *     the parade inside the walls as well to say it.
 *   * otherwise every run whose own path CLOSES A RING is its own interior,
 *     which is what the pound and each of the fifteen garden plots already are.
 *     No new coordinate is authored for any of them.
 *
 * A record may also state `ground.fringe_ring_local_enu_m`: the ONE ring the
 * trampled-grass fringe is measured from, for a treatment whose interiors are
 * several. Without it each band would feather at its own four edges, drawing a
 * grassy seam along the wall and along every internal join — the opposite of
 * what the fort's plates show, which is bare earth right up to the pickets.
 */
function interiorsOf(record, problems) {
  const ground = record.ground ?? {};
  const treatment = ground.treatment ?? null;
  if (!treatment) return [];
  if (!TREATMENTS[treatment]) {
    problems.push(`yards: ${record.id} states ground treatment '${treatment}', which this `
      + 'layer does not build — no ground is laid inside that fence');
    return [];
  }
  const level = LEVEL[ground.confidence] ?? 1;
  const out = [];
  const authored = ground.interior_local_enu_m;
  // One ring is `[[e, n], ...]` and several are `[[[e, n], ...], ...]`, so the
  // depth of the first coordinate is what tells them apart — no flag, and a
  // record written before T-0097 reads exactly as it always did.
  const many = Array.isArray(authored) && Array.isArray(authored[0])
    && Array.isArray(authored[0][0]);
  const fringeRing = Array.isArray(ground.fringe_ring_local_enu_m)
    && ground.fringe_ring_local_enu_m.length >= 3
    ? ring(ground.fringe_ring_local_enu_m) : null;
  if (many) {
    authored.forEach((r, i) => {
      if (!Array.isArray(r) || r.length < 3) return;
      out.push({ id: `${record.id}__interior_${i}`, record: record.id, treatment, level,
        pts: ring(r), fringePts: fringeRing });
    });
  } else if (Array.isArray(authored) && authored.length >= 3) {
    out.push({ id: `${record.id}__interior`, record: record.id, treatment, level,
      pts: ring(authored), fringePts: fringeRing });
  } else {
    for (const run of record.runs ?? []) {
      if (!closes(run.path_local_enu_m)) continue;
      out.push({ id: `${record.id}__${run.id ?? out.length}`, record: record.id,
        treatment, level, pts: ring(run.path_local_enu_m) });
    }
  }
  if (!out.length) {
    problems.push(`yards: ${record.id} states a ground treatment and encloses nothing this `
      + 'layer can bound — no run closes a ring and the record authors no interior');
  }
  return out;
}

/** The gateway that stands on this interior's own boundary, or null. A record
 *  states a point rather than a run id, so the gate that belongs here is the one
 *  that is actually on this ring. */
function gateOf(record, pts) {
  let best = null;
  for (const o of record.openings ?? []) {
    const at = o.at_local_enu_m;
    if (!Array.isArray(at) || at.length < 2) continue;
    const d = edgeDistance(pts, at[0], at[1]);
    if (d < 1.0 && (!best || d < best.d)) best = { d, e: at[0], n: at[1], width: o.width_m ?? 1.07 };
  }
  return best;
}

/** The rectangle a region is laid in, as a ring — in the interior's own axes, so
 *  a bed and a path are stated in the frame the plot is stated in. */
function rectRing(frame, u0, u1, v0, v1) {
  const at = (u, v) => [
    frame.e + u * frame.ux - v * frame.un,
    frame.n + u * frame.un + v * frame.ux,
  ];
  return [at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)];
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * @param {object} o records (the enclosure records) · terrain · confidence ·
 *                   problems
 * @returns {{group: THREE.Group, interiors: object[], census: object,
 *            suppressesSward: function, treatmentAt: function, dispose: function}}
 */
export function createFencedGround({
  records = [], terrain, confidence = null, problems = [],
} = {}) {
  const group = new THREE.Group();
  group.name = 'yard-ground';
  const out = {
    group,
    interiors: [],
    census: { interiors: 0, cells: 0, beds: 0, paths: 0, byTreatment: {} },
    suppressesSward: () => false,
    treatmentAt: () => null,
    dispose: () => {},
  };
  if (!terrain || !records.length) return out;

  for (const record of records) {
    for (const interior of interiorsOf(record, problems)) {
      interior.bbox = bboxOf(interior.pts);
      interior.gate = gateOf(record, interior.pts);
      interior.at = openestPoint(interior.pts, interior.bbox);
      out.interiors.push(interior);
    }
  }
  if (!out.interiors.length) return out;

  // T-2125: the feathered grounds, one per outer ring however many interiors
  // share it — each with its skirt (the ring pushed out by FEATHER_M, as one
  // quad per side) and the cover the drape and the sward both read.
  const feathers = new Map();
  for (const interior of out.interiors) {
    const width = FEATHER_M[interior.treatment];
    const ring = interior.fringePts;
    if (!width || !ring) continue;
    let f = feathers.get(ring);
    if (f === undefined) {
      const outer = offsetConvexRing(ring, width);
      f = outer ? {
        ring, width, outer, bbox: bboxOf(outer), interior,
        // Each quad wound anticlockwise, as every interior is, so its
        // triangles face up and are not culled.
        skirt: ring.map((p, i) => {
          const q = [p, ring[(i + 1) % ring.length], outer[(i + 1) % ring.length], outer[i]];
          return signedArea2(q) > 0 ? q : q.reverse();
        }),
        cover: (e, n) => featherCover(ring, width, e, n),
      } : null;
      if (!f) {
        problems.push(`yards: ${interior.record}'s outer ring is not convex — its ground is `
          + 'not feathered into the sward and stops at the ring');
      }
      feathers.set(ring, f);
    }
    if (f) interior.feather = f;
  }

  /** Is this point inside a fenced interior — the question `flora.js` asks
   *  through `main.js`'s block-list composition, and the question the smoke asks
   *  through `plantableAt`. Cheap rejection on the bounding box first: this runs
   *  once per lattice slot per frame rebuild. */
  out.suppressesSward = (e, n) => {
    for (const i of out.interiors) {
      const b = i.bbox;
      if (e < b.minE || e > b.maxE || n < b.minN || n > b.maxN) continue;
      if (pointInPolygon(i.pts, e, n)) {
        // T-2125: on a feathered ground the sward thins in at the share the
        // earth thins out, drawn per slot so the same slot always answers.
        return i.feather ? i.feather.cover(e, n) > ditherHash(e, n) : true;
      }
    }
    for (const f of feathers.values()) {
      if (!f) continue;
      const b = f.bbox;
      if (e < b.minE || e > b.maxE || n < b.minN || n > b.maxN) continue;
      if (pointInPolygon(f.outer, e, n) && !pointInPolygon(f.ring, e, n)) {
        return f.cover(e, n) > ditherHash(e, n);
      }
    }
    return false;
  };
  /** Which treatment covers this point, or null — so a gate can ask "is the
   *  ground here a working yard" rather than "is something drawn here". */
  out.treatmentAt = (e, n) => {
    for (const i of out.interiors) {
      const b = i.bbox;
      if (e < b.minE || e > b.maxE || n < b.minN || n > b.maxN) continue;
      if (pointInPolygon(i.pts, e, n)) return i.treatment;
    }
    return null;
  };

  // ---- geometry ---------------------------------------------------------- //

  const buffers = new Map();
  const bufFor = (surface) => {
    if (!buffers.has(surface)) buffers.set(surface, { pos: [], uv: [], col: [], conf: [] });
    return buffers.get(surface);
  };

  for (const interior of out.interiors) {
    const spec = TREATMENTS[interior.treatment];
    const pts = interior.pts;
    const b = interior.bbox;
    // The interior's own axes: `u` along its longer side. Every one of these
    // rings is rectilinear, so the bounding box IS the shape's frame and no
    // principal-axis fiction is needed.
    const wide = (b.maxE - b.minE) >= (b.maxN - b.minN);
    const frame = { e: b.minE, n: b.minN, ux: wide ? 1 : 0, un: wide ? 0 : 1 };
    const uLen = wide ? b.maxE - b.minE : b.maxN - b.minN;
    const vLen = wide ? b.maxN - b.minN : b.maxE - b.minE;
    const reach = FRINGE_M[interior.treatment] ?? 0.8;
    // The fringe is measured from the record's own outer ring where it states
    // one (T-0097) and from this interior's boundary otherwise — which is the
    // same answer for every record that has exactly one interior.
    const fringePts = interior.fringePts ?? pts;
    const fringeOf = (e, n) => Math.min(1, edgeDistance(fringePts, e, n) / reach);

    out.census.cells += layRegion(bufFor(spec.base), pts, terrain, {
      frame, period: PERIOD_M[spec.base], lift: LIFT_M.base, level: interior.level,
      tint: spec.fringe, alpha: spec.alpha, fringeOf, coverOf: interior.feather?.cover ?? null,
    });
    // T-2125: the skirt, laid once per feathered ground (by its first interior),
    // a quad per side of the ring, at the fringe's own tint and the cover's alpha.
    const feather = interior.feather;
    if (feather && feather.interior === interior) {
      for (const quad of feather.skirt) {
        out.census.cells += layRegion(bufFor(spec.base), quad, terrain, {
          frame, period: PERIOD_M[spec.base], lift: LIFT_M.base, level: interior.level,
          tint: spec.fringe, alpha: spec.alpha, fringeOf: () => 0, coverOf: feather.cover,
        });
      }
    }
    out.census.interiors += 1;
    out.census.byTreatment[interior.treatment] =
      (out.census.byTreatment[interior.treatment] ?? 0) + 1;

    // THE BEDS. Laid on the side of the plot AWAY from the gateway, because a
    // gate is where a person and a barrow come in and beds are what they come in
    // to; inset from the fence so a pale is not standing in a drill; capped at
    // four so one rule serves a 28 x 20 ft kitchen plot (which it fills) and a
    // hotel's back yard (where it makes a garden patch in the far corner rather
    // than ploughing the whole yard). Every bed is clipped to the interior on
    // the way in, so none of this can escape its own fence.
    if (spec.beds) {
      const gate = interior.gate;
      const u0 = BED.inset;
      const u1 = Math.max(u0, uLen - BED.inset);
      const v0 = BED.inset;
      const v1 = Math.max(v0, vLen - BED.inset);
      const pitch = BED.width + BED.walk;
      const count = Math.min(BED.most, Math.floor((v1 - v0 + BED.walk) / pitch));
      if (count >= 1) {
        // Which end is "away from the gate", in each axis of the plot's frame.
        const gu = gate ? (gate.e - frame.e) * frame.ux + (gate.n - frame.n) * frame.un : 0;
        const gv = gate ? -(gate.e - frame.e) * frame.un + (gate.n - frame.n) * frame.ux : 0;
        const runLen = Math.min(BED.longest, u1 - u0);
        const bu0 = (gu > uLen / 2) ? u0 : u1 - runLen;
        const bv1 = (gv > vLen / 2) ? v0 + count * pitch - BED.walk : v1;
        for (let k = 0; k < count; k++) {
          const top = bv1 - k * pitch;
          const rect = rectRing(frame, bu0, bu0 + runLen, top - BED.width, top);
          const bed = clipRingToRing(rect, pts);
          if (!bed) continue;
          // The bed's own frame, so its drills run down its length.
          const bb = bboxOf(bed);
          const bedFrame = { e: bb.minE, n: bb.minN, ux: frame.ux, un: frame.un };
          out.census.cells += layRegion(bufFor(spec.beds), bed, terrain, {
            frame: bedFrame, period: PERIOD_M[spec.beds], lift: LIFT_M.bed,
            level: interior.level, tint: [1, 1, 1], alpha: [0.99, 0.99],
            fringeOf: () => 1,
          });
          out.census.beds += 1;
        }
      }
    }

    // THE PATH. From the gateway, straight in across the plot on the inward
    // normal of the side the gate stands on — the way a person walks to the
    // door. Derived from the record's own gateway and the ring it stands on;
    // nothing new is authored, and where a record states no gateway there is no
    // path, which is the honest answer rather than a path from nowhere.
    if (spec.path && interior.gate) {
      const g = interior.gate;
      const inward = inwardNormal(pts, g.e, g.n);
      if (inward) {
        const half = Math.max(0.4, (g.width ?? 1.07) * 0.42);
        const reachIn = Math.max(uLen, vLen);
        const px = -inward.n;
        const pn = inward.e;
        const rect = [
          [g.e + px * half, g.n + pn * half],
          [g.e + inward.e * reachIn + px * half, g.n + inward.n * reachIn + pn * half],
          [g.e + inward.e * reachIn - px * half, g.n + inward.n * reachIn - pn * half],
          [g.e - px * half, g.n - pn * half],
        ];
        const path = clipRingToRing(rect, pts);
        if (path) {
          const pb = bboxOf(path);
          out.census.cells += layRegion(bufFor(spec.path), path, terrain, {
            frame: { e: pb.minE, n: pb.minN, ux: inward.e, un: inward.n },
            period: PERIOD_M[spec.path] * 0.4, lift: LIFT_M.path, level: interior.level,
            tint: [1, 1, 1], alpha: [0.94, 0.94], fringeOf: () => 1,
          });
          out.census.paths += 1;
        }
      }
    }
  }

  // The two shared tiles, made once for the whole layer: the road's grit for the
  // earths and the bed, the grass grain for the green.
  const tiles = { grit: roadGrit(), sward: swardTexture() };
  const disposables = [tiles.grit.texture, tiles.sward];
  for (const [surface, buf] of buffers) {
    if (!buf.pos.length) continue;
    const geo = new THREE.BufferGeometry();
    geo.name = `yard-${surface}`;
    geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(buf.uv, 2));
    // itemSize 4: three.js reads the fourth component as vertex alpha, which is
    // what carries the fringe out into the sward without a seam.
    geo.setAttribute('color', new THREE.Float32BufferAttribute(buf.col, 4));
    geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
    // Scratch from here (T-2063): the geometry holds the Float32 copy.
    buf.pos = buf.uv = buf.col = buf.conf = null;
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    // Every surface draws the shared tiles (T-2013, T-2090); only the bed keeps
    // a canvas, for its drills.
    const map = surface === 'garden_bed' ? bedTexture() : null;
    const mat = new THREE.MeshStandardMaterial({
      map,
      vertexColors: true,
      transparent: true,
      alphaTest: 0.02,
      depthWrite: false,
      roughness: 1,
      metalness: 0,
      polygonOffset: true,
      // The road ribbon's own offset, and for the road's own reason: a surface
      // draped on the terrain it is drawn against loses the depth test in
      // patches once precision has degraded, and one unit is nothing at that
      // range. The vertices are untouched — the drape is the terrain's.
      polygonOffsetFactor: -8,
      polygonOffsetUnits: -32,
    });
    mat.name = `yard-${surface}`;
    yardGround(mat, surface, tiles);
    confidence?.patch(mat);
    // This layer's own program, for the reason enclosures.js records at length:
    // `customProgramCacheKey` defaults to the SOURCE TEXT of `onBeforeCompile`,
    // which every material `confidence.patch()` touches shares, so two patched
    // materials that agree on their other program parameters share a compiled
    // program and one of them is drawn by the other's shader.
    mat.customProgramCacheKey = () => `chicago4d-yard-${surface}`;
    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = `yard-${surface}`;
    // A ground treatment lies ON the ground: it receives what the town casts
    // over it and casts nothing itself, which is also why it is not in the
    // furniture-shadow policy — there is nothing to take away at `light`.
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    mesh.renderOrder = surface === 'garden_bed' ? 2 : (surface === 'worn_earth' ? 1 : 0);
    group.add(mesh);
    disposables.push(geo, mat);
    if (map) disposables.push(map);
  }
  group.userData.census = out.census;
  if (!group.children.length) {
    problems.push('yards: every fenced interior refused its ground — nothing is laid inside '
      + 'any fence in the town');
  }
  out.dispose = () => { for (const d of disposables) d.dispose?.(); };
  return out;
}

/* -------------------------------------------------------------------------- */
/* helpers used above                                                          */
/* -------------------------------------------------------------------------- */

/** Clip one convex ring to another (possibly L-shaped) ring, by gridding the
 *  first against the second's cells. Used for a bed and a path, both of which
 *  are rectangles that must not escape the interior they were derived inside.
 *  Returns the intersection as a ring, or null if there is none. */
function clipRingToRing(rect, poly) {
  // The rectangle is clipped by every one of the interior's own edge lines,
  // keeping the side the interior's interior is on. For a convex interior that
  // is exact; for an L it is CONSERVATIVE — it keeps the largest convex piece —
  // and a conservative bed is a bed that stays inside its fence, which is the
  // property that matters here.
  let p = rect;
  const ccw = area2(poly) > 0;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[j];
    const b = poly[i];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    if (Math.abs(dx) < 1e-9 && Math.abs(dy) < 1e-9) continue;
    const keep = [];
    const side = (q) => {
      const s = dx * (q[1] - a[1]) - dy * (q[0] - a[0]);
      return ccw ? s : -s;
    };
    for (let m = 0, k = p.length - 1; m < p.length; k = m++) {
      const s0 = side(p[k]);
      const s1 = side(p[m]);
      if ((s0 >= -1e-9) !== (s1 >= -1e-9)) {
        const t = s0 / ((s0 - s1) || 1);
        keep.push([p[k][0] + (p[m][0] - p[k][0]) * t, p[k][1] + (p[m][1] - p[k][1]) * t]);
      }
      if (s1 >= -1e-9) keep.push(p[m]);
    }
    p = keep;
    if (p.length < 3) return null;
  }
  return p.length >= 3 ? p : null;
}

/**
 * The openest point in a ring — the sampled point inside it that is farthest
 * from any of its edges.
 *
 * A CENTROID WILL NOT DO, and the Western Hotel's yard is why: its interior is
 * an L wrapped round the hotel's own south-east corner, and the average of its
 * six corners lands INSIDE THE HOTEL. Anything that wants one point that stands
 * for a yard — a gate probing "what is the ground here", a proof frame standing
 * in it — needs a point that is actually in the yard and not near a fence.
 */
function openestPoint(pts, box) {
  const step = Math.max(0.25,
    Math.min(box.maxE - box.minE, box.maxN - box.minN) / 12);
  let best = null;
  for (let e = box.minE + step / 2; e < box.maxE; e += step) {
    for (let n = box.minN + step / 2; n < box.maxN; n += step) {
      if (!pointInPolygon(pts, e, n)) continue;
      const d = edgeDistance(pts, e, n);
      if (!best || d > best.d) best = { d, e, n };
    }
  }
  return best ? [best.e, best.n] : [(box.minE + box.maxE) / 2, (box.minN + box.maxN) / 2];
}

/** The unit vector pointing INTO the polygon from a point on its boundary. */
function inwardNormal(pts, e, n) {
  let best = null;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const a = pts[j];
    const b = pts[i];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const len2 = dx * dx + dy * dy || 1;
    let t = ((e - a[0]) * dx + (n - a[1]) * dy) / len2;
    t = Math.min(Math.max(t, 0), 1);
    const d = Math.hypot(a[0] + dx * t - e, a[1] + dy * t - n);
    if (!best || d < best.d) {
      const len = Math.sqrt(len2);
      best = { d, e: -dy / len, n: dx / len };
    }
  }
  if (!best) return null;
  // Whichever of the two normals steps inside. A step of a tenth of a metre is
  // well inside every plot here and well outside the numerical noise.
  if (pointInPolygon(pts, e + best.e * 0.1, n + best.n * 0.1)) return { e: best.e, n: best.n };
  if (pointInPolygon(pts, e - best.e * 0.1, n - best.n * 0.1)) return { e: -best.e, n: -best.n };
  return null;
}
