// Published 1904 household conversation + real Interact UI, phone and desktop.
// Run from chicago/4d after tools/publish.sh. NODE_PATH may supply Playwright.
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve('../../site/4d');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.wasm': 'application/wasm', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  let file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(root + '/') || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((resolve) => server.listen(4199, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }]) {
    const page = await browser.newPage({ viewport, hasTouch: viewport.width < 600 });
    const errors = [];
    page.on('pageerror', (e) => { errors.push(e.message); console.log('PAGE ERROR', e.message); });
    page.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url()); });
    await page.addInitScript(() => localStorage.setItem('chicago4d.settings', JSON.stringify({ timeOfDay: '23:00' })));
    await page.goto('http://127.0.0.1:4199/1904/', { waitUntil: 'domcontentloaded', timeout: 180000 });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 240000, polling: 1000 }).catch(async (error) => {
      console.log('BOOT FAILURE', await page.evaluate(() => ({ ready: window.__chicago4d?.ready, error: window.__chicago4d?.error, text: document.body.innerText.slice(-1800) })));
      throw error;
    });
    console.log('ready', viewport.width);
    await page.evaluate(() => {
      const a = window.__chicago4d;
      if (a.error) throw new Error(a.error);
      if (a.timeOfDay.current.hhmm !== '23:00') throw new Error('Night setting was not applied');
      document.getElementById('home-roam').click();
      a.navigator?.dock?.();
      a.renderer.setAnimationLoop(null);
      const step = (seconds) => { for (let i = 0; i < seconds * 20; i++) {
        a.houseDoors.update(0.05); a.interactions.update(0.05);
        for (const actor of a.humans.actors) actor.walk?.(0.05);
        a.days.update(0.05);
      } };
      const until = (condition, limit = 180) => { for (let i = 0; i < limit * 20 && !condition(); i++) step(0.05); };
      window.__probe = { step, until };
      const john = a.houseErrands.errands.find(t => t.actor.personId === 'glessner_john_j');
      window.__probe.john = john;
      a.days.update(0.05);
      until(() => john.actor.indoors);
      if (!a.houseErrands.callOut(john.actor.id).ok) throw new Error('Door call refused');
      until(() => !john.running);
      a.walker.teleport({ local_e: john.actor.e + 1, local_n: john.actor.n, yaw_deg: 270 });
      if (a.interactKey.refresh()?.id !== john.id) throw new Error('John is not the interaction target');
      a.renderer.render(a.scene3d, a.camera);
    });
    const key = page.locator('#btn-interact'), menu = page.locator('#interact-more');
    assert.equal(await key.getAttribute('aria-expanded'), 'false');
    await key.click();
    assert.equal(await key.getAttribute('aria-expanded'), 'true');
    const bounds = await menu.boundingBox();
    assert(bounds && bounds.x >= 0 && bounds.x + bounds.width <= viewport.width && bounds.y >= 0 && bounds.y + bounds.height <= viewport.height);
    const labels = await menu.locator('.ik-what').allTextContents();
    assert(labels.length >= 5 && labels.every(x => x.split(/\s+/).length <= 4));
    await page.screenshot({ path: `/tmp/t3536-menu-${viewport.width}.png` });
    await page.keyboard.press('Escape');
    assert.equal(await key.getAttribute('aria-expanded'), 'false');
    await key.click();
    await menu.getByRole('button', { name: 'Interact: Chat together — John J. Glessner', exact: true }).click();
    assert.equal(await key.getAttribute('aria-expanded'), 'false');
    const social = await page.evaluate(() => {
      const a = window.__chicago4d, { step, until, john } = window.__probe;
      until(() => a.days.people.filter(p => p.social).length === 2 && a.days.people.filter(p => p.social).every(p => p.mode === 'out'));
      step(1);
      const pair = a.days.people.filter(p => p.social);
      if (pair.length !== 2) throw new Error('No conversation pair');
      const distance = Math.hypot(pair[0].actor.e - pair[1].actor.e, pair[0].actor.n - pair[1].actor.n);
      if (distance > 2.2) throw new Error('Partners did not meet');
      const partners = pair.map(p => p.actor.personId);
      step(65); until(() => pair.every(p => p.actor.indoors));
      if (!pair.every(p => p.actor.indoors) || a.days.people.some(p => p.social)) throw new Error('Pair did not return inside');
      if (!a.houseErrands.callOut(john.actor.id).ok) throw new Error('Second door call refused');
      until(() => !john.running);
      if (!a.interactions.act(john, 'go_home').ok) throw new Error('Go inside refused');
      until(() => john.actor.indoors);
      if (!john.actor.indoors) throw new Error('Go inside did not complete');
      return { partners, distance, returnedInside: true, goInside: true };
    });
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ viewport, labels, bounds, social, pageErrors: errors, result: 'PASS' }));
    await page.close();
  }
} finally { await browser.close(); server.close(); }
