/**
 * GPU-compressed textures: one KTX2 loader for the whole renderer (T-2551, piece T-2582).
 *
 * A WebP, PNG or JPEG sheet is decoded on the CPU and uploaded as uncompressed RGBA8:
 * four bytes a texel, a third again for its mips. A Basis Universal `.ktx2` is
 * transcoded in a worker to the block format this GPU samples natively (ASTC or ETC2 on
 * a phone, BC7 or BC1 on a desktop) at half a byte to a byte a texel, and it stays that
 * size in GPU memory. `tools/ktx2_sheets.py` writes the files beside their sources.
 *
 * **One loader, one detection.** `initKTX2(renderer)` runs `detectSupport` once, at
 * boot, before any layer loads. Every GLTFLoader is handed the same instance through
 * `registerKTX2` so a `KHR_texture_basisu` GLB decodes on the same worker pool, and the
 * sheet loaders call `loadSheet`. The transcoder (`vendor/…/libs/basis/`, about 0.5 MB)
 * is fetched the first time a `.ktx2` is asked for, never at boot.
 *
 * **It degrades to the image path, never to a broken material.** `loadSheet` returns the
 * WebP/PNG/JPEG texture whenever the KTX2 path cannot serve: `initKTX2` was never called
 * (a tool harness importing one module), `?ktx2=0` (the kill switch, and the way to read
 * the before), a GPU that exposes no block format the transcoder targets, or a `.ktx2`
 * that did not arrive or would not transcode. The fallback is the exact texture this
 * module replaced, so the worst case is today's memory, not a missing roof.
 *
 * **One file, two residencies.** On the `light` texture tier (a phone, or a weak
 * desktop: device-profile.js `decide`) the top mip is dropped before upload, so a 1024²
 * sheet goes up as 512² and its chain — a quarter of the bytes from the same file, with
 * no second asset to ship or keep in step.
 * The shared GLB loader applies this same device policy before its texture is
 * cloned, including when residency re-decodes it. Full texture profiles retain
 * every mip; changing scene detail does not change the device texture profile.
 */
import * as THREE from 'three';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

let loader = null;
let dropTopMip = false;
let rendererRef = null;
let glbLoader = null;
/** What the boot found, for `__chicago4d.ktx2` and the memory meter's report. */
export const ktx2State = { enabled: false, reason: 'not initialised', dropTopMip: false, glb: 'shared',
  formats: null, sheets: { ktx2: 0, fallback: 0, gpuBytes: 0, failed: [] } };

/**
 * What a sheet holds on the GPU: a KTX2's transcoded blocks, every level it keeps; an
 * image's RGBA8 texels and a third again for the mips three generates. The memory
 * meter reads the sum (tools/measure_memory.mjs), so a before and after is one flag.
 */
export function sheetGpuBytes(tex) {
  if (tex.isCompressedTexture) return (tex.mipmaps ?? []).reduce((s, m) => s + (m.data?.byteLength ?? 0), 0);
  const img = tex.image;
  return Math.round((img?.width ?? 0) * (img?.height ?? 0) * 4 * 4 / 3);
}

/** Does this GPU expose any block format the Basis transcoder can target? */
function anyTarget(cfg) {
  return !!cfg && ['astcSupported', 'etc2Supported', 'etc1Supported', 'bptcSupported',
    'dxtSupported', 'pvrtcSupported'].some((k) => cfg[k]);
}

/**
 * Called once from main.js with the live renderer. `textures` is the device profile's
 * texture tier; `disabled` is the `?ktx2=0` kill switch.
 */
export function initKTX2(renderer, { textures = 'full', disabled = false } = {}) {
  dropTopMip = textures === 'light';
  ktx2State.dropTopMip = dropTopMip;
  rendererRef = renderer;
  if (disabled) { ktx2State.reason = 'off (?ktx2=0)'; return null; }
  try {
    const l = new KTX2Loader();
    l.detectSupport(renderer);
    const cfg = l.workerConfig;
    ktx2State.formats = Object.keys(cfg || {}).filter((k) => cfg[k]).map((k) => k.replace('Supported', ''));
    if (!anyTarget(cfg)) {
      // Transcoding to RGBA8 would cost what the image path costs, after a 0.5 MB
      // transcoder download and a worker. Not worth it; keep the image path.
      ktx2State.reason = 'no compressed format on this GPU';
      l.dispose();
      return null;
    }
    loader = withTexturePolicy(l);
    ktx2State.enabled = true;
    ktx2State.reason = 'on';
  } catch (err) {
    ktx2State.reason = `detectSupport failed — ${err.message}`;
  }
  return loader;
}

/**
 * Hand a KTX2 loader to a GLTFLoader, so a KHR_texture_basisu GLB decodes.
 *
 * Since T-2595 a textured web GLB REQUIRES the extension: it carries no PNG or JPEG to
 * fall back to, so a GLTFLoader with no KTX2 loader cannot open it at all. A sheet has
 * its image path; a GLB does not. So where the shared loader is off — `?ktx2=0`, or a
 * GPU with no block format — the GLB loader gets one of its own that transcodes every
 * texture to RGBA8, so the kill switch reads uncompressed storage rather than a
 * missing house. The same device texture policy applies there: Light drops mip 0
 * for both block-compressed and RGBA GLB textures; full texture profiles keep it.
 */
export function registerKTX2(gltfLoader) {
  const l = loader || rgbaGlbLoader();
  if (l) gltfLoader.setKTX2Loader(l);
  return gltfLoader;
}

function rgbaGlbLoader() {
  if (glbLoader || !rendererRef) return glbLoader;
  try {
    const l = new KTX2Loader();
    l.detectSupport(rendererRef);
    // No block format: the transcoder falls through to RGBA32 for every texture.
    for (const k of Object.keys(l.workerConfig || {})) l.workerConfig[k] = false;
    glbLoader = withTexturePolicy(l);
    ktx2State.glb = 'rgba8';
  } catch (err) {
    ktx2State.glb = `unavailable — ${err.message}`;
  }
  return glbLoader;
}

/**
 * T-2743: three's WorkerPool keeps the resolver of each worker's LAST task until
 * that worker takes another, and the resolver holds the worker's reply: every
 * transcoded level of that sheet, the top one `dropTop` let go included. So the
 * last sheet through each worker stayed in memory twice over (7.5 MB on the 1904
 * phone when the leaf atlas came last). An idle worker's resolver has already
 * run; dropping it changes nothing but what the page keeps.
 */
function forgetSettledTranscodes(l) {
  const pool = l?.workerPool;
  if (!pool?.workersResolve) return;
  for (let i = 0; i < pool.workersResolve.length; i++) {
    if (!(pool.workerStatus & (1 << i))) pool.workersResolve[i] = null;
  }
}

/** Apply the existing device texture policy at the shared loader boundary.
 * GLTFLoader and texture residency both call this same loader's load(), so a
 * house's initial decode and its later re-decode keep the same dimensions.
 * The library path may call dropTop again; the texture flag makes that a no-op.
 * No second loader/worker pool or second copy of the source image is created. */
function withTexturePolicy(l) {
  const load = l.load.bind(l);
  l.load = (url, onLoad, onProgress, onError) => load(url, (tex) => {
    dropTop(tex);
    forgetSettledTranscodes(l);
    onLoad?.(tex);
  }, onProgress, onError);
  return l;
}

/** The light tier's residency: upload from mip 1, a quarter of the bytes. */
function dropTop(tex) {
  if (!dropTopMip || tex.userData?.ktx2DroppedMip0 || !(tex.mipmaps?.length > 1)) return tex;
  tex.mipmaps = tex.mipmaps.slice(1);
  const { width, height } = tex.mipmaps[0];
  tex.image = { width, height, depth: 1 };
  tex.userData.ktx2DroppedMip0 = true;
  return tex;
}

/**
 * One library sheet: the `.ktx2` where this GPU can take it, else the image at
 * `fallbackUrl` through `imageLoader` (a THREE.TextureLoader). `srgb` tags colour;
 * every data map (normal, ORM) stays linear. The caller sets wrap and anisotropy on
 * whichever comes back — both are plain `THREE.Texture`s to a material.
 */
export async function loadSheet(ktx2Url, fallbackUrl, imageLoader, { srgb = false } = {}) {
  const tex = await loadCompressed(ktx2Url, { srgb });
  if (tex) {
    countSheet(tex);
    return tex;
  }
  return loadFallback(fallbackUrl, imageLoader, { srgb });
}

/**
 * The `.ktx2` alone, or null wherever `loadSheet` would fall back — for a sheet whose
 * fallback is not an image but a map the page derives (the wall relief's `orl`,
 * T-2588), so the caller decides what to do instead. Uncounted: the caller counts
 * what it keeps with `countSheet`, so a pair abandoned half-loaded is not billed.
 */
export async function loadCompressed(ktx2Url, { srgb = false } = {}) {
  if (!loader || !ktx2Url) return null;
  try {
    const tex = await loader.loadAsync(ktx2Url);
    // The file records its own transfer function, and KTX2Loader reads it; this
    // only asserts what the caller expects, so a mislabelled file reads as itself.
    tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    tex.userData.ktx2 = true;
    dropTop(tex);
    forgetSettledTranscodes(loader);
    return tex;
  } catch (err) {
    ktx2State.sheets.failed.push(`${ktx2Url.split('/').pop()}: ${err.message}`);
    return null;
  }
}

/** Bill a sheet the page keeps to the boot's report: `ktx2` or `fallback`, and its GPU bytes. */
export function countSheet(tex) {
  if (tex.userData?.ktx2) ktx2State.sheets.ktx2 += 1;
  else ktx2State.sheets.fallback += 1;
  ktx2State.sheets.gpuBytes += sheetGpuBytes(tex);
}

async function loadFallback(fallbackUrl, imageLoader, { srgb }) {
  ktx2State.sheets.fallback += 1;
  const tex = await imageLoader.loadAsync(fallbackUrl);
  tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  ktx2State.sheets.gpuBytes += sheetGpuBytes(tex);
  return tex;
}

/** `foo_orm.webp` → `foo_orm.ktx2`, `foo_orm_web.jpg` → `foo_orm.ktx2`: the converter's names. */
export function ktx2Beside(url) {
  return String(url).replace(/(_web)?\.(webp|png|jpe?g)$/i, '.ktx2');
}
