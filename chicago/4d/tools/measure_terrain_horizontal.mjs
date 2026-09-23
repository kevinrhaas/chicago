/**
 * measure_terrain_horizontal.mjs — the artefact the conforming pass does NOT
 * repair, measured where a visitor meets it.
 *
 * R-BUG3c found that `gltf-transform optimize` quantises the published ground
 * onto a 306 mm VERTICAL lattice, and fixed the consequence rather than the
 * cause: `conformGroundToField()` reads every height back off `heightfield.bin`
 * at load, so the height at a ground vertex is the field's own answer to the
 * micron. What that repair cannot touch is the other two axes. The same
 * quantiser moves E and N by up to 153 mm, and a vertex conformed at a
 * displaced position holds the right height for the wrong place.
 *
 * R-W6 asks whether that is worth 5.8 MB — 688 KB quantised against 6.45 MB
 * exact — and says the honest order is to measure the artefact BEFORE trading
 * for it. This is that measurement, and it is deliberately not a screenshot:
 *
 *   1. the DISPLACEMENT itself, against the master mesh, matched in plan
 *      because `meshopt` reorders vertices for the vertex cache; and
 *   2. what it costs the visitor — the drawn ground's departure from the field
 *      at every one of the field's own sample points, for every mesh, so the
 *      quantiser's share is separated from the DECIMATION error the mesh
 *      carries either way.
 *
 * (2) is the number that matters, because it is the number R-BUG3c measured
 * when the road was buried: roads, flora roots, building anchors and collision
 * are all placed at a true (E, N) with the field's height, so "is the thing
 * placed there under the ground that is drawn there" is the whole question. The
 * drawn ground is read by interpolating the containing triangle in plan, the
 * way a rasteriser does — no raycaster, no assumption about how the mesh is
 * built.
 *
 *   node tools/measure_terrain_horizontal.mjs                     table + verdict
 *   node tools/measure_terrain_horizontal.mjs --gate              assert, for check.sh
 *   node tools/measure_terrain_horizontal.mjs --json              machine-readable
 *   node tools/measure_terrain_horizontal.mjs --mesh f.glb=label  score a candidate
 *   node tools/measure_terrain_horizontal.mjs --epoch <id>
 *
 * `--mesh` is how a payload experiment is priced: build a candidate derivative
 * with the same `gltf-transform` the bake uses, hand it to this, and read the
 * same columns as the file that ships. Nothing here writes a GLB, because
 * nothing in this repo may author geometry outside a bake.
 *
 * Exit status is 0 for a report and 1 only when it cannot read what it was asked
 * to read — EXCEPT under `--gate`, which is new (T-0152) and is the reason the
 * artefact this file was written to measure no longer exists.
 *
 * It reported for a week because there was nothing to assert: no setting made
 * the number pass, so a gate on it would only have said that a compressor is a
 * compressor. T-0152 changed that. `generators/terrain_gen.py` now DERIVES the
 * skirt margin so the quantiser's rung is an exact submultiple of the terrain
 * grid, which puts every ground vertex on a rung and takes the plan displacement
 * to zero rather than merely making it small. Zero is a thing a gate can hold,
 * and it is held here rather than in the generator alone because the generator
 * asserts its own arithmetic while this asserts the BYTES — the same distinction
 * `measure_terrain_fit.mjs` draws between a bit depth asked for and one shipped.
 *
 * `tools/check.sh` runs it. It also still holds the master's fit through
 * `measure_terrain_fit.mjs`, and `tools/smoke_renderer.mjs` still holds the
 * surface actually drawn.
 */

import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { loadHeightfield, meshoptDecoder, groundVertices } from './measure_terrain_fit.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** `renderers/web/js/streets.js` lifts the road ribbon this far off the sampled
 * ground. It is the smallest vertical budget anything in this town is placed
 * with, so a surface error big enough to eat it is one that can bury a road —
 * which is exactly how R-BUG3c presented. */
export const LIFT_M = 0.022;

/** `generators/terrain_gen.py`'s MESH_FIT_TOLERANCE_M — the drift the generator
 * refuses to export a ground mesh past. */
export const MESH_FIT_TOLERANCE_M = 0.03;

/** How far a shipped vertex may stand from its master's plan position under
 * `--gate`, in metres. A micron, and deliberately not a budget: since T-0152 the
 * quantiser's rung divides the terrain grid exactly, so the displacement is zero
 * by construction and anything above float noise means the construction broke.
 * It is `generators/terrain_gen.py`'s LATTICE_RESIDUAL_TOLERANCE_M, the same
 * number on the other side of the bake. */
export const PLAN_LATTICE_TOLERANCE_M = 1e-6;

// --- the surface, as a rasteriser would read it --------------------------- //

/**
 * A plan-space bucket index over the mesh's triangles, restricted to the
 * heightfield's box.
 *
 * Restricted deliberately: the skirt's triangles run 1.55 km past the box on
 * every side, and indexing them whole would put one triangle in thousands of
 * cells to answer queries that are never asked. Outside the box there is no
 * field to compare against anyway — `measureMesh()` skips those vertices for
 * the same reason.
 */
function planIndex(xyz, indices, box, cell = 10) {
  const cols = Math.ceil((box.eMax - box.eMin) / cell);
  const rows = Math.ceil((box.nMax - box.nMin) / cell);
  const buckets = new Array(cols * rows);
  const tris = indices.length / 3;
  for (let t = 0; t < tris; t += 1) {
    const a = indices[t * 3] * 3;
    const b = indices[t * 3 + 1] * 3;
    const c = indices[t * 3 + 2] * 3;
    // ENU north is -z; the index works in (E, N) so the query does too.
    const eLo = Math.min(xyz[a], xyz[b], xyz[c]);
    const eHi = Math.max(xyz[a], xyz[b], xyz[c]);
    const nLo = Math.min(-xyz[a + 2], -xyz[b + 2], -xyz[c + 2]);
    const nHi = Math.max(-xyz[a + 2], -xyz[b + 2], -xyz[c + 2]);
    if (eHi < box.eMin || eLo > box.eMax || nHi < box.nMin || nLo > box.nMax) continue;
    const i0 = Math.max(0, Math.floor((eLo - box.eMin) / cell));
    const i1 = Math.min(cols - 1, Math.floor((eHi - box.eMin) / cell));
    const j0 = Math.max(0, Math.floor((nLo - box.nMin) / cell));
    const j1 = Math.min(rows - 1, Math.floor((nHi - box.nMin) / cell));
    for (let j = j0; j <= j1; j += 1) {
      for (let i = i0; i <= i1; i += 1) {
        (buckets[j * cols + i] ??= []).push(t);
      }
    }
  }
  return { buckets, cols, rows, cell, box };
}

/**
 * The height of the drawn surface at a plan position, or null where no triangle
 * covers it.
 *
 * Barycentric in plan, which is what a rasteriser interpolates. A triangle
 * degenerate in plan — a vertical wall seen from above — covers no query point
 * and is skipped rather than dividing by its own zero area. The cell lookup
 * CLAMPS rather than rejecting, because the box's own north and east edges land
 * exactly on the last cell boundary: rejecting them dropped 1,173 of the
 * field's samples and reported them as ground no triangle covers.
 */
function surfaceAt(idx, xyz, indices, e, n) {
  const i = Math.min(idx.cols - 1, Math.max(0, Math.floor((e - idx.box.eMin) / idx.cell)));
  const j = Math.min(idx.rows - 1, Math.max(0, Math.floor((n - idx.box.nMin) / idx.cell)));
  const bucket = idx.buckets[j * idx.cols + i];
  if (!bucket) return null;
  for (const t of bucket) {
    const a = indices[t * 3] * 3;
    const b = indices[t * 3 + 1] * 3;
    const c = indices[t * 3 + 2] * 3;
    const ae = xyz[a]; const an = -xyz[a + 2];
    const be = xyz[b]; const bn = -xyz[b + 2];
    const ce = xyz[c]; const cn = -xyz[c + 2];
    const d = (bn - cn) * (ae - ce) + (ce - be) * (an - cn);
    if (d === 0) continue;
    const w0 = ((bn - cn) * (e - ce) + (ce - be) * (n - cn)) / d;
    if (w0 < 0 || w0 > 1) continue;
    const w1 = ((cn - an) * (e - ce) + (ae - ce) * (n - cn)) / d;
    if (w1 < 0 || w1 > 1) continue;
    const w2 = 1 - w0 - w1;
    if (w2 < 0 || w2 > 1) continue;
    return w0 * xyz[a + 1] + w1 * xyz[b + 1] + w2 * xyz[c + 1];
  }
  return null;
}

/** `renderers/web/js/terrain.js` conformGroundToField(), on plain arrays.
 *
 * Identical in every respect that matters, including the clamp: the skirt lies
 * outside the box, where sampling at the clamped position reproduces the
 * generator's own rule of carrying each boundary vertex outward at its own
 * height. Conforming is what the browser does to whatever it loads, so every
 * mesh is measured after it — otherwise this would measure the 306 mm lattice
 * R-BUG3c already repaired instead of the artefact left behind.
 *
 * The one thing it does NOT copy is the renderer's termination taper (T-0939),
 * which bends the apron down over a landform the box has cut. That is deliberate
 * and not drift: every measurement this file reports is restricted to the box —
 * `measureMesh()` skips a vertex the field cannot answer for and `displacement()`
 * skips one outside it — and the taper applies only outside it, where the factor
 * is 0 at the seam. Copying it here would change no reported number and would put
 * a second reading of the apron's rule in a third file.
 */
function conform(xyz, hf, box) {
  let worst = 0;
  for (let i = 0; i < xyz.length; i += 3) {
    const e = Math.min(box.eMax, Math.max(box.eMin, xyz[i]));
    const n = Math.min(box.nMax, Math.max(box.nMin, -xyz[i + 2]));
    const y = hf.height(e, n);
    const d = Math.abs(y - xyz[i + 1]);
    if (d > worst) worst = d;
    xyz[i + 1] = y;
  }
  return worst;
}

function summarise(values) {
  if (!values.length) return { samples: 0 };
  const abs = Float64Array.from(values, Math.abs).sort();
  const sum = values.reduce((a, b) => a + b, 0);
  const sq = values.reduce((a, b) => a + b * b, 0);
  const pct = (p) => abs[Math.min(abs.length - 1, Math.floor(p * abs.length))];
  return {
    samples: values.length,
    mean_m: sum / values.length,
    rms_m: Math.sqrt(sq / values.length),
    p95_abs_m: pct(0.95),
    p99_abs_m: pct(0.99),
    max_abs_m: abs[abs.length - 1],
  };
}

/**
 * How far each vertex moved in plan, matched to the master by position.
 *
 * NOT by index: `meshopt` reorders vertices for the vertex cache, and a paired
 * read in file order reports the mesh's own 2.5 m grid spacing as its
 * quantisation error — 3.96 km at the skirt, which at least announces itself.
 * The match is unambiguous because the displacement is bounded by half a
 * quantisation step (153 mm at 14 bits) and the mesh's own vertices are 2.5 m
 * apart, so the nearest master vertex is always the right one; the largest
 * match distance is reported so that stops being an assumption.
 */
function displacement(master, mesh, box, cell = 2.5) {
  const cols = Math.ceil((box.eMax - box.eMin) / cell) + 1;
  const rows = Math.ceil((box.nMax - box.nMin) / cell) + 1;
  const grid = new Array(cols * rows);
  const key = (e, n) => {
    const i = Math.floor((e - box.eMin) / cell);
    const j = Math.floor((n - box.nMin) / cell);
    if (i < 0 || j < 0 || i >= cols || j >= rows) return -1;
    return j * cols + i;
  };
  for (let v = 0; v < master.count; v += 1) {
    const k = key(master.xyz[v * 3], -master.xyz[v * 3 + 2]);
    if (k >= 0) (grid[k] ??= []).push(v);
  }
  const de = [];
  const dn = [];
  const plan = [];
  let unmatched = 0;
  for (let v = 0; v < mesh.count; v += 1) {
    const e = mesh.xyz[v * 3];
    const n = -mesh.xyz[v * 3 + 2];
    if (e < box.eMin || e > box.eMax || n < box.nMin || n > box.nMax) continue;
    let best = -1;
    let bestD = Infinity;
    const i0 = Math.floor((e - box.eMin) / cell);
    const j0 = Math.floor((n - box.nMin) / cell);
    for (let j = j0 - 1; j <= j0 + 1; j += 1) {
      for (let i = i0 - 1; i <= i0 + 1; i += 1) {
        if (i < 0 || j < 0 || i >= cols || j >= rows) continue;
        for (const c of grid[j * cols + i] ?? []) {
          const d = Math.hypot(master.xyz[c * 3] - e, -master.xyz[c * 3 + 2] - n);
          if (d < bestD) { bestD = d; best = c; }
        }
      }
    }
    if (best < 0 || bestD > cell / 2) { unmatched += 1; continue; }
    de.push(e - master.xyz[best * 3]);
    dn.push(n - (-master.xyz[best * 3 + 2]));
    plan.push(bestD);
  }
  return { unmatched, east: summarise(de), north: summarise(dn), plan: summarise(plan) };
}

/**
 * The town's street centrelines, as flat segments in plan.
 *
 * A surface error only matters where something is placed on the ground, and the
 * road ribbon is both the tightest budget (LIFT_M) and the thing R-BUG3c watched
 * disappear. So the report says how close the over-budget samples come to a
 * street rather than leaving them as coordinates the reader has to look up.
 */
async function streetSegments(root, scene) {
  try {
    const doc = JSON.parse(await readFile(path.join(root, `data/streets/${scene}.json`), 'utf8'));
    const segs = [];
    for (const s of doc.streets ?? []) {
      const pts = s.path_local_enu_m ?? [];
      const name = s.name_1835 ?? s.id;
      for (let i = 1; i < pts.length; i += 1) segs.push([pts[i - 1], pts[i], name]);
    }
    return segs;
  } catch {
    return null;
  }
}

function distanceToSegments(e, n, segs) {
  let best = Infinity;
  let street = null;
  for (const [a, b, name] of segs) {
    const ve = b[0] - a[0];
    const vn = b[1] - a[1];
    const len2 = ve * ve + vn * vn;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((e - a[0]) * ve + (n - a[1]) * vn) / len2));
    const d = Math.hypot(e - (a[0] + t * ve), n - (a[1] + t * vn));
    if (d < best) { best = d; street = name; }
  }
  return { distance_m: best, street };
}

// --- the measurement ------------------------------------------------------ //

export async function measureTerrainHorizontal({
  epoch, root = ROOT, extra = [], cell = 10, scene = '1835',
} = {}) {
  const decoder = await meshoptDecoder(root);
  const epochDir = path.join(root, 'data/terrain/epochs', epoch);
  const hf = await loadHeightfield(epochDir);
  const { cols, rows, cell_m: step, origin_e: oe, origin_n: on } = hf.meta;
  const box = { eMin: oe, eMax: oe + (cols - 1) * step, nMin: on, nMax: on + (rows - 1) * step };
  const water = hf.meta.water_surface_m ?? 0;
  const streets = await streetSegments(root, scene);

  const wanted = [
    ['master', path.join(root, `assets/gltf/terrain__${epoch}.glb`)],
    ['shipped', path.join(root, `assets/web/terrain__${epoch}.glb`)],
    ...extra.map(({ label, file }) => [label, path.resolve(file)]),
  ];

  let master = null;
  const meshes = {};
  for (const [label, file] of wanted) {
    const mesh = await groundVertices(file, decoder, { indices: true });
    master ??= mesh;
    const bytes = (await stat(file)).size;

    // The vertical lattice, recovered from the shipped heights rather than from
    // the JSON — see measure_terrain_fit.mjs verticalStep() for why the
    // arithmetic answer is wrong by a factor of four.
    let lattice = null;
    if (mesh.accessor.normalized) {
      const ys = [...new Set(Array.from({ length: mesh.count }, (_, i) => mesh.xyz[i * 3 + 1]))]
        .sort((a, b) => a - b);
      lattice = Infinity;
      for (let i = 1; i < ys.length; i += 1) lattice = Math.min(lattice, ys[i] - ys[i - 1]);
      if (!Number.isFinite(lattice)) lattice = null;
    }

    // The height error the browser is handed, before conforming repairs it.
    const before = [];
    for (let i = 0; i < mesh.count; i += 1) {
      const e = mesh.xyz[i * 3];
      const n = -mesh.xyz[i * 3 + 2];
      if (!hf.inside(e, n)) continue;
      before.push(mesh.xyz[i * 3 + 1] - hf.height(e, n));
    }

    const moved = label === 'master' ? null : displacement(master, mesh, box);

    // Then the surface a visitor is actually shown, at every one of the field's
    // own sample points: the ground the town is placed on, asked about at every
    // place it is defined, rather than at whichever anchors a camera happens to
    // be offered.
    const correction = conform(mesh.xyz, hf, box);
    const idx = planIndex(mesh.xyz, mesh.indices, box, cell);
    const errors = [];
    const overLiftSlopes = [];
    let uncovered = 0;
    let overLift = 0;
    let overLiftDry = 0;
    let nearestStreet = null;
    let worst = { abs: -1 };
    // The local gradient, because it is the whole mechanism: a vertex conformed
    // at a displaced position holds the field's height for the WRONG place, so
    // what the displacement costs is (slope × displacement) and nothing else.
    // Flat prairie cannot show this artefact at any bit depth.
    const slopeAt = (e, n) => Math.hypot(
      (hf.height(e + step, n) - hf.height(e - step, n)) / (2 * step),
      (hf.height(e, n + step) - hf.height(e, n - step)) / (2 * step),
    );
    for (let j = 0; j < rows; j += 1) {
      const n = on + j * step;
      for (let i = 0; i < cols; i += 1) {
        const e = oe + i * step;
        const y = surfaceAt(idx, mesh.xyz, mesh.indices, e, n);
        if (y === null) { uncovered += 1; continue; }
        const ground = hf.height(e, n);
        const err = y - ground;
        errors.push(err);
        if (Math.abs(err) > LIFT_M) {
          overLift += 1;
          if (ground > water) overLiftDry += 1;
          overLiftSlopes.push(slopeAt(e, n));
          if (streets) {
            const near = distanceToSegments(e, n, streets);
            if (near.distance_m < (nearestStreet?.distance_m ?? Infinity)) {
              nearestStreet = { ...near, e, n, err, slope: slopeAt(e, n) };
            }
          }
        }
        if (Math.abs(err) > worst.abs) {
          worst = { abs: Math.abs(err), e, n, err, ground, slope: slopeAt(e, n) };
        }
      }
    }
    meshes[label] = {
      file: path.relative(root, file),
      bytes,
      quantised: !!mesh.accessor.normalized,
      vertical_lattice_m: lattice,
      before_conform: summarise(before),
      displacement: moved,
      conform_correction_max_m: correction,
      surface: {
        queried: rows * cols,
        uncovered,
        over_lift: overLift,
        over_lift_dry: overLiftDry,
        over_lift_slope: summarise(overLiftSlopes),
        over_lift_nearest_street: nearestStreet,
        median_slope: summarise(overLiftSlopes).samples
          ? Float64Array.from(overLiftSlopes).sort()[Math.floor(overLiftSlopes.length / 2)]
          : null,
        worst,
        ...summarise(errors),
      },
    };
  }

  return {
    epoch,
    box,
    query: { spacing_m: step, points: rows * cols },
    lift_m: LIFT_M,
    tolerance_m: MESH_FIT_TOLERANCE_M,
    meshes,
  };
}

function mm(v) {
  return v === null || v === undefined ? '—' : `${(v * 1000).toFixed(1)}`;
}

async function main() {
  const argv = process.argv.slice(2);
  const arg = (name, fallback) => (argv.includes(name) ? argv[argv.indexOf(name) + 1] : fallback);
  const epoch = arg('--epoch', 'e1834_harbor_cut');
  const extra = argv.reduce((acc, a, i) => {
    if (argv[i - 1] !== '--mesh') return acc;
    const [file, label] = a.split('=');
    acc.push({ file, label: label ?? path.basename(file, '.glb') });
    return acc;
  }, []);
  const result = await measureTerrainHorizontal({ epoch, extra });
  if (argv.includes('--gate')) return gate(result);
  if (argv.includes('--json')) {
    process.stdout.write(`${JSON.stringify(result, null, 1)}\n`);
    return;
  }
  console.log(`   terrain quantisation — ${epoch}, all figures in mm\n`);
  console.log('   mesh          KB    lattice   |Δy| before   plan move   '
    + 'SURFACE after conforming');
  console.log('                                   conform      max         '
    + 'rms     p99     max');
  for (const [label, m] of Object.entries(result.meshes)) {
    const s = m.surface;
    console.log(`   ${label.padEnd(11)} ${String(Math.round(m.bytes / 1024)).padStart(5)}`
      + `  ${(m.vertical_lattice_m === null ? 'float' : mm(m.vertical_lattice_m)).padStart(7)}`
      + `  ${mm(m.before_conform.max_abs_m).padStart(11)}`
      + `  ${(m.displacement ? mm(m.displacement.plan.max_abs_m) : '—').padStart(10)}`
      + `  ${mm(s.rms_m).padStart(8)}${mm(s.p99_abs_m).padStart(8)}${mm(s.max_abs_m).padStart(8)}`);
  }
  const base = result.meshes.master.surface;
  console.log(`\n   the surface columns are measured at all ${result.query.points.toLocaleString()}`
    + ' of the field\'s own sample points, AFTER conformGroundToField().');
  console.log(`   the master's ${mm(base.rms_m)} mm rms / ${mm(base.max_abs_m)} mm max is`
    + ' DECIMATION — every row carries it and no compressor setting touches it.');
  for (const [label, m] of Object.entries(result.meshes)) {
    if (label === 'master') continue;
    const s = m.surface;
    console.log(`   ${label}: ${s.over_lift.toLocaleString()} samples past the `
      + `${mm(result.lift_m)} mm road lift (${s.over_lift_dry.toLocaleString()} of them on dry `
      + `ground, median slope ${s.median_slope === null ? '—' : `${(s.median_slope * 100).toFixed(0)} %`}`
      + `), worst ${mm(s.worst.abs)} mm at E ${s.worst.e.toFixed(1)} N ${s.worst.n.toFixed(1)}`
      + ` (ground ${s.worst.ground.toFixed(2)} m, slope ${(s.worst.slope * 100).toFixed(0)} %)`
      + (!s.over_lift_nearest_street ? ''
        : `\n${' '.repeat(3)}${' '.repeat(label.length)}  the closest of them stands `
          + `${s.over_lift_nearest_street.distance_m.toFixed(1)} m from the centreline of `
          + `${s.over_lift_nearest_street.street}, `
          + `${mm(s.over_lift_nearest_street.err)} mm over the road it would carry`));
  }
}

/**
 * The two assertions, on the shipped bytes.
 *
 * ONE: the shipped ground's vertices stand exactly where the master's do, in
 * plan. That is the mechanism, and it is the one that fails FIRST — a change in
 * the box, in the grid spacing, in the bit depth or in `gltf-transform`'s own
 * quantisation model breaks commensurability, and the displacement comes back
 * before anything is visible. A micron of slack, four orders under the road lift
 * and four over the arithmetic's own residual.
 *
 * TWO: the consequence, because the mechanism is a theory about the consequence
 * and the consequence is what a visitor stands on. No sample point where the
 * drawn ground departs from the field by more than the road lift — which is what
 * R-BUG3c watched bury the roadway, and what T-0152's acceptance clause names.
 *
 * Both are asserted on the SHIPPED derivative only. The master is float and
 * carries the decimation error the generator already gates; asserting it here
 * would be a second, weaker copy of `measure_terrain_fit.mjs --gate`.
 */
function gate(result) {
  const shipped = result.meshes.shipped;
  const moved = shipped.displacement?.plan?.max_abs_m ?? null;
  const over = shipped.surface.over_lift;
  const worst = shipped.surface.worst;
  console.log(`   the shipped ground's vertices stand ${mm(moved)} mm from the master's in plan`
    + ` (lattice ${mm(shipped.vertical_lattice_m)} mm)`);
  console.log(`   the drawn surface is within ${mm(result.lift_m)} mm of the field at all `
    + `${result.query.points.toLocaleString()} sample points: ${over === 0 ? 'yes' : 'NO'}`
    + ` (worst ${mm(worst.abs)} mm at E ${worst.e.toFixed(1)} N ${worst.n.toFixed(1)})`);
  if (moved === null || moved > PLAN_LATTICE_TOLERANCE_M) {
    console.error(`   the publish step displaced the ground in plan by ${mm(moved)} mm. Its `
      + 'POSITION rung is no longer an exact submultiple of the terrain grid, so a vertex '
      + "conformed at load holds the field's height for the wrong place. See T-0152 and "
      + 'generators/terrain_gen.py skirt_margin_m() — the fix is a terrain bake, not a '
      + 'bit depth.');
    process.exit(1);
  }
  if (over > 0) {
    console.error(`   ${over.toLocaleString()} of the field's sample points carry ground drawn `
      + `more than ${mm(result.lift_m)} mm from where the town is anchored, worst `
      + `${mm(worst.abs)} mm on a ${(worst.slope * 100).toFixed(0)} % slope. The road ribbon is `
      + 'lifted by exactly that much, so this is the budget that buries a roadway (R-BUG3c).');
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exit(1); });
}
