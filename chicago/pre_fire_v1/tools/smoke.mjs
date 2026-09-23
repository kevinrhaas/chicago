/**
 * Smoke test for the Chicago Before the Fire viewer.
 *
 * Drives the real page in a real browser at mobile and desktop widths and fails
 * on any page error. Mobile is a release gate, not a nice-to-have.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/smoke.mjs
 *
 * Serves the published site tree by default so the test exercises what actually
 * ships, including the bare-path redirect. Override with SMOKE_ROOT.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

// Playwright is installed globally here, and ESM does not honour NODE_PATH, so
// resolve the global root and import by absolute path.
async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  // playwright is CommonJS; imported as ESM its exports land under .default
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const ROOT = process.env.SMOKE_ROOT
  || path.resolve(new URL('.', import.meta.url).pathname, '../../../site');
const PORT = Number(process.env.SMOKE_PORT || 4183);
const PREFIX = process.env.SMOKE_PREFIX || '';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp',
};

const failures = [];
const ok = [];
function check(name, cond, detail = '') {
  if (cond) { ok.push(name); console.log(`  pass  ${name}`); }
  else { failures.push(name); console.log(`  FAIL  ${name}${detail ? ` — ${detail}` : ''}`); }
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404); res.end('not found'); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}${PREFIX}/chicago/pre-fire`;
console.log(`serving ${ROOT} on ${PORT}\n`);

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });

for (const [label, viewport] of [
  ['mobile 390x780', { width: 390, height: 780 }],
  ['desktop 1280x800', { width: 1280, height: 800 }],
]) {
  console.log(`${label}:`);
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  // Record the failing URL, not just "404" — a bare status is not actionable.
  page.on('response', (r) => {
    if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`);
  });
  page.on('requestfailed', (r) => {
    // Requests aborted because the page navigated or the test finished are a
    // harness artifact, not a site defect. Everything else counts.
    const why = r.failure()?.errorText || '';
    if (!/ERR_ABORTED/.test(why)) errors.push(`request failed (${why}) ${r.url()}`);
  });
  page.on('console', (m) => {
    const t = m.text();
    // the bare "Failed to load resource" line duplicates the response hook above
    if (m.type() === 'error' && !t.startsWith('Failed to load resource')) errors.push(t);
  });

  // the bare path must not 404 — it used to
  const bare = await page.goto(base, { waitUntil: 'domcontentloaded' });
  check(`${label}: bare path serves (not 404)`, bare.status() === 200, `status ${bare.status()}`);
  await page.waitForURL(/\/viewer\/?$/, { timeout: 5000 }).catch(() => {});
  check(`${label}: bare path redirects to the viewer`, /\/viewer\/?$/.test(page.url()), page.url());

  await page.goto(`${base}/viewer/`, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.querySelectorAll('tbody tr').length > 0,
    { timeout: 15000 }).catch(() => {});

  const rows = await page.locator('tbody tr').count();
  check(`${label}: records table renders`, rows > 0, `${rows} rows`);

  // set the year to 1835 — the year the 4D project reconstructs
  await page.evaluate(() => {
    const el = document.querySelector('input[type=range]');
    el.value = 1835;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(300);
  const rows1835 = await page.locator('tbody tr').count();
  check(`${label}: 1835 shows structures`, rows1835 > 0, `${rows1835} rows`);

  const imgs = await page.locator('tbody img').count();
  check(`${label}: building images render in the table`, imgs > 0, `${imgs} images`);

  // 1834 must offer BOTH sheets, with Wright — the survey — selected ahead of
  // Hathaway, the map drawn from it (T-0801). The mirror held only Hathaway for
  // four months because there was no publish step; these checks are what notices.
  const views1834 = await page.evaluate(async () => {
    const el = document.querySelector('input[type=range]');
    el.value = 1834;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    await new Promise((r) => setTimeout(r, 300));
    const sel = document.getElementById('mapVariant');
    return {
      ids: [...sel.options].map((o) => o.value),
      selected: sel.value,
      note: document.getElementById('mapNote').textContent,
      meta: document.getElementById('mapMeta').textContent,
      src: document.getElementById('mapImage').getAttribute('src'),
    };
  });
  check(`${label}: 1834 offers both sheets`,
    views1834.ids.includes('MAP-1834-WRIGHT') && views1834.ids.includes('MAP-1834-HATHAWAY'),
    views1834.ids.join(', '));
  check(`${label}: Wright is 1834's default view`,
    views1834.selected === 'MAP-1834-WRIGHT', views1834.selected);
  check(`${label}: the Wright sheet carries its provenance`,
    /National Archives/.test(views1834.meta) && /Historic Urban Plans/.test(views1834.meta)
      && /Two portions are missing/.test(views1834.note),
    `${views1834.meta.slice(0, 80)} | ${views1834.note.slice(0, 60)}`);

  // Fetch the sheet by its own path, not by whatever the select happens to show:
  // following views1834.src would pass on the Hathaway image if Wright were missing.
  const WRIGHT_SRC = '../maps/images/1834-wright-map.jpg';
  const wrightImg = await page.evaluate(async (src) =>
    (await fetch(src, { method: 'HEAD' })).status, WRIGHT_SRC);
  check(`${label}: the Wright sheet is served`, wrightImg === 200,
    `status ${wrightImg} for ${WRIGHT_SRC}`);
  check(`${label}: the Wright sheet is what 1834 shows`, views1834.src === WRIGHT_SRC,
    views1834.src);

  // put the year back where the checks below expect it
  await page.evaluate(() => {
    const el = document.querySelector('input[type=range]');
    el.value = 1835;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(300);

  // the new Kurz & Allison sheet must actually load, not 404
  const kurz = await page.evaluate(async () => {
    const r = await fetch('../media/images/buildings/chicago_early_days_kurz_allison.jpg',
                          { method: 'HEAD' });
    return r.status;
  });
  check(`${label}: new reference image is served`, kurz === 200, `status ${kurz}`);

  const noneBroken = await page.evaluate(() =>
    [...document.images].every((i) => !i.complete || i.naturalWidth > 0));
  check(`${label}: no broken images`, noneBroken);

  const noHScroll = await page.evaluate(() =>
    document.documentElement.scrollWidth <= window.innerWidth + 1);
  check(`${label}: no horizontal overflow`, noHScroll);

  check(`${label}: zero page errors`, errors.length === 0, errors.slice(0, 3).join(' | '));
  await ctx.close();
  console.log('');
}

await browser.close();
server.close();

console.log(`${ok.length} passed, ${failures.length} failed`);
if (failures.length) { console.log(`FAILURES: ${failures.join(', ')}`); process.exit(1); }
console.log('SMOKE PASS');
