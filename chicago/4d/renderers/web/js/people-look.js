// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * people-look.js — the target tag names a PERSON you look at (T-3404).
 *
 * target.js answers "what building is right in front of you" for the tag, Home and Inspect
 * alike, and Inspect opens whatever it answers as a building. A person is not a building, so
 * they are not put into that shared answer: this wraps it for the TAG ALONE. Every
 * `interval` ms while the tag listens, `probe()` asks what person is under the crosshair (a
 * ray against the handful of figures' pick boxes, humans.js and the drivers'), and when one
 * stands nearer than the building behind them, within `within` metres, the tag hears the
 * person instead: `{ id: 'person:<id>', kind: 'person', personId, label, distance }`.
 * Otherwise it hears the building target.js gave, unchanged, at its own moment.
 *
 * The interface is the slice of target.js that target-tag.js reads, `on(fn, { within })`
 * and `current(within)`. No THREE, no DOM: tools/test_person_interaction.mjs drives it
 * with fakes.
 */
export const PERSON_LOOK_M = 30;

export function createPeopleLook({ target, probe, within: personWithin = PERSON_LOOK_M, interval = 500,
  every = (fn, ms) => setInterval(fn, ms), stopEvery = (id) => clearInterval(id) } = {}) {
  let person = null;
  let timer = null;
  const listeners = new Map();   // fn -> { within, building, seen, off }

  const asPerson = (hit) => (hit && hit.personId && Number.isFinite(hit.distance) && hit.distance <= personWithin
    ? { id: `person:${hit.personId}`, kind: 'person', personId: hit.personId, label: hit.label ?? null,
      record: null, distance: hit.distance } : null);

  function pick(building, within) {
    const b = building && building.distance <= within ? building : null;
    const p = person && person.distance <= within ? person : null;
    return p && (!b || p.distance <= b.distance) ? p : b;
  }

  function tell(fn, l) {
    const next = pick(l.building, l.within);
    if ((next?.id ?? null) === (l.seen?.id ?? null)) { l.seen = next; return; }
    const previous = l.seen;
    l.seen = next;
    fn(next, previous);
  }

  function look() {
    let hit = null;
    try { hit = probe(); } catch { hit = null; }
    person = asPerson(hit);
    for (const [fn, l] of [...listeners]) tell(fn, l);
  }

  return {
    on(fn, { within = Infinity } = {}) {
      const l = { within, building: null, seen: null, off: null };
      listeners.set(fn, l);
      l.off = target?.on?.((t) => { l.building = t; tell(fn, l); }, { within }) ?? null;
      if (timer === null) timer = every(look, interval);
      return () => {
        l.off?.();
        listeners.delete(fn);
        if (!listeners.size && timer !== null) { stopEvery(timer); timer = null; person = null; }
      };
    },
    current(within = Infinity) {
      const b = target?.current?.(within) ?? null;
      look();
      return pick(b, within);
    },
    /** For the console and the smoke: the person the tag would name now. */
    get person() { return person; },
    look,
  };
}
