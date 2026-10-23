/**
 * Researcher mode (T-2657, NAV-S03; design doc "Field Navigator Mk II" §12, owner ruling
 * 2026-10-16: no /research page, the internal views are hidden behind a toggle).
 *
 * A switch in Settings › Research ("Expert research", T-3022), OFF by default and remembered
 * per device. While it is on, <html> carries `data-researcher-mode`, a small RESEARCHER label
 * sits in the HUD's top row, and what the visitor pages hold back comes back where it was cut:
 *
 *   - every element marked `data-researcher` (css/skins.css hides them until the root has
 *     the attribute): the full "Why this default" essays, and anything another app marks —
 *     the order book, once T-2667 moves it behind the mode;
 *   - and the visitor's stand-ins step aside: an element marked `data-visitor-only` (the
 *     one-line "Why" hint) is hidden while it is on, so the full text is read once.
 *
 * WHAT IT NEVER SHOWS. The owner, 2026-10-18: "rewrite the records so you are not referring
 * to internal ticket numbers or internal record ids in researcher or educator mode", and "If
 * in that mode you want to refer to the tickets as a link or something as an external source
 * or link back, ok, but I don't want to talk internal ticket language to researchers." So no
 * ticket number, record id or file path is shown here either; tools/check_visitor_ui.py and
 * tools/check_strings.py read Researcher-mode text with the visitor's rules (only "order
 * book" is allowed). A ticket may appear only as a LINK, the way an external source would:
 * `ticketLinkHtml` writes one, behind a plain-words label, marked `data-researcher`.
 *
 * NOTHING IS RE-RENDERED. Both halves are in the page from the first paint and the switch
 * is one attribute, so turning it on or off never reloads a panel and cannot lose a place.
 */
import { t } from './strings/index.js';
import './strings/research.js';

export const STORAGE_KEY = 'chicago4d.researcher';
export const MODE_ATTR = 'data-researcher-mode';
/** Where a ticket opens: the tickets repository, by the path tickets.json gives it. */
export const TICKETS_BASE = 'https://github.com/kevinrhaas/chicago-tickets/blob/main/';

const escape = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

/** The address of a ticket from its `path` in tickets.json (`T-1500-1749/T-1519-….md`), or ''. */
export function ticketUrl(path) {
  const p = String(path ?? '').trim();
  return /^T-\d{4}-\d{4}\/T-\d{4}(-[\w.-]+)?\.md$/.test(p) ? TICKETS_BASE + p : '';
}

/**
 * A ticket as Researcher mode may show one: a link behind plain words ("how this was
 * decided", "the work record"), opening in a new tab, marked `data-researcher` so a visitor
 * never sees it. No number in the label, ever; '' when there is no address to link.
 * @param {{ path: string, label?: 'decided'|'record' }} o
 */
export function ticketLinkHtml({ path, label = 'decided' } = {}) {
  const href = ticketUrl(path);
  if (!href) return '';
  const words = t(label === 'record' ? 'research.link.record' : 'research.link.decided');
  return `<a class="research-link" data-researcher href="${escape(href)}" target="_blank" rel="noopener">${escape(words)}</a>`;
}

/** What this device remembers; off when nothing is stored or storage is unavailable. */
export function readMode(storage) {
  try { return storage?.getItem?.(STORAGE_KEY) === 'on'; } catch { return false; }
}

function writeMode(storage, on) {
  try { if (on) storage?.setItem?.(STORAGE_KEY, 'on'); else storage?.removeItem?.(STORAGE_KEY); } catch { /* private window */ }
}

/** Set or clear the root attribute the stylesheet keys on. */
export function applyMode(on, doc = globalThis.document) {
  const root = doc?.documentElement;
  if (!root) return;
  if (on) root.setAttribute(MODE_ATTR, ''); else root.removeAttribute(MODE_ATTR);
}

/**
 * Wire the switch (#s-researcher: Settings › Research › Expert research, T-3022) to the page
 * and to this device.
 * @returns {{ readonly on: boolean, set(on: boolean): boolean, toggle(): boolean, onChange(fn): () => void }}
 */
export function createResearcherMode({ doc = globalThis.document, storage = null } = {}) {
  let on = readMode(storage);
  const listeners = new Set();
  const box = doc?.getElementById?.('s-researcher') ?? null;
  const sync = () => { if (box) box.checked = on; };
  applyMode(on, doc);
  sync();
  function set(next) {
    const was = on;
    on = !!next;
    applyMode(on, doc);
    writeMode(storage, on);
    sync();
    if (on !== was) for (const fn of listeners) { try { fn(on); } catch { /* a listener's fault is its own */ } }
    return on;
  }
  box?.addEventListener?.('change', () => set(box.checked));
  return {
    get on() { return on; },
    set,
    toggle: () => set(!on),
    onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
