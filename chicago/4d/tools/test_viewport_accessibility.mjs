import assert from 'node:assert/strict';
import { viewportSize } from '../renderers/web/js/viewport.js';
import { createTouchBackend } from '../renderers/web/js/controls/touch.js';
import { createIntent } from '../renderers/web/js/controls/intent.js';

const windowFor = (width, height, scale = 1) => ({
  innerWidth: 390, innerHeight: 780, visualViewport: { width, height, scale },
});
for (const [label, win, expected] of [
  ['unmagnified phone', windowFor(390, 780), [390, 780, 1]],
  ['native 2x pinch', windowFor(195, 390, 2), [390, 780, 2]],
  ['native 3x pinch', windowFor(130, 260, 3), [390, 780, 3]],
  ['URL bar exposed', windowFor(390, 710), [390, 710, 1]],
  ['keyboard exposed', windowFor(390, 440), [390, 440, 1]],
  ['keyboard and 2x pinch', windowFor(195, 220, 2), [390, 440, 2]],
  ['landscape at 2x', { innerWidth: 780, innerHeight: 390,
    visualViewport: { width: 390, height: 195, scale: 2 } }, [780, 390, 2]],
  ['desktop browser zoom changes layout', { innerWidth: 640, innerHeight: 400,
    visualViewport: { width: 640, height: 400, scale: 1 } }, [640, 400, 1]],
  ['no visual viewport', { innerWidth: 1280, innerHeight: 800 }, [1280, 800, 1]],
  ['temporarily unavailable visual dimensions', windowFor(0, NaN, 2), [390, 780, 2]],
  ['invalid scale', windowFor(390, 780, 0), [390, 780, 1]],
]) {
  const result = viewportSize(win);
  assert.deepEqual([result.width, result.height, result.scale], expected, label);
}

const listeners = new Map();
const canvas = {
  addEventListener(type, fn) { listeners.set(type, fn); },
  removeEventListener(type) { listeners.delete(type); },
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 390, height: 780 }),
};
let cssHeight;
globalThis.window = windowFor(195, 390, 2);
globalThis.document = {
  body: { classList: { add() {}, remove() {} } },
  documentElement: { style: { setProperty(key, value) { if (key === '--vh') cssHeight = value; } } },
};
window.visualViewport.addEventListener = window.visualViewport.removeEventListener = () => {};
const intent = createIntent();
const reports = [];
const touch = createTouchBackend({ intent, domElement: canvas, onViewport: size => reports.push(size) });
touch.enable();
assert.deepEqual(reports.at(-1), { width: 390, height: 780, scale: 2 });
assert.equal(cssHeight, '780px', 'reading sheet keeps its layout height during magnification');
const fire = (type, id, x, y) => listeners.get(type)?.({
  pointerType: 'touch', pointerId: id, clientX: x, clientY: y, preventDefault() {},
});
fire('pointerdown', 1, 70, 500);
fire('pointerdown', 2, 300, 500);
fire('pointermove', 1, 70, 450);
fire('pointermove', 2, 320, 490);
assert(intent.forward > .9 && intent.yawDelta < 0 && intent.pitchDelta > 0,
  'independent thumbs still move and look together');
fire('pointercancel', 1, 70, 450);
assert.equal(intent.forward, 0, 'cancel releases movement');
const priorYaw = intent.yawDelta;
fire('pointermove', 2, 340, 490);
assert(intent.yawDelta < priorYaw, 'releasing the movement thumb preserves the look thumb');
fire('pointerup', 2, 340, 490);
// Measured after an off-centre native pinch: both client coordinates are left
// of the full 390px canvas midpoint, but they straddle the visible midpoint.
window.visualViewport.offsetLeft = 65;
window.visualViewport.width = 198;
intent.clearLook();
fire('pointerdown', 3, 105, 500);
fire('pointerdown', 4, 192, 500);
fire('pointermove', 3, 105, 450);
fire('pointermove', 4, 212, 490);
assert(intent.forward > .9 && intent.yawDelta < 0 && intent.pitchDelta > 0,
  'off-center browser magnification retains independent visible left/right roles');
fire('pointerup', 3, 105, 450);
fire('pointerup', 4, 212, 490);
touch.disable();
assert.equal(listeners.size, 0);
console.log('VIEWPORT ACCESSIBILITY PASS — zoom, keyboard, URL bar, orientation, fallback and independent two-thumb input');
