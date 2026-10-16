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
const SCOPE = new URL(self.registration.scope);
const PREFIX = `c4d-pack ${SCOPE.pathname} `;
const MANIFEST = '__pack__.json';

let index = null;   // Map rel -> { years: [year], net: bool }
let loading = null;

function relOf(url) {
  const u = new URL(url);
  if (u.origin !== SCOPE.origin || !u.pathname.startsWith(SCOPE.pathname)) return null;
  // year-pack.js downloading a pack: always the network, never the pack it replaces.
  if (u.searchParams.has('c4d-pack')) return null;
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
    const net = new Set(pack.network_first || []);
    for (const [rel] of pack.files) {
      const hit = map.get(rel);
      if (hit) hit.years.push(year);
      else map.set(rel, { years: [year], net: net.has(rel) });
    }
  }
  index = map;
  loading = null;
  return map;
}

async function fromPack(hit, key) {
  for (const year of hit.years) {
    const res = await (await caches.open(PREFIX + year)).match(key);
    if (res) return res;
  }
  return null;
}

async function serve(request, rel) {
  const map = index || await (loading ||= loadIndex());
  const hit = map.get(rel);
  if (!hit) return fetch(request);
  const key = new URL(rel, SCOPE).href;
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
  if (request.method !== 'GET') return;
  const rel = relOf(request.url);
  if (rel === null) return;
  if (index && !index.has(rel)) return;
  event.respondWith(serve(request, rel));
});
