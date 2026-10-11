#!/usr/bin/env node
/**
 * In-app QA for the card's Images tab (T-2389): boots a year in the source tree, opens
 * buildings' cards, proves no picture is requested before the tab opens, opens it, and
 * photographs the card at 1280x800 and 390x780.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/qa_images_tab_t2389.mjs [--store <dir with the store's files>] [--out <dir>]
 *
 * `--store` serves the image store's files from a local checkout of
 * kevinrhaas/chicago-images (prairie-1904/files/) for a container that cannot reach
 * its host; without it the store is requested live.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const arg = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const STORE = arg('--store');
const OUT = arg('--out') ?? path.join(ROOT, 'docs/RESEARCH/images-tab-2389');
fs.mkdirSync(OUT, { recursive: true });

let ns;
try { ns = await import('playwright'); } catch {
  const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
  ns = await import(path.join(root, 'playwright', 'index.js'));
}
const { chromium } = ns.chromium ? ns : ns.default;

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.bin': 'application/octet-stream', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p)] ?? 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const results = [];
const fail = (m) => { results.push(`FAIL ${m}`); };
const ok = (m) => { results.push(`ok   ${m}`); };

async function run(viewport, year, ids) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: viewport.width < 500 ? 2 : 1,
    isMobile: viewport.width < 500, hasTouch: viewport.width < 500 });
  const page = await ctx.newPage();
  const errors = [];
  const picRequests = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.route(/kevinrhaas\.github\.io\/chicago-images\//, (route) => {
    picRequests.push(route.request().url());
    const f = STORE && path.join(STORE, path.basename(new URL(route.request().url()).pathname));
    if (f && fs.existsSync(f)) route.fulfill({ status: 200, contentType: 'image/jpeg', body: fs.readFileSync(f) });
    else if (STORE) route.fulfill({ status: 404 });
    else route.continue();
  });
  await page.goto(`http://127.0.0.1:${port}/renderers/web/index.html?year=${year}&seed=1`);
  await page.waitForFunction(() => window.__chicago4d?.ready === true || !!window.__chicago4d?.error, null, { timeout: 600000 });
  await page.evaluate(async () => {
    const r = window.__chicago4d.renderer; r.render = () => {};
    const welcome = window.__chicago4d.welcome;
    if (welcome) {
      const deadline = Date.now() + 90_000;
      while (welcome.state !== 'world' && Date.now() < deadline) {
        if (welcome.state === 'welcome') welcome.enter('spawn');
        if (welcome.state !== 'world') await new Promise((res) => setTimeout(res, 100));
      }
    }
    document.getElementById('control-help-gotit')?.click();
  });
  const tag = `${viewport.width}x${viewport.height}`;
  for (const id of ids) {
    const start = picRequests.length;
    await page.evaluate((i) => { window.__chicago4d.pick(i); document.querySelector('#popup [data-pop-tab="evidence"]').click(); }, id);
    await page.waitForFunction(() => !/LOADING IMAGE INDEX/.test(document.querySelector('#popup [data-pop-pane="images"]')?.textContent ?? 'LOADING IMAGE INDEX'), null, { timeout: 30000 });
    const before = picRequests.length - start;
    const pre = await page.evaluate(() => ({
      tabs: [...document.querySelectorAll('#popup .pop-tab')].map((t) => t.textContent.replace(/\s+/g, ' ').trim()),
      srcBeforeOpen: document.querySelectorAll('#popup [data-pop-pane="images"] img[src]').length,
    }));
    if (pre.srcBeforeOpen === 0 && before === 0) ok(`${tag} ${id}: no picture requested before the tab opens`);
    else fail(`${tag} ${id}: ${pre.srcBeforeOpen} imgs had src / ${before} requests before the tab opened`);
    await page.evaluate(() => document.querySelector('#popup [data-pop-tab="images"]').click());
    await page.waitForTimeout(1500);
    const pane = await page.evaluate(() => {
      const p = document.querySelector('#popup [data-pop-pane="images"]');
      const tiles = [...p.querySelectorAll('.pop-pic-tile')];
      return {
        shown: !p.hasAttribute('hidden'),
        status: p.querySelector('.pop-pic-status')?.textContent ?? p.textContent.trim().slice(0, 80),
        imgs: p.querySelectorAll('img[src]').length,
        loaded: [...p.querySelectorAll('img[src]')].filter((i) => i.complete && i.naturalWidth > 0).length,
        maxNatural: Math.max(0, ...[...p.querySelectorAll('img[src]')].map((i) => i.naturalWidth)),
        tilesWithoutCredit: tiles.filter((t) => !t.querySelector('.pop-pic-tile-credit')?.textContent.trim()).length,

        linksWithoutHolder: [...p.querySelectorAll('.pop-pic-list li')].filter((li) => !li.querySelector('.pop-pic-meta')?.textContent.trim()).length,
      };
    });
    results.push(`     ${tag} ${id}: tabs [${pre.tabs.join(' | ')}] — ${pane.status}; ${pane.loaded}/${pane.imgs} images loaded, widest ${pane.maxNatural}px`);
    if (pane.shown && pane.tilesWithoutCredit === 0 && pane.linksWithoutHolder === 0) ok(`${tag} ${id}: every picture shown carries its credit`);
    else fail(`${tag} ${id}: ${JSON.stringify(pane)}`);
    if (pane.maxNatural <= 480) ok(`${tag} ${id}: only thumbnails (≤480 px) are loaded`);
    else fail(`${tag} ${id}: an image ${pane.maxNatural}px wide was loaded`);
    const tiles = await page.locator('#popup .pop-pic-tile').count();
    if (tiles) {
      const which = Math.min(1, tiles - 1);
      await page.evaluate((i) => document.querySelectorAll('#popup .pop-pic-tile')[i].click(), which);
      await page.waitForTimeout(1500);
      const v = await page.evaluate(() => {
        const el = document.querySelector('.pic-viewer');
        const img = el?.querySelector('img');
        return { open: !!el && !el.hidden, count: el?.querySelector('[data-pv-count]')?.textContent,
          credit: !!el?.querySelector('.pop-pic-credit')?.textContent.trim(),
          rights: el?.querySelector('.pop-pic-rights')?.textContent, shown: !!img?.complete && img.naturalWidth > 0 };
      });
      if (v.open && v.count === `${which + 1} / ${tiles}` && v.credit && v.shown) ok(`${tag} ${id}: a tapped thumbnail opens in the viewer with its credit (${v.count}, ${v.rights})`);
      else fail(`${tag} ${id}: viewer ${JSON.stringify(v)}`);
      await page.screenshot({ path: path.join(OUT, `${id}-viewer-${viewport.width < 500 ? 'phone' : 'desktop'}.jpg`), quality: 82, type: 'jpeg' });
      await page.evaluate(() => document.querySelector('.pic-viewer [data-pv-step="1"]').click());
      await page.waitForTimeout(300);
      const next = await page.evaluate(() => document.querySelector('.pic-viewer [data-pv-count]').textContent);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(200);
      const closed = await page.evaluate(() => document.querySelector('.pic-viewer').hidden
        && !document.querySelector('.pic-viewer img').hasAttribute('src'));
      if (next === `${((which + 1) % tiles) + 1} / ${tiles}` && closed) ok(`${tag} ${id}: the arrow steps on, and closing lets the picture go`);
      else fail(`${tag} ${id}: next ${next}, closed ${closed}`);
    }
    await page.evaluate(() => { document.querySelector('#popup').scrollTop = document.querySelector('#popup .pop-tabs').offsetTop - 8; });
    await page.waitForTimeout(300);
    await page.locator('#popup').screenshot({ path: path.join(OUT, `${id}-${viewport.width < 500 ? 'phone' : 'desktop'}.jpg`), quality: 82, type: 'jpeg' });
    await page.evaluate(() => document.querySelector('#popup [data-pop-tab="evidence"]').click());
  }
  if (errors.length) fail(`${tag} ${year}: page errors ${errors.slice(0, 3).join(' | ')}`); else ok(`${tag} ${year}: no page errors`);
  await ctx.close();
}

try {
  for (const vp of [{ width: 1280, height: 800 }, { width: 390, height: 780 }]) {
    await run(vp, '1904', ['glessner_house', 'keith_house_1808_prairie', 'goodman_house_1612_prairie', 'house_1604_prairie']);
    await run(vp, '1835', ['sauganash_hotel']);
  }
} finally {
  await browser.close();
  server.close();
}
console.log(results.join('\n'));
process.exit(results.some((r) => r.startsWith('FAIL')) ? 1 : 0);
