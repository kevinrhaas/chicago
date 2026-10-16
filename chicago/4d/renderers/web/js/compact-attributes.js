/**
 * compact-attributes.js — a batch keeps the precision it needs and no more (T-2568).
 *
 * The bake ships every building with `KHR_mesh_quantization`: Int16 positions,
 * Int8 normals. The batch re-expanded all of it to float32 and wrote float32
 * colour, roughness and confidence beside it, about 52 bytes a vertex on BOTH
 * the page and the GPU (measured on /1835/ at 390x780, 2026-10-16: 1,265,459
 * structure vertices, 52.8 B each, 67 MB of attributes). A phone that runs out
 * of memory crashes, and the owner reported exactly that.
 *
 * WebGL decodes a NORMALIZED integer attribute to a float in the vertex fetch,
 * so a shader that reads `normal`, `uv` or `color` reads the same kind of value
 * it always did. No shader changes; only the storage does. What each format
 * costs in precision:
 *
 *   normal     Int8 x4 normalized     1/127 a component, under half a degree.
 *   uv, uv1    Uint16 x2 normalized   1/65535 — only when every value is in
 *                                     [0, 1]; a tiling uv stays float32.
 *   color      Uint8 x4 normalized    1/255 — the piece tone (buildings.js
 *                                     pieceToneAttribute), only when every
 *                                     value is in [0, 1]; a brightening tone
 *                                     stays float32.
 *
 * EVERY FORMAT IS FOUR BYTES A VERTEX OR A MULTIPLE OF IT, and that is a rule,
 * not a preference. Safari's WebGL runs on Metal, and Metal wants a vertex
 * buffer's stride in multiples of four bytes; ANGLE meets a one-, two- or
 * three-byte stride by CONVERTING the attribute into a second, aligned buffer
 * at upload. A byte-wide `_roughness` would then cost an iPhone its one byte
 * AND the converted copy — more than the float32 it replaced, on the very
 * phone whose memory crashes this exists for. So the normal is padded to four
 * bytes, a tone to four, and the float scalars (`_roughness`, `_confidence`,
 * `_grain`) stay float32 here: compacting them means packing them together
 * into one four-byte attribute, which needs the shaders that read them to
 * change, and is its own piece of work. `compactPlan` refuses a rule whose
 * stride is not a multiple of four.
 *
 * POSITIONS ARE THEIR OWN CASE (T-2575), because a position is not in any fixed
 * range: `quantizePositions` writes them as Int16 x4 normalized (8 bytes, the
 * fourth padding to the four-byte stride) over a range of +/- `scale` metres,
 * and the scale goes into the instance's MATRIX, so the GPU's own batching
 * multiply undoes it. Two choices there are forced, not taste:
 *
 *   - THE SCALE IS UNIFORM. three meets an instance matrix's scale on the normal
 *     by dividing by its squared column lengths — the inverse-transpose of
 *     R*S — which is right only if the stored normal is the stored geometry's.
 *     It is not: the normal is the building's, and a squashed copy of the
 *     building would have a different one. With one scale on all three axes
 *     the division only shortens the normal, and three normalizes it.
 *   - THE OFFSET IS THE STRUCTURE'S OWN ORIGIN. The wall and roof relief
 *     (wall-relief.js, roof-relief.js) tile their maps in the structure's frame,
 *     from `transformed`, which is now the quantized position. They get the
 *     frame back as `transformed * length(batchingMatrix[0].xyz)` — see
 *     structureFrameGLSL — which a scale recovers and an offset would not:
 *     the matrix's translation is the placement plus the offset, and nothing in
 *     the shader can tell them apart.
 *
 * So the step is `scale / 32767` with `scale` the largest |coordinate| of the
 * whole STRUCTURE, never of a piece: a building split into spatial pieces or
 * across materials quantizes every piece on the same grid, and the vertex two
 * pieces share lands on the same value in both, so no crack opens between them.
 *
 * Anything not named here is left exactly as it arrived, and so is a named
 * attribute whose values fall outside the format's range — a format that would
 * clamp is never chosen.
 *
 * THE PLAN IS PER BATCH, NOT PER GEOMETRY. A `BatchedMesh` allocates its
 * buffers from the FIRST geometry added and refuses a later one whose
 * attribute differs in `normalized`; one that differs only in array type is
 * copied component by component with no range check. So the format is decided
 * once over every geometry a batch will hold, and every one is written to it.
 */

import * as THREE from 'three';

/**
 * name -> its compact format. `pad` widens a vec3 to four components, written
 * as `padValue`: a padded colour is RGBA to three, so its alpha is 1.
 */
export const RULES = {
  normal: { array: Int8Array, pad: 4, padValue: 0, min: -1, max: 1 },
  uv: { array: Uint16Array, min: 0, max: 1 },
  uv1: { array: Uint16Array, min: 0, max: 1 },
  color: { array: Uint8Array, pad: 4, padValue: 1, min: 0, max: 1 },
};

/** Bytes a vertex the rule writes for an attribute of `itemSize` components. */
export function strideOf(rule, itemSize) {
  return rule.array.BYTES_PER_ELEMENT * Math.max(itemSize, rule.pad ?? itemSize);
}

const SCALE = new Map([[Int8Array, 127], [Uint8Array, 255], [Int16Array, 32767], [Uint16Array, 65535]]);

// NaN fails both comparisons, so a channel carrying one stays float.
function inRange(array, min, max) {
  for (let i = 0; i < array.length; i += 1) {
    if (!(array[i] >= min && array[i] <= max)) return false;
  }
  return true;
}

/**
 * Which compact format each attribute takes across all of `geometries`.
 * @returns {Map<string, object>} name -> rule, for the attributes that compact
 */
export function compactPlan(geometries, rules = RULES) {
  const plan = new Map();
  for (const [name, rule] of Object.entries(rules)) {
    const attrs = geometries.map((g) => g.getAttribute(name));
    if (!attrs.length || attrs.some((a) => !a || a.isInterleavedBufferAttribute
      || !(a.array instanceof Float32Array))) continue;
    if (strideOf(rule, attrs[0].itemSize) % 4 !== 0) {
      throw new Error(`${name}: a ${strideOf(rule, attrs[0].itemSize)}-byte stride is converted `
        + 'to an aligned copy on Metal — see the header');
    }
    if (attrs.every((a) => inRange(a.array, rule.min, rule.max))) plan.set(name, rule);
  }
  return plan;
}

/** Rewrite `geometry`'s planned attributes into their compact formats, in place. */
export function compactGeometry(geometry, plan) {
  for (const [name, rule] of plan) {
    const src = geometry.getAttribute(name);
    const from = src.itemSize;
    const to = Math.max(from, rule.pad ?? from);
    const scale = SCALE.get(rule.array);
    const out = new rule.array(src.count * to);
    const a = src.array;
    const pad = Math.round((rule.padValue ?? 0) * scale);
    for (let i = 0; i < src.count; i += 1) {
      for (let k = 0; k < from; k += 1) out[i * to + k] = Math.round(a[i * from + k] * scale);
      for (let k = from; k < to; k += 1) out[i * to + k] = pad;
    }
    geometry.setAttribute(name, new THREE.BufferAttribute(out, to, true));
  }
  return geometry;
}

/** Bytes per vertex across a geometry's attributes (the index excluded). */
export function bytesPerVertex(geometry) {
  let bytes = 0;
  for (const attr of Object.values(geometry.attributes)) {
    bytes += attr.array.BYTES_PER_ELEMENT * attr.itemSize;
  }
  return bytes;
}

/** Int16's normalized range: three decodes `q` as `max(q / 32767, -1)`. */
export const POSITION_STEPS = 32767;

/**
 * The scale one structure's positions quantize over: its largest |coordinate|
 * across every geometry it puts into any batch, so that all of them share one
 * grid (see the header). A structure with no extent at all gets 1.
 */
export function positionScale(geometries) {
  let m = 0;
  for (const g of geometries) {
    const a = g.getAttribute('position').array;
    for (let i = 0; i < a.length; i += 1) m = Math.max(m, Math.abs(a[i]));
  }
  return m > 0 && Number.isFinite(m) ? m : 1;
}

/**
 * Rewrite `geometry`'s float positions as Int16 x4 normalized over +/- `scale`,
 * in place. The caller puts `scale` into the instance matrix — `placement *
 * makeScale(scale, scale, scale)` — so the batch draws exactly where it did.
 */
export function quantizePositions(geometry, scale) {
  const src = geometry.getAttribute('position');
  const a = src.array;
  const out = new Int16Array(src.count * 4);
  const k = POSITION_STEPS / scale;
  for (let i = 0; i < src.count; i += 1) {
    for (let c = 0; c < 3; c += 1) {
      out[i * 4 + c] = Math.max(-POSITION_STEPS, Math.min(POSITION_STEPS, Math.round(a[i * 3 + c] * k)));
    }
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(out, 4, true));
  return geometry;
}

/**
 * GLSL for a vertex-stage patch that needs the STRUCTURE's frame rather than the
 * world's: declares `vec3 <name>`, the position in metres in the structure's own
 * frame, after `<batching_vertex>`. A quantized batch carries its uniform scale
 * in the instance matrix (see the header); anything else has a scale of 1.
 */
export function structureFrameGLSL(name) {
  return `
    #ifdef USE_BATCHING
      vec3 ${name} = transformed * length( batchingMatrix[ 0 ].xyz );
    #else
      vec3 ${name} = transformed;
    #endif`;
}
