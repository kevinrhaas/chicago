import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const dataRoot = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
const jaunt = JSON.parse(fs.readFileSync(path.join(dataRoot, 'data/sidecars/1835/jaunts/schoolday-errand.json')));
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname;
  if (pathname === '/') { res.setHeader('Content-Type', 'text/html'); res.end('<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body></body></html>'); return; }
  const file = path.resolve(web, `.${pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : 'text/css' }); res.end(err ? '' : bytes);
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }]) {
    const page = await browser.newPage({ viewport });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.evaluate(async jaunt => {
      const { createJauntPreview } = await import('/js/jaunt-preview.js');
      const root = document.createElement('main'); document.body.append(root);
      window.fixtureSession = { session: 'test-session', phase: 'outcome', jaunt,
        outcome: jaunt.endings.find(ending => ending.completion_eligible),
        visited: jaunt.stops.map(stop => ({ id: stop.id, committed: true })) };
      window.preview = createJauntPreview({ root, dataBase: new URL('/data/', location.href), api: {}, destinations: {},
        getSession: () => window.fixtureSession, onDismiss: () => { window.fixtureSession = null; },
        fetcher: async url => String(url).endsWith('catalog.json')
          ? { ok: true, json: async () => ({ scene: '1835', jaunts: [] }) }
          : { ok: false, status: 404 },
      });
      await window.preview.open();
    }, jaunt);
    const check = page.locator('.jaunt-understanding');
    assert.equal(await check.count(), 1, 'offered on actual completion card');
    assert.equal(await check.getAttribute('open'), null, 'completion card stays compact');
    await check.locator('summary').click();
    assert.equal(await page.locator('textarea').count(), 3);
    // T-3670: the guide's three questions, each a group of real options with one answer.
    assert.equal(await page.locator('.jaunt-check-choices[role="group"]').count(), 3);
    const q1 = page.locator('.jaunt-check-question').first();
    const ids = await q1.locator('.jaunt-check-choice').evaluateAll(bs => bs.map(b => b.dataset.option));
    assert(ids.length === 3, 'three options');
    // Try every option until one is right: wrong ones say "not quite", the right one reveals the sources.
    let solved = false, wrongSeen = 0;
    for (const id of ids) {
      await q1.locator(`.jaunt-check-choice[data-option="${id}"]`).click();
      const said = await q1.locator('.jaunt-check-feedback').textContent();
      if (/^That’s it/.test(said)) { solved = true; break; }
      assert.match(said, /^Not quite/); wrongSeen++;
      assert.equal(await q1.locator(`.jaunt-check-choice[data-option="${id}"]`).getAttribute('aria-pressed'), 'true');
    }
    assert(solved, 'one option is the answer');
    assert.equal(await q1.locator('.jaunt-check-review').isVisible(), true, 'the right answer opens its sources');
    assert.equal(await q1.locator('.jaunt-check-choice:not([disabled])').count(), 0, 'solved stays solved');
    assert.equal(await q1.locator('.jaunt-check-choice.is-right').count(), 1);
    assert.equal(await q1.locator('.jaunt-check-reveal').isVisible(), false, 'nothing to reveal once solved');
    // A second question: two wrong tries offer "Show me the answer".
    const q2 = page.locator('.jaunt-check-question').nth(1);
    const q2ids = await q2.locator('.jaunt-check-choice').evaluateAll(bs => bs.map(b => b.dataset.option));
    let tries = 0;
    for (const id of q2ids) {
      if (tries === 2) break;
      await q2.locator(`.jaunt-check-choice[data-option="${id}"]`).click();
      if (/^Not quite/.test(await q2.locator('.jaunt-check-feedback').textContent())) tries++;
      else break;
    }
    if (tries === 2) {
      assert.equal(await q2.locator('.jaunt-check-reveal').isVisible(), true, 'after two tries the answer can be shown');
      await q2.locator('.jaunt-check-reveal').click();
      assert.equal(await q2.locator('.jaunt-check-choice.is-right').count(), 1);
      assert.equal(await q2.locator('.jaunt-check-review').isVisible(), true);
    }
    await page.locator('textarea').first().fill('<script>not markup</script> My own words');
    await page.getByRole('button', { name: 'Where does this come from?', exact: true }).first().click();
    assert.equal(await page.locator('.jaunt-check-review').first().isVisible(), true);
    assert.equal(await page.locator('.jaunt-check-review a').first().getAttribute('rel'), 'noopener noreferrer');
    await page.getByRole('button', { name: 'Revise your answer', exact: true }).first().click();
    assert.equal(await page.evaluate(() => document.activeElement.dataset.checkAnswer), '0');
    // Going away and returning to the same ending keeps tab-local drafts.
    await page.evaluate(() => window.preview.open());
    assert.match(await page.locator('textarea').first().inputValue(), /My own words/);
    await page.getByRole('button', { name: 'Start these questions again', exact: true }).click();
    assert.equal(await page.locator('textarea').first().inputValue(), '');
    assert.equal(await page.locator('.jaunt-check-choice:disabled').count(), 0, 'starting again re-opens every question');
    assert.equal(await page.locator('.jaunt-check-choice.is-right, .jaunt-check-choice.is-wrong').count(), 0);
    assert.equal(await page.locator('.jaunt-check-review').first().isVisible(), false);
    assert.equal(await page.evaluate(() => document.activeElement.dataset.checkAnswer), '0');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'no horizontal overflow');
    await page.getByRole('button', { name: 'Skip for now', exact: true }).click();
    assert.equal(await check.getAttribute('open'), null);
    assert.equal(await page.evaluate(() => document.activeElement.tagName), 'SUMMARY');
    await page.getByRole('button', { name: 'Close the finished outing', exact: true }).click();
    assert.equal(await check.count(), 0, 'dismiss removes session draft');
    assert.deepEqual(errors, []);
    await page.close();
  }
  console.log('JAUNT UNDERSTANDING VIEW PASS — actual completion integration at 390×780 and 1280×800, guide questions with retry and reveal, typing, source review, draft retention, retry, skip, focus, no overflow/errors');
} finally { await browser.close(); server.close(); }
