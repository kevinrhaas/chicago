// T-3671 (WCAG 2.1 AA, the visual criteria): the real index.html, CSS and interface modules,
// with no town. The Navigator (each app, each Settings pane), the HUD, a building card, a
// Jaunt's panel, the tour card, the hints, the arrival device and its welcome are measured in
// all four machines x light and dark:
//   1.4.3   every visible run of text against its own background, a translucent panel laid
//           over a white sky AND a black night (the worst of the two counts);
//   1.4.11  a field's edge, and a lit key's hairline, at 3:1 on what is behind them;
//   2.4.7   every control reached by Tab wears the one ring: 2 px or more, 3:1 on its panel,
//           with a halo of the panel's colour so it reads over the scene too;
//   1.4.4 / 1.4.10  at 200 % text, 1280 and 390 wide, every part reflows: nothing past the
//           screen's edge, no part scrolling both ways, no words cut short, and the text is
//           really larger (rail names, card, Jaunt panel, tour, hints, not only the screens);
//   1.4.12  the four text-spacing overrides cut no words;
//   1.3.4 / 1.4.4  no orientation lock, no maximum-scale on the page.
//   node tools/test_a11y_visual.mjs            the test
//   C4D_TEST_OUT=dir node tools/...            …and save the pictures
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const out = process.env.C4D_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });
const failures = [];
const check = (ok, what) => { if (!ok) failures.push(what); };

// ---- static: nothing locks the orientation or the page's zoom -------------------------
const indexHtml = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const meta = indexHtml.match(/<meta name="viewport"[^>]+>/)[0];
check(!/maximum-scale|user-scalable\s*=\s*(no|0)/.test(meta), `1.4.4: the viewport lets the browser zoom (${meta})`);
const jsFiles = fs.readdirSync(path.join(web, 'js'), { recursive: true }).filter((f) => f.endsWith('.js'));
const locks = jsFiles.filter((f) => /orientation\.lock\s*\(|lockOrientation\s*\(/.test(fs.readFileSync(path.join(web, 'js', f), 'utf8')));
check(!locks.length, `1.3.4: no script locks the orientation (${locks})`);
for (const f of fs.readdirSync(web).filter((n) => /\.(webmanifest|json)$/.test(n))) {
  check(!/"orientation"\s*:/.test(fs.readFileSync(path.join(web, f), 'utf8')), `1.3.4: ${f} sets no orientation`);
}
const { TEXT_SCALES } = await import(path.join(web, 'js/settings-app.js'));
check(Math.max(...TEXT_SCALES) === 2 && TEXT_SCALES[0] === 1, '1.4.4: Text size runs from 100 % to 200 %');
check(/<option value="2">200 %<\/option>/.test(indexHtml), '1.4.4: Settings offers 200 %');

// ---- the fixture -----------------------------------------------------------------------
const MEASURE = String.raw`
const cv = document.createElement('canvas'); cv.width = cv.height = 1;
const cx = cv.getContext('2d', { willReadFrequently: true });
const rgba = (c) => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
  const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
const over = (t, u) => [0, 1, 2].map((i) => t[i] * t[3] + u[i] * (1 - t[3])).concat(1);
const lum = ([r, g, b]) => [r, g, b].map((v) => v / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  .reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)]; return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const SCENES = [[255, 255, 255, 1], [0, 0, 0, 1]];
const name = (el) => { let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id;
  else if (typeof el.className === 'string' && el.className.trim()) s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
  const p = el.parentElement; const ps = !p ? '' : p.id ? '#' + p.id : typeof p.className === 'string' && p.className.trim() ? '.' + p.className.trim().split(/\s+/)[0] : p.tagName.toLowerCase();
  return ps + ' > ' + s; };
/** The colours an element is seen against, from itself up: each layer a list of choices (a
 * gradient's stops), down to the first opaque one, or to the scene. */
function backdrops(el, self = true) {
  const layers = []; let alpha = 1, opaque = false;
  for (let n = self ? el : el.parentElement; n && n.nodeType === 1; n = n.parentElement) {
    const s = getComputedStyle(n); alpha *= Number(s.opacity);
    const bg = rgba(s.backgroundColor);
    const grad = /gradient/.test(s.backgroundImage) ? (s.backgroundImage.match(/(rgba?\([^)]*\)|color\([^)]*\)|#[0-9a-f]{3,8}\b)/gi) || []).map(rgba) : [];
    if (grad.length) { layers.push(grad.map((g) => over(g, bg).slice(0, 3).concat(Math.max(g[3], bg[3])))); if (grad.every((g) => g[3] >= 0.999) || bg[3] >= 0.999) { opaque = true; break; } continue; }
    if (bg[3] > 0) { layers.push([bg]); if (bg[3] >= 0.999) { opaque = true; break; } }
  }
  let combos = [[]];
  for (const l of layers) { const next = []; for (const c of combos) for (const v of l) if (next.length < 64) next.push([...c, v]); combos = next; }
  const out = [];
  for (const scene of opaque ? [SCENES[0]] : SCENES) for (const combo of combos) {
    let c = scene; for (const l of combo.slice().reverse()) c = over(l, c); out.push(c);
  }
  return { colours: out, alpha };
}
const shown = (el) => { if (!el.getClientRects().length) return false; const r = el.getBoundingClientRect();
  return r.width >= 1 && r.height >= 1 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth
    && getComputedStyle(el).visibility === 'visible'; };
window.__text = () => {
  const rows = [];
  for (const el of document.body.querySelectorAll('*')) {
    if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
    if (!shown(el) || el.closest('[hidden], .visually-hidden, canvas, svg, option, :disabled, [aria-disabled="true"]')) continue;
    const cs = getComputedStyle(el), { colours, alpha } = backdrops(el);
    if (alpha < 0.05) continue;
    const fg = rgba(cs.color), size = parseFloat(cs.fontSize) * (el.currentCSSZoom || 1);
    const need = size >= 24 || (Number(cs.fontWeight) >= 700 && size >= 18.66) ? 3 : 4.5;
    const worst = Math.min(...colours.map((bg) => ratio(over([fg[0], fg[1], fg[2], fg[3] * alpha], bg), bg)));
    if (worst < need) rows.push(name(el) + ' "' + el.textContent.trim().slice(0, 30) + '" ' + worst.toFixed(2) + '/' + need);
  }
  return rows;
};
window.__parts = () => {
  const rows = [];
  // 1.4.11: a field is found by its edge (or its own fill); a lit key by its hairline.
  for (const el of document.body.querySelectorAll('input:not([type=range]):not([type=checkbox]):not([type=radio]):not([type=hidden]), select, textarea')) {
    if (!shown(el) || el.closest('[hidden]') || Number(getComputedStyle(el).opacity) < 0.05) continue;
    const s = getComputedStyle(el), { colours } = backdrops(el, false), own = rgba(s.backgroundColor), edge = rgba(s.borderTopColor);
    const w = parseFloat(s.borderTopWidth) + parseFloat(s.borderBottomWidth);
    const k = Math.max(w > 0 ? Math.min(...colours.map((bg) => ratio(over(edge, over(own, bg)), bg))) : 0,
      Math.min(...colours.map((bg) => ratio(over(own, bg), bg))));
    if (k < 3) rows.push('field ' + name(el) + ' edge ' + k.toFixed(2));
  }
  for (const el of document.body.querySelectorAll('[aria-pressed="true"], [aria-checked="true"][role="radio"], .seg-btn.is-on')) {
    if (!shown(el) || el.closest('[hidden]') || el.matches('.skin-tile, input')) continue;
    const s = getComputedStyle(el), { colours } = backdrops(el, false);
    const marks = [s.borderTopWidth !== '0px' && s.borderTopStyle !== 'none' ? s.borderTopColor : null,
      (/inset 0px 0px 0px 1px|0px 0px 0px 1px .*inset/.test(s.boxShadow) ? (s.boxShadow.match(/(rgba?\([^)]*\)|color\([^)]*\))/) || [])[0] : null),
      s.backgroundColor].filter(Boolean).map(rgba);
    const k = Math.max(...marks.map((m) => Math.min(...colours.map((bg) => ratio(over(m, bg), bg)))));
    if (k < 3) rows.push('lit ' + name(el) + ' ' + k.toFixed(2));
  }
  return rows;
};
window.__ring = () => {
  let el = document.activeElement; if (!el || el === document.body) return null;
  if (el.matches('.nav-tile-open')) el = el.closest('.nav-tile');   // the tile is the key (navigator.css)
  const s = getComputedStyle(el), { colours } = backdrops(el, false);
  const ring = rgba(s.outlineColor), halo = (s.boxShadow.match(/(rgba?\([^)]*\)|color\([^)]*\))/) || [])[0];
  return { el: name(el), style: s.outlineStyle, width: parseFloat(s.outlineWidth),
    panel: Math.min(...colours.map((bg) => ratio(over(ring, bg), bg))), halo: halo ? ratio(ring, over(rgba(halo), colours[0])) : 0,
    haloSpread: /0px 0px 0px (\d+)px/.exec(s.boxShadow)?.[1] ?? '0' };
};
/** 1.4.10: parts past the screen, parts that scroll both ways, words cut short. */
window.__reflow = (root = document.body) => {
  const rows = [], vw = document.documentElement.clientWidth;
  if (document.scrollingElement.scrollWidth > vw + 1) rows.push('the page scrolls sideways ' + document.scrollingElement.scrollWidth);
  for (const el of root.querySelectorAll('*')) {
    // Device furniture, not content: the telemetry strip, the arrival's screen code, and the closed
    // device's brand label (its open head shows it whole, below).
    if (!shown(el) || el.closest('[hidden], .visually-hidden, [aria-hidden="true"], canvas, svg, .hud-instrument .overview-map, .nav-telemetry, .gate-code')) continue;
    if (el.matches('.nav-label, .nav-code') && (el.closest('.navigator[data-detent="dock"], .navigator[data-detent="rail"]') || !document.documentElement.dataset.textScale)) continue;
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    if (s.position === 'absolute' && (s.clip.startsWith('rect') || s.width === '1px')) continue;   // a heading kept for assistive tech (visually hidden)
    if ((r.right > vw + 1 || r.left < -1) && el.textContent.trim() && !el.closest('[style*="translate"]')) {
      // past the edge, unless a scroller holds it (that scroller is reported below)
      let held = false; for (let p = el.parentElement; p; p = p.parentElement) { const ps = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(ps.overflowX)) { const pr = p.getBoundingClientRect(); if (pr.right <= vw + 1 && pr.left >= -1) held = true; break; } }
      if (!held) rows.push('past the edge: ' + name(el));
    }
    const x = /(auto|scroll)/.test(s.overflowX) && el.scrollWidth > el.clientWidth + 1, y = /(auto|scroll)/.test(s.overflowY) && el.scrollHeight > el.clientHeight + 1;
    if (x && y) rows.push('scrolls both ways: ' + name(el));
    if (x && !el.matches('.insp-swipe, .pop-pic-strip, .nav-rail, .pills, .jaunt-categories')) rows.push('scrolls sideways: ' + name(el));
    if (el.textContent.trim() && [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) {
      const clips = s.textOverflow === 'ellipsis' || (/(hidden|clip)/.test(s.overflowX + s.overflowY));
      if (clips && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 2)) rows.push('cut: ' + name(el) + ' "' + el.textContent.trim().slice(0, 24) + '"');
    }
  }
  return rows;
};
`;
const FIXTURE = String.raw`
const q = new URLSearchParams(location.search);
const { createNavigator } = await import('/js/navigator.js');
const { APPS } = await import('/js/apps/index.js');
const { applyTextScale } = await import('/js/settings-app.js');
const gate = document.getElementById('gate'); gate.hidden = true;
document.getElementById('hud').hidden = false;
applyTextScale(document.documentElement, q.get('scale') || 1);
window.nav = createNavigator({ root: document.getElementById('navigator'), scene: { id: '1835', target_date: '1835-07-01' }, apps: APPS,
  context: () => ({ actions: {}, scene: { id: '1835' } }) });
nav.open?.(2);
for (const id of ['btn-inspect', 'roam-tip']) { const e = document.getElementById(id); e.hidden = false; if (!e.textContent.trim()) e.textContent = 'Drag to look around. Tap a building to read about it.'; }
const hint = document.getElementById('hint'); hint.textContent = 'Click to look around · WASD to walk'; hint.classList.add('on');
document.getElementById('travel-banner').hidden = false;
const nh = document.getElementById('nav-hint'); nh.hidden = false; nh.textContent = 'Saved to your notebook';
const { createPopup } = await import('/js/popup.js');
window.popup = createPopup(document.getElementById('popup'));
popup.show({ id: 'fixture-house', sidecar: { id: 'fixture-house', name: 'Fixture house', kind: 'dwelling',
  change_note: 'A one-room frame house on the north side of the river, recorded on the 1835 assessment roll.',
  attributes: { use: { value: 'dwelling', confidence: 'attested', sources: [] }, storeys: { value: 2, confidence: 'inferred', sources: [] },
    roof: { value: 'gable', confidence: 'reconstructed', sources: [] } }, citations: [], placement: { position_confidence: 'inferred' } } });
document.getElementById('tour').hidden = false;
document.getElementById('tour-task').textContent = 'Walk to the corner of Lake and Clark.';
document.getElementById('tour-bubble').textContent = 'Use the keys or the stick to walk.';
document.getElementById('tour-next').hidden = false;
const { createJauntPanel } = await import('/js/jaunt-panel.js');
const jp = createJauntPanel({ destinations: { byId: () => ({ label: 'Lake and Clark' }) }, actions: new Proxy({}, { get: () => () => {} }) });
const stop = (id) => ({ id, destination: { kind: 'structure', id }, text: 'The settlement clusters along the south bank of the river, where the boats tie up and goods come ashore.',
  evidence: [], links: [{ label: 'Read the card', kind: 'structure', id }], choices: [] });
jp.render({ jaunt: { id: 'fx', title: 'Along the river', scene: '1835', stops: [stop('a'), stop('b'), stop('c')], evidence: [], allowed_modes: ['walk'], places: {} },
  phase: 'atStop', session: 1, stopIndex: 1, visited: [{ id: 'a', committed: true }, { id: 'b' }], mode: 'walk', context: { lines: [], passed: [] } });
jp.collapse(false);
const show = q.get('show');
if (show) {
  const keep = { nav: [], popup: ['popup'], jaunt: ['jaunt-panel'], tour: ['tour'], hint: ['nav-hint', 'roam-tip'] }[show] || [];
  for (const id of ['popup', 'tour', 'jaunt-panel', 'nav-hint', 'roam-tip']) if (!keep.includes(id)) document.getElementById(id).hidden = true;
  if (show !== 'nav') nav.dock?.();
  if (show === 'popup') document.documentElement.classList.add('card-open');
}
if (q.get('view') === 'gate' || q.get('view') === 'welcome') {
  document.getElementById('hud').hidden = true;
  for (const id of ['popup', 'tour', 'jaunt-panel', 'nav-hint']) document.getElementById(id).hidden = true;
  gate.hidden = false;
  if (q.get('view') === 'welcome') { gate.dataset.state = 'welcome'; document.getElementById('welcome').hidden = false; }
}
${MEASURE}
window.fixtureReady = true;
`;
const page0 = indexHtml.replace(/<script type="module" src="\.\/js\/(main|recall)\.js"><\/script>/g, '')
  .replace('</body>', '<script type="module" src="/fixture.js"></script></body>');
assert.notEqual(page0, indexHtml, 'the page\'s boot is replaced by the fixture');
const TYPES = { js: 'text/javascript', css: 'text/css', html: 'text/html', woff2: 'font/woff2', json: 'application/json', svg: 'image/svg+xml', png: 'image/png' };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(page0); return; }
  if (url.pathname === '/fixture.js') { res.writeHead(200, { 'Content-Type': 'text/javascript' }); res.end(FIXTURE); return; }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': TYPES[path.extname(file).slice(1)] || 'application/octet-stream' }); res.end(err ? '' : bytes); });
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
const MACHINES = ['control-room', 'brass', 'worlds-fair', 'deep-space'];
const contexts = {};
async function open(width, query = '', height = width < 600 ? 780 : 800) {
  const phone = width < 600;
  contexts[`${width}x${height}`] ??= await browser.newContext({ viewport: { width, height }, isMobile: phone, hasTouch: phone,
    deviceScaleFactor: 1, reducedMotion: 'reduce' });
  const page = await contexts[`${width}x${height}`].newPage(), errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`${origin}/?${query}`);
  await page.waitForFunction(() => window.fixtureReady, null, { timeout: 30000 });
  page.errors = errors;
  return page;
}
/** Wait out a screen's change (the device warms a screen in; a tone may fade). */
const settle = (page) => page.evaluate(() => Promise.race([Promise.all(document.getAnimations().map((a) => a.finished.catch(() => null))),
  new Promise((r) => setTimeout(r, 1500))]).then(() => new Promise((r) => setTimeout(r, 60))));
const tone = (page, skin, theme) => page.evaluate(([s, t]) => { document.documentElement.dataset.skin = s; document.documentElement.dataset.theme = t; }, [skin, theme]);
let measured = 0;
try {
  // ---- 1.4.3 / 1.4.11: every machine, both tones -------------------------------------
  for (const view of ['hud', 'gate', 'welcome']) {
    const page = await open(1280, `view=${view}`);
    const apps = view === 'hud' ? await page.evaluate(() => nav.apps) : [null];
    check(view !== 'hud' || apps.length >= 6, `the fixture's Navigator has its apps (${apps})`);
    for (const skin of MACHINES) for (const theme of ['dark', 'light']) {
      await tone(page, skin, theme);
      const bad = new Set();
      for (const app of apps) {
        if (app) await page.evaluate((a) => nav.select(a), app);
        const panes = app === 'settings' ? await page.evaluate(() => [...document.querySelectorAll('.set-tab')].map((b, i) => i)) : [null];
        for (const pane of panes) {
          if (pane !== null) await page.evaluate((i) => document.querySelectorAll('.set-tab')[i].click(), pane);
          await settle(page);
          for (const tab of view === 'hud' ? ['evidence', 'record'] : [null]) {
            if (tab) { await page.evaluate((t) => document.querySelector(`[data-pop-tab="${t}"]`)?.click(), tab); await settle(page); }
            const rows = await page.evaluate(() => [...__text(), ...__parts()]);
            measured++;
            for (const r of rows) bad.add(r);
          }
        }
      }
      check(!bad.size, `contrast, ${view}, ${skin}/${theme}:\n    ${[...bad].join('\n    ')}`);
    }
    check(!page.errors.length, `no page errors (${view}): ${page.errors}`);
    await page.close();
  }

  // ---- 2.4.7: the one focus ring, by Tab, on every machine and tone ------------------
  {
    const page = await open(1280, 'show=nav');
    // Home (the rail, its tiles and folds), Confidence (presets, check boxes) and Guide (the
    // notebook's fields, whose own rule hid the outline): every Tab stop in each.
    for (const app of ['home', 'confidence', 'guide']) {
      await page.evaluate((a) => nav.select(a), app); await settle(page);
      await page.evaluate(() => { for (const d of document.querySelectorAll('.navigator details')) d.open = true; });
      for (const skin of MACHINES) for (const theme of ['dark', 'light']) {
        await tone(page, skin, theme);
        await page.evaluate(() => { document.activeElement?.blur?.(); document.querySelector('.nav-app.is-on').focus(); });
        const seen = new Set(), bad = [];
        for (let i = 0; i < 45; i++) {
          await page.keyboard.press('Tab');
          const r = await page.evaluate(() => __ring());
          if (!r || seen.has(r.el)) continue;
          seen.add(r.el);
          if (r.style === 'none' || r.width < 2 || r.panel < 3 || r.halo < 3 || Number(r.haloSpread) < 4) bad.push(JSON.stringify(r));
        }
        check(seen.size >= 8, `Tab reaches eight controls or more (${seen.size}), ${app}, ${skin}/${theme}`);
        check(!bad.length, `focus ring, ${app}, ${skin}/${theme}:\n    ${bad.join('\n    ')}`);
      }
    }
    // The picture: a notebook field, whose own rule said outline: none.
    if (out) {
      await tone(page, 'control-room', 'dark');
      await page.evaluate(() => document.querySelector('.navigator form input:not([type=checkbox]), .navigator textarea')?.focus());
      await settle(page);
      const box = await page.evaluate(() => { const r = document.activeElement.getBoundingClientRect(); return { y: Math.max(0, Math.round(r.top - 160)) }; });
      await page.screenshot({ path: path.join(out, 'visual-focus-ring-1280-after.png'), clip: { x: 0, y: Math.min(box.y, 400), width: 640, height: 400 } });
    }
    await page.close();
    const phone = await open(390, 'show=nav');
    await phone.evaluate(() => document.getElementById('nav-tab-jaunts').focus());
    await phone.keyboard.press('Shift+Tab'); await phone.keyboard.press('Tab');
    const r = await phone.evaluate(() => __ring());
    check(r && r.style !== 'none' && r.width >= 2 && r.panel >= 3 && r.halo >= 3, `focus ring on the phone's tab bar ${JSON.stringify(r)}`);
    if (out) { await settle(phone); await phone.screenshot({ path: path.join(out, 'visual-focus-ring-390-after.png') }); }
    await phone.close();
  }

  // ---- 1.4.4 / 1.4.10: 200 % text, 1280 and 390 ----------------------------------------
  const sizes = {};
  for (const width of [1280, 390]) {
    for (const show of ['nav', 'popup', 'jaunt', 'tour', 'hint']) {
      for (const scale of [1, 2]) {
        const page = await open(width, `show=${show}&scale=${scale}`);
        if (show === 'nav') {
          for (const app of await page.evaluate(() => nav.apps)) {
            await page.evaluate((a) => nav.select(a), app); await settle(page);
            if (scale === 2) { const rows = await page.evaluate(() => __reflow()); check(!rows.length, `reflow at 200 %, ${width}, Navigator ${app}:\n    ${rows.join('\n    ')}`); }
          }
          await page.evaluate(() => nav.select('home'));
        } else if (scale === 2) {
          const rows = await page.evaluate(() => __reflow());
          check(!rows.length, `reflow at 200 %, ${width}, ${show}:\n    ${rows.join('\n    ')}`);
        }
        // How big the words really are on the screen (a zoomed part reports its own px).
        const px = await page.evaluate(() => Object.fromEntries([
          ['rail', '#nav-tab-home .nav-app-label'], ['head', '.nav-date'], ['screen', '#nav-home .panel-title, #nav-home strong, #nav-home p'],
          ['card', '#popup .pop-lead, #popup p'], ['jaunt', '#jaunt-panel .jaunt-body p'], ['tour', '#tour-bubble'], ['hint', '#nav-hint'], ['tip', '#roam-tip'],
          ['chip', '#year-badge .badge-year'], ['quick', '#btn-inspect .chip-label'],
        ].map(([k, sel]) => { const el = [...document.querySelectorAll(sel)].find((e) => e.getClientRects().length && getComputedStyle(e).visibility === 'visible');
          return [k, el ? parseFloat(getComputedStyle(el).fontSize) * (el.currentCSSZoom || 1) : null]; })));
        for (const [k, v] of Object.entries(px)) if (v) ((sizes[`${width}:${k}`] ??= {})[scale] ??= v);
        if (out && width === 390 && scale === 2 && ['nav', 'popup', 'jaunt'].includes(show)) {
          await settle(page); await page.screenshot({ path: path.join(out, `visual-text-200-390-${show}-after.png`) });
        }
        check(!page.errors.length, `no page errors (${show}, ${width}, ${scale}): ${page.errors}`);
        await page.close();
      }
    }
  }
  // The arrival device and its welcome, magnified whole, scroll in their overlay.
  for (const view of ['gate', 'welcome']) {
    const page = await open(390, `view=${view}&scale=2`);
    const rows = await page.evaluate(() => __reflow());
    check(!rows.length, `reflow at 200 %, 390, ${view}:\n    ${rows.join('\n    ')}`);
    await page.close();
  }
  // 1.4.10 at 100 %: 320 px wide (1280 at 400 %), and 640 x 400 (1280 x 800 at the browser's 200 %).
  for (const [w, h] of [[320, 640], [640, 400]]) for (const show of ['nav', 'popup', 'jaunt', 'tour']) {
    const page = await open(w, `show=${show}`, h);
    await settle(page);
    const rows = await page.evaluate(() => __reflow());
    check(!rows.length, `reflow at ${w} x ${h}, ${show}:\n    ${rows.join('\n    ')}`);
    await page.close();
  }
  const grew = Object.entries(sizes).filter(([, v]) => v[1] && v[2]);
  for (const [k, v] of grew) check(v[2] / v[1] > 1.9, `1.4.4: ${k} text is ${v[1]}px at 100 % and ${v[2]}px at 200 %`);
  for (const k of ['1280:rail', '1280:screen', '1280:card', '1280:jaunt', '1280:tour', '1280:hint', '1280:chip', '390:rail', '390:card', '390:jaunt', '390:tour'])
    check(grew.some(([g]) => g === k), `1.4.4: ${k} measured at both sizes`);

  // ---- 1.4.12: the text-spacing overrides cut no words -----------------------------------
  const SPACING = '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}';
  for (const width of [1280, 390]) for (const show of ['nav', 'popup', 'jaunt', 'tour', 'gate', 'welcome']) {
    const page = await open(width, ['gate', 'welcome'].includes(show) ? `view=${show}` : `show=${show}`);
    await page.addStyleTag({ content: SPACING });
    await settle(page);
    const rows = (await page.evaluate(() => __reflow())).filter((r) => r.startsWith('cut') || r.startsWith('past'));
    check(!rows.length, `1.4.12 text spacing, ${width}, ${show}:\n    ${rows.join('\n    ')}`);
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}
if (failures.length) {
  console.error(`A11Y VISUAL FAIL — ${failures.length}:\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log(`A11Y VISUAL PASS — ${measured} screens measured in 4 machines x 2 tones (text 4.5:1 / 3:1 over a white and a black scene, fields and lit keys 3:1); `
  + 'one 2 px focus ring with a panel halo on every Tab stop; 200 % text reflows at 1280 and 390 and really doubles; text spacing cuts nothing; no orientation or zoom lock');
