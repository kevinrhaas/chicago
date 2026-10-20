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
 * ONE DRAW, MANY BOXES (T-2700). A mesh too wide for one box is not cut into
 * meshes — one matrix a draw would be one box a draw, and T-2688 measured that
 * at 428 calls against a budget of 330. `packPositionBoxes` bins its triangles
 * into boxes the grid keeps and writes each vertex relative to its own box,
 * with the box's row in the material's table in the padding lane. The vertex
 * stage reads the row (`patchBoxTable`, and gpu-pick.js), the faces stay in
 * their order, and the mesh's matrix is the identity. Readers in metres take
 * `boxedPositionAt` or `positionsInMetres`; three's raycast is `raycastBoxed`;
 * a boxed caster's shadow is `boxDepthMaterial`.
 *
 * CONFIDENCE (T-2689) is 0, 0.5 or 1 and the shader bands on 0.5 exactly, which
 * no 8-bit normalized value holds — so it no longer has a float32 stream of its
 * own in these layers. It goes where there is room already paid for:
 *
 *   - frontage and the yard goods carry it in the colour's FOURTH lane, the one
 *     that was an alpha of exactly 1 (`setColorsAndConfidence`). Uint16 holds
 *     0, 0.50001 and 1; the shader rounds the lane to the nearest half, so it
 *     reads 0, 0.5 and 1 exactly (COLOR_LANE_CONFIDENCE), and it sets the
 *     varying colour's alpha back to the 1 it always was, so the blend of the
 *     frontage's transparent pass is what it was. 4 bytes a vertex for nothing.
 *   - the enclosures have no colour stream. A fence chunk's every vertex carries
 *     the weakest grade of its fence, so a chunk is almost always one grade
 *     whole: such a chunk carries NO confidence stream, records its grade on
 *     `geometry.userData.confidence`, and draws with a material whose shader
 *     reads that grade as a literal (`constantConfidence`). 4 bytes a vertex for
 *     nothing again.
 *
 * Either way only exactly 0, 0.5 and 1 move; a geometry carrying any other
 * value keeps the float32 `_confidence` it had (and a three-lane colour, so the
 * lane is never misread). A reader on the page asks `confidenceOf(geometry)`,
 * which hands back the per-vertex values wherever they are kept.
 *
 * WHAT STAYS FLOAT32, AND WHY. The grain `uv` / `uv1` are metres on a sheet a millimetre or two to the texel,
 * past what a half float holds at the board lengths laid. Each is left alone
 * rather than made approximately right.
 *
 * A stream that does not fit its compact range (a tone over 1, a normal longer
 * than one, a uv off the atlas) stays float32, whole: a compact copy that clamps
 * is a different picture.
 */

/**
 * The builders, bound to the caller's three. This module imports nothing,
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
    if (src && geometry.userData?.positionBoxes) {
      if (!src.array) return null;
      const out = new Float32Array(src.count * 3);
      const p = new THREE.Vector3();
      for (let i = 0; i < src.count; i += 1) {
        boxedPositionAt(geometry, i, p);
        out[i * 3] = p.x; out[i * 3 + 1] = p.y; out[i * 3 + 2] = p.z;
      }
      return new THREE.BufferAttribute(out, 3);
    }
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

  /** True when every value is exactly 0, 0.5 or 1: what a confidence lane holds. */
  const gradesOnly = (src) => {
    for (let i = 0; i < src.length; i += 1) {
      const v = src[i];
      if (v !== 0 && v !== 0.5 && v !== 1) return false;
    }
    return true;
  };

  /**
   * Set `geometry`'s `color` from linear rgb per vertex and put its confidence
   * (one value per vertex) in the colour's fourth lane (see the header). The
   * tones go Uint16 x 4 normalized where they fit, as `compactColors` writes
   * them, and Float32 x 4 where they do not; a confidence that is not all 0, 0.5
   * and 1 stays a float32 `_confidence` beside a three-lane colour.
   */
  function setColorsAndConfidence(geometry, colors, confidences) {
    const n = colors.length / 3;
    if (confidences.length !== n || !gradesOnly(confidences)) {
      geometry.setAttribute('color', float32(colors, 3));
      geometry.setAttribute('_confidence', float32(confidences, 1));
      return geometry;
    }
    let fits = true;
    for (let i = 0; i < colors.length; i += 1) {
      if (!(colors[i] >= -EPS && colors[i] <= 1 + EPS)) { fits = false; break; }
    }
    const out = fits ? new Uint16Array(n * 4) : new Float32Array(n * 4);
    for (let i = 0, j = 0; i < colors.length; i += 3, j += 4) {
      if (fits) {
        out[j] = Math.round(Math.max(0, Math.min(1, colors[i])) * 65535);
        out[j + 1] = Math.round(Math.max(0, Math.min(1, colors[i + 1])) * 65535);
        out[j + 2] = Math.round(Math.max(0, Math.min(1, colors[i + 2])) * 65535);
        out[j + 3] = Math.round(confidences[i / 3] * 65535);
      } else {
        out[j] = colors[i]; out[j + 1] = colors[i + 1]; out[j + 2] = colors[i + 2];
        out[j + 3] = confidences[i / 3];
      }
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(out, 4, fits));
    geometry.deleteAttribute('_confidence');
    geometry.userData.confidenceLane = 'color';
    return geometry;
  }

  /**
   * One grade for a whole geometry, or null: the value when every vertex holds
   * the same exact 0, 0.5 or 1, which is when a chunk can drop its stream and
   * draw with `constantConfidence(value)`.
   */
  function uniformGrade(confidences) {
    if (!confidences.length || !gradesOnly(confidences)) return null;
    const v = confidences[0];
    for (let i = 1; i < confidences.length; i += 1) if (confidences[i] !== v) return null;
    return v;
  }

  /**
   * A geometry's confidence per vertex, wherever it is kept: its own float
   * `_confidence`, the colour's fourth lane, or the one grade on
   * `userData.confidence`. Null where there is none, or where the array it
   * would be read from has been let go of after upload (upload-release.js).
   */
  function confidenceOf(geometry) {
    const own = geometry?.getAttribute('_confidence');
    if (own) return own;
    const position = geometry?.getAttribute('position');
    if (!position) return null;
    if (geometry.userData?.confidenceLane === 'color') {
      const color = geometry.getAttribute('color');
      if (!color?.array) return null;
      const out = new Float32Array(color.count);
      for (let i = 0; i < color.count; i += 1) out[i] = laneGrade(color.getW(i));
      return new THREE.BufferAttribute(out, 1);
    }
    const v = geometry.userData?.confidence;
    if (typeof v !== 'number') return null;
    return new THREE.BufferAttribute(new Float32Array(position.count).fill(v), 1);
  }

  /* ------------------------------------------------ one draw, many boxes (T-2700) */

  /**
   * A MATERIAL'S BOX TABLE: the pieces of every mesh drawn with it, in lane
   * order. `values` is flat, four numbers a piece (centre x, y, z and the
   * uniform half-extent), and `uniform` is what the vertex stage reads.
   */
  function createBoxTable() {
    return { count: 0, values: [], uniform: { value: new Float32Array(4) },
      materials: new Set(), depth: null };
  }

  /** Write `flat` (four numbers a piece) into the table from piece `first` on. */
  function writeBoxes(table, first, flat) {
    const count = Math.max(table.count, first + flat.length / 4);
    for (let i = 0; i < flat.length; i += 1) table.values[first * 4 + i] = flat[i];
    const grew = boxSlots(table) !== Math.max(1, count);
    table.count = count;
    table.uniform.value = new Float32Array(Math.max(4, count * 4));
    table.uniform.value.set(Array.from(table.values, (v) => v ?? 0));
    // The array's length is compiled into the program, so a table that grew
    // after a compile has every material that reads it compile again.
    if (grew) for (const m of table.materials) m.needsUpdate = true;
  }

  /**
   * CUT A MESH INTO BOXES THE GRID KEEPS, AND KEEP IT ONE MESH (T-2700). A
   * non-indexed float32 triangle mesh is binned, triangle by triangle on its
   * centre, into cells the 16-bit grid keeps to the millimetre (T-2688's cut:
   * the widest box `quantizeMeshPositions` keeps, less the widest triangle).
   * Each non-empty cell is a piece, and each piece's box goes into `table`. The
   * positions are written as Int16 x 4 normalized: xyz relative to the vertex's
   * own piece, and the padding lane w naming that piece (`lane / 32767`, the
   * lane being the piece's row in the table plus one, so a lane of 0 — every
   * quantized chunk's — and a float position's implied w of 1 name none).
   *
   * NOTHING IS REORDERED. Every face stays where it was, so a pick span, a lot
   * item's span, a walk-top range and `gl_VertexID` read as they read before,
   * and the mesh is still ONE draw: the vertex stage reads the box (see
   * `patchBoxTable`). Returns false and leaves the geometry alone when it
   * cannot be cut (indexed, interleaved, not float xyz, a triangle wider than
   * the box) or the table has no room left.
   */
  function packPositionBoxes(geometry, table, maxErrorM = POSITION_ERROR_M) {
    const src = geometry.getAttribute('position');
    if (geometry.index || !src || src.isInterleavedBufferAttribute || src.itemSize !== 3
      || !(src.array instanceof Float32Array) || !src.count || src.count % 3) return false;
    const box = 4 * POSITION_STEPS * maxErrorM;
    const a = src.array;
    const faces = src.count / 3;
    const lo = [Infinity, Infinity, Infinity];
    const hi = [-Infinity, -Infinity, -Infinity];
    const mid = new Float64Array(faces * 3);
    let widest = 0;
    for (let f = 0; f < faces; f += 1) {
      for (let c = 0; c < 3; c += 1) {
        const x0 = a[f * 9 + c], x1 = a[f * 9 + 3 + c], x2 = a[f * 9 + 6 + c];
        const tlo = Math.min(x0, x1, x2), thi = Math.max(x0, x1, x2);
        if (tlo < lo[c]) lo[c] = tlo;
        if (thi > hi[c]) hi[c] = thi;
        if (thi - tlo > widest) widest = thi - tlo;
        mid[f * 3 + c] = (tlo + thi) / 2;
      }
    }
    // A centre inside the cell puts its triangle inside the cell widened by half
    // the widest triangle each side; the millimetre left over covers rounding.
    const cell = box - widest - 0.001;
    if (!(cell > 0)) return false;
    const n = [0, 1, 2].map((c) => Math.floor((hi[c] - lo[c]) / cell) + 1);
    const keyOf = new Float64Array(faces);
    for (let f = 0; f < faces; f += 1) {
      let key = 0;
      for (let c = 2; c >= 0; c -= 1) {
        key = key * n[c] + Math.min(n[c] - 1, Math.floor((mid[f * 3 + c] - lo[c]) / cell));
      }
      keyOf[f] = key;
    }
    const keys = [...new Set(keyOf)].sort((x, y) => x - y);
    if (table.count + keys.length > BOX_TABLE_MAX) return false;
    const pieceOf = new Map(keys.map((k, i) => [k, i]));
    const plo = new Float64Array(keys.length * 3).fill(Infinity);
    const phi = new Float64Array(keys.length * 3).fill(-Infinity);
    const piece = new Uint16Array(faces);
    for (let f = 0; f < faces; f += 1) {
      const p = pieceOf.get(keyOf[f]);
      piece[f] = p;
      for (let v = 0; v < 9; v += 1) {
        const x = a[f * 9 + v], c = p * 3 + (v % 3);
        if (x < plo[c]) plo[c] = x;
        if (x > phi[c]) phi[c] = x;
      }
    }
    const flat = new Array(keys.length * 4);
    for (let p = 0; p < keys.length; p += 1) {
      let half = 0;
      for (let c = 0; c < 3; c += 1) {
        flat[p * 4 + c] = (plo[p * 3 + c] + phi[p * 3 + c]) / 2;
        half = Math.max(half, (phi[p * 3 + c] - plo[p * 3 + c]) / 2);
      }
      // NaN fails the comparison, so a mesh carrying one stays float.
      if (!(half / POSITION_STEPS / 2 <= maxErrorM)) return false;
      flat[p * 4 + 3] = half > 0 ? half : 1;
    }
    const first = table.count;
    const out = new Int16Array(src.count * 4);
    for (let f = 0; f < faces; f += 1) {
      const p = piece[f];
      const k = POSITION_STEPS / flat[p * 4 + 3];
      for (let v = 0; v < 3; v += 1) {
        const i = f * 9 + v * 3, j = (f * 3 + v) * 4;
        for (let c = 0; c < 3; c += 1) {
          out[j + c] = Math.max(-POSITION_STEPS, Math.min(POSITION_STEPS,
            Math.round((a[i + c] - flat[p * 4 + c]) * k)));
        }
        out[j + 3] = first + p + 1;
      }
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(out, 4, true));
    geometry.userData.positionBoxes = { first, boxes: flat };
    adoptPositionBoxes(geometry, table);
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
    return true;
  }

  /**
   * Put a boxed geometry's pieces into `table` at the rows its lanes name — a
   * prebuilt mesh arrives encoded (frontage.js `prebuiltGeometry`) — and make
   * it boxed on the page: its lane bound for the vertex stage, and its bounds
   * read in metres rather than off the -1..1 the grid stores.
   */
  function adoptPositionBoxes(geometry, table) {
    const pb = geometry.userData?.positionBoxes;
    if (!pb) return false;
    if (pb.first + pb.boxes.length / 4 > BOX_TABLE_MAX) return false;
    writeBoxes(table, pb.first, pb.boxes);
    ensureBoxLane(geometry);
    geometry.computeBoundingBox = function computeBoundingBox() {
      const m = positionsInMetres(this);
      if (m) (this.boundingBox ??= new THREE.Box3()).setFromBufferAttribute(m);
    };
    geometry.computeBoundingSphere = function computeBoundingSphere() {
      const m = positionsInMetres(this);
      if (!m) return;
      const c = new THREE.Box3().setFromBufferAttribute(m).getCenter(new THREE.Vector3());
      const v = new THREE.Vector3();
      let r2 = 0;
      for (let i = 0; i < m.count; i += 1) r2 = Math.max(r2, c.distanceToSquared(v.fromBufferAttribute(m, i)));
      (this.boundingSphere ??= new THREE.Sphere()).set(c, Math.sqrt(r2));
    };
    return true;
  }

  /**
   * Vertex `i` of `geometry` in its MESH's frame — what the vertex stage hands
   * the model matrix. A boxed geometry's piece is applied; a quantized one is
   * left on its -1..1 grid for the mesh's matrix to undo, as three would.
   */
  function boxedPositionAt(geometry, i, target) {
    const src = geometry.getAttribute('position');
    target.fromBufferAttribute(src, i);
    const pb = geometry.userData?.positionBoxes;
    if (!pb) return target;
    const j = (Math.round(src.getW(i) * POSITION_STEPS) - 1 - pb.first) * 4;
    const b = pb.boxes;
    return target.set(target.x * b[j + 3] + b[j], target.y * b[j + 3] + b[j + 1],
      target.z * b[j + 3] + b[j + 2]);
  }

  /**
   * THE LANE, BOUND UNDER ITS OWN NAME. three declares `position` as a vec3,
   * so no shader of a stock material can read its fourth lane. So the same
   * attribute is handed to the vertex stage a second time, as `aChiBox`, a
   * vec4 — the same object, so the same GPU buffer and not a byte more. It is
   * a getter that is not enumerable: every reader that walks a geometry's
   * attributes (the far merge, the prebuild, upload-release, the memory
   * readings) sees the streams it always saw, and three, which looks a
   * program's attributes up by name, finds it. A float position bound there
   * reads w = 1, which names no box.
   */
  function ensureBoxLane(geometry) {
    const attrs = geometry?.attributes;
    if (!attrs || Object.prototype.hasOwnProperty.call(attrs, BOX_LANE)) return;
    Object.defineProperty(attrs, BOX_LANE, {
      get() { return this.position; }, enumerable: false, configurable: true,
    });
  }

  const boxSlots = (table) => Math.max(1, table.count);

  /**
   * Decode the box in the vertex stage of `material` (T-2700): right after
   * `<begin_vertex>`, so every patch after it — the plank-gap filter, the
   * confidence — reads `transformed` in the mesh's metres, exactly as it read a
   * float mesh's. Every mesh drawn with the material has its lane bound as it
   * is drawn; one that names no box draws as it always did. Patch LAST, after
   * any `customProgramCacheKey` of the layer's own: the key gains the table's
   * length, which is compiled into the program.
   */
  function patchBoxTable(material, table) {
    table.materials.add(material);
    material.userData.boxTable = table;
    const prior = material.onBeforeCompile;
    material.onBeforeCompile = function (shader, renderer) {
      prior?.call(this, shader, renderer);
      shader.uniforms.uChiBoxes = table.uniform;
      const slots = boxSlots(table);
      shader.vertexShader = `attribute vec4 ${BOX_LANE};\nuniform vec4 uChiBoxes[${slots}];\n`
        + shader.vertexShader.replace('#include <begin_vertex>', /* glsl */`#include <begin_vertex>
{
  int chiBox = int(${BOX_LANE}.w * ${POSITION_STEPS}.0 + 0.5) - 1;
  if (chiBox >= 0 && chiBox < ${slots}) {
    transformed = transformed * uChiBoxes[chiBox].w + uChiBoxes[chiBox].xyz;
  }
}`);
    };
    const key = material.customProgramCacheKey;
    material.customProgramCacheKey = function customProgramCacheKey() {
      return `${key.call(this)}|boxes:${boxSlots(table)}`;
    };
    const before = material.onBeforeRender;
    material.onBeforeRender = function (renderer, scene, camera, geometry, ...rest) {
      before?.call(this, renderer, scene, camera, geometry, ...rest);
      ensureBoxLane(geometry);
    };
    material.needsUpdate = true;
    return material;
  }

  /**
   * The sun's pass for a boxed mesh: three's own depth material, decoding the
   * box. Without it a caster's shadow is drawn from the -1..1 grid, a blob at
   * the origin. One per table.
   */
  function boxDepthMaterial(table) {
    if (table.depth) return table.depth;
    const m = new THREE.MeshDepthMaterial();
    m.name = 'box-table-depth';
    m.customProgramCacheKey = () => 'chicago4d-box-table-depth';
    table.depth = patchBoxTable(m, table);
    return m;
  }

  const _inverse = new THREE.Matrix4();
  const _ray = new THREE.Ray();
  const _sphere = new THREE.Sphere();
  const _tri = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  const _hit = new THREE.Vector3();
  const _corner = [0, 0, 0];

  /**
   * `Mesh.raycast` for a boxed mesh: three's own reads the -1..1 grid. The
   * same test — the sphere, then each face against the ray in the mesh's frame,
   * culled by the material's side — over the decoded positions, the faces an
   * index and draw range name where the mesh has them (the far walk tops,
   * T-2701), as three's own walks them. Assigned as `mesh.raycast`; a mesh
   * whose arrays were let go of answers nothing, as the raycast never could.
   */
  function raycastBoxed(raycaster, intersects) {
    const geo = this.geometry;
    const pos = geo?.getAttribute('position');
    const index = geo?.index;
    if (!pos?.array || (index && !index.array) || !geo.boundingSphere) return;
    _sphere.copy(geo.boundingSphere).applyMatrix4(this.matrixWorld);
    if (!raycaster.ray.intersectsSphere(_sphere)) return;
    _inverse.copy(this.matrixWorld).invert();
    _ray.copy(raycaster.ray).applyMatrix4(_inverse);
    const side = Array.isArray(this.material) ? THREE.DoubleSide : this.material.side;
    const start = Math.max(0, geo.drawRange.start);
    const end = Math.min(index ? index.count : pos.count, geo.drawRange.start + geo.drawRange.count);
    for (let i = start; i + 2 < end; i += 3) {
      const f = Math.floor(i / 3);
      for (let v = 0; v < 3; v += 1) _corner[v] = index ? index.getX(i + v) : i + v;
      for (let v = 0; v < 3; v += 1) boxedPositionAt(geo, _corner[v], _tri[v]);
      const [va, vb, vc] = _tri;
      const got = side === THREE.BackSide ? _ray.intersectTriangle(vc, vb, va, true, _hit)
        : _ray.intersectTriangle(va, vb, vc, side === THREE.FrontSide, _hit);
      if (!got) continue;
      const point = _hit.clone().applyMatrix4(this.matrixWorld);
      const distance = raycaster.ray.origin.distanceTo(point);
      if (distance < raycaster.near || distance > raycaster.far) continue;
      const normal = new THREE.Vector3();
      THREE.Triangle.getNormal(va, vb, vc, normal);
      intersects.push({ distance, point, object: this, faceIndex: f,
        face: { a: _corner[0], b: _corner[1], c: _corner[2], normal, materialIndex: 0 } });
    }
  }

  return {
    compactNormals, compactColors, compactUnitUvs, quantizeMeshPositions, positionsInMetres,
    setColorsAndConfidence, uniformGrade, confidenceOf,
    createBoxTable, packPositionBoxes, adoptPositionBoxes, boxedPositionAt, ensureBoxLane,
    patchBoxTable, boxDepthMaterial, raycastBoxed,
  };
}

/** A colour lane's value read back as its grade: the nearest half, as the shader reads it. */
export const laneGrade = (w) => Math.floor(w * 2 + 0.5) / 2;

/**
 * The `packed` channel `confidence.patch` takes for a material whose geometries
 * keep their confidence in the colour's fourth lane (`setColorsAndConfidence`).
 * three declares `color` as a vec4 only when the geometry's colour has four
 * lanes (USE_COLOR_ALPHA); a geometry that kept a float `_confidence` has three
 * and compiles the other branch. Inserted after `begin_vertex`, which three
 * includes after `color_vertex`, so the varying alpha it puts back is final.
 */
export const COLOR_LANE_CONFIDENCE = {
  key: 'color-lane',
  assign: `
  #ifdef USE_COLOR_ALPHA
    vConfidence = floor( color.a * 2.0 + 0.5 ) * 0.5;
    vColor.a = 1.0;
  #else
    vConfidence = ( _confidence == _confidence ) ? clamp( _confidence, 0.0, 1.0 ) : 0.0;
  #endif`,
  declare(vertexShader) {
    const decl = '#ifndef USE_COLOR_ALPHA\nattribute float _confidence;\n#endif\n';
    return vertexShader.includes(decl) ? vertexShader : decl + vertexShader;
  },
};

/** The `packed` channel for a material that draws geometries of one grade. */
export function constantConfidence(value) {
  const v = Math.min(1, Math.max(0, Number(value) || 0));
  const glsl = Number.isInteger(v) ? v.toFixed(1) : String(v);
  return { key: `constant:${glsl}`, read: glsl, declare: (vertexShader) => vertexShader };
}

/** Int16's normalized range: WebGL decodes `q` as `max(q / 32767, -1)`. */
export const POSITION_STEPS = 32767;

/** The most a quantized position may move a vertex (T-2687): one millimetre. */
export const POSITION_ERROR_M = 0.001;

/**
 * The rows a box table holds (T-2700): a vec4 each in the vertex stage. 128 is
 * half of what WebGL 2 promises a vertex shader at the least (256 vectors), so
 * three's own uniforms keep the rest; gpu-pick.js reads the same table.
 */
export const BOX_TABLE_MAX = 128;

/** The name a boxed position's lane is bound under for the vertex stage. */
export const BOX_LANE = 'aChiBox';
