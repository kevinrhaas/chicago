// T-3658: real Navigator markup/CSS, native browser magnification and picture modal.
// A tiny WebGL canvas runs main.js's exact resize body; this is not a full-town smoke.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const main = fs.readFileSync(path.join(web, 'js/main.js'), 'utf8');
const meta = index.match(/<meta name="viewport"[^>]+>/)[0];
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)[0];
const resizeBody = main.match(/  function resize\(\) \{([\s\S]*?)\n  \}\n  window.addEventListener\('resize', resize\);/)[1];
assert(!/maximum-scale=1|user-scalable=no/.test(meta));
const out = process.env.C4D_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });
const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#237279"/><circle cx="150" cy="110" r="70" fill="#ebc17c"/></svg>';
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en"><head>${meta}${imports}
      <link rel="stylesheet" href="/css/walk.css"><link rel="stylesheet" href="/css/drawer.css"><link rel="stylesheet" href="/css/navigator.css">
      <link rel="stylesheet" href="/css/card.css"></head><body><canvas id="view"></canvas>
      <button id="outside" style="position:fixed;top:0;right:0">Outside control</button>
      <section id="already-inert" inert aria-hidden="true"><button>Unavailable control</button></section>
      <section id="retained-aria" aria-hidden="false"></section></body></html>`); return;
  }
  if (url.pathname.endsWith('.svg')) {
    res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); res.end(svg); return;
  }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript'
      : file.endsWith('.html') ? 'text/html' : 'text/css' }); res.end(err ? '' : bytes);
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE,
  args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const receipts = [];
try {
  for (const width of [390, 1280]) {
    const phone = width === 390;
    const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 },
      isMobile: phone, hasTouch: phone, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [];
    const pendingPictures = [];
    await page.route('**/pending-*.svg', route => pendingPictures.push(route));
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(origin);
    await page.evaluate(async resizeBody => {
      const THREE = await import('three');
      const { viewportSize } = await import('/js/viewport.js');
      const { createTouchBackend } = await import('/js/controls/touch.js');
      const { createIntent } = await import('/js/controls/intent.js');
      const { createNavigator } = await import('/js/navigator.js');
      const picture = await import('/js/pictures.js');
      window.fixturePicture = picture;
      const source = new DOMParser().parseFromString(await (await fetch('/index.html')).text(), 'text/html');
      const root = source.getElementById('navigator'); document.body.append(root);
      window.fixtureNav = createNavigator({ root, scene: { id: '1835', target_date: '1835-07-01' } });
      fixtureNav.open(2);
      const screen = root.querySelector('.nav-screen');
      const opener = document.createElement('button'); opener.id = 'open-picture'; opener.textContent = 'Open fixture pictures';
      screen.prepend(opener);
      for (let i = 0; i < 24; i++) {
        const p = document.createElement('p'); p.textContent = `Reading paragraph ${i + 1}. Historical evidence remains readable when the browser magnifies it.`;
        screen.append(p);
      }
      const bottom = document.createElement('button'); bottom.id = 'reading-end'; bottom.textContent = 'End of reading'; screen.append(bottom);
      window.fixtureDoc = { image_store: { base_url: location.origin + '/' }, by_structure: { fixture: [
        { id: 'one', title: 'Fixture picture one', kind: 'Photograph', holder: 'Test fixture', rights: 'Public domain',
          held: { t: 'one.svg', f: 'pending-one.svg' }, url: 'https://example.org/one' },
        { id: 'two', title: 'Fixture picture two', kind: 'Photograph', holder: 'Test fixture', rights: 'Public domain',
          held: { t: 'two.svg', f: 'pending-two.svg' }, url: 'https://example.org/two' },
      ] } };
      opener.onclick = () => picture.openPictureViewer(fixtureDoc, 'fixture', 0);
      const canvas = document.getElementById('view');
      const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
      renderer.setClearColor('#28626b'); renderer.setPixelRatio(1);
      window.fixtureResizeCount = 0;
      const setSize = renderer.setSize.bind(renderer);
      renderer.setSize = (...args) => { fixtureResizeCount++; return setSize(...args); };
      window.fixtureRenderer = renderer;
      const camera = new THREE.PerspectiveCamera();
      const resize = new Function('viewportSize', 'renderer', 'camera', 'H_FOV_DEG', 'DEG', 'THREE', 'gate',
        `return function resize() {${resizeBody}\n};`)(viewportSize, renderer, camera, 76, Math.PI / 180, THREE, null);
      window.fixtureResize = () => { resize(); renderer.clear(); };
      window.addEventListener('resize', fixtureResize);
      visualViewport?.addEventListener('resize', fixtureResize);
      window.fixtureIntent = createIntent();
      window.fixtureTouch = createTouchBackend({ intent: fixtureIntent, domElement: canvas, onViewport: fixtureResize });
      if (matchMedia('(pointer: coarse)').matches) fixtureTouch.enable();
      fixtureResize();
    }, resizeBody);

    const opener = page.locator('#open-picture');
    await opener.focus(); await page.keyboard.press('Enter');
    const dialog = page.locator('.pic-viewer');
    assert.equal(await dialog.evaluate(el => el.matches(':modal')), true, 'native modal is in the top layer');
    assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-pv-close')), true);
    if (out) await page.screenshot({ path: path.join(out, `${width}-picture-modal.png`) });
    await page.evaluate(() => document.getElementById('outside').focus());
    assert.equal(await page.evaluate(() => !!document.activeElement.closest('.pic-viewer')), true, 'background cannot receive focus');
    await dialog.locator('[data-pv-full]').focus();
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.evaluate(() => document.activeElement.href), 'https://example.org/one');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-pv-full')), true);
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => !!document.activeElement.closest('.pic-viewer')), true);
    }
    const beforeLevel = await page.evaluate(() => fixtureNav.level);
    await page.keyboard.press('n');
    assert.equal(await page.evaluate(() => fixtureNav.level), beforeLevel, 'modal prevents Navigator hotkey');
    await dialog.locator('[data-pv-credit] a').focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await dialog.locator('[data-pv-count]').textContent(), '2 / 2');
    assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-pv-close')), true, 'changing credit retains modal focus');
    assert.equal(await dialog.evaluate(el => !!el._loading), true, 'full-size image is still pending when closed');
    await page.keyboard.press('Escape');
    assert.equal(await dialog.isVisible(), false);
    assert.equal(await page.evaluate(() => document.activeElement.id), 'open-picture');
    assert.equal(await page.evaluate(() => fixtureNav.level), beforeLevel, 'Escape closes only the modal');
    assert.deepEqual(await dialog.evaluate(el => ({ open: el.open, image: el.querySelector('img').getAttribute('src'),
      loading: el._loading, doc: el._doc })), { open: false, image: null, loading: null, doc: null });
    await page.unroute('**/pending-*.svg');
    for (const route of pendingPictures) {
      await route.fulfill({ contentType: 'image/svg+xml', body: svg }).catch(() => {}); // A removed src may already have cancelled it.
    }
    await page.waitForTimeout(30);
    assert.equal(await dialog.locator('img').getAttribute('src'), null, 'late image delivery cannot revive the closed image');
    assert.deepEqual(await page.evaluate(() => ({ inert: document.getElementById('already-inert').inert,
      hidden: document.getElementById('already-inert').getAttribute('aria-hidden'),
      retained: document.getElementById('retained-aria').getAttribute('aria-hidden'),
      outside: document.getElementById('outside').inert })), { inert: true, hidden: 'true', retained: 'false', outside: false });
    await page.evaluate(() => {
      fixturePicture.openPictureViewer(fixtureDoc, 'fixture', 0);
      fixturePicture.closePictureViewer();
      fixturePicture.openPictureViewer({ ...fixtureDoc, by_structure: { fixture: [fixtureDoc.by_structure.fixture[0]] } }, 'fixture', 0);
    });
    await page.waitForTimeout(30);
    assert.equal(await dialog.evaluate(el => el.matches(':modal')), true, 'old close event does not close a reopened modal');
    await dialog.locator('[data-pv-full]').focus(); await page.keyboard.press('Shift+Tab');
    assert.equal(await page.evaluate(() => document.activeElement.href), 'https://example.org/one', 'hidden arrows are skipped');
    await dialog.evaluate(el => el.close());
    await page.waitForFunction(() => document.querySelector('.pic-viewer').hidden);

    const before = await page.evaluate(() => ({ canvas: [view.width, view.height], resizes: fixtureResizeCount, vh: document.documentElement.style.getPropertyValue('--vh'),
      sheet: document.getElementById('navigator').getBoundingClientRect().height, scale: visualViewport.scale,
      touch: [getComputedStyle(document.getElementById('navigator')).touchAction,
        getComputedStyle(document.getElementById('nav-home')).touchAction,
        getComputedStyle(document.getElementById('nav-grip')).touchAction, getComputedStyle(view).touchAction] }));
    if (phone) {
      const permitsPinch = value => value.includes('pinch-zoom') || value === 'manipulation' || value === 'auto';
      assert(before.touch.slice(0, 2).every(permitsPinch), JSON.stringify(before.touch));
      assert.deepEqual(before.touch.slice(2), ['none', 'none'], 'only handles and world reserve gestures');
      const client = await context.newCDPSession(page);
      const box = await opener.boundingBox();
      const pinchAt = { x: 130, y: Math.min(600, box.y + 200) };
      await page.evaluate(() => {
        window.pinchStarts = [];
        document.addEventListener('pointerdown', e => {
          const ancestors = []; for (let el = e.target; el; el = el.parentElement) ancestors.push([el.tagName, el.id, getComputedStyle(el).touchAction]);
          pinchStarts.push({ x: e.clientX, y: e.clientY, ancestors });
        }, { capture: true });
      });
      // Chromium's synthesized pinch emitted touches without zoom even on a
      // plain control page in this environment. Dispatch actual multi-touch;
      // CDP coordinates are visual-viewport CSS pixels, so keep each physical
      // finger position stable as the browser's own scale changes underneath it.
      await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [
        { id: 10, x: pinchAt.x - 45, y: pinchAt.y }, { id: 11, x: pinchAt.x + 45, y: pinchAt.y },
      ] });
      for (let step = 1; step <= 35; step++) {
        const scale = await page.evaluate(() => visualViewport.scale);
        if (scale >= 1.95) break;
        await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [
          { id: 10, x: (pinchAt.x - 45 - step * 3) / scale, y: pinchAt.y / scale },
          { id: 11, x: (pinchAt.x + 45 + step * 3) / scale, y: pinchAt.y / scale },
        ] });
        await page.waitForTimeout(20);
      }
      await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      await page.waitForFunction(() => visualViewport.scale > 1.8, null, { timeout: 3000 });
      const zoom = await page.evaluate(() => ({ canvas: [view.width, view.height], resizes: fixtureResizeCount, vh: document.documentElement.style.getPropertyValue('--vh'),
        sheet: document.getElementById('navigator').getBoundingClientRect().height, scale: visualViewport.scale, starts: pinchStarts }));
      assert.deepEqual(zoom.canvas, before.canvas, 'native pinch does not shrink the GPU drawing buffer');
      assert.equal(zoom.resizes, before.resizes, 'native pinch does not repeatedly reallocate the same drawing buffer');
      assert.equal(zoom.vh, before.vh);
      assert(Math.abs(zoom.sheet - before.sheet) < 1);
      await page.locator('#reading-end').focus();
      assert(await page.locator('#nav-home').evaluate(el => el.scrollTop > 0), 'magnified reading still scrolls to its final control');
      if (out) await page.screenshot({ path: path.join(out, '390-native-pinch.png') });
      await page.evaluate(() => {
        fixtureNav.dock(); fixtureIntent.clearLook();
        window.fixtureTouchTrace = [];
        view.addEventListener('pointerdown', e => fixtureTouchTrace.push({ x: e.clientX, y: e.clientY,
          offset: visualViewport.offsetLeft, visibleWidth: visualViewport.width, scale: visualViewport.scale }));
      });
      const scale = await page.evaluate(() => visualViewport.scale);
      await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [
        { id: 1, x: 80 / scale, y: 300 / scale }, { id: 2, x: 250 / scale, y: 300 / scale },
      ] });
      await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [
        { id: 1, x: 80 / scale, y: 230 / scale }, { id: 2, x: 280 / scale, y: 280 / scale },
      ] });
      const thumbs = await page.evaluate(() => ({ forward: fixtureIntent.forward, yaw: fixtureIntent.yawDelta,
        pitch: fixtureIntent.pitchDelta, trace: fixtureTouchTrace }));
      await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      assert(thumbs.forward > 0 && thumbs.yaw < 0 && thumbs.pitch > 0,
        `off-center magnification keeps independent movement and look thumbs: ${JSON.stringify(thumbs)}`);
      await page.evaluate(() => fixtureNav.open(2));
      const panBefore = await page.evaluate(() => visualViewport.offsetLeft);
      await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ id: 20, x: 140 / scale, y: 350 / scale }] });
      for (let step = 1; step <= 8; step++) {
        await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ id: 20, x: (140 - step * 10) / scale, y: 350 / scale }] });
        await page.waitForTimeout(20);
      }
      await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      const panAfter = await page.evaluate(() => visualViewport.offsetLeft);
      assert(Math.abs(panAfter - panBefore) > 10, `magnified reading permits horizontal browser pan: ${JSON.stringify({ panBefore, panAfter, trace: await page.evaluate(() => pinchStarts.at(-1)) })}`);
      // Settings and other hosted drawer sections have their own scroll area.
      // Exercise that real CSS nesting too; an inner contain would trap zoom pan.
      await page.evaluate(() => {
        const screen = document.getElementById('nav-home');
        const panel = document.createElement('section'); panel.className = 'hud-panel';
        const scroll = document.createElement('div'); scroll.className = 'panel-scroll';
        scroll.append(...screen.childNodes); panel.append(scroll); screen.append(panel);
        scroll.scrollTop = scroll.scrollHeight;
      });
      await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ id: 21, x: 140 / scale, y: 350 / scale }] });
      for (let step = 1; step <= 8; step++) {
        await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ id: 21, x: (140 - step * 10) / scale, y: 350 / scale }] });
        await page.waitForTimeout(20);
      }
      await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      const nestedPan = await page.evaluate(() => visualViewport.offsetLeft);
      assert(Math.abs(nestedPan - panAfter) > 10, 'hosted Navigator panel also permits horizontal browser pan');
      await client.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 });
      await page.setViewportSize({ width: 780, height: 390 });
      await page.waitForFunction(() => view.width === 780 && view.height === 390);
      await page.setViewportSize({ width: 390, height: 780 });
      await page.waitForFunction(() => view.width === 390 && view.height === 780);
      receipts.push({ width, nativePinch: zoom, magnifiedThumbs: thumbs, nativePan: { before: panBefore, after: panAfter, afterHostedPanel: nestedPan },
        orientation: 'passed', modal: 'passed', errors });
    } else receipts.push({ width, modal: 'passed', errors });
    assert.deepEqual(errors, []);
    await context.close();
  }
  if (out) fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(receipts, null, 2));
  console.log('ACCESSIBILITY BROWSER PASS — both widths: modal keyboard cycle, isolation, focus return, image cleanup; native phone pinch and orientation preserve canvas and reading');
} finally { await browser.close(); server.close(); }
