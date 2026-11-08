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
 * A PURPOSE FOR EVERY PART OF THE DAY (T-3505). The owner, 2026-11-08: *"I do not want to have
 * everyone standing in groups talking, it's fine if there are conversations that come together
 * and break up, but the whole day of theirs should not be spent talking, they should be doing
 * something their duty or other normal activities. Some if not many can be inside"*, and *"the
 * people should look natural that they are doing ordinary things on a loop ... They can take
 * breaks and go in and out of houses and buildings"*. The hour on the scene's clock stands still
 * while the visitor looks about, so a span is played as a round, on the layer's own clock (real
 * seconds), seeded so that a harness sees the same round on every load:
 *   - a talk (written, or a company) is a GATHERING that comes and goes: every GATHER.every_s or
 *     so (the knot's own beat) its people come together for GATHER.for_s, each of them seeded to
 *     come or not that time (join_p, two at least), stand in its ring and talk, and part again;
 *   - between gatherings each of them is at their OWN job, a few metres out from the ring and
 *     turned from it (OWN: a spot and two more about it, worked to and fro), or, a child, at play
 *     (PLAY: running between three places further off); a talk that names no one else is a job;
 *   - out at a job or a talk, someone whose day has them in a building whose door is within
 *     BREAK.reach_m of their place now and then goes in for a while and comes out again (BREAK):
 *     the door offers Ask for them while they are in, as for anyone inside;
 *   - a job's and a play's places are clear of every building and never across a wall
 *     (`clearWayOf`, the footprints the walker keeps out of), else tried at another bearing.
 * A figure the visitor can see but who is beyond NEAR_M keeps their round where it is (no jump
 * from a job to a ring in plain view); within it they walk from one to the next.
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
/** T-3505: a gathering's beat (each knot its own, seconds), how long it lasts, the chance each of
 *  its people comes to it; people further apart than spread_m gather at their own places. */
export const GATHER = Object.freeze({ every_s: [75, 150], for_s: [24, 52], join_p: 0.75, spread_m: 6 });
/** T-3505: one's own job between gatherings: out_m from the ring, its two more spots off_m about it. */
export const OWN = Object.freeze({ out_m: [1.8, 3.4], off_m: [1.2, 2.6], spots: 2, tries: 6 });
/** T-3505: a child's play between gatherings: three places this far about where they stood. */
export const PLAY = Object.freeze({ off_m: [2.5, 6], spots: 2 });
/** T-3505: a break indoors: a door this near; a beat of every_s, the break for_s, in p of beats. */
export const BREAK = Object.freeze({ reach_m: 45, every_s: [150, 330], for_s: [28, 75], p: 0.55 });
/** What a child is, by the dress drawn. */
export const CHILD_RE = /(^|_)(child|boy|girl|toddler)(_|$)/;
const lerp = ([lo, hi], t) => lo + (hi - lo) * t;

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

/** Whether segments p0-p1 and a-b cross ({e, n} or [e, n]). */
const xy = (p) => (Array.isArray(p) ? { e: p[0], n: p[1] } : pt(p));
function segCross(p0, p1, a, b) {
  const A = xy(a), B = xy(b);
  const d = (p, q, r) => (q.e - p.e) * (r.n - p.n) - (q.n - p.n) * (r.e - p.e);
  const d1 = d(A, B, p0), d2 = d(A, B, p1), d3 = d(p0, p1, A), d4 = d(p0, p1, B);
  return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
}
function segDist(p, a, b) {
  const A = xy(a), B = xy(b), de = B.e - A.e, dn = B.n - A.n, L = de * de + dn * dn;
  const t = L < 1e-12 ? 0 : Math.max(0, Math.min(1, ((p.e - A.e) * de + (p.n - A.n) * dn) / L));
  return Math.hypot(A.e + t * de - p.e, A.n + t * dn - p.n);
}
function insidePoly(p, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > p.n) !== (yj > p.n) && p.e < ((xj - xi) * (p.n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

/**
 * T-3505: `clear(a, b)` for walker.js footprints ([{ pts, walls?, ground? }]): whether one may
 * walk from a to b ({e, n}) and stand at b: b neither in a building nor within `margin_m` of
 * one, the way crossing none, nor a wall (an enclosure's, as fort-gates.js gives it). A parade is
 * ground. The footprints are read when asked (a layer may give one walls later).
 */
export function clearWayOf(footprints = [], { margin_m = 0.5 } = {}) {
  const box = new WeakMap();
  const boxOf = (fp) => {
    if (!box.has(fp)) {
      let e0 = Infinity, n0 = Infinity, e1 = -Infinity, n1 = -Infinity;
      for (const [e, n] of fp.pts ?? []) { e0 = Math.min(e0, e); n0 = Math.min(n0, n); e1 = Math.max(e1, e); n1 = Math.max(n1, n); }
      box.set(fp, { e0, n0, e1, n1 });
    }
    return box.get(fp);
  };
  return (a, b) => {
    const lo = { e: Math.min(a.e, b.e) - margin_m, n: Math.min(a.n, b.n) - margin_m };
    const hi = { e: Math.max(a.e, b.e) + margin_m, n: Math.max(a.n, b.n) + margin_m };
    for (const fp of footprints) {
      if (fp.ground) continue;
      if (Array.isArray(fp.walls)) {
        for (const w of fp.walls) if (segCross(a, b, w.a, w.b) || segDist(b, w.a, w.b) < margin_m) return false;
        continue;
      }
      const pts = fp.pts;
      if (!Array.isArray(pts) || pts.length < 3) continue;
      const k = boxOf(fp);
      if (k.e1 < lo.e || k.e0 > hi.e || k.n1 < lo.n || k.n0 > hi.n) continue;
      if (insidePoly(b, pts)) return false;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        if (segCross(a, b, pts[j], pts[i]) || segDist(b, pts[j], pts[i]) < margin_m) return false;
      }
    }
    return true;
  };
}

const toward = (p, deg, r) => ({ e: p.e + r * Math.sin((deg * Math.PI) / 180), n: p.n + r * Math.cos((deg * Math.PI) / 180) });
const local = (p, heading) => (heading === undefined ? { local_e: +p.e.toFixed(3), local_n: +p.n.toFixed(3) }
  : { local_e: +p.e.toFixed(3), local_n: +p.n.toFixed(3), heading_deg: +(((heading % 360) + 360) % 360).toFixed(1) });

/**
 * T-3505: a job about `at` ({e, n}), turned to `face` (degrees): its first place `out` metres off
 * along `face` (or at a turn of it, where that one is not clear), then `n` spots `off` metres
 * about that, each clear of buildings and walls from the first. -> { anchor, face, spots }.
 */
export function jobAbout(at, face, rand, clear = () => true, { out = 0, off = POTTER.off_m, n = POTTER.spots } = {}) {
  let anchor = at;
  if (out > 0) {
    anchor = null;
    for (const t of [0, 35, -35, 70, -70, 110, -110, 180]) {
      const q = toward(at, face + t, out);
      if (clear(at, q)) { anchor = q; face += t; break; }
    }
    anchor ??= at;
  }
  const spots = [];
  for (let i = 0; i < n; i++) {
    const side = i % 2 ? 1 : -1, b0 = face + side * (40 + rand() * 80), r = off[0] + (off[1] - off[0]) * rand();
    for (let k = 0; k < OWN.tries; k++) {
      const q = toward(anchor, b0 + side * k * 47, r);
      if (clear(anchor, q) && spots.every((s) => dist(s, q) > 0.8)) { spots.push(q); break; }
    }
  }
  return { anchor, face: ((face % 360) + 360) % 360, spots };
}

/**
 * T-3504: how each out span of each person is played on `date`. `people` is [{ key, b }] (a
 * record's behaviour and its person's key, for `chance` days). Returns a Map span -> played span
 * (a copy: `at` moved onto the person's place in its ring, `activity`/`knot`/`spots` filled in);
 * a span played as written is not in it.
 */
export function planDay(people, date, { clear = () => true } = {}) {
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
      // Alone: at a job about the place, two spots a little off it (clear of buildings).
      const span = first.span, rand = seededRandom(`potter:${first.key}:${span.from}`);
      const job = jobAbout(atOf(span), Number.isFinite(span.at.heading_deg) ? span.at.heading_deg : 0, rand, clear);
      Object.assign(play(span), { activity: 'work', spots: job.spots.map((q) => local(q)) });
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
  // T-3505: places of work that several people's jobs share at once (three of the militia at one
  // spot) are made one place each, in a ring about it, as a talk's are.
  const works = [];
  for (const x of outs) {
    const s = out.get(x.span) ?? x.span;
    if (s.activity !== 'work') continue;
    works.push({ x, s, pts: [s.at, ...(s.spots ?? [])] });
  }
  const SHARE_M = 0.65;
  const taken = new Set();
  for (let i = 0; i < works.length; i++) {
    for (let a = 0; a < works[i].pts.length; a++) {
      const tag = `${i}:${a}`;
      if (taken.has(tag)) continue;
      const here = pt(works[i].pts[a]);
      const group = [{ w: i, k: a }];
      for (let j = 0; j < works.length; j++) {
        if (j === i || works[j].x.key === works[i].x.key || !overlaps(works[i].s, works[j].s)) continue;
        for (let b = 0; b < works[j].pts.length; b++) {
          if (taken.has(`${j}:${b}`) || dist(pt(works[j].pts[b]), here) >= SHARE_M) continue;
          if (group.some((g) => g.w === j)) continue;
          group.push({ w: j, k: b });
        }
      }
      if (group.length < 2) continue;
      for (const g of group) taken.add(`${g.w}:${g.k}`);
      const ring = ringAbout(here, group.map((g) => works[g.w].x.key), `spot:${here.e.toFixed(1)}:${here.n.toFixed(1)}`);
      group.forEach((g, m) => {
        const w = works[g.w], p = play(w.x.span);
        if (!p.spots || p.spots === w.x.span.spots) p.spots = (w.x.span.spots ?? []).map((q) => ({ ...q }));
        const q = g.k === 0 ? p.at : p.spots[g.k - 1];
        q.local_e = +ring[m].e.toFixed(3); q.local_n = +ring[m].n.toFixed(3);
        w.s = p;
      });
    }
  }
  // T-3505: every talk a gathering that comes and goes, with each one's own job (a child's play)
  // between; a talk with no one else in it, a job.
  const centres = new Map();
  for (const [knot, members] of knots) {
    if (members.size < 2) continue;
    const ats = [...members.values()].map((spans) => atOf(out.get(spans[0]) ?? spans[0]));
    let far = 0;
    for (let i = 0; i < ats.length; i++) for (let j = i + 1; j < ats.length; j++) far = Math.max(far, dist(ats[i], ats[j]));
    centres.set(knot, far <= GATHER.spread_m
      ? { e: ats.reduce((t, p) => t + p.e, 0) / ats.length, n: ats.reduce((t, p) => t + p.n, 0) / ats.length } : null);
  }
  const children = new Set(people.filter((q) => q.child).map((q) => q.key));
  for (const x of outs) {
    const s = out.get(x.span) ?? x.span;
    if (s.activity !== 'talk') continue;
    const rand = seededRandom(`own:${x.key}:${x.span.from}`);
    const at = atOf(s), face0 = Number.isFinite(s.at.heading_deg) ? s.at.heading_deg : rand() * 360;
    if (!s.knot || (knots.get(s.knot)?.size ?? 0) < 2) {
      const job = jobAbout(at, face0, rand, clear);
      const p = play(x.span);
      p.activity = 'work'; p.spots = job.spots.map((q) => local(q)); delete p.knot;
      continue;
    }
    const centre = centres.get(s.knot);
    // Out from the ring, turned from it (at their own place when the knot's people stand apart).
    const away = centre && dist(at, centre) > 0.05 ? bearing(at.e - centre.e, at.n - centre.n) : (face0 + 180) % 360;
    const child = children.has(x.key);
    const job = centre
      ? jobAbout(at, away, rand, clear, { out: lerp(OWN.out_m, rand()), off: child ? PLAY.off_m : OWN.off_m, n: child ? PLAY.spots : OWN.spots })
      : jobAbout(at, away, rand, clear, { off: child ? PLAY.off_m : POTTER.off_m, n: child ? PLAY.spots : POTTER.spots });
    const own = { from: s.from, to: s.to, indoors: false, doing: s.doing, at: local(job.anchor, job.face) };
    if (child && job.spots.length) {
      Object.assign(own, { activity: 'walk', to_point: local(job.spots.at(-1)) });
      if (job.spots.length > 1 && clear(job.spots[0], job.spots[1])) own.via = [local(job.spots[0])];
    } else Object.assign(own, { activity: 'work', spots: job.spots.map((q) => local(q)) });
    play(x.span).round = { knot: s.knot, own };
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
 * @param {(a: {e:number, n:number}, b: {e:number, n:number}) => boolean} [o.clear]  T-3505: whether a
 *                                              job's way from a to b is clear (clearWayOf)
 */
export function createHumanDays({ humans, three = null, hour = () => null, date = () => null, doors = null,
  interactions = null, visitor = () => null, eye = () => null, router = null, problems = [],
  inside = null, spawn = null, despawn = null, clear = () => true } = {}) {
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
        .map((q) => ({ key: q.actor.personId ?? q.id, b: q.b, child: CHILD_RE.test(q.actor.instance?.appearance?.asset_id ?? '') })),
      today, { clear }) };
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
    p.round = null; p.phase = null; p.cur = null;
    if (span.away) { talk(a, false); a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.inside = null; return; }
    if (span.indoors) { talk(a, false); goIn(p, span.where); return; }
    // T-3505: a talk or a job is played as a round: gatherings, one's own job, breaks indoors.
    const act = span.activity ?? 'stand';
    if (span.round || act === 'work') {
      p.round = { knot: span.round?.knot ?? null, talk: span, own: span.round?.own ?? span, home: homeOf(p, span) };
      phaseTo(p, want(p));
      return;
    }
    comeOut(p, span);
  }

  // ── T-3505: rounds ──────────────────────────────────────────────────────────────────
  const keyOf = (p) => p.actor.personId ?? p.id;
  /** The building of today's day whose door is nearest the span's place, within BREAK.reach_m. */
  function homeOf(p, span) {
    const day = dayOn(p.b, date(), keyOf(p));
    const at = pt(span.at);
    let best = null;
    for (const where of new Set((day?.spans ?? []).filter((s) => s.indoors && !s.away && s.where).map((s) => s.where))) {
      const d = doorNear(where, at.e, at.n);
      const k = d ? dist(pt(d.step), at) : Infinity;
      if (k <= BREAK.reach_m && (!best || k < best.k)) best = { k, where };
    }
    return best?.where ?? null;
  }
  /** The knots' gatherings, worked out once a frame: { on, cycle, joined: Set of people }. */
  const gathers = new Map();
  let frame = 0;
  let byKnot = new Map();
  function gathering(knot) {
    let g = gathers.get(knot);
    if (!g) {
      const r = seededRandom(`gather:${knot}`);
      const every = lerp(GATHER.every_s, r());
      g = { every, off: r() * every, cycle: null, on: false, joined: new Set(), order: new Map(), frame: -1 };
      gathers.set(knot, g);
    }
    if (g.frame === frame) return g;
    g.frame = frame;
    const t = clock + g.off, c = Math.floor(t / g.every);
    if (c !== g.cycle) { g.cycle = c; g.joined.clear(); g.order.clear(); g.len = lerp(GATHER.for_s, seededRandom(`gather:${knot}:${c}`)()); }
    g.on = t - c * g.every < g.len;
    if (!g.on) { g.joined.clear(); return g; }
    const here = (byKnot.get(knot) ?? []).filter((q) => !q.called && !q.absent && q.phase !== 'in');
    for (const q of [...g.joined]) if (!here.includes(q)) g.joined.delete(q);
    const order = (q) => {
      if (!g.order.has(q)) g.order.set(q, seededRandom(`join:${knot}:${c}:${keyOf(q)}`)());
      return g.order.get(q);
    };
    for (const q of here) if (order(q) < GATHER.join_p) g.joined.add(q);
    if (g.joined.size < 2) for (const q of [...here].sort((x, y) => order(x) - order(y))) { if (g.joined.size >= 2) break; g.joined.add(q); }
    if (g.joined.size < 2) g.joined.clear();
    return g;
  }
  /** Whether it is a while indoors for `p` now (their own beat). */
  function breakOn(p) {
    if (!p.brk) {
      const r = seededRandom(`break:${keyOf(p)}`);
      const every = lerp(BREAK.every_s, r());
      p.brk = { every, off: r() * every };
    }
    const t = clock + p.brk.off, c = Math.floor(t / p.brk.every);
    const r = seededRandom(`break:${keyOf(p)}:${c}`);
    return r() < BREAK.p && t - c * p.brk.every < lerp(BREAK.for_s, r());
  }
  /** What the round has `p` at now: 'talk', 'in' (a break) or 'own'. */
  function want(p) {
    const r = p.round;
    if (r.knot && gathering(r.knot).joined.has(p)) return 'talk';
    if (r.home && breakOn(p) && (p.phase === 'in' || near(p.actor.e, p.actor.n))) return 'in';
    return 'own';
  }
  function phaseTo(p, phase) {
    const a = p.actor, r = p.round;
    p.phase = phase; p.job = null;
    p.token = (p.token ?? 0) + 1;
    talk(a, false);
    if (phase === 'in') { p.cur = null; goIn(p, r.home); return; }
    const span = phase === 'talk' ? r.talk : r.own;
    p.cur = span;
    if (a.indoors) { comeOut(p, span); return; }
    p.inside = null;
    p.mode = 'going_out';
    go(p, pt(span.at), span.at.heading_deg, () => { p.mode = 'out'; startActivity(p, span); });
  }
  function stepRound(p) {
    const w = want(p);
    // Seen from beyond NEAR_M, a figure keeps to what it is at (no jump in plain view).
    if (w !== p.phase && (near(p.actor.e, p.actor.n) || !p.actor.root?.visible)) phaseTo(p, w);
    else if (p.mode === 'out') stepJob(p);
  }

  /** Talks: everyone out whose span names the same knot, arrived, talks together. */
  function stepTalks(dt) {
    const groups = new Map();
    for (const p of people) {
      const s = p.round ? p.cur : (p.play ?? p.span);
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
      frame++;
      byKnot = new Map();
      for (const p of people) {
        const k = p.round?.knot;
        if (!k) continue;
        if (!byKnot.has(k)) byKnot.set(k, []);
        byKnot.get(k).push(p);
      }
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
        else if (p.round) stepRound(p);
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
        span: p.span ? { from: p.span.from, to: p.span.to, where: p.span.where ?? null,
          activity: p.span.indoors || p.phase === 'in' ? 'indoors' : ((p.round ? p.cur : null) ?? p.play ?? p.span).activity ?? 'stand' } : null,
        phase: p.phase ?? null, home: p.round?.home ?? null,
        called: !!p.called, e: +p.actor.e.toFixed(2), n: +p.actor.n.toFixed(2),
      }));
    },
  };
  return api;
}
