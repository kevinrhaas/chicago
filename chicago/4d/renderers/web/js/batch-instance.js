/**
 * ONE INSTANCED DRAW FOR EVERY COPY OF ONE PIECE — the grown trees' batches.
 *
 * A grown wood (tree-instances.js) is a few templates — each variant of each
 * species at each level — stood hundreds of times. Every stem is one instance of a
 * `BatchedMesh`, and three submits a BatchedMesh as a multi-draw with ONE ENTRY PER
 * INSTANCE it kept after its cull: a parkway of 500 elms in view is 1,000 draws
 * (wood and leaves), and the sun's pass draws the shading ones again. Each entry is
 * a draw to the driver (driver-draws.js), and on a machine whose GL loops them
 * (ANGLE over Metal on a Mac, a phone) the frame's cost follows the count, not the
 * triangles: the owner's desktop read 1904 at 65-90 ms walking and 146 ms flying
 * with 5,000+ driver draws, and adaptive resolution bought nothing.
 *
 * WHAT THIS DOES. After three has culled the batch for the pass (its own
 * `onBeforeRender`, per stem, in the view or in the sun), the kept entries are
 * grouped by the template they draw, and each template is ONE instanced entry
 * whose instance count is the stems kept for it. `WEBGL_multi_draw` carries the
 * counts (`multiDrawElementsInstancedWEBGL`), so the batch is still one multi-draw
 * — of a few dozen entries instead of a few thousand. The stems drawn, their cull,
 * their matrices and their colours (the T-2948 dissolve) are exactly what they
 * were; only the order they are drawn in changes, and an opaque or cut-out crown
 * does not depend on it.
 *
 * THE INDIRECT TABLE. three's batching shader finds a draw's instance as
 * `getIndirectIndex( gl_DrawID )`, one table entry per draw. Here the table's
 * first entries are, per draw, where its stems' run starts, and the runs follow:
 * an instance is `table[ table[ gl_DrawID ] + gl_InstanceID ]`. The materials'
 * shaders read it that way (`patchInstancedDraws`), so a batch drawn this way
 * holds one table entry per template beyond its stems (`extraSlots`).
 *
 * WHERE IT CANNOT. Without `WEBGL_multi_draw` three draws each entry on its own
 * and has no instance count to give; there the shader is not patched and the
 * batch is left as three draws it, so the two never disagree. A material that is
 * not patched (a stand-in drawn for a pick) is left as three draws it too.
 *
 * three's `renderer.info` counts each instanced entry as one instance; the rest of
 * its triangles are added here, so the triangle budgets read what the GPU drew.
 */

const MULTI_DRAW = 'WEBGL_multi_draw';

/** The draw the extension is about to receive for a regrouped batch. */
const pending = { counts: null, draws: 0, instances: null, info: null, extraTris: 0 };

/** Whether this renderer draws a regrouped batch: a multi-draw that carries instance counts. */
function instancedOn(renderer) {
  const ext = renderer?.extensions;
  if (!ext) return null;
  if (ext.__chiInstanced !== undefined) return ext.__chiInstanced;
  let on = null;
  if (ext.has(MULTI_DRAW)) {
    const md = ext.get(MULTI_DRAW);
    if (md && typeof md.multiDrawElementsInstancedWEBGL === 'function') {
      wrapExtension(md);
      on = md;
    }
  }
  ext.__chiInstanced = on;
  return on;
}

/**
 * three hands `multiDrawElementsWEBGL` the batch's own `_multiDrawCounts` array, so
 * the draw a regrouped batch prepared is known by that array and its count; it is
 * sent with its instance counts, and every other multi-draw passes through as it was.
 */
function wrapExtension(md) {
  if (md.__chiInstancedWrap) return;
  md.__chiInstancedWrap = true;
  const plain = md.multiDrawElementsWEBGL;
  md.multiDrawElementsWEBGL = function multiDrawElementsRegrouped(mode, counts, countsOffset, type, offsets,
    offsetsOffset, drawCount) {
    if (pending.counts !== null && pending.counts === counts && pending.draws === drawCount) {
      const instances = pending.instances;
      const info = pending.info;
      const extra = pending.extraTris;
      pending.counts = null; pending.instances = null; pending.info = null;
      md.multiDrawElementsInstancedWEBGL(mode, counts, countsOffset, type, offsets, offsetsOffset,
        instances, 0, drawCount);
      // three's info.update after this counts one instance a draw; the rest are here.
      if (info && mode === 4) info.triangles += extra;
      return undefined;
    }
    return plain.apply(this, arguments);
  };
}

/** Scratch arrays per batch, grown to what it has drawn. */
function scratchFor(batch, n, geometries) {
  let s = batch.userData.instanceScratch;
  if (!s || s.ids.length < n || s.gN.length < geometries) {
    const cap = Math.max(n, s?.ids.length ?? 0);
    const g = Math.max(geometries, s?.gN.length ?? 0);
    s = {
      ids: new Int32Array(cap), gOf: new Int32Array(cap),
      gN: new Int32Array(g), gPos: new Int32Array(g), instances: new Int32Array(g),
    };
    batch.userData.instanceScratch = s;
  }
  return s;
}

/**
 * Regroup the entries three kept into one instanced entry per template, and lay
 * the indirect table out as the patched shader reads it. Returns the entries saved.
 */
export function regroup(batch, renderer, geometry) {
  const n = batch._multiDrawCount;
  const indirect = batch._indirectTexture.image.data;
  pending.counts = null;
  if (n === 0) return 0;
  const index = geometry.getIndex();
  const bpe = index === null ? 1 : index.array.BYTES_PER_ELEMENT;
  const info = batch._instanceInfo;
  const geos = batch._geometryInfo;
  const G = geos.length;
  const s = scratchFor(batch, n, G);
  s.gN.fill(0, 0, G);
  for (let k = 0; k < n; k += 1) {
    const id = indirect[k];
    const g = info[id].geometryIndex;
    s.ids[k] = id; s.gOf[k] = g; s.gN[g] += 1;
  }
  let draws = 0;
  for (let g = 0; g < G; g += 1) if (s.gN[g] > 0) draws += 1;
  if (draws + n > indirect.length) {
    // Never at the capacity `extraSlots` asks for; drawn as nothing rather than wrongly.
    batch._multiDrawCount = 0;
    batch.userData.instanceOverflow = (batch.userData.instanceOverflow ?? 0) + 1;
    return 0;
  }
  const starts = batch._multiDrawStarts;
  const counts = batch._multiDrawCounts;
  let d = 0;
  let at = draws;
  let extraTris = 0;
  for (let g = 0; g < G; g += 1) {
    const m = s.gN[g];
    if (m === 0) continue;
    const gi = geos[g];
    starts[d] = gi.start * bpe;
    counts[d] = gi.count;
    s.instances[d] = m;
    indirect[d] = at;
    s.gPos[g] = at;
    extraTris += (gi.count / 3) * (m - 1);
    at += m;
    d += 1;
  }
  for (let k = 0; k < n; k += 1) {
    const g = s.gOf[k];
    indirect[s.gPos[g]] = s.ids[k];
    s.gPos[g] += 1;
  }
  batch._multiDrawCount = draws;
  batch._indirectTexture.needsUpdate = true;
  pending.counts = counts;
  pending.draws = draws;
  pending.instances = s.instances;
  pending.info = renderer.info?.render ?? null;
  pending.extraTris = Math.round(extraTris);
  return n - draws;
}

/**
 * Wrap a grown wood's batch so both its passes draw one instanced entry per
 * template. The sun's pass reaches `onBeforeRender` through three's own
 * `onBeforeShadow`, so one wrap serves both (as batch-coalesce.js's does).
 * @param {THREE.BatchedMesh} batch
 * @param {{saved?: number}} [stats] a running count of entries saved
 */
export function instanceDraws(batch, stats = null) {
  const prepare = batch.onBeforeRender;
  batch.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
    // three returns early, keeping last frame's list, when nothing can have moved;
    // that list has been regrouped already, and is drawn as it was.
    const kept = !this._visibilityChanged && !this.perObjectFrustumCulled && !this.sortObjects;
    const out = prepare.call(this, renderer, scene, camera, geometry, material, group);
    if (material?.userData?.instancedDraws && instancedOn(renderer)) {
      if (!kept) {
        const saved = regroup(this, renderer, geometry);
        if (stats) stats.saved = (stats.saved ?? 0) + saved;
        this.userData.instanceDraws = { held: pending.counts, instances: pending.instances, extraTris: pending.extraTris };
      } else if (this.userData.instanceDraws?.held) {
        // The list (and the table) three kept is the last one regrouped.
        const last = this.userData.instanceDraws;
        pending.counts = last.held; pending.draws = this._multiDrawCount; pending.instances = last.instances;
        pending.info = renderer.info?.render ?? null; pending.extraTris = last.extraTris;
      }
    }
    return out;
  };
  batch.userData.instancedDraws = true;
}

/** The table entries a batch drawn this way holds beyond one a stem: one a template. */
export const extraSlots = (geometries) => Math.max(0, geometries | 0);

/**
 * Read a batched draw's instance through the regrouped table. Defined after
 * three's `getIndirectIndex`, and then named over it, so every later reading of
 * `getIndirectIndex( gl_DrawID )` (three's matrix, its colour, the dissolve's
 * fade) reads the stem the instance is. Only where the renderer draws regrouped.
 */
const PARS = /* glsl */`
#ifdef USE_BATCHING
float chiInstancedIndex( const in int drawId ) {
  int run = int( getIndirectIndex( drawId ) );
  return getIndirectIndex( run + gl_InstanceID );
}
#define getIndirectIndex( i ) chiInstancedIndex( i )
#endif`;

/** Patch a grown tree material (or its shadow twin) to read the regrouped table. */
export function patchInstancedDraws(material) {
  const prior = material.onBeforeCompile;
  const isDefaultKey = material.customProgramCacheKey === Object.getPrototypeOf(material).customProgramCacheKey
    && !Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey');
  const priorKey = isDefaultKey ? String(prior) : material.customProgramCacheKey();
  const priorKeyFn = isDefaultKey ? null : material.customProgramCacheKey.bind(material);
  let on = false;
  material.onBeforeCompile = (shader, renderer) => {
    prior.call(material, shader, renderer);
    on = !!instancedOn(renderer);
    if (!on) return;
    shader.vertexShader = shader.vertexShader.replace('#include <batching_pars_vertex>',
      `#include <batching_pars_vertex>\n${PARS}`);
  };
  material.customProgramCacheKey = () => `${priorKeyFn ? priorKeyFn() : priorKey}|instanced-draws`;
  material.userData.instancedDraws = true;
  return material;
}
