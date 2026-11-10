/* 4D Chicago — the year pack's service worker (T-2561).
 *
 * Published at the root of the site (`/4d/sw.js`, and `/4d/dev/sw.js` on the dev
 * preview) by tools/write_year_packs.mjs, so its scope is the whole app: the year
 * doors (`/4d/1835/`), the renderer (`/4d/walk/`) and the data (`/4d/data/`).
 *
 * It is registered only when a visitor asks to keep a year on the device
 * (renderers/web/js/year-pack.js); a visitor who never does has no worker at all.
 * The page does the downloading — into Cache Storage, file by file, each checked
 * against the hash in `packs/<year>.json` — because a page can run as long as a
 * big download takes and a worker's event cannot. This file only SERVES:
 *
 *   - a request for a file in an installed pack is answered from the pack;
 *   - `build.json` and the changelog go to the network first, so What's-New is
 *     never stale while online, and fall back to the pack offline;
 *   - anything else — a download marked `?c4d-pack=`, a file in no pack, anything
 *     outside this worker's own scope — is not touched at all (no respondWith), so the network behaves as if no worker
 *     were installed.
 *
 * Production and the dev preview never serve each other's packs: each cache is
 * named for the scope that wrote it, and a request is looked up only under this
 * worker's own scope. The production worker's scope (/4d/) contains /4d/dev/,
 * but /4d/dev/ paths are not in its index, so it passes them through, and a
 * dev-preview visitor who keeps a year gets /4d/dev/sw.js, the narrower scope,
 * which the browser prefers.
 *
 * THE KILL SWITCH. When `offline/sw-off` exists, publish ships this file
 * with KILL = true. Browsers re-fetch a worker's script on navigation, so the
 * next visit installs the killed worker, which deletes its packs, unregisters
 * itself and reloads the open pages from the network. The page module reads the
 * same switch from build.json and does the same thing from its side.
 */
'use strict';
const KILL = false;
// tools/write_year_packs.mjs embeds the shared engine-neutral contract here.
const ASSET_ALIAS_CONTRACT = null;
const SCOPE = new URL(self.registration.scope);
const PREFIX = `c4d-pack ${SCOPE.pathname} `;
const MANIFEST = '__pack__.json';

let index = null;   // Map rel -> { years: [year], net: bool }
let loading = null;

function relOf(url) {
  const u = new URL(url);
  if (u.origin !== SCOPE.origin) return null;
  // Runtime aliases carry the legacy production-worker network bypass as well.
  // Only a hash-qualified DEV alias can override it after exact catalogue lookup.
  const runtimeAlias = /^[a-f0-9]{64}$/.test(u.searchParams.get('c4d-asset-alias') || '')
    && u.searchParams.get('c4d-pack') === u.searchParams.get('c4d-asset-alias');
  if (u.searchParams.has('c4d-pack') && !runtimeAlias) return null;
  if (!u.pathname.startsWith(SCOPE.pathname)) {
    const hash = u.searchParams.get('c4d-asset-alias');
    const key = `@alias ${u.pathname} ${hash}`;
    // A cold worker must load its installed catalogues before deciding. Only
    // exact same-origin production counterparts with a full digest reach that
    // lookup; an unknown candidate still takes the ordinary network path.
    const relative = u.pathname.startsWith('/4d/') ? u.pathname.slice(4) : '';
    return SCOPE.pathname === '/4d/dev/' && /^[a-f0-9]{64}$/.test(hash || '')
      && ASSET_ALIAS_CONTRACT?.pathOK(relative) ? key : null;
  }
  let rel;
  try { rel = decodeURIComponent(u.pathname.slice(SCOPE.pathname.length)); } catch { return null; }
  return rel === '' || rel.endsWith('/') ? `${rel}index.html` : rel;
}

async function loadIndex() {
  const map = new Map();
  for (const name of await caches.keys()) {
    if (!name.startsWith(PREFIX)) continue;
    const year = name.slice(PREFIX.length);
    const res = await (await caches.open(name)).match(new URL(MANIFEST, SCOPE).href);
    if (!res) continue;   // a download that never finished: nothing of it is served
    const pack = await res.json();
    let aliases = null;
    if (pack.assetAliases) {
      if (!ASSET_ALIAS_CONTRACT) throw new Error('Publication alias worker was not generated');
      const catalogue = ASSET_ALIAS_CONTRACT.validate(pack.assetAliases, SCOPE);
      const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ASSET_ALIAS_CONTRACT.input(catalogue.aliases)));
      const hash = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
      if (hash !== catalogue.id) throw new Error('Installed publication alias catalogue digest mismatch');
      aliases = catalogue.aliases;
    }
    const net = new Set(pack.network_first || []);
    for (const [rel, hash, bytes] of pack.files) {
      const hit = map.get(rel);
      if (hit) hit.years.push(year);
      else map.set(rel, { years: [year], net: net.has(rel) });
      const alias = aliases?.[rel];
      if (alias) {
        if (alias.sha256.slice(0, 16) !== hash || alias.bytes !== bytes)
          throw new Error('Installed pack disagrees with publication alias');
        const logical = map.get(rel);
        if (!logical.sha256) { logical.sha256 = alias.sha256; logical.bytes = bytes; }
        const key = `@alias ${alias.source} ${alias.sha256}`;
        const shared = map.get(key);
        if (shared) shared.years.push(year);
        else map.set(key, { years: [year], net: false, rel, sha256: alias.sha256, bytes });
      }
    }
  }
  index = map;
  loading = null;
  return map;
}

async function fromPack(hit, key) {
  for (const year of hit.years) {
    const res = await (await caches.open(PREFIX + year)).match(key);
    if (res) {
      if (hit.sha256) {
        if (res.status !== 200 || res.headers.has('content-range')) continue;
        const body = await res.clone().arrayBuffer();
        if (body.byteLength !== hit.bytes) continue;
        const digest = await crypto.subtle.digest('SHA-256', body);
        const hash = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
        if (hash !== hit.sha256) continue;
      }
      return res;
    }
  }
  return null;
}

async function serve(request, rel) {
  const map = index || await (loading ||= loadIndex());
  const hit = map.get(rel);
  if (!hit) return fetch(request);
  const key = new URL(hit.rel || rel, SCOPE).href;
  if (hit.net) {
    try {
      const res = await fetch(request);
      if (res.ok) return res;
    } catch { /* offline: the pack's copy below */ }
  }
  return (await fromPack(hit, key)) || fetch(request);
}

async function kill() {
  for (const name of await caches.keys()) if (name.startsWith(PREFIX)) await caches.delete(name);
  await self.registration.unregister();
  for (const client of await self.clients.matchAll({ type: 'window' })) client.navigate(client.url);
}

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil(KILL ? kill() : self.clients.claim().then(() => loadIndex()));
});
self.addEventListener('message', (event) => {
  // year-pack.js says so after it installs, updates or removes a pack.
  if (event.data?.type === 'pack-changed') event.waitUntil(loadIndex());
});
self.addEventListener('fetch', (event) => {
  if (KILL) return;
  const request = event.request;
  if (request.method !== 'GET' || request.headers.has('range')) return;
  const rel = relOf(request.url);
  if (rel === null) return;
  if (index && !index.has(rel)) return;
  event.respondWith(serve(request, rel));
});
