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
const { createFortGates, stockadePlan, drawsLeaves, leafDirections, wicketGeometry, FORT_GATES, SWING_S } = await import('../renderers/web/js/fort-gates.js');
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
    ok(layer.gates.length === 2, 'the main gate in each picket row');
    // On Whistler's passage: square in the gap between the two halves of the south range.
    const sw = footprints.find((f) => f.id === 'first_fort_dearborn_soldiers_barracks_sw').pts;
    const se = footprints.find((f) => f.id === 'first_fort_dearborn_soldiers_barracks_se').pts;
    const gapMid = (Math.max(...sw.map((p) => p[0])) + Math.min(...se.map((p) => p[0]))) / 2;
    for (const g of layer.gates) {
      ok(Math.abs(g.at[0] - gapMid) < 0.06, `${g.name} stands in the barracks' gap (${g.at[0].toFixed(2)} vs ${gapMid.toFixed(2)})`);
    }
    const outer = layer.gates.find((g) => g.id.includes('outer'));
    const inner = layer.gates.find((g) => g.id.includes('inner'));
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
