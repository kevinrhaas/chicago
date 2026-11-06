/**
 * travel.js — how "Go to" takes you there, and the pace you move at on your own.
 *
 * WHY A CONTROLLER THAT WRITES THE INTENT, NOT THE CAMERA
 *
 * The walker is the only thing that authors the camera, and it keeps every rule
 * that makes the town honest: the 0.35 m step, the footprint capsule, the deck
 * floor. A ride to a building must obey the same rules or it will glide through
 * a wall the visitor could not walk through. So this module behaves exactly like
 * an input backend — it writes `forward`, `yawDelta`, `pitchDelta`, `rise` on the
 * shared intent object and the walker consumes them — and it zeroes its own
 * writes afterwards so a standing touch value never leaks into the next frame.
 * The visitor's own writes are never touched: any movement of theirs, a look, a
 * sprint, an inspect or a flipped fly mode ends the ride and their input flows
 * through untouched that same frame (`stop('input')`).
 *
 * PACES ARE INTERFACE CHOICES, NOT CLAIMS ABOUT 1835
 *
 * A wagon at 7.15 m/s, a horse at 11.18 m/s galloping and 19 m/s at full stretch (T-2945), a
 * cruise height of 20–80 m: these are chosen so the town reads well at each pace
 * and a ride does not take seven minutes. They are how the camera moves, not
 * findings about how people moved, which is why there is no LIBERTIES entry for
 * them and why the Travel note says so in as many words. Riding a horse does not
 * draw a horse — by standing instruction there are no other people, and a mount
 * is a body on the scene the sources cannot place.
 *
 * STATES
 *
 *   ground:  idle → travelling → arriving → idle
 *   fly:     idle → ascending → cruising → descending → landing → arriving → idle
 *   glide:   idle → gliding → idle   (T-3432: a jaunt's start, flown to on a clock)
 *
 * `travelling` follows the router's waypoints; `arriving` eases the look onto
 * the building (focusPoint) over half a second and then opens its card
 * (`onArrive`). A missing ground route stops with an explanation. Stalls
 * (no progress for 2 s, or blocked for 1 s) re-plan once, then stop in place.
 * Only an explicitly selected instant journey teleports the visitor.
 *
 * Contract (main.js): createTravel({ walker, intent, hud, settings, router, terrain,
 *   focusPoint, structurePosition, footprints?, frame, teleport, goToAnchor, setFly, onArrive })
 *   -> { get mode, setMode(id), applyPace(), setHeadBob(bool), go(target) -> bool, stop(reason),
 *        update(dt, intent), afterWalk(intent, dt), get state, simulate(seconds, dt), router }
 *
 * `setFly` is the HUD's setter, never `walker.setFlying` directly: intent.flying
 * is the one master and a walker flipped behind its back is reverted on the next
 * frame (see main.js goTo()).
 */

import { bearingToYaw, yawToBearing } from './angles.js';

const DEG = Math.PI / 180;
const TAU = Math.PI * 2;

/**
 * The paces. hud.js reads `label`, `speed`, `sprint` and `hint` to paint the
 * pace chip and the Travel note; the rest is this controller's. `walk` has no
 * speed of its own — it is the Settings slider — and `instantly` is not a pace at
 * all, just the mode Go to has always had. Interface choices; see the header.
 */
export { PACES, paceSpeed } from './travel-settings.js';
import { PACES, paceSpeed, ARRIVAL_SETTLE_S, WALK, FLY } from './travel-settings.js';

/**
 * What a speed is CALLED, per pace — the word a slider shows as it moves. Metres
 * per second, first threshold that exceeds the value wins; the last entry has no
 * ceiling. These are names for a speed, not claims about 1835: a man cannot run
 * 20 mph and no horse has done 60, which is what the top entries say in as many
 * words.
 */
export const GAITS = {
  walk: [[0.9, 'stroll'], [1.8, 'walk'], [2.6, 'brisk walk'], [3.6, 'jog'], [5.5, 'run'],
    [7.5, 'sprint'], [Infinity, 'faster than any man']],
  // A wagon has no gait of its own — it rolls — so its words are the wagon's, not
  // the team's (the owner, 2026-09-05: "a wagon does not trot").
  wagon: [[0.9, 'crawl'], [1.8, 'walking pace'], [3.0, 'easy roll'], [4.5, 'steady roll'], [7, 'brisk pace'],
    [11, 'rattling along'], [Infinity, 'runaway']],
  horse: [[1.8, 'walk'], [3.0, 'jog'], [4.5, 'trot'], [7.5, 'canter'], [12.5, 'gallop'],
    [20, 'racing gallop'], [Infinity, 'beyond any horse']],
};
// Running is on foot, so it shares the walk's words (T-2651).
GAITS.run = GAITS.walk;

/** `gaitName('horse', 8.1)` → 'gallop'. Unknown pace or value → ''. */
export function gaitName(pace, metresPerSecond) {
  const table = GAITS[pace];
  const v = Number(metresPerSecond);
  if (!table || !Number.isFinite(v)) return '';
  for (const [ceiling, name] of table) if (v < ceiling) return name;
  return table[table.length - 1][1];
}


/** The paces that ride along the ground and take the router's route. */
const GROUND = new Set(['walk', 'run', 'wagon', 'horse']);

const LOOK_EPS = 0.002;        // radians/frame of the visitor's own look that ends a ride
const GRACE_S = 0.25;          // look deltas ignored this long after go() (a settling mouse)
const STALL_WINDOW_S = 2;      // no progress for this long …
const STALL_PROGRESS_M = 0.25; // … means less than this much closer
const BLOCKED_S = 1;           // or the walker refusing the step this long
const ARRIVE_TURN_S = ARRIVAL_SETTLE_S; // easing the look onto the building
const BANNER_INTERVAL_S = 0.25; // ≤ 4 Hz repaints of the distance
const GLIDE_TAN = Math.tan(18 * DEG); // descend once horizontal ≤ altitude / tan 18°
const LAND_HORIZ_M = 2.5;
const LAND_ALT_M = 4;
const GATE_OPEN_M = 6;         // T-3405: a walking ride opens a shut gate from this far …
const GATE_WAIT_M = 2.5;       // … and waits this far short of it until the leaves are still
const DEFAULT_RADIUS_M = 6;    // half a footprint diagonal when no footprint is known
const BOB_DECAY_M_PER_S = 0.35; // the gait dies within 0.3 s of stopping

/**
 * T-3432 (owner, 2026-11-06: "instead of jumping right into them, can you fly to the start
 * instead as long as it's like maybe 5-10 seconds max"). A glide is a flight on a clock, not
 * a steered ride: it takes `glideSeconds(d)` of wall time whatever the frame rate (a steered
 * flight across 1904 at 14 m/s is over a minute, and under a software renderer far longer),
 * climbs off the ground before it moves, looks along its way, and settles onto exactly the
 * pose it was given. 3.5 s for a hop, 8 s for the far side of town, never more.
 */
export const GLIDE_MAX_S = 8;
export const GLIDE_MIN_M = 8;   // nearer than this, there is nothing to fly
export function glideSeconds(d) {
  return Number.isFinite(d) && d >= GLIDE_MIN_M ? clamp(3 + d / 300, 3.5, GLIDE_MAX_S) : 0;
}
const smoother = (x) => x * x * x * (x * (x * 6 - 15) + 10);
const lerp = (a, b, t) => a + (b - a) * t;
const lerpAngle = (a, b, t) => a + wrapPi(b - a) * t;
/** Where a glide is `t` (0..1) of the way: { e, n, altitude, yaw, pitch }. Pure. */
export function glidePose(from, to, t) {
  const k = clamp(t, 0, 1), d = Math.hypot(to.e - from.e, to.n - from.n);
  // Up before along, down after: the eye leaves the ground before it crosses anything.
  const u = smoother(clamp((k - 0.1) / 0.8, 0, 1));
  const top = Math.max(from.altitude, to.altitude);
  const arc = d < 30 ? 0 : Math.max(0, clamp(0.16 * d, 18, 90) - top);
  const bump = k > 0 && k < 1 ? Math.pow(Math.sin(Math.PI * k), 0.6) : 0;
  const altitude = lerp(from.altitude, to.altitude, smoother(k)) + arc * bump;
  let yaw, pitch;
  if (d < 30) { yaw = lerpAngle(from.yaw, to.yaw, smoother(k)); pitch = lerp(from.pitch, to.pitch, smoother(k)); }
  else {
    // Turn onto the way, look a little down over the town, then onto the framing.
    const heading = bearingToYaw(Math.atan2(to.e - from.e, to.n - from.n) / DEG);
    const a = smoother(clamp(k / 0.25, 0, 1)), b = smoother(clamp((k - 0.62) / 0.38, 0, 1));
    yaw = lerpAngle(lerpAngle(from.yaw, heading, a), to.yaw, b);
    pitch = lerp(lerp(from.pitch, -14 * DEG, a), to.pitch, b);
  }
  return { e: lerp(from.e, to.e, u), n: lerp(from.n, to.n, u), altitude, yaw, pitch };
}

function wrapPi(a) { return Math.atan2(Math.sin(a), Math.cos(a)); }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

export function createTravel({
  walker, intent, hud, settings = {}, router = null, terrain = null,
  focusPoint, structurePosition, footprints = null, standFor = null,
  frame, teleport, goToAnchor, setFly, onArrive,
  // T-3405: the gates a ground route passes through, `along(points)` -> [{ at: [e, n],
  // blocks(), open() }] (main.js, from fort-gates.js); a walking ride opens each shut one
  // as it comes up to it and waits while it swings. `tickWorld(dt)` moves the world's
  // own clocks (the swing) inside simulate(), which has no frame loop to do it.
  gates = null, tickWorld = null,
} = {}) {
  let mode = 'instantly';
  let headBob = settings.headBob !== false;
  let phase = 'idle';
  /** The ride in progress, null when idle. See newRide() for the shape. */
  let ride = null;
  /** True between an update() that steered and the afterWalk() that cleaned up. */
  let wrote = false;
  let bobPhase = 0;
  const reduceMotion = typeof matchMedia === 'function'
    ? matchMedia('(prefers-reduced-motion: reduce)') : null;

  // ---- pace ---------------------------------------------------------------

  /** The pace in force: the ride's while riding along the ground, else the setting. */
  function activePace() {
    if (ride && GROUND.has(ride.mode)) return PACES[ride.mode];
    return PACES[settings.pace] ?? PACES.walk;
  }

  /**
   * Compose the slider values and the pace into WALK in one place, so a wagon
   * seat and a raised eye-height slider add rather than overwrite each other.
   * The eye is resettled at once: a slider you have to walk away from before it
   * does anything reads as broken.
   */
  function applyPace() {
    const pace = activePace();
    const base = paceSpeed(pace, settings) ?? PACES.walk.defaultSpeed;
    WALK.speed = base;
    WALK.sprintSpeed = Math.min(base * (pace.sprintFactor ?? 1), pace.maxSpeed ?? Infinity);
    WALK.eyeHeight = (Number.isFinite(settings.eyeHeight) ? settings.eyeHeight : 1.68)
      + (pace.eyeOffset ?? 0);
    walker?.resettle?.();
  }

  /**
   * The rider's head with the horse's gait — a camera offset the walker adds in
   * apply() only, so eyeY stays the honest eye height. Computed BEFORE the walker
   * runs, from last frame's speed, so the walker's own apply() is the one camera
   * write of the frame. Gallop figures while Shift is held.
   */
  function updateBob(dt, intentNow) {
    const s = walker.state;
    const pace = activePace();
    const gait = pace.bob;
    const allowed = headBob && settings.headBob !== false && !reduceMotion?.matches;
    const on = !!gait && allowed && !s.flying && s.speed > 0.05;
    if (on) {
      const sprint = !!intentNow.sprint && !ride;
      // The beat follows the speed the slider set: a canter's two strides a second
      // at 6.5 m/s, faster at a racing gallop, slower at a jog — within reason.
      const tempo = clamp(s.speed / (gait.atSpeed ?? 6.5), 0.6, 1.8);
      const hz = (sprint ? gait.sprintHz : gait.hz) * tempo;
      const amp = sprint ? gait.sprintAmp : gait.amp;
      const target = sprint ? WALK.sprintSpeed : WALK.speed;
      bobPhase = (bobPhase + TAU * hz * dt) % TAU;
      s.bob = amp * Math.sin(bobPhase) * Math.min(1, s.speed / Math.max(target, 0.01));
      return;
    }
    if (s.bob === 0) return;
    if (!allowed) { s.bob = 0; bobPhase = 0; return; }
    const step = BOB_DECAY_M_PER_S * dt;
    s.bob = Math.abs(s.bob) <= step ? 0 : s.bob - Math.sign(s.bob) * step;
    if (s.bob === 0) bobPhase = 0;
  }

  // ---- destinations --------------------------------------------------------

  function isAerial(target) { return typeof target?.altitude_m === 'number'; }
  function ownPoint(target) {
    const e = target.local_e ?? target.e;
    const n = target.local_n ?? target.n;
    return Number.isFinite(e) && Number.isFinite(n) ? { e, n } : null;
  }

  /** Half the footprint's bbox diagonal, or the default when footprints are not passed. */
  function radiusOf(id) {
    const fp = footprints?.find?.((f) => f.id === id);
    if (!fp?.pts?.length) return DEFAULT_RADIUS_M;
    let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
    for (const [e, n] of fp.pts) {
      if (e < e0) e0 = e; if (e > e1) e1 = e;
      if (n < n0) n0 = n; if (n > n1) n1 = n;
    }
    return Math.hypot(e1 - e0, n1 - n0) / 2;
  }

  /** Where the ride ends: beside a building, or at the point itself. */
  function destinationOf(target, { card = true, mode: arrivalMode = mode } = {}) {
    if (target.kind === 'structure') {
      const centre = structurePosition?.(target.id);
      if (!centre) return null;
      // Where a ride ends is where the building is framed whole (T-0824): the
      // same point an instant Go to stands you at, so the two cannot disagree.
      const framed = standFor?.(target.id, { mode: arrivalMode, card });
      if (framed && Number.isFinite(framed.e) && Number.isFinite(framed.n)) return framed;
      const off = router?.standOff?.(target.id, centre, radiusOf(target.id));
      return off && Number.isFinite(off.e) && Number.isFinite(off.n) ? off : centre;
    }
    return ownPoint(target);
  }

  /** Today's behaviour, and the fallback for every ride that cannot happen. */
  function arrived(ok, callbacks) {
    if (ok) callbacks?.onArrive?.(callbacks.token);
    return ok;
  }
  function goInstantly(target, callbacks) {
    const to = destinationOf(target, { card: !callbacks });
    if (to) reportRoute(target, [[to.e, to.n]], callbacks);
    if (target.kind === 'anchor') return arrived(goToAnchor?.(target.id) ?? false, callbacks);
    setFly?.(false);
    if (target.kind === 'structure') {
      const ok = frame?.(target.id, { mode, card: !callbacks }) ?? false;
      if (ok && !callbacks) onArrive?.(target.id);
      return arrived(ok, callbacks);
    }
    const p = ownPoint(target);
    if (target.kind === 'intersection' && p) {
      teleport?.({ local_e: p.e, local_n: p.n, yaw_deg: target.yaw_deg ?? 0 });
      return arrived(true, callbacks);
    }
    return false;
  }

  function reportRoute(target, points, callbacks) {
    const s = walker.state;
    callbacks?.onRoute?.({ ...callbacks.token, target, points: [[s.e, s.n], ...points] });
  }
  function newRide(target, to, points, rideMode, callbacks) {
    const s = walker.state;
    reportRoute(target, points, callbacks);
    return {
      mode: rideMode,
      kind: target.kind,
      id: target.id,
      person: target.person ?? null,
      dest: target.label ?? target.name ?? target.id,
      target,
      callbacks,
      to,
      points,
      index: 0,
      from: { e: s.e, n: s.n },
      sinceGo: 0,
      expectedFlying: rideMode === 'fly',
      replans: 0,
      progressT: 0,
      progressRef: Infinity,
      blockedT: 0,
      bannerT: 0,
      cruise: null,
      maxAlt: s.altitude,
      arrive: null,
      done: false,
      startedAt: Date.now(),
    };
  }

  // ---- distances -----------------------------------------------------------

  function remaining() {
    if (!ride) return null;
    const s = walker.state;
    if (ride.mode === 'fly') return Math.hypot(ride.to.e - s.e, ride.to.n - s.n);
    let d = 0;
    let pe = s.e, pn = s.n;
    for (let i = ride.index; i < ride.points.length; i++) {
      const [e, n] = ride.points[i];
      d += Math.hypot(e - pe, n - pn);
      pe = e; pn = n;
    }
    return d;
  }

  function paintBanner() {
    if (!ride) return;
    ride.dist_m = remaining();
    hud?.travelBanner?.({ verb: PACES[ride.mode]?.verb ?? 'Going to', dest: ride.dest, dist_m: ride.dist_m });
  }

  function finish() {
    phase = 'idle';
    ride = null;
    hud?.travelBanner?.(null);
    applyPace();   // back to the visitor's own pace and seat
  }

  // ---- the state machine ---------------------------------------------------

  function visitorInput(intentNow, r) {
    if (intentNow.moving || intentNow.sprint || intentNow.interact) return true;
    if (intentNow.flying !== r.expectedFlying) return true;
    if (r.sinceGo <= GRACE_S) return false;
    return Math.abs(intentNow.yawDelta) > LOOK_EPS || Math.abs(intentNow.pitchDelta) > LOOK_EPS;
  }

  /** Turn toward (e, n) at most `rateDeg`°/s; returns the remaining yaw error. */
  function turnToward(intentNow, e, n, rateDeg, dt) {
    const s = walker.state;
    const de = e - s.e, dn = n - s.n;
    if (Math.hypot(de, dn) < 1e-4) { intentNow.yawDelta = 0; return 0; }
    const want = bearingToYaw(Math.atan2(de, dn) / DEG);
    const diff = wrapPi(want - s.yaw);
    const cap = rateDeg * DEG * dt;
    intentNow.yawDelta = clamp(diff, -cap, cap);
    return diff;
  }

  function pitchTo(intentNow, target, dt, rateDeg = 70) {
    const cap = rateDeg * DEG * dt;
    intentNow.pitchDelta = clamp(target - walker.state.pitch, -cap, cap);
  }

  function advanceWaypoints(r) {
    const s = walker.state;
    while (r.index < r.points.length) {
      const [we, wn] = r.points[r.index];
      const d = Math.hypot(we - s.e, wn - s.n);
      // Reach the corner before turning. The previous speed-sized radius and
      // infinite 'passed' plane skipped corners while metres to their side.
      if (d < 0.08) r.index++;
      else break;
    }
  }

  function stallWatch(r, dt, metric, blockedCounts) {
    r.blockedT = blockedCounts && walker.state.blocked ? r.blockedT + dt : 0;
    r.progressT += dt;
    let stalled = r.blockedT >= BLOCKED_S;
    if (r.progressT >= STALL_WINDOW_S) {
      if (r.progressRef - metric < STALL_PROGRESS_M) stalled = true;
      r.progressT = 0;
      r.progressRef = metric;
    }
    if (stalled) onStall(r);
  }

  function onStall(r) {
    r.blockedT = 0;
    r.progressT = 0;
    if (r.replans < 1 && GROUND.has(r.mode)) {
      r.replans++;
      const s = walker.state;
      const route = router?.plan?.({ e: s.e, n: s.n }, r.to, { mode: r.mode }) ?? null;
      if (route?.points?.length) {
        reportRoute(r.target, route.points, r.callbacks);
        r.points = route.points;
        r.gates = gates?.along?.([[s.e, s.n], ...route.points]) ?? [];
        r.index = 0;
        r.from = { e: s.e, n: s.n };
        r.progressRef = remaining();
        return;
      }
    }
    const callbacks = r.callbacks;
    finish();
    callbacks?.onStop?.({ ...callbacks.token, reason: 'unreachable' });
    hud?.say?.('The route is blocked. Stopped here — choose another destination or Go instantly.');
  }

  function beginArrive(r) {
    phase = 'arriving';
    const s = walker.state;
    let yaw = null;
    let point = null;
    let yawOff = 0;
    let pitchOff = 0;
    if (r.kind === 'structure') {
      const f = standFor?.(r.id, { mode: r.mode, card: !r.callbacks }) ?? r.to;
      point = f.aim ?? r.to.aim ?? focusPoint?.(r.id) ?? null;
      // The framing rule's offsets (T-0824): the card opens on arrival and the
      // building should sit centred in the part of the screen it leaves free.
      yawOff = (f?.yawOffsetDeg ?? 0) * DEG;
      pitchOff = (f?.pitchOffsetDeg ?? 0) * DEG;
    } else if (Number.isFinite(r.target?.yaw_deg)) yaw = bearingToYaw(r.target.yaw_deg);
    r.arrive = { point, yaw, yawOff, pitchOff, t: ARRIVE_TURN_S, startYaw: s.yaw };
  }

  function steerGround(intentNow, dt) {
    const r = ride;
    advanceWaypoints(r);
    if (r.index >= r.points.length) { beginArrive(r); steerArrive(intentNow, dt); return; }
    const [we, wn] = r.points[r.index];
    const diff = turnToward(intentNow, we, wn, PACES[r.mode].turnRate, dt);
    const s = walker.state;
    const distance = Math.hypot(we - s.e, wn - s.n);
    // Turn on the spot, then take no more than the distance left on this leg.
    // This keeps even a fast horse on the planned sidewalk/street corner.
    intentNow.forward = Math.abs(diff) < 0.01 ? Math.min(1, distance / Math.max(WALK.speed * dt, 0.001)) : 0;
    // T-3405: a shut gate on the way is opened from GATE_OPEN_M off, and the ride waits
    // GATE_WAIT_M short of it while the leaves swing. Waiting is not a stall.
    if (r.gates?.length && gateHold(r, s)) {
      intentNow.forward = 0; intentNow.strafe = 0; intentNow.rise = 0; intentNow.sprint = false;
      pitchTo(intentNow, 0, dt);
      r.progressT = 0; r.progressRef = remaining(); r.blockedT = 0;
      return;
    }
    intentNow.strafe = 0;
    intentNow.rise = 0;
    intentNow.sprint = false;
    pitchTo(intentNow, 0, dt);
    if (intentNow.forward > 0) stallWatch(r, dt, remaining(), true);
    else { r.progressT = 0; r.progressRef = remaining(); }
  }

  /** True while a gate the ride is about to pass through is shut or still swinging. */
  function gateHold(r, s) {
    let hold = false;
    for (const g of r.gates) {
      if (!g.blocks()) continue;
      const d = Math.hypot(g.at[0] - s.e, g.at[1] - s.n);
      if (d <= GATE_OPEN_M) g.open();
      if (d <= GATE_WAIT_M) hold = true;
    }
    return hold;
  }

  function steerFlight(intentNow, dt) {
    const r = ride;
    const s = walker.state;
    const de = r.to.e - s.e, dn = r.to.n - s.n;
    const horiz = Math.hypot(de, dn);
    const alt = s.altitude;
    if (alt > r.maxAlt) r.maxAlt = alt;
    const gain = FLY.altitudeGain(alt);
    const hSpeed = FLY.speed * gain;
    const vSpeed = FLY.riseSpeed * gain;

    turnToward(intentNow, r.to.e, r.to.n, PACES.fly.turnRate, dt);
    intentNow.strafe = 0;
    intentNow.sprint = false;

    // T-3405: a flight to a raised view climbs to its height, slows over it and settles
    // into the view itself; it never comes down.
    if (r.aerial && phase !== 'ascending') {
      intentNow.forward = clamp(horiz / 12, 0.12, 1);
      intentNow.rise = clamp((r.cruise - alt) / 3, -1, 1);
      pitchTo(intentNow, 0, dt);
      if (horiz <= LAND_HORIZ_M && Math.abs(r.cruise - alt) < 2) { goToAnchor?.(r.id); r.done = true; return; }
      stallWatch(r, dt, horiz + Math.abs(r.cruise - alt), false);
      return;
    }
    if (phase === 'ascending') {
      intentNow.forward = horiz > 30 ? 0.5 : 0.15;
      intentNow.rise = 1;
      pitchTo(intentNow, 12 * DEG, dt);
      const inCone = !r.aerial && horiz <= alt / GLIDE_TAN && alt >= r.cruise * 0.5;
      if (alt >= r.cruise - 0.5 || inCone) phase = inCone ? 'descending' : 'cruising';
    } else if (phase === 'cruising') {
      intentNow.forward = 1;
      intentNow.rise = clamp((r.cruise - alt) / 3, -1, 1);
      pitchTo(intentNow, 0, dt);
      if (horiz <= alt / GLIDE_TAN) phase = 'descending';
    } else if (phase === 'descending') {
      // Nose toward the stand-off point, slow as it nears, and meter the descent so
      // the eye is ~2 m up when the horizontal distance runs out.
      pitchTo(intentNow, clamp(-Math.atan2(alt, Math.max(horiz, 1)), -35 * DEG, 0), dt);
      intentNow.forward = clamp(horiz / 12, 0.12, 1);
      const groundSpeed = Math.max(hSpeed * intentNow.forward * Math.cos(s.pitch), 0.1);
      const eta = Math.max(horiz, 0.5) / groundSpeed;
      const needed = -(alt - 1.8) / eta;
      const fromPitch = hSpeed * intentNow.forward * Math.sin(s.pitch);
      intentNow.rise = clamp((needed - fromPitch) / vSpeed, -1, 1);
      if (horiz <= LAND_HORIZ_M) phase = 'landing';
    } else if (phase === 'landing') {
      intentNow.forward = horiz > 0.6 ? clamp(horiz / 6, 0.05, 0.3) : 0;
      intentNow.rise = -1;
      pitchTo(intentNow, -30 * DEG, dt);
      if (horiz > 6) phase = 'descending';
      else if (alt < LAND_ALT_M && horiz <= LAND_HORIZ_M + 1) {
        setFly?.(false);
        r.expectedFlying = false;
        applyPace();
        beginArrive(r);
      }
    }
    stallWatch(r, dt, horiz + (phase === 'landing' ? alt : 0), false);
  }

  /** Ease yaw and pitch onto the building over ≤ ARRIVE_TURN_S, then finish in afterWalk. */
  function steerArrive(intentNow, dt) {
    const r = ride;
    const s = walker.state;
    intentNow.forward = 0;
    intentNow.strafe = 0;
    intentNow.rise = 0;
    intentNow.sprint = false;
    let yawT = s.yaw;
    let pitchT = 0;
    if (r.arrive.point) {
      const p = r.arrive.point;
      const de = p.x - s.e, dn = -p.z - s.n;
      // A larger compass bearing is a smaller yaw (yaw grows counter-clockwise).
      yawT = bearingToYaw(Math.atan2(de, dn) / DEG + (r.arrive.yawOff ?? 0) / DEG);
      pitchT = Math.atan2(p.y - s.eyeY, Math.max(Math.hypot(de, dn), 0.1)) + (r.arrive.pitchOff ?? 0);
    } else if (r.arrive.yaw !== null) {
      yawT = r.arrive.yaw;
    }
    const k = Math.min(1, dt / Math.max(r.arrive.t, 1e-6));
    intentNow.yawDelta = wrapPi(yawT - s.yaw) * k;
    intentNow.pitchDelta = (pitchT - s.pitch) * k;
    r.arrive.t -= dt;
    if (r.arrive.t <= 1e-6) r.done = true;
  }

  function complete() {
    const { kind, id, dest, callbacks } = ride;
    finish();
    if (callbacks) callbacks.onArrive?.(callbacks.token);
    else if (kind === 'structure') onArrive?.(id);
    else hud?.say?.(`Here — ${dest}`);
  }

  // ---- public --------------------------------------------------------------

  function stop(reason = 'button') {
    if (phase === 'idle') return;
    // A glide stopped for any reason is landed, never left hanging in the air.
    if (phase === 'gliding') landGlide(ride);
    const callbacks = ride?.callbacks;
    finish();
    callbacks?.onStop?.({ ...callbacks.token, reason });
    if (reason === 'button' || reason === 'input') hud?.say?.('Stopped');
  }

  function go(target, callbacks) {
    if (!target?.kind) return false;
    if (phase !== 'idle') stop('replaced');
    // Aerial viewpoints are a jump on the ground: a ride to the ground under a bird's-eye
    // view is not the view. So is any anchor Go to did not hand coordinates for. A flight
    // goes there (T-3405): it climbs to the view's height and settles into it.
    if (target.kind === 'anchor' && ((isAerial(target) && mode !== 'fly') || mode === 'instantly' || !ownPoint(target))) {
      return goInstantly(target, callbacks);
    }
    if (mode === 'instantly') return goInstantly(target, callbacks);
    const to = destinationOf(target, { card: !callbacks });
    if (!to) return false;

    if (mode === 'fly') {
      const s = walker.state;
      const d = Math.hypot(to.e - s.e, to.n - s.n);
      setFly?.(true);
      ride = newRide(target, to, [[to.e, to.n]], 'fly', callbacks);
      ride.cruise = PACES.fly.cruise(d);
      if (target.kind === 'anchor' && isAerial(target)) { ride.aerial = true; ride.cruise = target.altitude_m; }
      ride.progressRef = d;
      phase = 'ascending';
      paintBanner();
      return true;
    }

    // A ground ride. Down to earth first: the route is walked, not flown.
    if (walker.state.flying || intent.flying) setFly?.(false);
    const s = walker.state;
    const route = router?.plan?.({ e: s.e, n: s.n }, to, { mode }) ?? null;
    if (!route?.points?.length) {
      callbacks?.onStop?.({ ...callbacks.token, reason: 'unreachable' });
      hud?.say?.('No safe street route was found. Choose another destination or Go instantly.');
      return false;
    }
    ride = newRide(target, to, route.points, mode, callbacks);
    ride.gates = gates?.along?.([[s.e, s.n], ...route.points]) ?? [];
    ride.progressRef = remaining();
    phase = 'travelling';
    applyPace();   // the ride's pace and seat, restored by finish()
    paintBanner();
    return true;
  }

  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
  function poseGlide(p) {
    teleport?.({ local_e: p.e, local_n: p.n, altitude_m: p.altitude,
      yaw_deg: yawToBearing(p.yaw), pitch_deg: p.pitch / DEG });
  }
  function landGlide(r) {
    const to = r?.glide?.to;
    if (!to) return;
    setFly?.(false);
    teleport?.({ local_e: to.e, local_n: to.n, yaw_deg: yawToBearing(to.yaw), pitch_deg: to.pitch / DEG });
  }
  /**
   * T-3432: fly from `from` to `to` ({ e, n, altitude, yaw, pitch }: the eye's height above
   * the ground and the walker's own angles) in glideSeconds() of wall time, then land on
   * `to` exactly. Returns false, and moves nothing, when there is nothing to fly or the
   * visitor asked for reduced motion; the caller then simply stands at `to`.
   */
  function glide(from, to, callbacks = null, { label = null } = {}) {
    const d = Math.hypot(to.e - from.e, to.n - from.n);
    const seconds = glideSeconds(d);
    if (!(seconds > 0) || reduceMotion?.matches) return false;
    if (phase !== 'idle') stop('replaced');
    setFly?.(true);
    ride = newRide({ kind: 'glide', label: label ?? 'the start' }, { e: to.e, n: to.n }, [[to.e, to.n]], 'fly', callbacks);
    ride.glide = { from, to, seconds, elapsed: 0, t0: now() };
    phase = 'gliding';
    poseGlide(glidePose(from, to, 0));
    paintBanner();
    return true;
  }

  function update(dt, intentNow = intent) {
    updateBob(dt, intentNow);
    if (phase === 'idle' || !ride) return;
    ride.sinceGo += dt;
    if (phase === 'gliding') {
      // A glide is a cut, not a ride the visitor can stop halfway up: their first move
      // lands it, and their input flows on from the start.
      if (visitorInput(intentNow, ride)) { landGlide(ride); complete(); }
      return;
    }
    if (visitorInput(intentNow, ride)) { stop('input'); return; }
    wrote = true;
    if (phase === 'travelling') steerGround(intentNow, dt);
    else if (phase === 'arriving') steerArrive(intentNow, dt);
    else steerFlight(intentNow, dt);
  }

  function afterWalk(intentNow = intent, dt = 0) {
    if (wrote) {
      // Only what this controller wrote: the visitor's own writes end the ride
      // before update() steers, so nothing of theirs is standing here.
      intentNow.forward = 0;
      intentNow.strafe = 0;
      intentNow.rise = 0;
      intentNow.sprint = false;
      wrote = false;
    }
    if (!ride) return;
    if (phase === 'gliding') {
      // After the walker, so the pose written here is the one this frame draws. The
      // clock is the larger of the frames' dt and the wall's: simulate() has no wall.
      const g = ride.glide;
      g.elapsed = Math.max(g.elapsed + dt, (now() - g.t0) / 1000);
      if (g.elapsed >= g.seconds) { landGlide(ride); complete(); return; }
      poseGlide(glidePose(g.from, g.to, g.elapsed / g.seconds));
    }
    if (ride.done) { complete(); return; }
    ride.bannerT += dt;
    if (ride.bannerT >= BANNER_INTERVAL_S) { ride.bannerT = 0; paintBanner(); }
  }

  /**
   * Harness only: the same code path as tick(), run synchronously for `seconds`
   * of simulated time (or until the ride ends). Zeroes the intent first so a
   * held key in the test page is not read as the visitor cancelling.
   */
  function simulate(seconds, dt = 1 / 30) {
    intent.clear();
    const s = walker.state;
    const samples = [[s.e, s.n]];
    let t = 0;
    let sinceSample = 0;
    let maxAlt = s.altitude;
    const steps = Math.ceil(Math.max(0, seconds) / dt);
    for (let i = 0; i < steps && phase !== 'idle'; i++) {
      tickWorld?.(dt);
      update(dt, intent);
      walker.update(dt, intent);
      afterWalk(intent, dt);
      t += dt;
      sinceSample += dt;
      if (s.altitude > maxAlt) maxAlt = s.altitude;
      if (sinceSample >= 0.5) { samples.push([s.e, s.n]); sinceSample = 0; }
    }
    return { phase, e: s.e, n: s.n, altitude: s.altitude, maxAltitude: maxAlt, samples, seconds: t };
  }

  return {
    get mode() { return mode; },
    setMode(id) { if (id in PACES) mode = id; return mode; },
    applyPace,
    setHeadBob(on) { headBob = !!on; if (!headBob) walker.state.bob = 0; return headBob; },
    go,
    glide,
    stop,
    update,
    afterWalk,
    simulate,
    router,
    destinationOf,
    /** T-2654: the waypoints a ride under way has still to pass, for the Navigator's Map. */
    routeAhead() { return ride ? ride.points.slice(ride.index).map(([e, n]) => [e, n]) : []; },
    get state() {
      return {
        phase,
        mode,
        dest: ride?.dest ?? null,
        dest_id: ride?.id ?? null,
        person: ride?.person ?? null,
        dist_m: ride ? remaining() : null,
        remaining_points: ride ? Math.max(0, ride.points.length - ride.index) : 0,
        started_at: ride?.startedAt ?? null,
        flying: !!walker?.state?.flying,
        bob: walker?.state?.bob ?? 0,
      };
    },
  };
}
