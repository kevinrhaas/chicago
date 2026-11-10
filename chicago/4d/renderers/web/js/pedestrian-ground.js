/** Mask-admitted support from existing Float32 street geometry. No geometry is copied. */
import { createLazyRoadTriangleHeight } from './road-triangle-height.js';

/** A conservative proof of the cut shader's red>0.5 test. Blend edges keep the old floor.
 * Every contributing unsigned-byte red texel must itself exceed0.5; consequently any
 * nonnegative linear filtering of those texels exceeds the shader threshold too. */
export function definitelyCutByRedMask(mask, box, e, n) {
  const image = mask?.image, data = image?.data, w = image?.width, h = image?.height;
  if (!Number.isFinite(e) || !Number.isFinite(n) || !(data instanceof Uint8Array)
    || !Number.isSafeInteger(w) || !Number.isSafeInteger(h) || w < 1 || h < 1 || data.length !== w * h
    || mask.flipY || !box || ![box.x, box.y, box.z, box.w].every(Number.isFinite) || box.z <= 0 || box.w <= 0) return false;
  // These are the uploaded uniform and world-position float lanes. No raster is
  // regenerated, and no geometric polygon is substituted for the actual texture.
  const f = Math.fround;
  const u = f(f(f(e) - f(box.x)) * f(box.z));
  const v = f(f(f(-n) - f(box.y)) * f(box.w));
  if (!(u > 0 && v > 0 && u < 1 && v < 1)) return false;
  const x = u * w - 0.5, y = v * h - 0.5;
  const x0 = Math.floor(x), y0 = Math.floor(y);
  const clampX = a => Math.max(0, Math.min(w - 1, a));
  const clampY = a => Math.max(0, Math.min(h - 1, a));
  const a = clampX(x0), b = clampX(x0 + 1), c = clampY(y0), d = clampY(y0 + 1);
  return data[c * w + a] > 127 && data[c * w + b] > 127 && data[d * w + a] > 127 && data[d * w + b] > 127;
}

export function isPedestrianSurface(mesh) {
  return mesh?.userData?.pedestrianSurface === true
    && ['walk', 'parkway', 'curb', 'alley'].includes(mesh.userData.cls);
}

/** The old field is replaced only after mask admission AND an actual top triangle hit.
 * Uses the already-retained picking position/index arrays; the lazy index owns only
 * typed bucket references and transform snapshots, exactly as the roadway reader does. */
export function createMaskedPedestrianHeight(getMeshes, admits) {
  if (typeof getMeshes !== 'function' || typeof admits !== 'function') throw new Error('Pedestrian support requires surface and mask readers');
  const surface = createLazyRoadTriangleHeight(() => getMeshes().filter(isPedestrianSurface));
  let disposed = false, calls = 0, admitted = 0;
  return {
    heightAt(e, n) {
      if (disposed || !Number.isFinite(e) || !Number.isFinite(n)) return null;
      calls++;
      if (!admits(e, n)) return null;
      admitted++;
      const height = surface.heightAt(e, n);
      return Number.isFinite(height) ? height : null;
    },
    reading() { return { ...surface.reading(), calls, admitted }; },
    dispose() { disposed = true; surface.dispose(); getMeshes = admits = null; },
  };
}
