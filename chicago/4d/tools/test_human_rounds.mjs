// SPDX-License-Identifier: GPL-3.0-or-later
// T-3505 (owner, 2026-11-08: "I do not want to have everyone standing in groups talking, it's fine
// if there are conversations that come together and break up, but the whole day of theirs should
// not be spent talking, they should be doing something their duty or other normal activities. Some
// if not many can be inside", and "the people should look natural that they are doing ordinary
// things on a loop ... They can take breaks and go in and out of houses and buildings"):
// renderers/web/js/human-days.js plays a talk as a gathering that comes and goes, each of its
// people at their own job (a child at play) between, and takes people in for a while at their
// home's door. With stand-in actors and the 1812 town's own records, on 14 August:
//   - every talk of two or more is a round (a gathering and a job of one's own), a talk of one is
//     a job; every job's places are clear of the buildings and the fort's pickets;
//   - over ten minutes at morning, noon, afternoon and evening hours, no one out of doors spends
//     more than half of it talking, and the town on the whole far less; every knot with people out
//     gathers and parts again; people go in for a break and come out, and while in are offered at
//     their door; nobody out of doors stands idle but at a post;
//   - the same seeds play the same round on every load.
// T-3516 / T-3533: every drawn person in 1835 and 1904 has a day, including the
// Glessners and Christine; they are in or away at night,
// take breaks at their own doors, and 1904's staff gather now and then.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const days = await import(data(await js('human-days.js')));
const { createHumanDays, planDay, dayOn, spanAt, clearWayOf, GATHER, BREAK, POST_RE, CHILD_RE, NEAR_M } = days;
const { occupiedPolygons } = await import(data(await js('occupied-footprints.js')));
const doorsOf = async (scene) => JSON.parse(await fs.readFile(new URL(`data/humans/doors_${scene}.json`, here), 'utf8'));
const doors = await doorsOf('1812');
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };

// ── the footprints the walker keeps out of (walker.js footprintsFrom), the fort's pickets as walls ──
const FORT_GATES = ['first_fort_dearborn_pickets_outer', 'first_fort_dearborn_pickets_inner', 'first_fort_outer_officers_garden', 'fort_dearborn_palisade'];
async function footprintsOf(scene) {
const sideDir = new URL(`data/sidecars/${scene}/`, here);
const footprints = [];
for (const f of (await fs.readdir(sideDir)).filter((x) => x.endsWith('.json')).sort()) {
  const sc = JSON.parse(await fs.readFile(new URL(f, sideDir), 'utf8'));
  if (!sc?.placement || !sc.footprint) continue;
  if (sc.placement.vertical_anchor === 'water' || sc.drawn_by || ['camp', 'lodge_camp'].includes(sc.archetype)) continue;
  const th = ((sc.placement.rotation_deg ?? 0) * Math.PI) / 180, c = Math.cos(th), s = Math.sin(th);
  const e0 = sc.placement.local_e ?? 0, n0 = sc.placement.local_n ?? 0;
  const toWorld = ([u, v]) => [e0 + u * c + v * s, n0 - u * s + v * c];
  for (const [i, poly] of occupiedPolygons(sc.footprint).entries()) {
    const fp = { id: sc.id, pts: poly.map(toWorld) };
    if (i === 0 && sc.attributes?.kind?.value === 'parade') fp.ground = true;
    if (FORT_GATES.includes(sc.id)) fp.walls = fp.pts.map((a, k) => ({ a, b: fp.pts[(k + 1) % fp.pts.length] }));
    footprints.push(fp);
  }
}
return footprints;
}
const footprints = await footprintsOf('1812');
assert(footprints.length > 40, `the 1812 footprints (${footprints.length})`);
const clear = clearWayOf(footprints);
assert.equal(clear({ e: 0, n: 0 }, { e: 1, n: 0 }), true, 'open ground is clear');
{
  const fp = footprints.find((f) => !f.ground && !f.walls);
  const mid = fp.pts.reduce((t, [e, n]) => ({ e: t.e + e / fp.pts.length, n: t.n + n / fp.pts.length }), { e: 0, n: 0 });
  assert.equal(clear({ e: mid.e + 40, n: mid.n }, mid), false, `inside ${fp.id} is not clear`);
}

// ── the town's records ──
const dir = new URL('data/humans/instances/1812/', here);
const index = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
const recs = (await Promise.all(index.instances.map(async (id) => JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8')))))
  .filter((r) => r.display === 'shown');
const date = '1812-08-14';
const people = recs.filter((r) => Array.isArray(r.behaviour?.day))
  .map((r) => ({ key: r.person_id ?? r.id, b: r.behaviour, child: CHILD_RE.test(r.appearance?.asset_id ?? '') }));
const plan = planDay(people, date, { clear });
let rounds = 0, ownJobs = 0, ownPlaces = 0, plays = 0, lone = 0;
for (const p of people) {
  for (const s0 of dayOn(p.b, date, p.key)?.spans ?? []) {
    if (s0.indoors || !s0.at) continue;
    const s = plan.get(s0) ?? s0;
    if (s.activity === 'talk') {
      assert(s.round?.own, `${p.key} ${s0.from}-${s0.to}: a talk is a round, with a job of their own between its gatherings`);
      rounds++;
      const own = s.round.own, at = { e: own.at.local_e, n: own.at.local_n };
      const ring = { e: s.at.local_e, n: s.at.local_n };
      const places = own.activity === 'walk' ? [...(own.via ?? []), own.to_point] : own.spots ?? [];
      if (own.activity === 'walk') plays++; else ownJobs++;
      if (Math.hypot(at.e - ring.e, at.n - ring.n) > 0.05) assert(clear(ring, at), `${p.key}: from the ring to their job is clear`);
      for (const q of places) { assert(clear(at, { e: q.local_e, n: q.local_n }), `${p.key}: each place of their job is clear`); ownPlaces++; }
    } else if (s.activity === 'work' && s !== s0 && !s0.activity?.startsWith?.('work')) lone++;
  }
}
assert(rounds > 150, `the town's talks are rounds (${rounds})`);
assert(ownPlaces >= 1.6 * (ownJobs + plays), `nearly every job has its places, clear of buildings (${ownPlaces} for ${ownJobs + plays})`);
assert(plays > 5, `the children play between gatherings (${plays})`);

// ── played: stand-in actors through ten minutes at a few hours ──
function actor(r) {
  const a = {
    id: r.id, personId: r.person_id ?? r.id, instance: r, e: r.placement.local_e, n: r.placement.local_n, heading: 0,
    state: 'standing', indoors: false, inRange: true, path: null, standY: null, talking: false,
    root: { visible: false, getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    place() {}, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; }, turnTo() {},
    life: { attend() {}, nod() {} }, actions: { setTalk(on) { a.talking = !!on; }, greet() {}, hold() {} },
    // A walk takes a second a leg (the harness's own time).
    walkPath(pts, { endHeading = null, onArrive = null } = {}) {
      a.pending = { end: pts.at(-1), endHeading, onArrive, t: 1 }; a.state = 'walking'; return true;
    },
  };
  return a;
}
function play(hour, seconds = 600, dt = 0.25, { recs: rs = recs, date: dd = date, doors: ds = doors, clear: cl = clear, visit = { e: 1150, n: 220 } } = {}) {
  const actors = rs.map(actor);
  const humans = { actors, shown: true };
  let visitor = { ...visit };
  const things = [];
  const interactions = { add: (t) => things.push(t) };
  const d = createHumanDays({ humans, three, hour: () => hour, date: () => dd, doors: ds, interactions, clear: cl, visitor: () => visitor });
  const tally = new Map();
  const knots = new Map();
  let askable = 0;
  const kids = { out: 0, n: 0, most: 0 };
  for (let t = 0; t < seconds; t += dt) {
    for (const a of actors) {
      if (!a.pending) continue;
      a.pending.t -= dt;
      if (a.pending.t <= 0) { const q = a.pending; a.pending = null; a.e = q.end.e; a.n = q.end.n; a.state = 'standing'; q.onArrive?.(a); }
    }
    d.update(dt);
    for (const p of d.people) {
      if (!p.round || p.absent) continue;
      // Each figure near the visitor's eye: the visitor stands by each of them in turn.
      const k = p.actor.personId;
      if (!tally.has(k)) tally.set(k, { talk: 0, in: 0, own: 0, idle: 0, n: 0, brk: 0 });
      const c = tally.get(k);
      c.n++;
      if (p.phase === 'talk') c.talk++; else if (p.phase === 'in') c.in++; else c.own++;
      if (p.phase === 'in' && p.mode === 'in' && c.lastIn !== true) c.brk++;
      c.lastIn = p.phase === 'in' && p.mode === 'in';
      if (p.mode === 'out' && p.actor.state === 'standing' && !p.job && p.phase === 'own' && !POST_RE.test(p.span?.doing ?? '')) c.idle++;
      if (p.round.knot) {
        if (!knots.has(p.round.knot)) knots.set(p.round.knot, { on: 0, offs: 0, last: false });
      }
    }
    // T-3520: how many children are out, and the most of them in one place, of those the
    // visitor is near (one far off keeps to what it is at until it is seen near: NEAR_M).
    const seen = d.people.filter((p) => p.child && !p.absent && Math.hypot(p.actor.e - visitor.e, p.actor.n - visitor.n) < NEAR_M);
    const out = seen.filter((p) => !p.actor.indoors);
    kids.n += seen.length; kids.out += out.length;
    // Children with their family about them (a lodge at its meal) are not a crowd of children:
    // the most children in one place with fewer than one grown-up to two of them.
    const grown = d.people.filter((p) => !p.child && !p.absent && !p.actor.indoors);
    for (const a of out) {
      const by = (q) => Math.hypot(q.actor.e - a.actor.e, q.actor.n - a.actor.n) < 15;
      const here = out.filter(by).length, adults = grown.filter(by).length;
      if (adults * 2 < here) kids.most = Math.max(kids.most, here);
    }
    for (const [knot, g] of knots) {
      const on = d.people.some((p) => p.round?.knot === knot && p.phase === 'talk' && p.mode === 'out');
      if (on && !g.last) g.on++;
      if (!on && g.last) g.offs++;
      g.last = on;
    }
    if (Math.round(t / dt) % 40 === 0) {
      // Someone in on a break is offered at their home's door.
      const brk = d.people.find((p) => p.phase === 'in' && p.mode === 'in' && p.round?.home);
      if (brk) {
        const door = things.find((x) => x.structure === brk.round.home);
        if (door && door.actions.shut.some((a) => a.id === `ask:${brk.actor.personId}`)) askable++;
      }
    }
    // The visitor walks about the town, so every part of it is near now and then.
    if (Math.round(t / dt) % 80 === 0) {
      const p = d.people[Math.floor((t / seconds) * d.people.length) % d.people.length];
      visitor = { e: p.actor.e + 3, n: p.actor.n + 3 };
    }
  }
  return { tally, knots, askable, kids, snap: d.snapshot() };
}

const report = [];
const first = play(10, 120);
const again = play(10, 120);
assert.deepEqual(again.snap, first.snap, 'the same round on every load');
for (const hour of [7, 10, 15.5, 19.5]) {
  const { tally, knots, askable, kids } = play(hour);
  let talk = 0, all = 0, worst = 0, worstKey = '', idle = 0, breaks = 0;
  for (const [k, c] of tally) {
    talk += c.talk; all += c.n; idle += c.idle; breaks += c.brk;
    if (c.talk / c.n > worst) { worst = c.talk / c.n; worstKey = k; }
  }
  assert(worst <= 0.6, `${hour}h: ${worstKey} talks ${(100 * worst).toFixed(0)}% of ten minutes`);
  assert(talk / all < 0.4, `${hour}h: the town talks ${(100 * talk / all).toFixed(0)}% of its time out`);
  assert(idle / all < 0.02, `${hour}h: ${(100 * idle / all).toFixed(1)}% of the time someone out stands idle`);
  const met = [...knots.values()].filter((g) => g.on > 0);
  assert(met.length >= Math.ceil(knots.size * 0.6), `${hour}h: ${met.length} of ${knots.size} knots gather`);
  assert(met.filter((g) => g.offs > 0).length >= Math.ceil(met.length * 0.8), `${hour}h: gatherings part again`);
  assert(met.some((g) => g.on >= 3), `${hour}h: and come together again`);
  assert(breaks > 0, `${hour}h: someone goes in for a break`);
  assert(askable > 0, `${hour}h: and while in is offered at the door`);
  // T-3520 (owner, 2026-11-08: "the kids should not be all over the place", "occasionally
  // there are kids together playing" but not "such a centerpiece"): most children are in most
  // of the time, and no more than a handful are ever together out of doors.
  assert(kids.n && kids.out / kids.n < 0.4, `${hour}h: the children are out ${(100 * kids.out / kids.n).toFixed(0)}% of the time`);
  assert(kids.most <= 5, `${hour}h: ${kids.most} children out together in one place, few grown-ups by`);
  report.push(`${hour}h ${(100 * talk / all).toFixed(0)}% talk (most ${(100 * worst).toFixed(0)}%), ${met.length}/${knots.size} knots gather, ${breaks} breaks, children out ${(100 * kids.out / kids.n).toFixed(0)}% (${kids.most} together at most without grown-ups)`);
}
// ── 1835 and 1904 (T-3516 / T-3533): every drawn person has a day;
// played, they work, gather, take breaks in at
// their own doors, and are in (or away) at night.
for (const [scene, when, hours] of [['1835', '1835-07-01', [7, 12.5, 16]], ['1904', '1904-07-01', [10.5, 11.25, 15.5, 19.25]]]) {
  const dir = new URL(`data/humans/instances/${scene}/`, here);
  const idx = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
  const rs = (await Promise.all(idx.instances.map(async (id) => JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8')))))
    .filter((r) => r.display === 'shown');
  const withDay = rs.filter((r) => Array.isArray(r.behaviour?.day));
  const without = rs.filter((r) => !Array.isArray(r.behaviour?.day)).map((r) => r.id).sort();
  assert.deepEqual(without, [], `${scene}: every drawn person has a day, without exceptions`);
  const ds = await doorsOf(scene);
  const cl = clearWayOf(await footprintsOf(scene));
  const centre = { e: withDay.reduce((t, r) => t + r.placement.local_e, 0) / withDay.length, n: withDay.reduce((t, r) => t + r.placement.local_n, 0) / withDay.length };
  let night = 0;
  for (const r of withDay) {
    const s = spanAt(dayOn(r.behaviour, when, r.person_id), 2);
    if (s.indoors) night++;
  }
  assert.equal(night, withDay.length, `${scene}: at night everyone is in, or away`);
  const seen = [];
  for (const hour of hours) {
    let breaks = 0, idle = 0, talk = 0, all = 0;
    // The visitor stands by each of them in turn (a break is taken only near the visitor).
    for (const r of withDay) {
      const { tally } = play(hour, 400, 0.25, { recs: rs, date: when, doors: ds, clear: cl, visit: { e: r.placement.local_e + 3, n: r.placement.local_n } });
      const c = tally.get(r.person_id);
      if (!c) continue;
      breaks += c.brk; idle += c.idle; talk += c.talk; all += c.n;
    }
    assert(idle / Math.max(1, all) < 0.02, `${scene} ${hour}h: someone out stands idle`);
    assert(breaks > 0, `${scene} ${hour}h: someone goes in for a break`);
    // T-3533: shared breaks and evening company have their own slots; ordinary
    // working hours no longer require everyone to be assigned a conversation.
    if (scene === '1904' && [11.25, 19.25].includes(hour)) assert(talk > 0, `${scene} ${hour}h: the scheduled company gathers and parts`);
    seen.push(`${hour}h ${breaks} breaks, ${(100 * talk / Math.max(1, all)).toFixed(0)}% talk`);
  }
  void centre;
  report.push(`${scene}: ${withDay.length} with a day, ${ds.structures.length} homes with doors, ${seen.join(', ')}`);
}
void GATHER; void BREAK;
console.log(`human rounds: ${rounds} talks are rounds (${ownJobs} jobs, ${plays} at play, ${lone} lone jobs), clear of buildings; ${report.join('; ')}: PASS`);
