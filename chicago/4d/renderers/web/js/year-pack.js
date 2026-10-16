/** T-2561 — keep a year on this device.
 *
 * The welcome's "Keep 1835 on this device" control. On a tap it registers the
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

  /** Download the year's pack, or the part of it that changed. Resolves to what it fetched. */
  async function download({ onProgress = () => {} } = {}) {
    const res = await fetch(url(`packs/${year}.json`), { cache: 'no-store' });
    if (!res.ok) throw new Error(`no pack for ${year} (${res.status})`);
    const next = await res.json();
    const cache = await caches.open(cacheName);
    const old = await installedPack();
    const have = new Set((await cache.keys()).map((r) => decodeURIComponent(new URL(r.url).pathname.slice(root.pathname.length))));
    const plan = planUpdate(old, next, have);
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
          // A file that does not match its entry is a site mid-deploy: stop, keep
          // the installed pack as it was, and let the next visit try again.
          if (await digest(body) !== hash) throw new Error(`${rel} changed while downloading — the site is updating`);
          await cache.put(url(rel), new Response(body, { headers: {
            'content-type': got.headers.get('content-type') || 'application/octet-stream' } }));
          done += 1; bytes += size;
          onProgress({ done, count: plan.fetch.length, bytes, total });
        } catch (e) { failed = e; }
      }
    }
    await Promise.all(Array.from({ length: PARALLEL }, worker));
    if (failed) throw failed;
    for (const rel of plan.drop) await cache.delete(url(rel));
    // The pack's list goes in LAST: the worker serves nothing of a year until it is complete.
    await cache.put(url(MANIFEST), new Response(JSON.stringify(next), { headers: { 'content-type': 'application/json' } }));
    await tellWorker();
    state.installed = { id: next.id, count: next.count, bytes: next.bytes };
    state.last = { fetched: plan.fetch.length, fetchedBytes: total, dropped: plan.drop.length, id: next.id };
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
  let button = null, note = null, bar = null, drop = null;
  function build() {
    mount.replaceChildren();
    button = document.createElement('button');
    button.type = 'button'; button.className = 'welcome-pack-keep';
    button.addEventListener('click', () => (state.status === 'kept' ? null : install()));
    note = document.createElement('span'); note.className = 'welcome-pack-note';
    bar = document.createElement('i'); bar.className = 'welcome-pack-bar'; bar.setAttribute('aria-hidden', 'true');
    drop = document.createElement('button');
    drop.type = 'button'; drop.className = 'welcome-pack-remove'; drop.textContent = 'Remove';
    drop.addEventListener('click', () => { void remove(); });
    mount.append(button, note, drop, bar);
  }
  function render(progress) {
    if (!button) return;
    const size = state.published ? ` · ${mb(state.published.bytes)}` : '';
    const s = state.status;
    mount.dataset.state = s;
    button.disabled = s === 'downloading' || s === 'kept';
    drop.hidden = s !== 'kept';
    if (s === 'downloading') {
      const p = progress || {};
      const frac = p.total ? Math.min(1, p.bytes / p.total) : 0;
      button.innerHTML = `${iconSvg('keep', 18)}<span>Keeping ${year} on this device…</span>`;
      note.textContent = p.total ? `${Math.round(frac * 100)} % · ${mb(p.bytes)} of ${mb(p.total)}` : 'Starting…';
      bar.style.setProperty('--f', String(frac));
    } else if (s === 'kept') {
      button.innerHTML = `${iconSvg('kept', 18)}<span>${year} is on this device</span>`;
      note.textContent = 'Opens offline';
    } else if (s === 'error') {
      button.innerHTML = `${iconSvg('keep', 18)}<span>Keep ${year} on this device${size}</span>`;
      note.textContent = `Download stopped: ${state.error}. Tap to try again.`;
      button.disabled = false;
    } else {
      button.innerHTML = `${iconSvg('keep', 18)}<span>Keep ${year} on this device${size}</span>`;
      note.textContent = 'Downloads the year so it opens fast, even offline.';
    }
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
