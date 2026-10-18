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
// T-2614: the gesture started audio — or say what the gate saw instead.
const audioRunning = page => page.waitForFunction(() => __chicago4d.audio?.state === 'running', null, { timeout: 10000, polling: 100 })
  .catch(async () => { throw new Error(`audio not running after the gesture: ${JSON.stringify(await page.evaluate(() => ({ gate: __chicago4d.gesture?.state, journey: document.documentElement.dataset.journey, welcome: __chicago4d.welcome.state })))}`); });
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
    // T-2614: the autoplay warning a browser prints for audio made without a gesture.
    const autoplay = []; page.on('console', m => { if (/AudioContext|autoplay/i.test(m.text())) autoplay.push(m.text()); });
    await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1835&seed=1278`);
    // T-2613: Home opens halfway through the landing; read it once the landing has finished
    // (its reduced-motion crossfade is the one animation allowed before that).
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome'
      && document.documentElement.dataset.journey === 'landed', null, { timeout: 180000 });
    const initial = await page.evaluate(() => {
      const visible = el => { const b = el.getBoundingClientRect(); return b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth; };
      return { focus: document.activeElement.id, state: __chicago4d.welcome.state,
        actions: ['welcome-jaunts','welcome-explore','home-roam'].every(id => visible(document.getElementById(id))),
        help: document.getElementById('control-help') === null, // T-2661: no popover; Guide has the controls
        progress: getComputedStyle(document.getElementById('gate-bar')).display,
        animation: getComputedStyle(document.querySelector('.gate-card')).animationName,
        locked: !!document.pointerLockElement };
    });
    assert.equal(initial.focus, 'gate-title'); assert(initial.actions && initial.help && !initial.locked);
    assert.equal(initial.progress, 'none'); if (touch) assert.equal(initial.animation, 'none');
    // T-2614: landed, and still no AudioContext — it waits for the first real tap.
    assert.equal(await page.evaluate(() => __chicago4d.audio), null, 'no AudioContext before a gesture');
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
    const pause = await page.evaluate(() => ({ e: __chicago4d.walker.state.e, n: __chicago4d.walker.state.n, help: document.getElementById('control-help') === null }));
    assert(pause.help);
    await page.keyboard.press('w'); await page.keyboard.press('h');
    assert.equal(await page.evaluate(() => __chicago4d.walker.state.e), pause.e);
    assert.equal(await page.evaluate(() => __chicago4d.walker.state.n), pause.n);
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => __chicago4d.welcome.state), 'world');
    // T-2625: Start / Jaunts moved into the Navigator; focus returns to it, or to the device's handle.
    assert(['btn-start', 'nav-grip', 'nav-collapse'].includes(await page.evaluate(() => document.activeElement.id)));
    assert.equal(await page.evaluate(() => JSON.stringify(__chicago4d.hud.settings)), settings);
    await page.locator('#btn-start').dispatchEvent('click');
    // T-2614 (QA-04): on the phone a real tap on Free roam is the gesture that starts audio.
    if (touch) await page.locator('#home-roam').tap();
    else await page.locator('#home-roam').dispatchEvent('click');
    const spawn = await page.evaluate(() => ({ actual: { e: __chicago4d.walker.state.e, n: __chicago4d.walker.state.n }, spawn: __chicago4d.scene.spawn, locked: !!document.pointerLockElement,
      audio: __chicago4d.audio?.state ?? null, tag: !document.getElementById('look-tag').hidden }));
    assert(Math.hypot(spawn.actual.e - spawn.spawn.local_e, spawn.actual.n - spawn.spawn.local_n) < .01); assert(!spawn.locked);
    if (touch) {
      await audioRunning(page);
      assert.equal(spawn.tag, false, 'no CLICK TO ENGAGE LOOK on a touch device');
    }
    if (!touch) {
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light');
      // T-2614 (QA-05): CLICK TO ENGAGE LOOK until the first click on the scene takes the pointer.
      assert.equal(spawn.tag, true, 'CLICK TO ENGAGE LOOK shows in the town before lock');
      assert.equal(await page.evaluate(() => getComputedStyle(document.getElementById('look-tag')).textTransform), 'uppercase');
      await page.mouse.click(640, 400);
      // Polled on a clock, not on animation frames: the entered town can draw a frame in
      // seconds on a loaded runner, and a locked pointer is not a frame's business.
      await page.waitForFunction(() => !!document.pointerLockElement, null, { polling: 100 });
      // The tag goes on the lock event (it can trail the lock by a frame on a slow runner).
      await page.waitForFunction(() => document.getElementById('look-tag').hidden, null, { timeout: 10000, polling: 100 });
      await audioRunning(page);
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
    assert.deepEqual(errors, []); assert.deepEqual(autoplay, [], 'no autoplay warnings'); receipts.push({ viewport, initial, spawn, errors });
    console.log(`PASS ${viewport.width}: welcome, picker spawns, pause, focus, settings, default entry; no page errors`);
    await context.close();
  }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(receipts, null, 2) + '\n');
} finally { await browser.close(); server.close(); }
