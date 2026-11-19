#!/usr/bin/env node
// T-3671 (WCAG 2.1 AA, the menus): keyboard and screen-reader paths through the Navigator's
// rail, its screens, the sections' tab row and Settings' own tabs, over the page's real
// markup, CSS, hud.js, navigator.js and the apps — no town, no main.js.
//
// Asserts: the skip link (2.4.1), the title per year and screen (2.4.2), the canvas's name
// per year (1.1.1), roles/names/states of every tab row (4.1.2), label in name (2.5.3),
// headings in every screen (1.3.1), focus into a screen on open and back to the rail key
// (or the grip) on close, from the device and from a section's Escape (2.4.3), arrows that
// move without opening (3.2.1), visible focus (2.4.7), and the status line (4.1.3).
//
//   node tools/test_a11y_menus.mjs          (C4D_TEST_OUT=dir saves screenshots)
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pageTitle } from '../renderers/web/js/a11y-announce.js';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const html = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const out = process.env.C4D_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });

// ---- the markup and the pure parts ------------------------------------------------------
assert.match(html, /<html lang="en"/, 'the page names its language (3.1.1)');
assert.match(html, /<a class="skip-link" id="skip-navigator" href="#navigator"[^>]*>Skip to the Navigator<\/a>\s*(?:<!--[\s\S]*?-->\s*)?<div id="hud"[^>]*role="main"/,
  'the skip link stands right before the HUD, which is the page\'s main landmark');
assert.equal(pageTitle({ year: '1835' }), '1835 · 4D Chicago');
assert.equal(pageTitle({ year: '1904', screen: 'Settings' }), 'Settings · 1904 · 4D Chicago');
assert.equal(pageTitle({}), '4D Chicago');

// The page without its boot scripts: the fixture builds the HUD and the Navigator itself.
const page0 = html.replace(/<script type="module" src="[^"]+"><\/script>/g, '');
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') { res.setHeader('Content-Type', 'text/html'); res.end(page0); return; }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    const type = file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css'
      : file.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    res.writeHead(err ? 404 : 200, { 'Content-Type': type }); res.end(err ? '' : bytes);
  });
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
const settle = (page, ms = 120) => page.waitForTimeout(ms);
try {
  for (const width of [1280, 390]) {
    const phone = width === 390;
    const where = phone ? 'phone' : 'desktop';
    const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 },
      isMobile: phone, hasTouch: phone, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(origin);
    const active = () => page.evaluate(() => {
      const a = document.activeElement;
      return { id: a?.id ?? '', tag: a?.tagName ?? '', inNav: !!a?.closest?.('#navigator'), screen: a?.closest?.('.nav-screen')?.id ?? '' };
    });
    // Before the town: the skip link is out of the page while the arrival is up.
    assert.equal(await page.locator('#skip-navigator').evaluate((el) => getComputedStyle(el).display), 'none',
      `${where}: no skip link while the HUD is hidden`);
    await page.evaluate(async () => {
      const { createHud } = await import('/js/hud.js');
      const { createNavigator } = await import('/js/navigator.js');
      const { APPS } = await import('/js/apps/index.js');
      const host = await import('/js/apps/drawer-host.js');
      document.getElementById('gate').hidden = true;
      const hudRoot = document.getElementById('hud');
      const scene = { id: '1835', target_date: '1835-07-01' };
      const hud = createHud({ root: hudRoot, scene, registry: new Map(), isTouch: false,
        destinations: { targets: [], groups: [], search: () => [], count: () => 0 },
        onConfidence() {}, onFly() {}, onHelp() {}, onSetting() {}, onGoTo() {}, onHideLevel() {}, onTravelStop() {}, onShowGuide() {} });
      hudRoot.hidden = false;
      const api = { hud };
      const nav = createNavigator({ root: document.getElementById('navigator'), scene, apps: APPS,
        escFree: () => (document.getElementById('panel')?.hidden ?? true),
        context: () => ({ api, scene, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false, actions: {} }) });
      host.install({ hud, navigator: nav, doc: document });
      window.fx = { hud, nav, announce: (await import('/js/a11y-announce.js')).announce };
    });
    await settle(page, 300);
    const status = () => page.evaluate(() => document.getElementById('a11y-status')?.textContent ?? '');

    // ---- page level: title, canvas, skip link ----
    assert.equal(await page.title(), '1835 · 4D Chicago', `${where}: the docked title names the year`);
    assert.deepEqual(await page.locator('#view').evaluate((el) => [el.getAttribute('role'), el.getAttribute('aria-label')]),
      ['img', 'Chicago in 1835, a walkable 3-D view'], `${where}: the canvas says which year it shows`);
    await page.locator('#skip-navigator').focus();
    const skipBox = await page.locator('#skip-navigator').boundingBox();
    assert.ok(skipBox && skipBox.y >= 0 && skipBox.height > 20, `${where}: the focused skip link is in sight (${JSON.stringify(skipBox)})`);
    assert.notEqual(await page.locator('#skip-navigator').evaluate((el) => getComputedStyle(el).outlineStyle), 'none', `${where}: and shows its focus`);
    if (out) await page.screenshot({ path: path.join(out, `menus-skip-link-${width}.png`) });
    await page.keyboard.press('Enter');
    await settle(page);
    assert.equal(await page.evaluate(() => fx.nav.level > 0), true, `${where}: the skip link opens the Navigator`);
    assert.equal((await active()).id, 'nav-home', `${where}: and puts focus in its screen`);
    assert.equal(await page.title(), 'Home · 1835 · 4D Chicago', `${where}: the title names the open screen`);

    // ---- the rail: a tablist, one Tab stop, arrows that move without opening ----
    const rail = await page.evaluate(() => {
      const list = document.querySelector('#nav-rail .nav-tabs');
      const tabs = [...list.querySelectorAll('[role="tab"]')].filter((b) => !b.hidden);
      return { role: list.getAttribute('role'), orientation: list.getAttribute('aria-orientation'),
        stops: tabs.filter((b) => b.tabIndex === 0).map((b) => b.dataset.app),
        names: tabs.map((b) => [b.getAttribute('aria-label'), b.querySelector('.nav-app-label')?.textContent ?? '']),
        ids: tabs.map((b) => b.dataset.app) };
    });
    assert.equal(rail.role, 'tablist');
    assert.equal(rail.orientation, phone ? 'horizontal' : 'vertical', `${where}: the rail says which way its arrows run`);
    assert.deepEqual(rail.stops, ['home'], `${where}: one Tab stop on the rail, the open app's`);
    for (const [name, label] of rail.names) assert.ok(name && name.includes(label), `${where}: "${label}" is in its tab's name "${name}" (2.5.3)`);
    await page.locator('#nav-tab-home').focus();
    await page.keyboard.press(phone ? 'ArrowRight' : 'ArrowDown');
    assert.equal((await active()).id, `nav-tab-${rail.ids[1]}`, `${where}: an arrow moves along the rail`);
    assert.equal(await page.evaluate(() => fx.nav.app), 'home', `${where}: and opens nothing (3.2.1)`);
    assert.notEqual(await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle), 'none', `${where}: a rail key shows its focus (2.4.7)`);
    await page.keyboard.press('End');
    assert.equal((await active()).id, `nav-tab-${rail.ids.at(-1)}`, `${where}: End goes to the rail's last key`);
    await page.keyboard.press('Home');
    assert.equal((await active()).id, 'nav-tab-home', `${where}: Home to its first`);
    if (out) {
      await page.locator('#nav-tab-settings').focus();
      await page.screenshot({ path: path.join(out, `menus-rail-focus-${width}.png`) });
    }

    // ---- every screen: opened from its key, focus goes in, it is a named tabpanel with a heading ----
    const checked = [];
    for (const id of rail.ids) {
      await page.locator(`#nav-tab-${id}`).focus();
      await page.keyboard.press('Enter');
      await settle(page, 200);
      if (await page.evaluate(() => fx.nav.level) === 0 || await page.evaluate(() => fx.nav.app) !== id) continue; // a launch
      const s = await page.evaluate((id) => {
        const tab = document.getElementById(`nav-tab-${id}`);
        const panel = document.getElementById(tab.getAttribute('aria-controls'));
        const heads = [...panel.querySelectorAll('h1, h2, h3, [role="heading"]')].map((h) => h.textContent.trim()).filter(Boolean);
        const a = document.activeElement;
        return { panel: panel?.id, role: panel?.getAttribute('role'), by: panel?.getAttribute('aria-labelledby'), heads,
          focusIn: panel.contains(a), ring: getComputedStyle(a).outlineStyle, selected: tab.getAttribute('aria-selected') };
      }, id);
      assert.equal(s.role, 'tabpanel', `${where}: ${id}'s screen is a tabpanel`);
      // Named by its tab; Home by its own heading, "Navigator Home".
      assert.equal(s.by, id === 'home' ? 'nav-home-title' : `nav-tab-${id}`, `${where}: ${id}'s screen is named`);
      assert.equal(s.selected, 'true');
      assert.ok(s.focusIn, `${where}: opening ${id} puts focus in its screen (2.4.3)`);
      assert.notEqual(s.ring, 'none', `${where}: ${id}'s screen shows the focus it took`);
      assert.ok(s.heads.length > 0, `${where}: ${id}'s screen has a heading (1.3.1)`);
      // Every key a visitor can see in the device has a name (4.1.2).
      const nameless = await page.evaluate(() => [...document.querySelectorAll('#navigator button, #navigator a[href], #navigator [role="tab"]')]
        .filter((b) => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden')
        .filter((b) => {
          const by = (b.getAttribute('aria-labelledby') ?? '').split(/\s+/).map((x) => document.getElementById(x)?.textContent ?? '').join('');
          return !(b.getAttribute('aria-label') || by.trim() || b.textContent.trim() || b.title);
        }).map((b) => b.outerHTML.slice(0, 80)));
      assert.deepEqual(nameless, [], `${where}: every visible key in ${id} has a name`);
      checked.push(id);
    }
    assert.ok(['home', 'map', 'guide', 'settings', 'confidence'].every((id) => checked.includes(id)), `${where}: the screens were all opened (${checked})`);

    // ---- closing hands focus back: to the rail key (desktop) or the grip (phone) ----
    await page.locator('#nav-tab-map').focus();
    await page.keyboard.press('Enter');
    await settle(page, 200);
    assert.equal(await page.title(), 'Map · 1835 · 4D Chicago');
    await page.keyboard.press('Escape');
    await settle(page, 150);
    assert.equal(await page.evaluate(() => fx.nav.level), 0, `${where}: Escape closes the device`);
    assert.equal((await active()).id, phone ? 'nav-grip' : 'nav-tab-map', `${where}: focus goes back to the key that reopens it`);
    assert.equal(await status(), 'Navigator closed', `${where}: and a screen reader hears it close (4.1.3)`);
    assert.equal(await page.title(), '1835 · 4D Chicago');

    // A screen opened by the page's own keys (the year chip, the map) takes focus too.
    await page.evaluate(() => fx.nav.select('jump', { focus: true }));
    await settle(page, 200);
    assert.equal((await active()).screen, 'nav-app-jump', `${where}: select(…, { focus: true }) puts focus in the screen`);
    // One opened by code says so instead.
    await page.evaluate(() => fx.nav.select('guide'));
    await settle(page, 200);
    assert.equal(await status(), 'Guide open', `${where}: a screen opened without focus is announced`);

    // ---- the sections' tab row (Guide: Controls · About): roving, its own app only ----
    const sect = await page.evaluate(() => {
      const tabs = [...document.querySelectorAll('.panel-tab')].filter((t) => !t.hidden && t.getClientRects().length);
      return tabs.map((t) => ({ tab: t.dataset.tab, stop: t.tabIndex, controls: t.getAttribute('aria-controls'),
        role: document.getElementById(t.getAttribute('aria-controls'))?.getAttribute('role'),
        by: document.getElementById(t.getAttribute('aria-controls'))?.getAttribute('aria-labelledby') === t.id }));
    });
    assert.deepEqual(sect.map((t) => t.tab), ['evidence', 'controls'].filter((k) => sect.some((t) => t.tab === k)), `${where}: Guide shows its own sections' tabs`);
    assert.equal(sect.length, 2, `${where}: Guide's two sections`);
    assert.equal(sect.filter((t) => t.stop === 0).length, 1, `${where}: one Tab stop in the sections' row`);
    for (const t of sect) assert.ok(t.controls && t.role === 'tabpanel' && t.by, `${where}: ${t.tab} controls its tabpanel, which it names`);
    const first = sect.find((t) => t.stop === 0).tab;
    await page.locator(`.panel-tab[data-tab="${first}"]`).focus();
    await page.keyboard.press('ArrowRight');
    await settle(page);
    const moved = await page.evaluate(() => ({ tab: document.activeElement.dataset.tab, app: fx.nav.app }));
    assert.notEqual(moved.tab, first, `${where}: the arrow moves to the other section`);
    assert.equal(moved.app, 'guide', `${where}: and never to another app's section (3.2.1)`);
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.evaluate(() => document.activeElement.dataset.tab), first, `${where}: the row wraps within the app`);

    // ---- Settings' own tabs ----
    await page.locator('#nav-tab-settings').focus();
    await page.keyboard.press('Enter');
    await settle(page, 250);
    const tabsOf = () => page.evaluate(() => [...document.querySelectorAll('#settings-tabs [role="tab"]')].filter((b) => !b.hidden).map((b) => ({
      id: b.id, stop: b.tabIndex, selected: b.getAttribute('aria-selected'), controls: b.getAttribute('aria-controls'),
      role: document.getElementById(b.getAttribute('aria-controls'))?.getAttribute('role'),
      name: b.textContent.trim() })));
    let tabs = await tabsOf();
    assert.ok(tabs.length >= 8, `${where}: Settings' tabs are drawn`);
    assert.equal(tabs.filter((b) => b.stop === 0).length, 1, `${where}: one Tab stop in Settings' row`);
    for (const b of tabs) assert.ok(b.name && b.role === 'tabpanel', `${where}: ${b.id} is named and controls a tabpanel`);
    await page.keyboard.press('Tab');
    assert.equal((await active()).id, tabs.find((b) => b.stop === 0).id, `${where}: Tab from the screen reaches the selected tab`);
    await page.keyboard.press('End');
    assert.equal((await active()).id, tabs.at(-1).id, `${where}: End goes to the last tab`);
    await page.keyboard.press('Home');
    assert.equal((await active()).id, tabs[0].id, `${where}: Home to the first`);
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowRight');
    tabs = await tabsOf();
    const sel = tabs.find((b) => b.selected === 'true');
    assert.equal((await active()).id, sel.id, `${where}: the arrows select as they go`);
    assert.equal(await page.evaluate((id) => document.getElementById(document.getElementById(id).getAttribute('aria-controls')).getAttribute('aria-labelledby'), sel.id),
      sel.id, `${where}: the Settings tabpanel is named by the tab in force`);
    assert.notEqual(await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle), 'none', `${where}: a Settings tab shows its focus`);
    if (out) await page.screenshot({ path: path.join(out, `menus-settings-tabs-${width}.png`) });
    // Escape from inside a section: focus is not dropped on the page.
    await page.keyboard.press('Escape');
    await settle(page, 150);
    assert.equal(await page.evaluate(() => fx.nav.level), 0, `${where}: Escape in Settings closes the device`);
    assert.equal((await active()).id, phone ? 'nav-grip' : 'nav-tab-settings', `${where}: focus goes back to Settings' key, not the page`);
    if (out) await page.screenshot({ path: path.join(out, `menus-escape-return-${width}.png`) });

    // ---- the status line itself ----
    await page.evaluate(() => fx.announce('Arrived: Chicago, 1835'));
    await settle(page);
    assert.equal(await status(), 'Arrived: Chicago, 1835');
    assert.deepEqual(await page.evaluate(() => { const r = document.getElementById('a11y-status'); return [r.getAttribute('role'), r.getAttribute('aria-live')]; }), ['status', 'polite']);
    await page.evaluate(() => fx.announce('Arrived: Chicago, 1835'));
    assert.equal(await status(), '', `${where}: the same words again are emptied first, so they are heard again`);
    await settle(page);
    assert.equal(await status(), 'Arrived: Chicago, 1835');

    assert.deepEqual(errors, [], `${where}: no page errors`);
    await context.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log('A11Y MENUS PASS — both widths: skip link, title and canvas per year, rail and tab rows (roles, one Tab stop, arrows, Home/End, label in name), a heading and focus in every screen, focus back on close and on a section\'s Escape, the status line');
