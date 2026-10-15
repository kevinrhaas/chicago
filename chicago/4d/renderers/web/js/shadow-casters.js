/**
 * T-2529 — A STRUCTURE PIECE CASTS ONLY IF ITS SHADOW CAN REACH THE VIEW.
 *
 * three's shadow pass culls each BatchedMesh instance against the SUN's box
 * (±120 m at `light`) and nothing else, so a house beside or behind the visitor
 * draws its whole assembly into the shadow map although the sun throws that
 * shadow away from everything on screen. Measured on the phone at `light`, the
 * stand looking down Prairie's east row from 1613 to 1621 (published dev
 * 4743bcf9e): 1,370,993 triangles against the 1,270,000 ceiling, of which the
 * structures' shadow pass was 567,976 — 1620 Prairie, across the street and
 * behind the camera with the sun in the south-east, cost 68,723 of them and
 * threw no shadow anybody could see.
 *
 * The test is conservative, so the image does not change: a piece's bounding
 * sphere is swept along the sun's direction down to FLOOR_BELOW_M under its
 * base, and the piece is left out of the shadow map only when that whole swept
 * capsule lies outside ONE plane of the view frustum — where no point of its
 * shadow can land on anything the camera sees. Everything else is handed to
 * three's own shadow-camera cull exactly as before. Visibility is restored the
 * moment the shadow draw is prepared, so the colour pass, picking and every
 * other reader see the batch untouched.
 */
import * as THREE from 'three';

/** How far below a piece's own base its shadow is followed (Chicago is flat:
 * the river's banks are the deepest drop in any scene, a few metres). */
export const FLOOR_BELOW_M = 30;
/** Below this sine of the sun's height the sweep grows without bound; cast all. */
const LOW_SUN = 0.05;

const _frustum = new THREE.Frustum();
const _m = new THREE.Matrix4();
const _s = new THREE.Sphere();
const _end = new THREE.Vector3();
const _down = new THREE.Vector3();

/**
 * Wrap one batch's shadow preparation. `state.on` switches it (the detail tier
 * decides); `state.sun` returns the unit vector TOWARD the sun.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, sun:()=>THREE.Vector3, culled?:number}} state
 */
export function castOnlyTowardView(batch, state) {
  const prepare = batch.onBeforeShadow;
  const hidden = [];
  batch.onBeforeShadow = function (renderer, object, camera, shadowCamera, geometry, depthMaterial, group) {
    const sun = state.on && camera ? state.sun() : null;
    if (!sun || sun.y < LOW_SUN) {
      return prepare.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    }
    _down.copy(sun).negate();
    _frustum.setFromProjectionMatrix(
      _m.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse),
      camera.coordinateSystem, camera.reversedDepth);
    const planes = _frustum.planes;
    // buildings.js names every instance it adds here, so a gap is an id never
    // used and is skipped rather than asked about (three throws on those).
    const ids = this.userData.batchIndex ?? [];
    for (let i = 0; i < ids.length; i++) {
      if (ids[i] == null || !this.getVisibleAt(i)) continue;
      this.getMatrixAt(i, _m);
      this.getBoundingSphereAt(this.getGeometryIdAt(i), _s).applyMatrix4(_m);
      const r = _s.radius;
      const reach = (2 * r + FLOOR_BELOW_M) / -_down.y;
      _end.copy(_s.center).addScaledVector(_down, reach);
      for (let k = 0; k < 6; k++) {
        const p = planes[k];
        if (p.distanceToPoint(_s.center) < -r && p.distanceToPoint(_end) < -r) {
          hidden.push(i);
          break;
        }
      }
    }
    for (const i of hidden) this.setVisibleAt(i, false);
    try {
      return prepare.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    } finally {
      state.culled = (state.culled ?? 0) + hidden.length;
      for (const i of hidden) this.setVisibleAt(i, true);
      hidden.length = 0;
    }
  };
}
