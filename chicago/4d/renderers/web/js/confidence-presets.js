/**
 * confidence-presets.js — the Confidence view's four presets (T-2647, NAV-601; DESIGN §09).
 *
 *   NORMAL         everything shown, no colour. The default.
 *   BY GRADE       the Confidence view as it has always been: Attested gold, Inferred
 *                  silver, Reconstructed bronze and dithered. The C key toggles it.
 *   ATTESTED ONLY  only the parts somebody wrote down: Inferred and Reconstructed hidden,
 *                  no colour — exactly what hiding the two by hand gives (QA-12).
 *   X-RAY          Attested solid, Inferred at 50 %, Reconstructed ghosted at 25 %.
 *
 * A preset is three things put in force together: whether the colouring is on (the
 * HUD's Confidence view switch), which grades are hidden (the HUD's hidden set), and each
 * grade's look on the renderer (confidence.js setGrade). The HUD keeps the first two, as
 * it always has, so `setConfidenceView`, the hidden set's storage and every reader of
 * them are unchanged; the looks are the renderer's. Which preset is on is READ back from
 * that state, never stored beside it, so the app cannot show a preset the scene is not
 * in — a state no preset matches shows none pressed (T-2648's per-grade rows make those).
 *
 * T-2648: the colours a preset puts on are the curated swatch set all three grades are
 * wearing (confidence-rows.js) — the grade colours unless a visitor chose another whole
 * set, such as the colour-blind-safe one, which no preset takes away.
 *
 * The choice persists in localStorage['chicago4d.confidence'] (DESIGN §09): the looks
 * here, the colouring and the hidden set from the HUD, all in one record that each writer
 * merges into (T-2649, confidence-store.js), so it carries to the next page and year.
 */
import { GRADE_LOOK } from './confidence.js';
import { presetColours, setInForce, DEFAULT_SET } from './confidence-rows.js';
import { STORE_KEY, readChoices, keepChoices } from './confidence-store.js';

export const LEVELS = Object.freeze(['attested', 'inferred', 'reconstructed']);
export { STORE_KEY };

const looks = (inferred, reconstructed) => Object.freeze({
  attested: GRADE_LOOK.attested,
  inferred,
  reconstructed,
});

export const PRESETS = Object.freeze([
  Object.freeze({ id: 'normal', label: 'Normal', on: false, hidden: Object.freeze([]), looks: looks(GRADE_LOOK.inferred, GRADE_LOOK.reconstructed),
    note: 'Everything shown, no colour.' }),
  Object.freeze({ id: 'bygrade', label: 'By grade', on: true, hidden: Object.freeze([]), looks: looks(GRADE_LOOK.inferred, GRADE_LOOK.reconstructed),
    note: 'Attested gold, Inferred silver, Reconstructed bronze.' }),
  Object.freeze({ id: 'attested', label: 'Attested only', on: false, hidden: Object.freeze(['inferred', 'reconstructed']), looks: looks(GRADE_LOOK.inferred, GRADE_LOOK.reconstructed),
    note: 'Only the parts somebody wrote down.' }),
  Object.freeze({ id: 'xray', label: 'X-ray', on: true, hidden: Object.freeze([]),
    looks: looks(Object.freeze({ mode: 'ghost', opacity: 0.5 }), Object.freeze({ mode: 'ghost', opacity: 0.25 })),
    note: 'Attested solid, Inferred at half, Reconstructed ghosted.' }),
]);

export const presetById = (id) => PRESETS.find((p) => p.id === id) ?? null;

const close = (a, b) => Math.abs(a - b) < 0.005;
const sameLook = (a, b) => a.mode === b.mode && close(a.opacity, b.opacity);
// The colours are a preset's when all three grades wear one curated set (T-2648).
const sameColours = (view) => setInForce(view) !== null;

/**
 * Which preset the scene is in, read from the state itself: the colouring, the hidden
 * set and the looks. Looks only count while the colouring is on (they are not drawn
 * otherwise). Null when no preset matches.
 */
export function presetOf({ on, hidden, view }) {
  const gone = new Set(hidden);
  for (const p of PRESETS) {
    if (p.on !== !!on) continue;
    if (p.hidden.length !== gone.size || !p.hidden.every((l) => gone.has(l))) continue;
    if (on && !(sameColours(view) && LEVELS.every((l) => sameLook(view.grade(l), p.looks[l])))) continue;
    return p.id;
  }
  return null;
}

/**
 * Put a preset in force: the looks first (so the first frame coloured is the right
 * one), then the hidden set, then the colouring. `hud` is the HUD (setConfidence,
 * setHidden, hiddenLevels); `view` the renderer's confidence view.
 */
export function applyPreset(id, { hud, view, storage = null, announce = true } = {}) {
  const p = presetById(id);
  if (!p || !hud || !view) return null;
  const colours = presetColours(view);
  const ownSet = setInForce(view) ?? DEFAULT_SET;
  for (const level of LEVELS) {
    view.setGrade(level, { color: colours[level], mode: p.looks[level].mode, opacity: p.looks[level].opacity });
  }
  const hiddenNow = new Set(hud.hiddenLevels);
  for (const level of LEVELS) {
    const hide = p.hidden.includes(level);
    if (hiddenNow.has(level) !== hide) hud.setHidden(level, hide, { announce: false });
  }
  if (hud.confidenceOn !== p.on) hud.setConfidence(p.on, { announce: false });
  saveLooks(view, storage);
  // BY GRADE's note names gold, silver and bronze; under another set it says only its name.
  if (announce) hud.say?.(p.id === 'bygrade' && ownSet !== DEFAULT_SET ? p.label : `${p.label}: ${p.note}`);
  return p.id;
}

/** The C key: BY GRADE on, or (from any coloured state) back to NORMAL. */
export function toggleByGrade(deps) {
  return applyPreset(deps.hud?.confidenceOn ? 'normal' : 'bygrade', deps);
}

/** Keep each grade's look, for the next visit (the colouring and hidden set kept beside
 * them stay as they are). Storage refused, it is simply not kept; the scene is unchanged. */
export function saveLooks(view, storage = globalThis.localStorage) {
  try {
    const out = {};
    for (const level of LEVELS) {
      const g = view.grade(level);
      out[level] = { mode: g.mode, opacity: Math.round(g.opacity * 100) / 100, color: g.color };
    }
    keepChoices({ looks: out }, storage);
  } catch { /* a convenience */ }
  // T-2649: and say the looks moved, for whoever shows them beside the app (the HUD legend).
  try { globalThis.document?.dispatchEvent(new CustomEvent('chicago4d-confidence')); } catch { /* no page */ }
}

/** Put the kept looks back on the renderer at boot (before the HUD restores the colouring). */
export function restoreLooks(view, storage = globalThis.localStorage) {
  const kept = readChoices(storage);
  if (!kept.looks) return false;
  let any = false;
  for (const level of LEVELS) {
    const g = kept.looks[level];
    if (!g || typeof g !== 'object') continue;
    if (view.setGrade(level, { mode: g.mode, opacity: g.opacity, ...(typeof g.color === 'string' ? { color: g.color } : {}) })) any = true;
  }
  return any;
}
