#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3524 — Glessner's court service door and its Eighteenth Street side door open and shut as
 * people pass, and people climb and come down the stairs to them instead of vanishing at the
 * foot (house-doors.js § passages, human-days.js § doors that open).
 *
 * The owner, 2026-11-08: "when people enter the glessner house from the rear they just kind of
 * disappear at the staircase i think the door should work and the stairs and they should come
 * up and down the stairs".
 *
 * With the real 1904 Glessner record and data/humans/doors_1904.json:
 *   - each passage's plan is the door the model draws: jambs, sill and head off the record, its
 *     leaf box round the oak leaf and iron latch measured off the master GLB, hung on the jamb
 *     away from the latch;
 *   - the way up each stair: from open ground outside, every tread the generator lays at its
 *     own height in order (ten up the court flight, three front steps and eight up the alcove
 *     stair), rising only at its risers and never falling on the way in, onto the sill and
 *     through the leaf;
 *   - the layer: a held door swings open in PASSAGE_SWING_S and shuts once let go, and stays
 *     open while anyone still holds it;
 *   - a day: someone going in walks to the foot, up every tread (their feet at each height),
 *     waits at the door till it is open, goes through, is indoors only past the leaf, and the
 *     door shuts behind them; coming out it opens before they are seen to move, they come down
 *     to the ground, and it shuts once they are clear; two at once go one behind the other and
 *     never meet on the stair; asked for at the door, they come down it.
 *
 *   node tools/test_house_passages.mjs
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
const { enuToWorld } = await import('../renderers/web/js/terrain.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { glessnerCourtPlan, glessnerNorthEntryPlan, passagePlan, leafBox, takeDoorLeaf, doorLeafMaterial, createHouseDoors,
  PASSAGE_SWING_S } = await import('../renderers/web/js/house-doors.js');
const { createHumanDays, PASSAGE } = await import('../renderers/web/js/human-days.js');
const { createInteractions } = await import('../renderers/web/js/interact.js');

const ROOT = new URL('../', import.meta.url);
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const sidecar = JSON.parse(fs.readFileSync(new URL('data/sidecars/1904/glessner_house.json', ROOT), 'utf8'));
const doors = JSON.parse(fs.readFileSync(new URL('data/humans/doors_1904.json', ROOT), 'utf8'));
const BASE = 4.33;

// ---------------------------------------------------------------- the plans are the model's doors
// Measured off assets/gltf/glessner_house__as_built_1887.glb (glTF metres: x = u, z = -v): the
// court door's oak leaf x 17.49-18.63, y 1.91-4.44, v 14.56-14.65, its iron latch x 18.45-18.49;
// the side door's oak x 20.83-20.92, y 1.91-4.14, v 21.01-21.97, its latch v 21.79-21.83.
const MEASURED = {
  'glessner_house:service_stair': { oak: { x: [17.49, 18.63], y: [1.91, 4.44], v: [14.56, 14.65] }, iron: { x: [18.45, 18.49], v: [14.53, 14.56] }, hinge: 'left' },
  'glessner_house:north_entry': { oak: { x: [20.83, 20.92], y: [1.91, 4.14], v: [21.01, 21.97] }, iron: { x: [20.80, 20.83], v: [21.79, 21.83] }, hinge: 'right' },
};
const plans = [glessnerCourtPlan(sidecar), glessnerNorthEntryPlan(sidecar)];
ok(plans.every(Boolean), 'the record carries both passages');
for (const plan of plans) {
  const m = MEASURED[plan.id];
  ok(m, `${plan.id} is a door of doors_1904.json`);
  const row = doors.structures[0].doors.find((d) => d.id === plan.id);
  ok(row?.passage === true && !/not walked/.test(row.reconstructed ?? ''), `${plan.id}: the doors file names it a passage, climbed`);
  ok(near(plan.sill, 1.89, 0.01), `${plan.id}: its sill at 6 ft over north grade (${plan.sill.toFixed(3)})`);
  const box = leafBox(plan);
  for (const [what, b] of Object.entries({ oak: m.oak, iron: m.iron })) {
    ok(box.x[0] <= b.x[0] && box.x[1] >= b.x[1] && box.z[0] <= -b.v[1] && box.z[1] >= -b.v[0]
      && (!b.y || (box.y[0] <= b.y[0] && box.y[1] >= b.y[1])), `${plan.id}: the leaf box holds the baked ${what}`);
  }
  ok(plan.hinge === m.hinge && plan.grades.hinge === 'inferred', `${plan.id}: hung on the jamb away from its latch (${plan.hinge})`);
  ok(box.z[1] - box.z[0] < 0.6 || box.x[1] - box.x[0] < 0.6, `${plan.id}: the box is no deeper than the leaf`);
}

// ---------------------------------------------------------------- the way up each stair
const treadSet = (plan, prefix) => plan.treads.filter((t) => t.id.startsWith(prefix)).map((t) => t.y);
for (const [plan, flights] of [[plans[0], ['flight_']], [plans[1], ['front_', 'stair_']]]) {
  const way = passagePlan(plan);
  ok(way[0].y === null && way.at(-1).y === plan.sill, `${plan.id}: from open ground outside to the sill inside`);
  const ys = way.map((p) => p.y).filter((y) => y !== null);
  ok(ys.every((y, i) => i === 0 || y >= ys[i - 1] - 1e-9), `${plan.id}: the way in only climbs`);
  for (const prefix of flights) {
    for (const y of treadSet(plan, prefix)) ok(ys.some((h) => near(h, y, 1e-6)), `${plan.id}: it stands on the ${prefix} tread at ${y.toFixed(3)}`);
  }
  const want = flights.reduce((n, f) => n + treadSet(plan, f).length, 0);
  const levels = [...new Set(ys.map((y) => y.toFixed(4)))];
  ok(levels.length >= want, `${plan.id}: ${levels.length} heights for ${want} treads`);
  // Each riser: two points a quarter-metre apart, the one below and the one above.
  let risers = 0;
  for (let i = 1; i < way.length; i += 1) {
    const a = way[i - 1], b = way[i];
    if (a.y === null || Math.abs(a.y - b.y) < 1e-4) continue;
    risers += 1;
    ok(Math.hypot(b.u - a.u, b.v - a.v) <= 0.25, `${plan.id}: a riser is stepped up, not a ramp`);
  }
  ok(risers === want - 1, `${plan.id}: ${risers} risers between ${want} treads`);
  const before = way[way.door];
  ok(near(before.y, plan.sill, 1e-6), `${plan.id}: the point before the door is level with the sill`);
}

// ---------------------------------------------------------------- the layer: leaves lifted, hung, swung
const record = { id: 'glessner_house', sidecar };
function quad(pos, a, b, c, d) { pos.push(...a, ...b, ...c, ...a, ...c, ...d); }
const pieces = new Map();
for (const plan of plans) {
  const m = MEASURED[plan.id].oak;
  const pos = [];
  const cx = (m.x[0] + m.x[1]) / 2, cz = -(m.v[0] + m.v[1]) / 2;
  if (m.x[1] - m.x[0] > m.v[1] - m.v[0]) quad(pos, [m.x[0], 2, cz], [m.x[1], 2, cz], [m.x[1], 4, cz], [m.x[0], 4, cz]);
  else quad(pos, [cx, 2, -m.v[0]], [cx, 2, -m.v[1]], [cx, 4, -m.v[1]], [cx, 4, -m.v[0]]);
  // And the wall beside it, which stays.
  quad(pos, [cx + 3, 2, cz - 3], [cx + 4, 2, cz - 3], [cx + 4, 4, cz - 3], [cx + 3, 4, cz - 3]);
  const geoOf = () => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setIndex([...Array(pos.length / 3).keys()]);
    geo.computeVertexNormals();
    return geo;
  };
  const mesh = new THREE.Mesh(geoOf(), new THREE.MeshStandardMaterial({ name: 'oak' }));
  const got = takeDoorLeaf(record, mesh, new THREE.Matrix4());
  ok(got.length === 1 && got[0].doorId === plan.id && mesh.geometry.getIndex().count === 6, `${plan.id}: its leaf is lifted, the wall stays`);
  ok(takeDoorLeaf(record, new THREE.Mesh(geoOf(), new THREE.MeshStandardMaterial({ name: 'granite' })), new THREE.Matrix4()).length === 0,
    `${plan.id}: nothing but oak and iron is taken for it`);
  got[0].material = doorLeafMaterial(mesh.material);
  pieces.set(plan.id, got);
}
const pl = sidecar.placement;
const matrix = new THREE.Matrix4().compose(enuToWorld(pl.local_e, pl.local_n, BASE),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(pl.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1));
const buildings = { matrixOf: (id) => (id === 'glessner_house' ? matrix : null), doorLeaves: pieces };
const problems = [];
const layer = createHouseDoors({ registry: new Map([['glessner_house', record]]), buildings, footprints: [], decks: [], problems });
ok(problems.filter((x) => !x.startsWith('glessner_house:front')).length === 0, `both passages hang: ${problems.join('; ')}`);
const court = layer.passage('glessner_house:service_stair');
const side = layer.passage('glessner_house:north_entry');
ok(court && side && layer.passages.length === 2, 'the layer has the two passages');
ok(!layer.get('glessner_house:service_stair'), 'a passage is not a visitor\'s Interact door');
const leafMesh = layer.group.getObjectByName('house-door:glessner_house:service_stair');
const pivot = leafMesh.children.find((c) => c.children.some((m) => m.name.startsWith('house-door-leaf')));
const run = (s) => { for (let t = 0; t < s; t += 0.05) layer.update(0.05); };
court.hold('a');
run(PASSAGE_SWING_S * 0.5);
ok(court.state === 'opening' && !court.isOpen(), 'held, it starts to swing');
run(PASSAGE_SWING_S * 0.6);
ok(court.isOpen() && court.swing === 1 && Math.abs(pivot.rotation.y) > 1.5, `in ${PASSAGE_SWING_S} s it is open, the leaf turned ${(pivot.rotation.y * 180 / Math.PI).toFixed(0)} deg`);
court.hold('b'); court.release('a');
run(PASSAGE_SWING_S * 2);
ok(court.isOpen(), 'while anyone holds it, it stays open');
court.release('b');
run(PASSAGE_SWING_S * 1.1);
ok(court.state === 'closed' && Math.abs(pivot.rotation.y) < 1e-9, 'let go by all, it shuts');
// The swing turns inward: the free edge goes behind the wall face.
const way0 = court.way();
ok(way0.length > 20 && Number.isFinite(way0[way0.door].y) && way0[0].y === null, 'its way in ENU, world heights, open ground at the foot');
ok(near(way0[0].e, doors.structures[0].doors[0].step.local_e, 0.05) && near(way0[0].n, doors.structures[0].doors[0].step.local_n, 0.05),
  'the way starts where the doors file has one stand at the foot');
ok(near(way0.at(-1).y, BASE + plans[0].sill, 1e-3), 'and ends inside, on the sill');

// ---------------------------------------------------------------- a day: in and out by the stair
function actorOf(id, e, n) {
  const a = {
    id: `hi_${id}`, personId: id, instance: { id: `hi_${id}`, appearance: { asset_id: 'woman_x' } }, person: { name: id },
    e, n, heading: 0, state: 'standing', indoors: false, inRange: true, path: null, standY: null, track: [],
    heightAt: () => BASE, place() {}, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; a.track.push({ indoors: a.indoors, e: a.e, n: a.n }); },
    turnTo(h) { a.heading = h; },
    root: { visible: true, getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    life: { attend() {}, nod() {} }, actions: { setTalk() {}, greet() {} },
    walkPath(pts, { onArrive = null } = {}) {
      const p = pts.map((q) => ({ e: q.e, n: q.n, y: Number.isFinite(q.y) ? q.y : null }));
      if (p.length < 2) return false;
      a.path = { pts: p, leg: 0, t: 0, onArrive };
      a.e = p[0].e; a.n = p[0].n; a.standY = p[0].y;
      a.state = 'walking';
      return true;
    },
    step(dt) {
      const P = a.path;
      if (!P) return;
      let left = 1.3 * dt;
      while (left > 0 && P.leg < P.pts.length - 1) {
        const x = P.pts[P.leg], y = P.pts[P.leg + 1];
        const len = Math.hypot(y.e - x.e, y.n - x.n);
        const s = Math.min(left, len * (1 - P.t));
        P.t = len > 1e-9 ? P.t + s / len : 1;
        left -= s;
        if (P.t >= 1 - 1e-9) { P.leg += 1; P.t = 0; }
      }
      const x = P.pts[Math.min(P.leg, P.pts.length - 1)], y = P.pts[Math.min(P.leg + 1, P.pts.length - 1)];
      a.e = x.e + (y.e - x.e) * P.t; a.n = x.n + (y.n - x.n) * P.t;
      a.standY = x.y !== null && y.y !== null ? x.y + (y.y - x.y) * P.t : null;
      a.track.push({ e: a.e, n: a.n, y: a.standY, swing: court.swing, indoors: a.indoors });
      if (P.leg >= P.pts.length - 1) { a.path = null; a.state = 'standing'; P.onArrive?.(a); }
    },
  };
  return a;
}
const COURT = { local_e: 1352.89, local_n: -3233.17, heading_deg: 105 };   // Kate Ryan's place in the court
const span = (from, to, extra) => ({ from, to, ...extra });
const dayOf = (spans) => ({ state: 'standing', day: [{ spans }] });
const kate = actorOf('kate', COURT.local_e, COURT.local_n);
kate.instance.behaviour = dayOf([span(0, 12, { indoors: false, at: COURT, activity: 'stand', doing: 'on watch in the court' }), span(12, 15, { indoors: true, where: 'glessner_house' }),
  span(15, 24, { indoors: false, at: COURT, activity: 'stand', doing: 'on watch in the court' })]);
const mattie = actorOf('mattie', COURT.local_e + 1.5, COURT.local_n - 1);
mattie.instance.behaviour = dayOf([span(0, 12, { indoors: false, at: { ...COURT, local_e: COURT.local_e + 1.5, local_n: COURT.local_n - 1 }, activity: 'stand', doing: 'on watch in the court' }),
  span(12, 15, { indoors: true, where: 'glessner_house' }), span(15, 24, { indoors: false, at: { ...COURT, local_e: COURT.local_e + 1.5 }, activity: 'stand', doing: 'on watch in the court' })]);
const actors = [kate, mattie];
let hour = 11;
const visitor = { e: 1352, n: -3238 };
const interactions = createInteractions();
const dayProblems = [];
const days = createHumanDays({ humans: { actors, shown: true }, three: THREE, hour: () => hour, date: () => '1904-07-01', doors,
  interactions, visitor: () => visitor, passages: layer, problems: dayProblems });
let log = [];
const tick = (s, dt = 0.05) => {
  for (let t = 0; t < s; t += dt) {
    for (const a of actors) a.step(dt);
    days.update(dt); layer.update(dt);
    log.push(actors.map((a) => ({ e: a.e, n: a.n, y: a.standY, indoors: a.indoors })));
  }
};
tick(1);
ok(dayProblems.length === 0 && !kate.indoors, `out in the court at 11 (${dayProblems.join('; ')})`);
// Noon: both go in by the court door.
hour = 12;
kate.track = []; mattie.track = []; log = [];
tick(40);
const sill = BASE + plans[0].sill;
for (const a of [kate, mattie]) {
  ok(a.indoors && !a.path, `${a.personId} went in`);
  const t = a.track;
  const went = t.findIndex((x) => x.indoors === true);
  ok(went > 0, `${a.personId}: indoors only after walking`);
  const climbed = t.slice(0, went).filter((x) => x.y !== null && x.y !== undefined).map((x) => x.y);
  const treadsY = treadSet(plans[0], 'flight_').map((y) => BASE + y);
  ok(treadsY.every((y) => climbed.some((h) => near(h, y, 0.03))), `${a.personId}: stood at every tread's height on the way up`);
  ok(climbed.every((y, i) => i === 0 || y >= climbed[i - 1] - 1e-6), `${a.personId}: only climbing`);
  const last = t[went - 1];
  ok(near(last.y, sill, 1e-3) && Math.hypot(last.e - way0.leaf.e, last.n - way0.leaf.n) > 0.3 && t.slice(0, went).some((x) => near(x.y ?? 0, sill, 1e-3) && x.swing >= 0.9),
    `${a.personId}: went through the open door before going in`);
  const atDoor = t.filter((x) => Math.hypot(x.e - way0[way0.door].e, x.n - way0[way0.door].n) < 0.05);
  ok(atDoor.length && atDoor.at(-1).swing >= 0.9, `${a.personId}: the door was open when they stepped through it`);
}
// Never two on one tread: one went up behind the other.
let nearest = Infinity;
for (const [k, m] of log) {
  if (k.y == null || m.y == null || k.indoors || m.indoors) continue;
  nearest = Math.min(nearest, Math.hypot(k.e - m.e, k.n - m.n));
}
ok(nearest > 1.2, `on the stair together they keep apart (nearest ${nearest.toFixed(2)} m)`);
ok(court.state === 'closed' && !court.holders.size, 'and the door shut behind them');
ok(days.snapshot().every((s) => s.on_way === null), 'nobody is left on the way');

// Three o'clock: out again, down the stair.
hour = 15;
kate.track = []; mattie.track = [];
let shutWhileInside = true;
for (let t = 0; t < 40; t += 0.05) {
  for (const a of actors) a.step(0.05);
  days.update(0.05); layer.update(0.05);
  for (const a of actors) {
    // While someone stands in the doorway, the door is open.
    if (!a.indoors && a.standY !== null && Math.hypot(a.e - way0.leaf.e, a.n - way0.leaf.n) < 0.4 && court.swing < 0.9 && a.path) shutWhileInside = false;
  }
}
ok(shutWhileInside, 'nobody walks through the shut door coming out');
for (const a of [kate, mattie]) {
  ok(!a.indoors, `${a.personId} came out`);
  const ys = a.track.filter((x) => x.y != null).map((x) => x.y);
  ok(ys.length && near(ys[0], sill, 1e-3) && ys.every((y, i) => i === 0 || y <= ys[i - 1] + 1e-6), `${a.personId}: came down from the sill, only down`);
  ok(treadSet(plans[0], 'flight_').every((y) => ys.some((h) => near(h, BASE + y, 0.03))), `${a.personId}: down every tread`);
}
ok(court.state === 'closed', 'the door shut once they were clear of it');

// Asked for at the court door: they come down the stair to the visitor.
hour = 13;
tick(60);
ok(kate.indoors && mattie.indoors, 'back in at one');
const door = interactions.get('door:glessner_house:service_stair');
ok(door, 'the court door offers Ask for');
const ask = interactions.actionsOf(door).find((a) => a.label === 'Ask for kate');
ok(ask, 'Ask for kate at the court door');
kate.track = [];
interactions.act(door, ask.id);
for (let t = 0; t < 30; t += 0.05) { for (const a of actors) a.step(0.05); days.update(0.05); layer.update(0.05); interactions.update(0.05); }
ok(!kate.indoors && kate.track.some((x) => near(x.y ?? 0, sill, 1e-3)) && kate.track.some((x) => x.swing >= 0.9),
  'asked for, she opens the door and comes down the stair');
ok(Math.hypot(kate.e - visitor.e, kate.n - visitor.n) < 3, 'and up to the visitor');

// The side door off Eighteenth Street is walked the same way.
const sideWay = side.way();
ok(sideWay.filter((p) => p.y !== null).length > 15 && near(sideWay.at(-1).y, BASE + plans[1].sill, 1e-3), 'the side door has its way up the alcove');

console.log(`PASS: ${checks} checks — Glessner's court and side doors open and shut as people pass, up and down their stairs (T-3524; passages ${PASSAGE.follow_s} s apart)`);
