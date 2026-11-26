#!/usr/bin/env node
// T-3753 — the jaunt panel's Stops list and its loading rings, in a real browser, with the real
// panel (jaunt-panel.js), reducer (jaunts.js), CSS and icons and no town: 390x780 phone and
// 1280x800 desktop.
//
//  - Stops opens the route's stops in place of the story: numbered, the one you are at marked
//    (aria-current), each row a 44 px target; Esc and × close it and give focus back to Stops.
//  - A tap on a stop ahead or behind goes straight there (JUMP), the list closes, and arriving
//    at a scene still loading spins the Stops key; Next stop spins after a walk in; never past
//    the cap; Listen spins while its voice is still arriving.
//  - A jaunt whose choice decides the way on lists the stops up to it and says so.
//  - The menu's Start spins while its jaunt loads.
//
// Pictures: C4D_TEST_OUT=<dir> saves stops-<width>.png and loading-<width>.png there.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');

const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const meta = index.match(/<meta name="viewport"[^>]+>/)[0];
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)[0];
const out = process.env.C4D_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en" data-skin="control-room"><head><meta charset="utf-8">${meta}${imports}
      <link rel="stylesheet" href="/css/walk.css"></head>
      <body style="background:#33413c"><section id="popup" hidden></section><div id="menu-host" style="position:fixed;right:8px;bottom:8px;width:340px"></div></body></html>`);
    return;
  }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'application/octet-stream' });
    res.end(err ? '' : bytes);
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
let failed = false;
try {
  for (const width of [390, 1280]) {
    const phone = width === 390;
    const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 }, isMobile: phone, hasTouch: phone, deviceScaleFactor: out ? 2 : 1 });
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(origin);
    await page.evaluate(async () => {
      const { createJauntPanel } = await import('/js/jaunt-panel.js');
      const { reduce, emptyState, routeStops } = await import('/js/jaunts.js');
      const names = ['The Glessner House', 'The Kimball House', 'The Coleman House', 'The Keith House', 'The Pullman House', 'The Field House'];
      const stops = names.map((n, i) => ({ id: `s${i}`, destination: { kind: 'structure', id: `b${i}` }, text: `${n}: a stop of the walk.`, evidence: [], links: [], next: i < names.length - 1 ? `s${i + 1}` : '$end' }));
      const jaunt = { id: 'qa-line', content_version: 1, title: 'Prairie Avenue Walk', scene: '1904', premise: 'Six houses.', default_mode: 'walk', allowed_modes: ['walk', 'fly'],
        places: Object.fromEntries(names.map((n, i) => [`b${i}`, n])), opening: { text: 'JAUNT: PRAIRIE AVENUE WALK. Six houses.' }, stops,
        endings: [{ id: 'end', default: true, completion_eligible: true, text: 'Done.' }], evidence: [], keepsake: { title: 'A note', text: 'Six.' } };
      const branching = { ...jaunt, id: 'qa-branch', title: 'Errands', stops: [
        { ...stops[0], next: undefined, choices: [{ id: 'left', label: 'Left', next: 's1', consequence: 'Left.' }, { id: 'right', label: 'Right', next: 's2', consequence: 'Right.' }] },
        { ...stops[1], next: 's3' }, { ...stops[2], next: 's3' }, { ...stops[3], next: '$end' }] };
      let state;
      const calls = [];
      const panelRef = {};
      const set = (s) => { state = s; panelRef.panel.render(s); };
      const act = (name) => (...args) => {
        calls.push([name, ...args]);
        if (name === 'jump') set(reduce(state, { type: 'JUMP', stop: args[0] }));
        if (name === 'next') set(reduce(state, { type: 'NEXT' }));
      };
      const actions = Object.fromEntries(['next', 'prev', 'jump', 'end', 'menu', 'choose', 'revise', 'retry', 'detail', 'returnFromDetail', 'setMode', 'straight', 'resumeRide', 'dismissContext', 'replay', 'kindle', 'skip', 'finish', 'closeOverlay'].map(n => [n, act(n)]));
      const panel = panelRef.panel = createJauntPanel({ destinations: { byId: () => null }, actions });
      window.__rig = { panel, reduce, emptyState, routeStops, jaunt, branching, calls, set, get state() { return state; },
        arrive() { set(reduce(state, { type: 'ARRIVE', session: state.session, leg: state.leg })); } };
    });
    const rig = (fn, arg) => page.evaluate(fn, arg);
    await rig(() => { const r = window.__rig; r.set(r.reduce(r.emptyState(), { type: 'START', jaunt: r.jaunt, session: 1, mode: 'walk' })); r.arrive(); r.set(r.reduce(r.state, { type: 'NEXT' })); r.arrive(); });
    // The Stops key: a named, 44 px target beside Back.
    let seen = await rig(() => { const b = document.querySelector('#jaunt-panel [data-action="stops"]'), r = b.getBoundingClientRect();
      return { label: b.getAttribute('aria-label'), expanded: b.getAttribute('aria-expanded'), w: r.width, h: r.height,
        order: [...document.querySelectorAll('#jaunt-panel .jaunt-controls > button[data-action]')].filter(x => !x.hidden).map(x => x.dataset.action) }; });
    assert.equal(seen.label, 'All stops'); assert.equal(seen.expanded, 'false');
    assert(seen.w >= 44 && seen.h >= 44, `Stops is a 44 px target ${JSON.stringify(seen)}`);
    assert.deepEqual(seen.order.slice(-5), ['prev', 'stops', 'menu', 'end', 'next']);
    await page.locator('#jaunt-panel [data-action="stops"]').click();
    seen = await rig(() => { const p = document.getElementById('jaunt-panel');
      return { body: getComputedStyle(p.querySelector('.jaunt-body')).display, open: !p.querySelector('#jaunt-stops').hidden,
        rows: [...p.querySelectorAll('.jaunt-stop-row')].map(b => `${b.querySelector('.jaunt-stop-n').textContent}:${b.querySelector('.jaunt-stop-name').textContent}:${b.className.match(/jaunt-stop-(here|seen|ahead)/)[1]}`),
        focus: document.activeElement?.dataset.stop, current: p.querySelector('[aria-current="step"]')?.dataset.stop,
        small: [...p.querySelectorAll('.jaunt-stop-row')].filter(b => b.getBoundingClientRect().height < 44).length,
        fits: p.querySelector('#jaunt-stops').scrollWidth <= p.querySelector('#jaunt-stops').clientWidth }; });
    assert.equal(seen.body, 'none', 'the list stands in place of the story'); assert(seen.open);
    assert.deepEqual(seen.rows, ['1:The Glessner House:seen', '2:The Kimball House:here', '3:The Coleman House:ahead', '4:The Keith House:ahead', '5:The Pullman House:ahead', '6:The Field House:ahead']);
    assert.equal(seen.focus, 's1', 'focus goes to the stop you are at'); assert.equal(seen.current, 's1');
    assert.equal(seen.small, 0, 'every row is a 44 px target'); assert(seen.fits, 'no row runs off the panel');
    if (out) await page.screenshot({ path: path.join(out, `stops-${width}.png`) });
    // Arrow keys walk the rows, Esc closes and gives focus back to Stops.
    await page.keyboard.press('ArrowDown');
    assert.equal(await rig(() => document.activeElement?.dataset.stop), 's2');
    await page.keyboard.press('Escape');
    seen = await rig(() => ({ open: !document.getElementById('jaunt-stops').hidden, focus: document.activeElement?.dataset.action }));
    assert.deepEqual(seen, { open: false, focus: 'stops' });
    // A tap ahead goes straight there; arriving where the scene is still coming spins Stops.
    await page.locator('#jaunt-panel [data-action="stops"]').click();
    await page.locator('#jaunt-panel .jaunt-stop-row[data-stop="s4"]').click();
    seen = await rig(() => { const r = window.__rig; return { open: !document.getElementById('jaunt-stops').hidden, jump: r.calls.at(-1), phase: r.state.phase, instant: r.state.instant, stop: r.state.visited[r.state.stopIndex].id }; });
    assert.deepEqual(seen, { open: false, jump: ['jump', 's4'], phase: 'travelling', instant: true, stop: 's4' });
    await rig(() => { const r = window.__rig; r.arrive(); r.panel.loading({ scene: true }); });
    seen = await rig(() => ({ spin: [...document.querySelectorAll('#jaunt-panel .jaunt-loading')].map(b => b.dataset.action),
      busy: document.getElementById('jaunt-panel').hasAttribute('aria-busy'),
      ring: getComputedStyle(document.querySelector('#jaunt-panel [data-action="stops"]'), '::after').animationName,
      icon: getComputedStyle(document.querySelector('#jaunt-panel [data-action="stops"] .menu-icon')).visibility }));
    assert.deepEqual(seen, { spin: ['stops'], busy: true, ring: 'jaunt-spin', icon: 'hidden' });
    if (out) await page.screenshot({ path: path.join(out, `loading-${width}.png`) });
    await rig(() => window.__rig.panel.loading({ scene: false }));
    assert.deepEqual(await rig(() => [...document.querySelectorAll('#jaunt-panel .jaunt-loading')].length), 0, 'the ring stops once the scene is in');
    // Back to the first stop from the list (behind), then a walk in to the next: Next stop spins.
    await page.locator('#jaunt-panel [data-action="stops"]').click();
    await page.locator('#jaunt-panel .jaunt-stop-row[data-stop="s0"]').click();
    await rig(() => { const r = window.__rig; r.arrive(); });
    assert.equal(await rig(() => window.__rig.state.stopIndex), 0);
    await page.locator('#jaunt-panel [data-action="next"]').click();
    await rig(() => { const r = window.__rig; r.arrive(); r.panel.loading({ scene: true }); });
    seen = await rig(() => [...document.querySelectorAll('#jaunt-panel .jaunt-loading')].map(b => b.dataset.action));
    assert.deepEqual(seen, ['next', 'bar-next']);
    seen = await rig(() => getComputedStyle(document.querySelector('#jaunt-panel [data-action="next"]'), '::before').animationName);
    assert.equal(seen, 'jaunt-spin');
    // The cap: a scene that never comes stops spinning its key after 20 s.
    await rig(() => { const r = window.__rig, real = performance.now.bind(performance); performance.now = () => real() + 21000; r.panel.loading({ scene: true }); performance.now = real; });
    assert.equal(await rig(() => document.querySelectorAll('#jaunt-panel .jaunt-loading').length), 0, 'never past the cap');
    // Branching: the list ends at the choice and says so.
    await rig(() => { const r = window.__rig; r.set(r.reduce(r.emptyState(), { type: 'START', jaunt: r.branching, session: 2, mode: 'walk' })); r.arrive(); });
    await page.locator('#jaunt-panel [data-action="stops"]').click();
    seen = await rig(() => ({ rows: [...document.querySelectorAll('.jaunt-stop-row')].map(b => b.dataset.stop), note: document.querySelector('.jaunt-stops-note')?.textContent }));
    assert.deepEqual(seen, { rows: ['s0'], note: 'Your choice at this stop decides the way on.' });
    await page.locator('#jaunt-panel .jaunt-stops-close').click();
    assert.equal(await rig(() => document.activeElement?.dataset.action), 'stops', '× gives focus back to Stops');
    // The menu's Start spins while the jaunt loads.
    seen = await rig(async () => {
      const { createJauntMenu } = await import('/js/jaunt-menu.js');
      let done;
      const root = document.getElementById('menu-host');
      const menu = createJauntMenu({ root, estimate: () => null, onStart: () => new Promise(r => { done = r; }), onPreview: () => {} });
      menu.show([{ id: 'qa-line', title: 'Prairie Avenue Walk', premise: 'Six houses.', category: 'Walk', default_mode: 'walk', allowed_modes: ['walk'], stop_count: 6, scene: '1904', availability: 'available' }], [], null, false);
      const start = root.querySelector('[data-action="start"]');
      if (!start) return { start: false };
      start.click();
      const spinning = start.classList.contains('jaunt-loading') && start.getAttribute('aria-busy') === 'true' && start.disabled;
      const ring = getComputedStyle(start, '::after').animationName;
      done(true); await new Promise(r => setTimeout(r, 0));
      return { start: true, spinning, ring, after: start.classList.contains('jaunt-loading') || start.disabled };
    });
    assert.deepEqual(seen, { start: true, spinning: true, ring: 'jaunt-spin', after: false });
    assert.deepEqual(errors, [], 'zero page errors');
    console.log(`PASS ${width}: Stops list, jump back and ahead, loading rings on Stops / Next / Start, cap, branching note`);
    await context.close();
  }
} catch (error) { failed = true; console.error(error); }
finally { await browser.close(); server.close(); }
if (failed) process.exit(1);
console.log('JAUNT STOPS PASS — T-3753');
