/**
 * T-3286 — A FAR STRUCTURE CASTS ITS SHADOW FROM A COARSER COPY OF ITSELF.
 *
 * The sun's pass drew every structure piece inside its box whole, whatever its
 * distance from the visitor. Looking north up Prairie at Glessner from 60 m east
 * and 120 m south (T-3285's worst far stand, Full, 1280x800), the structures' sun
 * pass was 3,080,120 of the frame's 7.29 M triangles, in 1,191 pieces, and none of
 * those pieces is small: a house is about 25 of them, 16-64 px across on screen
 * there, so no piece can simply be left out. What a far piece CAN leave out is its
 * fine relief: Glessner's rusticated stone and tile courses, the mouldings and
 * frames of every neighbour, detail measured in millimetres that the shadow map
 * (a 0.117 m texel at `full`, world.js) cannot hold anyway.
 *
 * So each heavy piece gets a SHADOW TWIN, cut once at load by vertex clustering:
 * the piece's vertices are pooled in cells of CELL_M (and never across two
 * confidence values, so the depth material's dither stays where it was), each
 * pool becomes one vertex at its centroid, and every triangle whose three corners
 * do not land in three different pools is dropped. A twin is kept only where it
 * pays: at most KEEP_RATIO of the piece's triangles and at least MIN_SAVED fewer.
 * At CELL_M = 6 cm that is about a hundred pieces town-wide in 1904; Glessner's
 * 1.17 M sun-pass triangles at the far stand become about 25,000.
 *
 * THE TEST IS A BOUND ON THE SCREEN, taken from the VIEW camera. A twin vertex
 * sits at most sqrt(3) * CELL_M from every piece vertex it stands for (a centroid
 * of points in one cube), so a shadow edge it casts moves at most that far across
 * the light, and on the receiver at most that over the sine of the sun's height.
 * The piece is swapped for its twin in the sun's pass only where that movement
 * projects to at most MAX_PIXELS at the nearest view depth its shadow can land
 * on — the piece's bounding sphere swept down the sun's direction to
 * FLOOR_BELOW_M under its base, as shadow-casters.js sweeps it. Nearer than that,
 * or with the sun too low to bound the sweep, the piece casts whole as before.
 * It is an LOD of the shadow map, not a proof: an edge may move by up to a
 * pixel, and tools/qa_t3286_far_shadow.mjs reads every pixel of each held frame
 * back off and on to say how many did.
 *
 * The colour pass never draws a twin: it sits hidden the rest of the time, so
 * picking, the Confidence view and every reader of the batch see the piece
 * exactly as before, and the swap is undone the moment the shadow draw list is
 * prepared, the way shadow-casters.js and far-roof-relief.js do it.
 *
 * `?farshadow=0` turns it off, for the on/off pixel proof.
 */
import * as THREE from 'three';
import { FLOOR_BELOW_M } from './shadow-casters.js';

/** The clustering cell, in metres of the structure's own frame. */
export const CELL_M = 0.06;
/** The most a swapped shadow edge may move on screen, in pixels. */
export const MAX_PIXELS = 1;
/** A twin is kept only at or under this share of its piece's triangles... */
export const KEEP_RATIO = 0.5;
/** ...and only if it draws at least this many triangles fewer. */
export const MIN_SAVED = 500;
/**
 * T-3249 — ON A PHONE AT `light`, A STRUCTURE CASTS FROM ONE TEXEL TWIN OF ITSELF, NEAR AS
 * WELL AS FAR.
 *
 * The phone's sun pass (T-3247, 1904, 390x780, south from 1801 Prairie) drew about 600 k
 * structure triangles into a map whose texel is 23.4 cm: cornices, reveals, mullions, sash
 * and trim under a texel cost triangles there and change no texel. So a low-spec build for
 * a tier below `full` cuts, per structure and per batch it lies in, ONE twin of all its
 * pieces by the same vertex clustering at SUN_CELL_M, and the tier's TEXEL bound swaps it in
 * wherever the twin's edge moves no more than one texel of the map: sqrt(3) * 0.12 =
 * 0.208 m against 0.234 m. That bound is in the light's own frame, so it holds at any
 * distance from the visitor. (A desktop's `light` map is 11.7 cm, so it would never swap
 * one there, and none is cut.)
 *
 * The twin keeps NO VERTEX of its own. Each pool is drawn at the member vertex nearest its
 * centroid (inside the same cell, so the reach is unchanged) and the twin is only an index
 * into its pieces' vertices, which `rebaseGroupTwin` points at their ranges once they are
 * in the batch. One twin per structure, not per piece: 1904's 102 k structure pieces lie
 * in about 1,100 (batch, structure) groups. Measured on the phone (/1904/, resident
 * estimate, dev 375.6 MB): a centroid twin per piece cost +24.1 MB, a shared one per piece
 * +13.3 (its twenty thousand instance records), and this +6.7.
 *
 * A group is swapped only (a) while every one of its pieces is shown, so a piece another
 * hook has hidden is never cast by its twin, and (b) where its twin draws fewer triangles
 * than its pieces would: those whose shadow can reach the view (shadow-casters.js's test)
 * inside the sun's box, each at its own far twin's count. Otherwise the per-piece path
 * above stands. `full` and `balanced` never swap one (a phone's `balanced` shares
 * `light`'s batches, so it carries them) and keep the screen bound alone.
 */
export const SUN_CELL_M = 0.12;
/** A texel twin is kept at or under this share of its group's triangles... */
export const SUN_KEEP_RATIO = 0.6;
/** ...and only if it draws at least this many fewer. */
export const SUN_MIN_SAVED = 64;
/** Below this sine of the sun's height the sweep grows without bound: cast whole. */
const LOW_SUN = 0.05;
/** The farthest a twin vertex sits from any vertex it stands for, per metre of cell. */
const CENTROID_REACH = Math.sqrt(3);

export function farShadowFromSearch(search) {
  try { return new URLSearchParams(search ?? '').get('farshadow') !== '0'; } catch { return true; }
}

/**
 * The clustered twin of one piece, or null when it would not pay.
 * @param {THREE.BufferGeometry} geo  an indexed, non-interleaved piece, in its own frame
 * @param {number} cell  the cell in the geometry's units (CELL_M over the placement's scale)
 */
export function shadowTwin(geo, cell, { byNormal = false, keepRatio = KEEP_RATIO } = {}) {
  const index = geo.getIndex();
  const position = geo.getAttribute('position');
  if (!index || !position || !(cell > 0)) return null;
  if (Object.values(geo.attributes).some((a) => a.isInterleavedBufferAttribute)) return null;
  const ix = index.array;
  const triangles = ix.length / 3;
  if (triangles < MIN_SAVED) return null;
  const confidence = geo.getAttribute('_confidence');
  // T-3312: `byNormal` also keeps apart vertices whose normals differ (by a 1/16 grid on
  // each axis), so a face that survives the cut is shaded by its own normal: the colour
  // pass reads it, where the sun's depth pass never did (far-colour.js).
  const normal = byNormal ? geo.getAttribute('normal') : null;
  if (byNormal && !normal) return null;
  const NQ = 16, NAXIS = 2 * NQ + 1;
  const normalKey = (v) => ((Math.round(normal.getX(v) * NQ) + NQ) * NAXIS
    + Math.round(normal.getY(v) * NQ) + NQ) * NAXIS + Math.round(normal.getZ(v) * NQ) + NQ;
  const byKey = new Map();
  const n = position.count;
  const pa = position.array;
  const stride = position.itemSize;
  const pool = new Int32Array(n);
  // A cell is three 15-bit axes and the confidence's byte (as packScalars stores it), one
  // exact integer under 2^53, so the pools key a Map by number: about a third of a
  // second for the 1904 town's every piece, where string keys took two.
  const keyOf = new Map();
  const first = [];
  const sum = [];
  let ox = Infinity, oy = Infinity, oz = Infinity;
  for (let v = 0; v < n; v++) {
    const o = v * stride;
    if (pa[o] < ox) ox = pa[o];
    if (pa[o + 1] < oy) oy = pa[o + 1];
    if (pa[o + 2] < oz) oz = pa[o + 2];
  }
  const AXIS = 32768;
  for (let v = 0; v < n; v++) {
    const o = v * stride;
    const x = pa[o], y = pa[o + 1], z = pa[o + 2];
    const cx = Math.floor((x - ox) / cell), cy = Math.floor((y - oy) / cell), cz = Math.floor((z - oz) / cell);
    if (cx >= AXIS || cy >= AXIS || cz >= AXIS) return null; // a piece over ~2 km: leave it whole
    const c = confidence ? Math.round(Math.min(1, Math.max(0, confidence.getX(v))) * 254) : 0;
    const key = ((c * AXIS + cx) * AXIS + cy) * AXIS + cz;
    let cells = keyOf;
    if (normal) {
      const nk = normalKey(v);
      cells = byKey.get(nk);
      if (!cells) { cells = new Map(); byKey.set(nk, cells); }
    }
    let p = cells.get(key);
    if (p === undefined) {
      p = first.length;
      cells.set(key, p);
      first.push(v);
      sum.push(0, 0, 0, 0);
    }
    pool[v] = p;
    sum[p * 4] += x; sum[p * 4 + 1] += y; sum[p * 4 + 2] += z; sum[p * 4 + 3] += 1;
  }
  const pools = first.length;
  const kept = [];
  const seen = new Set();
  for (let t = 0; t < ix.length; t += 3) {
    const a = pool[ix[t]], b = pool[ix[t + 1]], c = pool[ix[t + 2]];
    if (a === b || b === c || a === c) continue;
    // one triangle per pooled corner set and winding: a duplicate adds no depth
    let r0 = a, r1 = b, r2 = c;
    if (b < a && b < c) { r0 = b; r1 = c; r2 = a; } else if (c < a && c < b) { r0 = c; r1 = a; r2 = b; }
    const key = (r0 * pools + r1) * pools + r2;
    if (key > Number.MAX_SAFE_INTEGER) return null; // over ~200,000 pools: leave it whole
    if (seen.has(key)) continue;
    seen.add(key);
    kept.push(a, b, c);
  }
  const twinTriangles = kept.length / 3;
  if (twinTriangles > triangles * keepRatio || triangles - twinTriangles < MIN_SAVED) return null;
  // only the pools a kept triangle uses
  const remap = new Int32Array(first.length).fill(-1);
  const order = [];
  for (let i = 0; i < kept.length; i++) {
    const p = kept[i];
    if (remap[p] < 0) { remap[p] = order.length; order.push(p); }
    kept[i] = remap[p];
  }
  const twin = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(geo.attributes)) {
    const size = attr.itemSize;
    const data = new attr.array.constructor(order.length * size);
    for (let i = 0; i < order.length; i++) {
      const p = order[i];
      if (name === 'position') {
        // the centroid: inside the piece's own extent, so it quantizes on the structure's grid
        const w = sum[p * 4 + 3];
        data[i * 3] = sum[p * 4] / w; data[i * 3 + 1] = sum[p * 4 + 1] / w; data[i * 3 + 2] = sum[p * 4 + 2] / w;
      } else {
        // every other attribute is its pool's first vertex: the depth pass reads only
        // the confidence, and the pool never mixes two of those
        for (let k = 0; k < size; k++) data[i * size + k] = attr.array[first[p] * size + k];
      }
    }
    twin.setAttribute(name, new THREE.BufferAttribute(data, size, attr.normalized));
  }
  const fits16 = order.length <= 65535;
  twin.setIndex(new THREE.BufferAttribute(fits16 ? Uint16Array.from(kept) : Uint32Array.from(kept), 1));
  twin.userData = { ...geo.userData };
  return { geo: twin, triangles, twinTriangles, reach: CENTROID_REACH * cell };
}

/**
 * T-3249: the texel twin of one structure's pieces in one batch, or null when it would
 * not pay. `geos` share the structure's frame and the batch's attribute set; `cell` is
 * SUN_CELL_M over the placement's scale. Returns an index-only geometry (every attribute
 * empty, in the pieces' own formats) whose values are vertex numbers counted through the
 * pieces in order, and the `segments` that say which piece each number falls in.
 */
export function groupTwin(geos, cell, { keepRatio = SUN_KEEP_RATIO, minSaved = SUN_MIN_SAVED } = {}) {
  if (!(cell > 0) || !geos.length) return null;
  const segments = [];
  let n = 0, triangles = 0;
  for (const g of geos) {
    const position = g.getAttribute('position');
    if (!g.getIndex() || !position) return null;
    if (Object.values(g.attributes).some((a) => a.isInterleavedBufferAttribute)) return null;
    segments.push({ offset: n, count: position.count });
    n += position.count;
    triangles += g.getIndex().count / 3;
  }
  if (triangles < minSaved) return null;
  let ox = Infinity, oy = Infinity, oz = Infinity;
  for (const g of geos) {
    const position = g.getAttribute('position'), pa = position.array, stride = position.itemSize;
    for (let o = 0; o < pa.length; o += stride) {
      if (pa[o] < ox) ox = pa[o];
      if (pa[o + 1] < oy) oy = pa[o + 1];
      if (pa[o + 2] < oz) oz = pa[o + 2];
    }
  }
  const AXIS = 32768;
  const pool = new Int32Array(n);
  const keyOf = new Map();
  const sum = [];
  let pools = 0;
  for (let k = 0; k < geos.length; k++) {
    const position = geos[k].getAttribute('position'), pa = position.array, stride = position.itemSize;
    const confidence = geos[k].getAttribute('_confidence');
    const base = segments[k].offset;
    for (let v = 0; v < position.count; v++) {
      const o = v * stride;
      const x = pa[o], y = pa[o + 1], z = pa[o + 2];
      const cx = Math.floor((x - ox) / cell), cy = Math.floor((y - oy) / cell), cz = Math.floor((z - oz) / cell);
      if (cx >= AXIS || cy >= AXIS || cz >= AXIS) return null;
      const c = confidence ? Math.round(Math.min(1, Math.max(0, confidence.getX(v))) * 254) : 0;
      const key = ((c * AXIS + cx) * AXIS + cy) * AXIS + cz;
      let p = keyOf.get(key);
      if (p === undefined) { p = pools++; keyOf.set(key, p); sum.push(0, 0, 0, 0); }
      pool[base + v] = p;
      sum[p * 4] += x; sum[p * 4 + 1] += y; sum[p * 4 + 2] += z; sum[p * 4 + 3] += 1;
    }
  }
  // each pool drawn at its member nearest the centroid
  const rep = new Int32Array(pools).fill(-1);
  const best = new Float64Array(pools).fill(Infinity);
  for (let k = 0; k < geos.length; k++) {
    const position = geos[k].getAttribute('position'), pa = position.array, stride = position.itemSize;
    const base = segments[k].offset;
    for (let v = 0; v < position.count; v++) {
      const p = pool[base + v], w = sum[p * 4 + 3], o = v * stride;
      const dx = pa[o] - sum[p * 4] / w, dy = pa[o + 1] - sum[p * 4 + 1] / w, dz = pa[o + 2] - sum[p * 4 + 2] / w;
      const d = dx * dx + dy * dy + dz * dz;
      if (d < best[p]) { best[p] = d; rep[p] = base + v; }
    }
  }
  const kept = [];
  const seen = new Set();
  for (let k = 0; k < geos.length; k++) {
    const ix = geos[k].getIndex().array, base = segments[k].offset;
    for (let t = 0; t < ix.length; t += 3) {
      const a = pool[base + ix[t]], b = pool[base + ix[t + 1]], c = pool[base + ix[t + 2]];
      if (a === b || b === c || a === c) continue;
      let r0 = a, r1 = b, r2 = c;
      if (b < a && b < c) { r0 = b; r1 = c; r2 = a; } else if (c < a && c < b) { r0 = c; r1 = a; r2 = b; }
      const key = (r0 * pools + r1) * pools + r2;
      if (key > Number.MAX_SAFE_INTEGER) return null;
      if (seen.has(key)) continue;
      seen.add(key);
      kept.push(rep[a], rep[b], rep[c]);
    }
  }
  const twinTriangles = kept.length / 3;
  if (twinTriangles > triangles * keepRatio || triangles - twinTriangles < minSaved) return null;
  const twin = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(geos[0].attributes)) {
    twin.setAttribute(name, new THREE.BufferAttribute(new attr.array.constructor(0), attr.itemSize, attr.normalized));
  }
  twin.setIndex(new THREE.BufferAttribute(n <= 65535 ? Uint16Array.from(kept) : Uint32Array.from(kept), 1));
  twin.userData = { ...geos[0].userData, groupTwin: true };
  return { geo: twin, segments, triangles, twinTriangles, reach: CENTROID_REACH * cell };
}

/**
 * T-3249: point a group twin's index at its pieces' vertices. It was added to `batch` as
 * `twinGeometryId` with no vertices, so BatchedMesh wrote each value offset by the twin's
 * own empty range (in a 16-bit index, modulo 2^16); each is moved into the range of the
 * piece its segment names. Nothing in this renderer compacts a laid batch (`optimize`),
 * which would move those ranges under it.
 */
export function rebaseGroupTwin(batch, twinGeometryId, pieceGeometryIds, segments) {
  const info = batch._geometryInfo?.[twinGeometryId];
  const index = batch.geometry.getIndex();
  if (!info || !index || info.reservedVertexCount !== 0 || pieceGeometryIds.length !== segments.length) {
    throw new Error('texel shadow twin: no batch range to rebase');
  }
  const starts = pieceGeometryIds.map((id) => batch._geometryInfo[id].vertexStart);
  const a = index.array, wrap = a instanceof Uint16Array ? 65536 : 0;
  for (let i = info.indexStart, end = info.indexStart + info.indexCount; i < end; i++) {
    let g = a[i] - info.vertexStart;
    if (g < 0) g += wrap;
    let lo = 0, hi = segments.length - 1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (segments[mid].offset <= g) lo = mid; else hi = mid - 1; }
    a[i] = starts[lo] + g - segments[lo].offset;
  }
  index.needsUpdate = true;
  index.addUpdateRange(info.indexStart, info.reservedIndexCount);
  info.boundingBox = null;
}

/** The farthest a twin's shadow edge can sit from the piece's, in metres. */
export function twinReachM(cellM = CELL_M) {
  return CENTROID_REACH * cellM;
}

const _sphere = new THREE.Sphere();
const _m = new THREE.Matrix4();
const _size = new THREE.Vector2();
const _end = new THREE.Vector3();

/**
 * Hide each piece of `pairs` whose twin's error cannot exceed MAX_PIXELS anywhere its
 * shadow can land, and show its twin; returns the swapped pairs, for `restore`.
 */
function swapFar(batch, renderer, camera, sun, pairs, swapped, maxPixels) {
  renderer.getDrawingBufferSize(_size);
  const pixels = _size.y * camera.projectionMatrix.elements[5] / 2;
  const view = camera.matrixWorldInverse;
  const v = view.elements;
  // view depth of a world point is -(row 2 of the view matrix) . point
  const depth = (p) => -(v[2] * p.x + v[6] * p.y + v[10] * p.z + v[14]);
  for (const p of pairs) {
    if (!batch.getVisibleAt(p.piece)) continue;
    batch.getMatrixAt(p.piece, _m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(p.piece), _sphere)
      .applyMatrix4(_m).applyMatrix4(batch.matrixWorld);
    const r = _sphere.radius;
    _end.copy(_sphere.center).addScaledVector(sun, -(2 * r + FLOOR_BELOW_M) / sun.y);
    // depth is linear along the sweep, so the capsule's nearest point is at one end
    const nearest = Math.min(depth(_sphere.center), depth(_end)) - r;
    if (!(nearest > 0)) continue;
    // `reachM` is in metres: the cell was cut as CELL_M over the placement's own scale
    if (p.reachM * pixels / (sun.y * nearest) > maxPixels) continue;
    // follow the piece if anything moved it since load
    batch.getMatrixAt(p.twin, _mTwin);
    if (!_mTwin.equals(_m)) batch.setMatrixAt(p.twin, _m);
    batch.setVisibleAt(p.piece, false);
    batch.setVisibleAt(p.twin, true);
    swapped.push(p);
  }
  return swapped;
}
const _mTwin = new THREE.Matrix4();

function restore(batch, swapped) {
  for (const p of swapped) {
    batch.setVisibleAt(p.twin, false);
    batch.setVisibleAt(p.piece, true);
  }
}

/**
 * T-3249: swap in each group twin whose reach is inside one texel of the map, where every
 * piece of its group is shown; returns the swapped groups, for `restoreGroups`.
 */
const _frustum = new THREE.Frustum();
const _box = new THREE.Frustum();
const _vp = new THREE.Matrix4();
const _s = new THREE.Sphere();

/** Each piece's bounding sphere in the world, and the group's, cut once: a structure stays put. */
function spheresOf(batch, g) {
  const n = g.pieces.length;
  const at = new Float32Array(n * 4);
  const box = new THREE.Box3(), part = new THREE.Box3();
  for (let k = 0; k < n; k++) {
    const i = g.pieces[k];
    batch.getMatrixAt(i, _m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(i), _s).applyMatrix4(_m).applyMatrix4(batch.matrixWorld);
    at[k * 4] = _s.center.x; at[k * 4 + 1] = _s.center.y; at[k * 4 + 2] = _s.center.z; at[k * 4 + 3] = _s.radius;
    box.union(_s.getBoundingBox(part));
  }
  batch.getMatrixAt(g.pieces[0], _m);
  return { at, whole: box.getBoundingSphere(new THREE.Sphere()), matrix: _m.clone() };
}

/**
 * Whether a sphere's shadow can reach the view, and how: 0 not at all, 1 in part, 2 wholly
 * inside every plane. shadow-casters.js's own test — the sphere swept down the sun to
 * FLOOR_BELOW_M under it, against each plane of the view frustum — so the pieces it leaves
 * out of the pass are not counted as a cost.
 */
function reach(x, y, z, r, sun) {
  const k = (2 * r + FLOOR_BELOW_M) / sun.y;
  const ex = x - sun.x * k, ey = y - sun.y * k, ez = z - sun.z * k;
  let inside = 2;
  for (const p of _frustum.planes) {
    const a = p.normal.x * x + p.normal.y * y + p.normal.z * z + p.constant;
    const b = p.normal.x * ex + p.normal.y * ey + p.normal.z * ez + p.constant;
    if (a < -r && b < -r) return 0;
    if (a < r || b < r) inside = 1;
  }
  return inside;
}

function swapGroups(batch, groups, texelM, swapped, camera, shadowCamera, sun) {
  _frustum.setFromProjectionMatrix(_vp.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse),
    camera.coordinateSystem, camera.reversedDepth);
  _box.setFromProjectionMatrix(_vp.multiplyMatrices(shadowCamera.projectionMatrix, shadowCamera.matrixWorldInverse),
    shadowCamera.coordinateSystem, shadowCamera.reversedDepth);
  // Three's own instance table when it has one, as confidence.js's leaveOut writes it:
  // this flips thousands of flags a shadow pass in 1904, and the public setVisibleAt
  // validates its id on every call. The same write: the flag, and `_visibilityChanged`
  // so the draw list is rebuilt.
  const info = Array.isArray(batch._instanceInfo) ? batch._instanceInfo : null;
  const shown = info ? (i) => info[i]?.active !== false && info[i]?.visible === true : (i) => batch.getVisibleAt(i);
  const show = info ? (i, v) => { info[i].visible = v; } : (i, v) => batch.setVisibleAt(i, v);
  for (const g of groups) {
    if (g.reachM > texelM) continue;
    if (!g.spheres) g.spheres = spheresOf(batch, g);
    else {
      batch.getMatrixAt(g.pieces[0], _m);
      if (!_m.equals(g.spheres.matrix)) g.spheres = spheresOf(batch, g);
    }
    const { at, whole } = g.spheres;
    // a group no part of whose shadow can reach the view, or outside the sun's box, is
    // left to the per-piece path: it casts nothing there either
    if (!_box.intersectsSphere(whole)) continue;
    const all = reach(whole.center.x, whole.center.y, whole.center.z, whole.radius, sun);
    if (all === 0) continue;
    let every = true;
    for (const p of g.pieces) if (!shown(p)) { every = false; break; }
    if (!every) continue;
    // A twin pays only where it draws fewer triangles than its pieces would: those whose
    // shadow can reach the view and that stand in the sun's box, each at the count of its
    // far twin where it has one (the fewest the per-piece path could draw it with, so the
    // test leans toward leaving a group whole).
    let cost = 0;
    if (all === 2 && _box.containsPoint(whole.center) && boxHolds(whole)) cost = g.allTriangles;
    else {
      for (let k = 0; k < g.pieces.length && cost <= g.twinTriangles; k++) {
        const x = at[k * 4], y = at[k * 4 + 1], z = at[k * 4 + 2], r = at[k * 4 + 3];
        if (!reach(x, y, z, r, sun)) continue;
        _s.center.set(x, y, z); _s.radius = r;
        if (_box.intersectsSphere(_s)) cost += g.pieceTriangles[k];
      }
    }
    if (cost <= g.twinTriangles) continue;
    batch.getMatrixAt(g.pieces[0], _m);
    batch.getMatrixAt(g.twin, _mTwin);
    if (!_mTwin.equals(_m)) batch.setMatrixAt(g.twin, _m);
    for (const p of g.pieces) show(p, false);
    show(g.twin, true);
    swapped.push(g);
  }
  if (info && swapped.length) batch._visibilityChanged = true;
  return swapped;
}

/** Whether a sphere lies wholly inside the sun's box. */
function boxHolds(sphere) {
  for (const p of _box.planes) if (p.distanceToPoint(sphere.center) < sphere.radius) return false;
  return true;
}

function restoreGroups(batch, swapped) {
  const info = Array.isArray(batch._instanceInfo) ? batch._instanceInfo : null;
  for (const g of swapped) {
    if (info) {
      info[g.twin].visible = false;
      for (const p of g.pieces) info[p].visible = true;
    } else {
      batch.setVisibleAt(g.twin, false);
      for (const p of g.pieces) batch.setVisibleAt(p, true);
    }
  }
  if (info && swapped.length) batch._visibilityChanged = true;
}

/**
 * Wrap one batch's shadow preparation. `pairs` is filled as instances are added:
 * `{ piece, twin, reachM, saved }`, instance ids in this batch. Install AFTER
 * far-roof-relief.js (so a relief piece swapped here is never also crest-swapped:
 * that hook passes over a hidden piece) and BEFORE batch-frustum-box.js's narrow
 * phase, which only trusts the hook it wrapped.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, sun:()=>THREE.Vector3|null, pairs:Array, maxPixels?:number, swapped?:number, saved?:number}} state
 *   `maxPixels` (default MAX_PIXELS) is the screen bound, for a harness that measures it.
 *   `groups` (T-3249) are `{ pieces, pieceTriangles, twin, twinTriangles, reachM, saved }`
 *   texel twins (`pieceTriangles[k]`: the fewest piece k can cast with) and `texelM` the
 *   sun map's texel in metres (0 or absent = off): a group whose twin moves an edge no
 *   more than that is swapped wherever it stands.
 */
export function drawFarShadowAsTwins(batch, state) {
  const prepareShadow = batch.onBeforeShadow;
  const swapped = [];
  const swappedGroups = [];
  const groups = state.groups ?? [];
  batch.onBeforeShadow = function (renderer, object, camera, shadowCamera, geometry, depthMaterial, group) {
    const sun = state.on && camera && (state.pairs.length || groups.length) ? state.sun() : null;
    if (!sun || !(sun.y >= LOW_SUN)) {
      state.swapped = 0; state.saved = 0; state.groupsSwapped = 0;
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    }
    const t0 = performance.now();
    // T-3249: the groups first, so a piece their twins stand in for is passed over below
    const texelM = state.texelM ?? 0;
    if (texelM > 0 && groups.length && shadowCamera) swapGroups(this, groups, texelM, swappedGroups, camera, shadowCamera, sun);
    swapFar(this, renderer, camera, sun, state.pairs, swapped, state.maxPixels ?? MAX_PIXELS);
    state.swapMs = performance.now() - t0;
    try {
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    } finally {
      state.swapped = swapped.length + swappedGroups.length;
      state.groupsSwapped = swappedGroups.length;
      let saved = 0;
      for (const p of swapped) saved += p.saved;
      for (const g of swappedGroups) saved += g.saved;
      state.saved = saved;
      restore(this, swapped);
      restoreGroups(this, swappedGroups);
      swapped.length = 0;
      swappedGroups.length = 0;
    }
  };
}
