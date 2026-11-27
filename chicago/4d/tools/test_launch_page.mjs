/**
 * test_launch_page.mjs — the launch page at /4d/ (T-3798).
 *
 *   node tools/test_launch_page.mjs            the System check's words (portal/launch-check.js) for every
 *                                              kind of computer, and the page itself: four year tiles that
 *                                              are real links, their stills on disk and small, the tools
 *                                              (music, settings, account), the classic console linked
 *                                              (check.sh runs this)
 *   node tools/test_launch_page.mjs --browser  the page served in its published shape, at 1280x800 and
 *                                              390x780: no page error, the check finishes by itself and
 *                                              gives a verdict, a tile click selects and a second click
 *                                              launches, Settings writes the town's own keys, music
 *                                              remembers on/off, no sideways scroll on the phone
 *
 * No smoke part loads the front door, so the browser half is how a change to it is driven.
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { createServer } from 'node:http';
import { fileURLToPath, pathToFileURL } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(APP, 'renderers/web');
const PORTAL = path.join(WEB, 'portal');
const STILL_CAP_KB = 90;
const YEARS = ['1835', '1904', '1812', '1871'];
const fail = (m) => { console.error(`FAIL launch page: ${m}`); process.exit(1); };
const check = (ok, m) => { if (!ok) fail(m); };

// ---- The check's words -------------------------------------------------------------------
const lc = await import(pathToFileURL(path.join(PORTAL, 'launch-check.js')).href);
const { verdictFor, checkRows, gpuWords, networkWords, CLOUD_MIN_MBPS } = lc;
const strong = { score: 82, grade: 'good', detail: 'full', webgl2: true, mbps: 60 };
const weak = { score: 31, grade: 'low', detail: 'balanced', webgl2: true, mbps: 40 };
const poor = { score: 12, grade: 'poor', detail: 'light', webgl2: true, mbps: 40 };
const noCloud = { offered: false, ready: false }, cloudSoon = { offered: true, ready: false }, cloudOn = { offered: true, ready: true };

let v = verdictFor(strong, noCloud);
assert.equal(v.kind, 'ready'); assert.equal(v.title, 'Ready · Full detail'); assert.equal(v.cloud, false);
v = verdictFor({ ...strong, grade: 'peak', score: 95 }, cloudOn);
assert.equal(v.kind, 'ready'); assert.equal(v.cloud, false, 'a strong computer is never pushed to the cloud'); assert.match(v.advice, /at its best/);
v = verdictFor(weak, noCloud);
assert.equal(v.kind, 'lower'); assert.equal(v.detail, 'balanced'); assert.match(v.title, /Balanced detail/); assert.doesNotMatch(v.advice, /cloud/i);
v = verdictFor(weak, cloudSoon);
assert.equal(v.cloud, true); assert.match(v.advice, /opening soon/);
v = verdictFor(poor, noCloud);
assert.equal(v.kind, 'lower'); assert.equal(v.detail, 'light'); assert.match(v.title, /Light detail/);
v = verdictFor(poor, cloudOn);
assert.equal(v.kind, 'cloud'); assert.equal(v.title, 'Cloud play recommended'); assert.match(v.advice, /Play from the cloud/);
v = verdictFor({ ...poor, mbps: CLOUD_MIN_MBPS - 1 }, cloudOn);
assert.equal(v.kind, 'lower', 'a slow link is never sent to the cloud'); assert.equal(v.cloud, false);
v = verdictFor({ ...strong, mbps: 2 }, noCloud);
assert.match(v.advice, /connection is slow/);
v = verdictFor({ ...strong, webgl2: false }, noCloud);
assert.equal(v.kind, 'blocked'); assert.match(v.advice, /Chrome, Edge, Firefox or Safari/);
v = verdictFor({ ...strong, webgl2: false }, cloudOn);
assert.equal(v.kind, 'blocked'); assert.equal(v.cloud, true);
v = verdictFor({ ...strong, software: true }, noCloud);
assert.equal(v.kind, 'lower', 'software drawing is never "ready", whatever the draw test scored'); assert.match(v.advice, /hardware acceleration/);
v = verdictFor({ ...strong, software: true }, cloudOn);
assert.equal(v.kind, 'cloud'); assert.match(v.advice, /or play from the cloud/i);
v = verdictFor(strong, noCloud, 'light');
assert.equal(v.detail, 'light'); assert.equal(v.title, 'Ready · Light detail'); assert.match(v.advice, /You chose Light detail/);
v = verdictFor(strong, noCloud, 'nonsense');
assert.equal(v.title, 'Ready · Full detail', 'an unknown chosen level falls back to the reading');

assert.equal(gpuWords('ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00009BC5) Direct3D11 vs_5_0 ps_5_0, D3D11)'), 'Intel UHD Graphics 630');
assert.equal(gpuWords('ANGLE Metal Renderer: Apple M2'), 'Apple M2');
assert.equal(gpuWords('NVIDIA GeForce RTX 3060/PCIe/SSE2'), 'NVIDIA GeForce RTX 3060');
assert.equal(gpuWords(''), 'not reported');
assert(gpuWords('X'.repeat(60)).length <= 34);
assert.equal(networkWords(NaN), 'not measured');
assert.equal(networkWords(3.24), '3.2 Mbps · slow');
assert.equal(networkWords(12), '12 Mbps · fine');
assert.equal(networkWords(40), '40 Mbps · fast');
assert.equal(networkWords(240), '240+ Mbps · fast');

let rows = checkRows({ signals: { webgl2: true, renderer: 'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00009BC5) Direct3D11 vs_5_0 ps_5_0, D3D11)', cores: 12, memoryGB: 8 } }, { mbps: 40, shared: true });
assert.deepEqual(rows, { gpu: 'Intel UHD Graphics 630 · shares system memory', cpu: '12 cores', memory: '8+ GB', network: '40 Mbps · fast' });
rows = checkRows({ signals: { webgl2: true, renderer: 'SwiftShader' }, why: 'software rasteriser' });
assert.match(rows.gpu, /software drawing/); assert.equal(rows.cpu, 'not reported'); assert.match(rows.memory, /not reported/);
rows = checkRows({ signals: {} });
assert.equal(rows.gpu, 'no 3D drawing in this browser');
console.log('PASS launch check words: ready, lower, cloud and blocked verdicts; chosen detail; slow links; graphics, memory and connection rows');

// ---- The page ----------------------------------------------------------------------------
const html = fs.readFileSync(path.join(PORTAL, 'index.html'), 'utf8');
const tiles = [...html.matchAll(/<a class="year-tile[^"]*" href="(\d{4})\/" data-year="(\d{4})"[^>]*>([^]*?)<\/a>/g)];
check(tiles.length === 4, `expected 4 year tiles, found ${tiles.length}`);
check(tiles.map((t) => t[2]).join() === YEARS.join(), `tiles are ${tiles.map((t) => t[2]).join()}, not ${YEARS.join()}`);
for (const [, href, year, body] of tiles) {
  check(href === year, `${year}'s tile links to ${href}/`);
  check(body.includes(`walk/portal/stills/${year}-800.webp`), `${year}'s tile has no still`);
  for (const f of [`${year}.webp`, `${year}-800.webp`]) {
    const p = path.join(PORTAL, 'stills', f);
    check(fs.existsSync(p), `stills/${f} is missing`);
    const kb = fs.statSync(p).size / 1024;
    check(kb <= STILL_CAP_KB, `stills/${f} is ${kb.toFixed(0)} KB, over the ${STILL_CAP_KB} KB cap`);
  }
}
for (const f of fs.readdirSync(path.join(PORTAL, 'stills'))) check(f === 'SOURCES.md' || /^(1835|1904|1812|1871)(-800)?\.webp$/.test(f), `stills/${f} is shipped but no tile uses it`);
check(!/year-tile is-selected/.test(html) && /<body[^>]*data-selected=""/.test(html), 'a tile starts selected; the page opens on Chicago 4D with no year chosen');
check(/id="play" href="#years"/.test(html) && html.includes('Choose a year</span>'), 'Play must start as "Choose a year", pointing at the years');
for (const id of ['music-toggle', 'settings-open', 'account-open', 'admin-open', 'play', 'play-cloud', 'check', 'check-meter', 'verdict-title', 'hero-verdict', 'settings', 'account', 'admin', 'launching', 's-skins', 'set-detail', 'set-lang', 'set-music', 'admin-body']) {
  check(html.includes(`id="${id}"`), `#${id} is missing`);
}
check((html.match(/<i><\/i>/g) || []).length === 20, 'the meter has twenty segments');
check(/<button[^>]*id="admin-open"[^>]*hidden/.test(html), 'the admin button starts hidden');
check(/<button[^>]*id="play-cloud"[^>]*hidden/.test(html), 'the cloud button starts hidden');
check(html.includes('href="console/"'), 'the classic console is not linked');
check(html.includes('<script type="module" src="walk/portal/launch.js"></script>'), 'launch.js is not loaded');
check(!/data-clips|portal\/clips/.test(html), 'the launch page names clips; it shows stills only');
check(!/\b(ai|gpu|webgl|three\.js|model)\b/i.test(html.replace(/<[^>]+>/g, ' ').replace(/content="[^"]*"/g, '')), 'the page sells technology in its words');
const js = fs.readFileSync(path.join(PORTAL, 'launch.js'), 'utf8');
check(js.includes("record: false"), 'the launch page sign-in must not record a year visit');
check(/MUSIC_KEY = 'chicago4d\.launch\.music'/.test(js), 'the music key changed');
check(js.includes("'chicago4d.settings'") && js.includes("'chicago.lang'"), 'Settings no longer write the town\'s own keys');
console.log(`PASS launch page: ${tiles.length} year tiles with stills, tools, check, dialogs, classic console linked`);

// ---- In a browser ------------------------------------------------------------------------
if (process.argv.includes('--browser')) {
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
    '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg' };
  const server = createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const year = rel.match(/^\/(\d{4})\/$/);
    if (year) { res.writeHead(200, { 'content-type': 'text/html' }); res.end(`<!doctype html><title>${year[1]}</title><p id="arrived">${year[1]}</p>`); return; }
    const file = rel === '/' ? path.join(PORTAL, 'index.html') : rel.startsWith('/walk/') ? path.join(WEB, rel.slice(6)) : null;
    try { const body = fs.readFileSync(file); res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream', 'cache-control': 'no-store' }); res.end(body); }
    catch { res.writeHead(404).end(); }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}/`;
  let ns;
  try { ns = await import('playwright'); } catch { ns = await import(path.join(execSync('npm root -g').toString().trim(), 'playwright', 'index.js')); }
  const { chromium } = ns.chromium ? ns : ns.default;
  const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
  try {
    for (const [name, viewport, phone] of [['desktop', { width: 1280, height: 800 }, false], ['phone', { width: 390, height: 780 }, true]]) {
      const ctx = await browser.newContext({ viewport, isMobile: phone, hasTouch: phone, serviceWorkers: 'block' });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(String(e)));
      await page.goto(base);
      await page.waitForFunction(() => document.getElementById('check').dataset.state === 'done', null, { timeout: 60000 });
      const read = await page.evaluate(() => ({
        verdict: document.getElementById('verdict-title').textContent,
        kind: document.getElementById('check').dataset.verdict || '',
        phase: document.getElementById('check-phase').textContent,
        rows: [...document.querySelectorAll('.check-log li')].map((li) => li.classList.contains('is-read')),
        lit: document.querySelectorAll('.check-meter i.on').length,
        chip: document.getElementById('hero-verdict-text').textContent,
        sideways: document.documentElement.scrollWidth - innerWidth,
        tilesShown: [...document.querySelectorAll('.year-tile')].filter((t) => t.getBoundingClientRect().width > 40).length,
      }));
      check(read.phase === 'COMPLETE' || read.phase === 'NO READING', `${name}: the check ended at ${read.phase}`);
      if (read.phase === 'COMPLETE') {
        check(['ready', 'lower', 'cloud', 'blocked'].includes(read.kind), `${name}: verdict kind ${read.kind}`);
        check(read.rows.every(Boolean), `${name}: not every row was read`);
        check(read.chip === read.verdict, `${name}: the hero chip says "${read.chip}", the check says "${read.verdict}"`);
      }
      check(read.sideways <= 1, `${name}: the page scrolls sideways by ${read.sideways}px`);
      check(read.tilesShown === 4, `${name}: ${read.tilesShown} tiles shown`);
      // No year is chosen at first; Play points at the years and goes nowhere.
      const hero = () => page.evaluate(() => ({ year: document.getElementById('hero-year').textContent, href: document.getElementById('play').getAttribute('href'),
        state: document.getElementById('hero-state').textContent, label: document.getElementById('play-label').textContent,
        selected: document.querySelectorAll('.year-tile.is-selected').length }));
      assert.deepEqual(await hero(), { year: 'Chicago 4D', href: '#years', state: 'STANDING BY', label: 'Choose a year', selected: 0 }, `${name}: the page opens on no year`);
      const playAt = () => page.evaluate(() => { const r = document.getElementById('play').getBoundingClientRect(); return { y: r.top + scrollY, height: r.height }; });
      const playBox = await playAt();
      await page.locator('#play').click();
      await page.waitForTimeout(300);
      check(page.url() === base && (await hero()).selected === 0, `${name}: Play with no year chose one or left the page`);
      if (!phone) {
        // A resting mouse fades only the backdrop; the words stay.
        await page.locator('.year-tile[data-year="1812"]').hover();
        await page.waitForTimeout(500);
        check((await hero()).year === 'Chicago 4D', `${name}: hovering a tile changed the hero's words`);
        check(await page.evaluate(() => document.querySelector('.backdrop-still.is-on')?.getAttribute('src')?.endsWith('/1812.webp')), `${name}: hovering 1812 did not fade its still in`);
      }
      // First click selects, second launches.
      await page.locator('.year-tile[data-year="1835"]').click();
      await page.waitForTimeout(600);
      assert.deepEqual(await hero(), { year: '1835', href: '1835/', state: 'LOCK NOMINAL', label: 'Play 1835', selected: 1 }, `${name}: selecting 1835`);
      const playAfter = await playAt();
      check(Math.abs(playAfter.y - playBox.y) < 1 && Math.abs(playAfter.height - playBox.height) < 1, `${name}: choosing a year moved Play from y ${playBox.y} to ${playAfter.y}`);
      if (!phone) {
        await page.mouse.move(5, 5);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(600);
        check((await hero()).selected === 0 && (await hero()).year === 'Chicago 4D', `${name}: Escape did not go back to no year`);
        await page.locator('.year-tile[data-year="1835"]').click();
        await page.waitForTimeout(600);
      }
      // Settings write the town's own keys.
      await page.locator('#settings-open').click();
      await page.locator('#set-detail').selectOption('light');
      await page.locator('#set-lang').selectOption('es');
      const keys = await page.evaluate(() => ({ town: JSON.parse(localStorage.getItem('chicago4d.settings') || '{}'), lang: localStorage.getItem('chicago.lang'),
        skins: document.querySelectorAll('#s-skins .skin-tile').length }));
      check(keys.town.detail === 'light', `${name}: Scene detail wrote ${JSON.stringify(keys.town)}`);
      check(keys.lang === 'es', `${name}: Language wrote ${keys.lang}`);
      check(keys.skins >= 4, `${name}: ${keys.skins} appearance tiles`);
      if (read.phase === 'COMPLETE') check((await page.locator('#verdict-title').textContent()).includes('Light'), `${name}: the verdict ignores the chosen detail`);
      await page.keyboard.press('Escape');
      // Music remembers on and off.
      await page.locator('#music-toggle').click();
      check(await page.evaluate(() => localStorage.getItem('chicago4d.launch.music')) === 'on', `${name}: music on not remembered`);
      check(await page.locator('#music-toggle').getAttribute('aria-pressed') === 'true', `${name}: music button not pressed`);
      await page.locator('#music-toggle').click();
      check(await page.evaluate(() => localStorage.getItem('chicago4d.launch.music')) === 'off', `${name}: music off not remembered`);
      // T-3797: everyone sees the cloud button; signed out, it is the waitlist, and asks for a sign-in.
      check(await page.locator('#play-cloud').isVisible(), `${name}: the cloud button is hidden`);
      check(await page.locator('#play-cloud span').textContent() === 'Join the cloud waitlist', `${name}: signed out, the cloud button is not the waitlist`);
      await page.locator('#play-cloud').click();
      await page.waitForFunction(() => document.getElementById('account').open, null, { timeout: 15000 });
      await page.keyboard.press('Escape');
      // The account sheet opens; off the live hosts it says sign-in is off here.
      await page.locator('#account-open').click();
      await page.waitForFunction(() => /Sign-in is off/.test(document.getElementById('account-note').textContent), null, { timeout: 15000 });
      await page.keyboard.press('Escape');
      await page.locator('.year-tile[data-year="1835"]').click();
      await page.waitForURL(`${base}1835/`, { timeout: 10000 });
      check(!errors.length, `${name}: page errors: ${errors.join(' | ')}`);
      console.log(`PASS launch page in the browser, ${name}: check ${read.phase.toLowerCase()} (${read.verdict}), select then launch, settings, music, account`);
      await ctx.close();
    }
  } finally { await browser.close(); server.close(); }
}
