#!/usr/bin/env node
// T-2617 (NAV-201): the Navigator device, its Home app, and the two small modules it
// reads — target.js (RIGHT IN FRONT OF YOU) and where.js (YOU ARE AT).
//
// No browser: the device runs over a hand-made DOM just large enough for it, the
// probe over a fake pick and pose, and the 1904 street answer over the real street
// grid, data/street_grid/1904.json, at the scene's own spawn.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTarget } from '../renderers/web/js/target.js';
import { createWhere, polygonDistance, facingWords, clockWords, screenDate } from '../renderers/web/js/where.js';
import { createNavigator, snapLevel, tapLevel, detentHeights, moveWords, DOCK_PX } from '../renderers/web/js/navigator.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const json = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));

// ---- target.js ----------------------------------------------------------------
{
  let hit = { id: 'glessner_house', record: { id: 'glessner_house' }, distance: 18 };
  let pose = { e: 0, n: 0, bearingDeg: 0, pitchDeg: 0 };
  let looks = 0;
  const t = createTarget({ pick: () => { looks++; return hit; }, pose: () => pose });
  t.tick(0);
  assert.equal(looks, 0, 'no listener, no look');
  const heard = [];
  const off = t.on((next, prev) => heard.push([next?.id ?? null, prev?.id ?? null]), { within: 40 });
  const wide = [];
  const offWide = t.on((next) => wide.push(next?.id ?? null), { within: 100 });
  t.tick(1000);
  assert.deepEqual(heard, [['glessner_house', null]], 'the first look is heard');
  t.tick(1100);
  assert.equal(looks, 1, 'at most one look per 500 ms');
  t.tick(2000);
  assert.equal(looks, 1, 'a still eye is not looked through again');
  pose = { ...pose, bearingDeg: 2 };
  t.tick(3000);
  assert.equal(looks, 1, 'a turn under 3 degrees is still');
  pose = { ...pose, bearingDeg: 5 };
  hit = { id: 'keith_house', record: {}, distance: 39.9 };
  t.tick(4000);
  assert.deepEqual(heard.at(-1), ['keith_house', 'glessner_house'], 'a turn onto another building is heard');
  pose = { ...pose, e: 1 };
  hit = { id: 'far_house', record: {}, distance: 40.1 };
  t.tick(5000);
  assert.deepEqual(heard.at(-1), [null, 'keith_house'], 'past 40 m is nothing in front of you');
  assert.deepEqual(wide, ['glessner_house', 'keith_house', 'far_house'], 'a listener asking within 100 m still sees it');
  assert.equal(t.current(40), null); assert.equal(t.current().id, 'far_house', 'current() answers out to the reach');
  offWide();
  const n = heard.length;
  pose = { ...pose, e: 2 };
  hit = null;
  t.tick(6000);
  assert.equal(heard.length, n, 'nothing to nothing is not news');
  t.invalidate();
  hit = { id: 'glessner_house', record: {}, distance: 5 };
  t.tick(6001);
  assert.equal(t.current().id, 'glessner_house', 'invalidate looks again at once, still or not');
  off();
  const before = looks;
  pose = { ...pose, e: 9 };
  t.tick(9000);
  assert.equal(looks, before, 'no listener left, no look');
  assert.throws(() => createTarget({}), /pick\(\) and pose\(\)/);
  const broken = createTarget({ pick: () => { throw new Error('pick failed'); }, pose: () => pose });
  assert.equal(broken.current(), null, 'a failing pick is nothing in front of you, not a crash');
}

// ---- where.js ------------------------------------------------------------------
{
  const scene1904 = json('data/scenes/1904.json');
  const grid = json('data/street_grid/1904.json');
  const where = createWhere({ grid });
  const spawn = scene1904.spawn;
  const at = where.at(spawn.local_e, spawn.local_n, spawn.yaw_deg);
  assert.equal(at?.mode, 'corner', JSON.stringify(at));
  assert.match(at.place, /Prairie Avenue/, at.place);
  assert.match(at.place, /Eighteenth Street/, at.place);
  // Halfway along Prairie between 16th and 18th: on Prairie, at no corner.
  const prairie = grid.carriageways.find((c) => c.id === 'prairie_16_18').polygon_local_m;
  const mid = prairie.reduce((a, [e, n]) => [a[0] + e / prairie.length, a[1] + n / prairie.length], [0, 0]);
  assert.deepEqual(where.at(mid[0], mid[1]), { mode: 'on', place: 'Prairie Avenue' });
  assert.equal(where.at(mid[0] + 5000, mid[1]), null, 'far from every street is nowhere named');
  assert.equal(polygonDistance(mid[0], mid[1], prairie), 0, 'inside a polygon is 0 m from it');

  // 1835 reads the scene index's street records through streets.status, by their 1835 names.
  const status = (mode) => () => ({ mode, distance_m: 30,
    streets: [{ name_1835: 'Lake Street' }, { name_1835: 'Dearborn Street' }].slice(0, mode === 'intersection' ? 2 : 1) });
  assert.deepEqual(createWhere({ streets: { status: status('intersection') } }).at(0, 0), { mode: 'corner', place: 'Lake Street & Dearborn Street' });
  assert.deepEqual(createWhere({ streets: { status: status('on') } }).at(0, 0), { mode: 'on', place: 'Lake Street' });
  assert.deepEqual(createWhere({ streets: { status: status('ahead') } }).at(0, 0), { mode: 'near', place: 'near Lake Street' });
  assert.equal(createWhere({ streets: { status: () => null } }).at(0, 0), null);

  assert.equal(facingWords(264.94), 'facing west');
  assert.equal(facingWords(-90), 'facing west');
  assert.equal(facingWords(44), 'facing north-east');
  assert.equal(clockWords(scene1904.lighting.local_time), '10:30 am');
  assert.equal(clockWords(json('data/scenes/1835.json').lighting.local_time), '12:30 pm');
  assert.equal(clockWords('00:05'), '12:05 am');
  assert.equal(clockWords(undefined), '');
  assert.equal(screenDate('1904-07-01'), '1904.07.01');
}

// ---- the heights -----------------------------------------------------------------
{
  const h = detentHeights(780);
  assert.deepEqual(h, [DOCK_PX, 374, 640]);
  assert.equal(snapLevel(300, 0, h, 0), 1, 'let go nearer HALF: HALF');
  assert.equal(snapLevel(600, 0, h, 1), 2, 'let go nearer FULL: FULL');
  assert.equal(snapLevel(120, 0, h, 1), 0, 'let go near the bottom: DOCK');
  assert.equal(snapLevel(380, 0.9, h, 1), 2, 'a quick flick up from HALF: FULL');
  assert.equal(snapLevel(380, -0.9, h, 1), 0, 'a quick flick down from HALF: DOCK');
  assert.equal(snapLevel(640, 2, h, 2), 2, 'no height above FULL');
  assert.deepEqual([0, 1, 2].map((l) => tapLevel(l)), [1, 2, 0], 'a tap steps up, and FULL drops to DOCK');
  assert.deepEqual([0, 1].map((l) => tapLevel(l, 2)), [1, 0], 'the desktop panel toggles');
  assert.equal(moveWords({}), 'Walking');
  assert.equal(moveWords({ pace: 'horse' }), 'On horseback');
  assert.equal(moveWords({ pace: 'wagon', riding: true }), 'By wagon, on the way');
  assert.equal(moveWords({ flying: true, pace: 'horse' }), 'Flying');
}

// ---- the device over a hand-made DOM -----------------------------------------------
function fakeDom() {
  const byId = new Map();
  const make = (tag, id = null) => {
    const listeners = {};
    const el = {
      tagName: tag.toUpperCase(), id, hidden: false, textContent: '', title: '', type: '', className: '',
      dataset: {}, style: { width: '', height: '', removeProperty(k) { this[k] = ''; } },
      attrs: {}, children: [], focused: 0,
      classList: { set: new Set(), add(c) { this.set.add(c); }, remove(c) { this.set.delete(c); }, contains(c) { return this.set.has(c); } },
      setAttribute(k, v) { this.attrs[k] = String(v); },
      getAttribute(k) { return this.attrs[k] ?? null; },
      addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
      dispatch(type, ev = {}) { for (const fn of listeners[type] ?? []) fn({ preventDefault() {}, target: el, button: 0, ...ev }); },
      append(c) { this.children.push(c); },
      insertBefore(c) { this.children.push(c); },
      cloneNode() { return make(tag); },
      focus() { this.focused++; },
      getBoundingClientRect: () => ({ height: Number.parseFloat(el.style.height) || 64 }),
      querySelector(sel) {
        const m = /^#([\w-]+)$/.exec(sel);
        if (m) return byId.get(m[1]) ?? null;
        if (sel === 'svg') return make('svg');
        if (sel === '[data-app="home"]') return homeApp;
        return null;
      },
      querySelectorAll(sel) { return sel === '.nav-app[data-app]' ? [homeApp, ...railButtons] : []; },
    };
    if (id) byId.set(id, el);
    return el;
  };
  const railButtons = [];
  const homeApp = make('button'); homeApp.dataset.app = 'home';
  const ids = ['nav-grip', 'nav-head', 'nav-rail', 'nav-collapse', 'nav-home-title', 'nav-where', 'nav-where-detail',
    'nav-front-name', 'nav-front-detail', 'nav-inspect', 'nav-jaunt', 'nav-jaunt-step', 'nav-jaunt-title', 'nav-jaunt-bar',
    'nav-move', 'nav-confidence', 'nav-date'];
  for (const id of ids) make(id === 'nav-grip' || id === 'nav-inspect' ? 'button' : 'div', id);
  const tabs = ['goto', 'travel', 'people', 'businesses', 'evidence', 'settings', 'controls', 'whatsnew'].map((t) => {
    const tab = make('button'); tab.dataset.tab = t; tab.attrs.title = t; return tab;
  });
  tabs.find((t) => t.dataset.tab === 'people').hidden = true; // a scene without residents (T-1740)
  const docEl = { dataset: {} };
  const body = { classList: { set: new Set(), add(c) { this.set.add(c); } } };
  const doc = {
    documentElement: docEl, body,
    querySelectorAll: (sel) => (sel === '.panel-tab[data-tab]' ? tabs : []),
    createElement: (tag) => { const b = make(tag); railButtons.push(b); return b; },
  };
  const root = make('section', 'navigator');
  root.ownerDocument = doc;
  byId.get('nav-rail').insertBefore = (c) => {};
  return { root, byId, doc, docEl, body, railButtons, homeApp };
}

for (const phone of [true, false]) {
  const dom = fakeDom();
  const calls = [];
  let pose = { e: 0, n: 0, bearingDeg: 264.94 };
  let hit = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 18.3 };
  const target = createTarget({ pick: () => hit, pose: () => ({ ...pose, pitchDeg: 0 }) });
  const grid = json('data/street_grid/1904.json');
  const spawn = json('data/scenes/1904.json').spawn;
  pose = { e: spawn.local_e, n: spawn.local_n, bearingDeg: spawn.yaw_deg };
  let jauntState = null;
  let t = 0;
  const nav = createNavigator({
    root: dom.root,
    scene: json('data/scenes/1904.json'),
    hud: { setPanel: (open) => calls.push(['panel', open]), selectTab: (id) => calls.push(['tab', id]) },
    target,
    where: createWhere({ grid }),
    pose: () => pose,
    jaunt: () => jauntState,
    move: () => ({ pace: 'walk' }),
    confidence: () => false,
    onInspect: (id) => calls.push(['inspect', id]),
    isPhone: () => phone,
    viewportHeight: () => 780,
    now: () => t,
  });
  const label = phone ? 'phone' : 'desktop';
  assert.equal(dom.body.classList.set.has('has-navigator'), true);
  assert.equal(dom.byId.get('nav-date').textContent, '1904.07.01', 'the screen header carries the scene date');
  assert.equal(nav.detent, phone ? 'dock' : 'rail', `${label}: it starts closed`);
  assert.equal(phone ? dom.docEl.dataset.navigator : dom.docEl.dataset.navigator, phone ? undefined : 'rail');

  // The rail: the drawer's sections, What's new left in the menu, a scene's missing section left out.
  const rail = dom.railButtons.filter((b) => b.dataset.bridge === 'drawer');
  assert.deepEqual(rail.map((b) => b.dataset.app), ['goto', 'travel', 'people', 'businesses', 'evidence', 'settings', 'controls']);

  // Opening by hand: Home paints at once and focus moves into it.
  dom.byId.get(phone ? 'nav-grip' : 'nav-collapse').dispatch('click');
  assert.equal(nav.detent, phone ? 'half' : 'open', `${label}: one tap opens it`);
  assert.equal(dom.byId.get('nav-home-title').focused, 1, `${label}: focus moves into Home on open`);
  assert.equal(dom.byId.get('nav-grip').attrs['aria-expanded'], 'true');
  const s = nav.snapshot();
  assert.match(s.where, /Prairie Avenue & East Eighteenth Street/, s.where);
  assert.equal(s.whereDetail, 'facing west · 10:30 am');
  assert.equal(s.front?.name, 'Glessner House');
  assert.match(dom.byId.get('nav-front-detail').textContent, /ft away$/);
  assert.equal(dom.byId.get('nav-inspect').hidden, false, 'the Inspect key shows with a target');
  assert.equal(s.jaunt, null, 'no Jaunt, no Jaunt block');
  assert.equal(dom.byId.get('nav-jaunt').hidden, true);
  assert.equal(s.move, 'Walking');
  assert.equal(s.confidence, 'Off');
  assert.equal(rail.find((b) => b.dataset.app === 'people').hidden, true, 'a section the scene leaves out stays out of the rail');

  // A Jaunt in progress, read within the half second.
  jauntState = { jaunt: { title: 'A corner of Prairie Avenue', stops: [{}, {}] }, stopIndex: 0 };
  t = 400; assert.equal(nav.update(), false, 'not before 500 ms');
  t = 600; assert.equal(nav.update(), true);
  assert.deepEqual(nav.snapshot().jaunt, { step: '1 / 2', title: 'A corner of Prairie Avenue' });
  assert.equal(dom.byId.get('nav-jaunt-bar').style.width, '50%');

  // Turning away: past 40 m is nothing in front of you, and the key goes.
  hit = null; pose = { ...pose, bearingDeg: 90 };
  t = 1200; target.tick(t);
  assert.equal(dom.byId.get('nav-front-name').textContent, 'Nothing close by');
  assert.equal(dom.byId.get('nav-inspect').hidden, true);
  hit = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 72 };
  pose = { ...pose, bearingDeg: 264 };
  t = 1800; target.tick(t);
  assert.equal(dom.byId.get('nav-front-name').textContent, 'Glessner House', `${label}: across the street (72 m, the 1904 spawn) is in front of you`);
  hit = { ...hit, distance: 101 }; pose = { ...pose, e: pose.e + 1 };
  t = 2400; target.tick(t);
  assert.equal(dom.byId.get('nav-front-name').textContent, 'Nothing close by', 'past 100 m is not');
  hit = { ...hit, distance: 12 }; pose = { ...pose, e: pose.e - 1 };
  t = 3000; target.tick(t);
  dom.byId.get('nav-inspect').dispatch('click');
  assert.deepEqual(calls.at(-1), ['inspect', 'glessner_house'], `${label}: Inspect opens the building's card`);
  if (phone) assert.equal(nav.detent, 'dock', 'phone: Inspect docks the sheet so the card has the screen');

  // A bridged icon closes the device and opens the drawer on its own section.
  nav.open(1);
  rail.find((b) => b.dataset.app === 'evidence').dispatch('click');
  assert.deepEqual(calls.slice(-2), [['panel', true], ['tab', 'evidence']]);
  assert.equal(nav.detent, phone ? 'dock' : 'rail');

  // Docked by the code (entering the town), focus stays where it was.
  nav.open(1);
  const focused = dom.byId.get('nav-home-title').focused;
  nav.dock();
  nav.open(1);
  assert.equal(dom.byId.get('nav-home-title').focused, focused, 'nothing moves focus when the code opens or docks it');
  t = 10_000; nav.dock();
  assert.equal(nav.update(), false, 'a docked device does not repaint');

  if (phone) {
    // Heights by hand: grip taps, then a drag of the head.
    nav.dock();
    const grip = dom.byId.get('nav-grip');
    grip.dispatch('click'); assert.equal(nav.detent, 'half');
    grip.dispatch('click'); assert.equal(nav.detent, 'full');
    grip.dispatch('click'); assert.equal(nav.detent, 'dock', 'from FULL, a tap drops it to DOCK');
    const head = dom.byId.get('nav-head');
    t = 20_000;
    head.dispatch('pointerdown', { pointerId: 1, clientY: 760 });
    t = 20_200;
    head.dispatch('pointermove', { pointerId: 1, clientY: 600 });
    t = 20_400;
    head.dispatch('pointermove', { pointerId: 1, clientY: 470 });
    assert.equal(dom.root.classList.contains('is-dragging'), true);
    head.dispatch('pointerup', { pointerId: 1, clientY: 470 });
    head.dispatch('click');
    assert.equal(nav.detent, 'half', 'a slow drag to about half height lets go at HALF');
    assert.equal(dom.root.style.height, '', 'the drag leaves no inline height behind');
    assert.equal(dom.root.classList.contains('is-dragging'), false);
    t = 30_000;
    head.dispatch('pointerdown', { pointerId: 2, clientY: 400 });
    t = 30_050;
    head.dispatch('pointermove', { pointerId: 2, clientY: 330 });
    head.dispatch('pointerup', { pointerId: 2, clientY: 330 });
    assert.equal(nav.detent, 'full', 'a quick flick up from HALF lets go at FULL');
  }
}

// ---- the markup and the stylesheet ----------------------------------------------------
{
  const html = fs.readFileSync(path.join(ROOT, 'renderers/web/index.html'), 'utf8');
  const css = fs.readFileSync(path.join(ROOT, 'renderers/web/css/navigator.css'), 'utf8');
  const section = html.slice(html.indexOf('<section id="navigator"'), html.indexOf('</section>\n\n<aside id="popup"'));
  assert(section.length > 100, 'the Navigator markup is in the page');
  assert.equal((section.match(/NAVIGATOR MK II/g) ?? []).length, 1, 'the device label is one string');
  assert.match(section, /SCR 01 · HOME/);
  assert(!/[a-z]+_[a-z]+/.test(section.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ')), 'no snake_case a visitor can read');
  assert.match(section, /Confidence view/, 'the locked term, exactly');
  const visible = section.replace(/<!--[\s\S]*?-->/g, '').replace(/<[^>]*>/g, ' ');
  assert(!/\b(Confidence chip|confidence view)\b/.test(visible), 'no variant of a locked term');
  for (const sel of ['[data-detent="half"]', '[data-detent="full"]', '[data-detent="rail"]', 'width: 400px', 'height: 64px',
    '.48', '.82', 'var(--ease-detent', 'prefers-reduced-motion']) {
    assert(css.includes(sel), `navigator.css carries ${sel}`);
  }
  assert.match(css, /\.28s var\(--ease-detent/, 'a height change takes 280 ms on the detent easing');
  assert.match(html, /<link rel="stylesheet" href="\.\/css\/navigator\.css">/);
  assert.match(html, /class="gate-code" aria-hidden="true"><span>NAVIGATOR MK II<\/span><span>SCR 01 · HOME<\/span>/,
    'the arrival device wears the screen code on its back face');
}

console.log('NAVIGATOR PASS — the probe looks only when asked and moved, each asker within its own distance (Home 100 m); the street at the 1904 spawn is Prairie & Eighteenth; '
  + 'DOCK, HALF and FULL by tap, drag and flick, the desktop panel to its rail; Home paints the place, the target, the Jaunt, Move and the Confidence view; the rail opens the drawer’s sections');
