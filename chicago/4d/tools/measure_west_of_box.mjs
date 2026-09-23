/**
 * measure_west_of_box.mjs — the west wall of the modelled ground: what stands
 * off it today, and what the wall that replaces it has to clear.
 *
 * T-1415, of T-1193. Its northern sibling `measure_north_of_box.mjs` answers
 * "what does the renderer DO with the committed town outside the box". This one
 * answers the question the west side asks instead, which is a decision and not
 * a consequence: `data/reconstruction/1835_phase2_west_wolf_point_approaches.json`
 * holds 35 of its 55 placements for want of ground, its own
 * `terrain_and_hydrology_gate` names E -700 m as the box it needs, and nothing
 * in this repo had ever derived that number or priced the field that carries it.
 *
 * A ROUND FIGURE IS NOT A DERIVATION. The other three walls of this box each
 * stand on three tests, written out in `terrain_spec.json` § box_derivation:
 *
 *   1. CONTAINS — it clears the westernmost thing the box must hold, and the
 *      clearance is stated in metres. Here that thing is not a placement's
 *      CENTRE but the western edge of its footprint: a roof is contained when
 *      all of it is, and `generate_west_infill.py`'s own validator tests the
 *      whole footprint for exactly that reason.
 *   2. ERROR BAR — it clears that thing's positional uncertainty as well as the
 *      thing. The West Division centres are dealt against a street grid fitted
 *      to the Wright 1834 sheet, so the bar is the georeference's own:
 *      `data/datum.json` records RMS 17.5 m and a MAXIMUM of 32.7 m, and a
 *      single point is owed the maximum rather than the mean.
 *   3. LATTICE — it lands on the existing 2.5 m sampling lattice, so no sample
 *      the field already carries moves. Both the southern extension (T-0464)
 *      and the northern one (T-1123) were careful to keep that property and it
 *      is cheap to keep.
 *
 * Run those three and the wall comes out at E -705 m, not at the recipe's
 * round -700: -700 clears the westernmost held footprint by 28.46 m, which
 * clears the sheet's RMS and stands 4.24 m SHORT of its worst residual. Five
 * metres and two columns of field buy that back. The tool derives it rather
 * than asserting it, so the number moves when a placement moves.
 *
 * IT MOVES NO GROUND. `grid` in `terrain_spec.json` is a mesh input and this
 * ticket does not touch it; `box_derivation` is prose (generators/
 * terrain_inputs.py § PROSE_KEYS, scheme v5) and is where the reasoning goes.
 * The heightfield, the collision surface, the water mask and the bake are
 * T-1416's, and the reading below is what that run has to close.
 *
 *   node tools/measure_west_of_box.mjs             table + verdict
 *   node tools/measure_west_of_box.mjs --json      machine-readable
 *   node tools/measure_west_of_box.mjs --gate      assert against the reading
 *   node tools/measure_west_of_box.mjs --write     rewrite the reading
 *   node tools/measure_west_of_box.mjs --self-test the assertions, fired
 *
 * `--gate` holds `data/terrain/west_of_box_reading.json` against a
 * re-derivation, so the wall's clearances cannot rot while the recipe, the
 * street layer or the box moves underneath them. It asserts AGREEMENT, not that
 * the wall is where anybody wanted it.
 */

import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const READING = 'data/terrain/west_of_box_reading.json';
const RECIPE = 'data/reconstruction/1835_phase2_west_wolf_point_approaches.json';

/** `renderers/web/js/terrain.js` § Heightfield.fallbackY. */
const FALLBACK_Y = 0;
/** `renderers/web/js/walker.js` § WALK.stepUp — the plank-walk rule. */
const STEP_UP_M = 0.35;
/** Metres. Re-derivation is deterministic; this is slack for float formatting. */
const TOL_M = 0.05;
const FT_TO_M = 0.3048;

// --- the renderer's own sampler, with terrain.js's semantics --------------- //

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

// --- the three tests ------------------------------------------------------- //

/**
 * The western edge of one placement's footprint, in local metres. Rotation is
 * about the centre, so the half-extent on E is the rotated bounding box's:
 * |w cos| + |d sin|, halved. Taking the centre alone would report a roof
 * contained while a corner of it stood on the constant.
 */
export function footprintWestEdge(p) {
  const [e] = p.center_local_enu_m.map(Number);
  const [w, d] = p.footprint_ft.map((v) => Number(v) * FT_TO_M);
  const th = (Number(p.rotation_deg) * Math.PI) / 180;
  return e - (Math.abs(w * Math.cos(th)) + Math.abs(d * Math.sin(th))) / 2;
}

/**
 * The wall itself: the westernmost held footprint edge, less the georeference's
 * worst residual, rounded WEST onto the sampling lattice. Rounding west and not
 * to-nearest is the whole point of a clearance — a wall rounded east could land
 * inside the bar it was derived to clear.
 */
export function deriveWall({ westmostEdge, maxResidualM, cell, currentEMin }) {
  const wanted = westmostEdge - maxResidualM;
  const columns = Math.ceil((currentEMin - wanted) / cell);
  return +(currentEMin - columns * cell).toFixed(6);
}

// --- walking the wall ------------------------------------------------------ //

/** The e_min wall, walked at the terrain cell: ground just inside against the
 *  constant just outside. `stepUp` decides what each metre of it is. */
function westWallScarp(hf) {
  const box = hf.meta.box_local_enu_m;
  const cell = hf.meta.cell_m;
  const e = box.e[0] + cell / 100;          // off the containment knife-edge
  const steps = Math.max(1, Math.round((box.n[1] - box.n[0]) / cell));
  const seg = (box.n[1] - box.n[0]) / steps;
  let oneWay = 0;
  let walkable = 0;
  let barred = 0;
  let maxStep = -Infinity;
  let minStep = Infinity;
  let sum = 0;
  // MIDPOINTS, one per segment: sampling the vertices counts n+1 samples into
  // n segments and reports more than 100 % of a wall.
  for (let i = 0; i < steps; i++) {
    const n = box.n[0] + seg * (i + 0.5);
    const step = hf.sample(e, n) - FALLBACK_Y;
    maxStep = Math.max(maxStep, step);
    minStep = Math.min(minStep, step);
    sum += step;
    if (step > STEP_UP_M) oneWay += seg;
    else if (step < -STEP_UP_M) barred += seg;
    else walkable += seg;
  }
  const len = seg * steps;
  return {
    _doc: 'The e_min wall walked at the terrain cell. `one_way_m` is perimeter where '
      + "the modelled ground stands more than the walker's step-up above the constant "
      + 'outside it: a visitor may walk out and may not walk back.',
    length_m: +len.toFixed(2),
    one_way_m: +oneWay.toFixed(2),
    one_way_fraction: +(oneWay / len).toFixed(4),
    walkable_both_ways_m: +walkable.toFixed(2),
    refuses_the_way_out_m: +barred.toFixed(2),
    step_down_max_m: +maxStep.toFixed(3),
    step_down_min_m: +minStep.toFixed(3),
    step_down_mean_m: +(sum / steps).toFixed(3),
  };
}

// --- the street layer ------------------------------------------------------ //

/** `streets.js` § createStreets. A record that fails this filter compiles to no
 *  geometry at all, so it cannot be draped on anything. Kept verbatim. */
const isDrawn = (r) => Array.isArray(r.path_local_enu_m)
  && r.path_local_enu_m.length >= 2
  && r.opened !== false && (r.track_width_m ?? 6) > 0;

// --- the traced water ------------------------------------------------------ //

/** Every vertex of a GeoJSON geometry, at any nesting depth. */
function* coords(geom) {
  const walk = function* (c) {
    if (typeof c[0] === 'number') yield c;
    else for (const x of c) yield* walk(x);
  };
  yield* walk(geom.coordinates);
}

export async function measure({ root = ROOT, epoch = 'e1834_harbor_cut', scene = '1835',
  recipe: recipeOverride = null, streets: streetsOverride = null } = {}) {
  const epochDir = path.join(root, 'data/terrain/epochs', epoch);
  const hf = await renderersHeightfield(epochDir);
  const box = hf.meta.box_local_enu_m;
  const cell = hf.meta.cell_m;
  const datum = JSON.parse(await readFile(path.join(root, 'data/datum.json'), 'utf8'));
  const recipe = recipeOverride
    ?? JSON.parse(await readFile(path.join(root, RECIPE), 'utf8'));
  const streets = streetsOverride
    ?? JSON.parse(await readFile(path.join(root, `data/streets/${scene}.json`), 'utf8')).streets;

  // --- 1. the held slots, which are what the wall is for -------------------
  // T-1444 retired the instantiation block, so the recipe now carries its text under
  // `instantiation_block_retired.was`. This reading is a DERIVATION OF THE WALL and
  // the wall was derived to hold those 35 slots: read the retired text rather than
  // re-deriving the wall from a parcel that no longer holds anything, which would
  // silently change what T-1415 measured.
  const gate = recipe.terrain_and_hydrology_gate;
  const blockText = gate.instantiation_block ?? gate.instantiation_block_retired?.was;
  if (!blockText) {
    throw new Error('the West recipe carries neither an instantiation block nor the '
      + 'retired text of one; the west wall cannot state what it was derived to hold');
  }
  const limit = Number(blockText.match(/centre E < (-?\d+(?:\.\d+)?) m/)[1]);
  const placements = recipe.placements.map((p) => ({
    id: p.id,
    family: p.family,
    centre_e_m: +Number(p.center_local_enu_m[0]).toFixed(2),
    centre_n_m: +Number(p.center_local_enu_m[1]).toFixed(2),
    west_edge_e_m: +footprintWestEdge(p).toFixed(2),
    held: Number(p.center_local_enu_m[0]) < limit,
  }));
  const held = placements.filter((p) => p.held).sort((a, b) => a.west_edge_e_m - b.west_edge_e_m);
  const westmost = held[0];

  // --- 2. the wall, derived ------------------------------------------------
  const rms = Number(datum.derivation.residual_m
    ?? (datum.derivation.method.match(/RMS ([\d.]+) m/) ?? [])[1]);
  const worst = Number((datum.derivation.method.match(/max ([\d.]+) m/) ?? [])[1]);
  const derived = deriveWall({
    westmostEdge: westmost.west_edge_e_m, maxResidualM: worst, cell, currentEMin: box.e[0],
  });
  const asked = Number(recipe.terrain_and_hydrology_gate.required_west_box_local_enu_m.e[0]);
  const columns = Math.round((box.e[0] - derived) / cell);
  const colsNow = hf.meta.cols;
  const colsThen = colsNow + columns;
  const wall = {
    _doc: 'The three tests every wall of this box stands on, run against the west one. '
      + '`derived_e_m` is computed here and not adopted: move a placement and it moves.',
    current_e_m: box.e[0],
    asked_for_e_m: asked,
    derived_e_m: derived,
    contains: {
      what: `${westmost.id} — the westernmost held placement, at its footprint's west edge`,
      e_m: westmost.west_edge_e_m,
      centre_e_m: westmost.centre_e_m,
      clearance_m: +(westmost.west_edge_e_m - derived).toFixed(2),
      clearance_from_asked_m: +(westmost.west_edge_e_m - asked).toFixed(2),
    },
    error_bar: {
      what: 'the Wright 1834 georeference — data/datum.json § derivation',
      rms_m: rms,
      worst_residual_m: worst,
      clears_rms_by_m: +(westmost.west_edge_e_m - derived - rms).toFixed(2),
      clears_worst_by_m: +(westmost.west_edge_e_m - derived - worst).toFixed(2),
      asked_clears_worst_by_m: +(westmost.west_edge_e_m - asked - worst).toFixed(2),
      asked_clears_worst: westmost.west_edge_e_m - asked >= worst,
      why_the_worst_and_not_the_mean: 'A wall clears ONE point — the westernmost roof — and '
        + 'the mean residual is a property of eight control points, not of that one.',
    },
    lattice: {
      cell_m: cell,
      columns_added: columns,
      lands_on_lattice: Math.abs((box.e[0] - derived) / cell - columns) < 1e-9,
      no_committed_sample_moves: true,
    },
  };

  // --- 3. what the new field costs -----------------------------------------
  const bytesPerSample = hf.meta.encoding === 'float32' ? 4 : 2;
  const field_cost = {
    _doc: 'Stated because T-1067 filed the northern wall\'s cost as a separate piece of work, '
      + 'and the same figure decides whether T-1416 is one run.',
    rows: hf.meta.rows,
    cols_now: colsNow,
    cols_then: colsThen,
    samples_now: colsNow * hf.meta.rows,
    samples_then: colsThen * hf.meta.rows,
    growth_fraction: +((colsThen - colsNow) / colsNow).toFixed(4),
    heightfield_bin_bytes_now: colsNow * hf.meta.rows * bytesPerSample,
    heightfield_bin_bytes_then: colsThen * hf.meta.rows * bytesPerSample,
  };

  // --- 4. the street layer against both walls ------------------------------
  const clipped = [];
  const offDerived = { drawn: [], platted_only: [] };
  const broughtIn = [];
  for (const st of streets) {
    const pts = st.path_local_enu_m ?? [];
    if (pts.length < 2) continue;
    const minE = Math.min(...pts.map((v) => v[0]));
    const pop = isDrawn(st) ? 'drawn' : 'platted_only';
    // A record whose westernmost vertex sits within half a cell of the wall was
    // CUT by the wall — its own note usually says so — which is a different
    // thing from a record that crosses it.
    if (Math.abs(minE - box.e[0]) <= cell / 2) {
      clipped.push({ id: st.id, name_1835: st.name_1835 ?? null, population: pop,
        west_end_e_m: +minE.toFixed(2) });
    }
    if (minE < derived - TOL_M) {
      offDerived[pop].push({ id: st.id, name_1835: st.name_1835 ?? null,
        west_end_e_m: +minE.toFixed(2),
        metres_past_the_derived_wall: +(derived - minE).toFixed(2) });
    } else if (minE < box.e[0] - TOL_M) {
      broughtIn.push({ id: st.id, population: pop, west_end_e_m: +minE.toFixed(2) });
    }
  }
  const bye = (a, b) => a.west_end_e_m - b.west_end_e_m;
  clipped.sort((a, b) => a.id.localeCompare(b.id));
  broughtIn.sort(bye);
  for (const k of Object.keys(offDerived)) offDerived[k].sort(bye);

  // --- 5. the traced water, and the terminus T-1416 has to answer ----------
  const oe = datum.origin_utm_e;
  const on = datum.origin_utm_n;
  const water = [];
  for (const file of ['river.geojson', 'branches.geojson', 'shoreline.geojson',
    'hydrology.geojson']) {
    const fc = JSON.parse(await readFile(path.join(epochDir, file), 'utf8'));
    for (const ft of fc.features) {
      let west = null;
      let north = null;
      for (const c of coords(ft.geometry)) {
        const e = c[0] - oe;
        const n = c[1] - on;
        if (west === null || e < west[0]) west = [e, n];
        if (north === null || n > north[1]) north = [e, n];
      }
      water.push({
        file,
        id: ft.properties?.id ?? ft.properties?.name ?? null,
        westmost_e_m: +west[0].toFixed(2),
        westmost_at_n_m: +west[1].toFixed(2),
        inside_the_derived_wall: west[0] >= derived,
        north_end_e_m: +north[0].toFixed(2),
        north_end_n_m: +north[1].toFixed(2),
        // A traced line that ENDS inside the box is a river that stops in the
        // middle of the modelled ground. Today the e_min wall cuts the North
        // Branch off before its trace runs out, so its terminus is off-box and
        // nobody can see it; the derived wall brings it in. The test is exactly
        // that — outside the present box, inside the derived one — and not "ends
        // inside the box", which every feature in the epoch satisfies and which
        // would report fourteen findings where there are three.
        terminus_brought_inside_by_the_move:
          !hf.contains(north[0], north[1]) && north[0] >= derived
          && north[0] <= box.e[1] && north[1] >= box.n[0] && north[1] <= box.n[1],
      });
    }
  }
  water.sort((a, b) => a.westmost_e_m - b.westmost_e_m);
  const termini = water.filter((w) => w.terminus_brought_inside_by_the_move);

  return {
    _doc: 'GENERATED by tools/measure_west_of_box.mjs — do not hand-edit. The west wall of '
      + 'the modelled ground: the three tests the replacement wall stands on, what it costs, '
      + 'and what still stands off it. This reading moves no ground; T-1416 does.',
    ticket: 'T-1415',
    parent: 'T-1193',
    epoch,
    scene,
    box_local_enu_m: box,
    fallback_y_m: FALLBACK_Y,
    step_up_m: STEP_UP_M,
    wall,
    field_cost,
    held_slots: {
      _doc: 'generate_west_infill.py HELD a placement whose CENTRE was west of its '
        + 'instantiation block, and the wall is derived from the westernmost FOOTPRINT '
        + 'edge of those, because a roof is contained when all of it is. T-1444 released '
        + 'all 35 onto the ground T-1416 built and retired the block; the figures below '
        + 'are kept as the derivation of the wall, which is what they always were, and '
        + 'no longer describe anything the generator withholds.',
      instantiation_block_e_m: limit,
      placements: placements.length,
      held: held.length,
      built: placements.length - held.length,
      westmost: westmost,
      all_inside_the_derived_wall: held.every((p) => p.west_edge_e_m >= derived),
      still_outside_the_asked_wall: held.filter((p) => p.west_edge_e_m < asked).map((p) => p.id),
      by_family: held.reduce((acc, p) => ({ ...acc, [p.family]: (acc[p.family] ?? 0) + 1 }), {}),
    },
    streets: {
      _doc: 'Three populations, never added together: records the present wall CUT, records '
        + 'the move brings onto modelled ground, and records that stand off the derived wall '
        + 'even after the move. The last are platted, unopened lines — `streets.js` compiles '
        + 'no ribbon for a record with track_width_m 0, so they draw nothing.',
      in_layer: streets.length,
      clipped_at_the_present_wall: clipped,
      brought_onto_the_ground_by_the_move: broughtIn,
      still_west_of_the_derived_wall: offDerived,
    },
    traced_water: {
      _doc: 'The whole traced water body has to be inside the box, as e_max requires. It is — '
        + 'and that is what creates T-1416\'s one real problem, recorded here rather than '
        + 'discovered during a bake: the North Branch\'s trace stops at the north line of '
        + 'Wright\'s survey, and today the e_min wall cuts the branch off well before it. '
        + 'Move the wall and the trace runs out INSIDE the modelled ground.',
      features: water,
      termini_brought_inside_by_the_move: termini.map((w) => w.id),
    },
    west_wall_scarp: westWallScarp(hf),
  };
}

// --- reporting and gating -------------------------------------------------- //

function table(r) {
  const w = r.wall;
  const o = [];
  o.push(`box  e [${r.box_local_enu_m.e.join(', ')}]  n [${r.box_local_enu_m.n.join(', ')}]`);
  o.push('');
  o.push('THE WEST WALL, DERIVED');
  o.push(`  present               E ${w.current_e_m}`);
  o.push(`  asked for by the recipe   E ${w.asked_for_e_m}`);
  o.push(`  DERIVED               E ${w.derived_e_m}   (${w.lattice.columns_added} columns)`);
  o.push(`  1 contains   ${w.contains.what}`);
  o.push(`               at E ${w.contains.e_m}, cleared by ${w.contains.clearance_m} m`);
  o.push(`  2 error bar  RMS ${w.error_bar.rms_m} m, worst ${w.error_bar.worst_residual_m} m; `
    + `cleared by ${w.error_bar.clears_worst_by_m} m`);
  o.push(`               the asked-for wall clears the worst residual: `
    + `${w.error_bar.asked_clears_worst} (${w.error_bar.asked_clears_worst_by_m} m)`);
  o.push(`  3 lattice    ${w.lattice.lands_on_lattice ? 'on the 2.5 m lattice' : 'OFF LATTICE'}`);
  o.push('');
  o.push(`FIELD  ${r.field_cost.cols_now} -> ${r.field_cost.cols_then} columns, `
    + `${(r.field_cost.growth_fraction * 100).toFixed(1)} % more samples, `
    + `heightfield.bin ${(r.field_cost.heightfield_bin_bytes_now / 1048576).toFixed(2)} -> `
    + `${(r.field_cost.heightfield_bin_bytes_then / 1048576).toFixed(2)} MB`);
  o.push('');
  o.push(`HELD SLOTS  ${r.held_slots.held} of ${r.held_slots.placements}, westmost `
    + `${r.held_slots.westmost.id} at E ${r.held_slots.westmost.west_edge_e_m}; `
    + `all inside the derived wall: ${r.held_slots.all_inside_the_derived_wall}`);
  o.push('');
  o.push(`STREETS  ${r.streets.clipped_at_the_present_wall.length} cut by the present wall, `
    + `${r.streets.brought_onto_the_ground_by_the_move.length} brought on by the move, `
    + `${r.streets.still_west_of_the_derived_wall.drawn.length} drawn and `
    + `${r.streets.still_west_of_the_derived_wall.platted_only.length} platted-only still off it`);
  o.push('');
  o.push(`TRACED WATER  westmost ${r.traced_water.features[0].id} at `
    + `E ${r.traced_water.features[0].westmost_e_m}; `
    + `${r.traced_water.termini_brought_inside_by_the_move.length} traced terminus/termini would `
    + 'fall INSIDE the new box — T-1416 has to answer that before it bakes');
  for (const id of r.traced_water.termini_brought_inside_by_the_move) o.push(`    - ${id}`);
  o.push('');
  o.push(`THE PRESENT WALL AS A WALKER MEETS IT  ${r.west_wall_scarp.length_m} m, of which `
    + `${r.west_wall_scarp.one_way_m} m `
    + `(${(r.west_wall_scarp.one_way_fraction * 100).toFixed(1)} %) is a one-way door; `
    + `deepest step ${r.west_wall_scarp.step_down_max_m} m`);
  return o.join('\n');
}

const near = (a, b) => typeof b === 'number' && Math.abs(a - b) <= TOL_M;

function diff(fresh, held) {
  const bad = [];
  for (const k of ['current_e_m', 'asked_for_e_m', 'derived_e_m']) {
    if (!near(fresh.wall[k], held.wall?.[k])) {
      bad.push(`wall.${k}: ${held.wall?.[k]} held, ${fresh.wall[k]} re-derived`);
    }
  }
  if (!near(fresh.wall.contains.e_m, held.wall?.contains?.e_m)) {
    bad.push(`wall.contains.e_m: ${held.wall?.contains?.e_m} held, ${fresh.wall.contains.e_m} re-derived`);
  }
  if (fresh.wall.contains.what !== held.wall?.contains?.what) {
    bad.push('wall.contains.what: the westernmost held placement is no longer the same one');
  }
  if (fresh.wall.lattice.columns_added !== held.wall?.lattice?.columns_added) {
    bad.push(`wall.lattice.columns_added: ${held.wall?.lattice?.columns_added} held, `
      + `${fresh.wall.lattice.columns_added} re-derived`);
  }
  for (const k of ['cols_now', 'cols_then', 'samples_then']) {
    if (fresh.field_cost[k] !== held.field_cost?.[k]) {
      bad.push(`field_cost.${k}: ${held.field_cost?.[k]} held, ${fresh.field_cost[k]} re-derived`);
    }
  }
  for (const k of ['held', 'built', 'placements']) {
    if (fresh.held_slots[k] !== held.held_slots?.[k]) {
      bad.push(`held_slots.${k}: ${held.held_slots?.[k]} held, ${fresh.held_slots[k]} re-derived`);
    }
  }
  if (fresh.held_slots.westmost.id !== held.held_slots?.westmost?.id) {
    bad.push('held_slots.westmost.id moved');
  }
  const sets = [
    ['streets.clipped_at_the_present_wall', fresh.streets.clipped_at_the_present_wall,
      held.streets?.clipped_at_the_present_wall],
    ['streets.brought_onto_the_ground_by_the_move', fresh.streets.brought_onto_the_ground_by_the_move,
      held.streets?.brought_onto_the_ground_by_the_move],
    ['streets.still_west_of_the_derived_wall.drawn', fresh.streets.still_west_of_the_derived_wall.drawn,
      held.streets?.still_west_of_the_derived_wall?.drawn],
    ['streets.still_west_of_the_derived_wall.platted_only',
      fresh.streets.still_west_of_the_derived_wall.platted_only,
      held.streets?.still_west_of_the_derived_wall?.platted_only],
  ];
  for (const [label, f, h] of sets) {
    const fs = new Set(f.map((x) => x.id));
    const hs = new Set((h ?? []).map((x) => x.id));
    for (const id of fs) if (!hs.has(id)) bad.push(`${label}: ${id} is there now and not in the reading`);
    for (const id of hs) if (!fs.has(id)) bad.push(`${label}: ${id} is in the reading and is not there now`);
  }
  const ft = new Set(fresh.traced_water.termini_brought_inside_by_the_move);
  const ht = new Set(held.traced_water?.termini_brought_inside_by_the_move ?? []);
  for (const id of ft) if (!ht.has(id)) bad.push(`traced_water: ${id} now ends inside the new box`);
  for (const id of ht) if (!ft.has(id)) bad.push(`traced_water: ${id} no longer ends inside the new box`);
  if (!near(fresh.west_wall_scarp.one_way_m, held.west_wall_scarp?.one_way_m)) {
    bad.push(`west_wall_scarp.one_way_m: ${held.west_wall_scarp?.one_way_m} held, `
      + `${fresh.west_wall_scarp.one_way_m} re-derived`);
  }
  return bad;
}

// --- the self-test --------------------------------------------------------- //

async function selfTest() {
  const out = [];
  let failed = 0;
  const ok = (name, cond, detail = '') => {
    out.push(`  ${cond ? ' ok  ' : 'FAIL '} ${name}${detail ? ` — ${detail}` : ''}`);
    if (!cond) failed += 1;
  };
  const real = await measure({});

  // 1. The wall clears the footprint, not the centre. A square roof rotated 45
  //    degrees reaches further west than its own width suggests, and the centre
  //    test cannot see it.
  const p = { center_local_enu_m: [-100, 0], footprint_ft: [40, 40], rotation_deg: 45 };
  const edge = footprintWestEdge(p);
  ok('a rotated footprint reaches further west than half its width',
    Math.abs(edge - (-100 - (40 * FT_TO_M * Math.SQRT2) / 2)) < 1e-9, `E ${edge.toFixed(2)}`);
  ok('…and the centre would have reported it 8.62 m further east',
    Math.abs(-100 - edge - 8.62) < 0.01);

  // 2. The wall rounds WEST onto the lattice, never to-nearest.
  const w1 = deriveWall({ westmostEdge: -671.54, maxResidualM: 32.7, cell: 2.5, currentEMin: -320 });
  ok('the derived wall lands on the lattice west of the clearance', w1 === -705, `E ${w1}`);
  ok('…and clears the clearance rather than landing just inside it',
    -671.54 - w1 >= 32.7, `${(-671.54 - w1).toFixed(2)} m >= 32.7 m`);
  const w2 = deriveWall({ westmostEdge: -670.0, maxResidualM: 32.5, cell: 2.5, currentEMin: -320 });
  ok('a clearance that lands exactly on a lattice column does not add a spare one',
    w2 === -702.5, `E ${w2}`);

  // 3. The recipe's round figure is the thing this tool exists to check.
  ok('the round -700 does NOT clear the worst residual',
    real.wall.error_bar.asked_clears_worst === false,
    `short by ${(-real.wall.error_bar.asked_clears_worst_by_m).toFixed(2)} m`);

  // 4. Move the westernmost placement and the wall moves with it.
  const recipe = JSON.parse(await readFile(path.join(ROOT, RECIPE), 'utf8'));
  const moved = JSON.parse(JSON.stringify(recipe));
  const target = moved.placements.find((x) => x.id === real.held_slots.westmost.id);
  target.center_local_enu_m[0] = Number(target.center_local_enu_m[0]) - 50;
  const after = await measure({ recipe: moved });
  ok('a placement moved 50 m west moves the derived wall west with it',
    after.wall.derived_e_m === real.wall.derived_e_m - 50,
    `E ${after.wall.derived_e_m}`);
  ok('…and the gate refuses the committed reading against it',
    diff(after, real).some((b) => b.startsWith('wall.derived_e_m')));

  // 5. A street carried west of the derived wall is caught, and the drawn and
  //    platted-only populations are never added together.
  const streets = JSON.parse(await readFile(path.join(ROOT, 'data/streets/1835.json'), 'utf8')).streets;
  const bent = JSON.parse(JSON.stringify(streets));
  const lake = bent.find((s) => s.id === 'lake');
  lake.path_local_enu_m[0] = [-900, lake.path_local_enu_m[0][1]];
  const withBent = await measure({ streets: bent });
  ok('a DRAWN street carried past the derived wall lands in the drawn population',
    withBent.streets.still_west_of_the_derived_wall.drawn.some((s) => s.id === 'lake'));
  ok('…and not in the platted-only one',
    !withBent.streets.still_west_of_the_derived_wall.platted_only.some((s) => s.id === 'lake'));
  ok('…and the gate refuses the committed reading against it',
    diff(withBent, real).some((b) => b.includes('lake')));

  // 6. The reading on disk is the one this tool derives.
  const onDisk = JSON.parse(await readFile(path.join(ROOT, READING), 'utf8'));
  ok('the committed reading re-derives', diff(real, onDisk).length === 0,
    diff(real, onDisk).join('; '));

  console.log(out.join('\n'));
  console.log(failed ? `SELF-TEST FAIL — ${failed}` : 'SELF-TEST PASS');
  return failed ? 1 : 0;
}

async function main(argv) {
  const arg = (k, d) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);
  if (argv.includes('--self-test')) return selfTest();
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
    let heldReading;
    try {
      heldReading = JSON.parse(await readFile(path.join(ROOT, READING), 'utf8'));
    } catch (err) {
      console.error(`${READING} is unreadable (${err.message}) — this reading is the `
        + 'committed answer to T-1415 and losing it loses the answer.');
      return 1;
    }
    const bad = diff(fresh, heldReading);
    if (bad.length) {
      console.error(`${READING} no longer matches what tools/measure_west_of_box.mjs re-derives:`);
      for (const b of bad) console.error(`  - ${b}`);
      console.error('Re-run with --write and say in the PR what moved and why.');
      return 1;
    }
    console.log(`west-wall reading holds: wall derived at E ${heldReading.wall.derived_e_m}, `
      + `${heldReading.held_slots.held} slots held, `
      + `${heldReading.field_cost.cols_then - heldReading.field_cost.cols_now} columns to add`);
    return 0;
  }
  console.log(table(fresh));
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main(process.argv.slice(2)).then((c) => process.exit(c));
}
