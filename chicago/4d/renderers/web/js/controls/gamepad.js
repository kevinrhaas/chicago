/**
 * gamepad.js — a game controller, Bluetooth or cable, through the browser's Gamepad API (T-3749).
 *
 * The owner, 2026-11-26: *"Controller support: Support Bluetooth gaming controllers."* An Xbox,
 * PlayStation or Switch Pro pad paired to a computer, a phone or a tablet shows up in
 * `navigator.getGamepads()` once a button is pressed, and every one of them the browser knows
 * is reported in the Standard Gamepad layout (BUTTON below). Nothing is installed and nothing
 * is switched on in Settings: the first press is the opt-in.
 *
 * TWO JOBS, decided afresh every frame:
 *
 *  - IN THE TOWN it is one more input backend of the kind intent.js describes: it writes the
 *    shared intent and nothing else. Left stick walks (analogue), right stick looks (Settings ›
 *    Look sensitivity scales it, as it does the mouse), the right trigger or a click of the left
 *    stick runs, and while flying the triggers climb and descend. The buttons press the keys the
 *    keyboard already has (`press`) — R, F, M, N, G and Esc — so a controller can never come to
 *    mean something the keyboard does not, and the listeners that own those keys (hud.js,
 *    navigator.js, navigation.js, interact.js, main.js) keep their own rules about focus.
 *  - IN A MENU (the arrival screen and welcome, a card, Settings, the Navigator, any key the
 *    controller has put focus on) the sticks stop walking and drive the page instead: the D-pad
 *    or left stick moves focus to the nearest key in that direction (`nearest`), A presses it,
 *    B is Esc, the bumpers step a row of tabs, the right stick scrolls, and left and right
 *    change a slider or a picker. D-pad up from the town reaches the keys on screen; B from a
 *    key with nothing left to close hands back to the town.
 *
 * Taking over is the switch's rule: a stick pushed or a button pressed activates this backend,
 * and a click, a key or a touch hands it back (main.js's own listeners do that already). While
 * the arrival screen is up no movement backend is live, so the controller only drives the menu.
 *
 * WHAT IT COSTS A VISITOR WITHOUT A CONTROLLER: one `gamepadconnected` listener. `poll` returns
 * at once until the browser has reported a pad.
 *
 * Pure helpers are exported for tools/check_gamepad.mjs, which reads this file in node.
 */

import { lookScale } from './intent.js';
import { ownsKeyboard, padEvents } from './keyboard.js';

/** The Standard Gamepad layout (w3c.github.io/gamepad § Remapping). */
export const BUTTON = {
  A: 0, B: 1, X: 2, Y: 3, LB: 4, RB: 5, LT: 6, RT: 7,
  VIEW: 8, MENU: 9, L3: 10, R3: 11, UP: 12, DOWN: 13, LEFT: 14, RIGHT: 15,
};
export const STICK_DEAD = 0.18;
export const TRIGGER_ON = 0.35;
/** Radians a second at a full right stick and Look sensitivity 1. */
export const LOOK_YAW = 2.6;
export const LOOK_PITCH = 1.7;
/** Focus moves once on a push, then repeats after REPEAT_FIRST every REPEAT_EVERY seconds. */
export const REPEAT_FIRST = 0.4;
export const REPEAT_EVERY = 0.13;
/** Pixels a second at a full right stick, in a menu. */
export const SCROLL_RATE = 1100;

/** A stick with a round dead zone taken out and the rest rescaled to 0..1, direction kept. */
export function radial(x, y, dead = STICK_DEAD) {
  const ax = Number(x) || 0, ay = Number(y) || 0;
  const m = Math.hypot(ax, ay);
  if (m <= dead) return [0, 0];
  const s = Math.min(1, (m - dead) / (1 - dead)) / m;
  return [ax * s, ay * s];
}

/** The look curve: fine near the centre, full speed at the rim. */
export function curve(v, power = 1.7) {
  const a = Math.min(1, Math.abs(Number(v) || 0));
  return Math.sign(v) * a ** power;
}

/** One pad as plain numbers: sticks after the dead zone, triggers 0..1, buttons pressed. */
export function readPad(gp) {
  const axes = gp?.axes ?? [];
  const buttons = gp?.buttons ?? [];
  const value = (i) => { const b = buttons[i]; return b == null ? 0 : typeof b === 'object' ? Number(b.value) || (b.pressed ? 1 : 0) : Number(b) || 0; };
  const down = (i) => { const b = buttons[i]; return b != null && (typeof b === 'object' ? !!b.pressed || (Number(b.value) || 0) > 0.5 : (Number(b) || 0) > 0.5); };
  const [lx, ly] = radial(axes[0], axes[1]);
  const [rx, ry] = radial(axes[2], axes[3]);
  const pressed = [];
  for (let i = 0; i < Math.max(17, buttons.length); i++) pressed.push(down(i));
  return { lx, ly, rx, ry, lt: value(BUTTON.LT), rt: value(BUTTON.RT), pressed };
}

/** Whether the visitor is using this pad at all this frame (a resting pad is not a takeover). */
export function inUse(s) {
  return !!s && (s.lx !== 0 || s.ly !== 0 || s.rx !== 0 || s.ry !== 0
    || s.lt > TRIGGER_ON || s.rt > TRIGGER_ON || s.pressed.some(Boolean));
}

/** Buttons that went down since `prev`. */
export function edges(prev, now) {
  return now.map((d, i) => d && !prev?.[i]);
}

/** A menu direction from the D-pad, else from the left stick past half way. */
export function direction(s) {
  if (!s) return null;
  const p = s.pressed;
  if (p[BUTTON.UP]) return 'up';
  if (p[BUTTON.DOWN]) return 'down';
  if (p[BUTTON.LEFT]) return 'left';
  if (p[BUTTON.RIGHT]) return 'right';
  const { lx, ly } = s;
  if (Math.max(Math.abs(lx), Math.abs(ly)) < 0.5) return null;
  return Math.abs(lx) > Math.abs(ly) ? (lx > 0 ? 'right' : 'left') : (ly > 0 ? 'down' : 'up');
}

/** Key repeat for a held direction: fires on the push, then after a pause, then steadily. */
export function repeat(state, dir, dt) {
  if (!dir) return { fire: false, state: { dir: null, wait: 0 } };
  if (dir !== state?.dir) return { fire: true, state: { dir, wait: REPEAT_FIRST } };
  const wait = (state.wait ?? 0) - dt;
  if (wait > 0) return { fire: false, state: { dir, wait } };
  return { fire: true, state: { dir, wait: REPEAT_EVERY } };
}

/** The pad to read: the one used most recently, of those connected. */
export function pickPad(pads, lastIndex = null) {
  const list = [...(pads ?? [])].filter((p) => p && p.connected !== false);
  if (!list.length) return null;
  const live = list.filter((p) => inUse(readPad(p)));
  if (live.length) return live.sort((a, b) => (b.timestamp ?? 0) - (a.timestamp ?? 0))[0];
  return list.find((p) => p.index === lastIndex) ?? list[0];
}

/**
 * Spatial focus: of `rects` (each `{ left, top, right, bottom }`), the index nearest `from` in
 * `dir`, or -1. Distance along the way counts once, distance across it twice, and a key that
 * overlaps the current one across the way is preferred, so a column of keys is walked down
 * before a key off to the side is reached.
 */
export function nearest(from, rects, dir) {
  const cx = (r) => (r.left + r.right) / 2, cy = (r) => (r.top + r.bottom) / 2;
  const vertical = dir === 'up' || dir === 'down';
  let best = -1, bestScore = Infinity;
  rects.forEach((r, i) => {
    if (!r) return;
    const dx = cx(r) - cx(from), dy = cy(r) - cy(from);
    const ahead = { down: dy, up: -dy, right: dx, left: -dx }[dir];
    if (!(ahead > 1)) return;
    const along = Math.max(0, { down: r.top - from.bottom, up: from.top - r.bottom, right: r.left - from.right, left: from.left - r.right }[dir]);
    const gap = vertical ? Math.max(0, r.left - from.right, from.left - r.right) : Math.max(0, r.top - from.bottom, from.top - r.bottom);
    const off = Math.abs(vertical ? dx : dy);
    const score = along + gap * 2 + off * 0.25 + (gap > 0 ? 40 : 0);
    if (score < bestScore) { bestScore = score; best = i; }
  });
  return best;
}

/** The rows of the controls sheet's Controller page (sheet.js), held to the bindings here. */
export const BINDINGS = {
  walk: 'left stick', look: 'right stick', run: 'RT', inspect: 'A', back: 'B', interact: 'X', fly: 'Y',
  climb: 'RT', descend: 'LT', jauntBack: 'LB', jauntNext: 'RB', navigator: 'Menu', map: 'View', goTo: 'D-pad down', keys: 'D-pad up',
};

/** What the page can be asked for, by the key the keyboard already has for it. */
const KEYS = {
  interact: { key: 'r', code: 'KeyR' },
  fly: { key: 'f', code: 'KeyF' },
  map: { key: 'm', code: 'KeyM' },
  navigator: { key: 'n', code: 'KeyN' },
  goTo: { key: 'g', code: 'KeyG' },
  escape: { key: 'Escape', code: 'Escape' },
};

const FOCUSABLE = 'button, a[href], input:not([type="hidden"]), select, textarea, summary, [tabindex]:not([tabindex="-1"]), '
  + '[role="button"], [role="tab"], [role="menuitem"], [role="option"], [role="radio"], [role="slider"], [role="switch"]';
/** Places that hold focus: the controller does not wander out of them. */
const TRAPS = 'dialog[open], [aria-modal="true"], .pic-viewer, #gate';
/** Where the first push lands when nothing has focus, in this order. */
const FIRST = ['dialog[open]', '[aria-modal="true"]', '.pic-viewer', '[role="dialog"]', '#gate', '#popup', '#panel',
  '#navigator', '#jaunt-panel', '#hud'];
/** In an open place, the key the first push lands on: the first of these that shows, in this order. */
const PREFERRED = ['[autofocus]', '.jaunt-primary', '.welcome-action', '[aria-selected="true"]', '[aria-checked="true"]', '.is-on'];

export function createGamepadBackend({
  intent,
  backends,
  doc = globalThis.document,
  win = globalThis.window,
  lookSpeed = () => 1,
  /** The arrival screen or welcome is up: no movement backend is live, the pad drives the menu. */
  gateOpen = () => false,
  /** A card, Settings or another panel holds the visitor (main.js knows which). */
  menuOpen = () => false,
  /** A headset or Window mode owns the view; the pad stands aside. */
  paused = () => false,
  /** What changes when Esc did something: compared after B to know whether to hand back. */
  signature = () => '',
  say = () => {},
} = {}) {
  let pads = 0;
  let enabled = false;
  let prev = [];
  let lastIndex = null;
  let rep = { dir: null, wait: 0 };
  let runLatch = false;
  let backCheck = null;
  let told = false;
  /** The key the controller itself last put focus on. */
  let padFocus = null;
  const nav = win?.navigator;

  const onConnect = () => {
    pads++;
    if (!told) {
      told = true;
      say?.(`Controller connected: left stick walks, right stick looks, A inspects, B goes back, Menu opens the Navigator`);
    }
  };
  const onDisconnect = () => {
    pads = Math.max(0, pads - 1);
    if (!pads && backends?.active === backend) {
      intent.clear();
      say?.('Controller disconnected');
    }
  };
  win?.addEventListener?.('gamepadconnected', onConnect);
  win?.addEventListener?.('gamepaddisconnected', onDisconnect);
  // A pad already paired and pressed before this page loaded is listed without an event.
  try { pads = [...(nav?.getGamepads?.() ?? [])].filter(Boolean).length; } catch { pads = 0; }

  // A real key, click or touch is the visitor leaving the controller: the focus ring goes with it.
  const unmark = (e) => { if (e?.isTrusted !== false && !padEvents.has(e)) mark(false); };
  win?.addEventListener?.('pointerdown', unmark, { capture: true });
  win?.addEventListener?.('keydown', unmark, { capture: true });

  function mark(on) {
    const root = doc?.documentElement;
    if (!root) return;
    if (on) root.dataset.input = 'gamepad';
    else if (root.dataset.input === 'gamepad') delete root.dataset.input;
  }

  /** Press a key the keyboard has, at whatever holds focus, as the keyboard would. */
  function press(name) {
    const k = KEYS[name];
    const Ev = win?.KeyboardEvent;
    if (!k || !Ev) return false;
    const active = doc.activeElement;
    const target = active && active !== doc.body && active.isConnected ? active : (doc.body ?? doc);
    const down = new Ev('keydown', { key: k.key, code: k.code, bubbles: true, cancelable: true, composed: true });
    padEvents.add(down);
    target.dispatchEvent(down);
    const up = new Ev('keyup', { key: k.key, code: k.code, bubbles: true, cancelable: true, composed: true });
    padEvents.add(up);
    target.dispatchEvent(up);
    return true;
  }

  // ---- the page's keys ---------------------------------------------------------------- //

  function visible(el) {
    if (!el?.isConnected || el.disabled || el.closest?.('[hidden], [inert], [aria-hidden="true"]')) return false;
    if (!el.getClientRects?.().length) return false;
    const cs = win.getComputedStyle?.(el);
    return !cs || (cs.visibility !== 'hidden' && cs.display !== 'none' && cs.pointerEvents !== 'none');
  }
  function onScreen(r) {
    return r.bottom > 0 && r.right > 0 && r.top < (win.innerHeight || 1e9) && r.left < (win.innerWidth || 1e9);
  }
  function candidates(scope) {
    return [...(scope ?? doc).querySelectorAll(FOCUSABLE)]
      .filter((el) => el.tagName !== 'CANVAS' && el.getAttribute('tabindex') !== '-2' && visible(el));
  }
  /** The open place that should take the first push, or null. */
  function topScope() {
    for (const sel of FIRST) {
      for (const el of doc.querySelectorAll(sel)) if (visible(el) && candidates(el).length) return el;
    }
    return null;
  }
  function focus(el) {
    if (!el) return false;
    padFocus = el;
    try { el.focus({ preventScroll: true }); } catch { el.focus?.(); }
    try { el.scrollIntoView?.({ block: 'nearest', inline: 'nearest' }); } catch { /* old engines */ }
    mark(true);
    return doc.activeElement === el;
  }
  function focusFirst() {
    const scope = topScope();
    if (!scope) return false;
    const list = candidates(scope);
    const shows = (el) => onScreen(el.getBoundingClientRect());
    let preferred = null;
    for (const sel of PREFERRED) if ((preferred = list.find((el) => el.matches(sel) && shows(el)))) break;
    return focus(preferred ?? list.find(shows) ?? list[0]);
  }
  function moveFocus(dir) {
    const from = doc.activeElement;
    if (!from || from === doc.body || !visible(from)) return focusFirst();
    const trap = from.closest?.(TRAPS);
    const tryIn = (scope) => {
      const list = candidates(scope).filter((el) => el !== from && !el.contains(from) && !from.contains(el));
      const i = nearest(from.getBoundingClientRect(), list.map((el) => el.getBoundingClientRect()), dir);
      return i >= 0 ? focus(list[i]) : false;
    };
    // Inside an open place first, then (unless it holds focus) anywhere on the page.
    const own = FIRST.map((sel) => from.closest?.(sel)).find(Boolean);
    if (own && tryIn(own)) return true;
    if (trap) return false;
    return tryIn(doc);
  }
  /** Left and right change a slider or a picker rather than leave it. */
  function adjust(el, dir) {
    if (dir !== 'left' && dir !== 'right') return false;
    const fire = () => { el.dispatchEvent(new win.Event('input', { bubbles: true })); el.dispatchEvent(new win.Event('change', { bubbles: true })); };
    if (el?.tagName === 'INPUT' && el.type === 'range') {
      if (dir === 'right') el.stepUp(); else el.stepDown();
      fire();
      return true;
    }
    if (el?.tagName === 'SELECT' && el.options?.length) {
      const i = Math.min(el.options.length - 1, Math.max(0, el.selectedIndex + (dir === 'right' ? 1 : -1)));
      if (i !== el.selectedIndex) { el.selectedIndex = i; fire(); }
      return true;
    }
    return false;
  }
  /** The bumpers step the row of tabs focus is in, or the open place's first row. */
  function stepTabs(step) {
    const active = doc.activeElement;
    const scope = active?.closest?.('[role="tablist"]')
      ?? (FIRST.map((sel) => active?.closest?.(sel)).find(Boolean) ?? topScope())?.querySelector?.('[role="tablist"]');
    const tabs = scope ? [...scope.querySelectorAll('[role="tab"]')].filter(visible) : [];
    if (!tabs.length) return false;
    const on = tabs.findIndex((t) => t === active || t.getAttribute('aria-selected') === 'true');
    const next = tabs[(Math.max(0, on) + step + tabs.length) % tabs.length];
    next.click();
    focus(next);
    return true;
  }
  function scrollBy(dy) {
    if (!dy) return;
    let el = doc.activeElement && doc.activeElement !== doc.body ? doc.activeElement : topScope();
    while (el && el !== doc.body) {
      const cs = win.getComputedStyle?.(el);
      if (el.scrollHeight > el.clientHeight + 1 && cs && /(auto|scroll)/.test(cs.overflowY)) { el.scrollTop += dy; return; }
      el = el.parentElement;
    }
  }
  /** The jaunt's own Back or Next stop key, if it is showing and not greyed. */
  function jauntStep(step) {
    const panel = doc.getElementById?.('jaunt-panel');
    if (!panel || !visible(panel)) return false;
    const names = step > 0 ? ['next', 'bar-next'] : ['prev'];
    for (const n of names) {
      const key = panel.querySelector(`[data-action="${n}"]`);
      if (key && visible(key)) { key.click(); return true; }
    }
    return false;
  }
  /** What Esc can change: main.js's own state, and any dialog or picture viewer it opened or shut. */
  const sigNow = () => `${signature()}|${doc.querySelectorAll('dialog[open], [role="dialog"]:not([hidden]), .pic-viewer:not([hidden])').length}`;
  function back() {
    backCheck = { sig: sigNow(), active: doc.activeElement };
    press('escape');
  }

  // ---- each frame ---------------------------------------------------------------------- //

  function menu(s, down, dt) {
    if (down[BUTTON.MENU]) { press('navigator'); return; }
    const dir = direction(s);
    const r = repeat(rep, dir, dt);
    rep = r.state;
    if (r.fire) {
      const active = doc.activeElement;
      if (!(active && adjust(active, dir))) moveFocus(dir);
    }
    if (down[BUTTON.A]) {
      const active = doc.activeElement;
      // A heading the page focused for a screen reader is not a key: the first A finds one.
      if (active && active !== doc.body && active.matches?.(FOCUSABLE) && visible(active)) { mark(true); active.click(); } else focusFirst();
    }
    if (down[BUTTON.B]) back();
    if (down[BUTTON.LB] && !stepTabs(-1)) jauntStep(-1);
    if (down[BUTTON.RB] && !stepTabs(1)) jauntStep(1);
    scrollBy(s.ry * SCROLL_RATE * dt);
  }

  function world(s, down, dt) {
    if (down[BUTTON.A]) { intent.interactPoint = null; intent.interactSource = 'key'; intent.interact = true; }
    if (down[BUTTON.B]) back();
    if (down[BUTTON.X]) press('interact');
    if (down[BUTTON.Y]) press('fly');
    if (down[BUTTON.VIEW]) press('map');
    if (down[BUTTON.MENU]) press('navigator');
    if (down[BUTTON.DOWN]) press('goTo');
    if (down[BUTTON.UP]) focusFirst();
    if (down[BUTTON.LB] || down[BUTTON.LEFT]) jauntStep(-1);
    if (down[BUTTON.RB] || down[BUTTON.RIGHT]) jauntStep(1);
    if (down[BUTTON.L3]) runLatch = !runLatch;
    if (s.lx === 0 && s.ly === 0) runLatch = false;

    intent.forward = s.ly ? -s.ly : 0;
    intent.strafe = s.lx;
    if (intent.flying) {
      intent.rise = (s.rt > TRIGGER_ON ? s.rt : 0) - (s.lt > TRIGGER_ON ? s.lt : 0);
      intent.sprint = runLatch;
    } else {
      intent.rise = 0;
      intent.sprint = runLatch || s.rt > TRIGGER_ON;
    }
    const k = lookScale(lookSpeed);
    intent.yawDelta += -curve(s.rx) * LOOK_YAW * k * dt;
    intent.pitchDelta += -curve(s.ry) * LOOK_PITCH * k * dt;
  }

  function still() {
    intent.forward = intent.strafe = intent.rise = 0;
    intent.sprint = false;
  }

  const backend = {
    name: 'gamepad',
    get connected() { return pads > 0; },
    get menu() { return lastMenu; },
    enable() {
      if (enabled) return;
      enabled = true;
      runLatch = false;
    },
    disable() {
      if (!enabled) return;
      enabled = false;
      runLatch = false;
      mark(false);
    },
    /** The walker reads the intent `poll` wrote; nothing more to do in the backend's turn. */
    update() {},

    /**
     * Read the pad and act. Called once a frame by main.js BEFORE the active backend's update,
     * with the frame's real seconds, whether or not this backend is the live one.
     */
    poll(dt = 1 / 60) {
      if (!pads || paused()) { prev = []; return; }
      let pad = null;
      try { pad = pickPad(nav?.getGamepads?.(), lastIndex); } catch { pad = null; }
      if (!pad) { prev = []; return; }
      if (pad.index !== lastIndex) { lastIndex = pad.index; prev = []; }
      const s = readPad(pad);
      const down = edges(prev, s.pressed);
      prev = s.pressed;

      // B, last frame: if Esc closed nothing and moved nothing, the key it left from goes, and the
      // controller is back in the town.
      if (backCheck) {
        const was = backCheck; backCheck = null;
        const active = doc.activeElement;
        if (active === was.active && sigNow() === was.sig && active && active !== doc.body && !gateOpen()) {
          active.blur?.();
          mark(false);
        }
      }

      const used = inUse(s);
      // The jaunt panel puts focus on its own Next stop key for a keyboard visitor; that is not the
      // controller going into a menu, so the town keeps the sticks until the pad itself goes there.
      const active = doc.activeElement;
      const pageFocusedJaunt = !!active?.closest?.('#jaunt-panel') && active !== padFocus;
      const inMenu = gateOpen() || menuOpen() || (ownsKeyboard(active) && !pageFocusedJaunt);
      lastMenu = inMenu;
      if (inMenu) {
        if (backends?.active === backend) still();
        if (used || down.some(Boolean)) menu(s, down, dt);
        else rep = { dir: null, wait: 0 };
        return;
      }
      rep = { dir: null, wait: 0 };
      if (backends?.active !== backend) {
        if (!used) return;
        backends.activate(backend);
      }
      world(s, down, dt);
    },

    dispose() {
      win?.removeEventListener?.('gamepadconnected', onConnect);
      win?.removeEventListener?.('gamepaddisconnected', onDisconnect);
      win?.removeEventListener?.('pointerdown', unmark, { capture: true });
      win?.removeEventListener?.('keydown', unmark, { capture: true });
    },

    /** For the check and the smoke: what a key press would reach. */
    _test: { press, focusFirst, moveFocus, jauntStep },
  };
  let lastMenu = false;
  return backend;
}
