/**
 * house-errands.js — a person who lives in a house, met in the street, can be sent inside:
 * up the steps, through the door, and in (T-3443); and called back out at the door, to
 * walk with the visitor round the house or into its court (T-3444).
 *
 * The owner, 2026-11-07: *"how can we interact with him? I suppose he needs to be somewhere,
 * sitting or standing near the house? we might want to be able to give them interactions
 * like tell them to go home into their house and or be able to call them from the house,
 * maybe interacting at the front door of buildings would allow you to ask for someone to
 * come to the door and then they can come to the door and open it and interact with you,
 * they could open the door and then walk down and around the house or in front of the house
 * or like glessner maybe into the back courtyard"*. So a drawn PERSON whose household has a
 * working front door (house-doors.js, T-3442) is an Interact thing (interact.js) of its own:
 *
 *   out    Greet       he turns to the visitor, looks at them and touches his hat brim
 *                      (human-life.js / human-actions.js), and his own card opens: the
 *                      record's card, never invented words (data/humans/contract.json § L1)
 *          Go home     he walks to his front door (by the town's walks, router.js, when he
 *                      is not already on his own front walk), up the steps, opens it, goes
 *                      in, and it closes behind him (left open if the visitor stands in it)
 *          a stroll    `HOUSE_STROLLS`: he walks the visitor somewhere about the house, the
 *                      visitor walking with him (follow.js) — round by Eighteenth Street to
 *                      the great arch, or through the carriage passage into the court
 *   home   —           indoors: not drawn, not picked, met by no one
 *
 * and his house's DOOR offers, while he is home, Ask for <him>: a knock, a wait, and he
 * opens the door from inside, comes out and down to the visitor (no further than the
 * sidewalk, never past them), touches his brim, and shuts the door behind him. He is out
 * again, with everything above.
 *
 * WHICH DOOR IS WHOSE: `HOUSEHOLD_DOORS`, from the household the person's row names (the
 * people directory's `household`) to the door its house is entered by. The Glessners' is
 * 1800 Prairie Avenue's front door, the one the household's address names (`glessner_house`
 * symbolic_location). Only doors house-doors.js hangs are listed. It is the family's door:
 * a row whose relationship is `servant` (Mattie Williamson, the cook) is not sent through it
 * — the staff came and went by the service entrance off the court, which is not hung yet.
 *
 * T-3533: scheduled household members, including staff, share these interactions. The day
 * engine owns their location and Go inside requests; front-door calls and guided strolls
 * temporarily hold the routine. The activity menu offers the whole seasonal day's outdoor
 * tasks at any hour. Indoor staff can answer a caller at the front door as well as their
 * normal service doors; ordinary routines still use the day engine's doors.
 *
 * Nothing here knows the DOM; tools/test_house_errands.mjs drives it with the real door
 * layer and a real HumanActor.
 */

/** A household, by its id in the people directory, and the door its house is entered by. */
export const HOUSEHOLD_DOORS = Object.freeze({
  hh_glessner_john_j: 'glessner_house:front',
});

/**
 * Where someone who answers a door will walk a visitor, by door: each to a scene anchor
 * (data/scenes/<year>.json `anchors`, the Meet the Glessner House stands, T-3264), turning
 * at the end to the anchor's own view. The router finds the way (the carriage passage into
 * the court is one of its lanes).
 */
export const HOUSE_STROLLS = Object.freeze({
  'glessner_house:front': Object.freeze([
    Object.freeze({ id: 'stroll:court', label: 'Show me the courtyard', anchor: 'glessner_tour_hall_bow' }),
    Object.freeze({ id: 'stroll:arch', label: 'Walk round to the arch', anchor: 'glessner_tour_arch' }),
  ]),
});

/** Who goes in and out by the front door: the household's own, not its staff. */
export const usesFrontDoor = (person) => !!person && person.relationship !== 'servant';

/** How near, on foot, the visitor must stand to a person for the Interact key to offer them. */
export const PERSON_REACH_M = 2.5;
/** Where a figure waits while its door swings: this far out from the leaf's face, on the
 *  threshold, on its top past the riser's ease, his chest clear of the leaf as it turns in. */
export const DOOR_WAIT_M = 0.3;
/** How far past the leaf a figure walks before it is indoors (house-doors.js `inside`). */
export const INDOORS_M = 1.2;
/** The greeting: how long it takes, before the card opens. */
export const GREET_S = 1.4;
/** A knock, and the time it takes someone to come to the door. */
export const ANSWER_S = 2.5;
/** Answering, he stands this far inside the leaf while it swings: out of its sweep (the
 *  leaf is 1.52 m wide on its north jamb), within the 1.9 m vestibule. */
export const ANSWER_FROM_M = 1.6;
/** Coming out to a visitor, he stops this far short of them. */
export const MEET_M = 1.3;

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const dist = (a, b) => Math.hypot(a.e - b.e, a.n - b.n);

/** The point `back` metres short of points[k], walking the path backwards from k. */
function pointShortOf(points, k, back) {
  let left = back;
  for (let i = k; i > 0; i--) {
    const a = points[i], b = points[i - 1];
    const len = Math.hypot(b.e - a.e, b.n - a.n);
    if (len >= left && len > 1e-9) {
      const t = left / len;
      const y = a.y !== null && b.y !== null ? a.y + (b.y - a.y) * t : (a.y ?? b.y);
      return { at: i, point: { e: a.e + (b.e - a.e) * t, n: a.n + (b.n - a.n) * t, y } };
    }
    left -= len;
  }
  return { at: 1, point: { ...points[0] } };
}

/** The path cut at `s` metres along it: [first part ending at s]. */
function cutAt(points, s) {
  const out = [points[0]];
  let run = 0;
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1], b = points[i];
    const len = dist(a, b);
    if (run + len >= s - 1e-9) {
      const t = len > 1e-9 ? (s - run) / len : 1;
      const y = a.y !== null && b.y !== null ? a.y + (b.y - a.y) * t : (t < 0.5 ? a.y : b.y);
      out.push({ e: a.e + (b.e - a.e) * t, n: a.n + (b.n - a.n) * t, y });
      return out;
    }
    run += len;
    out.push(b);
  }
  return out;
}

/** How far along `points` the point nearest (e, n) lies, metres. */
function alongOf(points, p) {
  let best = Infinity, at = 0, run = 0;
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1], b = points[i];
    const len = dist(a, b);
    const t = len > 1e-9 ? Math.max(0, Math.min(1, ((p.e - a.e) * (b.e - a.e) + (p.n - a.n) * (b.n - a.n)) / (len * len))) : 0;
    const d = Math.hypot(a.e + (b.e - a.e) * t - p.e, a.n + (b.n - a.n) * t - p.n);
    if (d < best) { best = d; at = run + t * len; }
    run += len;
  }
  return at;
}

const lengthOf = (points) => points.slice(1).reduce((s, p, i) => s + dist(points[i], p), 0);

/**
 * A person's way home from (e, n): house-doors.js's walk to the door, split where he waits
 * for the door: `{ toDoor, inside, inward, outward }`. On his own front walk (nearer the
 * door than the sidewalk) he walks straight on and the stretch behind him is cut off — a
 * man on his own walk does not go back to the sidewalk first; further off, `router`
 * (route.js) finds the town's way to the sidewalk at the foot of the walk, and the door's
 * own path takes him on from there. Null without a path.
 */
export function wayHome(houseDoors, doorId, from, { groundAt, router = null } = {}) {
  const opts = { inside: INDOORS_M, ...(groundAt ? { groundAt } : {}) };
  const own = houseDoors.path(doorId, opts);
  if (!own || own.length < 3) return null;
  const end = own.at(-1);
  const here = { e: from[0], n: from[1], y: null };
  let kept;
  if (dist(here, end) < dist(own[0], end) - 0.05 || !router) {
    // Keep the start, then only what lies nearer the door than he does.
    kept = [here, ...own.filter((p) => dist(p, end) < dist(here, end) - 0.05)];
  } else {
    const route = router.plan({ e: here.e, n: here.n }, { e: own[0].e, n: own[0].n }, { mode: 'walk' });
    const legs = (route?.points ?? [[here.e, here.n]]).map(([e, n]) => ({ e, n, y: null }));
    kept = [...legs.filter((p, i) => i === 0 || dist(p, legs[i - 1]) > 0.05), ...own];
  }
  // The leaf's face is the last point but one; he waits DOOR_WAIT_M short of it.
  const wait = pointShortOf(kept, kept.length - 2, DOOR_WAIT_M);
  const toDoor = [...kept.slice(0, wait.at), wait.point];
  const inside = [wait.point, ...kept.slice(wait.at)];
  return { toDoor, inside, inward: (own.outward + 180) % 360, outward: own.outward };
}

/**
 * Coming out of the door to a visitor at (e, n): from inside the leaf, out over the
 * threshold and down the walk, stopping MEET_M short of where the visitor stands along it
 * (on the threshold at the least, at the sidewalk at the most). `{ inside, out, outward }`:
 * `inside` is the stretch to the threshold, walked once the door is open.
 */
export function wayOut(houseDoors, doorId, to, { groundAt } = {}) {
  const own = houseDoors.path(doorId, { inside: ANSWER_FROM_M, ...(groundAt ? { groundAt } : {}) });
  if (!own || own.length < 3) return null;
  const path = [...own].reverse();                    // vestibule, leaf, threshold … sidewalk
  const total = lengthOf(path);
  const waitS = dist(path[0], path[1]) + DOOR_WAIT_M;  // the threshold, clear of the leaf
  let stop = waitS;
  if (to) {
    const v = { e: to[0], n: to[1] };
    const along = alongOf(path, v);
    // Past the sidewalk end (out in the street), he comes to the sidewalk and no further.
    const short = along >= total - 1e-6 ? Math.max(0, MEET_M - dist(v, path.at(-1))) : MEET_M;
    stop = Math.max(waitS, Math.min(total, along - short));
  }
  const walk = cutAt(path, stop);
  const atWait = cutAt(path, waitS);
  return { start: path[0], toThreshold: atWait, out: [atWait.at(-1), ...walk.slice(atWait.length - 1)].filter((p, i, a) => i === 0 || dist(p, a[i - 1]) > 1e-4), outward: own.outward };
}

/**
 * @param {object} o
 * @param {{ actors: object[], shown?: boolean }} o.humans   the human layer (humans.js)
 * @param {object} o.houseDoors                     house-doors.js's layer (open, close, get, path)
 * @param {object} o.interactions                   interact.js's engine
 * @param {() => {e:number, n:number} | null} [o.visitor]   where the visitor stands (local ENU)
 * @param {() => object | null} [o.eye]             the camera's world position (a Vector3), for gaze
 * @param {(actor: object) => void} [o.openCard]    open the person's own card
 * @param {(e:number, n:number) => number} [o.groundAt]
 * @param {object} [o.router]                       route.js's planner, for walks off his own front walk
 * @param {(id: string) => ({e:number, n:number, yaw_deg?:number} | null)} [o.anchorAt]  a scene anchor
 * @param {(actor: object, on: boolean) => void} [o.walkWith]  the visitor walks along (follow.js), or stops
 * @param {string[]} [o.problems]
 */
export function createHouseErrands({ days = null, humans, houseDoors, interactions, visitor = () => null, eye = () => null,
  openCard = () => {}, groundAt = null, router = null, anchorAt = () => null, walkWith = () => {}, problems = [] } = {}) {
  const errands = [];
  if (!humans || !houseDoors || !interactions) return { errands, get: () => null, sendHome: () => ({ ok: false }), callOut: () => ({ ok: false }), dispose() {} };
  const ground = groundAt ? { groundAt } : {};

  for (const actor of humans.actors ?? []) {
    const person = actor.person ?? actor.identity?.person ?? null;
    if (actor.identity?.kind !== 'person' || !person) continue;
    const doorId = HOUSEHOLD_DOORS[person.household];
    const scheduled = !!days && Array.isArray(actor.instance?.behaviour?.day);
    if (!doorId || (!scheduled && !usesFrontDoor(person))) continue;
    if (!houseDoors.get(doorId)) { problems.push(`${actor.id}: ${doorId} is not hung in this scene — he cannot be sent home`); continue; }
    const name = person.name ?? actor.id;
    const hosted = () => !!actor.jauntHost || !!days?.isHosted?.(actor);
    const door = () => houseDoors.get(doorId);
    let way = null, arrived = false, refused = false, walking = false;
    const walk = (points, heading) => {
      arrived = false;
      if (!actor.walkPath(points, { endHeading: heading, onArrive: () => { arrived = true; } })) arrived = true;
    };
    const doorOpen = () => { const d = door(); return !d || (d.state === 'open' && !d.running); };
    const doorShut = () => { const d = door(); return refused || !d || (d.state === 'closed' && !d.running); };
    const closeDoor = () => { refused = !houseDoors.close(doorId)?.ok; };
    const greet = () => {
      const v = visitor();
      if (v) actor.turnTo(bearing(v.e - actor.e, v.n - actor.n));
      const p = eye();
      if (p) actor.life?.attend?.(p, 6);
      actor.actions?.greet?.();
    };
    const stopWalking = () => { if (walking) { walking = false; walkWith(actor, false); } };

    const strolls = (HOUSE_STROLLS[doorId] ?? []).map((s) => ({
      id: s.id, label: s.label, to: 'out', said: '',
      refuse: () => (anchorAt(s.anchor) && router ? null : 'No way there from here'),
      steps: [{ label: 'Walking', until: () => arrived, timeout: 240, run: (t) => {
        if (t === 1) { stopWalking(); return; }
        if (t !== 0) return;
        if (scheduled) days.pause(actor.id);
        const a = anchorAt(s.anchor);
        const route = a && router?.plan({ e: actor.e, n: actor.n }, { e: a.e ?? a.local_e, n: a.n ?? a.local_n }, { mode: 'walk' });
        if (!route?.points?.length) { arrived = true; return; }
        walk([{ e: actor.e, n: actor.n, y: null }, ...route.points.map(([e, n]) => ({ e, n, y: null }))], a.yaw_deg ?? null);
        walking = true;
        walkWith(actor, true);
      } }],
    }));

    const thing = {
      id: `person:${actor.id}`,
      kind: 'person',
      personId: actor.personId,
      actor,
      door: doorId,
      name,
      states: ['out', 'home'],
      _state: actor.indoors ? 'home' : 'out',
      get state() { return scheduled ? (actor.indoors ? 'home' : 'out') : this._state; },
      set state(value) { this._state = value; },
      /** Where he is; indoors, with people hidden (Settings › Show › People), or held out
       *  by a jaunt that does not call for him (T-3495), nowhere a visitor can reach. */
      get at() { return actor.indoors || actor.disposed || humans.shown === false || humans.isHeld?.(actor) || hosted() ? null : [actor.e, actor.n]; },
      reach: PERSON_REACH_M,
      actions: {
        get out() { return hosted() ? [] : [
          { id: 'greet', label: 'Greet', to: 'out', said: '',
            steps: [{ label: 'Greeting', seconds: GREET_S, run: (t) => {
              if (t === 0) { if (scheduled) days.pause(actor.id); greet(); }
              if (t >= 1) openCard(actor);
            } }] },
          ...(scheduled ? [{ id: 'go_home', label: 'Go inside', said: '',
            refuse: () => days.request(actor.id).ok ? null : 'Not available just now',
            steps: [] }] : [{ id: 'go_home', label: 'Go inside', to: 'home', said: () => `${name} has gone in`,
            steps: [
              { label: 'Going inside', until: () => arrived, timeout: 180, run: (t) => {
                if (t !== 0) return;
                stopWalking();
                way = wayHome(houseDoors, doorId, [actor.e, actor.n], { ...ground, router });
                if (!way) { arrived = true; return; }
                walk(way.toDoor, way.inward);
              } },
              { label: 'Opening the door', until: doorOpen, timeout: 10, run: (t) => { if (t === 0) houseDoors.open(doorId); } },
              { label: 'Going in', until: () => arrived, timeout: 30, run: (t) => {
                if (t !== 0) return;
                if (way) walk(way.inside, way.inward); else arrived = true;
              } },
              { label: 'Closing the door', until: doorShut, timeout: 10, run: (t) => {
                if (t !== 0) return;
                actor.setIndoors(true);
                // Someone in the doorway: he leaves it open rather than shut it on them.
                closeDoor();
              } },
            ] },
          ]),
          ...(scheduled ? days.outdoorActivities(actor.id).map((a) => ({
            id: `activity:${a.id}`, label: a.label, said: '',
            refuse: () => days.request(actor.id, a.id).ok ? null : 'Not available just now', steps: [],
          })) : []),
          ...strolls,
        ]; },
        get home() { return hosted() ? [] : [
          // T-3444: asked for at the door (the door's own action starts this).
          { id: 'come_out', label: 'Come to the door', to: 'out', said: () => `${name} comes to the door`,
            steps: [
              { label: 'Coming to the door', seconds: ANSWER_S },
              { label: 'Opening the door', until: doorOpen, timeout: 10, run: (t) => {
                if (t !== 0) return;
                const v = visitor();
                way = wayOut(houseDoors, doorId, v ? [v.e, v.n] : null, ground);
                if (!way) return;
                // Just inside, facing out, as the door swings.
                actor.stopPath();
                actor.e = way.start.e; actor.n = way.start.n; actor.standY = way.start.y;
                actor.heading = way.outward;
                actor.setIndoors(false);
                actor.place?.();
                houseDoors.open(doorId);
              } },
              { label: 'Coming out', until: () => arrived, timeout: 30, run: (t) => {
                if (t !== 0) return;
                if (!way) { arrived = true; return; }
                const v = visitor();
                const end = way.out.at(-1);
                walk([...way.toThreshold, ...way.out.slice(1)], v ? bearing(v.e - end.e, v.n - end.n) : way.outward);
              } },
              { label: 'Closing the door', until: doorShut, timeout: 10, run: (t) => {
                if (t === 0) { closeDoor(); if (scheduled) days.pause(actor.id); greet(); }
              } },
            ] },
        ]; },
      },
    };
    interactions.add(thing);
    errands.push(thing);
  }

  // T-3444: each hung door with someone at home behind it offers to ask for them: first
  // while it is shut (a caller knocks), after Close while it stands open.
  for (const doorId of new Set(errands.map((t) => t.door))) {
    const d = houseDoors.get(doorId);
    const base = d.actions;
    const asks = () => errands.filter((t) => t.door === doorId && t.state === 'home' && (!days || !Array.isArray(t.actor.instance?.behaviour?.day) || days.canAsk(t.actor.id)) && !t.running).map((t) => ({
      id: `ask:${t.personId}`, label: `Ask for ${t.name}`, said: '',
      steps: [{ label: 'Knocking', seconds: 0, run: (x) => { if (x === 0) interactions.act(t, 'come_out'); } }],
    }));
    d.actions = {
      get closed() { return [...asks(), ...(base.closed ?? [])]; },
      get open() { return [...(base.open ?? []), ...asks()]; },
    };
  }

  const find = (id) => errands.find((t) => t.id === id || t.personId === id || t.actor.id === id) ?? null;
  return {
    errands,
    get: find,
    /** Send a person home now (the console, the smoke): { ok, why } from interact.js. */
    sendHome: (id) => { const t = find(id); return t ? interactions.act(t, 'go_home') : { ok: false, why: 'no such person' }; },
    /** Ask for a person at their door now, as the door's Ask for does. */
    callOut: (id) => { const t = find(id); return t ? interactions.act(t, 'come_out') : { ok: false, why: 'no such person' }; },
    /** Walk a person to one of their door's strolls ('stroll:court'). */
    stroll: (id, strollId) => { const t = find(id); return t ? interactions.act(t, strollId) : { ok: false, why: 'no such person' }; },
    dispose() {},
  };
}
