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
 * POSITIONS (T-2687) are their own case, because a position is in no fixed
 * range: `quantizeMeshPositions` writes a mesh's float positions as Int16 x 4,
 * normalized, relative to the mesh's own box, and puts the box's centre and its
 * half-extent into the MESH's matrix (position and a uniform scale), so the
 * vertex stage's own model matrix undoes it. 8 bytes for 12; the fourth lane is
 * padding to the four-byte stride. Three things follow from that:
 *
 *   - ONLY WHERE THE GRID KEEPS THE MILLIMETRE. One step is half-extent / 32767,
 *     so a vertex moves by at most half of one. A mesh is quantized when that is
 *     within `POSITION_ERROR_M` (1 mm: a half-extent up to 65.5 m) and is left
 *     float32 otherwise. The boards are 20 mm apart and a fence board is 22 mm
 *     thick, so a grid of a centimetre — what a town-long walk would get — moves
 *     the gaps a visitor can see. The long meshes are cut first (T-2688).
 *   - THE SCALE IS UNIFORM, so three's normal matrix only shortens the normal
 *     and the shader's normalize undoes it (compact-attributes.js says the same
 *     of the structures batch, T-2575).
 *   - ANYTHING THAT READS A POSITION AS METRES APPLIES THE MESH'S MATRIX, or
 *     reads `positionsInMetres(geometry)`. `BufferAttribute.getX` decodes to the
 *     -1..1 the GPU sees, not to metres; a raycast or a GPU pick goes through
 *     `matrixWorld` already and is unchanged. Inside a shader, a delta authored
 *     in metres in the mesh's frame is divided by the model matrix's scale
 *     (frontage.js, the plank-gap filter).
 *
 * WHAT STAYS FLOAT32, AND WHY. `_confidence` is 0, 0.5 or
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

  /**
   * Rewrite `mesh`'s float positions as Int16 x 4 normalized over its own box,
   * and move the box into the mesh's matrix (see the header). Leaves the mesh
   * exactly as it was, and returns false, when the grid would move a vertex by
   * more than `maxErrorM`, when the positions are not plain float xyz, or when
   * the mesh already carries a transform of its own.
   */
  function quantizeMeshPositions(mesh, maxErrorM = POSITION_ERROR_M) {
    const geo = mesh.geometry;
    const src = geo.getAttribute('position');
    if (!src || src.isInterleavedBufferAttribute || src.itemSize !== 3
      || !(src.array instanceof Float32Array) || !src.count) return false;
    if (mesh.position.lengthSq() !== 0 || mesh.scale.x !== 1 || mesh.scale.y !== 1
      || mesh.scale.z !== 1 || mesh.quaternion.w !== 1) return false;
    const a = src.array;
    const lo = [Infinity, Infinity, Infinity];
    const hi = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < a.length; i += 3) {
      for (let c = 0; c < 3; c += 1) {
        const v = a[i + c];
        if (v < lo[c]) lo[c] = v;
        if (v > hi[c]) hi[c] = v;
      }
    }
    const mid = [0, 1, 2].map((c) => (lo[c] + hi[c]) / 2);
    const half = Math.max(...[0, 1, 2].map((c) => (hi[c] - lo[c]) / 2));
    // NaN fails the comparison, so a mesh carrying one stays float.
    if (!(half / POSITION_STEPS / 2 <= maxErrorM)) return false;
    const scale = half > 0 ? half : 1;
    const k = POSITION_STEPS / scale;
    const out = new Int16Array(src.count * 4);
    for (let i = 0, j = 0; i < a.length; i += 3, j += 4) {
      for (let c = 0; c < 3; c += 1) {
        out[j + c] = Math.max(-POSITION_STEPS, Math.min(POSITION_STEPS,
          Math.round((a[i + c] - mid[c]) * k)));
      }
    }
    geo.setAttribute('position', new THREE.BufferAttribute(out, 4, true));
    geo.userData.positionQuantized = { offset: mid, scale };
    // Bounds in metres are wrong by the matrix now. Re-read them off the stored
    // positions, which is the frame every reader of them applies the matrix to.
    geo.boundingBox = null;
    geo.computeBoundingSphere();
    mesh.position.set(mid[0], mid[1], mid[2]);
    mesh.scale.setScalar(scale);
    mesh.updateMatrix();
    return true;
  }

  /**
   * A geometry's positions in metres in its mesh's parent frame — what they
   * were before `quantizeMeshPositions` — as a float32 attribute. A geometry
   * that was never quantized hands back its own attribute; one whose array has
   * been let go of after upload (upload-release.js) hands back null.
   */
  function positionsInMetres(geometry) {
    const src = geometry?.getAttribute('position');
    const q = geometry?.userData?.positionQuantized;
    if (!src || !q) return src ?? null;
    if (!src.array) return null;
    const out = new Float32Array(src.count * 3);
    for (let i = 0; i < src.count; i += 1) {
      out[i * 3] = src.getX(i) * q.scale + q.offset[0];
      out[i * 3 + 1] = src.getY(i) * q.scale + q.offset[1];
      out[i * 3 + 2] = src.getZ(i) * q.scale + q.offset[2];
    }
    return new THREE.BufferAttribute(out, 3);
  }

  return { compactNormals, compactColors, compactUnitUvs, quantizeMeshPositions, positionsInMetres };
}

/** Int16's normalized range: WebGL decodes `q` as `max(q / 32767, -1)`. */
export const POSITION_STEPS = 32767;

/** The most a quantized position may move a vertex (T-2687): one millimetre. */
export const POSITION_ERROR_M = 0.001;
