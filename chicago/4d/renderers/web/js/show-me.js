/**
 * show-me.js — Inspect's "Show me" (T-2640, NAV-503; DESIGN §08 "Look for", §13 motion).
 *
 * Each Look for item of a building's summary record (data/summaries/, compiled by
 * tools/compile_summaries.py) names a feature and the camera that sees it: `camera.yaw`, the
 * bearing the camera faces (0 north, 90 east), and `camera.pitch`, degrees above level.
 * Show me stands the visitor outside the building on the line that looks along that bearing
 * through the building's centre, faces the bearing at that pitch, and pulses an outline on
 * the building for 2 s. It aims ONLY where a record says to: an item without a camera, a
 * building without a footprint, or a stand that would put the visitor inside a building is
 * refused, never guessed at.
 *
 *   on foot   a 900 ms ease-in-out glide and turn to the stand (§13 "Show me camera turn");
 *   flying    down to the stand first (a viewpoint on the ground), then the turn;
 *   reduced motion  an instant cut, and the outline shows without pulsing.
 *
 * Pure planning (`plan`) is separate from running it (`createShowMe`), so the test drives
 * both with fakes; no THREE here.
 */
export const TURN_MS = 900;
export const PULSE_MS = 2000;
/** How far outside the footprint the stand is, and how far it may step back to clear a roof. */
export const STAND_CLEAR_M = 18;
export const STAND_MAX_EXTRA_M = 40;

const DEG = Math.PI / 180;
const wrap = (d) => ((d % 360) + 360) % 360;

/** A record's camera, or null when it does not name one a visitor can be pointed along. */
export function cameraOf(item) {
  const c = item?.camera;
  if (!c || !Number.isFinite(c.yaw) || !Number.isFinite(c.pitch)) return null;
  if (c.pitch < -90 || c.pitch > 90) return null;
  return { yaw: wrap(c.yaw), pitch: c.pitch };
}

/** The footprint's centre and the radius that encloses it, in field metres. */
export function footprintCentre(points) {
  if (!Array.isArray(points) || points.length < 3) return null;
  let e = 0, n = 0;
  for (const [x, y] of points) { e += x; n += y; }
  e /= points.length; n /= points.length;
  let r = 0;
  for (const [x, y] of points) r = Math.max(r, Math.hypot(x - e, y - n));
  return { e, n, r };
}

/**
 * Where to stand for one Look for item: on the far side of the building's centre from where
 * the camera looks, clear of the footprint, stepping back a metre at a time (up to
 * STAND_MAX_EXTRA_M) while `blocked(e, n)` says that spot is inside something. Null when the
 * record names no camera, there is no footprint, or no clear stand exists.
 */
export function plan(item, footprint, { blocked = () => false } = {}) {
  const cam = cameraOf(item);
  const c = footprintCentre(footprint);
  if (!cam || !c) return null;
  const se = Math.sin(cam.yaw * DEG), sn = Math.cos(cam.yaw * DEG);
  for (let extra = 0; extra <= STAND_MAX_EXTRA_M; extra += 1) {
    const d = c.r + STAND_CLEAR_M + extra;
    const e = c.e - se * d, n = c.n - sn * d;
    if (!blocked(e, n)) return { e, n, yaw: cam.yaw, pitch: cam.pitch, feature: item.feature ?? null, distance: d };
  }
  return null;
}

/** Ease in and out (cubic), for the turn. */
export function easeInOut(t) { return t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2; }

/** The shorter way round from one bearing to another, in degrees (−180 … 180]. */
export function turnBy(from, to) {
  const d = wrap(to - from);
  return d > 180 ? d - 360 : d;
}

export function createShowMe({
  pose,                       // () => { e, n, yaw, pitch, flying }
  place,                      // ({ e, n, yaw, pitch }) => void — set the walker there
  land = () => {},            // leave free-fly (a viewpoint is on the ground)
  outline = () => {},         // ({ on, pulse }) => void — the outline on the building
  reduced = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  frame = (fn) => globalThis.requestAnimationFrame?.(fn) ?? globalThis.setTimeout(() => fn(now()), 16),
  wait = (fn, ms) => globalThis.setTimeout(fn, ms),
  now = () => (globalThis.performance?.now?.() ?? Date.now()),
} = {}) {
  let run = 0;
  let last = null;

  function finish(id, target, resolve) {
    if (id !== run) return;
    place(target);
    const pulse = !reduced();
    outline({ on: true, pulse });
    last = { ...target, at: now(), cut: !pulse };
    wait(() => { if (id === run) outline({ on: false, pulse: false }); }, PULSE_MS);
    resolve(true);
  }

  /** Run a plan (from `plan`). Resolves true once the camera is there, false if refused. */
  function show(target) {
    const id = ++run;
    if (!target) return Promise.resolve(false);
    return new Promise((resolve) => {
      const start = pose();
      // A viewpoint is on the ground: leave free-fly first, then turn from where you are.
      if (start.flying) land();
      if (reduced()) { finish(id, target, resolve); return; }
      const t0 = now();
      const dYaw = turnBy(start.yaw, target.yaw);
      const step = () => {
        if (id !== run) { resolve(false); return; }
        const k = Math.min(1, (now() - t0) / TURN_MS);
        const f = easeInOut(k);
        if (k >= 1) { finish(id, target, resolve); return; }
        place({ e: start.e + (target.e - start.e) * f, n: start.n + (target.n - start.n) * f,
          yaw: wrap(start.yaw + dYaw * f), pitch: start.pitch + (target.pitch - start.pitch) * f });
        frame(step);
      };
      frame(step);
    });
  }

  return {
    show,
    /** Stop a turn under way (the visitor took the controls, or left the town). */
    cancel() { run++; outline({ on: false, pulse: false }); },
    get last() { return last ? { ...last } : null; },
  };
}
