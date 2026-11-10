#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3525 (owner, 2026-11-08: "this will be the first jaunt we will show people here ... have
 * john or frances welcome you and have everyone in the house explain their roles"): a stop's
 * `hosts` come to their marks while the visitor walks to it, turn to its stand, greet the
 * visitor on arrival, and go back about their day when the visitor walks on. Node only: the
 * controller with a recording adapter, jaunt-hosts.js with stand-in figures, and the real
 * human-days.js taking a person out of their day and giving them back.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createJaunts, stopPeople, hostIds, keptPeople, canNext } from '../renderers/web/js/jaunts.js';
import { createJauntHosts, markOf } from '../renderers/web/js/jaunt-hosts.js';
import { createHumanDays } from '../renderers/web/js/human-days.js';

const fixture = id => JSON.parse(fs.readFileSync(new URL(`../data/jaunts/_fixtures/fixture-${id}.json`, import.meta.url)));

// ---- who a stop keeps: its hosts with its people; on the way from a stop, its hosts too.
const s0 = { id: 'a', hosts: [{ person: 'john', local_e: 1, local_n: 2 }] }, s1 = { id: 'b', people: ['kate'], hosts: [{ person: 'mattie', local_e: 3, local_n: 4 }] };
assert.deepEqual(hostIds(s0), ['john']);
assert.deepEqual(stopPeople(s1), ['kate', 'mattie'], 'a stop keeps its people and its hosts');
const jaunt = { stops: [s0, s1] };
assert.deepEqual(keptPeople({ jaunt, visited: [{ id: 'a' }, { id: 'b' }], stopIndex: 1, phase: 'travelling', fromStopId: 'a' }), ['kate', 'mattie', 'john'],
  'walking on, the host who sent the visitor is kept until they arrive');
assert.deepEqual(keptPeople({ jaunt, visited: [{ id: 'a' }, { id: 'b' }], stopIndex: 1, phase: 'atStop', fromStopId: 'a' }), ['kate', 'mattie']);
assert.equal(markOf({ person: 'x', local_e: 'no', local_n: 1 }), null, 'a malformed mark is no mark');
console.log('PASS a stop keeps its hosts, and the last stop\'s hosts while walking on');

// ---- the controller brings the hosts of the stop ahead, greets on arrival, lets go at the end.
{
  const walk = structuredClone(fixture('walk'));
  walk.stops[0].hosts = [{ person: 'john', local_e: 1, local_n: 2 }];
  walk.stops[1].hosts = [{ person: 'mattie', local_e: 3, local_n: 4 }];
  const calls = [];
  const hosts = { sync: (stop, o) => calls.push(['sync', stop?.id ?? null, o.arrived]), release: () => calls.push(['release']) };
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go() { return true; } };
  const c = createJaunts({ load: async () => walk, resolve: x => x, place: () => true, enter: () => true, travel,
    showMenu() {}, render() {}, openDetail() {}, closeDetail() {}, onError(e) { throw e; }, storage: null, hosts });
  await c.start(walk.id);
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[0].id, true], 'at the first stop its host greets');
  c.next();
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[1].id, false], 'walking on, the next stop\'s host comes to the mark');
  const n = calls.length;
  c.straight();
  assert.equal(calls.length, n, 'the same leg again changes nothing');
  const beforeMenu = calls.length;
  c.menu();
  assert.equal(calls.length, beforeMenu, 'Menu pauses without sending a held host home');
  c.resume();
  assert.notDeepEqual(calls.at(-1), ['release'], 'Resume retains the paused outing host');
  c.end();
  assert.deepEqual(calls.at(-1), ['release'], 'End lets every host go');
}
console.log('PASS the controller brings each stop\'s hosts, greets on arrival and lets them go at the end');

// ---- jaunt-hosts.js: a figure with no day is walked to the mark, turned, greets, and walked back.
const planned = { plan: (a, b) => ({ points: [[a.e, a.n], [b.e, b.n]] }) };
const figure = (id, extra = {}) => ({
  id, personId: id, e: 0, n: 0, heading: 90, state: 'standing', path: null, indoors: false, disposed: false,
  greets: 0, attended: 0,
  walkPath(pts, { endHeading, onArrive }) { this.path = { pts, endHeading, onArrive }; this.state = 'walking'; return true; },
  arrive() { const p = this.path; this.path = null; this.e = p.pts.at(-1).e; this.n = p.pts.at(-1).n; if (p.endHeading !== null) this.heading = p.endHeading; this.state = 'standing'; p.onArrive?.(this); },
  turnTo(h) { this.heading = h; return true; }, setState(s) { this.state = s; }, setIndoors(on) { this.indoors = on; }, place() {},
  life: { attend() { figure.attended++; } }, actions: { greet() { figure.greets++; } }, ...extra,
});
figure.greets = 0; figure.attended = 0;
{
  const john = figure('john'), walker = figure('walker', { route: [{ local_e: 0, local_n: 0 }, { local_e: 9, local_n: 0 }] });
  walker.state = 'walking';
  const humans = { get: id => ({ john, walker })[id] ?? null };
  const h = createJauntHosts({ humans, router: planned, visitor: () => ({ e: 0, n: 10 }), eye: () => ({ x: 0, y: 1.6, z: 0 }) });
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 } });
  assert.ok(john.path, 'he walks to his mark');
  assert.equal(figure.greets, 0, 'no greeting before the visitor arrives');
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 }, arrived: true });
  assert.equal(figure.greets, 0, 'arrived first, he greets only once he stands at the mark');
  john.arrive();
  assert.equal(john.e, 0); assert.equal(john.n, 6);
  assert.ok(figure.greets === 1 && figure.attended === 1, 'at the mark he looks at the visitor and greets');
  assert.ok(Math.abs(john.heading - 0) < 1e-9, 'turned to the visitor (due north of him)');
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 }, arrived: true });
  assert.equal(figure.greets, 1, 'a stop greets once');
  // The next stop's host is a route walker: off her route to the mark, and back on it after.
  h.sync([{ person: 'walker', local_e: 4, local_n: 4 }], { stand: { e: 4, n: 8 } });
  assert.ok(john.path, 'let go, he walks back to where he was taken from');
  john.arrive();
  assert.equal(john.n, 0, 'back where he stood');
  assert.deepEqual(h.active, ['walker']);
  walker.arrive();
  h.release();
  walker.arrive();
  assert.equal(walker.state, 'walking', 'back where she left it, she walks her route again');
  assert.deepEqual(h.active, []);
}
console.log('PASS a host with no day walks to the mark, greets once there, and goes back; a route walker resumes her route');

// ---- human-days.js: a host is taken out of their day, out of the house by its door, and given back.
{
  const kate = figure('kate', { instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: true, where: 'house', doing: 'the kitchen' }] }] } } });
  kate.indoors = true;
  const humans = { actors: [kate], isHeld: () => false };
  const doors = { structures: [{ structure: 'house', name: 'House', doors: [
    { id: 'house:back', step: { local_e: 10, local_n: 0 }, leaf: { local_e: 10, local_n: -1 }, outward_deg: 0 },
    { id: 'house:front', step: { local_e: -10, local_n: 0 }, leaf: { local_e: -10, local_n: -1 }, outward_deg: 0 }] }] };
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15', doors, visitor: () => ({ e: 9, n: 8 }) });
  days.update(0.1);
  assert.equal(kate.indoors, true, 'her day has her in');
  assert.deepEqual(days.host('kate', { e: 9, n: 5 }, { heading: 0, onArrive: () => { kate.met = true; } }), { ok: true });
  assert.equal(kate.indoors, false, 'she comes out');
  assert.deepEqual([kate.path.pts[0].e, kate.path.pts[0].n], [10, 0], 'by the door nearest her mark');
  assert.equal(days.isHosted(kate), true);
  kate.arrive();
  assert.ok(kate.met && kate.e === 9 && kate.n === 5, 'and stands at it');
  for (let i = 0; i < 5; ++i) days.update(0.1);
  assert.equal(kate.path, null, 'her day leaves a host alone');
  assert.equal(days.host('nobody', { e: 0, n: 0 }).ok, false);
  assert.equal(days.unhost('kate'), true);
  days.update(0.1);
  assert.ok(kate.path, 'let go, she walks back to the house');
  assert.equal(kate.path.pts.at(-1).e, 10, 'to its nearest door');
  assert.equal(days.isHosted(kate), false);
}
console.log('PASS human-days takes a host out of her day, out by the nearest door, and gives her back');

// ---- by a T-3524 passage door: she comes down its stair, the door opening, then on to the mark.
{
  const kate = figure('kate', { instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: true, where: 'house', doing: 'the kitchen' }] }] } } });
  kate.indoors = true;
  const humans = { actors: [kate], isHeld: () => false };
  const doors = { structures: [{ structure: 'house', name: 'House', doors: [
    { id: 'house:stair', step: { local_e: 10, local_n: 0 }, leaf: { local_e: 10, local_n: -1 }, outward_deg: 0 }] }] };
  const held = new Set();
  const way = Object.assign([{ e: 10, n: 2 }, { e: 10, n: 0 }, { e: 10, n: -1 }, { e: 10, n: -2 }], { door: 2, leaf: { e: 10, n: -1 } });
  const pass = { id: 'house:stair', way: () => way, hold: (p) => held.add(p), release: (p) => held.delete(p), isOpen: () => held.size > 0 };
  const passages = { passage: (id) => (id === pass.id ? pass : null) };
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15', doors, passages, visitor: () => ({ e: 9, n: 8 }) });
  days.update(0.1);
  assert.equal(days.host('kate', { e: 9, n: 5 }, { heading: 0, onArrive: () => { kate.met2 = true; } }).ok, true);
  assert.equal(kate.indoors, false, 'she comes out on the stair');
  assert.ok(held.size === 1, 'the door is held open for her');
  assert.deepEqual([kate.path.pts[0].e, kate.path.pts[0].n], [10, -2], 'from the top of the way, inside');
  kate.arrive();
  assert.equal(held.size, 0, 'down and through, the door is let go');
  assert.ok(kate.path && kate.path.pts.at(-1).e === 9, 'and on to her mark');
  kate.arrive();
  assert.ok(kate.met2 && kate.e === 9 && kate.n === 5, 'where she stands');
}
console.log('PASS a host whose door is a passage comes out by its stair and door, then to the mark');
// ---- An already-hidden outdoor day host hands off unseen; visible travel never guesses.
for (const mode of ['walk', 'instantly', 'fly']) {
  const charles = figure('charles', { e: 1395.2, n: -3244.3, root: { visible: false }, instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: false, activity: 'stand', at: { local_e: 1395.2, local_n: -3244.3, heading_deg: 90 }, doing: 'keeping watch beside the carriage team' },
  ] }] } } });
  const humans = { actors: [charles], get: id => id === 'charles' ? charles : null, isHeld: () => false };
  let plans = 0;
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15',
    visitor: () => mode === 'fly' ? null : ({ e: 1333, n: -3209.5 }),
    hostRouter: { plan: () => { plans++; throw Error('a hidden handoff must not build the grid'); } } });
  days.update(.1);
  const hosts = createJauntHosts({ humans, days });
  const wanted = [{ person: 'charles', local_e: 1334.82, local_n: -3211.63 }];
  const before = figure.greets;
  hosts.sync(wanted, { arrived: true });
  assert.deepEqual([charles.e, charles.n], [1334.82, -3211.63], `${mode}: hidden host at unchanged tour mark`);
  assert.equal(charles.root.visible, false, 'handoff never reveals a hidden figure');
  assert.equal(charles.path, null);
  assert.equal(plans, 0);
  assert.equal(figure.greets, before + 1, 'already at mark, greet once');
  hosts.sync(wanted, { arrived: true });
  assert.equal(figure.greets, before + 1, 'repeated stop is idempotent');
  hosts.release();
  assert.equal(days.isHosted(charles), false);
  days.update(.1);
  assert.deepEqual([charles.e, charles.n], [1395.2, -3244.3], 'hidden handback returns to everyday post without a wall chord');
  hosts.sync(wanted, { arrived: true }); // Back to the stop after handback.
  assert.deepEqual([charles.e, charles.n], [1334.82, -3211.63]);
  hosts.release(); days.update(.1);
  assert.deepEqual(hosts.active, []);
  assert.equal(charles.jauntHost, false);
}
console.log('PASS hidden day-host handoff and handback in walk/instant/fly, back, repeated stop and cleanup');
{
  const charles = figure('charles', { e: 1395.2, n: -3244.3, root: { visible: true }, instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: false, activity: 'stand', at: { local_e: 1395.2, local_n: -3244.3, heading_deg: 90 }, doing: 'keeping watch beside the carriage team' },
  ] }] } } });
  const humans = { actors: [charles], get: () => charles };
  let ready = false, plans = 0;
  const routed = { plan: (a, b) => { plans++; return ready ? { points: [[a.e, a.n], [1395.2, -3207], [1334.82, -3207], [b.e, b.n]] } : null; } };
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15', visitor: () => ({ e: 1333, n: -3209.5 }), hostRouter: routed });
  days.update(.1);
  const hosts = createJauntHosts({ humans, days });
  const wanted = [{ person: 'charles', local_e: 1334.82, local_n: -3211.63 }], before = figure.greets;
  hosts.sync(wanted, { arrived: true });
  assert.equal(charles.path, null, 'unready router refuses visible movement');
  assert.deepEqual([charles.e, charles.n], [1395.2, -3244.3]);
  assert.equal(figure.greets, before, 'no false arrival or premature greeting');
  ready = true;
  for (let i = 0; i < 4; i++) days.update(.25);
  assert.ok(charles.path, 'retry uses the now-ready real route');
  assert.ok(charles.path.pts.some(p => p.n === -3207), 'the planner detour is preserved');
  assert.equal(figure.greets, before);
  charles.arrive();
  assert.equal(figure.greets, before + 1);
  hosts.release(); days.update(.1);
  assert.ok(charles.path, 'visible return also takes a planned route');
  assert.equal(charles.jauntHost, false);
  charles.arrive();
  assert.deepEqual([charles.e, charles.n], [1395.2, -3244.3]);
  assert.equal(days.isHosted(charles), false);
  assert.ok(plans >= 3);
}
{
  const charles = figure('charles', { root: { visible: true } });
  const hosts = createJauntHosts({ humans: { get: () => charles }, router: { plan: () => null } });
  hosts.sync([{ person: 'charles', local_e: 80, local_n: 20 }], { arrived: true });
  assert.equal(charles.path, null, 'dayless visible host also refuses an unplanned chord');
  assert.deepEqual([charles.e, charles.n], [0, 0]);
  assert.deepEqual(hosts.active, []);
  assert.ok(!charles.jauntHost);
  hosts.release();
}
console.log('PASS visible hosts await safe routing and arrival, with safe visible handback and no fake takeover');
{
  const charles = figure('charles', { e: 1395.2, n: -3244.3, root: { visible: true }, instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: false, activity: 'stand', at: { local_e: 1395.2, local_n: -3244.3, heading_deg: 90 }, doing: 'keeping watch beside the carriage team' },
  ] }] } } });
  const humans = { actors: [charles], get: id => id === 'charles' ? charles : null };
  let plans = 0;
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15',
    hostRouter: { plan: () => { plans++; return null; } } });
  days.update(.1);
  const hosts = createJauntHosts({ humans, days });
  const wanted = [{ person: 'charles', local_e: 1334.82, local_n: -3211.63 }];
  hosts.sync(wanted, { arrived: false });
  assert.deepEqual([charles.e, charles.n], [1395.2, -3244.3], 'ordinary sync never infers a camera cut');
  const beforeCut = plans;
  hosts.sync(wanted, { arrived: true, cut: true }); // caller has already moved the camera synchronously
  assert.deepEqual([charles.e, charles.n], [1334.82, -3211.63], 'actual camera cut prepares the same actor before its destination frame');
  assert.equal(plans, beforeCut, 'a camera cut does not build the grid');
  assert.equal(charles.root.visible, true, 'no synthetic hide was used to manufacture this cut');
  hosts.sync([], { retain: ['charles'] });
  for (let i = 0; i < 300; i++) days.update(.25);
  assert.equal(days.isHosted(charles), true, 'departing kept host stays at the mark even after a long paused leg');
  assert.deepEqual([charles.e, charles.n], [1334.82, -3211.63]);
  const beforeBack = figure.greets;
  hosts.sync(wanted, { arrived: true });
  assert.deepEqual([charles.e, charles.n], [1334.82, -3211.63], 'Back returns to the waiting host without a minute-long return');
  assert.equal(figure.greets, beforeBack, 'an unchanged retained stop does not repeat a greeting');
  charles.root.visible = false; // actual next-arrival crowd filtering occurs before host release
  hosts.sync([], { retain: [] }); days.update(.1);
  assert.equal(days.isHosted(charles), false);
  assert.deepEqual([charles.e, charles.n], [1395.2, -3244.3]);
  assert.equal(charles.jauntHost, false);
  assert.deepEqual(hosts.active, []);
}
console.log('PASS explicit camera-cut handoff, retained departing host, long pause/Back and hidden release');

// ---- Visible dayless handback retains ownership through unavailable/rejected routes.
for (const mode of ['no-route', 'walk-rejected', 'indoor-return-no-route', 'planner-throws']) {
  const john = figure('john', { indoors: mode === 'indoor-return-no-route', root: { visible: false } });
  let routeReady = true, rejected = false;
  const walkPath = john.walkPath;
  john.walkPath = function (...args) { return rejected ? false : walkPath.apply(this, args); };
  const h = createJauntHosts({ humans: { get: () => john }, router: { plan(a, b) {
    if (!routeReady && mode === 'planner-throws') throw Error('planner not ready');
    return routeReady ? { points: [[a.e, a.n], [b.e, b.n]] } : null;
  } } });
  h.sync([{ person: 'john', local_e: 8, local_n: 0 }], { arrived: true });
  john.root.visible = true; routeReady = mode === 'walk-rejected'; rejected = mode === 'walk-rejected';
  h.release();
  assert.deepEqual(h.active, [], `${mode}: released host is not still active`);
  assert.deepEqual(h.returning, ['john'], `${mode}: original home survives the failed return`);
  assert.deepEqual([john.e, john.n], [8, 0], `${mode}: no visible teleport`);
  routeReady = true; rejected = false;
  h.update(.5);
  assert.ok(john.path, `${mode}: the recovered planner resumes the return`);
  john.arrive();
  assert.deepEqual([john.e, john.n], [0, 0]);
  assert.equal(john.indoors, mode === 'indoor-return-no-route');
  assert.deepEqual(h.returning, [], `${mode}: ownership ends only at home`);
}
{
  const john = figure('john', { root: { visible: false }, route: [{ local_e: 0, local_n: 0 }, { local_e: 20, local_n: 0 }], state: 'walking' });
  const h = createJauntHosts({ humans: { get: () => john }, router: planned });
  h.sync([{ person: 'john', local_e: 8, local_n: 0 }]);
  john.root.visible = true; h.release();
  const obsoleteReturn = john.path.onArrive;
  h.sync([{ person: 'john', local_e: 12, local_n: 0 }]);
  obsoleteReturn();
  assert.equal(john.jauntHost, true, 'an old return cannot resume the route during a new takeover');
  john.arrive(); h.release(); john.arrive();
  assert.deepEqual([john.e, john.n], [0, 0], 'retaking a returning figure keeps their original everyday origin');
  assert.equal(john.state, 'walking', 'their original route resumes');
}
{
  const john = figure('john');
  const h = createJauntHosts({ humans: { get: () => john }, router: planned });
  const before = figure.greets;
  h.sync([{ person: 'john', local_e: 8, local_n: 0 }], { arrived: true });
  h.sync([], { retain: ['john'], arrived: false });
  john.arrive();
  assert.equal(figure.greets, before, 'a retained guide who arrives after the visitor left does not greet an absent visitor');
  h.release(); john.arrive();
}
console.log('PASS dayless handback survives unavailable/rejected/throwing routes, indoor return and a superseding takeover');

// ---- The real HumanActor path methods expose the guide's actual approach duration.
// Synthetic planner detour: this is CPU state/kinematics proof, not native-world routing or DOM acceptance.
{
  const source = fs.readFileSync(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
  const method = (start, end) => { const a = source.indexOf(start), b = source.indexOf(end, a); assert(a >= 0 && b > a); return source.slice(a, b); };
  const ActualPath = vm.runInNewContext(`(class ActualPath { ${[
    method('  walkPath(points,', '\n  /**'), method('  followPath(dt)', '\n  /** Advance'), method('  turnTo(heading,', '\n  /**'),
  ].join('\n')} })`, { Math, Number,
    PATH_TURN_DEG_S: Number(source.match(/export const PATH_TURN_DEG_S = ([0-9.]+);/)[1]),
    PATH_STAND_TURN_DEG: Number(source.match(/const PATH_STAND_TURN_DEG = ([0-9.]+);/)[1]) });
  for (const hidden of [false, true]) {
    const post = { e: 1395.2, n: -3244.3 }, mark = { e: 1334.82, n: -3211.63 };
    const charles = Object.assign(new ActualPath(), figure('charles', { ...post, root: { visible: !hidden }, body: null, gait: null, walkSpeed: 1.3,
      instance: { behaviour: { day: [{ spans: [{ from: 0, to: 24, indoors: false, activity: 'stand', doing: 'keeping watch', at: { local_e: post.e, local_n: post.n, heading_deg: 90 } }] }] } } }));
    delete charles.walkPath; delete charles.turnTo;
    const humans = { actors: [charles], get: () => charles };
    const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15', visitor: () => mark,
      hostRouter: { plan: (a, b) => ({ points: [[a.e, a.n], [1395.2, -3207], [1334.82, -3207], [b.e, b.n]] }) } });
    days.update(.1);
    const hosts = createJauntHosts({ humans, days });
    const jaunt = structuredClone(fixture('walk'));
    jaunt.stops[0].hosts = []; jaunt.stops[0].people = hidden ? [] : ['charles'];
    jaunt.stops[1].hosts = [{ person: 'charles', local_e: mark.e, local_n: mark.n }];
    let callbacks, firstArrival, readyAt = null, clock = 0;
    const c = createJaunts({ load: async () => jaunt, resolve: x => x, place: () => true, enter: () => true,
      travel: { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go(target, hooks) { callbacks = hooks; return true; } },
      storage: null, showMenu() {}, openDetail() {}, closeDetail() {}, onError(e) { throw e; },
      crowd: { hold(ids) { if (!ids.includes('charles')) charles.root.visible = false; }, restore() {} },
      hosts: { sync(stop, options) { hosts.sync(stop?.hosts ?? [], options); return { waiting: hosts.waiting.length > 0 }; }, release() { hosts.release(); } },
      render(state) { if (state.phase !== 'atStop' || state.stopIndex !== 1) return;
        firstArrival ??= { waiting: state.hostWaiting, distance: Math.hypot(charles.e - mark.e, charles.n - mark.n) };
        if (!state.hostWaiting) readyAt = clock;
      } });
    await c.start(jaunt.id); c.next(); callbacks.onArrive(callbacks.token);
    if (hidden) {
      assert.equal(firstArrival.waiting, false, 'hidden host is prepared before the first destination render');
      assert.equal(firstArrival.distance, 0); assert.equal(readyAt, 0);
    } else {
      assert.equal(firstArrival.waiting, true, 'first arrival render waits instead of presenting the absent guide\'s narration');
      assert(firstArrival.distance > 68);
      for (let i = 0; i < 1300; i++) { if (charles.path) charles.followPath(.05); days.update(.05); hosts.update(.05); clock += .05; }
      assert.equal(c.state.hostWaiting, true, 'the real guide is still approaching after 65 seconds on this synthetic detour');
      assert.equal(readyAt, null);
      while (charles.path && clock < 120) { charles.followPath(.05); days.update(.05); hosts.update(.05); clock += .05; }
      assert.equal(c.state.hostWaiting, false, 'the actual path arrival releases narration');
      assert(readyAt > 79 && readyAt < 80, `actual approach time ${readyAt}`);
      assert.equal(canNext(c.state), true, 'the visitor may continue rather than being trapped waiting');
    }
    c.end();
  }
}
console.log('PASS real-path visible-host narration waits for arrival; hidden handoff is ready in its first render');

console.log('JAUNT HOSTS PASS');
