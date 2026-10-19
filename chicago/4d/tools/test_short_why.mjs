#!/usr/bin/env node
// T-2658 (NAV-904): Short "Why?". Every "Why this default" becomes, for a visitor, one line
// saying what the default is and a "Why?" button that opens a bubble of 40 words at most;
// the full essay is Researcher mode's, under "Why this default". This reads, with no
// browser: the page's markup for every essay, the string table's words, the bubble's
// placement arithmetic at the phone and laptop sizes, its open / close wiring on a stand-in
// page (tap, click, keyboard, Escape, outside tap), and the stylesheet's reduced-motion and
// skin rules. The rendered page is the smoke's, part 13.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { placeTip, wireWhyTips, wordCount, TIP_ID, GUTTER } from '../renderers/web/js/why-tips.js';
import { t } from '../renderers/web/js/strings/index.js';
import '../renderers/web/js/strings/research.js';
import { visitorTextProblems } from '../renderers/web/js/fallback-summary.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers', 'web');
const read = (p) => fs.readFileSync(path.join(WEB, p), 'utf8');
const page = read('index.html');
const unescape = (s) => s.replace(/&rsquo;/g, '’').replace(/&amp;/g, '&').replace(/&#39;/g, "'");

// ---- every "Why this default" on the page, and nothing left as a visitor's essay ----------
// The page is the only place the Settings and Move screens' essays live (grep: `Why this
// default` appears in renderers/web only in index.html's three folds); a fourth fold, or one
// that is not Researcher mode's, fails here.
const folds = page.split('<details class="why"').length - 1;
assert.equal(folds, 3, `three "Why this default" folds on the page (found ${folds})`);
const SETTINGS = { eye: ['s-eye', 'eye-note'], brightness: ['s-brightness', 'brightness-note'], road: ['s-road-aid', 'road-aid-note'] };
const blocks = [...page.matchAll(/<input type="range" id="(s-[\w-]+)"[^>]*><\/label>\s*<!--(?:(?!-->)[\s\S])*-->\s*<div class="why-line" data-visitor-only>([\s\S]*?)<\/div>\s*<details class="why" data-researcher><summary>Why this default<\/summary>\s*<p class="legend-note why-full" id="([\w-]+)" data-researcher>([\s\S]*?)<\/p>\s*<\/details>/g)];
assert.equal(blocks.length, 3, 'each fold sits directly under its slider, after a visitor\'s one line and "Why?"');
const seen = new Set();
for (const [, input, line, fullId, full] of blocks) {
  const key = Object.keys(SETTINGS).find((k) => SETTINGS[k][0] === input);
  assert.ok(key, `${input} is a researched setting`);
  assert.equal(SETTINGS[key][1], fullId, `${input}'s full essay keeps its id #${fullId}`);
  seen.add(key);
  const hint = line.match(/<span class="why-hint" data-str="(research\.hint\.\w+)">([^<]*)<\/span>/);
  assert.ok(hint, `${key}: a one-line hint from the string table`);
  assert.equal(unescape(hint[2]), t(hint[1]), `${key}: the hint paints the table's words`);
  assert.ok(wordCount(t(hint[1])) <= 8 && t(hint[1]).length <= 44, `${key}: the hint fits one line on a phone (${t(hint[1]).length} characters)`);
  const btn = line.match(/<button type="button" class="why-btn" id="(why-\w+)" data-why="([\w-]+)" data-str="research\.why\.ask" data-str-label="(research\.why\.ask\.\w+)" aria-label="([^"]+)">Why\?<\/button>/);
  assert.ok(btn, `${key}: a "Why?" button, a real <button> a keyboard reaches`);
  assert.equal(t('research.why.ask'), 'Why?');
  assert.equal(btn[4], t(btn[3]), `${key}: the button says what it explains to a screen reader`);
  const text = line.match(new RegExp(`<span class="why-text" id="${btn[2]}" hidden data-str="(research\\.why\\.\\w+)">([^<]*)</span>`));
  assert.ok(text, `${key}: the button names the bubble's words, held hidden beside it`);
  assert.equal(unescape(text[2]), t(text[1]), `${key}: the bubble paints the table's words`);
  const n = wordCount(t(text[1]));
  assert.ok(n <= 40, `${key}: the bubble is ${n} words (40 at most)`);
  assert.ok(wordCount(full) > 40, `${key}: the full essay, longer, is kept for Researcher mode`);
  for (const s of [t(hint[1]), t(text[1]), t(btn[3])]) assert.deepEqual(visitorTextProblems(s), [], `${key}: "${s}" carries no id, path or ticket`);
  for (const id of [input, fullId, btn[1], btn[2]]) assert.equal(page.split(`id="${id}"`).length, 2, `#${id} is on the page once`);
}
assert.equal(seen.size, 3, 'eye height, brightness and road visibility each have one');
assert.doesNotMatch(page, /id="why-tip"/, 'the bubble is made once, on the body, by js/why-tips.js');

// ---- where the bubble goes --------------------------------------------------------------
{
  const phone = { w: 390, h: 780 };
  const btn = { left: 310, right: 358, top: 300, bottom: 328 };
  const size = { w: Math.min(300, phone.w - 2 * GUTTER), h: 120 };
  const at = placeTip(btn, size, phone);
  assert.equal(at.side, 'below', 'below the button when there is room');
  assert.equal(at.top, 336, 'a small gap under it');
  assert.equal(at.left + size.w, 358, 'its right edge on the button\'s');
  const low = placeTip({ ...btn, top: 700, bottom: 728 }, size, phone);
  assert.equal(low.side, 'above', 'above it near the bottom of the screen');
  assert.ok(low.top >= GUTTER && low.top + size.h <= 700, 'and clear of the button');
  const left = placeTip({ left: 20, right: 60, top: 100, bottom: 128 }, size, phone);
  assert.equal(left.left, GUTTER, 'never past the left gutter');
  const tall = placeTip(btn, { w: 358, h: 2000 }, phone);
  assert.ok(tall.top >= GUTTER && tall.left >= GUTTER, 'a bubble taller than the window is held inside it (it scrolls)');
  for (const view of [phone, { w: 390, h: 844 }, { w: 1440, h: 900 }, { w: 1280, h: 800 }]) {
    for (const y of [40, view.h / 2, view.h - 60]) {
      for (const x of [16, view.w / 2, view.w - 16]) {
        const w = Math.min(300, view.w - 2 * GUTTER);
        const p = placeTip({ left: x - 40, right: x, top: y, bottom: y + 28 }, { w, h: 140 }, view);
        assert.ok(p.left >= GUTTER && p.left + w <= view.w - GUTTER && p.top >= GUTTER && p.top + 140 <= view.h - GUTTER,
          `${view.w}x${view.h}: a bubble for a button at ${x},${y} is inside the window`);
      }
    }
  }
}

// ---- opening and closing it, on a stand-in page -------------------------------------------
function fakePage() {
  const listeners = { doc: [], win: [] };
  const on = (bag) => (type, fn, opt) => bag.push({ type, fn, capture: opt === true || !!opt?.capture });
  const make = (tag) => {
    const el = {
      tagName: tag.toUpperCase(), id: '', className: '', hidden: false, textContent: '', isConnected: true,
      style: {}, dataset: {}, attrs: new Map(), handlers: [], children: [], offsetHeight: 90, focused: 0,
      rect: { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 },
      setAttribute(k, v) { this.attrs.set(k, String(v)); }, getAttribute(k) { return this.attrs.get(k) ?? null; },
      addEventListener(type, fn) { this.handlers.push({ type, fn }); },
      contains(x) { return x === this; }, getBoundingClientRect() { return this.rect; }, focus() { this.focused++; },
      append(c) { this.children.push(c); byId.set(c.id, c); },
    };
    return el;
  };
  const byId = new Map();
  const body = make('body');
  const buttons = [];
  for (const [i, k] of ['eye', 'road'].entries()) {
    const b = make('button'); b.id = `why-${k}`; b.dataset.why = `why-${k}-text`;
    b.rect = { left: 300, right: 350, top: 200 + i * 200, bottom: 228 + i * 200, width: 50, height: 28 };
    const s = make('span'); s.id = `why-${k}-text`; s.hidden = true; s.textContent = `  The ${k} reason,\n  in a few words. `;
    byId.set(b.id, b); byId.set(s.id, s); buttons.push(b);
  }
  const win = { innerWidth: 390, innerHeight: 780, addEventListener: on(listeners.win) };
  const doc = { body, defaultView: win, getElementById: (id) => byId.get(id) ?? null, createElement: make,
    querySelectorAll: (sel) => (sel === 'button.why-btn[data-why]' ? buttons : []), addEventListener: on(listeners.doc) };
  const fire = (bag, type, e) => { for (const l of bag) if (l.type === type) l.fn(e); };
  const click = (b) => { fire(listeners.doc, 'pointerdown', { target: b }); for (const h of b.handlers) if (h.type === 'click') h.fn({ stopPropagation() {} }); };
  const key = (k, target = body) => { const e = { key: k, target, stopped: false, prevented: false,
    stopPropagation() { this.stopped = true; }, preventDefault() { this.prevented = true; } }; fire(listeners.win, 'keydown', e); return e; };
  return { doc, win, body, buttons, listeners, click, key, tap: (target) => fire(listeners.doc, 'pointerdown', { target }), fire };
}
{
  const p = fakePage();
  const tips = wireWhyTips(p.doc);
  const tip = p.doc.getElementById(TIP_ID);
  assert.ok(tip && tip.hidden, 'one bubble on the body, hidden');
  assert.equal(tip.getAttribute('role'), 'status', 'read out when it opens');
  const [eye, road] = p.buttons;
  assert.equal(eye.getAttribute('aria-controls'), TIP_ID);
  assert.equal(eye.getAttribute('aria-expanded'), 'false');
  p.click(eye);
  assert.equal(tip.hidden, false, 'a tap or click on "Why?" opens it');
  assert.equal(tip.textContent, 'The eye reason, in a few words.', 'with that setting\'s words');
  assert.equal(eye.getAttribute('aria-expanded'), 'true');
  assert.equal(tips.openFor, eye);
  assert.equal(tip.style.top, '236px', 'under its button');
  assert.ok(p.listeners.doc.some((l) => l.type === 'pointerdown' && l.capture), 'outside taps are heard before anything else takes them');
  p.tap(tip);
  assert.equal(tip.hidden, false, 'a tap on the bubble itself leaves it open');
  p.click(eye);
  assert.equal(tip.hidden, true, 'the button again closes it');
  assert.equal(eye.getAttribute('aria-expanded'), 'false');
  p.click(eye);
  p.tap(p.body);
  assert.equal(tip.hidden, true, 'a tap anywhere else closes it');
  p.click(eye);
  p.click(road);
  assert.equal(tips.openFor, road, 'another "Why?" moves it');
  assert.equal(tip.textContent, 'The road reason, in a few words.');
  assert.equal(eye.getAttribute('aria-expanded'), 'false', 'and the first button says it is closed');
  assert.equal(p.key('Enter', road).stopped, false);
  assert.equal(tip.hidden, false, 'Enter on its own button is the button\'s (it toggles by click)');
  assert.equal(p.key('Shift', road).stopped, false);
  assert.equal(tip.hidden, false, 'a modifier key leaves it');
  const esc = p.key('Escape', road);
  assert.equal(tip.hidden, true, 'Escape closes it');
  assert.ok(esc.stopped && esc.prevented, 'and goes no further, so the Navigator stays open');
  assert.equal(road.focused, 1, 'focus is back on its button');
  assert.equal(p.key('Escape').stopped, false, 'with no bubble open, Escape is everyone else\'s');
  p.click(eye);
  p.key('Tab', eye);
  assert.equal(tip.hidden, true, 'moving on with the keyboard closes it');
  p.click(eye);
  eye.rect = { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 };
  p.fire(p.listeners.doc, 'scroll', {});
  assert.equal(tip.hidden, true, 'a button that is no longer drawn (Researcher mode, a closed screen) takes its bubble with it');
  const none = wireWhyTips(null);
  none.open(); none.close();
  assert.equal(none.openFor, null, 'no page: no throw');
}

// ---- reduced motion and the four machines ------------------------------------------------
{
  const walk = read('css/walk.css');
  const drawer = read('css/drawer.css');
  const rule = (css, sel) => css.match(new RegExp(`(^|\\n)${sel.replace(/[.[\]"=]/g, '\\$&')} \\{([^}]*)\\}`))?.[2] ?? '';
  const tipCss = rule(walk, '.why-tip');
  assert.match(walk, /@media \(prefers-reduced-motion: reduce\) \{ \.why-tip \{ animation: none; \} \}/, 'the bubble does not fade in under reduced motion');
  assert.match(drawer, /@media \(prefers-reduced-motion: reduce\) \{ \.why-btn \{ transition: none; \} \}/, 'nor does the button');
  // Every colour and corner is a skin token, so each of the four machines (css/skins.css)
  // dresses the bubble and the button in its own panel, ink, accent and corner.
  const btnCss = rule(drawer, '.why-btn');
  for (const [name, css] of [['bubble', tipCss], ['button', btnCss], ['line', rule(drawer, '.why-hint')]]) {
    assert.ok(css, `the ${name} has its rule`);
    assert.doesNotMatch(css, /#[0-9a-f]{3,8}\b|rgba?\(/i, `the ${name} names no colour of its own`);
  }
  assert.match(tipCss, /var\(--panel-solid\)/); assert.match(tipCss, /var\(--accent\)/); assert.match(tipCss, /var\(--ink\)/);
  assert.match(tipCss, /var\(--text-scale, 1\)/, 'and grows with Settings › Text size');
  const skins = read('css/skins.css');
  for (const skin of ['control-room', 'brass', 'worlds-fair', 'deep-space']) {
    const block = skins.match(new RegExp(`html\\[data-skin="${skin}"\\] \\{([^}]*)\\}`))?.[1] ?? '';
    for (const token of ['--panel-solid', '--ink', '--ink-dim', '--accent', '--accent-ink']) assert.ok(block.includes(`${token}:`), `${skin} sets ${token}`);
  }
  assert.match(drawer, /@media \(pointer: coarse\) \{ \.why-btn \{ min-height: 32px; min-width: 48px; \} \}/, 'a finger-sized target on a touch screen');
  const main = fs.readFileSync(path.join(WEB, 'js', 'main.js'), 'utf8');
  assert.ok(main.indexOf('applyStrings(document);') < main.indexOf('api.whyTips = wireWhyTips(document);'), 'wired after the page has the table\'s words');
}

console.log('SHORT WHY PASS — three researched settings, each one line and a "Why?" bubble of 40 words at most that opens by tap, click or key and closes on Escape or an outside tap; the full essay is Researcher mode\'s');
