#!/usr/bin/env node
/**
 * The year pack, driven in a real browser (T-2561).
 *
 *   node tools/smoke_year_pack.mjs --part keep   --viewport mobile    # ~3 min
 *   node tools/smoke_year_pack.mjs --part keep   --viewport desktop   # ~3 min
 *   node tools/smoke_year_pack.mjs --part update                      # ~3 min
 *   node tools/smoke_year_pack.mjs --part warm   [--rtt 40]           # ~5 min
 *
 * Serves the PUBLISHED mirror (run tools/publish.sh first) the way the site is
 * laid out: production at /4d/ and the dev preview at /4d/dev/ (the same tree,
 * as deploy.yml copies it). Every part fails on any page error.
 *
 *   keep    a visitor taps "Keep 1835 on this device" on the welcome; every file
 *           of the pack is fetched once and kept. Then the browser goes offline
 *           AND the server stops answering, the page reloads, the town boots and
 *           walks — with zero requests reaching the server. A dev-preview file is
 *           not answered from production's pack.
 *   update  "a second publish with one changed GLB": the pack is kept, one GLB's
 *           bytes change (a same-length edit to its JSON chunk, so it still
 *           parses) and the pack lists the new hash. The next visit fetches that
 *           file and nothing else, counted at the server. Then the kill switch is
 *           thrown (build.json sw_off, sw.js KILL = true) and the next visit
 *           unregisters the worker and deletes the pack, asserted.
 *   warm    boot time to ready at the phone profile (390x780 touch, no CPU
 *           throttle, as tools/measure_boot_phases.mjs), cold and warm without
 *           a pack against warm with one. `--rtt N` delays every response N ms,
 *           a phone's round trip; localhost has none, and the HTTP cache's
 *           revalidations are what a pack saves. Quote the printed lines.
 */
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hashOf, swText } from './write_year_packs.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(here, '../../../site/4d');
const YEAR = '1835';
const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const PART = arg('part', 'keep');
const VIEWPORT = arg('viewport', PART === 'update' ? 'desktop' : 'mobile');
const RTT = Number(arg('rtt', '0'));
const SHOTS = arg('shots', null);
const TYPES = { '.js': 'text/javascript', '.json': 'application/json', '.html': 'text/html', '.css': 'text/css',
  '.wasm': 'application/wasm', '.webp': 'image/webp', '.woff2': 'font/woff2', '.png': 'image/png',
  '.webmanifest': 'application/manifest+json', '.glb': 'model/gltf-binary', '.ktx2': 'image/ktx2' };

if (!fs.existsSync(path.join(SITE, 'packs', `${YEAR}.json`))) {
  console.error(`smoke_year_pack: ${SITE}/packs/${YEAR}.json is missing — run tools/publish.sh first`);
  process.exit(2);
}
const t0 = Date.now();
const failures = [];
const check = (what, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures.push(what);
};

// ---- the server: /4d/ and /4d/dev/, an overlay for "a second publish", a hit counter, an off switch
const overlay = new Map();
let hits = [];
let down = false;
const server = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  hits.push(q.url);
  if (down) { q.socket.destroy(); return; }
  const m = u.match(/^\/4d\/(?:dev\/)?(.*)$/);
  if (!m) { r.writeHead(404); r.end(); return; }
  let rel = m[1];
  if (rel === '' || rel.endsWith('/')) rel += 'index.html';
  const p = path.resolve(SITE, rel);
  if (!p.startsWith(SITE + path.sep)) { r.writeHead(403); r.end(); return; }
  const send = (data) => setTimeout(() => {
    const st = overlay.has(rel) ? null : fs.statSync(p);
    const lm = st ? st.mtime.toUTCString() : null;
    if (lm && q.headers['if-modified-since'] === lm) { r.writeHead(304); r.end(); return; }
    r.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream',
      'cache-control': 'max-age=600', ...(lm ? { 'last-modified': lm } : {}) });
    r.end(data);
  }, RTT);
  if (overlay.has(rel)) { send(overlay.get(rel)); return; }
  fs.readFile(p, (err, data) => { if (err) { r.writeHead(404); r.end(); return; } send(data); });
});
await new Promise((res) => server.listen(0, '127.0.0.1', res));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const DOOR = `${ORIGIN}/4d/${YEAR}/`;

const { chromium } = await import('playwright');
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const contextFor = async (viewport = VIEWPORT) => {
  const ctx = await browser.newContext(viewport === 'mobile'
    ? { viewport: { width: 390, height: 780 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 }
    : { viewport: { width: 1280, height: 800 } });
  await ctx.addInitScript(() => localStorage.setItem('chicago4d.settings', JSON.stringify({ detail: 'light' })));
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  return { ctx, page, errors };
};
const booted = async (page, label) => {
  const t = Date.now();
  await page.waitForFunction(() => window.__chicago4d?.ready === true || !!window.__chicago4d?.error, null,
    { timeout: 300_000, polling: 250 });
  const error = await page.evaluate(() => window.__chicago4d.error);
  check(`${label}: the town boots`, !error, error || `${((Date.now() - t) / 1000).toFixed(1)} s`);
  return Date.now() - t;
};
const pack = JSON.parse(fs.readFileSync(path.join(SITE, 'packs', `${YEAR}.json`), 'utf8'));
const keep = async (page, label) => {
  await page.waitForFunction(() => window.__chicago4d?.pack && !document.getElementById('welcome-pack').hidden,
    null, { timeout: 60_000 });
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, `${label}-offer.png`) });
  const before = hits.length;
  const t = Date.now();
  await page.click('.welcome-pack-keep');
  if (SHOTS) {
    await page.waitForFunction(() => document.getElementById('welcome-pack').dataset.state === 'downloading');
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SHOTS, `${label}-downloading.png`) });
  }
  await page.waitForFunction(() => ['kept', 'error'].includes(window.__chicago4d.pack.state.status), null,
    { timeout: 300_000, polling: 500 });
  const st = await page.evaluate(() => ({ ...window.__chicago4d.pack.state }));
  // The pack's own downloads carry `?c4d-pack=`; the page may fetch other files meanwhile.
  const fetched = hits.slice(before).filter((u) => u.includes('c4d-pack=')).map((u) => u.split('?')[0]);
  check(`${label}: the pack downloads and is kept`, st.status === 'kept', st.error || `${st.last?.fetched} files, `
    + `${(st.last?.fetchedBytes / 1e6).toFixed(1)} MB in ${((Date.now() - t) / 1000).toFixed(1)} s`);
  check(`${label}: every file in the pack fetched exactly once`,
    st.last?.fetched === pack.count && fetched.length === pack.count && new Set(fetched).size === pack.count,
    `${pack.count} listed, ${fetched.length} requests, ${new Set(fetched).size} distinct`);
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, `${label}-kept.png`) });
  return st;
};
const enterAndWalk = async (page, label) => {
  const moved = await page.evaluate(async () => {
    const welcome = window.__chicago4d.welcome;
    const deadline = Date.now() + 90_000;
    while (welcome.state !== 'world' && Date.now() < deadline) {
      if (welcome.state === 'welcome') welcome.enter('spawn');
      await new Promise((r) => setTimeout(r, 100));
    }
    document.exitPointerLock?.();
    return welcome.state;
  });
  const before = await page.evaluate(() => ({ ...window.__chicago4d.player }));
  await page.keyboard.down('KeyW');
  await page.waitForTimeout(2200);
  await page.keyboard.up('KeyW');
  const after = await page.evaluate(() => ({ ...window.__chicago4d.player }));
  const d = Math.hypot(after.e - before.e, after.n - before.n);
  check(`${label}: enters the town and walks`, moved === 'world' && d > 0.3, `${moved}, moved ${d.toFixed(2)} m in 2.2 s`);
};
/** A same-length edit inside a GLB's JSON chunk: different bytes, still the same valid GLB. */
const editGlb = (buf) => {
  const out = Buffer.from(buf);
  const jsonLen = out.readUInt32LE(12);
  const json = out.subarray(20, 20 + jsonLen).toString('latin1');
  // The asset's generator string is free text: flip the case of its first letter.
  const g = json.indexOf('"generator":"');
  if (g >= 0) { const at = 20 + g + 13; out[at] ^= 0x20; return out; }
  // Otherwise the chunk's trailing padding (spaces, to a 4-byte boundary) becomes a tab.
  const end = json.lastIndexOf('}');
  if (end + 1 < jsonLen) { out[20 + end + 1] = 0x09; return out; }
  throw new Error('the GLB JSON chunk has no generator and no padding to edit');
};

try {
  if (PART === 'keep') {
    const { ctx, page, errors } = await contextFor();
    const label = `keep/${VIEWPORT}`;
    await page.goto(DOOR);
    await booted(page, `${label} online`);
    await keep(page, label);
    // Offline twice over: the browser's network and the server itself.
    await ctx.setOffline(true);
    down = true;
    const before = hits.length;
    await page.reload();
    await booted(page, `${label} offline`);
    const state = await page.evaluate(() => window.__chicago4d.pack.ready.then((s) => s.status));
    check(`${label} offline: the welcome says the year is kept`, state === 'kept', state);
    await enterAndWalk(page, `${label} offline`);
    // The one request allowed out is the browser's own check for a newer sw.js, made
    // on navigation whatever the page does; it fails, and the kept worker carries on.
    const out = hits.slice(before).filter((u) => u.split('?')[0] !== '/4d/sw.js');
    check(`${label} offline: no request for the town reached the server`, out.length === 0,
      `${out.length} did: ${out.slice(0, 5).join(', ')}`);
    const devServed = await page.evaluate(async () => {
      try { return (await fetch('/4d/dev/walk/js/main.js')).ok; } catch { return false; }
    });
    check(`${label}: production's pack does not answer for the dev preview`, devServed === false);
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, `${label}-offline-town.png`), timeout: 60_000 }).catch(() => {});
    check(`${label}: zero page errors`, errors.length === 0, errors.slice(0, 3).join(' | '));
    await ctx.close();
  } else if (PART === 'update') {
    const { ctx, page, errors } = await contextFor();
    const label = `update/${VIEWPORT}`;
    await page.goto(DOOR);
    await booted(page, `${label} first visit`);
    await keep(page, label);
    // A second publish, one GLB changed.
    const glbs = pack.files.filter(([rel]) => /^data\/gltf\/[^/]+\.glb$/.test(rel) && !/terrain|water/.test(rel));
    const [rel] = glbs[Math.floor(glbs.length / 2)];
    const edited = editGlb(fs.readFileSync(path.join(SITE, rel)));
    const files = pack.files.map((f) => (f[0] === rel ? [rel, hashOf(edited), edited.length] : f));
    const id = hashOf(files.map((f) => f.join(' ')).join('\n'));
    const next = { ...pack, id, files };
    const index = JSON.parse(fs.readFileSync(path.join(SITE, 'packs/index.json'), 'utf8'));
    overlay.set(rel, edited);
    overlay.set(`packs/${YEAR}.json`, Buffer.from(JSON.stringify(next)));
    overlay.set('packs/index.json', Buffer.from(JSON.stringify({ ...index, [YEAR]: { ...index[YEAR], id } })));
    const before = hits.length;
    await page.reload();
    await booted(page, `${label} after the second publish`);
    await page.evaluate(() => window.__chicago4d.pack.settled());
    const st = await page.evaluate(() => ({ ...window.__chicago4d.pack.state }));
    const gotten = hits.slice(before).filter((u) => u.split('?')[0].endsWith(`/${rel}`));
    const marked = hits.slice(before).filter((u) => u.includes('c4d-pack='));
    check(`${label}: the update fetches only the changed GLB`,
      st.status === 'kept' && st.last?.fetched === 1 && st.last?.id === id && gotten.length === 1 && marked.length === 1,
      `${st.last?.fetched} file(s) fetched by the pack, ${marked.length} pack download(s) at the server, `
      + `${rel} requested ${gotten.length}x, pack ${st.last?.id}`
      + (st.status === 'kept' && st.last ? '' : ` (state ${JSON.stringify(st)})`));
    const kept = await page.evaluate(async (u) => {
      const c = await caches.open([...(await caches.keys())].find((n) => n.startsWith('c4d-pack ')));
      const res = await c.match(new URL(u, location.href).href);
      return res ? [...new Uint8Array(await crypto.subtle.digest('SHA-256', await res.arrayBuffer()))]
        .map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16) : null;
    }, `/4d/${rel}`);
    check(`${label}: the kept copy is the new file`, kept === hashOf(edited), `${kept}`);
    // The kill switch.
    const stamp = JSON.parse(fs.readFileSync(path.join(SITE, 'build.json'), 'utf8'));
    overlay.set('build.json', Buffer.from(JSON.stringify({ ...stamp, sw_off: true })));
    overlay.set('sw.js', Buffer.from(swText(true)));
    await page.reload();
    await booted(page, `${label} after the kill switch`);
    await page.evaluate(() => window.__chicago4d.pack.ready);
    await page.waitForFunction(async () => (await navigator.serviceWorker.getRegistrations()).length === 0
      && !(await caches.keys()).some((n) => n.startsWith('c4d-pack ')), null, { timeout: 60_000, polling: 500 })
      .catch(() => {});
    const left = await page.evaluate(async () => ({
      regs: (await navigator.serviceWorker.getRegistrations()).length,
      packs: (await caches.keys()).filter((n) => n.startsWith('c4d-pack ')).length,
      control: document.getElementById('welcome-pack').hidden,
    }));
    check(`${label}: the kill switch unregisters the worker and deletes the pack`,
      left.regs === 0 && left.packs === 0 && left.control, JSON.stringify(left));
    check(`${label}: zero page errors`, errors.length === 0, errors.slice(0, 3).join(' | '));
    await ctx.close();
  } else if (PART === 'warm') {
    const label = `warm/mobile rtt ${RTT} ms`;
    const a = await contextFor('mobile');
    await a.page.goto(DOOR);
    const cold = await booted(a.page, `${label} cold, no pack`);
    await a.page.reload();
    const warm = await booted(a.page, `${label} warm, no pack (HTTP cache)`);
    check(`${label}: zero page errors without a pack`, a.errors.length === 0, a.errors.slice(0, 3).join(' | '));
    await a.ctx.close();
    const b = await contextFor('mobile');
    await b.page.goto(DOOR);
    await booted(b.page, `${label} cold, before keeping`);
    await keep(b.page, label);
    const before = hits.length;
    await b.page.reload();
    const packed = await booted(b.page, `${label} warm, from the pack`);
    const reached = hits.length - before;
    check(`${label}: zero page errors with a pack`, b.errors.length === 0, b.errors.slice(0, 3).join(' | '));
    await b.ctx.close();
    console.log(`BOOT TO READY  ${label}: cold ${(cold / 1000).toFixed(1)} s · warm ${(warm / 1000).toFixed(1)} s`
      + ` · warm from the pack ${(packed / 1000).toFixed(1)} s (${reached} requests reached the server)`);
  } else throw new Error(`unknown --part ${PART}`);
} catch (e) {
  check(`${PART}: ran to the end`, false, String(e?.stack || e).split('\n').slice(0, 3).join(' '));
} finally {
  await browser.close();
  server.close();
}
console.log(`smoke_year_pack --part ${PART} (${VIEWPORT}): ${failures.length ? `${failures.length} FAILED` : 'all passed'}`
  + ` in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
process.exit(failures.length ? 1 : 0);
