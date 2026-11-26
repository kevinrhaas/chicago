#!/usr/bin/env node
/**
 * T-3749 — a game controller (renderers/web/js/controls/gamepad.js) and its wiring.
 *
 * Holds the pure half to its rules (the round dead zone, the look curve, reading a Standard
 * Gamepad, a resting pad is no takeover, one push one edge, the menu direction and its key
 * repeat, the most recently used pad, spatial focus), drives the backend against a stand-in
 * pad and page (a stick takes over from the live backend and walks; the right stick looks at
 * Settings › Look sensitivity; the trigger runs on foot and climbs in the air; A inspects; the
 * buttons press the keyboard's own keys and never switch the keyboard backend on; a menu stops
 * the walk; a headset pauses it), and reads main.js, sheet.js and walk.css for the wiring. The
 * real page, with a real focus ring and real keys, is driven by the smoke's controller pass.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const at = (p) => import(pathToFileURL(path.join(web, p)).href);
const gp = await at('js/controls/gamepad.js');
const { createIntent, createBackendSwitch, controlScheme } = await at('js/controls/intent.js');
const { createDesktopKeyCapture, padEvents } = await at('js/controls/keyboard.js');
const { CONTROL_SHEETS, SCHEMES } = await at('js/controls/sheet.js');
const main = await readFile(path.join(web, 'js/main.js'), 'utf8');
const css = await readFile(path.join(web, 'css/walk.css'), 'utf8');

// keyboard.js asks `instanceof HTMLElement`; node has no DOM.
globalThis.HTMLElement ??= class HTMLElement {};

const checks = [];
function check(name, run) { run(); checks.push(name); }
const near = (a, b, eps = 1e-9) => Math.abs(a - b) <= eps;
const { BUTTON } = gp;

/** A Standard Gamepad: four axes, seventeen buttons. */
function pad({ axes = [0, 0, 0, 0], down = [], values = {}, index = 0, timestamp = 1 } = {}) {
  const buttons = Array.from({ length: 17 }, (_, i) => {
    const value = values[i] ?? (down.includes(i) ? 1 : 0);
    return { pressed: down.includes(i) || value > 0.5, value };
  });
  return { index, id: 'Test pad (STANDARD GAMEPAD)', mapping: 'standard', connected: true, timestamp, axes, buttons };
}

check('the dead zone is round, and the rest of the throw is rescaled to the rim', () => {
  assert.deepEqual(gp.radial(0.1, 0.1), [0, 0]);
  assert.deepEqual(gp.radial(0, 0), [0, 0]);
  const [x, y] = gp.radial(0, -1);
  assert.ok(near(x, 0) && near(y, -1));
  const [hx] = gp.radial(gp.STICK_DEAD + (1 - gp.STICK_DEAD) / 2, 0);
  assert.ok(near(hx, 0.5));
  const [dx, dy] = gp.radial(Math.SQRT1_2, Math.SQRT1_2);
  assert.ok(near(Math.hypot(dx, dy), 1, 1e-6) && near(dx, dy), 'a diagonal keeps its direction');
});

check('the look curve is fine at the centre and full at the rim, sign kept', () => {
  assert.equal(gp.curve(0), 0);
  assert.equal(gp.curve(1), 1);
  assert.equal(gp.curve(-1), -1);
  assert.ok(gp.curve(0.5) < 0.5 && gp.curve(0.5) > 0);
  assert.equal(gp.curve(2), 1);
});

check('a Standard Gamepad reads as sticks, triggers and pressed buttons; a resting one is no takeover', () => {
  const s = gp.readPad(pad({ axes: [0.05, -0.08, 0.02, 0.01] }));
  assert.equal(s.pressed.length, 17);
  assert.ok(!gp.inUse(s), 'stick drift inside the dead zone does not take over');
  assert.ok(gp.inUse(gp.readPad(pad({ axes: [0, -1, 0, 0] }))));
  assert.ok(gp.inUse(gp.readPad(pad({ down: [BUTTON.A] }))));
  const t = gp.readPad(pad({ values: { [BUTTON.RT]: 0.7, [BUTTON.LT]: 0.2 } }));
  assert.ok(near(t.rt, 0.7) && near(t.lt, 0.2));
  assert.ok(gp.inUse(t));
  assert.ok(!gp.inUse(gp.readPad(pad({ values: { [BUTTON.LT]: 0.2 } }))), 'a resting trigger is not a press');
  assert.equal(gp.readPad(null).pressed.length, 17, 'no pad reads as nothing pressed');
});

check('one push is one edge', () => {
  const a = gp.readPad(pad({ down: [BUTTON.A] })).pressed;
  assert.equal(gp.edges([], a)[BUTTON.A], true);
  assert.equal(gp.edges(a, a)[BUTTON.A], false);
});

check('a menu direction comes from the D-pad first, then the stick past half way', () => {
  assert.equal(gp.direction(gp.readPad(pad({ down: [BUTTON.DOWN] }))), 'down');
  assert.equal(gp.direction(gp.readPad(pad({ down: [BUTTON.LEFT], axes: [1, 0, 0, 0] }))), 'left');
  assert.equal(gp.direction(gp.readPad(pad({ axes: [0.9, 0.2, 0, 0] }))), 'right');
  assert.equal(gp.direction(gp.readPad(pad({ axes: [0.1, -0.95, 0, 0] }))), 'up');
  assert.equal(gp.direction(gp.readPad(pad({ axes: [0.3, 0.3, 0, 0] }))), null);
});

check('a held direction fires on the push, waits, then repeats steadily', () => {
  let r = gp.repeat(null, 'down', 0.016);
  assert.ok(r.fire);
  let fired = 0;
  for (let t = 0; t < gp.REPEAT_FIRST - 0.02; t += 0.016) { r = gp.repeat(r.state, 'down', 0.016); fired += r.fire; }
  assert.equal(fired, 0, 'no repeat before the pause');
  for (let t = 0; t < 1; t += 0.016) { r = gp.repeat(r.state, 'down', 0.016); fired += r.fire; }
  assert.ok(fired >= 6 && fired <= 9, `about one every ${gp.REPEAT_EVERY}s: ${fired}`);
  assert.ok(gp.repeat(r.state, 'up', 0.016).fire, 'a new direction fires at once');
  assert.ok(!gp.repeat(r.state, null, 0.016).fire);
});

check('the pad read is the one in use, else the one used last', () => {
  const a = pad({ index: 0, timestamp: 5 }), b = pad({ index: 1, timestamp: 9, axes: [0, -1, 0, 0] });
  assert.equal(gp.pickPad([a, b]).index, 1);
  assert.equal(gp.pickPad([a, pad({ index: 1 })], 1).index, 1);
  assert.equal(gp.pickPad([null, a]).index, 0);
  assert.equal(gp.pickPad([]), null);
});

check('spatial focus walks a column before stepping off to the side, and never backwards', () => {
  const box = (l, t, w = 100, h = 30) => ({ left: l, top: t, right: l + w, bottom: t + h });
  const from = box(0, 0);
  const rects = [box(0, 40), box(140, 10), box(0, 200), box(0, -60)];
  assert.equal(gp.nearest(from, rects, 'down'), 0);
  assert.equal(gp.nearest(from, rects, 'right'), 1);
  assert.equal(gp.nearest(from, rects, 'up'), 3);
  assert.equal(gp.nearest(from, rects, 'left'), -1);
  // A tall key beside a short one: down goes to the key below, not the one beside it.
  assert.equal(gp.nearest(box(0, 0, 100, 30), [box(110, 5, 100, 60), box(0, 50)], 'down'), 1);
});

// ---- the backend, against a stand-in pad and page --------------------------------------- //

function harness({ gate = false, menu = false, paused = false } = {}) {
  const intent = createIntent();
  const backends = createBackendSwitch(intent);
  const listeners = {};
  const dispatched = [];
  const body = { tagName: 'BODY', isConnected: true, dispatchEvent: (e) => { dispatched.push(e); for (const fn of listeners[e.type] ?? []) fn(e); return true; } };
  const doc = {
    body, activeElement: body,
    documentElement: { dataset: {} },
    querySelectorAll: () => [], querySelector: () => null, getElementById: () => null,
  };
  class KeyboardEvent { constructor(type, init) { Object.assign(this, init); this.type = type; this.target = body; this.isTrusted = false; } }
  let pads = [];
  const win = {
    navigator: { getGamepads: () => pads },
    KeyboardEvent,
    innerWidth: 1280, innerHeight: 800,
    addEventListener: (type, fn) => { (listeners[type] ??= []).push(fn); },
    removeEventListener: () => {},
    getComputedStyle: () => ({ visibility: 'visible', display: 'block' }),
  };
  const said = [];
  let speed = 1;
  const keyboard = { name: 'pointerlock', on: 0, enable() { this.on++; }, disable() {}, update() {} };
  const g = gp.createGamepadBackend({
    intent, backends, doc, win,
    lookSpeed: () => speed,
    gateOpen: () => gate, menuOpen: () => menu, paused: () => paused,
    say: (l) => said.push(l),
  });
  const set = (p) => { pads = p ? [p] : []; };
  const connect = (p) => { set(p); for (const fn of listeners.gamepadconnected ?? []) fn({ gamepad: p }); };
  return {
    intent, backends, g, doc, win, said, dispatched, keyboard, listeners, set, connect,
    speed: (v) => { speed = v; },
    gate: (v) => { gate = v; }, menu: (v) => { menu = v; }, pause: (v) => { paused = v; },
  };
}

check('no controller, no work: poll returns before reading anything', () => {
  const h = harness();
  let read = 0;
  h.win.navigator.getGamepads = () => { read++; return []; };
  h.g.poll(1 / 60);
  assert.equal(read, 0);
  assert.equal(h.backends.name, 'none');
});

check('a pushed stick takes over from the live backend and walks, analogue', () => {
  const h = harness();
  h.backends.activate(h.keyboard);
  h.connect(pad());
  assert.match(h.said[0], /Controller connected/);
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'pointerlock', 'a resting pad does not take over');
  h.set(pad({ axes: [0.5, -1, 0, 0] }));
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'gamepad');
  assert.ok(h.intent.forward > 0.85, `forward ${h.intent.forward} (a stick past its rim is held to it)`);
  assert.ok(h.intent.strafe > 0.3 && h.intent.strafe < 0.6, `strafe ${h.intent.strafe}`);
  assert.equal(h.intent.sprint, false);
  h.set(pad());
  h.g.poll(1 / 60);
  assert.equal(h.intent.forward, 0, 'let go, it stops');
  assert.equal(h.backends.name, 'gamepad', 'and stays the controls until something else is used');
});

check('the right stick looks, at Settings › Look sensitivity, up is up and right is right', () => {
  const h = harness();
  h.connect(pad());
  h.set(pad({ axes: [0, 0, 1, 0] }));
  h.g.poll(0.5);
  assert.ok(near(h.intent.yawDelta, -gp.LOOK_YAW * 0.5, 1e-6), `yaw ${h.intent.yawDelta} (+ is left)`);
  h.intent.clearLook();
  h.set(pad({ axes: [0, 0, 0, -1] }));
  h.g.poll(0.5);
  assert.ok(near(h.intent.pitchDelta, gp.LOOK_PITCH * 0.5, 1e-6), `pitch ${h.intent.pitchDelta} (+ is up)`);
  h.intent.clearLook();
  h.set(pad({ axes: [0, 0, 1, 0] }));
  h.speed(2);
  h.g.poll(0.5);
  assert.ok(near(h.intent.yawDelta, -gp.LOOK_YAW, 1e-6), 'sensitivity 2 turns twice as fast');
});

check('the right trigger runs on foot, and climbs (with the left descending) while flying', () => {
  const h = harness();
  h.connect(pad());
  h.set(pad({ axes: [0, -1, 0, 0], values: { [BUTTON.RT]: 1 } }));
  h.g.poll(1 / 60);
  assert.equal(h.intent.sprint, true);
  assert.equal(h.intent.rise, 0);
  h.intent.flying = true;
  h.g.poll(1 / 60);
  assert.equal(h.intent.sprint, false);
  assert.equal(h.intent.rise, 1);
  h.set(pad({ values: { [BUTTON.LT]: 1 } }));
  h.g.poll(1 / 60);
  assert.equal(h.intent.rise, -1);
});

check('A inspects down the crosshair, once a press, as the keyboard\'s E does', () => {
  const h = harness();
  h.connect(pad());
  h.set(pad({ down: [BUTTON.A] }));
  h.g.poll(1 / 60);
  assert.deepEqual(h.intent.takeInteract(), { point: null, source: 'key' });
  h.g.poll(1 / 60);
  assert.equal(h.intent.takeInteract(), false, 'held is not pressed again');
});

check('the buttons press the keyboard\'s own keys, and those never switch the keyboard on', () => {
  const h = harness();
  h.connect(pad());
  const want = { [BUTTON.X]: 'KeyR', [BUTTON.Y]: 'KeyF', [BUTTON.VIEW]: 'KeyM', [BUTTON.MENU]: 'KeyN', [BUTTON.DOWN]: 'KeyG', [BUTTON.B]: 'Escape' };
  let activated = 0;
  const capture = createDesktopKeyCapture({ activate: () => { activated++; }, lock: () => {} });
  h.listeners.keydown = [...(h.listeners.keydown ?? []), (e) => capture(e)];
  for (const [button, code] of Object.entries(want)) {
    h.dispatched.length = 0;
    h.set(pad({ down: [Number(button)] }));
    h.g.poll(1 / 60);
    const downs = h.dispatched.filter((e) => e.type === 'keydown');
    assert.equal(downs.length, 1, `button ${button} presses one key`);
    assert.equal(downs[0].code, code, `button ${button} is ${code}`);
    assert.ok(padEvents.has(downs[0]), 'marked as the controller\'s');
    h.set(pad());
    h.g.poll(1 / 60);
  }
  assert.equal(activated, 0, 'the keyboard backend was not switched on by a controller key');
  assert.equal(h.backends.name, 'gamepad');
});

check('the arrival screen and an open card take the sticks from the walk', () => {
  const h = harness({ gate: true });
  h.connect(pad({ axes: [0, -1, 0, 0] }));
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'none', 'no movement backend is switched on behind the arrival screen');
  assert.equal(h.intent.forward, 0);
  h.gate(false);
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'gamepad');
  assert.ok(h.intent.forward > 0.9);
  h.menu(true);
  h.g.poll(1 / 60);
  assert.equal(h.intent.forward, 0, 'a card open: the stick moves focus, not the visitor');
  h.set(pad({ down: [BUTTON.A] }));
  h.g.poll(1 / 60);
  assert.equal(h.intent.takeInteract(), false, 'A in a menu presses a key on it, not the town');
});

check('a jaunt panel that focused its own Next stop key does not take the sticks from the walk', () => {
  const h = harness();
  const next = { tagName: 'BUTTON', isConnected: true, closest: (sel) => (/#jaunt-panel|button/.test(sel) ? {} : null), dispatchEvent: h.doc.body.dispatchEvent };
  h.doc.activeElement = next;
  h.connect(pad({ axes: [0, -1, 0, 0] }));
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'gamepad');
  assert.ok(h.intent.forward > 0.9, 'the stick walks with the jaunt\'s key focused');
});

check('a headset or Window mode puts the controller aside, and a lost one stops the walk', () => {
  const h = harness();
  h.connect(pad({ axes: [0, -1, 0, 0] }));
  h.pause(true);
  h.g.poll(1 / 60);
  assert.equal(h.backends.name, 'none');
  h.pause(false);
  h.g.poll(1 / 60);
  assert.ok(h.intent.forward > 0.9);
  for (const fn of h.listeners.gamepaddisconnected) fn({});
  assert.equal(h.intent.forward, 0);
  assert.match(h.said.at(-1), /disconnected/);
});

check('the Guide offers a Controller sheet, chosen while the controller is the controls', () => {
  assert.deepEqual(SCHEMES, ['touch', 'keyboard', 'controller']);
  assert.equal(controlScheme('gamepad', true), 'controller');
  const words = CONTROL_SHEETS.controller.rows.map(([k, d]) => `${k.join(' ')} ${d}`).join('\n');
  for (const [k, re] of [['Left stick', /walk/], ['Right stick', /look/], ['A', /inspect/], ['B', /back/], ['X', /gate/],
    ['Y', /fly/], ['RT', /run/], ['LT', /descend/], ['LB RB', /jaunt/], ['Menu', /Navigator/], ['View', /map/],
    ['D-pad down', /go to/], ['D-pad up', /keys on screen/]]) {
    assert.match(words, new RegExp(`^${k} [^\\n]*${re.source}`, 'm'), `the sheet's ${k} row`);
  }
});

check('main.js polls the controller before the live backend, every frame, and wires its menu and pause', () => {
  assert.match(main, /import \{ createGamepadBackend \} from '\.\/controls\/gamepad\.js';/);
  const poll = main.indexOf('gamepad.poll(');
  const update = main.indexOf('backends.active?.update?.(dt)');
  assert.ok(poll > 0 && update > poll && update - poll < 200, 'polled just before the live backend writes');
  assert.match(main, /paused: \(\) => !!\(xrMode\?\.presenting \|\| windowMode\?\.on\)/);
  assert.match(main, /menuOpen: \(\) => !!popup\.openId \|\| hud\.panelOpen\(\)/);
  assert.match(main, /gateOpen: \(\) => gateOpen/);
  assert.match(main, /lookSpeed: \(\) => hud\.settings\.lookSpeed/);
});

check('the key the controller is on always shows a focus ring', () => {
  assert.match(css, /html\[data-input="gamepad"\] body :focus \{ outline: 3px solid var\(--accent\)/);
});

console.log(`check_gamepad: ${checks.length} checks — ${checks.join('; ')}`);
