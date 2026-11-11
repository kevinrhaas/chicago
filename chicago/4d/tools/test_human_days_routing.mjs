// SPDX-License-Identifier: GPL-3.0-or-later
// Real day controller/day-router/full-router controls on a small obstacle fixture.
// The city grid is never allocated here; built/stats prove which calls warm it.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { createRouter } from '../renderers/web/js/route.js';
import { createInteractions } from '../renderers/web/js/interact.js';

const source = await fs.readFile(process.argv[2] ?? new URL('../renderers/web/js/human-days.js', import.meta.url), 'utf8');
const { createHumanDays, createDayRouter, clearWayOf } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const home = 'test_home';
const wall = { id: 'test_wall', pts: [[4, -3], [6, -3], [6, 3], [4, 3]] };
const door = { id: 'test_home:front', step: { local_e: 0, local_n: 0 },
  leaf: { local_e: 0, local_n: 0 }, outward_deg: 90 };
const IN = (from, to) => ({ from, to, indoors: true, where: home });
const OUT = (at, activity = 'work') => ({ from: 8, to: 18, indoors: false,
  at: { local_e: at.e, local_n: at.n, heading_deg: 0 }, activity, doing: activity,
  ...(activity === 'work' ? { spots: [{ local_e: at.e, local_n: at.n }] } : {}) });
const day = (at, activity) => [{ spans: [IN(0, 8), OUT(at, activity), IN(18, 24)] }];

function actor(id, at, behaviour, { scene = '1812', indoors = false } = {}) {
  const a = { id, personId: id, instance: { id, person_id: id, scene, behaviour,
    appearance: { asset_id: 'settler_1812' }, placement: { local_e: at.e, local_n: at.n, heading_deg: 0 } },
    e: at.e, n: at.n, heading: 0, indoors, state: 'standing', path: null,
    root: { visible: true }, walks: [], places: 0,
    setIndoors(on) { this.indoors = !!on; }, setState(s) { this.state = s; },
    place() { this.places++; }, turnTo(h) { this.heading = h; },
    stopPath() { this.path = this.pending = null; },
    walkPath(points, { endHeading = null, onArrive = null } = {}) {
      this.walks.push(points.map(p => ({ ...p }))); this.path = points;
      this.pending = { points, endHeading, onArrive }; return true;
    },
    arrive() {
      if (!this.pending) return;
      const p = this.pending; this.pending = this.path = null;
      this.e = p.points.at(-1).e; this.n = p.points.at(-1).n;
      if (p.endHeading !== null) this.heading = p.endHeading;
      p.onArrive?.();
    },
  };
  return a;
}

function fixture({ blocked = true, target = { e: 10, n: 0 }, at = { e: 0, n: 0 },
  scene = '1812', entries = null, soldier = false, initialHour = 10 } = {}) {
  const footprints = blocked ? [wall] : [];
  const clear = clearWayOf(footprints);
  const full = createRouter({ terrain: { heightfield: { loaded: true, widthM: 30, depthM: 30,
    originE: -10, originN: -10 }, surfaceHeight: () => 0 }, footprints, cell: 1, inflate: .1 });
  let plans = 0, hostPlans = 0;
  const originalPlan = full.plan;
  full.plan = (...args) => { plans++; return originalPlan(...args); };
  const humans = { actors: [], shown: true };
  const a = entries ? null : actor('test_person', at, soldier
    ? { hours: [5.5, 21], quarters: home } : { day: day(target) }, { scene, indoors: soldier });
  if (a) humans.actors.push(a);
  let visitor = { e: 0, n: 0 }, localHour = initialHour;
  const life = createHumanDays({ humans, hour: () => localHour, date: () => '1812-08-14',
    visitor: () => visitor, doors: { structures: [{ structure: home, name: home, doors: [door] }] },
    interactions: createInteractions(), clear,
    router: createDayRouter({ router: () => full, clear, buildWhenBlocked: scene === '1904' }),
    hostRouter: { plan(...args) { hostPlans++; return full.plan(...args); } },
    inside: entries && { people: entries },
    spawn: entries ? entry => {
      const spawned = actor(entry.person, { e: 0, n: 0 }, {}, { scene });
      humans.actors.push(spawned); return spawned;
    } : null,
    despawn: a => { const i = humans.actors.indexOf(a); if (i >= 0) humans.actors.splice(i, 1); },
  });
  const tick = (seconds, arrive = false) => {
    for (let i = 0; i < Math.ceil(seconds / .25); i++) {
      if (arrive) for (const a of [...humans.actors]) a.arrive();
      life.update(.25);
    }
  };
  return { a, humans, life, full, clear, tick,
    get plans() { return plans; }, get hostPlans() { return hostPlans; },
    visitor(p) { visitor = p; }, hour(h) { localHour = h; }, block() { if (!footprints.length) footprints.push(wall); full.invalidate(); } };
}

// A blocked automatic routine must defer, not allocate the full town grid or
// walk a straight chord through the wall. The real guarded router is used.
{
  const f = fixture({ initialHour: 7 }); f.tick(.25); f.a.arrive(); f.a.walks.length = 0; f.hour(10); f.tick(2);
  assert.equal(f.plans, 0, 'a cold automatic routine must not warm the full route grid');
  assert.equal(f.hostPlans, 0); assert.equal(f.full.built, false); assert.equal(f.full.stats.cells, 0);
  assert.equal(f.a.walks.length, 0); assert.deepEqual([f.a.e, f.a.n], [0, 0]);
  assert(f.life.people[0].pendingHostMove, 'the blocked move remains retryable, not falsely arrived');
  // A real user route warms the existing router; the waiting routine then uses
  // its actual safe detour without bypassing the guarded day adapter.
  assert(f.full.plan({ e: 0, n: 0 }, { e: 10, n: 0 }, { mode: 'walk' }));
  f.tick(1); assert(f.a.walks.length > 0); assert.equal(f.hostPlans, 0);
  const path = f.a.walks.at(-1);
  assert(path.some(p => Math.abs(p.n) > 3));
  assert(path.slice(1).every((p, i) => f.clear(path[i], p)), 'the warmed route stays outside the wall');
  f.a.arrive(); assert.equal(f.a.state, 'working', 'the routine resumes its real activity');
}

// Clear automatic work still walks immediately, with no nav allocation.
{
  const f = fixture({ target: { e: 0, n: 10 }, initialHour: 7 }); f.tick(.25); f.a.arrive(); f.a.walks.length = 0; f.hour(10); f.tick(.25);
  assert.equal(f.a.walks.length, 1); assert.equal(f.plans, 0); assert.equal(f.full.built, false);
  f.a.arrive(); assert.equal(f.a.state, 'working');
}

// Automatic household conversations are not visitor requests. Neither their
// first journey nor their retry may bypass the cold-grid guard.
{
  const entries = ['resident_a', 'resident_b'].map(person => ({ person, name: person, home,
    door: door.id, asset_id: 'settler_1812', day: day({ e: 10, n: 0 }, 'talk') }));
  const f = fixture({ entries }); f.tick(2);
  assert.equal(f.life.people.length, 2);
  assert(f.life.people.every(p => p.social && !p.social.visitorRequested));
  assert.equal(f.plans, 0); assert.equal(f.hostPlans, 0); assert.equal(f.full.built, false);
}

// The nearby resident rotation also creates an automatic return override.
// A newly closed obstacle must not turn that override into user intent.
{
  const entries = [{ person: 'resident', name: 'Resident', home, door: door.id,
    asset_id: 'settler_1812', day: day({ e: 10, n: 0 }) }];
  const f = fixture({ blocked: false, entries }); f.tick(2, true);
  assert.equal(f.humans.actors[0].e, 10);
  f.block(); f.tick(122);
  const p = f.life.people[0]; assert(p?.override && !p.override.visitorRequested);
  assert(p.pendingHostMove); assert.equal(f.plans, 0); assert.equal(f.hostPlans, 0);
  assert.equal(f.full.built, false);
}

// Other eras keep their preexisting blocked safe-trip routing policy.
for (const scene of ['1835', '1904']) {
  const f = fixture({ scene, at: { e: 10, n: 0 } }); f.tick(.25);
  assert.equal(f.life.request(f.a.id, null, { inside: 'home' }).ok, true);
  assert(f.hostPlans > 0, `${scene} explicit inside request retains its full blocked route`);
  assert.equal(f.full.built, true);
}
{
  const f = fixture({ scene: '1904', initialHour: 7 });
  f.tick(.25); f.a.arrive(); f.a.walks.length = 0; f.hour(10); f.tick(.25);
  assert(f.plans > 0, '1904 automatic blocked trips retain their warming day-router policy');
  assert.equal(f.full.built, true);
}

// A visitor's explicit Go home keeps real blocked-route access.
{
  const f = fixture({ at: { e: 10, n: 0 } }); f.tick(.25);
  assert.equal(f.life.request(f.a.id, null, { inside: 'home' }).ok, true);
  assert.equal(f.life.people[0].override.visitorRequested, true);
  assert(f.hostPlans > 0); assert.equal(f.full.built, true);
  const path = f.a.walks.at(-1); assert(path.some(p => Math.abs(p.n) > 3));
}

// An explicit door call's return retains ownership after called is cleared,
// including delayed route callbacks, then clears it on the soldier's arrival.
{
  const f = fixture({ blocked: false, soldier: true }); f.visitor({ e: 10, n: 0 }); f.tick(.25);
  assert.equal(f.life.ask(f.a.id).ok, true); f.a.arrive();
  assert(f.a.e > 8); assert.equal(f.full.built, false);
  f.block(); f.visitor({ e: 50, n: 0 }); f.tick(5);
  assert.equal(f.life.people[0].called, null); assert.equal(f.life.people[0].visitorReturn, true);
  assert(f.hostPlans > 0); f.a.arrive(); f.a.arrive();
  assert.equal(f.a.indoors, true); assert.equal(f.life.people[0].visitorReturn, false);
}

// Requested conversations retain explicit ownership for both actual participants
// and their scheduled return; an automatic conversation above stays guarded.
{
  const f = fixture({ target: { e: 0, n: 0 } });
  const q = actor('requested_neighbour', { e: 10, n: 0 }, { day: day({ e: 10, n: 0 }) });
  f.humans.actors.push(q); f.tick(.25);
  assert.equal(f.life.request(f.a.id, 'chat').ok, true);
  assert(f.life.people.every(p => p.social?.visitorRequested));
  assert(f.hostPlans > 0, 'a requested partner may use the full blocked route');
  f.a.arrive(); q.arrive(); f.tick(.25);
  const calls = f.hostPlans; f.tick(61);
  assert(f.life.people.every(p => !p.social));
  assert(f.hostPlans > calls, 'the requested conversation retains its blocked return route');
  q.arrive(); q.arrive(); assert.equal(f.life.people.find(p => p.actor === q).visitorReturn, false);
}

// Expiring a real outdoor request transfers ownership before clearing override.
// A newly closed obstacle on the return may build a genuinely requested route.
{
  const f = fixture({ blocked: false, target: { e: 0, n: 0 } });
  const far = { ...OUT({ e: 10, n: 0 }), from: 12, doing: 'far work' };
  f.a.instance.behaviour.day[0].spans[1].to = 12;
  f.a.instance.behaviour.day[0].spans.splice(2, 0, far); f.tick(.25);
  assert.equal(f.life.request(f.a.id, 1).ok, true); f.a.arrive();
  assert.equal(f.a.e, 10); assert.equal(f.full.built, false);
  f.block(); f.tick(301);
  assert.equal(f.life.people[0].override, null); assert.equal(f.life.people[0].visitorReturn, true);
  assert(f.hostPlans > 0); f.a.arrive(); assert.equal(f.life.people[0].visitorReturn, false);
}

// A real host handback keeps full-router priority even when goIn/phaseTo has
// also set safeRoutineTravel. A declared camera cut remains allocation-free.
{
  const f = fixture({ blocked: false, target: { e: 0, n: 0 } }); f.tick(.25);
  assert.equal(f.life.host(f.a.id, { e: 10, n: 0 }, { safeTravel: true }).ok, true);
  assert.equal(f.hostPlans, 1); f.a.arrive(); f.life.unhost(f.a.id); f.tick(.25);
  assert(f.hostPlans >= 2, 'real host handback is not demoted to the routine shortcut');
  f.a.arrive(); assert.equal(f.life.people[0].safeHostTravel, false);
  const cut = fixture(); cut.tick(.25);
  assert.equal(cut.life.host(cut.a.id, { e: 10, n: 0 }, { safeTravel: true, atCut: true }).ok, true);
  assert.equal(cut.hostPlans, 0); assert.equal(cut.full.built, false);
}

console.log('human days routing: cold automatic work/social/return guarded; clear work, warmed detours, explicit request/call/host and cut handoffs PASS');
