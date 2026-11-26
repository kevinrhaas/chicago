/** Keyboard ownership follows focus, never whether a non-modal panel is visible.
 * A menu's arrows, a button's Space and a reader's scrolling belong to that UI.
 * The capture handler and the movement backend must make the same decision. */
const READERS = '#navigator, #popup, #panel, #gate, #jaunt-panel, .pic-viewer, dialog, [role="dialog"]';
const CONTROLS = 'button, a[href], summary, input, textarea, select, audio[controls], video[controls], [role="button"], [role="tab"], [role="slider"], [role="spinbutton"], [role="listbox"], [role="menuitem"]';
/** T-3749: key events the game controller pressed (controls/gamepad.js). They reach every key's
 * own listener as the keyboard's would, but they are not the visitor taking up the keyboard. */
export const padEvents = new WeakSet();
const element = target => target?.nodeType === 3 ? target.parentElement : target;

/** Kept separate from UI ownership: E may close a card, but never a text field. */
export function isTyping(target) {
  const el = target instanceof HTMLElement ? target : null;
  if (!el) return false;
  if (el.isContentEditable) return true;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
}

export function ownsKeyboard(target) {
  const el = element(target);
  return !!el && (isTyping(el) || !!el.closest?.(READERS) || !!el.closest?.(CONTROLS));
}

export function worldKeyAllowed(event, { holding = false, inspecting = false } = {}) {
  if (!event || event.defaultPrevented || event.isComposing || event.metaKey || event.ctrlKey || event.altKey) return false;
  const target = element(event.target);
  if (isTyping(target)) return false;
  const owned = ownsKeyboard(target);
  // T-2954/T-3022: E closes a building card opened by hand, including while its
  // buttons have focus. A nested picture dialog or another app owns its keys.
  if (owned) return event.code === 'KeyE' &&
    ((holding && !!target?.closest?.('#popup')) || (inspecting && !!target?.closest?.('#nav-app-inspect'))) &&
    !target.closest?.('.pic-viewer, dialog, [role="dialog"]');
  return !holding || event.code === 'KeyE';
}

/** Runs in capture, before a rail can preventDefault in its own bubbling handler. */
export function createDesktopKeyCapture({ enabled = () => true, holding = () => false, inspecting = () => false, activate, lock }) {
  return event => {
    if (padEvents.has(event)) return;
    if (!enabled() || !worldKeyAllowed(event, { holding: holding(), inspecting: inspecting() })) return;
    activate();
    if (/^(Key[WASD]|Arrow(Up|Down|Left|Right))$/.test(event.code)) lock();
  };
}
