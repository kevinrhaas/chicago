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
import { install as installDrawerHost, SECTION_HOME, APP_SECTIONS, goToPick } from '../renderers/web/js/apps/drawer-host.js';
import * as mapView from '../renderers/web/js/apps/map-view.js';
import { createTargetTag, tagWords, DWELL_MS, TAG_WITHIN_M, HOLD_MS, FADE_MS, TAG_PLACES, TAG_HOLDS, normalTagPlace, normalTagHold, addressKey, sameAddress } from '../renderers/web/js/target-tag.js';

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

// T-2723: with pickAsync, a moving eye's look is heard when its answer lands, never waited for.
{
  let pose = { e: 0, n: 0, bearingDeg: 0, pitchDeg: 0 };
  let now = 0, asks = 0;
  const pending = [];
  const at = (id, distance = 10) => ({ id, record: {}, distance });
  const t = createTarget({ pick: () => { now += 1; return at('asked_now'); }, pose: () => pose,
    pickAsync: () => { asks++; return new Promise((res, rej) => pending.push({ res, rej })); } });
  const settle = () => new Promise((r) => setTimeout(r, 0));
  const heard = [];
  t.on((next) => heard.push(next?.id ?? null));
  t.tick(1000);
  assert.equal(asks, 1); assert.equal(now, 0, 'the tick asks the GPU later, not now');
  assert.deepEqual(heard, [], 'nothing is heard before the answer lands');
  pose = { ...pose, e: 5 };
  t.tick(2000);
  assert.equal(asks, 1, 'one look in flight at a time');
  pending.shift().res(at('keith_house'));
  await settle();
  assert.deepEqual(heard, ['keith_house'], 'the answer is heard when it lands');
  t.tick(3000);
  assert.equal(asks, 2, 'and the eye that moved meanwhile is looked through again');
  t.invalidate();
  pending.shift().res(at('stale_house'));
  await settle();
  assert.deepEqual(heard, ['keith_house'], 'an answer overtaken by invalidate() is dropped');
  t.tick(3001);
  assert.equal(asks, 3, 'and the told eye looks again');
  t.invalidate();
  assert.equal(t.current().id, 'asked_now', 'current() after invalidate() answers at once');
  assert.equal(now, 1);
  pending.shift().res(at('late_house'));
  await settle();
  assert.equal(t.current().id, 'asked_now', 'an answer older than an asked one is dropped');
  pose = { ...pose, e: 9 };
  assert.equal(t.current().id, 'asked_now', 'a moved eye asked current() keeps its last answer…');
  assert.equal(asks, 4, '…and looks again later');
  pending.shift().rej(new Error('context lost'));
  await settle();
  assert.equal(t.current(), null, 'a failed read is nothing in front of you, not a crash');
  pose = { ...pose, e: 20 };
  t.tick(9000);
  assert.equal(asks, 5, 'and the look after it still goes');
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
  const onPrairie = where.at(mid[0], mid[1]);
  assert.equal(onPrairie?.mode, 'on', JSON.stringify(onPrairie));
  assert.equal(onPrairie.place, 'Prairie Avenue');
  // T-2741: and the lot beside you gives the period house number.
  assert.match(onPrairie.address, /^1[67]\d\d(–1[67]\d\d)? Prairie Avenue$/, onPrairie.address);
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
      // A string is a text node in the DOM (Element.append); this fake keeps elements only.
      append(...cs) { for (const c of cs) { if (typeof c === 'string') continue; c.parent?.children.splice(c.parent.children.indexOf(c), 1); c.parent = el; el.children.push(c); } },
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
  add(head, 'button', 'nav-close');
  const navBody = add(root, 'div', null, ['nav-body']);
  const rail = add(navBody, 'nav', 'nav-rail');
  add(rail, 'button', 'nav-collapse');
  const home = add(navBody, 'div', 'nav-home', ['nav-screen']);
  for (const id of ['nav-home-title', 'nav-where', 'nav-where-detail', 'nav-front-name', 'nav-front-detail', 'nav-inspect',
    'nav-jaunt', 'nav-jaunt-step', 'nav-jaunt-title', 'nav-jaunt-bar', 'nav-move', 'nav-confidence']) add(home, 'div', id);
  for (const id of ['nav-tile-move', 'nav-tile-confidence']) add(home, 'button', id);
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
      actions: { openSection: (id) => calls.push(['section', id]), jaunts: () => calls.push(['jaunts']), inspect: (id) => calls.push(['card', id]),
        jauntList: () => calls.push(['jaunt-list']), gotoList: () => calls.push(['goto-list']), freeRoam: () => calls.push(['roam']),
        map: () => calls.push(['map']) } }),
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
  assert.deepEqual(calls.at(-1), ['inspect', 'glessner_house'], `${label}: Inspect opens the building`);
  // T-3022: the building opens in Inspect, inside the device, so a phone's sheet stays up.
  if (phone) assert.notEqual(nav.detent, 'dock', 'phone: the Inspect key leaves the sheet up');

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
  // T-3021: Home's MOVE tile opens Move, and Back from it returns to the app it came from.
  dom.byId.get('nav-tile-move').dispatch('click');
  await Promise.resolve();
  assert.equal(nav.app, 'move', `${label}: Home's Move tile opens Move`);
  assert.equal(nav.backTo().id, 'home', 'and Back goes to Home, where it was opened from');
  await nav.back();
  assert.equal(nav.app, 'home', `${label}: Back returns to Home`);
  await nav.select('guide');
  assert.deepEqual([fakeHud.open, fakeHud.tab], [true, 'controls'], 'Guide opens Controls first');
  nav.dock();
  assert.equal(fakeHud.open, false, 'docking closes it');
  nav.open(1);
  assert.equal(fakeHud.open, true, 'and opening again brings it back');
  // Go to is not a section: it is the Jaunts app's own segment (T-2630), and the drawer's
  // Go to list retires with the drawer (T-2620).
  assert.equal(SECTION_HOME.goto, undefined, 'no app holds the drawer\u2019s Go to list');

  // The HUD's own calls keep their meaning through the adapter (hud.setPanel / selectTab).
  const goTos = [];
  fakeHud.tab = 'goto';
  const adapter = installDrawerHost({ hud: fakeHud, navigator: nav, doc: dom.doc, openGoTo: () => goTos.push('goto') });
  assert.equal(fakeHud.tab, 'controls', 'the HUD\u2019s opening section moves off the retired Go to');
  assert.equal(dom.panel.children[0].children.find((t) => t.dataset.tab === 'goto').hidden, true, 'Go to\u2019s tab leaves the row for good');
  adapter.open('goto');
  assert.deepEqual(goTos, ['goto'], 'asking for Go to opens the Jaunts app\u2019s Go to');
  // A pick in that Go to, in the town, goes there (goToTarget) and pockets the device; the
  // gate is shut, so enterWorld (the way in) would refuse it. From the gate, a pick enters.
  {
    const log = [];
    let town = true;
    const pick = goToPick({ inTown: () => town, goTo: (t) => { log.push(['go', t.id]); return t.id !== 'nowhere'; },
      enterWorld: (t) => { log.push(['enter', t?.id ?? null]); return true; }, dock: () => log.push(['dock']), entered: () => log.push(['entered']) });
    assert.equal(pick({ kind: 'business', id: 'biz_p_f_peck' }), true, 'in the town a Go to pick goes there');
    assert.deepEqual(log, [['go', 'biz_p_f_peck'], ['dock']], 'through goToTarget, never enterWorld, and the device docks');
    log.length = 0;
    assert.equal(pick({ kind: 'structure', id: 'nowhere' }), false, 'a pick goToTarget refuses is refused');
    assert.deepEqual(log, [['go', 'nowhere']], 'and the device stays open on the list');
    log.length = 0;
    assert.equal(pick(null), false, 'no target, no move');
    town = false; log.length = 0;
    assert.equal(pick({ kind: 'anchor', id: 'lake_at_canal' }), true);
    assert.deepEqual(log, [['enter', 'lake_at_canal'], ['entered']], 'from the gate a pick is the way in');
  }
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
  // T-2630: Jaunts is a real screen now — three segments, Jaunts first, its list asked for.
  nav.open(1);
  await nav.select('jaunts');
  const jaunts = dom.byId.get('nav-app-jaunts');
  assert(jaunts && !jaunts.hidden, 'Jaunts opens in its own screen');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 02 · JAUNTS');
  const segs = jaunts.children[0];
  assert.equal(segs.getAttribute('role'), 'tablist');
  assert.deepEqual(segs.children.map((b) => b.textContent), ['Jaunts', 'Go to', 'Free roam'], 'Jaunts · Go to · Free roam');
  assert.deepEqual(segs.children.map((b) => b.getAttribute('aria-selected')), ['true', 'false', 'false']);
  assert.deepEqual(calls.at(-1), ['jaunt-list'], 'the Jaunts segment asks for the Jaunts list');
  segs.children[1].dispatch('click');
  assert.deepEqual(calls.at(-1), ['goto-list'], 'Go to asks for the search');
  assert.equal(jaunts.children[2].hidden, false, 'and shows its panel');
  segs.children[2].dispatch('click');
  const roamKey = jaunts.children[3].children.find((c) => c.className.split(' ').includes('nav-roam'));
  roamKey.dispatch('click');
  assert.deepEqual(calls.at(-1), ['roam'], 'Free roam pockets the device');

  // Jump is a real, lazy screen: loaded on first open, with HERE on this scene and the Recall key.
  nav.open(1);
  await nav.select('jump');
  const jump = dom.byId.get('nav-app-jump');
  assert(jump && !jump.hidden, 'Jump opens in its own screen');
  assert.equal(dom.byId.get('nav-code').textContent, 'SCR 08 · JUMP');
  const cards = jump.children[0].children;
  // T-2655: all three destinations, in the Observatory's order (1812 is a link too).
  assert.deepEqual(cards.map((c) => c.tagName), ['A', 'DIV', 'A'], '1835 and 1812 are links, 1904 (here) is not');
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
  // Go to is the Jaunts app's own (T-2630); the drawer's Go to list retired with it (T-2620).
  assert.deepEqual(Object.keys(SECTION_HOME).sort(), ['businesses', 'controls', 'evidence', 'people', 'settings', 'travel', 'whatsnew']);
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
  // T-3253: every Blue Book household is a block of its own; the Glessners' is one of them.
  assert(screen.children.length >= 60, `1904: ${screen.children.length} households`);
  const block = screen.children.find((b) => b.children[1]?.textContent === 'The Glessner household at 1800 Prairie Avenue');
  assert(block, 'the Glessner household has its block');
  const people = block.children.filter((c) => c.classList.contains('nav-person'));
  // T-3258: the family first, then the staff (Mattie Williamson and the five the 1900 census names), by name.
  assert.deepEqual(people.map((p) => p.children[0].textContent), ['John J. Glessner', 'Frances M. Glessner', 'August Billings',
    'Charles Nelson', 'Christine Nelson', 'Kate Ryan', 'Martha L. (Mattie) Williamson', 'Mary Reynolds'], 'the head first, the staff last');
  assert.deepEqual(people.map((p) => p.children[1].textContent).filter((s, i) => [0, 1, 6, 7].includes(i)),
    ['Head of the household · Attested', 'Wife · Attested', 'Servant · Attested', 'Servant · Inferred'], 'their place and the record\u2019s grade, in the locked terms');
  people[0].dispatch('click');
  assert.deepEqual(inspected, ['glessner_house'], 'a tap takes you to the house they live in');
  await nav4.select('home'); await nav4.select('people');
  assert.equal(reads, 1, 'and not read again');
}

// ---- T-2627: the HUD's target tag — 400 ms of rest on a building, then its name and distance;
// a tap (or the quick column's Inspect key) opens Inspect --------------------------------------
{
  assert.equal(DWELL_MS, 400); assert.equal(TAG_WITHIN_M, 40);
  const glessner = { id: 'glessner_house', record: { id: 'glessner_house', sidecar: { name: 'Glessner House' } }, distance: 11.6 };
  assert.equal(tagWords(glessner), 'Glessner House · 38 ft');
  assert.equal(tagWords({ id: 'keith_house_1808_prairie', record: {}, distance: 20 }).includes('_'), false, 'no snake_case in the tag');
  let clock = 0;
  const timers = [];
  const wait = (fn, ms) => { const t = { at: clock + ms, fn, live: true }; timers.push(t); return t; };
  const cancel = (t) => { t.live = false; };
  const advance = (ms) => { clock += ms; for (const t of timers.filter((x) => x.live && x.at <= clock)) { t.live = false; t.fn(); } };
  let hear = null, within = null, now = null;
  const target = { on: (fn, o) => { hear = fn; within = o.within; return () => { hear = null; }; }, current: () => now };
  const el = () => { const ls = {}; return { hidden: true, textContent: '', attrs: {}, setAttribute(k, v) { this.attrs[k] = v; },
    addEventListener(t, fn) { ls[t] = fn; }, click() { ls.click?.(); } }; };
  const tagEl = el(), keyEl = el();
  const opened = [];
  const tag = createTargetTag({ target, tagEl, keyEl, wait, cancel, onInspect: (t) => opened.push(t.id) });
  assert.equal(within, 40, 'the tag listens within the Inspect distance');
  now = glessner; hear(glessner);
  advance(399);
  assert.equal(tagEl.hidden, true, 'nothing before the dwell');
  advance(1);
  assert.equal(tagEl.hidden, false, 'after 400 ms of rest the tag shows');
  assert.equal(tagEl.textContent, 'Glessner House · 38 ft');
  assert.equal(keyEl.hidden, false, 'and the quick column offers Inspect');
  tagEl.click(); keyEl.click();
  assert.deepEqual(opened, ['glessner_house', 'glessner_house'], 'a tap on the tag or the key opens Inspect on it');
  // A glance away hides it at once; a glance past a building shows nothing.
  now = null; hear(null);
  assert.equal(tagEl.hidden, true); assert.equal(keyEl.hidden, true);
  const other = { id: 'keith_house', record: { sidecar: { name: 'Keith House' } }, distance: 20 };
  now = other; hear(other); advance(200);
  now = null; hear(null); advance(400);
  assert.equal(tagEl.hidden, true, 'a building passed in under 400 ms never shows');
  // Out of the town (Home, a menu) it never shows, and coming back reads the probe again.
  now = glessner; hear(glessner); advance(400);
  tag.setEnabled(false);
  assert.equal(tagEl.hidden, true);
  hear(other); advance(400);
  assert.equal(tagEl.hidden, true, 'disabled, nothing shows');
  tag.setEnabled(true); advance(400);
  assert.equal(tagEl.textContent, 'Glessner House · 38 ft', 'back in the town, the dwell runs on what is in front');
  assert.equal(tag.current.id, 'glessner_house');
}

// ---- T-2736: the target tag is a glance, not a sign — it holds, fades, and stays gone for that
// building until the reticle leaves it; the Inspect key stays while the building is in front ------
{
  assert.equal(HOLD_MS, 3000); assert.equal(FADE_MS, 600);
  let clock = 0;
  const timers = [];
  const wait = (fn, ms) => { const t = { at: clock + ms, fn, live: true }; timers.push(t); return t; };
  const cancel = (t) => { t.live = false; };
  const advance = (ms) => { const end = clock + ms; for (;;) {
    const due = timers.filter((x) => x.live && x.at <= end).sort((a, b) => a.at - b.at)[0];
    if (!due) break; clock = due.at; due.live = false; due.fn(); } clock = end; };
  let hear = null, now = null;
  const target = { on: (fn) => { hear = fn; return () => { hear = null; }; }, current: () => now };
  const el = () => { const cls = new Set(); return { hidden: true, textContent: '', setAttribute() {}, addEventListener() {},
    classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c) } }; };
  const tagEl = el(), keyEl = el();
  createTargetTag({ target, tagEl, keyEl, wait, cancel });
  const glessner = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 11.6 };
  now = glessner; hear(glessner); advance(DWELL_MS);
  assert.equal(tagEl.hidden, false, 'shown after the dwell');
  advance(HOLD_MS - 1);
  assert.equal(tagEl.classList.contains('is-fading'), false, 'held, not yet fading');
  advance(1);
  assert.equal(tagEl.classList.contains('is-fading'), true, 'then it fades');
  assert.equal(tagEl.hidden, false, 'still in the page while it fades');
  advance(FADE_MS);
  assert.equal(tagEl.hidden, true, 'and is gone once faded');
  assert.equal(tagEl.classList.contains('is-fading'), false);
  assert.equal(keyEl.hidden, false, 'Inspect stays one tap away while the building is in front');
  // The probe re-answering the same building (a step closer, back from a menu) does not bring it back.
  hear({ ...glessner, distance: 9 }); advance(HOLD_MS + FADE_MS);
  assert.equal(tagEl.hidden, true, 'gone for that building until the reticle leaves it');
  // Looking away and back shows it again, for another glance.
  now = null; hear(null);
  assert.equal(keyEl.hidden, true);
  now = glessner; hear(glessner); advance(DWELL_MS);
  assert.equal(tagEl.hidden, false, 'looking back shows it again');
  advance(HOLD_MS + FADE_MS);
  assert.equal(tagEl.hidden, true, 'and it fades again');
  // A new building mid-fade starts its own dwell and its own hold.
  now = null; hear(null); now = glessner; hear(glessner); advance(DWELL_MS + HOLD_MS + 100);
  assert.equal(tagEl.classList.contains('is-fading'), true);
  const keith = { id: 'keith_house', record: { sidecar: { name: 'Keith House' } }, distance: 20 };
  now = keith; hear(keith);
  assert.equal(tagEl.hidden, true, 'a new building hides the fading tag at once');
  assert.equal(tagEl.classList.contains('is-fading'), false);
  advance(DWELL_MS);
  assert.equal(tagEl.hidden, false); assert.equal(tagEl.textContent, 'Keith House · 66 ft');
  advance(HOLD_MS - 1);
  assert.equal(tagEl.hidden, false, 'with a full hold of its own');
}

// ---- T-2736 (owner, 2026-10-17): Settings › Show turns the tag off; on by default; the Inspect
// key stays either way ------------------------------------------------------------------------
{
  let clock = 0;
  const timers = [];
  const wait = (fn, ms) => { const t = { at: clock + ms, fn, live: true }; timers.push(t); return t; };
  const cancel = (t) => { t.live = false; };
  const advance = (ms) => { clock += ms; for (const t of timers.filter((x) => x.live && x.at <= clock)) { t.live = false; t.fn(); } };
  let hear = null, now = null;
  const target = { on: (fn) => { hear = fn; return () => {}; }, current: () => now };
  const el = () => ({ hidden: true, textContent: '', setAttribute() {}, addEventListener() {} });
  const glessner = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 11.6 };
  const keith = { id: 'keith_house', record: { sidecar: { name: 'Keith House' } }, distance: 20 };
  const tagEl = el(), keyEl = el();
  const tag = createTargetTag({ target, tagEl, keyEl, wait, cancel });
  now = glessner; hear(glessner); advance(DWELL_MS);
  assert.equal(tagEl.hidden, false, 'on by default');
  tag.setTagShown(false);
  assert.equal(tagEl.hidden, true, 'turned off, a showing tag goes at once');
  assert.equal(keyEl.hidden, false, 'the Inspect key stays');
  now = keith; hear(keith); advance(DWELL_MS);
  assert.equal(tagEl.hidden, true, 'and no new building shows one');
  assert.equal(keyEl.hidden, false);
  tag.setTagShown(true);
  now = null; hear(null); now = glessner; hear(glessner); advance(DWELL_MS);
  assert.equal(tagEl.hidden, false, 'turned back on, the next look shows it');
  const offEl = el();
  createTargetTag({ target: { on: (fn) => { hear = fn; return () => {}; }, current: () => now }, tagEl: offEl, keyEl: el(), wait, cancel, tagShown: false });
  now = keith; hear(keith); advance(DWELL_MS);
  assert.equal(offEl.hidden, true, 'a visitor who turned it off never sees it after a reload');
}

// ---- T-2942 (owner, 2026-10-20): the tag docks on the right under the address by default,
// moves to the centre or the bottom, fades by default or stays, and never repeats the address --
{
  assert.deepEqual(TAG_PLACES, ['right', 'centre', 'bottom'], 'right is the default place');
  assert.deepEqual(TAG_HOLDS, ['fade', 'always'], 'fading is the default');
  assert.equal(normalTagPlace(undefined), 'right'); assert.equal(normalTagPlace('bottom'), 'bottom'); assert.equal(normalTagPlace('x'), 'right');
  assert.equal(normalTagHold(undefined), 'fade'); assert.equal(normalTagHold('always'), 'always');
  assert.equal(addressKey('1800 S. Prairie Ave.'), addressKey('1800 Prairie Avenue'));
  assert.ok(sameAddress('1800 Prairie Avenue', ['1800 Prairie Avenue', '1800 S Prairie Ave']));
  assert.ok(sameAddress('1801 Prairie Avenue', ['Prairie Avenue', '1801 S Prairie Ave']), 'today\'s spelling counts too');
  assert.ok(sameAddress('2100 Prairie Avenue — Sherman Victorian Gothic', ['2100 Prairie Avenue']), 'a name led by the address');
  assert.equal(sameAddress('Glessner House', ['1800 Prairie Avenue']), false, 'a real name is not the address');
  assert.equal(sameAddress('1801 Prairie Avenue', ['1800 Prairie Avenue']), false, 'the house across the way is another address');
  assert.equal(sameAddress('Prairie Avenue', ['Prairie Avenue']), false, 'a street alone is not a house\'s address');

  let clock = 0;
  const timers = [];
  const wait = (fn, ms) => { const t = { at: clock + ms, fn, live: true }; timers.push(t); return t; };
  const cancel = (t) => { t.live = false; };
  const advance = (ms) => { const end = clock + ms; for (;;) {
    const due = timers.filter((x) => x.live && x.at <= end).sort((a, b) => a.at - b.at)[0];
    if (!due) break; clock = due.at; due.live = false; due.fn(); } clock = end; };
  let hear = null, now = null;
  const target = { on: (fn) => { hear = fn; return () => {}; }, current: () => now };
  // A parent that records what is put in it, and an element that knows its parent.
  const parent = (name) => ({ name, kids: [], insertBefore(el, before) {
    if (el.parentNode) el.parentNode.kids = el.parentNode.kids.filter((k) => k !== el);
    const at = before ? this.kids.indexOf(before) : -1;
    if (at < 0) this.kids.push(el); else this.kids.splice(at, 0, el);
    el.parentNode = this; } });
  const el = () => { const cls = new Set(); return { hidden: true, textContent: '', dataset: {}, parentNode: null, get nextSibling() {
    const k = this.parentNode?.kids ?? []; return k[k.indexOf(this) + 1] ?? null; }, setAttribute() {}, addEventListener() {},
    classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c) } }; };
  const right = parent('right'), centre = parent('centre'), bottom = parent('bottom');
  const hint = el(); bottom.insertBefore(hint, null);
  const tagEl = el(), keyEl = el();
  centre.insertBefore(tagEl, null);
  let card = ['1800 Prairie Avenue', '1800 S Prairie Ave'];
  const tag = createTargetTag({ target, tagEl, keyEl, wait, cancel, addresses: () => card, place: 'right', holdMode: 'fade',
    slots: { right: { parent: right }, centre: { parent: centre }, bottom: { parent: bottom, before: hint } } });
  assert.equal(tag.place, 'right'); assert.equal(tag.hold, 'fade');
  assert.equal(tagEl.parentNode, right, 'by default the tag stands in the right-hand column');
  assert.equal(tagEl.dataset.place, 'right');
  const glessner = { id: 'glessner_house', record: { sidecar: { name: 'Glessner House' } }, distance: 11.6 };
  const numbered = { id: 'house_1800', record: { sidecar: { name: '1800 Prairie Avenue' } }, distance: 8 };
  now = glessner; hear(glessner); advance(DWELL_MS);
  assert.equal(tagEl.hidden, false, 'docked, a named building shows');
  assert.equal(tagEl.textContent, 'Glessner House · 38 ft');
  advance(HOLD_MS - 1);
  assert.equal(tagEl.classList.contains('is-fading'), false, 'the choice of fading does not shorten the hold');
  advance(1 + FADE_MS);
  assert.equal(tagEl.hidden, true, 'and fades by default');
  // A building named by the very address the card shows: docked, the tag would repeat it.
  now = numbered; hear(numbered); advance(DWELL_MS);
  assert.equal(tagEl.hidden, true, 'docked, a name that only repeats the card\'s address is not shown');
  assert.equal(keyEl.hidden, false, 'the Inspect key still offers it');
  card = ['1700 Prairie Avenue'];
  hear({ ...numbered, distance: 9 });
  assert.equal(tagEl.hidden, false, 'once the card names another address, the tag says the house\'s');
  card = ['1800 Prairie Avenue'];
  // Centre and bottom keep the name whatever the card says.
  tag.setPlace('centre');
  assert.equal(tagEl.parentNode, centre); assert.equal(tagEl.dataset.place, 'centre');
  assert.equal(tagEl.hidden, false, 'in the centre the full name shows, as it always did');
  tag.setPlace('bottom');
  assert.equal(tagEl.parentNode, bottom); assert.equal(bottom.kids[0], tagEl, 'at the bottom it stands above the hint');
  assert.equal(tagEl.hidden, false);
  // Always shown: no fade, for as long as the building is in the reticle; a new one replaces it.
  tag.setHold('always');
  now = glessner; hear(glessner); advance(DWELL_MS + HOLD_MS * 5);
  assert.equal(tagEl.hidden, false, 'always shown does not fade');
  assert.equal(tagEl.classList.contains('is-fading'), false);
  now = null; hear(null);
  assert.equal(tagEl.hidden, true, 'it still goes when the reticle leaves the building');
  // Back to fading: a tag already spent comes back when the choice changes, then fades again.
  now = glessner; hear(glessner); advance(DWELL_MS);
  tag.setHold('fade');
  assert.equal(tagEl.hidden, false);
  advance(HOLD_MS + FADE_MS);
  assert.equal(tagEl.hidden, true, 'fading again');
  tag.setPlace('right');
  assert.equal(tagEl.parentNode, right);
  assert.equal(tagEl.hidden, false, 'moving it shows it afresh where it now stands');
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
      context: () => ({ scene: { id: '1904' }, hasPeople: false, actions: { openSection: (section) => calls.push(section) } }) });
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
    // A stub runs and docks the device; it is not an app the dock opens to. (Map, Jaunts,
    // the Confidence view and Settings were the stub here until each became a screen:
    // T-2654, T-2630, T-2647, and T-2620's Settings, which holds the drawer's Settings and
    // What's new. With none left on the rail, the test brings its own.)
    nav.register({ id: 'stub', label: 'Stub', code: 'SCR 99', order: 95, icon: '<svg></svg>', launch: () => { calls.push('stub'); } });
    await nav.select('stub');
    assert.deepEqual(calls, ['stub']);
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

// ---- T-2640: Show me — the camera turns to a Look for feature, only along a camera the
// building's summary record names; 900 ms ease-in-out, a cut with reduced motion ----------------
{
  const sm = await import('../renderers/web/js/show-me.js');
  const glessner = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/summaries/glessner_house.json'), 'utf8'));
  // A square house 20 m a side, centred at (100, 50).
  const house = [[90, 40], [110, 40], [110, 60], [90, 60]];
  assert.equal(sm.cameraOf({ text: 'x' }), null, 'no camera named, nothing to aim at');
  assert.equal(sm.cameraOf({ camera: { yaw: 10 } }), null);
  assert.deepEqual(sm.cameraOf({ camera: { yaw: -90, pitch: 5 } }), { yaw: 270, pitch: 5 });
  assert.equal(sm.plan(glessner.lookFor[0], null), null, 'no footprint, no stand: never a guess');
  for (const item of glessner.lookFor) {
    const p = sm.plan(item, house);
    assert(p, `${item.feature}: the record's camera gives a stand`);
    // The stand looks along the record's bearing through the house's centre.
    const back = Math.atan2(100 - p.e, 50 - p.n) * 180 / Math.PI;
    assert(Math.abs(sm.turnBy(back, item.camera.yaw)) < 1e-6, `${item.feature}: faces the house along yaw ${item.camera.yaw}`);
    assert.equal(p.pitch, item.camera.pitch);
    assert(Math.hypot(p.e - 100, p.n - 50) >= 10 + sm.STAND_CLEAR_M - 0.5 && !sm.inside([p.e, p.n], house), 'and stands clear of its wall');
  }
  // A stand inside another building steps back; with nowhere clear, Show me is refused.
  const blockedNear = (e, n) => Math.hypot(e - 100, n - 50) < 40;
  assert(Math.hypot(...(({ e, n }) => [e - 100, n - 50])(sm.plan(glessner.lookFor[1], house, { blocked: blockedNear }))) >= 40);
  assert.equal(sm.plan(glessner.lookFor[1], house, { blocked: () => true }), null);
  // Another building on the line of sight hides the feature from every stand behind it: refused.
  const across = [[95, 72], [105, 72], [105, 80], [95, 80]]; // north of the house, across the street
  assert.equal(sm.plan(glessner.lookFor[1], house, { sighted: (e, n, we, wn) => !sm.crosses([e, n], [we, wn], [across]) }), null);
  assert.equal(sm.crosses([100, 100], [100, 60], [across]), true);
  assert.equal(sm.crosses([120, 100], [120, 60], [across]), false);
  const aside = sm.plan(glessner.lookFor[1], house, { sighted: (e, n, we, wn) => !sm.crosses([e, n], [we, wn], [[[130, 72], [140, 72], [140, 80], [130, 80]]]) });
  assert(aside && aside.n < 80, 'a building off the line changes nothing');
  assert.equal(sm.plan(glessner.lookFor[1], house, { sighted: () => false }), null, 'no spot that sees it: refused, not guessed');
  // A house round a courtyard has its centre outside its walls: the stand is still outside
  // the far wall, not in the yard.
  const ring = [[0, 0], [40, 0], [40, 40], [0, 40], [0, 30], [30, 30], [30, 10], [0, 10]]; // a C open to the west
  const cp = sm.plan({ feature: 'x', camera: { yaw: 270, pitch: 5 } }, ring);
  assert(cp.e > 40 && !sm.inside([cp.e, cp.n], ring), `the stand clears the far (east) wall (${cp.e.toFixed(1)}, ${cp.n.toFixed(1)})`);
  assert.equal(sm.turnBy(350, 10), 20); assert.equal(sm.turnBy(10, 350), -20);
  assert.equal(sm.easeInOut(0), 0); assert.equal(sm.easeInOut(1), 1); assert(Math.abs(sm.easeInOut(0.5) - 0.5) < 1e-9);

  for (const reduced of [false, true]) {
    let clock = 0;
    const frames = [], timers = [];
    let at = { e: 0, n: 0, yaw: 300, pitch: 0, flying: true };
    const placed = [], outlines = [];
    let landed = 0;
    const run = sm.createShowMe({ pose: () => at, place: (q) => { placed.push(q); at = { ...at, ...q }; },
      land: () => { landed++; at.flying = false; }, outline: (o) => outlines.push(o), reduced: () => reduced,
      frame: (fn) => frames.push(fn), wait: (fn, ms) => timers.push({ fn, ms }), now: () => clock });
    const target = sm.plan(glessner.lookFor[1], house);
    const done = run.show(target);
    assert.equal(landed, 1, 'flying, it comes down to the viewpoint first');
    if (!reduced) {
      while (frames.length) { clock += 100; frames.shift()(); }
      assert(placed.length >= 9, 'a glide over about 900 ms');
      assert.equal(clock >= sm.TURN_MS, true);
    } else {
      assert.equal(placed.length, 1, 'reduced motion: one cut, no glide');
    }
    assert.equal(await done, true);
    assert.deepEqual([at.e, at.n, at.yaw, at.pitch], [target.e, target.n, target.yaw, target.pitch], 'and it ends exactly on the record’s view');
    assert.deepEqual(outlines.at(-1), { on: true, pulse: !reduced }, reduced ? 'the outline shows, still' : 'the outline pulses');
    assert.equal(timers.at(-1).ms, sm.PULSE_MS, 'for 2 s');
    timers.at(-1).fn();
    assert.deepEqual(outlines.at(-1), { on: false, pulse: false });
    assert.equal(run.last.cut, reduced);
  }
  assert.equal(await sm.createShowMe({ pose: () => ({}), place: () => {} }).show(null), false, 'no plan, nothing moves');
  // The 2 s count from when the outline is drawn (a slow frame must not find it already
  // off), and a new Show me puts the last outline away first.
  {
    let drawnNow = null;
    const seen = [], waits = [];
    const late = sm.createShowMe({ pose: () => ({ e: 0, n: 0, yaw: 0, pitch: 0 }), place: () => {}, reduced: () => true,
      outline: (o) => { seen.push(o); return o.on ? new Promise((r) => { drawnNow = r; }) : undefined; },
      wait: (fn, ms) => waits.push({ fn, ms }) });
    await late.show(sm.plan(glessner.lookFor[0], house));
    assert.deepEqual(seen[0], { on: false, pulse: false }, 'the last outline is put away first');
    await Promise.resolve();
    assert.equal(waits.length, 0, 'no 2 s countdown before the outline is drawn');
    drawnNow(); await Promise.resolve(); await Promise.resolve();
    assert.equal(waits.length, 1); assert.equal(waits[0].ms, sm.PULSE_MS, 'it starts when the outline is drawn');
  }

  // Inspect draws Show me only on Look for items whose record names a camera.
  const view = fs.readFileSync(path.join(ROOT, 'renderers/web/js/apps/inspect-view.js'), 'utf8');
  assert.match(view, /if \(cameraOf\(l\) && ctx\.actions\?\.showMe\)/);
}

// ---- T-2654: the Map app — the whole field in the device, tap a building to preview, Go;
// the active Jaunt dotted; a legend in the Confidence view colours -----------------------------
{
  const { inside, hitBuilding, fitField, nearView, buildingName, centroid, NEAR_K } = mapView;
  const sq = (e, n, s, id, grade) => Object.assign([[e - s, n - s], [e + s, n - s], [e + s, n + s], [e - s, n + s]], { id, grade });
  const yard = sq(0, 0, 30, 'yard', 'inferred'), shed = sq(5, 5, 4, 'shed', 'reconstructed'), far = sq(100, 0, 5, 'far', 'attested');
  assert.equal(inside([0, 0], yard), true); assert.equal(inside([40, 0], yard), false);
  assert.equal(hitBuilding([yard, shed, far], 5, 5)?.id, 'shed', 'the smallest footprint under the tap wins');
  assert.equal(hitBuilding([yard, shed, far], -20, -20)?.id, 'yard');
  assert.equal(hitBuilding([yard, shed, far], 108, 0, 10)?.id, 'far', 'a near miss finds the nearest house');
  assert.equal(hitBuilding([yard, shed, far], 300, 300), null);
  assert.deepEqual(centroid(far), [100, 0]);
  const field = { eMin: -1000, eMax: 1020, nMin: -3800, nMax: 1120, widthM: 2020, depthM: 4920 };
  const f = fitField(field, 300, 600);
  assert(f.w <= 300 && f.h <= 600 && Math.abs(f.h / f.w - 4920 / 2020) < 0.02, 'the whole field keeps its shape');
  const v = nearView(field, { e: 0, n: 0 }, 300, 345);
  assert(Math.abs((v.eMax - v.eMin) - 300 / NEAR_K) < 1e-6 && Math.abs((v.eMin + v.eMax) / 2) < 1e-6, 'close up, centred on you');
  assert.equal(nearView(field, { e: -999, n: 0 }, 300, 345).eMin, field.eMin, 'and kept inside the field');
  assert.equal(buildingName({ sidecar: { name: 'Sauganash Hotel' } }, 'sauganash_hotel'), 'Sauganash Hotel');
  assert.equal(buildingName({}, 'lot_7_block_16'), 'A building', 'never an id');

  // Mount over a fake page: a canvas that records what is drawn.
  const calls = [];
  const g = new Proxy({}, { get: (_, k) => (k in g2 ? g2[k] : (...a) => calls.push([k, ...a])), set: (_, k, val) => { g2[k] = val; calls.push(['set', k, val]); return true; } });
  const g2 = { setLineDash: (d) => calls.push(['dash', d.join(',')]), getImageData: () => ({ data: [] }) };
  const listeners = new Map();
  const mk = (tag) => {
    const el = { tagName: tag.toUpperCase(), children: [], hidden: false, textContent: '', className: '', style: {}, attrs: {}, isConnected: true,
      classList: { s: new Set(), add(c) { this.s.add(c); } },
      append(...c) { el.children.push(...c); }, replaceChildren(...c) { el.children = c; },
      setAttribute(k, val) { el.attrs[k] = String(val); }, getAttribute(k) { return el.attrs[k] ?? null; },
      addEventListener(t, fn) { listeners.set(`${el.className}|${t}`, fn); },
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 320, height: 520 }),
      getContext: () => g, width: 0, height: 0 };
    return el;
  };
  const doc = { createElement: mk, documentElement: {}, defaultView: { devicePixelRatio: 1, setInterval: () => 1, clearInterval() {}, localStorage: null,
    getComputedStyle: () => ({ getPropertyValue: (k) => ({ '--grade-attested': '#a', '--grade-inferred': '#b', '--grade-reconstructed': '#c', '--accent': '#d' }[k] ?? '') }) } };
  const el = mk('div'); el.ownerDocument = doc;
  let player = { e: 0, n: 0, bearingDeg: 90 };
  const went = [];
  const navigation = { field: () => field, player, outlines: [yard, shed, far], drawView: (dest, view) => calls.push(['field', view.eMin]), drawMarker: (dest, x, y) => calls.push(['arrow', Math.round(x), Math.round(y)]), units: 'imperial' };
  const docked = [], opened = [];
  const ctx = { api: { navigation, registry: new Map([['shed', { sidecar: { name: 'Tool shed' } }]]) },
    navigator: { level: 1, detent: 'half', dock: () => docked.push(1), open: (l) => opened.push(l) },
    actions: { goTo: (id) => { went.push(id); return true; }, jauntRoute: () => ({ stops: [[0, 0], [20, 10], [40, 0]], at: 1 }), travelRoute: () => [] } };
  mapView.mount(el, ctx);
  const [scope, preview, bar, foot] = el.children;
  mapView.shown(el, ctx);
  assert.deepEqual(opened, [2], 'on a phone the Map opens at FULL, not HALF');
  assert.equal(el.children.length, 4);
  assert(calls.some((c) => c[0] === 'arrow'), 'your arrow is drawn');
  assert(calls.some((c) => c[0] === 'dash' && c[1] === '1.5,4'), 'the active Jaunt route is dotted');
  assert.equal(el._mapApi.zoom, 'near', 'it opens close up around you');
  assert.match(foot.textContent, /Whole field/);
  const [zoomBtn, legendBtn, legend] = bar.children;
  assert.equal(legendBtn.textContent, 'Confidence view colours', 'the locked term, exactly');
  assert.deepEqual(legend.children.map((li) => li.children[1].textContent), ['Attested', 'Inferred', 'Reconstructed']);
  assert.equal(legend.hidden, true);
  calls.length = 0;
  listeners.get('nav-map-toggle nav-map-legend-toggle|click')();
  assert.equal(legend.hidden, false); assert.equal(legendBtn.attrs['aria-pressed'], 'true');
  assert(calls.some((c) => c[0] === 'set' && c[1] === 'fillStyle' && c[2] === '#c'), 'footprints take the Confidence view colours');
  // Tap the shed (at the centre of the close-up the shed is 5 m north-east of you).
  const view = el._mapApi.view, k = el._mapApi.size.k;
  listeners.get('nav-map-canvas|click')({ clientX: (5 - view.eMin) * k, clientY: (view.nMax - 5) * k });
  assert.equal(el._mapApi.selected, 'shed');
  assert.equal(preview.hidden, false);
  assert.equal(preview.children[1].textContent, 'Tool shed');
  assert.match(preview.children[2].textContent, /^Reconstructed · \d+ ft away$/);
  listeners.get('nav-key nav-map-go|click')();
  assert.deepEqual(went, ['shed'], 'Go travels there');
  assert.deepEqual(docked, [1], 'and on a phone the device steps down so the ride is in view');
  el._mapApi.setZoom('field');
  assert.equal(zoomBtn.textContent, 'Close up');
  assert.match(foot.textContent, /east to west/);
  mapView.unmount(el);
  assert.equal(el.children.length, 0);
}

// ---- T-2625: the HUD declutter — Start / Jaunts, pace, theme and the menu leave the HUD; each
// lives in the Navigator (the Confidence chip and caret left with T-2647) --------------------
{
  const html = fs.readFileSync(path.join(ROOT, 'renderers/web/index.html'), 'utf8');
  const top = html.slice(html.indexOf('<div class="hud-top">'), html.indexOf('<div class="hud-moved"'));
  assert(top.length > 100, 'the HUD markup comes before the parked controls');
  for (const id of ['btn-start', 'btn-confidence', 'btn-confidence-more', 'btn-pace', 'btn-theme', 'btn-help']) {
    assert(!top.includes(`id="${id}"`), `the HUD's top row no longer holds #${id}`);
  }
  const parked = html.slice(html.indexOf('<div class="hud-moved"'), html.indexOf('</div>', html.indexOf('<div class="hud-moved"')));
  assert(/id="btn-start"/.test(parked), 'Start / Jaunts waits, hidden, with its id; the Jaunts app holds its choices');
  // T-2656: the switch is Settings › Display's two-way choice, #s-theme, and the old chip is gone.
  assert.equal((html.match(/id="btn-theme"/g) ?? []).length, 0);
  assert.equal((html.match(/id="s-theme"/g) ?? []).length, 1);
  const settings = html.slice(html.indexOf('data-panel="settings"'), html.indexOf('</section>', html.indexOf('data-panel="settings"')));
  assert(/id="s-theme"/.test(settings), 'light / dark lives in Settings');
  assert(!/id="btn-pace"/.test(html), 'the pace chip is gone; Move holds the pace');
  assert(/id="s-move"/.test(html), 'Move\'s picker holds the pace');
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
  // T-2627: the quick column holds the Inspect key alone — T-2977 moved Walk/Fly into the
  // instrument's heading row, so the key appearing no longer shifts it.
  const quick = html.slice(html.indexOf('<div class="quick-column"'), html.indexOf('</div>', html.indexOf('<div class="quick-column"')));
  assert.equal((quick.match(/<button\b/g) ?? []).length, 1, 'the quick column holds the Inspect key alone');
  assert.match(quick, /id="btn-inspect"[^>]*hidden/);
  const row = html.slice(html.indexOf('<div class="compass-row">'), html.indexOf('<div id="compass"'));
  assert.match(row, /<button type="button" id="btn-fly" class="fly-key" aria-pressed="false"/, 'T-2977: Walk/Fly is the heading row\'s round key');
  assert.match(row, /id="fly-label">Fly</, 'T-2977: the key keeps its Walk/Fly name for a screen reader');
  const walkCss = fs.readFileSync(new URL('../renderers/web/css/walk.css', import.meta.url), 'utf8');
  assert.match(walkCss, /\.quick-column > \.quick-inspect\[hidden\] \{[^}]*opacity: 0; visibility: hidden;[^}]*visibility 0s linear \.25s/,
    'T-2977: the Inspect key fades out, and leaves the pointer and the tab order once the fade is done');
  assert.match(walkCss, /@media \(max-height: 500px\) and \(orientation: landscape\) \{\s*\.quick-column \{ top: auto;/,
    'T-2977: a phone on its side puts the Inspect key in the lower corner, clear of the instrument');
  assert.match(html, /<button type="button" class="target-tag" id="target-tag" data-place="centre" data-label="Ahead" hidden><\/button>/);
  // T-2942: Settings › Show › where the name shows (right first: the default) and whether it fades.
  assert.match(html, /<select id="s-look-tag-place">\s*<option value="right">[^<]+<\/option>\s*<option value="centre">[^<]+<\/option>\s*<option value="bottom">/);
  assert.match(html, /<select id="s-look-tag-hold">\s*<option value="fade">Fades after a few seconds<\/option>\s*<option value="always">Always shown<\/option>/);
  assert.match(html, /<div class="instrument-below" id="instrument-below">\s*<div id="street-readout"/, 'the docked tag\'s column starts with the address');
  assert.match(html, /<div class="hud-bottom" id="hud-bottom">/);
  assert.match(html, /<input type="checkbox" id="s-look-tag">/, 'T-2736: Settings › Show offers the look-at tag');
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
  // T-2654: Map is its own screen now, not a stub that opened the pop-out.
  assert.equal(nav.app, 'map', '?nav=map opens the Map');
  assert.ok(nav.level > 0, 'and the device opens to show it');
  // Jaunts is a screen since T-2630 (no longer a launch), so the link opens it in the device.
  await nav.openLink({ app: 'jaunts' });
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(nav.app, 'jaunts', '?nav=jaunts opens Jaunts');
  await nav.openLink({ app: 'inspect', id: 'glessner_house', tab: 'design' });
  // T-2638: the dossier has landed, so the link opens Inspect's own screen on that building
  // (the link's id is offered as the one selected), not the card.
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(nav.app, 'inspect', '?nav=inspect:glessner_house opens Inspect');
  assert.ok(!calls.some((c) => c[0] === 'card'), 'and not the building card');
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
      actions: { openSection: (id) => calls.push(['section', id]), jaunts: () => calls.push(['jaunts']), confidenceMenu: () => calls.push(['confidence-menu']) } }) });
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
  // Every rail app holds a screen now (Move and Settings since T-2620, the Confidence view
  // since T-2647), so a launch app is the test's own.
  nav.register({ id: 'stub', label: 'Stub', code: 'SCR 99', order: 95, icon: '<svg></svg>', launch: () => { calls.push(['stub']); } });
  await Promise.resolve();
  const stubAt = nav.apps.indexOf('stub') + 1;
  assert.ok(stubAt >= 1 && stubAt <= 9, `${where}: the stub is within reach of a digit (${nav.apps.join(', ')})`);
  press(String(stubAt));
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(calls.at(-1), ['stub'], `${where}: a digit runs a launch app`);

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

// ---- the close key (T-2742): the header's X does what the collapse arrow does ----------
for (const phone of [false, true]) {
  const dom = miniDom();
  const nav = createNavigator({ root: dom.root, scene: json('data/scenes/1904.json'), isPhone: () => phone, storage: fakeStorage(),
    apps: APPS, keyTarget: null, viewportHeight: () => 780,
    context: () => ({ scene: { id: '1904' }, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false, actions: {} }) });
  await Promise.resolve();
  const where = phone ? 'phone' : 'desktop';
  const x = dom.byId.get('nav-close');
  for (const opened of [1, 2]) {
    nav.open(opened);
    assert.ok(nav.level > 0, `${where}: open`);
    let stopped = 0;
    x.dispatch('pointerdown', { stopPropagation() { stopped += 1; } });
    x.dispatch('click', { stopPropagation() { stopped += 1; } });
    assert.equal(nav.level, 0, `${where}: the X closes it, from level ${opened}`);
    assert.equal(nav.detent, phone ? 'dock' : 'rail', `${where}: to the dock or the rail, where the collapse arrow sends it`);
    assert.equal(stopped, 2, `${where}: its press starts no drag, and its tap never reaches the head's "open when docked" tap`);
  }
  // close()'s own focus rule: the mini DOM lays nothing out, so the grip counts as shown.
  assert.ok(dom.byId.get('nav-grip').focused > 0, `${where}: focus goes back to the handle that reopens it`);
  // The head's own tap, which the X's tap stops short of, would have reopened it.
  dom.byId.get('nav-head').dispatch('click');
  assert.ok(nav.level > 0, `${where}: (the head's tap does reopen a docked device, which is why the X stops its click)`);
}
console.log('NAVIGATOR CLOSE KEY PASS — the header\'s X docks the device on a phone and folds it to the rail on a desktop, without starting a drag or reopening through the head');

console.log('NAVIGATOR KEYS PASS — N and Tab-from-the-scene toggle it, 1–9 open the rail\'s apps, Escape closes it; focus moves into the app and back to the grip; nothing fires while typing or before landing');

console.log('NAVIGATOR PASS — the probe looks only when asked and moved, each asker within its own distance (Home 100 m); the street at the 1904 spawn is Prairie & Eighteenth; '
  + 'DOCK, HALF and FULL by tap, drag and flick, the desktop panel to its rail; Home paints the place, the target, the Jaunt, Move and the Confidence view; the rail opens the drawer’s sections');
