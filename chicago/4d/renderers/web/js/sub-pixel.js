/**
 * T-3426 — AT `light`, A STRUCTURE PIECE THAT IS SMALLER THAN A PIXEL IS NOT DRAWN.
 *
 * `light` has to stay materially cheaper than `full` at the worst stand
 * (tools/smoke_renderer.mjs: light <= 0.9 x full, in driver draws). At West prairie,
 * looking east across the sward at the whole town, it was not: 4,100 against 4,498 on
 * a 390x780 phone, 4,981 against 5,445 at 1280x800. Charged draw by draw
 * (`tools/measure_stand_budget.mjs --stand prairie_west --attribute`), the structures'
 * colour pass was 2,974 of the phone's 4,100 at BOTH tiers. Every structure piece is
 * its own draw in the batch's multi-draw (batch-coalesce.js joins only pieces of one
 * instance), and from 250-1,000 m most of what the town sends is a moulding, a sash, a
 * chimney pot or a step that lands on one or two pixels. far-colour.js (T-3312) cuts
 * the triangles of a far piece; it cannot cut the draw, because the twin is a draw too.
 *
 * THE TEST IS far-colour.js's, TAKEN TO ITS LIMIT. That module swaps a piece for a
 * coarser copy where no edge moves more than MAX_PIXELS (1) on screen. A piece whose
 * WHOLE bounding sphere, at the sphere's nearest view depth, projects to a radius of
 * at most MAX_RADIUS_PIXELS (1) is one whose every point lies within a pixel of its
 * centre: collapsing it to nothing moves no edge of it further than that. So it is
 * not drawn in the colour pass. Nearer, or bigger, it draws as before.
 *
 * Measured on the published mirror, dev 589fb6c67, at West prairie (driver draws,
 * light; full unchanged):
 *                  off    r <= 0.5 px   r <= 1 px    full    1 px / full
 *   390x780       4,100     3,652        3,149       4,498      0.70
 *   1280x800      4,981     4,942        4,532       5,445      0.83
 * Half a pixel is not enough at 1280x800 (0.908 against the 0.9 bar), and 1 px is
 * the rule the colour twins already keep, so 1 px it is, not a number tuned to pass.
 *
 * WHAT IT COSTS, said plainly: a far speck can drop a pixel it would have tinted,
 * and a row of specks (a far fence of window sashes) can thin by those pixels. It is
 * a level of detail on the floor tier and not a proof, the same standing as the
 * colour twins. Only the colour pass: the sun's pass is never touched (three prepares
 * it through here with no scene; far-shadow.js and shadow-casters.js own it), and
 * picking, the Confidence view and every reader of the batch see the piece, because
 * it is hidden only inside the colour pass's draw-list preparation and put back
 * before the hook returns, the way far-colour.js does it. `full` and `balanced` draw
 * every piece. `?subpixel=0` turns it off, for an on/off comparison.
 */

/** The largest on-screen radius, in pixels, of a piece that is not drawn at `light`. */
export const MAX_RADIUS_PIXELS = 1;

export function subPixelFromSearch(search) {
  try { return new URLSearchParams(search ?? '').get('subpixel') !== '0'; } catch { return true; }
}

/** Every instance's bounding sphere in world space, cached until the batch changes. */
function spheresOf(batch, scratch) {
  const n = batch._instanceInfo.length;
  const version = batch._matricesTexture.version;
  let c = batch.userData.subPixelSpheres;
  if (c && c.n === n && c.version === version && c.world === batch.matrixWorld.elements.join()) return c;
  const centre = new Float64Array(n * 3);
  const radius = new Float64Array(n);
  const { m, sphere } = scratch;
  for (let i = 0; i < n; i += 1) {
    if (!batch._instanceInfo[i].active) { radius[i] = Infinity; continue; }
    batch.getMatrixAt(i, m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(i), sphere)
      .applyMatrix4(m).applyMatrix4(batch.matrixWorld);
    centre[i * 3] = sphere.center.x; centre[i * 3 + 1] = sphere.center.y; centre[i * 3 + 2] = sphere.center.z;
    radius[i] = sphere.radius;
  }
  c = { n, version, world: batch.matrixWorld.elements.join(), centre, radius };
  batch.userData.subPixelSpheres = c;
  return c;
}

/**
 * Wrap one structure batch's colour-pass draw-list preparation. Install AFTER
 * far-colour.js, so this runs first and a piece hidden here is passed over there (its
 * twin stays hidden), and BEFORE batch-frustum-box.js's narrow phase, which trusts
 * only the hook it wrapped.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, maxPixels?:number, skipped?:number}} state
 * @param {{m:THREE.Matrix4, sphere:THREE.Sphere}} scratch
 */
export function skipSubPixelPieces(batch, state, scratch) {
  const prepare = batch.onBeforeRender;
  const hidden = [];
  batch.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
    if (!state.on || scene === null || !camera) {
      if (scene !== null) state.skipped = 0;
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    }
    const { centre, radius, n } = spheresOf(this, scratch);
    // pixels per metre at unit view depth, the same reading far-colour.js takes
    const pixels = renderer.domElement.height * camera.projectionMatrix.elements[5] / 2;
    const limit = state.maxPixels ?? MAX_RADIUS_PIXELS;
    const e = camera.matrixWorldInverse.elements;
    const info = this._instanceInfo;
    for (let i = 0; i < n; i += 1) {
      if (!info[i].active || !info[i].visible) continue;
      const x = centre[i * 3], y = centre[i * 3 + 1], z = centre[i * 3 + 2];
      // view depth is -z in the camera frame; the nearest a fragment can sit is the sphere's near side
      const nearest = -(e[2] * x + e[6] * y + e[10] * z + e[14]) - radius[i];
      if (!(nearest > 0)) continue;
      if (radius[i] * pixels / nearest > limit) continue;
      this.setVisibleAt(i, false);
      hidden.push(i);
    }
    try {
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    } finally {
      state.skipped = hidden.length;
      for (const i of hidden) this.setVisibleAt(i, true);
      hidden.length = 0;
    }
  };
}
