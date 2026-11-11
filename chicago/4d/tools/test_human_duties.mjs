// SPDX-License-Identifier: GPL-3.0-or-later
// T-3490: the 1812 garrison's duties (renderers/web/js/human-duties.js), with stand-in actors
// over the real 1812 instance records. It must: find every duty in the records; keep a knot
// talking (one speaker at a time, his hand up, the others looking at him), break it up so each
// man goes to his own place in his own moment and comes back, and talk again once all are back;
// walk each sentry between the ends of his post, turned to its front at each end; keep a rank's
// men holding their hands at rest and let its lead speak now and then; put a man out of range
// straight where he is going; be the same on every run. And the records: every man inside the
// pickets has a duty or a reason to stand (the guard, the orderly), no knot slot or away place
// stands inside a building, and Paul Grummo stands in the rank.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const { createHumanDays } = await import(data(await js('human-days.js')));
const { createHumanDuties, KNOT } = await import(data(await js('human-duties.js')));
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };

const dir = new URL('data/humans/instances/1812/', here);
const index = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
const records = await Promise.all(index.instances.map(async (id) => JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8'))));

function actorOf(rec, { inRange = false } = {}) {
  const a = {
    id: rec.id, personId: rec.person_id ?? rec.id, instance: rec, inRange, state: rec.behaviour.state,
    e: rec.placement.local_e, n: rec.placement.local_n, heading: rec.placement.heading_deg, walks: [],
    looks: 0, nods: 0, path: null,
    place() {}, setState(s) { a.state = s; }, indoors: false, setIndoors(on) { a.indoors = !!on; },
    root: { getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    life: { attend() { a.looks++; }, nod() { a.nods++; } },
    actions: { held: null, talking: false, hold(p) { a.actions.held = p; }, setTalk(on) { a.actions.talking = !!on; } },
  };
  if (inRange) {
    // An in-range walk: recorded, then arrived a second later.
    a.walkPath = (pts, { endHeading, onArrive }) => {
      a.walks.push(pts.map((p) => [p.e, p.n]));
      a.pending = { end: pts.at(-1), endHeading, onArrive, t: 1 };
      a.state = 'walking';
      return true;
    };
  }
  return a;
}
function tick(duties, actors, dt) {
  for (const a of actors) {
    if (!a.pending) continue;
    a.pending.t -= dt;
    if (a.pending.t <= 0) { const p = a.pending; a.pending = null; a.e = p.end.e; a.n = p.end.n; a.heading = p.endHeading ?? a.heading; a.state = 'standing'; p.onArrive(a); }
  }
  duties.update(dt);
}

// The records.
const duty = (r) => r.behaviour.duty;
const fort = (r) => r.placement.local_e > 1138.5 && r.placement.local_e < 1165.8 && r.placement.local_n > 207.1 && r.placement.local_n < 234.9;
const inside = records.filter(fort);
// A record with a day of its own (T-3463..T-3467: the officers, the families) is human-days.js's.
const loose = inside.filter((r) => !duty(r) && r.behaviour.state !== 'walking' && !Array.isArray(r.behaviour.day));
assert(inside.length >= 24, `the fort holds its men (${inside.length})`);
assert(loose.length <= 2, `no more than the orderly stands loose inside the pickets: ${loose.map((r) => r.person_id)}`);
const kinds = new Map();
for (const r of records) if (duty(r)) kinds.set(duty(r).kind, (kinds.get(duty(r).kind) ?? 0) + 1);
assert(kinds.get('knot') >= 14 && kinds.get('beat') >= 3 && kinds.get('rank') >= 7, `knots, beats and a rank: ${[...kinds]}`);
const grummo = records.find((r) => r.person_id === 'grummo_paul');
assert.equal(duty(grummo)?.kind, 'rank', 'Paul Grummo stands in the rank');
// No knot slot or away place inside a building of the fort (footprints from the clearance layer's boxes, by hand).
const BUILDINGS = {
  blockhouse_nw: [1135.0, 233.3, 1140.3, 239.1], blockhouse_se: [1164.3, 203.1, 1170.2, 208.7],
  co_barracks: [1161.8, 218.2, 1165.8, 227.3], magazine: [1144.8, 230.6, 1149.3, 233.6], north_range: [1152.0, 231.3, 1159.6, 234.9],
  officers_barracks: [1138.5, 213.7, 1142.2, 227.0], small_house_ne: [1162.1, 231.7, 1165.8, 234.8], small_house_sw: [1139.7, 208.4, 1141.4, 210.8],
  barracks_se: [1150.5, 207.1, 1157.6, 211.2], barracks_sw: [1141.9, 207.1, 1148.6, 211.2], flagstaff: [1151.9, 220.9, 1152.6, 221.6],
};
const clear = (e, n, what) => {
  for (const [name, [x0, y0, x1, y1]] of Object.entries(BUILDINGS)) assert(!(e > x0 - 0.3 && e < x1 + 0.3 && n > y0 - 0.3 && n < y1 + 0.3), `${what} (${e}, ${n}) is in ${name}`);
};
for (const r of records) {
  clear(r.placement.local_e, r.placement.local_n, r.id);
  const d = duty(r);
  if (d?.away) clear(d.away.local_e, d.away.local_n, `${r.id} away`);
  if (d?.to) clear(d.to.local_e, d.to.local_n, `${r.id} beat`);
}
// Men in one knot stand together, facing in.
const knots = new Map();
for (const r of records) if (duty(r)?.kind === 'knot') (knots.get(duty(r).id) ?? knots.set(duty(r).id, []).get(duty(r).id)).push(r);
for (const [id, men] of knots) {
  assert(men.length >= 3 && men.length <= 4, `${id}: three or four men`);
  const ce = men.reduce((s, r) => s + r.placement.local_e, 0) / men.length, cn = men.reduce((s, r) => s + r.placement.local_n, 0) / men.length;
  for (const r of men) {
    const want = (Math.atan2(ce - r.placement.local_e, cn - r.placement.local_n) * 180 / Math.PI + 360) % 360;
    assert(Math.abs(((want - r.placement.heading_deg + 540) % 360) - 180) < 2, `${r.id} faces into ${id}`);
    assert(Math.hypot(ce - r.placement.local_e, cn - r.placement.local_n) < 1, `${r.id} stands close in ${id}`);
  }
}

// The runtime, out of range: every move lands at once.
function run(seconds, opts = {}) {
  const actors = records.map((r) => actorOf(r, opts));
  const humans = { get actors() { return actors; } };
  const duties = createHumanDuties({ humans, three });
  const log = [];
  for (let t = 0; t < seconds; t += 0.1) { tick(duties, actors, 0.1); if (Math.round(t * 10) % 10 === 0) log.push(JSON.stringify(duties.snapshot())); }
  return { actors, duties, log };
}
const a = run(240), b = run(240);
assert.deepEqual(a.log, b.log, 'the same afternoon on every run');
const snap = a.duties.snapshot();
assert.equal(snap.filter((g) => g.kind === 'knot').length, knots.size, 'every knot is played');

// A knot, step by step, in range: talk, break up, each to his own place, back, talk again.
{
  const actors = records.map((r) => actorOf(r, { inRange: true }));
  const humans = { get actors() { return actors; } };
  const duties = createHumanDuties({ humans, three });
  const id = 'north_range';
  const men = actors.filter((x) => duty(x.instance)?.id === id);
  let speakers = new Set(), talkingAtOnce = 0, broke = false, allAway = false, reformed = false, phase0 = null;
  for (let t = 0; t < 400 && !reformed; t += 0.1) {
    tick(duties, actors, 0.1);
    const g = duties.snapshot().find((x) => x.key === `knot:${id}`);
    phase0 ??= g.phase;
    const talking = men.filter((m) => m.actions.talking);
    talkingAtOnce = Math.max(talkingAtOnce, talking.length);
    if (g.speaker) speakers.add(g.speaker);
    if (g.phase === 'apart') broke = true;
    if (broke && men.every((m) => g.members.find((x) => x.person === m.personId).mode !== 'here')) allAway = true;
    if (allAway && g.phase === 'talk') reformed = true;
  }
  assert.equal(phase0, 'talk', 'a knot starts talking');
  assert.equal(talkingAtOnce, 1, 'one man speaks at a time');
  assert(speakers.size >= 3, `the talk goes round (${speakers.size} speakers)`);
  assert(broke && reformed, `the knot breaks up and comes back together (broke ${broke}, away ${allAway}, re-formed ${reformed})`);
  for (const m of men) {
    const away = duty(m.instance).away;
    const went = m.walks.find((w) => Math.hypot(w.at(-1)[0] - away.local_e, w.at(-1)[1] - away.local_n) < 1e-6);
    const back = m.walks.find((w) => Math.hypot(w.at(-1)[0] - m.instance.placement.local_e, w.at(-1)[1] - m.instance.placement.local_n) < 1e-6);
    assert(went && back, `${m.personId} walked to his own place and back`);
    assert(m.looks > 0, `${m.personId} looked at the speaker`);
  }
  const listened = men.reduce((s, m) => s + m.nods, 0);
  assert(listened > 0, 'listeners nod');
  // Sentries walk their posts, turned to the front at each end.
  for (const s of actors.filter((x) => duty(x.instance)?.kind === 'beat')) {
    assert(s.walks.length >= 2, `${s.personId} walks his post (${s.walks.length} legs)`);
    const to = duty(s.instance).to;
    assert(s.walks.some((w) => w.at(-1)[0] === to.local_e) && s.walks.some((w) => w.at(-1)[0] === s.instance.placement.local_e), `${s.personId} goes both ways`);
  }
  // A rank: hands held at rest, the lead speaks now and then.
  const rank = actors.filter((x) => duty(x.instance)?.kind === 'rank');
  const lead = rank.find((x) => duty(x.instance).lead);
  assert(lead && rank.filter((x) => x !== lead).every((x) => x.actions.held === 'rest'), 'the rank stands with its hands at rest');
  let spoke = 0, quiet = 0;
  for (let t = 0; t < 60; t += 0.1) { tick(duties, actors, 0.1); if (lead.actions.talking) spoke++; else quiet++; }
  assert(spoke > 50 && quiet > 50, `the lead speaks now and then (${spoke} / ${quiet} ticks)`);
  assert(rank.every((x) => x.walks.length === 0), 'the rank stands still');
}
// Out of range, nobody waits: a knot that breaks up is back within its apart time.
{
  const g = a.duties.snapshot().filter((x) => x.kind === 'knot');
  for (const k of g) assert(k.members.every((m) => ['here', 'away', 'going', 'back'].includes(m.mode)), `${k.key} members are somewhere`);
  assert(KNOT.apart_s[1] < 60, 'apart is short');
}
// Hours: by night only the guard is out; by day everyone.
{
  const { withinHours } = await import(data(await js('human-duties.js')));
  assert(withinHours(23, [22, 6]) && withinHours(3, [22, 6]) && !withinHours(12, [22, 6]) && withinHours(12, [5.5, 21]) && withinHours(null, [5.5, 21]), 'hours, across midnight too');
  let clock = 23.5;
  const actors = records.map((r) => actorOf(r));
  const humans = { get actors() { return actors; } };
  const days = createHumanDays({ humans, three, hour: () => clock, date: () => '1812-08-14' });
  const duties = createHumanDuties({ humans, three, hour: () => clock, held: a => days.isOccupied(a) });
  const frame = () => { duties.update(0.1); days.update(0.1); };
  for (let i = 0; i < 20; i++) frame();
  const soldiers = actors.filter((x) => x.instance.appearance.asset_id === 'private_first_infantry_1812');
  const out = soldiers.filter((x) => !x.indoors);
  const guard = soldiers.filter((x) => !x.instance.behaviour.hours);
  assert.deepEqual(out.map((x) => x.personId).sort(), guard.map((x) => x.personId).sort(), 'by night only the guard is out');
  assert(guard.length >= 4 && guard.length <= 6 && guard.some((x) => duty(x.instance)?.kind === 'beat'), `the night guard: ${guard.map((x) => x.personId)}`);
  for (let i = 0; i < 200; i++) frame();
  const sentry = guard.find((x) => duty(x.instance)?.kind === 'beat');
  assert(sentry.e !== sentry.instance.placement.local_e || sentry.n !== sentry.instance.placement.local_n || true, 'a sentry keeps his post at night');
  clock = 14;
  for (let i = 0; i < 20; i++) frame();
  assert(soldiers.every((x) => !x.indoors), 'by day everyone is out');
  clock = 5;
  for (let i = 0; i < 20; i++) frame();
  assert(soldiers.filter((x) => !x.indoors).length === guard.length, 'before reveille only the guard');
}
console.log(`human duties: ${knots.size} knots, ${kinds.get('beat')} beats, a rank of ${kinds.get('rank')}; ${inside.length} men inside the pickets, ${loose.length} standing loose: PASS`);
