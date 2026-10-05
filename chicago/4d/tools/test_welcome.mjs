#!/usr/bin/env node
// T-1278: real published welcome, direct entry, pause and keyboard-safe layouts.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
const playwright = await import(path.join((process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' }).trim()).split(path.delimiter)[0], 'playwright/index.js'));
const { chromium } = playwright.chromium ? playwright : playwright.default;
const root = path.resolve('../../site/4d');
const out = path.resolve('docs/performance/welcome'); fs.mkdirSync(out, { recursive: true });
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname;
  const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--enable-unsafe-swiftshader'] });
const receipts = [];
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }]) {
    const touch = viewport.width === 390;
    const context = await browser.newContext({ viewport, hasTouch: touch, isMobile: touch, reducedMotion: touch ? 'reduce' : 'no-preference' });
    if (!touch) await context.addInitScript(() => {
      localStorage.setItem('chicago4d.theme', 'light');
      localStorage.setItem('chicago4d.settings', JSON.stringify({ pace: 'wagon', travelMode: 'horse' }));
    });
    const page = await context.newPage(), errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1835&seed=1278`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', null, { timeout: 180000 });
    const initial = await page.evaluate(() => {
      const visible = el => { const b = el.getBoundingClientRect(); return b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth; };
      return { focus: document.activeElement.id, state: __chicago4d.welcome.state,
        actions: ['welcome-jaunts','welcome-explore','gate-btn'].every(id => visible(document.getElementById(id))),
        help: document.getElementById('control-help').hidden,
        progress: getComputedStyle(document.getElementById('gate-bar')).display,
        animation: getComputedStyle(document.querySelector('.gate-card')).animationName,
        locked: !!document.pointerLockElement };
    });
    assert.equal(initial.focus, 'gate-title'); assert(initial.actions && initial.help && !initial.locked);
    assert.equal(initial.progress, 'none'); if (touch) assert.equal(initial.animation, 'none');
    await page.screenshot({ path: path.join(out, `${viewport.width}-welcome.png`) });
    await page.locator('#welcome-jaunts').dispatchEvent('click');
    assert(await page.locator('#welcome-jaunts-region').isVisible());
    // T-2120: the back arrow returns to the three choices; Starting at… leads with five quick starts.
    await page.locator('#welcome-back').dispatchEvent('click');
    assert(await page.locator('#welcome-jaunts-region').isHidden() && await page.locator('#welcome-back').isHidden());
    await page.locator('#welcome-explore').dispatchEvent('click');
    assert.equal(await page.locator('#welcome-quick .welcome-quick-start').count(), 5);
    const before = await page.evaluate(() => ({ ...__chicago4d.player }));
    await page.locator('#welcome-search').fill('Sauganash');
    await page.keyboard.type('wasd');
    assert.equal(await page.evaluate(() => !!document.pointerLockElement), false);
    const after = await page.evaluate(() => ({ ...__chicago4d.player }));
    assert.equal(after.e, before.e); assert.equal(after.n, before.n);
    await page.locator('#welcome-search').fill('Sauganash');
    await page.screenshot({ path: path.join(out, `${viewport.width}-picker.png`) });
    const settings = await page.evaluate(() => JSON.stringify(__chicago4d.hud.settings));
    for (const kind of ['structure', 'intersection', 'person']) {
      const result = await page.evaluate(kind => {
        const a = __chicago4d;
        if (a.welcome.state === 'world') a.welcome.show();
        const target = a.destinations.targets.find(t => t.kind === kind && a.destinations.resolve(t, { card: false }));
        if (!target) return null;
        const expected = a.destinations.resolve(target, { card: false }).standOff;
        const entered = a.welcome.enter(kind, target.id);
        return { kind, id: target.id, expected, entered, actual: { e: a.walker.state.e, n: a.walker.state.n }, state: a.welcome.state,
          locked: !!document.pointerLockElement, travel: a.travel.state };
      }, kind);
      assert(result?.entered && result.state === 'world' && !result.locked, JSON.stringify(result));
      assert(Math.hypot(result.actual.e - result.expected.e, result.actual.n - result.expected.n) < .01);
      receipts.push(result);
    }
    // A quick start enters the town at its viewpoint.
    const quick = await page.evaluate(() => {
      const a = __chicago4d; if (a.welcome.state === 'world') a.welcome.show();
      a.welcome.enter('explore'); document.querySelector('#welcome-quick [data-id="forks"]').click();
      return { state: a.welcome.state, e: a.walker.state.e, n: a.walker.state.n, anchor: a.destinations.byId('anchor', 'forks') };
    });
    assert.equal(quick.state, 'world', JSON.stringify(quick));
    await page.locator('#btn-start').dispatchEvent('click');
    const pause = await page.evaluate(() => ({ e: __chicago4d.walker.state.e, n: __chicago4d.walker.state.n, help: document.getElementById('control-help').hidden }));
    assert(pause.help);
    await page.keyboard.press('w'); await page.keyboard.press('h');
    assert.equal(await page.evaluate(() => __chicago4d.walker.state.e), pause.e);
    assert.equal(await page.evaluate(() => __chicago4d.walker.state.n), pause.n);
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => __chicago4d.welcome.state), 'world');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'btn-start');
    assert.equal(await page.evaluate(() => JSON.stringify(__chicago4d.hud.settings)), settings);
    await page.locator('#btn-start').dispatchEvent('click');
    await page.locator('#gate-btn').dispatchEvent('click');
    const spawn = await page.evaluate(() => ({ actual: { e: __chicago4d.walker.state.e, n: __chicago4d.walker.state.n }, spawn: __chicago4d.scene.spawn, locked: !!document.pointerLockElement }));
    assert(Math.hypot(spawn.actual.e - spawn.spawn.local_e, spawn.actual.n - spawn.spawn.local_n) < .01); assert(!spawn.locked);
    if (!touch) {
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light');
      await page.mouse.click(640, 400);
      await page.waitForFunction(() => !!document.pointerLockElement);
      await page.locator('#btn-start').dispatchEvent('click');
      assert.equal(await page.evaluate(() => !!document.pointerLockElement), false);
      await page.keyboard.press('Escape');
    }
    if (touch) {
      for (const size of [{ width: 320, height: 568 }, { width: 780, height: 390 }, { width: 390, height: 400 }]) {
        await page.setViewportSize(size.height === 400 ? { width: 390, height: 780 } : size);
        if (size.height === 400) await page.evaluate(() => {
          Object.defineProperty(window.visualViewport, 'height', { configurable: true, get: () => 400 });
          window.visualViewport.dispatchEvent(new Event('resize'));
        });
        await page.evaluate(() => __chicago4d.welcome.show());
        await page.locator('#welcome-explore').dispatchEvent('click');
        await page.locator('#welcome-search').fill('');
        const layout = await page.evaluate(() => {
          const list = document.getElementById('welcome-results'), card = document.querySelector('.gate-card'), b = list.getBoundingClientRect(), c = card.getBoundingClientRect();
          return { width: innerWidth, height: innerHeight, overflow: document.documentElement.scrollWidth > innerWidth, list: { top: b.top, bottom: b.bottom, height: b.height }, card: { top: c.top, bottom: c.bottom }, scrollable: list.scrollHeight > list.clientHeight };
        });
        assert(!layout.overflow && layout.list.height >= 44 && layout.list.bottom <= size.height && layout.card.bottom <= size.height + 1, JSON.stringify(layout));
        assert(layout.scrollable);
        await page.screenshot({ path: path.join(out, `${size.width}x${size.height}-picker.png`) }); receipts.push(layout);
      }
    }
    assert.deepEqual(errors, []); receipts.push({ viewport, initial, spawn, errors });
    console.log(`PASS ${viewport.width}: welcome, picker spawns, pause, focus, settings, default entry; no page errors`);
    await context.close();
  }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(receipts, null, 2) + '\n');
} finally { await browser.close(); server.close(); }
