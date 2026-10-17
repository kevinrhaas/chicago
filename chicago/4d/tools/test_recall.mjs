// T-2735 — the way home (js/recall.js): "← All destinations" and Recall ask first, CANCEL
// or Esc leaves the scene as it was, RETURN plays the reverse ring and then goes, the
// journey moves to `recall` only as the page leaves, and reduced motion skips the ring.
//
//   node tools/test_recall.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRecall, pageYear, RECALL_MS, RECALL_KEY } from '../renderers/web/js/recall.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, '../renderers/web');

function fakeDom() {
  const winFns = {};
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), className: '', textContent: '', id: '', type: '', attrs: {}, children: [], parent: null,
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      removeAttribute(k) { delete this.attrs[k]; }, hasAttribute(k) { return k in this.attrs; },
      append(...cs) { for (let c of cs) { if (typeof c === 'string') c = { textContent: c, children: [] }; c.parent = el; el.children.push(c); } },
      remove() { if (el.parent) { el.parent.children.splice(el.parent.children.indexOf(el), 1); el.parent = null; } },
      addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
      focus() { doc.activeElement = el; },
      click(target = el) { const e = { target, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } }; for (const fn of fns.click ?? []) fn(e); return e; },
    };
    return el;
  };
  const doc = { createElement: make, activeElement: null };
  doc.body = make('body');
  doc.documentElement = make('html');
  const win = {
    addEventListener(type, fn, capture) { assert.equal(capture, true, 'the recall listens at window capture'); (winFns[type] ??= []).push(fn); },
    key(key) {
      const e = { key, stopped: false, prevented: false, stopImmediatePropagation() { this.stopped = true; }, preventDefault() { this.prevented = true; } };
      for (const fn of winFns.keydown ?? []) fn(e);
      return e;
    },
  };
  doc.activeElement = doc.body;
  return { doc, win };
}
const walk = (el, out = []) => { for (const c of el.children ?? []) { out.push(c); walk(c, out); } return out; };
const find = (doc, cls) => walk(doc.body).find((e) => String(e.className).split(' ').includes(cls));
const text = (el) => [el.textContent, ...(el.children ?? []).map(text)].join('');

function harness({ reduced = false, year = '1904' } = {}) {
  const { doc, win } = fakeDom();
  const timers = [];
  const went = [];
  const stored = new Map();
  let clock = 1000;
  const r = createRecall({
    doc, win, year, reduced: () => reduced, present: 2026,
    go: (href) => went.push(href),
    wait: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    cancel: (id) => { if (timers[id - 1]) timers[id - 1].fn = null; },
    storage: { setItem: (k, v) => stored.set(k, v) },
    now: () => clock, frame: () => 0,
  });
  const run = (ms) => { for (const t of timers.filter((x) => x.fn && x.ms <= ms)) { const f = t.fn; t.fn = null; f(); } };
  return { r, doc, win, timers, went, stored, run, tick: (ms) => { clock += ms; } };
}

// ---- the prompt asks first, and a no leaves everything as it was ----------------------
{
  const h = harness();
  const leaving = [];
  h.r.onReturn((href) => leaving.push(href));
  const opener = h.doc.createElement('a');
  h.doc.activeElement = opener;
  assert.equal(h.r.ask('../'), true);
  assert.equal(h.r.open, 'prompt');
  const shade = find(h.doc, 'recall-confirm');
  assert.ok(shade, 'the prompt is on screen');
  assert.equal(shade.getAttribute('role'), 'alertdialog');
  assert.equal(shade.getAttribute('aria-modal'), 'true');
  assert.match(text(shade), /Return to the Temporal Observatory\?/);
  assert.match(text(shade), /Chicago, 1904/, 'it says which destination you leave');
  assert.match(text(shade), /Temporal recall/);
  assert.doesNotMatch(text(shade), /[a-z0-9]+_[a-z0-9]+|\{|\}/i, 'no id, snake_case or unfilled placeholder');
  assert.ok(h.doc.documentElement.hasAttribute('data-recall-open'));
  const no = find(h.doc, 'recall-cancel'), yes = find(h.doc, 'recall-go');
  assert.equal(no.textContent, 'Cancel');
  assert.equal(yes.textContent, 'Return');
  assert.equal(h.doc.activeElement, no, 'the safe answer has the focus');
  assert.equal(h.r.ask('../'), false, 'one prompt at a time');
  // The prompt owns the keyboard: Tab stays on its two keys, nothing reaches the town.
  const tab = h.win.key('Tab');
  assert.ok(tab.stopped && tab.prevented);
  assert.equal(h.doc.activeElement, yes);
  h.win.key('Tab');
  assert.equal(h.doc.activeElement, no);
  const w = h.win.key('w');
  assert.ok(w.stopped, 'a walk key does not reach the controls under the prompt');
  assert.equal(w.prevented, false, 'but it is not cancelled outright');
  // CANCEL
  no.click();
  assert.equal(h.r.open, null);
  assert.equal(find(h.doc, 'recall-confirm'), undefined, 'the prompt goes');
  assert.ok(!h.doc.documentElement.hasAttribute('data-recall-open'));
  assert.equal(h.doc.activeElement, opener, 'focus goes back where it was');
  assert.deepEqual(h.went, [], 'nowhere was gone');
  assert.deepEqual(leaving, [], 'and the journey was never told');
  assert.equal(h.win.key('x').stopped, false, 'with the prompt gone the keyboard is the town\'s again');
  // Esc is a no too
  h.r.ask('../');
  assert.ok(h.win.key('Escape').prevented);
  assert.equal(h.r.open, null);
  // and so is a tap on the shade outside the card
  h.r.ask('../');
  const s2 = find(h.doc, 'recall-confirm');
  s2.click(s2);
  assert.equal(h.r.open, null);
  h.r.ask('../');
  const s3 = find(h.doc, 'recall-confirm');
  s3.click(find(h.doc, 'recall-card'));
  assert.equal(h.r.open, 'prompt', 'a tap on the card itself is not a no');
  h.r.close();
  assert.deepEqual(h.went, []);
  assert.equal(h.timers.length, 0, 'no ring was started');
}

// ---- RETURN: the reverse ring, then the Observatory -----------------------------------
{
  const h = harness();
  const leaving = [];
  h.r.onReturn((href) => leaving.push(href));
  h.r.ask('/4d/');
  find(h.doc, 'recall-go').click();
  assert.equal(find(h.doc, 'recall-confirm'), undefined, 'the prompt gives way to the ring');
  assert.equal(h.r.open, 'ring');
  const ring = find(h.doc, 'recall-ring');
  assert.ok(ring, 'the reverse ring is on screen');
  assert.equal(walk(ring).filter((e) => e.tagName === 'I' && /recall-ring-[ab]/.test(e.className)).length, 2, 'two rings, as on the way out');
  assert.match(text(find(h.doc, 'recall-ring-seq')), /Arrive.*Lock.*Scan/, 'the lamps read the outbound sequence backwards');
  assert.equal(find(h.doc, 'recall-ring-year').textContent, '1904', 'the readout starts at the destination year');
  const label = find(h.doc, 'recall-ring-label');
  assert.deepEqual(leaving, [], 'the journey moves only as the page leaves');
  h.run(400); assert.match(label.textContent, /rewinding/i);
  h.run(800); assert.match(label.textContent, /Observatory/);
  assert.deepEqual(h.went, []);
  h.tick(RECALL_MS);
  h.run(RECALL_MS);
  assert.deepEqual(h.went, ['/4d/'], 'then the page goes home');
  assert.deepEqual(leaving, ['/4d/'], 'telling the journey as it goes');
  assert.equal(h.stored.get(RECALL_KEY), String(1000 + RECALL_MS), 'and stamping the trip for the Observatory\'s tail');
  assert.ok(RECALL_MS <= 1200, 'the trip home is short and light');
}

// ---- Esc or Abort during the ring stays put; depart() skips the question --------------
{
  const h = harness();
  h.r.depart('../');
  assert.equal(find(h.doc, 'recall-confirm'), undefined, 'depart() asks nothing (the stalled jump has nothing to lose)');
  assert.equal(h.r.open, 'ring');
  assert.ok(h.win.key('Escape').prevented);
  assert.equal(h.r.open, null);
  assert.equal(find(h.doc, 'recall-ring'), undefined);
  h.run(RECALL_MS);
  assert.deepEqual(h.went, [], 'an aborted ring goes nowhere');
  assert.equal(h.stored.size, 0, 'and writes no stamp');
  h.r.depart('../');
  find(h.doc, 'recall-ring-abort').click();
  h.run(RECALL_MS);
  assert.deepEqual(h.went, []);
}

// ---- reduced motion keeps the question and skips the ring ------------------------------
{
  const h = harness({ reduced: true });
  h.r.ask('../');
  assert.ok(find(h.doc, 'recall-confirm'), 'the prompt still asks');
  find(h.doc, 'recall-go').click();
  assert.equal(find(h.doc, 'recall-ring'), undefined, 'no ring');
  assert.deepEqual(h.went, ['../'], 'straight home');
}

// ---- a page with no year still reads ---------------------------------------------------
{
  const h = harness({ year: null });
  h.r.ask('../');
  assert.match(text(find(h.doc, 'recall-confirm')), /this destination/);
  assert.doesNotMatch(text(find(h.doc, 'recall-confirm')), /null|undefined|\{/);
}

assert.equal(pageYear({ pathname: '/4d/1904/', search: '' }), '1904');
assert.equal(pageYear({ pathname: '/4d/dev/1835/index.html', search: '' }), '1835');
assert.equal(pageYear({ pathname: '/4d/walk/', search: '?year=1812' }), '1812');
assert.equal(pageYear({ pathname: '/4d/walk/', search: '' }), null);

// ---- the page wires it: its own module ahead of main.js, a stylesheet, the tail --------
{
  const index = readFileSync(path.join(web, 'index.html'), 'utf8');
  const at = (s) => index.indexOf(s);
  assert.ok(at('src="./js/recall.js"') > 0 && at('src="./js/recall.js"') < at('src="./js/main.js"'), 'recall.js loads ahead of main.js, so its key handler is first');
  assert.ok(at('href="./css/recall.css"') > 0, 'the prompt has its stylesheet');
  const main = readFileSync(path.join(web, 'js/main.js'), 'utf8');
  assert.doesNotMatch(main, /closest\?\.\('\.skin-tools a, #gate-observatory'\)\) journey\.recall\(\)/, 'the link no longer moves the journey on click');
  assert.match(main, /onReturn\(\(\) => journey\.recall\(\)\)/, 'the journey moves as the page leaves');
  const css = readFileSync(path.join(web, 'css/recall.css'), 'utf8');
  for (const skin of ['brass', 'worlds-fair', 'deep-space']) assert.ok(css.includes(`html[data-skin="${skin}"] .recall-card`), `${skin} dresses the prompt`);
  assert.match(css, /prefers-reduced-motion/);
  const skins = readFileSync(path.join(web, 'css/skins.css'), 'utf8');
  assert.match(skins, /html\[data-recall\]::after/, 'the Observatory picks up the ring\'s tail');
  const skinJs = readFileSync(path.join(web, 'js/skin.js'), 'utf8');
  assert.match(skinJs, /chicago4d\.recall/);
}

console.log('RECALL PASS — All destinations and Recall ask first; Cancel, Esc or a tap outside stay put; Return runs the reverse ring, stamps the trip and goes; Esc aborts the ring; reduced motion asks and skips the ring');
