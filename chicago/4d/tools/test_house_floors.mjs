#!/usr/bin/env node
/**
 * The visitor climbs every stair (renderers/web/js/house-floors.js, back-yards.js stoopDecks,
 * data from tools/prairie_barriers.py floor via derive_doors_scene.py).
 *
 * The owner, 2026-11-14: "I cants walk ups stairs to the door outside a house to interact and
 * see who is home ask them to come out" and "Anywhere there are stairs I should be able to climb".
 *
 *   1. The reader: a floor's cells answer at their heights through the house's drawn turn, its
 *      walls are marked, off the grid is the ground's, and mergeDecks answers as its parts do.
 *   2. The real file: every 1904 front stoop that has a door hung on it is a floor its way up
 *      stands on, and the walker (walker.js, its own step rule) walks from the street up it to the
 *      door at the sill, a tread at a time; and is turned back by the rails and cheek walls beside
 *      it (walking at the flight from its side, it never climbs past a riser's height).
 *   3. The back yards: the walker climbs every back stoop from the yard to its landing at the
 *      door; where a stoop has rails, they stand past any step.
 *   4. A door is knocked at from the treads and landing of its stoop, not only from its foot.
 */
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);

const THREE = await import('three');
const { houseFloorDecks, floorDecks, mergeDecks, stairSurface } = await import('../renderers/web/js/house-floors.js');
const { createWalker, footprintsFrom, WALK } = await import('../renderers/web/js/walker.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { deckGroundHeight } = await import('../renderers/web/js/deck-surface.js');

let checks = 0;
const fails = [];
const ok = (cond, msg) => { checks++; if (!cond) fails.push(msg); };
const read = (rel) => JSON.parse(fs.readFileSync(new URL(rel, import.meta.url), 'utf8'));

/** The matrix buildings.js draws a house at: its placement, standing at `y`. */
const matrixOf = (pl, y = 0) => new THREE.Matrix4().compose(new THREE.Vector3(pl.local_e ?? 0, y, -(pl.local_n ?? 0)),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(pl.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1)).elements;
/** The model's plan (u, v) in local E/N: walker.js's clockwise compass turn. */
const enuOf = (pl, u, v) => {
  const th = (pl.rotation_deg ?? 0) * Math.PI / 180;
  return { e: pl.local_e + u * Math.cos(th) + v * Math.sin(th), n: pl.local_n - u * Math.sin(th) + v * Math.cos(th) };
};

// 1. One house turned 90°, standing 3 m up: a floor of two treads and a wall beside them.
{
  const pl = { local_e: 100, local_n: 200, rotation_deg: 90 };
  // cells i 0..10 (u 0..1), j 0..5 (v 0..0.5): u < 0.5 at 0.40 m, u >= 0.5 at 0.20 m; a wall at j 5.
  const row = { structure: 'x', placement: pl, floor: { cell: 0.1, u0: 0, v0: 0, ni: 10, nj: 6, count: 2,
    rects: '0 5 0 5 40 5 10 0 5 20', wall_count: 1, walls: '0 10 5 6 140' } };
  const [fl, wall] = houseFloorDecks(row, Array.from(matrixOf(pl, 3)));
  const at = (u, v) => enuOf(pl, u, v);
  let p = at(0.2, 0.2);
  ok(Math.abs(fl.heightAt(p.e, p.n) - 3.4) < 1e-5, `the upper tread stands at its height over the house's ground (${fl.heightAt(p.e, p.n)})`);
  p = at(0.7, 0.2);
  ok(Math.abs(fl.heightAt(p.e, p.n) - 3.2) < 1e-5, 'the lower tread at its height');
  p = at(0.7, 0.5);
  ok(fl.heightAt(p.e, p.n) === null && Math.abs(wall.heightAt(p.e, p.n) - 4.4) < 1e-5 && wall.wall === true, 'the wall cell is the walls deck\'s, marked a wall');
  p = at(1.5, 0.2);
  ok(fl.heightAt(p.e, p.n) === null, 'off the grid the ground answers');
  const wrong = { e: 100 - 0.2, n: 200 + 0.2 };
  ok(fl.heightAt(wrong.e, wrong.n) === null, 'the turn is clockwise, as walker.js turns a footprint');
  const merged = mergeDecks([fl, { id: 'slab', y: 3.3, pts: [[99, 199], [101, 199], [101, 201], [99, 201]] }], 'm');
  p = at(0.7, 0.2);
  ok(Math.abs(merged.heightAt(p.e, p.n) - 3.3) < 1e-5, 'merged, the highest part answers');
  p = at(0.2, 0.2);
  ok(Math.abs(merged.heightAt(p.e, p.n) - 3.4) < 1e-5, 'merged, a grid part answers where it is higher');
  ok(merged.heightAt(500, 500) === null, 'merged, nothing answers far off');
  const terrain = { surfaceHeight: () => 3, walkHeight: () => 3, isWater: () => false };
  p = at(0.7, 0.5);
  ok(Math.abs(deckGroundHeight(terrain, stairSurface([fl, wall]), p.e, p.n) - 3) < 1e-6, 'nobody is stood on a wall: a figure there stands on the ground');
  ok(houseFloorDecks({ ...row, floor: { ...row.floor, rects: 'x' } }, Array.from(matrixOf(pl))).length === 0, 'a broken floor is laid as nothing');
}

/** A walker on flat ground at 0, the house's footprint kept, these decks. */
function walkerFor(record, decks) {
  const camera = new THREE.PerspectiveCamera();
  const terrain = { surfaceHeight: () => 0, walkHeight: () => 0, isWater: () => false, height: () => 0 };
  const registry = new Map(record ? [[record.id, record]] : []);
  return createWalker({ camera, terrain, footprints: footprintsFrom(registry), decks, spawn: {} });
}
/** Walk from `from` toward `to` ({e, n}, or a list of them in turn) for up to `seconds`; the
 *  heights stood on, in order. */
function walkTo(w, from, to, seconds = 20) {
  w.teleport({ local_e: from.e, local_n: from.n });
  const ys = [w.state.groundY];
  const intent = { forward: 1, strafe: 0, yawDelta: 0, pitchDelta: 0, clearLook() {}, flying: false, sprint: false };
  const goals = Array.isArray(to) ? [...to] : [to];
  let stuck = 0;
  for (let t = 0; t < seconds && goals.length; t += 1 / 60) {
    const g = goals[0];
    const de = g.e - w.state.e, dn = g.n - w.state.n;
    if (Math.hypot(de, dn) < 0.08 || (stuck > 30 && goals.length > 1)) { goals.shift(); stuck = 0; continue; }
    w.state.yaw = bearingToYaw(Math.atan2(de, dn) * 180 / Math.PI);
    const [e0, n0] = [w.state.e, w.state.n];
    w.update(1 / 60, intent);
    stuck = Math.hypot(w.state.e - e0, w.state.n - n0) < 1e-4 ? stuck + 1 : 0;
    ys.push(w.state.groundY);
  }
  return ys;
}

// 2. The real file: up every hung front door's stoop, and never over its side.
let houses = 0, climbed = 0, walled = 0, rects = 0;
{
  const doors = read('../data/humans/doors_1904.json');
  const rows = [...doors.structures, ...(doors.barriers ?? [])];
  const floors = rows.filter((r) => r.floor);
  houses = floors.length;
  rects = floors.reduce((n, r) => n + r.floor.count + (r.floor.wall_count ?? 0), 0);
  ok(houses >= 70, `the Prairie houses' stoops are read (${houses} floors)`);
  for (const row of doors.structures) {
    const door = (row.doors ?? []).find((d) => d.passage && d.plan?.way?.length >= 2 && d.id.endsWith(':front'));
    if (!door) continue;
    const sc = read(`../data/sidecars/1904/${row.structure}.json`);
    const record = { id: row.structure, sidecar: sc };
    const pl = row.placement;
    ok(!!row.floor, `${row.structure}: its front stoop is a floor to climb`);
    if (!row.floor) continue;
    const decks = stairSurface(floorDecks([row], () => Array.from(matrixOf(pl))));
    // The footprint's doorway is cut by house-doors.js in the app; here the step rule alone.
    const w = walkerFor(null, decks);
    const way = door.plan.way;
    const sill = door.plan.sill;
    // Every point of the way up (derive_doors_scene.py stoop_way, read off the same model) stands
    // on the floor at its height: the visitor climbs the treads a resident does.
    // (to the grid's tenth of a metre: a way's point at a riser stands on one tread or the other)
    const near = (u, v, y) => [[0, 0], [0.1, 0], [-0.1, 0], [0, 0.1], [0, -0.1]]
      .some(([du, dv]) => { const q = enuOf(pl, u + du, v + dv); return Math.abs(w.surfaceAt(q.e, q.n) - y) <= 0.06; });
    const off = way.filter(([u, v, y]) => y !== null && !near(u, v, y));
    ok(!off.length, `${row.structure}: the way up its stoop stands on its floor (${off.slice(0, 2).map((p) => p.join(' ')).join('; ')})`);
    // From out on the walk, up the way, to the door.
    const out = enuOf(pl, way[0][0] + 1.0, way[0][1]);
    const leaf = enuOf(pl, door.plan.origin[0], door.plan.origin[1]);
    const ys = walkTo(w, out, way.map(([u, v]) => enuOf(pl, u, v)));
    const jumps = ys.slice(1).map((y, i) => y - ys[i]);
    const reach = Math.hypot(w.state.e - leaf.e, w.state.n - leaf.n);
    const up = Math.abs(w.state.groundY - sill) < 0.06;
    ok(up && reach < 0.8, `${row.structure}: the walker climbs its stoop to the door (stands at ${w.state.groundY.toFixed(2)} of ${sill}, ${reach.toFixed(2)} m from the leaf)`);
    ok(Math.max(...jumps) <= WALK.stepUp + 1e-6, `${row.structure}: a tread at a time (largest rise ${Math.max(...jumps).toFixed(2)})`);
    if (up && reach < 0.8) climbed++;
    // Across the flight from its side, at mid-flight: a rail, a cheek or the stoop's own side turns one back.
    const k = Math.floor(way.length / 2);
    const mid = way[k], a = way[Math.max(0, k - 1)], b = way[Math.min(way.length - 1, k + 1)];
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (mid[2] !== null && mid[2] > 0.6 && L > 1e-6) {
      const [pu, pv] = [-(b[1] - a[1]) / L, (b[0] - a[0]) / L];
      const ys2 = walkTo(w, enuOf(pl, mid[0] + pu * 4, mid[1] + pv * 4), enuOf(pl, mid[0] - pu * 4, mid[1] - pv * 4), 8);
      const highest = Math.max(...ys2);
      ok(highest <= WALK.stepUp + 0.05, `${row.structure}: walking at the flight from its side, one is turned back (stood at ${highest.toFixed(2)})`);
      if (highest <= WALK.stepUp + 0.05) walled++;
    }
  }
  ok(climbed >= 50, `the walker climbs the hung front doors' stoops (${climbed})`);
}

// 3. The back yards: every back stoop climbed from the yard to its landing.
let backs = 0;
{
  const doc = read('../data/back_yards/1904.json');
  const by = await import('../renderers/web/js/back-yards.js');
  globalThis.OffscreenCanvas ??= class {
    constructor(w, h) { this.width = w; this.height = h; }
    getContext() {
      const noop = () => {};
      return new Proxy({}, { get: (_, k) => (k === 'getImageData' ? (x, y, w, h) => ({ data: new Uint8ClampedArray(w * h * 4) })
        : k === 'createLinearGradient' || k === 'createRadialGradient' ? () => ({ addColorStop: noop }) : noop), set: () => true });
    }
  };
  const terrain = { surfaceHeight: () => 0, walkHeight: () => 0, isWater: () => false, grid: { cellM: 2.5, originE: 0, originN: 0 } };
  const yards = await by.createBackYards({ doc, terrain, problems: [], confidence: { patch() {} } });
  const decks = yards.stairDecks;
  const stoops = decks.filter((d) => d.id.endsWith(':stoop'));
  ok(stoops.length >= 100, `the back yards' stoops are decks (${stoops.length})`);
  const surface = stairSurface(decks);
  const w = walkerFor(null, surface);
  const doors = doc.lots.flatMap((l) => l.doors ?? []).filter((d) => d.stoop && Number.isFinite(d.e));
  for (const d of doors) {
    const deck = stoops.find((x) => x.id === `${d.id}:stoop`);
    if (!deck) continue;
    const f = by.frameAt(d.e, d.n, d.facing_deg ?? 0);
    const [ie, inn] = f.plan(0.4, 0);
    const top = deck.heightAt(ie, inn);
    const [fe, fn] = f.plan(6, 0);
    const ys = walkTo(w, { e: fe, n: fn }, { e: ie, n: inn }, 10);
    const jumps = ys.slice(1).map((y, i) => y - ys[i]);
    ok(Math.abs(w.state.groundY - top) < 0.02, `${d.id}: the walker climbs its back stoop to the landing (${w.state.groundY.toFixed(2)} of ${top?.toFixed(2)})`);
    ok(Math.max(...jumps) <= WALK.stepUp + 1e-6, `${d.id}: a tread at a time`);
    backs++;
    for (const rail of decks.filter((x) => x.wall && x.id.startsWith(`${d.id}:rail`))) {
      ok(rail.y - top > WALK.stepUp, `${rail.id}: a rail stands past any step`);
    }
  }
  yards.dispose?.();
}

// 4. Knocking from the top of the steps (interact.js `spots`, human-days.js door things): a door
//    whose place is the foot of its stoop is worked from its landing too, and not from far off.
{
  const { createInteractions } = await import('../renderers/web/js/interact.js');
  const { DOOR_REACH_M } = await import('../renderers/web/js/human-days.js');
  const it = createInteractions();
  const foot = [0, 0], landing = [0, 5];
  it.add({ id: 'door:x', kind: 'door', name: 'x', states: ['shut'], state: 'shut', at: foot, spots: [[0, 1], [0, 3], landing],
    reach: DOOR_REACH_M, actions: { shut: [{ id: 'knock', label: 'Knock', steps: [] }] } });
  ok(it.nearest(0, 5.4, 0)?.id === 'door:x', 'a door is knocked at from its landing, past its reach of the foot of the steps');
  ok(it.nearest(0, -1, 0)?.id === 'door:x', '... and from the foot of the steps, as before');
  ok(it.nearest(5, 9, 0) === null, '... and not from far off');
}

if (fails.length) {
  console.error(`test_house_floors: FAIL (${fails.length} of ${checks})`);
  for (const f of fails.slice(0, 40)) console.error(`  - ${f}`);
  process.exit(1);
}
console.log(`test_house_floors: PASS (${checks} checks; ${houses} house floors in ${rects} rectangles, ${climbed} front stoops climbed, `
  + `${walled} turned back at the side, ${backs} back stoops climbed)`);
