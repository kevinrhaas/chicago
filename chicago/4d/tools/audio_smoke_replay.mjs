// Replay exactly the published audio bytes at localhost without widening bucket
// CORS. The bake smoke checks out only tools/ and receives a published artifact;
// it must not need unpublished renderers/audio files merely to boot.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { hostedCatalog, ROOT } from './audio_hosting.mjs';

const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const mime = { '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.mp3': 'audio/mpeg' };

export function createAudioReplay({ site, root = ROOT, fetcher = globalThis.fetch } = {}) {
  const policy = read(path.join(root, 'tools/audio-hosting.json'));
  const base = new URL(policy.public_base);
  if (policy.version !== 1 || base.protocol !== 'https:' || base.username || base.password
    || base.search || base.hash || !base.pathname.endsWith('/')) throw Error('Invalid audio replay host policy');
  const receipt = read(path.join(root, 'tools/audio-host-verification.json'));
  if (!receipt.complete || !Array.isArray(receipt.errors) || receipt.errors.length
    || receipt.public_base !== base.href || receipt.origin !== policy.origin)
    throw Error('Audio replay receipt does not match host policy');
  const verified = new Map(receipt.verified.map(row => [row.key, row]));
  const catalog = read(path.join(site, 'walk/audio/catalog.json'));
  if (catalog.hosting?.public_base !== base.href || catalog.hosting?.scope !== policy.scope)
    throw Error('Published audio replay catalogue names a different host');
  const sourceDir = path.join(root, 'renderers/web/audio');
  const local = fs.existsSync(path.join(sourceDir, 'catalog.json')) ? hostedCatalog({ root }) : null;
  if (local && JSON.stringify(local.catalog) !== JSON.stringify(catalog))
    throw Error('Published audio replay catalogue differs from source');
  const items = new Map();
  let index = 0;
  for (const asset of catalog.assets) for (const field of asset.kind === 'music' ? ['opus', 'aac'] : ['url']) {
    const url = asset[field], expected = asset.kind === 'music' ? asset.delivery[field] : asset.delivery;
    const ext = typeof url === 'string' ? path.extname(new URL(url).pathname) : '';
    if (!/^[a-f0-9]{64}$/.test(expected?.sha256 ?? '') || !mime[ext]
      || !Number.isSafeInteger(expected?.bytes) || expected.bytes <= 0)
      throw Error('Invalid audio replay integrity metadata');
    const key = `media/${expected.sha256}${ext}`;
    if (url !== new URL(key, base).href || verified.get(key)?.bytes !== expected.bytes)
      throw Error('Audio replay URL/bytes were not verified on the configured host');
    items.set(url, { ...expected, contentType: mime[ext], file: local ? path.join(sourceDir, local.media[index]) : null });
    index++;
  }
  const cache = new Map();
  return {
    size: items.size,
    mode: local ? 'verified local media replay' : 'verified hosted media replay for sparse artifact',
    has: url => items.has(url),
    async get(url) {
      const entry = items.get(url);
      if (!entry) throw Error('Audio replay refused an unlisted URL');
      if (!cache.has(url)) cache.set(url, (async () => {
        let body;
        if (entry.file) body = fs.readFileSync(entry.file);
        else {
          const response = await fetcher(url, {
            redirect: 'error', credentials: 'omit', signal: AbortSignal.timeout(30000),
            headers: { 'User-Agent': 'Mozilla/5.0 Chicago4D-AudioVerifier/1.0', Origin: policy.origin },
          });
          if (response.status !== 200 || !response.body) throw Error(`Audio replay HTTP ${response.status}`);
          const chunks = []; let bytes = 0;
          for await (const chunk of response.body) {
            bytes += chunk.length;
            if (bytes > entry.bytes) throw Error('Audio replay body exceeds verified size');
            chunks.push(Buffer.from(chunk));
          }
          body = Buffer.concat(chunks);
        }
        if (body.length !== entry.bytes || createHash('sha256').update(body).digest('hex') !== entry.sha256)
          throw Error('Audio replay bytes differ from verified delivery');
        return { body, contentType: entry.contentType };
      })());
      return cache.get(url);
    },
  };
}

// T-3579: the narration index is the one hosted file the published app reads that
// cannot be replayed from verified bytes. The voicer rewrites it in place (no-cache;
// docs/AUDIO.md § Narration), so there is no receipt to hold it to, and the bucket
// refuses localhost, so every boot logged a CORS console.error and failed part 15's
// zero-page-errors check on both viewports. The smoke checks no narration, so it
// stands in the index as an EMPTY one — the app's own "a jaunt not yet voiced" path
// (js/narration.js: nothing offered, nothing fails) — rather than widening bucket
// CORS or trusting unverified bytes. The path is js/narration.js's INDEX_PATH; it is
// written here because the bake smoke checks out only tools/.
export const NARRATION_INDEX_PATH = 'narration/index.json';
export const EMPTY_NARRATION_INDEX = Object.freeze({ version: 1, clips: Object.freeze({}) });

export function narrationIndexUrl({ root = ROOT } = {}) {
  const policy = read(path.join(root, 'tools/audio-hosting.json'));
  return new URL(NARRATION_INDEX_PATH, policy.public_base).href;
}

/** Route the hosted narration index on a Playwright browser context to an empty index. */
export async function standInNarrationIndex(context, { origin, root = ROOT } = {}) {
  const url = narrationIndexUrl({ root });
  await context.route(u => u.href.split('?')[0] === url, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': origin, 'Cache-Control': 'no-store' },
    body: JSON.stringify(EMPTY_NARRATION_INDEX),
  }));
  return url;
}
