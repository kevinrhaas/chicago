/**
 * THE DEPTH-BREAK DISCRIMINATOR — what the depth field does at a moving pixel.
 *
 * T-0013 wrote this to answer R-BUG6(c2): of the pixels a layer's own footprint
 * surrounds on all eight sides, how many are the layer FIGHTING ITSELF and how
 * many are one of its surfaces in front of another? The three answers a renderer
 * can give are told apart from the DEPTH FIELD itself rather than by analogy:
 *
 *   1. **an internal edge** — the pixel straddles a depth DISCONTINUITY between
 *      two surfaces of the same layer (one crown in front of another, a chimney
 *      against its own roof, a house against the house behind). A camera
 *      resamples such an edge whatever it is made of: that is antialiasing
 *      working, exactly as a layer-to-layer silhouette is, and it is not a
 *      defect.
 *   2. **a depth REORDER** — the depth field is locally smooth and the
 *      front-most surface is at a different distance after the nudge. Two
 *      surfaces swapped. That IS a fight.
 *   3. **neither** — the same surface at the same distance, drawn a different
 *      colour. Nothing about the geometry moved; the cause is shading. A
 *      near-coplanar z-fight also lands here, because a pair a millimetre apart
 *      swaps without moving the depth.
 *
 * A discontinuity is a SECOND difference, not a slope: `|d(-1) + d(+1) - 2·d(0)|`
 * is ~0 on any plane however steeply it is seen, and large at a break, so a
 * grazing roof cannot be mistaken for an edge and no per-surface threshold is
 * needed. A 2 mm camera translation moves a real surface's distance by at most
 * 2 mm, so anything past `REORDER_M` is a different surface.
 *
 * WHY IT IS A MODULE. `tools/diagnose_interior_flicker.mjs` measured all of the
 * above and `tools/measure_tie_class.mjs` is the instrument whose "INTERIOR"
 * column the finding corrects (T-0156). Both now ask the same question of the
 * same frames, and a copied discriminator is two discriminators the moment one
 * of them is tuned — which is the failure this project has already paid for
 * twice, in `generate_frontage_works.py`'s imported trade table and in
 * `block_faces`' imported face arithmetic. There is one copy, and it is here.
 */

/** A depth break, in metres of second difference. 2 mm of camera cannot make one. */
export const BREAK_M = Number(process.env.TIE_BREAK_M || 0.3);
/** A different surface, in metres. A 2 mm nudge moves a real one by 2 mm. */
export const REORDER_M = Number(process.env.TIE_REORDER_M || 0.3);
/** The renderer's far plane. `stats().cameraNear` gives the other end live. */
export const FAR_M = 3000;

/**
 * Swap every mesh onto a packed-depth material, or back.
 *
 * Every mesh keeps its own `onBeforeCompile`, because the trees' wind patch
 * displaces vertices there: a depth pass without it would photograph the town's
 * geometry and the timber's ghost, and every crown would read as a break.
 *
 * Resolves the PAGE's own three through its own import map, so the depth
 * material is the same class the renderer already compiled against.
 */
export async function swapDepthMaterials(page, on) {
  return page.evaluate(async (want) => {
    const api = window.__chicago4d;
    if (!window.__chiTHREE) {
      const map = JSON.parse(document.querySelector('script[type=importmap]').textContent);
      window.__chiTHREE = await import(new URL(map.imports.three, location.href).href);
    }
    const THREE = window.__chiTHREE;
    api.scene3d.traverse((o) => {
      if (!o.isMesh || !o.material) return;
      if (want) {
        const src = Array.isArray(o.material) ? o.material[0] : o.material;
        if (!o.userData.__origMat) o.userData.__origMat = o.material;
        const d = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
        d.side = src.side;
        d.alphaTest = src.alphaTest ?? 0;
        if (src.alphaMap) d.alphaMap = src.alphaMap;
        if (typeof src.onBeforeCompile === 'function') d.onBeforeCompile = src.onBeforeCompile;
        d.customProgramCacheKey = () => `chi-depth-${src.uuid}`;
        o.material = d;
      } else if (o.userData.__origMat) {
        o.material.dispose?.();
        o.material = o.userData.__origMat;
        delete o.userData.__origMat;
      }
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
    return want;
  }, on);
}

/** three's packDepthToRGBA, read back: UnpackDownscale / (256^3, 256^2, 256, 1). */
export function unpack(img, p) {
  const i = p * 4;
  const v = (img.data[i] / 255) / 16777216
    + (img.data[i + 1] / 255) / 65536
    + (img.data[i + 2] / 255) / 256
    + (img.data[i + 3] / 255);
  return v * (255 / 256);
}

/** A whole packed-depth frame, linearised to metres along the view axis. */
export function lineariseDepth(img, near, far = FAR_M) {
  const out = new Float64Array(img.width * img.height);
  for (let p = 0; p < out.length; p++) {
    const ndc = 2 * unpack(img, p) - 1;
    out[p] = (2 * near * far) / (far + near - ndc * (far - near));
  }
  return out;
}

/**
 * Partition `pixels` into the three classes above, plus `sky` — a pixel whose
 * depth cannot be decoded.
 *
 * `sky` is a finding rather than a gap in one: a packed depth photographed
 * through MSAA is a BLEND of the samples' bytes and the packing is not linear
 * across its four channels, so a pixel that reads the far plane where its layer
 * is drawn is a pixel with more than one surface in it — an edge, counted
 * separately rather than assumed.
 */
export function classifyDepth(pixels, lin0, lin1, width, opts = {}) {
  const breakM = opts.breakM ?? BREAK_M;
  const reorderM = opts.reorderM ?? REORDER_M;
  const far = opts.far ?? FAR_M;
  const out = { break: [], reorder: [], smooth: [], sky: [] };
  for (const p of pixels) {
    if (lin0[p] > far * 0.9) { out.sky.push(p); continue; }
    const sx = Math.abs(lin0[p - 1] + lin0[p + 1] - 2 * lin0[p]);
    const sy = Math.abs(lin0[p - width] + lin0[p + width] - 2 * lin0[p]);
    if (Math.max(sx, sy) > breakM) { out.break.push(p); continue; }
    if (Math.abs(lin1[p] - lin0[p]) > reorderM) { out.reorder.push(p); continue; }
    out.smooth.push(p);
  }
  return out;
}
