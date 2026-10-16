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
 * `_grain`, the piece tone) are not given byte rules at all: they are PACKED
 * together into one four-byte attribute, which the shaders that read them
 * decode (T-2574, § the four scalars below). `compactPlan` refuses a rule
 * whose stride is not a multiple of four.
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

/**
 * THE FOUR SCALARS IN ONE FOUR-BYTE ATTRIBUTE (T-2574).
 *
 * The header's rule is why this exists: a lone byte-wide scalar is a
 * misaligned stride on Metal, so `_roughness`, `_confidence`, `_grain` and the
 * piece tone went on costing four bytes each in float32 — sixteen bytes a
 * vertex of four numbers that each take a handful of values. Packed into one
 * `Uint8 x4` they cost four, and the stride is four.
 *
 * The bytes are NOT normalized. WebGL hands the shader each one as a float from
 * 0 to 255, and the shader divides by the lane's own scale, so each lane picks
 * the scale that makes the values the dataset actually writes come out exact:
 *
 *   x  roughness    byte / 200          every two-decimal finish is exact;
 *                                       clamped to [0, 1], as three clamps it.
 *   y  confidence   byte / 254          0, 0.5 and 1 are exact (0, 127, 254).
 *                                       A normalized byte reads 0.5 as 0.50196
 *                                       and `chicago_wInferred` as 0.992; this
 *                                       reads it as 0.5. Clamped to [0, 1] and
 *                                       NaN to 0, as the shader always did.
 *   z  grain        (byte - 128) / 100  ±1 and ±0.3 exact, and its SIGN kept
 *                                       (a negative grain is a standing timber,
 *                                       wall-relief.js); 0 where none is bound.
 *   w  piece tone   byte / chiToneScale the scale is PER BATCH: the largest
 *                                       WHOLE number that still fits the
 *                                       batch's largest tone in a byte (255
 *                                       when none exceeds 1). Whole, so a tone
 *                                       of 1 is the byte `scale` and reads
 *                                       exactly 1 — an untoned mesh in a toned
 *                                       batch is not brightened by a rounding.
 *
 * Every clamp above is one the shader already applied to the float, so it
 * changes no pixel. The shaders read the lanes through SCALARS_GLSL, the one
 * place the scales are written in GLSL.
 */
export const SCALARS = '_chiScalars';

/** source attribute -> its lane, its scale (null: the batch's tone scale), its
 *  zero byte, the value a geometry without it carries, and its clamp. */
export const SCALAR_CODES = {
  _roughness: { lane: 0, scale: 200, zero: 0, fill: 1, min: 0, max: 1 },
  _confidence: { lane: 1, scale: 254, zero: 0, fill: 0, min: 0, max: 1 },
  _grain: { lane: 2, scale: 100, zero: 128, fill: 0, min: -1.28, max: 1.27 },
  _tone: { lane: 3, scale: null, zero: 0, fill: 1, min: 0, max: Infinity },
};

const LANES = 'xyzw';
const glslFloat = (v) => (Number.isInteger(v) ? v.toFixed(1) : String(v));
function laneGLSL(code, scale) {
  const byte = `_chiScalars.${LANES[code.lane]}`;
  return `(${code.zero ? `(${byte} - ${glslFloat(code.zero)})` : byte} / ${scale})`;
}

/** GLSL for each lane, and the declaration every patch that reads one needs. */
export const SCALARS_GLSL = {
  roughness: laneGLSL(SCALAR_CODES._roughness, glslFloat(SCALAR_CODES._roughness.scale)),
  confidence: laneGLSL(SCALAR_CODES._confidence, glslFloat(SCALAR_CODES._confidence.scale)),
  grain: laneGLSL(SCALAR_CODES._grain, glslFloat(SCALAR_CODES._grain.scale)),
  tone: laneGLSL(SCALAR_CODES._tone, 'chiToneScale'),
  /**
   * Prepend the attribute once. Three patches read it on one material (the
   * batch's own, wall-relief's and confidence's), each chained over the last,
   * and GLSL refuses a second declaration.
   */
  declare(vertexShader) {
    const decl = `attribute vec4 ${SCALARS};\n`;
    return vertexShader.includes(decl) ? vertexShader : decl + vertexShader;
  },
};

/** The tone scale for a batch of geometries: the largest whole number that
 *  fits its largest `_tone` in a byte. */
export function toneScaleOf(geometries) {
  let most = 1;
  for (const g of geometries) {
    const a = g.getAttribute('_tone');
    if (!a) continue;
    for (let i = 0; i < a.count; i += 1) {
      const v = a.getX(i);
      if (v > most) most = v;
    }
  }
  return Math.max(1, Math.floor(255 / most));
}

/**
 * Write `geometry`'s four scalars into one `Uint8 x4` attribute and delete the
 * float sources, in place. Every geometry in a batch must be packed with the
 * batch's one `toneScale`.
 */
export function packScalars(geometry, toneScale) {
  const n = geometry.getAttribute('position').count;
  const out = new Uint8Array(n * 4);
  for (const [name, code] of Object.entries(SCALAR_CODES)) {
    const src = geometry.getAttribute(name);
    const scale = code.scale ?? toneScale;
    for (let i = 0; i < n; i += 1) {
      let v = src ? src.getX(i) : code.fill;
      if (!(v === v)) v = code.fill;
      v = Math.min(code.max, Math.max(code.min, v));
      out[i * 4 + code.lane] = Math.min(255, Math.max(0, Math.round(v * scale + code.zero)));
    }
    if (src) geometry.deleteAttribute(name);
  }
  geometry.setAttribute(SCALARS, new THREE.BufferAttribute(out, 4, false));
  return geometry;
}

/** The value a shader reads from lane `name` of vertex `i` — the readback. */
export function unpackScalar(attribute, name, i, toneScale = 255) {
  const code = SCALAR_CODES[name];
  return (attribute.array[i * 4 + code.lane] - code.zero) / (code.scale ?? toneScale);
}
