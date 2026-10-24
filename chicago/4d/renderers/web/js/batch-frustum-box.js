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

const DIRECTIONAL_SHADOW_CLASS = new THREE.DirectionalLight().shadow.constructor;
const STOCK_SHADOW = [THREE.ShaderChunk.shadowmap_vertex, THREE.ShaderChunk.shadowmap_pars_fragment];
/** Exact native directional PCF frame only; any unsupported state skips this phase. */
function shadowViewFrame(out, renderer, camera, shadowCamera, descriptor, batch) {
  try {
    const light = descriptor?.light?.(), map = light?.shadow?.map, depth = map?.depthTexture;
    if (descriptor?.fresh?.() !== true || renderer?.constructor !== THREE.WebGLRenderer
        || renderer.shadowMap?.enabled !== true || renderer.shadowMap.autoUpdate !== true
        || renderer.shadowMap.type !== THREE.PCFShadowMap || light?.constructor !== THREE.DirectionalLight
        || light.castShadow !== true || light.shadow?.constructor !== DIRECTIONAL_SHADOW_CLASS
        || light.shadow.autoUpdate !== true || light.shadow.camera !== shadowCamera
        || camera?.constructor !== THREE.PerspectiveCamera || camera.isArrayCamera
        || camera.coordinateSystem !== THREE.WebGLCoordinateSystem || camera.reversedDepth !== false
        || shadowCamera?.constructor !== THREE.OrthographicCamera || shadowCamera.view !== null
        || shadowCamera.zoom !== 1 || shadowCamera.coordinateSystem !== THREE.WebGLCoordinateSystem
        || shadowCamera.reversedDepth !== false || !finiteMatrix(camera.projectionMatrix)
        || !finiteMatrix(camera.matrixWorldInverse) || !affine(shadowCamera.matrixWorld)
        || !finiteMatrix(shadowCamera.matrixWorldInverse) || !batch.matrixWorld.equals(out.identity)
        || map?.samples !== 0 || !depth?.isDepthTexture || depth.type !== THREE.UnsignedIntType
        || depth.format !== THREE.DepthFormat || depth.minFilter !== THREE.LinearFilter
        || depth.magFilter !== THREE.LinearFilter || depth.compareFunction !== THREE.LessEqualCompare
        || depth.wrapS !== THREE.ClampToEdgeWrapping || depth.wrapT !== THREE.ClampToEdgeWrapping
        || STOCK_SHADOW[0] !== THREE.ShaderChunk.shadowmap_vertex
        || STOCK_SHADOW[1] !== THREE.ShaderChunk.shadowmap_pars_fragment) return null;
    const shadow = light.shadow, c = shadowCamera, w = shadow.mapSize.x, h = shadow.mapSize.y;
    const width = c.right - c.left, height = c.top - c.bottom, span = c.far - c.near;
    if (![w,h,width,height,span,c.near,shadow.bias,shadow.normalBias].every(Number.isFinite)
        || !Number.isInteger(w) || w < 1 || w !== h || map.width !== w || map.height !== h
        || depth.image?.width !== w || depth.image?.height !== h
        || width <= 0 || width !== height || span <= 0 || c.near <= 0 || shadow.radius !== 1
        || shadow.getFrameExtents().x !== 1 || shadow.getFrameExtents().y !== 1) return null;
    out.expected.copy(c.matrixWorld).invert();
    if (!out.expected.equals(c.matrixWorldInverse)) return null;
    out.expected.makeOrthographic(c.left,c.right,c.top,c.bottom,c.near,c.far,c.coordinateSystem,false);
    if (!out.expected.equals(c.projectionMatrix)) return null;
    out.clip.multiplyMatrices(c.projectionMatrix,c.matrixWorldInverse);
    out.expected.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1).multiply(out.clip);
    if (!out.expected.equals(shadow.matrix)) return null;
    const e = c.matrixWorld.elements;
    const xx=e[0]*e[0]+e[1]*e[1]+e[2]*e[2], yy=e[4]*e[4]+e[5]*e[5]+e[6]*e[6], zz=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];
    if (Math.max(Math.abs(xx-1),Math.abs(yy-1),Math.abs(zz-1),
        Math.abs(e[0]*e[4]+e[1]*e[5]+e[2]*e[6]),Math.abs(e[0]*e[8]+e[1]*e[9]+e[2]*e[10]),
        Math.abs(e[4]*e[8]+e[5]*e[9]+e[6]*e[10])) > 1e-12) return null;
    out.ray.set(-e[8],-e[9],-e[10]).normalize();
    // Native5-tap unit-radius PCF + linear compare footprint, normal bias,
    // normalized depth bias and a depth/numeric allowance; never reduce this.
    out.margin = 2*Math.SQRT2*(width/w) + Math.abs(shadow.normalBias)
      + Math.abs(shadow.bias)*span + 2**-23*span;
    out.clip.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
    out.frustum.setFromProjectionMatrix(out.clip,camera.coordinateSystem,false);
    if (!Number.isFinite(out.margin) || out.frustum.planes.some(p=>![...p.normal.toArray(),p.constant].every(Number.isFinite))) return null;
    out.camera = shadowCamera; return out;
  } catch { return null; }
}
function shadowCannotReachView(frame, box) {
  for (const {normal:n,constant:d} of frame.frustum.planes) {
    // Strict angular fringe: an uncertain/parallel direction always keeps caster.
    if (n.dot(frame.ray) >= -1e-10) continue;
    const support=d+n.x*(n.x>=0?box.max.x:box.min.x)+n.y*(n.y>=0?box.max.y:box.min.y)+n.z*(n.z>=0?box.max.z:box.min.z);
    if (Number.isFinite(support) && support < -frame.margin*(Math.abs(n.x)+Math.abs(n.y)+Math.abs(n.z))) return true;
  }
  return false;
}

/** No renderer/visibility/geometry mutation: only compact a freshly prepared list. */
export function installFrustumBoxCull(batch, trustedSource, depthMaterial, acceptsSeason, stats = null, shadowDescriptor = null) {
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
  let renderHook = null, shadowHook = null, shadowFrame = null;
  const shadowScratch = { identity: new THREE.Matrix4(), clip: new THREE.Matrix4(), expected: new THREE.Matrix4(),
    frustum: new THREE.Frustum(), ray: new THREE.Vector3(), margin: 0, camera: null };
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
    let rejected = 0, shadowRejected = 0;
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
        else if (shadowFrame?.camera === camera && material === depthMaterial && shadowCannotReachView(shadowFrame, box)) {
          keep[k] = false; rejected++; shadowRejected++;
        }
      } catch { /* Unknown/malformed instances fail open, without hiding them. */ }
    }
    if (!rejected) return 0;
    let m = 0;
    for (let k = 0; k < n; k++) if (keep[k]) {
      starts[m] = starts[k]; counts[m] = counts[k]; indirect[m] = indirect[k]; m++;
    }
    batch._multiDrawCount = m;
    batch._indirectTexture.needsUpdate = true;
    if (stats) {
      stats.boxRejected = (stats.boxRejected ?? 0) + rejected;
      stats.shadowViewRejected = (stats.shadowViewRejected ?? 0) + shadowRejected;
    }
    return rejected;
  }
  const prepare = batch.onBeforeRender;
  batch.onBeforeRender = function(renderer, scene, camera, geometry, material, group) {
    const out = prepare.call(this, renderer, scene, camera, geometry, material, group);
    cullPrepared.call(this, camera, geometry, material);
    return out;
  };
  const prepareShadow = batch.onBeforeShadow;
  batch.onBeforeShadow = function(renderer, object, camera, shadowCamera, geometry, material, group) {
    const previous = shadowFrame;
    shadowFrame = object === batch ? shadowViewFrame(shadowScratch,renderer,camera,shadowCamera,shadowDescriptor,batch) : null;
    try { return prepareShadow.call(this,renderer,object,camera,shadowCamera,geometry,material,group); }
    finally { shadowFrame = previous; }
  };
  cullPrepared.seal = () => { renderHook = batch.onBeforeRender; shadowHook = batch.onBeforeShadow; };
  return cullPrepared;
}
