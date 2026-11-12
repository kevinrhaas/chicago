// Published shared person selection: real walking actor + Interact UI, phone and desktop.
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
await new Promise((resolve) => server.listen(4203, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }]) {
    if (process.env.PROBE_VIEWPORT && Number(process.env.PROBE_VIEWPORT) !== viewport.width) continue;
    const page = await browser.newPage({ viewport, hasTouch: viewport.width < 600 });
    const errors = [];
    page.on('pageerror', (e) => { errors.push(e.message); console.log('PAGE ERROR', e.message); });
    page.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url()); });
    await page.addInitScript(settings => localStorage.setItem('chicago4d.settings', JSON.stringify({ timeOfDay: '23:00', ...settings })), { ...(process.env.PROBE_QUALITY ? { quality: Number(process.env.PROBE_QUALITY) } : {}), ...(process.env.PROBE_DETAIL ? { detail: process.env.PROBE_DETAIL } : {}) });
    await page.goto('http://127.0.0.1:4203/1904/', { waitUntil: 'domcontentloaded', timeout: 180000 });
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
    await page.evaluate((fast) => {
      const a = window.__chicago4d;
      if (a.error) throw new Error(a.error);
      if (a.timeOfDay.current.hhmm !== '23:00') throw new Error('Night setting was not applied');
      a.navigator?.dock?.();
      a.renderer.setAnimationLoop(null);
      a.renderer.render = window.__probeDraw;
      const step = (seconds) => { for (let i = 0; i < seconds * 20; i++) {
        a.interactions.update(0.05);
        a.humans.update(0.05, a.camera, a.walker.state, 0.05);
        a.days.update(0.05);
        a.houseDoors.update(0.05); a.spacing?.update(0.05);
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
      const target = a.interactKey.refresh();
      window.__probe.roster = a.humans.actors.length;
      if (target?.id !== john.id) throw new Error('John is not the interaction target: ' + JSON.stringify({ target: target?.id, welcome: a.welcome.state, at: john.at, indoors: john.actor.indoors, shown: a.humans.shown, held: a.humans.isHeld?.(john.actor), walker: a.walker.state }));
      // Draw once with the expanded menu below; this setup needs no GPU frame.
    }, !!process.env.PROBE_FAST);
    // A real scheduled work trip, not a synthetic actor path.
    const walking = await page.evaluate(() => {
      const a = window.__chicago4d, { john, step, until } = window.__probe;
      const task = a.days.outdoorActivities(john.actor.id).find(x => x.span.activity === 'work');
      if (!task || !a.days.request(john.actor.id, task.id).ok) throw new Error('Outdoor work refused');
      until(() => john.actor.path && !john.actor.indoors && !a.days.people.find(p => p.id === john.actor.id).passing);
      if (!john.actor.path) throw new Error('No real walk to work');
      const actor = john.actor;
      step(.2);
      const e = actor.e, n = actor.n; step(.2);
      const de = actor.e-e, dn = actor.n-n, d = Math.hypot(de,dn);
      if (d < .001) throw new Error('Actor is not walking');
      a.walker.teleport({local_e: actor.e-de/d*2.3, local_n: actor.n-dn/d*2.3, yaw_deg: Math.atan2(de,dn)*180/Math.PI});
      if (a.interactKey.refresh()?.id !== john.id) throw new Error('Walker not offered');
      step(.5);
      if (a.interactKey.refresh()?.id !== john.id) throw new Error('Walking grace lost target');
      return { distance: Math.hypot(actor.e-a.walker.state.e, actor.n-a.walker.state.n) };
    });
    const key = page.locator('#btn-interact'), menu = page.locator('#interact-more');
    await key.click();
    assert.equal(await key.getAttribute('aria-expanded'), 'true');
    const paused = await page.evaluate(() => {
      const { john, step } = window.__probe, p = [john.actor.e,john.actor.n];
      step(20); window.__chicago4d.interactKey.refresh();
      return { distance: Math.hypot(john.actor.e-p[0],john.actor.n-p[1]), path: !!john.actor.path };
    });
    assert(paused.distance < .001 && !paused.path, JSON.stringify(paused));
    const bounds = await menu.boundingBox();
    assert(bounds && bounds.x >= 0 && bounds.x + bounds.width <= viewport.width && bounds.y >= 0 && bounds.y + bounds.height <= viewport.height);
    const labels = await menu.locator('.ik-what').allTextContents();
    assert.deepEqual(labels.slice(-2), ['Go inside', 'Go home']);
    assert.equal(await menu.locator('.ik-icon svg').count(), labels.length);
    assert(labels.every(x => x.split(/\s+/).length <= 4));
    await page.evaluate(() => { const a = window.__chicago4d; a.renderer.render(a.scene3d,a.camera); });
    await page.screenshot({timeout: 120000, path: `/tmp/t3543-interact-${viewport.width}.png`});
    await page.keyboard.press('Escape');
    const resumed = await page.evaluate(() => {
      const a=window.__chicago4d, {john,step}=window.__probe, p=[john.actor.e,john.actor.n];
      step(1);
      return Math.hypot(john.actor.e-p[0],john.actor.n-p[1]);
    });
    assert(resumed > .01, 'Closing the menu must resume the unfinished walk');
    // The physical figure click dispatches this same selection event/card route.
    const pinned = await page.evaluate(() => {
      const a=window.__chicago4d, {john}=window.__probe;
      a.humans.select(john.actor.id);
      a.walker.teleport({local_e: john.actor.e+30,local_n: john.actor.n+30,yaw_deg:225});
      return a.interactKey.refresh()?.id;
    });
    assert.equal(pinned, await page.evaluate(() => window.__probe.john.id));
    await key.click();
    assert.equal(await key.getAttribute('aria-expanded'), 'true');
    await menu.locator('[data-action="go_inside"]').click();
    const indoors = await page.evaluate(() => {
      const a=window.__chicago4d, {john,until}=window.__probe;
      const person=a.days.people.find(p => p.id===john.actor.id);
      const state=()=>({indoors:john.actor.indoors,e:john.actor.e,n:john.actor.n,state:john.actor.state,inRange:john.actor.inRange,
        path:john.actor.path && {pts:john.actor.path.pts,leg:john.actor.path.leg,t:john.actor.path.t,arrived:john.actor.path.arrived},
        mode:person.mode,inside:person.inside,passing:person.passing,attending:!!person.attending,
        pending:person.pendingHostMove && {to:person.pendingHostMove.to,from:person.pendingHostMove.from,token:person.pendingHostMove.token},
        token:person.token,override:person.override,nearest:a.days.nearestEntrance(john.actor.id)?.door.id,
        hud:document.querySelector('#status')?.textContent});
      const before=state(); until(() => john.actor.indoors);
      return {before,after:state()};
    });
    console.log('inside trace',JSON.stringify(indoors));
    assert(indoors.after.indoors, 'Go inside should use an actual entrance: '+JSON.stringify(indoors));
    await page.evaluate(() => {
      const a=window.__chicago4d, {john,until}=window.__probe;
      if (!a.houseErrands.callOut(john.actor.id).ok) throw new Error('Door call refused');
      until(() => !john.running);
      a.humans.select(john.actor.id); a.interactKey.refresh();
    });
    await key.click();
    await menu.locator('[data-action="go_home"]').click();
    assert(await page.evaluate(() => { const {john,until}=window.__probe; until(() => john.actor.indoors); return john.actor.indoors; }));
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({viewport,labels,bounds,walking,paused,resumed,pinned,pageErrors:errors,result:'PASS'}));
    await page.close();
  }
} finally { await browser.close(); server.close(); }
