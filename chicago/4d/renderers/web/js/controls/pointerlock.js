/**
 * pointerlock.js — the desktop backend: WASD plus mouse-look under pointer lock.
 *
 * `PointerLockControls` is used for what it is genuinely good at — the Pointer
 * Lock API plumbing, the lock/unlock events, the polar clamp — but it is NOT
 * pointed at the camera. It drives a throwaway rig, and this backend reports the
 * frame's rotation as `yawDelta` / `pitchDelta` on the shared intent object.
 *
 * That indirection buys the invariant in intent.js: the camera has exactly one
 * author (the walker), so desktop and touch cannot fight over it, and the smoke
 * harness can drive the same intent both backends write.
 *
 * `dragLook` (cloud play, `?look=drag`; the owner, 2026-11-27: "the mouse movements do not
 * seem to work, I could not look around"): a streamed browser cannot hand the pointer lock
 * through to the player's own browser, so the look is a drag instead. Hold the left button
 * and move to look, the way a phone's finger does (the same sign as the mouse under lock);
 * a click that did not drag is a click. No lock is ever asked for.
 *
 * Keys are read whether or not the pointer is locked. Walking before you click
 * is the friendlier behaviour, and it is what lets a headless test press W.
 */

import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { lookScale } from './intent.js';
import { ownsKeyboard, worldKeyAllowed } from './keyboard.js';
export { isTyping } from './keyboard.js';

const KEYS = {
  KeyW: 'ahead', ArrowUp: 'ahead',
  KeyS: 'back', ArrowDown: 'back',
  KeyA: 'left', ArrowLeft: 'left',
  KeyD: 'right', ArrowRight: 'right',
};

/** Pixels a press may wander before it is a drag (look) rather than a click. */
export const DRAG_SLOP_PX = 4;
/** Radians of turn per pixel of drag at sensitivity 1: the mouse's own under lock. */
export const DRAG_RAD_PER_PX = 0.002;

export function createPointerLockBackend({ intent, domElement, onLockChange, onDragLook, holding = () => false, inspecting = () => false, lookSpeed = () => 1, dragLook = false }) {
  // PointerLockControls connects its document listeners in the constructor, so
  // enabling and disabling this backend flips `controls.enabled` rather than
  // reconnecting — connect() twice would double-register every listener.
  const rig = new THREE.Object3D();
  const controls = new PointerLockControls(rig, domElement);
  controls.enabled = false;
  // T-3563: Settings › Look › Mouse sensitivity scales this; 1 is the turn it always had.
  controls.pointerSpeed = lookScale(lookSpeed);
  controls.minPolarAngle = Math.PI * 0.06;
  controls.maxPolarAngle = Math.PI * 0.94;

  const held = new Set();
  const euler = new THREE.Euler(0, 0, 0, 'YXZ');
  let prevYaw = 0;
  let prevPitch = 0;
  let enabled = false;

  /**
   * Click inspects, in both modes.
   *
   * On foot a visitor learns Space. In free-fly Space is ascend — the flycam
   * convention, and the right call — so the key they learned stops answering in
   * the one view that shows them the whole town, and it reads as inspect being
   * switched off up there. E has always worked and nobody guesses E.
   *
   * A click under the crosshair is the gesture everyone already has, it means
   * the same thing in both modes, and while the pointer is locked it is
   * otherwise unused: the canvas click handler only takes the lock, and once
   * locked it never fires again.
   */
  function onMouseDown(e) {
    if (!controls.isLocked || e.button !== 0) return;
    intent.interactPoint = null;
    intent.interactSource = 'point';
    intent.interact = true;
  }

  function onKeyDown(e) {
    if (!worldKeyAllowed(e, { holding: holding(), inspecting: inspecting() })) return;
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') { held.add('sprint'); return; }
    // Vertical, free-fly only. Space is overloaded — it inspects on foot and
    // ascends in the air — which is why the backend has to see intent.flying.
    // The alternative was a third key nobody would find; ascend-on-Space is
    // what every flycam in existence does, and inspect has E either way.
    if (e.code === 'Space' && intent.flying) { held.add('up'); e.preventDefault(); return; }
    if (e.code === 'KeyQ') { held.add('down'); e.preventDefault(); return; }
    if (e.code === 'KeyE' || e.code === 'Space') {
      // Space also inspects: on a trackpad, E and a click are the same reach.
      // No point: a keyboard inspection is always down the crosshair.
      if (!e.repeat) {
        intent.interactPoint = null;
        intent.interactSource = 'key';
        intent.interact = true;
      }
      e.preventDefault();
      return;
    }
    const dir = KEYS[e.code];
    if (!dir) return;
    held.add(dir);
    e.preventDefault();
  }

  function onKeyUp(e) {
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') { held.delete('sprint'); return; }
    // Released unconditionally, NOT behind `intent.flying`: leaving fly mode
    // with Space down would otherwise strand 'up' in the held set and the
    // visitor would rise forever with nothing pressed.
    if (e.code === 'Space') { held.delete('up'); return; }
    if (e.code === 'KeyQ') { held.delete('down'); return; }
    const dir = KEYS[e.code];
    if (dir) held.delete(dir);
  }

  function onBlur() { held.clear(); }

  function onFocus(e) {
    if (!ownsKeyboard(e.target)) return;
    held.clear();
    intent.forward = intent.strafe = intent.rise = 0;
    intent.sprint = false;
    // A key queued just before the UI took focus must not inspect behind it.
    if (intent.interactSource === 'key') {
      intent.interact = false; intent.interactPoint = null; intent.interactSource = null;
    }
  }

  // Drag look (dragLook only): a press on the view, then movement with the button held.
  let press = null;
  let lastDragged = false;
  function onDragDown(e) {
    if (e.button !== 0 || e.target !== domElement) return;
    press = { x: e.clientX, y: e.clientY, moved: false };
    lastDragged = false;
  }
  function onDragMove(e) {
    if (!press) return;
    if (!(e.buttons & 1)) { press = null; return; }
    if (!press.moved) {
      if (Math.hypot(e.clientX - press.x, e.clientY - press.y) < DRAG_SLOP_PX) return;
      press.moved = true;
      onDragLook?.();
    }
    const k = DRAG_RAD_PER_PX * lookScale(lookSpeed);
    intent.yawDelta -= (e.clientX - press.x) * k;
    intent.pitchDelta -= (e.clientY - press.y) * k;
    press.x = e.clientX; press.y = e.clientY;
  }
  function onDragUp() { lastDragged = !!press?.moved; press = null; }

  function onLock() { onLockChange?.(true); }
  function onUnlock() { onLockChange?.(false); }

  return {
    name: 'pointerlock',
    controls,
    get isLocked() { return controls.isLocked; },
    dragLook,
    /** Did the press that ended with this click drag the view (then it is not a click)? */
    get dragged() { return lastDragged; },

    lock() {
      if (dragLook) return;
      try { controls.lock(); } catch { /* a denied lock is not an error worth a page error */ }
    },
    unlock() { controls.unlock(); },

    enable() {
      if (enabled) return;
      enabled = true;
      window.addEventListener('keydown', onKeyDown);
      window.addEventListener('mousedown', onMouseDown);
      window.addEventListener('keyup', onKeyUp);
      window.addEventListener('blur', onBlur);
      window.addEventListener('focusin', onFocus);
      if (dragLook) {
        window.addEventListener('pointerdown', onDragDown);
        window.addEventListener('pointermove', onDragMove);
        window.addEventListener('pointerup', onDragUp);
        window.addEventListener('pointercancel', onDragUp);
      }
      controls.addEventListener('lock', onLock);
      controls.addEventListener('unlock', onUnlock);
      controls.enabled = true;
      rig.rotation.set(0, 0, 0);
      prevYaw = prevPitch = 0;
    },

    disable() {
      if (!enabled) return;
      enabled = false;
      held.clear();
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur', onBlur);
      window.removeEventListener('focusin', onFocus);
      window.removeEventListener('pointerdown', onDragDown);
      window.removeEventListener('pointermove', onDragMove);
      window.removeEventListener('pointerup', onDragUp);
      window.removeEventListener('pointercancel', onDragUp);
      press = null;
      controls.removeEventListener('lock', onLock);
      controls.removeEventListener('unlock', onUnlock);
      if (controls.isLocked) controls.unlock();
      controls.enabled = false;
    },

    /** Write this frame's intent. Called once per frame by main.js. */
    update() {
      if (!enabled) return;
      if (holding() || ownsKeyboard(domElement.ownerDocument.activeElement)) held.clear();
      intent.forward = (held.has('ahead') ? 1 : 0) - (held.has('back') ? 1 : 0);
      intent.strafe = (held.has('right') ? 1 : 0) - (held.has('left') ? 1 : 0);
      intent.rise = (held.has('up') ? 1 : 0) - (held.has('down') ? 1 : 0);
      intent.sprint = held.has('sprint');

      // Read every frame, so a move of the slider takes at once.
      controls.pointerSpeed = lookScale(lookSpeed);
      euler.setFromQuaternion(rig.quaternion, 'YXZ');
      intent.yawDelta += euler.y - prevYaw;
      intent.pitchDelta += euler.x - prevPitch;
      // T-3753 (the owner, 2026-11-26: "users could not look up during a jaunt, sometimes it
      // freezes and you can't look up"): the rig is levelled again every frame, so its polar
      // clamp only ever bounds one frame's turn. Kept, it held the visitor's own look while
      // the view was turned for them (a jaunt's arrivals, flights and glides set the walker's
      // pitch, never the rig's): look up 60° at a house, be levelled on the way to the next
      // stop, and the rig was still at 60°, 19° short of its ceiling, so the mouse stopped
      // answering upward 19° above level. The walker's own ±85° is the one limit.
      rig.quaternion.identity();
      prevYaw = 0;
      prevPitch = 0;
    },

    dispose() {
      this.disable();
      controls.dispose();
    },
  };
}
