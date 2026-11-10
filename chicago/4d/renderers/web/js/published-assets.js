/** Publication addresses only: logical assets, geometry, LOD and sidecars stay unchanged. */
export const ASSET_ALIAS_SCHEMA = 1;

/** Self contained so the native pack writer embeds this exact validator in the classic worker. */
export function createAssetAliasContract() {
  const hex = /^[a-f0-9]{64}$/;
  const pathOK = (p) => typeof p === 'string' && !p.includes('..')
    && /^(?:data\/gltf\/[A-Za-z0-9_./-]+\.(?:glb|ktx2)|data\/prebuilt\/[0-9]{4}\/[A-Za-z0-9_.-]+\.bin\.gz)$/.test(p)
    && !p.includes('//');
  const input = (aliases) => JSON.stringify(Object.keys(aliases).sort().map((rel) => {
    const r = aliases[rel]; return [rel, r.source, r.sha256, r.bytes];
  }));
  function validate(catalogue, root) {
    root = new URL(root);
    if (!catalogue || catalogue.schema !== 1 || catalogue.scope !== '/4d/dev/'
      || catalogue.productionScope !== '/4d/' || root.pathname !== catalogue.scope
      || !hex.test(catalogue.id) || !catalogue.aliases || Array.isArray(catalogue.aliases)
      || typeof catalogue.aliases !== 'object') throw new Error('Invalid publication alias catalogue');
    const aliases = Object.create(null);
    for (const [rel, r] of Object.entries(catalogue.aliases)) {
      if (!pathOK(rel) || !r || r.source !== `/4d/${rel}` || !hex.test(r.sha256)
        || !Number.isSafeInteger(r.bytes) || r.bytes < 0) throw new Error('Invalid publication alias entry');
      const source = new URL(r.source, root);
      if (source.origin !== root.origin || source.pathname !== r.source || source.search || source.hash)
        throw new Error('Publication alias must be the exact same-origin production counterpart');
      aliases[rel] = Object.freeze({ source: r.source, sha256: r.sha256, bytes: r.bytes });
    }
    return Object.freeze({ schema: 1, scope: catalogue.scope, productionScope: catalogue.productionScope,
      id: catalogue.id, aliases: Object.freeze(aliases) });
  }
  return Object.freeze({ validate, input, pathOK });
}

const contract = createAssetAliasContract();
export const validateAssetAliases = contract.validate;
export const assetAliasIdInput = contract.input;
const pending = new Map();
export const hasPublishedAssetPointer = (doc = globalThis.document) => !!doc?.querySelector?.('meta[name="c4d-asset-aliases"]');
const hexOf = (bytes) => [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, '0')).join('');
export async function assetSha256(bytes) { return hexOf(await crypto.subtle.digest('SHA-256', bytes)); }

/** No pointer means no request: source, workers and old published mirrors retain identity. */
export async function publishedAssetCatalogue({ document: doc = globalThis.document, fetchImpl = globalThis.fetch } = {}) {
  const meta = doc?.querySelector?.('meta[name="c4d-asset-aliases"]');
  if (!meta) return null;
  const expected = meta.getAttribute('data-sha256');
  const url = new URL(meta.getAttribute('content'), doc.baseURI);
  const root = new URL('.', url);
  if (!/^[a-f0-9]{64}$/.test(expected) || url.pathname !== `${root.pathname}asset-aliases.${expected}.json`
    || url.search || url.hash || url.origin !== new URL(doc.baseURI).origin)
    throw new Error('Invalid publication alias pointer');
  const key = `${url.href} ${expected}`;
  if (!pending.has(key)) {
    const request = (async () => {
    const response = await fetchImpl(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`Publication alias catalogue: ${response.status}`);
    const catalogue = validateAssetAliases(await response.json(), root);
    if (catalogue.id !== expected || await assetSha256(new TextEncoder().encode(assetAliasIdInput(catalogue.aliases))) !== expected)
      throw new Error('Publication alias catalogue digest mismatch');
    return { catalogue, root };
    })();
    pending.set(key, request);
    request.catch(() => { if (pending.get(key) === request) pending.delete(key); });
  }
  return pending.get(key);
}

export async function publishedAssetAddress(input, options) {
  const logical = new URL(input);
  const configured = await publishedAssetCatalogue(options);
  if (!configured || logical.origin !== configured.root.origin || !logical.pathname.startsWith(configured.root.pathname))
    return { logical, source: logical, alias: null };
  const rel = logical.pathname.slice(configured.root.pathname.length);
  const alias = configured.catalogue.aliases[rel];
  if (!alias) return { logical, source: logical, alias: null };
  const source = new URL(alias.source, configured.root);
  source.search = logical.search;
  source.searchParams.set('c4d-asset-alias', alias.sha256);
  // An older production worker may control DEV before its own pack is installed.
  // Its existing pack-download bypass prevents old production bytes substituting.
  source.searchParams.set('c4d-pack', alias.sha256);
  return { logical, source, alias };
}

/** Consume once, validate the original buffer, and hand it to the native parser without a copy. */
export async function fetchPublishedAssetBytes(input, options = {}, environment) {
  const { source, alias } = hasPublishedAssetPointer(environment?.document)
    ? await publishedAssetAddress(input, environment) : { source: input, alias: null };
  const response = await (environment?.fetchImpl ?? fetch)(source, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  if (alias && (response.status !== 200 || response.headers.has('content-range')))
    throw new Error('Publication aliases require a complete response');
  const bytes = await response.arrayBuffer();
  if (alias && (bytes.byteLength !== alias.bytes || await assetSha256(bytes) !== alias.sha256))
    throw new Error('Published asset differs from its exact alias catalogue');
  return bytes;
}

/** The native shared-sheet layout: a complete external KTX2 buffer used only by images. */
export function completeTextureBuffer(json, bufferIndex) {
  const buffer = json.buffers?.[bufferIndex];
  if (!buffer || !Number.isSafeInteger(buffer.byteLength) || buffer.byteLength <= 0) return false;
  const views = new Set((json.bufferViews || []).flatMap((v, index) => v.buffer === bufferIndex ? [index] : []));
  if (!views.size) return false;
  for (const index of views) {
    const view = json.bufferViews[index];
    const images = (json.images || []).filter((i) => i.bufferView === index);
    if ((view.byteOffset ?? 0) !== 0 || view.byteLength !== buffer.byteLength || view.byteStride !== undefined
      || view.target !== undefined || !images.length || images.some((i) => i.mimeType !== 'image/ktx2')) return false;
  }
  let imageOnly = true;
  const visit = (value, location = '') => {
    if (!value || typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      const at = location ? `${location}/${key}` : key;
      if (key === 'bufferView' && views.has(child) && !/^images\/[0-9]+\/bufferView$/.test(at)) imageOnly = false;
      if (key === 'buffer' && child === bufferIndex && !/^bufferViews\/[0-9]+\/buffer$/.test(at)) imageOnly = false;
      visit(child, at);
    }
  };
  visit(json);
  return imageOnly;
}

/** Official GLTFLoader extension boundary; embedded/geometry buffers keep the native path. */
export function registerPublishedTextureBuffers(loader) {
  const pendingBuffers = new Map();
  loader.register((parser) => ({
    name: 'C4D_publication_texture_buffers',
    loadBufferView(index) {
      const view = parser.json.bufferViews?.[index];
      const buffer = parser.json.buffers?.[view?.buffer];
      if (!buffer?.uri || !hasPublishedAssetPointer()) return null;
      const logical = new URL(buffer.uri, parser.options.path);
      // General external geometry is deliberately outside this contract.
      if (!/^\/4d\/dev\/data\/gltf\/sheets\/[a-f0-9]{16}\.ktx2$/.test(logical.pathname)) return null;
      return publishedAssetAddress(logical).then(({ alias, source }) => {
        if (!alias) return parser.loadBufferView(index);
        if (!completeTextureBuffer(parser.json, view.buffer) || buffer.byteLength !== alias.bytes)
          throw new Error('Publication texture buffer must be a complete image-only KTX2 sheet');
        const key = source.href;
        let bytes = pendingBuffers.get(key);
        if (!bytes) {
          bytes = fetchPublishedAssetBytes(logical);
          pendingBuffers.set(key, bytes);
          const clear = () => { if (pendingBuffers.get(key) === bytes) pendingBuffers.delete(key); };
          bytes.then(clear, clear);
        }
        // The only allowed view covers the complete buffer. No geometry/offset
        // rewrite or copy: native image Source interning sees the same bytes.
        return bytes;
      });
    },
  }));
  return loader;
}

/** An installed pack may fetch a source URL, but its cache key remains the logical DEV URL. */
export async function verifiedPackAliases(pack, root) {
  if (!pack.assetAliases) return null;
  const catalogue = validateAssetAliases(pack.assetAliases, root);
  if (await assetSha256(new TextEncoder().encode(assetAliasIdInput(catalogue.aliases))) !== catalogue.id)
    throw new Error('Pack publication alias digest mismatch');
  const entries = new Map(pack.files.map((row) => [row[0], row]));
  for (const [rel, r] of Object.entries(catalogue.aliases)) {
    const entry = entries.get(rel);
    if (entry && (entry[1] !== r.sha256.slice(0, 16) || entry[2] !== r.bytes))
      throw new Error('Pack entry disagrees with publication alias');
  }
  return catalogue;
}
