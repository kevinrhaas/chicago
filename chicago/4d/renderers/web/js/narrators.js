// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3627: the narrators a visitor chooses between in Settings › Sound, on their own so the
 * Settings card can offer them without loading the narration player (narration.js), which
 * only an outing that speaks ever runs. narration.js keeps its own copy, because it imports
 * nothing (chicago-4d-narration.yml checks it out alone to voice the scripts), and
 * tools/test_narration.mjs holds the two equal.
 *
 * (The owner, 2026-11-13: "i have two narrators, people should be able to select which one
 * they use the essayist is the default".) The voicer voices every narrator script once for
 * each; data/narration/voices.json binds each to an ElevenLabs voice, and
 * tools/test_narration.mjs holds the two lists equal.
 */
export const NARRATORS = Object.freeze([
  { id: 'essayist', label: 'Cultivated Essayist' },
  { id: 'storyteller', label: 'Midwestern Storyteller' },
]);
export const DEFAULT_NARRATOR = 'essayist';
export const normalNarrator = v => (NARRATORS.some(n => n.id === v) ? v : DEFAULT_NARRATOR);
