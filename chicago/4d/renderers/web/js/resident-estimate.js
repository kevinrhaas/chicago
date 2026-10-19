/**
 * resident-estimate.js — what the page has handed the GPU, read off the scene (T-2828).
 *
 * The owner's 1904 phone was killed walking up to the Glessner front, and the black box
 * (blackbox.js) said what was resident only as counts: 741 textures, 291 geometries.
 * iOS gives a page no heap reading, so a count was all the next report could carry, and
 * a count does not say whether 741 textures are 40 MB or 400. This is the byte figure
 * the page CAN read: the scene walked, every geometry's attributes at the layout they
 * were uploaded at (upload-release.js records it as it lets an array go, T-2569), and
 * every texture three has a GPU copy of, once per source, at its texels (a KTX2 at its
 * transcoded blocks; a level a phone let go of, at the bytes texture residency
 * recorded). It is an ESTIMATE — what a driver adds is not here, and shadow maps and
 * render targets are not textures of the scene — and it sits beside the measured meter
 * (tools/measure_memory.mjs) for exactly that reason. The black box reads it every
 * SAMPLE_MS (3 s), so it allocates two sets a call and nothing per object.
 */

/** `{ geometry, textures }` in bytes, for `scene` as `renderer` has uploaded it. */
export function residentEstimate(scene, renderer) {
  const seenGeo = new Set();
  const seenTex = new Set();
  let geometry = 0;
  let textures = 0;
  const props = renderer?.properties;
  const attrBytes = (attr, isIndex) => {
    if (!attr) return 0;
    const data = attr.isInterleavedBufferAttribute ? attr.data : attr;
    if (seenGeo.has(data)) return 0;
    seenGeo.add(data);
    if (data.array?.byteLength) return data.array.byteLength;
    if (data.userData?.uploadBytes) return data.userData.uploadBytes;
    const count = data.count ?? attr.count ?? 0;
    const item = data.stride ?? attr.itemSize ?? 1;
    return count * item * (isIndex ? (count > 65535 ? 4 : 2) : 4);
  };
  const texBytes = (t) => {
    if (t.isCompressedTexture) {
      let sum = 0;
      for (const m of t.mipmaps ?? []) sum += m?.data?.byteLength ?? 0;
      return sum || t.userData?.releasedBytes || 0;
    }
    const img = t.image ?? t.source?.data;
    if (img?.data?.byteLength) return img.data.byteLength;
    const w = img?.width || img?.videoWidth || 0;
    const h = img?.height || img?.videoHeight || 0;
    return Math.round(w * h * 4 * (t.generateMipmaps ? 4 / 3 : 1));
  };
  const texture = (t) => {
    if (!t?.isTexture || seenTex.has(t.source ?? t)) return;
    if (props && props.get(t).__webglTexture === undefined) return; // never uploaded, or let go
    seenTex.add(t.source ?? t);
    textures += texBytes(t);
  };
  const material = (m) => {
    if (!m) return;
    for (const key in m) {
      const v = m[key];
      if (v?.isTexture) texture(v);
    }
  };
  scene.traverse((o) => {
    const g = o.geometry;
    if (g?.attributes) {
      for (const name in g.attributes) geometry += attrBytes(g.attributes[name], false);
      geometry += attrBytes(g.index, true);
    }
    if (o.isInstancedMesh) geometry += attrBytes(o.instanceMatrix, false) + attrBytes(o.instanceColor, false);
    if (Array.isArray(o.material)) for (const m of o.material) material(m);
    else material(o.material);
  });
  return { geometry, textures };
}
