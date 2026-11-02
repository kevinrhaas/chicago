/**
 * walker.js — a person on foot. No physics engine.
 *
 * A capsule sliding on the heightfield sampler, and that is the whole model. It
 * is enough because there is nothing to simulate: no jumping, no vehicles, no
 * ragdolls, and — by standing instruction in `AGENTS.md` — no other people.
 * Importing a physics engine to walk across a prairie would cost a megabyte and
 * a build step to reproduce what forty lines of arithmetic already do.
 *
 * The one rule that is not arbitrary: a **0.35 m step-up limit**. That is a
 * little over a foot, which is what a plank walk stands above the mud and what a
 * person steps onto without thinking. Below it you step up; above it you are
 * looking at a wall and you stop. Downhill is free — you can always step down.
 *
 * The one thing that is not the heightfield: **bridge decks** (T-0001). A deck is
 * a surface the visitor stands on that the terrain knows nothing about, so the
 * floor is `surfaceAt()` rather than `terrain.walkHeight()` and every path in this
 * module asks it. Getting ONTO a deck from the bank asks nothing of this module:
 * the approach earthworks (T-0046) grade the terrain itself to meet each deck at
 * its ends, so the walk up is ordinary heightfield walking and the step from
 * earth to planks is millimetres. See docs/LIBERTIES.md L147.
 *
 * The one hole in a wall: **a passage** (T-2943). A footprint is solid, but a sidecar
 * may declare `footprint.passages` — an opening the model really has through the
 * building (Glessner's carriage passage from Prairie Avenue to the court): its plan in
 * the footprint's frame, which edges are its open ends, and its clear height. Where
 * that height clears the eye (WALK.eyeHeight, the seat included, + HEADROOM_MARGIN_M),
 * the capsule inside the passage is held off its two side walls instead of being
 * pushed out of the building, so a visitor on foot walks through and a rider who would
 * strike the soffit does not. The open ends run LANE_REACH_M past the façade, so the
 * passage takes over before the façade's own push-out would turn you back.
 */

import * as THREE from 'three';
import { deckFromSidecar, deckHeightAt } from './deck-surface.js';
import { enuToWorld, bearingToYaw, yawToBearing } from './terrain.js';

const DEG = Math.PI / 180;

/**
 * The walk numbers, and the fly numbers, both live in travel-settings.js: they are
 * the one definition travel.js writes and the pure estimates read, and neither needs
 * a renderer to be read. Re-exported here because this is the module that walks by
 * them.
 */
import { WALK, FLY } from './travel-settings.js';
export { WALK, FLY };

/** Point-in-polygon, ray casting. `pts` is [[e, n], ...]. */
function inside(e, n, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i];
    const [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n)
        && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

/** Nearest point on a polygon's boundary. */
function nearestOnBoundary(e, n, pts) {
  let best = null;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ax, ay] = pts[j];
    const [bx, by] = pts[i];
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy || 1e-9;
    const t = Math.max(0, Math.min(1, ((e - ax) * dx + (n - ay) * dy) / len2));
    const px = ax + dx * t;
    const py = ay + dy * t;
    const d = Math.hypot(e - px, n - py);
    if (!best || d < best.d) best = { e: px, n: py, d };
  }
  return best;
}

/**
 * Turn each sidecar's footprint into a world-space polygon in local ENU metres.
 * Tolerates both shapes seen in the wild: a bare `[[u, v], ...]` array and a
 * `{ polygon, confidence, note }` object.
 */
/** T-2943: the eye must clear a passage's soffit by this much to walk through it. */
export const HEADROOM_MARGIN_M = 0.1;
/** T-2943: how far a passage's open ends reach past the walls, so its lane takes over
 * from the façade's push-out (more than WALK.radius, with room to spare). */
export const LANE_REACH_M = 1.0;

/**
 * T-2943: a passage as the walker uses it — its plan in world metres, its open ends
 * pushed LANE_REACH_M outward along the side walls, and those side walls as segments.
 * `toWorld` maps a footprint-frame [u, v] to [e, n]. Returns null for a malformed one.
 */
export function passageLane(passage, toWorld = (p) => p) {
  const plan = passage?.polygon;
  if (!Array.isArray(plan) || plan.length < 3 || !Number.isFinite(passage.clear_m)) return null;
  const pts = plan.map(toWorld);
  const n = pts.length;
  const open = new Set((passage.open_edges ?? []).map(([a, b]) => `${Math.min(a, b)}:${Math.max(a, b)}`));
  const edge = (i) => [i, (i + 1) % n];
  const isOpen = ([a, b]) => open.has(`${Math.min(a, b)}:${Math.max(a, b)}`);
  const lane = pts.map((p) => [...p]);
  for (let i = 0; i < n; i++) {
    const touchesOpen = isOpen(edge(i)) || isOpen(edge((i - 1 + n) % n));
    if (!touchesOpen) continue;
    // The wall edge that meets this corner: run outward along it.
    const wall = [edge(i), edge((i - 1 + n) % n)].find((ed) => !isOpen(ed));
    if (!wall) continue;
    const other = wall[0] === i ? wall[1] : wall[0];
    const dx = pts[i][0] - pts[other][0], dy = pts[i][1] - pts[other][1];
    const len = Math.hypot(dx, dy) || 1;
    lane[i] = [pts[i][0] + (dx / len) * LANE_REACH_M, pts[i][1] + (dy / len) * LANE_REACH_M];
  }
  const walls = [];
  for (let i = 0; i < n; i++) if (!isOpen(edge(i))) walls.push([lane[i], lane[(i + 1) % n]]);
  const centre = lane.reduce((c, p) => [c[0] + p[0] / n, c[1] + p[1] / n], [0, 0]);
  return { kind: passage.kind ?? 'passage', clear: passage.clear_m, floor: passage.floor_m ?? 0, pts, lane, walls, centre };
}

export function footprintsFrom(registry, { camps = false } = {}) {
  const out = [];
  for (const record of registry.values()) {
    const raw = record.sidecar?.footprint;
    const poly = Array.isArray(raw) ? raw : raw?.polygon;
    if (!Array.isArray(poly) || poly.length < 3) continue;

    const p = record.sidecar.placement ?? {};
    // A water-anchored structure's footprint is a DECK, not a wall, so it is not
    // an obstruction: treating a bridge as one would put an invisible barrier
    // across the river with nothing visible at head height to explain it. The
    // same polygon is a SURFACE instead — see decksFrom() below, which reads it
    // as the thing you stand on rather than the thing you are kept out of.
    if (p.vertical_anchor === 'water') continue;
    // And a record drawn by another layer is not an obstruction either. The
    // estray pen's footprint is now a fence line rather than a wall (T-0051),
    // and enclosures.js is explicit that a visitor walks THROUGH a fence — so
    // keeping the polygon here would leave an invisible box on the public
    // square with nothing at head height to explain it, which is the same bug
    // the water clause above exists to prevent.
    if (record.sidecar?.drawn_by) continue;
    // Nor is a camp's ground (T-1803). Its footprint is the strip of bank the tents
    // stand on, open between every pitch, and a polygon the length of a row of tents
    // would be an invisible wall across the riverfront with gaps in plain view. It IS
    // ground nothing grows through, though, so the planting keep-out asks for the
    // camps alone with `{ camps: true }` and gets exactly those.
    if ((record.sidecar?.archetype === 'camp') !== camps) continue;
    const th = (p.rotation_deg ?? 0) * DEG;
    const cos = Math.cos(th);
    const sin = Math.sin(th);
    const e0 = p.local_e ?? 0;
    const n0 = p.local_n ?? 0;

    // Compass-bearing rotation, matching bearingToYaw(): clockwise from north.
    const toWorld = ([u, v]) => [e0 + u * cos + v * sin, n0 - u * sin + v * cos];
    const fp = { id: record.id, pts: poly.map(toWorld) };
    // T-2943: the openings through it a visitor may walk (see the header).
    const lanes = (Array.isArray(raw?.passages) ? raw.passages : []).map((p) => passageLane(p, toWorld)).filter(Boolean);
    if (lanes.length) fp.passages = lanes;
    out.push(fp);
  }
  return out;
}

/**
 * The surfaces a visitor may stand ON TOP OF, as opposed to the ground, THAT THE
 * STRUCTURE REGISTRY CARRIES.
 *
 * In the registry that means bridge decks and nothing else, and the dataset says so: the
 * sidecar carries `placement.walk_surface_m` — the height of the deck above the
 * structure's own anchor — and it is `null` on all 327 structures that are not a
 * crossing. The number is the generator's `deck_height_m`, carried through by
 * `tools/compile_scene.py`, so the plank a visitor's boot is on and the plank the
 * mesh draws are one number rather than two that agree until they do not.
 *
 * The plan outline is the FOOTPRINT, which for a bridge record is documented as
 * the deck outline rather than a placeholder — so the surface ends exactly where
 * the drawn deck ends, and stepping off the side of one is stepping off the side
 * of what you can see.
 *
 * ONLY water-anchored structures are read. A deck's world height is its anchor
 * plus `walk_surface_m`, and a `water` anchor is a literal zero by the definition
 * of the vertical datum (docs/GLB-CONTRACT.md); resolving a terrain anchor would
 * mean re-deriving the lowest ground under the footprint, which is buildings.js's
 * job and not a calculation to keep a second copy of. Nothing in the dataset needs
 * it, and skipping is visible — the deck simply is not walkable — where guessing
 * would put a floating surface in the air.
 *
 * IT IS NOT THE ONLY SOURCE OF DECKS. The street edge's plank walks publish
 * their own (T-0119), and since T-0058 so do the river wharves: a wharf stands
 * over the water with no structure record at all, so it can carry neither a
 * sidecar nor a `walk_surface_m`, and its layer hands over the deck it drew and
 * every tread of its boarding stair in this same shape. `main.js` puts every
 * lot in the one array `createWalker` is given. What this function owns is the
 * REGISTRY'S half, and the return shape below is the contract between them.
 *
 * @param {Map} registry the loaded structure registry
 * @returns {Array<{id:string, y:number, pts:number[][]}>}
 */
export function decksFrom(registry) {
  const out = [];
  for (const record of registry.values()) {
    const deck = deckFromSidecar(record.id, record.sidecar);
    if (deck) out.push(deck);
  }
  return out;
}

/**
 * @param {object} o
 * @param {THREE.PerspectiveCamera} o.camera
 * @param {{height:(e:number,n:number)=>number}} o.terrain
 * @param {Array<{id:string, pts:number[][]}>} o.footprints
 * @param {Array<{id:string, y:number, pts:number[][]}>} o.decks
 * @param {{local_e:number, local_n:number, yaw_deg:number}} o.spawn
 */
export function createWalker({ camera, terrain, footprints = [], decks = [], spawn = {} }) {
  const state = {
    e: spawn.local_e ?? 0,
    n: spawn.local_n ?? 0,
    yaw: bearingToYaw(spawn.yaw_deg ?? 0),
    pitch: 0,
    groundY: 0,
    eyeY: 0,
    speed: 0,
    /** Set when the last move was blocked by the step-up rule. */
    blocked: false,
    /** Free-fly mode. The walker owns the transition; the intent owns the wish. */
    flying: false,
    /** Metres above local ground, 0 on foot. What the HUD reports. */
    altitude: 0,
    /**
     * The gait's vertical head movement, metres, written by travel.js and added
     * to the camera in apply() ONLY. `eyeY` stays the honest standing eye height
     * — the eye-height smoke reads it — so a rider's bob is a camera offset, not
     * a change of stature. Zero on foot, in the air, and under reduced motion.
     */
    bob: 0,
  };
  const euler = new THREE.Euler(0, 0, 0, 'YXZ');
  const world = new THREE.Vector3();

  /**
   * The floor, and the ONLY thing in this module that answers "how high is the
   * surface here". Every path — walking, stepping, teleporting, landing out of
   * free-fly — goes through it, because a walker that agreed with itself only on
   * some of them is how you end up standing on a bridge and falling through it
   * when you stop moving.
   *
   * `decks` carries the bridges the registry declares (`decksFrom`), the street
   * edge's boards, and the wharf decks and stair treads their layer publishes at
   * the height it drew them. Nothing here cares which is which: a deck is an id,
   * a height and a plan outline, and every route hands over exactly that. The
   * HIGHEST deck covering a point wins, which is what makes a flight of treads
   * behave as a stair rather than as one ambiguous slab.
   *
   * `terrain.walkHeight()` is the answer wherever no deck covers the point, wading
   * barrier and all. Where a deck does:
   *
   * - **Over water the deck wins outright.** The barrier is a navigation rule
   *   about a river you have no boat for (terrain.js's header), and a bridge is
   *   precisely the thing that answers it. It also sits at 4.0 m, ABOVE every deck
   *   in the dataset, so a plain max() would leave the visitor hovering 1.8 m over
   *   the planks — which is the float docs/LIBERTIES.md L9 records.
   * - **Over land the higher surface wins.** A deck may run BELOW the ground it
   *   crosses: the slough this bridge spans is not modelled in this terrain epoch,
   *   so its deck lies about 0.4 m inside the prairie. Letting the deck win there
   *   would sink a visitor into a hill to walk a bridge over a stream that is not
   *   drawn. The ground is what they can see, so the ground is what they walk.
   */
  function surfaceAt(e, n) {
    let deckY = null;
    for (const d of decks) {
      if (!inside(e, n, d.pts)) continue;
      const y = deckHeightAt(d, e, n);
      if (typeof y === 'number' && (deckY === null || y > deckY)) deckY = y;
    }
    if (deckY === null) return terrain.walkHeight(e, n);
    return terrain.isWater(e, n) ? deckY : Math.max(deckY, terrain.surfaceHeight(e, n));
  }

  state.groundY = surfaceAt(state.e, state.n);
  state.eyeY = state.groundY + WALK.eyeHeight;

  /** T-2943: the passage of `fp` whose lane holds this point and clears the eye, or null. */
  function laneAt(fp, e, n) {
    if (!fp.passages) return null;
    const need = WALK.eyeHeight + HEADROOM_MARGIN_M;
    return fp.passages.find((l) => l.clear >= need && inside(e, n, l.lane)) ?? null;
  }

  /** T-2943: inside a passage, held WALK.radius off its side walls (and nothing else of it). */
  function keepInLane(lane, e, n) {
    for (const [a, b] of lane.walls) {
      const near = nearestOnBoundary(e, n, [a, b]);
      if (!near || near.d >= WALK.radius) continue;
      let dx = e - near.e, dy = n - near.n;
      let len = Math.hypot(dx, dy);
      if (len < 1e-6) { dx = lane.centre[0] - near.e; dy = lane.centre[1] - near.n; len = Math.hypot(dx, dy) || 1; }
      e = near.e + (dx / len) * WALK.radius;
      n = near.n + (dy / len) * WALK.radius;
    }
    return { e, n };
  }

  /** Slide the capsule out of any footprint it has ended up inside. */
  function pushOut(e, n) {
    for (const fp of footprints) {
      const lane = laneAt(fp, e, n);
      if (lane) { ({ e, n } = keepInLane(lane, e, n)); continue; }
      const near = nearestOnBoundary(e, n, fp.pts);
      if (!near) continue;
      const within = inside(e, n, fp.pts);
      if (!within && near.d >= WALK.radius) continue;

      let dx = e - near.e;
      let dy = n - near.n;
      const len = Math.hypot(dx, dy);
      if (len < 1e-6) { dx = 1; dy = 0; }     // standing exactly on an edge
      else { dx /= len; dy /= len; }
      // Inside, that vector points into the building; outside, away from it.
      if (within) { dx = -dx; dy = -dy; }
      e = near.e + dx * WALK.radius;
      n = near.n + dy * WALK.radius;
    }
    return { e, n };
  }

  /** One axis at a time, so you slide along a slope instead of sticking to it. */
  function tryStep(e, n, de, dn) {
    let ok = true;
    const here = surfaceAt(e, n);
    let next = { e, n };

    if (de !== 0) {
      const cand = { e: e + de, n };
      if (surfaceAt(cand.e, cand.n) - here <= WALK.stepUp) next = cand;
      else ok = false;
    }
    if (dn !== 0) {
      const cand = { e: next.e, n: n + dn };
      if (surfaceAt(cand.e, cand.n) - here <= WALK.stepUp) next = cand;
      else ok = false;
    }
    return { ...next, ok };
  }

  return {
    state,
    /** The walk surface (decks included) — exposed for the route planner. */
    surfaceAt,
    get position() { return world.clone(); },
    get enu() { return { e: state.e, n: state.n, y: state.eyeY }; },
    get bearingDeg() { return yawToBearing(state.yaw); },

    /**
     * Put the visitor somewhere. `altitude_m` makes it an AERIAL arrival: the
     * mode flips to free-fly and the eye goes to that height, because an
     * overhead viewpoint you are dropped into on foot is just a viewpoint of
     * some grass.
     */
    teleport({ local_e = state.e, local_n = state.n, yaw_deg = null,
               altitude_m = null, pitch_deg = null } = {}) {
      state.e = local_e;
      state.n = local_n;
      if (yaw_deg !== null) state.yaw = bearingToYaw(yaw_deg);
      if (pitch_deg !== null) {
        state.pitch = Math.max(-WALK.pitchLimit,
          Math.min(WALK.pitchLimit, pitch_deg * DEG));
      } else if (altitude_m === null) {
        // Arriving on foot levels the view. Without this you keep whatever
        // angle you had, so stepping off an aerial viewpoint down to a street
        // corner lands you staring at the cobbles — and, less visibly, aims
        // every crosshair inspection at the ground instead of the building.
        state.pitch = 0;
      }
      state.groundY = surfaceAt(state.e, state.n);
      if (altitude_m !== null) {
        this.setFlying(true);
        state.eyeY = state.groundY + Math.max(FLY.minClearance, altitude_m);
        state.altitude = state.eyeY - state.groundY;
      } else {
        this.setFlying(false);
        state.eyeY = state.groundY + WALK.eyeHeight;
        state.altitude = 0;
      }
      this.apply();
    },

    /** Stand `distance` metres from a world point, looking at it. */
    /**
     * Put the eye back where the current WALK.eyeHeight says it belongs.
     *
     * Only meaningful on foot: in free-fly the eye height is an altitude the
     * visitor is flying, not a stature, and resettling would yank them to the
     * ground mid-flight. Called when the eye-height setting changes, so the
     * slider moves the view under you instead of on the next footstep.
     */
    resettle() {
      if (state.flying) return false;
      state.groundY = surfaceAt(state.e, state.n);
      state.eyeY = state.groundY + WALK.eyeHeight;
      this.apply();
      return true;
    },

    lookAt(target, distance = 26, fromBearingDeg = null) {
      const te = target.x;
      const tn = -target.z;
      const bearing = fromBearingDeg ?? 200;   // stand south-west of the subject
      const rad = bearing * DEG;
      state.e = te + Math.sin(rad) * distance;
      state.n = tn + Math.cos(rad) * distance;
      state.groundY = surfaceAt(state.e, state.n);
      state.eyeY = state.groundY + WALK.eyeHeight;

      const de = te - state.e;
      const dn = tn - state.n;
      state.yaw = bearingToYaw((Math.atan2(de, dn) / DEG + 360) % 360);
      const rise = (target.y || 4) - state.eyeY;
      state.pitch = Math.atan2(rise, Math.hypot(de, dn));
      this.apply();
    },

    /**
     * Enter or leave free-fly.
     *
     * Leaving SNAPS to the ground, which was not the first instinct. Letting
     * the walk path's existing ground-smoothing fly the eye down looked elegant
     * and is wrong at altitude: that term is exponential with a 14/s constant,
     * so it covers 87% of the drop in the first second — from 175 m that is a
     * 150 m/s plummet, and the remaining 13% then crawls for several seconds.
     * Both halves are bad. A rate-limited descent instead is a seven-second
     * cutscene nobody asked for. Snapping is honest and instant: you were
     * above this spot, now you are standing on it.
     */
    setFlying(on) {
      const next = !!on;
      if (next === state.flying) return next;
      state.flying = next;
      state.blocked = false;
      if (!next) {
        // Landing inside a building is possible — nothing pushed you out while
        // you were in the air — so clear the footprints before settling.
        const clear = pushOut(state.e, state.n);
        state.e = clear.e;
        state.n = clear.n;
        state.groundY = surfaceAt(state.e, state.n);
        state.eyeY = state.groundY + WALK.eyeHeight;
        state.altitude = 0;
        this.apply();
      }
      return state.flying;
    },

    /**
     * Free movement. Deliberately does NOT call tryStep or pushOut: the
     * step-up rule and the footprint capsule are the two things that make
     * walking honest, and they are exactly what you are asking to leave.
     * Terrain is still a floor — you may skim the prairie, not tunnel it.
     */
    updateFly(dt, intent) {
      let f = intent.forward;
      let s = intent.strafe;
      const mag = Math.hypot(f, s);
      if (mag > 1) { f /= mag; s /= mag; }

      state.groundY = surfaceAt(state.e, state.n);
      const gain = FLY.altitudeGain(state.eyeY - state.groundY);
      const base = intent.sprint ? FLY.sprintSpeed : FLY.speed;
      const speed = base * gain;

      // Forward follows the LOOK direction, pitch included — the whole point is
      // to nose up and rise away from the town, or dive back into it. Strafe
      // stays level, so sliding sideways for a better angle does not drift you
      // up or down without asking.
      const cosP = Math.cos(state.pitch);
      const sinY = Math.sin(state.yaw);
      const cosY = Math.cos(state.yaw);
      const fx = -sinY * cosP, fz = -cosY * cosP, fy = Math.sin(state.pitch);
      const rx = cosY, rz = -sinY;

      const dx = (fx * f + rx * s) * speed * dt;
      const dz = (fz * f + rz * s) * speed * dt;
      const dy = fy * f * speed * dt + intent.rise * FLY.riseSpeed * gain * dt;

      state.e += dx;
      state.n += -dz;                      // world -z is north
      state.eyeY += dy;

      const floor = surfaceAt(state.e, state.n) + FLY.minClearance;
      state.eyeY = Math.max(floor, Math.min(FLY.maxAltitude, state.eyeY));
      state.groundY = surfaceAt(state.e, state.n);
      state.altitude = state.eyeY - state.groundY;
      state.speed = Math.hypot(dx, dz, dy) / Math.max(dt, 1e-6);

      this.apply();
    },

    /** Write the camera. The ONLY place the camera transform is authored. */
    apply() {
      enuToWorld(state.e, state.n, state.eyeY + state.bob, world);
      camera.position.copy(world);
      euler.set(state.pitch, state.yaw, 0, 'YXZ');
      camera.quaternion.setFromEuler(euler);
    },

    /**
     * @param {number} dt seconds
     * @param {object} intent  the shared intent object
     */
    update(dt, intent) {
      state.yaw += intent.yawDelta;
      state.pitch = Math.max(-WALK.pitchLimit,
        Math.min(WALK.pitchLimit, state.pitch + intent.pitchDelta));
      intent.clearLook();

      if (intent.flying !== state.flying) this.setFlying(intent.flying);
      if (state.flying) { this.updateFly(dt, intent); return; }

      let f = intent.forward;
      let s = intent.strafe;
      const mag = Math.hypot(f, s);
      if (mag > 1) { f /= mag; s /= mag; }

      const speed = intent.sprint ? WALK.sprintSpeed : WALK.speed;
      state.speed = Math.hypot(f, s) * speed;

      if (state.speed > 0) {
        // Camera-relative, flattened to the ground plane.
        const sinY = Math.sin(state.yaw);
        const cosY = Math.cos(state.yaw);
        const fx = -sinY, fz = -cosY;       // forward in world XZ
        const rx = cosY, rz = -sinY;        // right in world XZ
        const dx = (fx * f + rx * s) * speed * dt;
        const dz = (fz * f + rz * s) * speed * dt;

        const step = tryStep(state.e, state.n, dx, -dz);   // world -z is north
        state.blocked = !step.ok;
        state.e = step.e;
        state.n = step.n;
      } else {
        state.blocked = false;
      }

      // Every frame, not only while walking: a building whose placement moves
      // under a standing visitor should push them out, not swallow them.
      const clear = pushOut(state.e, state.n);
      state.e = clear.e;
      state.n = clear.n;

      // Walking is a constraint, not a camera animation: the eye stays exactly
      // WALK.eyeHeight above the SAME bilinear heightfield that built the mesh.
      // The old exponential easing lagged behind on every rise and fall, so the
      // visitor visibly entered a bank while climbing and floated while coming
      // down.  Bilinear sampling already makes ordinary terrain continuous;
      // the 0.35 m step rule above is the only place an actual step may occur.
      state.groundY = surfaceAt(state.e, state.n);
      state.eyeY = state.groundY + WALK.eyeHeight;
      state.altitude = 0;

      this.apply();
    },
  };
}
