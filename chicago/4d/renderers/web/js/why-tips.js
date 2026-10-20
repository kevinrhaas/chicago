/**
 * Short "Why?" (T-2658, NAV-904; design doc "Field Navigator Mk II" §07 Settings: "Each 'Why
 * this default' essay becomes a one-line hint plus a 'Why?' popover of 40 words or fewer").
 *
 * Under each researched setting a visitor reads one line saying what the default is, and a
 * small "Why?" button beside it. A tap, a click, or Enter / Space on the button opens a bubble
 * of 40 words at most beside it; a tap anywhere else, Escape, or the button again closes it.
 * The bubble's words are the string table's (`research.why.*`), held in the page beside the
 * button in a hidden element the button names (`data-why`), so the gates read them in place.
 * The full essay is Researcher mode's (js/researcher.js), under "Why this default".
 *
 * ONE BUBBLE, ON THE PAGE'S BODY. The settings sit inside the Navigator's screen, which slides
 * with a transform and scales with the text size; a fixed bubble inside it would be placed
 * against the screen, not the window, and clipped by its scroll. So the bubble is one element
 * on <body>, placed from the button's box, kept 16 px inside the window on every side.
 */

export const TIP_ID = 'why-tip';
export const GUTTER = 16;
export const GAP = 8;
export const MAX_WIDTH = 300;

/** The number of words in `text` (what the 40-word rule counts). */
export const wordCount = (text) => String(text ?? '').trim().split(/\s+/).filter(Boolean).length;

/**
 * Where the bubble goes: below the button, its right edge on the button's, unless that runs
 * off the window; above when there is no room below; and never nearer the window's edge than
 * the gutter. Pure, so the arithmetic is tested without a browser.
 * @param {{ left: number, right: number, top: number, bottom: number }} anchor  the button's box
 * @param {{ w: number, h: number }} size  the bubble's
 * @param {{ w: number, h: number }} view  the window's
 * @returns {{ left: number, top: number, side: 'below'|'above' }}
 */
export function placeTip(anchor, size, view, { gutter = GUTTER, gap = GAP } = {}) {
  const w = Math.min(size.w, Math.max(0, view.w - 2 * gutter));
  const h = Math.min(size.h, Math.max(0, view.h - 2 * gutter));
  const left = Math.max(gutter, Math.min(anchor.right - w, view.w - gutter - w));
  const below = anchor.bottom + gap;
  const above = anchor.top - gap - h;
  let top; let side;
  if (below + h <= view.h - gutter) { top = below; side = 'below'; }
  else if (above >= gutter) { top = above; side = 'above'; }
  else { top = Math.max(gutter, view.h - gutter - h); side = 'below'; }
  return { left: Math.round(left), top: Math.round(top), side };
}

const MODIFIERS = new Set(['Shift', 'Control', 'Alt', 'Meta', 'CapsLock']);

/**
 * Wire every `button.why-btn[data-why]` under `doc` to the one bubble.
 * @returns {{ open(button: Element): void, close(): void, readonly openFor: Element|null, readonly el: Element|null }}
 */
export function wireWhyTips(doc = globalThis.document) {
  const view = doc?.defaultView;
  if (!doc?.body || !view) return { open() {}, close() {}, get openFor() { return null; }, get el() { return null; } };
  let tip = doc.getElementById(TIP_ID);
  if (!tip) {
    tip = doc.createElement('div');
    tip.id = TIP_ID;
    tip.className = 'why-tip';
    tip.setAttribute('role', 'status');
    tip.hidden = true;
    doc.body.append(tip);
  }
  let openFor = null;

  function place() {
    if (!openFor) return;
    const r = openFor.getBoundingClientRect();
    // The button has gone (its screen closed, Researcher mode came on): so does the bubble.
    if (!openFor.isConnected || (r.width === 0 && r.height === 0) || r.bottom < 0 || r.top > view.innerHeight) { close(); return; }
    const width = Math.min(MAX_WIDTH, view.innerWidth - 2 * GUTTER);
    tip.style.width = `${width}px`;
    tip.style.maxHeight = `${view.innerHeight - 2 * GUTTER}px`;
    const at = placeTip(r, { w: width, h: tip.offsetHeight }, { w: view.innerWidth, h: view.innerHeight });
    tip.style.left = `${at.left}px`;
    tip.style.top = `${at.top}px`;
    tip.dataset.side = at.side;
  }

  function open(button) {
    const words = doc.getElementById(button?.dataset?.why ?? '')?.textContent.replace(/\s+/g, ' ').trim();
    if (!words) return;
    if (openFor && openFor !== button) openFor.setAttribute('aria-expanded', 'false');
    tip.textContent = words;
    tip.dataset.for = button.dataset.why;
    tip.hidden = false;
    openFor = button;
    button.setAttribute('aria-expanded', 'true');
    place();
  }

  function close() {
    if (!openFor && tip.hidden) return;
    tip.hidden = true;
    delete tip.dataset.for;
    openFor?.setAttribute('aria-expanded', 'false');
    openFor = null;
  }

  for (const button of doc.querySelectorAll('button.why-btn[data-why]')) {
    button.setAttribute('aria-controls', TIP_ID);
    button.setAttribute('aria-expanded', 'false');
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      if (openFor === button) close(); else open(button);
    });
  }
  // A tap anywhere but the bubble and its own button closes it (its button toggles it).
  doc.addEventListener('pointerdown', (e) => {
    if (openFor && !tip.contains(e.target) && !openFor.contains(e.target)) close();
  }, true);
  // Escape closes the bubble and nothing else: the Navigator's own Escape closes the device,
  // so the press stops here while a bubble is open. Any other key but the button's own
  // Enter / Space closes it too, so it never floats over a screen that has moved on.
  view.addEventListener('keydown', (e) => {
    if (!openFor) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      const back = openFor;
      close();
      back.focus?.({ preventScroll: true });
      return;
    }
    if (MODIFIERS.has(e.key)) return;
    if ((e.key === 'Enter' || e.key === ' ') && e.target === openFor) return;
    close();
  }, true);
  doc.addEventListener('scroll', place, { capture: true, passive: true });
  view.addEventListener('resize', place);

  return { open, close, get openFor() { return openFor; }, get el() { return tip; } };
}
