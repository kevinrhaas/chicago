/** T-2561 — keep a year on this device.
 *
 * The welcome's small "Offline copy" control (quieted by T-2947). On a tap it registers the
 * site's service worker (`../sw.js`, scope `../`: see offline/sw.js) and
 * downloads the year's pack (`../packs/<year>.json`, written by
 * tools/write_year_packs.mjs) into Cache Storage, checking every file against
 * the hash in the pack. From then on the year boots from the device, with or
 * without a network.
 *
 * Updates fetch only what changed: on every later visit, online, the installed
 * pack's id is compared with the published one and the difference — and only
 * the difference — is downloaded in the background (`planUpdate`). The worker
 * keeps serving the installed files until the new pack is complete.
 *
 * Kill switch: `"sw_off": true` in build.json (publish.sh writes it when
 * offline/sw-off exists) makes this module unregister the worker and
 * delete the packs. The published sw.js carries the same switch from its side.
 *
 * Nothing here runs in the source tree (renderers/web/ served directly): there
 * is no sw.js or pack beside it. A visitor who never taps the control gets no
 * worker at all, and every failure here is shown on the control, never thrown.
 */
import { iconSvg } from './menu-icons.js';

const MANIFEST = '__pack__.json';
const PARALLEL = 6;
const RETRY_MS = 8000;

/** What an update has to fetch and what it can delete; `have` (the rels the cache holds) refetches
 *  an entry the browser evicted. tools/write_year_packs.mjs --self-test tests this function. */
export function planUpdate(old, next, have = null) {
  const had = new Map((old?.files || []).map(([rel, hash]) => [rel, hash]));
  const want = new Set(next.files.map(([rel]) => rel));
  return {
    fetch: next.files.filter(([rel, hash]) => had.get(rel) !== hash || (have && !have.has(rel))),
    drop: [...had.keys()].filter((rel) => !want.has(rel)),
  };
}

const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
const mb = (n) => (n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : `${Math.max(0.1, n / 1e6).toFixed(n >= 1e8 ? 0 : 1)} MB`);

export function createYearPack({ year, mount, base = document.baseURI, dev = false }) {
  const root = new URL('../', base);                       // the site root: /4d/ or /4d/dev/
  const cacheName = `c4d-pack ${root.pathname} ${year}`;   // sw.js names it the same way
  const supported = !dev && !!mount && 'serviceWorker' in navigator && 'caches' in globalThis
    && globalThis.isSecureContext !== false && !/[?&]nosw\b/.test(location.search);
  const state = { year, supported, status: 'idle', installed: null, published: null, last: null, error: null };
  let busy = null;

  const url = (rel) => new URL(rel, root).href;
  const registration = () => navigator.serviceWorker.getRegistration(root.href).catch(() => null);
  const tellWorker = async () => {
    const reg = await registration();
    (reg?.active || reg?.waiting || reg?.installing)?.postMessage({ type: 'pack-changed' });
  };

  async function installedPack() {
    if (!(await caches.has(cacheName))) return null;
    const res = await (await caches.open(cacheName)).match(url(MANIFEST));
    return res ? res.json() : null;
  }

  async function digest(bytes) {
    return hex(await crypto.subtle.digest('SHA-256', bytes)).slice(0, 16);
  }

  /** The published list. Cache-busted, so a CDN copy older than the files it lists cannot answer. */
  async function publishedPack() {
    const res = await fetch(url(`packs/${year}.json?t=${Date.now()}`), { cache: 'no-store' });
    if (!res.ok) throw new Error(`no pack for ${year} (${res.status})`);
    return res.json();
  }

  /** Fetch what `next` adds over the installed pack and over `put`, the files this download
   *  already stored (rel -> hash), so a retry picks up where the last attempt stopped. */
  async function fetchFiles(next, old, put, cache, onProgress) {
    const base = new Map((old?.files || []).map(([rel, hash]) => [rel, hash]));
    for (const [rel, hash] of put) base.set(rel, hash);
    const have = new Set((await cache.keys()).map((r) => decodeURIComponent(new URL(r.url).pathname.slice(root.pathname.length))));
    const plan = planUpdate({ files: [...base] }, next, have);
    const total = plan.fetch.reduce((s, f) => s + f[2], 0);
    let done = 0, bytes = 0, failed = null;
    const queue = plan.fetch.slice();
    onProgress({ done, count: plan.fetch.length, bytes, total });
    async function worker() {
      while (queue.length && !failed) {
        const [rel, hash, size] = queue.shift();
        try {
          // Marked, so the worker never answers it from the pack being replaced
          // (sw.js passes `c4d-pack` requests straight to the network).
          const got = await fetch(`${url(rel)}?c4d-pack=${hash}`, { cache: 'no-store' });
          if (!got.ok) throw new Error(`${rel}: ${got.status}`);
          const body = await got.arrayBuffer();
          // A file that does not match its entry is a site mid-deploy: stop, and let
          // download() read the list again.
          if (await digest(body) !== hash) throw Object.assign(new Error(`${rel} changed while downloading`), { stale: true, rel });
          await cache.put(url(rel), new Response(body, { headers: {
            'content-type': got.headers.get('content-type') || 'application/octet-stream' } }));
          put.set(rel, hash);
          done += 1; bytes += size;
          onProgress({ done, count: plan.fetch.length, bytes, total });
        } catch (e) { failed = e; }
      }
    }
    await Promise.all(Array.from({ length: PARALLEL }, worker));
    if (failed) throw failed;
    return { plan, total };
  }

  /** Download the year's pack, or the part of it that changed. Resolves to what it fetched.
   *  T-2947: a deploy that lands mid-download changes files under it. The list is read
   *  again and the download carries on from what it already holds: a new list is followed
   *  at once, the same list is given a moment for the CDN to catch up. Three tries. */
  async function download({ onProgress = () => {} } = {}) {
    const cache = await caches.open(cacheName);
    const old = await installedPack();
    const put = new Map();
    let next = await publishedPack();
    let got = null;
    for (let attempt = 1; !got; attempt += 1) {
      try {
        got = await fetchFiles(next, old, put, cache, onProgress);
      } catch (e) {
        if (!e.stale) throw e;
        if (attempt >= 3) throw new Error('the site is mid-update; try again in a few minutes');
        const again = await publishedPack();
        if (again.id === next.id) await new Promise((r) => setTimeout(r, RETRY_MS));
        next = again;
      }
    }
    const { plan, total } = got;
    for (const rel of plan.drop) await cache.delete(url(rel));
    // The pack's list goes in LAST: the worker serves nothing of a year until it is complete.
    await cache.put(url(MANIFEST), new Response(JSON.stringify(next), { headers: { 'content-type': 'application/json' } }));
    await tellWorker();
    state.installed = { id: next.id, count: next.count, bytes: next.bytes };
    state.last = { fetched: put.size, fetchedBytes: total, dropped: plan.drop.length, id: next.id };
    return state.last;
  }

  async function register() {
    const reg = await navigator.serviceWorker.register(url('sw.js'), { scope: root.href });
    if (!reg.active) {
      await new Promise((resolve) => {
        const w = reg.installing || reg.waiting;
        if (!w) { resolve(); return; }
        w.addEventListener('statechange', () => { if (w.state === 'activated' || w.state === 'redundant') resolve(); });
        setTimeout(resolve, 10_000);
      });
    }
    return reg;
  }

  /** Unregister the worker and delete every pack this scope wrote. */
  async function remove() {
    const reg = await registration();
    for (const name of await caches.keys()) if (name.startsWith(`c4d-pack ${root.pathname} `)) await caches.delete(name);
    if (reg) await reg.unregister();
    state.installed = null;
    state.status = 'idle';
    render();
  }

  async function install() {
    if (!supported || busy) return busy;
    if (state.status === 'kept') return state.last;
    state.status = 'downloading'; state.error = null; render({ done: 0, bytes: 0, total: state.published?.bytes || 0 });
    busy = (async () => {
      try {
        await register();
        await download({ onProgress: render });
        try { await navigator.storage?.persist?.(); } catch { /* a refusal still keeps the pack */ }
        state.status = 'kept';
      } catch (e) {
        state.status = 'error'; state.error = String(e?.message || e);
      }
      busy = null; render();
      return state.last;
    })();
    return busy;
  }

  // ---- the control on the welcome ------------------------------------------------
  // T-2947: one small mono line, not a button that shouts. Tapping it opens a short
  // explanation with the download in it (the phone has no hover for a tooltip), so
  // 238 MB never starts from a stray tap.
  let toggle = null, info = null, note = null, keep = null, drop = null, bar = null;
  function build() {
    mount.replaceChildren();
    toggle = document.createElement('button');
    toggle.type = 'button'; toggle.className = 'welcome-pack-toggle';
    toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-controls', 'welcome-pack-info');
    toggle.addEventListener('click', () => {
      info.hidden = !info.hidden;
      toggle.setAttribute('aria-expanded', String(!info.hidden));
    });
    info = document.createElement('div');
    info.id = 'welcome-pack-info'; info.className = 'welcome-pack-info'; info.hidden = true;
    note = document.createElement('p'); note.className = 'welcome-pack-note';
    keep = document.createElement('button');
    keep.type = 'button'; keep.className = 'welcome-pack-keep';
    keep.addEventListener('click', () => { void install(); });
    drop = document.createElement('button');
    drop.type = 'button'; drop.className = 'welcome-pack-remove'; drop.textContent = 'Remove';
    drop.addEventListener('click', () => { void remove(); });
    bar = document.createElement('i'); bar.className = 'welcome-pack-bar'; bar.setAttribute('aria-hidden', 'true');
    info.append(note, keep, drop, bar);
    mount.append(toggle, info);
  }
  function render(progress) {
    if (!toggle) return;
    const size = state.published ? mb(state.published.bytes) : '';
    const s = state.status;
    mount.dataset.state = s;
    keep.hidden = s === 'downloading' || s === 'kept';
    drop.hidden = s !== 'kept';
    let line, tip;
    if (s === 'downloading') {
      const p = progress || {};
      const frac = p.total ? Math.min(1, p.bytes / p.total) : 0;
      line = `Offline copy · ${Math.round(frac * 100)} %`;
      tip = `Saving ${year} on this device`;
      note.textContent = p.total ? `Saving ${year}: ${mb(p.bytes)} of ${mb(p.total)}. Keep this page open.` : `Saving ${year}…`;
      bar.style.setProperty('--f', String(frac));
    } else if (s === 'kept') {
      line = 'Offline copy · kept';
      tip = `${year} is on this device and opens offline`;
      note.textContent = `${year} is on this device and opens with no connection. Updates fetch only what changed.`;
    } else if (s === 'error') {
      line = 'Offline copy · stopped';
      tip = `The offline copy stopped: ${state.error}`;
      note.textContent = `Stopped: ${state.error}.`;
      keep.textContent = 'Try again';
    } else {
      line = 'Offline copy';
      tip = `Keep ${year} on this device${size ? ` (${size})` : ''} so it opens with no connection`;
      note.textContent = `Saves ${year}${size ? ` (${size})` : ''} on this device so it opens with no connection. `
        + 'The browser\'s own cache can be cleared at any time; this copy stays until you remove it.';
      keep.textContent = size ? `Download ${size}` : 'Download';
    }
    toggle.innerHTML = `${iconSvg(s === 'kept' ? 'kept' : 'keep', 14)}<span>${line}</span>`;
    toggle.title = tip;
    mount.hidden = false;
  }

  /** On every boot: honour the kill switch, show the state, and bring a kept pack up to date. */
  async function start() {
    if (!supported) return state;
    try {
      const reg = await registration();
      let stamp = null;
      try { stamp = await (await fetch(url('build.json'), { cache: 'no-store' })).json(); } catch { /* offline */ }
      if (stamp?.sw_off) { if (reg) await remove(); mount.hidden = true; state.status = 'off'; return state; }
      try {
        const index = await (await fetch(url('packs/index.json'), { cache: 'no-store' })).json();
        state.published = index[year] || null;
      } catch { /* offline: the installed pack answers below */ }
      const kept = reg ? await installedPack() : null;
      if (kept) state.installed = { id: kept.id, count: kept.count, bytes: kept.bytes };
      if (!state.published && !kept) { mount.hidden = true; return state; }   // nothing to keep for this year
      if (!mount.childElementCount) build();
      state.status = kept ? 'kept' : 'idle';
      render();
      // Updates by hash: a kept pack behind the published one fetches the difference.
      if (kept && state.published && state.published.id !== kept.id && !navigator.connection?.saveData) {
        state.status = 'downloading'; render();
        busy = download({ onProgress: render })
          .then(() => { state.status = 'kept'; }, (e) => { state.status = 'error'; state.error = String(e?.message || e); })
          .finally(() => { busy = null; render(); });
      }
    } catch (e) {
      state.status = 'error'; state.error = String(e?.message || e);
      if (button) render(); else mount.hidden = true;
    }
    return state;
  }

  const ready = start();
  if (supported && !dev) {
    // The installed app opens at this year's door (tools/write_year_packs.mjs writes one per year).
    const link = document.createElement('link');
    link.rel = 'manifest'; link.href = url(`${year}/app.webmanifest`);
    document.head.appendChild(link);
  }
  return {
    state, ready, install, remove,
    /** Resolves when no download is running. */
    settled: () => Promise.resolve(ready).then(() => busy),
  };
}
