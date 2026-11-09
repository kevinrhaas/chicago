// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * jaunt-hosts.js — the people who show a visitor round on a jaunt (T-3525).
 *
 * The owner, 2026-11-08: *"this will be the first jaunt we will show people here ... do a
 * tour of glessner house from the outside by all the people who live there, like have john or
 * frances welcome you and have everyone in the house explain their roles in the house ... you
 * walk around and visit people"*. So a jaunt stop may name `hosts`: the person who tells that
 * stop, and the mark they stand at (data/jaunts/schema.json). While the visitor walks to the
 * stop its hosts come to their marks (out of the house by its door, when their day has them
 * in), turn to the stop's stand, and greet the visitor when they arrive; when the visitor
 * walks on, they go back about their day.
 *
 *   sync(hosts, { stand, arrived })   hosts = [{ person, local_e, local_n }] wanted now;
 *                                     `stand` ({ e, n }) is where the visitor will stand, so
 *                                     each turns to it; `arrived` greets them (once a stop)
 *   release()                         every host back to their day
 *   active                            the person ids held as hosts now
 *
 * A person with a day (human-days.js) is taken out of it by `days.host` and given back by
 * `days.unhost`. Walking up to a host does not open their card (`actor.jauntHost`): the stop's
 * text is their introduction, and its person link opens the card. One without (a figure standing at its placement, or walking a looped route)
 * is walked to the mark by its own `walkPath` and back to where it was taken from after; a
 * route walker then takes up its route again. Nothing here says a word: the words are the
 * stop's text, and the figure only turns, looks and greets (human-actions.js), as anywhere.
 */

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const dist = (a, b) => Math.hypot(a.e - b.e, a.n - b.n);

/** The mark a stop's host stands at: { e, n }, or null for a malformed row. */
export function markOf(host) {
  const e = Number(host?.local_e), n = Number(host?.local_n);
  return typeof host?.person === 'string' && host.person && Number.isFinite(e) && Number.isFinite(n) ? { e, n } : null;
}

/** The person ids a stop's `hosts` name. */
export const hostIds = (stop) => (Array.isArray(stop?.hosts) ? stop.hosts : []).map((h) => h?.person).filter((id) => typeof id === 'string' && id);

export function createJauntHosts({ humans, days = null, router = null, visitor = () => null, eye = () => null } = {}) {
  /** person id -> { actor, mark, via: 'days'|'self', back, route, arrived, greeted } */
  const held = new Map();

  function way(a, b) {
    const route = router?.plan?.({ e: a.e, n: a.n }, { e: b.e, n: b.n }, { mode: 'walk' });
    const pts = route?.points?.length ? route.points.map(([e, n]) => ({ e, n })) : [];
    return [{ e: a.e, n: a.n }, ...pts.filter((p) => dist(p, a) > 0.05 && dist(p, b) > 0.05), { e: b.e, n: b.n }];
  }

  function greet(h) {
    const a = h.actor;
    if (h.greeted || !a || a.disposed) return;
    h.greeted = true;
    const v = visitor();
    if (v) a.turnTo?.(bearing(v.e - a.e, v.n - a.n));
    const e = eye();
    if (e) a.life?.attend?.(e, 6);
    a.actions?.greet?.();
  }

  function take(host, stand) {
    const mark = markOf(host);
    const actor = humans?.get?.(host.person);
    if (!mark || !actor || actor.disposed) return null;
    const heading = stand ? bearing(stand.e - mark.e, stand.n - mark.n) : null;
    actor.jauntHost = true;   // humans.js: walking up to a host does not open their card over the stop
    const h = { actor, mark, heading, via: null, back: null, route: false, arrived: false, greeted: false, wantGreet: false };
    const onArrive = () => { h.arrived = true; if (h.wantGreet) greet(h); };
    if (days?.host?.(host.person, mark, { heading, onArrive })?.ok) {
      h.via = 'days';
      return h;
    }
    // No day of their own: walk them there, and remember where they were.
    h.via = 'self';
    h.back = { e: actor.e, n: actor.n, heading: actor.heading, indoors: !!actor.indoors };
    h.route = actor.state === 'walking' && !actor.path && Array.isArray(actor.route);
    if (actor.indoors) { actor.setIndoors?.(false); actor.e = mark.e; actor.n = mark.n; actor.standY = null; actor.place?.(); }
    const pts = way({ e: actor.e, n: actor.n }, mark);
    if (dist(pts[0], mark) < 0.05 || !actor.walkPath?.(pts, { endHeading: heading, onArrive })) {
      actor.path = null; actor.e = mark.e; actor.n = mark.n;
      if (Number.isFinite(heading)) actor.heading = heading;
      actor.setState?.('standing'); actor.place?.();
      onArrive();
    }
    return h;
  }

  function give(person, h) {
    held.delete(person);
    const a = h.actor;
    if (!a || a.disposed) return;
    a.jauntHost = false;
    if (h.via === 'days') { days?.unhost?.(person); return; }
    const b = h.back;
    const home = () => {
      if (b.indoors) { a.setIndoors?.(true); return; }
      if (h.route) a.setState?.('walking');
    };
    const pts = way({ e: a.e, n: a.n }, b);
    if (dist(pts[0], b) < 0.05 || !a.walkPath?.(pts, { endHeading: b.heading, onArrive: home })) {
      a.path = null; a.e = b.e; a.n = b.n; a.heading = b.heading; a.setState?.('standing'); a.place?.(); home();
    }
  }

  const api = {
    get active() { return [...held.keys()]; },
    sync(hosts = [], { stand = null, arrived = false } = {}) {
      const wanted = new Map();
      for (const host of Array.isArray(hosts) ? hosts : []) if (markOf(host)) wanted.set(host.person, host);
      for (const [person, h] of [...held]) {
        const w = wanted.get(person);
        if (!w || dist(markOf(w), h.mark) > 0.05) give(person, h);
      }
      for (const [person, host] of wanted) {
        if (held.has(person)) continue;
        const h = take(host, stand);
        if (h) held.set(person, h);
      }
      if (arrived) for (const h of held.values()) { h.wantGreet = true; if (h.arrived) greet(h); }
      return api.active;
    },
    release() { for (const [person, h] of [...held]) give(person, h); },
  };
  return api;
}
