/**
 * motion.js — the one motion choice (T-3671, WCAG 2.2.2 and 2.3.3; the owner asked for
 * "motion-comfort settings").
 *
 * Settings › Look › Motion is three keys:
 *
 *   system  (the default) follow the device: `prefers-reduced-motion: reduce` reduces.
 *   reduce  reduce, whatever the device says.
 *   full    full motion, whatever the device says.
 *
 * It is kept at `chicago4d.motion` (localStorage). Every reader that used to ask the media
 * query itself asks `reducedMotion()` here instead, and a reader that wants to hear a change
 * subscribes with `onMotionChange(fn)`. `motionQuery` is a MediaQueryList-shaped stand-in
 * (`matches`, `addEventListener('change', fn)`) for the readers written against one.
 *
 * The page carries the answer as html[data-motion="reduce" | "full"]: css/walk.css ends with
 * the one rule that takes every transition and animation to (almost) nothing under "reduce".
 * A stylesheet's own `@media (prefers-reduced-motion: reduce)` rules still follow the device,
 * so Full on a device that asks for less keeps those few CSS effects reduced; everything the
 * scripts move (head bob, fly-ins, the Jump and Recall rings, the telemetry strip) follows it.
 *
 * What Reduce does, file by file: travel.js (no head bob, no glides: a cut to the place),
 * recall.js and apps/jump-view.js (the ring travel is a cut), nav-rail.js (a crossfade, not a
 * warm-up), show-me.js (no pulse, no fly), arrival.js (no rolling year), nav-telemetry.js (the
 * strip stands at its steady reading), standing-horses.js and the town's teams (they stand).
 *
 * No DOM is needed to import it: a test, or a module loaded under node, reads `system` and the
 * device's answer as "no preference".
 */

export const MOTION_KEY = 'chicago4d.motion';
export const MOTION_CHOICES = Object.freeze(['system', 'reduce', 'full']);
export const MOTION_LABELS = Object.freeze({ system: 'System', reduce: 'Reduce', full: 'Full' });
const QUERY = '(prefers-reduced-motion: reduce)';

const listeners = new Set();
let choice = null;      // read lazily, so a test can set storage before the first read
let media = null;       // the device's MediaQueryList, once asked
let mediaHooked = false;

function store() { try { return globalThis.localStorage ?? null; } catch { return null; } }

/** A stored value as a choice: anything else is `system`. */
export function normalMotion(v) {
  return MOTION_CHOICES.includes(v) ? v : 'system';
}

function deviceQuery() {
  if (media) return media;
  try { media = globalThis.matchMedia?.(QUERY) ?? null; } catch { media = null; }
  if (media && !mediaHooked) {
    mediaHooked = true;
    const changed = () => { if (motionChoice() === 'system') emit(); };
    try { media.addEventListener?.('change', changed); } catch { /* an old engine: addListener */ try { media.addListener?.(changed); } catch { /* none */ } }
  }
  return media;
}

/** Whether the device asks for less motion. */
export function deviceReduces() {
  return !!deviceQuery()?.matches;
}

/** The choice in force: 'system', 'reduce' or 'full'. */
export function motionChoice() {
  if (choice === null) {
    let v = null;
    try { v = store()?.getItem?.(MOTION_KEY) ?? null; } catch { v = null; }
    choice = normalMotion(v);
  }
  return choice;
}

/** Whether motion is reduced now: the choice, or the device's answer under `system`. */
export function reducedMotion(c = motionChoice()) {
  if (c === 'reduce') return true;
  if (c === 'full') return false;
  return deviceReduces();
}

/** Put the answer on the page: html[data-motion]. Returns it. */
export function applyMotion(doc = globalThis.document) {
  const reduce = reducedMotion();
  const root = doc?.documentElement;
  if (root?.setAttribute) {
    root.setAttribute('data-motion', reduce ? 'reduce' : 'full');
    root.setAttribute('data-motion-choice', motionChoice());
  }
  return reduce ? 'reduce' : 'full';
}

function emit() {
  const reduce = reducedMotion();
  applyMotion();
  for (const fn of [...listeners]) { try { fn(reduce, motionChoice()); } catch (e) { console.warn('[motion]', e); } }
  try { globalThis.document?.dispatchEvent?.(new CustomEvent('chicago4d-motion', { detail: { reduce, choice: motionChoice() } })); } catch { /* no DOM */ }
}

/** Set and keep the choice; every subscriber hears it. Returns the choice in force. */
export function setMotionChoice(next) {
  const c = normalMotion(next);
  choice = c;
  try {
    if (c === 'system') store()?.removeItem?.(MOTION_KEY);
    else store()?.setItem?.(MOTION_KEY, c);
  } catch { /* storage refused: the choice holds for the visit */ }
  emit();
  return c;
}

/** Hear every change of the answer (the choice, or the device under `system`). Returns an unsubscribe. */
export function onMotionChange(fn) {
  if (typeof fn !== 'function') return () => {};
  deviceQuery();
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** A MediaQueryList-shaped view of the answer, for the readers written against one. */
export const motionQuery = Object.freeze({
  media: QUERY,
  get matches() { return reducedMotion(); },
  addEventListener(type, fn) { if (type === 'change' && typeof fn === 'function') { fn.__motionOff = onMotionChange(() => fn({ matches: reducedMotion(), media: QUERY })); } },
  removeEventListener(type, fn) { if (type === 'change') fn?.__motionOff?.(); },
});

/** Another tab changed it: follow. */
try {
  globalThis.addEventListener?.('storage', (e) => {
    if (e?.key !== MOTION_KEY) return;
    choice = normalMotion(e.newValue);
    emit();
  });
} catch { /* no window */ }

applyMotion();
