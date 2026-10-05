/**
 * Image sharpness — the renderer's pixel-ratio cap, Settings' three stops
 * (Low 1, Medium 1.5, High 2).
 *
 * T-2110, the owner's answer (a): a phone starts at Low and a desktop stays at
 * Medium. Measured on the phone stand-in, Low drew a frame 26-29 % faster than
 * Medium at Light detail, the single largest lever T-2099 found; the softness
 * is real but small at a phone's viewing distance
 * (docs/measurements/t-2110-sharpness/phone-light-low-medium.jpg).
 *
 * hud.js stores '' for "never chosen", so this guess is never frozen into
 * storage the first time some other setting is saved, and a stored number is
 * the visitor's own choice, always honoured.
 */
export const SHARPNESS_STOPS = Object.freeze([1, 1.5, 2]);

/** The ratio a visitor who never chose starts at. */
export function sharpnessGuess(coarse) {
  return coarse ? 1 : 1.5;
}

/** The ratio in force: the stored choice if there is one, else the guess. */
export function resolveSharpness(stored, coarse) {
  const n = Number(stored);
  return Number.isFinite(n) && n > 0 ? n : sharpnessGuess(coarse);
}
