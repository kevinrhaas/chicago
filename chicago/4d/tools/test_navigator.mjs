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
import { createNavigator, snapLevel, tapLevel, detentHeights, moveWords, DOCK_PX, dockPill, dockYear, JOYSTICK_CLEAR_PX, DOCK_PILL_PX } from '../renderers/web/js/navigator.js';
import { createRail, railOrder, capped, MAX_ICONS } from '../renderers/web/js/nav-rail.js';
import { APPS } from '../renderers/web/js/apps/index.js';
import { install as installDrawerHost, SECTION_HOME, APP_SECTIONS } from '../renderers/web/js/apps/drawer-host.js';

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

// ---- a hand-made DOM, just large enough for the device and its rail ----------------
function miniDom() {
  const byId = new Map();
  const matches = (el, sel) => {
    let m;
    if ((m = /^#([\w-]+)$/.exec(sel))) return el.id === m[1];
    if ((m = /^\.([\w-]+)$/.exec(sel))) return el.classList.contains(m[1]);
    if ((m = /^\[data-app="([\w-]+)"\]$/.exec(sel))) return el.dataset.app === m[1];
    if ((m = /^\.([\w-]+)\[data-tab\]$/.exec(sel))) return el.classList.contains(m[1]) && el.dataset.tab != null;
    if ((m = /^\.([\w-]+)\[data-tab="([\w-]+)"\]$/.exec(sel))) return el.classList.contains(m[1]) && el.dataset.tab === m[2];
    if (sel === 'svg') return el.tagName === 'SVG';
    return false;
  };
  const walk = (el, out = []) => { for (const c of el.children) { out.push(c); walk(c, out); } return out; };
  const make = (tag, id = null) => {
    const listeners = {};
    let _id = null;
    const el = {
      tagName: tag.toUpperCase(), hidden: false, textContent: '', title: '', type: '', href: '',
      get ownerDocument() { return doc; },
      dataset: {}, style: { width: '', height: '', removeProperty(k) { this[k] = ''; } },
      attrs: {}, children: [], parent: null, focused: 0, html: '',
      get id() { return _id; }, set id(v) { if (_id) byId.delete(_id); _id = v; if (v) byId.set(v, el); },
      get className() { return [...this.classList.set].join(' '); },
      set className(v) { this.classList.set = new Set(String(v).split(/\s+/).filter(Boolean)); },
      classList: {
        set: new Set(),
        add(...c) { for (const x of c) this.set.add(x); }, remove(...c) { for (const x of c) this.set.delete(x); },
        contains(c) { return this.set.has(c); },
        toggle(c, on = !this.set.has(c)) { if (on) this.set.add(c); else this.set.delete(c); return on; },
      },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
      dispatch(type, ev = {}) { for (const fn of listeners[type] ?? []) fn({ preventDefault() {}, target: el, button: 0, ...ev }); },
      append(...cs) { for (const c of cs) { c.parent?.children.splice(c.parent.children.indexOf(c), 1); c.parent = el; el.children.push(c); } },
      insertBefore(c, ref) {
        c.parent?.children.splice(c.parent.children.indexOf(c), 1);
        c.parent = el;
        const i = ref ? el.children.indexOf(ref) : -1;
        if (i < 0) el.children.push(c); else el.children.splice(i, 0, c);
      },
      remove() { if (el.parent) { el.parent.children.splice(el.parent.children.indexOf(el), 1); el.parent = null; } },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      insertAdjacentHTML(_where, html) { el.html += html; },
      cloneNode() { return make(tag); },
      focus() { el.focused++; },
      getBoundingClientRect: () => ({ height: Number.parseFloat(el.style.height) || 64 }),
      querySelector(sel) { return el.querySelectorAll(sel)[0] ?? null; },
      querySelectorAll(sel) {
        const [first, ...rest] = sel.split(' ');
        let scope = walk(el).filter((c) => matches(c, first));
        for (const part of rest) scope = scope.flatMap((x) => walk(x).filter((c) => matches(c, part)));
        return scope;
      },
      get parentElement() { return el.parent; },
    };
    if (id) el.id = id;
    return el;
  };
  const docEl = { dataset: {} };
  const body = make('body');
  const doc = {
    documentElement: docEl, body,
    createElement: (tag) => make(tag),
    getElementById: (id) => byId.get(id) ?? null,
    querySelectorAll: (sel) => body.querySelectorAll(sel),
    querySelector: (sel) => body.querySelector(sel),
  };
  const add = (parent, tag, id, cls = []) => { const e = make(tag, id); e.classList.add(...cls); parent.append(e); return e; };
  const root = add(body, 'section', 'navigator');
  add(root, 'button', 'nav-grip');
  const head = add(root, 'header', 'nav-head');
  add(head, 'span', 'nav-code');
  add(head, 'span', 'nav-date');
  const navBody = add(root, 'div', null, ['nav-body']);
  const rail = add(navBody, 'nav', 'nav-rail');
  add(rail, 'button', 'nav-collapse');
  const home = add(navBody, 'div', 'nav-home', ['nav-screen']);
  for (const id of ['nav-home-title', 'nav-where', 'nav-where-detail', 'nav-front-name', 'nav-front-detail', 'nav-inspect',
    'nav-jaunt', 'nav-jaunt-step', 'nav-jaunt-title', 'nav-jaunt-bar', 'nav-move', 'nav-confidence']) add(home, 'div', id);
  // The drawer's #panel, still in #hud as the page is written (T-2620 moves it into the apps).
  const hud = add(body, 'div', 'hud');
  const panel = add(hud, 'div', 'panel', ['hud-panel']);
  panel.hidden = true;
  const tabsRow = add(panel, 'nav', null, ['panel-tabs']);
  for (const t of ['goto', 'travel', 'people', 'businesses', 'evidence', 'settings', 'controls', 'whatsnew']) {
    const tab = add(tabsRow, 'button', null, ['panel-tab']); tab.dataset.tab = t;
  }
  add(hud, 'span', 'help-dot').hidden = true;
  return { root, doc, docEl, body, byId, rail, panel };
}
// T-2622: the tabs sit in the rail's tablist wrapper, in front of the collapse key.
const tabsOf = (dom) => dom.rail.children.find((c) => c.classList.contains('nav-tabs'))?.children ?? [];
const railIds = (dom) => tabsOf(dom).filter((b) => b.dataset.app && !b.hidden).map((b) => b.dataset.app);
const button = (dom, id) => tabsOf(dom).find((b) => b.dataset.app === id);
const fakeStorage = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), m }; };

// ---- nav-rail.js: the registry on its own ---------------------------------------------
{
  const mk = (id, order, extra = {}) => ({ id, label: id, code: `SCR · ${id}`, order, icon: '<svg></svg>', launch: () => {}, ...extra });
  assert.deepEqual(railOrder([mk('settings', 100, { pin: 'bottom' }), mk('jaunts', 10), mk('home', 0), mk('guide', 90, { pin: 'bottom' }), mk('map', 40)]).map((a) => a.id),
    ['home', 'jaunts', 'map', 'guide', 'settings'], 'the top group by order, then the pinned foot');
  const many = Array.from({ length: 12 }, (_, i) => mk(`c${i}`, 10 + i, { when: () => true }));
  const fixed = [mk('home', 0), mk('guide', 90, { pin: 'bottom' })];
  const ordered = railOrder([...fixed, ...many]);
  const wants = new Map(ordered.map((a) => [a.id, true]));
  const kept = capped(ordered, wants);
  assert.equal(kept.size, MAX_ICONS, 'never more than ten');
  assert(kept.has('home') && kept.has('guide'), 'the always-on and the pinned keep their place');
  assert(!kept.has('c11') && !kept.has('c10') && !kept.has('c9'), 'the latest contextual ones give way');

  // The registry over the mini DOM: a contextual app with a linger, a badge, a glow, a lazy app, a stub.
  const dom = miniDom();
  let t = 0;
  const later = [];
  const wait = (fn, ms) => later.push([t + ms, fn]);
  const run = () => { for (const [at, fn] of later.splice(0)) { if (at <= t) fn(); else later.push([at, fn]); } };
  let ctxv = { selected: null, target: null, badge: false, glow: false };
  const storage = fakeStorage();
  let reduced = false;
  const opened = [], launched = [];
  let loads = 0, mounts = 0;
  const rail = createRail({
    rail: dom.rail, screens: dom.root.querySelector('.nav-body'), codeEl: dom.byId.get('nav-code'), doc: dom.doc,
    context: () => ctxv, before: dom.byId.get('nav-collapse'), storage, reduced: () => reduced, now: () => t, wait,
    onOpen: (id, by) => opened.push([id, by]), onLaunch: (id) => launched.push(id),
  });
  rail.register({ id: 'home', label: 'Home', code: 'SCR 01 · HOME', order: 0, icon: '<svg></svg>', panel: 'nav-home' });
  rail.register({ id: 'jaunts', label: 'Jaunts', code: 'SCR 02 · JAUNTS', order: 10, icon: '<svg></svg>', launch: (c) => launched.push(['jaunts-ran', !!c]) });
  rail.register({ id: 'inspect', label: 'Inspect', code: 'SCR 03 · INSPECT', order: 20, icon: '<svg></svg>',
    when: (c) => !!(c.selected || c.target), linger: 300, launch: () => {} });
  rail.register({ id: 'confidence', label: 'Confidence view', code: 'SCR 07', order: 50, icon: '<svg></svg>', glow: (c) => c.glow, launch: () => {} });
  rail.register({ id: 'jump', label: 'Jump', code: 'SCR 08 · JUMP', order: 70, icon: '<svg></svg>',
    load: async () => { loads++; return { default: { mount(el) { mounts++; el.textContent = 'jump'; } } }; } });
  rail.register({ id: 'settings', label: 'Settings', code: 'SCR 10', order: 100, pin: 'bottom', icon: '<svg></svg>', badge: (c) => c.badge, launch: () => {} });
  assert.throws(() => rail.register({ id: 'home', label: 'Home', panel: 'x' }), /already registered/);
  assert.throws(() => rail.register({ id: 'two', label: 'Two', panel: 'x', load() {} }), /needs one of/);
  assert.throws(() => rail.register({ id: 'none', label: 'None' }), /needs one of/);
  assert.equal(dom.rail.children.at(-1).id, 'nav-collapse', 'apps go in front of the collapse key');
  // T-2622: the rail is a tablist (its own wrapper, since the collapse key is no tab), each
  // app a labelled tab, its screen a tabpanel labelled by it.
  const tablist = dom.rail.children.find((c) => c.classList.contains('nav-tabs'));
  assert.equal(tablist.getAttribute('role'), 'tablist');
  assert.equal(tablist.getAttribute('aria-label'), 'Navigator apps');
  assert.deepEqual(dom.rail.children.map((c) => c.id || c.className), ['nav-tabs', 'nav-collapse']);
  for (const b of tabsOf(dom)) {
    assert.equal(b.getAttribute('role'), 'tab', `${b.dataset.app} is a tab`);
    assert.ok(b.getAttribute('aria-label'), `${b.dataset.app}'s tab is labelled`);
    assert.equal(b.getAttribute('aria-pressed'), null, 'a tab says aria-selected, never aria-pressed');
  }
  assert.equal(button(dom, 'settings').classList.contains('nav-app-foot-first'), true, 'Settings starts the foot');

  await rail.select('home', { by: 'quiet' });
  rail.evaluate(t);
  assert.deepEqual(railIds(dom), ['home', 'jaunts', 'confidence', 'jump', 'settings'], 'no target, no Inspect');

  // QA-07: look at the Glessner House — Inspect slides in, new; look away — it leaves 300 ms later.
  ctxv = { ...ctxv, target: { id: 'glessner_house', distance: 30 } };
  t = 1000; rail.evaluate(t);
  const insp = button(dom, 'inspect');
  assert.deepEqual(railIds(dom), ['home', 'jaunts', 'inspect', 'confidence', 'jump', 'settings'], 'Inspect slides in under Jaunts');
  assert(insp.classList.contains('is-entering') && insp.classList.contains('is-new'), 'with the slide, the glint and the first-appearance dot');
  t = 1240; run();
  assert(!insp.classList.contains('is-entering'), 'the slide is done within 240 ms');
  ctxv = { ...ctxv, target: null };
  t = 1300; rail.evaluate(t);
  assert.equal(insp.hidden, false, 'a glance away keeps it');
  t = 1590; rail.evaluate(t);
  assert.equal(insp.hidden, false, '…for 300 ms');
  t = 1600; rail.evaluate(t);
  assert(insp.classList.contains('is-leaving'), 'then it slides out');
  t = 1840; run();
  assert.equal(insp.hidden, true, 'and is gone 240 ms later');
  // Selected, it stays with no target at all.
  ctxv = { ...ctxv, selected: 'glessner_house' };
  t = 2000; rail.evaluate(t); ctxv = { ...ctxv, target: null };
  t = 5000; rail.evaluate(t);
  assert.equal(insp.hidden, false, 'a selected building keeps Inspect with no target');
  await rail.select('inspect', { by: 'hand' });
  assert.equal(insp.classList.contains('is-new'), false, 'opening it once clears the dot');
  assert.deepEqual(JSON.parse(storage.m.get('chicago4d.navigator.seen')), ['inspect'], 'and remembers it was seen');
  assert.deepEqual(launched.at(-1), 'inspect', 'a stub launches (and the device docks)');

  // A second visit: the dot does not come back for an app once seen.
  const dom2 = miniDom();
  const rail2 = createRail({ rail: dom2.rail, screens: dom2.root.querySelector('.nav-body'), doc: dom2.doc, storage, wait: () => {}, reduced: () => true,
    context: () => ({ target: { id: 'x', distance: 1 } }) });
  rail2.register({ id: 'inspect', label: 'Inspect', when: (c) => !!c.target, launch: () => {} });
  rail2.evaluate(0);
  assert.equal(button(dom2, 'inspect').classList.contains('is-new'), false, 'a seen app carries no dot on the next visit');
  assert.equal(button(dom2, 'inspect').classList.contains('is-entering'), false, 'no slide with reduced motion');

  // Badge and glow.
  ctxv = { ...ctxv, badge: true, glow: true };
  rail.evaluate(t);
  assert(button(dom, 'settings').classList.contains('is-badged'), 'Settings carries What’s new’s dot');
  assert(button(dom, 'confidence').classList.contains('is-glowing'), 'the Confidence view icon glows while the view is on');

  // A lazy app loads once, on first open, into its own screen; switching shows the warm-up.
  await rail.select('home', { by: 'hand' });
  assert.equal(loads, 0, 'nothing loads before it is opened');
  await rail.select('jump', { by: 'hand' });
  await rail.select('home', { by: 'hand' });
  await rail.select('jump', { by: 'hand' });
  assert.equal(loads, 1); assert.equal(mounts, 1, 'loaded and mounted once');
  const jumpPanel = dom.byId.get('nav-app-jump');
  assert.equal(jumpPanel.textContent, 'jump');
  assert.equal(jumpPanel.hidden, false); assert.equal(dom.byId.get('nav-home').hidden, true, 'one screen at a time');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 08 · JUMP', 'the header reads the open app’s screen code');
  assert(jumpPanel.classList.contains('is-warming') && dom.byId.get('nav-code').classList.contains('is-warming'), 'the tube warm-up runs on a switch');
  t += 160; run();
  assert(!jumpPanel.classList.contains('is-warming'), 'for 160 ms');
  reduced = true;
  await rail.select('home', { by: 'hand' });
  assert(dom.byId.get('nav-home').classList.contains('is-fading'), 'a crossfade instead under reduced motion');
  assert.deepEqual(button(dom, 'home').getAttribute('aria-selected'), 'true');
  assert.equal(button(dom, 'home').tabIndex, 0, 'roving focus: the open app\'s tab is the rail\'s Tab stop');
  assert.equal(button(dom, 'jaunts').tabIndex, -1);
  assert.equal(button(dom, 'jaunts').getAttribute('aria-selected'), 'false');
  assert.equal(jumpPanel.getAttribute('role'), 'tabpanel');
  assert.equal(jumpPanel.getAttribute('aria-labelledby'), 'nav-tab-jump');
  assert.equal(button(dom, 'jump').getAttribute('aria-controls'), 'nav-app-jump');
  assert.equal(jumpPanel.tabIndex, -1, 'an app\'s screen takes focus on open');
  assert.deepEqual(rail.unregister('jump'), true);
  assert.equal(button(dom, 'jump'), undefined, 'unregister takes the icon out');
}

// ---- the device, its Home and its apps -------------------------------------------------
for (const phone of [true, false]) {
  const dom = miniDom();
  const calls = [];
  // Where 1904 opens, the Glessner House is 72 m off: in front of you, not yet within Inspect's 40 m.
  let hit = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 72 };
  const spawn = json('data/scenes/1904.json').spawn;
  let pose = { e: spawn.local_e, n: spawn.local_n, bearingDeg: spawn.yaw_deg };
  const target = createTarget({ pick: () => hit, pose: () => ({ ...pose, pitchDeg: 0 }) });
  let jauntState = null;
  let t = 0;
  const label = phone ? 'phone' : 'desktop';
  // The HUD's side of the drawer: a section open or shut, and which one (hud.js).
  const fakeHud = {
    open: false, tab: 'goto', host: null,
    panelOpen() { return this.open; },
    setPanel(open, { fromHost = false } = {}) { this.open = !!open; dom.panel.hidden = !open; if (!fromHost) this.host?.[open ? 'open' : 'close']?.(this.tab); },
    selectTab(t, { fromHost = false } = {}) { this.tab = t; if (!fromHost && this.open) this.host?.show?.(t); },
    setHost(h) { this.host = h; },
  };
  const nav = createNavigator({
    root: dom.root,
    scene: json('data/scenes/1904.json'),
    target,
    where: createWhere({ grid: json('data/street_grid/1904.json') }),
    pose: () => pose,
    jaunt: () => jauntState,
    move: () => ({ pace: 'walk' }),
    confidence: () => false,
    onInspect: (id) => calls.push(['inspect', id]),
    isPhone: () => phone,
    viewportHeight: () => 780,
    now: () => t,
    storage: fakeStorage(),
    apps: APPS,
    context: () => ({ api: { hud: fakeHud }, scene: { id: '1904' }, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false,
      actions: { openSection: (id) => calls.push(['section', id]), jaunts: () => calls.push(['jaunts']), inspect: (id) => calls.push(['card', id]) } }),
  });
  await Promise.resolve();
  assert.equal(dom.body.classList.contains('has-navigator'), true);
  assert.equal(dom.byId.get('nav-date').textContent, '1904.07.01', 'the screen header carries the scene date');
  assert.equal(nav.detent, phone ? 'dock' : 'rail', `${label}: it starts closed`);
  assert.equal(nav.app, 'home', 'Home is the open app');
  assert.equal(dom.docEl.dataset.navigator, phone ? undefined : 'rail');
  assert(APPS.length <= MAX_ICONS && new Set(APPS.map((a) => a.id)).size === APPS.length, 'ten apps at most, each once');
  for (const app of APPS) {
    assert(app.label && app.code && /^SCR \d\d · /.test(app.code) && /^<svg[\s\S]*<\/svg>$/.test(app.icon), `${app.id} declares a label, a screen code and an icon`);
    assert(!/[a-z]+_[a-z]+/.test(app.label), `${app.id}: no snake_case in its label`);
  }

  // Opening by hand: Home paints at once and focus moves into it.
  dom.byId.get(phone ? 'nav-grip' : 'nav-collapse').dispatch('click');
  assert.equal(nav.detent, phone ? 'half' : 'open', `${label}: one tap opens it`);
  // T-2622: onto Home's screen, which shows its focus ring (the heading is visually hidden).
  assert.equal(dom.byId.get('nav-home').focused, 1, `${label}: focus moves into Home on open`);
  // 1904 has no people records and nothing within 40 m of the reticle yet: no People, no Inspect.
  assert.deepEqual(nav.apps, ['home', 'jaunts', 'map', 'confidence', 'move', 'jump', 'guide', 'settings'], `${label}: the usual eight`);
  const s = nav.snapshot();
  assert.match(s.where, /Prairie Avenue & East Eighteenth Street/, s.where);
  assert.equal(s.whereDetail, 'facing west · 10:30 am');
  assert.equal(s.front?.name, 'Glessner House');
  assert.equal(dom.byId.get('nav-inspect').hidden, false, 'the Inspect key shows with a target');
  assert.equal(s.jaunt, null, 'no Jaunt, no Jaunt block');
  assert.equal(s.move, 'Walking');
  assert.equal(s.confidence, 'Off');

  // Walk up to it: the probe's 40 m answer brings Inspect onto the rail (QA-07 in the device).
  hit = { ...hit, distance: 18.3 }; pose = { ...pose, e: pose.e - 1 };
  t = 600; target.tick(t);
  assert.deepEqual(nav.apps.slice(0, 3), ['home', 'jaunts', 'inspect'], `${label}: 18 m away, Inspect slides in under Jaunts`);

  // A Jaunt in progress, read within the half second.
  nav.refresh();
  jauntState = { jaunt: { title: 'A corner of Prairie Avenue', stops: [{}, {}] }, stopIndex: 0 };
  t = 900; assert.equal(nav.update(), false, 'not before 500 ms');
  t = 1200; assert.equal(nav.update(), true);
  assert.deepEqual(nav.snapshot().jaunt, { step: '1 / 2', title: 'A corner of Prairie Avenue' });
  assert.equal(dom.byId.get('nav-jaunt-bar').style.width, '50%');

  // Turning away: past 100 m is nothing in front of you, and the key goes.
  hit = null; pose = { ...pose, bearingDeg: 90 };
  t = 1800; target.tick(t);
  assert.equal(dom.byId.get('nav-front-name').textContent, 'Nothing close by');
  assert.equal(dom.byId.get('nav-inspect').hidden, true);
  hit = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 72 };
  pose = { ...pose, bearingDeg: 264 };
  t = 2400; target.tick(t);
  assert.equal(dom.byId.get('nav-front-name').textContent, 'Glessner House', `${label}: across the street (72 m, the 1904 spawn) is in front of you`);
  hit = { ...hit, distance: 12 }; pose = { ...pose, e: pose.e + 1 };
  t = 3000; target.tick(t);
  dom.byId.get('nav-inspect').dispatch('click');
  assert.deepEqual(calls.at(-1), ['inspect', 'glessner_house'], `${label}: Inspect opens the building's card`);
  if (phone) assert.equal(nav.detent, 'dock', 'phone: Inspect docks the sheet so the card has the screen');

  // T-2620: the drawer's sections are apps. Settings moves the one #panel into its screen,
  // shows its own two tabs (Settings, What's new), opens its section; Home takes it away again.
  nav.open(1);
  button(dom, 'settings').dispatch('click');
  await Promise.resolve();
  const settingsScreen = dom.byId.get('nav-app-settings');
  assert.equal(dom.panel.parent, settingsScreen, `${label}: #panel now lives in the Settings app`);
  assert.deepEqual([fakeHud.open, fakeHud.tab], [true, 'settings'], 'and its section is open');
  const visibleTabs = (d) => d.panel.children[0].children.filter((t) => !t.classList.contains('is-elsewhere')).map((t) => t.dataset.tab);
  assert.deepEqual(visibleTabs(dom), ['settings', 'whatsnew'], 'only its own tabs show — two, not eight');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 10 · SETTINGS');
  await nav.select('move');
  assert.equal(dom.panel.parent, dom.byId.get('nav-app-move'), 'Move takes #panel next');
  assert.deepEqual([fakeHud.open, fakeHud.tab], [true, 'travel']);
  assert(dom.panel.classList.contains('has-one-section'), 'one section, no tab row');
  await nav.select('home');
  assert.equal(fakeHud.open, false, 'Home closes the section');
  await nav.select('guide');
  assert.deepEqual([fakeHud.open, fakeHud.tab], [true, 'controls'], 'Guide opens Controls first');
  nav.dock();
  assert.equal(fakeHud.open, false, 'docking closes it');
  nav.open(1);
  assert.equal(fakeHud.open, true, 'and opening again brings it back');
  await nav.select('jaunts');
  assert.deepEqual([fakeHud.open, fakeHud.tab], [true, 'goto'], 'Jaunts holds Go to');
  const lead = dom.byId.get('nav-jaunts-open');
  assert(lead && lead.parent === dom.byId.get('nav-app-jaunts'), 'under a Take a Jaunt key');
  lead.dispatch('click');
  assert.deepEqual(calls.at(-1), ['jaunts'], 'which opens the Jaunts list');
  assert.equal(nav.detent, phone ? 'dock' : 'rail');

  // The HUD's own calls keep their meaning through the adapter (hud.setPanel / selectTab).
  const adapter = installDrawerHost({ hud: fakeHud, navigator: nav, doc: dom.doc });
  assert.equal(button(dom, 'settings').children.some((c) => c.id === 'help-dot'), true, 'What\u2019s new\u2019s dot rides the Settings icon');
  fakeHud.tab = 'evidence';
  adapter.open('evidence');
  await Promise.resolve();
  assert.equal(nav.app, 'guide', 'opening Evidence opens the Guide');
  adapter.show('whatsnew');
  await Promise.resolve();
  assert.equal(nav.app, 'settings', 'choosing What\u2019s new switches to Settings');
  adapter.close();
  assert.equal(nav.detent, phone ? 'dock' : 'rail', 'closing the section docks the device');
  await nav.select('home');
  nav.open(1);
  adapter.close();
  assert.equal(nav.detent, phone ? 'half' : 'open', 'but closing a section never docks Home');

  // Jump is a real, lazy screen: loaded on first open, with HERE on this scene and the Recall key.
  nav.open(1);
  await nav.select('jump');
  const jump = dom.byId.get('nav-app-jump');
  assert(jump && !jump.hidden, 'Jump opens in its own screen');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 08 · JUMP');
  const cards = jump.children[0].children;
  assert.deepEqual(cards.map((c) => c.tagName), ['A', 'DIV'], '1835 is a link, 1904 (here) is not');
  assert.equal(cards[1].getAttribute('aria-current'), 'page');
  assert.equal(cards[0].href, '../1835/');
  assert.equal(jump.children[1].href, '../', 'Recall goes back to the Observatory');
  await nav.select('home');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 01 · HOME');

  // Docked by the code (entering the town), focus stays where it was.
  nav.open(1);
  const focused = dom.byId.get('nav-home').focused;
  nav.dock();
  nav.open(1);
  assert.equal(dom.byId.get('nav-home').focused, focused, 'nothing moves focus when the code opens or docks it');
  t = 10_000; nav.dock();
  assert.equal(nav.update(), false, 'a docked device does not repaint Home');

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

// People: on the rail wherever the scene has a people directory — 1835's town, opened in the
// drawer's People section, and 1904's Glessner household (T-2702), which has no drawer section
// (T-1740) and so opens the Navigator's own screen, its directory read on first open.
{
  const dom = miniDom();
  const hud = { open: false, tab: 'goto', panelOpen() { return this.open; }, setPanel(o) { this.open = o; dom.panel.hidden = !o; }, selectTab(t) { this.tab = t; } };
  const nav = createNavigator({ root: dom.root, scene: json('data/scenes/1835.json'), isPhone: () => false, storage: fakeStorage(),
    apps: APPS, context: () => ({ api: { hud }, hasPeople: true, peopleSection: true }) });
  assert(nav.apps.includes('people'), '1835: People shows');
  assert.deepEqual(nav.apps.slice(0, 3), ['home', 'jaunts', 'people'], 'under Jaunts');
  await nav.select('people');
  assert.equal(dom.panel.parent, dom.byId.get('nav-app-people'), '1835: People holds the drawer\u2019s People section');
  assert.deepEqual([hud.open, hud.tab], [true, 'people']);
  assert.deepEqual(dom.panel.children[0].children.filter((t) => !t.classList.contains('is-elsewhere')).map((t) => t.dataset.tab),
    ['people', 'businesses'], '…with Businesses beside it');
  // A close that lands while People is still mounting for the first time wins: the section
  // ends shut and the device docked, not reopened by the late mount.
  {
    const d2 = miniDom();
    const h2 = { open: false, tab: 'goto', panelOpen() { return this.open; }, setPanel(o) { this.open = o; d2.panel.hidden = !o; },
      selectTab(t) { this.tab = t; }, setHost() {} };
    const n2 = createNavigator({ root: d2.root, scene: json('data/scenes/1835.json'), isPhone: () => true, storage: fakeStorage(),
      apps: APPS, context: () => ({ api: { hud: h2 }, hasPeople: true, peopleSection: true }) });
    const a2 = installDrawerHost({ hud: h2, navigator: n2, doc: d2.doc });
    a2.open('people');
    a2.close();
    for (let i = 0; i < 5; i++) await Promise.resolve();
    await new Promise((r) => setTimeout(r, 0));
    assert.equal(h2.open, false, 'a close before the first mount finishes keeps the section shut');
    assert.equal(n2.detent, 'dock', '…and the device docked');
  }
  // Every section the drawer had has an app to hold it, and no app holds more than two.
  assert.deepEqual(Object.keys(SECTION_HOME).sort(), ['businesses', 'controls', 'evidence', 'goto', 'people', 'settings', 'travel', 'whatsnew']);
  assert(Object.values(APP_SECTIONS).every((t) => t.length <= 2) && Object.keys(APP_SECTIONS).every((a) => APPS.some((x) => x.id === a)));

  const none = createNavigator({ root: miniDom().root, scene: json('data/scenes/1904.json'), isPhone: () => false, storage: fakeStorage(),
    apps: APPS, context: () => ({ hasPeople: false }) });
  assert(!none.apps.includes('people'), 'no directory, no People');

  const dir = json('data/sidecars/1904/people.json');
  let reads = 0;
  const dom4 = miniDom();
  const inspected = [];
  const nav4 = createNavigator({ root: dom4.root, scene: json('data/scenes/1904.json'), isPhone: () => false, storage: fakeStorage(),
    apps: APPS, context: () => ({ hasPeople: true, peopleSection: false,
      actions: { peopleDirectory: async () => { reads++; return dir; }, inspect: (id) => inspected.push(id) } }) });
  assert(nav4.apps.includes('people'), '1904: People shows for the Glessner household');
  assert.equal(reads, 0, 'the directory is not read before People opens');
  await nav4.select('people');
  const screen = dom4.byId.get('nav-app-people');
  assert(screen && !screen.hidden, '1904: People opens its own screen');
  assert.equal(reads, 1, 'read once, on first open');
  const block = screen.children[0];
  assert.equal(block.children[1].textContent, 'The Glessner household at 1800 Prairie Avenue');
  const people = block.children.filter((c) => c.classList.contains('nav-person'));
  assert.deepEqual(people.map((p) => p.children[0].textContent), ['John J. Glessner', 'Frances M. Glessner'], 'the head first');
  assert.deepEqual(people.map((p) => p.children[1].textContent), ['Head of the household · Attested', 'Wife · Attested'], 'their place and the record\u2019s grade, in the locked terms');
  people[0].dispatch('click');
  assert.deepEqual(inspected, ['glessner_house'], 'a tap takes you to the house they live in');
  await nav4.select('home'); await nav4.select('people');
  assert.equal(reads, 1, 'and not read again');
}

// ---- T-2625: the HUD declutter — Start / Jaunts, the Confidence chip and caret, pace, theme
// and the menu leave the HUD; each lives in the Navigator ----------------------------------------
{
  const html = fs.readFileSync(path.join(ROOT, 'renderers/web/index.html'), 'utf8');
  const top = html.slice(html.indexOf('<div class="hud-top">'), html.indexOf('<div class="hud-moved"'));
  for (const id of ['btn-start', 'btn-confidence', 'btn-confidence-more', 'btn-pace', 'btn-theme', 'btn-help']) {
    assert(!top.includes(`id="${id}"`), `the HUD's top row no longer holds #${id}`);
  }
  const parked = html.slice(html.indexOf('<div class="hud-moved"'), html.indexOf('<div class="control-help"'));
  assert(/id="btn-start"/.test(parked) && /id="confidence-group"/.test(parked) && /id="cm-reset"/.test(parked), 'Start / Jaunts and the Confidence group wait for their apps');
  assert.equal((html.match(/id="btn-theme"/g) ?? []).length, 1);
  const settings = html.slice(html.indexOf('data-panel="settings"'), html.indexOf('</section>', html.indexOf('data-panel="settings"')));
  assert(/id="btn-theme"/.test(settings), 'light / dark lives in Settings');
  assert(!/id="btn-pace"/.test(html), 'the pace chip is gone; Move holds the pace');
  // The Confidence app takes the chip, caret and menu in as they are.
  const { default: conf } = await import('../renderers/web/js/apps/confidence.js');
  assert.equal(conf.launch, undefined, 'the Confidence app is a screen now, not a stub');
  const group = { parentElement: null };
  let clicked = 0, timer = null;
  const menu = { hidden: true };
  const doc = { createElement: () => ({ className: '', textContent: '' }),
    getElementById: (id) => ({ 'confidence-group': group, 'confidence-menu': menu, 'btn-confidence-more': { click: () => { clicked++; menu.hidden = false; } } }[id] ?? null),
    defaultView: { setTimeout: (fn) => { timer = fn; } } };
  const kids = [];
  const el = { ownerDocument: doc, hidden: false, append: (...c) => { for (const x of c) { kids.push(x); x.parentElement = el; } } };
  conf.mount(el);
  assert.equal(group.parentElement, el, 'the group moves into the app');
  conf.shown(el);
  assert.equal(clicked, 0, 'the menu opens after the opening click has finished');
  timer();
  assert.equal(clicked, 1); assert.equal(menu.hidden, false, 'opening the app shows the levels');
}

// ---- T-2619: the dock — closed, it shows the lamp, the label, the year and the icon of the
// app it opens to; one tap (or a swipe up) opens that last app at HALF -------------------
{
  assert.equal(dockYear({ target_date: '1904-07-01' }), '1904');
  assert.equal(dockYear({ id: '1835' }), '1835');
  assert.equal(dockYear({}), '');
  const pill = dockPill(390);
  assert.equal(pill.width, DOCK_PILL_PX);
  assert(pill.clear && pill.left >= JOYSTICK_CLEAR_PX && 390 - pill.right >= JOYSTICK_CLEAR_PX,
    `on a 390 px phone the pill (${pill.left}–${pill.right}) keeps the joystick corner clear`);
  for (const phone of [true, false]) {
    const label = phone ? 'phone' : 'desktop';
    const dom = miniDom();
    const head = dom.byId.get('nav-head');
    const add = (tag, id) => { const e = dom.doc.createElement(tag); e.id = id; head.append(e); return e; };
    add('span', 'nav-dock-app'); add('span', 'nav-dock-year');
    let t = 0;
    const calls = [];
    const nav = createNavigator({ root: dom.root, scene: { id: '1904', target_date: '1904-07-01' }, isPhone: () => phone,
      viewportHeight: () => 844, now: () => t, storage: fakeStorage(), apps: APPS,
      context: () => ({ scene: { id: '1904' }, hasPeople: false, actions: { map: () => calls.push('map') } }) });
    await Promise.resolve();
    let d = nav.snapshot().dock;
    assert.equal(nav.level, 0, `${label}: it starts closed`);
    assert.equal(d.year, '1904', `${label}: the closed device shows the year`);
    assert.equal(d.app, 'home', `${label}: and the app it opens to, Home at first`);
    assert.equal(d.label, 'Open the Navigator on Home');
    // Open another screen, then close it: the dock now opens to that one.
    assert.equal(await nav.select('jump'), true);
    nav.dock();
    d = nav.snapshot().dock;
    assert.equal(d.app, 'jump', `${label}: the dock remembers the last app`);
    assert.equal(d.label, 'Open the Navigator on Jump');
    assert.equal(dom.byId.get('nav-dock-app').dataset.app, 'jump');
    // A stub (Map) runs and docks the device; it is not an app the dock opens to.
    await nav.select('map');
    assert.deepEqual(calls, ['map']);
    assert.equal(nav.level, 0);
    assert.equal(nav.snapshot().dock.app, 'jump', `${label}: a stub leaves the dock on the last screen`);
    // One tap on the closed device opens that last app — at HALF on a phone.
    dom.byId.get(phone ? 'nav-grip' : 'nav-head').dispatch('click');
    assert.equal(nav.detent, phone ? 'half' : 'open', `${label}: one tap opens it`);
    assert.equal(nav.app, 'jump', `${label}: on the last app`);
    assert.equal(dom.byId.get('nav-grip').getAttribute('aria-label'), 'Lower the Navigator');
    nav.dock();
    if (phone) {
      // The pill's face (the head) opens it too, and so does a swipe up from it.
      head.dispatch('click');
      assert.equal(nav.detent, 'half', 'a tap on the pill opens it at HALF');
      nav.dock();
      t = 1000; head.dispatch('pointerdown', { pointerId: 7, clientY: 810 });
      t = 1040; head.dispatch('pointermove', { pointerId: 7, clientY: 760 });
      t = 1080; head.dispatch('pointermove', { pointerId: 7, clientY: 700 });
      head.dispatch('pointerup', { pointerId: 7, clientY: 700 });
      head.dispatch('click');
      assert.equal(nav.detent, 'half', 'a swipe up from the dock opens it at HALF');
      assert.equal(nav.app, 'jump');
    }
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
  // T-2619: the closed device's year and app icon, and the pill on a phone.
  assert.match(section, /id="nav-dock-app" aria-hidden="true"/);
  assert.match(section, /id="nav-dock-year" aria-hidden="true"/);
  assert.match(css, /--dock-w: 136px/, 'the pill is as wide as navigator.js says');
  assert.match(css, /\[data-detent="dock"\]:not\(\.is-dragging\) \{ left: calc\(50% - var\(--dock-w\) \/ 2\)/, 'the pill sits at the bottom centre');
  assert.match(html, /class="gate-code" aria-hidden="true"><span>NAVIGATOR MK II<\/span><span>SCR 01 · HOME<\/span>/,
    'the arrival device wears the screen code on its back face');
}

// ---- deep links and Back (T-2621) ------------------------------------------------------
{
  const dom = miniDom();
  const calls = [];
  const nav = createNavigator({ root: dom.root, scene: json('data/scenes/1904.json'), isPhone: () => false, storage: fakeStorage(),
    apps: APPS, viewportHeight: () => 780,
    context: () => ({ scene: { id: '1904' }, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false,
      actions: { inspect: (id) => calls.push(['card', id]), map: () => calls.push(['map']), jaunts: () => calls.push(['jaunts']) } }) });
  await Promise.resolve();
  const seen = [];
  const off = nav.onChange((s) => seen.push(s));
  assert.equal(nav.has('map'), true);
  assert.equal(await nav.openLink({ app: 'no-such-app' }), false, 'a link to an app the rail does not have is ignored');
  assert.deepEqual(calls, []);
  await nav.openLink({ app: 'map' });
  assert.deepEqual(calls.at(-1), ['map'], '?nav=map opens the Map');
  await nav.openLink({ app: 'jaunts' });
  // T-2620: Jaunts is a screen (the drawer's Go to, with Take a Jaunt), not a stub any more.
  assert.equal(nav.app, 'jaunts', '?nav=jaunts opens Jaunts');
  await nav.openLink({ app: 'inspect', id: 'glessner_house', tab: 'design' });
  assert.deepEqual(calls.at(-1), ['card', 'glessner_house'], '?nav=inspect:glessner_house opens that building (its card until the dossier lands)');
  assert.deepEqual(nav.link, { app: 'inspect', id: 'glessner_house', tab: 'design' }, 'the app reads its id and tab off ctx.link');
  await nav.openLink({ app: 'jump' });
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(nav.app, 'jump');
  assert.ok(nav.level > 0, 'a screen app opens the device');
  assert.ok(seen.some((x) => x.app === 'jump' && x.level > 0), 'onChange hears the open app');
  nav.closeApp();
  assert.equal(nav.app, 'home');
  assert.equal(nav.level, 0, 'closeApp: back to Home, docked — what Back does');
  assert.equal(nav.link, null);
  off();
}

// ---- the keyboard (T-2622, §14 Accessibility; QA-05, QA-19) ------------------------------
for (const phone of [false, true]) {
  const dom = miniDom();
  const keys = { fns: [], addEventListener(type, fn) { if (type === 'keydown') this.fns.push(fn); } };
  const press = (key, extra = {}) => {
    const e = { key, shiftKey: false, metaKey: false, ctrlKey: false, altKey: false, target: null, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; }, ...extra };
    for (const fn of keys.fns) fn(e);
    return e.defaultPrevented;
  };
  let active = true, escFree = true;
  const calls = [];
  const nav = createNavigator({ root: dom.root, scene: json('data/scenes/1904.json'), isPhone: () => phone, storage: fakeStorage(),
    apps: APPS, keyTarget: keys, keysActive: () => active, escFree: () => escFree, viewportHeight: () => 780,
    context: () => ({ scene: { id: '1904' }, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false,
      actions: { openSection: (id) => calls.push(['section', id]), jaunts: () => calls.push(['jaunts']), map: () => calls.push(['map']) } }) });
  await Promise.resolve();
  const where = phone ? 'phone' : 'desktop';
  const shut = nav.detent;
  const home = dom.byId.get('nav-home');
  const grip = dom.byId.get('nav-grip');

  active = false;
  assert.equal(press('n'), false, `${where}: no key works while the arrival is up`);
  assert.equal(nav.detent, shut);
  active = true;

  const f0 = home.focused;
  assert.equal(press('n'), true, `${where}: N is taken`);
  assert.equal(nav.level, 1, `${where}: N opens the Navigator`);
  assert.equal(home.focused, f0 + 1, `${where}: and focus moves into it`);
  assert.equal(press('N'), true);
  assert.equal(nav.level, 0, `${where}: N again closes it`);
  assert.equal(grip.focused > 0, true, `${where}: focus goes back to the grip, a visible place to stand`);

  assert.equal(press('n', { target: { tagName: 'INPUT' } }), false, `${where}: N in a text field is a letter`);
  assert.equal(nav.level, 0);
  assert.equal(press('n', { ctrlKey: true }), false, `${where}: Ctrl+N is the browser's`);

  assert.equal(press('Tab', { shiftKey: true }), false, `${where}: Shift+Tab is left alone`);
  assert.equal(press('Tab'), true, `${where}: Tab from the scene opens the Navigator`);
  assert.equal(nav.level, 1);
  assert.equal(press('Tab'), false, `${where}: with it open, Tab moves focus as Tab does`);

  // 1–9: the rail's apps in the order they show.
  const order = nav.apps;
  const jumpAt = order.indexOf('jump') + 1;
  assert.ok(jumpAt >= 1 && jumpAt <= 9, `${where}: Jump is within reach of a digit (${order.join(', ')})`);
  assert.equal(press(String(jumpAt)), true);
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(nav.app, 'jump', `${where}: ${jumpAt} opens the ${jumpAt}th app, Jump`);
  assert.ok(dom.byId.get('nav-app-jump')?.focused >= 1, `${where}: focus moves into the app's screen`);
  if (order.length < 9) assert.equal(press('9'), false, `${where}: a digit with no app behind it is not taken`);
  // T-2620 made Move a screen; Map is still a launch (it opens the whole field).
  const mapAt = order.indexOf('map') + 1;
  press(String(mapAt));
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(calls.at(-1), ['map'], `${where}: a digit runs a launch app (Map opens the whole field)`);

  // Escape closes it — at once when nothing else is waiting for it.
  nav.open();
  escFree = false;
  assert.equal(press('Escape'), false, `${where}: Escape goes to the drawer or a card first`);
  assert.equal(nav.level, 1);
  escFree = true;
  assert.equal(press('Escape'), true);
  assert.equal(nav.level, 0, `${where}: Escape closes the Navigator`);
  assert.equal(press('Escape'), false, `${where}: a closed Navigator leaves Escape alone`);
}

console.log('NAVIGATOR KEYS PASS — N and Tab-from-the-scene toggle it, 1–9 open the rail\'s apps, Escape closes it; focus moves into the app and back to the grip; nothing fires while typing or before landing');

console.log('NAVIGATOR PASS — the probe looks only when asked and moved, each asker within its own distance (Home 100 m); the street at the 1904 spawn is Prairie & Eighteenth; '
  + 'DOCK, HALF and FULL by tap, drag and flick, the desktop panel to its rail; Home paints the place, the target, the Jaunt, Move and the Confidence view; the rail opens the drawer’s sections');
