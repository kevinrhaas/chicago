// SPDX-License-Identifier: GPL-3.0-or-later
/** T-3792. Hair quality and secondary motion, independent of bodies and photographs.
 * Geometry remains rooted and skinned by human-hair.js. This module budgets the
 * optional near card draws and motion work; it never hides a person or their base cap.
 * Light keeps the existing static cap/tail silhouette. All motion is reconstructed.
 */
export const HAIR_QUALITY = Object.freeze({
  light: Object.freeze({ heads: 0, triangles: 0, distance: 0, motion_m: 0 }),
  // All optional near scalp/facial cards share this bound. Existing LOD1 is
  // about 5,400 scalp triangles plus facial cards per head.
  balanced: Object.freeze({ heads: 12, triangles: 72000, distance: 20, motion_m: .002 }),
  // Existing LOD0 can spend five segments on each of 2,400 cards. Keep a crowd
  // below 220k near-card triangles, rather than giving every close head that cost.
  full: Object.freeze({ heads: 16, triangles: 220000, distance: 24, motion_m: .008 }),
});

const finite = (n, fallback = 0) => Number.isFinite(n) ? n : fallback;
const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

/** Exact critically damped spring for a constant target over a frame.
 * No explicit-Euler instability at low frame rates, substeps or frame allocations.
 */
export class HairSpring {
  constructor({ frequency = 4, limit = .008 } = {}) {
    this.omega = 2 * Math.PI * clamp(finite(frequency, 4), .5, 20);
    this.limit = Math.max(0, finite(limit));
    this.reset();
  }
  reset() { this.x = this.z = this.vx = this.vz = 0; }
  advance(dt, targetX, targetZ) {
    dt = clamp(finite(dt), 0, 1);
    if (!dt) return this;
    targetX = finite(targetX); targetZ = finite(targetZ);
    const r = Math.hypot(targetX, targetZ), scale = r > this.limit ? this.limit / r : 1;
    targetX *= scale; targetZ *= scale;
    const w = this.omega, decay = Math.exp(-w * dt);
    const x = this.x - targetX, z = this.z - targetZ;
    const cx = this.vx + w * x, cz = this.vz + w * z;
    this.x = targetX + (x + cx * dt) * decay;
    this.z = targetZ + (z + cz * dt) * decay;
    this.vx = (this.vx - w * cx * dt) * decay;
    this.vz = (this.vz - w * cz * dt) * decay;
    const length = Math.hypot(this.x, this.z);
    if (length > this.limit) {
      this.x *= this.limit / length; this.z *= this.limit / length;
      // A constrained tip cannot keep accelerating farther through its limit.
      const outward = this.vx * this.x + this.vz * this.z;
      if (outward > 0 && this.limit > 0) {
        this.vx -= outward * this.x / (this.limit * this.limit);
        this.vz -= outward * this.z / (this.limit * this.limit);
      }
    }
    return this;
  }
}

/** One near hair layer. The uniform is owned by this body, never shared by name. */
export class HairDynamics {
  constructor({ uniform, triangles, addedTriangles = 0, setVisible, tied = true, phase = 0 } = {}) {
    this.uniform = uniform;
    this.triangles = Math.max(0, finite(triangles));
    this.addedTriangles = Math.min(this.triangles, Math.max(0, finite(addedTriangles)));
    this.setVisible = setVisible;
    this.tied = tied;
    this.phase = finite(phase);
    this.spring = new HairSpring({ frequency: tied ? 7 : 3.5 });
    this.time = 0; this.enabled = true; this.disposed = false; this.initialized = false;
    this.previousX = this.previousZ = this.previousHeading = this.velocityX = this.velocityZ = 0;
  }
  enable(on) {
    if (this.disposed) return;
    on = !!on;
    if (on !== this.enabled) this.setVisible?.(on);
    this.enabled = on;
    if (!on) { this.spring.reset(); this.initialized = false; }
    this.write();
  }
  write() {
    const v = this.uniform?.value;
    if (v) { v.x = this.spring.x; v.y = this.spring.z; v.z = this.time; v.w = this.enabled ? 1 : 0; }
  }
  takePoseFrom(previous) {
    if (!previous || previous.disposed || this.disposed) return;
    for (const key of ['time','initialized','previousX','previousZ','previousHeading','velocityX','velocityZ']) this[key] = previous[key];
    for (const key of ['x','z','vx','vz']) this.spring[key] = previous.spring[key];
    this.write();
  }
  advance(dt, actor, quality, windX = .35, windZ = .12) {
    if (this.disposed || !this.enabled) return;
    dt = clamp(finite(dt), 0, .25);
    if (!dt) return;
    // Seated drivers have a moving vehicle parent. Sample its complete world
    // transform as well as the actor's own transform; no vector is allocated.
    actor.root?.updateWorldMatrix?.(true, false);
    const world = actor.root?.matrixWorld?.elements;
    const x = finite(world?.[12], finite(actor.root?.position?.x));
    const z = finite(world?.[14], finite(actor.root?.position?.z));
    const heading = world && Math.hypot(world[8], world[10]) > 1e-8 ? Math.atan2(world[8], world[10])
      : finite(actor.root?.rotation?.y, finite(actor.heading) * Math.PI / 180);
    let ax = 0, az = 0, turn = 0;
    const dx = x - this.previousX, dz = z - this.previousZ;
    if (this.initialized && dt > 0 && Math.hypot(dx, dz) < 1 && dt < .2) {
      const vx = dx / dt, vz = dz / dt;
      ax = clamp((vx - this.velocityX) / dt, -12, 12);
      az = clamp((vz - this.velocityZ) / dt, -12, 12);
      turn = clamp(Math.atan2(Math.sin(heading - this.previousHeading), Math.cos(heading - this.previousHeading)) / dt, -4, 4);
      this.velocityX = vx; this.velocityZ = vz;
    } else { this.velocityX = this.velocityZ = 0; this.spring.reset(); }
    this.previousX = x; this.previousZ = z; this.previousHeading = heading; this.initialized = true;
    this.time = (this.time + dt) % 4096;
    const s = Math.sin(heading), c = Math.cos(heading);
    // Tied updos and short cuts respond far less than loose hair. Wind is a small
    // declared reconstruction until the weather supplies its own vector.
    const gust = .75 + .25 * Math.sin(this.time * 1.7 + this.phase);
    const side = ((finite(windX) * c - finite(windZ) * s) * .0012 * gust - (ax * c - az * s) * .0002 - turn * .00035);
    const back = ((finite(windX) * s + finite(windZ) * c) * .0012 * gust - (ax * s + az * c) * .0002);
    this.spring.limit = quality.motion_m * (this.tied ? .25 : 1);
    this.spring.advance(dt, side, back); this.write();
  }
  dispose() {
    if (this.disposed) return;
    this.enable(false); this.disposed = true; this.setVisible = null; this.uniform = null;
  }
}

/** Nearest hair layers get the shared budget. Body silhouettes always remain.
 * Only already-loaded near layers are sorted; geometry is not rebuilt per frame.
 */
export class HairBudget {
  constructor() {
    this.actors = new Set();
    this.candidates = [];
    this.stats = { detail: 'light', heads: 0, triangles: 0, addedTriangles: 0, candidates: 0 };
  }
  update(actors, dt, detail = 'balanced') {
    actors ??= this.actors;
    const q = HAIR_QUALITY[detail] ?? HAIR_QUALITY.balanced, list = this.candidates;
    list.length = 0;
    for (const a of actors) {
      const hair = a.hair?.runtime;
      if (!hair || hair.disposed) continue;
      if (a.disposed || a.indoors || !a.root?.visible || !a.inRange || !(a.distance <= q.distance)) { hair.enable(false); continue; }
      list.push(a);
    }
    // A small incumbent preference prevents a stationary group alternating its
    // hair detail when two camera distances jitter around the same value.
    list.sort((a, b) => (a.distance - (a.hair.runtime.enabled ? .35 : 0)) - (b.distance - (b.hair.runtime.enabled ? .35 : 0)) || String(a.id).localeCompare(String(b.id)));
    let heads = 0, triangles = 0, addedTriangles = 0;
    for (const a of list) {
      const h = a.hair.runtime, admit = heads < q.heads && triangles + h.triangles <= q.triangles;
      h.enable(admit);
      if (admit) { heads++; triangles += h.triangles; addedTriangles += h.addedTriangles; h.advance(dt, a, q); }
    }
    Object.assign(this.stats, { detail, heads, triangles, addedTriangles, candidates: list.length });
    return this.stats;
  }
  register(actor) { this.actors.add(actor); }
  unregister(actor) {
    this.actors.delete(actor);
    const index = this.candidates.indexOf(actor);
    if (index >= 0) this.candidates.splice(index, 1);
    if (!this.actors.size) Object.assign(this.stats, { heads: 0, triangles: 0, addedTriangles: 0, candidates: 0 });
  }
  dispose() {
    for (const a of this.actors) a.hair?.runtime?.enable(false);
    this.candidates.length = 0; this.actors.clear();
    Object.assign(this.stats, { heads: 0, triangles: 0, addedTriangles: 0, candidates: 0 });
  }
}
