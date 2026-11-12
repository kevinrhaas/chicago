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
 *   - the Interact key offers Greet first and Go inside as a second key, numbered 2; R greets,
 *     2 sends him home, and a number nothing answers to is left alone;
 *   - Greet turns him to the visitor and opens his card once the greeting is done, saying
 *     nothing on the status line;
 *   - Go inside: he walks only toward the door (never back to the sidewalk first), up onto the
 *     threshold at the sill, waits clear of the leaf while it swings, walks in past it, is
 *     indoors (no longer drawn, picked or offered), and the door shuts behind him; the key
 *     says he has gone in;
 *   - with the visitor standing in the doorway, he goes in and leaves it open;
 *   - T-3444: while he is in, his door offers Ask for him first (a knock); asked, he comes,
 *     opens the door from inside clear of its swing, comes out and down to the visitor (no
 *     nearer than MEET_M, no further than the sidewalk), turns to them and shuts the door;
 *     he can then walk them to a stand about the house (the router's way, the visitor
 *     walking with him), and from there go home by the town's walks and his steps;
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
const { createHumanDays } = await import('../renderers/web/js/human-days.js');
const { HumanActor } = await import('../renderers/web/js/humans.js');
const { enuToWorld } = await import('../renderers/web/js/terrain.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { glessnerFrontPlan, takeDoorLeaf, doorLeafMaterial, createHouseDoors, DOOR_SWING_S } = await import('../renderers/web/js/house-doors.js');
const { createHouseErrands, wayHome, wayOut, HOUSEHOLD_DOORS, HOUSE_STROLLS, DOOR_WAIT_M, GREET_S, PERSON_REACH_M, ANSWER_S, MEET_M, ANSWER_FROM_M }
  = await import('../renderers/web/js/house-errands.js');

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
const scene = read('data/scenes/1904.json');
const anchorAt = (id) => scene.anchors.find((a) => a.id === id) ?? null;
// A stand-in router: straight there, by way of a point to turn at (route.js is the town's).
const plans = [];
const router = { plan: (a, b) => { plans.push([a, b]); return { points: [[a.e, a.n], [(a.e + b.e) / 2, a.n], [b.e, b.n]] }; } };
const withHim = [];
const errands = createHouseErrands({ humans: { actors: [john, mattie, neighbour] }, houseDoors: doors, interactions: ix,
  visitor: () => visitor, eye: () => new THREE.Vector3(0, 1.6, 0), openCard: (a) => opened.push(a.id), groundAt: () => BASE,
  router, anchorAt, walkWith: (a, on) => withHim.push([a.id, on]) });
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
ok(key.refresh() === thing && keyEl.textContent === 'Interact' && moreEl.hidden, 'person actions start collapsed');
ok(key.choices.join() === 'greet,stroll:court,stroll:arch,go_home', 'all actions remain available');
ok(HOUSE_STROLLS[plan.id].every((x) => anchorAt(x.anchor)), 'every walk goes to a stand the scene has');
let prevented = 0;
const press = (code) => keyListeners.keydown({ code, target: null, preventDefault: () => { prevented += 1; } });
press('Digit5');
ok(prevented === 0 && !thing.running, 'a number nothing answers to is left alone');

// ---------------------------------------------------------------- Greet
press('KeyR');
ok(!moreEl.hidden && moreEl.children.length === 5 && !thing.running, 'R opens the complete menu without greeting');
ok(moreEl.children.at(-1).children.find((c) => c.className === 'ik-what').textContent === 'Go home', 'residence action is clearly named and grouped last');
press('Escape');
ok(moreEl.hidden, 'Escape collapses the menu');
press('Digit1');
ok(!thing.running, 'hidden menu shortcuts do not trigger actions');
press('KeyR');
press('Digit1');
ok(moreEl.hidden, 'choosing an action collapses the menu');
ok(thing.running?.action.id === 'greet' && john.greeted === 1 && john.attended?.s === 6, 'Greet greets him: he looks at the visitor and touches his brim');
const toVisitor = (Math.atan2(visitor.e - john.e, visitor.n - john.n) * 180 / Math.PI + 360) % 360;
for (let i = 0; i < 90; i++) { ix.update(1 / 60); john.walk(1 / 60); }
ok(Math.abs(((john.heading - toVisitor + 540) % 360) - 180) < 1, `and turns to them (${john.heading.toFixed(1)} vs ${toVisitor.toFixed(1)})`);
ok(opened.length === 1 && opened[0] === john.id && !thing.running && thing.state === 'out', `his card opens when the greeting is done (${GREET_S} s)`);
ok(said.length === 0, 'and the status line says nothing over it');

// ---------------------------------------------------------------- Go inside
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
press('KeyR');
press('Digit4');
ok(thing.running?.action.id === 'go_home', 'the last numbered action sends him home');
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

// ---------------------------------------------------------------- T-3444: asked for at the door
{
  const at0 = enu(face + plan.sidewalk - 1.0, mid + 0.3);  // the visitor, on the walk below the steps
  visitor = { e: at0.e, n: at0.n };
  // The door left open by the last test: shut it first.
  ix.act(door, 'close'); ix.update(DOOR_SWING_S + 0.05);
  ok(door.state === 'closed', 'his door is shut');
  const offers = ix.offer(door);
  ok(offers.label === 'Ask for John J. Glessner' && offers.more.map((a) => a.id).join() === 'open',
    'at his shut door, Ask for him comes first, then Open door');
  ok(ix.act(door).ok && thing.running?.action.id === 'come_out', 'a knock asks for him');
  ix.update(1 / 60);
  ok(!door.running && door.state === 'closed', 'the door is not opened by the knock');
  const trail = [];
  for (let i = 0; i < 60 * 30 && thing.running; i++) {
    ix.update(1 / 60); john.walk(1 / 60);
    if (!john.indoors) trail.push({ ...toPlan(john.e, john.n), y: john.root.position.y, step: thing.running?.index ?? null, door: door.state, swing: door.swing });
  }
  ok(thing.state === 'out' && !john.indoors && said.at(-1) === 'John J. Glessner comes to the door', `he comes to the door (${said.at(-1)})`);
  const first = trail[0];
  ok(first.step === 1 && near(first.d, plan.leaf.back - ANSWER_FROM_M, 0.01) && first.swing < 0.1,
    `he appears ${ANSWER_FROM_M} m inside the leaf as it starts to swing`);
  const hinge = { d: plan.leaf.back, s: plan.hinge === 'right' ? plan.jambs[1] : plan.jambs[0] };
  const width = plan.jambs[1] - plan.jambs[0];
  ok(Math.hypot(first.d - hinge.d, first.s - hinge.s) > width, 'out of the leaf\'s sweep');
  ok(trail.filter((t) => t.step === 2).every((t) => t.door === 'open'), 'he walks out once it is open');
  const end = toPlan(john.e, john.n);
  const meet = Math.hypot(john.e - visitor.e, john.n - visitor.n);
  ok(near(meet, MEET_M, 0.15) && end.d > plan.leaf.front + DOOR_WAIT_M - 0.01, `down the walk to ${meet.toFixed(2)} m from the visitor`);
  const toV = (Math.atan2(visitor.e - john.e, visitor.n - john.n) * 180 / Math.PI + 360) % 360;
  ok(Math.abs(((john.heading - toV + 540) % 360) - 180) < 2, 'turned to them');
  ok(door.state === 'closed' && john.greeted >= 2, 'the door shut behind him, and he touches his brim');
  ok(key.refresh() === thing && key.choices[0] === 'greet', 'and he is offered again: Greet first');
  // Asked for from the sidewalk, he comes no further than the sidewalk.
  const far = wayOut(doors, plan.id, [enu(face + plan.sidewalk + 8, mid).e, enu(face + plan.sidewalk + 8, mid).n]);
  ok(near(toPlan(far.out.at(-1).e, far.out.at(-1).n).d, plan.sidewalk, 1e-3), 'asked for from the street, he stops at the sidewalk');
  const close = wayOut(doors, plan.id, [enu(face + 0.1, mid).e, enu(face + 0.1, mid).n]);
  ok(near(toPlan(close.out.at(-1).e, close.out.at(-1).n).d, plan.leaf.front + DOOR_WAIT_M, 1e-3), 'and with the visitor on the threshold, on it');
}

// ---------------------------------------------------------------- T-3444: a walk about the house
{
  plans.length = 0; withHim.length = 0;
  const court = anchorAt('glessner_tour_hall_bow');
  ok(ix.act(thing, 'stroll:court').ok && plans.length === 1 && withHim.at(-1)?.[1] === true, 'Show me the courtyard: the router finds his way, and the visitor walks with him');
  for (let i = 0; i < 60 * 90 && thing.running; i++) { ix.update(1 / 60); john.walk(1 / 60); }
  ok(!thing.running && near(john.e, court.local_e, 1e-6) && near(john.n, court.local_n, 1e-6), 'he walks to the court\'s stand');
  ok(near(john.heading, court.yaw_deg, 0.6) && withHim.at(-1)?.[1] === false, 'turns to its view, and the walking-with ends');
  // From the court, home: by the town's way to the foot of his walk, then up it.
  plans.length = 0;
  const home = wayHome(doors, plan.id, [john.e, john.n], { router });
  const hp = home.toDoor.map((q) => toPlan(q.e, q.n));
  ok(plans.length === 1 && hp.some((q) => near(q.d, plan.sidewalk, 1e-3)), 'from the court his way home comes round by the sidewalk');
  ok(ix.act(thing, 'go_home').ok, 'and he goes');
  for (let i = 0; i < 60 * 120 && thing.running; i++) { ix.update(1 / 60); john.walk(1 / 60); }
  ok(thing.state === 'home' && john.indoors, 'all the way in');
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

// T-3533: the real day engine and errand engine share one actor without fighting.
{
  const { createHumanDays } = await import('../renderers/web/js/human-days.js');
  const engine = createInteractions();
  const a = actorFor(instance, person);
  const staff = actorFor(read('data/humans/instances/1904/hi_glessner_williamson_martha_l_1904.json'), cook);
  const humans = { actors: [a, staff] };
  let household, caller = null;
  const daily = createHumanDays({ humans, hour: () => 23, date: () => '1904-07-01',
    doors: read('data/humans/doors_1904.json'), interactions: engine,
    visitor: () => caller, held: (actor) => !!household?.get(actor.id)?.running });
  daily.update(0.1);
  caller = visitor;
  household = createHouseErrands({ humans, houseDoors: doors, interactions: engine, days: daily,
    visitor: () => visitor, groundAt: () => BASE, router, anchorAt });
  ok(household.errands.length === 2, 'scheduled staff have the same outdoor interactions as family');
  ok(household.get(a.id).state === 'home', 'errand state reflects the schedule');
  ok(household.callOut(a.id).ok, 'scheduled resident can answer the working front door');
  for (let i = 0; i < 60 * 90; i++) { engine.update(1 / 60); ix.update(1 / 60); a.walk(1 / 60); daily.update(1 / 60); }
  ok(!a.indoors && daily.isCalled(a), 'front-door call holds the resident outside his night routine');
  const choices = engine.actionsOf(household.get(a.id));
  ok(choices.some((c) => c.id.startsWith('activity:')), 'normal outdoor activities offered after answering');
  ok(choices.some((c) => c.label === 'Go inside'), 'Go inside remains available');
  const task = choices.find((c) => c.id.startsWith('activity:'));
  ok(engine.act(household.get(a.id), task.id).ok, 'can request a normal outdoor activity at night');
  daily.update(0.1);
  ok(!a.indoors && !daily.isCalled(a), 'activity replaces the door call without the night schedule interrupting');

  // The reciprocal lease: manual Greet/Stroll cannot replace a tour guide's
  // live route or arrival callback, even through the public direct action API.
  const errand = household.get(a.id);
  a.jauntHost = true;
  a.walkPath([{ e: a.e, n: a.n }, { e: a.e + 8, n: a.n }], { endHeading: 90, onArrive() {} });
  const guidePath = a.path;
  ok(errand.at === null && engine.actionsOf(errand).length === 0, 'an approaching jaunt guide offers no competing household interactions');
  ok(!engine.act(errand, 'greet').ok && !household.stroll(a.id, 'stroll:court').ok, 'direct Greet and Stroll also refuse the guide lease');
  ok(a.path === guidePath && !errand.running, 'refused actions preserve the guide path and callback');
  a.setIndoors(true);
  ok(!household.callOut(a.id).ok && a.path === guidePath, 'calling an indoor hosted guide cannot replace the doorway handoff');
  a.jauntHost = false;
  a.setIndoors(false);
  ok(engine.actionsOf(errand).some(c => c.id === 'greet'), 'household interactions return after the guide lease is released');
}

// T-3543: the real walking actor pauses for choices, and nearby shelter differs from home.
{
  const indoor = (from, to, where) => ({ from, to, indoors: true, where });
  const day = [{ spans: [indoor(0, 6, 'home'), { from: 6, to: 20, indoors: false,
    at: { local_e: 9, local_n: 0 }, activity: 'work', doing: 'garden tasks' }, indoor(20, 24, 'home')] }];
  const a = actorFor({ ...instance, id: 'menu-walker', placement: { local_e: 9, local_n: 0, heading_deg: 90 },
    behaviour: { state: 'standing', day } }, person);
  const b = actorFor({ ...instance, id: 'nearby-host', person_id: 'host', placement: { local_e: 10, local_n: 0, heading_deg: 0 },
    behaviour: { day: [{ spans: [indoor(0, 24, 'nearby')] }] } }, { ...person, id: 'host' });
  const doorData = { structures: ['home', 'nearby'].map((structure, i) => ({ structure, name: structure,
    doors: [{ id: structure + ':door', step: { local_e: i * 10, local_n: -2 },
      leaf: { local_e: i * 10, local_n: -1 }, outward_deg: 180 }] })) };
  let h = 10;
  const engine = createInteractions();
  const layer = createHumanDays({ humans: { actors: [a, b] }, hour: () => h, date: () => '1904-07-01',
    interactions: engine, doors: doorData, visitor: () => ({ e: 9, n: 0 }), clear: () => true });
  const tick = seconds => { for (let i = 0; i < seconds * 20; i++) { a.walk(.05); b.walk(.05); layer.update(.05); } };
  tick(2);
  a.walkPath([{ e: a.e, n: a.n }, { e: 14, n: 0 }]); a.walk(.5);
  const route = a.path, position = [a.e, a.n], release = layer.attend(a.id);
  ok(typeof release === 'function' && layer.isOccupied(a), 'opening the menu temporarily owns the walker');
  tick(10); assert.deepEqual([a.e, a.n], position, 'a real walking actor stays put while choices are open');
  release(); ok(a.path === route, 'dismissal restores the same unfinished route');
  a.walk(.5); ok(Math.hypot(a.e - position[0], a.n - position[1]) > .01, 'the walk continues after dismissal');
  ok(layer.nearestEntrance(a.id)?.structure === 'nearby' && layer.residence(a.id) === 'home', 'nearest entrance and residence are distinct');
  ok(layer.request(a.id, null, { inside: 'nearest' }).ok, 'Go inside accepts the nearby entrance'); tick(20);
  ok(a.indoors && layer.people.find(p => p.actor === a).inside === 'nearby', 'Go inside reaches the nearby building');
  ok(layer.doors.find(t => t.structure === 'nearby').actions.shut.some(x => x.id === `ask:${a.personId}`), 'the guest is callable at the building they actually entered');
  ok(layer.request(a.id, null, { inside: 'home' }).ok, 'Go home accepts their residence while sheltered elsewhere');
  tick(.1); ok(!a.indoors && a.e > 8, 'returning home first exits the nearby building, without teleporting home');
  tick(30); ok(a.indoors && layer.people.find(p => p.actor === a).inside === 'home', 'Go home returns to the residence');
  h = 21; tick(1); h = 10; tick(12);
  const release2 = layer.attend(a.id); h = 21; tick(15); release2();
  ok(a.indoors, 'closing a menu after the hour changes resumes the new daily duty');
  h = 10; layer.ask(a.id); tick(12);
  const release3 = layer.attend(a.id);
  layer.host(a.id, { e: 12, n: 0 }, { heading: 90 }); const hostPath = a.path; release3();
  ok(layer.isHosted(a) && a.path === hostPath, 'dismissing an older menu cannot undo a jaunt takeover');
}

// A selected person's return trip must finish after they leave drawing range.
{
  const a = actorFor({ ...instance, id: 'offscreen-return', placement: { local_e: 0, local_n: 0, heading_deg: 90 },
    behaviour: { state: 'standing' } }, person);
  let arrivals = 0;
  a.walkPath([{ e: 0, n: 0 }, { e: 10, n: 0 }], { onArrive() { arrivals++; a.setIndoors(true); } });
  const far = new THREE.Vector3(1000, BASE, 0);
  for (let i = 0; i < 400 && !a.path?.arrived; i++) a.update(.05, far);
  ok(a.path?.arrived && Math.abs(a.e - 10) < .001, 'an offscreen one-time walk still reaches its destination');
  // The visitor returns on the arrival frame: finishing inside must win over LOD re-entry.
  a.recheck = 0; a.update(.05, new THREE.Vector3(a.e, BASE, -a.n));
  ok(arrivals === 1 && a.indoors && !a.inRange && !a.root.visible, 'arrival fires once and stays indoors even when the visitor returns');
  ok(a.counters.animated === 0, 'finishing an offscreen walk does not animate an unseen body');
  a.dispose();
}

doors.dispose();
console.log(`PASS: ${checks} checks — John J. Glessner on his front walk is greeted and goes home up his steps (T-3443); asked for at his door, he comes out and walks you round (T-3444)`);
