#!/usr/bin/env node
// T-2661 (NAV-803): Guide's controls sheet — touch on a phone, keyboard and mouse on a
// laptop, read from controls/intent.js — replacing the control-help popover. No browser:
// the sheet is mounted over a small hand-made DOM; the smoke (parts 6 and 12) opens it in
// a page on both viewports.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { controlScheme } from '../renderers/web/js/controls/intent.js';
import { CONTROL_SHEETS, SCHEMES } from '../renderers/web/js/controls/sheet.js';
import { mount, shown, unmount } from '../renderers/web/js/apps/guide-view.js';
import GUIDE from '../renderers/web/js/apps/guide.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- a small DOM: elements, text nodes, attributes and clicks ---------------------------
function fakeDoc() {
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), className: '', id: '', type: '', dataset: {}, attrs: {}, children: [], parent: null, _text: '',
      get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
      set textContent(v) { this._text = String(v); this.children = []; },
      classList: {
        toggle(c, on) { const s = new Set(el.className.split(' ').filter(Boolean)); if (on) s.add(c); else s.delete(c); el.className = [...s].join(' '); },
        contains(c) { return el.className.split(' ').includes(c); },
      },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) {
        for (let c of cs) {
          if (typeof c === 'string') c = { nodeType: 3, textContent: c, children: [] };
          c.parent = el; el.children.push(c);
        }
      },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
      click() { for (const fn of fns.click ?? []) fn({ preventDefault() {} }); },
      get ownerDocument() { return doc; },
    };
    return el;
  };
  const doc = { createElement: make };
  return doc;
}
const all = (el, out = []) => { for (const c of el.children ?? []) { if (c.tagName) { out.push(c); all(c, out); } } return out; };
const find = (el, pred) => all(el).filter(pred);
const sheetOf = (panel) => find(panel, (e) => e.tagName === 'DL')[0];
const segButtons = (panel) => find(panel, (e) => e.tagName === 'BUTTON' && e.dataset.scheme);

// ---- the scheme comes from the controls in use ----------------------------------------------
assert.equal(controlScheme('touch'), 'touch');
assert.equal(controlScheme('pointerlock'), 'keyboard');
assert.equal(controlScheme('touch', false), 'touch', 'a tapped laptop is a touch screen for now');
assert.equal(controlScheme('pointerlock', true), 'keyboard', 'a phone with a keyboard typing is a keyboard');
assert.equal(controlScheme('none', true), 'touch', 'before either is live, the device guesses: a phone');
assert.equal(controlScheme('none', false), 'keyboard', '…and a laptop');
assert.equal(controlScheme(undefined), 'keyboard');
assert.deepEqual(SCHEMES, ['touch', 'keyboard']);

// ---- a phone shows touch, a laptop the keyboard ------------------------------------------
const doc = fakeDoc();
let listener = null;
const ctxFor = (controls, coarse) => ({ controls, coarse, actions: { onControls: (fn) => { listener = fn; return () => { listener = null; }; } } });

const phone = doc.createElement('div');
mount(phone, ctxFor('touch', true));
let dl = sheetOf(phone);
assert.equal(dl.dataset.scheme, 'touch', 'a phone shows the touch controls');
assert.equal(find(phone, (e) => e.id === 'guide-controls')[0]?.dataset.scheme, 'touch');
assert.equal(find(dl, (e) => e.tagName === 'KBD').length, 0, 'gestures are words, not keys');
assert.match(phone.textContent, /left thumb/i, 'the left thumb walks');
assert.match(phone.textContent, /right side/i, 'the right side looks');
assert.equal(find(dl, (e) => e.tagName === 'DT').length, CONTROL_SHEETS.touch.rows.length);
assert.deepEqual(segButtons(phone).map((b) => [b.textContent, b.getAttribute('aria-checked')]), [['Touch', 'true'], ['Keyboard', 'false']]);
assert.match(phone.textContent, /On this device/);
unmount(phone);
assert.equal(listener, null, 'unmount lets go of the controls switch');

const laptop = doc.createElement('div');
mount(laptop, ctxFor('pointerlock', false));
dl = sheetOf(laptop);
assert.equal(dl.dataset.scheme, 'keyboard', 'a laptop shows the keyboard controls');
const kbds = find(dl, (e) => e.tagName === 'KBD').map((k) => k.textContent);
for (const key of ['W', 'A', 'S', 'D', 'Shift', 'E', 'F', 'C', 'G', 'M', 'N', 'H', 'Esc']) assert(kbds.includes(key), `the keyboard sheet shows ${key}`);
assert.match(laptop.textContent, /N\s*open or close the Navigator/, 'N opens the Navigator, as T-2622 binds it');
assert.match(laptop.textContent, /1–9\s*open a Navigator app/);
// Words kept apart: a row's keys and its meaning never run together (the T-2655 lesson).
for (const [keys, does] of CONTROL_SHEETS.keyboard.rows) {
  assert(laptop.textContent.includes(` ${keys.join(' ')} ${does} `), `"${keys.join(' ')} ${does}" reads apart from its neighbours`);
}

// The controls change under it (a laptop's touch screen is tapped): it follows…
listener('touch');
assert.equal(sheetOf(laptop).dataset.scheme, 'touch', 'the sheet follows the live controls');
listener('pointerlock');
assert.equal(sheetOf(laptop).dataset.scheme, 'keyboard');
// …until the visitor picks a sheet themselves.
segButtons(laptop).find((b) => b.dataset.scheme === 'touch').click();
assert.equal(sheetOf(laptop).dataset.scheme, 'touch', 'a tap on Touch shows the touch sheet');
assert.match(laptop.textContent, /Your choice/);
listener('pointerlock');
assert.equal(sheetOf(laptop).dataset.scheme, 'touch', 'a picked sheet stays picked');
shown(laptop, ctxFor('pointerlock', false));
assert.equal(sheetOf(laptop).dataset.scheme, 'touch', '…when Guide opens again too');
unmount(laptop);
// A fresh mount starts from the controls again.
const again = doc.createElement('div');
mount(again, ctxFor('none', true));
assert.equal(sheetOf(again).dataset.scheme, 'touch');
shown(again, ctxFor('pointerlock', true));
assert.equal(sheetOf(again).dataset.scheme, 'keyboard', 'opening Guide reads the controls in use');
unmount(again);

// ---- the sheet holds every key the drawer's list names ------------------------------------
const html = read('renderers/web/index.html');
const a = html.indexOf('id="keys-desktop"');
const drawerKeys = [...html.slice(a, html.indexOf('</dl>', a)).matchAll(/<kbd>([^<]+)<\/kbd>/g)].map((m) => m[1]);
const sheetKeys = new Set(CONTROL_SHEETS.keyboard.rows.flatMap(([keys]) => keys)
  .flatMap((k) => (k === '1–9' ? ['1', '2', '3', '4', '5', '6', '7', '8', '9', k] : [k])));
const missing = drawerKeys.filter((k) => !sheetKeys.has(k));
assert.deepEqual(missing, [], `the Guide sheet lists every key the drawer does: missing ${missing.join(', ')}`);

// ---- the words: no ids, paths or snake_case; the locked term as it is ------------------------
const words = SCHEMES.flatMap((s) => [CONTROL_SHEETS[s].title, CONTROL_SHEETS[s].intro, ...CONTROL_SHEETS[s].rows.flat(2)]).join(' ');
assert(!/[a-z0-9]+_[a-z0-9]+|\.js\b|#[a-z]/i.test(words), words);
assert.match(words, /the Confidence view/, 'the locked term, exactly');
assert(!/confidence mode|confidence view/.test(words.replace(/Confidence view/g, '')), 'no other spelling of it');

// ---- the popover is gone, and Guide is a screen ----------------------------------------------
for (const gone of ['control-help', 'control-help-gotit', 'control-help-close', 'control-help-desktop', 'control-help-touch']) {
  assert(!html.includes(`id="${gone}"`), `#${gone} is gone from the page`);
}
assert(/id="s-show-control-help"[^>]*>Show the controls</.test(html), 'Settings still opens the controls, in Guide');
const hud = read('renderers/web/js/hud.js');
assert(!/\$\('control-help/.test(hud) && !/CONTROL_HELP_KEY/.test(hud), 'hud.js reads no popover');
assert(!/control-help/.test(read('renderers/web/css/walk.css')), 'and styles none');
assert.equal(typeof GUIDE.load, 'function', 'Guide loads its own screen');
assert.equal(GUIDE.launch, undefined, '…instead of opening the drawer');
assert.equal(GUIDE.pin, 'bottom', 'pinned to the foot of the rail');
const view = await GUIDE.load();
assert.equal(typeof view.mount, 'function');

console.log('test_nav_guide: touch on a phone, keyboard on a laptop, following the live controls; every drawer key listed; the popover gone');
