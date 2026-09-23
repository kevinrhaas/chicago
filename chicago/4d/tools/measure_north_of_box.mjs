/**
 * measure_north_of_box.mjs — what the renderer does with the committed town
 * that stands OUTSIDE the modelled ground, measured rather than assumed.
 *
 * T-1067. `data/terrain/epochs/e1834_harbor_cut/heightfield.json` boxes the
 * modelled ground at n +400 m, and T-1060 committed Kinzie's Addition's streets
 * running north to n +1029.71. Nothing in the gate could say what a visitor
 * therefore sees, because the two files never meet: the terrain gate measures
 * the ground against the mesh drawn FROM it (measure_terrain_fit.mjs), and the
 * street gate measures corridors against the plat. Neither asks whether a
 * street is standing on modelled ground at all.
 *
 * THE ANSWER IS SMALLER THAN THE TICKET ASSUMED, AND THAT IS THE POINT of
 * measuring first. Eleven of the Addition's thirteen streets are
 * `opened: false, track_width_m: 0` — platted, unopened, unworn — and
 * `streets.js` § createStreets filters exactly those out before it builds
 * anything, so they draw NOTHING and cannot be draped on anything. This tool
 * therefore separates the two populations and never adds them up:
 *
 *   DRAWN        a ribbon exists, its vertices are draped on
 *                `terrain.surfaceHeight()`, and off the grid that is a constant.
 *   PLATTED ONLY the record stands off the grid but compiles to no geometry;
 *                it is a claim about ground that is not modelled, not a fiction
 *                that is drawn.
 *
 * WHAT IS MEASURED, and why each number rather than a screenshot:
 *
 *   1. THE BOUNDARY ITSELF, walked at the terrain cell. `terrain.js`
 *      § Heightfield answers `sample()` with `fallbackY` — the constant 0, the
 *      summer-1835 water surface — at any (e, n) its `contains()` refuses. So
 *      the box edge is a scarp whose height is the modelled ground's own, and
 *      that is a property of the box, not of anything built on it.
 *
 *   2. WHETHER THE WALKER CAN COME BACK. `walker.js` WALK.stepUp is 0.35 m and
 *      downhill is free. Perimeter where the ground inside stands more than
 *      0.35 m above the constant is a ONE-WAY DOOR: the visitor walks out and
 *      the step-up rule refuses the way back. That is what makes the gap
 *      visible to somebody who is not reading JSON, and it is measured in
 *      metres of perimeter rather than asserted.
 *
 *   3. OFF-GRID STREET, in metres and by WHICH edge it leaves through, for the
 *      drawn and the platted-only populations separately. Both track edges are
 *      walked as well as the centreline, because a ribbon whose centre is
 *      inside and whose kerb is not is still half on a constant.
 *
 * It does NOT measure the 54 blocks T-1061 read. That file is a reading of paper
 * — its own clause 5 says it authors no ground — and seating it here to make a
 * count would be this tool inventing the very thing the reading refused to.
 * The streets are the Addition's committed ENU geometry and they are what is
 * measured.
 *
 *   node tools/measure_north_of_box.mjs              table + verdict
 *   node tools/measure_north_of_box.mjs --json       machine-readable
 *   node tools/measure_north_of_box.mjs --gate       assert against the reading
 *   node tools/measure_north_of_box.mjs --write      rewrite the reading
 *   node tools/measure_north_of_box.mjs --epoch <id> --scene <id>
 *
 * `--gate` holds the committed reading at `data/terrain/north_of_box_reading.json`
 * against a re-derivation, so the numbers cannot rot silently while the box or
 * the street layer moves underneath them: extend the ground north and the gate
 * fails until the reading is rewritten, which is exactly the moment somebody
 * should be looking at it. It asserts AGREEMENT, not that the gap is small —
 * there is no setting of this repo today that makes it small, and a gate that
 * demanded one would only ever be red.
 */

import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const READING = 'data/terrain/north_of_box_reading.json';

/** `renderers/web/js/terrain.js` § Heightfield.fallbackY. */
const FALLBACK_Y = 0;
/** `renderers/web/js/walker.js` § WALK.stepUp — the plank-walk rule. */
const STEP_UP_M = 0.35;
/** How finely a centreline is walked. Half the terrain cell (2.5 m), so a
 *  crossing is located to better than the grid that decides it. */
const WALK_STEP_M = 1.0;
/** Metres, on lengths of order 10^3. Re-derivation is deterministic; this is
 *  slack for float formatting only. */
const LENGTH_TOL_M = 0.05;

// --- the renderer's own sampler ------------------------------------------- //

/**
 * A heightfield read with `terrain.js`'s semantics, which are NOT
 * `measure_terrain_fit.mjs`'s: that one CLAMPS at the edge because it is
 * scoring a mesh built inside the box, and clamping here would report the
 * bank's own height out on the prairie and hide the whole artefact.
 */
async function renderersHeightfield(epochDir) {
  const meta = JSON.parse(await readFile(path.join(epochDir, 'heightfield.json'), 'utf8'));
  const raw = await readFile(path.join(epochDir, meta.bin ?? 'heightfield.bin'));
  const arr = meta.encoding === 'float32'
    ? new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4)
    : new Int16Array(raw.buffer, raw.byteOffset, raw.byteLength / 2);
  const { cols, rows, cell_m: cell, origin_e: oe, origin_n: on } = meta;
  const scale = meta.scale ?? 0.01;
  const offset = meta.offset ?? 0;
  const at = (i, j) => arr[j * cols + i] * scale + offset;
  const contains = (e, n) => {
    const gx = (e - oe) / cell;
    const gy = (n - on) / cell;
    return gx >= 0 && gy >= 0 && gx <= cols - 1 && gy <= rows - 1;
  };
  return {
    meta,
    contains,
    /** terrain.js Heightfield.sample(): bilinear inside, the constant outside. */
    sample(e, n) {
      if (!contains(e, n)) return FALLBACK_Y;
      const gx = (e - oe) / cell;
      const gy = (n - on) / cell;
      const i = Math.min(Math.floor(gx), cols - 2);
      const j = Math.min(Math.floor(gy), rows - 2);
      const fx = gx - i;
      const fy = gy - j;
      const south = at(i, j) * (1 - fx) + at(i + 1, j) * fx;
      const north = at(i, j + 1) * (1 - fx) + at(i + 1, j + 1) * fx;
      return south * (1 - fy) + north * fy;
    },
  };
}

// --- walking a street ------------------------------------------------------ //

const hyp = (dx, dy) => Math.sqrt(dx * dx + dy * dy);

/** The three lines a street draws: its centre and the two edges of the track
 *  `streets.js` builds at `track_width_m`. Offsets are per segment, which is
 *  what the ribbon does at anything but a mitre. */
function* lines(street) {
  const path_ = street.path_local_enu_m ?? [];
  const half = (street.track_width_m ?? street.corridor_width_m ?? 0) / 2;
  for (const [label, off] of [['centre', 0], ['west_edge', -half], ['east_edge', half]]) {
    if (off === 0 && label !== 'centre') continue;
    const pts = [];
    for (let i = 0; i < path_.length; i++) {
      const a = path_[Math.max(0, i - 1)];
      const b = path_[Math.min(path_.length - 1, i + 1)];
      const d = hyp(b[0] - a[0], b[1] - a[1]) || 1;
      // Left normal of the local tangent: (-dy, dx)/|d|.
      pts.push([path_[i][0] + off * (-(b[1] - a[1]) / d), path_[i][1] + off * ((b[0] - a[0]) / d)]);
    }
    yield [label, pts];
  }
}

/**
 * Walk one polyline, returning the metres on and off the grid and every
 * crossing between the two, located by bisection on the containment test.
 */
function walkLine(pts, hf) {
  let on = 0;
  let off = 0;
  const crossings = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const [e0, n0] = pts[i];
    const [e1, n1] = pts[i + 1];
    const len = hyp(e1 - e0, n1 - n0);
    if (len === 0) continue;
    const steps = Math.max(1, Math.ceil(len / WALK_STEP_M));
    const at_ = (t) => [e0 + (e1 - e0) * t, n0 + (n1 - n0) * t];
    let prevIn = hf.contains(e0, n0);
    for (let s = 1; s <= steps; s++) {
      const t = s / steps;
      const [e, n] = at_(t);
      const nowIn = hf.contains(e, n);
      const seg = len / steps;
      if (nowIn && prevIn) on += seg;
      else if (!nowIn && !prevIn) off += seg;
      else {
        // Split the step at the boundary, found to a millimetre.
        let lo = (s - 1) / steps;
        let hi = t;
        for (let k = 0; k < 40; k++) {
          const mid = (lo + hi) / 2;
          const [me, mn] = at_(mid);
          if (hf.contains(me, mn) === prevIn) lo = mid; else hi = mid;
        }
        const cut = (lo + hi) / 2;
        const inside = at_(prevIn ? lo : hi);
        on += seg * (prevIn ? (cut - (s - 1) / steps) : (t - cut)) * steps;
        off += seg * (prevIn ? (t - cut) : (cut - (s - 1) / steps)) * steps;
        const [ce, cn] = at_(cut);
        const insideY = hf.sample(inside[0], inside[1]);
        crossings.push({
          leaving: prevIn,
          e: +ce.toFixed(2),
          n: +cn.toFixed(2),
          ground_inside_m: +insideY.toFixed(3),
          drawn_outside_m: FALLBACK_Y,
          step_m: +(insideY - FALLBACK_Y).toFixed(3),
          return_refused: insideY - FALLBACK_Y > STEP_UP_M,
        });
      }
      prevIn = nowIn;
    }
  }
  return { on_m: on, off_m: off, crossings };
}

// --- the measurement ------------------------------------------------------- //

/** `streets.js` § createStreets. A record that fails this filter compiles to no
 *  geometry at all, so it cannot be draped on anything. Kept verbatim so the two
 *  files can be diffed by eye when the renderer's rule changes. */
const isDrawn = (r) => Array.isArray(r.path_local_enu_m)
  && r.path_local_enu_m.length >= 2
  && r.opened !== false && (r.track_width_m ?? 6) > 0;

/** Which wall of the box a point is outside, in the box's own words. A corner
 *  exit names both. */
function outsideEdges(e, n, box) {
  const out = [];
  if (n > box.n[1]) out.push('n_max');
  if (n < box.n[0]) out.push('n_min');
  if (e > box.e[1]) out.push('e_max');
  if (e < box.e[0]) out.push('e_min');
  return out;
}

/**
 * The box edge as a scarp. Walked at the terrain cell along all four walls: the
 * ground the field reports just INSIDE, against the constant just outside.
 * `stepUp` decides which of three things each metre of perimeter is.
 */
function perimeter(hf) {
  const box = hf.meta.box_local_enu_m;
  const cell = hf.meta.cell_m;
  const inset = cell / 100;           // inside the wall, off the containment knife-edge
  const walls = [];
  const push = (id, from, to, fixed, axis) => {
    const pts = [];
    const steps = Math.max(1, Math.round(Math.abs(to - from) / cell));
    for (let i = 0; i <= steps; i++) {
      const v = from + ((to - from) * i) / steps;
      pts.push(axis === 'e' ? [v, fixed] : [fixed, v]);
    }
    walls.push({ id, pts, seg: Math.abs(to - from) / steps });
  };
  push('n_max', box.e[0], box.e[1], box.n[1] - inset, 'e');
  push('n_min', box.e[0], box.e[1], box.n[0] + inset, 'e');
  push('e_max', box.n[0], box.n[1], box.e[1] - inset, 'n');
  push('e_min', box.n[0], box.n[1], box.e[0] + inset, 'n');

  const out = {};
  let total = 0;
  let oneWay = 0;
  for (const w of walls) {
    let stepOut = 0;      // ground inside stands above the constant by > stepUp
    let walkable = 0;     // within the step rule both ways
    let barred = 0;       // ground inside is BELOW the constant: the way out is the climb
    let maxStep = -Infinity;
    let minStep = Infinity;
    let sum = 0;
    // MIDPOINTS, one per segment. Sampling the vertices instead counts n+1
    // samples into n segments' worth of length and reports 100.3 % of a wall.
    for (let i = 0; i < w.pts.length - 1; i++) {
      const e = (w.pts[i][0] + w.pts[i + 1][0]) / 2;
      const n = (w.pts[i][1] + w.pts[i + 1][1]) / 2;
      const step = hf.sample(e, n) - FALLBACK_Y;
      maxStep = Math.max(maxStep, step);
      minStep = Math.min(minStep, step);
      sum += step;
      if (step > STEP_UP_M) stepOut += w.seg;
      else if (step < -STEP_UP_M) barred += w.seg;
      else walkable += w.seg;
    }
    const len = w.seg * (w.pts.length - 1);
    total += len;
    oneWay += stepOut;
    out[w.id] = {
      length_m: +len.toFixed(2),
      one_way_m: +stepOut.toFixed(2),
      one_way_fraction: +(stepOut / len).toFixed(4),
      walkable_both_ways_m: +walkable.toFixed(2),
      refuses_the_way_out_m: +barred.toFixed(2),
      step_down_max_m: +maxStep.toFixed(3),
      step_down_min_m: +minStep.toFixed(3),
      step_down_mean_m: +(sum / (w.pts.length - 1)).toFixed(3),
    };
  }
  return {
    _doc: 'Each wall of the box, walked at the terrain cell. `one_way_m` is perimeter '
      + 'where the modelled ground stands more than the walker\'s step-up above the '
      + 'constant outside it: a visitor may walk out and may not walk back.',
    walls: out,
    total_m: +total.toFixed(2),
    one_way_m: +oneWay.toFixed(2),
    one_way_fraction: +(oneWay / total).toFixed(4),
  };
}

export async function measure({ root = ROOT, epoch = 'e1834_harbor_cut', scene = '1835' } = {}) {
  const hf = await renderersHeightfield(path.join(root, 'data/terrain/epochs', epoch));
  const box = hf.meta.box_local_enu_m;
  const sceneFile = JSON.parse(await readFile(path.join(root, `data/scenes/${scene}.json`), 'utf8'));
  const streets = JSON.parse(await readFile(path.join(root, `data/streets/${scene}.json`), 'utf8')).streets;

  const pops = { drawn: [], platted_only: [] };
  const totals = { drawn: { on: 0, off: 0 }, platted_only: { on: 0, off: 0 } };
  for (const st of streets) {
    const pop = isDrawn(st) ? 'drawn' : 'platted_only';
    // A STREET'S LENGTH IS ITS CENTRELINE. The track edges are walked too, but
    // their metres are reported beside the centreline's and never added to it:
    // summing three parallel lines turns 630 m of Wolcott Street into 1,889.
    const byLine = {};
    const edges = new Set();
    const crossings = [];
    for (const [label, pts] of lines(st)) {
      const r = walkLine(pts, hf);
      byLine[label] = { on_grid_m: +r.on_m.toFixed(2), off_grid_m: +r.off_m.toFixed(2) };
      if (label === 'centre') for (const c of r.crossings) crossings.push(c);
    }
    const on = byLine.centre.on_grid_m;
    const off = byLine.centre.off_grid_m;
    const worstEdge = Math.max(byLine.west_edge?.off_grid_m ?? 0, byLine.east_edge?.off_grid_m ?? 0);
    for (const [e, n] of st.path_local_enu_m) for (const w of outsideEdges(e, n, box)) edges.add(w);
    totals[pop].on += on;
    totals[pop].off += off;
    // Sub-cell slivers are a track edge grazing the wall, not a street off the
    // ground; below the terrain cell there is nothing to report.
    if (Math.max(off, worstEdge) < hf.meta.cell_m) continue;
    pops[pop].push({
      id: st.id,
      name_1835: st.name_1835 ?? null,
      on_grid_m: +on.toFixed(2),
      off_grid_m: +off.toFixed(2),
      off_grid_fraction: +(off / (on + off)).toFixed(4),
      track_edge_off_grid_m: +worstEdge.toFixed(2),
      leaves_through: [...edges].sort(),
      north_end_n_m: Math.max(...st.path_local_enu_m.map((v) => v[1])),
      crossings: crossings.sort((a, b) => b.step_m - a.step_m).slice(0, 4),
    });
  }
  for (const k of Object.keys(pops)) pops[k].sort((a, b) => b.off_grid_m - a.off_grid_m);

  // The viewpoint T-1062 could not finish, standing where it stands.
  const vp = (sceneFile.viewpoints ?? sceneFile.anchors ?? []).find((v) => v.id === 'kinzie_block');
  const viewpoint = vp ? {
    id: vp.id,
    label: vp.label ?? null,
    local_e: vp.local_e,
    local_n: vp.local_n,
    yaw_deg: vp.yaw_deg ?? null,
    on_modelled_ground: hf.contains(vp.local_e, vp.local_n),
    ground_m: +hf.sample(vp.local_e, vp.local_n).toFixed(3),
    metres_to_n_max: +(box.n[1] - vp.local_n).toFixed(2),
    note: 'It stands on modelled ground and looks north at the wall.',
  } : null;

  return {
    _doc: 'GENERATED by tools/measure_north_of_box.mjs — do not hand-edit. '
      + 'What the renderer does with committed streets that stand off the modelled ground, '
      + 'and what the edge of the modelled ground is to a walker.',
    ticket: 'T-1067',
    epoch,
    scene,
    box_local_enu_m: box,
    fallback_y_m: FALLBACK_Y,
    step_up_m: STEP_UP_M,
    perimeter: perimeter(hf),
    viewpoint,
    totals: {
      streets_in_layer: streets.length,
      drawn: {
        streets: streets.filter(isDrawn).length,
        partly_off_grid: pops.drawn.length,
        on_grid_m: +totals.drawn.on.toFixed(2),
        off_grid_m: +totals.drawn.off.toFixed(2),
        off_grid_fraction: +(totals.drawn.off / (totals.drawn.on + totals.drawn.off)).toFixed(4),
      },
      platted_only: {
        streets: streets.length - streets.filter(isDrawn).length,
        partly_off_grid: pops.platted_only.length,
        on_grid_m: +totals.platted_only.on.toFixed(2),
        off_grid_m: +totals.platted_only.off.toFixed(2),
        off_grid_fraction: +(totals.platted_only.off
          / (totals.platted_only.on + totals.platted_only.off)).toFixed(4),
      },
    },
    drawn: pops.drawn,
    platted_only: pops.platted_only,
  };
}

// --- reporting and gating -------------------------------------------------- //

function table(r) {
  const out = [];
  const b = r.box_local_enu_m;
  out.push(`box  e [${b.e.join(', ')}]  n [${b.n.join(', ')}]   fallback y = ${r.fallback_y_m}`);
  out.push('');
  out.push('DRAWN STREET OFF THE MODELLED GROUND — a ribbon draped on the constant');
  if (!r.drawn.length) out.push('  (none)');
  for (const s of r.drawn) {
    out.push(`  ${s.id.padEnd(24)}${String(s.off_grid_m).padStart(9)} m`
      + `${(`${(s.off_grid_fraction * 100).toFixed(1)} %`).padStart(9)}`
      + `   out through ${s.leaves_through.join(', ') || '—'}`);
  }
  out.push('');
  out.push('PLATTED, UNOPENED — the record stands off the ground; nothing is drawn');
  out.push(`  ${r.platted_only.length} of ${r.totals.platted_only.streets} such records, `
    + `${r.totals.platted_only.off_grid_m.toFixed(0)} m of line`);
  out.push('');
  out.push('THE EDGE OF THE MODELLED GROUND, as a walker meets it');
  out.push('  wall     length m   one-way m    of it   deepest step');
  for (const [id, w] of Object.entries(r.perimeter.walls)) {
    out.push(`  ${id.padEnd(9)}${String(w.length_m).padStart(8)}${String(w.one_way_m).padStart(12)}`
      + `${(`${(w.one_way_fraction * 100).toFixed(1)} %`).padStart(9)}`
      + `${String(w.step_down_max_m).padStart(15)}`);
  }
  out.push('');
  if (r.viewpoint) {
    out.push(`viewpoint ${r.viewpoint.id}: on modelled ground = ${r.viewpoint.on_modelled_ground}, `
      + `ground ${r.viewpoint.ground_m} m, ${r.viewpoint.metres_to_n_max} m short of n_max.`);
  }
  out.push(`${r.perimeter.one_way_m.toFixed(0)} m of the box's ${r.perimeter.total_m.toFixed(0)} m `
    + `perimeter (${(r.perimeter.one_way_fraction * 100).toFixed(1)} %) is a one-way door: the `
    + `ground inside stands more than ${r.step_up_m} m above the constant outside.`);
  return out.join('\n');
}

/** Compare a re-derivation with the committed reading. Lengths to LENGTH_TOL_M,
 *  counts exactly, and the street sets by id. */
function diff(fresh, held) {
  const bad = [];
  const near = (a, b) => typeof b === 'number' && Math.abs(a - b) <= LENGTH_TOL_M;
  for (const pop of ['drawn', 'platted_only']) {
    for (const k of ['on_grid_m', 'off_grid_m']) {
      if (!near(fresh.totals[pop][k], held.totals?.[pop]?.[k])) {
        bad.push(`totals.${pop}.${k}: ${held.totals?.[pop]?.[k]} held, ${fresh.totals[pop][k]} re-derived`);
      }
    }
    for (const k of ['streets', 'partly_off_grid']) {
      if (fresh.totals[pop][k] !== held.totals?.[pop]?.[k]) {
        bad.push(`totals.${pop}.${k}: ${held.totals?.[pop]?.[k]} held, ${fresh.totals[pop][k]} re-derived`);
      }
    }
    const f = new Set(fresh[pop].map((s) => s.id));
    const h = new Set((held[pop] ?? []).map((s) => s.id));
    for (const id of f) if (!h.has(id)) bad.push(`${pop}: ${id} is off the grid now and is not in the reading`);
    for (const id of h) if (!f.has(id)) bad.push(`${pop}: ${id} is in the reading and is now on the grid`);
    for (const s of fresh[pop]) {
      const held_ = (held[pop] ?? []).find((x) => x.id === s.id);
      if (held_ && !near(s.off_grid_m, held_.off_grid_m)) {
        bad.push(`${pop}: ${s.id}.off_grid_m: ${held_.off_grid_m} held, ${s.off_grid_m} re-derived`);
      }
    }
  }
  if (!near(fresh.perimeter.one_way_m, held.perimeter?.one_way_m)) {
    bad.push(`perimeter.one_way_m: ${held.perimeter?.one_way_m} held, ${fresh.perimeter.one_way_m} re-derived`);
  }
  for (const [id, w] of Object.entries(fresh.perimeter.walls)) {
    const held_ = held.perimeter?.walls?.[id];
    if (!near(w.one_way_m, held_?.one_way_m)) {
      bad.push(`perimeter.${id}.one_way_m: ${held_?.one_way_m} held, ${w.one_way_m} re-derived`);
    }
  }
  if (fresh.viewpoint?.on_modelled_ground !== held.viewpoint?.on_modelled_ground) {
    bad.push('viewpoint.on_modelled_ground moved');
  }
  return bad;
}

async function main(argv) {
  const arg = (k, d) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);
  const epoch = arg('--epoch', 'e1834_harbor_cut');
  const scene = arg('--scene', '1835');
  const fresh = await measure({ epoch, scene });

  if (argv.includes('--write')) {
    await writeFile(path.join(ROOT, READING), `${JSON.stringify(fresh, null, 1)}\n`);
    console.log(`wrote ${READING}`);
    return 0;
  }
  if (argv.includes('--json')) {
    console.log(JSON.stringify(fresh, null, 1));
    return 0;
  }
  if (argv.includes('--gate')) {
    let held;
    try {
      held = JSON.parse(await readFile(path.join(ROOT, READING), 'utf8'));
    } catch (err) {
      console.error(`${READING} is unreadable (${err.message}) — `
        + 'this reading is the committed answer to T-1067 and losing it loses the answer.');
      return 1;
    }
    const bad = diff(fresh, held);
    if (bad.length) {
      console.error(`${READING} no longer matches what tools/measure_north_of_box.mjs re-derives:`);
      for (const b of bad) console.error(`  - ${b}`);
      console.error('Re-run with --write and say in the PR what moved and why.');
      return 1;
    }
    console.log(`north-of-box reading holds: ${held.totals.drawn.off_grid_m.toFixed(0)} m of drawn `
      + `street off the modelled ground, ${held.perimeter.one_way_m.toFixed(0)} m of one-way edge`);
    return 0;
  }
  console.log(table(fresh));
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main(process.argv.slice(2)).then((c) => process.exit(c));
}
