// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * follow.js — walk alongside a person in town (T-3404).
 *
 * Kevin, 2026-11-06: "make progress on completing humans and making them fully available
 * to interact with". A card and Find this person already reach the people placed in town;
 * Follow keeps the visitor beside one of them as they go, so Hans Johnson's brougham can
 * be walked with round the block instead of watched leaving.
 *
 * It is a second writer of the intent, the way travel.js is (controls/intent.js): `steer`
 * writes `forward`, `strafe`, `sprint`, `yawDelta` and `pitchDelta` BEFORE the walker reads
 * them, and `afterWalk` zeroes the movement it wrote once the walker has consumed it. So the
 * walker's own collision, steps and ground hold for a follower exactly as for a walker, and
 * any movement the VISITOR writes (a key, the stick, fly) ends the follow before it steers.
 * Looking round does not: the visitor's own look holds the view for LOOK_HOLD_S, then the
 * eye eases back to the person.
 *
 * The stand: SIDE_M to one side of the person and BEHIND_M back along their heading — the
 * side the visitor was on when they asked, or the other when that one is blocked (a house,
 * a fence: the router's own `blockedAt`). 4 m is the same offset Find this person sets a
 * visitor down at beside a driver's seat (main.js goToTarget), clear of the carriage's
 * envelope, so a follower never stops the journey they are following. Further than JUMP_M
 * (a jaunt elsewhere, a teleport) the visitor is set down at the stand at once.
 *
 * Smooth, not snapped (Kevin, 2026-11-06: "when i follow hans it is very jittery along side
 * him"). The town's carriages move AFTER the walker each frame, so a follower that steps
 * straight onto the stand trails by exactly one frame's travel: at 60 fps with the odd
 * dropped frame the eye's speed swung between 0 and twice the carriage's, and the look,
 * re-aimed every step at a bobbing head on a swaying box, shook with it. Now the person's
 * velocity is estimated from where they were seen, the stand is taken where they are NOW
 * (seen + velocity × time since), heading and head height are low-passed, and the eye eases
 * to the stand and turns to the person on critically damped curves rather than at a rate cap.
 *
 * Nothing here knows THREE or the DOM: `locate(personId)` answers where the person is now,
 * in local ENU metres with a compass heading, and tools/test_person_interaction.mjs drives
 * it with fakes.
 */
import { DEG, bearingToYaw } from './angles.js';

export const FOLLOW = Object.freeze({
  SIDE_M: 4, BEHIND_M: 1, CATCH_UP_M: 2.5, JUMP_M: 40, LOOK_HOLD_S: 2.5,
  TURN_DEG_S: 150, PITCH_DEG_S: 60, HEAD_ABOVE_GROUND_M: 1.6,
  // Smoothing time constants, seconds (T-3404 follow-up): the person's measured velocity,
  // their heading and head height (a gait's bob and a box's sway are not followed), the
  // eye's ease onto the stand, and its turn onto the person.
  VEL_TAU_S: 0.3, HEADING_TAU_S: 0.6, HEAD_TAU_S: 1.2, STAND_TAU_S: 0.25, LOOK_TAU_S: 0.25,
  // Seen in the same place this long, they have stopped: the estimate decays to rest.
  STILL_S: 0.15,
});

const wrapPi = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
/** The fraction of the way an exponential ease of time constant `tau` goes in `dt`. */
const ease = (dt, tau) => 1 - Math.exp(-Math.max(dt, 0) / tau);

/** Where to stand beside a person facing `headingDeg`: `side` +1 right of them, -1 left. */
export function followStand(person, side) {
  const b = (person.heading_deg ?? 0) * DEG;
  const fe = Math.sin(b), fn = Math.cos(b);      // ahead of them
  const re = Math.cos(b), rn = -Math.sin(b);     // to their right
  return { e: person.e + re * side * FOLLOW.SIDE_M - fe * FOLLOW.BEHIND_M,
    n: person.n + rn * side * FOLLOW.SIDE_M - fn * FOLLOW.BEHIND_M };
}

/**
 * @param {object} o
 * @param {{ state: object, teleport: Function }} o.walker
 * @param {(personId: string) => ({ e, n, heading_deg, head_y?, name? } | null)} o.locate
 * @param {(e: number, n: number) => boolean} [o.blockedAt]
 * @param {{ speed: number, sprintSpeed: number }} o.walk   the walker's own paces
 * @param {() => boolean} [o.busy]     true while something else steers (a Go to ride)
 * @param {(state: object|null, why: string) => void} [o.onChange]
 */
export function createFollow({ walker, locate, blockedAt = () => false, walk, busy = () => false, onChange = () => {} }) {
  if (!walker?.state || typeof locate !== 'function' || !(walk?.speed > 0)) throw Error('follow: a walker, a locate() and the walk paces are required');
  let current = null;   // { personId, name, side, lookHeld }
  let wrote = false;
  // Where the person was last seen and how they move: { e, n, age, ve, vn, heading, headY, goal }.
  let track = null;

  /** The person as they are now: seen position carried on by their velocity, heading and
   * head height low-passed. Called once per walker step with that step's dt. */
  function observe(person, dt) {
    const headY = person.head_y ?? null;
    if (!track) {
      track = { e: person.e, n: person.n, age: 0, ve: 0, vn: 0, heading: person.heading_deg ?? 0, headY, goal: null };
    } else {
      // `age` is the time since they were last seen to move, up to the start of this step:
      // the town moves them after the walker, so a move seen now was made over that time.
      const de = person.e - track.e, dn = person.n - track.n;
      const moved = Math.hypot(de, dn);
      if (moved > FOLLOW.JUMP_M / 4) {
        // Set down elsewhere: start the estimate afresh.
        Object.assign(track, { e: person.e, n: person.n, age: 0, ve: 0, vn: 0, heading: person.heading_deg ?? 0, headY, goal: null });
      } else if (moved > 1e-6 && track.age > 0) {
        const k = ease(track.age, FOLLOW.VEL_TAU_S);
        track.ve += (de / track.age - track.ve) * k;
        track.vn += (dn / track.age - track.vn) * k;
        track.e = person.e; track.n = person.n; track.age = 0;
      } else if (moved > 1e-6) {
        track.e = person.e; track.n = person.n;
      } else if (track.age > FOLLOW.STILL_S) {
        const k = ease(dt, FOLLOW.VEL_TAU_S / 2);
        track.ve -= track.ve * k; track.vn -= track.vn * k;
      }
      const dh = ((((person.heading_deg ?? 0) - track.heading) % 360) + 540) % 360 - 180;
      track.heading = (track.heading + dh * ease(dt, FOLLOW.HEADING_TAU_S) + 360) % 360;
      if (headY !== null) track.headY = track.headY === null ? headY : track.headY + (headY - track.headY) * ease(dt, FOLLOW.HEAD_TAU_S);
    }
    // Where they will be when this step's frame is drawn: seen, carried on by their pace.
    track.age += dt;
    const ahead = Math.min(track.age, 0.25);
    return { ...person, e: track.e + track.ve * ahead, n: track.n + track.vn * ahead,
      heading_deg: track.heading, head_y: track.headY ?? undefined };
  }

  function stop(why = 'button') {
    if (!current) return false;
    const was = current;
    current = null;
    onChange(null, why, was);
    return true;
  }

  /** The side of the person the visitor stands, preferring one whose stand is clear. */
  function pickSide(person, prefer) {
    for (const side of [prefer, -prefer]) {
      const s = followStand(person, side);
      if (!blockedAt(s.e, s.n)) return side;
    }
    return 0;   // both blocked: hold where you are and watch
  }

  /** The side the visitor is on now, or the clear one. */
  function sideFor(person) {
    const s = walker.state;
    const b = (person.heading_deg ?? 0) * DEG;
    const rightness = (s.e - person.e) * Math.cos(b) + (s.n - person.n) * -Math.sin(b);
    return pickSide(person, rightness >= 0 ? 1 : -1);
  }

  /**
   * Begin following. `wait` seconds: a person whose figure is still loading (a driver's
   * model loads only once the visitor is near their round) is waited for that long.
   */
  function start(personId, { name = null, wait = 0 } = {}) {
    const person = personId ? locate(personId) : null;
    if (!person && !(wait > 0)) return false;
    if (current) stop('switched');
    current = { personId, name: name ?? person?.name ?? null, side: person ? sideFor(person) : null,
      lookHeld: 0, waitLeft: person ? 0 : wait };
    track = null;
    onChange({ ...current }, 'start');
    return true;
  }

  /** Before the walker: the visitor's own movement ends it; otherwise steer to the stand. */
  function steer(dt, intent) {
    if (!current) return false;
    if (busy()) { stop('travel'); return false; }
    if (intent.moving || intent.sprint || intent.flying || walker.state.flying) { stop('input'); return false; }
    const seen = locate(current.personId);
    if (!seen) {
      if (current.waitLeft > 0) { current.waitLeft -= dt; return false; }
      stop('gone'); return false;
    }
    current.waitLeft = 0;
    const person = observe(seen, dt);
    if (current.side === null) current.side = sideFor(person);
    if (!current.name && person.name) current.name = person.name;
    const s = walker.state;
    let side = current.side;
    let stand = side ? followStand(person, side) : { e: s.e, n: s.n };
    if (side && blockedAt(stand.e, stand.n)) {
      side = pickSide(person, side);
      current.side = side;
      stand = side ? followStand(person, side) : { e: s.e, n: s.n };
    }
    const far = Math.hypot(stand.e - s.e, stand.n - s.n);
    if (far > FOLLOW.JUMP_M) {
      walker.teleport({ local_e: stand.e, local_n: stand.n,
        yaw_deg: (Math.atan2(person.e - stand.e, person.n - stand.n) / DEG + 360) % 360 });
      track.goal = { e: stand.e, n: stand.n };
      return true;
    }
    // The goal goes with the person (their velocity) and eases onto the stand, so the eye
    // moves at their pace instead of in one-frame snaps.
    if (!track.goal) track.goal = { e: s.e, n: s.n };
    const g = track.goal, kg = ease(dt, FOLLOW.STAND_TAU_S);
    g.e += track.ve * dt + (stand.e - g.e - track.ve * dt) * kg;
    g.n += track.vn * dt + (stand.n - g.n - track.vn * dt) * kg;
    // Held back by a wall or a fence, the goal waits where the eye is, not beyond it.
    if (Math.hypot(g.e - s.e, g.n - s.n) > FOLLOW.CATCH_UP_M * 2) { g.e = s.e + (g.e - s.e) / 2; g.n = s.n + (g.n - s.n) / 2; }
    const de = g.e - s.e, dn = g.n - s.n;
    const dist = Math.hypot(de, dn);
    // The visitor's own look holds the view a while; then the eye eases back to them.
    const looked = Math.abs(intent.yawDelta) > 1e-4 || Math.abs(intent.pitchDelta) > 1e-4;
    current.lookHeld = looked ? FOLLOW.LOOK_HOLD_S : Math.max(0, current.lookHeld - dt);
    let yaw = s.yaw;
    if (!looked && current.lookHeld <= 0) {
      const want = bearingToYaw(Math.atan2(person.e - s.e, person.n - s.n) / DEG);
      const cap = FOLLOW.TURN_DEG_S * DEG * dt, kl = ease(dt, FOLLOW.LOOK_TAU_S);
      intent.yawDelta = clamp(wrapPi(want - s.yaw) * kl, -cap, cap);
      yaw = s.yaw + intent.yawDelta;
      const eyeY = s.eyeY ?? 0;
      const headY = person.head_y ?? ((s.groundY ?? 0) + FOLLOW.HEAD_ABOVE_GROUND_M);
      const over = Math.hypot(person.e - s.e, person.n - s.n);
      // Aimed at their chest, so the person and the street around them share the view.
      const wantPitch = clamp(Math.atan2(headY - 0.45 - eyeY, Math.max(over, 0.5)), -0.5, 0.5);
      const pcap = FOLLOW.PITCH_DEG_S * DEG * dt;
      intent.pitchDelta = clamp((wantPitch - s.pitch) * kl, -pcap, pcap);
    }
    // Camera-relative, as the walker reads it: forward along the yaw it will have.
    const fe = -Math.sin(yaw), fn = Math.cos(yaw);
    const re = Math.cos(yaw), rn = Math.sin(yaw);
    // Sprint to catch up, and keep sprinting till close: no flicker between the two paces.
    const sprint = walk.sprintSpeed > walk.speed && (dist > FOLLOW.CATCH_UP_M || (current.sprinting && dist > 0.5));
    current.sprinting = sprint;
    const pace = (sprint ? walk.sprintSpeed : walk.speed) * Math.max(dt, 1e-6);
    let f = (de * fe + dn * fn) / pace, r = (de * re + dn * rn) / pace;
    const mag = Math.hypot(f, r);
    if (mag > 1) { f /= mag; r /= mag; }
    // No dead zone worth a frame's travel: at a carriage's pace one frame is 2-3 cm, and
    // a 5 cm one left the eye standing, then lunging (the jitter Kevin saw).
    if (dist < 0.002) { f = 0; r = 0; }
    intent.forward = f; intent.strafe = r; intent.sprint = sprint;
    wrote = true;
    return true;
  }

  /** After the walker has consumed it: zero exactly what steer wrote. */
  function afterWalk(intent) {
    if (!wrote) return;
    intent.forward = 0; intent.strafe = 0; intent.sprint = false;
    wrote = false;
  }

  return {
    start, stop, steer, afterWalk,
    get active() { return !!current; },
    get personId() { return current?.personId ?? null; },
    get state() { return current ? { ...current } : null; },
  };
}
