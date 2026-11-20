/**
 * letter-keys.js — single-key shortcuts can be turned off (T-3671, WCAG 2.1.4).
 *
 * The town answers bare letter and number keys anywhere on the page: W A S D walk, Q and E
 * go down and up or board, H G C F P N M V open things, 1–9 pick. A speech-input user, or
 * anyone whose fingers slip, sets them off by accident. Settings › Look › Letter keys turns
 * them off: while it is Off, a bare printable key (a letter, number, punctuation or symbol,
 * with no Ctrl, Alt or Meta held) is stopped here before any of the page's own listeners
 * hear it. The arrow keys, Space, Enter, Tab, Escape, Home and End still work, so the walker
 * still walks on the arrows and every control still answers the keyboard; a text field
 * still takes every key.
 *
 * Kept at `chicago4d.letterKeys` ('on', the default, or 'off'). Imported by recall.js, the
 * module index.html loads ahead of main.js, so its window-capture listener is registered
 * before welcome.js's and every other key handler on the page.
 */

export const LETTER_KEYS_KEY = 'chicago4d.letterKeys';
export const LETTER_KEY_CHOICES = Object.freeze(['on', 'off']);
export const LETTER_KEY_LABELS = Object.freeze({ on: 'On', off: 'Off' });

const listeners = new Set();
let choice = null;

function store() { try { return globalThis.localStorage ?? null; } catch { return null; } }

export function normalLetterKeys(v) { return v === 'off' ? 'off' : 'on'; }

export function letterKeysChoice() {
  if (choice === null) {
    let v = null;
    try { v = store()?.getItem?.(LETTER_KEYS_KEY) ?? null; } catch { v = null; }
    choice = normalLetterKeys(v);
  }
  return choice;
}

export function letterKeysOn() { return letterKeysChoice() === 'on'; }

export function setLetterKeys(v) {
  const next = normalLetterKeys(v);
  choice = next;
  try { store()?.setItem?.(LETTER_KEYS_KEY, next); } catch { /* private window */ }
  for (const fn of listeners) { try { fn(next); } catch { /* a listener's own fault */ } }
  return next;
}

export function onLetterKeysChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Where every key belongs to the control: text fields and editable regions. */
function typingTarget(t) {
  if (!t || t.nodeType !== 1) return false;
  if (t.isContentEditable) return true;
  const tag = t.tagName;
  if (tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (tag !== 'INPUT') return false;
  const type = String(t.type || 'text').toLowerCase();
  return !['button', 'checkbox', 'radio', 'range', 'reset', 'submit', 'image', 'color', 'file'].includes(type);
}

/** A bare character key: one printable character and no Ctrl, Alt or Meta. Space is not one. */
export function isCharacterShortcut(e) {
  if (!e || e.ctrlKey || e.altKey || e.metaKey) return false;
  const k = e.key;
  if (typeof k !== 'string' || [...k].length !== 1 || k === ' ') return false;
  return /[\p{L}\p{N}\p{P}\p{S}]/u.test(k);
}

/** Whether this key event is held back from the page's shortcuts now. */
export function blocksKey(e, on = letterKeysOn()) {
  return !on && isCharacterShortcut(e) && !typingTarget(e.target);
}

let installed = false;
export function installLetterKeys(win = globalThis.window) {
  if (installed || !win?.addEventListener) return false;
  installed = true;
  const stop = (e) => { if (blocksKey(e)) e.stopImmediatePropagation(); };
  win.addEventListener('keydown', stop, true);
  win.addEventListener('keypress', stop, true);
  return true;
}

installLetterKeys();
