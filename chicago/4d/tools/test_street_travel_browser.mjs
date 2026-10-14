#!/usr/bin/env node
// Published geometry, both eras and viewports; run after tools/publish.sh.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve('../../site/4d');
const out = path.resolve(process.env.STREET_TRAVEL_OUT || '/tmp/chicago-street-travel');
fs.mkdirSync(out, { recursive: true });
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  const file = path.join(root, url.pathname.endsWith('/') ? `${url.pathname}index.html` : url.pathname);
  fs.readFile(file, (err, data) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : data); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const receipts = [];
try {
  for (const year of [1835, 1904]) {
    const page = await browser.newPage({ viewport: { width: 390, height: 780 }, isMobile: true, hasTouch: true });
    page.setDefaultTimeout(180000);
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(() => localStorage.setItem('chicago4d.controlHelpDismissed', '1'));
    await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=${year}&seed=2496`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 240000 });
    await page.evaluate(() => __chicago4d.welcome.enter('spawn'));
    console.log(`READY ${year}`);
    for (const width of [390, 1280]) {
      await page.setViewportSize({ width, height: width === 390 ? 780 : 800 });
      const receipt = await page.evaluate(year => {
        const a = __chicago4d, id = year === 1904 ? 'glessner_house' : 'sauganash_hotel', modes = [];
        for (const mode of ['walk', 'horse', 'wagon']) {
          a.popup.close(); a.travel.stop(); a.setFly(false);
          if (year === 1904) a.walker.teleport({ local_e: 1300, local_n: -3230 });
          else a.goTo('south_water');
          a.travel.setMode(mode);
          let arrived = false, stopped = null;
          const ok = a.travel.go({ kind: 'structure', id }, { onArrive: () => arrived = true, onStop: r => stopped = r });
          const ride = a.travel.simulate(900);
          modes.push({ mode, ok, arrived, stopped, phase: ride.phase, seconds: ride.seconds,
            e: ride.e, n: ride.n, surface: a.router.classAt(ride.e, ride.n) });
        }
        a.travel.setMode('walk');
        a.travel.go({ kind: 'structure', id }, { onArrive() {} }); a.travel.simulate(900);
        const f = a.framing(id, { card: false }), b = a.buildings.instanceBounds()[id];
        const front = f.front, normal = { e: Math.sin(front.bearing), n: Math.cos(front.bearing) };
        const ground = a.terrain.surfaceHeight(front.e, front.n);
        const corners = [-1, 1].flatMap(side => [ground, ground + b.size[1]].map(y => {
          const p = a.project(front.e + side * normal.n * front.width / 2, front.n - side * normal.e * front.width / 2, y);
          return { x: p.x, y: p.y, z: p.z };
        }));
        return { year, width: innerWidth, modes, front, corners };
      }, year);
      for (const r of receipt.modes) {
        assert(r.ok && r.arrived && !r.stopped && r.phase === 'idle', JSON.stringify(r));
        assert.equal(r.surface, r.mode === 'walk' ? 'sidewalk' : 'track');
      }
      assert(receipt.corners.every(p => Math.abs(p.x) < 1 && Math.abs(p.y) < 1 && p.z < 1), JSON.stringify(receipt));
      if (year === 1904) assert.equal(receipt.front.street, 'prairie');
      receipts.push(receipt); fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify(receipts, null, 2));
      await page.screenshot({ path: path.join(out, `${year}-${width}.png`) });
      console.log(`PASS ${year} ${width}: all ground modes arrive on their surface; facade fits in frame`);
    }
    assert.deepEqual(errors, []); await page.close();
  }
} finally { await browser.close(); server.close(); }
console.log(`STREET TRAVEL BROWSER PASS — ${out}`);
