// SPDX-License-Identifier: GPL-3.0-or-later
/** Moving drivers use the fort gate's Interact key and sequence engine.
 * The actor remains authoritative: a refused resume never changes its state.
 * No input handlers, model copies or invented conversation live in this adapter.
 *
 * Step back (Kevin, 2026-11-07: "the step back and let the wagon pass interaction did not
 * work"): a team stopped because the visitor stands in its road offered the action with no
 * steps, so a press did nothing. `giveRoom` is the scene's half of it: `plan(actor)` finds
 * where the visitor steps to ({ from, to } in ENU, or null when there is no room) and
 * `place(e, n)` puts them there. The visitor walks aside, then the team goes on.
 *
 * T-3557 (Kevin, 2026-11-14: "we wanted to be able to board and drive the team around"):
 * with a `ride` (createTeamRide, one per scene) and an actor that has the drive API
 * (seat/takeReins/drive/handBack), the same thing also offers Climb up; aboard, Take the
 * reins / Hand back the reins and Get down. The ride owns where the visitor's eye is while
 * aboard, climbing or getting down; main.js holds the walker there after the walk
 * (`ride.hold`) and turns movement keys into the team's throttle and steering
 * (`ride.drive`). Riding and driving are reconstructed play (docs/LIBERTIES.md
 * L-board-drive-3557), never a claim about anyone's journey.
 */
import { bearingToYaw } from './angles.js';
import { giveRoomStand } from './transport-clearance.js';

const retired = new WeakSet();
const smooth = t => t * t * (3 - 2 * t);
const clamp1 = v => (Number.isFinite(v) ? Math.max(-1, Math.min(1, v)) : 0);
const lerp = (a, b, t) => a + (b - a) * t;
const turn = (from, to) => ((to - from + 540) % 360) - 180;

/** The drive API a team needs before it can be boarded (team-drive.js, T-3557). */
export const canBoard = actor => typeof actor?.seat === 'function' && typeof actor.takeReins === 'function'
  && typeof actor.handBack === 'function' && typeof actor.drive === 'function';

/** Seconds of the climb up, the climb down, and the longest wait for a driven team to pull up. */
export const RIDE_S = Object.freeze({ climb: 1.1, alight: 0.9, pullUp: 4 });

/**
 * The visitor aboard a team: at most one team per scene. Readers, all optional:
 *   visitor()        { e, n, y, bearing } — the visitor's eye now (the walker)
 *   standFor(actor)  { e, n } — a clear stand beside the team to get down to, or null
 *   groundAt(e, n)   the ground height a visitor stands on there
 *   walkEye()        the standing eye height
 *   onBoard(actor, on, why)  told when the visitor climbs up (true) and is down again (false)
 *   reducedMotion()  true: the team does not move (prefers-reduced-motion)
 */
export function createTeamRide({ visitor = () => null, standFor = () => null, groundAt = () => NaN,
  walkEye = () => 1.6, onBoard = () => {}, reducedMotion = () => false } = {}) {
  let actor = null, phase = null, eye = null, landing = null, pulling = false;
  let cruise = 0;   // the pace the team walks on at under the reins, until whoa
  let from = null, lastHeading = null, still = 0, lastAt = null;
  const seatOf = a => {
    try {
      const s = a?.seat?.();
      return s && [s.e, s.n, s.y].every(Number.isFinite) ? s : null;
    } catch { return null; }
  };
  const headingOf = a => {
    const s = seatOf(a);
    const h = Number.isFinite(s?.heading_deg) ? s.heading_deg : a?.heading_deg;
    return Number.isFinite(h) ? h : null;
  };
  const eyeOn = (e, n) => {
    const g = groundAt(e, n);
    return (Number.isFinite(g) ? g : (from?.y ?? 1.6) - walkEye()) + walkEye();
  };
  /** Where the visitor gets down to: a clear stand beside the team, or where they climbed up from. */
  const standOf = a => {
    let s = null;
    try { s = standFor(a); } catch { s = null; }
    if (Number.isFinite(s?.e) && Number.isFinite(s?.n)) return { e: s.e, n: s.n };
    return from ? { e: from.e, n: from.n } : null;
  };
  const end = (why, land) => {
    const a = actor;
    if (land) {
      const s = phase === 'alighting' && from?.stand ? from.stand : standOf(a);
      landing = s ?? null;
    }
    // The visitor's hands leave the reins with them: the driver takes his team home.
    if (a && (a.mode === 'reins' || a.mode === 'returning') && !a.disposed) { try { a.handBack(); } catch { /* the actor stays authoritative */ } }
    actor = null; phase = null; eye = null; pulling = false; lastHeading = null; from = null;
    onBoard(a, false, why);
    return true;
  };
  const ride = {
    get actor() { return actor; },
    get phase() { return phase; },
    get aboard() { return phase === 'seated' ? actor : null; },
    get driving() { return phase === 'seated' && actor?.mode === 'reins'; },
    get pullingUp() { return pulling; },
    get landing() { return landing; },
    reducedMotion: () => !!reducedMotion(),
    seatOf,

    /** Climb: the eye eases from where the visitor stands, up over the wheel, onto the seat. */
    climb(a, t) {
      if (actor !== a || phase !== 'climbing') {
        if (actor && actor !== a) return false;
        if (phase === 'seated') return true;
        const v = visitor();
        actor = a; phase = 'climbing'; landing = null; pulling = false;
        from = v && [v.e, v.n, v.y].every(Number.isFinite) ? { e: v.e, n: v.n, y: v.y, bearing: v.bearing ?? 0 } : null;
        onBoard(a, true, 'climb');
      }
      const s = seatOf(a);
      if (!s) return false;
      const f = smooth(Math.max(0, Math.min(1, t))), o = from ?? { ...s, bearing: headingOf(a) ?? 0 };
      const heading = headingOf(a) ?? o.bearing;
      eye = { e: lerp(o.e, s.e, f), n: lerp(o.n, s.n, f), y: lerp(o.y, s.y, f) + Math.sin(f * Math.PI) * 0.25,
        bearing: (o.bearing + turn(o.bearing, heading) * f + 360) % 360 };
      if (t >= 1) { phase = 'seated'; eye = null; lastHeading = heading; }
      return true;
    },

    /** Get down, first part: a team under the visitor's reins pulls up; one on its round stops. */
    pullUp(a) {
      if (actor !== a || phase !== 'seated') return false;
      still = 0; lastAt = null;
      if (a.mode === 'reins') pulling = true;
      else if (a.state === 'moving') a.stop('alighting');
      return true;
    },
    /** True once the team has pulled up (a stopped journey is stopped already). */
    stilled(a) {
      if (actor !== a) return true;
      if (a.mode !== 'reins' && a.mode !== 'returning' && a.state !== 'moving') return true;
      // The actor's own eased speed, where it has one (team-drive.js); else, three still readings.
      if (Number.isFinite(a.speed_m_s)) return a.speed_m_s <= 1e-6;
      const at = a.at;
      if (Array.isArray(at) && lastAt && Math.hypot(at[0] - lastAt[0], at[1] - lastAt[1]) < 1e-4) still++;
      else still = 0;
      lastAt = Array.isArray(at) ? [...at] : null;
      return still >= 3;
    },
    /** Get down, second part: the eye eases from the seat down to a clear stand beside the team. */
    alight(a, t) {
      if (actor !== a) return false;
      if (t === 0 || phase !== 'alighting') {
        const s = seatOf(a), to = standOf(a);
        if (!to) return false;
        phase = 'alighting'; pulling = false;
        const start = s ?? (from && Number.isFinite(from.y) ? from : { e: to.e, n: to.n, y: eyeOn(to.e, to.n) });
        from = { e: start.e, n: start.n, y: start.y, bearing: from?.bearing ?? 0, stand: to };
      }
      const s = from, to = from.stand, f = smooth(Math.max(0, Math.min(1, t)));
      eye = { e: lerp(s.e, to.e, f), n: lerp(s.n, to.n, f), y: lerp(s.y, eyeOn(to.e, to.n), f) + Math.sin(f * Math.PI) * 0.15, bearing: null };
      if (t >= 1) {
        landing = { e: to.e, n: to.n }; actor = null; phase = null; eye = null; from = null; lastHeading = null;
        // Off the box, the reins are the driver's again: he takes his team back to its round.
        if (a.mode === 'reins' && !a.disposed) { try { a.handBack(); } catch { /* the actor stays authoritative */ } }
        onBoard(a, false, 'get-down');
      }
      return true;
    },

    /**
     * Put the visitor down at once (a tier or year change, the team hidden or put up): beside
     * the team, or where they climbed up from. `land: false` leaves the walker where it is
     * (they took to the air, or a Go to is walking them away). False when nobody is aboard.
     */
    release(why = 'release', { land = true } = {}) {
      if (!actor) return false;
      return end(why, land);
    },
    /** A team leaving the scene mid-sequence: a climb finishes seated, a get-down lands. */
    settle(a) {
      if (actor !== a) return false;
      if (phase === 'climbing') ride.climb(a, 1);
      else if (phase === 'alighting') ride.alight(a, 1);
      return true;
    },

    /**
     * Called every frame before the walk and before the team's update. Aboard, movement keys
     * no longer walk: with the reins they are the team's throttle (forward/back) and steering
     * (sideways; +1 right), anything else is dropped. Look stays the visitor's.
     */
    drive(intent) {
      if (!actor || !intent) { cruise = 0; return false; }
      const a = actor;
      if (a.mode !== 'reins') cruise = 0;
      if (phase === 'seated' && (a.mode === 'reins' || pulling)) {
        // A team walks on until it is told to whoa: a push forward sets the pace (a stick's
        // tilt is the pace), letting go keeps it, a pull back pulls up. Nobody has to hold a
        // key or a thumb down to cross a block, on a phone above all.
        const f = clamp1(intent.forward);
        if (pulling || f < -0.15) cruise = 0;
        else if (f > 0.15) cruise = f;
        const input = pulling ? { throttle: -1, steer: 0 }
          : { throttle: f < -0.15 ? -1 : cruise, steer: clamp1(intent.strafe) };
        try { a.drive(input); } catch { /* a refused step pulls the team up inside the actor */ }
      }
      intent.forward = 0; intent.strafe = 0; intent.rise = 0; intent.sprint = false;
      return true;
    },

    /**
     * Called after the walk (and again after the teams have moved): the eye is on the seat, or on
     * its way up or down. Returns true while it holds the visitor. A team that is gone, hidden or
     * put up puts the visitor down; free-fly lets them go where they are.
     */
    hold(walker, WALK) {
      const s = walker?.state;
      if (!s) return false;
      if (landing && !actor) {
        const l = landing; landing = null;
        if (!s.flying) walker.teleport({ local_e: l.e, local_n: l.n, yaw_deg: walker.bearingDeg, pitch_deg: s.pitch * 180 / Math.PI });
        return false;
      }
      if (!actor) return false;
      if (s.flying) { end('fly', false); return false; }
      if (actor.disposed || actor.visible === false) { end('gone', true); return ride.hold(walker, WALK); }
      let at = eye, bearing = eye?.bearing ?? null;
      if (phase === 'seated') {
        const seat = seatOf(actor);
        if (!seat) { end('no-seat', true); return ride.hold(walker, WALK); }
        at = seat;
        // The view turns with the team (the visitor looks about from the seat as it goes round).
        const heading = headingOf(actor);
        if (heading !== null && lastHeading !== null) bearing = (walker.bearingDeg + turn(lastHeading, heading) + 360) % 360;
        lastHeading = heading;
      }
      if (!at) return false;
      s.e = at.e; s.n = at.n; s.eyeY = at.y;
      s.groundY = at.y - (WALK?.eyeHeight ?? 1.6);
      s.altitude = 0; s.stepEase = 0; s.bob = 0;
      if (bearing !== null && bearing !== undefined) s.yaw = bearingToYaw(bearing);
      walker.apply();
      return true;
    },
  };
  return ride;
}

/** The visitor as a team's clearance sees them: nobody, for the team they are aboard. */
export const riderOffTeam = (ride, id, visitor) => () => (ride?.actor?.id === id ? null : visitor());

/**
 * Where a visitor aboard `actor` gets down to: the nearest stand beside the team (sideways
 * preferred) that its whole measured envelope misses — where it stands and along the road it
 * drives next (12 m of its round; 4 m straight on under the reins) — and that `blockedAt`
 * lets a walker stand on and walk to from the seat. The same search as Step back
 * (transport-clearance.js giveRoomStand), widened to 10 m when 6 m finds nothing. Null: none.
 */
export function boardStand({ actor, row, blockedAt = () => false, ahead_m = 12 }) {
  const seat = (() => { try { return actor?.seat?.(); } catch { return null; } })();
  if (!row || !Array.isArray(row.envelope_local_xz_m) || !seat || ![seat.e, seat.n, seat.yaw_rad].every(Number.isFinite)) return null;
  const local = Array.isArray(row.passenger_local_m) ? row.passenger_local_m
    : [-row.driver_local_m[0], row.driver_local_m[1], row.driver_local_m[2]];
  const yaw = seat.yaw_rad, c = Math.cos(yaw), s = Math.sin(yaw);
  // The vehicle root under the seat (transport-loop.js localToEnu, inverted), unless the actor says.
  const pose = actor.pose;
  const root = pose && [pose.e, pose.n, pose.yaw].every(Number.isFinite) ? pose
    : { e: seat.e - c * local[0] - s * local[2], n: seat.n - s * local[0] + c * local[2], yaw };
  const poses = [{ e: root.e, n: root.n, yaw: root.yaw }];
  try {
    if ((actor.mode ?? 'route') === 'route' && typeof actor.previewAt === 'function') {
      const from = actor.snapshot().distance_m;
      for (let d = .25; d <= ahead_m; d += .25) poses.push(actor.previewAt(from + d));
    } else {
      const fe = Math.sin(root.yaw), fn = -Math.cos(root.yaw);
      for (let d = .25; d <= 4; d += .25) poses.push({ e: root.e + fe * d, n: root.n + fn * d, yaw: root.yaw });
    }
  } catch { /* the stand beside where it stands still holds */ }
  const at = { e: seat.e, n: seat.n };
  for (const reach_m of [6, 10]) {
    const stand = giveRoomStand({ poses, envelope_local_xz_m: row.envelope_local_xz_m, at, blockedAt, reach_m });
    if (stand && stand.moved_m > 0) return stand;
  }
  return null;
}

export function registerTransportInteraction(interactions, actor, { reach = 6, giveRoom = null, vehicle = 'wagon',
  driver = 'driver', onFoot = false, ride = null, reinsHint = () => 'You have the reins' } = {}) {
  if (!interactions?.add || !actor?.id || !actor?.name
      || typeof actor.stop !== 'function' || typeof actor.resume !== 'function'
      || typeof actor.canResume !== 'function' || !(Number.isFinite(reach) && reach > 0)
      || (giveRoom && (typeof giveRoom.plan !== 'function' || typeof giveRoom.place !== 'function'))
      || (ride && (typeof ride.climb !== 'function' || typeof ride.alight !== 'function'))) {
    throw Error('transport interaction requires a driver actor and the shared interaction engine');
  }
  const previous = interactions.get?.(`driver:${actor.id}`);
  if (previous && !retired.has(previous)) throw Error(`driver ${actor.id} already has an interaction`);
  let live = actor;
  const state = () => live?.state === 'moving' ? 'moving' : 'stopped';
  const refresh = () => { thing.state = state(); return thing; };
  const run = fn => t => {
    // Even a zero-second step receives run(0), then run(1). The command
    // happens once at its beginning; the sequence's finish is only a receipt.
    if (t !== 0 || !live?.visible) return;
    fn(live);
    refresh();
  };
  const stop = { id: 'stop', label: 'Stop driver', steps: [
    { label: 'Stopping', seconds: 0, run: run(a => a.stop('interaction')) },
  ] };
  const resume = { id: 'continue', label: 'Continue journey', steps: [
    { label: 'Continuing', seconds: 0, run: run(a => { if (a.canResume()) a.resume(); }) },
  ] };
  // T-3475: stepping aside is a short walk, eased, then the team is let go.
  const STEP_S = 0.8;
  let room = null;
  const blocked = { id: 'give-room', label: `Step back to let the ${vehicle} pass`,
    refuse() {
      room = live?.visible && giveRoom ? giveRoom.plan(live) : null;
      return room ? null : 'No room to step aside here';
    },
    steps: [
      { label: 'Stepping back', seconds: STEP_S, run(t) {
        if (!room || !live?.visible) return;
        const k = smooth(t);
        giveRoom.place(room.from.e + (room.to.e - room.from.e) * k, room.from.n + (room.to.n - room.from.n) * k);
      } },
      { label: 'Letting it pass', seconds: 0, run: run(a => { room = null; if (a.canResume()) a.resume(); }) },
    ],
    said: () => live?.state === 'moving' ? `The ${vehicle} goes on` : `Still in the ${vehicle}'s way`,
  };

  // T-3557: boarding. Only a team with the drive API, in a scene with a ride, offers it.
  const boardable = () => !!ride && canBoard(live);
  const mine = () => !!ride && ride.actor === live && !!live;
  let wasMoving = false;
  const still = () => ride?.reducedMotion?.() ? ' · reduced motion: the team stands' : '';
  const climb = { id: 'climb-up', label: onFoot ? `Climb up onto the ${vehicle}` : `Climb up beside the ${driver}`,
    refuse() {
      if (ride.actor && ride.actor !== live) return 'Already aboard';
      return ride.seatOf(live) ? null : `No seat on this ${vehicle}`;
    },
    steps: [
      { label: 'Pulling up', seconds: 0, run: run(a => { wasMoving = a.state === 'moving'; if (wasMoving) a.stop('boarding'); ride.climb(a, 0); }) },
      { label: 'Climbing up', seconds: RIDE_S.climb, run(t) { if (live) ride.climb(live, t); } },
      { label: 'Moving off', seconds: 0, run: run(a => { if (wasMoving && !ride.reducedMotion() && a.canResume()) a.resume(); wasMoving = false; }) },
    ],
    said: () => `Aboard${still()}`,
  };
  const reins = { id: 'take-reins', label: 'Take the reins', steps: [
    { label: 'Taking the reins', seconds: 0, run: run(a => a.takeReins()) },
  ], said: () => live?.mode === 'reins' ? `${reinsHint()}${still()}` : `The ${driver} keeps the reins` };
  const handBack = { id: 'hand-back', label: 'Hand back the reins', steps: [
    { label: 'Handing back', seconds: 0, run: run(a => a.handBack()) },
  ], said: () => `The ${driver} takes the reins` };
  const getDown = { id: 'get-down', label: 'Get down',
    refuse: () => (mine() && ride.phase === 'seated' ? null : 'Not aboard'),
    steps: [
      { label: 'Pulling up', timeout: RIDE_S.pullUp,
        run(t) { if (t === 0 && live) { wasMoving = live.mode === 'route' && live.state === 'moving'; ride.pullUp(live); } },
        until: () => !live || ride.stilled(live) },
      { label: 'Getting down', seconds: RIDE_S.alight, run(t) { if (live) ride.alight(live, t); } },
      { label: 'Down', seconds: 0, run: run(a => {
        // A team on its own round goes on once the visitor is clear of it.
        if (wasMoving && a.mode === 'route' && a.canResume()) a.resume();
        wasMoving = false;
      }) },
    ],
    said: () => `Down beside the ${vehicle}`,
  };
  const aboardActions = () => {
    const mode = live.mode;
    if (mode === 'reins') return [handBack, getDown];
    if (mode === 'returning') return [reins, getDown];
    const journey = live.state === 'moving' ? stop : live.canResume() ? resume : null;
    return [reins, ...(journey ? [journey] : []), getDown];
  };

  const thing = {
    id: `driver:${actor.id}`, name: actor.name, kind: 'vehicle',
    states: ['moving', 'stopped'], state: state(), reach,
    get at() {
      if (!live?.visible) return null;
      const at = live.at;
      return Array.isArray(at) && at.length === 2 && at.every(Number.isFinite) ? at : null;
    },
    /** Aboard, the team is worked from the seat: always the nearest thing to the visitor. */
    get spots() {
      if (!mine()) return [];
      const s = ride.seatOf(live);
      return s ? [[s.e, s.n]] : [];
    },
    get actions() {
      refresh();
      if (!live?.visible) return {};
      if (mine()) {
        if (ride.phase !== 'seated') return {};
        const list = aboardActions();
        return { moving: list, stopped: list };
      }
      // Aboard another team: this one is not worked from there.
      if (ride?.actor) return {};
      const board = boardable() ? [climb] : [];
      return { moving: [stop, ...board], stopped: [live.canResume() ? resume : blocked, ...board] };
    },
  };
  interactions.add(thing);
  return {
    thing, refresh,
    dispose() {
      // This adapter does not own the vehicle. Retire its offer even on the
      // original fort engine, which has no remove() API, without retaining it.
      // T-3557: a team that is only re-registered (another team loaded) keeps its visitor; a
      // sequence it was running finishes at once. A team leaving the scene puts them down.
      if (mine()) {
        ride.settle(live);
        if (live.disposed) ride.release('gone');
      }
      live = null;
      retired.add(thing);
      thing.running = null;
      thing.state = 'stopped';
      interactions.remove?.(thing.id);
    },
  };
}

/** A layer owns its registrations, just as it owns its moving actors. */
export function registerTransportInteractions(interactions, actors, options) {
  // Options may differ per team (its word, its own road to step out of): a function of the actor.
  const handles = actors.map(actor => registerTransportInteraction(interactions, actor,
    typeof options === 'function' ? options(actor) : options));
  return {
    refresh() { for (const handle of handles) handle.refresh(); },
    dispose() { for (const handle of handles) handle.dispose(); },
    get list() { return handles.map(handle => handle.thing); },
  };
}
