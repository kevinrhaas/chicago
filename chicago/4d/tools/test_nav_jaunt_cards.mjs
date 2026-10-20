#!/usr/bin/env node
// T-2631 (NAV-402): Jaunt cards — a credited plate of the route's own stops where the
// project holds one (never a stand-in), the keepsake once earned, and the outing in
// progress pinned on top as a Continue card. Reads pictures.js § plateFor and drives
// jaunt-menu.js's real cards over a small hand-made DOM. No browser; the smoke (part 15)
// pauses a Jaunt and taps Continue in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { plateFor } from '../renderers/web/js/pictures.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- plates: credited, the stops' own, or none ---------------------------------------------
const doc = {
  image_store: { base_url: 'https://images.example.org/store/' },
  by_structure: {
    linked_only: [{ id: 'l1', title: 'A linked picture', url: 'https://holder.example/1' }],
    glessner_house: [
      { id: 'g1', kind: 'PHOTO', title: 'Glessner House, south front', creator: 'HABS photographer',
        holder: 'Library of Congress — Prints and Photographs', collection: 'HABS', rights: 'public domain', held: { t: 'thumbs/g1.jpg' } },
    ],
  },
};
assert.equal(plateFor(doc, ['nowhere', 'linked_only']), null, 'a picture that is only linked is never shown as a plate');
assert.equal(plateFor(null, ['glessner_house']), null, 'no pictures file, no plate');
const plate = plateFor(doc, ['linked_only', 'glessner_house']);
assert.equal(plate.src, 'https://images.example.org/store/thumbs/g1.jpg');
assert.equal(plate.structure, 'glessner_house', 'the first stop that has a held picture');
assert.equal(plate.credit, 'Library of Congress', 'the holder, as the card shows it');
assert.match(plate.full, /HABS photographer/);
assert.match(plate.full, /PUBLIC DOMAIN/, 'the whole credit and the rights ride along');
assert.match(plate.alt, /^PHOTO: Glessner House/);

// ---- the cards, over a small DOM -----------------------------------------------------------
function makeDom() {
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), children: [], parent: null, dataset: {}, attrs: {}, hidden: false, disabled: false,
      title: '', type: '', value: '', src: '', alt: '', loading: '', decoding: '', tabIndex: 0, _text: '', _cls: new Set(),
      get className() { return [...this._cls].join(' '); }, set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
      classList: null,
      get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
      set textContent(v) { this._text = String(v ?? ''); this.children = []; },
      set innerHTML(v) { this._html = v; },
      get content() { const svg = make('svg'); return { firstChild: svg }; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { if (c == null) continue; const n = typeof c === 'string' ? Object.assign(make('#text'), { _text: c }) : c; n.parent = el; el.children.push(n); } },
      prepend(...cs) { const old = el.children; el.children = []; el.append(...cs); el.children.push(...old); },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      addEventListener(t, fn) { (fns[t] ??= []).push(fn); },
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
    if ((m = /^\[data-([\w-]+)\]$/.exec(s))) return el.dataset?.[m[1]] != null;
    if ((m = /^\[data-action="([\w-]+)"\]$/.exec(s))) return el.dataset?.action === m[1];
    if ((m = /^([a-z0-9]+)$/.exec(s))) return el.tagName === m[1].toUpperCase();
    return false;
  });
  return { createElement: make };
}
globalThis.document = makeDom();
const { createJauntMenu } = await import('../renderers/web/js/jaunt-menu.js');
const root = document.createElement('div');
const rows = [
  { id: 'prairie-walk', title: 'Prairie Walk', premise: 'Walk the avenue.', category: 'Orientation', primary_family: 'Ways & Means',
    availability: 'available', stop_count: 3, default_mode: 'walk', allowed_modes: ['walk', 'instantly'],
    destinations: [{ kind: 'structure', id: 'glessner_house' }] },
  { id: 'no-picture', title: 'No Picture', premise: 'Nowhere pictured.', category: 'Orientation', primary_family: 'Ways & Means',
    availability: 'available', stop_count: 2, default_mode: 'walk', allowed_modes: ['walk'], destinations: [{ kind: 'structure', id: 'nowhere' }] },
];
const menu = createJauntMenu({ root, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {},
  plateFor: (row) => plateFor(doc, row.destinations.map((d) => d.id)), kept: (row) => row.id === 'prairie-walk' });
menu.show(rows);
const cards = root.querySelectorAll('.jaunt-card');
assert.equal(cards.length, 2);
const byId = Object.fromEntries(cards.map((c) => [c.dataset.jaunt, c]));
const img = byId['prairie-walk'].querySelectorAll('img')[0];
assert(img && img.src === plate.src && img.loading === 'lazy', 'a plate of the route\'s own stop');
assert(byId['prairie-walk'].querySelectorAll('.jaunt-type')[0].classList.contains('has-plate'));
assert.equal(byId['prairie-walk'].querySelectorAll('.jaunt-credit')[0]?.textContent, 'Picture: Library of Congress', 'and its credit, on the card');
assert.equal(byId['prairie-walk'].querySelectorAll('.jaunt-kept')[0]?.textContent, 'Keepsake earned', 'the keepsake, once earned');
assert.equal(byId['no-picture'].querySelectorAll('img').length, 0, 'no held picture: no plate, the family icon stays');
assert.equal(byId['no-picture'].querySelectorAll('.jaunt-credit').length, 0);
assert.equal(byId['no-picture'].querySelectorAll('.jaunt-kept').length, 0, 'no keepsake, no badge');
const text = byId['prairie-walk'].textContent;
assert(/Prairie Walk/.test(text) && /Walk the avenue\./.test(text) && /3 stops/.test(text) && /10 min/.test(text),
  `title, premise, stops and minutes: ${text}`);

// ---- the Continue card in jaunt-preview.js ------------------------------------------------
const preview = read('renderers/web/js/jaunt-preview.js');
assert(/`Continue · Stop \$\{at \+ 1\} of \$\{stops\.length \|\| at \+ 1\}`/.test(preview), 'CONTINUE · STOP n OF m');
assert(/next \? `Next: \$\{label\(next\)\}`/.test(preview), 'Next: the next stop by name');
assert(/if \(session\.phase === 'menu'\) prefix\.unshift\(note\)/.test(preview), 'an outing in progress is pinned on top');
assert(/button\('Continue'/.test(preview), 'its key is Continue');
assert(/if \(!jauntRestoreTried\) \{ jauntRestoreTried = true; if \(!jauntRuntime\.state\.jaunt\) await jauntRuntime\.restore\(\); \}/.test(read('renderers/web/js/main.js')),
  'a saved outing is restored when the list first opens, so Continue survives a reload');

console.log('test_nav_jaunt_cards: credited plates of the stops or none, keepsakes, and Continue pinned on top');

// ---- T-2944 (owner, 2026-10-20): titles lead with what is distinctive, and the list keeps
// related outings together — by kind, featured first within it, then by name ---------------
{
  const { jauntOrder, sortTitle, filterJaunts } = await import('../renderers/web/js/jaunt-menu.js');
  const { FAMILIES } = await import('../renderers/web/js/menu-icons.js');
  const { readFileSync } = await import('node:fs');
  const catalog = (y) => JSON.parse(readFileSync(new URL(`../data/sidecars/${y}/jaunts/catalog.json`, import.meta.url), 'utf8')).jaunts;
  assert.equal(sortTitle('A Letter Home'), 'Letter Home'); assert.equal(sortTitle('An Evening Stroll'), 'Evening Stroll');
  assert.equal(sortTitle('The architects'), 'architects'); assert.equal(sortTitle('Taverns of Chicago'), 'Taverns of Chicago');
  for (const y of ['1835', '1904']) {
    const rows = filterJaunts(catalog(y));
    for (const r of rows) {
      assert(!/^(Prairie Avenue|Style walk):/.test(r.title), `${y}: "${r.title}" leads with what it shares, not what it is`);
      assert(r.title.length <= 34, `${y}: "${r.title}" is short enough for two lines on a phone`);
    }
    const kinds = rows.map((r) => FAMILIES.indexOf(r.primary_family));
    assert.deepEqual(kinds, [...kinds].sort((a, b) => a - b), `${y}: grouped by kind, in the pills' order`);
    for (let i = 1; i < rows.length; i++) assert(jauntOrder(rows[i - 1], rows[i]) < 0, `${y}: ${rows[i - 1].title} before ${rows[i].title}`);
  }
  const t1904 = filterJaunts(catalog('1904')).map((r) => r.title);
  const styles = t1904.map((t, i) => (/ style walk$/.test(t) ? i : -1)).filter((i) => i >= 0);
  assert.deepEqual(styles.map((i) => t1904[i]), ['Italianate style walk', 'Romanesque style walk', 'Second Empire style walk']);
  assert.equal(styles[2] - styles[0], 2, 'the three style walks sit together');
}
