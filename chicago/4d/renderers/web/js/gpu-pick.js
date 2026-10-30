/**
 * gpu-pick.js — a tap answered by the GPU, so a phone can let go of the
 * triangles it was keeping only to answer one (T-2572, from T-2550).
 *
 * Until this, `frontage`, `enclosures` and `yard` each kept `position` (and
 * the index) in the page after upload (upload-release.js `RELEASE_KEEP`), for
 * one reason: `pickAt` raycast the chunk's own triangles. On the 1835 phone
 * that was about 151 MB of page memory duplicating what the GPU already held
 * (frontage 80, enclosures 41, yard 30 — the reading in T-2546).
 *
 * So a tap draws the candidate chunks once more, into ONE pixel: a 1x1
 * target, through a camera whose view is offset so that pixel's centre is
 * exactly the tapped ray, with an id material that writes three 32-bit words
 *
 *   slot      the chunk's slot in the candidate list, 1-based (0 is a miss)
 *   id        `gl_VertexID` of the triangle's provoking vertex (`flat`)
 *   distance  from the eye, `floatBitsToUint(length(view position))`
 *
 * and reads that one pixel back. Each word goes out as its four bytes into an
 * attachment of its own, three plain RGBA8 attachments, and is put back
 * together here (T-2822). Until then it was one `RGBA32UI` pixel read with
 * `RGBA_INTEGER`, the read WebKit has lost the context on (WebKit bug 245476):
 * on an iPhone, a tap on the Glessner House, or the Navigator opening beside it
 * (Home's probe asks the same pick), reset the display. An RGBA8 read is the one
 * every WebGL implementation must support. The layers' chunks are NON-INDEXED triangle
 * soups, so the provoking vertex names the face (`floor(vertex / 3)`) and the
 * face spans each layer already keeps resolve it exactly as they resolved the
 * raycast's `faceIndex`. The distance gives back the hit point on the ray.
 *
 * The id material transforms the stored positions and nothing else, which is
 * what the raycast tested: no relief, no discarded plank gap, no wind. A boxed
 * mesh's position (T-2700, compact-streams.js) is read whole, as a vec4, and
 * its padding lane's box is applied from the table its material carries, as
 * that material's own vertex stage applies it; a lane naming none (a quantized
 * chunk's 0, a float position's implied 1) leaves the position as stored. It
 * culls the side the chunk's own material culls, as the raycast did. And it
 * draws exactly the list it is handed, hidden or not — `THREE.Raycaster` does
 * not test `visible` either, and each layer already filters what it hands in.
 *
 * A `BatchedMesh` — the buildings, one batch per material — cannot be stood in
 * for by a plain mesh: its instances are placed by a matrix texture and drawn by
 * one multi-draw. So a batch is drawn ITSELF, once per batch, with its material
 * swapped for a batching id material that writes the instance (three's
 * `batchId`, what `BatchedMesh.raycast` reports) in `g` instead of the vertex
 * (T-2573). Each pass draws into the same pixel and the same depth, so the
 * nearest surface across the plain chunks and every batch wins. The batch's own
 * per-instance cull runs against the one-pixel frustum, so a pick draws only the
 * buildings under the finger; a hidden instance is skipped by both engines.
 *
 * Only the batches the ray can meet are drawn (T-2827). Every instance's box is
 * kept in the world, and a batch none of whose shown instances' boxes the ray
 * meets within reach cannot be hit, so it is not drawn; a pick no box answers
 * draws nothing at all. Drawing all 183 batches of 1904 on every look was 183
 * passes, each culling every instance and uploading the batch's indirect
 * texture, twice a second while the HUD's target probe listened, and an iPhone
 * stopped the page in the middle of one (Kevin's black-box records, T-2826).
 * `boxPick` is that box test alone, nearest box wins: what a phone's probe asks
 * (main.js), so looking around a phone draws no pick at all.
 *
 * The gaze target's look (target.js, main.js) does not wait for its answer
 * (T-2723). `readPixels` into page memory waits for the GPU to finish all it was
 * handed before the read, the frame included, so the look was a pipeline flush
 * on the main thread every 500 ms of movement: 63 of 72 s of a profiled walk on
 * the steward runner (T-2721). `gpuPickAsync` draws the same pick in the same
 * frame and reads its pixel into a pixel-pack buffer behind a fence, and the
 * answer is put together a frame or two later, once the fence says the GPU got
 * there; a tap still reads at once, as a tap must (`gpuPick`). Where there is no
 * fence to wait on it is `gpuPick`, and a chunk rebuilt before the answer lands
 * answers nothing rather than a face of geometry that is gone.
 *
 * `raycastPick` is the old path, kept as the oracle while arrays exist (the
 * desktop, which releases nothing, and the harness's `?keep-geometry=1`):
 * `tools/check_upload_release.mjs` taps a fixed list on the desktop and
 * holds the two to the same answer.
 */

import * as THREE from 'three';
import { BOX_TABLE_MAX, POSITION_STEPS } from './compact-streams.js';

let renderer = null;

/** main.js hands over its renderer once; until then a pick falls back to the raycast. */
export function setPickRenderer(r) { renderer = r ?? null; }

let pickLog = null;
/** T-2826: each pick's start and end go to the black box (blackbox.js), so a reset
 *  mid-pick is told from one after it. */
export function setPickLog(fn) { pickLog = typeof fn === 'function' ? fn : null; }

/** The ray budget every layer's pick has always used: as far as you can see from this height. */
export function pickReach(camera) { return Math.max(400, camera.position.y * 4); }

const VERT = /* glsl */`
in vec4 position;
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform vec4 uBoxes[${BOX_TABLE_MAX}];
uniform int uBoxCount;
flat out highp uint vVertex;
out vec3 vView;
void main() {
  vec3 p = position.xyz;
  int box = int(position.w * ${POSITION_STEPS}.0 + 0.5) - 1;
  if (box >= 0 && box < uBoxCount) p = p * uBoxes[box].w + uBoxes[box].xyz;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vView = mv.xyz;
  vVertex = uint(gl_VertexID);
  gl_Position = projectionMatrix * mv;
}`;

/** A word as its four bytes, low first, each exact in an 8-bit unorm channel. */
const BYTES = /* glsl */`
vec4 bytes(highp uint v) {
  return vec4(uvec4(v, v >> 8u, v >> 16u, v >> 24u) & 255u) / 255.0;
}`;

const FRAG = /* glsl */`
precision highp float;
precision highp int;
uniform highp uint uSlot;
flat in highp uint vVertex;
in vec3 vView;
layout(location = 0) out highp vec4 pickSlot;
layout(location = 1) out highp vec4 pickId;
layout(location = 2) out highp vec4 pickDistance;
${BYTES}
void main() {
  pickSlot = bytes(uSlot);
  pickId = bytes(vVertex);
  pickDistance = bytes(floatBitsToUint(length(vView)));
}`;

/**
 * The batch's id material: a (non-raw) ShaderMaterial, so three prepends
 * `USE_BATCHING` and binds the batch's matrix and indirect textures, and the
 * instance a draw belongs to is read the way `<batching_vertex>` reads it.
 */
const VERT_BATCHED = /* glsl */`
#include <batching_pars_vertex>
flat out highp uint vVertex;
out vec3 vView;
void main() {
  #ifdef USE_BATCHING
    float pickBatchId = getIndirectIndex( gl_DrawID );
    vec4 mv = modelViewMatrix * getBatchingMatrix( pickBatchId ) * vec4( position, 1.0 );
    vVertex = uint( pickBatchId );
  #else
    vec4 mv = modelViewMatrix * vec4( position, 1.0 );
    vVertex = uint( gl_VertexID );
  #endif
  vView = mv.xyz;
  gl_Position = projectionMatrix * mv;
}`;

const FRAG_BATCHED = /* glsl */`
uniform highp uint uSlot;
flat in highp uint vVertex;
in vec3 vView;
layout(location = 0) out highp vec4 pickSlot;
layout(location = 1) out highp vec4 pickId;
layout(location = 2) out highp vec4 pickDistance;
${BYTES}
void main() {
  pickSlot = bytes(uSlot);
  pickId = bytes(vVertex);
  pickDistance = bytes(floatBitsToUint(length(vView)));
}`;

const materials = new Map();
function materialFor(side, batched = false) {
  const key = `${batched ? 'b' : 'm'}${side}`;
  let m = materials.get(key);
  if (!m) {
    const Kind = batched ? THREE.ShaderMaterial : THREE.RawShaderMaterial;
    m = new Kind({
      name: batched ? 'gpu-pick-id-batched' : 'gpu-pick-id', glslVersion: THREE.GLSL3,
      vertexShader: batched ? VERT_BATCHED : VERT, fragmentShader: batched ? FRAG_BATCHED : FRAG,
      uniforms: batched ? { uSlot: { value: 0 } } : {
        uSlot: { value: 0 }, uBoxCount: { value: 0 }, uBoxes: { value: new Float32Array(4) },
      }, side,
    });
    materials.set(key, m);
  }
  return m;
}

function sideOf(src) {
  return Array.isArray(src.material) ? THREE.DoubleSide : (src.material?.side ?? THREE.FrontSide);
}

/** Each stand-in writes its own slot and its source's box table, during the one draw. */
function writeSlot(_r, _s, _c, _g, material) {
  material.uniforms.uSlot.value = this.userData.slot;
  const table = this.userData.boxes;
  material.uniforms.uBoxCount.value = table ? table.count : 0;
  if (table) material.uniforms.uBoxes.value = table.uniform.value;
  material.uniformsNeedUpdate = true;
}

const EMPTY = new THREE.BufferGeometry();
const scene = new THREE.Scene();
scene.matrixWorldAutoUpdate = false;
const pool = [];
let target = null;
const cameras = { perspective: new THREE.PerspectiveCamera(), orthographic: new THREE.OrthographicCamera() };
for (const c of Object.values(cameras)) c.matrixWorldAutoUpdate = false;
/** What the pick holds, for the harness (T-2828): one target, its id materials, its stand-ins. */
export function pickResources() {
  return { targets: target ? 1 : 0, materials: materials.size, pool: pool.length };
}
const texel = new Uint32Array(3); // slot, id, distance bits
const texelFloat = new Float32Array(texel.buffer);
const bytes = new Uint8Array(4);
/** A word put back together from its four bytes, low first, at `at`. */
const word = (b, at = 0) => (b[at] | (b[at + 1] << 8) | (b[at + 2] << 16) | (b[at + 3] << 24)) >>> 0;
const size = new THREE.Vector2();
const clear = new THREE.Color();
const ray = new THREE.Raycaster();

const box = new THREE.Box3();
const boxMatrix = new THREE.Matrix4();
const worldBoxes = new WeakMap(); // batch → { version, count, world, boxes }

/**
 * Each instance's box in the world, six floats an instance, kept until the batch
 * moves or its matrices change. upload-release.js caches every geometry's box
 * before a phone lets go of the positions, so this reads no released array.
 */
function boxesOf(batch) {
  const info = batch._instanceInfo;
  const version = batch._matricesTexture?.version ?? 0;
  const kept = worldBoxes.get(batch);
  if (kept && kept.version === version && kept.count === info.length && kept.world.equals(batch.matrixWorld)) {
    return kept.boxes;
  }
  const boxes = new Float32Array(info.length * 6).fill(NaN);
  for (let i = 0; i < info.length; i += 1) {
    if (!info[i].active || !batch.getBoundingBoxAt(info[i].geometryIndex, box)) continue;
    // A centimetre out, so the float32 copy never shaves a triangle on the box's face.
    box.applyMatrix4(batch.getMatrixAt(i, boxMatrix).premultiply(batch.matrixWorld)).expandByScalar(0.01);
    box.min.toArray(boxes, i * 6);
    box.max.toArray(boxes, i * 6 + 3);
  }
  worldBoxes.set(batch, { version, count: info.length, world: batch.matrixWorld.clone(), boxes });
  return boxes;
}

/**
 * The nearest shown instance whose box `worldRay` meets within `far`: `{ batchId, distance }`
 * or null. The slab test is written out over the raw floats: 1904 holds 37k parts.
 */
function nearestBox(batch, worldRay, far) {
  const info = batch._instanceInfo;
  const boxes = boxesOf(batch);
  const { origin: o, direction: d } = worldRay;
  const ix = 1 / d.x, iy = 1 / d.y, iz = 1 / d.z;
  let best = -1, bestT = far;
  for (let i = 0, j = 0; i < info.length; i += 1, j += 6) {
    const x0 = boxes[j];
    if (x0 !== x0 || !info[i].visible || !info[i].active) continue; // NaN: no box
    let t0 = (x0 - o.x) * ix, t1 = (boxes[j + 3] - o.x) * ix;
    let lo = Math.min(t0, t1), hi = Math.max(t0, t1);
    t0 = (boxes[j + 1] - o.y) * iy; t1 = (boxes[j + 4] - o.y) * iy;
    lo = Math.max(lo, Math.min(t0, t1)); hi = Math.min(hi, Math.max(t0, t1));
    t0 = (boxes[j + 2] - o.z) * iz; t1 = (boxes[j + 5] - o.z) * iz;
    lo = Math.max(lo, Math.min(t0, t1)); hi = Math.min(hi, Math.max(t0, t1));
    if (hi < 0 || lo > hi) continue;
    const t = Math.max(lo, 0); // a ray that starts inside meets the box at once
    if (t <= bestT) { bestT = t; best = i; }
  }
  return best < 0 ? null : { batchId: best, distance: bestT };
}

/**
 * Draw `meshes` into one pixel under `ndc` and read back what is nearest.
 * @returns {{object, batchId, vertex, face, distance, point}|null|undefined}
 *   `batchId` is the instance a batch was hit on (null for a plain chunk).
 *   undefined when there is no renderer to draw with (the caller raycasts).
 */
export function gpuPick(meshes, ndc, camera, far = pickReach(camera)) {
  if (!renderer || !meshes.length) return renderer ? null : undefined;
  ray.setFromCamera(ndc, camera);
  texel.fill(0);
  if (!drawPick(meshes, ndc, camera, far, readNow)) return null;
  return answer(meshes, ray.ray, far);
}

/**
 * `gpuPick` without the wait (T-2723): drawn now, in the caller's frame, and
 * answered once the GPU has got to it. Resolves as `gpuPick` returns.
 */
export async function gpuPickAsync(meshes, ndc, camera, far = pickReach(camera)) {
  const gl = renderer?.getContext?.();
  if (!gl || typeof gl.fenceSync !== 'function') return gpuPick(meshes, ndc, camera, far);
  if (!meshes.length) return null;
  ray.setFromCamera(ndc, camera);
  const at = ray.ray.clone();
  const drawn = meshes.map((m) => m.geometry);
  let read = null;
  if (!drawPick(meshes, ndc, camera, far, () => { read = readLater(gl); })) return null;
  const words = await read;
  if (!words || meshes.some((m, i) => m.geometry !== drawn[i])) {
    pickLog?.('picked', { hit: 0, later: true });
    return null;
  }
  texel.set(words);
  return answer(meshes, at, far);
}

/** How often a waiting read asks its fence, and when it gives up on one that never
 *  settles (a lost context answers WAIT_FAILED at once): long, since a software
 *  rasteriser's frame can take seconds and its answer is still good. */
const POLL_MS = 4;
const GIVE_UP_MS = 30000;

/**
 * The pixel's three words into a pixel-pack buffer, and a fence after them. The
 * buffer is unbound before this returns: a `readPixels` into page memory with a
 * pack buffer bound is an error, and a tap may read while this one waits.
 * @returns {Promise<Uint32Array|null>}
 */
function readLater(gl) {
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.PIXEL_PACK_BUFFER, buffer);
  gl.bufferData(gl.PIXEL_PACK_BUFFER, 12, gl.STREAM_READ);
  for (let k = 0; k < 3; k += 1) {
    gl.readBuffer(gl.COLOR_ATTACHMENT0 + k);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, k * 4);
  }
  gl.readBuffer(gl.COLOR_ATTACHMENT0);
  gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
  const fence = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
  gl.flush();
  const since = performance.now();
  return new Promise((resolve) => {
    const done = (words) => {
      gl.deleteSync(fence);
      gl.deleteBuffer(buffer);
      resolve(words);
    };
    const probe = () => {
      const state = gl.clientWaitSync(fence, 0, 0);
      if (state === gl.TIMEOUT_EXPIRED && performance.now() - since < GIVE_UP_MS) {
        setTimeout(probe, POLL_MS);
        return;
      }
      if (state !== gl.ALREADY_SIGNALED && state !== gl.CONDITION_SATISFIED) { done(null); return; }
      const b = new Uint8Array(12);
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, buffer);
      gl.getBufferSubData(gl.PIXEL_PACK_BUFFER, 0, b);
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
      done(Uint32Array.of(word(b), word(b, 4), word(b, 8)));
    };
    setTimeout(probe, POLL_MS);
  });
}

/** The read a tap waits for: a miss reads one attachment; a hit, all three. */
function readNow() {
  for (let k = 0; k < 3; k += 1) {
    renderer.readRenderTargetPixels(target, 0, 0, 1, 1, bytes, undefined, k);
    texel[k] = word(bytes);
    if (!texel[0]) break;
  }
}

/**
 * The pick's draw into its one pixel, and `read` while that pixel is bound.
 * False when no candidate can be met, and then nothing is drawn.
 */
function drawPick(meshes, ndc, camera, far, read) {
  const met = meshes.map((src) => !src.isBatchedMesh || !!nearestBox(src, ray.ray, far));
  if (!met.includes(true)) return false;
  if (!target) {
    target = new THREE.WebGLRenderTarget(1, 1, {
      count: 3, type: THREE.UnsignedByteType, format: THREE.RGBAFormat,
      minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
      generateMipmaps: false, depthBuffer: true,
    });
  }
  const cam = camera.isOrthographicCamera ? cameras.orthographic : cameras.perspective;
  cam.copy(camera, false);
  cam.matrixWorld.copy(camera.matrixWorld);
  cam.matrixWorldInverse.copy(camera.matrixWorldInverse);
  if (cam.isPerspectiveCamera) cam.far = Math.max(camera.far, far);
  renderer.getDrawingBufferSize(size);
  const w = Math.max(1, size.x); const h = Math.max(1, size.y);
  // The 1x1 view's pixel centre is the tapped point itself.
  cam.setViewOffset(w, h, ((ndc.x + 1) / 2) * w - 0.5, ((1 - ndc.y) / 2) * h - 0.5, 1, 1);

  // Plain chunks are stood in for; a batch is drawn itself, in a pass of its own.
  let stood = 0;
  const batches = [];
  for (let i = 0; i < meshes.length; i += 1) {
    const src = meshes[i];
    if (src.isBatchedMesh) {
      if (met[i]) batches.push(i);
      continue;
    }
    let stand = pool[stood];
    if (!stand) {
      stand = new THREE.Mesh(EMPTY, materialFor(THREE.FrontSide));
      stand.matrixAutoUpdate = false;
      stand.frustumCulled = false;
      stand.onBeforeRender = writeSlot;
      pool.push(stand);
      scene.add(stand);
    }
    stand.geometry = src.geometry;
    stand.material = materialFor(sideOf(src));
    stand.matrixWorld.copy(src.matrixWorld);
    stand.userData.slot = i + 1;
    stand.userData.boxes = src.material?.userData?.boxTable ?? null;
    stand.visible = true;
    stood += 1;
  }
  for (let i = stood; i < pool.length; i += 1) pool[i].visible = false;

  const was = {
    target: renderer.getRenderTarget(), autoClear: renderer.autoClear,
    alpha: renderer.getClearAlpha(), shadow: renderer.shadowMap.autoUpdate,
    infoReset: renderer.info.autoReset,
    // The frame's own counts: the pick passes are not the visitor's frame, and a
    // stats() read before the next frame would otherwise report them as drawn.
    render: { ...renderer.info.render },
  };
  renderer.getClearColor(clear);
  pickLog?.('pick', { meshes: stood, batches: batches.length });
  try {
    renderer.autoClear = true;
    renderer.shadowMap.autoUpdate = false;
    renderer.info.autoReset = false;
    renderer.setClearColor(0x000000, 0);
    renderer.setRenderTarget(target);
    renderer.render(scene, cam);
    // Every batch after into the same pixel and depth: the nearest wins.
    renderer.autoClear = false;
    for (const i of batches) drawBatch(meshes[i], i + 1, cam);
    renderer.setRenderTarget(target); // bound again: the read is of this pixel
    read();
  } finally {
    renderer.setRenderTarget(was.target);
    renderer.setClearColor(clear, was.alpha);
    renderer.autoClear = was.autoClear;
    renderer.shadowMap.autoUpdate = was.shadow;
    renderer.info.autoReset = was.infoReset;
    Object.assign(renderer.info.render, was.render);
    cam.clearViewOffset();
    // Hold no layer's geometry past the pick: a rebuilt layer disposes its old chunks.
    for (let i = 0; i < stood; i += 1) { pool[i].geometry = EMPTY; pool[i].userData.boxes = null; }
  }
  return true;
}

/** `texel` as the layer's hit: what slot, which instance or face, how far down `worldRay`. */
function answer(meshes, worldRay, far) {
  const slot = texel[0];
  const distance = texelFloat[2];
  pickLog?.('picked', { hit: slot ? (meshes[slot - 1]?.name || slot) : 0 });
  if (!slot || slot > meshes.length || !(distance <= far)) return null;
  const object = meshes[slot - 1];
  const point = worldRay.at(distance, new THREE.Vector3());
  if (object.isBatchedMesh) return { object, batchId: texel[1], vertex: null, face: null, distance, point };
  const vertex = texel[1];
  return { object, batchId: null, vertex, face: object.geometry.index ? null : Math.floor(vertex / 3),
    distance, point };
}

/**
 * One batch, drawn as itself under its id material. Rendered as its own root, so
 * three neither re-parents it nor reads its siblings; its matrixWorld is the
 * frame's, recomputed from the parent it still has.
 */
function drawBatch(batch, slot, cam) {
  const material = batch.material;
  const pick = materialFor(sideOf(batch), true);
  pick.uniforms.uSlot.value = slot;
  pick.uniformsNeedUpdate = true;
  batch.material = pick;
  try {
    renderer.render(batch, cam);
  } finally {
    batch.material = material;
  }
}

/**
 * The batches' boxes alone, nearest first: no draw, no readback, and no plain
 * chunk (those have no instance boxes). A box is a building part's box, so it is
 * a little generous where the part is not a box, and a ray that starts inside
 * one answers that part at once.
 */
export function boxPick(meshes, ndc, camera, far = pickReach(camera)) {
  ray.setFromCamera(ndc, camera);
  let best = null;
  for (const src of meshes) {
    if (!src.isBatchedMesh) continue;
    const hit = nearestBox(src, ray.ray, far);
    if (hit && (!best || hit.distance < best.distance)) best = { object: src, ...hit };
  }
  if (!best) return null;
  return { object: best.object, batchId: best.batchId, vertex: null, face: null, distance: best.distance,
    point: ray.ray.at(best.distance, new THREE.Vector3()) };
}

const forward = new THREE.Vector3();

/**
 * The raycast the layers used before: the oracle while the page arrays exist.
 * It starts at the camera's near plane, as the GPU pick and the frame do: a
 * surface nearer than that is clipped, so no tap can land on it (T-3248 — an
 * eye stood 9 cm off a tavern's woodpile, and the raycast answered the pile
 * the frame had cut away). The plane is flat, so off the axis a ray reaches it
 * further out; an orthographic ray already starts on it.
 */
export function raycastPick(meshes, ndc, camera, far = pickReach(camera)) {
  ray.setFromCamera(ndc, camera);
  ray.near = camera.isPerspectiveCamera
    ? camera.near / ray.ray.direction.dot(camera.getWorldDirection(forward)) : 0;
  ray.far = far;
  const hits = ray.intersectObjects(meshes, false);
  if (!hits.length) return null;
  const hit = hits[0];
  return { object: hit.object, batchId: hit.batchId ?? null, vertex: null, face: hit.faceIndex ?? null,
    distance: hit.distance, point: hit.point.clone() };
}

/**
 * What a tap may land on is what the frame may draw. A chunk the furniture
 * reach is holding back (`reachCulled`, main.js) is not on screen, and on a
 * phone it has not been uploaded yet: drawing it into the pick would hand the
 * GPU a chunk the walk never asked for. The raycast answered a tap on one,
 * opening the card of something nobody could see; neither engine does now.
 * Hidden far-merge members stay — their cluster draws them, so they are seen.
 */
function drawable(mesh) { return !mesh.userData.reachCulled; }

/**
 * A layer's picks over one resolver: `pickAt` on the GPU (the raycast only
 * where there is no renderer), `pickAtAsync` the same without the wait (the gaze
 * target's, T-2723), `pickAtBox` from the batches' boxes, and `pickAtRaycast`,
 * the oracle.
 *
 * @param {() => THREE.Mesh[]} candidates  what a tap on this layer may hit
 * @param {(hit) => object|null} resolve   `{object, batchId, face, distance, point}` → the layer's answer
 */
export function layerPick(candidates, resolve) {
  const centre = { x: 0, y: 0 };
  const run = (engine) => (ndc, camera) => {
    if (!camera) return null;
    const hit = engine(candidates().filter(drawable), ndc ?? centre, camera, pickReach(camera));
    return hit ? resolve(hit) : null;
  };
  const gpu = run(gpuPick);
  const cast = run(raycastPick);
  return {
    pickAtBox: run(boxPick),
    pickAt: (ndc, camera) => {
      if (!camera) return null;
      if (!renderer) return cast(ndc, camera);
      return gpu(ndc, camera);
    },
    pickAtAsync: async (ndc, camera) => {
      if (!camera) return null;
      if (!renderer) return cast(ndc, camera);
      const hit = await gpuPickAsync(candidates().filter(drawable), ndc ?? centre, camera, pickReach(camera));
      return hit ? resolve(hit) : null;
    },
    pickAtRaycast: cast,
  };
}
