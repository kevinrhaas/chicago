/**
 * upload-release.js — a phone keeps the town on the GPU, not twice.
 *
 * T-2158. Every vertex three.js draws is held twice: once in the page, in the
 * typed array the layer built, and once on the GPU, where `bufferData` copied
 * it. The page copy is only read again by code that re-reads geometry — a
 * pick, the far merge, a layer that rewrites its own colours — and on 1835 it
 * came to about 360 MB of a phone tab that iOS kills at the end of the load.
 *
 * So on a phone, each listed layer lets go of the page copy the moment three
 * has uploaded it (`BufferAttribute.onUpload`, the hook three provides for
 * exactly this). Nothing on screen changes: the GPU buffer is the one that was
 * always drawn. What is kept is what something still reads:
 *
 *  - `position` (and the index) of a layer that answers a tap by raycasting
 *    the chunk's own triangles (and the uv and normal three would interpolate
 *    at the hit are set aside for the raycast — no pick reads them). Today no
 *    layer listed here does: the plank walks, fences and yard goods (T-2572)
 *    and the buildings' batches (T-2573) are picked by a one-pixel id pass on
 *    the GPU instead (gpu-pick.js), so they keep nothing;
 *  - any attribute uploaded as DYNAMIC, because its layer rewrites it (the
 *    frontage's far walk index, the horizon's timber), and the whole geometry
 *    of anything whose position is dynamic;
 *  - every bounding volume, computed before the position can go, so the
 *    frustum never needs it again — for a BatchedMesh that is each of its
 *    geometries' box and sphere too, which three computes lazily off the
 *    positions the first time an instance is culled or sorted, and which are
 *    then kept as float32 figures rather than objects (batch-bounds.js, T-3173);
 *  - a BatchedMesh index's element size, which three reads on every draw that
 *    culls: its array is swapped for an empty one of the same type, not dropped;
 *  - a geometry flagged `userData.rereadBeforeRelease`, which its layer will
 *    rebuild from its own arrays after this upload — the terrain's far base,
 *    which `batchDistantGround()` cuts into pieces once the frontage has
 *    protected it (T-2180). Its replacement is not flagged, so the next pass
 *    lets that one go as usual.
 *
 * The far merge reads chunk arrays to build a cluster; a cluster of released
 * chunks refuses and stays chunked (far-merge.js), which at `light` — the
 * phone's tier — never merges anything anyway.
 *
 * A lost WebGL context would need the page copies to re-upload. iOS drops a
 * context under memory pressure, so if one is lost after anything was let go,
 * the page reloads on restore rather than drawing nothing — once a session, and
 * never in a loop: crash-guard.js owns the context events (T-2547) and reads
 * `uploadReleaseState().attributes` to know whether a reload is needed.
 */

import * as THREE from 'three';
import { isSharedImage, retireSharedImage, sourceTextureSlots } from './shared-images.js';
import { compactBatchBounds } from './batch-bounds.js';

/** Layer → attributes it must keep for a tap. Unlisted layers keep nothing. */
export const RELEASE_KEEP = {
  terrain: [],
  trees: [],
  'street-trees': [],
  'yard-ground': [],
  streets: [],
  // Street-grid CPU ray picks keep positions and indices; other uploaded lanes can go.
  'street-grid': ['position', 'index'],
  // Front yards pick analytically; keep triangles for ordinary raycast compatibility.
  'front-yards': ['position', 'index'],
  // T-2572: picked on the GPU (gpu-pick.js), so their triangles go too.
  frontage: [],
  enclosures: [],
  yard: [],
  // T-2573: picked on the GPU too. The weathering handle rewrites the
  // buildings' INSTANCE colours, which are not vertex attributes (T-2568), and
  // no vertex colour reaches a batch (T-2570), so nothing is kept for it either.
  structures: [],
  // T-2775: the 1904 lakefront railway. Its pick marches the ray to the ground and
  // tests the strips' stations (railway.js), so no triangle is read back.
  railway: [],
  // Context streets have no triangle pick: context.js raycasts only its building meshes.
  'context:streets': [],
  // T-3407: the 1812 officers' garden picks its beds on their planes (gardens.js pickAt) and
  // swaps its plants' levels by geometry id, so no array is read back after upload.
  gardens: [],
  // T-3488: the 1904 back yards pick on their surfaces' planes, their doors' and posts' boxes
  // (back-yards.js pickAt), and swap their crop rows' levels by geometry id: nothing is read back.
  'back-yards': [],
  // T-3510: the 1812 crossing boats answer a tap by raycasting their merged hulls
  // (crossings.js pickAt), so their positions stay; colour, uv, normal and grade go.
  crossings: ['position'],
};

function dropArray() { this.array = null; }
/** A BatchedMesh reads `index.array.BYTES_PER_ELEMENT` to place its multi-draw. */
function emptyArray() { this.array = new this.array.constructor(0); }

/**
 * HARNESS ONLY: `?keep-geometry=1` uploads exactly as a phone does but keeps
 * the page arrays, because the smoke's probes read vertices back to check what
 * was laid. `tools/check_upload_release.mjs` boots without it and holds the
 * release itself to account: the arrays go, and picking and walking still work.
 */
const KEEP_ARRAYS = (() => {
  try { return new URLSearchParams(window.location.search).get('keep-geometry') === '1'; } catch { return false; }
})();

const census = { geometries: 0, attributes: 0, bytes: 0, keptForHarness: KEEP_ARRAYS,
  // T-2548: the buildings' source glTF geometry, and their decoded images.
  sources: 0, sourceBytes: 0, images: 0, imageBytes: 0,
  // T-2828: a GLB KTX2's transcoded levels, let go by texture residency once uploaded.
  compressed: 0, compressedBytes: 0,
  // T-3173: BatchedMesh geometry bounds moved into typed arrays (batch-bounds.js).
  boundsRows: 0, boundsBytes: 0 };

/** T-2828: texture-residency.js let go of one source's transcoded levels (`bytes`). */
export function noteReleasedLevels(bytes) {
  census.compressed += 1;
  census.compressedBytes += bytes;
}

function release(attr, drop = dropArray) {
  if (!attr || !attr.array || attr.userData?.uploadReleased) return;
  if (attr.usage !== THREE.StaticDrawUsage) return;
  if (attr.isInterleavedBufferAttribute || attr.isInstancedBufferAttribute) return;
  attr.userData = attr.userData || {};
  attr.userData.uploadReleased = true;
  // What the GPU holds once the array is gone, at its own layout: a compact
  // attribute (T-2569) is not the float32 the meter would otherwise assume.
  attr.userData.uploadBytes = attr.array.byteLength;
  census.attributes += 1;
  census.bytes += attr.array.byteLength;
  if (!KEEP_ARRAYS) attr.onUpload(drop);
}

/** Railway alone opts in after its last matrix write. Shared near/far users
 * must all have full-capacity bounds before the shared upload array can go. */
function markRailwayStaticMatrices(layer) {
  if (layer.name !== 'railway') return;
  const users = new Map();
  layer.traverse(o => {
    const a = o.instanceMatrix;
    if (!o.isInstancedMesh || !a?.array
      || a.itemSize !== 16 || a.usage !== THREE.StaticDrawUsage
      || !(a.array instanceof Float32Array) || !a.count || a.userData?.uploadReleased) return;
    if (!users.has(a)) users.set(a, []);
    users.get(a).push(o);
  });
  for (const [a, meshes] of users) {
    if (!meshes.every(m => m.userData.railwayStaticMatrix === true)) continue;
    a.userData = a.userData || {};
    a.userData.uploadReleased = true; a.userData.uploadBytes = a.array.byteLength;
    census.attributes += 1; census.bytes += a.array.byteLength;
    if (KEEP_ARRAYS) continue;
    const previousUpload = a.onUploadCallback;
    a.onUpload(function releaseRailwayMatrix() {
      // No future tier/count increase may lazily read a discarded matrix.
      const box = new THREE.Box3(), sphere = new THREE.Sphere();
      for (const mesh of meshes) {
        const count = mesh.count, oldBox = mesh.boundingBox, oldSphere = mesh.boundingSphere;
        if (oldBox) box.union(oldBox);
        if (oldSphere) sphere.union(oldSphere);
        try {
          mesh.count = this.count; mesh.boundingBox = null; mesh.boundingSphere = null;
          mesh.computeBoundingBox(); mesh.computeBoundingSphere();
          box.union(mesh.boundingBox); sphere.union(mesh.boundingSphere);
        } finally { mesh.count = count; mesh.boundingBox = oldBox; mesh.boundingSphere = oldSphere; }
      }
      // Preserve near/far's shared sphere and never shrink any previous bound.
      const sharedSphere = meshes.find(m => m.boundingSphere)?.boundingSphere ?? new THREE.Sphere();
      sharedSphere.copy(sphere);
      for (const mesh of meshes) {
        if (mesh.boundingBox) mesh.boundingBox.copy(box); else mesh.boundingBox = box.clone();
        mesh.boundingSphere = sharedSphere;
      }
      previousUpload.call(this);
      this.array = null;
      this.onUploadCallback = previousUpload;
    });
  }
}

/** A geometry this pass will let go of; the others keep their arrays and are passed over. */
function releasable(o) {
  const geo = o.geometry;
  if (!geo || o.isInstancedMesh || geo.userData.uploadReleased) return false;
  if (geo.userData.rereadBeforeRelease) return false;
  const pos = geo.attributes.position;
  return !!pos && pos.usage === THREE.StaticDrawUsage;
}

/**
 * T-2646: the Confidence view's ghost pass reads which grades a geometry holds off its
 * `_confidence` channel; once the channel's page copy is gone, it reads the range kept here.
 */
function readConfidenceRange(geo, keep) {
  const conf = geo.attributes._confidence;
  if (!conf?.array || conf.itemSize !== 1 || keep.includes('_confidence')) return;
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < conf.count; i += 1) {
    const v = conf.getX(i);
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  if (conf.count && Number.isFinite(lo) && Number.isFinite(hi)) geo.userData.confidenceRange = [lo, hi];
}

function markObject(o, keep) {
  if (!releasable(o)) return;
  const geo = o.geometry;
  geo.userData.uploadReleased = true;
  if (!geo.boundingSphere) geo.computeBoundingSphere();
  if (!geo.boundingBox) geo.computeBoundingBox();
  if (o.isBatchedMesh) batchBounds(o);
  census.geometries += 1;
  if (!geo.userData.confidenceRange) readConfidenceRange(geo, keep);
  for (const [attrName, attr] of Object.entries(geo.attributes)) {
    if (!keep.includes(attrName)) release(attr);
  }
  if (geo.index && !keep.includes('index')) release(geo.index, o.isBatchedMesh ? emptyArray : dropArray);
  if (keep.includes('position')) pickWithoutReleased(o);
}

/** Mark one layer's geometries to let go of their page arrays once uploaded. */
function markLayer(layer, keep) {
  markRailwayStaticMatrices(layer);
  layer.traverse((o) => markObject(o, keep));
}

const _box = new THREE.Box3();
const _sphere = new THREE.Sphere();

/**
 * Every geometry of a batch has its box and sphere cached before its positions
 * can go: three computes them off the positions on first use (a cull, a sort,
 * the sun's cast test), and an instance first shown after the release would
 * otherwise read an array that is not there.
 */
function batchBounds(batch) {
  const n = batch._geometryCount ?? batch._geometryInfo?.length ?? 0;
  for (let id = 0; id < n; id += 1) {
    if (batch._geometryInfo?.[id]?.active === false) continue;
    batch.getBoundingBoxAt(id, _box);
    batch.getBoundingSphereAt(id, _sphere);
  }
  // T-3173: and then kept as figures in two typed arrays rather than a Box3 and a
  // Sphere apiece — about 20 MB of a phone's JS heap on /1904/ (batch-bounds.js).
  const rows = compactBatchBounds(batch);
  if (rows) { census.boundsRows += rows; census.boundsBytes += batch.userData.compactBounds.bytes; }
}

/** What three's raycast interpolates at a hit when the geometry carries it. */
const HIT_ATTRIBUTES = ['uv', 'uv1', 'uv2', 'uv3', 'normal'];

/**
 * A tap raycasts the chunk's own triangles, and three then interpolates the uv
 * and normal at the hit if the geometry carries them — reading arrays a phone
 * has let go of. No `pickAt` reads either (they resolve a hit by face and
 * point), so for the length of the raycast those attributes are set aside,
 * and put back before anything can draw.
 */
function pickWithoutReleased(o) {
  if (o.userData.uploadReleasedPick) return;
  o.userData.uploadReleasedPick = true;
  const raycast = o.raycast;
  o.raycast = function raycastReleased(raycaster, intersects) {
    const attrs = this.geometry?.attributes;
    const aside = [];
    if (attrs) {
      for (const name of HIT_ATTRIBUTES) {
        if (attrs[name] && attrs[name].array === null) { aside.push([name, attrs[name]]); delete attrs[name]; }
      }
    }
    try {
      return raycast.call(this, raycaster, intersects);
    } finally {
      for (const [name, attr] of aside) attrs[name] = attr;
    }
  };
}

/**
 * Mark every listed layer under `scene` to let go of its page arrays once they
 * are uploaded. Idempotent: a layer built later (the trees) is picked up by
 * calling it again, and a geometry already marked is passed over.
 */
export function releaseAfterUpload(scene, keepByLayer = RELEASE_KEEP) {
  for (const [name, keep] of Object.entries(keepByLayer)) {
    const layer = scene.getObjectByName(name);
    if (layer) markLayer(layer, keep);
  }
  return { ...census };
}

const _scissor = new THREE.Vector4();

const DRAWS = ['drawArrays', 'drawElements', 'drawArraysInstanced', 'drawElementsInstanced'];
const MULTI_DRAWS = ['multiDrawArraysWEBGL', 'multiDrawElementsWEBGL',
  'multiDrawArraysInstancedWEBGL', 'multiDrawElementsInstancedWEBGL'];
const noDraw = () => {};

/** Hold the context's draw calls (an own property over each); the returned call lifts them. */
function holdDraws(gl) {
  const held = [];
  const hold = (target, names) => {
    for (const name of names) {
      if (!target || typeof target[name] !== 'function') continue;
      held.push([target, name, Object.prototype.hasOwnProperty.call(target, name), target[name]]);
      target[name] = noDraw;
    }
  };
  hold(gl, DRAWS);
  hold(gl.getExtension('WEBGL_multi_draw'), MULTI_DRAWS);
  return () => {
    for (const [target, name, own, fn] of held.reverse()) {
      if (own) target[name] = fn; else delete target[name];
    }
  };
}

/**
 * HAND A LAYER TO THE GPU AS SOON AS IT IS BUILT, on a phone, so its page
 * arrays go while the next layer is still being laid rather than all at once
 * under the first frame — where every layer's page copy and its GPU copy were
 * alive together, which is the moment iOS killed the tab.
 *
 * The layer is rendered once, alone (siblings hidden, the lights kept, so the
 * programs are the ones the real frame uses), into one scissored pixel of the
 * canvas the loader still covers, with frustum culling off so every chunk that
 * is shown is uploaded, and with the sun's pass held so nothing else is drawn.
 * `hide(o)` keeps back what this tier never shows (the cross-street walks and
 * the woodpiles at `light`), so the GPU is not handed what it will never draw.
 * Everything touched is put back exactly as it was.
 *
 * T-2824. THE PASS UPLOADS AND DOES NOT DRAW. Every upload it exists for — the
 * buffers, the textures, the programs — happens before three's draw call, and the
 * draw itself never ran: with the sun's pass held, no shadow map exists yet, three
 * binds a colour texture to the `sampler2DShadow`, and every draw was refused
 * (GL_INVALID_OPERATION, 267 on a 1904 phone boot). Lending the sun a 1×1
 * comparing map let those draws through, and drawing every chunk unculled cost
 * +67-74 MB in the GPU process (SwiftShader, 1904 phone), still held once the
 * town had settled (docs/measurements/t-2824-boot-upload-pass.json). So the draw
 * calls are held for the length of the pass: the same uploads as before, no errors.
 */
export function uploadLayerNow(renderer, scene, camera, layer, { hide = () => false, only = null, lights = null } = {}) {
  const keep = RELEASE_KEEP[layer?.name];
  if (!keep || !layer.visible) return;
  markLayer(layer, keep);
  const restore = [];
  // T-3728: a piece of the layer only (`uploadLayerSliced`), picked by a layer bit the
  // camera alone tests for this pass; the lights take the bit too, so the programs are
  // still the ones the real frame uses.
  const tagged = [];
  const mask = camera.layers.mask;
  if (only) {
    for (const o of [...only, ...(lights ?? [])]) {
      if (!o.layers.isEnabled(PIECE_LAYER)) { o.layers.enable(PIECE_LAYER); tagged.push(o); }
    }
    camera.layers.set(PIECE_LAYER);
  }
  for (const c of scene.children) {
    if (c !== layer && !c.isLight && c.visible) { restore.push([c, 'visible', true]); c.visible = false; }
  }
  layer.traverse((o) => {
    if (o !== layer && o.visible && hide(o)) { restore.push([o, 'visible', true]); o.visible = false; }
    if (o.frustumCulled) { restore.push([o, 'frustumCulled', true]); o.frustumCulled = false; }
    if (o.isBatchedMesh && o.perObjectFrustumCulled) {
      restore.push([o, 'perObjectFrustumCulled', true]); o.perObjectFrustumCulled = false;
    }
  });
  const shadow = renderer.shadowMap;
  const auto = shadow.autoUpdate;
  const needs = shadow.needsUpdate;
  const scissorTest = renderer.getScissorTest();
  renderer.getScissor(_scissor);
  shadow.autoUpdate = false;
  shadow.needsUpdate = false;
  renderer.setScissorTest(true);
  renderer.setScissor(0, 0, 1, 1);
  const lift = holdDraws(renderer.getContext());
  try {
    renderer.render(scene, camera);
  } finally {
    lift();
    renderer.setScissor(_scissor);
    renderer.setScissorTest(scissorTest);
    shadow.autoUpdate = auto;
    shadow.needsUpdate = needs;
    for (const [o, key, value] of restore) o[key] = value;
    for (const o of tagged) o.layers.disable(PIECE_LAYER);
    camera.layers.mask = mask;
  }
}

/**
 * T-3728 (Bill's PC, 2026-11-23). ONE LAYER'S UPLOAD WAS ONE TASK: 2.55 s on the UHD 630,
 * 1.44 s of it the bounds `markLayer` computes off the positions before they can go, and
 * 0.97 s the pass above handing every buffer and texture to the driver at once. Nothing
 * can paint while either runs, so the boot stood still.
 *
 * So first the bounds, worked out in slices (`pause()` returns a promise when a yield is
 * due): the same box and sphere three would compute, figure for figure — a box is the
 * least and greatest of each axis whatever the order, and the sphere is centred on the box
 * and reaches the farthest vertex, as `computeBoundingSphere` has it (a geometry with
 * morph targets is left to three). A batch's geometries are each three's own, a few at a
 * time. Then the pass above runs once per piece of the layer, a piece being the drawables
 * whose page arrays come to about `pieceBytes`, re-sized so each takes about `pieceMs`,
 * with a yield between pieces. The same objects are uploaded, with the same programs, as
 * in one pass; every piece puts back everything it touched before the yield.
 */
export async function uploadLayerSliced(renderer, scene, camera, layer, {
  hide = () => false, pause = () => null, pieceBytes = 4 << 20, pieceMs = 40,
} = {}) {
  const keep = RELEASE_KEEP[layer?.name];
  if (!keep || !layer.visible) return;
  const wait = async () => { const p = pause(); if (p) await p; };
  const objects = [];
  layer.traverse((o) => { if (releasable(o)) objects.push(o); });
  for (const o of objects) {
    if (!releasable(o)) continue;
    await sliceBounds(o.geometry, wait);
    if (o.isBatchedMesh) await sliceBatchBounds(o, wait);
    if (!o.geometry.userData.confidenceRange) readConfidenceRange(o.geometry, keep);
    await wait();
  }
  if (!layer.visible) return;
  markLayer(layer, keep);
  // What the pass would draw: shown, not held back by `hide`, and a drawable.
  const pieces = [];
  const walk = (o) => {
    if (!o.visible || (o !== layer && hide(o))) return;
    if ((o.isMesh || o.isLine || o.isPoints || o.isSprite) && o.geometry && o.layers.test(camera.layers)) pieces.push(o);
    for (const c of o.children) walk(c);
  };
  walk(layer);
  const lights = [];
  scene.traverse((o) => { if (o.isLight) lights.push(o); });
  let budget = pieceBytes;
  for (let i = 0; i < pieces.length;) {
    const only = [];
    let bytes = 0;
    while (i < pieces.length && (only.length === 0 || bytes < budget)) {
      bytes += pageBytes(pieces[i].geometry);
      only.push(pieces[i]);
      i += 1;
    }
    if (!layer.visible) return;
    const t0 = performance.now();
    uploadLayerNow(renderer, scene, camera, layer, { hide, only, lights });
    const ms = performance.now() - t0;
    if (bytes > 0 && ms > 0) budget = Math.min(64 << 20, Math.max(Math.min(1 << 20, pieceBytes), bytes * pieceMs / ms));
    if (i < pieces.length) await wait();
  }
}

/**
 * T-3728 (Bill's PC, 2026-11-23, second profile): the town's first frame still stood for
 * 1.0 s, handing the textures it was the first to draw to the driver (0.53 s of them) in
 * the frame. This is that frame's upload, made ahead while the loader covers the canvas:
 * one layer of the scene at a time, as the camera stands, culled as the frame culls it —
 * so what goes up is what the first frame would have sent, nothing more — drawn into one
 * held pixel as `uploadLayerNow` draws, with a yield between layers. A layer's programs
 * must be built already (main.js compiles them just before); nothing is let go here that
 * the settle passes did not already mark.
 */
export async function uploadSceneSliced(renderer, scene, camera, { pause = () => null } = {}) {
  const gl = renderer.getContext();
  for (const layer of [...scene.children]) {
    if (layer.isLight || !layer.visible) continue;
    const restore = [];
    for (const c of scene.children) {
      if (c !== layer && !c.isLight && c.visible) { restore.push(c); c.visible = false; }
    }
    const shadow = renderer.shadowMap;
    const auto = shadow.autoUpdate, needs = shadow.needsUpdate, scissorTest = renderer.getScissorTest();
    renderer.getScissor(_scissor);
    shadow.autoUpdate = false; shadow.needsUpdate = false;
    renderer.setScissorTest(true); renderer.setScissor(0, 0, 1, 1);
    const lift = holdDraws(gl);
    try {
      renderer.render(scene, camera);
    } finally {
      lift();
      renderer.setScissor(_scissor); renderer.setScissorTest(scissorTest);
      shadow.autoUpdate = auto; shadow.needsUpdate = needs;
      for (const c of restore) c.visible = true;
    }
    const p = pause(); if (p) await p;
  }
}

/** A layer bit no other pass sets (the Confidence view's ghosts are on 31). */
const PIECE_LAYER = 30;

/** What a drawable still holds in the page, priced for a piece; a small floor for each. */
function pageBytes(geo) {
  let bytes = 4096;
  const seen = new Set();
  for (const attr of [...Object.values(geo.attributes), geo.index]) {
    const array = attr?.isInterleavedBufferAttribute ? attr.data.array : attr?.array;
    if (array && !seen.has(array)) { seen.add(array); bytes += array.byteLength; }
  }
  return bytes;
}

const SLICE_VERTICES = 32768;
const _sv = new THREE.Vector3();

/** `computeBoundingBox` and `computeBoundingSphere`, the same figures, with a yield due now and then. */
async function sliceBounds(geo, wait) {
  if (geo.boundingBox && geo.boundingSphere) return;
  const pos = geo.attributes.position;
  if (!pos || pos.isGLBufferAttribute || geo.morphAttributes?.position || pos.count < SLICE_VERTICES) {
    if (!geo.boundingSphere) geo.computeBoundingSphere();
    if (!geo.boundingBox) geo.computeBoundingBox();
    return;
  }
  const box = new THREE.Box3();
  for (let i = 0, n = pos.count; i < n; i += 1) {
    box.expandByPoint(_sv.fromBufferAttribute(pos, i));
    if (i % SLICE_VERTICES === SLICE_VERTICES - 1) await wait();
  }
  if (!geo.boundingSphere) {
    const center = box.getCenter(new THREE.Vector3());
    let maxRadiusSq = 0;
    for (let i = 0, n = pos.count; i < n; i += 1) {
      maxRadiusSq = Math.max(maxRadiusSq, center.distanceToSquared(_sv.fromBufferAttribute(pos, i)));
      if (i % SLICE_VERTICES === SLICE_VERTICES - 1) await wait();
    }
    // A frame drawn under a yield may have asked three for it meanwhile: the same figures.
    if (!geo.boundingSphere) geo.boundingSphere = new THREE.Sphere(center, Math.sqrt(maxRadiusSq));
  }
  if (!geo.boundingBox) geo.boundingBox = box;
}

/** Each geometry of a batch has three's own box and sphere cached, a few at a time. */
async function sliceBatchBounds(batch, wait) {
  if (batch.userData.compactBounds) return;
  const n = batch._geometryCount ?? batch._geometryInfo?.length ?? 0;
  for (let id = 0; id < n; id += 1) {
    if (batch._geometryInfo?.[id]?.active === false) continue;
    batch.getBoundingBoxAt(id, _box);
    batch.getBoundingSphereAt(id, _sphere);
    if (id % 64 === 63) await wait();
  }
}

/**
 * T-2548. A PHONE LETS GO OF EACH BUILDING'S SOURCE GEOMETRY ONCE ITS BATCH HOLDS
 * A COPY. `createBuildings` normalises every source mesh into a float32 copy in
 * the batch, and the source — the GLB's quantized, interleaved arrays — was then
 * kept in the registry for nothing but a detail rebuild: about 49 MB of the 1904
 * phone's ArrayBuffers, 12.5 MB of it Glessner's. The scene graph, materials and
 * textures stay (the batch draws with those textures, and the card reads the
 * record); the attributes and the index go. A released row is marked
 * `sourceReleased`, and a rebuild re-reads its GLB first (main.js, from the HTTP
 * cache). Idempotent: a row already released is passed over.
 */
export function releaseSources(registry) {
  for (const row of registry.values()) {
    if (!row.gltf || row.sourceReleased) continue;
    const buffers = new Set();
    row.gltf.scene?.traverse((o) => {
      const geo = o.geometry;
      if (!geo) return;
      for (const attr of [...Object.values(geo.attributes), geo.index]) {
        const array = attr?.isInterleavedBufferAttribute ? attr.data.array : attr?.array;
        if (array?.buffer) buffers.add(array.buffer);
      }
      for (const name of Object.keys(geo.attributes)) geo.deleteAttribute(name);
      geo.setIndex(null);
      geo.dispose();
    });
    collapseScene(row);
    row.sourceReleased = true;
    census.sources += 1;
    for (const buffer of buffers) census.sourceBytes += buffer.byteLength;
  }
}

/**
 * T-3173. A RELEASED ROW KEEPS ITS MATERIALS, NOT ITS NODE TREE. With the geometry
 * gone, the GLB's Object3D tree was still held twice per building (`gltf.scene`,
 * `gltf.scenes`, and `record.node` inside them): every node's matrices, children
 * arrays and `extras` userData, about 9 MB of the 1904 phone's JS heap for 411
 * structures. Nothing reads the tree once the batch is built — the card reads the
 * record's sidecar, and a detail rebuild re-reads a released row's GLB first
 * (main.js `rereadReleased`). What a retired gltf still owes is disposal of its
 * materials and the textures they reach (`disposeLoadedAsset`, which walks the
 * scene for them; the batches draw with those same materials). So the scene becomes
 * one plain node carrying the list — not an Object3D apiece, each of which is three
 * matrices and more — with a `traverse` that visits it: the same disposal, none of
 * the tree.
 */
function collapseScene(row) {
  const scene = row.gltf.scene;
  if (!scene || scene.collapsed) return;
  const requiredTextureSlots = [...sourceTextureSlots(scene)];
  const materials = new Set();
  scene.traverse((o) => {
    for (const material of (Array.isArray(o.material) ? o.material : [o.material])) if (material) materials.add(material);
  });
  const carrier = { material: [...materials] };
  const collapsed = { name: scene.name, collapsed: true, requiredTextureSlots, traverse(visit) { visit(carrier); } };
  row.gltf.scene = collapsed;
  if (Array.isArray(row.gltf.scenes)) row.gltf.scenes = [collapsed];
  row.node = null;
}

/**
 * T-2548. A PHONE CLOSES A BUILDING'S DECODED IMAGE ONCE THE GPU HOLDS IT. Three
 * keeps every `texture.image` (an ImageBitmap) after upload, so each picture a
 * house is painted with was held twice, decoded in the page and again on the GPU.
 *
 * Only an image that came out of a GLB through the shared-image cache is closed
 * (shared-images.js), and only when EVERY texture of the structures batch that
 * draws from it has its GPU texture and the source is uploaded — three uploads
 * once per source and sampler setup, and a second sampler on a source would
 * otherwise read a closed bitmap. The image also leaves the cache, so a GLB
 * parsed later (a detail rebuild) decodes its own copy rather than being handed
 * this closed one. Anything not yet uploaded is left open: nothing re-uploads a
 * building texture after the build, and a restored context needs the page back,
 * which crash-guard.js reloads for when the census counts a closed image.
 */
export function closeUploadedImages(group, renderer) {
  const bySource = new Map();
  group.traverse((o) => {
    // A shadow's own depth material can sample the same map with its own sampler.
    for (const material of [].concat(o.material ?? [], o.customDepthMaterial ?? [],
      o.customDistanceMaterial ?? [])) {
      for (const value of Object.values(material)) {
        if (!value?.isTexture || !value.source) continue;
        if (!bySource.has(value.source)) bySource.set(value.source, new Set());
        bySource.get(value.source).add(value);
      }
    }
  });
  const props = renderer.properties;
  for (const [source, textures] of bySource) {
    const image = source.data;
    if (typeof ImageBitmap === 'undefined' || !(image instanceof ImageBitmap)) continue;
    if (!isSharedImage(image)) continue;
    const uploaded = props.get(source).__version === source.version
      && [...textures].every((t) => props.get(t).__webglTexture !== undefined);
    if (!uploaded) continue;
    retireSharedImage(image);
    census.images += 1;
    census.imageBytes += image.width * image.height * 4;
    image.close();
  }
}

/** What has been marked so far — read by the harness, never by the scene. */
export function uploadReleaseState() { return { ...census }; }
