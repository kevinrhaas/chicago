// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: "Tell me a story" for everyone you can greet, in every year. Joins the shared
 * Interact engine (interact.js `extend`): wherever a person offers Greet, Tell me a story
 * follows it. The teller stops, turns to you, waves, and talks while the story is open.
 *
 * main.js hands in what it alone knows (the scene, where the data is, the HUD, Find);
 * the stories and the memory of what you heard are tales.js, the card tale-card.js.
 */

import { createTales } from './tales.js';
import { createTaleCard } from './tale-card.js';

export const TALE_ACTION = 'tale';
const TALK_S = 30;                     // the teller's mouth moves this long, then rests

const FEMALE = /woman|girl|lady|wife|mrs|miss|maid|flynn_mary|frances|christine|mattie/i;

/** A figure's sex as best the drawn body tells it, for one the library has no row for. */
function sexOf(thing) {
  const a = thing.actor;
  const s = a?.person?.sex ?? a?.identity?.person?.sex;
  if (s === 'f' || s === 'female') return 'f';
  if (s === 'm' || s === 'male') return 'm';
  const asset = a?.instance?.appearance?.asset_id ?? a?.assetId ?? '';
  return FEMALE.test(asset) || /^(Mrs\.?|Miss)\b/.test(thing.name ?? '') ? 'f' : 'm';
}

/**
 * The Tell me a story action for a person whose actions are `base`, or null where none
 * belongs (not a person, or no Greet offered: out of reach, in a jaunt's hands).
 */
export function storyAction(thing, base, tell) {
  if (thing?.kind !== 'person' || !Array.isArray(base)) return null;
  const greet = base.find((a) => a.id === 'greet');
  if (!greet) return null;
  return {
    id: TALE_ACTION, label: 'Tell me a story', detail: 'Hear a story of their life and times', said: '',
    steps: [{ label: 'Listening', seconds: 0.8, run(t) {
      // Greet's own first beat: they stop, turn to you and wave.
      if (t === 0) greet.steps?.[0]?.run?.(0);
      if (t >= 1) tell(thing);
    } }],
  };
}

/** Base actions with the story put straight after Greet. */
export function withStory(thing, base, tell) {
  const story = storyAction(thing, base, tell);
  if (!story) return base;
  const at = base.findIndex((a) => a.id === 'greet');
  return [...base.slice(0, at + 1), story, ...base.slice(at + 1)];
}

/**
 * @param {object} o
 * @param {ReturnType<import('./interact.js').createInteractions>} o.interactions
 * @param {string} o.scene                     '1812' | '1835' | '1904'
 * @param {string} o.base                      the URL data/tales/ is served at
 * @param {() => string|null} [o.date]         the scene date now (ISO)
 * @param {(text: string) => void} [o.say]
 * @param {(id: string) => (true|string)} [o.canFind]
 * @param {(id: string) => void} [o.find]
 * @param {Document} [o.doc]
 */
export function createTaleTeller({ interactions, scene, base, date = () => null, say = () => {},
  canFind = () => true, find = () => {}, doc = globalThis.document, fetchJson = null, storage } = {}) {
  const tales = createTales({ scene, base, date, fetchJson, ...(storage !== undefined ? { storage } : {}) });
  let talking = null, quiet = 0;
  const hush = () => {
    clearTimeout(quiet);
    talking?.actions?.setTalk?.(false);
    talking = null;
  };
  let asked = null;
  const card = createTaleCard({ doc, canFind,
    find: (id) => { card.close(); find(id); },
    another: () => { if (asked) void tell(asked); },
    closed: hush,
  });
  async function tell(thing) {
    asked = thing;
    const personId = thing.personId ?? thing.actor?.personId ?? String(thing.id).replace(/^person:/, '');
    let got = null;
    try { got = await tales.tell(personId, { sex: sexOf(thing) }); } catch { say('Stories could not be loaded just now'); return null; }
    if (!got) { say(thing.name ? `${thing.name} has no story just now` : 'No story just now'); return null; }
    hush();
    talking = thing.actor ?? null;
    talking?.actions?.setTalk?.(true);
    quiet = setTimeout(() => { talking?.actions?.setTalk?.(false); }, TALK_S * 1000);
    card.show({ teller: thing.name, personId, tale: got.tale, own: got.own });
    return got;
  }
  interactions.extend?.((thing, actions) => withStory(thing, actions, (t) => { void tell(t); }));
  return { tales, card, tell };
}
