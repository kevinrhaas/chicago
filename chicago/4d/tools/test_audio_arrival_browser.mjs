// T-3532: real published arrival page and trusted opt-in, using real R2 media.
// This checks loading-screen audio, not the complete town's release smoke.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../site/4d');
const origin = 'https://chicago.polecat.live';
const prefix = '/4d/dev/';
const catalog = JSON.parse(await fs.readFile(path.join(root, 'walk/audio/catalog.json'), 'utf8'));
let pw;
try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
const proxyInfo = proxyUrl ? new URL(proxyUrl) : null;
const proxy = proxyInfo ? { server: proxyInfo.origin, ...(proxyInfo.username ? { username: decodeURIComponent(proxyInfo.username), password: decodeURIComponent(proxyInfo.password) } : {}) } : undefined;
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.css': 'text/css', '.wasm': 'application/wasm',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };

for (const width of [390, 1280]) {
  const browser = await pw.chromium.launch({ proxy, executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width, height: 780 }, hasTouch: width === 390 });
    const errors = [], requests = [], badMedia = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => {
      if (r.url().startsWith(catalog.hosting.public_base) || r.url().includes('/walk/audio/')) requests.push(r.url());
    });
    page.on('response', r => {
      if (r.url().startsWith(catalog.hosting.public_base) && ![200, 206].includes(r.status())) badMedia.push([r.status(), r.url()]);
    });
    // Only app files are replayed. Bucket requests go to the real public host,
    // so its actual browser CORS policy and media response remain under test.
    await page.route(origin + '/**', async route => {
      const url = new URL(route.request().url());
      if (!url.pathname.startsWith(prefix)) return route.fulfill({ status: 404, body: 'Outside fixture' });
      let rel = decodeURIComponent(url.pathname.slice(prefix.length));
      if (rel.endsWith('/')) rel += 'index.html';
      const file = path.resolve(root, rel);
      if (!file.startsWith(root + path.sep)) return route.abort();
      try { await route.fulfill({ body: await fs.readFile(file), contentType: mime[path.extname(file)] ?? 'application/octet-stream' }); }
      catch { await route.fulfill({ status: 404, body: 'Not found' }); }
    });
    await page.goto(origin + prefix + 'walk/?year=1835&detail=light', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !!window.__chicago4d?.gesture, null, { timeout: 60000 });
    assert.equal(await page.locator('#arrival-sound').getAttribute('aria-pressed'), 'false');
    assert.equal(requests.length, 0, 'no audio catalogue or media request before opt-in');
    const toggle = page.locator('#arrival-sound');
    assert.equal((await toggle.textContent()).trim(), '', 'speaker has no visible text');
    const box = await toggle.boundingBox();
    assert.equal(box.width, 44); assert.equal(box.height, 44, 'compact icon retains a touch target');
    const capture = async stage => {
      if (!process.env.AUDIO_PROOF_DIR) return;
      await fs.mkdir(process.env.AUDIO_PROOF_DIR, {recursive:true});
      await page.screenshot({path:path.join(process.env.AUDIO_PROOF_DIR, `audio-${width}-${stage}.png`)});
    };
    await capture('muted');
    await toggle.click({ timeout: 30000 });
    await page.waitForFunction(() => window.__chicago4d?.sound?.state.context === 'running', null, { timeout: 30000 });
    assert.equal(await page.evaluate(() => __chicago4d.sound.state.recorded.playing), false);
    const musicURLs = catalog.assets.filter(a=>a.kind==='music').flatMap(a=>[a.opus,a.aac]);
    assert(!requests.some(url=>musicURLs.includes(url)), 'no period music request during arrival');
    await capture('loading-on');
    await page.waitForFunction(() => __chicago4d.ready === true && __chicago4d.welcome?.state === 'welcome', null, {timeout:240000,polling:500});
    await page.evaluate(() => {
      const a=__chicago4d; window.savedRender=a.renderer.render;
      a.renderer.render=(scene,camera)=>camera?.updateMatrixWorld?.();
    });
    await page.waitForFunction(() => __chicago4d.sound.state.recorded.voices.includes('wind'), null, { timeout: 30000 });
    assert(!requests.some(url=>musicURLs.includes(url)), 'no period music through the arrival choices');
    await page.evaluate(() => {
      const api = window.__chicago4d, analyser = api.audio.createAnalyser();
      // Insert a meter without changing gain or adding a second audible path.
      api.sound.nodes.master.disconnect(api.audio.destination);
      api.sound.nodes.master.connect(analyser); analyser.connect(api.audio.destination);
      window.__audioMeter = analyser;
    });
    await page.waitForFunction(() => {
      const values = new Float32Array(window.__audioMeter.fftSize);
      window.__audioMeter.getFloatTimeDomainData(values);
      return values.some(v => Math.abs(v) > 0.000001);
    }, null, { timeout: 30000, polling: 50 });
    const on = await page.evaluate(() => window.__chicago4d.sound.state);
    assert.equal(on.recorded.track, null, 'arrival ambience does not start the period score');
    assert.deepEqual(on.recorded.errors, []);
    assert.equal(await page.locator('#arrival-sound').getAttribute('aria-pressed'), 'true');
    assert(requests.some(u => u.startsWith(catalog.hosting.public_base)), 'real R2 ambience requested');
    await capture('on');
    await page.locator('#arrival-sound').click();
    assert(await page.evaluate(() => {
      const state = window.__chicago4d.sound.state;
      return state.silent && !state.recorded.playing && state.recorded.voices.length === 0;
    }));
    assert.equal(await page.locator('#arrival-sound').getAttribute('aria-pressed'), 'false');
    await toggle.click();
    await page.locator('#home-roam').click();
    await page.waitForFunction(() => __chicago4d.sound.state.recorded.playing, null, {timeout:45000});
    assert.equal(await page.evaluate(() => __chicago4d.sound.state.recorded.track), 'Border Ballad');
    assert.equal(await page.locator('#s-sound-effects').getAttribute('aria-describedby'), 's-sound-effects-help');
    assert.match(await page.locator('#s-sound-effects-help').textContent(), /wagon wheels and harness jingles/);
    assert.match(await page.locator('#s-sound-ambience-help').textContent(), /wind, lake waves, birds and insects/);
    await page.evaluate(()=>{__chicago4d.hud.setPanel(true);__chicago4d.hud.selectTab('settings');});
    await page.locator('#s-sound').scrollIntoViewIfNeeded();
    await capture('settings');
    assert.deepEqual(badMedia, []); assert.deepEqual(errors, []);
    await page.evaluate(()=>{__chicago4d.sound.dispose();__chicago4d.renderer.render=savedRender;});
    console.log(`ARRIVAL AUDIO PASS ${width}px: real published page, zero muted fetches, trusted speaker click, real R2 ambience through master gain, no arrival music, second click mutes, period music after entering town, settings examples, zero page/media errors`);
  } finally { await browser.close(); }
}
