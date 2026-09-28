/**
 * Smoke test for Atlas notes (site/notes/) on every documentation page.
 *
 * Serves site/ at the root, injects a fake notes database (window.ATLAS_NOTES_DB)
 * and answers its four RPCs in memory with the same rules setup.sql enforces:
 * readers get non-archived notes with no IP; a valid edit token gets everything
 * and may add / archive / restore; a bad token is refused. Then it drives the real
 * pages at 390×780 and 1280×800 and fails on any page error.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node chicago/atlas-notes/smoke.mjs            (SHOTS=dir to save screenshots)
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); }
  catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const ROOT = path.resolve(new URL('.', import.meta.url).pathname, '../../site');
const PORT = Number(process.env.SMOKE_PORT || 4191);
const SHOTS = process.env.SHOTS || '';
const TOKEN = 'a'.repeat(64);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml' };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let file = path.join(ROOT, p);
  if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
    if (!p.endsWith('/')) { res.writeHead(301, { Location: p + '/' }); return res.end(); }
    file = path.join(file, 'index.html');
  }
  if (!fs.existsSync(file)) { res.writeHead(404); return res.end('404'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(PORT);

// ---- the fake database: setup.sql's rules, in memory --------------------------
let rows = [], seq = 0;
const EDITOR = 'Bill Tyre';
function answer(fn, a) {
  const editor = a.p_token ? (a.p_token === TOKEN ? EDITOR : false) : null;
  if (editor === false || (fn !== 'notes_list' && !editor)) return [401, { code: '28P01', message: 'notes: edit link not recognised' }];
  const out = r => editor ? r : { ...r, ip: null, ua: null, device: null, archived_by: null };
  if (fn === 'notes_whoami') return [200, { name: EDITOR }];
  if (fn === 'notes_list') return [200, rows.filter(r => r.page === a.p_page && (editor || !r.archived_at)).map(out)];
  if (fn === 'notes_add') {
    const r = { id: 'n' + ++seq, page: a.p_page, target: a.p_target, target_label: a.p_label, body: a.p_body.trim(), author: EDITOR, created_at: new Date(Date.now() + seq).toISOString(), archived_at: null, archived_by: null, ip: '203.0.113.7', ua: 'Mozilla/5.0 (iPhone) Safari/605', device: a.p_device, path: a.p_path };
    rows.unshift(r); return [200, [r]];
  }
  if (fn === 'notes_archive') {
    const r = rows.find(x => x.id === a.p_id); if (!r) return [200, []];
    r.archived_at = a.p_archive ? new Date().toISOString() : null; r.archived_by = a.p_archive ? EDITOR : null; return [200, [r]];
  }
  return [404, {}];
}

let failures = 0, passes = 0;
const check = (ok, label, detail = '') => { if (ok) passes++; else failures++; console.log((ok ? '  pass  ' : '  FAIL  ') + label + (ok || !detail ? '' : ' — ' + detail)); };

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const base = `http://127.0.0.1:${PORT}`;

async function session(viewport, { token = null } = {}) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  await context.addInitScript(() => { window.ATLAS_NOTES_DB = { url: 'https://notes.test', key: 'sb_publishable_test' }; });
  await context.route('https://notes.test/**', async route => {
    const fn = route.request().url().split('/rpc/')[1];
    const [status, body] = answer(fn, JSON.parse(route.request().postData() || '{}'));
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => { if (r.status() >= 400 && !r.url().startsWith('https://notes.test')) errors.push('HTTP ' + r.status() + ' ' + r.url()); });
  return { context, page, errors, token };
}
const visible = (page, sel) => page.locator(sel).evaluateAll(els => els.filter(e => e.offsetParent !== null || getComputedStyle(e).position === 'fixed').length);
const noOverflow = page => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
const shot = async (page, name) => { if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true }); await page.screenshot({ path: path.join(SHOTS, name + '.png') }); } };

for (const [tag, viewport] of [['mobile 390x780', { width: 390, height: 780 }], ['desktop 1280x800', { width: 1280, height: 800 }]]) {
  console.log(tag + ':');
  rows = []; seq = 0;

  // 1. A reader on a page with no notes: nothing extra shows.
  let s = await session(viewport);
  await s.page.goto(base + '/prairie-1904/viewer/');
  await s.page.waitForSelector('#buildingList details');
  await s.page.waitForFunction(() => document.documentElement.classList.contains('an-ready'));
  check(await visible(s.page, '.an-pencil') === 0, `${tag}: reader sees no pencils when there are no notes`);
  check(await s.page.locator('.an-toggle').isHidden(), `${tag}: reader sees no Notes button when there are no notes`);
  await shot(s.page, tag.split(' ')[0] + '-prairie-reader-empty');
  check(await noOverflow(s.page), `${tag}: prairie has no horizontal overflow`);
  check(!s.errors.length, `${tag}: reader page — zero page errors`, s.errors.join(' | '));
  await s.context.close();

  // 2. An editor arrives on their edit link.
  s = await session(viewport);
  await s.page.goto(base + '/prairie-1904/viewer/?notes=' + TOKEN + '#buildings');
  await s.page.waitForFunction(() => document.documentElement.classList.contains('an-editor'));
  check(!s.page.url().includes(TOKEN) && s.page.url().endsWith('#buildings'), `${tag}: the token leaves the address bar, the hash stays`, s.page.url());
  check(await s.page.evaluate(t => localStorage.getItem('atlas.notes.token') === t, TOKEN), `${tag}: the token is kept on this device`);
  const cards = await s.page.locator('#buildingList details').count();
  check(await visible(s.page, '#buildingList details .an-pencil') === cards, `${tag}: editor sees a pencil on every building card`, cards + ' cards');
  check(await visible(s.page, '#sourceList .an-pencil') > 0 && await visible(s.page, '#glessnerSections .an-pencil') > 0 && await visible(s.page, 'h2 .an-pencil') === 6 && await visible(s.page, '#mapTitle .an-pencil') === 1,
    `${tag}: pencils on sources, Glessner sections, the six section headings and the map`);
  check(await s.page.locator('.tabs-band .an-toggle').isVisible(), `${tag}: the Notes button sits in the tab band`);
  await shot(s.page, tag.split(' ')[0] + '-prairie-editor');

  const card = s.page.locator('#buildingList details').first();
  const cardName = await card.locator('summary h3').textContent();
  await card.locator('.an-pencil').click();
  check(await card.evaluate(d => !d.open), `${tag}: clicking a pencil does not open or close the card`);
  check(await s.page.locator('.an-panel').isVisible(), `${tag}: the notes panel opens`);
  check((await s.page.locator('.an-title').textContent()) === cardName, `${tag}: the panel is titled for the card`);
  await s.page.locator('.an-panel textarea').fill('Check the porch against the 1886 Robinson sheet.');
  await s.page.locator('.an-save').click();
  await s.page.waitForSelector('.an-panel .an-note');
  const note = s.page.locator('.an-panel .an-note').first();
  check((await note.locator('.an-body').textContent()) === 'Check the porch against the 1886 Robinson sheet.', `${tag}: the note is saved and listed`);
  check((await note.locator('strong').textContent()) === EDITOR, `${tag}: the note is signed by the editor from the database`);
  check(/IP 203\.0\.113\.7/.test(await note.locator('.an-meta').first().textContent()), `${tag}: the editor sees the IP / browser line`);
  check((await card.locator('.an-pencil .an-n').textContent()) === '1', `${tag}: the card's pencil shows the count`);
  check((await s.page.locator('.an-toggle .an-n').textContent()) === '1', `${tag}: the Notes button shows the page count`);
  await shot(s.page, tag.split(' ')[0] + '-prairie-panel');
  await s.page.locator('.an-panel textarea').fill('A second thought.');
  await s.page.keyboard.press('Control+Enter');
  await s.page.waitForFunction(() => document.querySelectorAll('.an-panel .an-note').length === 2);
  check(true, `${tag}: Ctrl+Enter saves`);
  await s.page.locator('.an-panel .an-note').first().getByRole('button', { name: 'Archive' }).click();
  await s.page.waitForFunction(() => document.querySelectorAll('.an-panel .an-note').length === 1);
  check(await s.page.getByRole('button', { name: 'Show archived (1)' }).isVisible(), `${tag}: an archived note leaves the list and is offered under "Show archived"`);
  await s.page.getByRole('button', { name: 'Show archived (1)' }).click();
  check(await s.page.locator('.an-archived').count() === 1, `${tag}: the archived note is still readable by the editor`);
  await s.page.locator('.an-archived').getByRole('button', { name: 'Restore' }).click();
  await s.page.waitForFunction(() => document.querySelectorAll('.an-panel .an-note:not(.an-archived)').length === 2);
  check(true, `${tag}: restore brings it back`);
  await s.page.locator('.an-panel .an-note').first().getByRole('button', { name: 'Archive' }).click(); // leave one archived
  await s.page.keyboard.press('Escape');
  check(await s.page.locator('.an-panel').isHidden(), `${tag}: Escape closes the panel`);

  // The page-level panel indexes the notes elsewhere, and jumps to them.
  await s.page.locator('.an-toggle').click();
  await s.page.locator('.an-panel textarea').fill('Whole-page note.');
  await s.page.locator('.an-save').click();
  await s.page.waitForSelector('.an-index-item');
  await s.page.locator('.an-index-item').first().click();
  check((await s.page.locator('.an-title').textContent()) === cardName, `${tag}: the page index opens that card's notes`);
  await s.page.getByRole('button', { name: /Show it on the page/ }).click();
  await s.page.waitForTimeout(700);
  check(await card.evaluate(d => d.open && Math.abs(d.getBoundingClientRect().top) < innerHeight), `${tag}: "show it on the page" opens and reveals the card`);
  check(!s.errors.length, `${tag}: editor page — zero page errors`, s.errors.join(' | '));
  await s.context.close();

  // 3. A reader now sees exactly the live notes, read-only.
  s = await session(viewport);
  await s.page.goto(base + '/prairie-1904/viewer/');
  await s.page.waitForFunction(() => document.documentElement.classList.contains('an-ready') && document.querySelector('.an-toggle .an-n').textContent === '2');
  check(await visible(s.page, '.an-pencil') === 1, `${tag}: reader sees a pencil only on the card that has a note`);
  await s.page.locator('#buildingList .an-pencil.an-has').click();
  check(await s.page.locator('.an-panel .an-note').count() === 1 && await s.page.locator('.an-archived').count() === 0, `${tag}: reader sees the live note, not the archived one`);
  check(await s.page.locator('.an-panel textarea, .an-panel button:has-text("Archive")').count() === 0, `${tag}: reader cannot add or archive`);
  check(await s.page.locator('.an-panel .an-meta').count() === 0, `${tag}: reader does not see the IP / browser line`);
  await shot(s.page, tag.split(' ')[0] + '-prairie-reader-panel');
  check(!s.errors.length, `${tag}: reader page with notes — zero page errors`, s.errors.join(' | '));
  await s.context.close();

  // 4. A wrong link is refused and forgotten.
  s = await session(viewport);
  await s.page.goto(base + '/prairie-1904/viewer/?notes=not-a-real-token');
  await s.page.waitForFunction(() => document.documentElement.classList.contains('an-ready') && !document.querySelector('.an-toggle').hidden);
  check(!(await s.page.evaluate(() => document.documentElement.classList.contains('an-editor'))) && await s.page.evaluate(() => localStorage.getItem('atlas.notes.token') === null), `${tag}: a wrong edit link gives read-only access and is not kept`);
  await s.page.locator('.an-toggle').click();
  check(/not recognised/.test(await s.page.locator('.an-panel').textContent()), `${tag}: and says so`);
  await s.context.close();

  // 5. The other documentation pages, as an editor.
  s = await session(viewport);
  await s.page.goto(base + '/?notes=' + TOKEN);
  await s.page.waitForFunction(() => document.documentElement.classList.contains('an-editor'));
  check(await s.page.locator('.an-fab').isVisible(), `${tag}: landing page — floating Notes button for editors`);
  check(await noOverflow(s.page), `${tag}: landing page — no horizontal overflow`);
  for (const [url, rowSel] of [['/pre-fire/viewer/', '#buildingRows td[data-note]'], ['/rebuilding-1870s/viewer/', '#buildingRows td[data-note]']]) {
    await s.page.goto(base + url);
    await s.page.waitForSelector(rowSel);
    await s.page.waitForFunction(() => document.documentElement.classList.contains('an-editor'));
    check(await visible(s.page, rowSel + ' .an-pencil') > 0 && await visible(s.page, '#mapTitle .an-pencil') === 1, `${tag}: ${url} — pencils on rows and the map`);
    await s.page.locator('#year').evaluate(el => { el.value = el.max; el.dispatchEvent(new Event('input')); });
    check(await visible(s.page, '#mapTitle .an-pencil') === 1, `${tag}: ${url} — the map pencil survives a year change`);
    await s.page.locator(rowSel + ' .an-pencil').first().click();
    await s.page.locator('.an-panel textarea').fill('Row note on ' + url);
    await s.page.locator('.an-save').click();
    await s.page.waitForSelector('.an-panel .an-note');
    check((await s.page.locator(rowSel + ' .an-pencil .an-n').first().textContent()) === '1', `${tag}: ${url} — a row note saves and counts`);
    await shot(s.page, tag.split(' ')[0] + url.split('/')[1] + '-panel');
    await s.page.keyboard.press('Escape');
    check(await noOverflow(s.page), `${tag}: ${url} — no horizontal overflow`);
  }
  check(!s.errors.length, `${tag}: other pages — zero page errors`, s.errors.join(' | '));
  await s.context.close();
}

await browser.close();
server.close();
console.log(`\n${passes} passed, ${failures} failed`);
if (failures) process.exit(1);
console.log('NOTES SMOKE PASS');
