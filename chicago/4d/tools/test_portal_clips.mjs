/**
 * test_portal_clips.mjs — the home page's destination clips (T-2685).
 *
 *   node tools/test_portal_clips.mjs            the files: every clip a card names exists in both
 *                                               formats, nothing on disk is unnamed, and the weight
 *                                               stays inside its cap (check.sh runs this)
 *   node tools/test_portal_clips.mjs --browser  the page: at 1440x1000 and 390x780 each card fetches
 *                                               exactly one clip and plays it in black and white,
 *                                               with no page error;
 *                                               with reduced motion no clip is fetched at all
 *
 * No smoke part loads the Observatory, so the browser half is how a change to the
 * portal is driven before it ships. Playwright's Chromium has no H.264, so it plays
 * the WebM; the MP4s are what Safari and every iPhone browser get.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORTAL = path.join(APP, 'renderers/web/portal');
const CLIPS = path.join(PORTAL, 'clips');
// A visitor fetches three clips, one per card; the cap keeps each one a small download.
const CLIP_CAP_KB = 300;
const TOTAL_CAP_MB = 5;
const fail = (m) => { console.error(`FAIL portal clips: ${m}`); process.exit(1); };

const html = fs.readFileSync(path.join(PORTAL, 'index.html'), 'utf8');
if (!html.includes('<script src="walk/portal/clips.js" defer></script>')) fail('index.html does not load walk/portal/clips.js');
const cards = [...html.matchAll(/data-year="(\d{4})"[^]*?data-clips="([^"]*)"/g)].map(m => ({ year: m[1], names: m[2].split(',').filter(Boolean) }));
if (cards.length !== 3) fail(`expected 3 cards naming clips, found ${cards.length}`);
const named = new Set();
for (const { year, names } of cards) {
  if (names.length < 3) fail(`${year} names ${names.length} clips; the library is at least three`);
  const shots = JSON.parse(fs.readFileSync(path.join(APP, 'tools/portal_clips', `${year}.json`), 'utf8')).shots.map(s => `${year}-${s.id}`);
  for (const n of names) {
    if (!n.startsWith(`${year}-`)) fail(`${year}'s card names ${n}, another year's clip`);
    if (!shots.includes(n)) fail(`${n} is on the card but not in tools/portal_clips/${year}.json, so it cannot be re-filmed`);
    for (const ext of ['mp4', 'webm']) if (!fs.existsSync(path.join(CLIPS, `${n}.${ext}`))) fail(`${n}.${ext} is missing`);
    named.add(n);
  }
}
let total = 0;
for (const f of fs.readdirSync(CLIPS)) {
  const stem = f.replace(/\.(mp4|webm)$/, '');
  if (stem === f) fail(`clips/${f} is neither MP4 nor WebM`);
  if (!named.has(stem)) fail(`clips/${f} is shipped but no card names it`);
  const kb = fs.statSync(path.join(CLIPS, f)).size / 1024;
  if (kb > CLIP_CAP_KB) fail(`clips/${f} is ${kb.toFixed(0)} KB, over the ${CLIP_CAP_KB} KB cap`);
  total += kb;
}
if (total / 1024 > TOTAL_CAP_MB) fail(`clips weigh ${(total / 1024).toFixed(2)} MB, over the ${TOTAL_CAP_MB} MB cap`);
console.log(`PASS portal clips: ${named.size} clips across ${cards.map(c => `${c.year} (${c.names.length})`).join(', ')}, both formats, ${(total / 1024).toFixed(2)} MB`);

if (process.argv.includes('--browser')) {
  // Served in the published shape: the Observatory at the root, the renderer at walk/.
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.jpg': 'image/jpeg',
    '.webm': 'video/webm', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
  const server = createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const file = rel === '/' ? path.join(PORTAL, 'index.html')
      : rel.startsWith('/walk/') ? path.join(APP, 'renderers/web', rel.slice(6)) : null;
    try { const body = fs.readFileSync(file); res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' }); res.end(body); }
    catch { res.writeHead(404).end(); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}/`;
  let ns;
  try { ns = await import('playwright'); } catch { ns = await import(path.join(execSync('npm root -g').toString().trim(), 'playwright', 'index.js')); }
  const { chromium } = ns.chromium ? ns : ns.default;
  const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
  for (const [name, viewport, reducedMotion] of [['desktop', { width: 1440, height: 1000 }, 'no-preference'],
    ['phone', { width: 390, height: 780 }, 'no-preference'], ['reduced', { width: 1440, height: 1000 }, 'reduce']]) {
    const ctx = await browser.newContext({ viewport, reducedMotion, isMobile: name === 'phone', hasTouch: name === 'phone' });
    const page = await ctx.newPage();
    const errors = [], fetched = [];
    page.on('pageerror', e => errors.push(String(e)));
    page.on('request', q => { if (/\/portal\/clips\//.test(q.url())) fetched.push(q.url().split('/').pop()); });
    await page.goto(base);
    await page.evaluate(() => document.querySelector('.era-grid').scrollIntoView());
    await page.waitForTimeout(5000);
    // The phone stacks the cards: walk each into view so each one gets its turn to play.
    for (const i of [1, 2]) { await page.evaluate(n => document.querySelectorAll('.era')[n].scrollIntoView(), i); await page.waitForTimeout(1500); }
    const feeds = await page.evaluate(() => [...document.querySelectorAll('.era-plate')].map(p => p.dataset.feed || 'none'));
    // Kevin wants the footage in black and white (T-2734): every feed, and its blocky frames, is grayscale.
    const tones = await page.evaluate(() => [...document.querySelectorAll('.era-feed,.era-feed-blocks')].map(e => getComputedStyle(e).filter));
    if (errors.length) fail(`${name}: page errors: ${errors.join(' | ')}`);
    if (reducedMotion === 'reduce') {
      if (fetched.length) fail(`${name}: reduced motion fetched ${fetched.join(', ')}`);
      if (feeds.some(f => f !== 'none')) fail(`${name}: reduced motion built a feed (${feeds.join(', ')})`);
    } else {
      if (fetched.length !== 3 || new Set(fetched.map(f => f.slice(0, 4))).size !== 3) fail(`${name}: expected one clip per card, fetched ${fetched.join(', ') || 'none'}`);
      if (fetched.some(f => !f.endsWith('.webm'))) fail(`${name}: this Chromium plays WebM, but it fetched ${fetched.join(', ')}`);
      if (feeds.some(f => f !== 'live')) fail(`${name}: feeds are ${feeds.join(', ')}, not all live`);
      if (tones.length !== 6 || tones.some(t => !t.includes('grayscale(1)'))) fail(`${name}: the feeds are not black and white (${tones.join(' | ')})`);
    }
    console.log(`PASS portal clips in the page, ${name}: ${reducedMotion === 'reduce' ? 'stills only, nothing fetched' : `${fetched.join(', ')} playing`}`);
    await ctx.close();
  }
  await browser.close();
  server.close();
}
