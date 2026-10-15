/**
 * T-2502: a scene's APRON FIELD — a second, small heightfield the scene stands
 * beside its terrain box, so a place off the box has ground of its own.
 *
 * The 1812 scene's is the South Branch carried from the box floor down to Lee's
 * Place (`data/terrain/epochs/e1830_natural/apron_south_branch.json`, written by
 * tools/derive_apron_south_branch_1812.py). Its layout is the box's own, row 0 at
 * the south edge, so it is adopted into a plain `Heightfield`; terrain.js samples
 * it outside the box before falling back, cuts the box's carried apron out over
 * the field's `cut_local_enu_m`, and draws the mesh built here in its place.
 *
 * The mesh is the field's own samples, one vertex each, so it is the surface the
 * walker stands on by construction. Two rows are added, and neither moves a
 * sample: a LIP carried a hand's breadth north under the box's floor row, so the
 * two meshes' different spacings cannot open a crack where they meet, and the
 * south row carried on to `skirtToN` at its own heights — the rule the box's own
 * skirt keeps, so the river leaves the field's south edge rather than ending in a
 * bank there.
 */
import * as THREE from 'three';

/** How far north the lip runs under the box's floor row, and how far below it. */
export const APRON_LIP_M = 0.5;
export const APRON_LIP_DROP_M = 0.03;
/** terrain_gen.CONF_CONJECTURAL: every sample of an apron field is conjectural. */
const CONF_CONJECTURAL = 1.0;

/**
 * @param {{cols:number, rows:number, cellM:number, originE:number, originN:number,
 *          data:Float32Array}} hf  an adopted Heightfield
 * @param {number} skirtToN  local N the south row is carried to (south of originN)
 * @returns {THREE.BufferGeometry}
 */
export function apronGeometry(hf, skirtToN) {
  const { cols, rows, cellM, originE, originN, data } = hf;
  const outRows = rows + 2;
  const pos = new Float32Array(cols * outRows * 3);
  // glTF / world: +X east, +Y up, -Z north.
  const put = (row, c, n, y) => {
    const i = (row * cols + c) * 3;
    pos[i] = originE + c * cellM;
    pos[i + 1] = y;
    pos[i + 2] = -n;
  };
  const south = Math.min(skirtToN, originN);
  const northN = originN + (rows - 1) * cellM;
  for (let c = 0; c < cols; c++) {
    put(0, c, south, data[c]);
    for (let r = 0; r < rows; r++) put(r + 1, c, originN + r * cellM, data[r * cols + c]);
    put(rows + 1, c, northN + APRON_LIP_M, data[(rows - 1) * cols + c] - APRON_LIP_DROP_M);
  }
  const idx = new Uint32Array((cols - 1) * (outRows - 1) * 6);
  let k = 0;
  for (let r = 0; r < outRows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      const a = r * cols + c;
      // Rows run northward toward -Z, columns eastward along +X: a -> a+1 ->
      // a+cols is counter-clockwise from above, so every face points up (see
      // terrain.js gridGeometry, which learnt that the hard way).
      idx[k++] = a; idx[k++] = a + 1; idx[k++] = a + cols;
      idx[k++] = a + 1; idx[k++] = a + cols + 1; idx[k++] = a + cols;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('_confidence',
    new THREE.BufferAttribute(new Float32Array(cols * outRows).fill(CONF_CONJECTURAL), 1));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  g.computeBoundingBox();
  g.computeBoundingSphere();
  return g;
}

/**
 * The ground cut (terrain.js § GROUND_CUT_FRAGMENT) that takes the box's own
 * carried apron out from under the field: a one-texel mask over the whole cut box.
 * @param {{e:number[], n:number[]}} cut  `cut_local_enu_m`
 */
export function apronCut(cut) {
  const mask = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1);
  mask.needsUpdate = true;
  const [e0, e1] = cut.e;
  const [n0, n1] = cut.n;
  return { mask, x0: e0, z0: -n1, width: e1 - e0, depth: n1 - n0 };
}
