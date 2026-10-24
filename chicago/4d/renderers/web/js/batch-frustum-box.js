// Full rigid structures only: a conservative narrow phase after native spheres.
import * as THREE from 'three';
const TAGS = new Set(['metric-wall-uv-v2', 'metric-roof-uv-v2', 'pane-v1', 'glessner-roof-course-pixels-v1']);
export function rigidHookChain(key, depth = 0) {
  return depth < 16 && Array.isArray(key) && (key.length === 1 && key[0] === 'three-default'
    || key.length === 3 && TAGS.has(key[1]) && rigidHookChain(key[0], depth + 1));
}
const hooks = m => [m.onBeforeCompile, m.onBeforeRender, m.customProgramCacheKey];
const sameHooks = (m, captured) => hooks(m).every((fn, i) => fn === captured[i]);
const plain = m => m && Object.entries(m.defines ?? {}).every(([k,v]) => ['STANDARD','PHYSICAL'].includes(k) && v === '')
  && !m.transparent && m.opacity === 1 && !m.transmission
  && !m.displacementMap && !m.wireframe && !m.alphaTest && !m.alphaHash && !m.alphaMap
  && !m.polygonOffset && !m.stencilWrite && !m.clippingPlanes?.length;
export function rigidBoundsMaterial(m, captured) {
  return (m?.constructor === THREE.MeshStandardMaterial && m.type === 'MeshStandardMaterial'
    || m?.constructor === THREE.MeshPhysicalMaterial && m.type === 'MeshPhysicalMaterial')
    && plain(m) && rigidHookChain(captured);
}
const finiteMatrix = m => m?.isMatrix4 && m.elements.every(Number.isFinite);
const affine = m => finiteMatrix(m) && m.elements[3] === 0 && m.elements[7] === 0
  && m.elements[11] === 0 && m.elements[15] === 1 && m.determinant() !== 0;
const finiteBox = b => b && !b.isEmpty() && [b.min.x,b.min.y,b.min.z,b.max.x,b.max.y,b.max.z].every(Number.isFinite);

/** No renderer/visibility/geometry mutation: only compact a freshly prepared list. */
export function installFrustumBoxCull(batch, trustedSource, depthMaterial, acceptsSeason, stats = null) {
  if (trustedSource !== true || batch.constructor !== THREE.BatchedMesh
      || depthMaterial?.constructor !== THREE.MeshDepthMaterial || depthMaterial.type !== 'MeshDepthMaterial') return null;
  const source = batch.material, sourceHooks = hooks(source), depthHooks = hooks(depthMaterial);
  const sourceType = source.type, depthType = depthMaterial.type, sourceClass = source.constructor, depthClass = depthMaterial.constructor;
  const geometry = batch.geometry, position = geometry.getAttribute('position'), index = geometry.getIndex();
  const positionVersion = position?.version, indexVersion = index?.version;
  const positionArray = position?.array, indexArray = index?.array;
  const positionArrayType = positionArray?.constructor, indexArrayType = indexArray?.constructor;
  const format = a => a ? [a.itemSize, a.normalized, a.gpuType, a.count].join(':') : null;
  const positionFormat = format(position), indexFormat = format(index);
  const frustum = new THREE.Frustum(), clip = new THREE.Matrix4(), instance = new THREE.Matrix4();
  const box = new THREE.Box3(), keep = [], range = {};
  let renderHook = null, shadowHook = null;
  function cullPrepared(camera, drawnGeometry, material) {
    if (this !== batch || !renderHook || batch.onBeforeRender !== renderHook || batch.onBeforeShadow !== shadowHook || batch.material !== source || drawnGeometry !== geometry || batch.geometry !== geometry
        || batch.perObjectFrustumCulled !== true || !plain(source) || source.type !== sourceType || source.constructor !== sourceClass
        || !(sameHooks(source, sourceHooks) || acceptsSeason?.(source, sourceHooks))
        || !(material === source || material === depthMaterial && material.type === depthType && material.constructor === depthClass && sameHooks(material, depthHooks) && plain(material))
        || geometry.getAttribute('position') !== position || position?.version !== positionVersion || position?.array !== positionArray || positionArray?.constructor !== positionArrayType || format(position) !== positionFormat
        || geometry.getIndex() !== index || index?.version !== indexVersion || index?.array !== indexArray || indexArray?.constructor !== indexArrayType || format(index) !== indexFormat
        || Object.values(geometry.morphAttributes ?? {}).some(a => !Array.isArray(a) || a.length)
        || camera?.isArrayCamera || ![THREE.WebGLCoordinateSystem, THREE.WebGPUCoordinateSystem].includes(camera?.coordinateSystem)
        || typeof camera.reversedDepth !== 'boolean' || !finiteMatrix(camera.projectionMatrix) || !finiteMatrix(camera.matrixWorldInverse)
        || !affine(batch.matrixWorld)) return 0;
    const n = batch._multiDrawCount, starts = batch._multiDrawStarts, counts = batch._multiDrawCounts;
    const indirect = batch._indirectTexture?.image?.data, bpe = index ? index.array?.BYTES_PER_ELEMENT : 1;
    if (!Number.isInteger(n) || n < 1 || !bpe || !indirect || n > Math.min(starts.length, counts.length, indirect.length)) return 0;
    clip.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse).multiply(batch.matrixWorld);
    frustum.setFromProjectionMatrix(clip, camera.coordinateSystem, camera.reversedDepth);
    if (frustum.planes.some(p => ![...p.normal.toArray(), p.constant].every(Number.isFinite))) return 0;
    const planeMagnitude = Math.max(1, ...frustum.planes.map(p => Math.abs(p.constant)));
    let rejected = 0;
    for (let k = 0; k < n; k++) {
      keep[k] = true;
      try {
        const id = indirect[k], geometryId = batch.getGeometryIdAt(id);
        const r = batch.getGeometryRangeAt(geometryId, range);
        // A joined/stale/unknown entry is never bounded by its first member alone.
        if (!r || starts[k] !== r.start * bpe || counts[k] !== r.count) continue;
        if (!batch.getBoundingBoxAt(geometryId, box) || !finiteBox(box)) continue;
        batch.getMatrixAt(id, instance);
        if (!affine(instance)) continue;
        box.applyMatrix4(instance);
        if (!finiteBox(box)) continue;
        // Expand a numerical fringe rather than reject grazing stored vertices.
        const magnitude = Math.max(planeMagnitude, Math.abs(box.min.x), Math.abs(box.min.y), Math.abs(box.min.z),
          Math.abs(box.max.x), Math.abs(box.max.y), Math.abs(box.max.z));
        box.expandByScalar(1e-4 + 32 * 2 ** -23 * magnitude);
        if (!frustum.intersectsBox(box)) { keep[k] = false; rejected++; }
      } catch { /* Unknown/malformed instances fail open, without hiding them. */ }
    }
    if (!rejected) return 0;
    let m = 0;
    for (let k = 0; k < n; k++) if (keep[k]) {
      starts[m] = starts[k]; counts[m] = counts[k]; indirect[m] = indirect[k]; m++;
    }
    batch._multiDrawCount = m;
    batch._indirectTexture.needsUpdate = true;
    if (stats) stats.boxRejected = (stats.boxRejected ?? 0) + rejected;
    return rejected;
  }
  const prepare = batch.onBeforeRender;
  batch.onBeforeRender = function(renderer, scene, camera, geometry, material, group) {
    const out = prepare.call(this, renderer, scene, camera, geometry, material, group);
    cullPrepared.call(this, camera, geometry, material);
    return out;
  };
  cullPrepared.seal = () => { renderHook = batch.onBeforeRender; shadowHook = batch.onBeforeShadow; };
  return cullPrepared;
}
