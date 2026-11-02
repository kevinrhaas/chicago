/**
 * T-3312 — AT `light`, A FAR STRUCTURE PIECE IS DRAWN FROM A COARSER COPY OF ITSELF.
 *
 * From 60 m over the 18th Street / Prairie-Calumet alley corner, on a 390x780
 * phone at `light`, the 1904 scene drew 1,598,204 triangles against the tier's
 * 1,270,000. Charged draw by draw (tools/qa_t3312_alley_corner.mjs), the structures
 * were 1,316,964 of it and their colour pass 1,078,336; the suspects the ticket
 * named — the 1800 Calumet palm house, the Pullman glasshouse ranges, the parkway
 * trees — were under 100,000 together. What the frame carries is the big Prairie
 * Avenue houses (Ream 1901, Doane 1827, Moulton-Lowden 1912, 1828, Field 1905, Dent
 * 1823 ...) seen whole from the air at 60-150 m, every moulding, sash bar and
 * carved course of them, on a screen where one pixel there is 9-22 cm across.
 *
 * T-3286 already cuts each heavy piece a coarser copy for the sun's pass
 * (far-shadow.js): its vertices pooled in 6 cm cells, each pool one vertex at its
 * centroid, every triangle whose corners do not land in three pools dropped. That
 * twin cannot be drawn in the colour pass, because the colour pass reads the
 * normal and a pool there mixes the faces that meet at a corner: a surviving wall
 * triangle would be lit by its neighbour's normal. So each heavy piece gets a
 * second twin, cut the same way (in 8 cm cells, CELL_M) except that a pool never mixes two normals
 * (`shadowTwin(geo, cell, { byNormal: true })`): every face larger than a cell
 * keeps its own normal, and every face smaller than one — the detail — closes up.
 *
 * THE TEST IS T-3286's, ON THE VIEW. A twin vertex sits at most sqrt(3) x CELL_M
 * (13.9 cm) from every vertex it stands for, so no edge of the twin is further
 * than that from the piece's. The piece is swapped for its twin in the colour pass
 * only where that distance projects to at most MAX_PIXELS at the nearest view depth
 * of the piece's bounding sphere; nearer, it draws whole as before. It is a level
 * of detail and not a proof — an edge may move by up to a pixel, and a detail
 * smaller than a cell is gone — so tools/qa_t3312_alley_corner.mjs reads every
 * pixel of each held frame back off and on, with a positive control, and says how
 * many changed.
 *
 * ONLY AT `light`. `light` is the floor a weak machine boots into and has to stay
 * inside its own ceiling (AGENTS.md § the frame budget); `full` and `balanced` keep
 * every piece exact. The twins are cut only when the batches are built for a tier
 * below `full` (main.js `colourTwins`), so a desktop at `full` carries none of them.
 * Picking, the Confidence view and every reader of the batch see the piece: the
 * twin is hidden except inside the colour pass's draw-list preparation, and the
 * swap is undone before the hook returns, the way far-roof-relief.js does it.
 * `?farcolour=0` turns it off, for the on/off pixel proof.
 *
 * ONE COST, KNOWN AND LEFT: the view filter (view-occlusion.js) takes a piece as an
 * occluder only while it is visible, and it reads its occluders once a frame inside
 * the first batch's preparation, after this hook has swapped that batch. A far piece
 * of that batch therefore hides nothing behind it in the frame it is swapped. The
 * filter stays conservative (fewer occluders can only draw more), and the readings
 * above are net of it.
 */
import * as THREE from 'three';

/** The most an edge of a swapped piece may move on screen, in pixels. */
export const MAX_PIXELS = 1;
/**
 * The clustering cell, in metres of the structure's own frame. Coarser than the sun's
 * 6 cm because the bound is a view pixel, not a shadow texel: at 8 cm the reach is
 * 13.9 cm, under a pixel past about 95 m of depth on a 390x780 phone. Read at the
 * `roof` stand on the published app (docs/RESEARCH/alley-corner-budget-3312/):
 *   cell  keep  pieces  twin tris   roof stand    px changed
 *   4 cm  0.5     208    170,564   1,382,582        448
 *   4 cm  0.8     276    277,316   1,363,567        473
 *   6 cm  0.5     313    177,411   1,285,925        609
 *   6 cm  0.8     355    228,664   1,277,298        620
 *   8 cm  0.8     394    178,033   1,241,166        722   <- this
 *   8 cm  0.9     394    178,033   1,241,166        722
 *  10 cm  0.8     433    152,717   1,224,205        763
 * A finer cell keeps more of each piece and lets nearer pieces swap; a coarser one
 * keeps less and swaps only farther ones. 8 cm is the first that brings the stand
 * inside 1,270,000, with the fewest pixels changed of those that do.
 */
export const CELL_M = 0.08;
/** A twin is kept only at or under this share of its piece's triangles (the sun's
 *  is 0.5; a colour twin keeps every face over a cell, so more of them land between). */
export const KEEP_RATIO = 0.8;

export function farColourFromSearch(search) {
  try { return new URLSearchParams(search ?? '').get('farcolour') !== '0'; } catch { return true; }
}

const _sphere = new THREE.Sphere();
const _m = new THREE.Matrix4();
const _mTwin = new THREE.Matrix4();
const _size = new THREE.Vector2();
const _colour = new THREE.Color();
const _colourTwin = new THREE.Color();

function swapFar(batch, renderer, camera, pairs, swapped, maxPixels, control) {
  renderer.getDrawingBufferSize(_size);
  const pixels = _size.y * camera.projectionMatrix.elements[5] / 2;
  const view = camera.matrixWorldInverse;
  for (const p of pairs) {
    if (!batch.getVisibleAt(p.piece)) continue;
    batch.getMatrixAt(p.piece, _m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(p.piece), _sphere)
      .applyMatrix4(_m).applyMatrix4(batch.matrixWorld);
    // view depth is -z in the camera frame; the nearest a fragment can sit is the sphere's near side
    const nearest = -_sphere.center.applyMatrix4(view).z - _sphere.radius;
    if (!(nearest > 0)) continue;
    if (p.reachM * pixels / nearest > maxPixels) continue;
    // follow the piece if anything moved it since load, and wear its paint
    batch.getMatrixAt(p.twin, _mTwin);
    if (!_mTwin.equals(_m)) batch.setMatrixAt(p.twin, _m);
    batch.getColorAt(p.piece, _colour);
    if (!batch.getColorAt(p.twin, _colourTwin).equals(_colour)) batch.setColorAt(p.twin, _colour);
    batch.setVisibleAt(p.piece, false);
    // the harness's positive control draws neither: what the swap could have changed at most
    batch.setVisibleAt(p.twin, !control);
    swapped.push(p);
  }
  return swapped;
}

function restore(batch, swapped) {
  for (const p of swapped) {
    batch.setVisibleAt(p.twin, false);
    batch.setVisibleAt(p.piece, true);
  }
}

/**
 * Wrap one batch's colour-pass draw-list preparation. `pairs` is filled as instances
 * are added: `{ piece, twin, reachM, saved }`, instance ids in this batch. Install
 * AFTER far-roof-relief.js (it runs first, so a piece swapped here is passed over
 * there) and BEFORE batch-frustum-box.js's narrow phase, which only trusts the hook
 * it wrapped. The sun's pass is never touched: three prepares it through here with
 * no scene, and far-shadow.js owns it.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, pairs:Array, maxPixels?:number, control?:boolean, swapped?:number, saved?:number}} state
 *   `control` (a harness's) hides each piece the test passes and draws no twin in its place.
 */
export function drawFarColourAsTwins(batch, state) {
  const prepare = batch.onBeforeRender;
  const swapped = [];
  batch.onBeforeRender = function (renderer, scene, camera, geometry, material, group) {
    if (!state.on || scene === null || !camera || !state.pairs.length) {
      if (scene !== null) { state.swapped = 0; state.saved = 0; }
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    }
    swapFar(this, renderer, camera, state.pairs, swapped, state.maxPixels ?? MAX_PIXELS, state.control === true);
    try {
      return prepare.call(this, renderer, scene, camera, geometry, material, group);
    } finally {
      state.swapped = swapped.length;
      let saved = 0;
      for (const p of swapped) saved += p.saved;
      state.saved = saved;
      restore(this, swapped);
      swapped.length = 0;
    }
  };
}
