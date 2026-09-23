/**
 * road_joint_probe.mjs — T-0184's instrument, in one place.
 *
 * A function and nothing else, for the same reason `drawn_placement_census.mjs`
 * is: `tools/measure_road_joints.mjs` runs it as an instrument and
 * `tools/smoke_renderer.mjs` runs it as a release gate, and they run THE SAME
 * CODE rather than two readings of the same idea. It is serialised into the page
 * with `JOINT_PROBE.toString()`, so it may close over NOTHING from this module:
 * everything it needs comes off `window.__chicago4d` or its one argument.
 *
 * THE QUESTION. Where a street's centreline bends, does the drawn ribbon cover
 * the ground the street's own record claims? "The ground it claims" is the
 * NOMINAL RIBBON — every point within `track_width_m / 2` of the drawn
 * centreline. That is not a definition invented for this gate: it is the same
 * point-to-polyline distance `streets.js` already answers `hitsAt`,
 * `blocksGrowth` and the flora-clearing corridor with, so at a bend the sward is
 * cleared in a rounded corner and any ribbon that fails to reach it leaves bare
 * ground rather than grass.
 *
 * THE PROBE. A 2 cm plan lattice over a disc of `half + pad` around the bend.
 * Each point is classified twice — is it inside the nominal ribbon, and is it
 * inside any drawn street triangle in plan — and the uncovered count times the
 * cell area is an area in square metres. Coverage is asked of EVERY street, not
 * only the bending one, because a crossing street's roadway is roadway: L178's
 * 0.30 m2 at the Dearborn corner is what is left after South Water Street's own
 * 10.5 m ribbon has covered half of the wedge.
 *
 * THE CONTROL IS BUILT IN, AND IT RUNS ON EVERY BUILD. An instrument that has
 * only ever seen one value has demonstrated nothing (R-A1), and a joint gate on
 * a fixed build would read zero forever whether or not it could see anything.
 * So the same lattice is also probed against a REFERENCE ribbon built here from
 * the committed centrelines under the rule that shipped before T-0184 — every
 * panel square to its own chord, same 2.25 m sampling, same waterline trim, same
 * sliver drop. The reference is not a paraphrase of the current module; it is
 * the old rule, kept deliberately, so `square.uncovered` is the wedge the fix
 * closed and `drawn.uncovered` is what is left. If the reference ever reads
 * zero, the probe is not an instrument and the runner says so.
 *
 * Drape refinement does not enter: a refined panel subdivides the same plan
 * quad, so the ribbon's plan footprint is identical at every level and this
 * measurement is a plan measurement.
 *
 * `overhangM` is the census question asked locally — the furthest any drawn
 * vertex near the bend stands beyond its own street's half-width, computed with
 * `drawn_placement_census.mjs`'s exact arithmetic. A mitred corner necessarily
 * stands `half * (sec(turn/2) - 1)` past the vertex, so this is the number that
 * says whether closing a joint has pushed the ribbon off its own record.
 */
export const JOINT_PROBE = (opts) => {
  const a = window.__chicago4d;
  const CELL = opts.cellM;
  const PAD = opts.padM;
  const TURN_EPS = (opts.turnEpsDeg * Math.PI) / 180;
  const ONLY = opts.only || null;
  const CLIP_STEPS = 6;
  const STEP_M = 2.25;
  const MIN_PANEL_W_M = 1.0;

  const segDist = (e, n, A, B) => {
    const de = B[0] - A[0];
    const dn = B[1] - A[1];
    const l2 = de * de + dn * dn || 1e-9;
    let t = ((e - A[0]) * de + (n - A[1]) * dn) / l2;
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    return Math.hypot(e - (A[0] + de * t), n - (A[1] + dn * t));
  };
  const lineDist = (e, n, line) => {
    let best = Infinity;
    for (let i = 1; i < line.length; i++) {
      const d = segDist(e, n, line[i - 1], line[i]);
      if (d < best) best = d;
    }
    return best;
  };
  const lineOf = (rec) => rec.drawn || rec.path;
  const halfOf = (rec) => (rec.track_width_m == null ? 6 : rec.track_width_m) * 0.5;
  // The census's own question: how far past ITS OWN street's half-width does a
  // drawn point stand, taking the most generous street in town.
  const beyondHalf = (e, n) => {
    let best = Infinity;
    for (const rec of a.streets.records) {
      const b = rec.bounds;
      if (b && (e < b.e0 || e > b.e1 || n < b.n0 || n > b.n1)) continue;
      const d = lineDist(e, n, lineOf(rec)) - halfOf(rec);
      if (d < best) best = d;
    }
    return best;
  };

  const boxed = (t) => {
    const e0 = Math.min(t[0][0], t[1][0], t[2][0]);
    const e1 = Math.max(t[0][0], t[1][0], t[2][0]);
    const n0 = Math.min(t[0][1], t[1][1], t[2][1]);
    const n1 = Math.max(t[0][1], t[1][1], t[2][1]);
    return [t[0], t[1], t[2], e0, e1, n0, n1];
  };

  // ---- the ribbon as DRAWN, read back out of the scene in plan ----
  const drawnTris = [];
  const drawnVerts = [];
  a.streets.group.traverse((o) => {
    const pos = o.geometry && o.geometry.getAttribute && o.geometry.getAttribute('position');
    const idx = o.geometry && o.geometry.index;
    if (!pos || !idx) return;
    o.updateWorldMatrix(true, false);
    const m = o.matrixWorld.elements;
    const plan = [];
    for (let i = 0; i < pos.count; i++) {
      const vx = pos.getX(i);
      const vy = pos.getY(i);
      const vz = pos.getZ(i);
      const e = m[0] * vx + m[4] * vy + m[8] * vz + m[12];
      const z = m[2] * vx + m[6] * vy + m[10] * vz + m[14];
      plan.push([e, -z]);
    }
    for (const p of plan) drawnVerts.push(p);
    for (let i = 0; i < idx.count; i += 3) {
      drawnTris.push(boxed([plan[idx.getX(i)], plan[idx.getX(i + 1)], plan[idx.getX(i + 2)]]));
    }
  });

  // ---- the reference ribbon: square joints, the rule that shipped before ----
  // `emitted` is the by-product that makes the nominal ribbon honest: the
  // chords the module is ALLOWED to paint, after the centreline water test and
  // the sliver drop. Ground inside the buffer of a chord the module refuses is
  // not a joint's wedge, it is R-BUG4's "clip, don't paint a ford" doing its
  // job, and counting it here would bury the thing being measured. It buries a
  // lot: North Water Street's own committed line runs inside the water mask
  // from E 330 to E 576, so three of its bends sit on ground no ribbon may be
  // drawn on at all (33.8 m2 apiece, filed as its own ticket).
  const emitted = new Map();
  const squareTris = [];
  for (const rec of a.streets.records) {
    emitted.set(rec.id, []);
    const half = halfOf(rec);
    const line = lineOf(rec);
    const pts = [];
    for (let i = 1; i < line.length; i++) {
      const A = line[i - 1];
      const B = line[i];
      const d = Math.hypot(B[0] - A[0], B[1] - A[1]);
      const c = Math.max(1, Math.ceil(d / STEP_M));
      for (let j = 0; j < c; j++) {
        if (!pts.length) pts.push([A[0], A[1]]);
        const t = (j + 1) / c;
        pts.push([A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t]);
      }
    }
    for (let i = 1; i < pts.length; i++) {
      const A = pts[i - 1];
      const B = pts[i];
      const de = B[0] - A[0];
      const dn = B[1] - A[1];
      const L = Math.hypot(de, dn);
      if (L < 1e-5) continue;
      if (a.terrain.isWater(A[0], A[1]) || a.terrain.isWater(B[0], B[1])) continue;
      const ue = -dn / L;
      const un = de / L;
      const reach = (e0, n0, se, sn) => {
        if (!a.terrain.isWater(e0 + se * half, n0 + sn * half)) return half;
        let lo = 0;
        let hi = half;
        for (let k = 0; k < CLIP_STEPS; k++) {
          const mid = (lo + hi) * 0.5;
          if (a.terrain.isWater(e0 + se * mid, n0 + sn * mid)) hi = mid;
          else lo = mid;
        }
        return lo;
      };
      const aL = reach(A[0], A[1], ue, un);
      const aR = reach(A[0], A[1], -ue, -un);
      const bL = reach(B[0], B[1], ue, un);
      const bR = reach(B[0], B[1], -ue, -un);
      if (aL + aR < MIN_PANEL_W_M || bL + bR < MIN_PANEL_W_M) continue;
      emitted.get(rec.id).push([A, B]);
      const p00 = [A[0] + ue * aL, A[1] + un * aL];
      const p01 = [A[0] - ue * aR, A[1] - un * aR];
      const p10 = [B[0] + ue * bL, B[1] + un * bL];
      const p11 = [B[0] - ue * bR, B[1] - un * bR];
      squareTris.push(boxed([p00, p10, p01]), boxed([p01, p10, p11]));
    }
  }

  const inside = (t, e, n) => {
    const s = (A, B) => (B[0] - A[0]) * (n - A[1]) - (B[1] - A[1]) * (e - A[0]);
    const d0 = s(t[0], t[1]);
    const d1 = s(t[1], t[2]);
    const d2 = s(t[2], t[0]);
    return !((d0 < 0 || d1 < 0 || d2 < 0) && (d0 > 0 || d1 > 0 || d2 > 0));
  };
  const near = (list, e0, e1, n0, n1) => list.filter(
    (t) => t[4] >= e0 && t[3] <= e1 && t[6] >= n0 && t[5] <= n1,
  );

  // ---- the joints ----
  const joints = [];
  for (const rec of a.streets.records) {
    const line = lineOf(rec);
    const half = halfOf(rec);
    for (let i = 1; i < line.length - 1; i++) {
      const A = line[i - 1];
      const P = line[i];
      const B = line[i + 1];
      const t1 = Math.atan2(P[1] - A[1], P[0] - A[0]);
      const t2 = Math.atan2(B[1] - P[1], B[0] - P[0]);
      let turn = t2 - t1;
      while (turn > Math.PI) turn -= 2 * Math.PI;
      while (turn < -Math.PI) turn += 2 * Math.PI;
      if (Math.abs(turn) < TURN_EPS) continue;
      if (ONLY && !ONLY.some((o) => o.street === rec.id && o.index === i)) continue;
      const R = half + PAD;
      const e0 = P[0] - R;
      const e1 = P[0] + R;
      const n0 = P[1] - R;
      const n1 = P[1] + R;
      const dt = near(drawnTris, e0, e1, n0, n1);
      const st = near(squareTris, e0, e1, n0, n1);
      const chords = emitted.get(rec.id)
        .filter((c) => Math.min(c[0][0], c[1][0]) <= e1 && Math.max(c[0][0], c[1][0]) >= e0
          && Math.min(c[0][1], c[1][1]) <= n1 && Math.max(c[0][1], c[1][1]) >= n0);
      let buffer = 0;
      let nominal = 0;
      let drawnGap = 0;
      let squareGap = 0;
      for (let e = e0 + CELL * 0.5; e < e1; e += CELL) {
        for (let n = n0 + CELL * 0.5; n < n1; n += CELL) {
          if (Math.hypot(e - P[0], n - P[1]) > R) continue;
          if (lineDist(e, n, line) > half) continue;
          buffer++;
          // The ribbon may only be painted along a chord the module emitted,
          // and never on water.
          let paintable = false;
          for (let k = 0; k < chords.length && !paintable; k++) {
            paintable = segDist(e, n, chords[k][0], chords[k][1]) <= half;
          }
          if (!paintable || a.terrain.isWater(e, n)) continue;
          nominal++;
          let hit = false;
          for (let k = 0; k < dt.length && !hit; k++) {
            const t = dt[k];
            if (e < t[3] || e > t[4] || n < t[5] || n > t[6]) continue;
            hit = inside(t, e, n);
          }
          if (!hit) drawnGap++;
          let sq = false;
          for (let k = 0; k < st.length && !sq; k++) {
            const t = st[k];
            if (e < t[3] || e > t[4] || n < t[5] || n > t[6]) continue;
            sq = inside(t, e, n);
          }
          if (!sq) squareGap++;
        }
      }
      let overhang = -Infinity;
      let overhangAt = null;
      for (const v of drawnVerts) {
        if (v[0] < e0 || v[0] > e1 || v[1] < n0 || v[1] > n1) continue;
        const d = beyondHalf(v[0], v[1]);
        if (d > overhang) { overhang = d; overhangAt = [+v[0].toFixed(3), +v[1].toFixed(3)]; }
      }
      const cell = CELL * CELL;
      joints.push({
        street: rec.id,
        index: i,
        at: [+P[0].toFixed(2), +P[1].toFixed(2)],
        turnDeg: +((turn * 180) / Math.PI).toFixed(2),
        halfM: half,
        // The closed form the ticket and L178 quote: the sector a square joint
        // leaves open on the outside of the turn, apex on the centreline.
        sectorM2: +((half * half * Math.abs(turn)) / 2).toFixed(3),
        bufferM2: +(buffer * cell).toFixed(3),
        nominalM2: +(nominal * cell).toFixed(3),
        drawnGapM2: +(drawnGap * cell).toFixed(3),
        squareGapM2: +(squareGap * cell).toFixed(3),
        overhangM: Number.isFinite(overhang) ? +overhang.toFixed(3) : null,
        overhangAt,
      });
    }
  }

  const sum = (k) => +joints.reduce((x, j) => x + j[k], 0).toFixed(3);
  return {
    cellM: CELL,
    padM: PAD,
    turnEpsDeg: opts.turnEpsDeg,
    triangles: drawnTris.length,
    referenceTriangles: squareTris.length,
    joints,
    totals: {
      joints: joints.length,
      // A bend whose own ribbon is refused for water carries no joint question.
      // Counted rather than hidden: a fix that made the ribbon vanish would show
      // up here as bends leaving the population.
      waterRefusedJoints: joints.filter((j) => j.nominalM2 < j.bufferM2 * 0.5).length,
      drawnGapM2: sum('drawnGapM2'),
      squareGapM2: sum('squareGapM2'),
      sectorM2: sum('sectorM2'),
      worstOverhangM: joints.reduce((x, j) => Math.max(x, j.overhangM == null ? -Infinity : j.overhangM), -Infinity),
    },
  };
};
