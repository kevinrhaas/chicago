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
import { verifiedPackAliases } from './published-assets.js';
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

/** T-3758: time left, as a person says it: "about 4 min", "under a minute". Null when unknown. */
export function timeLeft(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return null;
  if (seconds < 50) return 'under a minute';
  if (seconds < 90) return 'about a minute';
  if (seconds < 3600) return `about ${Math.round(seconds / 60)} min`;
  const h = Math.floor(seconds / 3600), m = Math.round((seconds % 3600) / 600) * 10;
  return m >= 60 ? `about ${h + 1} h` : `about ${h} h${m ? ` ${m} min` : ''}`;
}

/**
 * T-3758: the download's ETA from its own pace. The rate is the bytes saved over the time since
 * the first file began, eased (a 10 s time constant) so one slow file does not swing it, and no
 * ETA is given until 3 s and 2 MB are in hand: a guess from the first file is wrong both ways.
 */
export function createPace({ now = () => performance.now() } = {}) {
  let t0 = null, lastAt = null, rate = null, lastBytes = 0;
  return {
    reset() { t0 = null; lastAt = null; rate = null; lastBytes = 0; },
    /** Seconds left for `bytes` of `total`, or null while there is too little to tell. */
    eta(bytes, total) {
      const at = now();
      if (t0 == null) { t0 = at; lastAt = at; lastBytes = bytes; return null; }
      const elapsed = (at - t0) / 1000;
      const sinceLast = (at - lastAt) / 1000;
      if (sinceLast > 0.25) {
        const whole = (bytes - 0) / Math.max(1e-3, elapsed);
        const recent = (bytes - lastBytes) / sinceLast;
        const live = 0.5 * whole + 0.5 * recent;
        const k = rate == null ? 1 : 1 - Math.exp(-sinceLast / 10);
        rate = rate == null ? live : rate + (live - rate) * k;
        lastAt = at; lastBytes = bytes;
      }
      if (elapsed < 3 || bytes < 2e6 || !(rate > 0) || !(total > bytes)) return total > 0 && bytes >= total ? 0 : null;
      return (total - bytes) / rate;
    },
  };
}

/**
 * T-3675: what the control says, in each state. Pure: tools/check_chromebook.mjs reads it.
 * `classroom` (a Chromebook) names the welcome line for the teacher readying a class set;
 * the note says the same honest thing to everyone: the copy is this device's, so a class
 * set is prepared one device at a time, and nothing is downloaded once for the room.
 */
export function packWords({ year, status = 'idle', size = '', progress = null, error = '', classroom = false } = {}) {
  const sized = size ? ` (${size})` : '';
  if (status === 'downloading') {
    const p = progress || {};
    const fraction = p.total ? Math.min(1, p.bytes / p.total) : 0;
    // Floor, not round: a download never reads 100 % before its last byte is saved.
    const pct = `${Math.floor(fraction * 100)} %`;
    const left = timeLeft(p.eta);
    return {
      line: classroom ? `Preparing for class · ${pct}` : `Offline copy · ${pct}`,
      tip: `Saving ${year} on this device${left ? `, ${left} left` : ''}`,
      note: p.total ? `Saving ${year}: ${mb(p.bytes)} of ${mb(p.total)}${left ? `, ${left} left` : ''}. Keep this page open.`
        : `Saving ${year}: checking what this device already holds…`,
      setting: `Saving ${year} · ${pct}${left ? ` · ${left} left` : ''}`, keep: 'Download', fraction,
    };
  }
  if (status === 'kept') {
    return {
      line: classroom ? 'Ready for class · works offline' : 'Offline copy · kept',
      tip: `${year} is on this device and opens offline`,
      note: `Ready: ${year} is on this device and opens with no connection. To check, turn Wi-Fi off and `
        + 'reload this page. Updates fetch only what changed.',
      setting: `${year} · ready offline`, keep: 'Download', fraction: 1,
    };
  }
  if (status === 'error') {
    return {
      line: classroom ? 'Prepare for class · stopped' : 'Offline copy · stopped',
      tip: `The offline copy stopped: ${error}`,
      note: `Stopped: ${error}.`, setting: `${year} · stopped`, keep: 'Try again', fraction: 0,
    };
  }
  return {
    line: classroom ? `Prepare for class${size ? ` · ${size}` : ''}` : 'Offline copy',
    tip: `Keep ${year} on this device${sized} so it opens with no connection`,
    note: `Saves ${year}${sized} on this device so it opens with no connection. To prepare a class, do this `
      + 'on each device before the lesson: every device keeps its own copy, and nothing is shared across '
      + 'the room. It stays until you remove it.',
    setting: `Offline copy of ${year}`,
    keep: size ? `Download ${size}` : 'Download', fraction: 0,
  };
}

export function createYearPack({ year, mount, base = document.baseURI, dev = false, classroom = false }) {
  const root = new URL('../', base);                       // the site root: /4d/ or /4d/dev/
  const cacheName = `c4d-pack ${root.pathname} ${year}`;   // sw.js names it the same way
  const supported = !dev && !!mount && 'serviceWorker' in navigator && 'caches' in globalThis
    && globalThis.isSecureContext !== false && !/[?&]nosw\b/.test(location.search);
  const state = { year, supported, status: 'idle', installed: null, published: null, last: null, error: null };
  let busy = null;
  let shown = false;   // a pack is on offer here (start() found one published or kept)

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

  /** The published list. Cache-busted, so a CDN copy older than the files it lists cannot answer. */
  async function publishedPack() {
    const res = await fetch(url(`packs/${year}.json?t=${Date.now()}`), { cache: 'no-store' });
    if (!res.ok) throw new Error(`no pack for ${year} (${res.status})`);
    return res.json();
  }

  /** Fetch what `next` adds over the installed pack and over `put`, the files this download
   *  already stored (rel -> hash), so a retry picks up where the last attempt stopped. */
  async function fetchFiles(next, old, put, cache, onProgress, carried = 0) {
    const aliases = await verifiedPackAliases(next, root);
    const base = new Map((old?.files || []).map(([rel, hash]) => [rel, hash]));
    for (const [rel, hash] of put) base.set(rel, hash);
    const have = new Set((await cache.keys()).map((r) => decodeURIComponent(new URL(r.url).pathname.slice(root.pathname.length))));
    const plan = planUpdate({ files: [...base] }, next, have);
    const total = plan.fetch.reduce((s, f) => s + f[2], 0);
    // T-3758: the bar counts bytes as they arrive (a 20 MB file used to hold it still, then jump),
    // and a retry after a mid-deploy carries what earlier tries saved (`carried`), so the size
    // shown neither grows nor resets while the download runs.
    let done = 0, bytes = 0, failed = null, inFlight = 0;
    const queue = plan.fetch.slice();
    const report = () => onProgress({ done, count: plan.fetch.length, bytes: carried + bytes + inFlight, total: carried + total });
    report();
    async function worker() {
      while (queue.length && !failed) {
        const [rel, hash, size] = queue.shift();
        let counted = 0;   // this file's bytes on the bar so far
        try {
          // Marked, so the worker never answers it from the pack being replaced
          // (sw.js passes `c4d-pack` requests straight to the network).
          const alias = aliases?.aliases[rel];
          const source = alias ? new URL(alias.source, root).href : url(rel);
          const got = await fetch(`${source}?c4d-pack=${hash}`, { cache: 'no-store' });
          if (!got.ok) throw new Error(`${rel}: ${got.status}`);
          if (alias && (got.status !== 200 || got.headers.has('content-range')))
            throw new Error(`${rel}: publication source is not a complete response`);
          let body;
          const reader = got.body?.getReader?.();
          if (reader) {
            const parts = [];
            let n = 0;
            for (;;) {
              const { done: end, value } = await reader.read();
              if (end) break;
              parts.push(value); n += value.byteLength;
              const now = Math.min(n, size);
              inFlight += now - counted; counted = now;
              report();
            }
            const all = new Uint8Array(n);
            let at = 0;
            for (const part of parts) { all.set(part, at); at += part.byteLength; }
            body = all.buffer;
          } else body = await got.arrayBuffer();
          // A file that does not match its entry is a site mid-deploy: stop, and let
          // download() read the list again.
          const fullHash = hex(await crypto.subtle.digest('SHA-256', body));
          if (body.byteLength !== size || fullHash.slice(0, 16) !== hash || (alias && fullHash !== alias.sha256)) throw Object.assign(new Error(`${rel} changed while downloading`), { stale: true, rel });
          await cache.put(url(rel), new Response(body, { headers: {
            'content-type': got.headers.get('content-type') || 'application/octet-stream' } }));
          put.set(rel, hash);
          inFlight -= counted; counted = 0;
          done += 1; bytes += size;
          report();
        } catch (e) { inFlight -= counted; failed = e; }
      }
    }
    await Promise.all(Array.from({ length: PARALLEL }, worker));
    if (failed) throw Object.assign(failed, { saved: bytes });
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
    let got = null, carried = 0;
    for (let attempt = 1; !got; attempt += 1) {
      try {
        got = await fetchFiles(next, old, put, cache, onProgress, carried);
      } catch (e) {
        carried += e.saved || 0;
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
    // No size until the plan is read: the published size counts files this device may already hold.
    state.status = 'downloading'; state.error = null; pace.reset(); render({ done: 0, bytes: 0, total: 0 });
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

  // ---- the control on the welcome, and its twin in Settings -------------------------
  // T-2947: one small mono line, not a button that shouts. Tapping it opens a short
  // explanation with the download in it (the phone has no hover for a tooltip), so
  // 238 MB never starts from a stray tap. T-3675: on a Chromebook the line reads
  // "Prepare for class" with the size, and Settings › Graphics carries the same
  // download (attachSettings), so a teacher readying a class set finds it either way.
  const views = [];
  let lastProgress = null;
  const pace = createPace();
  let paintedAt = -Infinity;
  function build() {
    mount.replaceChildren();
    const toggle = document.createElement('button');
    toggle.type = 'button'; toggle.className = 'welcome-pack-toggle';
    toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-controls', 'welcome-pack-info');
    const info = document.createElement('div');
    info.id = 'welcome-pack-info'; info.className = 'welcome-pack-info'; info.hidden = true;
    toggle.addEventListener('click', () => {
      info.hidden = !info.hidden;
      toggle.setAttribute('aria-expanded', String(!info.hidden));
    });
    const v = parts('welcome-pack');
    info.append(v.note, v.keep, v.drop, v.bar);
    mount.append(toggle, info);
    views.push({ ...v, kind: 'welcome', root: mount, toggle });
  }
  /** The note, the two buttons and the bar, which both views share. */
  function parts(cls) {
    const note = document.createElement('p');
    note.className = cls === 'welcome-pack' ? 'welcome-pack-note' : 'legend-note pack-settings-note';
    const keep = document.createElement('button');
    keep.type = 'button'; keep.className = cls === 'welcome-pack' ? 'welcome-pack-keep' : 'setting-button pack-keep';
    keep.addEventListener('click', () => { void install(); });
    const drop = document.createElement('button');
    drop.type = 'button'; drop.className = cls === 'welcome-pack' ? 'welcome-pack-remove' : 'setting-button pack-remove';
    drop.textContent = 'Remove';
    drop.addEventListener('click', () => { void remove(); });
    const bar = document.createElement('i'); bar.className = `${cls}-bar`; bar.setAttribute('aria-hidden', 'true');
    return { note, keep, drop, bar };
  }
  /** T-3675: the same download in Settings, as its own group after `anchor` (Graphics › Performance). */
  let settingsAnchor = null;
  function buildSettings() {
    if (!settingsAnchor || views.some((v) => v.kind === 'settings')) return;
    const group = document.createElement('div');
    group.className = 'settings-group pack-settings'; group.id = 's-offline';
    group.dataset.setPane = settingsAnchor.dataset.setPane || 'graphics';
    group.hidden = settingsAnchor.hidden;          // the tab in view decides, as for every group
    const head = document.createElement('h4'); head.textContent = 'Prepare for class';
    const row = document.createElement('div'); row.className = 'field row';
    const label = document.createElement('span');
    const v = parts('pack-settings');
    const actions = document.createElement('span'); actions.className = 'pack-settings-actions';
    actions.append(v.keep, v.drop);
    row.append(label, actions);
    group.append(head, row, v.note, v.bar);
    settingsAnchor.after(group);
    views.push({ ...v, kind: 'settings', root: group, label });
  }
  function render(progress) {
    if (progress) lastProgress = { ...progress, eta: pace.eta(progress.bytes, progress.total) };
    if (!views.length) return;
    const s = state.status;
    // Bytes now arrive many times a second: paint at most four times a second while downloading.
    const at = performance.now();
    if (progress && s === 'downloading' && at - paintedAt < 250 && progress.bytes < progress.total) return;
    paintedAt = at;
    const p = s === 'downloading' ? (lastProgress || {}) : null;
    const words = packWords({ year, status: s, size: state.published ? mb(state.published.bytes) : '',
      progress: p, error: state.error, classroom });
    for (const v of views) {
      v.root.dataset.state = s;
      v.keep.hidden = s === 'downloading' || s === 'kept';
      v.drop.hidden = s !== 'kept';
      v.keep.textContent = words.keep;
      v.note.textContent = words.note;
      v.bar.style.setProperty('--f', String(words.fraction));
      if (v.toggle) {
        v.toggle.innerHTML = `${iconSvg(s === 'kept' ? 'kept' : 'keep', 14)}<span>${words.line}</span>`;
        v.toggle.title = words.tip;
      }
      if (v.label) v.label.textContent = words.setting;
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
      shown = true; buildSettings();
      state.status = kept ? 'kept' : 'idle';
      render();
      // Updates by hash: a kept pack behind the published one fetches the difference.
      if (kept && state.published && state.published.id !== kept.id && !navigator.connection?.saveData) {
        state.status = 'downloading'; pace.reset(); render();
        busy = download({ onProgress: render })
          .then(() => { state.status = 'kept'; }, (e) => { state.status = 'error'; state.error = String(e?.message || e); })
          .finally(() => { busy = null; render(); });
      }
    } catch (e) {
      state.status = 'error'; state.error = String(e?.message || e);
      if (views.length) render(); else mount.hidden = true;
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
    /** T-3675: Settings' "Prepare for class" group, placed after `anchor` once a pack is on offer. */
    attachSettings(anchor) {
      settingsAnchor = anchor || null;
      if (shown) { buildSettings(); render(); }
    },
    /** Resolves when no download is running. */
    settled: () => Promise.resolve(ready).then(() => busy),
  };
}
