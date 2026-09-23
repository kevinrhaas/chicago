/**
 * drawn_timber_census.mjs — where the near-field wood is DRAWN, against the
 * station list that decided to plant it.
 *
 * ROADMAP R-BUG5b's question, asked of the object that answers it today. The
 * question has not changed since the whole near-field wood was found drawn
 * mirrored across the datum's east-west line while three green gates watched:
 * every woody check this project had walked `stations`, the list the planter
 * writes at the moment it DECIDES to plant, and nothing read the geometry back
 * to ask where a tree was DRAWN.
 *
 * WHY THIS FILE EXISTS AT ALL — T-0243. The gate that asks it lived inline in
 * `tools/smoke_renderer.mjs` and traversed for `/^timber__/`, the four quadrant
 * meshes `timber__q0…q3`. T-0223 replaced those with a single `THREE.BatchedMesh`
 * named `timber`, and from that merge the regex matched NOTHING:
 *
 *   - `every tree drawn stands at its own station` went red on its own liveness
 *     clause (`meshes > 0`), on an unmodified `dev`, for every branch cut from
 *     it. It at least announced itself.
 *   - `no timber is drawn out in the channel` asserts `offshore === 0`, and an
 *     empty traversal gives zero offshore vertices. **It passed, green, having
 *     asserted nothing about the timber since the lattice landed.** That is the
 *     defect this file is really here for, and it is why every count below is
 *     paired with a liveness clause the check itself proves it walked.
 *
 * AND WHY IT IS NOT A RENAME. A `BatchedMesh` holds every chunk in one pair of
 * buffers with a per-instance transform the batch owns, so
 * `geometry.getAttribute('position')` read through `matrixWorld` no longer
 * gives a chunk's world position: the walk has to go through each instance's
 * own geometry range and its own matrix. That is what the census below does,
 * through `_instanceInfo` / `_geometryInfo` / `_matricesTexture` — the two
 * structures `BatchedMesh.getBoundingBoxAt()` and `getMatrixAt()` read, walked
 * here so the census needs no THREE inside the page, exactly as
 * `drawn_placement_census.mjs` walks the building batches.
 *
 * It still reads a plain merged mesh named `timber__*` if one is there, so the
 * gate does not silently empty itself again if the batching is ever unwound.
 *
 * A function and a fault injector, and nothing else: `tools/measure_drawn_timber.mjs`
 * runs them as an instrument and `tools/smoke_renderer.mjs` runs the census as a
 * release gate, and they run THE SAME CODE rather than two readings of the same
 * idea. Both are serialised into the page with `.toString()`, so they may close
 * over NOTHING from this module: everything comes off `window.__chicago4d`.
 */

/**
 * THE TWO BARS, and they live INSIDE the census — `strayBarM` and `offshoreBarM`
 * come back in its result and neither the gate nor the instrument writes its own
 * copy. The function is serialised into the page, so it cannot close over a
 * module constant; a constant exported beside it would be a second number free
 * to drift from the one actually applied.
 *
 * 24 m is the reach of the widest crown `trees.js` draws plus its lean, and is
 * deliberately generous: the fault being hunted is off by twice a northing —
 * hundreds of metres — not by a branch. 12 m is a bank willow leaning out over
 * the channel, which the sources put there on purpose (`lean` in SPECIES, and
 * `TREE_DRY_MARGIN_M`'s box). Both were argued in T-0110's box and the crowns
 * have not changed; T-0243 repaired the traversal under them and moved neither.
 */
export const TIMBER_CENSUS = () => {
  const STRAY_BAR_M = 24;
  const OFFSHORE_BAR_M = 12;
  const a = window.__chicago4d;
  const terrain = a.terrain;
  const stations = a.trees.group.userData.stations ?? [];
  // Nearest station, on a 24 m hash — wider than any crown, so the nine cells
  // around a vertex always contain its own stem if it has one.
  const CELL = 24;
  const key = (e, n) => `${Math.round(e / CELL)},${Math.round(n / CELL)}`;
  const grid = new Map();
  for (const s of stations) {
    const k = key(s.e, s.n);
    if (!grid.has(k)) grid.set(k, []);
    grid.get(k).push(s);
  }
  const nearestStation = (e, n) => {
    let best = Infinity;
    for (let de = -1; de <= 1; de++) {
      for (let dn = -1; dn <= 1; dn++) {
        for (const s of grid.get(key(e + de * CELL, n + dn * CELL)) ?? []) {
          const d = Math.hypot(s.e - e, s.n - n);
          if (d < best) best = d;
        }
      }
    }
    return best;
  };
  // How far a wet point stands from the nearest dry ground, by expanding rings.
  // Bounded: past the last radius the answer is "further than this gate cares
  // about", which is already a failure.
  const RADII = [2, 4, 8, 12, 16, 24, 32, 48];
  const shoreDist = (e, n) => {
    for (const r of RADII) {
      for (let k = 0; k < 16; k++) {
        const t = (k / 16) * Math.PI * 2;
        if (!terrain.isWater(e + Math.cos(t) * r, n + Math.sin(t) * r)) return r;
      }
    }
    return 99;
  };

  const out = {
    objects: 0, batches: 0, plainMeshes: 0, chunks: 0, inactiveChunks: 0,
    stations: stations.length, verts: 0,
    stray: 0, worstStray: 0, worstStrayAt: null, outOfHash: 0,
    wet: 0, offshore: 0, worstOffshore: 0, worstOffshoreAt: null,
    strayBarM: STRAY_BAR_M, offshoreBarM: OFFSHORE_BAR_M,
    // Every chunk this census could not read back, by reason. A chunk that
    // cannot be read is not a chunk that is clean, and the gate refuses on it
    // rather than counting a smaller population.
    unreadable: 0,
  };

  // The one place a drawn vertex is judged, so the batched path and the plain
  // path cannot answer the same question two ways.
  const takeVertex = (x, z) => {
    // terrain.js worldToEnu: e = x, n = -z. The convention this whole census
    // exists because something else did not follow.
    const e = x;
    const n = -z;
    out.verts++;
    const d = nearestStation(e, n);
    // A vertex with no station anywhere in the nine cells around it is further
    // than the hash can measure, which is already further than the bar. It is
    // counted as a stray and reported SEPARATELY rather than allowed to set
    // `worstStray` to Infinity — a worst case printed as `null` says nothing,
    // and this is the shape a mirrored chunk actually takes.
    if (Number.isFinite(d)) {
      if (d > out.worstStray) {
        out.worstStray = d;
        out.worstStrayAt = { e: +e.toFixed(1), n: +n.toFixed(1) };
      }
    } else {
      out.outOfHash++;
    }
    if (d > STRAY_BAR_M) out.stray++;
    if (!terrain.isWater(e, n)) return;
    out.wet++;
    const s = shoreDist(e, n);
    if (s > OFFSHORE_BAR_M) {
      out.offshore++;
      if (s > out.worstOffshore) {
        out.worstOffshore = s;
        out.worstOffshoreAt = { e: +e.toFixed(1), n: +n.toFixed(1) };
      }
    }
  };

  // Rows 0 and 2 of W * M, column-major, which is all a horizontal census needs.
  const composeXZ = (W, M) => {
    const r = new Array(8);
    for (let j = 0; j < 4; j++) {
      r[j] = W[0] * M[4 * j] + W[4] * M[4 * j + 1] + W[8] * M[4 * j + 2] + W[12] * M[4 * j + 3];
      r[4 + j] = W[2] * M[4 * j] + W[6] * M[4 * j + 1] + W[10] * M[4 * j + 2] + W[14] * M[4 * j + 3];
    }
    return r;
  };
  const IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

  a.scene3d.traverse((o) => {
    // `timber` is T-0223's single batch; `timber__q0…q3` were the four merged
    // quadrant meshes before it. Both shapes are read, so unwinding the batch
    // cannot empty this census the way landing it did.
    if (!/^timber(__|$)/.test(o.name)) return;
    out.objects++;
    o.updateWorldMatrix(true, false);
    const W = o.matrixWorld.elements;
    const pos = o.geometry?.getAttribute?.('position');
    if (!pos) { out.unreadable++; return; }

    if (o.isBatchedMesh) {
      out.batches++;
      const matrices = o._matricesTexture?.image?.data;
      const instanceInfo = o._instanceInfo ?? [];
      const geometryInfo = o._geometryInfo ?? [];
      if (!matrices || instanceInfo.length === 0) { out.unreadable++; return; }
      for (let i = 0; i < instanceInfo.length; i++) {
        if (instanceInfo[i].active === false) { out.inactiveChunks++; continue; }
        const gi = geometryInfo[instanceInfo[i].geometryIndex];
        if (!gi || !(gi.vertexCount > 0)) { out.unreadable++; continue; }
        out.chunks++;
        // The instance matrix the GPU is handed, under the object's own world
        // matrix. `trees.js` writes identity here and lets the chunk geometry
        // carry absolute world coordinates — but a census that assumed that
        // would be reading the renderer's intention rather than its buffers,
        // which is the whole failure mode this file is named after.
        const o16 = i * 16;
        const M = new Array(16);
        for (let k = 0; k < 16; k++) M[k] = matrices[o16 + k];
        const c = composeXZ(W, M);
        for (let v = gi.vertexStart, l = gi.vertexStart + gi.vertexCount; v < l; v++) {
          const vx = pos.getX(v);
          const vy = pos.getY(v);
          const vz = pos.getZ(v);
          takeVertex(
            c[0] * vx + c[1] * vy + c[2] * vz + c[3],
            c[4] * vx + c[5] * vy + c[6] * vz + c[7],
          );
        }
      }
      return;
    }

    if (!o.isMesh) { out.unreadable++; return; }
    out.plainMeshes++;
    out.chunks++;
    const c = composeXZ(W, IDENTITY);
    for (let v = 0; v < pos.count; v++) {
      const vx = pos.getX(v);
      const vy = pos.getY(v);
      const vz = pos.getZ(v);
      takeVertex(
        c[0] * vx + c[1] * vy + c[2] * vz + c[3],
        c[4] * vx + c[5] * vy + c[6] * vz + c[7],
      );
    }
  });

  out.worstStray = +out.worstStray.toFixed(1);
  return out;
};

/**
 * THE NEGATIVE CONTROL — displace two chunks of the live timber and prove the
 * census reports both of them.
 *
 * R-A1's finding, one parcel on: *an assertion that can only ever see one value
 * is not an assertion.* T-0243 is the second time this project has shipped a
 * green tick pointed at the wrong population, so the repair is not believed
 * because it went green — it is believed because a deliberately displaced chunk
 * turns it red, once per bar:
 *
 *   1. **the mirror**, which is R-BUG5b's own fault applied to one chunk: set
 *      the instance matrix's z scale to -1, so that chunk's absolute world
 *      coordinates are reflected across the datum's east-west line. The chunk
 *      chosen is the one standing furthest from that line, because a chunk ON
 *      the line is its own mirror and would demonstrate nothing. That must
 *      raise `stray`.
 *   2. **the drowning**, which is the picture the owner reported: translate a
 *      chunk out to a point the terrain mask calls water and that stands
 *      further than a willow's lean from any dry ground. That must raise
 *      `offshore` — the half that was passing on an empty traversal, and so the
 *      half with no evidence at all that it can fail.
 *
 * It mutates the page it is called in. Run the real census FIRST.
 */
export const BREAK_TIMBER = () => {
  const a = window.__chicago4d;
  let batch = null;
  a.scene3d.traverse((o) => {
    if (!batch && o.isBatchedMesh && /^timber(__|$)/.test(o.name)) batch = o;
  });
  if (!batch) return { ok: false, why: 'no batched timber in the scene' };
  const matrices = batch._matricesTexture?.image?.data;
  const instanceInfo = batch._instanceInfo ?? [];
  const geometryInfo = batch._geometryInfo ?? [];
  const pos = batch.geometry.getAttribute('position');
  if (!matrices || !pos) return { ok: false, why: 'the batch exposes no buffers' };

  // Each chunk's centroid in ENU, read off the same buffers the census reads.
  const chunks = [];
  for (let i = 0; i < instanceInfo.length; i++) {
    if (instanceInfo[i].active === false) continue;
    const gi = geometryInfo[instanceInfo[i].geometryIndex];
    if (!gi || !(gi.vertexCount > 0)) continue;
    let sx = 0;
    let sz = 0;
    for (let v = gi.vertexStart, l = gi.vertexStart + gi.vertexCount; v < l; v++) {
      sx += pos.getX(v);
      sz += pos.getZ(v);
    }
    chunks.push({ i, e: sx / gi.vertexCount, n: -(sz / gi.vertexCount), verts: gi.vertexCount });
  }
  if (chunks.length < 2) return { ok: false, why: `only ${chunks.length} chunk(s) to displace` };

  // (1) the mirror — the chunk furthest from the datum's east-west line.
  const far = chunks.slice().sort((p, q) => Math.abs(q.n) - Math.abs(p.n))[0];
  matrices[far.i * 16 + 10] = -1;

  // (2) the drowning — a point the mask calls water, at least 16 m from dry
  // ground, found by asking the terrain rather than by writing a coordinate
  // down here where the channel could move out from under it.
  const dry = (e, n) => !a.terrain.isWater(e, n);
  const openWater = (e, n) => {
    if (dry(e, n)) return false;
    for (let k = 0; k < 24; k++) {
      const t = (k / 24) * Math.PI * 2;
      if (dry(e + Math.cos(t) * 16, n + Math.sin(t) * 16)) return false;
    }
    return true;
  };
  let target = null;
  for (let e = -600; e <= 600 && !target; e += 8) {
    for (let n = -600; n <= 600; n += 8) {
      if (openWater(e, n)) { target = { e, n }; break; }
    }
  }
  if (!target) return { ok: false, why: 'no open water 16 m from any bank in the modelled field' };
  const victim = chunks.find((c) => c.i !== far.i) ?? chunks[0];
  const o16 = victim.i * 16;
  matrices[o16 + 12] += target.e - victim.e;
  // world z = -n, so the translation to put the chunk at northing target.n.
  matrices[o16 + 14] += -(target.n) - (-(victim.n));
  if (batch._matricesTexture) batch._matricesTexture.needsUpdate = true;

  return {
    ok: true,
    chunks: chunks.length,
    mirrored: { chunk: far.i, n: +far.n.toFixed(1), verts: far.verts,
      movedM: +Math.abs(2 * far.n).toFixed(1) },
    drowned: { chunk: victim.i, verts: victim.verts,
      from: { e: +victim.e.toFixed(1), n: +victim.n.toFixed(1) }, to: target },
  };
};
