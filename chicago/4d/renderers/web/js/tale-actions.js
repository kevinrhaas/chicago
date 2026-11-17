// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3627: the Tell me a story and Ask a question ACTIONS, on their own. They are all the town
 * needs at boot to offer both wherever a person offers Greet; the teller that answers them
 * (tale-teller.js, with tales.js, asks.js, tale-card.js and ask-card.js) is loaded the first
 * time a visitor asks, by main.js. tale-teller.js re-exports everything here.
 */

export const TALE_ACTION = 'tale';
export const ASK_ACTION = 'ask';
/**
 * The Tell me a story action for a person whose actions are `base`, or null where none
 * belongs (not a person, or no Greet offered: out of reach, in a jaunt's hands).
 */
export function storyAction(thing, base, tell) {
  return talkAction(thing, base, tell, { id: TALE_ACTION, label: 'Tell me a story', detail: 'Hear a story of their life and times', step: 'Listening' });
}

/** The Ask a question action, where Tell me a story belongs. */
export function askAction(thing, base, ask) {
  return talkAction(thing, base, ask, { id: ASK_ACTION, label: 'Ask a question', detail: 'Five things to ask them, and what they will tell you', step: 'Asking' });
}

function talkAction(thing, base, go, { id, label, detail, step }) {
  if (thing?.kind !== 'person' || !Array.isArray(base)) return null;
  const greet = base.find((a) => a.id === 'greet');
  if (!greet) return null;
  return {
    id, label, detail, said: '',
    steps: [{ label: step, seconds: 0.8, run(t) {
      // Greet's own first beat: they stop, turn to you and wave.
      if (t === 0) greet.steps?.[0]?.run?.(0);
      if (t >= 1) go(thing);
    } }],
  };
}

/** Base actions with the story (and, given `ask`, the questions) put straight after Greet. */
export function withStory(thing, base, tell, ask = null) {
  const story = storyAction(thing, base, tell);
  if (!story) return base;
  const extra = [story, ...(ask ? [askAction(thing, base, ask)] : [])];
  const at = base.findIndex((a) => a.id === 'greet');
  return [...base.slice(0, at + 1), ...extra, ...base.slice(at + 1)];
}

