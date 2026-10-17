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
import { createRail, railOrder, capped, MAX_ICONS } from '../renderers/web/js/nav-rail.js';
import { APPS } from '../renderers/web/js/apps/index.js';

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
      querySelector(sel) { return walk(el).find((c) => matches(c, sel)) ?? null; },
      querySelectorAll(sel) { return walk(el).filter((c) => matches(c, sel)); },
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
    querySelectorAll: (sel) => walk(body).filter((c) => matches(c, sel)),
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
  return { root, doc, docEl, body, byId, rail };
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
    context: () => ({ scene: { id: '1904' }, hasPeople: false, selected: null, confidenceOn: false, whatsNewUnread: false,
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

  // A stub app (Settings, until its lane lands) docks the device and opens the drawer's section.
  nav.open(1);
  button(dom, 'settings').dispatch('click');
  await Promise.resolve();
  assert.deepEqual(calls.at(-1), ['section', 'settings']);
  assert.equal(nav.detent, phone ? 'dock' : 'rail');
  nav.open(1);
  button(dom, 'jaunts').dispatch('click');
  await Promise.resolve();
  assert.deepEqual(calls.at(-1), ['jaunts'], 'Jaunts opens the Jaunts list');

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
  const calls = [];
  const dom = miniDom();
  const nav = createNavigator({ root: dom.root, scene: json('data/scenes/1835.json'), isPhone: () => false, storage: fakeStorage(),
    apps: APPS, context: () => ({ hasPeople: true, peopleSection: true, actions: { openSection: (id) => calls.push(id) } }) });
  assert(nav.apps.includes('people'), '1835: People shows');
  assert.deepEqual(nav.apps.slice(0, 3), ['home', 'jaunts', 'people'], 'under Jaunts');
  await nav.select('people');
  assert.deepEqual(calls, ['people'], '1835: People opens the drawer\u2019s section');
  assert.equal(dom.byId.get('nav-app-people') ?? null, null, '…and builds no screen of its own');

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
      actions: { openSection: (id) => calls.push(['section', id]), jaunts: () => calls.push(['jaunts']) } }) });
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
  const moveAt = order.indexOf('move') + 1;
  press(String(moveAt));
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(calls.at(-1), ['section', 'travel'], `${where}: a digit runs a launch app (Move opens its section)`);

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
