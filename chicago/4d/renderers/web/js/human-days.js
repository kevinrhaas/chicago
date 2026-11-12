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
 * EVERY YEAR (T-3516): main.js plays 1835's and 1904's people's days too, each by its own
 * data/humans/doors_<year>.json (tools/derive_doors_scene.py); their days are written by
 * docs/RESEARCH/people-days-1835-1904/days.py. A talk whose people stand further apart than
 * GATHER.spread_m (the Glessner court's cook, cook and stable helper) gathers in a ring about the
 * one of them nearest their middle; each keeps a job about their own place between.
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
 * DOORS THAT OPEN, STAIRS THAT ARE CLIMBED (T-3524). The owner, 2026-11-08, of the Glessner
 * court: *"when people enter the glessner house from the rear they just kind of disappear at the
 * staircase i think the door should work and the stairs and they should come up and down the
 * stairs"*. A door the caller's `passages` knows by its id (house-doors.js § passages: Glessner's
 * court service entrance and its Eighteenth Street side door) is walked through, not vanished
 * at: going in, a person walks to the foot of its way, up every tread to the door, which opens
 * before them (it starts to as they come within OPEN_AHEAD_M; they wait at it till it is open),
 * through it, and only then are they indoors, and it shuts behind them; coming out, it opens,
 * they step out of the dark behind it, it shuts once they are PASSAGE.shut_past_m past it, and
 * they walk down to the ground. A person called to the door comes down it to the visitor and
 * goes back up it. While anyone is on the way they finish it (no new hour, round or call
 * turns them on a stair); the way is used one direction at a time, a follower PASSAGE.follow_s
 * behind whoever went before, so nobody meets anybody on a tread; the door stays open while
 * anyone holds it. Far from the visitor (beyond NEAR_M), as before, they are put in or out.
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
 *  its people comes to it. T-3516: people further apart than spread_m gather in a ring about the
 *  one of them nearest their middle, those within reach_m of that one. */
export const GATHER = Object.freeze({ every_s: [75, 150], for_s: [24, 52], join_p: 0.75, spread_m: 6, reach_m: 30 });
/** T-3505: one's own job between gatherings: out_m from the ring, its two more spots off_m about it. */
export const OWN = Object.freeze({ out_m: [1.8, 3.4], off_m: [1.2, 2.6], spots: 2, tries: 6 });
/** T-3505: a child's play between gatherings: three places this far about where they stood. */
export const PLAY = Object.freeze({ off_m: [2.5, 6], spots: 2 });
/** T-3524: a passage (a door drawn people open, up its stair): it starts to open this far ahead
 *  of them; they wait at it at most open_wait_s; it shuts once they are shut_past_m beyond it;
 *  a follower starts up follow_s after the last one; one waits for a way in use at most busy_s;
 *  a passage taking longer than stuck_s is let go. */
export const PASSAGE = Object.freeze({ open_ahead_m: 2.2, open_wait_s: 5, shut_past_m: 1.3, follow_s: 3, busy_s: 25, stuck_s: 60 });
/** T-3505: a break indoors: a door this near; a beat of every_s, the break for_s, in p of beats. */
export const BREAK = Object.freeze({ reach_m: 45, every_s: [150, 330], for_s: [28, 75], p: 0.55 });
/**
 * T-3573: someone at home asked for by Find or Follow steps out on a walk (`outing`): for_s
 * seconds of it, for_s more each time it runs out while the visitor is following them
 * (followed_s); their own day's walk is taken when it is at least own_min_m long.
 */
export const OUTING = Object.freeze({ for_s: 420, followed_s: 45, own_min_m: 40 });
/**
 * T-3520: children (the owner, 2026-11-08, of the 1812 fort yard: "the kids should not be all
 * over the place", "occasionally there are kids together playing" but not "such a centerpiece";
 * "when so many kids and no parents they should leave and come out of the door"). A child goes
 * in for a door within reach_m (a household's own house is further off than a man's workplace);
 * spends p of its beats of every_s indoors for for_s; when out on its own plays by its own door,
 * door_m out from the step, rather than about the parade; and a gathering of children only
 * comes together on a slower beat (play_every_s) and for a while (play_for_s).
 */
export const CHILD = Object.freeze({ reach_m: 150, every_s: [130, 260], for_s: [100, 220], p: 0.9,
  play_every_s: [320, 640], play_for_s: [35, 80], door_m: [1.4, 3.6] });
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
 * T-3572: points ({e, n}) by square cell of side `size`: returns `near(p)`, the indices of every
 * point in p's cell and the eight about it, ascending — every point within `size` of p, and some
 * further, in the order the points were given.
 */
function cellIndex(points, size) {
  const cells = new Map();
  points.forEach((q, i) => {
    const key = `${Math.floor(q.e / size)},${Math.floor(q.n / size)}`;
    let list = cells.get(key);
    if (!list) cells.set(key, (list = []));
    list.push(i);
  });
  return (p) => {
    const ce = Math.floor(p.e / size), cn = Math.floor(p.n / size), out = [];
    for (let de = -1; de <= 1; de++) for (let dn = -1; dn <= 1; dn++) {
      const list = cells.get(`${ce + de},${cn + dn}`);
      if (list) for (const i of list) out.push(i);
    }
    return out.sort((x, y) => x - y);
  };
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
    for (const span of day.spans ?? []) if (!span.indoors && span.at && !span.duty) outs.push({ key, span });
  }
  const play = (span) => { if (!out.has(span)) out.set(span, { ...span, at: { ...span.at } }); return out.get(span); };
  // Lone or in company: everyone standing (not at a post) is grouped with whoever else stands
  // within GROUP_M at an overlapping hour (single linkage).
  const standing = outs.filter((x) => (x.span.activity ?? 'stand') === 'stand' && !x.span.duty && !POST_RE.test(x.span.doing ?? ''));
  // T-3572: each is asked only of those in its own GROUP_M cell and the eight about it (in
  // the order of `standing`, as the whole list was asked before): 1812's town is some 1,100
  // spans, and asking every pair cost a quarter of a second each time the town was re-planned.
  const nearStanding = cellIndex(standing.map((x) => atOf(x.span)), GROUP_M);
  const seen = new Set();
  for (const first of standing) {
    if (seen.has(first)) continue;
    const group = [first];
    seen.add(first);
    for (let i = 0; i < group.length; i++) {
      const a = atOf(group[i].span);
      for (const k of nearStanding(a)) {
        const o = standing[k];
        if (seen.has(o) || o.key === group[i].key) continue;
        const c = atOf(o.span);
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
  // T-3572: the places by SHARE_M cell, so each is asked only of its neighbours (in the order
  // of `works` and of each one's places, as before). A place is moved only once it is taken,
  // and a taken one is never asked again, so the cells hold for the whole pass.
  const placeOf = [];
  works.forEach((w, j) => w.pts.forEach((q, b) => placeOf.push([j, b, pt(q)])));
  const nearPlace = cellIndex(placeOf.map((x) => x[2]), SHARE_M);
  for (let i = 0; i < works.length; i++) {
    for (let a = 0; a < works[i].pts.length; a++) {
      const tag = `${i}:${a}`;
      if (taken.has(tag)) continue;
      const here = pt(works[i].pts[a]);
      const group = [{ w: i, k: a }];
      for (const m of nearPlace(here)) {
        const [j, b] = placeOf[m];
        if (j === i || works[j].x.key === works[i].x.key || !overlaps(works[i].s, works[j].s)) continue;
        if (taken.has(`${j}:${b}`) || dist(pt(works[j].pts[b]), here) >= SHARE_M) continue;
        if (group.some((g) => g.w === j)) continue;
        group.push({ w: j, k: b });
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
  const centres = new Map(), hosts = new Map(), hostAt = new Map();
  const middle = (ats) => ({ e: ats.reduce((t, p) => t + p.e, 0) / ats.length, n: ats.reduce((t, p) => t + p.n, 0) / ats.length });
  for (const [knot, members] of knots) {
    if (members.size < 2) continue;
    const ats = [...members.values()].map((spans) => atOf(out.get(spans[0]) ?? spans[0]));
    let far = 0;
    for (let i = 0; i < ats.length; i++) for (let j = i + 1; j < ats.length; j++) far = Math.max(far, dist(ats[i], ats[j]));
    if (far <= GATHER.spread_m) { centres.set(knot, middle(ats)); continue; }
    // T-3516: standing far apart (the Glessner court's cook, maid and stable helper), they come
    // together about the one of them nearest their middle, each to a place of a ring about that
    // one's own; those further than reach_m from it keep to their jobs.
    const keys = [...members.keys()].sort();
    const written = keys.map((k) => atOf(members.get(k)[0]));
    const mid = middle(written);
    let h = 0;
    written.forEach((q, i) => { if (dist(q, mid) < dist(written[h], mid)) h = i; });
    const host = written[h];
    const near = keys.filter((_, i) => dist(written[i], host) <= GATHER.reach_m);
    if (near.length < 2) continue;
    // Turned (seeded) so that none of its places is another's talk place at the same time.
    const others = [];
    for (const x of outs) {
      const q = out.get(x.span) ?? x.span;
      if (q.activity === 'talk' && q.knot !== knot) others.push({ key: x.key, span: x.span, at: atOf(q) });
    }
    for (const [hk, sp] of hostAt) if (hk !== knot) others.push(...sp);
    const clashes = (k, q) => others.some((o) => o.key !== k && dist(o.at, q) < 0.65 && overlaps(o.span, members.get(k)[0]));
    let best = null;
    for (let turn = 0; turn < 8; turn++) {
      const ring = ringAbout(host, near, turn ? `${knot}:${turn}` : knot);
      const spots = new Map();
      near.forEach((k, i) => { if (clear(host, ring[i])) spots.set(k, ring[i]); });
      const clash = [...spots].filter(([k, q]) => clashes(k, q)).length;
      if (!best || clash < best.clash) best = { spots, clash };
      if (!clash) break;
    }
    // Whoever's place is still another's keeps to their job.
    for (const [k, q] of [...best.spots]) if (clashes(k, q)) best.spots.delete(k);
    if (best.spots.size >= 2) {
      hosts.set(knot, best.spots);
      hostAt.set(knot, [...best.spots].map(([k, q]) => ({ key: k, span: members.get(k)[0], at: q })));
    }
  }
  const children = new Set(people.filter((q) => q.child).map((q) => q.key));
  for (const x of outs) {
    const s = out.get(x.span) ?? x.span;
    if (s.activity !== 'talk') continue;
    const rand = seededRandom(`own:${x.key}:${x.span.from}`);
    const at = atOf(s), face0 = Number.isFinite(s.at.heading_deg) ? s.at.heading_deg : rand() * 360;
    const spots = hosts.get(s.knot);
    if (!s.knot || (knots.get(s.knot)?.size ?? 0) < 2 || (!centres.has(s.knot) && !spots?.has(x.key))) {
      const job = jobAbout(at, face0, rand, clear);
      const p = play(x.span);
      p.activity = 'work'; p.spots = job.spots.map((q) => local(q)); delete p.knot;
      continue;
    }
    if (spots) {
      // T-3516: a job about their own place; to the gathering, a place in the ring about the host.
      const own0 = atOf(x.span), child = children.has(x.key);
      const job = jobAbout(own0, face0, rand, clear, { off: child ? PLAY.off_m : POTTER.off_m, n: child ? PLAY.spots : POTTER.spots });
      const own = { from: s.from, to: s.to, indoors: false, doing: s.doing, at: local(job.anchor, job.face) };
      if (child && job.spots.length) Object.assign(own, { activity: 'walk', to_point: local(job.spots.at(-1)) });
      else Object.assign(own, { activity: 'work', spots: job.spots.map((q) => local(q)) });
      const p = play(x.span), r = spots.get(x.key);
      p.at = local(r, r.heading_deg);
      p.round = { knot: s.knot, own };
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

/** Keep ordinary clear chores cheap; warm the route grid only for an obstructed trip. */
export function createDayRouter({ router, clear, buildWhenBlocked = false }) {
  return {
    plan(from, to, options) {
      const current = router();
      if (!current || (!current.built && !(buildWhenBlocked && !clear(from, to)))) return null;
      return current.plan(from, to, options);
    },
  };
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
 * @param {object} [o.hostRouter]               real planner for visible jaunt takeovers/returns
 * @param {string[]} [o.problems]
 * @param {(a: {e:number, n:number}, b: {e:number, n:number}) => boolean} [o.clear]  T-3505: whether a
 *                                              job's way from a to b is clear (clearWayOf)
 * @param {(actor: object) => boolean} [o.followed]  T-3573: whether the visitor is following this
 *                                              figure now (an outing lasts while they are)
 */
export function createHumanDays({ humans, three = null, hour = () => null, date = () => null, doors = null,
  interactions = null, visitor = () => null, eye = () => null, router = null, hostRouter = null, problems = [],
  inside = null, spawn = null, despawn = null, openCard = () => {}, openResident = () => {}, clear = () => true, held = () => false, passages = null, followed = () => false } = {}) {
  const Vec = three?.Vector3;
  let people = [];
  const workSourcePeople = new Map();
  let seen = -1;
  let clock = 0;
  const talks = new Map();
  const socials = new Set();
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
  /** Lazy household residents, materialized for a nearby outing or a door call. */
  const insideOnly = (inside?.people ?? []).filter((x) => x?.person && x.home);
  const householdCare = (inside?.care ?? []).filter(x => x?.person && x.home && x.care_only);
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

  const requestedRoute = (p) => !!(p.safeHostTravel || (p.actor.instance?.scene === '1812'
    && (p.visitorReturn || p.called?.visitorRequested || p.social?.visitorRequested || p.override?.visitorRequested)));
  /** Walk `actor` to `to` (or put them there, far off), facing `heading`; then `done`. */
  function go(p, to, heading, done, { from = null, speed = null, direct = false } = {}) {
    const a = p.actor;
    const start = from ?? { e: a.e, n: a.n };
    const requested = requestedRoute(p);
    const safe = requested || (!!p.safeRoutineTravel && (near(start.e, start.n) || near(to.e, to.n)));
    // A routine leaving a door is still hidden until the actor's next render update.
    // That lag must not authorize a jump across the street. Jaunt cuts keep their own rule.
    const hidden = p.cutHandoff || (!p.safeRoutineTravel && a.root?.visible === false);
    p.cutHandoff = false; // the cut grants one handoff only, never a later return
    if (safe && dist(start, to) >= 0.05 && !hidden) {
      let route;
      // Automatic routines must respect the day router's cold-grid policy.
      // The full planner is for actual visitor/jaunt journeys, not every nearby
      // blocked chore. An unavailable routine route waits and retries safely.
      try { route = (direct || (!p.safeHostTravel && (p.safeRoutineTravel || requested))) && clear(start, to)
        ? { points: [[start.e, start.n], [to.e, to.n]] }
        : (requested || a.instance?.scene !== '1812' ? (hostRouter ?? router) : router)?.plan?.(start, to, { mode: 'walk' }); } catch { /* retry below */ }
      const pts = Array.isArray(route?.points) && route.points.every((q) => Array.isArray(q) && q.length === 2 && q.every(Number.isFinite)) ? route.points : null;
      if (!pts?.length || Math.hypot(pts.at(-1)[0] - to.e, pts.at(-1)[1] - to.n) > 0.05 || typeof a.walkPath !== 'function') {
        a.path = null; a.setState?.('standing');
        p.pendingHostMove = { to, heading, done, from, speed, direct, token: p.token, retry: clock + 0.5 };
        return; // no chord, visible teleport, or false arrival when the planner is unavailable
      }
      p.pendingHostMove = null;
      const token = (p.token = (p.token ?? 0) + 1);
      const points = [{ e: start.e, n: start.n }, ...pts.map(([e, n]) => ({ e, n })), { e: to.e, n: to.n }]
        .filter((q, i, all) => !i || dist(q, all[i - 1]) > 0.05);
      const ok = a.walkPath(points, { speed, endHeading: Number.isFinite(heading) ? heading : null,
        onArrive: () => { if (p.token === token) done?.(); } });
      if (!ok) p.pendingHostMove = { to, heading, done, from, speed, direct, token, retry: clock + 0.5 };
      return;
    }
    if ((safe && hidden) || (!safe && !near(start.e, start.n) && !near(to.e, to.n)) || typeof a.walkPath !== 'function' || dist(start, to) < 0.05) {
      a.path = null;
      a.e = to.e; a.n = to.n;
      if (Number.isFinite(heading)) a.heading = heading;
      a.standY = null;
      a.place?.();
      done?.();
      return;
    }
    const token = (p.token = (p.token ?? 0) + 1);
    const ok = a.walkPath(direct && clear(start, to) ? [start, to] : way(start, to), { speed, endHeading: Number.isFinite(heading) ? heading : null,
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

  // ── T-3524: passages ──────────────────────────────────────────────────────────────
  /** The passage a door is (house-doors.js), or null for a door that is only stood at. */
  const passageOf = (door) => (door?.id ? passages?.passage?.(door.id) ?? null : null);
  /** Who is on each passage's way now: id -> [{ p, dir, at }]. */
  const onWays = new Map();
  /** Things waited on: [{ p, token, until, then, deadline }], looked at once a frame. */
  let waits = [];
  function waitFor(p, until, then, seconds) {
    if (until()) { then(); return; }
    waits.push({ p, token: p.token, until, then, deadline: clock + seconds });
  }
  function stepWaits() {
    if (!waits.length) return;
    const now = waits;
    waits = [];
    for (const w of now) {
      if (w.p.token !== w.token || w.p.actor.disposed) continue;
      if (w.until() || clock >= w.deadline) w.then();
      else waits.push(w);
    }
  }
  /** Whether `dir` ('in' | 'out') may start on the way now: nobody the other way, the last one
   *  going this way far enough ahead. */
  function wayFree(pass, dir) {
    const on = onWays.get(pass.id) ?? [];
    return on.every((u) => u.dir === dir && clock - u.at >= PASSAGE.follow_s);
  }
  function onWay(p, pass, dir) {
    const on = onWays.get(pass.id) ?? [];
    on.push({ p, dir, at: clock });
    onWays.set(pass.id, on);
    p.passing = { door: pass, since: clock };
  }
  /** Off the way and no longer holding its door (done, or let go). */
  function offWay(p) {
    if (!p.passing) return;
    const pass = p.passing.door;
    pass.release(p);
    const on = (onWays.get(pass.id) ?? []).filter((u) => u.p !== p);
    if (on.length) onWays.set(pass.id, on); else onWays.delete(pass.id);
    p.passing = null;
  }
  /** The way through, outside to in, with the ground filled in where it is open ground. */
  function wayOf(p, pass) {
    const raw = pass.way();
    const a = p.actor;
    const out = raw.map((q) => ({ e: q.e, n: q.n, y: Number.isFinite(q.y) ? q.y : (a.heightAt?.(q.e, q.n) ?? null) }));
    out.door = raw.door;
    out.leaf = raw.leaf;
    return out;
  }
  /** Walk `p` in by `door` and call `inside()` once they are in. */
  function enterBy(p, door, inside) {
    const a = p.actor;
    const pass = passageOf(door);
    if (!pass) {
      const step = pt(door.step), leaf = pt(door.leaf);
      go(p, step, (door.outward_deg + 180) % 360, () => {
        const t = ++p.token;
        if (!a.walkPath?.([step, leaf], { onArrive: () => { if (p.token === t) inside(); } })) inside();
      });
      return;
    }
    const w = wayOf(p, pass);
    const k = w.door;
    go(p, w[0], bearing(w[1].e - w[0].e, w[1].n - w[0].n), () => {
      waitFor(p, () => wayFree(pass, 'in'), () => {
        onWay(p, pass, 'in');
        const t = ++p.token;
        const done = () => { offWay(p); inside(); };
        const atDoor = () => {
          if (p.token !== t) return;
          pass.hold(p);
          waitFor(p, () => pass.isOpen(), () => {
            const t2 = ++p.token;
            if (!a.walkPath(w.slice(k), { onArrive: () => { if (p.token === t2) done(); } })) done();
          }, PASSAGE.open_wait_s);
        };
        if (!a.walkPath?.(w.slice(0, k + 1), { onArrive: atDoor })) { done(); return; }
        // The door starts to open as they come up to it.
        waitFor(p, () => dist(a, w[k]) < PASSAGE.open_ahead_m, () => pass.hold(p), PASSAGE.stuck_s);
      }, PASSAGE.busy_s);
    });
  }
  /** Bring `p` (indoors) out by `door` and call `out(from)` where they stand outside. */
  function exitBy(p, door, out) {
    const a = p.actor;
    const pass = passageOf(door);
    const step = pt(door.step);
    if (!pass || !near(step.e, step.n)) {
      a.e = step.e; a.n = step.n; a.standY = null; a.heading = door.outward_deg;
      a.setIndoors?.(false);
      a.place?.();
      out(step);
      return;
    }
    const w = wayOf(p, pass);
    const back = [...w].reverse();
    waitFor(p, () => wayFree(pass, 'out'), () => {
      onWay(p, pass, 'out');
      a.path = null;
      a.e = back[0].e; a.n = back[0].n; a.standY = back[0].y;
      a.heading = bearing(back[1].e - back[0].e, back[1].n - back[0].n);
      a.setIndoors?.(false);
      a.place?.();
      pass.hold(p);
      ++p.token;
      waitFor(p, () => pass.isOpen(), () => {
        const t2 = ++p.token;
        const done = () => { offWay(p); out(back.at(-1)); };
        if (!a.walkPath?.(back, { onArrive: () => { if (p.token === t2) done(); } })) { done(); return; }
        // Once they are clear of its swing, it shuts behind them.
        waitFor(p, () => dist(a, w.leaf) > PASSAGE.shut_past_m || !a.path, () => pass.release(p), PASSAGE.stuck_s);
      }, PASSAGE.open_wait_s);
    }, PASSAGE.busy_s);
  }

  function collect() {
    const actors = humans.actors, active = new Set(actors);
    const previous = new Map(people.map(p => [p.actor, p]));
    // Vehicles and other visitors can change the roster during a household's
    // activity. Keep each existing resident's paths, calls and shared session.
    for (const session of [...socials]) {
      if (session.members.some(p => !active.has(p.actor) || p.b !== p.actor.instance?.behaviour)) endSocial(session);
    }
    people = []; workSourcePeople.clear();
    for (const actor of actors) {
      if (spawned.some((q) => q.actor === actor)) continue;
      const b = actor.instance?.behaviour;
      if (!b || (!Array.isArray(b.day) && !b.presence && !b.quarters)) continue;
      const prior = previous.get(actor);
      if (prior?.b === b) { people.push(prior); continue; }
      people.push({
        actor, b, id: actor.id, rand: seededRandom(`day:${actor.id}`), span: null, inside: null,
        mode: actor.indoors ? 'in' : 'out', absent: false, called: null, job: null,
        soldier: Array.isArray(b.hours) && !Array.isArray(b.day),
        child: CHILD_RE.test(actor.instance?.appearance?.asset_id ?? ''),
      });
    }
    people.push(...spawned);
    for (const p of people) registerPerson(p);
    seen = humans.actors.length;
    // Lazy residents have local work places and explicit companion sessions.
    // Adding/removing one need not re-plan the whole town's gatherings.
    if (people.some(p => !p.entry && previous.get(p.actor) !== p)
      || [...previous.values()].some(p => !p.entry && !active.has(p.actor))) {
      plan = { date: undefined, map: new Map() };
    }
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
    return [...insideOnly, ...householdCare].filter((x) => x.home === structure && onDate(today, x.presence)
      && (humans.crowdKept == null || humans.crowdKept.includes(x.person))
      && !spanAt(dayOn(x, today, x.person), hour())?.away
      && !spawned.some((q) => q.entry === x) && doorOf(x, here) === doorId);
  }
  /** An inside-only person's figure, built at the door they were asked for at. */
  function summon(entry, door) {
    if (entry.care_only) return null; // infants never acquire an independent walking actor
    let actor = null;
    try { actor = spawn?.(entry, door) ?? null; } catch (err) { problems.push(`human-days: ${entry.person} could not be built: ${err?.message ?? err}`); }
    if (!actor) return null;
    const p = { actor, b: { presence: entry.presence, ask_order: entry.ask_order, day: entry.day }, id: actor.id ?? `inside:${entry.person}`,
      rand: seededRandom(`day:${entry.person}`), span: null, inside: door.structure, mode: 'in', absent: false,
      called: null, job: null, soldier: false, entry,
      child: CHILD_RE.test(entry.asset_id ?? '') };
    actor.instance.behaviour = p.b;
    actor.personId ??= entry.person;
    actor.setIndoors?.(true);
    spawned.push(p);
    people.push(p);
    registerPerson(p);
    return p;
  }
  /** Back in: the figure goes. */
  function retire(p) {
    offWay(p);
    const k = spawned.indexOf(p);
    if (k >= 0) spawned.splice(k, 1);
    const i = people.indexOf(p);
    if (i >= 0) people.splice(i, 1);
    interactions?.remove?.(`person:${p.id}`);
    // Let HumanActor.dispose release its body, cached rigs and scene root first.
    // Marking it disposed before remove() makes that cleanup an early return.
    try { despawn?.(p.actor); p.actor.dispose?.(); } catch (err) { problems.push(`human-days: ${p.entry.person} could not be taken away: ${err?.message ?? err}`); }
    p.actor.disposed = true;
  }

  const homeDoor = (p, structure, e, n) => (p.entry?.door && doorsOf(structure).find(d => d.id === p.entry.door)) || doorNear(structure, e, n);

  function goIn(p, structure, doorId = null) {
    const a = p.actor;
    const previous = p.inside;
    p.inside = structure;
    if (a.instance?.scene === '1812') p.safeRoutineTravel = true;
    if (p.entry) rested.set(p.entry.person, { date: date(), span: spanAt(dayOn(p.b, date(), keyOf(p)), hour()) });
    if (a.indoors && (!previous || previous === structure)) { p.mode = 'in'; p.visitorReturn = false; if (!p.hosted) p.safeHostTravel = false; return; }
    const door = doorsOf(structure).find(d => d.id === doorId) ?? homeDoor(p, structure, a.e, a.n);
    if (!door || (!requestedRoute(p) && !near(a.e, a.n))) { a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.visitorReturn = false; if (!p.hosted) p.safeHostTravel = false; return; }
    const inward = () => {
      p.mode = 'going_in';
      enterBy(p, door, () => { a.setIndoors?.(true); p.mode = 'in'; p.visitorReturn = false; if (!p.hosted) p.safeHostTravel = false; });
    };
    if (a.indoors && previous !== structure) {
      const out = homeDoor(p, previous, a.e, a.n);
      if (out) { p.mode = 'going_out'; exitBy(p, out, inward); return; }
    }
    p.mode = 'going_in';
    inward();
  }

  function comeOut(p, span) {
    const a = p.actor;
    const to = pt(span.at);
    const onward = (from) => {
      p.inside = null;
      p.mode = 'going_out';
      go(p, to, span.at.heading_deg, () => { p.mode = 'out'; startActivity(p, span); }, { from });
    };
    if (a.indoors) {
      const door = p.inside ? homeDoor(p, p.inside, to.e, to.n) : null;
      if (door) { p.mode = 'going_out'; exitBy(p, door, onward); return; }
      a.e = to.e; a.n = to.n; a.standY = null;
      a.heading = span.at.heading_deg ?? a.heading;
      a.setIndoors?.(false);
      a.place?.();
      onward(to);
      return;
    }
    onward(null);
  }

  function startActivity(p, span) {
    const a = p.actor;
    const act = span.activity ?? 'stand';
    if (!p.hosted) p.safeHostTravel = false; // returned to the everyday post
    p.visitorReturn = false;
    p.safeRoutineTravel = false;
    p.job = null;
    // Talking starts only once a real partner has arrived.
    a.setState?.(act === 'work' ? 'working' : 'standing');
    if (span.duty) {
      if (!p.b.duty) a.setState?.(p.b.state ?? 'standing');
      return;
    }
    if (act === 'work') {
      const nearby = !span.spots
        ? jobAbout(pt(span.at), span.at.heading_deg ?? 0, p.rand, clear).spots : [];
      const spots = [pt(span.at), ...(span.spots ? span.spots.map(pt) : nearby)];
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
    if ((p.actor.instance?.scene === '1904' || p.entry) && (written.activity === 'talk' || (p.entry?.supervised && !written.indoors && !written.away)) && !p.social) {
      if (startSocial(p, written).ok) return;
      // No available companion: return to household duties rather than wait alone.
      restAfterTalk(p);
      return;
    }
    const a = p.actor;
    p.span = written;
    const span = p.play = playOf(written);
    p.job = null;
    p.token = (p.token ?? 0) + 1;
    p.round = null; p.phase = null; p.cur = null;
    if (span.away) { talk(a, false); a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.inside = null; p.visitorReturn = false; return; }
    if (span.indoors) { talk(a, false); goIn(p, span.where, span.door); return; }
    // T-3505: a talk or a job is played as a round: gatherings, one's own job, breaks indoors.
    const act = span.activity ?? 'stand';
    if (!span.duty && (span.round || act === 'work')) {
      p.round = { knot: span.round?.knot ?? null, talk: span, own: span.round?.own ?? span, home: homeOf(p, span) };
      // T-3520: a child out on its own plays by its own door, not about the yard.
      if (p.child && p.round.home) p.round.own = byTheDoor(p, p.round.home, span) ?? p.round.own;
      phaseTo(p, want(p));
      return;
    }
    comeOut(p, span);
  }

  // ── T-3505: rounds ──────────────────────────────────────────────────────────────────
  const keyOf = (p) => p.actor.personId ?? p.id;
  const home = (p) => (dayOn(p.b, date(), keyOf(p))?.spans ?? []).find((s) => s.indoors && !s.away && s.where)?.where ?? p.b.shelter;
  const unavailable = (p) => p.absent || !onDate(date(), p.b.presence) || p.actor.disposed || p.hosted || held(p.actor) || humans.isHeld?.(p.actor);

  function restAfterTalk(p, visitorRequested = false) {
    const original = spanAt(dayOn(p.b, date(), keyOf(p)), hour());
    const where = home(p);
    if (!where) return;
    const span = { indoors: true, where, doing: 'back to household duties' };
    p.override = { span, original, date: date(), until: null, visitorRequested };
    enter(p, span);
  }

  /** A shared break owns both paths until both arrive, chat, and resume their days. */
  function startSocial(p, span, visitorRequested = false) {
    const where = home(p);
    const supervised = !!p.entry?.supervised;
    const compatible = q => (!supervised || p.entry.caregivers?.includes(keyOf(q)))
      && (!q.entry?.supervised || q.entry.caregivers?.includes(keyOf(p)));
    const currentOf = q => spanAt(dayOn(q.b, date(), keyOf(q)), hour());
    const anchor = p.actor.indoors ? pt(span.at) : { e: p.actor.e, n: p.actor.n };
    // A shared household/camp is not permission to recruit someone across town.
    // Indoors, read the real exit rather than the actor's last outdoor position.
    const exitOf = q => homeDoor(q, q.inside ?? home(q), anchor.e, anchor.n);
    const distanceOf = q => q.actor.indoors
      ? (exitOf(q) ? dist(pt(exitOf(q).step), anchor) : Infinity) : dist(q.actor, anchor);
    const candidates = people.filter((q) => q !== p && where && compatible(q)
      && (q.actor.indoors ? ((q.inside ?? home(q)) === where
        || (q.actor.instance?.scene === '1812' && distanceOf(q) < 30)) : distanceOf(q) < 18)
      && !unavailable(q) && !q.attending && !q.social && !q.called && !q.passing && !q.override
      && !currentOf(q)?.away
      && !(currentOf(q)?.duty && (q.b.duty?.kind === 'beat' || POST_RE.test(currentOf(q)?.doing ?? ''))));
    candidates.sort((a, b) => Number(a.actor.indoors) - Number(b.actor.indoors)
      || (supervised ? p.entry.caregivers.indexOf(keyOf(a)) - p.entry.caregivers.indexOf(keyOf(b)) : 0)
      || distanceOf(a) - distanceOf(b));
    let q = candidates[0];
    if (!q && spawn && (!p.autonomousUntil || spawned.length < 3)) {
      const entry = insideOnly.filter(x => x.person !== keyOf(p) && x.home === where
        && (!supervised || p.entry.caregivers?.includes(x.person))
        && (!x.supervised || x.caregivers?.includes(keyOf(p)))
        && (humans.crowdKept == null || humans.crowdKept.includes(x.person))
        && (!p.entry?.door || x.door === p.entry.door) && onDate(date(), x.presence)
        && !spanAt(dayOn(x, date(), x.person), hour())?.away
        && !spawned.some(m => m.entry === x))
        .sort((a, b) => supervised ? p.entry.caregivers.indexOf(a.person) - p.entry.caregivers.indexOf(b.person) : 0)[0];
      const door = entry && doorThings.find(t => t.door.id === entry.door);
      if (door) q = summon(entry, door.door);
    }
    if (!q) return { ok: false, why: supervised ? 'A household adult is not free just now' : 'Nobody is free to chat just now' };
    const at = q.actor.indoors ? anchor : { e: q.actor.e, n: q.actor.n };
    // Use a clear, nearby standing place; never put the partner through a wall.
    const next = [0, 90, 180, 270].map((h) => ({ e: at.e + Math.sin(h * Math.PI / 180) * 1.4,
      n: at.n + Math.cos(h * Math.PI / 180) * 1.4 })).find((to) => clear(at, to));
    if (!next) return { ok: false, why: 'There is no room to chat here' };
    const session = { members: [p, q], supervised: supervised || !!q.entry?.supervised, outing: supervised && span.activity !== 'talk' ? span : null, date: date(), started: clock, chatting: null, visitorRequested,
      originals: [p, q].map((m) => spanAt(dayOn(m.b, date(), keyOf(m)), hour())) };
    socials.add(session);
    for (const [i, m] of session.members.entries()) {
      if (m.actor.instance?.scene === '1812') m.safeRoutineTravel = true;
      m.social = session; m.called = null; m.override = null; m.job = null; m.round = null;
      m.phase = null; m.cur = null;
      m.token = (m.token ?? 0) + 1;
      m.actor.stopPath?.(); talk(m.actor, false);
      const to = i ? at : next;
      const activity = { ...span, round: undefined, at: local(to), activity: 'talk' };
      m.span = activity; m.play = activity;
      comeOut(m, activity);
    }
    return { ok: true };
  }

  function endSocial(session) {
    socials.delete(session);
    for (const p of session.members) {
      p.social = null; p.span = null; p.play = null;
      p.token = (p.token ?? 0) + 1;
      talk(p.actor, false);
      // A jaunt or another interaction now owns its actor and path.
      if (unavailable(p) || !humans.actors.includes(p.actor)) continue;
      offWay(p); p.actor.stopPath?.(); p.actor.path = null; talk(p.actor, false);
      const current = spanAt(dayOn(p.b, date(), keyOf(p)), hour());
      if (p.actor.instance?.scene === '1812') p.safeRoutineTravel = true;
      if (p.entry || (current?.activity === 'talk' && !current.duty)) restAfterTalk(p, session.visitorRequested);
      else if (current) {
        if (session.visitorRequested) p.visitorReturn = true;
        enter(p, current);
      }
    }
  }

  // Shared short walks use the child's pace and only clear, nearby frontage. A
  // caregiver waits whenever the child's menu/card holds them, and returns with them.
  // Keep these already-clear short legs direct: independent grid snapping sends
  // one partner on a detour and separates them even when their speeds match.
  function stepOuting(s) {
    if (!s.bases) s.bases = s.members.map(m => ({ e: m.actor.e, n: m.actor.n }));
    if (s.moving || clock < (s.nextMove ?? 0) || s.outing.activity === 'greet') return;
    const start = pt(s.outing.at), end = pt(s.outing.to_point ?? s.outing.at);
    const delta = { e: end.e - start.e, n: end.n - start.n };
    const offset = s.leg ? { e: 0, n: 0 } : delta;
    const targets = s.bases.map(b => ({ e: b.e + offset.e, n: b.n + offset.n }));
    if (dist(start, end) < .2 || !targets.every((to, i) => clear(s.members[i].actor, to))) {
      s.nextMove = clock + 4; return;
    }
    s.moving = true; s.arrived = 0;
    for (const [i, m] of s.members.entries()) {
      talk(m.actor, false);
      go(m, targets[i], bearing(targets[i].e - m.actor.e, targets[i].n - m.actor.n), () => {
        if (m.social !== s) return;
        if (++s.arrived === s.members.length) { s.moving = false; s.leg = !s.leg; s.nextMove = clock + 3; }
      }, { speed: .65, direct: true });
    }
  }

  function stepSocials() {
    for (const s of [...socials]) {
      const [p, q] = s.members;
      if (s.date !== date() || s.members.some((m, i) => unavailable(m)
        || spanAt(dayOn(m.b, date(), keyOf(m)), hour()) !== s.originals[i])
        || clock - s.started > (s.outing ? 330 : 150) || (s.chatting !== null && clock - s.chatting >= (s.outing ? (s.visitorRequested ? 150 : 90) : 60))) {
        endSocial(s); continue;
      }
      if (s.members.some(m => m.attending)) { for (const m of s.members) talk(m.actor, false); continue; }
      const together = s.members.every((m) => m.mode === 'out' && !m.actor.indoors && !m.passing)
        && dist(p.actor, q.actor) <= 2.2;
      if (s.outing && s.chatting !== null) { stepOuting(s); continue; }
      if (!together) { for (const m of s.members) talk(m.actor, false); continue; }
      if (s.chatting === null) {
        s.chatting = clock;
        p.actor.turnTo?.(bearing(q.actor.e - p.actor.e, q.actor.n - p.actor.n));
        q.actor.turnTo?.(bearing(p.actor.e - q.actor.e, p.actor.n - q.actor.n));
      }
      if (s.outing) { stepOuting(s); continue; }
      for (const [i, m] of s.members.entries()) {
        const other = s.members[1 - i].actor;
        talk(m.actor, Math.floor((clock - s.chatting) / 4) % 2 === i);
        look(m.actor, other, 1);
      }
    }
  }
  /** The building of today's day whose door is nearest the span's place, within BREAK.reach_m. */
  function homeOf(p, span) {
    const day = dayOn(p.b, date(), keyOf(p));
    const at = pt(span.at);
    let best = null;
    for (const where of new Set((day?.spans ?? []).filter((s) => s.indoors && !s.away && s.where).map((s) => s.where))) {
      const d = doorNear(where, at.e, at.n);
      const k = d ? dist(pt(d.step), at) : Infinity;
      if (k <= (p.child ? CHILD.reach_m : BREAK.reach_m) && (!best || k < best.k)) best = { k, where };
    }
    return best?.where ?? null;
  }
  /** T-3520: a child's play by its own door: out from the step a little way and back. */
  function byTheDoor(p, where, span) {
    const d = homeDoor(p, where, pt(span.at).e, pt(span.at).n);
    if (!d) return null;
    const r = seededRandom(`door-play:${keyOf(p)}:${where}`);
    const s = pt(d.step), out = (Number(d.outward_deg) || 0) + (r() - 0.5) * 70;
    const far = lerp(CHILD.door_m, r()), near0 = Math.min(far - 0.8, 1.1);
    const at = (m, deg) => ({ e: s.e + Math.sin(deg * Math.PI / 180) * m, n: s.n + Math.cos(deg * Math.PI / 180) * m });
    const a = at(near0, out), b = at(far, out + (r() - 0.5) * 60);
    if (!clear(s, a) || !clear(a, b)) return null;
    return { ...span, activity: 'walk', at: local(a, (out + 180) % 360), to_point: local(b), via: [], once: false, round: undefined,
      doing: 'playing by the door' };
  }
  /** The knots' gatherings, worked out once a frame: { on, cycle, joined: Set of people }. */
  const gathers = new Map();
  let frame = 0;
  let byKnot = new Map();
  function gathering(knot) {
    let g = gathers.get(knot);
    const members = byKnot.get(knot) ?? [];
    // (Made again once its people are known: before the first frame it has none.)
    if (!g || (g.kids === null && members.length)) {
      const r = seededRandom(`gather:${knot}`);
      // T-3520: children at play together only now and then.
      const kids = members.length ? members.every((q) => q.child) : null;
      const every = lerp(kids ? CHILD.play_every_s : GATHER.every_s, r());
      g = { every, off: r() * every, cycle: null, on: false, joined: new Set(), order: new Map(), frame: -1, kids };
      gathers.set(knot, g);
    }
    if (g.frame === frame) return g;
    g.frame = frame;
    const t = clock + g.off, c = Math.floor(t / g.every);
    if (c !== g.cycle) { g.cycle = c; g.joined.clear(); g.order.clear(); g.len = lerp(g.kids ? CHILD.play_for_s : GATHER.for_s, seededRandom(`gather:${knot}:${c}`)()); }
    g.on = t - c * g.every < g.len;
    if (!g.on) { g.joined.clear(); return g; }
    const here = (byKnot.get(knot) ?? []).filter((q) => !q.called && !q.absent && !q.hosted && !held(q.actor) && !humans.isHeld?.(q.actor) && q.phase !== 'in');
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
    const B = p.child ? CHILD : BREAK;   // T-3520: a child is in more than out
    if (!p.brk) {
      const r = seededRandom(`break:${keyOf(p)}`);
      const every = lerp(B.every_s, r());
      p.brk = { every, off: r() * every };
    }
    const t = clock + p.brk.off, c = Math.floor(t / p.brk.every);
    const r = seededRandom(`break:${keyOf(p)}:${c}`);
    return r() < B.p && t - c * p.brk.every < lerp(B.for_s, r());
  }
  /** What the round has `p` at now: 'talk', 'in' (a break) or 'own'. */
  function want(p) {
    const r = p.round;
    if (r.knot && gathering(r.knot).joined.has(p)) return 'talk';
    // T-3520: one out of sight goes in on their beat too (else everyone the visitor comes upon
    // is out of doors, the children of a whole yard among them); one far off but in sight keeps
    // to what they are at (stepRound).
    if (!p.override?.until && r.home && breakOn(p) && (p.phase === 'in' || near(p.actor.e, p.actor.n) || !p.actor.root?.visible)) return 'in';
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
      if (p.social || held(p.actor) || humans.isHeld?.(p.actor) || p.mode !== 'out' || p.called || p.hosted || !s || s.activity !== 'talk' || !s.knot) continue;
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
  // The 1904 household remains callable even during an off-scene errand or office period.
  function recallHome(p) {
    if (p.actor.instance?.scene !== '1904' || !p.span?.away) return null;
    return (dayOn(p.b, date(), keyOf(p))?.spans ?? []).find((s) => s.indoors && s.where)?.where ?? null;
  }
  function within(structure) {
    return people.filter((p) => !p.absent && !p.social && !p.called && !p.hosted && !held(p.actor) && !humans.isHeld?.(p.actor) && p.actor.indoors
      && (p.soldier ? p.b.quarters === structure : p.mode === 'in' && (p.inside ?? recallHome(p)) === structure))
      .sort((x, y) => (x.b.ask_order ?? 50) - (y.b.ask_order ?? 50) || nameOf(x).localeCompare(nameOf(y)));
  }
  const nameOf = (p) => p.entry?.name ?? p.actor.person?.name ?? p.actor.identity?.person?.name ?? p.actor.instance?.display_name ?? p.actor.personId ?? p.actor.id;

  function callOut(p, door) {
    if (p.entry?.supervised) {
      p.autonomousUntil = null;
      const span = { indoors: false, at: { ...door.step, heading_deg: door.outward_deg }, activity: 'greet', doing: 'at the door with a household adult' };
      const result = startSocial(p, span, true);
      if (!result.ok) restAfterTalk(p, true);
      return result;
    }
    p.autonomousUntil = null;
    p.override = null;
    p.called = { door, since: clock, off: 0, visitorRequested: true };
    p.job = null;
    p.token = (p.token ?? 0) + 1;
    p.mode = 'called';
    // Out of the door (down its stair, T-3524), then up to the visitor.
    exitBy(p, door, (from) => meet(p, from));
    return { ok: true };
  }
  function meet(p, step) {
    const a = p.actor;
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
    if (p.passing) return;       // on the stair to the door: they finish it first
    const v = visitor();
    const off = !v || Math.hypot(v.e - p.actor.e, v.n - p.actor.n) > STAY_M;
    c.off = off ? c.off + dt : 0;
    if (clock - c.since < STAY_S && c.off < LEAVE_S) return;
    // Let go: back in by the door they came out of, or on to the hour's place.
    p.called = null;
    if (c.visitorRequested) p.visitorReturn = true; // retain the visitor's return leg until arrival
    if (p.soldier || p.entry) {
      const back = c.door;
      p.inside = p.entry ? back.structure : p.b.quarters;
      p.mode = 'going_in';
      const inAgain = () => { p.actor.setIndoors?.(true); p.mode = 'in'; p.visitorReturn = false; if (!p.hosted) p.safeHostTravel = false; if (p.entry) retire(p); };
      enterBy(p, back, inAgain);
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
      if (p.b.shelter) wanted.add(p.b.shelter);
      for (const v of p.b.day ?? []) for (const s of v.spans ?? []) if (s.indoors && s.where) wanted.add(s.where);
    }
    if (spawn) for (const x of [...insideOnly, ...householdCare]) wanted.add(x.home);
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
              const asks = shown.map(({ p, entry, name }) => {
                let answer = `${name} comes to the door`;
                return (p ? {
                id: `ask:${p.actor.personId ?? p.id}`, label: `Ask for ${name}`, said: () => answer,
                refuse: () => (p.social || p.called || !p.actor.indoors || p.hosted || held(p.actor) || humans.isHeld?.(p.actor) ? `${name} is not available` : null),
                steps: [{ label: 'Knocking', seconds: ANSWER_S, run: (t) => { if (t >= 1) { const result = callOut(p, d); if (!result.ok) answer = result.why; } } }],
              } : entry.care_only ? {
                id: `ask:${entry.person}`, label: `Ask after ${name}`, said: () => careStatus(entry.person)?.text ?? '',
                steps: [{ label: 'Knocking', seconds: ANSWER_S, run: t => { if (t >= 1) openResident(entry.person); } }],
              } : {
                id: `ask:${entry.person}`, label: `Ask for ${name}`, said: () => answer,
                refuse: () => (spawned.some((q) => q.entry === entry) ? `${name} is not in` : null),
                steps: [{ label: 'Knocking', seconds: ANSWER_S, run: (t) => { if (t >= 1) { const q = summon(entry, d); const result = q ? callOut(q, d) : { ok: false, why: `${name} could not come out` }; if (!result.ok) answer = result.why; } } }],
              }); });
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

  // T-3540: generic 1812 people use their day engine's doors and ownership.
  // Registration follows the roster, including a lodge resident materialized later.
  function registerPerson(p) {
    if (!interactions || (!p.entry && p.actor.instance?.scene !== '1812') || interactions.get?.(`person:${p.id}`)) return;
    const a = p.actor;
    interactions.add({
      id: `person:${p.id}`, kind: 'person', personId: a.personId, actor: a, name: nameOf(p),
      states: ['out', 'home'], get state() { return a.indoors ? 'home' : 'out'; }, set state(_) {},
      get at() { return a.indoors || unavailable(p) || humans.shown === false ? null : [a.e, a.n]; }, reach: 2.5,
      actions: { get out() { return [
        { id: 'greet', label: 'Greet', icon: '👋', said: '', steps: [{ seconds: 1.4, label: 'Greeting', run(t) {
          if (t === 0) { api.pause(p.id); const v = visitor(); if (v) a.turnTo?.(bearing(v.e - a.e, v.n - a.n)); a.actions?.greet?.(); }
          if (t >= 1) openCard(a);
        } }] },
        ...api.outdoorActivities(p.id).map(activity => ({ id: `activity:${activity.id}`, ...routineOffer(activity), said: '', steps: [],
          refuse() { const r = api.request(p.id, activity.id); return r.ok ? null : r.why; } })),
        { id: 'go_inside', label: 'Go inside', detail: 'Enter the nearest available building', said: '', steps: [],
          refuse() { const r = api.request(p.id, null, { inside: 'nearest' }); return r.ok ? null : r.why; } },
        ...(api.residence(p.id) ? [{ id: 'go_home', label: 'Go home', detail: 'Return to their residence', said: '', steps: [],
          refuse() { const r = api.request(p.id, null, { inside: 'home' }); return r.ok ? null : r.why; } }] : []),
      ]; }, home: [] },
    });
  }

  // Logical days are cheap; only a few additional nearby figures need meshes.
  // After a short outing they return through their own door, then another resident
  // can take a turn. A caller can still ask for any person behind that door.
  const rested = new Map();
  let residentsAt = 0;
  function stepResidents() {
    if (!spawn || clock < residentsAt || humans.shown === false || humans.crowdKept != null || !visitor()) return;
    residentsAt = clock + 5;
    for (const p of spawned) {
      if (p.autonomousUntil && clock >= p.autonomousUntil && !p.called && !p.social && !p.hosted && !p.override && !p.attending) restAfterTalk(p);
    }
    if (spawned.length >= 3) return;
    const v = visitor();
    const candidates = insideOnly.filter(entry => {
      if (entry.supervised && spawned.length > 1) return false; // reserve a place for the caregiver
      if (!entry.day || !onDate(date(), entry.presence) || spawned.some(p => p.entry === entry || p.entry.door === entry.door)) return false;
      const span = spanAt(dayOn(entry, date(), entry.person), hour());
      const last = rested.get(entry.person);
      if (!span || span.indoors || span.away || !span.at || (last?.date === date() && last.span === span)) return false;
      return dist(pt(span.at), v) < 45;
    });
    // Stable per-person staggering, rotating among everyone eligible this hour.
    candidates.sort((a, b) => seededRandom(`resident:${date()}:${a.person}`)() - seededRandom(`resident:${date()}:${b.person}`)());
    for (const entry of candidates) {
      const here = doorThings.filter(t => t.structure === entry.home);
      const door = here.find(t => t.door.id === doorOf(entry, here));
      if (!door) continue;
      const p = summon(entry, door.door);
      if (p) { p.autonomousUntil = clock + 120; enter(p, spanAt(dayOn(p.b, date(), keyOf(p)), hour())); }
      break; // at most one figure built per five seconds
    }
  }

  function careStatus(id) {
    const entry = householdCare.find(x => x.person === id);
    if (!entry || !onDate(date(), entry.presence)) return null;
    const doing = spanAt(dayOn(entry, date(), id), hour())?.doing ?? 'in household care';
    const names = entry.caregivers.map(id => insideOnly.find(x => x.person === id)?.name
      ?? people.find(p => keyOf(p) === id)?.actor.person?.name).filter(Boolean);
    return { person: id, doing, caregivers: entry.caregivers, names, home: entry.home,
      text: `${entry.name} is ${doing}. In this reconstruction, care is shared by adults of the household${names.length ? `, including ${names.slice(0, 2).join(' and ')}` : ''}.` };
  }

  // ── T-3573: someone at home steps out ─────────────────────────────────────────────
  /** Who `id` is (a figure's person or instance id, or an inside-only resident's person id). */
  const byId = (id) => people.find((q) => q.id === id || q.actor.personId === id) ?? null;
  /**
   * Whether `id` is in town and at home now, so that Find and Follow can bring them out:
   * { ok, p?, entry?, structure, name } or { ok: false, why, out? } (`out`: they are out now).
   */
  function atHomeOf(id) {
    if (!id || humans.shown === false) return { ok: false, why: 'People are hidden' };
    const kept = (key) => humans.crowdKept == null || humans.crowdKept.includes(key);
    const p = byId(id);
    if (p) {
      const a = p.actor;
      if (a.disposed || p.absent || !onDate(date(), p.b.presence)) return { ok: false, why: 'not here on this date' };
      if (!a.indoors || p.mode === 'going_out') return { ok: false, why: 'out now', out: true };
      if (p.soldier || p.entry?.supervised) return { ok: false, why: 'Not free to come out' };
      if (p.passing || p.social || p.called || p.hosted || p.attending || held(a) || humans.isHeld?.(a) || !kept(keyOf(p))) return { ok: false, why: 'Not available just now' };
      const now = spanAt(dayOn(p.b, date(), keyOf(p)), hour());
      if (now?.away && !recallHome(p)) return { ok: false, why: 'not here on this date' };
      const structure = p.inside ?? recallHome(p) ?? home(p);
      if (!structure || !doorsOf(structure).length) return { ok: false, why: 'no door known' };
      return { ok: true, p, structure, name: nameOf(p) };
    }
    const entry = spawn ? insideOnly.find((x) => x.person === id) : null;
    if (!entry) return { ok: false, why: 'no such person' };
    if (!onDate(date(), entry.presence) || spanAt(dayOn(entry, date(), entry.person), hour())?.away) return { ok: false, why: 'not here on this date' };
    if (entry.supervised || entry.care_only) return { ok: false, why: 'Not free to come out' };
    if (!kept(entry.person)) return { ok: false, why: 'Not available just now' };
    const here = doorThings.filter((t) => t.structure === entry.home);
    const door = here.find((t) => t.door.id === doorOf(entry, here));
    if (!door) return { ok: false, why: 'no door known' };
    return { ok: true, entry, door, structure: entry.home, name: entry.name ?? entry.person };
  }
  /** Their own day's walk, when it is a real one (OUTING.own_min_m): a walk span, or null. */
  function ownWalkOf(p, entry) {
    const spans = p ? api.outdoorActivities(p.id).map((x) => x.span)
      : (dayOn(entry, date(), entry.person)?.spans ?? []).filter((s) => !s.indoors && !s.away && s.at);
    for (const s of spans) {
      if (s.activity !== 'walk' || !s.to_point) continue;
      const route = [pt(s.at), ...(s.via ?? []).map(pt), pt(s.to_point)];
      let length = 0;
      for (let i = 1; i < route.length; i++) length += dist(route[i], route[i - 1]);
      if (length >= OUTING.own_min_m) return { at: s.at, via: s.via ?? [], to_point: s.to_point, doing: s.doing ?? null };
    }
    return null;
  }
  /** Out on `span` now, for `seconds` (more while followed); { ok, why?, actor? }. */
  function stepOut(id, span, seconds) {
    const found = atHomeOf(id);
    if (!found.ok) return found.out ? { ok: true, already: true, actor: byId(id)?.actor ?? null } : found;
    let p = found.p;
    if (!p) {
      p = summon(found.entry, found.door.door);
      if (!p) return { ok: false, why: `${found.name} could not come out` };
    }
    p.attending = null; p.called = null; p.autonomousUntil = null;
    const original = spanAt(dayOn(p.b, date(), keyOf(p)), hour());
    p.override = { span, original, date: date(), until: clock + seconds, visitorRequested: true, outing: true };
    enter(p, span);
    return { ok: true, actor: p.actor };
  }

  const api = {
    careStatus,
    get people() { return people; },
    get doors() { return doorThings; },
    residence(id) {
      const p = people.find(q => q.id === id || q.actor.personId === id);
      return p && ((dayOn(p.b, date(), keyOf(p))?.spans ?? []).find(s => s.indoors && !s.away && s.where)?.where
        ?? p.entry?.home ?? p.b.quarters) || null;
    },
    nearestEntrance(id) {
      const p = people.find(q => q.id === id || q.actor.personId === id);
      if (!p) return null;
      // Only currently present households: an August camp is not an entrance in winter.
      const present = new Set(people.filter(q => !q.absent && onDate(date(), q.b.presence)).flatMap(q => [home(q), q.inside]));
      for (const entry of insideOnly) if (onDate(date(), entry.presence)) present.add(entry.home);
      const candidates = doorThings.filter(t => present.has(t.structure))
        .sort((a, b) => dist(p.actor, pt(a.door.step)) - dist(p.actor, pt(b.door.step)));
      for (const t of candidates) {
        const end = pt(t.door.step);
        if (clear(p.actor, end)) return t;
        try {
          const route = (hostRouter ?? router)?.plan?.({ e: p.actor.e, n: p.actor.n }, end, { mode: 'walk' });
          if (route?.points?.length && Math.hypot(route.points.at(-1)[0] - end.e, route.points.at(-1)[1] - end.n) < .05) return t;
        } catch { /* try the next real entrance */ }
      }
      return null;
    },
    /** Pause a menu's person without discarding the walk or taking over a jaunt. */
    attend(id) {
      const p = people.find(q => q.id === id || q.actor.personId === id);
      if (!p || unavailable(p) || p.attending || p.passing || p.actor.indoors) return null;
      const pair = p.social?.supervised ? p.social : null;
      if (p.social && !pair) endSocial(p.social);
      const companions = pair?.members.filter(m => m !== p).map(m => ({ m, path: m.actor.path, state: m.actor.state, token: m.token })) ?? [];
      for (const { m } of companions) { m.actor.path = null; m.actor.setState?.('standing'); }
      const a = p.actor;
      const hold = { path: a.path, state: a.state, token: p.token, date: date(),
        span: spanAt(dayOn(p.b, date(), keyOf(p)), hour()) };
      p.attending = hold; a.path = null; a.setState?.('standing'); talk(a, false);
      const v = visitor(); if (v) a.turnTo?.(bearing(v.e - a.e, v.n - a.n));
      return () => {
        if (p.attending !== hold) return;
        p.attending = null;
        for (const { m, path, state, token } of companions) if (m.social === pair && m.token === token) { m.actor.path = path; m.actor.setState?.(state); }
        if (unavailable(p) || p.token !== hold.token) return;
        if (date() !== hold.date || spanAt(dayOn(p.b, date(), keyOf(p)), hour()) !== hold.span) { p.span = null; return; }
        a.path = hold.path; a.setState?.(hold.state);
      };
    },
    canAsk(id) {
      return people.some((p) => (p.id === id || p.actor.personId === id) && !p.absent && (!p.span?.away || recallHome(p)) && p.actor.indoors && !p.social && !p.called && !p.hosted && !held(p.actor) && !humans.isHeld?.(p.actor));
    },
    /**
     * T-3573: whether `id` is in town and at home now (indoors, present, free), so that Find
     * and Follow can bring them out: { structure, name } or null.
     */
    homeNow(id) {
      const found = atHomeOf(id);
      return found.ok ? { structure: found.structure, name: found.name } : null;
    },
    /**
     * T-3573: someone at home is asked for by Find or Follow. Says how they will come out:
     * { ok, structure, name, doing, door: { id, step: {e, n}, outward_deg }, start() } or
     * { ok: false, why }. `loop(structure, door)` gives the walk round their block
     * (block-walk.js: { at, via, to_point, doing }) when their own day has no walk of its own.
     * `start()` (on the visitor's arrival at the door) brings them out of it on that walk for
     * `seconds`, and for OUTING.followed_s more each time it runs out while they are followed:
     * { ok, why?, actor? }.
     */
    outing(id, { loop = null, seconds = OUTING.for_s } = {}) {
      const found = atHomeOf(id);
      if (!found.ok) return found;
      const { p, entry, structure } = found;
      const doorsHere = doorsOf(structure);
      const faceDoor = entry ? found.door.door : (doorsHere.find((d) => !/:back$/.test(d.id)) ?? doorsHere[0]);
      const shape = ownWalkOf(p, entry) ?? loop?.(structure, faceDoor) ?? null;
      if (!shape?.at || !shape.to_point) return { ok: false, why: 'Nowhere to walk from here' };
      const span = { from: 0, to: 24, indoors: false, activity: 'walk', at: shape.at, via: shape.via ?? [],
        to_point: shape.to_point, doing: shape.doing ?? 'a walk', once: false, outing: true };
      const at = pt(span.at);
      const door = entry ? faceDoor : (homeDoor(p, structure, at.e, at.n) ?? faceDoor);
      return { ok: true, structure, name: found.name, doing: span.doing,
        door: { id: door.id, step: pt(door.step), outward_deg: door.outward_deg ?? null },
        start: () => stepOut(id, span, seconds) };
    },
    pause(id) {
      const p = people.find((q) => q.id === id);
      if (!p || p.hosted || p.passing) return;
      if (p.social?.supervised) {
        const s = p.social;
        for (const m of s.members) { m.actor.stopPath?.(); m.actor.path = null; m.token = (m.token ?? 0) + 1; m.actor.setState?.('standing'); talk(m.actor, false); }
        s.outing = { ...p.span, activity: 'greet' }; s.started = clock; s.chatting = clock; s.visitorRequested = true;
        return;
      }
      if (p.social) endSocial(p.social);
      const where = home(p);
      const door = where && homeDoor(p, where, p.actor.e, p.actor.n);
      if (!door) return;
      p.token = (p.token ?? 0) + 1;
      p.actor.stopPath?.(); talk(p.actor, false); p.job = null; p.round = null;
      p.called = { door, since: clock, off: 0, visitorRequested: true };
    },
    outdoorActivities(id) {
      const p = people.find((q) => q.id === id || q.actor.personId === id);
      if (!p) return [];
      if (unavailable(p) || (spanAt(dayOn(p.b, date(), keyOf(p)), hour())?.away && !recallHome(p))) return [];
      const activities = (dayOn(p.b, date(), keyOf(p))?.spans ?? []).filter((s) => !s.indoors && !s.away && s.at)
        .map((s, i) => {
          // A requested duty belongs to the day engine for its five-minute visit,
          // including a sentry's real beat and a field worker's ordinary task.
          const duty = p.b.duty, route = p.b.route;
          const span = s.duty ? { ...s, duty: false,
            activity: duty?.kind === 'beat' || route?.length ? 'walk' : duty?.kind === 'knot' ? 'talk' : p.b.state === 'working' ? 'work' : 'stand',
            ...(duty?.kind === 'beat' ? { to_point: duty.to } : route?.length ? { via: route.slice(0, -1), to_point: route.at(-1) } : {}),
          } : s;
          return { id: i, label: s.doing, span };
        })
        .filter((s, i, all) => all.findIndex((a) => a.label === s.label) === i);
      if ((p.entry || p.actor.instance?.scene === '1812') && !activities.some(a => a.span.activity === 'talk') && activities.length) {
        const span = { ...activities[0].span, activity: 'talk', doing: 'a break with a neighbour' };
        activities.push({ id: 'chat', label: span.doing, span });
      }
      return activities;
    },
    /** A visitor's request lasts five minutes; going inside lasts until the next scheduled span. */
    request(id, activity = null, { inside = null } = {}) {
      const p = people.find((q) => q.id === id || q.actor.personId === id);
      if (!p || unavailable(p) || p.passing || (spanAt(dayOn(p.b, date(), keyOf(p)), hour())?.away && !recallHome(p))) return { ok: false, why: 'Not available just now' };
      p.attending = null;
      const original = spanAt(dayOn(p.b, date(), keyOf(p)), hour());
      const entrance = activity === null && inside === 'nearest' ? api.nearestEntrance(id) : null;
      const where = inside === 'nearest' ? entrance?.structure : inside === 'home' ? api.residence(id) : home(p);
      const span = activity === null ? (where && { from: 0, to: 24, indoors: true, where, door: entrance?.door.id, doing: 'inside at your request' })
        : api.outdoorActivities(id).find((s) => s.id === activity)?.span;
      if (!span) return { ok: false, why: 'No activity available' };
      const carePair = p.social?.supervised ? p.social : null;
      if (carePair && activity !== null && (p.entry?.supervised || ['talk', 'walk'].includes(span.activity))) {
        for (const m of carePair.members) { m.actor.stopPath?.(); m.actor.path = null; m.token = (m.token ?? 0) + 1; talk(m.actor, false); }
        carePair.outing = span.activity === 'talk' ? null : span; carePair.bases = null; carePair.moving = false; carePair.nextMove = 0; carePair.leg = false;
        carePair.started = clock; carePair.chatting = clock; carePair.visitorRequested = true;
        for (const m of carePair.members) { m.span = span; m.play = span; }
        return { ok: true };
      }
      if (p.social) endSocial(p.social);
      if (carePair && activity === null) for (const m of carePair.members.filter(m => m !== p)) {
        m.override = { span, original: spanAt(dayOn(m.b, date(), keyOf(m)), hour()), date: date(), until: null, visitorRequested: true };
        enter(m, span);
      }
      p.autonomousUntil = null;
      if (span.activity === 'talk' || (p.entry?.supervised && !span.indoors)) return startSocial(p, span, true);
      p.called = null;
      if (p.actor.instance?.scene === '1812' || activity === null) p.safeRoutineTravel = true;
      p.override = { span, original, date: date(), until: activity === null ? null : clock + 300, visitorRequested: true };
      enter(p, span);
      return { ok: true };
    },
    /** One frame, after humans.update and the duties. */
    update(dt) {
      if (!humans || !(dt > 0)) return;
      if (humans.actors.length !== seen) { collect(); if (!doorThings.length) makeDoors(); }
      dt = Math.min(dt, 0.25);
      clock += dt;
      stepSocials();
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
        if (a.disposed || humans.isHeld?.(a) || held(a)) continue;
        if (p.entry && !p.b.day) {   // legacy inside-only records without a routine
          if (!onDate(today, p.b.presence)) retire(p);
          else if (p.called) stepCalled(p, dt);
          continue;
        }
        // Off their dates, or on a date their days do not cover (15 August is the battle
        // jaunt's), nowhere.
        const present = onDate(today, p.b.presence) && (!Array.isArray(p.b.day) || !!dayOn(p.b, today, p.actor.personId ?? p.id));
        if (!present) {
          if (p.entry) { retire(p); continue; }
          if (!p.absent) { offWay(p); p.absent = true; p.called = null; p.span = null; p.job = null; a.path = null; a.setIndoors?.(true); p.mode = 'in'; p.inside = null; }
          continue;
        }
        if (p.absent) { p.absent = false; if (p.soldier) a.setIndoors?.(false); }
        if (p.attending && (p.attending.date !== today || spanAt(dayOn(p.b, today, keyOf(p)), h) !== p.attending.span)) {
          p.attending = null; a.path = null; p.span = null;
        }
        if (p.attending) continue;
        if (p.pendingHostMove) {
          const move = p.pendingHostMove;
          if (move.token !== p.token) p.pendingHostMove = null;
          else if (clock >= move.retry) { p.pendingHostMove = null; go(p, move.to, move.heading, move.done, { from: move.from, speed: move.speed, direct: move.direct }); }
        }
        if (!p.hosted && a.instance?.scene === '1812' && spanAt(dayOn(p.b, today, keyOf(p)), h)?.away) {
          p.called = null; p.override = null;
        }
        if (p.hosted || p.social) continue;   // A jaunt or paired conversation owns the path.
        // T-3524: on a passage's stair or in its doorway, they finish it before anything else.
        if (p.passing) { if (clock - p.passing.since > PASSAGE.stuck_s) offWay(p); continue; }
        if (p.called) { stepCalled(p, dt); continue; }
        if (p.entry && a.indoors && p.mode === 'in' && p.inside === p.entry.home) { retire(p); continue; }
        if (p.soldier) continue;   // his hours are human-duties.js's
        let span = spanAt(dayOn(p.b, today, p.actor.personId ?? p.id), h);
        if (p.override) {
          // T-3573: a walk someone stepped out on goes on while the visitor walks with them.
          if (p.override.outing && p.override.date === today && clock >= p.override.until && followed(a)) p.override.until = clock + OUTING.followed_s;
          if (p.override.date !== today || (p.override.until ? clock >= p.override.until : span !== p.override.original)) {
            const visitorRequested = p.override.visitorRequested;
            p.override = null; p.span = null;
            if (visitorRequested) p.visitorReturn = true; // return from the requested activity
            if (p.entry) { restAfterTalk(p, visitorRequested); continue; }
          } else span = p.override.span;
        }
        if (!span) continue;
        if (span !== p.span) enter(p, span);
        else if (p.round) stepRound(p);
        else if (p.mode === 'out') stepJob(p);
      }
      stepWaits();
      stepTalks(dt);
      stepResidents();
    },
    /** Ask for someone at their door now, as the door's Ask for does: { ok, why }. */
    ask(personOrInstance) {
      const care = careStatus(personOrInstance);
      if (care) {
        if (humans.crowdKept != null) return { ok: false, why: 'Not available during this jaunt' };
        openResident(personOrInstance); return { ok: true, householdCare: true, care };
      }
      const p = people.find((x) => x.actor.personId === personOrInstance || x.id === personOrInstance);
      const entry = !p && spawn ? insideOnly.find((x) => x.person === personOrInstance) : null;
      if (entry) {
        if (humans.crowdKept != null && !humans.crowdKept.includes(entry.person)) return { ok: false, why: 'Not available during this jaunt' };
        if (!onDate(date(), entry.presence) || spanAt(dayOn(entry, date(), entry.person), hour())?.away) return { ok: false, why: 'not here on this date' };
        if (spawned.some((q) => q.entry === entry)) return { ok: false, why: 'not indoors' };
        const here = doorThings.filter((t) => t.structure === entry.home);
        const id = doorOf(entry, here);
        const door = here.find((t) => t.door.id === id);
        if (!door) return { ok: false, why: `no door known for ${entry.home}` };
        const q = summon(entry, door.door);
        if (!q) return { ok: false, why: 'could not be built' };
        return { ...callOut(q, door.door), door: door.id };
      }
      if (!p) return { ok: false, why: 'no such person' };
      if (p.absent || (p.span?.away && !recallHome(p))) return { ok: false, why: 'not here on this date' };
      if (p.hosted || held(p.actor) || humans.isHeld?.(p.actor)) return { ok: false, why: 'Not available just now' };
      if (p.social || !p.actor.indoors || p.called) return { ok: false, why: 'not indoors' };
      const structure = p.soldier ? p.b.quarters : (p.inside ?? recallHome(p));
      const door = doorThings.find((t) => t.structure === structure);
      if (!door) return { ok: false, why: `no door known for ${structure}` };
      return { ...callOut(p, door.door), door: door.id };
    },
    /**
     * T-3525: a jaunt's host. Take `personOrInstance` out of their day and walk them to
     * `mark` ({ e, n }), out of the house by its door nearest the mark if they are in, and
     * stand there turned to `heading`; `onArrive` once they stand. { ok, why }. They stay
     * until `unhost`, which gives them back to the hour's place (in by a door, or out to it).
     * `safeTravel` requires real routes whenever visible, including handback; `atCut` is
     * granted only after an actual synchronous camera cut, before its first destination frame.
     */
    host(personOrInstance, mark, { heading = null, onArrive = null, safeTravel = false, atCut = false } = {}) {
      const p = people.find((x) => x.actor.personId === personOrInstance || x.id === personOrInstance);
      if (!p || p.entry) return { ok: false, why: 'no such person' };
      if (p.absent) return { ok: false, why: 'not here on this date' };
      // An errand owns its path and arrival callback until it finishes. The jaunt
      // retries afterwards; taking it now would strand both activities.
      if (held(p.actor)) return { ok: false, why: 'finishing another activity', retryable: true };
      if (p.social) endSocial(p.social);
      if (p.called) p.called = null;
      const a = p.actor, to = { e: mark.e, n: mark.n };
      p.hosted = { mark: to, heading };
      p.attending = null;
      p.safeHostTravel = safeTravel;
      p.visitorReturn = false;
      p.safeRoutineTravel = false;
      p.cutHandoff = atCut && !a.indoors;
      p.pendingHostMove = null;
      p.job = null; p.round = null; p.phase = null; p.cur = null;
      p.token = (p.token ?? 0) + 1;
      talk(a, false);
      offWay(p);                // off any stair they were on (T-3524), and its door let go
      const arrive = () => { if (p.hosted) onArrive?.(a); };
      const structure = a.indoors ? (p.inside ?? p.span?.where ?? null) : null;
      const door = structure ? doorNear(structure, to.e, to.n) : null;
      p.inside = null;
      p.mode = 'hosted';
      a.setState?.('standing');
      if (door) {
        // Out by that door: up or down its stair, the door opening and shutting (T-3524), then on.
        const t = p.token;
        exitBy(p, door, (from) => { if (p.hosted && p.token >= t) go(p, to, heading, arrive, { from }); });
        return { ok: true };
      }
      if (a.indoors) {
        a.e = to.e; a.n = to.n; a.standY = null;
        if (Number.isFinite(heading)) a.heading = heading;
        a.setIndoors?.(false);
        a.place?.();
      }
      go(p, to, heading, arrive);
      return { ok: true };
    },
    /** T-3525: let a jaunt's host go back to their day. */
    unhost(personOrInstance) {
      const p = people.find((x) => x.actor.personId === personOrInstance || x.id === personOrInstance);
      if (!p?.hosted) return false;
      p.hosted = null;
      p.pendingHostMove = null;
      p.token = (p.token ?? 0) + 1;
      offWay(p);
      p.span = null;            // the next frame enters the hour's span from where they stand
      p.mode = p.actor.indoors ? 'in' : 'out';
      return true;
    },
    /** T-3525: whether a jaunt holds this figure as a host. */
    isHosted: (actor) => !!people.find((p) => p.actor === actor)?.hosted,
    /** Whether a person is held out by a call (human-duties.js leaves them be). */
    isCalled: (actor) => !!people.find(p => p.actor === actor)?.called,
    /** Calls, jaunts and scheduled trips temporarily release the duty engine. */
    isOccupied: (actor) => {
      const p = people.find(q => q.actor === actor);
      return !!p && (!!p.called || !!p.hosted || !!p.social || !!p.override || !!p.passing || !!p.attending
        || (Array.isArray(p.b.day) && (!p.span?.duty || p.mode !== 'out')));
    },
    /** Lazy residents and the number of their currently materialized figures. */
    get insideOnly() { return { listed: insideOnly.length, inCare: householdCare.length, out: spawned.length }; },
    /** The live primary work place AFTER shared spots are separated. This is
     * a source for a generated tool action, not permission to sound a generic job. */
    workSource(id) {
      let p = workSourcePeople.get(id);
      if (!p) { p = people.find(q => q.id === id || q.actor.personId === id); if (p) workSourcePeople.set(id, p); }
      const s = (p?.round ? p.cur : null) ?? p?.play ?? p?.span;
      if (!p || p.absent || p.actor.indoors || p.mode !== 'out' || p.called || p.hosted || p.social
        || p.override || p.passing || p.attending || held(p.actor) || humans.isHeld?.(p.actor)
        || s?.activity !== 'work' || p.job?.kind !== 'work' || p.job.moving || p.job.at !== 0
        || p.actor.state !== 'working' || !p.span?.at || !p.job.spots[0]) return null;
      return { actorId: p.id, epoch: p.token ?? 0, active: true,
        originalAt: { e: p.span.at.local_e, n: p.span.at.local_n },
        at: { ...p.job.spots[0] }, heading: p.job.face ?? p.actor.heading,
        from: p.span.from, to: p.span.to, doing: p.span.doing ?? null };
    },
    /** Who is where, for the harness. */
    snapshot() {
      return people.map((p) => ({
        person: p.actor.personId, instance: p.id, absent: p.absent, mode: p.mode, indoors: !!p.actor.indoors,
        inside: p.actor.indoors ? (p.soldier ? p.b.quarters ?? null : p.inside) : null,
        span: p.span ? { from: p.span.from, to: p.span.to, where: p.span.where ?? null,
          activity: p.span.indoors || p.phase === 'in' ? 'indoors' : ((p.round ? p.cur : null) ?? p.play ?? p.span).activity ?? 'stand' } : null,
        phase: p.phase ?? null, home: p.round?.home ?? null,
        called: !!p.called, e: +p.actor.e.toFixed(2), n: +p.actor.n.toFixed(2),
        on_way: p.passing?.door.id ?? null,
      }));
    },
  };
  return api;
}

/** Short 1812 action names, with the full reconstructed description in the detail. */
export function routineOffer(activity) {
  const text = activity.label ?? '';
  const rules = [
    [/sentry|patrol|walking.*post/i, 'Walk the post', '↗'], [/guard|watch|orderly/i, 'Keep watch', '◉'],
    [/rank|fatigue party/i, 'Daily duties', '⚒'], [/smoking/i, 'Take a breather', '◌'],
    [/play|younger child|children/i, 'Play nearby', '↗'],
    [/garden|cornfield|plants/i, 'Tend garden', '❧'],
    [/water/i, 'Fetch water', '◒'], [/wood|fire|kettle/i, 'Tend the hearth', '♨'],
    [/pony|horse|bridle|stable/i, 'Tend horses', '♞'], [/canoe|boat|paddle/i, 'Tend boats', '⚒'],
    [/fish/i, 'Fishing tasks', '⚒'], [/skin|sew|mend|moccasin|equipment|gear/i, 'Mend and repair', '⚒'],
    [/corn|meal|meat|cook|bake/i, 'Prepare food', '♨'],
    [/walk|taking the air|rounds|river|bank/i, 'Take a walk', '↗'],
    [/mat|lodge|house/i, 'Household tasks', '⌂'], [/order|inspect|office/i, 'Daily rounds', '↗'],
  ];
  if (activity.span?.activity === 'talk') return { label: 'Chat together', icon: '💬', detail: text };
  const rule = rules.find(([pattern]) => pattern.test(text));
  return { label: rule?.[1] ?? 'Outdoor tasks', icon: rule?.[2] ?? '⚒', detail: text };
}
