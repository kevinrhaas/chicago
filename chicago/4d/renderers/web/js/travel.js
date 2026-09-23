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
 * A wagon at 3.6 m/s, a horse at 6.5 m/s cantering and 11 m/s galloping, a
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
 *
 * `travelling` follows the router's waypoints; `arriving` eases the look onto
 * the building (focusPoint) over half a second and then opens its card
 * (`onArrive`). A null route — the router found no walkable way, or has not been
 * built — falls back to the instant behaviour with a message, so the visitor is
 * never left standing. Stalls (no progress for 2 s, or blocked for 1 s) re-plan
 * once from where the visitor stands and then fall back the same way.
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

import { WALK, FLY } from './walker.js';
import { bearingToYaw } from './terrain.js';

const DEG = Math.PI / 180;
const TAU = Math.PI * 2;

/**
 * The paces. hud.js reads `label`, `speed`, `sprint` and `hint` to paint the
 * pace chip and the Travel note; the rest is this controller's. `walk` has no
 * speed of its own — it is the Settings slider — and `instantly` is not a pace at
 * all, just the mode Go to has always had. Interface choices; see the header.
 */
export const PACES = {
  instantly: { label: 'Instantly', hint: 'straight there, as before' },
  // Each ground pace has its own slider (T-0823): `settingKey` names the stored
  // value, `defaultSpeed` is what a fresh visitor gets, `maxSpeed` is the slider's
  // ceiling — 20, 30 and 60 mph, the owner's figures — and `sprintFactor` is what
  // Shift does to it (a run on foot, nothing on a wagon, a gallop on a horse),
  // capped at the ceiling. The gait names a slider shows are in GAITS below.
  walk: {
    label: 'Walk', verb: 'Walking to', eyeOffset: 0, turnRate: 150,
    settingKey: 'speed', defaultSpeed: 1.45, maxSpeed: 8.94, sprintFactor: 2.28,
    hint: 'your own two feet',
  },
  wagon: {
    label: 'Wagon', verb: 'Driving to', eyeOffset: 0.5, turnRate: 70,
    settingKey: 'wagonSpeed', defaultSpeed: 3.6, maxSpeed: 13.41, sprintFactor: 1,
    hint: 'a light wagon',
  },
  horse: {
    label: 'Horse', verb: 'Riding to', eyeOffset: 0.75, turnRate: 90,
    settingKey: 'horseSpeed', defaultSpeed: 6.5, maxSpeed: 26.82, sprintFactor: 1.7,
    // The gait figures are a canter's (2 strides a second at 6.5 m/s); updateBob
    // scales the beat with the speed the slider actually set.
    bob: { hz: 2.0, amp: 0.06, sprintHz: 1.6, sprintAmp: 0.09, atSpeed: 6.5 },
    hint: 'in the saddle; Shift to gallop',
  },
  fly: {
    label: 'Fly', verb: 'Flying to', turnRate: 120,
    /** Cruise height in metres for a trip of `d` metres: low for a hop, higher
     *  for a crossing so the whole route is in view. */
    cruise: (d) => Math.min(80, Math.max(20, 12 + 0.15 * d)),
    hint: 'up, across and down to the door',
  },
};

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

/** `gaitName('horse', 8.1)` → 'gallop'. Unknown pace or value → ''. */
export function gaitName(pace, metresPerSecond) {
  const table = GAITS[pace];
  const v = Number(metresPerSecond);
  if (!table || !Number.isFinite(v)) return '';
  for (const [ceiling, name] of table) if (v < ceiling) return name;
  return table[table.length - 1][1];
}

/** The slider value for a pace: the stored setting, clamped to the pace's range. */
export function paceSpeed(pace, settings = {}) {
  const p = typeof pace === 'string' ? PACES[pace] : pace;
  if (!p?.settingKey) return null;
  const stored = Number(settings[p.settingKey]);
  const base = Number.isFinite(stored) ? stored : p.defaultSpeed;
  return clamp(base, 0.5, p.maxSpeed);
}

/** The paces that ride along the ground and take the router's route. */
const GROUND = new Set(['walk', 'wagon', 'horse']);

const WAYPOINT_M = 1.2;        // a waypoint counts as reached inside this
const LOOK_EPS = 0.002;        // radians/frame of the visitor's own look that ends a ride
const GRACE_S = 0.25;          // look deltas ignored this long after go() (a settling mouse)
const STALL_WINDOW_S = 2;      // no progress for this long …
const STALL_PROGRESS_M = 0.25; // … means less than this much closer
const BLOCKED_S = 1;           // or the walker refusing the step this long
const ARRIVE_TURN_S = 0.5;     // easing the look onto the building
const BANNER_INTERVAL_S = 0.25; // ≤ 4 Hz repaints of the distance
const GLIDE_TAN = Math.tan(18 * DEG); // descend once horizontal ≤ altitude / tan 18°
const LAND_HORIZ_M = 2.5;
const LAND_ALT_M = 4;
const DEFAULT_RADIUS_M = 6;    // half a footprint diagonal when no footprint is known
const BOB_DECAY_M_PER_S = 0.35; // the gait dies within 0.3 s of stopping

function wrapPi(a) { return Math.atan2(Math.sin(a), Math.cos(a)); }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

export function createTravel({
  walker, intent, hud, settings = {}, router = null, terrain = null,
  focusPoint, structurePosition, footprints = null, standFor = null,
  frame, teleport, goToAnchor, setFly, onArrive,
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
    const base = paceSpeed(pace, settings) ?? 1.45;
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
  function destinationOf(target) {
    if (target.kind === 'structure') {
      const centre = structurePosition?.(target.id);
      if (!centre) return null;
      // Where a ride ends is where the building is framed whole (T-0824): the
      // same point an instant Go to stands you at, so the two cannot disagree.
      const framed = standFor?.(target.id);
      if (framed && Number.isFinite(framed.e) && Number.isFinite(framed.n)) return { e: framed.e, n: framed.n };
      const off = router?.standOff?.(target.id, centre, radiusOf(target.id));
      return off && Number.isFinite(off.e) && Number.isFinite(off.n) ? off : centre;
    }
    return ownPoint(target);
  }

  /** Today's behaviour, and the fallback for every ride that cannot happen. */
  function goInstantly(target) {
    if (target.kind === 'anchor') return goToAnchor?.(target.id) ?? false;
    setFly?.(false);
    if (target.kind === 'structure') {
      const ok = frame?.(target.id) ?? false;
      if (ok) onArrive?.(target.id);
      return ok;
    }
    const p = ownPoint(target);
    if (target.kind === 'intersection' && p) {
      teleport?.({ local_e: p.e, local_n: p.n, yaw_deg: target.yaw_deg ?? 0 });
      return true;
    }
    return false;
  }

  function newRide(target, to, points, rideMode) {
    const s = walker.state;
    return {
      mode: rideMode,
      kind: target.kind,
      id: target.id,
      person: target.person ?? null,
      dest: target.label ?? target.name ?? target.id,
      target,
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
    if (Math.hypot(de, dn) < 0.5) { intentNow.yawDelta = 0; return 0; }
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
      const prev = r.index > 0 ? r.points[r.index - 1] : [r.from.e, r.from.n];
      const d = Math.hypot(we - s.e, wn - s.n);
      // Past the plane through the waypoint perpendicular to its leg: the
      // walker overshot it, which at a gallop happens every few frames.
      const passed = (we - s.e) * (we - prev[0]) + (wn - s.n) * (wn - prev[1]) < 0;
      // A galloping ride covers a 1.2 m circle in a frame or two; the reach grows
      // with the speed so a fast ride does not overshoot and circle back.
      const reach = Math.max(WAYPOINT_M, walker.state.speed * 0.12);
      if (d < reach || passed) r.index++;
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
      const route = router?.plan?.({ e: s.e, n: s.n }, r.to) ?? null;
      if (route?.points?.length) {
        r.points = route.points;
        r.index = 0;
        r.from = { e: s.e, n: s.n };
        r.progressRef = remaining();
        return;
      }
    }
    const target = r.target;
    finish();
    goInstantly(target);
    hud?.say?.('Could not get through — went straight there');
  }

  function beginArrive(r) {
    phase = 'arriving';
    const s = walker.state;
    let yaw = null;
    let point = null;
    let yawOff = 0;
    let pitchOff = 0;
    if (r.kind === 'structure') {
      point = focusPoint?.(r.id) ?? null;
      // The framing rule's offsets (T-0824): the card opens on arrival and the
      // building should sit centred in the part of the screen it leaves free.
      const f = standFor?.(r.id);
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
    intentNow.forward = Math.abs(diff) < 60 * DEG ? 1 : 0.25;
    intentNow.strafe = 0;
    intentNow.rise = 0;
    intentNow.sprint = false;
    pitchTo(intentNow, 0, dt);
    stallWatch(r, dt, remaining(), true);
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

    if (phase === 'ascending') {
      intentNow.forward = horiz > 30 ? 0.5 : 0.15;
      intentNow.rise = 1;
      pitchTo(intentNow, 12 * DEG, dt);
      const inCone = horiz <= alt / GLIDE_TAN && alt >= r.cruise * 0.5;
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
    const { kind, id, dest } = ride;
    finish();
    if (kind === 'structure') onArrive?.(id);
    else hud?.say?.(`Here — ${dest}`);
  }

  // ---- public --------------------------------------------------------------

  function stop(reason = 'button') {
    if (phase === 'idle') return;
    finish();
    if (reason === 'button' || reason === 'input') hud?.say?.('Stopped');
  }

  function go(target) {
    if (!target?.kind) return false;
    if (phase !== 'idle') stop('replaced');
    // Aerial viewpoints are always a jump: a ride to the ground under a bird's-eye
    // view is not the view. So is any anchor Go to did not hand coordinates for.
    if (target.kind === 'anchor' && (isAerial(target) || mode === 'instantly' || !ownPoint(target))) {
      return goToAnchor?.(target.id) ?? false;
    }
    if (mode === 'instantly') return goInstantly(target);
    const to = destinationOf(target);
    if (!to) return false;

    if (mode === 'fly') {
      const s = walker.state;
      const d = Math.hypot(to.e - s.e, to.n - s.n);
      setFly?.(true);
      ride = newRide(target, to, [[to.e, to.n]], 'fly');
      ride.cruise = PACES.fly.cruise(d);
      ride.progressRef = d;
      phase = 'ascending';
      paintBanner();
      return true;
    }

    // A ground ride. Down to earth first: the route is walked, not flown.
    if (walker.state.flying || intent.flying) setFly?.(false);
    const s = walker.state;
    const route = router?.plan?.({ e: s.e, n: s.n }, to) ?? null;
    if (!route?.points?.length) {
      const ok = goInstantly(target);
      hud?.say?.('No walkable route was found — went straight there');
      return ok;
    }
    ride = newRide(target, to, route.points, mode);
    ride.progressRef = remaining();
    phase = 'travelling';
    applyPace();   // the ride's pace and seat, restored by finish()
    paintBanner();
    return true;
  }

  function update(dt, intentNow = intent) {
    updateBob(dt, intentNow);
    if (phase === 'idle' || !ride) return;
    ride.sinceGo += dt;
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
    stop,
    update,
    afterWalk,
    simulate,
    router,
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
