#!/usr/bin/env node
/**
 * T-3443 — John J. Glessner stands on his front walk; Interact greets him or sends him home,
 * up his steps, through his door and in.
 *
 * With the real 1904 Glessner record and its door layer (house-doors.js, T-3442), on flat
 * ground, and a real HumanActor standing where his instance record puts him:
 *   - the instance stands on his own front walk, facing the street, within reach of nobody
 *     else's door; the person thing is made for him and not for his cook, nor for a man of
 *     another household;
 *   - the Interact key offers Greet first and Go home as a second key, numbered 2; R greets,
 *     2 sends him home, and a number nothing answers to is left alone;
 *   - Greet turns him to the visitor and opens his card once the greeting is done, saying
 *     nothing on the status line;
 *   - Go home: he walks only toward the door (never back to the sidewalk first), up onto the
 *     threshold at the sill, waits clear of the leaf while it swings, walks in past it, is
 *     indoors (no longer drawn, picked or offered), and the door shuts behind him; the key
 *     says he has gone in;
 *   - with the visitor standing in the doorway, he goes in and leaves it open;
 *   - interact.js: a step that waits on the world ends when it is answered, or at its timeout.
 *
 *   node tools/test_house_errands.mjs
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
const { footprintsFrom } = await import('../renderers/web/js/walker.js');
const { createInteractions, createInteractKey } = await import('../renderers/web/js/interact.js');
const { HumanActor } = await import('../renderers/web/js/humans.js');
const { enuToWorld } = await import('../renderers/web/js/terrain.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { glessnerFrontPlan, takeDoorLeaf, doorLeafMaterial, createHouseDoors, DOOR_SWING_S } = await import('../renderers/web/js/house-doors.js');
const { createHouseErrands, wayHome, HOUSEHOLD_DOORS, DOOR_WAIT_M, GREET_S, PERSON_REACH_M } = await import('../renderers/web/js/house-errands.js');

const ROOT = new URL('../', import.meta.url);
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const read = (rel) => JSON.parse(fs.readFileSync(new URL(rel, ROOT), 'utf8'));

const sidecar = read('data/sidecars/1904/glessner_house.json');
const BASE = 4.33;
const plan = glessnerFrontPlan(sidecar);
const face = plan.origin[0];
const [approach] = plan.treads;

// The door layer, as test_house_doors.mjs hangs it: a baked leaf lifted from a stand-in mesh.
function bakedLeaf() {
  const pos = [], u = face + plan.leaf.front;
  pos.push(u, 0.3, -11.9, u, 0.3, -13.1, u, 2.4, -13.1, u, 0.3, -11.9, u, 2.4, -13.1, u, 2.4, -11.9);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(12).fill(0.5), 2));
  geo.setIndex([0, 1, 2, 3, 4, 5]);
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name: 'oak' }));
}
const record = { id: 'glessner_house', sidecar };
const oak = bakedLeaf();
const pieces = takeDoorLeaf(record, oak, new THREE.Matrix4());
for (const piece of pieces) piece.material = doorLeafMaterial(oak.material);
const p = sidecar.placement;
const matrix = new THREE.Matrix4().compose(enuToWorld(p.local_e, p.local_n, BASE),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(p.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1));
const registry = new Map([['glessner_house', record]]);
const footprints = footprintsFrom(registry);
const decks = [];
const ix = createInteractions();
let visitor = null;
const doors = createHouseDoors({ registry, buildings: { matrixOf: () => matrix, doorLeaves: new Map([[plan.id, pieces]]) },
  footprints, decks, interactions: ix, visitor: () => visitor, groundAt: () => BASE, problems: [] });
const door = doors.get(plan.id);
ok(door, 'the front door hangs');
const inv = matrix.clone().invert();
const toPlan = (e, n) => { const w = new THREE.Vector3(e, 0, -n).applyMatrix4(inv); return { d: w.x - face, s: -w.z }; };
const enu = (u, v) => { const w = new THREE.Vector3(u, 0, -v).applyMatrix4(matrix); return { e: w.x, n: -w.z }; };
const mid = (plan.jambs[0] + plan.jambs[1]) / 2;

// ---------------------------------------------------------------- where he stands
const instance = read('data/humans/instances/1904/hi_glessner_john_j_1904.json');
ok(read('data/humans/instances/1904/index.json').instances.includes(instance.id), 'his record is in the 1904 index');
ok(instance.person_id === 'glessner_john_j' && instance.appearance.asset_id === 'glessner_john_j_1904', 'it is John J. Glessner, in his 1904 dress');
const at = toPlan(instance.placement.local_e, instance.placement.local_n);
ok(at.d > 0.5 && at.d < approach.d[1] && at.s > approach.s[0] && at.s < approach.s[1],
  `he stands on his own front walk, ${at.d.toFixed(2)} m out from his door`);
const outward = doors.path(plan.id).outward;
ok(Math.abs(((instance.placement.heading_deg - outward + 540) % 360) - 180) < 30, 'facing the street');
ok(instance.provenance.grade === 'reconstructed' && instance.provenance.liberty === 'L418'
  && instance.provenance.sources.every((s) => fs.existsSync(new URL(`data/sources/${s}.json`, ROOT))), 'reconstructed, under L418, every source on file');
const people = read('data/sidecars/1904/people.json').people;
const person = people.find((x) => x.id === 'glessner_john_j');
ok(HOUSEHOLD_DOORS[person.household] === plan.id, 'his household enters by this door');

// ---------------------------------------------------------------- the errand thing
function actorFor(inst, who) {
  const a = new HumanActor({ instance: inst, person: who, identity: { kind: 'person', personId: who.id, person: who, profile: null, role: null }, assets: {}, heightAt: () => BASE });
  a.walkSpeed = 1.2;
  a.life = { attend: (pt, s) => { a.attended = { pt, s }; } };
  a.actions = { greet: () => { a.greeted = (a.greeted ?? 0) + 1; } };
  return a;
}
const john = actorFor(instance, person);
const cook = people.find((x) => x.id === 'glessner_williamson_martha_l');
const mattie = actorFor({ ...instance, id: 'hi_cook', person_id: cook.id, placement: { local_e: 1367.5, local_n: -3233, heading_deg: 95 } }, cook);
const other = people.find((x) => x.household && x.household !== person.household && x.relationship === 'head');
const neighbour = actorFor({ ...instance, id: 'hi_other', person_id: other.id }, other);
const opened = [];
const errands = createHouseErrands({ humans: { actors: [john, mattie, neighbour] }, houseDoors: doors, interactions: ix,
  visitor: () => visitor, eye: () => new THREE.Vector3(0, 1.6, 0), openCard: (a) => opened.push(a.id), groundAt: () => BASE });
ok(errands.errands.length === 1 && errands.get('glessner_john_j')?.actor === john, 'only he is made a thing: not the cook, nor a neighbour');
const thing = errands.get('glessner_john_j');
ok(thing.state === 'out' && thing.kind === 'person' && thing.reach === PERSON_REACH_M, 'out, a person, within arm\'s reach');
{
  const hidden = createInteractions();
  const layer = { actors: [john], shown: false };
  const t = createHouseErrands({ humans: layer, houseDoors: doors, interactions: hidden }).errands[0];
  ok(t.at === null && hidden.nearest(john.e, john.n) === null, 'with people hidden in Settings he is offered to no one');
  layer.shown = true;
  ok(hidden.nearest(john.e, john.n) === t, 'and shown again, he is');
}

// A fake document, enough for the second key.
const doc = { createElement: (tag) => { const el = { tag, children: [], dataset: {}, attrs: {}, listeners: {}, textContent: '',
  append(...c) { el.children.push(...c); }, appendChild(c) { el.children.push(c); }, setAttribute(k, v) { el.attrs[k] = v; },
  addEventListener(t, fn) { el.listeners[t] = fn; } }; return el; } };
const moreEl = doc.createElement('div');
moreEl.hidden = true;
moreEl.replaceChildren = () => { moreEl.children = []; };
const keyEl = { hidden: true, textContent: '', dataset: {}, setAttribute() {}, addEventListener() {}, removeEventListener() {} };
const said = [];
const keyListeners = {};
const keys = { addEventListener: (t, fn) => { keyListeners[t] = fn; }, removeEventListener() {} };
const standBy = enu(face + at.d + 1.2, at.s + 0.4);
visitor = { e: standBy.e, n: standBy.n };
const key = createInteractKey({ interactions: ix, keyEl, moreEl, doc, keys,
  where: () => ({ ...visitor, bearing: (outward + 180) % 360, flying: false }), say: (t) => said.push(t) });
ok(key.refresh() === thing && keyEl.textContent === 'Greet', 'beside him the key offers Greet');
ok(key.choices.join() === 'greet,go_home' && !moreEl.hidden && moreEl.children.length === 1
  && moreEl.children[0].children[0].textContent === 'Go home' && moreEl.children[0].children[1].textContent === '2',
  'and Go home on a second key, numbered 2');
let prevented = 0;
const press = (code) => keyListeners.keydown({ code, target: null, preventDefault: () => { prevented += 1; } });
press('Digit5');
ok(prevented === 0 && !thing.running, 'a number nothing answers to is left alone');

// ---------------------------------------------------------------- Greet
press('KeyR');
ok(thing.running?.action.id === 'greet' && john.greeted === 1 && john.attended?.s === 6, 'R greets him: he looks at the visitor and touches his brim');
const toVisitor = (Math.atan2(visitor.e - john.e, visitor.n - john.n) * 180 / Math.PI + 360) % 360;
for (let i = 0; i < 90; i++) { ix.update(1 / 60); john.walk(1 / 60); }
ok(Math.abs(((john.heading - toVisitor + 540) % 360) - 180) < 1, `and turns to them (${john.heading.toFixed(1)} vs ${toVisitor.toFixed(1)})`);
ok(opened.length === 1 && opened[0] === john.id && !thing.running && thing.state === 'out', `his card opens when the greeting is done (${GREET_S} s)`);
ok(said.length === 0, 'and the status line says nothing over it');

// ---------------------------------------------------------------- Go home
function run(seconds, onFrame = null) {
  const trail = [];
  for (let i = 0; i < seconds * 60; i++) {
    ix.update(1 / 60);
    john.walk(1 / 60);
    trail.push({ ...toPlan(john.e, john.n), y: john.root.position.y, step: thing.running?.index ?? null, door: door.state, indoors: john.indoors });
    onFrame?.(i);
    if (!thing.running) break;
  }
  return trail;
}
const start = toPlan(john.e, john.n);
press('Digit2');
ok(thing.running?.action.id === 'go_home', '2 sends him home');
const trail = run(30);
ok(thing.state === 'home' && !thing.running, `he is home (${(trail.length / 60).toFixed(1)} s)`);
ok(trail.every((t) => t.d <= start.d + 1e-6), 'walking only toward the door, never back to the sidewalk first');
ok(trail.every((t) => Math.abs(t.s - mid) < Math.abs(start.s - mid) + 0.01), 'and squaring up to the doorway as he goes');
const waiting = trail.filter((t) => t.step === 1);
ok(waiting.length > 30 && waiting.every((t) => near(t.d, plan.leaf.front + DOOR_WAIT_M, 0.01) && near(t.y, BASE + plan.sill, 1e-6)),
  `he waits on the threshold, at the sill, ${DOOR_WAIT_M} m clear of the leaf, while it swings`);
ok(waiting[0].door === 'closed' && trail.find((t) => t.step === 2)?.door === 'open', 'the door opens for him');
ok(trail.filter((t) => t.step === 2).some((t) => t.d < plan.leaf.back - 1), 'he walks in past the leaf');
ok(trail.filter((t) => t.step !== null && t.step < 3).every((t) => !t.indoors) && john.indoors, 'and once inside he is indoors');
ok(door.state === 'closed' && !door.running, 'the door shuts behind him');
ok(said.at(-1) === 'John J. Glessner has gone in', `the key says so ("${said.at(-1)}")`);
ok(thing.at === null && key.refresh() !== thing && key.choices.length === 0, 'he is no longer offered');
john.update(1 / 60, new THREE.Vector3(0, 0, 0));
ok(!john.root.visible && !john.inRange, 'nor drawn, nor in range to be met');

// ---------------------------------------------------------------- someone in the doorway
{
  john.setIndoors(false);
  thing.state = 'out';
  const back = enu(face + at.d, at.s);
  john.e = back.e; john.n = back.n; john.standY = null;
  // The visitor on the threshold, in the leaf's sweep, just inside the jamb.
  const inSweep = enu(face + plan.leaf.front - 0.4, mid - 0.2);
  visitor = { e: inSweep.e, n: inSweep.n };
  ok(ix.act(thing, 'go_home').ok, 'sent home again, with the visitor in the doorway');
  run(30);
  ok(thing.state === 'home' && john.indoors && door.state === 'open', 'he goes in and leaves the door open rather than shut it on them');
}

// ---------------------------------------------------------------- the way home, alone
{
  const way = wayHome(doors, plan.id, [enu(face + plan.sidewalk + 4, mid + 3).e, enu(face + plan.sidewalk + 4, mid + 3).n]);
  const pp = way.toDoor.map((q) => toPlan(q.e, q.n));
  ok(pp.some((q) => near(q.d, plan.sidewalk, 1e-3)), 'from out in the street the way home comes in by the sidewalk');
  ok(near(pp.at(-1).d, plan.leaf.front + DOOR_WAIT_M, 1e-3) && near(way.inward, (outward + 180) % 360, 1e-9), 'and waits at the door, facing in');
}

// ---------------------------------------------------------------- interact.js: steps that wait on the world
{
  const ix2 = createInteractions();
  let answered = false;
  const t2 = ix2.add({ id: 'x', name: 'X', states: ['a', 'b'], state: 'a', at: [0, 0],
    actions: { a: [{ id: 'go', label: 'Go', to: 'b', steps: [{ label: 'Waiting', until: () => answered, timeout: 2 }] }] } });
  ix2.act(t2);
  ix2.update(1);
  ok(t2.running && t2.state === 'a', 'a step that waits on the world waits');
  answered = true;
  ix2.update(1 / 60);
  ok(!t2.running && t2.state === 'b', 'and ends when it is answered');
  t2.state = 'a'; answered = false;
  ix2.act(t2);
  ix2.update(1.5); ix2.update(0.6);
  ok(!t2.running && t2.state === 'b', 'or at its timeout');
}

doors.dispose();
console.log(`PASS: ${checks} checks — John J. Glessner on his front walk is greeted, and goes home up his steps and in (T-3443)`);
