/**
 * touch.js — the mobile backend. Hand-rolled, no dependencies.
 *
 * Left half: a virtual thumbstick that appears wherever the thumb lands, so it
 * works on any hand size and any phone without a fixed hit target to hunt for.
 * Right half: drag to look. Tap without dragging: inspect what you tapped.
 *
 * Two things this has to get right, because 390x780 is a release gate:
 *
 *  - **`visualViewport`.** On iOS the URL bar slides away and `innerHeight`
 *    lies about it. Sizing the canvas from `window.innerHeight` gives you a
 *    scene that is a bar-height too tall, permanently, with the horizon parked
 *    off-screen. The viewport callback here reports the *visual* viewport, and
 *    main.js resizes the renderer from that.
 *
 *  - **Pointer capture and multi-touch.** Walking and looking happen at the same
 *    time, one finger each, and either can be lifted first. Every pointer is
 *    tracked by id; nothing is global state that the other thumb can clobber.
 */

const LOOK_SENSITIVITY = 0.0032;   // radians per CSS pixel
const STICK_RADIUS = 52;           // px to full deflection
const DEAD_ZONE = 6;               // px before anything moves
const TAP_MS = 260;                // hold shorter than this...
const TAP_SLOP = 12;               // ...and moved less than this = a tap

export function createTouchBackend({ intent, domElement, ui = {}, onViewport }) {
  const { layer, stick, knob, risePad, riseUp, riseDown } = ui;

  /** pointerId -> { role, startX, startY, x, y, t0, moved } */
  const active = new Map();
  let moveId = null;
  let lookId = null;
  let enabled = false;

  function isTouchLike(e) {
    return e.pointerType === 'touch' || e.pointerType === 'pen';
  }

  /**
   * Pointer capture keeps a thumb that slides off the stick still driving it.
   * It throws for a pointer the browser does not consider active — a synthetic
   * event, an already-released id, older Safari — and none of those are worth
   * an uncaught exception in a walkthrough.
   */
  function capture(pointerId, on) {
    try {
      if (on) domElement.setPointerCapture?.(pointerId);
      else domElement.releasePointerCapture?.(pointerId);
    } catch { /* not capturable; events still arrive on the element */ }
  }

  function showStick(x, y) {
    if (!stick) return;
    stick.style.left = `${x}px`;
    stick.style.top = `${y}px`;
    stick.classList.add('on');
    if (knob) knob.style.transform = 'translate(0px, 0px)';
  }

  function moveKnob(dx, dy) {
    if (knob) knob.style.transform = `translate(${dx}px, ${dy}px)`;
  }

  function hideStick() {
    stick?.classList.remove('on');
    if (knob) knob.style.transform = 'translate(0px, 0px)';
  }

  /**
   * The rise pad. Its own pointer handlers, NOT the canvas ones: the buttons
   * sit over the right half, which is the look region, so a thumb held on one
   * would otherwise also be dragging the view. `stopPropagation` plus their own
   * capture keeps the two apart.
   *
   * `pointercancel` matters as much as `pointerup` here — the browser steals a
   * pointer on scroll-gesture arbitration, and a stolen pointerup is how you get
   * a visitor ascending forever with nothing held.
   */
  function bindRise(btn, value) {
    if (!btn) return;
    const stop = () => {
      if (intent.rise === value) intent.rise = 0;
      btn.classList.remove('on');
    };
    btn.addEventListener('pointerdown', (e) => {
      if (!enabled) return;
      intent.rise = value;
      btn.classList.add('on');
      try { btn.setPointerCapture?.(e.pointerId); } catch { /* not capturable */ }
      e.stopPropagation();
      e.preventDefault();
    });
    for (const type of ['pointerup', 'pointercancel', 'pointerleave']) {
      btn.addEventListener(type, (e) => { stop(); e.stopPropagation(); });
    }
  }
  bindRise(riseUp, 1);
  bindRise(riseDown, -1);

  /** Show the vertical controls only when they do something. */
  function syncRisePad() {
    risePad?.toggleAttribute('hidden', !(enabled && intent.flying));
    if (!intent.flying) {
      intent.rise = 0;
      riseUp?.classList.remove('on');
      riseDown?.classList.remove('on');
    }
  }

  function onPointerDown(e) {
    if (!enabled || !isTouchLike(e)) return;
    const rect = domElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const leftHalf = x < rect.width * 0.5;

    // One thumb per role. A second finger in an occupied half is ignored rather
    // than stealing the role out from under the first.
    let role = null;
    if (leftHalf && moveId === null) { role = 'move'; moveId = e.pointerId; }
    else if (!leftHalf && lookId === null) { role = 'look'; lookId = e.pointerId; }
    else return;

    active.set(e.pointerId, { role, startX: x, startY: y, x, y, t0: performance.now(), moved: 0 });
    capture(e.pointerId, true);
    if (role === 'move') showStick(x, y);
    e.preventDefault();
  }

  function onPointerMove(e) {
    const p = active.get(e.pointerId);
    if (!p) return;
    const rect = domElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (p.role === 'look') {
      // Look is a DELTA, accumulated into the intent and consumed by the walker.
      intent.yawDelta -= (x - p.x) * LOOK_SENSITIVITY;
      intent.pitchDelta -= (y - p.y) * LOOK_SENSITIVITY;
    } else {
      let dx = x - p.startX;
      let dy = y - p.startY;
      const len = Math.hypot(dx, dy);
      if (len > STICK_RADIUS) {
        dx *= STICK_RADIUS / len;
        dy *= STICK_RADIUS / len;
      }
      moveKnob(dx, dy);
      const mag = Math.hypot(dx, dy);
      if (mag <= DEAD_ZONE) {
        intent.forward = 0;
        intent.strafe = 0;
      } else {
        const scale = (mag - DEAD_ZONE) / (STICK_RADIUS - DEAD_ZONE) / mag;
        intent.forward = -dy * scale;      // up the screen is forward
        intent.strafe = dx * scale;
        // Push past three quarters and you are running. No sprint button to hunt for.
        intent.sprint = mag > STICK_RADIUS * 0.75;
      }
    }

    p.moved = Math.max(p.moved, Math.hypot(x - p.startX, y - p.startY));
    p.x = x;
    p.y = y;
    e.preventDefault();
  }

  function onPointerUp(e) {
    const p = active.get(e.pointerId);
    if (!p) return;
    active.delete(e.pointerId);
    capture(e.pointerId, false);

    if (p.role === 'move') {
      moveId = null;
      intent.forward = 0;
      intent.strafe = 0;
      intent.sprint = false;
      hideStick();
    } else {
      lookId = null;
      const quick = performance.now() - p.t0 < TAP_MS;
      if (quick && p.moved < TAP_SLOP) {
        // A tap on the right half inspects whatever is under the finger.
        const rect = domElement.getBoundingClientRect();
        intent.interactPoint = {
          x: (p.x / rect.width) * 2 - 1,
          y: -(p.y / rect.height) * 2 + 1,
        };
        intent.interactSource = 'point';
        intent.interact = true;
      }
    }
  }

  function onCancel(e) { onPointerUp(e); }

  /**
   * The iOS URL bar problem. `visualViewport` is the only honest answer for how
   * much of the page the user can actually see; `innerHeight` is not.
   */
  function reportViewport() {
    const vv = window.visualViewport;
    const width = Math.round(vv?.width ?? window.innerWidth);
    const height = Math.round(vv?.height ?? window.innerHeight);
    document.documentElement.style.setProperty('--vh', `${height}px`);
    onViewport?.({ width, height, scale: vv?.scale ?? 1 });
  }

  return {
    name: 'touch',
    reportViewport,

    enable() {
      if (enabled) return;
      enabled = true;
      layer?.removeAttribute('hidden');
      document.body.classList.add('is-touch');
      domElement.addEventListener('pointerdown', onPointerDown, { passive: false });
      domElement.addEventListener('pointermove', onPointerMove, { passive: false });
      domElement.addEventListener('pointerup', onPointerUp);
      domElement.addEventListener('pointercancel', onCancel);
      window.visualViewport?.addEventListener('resize', reportViewport);
      window.visualViewport?.addEventListener('scroll', reportViewport);
      reportViewport();
      syncRisePad();
    },

    disable() {
      if (!enabled) return;
      enabled = false;
      active.clear();
      moveId = lookId = null;
      hideStick();
      intent.rise = 0;
      syncRisePad();
      layer?.setAttribute('hidden', '');
      document.body.classList.remove('is-touch');
      domElement.removeEventListener('pointerdown', onPointerDown);
      domElement.removeEventListener('pointermove', onPointerMove);
      domElement.removeEventListener('pointerup', onPointerUp);
      domElement.removeEventListener('pointercancel', onCancel);
      window.visualViewport?.removeEventListener('resize', reportViewport);
      window.visualViewport?.removeEventListener('scroll', reportViewport);
    },

    /**
     * Event-driven for movement, but the rise pad's VISIBILITY tracks a mode
     * that can change from anywhere (the HUD chip, the F key, an anchor jump),
     * so its one poll per frame is cheaper than an event bus for one boolean.
     */
    update() { syncRisePad(); },

    dispose() { this.disable(); },
  };
}

/** Best guess at whether this device wants the touch backend by default. */
export function prefersTouch() {
  return window.matchMedia?.('(pointer: coarse)').matches
    || (navigator.maxTouchPoints > 0 && window.innerWidth < 900);
}
