// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * follow.js — walk with a person in town, right behind them (T-3404, T-3471).
 *
 * Kevin, 2026-11-06: "make progress on completing humans and making them fully available
 * to interact with". A card and Find this person already reach the people placed in town;
 * Follow keeps the visitor with one of them as they go, so Hans Johnson's brougham can
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
 * The stand (T-3471, Kevin, 2026-11-07: "when i follow someone like frances, i get stuck on
 * walls, maybe when we follow we should go right behind them by default instead of along
 * side?"). It was 4 m to one side of the person: walking down a front walk, a passage or the
 * Glessners' court that stand is inside a house or a wall, the walker pressed against the
 * stone and the eye looked at the person through it. Now it is BEHIND_M straight back along
 * the way they are going (behind their back when they stand), a third-person game's trailing
 * view. Where a wall, fence or house is in the line from them to it, the stand is pulled in
 * toward them, or swung round them when pulled in too far — always to a point the router's
 * capsule test (`clearBetween`) says a visitor could walk to from them in a straight line,
 * so it is never in a wall and always in sight of them. A driver's carriage trails behind
 * him: the stand there is DRIVER_BEHIND_M back and DRIVER_SIDE_M off its line, where he shows
 * past its side and its envelope never has the visitor in its way. The follower walks
 * straight to the stand, or, a wall between, round by the person's own trail (where they
 * have just walked, so a way the visitor can walk too); held against a wall even so, not
 * closing on the stand for STUCK_S, the visitor is set down at the stand. Further than
 * JUMP_M (a jaunt elsewhere, a teleport) they are set down at once.
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
  // T-3471 (Kevin, 2026-11-07: "when i follow someone like frances, i get stuck on walls,
  // maybe when we follow we should go right behind them by default instead of along side?").
  // On foot: BEHIND_M straight back along their way, no side offset. A driver sits on a
  // box with the carriage behind him (the measured envelope runs 2.6 m back of the box and
  // 1.2 m either side of its line), so a follower stands DRIVER_BEHIND_M back and
  // DRIVER_SIDE_M off the line: 2.4 m behind its rear, and the eye's line to the box clears
  // the body's back corner (at 1 m of a 2.1 m roof straight behind, all but his hat was
  // hidden), with the carriage never having the visitor in its way.
  BEHIND_M: 2.4, MIN_BEHIND_M: 0.9,
  DRIVER_BEHIND_M: 5, DRIVER_SIDE_M: 2.6, DRIVER_MIN_BEHIND_M: 3.6,
  // Where a wall is in the way the stand is pulled in toward the person, or swung round
  // them (degrees, both ways); a swing costs as much as SWING_COST_M of pulled-in distance
  // per 45 degrees. The line is tested from START_M out from the person (they may be in a
  // doorway, nearer a wall than a visitor's shoulders allow).
  SWINGS_DEG: [25, 50, 80, 115, 150, 180], SWING_COST_M: 1.2, START_M: 0.5,
  RESOLVE_S: 0.15, ROUTE_S: 0.2,
  // A resolve stops looking round once it has spent this long (a capsule test is ~0.5 ms
  // on a laptop in software; walled in, the whole search is ~70 of them): the best found
  // so far stands, or the last stand is kept, and a held follower looks again less often.
  RESOLVE_BUDGET_MS: 6, HELD_RESOLVE_S: 0.6,
  // Not closing on the stand for STUCK_S while further than STUCK_M from it: held by a
  // wall the trail does not get round; set down at the stand.
  STUCK_S: 1.2, STUCK_M: 1.2,
  // Their way, not the way they face, once they move faster than MOVING_M_S; the eye
  // looks LOOK_AHEAD_S of their pace ahead of them (capped LOOK_AHEAD_MAX_M), along the
  // street they are going down, with them in the lower middle of the view.
  MOVING_M_S: 0.3, LOOK_AHEAD_S: 1.5, LOOK_AHEAD_MAX_M: 4,
  // The trail: where they have been, a point each TRAIL_STEP_M, TRAIL_MAX points kept.
  TRAIL_STEP_M: 0.4, TRAIL_MAX: 60,
  CATCH_UP_M: 2.5, JUMP_M: 40, LOOK_HOLD_S: 2.5,
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

/** The unit vector pointing back from a person: against their way when they are moving
 * (`ve`, `vn` m/s), else behind their back (`heading_deg`, compass). */
export function backOf(person, ve = 0, vn = 0) {
  const v = Math.hypot(ve, vn);
  if (v > FOLLOW.MOVING_M_S) return { e: -ve / v, n: -vn / v };
  const b = (person.heading_deg ?? 0) * DEG;
  return { e: -Math.sin(b), n: -Math.cos(b) };
}

/**
 * The stand behind a person with nothing in the way: `back` the unit vector behind them,
 * `side` +1 / -1 the side of a driver's carriage (to the right / left of their way, 0 on
 * foot), `t` how much of the full distance (1 = all of it; a wall pulls it in).
 */
export function followStand(person, { back = backOf(person), side = 0, t = 1 } = {}) {
  const driver = !!person.driver;
  const d = (driver ? FOLLOW.DRIVER_BEHIND_M : FOLLOW.BEHIND_M) * t;
  const s = driver ? FOLLOW.DRIVER_SIDE_M * side * t : 0;
  // Right of their way (compass): ahead = -back, and right of ahead is (ahead.n, -ahead.e).
  return { e: person.e + back.e * d - back.n * s, n: person.n + back.n * d + back.e * s };
}

/** A wall-free line by sampling a point test every 0.25 m, when no exact one is given. */
const now = () => (globalThis.performance?.now?.() ?? Date.now());

const sampledClear = (blockedAt) => (ae, an, be, bn) => {
  const steps = Math.max(1, Math.ceil(Math.hypot(be - ae, bn - an) / 0.25));
  for (let i = 0; i <= steps; i++) if (blockedAt(ae + (be - ae) * i / steps, an + (bn - an) * i / steps)) return false;
  return true;
};

/**
 * @param {object} o
 * @param {{ state: object, teleport: Function }} o.walker
 * @param {(personId: string) => ({ e, n, heading_deg, head_y?, name?, driver? } | null)} o.locate
 * @param {(e: number, n: number) => boolean} [o.blockedAt]
 * @param {(ae: number, an: number, be: number, bn: number) => boolean} [o.clearBetween]
 *   true where a visitor could walk the straight line (the router's capsule test); by
 *   default `blockedAt` sampled along it
 * @param {{ speed: number, sprintSpeed: number }} o.walk   the walker's own paces
 * @param {() => boolean} [o.busy]     true while something else steers (a Go to ride)
 * @param {(state: object|null, why: string) => void} [o.onChange]   why: 'start' (state.waitLeft
 *   > 0 while the person is not there yet), 'found' (a waited-for person is there now), or
 *   with null: 'button', 'input', 'travel', 'gone', 'switched'
 */
export function createFollow({ walker, locate, blockedAt = () => false, clearBetween = null, walk, busy = () => false, onChange = () => {} }) {
  if (!walker?.state || typeof locate !== 'function' || !(walk?.speed > 0)) throw Error('follow: a walker, a locate() and the walk paces are required');
  const clear = typeof clearBetween === 'function' ? clearBetween : sampledClear(blockedAt);
  let current = null;   // { personId, name, side, lookHeld, ... }
  let wrote = false;
  // Where the person was last seen and how they move: { e, n, age, ve, vn, heading, headY, goal }.
  let track = null;
  // Where they have been, oldest first (T-3471): the way round a corner for a follower
  // a wall has cut off from the stand.
  let trail = [];

  /** The person as they are now: seen position carried on by their velocity, heading and
   * head height low-passed. Called once per walker step with that step's dt. */
  function observe(person, dt) {
    const headY = person.head_y ?? null;
    if (!track) {
      track = { e: person.e, n: person.n, age: 0, ve: 0, vn: 0, heading: person.heading_deg ?? 0, headY, goal: null };
      trail = [{ e: person.e, n: person.n }];
    } else {
      // `age` is the time since they were last seen to move, up to the start of this step:
      // the town moves them after the walker, so a move seen now was made over that time.
      const de = person.e - track.e, dn = person.n - track.n;
      const moved = Math.hypot(de, dn);
      if (moved > FOLLOW.JUMP_M / 4) {
        // Set down elsewhere: start the estimate afresh.
        Object.assign(track, { e: person.e, n: person.n, age: 0, ve: 0, vn: 0, heading: person.heading_deg ?? 0, headY, goal: null });
        trail = [{ e: person.e, n: person.n }];
        if (current) current.offset = null;
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
      const last = trail.at(-1);
      if (Math.hypot(person.e - last.e, person.n - last.n) >= FOLLOW.TRAIL_STEP_M) {
        trail.push({ e: person.e, n: person.n });
        if (trail.length > FOLLOW.TRAIL_MAX) trail.shift();
      }
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

  /** The side of a driver's carriage the visitor is on now (+1 right of its way). */
  function sideFor(person) {
    if (!person.driver) return 0;
    const s = walker.state;
    const back = backOf(person, track?.ve ?? 0, track?.vn ?? 0);
    const rightness = (s.e - person.e) * -back.n + (s.n - person.n) * back.e;
    return rightness >= 0 ? 1 : -1;
  }

  /**
   * The stand, as an offset from the person (T-3471): straight back along their way, pulled
   * in toward them where a wall, fence or house is in the line, or swung round them when
   * pulled in too far; null when nowhere near them is clear (hold and watch).
   */
  function resolveStand(person) {
    const driver = !!person.driver;
    const full = driver ? FOLLOW.DRIVER_BEHIND_M : FOLLOW.BEHIND_M;
    const least = (driver ? FOLLOW.DRIVER_MIN_BEHIND_M : FOLLOW.MIN_BEHIND_M) / full;
    const back0 = backOf(person, track?.ve ?? 0, track?.vn ?? 0);
    const reach = (back, side) => {
      // From the full stand inward: the first whose line to the person is clear.
      const from = { e: person.e + back.e * FOLLOW.START_M, n: person.n + back.n * FOLLOW.START_M };
      for (const t of [1, 0.75, 0.55]) {
        if (t < least - 1e-9) break;
        const st = followStand(person, { back, side, t });
        if (clear(from.e, from.n, st.e, st.n)) return { t, st };
      }
      const st = followStand(person, { back, side, t: least });
      return clear(from.e, from.n, st.e, st.n) ? { t: least, st } : null;
    };
    const sides = driver ? [current.side || 1, -(current.side || 1)] : [0];
    const t0 = now();
    let best = null, spent = false;
    for (const side of sides) {
      if (spent) break;
      const penalty = side === sides[0] ? 0 : 0.5;   // a driver: the visitor's own side first
      for (const deg of [0, ...FOLLOW.SWINGS_DEG.flatMap((d) => (d === 180 ? [d] : [d, -d]))]) {
        const cost = (Math.abs(deg) / 45) * FOLLOW.SWING_COST_M + penalty;
        // Nothing further round can beat what is found: at best its full distance, less more.
        if (best && best.score >= full - cost) break;
        if (deg !== 0 && now() - t0 > FOLLOW.RESOLVE_BUDGET_MS) { spent = true; break; }
        const a = deg * DEG, c = Math.cos(a), sn = Math.sin(a);
        const back = { e: back0.e * c - back0.n * sn, n: back0.e * sn + back0.n * c };
        const r = reach(back, side);
        if (!r) continue;
        const score = r.t * full - cost;
        if (!best || score > best.score) best = { score, side, st: r.st };
      }
      if (best && best.side === side && best.score >= full - 1e-9) break;
    }
    if (!best) return spent && current.offset ? current.offset : null;
    if (driver) current.side = best.side;
    return { e: best.st.e - person.e, n: best.st.n - person.n };
  }

  /** Where to walk to reach `goal` from the eye: straight there when the line is clear,
   * else to the newest point of the person's own trail the eye can reach in a line. */
  function wayTo(goal) {
    const s = walker.state;
    if (clear(s.e, s.n, goal.e, goal.n)) return null;
    for (let i = trail.length - 1; i >= 0; i--) {
      const p = trail[i];
      if (Math.hypot(p.e - s.e, p.n - s.n) < 0.3) break;
      if (clear(s.e, s.n, p.e, p.n)) return { e: p.e, n: p.n };
    }
    return null;
  }

  /**
   * Begin following. `wait` seconds: a person whose figure is still loading (a driver's
   * model loads only once the visitor is near their round) is waited for that long.
   */
  function start(personId, { name = null, wait = 0 } = {}) {
    const person = personId ? locate(personId) : null;
    if (!person && !(wait > 0)) return false;
    if (current) stop('switched');
    track = null; trail = [];
    current = { personId, name: name ?? person?.name ?? null, side: person ? sideFor(person) : null,
      lookHeld: 0, waitLeft: person ? 0 : wait, offset: null, resolveLeft: 0, routeLeft: 0, via: null,
      stuckLeft: FOLLOW.STUCK_S, stuckFrom: Infinity, held: false };
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
    // Waited for (a figure loading, or someone still in their doorway): here now.
    if (current.waitLeft > 0) { current.waitLeft = 0; onChange({ ...current }, 'found'); }
    const person = observe(seen, dt);
    if (current.side === null) current.side = sideFor(person);
    if (!current.name && person.name) current.name = person.name;
    const s = walker.state;
    // The stand is resolved a few times a second (walls are tested then) and carried with
    // the person in between, so it moves at their pace.
    current.resolveLeft -= dt;
    if (current.resolveLeft <= 0) {
      current.offset = resolveStand(person);
      current.held = !current.offset;
      current.resolveLeft = current.held ? FOLLOW.HELD_RESOLVE_S : FOLLOW.RESOLVE_S;
    }
    const off = current.offset;
    const stand = off ? { e: person.e + off.e, n: person.n + off.n } : { e: s.e, n: s.n };
    const far = Math.hypot(stand.e - s.e, stand.n - s.n);
    const setDown = () => {
      walker.teleport({ local_e: stand.e, local_n: stand.n,
        yaw_deg: (Math.atan2(person.e - stand.e, person.n - stand.n) / DEG + 360) % 360 });
      track.goal = { e: stand.e, n: stand.n };
      current.via = null; current.stuckLeft = FOLLOW.STUCK_S; current.stuckFrom = Infinity;
    };
    if (far > FOLLOW.JUMP_M) { setDown(); return true; }
    // Held against a wall (T-3471: Kevin's view into the granite by 1800 Prairie): not
    // closing on the stand for STUCK_S while still well off it, the visitor is set down
    // at the stand, which is clear and in a line with the person.
    if (off && far > FOLLOW.STUCK_M) {
      if (!Number.isFinite(current.stuckFrom)) current.stuckFrom = far;
      current.stuckLeft -= dt;
      if (current.stuckLeft <= 0) {
        if (current.stuckFrom - far < 0.3) { setDown(); return true; }
        current.stuckLeft = FOLLOW.STUCK_S; current.stuckFrom = far;
      }
    } else { current.stuckLeft = FOLLOW.STUCK_S; current.stuckFrom = Infinity; }
    // The goal goes with the person (their velocity) and eases onto the stand, so the eye
    // moves at their pace instead of in one-frame snaps.
    if (!track.goal) track.goal = { e: s.e, n: s.n };
    const g = track.goal, kg = ease(dt, FOLLOW.STAND_TAU_S);
    g.e += track.ve * dt + (stand.e - g.e - track.ve * dt) * kg;
    g.n += track.vn * dt + (stand.n - g.n - track.vn * dt) * kg;
    // Held back by a wall or a fence, the goal waits where the eye is, not beyond it.
    if (Math.hypot(g.e - s.e, g.n - s.n) > FOLLOW.CATCH_UP_M * 2) { g.e = s.e + (g.e - s.e) / 2; g.n = s.n + (g.n - s.n) / 2; }
    // A wall between the eye and the goal: round it by the person's own trail.
    current.routeLeft -= dt;
    if (current.routeLeft <= 0) { current.routeLeft = FOLLOW.ROUTE_S; current.via = wayTo(g); }
    const aim = current.via ?? g;
    if (current.via && Math.hypot(aim.e - s.e, aim.n - s.n) < 0.3) current.routeLeft = 0;
    const de = aim.e - s.e, dn = aim.n - s.n;
    const dist = Math.hypot(de, dn);
    // The visitor's own look holds the view a while; then the eye eases back to them.
    const looked = Math.abs(intent.yawDelta) > 1e-4 || Math.abs(intent.pitchDelta) > 1e-4;
    current.lookHeld = looked ? FOLLOW.LOOK_HOLD_S : Math.max(0, current.lookHeld - dt);
    let yaw = s.yaw;
    if (!looked && current.lookHeld <= 0) {
      // Past them, a little way along where they are going: from behind, the street ahead
      // and the person in it share the view. Standing, the eye is on them.
      const v = Math.hypot(track.ve, track.vn);
      const lead = Math.min(FOLLOW.LOOK_AHEAD_MAX_M, v * FOLLOW.LOOK_AHEAD_S);
      const look = v > FOLLOW.MOVING_M_S ? { e: person.e + track.ve / v * lead, n: person.n + track.vn / v * lead } : person;
      const want = bearingToYaw(Math.atan2(look.e - s.e, look.n - s.n) / DEG);
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
    get state() { return current ? { personId: current.personId, name: current.name, side: current.side,
      lookHeld: current.lookHeld, held: current.held, offset: current.offset ? { ...current.offset } : null } : null; },
  };
}
