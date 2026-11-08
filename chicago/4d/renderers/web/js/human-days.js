// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-days.js — a person's day: where they are at each hour, indoors or out and at what,
 * on the scene's own date; and asking at a door for someone inside (T-3463..T-3467).
 *
 * The owner, 2026-11-08, of the 1812 town (the Kinzies, Black Partridge, Lalime and
 * "everyone"): *"Follow the same rules for deployment of these people some inside and others
 * active and doing what they would be doing as normal activities per time of day"*, *"If
 * they are inside I can walk to door and ask for any person inside"*, and *"if we set to
 * winter lalime would exist and we will need him for the murder jaunt"*. So a record's
 * `behaviour` may carry:
 *
 *   presence  { from, to }   ISO dates (either may be left out) the person is in the scene
 *                            at all. Off them they are nowhere: not drawn, not met, not asked
 *                            for. Jean Lalime is until 17 June 1812, the day he was killed; so
 *                            the winter scene (Settings › Season, 15 February) and the murder
 *                            jaunt's June stops have him, and 14 August does not.
 *   day       [{ dates?, chance?, spans }]   the first variant whose `dates` hold the
 *                            scene's date (or that has none) is the day played. `dates` is
 *                            {from, to} (ISO) and may add `months` ([1-12]) and `years`
 *                            ({from, to}: a run of years the months recur in). A variant with
 *                            `chance` (0-1) is a day that comes only so often (a Potawatomi
 *                            family in to trade "about one day in five"): on the other dates,
 *                            seeded by the person and the date, they are away. Its spans
 *                            cover 0-24 h, each `{ from, to, indoors, where, at, activity, ... }`:
 *
 *     indoors: true        in `where` (a structure id): not drawn; the building's door
 *                          offers Ask for <them>; with `away`, off the scene altogether
 *     indoors: false       out at `at` ({local_e, local_n, heading_deg}), doing `activity`:
 *       stand              standing there, turned to heading_deg (the life layer looks about)
 *       talk               with whoever else's span names the same `knot` at that hour: one
 *                          speaks, hand moving, the others look at him, nod; the speaker
 *                          changes (as human-duties.js's knot, without the walking apart)
 *       work               at a job there: from `at` to each of `spots` (a few metres about
 *                          it) and back, a while at each, turned to the work (heading_deg)
 *       walk               to and fro between `at` and `to_point` (by way of `via`, a list
 *                          of points, when given), a pause at each end; with `once`, from `at`
 *                          by `via` to `to_point` and there they stand (a path walked once)
 *
 * EVERYONE APART, EVERYONE AT SOMETHING (T-3504). The owner, 2026-11-08, of two figures standing
 * in one place on the 1812 parade: *"two people occupying the same space? Prevent that"*, and
 * *"give everyone a purpose or task so they are all not standing around idly"*. A span as written
 * is played (`plan()`, once per scene date) so that:
 *   - the people of one talk stand in a ring about the knot's place, facing in (RING), unless their
 *     own `at`s already stand them apart: a knot's records all name the knot's one point;
 *   - two or more people standing out at once within GROUP_M of each other are a company and
 *     talk (an implicit knot, in a ring about where they stood): waiting at the factory, an
 *     evening at the yard, a muster;
 *   - one person standing alone is at a job there (`work` about two spots a few metres off,
 *     POTTER), unless the span is a post (a sentry, a watch, a guard: POST_RE), which is stood.
 * Where and when stay the record's; only how the hour is spent is filled in (liberty
 * L-t3504-people-apart). human-spacing.js keeps whoever is left too close a body's width apart.
 *
 * Between spans a person walks: out of the door of the building they were in, to the next
 * span's place, or from where they are to the door and in. The way is the router's (route.js)
 * when there is one, else straight. Far from the visitor (beyond NEAR_M), no one walks: they
 * are put where the span has them, so a visitor coming up finds each person at the hour's work.
 *
 * DOORS: data/humans/doors_1812.json (tools/derive_doors_1812.py, read off the models). Each
 * door is an Interact thing (interact.js): while anyone is in the building it offers Ask for
 * <name>, for each of them (ASK_PAGE at a time, with Others inside… for the rest). Asked, the
 * person comes to the door after a knock and a wait, out of it, and up to the visitor (MEET_M
 * short), turns to them and touches a hat; their card opens if the visitor presses on them as
 * for anyone. They stay while the visitor is near; once the visitor has walked off (STAY_M,
 * for LEAVE_S) or after STAY_S, they go back to what the hour has them doing, in by the same
 * door if that is indoors. A soldier in quarters (human-duties.js `behaviour.hours`, with
 * `behaviour.quarters` naming the building) is asked for the same way.
 *
 * INSIDE ONLY: people carded but not drawn (the gathering's lodges) come in an `inside` list,
 * { people: [{ person, name, home, door?, presence?, ask_order? }] }. On their dates they are in
 * `home` and offered at its doors (at `door` if given, else at one of its doors picked by their
 * id) beside anyone drawn in there. Asked for, the caller's `spawn(entry, door)` builds their
 * figure at the step (or returns null and the knock goes unanswered); once let go they walk
 * back in by the same door and `despawn(actor)` takes the figure away. Nothing of theirs is
 * built until they are asked for.
 *
 * L1 holds (data/humans/contract.json § l1): nothing is said, no event of the day is acted
 * out. Every timing is seeded by the person's id, so a harness sees the same hour on every
 * load. Where and what are reconstructed (each record's provenance and liberty); this layer
 * plays them. Nothing here knows the DOM; tools/test_human_days.mjs drives it with stand-ins.
 */

/** FNV-1a into mulberry32, as human-duties.js's (kept here so this imports nothing). */
function seededRandom(key) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < key.length; i++) { h ^= key.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  let a = h || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const DAY_ACTIVITIES = Object.freeze(['stand', 'talk', 'work', 'walk']);
/** Seconds: at each work spot; at each end of a walk; a speaker's turn in a talk. */
export const WORK = Object.freeze({ at_s: [7, 18], first_s: [0, 9] });
export const WALK = Object.freeze({ pause_s: [3, 9] });
export const TALK = Object.freeze({ speak_s: [2.6, 6.8], nod_p: 0.4 });
/** Within this of the visitor a person walks between places; beyond it, is put there. */
export const NEAR_M = 90;
/** A door: how near to stand to it; a knock and the wait before the door is answered. */
export const DOOR_REACH_M = 2.4;
export const ANSWER_S = 2.5;
/** Coming to a visitor, they stop this short; no further from the door than COME_M. */
export const MEET_M = 1.3;
export const COME_M = 9;
/** Called out: they stay STAY_S at most, and leave once the visitor is STAY_M off for LEAVE_S. */
export const STAY_S = 150;
export const STAY_M = 12;
export const LEAVE_S = 4;
/** How many Ask for <name> a door offers at once. */
export const ASK_PAGE = 6;
const HEAD_M = 1.6;
/** T-3504: a talk's ring: neighbours GAP_M apart, never nearer the middle than MIN_R_M; a knot
 *  whose people already stand SPREAD_M apart keeps their own places. */
export const RING = Object.freeze({ gap_m: 0.95, min_r_m: 0.6, spread_m: 0.7 });
/** People standing out at the same time this near one another are one company (they talk). */
export const GROUP_M = 6;
/** One person standing alone, not at a post, works about two spots this far off their place. */
export const POTTER = Object.freeze({ off_m: [1.4, 3.0], spots: 2 });
/** What a post is: the span's own words say the person keeps a watch there. */
export const POST_RE = /\b(sentry|sentinel|sentries|guard|watch|post|picket|lookout)\b/i;

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const pt = (p) => ({ e: p.local_e ?? p.e, n: p.local_n ?? p.n });
const dist = (a, b) => Math.hypot(a.e - b.e, a.n - b.n);

/** Whether ISO `date` ('1812-08-14') lies in { from, to } (inclusive; either may be absent). */
export function onDate(date, window) {
  if (!window || !date) return true;
  const d = String(date).slice(0, 10);
  if (window.from && d < window.from) return false;
  if (window.to && d > window.to) return false;
  if (Array.isArray(window.months) && !window.months.includes(Number(d.slice(5, 7)))) return false;
  if (window.years) {
    const y = Number(d.slice(0, 4));
    if ((window.years.from && y < window.years.from) || (window.years.to && y > window.years.to)) return false;
  }
  return true;
}

/** The day of someone whose `chance` day did not come: away, all day. */
export const AWAY_DAY = Object.freeze({ away_day: true, spans: Object.freeze([Object.freeze({ from: 0, to: 24, indoors: true, away: true })]) });

/** Whether a `chance` day comes for `key` on `date` (seeded: the same on every load). */
export function chanceDay(key, date, chance) {
  if (!(chance < 1)) return true;
  return seededRandom(`chance:${key}:${String(date ?? '').slice(0, 10)}`)() < chance;
}

/** Whether `hour` lies in [from, to); `to` may pass midnight. */
export function inSpan(hour, { from, to }) {
  return from <= to ? hour >= from && hour < to : hour >= from || hour < to;
}

/** The day `behaviour` plays on `date`: the first variant whose dates hold it (for `key`, a
 *  person's id, a `chance` day may not come: then AWAY_DAY). */
export function dayOn(behaviour, date, key = '') {
  const days = behaviour?.day;
  if (!Array.isArray(days)) return null;
  const v = days.find((x) => onDate(date, x.dates)) ?? null;
  if (v && Number.isFinite(v.chance) && !chanceDay(key, date, v.chance)) return AWAY_DAY;
  return v;
}

/** The span of `day` at `hour` (0-24); the first span when the hour is unknown. */
export function spanAt(day, hour) {
  const spans = day?.spans ?? [];
  if (!spans.length) return null;
  if (!Number.isFinite(hour)) return spans[0];
  return spans.find((s) => inSpan(((hour % 24) + 24) % 24, s)) ?? spans[spans.length - 1];
}

/** A short name for a building: its record's name to the first comma. */
export const shortName = (name) => String(name ?? '').split(/[,;(]/)[0].trim();

/**
 * T-3504: places for `ids` (in that order) in a ring about `centre` ({e, n}), each turned to the
 * middle: [{ e, n, heading_deg }]. Seeded by `key`, so a knot stands the same way on every load.
 */
export function ringAbout(centre, ids, key = '') {
  const k = ids.length;
  if (k < 2) return ids.map(() => ({ e: centre.e, n: centre.n, heading_deg: null }));
  const r = Math.max(RING.min_r_m, RING.gap_m / (2 * Math.sin(Math.PI / k)));
  const base = seededRandom(`ring:${key}`)() * 360;
  return ids.map((_, i) => {
    const b = (base + (360 * i) / k) % 360, rad = (b * Math.PI) / 180;
    return { e: centre.e + r * Math.sin(rad), n: centre.n + r * Math.cos(rad), heading_deg: (b + 180) % 360 };
  });
}

const atOf = (span) => ({ e: span.at.local_e, n: span.at.local_n });
const overlaps = (a, b) => {
  const seg = (s) => (s.from <= s.to ? [[s.from, s.to]] : [[s.from, 24], [0, s.to]]);
  return seg(a).some(([a0, a1]) => seg(b).some(([b0, b1]) => a0 < b1 && b0 < a1));
};

/**
 * T-3504: how each out span of each person is played on `date`. `people` is [{ key, b }] (a
 * record's behaviour and its person's key, for `chance` days). Returns a Map span -> played span
 * (a copy: `at` moved onto the person's place in its ring, `activity`/`knot`/`spots` filled in);
 * a span played as written is not in it.
 */
export function planDay(people, date) {
  const out = new Map();
  const outs = [];
  for (const { key, b } of people) {
    const day = dayOn(b, date, key);
    if (!day || day.away_day) continue;
    for (const span of day.spans ?? []) if (!span.indoors && span.at) outs.push({ key, span });
  }
  const play = (span) => { if (!out.has(span)) out.set(span, { ...span, at: { ...span.at } }); return out.get(span); };
  // Lone or in company: everyone standing (not at a post) is grouped with whoever else stands
  // within GROUP_M at an overlapping hour (single linkage).
  const standing = outs.filter((x) => (x.span.activity ?? 'stand') === 'stand' && !POST_RE.test(x.span.doing ?? ''));
  const seen = new Set();
  for (const first of standing) {
    if (seen.has(first)) continue;
    const group = [first];
    seen.add(first);
    for (let i = 0; i < group.length; i++) {
      for (const o of standing) {
        if (seen.has(o) || o.key === group[i].key) continue;
        const a = atOf(group[i].span), c = atOf(o.span);
        if (Math.hypot(a.e - c.e, a.n - c.n) <= GROUP_M && overlaps(group[i].span, o.span)) { seen.add(o); group.push(o); }
      }
    }
    const keys = new Set(group.map((x) => x.key));
    if (keys.size >= 2) {
      const knot = `company:${group[0].key}:${group[0].span.from}`;
      for (const x of group) Object.assign(play(x.span), { activity: 'talk', knot });
    } else {
      // Alone: at a job about the place, two spots a little off it.
      const span = first.span, at = atOf(span), rand = seededRandom(`potter:${first.key}:${span.from}`);
      const spots = [];
      for (let i = 0; i < POTTER.spots; i++) {
        const bearingDeg = (Number.isFinite(span.at.heading_deg) ? span.at.heading_deg : 0) + (i ? 1 : -1) * (40 + rand() * 80);
        const r = POTTER.off_m[0] + (POTTER.off_m[1] - POTTER.off_m[0]) * rand();
        spots.push({ local_e: at.e + r * Math.sin((bearingDeg * Math.PI) / 180), local_n: at.n + r * Math.cos((bearingDeg * Math.PI) / 180) });
      }
      Object.assign(play(span), { activity: 'work', spots });
    }
  }
  // Every knot, written or a company: its people in a ring about its place, unless they already
  // stand apart.
  const knots = new Map();
  for (const x of outs) {
    const s = out.get(x.span) ?? x.span;
    if ((s.activity ?? 'stand') !== 'talk' || !s.knot) continue;
    if (!knots.has(s.knot)) knots.set(s.knot, new Map());
    const members = knots.get(s.knot);
    if (!members.has(x.key)) members.set(x.key, []);
    members.get(x.key).push(x.span);
  }
  for (const [knot, members] of knots) {
    const keys = [...members.keys()].sort();
    if (keys.length < 2) continue;
    const ats = keys.map((k) => atOf(members.get(k)[0]));
    let apart = true;
    for (let i = 0; i < ats.length && apart; i++) for (let j = i + 1; j < ats.length; j++) {
      if (Math.hypot(ats[i].e - ats[j].e, ats[i].n - ats[j].n) < RING.spread_m) { apart = false; break; }
    }
    if (apart) continue;
    const centre = { e: ats.reduce((t, p) => t + p.e, 0) / ats.length, n: ats.reduce((t, p) => t + p.n, 0) / ats.length };
    const ring = ringAbout(centre, keys, knot);
    keys.forEach((k, i) => {
      for (const span of members.get(k)) {
        const p = play(span);
        p.at.local_e = +ring[i].e.toFixed(3); p.at.local_n = +ring[i].n.toFixed(3); p.at.heading_deg = +ring[i].heading_deg.toFixed(1);
      }
    });
  }
  return out;
}

/**
 * @param {object} o
 * @param {{ actors: object[], shown?: boolean, isHeld?: (a: object) => boolean }} o.humans
 * @param {object} [o.three]                   three.js (for gaze points)
 * @param {() => number | null} [o.hour]        local solar hour, 0-24
 * @param {() => string | null} [o.date]        the scene's ISO date
 * @param {object} [o.doors]                    data/humans/doors_1812.json
 * @param {object} [o.interactions]             interact.js's engine
 * @param {() => {e:number, n:number} | null} [o.visitor]   where the visitor stands, on foot
 * @param {() => object | null} [o.eye]         the camera's world position (a Vector3)
 * @param {object} [o.router]                   route.js's planner ({ plan(from, to, {mode}) })
 * @param {string[]} [o.problems]
 */
export function createHumanDays({ humans, three = null, hour = () => null, date = () => null, doors = null,
  interactions = null, visitor = () => null, eye = () => null, router = null, problems = [],
  inside = null, spawn = null, despawn = null } = {}) {
  const Vec = three?.Vector3;
  let people = [];
  let seen = -1;
  let clock = 0;
  const talks = new Map();
  /** T-3504: how today's spans are played (planDay), made again when the date or the people change. */
  let plan = { date: undefined, map: new Map() };
  const playOf = (span) => {
    const today = date();
    if (plan.date !== today) {
      plan = { date: today, map: planDay(people.filter((q) => !q.entry && !q.soldier && Array.isArray(q.b.day))
        .map((q) => ({ key: q.actor.personId ?? q.id, b: q.b })), today) };
    }
    return plan.map.get(span) ?? span;
  };
  const doorThings = [];
  /** Inside-only people (no figure until asked for), and those of them called out now. */
  const insideOnly = (inside?.people ?? []).filter((x) => x?.person && x.home);
  const spawned = [];
  const byStructure = new Map();
  for (const s of doors?.structures ?? []) byStructure.set(s.structure, s);

  const headOf = (actor) => {
    if (Vec && actor.root?.getWorldPosition) { const v = actor.root.getWorldPosition(new Vec()); v.y += HEAD_M; return v; }
    return null;
  };
  const look = (actor, at, seconds) => { const p = headOf(at); if (p) actor.life?.attend?.(p, seconds); };
  const talk = (actor, on) => actor.actions?.setTalk?.(on);
  const near = (e, n) => { const v = visitor(); return !!v && Math.hypot(v.e - e, v.n - n) < NEAR_M; };

  /** The way from a to b, on foot. */
  function way(a, b) {
    const route = router?.plan?.({ e: a.e, n: a.n }, { e: b.e, n: b.n }, { mode: 'walk' });
    const pts = route?.points?.length ? route.points.map(([e, n]) => ({ e, n })) : [];
    return [{ e: a.e, n: a.n }, ...pts.filter((p) => dist(p, a) > 0.05 && dist(p, b) > 0.05), { e: b.e, n: b.n }];
  }

  /** Walk `actor` to `to` (or put them there, far off), facing `heading`; then `done`. */
  function go(p, to, heading, done, { from = null } = {}) {
    const a = p.actor;
    const start = from ?? { e: a.e, n: a.n };
    if (!near(start.e, start.n) && !near(to.e, to.n) || typeof a.walkPath !== 'function' || dist(start, to) < 0.05) {
      a.path = null;
      a.e = to.e; a.n = to.n;
      if (Number.isFinite(heading)) a.heading = heading;
      a.standY = null;
      a.place?.();
      done?.();
      return;
    }
    const token = (p.token = (p.token ?? 0) + 1);
    const ok = a.walkPath(way(start, to), { endHeading: Number.isFinite(heading) ? heading : null,
      onArrive: () => { if (p.token === token) done?.(); } });
    if (!ok) done?.();
  }

  const doorsOf = (structure) => byStructure.get(structure)?.doors ?? [];
  /** The door of `structure` nearest (e, n). */
  function doorNear(structure, e, n) {
    let best = null;
    for (const d of doorsOf(structure)) {
      const s = pt(d.step);
      const k = Number.isFinite(e) ? Math.hypot(s.e - e, s.n - n) : 0;
      if (!best || k < best.k) best = { k, d };
    }
    return best?.d ?? null;
  }

  function collect() {
    people = [];
    for (const actor of humans.actors) {
      if (spawned.some((q) => q.actor === actor)) continue;
      const b = actor.instance?.behaviour;
      if (!b || (!Array.isArray(b.day) && !b.presence && !b.quarters)) continue;
      people.push({
        actor, b, id: actor.id, rand: seededRandom(`day:${actor.id}`), span: null, inside: null,
        mode: actor.indoors ? 'in' : 'out', absent: false, called: null, job: null,
        soldier: Array.isArray(b.hours) && !Array.isArray(b.day),
      });
    }
    people.push(...spawned);
    seen = humans.actors.length;
    plan = { date: undefined, map: new Map() };
  }

  /** Which door of its home an inside-only person answers at. */
  function doorOf(entry, doorsHere) {
    if (entry.door) return doorsHere.find((t) => t.door.id === entry.door) ? entry.door : null;
    if (!doorsHere.length) return null;
    return doorsHere[Math.floor(seededRandom(`inside:${entry.person}`)() * doorsHere.length) % doorsHere.length].door.id;
  }
  /** Inside-only people in `structure` at the door `doorId` today, not already out. */
  function ghostsAt(structure, doorId) {
    const today = date();
    const here = doorThings.filter((t) => t.structure === structure);
    return insideOnly.filter((x) => x.home === structure && onDate(today, x.presence)
      && !spawned.some((q) => q.entry === x) && doorOf(x, here) === doorId);
  }
  /** An inside-only person's figure, built at the door they were asked for at. */
  function summon(entry, door) {
    let actor = null;
    try { actor = spawn?.(entry, door) ?? null; } catch (err) { problems.push(`human-days: ${entry.person} could not be built: ${err?.message ?? err}`); }
    if (!actor) return null;
    const p = { actor, b: { presence: entry.presence, ask_order: entry.ask_order }, id: actor.id ?? `inside:${entry.person}`,
      rand: seededRandom(`day:${entry.person}`), span: null, inside: door.structure, mode: 'in', absent: false,
      called: null, job: null, soldier: false, entry };
    actor.personId ??= entry.person;
    actor.setIndoors?.(true);
    spawned.push(p);
    people.push(p);
    return p;
  }
  /** Back in: the figure goes. */
  function retire(p) {
    const k = spawned.indexOf(p);
    if (k >= 0) spawned.splice(k, 1);
    const i = people.indexOf(p);
    if (i >= 0) people.splice(i, 1);
    p.actor.disposed = true;
    try { despawn?.(p.actor); } catch (err) { problems.push(`human-days: ${p.entry.person} could not be taken away: ${err?.message ?? err}`); }
  }

  function goIn(p, structure) {
    const a = p.actor;
    p.inside = structure;
    if (a.indoors) { p.mode = 'in'; return; }
    const door = doorNear(structure, a.e, a.n);
    if (!door || !near(a.e, a.n)) { a.path = null; a.setIndoors?.(true); p.mode = 'in'; return; }
    p.mode = 'going_in';
    const step = pt(door.step), leaf = pt(door.leaf);
    go(p, step, (door.outward_deg + 180) % 360, () => {
      const t = ++p.token;
      if (!a.walkPath?.([step, leaf], { onArrive: () => { if (p.token === t) { a.setIndoors?.(true); p.mode = 'in'; } } })) {
        a.setIndoors?.(true); p.mode = 'in';
      }
    });
  }

  function comeOut(p, span) {
    const a = p.actor;
    const to = pt(span.at);
    let from = null;
    if (a.indoors) {
      const door = p.inside ? doorNear(p.inside, to.e, to.n) : null;
      from = door ? pt(door.step) : to;
      a.e = from.e; a.n = from.n; a.standY = null;
      a.heading = door ? door.outward_deg : (span.at.heading_deg ?? a.heading);
      a.setIndoors?.(false);
      a.place?.();
    }
    p.inside = null;
    p.mode = 'going_out';
    go(p, to, span.at.heading_deg, () => { p.mode = 'out'; startActivity(p, span); }, { from });
  }

  function startActivity(p, span) {
    const a = p.actor;
    const act = span.activity ?? 'stand';
    p.job = null;
    a.setState?.(act === 'talk' ? 'talking' : act === 'work' ? 'working' : 'standing');
    if (act === 'work') {
      const spots = [pt(span.at), ...(span.spots ?? []).map(pt)];
      p.job = { kind: 'work', spots, at: 0, until: clock + between(p, WORK.first_s), moving: false,
        face: span.at.heading_deg };
    } else if (act === 'walk' && span.to_point) {
      const route = [pt(span.at), ...(span.via ?? []).map(pt), pt(span.to_point)];
      p.job = { kind: 'walk', route, at: 0, dir: 1, once: !!span.once, until: clock + (span.once ? 0 : between(p, WALK.pause_s)),
        moving: false, face: span.at.heading_deg };
    }
  }

  const between = (p, [lo, hi]) => lo + (hi - lo) * p.rand();

  function stepJob(p) {
    const j = p.job;
    if (!j || j.moving || clock < j.until) return;
    j.moving = true;
    let next, face;
    if (j.kind === 'work') {
      // Back to the first place between each of the others, as a man at a woodpile or a bench goes.
      next = j.at === 0 ? 1 + Math.floor(p.rand() * Math.max(1, j.spots.length - 1)) : 0;
      if (j.spots.length < 2) next = 0;
      face = j.face;
      const to = j.spots[next];
      go(p, to, face, () => { j.at = next; j.moving = false; j.until = clock + between(p, WORK.at_s); p.actor.setState?.('working'); });
    } else {
      // Along the route a point at a time; a pause only at its ends. Walked once, they stop at
      // its end, turned the way they came in.
      const last = j.route.length - 1;
      if (j.once && j.at === last) { p.job = null; p.actor.setState?.('standing'); return; }
      if (j.at === last) j.dir = -1;
      else if (j.at === 0) j.dir = 1;
      next = j.at + j.dir;
      const to = j.route[next], other = j.route[j.at];
      face = bearing(to.e - other.e, to.n - other.n);
      const end = next === 0 || next === last;
      go(p, to, Number.isFinite(j.face) && next === 0 && !j.once ? j.face : face, () => {
        j.at = next; j.moving = false; j.until = clock + (end && !j.once ? between(p, WALK.pause_s) : 0);
      });
    }
  }

  /** Move a person to `span` (the hour has turned, or they were let go from a call). */
  function enter(p, written) {
    const a = p.actor;
    p.span = written;
    const span = p.play = playOf(written);
    p.job = null;
    p.token = (p.token ?? 0) + 1;
    if (span.away) { talk(a, false); a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.inside = null; return; }
    if (span.indoors) { talk(a, false); goIn(p, span.where); return; }
    comeOut(p, span);
  }

  /** Talks: everyone out whose span names the same knot, arrived, talks together. */
  function stepTalks(dt) {
    const groups = new Map();
    for (const p of people) {
      const s = p.play ?? p.span;
      if (p.mode !== 'out' || p.called || !s || s.activity !== 'talk' || !s.knot) continue;
      if (humans.isHeld?.(p.actor)) continue;
      if (!groups.has(s.knot)) groups.set(s.knot, []);
      groups.get(s.knot).push(p);
    }
    for (const [id, g] of talks) if (!groups.has(id)) { if (g.speaker) talk(g.speaker.actor, false); talks.delete(id); }
    for (const [id, here] of groups) {
      if (!talks.has(id)) talks.set(id, { rand: seededRandom(`talk:${id}`), speaker: null, t: 0.5 });
      const g = talks.get(id);
      g.t -= dt;
      if (g.speaker && !here.includes(g.speaker)) { talk(g.speaker.actor, false); g.speaker = null; g.t = 0; }
      if (g.t > 0) continue;
      if (g.speaker) talk(g.speaker.actor, false);
      if (here.length < 2) { g.speaker = null; g.t = 1; continue; }
      const others = here.filter((m) => m !== g.speaker);
      const next = others[Math.floor(g.rand() * others.length)];
      const span = TALK.speak_s[0] + (TALK.speak_s[1] - TALK.speak_s[0]) * g.rand();
      g.speaker = next; g.t = span;
      talk(next.actor, true);
      const listeners = here.filter((m) => m !== next);
      look(next.actor, listeners[Math.floor(g.rand() * listeners.length)].actor, span);
      for (const m of listeners) {
        look(m.actor, next.actor, span + 0.4);
        if (g.rand() < TALK.nod_p) m.actor.life?.nod?.();
      }
    }
  }

  // ── Asked for at a door ─────────────────────────────────────────────────────────────
  /** Who is in `structure` now and can be asked for: present, in, not already called out. */
  function within(structure) {
    return people.filter((p) => !p.absent && !p.called && p.actor.indoors
      && (p.soldier ? p.b.quarters === structure : p.mode === 'in' && p.inside === structure))
      .sort((x, y) => (x.b.ask_order ?? 50) - (y.b.ask_order ?? 50) || nameOf(x).localeCompare(nameOf(y)));
  }
  const nameOf = (p) => p.entry?.name ?? p.actor.person?.name ?? p.actor.identity?.person?.name ?? p.actor.instance?.display_name ?? p.actor.personId ?? p.actor.id;

  function callOut(p, door) {
    const a = p.actor;
    const step = pt(door.step);
    p.called = { door, since: clock, off: 0 };
    p.job = null;
    p.token = (p.token ?? 0) + 1;
    a.e = step.e; a.n = step.n; a.standY = null; a.heading = door.outward_deg;
    a.setIndoors?.(false);
    a.place?.();
    p.mode = 'called';
    const v = visitor();
    if (!v) return;
    const d = dist(step, v);
    const go_m = Math.max(0, Math.min(COME_M, d - MEET_M));
    const to = d > 1e-6 ? { e: step.e + (v.e - step.e) * go_m / d, n: step.n + (v.n - step.n) * go_m / d } : step;
    const face = bearing(v.e - to.e, v.n - to.n);
    const greet = () => {
      const w = visitor();
      if (w) a.turnTo?.(bearing(w.e - a.e, w.n - a.n));
      const e = eye();
      if (e) a.life?.attend?.(e, 6);
      a.actions?.greet?.();
    };
    if (go_m < 0.2) { a.heading = face; a.place?.(); greet(); return; }
    const t = p.token;
    if (!a.walkPath?.([step, to], { endHeading: face, onArrive: () => { if (p.token === t) greet(); } })) greet();
  }

  function stepCalled(p, dt) {
    const c = p.called;
    const v = visitor();
    const off = !v || Math.hypot(v.e - p.actor.e, v.n - p.actor.n) > STAY_M;
    c.off = off ? c.off + dt : 0;
    if (clock - c.since < STAY_S && c.off < LEAVE_S) return;
    // Let go: back in by the door they came out of, or on to the hour's place.
    p.called = null;
    if (p.soldier || p.entry) {
      const back = c.door;
      p.inside = p.entry ? back.structure : p.b.quarters;
      p.mode = 'going_in';
      const step = pt(back.step), leaf = pt(back.leaf);
      const inAgain = () => { p.actor.setIndoors?.(true); p.mode = 'in'; if (p.entry) retire(p); };
      go(p, step, (back.outward_deg + 180) % 360, () => {
        const t = ++p.token;
        if (!p.actor.walkPath?.([step, leaf], { onArrive: () => { if (p.token === t) inAgain(); } })) inAgain();
      });
      return;
    }
    p.inside = c.door.structure;
    p.span = null;
  }

  function makeDoors() {
    if (!interactions) return;
    const wanted = new Set();
    for (const p of people) {
      if (p.b.quarters) wanted.add(p.b.quarters);
      for (const v of p.b.day ?? []) for (const s of v.spans ?? []) if (s.indoors && s.where) wanted.add(s.where);
    }
    if (spawn) for (const x of insideOnly) wanted.add(x.home);
    for (const structure of wanted) {
      const rec = byStructure.get(structure);
      if (!rec) { problems.push(`human-days: no door is known for ${structure}; who is in it cannot be asked for`); continue; }
      const label = shortName(rec.name) || structure;
      for (const door of rec.doors) {
        let page = 0;
        const d = { ...door, structure };
        const thing = {
          id: `door:${door.id}`, kind: 'door', name: `${label}, door`, structure, door: d,
          states: ['shut'], state: 'shut',
          get at() { return humans.shown === false ? null : [door.step.local_e, door.step.local_n]; },
          reach: DOOR_REACH_M,
          actions: {
            get shut() {
              const inside = [...within(structure).map((p) => ({ p, name: nameOf(p), order: p.b.ask_order ?? 50 })),
                ...(spawn ? ghostsAt(structure, door.id) : []).map((x) => ({ entry: x, name: x.name ?? x.person, order: x.ask_order ?? 50 }))]
                .sort((x, y) => x.order - y.order || x.name.localeCompare(y.name));
              if (!inside.length) {
                return [{ id: 'knock', label: 'Knock', said: 'No one comes to the door', steps: [{ label: 'Knocking', seconds: ANSWER_S }] }];
              }
              const pages = Math.ceil(inside.length / ASK_PAGE);
              page %= pages;
              const shown = inside.slice(page * ASK_PAGE, page * ASK_PAGE + ASK_PAGE);
              const asks = shown.map(({ p, entry, name }) => (p ? {
                id: `ask:${p.actor.personId ?? p.id}`, label: `Ask for ${name}`, said: () => `${name} comes to the door`,
                refuse: () => (p.called || !p.actor.indoors ? `${name} is not in` : null),
                steps: [{ label: 'Knocking', seconds: ANSWER_S, run: (t) => { if (t >= 1) callOut(p, d); } }],
              } : {
                id: `ask:${entry.person}`, label: `Ask for ${name}`, said: () => `${name} comes to the door`,
                refuse: () => (spawned.some((q) => q.entry === entry) ? `${name} is not in` : null),
                steps: [{ label: 'Knocking', seconds: ANSWER_S, run: (t) => { if (t >= 1) { const q = summon(entry, d); if (q) callOut(q, d); } } }],
              }));
              if (pages > 1) asks.push({ id: 'others', label: 'Others inside…', said: '', steps: [{ label: '', seconds: 0, run: (t) => { if (t === 0) page += 1; } }] });
              return asks;
            },
          },
        };
        interactions.add(thing);
        doorThings.push(thing);
      }
    }
  }

  const api = {
    get people() { return people; },
    get doors() { return doorThings; },
    /** One frame, after humans.update and the duties. */
    update(dt) {
      if (!humans || !(dt > 0)) return;
      if (humans.actors.length !== seen) { collect(); if (!doorThings.length) makeDoors(); }
      dt = Math.min(dt, 0.25);
      clock += dt;
      const h = hour();
      const today = date();
      for (const p of [...people]) {
        const a = p.actor;
        if (a.disposed) continue;
        if (p.entry) {   // an inside-only person out at the door: theirs is only the call
          if (!onDate(today, p.b.presence)) retire(p);
          else if (p.called) stepCalled(p, dt);
          continue;
        }
        // Off their dates, or on a date their days do not cover (15 August is the battle
        // jaunt's), nowhere.
        const present = onDate(today, p.b.presence) && (!Array.isArray(p.b.day) || !!dayOn(p.b, today, p.actor.personId ?? p.id));
        if (!present) {
          if (!p.absent) { p.absent = true; p.called = null; p.span = null; p.job = null; a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.inside = null; }
          continue;
        }
        if (p.absent) { p.absent = false; if (p.soldier) a.setIndoors?.(false); }
        if (p.called) { stepCalled(p, dt); continue; }
        if (p.soldier) continue;   // his hours are human-duties.js's
        const span = spanAt(dayOn(p.b, today, p.actor.personId ?? p.id), h);
        if (!span) continue;
        if (span !== p.span) enter(p, span);
        else if (p.mode === 'out') stepJob(p);
      }
      stepTalks(dt);
    },
    /** Ask for someone at their door now, as the door's Ask for does: { ok, why }. */
    ask(personOrInstance) {
      const p = people.find((x) => x.actor.personId === personOrInstance || x.id === personOrInstance);
      const entry = !p && spawn ? insideOnly.find((x) => x.person === personOrInstance) : null;
      if (entry) {
        if (!onDate(date(), entry.presence)) return { ok: false, why: 'not here on this date' };
        if (spawned.some((q) => q.entry === entry)) return { ok: false, why: 'not indoors' };
        const here = doorThings.filter((t) => t.structure === entry.home);
        const id = doorOf(entry, here);
        const door = here.find((t) => t.door.id === id);
        if (!door) return { ok: false, why: `no door known for ${entry.home}` };
        const q = summon(entry, door.door);
        if (!q) return { ok: false, why: 'could not be built' };
        callOut(q, door.door);
        return { ok: true, door: door.id };
      }
      if (!p) return { ok: false, why: 'no such person' };
      if (p.absent) return { ok: false, why: 'not here on this date' };
      if (!p.actor.indoors || p.called) return { ok: false, why: 'not indoors' };
      const structure = p.soldier ? p.b.quarters : p.inside;
      const door = doorThings.find((t) => t.structure === structure);
      if (!door) return { ok: false, why: `no door known for ${structure}` };
      callOut(p, door.door);
      return { ok: true, door: door.id };
    },
    /** Whether a person is held out by a call (human-duties.js leaves them be). */
    isCalled: (actor) => !!people.find((p) => p.actor === actor)?.called,
    /** The inside-only people (no figure until asked for), and how many are out now. */
    get insideOnly() { return { listed: insideOnly.length, out: spawned.length }; },
    /** Who is where, for the harness. */
    snapshot() {
      return people.map((p) => ({
        person: p.actor.personId, instance: p.id, absent: p.absent, mode: p.mode, indoors: !!p.actor.indoors,
        inside: p.actor.indoors ? (p.soldier ? p.b.quarters ?? null : p.inside) : null,
        span: p.span ? { from: p.span.from, to: p.span.to, activity: p.span.indoors ? 'indoors' : (p.play ?? p.span).activity ?? 'stand', where: p.span.where ?? null } : null,
        called: !!p.called, e: +p.actor.e.toFixed(2), n: +p.actor.n.toFixed(2),
      }));
    },
  };
  return api;
}
