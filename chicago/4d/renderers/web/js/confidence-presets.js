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
 * The choice persists in localStorage['chicago4d.confidence'] (DESIGN §09) as the looks
 * the colouring and hiding do not already carry; the HUD's own keys carry the rest.
 */
import { GRADE_COLORS, GRADE_LOOK } from './confidence.js';

export const LEVELS = Object.freeze(['attested', 'inferred', 'reconstructed']);
export const STORE_KEY = 'chicago4d.confidence';

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
const sameColour = (view, level) => (view.grade(level)?.color ?? '').toLowerCase()
  === `#${GRADE_COLORS[level].scene.toString(16).padStart(6, '0')}`;

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
    if (on && !LEVELS.every((l) => sameLook(view.grade(l), p.looks[l]) && sameColour(view, l))) continue;
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
  for (const level of LEVELS) {
    view.setGrade(level, { color: GRADE_COLORS[level].scene, mode: p.looks[level].mode, opacity: p.looks[level].opacity });
  }
  const hiddenNow = new Set(hud.hiddenLevels);
  for (const level of LEVELS) {
    const hide = p.hidden.includes(level);
    if (hiddenNow.has(level) !== hide) hud.setHidden(level, hide, { announce: false });
  }
  if (hud.confidenceOn !== p.on) hud.setConfidence(p.on, { announce: false });
  saveLooks(view, storage);
  if (announce) hud.say?.(`${p.label}: ${p.note}`);
  return p.id;
}

/** The C key: BY GRADE on, or (from any coloured state) back to NORMAL. */
export function toggleByGrade(deps) {
  return applyPreset(deps.hud?.confidenceOn ? 'normal' : 'bygrade', deps);
}

/** Keep each grade's look, for the next visit. Storage refused, it is simply not kept. */
export function saveLooks(view, storage = globalThis.localStorage) {
  try {
    const out = {};
    for (const level of LEVELS) {
      const g = view.grade(level);
      out[level] = { mode: g.mode, opacity: Math.round(g.opacity * 100) / 100, color: g.color };
    }
    storage?.setItem(STORE_KEY, JSON.stringify({ looks: out }));
  } catch { /* a convenience */ }
}

/** Put the kept looks back on the renderer at boot (before the HUD restores the colouring). */
export function restoreLooks(view, storage = globalThis.localStorage) {
  let kept = null;
  try { kept = JSON.parse(storage?.getItem(STORE_KEY) ?? 'null'); } catch { kept = null; }
  if (!kept?.looks) return false;
  let any = false;
  for (const level of LEVELS) {
    const g = kept.looks[level];
    if (!g || typeof g !== 'object') continue;
    if (view.setGrade(level, { mode: g.mode, opacity: g.opacity, ...(typeof g.color === 'string' ? { color: g.color } : {}) })) any = true;
  }
  return any;
}
