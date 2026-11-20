// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: "Tell me a story" and "Ask a question" for everyone you can greet, in every year.
 * Joins the shared Interact engine (interact.js `extend`): wherever a person offers Greet, Tell
 * me a story and Ask a question follow it. The person stops, turns to you, waves, and talks
 * while the card is open. Each comes to you in their own temper, from their own history
 * (tales.js personaOf), and that temper leans which stories and questions they offer.
 *
 * main.js hands in what it alone knows (the scene, where the data is, the HUD, Find);
 * the stories and the memory of what you heard are tales.js, the questions asks.js, the cards
 * tale-card.js and ask-card.js.
 */

import { createTales, personaOf, mannerOf } from './tales.js';
import { createTaleCard } from './tale-card.js';
import { createAsks } from './asks.js';
import { createAskCard } from './ask-card.js';

import { TALE_ACTION, ASK_ACTION, storyAction, askAction, withStory } from './tale-actions.js';
export { TALE_ACTION, ASK_ACTION, storyAction, askAction, withStory };
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
  const talk = (thing) => {
    hush();
    talking = thing.actor ?? null;
    talking?.actions?.setTalk?.(true);
    quiet = setTimeout(() => { talking?.actions?.setTalk?.(false); }, TALK_S * 1000);
  };
  const idOf = (thing) => thing.personId ?? thing.actor?.personId ?? String(thing.id).replace(/^person:/, '');
  let asked = null;
  const card = createTaleCard({ doc, canFind,
    find: (id) => { card.close(); find(id); },
    another: () => { if (asked) void tell(asked); },
    closed: hush,
  });
  const asks = createAsks({ scene, load: () => tales.load(), ...(storage !== undefined ? { storage } : {}) });
  const askCard = createAskCard({ doc, canFind,
    find: (id) => { askCard.close(); find(id); },
    answered: (pid, askId) => asks.asked(pid, askId),
    closed: hush,
  });
  async function tell(thing) {
    asked = thing;
    const personId = idOf(thing);
    const sex = sexOf(thing);
    let got = null;
    try { got = await tales.tell(personId, { sex }); } catch { say('Stories could not be loaded just now'); return null; }
    if (!got) { say(thing.name ? `${thing.name} has no story just now` : 'No story just now'); return null; }
    askCard.close();
    talk(thing);
    const lib = await tales.load();
    const persona = personaOf(lib, personId, sex);
    card.show({ teller: thing.name, personId, tale: got.tale, own: got.own, persona,
      manner: mannerOf(lib, persona, `${personId}:${got.tale.id}`) });
    return got;
  }
  async function ask(thing) {
    const personId = idOf(thing);
    const sex = sexOf(thing);
    let got = null;
    try { got = await asks.offer(personId, { sex }); } catch { say('Questions could not be loaded just now'); return null; }
    if (!got.asks.length) { say(thing.name ? `${thing.name} has nothing to say just now` : 'Nothing to say just now'); return null; }
    card.close();
    talk(thing);
    askCard.show({ teller: thing.name, personId, persona: got.persona, asks: got.asks, done: got.done,
      manner: (askId) => mannerOf(got.lib, got.persona, `${personId}:${askId}`) });
    return got;
  }
  interactions.extend?.((thing, actions) => withStory(thing, actions, (t) => { void tell(t); }, (t) => { void ask(t); }));
  return { tales, card, tell, asks, askCard, ask };
}
