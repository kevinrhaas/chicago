#!/usr/bin/env node
// T-2665 (NAV-805): the Navigator License. Finishing the Field Check awards it once per
// device (Skip never does; a replay that finishes again keeps the one license), storage
// behind try/catch, and it shows with the Jaunt keepsakes in the Jaunts app's daybook after
// a reload. Drives js/license.js with js/tour.js over a fake storage and clock, and
// js/jaunt-preview.js's real daybook over a small hand-made DOM with the 1835 daybook.
// No browser; the smoke (part 13) finishes the Field Check and opens the daybook in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createLicense, issuedOn, LICENSE_KEY } from '../renderers/web/js/license.js';
import { createTour, STEPS, TOUR_KEY } from '../renderers/web/js/tour.js';
import { t } from '../renderers/web/js/strings/index.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const store = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; };
const refusing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
const WHEN = new Date('2026-10-18T15:00:00Z');

// ---- the words: the design's name, no ids, short lines ------------------------------------
assert.equal(t('license.title'), 'Navigator License', 'section 11 names it NAVIGATOR LICENSE');
for (const k of ['form', 'text', 'issued', 'held', 'awarded', 'reset-confirm', 'no-jaunt-keepsakes']) {
  const s = t(`license.${k}`);
  assert.ok(s, `license.${k} is in the string table`);
  assert.doesNotMatch(s, /\b(tier|ticket)s?\b|[a-z]+_[a-z]+|\/|T-\d+/i, `license.${k} carries no id, path, "tier" or "ticket"`);
  assert.ok(s.split(/\s+/).length <= 14, `license.${k} reads in 14 words or fewer, like a bubble`);
}
assert.equal(issuedOn('2026-10-18T15:00:00Z'), 'Oct 18, 2026');
assert.equal(issuedOn('not a date'), null);
assert.equal(issuedOn(null), null);

// ---- finishing the Field Check awards it once; Skip never does ---------------------------
// Runs the real tour to its end: Next on 01, each waiting step's action, Finish on 08.
function runTour(tour, probe) {
  tour.start();
  assert.equal(tour.press(), true);
  probe.yawDeg = (probe.yawDeg + 90) % 360; tour.tick();
  probe.e += 6; tour.tick();
  probe.opens += 1; probe.selected = true; tour.tick();
  probe.selected = false; tour.tick();
  probe.apps = { ...probe.apps, move: (probe.apps.move ?? 0) + 1 }; tour.tick();
  probe.apps = { ...probe.apps, settings: (probe.apps.settings ?? 0) + 1 }; tour.tick();
  assert.equal(tour.step, STEPS.length - 1, 'on step 08');
}
{
  const s = store();
  const license = createLicense({ storage: s, now: () => WHEN });
  const awards = [];
  const probe = { yawDeg: 0, e: 0, n: 0, opens: 0, selected: false, apps: {}, scene: '1835' };
  const tour = createTour({ probe: () => probe, storage: s, onFinish: () => awards.push(license.award()) });
  assert.equal(license.held, false, 'nothing held before the tour');
  assert.equal(license.card(), null, 'and no card');

  // Skip at 08 is not finishing.
  runTour(tour, probe);
  tour.skip();
  assert.deepEqual(awards, [], 'Skip never awards it');
  assert.equal(license.held, false);
  assert.equal(s.m.get(LICENSE_KEY), undefined);

  // A replay finished: awarded, dated, on this device.
  runTour(tour, probe);
  assert.equal(tour.press(), true, 'Finish on step 08');
  assert.deepEqual(awards, [true], 'Finish awards it');
  assert.equal(license.held, true);
  assert.deepEqual(JSON.parse(s.m.get(LICENSE_KEY)), { earned: WHEN.toISOString() }, 'kept on this device, with the day it was issued');
  const card = license.card();
  assert.deepEqual(card, { form: t('license.form'), title: 'Navigator License', text: t('license.text'), line: 'Issued Oct 18, 2026 · Good in every year' });

  // Again: one license.
  runTour(tour, probe);
  tour.press();
  assert.deepEqual(awards, [true, false], 'a replay that finishes again keeps the one license');

  // A reload: a fresh page reads it back.
  const reloaded = createLicense({ storage: s, now: () => new Date() });
  assert.equal(reloaded.held, true, 'held after a reload');
  assert.equal(reloaded.earned, WHEN.toISOString(), 'with its first issue date');
  assert.equal(reloaded.award(), false, 'and not awarded twice');
}

// ---- a device that finished before the license existed holds it, undated -----------------
{
  const s = store();
  s.setItem(TOUR_KEY, JSON.stringify({ active: false, step: null, done: true }));
  const license = createLicense({ storage: s });
  assert.equal(license.held, true, 'the tour\'s own record says it was finished');
  assert.equal(license.card().line, 'Good in every year', 'undated: no day is invented');
  s.setItem(TOUR_KEY, JSON.stringify({ active: false, step: null, done: false }));
  assert.equal(createLicense({ storage: s }).held, false, 'a skipped tour holds nothing');
}

// ---- storage refused: no error, held for this page ---------------------------------------
{
  const license = createLicense({ storage: refusing, now: () => WHEN });
  assert.equal(license.held, false);
  assert.equal(license.award(), true, 'refused storage still awards it');
  assert.equal(license.held, true, '…held for this page');
  assert.equal(license.award(), false, '…once');
  license.forget();
  assert.equal(license.held, false, 'the harness can forget it');
  const none = createLicense({ storage: null });
  assert.equal(none.award(), true, 'no storage at all: nothing throws');
  const broken = store(); broken.setItem(LICENSE_KEY, '{not json');
  assert.equal(createLicense({ storage: broken }).held, false, 'a damaged record reads as none, never an error');
}

// ---- the daybook in the Jaunts app shows it with the Jaunt keepsakes ---------------------
function makeDom() {
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), children: [], parent: null, dataset: {}, attrs: {}, hidden: false, disabled: false,
      title: '', type: '', tabIndex: 0, _text: '', _cls: new Set(),
      get className() { return [...this._cls].join(' '); }, set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
      classList: null,
      get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
      set textContent(v) { this._text = String(v ?? ''); this.children = []; },
      set innerHTML(v) { this._html = v; },
      get content() { return { firstChild: make('svg') }; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; }, removeAttribute(k) { delete this.attrs[k]; },
      append(...cs) { for (const c of cs) { if (c == null) continue; const n = typeof c === 'string' ? Object.assign(make('#text'), { _text: c }) : c; n.parent = el; el.children.push(n); } },
      prepend(...cs) { const old = el.children; el.children = []; el.append(...cs); el.children.push(...old); },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
      click() { for (const fn of fns.click ?? []) fn({ preventDefault() {} }); },
      closest: () => null, focus() {}, scrollIntoView() {}, matches: () => false,
      get isConnected() { return true; },
      querySelectorAll(sel) { return walk(el).filter((c) => matches(c, sel)); },
      querySelector(sel) { return el.querySelectorAll(sel)[0] ?? null; },
    };
    el.classList = { add: (...c) => c.forEach((x) => el._cls.add(x)), remove: (...c) => c.forEach((x) => el._cls.delete(x)),
      contains: (c) => el._cls.has(c), toggle: (c, on = !el._cls.has(c)) => { if (on) el._cls.add(c); else el._cls.delete(c); return on; } };
    return el;
  };
  const walk = (el, out = []) => { for (const c of el.children) { out.push(c); walk(c, out); } return out; };
  const matches = (el, sel) => sel.split(',').some((s) => {
    s = s.trim();
    let m;
    if ((m = /^\.([\w-]+)$/.exec(s))) return el._cls?.has(m[1]);
    if ((m = /^\[data-action="([\w-]+)"\]$/.exec(s))) return el.dataset?.action === m[1];
    if ((m = /^\[data-keepsake="([\w:-]+)"\]$/.exec(s))) return el.dataset?.keepsake === m[1];
    if ((m = /^([a-z0-9]+)$/.exec(s))) return el.tagName === m[1].toUpperCase();
    return false;
  });
  return { createElement: make };
}
globalThis.document = makeDom();
const { createJauntPreview } = await import('../renderers/web/js/jaunt-preview.js');
const book = JSON.parse(read('data/sidecars/1835/jaunts/daybook.json'));
const fetcher = async (url) => {
  const name = String(url).split('/').pop();
  const body = name === 'daybook.json' ? book : name === 'catalog.json' ? { scene: '1835', jaunts: [] } : null;
  return { ok: !!body, status: body ? 200 : 404, json: async () => body };
};
async function daybookOf(license, storage) {
  const root = document.createElement('div');
  const preview = createJauntPreview({ root, scene: '1835', dataBase: 'https://example.test/', destinations: { byId: () => null }, api: {},
    fetcher, storage, license, onStart: () => true });
  await preview.open();
  return { root, preview };
}
const openBook = (root) => { root.querySelector('[data-action="daybook"]').click(); return root.querySelector('.jaunt-daybook'); };
{
  const s = store();
  const license = createLicense({ storage: s, now: () => WHEN });
  // Not held: the daybook is as it was.
  let { root } = await daybookOf(license, s);
  assert.match(root.querySelector('[data-action="daybook"]').textContent, /· 0 kept$/);
  let view = openBook(root);
  assert.equal(view.querySelectorAll('[data-keepsake="navigator-license"]').length, 0, 'no license before the tour is finished');
  assert.match(view.textContent, /No keepsakes yet\./);

  // Awarded, then a reload: a fresh license and daybook from the same storage.
  license.award();
  ({ root } = await daybookOf(createLicense({ storage: s }), s));
  assert.match(root.querySelector('[data-action="daybook"]').textContent, /· 1 kept$/, 'the daybook chip counts it');
  view = openBook(root);
  const [card] = view.querySelectorAll('[data-keepsake="navigator-license"]');
  assert.ok(card, 'shown in the daybook after a reload');
  assert.ok(card._cls.has('jaunt-keepsake') && card._cls.has('jaunt-keepsake-license'), 'drawn as a keepsake, in its own style');
  assert.equal(card.parent._cls.has('jaunt-keepsakes'), true, 'on the keepsakes shelf');
  assert.match(card.textContent, /Navigator License/);
  assert.match(card.textContent, /Issued Oct 18, 2026/);
  assert.match(view.textContent, /No jaunt keepsakes yet\./, 'with no jaunt finished, the shelf says so without denying the license');
  assert.equal(view.querySelectorAll('[data-action="daybook-reset"]').length, 0, 'nothing to reset: the license is not the daybook\'s');

  // With a Jaunt keepsake beside it: the Jaunt's first, the license after; Reset leaves it.
  let { root: r2, preview } = await daybookOf(createLicense({ storage: s }), s);
  const journal = await preview.daybook();
  const family = book.families[0];
  journal.award({ id: 'test-jaunt', keepsake: { id: 'k', family: family.name, title: 'A Test Memento', text: 'Kept for the test.' } });
  await preview.open();
  assert.match(r2.querySelector('[data-action="daybook"]').textContent, /· 2 kept$/);
  view = openBook(r2);
  const shelf = view.querySelector('.jaunt-keepsakes');
  assert.deepEqual(shelf.children.map((c) => c.dataset.keepsake), ['test-jaunt:k', 'navigator-license'], 'with the Jaunt keepsakes, on one shelf');
  const reset = view.querySelector('[data-action="daybook-reset"]');
  reset.click();
  assert.equal(reset.textContent, t('license.reset-confirm'), 'the confirm says the license stays');
  reset.click();
  view = r2.querySelector('.jaunt-daybook');
  assert.deepEqual(view.querySelector('.jaunt-keepsakes').children.map((c) => c.dataset.keepsake), ['navigator-license'], 'Reset daybook leaves it');
  assert.equal(createLicense({ storage: s }).held, true);
}

// ---- the page: Finish awards it and says so once; Jaunts gets it ---------------------------
const main = read('renderers/web/js/main.js');
assert(/onFinish: \(\) => awardLicense\(\)/.test(main), 'the tour\'s Finish awards it (Skip calls no onFinish)');
assert(/if \(!license\.award\(\)\) return false;/.test(main), 'the awarded line shows only when it is newly awarded');
assert(/el\.textContent = license\.awardedText\(\); el\.dataset\.hint = 'license'; el\.hidden = false;/.test(main), 'on the one-line hint, which takes no pointer events');
assert(/modeNote: \(jaunt\) => jauntWay\(jaunt\)\.note,\n\s+license,/.test(main), 'the Jaunts app\'s daybook is handed the license');
assert(/api\.license = license;/.test(main), 'the smoke reaches it');
assert(/\.jaunt-keepsake-license \{[^}]*currentColor/.test(read('renderers/web/css/jaunt.css')), 'drawn in the skin\'s own ink, so every machine skin and both themes carry it');

console.log('test_license: finishing the Field Check awards the Navigator License once per device, and the Jaunts daybook shows it after a reload');
