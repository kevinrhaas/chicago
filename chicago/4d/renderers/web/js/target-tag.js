/**
 * target-tag.js — the HUD's target tag and its Inspect key (T-2627, NAV-303; DESIGN §10).
 *
 * When the reticle rests on a building for 400 ms, a tag under it says what and how far:
 * "GLESSNER HOUSE · 38 FT". A tap on the tag, or the quick column's Inspect key that
 * appears with it, opens Inspect; E already inspects down the crosshair.
 *
 * It looks at nothing itself. target.js (T-2617) answers "what is right in front of
 * you" for every asker from one shared probe — at most every 500 ms, and only after the
 * eye has moved — so the tag costs no pick of its own: it listens within 40 m (the
 * Inspect distance) and waits out the dwell on a timer. Losing the target hides the tag
 * at once; a new one waits its own 400 ms. No DOM beyond the two elements it is handed,
 * no THREE: tools/test_navigator.mjs drives it with fakes.
 *
 * T-2736 (owner, 2026-10-17: "if you see it it should show and then disappear"): the
 * tag is a glance, not a sign. It holds HOLD_MS, fades over FADE_MS (`.is-fading`), and
 * stays gone for that building until the reticle leaves it; looking back shows it again.
 * The Inspect key stays while the building is in the reticle, so Inspect is one tap away.
 */
import { formatDistance } from './units.js';
import { displayName } from './display-name.js';

export const DWELL_MS = 400;
export const TAG_WITHIN_M = 40;
export const HOLD_MS = 3000;
export const FADE_MS = 600;

/** The tag's words: the building's display name and its distance, in the visitor's units. */
export function tagWords(t, units = 'imperial') {
  if (!t) return '';
  // A record with no name falls back to its id in displayName; a visitor never reads an id.
  const title = displayName(t.record?.sidecar ?? {}, t.id).title;
  const name = title && !/[a-z0-9]_[a-z0-9]/i.test(title) ? title : 'A building';
  return `${name} · ${formatDistance(t.distance, units)}`;
}

export function createTargetTag({
  target,
  tagEl = null,
  keyEl = null,
  units = () => 'imperial',
  onInspect = () => {},
  dwell = DWELL_MS,
  within = TAG_WITHIN_M,
  hold = HOLD_MS,
  fade = FADE_MS,
  wait = (fn, ms) => setTimeout(fn, ms),
  cancel = (id) => clearTimeout(id),
} = {}) {
  let shown = null;    // the target the tag is showing
  let pending = null;  // the timer waiting out the dwell
  let fading = null;   // the timer holding, then fading, the tag
  let spent = null;    // the id whose tag has faded: it stays gone until the reticle leaves it
  let enabled = true;

  function stopFade() {
    if (fading !== null) { cancel(fading); fading = null; }
    tagEl?.classList?.remove('is-fading');
  }

  function paint(t) {
    const fresh = !!t && t.id !== shown?.id;
    shown = t;
    if (!t) spent = null;
    const words = tagWords(t, units());
    if (tagEl) {
      tagEl.hidden = !t || spent === t.id;
      if (t) {
        tagEl.textContent = words;
        tagEl.setAttribute?.('aria-label', `Inspect ${words}`);
      }
    }
    if (keyEl) {
      keyEl.hidden = !t;
      if (t) keyEl.setAttribute?.('aria-label', `Inspect ${words}`);
    }
    if (!t || fresh) stopFade();
    if (t && fresh) {
      fading = wait(() => {
        tagEl?.classList?.add('is-fading');
        fading = wait(() => {
          fading = null;
          spent = t.id;
          tagEl?.classList?.remove('is-fading');
          if (tagEl) tagEl.hidden = true;
        }, fade);
      }, hold);
    }
  }

  function hear(t) {
    if (pending !== null) { cancel(pending); pending = null; }
    if (!t || !enabled) { paint(null); return; }
    if (shown && shown.id === t.id) { paint(t); return; }
    paint(null);
    pending = wait(() => {
      pending = null;
      // The probe's latest answer, so the distance is the one at the end of the dwell.
      const now = target?.current?.(within) ?? t;
      if (enabled && now && now.id === t.id) paint(now);
    }, dwell);
  }

  const off = target?.on?.(hear, { within }) ?? null;
  const open = () => { if (shown) onInspect(shown); };
  tagEl?.addEventListener?.('click', open);
  keyEl?.addEventListener?.('click', open);

  return {
    get current() { return shown; },
    /** Off while the visitor is not in the town (Home, a menu): the tag never shows there. */
    setEnabled(on) {
      enabled = !!on;
      hear(enabled ? target?.current?.(within) ?? null : null);
    },
    open,
    dispose() { off?.(); hear(null); },
  };
}
