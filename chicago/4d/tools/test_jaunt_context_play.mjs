#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const root = path.resolve('../../site/4d'), out = path.resolve('docs/performance/jaunt-context');
fs.mkdirSync(out, { recursive: true });
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname;
  const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  for (const width of [390, 1280].filter(w => !process.env.JAUNT_VIEWPORT || String(w) === process.env.JAUNT_VIEWPORT)) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 }, hasTouch: width === 390, isMobile: width === 390, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [], records = [];
    page.setDefaultTimeout(90000); page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1835&seed=1257`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 180000 });
    await page.evaluate(() => __chicago4d.setDetail('light'));
    assert(await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago', { mode: 'instantly' })));
    const atStop = () => page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop');
    const snapshot = () => page.evaluate(() => {
      const s = __chicago4d.jaunts.state;
      return { stopIndex: s.stopIndex, choice: s.choice, vars: s.vars, inventory: s.inventory, events: s.events,
        estimate: s.estimate, scroll: document.querySelector('.jaunt-body').scrollTop };
    });
    async function click(locator) {
      await locator.waitFor({ state: 'visible' });
      const point = await locator.evaluate(el => {
        el.scrollIntoView({ block: 'nearest' });
        const r = el.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2;
        if (el.disabled || !el.contains(document.elementFromPoint(x, y))) throw new Error('Control is covered or disabled');
        return { x, y };
      });
      await page.mouse.click(point.x, point.y);
    }
    async function layout(id) {
      const boxes = await page.evaluate(id => {
        const rect = el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
        return { card: rect(document.getElementById(id)), nav: rect(document.querySelector('.jaunt-bar')),
          viewport: { width: innerWidth, height: innerHeight }, bodyWidth: document.body.scrollWidth };
      }, id);
      const { card: a, nav: b, viewport } = boxes;
      assert(a.w > 0 && a.h > 0 && b.h > 0, JSON.stringify(boxes));
      assert(a.y >= 0 && a.y + a.h <= b.y + 1, JSON.stringify(boxes));
      assert(b.y + b.h <= viewport.height - 79, 'navigation clears the walking-control floor');
      assert(boxes.bodyWidth <= viewport.width + 1, JSON.stringify(boxes));
      return boxes;
    }
    await atStop(); console.log(`CONTEXT ${width}: scene ready`);
    for (const [kind, id, overlay] of [['structure', 'sauganash_hotel', 'popup'], ['person', 'kinzie_juliette', 'panel'], ['source', 'kinzie_waubun_1856', 'panel']]) {
      const chip = page.locator(`[data-link="${kind}:${id}"]`);
      await chip.evaluate(el => el.scrollIntoView({ block: 'nearest' })); const before = await snapshot();
      await click(chip); await page.waitForSelector(`#${overlay}:not([hidden])`);
      if (kind === 'source') await page.waitForSelector('#sources .src-detail');
      if (kind === 'person') await page.waitForSelector('.people-card-body:not([aria-busy])');
      records.push({ kind, before, layout: await layout(overlay) });
      await page.screenshot({ path: path.join(out, `${width}-${kind}.png`) });
      await click(page.locator('.jaunt-bar [data-action=return]')); await atStop();
      assert.deepEqual(await snapshot(), before, `${kind} restores exact state and scroll`);
      console.log(`CONTEXT ${width}: ${kind} returns unchanged`);
    }
    await page.evaluate(() => { __chicago4d.jaunts.setMode('horse'); __chicago4d.jaunts.next(); });
    await page.waitForSelector('.jaunt-leg-notes');
    const road = await page.evaluate(() => structuredClone(__chicago4d.jaunts.state.context));
    assert.equal(road.lines.length, 2); assert.equal(road.authored, true);
    await click(page.getByRole('button', { name: 'Dismiss road notes', exact: true }));
    assert(await page.locator('.jaunt-leg-notes').isHidden());
    await page.evaluate(() => __chicago4d.jaunts.straight()); await atStop();
    assert(await page.locator('.jaunt-road-history').isVisible());
    await click(page.locator('.jaunt-road-history > summary'));
    await page.screenshot({ path: path.join(out, `${width}-road.png`) });
    console.log(`CONTEXT ${width}: road notes dismiss and remain readable`);
    assert(await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago', { mode: 'instantly' })));
    await atStop();
    await page.evaluate(() => { for (let i = 0; i < 4; i++) __chicago4d.jaunts.next(); __chicago4d.jaunts.choose('rest'); });
    await atStop(); const chosen = await snapshot(); assert.equal(chosen.choice, 'rest');
    await page.evaluate(() => __chicago4d.jaunts.detail({ kind: 'structure', id: 'brown_boarding_house' }));
    await page.waitForSelector('#popup:not([hidden])');
    await page.clock.install(); await page.clock.fastForward('02:00');
    await page.evaluate(() => __chicago4d.jaunts.returnFromDetail()); await atStop();
    assert.deepEqual(await snapshot(), chosen, 'two minutes reading earns/spends nothing');
    await page.clock.resume();
    console.log(`CONTEXT ${width}: two minutes reading preserves choices and resources`);
    await page.evaluate(() => __chicago4d.jaunts.detail({ kind: 'person', id: 'missing-person' }));
    await page.waitForSelector('#jaunt-context-card:not([hidden])'); await layout('jaunt-context-card');
    assert.match(await page.locator('#jaunt-context-card').innerText(), /No card yet/);
    await page.screenshot({ path: path.join(out, `${width}-unavailable.png`) });
    await click(page.locator('#jaunt-context-card button')); await atStop();
    await page.route('**/residents/households/hh_beaubien_mark.json', route => route.fulfill({ status: 404, body: 'missing' }));
    await page.evaluate(() => __chicago4d.jaunts.detail({ kind: 'person', id: 'beaubien_mark' }));
    await page.waitForFunction(() => document.querySelector('#people-directory')?.textContent.includes('No card yet'));
    await layout('panel'); await click(page.locator('.jaunt-bar [data-action=return]')); await atStop();
    await page.route('**/sources/andreas_1884_v1.json', route => route.fulfill({ status: 404, body: 'missing' }));
    await page.evaluate(() => __chicago4d.jaunts.detail({ kind: 'source', id: 'andreas_1884_v1' }));
    await page.waitForSelector('#jaunt-context-card:not([hidden])');
    await click(page.locator('#jaunt-context-card button')); await atStop();
    assert.deepEqual(await snapshot(), chosen, 'failed dossiers and sources preserve the outing');
    console.log(`CONTEXT ${width}: missing cards preserve the outing`);
    let pending, release;
    const waiting = new Promise(r => { pending = r; }), released = new Promise(r => { release = r; });
    await page.route('**/sources/chicago_democrat_1833_11_26.json', async route => { pending(); await released; await route.fulfill({ status: 404, body: 'missing' }); });
    await page.evaluate(() => __chicago4d.jaunts.detail({ kind: 'source', id: 'chicago_democrat_1833_11_26' }));
    let timer;
    try {
      await Promise.race([waiting, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Pending source request was not observed')), 90000); })]);
    } finally { clearTimeout(timer); }
    await page.evaluate(() => __chicago4d.jaunts.end()); release();
    await page.waitForFunction(() => __chicago4d.jaunts.state.jaunt === null);
    assert(await page.locator('#popup').isHidden()); assert(await page.locator('#panel').isHidden());
    assert(await page.locator('#jaunt-context-card').isHidden()); assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out, `${width}-state.json`), JSON.stringify({ records, chosen, pageErrors: errors }, null, 2) + '\n');
    console.log(`JAUNT CONTEXT PASS — ${width}; cards, state, road notes, missing cards, pending exit; zero page errors`);
    await context.close();
  }
} finally { await browser.close(); await new Promise(r => server.close(r)); }
