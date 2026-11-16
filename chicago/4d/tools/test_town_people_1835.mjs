// SPDX-License-Identifier: GPL-3.0-or-later
// T-3556 (owner, 2026-11-15: "fill out the 1835 people, include their ability to enter and exit
// their homes or places of business and add all interactions with them as possible"). The 1835
// town's residents (data/humans/inside_1835.json, tools/town_people_1835.py) as the day engine
// (renderers/web/js/human-days.js) plays them, with stand-in actors, the real interact.js and the
// real data/humans/doors_1835.json. It must:
//   - read every templated day whole (0-24 h, summer and winter), each span `where` their home or
//     their place of business, each place outside a door one of their own points;
//   - give every home and place of business a door, and every person a body the 1835 town draws;
//   - offer Ask for someone at their HOME door while the hour has them home, and at their place of
//     business's door (and not at home) while it has them at work; asked there, they come out of it;
//   - offer Greet, Go inside, Go home and Go to work to someone out, and go in at work when asked;
//   - bring several of them out about the visitor at once, up to the scene's number, never more;
//   - and bring someone at home out for Find (homeNow), at the door of where they are now.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const { createHumanDays, expandInside, dayOn, spanAt } = await import(data(await js('human-days.js')));
const { createInteractions } = await import('../renderers/web/js/interact.js');
const json = async (rel) => JSON.parse(await fs.readFile(new URL(rel, here), 'utf8'));
const doors = await json('data/humans/doors_1835.json');
const raw = await json('data/humans/inside_1835.json');
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };
const SUMMER = '1835-07-01', WINTER = '1835-01-15';

// ── the file, read whole ──
const inside = expandInside(structuredClone(raw));
assert(inside.people.length > 2000, `the town's people are there (${inside.people.length})`);
assert(inside.care.length > 100, `and its infants in household care (${inside.care.length})`);
const byStructure = new Map(doors.structures.map((r) => [r.structure, r]));
const bodies = new Set((await fs.readdir(new URL('assets/humans/web/', here))).filter((f) => f.endsWith('.lod0.glb')).map((f) => f.replace('.lod0.glb', '')));
const looks = (await json('data/humans/variation/looks_1835_town.json')).persons;
const dress = (await json('data/humans/variation/dress_1835_town.json')).persons;
let atWork = 0;
for (const e of inside.people) {
  assert(byStructure.get(e.home)?.doors.some((d) => d.id === e.door), `${e.person}: their home ${e.home} has the door ${e.door}`);
  if (e.work) {
    atWork++;
    assert(byStructure.get(e.work)?.doors.some((d) => d.id === e.work_door), `${e.person}: their place of business ${e.work} has its door`);
  }
  assert(bodies.has(e.asset_id), `${e.person}: drawn on a body that is built (${e.asset_id})`);
  assert(looks[e.person] && dress[e.person], `${e.person}: their own looks and dress`);
  assert.equal(e.provenance?.liberty, 'L-town-people-1835', `${e.person}: the file's provenance under their own`);
  for (const date of [SUMMER, WINTER]) {
    const day = dayOn(e, date, e.person);
    assert(day?.spans?.length, `${e.person}: a day on ${date}`);
    let t = 0;
    for (const s of day.spans) {
      assert.equal(s.from, t, `${e.person} ${date}: the day is whole at ${t}`);
      assert(s.to > s.from, `${e.person} ${date}: a span has length`);
      t = s.to;
      if (s.indoors && !s.away) assert([e.home, e.work].includes(s.where), `${e.person}: indoors at home or at their place of business, not ${s.where}`);
      if (!s.indoors) {
        assert(Number.isFinite(s.at?.local_e) && Number.isFinite(s.at?.local_n), `${e.person}: out at one of their points`);
        if (s.activity === 'walk') assert(Number.isFinite(s.to_point?.local_e), `${e.person}: a walk has its far end`);
      }
    }
    assert.equal(t, 24, `${e.person} ${date}: to midnight`);
  }
  assert.equal(dayOn(e, SUMMER, e.person), dayOn(e, SUMMER, e.person), 'a day read twice is the same day (kept)');
}
assert(atWork >= 20, `people go to a place of business of their own (${atWork})`);
const noon = inside.people.filter((e) => !spanAt(dayOn(e, SUMMER, e.person), 12.5).indoors).length;
assert(noon > inside.people.length * 0.2, `at the scene's half past twelve many are out of doors (${noon})`);

// ── stand-in actors ──
function actorOf(entry, door) {
  const a = {
    id: `hi_inside_${entry.person}`, personId: entry.person, instance: { scene: '1835', appearance: { asset_id: entry.asset_id } },
    person: { name: entry.name }, e: door.step.local_e, n: door.step.local_n, heading: door.outward_deg, state: 'standing',
    indoors: true, inRange: true, path: null, walks: [], greets: 0,
    place() {}, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; }, turnTo(h) { a.heading = h; },
    root: { getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    life: { attend() {}, nod() {} },
    actions: { talking: false, setTalk(on) { a.actions.talking = !!on; }, greet() { a.greets++; }, hold() {} },
    walkPath(pts, { endHeading = null, onArrive = null } = {}) {
      a.walks.push(pts.map((p) => [p.e, p.n]));
      a.pending = { end: pts.at(-1), endHeading, onArrive, t: 0.5 };
      a.state = 'walking';
      return true;
    },
  };
  return a;
}
function town({ hour, visitor, residentsNear = 4 }) {
  const actors = [];
  const humans = { actors, shown: true };
  const ix = createInteractions();
  const built = [];
  const problems = [];
  const life = createHumanDays({ humans, three, hour: () => hour.at, date: () => SUMMER, doors, interactions: ix,
    visitor: () => visitor.at, inside: expandInside(structuredClone(raw)), residentsNear, problems,
    spawn(entry, door) { const a = actorOf(entry, door); actors.push(a); built.push(entry.person); return a; },
    despawn(a) { const i = actors.indexOf(a); if (i >= 0) actors.splice(i, 1); } });
  const step = (n, dt = 0.1) => { for (let i = 0; i < n; i++) {
    for (const a of [...actors]) {
      if (!a.pending) continue;
      a.pending.t -= dt;
      if (a.pending.t <= 0) { const q = a.pending; a.pending = null; a.e = q.end.e; a.n = q.end.n; a.state = 'standing'; q.onArrive?.(a); }
    }
    life.update(dt); ix.update(dt);
  } };
  return { actors, ix, life, built, problems, step, humans };
}
const asks = (ix, id) => ix.actionsOf(ix.get(`door:${id}`)).map((a) => a.id);

// Someone with a place of business: at business at ten, at dinner at home at a quarter to one.
const worker = inside.people.find((e) => e.work && e.routine === 'gentleman') ?? inside.people.find((e) => e.work);
const wDay = dayOn(worker, SUMMER, worker.person);
const workHour = wDay.spans.find((s) => s.indoors && s.where === worker.work);
const homeHour = wDay.spans.find((s) => s.indoors && s.where === worker.home && s.from > 6);
{
  const hour = { at: (workHour.from + workHour.to) / 2 }, visitor = { at: null };
  const t = town({ hour, visitor });
  t.step(2);
  assert.deepEqual(t.problems, [], 'every building of theirs has a door');
  assert(asks(t.ix, worker.work_door).includes(`ask:${worker.person}`), `${worker.name} is asked for at their place of business while at work`);
  assert(!asks(t.ix, worker.door).includes(`ask:${worker.person}`), 'and not at home then');
  assert.equal(t.life.homeNow(worker.person)?.structure, worker.work, 'Find brings them out of where they are now');
  const workDoor = byStructure.get(worker.work).doors.find((d) => d.id === worker.work_door);
  visitor.at = { e: workDoor.step.local_e + 3, n: workDoor.step.local_n };
  t.ix.act(t.ix.get(`door:${worker.work_door}`), `ask:${worker.person}`);
  t.step(40);
  assert(t.built.includes(worker.person), 'asked for there, they are built');
  const a = t.actors.find((x) => x.personId === worker.person);
  assert.equal(a.indoors, false, 'and come out');
  assert(Math.hypot(a.walks[0][0][0] - workDoor.step.local_e, a.walks[0][0][1] - workDoor.step.local_n) < 1.5, 'out of the door of their place of business');
  const offers = t.ix.actionsOf(t.ix.get(`person:${a.id}`)).map((x) => x.id);
  for (const id of ['greet', 'go_inside', 'go_home', 'go_work']) assert(offers.includes(id), `out, ${worker.name} can be asked to ${id} (${offers})`);
  t.ix.act(t.ix.get(`person:${a.id}`), 'go_work');
  t.step(60);
  assert(a.indoors || t.actors.indexOf(a) < 0, 'asked to go to work, they go in');
  assert.equal(t.life.homeNow(worker.person)?.structure, worker.work, 'at their place of business, where Find would bring them out');
  hour.at = (homeHour.from + homeHour.to) / 2;
  visitor.at = null;
  t.step(10);
  assert(t.life.homeNow(worker.person) == null || t.life.homeNow(worker.person).structure === worker.home, 'at dinner they are at home');
}
{
  const t = town({ hour: { at: (homeHour.from + homeHour.to) / 2 }, visitor: { at: null } });
  t.step(2);
  assert(asks(t.ix, worker.door).includes(`ask:${worker.person}`), `${worker.name} is asked for at home while the hour has them home`);
  assert(!asks(t.ix, worker.work_door).includes(`ask:${worker.person}`), 'and not at their place of business then');
}

// About the visitor at half past twelve, several townspeople come out of their doors, never more
// than the scene's number at once.
{
  // The street with the most houses whose people are out then (each door lets out one at a time).
  const out = new Map();
  for (const e of inside.people) {
    const s = spanAt(dayOn(e, SUMMER, e.person), 12.5);
    if (!s.indoors) out.set(e.door, s.at);
  }
  const ats = [...out.values()];
  const around = (p) => ats.filter((q) => Math.hypot(q.local_e - p.local_e, q.local_n - p.local_n) < 35).length;
  const step = ats.reduce((best, p) => (around(p) > around(best) ? p : best), ats[0]);
  const t = town({ hour: { at: 12.5 }, visitor: { at: { e: step.local_e, n: step.local_n } }, residentsNear: 5 });
  let most = 0;
  for (let i = 0; i < 120; i++) { t.step(10, 0.1); most = Math.max(most, t.actors.length); }
  assert(most >= 3, `several are out about the visitor (${most})`);
  assert(most <= 5, `never more than the scene's number at once (${most})`);
  assert(t.actors.every((a) => !a.disposed), 'the ones out are live figures');
}
// T-3553 (the owner, 2026-11-16: "make sure there are people present ... in scene of jaunt all
// eras"): at a jaunt stop with no stage or hosts the people about its stand stay out; where none
// are out (the small hours), some of those at home near it come out of their own doors, adults,
// up to the stop's number, and a jaunt holding everyone (a staged stop) brings nobody out.
{
  const { JAUNT_LOCALS } = await import(data(await js('human-days.js')));
  const at3 = inside.people.filter((e) => spanAt(dayOn(e, SUMMER, e.person), 3).indoors).length;
  assert.equal(at3, inside.people.length, 'at three in the morning everyone is in');
  // A stand among the most houses.
  const steps = [...byStructure.values()].flatMap((s) => s.doors.map((d) => ({ structure: s.structure, e: d.step.local_e, n: d.step.local_n })));
  const homes = new Set(inside.people.map((e) => e.home));
  const near = (p) => steps.filter((q) => homes.has(q.structure) && Math.hypot(q.e - p.e, q.n - p.n) < JAUNT_LOCALS.door_m).length;
  const stand = steps.reduce((best, p) => (near(p) > near(best) ? p : best), steps[0]);
  const run = () => town({ hour: { at: 3 }, visitor: { at: { e: stand.e + 4, n: stand.n } }, residentsNear: 4 });
  for (const [label, area] of [['staged', null], ['plain', { e: stand.e + 4, n: stand.n, r: JAUNT_LOCALS.r_m, structure: stand.structure }]]) {
    const t = run();
    const humans = t.humans;
    humans.crowdKept = []; humans.crowdArea = area;
    humans.keeps = (id, e, n) => !!area && Number.isFinite(e) && Math.hypot(e - area.e, n - area.n) <= area.r;
    humans.isHeld = (a) => !humans.keeps(a.personId, a.e, a.n);
    for (let i = 0; i < 40; i++) t.step(10, 0.1);
    const out = t.actors.filter((a) => !a.indoors);
    if (!area) { assert.equal(out.length, 0, 'a staged stop holds the town: nobody comes out'); continue; }
    assert(out.length >= JAUNT_LOCALS.min_full, `a quiet stop has people about it (${out.length})`);
    if (process.env.QA_VERBOSE) console.log(out.map((a) => `${a.person.name} ${a.state} ${Math.hypot(a.e - area.e, a.n - area.n).toFixed(1)} m`));
    for (const a of out) {
      assert(!/(^|_)(child|boy|girl|toddler)(_|$)/.test(a.instance.appearance.asset_id ?? ''), `${a.person.name}: an adult is called out`);
      assert(Math.hypot(a.e - area.e, a.n - area.n) <= area.r, `${a.person.name} stays about the stand`);
    }
    const offers = t.ix.actionsOf(t.ix.get(`person:${out[0].id}`)).map((x) => x.id);
    assert(offers.includes('greet'), `one called out can be greeted (${offers})`);
  }
  // A stand with no door near it: those called out from further off walk an errand toward it.
  {
    const far = { e: stand.e + 45, n: stand.n, r: JAUNT_LOCALS.r_m, structure: null };
    const t = town({ hour: { at: 3 }, visitor: { at: { e: far.e, n: far.n } }, residentsNear: 4 });
    const humans = t.humans;
    humans.crowdKept = []; humans.crowdArea = far;
    humans.keeps = (id, e, n) => Number.isFinite(e) && Math.hypot(e - far.e, n - far.n) <= far.r;
    humans.isHeld = (a) => !humans.keeps(a.personId, a.e, a.n);
    let errand = 0;
    for (let i = 0; i < 40; i++) { t.step(10, 0.1); errand = Math.max(errand, t.actors.filter((a) => !a.indoors && a.walks.some((w) => Math.hypot(w.at(-1)[0] - far.e, w.at(-1)[1] - far.n) < JAUNT_LOCALS.errand_m + 1)).length); }
    assert(t.actors.filter((a) => !a.indoors).length >= 1, 'a stand away from the doors still has people about it');
    if (process.env.QA_VERBOSE) console.log('errands toward a far stand:', errand);
  }
}
console.log(`1835 town people: ${inside.people.length} people and ${inside.care.length} in care, ${atWork} with a place of business; days whole in summer and winter, asked for at home or at work by the hour, out of the right door, several about the visitor and no more than the scene's number`);
