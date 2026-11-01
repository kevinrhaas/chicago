/**
 * T-3272 — A ROOF PIECE PAST ITS RELIEF'S LAST VISIBLE PIXEL DRAWS ITS CRESTS ONLY.
 *
 * Glessner's tile relief (glessner-roof-filter.js, T-2204) is discarded in the
 * fragment shader wherever one exposed course spans fewer than 6 projected
 * pixels: `coursePixels = course * P / viewDepth`, with P the drawing buffer's
 * height times the projection's y scale over two. Its courses are 0.127 m, so on
 * an 800-pixel desktop every relief fragment is gone past about 14 m of depth —
 * and the triangles were still submitted at any distance. Looking south down the
 * 16th-18th west alley from 1616 Prairie's rear, Glessner stands 240 m away and
 * its three relief pieces drew 275,527 triangles in the colour pass of which not
 * one could leave a fragment (docs/RESEARCH/alley-budget-3272/).
 *
 * THE TEST IS A PROOF, NOT A GUESS, so the image does not change. Each relief
 * piece gets a TWIN: the same vertices and attributes, holding only the triangles
 * with at least one corner whose course is not positive — the crests and beds,
 * which the shader never filters, and every mixed triangle, left to the shader
 * exactly as before. A triangle all three of whose corners carry a positive course
 * interpolates a course no larger than the piece's maximum at every fragment, at
 * a view depth no smaller than the nearest point of the piece's bounding sphere.
 * When that bound gives `maxCourse * P / nearestDepth <= 6` (with a 1% margin for
 * float32 in the shader), every one of those fragments is discarded, so drawing
 * the twin instead of the piece writes the same colour and the same depth to
 * every pixel. Otherwise nothing is swapped.
 *
 * T-3285 — AND THE SUN'S PASS TAKES THE SAME SWAP, on the same test. Its depth
 * material carries no discard, so there the twin is a claim about the shadow
 * map, not a proof: what it leaves out is the tile noses, which stand 6 mm off
 * the bed they lap (glessner-roof-filter.js), against a shadow texel of
 * 2 x 240 / 4096 = 0.117 m and a normal bias of 0.045 m on `full` (world.js).
 * A receiver is pushed 45 mm along its normal before it is compared, so a 6 mm
 * nose cannot shade it; the crests and beds, which ARE the roof's shape and its
 * silhouette against the ground, are all still drawn. The test is taken from
 * the VIEW camera (three hands it to onBeforeShadow), so the sun swaps exactly
 * the pieces the colour pass does: wherever a nose can still reach a pixel, it
 * also still casts. The claim is checked the way the colour pass's was, every
 * pixel of the held frame read back off and on (tools/qa_t3272_far_relief.mjs,
 * docs/RESEARCH/alley-budget-3272/). Looking down the 16th-18th alley from
 * 1616's rear it is 247,165 triangles more, at every stand the colour pass swaps.
 *
 * The twin sits hidden the rest of the time, so picking, the Confidence view and
 * every reader of the batch see the piece exactly as before; the swap is undone
 * the moment the draw list is prepared, the same way shadow-casters.js does it.
 *
 * `?farrelief=0` turns it off in both passes, for the on/off pixel proof, and
 * `buildings.farRelief.sun = false` keeps the sun's pass whole on its own.
 */
import * as THREE from 'three';

/** The shader's lower smoothstep edge: at or below this, coverage is 0 and it discards. */
export const RELIEF_DISCARD_PIXELS = 6;
/** Room for float32 interpolation in the shader against this float64 bound. */
const MARGIN = 0.99;

export function farReliefFromSearch(search) {
  try { return new URLSearchParams(search ?? '').get('farrelief') !== '0'; } catch { return true; }
}

/**
 * The crests-and-beds subset of one relief piece: every triangle with a corner whose
 * course is not positive, in its original order, on just the vertices they use. Null
 * when the piece has no relief-only triangle (nothing to gain) or no relief at all.
 * @param {THREE.BufferGeometry} geo  an indexed piece carrying `_roof_detail`
 */
export function crestTwin(geo) {
  const detail = geo.getAttribute('_roof_detail');
  const index = geo.getIndex();
  if (!detail || !index) return null;
  if (Object.values(geo.attributes).some((a) => a.isInterleavedBufferAttribute)) return null;
  const ix = index.array;
  const keep = [];
  let maxCourse = 0;
  for (let t = 0; t < ix.length; t += 3) {
    const a = detail.getX(ix[t]), b = detail.getX(ix[t + 1]), c = detail.getX(ix[t + 2]);
    if (a > 0 && b > 0 && c > 0) {
      maxCourse = Math.max(maxCourse, a, b, c);
    } else {
      keep.push(t);
    }
  }
  if (keep.length * 3 === ix.length || maxCourse <= 0) return null;
  const remap = new Map();
  const order = [];
  const out = new Uint32Array(keep.length * 3);
  let o = 0;
  for (const t of keep) {
    for (let k = 0; k < 3; k++) {
      const v = ix[t + k];
      let n = remap.get(v);
      if (n === undefined) { n = order.length; remap.set(v, n); order.push(v); }
      out[o++] = n;
    }
  }
  const twin = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(geo.attributes)) {
    const size = attr.itemSize;
    const data = new attr.array.constructor(order.length * size);
    for (let i = 0; i < order.length; i++) {
      for (let k = 0; k < size; k++) data[i * size + k] = attr.array[order[i] * size + k];
    }
    twin.setAttribute(name, new THREE.BufferAttribute(data, size, attr.normalized));
  }
  const fits16 = order.length <= 65535;
  twin.setIndex(new THREE.BufferAttribute(fits16 ? Uint16Array.from(out) : out, 1));
  twin.userData = { ...geo.userData };
  return { geo: twin, maxCourse, reliefTriangles: ix.length / 3 - keep.length };
}

const _sphere = new THREE.Sphere();
const _m = new THREE.Matrix4();
const _size = new THREE.Vector2();
const _colour = new THREE.Color();
const _colourTwin = new THREE.Color();

/**
 * Hide every piece of `pairs` whose relief cannot leave a fragment from `camera` (the
 * view camera, in either pass) and show its twin in its place; returns the pairs it
 * swapped, for `restore`.
 */
function swapFar(batch, renderer, camera, pairs, swapped) {
  renderer.getDrawingBufferSize(_size);
  const pixels = _size.y * camera.projectionMatrix.elements[5] / 2;
  const view = camera.matrixWorldInverse;
  for (const p of pairs) {
    if (!batch.getVisibleAt(p.piece)) continue;
    batch.getMatrixAt(p.piece, _m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(p.piece), _sphere)
      .applyMatrix4(_m).applyMatrix4(batch.matrixWorld);
    // view depth is -z in the camera frame; the nearest a fragment can sit is the sphere's near side
    const nearest = -_sphere.center.applyMatrix4(view).z - _sphere.radius;
    if (!(nearest > 0)) continue;
    if (p.maxCourse * pixels / nearest > RELIEF_DISCARD_PIXELS * MARGIN) continue;
    // the twin wears the piece's paint (weathering repaints the piece only)
    batch.getColorAt(p.piece, _colour);
    if (!batch.getColorAt(p.twin, _colourTwin).equals(_colour)) batch.setColorAt(p.twin, _colour);
    batch.setVisibleAt(p.piece, false);
    batch.setVisibleAt(p.twin, true);
    swapped.push(p);
  }
  return swapped;
}

function restore(batch, swapped) {
  for (const p of swapped) {
    batch.setVisibleAt(p.twin, false);
    batch.setVisibleAt(p.piece, true);
  }
  swapped.length = 0;
}

/**
 * Wrap one batch's draw-list preparation, in the colour pass and the sun's. `pairs` is
 * filled as instances are added: `{ piece, twin, maxCourse }`, instance ids in this batch.
 * Install BEFORE batch-frustum-box.js's narrow phase, which only trusts the hook it
 * wrapped, and AFTER shadow-casters.js, so its cull sees the twin the sun will draw.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, sun?:boolean, pairs:Array, swapped?:number, sunSwapped?:number}} state
 *   `sun` (default on) lets the sun's pass keep the relief whole while the colour pass swaps.
 */
export function drawFarReliefAsCrests(batch, state) {
  const prepare = batch.onBeforeRender;
  const swapped = [];
  batch.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
    // three's shadow pass prepares through here with no scene (BatchedMesh.onBeforeShadow),
    // after the hook below has already swapped what the sun draws.
    if (!state.on || scene === null || !camera || !state.pairs.length) {
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    }
    swapFar(this, renderer, camera, state.pairs, swapped);
    try {
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    } finally {
      state.swapped = swapped.length;
      restore(this, swapped);
    }
  };
  const prepareShadow = batch.onBeforeShadow;
  const sunSwapped = [];
  batch.onBeforeShadow = function (renderer, object, camera, shadowCamera, geometry, depthMaterial, group) {
    if (!state.on || state.sun === false || !camera || !state.pairs.length) {
      state.sunSwapped = 0;
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    }
    swapFar(this, renderer, camera, state.pairs, sunSwapped);
    try {
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    } finally {
      state.sunSwapped = sunSwapped.length;
      restore(this, sunSwapped);
    }
  };
}
