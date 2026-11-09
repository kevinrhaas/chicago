// SPDX-License-Identifier: GPL-3.0-or-later
// T-3504 (owner, 2026-11-08, of the 1812 parade: "there are two people occupying the same space?
// Prevent that", and "give everyone a purpose or task so they are all not standing around idly"):
// renderers/web/js/human-spacing.js keeps every pair of figures a body's width apart, and
// human-days.js plays each day so that a talk's people stand in a ring, people standing together
// talk and one standing alone is at a job. With stand-in actors and every year's real records:
//   - two people on one point are put apart at once when not drawn, a step at a time when drawn;
//   - a walker steps round a stander; a figure on a tread is never moved;
//   - planDay stands no two people of 1812 in one place at any quarter hour of 14 August, and
//     leaves no one standing idle out of doors but at a post;
//   - all of 1812, 1835 and 1904 played through the day with human-days, human-duties and the
//     spacing pass: no two figures out of doors nearer than MIN_M at any quarter hour.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8');
const { createHumanSpacing, keepOutOf, wallsFrom, BODY_R_M, MIN_M, RATE_M_S, MAX_M } = await import(data(await js('human-spacing.js')));
const { createHumanDays, planDay, dayOn, spanAt, POST_RE } = await import(data(await js('human-days.js')));
const { createHumanDuties } = await import(data(await js('human-duties.js')));
const doors = JSON.parse(await fs.readFile(new URL('data/humans/doors_1812.json', here), 'utf8'));
const three = { Vector3: class { constructor() { this.x = 0; this.y = 0; this.z = 0; } } };

function actor(id, e, n, extra = {}) {
  const a = {
    id, personId: id.replace(/^hi_/, ''), e, n, heading: 0, state: 'standing', indoors: false, inRange: true,
    path: null, standY: null, places: 0, instance: { id, placement: { local_e: e, local_n: n, heading_deg: 0 }, behaviour: {} },
    root: { visible: false, getWorldPosition(v) { v.x = a.e; v.y = 0; v.z = -a.n; return v; } },
    place() { a.places++; }, setState(s) { a.state = s; }, setIndoors(on) { a.indoors = !!on; }, turnTo() {},
    life: { attend() {}, nod() {} }, actions: { setTalk() {}, greet() {}, hold() {} },
    // A walk is over at once: the figure is where it was going (the harness's own time).
    walkPath(pts, { endHeading = null, onArrive = null } = {}) {
      const end = pts.at(-1); a.e = end.e ?? end.local_e; a.n = end.n ?? end.local_n;
      if (Number.isFinite(endHeading)) a.heading = endHeading;
      a.state = 'standing'; onArrive?.(a); return true;
    },
    ...extra,
  };
  return a;
}
const at = (a) => ({ e: a.e + (a.spaceE ?? 0), n: a.n + (a.spaceN ?? 0) });
const apart = (a, b) => Math.hypot(at(a).e - at(b).e, at(a).n - at(b).n);

// ── two on one point, not drawn: apart at once, the same way every load ──
{
  const a = actor('hi_a', 10, 10), b = actor('hi_b', 10, 10);
  const sp = createHumanSpacing({ humans: { actors: [a, b] } });
  sp.update(0.016);
  assert(apart(a, b) >= MIN_M - 1e-6, `one point taken apart (${apart(a, b)})`);
  const a2 = actor('hi_a', 10, 10), b2 = actor('hi_b', 10, 10);
  createHumanSpacing({ humans: { actors: [a2, b2] } }).update(0.016);
  assert.equal(a2.spaceE, a.spaceE, 'seeded: the same on every load');
  assert(a.places > 0 && b.places > 0, 'both re-placed');
}
// ── drawn: a step at a time ──
{
  const a = actor('hi_a', 0, 0), b = actor('hi_b', 0.1, 0);
  a.root.visible = b.root.visible = true;
  const sp = createHumanSpacing({ humans: { actors: [a, b] } });
  sp.update(0.1);
  const first = Math.hypot(a.spaceE, a.spaceN);
  assert(first <= RATE_M_S * 0.1 + 1e-6, `a drawn figure steps, never jumps (${first})`);
  for (let i = 0; i < 40; i++) sp.update(0.1);
  assert(apart(a, b) >= MIN_M - 1e-3, `apart after a few steps (${apart(a, b)})`);
}
// ── a walker steps round a stander; a figure on a tread is not moved ──
{
  const s = actor('hi_stand', 0, 0), w = actor('hi_walk', 0.2, 0, { state: 'walking' });
  const t = actor('hi_tread', 0, 0.2, { standY: 1.2 });
  const sp = createHumanSpacing({ humans: { actors: [s, w, t] } });
  sp.update(0.016);
  assert(Math.hypot(w.spaceE, w.spaceN) > Math.hypot(s.spaceE, s.spaceN), 'the walker takes the step aside');
  assert.equal(t.spaceE, 0); assert.equal(t.spaceN, 0);
  assert(apart(s, t) >= MIN_M - 1e-3 && apart(w, t) >= MIN_M - 1e-3, 'others keep clear of the one on the tread');
  for (const a of [s, w]) assert(Math.hypot(a.spaceE, a.spaceN) <= MAX_M + 1e-9);
}
// ── never into a building ──
{
  const a = actor('hi_a', 0, 0), b = actor('hi_b', 0, 0);
  const sp = createHumanSpacing({ humans: { actors: [a, b] }, blockedAt: (e) => e > 0.05 });
  sp.update(0.016);
  for (const x of [a, b]) assert(!(x.e + x.spaceE > 0.05), 'not pushed into the blocked side');
}

// ── T-3520 (owner, 2026-11-08: "people can stand and break the wall of the mat walls"): no one
// stands in a lodge's wall; one at its door step, outside, is left where they are ──
{
  const ring = Array.from({ length: 16 }, (_, i) => [20 + 2.5 * Math.sin(i * Math.PI / 8), 20 + 2.5 * Math.cos(i * Math.PI / 8)]);
  const walls = [{ id: 'lodge', pts: ring }];
  const inWall = actor('hi_in', 20 + 2.4, 20), inside = actor('hi_mid', 20.3, 20.2), step = actor('hi_step', 20, 20 + 2.5 + 0.55);
  const sp = createHumanSpacing({ humans: { actors: [inWall, inside, step] }, keepOut: walls });
  sp.update(0.016);
  const W = wallsFrom(walls);
  for (const a of [inWall, inside]) assert(!keepOutOf(W, at(a).e, at(a).n, BODY_R_M - 0.01), `${a.id} is out of the lodge's wall (${at(a).e.toFixed(2)}, ${at(a).n.toFixed(2)})`);
  assert(Math.hypot(at(inWall).e - 20, at(inWall).n - 20) < 2.5 + BODY_R_M + 0.3, 'moved just past the wall, not far off');
  assert.equal(step.spaceE, 0, 'one at the door step is left where they stand');
  // Drawn, a step at a time.
  const d = actor('hi_drawn', 20.5, 20); d.root.visible = true;
  createHumanSpacing({ humans: { actors: [d] }, keepOut: walls }).update(0.1);
  assert(Math.hypot(d.spaceE, d.spaceN) <= RATE_M_S * 0.1 + 1e-6, 'a drawn figure steps out, no jump');
}

// ── every year's records, played through the day ──
async function records(scene) {
  const dir = new URL(`data/humans/instances/${scene}/`, here);
  const index = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
  return Promise.all(index.instances.map(async (id) => JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8'))));
}
const DATES = { 1812: '1812-08-14', 1835: '1835-07-01', 1904: '1904-06-15' };
const report = [];
for (const scene of ['1812', '1835', '1904']) {
  const recs = (await records(scene)).filter((r) => r.display === 'shown');
  const date = DATES[scene];
  if (scene === '1812') {
    // planDay: nobody idle out of doors but at a post; no two of a ring or a company on one spot.
    const people = recs.filter((r) => Array.isArray(r.behaviour?.day)).map((r) => ({ key: r.person_id ?? r.id, b: r.behaviour }));
    const plan = planDay(people, date);
    let idle = 0, posts = 0, near = 0;
    for (let h = 0; h < 24; h += 0.25) {
      const spots = [];
      for (const p of people) {
        const s0 = spanAt(dayOn(p.b, date, p.key), h);
        if (!s0 || s0.indoors) continue;
        const s = plan.get(s0) ?? s0;
        if ((s.activity ?? 'stand') === 'stand') { if (POST_RE.test(s.doing ?? '')) posts++; else idle++; }
        if (['stand', 'talk'].includes(s.activity ?? 'stand')) spots.push({ key: p.key, e: s.at.local_e, n: s.at.local_n });
      }
      for (let i = 0; i < spots.length; i++) for (let j = i + 1; j < spots.length; j++) {
        if (Math.hypot(spots[i].e - spots[j].e, spots[i].n - spots[j].n) < MIN_M - 0.02) near++;
      }
    }
    assert.equal(idle, 0, 'nobody stands idle out of doors (alone they work, together they talk)');
    assert.equal(near, 0, 'no two people of a talk or a company on one spot');
    report.push(`1812 plan: ${plan.size} spans played anew, ${posts / 4} post-hours stood`);
  }
  const actors = recs.map((r) => {
    const a = actor(r.id, r.placement.local_e, r.placement.local_n);
    a.instance = r; a.personId = r.person_id ?? r.id; a.state = r.behaviour?.state ?? 'standing';
    return a;
  });
  const humans = { actors, shown: true };
  let hour = 0;
  const visitor = () => ({ e: actors[0]?.e ?? 0, n: actors[0]?.n ?? 0 });
  const days = createHumanDays({ humans, three, hour: () => hour, date: () => date, doors, visitor: () => null });
  const duties = createHumanDuties({ humans, three, hour: () => hour });
  // T-3520: the camps' lodge walls, as main.js hands them in (doors_1812.json `walls`).
  const walls = scene === '1812' ? doors.structures.flatMap((s) => (s.walls ?? []).map((pts, i) => ({ id: `${s.structure}:${i}`, pts }))) : [];
  const W = wallsFrom(walls);
  const spacing = createHumanSpacing({ humans, keepOut: walls });
  let worst = Infinity, worstAt = '', inWalls = 0, inWallAt = '';
  if (scene === '1812') assert(walls.length > 50, `the camps' lodges have walls (${walls.length})`);
  for (hour = 0; hour < 24; hour += 0.25) {
    for (let i = 0; i < 3; i++) { duties.update(0.25); days.update(0.25); spacing.update(0.25); }
    const out = actors.filter((a) => !a.indoors);
    for (const a of out) if (keepOutOf(W, at(a).e, at(a).n, BODY_R_M - 0.02)) { inWalls++; inWallAt ||= `${a.id} at ${hour}h, ${a.state}, at ${at(a).e.toFixed(2)},${at(a).n.toFixed(2)} off ${(a.spaceE ?? 0).toFixed(2)},${(a.spaceN ?? 0).toFixed(2)} standY ${a.standY}`; }
    for (let i = 0; i < out.length; i++) for (let j = i + 1; j < out.length; j++) {
      const d = apart(out[i], out[j]);
      if (d < worst) { worst = d; worstAt = `${out[i].id} / ${out[j].id} at ${hour}h`; }
    }
  }
  void visitor;
  assert(worst >= MIN_M - 0.02, `${scene}: two figures ${worst.toFixed(2)} m apart (${worstAt})`);
  assert.equal(inWalls, 0, `${scene}: someone stands in a lodge's wall (${inWallAt})`);
  report.push(`${scene}: ${actors.length} figures, nearest pair ${worst === Infinity ? '-' : worst.toFixed(2)} m`);
}
console.log(`human spacing: one point taken apart, a step at a time when drawn, walkers round standers; ${report.join('; ')}: PASS`);
