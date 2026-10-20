/**
 * T-2927 — ONE DRAW FOR A RUN OF PIECES THAT DRAW AS ONE.
 *
 * Where a scene has Glessner's inspection model (1904), the `light` and `balanced`
 * structures are cut into 4 m × 2 m cells (T-2219, main.js `spatialCells`), so a
 * phone standing in a courtyard submits only the cells in its view. Each cell is
 * its own BatchedMesh instance, and every instance three keeps after its cull is
 * one entry of the multi-draw — one draw to the GPU driver. From the ground most
 * cells are culled. From the air none are: at Read frame pacing's 1904 flight pose
 * (pacing-read.js SCENE_POSES) the structures were 25,309 draws a frame, 19,829 in
 * the colour pass and 5,480 in the sun's, against 339 the renderer's own counter
 * reports, and the owner's phone drew that frame in 73–80 ms.
 *
 * The cells of one source mesh were added one after another, so their index
 * ranges are contiguous, and they share their structure's matrix and paint. Two
 * neighbouring entries whose ranges touch and whose instance data are identical
 * (matrix, colour, structure) draw exactly what one draw over both ranges draws,
 * so after three has culled and sorted the list they are joined into one entry.
 * A culled cell between two drawn ones breaks the run, so the cull is kept; the
 * triangles drawn are the same triangles. Each joined run is placed where its
 * nearest member was in three's front-to-back order. A blended batch keeps
 * three's order exactly (its order is its blending): there only entries already
 * next to each other in the list are joined (`joinNeighbours`).
 *
 * The pick reads the instance a draw names (gpu-pick.js); a joined run names its
 * first member, whose structure is every member's, so a pick resolves the same.
 */

/** `?coalesce=0` draws every piece on its own again, as before T-2927: the same
 *  page's before and after, on the same phone. Read once, at load. */
export const COALESCE_ON = (() => {
  try { return new URLSearchParams(globalThis.location?.search ?? '').get('coalesce') !== '0'; } catch { return true; }
})();

/** Scratch arrays per batch, grown to the largest list it has drawn. */
function scratchFor(batch, n, instances) {
  let s = batch.userData.coalesceScratch;
  if (!s || s.ids.length < n || s.slotOf.length < instances) {
    const cap = Math.max(n, s?.ids.length ?? 0);
    const slotOf = new Int32Array(Math.max(instances, s?.slotOf.length ?? 0)).fill(-1);
    s = {
      ids: new Int32Array(cap), starts: new Int32Array(cap), counts: new Int32Array(cap),
      runOf: new Int32Array(cap), runStart: new Int32Array(cap), runCount: new Int32Array(cap),
      runId: new Int32Array(cap), runMin: new Int32Array(cap), slotOf,
    };
    batch.userData.coalesceScratch = s;
  }
  return s;
}

function sameInstance(batch, a, b) {
  const owner = batch.userData.batchIndex;
  if (owner && owner[a] !== owner[b]) return false;
  const m = batch._matricesTexture.image.data;
  for (let i = 0, p = a * 16, q = b * 16; i < 16; i += 1) if (m[p + i] !== m[q + i]) return false;
  const c = batch._colorsTexture?.image.data;
  if (c) for (let i = 0, p = a * 4, q = b * 4; i < 4; i += 1) if (c[p + i] !== c[q + i]) return false;
  return true;
}

/**
 * Each instance's run group: an instance takes the previous one's group when the
 * two draw the same instance data, and its own otherwise. Kept per batch and made
 * again only when an instance is added or a matrix or colour is written (each
 * write bumps its texture's version), so a frame compares two integers, not twenty
 * floats.
 */
function groupsOf(batch) {
  const instances = batch._instanceInfo.length;
  const mv = batch._matricesTexture.version;
  const cv = batch._colorsTexture?.version ?? -1;
  let g = batch.userData.coalesceGroups;
  if (g && g.instances === instances && g.mv === mv && g.cv === cv) return g.of;
  const of = g && g.of.length >= instances ? g.of : new Int32Array(Math.max(instances, 1));
  for (let i = 0; i < instances; i += 1) of[i] = i > 0 && sameInstance(batch, i - 1, i) ? of[i - 1] : i;
  g = { instances, mv, cv, of };
  batch.userData.coalesceGroups = g;
  return of;
}

/**
 * Join the touching, identical entries of the multi-draw three has just built for
 * `batch`. Returns how many entries were removed. Exported for the test.
 */
export function joinRuns(batch, geometry, material) {
  const n = batch._multiDrawCount;
  if (n < 2 || material?.wireframe) return 0;
  const index = geometry.getIndex();
  const bpe = index === null ? 1 : index.array.BYTES_PER_ELEMENT;
  const starts = batch._multiDrawStarts;
  const counts = batch._multiDrawCounts;
  const indirect = batch._indirectTexture.image.data;
  if (material?.transparent) return joinNeighbours(batch, n, bpe, starts, counts, indirect, groupsOf(batch));
  const instances = batch._instanceInfo.length;
  const group = groupsOf(batch);
  const s = scratchFor(batch, n, instances);
  for (let k = 0; k < n; k += 1) {
    s.ids[k] = indirect[k]; s.starts[k] = starts[k]; s.counts[k] = counts[k];
    s.slotOf[indirect[k]] = k;
  }
  // Walk the drawn entries in instance order — the order the pieces were added in,
  // and so the order of their ranges — and grow a run while the next one touches it
  // and draws the same instance data.
  let runs = 0;
  let prev = -1;
  for (let i = 0; i < instances; i += 1) {
    const k = s.slotOf[i];
    if (k < 0) continue;
    s.slotOf[i] = -1;
    const r = runs - 1;
    if (prev >= 0 && s.starts[k] === s.runStart[r] + s.runCount[r] * bpe && group[prev] === group[i]) {
      s.runCount[r] += s.counts[k];
      if (k < s.runMin[r]) s.runMin[r] = k;
      s.runOf[k] = r;
    } else {
      s.runStart[runs] = s.starts[k]; s.runCount[runs] = s.counts[k];
      s.runId[runs] = i; s.runMin[runs] = k; s.runOf[k] = runs;
      runs += 1;
    }
    prev = i;
  }
  if (runs === n) return 0;
  // Each run where its nearest member stood in three's order.
  let m = 0;
  for (let k = 0; k < n; k += 1) {
    const r = s.runOf[k];
    if (s.runMin[r] !== k) continue;
    starts[m] = s.runStart[r]; counts[m] = s.runCount[r]; indirect[m] = s.runId[r];
    m += 1;
  }
  batch._multiDrawCount = m;
  batch._indirectTexture.needsUpdate = true;
  return n - m;
}

/**
 * A blended batch keeps three's order exactly: only entries already NEXT to each
 * other in its list are joined, when their ranges touch and their instance data
 * match, so every triangle is drawn in the order it was drawn before. (Where
 * three keeps instance order, `sortObjects = false` — the railway's ground — that
 * is every run; where it sorts back to front it is the few that sort together.)
 */
function joinNeighbours(batch, n, bpe, starts, counts, indirect, group) {
  let m = 0;
  for (let k = 0; k < n; k += 1) {
    if (m > 0 && starts[k] === starts[m - 1] + counts[m - 1] * bpe
        && group[indirect[m - 1]] === group[indirect[k]]) {
      counts[m - 1] += counts[k];
      continue;
    }
    starts[m] = starts[k]; counts[m] = counts[k]; indirect[m] = indirect[k];
    m += 1;
  }
  if (m === n) return 0;
  batch._multiDrawCount = m;
  batch._indirectTexture.needsUpdate = true;
  return n - m;
}

/**
 * Wrap a structures batch so both its passes draw joined runs. The sun's pass
 * reaches `onBeforeRender` through three's own `onBeforeShadow` (and through
 * shadow-casters.js, which wraps that), so one wrap serves both.
 * @param {THREE.BatchedMesh} batch
 * @param {{joined?: number}} [stats] a running count of entries removed
 */
export function coalesceRuns(batch, stats = null) {
  if (!COALESCE_ON) return;
  const prepare = batch.onBeforeRender;
  batch.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
    // three returns early, keeping last frame's list, when nothing can have moved;
    // that list has been joined already.
    const kept = !this._visibilityChanged && !this.perObjectFrustumCulled && !this.sortObjects;
    const out = prepare.call(this, renderer, scene, camera, geometry, material, group);
    if (!kept) {
      const removed = joinRuns(this, geometry, material);
      if (stats) stats.joined = (stats.joined ?? 0) + removed;
    }
    return out;
  };
  batch.userData.coalesced = true;
}
