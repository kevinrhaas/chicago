// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * card-a11y.js — the keyboard and screen-reader half of every card a visitor opens (T-3671).
 *
 * WCAG 2.1 AA, shared by the building card (popup.js), Inspect's tabs (apps/inspect-view.js),
 * the age tabs (reading-level.js) and the story and question cards (tale-card.js, ask-card.js):
 *
 *   rovingTabs   a tab strip is one Tab stop; Left/Right move along it and select, Home and
 *                End go to its ends (4.1.2, 2.1.1 — the ARIA tabs pattern, automatic activation)
 *   syncRoving   the selected tab is the strip's one Tab stop
 *   labelTabs    each tab an id, each panel labelled by its tab
 *   wireToggles  a "why" toggle says whether its note is open and which note it opens
 *   openerOf     what had focus when a card opened, to give focus back to on close (2.4.3)
 *   giveBack     focus back to it, or, for a card opened from the 3-D scene, to the scene
 *                canvas, which the Navigator already reads as "on the scene" (Tab opens it)
 *
 * Everything is applied to the DOM after a card's HTML is drawn, never to the HTML string, so
 * a card's markup as compiled stays byte for byte what the card tests hash. Each function is
 * a no-op on a fake document (tools/test_brougham_card.mjs, test_tales.mjs).
 */

const TAB = '[role="tab"]';
const usable = (t) => !t.disabled && !t.hidden && t.getAttribute?.('aria-disabled') !== 'true'
  && (typeof t.getClientRects !== 'function' || t.getClientRects().length > 0);

/** Tabs of one strip, in order, that can take focus now. */
function tabsOf(list) {
  return [...(list?.querySelectorAll?.(TAB) ?? [])].filter((t) => t.closest('[role="tablist"]') === list && usable(t));
}

/** The selected tab is the strip's one Tab stop; the rest are reached with the arrows. */
export function syncRoving(list) {
  const tabs = [...(list?.querySelectorAll?.(TAB) ?? [])];
  if (!tabs.length) return;
  const on = tabs.find((t) => t.getAttribute?.('aria-selected') === 'true' && usable(t)) ?? tabs.find(usable) ?? tabs[0];
  for (const t of tabs) t.tabIndex = t === on ? 0 : -1;
}

/**
 * Arrow keys over every tab strip inside `root`, delegated so a redrawn card keeps them.
 * `activate(tab)` selects a tab; by default the tab is clicked, which is how every strip
 * here already selects. Installed once per root.
 */
export function rovingTabs(root, { activate = (tab) => tab.click() } = {}) {
  if (!root?.addEventListener || root.__rovingTabs) return;
  root.__rovingTabs = true;
  root.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
    const tab = e.target?.closest?.(TAB);
    const list = tab?.closest?.('[role="tablist"]');
    if (!list || !root.contains(list)) return;
    const tabs = tabsOf(list);
    const at = tabs.indexOf(tab);
    if (at < 0) return;
    const vertical = list.getAttribute('aria-orientation') === 'vertical';
    const next = vertical ? 'ArrowDown' : 'ArrowRight', prev = vertical ? 'ArrowUp' : 'ArrowLeft';
    let to = null;
    if (e.key === next) to = tabs[(at + 1) % tabs.length];
    else if (e.key === prev) to = tabs[(at - 1 + tabs.length) % tabs.length];
    else if (e.key === 'Home') to = tabs[0];
    else if (e.key === 'End') to = tabs[tabs.length - 1];
    else return;
    e.preventDefault();
    e.stopPropagation();
    if (to === tab) return;
    to.focus({ preventScroll: true });
    // A strip wider than a phone scrolls sideways: bring the tab into view, and no further.
    to.scrollIntoView?.({ block: 'nearest', inline: 'nearest' });
    activate(to);
    syncRoving(list);
  });
}

/** Each tab an id (`<panel id>-tab` where it has none), each panel it controls labelled by it. */
export function labelTabs(root) {
  const doc = root?.ownerDocument;
  if (!doc || !root.querySelectorAll) return;
  for (const t of root.querySelectorAll(`${TAB}[aria-controls]`)) {
    const key = t.getAttribute('aria-controls');
    if (!t.id) t.id = `${key}-tab`;
    const panel = doc.getElementById(key);
    if (panel && root.contains(panel) && !panel.hasAttribute('aria-labelledby')) panel.setAttribute('aria-labelledby', t.id);
  }
}

let toggleSeq = 0;
/** A "why" toggle names the note it opens and says whether it is open. */
export function wireToggles(root) {
  if (!root?.querySelectorAll) return;
  for (const b of root.querySelectorAll('[data-toggle-note]')) {
    const note = b.parentElement?.querySelector('[data-note]');
    if (!note) continue;
    if (!note.id) note.id = `card-note-${++toggleSeq}`;
    b.setAttribute('aria-controls', note.id);
    b.setAttribute('aria-expanded', String(!note.hasAttribute('hidden')));
  }
}

/** Flip one toggle's note; returns whether it is now shown. */
export function flipToggle(b) {
  const note = b?.parentElement?.querySelector('[data-note]');
  if (!note) return null;
  const shown = note.hasAttribute('hidden');
  note.toggleAttribute('hidden', !shown);
  b.textContent = shown ? 'hide' : 'why';
  b.setAttribute?.('aria-expanded', String(shown));
  return shown;
}

/** What had focus as `card` opened, when it is a control outside the card worth going back to. */
export function openerOf(card) {
  const doc = card?.ownerDocument;
  const a = doc?.activeElement;
  if (!a || a === doc.body || a === doc.documentElement || card.contains?.(a)) return null;
  return a;
}

const visible = (el) => !!el?.isConnected && !el.closest?.('[hidden], [inert]')
  && (typeof el.getClientRects !== 'function' || el.getClientRects().length > 0);

/**
 * Focus back to where it was when the card opened. A card opened from the scene (a click, a
 * tap, the Interact key) had nothing focused, and a list row that opened it may have gone with
 * the list: either way focus goes to the scene canvas, the stable place a keyboard visitor
 * walks from, and the Navigator's Tab (navigator.js `onScene`) opens the rail from there.
 */
export function giveBack(opener, doc = globalThis.document) {
  if (!doc?.getElementById) return null;
  if (opener && visible(opener) && typeof opener.focus === 'function') {
    opener.focus({ preventScroll: true });
    if (doc.activeElement === opener) return opener;
  }
  const canvas = doc.getElementById('view');
  if (canvas) {
    if (!canvas.hasAttribute('tabindex')) canvas.setAttribute('tabindex', '-1');
    canvas.focus({ preventScroll: true });
    return canvas;
  }
  return null;
}

/** Focus a card's heading (reachable by script only), so a screen reader reads the card's name. */
export function focusHeading(h) {
  if (!h?.focus) return false;
  if (!h.hasAttribute('tabindex')) h.setAttribute('tabindex', '-1');
  h.focus({ preventScroll: true });
  return true;
}
