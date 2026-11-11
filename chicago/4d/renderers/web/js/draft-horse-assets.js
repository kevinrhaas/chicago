// SPDX-License-Identifier: GPL-3.0-or-later
// One immutable horse template across the moving and parked teams. Each team
// owns its cloned skeletons; embedded images/geometry live until the last lease.
import { disposeLoadedAsset } from './scene-loader.js';
import { prepareHorseTemplate } from './horse-appearance.js';

const entries = new Map();

/**
 * T-3542: THE HORSE'S PICTURES, SOFTER ON A DEVICE SAVING MEMORY. Since the owner's ruling
 * (2026-11-10) a phone's Light keeps its horses and carriages; their pictures (six maps,
 * about 22 MB on the GPU) are what that costs it. main.js sets a cap on a memory-saving
 * device (main.js `lowMem`), and every map wider or taller than it is redrawn at the cap
 * before the template is shared: the same horse, blurrier up close, never gone.
 */
let textureCap = 0;
export function setDraftHorseTextureCap(px) { textureCap = Number.isFinite(px) && px > 0 ? px : 0; }

/** Redraw each map image over `cap` px at the cap (aspect kept). Returns the count redrawn. */
export async function capTextureImages(root, cap) {
  if (!(cap > 0) || typeof createImageBitmap !== 'function') return 0;
  const seen = new Map();
  root.traverse(node => {
    for (const material of [node.material].flat().filter(Boolean)) {
      for (const value of Object.values(material)) {
        const image = value?.isTexture ? value.image : null;
        const w = image?.width, h = image?.height;
        if (!image || !(Math.max(w, h) > cap)) continue;
        if (!seen.has(image)) seen.set(image, []);
        if (!seen.get(image).includes(value)) seen.get(image).push(value);
      }
    }
  });
  for (const [image, textures] of seen) {
    const k = cap / Math.max(image.width, image.height);
    const smaller = await createImageBitmap(image, { resizeWidth: Math.max(1, Math.round(image.width * k)),
      resizeHeight: Math.max(1, Math.round(image.height * k)), resizeQuality: 'high' });
    for (const texture of textures) { texture.image = smaller; texture.needsUpdate = true; }
    image.close?.();
  }
  return seen.size;
}

export async function acquireDraftHorse({ url, sha256, materialVariant, loader }) {
  if (!url || !/^[a-f0-9]{64}$/.test(sha256 ?? '') || !loader?.parseAsync
    || !['source_native', 'organic_dielectric_v1'].includes(materialVariant)) {
    throw Error('draft horse: explicit bound asset, material variant and loader required');
  }
  const cap = textureCap;
  const key = `${url}|${sha256}|${materialVariant}|${cap}`;
  let entry = entries.get(key);
  if (!entry) {
    entry = { leases: 0, asset: null, promise: null };
    entry.promise = (async () => {
      const response = await fetch(url);
      if (!response.ok) throw Error(`draft horse: HTTP${response.status}`);
      const bytes = await response.arrayBuffer();
      const actual = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
        .map(n => n.toString(16).padStart(2, '0')).join('');
      if (actual !== sha256) throw Error('draft horse: actual horse differs from its model binding');
      const asset = await loader.parseAsync(bytes, new URL('.', url).href);
      if (cap) await capTextureImages(asset.scene, cap);
      prepareHorseTemplate(asset, materialVariant);
      entry.asset = asset;
      return asset;
    })();
    entries.set(key, entry);
  }
  entry.leases++;
  const release = () => {
    if (!entry.leases) return;
    entry.leases--;
    if (!entry.leases) {
      if (entries.get(key) === entry) entries.delete(key);
      if (entry.asset) disposeLoadedAsset(entry.asset);
    }
  };
  try {
    const asset = await entry.promise;
    let released = false;
    return { asset, release() { if (!released) { released = true; release(); } } };
  } catch (error) { release(); throw error; }
}
