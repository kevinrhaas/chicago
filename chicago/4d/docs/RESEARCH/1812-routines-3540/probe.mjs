// Published 1812 Native lodge conversation + real Interact UI, phone and desktop.
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
await new Promise((resolve) => server.listen(4201, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }]) {
    if (process.env.PROBE_VIEWPORT && Number(process.env.PROBE_VIEWPORT) !== viewport.width) continue;
    const page = await browser.newPage({ viewport, hasTouch: viewport.width < 600 });
    const errors = [];
    page.on('pageerror', (e) => { errors.push(e.message); console.log('PAGE ERROR', e.message); });
    page.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url()); });
    await page.addInitScript((quality) => localStorage.setItem('chicago4d.settings', JSON.stringify({ timeOfDay: '23:00', ...(quality ? { quality } : {}) })), process.env.PROBE_QUALITY ? Number(process.env.PROBE_QUALITY) : null);
    await page.goto('http://127.0.0.1:4201/1812/', { waitUntil: 'domcontentloaded', timeout: 180000 });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 240000, polling: 1000 }).catch(async (error) => {
      console.log('BOOT FAILURE', await page.evaluate(() => ({ ready: window.__chicago4d?.ready, error: window.__chicago4d?.error, text: document.body.innerText.slice(-1800) })));
      throw error;
    });
    console.log('ready', viewport.width);
    // As in the canonical smoke's holdDraws helper, let the arrival UI finish
    // without repeated software-GPU draws. Restore the draw for the screenshot.
    await page.evaluate(() => {
      const r = window.__chicago4d.renderer;
      window.__probeDraw = r.render;
      r.render = (scene, camera) => camera?.updateMatrixWorld?.();
    });
    // Ready precedes the arrival card's landing, as in the canonical smoke.
    await page.waitForFunction(() => ['welcome', 'world'].includes(window.__chicago4d.welcome.state), null, { timeout: 90000, polling: 100 }).catch(async error => {
      console.log('ARRIVAL FAILURE', await page.evaluate(() => ({ state: window.__chicago4d.welcome.state, error: window.__chicago4d.error, text: document.body.innerText.slice(-2500) })));
      throw error;
    });
    await page.evaluate(() => { if (window.__chicago4d.welcome.state === 'welcome') document.getElementById('home-roam').click(); });
    await page.waitForFunction(() => window.__chicago4d.welcome.state === 'world', null, { timeout: 90000, polling: 100 });
    const setup = await page.evaluate(async () => {
      const a = window.__chicago4d;
      a.navigator?.dock?.(); a.renderer.setAnimationLoop(null);
      a.renderer.render = window.__probeDraw;
      const step = seconds => { for (let i = 0; i < seconds * 20; i++) {
        a.interactions.update(.05); a.humans.update(.05, a.camera, a.walker.state, .05);
        a.duties.update(.05); a.days.update(.05); a.houseDoors?.update(.05); a.spacing?.update(.05);
      } };
      const until = (fn, seconds = 180) => { for (let i = 0; i < seconds * 20 && !fn(); i++) step(.05); };
      step(3);
      const inside = await fetch('../data/humans/inside_1812.json').then(r => r.json());
      const entry = inside.people.find(e => e.person.startsWith('gathering_') && /woman/.test(e.asset_id));
      const door = a.days.doors.find(t => t.door.id === entry.door);
      a.walker.teleport({ local_e: door.at[0] + 4, local_n: door.at[1] + 3, yaw_deg: 230 });
      if (!a.days.ask(entry.person).ok) throw new Error('Native resident door call refused');
      const resident = a.days.people.find(p => p.actor.personId === entry.person);
      until(() => !resident.actor.indoors && !resident.actor.path);
      const actor = resident.actor;
      a.walker.teleport({ local_e: actor.e + 1, local_n: actor.n, yaw_deg: 270 });
      const target = a.interactKey.refresh();
      if (target?.id !== `person:${actor.id}`) throw new Error('Wrong Interact target: ' + target?.id);
      window.__probe = { step, until, resident, entry };
      return { name: target.name, id: target.id, controls: a.interactions.actionsOf(target).map(x => x.label) };
    });
    console.log('setup', viewport.width, JSON.stringify(setup));
    const key = page.locator('#btn-interact'), menu = page.locator('#interact-more');
    assert.equal(await key.getAttribute('aria-expanded'), 'false');
    await key.click();
    const bounds = await menu.boundingBox();
    assert(bounds && bounds.x >= 0 && bounds.x + bounds.width <= viewport.width && bounds.y >= 0 && bounds.y + bounds.height <= viewport.height);
    const labels = await menu.locator('.ik-what').allTextContents();
    assert(labels.length >= 4 && labels.every(x => x.split(/\s+/).length <= 3));
    if (!process.env.PROBE_FAST) {
      await page.evaluate(() => { const a = window.__chicago4d; a.renderer.render(a.scene3d, a.camera); });
      await page.screenshot({ timeout: 120000, path: `/tmp/t3540-menu-${viewport.width}.png` });
    }
    await menu.getByRole('button', { name: `Interact: Chat together — ${setup.name}`, exact: true }).first().click();
    assert.equal(await key.getAttribute('aria-expanded'), 'false');
    // Newly called companions load their portable bodies asynchronously.
    await page.waitForTimeout(1500);
    const result = await page.evaluate(() => {
      const a = window.__chicago4d, { step, until, resident, entry } = window.__probe;
      const pair = a.days.people.filter(p => p.social);
      if (pair.length !== 2) throw new Error('No pair: ' + JSON.stringify(a.days.snapshot().filter(p => p.instance === resident.id)));
      until(() => pair.every(p => p.mode === 'out') || pair.some(p => !p.social)); step(1);
      const distance = Math.hypot(pair[0].actor.e - pair[1].actor.e, pair[0].actor.n - pair[1].actor.n);
      if (pair.some(p => !p.social) || distance > 2.2) throw new Error('Pair failed to meet: ' + JSON.stringify(pair.map(p => ({ id: p.id, mode: p.mode, e: p.actor.e, n: p.actor.n, pending: p.pendingHostMove }))));
      const partners = pair.map(p => p.actor.personId);
      step(65); until(() => pair.every(p => p.actor.indoors || p.actor.disposed));
      if (!pair.every(p => p.actor.indoors || p.actor.disposed)) throw new Error('Pair failed to return');
      if (!resident.actor.disposed || resident.actor.root.parent || resident.actor.body || a.interactions.get(`person:${resident.id}`)) throw new Error('Lazy resident failed to release mesh/control');
      if (!a.days.ask(entry.person).ok) throw new Error('Second door call refused');
      const again = a.days.people.find(p => p.actor.personId === entry.person);
      until(() => !again.actor.indoors && !again.actor.path);
      const activity = a.days.outdoorActivities(again.id).find(x => x.span.activity === 'work');
      if (!a.days.request(again.id, activity.id).ok) throw new Error('Night-time activity refused');
      until(() => again.mode === 'out'); step(3);
      if (again.actor.indoors) throw new Error('Requested work stayed indoors');
      const nearest = a.days.nearestEntrance(again.id);
      if (!nearest || !a.days.request(again.id, null, { inside: 'nearest' }).ok) throw new Error('Go inside refused');
      until(() => again.actor.indoors || again.actor.disposed);
      if (!again.actor.indoors || again.inside !== nearest.structure) throw new Error('Go inside missed the nearest entrance');
      if (!again.actor.disposed) {
        if (!a.days.request(again.id, null, { inside: 'home' }).ok) throw new Error('Return home refused');
        until(() => again.actor.disposed);
      }
      if (!again.actor.disposed || again.actor.root.parent || again.actor.body) throw new Error('Return home failed to retire the figure');
      return { partners, distance, returnedInside: true, nightActivity: activity.label, goInside: nearest.structure, goHome: true };
    });
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ viewport, labels, bounds, result, pageErrors: errors, status: 'PASS' }));
    await page.close();
  }
} finally { await browser.close(); server.close(); }
