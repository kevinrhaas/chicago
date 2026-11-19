/** Published pre-fire viewer + 1871 research browser checks.
 * Run: PW_EXECUTABLE=/usr/bin/chromium node tools/smoke_research.mjs
 * The atlas notes API is stubbed: these checks exercise static research, not notes.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(process.env.SMOKE_ROOT || fileURLToPath(new URL('../../../site/', import.meta.url)));
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  let file;
  try { file = path.resolve(ROOT, '.' + decodeURIComponent(new URL(req.url, 'http://local').pathname)); }
  catch { res.writeHead(400); res.end(); return; }
  if (!file.startsWith(ROOT + path.sep) && file !== ROOT) { res.writeHead(403); res.end(); return; }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file)) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'content-type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const viewerURL = `${origin}/pre-fire/viewer/`;
let browser;
let passed = 0;
function check(condition, message) { assert.ok(condition, message); passed++; console.log(`PASS ${message}`); }
async function noOverflow(page, label) {
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${label}: no horizontal overflow`);
}

try {
  browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined), headless: true });
  const model = JSON.parse(fs.readFileSync(path.join(ROOT, 'pre-fire/viewer/research-1871.json'), 'utf8'));
  check(model.cards.length > 0, 'published dossier contains research cards');
  for (const [label, viewport] of [['mobile', { width: 390, height: 780 }], ['desktop', { width: 1280, height: 800 }]]) {
    const context = await browser.newContext({ viewport });
    await context.route('https://*.supabase.co/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('response', response => {
      if (response.url().startsWith(origin) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    await page.goto(`${origin}/pre-fire`, { waitUntil: 'domcontentloaded' });
    await page.waitForURL(/\/pre-fire\/viewer\/$/);
    await page.waitForFunction(() => Number(document.getElementById('activeCount')?.textContent.replaceAll(',', '')) > 0);
    check(await page.locator('#buildingRows tr').count() > 0, `${label}: original viewer renders records`);
    await page.locator('button[data-year="1871"]').click();
    check(await page.locator('#yearOutput').textContent() === '1871', `${label}: original year selection works`);
    check(await page.locator('#buildingRows tr').count() > 0, `${label}: 1871 retains structure index`);
    await noOverflow(page, `${label} viewer`);
    const researchLink = page.locator('a[href*="research.html"]').first();
    check(await researchLink.count() === 1, `${label}: viewer links to research`);
    await researchLink.click();
    await page.waitForSelector('details.research-card');
    const cards = page.locator('details.research-card:visible');
    check(await cards.count() === model.cards.length, `${label}: every research card is visible initially`);
    check(await page.locator('#year-audit .audit-card').count() === model.year_audit.length, `${label}: all year audits render`);
    check(await page.locator('#readiness .readiness-card').count() === model.readiness.length, `${label}: all readiness tasks render`);
    const downloads = await page.evaluate(async () => Promise.all([...document.querySelectorAll('a[download]')].map(async link => ({ href: link.getAttribute('href'), status: (await fetch(link.href)).status }))));
    check(downloads.length >= 2 && downloads.every(item => item.status === 200), `${label}: JSON and annual coverage downloads are served`);
    await noOverflow(page, `${label} research`);

    const first = model.cards[0];
    await page.locator('#research-search').fill(first.title);
    check(await cards.count() > 0 && await page.locator(`#claim-${first.id}`).isVisible(), `${label}: title search finds its card`);
    const sourceTitle = first.sources[0].title;
    await page.locator('#research-search').fill(sourceTitle);
    check(await page.locator(`#claim-${first.id}`).isVisible(), `${label}: source search finds cited card`);
    await page.locator('#research-search').fill('unfindable-research-query-9ba782');
    check(await cards.count() === 0 && await page.locator('#empty-state').isVisible(), `${label}: empty search states no matches`);
    await page.locator('#clear-filters').click();
    check(await cards.count() === model.cards.length, `${label}: clear restores every card`);

    const category = first.category;
    await page.locator('#category').selectOption(category);
    check(await cards.count() === model.cards.filter(card => card.category === category).length, `${label}: category filter returns only its category`);
    const status = first.evidence_status;
    await page.locator('#evidence').selectOption(status);
    check(await cards.count() === model.cards.filter(card => card.category === category && card.evidence_status === status).length, `${label}: category and evidence filters combine`);
    check(new URL(page.url()).searchParams.get('evidence') === status, `${label}: filter state is shareable`);
    await page.locator('#clear-filters').click();
    await page.locator('#expand-all').click();
    check(await page.locator('details.research-card[open]').count() === model.cards.length, `${label}: expand reveals all evidence`);
    const firstBody = page.locator(`#claim-${first.id} .card-body`);
    check((await firstBody.textContent()).includes(first.sources[0].locator), `${label}: source locator is readable`);
    const sourceLinks = firstBody.locator('a[href^="https://"]');
    check(await sourceLinks.count() > 0, `${label}: citations link to sources`);
    for (const card of model.cards) {
      const references = card.sources.filter(source => source.reference_image).map(source => source.reference_image);
      for (const [index, reference] of references.entries()) {
        const figure = page.locator(`#claim-${card.id} .source-image`).nth(index);
        const img = figure.locator('img');
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(image => image.decode());
        check(await img.getAttribute('alt') === reference.alt && await img.evaluate(image => image.naturalWidth > 0), `${label}: reference image loads with descriptive alt text`);
        check((await figure.innerText()).includes(reference.caption) && (await figure.innerText()).includes(reference.credit) && (await figure.innerText()).includes(reference.rights), `${label}: reference caption, credit and rights are visible`);
        const file = await context.request.get(new URL(reference.local_image, viewerURL).href);
        const bytes = await file.body();
        check(file.ok() && bytes.length === reference.bytes && createHash('sha256').update(bytes).digest('hex') === reference.sha256, `${label}: served reference is the exact documented file`);
      }
    }
    await noOverflow(page, `${label} expanded research`);
    await page.locator('#collapse-all').click();
    check(await page.locator('details.research-card[open]').count() === 0, `${label}: collapse works`);

    await page.goto(`${viewerURL}research.html?q=unfindable-research-query-9ba782#claim-${first.id}`);
    await page.waitForSelector(`#claim-${first.id}[open]`);
    check(await page.locator(`#claim-${first.id}`).isVisible(), `${label}: direct evidence link overrides conflicting search`);
    check(errors.length === 0, `${label}: zero page errors and local asset failures (${errors.join('; ')})`);
    if (process.env.SMOKE_SCREENSHOT_DIR) {
      fs.mkdirSync(process.env.SMOKE_SCREENSHOT_DIR, { recursive: true });
      await page.goto(`${viewerURL}research.html`);
      await page.waitForSelector('details.research-card');
      await page.screenshot({ path: path.join(process.env.SMOKE_SCREENSHOT_DIR, `prefire-research-${label}.png`), fullPage: false });
    }
    await context.close();
  }
  const failedContext = await browser.newContext({ viewport: { width: 390, height: 780 } });
  await failedContext.route('**/research-1871.json*', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  const failedPage = await failedContext.newPage();
  const loadErrors = [];
  failedPage.on('pageerror', error => loadErrors.push(String(error)));
  await failedPage.goto(`${viewerURL}research.html`);
  await failedPage.waitForSelector('#load-status.load-error');
  check(await failedPage.locator('#load-status').isVisible(), 'failed data request exposes a visible error');
  check(loadErrors.length === 0, 'failed data request does not throw an uncaught error');
  await failedContext.close();
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
console.log(`SMOKE PASS: ${passed} checks`);
