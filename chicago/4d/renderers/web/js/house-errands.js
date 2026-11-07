/**
 * house-errands.js — a person who lives in a house, met in the street, can be sent home:
 * up the steps, through the door, and in (T-3443).
 *
 * The owner, 2026-11-07: *"how can we interact with him? I suppose he needs to be somewhere,
 * sitting or standing near the house? we might want to be able to give them interactions
 * like tell them to go home into their house"*. So a drawn PERSON whose household has a
 * working front door (house-doors.js, T-3442) is an Interact thing (interact.js) of its own:
 *
 *   out    Greet     he turns to the visitor, looks at them and touches his hat brim
 *                    (human-life.js / human-actions.js), and his own card opens: the record's
 *                    card, never invented words (data/humans/contract.json § L1)
 *          Go home   he walks from where he stands up his front walk and steps to the door,
 *                    opens it, goes in, and it closes behind him (unless the visitor is
 *                    standing in its swing, when it is left open)
 *   home   —         indoors: not drawn, not picked, met by no one. Calling him back out at
 *                    the door is T-3444's.
 *
 * WHICH DOOR IS WHOSE: `HOUSEHOLD_DOORS`, from the household the person's row names (the
 * people directory's `household`) to the door its house is entered by. The Glessners' is
 * 1800 Prairie Avenue's front door, the one the household's address names (`glessner_house`
 * symbolic_location). Only doors house-doors.js hangs are listed. It is the family's door:
 * a row whose relationship is `servant` (Mattie Williamson, the cook) is not sent through it
 * — the staff came and went by the service entrance off the court, which is not hung yet.
 *
 * Nothing here knows the DOM; tools/test_house_errands.mjs drives it with the real door
 * layer and a real HumanActor.
 */

/** A household, by its id in the people directory, and the door its house is entered by. */
export const HOUSEHOLD_DOORS = Object.freeze({
  hh_glessner_john_j: 'glessner_house:front',
});

/** Who goes in and out by the front door: the household's own, not its staff. */
export const usesFrontDoor = (person) => !!person && person.relationship !== 'servant';

/** How near, on foot, the visitor must stand to a person for the Interact key to offer them. */
export const PERSON_REACH_M = 2.5;
/** Where a figure waits while its door swings: this far out from the leaf's face, on the
 *  threshold (his chest clear of the leaf as it turns in). */
export const DOOR_WAIT_M = 0.3;
/** How far past the leaf a figure walks before it is indoors (house-doors.js `inside`). */
export const INDOORS_M = 1.2;
/** The greeting: how long it takes, before the card opens. */
export const GREET_S = 1.4;

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;

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

/**
 * A person's way home from (e, n): house-doors.js's walk to the door, with the stretch
 * behind him cut off (a man standing on his own front walk does not go back to the
 * sidewalk first), split where he waits for the door: `[toDoor, inside]`, and the
 * heading that faces the door. Null without a path.
 */
export function wayHome(houseDoors, doorId, from, { groundAt } = {}) {
  const pts = houseDoors.path(doorId, { from, inside: INDOORS_M, ...(groundAt ? { groundAt } : {}) });
  if (!pts || pts.length < 3) return null;
  const end = pts.at(-1);
  const far = (p) => Math.hypot(p.e - end.e, p.n - end.n);
  const start = pts[0];
  // Keep the start, then only what lies nearer the door than he does.
  const kept = [start, ...pts.slice(1).filter((p) => far(p) < far(start) - 0.05)];
  // The leaf's face is the last point but one; he waits DOOR_WAIT_M short of it.
  const leafAt = kept.length - 2;
  const wait = pointShortOf(kept, leafAt, DOOR_WAIT_M);
  const toDoor = [...kept.slice(0, wait.at), wait.point];
  const inside = [wait.point, ...kept.slice(wait.at)];
  return { toDoor, inside, inward: (pts.outward + 180) % 360, outward: pts.outward };
}

/**
 * @param {object} o
 * @param {{ actors: object[] }} o.humans          the human layer (humans.js)
 * @param {object} o.houseDoors                     house-doors.js's layer (open, close, get, path)
 * @param {object} o.interactions                   interact.js's engine
 * @param {() => {e:number, n:number} | null} [o.visitor]   where the visitor stands (local ENU)
 * @param {() => object | null} [o.eye]             the camera's world position (a Vector3), for gaze
 * @param {(actor: object) => void} [o.openCard]    open the person's own card
 * @param {(e:number, n:number) => number} [o.groundAt]
 * @param {string[]} [o.problems]
 */
export function createHouseErrands({ humans, houseDoors, interactions, visitor = () => null, eye = () => null,
  openCard = () => {}, groundAt = null, problems = [] } = {}) {
  const errands = [];
  if (!humans || !houseDoors || !interactions) return { errands, get: () => null, dispose() {} };

  for (const actor of humans.actors ?? []) {
    const person = actor.person ?? actor.identity?.person ?? null;
    if (actor.identity?.kind !== 'person' || !person) continue;
    const doorId = HOUSEHOLD_DOORS[person.household];
    if (!doorId || !usesFrontDoor(person)) continue;
    if (!houseDoors.get(doorId)) { problems.push(`${actor.id}: ${doorId} is not hung in this scene — he cannot be sent home`); continue; }
    const name = person.name ?? actor.id;
    const door = () => houseDoors.get(doorId);
    let way = null, arrived = false, refused = false;
    const walk = (points, heading) => {
      arrived = false;
      if (!actor.walkPath(points, { endHeading: heading, onArrive: () => { arrived = true; } })) arrived = true;
    };

    const thing = {
      id: `person:${actor.id}`,
      kind: 'person',
      personId: actor.personId,
      actor,
      door: doorId,
      name,
      states: ['out', 'home'],
      state: actor.indoors ? 'home' : 'out',
      /** Where he is; indoors, or with people hidden (Settings › Show › People), nowhere a
       *  visitor can reach. */
      get at() { return actor.indoors || actor.disposed || humans.shown === false ? null : [actor.e, actor.n]; },
      reach: PERSON_REACH_M,
      actions: {
        out: [
          { id: 'greet', label: 'Greet', to: 'out', said: '',
            steps: [{ label: 'Greeting', seconds: GREET_S, run: (t) => {
              if (t === 0) {
                const v = visitor();
                if (v) actor.turnTo(bearing(v.e - actor.e, v.n - actor.n));
                const p = eye();
                if (p) actor.life?.attend?.(p, 6);
                actor.actions?.greet?.();
              }
              if (t >= 1) openCard(actor);
            } }] },
          { id: 'go_home', label: 'Go home', to: 'home', said: () => `${name} has gone in`,
            steps: [
              { label: 'Walking home', until: () => arrived, timeout: 90, run: (t) => {
                if (t !== 0) return;
                way = wayHome(houseDoors, doorId, [actor.e, actor.n], groundAt ? { groundAt } : {});
                if (!way) { arrived = true; return; }
                walk(way.toDoor, way.inward);
              } },
              { label: 'Opening the door', until: () => { const d = door(); return !d || (d.state === 'open' && !d.running); },
                timeout: 10, run: (t) => { if (t === 0) houseDoors.open(doorId); } },
              { label: 'Going in', until: () => arrived, timeout: 30, run: (t) => {
                if (t !== 0) return;
                if (way) walk(way.inside, way.inward); else arrived = true;
              } },
              { label: 'Closing the door', until: () => { const d = door(); return refused || !d || (d.state === 'closed' && !d.running); },
                timeout: 10, run: (t) => {
                  if (t !== 0) return;
                  actor.setIndoors(true);
                  // Someone in the doorway: he leaves it open rather than shut it on them.
                  refused = !houseDoors.close(doorId)?.ok;
                } },
            ] },
        ],
        home: [],
      },
    };
    interactions.add(thing);
    errands.push(thing);
  }

  return {
    errands,
    get: (id) => errands.find((t) => t.id === id || t.personId === id || t.actor.id === id) ?? null,
    /** Send a person home now (the console, the smoke): { ok, why } from interact.js. */
    sendHome: (id) => {
      const t = errands.find((x) => x.id === id || x.personId === id || x.actor.id === id);
      return t ? interactions.act(t, 'go_home') : { ok: false, why: 'no such person' };
    },
    dispose() {},
  };
}
