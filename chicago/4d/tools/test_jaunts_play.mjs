#!/usr/bin/env node
// Published, real-travel acceptance: fixtures change content, never runtime code.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url), { chromium } = require('playwright');
const root = path.resolve('../../site/4d'), out = path.resolve('docs/performance/jaunts-play');
fs.mkdirSync(out, { recursive: true });
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname.replace(/^\/dev\//, '/');
  const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const fixtures = ['walk', 'shopping', 'tavern'].map(id => JSON.parse(fs.readFileSync(`data/jaunts/_fixtures/fixture-${id}.json`)));
const fixture = fixtures[0], fixturesById = Object.fromEntries(fixtures.map(doc => [doc.id, doc]));
const catalog = JSON.parse(fs.readFileSync('data/sidecars/1835/jaunts/catalog.json'));
for (const doc of fixtures) catalog.jaunts.push({ id: doc.id, title: doc.title, premise: doc.premise, stop_count: doc.stops.length,
  primary_family: doc.keepsake.family, category: doc.category, content_version: doc.content_version,
  default_mode: doc.default_mode, allowed_modes: doc.allowed_modes, availability: 'available' });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }].filter(v => !process.env.JAUNT_VIEWPORT || String(v.width) === process.env.JAUNT_VIEWPORT)) {
    const context = await browser.newContext({ viewport, hasTouch: viewport.width === 390, isMobile: viewport.width === 390, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [], requests = [], states = [];
    // Match the shared smoke's software-renderer action budget. Assertions stay unchanged.
    page.setDefaultTimeout(90000);
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => { if (/jaunts\/|jaunts.js|jaunt-panel.js|jaunt-preview.js|jaunt.css/.test(r.url())) requests.push(r.url()); });
    await page.route('**/jaunts/catalog.json', r => r.fulfill({ json: catalog }));
    await page.route('**/jaunts/fixture-*.json', r => {
      const id = path.basename(new URL(r.request().url()).pathname, '.json');
      return fixturesById[id] ? r.fulfill({ json: fixturesById[id] }) : r.continue();
    });
    const prefix = viewport.width === 390 ? '/walk/' : '/dev/walk/';
    await page.goto(`http://127.0.0.1:${server.address().port}${prefix}?year=1835&seed=1279`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 180000 });
    assert.equal(requests.length, 0, 'no jaunt requests at boot');
    console.log(`JAUNT PLAY ${viewport.width}: welcome ready`);
    const state = () => page.evaluate(() => structuredClone(__chicago4d.jaunts.state));
    const atStop = () => page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop');
    async function click(locator) {
      await locator.waitFor({ state: 'visible' });
      const point = await locator.evaluate(el => {
        el.scrollIntoView({ block: 'nearest' });
        const r = el.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2;
        if (el.disabled || r.width < 1 || r.height < 1 || !el.contains(document.elementFromPoint(x, y))) throw new Error('Control is disabled, invisible or covered');
        return { x, y };
      });
      // Trusted mouse input without waiting for multiple town-rendering frames.
      await page.mouse.click(point.x, point.y);
    }
    const finishRide = async () => {
      await page.evaluate(() => { if (__chicago4d.travel.state.phase !== 'idle') __chicago4d.travel.simulate(600); });
      await atStop(); assert.equal(await page.evaluate(() => __chicago4d.travel.state.phase), 'idle');
    };
    async function layout(overlay) {
      const boxes = await page.evaluate(id => {
        const rect = el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
        return { nav: rect(document.querySelector('.jaunt-controls')), buttons: [...document.querySelectorAll('.jaunt-controls button:not([hidden]), .jaunt-controls select')].map(rect),
          overlay: id ? rect(document.getElementById(id)) : null, width: innerWidth, height: innerHeight, body: document.body.scrollWidth, lock: !!document.pointerLockElement };
      }, overlay);
      assert.equal(boxes.lock, false); assert(boxes.body <= boxes.width + 1);
      assert(boxes.buttons.every(r => r.h >= 44 && r.w >= 44 && r.y >= 0 && r.y + r.h <= boxes.height + 1), JSON.stringify(boxes));
      if (boxes.overlay) {
        const a = boxes.nav, b = boxes.overlay;
        assert(Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y)) === 0, JSON.stringify(boxes));
      }
      return boxes;
    }
    await click(page.locator('#welcome-jaunts'));
    await click(page.locator('[data-jaunt="new-in-chicago"]').getByRole('button', { name: 'Start Jaunt', exact: true }));
    await atStop(); assert(await page.locator('[data-action=prev]').isDisabled());
    console.log(`JAUNT PLAY ${viewport.width}: first stop`);
    await layout(); states.push(await state()); await page.screenshot({ path: path.join(out, `${viewport.width}-stop.png`) });
    if (process.env.JAUNT_FRAMING_ONLY !== '1') {
    await click(page.locator('#jaunt-panel').getByRole('button', { name: 'About this place' }));
    await page.waitForSelector('#popup:not([hidden])'); await layout('popup');
    await page.screenshot({ path: path.join(out, `${viewport.width}-detail.png`) });
    await page.evaluate(() => __chicago4d.popup.close()); await atStop();
    await page.locator('#btn-help').evaluate(el => el.click());
    await page.waitForSelector('#panel:not([hidden])'); await layout('panel');
    await page.screenshot({ path: path.join(out, `${viewport.width}-drawer.png`) });
    await page.evaluate(() => __chicago4d.hud.setPanel(false));
    if (viewport.width === 390) for (const size of [{ width: 320, height: 568 }, { width: 780, height: 390 }, viewport]) { await page.setViewportSize(size); await layout(); }
    await click(page.locator('[data-action=next]')); const leg = (await state()).leg;
    await page.evaluate(() => { for (let i = 0; i < 5; ++i) __chicago4d.jaunts.next(); }); assert.equal((await state()).leg, leg);
    await finishRide();
    await click(page.locator('[data-action=prev]')); await finishRide();
    await click(page.locator('[data-action=next]')); await finishRide();
    const beforePause = await state();
    console.log(`JAUNT PLAY ${viewport.width}: previous/next complete`);
    await click(page.locator('[data-action=menu]'));
    const position = await page.evaluate(() => JSON.stringify(__chicago4d.walker.state));
    await click(page.getByRole('button', { name: 'Resume Jaunt', exact: true })); await atStop();
    assert.equal((await state()).stopIndex, beforePause.stopIndex);
    assert.equal(await page.evaluate(() => JSON.stringify(__chicago4d.walker.state)), position);
    }
    await click(page.locator('[data-action=next]'));
    const endMs = await page.evaluate(() => { const start = performance.now(); __chicago4d.jaunts.end(); return performance.now() - start; });
    assert(endMs < 200, `End took ${endMs}ms`); assert.equal((await state()).jaunt, null);
    assert.equal(await page.evaluate(() => __chicago4d.travel.state.phase), 'idle');
    await page.waitForFunction(() => document.activeElement?.textContent === 'Start Jaunt');
    const framing = [];
    for (const anchor of ['sauganash', 'cermak_prairie']) {
      assert(await page.evaluate(id => __chicago4d.welcome.enter('anchor', id), anchor), `entered ${anchor}`);
      assert(await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago'))); await atStop();
      framing.push(await page.evaluate(() => { const s = __chicago4d.walker.state; return [s.e, s.n, s.yaw, s.pitch]; }));
      await page.evaluate(() => __chicago4d.jaunts.end());
      await page.waitForSelector('[data-jaunt="new-in-chicago"]');
    }
    assert.deepEqual(framing[0], framing[1]);
    console.log(`JAUNT PLAY ${viewport.width}: End ${endMs.toFixed(1)}ms, identical near/far start framing`);
    if (process.env.JAUNT_FRAMING_ONLY === '1') {
      assert.deepEqual(errors, []);
      fs.writeFileSync(path.join(out, `${viewport.width}-framing.json`), JSON.stringify({ viewport, endMs, anchors: ['sauganash', 'cermak_prairie'], framing, pageErrors: errors }, null, 2) + '\n');
      console.log(`JAUNT FRAMING PASS — ${viewport.width}, both anchors entered, identical framing, layouts and 0 page errors`);
      await context.close(); continue;
    }
    assert(await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago'))); await atStop();
    for (let i = 0; i < 6; ++i) {
      const s = await state(); if (s.phase === 'outcome') break; states.push(s);
      console.log(`JAUNT PLAY ${viewport.width}: pilot stop ${s.stopIndex + 1}`);
      const choice = s.jaunt.stops.find(x => x.id === s.visited[s.stopIndex].id).choices?.[0];
      if (choice) await page.evaluate(id => __chicago4d.jaunts.choose(id), choice.id);
      await page.evaluate(() => __chicago4d.jaunts.next());
      if ((await state()).phase === 'travelling') await finishRide();
    }
    const outcome = await state(); assert.equal(outcome.phase, 'outcome'); assert.equal(outcome.visited.length, 5);
    assert.equal(outcome.events.filter(e => e.type === 'complete').length, 1); states.push(outcome);
    await page.getByRole('heading', { name: 'Outing complete', exact: true }).waitFor();
    await page.screenshot({ path: path.join(out, `${viewport.width}-outcome.png`) });
    assert(await page.evaluate(id => __chicago4d.jaunts.start(id), fixture.id));
    await page.evaluate(() => __chicago4d.jaunts.next()); await finishRide(); await page.evaluate(() => __chicago4d.jaunts.next());
    assert.equal((await state()).phase, 'outcome');
    for (const doc of fixtures) {
      assert(await page.evaluate(id => __chicago4d.jaunts.start(id), doc.id)); await atStop();
      const expected = Object.keys(doc.variables || {}).length + (doc.inventory ? 1 : 0);
      assert.equal(await page.locator('.jaunt-resources li').count(), expected, `${doc.id} resource strip`);
      if (expected && viewport.width === 390) {
        const rows390 = await page.locator('.jaunt-resources li').evaluateAll(nodes => new Set(nodes.map(n => Math.round(n.getBoundingClientRect().y))).size);
        assert.equal(rows390, 1, `${doc.id} resource strip at 390px`);
        await page.setViewportSize({ width: 320, height: 568 });
        const rows320 = await page.locator('.jaunt-resources li').evaluateAll(nodes => new Set(nodes.map(n => Math.round(n.getBoundingClientRect().y))).size);
        assert(rows320 <= 2, `${doc.id} resource strip at 320px`); await page.setViewportSize(viewport);
      }
      if (doc.id === 'fixture-shopping') {
        assert.match(await page.locator('.jaunt-choice').first().innerText(), /costs 75 ¢.*you have \$1\.20/s);
        await page.evaluate(() => __chicago4d.jaunts.choose('buy'));
        await page.evaluate(() => { const button = document.querySelector('[data-action=next]'); button.click(); button.click(); });
        const bought = await state(); assert.equal(bought.vars.money, 45);
        assert.equal(bought.events.filter(e => e.type === 'decision').length, 1);
      } else if (doc.id === 'fixture-tavern') {
        await page.evaluate(() => { __chicago4d.jaunts.choose('abstain'); __chicago4d.jaunts.next(); });
        assert.equal((await state()).outcome.id, 'clear-headed');
      } else {
        // fixture-walk has two stops: ride to the second, then end there (as the walk above does).
        await page.evaluate(() => __chicago4d.jaunts.next()); await finishRide(); await page.evaluate(() => __chicago4d.jaunts.next());
      }
      assert.equal((await state()).phase, 'outcome');
    }
    await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago')); await atStop();
    await page.evaluate(() => __chicago4d.jaunts.menu()); await click(page.locator('#welcome-jaunts-explore'));
    assert.equal((await state()).jaunt, null); assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out, `${viewport.width}-play.json`), JSON.stringify({ viewport, prefix, endMs, bootJauntRequests: 0, states, requests, pageErrors: errors }, null, 2) + '\n');
    console.log(`JAUNT PLAY PASS — ${viewport.width}×${viewport.height}, pilot and fixture, End ${endMs.toFixed(1)}ms, 0 page errors`);
    await context.close();
  }
} finally { await browser.close(); server.close(); }
