/**
 * Free roam's one-time tip (T-2634, DESIGN §07 "Jaunts": "Free roam: docks the Navigator
 * and shows a one-time tip: 'Tap any building to inspect it.'").
 *
 * Once per device: the first Free roam remembers it in localStorage, inside try/catch —
 * where storage is refused the tip shows once per page instead, never an error. The words
 * follow the controls in use: a tap on a touch screen, a click (or E) with a mouse.
 */
export const ROAM_TIP_KEY = 'chicago4d.roamTipSeen';
export const ROAM_TIP_MS = 6000;

export const tipText = (touch) => (touch ? 'Tap any building to inspect it.' : 'Click any building, or press E, to inspect it.');

export function createRoamTip({ el, storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
  wait = (fn, ms) => setTimeout(fn, ms), cancel = (id) => clearTimeout(id) } = {}) {
  let shownThisPage = false;
  let timer = null;
  const seen = () => {
    if (shownThisPage) return true;
    try { return storage?.getItem(ROAM_TIP_KEY) === '1'; } catch { return false; }
  };
  function hide() {
    if (timer !== null) { cancel(timer); timer = null; }
    if (el) el.hidden = true;
  }
  el?.addEventListener?.('click', hide);
  return {
    /** Show the tip if this device has not had it; true when it showed. */
    show({ touch = false } = {}) {
      if (seen()) return false;
      shownThisPage = true;
      try { storage?.setItem(ROAM_TIP_KEY, '1'); } catch { /* remembered for this page only */ }
      if (el) { el.textContent = tipText(touch); el.hidden = false; }
      if (timer !== null) cancel(timer);
      timer = wait(hide, ROAM_TIP_MS);
      return true;
    },
    hide,
    /** Harness only: forget this device has had the tip, so a check can see it again. */
    forget() { hide(); shownThisPage = false; try { storage?.removeItem(ROAM_TIP_KEY); } catch { /* nothing kept */ } },
    get showing() { return !!el && !el.hidden; },
  };
}
