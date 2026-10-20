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
 * Settings › Show › "Name of what you look at" turns the tag off (`setTagShown`); the
 * Inspect key stays either way.
 *
 * T-2942 (owner, 2026-10-20: "default that to put that on the right side and make it
 * smaller, so it fits with the navigation below the address and its not duplicative with
 * the address show, the tags should have a consistency, you can keep the existing and make
 * it an option to display in center, or maybe bottom … and you can also have a setting to
 * control if its always shown or disappears after a few seconds which should be the
 * default"). Two more choices in Settings › Show:
 *
 *   place     'right' (default) docks the tag in the right-hand column under the address,
 *             styled like that card; 'centre' is T-2627's place under the crosshair, kept
 *             as it was; 'bottom' puts it at the top of the HUD's bottom row.
 *   hold      'fade' (default) is T-2736's glance; 'always' keeps it while the building
 *             is in the reticle.
 *
 * Docked on the right, the tag does not repeat the address: when the building's name IS
 * the address the card already shows (a Prairie Avenue house titled by its number), the
 * name would say the same thing twice, so the docked tag stays hidden and the Inspect key
 * carries the tap (`sameAddress`). Centre and bottom show it as they always did.
 */
import { formatDistance } from './units.js';
import { displayName } from './display-name.js';

export const DWELL_MS = 400;
export const TAG_WITHIN_M = 40;
export const HOLD_MS = 3000;
export const FADE_MS = 600;

/** T-2942: where the tag shows, and whether it fades. The first of each is the default. */
export const TAG_PLACES = Object.freeze(['right', 'centre', 'bottom']);
export const TAG_HOLDS = Object.freeze(['fade', 'always']);
export const normalTagPlace = (v) => (TAG_PLACES.includes(v) ? v : TAG_PLACES[0]);
export const normalTagHold = (v) => (TAG_HOLDS.includes(v) ? v : TAG_HOLDS[0]);

/** The building's name a visitor reads (never an id). */
export function tagName(t) {
  if (!t) return '';
  // A record with no name falls back to its id in displayName; a visitor never reads an id.
  const title = displayName(t.record?.sidecar ?? {}, t.id).title;
  return title && !/[a-z0-9]_[a-z0-9]/i.test(title) ? title : 'A building';
}

/** The tag's words: the building's display name and its distance, in the visitor's units. */
export function tagWords(t, units = 'imperial') {
  if (!t) return '';
  return `${tagName(t)} · ${formatDistance(t.distance, units)}`;
}

/** An address reduced to what two spellings of it share: "1800 S. Prairie Ave." and
 * "1800 Prairie Avenue" are one address. Exported for the tests. */
export function addressKey(text) {
  return String(text ?? '').toLowerCase()
    .replace(/[.,]/g, ' ')
    .replace(/\b(?:s|south|n|north|e|east|w|west)\b/g, ' ')
    .replace(/\bavenue\b/g, 'ave').replace(/\bstreet\b/g, 'st').replace(/\bboulevard\b/g, 'blvd')
    .replace(/\s+/g, ' ').trim();
}

/** T-2942: does a building's name only repeat an address the card already shows? True when
 * the name, or the part of it before a dash, is one of those addresses. */
export function sameAddress(name, addresses = []) {
  const head = addressKey(String(name ?? '').split(/\s[—–-]\s/)[0]);
  if (!head || !/\d/.test(head)) return false;
  return addresses.some((a) => addressKey(a) === head);
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
  tagShown = true,
  place = TAG_PLACES[0],
  holdMode = TAG_HOLDS[0],
  // T-2942: the three places the tag can stand ({ right, centre, bottom } → a parent
  // element, and the node to insert before); a missing one leaves the tag where it is.
  slots = null,
  // The addresses the right-hand card shows now, so a docked tag never repeats them.
  addresses = () => [],
  wait = (fn, ms) => setTimeout(fn, ms),
  cancel = (id) => clearTimeout(id),
} = {}) {
  let shown = null;    // the target the tag is showing
  let pending = null;  // the timer waiting out the dwell
  let fading = null;   // the timer holding, then fading, the tag
  let spent = null;    // the id whose tag has faded: it stays gone until the reticle leaves it
  let enabled = true;
  let tagOn = !!tagShown;
  let where = normalTagPlace(place);
  let holding = normalTagHold(holdMode);

  /** The tag's own children: the name and the distance, so the docked card can set them
   * apart; its text stays "NAME · DISTANCE" (the label is drawn by CSS from data-label). */
  function words(t) {
    if (!tagEl) return;
    const doc = tagEl.ownerDocument;
    const name = tagName(t), dist = ` · ${formatDistance(t.distance, units())}`;
    if (!doc?.createElement || !tagEl.replaceChildren) { tagEl.textContent = `${name}${dist}`; return; }
    const a = doc.createElement('span'); a.className = 'tt-name'; a.textContent = name;
    const b = doc.createElement('span'); b.className = 'tt-dist'; b.textContent = dist;
    tagEl.replaceChildren(a, b);
  }

  /** Docked on the right and naming only the address the card shows: say nothing. */
  const repeats = (t) => where === 'right' && !!t && sameAddress(tagName(t), addresses?.() ?? []);

  function seat() {
    if (tagEl?.dataset) tagEl.dataset.place = where;
    const slot = slots?.[where];
    if (!tagEl || !slot?.parent) return;
    const before = slot.before ?? null;
    if (tagEl.parentNode !== slot.parent || (before && tagEl.nextSibling !== before)) {
      slot.parent.insertBefore(tagEl, before && before.parentNode === slot.parent ? before : null);
    }
  }
  seat();

  function stopFade() {
    if (fading !== null) { cancel(fading); fading = null; }
    tagEl?.classList?.remove('is-fading');
  }

  function paint(t) {
    const fresh = !!t && t.id !== shown?.id;
    shown = t;
    if (!t) spent = null;
    const said = tagWords(t, units());
    if (tagEl) {
      tagEl.hidden = !t || !tagOn || spent === t.id || repeats(t);
      if (t) {
        words(t);
        tagEl.setAttribute?.('aria-label', `Inspect ${said}`);
      }
    }
    if (keyEl) {
      keyEl.hidden = !t;
      if (t) keyEl.setAttribute?.('aria-label', `Inspect ${said}`);
    }
    if (!t || fresh) stopFade();
    if (t && fresh && holding === 'fade') arm(t);
  }

  /** T-2736: hold, fade, and stay gone for this building until the reticle leaves it. */
  function arm(t) {
    stopFade();
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
    /** Settings › Show: the visitor's choice to see the tag at all (the Inspect key stays). */
    setTagShown(on) {
      tagOn = !!on;
      if (!tagOn) { stopFade(); if (tagEl) tagEl.hidden = true; }
    },
    /** T-2942: Settings › Show › Where the name shows. Moving it shows it afresh. */
    setPlace(p) {
      where = normalTagPlace(p);
      seat();
      spent = null;
      if (shown) { const t = shown; shown = null; paint(t); }
      return where;
    },
    /** T-2942: Settings › Show › The name: 'fade' after a few seconds, or 'always'. */
    setHold(h) {
      holding = normalTagHold(h);
      spent = null;
      stopFade();
      if (shown) { const t = shown; shown = null; paint(t); }
      return holding;
    },
    get place() { return where; },
    get hold() { return holding; },
    open,
    dispose() { off?.(); hear(null); },
  };
}
