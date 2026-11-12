/**
 * T-3571 — the sound keys outside Settings: the arrival's speaker (T-3532) and the
 * Navigator's two mute keys (the owner, 2026-11-12: "add mute all sound and mute music
 * toggles to navigator"). Each flips one of Settings › Sound's levels between silence
 * and the level it had before, so a key and its slider never disagree.
 *
 *   all    soundMaster  every sound; lit while the master level is 0
 *   music  soundMusic   the period music only; lit while the music level is 0
 *
 * Pure: no DOM, no storage. js/main.js reads the levels, applies the change and paints.
 */
import { SOUND_DEFAULTS, normalVolume } from './settings-app.js';

export const MUTE_KEYS = Object.freeze({ all: 'soundMaster', music: 'soundMusic' });
/** Where each level's last audible value is kept, to put back on unmute. */
const LAST = Object.freeze({ soundMaster: 'soundLastMaster', soundMusic: 'soundLastMusic' });
/** The level an unmute restores when nothing audible was ever kept. */
const RESTORE = Object.freeze({ soundMaster: 0.8, soundMusic: SOUND_DEFAULTS.soundMusic });

/** True while `key` is silent in `levels`. */
export function isMuted(levels, key) {
  return normalVolume(levels?.[key], SOUND_DEFAULTS[key]) <= 0;
}

/**
 * The change one press makes: an audible level goes to 0 and is kept as the last level;
 * a silent one comes back to its last audible level (or the restore default). Returns
 * `{ [key], [lastKey], soundChosen: true }`; a press is the visitor's choice (T-2941).
 */
export function flipSound(levels, key) {
  if (!LAST[key]) throw new Error(`flipSound: no mute for ${key}`);
  const lastKey = LAST[key];
  const now = normalVolume(levels?.[key], SOUND_DEFAULTS[key]);
  if (now > 0) return { [key]: 0, [lastKey]: now, soundChosen: true };
  const back = normalVolume(levels?.[lastKey], RESTORE[key]) || RESTORE[key];
  return { [key]: back, [lastKey]: back, soundChosen: true };
}
