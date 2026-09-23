/**
 * measure_anchors.mjs — whether the places a visitor is OFFERED are places a
 * visitor can stand, measured against the same heightfield the walker uses.
 *
 * T-0467. `data/scenes/*.json` § anchors is the list `goto.js` paints under
 * Viewpoints and `travel.js` rides to, and the smoke harness drives the same
 * ids. Nothing in the gate asked whether an anchor stands on modelled ground.
 * That question was cheap to ignore while every anchor sat inside the 1834
 * plat; T-0464 carried the modelled box south to Twenty-Second Street and this
 * ticket puts cameras 3.8 km down it, most of a mile past the last row any
 * source in this corpus describes. An anchor out there is one typo away from
 * standing in Lake Michigan or on the constant outside the box, and neither
 * failure is visible in a diff.
 *
 * WHAT IS MEASURED, per anchor, and each one is a different way to be wrong:
 *
 *   inside        `contains(e, n)` — the box test terrain.js § Heightfield
 *                 answers `sample()` with `fallbackY` outside. An anchor
 *                 outside the box stands on the constant 0 with the modelled
 *                 scarp beside it.
 *   ground_m      the bilinear sample, in the same metres as the heightfield.
 *   dry           ground stands ABOVE `water_surface_m`. Below it the walker is
 *                 under the water plane: a camera in the lake or in the river
 *                 channel, which is how `forks` was wrong before T-0041 and how
 *                 a southern anchor would be wrong now (the pre-fill shore
 *                 crosses 390 m of easting between Twelfth Street and the box
 *                 floor, so a fixed easting that is dry at one row is not at
 *                 another).
 *   margin_m      metres to the nearest cell that is wet OR outside the box —
 *                 how much room the stand actually has. Reported, and held
 *                 against a floor only for anchors that declare one.
 *   inside_a_roof the anchor's point falls inside a committed structure
 *                 footprint that is NOT walkable. A standing viewpoint inside a
 *                 building is a camera in a wall; an AERIAL anchor
 *                 (`altitude_m`) is exempt, because it is a bird's-eye above
 *                 the ground and the town is the point.
 *   stands_on     the anchor is on a DECK — a structure whose placement
 *                 declares `walk_surface_m`, which is the eight bridges, piers
 *                 and slough crossings. `north_branch_bridge_deck` is the
 *                 anchor this exists for: it stands mid-span over a channel
 *                 2.38 m under the water plane, and it is CORRECT. A deck
 *                 answers the dry test in place of the terrain, so the rule is
 *                 written on the walk surface rather than made an exception for
 *                 one id.
 *
 * It does NOT score the VIEW. Whether an anchor frames anything worth looking
 * at is the renderer smoke's question (tools/smoke_renderer.mjs § JUMPS drives
 * anchors and reads the frame); this tool answers the prior one, offline and in
 * about a second, so a bad coordinate is caught at commit rather than twenty
 * minutes into a leg.
 *
 *   node tools/measure_anchors.mjs                 table + verdict
 *   node tools/measure_anchors.mjs --json          machine-readable
 *   node tools/measure_anchors.mjs --gate          assert against the reading
 *   node tools/measure_anchors.mjs --write         rewrite the reading
 *   node tools/measure_anchors.mjs --self-test     the rules, on synthetic ground
 *
 * `--gate` holds `data/render/anchor_ground_reading.json` against a
 * re-derivation AND asserts the two properties that are not opinions — every
 * anchor inside the box, every standing anchor dry and out of a wall. The
 * reading carries the numbers so a drift in the heightfield under a camera that
 * is still legal is still visible.
 */

import { readFile, writeFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const READING = 'data/render/anchor_ground_reading.json';

/** `renderers/web/js/terrain.js` § Heightfield.fallbackY. */
const FALLBACK_Y = 0;
/** How far out the margin scan looks before it reports "> this". Beyond a few
 *  hundred metres the number stops meaning anything to a person standing there. */
const MARGIN_MAX_M = 400;
/** Metres. Re-derivation is deterministic; this is slack for float formatting. */
const TOL_M = 0.01;

// --- the renderer's own sampler ------------------------------------------- //

/** terrain.js § Heightfield semantics: bilinear inside the box, the constant
 *  outside it. Deliberately NOT clamped — clamping would report the bank's
 *  height out on the prairie and hide exactly the failure this tool is for. */
export function heightfield(meta, arr) {
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
    cell,
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

async function loadHeightfield(epoch) {
  const dir = path.join(ROOT, 'data/terrain/epochs', epoch);
  const meta = JSON.parse(await readFile(path.join(dir, 'heightfield.json'), 'utf8'));
  const raw = await readFile(path.join(dir, meta.bin ?? 'heightfield.bin'));
  const arr = meta.encoding === 'float32'
    ? new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4)
    : new Int16Array(raw.buffer, raw.byteOffset, raw.byteLength / 2);
  return heightfield(meta, arr);
}

// --- the measurements ------------------------------------------------------ //

/** Metres to the nearest cell that is wet or off the box, scanned on rings at
 *  the terrain cell. Returns null past MARGIN_MAX_M — "further than matters". */
export function marginToWater(hf, e, n, waterM) {
  for (let r = hf.cell; r <= MARGIN_MAX_M; r += hf.cell) {
    const steps = Math.max(12, Math.ceil((2 * Math.PI * r) / hf.cell));
    for (let s = 0; s < steps; s++) {
      const a = (2 * Math.PI * s) / steps;
      const te = e + r * Math.cos(a);
      const tn = n + r * Math.sin(a);
      if (!hf.contains(te, tn) || hf.sample(te, tn) <= waterM) return r;
    }
  }
  return null;
}

/** navigation.js § structureOutlines: the sidecar polygon, rotated and placed. */
export function outline(sidecar) {
  const raw = sidecar?.footprint;
  const polygon = Array.isArray(raw) ? raw : raw?.polygon;
  const placement = sidecar?.placement ?? {};
  if (!Array.isArray(polygon) || polygon.length < 3) return null;
  const th = (placement.rotation_deg ?? 0) * (Math.PI / 180);
  const cos = Math.cos(th);
  const sin = Math.sin(th);
  const e0 = placement.local_e ?? 0;
  const n0 = placement.local_n ?? 0;
  return polygon.map(([u, v]) => [e0 + u * cos + v * sin, n0 - u * sin + v * cos]);
}

/** Even-odd ray cast. A point on an edge counts as inside, which is the
 *  conservative answer for "is the camera in a wall". */
export function inPolygon([e, n], poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [ei, ni] = poly[i];
    const [ej, nj] = poly[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) inside = !inside;
  }
  return inside;
}

async function sceneOutlines(scene) {
  const dir = path.join(ROOT, 'data/sidecars', scene);
  const out = [];
  let names = [];
  try { names = await readdir(dir); } catch { return out; }
  for (const name of names) {
    if (!name.endsWith('.json')) continue;
    const sidecar = JSON.parse(await readFile(path.join(dir, name), 'utf8'));
    const poly = outline(sidecar);
    if (poly) {
      out.push({
        id: name.replace(/\.json$/, ''),
        poly,
        // A declared walk surface is what makes a footprint somewhere to STAND
        // rather than something to stand in. See docs/GLB-CONTRACT.md.
        walk_surface_m: sidecar.placement?.walk_surface_m ?? null,
      });
    }
  }
  return out;
}

export async function measure({ scene = '1835' } = {}) {
  const sceneFile = JSON.parse(await readFile(path.join(ROOT, 'data/scenes', `${scene}.json`), 'utf8'));
  const hf = await loadHeightfield(sceneFile.terrain_epoch);
  const waterM = hf.meta.water_surface_m ?? 0;
  const roofs = await sceneOutlines(scene);
  const rows = sceneFile.anchors.map((a) => {
    const e = a.local_e;
    const n = a.local_n;
    const aerial = Number.isFinite(a.altitude_m);
    const inside = hf.contains(e, n);
    const ground = hf.sample(e, n);
    const margin = inside ? marginToWater(hf, e, n, waterM) : 0;
    const under = aerial ? null : (roofs.find((r) => inPolygon([e, n], r.poly)) ?? null);
    const deck = under && Number.isFinite(under.walk_surface_m) ? under : null;
    return {
      id: a.id,
      local_e: e,
      local_n: n,
      aerial,
      inside,
      ground_m: Number(ground.toFixed(3)),
      // A deck carries the visitor above the water; the terrain under it does not.
      dry: inside && (ground > waterM || !!deck),
      stands_on: deck ? deck.id : null,
      deck_m: deck ? deck.walk_surface_m : null,
      margin_m: margin === null ? null : Number(margin.toFixed(2)),
      inside_a_roof: deck ? null : (under?.id ?? null),
    };
  });
  return {
    _doc: 'GENERATED by tools/measure_anchors.mjs — do not hand-edit. Whether every '
      + 'viewpoint a visitor is offered stands on modelled, dry, unbuilt ground.',
    ticket: 'T-0467',
    scene,
    epoch: sceneFile.terrain_epoch,
    box_local_enu_m: hf.meta.box_local_enu_m,
    water_surface_m: waterM,
    margin_scan_max_m: MARGIN_MAX_M,
    anchors: rows,
    totals: {
      anchors: rows.length,
      outside_the_box: rows.filter((r) => !r.inside).length,
      wet: rows.filter((r) => !r.dry).length,
      in_a_roof: rows.filter((r) => r.inside_a_roof).length,
      on_a_deck: rows.filter((r) => r.stands_on).length,
      southernmost_n: rows.length ? Math.min(...rows.map((r) => r.local_n)) : null,
    },
  };
}

// --- the gate -------------------------------------------------------------- //

function faults(reading) {
  const bad = [];
  for (const a of reading.anchors) {
    if (!a.inside) bad.push(`${a.id}: stands outside the modelled box — the walker gets the constant ${FALLBACK_Y} m there, not ground`);
    else if (!a.dry) bad.push(`${a.id}: ground ${a.ground_m} m is at or below the water surface ${reading.water_surface_m} m and no deck carries it — the camera is in the water`);
    if (a.inside_a_roof) bad.push(`${a.id}: falls inside ${a.inside_a_roof}'s footprint — a standing viewpoint inside a building is a camera in a wall`);
  }
  return bad;
}

function drift(fresh, committed) {
  const out = [];
  const byId = new Map((committed.anchors ?? []).map((a) => [a.id, a]));
  for (const a of fresh.anchors) {
    const was = byId.get(a.id);
    if (!was) { out.push(`${a.id}: not in the committed reading`); continue; }
    byId.delete(a.id);
    for (const k of ['local_e', 'local_n', 'ground_m']) {
      if (Math.abs((was[k] ?? NaN) - a[k]) > TOL_M) out.push(`${a.id}.${k}: reading ${was[k]}, re-derived ${a[k]}`);
    }
    if (was.inside_a_roof !== a.inside_a_roof) out.push(`${a.id}.inside_a_roof: reading ${was.inside_a_roof}, re-derived ${a.inside_a_roof}`);
    if ((was.stands_on ?? null) !== (a.stands_on ?? null)) out.push(`${a.id}.stands_on: reading ${was.stands_on ?? null}, re-derived ${a.stands_on}`);
    if (was.margin_m !== a.margin_m) out.push(`${a.id}.margin_m: reading ${was.margin_m}, re-derived ${a.margin_m}`);
  }
  for (const id of byId.keys()) out.push(`${id}: in the committed reading, no longer an anchor`);
  return out;
}

// --- self-test ------------------------------------------------------------- //

function selfTest() {
  const fails = [];
  const ok = (what, cond) => { if (!cond) fails.push(what); };
  // A 3x3 field, 10 m cells, origin at (0, 0): a dry plateau with one wet cell.
  const meta = { cols: 3, rows: 3, cell_m: 10, origin_e: 0, origin_n: 0, scale: 1, offset: 0, water_surface_m: 0 };
  const hf = heightfield(meta, new Int16Array([2, 2, 2, 2, 2, 2, 2, -1, 2]));
  ok('contains() refuses a point west of the box', hf.contains(-1, 10) === false);
  ok('contains() admits the far corner', hf.contains(20, 20) === true);
  ok('sample() answers the constant outside the box', hf.sample(-5, 10) === FALLBACK_Y);
  ok('sample() reads the plateau', Math.abs(hf.sample(0, 0) - 2) < 1e-9);
  ok('sample() reads the wet cell', hf.sample(10, 20) < 0);
  ok('marginToWater finds the wet cell one ring out', marginToWater(hf, 0, 20, 0) === 10);
  ok('marginToWater reports the box edge as a margin', marginToWater(hf, 0, 0, 0) === 10);
  // A unit square placed at (100, 100) and turned 90 degrees still contains its own centre.
  const poly = outline({ footprint: [[0, 0], [10, 0], [10, 10], [0, 10]], placement: { local_e: 100, local_n: 100, rotation_deg: 90 } });
  ok('outline() places and turns a footprint', poly.length === 4);
  ok('inPolygon() catches a point inside the turned footprint', inPolygon([105, 95], poly));
  ok('inPolygon() lets a point outside it through', !inPolygon([130, 130], poly));
  // The fault rules fire on each way of being wrong, and stay quiet on a good anchor.
  const f = (a) => faults({ water_surface_m: 0, anchors: [a] });
  ok('a good anchor raises nothing', f({ id: 'a', inside: true, dry: true, ground_m: 2, inside_a_roof: null }).length === 0);
  ok('a deck over water raises nothing', f({ id: 'a', inside: true, dry: true, ground_m: -2.4, stands_on: 'bridge', inside_a_roof: null }).length === 0);
  ok('an anchor off the box is a fault', f({ id: 'a', inside: false, dry: false, ground_m: 0, inside_a_roof: null }).length === 1);
  ok('a wet anchor is a fault', f({ id: 'a', inside: true, dry: false, ground_m: -1, inside_a_roof: null }).length === 1);
  ok('an anchor in a wall is a fault', f({ id: 'a', inside: true, dry: true, ground_m: 2, inside_a_roof: 'barn' }).length === 1);
  ok('drift() catches a moved anchor', drift(
    { anchors: [{ id: 'a', local_e: 1, local_n: 2, ground_m: 3, margin_m: 4, inside_a_roof: null }] },
    { anchors: [{ id: 'a', local_e: 1, local_n: 9, ground_m: 3, margin_m: 4, inside_a_roof: null }] },
  ).length === 1);
  ok('drift() catches a retired anchor', drift({ anchors: [] }, { anchors: [{ id: 'gone' }] }).length === 1);
  for (const bad of fails) console.error(`FAIL  ${bad}`);
  console.log(fails.length ? `measure_anchors self-test: ${fails.length} failure(s)` : 'measure_anchors self-test: all rules hold');
  return fails.length === 0;
}

// --- cli ------------------------------------------------------------------- //

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const opt = (name, fallback) => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};

if (flag('--self-test')) process.exit(selfTest() ? 0 : 1);

const reading = await measure({ scene: opt('--scene', '1835') });
const bad = faults(reading);

if (flag('--json')) {
  console.log(JSON.stringify(reading, null, 2));
} else if (!flag('--gate') || bad.length) {
  const w = (s, n) => String(s).padEnd(n);
  console.log(`anchors of scene ${reading.scene} on epoch ${reading.epoch}\n`);
  console.log(`${w('id', 30)}${w('e', 11)}${w('n', 11)}${w('ground', 9)}${w('margin', 9)}stand`);
  for (const a of reading.anchors) {
    const stand = !a.inside ? 'OFF THE BOX' : !a.dry ? 'IN THE WATER'
      : a.inside_a_roof ? `IN ${a.inside_a_roof}` : a.stands_on ? `on ${a.stands_on}`
        : a.aerial ? 'aerial' : 'ok';
    console.log(`${w(a.id, 30)}${w(a.local_e, 11)}${w(a.local_n, 11)}${w(`${a.ground_m} m`, 9)}${w(a.margin_m === null ? `>${MARGIN_MAX_M} m` : `${a.margin_m} m`, 9)}${stand}`);
  }
  console.log(`\n${reading.totals.anchors} anchors, southernmost at n ${reading.totals.southernmost_n} m`);
}

if (flag('--write')) {
  await writeFile(path.join(ROOT, READING), `${JSON.stringify(reading, null, 2)}\n`);
  console.log(`wrote ${READING}`);
}

if (flag('--gate')) {
  const committed = JSON.parse(await readFile(path.join(ROOT, READING), 'utf8'));
  const moved = drift(reading, committed);
  for (const line of bad) console.error(`FAIL  ${line}`);
  for (const line of moved) console.error(`FAIL  the committed reading no longer re-derives — ${line}`);
  if (bad.length || moved.length) {
    console.error('\nAn anchor is a place the app OFFERS. Fix the coordinate, or re-measure with '
      + '--write when the ground moved under it on purpose.');
    process.exit(1);
  }
  console.log(`anchor ground: ${reading.totals.anchors} anchors, all inside the box, dry and out of a wall; `
    + 'the committed reading re-derives.');
}
