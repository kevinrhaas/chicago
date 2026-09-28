#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve('../../site/4d'), out = path.resolve('docs/performance/jaunt-travel');
fs.mkdirSync(out, { recursive: true });
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname.replace(/^\/dev\//, '/');
  const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }].filter(v => !process.env.JAUNT_VIEWPORT || String(v.width) === process.env.JAUNT_VIEWPORT)) {
    const context = await browser.newContext({ viewport, hasTouch: viewport.width === 390, isMobile: viewport.width === 390, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [];
    page.setDefaultTimeout(90000); page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}${viewport.width === 390 ? '' : '/dev'}/walk/?year=1835&seed=1280`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 180000 });
    const saved = await page.evaluate(() => JSON.stringify(Object.entries(localStorage).sort()));
    console.log(`JAUNT TRAVEL ${viewport.width}: welcome ready`);
    const layout = async (overlay = null) => {
      const boxes = await page.evaluate(id => {
        const rect = el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
        return { width: innerWidth, height: innerHeight, body: document.body.scrollWidth,
          controls: [...document.querySelectorAll('.jaunt-controls button:not([hidden]), .jaunt-controls select')].map(rect),
          nav: rect(document.querySelector('.jaunt-controls')), popup: rect(document.getElementById(id || 'popup')) };
      }, overlay);
      assert(boxes.body <= boxes.width + 1);
      assert(boxes.controls.every(r => r.h >= 44 && r.w >= 44 && r.y >= 0 && r.y + r.h <= boxes.height + 1), JSON.stringify(boxes));
      if (overlay) {
        const a = boxes.nav, b = boxes.popup;
        assert.equal(Math.max(0, Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)) * Math.max(0, Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)), 0, 'detail leaves navigation clear');
      }
    };
    await page.locator('#welcome-jaunts').click();
    const card = page.locator('[data-jaunt="new-in-chicago"]'), select = card.locator('select');
    await select.waitFor();
    const estimates = {};
    for (const mode of ['walk', 'wagon', 'horse', 'fly', 'instantly']) {
      await select.selectOption(mode); estimates[mode] = await card.locator('[data-jaunt-estimate]').innerText();
    }
    assert.notEqual(estimates.walk, estimates.instantly);
    console.log(`JAUNT TRAVEL ${viewport.width}: card estimates ${JSON.stringify(estimates)}`);
    await select.selectOption('horse');
    await page.screenshot({ path: path.join(out, `${viewport.width}-menu.png`) });
    assert(await page.evaluate(() => __chicago4d.jaunts.start('new-in-chicago', { mode: 'horse' })));
    await layout();
    if (viewport.width === 390) for (const size of [{ width: 320, height: 568 }, { width: 780, height: 390 }, viewport]) { await page.setViewportSize(size); await layout(); }
    await page.evaluate(() => { __chicago4d.jaunts.next(); __chicago4d.travel.simulate(1); });
    const before = await page.evaluate(() => structuredClone(__chicago4d.jaunts.state));
    await page.getByRole('combobox', { name: 'Jaunt travel mode', exact: true }).selectOption('fly');
    const switched = await page.evaluate(() => {
      const a = __chicago4d, state = structuredClone(a.jaunts.state), motion = a.travel.simulate(3);
      return { state, motion, banner: document.getElementById('travel-banner').textContent };
    });
    assert.equal(switched.state.session, before.session); assert.equal(switched.state.stopIndex, before.stopIndex);
    assert.deepEqual(switched.state.vars, before.vars); assert.deepEqual(switched.state.inventory, before.inventory);
    assert(switched.state.estimate.seconds < before.estimate.seconds, 'flying lowers the remaining estimate');
    assert(switched.motion.maxAltitude > 3, 'the controller climbs'); assert.match(switched.banner, /Flying to/);
    await layout();
    await page.screenshot({ path: path.join(out, `${viewport.width}-flying.png`) });
    console.log(`JAUNT TRAVEL ${viewport.width}: horse to fly, ${before.estimate.seconds.toFixed(1)}s to ${switched.state.estimate.seconds.toFixed(1)}s remaining`);
    const landing = await page.evaluate(() => __chicago4d.travel.simulate(600));
    assert.equal(landing.phase, 'idle');
    await page.waitForFunction(() => __chicago4d.jaunts.state.phase === 'atStop');
    assert.equal(await page.evaluate(() => __chicago4d.walker.state.flying), false);
    assert(Math.abs(await page.evaluate(() => __chicago4d.walker.state.eyeY - __chicago4d.walker.state.groundY) - 1.68) < 0.05, 'flight arrival stands on ground');
    await page.locator('#jaunt-panel').getByRole('button', { name: 'About this place', exact: true }).click();
    await page.waitForSelector('#popup:not([hidden])'); await layout('popup');
    await page.evaluate(() => __chicago4d.popup.close());
    await page.evaluate(() => {
      const a = __chicago4d; a.jaunts.next(); a.travel.simulate(0.5);
      a.intent.forward = 1; a.travel.update(1 / 30, a.intent); a.intent.clear();
    });
    await page.getByRole('button', { name: 'Resume ride', exact: true }).waitFor();
    const paused = await page.evaluate(() => structuredClone(__chicago4d.jaunts.state));
    await page.evaluate(() => __chicago4d.hud.setPanel(true)); await layout('panel');
    await page.evaluate(() => __chicago4d.hud.setPanel(false));
    await page.getByRole('button', { name: 'Resume ride', exact: true }).click();
    assert.equal(await page.evaluate(() => __chicago4d.jaunts.state.stopIndex), paused.stopIndex);
    await page.getByRole('button', { name: 'Go straight to next stop', exact: true }).click();
    await page.screenshot({ path: path.join(out, `${viewport.width}-arrival.png`) });
    await page.evaluate(() => __chicago4d.jaunts.end());
    assert.equal(await page.evaluate(() => JSON.stringify(Object.entries(localStorage).sort())), saved, 'session modes do not change saved settings');
    console.log(`JAUNT TRAVEL ${viewport.width}: ground arrival, pause/resume and saved settings pass`);
    // Run the primary path in one evaluation so rendering cadence cannot add
    // unmeasured wall-clock travel between simulated legs. Reading time is the
    // content's declared primary reading budget, not an assertion about a reader.
    const measured = await page.evaluate(async () => {
      const a = __chicago4d; await a.jaunts.start('new-in-chicago');
      const initial = a.jaunts.state, estimate = initial.estimate.seconds, legs = [];
      const reading = initial.jaunt.opening.read_s + initial.jaunt.stops.reduce((n, s) => n + s.read_s + (s.action_s || 0), 0);
      for (let i = 0; i < 10 && a.jaunts.state.phase !== 'outcome'; i++) {
        a.jaunts.next(); if (a.jaunts.state.phase === 'travelling') legs.push(a.travel.simulate(1800));
      }
      const result = { estimate, reading, legs, seconds: reading + legs.reduce((n, l) => n + l.seconds, 0), phase: a.jaunts.state.phase };
      a.jaunts.end(); return result;
    });
    assert.equal(measured.phase, 'outcome'); assert(Math.abs(measured.seconds / measured.estimate - 1) <= 0.25, JSON.stringify(measured));
    assert.deepEqual(errors, []);
    const receipt = { viewport, estimates, before: before.estimate, after: switched.state.estimate, maxAltitude: switched.motion.maxAltitude, measured, pageErrors: errors, savedSettingsUnchanged: true };
    fs.writeFileSync(path.join(out, `${viewport.width}.json`), JSON.stringify(receipt, null, 2) + '\n');
    console.log(`JAUNT TRAVEL PASS ${viewport.width}: estimated ${measured.estimate.toFixed(1)}s, measured ${measured.seconds.toFixed(1)}s; five modes, flight, pause/resume and unchanged settings`);
    await context.close();
  }
} finally { await browser.close(); server.close(); }
