/**
 * scene-loader.js — scene JSON -> GLBs + sidecars -> a registry keyed by
 * `structure_id`.
 *
 * The renderer consumes glTF plus JSON sidecars and nothing else
 * (`AGENTS.md` rule 5). It never reaches into `generators/`, never resolves a
 * structure's phases against the scene date, never decides what is documented.
 * All of that has already happened by the time these files exist; here we only
 * fetch, index and hand on.
 *
 * Where the data lives
 * --------------------
 * Two committed layouts, told apart by the page's own path rather than by
 * probing (a probe means a 404 in the network log, and a 404 in the network log
 * means the smoke test cannot tell a healthy boot from a broken one):
 *
 *   dev        renderers/web/index.html   ->  ../../data/   ../../assets/
 *   published  4d/walk/index.html         ->  ../data/      ../data/
 *              4d/, 4d/1835/ (front doors, `<base href>` into walk/) -> same
 *
 * `?data=` and `?assets=` override either.
 */

import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { registerKTX2 } from './ktx2.js';
import { shareImageSources, releaseSharedImage } from './shared-images.js';
import { resolveStructureVersion } from './structure-versions.js';

const GLB_MAGIC = 0x46546c67;   // 'glTF', little-endian

export function resolveBases(loc = window.location) {
  const params = new URLSearchParams(loc.search);
  // The DOCUMENT's base, not the address bar: the published front doors
  // (/4d/, /4d/1835/) are copies of walk/index.html carrying
  // `<base href="…walk/">`, so they resolve from walk/ exactly as walk/ does.
  const base = (loc === globalThis.window?.location && globalThis.document?.baseURI) || loc.href;
  const here = new URL('.', base);
  const dev = /\/renderers\/web\/$/.test(here.pathname);
  return {
    dev,
    sourceAssetLayout: dev && !params.has('assets'),
    dataBase: new URL(params.get('data') ?? (dev ? '../../data/' : '../data/'), here),
    // Published layout puts the web-derivative GLBs at data/gltf/, and sidecar
    // `asset` paths are relative to the data root (see docs/GLB-CONTRACT.md
    // § Paths). In the source tree the same files sit under assets/web/.
    assetBase: new URL(params.get('assets') ?? (dev ? '../../assets/' : '../data/'), here),
  };
}

/** T-1730: only this explicitly selected comparison build has a detail derivative.
 * It remains the same record, version, placement and confidence at every setting. */
export function hasInspectionLod(record) {
  return record?.id === 'glessner_house' && (record.version?.label === 'v4'
    || (!record.version && record.sidecar?.asset === 'gltf/glessner_house__as_built_1887.glb'))
    && typeof record.sidecar?.asset_lods?.light === 'string'
    && record.sidecar.asset_lods.light.length > 0;
}

export function detailAssetPath(record, detail) {
  return hasInspectionLod(record) && (detail === 'balanced' || detail === 'light')
    ? record.sidecar.asset_lods.light : record.sidecar.asset;
}

export function detailAssetUrl(record, detail, bases) {
  const asset = detailAssetPath(record, detail);
  // The ordinary source viewer reads masters from assets/gltf. A render-only LOD
  // has no pretend master: its source-layout address is assets/web instead.
  const relative = bases.sourceAssetLayout && asset !== record.sidecar.asset
    ? asset.replace(/^gltf\//, 'web/') : asset;
  return new URL(relative, bases.assetBase);
}

/** A serial, latest-request-wins transaction. Preparation never removes the visible
 * model. Superseded work is disposed; a failed request leaves the committed tier. */
export function createLatestDetailSwitch({ initial, prepare, commit, discard, onError }) {
  let current = initial;
  let requested = initial;
  let revision = 0;
  let pending = Promise.resolve(false);
  return {
    get current() { return current; },
    set(level) {
      if (level === requested) return pending;
      requested = level;
      const mine = ++revision;
      const run = pending.then(async () => {
        if (mine !== revision || level === current) return false;
        let candidate;
        try {
          candidate = await prepare(level);
          if (mine !== revision) { discard(candidate); return false; }
          commit(candidate, level);
          current = level;
          return true;
        } catch (error) {
          if (candidate) discard(candidate);
          if (mine === revision) {
            requested = current;
            onError(error, level, current);
          }
          return false;
        }
      });
      pending = run;
      return run;
    },
  };
}

/** Source GLTF resources are separate from the normalized batch buffers. Called
 * only after their last batch is retired, never while the old model is visible. */
export function disposeLoadedAsset(gltf) {
  const geometries = new Set();
  const materials = new Set();
  const textures = new Set();
  gltf?.scene?.traverse((node) => {
    if (node.geometry) geometries.add(node.geometry);
    for (const material of (Array.isArray(node.material) ? node.material : [node.material])) {
      if (!material) continue;
      materials.add(material);
      for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
    }
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
  const images = new Set();
  for (const texture of textures) { texture.dispose(); if (texture.image) images.add(texture.image); }
  // T-2464: a bitmap another building still draws with stays open.
  for (const image of images) if (releaseSharedImage(image)) image.close?.();
}

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/**
 * Put a packed boot sidecar back together (T-2315). `tools/pack_boot_sidecars.mjs`
 * ships each scene's records fifty to a file (`boot/part-<n>.json`, by index row), with
 * every value three or more of them repeat replaced by `{ "$shared": n }`, and the
 * values once, in `boot/shared.json`. This restores the
 * record in place, key for key and in order, so the registry holds exactly what the
 * record's own URL holds. Each object is a fresh copy: two records must never share one
 * object, or a change to one card's data would quietly be a change to another's. The
 * gate runs the tool's copy of this function over every shipped record.
 */
export function rehydrate(v, values) {
  if (v === null || typeof v !== 'object') return v;
  const keys = Object.keys(v);
  if (keys.length === 1 && keys[0] === '$shared' && !Array.isArray(v)) {
    const got = values[v.$shared];
    if (got === undefined) throw new Error(`no shared value ${v.$shared}`);
    return structuredClone(got);
  }
  for (const k of keys) v[k] = rehydrate(v[k], values);
  return v;
}

/** Peek at a GLB's JSON chunk without decoding the whole asset. */
function glbHeader(buffer) {
  const dv = new DataView(buffer);
  if (buffer.byteLength < 20 || dv.getUint32(0, true) !== GLB_MAGIC) return null;
  const jsonLength = dv.getUint32(12, true);
  const text = new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength));
  try { return JSON.parse(text); } catch { return null; }
}

let meshoptPromise = null;
/**
 * `EXT_meshopt_compression` is what the published web derivatives carry
 * (docs/GLB-CONTRACT.md, "Compression"). The decoder is vendored, but importing
 * it instantiates a WebAssembly module, so it is loaded only when an asset
 * actually needs it — an uncompressed master must not pay for it.
 */
export function loadMeshoptDecoder() {
  if (!meshoptPromise) {
    meshoptPromise = import('three/addons/libs/meshopt_decoder.module.js')
      .then((m) => m.MeshoptDecoder);
  }
  return meshoptPromise;
}

/**
 * Fetch one asset, and if the network refuses once, ASK AGAIN — T-1126.
 *
 * A scene load fires ~380 concurrent `fetch`es at a static host in the space of
 * a second. Browsers cap concurrency per origin and queue the rest, and a
 * queued request is a request that can be dropped: on 14 September 2026 the
 * owner walked Dearborn Street and found one auction room absent, with its
 * signboard still hanging where its east wall should have been, and the same
 * page reloaded a minute later had it. One GLB out of 380, transient, gone on
 * reload — the signature of a dropped request, not of a broken file.
 *
 * Nothing here diagnoses WHICH cause it was, and it deliberately does not try:
 * a single retry after a short pause answers the dropped-request family
 * (concurrency queue, aborted socket, a `publish.sh` window while the mirror is
 * mid-write) without a theory about which member of it happened. What makes the
 * rate knowable is not this function but the count it feeds — `retried` says how
 * often the first ask failed, which is the figure that was missing.
 *
 * The retry is ONE, and it is not a loop. A GLB that is genuinely absent or
 * genuinely corrupt must still fail fast and be reported: the answer to a
 * missing building is a named error, never a page that hangs looking for it.
 */
async function fetchAsset(url) {
  let first;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return { buffer: await res.arrayBuffer(), retried: attempt > 0 };
    } catch (err) {
      if (attempt) throw new Error(`${err.message} (asked twice)`);
      first = err;
      // Long enough for a saturated connection pool to drain a slot, short
      // enough that nobody waits on it: the other ~379 loads are still in
      // flight beside this one and the boot is gated on all of them.
      await new Promise((r) => { setTimeout(r, 250); });
    }
  }
  throw first;
}

/**
 * HOW MANY STRUCTURES LOAD AT ONCE — T-2597. Every one, still, and on purpose.
 *
 * `loadScene` starts every structure of the year together: 686 sidecars and GLB
 * fetches on 1835, 151 on 1904. T-2554 asked for a pool of 6 to 8, on the theory
 * that every GLB arriving before its parse finished was held beside every other
 * one, so the boot's peak was the whole town's files at once. T-2597 measured it
 * (`tools/measure_boot_peak.mjs`, HTTP/2 at a 60 ms round trip, 2026-10-16) and
 * the theory does not hold where it matters:
 *
 *   - on 1904 the most GLB bytes ever held unparsed are ONE file, Glessner's
 *     (56.4 MB at full, 31.1 MB light): the small houses parse as they land. A
 *     pool of 24 held 63.6 / 38.3 MB, because it holds two dozen files beside
 *     Glessner instead of none. No count pool can go under the largest file;
 *     T-2596 (Glessner in KTX2, light capped at 1024) is what shrinks it.
 *   - on 1835 the pile is 13.4 MB of a boot that peaks above 400 MB of
 *     ArrayBuffers, and a pool of 8 cut it to 0.2 MB for 5 s more boot on a
 *     phone (686 loads in 8 lanes is ~86 round trips end to end).
 *
 * So the default stays unbounded. `?boot-pool=N` runs the loads N at a time, in
 * index order, and `?boot-pool=0` is the unbounded default named, so the meter
 * reads any pool against today in one build; `bootPool` on the harness handle
 * says what the boot held.
 */
export const BOOT_POOL = Infinity;

/** The pool a page address asks for: a positive N, or BOOT_POOL (0, absent, or malformed). */
export function bootPoolFromSearch(search) {
  const raw = new URLSearchParams(search).get('boot-pool');
  const n = raw === null ? NaN : Number(raw);
  return Number.isInteger(n) && n > 0 ? n : BOOT_POOL;
}

/**
 * Run `work(item, index)` over `items` with at most `limit` running at once, in
 * index order; resolves when all have, rejects with the first error (as
 * `Promise.all` did). `limit` of Infinity is every item at once.
 */
export async function pooled(items, limit, work) {
  const lanes = Math.max(1, Math.min(items.length, Number.isFinite(limit) ? Math.floor(limit) : items.length));
  let next = 0;
  const lane = async () => {
    while (next < items.length) {
      const at = next;
      next += 1;
      await work(items[at], at);
    }
  };
  await Promise.all(Array.from({ length: items.length ? lanes : 0 }, lane));
}

/**
 * Load one scene.
 *
 * `version` is `readVersionRequest(location.search)` — `?structure=<id>&version=<label>`
 * (T-1727). When it names a committed version, exactly that one entry's sidecar (and so
 * its mesh) is loaded from the version instead of the default; nothing else changes. The
 * versions index is fetched ONLY in that case, so a plain boot downloads nothing new.
 *
 * @returns {Promise<{
 *   year: string, scene: object, datum: object,
 *   registry: Map<string, object>, problems: string[], bytes: number,
 *   versionState: object|null
 * }>}
 */
export async function loadScene(year, bases = resolveBases(), {
  onProgress = () => {}, version = null, detail = 'full', keepAssetBytes = true,
  pool = BOOT_POOL,
  keepEncodedImages = false,
} = {}) {
  const { dataBase, assetBase } = bases;
  const problems = [];

  const [scene, datum] = await Promise.all([
    getJSON(new URL(`scenes/${year}.json`, dataBase)),
    getJSON(new URL('datum.json', dataBase)),
  ]);

  // Which sidecars belong to this scene. A static host cannot be globbed, so
  // the set has to be published as data. docs/GLB-CONTRACT.md does not specify
  // this file yet — see the Track B report; the shape is deliberately trivial so
  // that compile_scene.py can adopt it without argument.
  const indexUrl = new URL(`sidecars/${year}/index.json`, dataBase);
  let index;
  try {
    index = await getJSON(indexUrl);
  } catch (err) {
    problems.push(`no sidecar index for scene ${year} (${err.message}) — nothing to place`);
    return { year, scene, datum, registry: new Map(), problems, bytes: 0, versionState: null };
  }

  // The index lists either bare ids or `{ id, sidecar, asset }` rows. Accept
  // both: the compiler and this renderer are being written in parallel, and a
  // loader that dies on the richer shape is a loader that dies on the version
  // that eventually ships.
  const entries = (Array.isArray(index.structures) ? index.structures : [])
    .map((row) => (typeof row === 'string' ? { id: row } : row))
    .filter((row) => row && typeof row.id === 'string');

  // T-1727. One entry, at most, is pointed at a version instead of its default. A copy
  // of the row, never the row: `index` is handed on to the rest of the page as the
  // scene's own list, and it must go on saying what the default town is.
  const versionState = await resolveStructureVersion(version, {
    year, dataBase, entries, getJSON,
  });
  if (versionState.active) {
    const at = entries.findIndex((row) => row.id === versionState.active.id);
    entries[at] = { ...entries[at], sidecar: versionState.active.sidecar, version: versionState.active };
  }

  // T-2315. The published index names the packed boot copies; the source tree's does
  // not, so the dev layout reads each record whole and never asks for a file that is
  // not there. The shared values are one request, made once, before any record.
  const boot = index.boot && typeof index.boot.dir === 'string' && typeof index.boot.shared === 'string'
    && Number.isInteger(index.boot.per_part) && index.boot.per_part > 0 ? index.boot : null;
  let shared = null;
  if (boot) {
    try {
      shared = (await getJSON(new URL(boot.shared, dataBase))).values;
      if (!Array.isArray(shared)) throw new Error('holds no `values`');
    } catch (err) {
      problems.push(`${boot.shared}: ${err.message} — every record loads whole instead`);
      shared = null;
    }
  }

  // Each part is asked for once, by whichever of its records gets there first.
  const parts = new Map();
  const bootRecord = (at, id) => {
    const name = `part-${Math.floor(at / boot.per_part)}.json`;
    if (!parts.has(name)) parts.set(name, getJSON(new URL(`${boot.dir}${name}`, dataBase)));
    return parts.get(name).then((part) => {
      if (!Object.hasOwn(part, id)) throw new Error(`not in ${boot.dir}${name}`);
      return rehydrate(part[id], shared);
    });
  };

  // The shared KTX2 loader (T-2582), so a KHR_texture_basisu derivative decodes.
  const loader = registerKTX2(new GLTFLoader());
  // T-2464: houses built on one kit embed the same maps; decode each once.
  // T-2598: a phone keeps each picture's encoded bytes, so texture residency can
  // decode one again after the decoded copy was closed (texture-residency.js).
  const sharedImages = shareImageSources(loader, { keepEncoded: keepEncodedImages });
  const registry = new Map();
  let bytes = 0;
  // Keep compressed bytes, not a parsed scene whose materials batching may modify.
  // Only opt-in LOD records use this cache; a light boot never fetches the full GLB.
  // T-2548: a phone does not bank them (`keepAssetBytes: false`). It boots `light`
  // and almost never switches, and on 1904 the bank was the whole 32.6 MB Glessner
  // light GLB held for a switch that, when it comes, the HTTP cache answers.
  const assetBytes = new Map();
  const bank = (record) => keepAssetBytes && hasInspectionLod(record);
  // T-2597: GLB bytes fetched and not yet parsed, now and at their most — the pile
  // a pool would bound. The harness reads the peak as `bootPool`.
  const held = { bytes: 0, assets: 0, peakBytes: 0, peakAssets: 0 };
  async function loadDetailAsset(record, level) {
    const assetUrl = detailAssetUrl(record, level, bases);
    const key = String(assetUrl);
    let got = bank(record) ? assetBytes.get(key) : null;
    let holding = 0;
    if (!got) {
      got = await fetchAsset(assetUrl);
      bytes += got.buffer.byteLength;
      holding = got.buffer.byteLength;
      held.bytes += holding;
      held.assets += 1;
      held.peakBytes = Math.max(held.peakBytes, held.bytes);
      held.peakAssets = Math.max(held.peakAssets, held.assets);
    }
    try {
      const header = glbHeader(got.buffer);
      if (header?.extensionsRequired?.includes('EXT_meshopt_compression')) {
        loader.setMeshoptDecoder(await loadMeshoptDecoder());
      }
      // T-3232: GLTFLoader resolves a buffer's URI by appending it to this path, so
      // it is the GLB's directory, not its URL: a published GLB that shares a texture
      // sheet names it as `sheets/<hash>.ktx2` beside it (tools/share_glb_sheets.mjs).
      const gltf = await new Promise((resolve, reject) => {
        loader.parse(got.buffer, new URL('.', assetUrl).href, resolve, reject);
      });
      // T-2464: nothing here reads the parser once the scene is built, and it holds
      // the file's whole binary chunk and every buffer view it sliced (embedded
      // images included) for as long as the building is loaded. Let it go.
      gltf.parser = null;
      // A 200 response can still contain a damaged GLB. Bank only bytes that
      // decoded, and evict any failed cached parse so retry can fetch repaired data.
      if (bank(record)) assetBytes.set(key, got);
      return { gltf, assetUrl: key, assetDetail: level,
        assetIsPlaceholder: !!header?.asset?.extras?.placeholder,
        assetRetried: got.retried, loadFailed: null };
    } catch (error) {
      assetBytes.delete(key);
      throw error;
    } finally {
      if (holding) { held.bytes -= holding; held.assets -= 1; }
    }
  }

  let completed = 0;
  onProgress(0, entries.length);
  const loadOne = async ({ id, sidecar: sidecarPath, version: chosen = null }, at) => {
    const sidecarUrl = new URL(sidecarPath ?? `sidecars/${year}/${id}.json`, dataBase);
    let sidecar;
    try {
      // A structure pointed at a version (`chosen`) reads its version file whole.
      sidecar = shared && !chosen ? await bootRecord(at, id) : await getJSON(sidecarUrl);
    } catch (err) {
      problems.push(`sidecar ${id}: ${err.message}`);
      return;
    }
    if (sidecar.id !== id) {
      problems.push(`sidecar ${id}: declares id '${sidecar.id}' — index and file disagree`);
    }
    if (sidecar.review_required) {
      // AGENTS.md, owner ruling 2026-10-16: retain the review annotation;
      // it does not block scene release and must not pass unremarked.
      problems.push(`${id}: review_required is set — review annotation retained; this flag does not block scene release`);
    }

    /**
     * A sidecar with NO asset is not a bake that failed to arrive — it is a
     * record whose geometry is drawn by another layer, and `drawn_by` names
     * which. The estray pen is the first: a pound is a fence, and it is drawn
     * by `enclosures.js` out of `data/enclosures/estray_pen.json` (T-0051,
     * docs/LIBERTIES.md L60). The record still loads, because the card a
     * visitor opens is still compiled from it; what it does not do is fetch a
     * GLB that does not exist and report the 404 as a problem.
     */
    if (!sidecar.asset) {
      registry.set(id, {
        id,
        sidecar,
        gltf: null,
        drawnBy: sidecar.drawn_by ?? null,
        assetIsPlaceholder: false,
        /** T-1126: why this record's geometry is not in the scene, or null if
         *  nothing went wrong. A record drawn by another layer is not a failure
         *  and does not set it. */
        loadFailed: null,
        assetRetried: false,
        assetUrl: null,
        sidecarUrl: String(sidecarUrl),
        /** T-1727: the versions-index row this entry was loaded from, or null for the
         *  default. The card and the HUD name it; nothing else reads it. */
        version: chosen,
        instanceId: null,
        node: null,
      });
      if (!sidecar.drawn_by) {
        problems.push(`${id}: the sidecar names no asset and no layer that draws `
          + 'it — nothing of this structure is in the scene');
      }
      return;
    }

    const assetRecord = { id, sidecar, version: chosen };
    const assetUrl = detailAssetUrl(assetRecord, detail, bases);
    let gltf = null;
    /**
     * Is the shape you are looking at a bake from the record, or a stand-in?
     *
     * The GLB says so about itself (`asset.extras.placeholder`) and nothing else
     * can: the sidecar is compiled from `data/` alone and never opens a mesh, so
     * a record cannot know which of its bakes is real. The fact is therefore
     * carried from the file it is a fact about to the card that shows it, rather
     * than routed through a sidecar field the compiler would have to invent.
     */
    let assetIsPlaceholder = false;
    let loadFailed = null;
    let assetRetried = false;
    try {
      const got = await loadDetailAsset(assetRecord, detail);
      gltf = got.gltf;
      assetRetried = got.assetRetried;
      if (got.assetIsPlaceholder) {
        assetIsPlaceholder = true;
        problems.push(`${id}: rendering a PLACEHOLDER asset (${sidecar.asset}) — `
          + 'massing only, not a bake');
      }
    } catch (err) {
      /**
       * NAME THE STRUCTURE, not just the file — T-1126. This line used to read
       * `asset <path>: <error>`, which is the one fact a reader of the problem
       * list cannot act on: it says a bake is missing without saying which
       * building is therefore absent from the town, and every layer downstream
       * that hangs furniture on that building goes on hanging it.
       */
      loadFailed = err.message;
      problems.push(`${id}: its asset ${sidecar.asset} did not load (${err.message}) — `
        + 'the building is NOT in the scene');
    }
    if (assetRetried) {
      problems.push(`${id}: its asset ${sidecar.asset} failed on the first ask and `
        + 'loaded on the second — a dropped request, not a bad file');
    }

    registry.set(id, {
      id,
      sidecar,
      gltf,
      drawnBy: null,
      assetIsPlaceholder,
      loadFailed,
      assetRetried,
      assetUrl: String(assetUrl),
      assetDetail: detail,
      sidecarUrl: String(sidecarUrl),
      /** T-1727: the versions-index row this entry was loaded from, or null. */
      version: chosen,
      /** filled in by buildings.js once the node is in the batch */
      instanceId: null,
      node: null,
    });
  };

  // T-2597: unbounded unless the address asks for a pool — see BOOT_POOL.
  await pooled(entries, pool, async (row, at) => {
    try { await loadOne(row, at); } finally { onProgress(++completed, entries.length); }
  });
  return { year, scene, datum, registry, problems, get bytes() { return bytes; },
    index, versionState, loadDetailAsset, sharedImages: sharedImages.stats,
    /** T-2548: how many GLBs are banked for a detail switch — the harness reads it. */
    get bankedAssets() { return assetBytes.size; },
    /** T-2597: the pool size, and the most GLB bytes (and files) held unparsed at once. */
    get bootPool() {
      return { size: Number.isFinite(pool) ? pool : 0,
        peakBytes: held.peakBytes, peakAssets: held.peakAssets };
    } };
}
