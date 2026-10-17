// T-2655 — the Navigator's Jump app (js/apps/jump-view.js): era mini-cards with HERE,
// the in-world jump (ring, transfer stamp, then the destination's own arrival), and
// RECALL as the screen's one signal-red key.
//
//   node tools/test_nav_jump.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mount, unmount, jumpTo, DESTINATIONS, RING_MS } from '../renderers/web/js/apps/jump-view.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, '../renderers/web');

function fakeDoc() {
  const docFns = {};
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), className: '', textContent: '', innerHTML: '', dataset: {}, attrs: {}, children: [], parent: null,
      href: '', src: '', alt: '', type: '',
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      // A string is a text node, as in the DOM (the cards space their words with them).
      append(...cs) {
        for (let c of cs) {
          if (typeof c === 'string') c = { nodeType: 3, className: '', textContent: c, children: [], dataset: {}, getAttribute: () => null };
          c.parent = el; el.children.push(c);
        }
      },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      remove() { if (el.parent) { el.parent.children.splice(el.parent.children.indexOf(el), 1); el.parent = null; } },
      addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
      click(extra = {}) {
        const e = { button: 0, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, ...extra };
        for (const fn of fns.click ?? []) fn(e);
        return e;
      },
      get ownerDocument() { return doc; },
    };
    return el;
  };
  const doc = {
    createElement: make,
    body: null,
    addEventListener(type, fn) { (docFns[type] ??= []).push(fn); },
    removeEventListener(type, fn) { docFns[type] = (docFns[type] ?? []).filter((f) => f !== fn); },
    key(key) { const e = { key, preventDefault() {}, stopPropagation() {} }; for (const fn of docFns.keydown ?? []) fn(e); },
  };
  doc.body = make('body');
  return doc;
}
const walk = (el, out = []) => { for (const c of el.children) { out.push(c); walk(c, out); } return out; };
// What the DOM's textContent gives: the text, run together with no separator added — so
// a card whose words touch ("1835Here") reads as it would in a page (T-2655 mobile smoke).
const text = (el) => [el.textContent, ...el.children.map(text)].join('');

// ---- the cards ---------------------------------------------------------------------
{
  const doc = fakeDoc();
  const panel = doc.createElement('div');
  const calls = [];
  const timers = [];
  const stored = new Map();
  mount(panel, { scene: { id: '1904' }, actions: { recall: () => calls.push('recall') } }, {
    doc, reduced: false, go: (href) => calls.push(['go', href]),
    wait: (fn, ms) => { timers.push({ fn, ms }); return timers.length; }, cancel: (id) => { timers[id - 1].fn = null; },
    storage: { setItem: (k, v) => stored.set(k, v) },
  });
  const all = walk(panel);
  const cards = all.filter((e) => e.className.split(' ').includes('nav-jump'));
  assert.deepEqual(cards.map((c) => c.dataset.year), ['1835', '1904', '1812'], 'the three destinations, in the Observatory\'s order');
  const herecard = cards.find((c) => c.getAttribute('aria-current') === 'page');
  assert.equal(herecard.dataset.year, '1904', 'the one you are in is marked');
  assert.equal(herecard.tagName, 'DIV', 'and is not a link');
  assert.match(text(herecard), /\bHere\b/, 'HERE on its card (set in mono caps by the stylesheet)');
  assert.equal(cards.filter((c) => /\bHere\b/.test(text(c))).length, 1, 'HERE on one card only');
  for (const c of cards) {
    const img = c.children.find((x) => x.tagName === 'IMG');
    assert.ok(img && DESTINATIONS.some((d) => d.plate === img.src) && img.alt === '', `${c.dataset.year}: wears its Observatory plate, decorative`);
    assert.doesNotMatch(text(c), /[a-z0-9]+_[a-z0-9]+/i, `${c.dataset.year}: no id or snake_case`);
  }
  assert.match(text(cards[0]), /River|Chicago|water/i);
  assert.match(text(cards[2]), /14 August 1812/, 'the 1812 card carries its scene date');
  const keys = all.filter((e) => e.className.split(' ').includes('nav-key'));
  assert.equal(keys.length, 1, 'RECALL is the screen\'s one key, so its one signal-red one');
  assert.match(keys[0].className, /\bnav-recall\b/);
  assert.equal(keys[0].href, '../', 'RECALL goes to the Observatory');
  assert.match(keys[0].innerHTML, /Recall/);
  keys[0].click();
  assert.deepEqual(calls, ['recall'], 'and tells the journey it is recalling');

  // Picking 1835 from 1904: the ring, the stamp, then the page.
  const to1835 = cards.find((c) => c.dataset.year === '1835');
  assert.equal(to1835.href, '../1835/');
  const modified = to1835.click({ metaKey: true });
  assert.equal(modified.defaultPrevented, false, 'a modified click opens the page as a link does');
  const e = to1835.click();
  assert.equal(e.defaultPrevented, true, 'a plain click jumps in the world');
  const ring = doc.body.children.find((c) => c.className === 'nav-jump-ring');
  assert.ok(ring, 'the transfer ring closes over the town');
  assert.equal(ring.getAttribute('role'), 'status');
  assert.match(text(ring), /Jumping to 1835/);
  assert.equal(stored.has('chicago4d.transfer'), false, 'no stamp while the ring runs: a late timer must not age it');
  assert.equal(timers.at(-1).ms, RING_MS, `the ring runs ${RING_MS} ms`);
  assert.equal(jumpTo(DESTINATIONS[2], { doc }), false, 'one jump at a time');
  const before = Date.now();
  timers.at(-1).fn();
  assert.ok(stored.get('chicago4d.transfer') >= before, 'the Observatory\'s transfer stamp is written as the page goes, so the arrival starts on the ring\'s tail');
  assert.deepEqual(calls.at(-1), ['go', '../1835/'], 'then the destination page, which runs its own time-stream and landing');
  unmount(panel);
  assert.equal(panel.children.length, 0);
}

// Escape (or Abort) during the ring stays put; reduced motion goes at once.
{
  const doc = fakeDoc();
  const gone = [];
  const timers = [];
  const kept = new Map();
  jumpTo(DESTINATIONS[0], { doc, reduced: false, go: (h) => gone.push(h), wait: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    cancel: (id) => { timers[id - 1].fn = null; }, storage: { setItem: (k, v) => kept.set(k, v) } });
  doc.key('Escape');
  assert.equal(timers[0].fn, null, 'Escape aborts the jump');
  assert.equal(kept.size, 0, 'an aborted jump leaves no transfer stamp');
  assert.equal(doc.body.children.length, 0, 'and takes the ring away');
  jumpTo(DESTINATIONS[0], { doc, reduced: false, go: (h) => gone.push(h), wait: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    cancel: (id) => { timers[id - 1].fn = null; }, storage: null });
  doc.body.children[0].children.find((c) => c.className === 'nav-jump-abort').click();
  assert.equal(timers[1].fn, null, 'so does Abort');
  jumpTo(DESTINATIONS[1], { doc, reduced: true, go: (h) => gone.push(h), wait: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    cancel: () => {}, storage: null });
  assert.equal(timers[2].ms, 0, 'reduced motion: no ring time, the page goes at once');
  timers[2].fn();
  assert.deepEqual(gone, ['../1904/']);
}

// The plates exist, the stylesheet has the ring, its reduced-motion rule and the red key.
{
  for (const d of DESTINATIONS) assert.ok(readFileSync(path.join(web, d.plate)).length > 1000, `${d.plate} is in the tree`);
  const css = readFileSync(path.join(web, 'css/navigator.css'), 'utf8');
  assert.match(css, /\.nav-jump-ring i \{[^}]*animation: nav-crossing 1\.2s/);
  assert.match(css, /prefers-reduced-motion: reduce\) \{\s*\.nav-jump-ring, \.nav-jump-ring i \{ animation: none; \}/);
  assert.match(css, /\.nav-key[\s\S]*?background: var\(--signal/, 'the key is signal red');
  const main = readFileSync(path.join(web, 'js/main.js'), 'utf8');
  assert.match(main, /getElementById\('year-badge'\)\?\.addEventListener\('click', \(\) => \{ void navigatorUi\?\.select\('jump'\)/, 'the year chip opens Jump (T-2626\'s #year-badge button)');
}

console.log('NAV JUMP PASS — three era cards, HERE on yours; a pick runs the ring and the transfer stamp, then the page; Escape aborts; RECALL the one red key');
