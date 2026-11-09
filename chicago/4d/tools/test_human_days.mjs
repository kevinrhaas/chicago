// SPDX-License-Identifier: GPL-3.0-or-later
// T-3463..T-3467: a person's day and asking at a door (renderers/web/js/human-days.js), with
// stand-in actors, the real interact.js engine and the real data/humans/doors_1812.json. It must:
// read dates and spans as the schema has them; keep someone off their dates nowhere (Jean
// Lalime gone on 14 August, there in February); put each person indoors or out at each hour's
// place, walking out of the door near the visitor and put there far off; keep a talk going with
// one speaker at a time; take a worker between his spots; let a door offer Ask for each person
// in its building (and a Knock when no one is), bring the one asked for out at the door and up
// to the visitor, and back in once the visitor walks off; do the same for a soldier in quarters,
// whom human-duties.js then leaves alone; and every building a record puts anyone in has a door.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const days = await import(data(await js('human-days.js')));
const { createHumanDays, onDate, spanAt, dayOn, inSpan, chanceDay, AWAY_DAY, ASK_PAGE, STAY_M, LEAVE_S, NEAR_M } = days;
const { createHumanDuties } = await import(data(await js('human-duties.js')));
const { createInteractions } = await import(data(await js('interact.js')));
const doors = JSON.parse(await fs.readFile(new URL('data/humans/doors_1812.json', here), 'utf8'));
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };

// ── dates and spans ──
assert.equal(onDate('1812-08-14', { to: '1812-06-17' }), false, 'after the window');
assert.equal(onDate('1812-02-15', { to: '1812-06-17' }), true, 'inside the window');
assert.equal(onDate('1812-06-17', { to: '1812-06-17' }), true, 'the window is inclusive');
assert.equal(onDate('1812-08-14', { from: '1812-08-13' }), true);
assert.equal(onDate(null, { from: '1812-08-13' }), true, 'no date known: present');
assert.equal(inSpan(23, { from: 21, to: 5.5 }), true, 'a span may pass midnight');
assert.equal(inSpan(3, { from: 21, to: 5.5 }), true);
assert.equal(inSpan(12, { from: 21, to: 5.5 }), false);
const twoDays = { day: [{ dates: { to: '1812-04-06' }, spans: [{ from: 0, to: 24, indoors: true, where: 'kinzie_house_1812' }] },
  { spans: [{ from: 0, to: 24, indoors: true, where: 'first_fort_outer_agents_house' }] }] };
assert.equal(spanAt(dayOn(twoDays, '1812-02-15'), 10).where, 'kinzie_house_1812', 'the first variant whose dates hold');
assert.equal(spanAt(dayOn(twoDays, '1812-08-14'), 10).where, 'first_fort_outer_agents_house', 'else the undated one');
// Months over a run of years; a day that comes only so often (seeded, about the share asked).
assert.equal(onDate('1812-02-15', { months: [12, 1, 2, 3] }), true, 'a winter month');
assert.equal(onDate('1812-08-14', { months: [12, 1, 2, 3] }), false, 'not a winter month');
assert.equal(onDate('1812-02-15', { months: [2], years: { from: 1803, to: 1811 } }), false, 'outside the run of years');
assert.equal(onDate('1810-02-15', { months: [2], years: { from: 1803, to: 1811 } }), true);
const visits = { day: [{ dates: { from: '1812-04-01', to: '1812-07-05' }, chance: 0.2, spans: [OUTq(0, 24)] }] };
function OUTq(from, to) { return { from, to, indoors: false, at: { local_e: 1088, local_n: 236, heading_deg: 0 }, activity: 'stand' }; }
let came = 0;
for (let d = 1; d <= 30; d++) {
  const date = `1812-06-${String(d).padStart(2, '0')}`;
  const v = dayOn(visits, date, 'potawatomi_x');
  assert.equal(v, dayOn(visits, date, 'potawatomi_x'), 'the same day on every load');
  if (v !== AWAY_DAY) came++;
  else assert.equal(spanAt(v, 10).away, true, 'on the other days, away');
}
assert(came >= 2 && came <= 12, `about one day in five comes (${came} of 30)`);
assert.equal(chanceDay('x', '1812-06-01', 1), true, 'a chance of 1 always comes');

// ── stand-in actors ──
function actorOf(rec, name) {
  const a = {
    id: rec.id, personId: rec.person_id, instance: rec, person: { name }, identity: { kind: 'person', person: { name } },
    e: rec.placement.local_e, n: rec.placement.local_n, heading: rec.placement.heading_deg, state: 'standing',
    indoors: false, inRange: true, path: null, walks: [], greets: 0, looks: 0, nods: 0,
    place() {}, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; },
    turnTo(h) { a.heading = h; },
    root: { getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    life: { attend() { a.looks++; }, nod() { a.nods++; } },
    actions: { talking: false, setTalk(on) { a.actions.talking = !!on; }, greet() { a.greets++; }, hold() {} },
    walkPath(pts, { endHeading = null, onArrive = null } = {}) {
      a.walks.push(pts.map((p) => [p.e, p.n]));
      a.pending = { end: pts.at(-1), endHeading, onArrive, t: 1 };
      a.state = 'walking';
      return true;
    },
  };
  return a;
}
const rec = (id, behaviour, at = [1150, 221, 0]) => ({ id: `hi_${id}`, person_id: id, scene: '1812',
  placement: { local_e: at[0], local_n: at[1], heading_deg: at[2] }, behaviour: { state: 'standing', ...behaviour } });
const OUT = (from, to, e, n, h, extra = {}) => ({ from, to, indoors: false, at: { local_e: e, local_n: n, heading_deg: h }, ...extra });
const IN = (from, to, where) => ({ from, to, indoors: true, where });

const lalime = actorOf(rec('lalime_jean', { presence: { to: '1812-06-17' },
  day: [{ spans: [IN(0, 6, 'lalime_house_1812'), OUT(6, 20, 1103, 347, 0, { activity: 'work', spots: [{ local_e: 1105, local_n: 348 }] }), IN(20, 24, 'lalime_house_1812')] }] }), 'Jean Lalime');
const kinzie = actorOf(rec('kinzie_john_elder', { ask_order: 1,
  day: [{ spans: [IN(0, 7, 'kinzie_house_1812'), OUT(7, 12, 1150, 332, 180, { activity: 'talk', knot: 'bank' }), IN(12, 24, 'kinzie_house_1812')] }] }), 'John Kinzie');
const eleanor = actorOf(rec('kinzie_eleanor', { ask_order: 2,
  day: [{ spans: [IN(0, 7, 'kinzie_house_1812'), OUT(7, 12, 1151, 331, 0, { activity: 'talk', knot: 'bank' }), IN(12, 24, 'kinzie_house_1812')] }] }), 'Eleanor Kinzie');
const walker = actorOf(rec('walker_x', { day: [{ spans: [OUT(0, 24, 1120, 300, 90, { activity: 'walk', to_point: { local_e: 1130, local_n: 300 } })] }] }), 'A walker');
const soldier = actorOf(rec('needs_john', { hours: [5.5, 21], quarters: 'first_fort_dearborn_soldiers_barracks_se',
  duty: { kind: 'beat', to: { local_e: 1158, local_n: 215 } } }, [1155, 215, 0]), 'John Needs');
const once = actorOf(rec('carrier_x', { day: [{ spans: [OUT(0, 24, 1120, 290, 90, { activity: 'walk', once: true,
  via: [{ local_e: 1125, local_n: 292 }], to_point: { local_e: 1130, local_n: 290 } })] }] }), 'A carrier');
const actors = [lalime, kinzie, eleanor, walker, once, soldier];
const humans = { actors, shown: true };

let hour = 10, date = '1812-08-14';
let visitor = { e: 1152, n: 326 };
const interactions = createInteractions();
const problems = [];
const life = createHumanDays({ humans, three, hour: () => hour, date: () => date, doors, interactions, visitor: () => visitor, problems });
const duties = createHumanDuties({ humans, three, hour: () => hour, held: (a) => life.isCalled(a) });
function tick(dt = 0.1, n = 1) {
  for (let i = 0; i < n; i++) {
    for (const a of actors) {
      if (!a.pending) continue;
      a.pending.t -= dt;
      if (a.pending.t <= 0) { const p = a.pending; a.pending = null; a.e = p.end.e; a.n = p.end.n; a.heading = p.endHeading ?? a.heading; a.state = 'standing'; p.onArrive?.(a); }
    }
    duties.update(dt);
    life.update(dt);
    interactions.update(dt);
  }
}
tick(0.1, 30);
assert.deepEqual(problems, [], 'every building in the stand-ins has a door');
const snap = () => Object.fromEntries(life.snapshot().map((s) => [s.person, s]));

// Lalime: gone on 14 August, nowhere and not asked for.
assert.equal(snap().lalime_jean.absent, true, 'Lalime is not in the town on 14 August');
assert.equal(lalime.indoors, true);
const lalimeDoor = interactions.get('door:lalime_house_1812:front');
assert(lalimeDoor, 'the Lalime house door is an Interact thing');
assert.deepEqual(interactions.actionsOf(lalimeDoor).map((a) => a.id), ['knock'], 'no one to ask for at his door on 14 August');

// The Kinzies out on the bank at ten, talking: one speaker at a time.
assert.equal(kinzie.indoors, false); assert.equal(eleanor.indoors, false);
assert.equal(snap().kinzie_john_elder.mode, 'out');
let talkers = 0, both = 0;
for (let i = 0; i < 200; i++) { tick(0.1); const n = [kinzie, eleanor].filter((a) => a.actions.talking).length; talkers += n; if (n > 1) both++; }
assert(talkers > 50, 'the two talk'); assert.equal(both, 0, 'never both at once');
assert(kinzie.looks + eleanor.looks > 2, 'they look at each other');

// The walker goes to and fro.
assert(walker.walks.length >= 2, 'a walker walks between his ends');
// A path walked once: by its point, to its end, and there he stands.
assert.deepEqual([once.e, once.n], [1130, 290], 'the carrier is at the end of his path');
assert.equal(once.walks.length, 3, 'to the start of his path, then its two legs');
assert.equal(once.walks[1].at(-1)[0], 1125, 'by the point on the way');
assert.equal(snap().carrier_x.mode, 'out');

// Noon: the Kinzies go in by their own door (near the visitor, so walking).
hour = 12.5;
const before = kinzie.walks.length;
tick(0.1, 60);
assert(kinzie.walks.length > before, 'Kinzie walks to his door');
assert.equal(kinzie.indoors, true, 'and is in');
assert.equal(snap().kinzie_john_elder.inside, 'kinzie_house_1812');

// At the Kinzie door: Ask for each of them, John first.
const kdoor = interactions.get('door:kinzie_house_1812:door2') ?? interactions.get('door:kinzie_house_1812:front');
const asks = interactions.actionsOf(kdoor).map((a) => a.label);
assert.deepEqual(asks.slice(0, 2), ['Ask for John Kinzie', 'Ask for Eleanor Kinzie'], `the door offers both, in order: ${asks}`);
visitor = { e: kdoor.at[0] + 4, n: kdoor.at[1] - 3 };
assert.equal(interactions.act(kdoor).ok, true);
tick(0.1, 30);
assert.equal(kinzie.indoors, false, 'asked for, he comes out');
assert.equal(life.isCalled(kinzie), true);
tick(0.1, 30);
const gap = Math.hypot(kinzie.e - visitor.e, kinzie.n - visitor.n);
assert(gap > 0.8 && gap < 2.2, `he stops short of the visitor (${gap.toFixed(2)} m)`);
assert(kinzie.greets >= 1, 'and greets them');
assert(!interactions.actionsOf(kdoor).some((a) => a.label === 'Ask for John Kinzie'), 'he is no longer offered while out');
// The visitor walks off; he goes back in.
visitor = { e: visitor.e + STAY_M + 10, n: visitor.n };
tick(0.1, Math.ceil(LEAVE_S / 0.1) + 80);
assert.equal(life.isCalled(kinzie), false);
visitor = { e: kdoor.at[0] + 4, n: kdoor.at[1] - 3 };
tick(0.1, 80);
assert.equal(kinzie.indoors, true, 'and once let go he is back in');

// Far off, no one walks: put straight where the hour has them.
visitor = { e: 0, n: 0 };
hour = 8;
const walksBefore = kinzie.walks.length;
tick(0.1, 3);
assert.equal(kinzie.indoors, false);
assert.equal(kinzie.walks.length, walksBefore, 'far from the visitor he is put, not walked');
// T-3505: at his talk's place or at his own job between its gatherings, a few metres off.
assert(Math.hypot(kinzie.e - 1150, kinzie.n - 332) < 8, `put at his round (${kinzie.e}, ${kinzie.n})`);
assert(NEAR_M > 40);

// February: Lalime is at his work by his house, and in at night, asked for at his door.
date = '1812-02-15';
hour = 10;
tick(0.1, 3);
assert.equal(snap().lalime_jean.absent, false, 'in February Lalime is in the town');
assert.equal(lalime.indoors, false);
assert.equal(lalime.state, 'working');
hour = 22;
tick(0.1, 3);
assert.equal(lalime.indoors, true);
assert.deepEqual(interactions.actionsOf(lalimeDoor).map((a) => a.label), ['Ask for Jean Lalime']);

// A soldier in quarters at night is asked for at his barracks' door; his duty leaves him be.
date = '1812-08-14';
hour = 23;
tick(0.1, 3);
assert.equal(soldier.indoors, true, 'in quarters at night');
const bdoor = interactions.get('door:first_fort_dearborn_soldiers_barracks_se:front');
assert(interactions.actionsOf(bdoor).some((a) => a.label === 'Ask for John Needs'));
visitor = { e: bdoor.at[0], n: bdoor.at[1] + 5 };
interactions.act(bdoor, 'ask:needs_john');
tick(0.1, 60);
assert.equal(soldier.indoors, false, 'he comes out at night when asked for');
assert.equal(life.isCalled(soldier), true);
tick(0.1, 20);
assert.equal(soldier.indoors, false, 'and human-duties.js does not send him back in while he is called');
visitor = { e: visitor.e + 40, n: visitor.n };
tick(0.1, 200);
assert.equal(soldier.indoors, true, 'let go, he goes back in');

// Paging: more than ASK_PAGE people inside get Others inside….
{
  const many = Array.from({ length: ASK_PAGE + 3 }, (_, i) => actorOf(rec(`man_${i}`, { hours: [5.5, 21], quarters: 'first_fort_dearborn_soldiers_barracks_sw' }), `Man ${String(i).padStart(2, '0')}`));
  const ix = createInteractions();
  const h2 = { actors: many, shown: true };
  const l2 = createHumanDays({ humans: h2, three, hour: () => 23, date: () => '1812-08-14', doors, interactions: ix, visitor: () => null });
  const d2 = createHumanDuties({ humans: h2, three, hour: () => 23, held: (a) => l2.isCalled(a) });
  d2.update(0.1); l2.update(0.1);
  const door = ix.get('door:first_fort_dearborn_soldiers_barracks_sw:front');
  const first = ix.actionsOf(door).map((a) => a.label);
  assert.equal(first.length, ASK_PAGE + 1);
  assert.equal(first.at(-1), 'Others inside…');
  ix.act(door, 'others'); ix.update(0.1);
  const second = ix.actionsOf(door).map((a) => a.label);
  assert(second.includes('Ask for Man 08'), `the next page: ${second}`);
}

// Inside only: carded people with no figure are offered at their lodge's door, built when asked
// for, and taken away again once they have gone back in.
{
  const camp = 'potawatomi_camp_1812_middle';
  const inside = { people: [
    { person: 'gathering_a', name: 'A Potawatomi woman', home: camp, door: `${camp}:lodge3` },
    { person: 'gathering_b', name: 'A Potawatomi man', home: camp, door: `${camp}:lodge3`, presence: { from: '1812-08-13' } },
    { person: 'gathering_c', name: 'A Potawatomi boy', home: camp },
    { person: 'gathering_late', name: 'A late comer', home: camp, door: `${camp}:lodge3`, presence: { from: '1812-08-20' } },
  ] };
  const h3 = { actors: [], shown: true };
  const ix = createInteractions();
  const built = [], gone = [];
  let v3 = null;
  const spawn = (entry, door) => {
    const a = actorOf(rec(entry.person, {}, [door.step.local_e, door.step.local_n, door.outward_deg]), entry.name);
    a.indoors = true;
    built.push(entry.person);
    h3.actors.push(a);
    return a;
  };
  const despawn = (a) => { gone.push(a.personId); h3.actors.splice(h3.actors.indexOf(a), 1); };
  const l3 = createHumanDays({ humans: h3, three, hour: () => 12, date: () => '1812-08-14', doors, interactions: ix,
    visitor: () => v3, inside, spawn, despawn });
  const step3 = (n) => { for (let i = 0; i < n; i++) {
    for (const a of h3.actors) {
      if (!a.pending) continue;
      a.pending.t -= 0.1;
      if (a.pending.t <= 0) { const q = a.pending; a.pending = null; a.e = q.end.e; a.n = q.end.n; a.state = 'standing'; q.onArrive?.(a); }
    }
    l3.update(0.1); ix.update(0.1);
  } };
  step3(1);
  const lodge3 = ix.get(`door:${camp}:lodge3`);
  assert(lodge3, 'the lodge door is an Interact thing with no figure drawn in it');
  assert.deepEqual(ix.actionsOf(lodge3).map((a) => a.label), ['Ask for A Potawatomi man', 'Ask for A Potawatomi woman'],
    'those at this lodge on this date, and no one not yet come');
  const cDoors = l3.doors.filter((t) => t.structure === camp && ix.actionsOf(t).some((a) => a.label === 'Ask for A Potawatomi boy'));
  assert.equal(cDoors.length, 1, 'one with no door named answers at one door of the camp, picked by their id');
  assert.deepEqual(built, [], 'nothing is built until someone is asked for');
  v3 = { e: lodge3.at[0], n: lodge3.at[1] + 5 };
  ix.act(lodge3, 'ask:gathering_a');
  step3(40);
  assert.deepEqual(built, ['gathering_a'], 'asked for, she is built');
  const her = h3.actors[0];
  assert.equal(her.indoors, false, 'and comes out');
  assert(her.greets >= 1, 'and greets the visitor');
  assert.deepEqual(ix.actionsOf(lodge3).map((a) => a.label), ['Ask for A Potawatomi man'], 'she is no longer offered while out');
  v3 = { e: v3.e + 40, n: v3.n };
  step3(300);
  assert.deepEqual(gone, ['gathering_a'], 'let go, she goes back in and her figure is taken away');
  assert.equal(h3.actors.length, 0);
  assert.equal(l3.insideOnly.out, 0);
  assert.deepEqual(ix.actionsOf(lodge3).map((a) => a.label), ['Ask for A Potawatomi man', 'Ask for A Potawatomi woman'], 'and is offered again');
  assert.equal(l3.ask('gathering_late').ok, false, 'not here before the date');
  assert.equal(l3.ask('gathering_b').ok, true, 'asked for by the harness too');
  step3(5);
  assert.equal(l3.insideOnly.out, 1);
  // With no spawn, nothing is offered for them.
  const ix4 = createInteractions();
  const l4 = createHumanDays({ humans: { actors: [], shown: true }, three, hour: () => 12, date: () => '1812-08-14', doors, interactions: ix4, inside });
  l4.update(0.1);
  assert(!ix4.get(`door:${camp}:lodge3`), 'no spawn: no door for them');
}

// Every building a 1812 record puts anyone in has a door.
const dir = new URL('data/humans/instances/1812/', here);
const index = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
const records = await Promise.all(index.instances.map(async (id) => JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8'))));
const withDoor = new Set(doors.structures.map((s) => s.structure));
const want = new Set();
for (const r of records) {
  const b = r.behaviour ?? {};
  if (b.quarters) want.add(b.quarters);
  for (const v of b.day ?? []) {
    let hours = 0;
    for (const s of v.spans) {
      if (s.indoors && !s.away) want.add(s.where);
      hours += s.from <= s.to ? s.to - s.from : 24 - s.from + s.to;
    }
    assert(Math.abs(hours - 24) < 1e-6, `${r.id}: its day's spans cover 24 hours (${hours})`);
  }
}
const doorless = [...want].filter((s) => !withDoor.has(s));
assert.deepEqual(doorless, [], `every building someone is in has a door: ${doorless}`);
const n = records.filter((r) => r.behaviour?.day || r.behaviour?.quarters).length;
console.log(`human days: dates, spans, talk, work, walk, doors and asking hold (${n} 1812 records with a day or quarters; ${doors.structures.length} buildings with doors)`);
