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
