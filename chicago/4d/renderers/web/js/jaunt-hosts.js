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
  // Released dayless figures keep their original place until a safe return succeeds.
  const returning = new Map();
  let wanted = new Map(), stand = null, readyCallback = null, skipped = new Set(), visitorArrived = false, clock = 0, retryAt = 0;
  const waiting = () => [...wanted.keys()].filter((id) => !skipped.has(id) && !held.get(id)?.arrived);
  function notifyReady() { if (!waiting().length) { const done = readyCallback; readyCallback = null; done?.(); } }


  function way(a, b) {
    let route;
    try { route = router?.plan?.({ e: a.e, n: a.n }, { e: b.e, n: b.n }, { mode: 'walk' }); } catch { return null; }
    if (!Array.isArray(route?.points) || !route.points.length || !route.points.every((q) => Array.isArray(q) && q.length === 2 && q.every(Number.isFinite))) return null;
    if (Math.hypot(route.points.at(-1)[0] - b.e, route.points.at(-1)[1] - b.n) > 0.05) return null;
    const pts = route.points.map(([e, n]) => ({ e, n }));
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

  function take(host, stand, cut = false) {
    const mark = markOf(host);
    const actor = humans?.get?.(host.person);
    if (!mark || !actor || actor.disposed) { skipped.add(host.person); return null; }
    const heading = stand ? bearing(stand.e - mark.e, stand.n - mark.n) : null;
    const h = { actor, mark, heading, via: null, back: null, route: false, arrived: false, greeted: false, wantGreet: false };
    const onArrive = () => { if (h.released) return; h.arrived = true; if (h.wantGreet) greet(h); notifyReady(); };
    const day = days?.host?.(host.person, mark, { heading, onArrive, safeTravel: true, atCut: cut });
    if (day?.ok) {
      actor.jauntHost = true;
      h.via = 'days';
      return h;
    }
    if (day && day.why !== 'no such person') { skipped.add(host.person); return null; } // absent is not a dayless figure
    // No day of their own: walk them there, and remember where they were.
    h.via = 'self';
    const previous = returning.get(host.person);
    h.back = previous?.back ?? { e: actor.e, n: actor.n, heading: actor.heading, indoors: !!actor.indoors };
    h.route = previous?.route ?? (actor.state === 'walking' && !actor.path && Array.isArray(actor.route));
    if (actor.indoors) { actor.setIndoors?.(false); actor.e = mark.e; actor.n = mark.n; actor.standY = null; actor.place?.(); }
    const hidden = actor.root?.visible === false || cut; // cut is supplied only after the camera actually jumped
    const close = dist(actor, mark) < 0.05;
    const pts = hidden || close ? null : way({ e: actor.e, n: actor.n }, mark);
    if (!hidden && !close && !pts) return null;
    actor.jauntHost = true;
    if (hidden || close) {
      actor.path = null; actor.e = mark.e; actor.n = mark.n;
      if (Number.isFinite(heading)) actor.heading = heading;
      actor.setState?.('standing'); actor.place?.();
      onArrive();
    } else if (!actor.walkPath?.(pts, { endHeading: heading, onArrive })) {
      actor.jauntHost = false; return null;
    }
    if (previous) { previous.returning = false; returning.delete(host.person); }
    return h;
  }

  function returnHome(person, h) {
    const a = h.actor, b = h.back;
    if (!a || a.disposed) { returning.delete(person); return; }
    if (h.movingBack && a.path) return;
    h.movingBack = false;
    const home = () => {
      if (returning.get(person) !== h) return; // a later takeover owns this figure now
      returning.delete(person);
      h.returning = false;
      if (b.indoors) { a.setIndoors?.(true); return; }
      if (h.route) a.setState?.('walking');
    };
    const hidden = a.root?.visible === false;
    const close = dist(a, b) < 0.05;
    const pts = hidden || close ? null : way(a, b);
    if (hidden || close) {
      a.path = null; a.e = b.e; a.n = b.n; a.heading = b.heading;
      a.setState?.('standing'); a.place?.(); home();
    } else if (pts) {
      h.movingBack = true;
      if (!a.walkPath?.(pts, { endHeading: b.heading, onArrive: home })) h.movingBack = false;
    }
    // An unavailable/rejected route retains this return; update retries without teleporting.
  }

  function give(person, h) {
    held.delete(person);
    h.released = true;
    const a = h.actor;
    if (!a || a.disposed) return;
    a.jauntHost = false;
    if (h.via === 'days') { days?.unhost?.(person); return; }
    h.returning = true; h.movingBack = false;
    returning.set(person, h);
    returnHome(person, h);
  }

  function takeWanted(cut = false) {
    for (const [person, host] of wanted) {
      if (held.has(person) || skipped.has(person)) continue;
      const h = take(host, stand, cut);
      if (h) { h.wantGreet = visitorArrived; held.set(person, h); if (h.arrived && h.wantGreet) greet(h); }
    }
    notifyReady();
  }

  const api = {
    get active() { return [...held.keys()]; },
    get waiting() { return waiting(); },
    get returning() { return [...returning.keys()]; },
    sync(hosts = [], { stand: target = null, arrived = false, retain = [], cut = false, onReady = null } = {}) {
      const retained = new Set(retain);
      wanted = new Map(); stand = target; skipped = new Set(); readyCallback = onReady; visitorArrived = arrived;
      for (const host of Array.isArray(hosts) ? hosts : []) if (markOf(host)) wanted.set(host.person, host);
      for (const [person, h] of [...held]) {
        const w = wanted.get(person);
        if ((!w && !retained.has(person)) || (w && (dist(markOf(w), h.mark) > 0.05 || (cut && !h.arrived)))) give(person, h);
      }
      takeWanted(cut);
      for (const [person, h] of held) {
        h.wantGreet = arrived && wanted.has(person);
        if (h.wantGreet && h.arrived) greet(h);
      }
      notifyReady();
      return api.active;
    },
    update(dt) {
      if (!(dt > 0) || !Number.isFinite(dt)) return;
      clock += dt;
      if (clock < retryAt) return;
      retryAt = clock + 0.5;
      for (const [person, h] of returning) returnHome(person, h);
      takeWanted();
    },
    release() {
      wanted.clear(); skipped.clear(); readyCallback = null;
      for (const [person, h] of [...held]) give(person, h);
    },
  };
  return api;
}
