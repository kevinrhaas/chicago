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
 * `RGBA32UI` target, through a camera whose view is offset so that pixel's
 * centre is exactly the tapped ray, with an id material that writes
 *
 *   r  the chunk's slot in the candidate list, 1-based (0 is a miss)
 *   g  `gl_VertexID` of the triangle's provoking vertex (`flat`)
 *   b  the distance from the eye, `floatBitsToUint(length(view position))`
 *
 * and reads that one pixel back. The layers' chunks are NON-INDEXED triangle
 * soups, so the provoking vertex names the face (`floor(vertex / 3)`) and the
 * face spans each layer already keeps resolve it exactly as they resolved the
 * raycast's `faceIndex`. The distance gives back the hit point on the ray.
 *
 * The id material transforms the stored positions and nothing else, which is
 * what the raycast tested: no relief, no discarded plank gap, no wind. It
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
 * `raycastPick` is the old path, kept as the oracle while arrays exist (the
 * desktop, which releases nothing, and the harness's `?keep-geometry=1`):
 * `tools/check_upload_release.mjs` taps a fixed list on the desktop and
 * holds the two to the same answer.
 */

import * as THREE from 'three';

let renderer = null;

/** main.js hands over its renderer once; until then a pick falls back to the raycast. */
export function setPickRenderer(r) { renderer = r ?? null; }

/** The ray budget every layer's pick has always used: as far as you can see from this height. */
export function pickReach(camera) { return Math.max(400, camera.position.y * 4); }

const VERT = /* glsl */`
in vec3 position;
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
flat out highp uint vVertex;
out vec3 vView;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vView = mv.xyz;
  vVertex = uint(gl_VertexID);
  gl_Position = projectionMatrix * mv;
}`;

const FRAG = /* glsl */`
precision highp float;
precision highp int;
uniform highp uint uSlot;
flat in highp uint vVertex;
in vec3 vView;
layout(location = 0) out highp uvec4 pickOut;
void main() {
  pickOut = uvec4(uSlot, vVertex, floatBitsToUint(length(vView)), 1u);
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
layout(location = 0) out highp uvec4 pickOut;
void main() {
  pickOut = uvec4(uSlot, vVertex, floatBitsToUint(length(vView)), 1u);
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
      uniforms: { uSlot: { value: 0 } }, side,
    });
    materials.set(key, m);
  }
  return m;
}

function sideOf(src) {
  return Array.isArray(src.material) ? THREE.DoubleSide : (src.material?.side ?? THREE.FrontSide);
}

/** Each stand-in writes its own slot: set per object, during the one draw. */
function writeSlot(_r, _s, _c, _g, material) {
  material.uniforms.uSlot.value = this.userData.slot;
  material.uniformsNeedUpdate = true;
}

const EMPTY = new THREE.BufferGeometry();
const scene = new THREE.Scene();
scene.matrixWorldAutoUpdate = false;
const pool = [];
let target = null;
const cameras = { perspective: new THREE.PerspectiveCamera(), orthographic: new THREE.OrthographicCamera() };
for (const c of Object.values(cameras)) c.matrixWorldAutoUpdate = false;
const texel = new Uint32Array(4);
const texelFloat = new Float32Array(texel.buffer);
const size = new THREE.Vector2();
const clear = new THREE.Color();
const ray = new THREE.Raycaster();

/**
 * Draw `meshes` into one pixel under `ndc` and read back what is nearest.
 * @returns {{object, batchId, vertex, face, distance, point}|null|undefined}
 *   `batchId` is the instance a batch was hit on (null for a plain chunk).
 *   undefined when there is no renderer to draw with (the caller raycasts).
 */
export function gpuPick(meshes, ndc, camera, far = pickReach(camera)) {
  if (!renderer || !meshes.length) return renderer ? null : undefined;
  if (!target) {
    target = new THREE.WebGLRenderTarget(1, 1, {
      type: THREE.UnsignedIntType, format: THREE.RGBAIntegerFormat, internalFormat: 'RGBA32UI',
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
    if (src.isBatchedMesh) { batches.push(i); continue; }
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
    stand.visible = true;
    stood += 1;
  }
  for (let i = stood; i < pool.length; i += 1) pool[i].visible = false;

  const was = {
    target: renderer.getRenderTarget(), autoClear: renderer.autoClear,
    alpha: renderer.getClearAlpha(), shadow: renderer.shadowMap.autoUpdate,
    infoReset: renderer.info.autoReset,
  };
  renderer.getClearColor(clear);
  texel.fill(0);
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
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA_INTEGER, gl.UNSIGNED_INT, texel);
  } finally {
    renderer.setRenderTarget(was.target);
    renderer.setClearColor(clear, was.alpha);
    renderer.autoClear = was.autoClear;
    renderer.shadowMap.autoUpdate = was.shadow;
    renderer.info.autoReset = was.infoReset;
    cam.clearViewOffset();
    // Hold no layer's geometry past the pick: a rebuilt layer disposes its old chunks.
    for (let i = 0; i < stood; i += 1) pool[i].geometry = EMPTY;
  }

  const slot = texel[0];
  const distance = texelFloat[2];
  if (!slot || slot > meshes.length || !(distance <= far)) return null;
  const object = meshes[slot - 1];
  ray.setFromCamera(ndc, camera);
  const point = ray.ray.at(distance, new THREE.Vector3());
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

/** The raycast the layers used before: the oracle while the page arrays exist. */
export function raycastPick(meshes, ndc, camera, far = pickReach(camera)) {
  ray.setFromCamera(ndc, camera);
  ray.near = 0;
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
 * A layer's pair of picks over one resolver: `pickAt` on the GPU (the raycast
 * only where there is no renderer), and `pickAtRaycast`, the oracle.
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
    pickAt: (ndc, camera) => {
      if (!camera) return null;
      if (!renderer) return cast(ndc, camera);
      return gpu(ndc, camera);
    },
    pickAtRaycast: cast,
  };
}
