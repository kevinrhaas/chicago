/**
 * COMPACT VERTEX STREAMS FOR THE TIMBER LAYERS (T-2569).
 *
 * The frontage, the enclosures and the yard goods each lay their own timber and
 * hand it to three as float32: 4 bytes a component, on the page and again on the
 * GPU. Three of those streams carry far less than that:
 *
 *   normal ..... unit vectors. Int8 x 4, normalized: 4 bytes for 12. The fourth
 *                byte is padding, so the stride is a multiple of four (Metal pads
 *                an unaligned stride with a converted copy of its own); the
 *                shader's `vec3 normal` never reads it. A component is off by at
 *                most 1/254, under a degree of angle on a face.
 *   color ...... linear tones in [0, 1]. Uint16 x 4, normalized: 8 bytes for 12,
 *                the fourth an alpha of exactly 1. Sixteen bits and not eight on
 *                purpose: the tones are LINEAR, and eight bits there band the dark
 *                timber by a level or two once encoded; at sixteen a channel is off
 *                by at most 1/131070. The four channels switch three's
 *                `USE_COLOR_ALPHA`, which multiplies the alpha by that 1.
 *   uv (atlas) . a cell of the yard's mark atlas, in [0, 1]. Uint16 x 2,
 *                normalized: 4 bytes for 8.
 *
 * All three are decoded by WebGL's own normalized-attribute path, so no shader
 * changes and every patch that reads `normal` or `color` reads what it read.
 * `BufferAttribute.getX` denormalizes the same way, so a reader on the page (a
 * pick, the smoke's probes) sees the decoded value.
 *
 * WHAT STAYS FLOAT32, AND WHY. `position` is kept on the page for a tap and read
 * as metres by everything that asks where a board is; quantizing it means a
 * matrix per chunk and every reader made to apply it. `_confidence` is 0, 0.5 or
 * 1 and the shader bands on 0.5 exactly, which no 8-bit normalized value holds.
 * The grain `uv` / `uv1` are metres on a sheet a millimetre or two to the texel,
 * past what a half float holds at the board lengths laid. Each is left alone
 * rather than made approximately right.
 *
 * A stream that does not fit its compact range (a tone over 1, a normal longer
 * than one, a uv off the atlas) stays float32, whole: a compact copy that clamps
 * is a different picture.
 */

/**
 * The three builders, bound to the caller's three. This module imports nothing,
 * so the node checks that load a layer from source (check_plank_gap_filter.mjs
 * and its neighbours) resolve it as a plain file.
 */
export function compactStreams(THREE) {
  const EPS = 1e-6;

  /** The values as a Float32 attribute: the fallback, and today's layout. */
  const float32 = (src, size) => new THREE.BufferAttribute(
    src instanceof Float32Array ? src : Float32Array.from(src), size);

  /** Unit normals, xyz per vertex, as Int8 x 4 normalized (w = 0). */
  function compactNormals(src) {
    for (let i = 0; i < src.length; i += 1) {
      if (!(Math.abs(src[i]) <= 1 + EPS)) return float32(src, 3);
    }
    const out = new Int8Array((src.length / 3) * 4);
    for (let i = 0, j = 0; i < src.length; i += 3, j += 4) {
      out[j] = Math.round(Math.max(-1, Math.min(1, src[i])) * 127);
      out[j + 1] = Math.round(Math.max(-1, Math.min(1, src[i + 1])) * 127);
      out[j + 2] = Math.round(Math.max(-1, Math.min(1, src[i + 2])) * 127);
    }
    return new THREE.BufferAttribute(out, 4, true);
  }

  /** Linear rgb per vertex, as Uint16 x 4 normalized (a = 1). */
  function compactColors(src) {
    for (let i = 0; i < src.length; i += 1) {
      if (!(src[i] >= -EPS && src[i] <= 1 + EPS)) return float32(src, 3);
    }
    const out = new Uint16Array((src.length / 3) * 4);
    for (let i = 0, j = 0; i < src.length; i += 3, j += 4) {
      out[j] = Math.round(Math.max(0, Math.min(1, src[i])) * 65535);
      out[j + 1] = Math.round(Math.max(0, Math.min(1, src[i + 1])) * 65535);
      out[j + 2] = Math.round(Math.max(0, Math.min(1, src[i + 2])) * 65535);
      out[j + 3] = 65535;
    }
    return new THREE.BufferAttribute(out, 4, true);
  }

  /** Texture coordinates already in [0, 1], as Uint16 x 2 normalized. */
  function compactUnitUvs(src) {
    for (let i = 0; i < src.length; i += 1) {
      if (!(src[i] >= -EPS && src[i] <= 1 + EPS)) return float32(src, 2);
    }
    const out = new Uint16Array(src.length);
    for (let i = 0; i < src.length; i += 1) {
      out[i] = Math.round(Math.max(0, Math.min(1, src[i])) * 65535);
    }
    return new THREE.BufferAttribute(out, 2, true);
  }

  return { compactNormals, compactColors, compactUnitUvs };
}
