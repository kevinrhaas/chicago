/**
 * confidence-rows.js — the Confidence view's per-grade rows (T-2648, NAV-602; DESIGN §09, M9).
 *
 * "Each grade gets one row with four controls": Show (the HUD's hidden set, T-2647's
 * switches), Colour (four curated swatches), Look (Tint, Ghost or Dither) and Opacity
 * (0-100 %). This module is the state side of the three that are new — what each swatch
 * is, which one is in force, and what a tap puts on the renderer — so the app
 * (apps/confidence-view.js) only draws them, and a test can drive them without a page.
 *
 * Every control writes the renderer's per-grade uniforms through confidence.js
 * `setGrade` (T-2646) and nothing else: a colour or an opacity is a uniform write, and a
 * Look re-plans which objects the ghost pass draws. No geometry is rebuilt and no
 * material recompiled, so a slider dragged across its range costs a frame nothing.
 *
 * THE SWATCHES are four SETS, one swatch per grade in each, so that picking the same
 * place in every row gives a palette that was chosen as a whole:
 *
 *   medal   gold / silver / bronze — the grade colours (GRADE_COLORS, T-2671), the default.
 *   garden  green / sky / plum.
 *   ember   cream / amber / brick.
 *   safe    blue / yellow / vermilion — the colour-blind-safe set: three colours of
 *           Okabe and Ito's "Color Universal Design" palette (2008), drawn up so that
 *           people with the common colour-vision deficiencies can tell them apart.
 *           tools/test_confidence_rows.mjs holds the three apart under simulated
 *           protanopia, deuteranopia and tritanopia (the measure check_grade_colors.mjs
 *           holds the defaults to), and every row's four apart to ordinary vision.
 *
 * A curated set in force on all three grades is what the presets keep (confidence-
 * presets.js): a visitor who chose the colour-blind-safe set is not handed gold back by
 * X-RAY or the C key. A mix of sets is the visitor's own, and no preset matches it.
 */
import { GRADE_COLORS, GRADE_MODES } from './confidence.js';

export const LEVELS = Object.freeze(['attested', 'inferred', 'reconstructed']);
/** The three looks, in the order the row offers them. */
export const LOOKS = Object.freeze(Object.keys(GRADE_MODES));

const hex = (n) => `#${n.toString(16).padStart(6, '0')}`;
const set = (id, names, colours, extra = {}) => Object.freeze({
  id, ...extra,
  names: Object.freeze(names),
  colours: Object.freeze(colours),
});

export const SWATCH_SETS = Object.freeze([
  set('medal', { attested: 'gold', inferred: 'silver', reconstructed: 'bronze' }, {
    attested: hex(GRADE_COLORS.attested.scene),
    inferred: hex(GRADE_COLORS.inferred.scene),
    reconstructed: hex(GRADE_COLORS.reconstructed.scene),
  }),
  set('garden', { attested: 'green', inferred: 'sky', reconstructed: 'plum' },
    { attested: '#3fa66b', inferred: '#7fb4e0', reconstructed: '#9a5aa8' }),
  set('ember', { attested: 'cream', inferred: 'amber', reconstructed: 'brick' },
    { attested: '#f2e6c4', inferred: '#e3a24a', reconstructed: '#b23a2e' }),
  set('safe', { attested: 'blue', inferred: 'yellow', reconstructed: 'vermilion' },
    { attested: '#0072b2', inferred: '#f0e442', reconstructed: '#d55e00' }, { colourBlindSafe: true }),
]);
export const DEFAULT_SET = 'medal';
export const SAFE_SET = 'safe';
export const setById = (id) => SWATCH_SETS.find((s) => s.id === id) ?? null;

/** One grade's four swatches, in set order: `{ set, name, hex, colourBlindSafe }`. */
export function swatchesOf(level) {
  return SWATCH_SETS.map((s) => ({ set: s.id, name: s.names[level], hex: s.colours[level], colourBlindSafe: !!s.colourBlindSafe }));
}

const colourOf = (view, level) => String(view?.grade?.(level)?.color ?? '').toLowerCase();

/** Which swatch a grade is wearing: its set's id, or null for a colour no swatch has. */
export function swatchOf(view, level) {
  const c = colourOf(view, level);
  return SWATCH_SETS.find((s) => s.colours[level] === c)?.id ?? null;
}

/** The curated set all three grades are wearing, or null for a mix (or a stray colour). */
export function setInForce(view) {
  const first = swatchOf(view, LEVELS[0]);
  return first && LEVELS.every((l) => swatchOf(view, l) === first) ? first : null;
}

/** The colours a preset puts on: the whole set in force, else the grade colours. */
export function presetColours(view) {
  return setById(setInForce(view) ?? DEFAULT_SET).colours;
}

/**
 * A row control was used: the scene has to show it. The colouring comes on (a colour or
 * a look is not drawn without it) and the grade is shown again if it was hidden.
 */
function reveal({ hud }, level) {
  if (!hud) return;
  if (hud.hiddenLevels?.includes(level)) hud.setHidden(level, false, { announce: false });
  if (!hud.confidenceOn) hud.setConfidence(true, { announce: false });
}

/** Put one swatch (a set's id) on one grade. Returns the look now in force, or null. */
export function setSwatch(deps, level, setId) {
  const s = setById(setId);
  if (!s || !LEVELS.includes(level) || !deps?.view) return null;
  const look = deps.view.setGrade(level, { color: s.colours[level] });
  if (look) reveal(deps, level);
  return look;
}

/** Put a whole set on all three grades (the colour-blind-safe one, from its own switch). */
export function applySet(deps, setId) {
  const s = setById(setId);
  if (!s || !deps?.view) return null;
  for (const level of LEVELS) deps.view.setGrade(level, { color: s.colours[level] });
  if (deps.hud && !deps.hud.confidenceOn) deps.hud.setConfidence(true, { announce: false });
  return s.id;
}

/** One grade's Look: 'tint', 'ghost' or 'dither'. */
export function setLook(deps, level, mode) {
  if (!LOOKS.includes(mode) || !LEVELS.includes(level) || !deps?.view) return null;
  const look = deps.view.setGrade(level, { mode });
  if (look) reveal(deps, level);
  return look;
}

/** One grade's opacity, as the slider gives it: a whole percent, 0 to 100. */
export function setOpacity(deps, level, percent) {
  const p = Number(percent);
  if (!Number.isFinite(p) || !LEVELS.includes(level) || !deps?.view) return null;
  const look = deps.view.setGrade(level, { opacity: Math.min(100, Math.max(0, Math.round(p))) / 100 });
  if (look) reveal(deps, level);
  return look;
}

/** A grade's opacity as the slider shows it: a whole percent. */
export const percentOf = (look) => Math.round((Number(look?.opacity) || 0) * 100);
