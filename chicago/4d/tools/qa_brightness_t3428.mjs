#!/usr/bin/env node
// T-3428 — the brightness aid at 1x, 2x and 4x, photographed where the owner found the
// scene too dim: the Architects of Prairie Avenue jaunt, stop 2, the Glessner front under
// the parkway elms. Writes one JPEG per level and a JSON of mean luma in the sky band (top
// eighth of the frame) and the shaded front (a box low in the middle), so "the shade
// lifted and the sky did not wash out" is a reading and not only a picture.
//   node tools/qa_brightness_t3428.mjs           # phone 390x780
//   QA_DESKTOP=1 node tools/qa_brightness_t3428.mjs
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, process.env.SMOKE_ROOT || '../../site/4d');
const out = process.env.QA_OUT || path.join(root, 'docs/RESEARCH/brightness-3428');
fs.mkdirSync(out, { recursive: true });
const desktop = !!process.env.QA_DESKTOP, tag = desktop ? 'desktop' : 'phone';
const BOOT_MS = Number(process.env.QA_BOOT_MS) || 900000;
const LEVELS = (process.env.QA_LEVELS || '0,1,1.5,2').split(',').map(Number);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try { if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html'); res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res); } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const viewport = desktop ? { width: 1280, height: 800 } : { width: 390, height: 780 };
const page = await (await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: !desktop, hasTouch: !desktop, reducedMotion: 'reduce' })).newPage();
page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', e => errors.push(String(e)));
const rows = [];
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1904`);
  await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: BOOT_MS, polling: 1000 });
  const at = await page.evaluate(async () => {
    const api = __chicago4d, state = () => api.jaunts.state;
    const settle = async test => { for (let i = 0; i < 2400 && !test(); i++) await new Promise(r => setTimeout(r, 25)); return test(); };
    if (!await api.jaunts.start('prairie-architects', { mode: 'instantly', chosen: true })) return { error: 'did not start' };
    if (!await settle(() => state()?.phase === 'atStop')) return { error: `start ended in ${state()?.phase}` };
    api.jaunts.next();
    for (let laps = 0; api.travel.state.phase !== 'idle' && laps < 40; laps++) { api.travel.simulate(15); await new Promise(r => setTimeout(r, 0)); }
    if (!await settle(() => state()?.phase === 'atStop')) return { error: `next ended in ${state()?.phase}` };
    return { stop: state().visited[state().stopIndex]?.id, e: api.walker.state.e, n: api.walker.state.n };
  });
  if (at.error) throw new Error(at.error);
  console.log('at', JSON.stringify(at));
  // Let streaming settle, then hold the clock so the levels differ only by the aid.
  await page.waitForTimeout(desktop ? 60000 : 90000);
  await page.evaluate(() => { const a = __chicago4d; a.setAnimationHold?.(true); a.renderer.setAnimationLoop(null); });
  // Each level is the same held frame — no step between, so the only thing that moves is
  // the aid. Pixels are classed ONCE, on the calibrated frame: SKY is blue-dominant open
  // sky, SHADE is a dark pixel in the lower two thirds (the front under the elms and the
  // walk), SUN a bright one there. Each class reports the median display-luma ratio
  // against the calibrated frame; the calibrated frame is drawn last again to prove the
  // hold (its ratio must be exactly 1).
  const order = [...LEVELS, 0];
  const ratios = await page.evaluate((order) => {
    const a = __chicago4d, frames = [];
    for (const s of order) {
      a.setBrightness(s); a.world.aim(a.camera); a.renderer.render(a.scene3d, a.camera);
      const gl = a.renderer.getContext(), w = gl.drawingBufferWidth, h = gl.drawingBufferHeight, px = new Uint8Array(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
      frames.push({ s, w, h, px, exposure: a.exposure, env: a.scene3d.environmentIntensity, skyExposure: a.world.sky.material.uniforms.skyExposure.value });
    }
    const base = frames[0], { w, h } = base, L = (px, i) => 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2];
    const cls = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const k = y * w + x, i = k * 4, p = base.px, l = L(p, i), top = h - 1 - y; // readPixels is bottom-up
      if (p[i + 2] > p[i] + 40 && p[i + 2] > 110) cls[k] = 1;
      else if (top > h / 3 && l > 8 && l < 55) cls[k] = 2;
      else if (top > h / 3 && l > 120 && l < 230) cls[k] = 3;
    }
    const med = (v) => { if (!v.length) return null; v.sort((x, y) => x - y); return Math.round(v[v.length >> 1] * 100) / 100; };
    return frames.map((f) => {
      const v = [[], [], [], []], clip = [0, 0, 0, 0], n = [0, 0, 0, 0];
      for (let k = 0; k < w * h; k++) {
        const c = cls[k]; if (!c) continue; const i = k * 4, l0 = L(base.px, i), l1 = L(f.px, i);
        n[c]++; if (k % 7 === 0) v[c].push(l1 / Math.max(1, l0)); if (f.px[i] > 250 && f.px[i + 1] > 250 && f.px[i + 2] > 250) clip[c]++;
      }
      const name = ['', 'sky', 'shade', 'sun'];
      const o = { stops: f.s, x: 2 ** f.s, exposure: +f.exposure.toFixed(3), env: +f.env.toFixed(3), skyExposure: +f.skyExposure.toFixed(4) };
      for (const c of [1, 2, 3]) o[name[c]] = { px: n[c], ratio: med(v[c]), clippedPct: n[c] ? Math.round(clip[c] / n[c] * 1000) / 10 : 0 };
      return o;
    });
  }, order);
  for (const r of ratios) { rows.push(r); console.log(JSON.stringify(r)); }
  // The pictures are the same held frames, read back from the drawing buffer rather than
  // screenshotted: a page screenshot composites whatever the page drew last, which is not
  // necessarily the held frame.
  const shots = await page.evaluate((levels) => {
    const a = __chicago4d, outShots = [];
    for (const s of levels) {
      a.setBrightness(s); a.world.aim(a.camera); a.renderer.render(a.scene3d, a.camera);
      const gl = a.renderer.getContext(), w = gl.drawingBufferWidth, h = gl.drawingBufferHeight, px = new Uint8ClampedArray(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
      const flip = new Uint8ClampedArray(w * h * 4);
      for (let y = 0; y < h; y++) flip.set(px.subarray((h - 1 - y) * w * 4, (h - y) * w * 4), y * w * 4);
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      c.getContext('2d').putImageData(new ImageData(flip, w, h), 0, 0);
      outShots.push({ s, url: c.toDataURL('image/jpeg', 0.88) });
    }
    return outShots;
  }, LEVELS);
  for (const { s: lv, url } of shots) {
    const x = (2 ** lv).toFixed(1).replace(/\.0$/, '');
    fs.writeFileSync(path.join(out, `${tag}-glessner-front-${x}x.jpg`), Buffer.from(url.split(',')[1], 'base64'));
  }
  await page.evaluate(() => __chicago4d.setBrightness(0));
} finally {
  fs.writeFileSync(path.join(out, `${tag}.json`), JSON.stringify({ rows, errors }, null, 1));
  if (errors.length) console.log('pageerrors:', errors);
  await browser.close(); server.close();
}
