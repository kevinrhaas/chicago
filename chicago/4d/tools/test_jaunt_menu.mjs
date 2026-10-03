#!/usr/bin/env node
// T-1259: the published welcome, real engine, and a content-only 55-row catalog.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url), { chromium } = require('playwright');
const root = path.resolve('../../site/4d'), out = path.resolve('docs/performance/jaunt-menu');
fs.mkdirSync(out, { recursive: true });
const catalog = JSON.parse(fs.readFileSync('data/jaunts/_fixtures/catalog-55.json'));
const pilot = JSON.parse(fs.readFileSync('data/sidecars/1835/jaunts/new-in-chicago.json'));
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname.replace(/^\/dev\//, '/');
  const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const receipts = [];
let activePage;
try {
  for (const viewport of [{ width: 390, height: 780 }, { width: 1280, height: 800 }].filter(v => !process.env.JAUNT_VIEWPORT || String(v.width) === process.env.JAUNT_VIEWPORT)) {
    const context = await browser.newContext({ viewport, isMobile: viewport.width === 390, hasTouch: viewport.width === 390, reducedMotion: 'reduce' });
    const page = activePage = await context.newPage(), errors = [], requests = [];
    page.setDefaultTimeout(90000);
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => { if (/jaunts\/|jaunt-menu.js|jaunt-preview.js/.test(r.url())) requests.push(r.url()); });
    await page.route('**/jaunts/catalog.json', r => r.fulfill({ json: catalog }));
    await page.route('**/jaunts/fixture-menu-*.json', r => {
      const id = path.basename(new URL(r.request().url()).pathname, '.json');
      const row = catalog.jaunts.find(row => row.id === id);
      return r.fulfill({ json: { ...pilot, id, title: row.title } });
    });
    const click = async locator => {
      console.log(`MENU ${viewport.width}: click ${await locator.first().textContent()}`);
      await locator.waitFor({ state: 'visible' });
      const point = await locator.evaluate(el => {
        el.scrollIntoView({ block: 'nearest' });
        const r = el.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2;
        if (el.disabled || !el.contains(document.elementFromPoint(x, y))) throw new Error('Control covered or disabled');
        return { x, y };
      });
      await page.mouse.click(point.x, point.y);
    };
    await page.goto(`http://127.0.0.1:${server.address().port}/${viewport.width === 1280 ? 'dev/' : ''}walk/?year=1835&seed=1259`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 180000 });
    assert.equal(requests.length, 0, 'no jaunt code or catalog at boot');
    // The scaffold smoke verifies continuous scene drawing separately. Keep the real
    // engine and DOM live, but stop background WebGL draws for menu-only interactions.
    await page.evaluate(() => __chicago4d.renderer.setAnimationLoop(null));
    console.log(`MENU ${viewport.width}: boot ready; no jaunt requests`);
    await click(page.locator('#welcome-sources'));
    await page.locator('#panel').waitFor({ state: 'visible' });
    assert(await page.getByRole('button', { name: /^Sources/ }).count());
    await click(page.locator('#panel-close'));
    await page.waitForSelector('#gate:not([hidden])');
    console.log(`MENU ${viewport.width}: opening catalog`);
    await click(page.locator('#welcome-jaunts'));
    await page.waitForSelector('.jaunt-list .jaunt-card');
    assert.equal(await page.locator('.jaunt-card').count(), 26);
    assert.equal(await page.locator('.jaunt-list .jaunt-card').count(), 20);
    assert.equal(await page.locator('.jaunt-featured .jaunt-card').count(), 6);
    console.log(`MENU ${viewport.width}: catalog ready`);
    await page.locator('#jaunt-menu-search').fill('tavern');
    assert.equal(await page.locator('.jaunt-list .jaunt-card').count(), 11);
    assert(!(await page.locator('.jaunt-featured').isVisible()));
    await click(page.getByRole('button', { name: 'Taverns', exact: true }));
    assert.equal(await page.locator('.jaunt-list .jaunt-card').count(), 11);
    await click(page.getByRole('button', { name: 'Clear filters', exact: true }));
    assert.equal(await page.locator('.jaunt-list .jaunt-card').count(), 20);
    await click(page.getByRole('button', { name: 'More outings', exact: true }));
    const card = page.locator('.jaunt-list [data-jaunt="fixture-menu-25"]');
    const select = card.locator('select'), duration = card.locator('[data-jaunt-estimate]');
    await select.selectOption('walk'); const walking = await duration.innerText();
    await select.selectOption('instantly'); assert.notEqual(await duration.innerText(), walking);
    assert.match(await card.innerText(), /Outing 25.*sample outing.*Taverns.*5 stops.*about.*min.*Instantly/s);
    // Enter activates a real Start control and the exact scroll/focus comes back after End.
    await card.getByRole('button', { name: 'Start Jaunt', exact: true }).evaluate(el => { el.scrollIntoView({ block: 'nearest' }); el.focus({ preventScroll: true }); });
    const before = await page.locator('#welcome-jaunts-region').evaluate(el => el.scrollTop);
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop');
    await page.evaluate(() => __chicago4d.jaunts.end());
    await page.waitForFunction(() => document.activeElement?.dataset.action === 'start');
    const returned = await page.evaluate(() => ({ scroll: document.querySelector('#welcome-jaunts-region').scrollTop,
      focus: document.activeElement.outerHTML, rect: document.activeElement.getBoundingClientRect().toJSON(), region: document.querySelector('#welcome-jaunts-region').getBoundingClientRect().toJSON(), card: document.activeElement.closest('[data-jaunt]')?.dataset.jaunt }));
    assert(returned.rect.y >= returned.region.y && returned.rect.bottom <= returned.region.bottom + 1, 'restored Start stays visible');
    assert.equal(returned.card, 'fixture-menu-25'); assert(Math.abs(returned.scroll - before) <= 1, JSON.stringify({ before, returned }));
    await page.screenshot({ path: path.join(out, `${viewport.width}-return.png`) });
    await click(card.getByRole('button', { name: 'Start Jaunt', exact: true }));
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop');
    await page.evaluate(() => __chicago4d.jaunts.menu());
    await page.waitForSelector('.jaunt-session-note');
    await page.locator('#jaunt-menu-search').fill('tavern');
    await click(page.getByRole('button', { name: 'Resume Jaunt', exact: true }));
    await page.waitForFunction(() => __chicago4d.jaunts.state?.phase === 'atStop');
    assert.equal(await page.evaluate(() => __chicago4d.jaunts.state.jaunt.id), 'fixture-menu-25');
    await page.evaluate(() => __chicago4d.jaunts.menu());
    await page.waitForSelector('.jaunt-session-note');
    await click(page.locator('#welcome-explore'));
    assert.equal(await page.evaluate(() => __chicago4d.jaunts.state.jaunt), null);
    await click(page.locator('#welcome-jaunts'));
    await page.waitForSelector('#jaunt-menu-search');
    assert.equal(await page.locator('#jaunt-menu-search').inputValue(), 'tavern');
    await click(page.getByRole('button', { name: 'Clear filters', exact: true }));
    await click(page.getByRole('button', { name: 'More outings', exact: true }));
    await click(page.getByRole('button', { name: 'More outings', exact: true }));
    assert.equal(await page.locator('.jaunt-list .jaunt-card').count(), 15);
    const held = page.locator('[data-jaunt="fixture-menu-54"]');
    assert.match(await held.innerText(), /Unavailable — Consultation required/);
    assert.equal(await held.getByRole('button', { name: 'Start Jaunt', exact: true }).count(), 0);
    for (const size of viewport.width === 390 ? [{ width: 390, height: 430 }, viewport] : [viewport]) {
      await page.setViewportSize(size);
      await page.locator('#jaunt-menu-search').focus();
      await page.getByRole('button', { name: 'Earlier outings', exact: true }).scrollIntoViewIfNeeded();
      const layout = await page.evaluate(() => ({ width: innerWidth, body: document.body.scrollWidth,
        scroll: document.querySelector('#welcome-jaunts-region').getBoundingClientRect().height,
        target: document.querySelector('.jaunt-window-nav button').getBoundingClientRect().toJSON(), height: innerHeight }));
      assert(layout.body <= layout.width + 1 && layout.scroll > 44, JSON.stringify(layout));
      assert(layout.target.y >= 0 && layout.target.bottom <= layout.height && layout.target.height >= 44, JSON.stringify(layout));
      await page.screenshot({ path: path.join(out, `${size.width}-${size.height}-window.png`) });
    }
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => __chicago4d.welcome.state), 'world');
    assert.equal(errors.length, 0, errors.join('\n'));
    receipts.push({ viewport, bootJauntRequests: 0, maxCards: 26, beforeScroll: before, returned, pageErrors: errors });
    console.log(`MENU ${viewport.width}: PASS — filters, 55 rows, mode, Start/End, resume, Explore, layouts, Escape`);
    await context.close();
  }
  fs.writeFileSync(path.join(out, 'acceptance.json'), JSON.stringify(receipts, null, 2) + '\n');
} catch (error) {
  if (activePage) {
    await activePage.screenshot({ path: path.join(out, 'failure.png') }).catch(() => {});
    console.error(await activePage.evaluate(() => ({ active: document.activeElement?.outerHTML, gateHidden: document.querySelector('#gate')?.hidden, hudHidden: document.querySelector('#hud')?.hidden, panelHidden: document.querySelector('#panel')?.hidden, text: document.body.innerText.slice(-3000) })).catch(() => null));
  }
  throw error;
} finally { await browser.close(); server.close(); }
