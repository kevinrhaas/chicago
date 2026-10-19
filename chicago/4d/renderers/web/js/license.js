/**
 * The Navigator License (T-2665, NAV-805; design doc section 11, M10 step 07: "Tap Finish.
 * Awards the NAVIGATOR LICENSE keepsake").
 *
 * Finishing the Field Check (js/tour.js, Finish on step 07) awards it, once per device.
 * Skip is not finishing, and a replay that finishes again keeps the one license. It is
 * shown with the Jaunt keepsakes, in the Jaunts app's daybook (js/jaunt-preview.js draws
 * the card from `card()` below), in every year: it is the device's, not one year's daybook,
 * so Reset daybook does not take it.
 *
 * Kept in localStorage under its own key, every read and write inside try/catch: where
 * storage is refused the license is held for this page only, never an error (as
 * js/roam-tip.js and js/tour-offer.js). A device that finished the Field Check before the
 * license existed (the tour's own record says `done`) holds it too, undated.
 */
import { t } from './strings/index.js';
import './strings/license.js';

export const LICENSE_KEY = 'chicago4d.navigatorLicense';
const TOUR_KEY = 'chicago4d.tour'; // js/tour.js

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };

/** "Oct 18, 2026" for a stored ISO time, or null. */
export function issuedOn(iso) {
  const d = typeof iso === 'string' ? new Date(iso) : null;
  if (!d || Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function createLicense({ storage = local(), now = () => new Date() } = {}) {
  let here = null; // awarded on this page; what is held when storage is refused
  const get = (k) => { try { return storage?.getItem(k) ?? null; } catch { return null; } };
  const json = (k) => { try { return JSON.parse(get(k) || 'null'); } catch { return null; } };
  const saved = () => { const v = json(LICENSE_KEY); return v && typeof v === 'object' ? v : null; };
  const own = () => here ?? saved();
  const api = {
    /** Whether this device holds the license. */
    get held() { return !!(own() || json(TOUR_KEY)?.done === true); },
    /** When it was issued (ISO), or null for one held from an earlier finish. */
    get earned() { const e = own()?.earned; return typeof e === 'string' ? e : null; },
    /** Finishing the Field Check: true the first time, false once held. */
    award() {
      if (own()) return false;
      here = { earned: now().toISOString() };
      try { storage?.setItem(LICENSE_KEY, JSON.stringify(here)); } catch { /* held for this page only */ }
      return true;
    },
    /** The keepsake card's words, or null while it is not held. */
    card() {
      if (!api.held) return null;
      const date = issuedOn(api.earned);
      return { form: t('license.form'), title: t('license.title'), text: t('license.text'),
        line: date ? t('license.issued', { date }) : t('license.held') };
    },
    /** The line that says it was awarded, as the Finish closes the tour. */
    awardedText: () => t('license.awarded'),
    /** Harness only: forget the license, so a check can award it again. */
    forget() { here = null; try { storage?.removeItem(LICENSE_KEY); } catch { /* nothing kept */ } },
  };
  return api;
}
