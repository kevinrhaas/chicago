// SPDX-License-Identifier: GPL-3.0-or-later
// One immutable horse template across the moving and parked teams. Each team
// owns its cloned skeletons; embedded images/geometry live until the last lease.
import { disposeLoadedAsset } from './scene-loader.js';
import { prepareHorseTemplate } from './horse-appearance.js';

const entries = new Map();
export async function acquireDraftHorse({ url, sha256, materialVariant, loader }) {
  if (!url || !/^[a-f0-9]{64}$/.test(sha256 ?? '') || !loader?.parseAsync
    || !['source_native', 'organic_dielectric_v1'].includes(materialVariant)) {
    throw Error('draft horse: explicit bound asset, material variant and loader required');
  }
  const key = `${url}|${sha256}|${materialVariant}`;
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
