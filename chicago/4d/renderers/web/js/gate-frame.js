/**
 * WHEN THE TOWN UNDER THE MENU NEEDS DRAWING AGAIN (T-2113).
 *
 * The arrival and the welcome are a menu laid over the town, and the walk is
 * held while they are up, so the frame under them is the same picture frame
 * after frame: T-2111 read 3 frames in 23.5 s on the desktop stand-in and 6 in
 * 19.5 s on the phone, every one identical, and on a phone GPU that is every
 * display refresh, each the cost of a whole landing view.
 *
 * So while the gate is up the loop draws only when something it would draw has
 * changed. `frameSignature` folds what a frame is made of into one number: the
 * camera's matrices, the drawing buffer's size, the exposure and the fog, and
 * for every VISIBLE object its id, transform, geometry (draw range, instance
 * count, every buffer's version) and materials (version, opacity, each texture's
 * version, each plain uniform's value). A layer streaming in, a buffer
 * rewritten, a texture landing, a detail or sharpness change, a resize, a
 * uniform written — each moves the number, and the next tick draws.
 *
 * What it does not see is a value written into a shader that no material owns
 * (an `onBeforeCompile` closure), so the caller also marks the gate dirty on
 * every setting a visitor changes, and always draws when a frame is asked for
 * (`step()`, `capture()`). It reads, never writes: no flag on any object.
 */

const f64 = new Float64Array(1);
const u32 = new Uint32Array(f64.buffer);
const PRIME = 0x01000193;

/** FNV-1a over the exact bits of a double: no rounding, so no change too small. */
function mix(h, x) {
  f64[0] = typeof x === 'number' ? x : (x ? 1 : 0);
  h = Math.imul(h ^ u32[0], PRIME);
  return Math.imul(h ^ u32[1], PRIME);
}

const TEXTURE_SLOTS = ['map', 'alphaMap', 'aoMap', 'bumpMap', 'displacementMap',
  'emissiveMap', 'envMap', 'lightMap', 'metalnessMap', 'normalMap', 'roughnessMap',
  'specularMap', 'transmissionMap', 'thicknessMap', 'clearcoatMap', 'sheenColorMap'];

function mixValue(h, v) {
  if (v === null || v === undefined) return mix(h, -1);
  if (typeof v === 'number' || typeof v === 'boolean') return mix(h, v);
  if (v.isTexture) return mix(mix(h, v.id), v.version);
  if (v.isColor) return mix(mix(mix(h, v.r), v.g), v.b);
  if (v.isVector2 || v.isVector3 || v.isVector4 || v.isQuaternion) {
    h = mix(mix(h, v.x), v.y);
    if ('z' in v) h = mix(h, v.z);
    if ('w' in v) h = mix(h, v.w);
    return h;
  }
  if (v.isMatrix3 || v.isMatrix4 || ArrayBuffer.isView(v) || Array.isArray(v)) {
    const a = v.elements ?? v;
    for (let i = 0; i < a.length; i++) h = typeof a[i] === 'object' ? mixValue(h, a[i]) : mix(h, a[i]);
    return h;
  }
  return h;
}

function mixMaterial(h, m, seen) {
  if (!m) return h;
  h = mix(h, m.id);
  if (seen.has(m)) return h;
  seen.add(m);
  h = mix(mix(mix(h, m.version), m.visible), m.opacity);
  for (const slot of TEXTURE_SLOTS) if (m[slot]) h = mixValue(h, m[slot]);
  if (m.color) h = mixValue(h, m.color);
  if (m.emissive) h = mixValue(h, m.emissive);
  if (m.uniforms) for (const key in m.uniforms) h = mixValue(h, m.uniforms[key]?.value);
  return h;
}

function mixGeometry(h, g) {
  if (!g) return h;
  h = mix(mix(mix(h, g.id), g.drawRange.start), g.drawRange.count);
  if (g.index) h = mix(h, g.index.version);
  const attrs = g.attributes;
  for (const key in attrs) {
    const a = attrs[key];
    h = mix(h, a.isInterleavedBufferAttribute ? a.data.version : a.version);
  }
  return h;
}

/**
 * One number for the frame `renderer.render(scene, camera)` would draw now.
 * Equal numbers mean nothing the renderer reads has moved.
 */
export function frameSignature(renderer, scene, camera, scratch = new Set()) {
  scratch.clear();
  let h = 0x811c9dc5;
  for (const m of [camera.matrixWorld, camera.projectionMatrix]) h = mixValue(h, m);
  // The canvas's own width and height ARE the drawing buffer (size × pixel ratio).
  const canvas = renderer.domElement;
  h = mix(mix(h, canvas?.width ?? 0), canvas?.height ?? 0);
  h = mix(h, renderer.toneMappingExposure);
  h = mix(mix(h, renderer.shadowMap?.enabled), renderer.shadowMap?.type);
  const fog = scene.fog;
  if (fog) h = mix(mix(mix(mixValue(h, fog.color), fog.near ?? 0), fog.far ?? 0), fog.density ?? 0);
  if (scene.background) h = mixValue(h, scene.background);
  scene.traverseVisible((o) => {
    h = mix(h, o.id);
    h = mixValue(mixValue(mixValue(h, o.position), o.quaternion), o.scale);
    if (o.isLight) {
      h = mix(mixValue(mix(h, o.intensity), o.color), o.castShadow);
      return;
    }
    if (o.geometry) h = mixGeometry(h, o.geometry);
    if (o.isInstancedMesh || o.isBatchedMesh) {
      h = mix(h, o.count ?? o.instanceCount ?? 0);
      if (o.instanceMatrix) h = mix(h, o.instanceMatrix.version);
      if (o.instanceColor) h = mix(h, o.instanceColor.version);
    }
    const mat = o.material;
    if (Array.isArray(mat)) for (const m of mat) h = mixMaterial(h, m, scratch);
    else h = mixMaterial(h, mat, scratch);
  });
  return h >>> 0;
}


/**
 * The gate's draw policy. `due()` is asked once per tick while the gate is up;
 * it answers true for the first frame, after `invalidate()`, and whenever the
 * signature moved since the last frame it let through. `reset()` forgets the
 * last frame, so the gate's next opening always draws once.
 */
export function createGateFrame({ renderer, scene, camera }) {
  const scratch = new Set();
  let last = null;
  let dirty = true;
  let held = 0;
  return {
    due() {
      const sig = frameSignature(renderer, scene, camera, scratch);
      if (dirty || sig !== last) { dirty = false; last = sig; return true; }
      held++;
      return false;
    },
    invalidate() { dirty = true; },
    reset() { last = null; dirty = true; },
    /** Ticks the gate has let pass without a draw, for a measurement to read. */
    get held() { return held; },
  };
}
