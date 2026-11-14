// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Teams that give way to each other where their roads cross (Kevin, 2026-11-13, of the
 * 1904 carriages: "they should potentially cross paths and one will wait for the other to
 * cross while they proceed").
 *
 * WHERE: before anything moves, every pair of a scene's circuits is swept at half-metre
 * steps, each step the team's whole footprint (its row's `envelope_local_xz_m`, the
 * vehicle, team and pole, plus a margin) at that place on the road. Wherever two
 * footprints can overlap, that stretch of each road is a CONFLICT ZONE of the pair: an
 * intersection where one turns across the other, or a corner where both sweep wide.
 *
 * WHO GOES: on each circuit, zones that lie close together (with any partner) are taken as
 * one CLUSTER, so a team never stops between two of them. A team nearing a cluster asks
 * for every zone in it at once; it gets them only if no other team holds any of their
 * partners, and then holds them until it has driven clear of the cluster's end. Otherwise
 * it pulls up at the cluster's edge and waits. First to ask goes; the other waits for it to
 * cross, then proceeds.
 *
 * A waiting team holds nothing, and a team holding a cluster is never made to wait inside
 * it, so the scheme cannot deadlock (no hold-and-wait), whatever the number of teams.
 * A team stopped for another reason (a visitor in the road) keeps what it holds, and the
 * other simply waits longer, as a coachman would.
 *
 * Planar only: the zones read the routes and the envelopes, never the ground or models.
 */

const wrap = (n, total) => ((n % total) + total) % total;

/** The team's footprint at a route distance: four corners in ENU, and their bounds. */
export function footprintAt(route, row, s, margin) {
  const rear = route.at(s), yaw = rear.yaw, c = Math.cos(yaw), sn = Math.sin(yaw);
  const ra = row.root_ahead_of_rear_axle_m ?? 0;
  // The vehicle root, ahead of the rear axle (transport-loop.js poseAt).
  const e = rear.e + sn * ra, n = rear.n - c * ra;
  const [x0, z0, x1, z1] = row.envelope_local_xz_m;
  const corners = [[x0 - margin, z0 - margin], [x1 + margin, z0 - margin], [x1 + margin, z1 + margin], [x0 - margin, z1 + margin]]
    .map(([x, z]) => [e + c * x + sn * z, n + sn * x - c * z]);
  const es = corners.map(p => p[0]), ns = corners.map(p => p[1]);
  return { corners, w: Math.min(...es), e: Math.max(...es), s: Math.min(...ns), n: Math.max(...ns) };
}

/** Separating-axis overlap of two convex quadrilaterals. */
export function overlaps(a, b) {
  if (a.e < b.w || b.e < a.w || a.n < b.s || b.n < a.s) return false;
  for (const poly of [a.corners, b.corners]) {
    for (let i = 0; i < 4; i++) {
      const p = poly[i], q = poly[(i + 1) % 4], ax = q[1] - p[1], ay = p[0] - q[0];
      let amin = Infinity, amax = -Infinity, bmin = Infinity, bmax = -Infinity;
      for (const [x, y] of a.corners) { const d = x * ax + y * ay; amin = Math.min(amin, d); amax = Math.max(amax, d); }
      for (const [x, y] of b.corners) { const d = x * ax + y * ay; bmin = Math.min(bmin, d); bmax = Math.max(bmax, d); }
      if (amax < bmin || bmax < amin) return false;
    }
  }
  return true;
}

/** Runs of flagged sample indices on a closed route, joined across small gaps and across 0. */
function runsOf(flags, gap) {
  const count = flags.length, on = [];
  for (let i = 0; i < count; i++) if (flags[i]) on.push(i);
  if (!on.length) return [];
  if (on.length === count) return [[0, count - 1]];
  const runs = [];
  let start = on[0], last = on[0];
  for (const i of on.slice(1)) {
    if (i - last > gap) { runs.push([start, last]); start = i; }
    last = i;
  }
  runs.push([start, last]);
  // Across the route's start: the last run joins the first, its end passing the count.
  if (runs.length > 1 && runs[0][0] + count - runs.at(-1)[1] <= gap) {
    const tail = runs.pop(); runs[0] = [tail[0], runs[0][1] + count];
  }
  return runs;
}
const runHas = (run, i, count) => (i >= run[0] && i <= run[1]) || (i + count >= run[0] && i + count <= run[1]);

/**
 * Every conflict zone between the circuits. `circuits` are { id, row, route }. Returns
 * zones { id, a, b, at: { [id]: [start_m, end_m] } } (an end may pass the route's length).
 */
export function conflictZones(circuits, { step_m = .5, margin_m = .6, gap_samples = 4 } = {}) {
  const sampled = circuits.map(circuit => {
    const count = Math.max(8, Math.ceil(circuit.route.length / step_m)), step = circuit.route.length / count;
    const prints = Array.from({ length: count }, (_, i) => footprintAt(circuit.route, circuit.row, i * step, margin_m));
    return { ...circuit, count, step, prints };
  });
  const zones = [];
  for (let i = 0; i < sampled.length; i++) for (let j = i + 1; j < sampled.length; j++) {
    const A = sampled[i], B = sampled[j];
    // A coarse grid over B's footprints keeps the pair sweep near linear.
    const cell = 8, grid = new Map(), key = (x, y) => `${x},${y}`;
    B.prints.forEach((p, k) => {
      for (let x = Math.floor(p.w / cell); x <= Math.floor(p.e / cell); x++)
        for (let y = Math.floor(p.s / cell); y <= Math.floor(p.n / cell); y++) {
          const k2 = key(x, y); if (!grid.has(k2)) grid.set(k2, []); grid.get(k2).push(k);
        }
    });
    const pairs = [], flagA = new Uint8Array(A.count), flagB = new Uint8Array(B.count);
    A.prints.forEach((p, ka) => {
      const seen = new Set();
      for (let x = Math.floor(p.w / cell); x <= Math.floor(p.e / cell); x++)
        for (let y = Math.floor(p.s / cell); y <= Math.floor(p.n / cell); y++) for (const kb of grid.get(key(x, y)) ?? []) {
          if (seen.has(kb)) continue; seen.add(kb);
          if (overlaps(p, B.prints[kb])) { pairs.push([ka, kb]); flagA[ka] = 1; flagB[kb] = 1; }
        }
    });
    if (!pairs.length) continue;
    const runsA = runsOf(flagA, gap_samples), runsB = runsOf(flagB, gap_samples);
    // One zone for each stretch of A and stretch of B whose footprints meet.
    const met = new Map();
    for (const [ka, kb] of pairs) {
      const ra = runsA.findIndex(r => runHas(r, ka, A.count)), rb = runsB.findIndex(r => runHas(r, kb, B.count));
      met.set(`${ra}:${rb}`, [ra, rb]);
    }
    for (const [ra, rb] of met.values()) {
      const a = runsA[ra], b = runsB[rb];
      zones.push({ id: `${A.id}|${B.id}|${zones.length}`, a: A.id, b: B.id, at: {
        [A.id]: [a[0] * A.step, (a[1] + 1) * A.step], [B.id]: [b[0] * B.step, (b[1] + 1) * B.step] } });
    }
  }
  return zones;
}

/** A circuit's zones gathered into clusters: zones closer than `join_m` are one cluster. */
export function clustersFor(id, length, zones, { join_m = 14 } = {}) {
  const mine = zones.filter(z => z.at[id]).map(z => ({ start: z.at[id][0], end: z.at[id][1], ids: [z.id] }))
    .sort((p, q) => p.start - q.start);
  const out = [];
  for (const z of mine) {
    const last = out.at(-1);
    if (last && z.start - last.end <= join_m) { last.end = Math.max(last.end, z.end); last.ids.push(...z.ids); }
    else out.push({ ...z, ids: [...z.ids] });
  }
  // Across the route's start.
  if (out.length > 1 && out[0].start + length - out.at(-1).end <= join_m) {
    const tail = out.pop();
    out[0] = { start: tail.start, end: Math.max(tail.end, out[0].end + length), ids: [...tail.ids, ...out[0].ids] };
  }
  return out.map(c => ({ ...c, start: wrap(c.start, length), end: wrap(c.start, length) + (c.end - c.start) }));
}

/**
 * The crossing keeper for one scene's circuits. `gateFor(id)` is what a transport loop
 * asks each step (`allow(distance, ds)` → the metres it may advance; `moved(ds)` after).
 */
export function createCrossings(circuits, options = {}) {
  const { claim_m = 9, ...zoneOptions } = options;
  const zones = conflictZones(circuits, zoneOptions);
  const holder = new Map(); // zone id -> circuit id holding it
  const state = new Map(circuits.map(c => [c.id, { id: c.id, length: c.route.length,
    clusters: clustersFor(c.id, c.route.length, zones, options), claim: null, waitingFor: null, waits: 0 }]));
  const partnersOf = ids => ids.map(z => holder.get(z)).filter(Boolean);
  const take = (st, cluster, remaining) => {
    for (const z of cluster.ids) holder.set(z, st.id);
    st.claim = { cluster, remaining }; st.waitingFor = null;
  };
  const release = st => {
    if (!st.claim) return;
    for (const z of st.claim.cluster.ids) if (holder.get(z) === st.id) holder.delete(z);
    st.claim = null;
  };
  const free = (st, cluster) => partnersOf(cluster.ids).filter(h => h !== st.id);
  const gate = id => {
    const st = state.get(id);
    if (!st) return null;
    let primed = false;
    return {
      allow(distance, ds) {
        if (!st.clusters.length) return ds;
        if (!primed) {
          primed = true;
          // A team that starts (or is restored) inside a cluster takes it, so it never stops there.
          for (const c of st.clusters) {
            const into = wrap(distance - c.start, st.length);
            if (into < c.end - c.start && !st.claim) { take(st, c, c.end - c.start - into); }
          }
        }
        if (st.claim) return ds;
        let next = null, ahead = Infinity;
        for (const c of st.clusters) {
          const a = wrap(c.start - distance, st.length);
          if (a < ahead) { ahead = a; next = c; }
        }
        if (!next || ahead > claim_m + ds) { st.waitingFor = null; return ds; }
        const others = free(st, next);
        if (!others.length) { take(st, next, ahead + (next.end - next.start)); return ds; }
        if (st.waitingFor !== others[0]) st.waits++;
        st.waitingFor = others[0];
        // Pull up at the cluster's edge.
        return Math.max(0, Math.min(ds, ahead - .05));
      },
      moved(ds) {
        if (!st.claim || !(ds > 0)) return;
        st.claim.remaining -= ds;
        if (st.claim.remaining <= 0) release(st);
      },
      /** Let go of everything (the team is gone: disposed, a tier dropped it). */
      drop() { release(st); st.waitingFor = null; },
      get waitingFor() { return st.waitingFor; },
      snapshot() { return { holding: st.claim ? [...st.claim.cluster.ids] : [], waiting_for: st.waitingFor, waits: st.waits }; },
    };
  };
  return { zones, state, gateFor: gate,
    snapshot() { return Object.fromEntries([...state.values()].map(st => [st.id, {
      clusters: st.clusters.map(c => [Math.round(c.start * 10) / 10, Math.round(c.end * 10) / 10]),
      holding: st.claim ? [...st.claim.cluster.ids] : [], waiting_for: st.waitingFor, waits: st.waits }])); } };
}
