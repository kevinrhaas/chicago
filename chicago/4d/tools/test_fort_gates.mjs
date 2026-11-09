#!/usr/bin/env node
/**
 * T-3319 — a visitor walks into Fort Dearborn through a gate the Interact key opens.
 *
 * On flat ground, with the real 1835 and 1812 sidecars:
 *   - the interaction engine: a two-state thing starts, swings and lands in its new state
 *     once; a step with a prompt waits for the next press; a press mid-swing does nothing;
 *   - each stockade's walls are what palisade.py builds (the 1812 gates now on Whistler's
 *     passage, square in the gap between the two halves of the south range);
 *   - walking at a shut gate stops outside it; opened, the walk goes through onto the
 *     parade (no longer a solid block) and the buildings inside still stop it; the curtain
 *     stops it everywhere else; and a gate shut on someone standing in it puts them out
 *     on the side they were on;
 *   - the Interact key offers the nearest gate in reach, on foot only, and R presses it;
 *   - T-3407: the 1812 commanding officer's garden has one wicket leaf on its north side;
 *     shut, it keeps a walker out; opened, the walk goes in onto the garden's walks, and
 *     the paling holds everywhere else.
 *
 *   node tools/test_fort_gates.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker, footprintsFrom, WALK, segmentsCross } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const { createFortGates, stockadePlan, drawsLeaves, leafDirections, wicketGeometry, FORT_GATES, SWING_S, gatesOnRoute } = await import('../renderers/web/js/fort-gates.js');
const { createRouter } = await import('../renderers/web/js/route.js');
const { createTravel } = await import('../renderers/web/js/travel.js');
const { createInteractions, createInteractKey, INTERACT_KEY } = await import('../renderers/web/js/interact.js');

const ROOT = new URL('../', import.meta.url);
const flat = { walkHeight: () => 0, surfaceHeight: () => 0, isWater: () => false };
const inside = (e, n, pts) => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };

// ---------------------------------------------------------------- the engine
{
  const seen = [];
  const ix = createInteractions({ onChange: (t, ev) => seen.push(ev) });
  let swing = 0;
  const lever = ix.add({ id: 'x', name: 'Lever', states: ['down', 'up'], state: 'down', at: [0, 0], reach: 3,
    actions: { down: [{ id: 'raise', label: 'Raise', to: 'up', steps: [{ label: 'Raising', seconds: 1, run: (t) => { swing = t; } }] }],
      up: [{ id: 'lower', label: 'Lower', to: 'down', steps: [
        { label: 'Unlatching', prompt: 'Lift the latch', seconds: 0 },
        { label: 'Lowering', seconds: 0.5, run: (t) => { swing = 1 - t; } }] }] } });
  ok(ix.offer(lever).label === 'Raise', 'a resting thing offers its first action');
  ok(ix.act('x').ok && lever.running && lever.state === 'down', 'a press starts the sequence; the state waits for its end');
  ok(ix.offer(lever).busy && ix.offer(lever).label === 'Raising…', 'mid-swing the key reads the step, busy');
  ok(!ix.act('x').ok, 'a press mid-swing does nothing');
  ix.update(0.5); ok(Math.abs(swing - 0.5) < 1e-9 && lever.state === 'down', 'half a second is half the swing');
  ix.update(0.6); ok(!lever.running && lever.state === 'up' && swing === 1, 'the swing ends in the new state, once');
  ok(ix.act('x').ok && lever.running.waiting && ix.offer(lever).label === 'Lift the latch', 'a prompt step waits and the key reads its prompt');
  ix.update(5); ok(lever.running?.waiting, 'a waiting step does not run on time alone');
  ok(ix.act('x').ok, 'the next press lets it go'); ix.update(0); ix.update(0.5);
  ok(lever.state === 'down' && swing === 0, 'then the rest of the sequence runs to its end');
  ok(seen.filter((e) => e === 'done').length === 2, 'two sequences, two endings');
  assert.throws(() => ix.add({ id: 'bad', states: ['a'], state: 'b' }), 'a thing must be in one of its states');
  ok(ix.nearest(2, 0)?.id === 'x' && ix.nearest(4, 0) === null, 'in reach is within reach, not beyond');
}

// ---------------------------------------------------------------- the real forts
// T-3405: a walking ride from `from` to `to` through the fort's gates, on the walker.
function rideIn(year, footprints, layer, ix, router, from, to) {
  const camera = new THREE.PerspectiveCamera();
  const walker = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: from.e, local_n: from.n, yaw_deg: 0 } });
  const intent = createIntent();
  let arrivals = 0, stops = 0, waited = 0;
  const travel = createTravel({ walker, intent, router, terrain: flat,
    gates: { along: (pts) => gatesOnRoute(layer.gates, pts).map((g) => ({ at: g.at,
      blocks: () => !(g.state === 'open' && !g.running), open: () => { if (g.state !== 'open' && !g.running) ix.act(g, 'open'); } })) },
    tickWorld: (dt) => ix.update(dt) });
  travel.setMode('walk');
  const through = gatesOnRoute(layer.gates, router.plan(from, to, { mode: 'walk' })?.points ?? []);
  ok(through.length > 0 && through.every((g) => g.state === 'closed'), `${year}: the walk's gates start shut (${through.map((g) => g.id).join()})`);
  ok(travel.go({ kind: 'anchor', id: 'in', local_e: to.e, local_n: to.n, yaw_deg: 0 },
    { token: {}, onArrive: () => arrivals++, onStop: () => stops++ }), `${year}: the walk sets off`);
  for (let i = 0; i < 3000 && travel.state.phase !== 'idle'; i++) {
    const before = [walker.state.e, walker.state.n];
    ix.update(1 / 30);
    travel.update(1 / 30, intent); walker.update(1 / 30, intent); travel.afterWalk(intent, 1 / 30);
    if (Math.hypot(walker.state.e - before[0], walker.state.n - before[1]) < 1e-4 && travel.state.phase === 'travelling') waited++;
  }
  ok(arrivals === 1 && stops === 0, `${year}: the walk arrives inside (arrivals ${arrivals}, stops ${stops})`);
  ok(Math.hypot(walker.state.e - to.e, walker.state.n - to.n) < 0.2, `${year}: where it was sent (${walker.state.e.toFixed(1)}, ${walker.state.n.toFixed(1)})`);
  ok(through.every((g) => g.state === 'open'), `${year}: it opened the gates on the way`);
  ok(waited > 0, `${year}: and waited for the leaves to swing`);
}

function registryOf(year, match) {
  const dir = new URL(`data/sidecars/${year}/`, ROOT);
  const reg = new Map();
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.json') || !match.test(f)) continue;
    const sidecar = JSON.parse(fs.readFileSync(new URL(f, dir), 'utf8'));
    reg.set(sidecar.id, { id: sidecar.id, sidecar });
  }
  return reg;
}
const identity = { matrixOf: () => new THREE.Matrix4() };
function fort(year, match = null) {
  const registry = registryOf(year, match ?? (year === '1835' ? /^fort_dearborn_/ : /^first_fort_dearborn_/));
  const footprints = footprintsFrom(registry);
  const problems = [];
  const layer = createFortGates({ registry, buildings: identity, footprints, problems });
  const ix = createInteractions();
  for (const g of layer.gates) ix.add(g);
  return { registry, footprints, layer, ix, problems };
}
function walkFrom(footprints, from, yawDeg, seconds, { ix = null } = {}) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: from[0], local_n: from[1], yaw_deg: yawDeg } });
  const intent = createIntent();
  const path = [];
  for (let i = 0; i < seconds * 60; i++) {
    intent.forward = 1;
    ix?.update(1 / 60);
    w.update(1 / 60, intent);
    path.push([w.state.e, w.state.n]);
  }
  return { w, path, end: path.at(-1) };
}
const openAll = (ix, ids = null) => {
  for (const t of ix.list) if (!ids || ids.includes(t.id)) ix.act(t.id);
  ix.update(SWING_S + 0.1);
};
/** A gate's middle and its inward normal in ENU, from the layer's own record. */
const gateAt = (thing, plan, sidecar) => {
  const g = plan.gates.find((x) => `${sidecar.id}:${x.side}` === thing.id);
  const th = (sidecar.placement.rotation_deg ?? 0) * Math.PI / 180;
  const rot = ([u, v]) => [u * Math.cos(th) + v * Math.sin(th), -u * Math.sin(th) + v * Math.cos(th)];
  return { at: thing.at, inward: rot(g.inward) };
};
const speedWas = WALK.speed;
WALK.speed = 1.5;
try {
  // ---- 1835: the second fort, its north and south gates
  {
    const { registry, footprints, layer, ix, problems } = fort('1835');
    ok(problems.length === 0, `1835 hangs its gates without complaint: ${problems.join('; ')}`);
    ok(layer.gates.map((g) => g.id).sort().join() === 'fort_dearborn_palisade:n,fort_dearborn_palisade:s', 'the 1835 stockade has its two gates, north and south');
    ok(layer.gates.every((g) => g.state === 'closed'), 'every gate starts shut');
    ok(drawsLeaves(registry.get('fort_dearborn_palisade')) && !drawsLeaves(registry.get('fort_dearborn_parade')), 'only the stockade gives up its baked leaves');
    const pal = registry.get('fort_dearborn_palisade').sidecar;
    const plan = stockadePlan(pal);
    ok(plan.walls.length === 4 + 2 * 1 + 2 * 4, `curtain in six runs (two gates, two bastion corners) plus two bastions of four returns: ${plan.walls.length}`);
    const fpPal = footprints.find((f) => f.id === 'fort_dearborn_palisade');
    const fpParade = footprints.find((f) => f.id === 'fort_dearborn_parade');
    ok(Array.isArray(fpPal.walls) && fpParade.ground === true, 'the stockade is walls and the parade is ground');
    const south = layer.gates.find((g) => g.id.endsWith(':s'));
    const { at, inward } = gateAt(south, plan, pal);
    const start = [at[0] - inward[0] * 6, at[1] - inward[1] * 6];
    const yaw = (Math.atan2(inward[0], inward[1]) * 180 / Math.PI + 360) % 360;

    const shut = walkFrom(footprints, start, yaw, 8);
    const d = (p) => (p[0] - at[0]) * inward[0] + (p[1] - at[1]) * inward[1];
    ok(d(shut.end) < -WALK.radius + 0.01, `at the shut south gate the walk stops outside it (${d(shut.end).toFixed(2)} m)`);
    ok(shut.path.every((p) => d(p) < 0), 'and never passes it');

    openAll(ix, [south.id]);
    ok(south.state === 'open', 'Interact opens it');
    const through = walkFrom(footprints, start, yaw, 7);
    ok(d(through.end) > 3, `opened, the walk goes through (${d(through.end).toFixed(2)} m in)`);
    ok(inside(through.end[0], through.end[1], fpPal.pts), 'and ends inside the fort');
    // Strafing round the parade and on: the guard house and store house still stop it.
    for (const id of ['fort_dearborn_guard_house', 'fort_dearborn_store_house', 'fort_dearborn_barracks']) {
      const fp = footprints.find((f) => f.id === id);
      ok(!through.path.some((p) => inside(p[0], p[1], fp.pts)), `never inside ${id}`);
    }
    // Walk on north across the parade to the far wall: the parade does not stop it,
    // the curtain does — and the north gate, shut, holds.
    // The south gate stands at the middle of its wall and the guard house's corner
    // reaches 1.9 m across its west half 4.7 m in, so the way on is past that corner,
    // between it and the store house (Hubbard: "on either side of the southern gate").
    const sidle = walkFrom(footprints, through.end, (yaw + 90) % 360, 1.0);
    const across = walkFrom(footprints, sidle.end, yaw, 40);
    ok(inside(across.end[0], across.end[1], fpPal.pts), `across the parade the walk stays in the fort (${across.end.map((x) => x.toFixed(1))})`);
    ok(d(across.end) > 20, `and gets well past the parade's south edge (${d(across.end).toFixed(1)} m in)`);
    // Into the west curtain from inside: held off it, never out.
    const west = walkFrom(footprints, [fpPal.pts[0][0] + 6 * Math.cos(8 * Math.PI / 180) + 20 * Math.sin(8 * Math.PI / 180), fpPal.pts[0][1] + 20], 278, 10);
    ok(inside(west.end[0], west.end[1], fpPal.pts), 'walking into the west curtain from inside stops at it');
    // A gate shut on someone standing in it puts them out on the side they were on.
    const camera = new THREE.PerspectiveCamera();
    const mid = [at[0] + inward[0] * 0.05, at[1] + inward[1] * 0.05];
    const w = createWalker({ camera, terrain: flat, footprints, spawn: { local_e: mid[0], local_n: mid[1], yaw_deg: yaw } });
    ix.act(south.id); ix.update(SWING_S + 0.1);
    ok(south.state === 'closed', 'Interact shuts it again');
    const intent = createIntent(); w.update(1 / 60, intent);
    ok(d([w.state.e, w.state.n]) >= WALK.radius + 0.05, `shut on a visitor in the gateway, it puts them inside, where they stood (${d([w.state.e, w.state.n]).toFixed(2)})`);
    // The leaves swing inward: open, each one's free end is inside the wall line.
    const g = plan.gates.find((x) => x.side === 's');
    for (const { hinge, dir } of leafDirections(g, 1)) {
      ok(Math.abs(dir[0] - g.inward[0]) < 1e-9 && Math.abs(dir[1] - g.inward[1]) < 1e-9, 'open, a leaf stands square into the fort');
      ok(Math.abs(Math.abs(hinge[0] - g.centre[0]) - g.half) < 1e-9, 'hung on its jamb');
    }
  }

  // ---- 1812: the first fort, its main gate through both picket rows
  {
    const { registry, footprints, layer, ix, problems } = fort('1812');
    ok(problems.length === 0, `1812 hangs its gates without complaint: ${problems.join('; ')}`);
    ok(layer.gates.length === 4, 'a main gate and west wicket in each picket row');
    // On Whistler's passage: square in the gap between the two halves of the south range.
    const sw = footprints.find((f) => f.id === 'first_fort_dearborn_soldiers_barracks_sw').pts;
    const se = footprints.find((f) => f.id === 'first_fort_dearborn_soldiers_barracks_se').pts;
    const gapMid = (Math.max(...sw.map((p) => p[0])) + Math.min(...se.map((p) => p[0]))) / 2;
    for (const g of layer.gates.filter((gate) => gate.id.endsWith(':s'))) {
      ok(Math.abs(g.at[0] - gapMid) < 0.06, `${g.name} stands in the barracks' gap (${g.at[0].toFixed(2)} vs ${gapMid.toFixed(2)})`);
    }
    const outer = layer.gates.find((g) => g.id.includes('outer') && g.id.endsWith(':s'));
    const inner = layer.gates.find((g) => g.id.includes('inner') && g.id.endsWith(':s'));
    const start = [outer.at[0], outer.at[1] - 6];
    const fpIn = footprints.find((f) => f.id === 'first_fort_dearborn_pickets_inner');
    const fpOut = footprints.find((f) => f.id === 'first_fort_dearborn_pickets_outer');

    const shut = walkFrom(footprints, start, 0, 6);
    ok(shut.end[1] < outer.at[1] - WALK.radius + 0.01, `both shut: stopped outside the outer row (${(shut.end[1] - outer.at[1]).toFixed(2)})`);
    openAll(ix, [outer.id]);
    const between = walkFrom(footprints, start, 0, 8);
    ok(between.end[1] > outer.at[1] + 0.3 && between.end[1] < inner.at[1] - WALK.radius + 0.01,
      `outer open, inner shut: between the rows (${between.end[1].toFixed(2)}, rows at ${outer.at[1].toFixed(2)} / ${inner.at[1].toFixed(2)})`);
    openAll(ix, [inner.id]);
    const into = walkFrom(footprints, start, 0, 16);
    ok(inside(into.end[0], into.end[1], fpIn.pts) && into.end[1] > inner.at[1] + 5, `both open: onto the parade (${into.end.map((x) => x.toFixed(1))})`);
    for (const id of ['first_fort_dearborn_soldiers_barracks_sw', 'first_fort_dearborn_soldiers_barracks_se']) {
      const fp = footprints.find((f) => f.id === id);
      ok(!into.path.some((p) => inside(p[0], p[1], fp.pts)), `through the passage, never inside ${id}`);
    }
    ok(inside(into.end[0], into.end[1], fpOut.pts), 'inside both rows');
  }

  // ---- T-3041: independent west wickets beside the northwest blockhouse.
  {
    const { registry, footprints, layer, ix, problems } = fort('1812');
    ok(problems.length === 0, `the west wickets hang without complaint: ${problems.join('; ')}`);
    const outer = layer.gates.find((g) => g.id.includes('outer') && g.id.endsWith(':w'));
    const inner = layer.gates.find((g) => g.id.includes('inner') && g.id.endsWith(':w'));
    ok(outer && inner && Math.abs(outer.at[1] - inner.at[1]) < 0.001, 'both west cuts align across the two rows');
    const fpIn = footprints.find((f) => f.id === 'first_fort_dearborn_pickets_inner');
    const block = footprints.find((f) => f.id === 'first_fort_dearborn_blockhouse_nw');
    const range = footprints.find((f) => f.id === 'first_fort_dearborn_officers_barracks');
    ok(inner.at[1] + 0.75 < Math.min(...block.pts.map((p) => p[1])), 'the west opening is south of the northwest blockhouse');
    ok(inner.at[1] - 0.75 > Math.max(...range.pts.map((p) => p[1])), 'and north of the existing west range');
    for (const row of ['inner', 'outer']) {
      const sc = registry.get(`first_fort_dearborn_pickets_${row}`).sidecar;
      const plan = stockadePlan(sc), west = plan.gates.find((g) => g.side === 'w');
      const south = plan.gates.find((g) => g.side === 's');
      ok(west.kind === 'wicket' && leafDirections(west, 0).length === 1, `${row}: one west wicket leaf`);
      ok(Math.abs(2 * west.half - 1.18) < 1e-9 && west.confidence === 1, `${row}: reconstructed clear span is 1.18 m`);
      ok(south.kind === 'gateway' && leafDirections(south, 0).length === 2 && south.confidence === (row === 'inner' ? 0 : 0.5),
        `${row}: the source-supported south gate keeps its two leaves and occurrence grade`);
      const meshes = [];
      layer.group.traverse((mesh) => { if (mesh.isMesh && mesh.userData.structure_id === sc.id) meshes.push(mesh); });
      for (const [side, grade] of [['w', 1], ['s', row === 'inner' ? 0 : 0.5]]) {
        const leaves = meshes.filter((mesh) => mesh.name.endsWith(`:${side}`));
        ok(leaves.length === (side === 'w' ? 1 : 2)
          && leaves.every((mesh) => [...mesh.geometry.getAttribute('_confidence').array].every((c) => c === grade)),
        `${row}: actual ${side} leaf vertices retain the applicable confidence`);
      }
    }
    const start = [outer.at[0] - 6, outer.at[1]];
    const shut = walkFrom(footprints, start, 90, 8);
    ok(shut.end[0] < outer.at[0] - WALK.radius + 0.01, 'west, both shut: stopped outside the outer row');
    openAll(ix, [inner.id]);
    const innerOnly = walkFrom(footprints, start, 90, 8);
    ok(innerOnly.end[0] < outer.at[0] - WALK.radius + 0.01, 'west, inner only open: outer leaf still holds');
    openAll(ix, [inner.id, outer.id]); // close inner, open outer
    const between = walkFrom(footprints, start, 90, 8);
    ok(between.end[0] > outer.at[0] + 0.3 && between.end[0] < inner.at[0] - WALK.radius + 0.01,
      'west, outer only open: stopped between the rows');
    openAll(ix, [inner.id]);
    const through = walkFrom(footprints, start, 90, 10);
    ok(inside(through.end[0], through.end[1], fpIn.pts) && through.end[0] > inner.at[0] + 3,
      'west, both open: a visitor walks into the fort');
    for (const fp of [block, range]) {
      ok(!through.path.some((p) => inside(p[0], p[1], fp.pts)), `west passage never enters ${fp.id}`);
    }
    // At a point outside the wicket, the west curtain continues to hold.
    const beside = walkFrom(footprints, [start[0], start[1] - 2], 90, 8);
    ok(beside.end[0] < outer.at[0] - WALK.radius + 0.01, 'opening the wicket leaves the adjacent curtain solid');
    const intoLeaf = walkFrom(footprints, [outer.at[0] + 0.8, outer.at[1] + 1.8], 180, 3);
    ok(intoLeaf.end[1] > outer.at[1] - 0.75, 'an open west leaf remains solid to a visitor crossing its swing');
  }

  // ---- 1812: the commanding officer's garden, its wicket on the walk from the fort (T-3407)
  {
    const { registry, footprints, layer, ix, problems } = fort('1812', /^first_fort_outer_officers_garden\.json$/);
    ok(problems.length === 0, `the garden hangs its gate without complaint: ${problems.join('; ')}`);
    ok(layer.gates.length === 1 && layer.gates[0].name === 'Garden gate', 'the garden has one gate, on its north side');
    const sc = registry.get('first_fort_outer_officers_garden').sidecar;
    const plan = stockadePlan(sc);
    const g = plan.gates[0];
    ok(g.kind === 'wicket' && g.side === 'n', 'a wicket in the north paling');
    ok(Math.abs(g.centre[0] - plan.w / 2) < 1e-9, 'at the middle of the north side, where the draught brings the walk in');
    const legs = leafDirections(g, 0);
    ok(legs.length === 1 && Math.abs(legs[0].len - 2 * g.half) < 1e-9, 'one leaf, closing the whole way between the posts');
    const open = leafDirections(g, 1)[0];
    ok(open.dir[0] * g.inward[0] + open.dir[1] * g.inward[1] > 0.9, 'it swings inward, into the garden');
    const geo = wicketGeometry({ len: 1.18, foot: g.foot, head: g.head, pale: g.pale });
    ok(geo.getAttribute('uv') && geo.getAttribute('position').count > 300, 'its leaf is pales, rails and a brace, grained');
    const fp = footprints.find((f) => f.id === 'first_fort_outer_officers_garden');
    ok(Array.isArray(fp.walls), 'the garden is its paling, not a solid block');
    const gate = layer.gates[0];
    const start = [gate.at[0], gate.at[1] + 5];             // on the walk north of it, facing south
    const shut = walkFrom(footprints, start, 180, 6);
    ok(shut.end[1] > gate.at[1] + WALK.radius - 0.01, `shut, the walk stops outside the garden (${(shut.end[1] - gate.at[1]).toFixed(2)} m)`);
    openAll(ix, [gate.id]);
    ok(gate.state === 'open', 'Interact opens it');
    const into = walkFrom(footprints, start, 180, 10);
    ok(inside(into.end[0], into.end[1], fp.pts) && into.end[1] < gate.at[1] - 4, `opened, the walk goes in (${(gate.at[1] - into.end[1]).toFixed(1)} m in)`);
    const east = walkFrom(footprints, into.end, 90, 40);
    ok(inside(east.end[0], east.end[1], fp.pts), 'and walking on east, the paling holds');
  }

  // ---- T-3405: a WALKING RIDE (Go to, a jaunt on Walk) goes in through the gates: the
  // planner reads the stockade as its walls with the gateways open and the parade as
  // ground, holds the route to each gateway's middle, and the ride opens each shut gate
  // as it comes up to it and waits while it swings.
  {
    const { footprints, layer, ix } = fort('1812');
    const router = createRouter({ terrain: { ...flat, heightfield: { loaded: true, originE: 1050, originN: 120, widthM: 200, depthM: 160 } },
      footprints, cell: 1, inflate: 0.1 });
    const from = { e: 1148.5, n: 190 }, parade = { e: 1146, n: 220 };
    const route = router.plan(from, parade, { mode: 'walk' });
    ok(route?.points?.length, 'a walk is planned from outside the fort onto the parade');
    const order = gatesOnRoute(layer.gates, route.points).map((g) => g.id);
    ok(order.join() === 'first_fort_dearborn_pickets_outer:s,first_fort_dearborn_pickets_inner:s', `through the outer gate, then the inner (${order.join()})`);
    for (const g of layer.gates.filter((gate) => gate.id.endsWith(':s'))) {
      ok(route.points.some(([e, n]) => Math.abs(e - g.at[0]) < 0.01 && Math.abs(n - (g.at[1] - 1.5)) < 0.01)
        && route.points.some(([e, n]) => Math.abs(e - g.at[0]) < 0.01 && Math.abs(n - (g.at[1] + 1.5)) < 0.01),
      `${g.name}: the route is held to the gateway's middle, square to it`);
    }
    ok(router.plan({ e: 1146, n: 214 }, { e: 1157, n: 218 }, { mode: 'walk' })?.points.length, 'across the parade, which is ground, not a block');
    const round = router.plan({ e: 1120, n: 220 }, { e: 1180, n: 220 }, { mode: 'walk' });
    ok(round && round.length_m > 70 && gatesOnRoute(layer.gates, round.points).length === 0, `past the fort a walk goes round it, not through (${round?.length_m.toFixed(0)} m)`);

    rideIn('1812', footprints, layer, ix, router, from, parade);
  }

  // The separate western approach crosses its two wickets, not the south gateway.
  {
    const { footprints, layer, ix } = fort('1812');
    const router = createRouter({ terrain: { ...flat, heightfield: { loaded: true, originE: 1050, originN: 120, widthM: 200, depthM: 160 } },
      footprints, cell: 1, inflate: 0.1 });
    const outer = layer.gates.find((g) => g.id.includes('outer') && g.id.endsWith(':w'));
    const inner = layer.gates.find((g) => g.id.includes('inner') && g.id.endsWith(':w'));
    const from = { e: outer.at[0] - 6, n: outer.at[1] }, to = { e: inner.at[0] + 4, n: inner.at[1] };
    const route = router.plan(from, to, { mode: 'walk' });
    ok(route?.points?.length, 'a walking ride is planned through the western approach');
    ok(gatesOnRoute(layer.gates, route.points).map((g) => g.id).join()
      === 'first_fort_dearborn_pickets_outer:w,first_fort_dearborn_pickets_inner:w',
    'the western route crosses the outer and inner wickets in order');
    rideIn('1812 west', footprints, layer, ix, router, from, to);
  }

  // ---- T-3405, 1835: in by the south gate, past the guard house's corner, onto the parade.
  {
    const { footprints, layer, ix } = fort('1835');
    const router = createRouter({ terrain: { ...flat, heightfield: { loaded: true, originE: 1000, originN: 20, widthM: 260, depthM: 260 } },
      footprints, cell: 1, inflate: 0.1 });
    const south = layer.gates.find((g) => g.id.endsWith(':s'));
    rideIn('1835', footprints, layer, ix, router, { e: south.at[0], n: south.at[1] - 8 }, { e: 1151, n: 212 });
  }

  // ---- the walls' own rule: a segment crossing
  ok(segmentsCross([0, -1], [0, 1], [-1, 0], [1, 0]) && !segmentsCross([0, 1], [0, 2], [-1, 0], [1, 0]), 'crossing is crossing');

  // ---- the key: on foot, in reach, R presses it
  {
    const { layer, ix } = fort('1835');
    const south = layer.gates.find((g) => g.id.endsWith(':s'));
    const listeners = {};
    const keys = { addEventListener: (t, fn) => { listeners[t] = fn; }, removeEventListener: () => {} };
    const keyEl = { hidden: true, dataset: {}, attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener() {}, removeEventListener() {} };
    let here = { e: south.at[0], n: south.at[1] - 3, bearing: 8, flying: false };
    const said = [];
    const key = createInteractKey({ interactions: ix, keyEl, where: () => here, say: (t) => said.push(t), keys });
    key.refresh();
    ok(!keyEl.hidden && keyEl.textContent === 'Open gate' && key.current === south, 'in reach of the south gate the key offers to open it');
    here = { ...here, flying: true }; key.refresh();
    ok(keyEl.hidden, 'flying, there is nothing to work');
    here = { ...here, flying: false, n: south.at[1] - 9 }; key.refresh();
    ok(keyEl.hidden, 'out of reach, the key goes');
    here = { ...here, n: south.at[1] - 2 };
    let prevented = false;
    listeners.keydown({ code: INTERACT_KEY, target: null, preventDefault: () => { prevented = true; } });
    ok(prevented && south.running, 'R presses it');
    ok(keyEl.textContent === 'Opening…' && keyEl.attrs['aria-disabled'] === 'true', 'mid-swing it reads Opening…');
    ix.update(SWING_S + 0.1);
    ok(south.state === 'open' && keyEl.textContent === 'Close gate', 'open, it offers to close');
    ok(said.at(-1) === 'South gate open', `and the status line says so (${said.at(-1)})`);
  }
  ok(Object.keys(FORT_GATES).length === 4, 'three stockades and the officers\' garden carry gates a visitor works');
} finally {
  WALK.speed = speedWas;
}
console.log(`test_fort_gates: PASS (${checks} checks)`);
