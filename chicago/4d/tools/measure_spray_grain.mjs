/**
 * ROADMAP K57 — THE SHRUB SPRAY'S GRAIN, MEASURED RATHER THAN PREFERRED.
 *
 *   node tools/measure_spray_grain.mjs [--grain fill,plate]... [--bearings N]
 *                                      [--grid N] [--json] [--gate]
 *
 * K56 answered *what a spray stands for* — a leaf MASS, a season's leaves on one
 * shoot — and doubled the count from 16 to 32 because sixteen plates covered
 * 17.7 % of the shell and a visitor could see straight through every clump. It
 * left the finer question open: **at the same total plate area, is the shell
 * better read as 32 masses of 0.4 m or 64 of 0.2 m?**
 *
 * WHY THIS IS A TOOL AND NOT A JUDGEMENT. That question has a number attached in
 * both directions — grain costs triangles and buys coverage — and neither number
 * had ever been printed. K56's own shell-fill figures were taken by a script that
 * was never committed, so they cannot be reproduced and cannot be re-pointed at a
 * candidate. This tool commits the instrument: it reads
 * `renderers/web/js/shrub-grain.js`, which is the SAME arithmetic the scene draws,
 * so a figure here is a figure about the town and not about a port of it.
 *
 * WHAT IT MEASURES, and why each one is here.
 *
 *   plate area ......... the sum of the drawn quads, in archetype units². The
 *                        quantity the parcel holds fixed, and the one figure that
 *                        is comparable with K56's committed table (1.399 → 2.698).
 *   silhouette ......... the convex hull of the projected foliage, per bearing.
 *                        The bush's outline: what the eye takes the plant's size
 *                        to be.
 *   foliage cover ...... the UNION of the projected plates as a fraction of that
 *                        silhouette. **This is the number the parcel turns on**,
 *                        because "you can see straight through it" is a statement
 *                        about union and not about a sum — a sum counts a plate
 *                        twice where two overlap, which is exactly where the eye
 *                        counts it once.
 *   overdraw ........... sum ÷ union. What the extra plates are being spent on.
 *   stem cover ......... the fraction of the projected woody stems that has
 *                        foliage in front of it. K56's second finding: a stem is
 *                        written dark enough to be a black stick wherever the
 *                        shell is open, so this is the number that says whether
 *                        the arching band did its job.
 *   reach .............. the furthest horizontal extent of any plate, against the
 *                        recorded half-width of 1.0. A grain that shrinks plates
 *                        pulls the clump in, and the clump's width is RECORDED —
 *                        so this is the axis on which a finer grain can lose.
 *   plate long side .... in centimetres on a 2.25 m hazel, against the ~10 cm of a
 *                        single hazel leaf. THE BOUND K56 STATED: a plate must
 *                        stay plainly bigger than one leaf, because two triangles
 *                        that claim to be a leaf are a lie the abstraction does
 *                        not tell.
 *   triangles .......... per shrub, and in the wet woods' ring, against the
 *                        1,000,000 the scene budgets at `full` detail.
 *
 * Orthographic projection, not perspective, and deliberately: a perspective
 * reading would fold the viewing distance into an answer about geometry, and the
 * same shrub is drawn from 2 m and from 40 m in one frame.
 *
 * It renders no frame and needs no browser, so it costs about a second — the fast
 * half of this project's two-speed build. `tools/check.sh` parses it; the drawn
 * count it does not touch, which is `tools/measure_sward_draw.mjs`.
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SHRUB_GRAIN, shrubLayout, shrubTriangles } from
  '../renderers/web/js/shrub-grain.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));

const argv = process.argv.slice(2);
const flagVals = (name) => {
  const out = [];
  for (let i = 0; i < argv.length; i++) if (argv[i] === name) out.push(argv[++i]);
  return out;
};
const BEARINGS = Number(flagVals('--bearings')[0] || 24);
const GRID = Number(flagVals('--grid')[0] || 512);
const asJson = argv.includes('--json');
const isGate = argv.includes('--gate');
/** `tools/check.sh` wants the verdict, not the candidate table. */
const quiet = argv.includes('--quiet');

/** The clump this project keeps quoting: a 2.25 m hazel, so 1.125 m per unit. */
const HAZEL_RADIUS_M = 1.125;
/** A single hazel leaf, from the flora dossier's own description. The floor the
 *  plate may not approach: below it the plate stops being a mass of leaves. */
const LEAF_M = 0.10;
/** The wet woods' ring: shrubs drawn standing in `z06_dense_forest`, read off
 *  `tools/measure_sward_draw.mjs` on the published mirror at K57. K54 and K56
 *  quote 156; the census reads 167 there today, after K55 re-dealt the forb
 *  layer, so the number is taken from the census rather than from a document. */
const WET_WOODS_SHRUBS = 167;
/** The scene's triangle budget at `full` detail. */
const TRI_BUDGET = 1_000_000;

function rngFrom(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

/** The archetype's own seed, so this measures the bush the scene draws. */
const SEED = 0x5c123b00;

const cross = (ax, ay, az, bx, by, bz) => [
  ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx,
];

/** Area of one drawn quad, as the two triangles the renderer indexes. */
function quadArea([a, b, c, d]) {
  const tri = (p, q, r) => {
    const n = cross(q[0] - p[0], q[1] - p[1], q[2] - p[2],
      r[0] - p[0], r[1] - p[1], r[2] - p[2]);
    return 0.5 * Math.hypot(n[0], n[1], n[2]);
  };
  // (a, b, c) and (b, d, c) — the same winding `flora.js` pushes.
  return tri(a, b, c) + tri(b, d, c);
}

/** Project onto the screen of a horizontal camera on `bearing` radians. */
function project(p, bearing) {
  const rx = Math.cos(bearing);
  const rz = -Math.sin(bearing);
  return [p[0] * rx + p[2] * rz, p[1]];
}

/** Monotone-chain convex hull of 2-D points, and its area. */
function hull(points) {
  const pts = points.slice().sort((p, q) => (p[0] - q[0]) || (p[1] - q[1]));
  if (pts.length < 3) return { poly: pts, area: 0 };
  const half = (list) => {
    const out = [];
    for (const p of list) {
      while (out.length >= 2) {
        const [ox, oy] = out[out.length - 2];
        const [px, py] = out[out.length - 1];
        if ((px - ox) * (p[1] - oy) - (py - oy) * (p[0] - ox) > 0) break;
        out.pop();
      }
      out.push(p);
    }
    return out;
  };
  const poly = [...half(pts).slice(0, -1), ...half(pts.reverse()).slice(0, -1)];
  let area = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    area += x0 * y1 - x1 * y0;
  }
  return { poly, area: Math.abs(area) / 2 };
}

function inConvex(poly, x, y) {
  for (let i = 0; i < poly.length; i++) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    if ((x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < -1e-12) return false;
  }
  return true;
}

/** Mark a projected quad into `mask`, scanning only its own bounding box. */
function rasterQuad(mask, quad, box, n, gx, gy) {
  const tris = [[quad[0], quad[1], quad[2]], [quad[1], quad[3], quad[2]]];
  const cw = (box.x1 - box.x0) / gx;
  const ch = (box.y1 - box.y0) / gy;
  for (const t of tris) {
    const xs = t.map((p) => p[0]);
    const ys = t.map((p) => p[1]);
    const i0 = Math.max(0, Math.floor((Math.min(...xs) - box.x0) / cw));
    const i1 = Math.min(gx - 1, Math.ceil((Math.max(...xs) - box.x0) / cw));
    const j0 = Math.max(0, Math.floor((Math.min(...ys) - box.y0) / ch));
    const j1 = Math.min(gy - 1, Math.ceil((Math.max(...ys) - box.y0) / ch));
    const [[ax, ay], [bx, by], [cx, cy]] = t;
    const d = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
    if (d === 0) continue;
    for (let j = j0; j <= j1; j++) {
      const y = box.y0 + (j + 0.5) * ch;
      for (let i = i0; i <= i1; i++) {
        const x = box.x0 + (i + 0.5) * cw;
        const w0 = ((bx - ax) * (y - ay) - (by - ay) * (x - ax)) / d;
        const w1 = ((x - ax) * (cy - ay) - (y - ay) * (cx - ax)) / d;
        if (w0 >= 0 && w1 >= 0 && w0 + w1 <= 1) mask[j * gx + i] = 1;
      }
    }
  }
  return n;
}

function measure(grain) {
  const { stems, sprays } = shrubLayout(rngFrom(SEED), grain);
  const plateArea = sprays.reduce((s, p) => s + quadArea(p.corners), 0);
  const reach = Math.max(...sprays.flatMap((p) =>
    p.corners.map(([x, , z]) => Math.hypot(x, z))));
  const longSide = sprays.map((p) => Math.hypot(p.len, p.rise));
  const meanLong = longSide.reduce((a, b) => a + b, 0) / longSide.length;

  const cover = [];
  const stemCover = [];
  const silhouette = [];
  const overdraw = [];
  for (let b = 0; b < BEARINGS; b++) {
    const bearing = (b / BEARINGS) * Math.PI * 2;
    const sprayQuads = sprays.map((p) => p.corners.map((c) => project(c, bearing)));
    const stemQuads = stems.map((s) => s.corners.map((c) => project(c, bearing)));
    const all = sprayQuads.flat();
    const { poly, area: hullArea } = hull(all);
    const xs = all.map((p) => p[0]);
    const ys = [...all.map((p) => p[1]), 0];
    const box = {
      x0: Math.min(...xs), x1: Math.max(...xs),
      y0: Math.min(...ys), y1: Math.max(...ys),
    };
    const span = Math.max(box.x1 - box.x0, box.y1 - box.y0) || 1;
    const gx = Math.max(8, Math.round(GRID * (box.x1 - box.x0) / span));
    const gy = Math.max(8, Math.round(GRID * (box.y1 - box.y0) / span));
    const cw = (box.x1 - box.x0) / gx;
    const ch = (box.y1 - box.y0) / gy;
    const cellArea = cw * ch;

    const foliage = new Uint8Array(gx * gy);
    for (const q of sprayQuads) rasterQuad(foliage, q, box, 0, gx, gy);
    const wood = new Uint8Array(gx * gy);
    for (const q of stemQuads) rasterQuad(wood, q, box, 0, gx, gy);

    let union = 0;
    let woodCells = 0;
    let woodCovered = 0;
    let hullCells = 0;
    for (let j = 0; j < gy; j++) {
      const y = box.y0 + (j + 0.5) * ch;
      for (let i = 0; i < gx; i++) {
        const k = j * gx + i;
        if (foliage[k]) union++;
        if (wood[k]) { woodCells++; if (foliage[k]) woodCovered++; }
        if (inConvex(poly, box.x0 + (i + 0.5) * cw, y)) hullCells++;
      }
    }
    const unionArea = union * cellArea;
    const hullMeasured = hullCells * cellArea || hullArea;
    silhouette.push(hullMeasured);
    cover.push(unionArea / hullMeasured);
    overdraw.push(unionArea > 0
      ? sprayQuads.reduce((s, q) => s + Math.abs(shoelace(q)), 0) / unionArea
      : 0);
    stemCover.push(woodCells ? woodCovered / woodCells : 0);
  }

  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const tri = shrubTriangles(grain);
  return {
    sprays: sprays.length,
    plate: grain.plate,
    triangles: tri,
    wetWoods: tri * WET_WOODS_SHRUBS,
    plateArea,
    silhouette: mean(silhouette),
    cover: mean(cover),
    coverWorst: Math.min(...cover),
    overdraw: mean(overdraw),
    stemCover: mean(stemCover),
    reach,
    longSideM: meanLong * HAZEL_RADIUS_M,
    leafRatio: (meanLong * HAZEL_RADIUS_M) / LEAF_M,
  };
}

/** Projected area of a quad in screen units, for the overdraw ratio. */
function shoelace(q) {
  const order = [q[0], q[1], q[3], q[2]];
  let a = 0;
  for (let i = 0; i < order.length; i++) {
    const [x0, y0] = order[i];
    const [x1, y1] = order[(i + 1) % order.length];
    a += x0 * y1 - x1 * y0;
  }
  return a / 2;
}

/**
 * The candidates, and why these. `plate` at `sqrt(24 + 8) / sqrt(fill + 8)` holds
 * the total plate area of the shipped 32 — which is the parcel's own question,
 * asked at 48 and at 64 — and `plate` 1.00 at the same counts is what refusing to
 * hold it costs. 16 is pre-K56, for the record.
 */
const areaHolding = (fill) => Math.sqrt(32 / (fill + 8));
const CANDIDATES = flagVals('--grain').length
  ? flagVals('--grain').map((s) => {
    const [fill, plate] = s.split(',').map(Number);
    return { label: `${2 * 4 + fill} @ ${plate.toFixed(3)}`, grain: { stems: 4, fill, plate } };
  })
  : [
    // NOT the pre-K56 bush: that one had TWO bands, and this table has three, so
    // its plate area reads 1.387 where K56's committed figure is 1.399. The row is
    // here for the count alone. The `32 @ 1.000` row IS the shipped bush, and its
    // 2.698 reproduces K56's committed plate area to the digit — which is the
    // check that this instrument measures the town and not a port of it.
    { label: '16 @ 1.000 (count only)', grain: { stems: 4, fill: 8, plate: 1.00 } },
    { label: '32 @ 1.000 (K56, shipped)', grain: { stems: 4, fill: 24, plate: 1.00 } },
    { label: '48 @ 0.816 (area held)', grain: { stems: 4, fill: 40, plate: areaHolding(40) } },
    { label: '64 @ 0.707 (area held)', grain: { stems: 4, fill: 56, plate: areaHolding(56) } },
    { label: '48 @ 1.000 (area grows)', grain: { stems: 4, fill: 40, plate: 1.00 } },
    { label: '64 @ 1.000 (area grows)', grain: { stems: 4, fill: 56, plate: 1.00 } },
    { label: '64 @ 0.790 (area +25 %)', grain: { stems: 4, fill: 56, plate: 0.79 } },
  ];

const shipped = measure(SHRUB_GRAIN);
const rows = quiet ? [] : CANDIDATES.map((c) => ({ label: c.label, ...measure(c.grain) }));

if (quiet) {
  console.log(`shipped: ${shipped.sprays} sprays @ plate ${shipped.plate.toFixed(3)} — `
    + `cover ${(shipped.cover * 100).toFixed(1)}% (worst bearing `
    + `${(shipped.coverWorst * 100).toFixed(1)}%), stem cover `
    + `${(shipped.stemCover * 100).toFixed(1)}%, reach ${shipped.reach.toFixed(3)} of the `
    + `recorded half-width, plate ${(shipped.longSideM * 100).toFixed(1)} cm `
    + `(${shipped.leafRatio.toFixed(1)}× a leaf), ${shipped.triangles} triangles`);
} else if (asJson) {
  console.log(JSON.stringify({ bearings: BEARINGS, grid: GRID, rows, shipped }, null, 2));
} else {
  console.log(`shrub spray grain — ${BEARINGS} bearings, ${GRID}-cell silhouette, `
    + 'orthographic\n');
  const head = ['candidate', 'area', 'sil.', 'cover', 'worst', 'over', 'stem',
    'reach', 'plate cm', '×leaf', 'tris', 'wet woods'];
  const fmt = (r) => [
    r.label,
    r.plateArea.toFixed(3),
    r.silhouette.toFixed(3),
    `${(r.cover * 100).toFixed(1)}%`,
    `${(r.coverWorst * 100).toFixed(1)}%`,
    r.overdraw.toFixed(2),
    `${(r.stemCover * 100).toFixed(1)}%`,
    r.reach.toFixed(3),
    (r.longSideM * 100).toFixed(1),
    r.leafRatio.toFixed(1),
    String(r.triangles),
    `${r.wetWoods.toLocaleString('en-US')} (${(100 * r.wetWoods / TRI_BUDGET).toFixed(1)}%)`,
  ];
  const table = [head, ...rows.map(fmt)];
  const w = head.map((_, i) => Math.max(...table.map((r) => r[i].length)));
  for (const [n, r] of table.entries()) {
    console.log(r.map((c, i) => (i === 0 ? c.padEnd(w[i]) : c.padStart(w[i]))).join('  '));
    if (n === 0) console.log(w.map((x) => '-'.repeat(x)).join('  '));
  }
  console.log(`\nSHIPPED: ${shipped.sprays} sprays @ plate ${shipped.plate.toFixed(3)} — `
    + `cover ${(shipped.cover * 100).toFixed(1)}%, stem cover `
    + `${(shipped.stemCover * 100).toFixed(1)}%, reach ${shipped.reach.toFixed(3)}, `
    + `${shipped.triangles} triangles`);
}

/**
 * THE GATE. Three assertions, and each is the bound a candidate could break
 * rather than a number a run chose.
 *
 *   1. the plate stays a MASS — its long side stays at least twice a hazel leaf,
 *      because at one leaf the abstraction is claiming to draw something it
 *      cannot (K56, L124).
 *   2. the clump keeps its RECORDED width — reach ≥ 0.95 of the half-width the
 *      record carries. A finer grain shrinks the plates, and the plates are what
 *      the eye reads the width off; the width is not a rendering choice.
 *   3. the shell is not see-through — foliage cover ≥ 40 % at EVERY bearing. A
 *      ratchet, not a target: K56's 32 sprays read 33.0 % at their worst bearing
 *      and K57's 48 read 43.0 %, so the bar sits above what was shipped yesterday
 *      and below what ships today, and the count cannot fall back unnoticed.
 */
if (isGate) {
  const fails = [];
  if (shipped.leafRatio < 2) {
    fails.push(`plate long side ${(shipped.longSideM * 100).toFixed(1)} cm is `
      + `${shipped.leafRatio.toFixed(2)}× a ${LEAF_M * 100} cm leaf, under 2×`);
  }
  if (shipped.reach < 0.95) {
    fails.push(`reach ${shipped.reach.toFixed(3)} of the recorded half-width, under 0.95`);
  }
  if (shipped.coverWorst < 0.40) {
    fails.push(`worst-bearing foliage cover ${(shipped.coverWorst * 100).toFixed(1)}%, under 40%`);
  }
  for (const f of fails) console.error(`FAIL: ${f}`);
  console.log(fails.length ? 'GATE: FAIL' : 'GATE: PASS');
  process.exit(fails.length ? 1 : 0);
}
