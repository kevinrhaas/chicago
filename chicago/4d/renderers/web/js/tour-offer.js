/**
 * The Field Check's offer, and the one-time hints after it (T-2664, NAV-802; design doc
 * section 11 and M2).
 *
 * THE OFFER. Home's "First time? Take the 60-second tour", under its three choices. It is
 * offered once per device: whatever the visitor does with it the first time — takes it, or
 * goes into the town by any other choice, which declines it — is remembered, and it is not
 * shown again. A Field Check already finished, or left running for a reload to resume
 * (js/tour.js, `chicago4d.tour`), is not offered either.
 *
 * THE HINTS. One line each, once per device, for the first Jaunt (at its first stop), the
 * first Jump (on the far year's way into the town) and the first Reconstructed building
 * (when its card or Inspect opens). None shows while the Field Check is running: the tour
 * has the screen, and a hint held back is still owed. A hint takes no pointer events and
 * goes after a few seconds, or at the visitor's next move.
 *
 * Every read and write of storage is inside try/catch: where storage is refused, the offer
 * and each hint show once per page instead, never an error (as js/roam-tip.js).
 */
import { t } from './strings/index.js';
import './strings/tour.js';

export const OFFER_KEY = 'chicago4d.tourOffer';
export const HINTS_KEY = 'chicago4d.hintsSeen';
/** Written (session storage) by the Navigator's Jump as the page goes (apps/jump-view.js),
 * read once by the far year: an arrival from the Observatory is not a Jump. */
export const JUMPED_KEY = 'chicago4d.jumped';
export const HINT_IDS = ['jaunt', 'jump', 'reconstructed'];
export const HINT_MS = 6000;
const TOUR_KEY = 'chicago4d.tour'; // js/tour.js

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };
const session = () => { try { return globalThis.sessionStorage ?? null; } catch { return null; } };

export const offerText = () => t('tour.offer');
export const hintText = (id) => (HINT_IDS.includes(id) ? t(`tour.hint.${id}`) : '');

export function createTourOffer({ storage = local() } = {}) {
  let spentHere = null;
  const get = (k) => { try { return storage?.getItem(k) ?? null; } catch { return null; } };
  return {
    /** Whether Home should offer the tour now. */
    due() {
      if (spentHere) return false;
      const v = get(OFFER_KEY);
      if (v === 'taken' || v === 'declined') return false;
      let tour = null;
      try { tour = JSON.parse(get(TOUR_KEY) || 'null'); } catch { tour = null; }
      return !(tour?.active || tour?.done);
    },
    /** The visitor answered: 'taken', or 'declined' (any other way into the town). */
    spend(how = 'declined') {
      if (spentHere) return false;
      spentHere = how === 'taken' ? 'taken' : 'declined';
      try { storage?.setItem(OFFER_KEY, spentHere); } catch { /* remembered for this page only */ }
      return true;
    },
    get state() { return spentHere ?? get(OFFER_KEY); },
    /** Harness only: forget the answer, so a check can see the offer again. */
    forget() { spentHere = null; try { storage?.removeItem(OFFER_KEY); } catch { /* nothing kept */ } },
  };
}

/** True once, on the page a Jump brought the visitor to; the stamp is cleared as it is read. */
export function takeJumped(store = session()) {
  try {
    const v = store?.getItem(JUMPED_KEY);
    if (v) store.removeItem(JUMPED_KEY);
    return !!v;
  } catch { return false; }
}

export function createHints({ el = null, storage = local(), blocked = () => false,
  wait = (fn, ms) => setTimeout(fn, ms), cancel = (id) => clearTimeout(id) } = {}) {
  const seenHere = new Set();
  let timer = null, current = null;
  const stored = () => {
    try { const v = JSON.parse(storage?.getItem(HINTS_KEY) || '[]'); return Array.isArray(v) ? v : []; } catch { return []; }
  };
  const seen = (id) => seenHere.has(id) || stored().includes(id);
  function hide() {
    if (timer !== null) { cancel(timer); timer = null; }
    current = null;
    if (el) el.hidden = true;
  }
  return {
    /** Show hint `id` if this device has not had it and nothing holds it back; true when it showed. */
    show(id) {
      if (!HINT_IDS.includes(id) || seen(id)) return false;
      let held = false;
      try { held = !!blocked(); } catch { held = false; }
      if (held) return false;
      seenHere.add(id);
      try { storage?.setItem(HINTS_KEY, JSON.stringify([...new Set([...stored(), id])])); } catch { /* this page only */ }
      current = id;
      if (el) { el.textContent = hintText(id); el.dataset.hint = id; el.hidden = false; }
      if (timer !== null) cancel(timer);
      timer = wait(hide, HINT_MS);
      return true;
    },
    hide,
    seen,
    /** Harness only: forget every hint, so a check can see them again. */
    forget() { hide(); seenHere.clear(); try { storage?.removeItem(HINTS_KEY); } catch { /* nothing kept */ } },
    get showing() { return !!el && !el.hidden; },
    get current() { return current; },
  };
}
