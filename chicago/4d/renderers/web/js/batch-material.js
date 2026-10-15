// T-2227: inspection batches may share immutable texture Sources, but only
// when the full sampler/material state and registered shader closures agree.
// Unknown hooks and mutable/custom texture types remain isolated.
import * as THREE from 'three';

const identities = new WeakMap();
let nextIdentity = 1;
function identity(value) {
  if (!identities.has(value)) identities.set(value, nextIdentity++);
  return identities.get(value);
}
function valueKey(value, seen = new Set()) {
  if (value === null) return ['null'];
  const type = typeof value;
  if (type === 'number') return ['number', Number.isFinite(value) ? value : String(value)];
  if (type !== 'object' && type !== 'function') return [type, String(value)];
  if (type === 'function' || seen.has(value)) return ['identity', identity(value)];
  if (value.isTexture) return textureState(value, seen);
  if (value.isColor) return ['Color', value.r, value.g, value.b];
  if (value.isVector2 || value.isVector3 || value.isVector4 || value.isEuler
      || value.isQuaternion || value.isMatrix3 || value.isMatrix4) {
    return [value.constructor.name, value.toArray().map(v => valueKey(v))];
  }
  if (value.isPlane) return ['Plane', valueKey(value.normal), valueKey(value.constant)];
  if (ArrayBuffer.isView(value)) return [value.constructor.name, ...Array.from(value, v => valueKey(v))];
  if (Array.isArray(value)) {
    seen.add(value);
    const result = ['array', value.map(v => valueKey(v, seen))];
    seen.delete(value); return result;
  }
  if (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null) {
    seen.add(value);
    const result = ['object', Object.keys(value).sort().map(k => [k, valueKey(value[k], seen)])];
    seen.delete(value); return result;
  }
  return ['identity', identity(value)];
}
function textureState(texture, seen = new Set()) {
  // Render targets, videos and manually animated sources are not immutable
  // decoded images. Unknown subclasses also retain their texture identity.
  if (texture.constructor !== THREE.Texture || texture.isRenderTargetTexture
      || texture.onUpdate || texture.renderTarget) return ['texture', identity(texture)];
  // WebGLTextures adds a disposal listener on first upload. That lifetime
  // bookkeeping must not change the key after a Full/Light round trip.
  const omit = new Set(['uuid', 'name', 'source', 'version', 'matrix', '_listeners']);
  const matrix = texture.matrixAutoUpdate
    ? new THREE.Matrix3().setUvTransform(texture.offset.x, texture.offset.y,
      texture.repeat.x, texture.repeat.y, texture.rotation, texture.center.x, texture.center.y)
    : texture.matrix;
  seen.add(texture);
  const result = ['texture-state', identity(texture.source), valueKey(matrix),
    Object.keys(texture).filter(k => !omit.has(k)).sort().map(k => [k, valueKey(texture[k], seen)])];
  seen.delete(texture); return result;
}
export function textureKey(texture) { return JSON.stringify(textureState(texture)); }

const patchRegistry = new WeakMap();
const base = THREE.Material.prototype;
const hooks = m => [m.onBeforeCompile, m.onBeforeRender, m.customProgramCacheKey];
export function captureHooks(material) {
  const current = hooks(material), known = patchRegistry.get(material);
  if (known && current.every((fn, i) => fn === known.functions[i])) return known.key;
  if (current.every((fn, i) => fn === hooks(base)[i])) return ['three-default'];
  // Even the same function object may read per-material state from a WeakMap.
  return ['opaque-hooks', identity(material)];
}
export function registerPatch(material, prior, tag, capturedValues) {
  const key = [prior, tag, valueKey(capturedValues)];
  patchRegistry.set(material, { key, functions: hooks(material) });
}
export function materialKey(material) {
  if (material.constructor !== THREE.MeshStandardMaterial && material.constructor !== THREE.MeshPhysicalMaterial) {
    return JSON.stringify(['material', identity(material)]);
  }
  // These values are moved into vertex attributes or overwritten for every
  // batch by buildings.js. Everything else remains part of equivalence.
  const omit = new Set(['uuid', 'name', 'version', 'color', 'vertexColors', '_listeners',
    'onBeforeCompile', 'onBeforeRender', 'customProgramCacheKey']);
  if (!material.roughnessMap) omit.add('roughness');
  return JSON.stringify([material.type, captureHooks(material),
    Object.keys(material).filter(k => !omit.has(k)).sort().map(k => [k, valueKey(material[k])])]);
}
