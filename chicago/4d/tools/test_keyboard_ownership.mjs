#!/usr/bin/env node
/** T-3658: real desktop capture + PointerLockControls/backend over a small event
 * fixture. No browser/world/GPU. Capture runs before a rail's target handler;
 * the backend runs after it. Native activation itself remains a browser check. */
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { createIntent } from '../renderers/web/js/controls/intent.js';
import { createDesktopKeyCapture, ownsKeyboard, worldKeyAllowed, isTyping } from '../renderers/web/js/controls/keyboard.js';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url);
const hooks = registerHooks({ resolve(specifier, context, next) {
  if (specifier === 'three') return { url: new URL('three.module.js', vendor).href, shortCircuit: true };
  if (specifier.startsWith('three/addons/')) return { url: new URL(specifier.slice(6), vendor).href, shortCircuit: true };
  return next(specifier, context);
} });
const { createPointerLockBackend } = await import('../renderers/web/js/controls/pointerlock.js');
hooks.deregister();

class Events {
  listeners = new Map();
  addEventListener(type, fn, options) {
    const list = this.listeners.get(type) ?? [];
    list.push({ fn, capture: options === true || !!options?.capture }); this.listeners.set(type, list);
  }
  removeEventListener(type, fn) { this.listeners.set(type, (this.listeners.get(type) ?? []).filter(row => row.fn !== fn)); }
  fire(type, event, capture = false) {
    for (const row of [...(this.listeners.get(type) ?? [])]) if (row.capture === capture) row.fn(event);
  }
}
const win = new Events(), doc = new Events();
globalThis.window = win;
class Element {
  constructor(tagName, parentElement = null, attrs = {}) {
    this.tagName = tagName.toUpperCase(); this.parentElement = parentElement; this.attrs = attrs; this.ownerDocument = doc;
  }
  get isContentEditable() { return this.attrs.contenteditable === true || !!this.parentElement?.isContentEditable; }
  matches(selector) {
    if (selector[0] === '#') return this.attrs.id === selector.slice(1);
    if (selector[0] === '.') return (this.attrs.class ?? '').split(' ').includes(selector.slice(1));
    const [, tag, attr, value] = /^(\w+)?(?:\[([\w-]+)(?:="([^"]*)")?\])?$/.exec(selector) ?? [];
    return (!tag || this.tagName === tag.toUpperCase()) && (!attr || (value === undefined ? attr in this.attrs : this.attrs[attr] === value));
  }
  closest(selectors) {
    for (let el = this; el; el = el.parentElement) if (selectors.split(',').some(s => el.matches(s.trim()))) return el;
    return null;
  }
  focus() { doc.activeElement = this; win.fire('focusin', { target: this }); }
}
globalThis.HTMLElement = Element;
const body = new Element('body'), canvas = new Element('canvas', body);
const nav = new Element('section', body, { id: 'navigator' });
const rail = new Element('button', nav, { role: 'tab' });
const reading = new Element('div', nav);
const inspect = new Element('div', nav, { id: 'nav-app-inspect' });
const inspectButton = new Element('button', inspect);
const popup = new Element('aside', body, { id: 'popup' });
const popupButton = new Element('button', popup), popupInput = new Element('input', popup);
const picture = new Element('div', popup, { class: 'pic-viewer', role: 'dialog' });
const pictureButton = new Element('button', picture);
const nativeDialog = new Element('dialog', popup);
const nativeDialogButton = new Element('button', nativeDialog);
let lockRequests = 0, activates = 0, holding = false, inspecting = false, enabled = true;
canvas.requestPointerLock = () => { lockRequests++; };
doc.exitPointerLock = () => {};
doc.activeElement = body;
const intent = createIntent();
const backend = createPointerLockBackend({ intent, domElement: canvas, holding: () => holding, inspecting: () => inspecting });
backend.enable();
const capture = createDesktopKeyCapture({ enabled: () => enabled, holding: () => holding, inspecting: () => inspecting,
  activate: () => { activates++; }, lock: () => backend.lock() });
win.addEventListener('keydown', capture, { capture: true });
const event = (code, target = doc.activeElement, extra = {}) => ({
  code, key: code === 'Space' ? ' ' : code, target, defaultPrevented: false,
  preventDefault() { this.defaultPrevented = true; }, ...extra,
});
function down(code, target, extra, targetHandler = () => {}) {
  const e = event(code, target, extra);
  win.fire('keydown', e, true); targetHandler(e); win.fire('keydown', e); backend.update(); return e;
}
function up(code, target, extra) { win.fire('keyup', event(code, target, extra)); backend.update(); }
function reset() {
  win.fire('blur', {}); intent.clear(); intent.flying = false;
  holding = inspecting = false; enabled = true; lockRequests = activates = 0; body.focus();
}
function still(message) {
  assert.deepEqual([intent.forward, intent.strafe, intent.rise, intent.sprint, intent.interact], [0, 0, 0, false, false], message);
}

// Before the fix: this actual capture/backend path requested one lock and set
// forward=-1 on ArrowDown; Space then set interact=true and prevented default.
rail.focus();
down('ArrowDown', rail, {}, e => e.preventDefault());
assert.equal(lockRequests, 0, 'rail capture must stand down before the rail can handle its arrow');
assert.equal(activates, 0, 'UI keys do not switch a touch user into keyboard/mouse'); still('rail arrow does not walk');
assert.equal(down('Space', rail).defaultPrevented, false, 'Space reaches the native button default'); still('rail Space does not inspect');

for (const target of [reading, popupButton, pictureButton, nativeDialog, nativeDialogButton, new Element('button', body),
  new Element('a', body, { href: '/source' }), new Element('summary', body),
  new Element('div', body, { role: 'slider' }), new Element('input', body),
  new Element('textarea', body), new Element('select', body), new Element('div', body, { contenteditable: true })]) {
  reset(); target.focus();
  assert.equal(ownsKeyboard(target), true);
  for (const code of ['ArrowUp', 'ArrowDown', 'KeyW', 'KeyQ', 'KeyE', 'Space', 'ShiftLeft']) {
    assert.equal(down(code, target).defaultPrevented, false, `${target.tagName} owns ${code}`);
    still(`${target.tagName} keeps movement and inspect`);
  }
  assert.equal(lockRequests, 0); assert.equal(activates, 0);
}
assert.equal(ownsKeyboard({ nodeType: 3, parentElement: reading }), true, 'text-node events inherit their reader');
assert.equal(isTyping(rail), false, 'UI ownership did not turn every control into a text field');
assert.equal(isTyping(popupInput), true);
assert.equal(isTyping(new Element('span', new Element('div', body, { contenteditable: true }))), true);

// A Navigator remains in the document and can be visible while focus is world-owned.
reset(); canvas.focus();
assert.equal(down('KeyW', canvas).defaultPrevented, true); assert.equal(lockRequests, 1); assert.equal(intent.forward, 1);
up('KeyW', canvas); still('W release stops');
down('ArrowLeft', body); assert.equal(intent.strafe, -1); up('ArrowLeft', body);
assert.equal(down('Space', body).defaultPrevented, true); assert.equal(intent.takeInteract().source, 'key');
down('KeyE', body); assert.equal(intent.takeInteract().source, 'key');
intent.flying = true; down('Space', body); assert.equal(intent.rise, 1); up('Space', body); assert.equal(intent.rise, 0);
down('KeyQ', body); assert.equal(intent.rise, -1); up('KeyQ', body);

// Already-handled events/modifiers/IME must be rejected by both capture and backend.
for (const extra of [{ defaultPrevented: true }, { metaKey: true }, { ctrlKey: true }, { altKey: true }, { isComposing: true }]) {
  reset(); down('KeyW', body, extra); down('Space', body, extra); still('handled key remains handled');
  assert.equal(lockRequests, 0); assert.equal(activates, 0);
}
reset(); down('KeyW', body, {}, e => e.preventDefault()); still('backend respects a later preventDefault');
// Capture cannot foresee a later world handler; UI ownership protects before that phase.
assert.equal(lockRequests, 1);

// Focus transfer immediately releases keys already held and any pending key inspect.
reset(); intent.flying = true;
down('KeyW', body); down('ShiftLeft', body); down('Space', body);
assert.equal(intent.forward, 1); assert.equal(intent.sprint, true); assert.equal(intent.rise, 1);
reading.focus(); still('focus stops already-held motion without waiting for keyup');
body.focus(); backend.update(); still('returning focus does not resurrect old keys');
up('KeyW', reading, { defaultPrevented: true }); up('Space', reading); up('ShiftLeft', reading);
reset(); down('KeyE', body); reading.focus(); still('queued inspect is dropped when UI takes focus');
// A focus handler installed after focus has moved is also safe on the next frame.
reset(); down('KeyW', body); doc.activeElement = rail; backend.update(); still('active reader catches a missed focus event');

// Keep the established E-to-close card contract; text, other apps and modals retain E.
reset(); holding = true;
for (const target of [body, popup, popupButton]) {
  target.focus(); assert.equal(down('KeyE', target).defaultPrevented, true);
  assert.equal(intent.takeInteract().source, 'key');
  assert.equal(down('Space', target).defaultPrevented, false); still('Space belongs to an open card');
}
for (const target of [popupInput, pictureButton, nativeDialog, nativeDialogButton, rail]) {
  target.focus(); assert.equal(down('KeyE', target).defaultPrevented, false); still('text/dialog/other app keeps E');
}
assert.equal(lockRequests, 0);
reset(); inspecting = true; inspectButton.focus();
assert.equal(down('KeyE', inspectButton).defaultPrevented, true); assert.equal(intent.takeInteract().source, 'key');
assert.equal(down('Space', inspectButton).defaultPrevented, false); still('Navigator Inspect button retains Space');
rail.focus(); assert.equal(down('KeyE', rail).defaultPrevented, false);
body.focus(); down('KeyW', body); assert.equal(intent.forward, 1, 'visible Inspect does not disable world focus'); up('KeyW', body);
reset(); inspectButton.focus(); assert.equal(down('KeyE', inspectButton).defaultPrevented, false, 'automatic Inspect is not an E-to-close card');

// Arrival/XR/window mode can disable desktop activation without disturbing UI keys.
reset(); enabled = false; capture(event('ArrowUp', body)); assert.equal(activates, 0); assert.equal(lockRequests, 0);
assert.equal(worldKeyAllowed(event('KeyE', popupInput), { holding: true }), false);
backend.disable(); assert.equal((win.listeners.get('focusin') ?? []).length, 0, 'no focus listener leaked');
backend.enable(); assert.equal((win.listeners.get('focusin') ?? []).length, 1);
backend.dispose(); win.removeEventListener('keydown', capture);
console.log('Keyboard ownership PASS — actual capture/backend, UI arrows/Space, world controls, focus transfer, prevented keys, popup/Inspect E, lifecycle.');
