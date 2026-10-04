#!/usr/bin/env node
/** T-2045 — boot variants for the arrival-and-jaunts path, on the published mirror.
 *
 * Smoke part 14 (T-2044) walks the path once, on a clean cold boot. A visitor does
 * not always arrive that way, so this boots the published town (`site/4d`, run
 * `tools/publish.sh` first) eight more ways and asks, of each, the same three things:
 * the arrival never reads 1835 before the scene is ready and never counts back up;
 * the welcome is reached, or a failure says so and offers Retry; and a jaunt then
 * starts at its first stop (or, where the catalog is the thing that failed, the town
 * can still be entered on your own). Zero page errors throughout.
 *
 *   warm          a second visit in the same browser: assets from the HTTP cache,
 *                 the first visit's timing history read back
 *   slow          CPU 4x and Fast 3G (1.6 Mbps, 150 ms)
 *   essential     terrain.js throws: Retry, no welcome; Retry then arrives
 *   optional      people.json 503: the town still arrives
 *   reduced       prefers-reduced-motion: at most five years shown, no digit flips
 *   background    the tab hidden mid-boot and again mid-jaunt, then brought back
 *   stale         a timing history from another build, an absurd one from this
 *                 build, a corrupt one, and a saved outing from an older version
 *   catalog       statuses.json and the jaunt catalog both fail
 *
 *   node tools/measure_arrival_jaunt_variants.mjs [--only warm,slow] [--stills DIR]
 *   VARIANTS_VIEWPORT=desktop   1280x800 mouse instead of 390x780 touch
 *
 * Headless Chromium has no way to background a tab (bringToFront and the lifecycle
 * freeze both leave `visibilityState` at visible), so `background` does what the
 * browser does to a hidden tab, from an init script: `document.hidden` reads true,
 * `visibilitychange` fires, and animation frames are held until it comes back.
 * Rides are finished with `travel.simulate`, as part 14 does.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../site/4d');
if (!fs.existsSync(path.join(root, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${root} — run tools/publish.sh first`);
  process.exit(2);
}
const argValue = name => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : null; };
const ONLY = argValue('--only')?.split(',') ?? null;
const STILLS = argValue('--stills');
if (STILLS) fs.mkdirSync(STILLS, { recursive: true });
const DESKTOP = process.env.VARIANTS_VIEWPORT === 'desktop';
const VIEW = DESKTOP ? { width: 1280, height: 800, touch: false, name: 'desktop' }
  : { width: 390, height: 780, touch: true, name: 'mobile' };
const { chromium } = await import('playwright');

// The mirror, gzipped, with Pages' ten-minute lifetime and an ETag, so a second
// visit is a warm one. Every
// response is counted, so `warm` can show what the network was actually asked for.
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.wasm': 'application/wasm', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const gz = new Map();
let served = { requests: 0, revalidated: 0, bytes: 0 };
const server = http.createServer((req, res) => {
  let name = decodeURIComponent(req.url.split('?')[0]);
  if (name.endsWith('/')) name += 'index.html';
  const file = path.resolve(root, '.' + name);
  if (!file.startsWith(root + '/')) { res.writeHead(403).end(); return; }
  try {
    if (!gz.has(file)) {
      const body = zlib.gzipSync(fs.readFileSync(file));
      gz.set(file, { body, etag: `"${crypto.createHash('sha1').update(body).digest('hex').slice(0, 16)}"` });
    }
    const { body, etag } = gz.get(file);
    served.requests += 1;
    // The data loaders fetch with `cache: 'no-cache'`, which revalidates every time;
    // GitHub Pages answers that with a 304 on its ETag, and so does this.
    if (req.headers['if-none-match'] === etag) { served.revalidated += 1; res.writeHead(304, { ETag: etag }).end(); return; }
    served.bytes += body.length;
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream',
      'Content-Encoding': 'gzip', 'Cache-Control': 'max-age=600', ETag: etag });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/walk/?year=1835`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'] });

/** Runs in the page before any of its scripts. */
function probe() {
  try {
    // The path is chrome, not rendering: the town is drawn at `light`, as part 14 does.
    if (!localStorage.getItem('chicago4d.settings')) localStorage.setItem('chicago4d.settings', JSON.stringify({ detail: 'light' }));
  } catch { /* storage refused: the default tier stands */ }
  window.__years = [];
  new MutationObserver(() => {
    const year = document.getElementById('arrival-year')?.dataset.year;
    // Which hint row the gate shows a visitor while it counts: the keys, or the thumbs.
    if (year && !window.__hint) {
      const shown = [...document.querySelectorAll('.gate-keys')].filter(el => getComputedStyle(el).display !== 'none');
      window.__hint = shown.map(el => (el.classList.contains('gate-touch') ? 'touch' : 'keys')).join('+') || 'none';
    }
    if (year && year !== window.__years.at(-1)?.year) {
      window.__years.push({ year, ready: window.__chicago4d?.ready === true, hidden: document.hidden, at: performance.now() });
    }
  }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-year'] });
  // Every loading card shown before the scene was ready.
  window.__cards = [];
  new MutationObserver(() => {
    const text = document.getElementById('arrival-card')?.textContent.trim();
    if (text && text !== window.__cards.at(-1) && window.__chicago4d?.ready !== true) window.__cards.push(text);
  }).observe(document, { subtree: true, childList: true, characterData: true });
  // What a browser does to a background tab: hidden, and no animation frames.
  let hidden = false;
  const held = [];
  const raf = window.requestAnimationFrame.bind(window), caf = window.cancelAnimationFrame.bind(window);
  let nextId = 1e9;
  Object.defineProperty(Document.prototype, 'hidden', { configurable: true, get: () => hidden });
  Object.defineProperty(Document.prototype, 'visibilityState', { configurable: true, get: () => (hidden ? 'hidden' : 'visible') });
  window.requestAnimationFrame = cb => { if (!hidden) return raf(cb); held.push([++nextId, cb]); return nextId; };
  window.cancelAnimationFrame = id => { const i = held.findIndex(h => h[0] === id); if (i >= 0) held.splice(i, 1); else caf(id); };
  window.__background = on => {
    hidden = on;
    document.dispatchEvent(new Event('visibilitychange'));
    if (!on) for (const [, cb] of held.splice(0)) raf(cb);
    return held.length;
  };
}

const results = [];
let failures = 0;
function check(variant, name, ok, detail = '') {
  results.push({ variant, viewport: VIEW.name, name, ok: !!ok, detail });
  if (!ok) failures += 1;
  console.log(`${ok ? 'PASS' : 'FAIL'} [${VIEW.name}/${variant}] ${name}${detail ? ` — ${detail}` : ''}`);
}

async function open(variant, { reducedMotion = 'no-preference', init = null } = {}) {
  const ctx = await browser.newContext({ viewport: { width: VIEW.width, height: VIEW.height },
    hasTouch: VIEW.touch, deviceScaleFactor: VIEW.touch ? 2 : 1, reducedMotion });
  await ctx.addInitScript(probe);
  if (init) await ctx.addInitScript(init.fn, init.arg);
  const page = await ctx.newPage();
  page.setDefaultTimeout(120_000);
  const errors = [];
  page.on('pageerror', e => errors.push(e.message || String(e)));
  return { ctx, page, errors };
}

const until = (page, fn, arg = null, timeout = 240_000) => page.waitForFunction(fn, arg, { polling: 250, timeout });
const arrived = (page, timeout) => until(page, () => window.__chicago4d?.welcome?.state === 'welcome', null, timeout);

/** A visitor's own tap: the first visible match, hit-tested at its centre (part 14's). */
async function tap(page, sel, text = null) {
  const at = await page.evaluate(([s, t]) => {
    const el = [...document.querySelectorAll(s)].find(x => x.getClientRects().length
      && getComputedStyle(x).visibility !== 'hidden' && (t === null || x.textContent.trim() === t));
    if (!el) return { why: `nothing visible matches ${s}` };
    if (el.disabled) return { why: `${s} is disabled` };
    el.scrollIntoView({ block: 'nearest' });
    const r = el.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2;
    const top = document.elementFromPoint(x, y);
    if (!top || !(top === el || el.contains(top))) return { why: `${s} is covered by <${top?.tagName.toLowerCase()} class="${top?.className}">` };
    return { x, y };
  }, [sel, text]);
  if (at.why) throw new Error(`tap: ${at.why}${text ? ` ("${text}")` : ''}`);
  await page.mouse.click(at.x, at.y);
}

/** The arrival's record: years shown in order, each with whether the scene was ready. */
async function yearsCheck(variant, page, label = 'the arrival') {
  const years = await page.evaluate(() => window.__years);
  const early = years.filter(y => y.year === '1835' && !y.ready);
  const ok = years.length >= 2 && Number(years[0].year) > 1835 && !early.length
    && years.every((y, i) => !i || Number(y.year) <= Number(years[i - 1].year));
  check(variant, `${label} counts down, never back up, and reads 1835 only once the scene is ready`, ok,
    `${years.length} readings ${years[0]?.year}→${years.at(-1)?.year}${early.length ? `; 1835 before ready ×${early.length}` : ''}`);
  const hint = await page.evaluate(() => window.__hint);
  const want = VIEW.touch ? 'touch' : 'keys';
  check(variant, `${label} shows the ${want === 'touch' ? 'thumb' : 'keyboard'} hints this device will use`, hint === want, `shows ${hint}`);
  return years;
}

const jauntState = page => page.evaluate(() => {
  const s = window.__chicago4d.jaunts.state;
  return { id: s?.jaunt?.id ?? null, phase: s?.phase ?? null, stopIndex: s?.stopIndex ?? null, notice: s?.notice ?? null };
});
const atStop = page => until(page, () => window.__chicago4d.jaunts.state?.phase === 'atStop');

async function startJaunt(variant, page, id = 'new-in-chicago', { menuOpen = false } = {}) {
  if (!menuOpen) await tap(page, '#welcome-jaunts');
  await until(page, j => !!document.querySelector(`[data-jaunt="${j}"] [data-action="start"]`), id);
  await tap(page, `[data-jaunt="${id}"] [data-action="start"]`);
  await atStop(page);
  const s = await jauntState(page);
  check(variant, `the jaunt "${id}" starts at its first stop`, s.id === id && s.stopIndex === 0, JSON.stringify(s));
  return s;
}

async function exploreOnMyOwn(variant, page) {
  await tap(page, '#welcome-explore');
  await until(page, () => !!document.querySelector('#welcome-picker:not([hidden]) .welcome-destination:not(:disabled)'));
  await tap(page, '#welcome-results .welcome-destination:not(:disabled)');
  await until(page, () => window.__chicago4d.welcome.state === 'world');
  check(variant, 'a place picked under Starting At… enters the town',
    await page.evaluate(() => document.getElementById('gate').hidden));
}

async function still(page, name) {
  if (STILLS) await page.screenshot({ path: path.join(STILLS, `${VIEW.name}-${name}.jpg`), type: 'jpeg', quality: 60 });
}

async function finish(variant, { ctx, page, errors }, still_ = variant) {
  await still(page, still_);
  check(variant, 'zero page errors', !errors.length, errors.slice(0, 3).join(' | '));
  await ctx.close();
}

const clock = () => { const t0 = Date.now(); return () => `${((Date.now() - t0) / 1000).toFixed(1)} s`; };

const VARIANTS = {
  async warm() {
    const v = 'warm', run = await open(v), { page } = run;
    served = { requests: 0, revalidated: 0, bytes: 0 };
    let t = clock();
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    const cold = { ...served, time: t() };
    const written = await page.evaluate(() => ({
      history: JSON.parse(localStorage.getItem('c4d.boot.timings.v1') || 'null'),
      warmFlag: sessionStorage.getItem('c4d.loading.build.1835'),
    }));
    check(v, 'the first visit leaves a timing history for this build and marks the loading copy seen',
      !!written.history?.build && !!written.warmFlag, `build ${written.history?.build}`);
    served = { requests: 0, revalidated: 0, bytes: 0 };
    t = clock();
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    const warm = { ...served, time: t() };
    check(v, 'the second visit is served from the browser cache',
      warm.bytes < cold.bytes * 0.05, `cold ${cold.requests} requests ${(cold.bytes / 1e6).toFixed(2)} MB in ${cold.time}; warm ${warm.requests} `
      + `requests (${warm.revalidated} answered 304) ${(warm.bytes / 1e6).toFixed(2)} MB in ${warm.time}`);
    const read = await page.evaluate(async () => {
      const { BOOT_WEIGHTS } = await import('./js/boot-weights.js');
      const boot = window.__chicago4d.boot;
      const history = JSON.parse(localStorage.getItem('c4d.boot.timings.v1'));
      const cell = Object.entries(history.cells).find(([k]) => k.endsWith('/light'));
      const defaults = BOOT_WEIGHTS[cell[0].split('/')[0]].light.cold;
      return Object.entries(boot.expected).filter(([id]) => defaults[id] > 0).map(([id, value]) => ({ id, value, default: defaults[id] }));
    });
    check(v, 'the second visit paces the arrival from the first visit\'s timings, not the shipped defaults',
      read.some(r => Math.abs(r.value - r.default) > 1e-9),
      read.map(r => `${r.id} ${r.value.toFixed(2)}/${r.default.toFixed(2)}`).join(', '));
    await yearsCheck(v, page, 'the warm arrival');
    await startJaunt(v, page);
    await finish(v, run);
  },

  async slow() {
    const v = 'slow', run = await open(v), { page } = run;
    const cdp = await run.ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150,
      downloadThroughput: 1.6e6 / 8, uploadThroughput: 750e3 / 8 });
    const t = clock();
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 240_000 });
    await arrived(page, 480_000);
    const time = t();
    const years = await yearsCheck(v, page, 'the throttled arrival');
    check(v, 'a slow boot shows the year moving, not one jump at the end',
      new Set(years.map(y => y.year)).size >= 4, `${new Set(years.map(y => y.year)).size} distinct years; welcome at ${time}`);
    await startJaunt(v, page);
    await finish(v, run);
  },

  async essential() {
    const v = 'essential', run = await open(v), { page } = run;
    const terrain = fs.readFileSync(path.join(root, 'walk/js/terrain.js'), 'utf8');
    const marker = 'const heightfield = new Heightfield();';
    if (!terrain.includes(marker)) throw new Error('terrain.js no longer carries the failure seam this variant breaks');
    await page.route('**/terrain.js', route => route.fulfill({ contentType: 'text/javascript',
      body: terrain.replace(marker, `throw new Error("forced terrain failure"); ${marker}`) }));
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await until(page, () => window.__chicago4d?.arrival?.state.failed);
    await page.waitForTimeout(500);
    const failed = await page.evaluate(() => ({ welcome: window.__chicago4d.welcome.state,
      year: window.__chicago4d.arrival.state.year, copy: document.getElementById('gate-sub').textContent,
      button: document.getElementById('gate-btn').textContent, disabled: document.getElementById('gate-btn').disabled,
      hint: [...document.querySelectorAll('.gate-keys')].filter(el => getComputedStyle(el).display !== 'none')
        .map(el => (el.classList.contains('gate-touch') ? 'touch' : 'keys')).join('+') }));
    check(v, 'an essential failure says what failed, offers Retry, and does not arrive',
      failed.welcome !== 'welcome' && failed.year >= 1836 && /forced terrain failure/.test(failed.copy)
      && failed.button === 'Retry' && !failed.disabled, JSON.stringify(failed));
    check(v, 'the failure screen shows the hints this device will use', failed.hint === (VIEW.touch ? 'touch' : 'keys'), `shows ${failed.hint}`);
    await yearsCheck(v, page, 'the failed arrival');
    await still(page, 'essential-failed');
    await page.unroute('**/terrain.js');
    await Promise.all([page.waitForNavigation({ waitUntil: 'domcontentloaded' }), tap(page, '#gate-btn')]);
    await arrived(page);
    check(v, 'Retry reloads and, the fault gone, the town arrives', true);
    await startJaunt(v, page);
    await finish(v, run);
  },

  async optional() {
    const v = 'optional', run = await open(v), { page } = run;
    let hits = 0;
    await page.route('**/people.json', route => { hits += 1; return route.fulfill({ status: 503, body: 'forced optional failure' }); });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    const read = await page.evaluate(() => ({ people: window.__chicago4d.boot.timings().find(p => p.id === 'people')?.error ?? null,
      copy: document.getElementById('gate-sub').textContent, year: window.__chicago4d.arrival.state.year }));
    check(v, 'people.json failing still arrives at 1835, the failure recorded on the optional phase',
      hits > 0 && !!read.people && read.year === 1835, `${hits} request(s) refused; ${JSON.stringify(read)}`);
    await yearsCheck(v, page);
    await startJaunt(v, page);
    await finish(v, run);
  },

  async reduced() {
    const v = 'reduced', run = await open(v, { reducedMotion: 'reduce' }), { page } = run;
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    const years = await yearsCheck(v, page);
    const animations = await page.evaluate(() => document.getElementById('arrival-year').getAnimations({ subtree: true }).length);
    check(v, 'reduced motion shows at most five years and flips no digits',
      new Set(years.map(y => y.year)).size <= 5 && animations === 0,
      `${[...new Set(years.map(y => y.year))].join(' ')}; ${animations} animation(s)`);
    await startJaunt(v, page);
    await finish(v, run);
  },

  async background() {
    const v = 'background', run = await open(v), { page } = run;
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await until(page, () => window.__years.length >= 2 && !window.__chicago4d?.ready);
    const before = await page.evaluate(() => { window.__background(true); return window.__years.at(-1).year; });
    await page.waitForTimeout(6000);
    const whileHidden = await page.evaluate(() => window.__years.filter(y => y.hidden).length);
    await page.evaluate(() => window.__background(false));
    await arrived(page);
    const years = await yearsCheck(v, page, 'an arrival hidden mid-boot');
    check(v, 'a hidden tab flips no digits, and on its return the year goes on from where it stood',
      whileHidden === 0 && Number(years.find(y => !y.hidden && Number(y.year) <= Number(before))?.year) <= Number(before),
      `hidden at ${before}; ${whileHidden} reading(s) while hidden; then ${years.at(-1).year}`);
    await startJaunt(v, page);
    await page.evaluate(() => window.__background(true));
    await page.waitForTimeout(3000);
    await page.evaluate(() => window.__background(false));
    const after = await jauntState(page);
    check(v, 'a jaunt at its stop is still at that stop when the tab comes back',
      after.id === 'new-in-chicago' && after.phase === 'atStop' && after.stopIndex === 0, JSON.stringify(after));
    await tap(page, '#jaunt-panel [data-action="next"]');
    await until(page, () => window.__chicago4d.jaunts.state.phase === 'travelling');
    await page.evaluate(() => window.__background(true));
    await page.waitForTimeout(3000);
    await page.evaluate(() => window.__background(false));
    const riding = await jauntState(page);
    await page.evaluate(() => { if (window.__chicago4d.travel.state.phase !== 'idle') window.__chicago4d.travel.simulate(600); });
    await atStop(page);
    const landed = await jauntState(page);
    check(v, 'a ride the tab left mid-way carries on when it comes back, and lands at the next stop',
      ['travelling', 'atStop'].includes(riding.phase) && landed.stopIndex === 1, `${riding.phase} → stop ${landed.stopIndex}`);
    await finish(v, run);
  },

  async stale() {
    const v = 'stale';
    // A history from another build, a saved outing from an older version of its jaunt.
    const seed = { fn: () => {
      if (sessionStorage.getItem('stale.seeded')) return;
      sessionStorage.setItem('stale.seeded', '1');
      const wild = { scene: 999, terrain: 999, buildings: 999, ground: 999, flora: 999, interaction: 999 };
      localStorage.setItem('c4d.boot.timings.v1', JSON.stringify({ build: 'an-older-build', cells: { 'mobile/light': wild, 'desktop/light': wild } }));
      localStorage.setItem('c4d.jaunt.session.v1', JSON.stringify({ content_version: 'an-older-version', jaunt: 'new-in-chicago', events: [] }));
    } };
    const run = await open(v, { init: seed }), { page } = run;
    const expected = () => page.evaluate(async () => {
      const { BOOT_WEIGHTS } = await import('./js/boot-weights.js');
      const touch = matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
      const defaults = BOOT_WEIGHTS[touch ? 'mobile' : 'desktop'].light.cold;
      return Object.entries(window.__chicago4d.boot.expected).filter(([id]) => defaults[id] > 0)
        .map(([id, value]) => ({ id, value, ratio: value / defaults[id] }));
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    let read = await expected();
    check(v, 'a timing history from another build is ignored: the arrival paces by the shipped defaults',
      read.every(r => Math.abs(r.ratio - 1) < 1e-9), read.map(r => `${r.id} ×${r.ratio.toFixed(2)}`).join(', '));
    await yearsCheck(v, page, 'the arrival over another build\'s history');
    // A saved outing is restored when the Jaunts menu first opens, and its notice is shown there.
    const savedOuting = () => page.evaluate(async () => {
      await new Promise(r => setTimeout(r, 300));
      return { saved: localStorage.getItem('c4d.jaunt.session.v1'),
        shown: [...document.querySelectorAll('#welcome-jaunts-content .jaunt-session-note')].map(n => n.textContent.trim()).join(' ') };
    });
    await tap(page, '#welcome-jaunts');
    await until(page, () => !!document.querySelector('[data-jaunt="new-in-chicago"] [data-action="start"]'));
    const outing = await savedOuting();
    check(v, 'a saved outing from an older version is discarded, and the Jaunts menu says so',
      outing.saved === null && /older version/.test(outing.shown), JSON.stringify(outing));
    await still(page, 'stale-outing');
    await startJaunt(v, page, 'new-in-chicago', { menuOpen: true });

    // This build's own history, made absurd: every phase a hundred times what it took.
    await page.evaluate(() => {
      const h = JSON.parse(localStorage.getItem('c4d.boot.timings.v1'));
      for (const cell of Object.values(h.cells)) for (const k of Object.keys(cell)) cell[k] = k === 'scene' ? 1e-6 : 1e6;
      localStorage.setItem('c4d.boot.timings.v1', JSON.stringify(h));
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    read = await expected();
    check(v, 'an absurd history from this build is held to a quarter and four times the defaults',
      read.every(r => r.ratio >= 0.25 - 1e-9 && r.ratio <= 4 + 1e-9) && read.some(r => Math.abs(r.ratio - 1) > 1e-9),
      read.map(r => `${r.id} ×${r.ratio.toFixed(2)}`).join(', '));
    await yearsCheck(v, page, 'the arrival over an absurd history');

    await page.evaluate(() => {
      localStorage.setItem('c4d.boot.timings.v1', '{"build": not json');
      localStorage.setItem('c4d.jaunt.session.v1', '[[[');
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    read = await expected();
    await yearsCheck(v, page, 'the arrival over a corrupt history');
    await tap(page, '#welcome-jaunts');
    await until(page, () => !!document.querySelector('[data-jaunt="new-in-chicago"] [data-action="start"]'));
    const damaged = await savedOuting();
    check(v, 'a corrupt history and a corrupt saved outing cost nothing but themselves',
      read.every(r => Math.abs(r.ratio - 1) < 1e-9) && damaged.saved === null && /damaged/.test(damaged.shown),
      JSON.stringify(damaged));
    await startJaunt(v, page, 'new-in-chicago', { menuOpen: true });
    await finish(v, run);
  },

  async catalog() {
    const v = 'catalog', run = await open(v), { page } = run;
    let statuses = 0, catalogs = 0, refuseCatalog = true;
    await page.route('**/loading/statuses.json', route => { statuses += 1; return route.fulfill({ status: 503, body: 'forced' }); });
    await page.route('**/jaunts/catalog.json', route => {
      catalogs += 1;
      return refuseCatalog ? route.fulfill({ status: 503, body: 'forced' }) : route.continue();
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await arrived(page);
    const gate = await page.evaluate(async () => {
      const { EARLY_ENTRIES } = await import('./js/loading-early.js');
      const early = new Set(EARLY_ENTRIES.map(e => e.text));
      return { cards: window.__cards.length, early: window.__cards.filter(c => early.has(c)).length,
        first: window.__cards.find(c => early.has(c)) ?? null, year: window.__chicago4d.arrival.state.year };
    });
    check(v, 'statuses.json failing still arrives, the loading cards drawn from the early entries',
      statuses > 0 && gate.year === 1835 && gate.early > 0,
      `${statuses} refused; ${gate.early} of ${gate.cards} cards from the early set, e.g. "${gate.first}"`);
    await yearsCheck(v, page);
    await tap(page, '#welcome-jaunts');
    await until(page, () => /Jaunts could not load/.test(document.getElementById('welcome-jaunts-content')?.textContent || ''));
    check(v, 'a failed catalog says so in the Jaunts region and offers Try again',
      catalogs > 0 && await page.locator('#welcome-jaunts-content button', { hasText: 'Try again' }).isVisible(), `${catalogs} refused`);
    await still(page, 'catalog-failed');
    await exploreOnMyOwn(v, page);
    await tap(page, '#btn-start');
    await until(page, () => window.__chicago4d.welcome.state === 'welcome');
    refuseCatalog = false;
    await tap(page, '#welcome-jaunts');
    await until(page, () => !!document.querySelector('#welcome-jaunts-content [data-jaunt]')
      || [...document.querySelectorAll('#welcome-jaunts-content button')].some(b => b.textContent.trim() === 'Try again'));
    if (await page.locator('#welcome-jaunts-content button', { hasText: 'Try again' }).isVisible()) {
      await tap(page, '#welcome-jaunts-content button', 'Try again');
    }
    await until(page, () => !!document.querySelector('[data-jaunt="new-in-chicago"] [data-action="start"]'));
    await tap(page, '[data-jaunt="new-in-chicago"] [data-action="start"]');
    await atStop(page);
    const s = await jauntState(page);
    check(v, 'once the catalog answers, Try again lists the jaunts and one starts at its first stop',
      s.id === 'new-in-chicago' && s.stopIndex === 0, JSON.stringify(s));
    await finish(v, run);
  },
};

const names = ONLY ?? Object.keys(VARIANTS);
const timings = {};
try {
  for (const name of names) {
    if (!VARIANTS[name]) throw new Error(`no variant "${name}" (have ${Object.keys(VARIANTS).join(', ')})`);
    const t = clock();
    console.log(`START [${VIEW.name}/${name}]`);
    try { await VARIANTS[name](); } catch (e) { check(name, 'ran to the end', false, String(e.message || e).split('\n')[0]); }
    timings[name] = t();
    console.log(`END [${VIEW.name}/${name}] ${timings[name]}`);
  }
} finally {
  await browser.close();
  await new Promise(r => server.close(r));
}
if (STILLS) {
  // Variants run in batches under the foreground ceiling; each batch replaces its own rows.
  const file = path.join(STILLS, `${VIEW.name}-results.json`);
  let prior = { timings: {}, results: [] };
  try { prior = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { /* first batch */ }
  fs.writeFileSync(file, `${JSON.stringify({ viewport: VIEW, browser: browser.version(),
    timings: { ...prior.timings, ...timings },
    results: [...prior.results.filter(r => !names.includes(r.variant)), ...results] }, null, 2)}\n`);
}
console.log(`${failures ? 'FAIL' : 'PASS'}: ${results.length - failures}/${results.length} checks at ${VIEW.width}x${VIEW.height}`);
process.exit(failures ? 1 : 0);
