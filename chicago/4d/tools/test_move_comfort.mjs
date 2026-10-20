#!/usr/bin/env node
// T-2653 (NAV-703): Move's comfort settings — the head bob, the eye height (its researched
// default and its "Why this default") and snap-turn on touch. Drives the real touch backend
// over a small fake canvas for snap-turn, and reads the markup and the defaults. No
// browser; the smoke (part 12) moves the eye and stores the three settings in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createIntent } from '../renderers/web/js/controls/intent.js';
import { createTouchBackend, snapYaw, SNAP_DEG, SNAP_PX } from '../renderers/web/js/controls/touch.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const STEP = SNAP_DEG * Math.PI / 180;
const near = (a, b) => Math.abs(a - b) < 1e-9;

// ---- snap steps -----------------------------------------------------------------------
assert.equal(SNAP_DEG, 30);
let r = snapYaw(0, SNAP_PX - 1);
assert.equal(r.yaw, 0, 'short of a step, nothing turns');
assert.equal(r.carry, SNAP_PX - 1, '…and the drag is carried');
r = snapYaw(r.carry, 1);
assert(near(r.yaw, -STEP), 'a full step to the right turns right by 30°');
assert.equal(r.carry, 0);
r = snapYaw(0, -2 * SNAP_PX - 5);
assert(near(r.yaw, 2 * STEP), 'two steps to the left turn left by 60°');
assert.equal(r.carry, -5);

// ---- the touch backend turns in steps with it on, smoothly with it off -----------------------
function canvas() {
  const fns = {};
  return {
    addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
    removeEventListener(type, fn) { fns[type] = (fns[type] ?? []).filter((f) => f !== fn); },
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 390, height: 780 }),
    fire(type, e) { for (const fn of fns[type] ?? []) fn({ pointerType: 'touch', pointerId: 7, preventDefault() {}, ...e }); },
  };
}
globalThis.window = { innerWidth: 390, innerHeight: 780, visualViewport: null };
globalThis.document = { body: { classList: { add() {}, remove() {} } }, documentElement: { style: { setProperty() {} } } };
let snapOn = true;
const intent = createIntent();
const el = canvas();
const touch = createTouchBackend({ intent, domElement: el, snapTurn: () => snapOn });
touch.enable();
el.fire('pointerdown', { clientX: 300, clientY: 400 });
el.fire('pointermove', { clientX: 300 + SNAP_PX * 0.6, clientY: 400 });
assert.equal(intent.yawDelta, 0, 'snap-turn on: part of a step does not turn yet');
el.fire('pointermove', { clientX: 300 + SNAP_PX * 1.2, clientY: 410 });
assert(near(intent.yawDelta, -STEP), `snap-turn on: one step, all at once (${intent.yawDelta})`);
assert(intent.pitchDelta !== 0, 'looking up and down stays smooth');
el.fire('pointerup', { clientX: 300 + SNAP_PX * 1.2, clientY: 410 });
intent.clearLook();
snapOn = false;
el.fire('pointerdown', { clientX: 300, clientY: 400 });
el.fire('pointermove', { clientX: 310, clientY: 400 });
assert(intent.yawDelta < 0 && intent.yawDelta > -STEP / 4, `snap-turn off: a smooth turn (${intent.yawDelta})`);
el.fire('pointerup', { clientX: 310, clientY: 400 });
touch.disable();

// ---- the three settings: in Move's Comfort, with their defaults ----------------------------
const html = read('renderers/web/index.html');
const a = html.indexOf('data-panel="travel"');
const move = html.slice(a, html.indexOf('</section>', a));
const comfort = move.slice(move.indexOf('id="move-comfort"'));
assert(move.includes('id="move-comfort">Comfort<'), 'Move has a Comfort group');
for (const id of ['s-head-bob', 's-eye', 'v-eye', 'eye-note', 's-snap-turn']) {
  assert(comfort.includes(`id="${id}"`), `#${id} is in Move › Comfort`);
  assert.equal(html.split(`id="${id}"`).length, 2, `#${id} is on the page once`);
}
// T-2657 / T-2658: a one-line hint and its "Why?" bubble for a visitor, and the full essay
// (#eye-note) for Researcher mode.
assert(/<div class="why-line" data-visitor-only>[\s\S]*?<span class="why-text" id="why-eye-text" hidden data-str="research\.why\.eye">The default, 1\.68 m[\s\S]*?<details class="why" data-researcher><summary>Why this default<\/summary>\s*<p class="legend-note why-full" id="eye-note" data-researcher>The default, 1\.68 m/.test(comfort),
  'the eye height keeps its "Why this default", naming the researched figure');
const settingsPanel = html.slice(html.indexOf('data-panel="settings"'), html.indexOf('</section>', html.indexOf('data-panel="settings"')));
assert(!settingsPanel.includes('id="s-eye"'), 'eye height has left Settings');
assert(/your eye height and the other comfort settings are under<\/span> <b[^>]*>Move<\/b>/.test(settingsPanel), 'Settings says where it went');
const hud = read('renderers/web/js/hud.js');
assert(/eyeHeight: 1\.68\b/.test(hud), 'eye height defaults to the researched 1.68 m');
assert(/headBob: true\b/.test(hud), 'the head bob is on by default');
assert(/snapTurn: false\b/.test(hud), 'snap-turn is off by default');
assert(/wireToggle\('s-head-bob', 'headBob'\)/.test(hud) && /wireToggle\('s-snap-turn', 'snapTurn'\)/.test(hud)
  && /wireRange\('s-eye', 'v-eye', 'eyeHeight'/.test(hud), 'all three are wired to stored settings');
assert(/snapTurn: \(\) => !!hud\.settings\.snapTurn/.test(read('renderers/web/js/main.js')), 'the touch backend reads the setting');
// Visitor words: no ids or snake_case.
const words = comfort.replace(/<!--[\s\S]*?-->/g, '').replace(/<[^>]+>/g, ' ');
assert(!/[a-z]+_[a-z]+|\.js\b/.test(words), words);

console.log('test_move_comfort: head bob, eye height (1.68 m, with its Why) and snap-turn on touch, in Move › Comfort');
