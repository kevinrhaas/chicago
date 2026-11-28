#!/usr/bin/env node
/** Cloud play's drag look (js/controls/pointerlock.js, `dragLook`; the owner, 2026-11-27: "the
 * mouse movements do not seem to work, I could not look around"). A streamed browser cannot pass
 * the pointer lock through to the player's own browser, so under ?look=drag the look is a drag
 * with the left button held: it turns the view the way the mouse does under lock, never asks for
 * a lock, and a press that did not drag stays a click. Over a small event fixture, no browser. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { registerHooks } from 'node:module';
import { createIntent } from '../renderers/web/js/controls/intent.js';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url);
const hooks = registerHooks({ resolve(specifier, context, next) {
  if (specifier === 'three') return { url: new URL('three.module.js', vendor).href, shortCircuit: true };
  if (specifier.startsWith('three/addons/')) return { url: new URL(specifier.slice(6), vendor).href, shortCircuit: true };
  return next(specifier, context);
} });
const { createPointerLockBackend, DRAG_SLOP_PX, DRAG_RAD_PER_PX } = await import('../renderers/web/js/controls/pointerlock.js');
hooks.deregister();

class Events {
  listeners = new Map();
  addEventListener(type, fn) { const l = this.listeners.get(type) ?? []; l.push(fn); this.listeners.set(type, l); }
  removeEventListener(type, fn) { this.listeners.set(type, (this.listeners.get(type) ?? []).filter((f) => f !== fn)); }
  fire(type, e) { for (const fn of [...(this.listeners.get(type) ?? [])]) fn(e); }
  count(type) { return (this.listeners.get(type) ?? []).length; }
}
const win = new Events(), doc = new Events();
globalThis.window = win;
doc.activeElement = null;
doc.exitPointerLock = () => {};
const canvas = { ownerDocument: doc, tagName: 'CANVAS', requestPointerLock() { locks++; }, closest: () => null, matches: () => false };
let locks = 0, engaged = 0;

function backendWith(dragLook) {
  const intent = createIntent();
  const b = createPointerLockBackend({ intent, domElement: canvas, dragLook, onDragLook: () => { engaged++; } });
  b.enable();
  return { intent, b };
}
const press = (x, y) => win.fire('pointerdown', { button: 0, buttons: 1, target: canvas, clientX: x, clientY: y });
const move = (x, y, buttons = 1) => win.fire('pointermove', { buttons, target: canvas, clientX: x, clientY: y });
const release = () => win.fire('pointerup', { button: 0, buttons: 0, target: canvas });

// Drag look on.
{
  const { intent, b } = backendWith(true);
  b.lock();
  assert.equal(locks, 0, 'drag look never asks for the pointer lock');
  press(100, 100);
  move(100 + DRAG_SLOP_PX - 1, 100);
  assert.equal(intent.yawDelta, 0, 'a press that wanders less than the slop does not turn');
  move(150, 120);
  assert.ok(intent.yawDelta < 0 && intent.pitchDelta < 0, 'dragging right and down turns right and looks down, as the mouse does under lock');
  assert.ok(Math.abs(intent.yawDelta + 50 * DRAG_RAD_PER_PX) < 1e-9, 'the turn is the mouse\'s own per pixel at sensitivity 1');
  assert.equal(engaged, 1, 'the first drag engages the look (the tag goes)');
  release();
  assert.equal(b.dragged, true, 'the click that ends a drag is known as a drag');
  intent.yawDelta = intent.pitchDelta = 0;
  move(300, 300, 0);
  assert.equal(intent.yawDelta, 0, 'moving with no button held does not turn');
  press(200, 200); release();
  assert.equal(b.dragged, false, 'a press without a drag stays a click');
  press(10, 10); move(80, 10, 0);
  assert.equal(intent.yawDelta, 0, 'a button let go outside the page ends the drag');
  win.fire('pointerdown', { button: 0, buttons: 1, target: { closest: () => null }, clientX: 0, clientY: 0 }); move(90, 0);
  assert.equal(intent.yawDelta, 0, 'a press on the page\'s own controls does not drag the view');
  b.disable();
  assert.equal(win.count('pointermove'), 0, 'disabling lets go of the drag listeners');
}
// Drag look off: the desktop is as it was.
{
  const { intent, b } = backendWith(false);
  b.lock();
  assert.equal(locks, 1, 'without it a click still takes the pointer lock');
  press(100, 100); move(200, 100);
  assert.equal(intent.yawDelta, 0, 'and a drag does nothing');
  b.disable();
}
// The wiring: the town reads ?look=drag, its clicks pick, and the cloud machine asks for it.
const main = fs.readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
assert.ok(/dragLook: params\.get\('look'\) === 'drag'/.test(main), 'the town takes drag look from ?look=drag');
assert.ok(/if \(pointerlock\.dragLook\) \{\s*if \(pointerlock\.dragged\) return;/.test(main), 'the end of a drag is not a click; a plain click picks what is under it');
assert.ok(/tag\.textContent = 'Drag to look around'/.test(main), 'the tag says to drag');
assert.ok(/"Drag to look around": "Arrastra para mirar alrededor"/.test(fs.readFileSync(new URL('../renderers/web/js/strings/es/text.js', import.meta.url), 'utf8')), 'and says it in Spanish');
assert.ok(/URL="\$URL\?look=drag"/.test(fs.readFileSync(new URL('./stream/machine/session.sh', import.meta.url), 'utf8')), 'the cloud machine opens the year with drag look');

console.log('test_drag_look: under ?look=drag the view turns by dragging, no lock is asked for, a plain click stays a click');
