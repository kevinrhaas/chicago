/**
 * a11y-announce.js — the page's one status line for screen readers (T-3671, WCAG 4.1.3),
 * and the document's title (2.4.2).
 *
 * `announce(text)` speaks a short status without moving focus: arriving in a year, a
 * screen of the Navigator opening or closing. It writes into a visually hidden live region
 * (polite by default; `{ assertive: true }` for the rare thing that must interrupt) that is
 * made on first use, so the module costs nothing until something speaks. The same words
 * twice in a row are spoken twice: the region is emptied first and filled a frame later.
 *
 * `pageTitle({ year, screen })` is the tab's title: the screen that is open, then the year,
 * then the name — "Settings · 1835 · 4D Chicago", or "1835 · 4D Chicago" with the device
 * docked — and `setPageTitle` writes it.
 */
export const APP_NAME = '4D Chicago';
const REGION_IDS = { polite: 'a11y-status', assertive: 'a11y-alert' };

function region(doc, assertive) {
  const id = REGION_IDS[assertive ? 'assertive' : 'polite'];
  let el = doc.getElementById?.(id);
  if (el) return el;
  el = doc.createElement('div');
  el.id = id;
  el.className = 'visually-hidden';
  el.setAttribute('role', assertive ? 'alert' : 'status');
  el.setAttribute('aria-live', assertive ? 'assertive' : 'polite');
  el.setAttribute('aria-atomic', 'true');
  doc.body?.append(el);
  return el;
}

let pending = 0;
/** Speak `text` to a screen reader. Returns the region it went into (null without a page). */
export function announce(text, { assertive = false, doc = globalThis.document } = {}) {
  const words = String(text ?? '').trim();
  if (!doc?.body || !words) return null;
  const el = region(doc, assertive);
  el.textContent = '';
  const ticket = ++pending;
  const put = () => { if (ticket === pending) el.textContent = words; };
  const later = doc.defaultView?.requestAnimationFrame ?? ((fn) => setTimeout(fn, 16));
  // A frame apart, so a reader hears the change even when the words are the same.
  try { later(() => setTimeout(put, 30)); } catch { put(); }
  return el;
}

/** The document title for a year and, when one is open, a screen. */
export function pageTitle({ year = '', screen = '' } = {}) {
  return [screen, year, APP_NAME].filter(Boolean).join(' · ');
}

export function setPageTitle(parts, doc = globalThis.document) {
  const title = pageTitle(parts);
  if (doc && doc.title !== title) doc.title = title;
  return title;
}
