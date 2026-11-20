// T-3671 (WCAG 2.1.4): single-key shortcuts can be turned off in Settings › Look › Letter keys.
// A browser fixture: the real letter-keys.js and settings-app.js row, no town.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { isCharacterShortcut, blocksKey, normalLetterKeys } from '../renderers/web/js/letter-keys.js';
const { chromium } = createRequire(import.meta.url)('playwright');

// Pure rules first.
for (const k of ['w', 'W', 'e', '1', '?', '/', ',', '[', 'é', '+']) assert(isCharacterShortcut({ key: k }), `${k} is a character key`);
for (const k of [' ', 'ArrowUp', 'Enter', 'Escape', 'Tab', 'Home', 'Shift', 'F1']) assert(!isCharacterShortcut({ key: k }), `${k} is not`);
assert(!isCharacterShortcut({ key: 'c', ctrlKey: true }), 'Ctrl+C is left alone');
assert(!isCharacterShortcut({ key: 'r', metaKey: true }), 'Meta+R is left alone');
assert(!blocksKey({ key: 'w', target: null }, true), 'On lets letters through');
assert(blocksKey({ key: 'w', target: null }, false), 'Off holds letters back');
assert(!blocksKey({ key: 'w', target: { nodeType: 1, tagName: 'INPUT', type: 'text' } }, false), 'a text field takes every key');
assert(blocksKey({ key: 'w', target: { nodeType: 1, tagName: 'BUTTON' } }, false), 'a button does not');
assert.equal(normalLetterKeys('x'), 'on');
assert.equal(normalLetterKeys('off'), 'off');

const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)[0];
// recall.js loads before main.js and is what brings the filter in first.
assert(index.indexOf('src="./js/recall.js"') > 0 && index.indexOf('src="./js/recall.js"') < index.indexOf('src="./js/main.js"'), 'recall.js loads ahead of main.js');
assert(/import '\.\/letter-keys\.js'/.test(fs.readFileSync(path.join(web, 'js/recall.js'), 'utf8')), 'recall.js imports letter-keys.js');

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en"><head>${imports}
      <link rel="stylesheet" href="/css/walk.css"><link rel="stylesheet" href="/css/navigator.css"></head>
      <body><section class="settings-group" data-set-pane="look"><div id="s-look"></div></section>
      <input id="note" type="text"><button id="b">Key</button></body></html>`); return;
  }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : 'text/css' });
    res.end(err ? '' : bytes);
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 } });
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(origin);
    await page.evaluate(async () => {
      await import('/js/letter-keys.js');
      const app = await import('/js/settings-app.js');
      window.__heard = [];
      // A page handler registered later, at window capture like welcome.js's.
      window.addEventListener('keydown', (e) => window.__heard.push(e.key), true);
      app.wireLetterKeys(app.letterKeysGroup(document));
    });
    const heard = () => page.evaluate(() => window.__heard.splice(0));
    await page.focus('#b');
    await page.keyboard.press('w'); await page.keyboard.press('ArrowUp');
    assert.deepEqual(await heard(), ['w', 'ArrowUp'], `${width}: On — letters reach the page`);

    // The row: a labelled radio group, one Tab stop, the arrows move the choice.
    const row = await page.evaluate(() => {
      const seg = document.getElementById('s-letter-keys');
      const radios = [...seg.querySelectorAll('[role=radio]')];
      return { role: seg.getAttribute('role'), label: document.getElementById(seg.getAttribute('aria-labelledby'))?.textContent,
        names: radios.map(r => r.textContent), checked: radios.map(r => r.getAttribute('aria-checked')), tabs: radios.map(r => r.tabIndex),
        described: !!document.getElementById(seg.getAttribute('aria-describedby'))?.textContent };
    });
    assert.deepEqual(row, { role: 'radiogroup', label: 'Letter keys', names: ['On', 'Off'], checked: ['true', 'false'], tabs: [0, -1], described: true }, `${width}: row`);
    await page.focus('#s-letter-keys [data-letter-keys="on"]');
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.evaluate(() => document.activeElement.dataset.letterKeys), 'off', `${width}: arrow moves to Off`);
    assert.equal(await page.evaluate(() => localStorage.getItem('chicago4d.letterKeys')), 'off', `${width}: stored`);
    await heard();

    await page.focus('#b');
    await page.keyboard.press('w'); await page.keyboard.press('1'); await page.keyboard.press('?');
    await page.keyboard.press('ArrowUp'); await page.keyboard.press('Escape'); await page.keyboard.press('Enter');
    assert.deepEqual(await heard(), ['ArrowUp', 'Escape', 'Enter'], `${width}: Off — letters held back, arrows/Esc/Enter pass`);
    await page.keyboard.press('Control+a');
    assert.deepEqual(await heard(), ['Control', 'a'], `${width}: Off — Ctrl chords pass`);
    await page.focus('#note');
    await page.keyboard.type('wasd');
    assert.equal(await page.inputValue('#note'), 'wasd', `${width}: a text field still types`);
    assert.deepEqual(await heard(), ['w', 'a', 's', 'd'], `${width}: and its keys still reach the page`);

    // Kept across a reload.
    await page.reload();
    const after = await page.evaluate(async () => (await import('/js/letter-keys.js')).letterKeysChoice());
    assert.equal(after, 'off', `${width}: kept after reload`);
    assert.deepEqual(errors, [], `${width}: no page errors`);
    console.log(`PASS ${width}: Letter keys On/Off — held back when Off, arrows and controls still answer, kept`);
    await context.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log('A11Y LETTER KEYS PASS — WCAG 2.1.4 single-key shortcuts can be turned off');
