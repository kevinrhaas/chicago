/**
 * drawn_placement_census.mjs — ROADMAP K50's census, in one place.
 *
 * A function, and nothing else: `tools/measure_drawn_placement.mjs` runs it as
 * an instrument and `tools/smoke_renderer.mjs` runs it as a release gate, and
 * they run THE SAME CODE rather than two readings of the same idea. That is not
 * tidiness — R-BUG5's own box records `measure_far_timber.py` and the browser
 * disagreeing until they were made to agree sample for sample, and a gate that
 * paraphrases its instrument is a gate that can pass a build the instrument
 * fails.
 *
 * It is serialised into the page with `CENSUS.toString()`, so it may close over
 * NOTHING from this module: everything it needs comes off `window.__chicago4d`.
 */

/**
 * THE NEGATIVE CONTROL — put R-BUG5b's fault into the live scene.
 *
 * R-A1's finding, one parcel on: *an assertion that can only ever see one value
 * is not an assertion*. A placement gate that has only ever run on a correct
 * build has demonstrated nothing, and this project has shipped two gates that
 * were green because they were pointed at the wrong population rather than
 * because the town was right.
 *
 * So this reproduces the exact fault, in the exact terms it had: hand the ENU
 * northing to the slot that wants a three world z. For a building that is the
 * sign of its instance matrix's z translation; for the road ribbon it is the
 * sign of every drawn vertex's z. Nothing else is touched, and nothing here
 * runs outside `--refute`.
 *
 * It mutates the page it is called in. Run the real census FIRST.
 */
export const BREAK_IT = () => {
  const a = window.__chicago4d;
  let instances = 0;
  let verts = 0;
  for (const batch of a.buildings.batches ?? []) {
    const m = batch._matricesTexture?.image?.data;
    if (!m) continue;
    for (let i = 0; i < (batch._instanceInfo ?? []).length; i++) {
      // Matrix4.elements[14] is the z translation — `enuToWorld`'s `-n`.
      m[i * 16 + 14] = -m[i * 16 + 14];
      instances++;
    }
  }
  a.streets.group.traverse((o) => {
    if (!o.isMesh || !o.geometry?.getAttribute) return;
    const p = o.geometry.getAttribute('position');
    for (let i = 0; i < p.count; i++) { p.setZ(i, -p.getZ(i)); verts++; }
    p.needsUpdate = true;
  });
  return { instances, verts };
};

export const CENSUS = () => {
  const a = window.__chicago4d;

  // ---- buildings: the drawn body against the sidecar's own anchor ----
  //
  // UNION ACROSS MATERIALS, and it is not a detail. A structure is added to one
  // batch per material it uses, so it holds several instances and any one of
  // them is walls, or roof, or trim — never the building. `instanceBounds()`
  // says so in its own comment, and a first reading of this census that took
  // the per-instance box reported 279 strays out of 1,310 "bodies" for a town
  // of 331 structures. The plan box below is accumulated per structure id.
  const B = {
    batches: 0, instances: 0, compared: 0, unrecorded: 0, verts: 0,
    outside: 0, worst: 0, worstId: null, worstSpan: 0,
    mirrorCloser: 0, worstMirrorId: null, strays: [], corners: [], worstCorner: 0,
  };
  const plan = new Map();
  for (const batch of a.buildings.batches ?? []) {
    B.batches++;
    const pos = batch.geometry.getAttribute('position');
    const index = batch.geometry.index;
    // The two structures BatchedMesh.getBoundingBoxAt() and getMatrixAt() read,
    // walked here so the census needs no THREE inside the page. The position
    // buffer is the buffer the GPU is handed; the matrix is the transform it is
    // handed with. There is no third place the geometry could come from.
    const matrices = batch._matricesTexture?.image?.data;
    const instanceInfo = batch._instanceInfo ?? [];
    const geometryInfo = batch._geometryInfo ?? [];
    const ids = batch.userData.batchIndex ?? [];
    if (!matrices) continue;
    for (let i = 0; i < instanceInfo.length; i++) {
      if (instanceInfo[i].active === false) continue;
      B.instances++;
      const id = ids[i];
      const rec = a.registry.get(id);
      const p = rec?.sidecar?.placement;
      if (!p || typeof p.local_e !== 'number' || typeof p.local_n !== 'number') {
        B.unrecorded++;
        continue;
      }
      const gi = geometryInfo[instanceInfo[i].geometryIndex];
      if (!gi) { B.unrecorded++; continue; }
      const o = i * 16;
      const m0 = matrices[o]; const m4 = matrices[o + 4];
      const m8 = matrices[o + 8]; const m12 = matrices[o + 12];
      const m2 = matrices[o + 2]; const m6 = matrices[o + 6];
      const m10 = matrices[o + 10]; const m14 = matrices[o + 14];
      let e0 = Infinity; let e1 = -Infinity;
      let n0 = Infinity; let n1 = -Infinity;
      for (let k = gi.start, l = gi.start + gi.count; k < l; k++) {
        const iv = index ? index.getX(k) : k;
        const vx = pos.getX(iv);
        const vy = pos.getY(iv);
        const vz = pos.getZ(iv);
        const x = m0 * vx + m4 * vy + m8 * vz + m12;
        const z = m2 * vx + m6 * vy + m10 * vz + m14;
        // terrain.js worldToEnu: e = x, n = -z.
        const e = x;
        const n = -z;
        if (e < e0) e0 = e;
        if (e > e1) e1 = e;
        if (n < n0) n0 = n;
        if (n > n1) n1 = n;
        B.verts++;
      }
      if (!Number.isFinite(e0)) { B.unrecorded++; continue; }
      const box = plan.get(id);
      if (box) {
        box.e0 = Math.min(box.e0, e0); box.e1 = Math.max(box.e1, e1);
        box.n0 = Math.min(box.n0, n0); box.n1 = Math.max(box.n1, n1);
        box.parts++;
      } else {
        plan.set(id, { e0, e1, n0, n1, parts: 1, e: p.local_e, n: p.local_n });
      }
    }
  }
  for (const [id, box] of plan) {
    B.compared++;
    // How far outside its own drawn plan footprint the record's anchor falls.
    // Zero for every building whose body was drawn where it was placed.
    const outE = Math.max(box.e0 - box.e, box.e - box.e1, 0);
    const outN = Math.max(box.n0 - box.n, box.n - box.n1, 0);
    const out = Math.hypot(outE, outN);
    const span = Math.hypot(box.e1 - box.e0, box.n1 - box.n0);
    // And how far the anchor is from the NEAREST CORNER of that footprint,
    // which is the number K30(b)'s reading predicts to be small: the records
    // are derived to their frontage and the body grows from the minimum corner.
    let corner = Infinity;
    for (const ce of [box.e0, box.e1]) {
      for (const cn of [box.n0, box.n1]) {
        corner = Math.min(corner, Math.hypot(ce - box.e, cn - box.n));
      }
    }
    if (corner > B.worstCorner) B.worstCorner = corner;
    if (out > 1) {
      B.outside++;
      if (B.strays.length < 12) {
        B.strays.push({ id, out: +out.toFixed(2), span: +span.toFixed(1),
          parts: box.parts,
          anchor: [+box.e.toFixed(1), +box.n.toFixed(1)],
          drawn: [+((box.e0 + box.e1) / 2).toFixed(1), +((box.n0 + box.n1) / 2).toFixed(1)] });
      }
    }
    if (out > B.worst) {
      B.worst = out;
      B.worstId = id;
      B.worstSpan = +span.toFixed(1);
    }
    // THE MIRROR TEST, and it needs a scale guard to mean anything. A body
    // whose anchor sits within a few metres of the datum's east-west line is
    // nearer to its own mirror for arithmetic reasons that have nothing to do
    // with a sign error, so only anchors well off that line are asked. Under a
    // mirrored northing a building 200 m north is drawn 400 m from its anchor.
    const dce = (box.e0 + box.e1) / 2;
    const dcn = (box.n0 + box.n1) / 2;
    const own = Math.hypot(dce - box.e, dcn - box.n);
    const mirrored = Math.hypot(dce - box.e, dcn + box.n);
    if (Math.abs(box.n) > 5 && mirrored < own - 1e-6) {
      B.mirrorCloser++;
      if (B.corners.length < 8) {
        B.corners.push({ id, anchorN: +box.n.toFixed(1), drawnN: +dcn.toFixed(1),
          own: +own.toFixed(2), mirrored: +mirrored.toFixed(2) });
      }
      if (!B.worstMirrorId) B.worstMirrorId = id;
    }
  }

  // ---- streets: the drawn ribbon against the committed centreline ----
  // `addRecord()` emits its corners at most `track_width_m / 2` either side of
  // the centreline and clips them INWARDS at the waterline, so every drawn
  // vertex owes a centreline within its own street's half-width. The nearest
  // over the whole set is taken, which is the generous reading: a vertex has to
  // be off every street in town before it is counted.
  //
  // AND THE MIRROR TEST IS NOT THE INSTRUMENT HERE — the half-width test is.
  // A first reading asked whether a vertex is nearer to a street at its
  // mirrored northing and reported 3,754 of 19,372, on a build where every
  // single vertex is inside its own track. The reason is the town: on a street
  // GRID a point reflected across an east-west line lands on or near another
  // east-west street more often than not, and a vertex at the EDGE of its own
  // track scores worse than a mirror landing mid-track by construction. So
  // `mirrorAlsoOnRoad` is reported as a diagnostic and gates nothing; what
  // catches a mirrored ribbon is `stray`, because a reflected road runs where
  // no centreline is recorded.
  //
  // T-0111. THE CENTRELINE A DRAWN VERTEX OWES IS THE ONE IT WAS DRAWN FROM.
  // A street may now commit two lines — `path_local_enu_m`, the plat, and
  // `drawn_track_local_enu_m`, the worn wheel line the ribbon is actually
  // painted on — so the test reads `drawn`, which IS `path` for every street
  // that authors no separate track. The assertion is unchanged in kind and in
  // strictness: a vertex still owes a COMMITTED centreline within its own
  // street's half-width, and a mirrored ribbon still runs where neither line
  // is recorded. Measuring the drawn ribbon against a line it was never drawn
  // from would report a stray for authored data and miss the mirroring this
  // exists to catch, which is the R-BUG3c trap in the other direction.
  const S = { meshes: 0, verts: 0, stray: 0, worst: 0, worstAt: null, beyondBounds: 0,
              mirrorAlsoOnRoad: 0, records: (a.streets.records ?? []).length };
  const pointSeg = (e, n, A, C) => {
    const de = C[0] - A[0];
    const dn = C[1] - A[1];
    const len2 = de * de + dn * dn || 1e-9;
    const t = Math.max(0, Math.min(1, ((e - A[0]) * de + (n - A[1]) * dn) / len2));
    return Math.hypot(e - (A[0] + de * t), n - (A[1] + dn * t));
  };
  const nearestRoad = (e, n) => {
    let best = Infinity;
    for (const rec of a.streets.records ?? []) {
      const half = (rec.track_width_m ?? 6) * 0.5;
      const b = rec.bounds;
      if (b && (e < b.e0 || e > b.e1 || n < b.n0 || n > b.n1)) continue;
      const line = rec.drawn ?? rec.path;
      for (let i = 1; i < line.length; i++) {
        const d = pointSeg(e, n, line[i - 1], line[i]) - half;
        if (d < best) best = d;
      }
    }
    return best;
  };
  a.streets.group.traverse((o) => {
    if (!o.isMesh || !o.geometry?.getAttribute) return;
    S.meshes++;
    o.updateWorldMatrix(true, false);
    const pos = o.geometry.getAttribute('position');
    const m = o.matrixWorld.elements;
    for (let i = 0; i < pos.count; i++) {
      const vx = pos.getX(i);
      const vy = pos.getY(i);
      const vz = pos.getZ(i);
      const x = m[0] * vx + m[4] * vy + m[8] * vz + m[12];
      const z = m[2] * vx + m[6] * vy + m[10] * vz + m[14];
      const e = x;
      const n = -z;
      S.verts++;
      const d = nearestRoad(e, n);
      if (d > 0.05) {
        S.stray++;
        // A vertex outside every street's padded bounds has no finite distance
        // to report, and printing `Infinity` as a "worst" tells nobody anything.
        // It is counted on its own line: off the grid entirely.
        if (!Number.isFinite(d)) S.beyondBounds++;
        else if (d > S.worst) { S.worst = d; S.worstAt = { e: +e.toFixed(1), n: +n.toFixed(1) }; }
      }
      if (nearestRoad(e, -n) <= 0.05) S.mirrorAlsoOnRoad++;
    }
  });

  return { buildings: B, streets: S };
};
