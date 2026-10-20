/**
 * target.js — what is right in front of you (T-2617, NAV-201).
 *
 * The Navigator's Home says "RIGHT IN FRONT OF YOU", the HUD's target tag (T-2627)
 * says it after a dwell, and Inspect (T-2638) offers itself within 40 m. All three
 * ask the same question at different distances, so it is answered once, here, out to
 * `reach`, and each asker says how near is near for it (`within`): Home takes the
 * building across the street (100 m — the Glessner House is 72 m from where 1904
 * opens), Inspect will take 40 m.
 *
 * It asks nothing new of the renderer. Tapping a building already answers "what is
 * under this point" with a one-pixel GPU pick per layer (gpu-pick.js), and inspect()
 * in main.js already aims "down the crosshair" by passing no point at all. The probe
 * is that same aim, handed in as `pick()`, with three limits so it costs nothing a
 * visitor would notice:
 *
 *   - it runs only while something is listening (`on`) or has just asked (`current`);
 *   - at most once per `interval` (500 ms), and only after the eye has moved
 *     (`moveM` metres or `turnDeg` degrees) since the last look, or was told to look
 *     again (`invalidate`, after a teleport);
 *   - it answers only within `reach` metres (150 m), and each listener only within
 *     its own `within`.
 *
 * `pick()` returns `{ id, record, distance }` or null; `pose()` returns
 * `{ e, n, bearingDeg, pitchDeg }`. A listener hears `(target, previous)` when the id
 * IT sees changes, null included. No DOM, no THREE: tools/test_navigator.mjs drives it with
 * fakes.
 *
 * `pickAsync()`, where given, is the same answer as a promise, and the look a moving
 * eye takes (T-2723): `pick()` read the GPU's pixel back on the spot, which waits for
 * the GPU to finish the frame, so every 500 ms of walking was a stalled frame. A look
 * waits for its answer before the next is asked, and an answer that lands after the
 * eye was told to look again (`invalidate`, `clear`, or an asked `current()`) is
 * dropped. `current()` after `invalidate()` still asks `pick()` at once: an asked
 * question is answered now, a rhythm is not.
 */
export function createTarget({ pick, pickAsync = null, pose, reach = 150, interval = 500, moveM = 0.5, turnDeg = 3 } = {}) {
  if (typeof pick !== 'function' || typeof pose !== 'function') throw new Error('createTarget needs pick() and pose()');
  let current = null;
  let lastAt = -Infinity;
  let lastPose = null;
  let dirty = true;
  let waiting = null; // the look in flight, while one is
  let latest = null; // the look whose answer will be heard
  const listeners = new Map(); // fn → { within, seen }
  const near = (t, within) => (t && t.distance <= within ? t : null);

  const moved = (p) => !lastPose
    || Math.hypot(p.e - lastPose.e, p.n - lastPose.n) >= moveM
    || Math.abs(((p.bearingDeg - lastPose.bearingDeg + 540) % 360) - 180) >= turnDeg
    || Math.abs((p.pitchDeg ?? 0) - (lastPose.pitchDeg ?? 0)) >= turnDeg;

  function look() {
    let hit = null;
    latest = null;
    try { hit = pick(); } catch { hit = null; }
    return hear(hit);
  }

  /** The look without the wait: drawn now, heard when it lands, unless overtaken. */
  function lookLater() {
    const mine = {};
    waiting = latest = mine;
    let asked;
    try { asked = Promise.resolve(pickAsync()); } catch { asked = Promise.resolve(null); }
    asked.catch(() => null).then((hit) => {
      if (waiting === mine) waiting = null;
      if (latest === mine) { latest = null; hear(hit); }
    });
    return current;
  }

  function hear(hit) {
    const next = hit && hit.id && Number.isFinite(hit.distance) && hit.distance <= reach
      ? { id: hit.id, record: hit.record ?? null, distance: hit.distance } : null;
    current = next;
    for (const [fn, l] of [...listeners]) {
      const mine = near(next, l.within);
      if ((mine?.id ?? null) === (l.seen?.id ?? null)) continue;
      const previous = l.seen;
      l.seen = mine;
      try { fn(mine, previous); } catch (error) { console.error('[target] listener failed', error); }
    }
    return current;
  }

  /** Called once a frame (main.js) while the visitor is in the town. */
  function tick(now) {
    if (!listeners.size) return current;
    if (now - lastAt < interval || waiting) return current;
    const p = pose();
    if (!dirty && !moved(p)) return current;
    lastAt = now;
    lastPose = { ...p };
    dirty = false;
    return pickAsync ? lookLater() : look();
  }

  return {
    tick,
    /** The last answer within `within` metres; look again first if the eye has moved since
     *  (with `pickAsync`, a moved eye's look is heard when it lands; a told one is looked at now). */
    current(within = reach) {
      const p = pose();
      if (dirty || (moved(p) && !pickAsync)) { lastPose = { ...p }; dirty = false; look(); }
      else if (moved(p) && !waiting) { lastPose = { ...p }; lookLater(); }
      return near(current, within);
    },
    on(fn, { within = reach } = {}) {
      listeners.set(fn, { within, seen: null });
      dirty = true;
      return () => listeners.delete(fn);
    },
    /** The world moved under the eye (a teleport, a scene change): look again next tick. */
    invalidate() { dirty = true; lastAt = -Infinity; latest = null; },
    /** Forget the answer without telling anyone (the visitor left the town). */
    clear() { current = null; lastPose = null; dirty = true; latest = null; },
    get reach() { return reach; },
  };
}
