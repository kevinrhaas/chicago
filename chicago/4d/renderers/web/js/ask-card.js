// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: the card you put your questions on. "Ask <Name>", who they are (their temperament and
 * their record), then their five questions. Tap one: how they come to it, their answer, one or two
 * follow-ups that each reveal more, and a Find key where they send you to someone. "Other
 * questions" goes back to the five, the answered ones ticked. X (or Escape) closes. On a phone it
 * is a sheet along the bottom, like the story card.
 *
 * Nothing here knows the town: tale-teller.js hands it the person and what to do.
 * tools/test_tales.mjs drives it with a fake document.
 */

import { iconSvg } from './menu-icons.js';
import { readingTabs, forgetAge } from './reading-level.js';

/**
 * @param {object} o
 * @param {Document} [o.doc]
 * @param {HTMLElement} [o.parent]
 * @param {(personId: string) => (true|string)} [o.canFind]
 * @param {(personId: string) => void} [o.find]
 * @param {(personId: string, askId: string) => void} [o.answered]   a question was answered
 * @param {() => void} [o.closed]
 */
export function createAskCard({ doc = globalThis.document, parent = null, canFind = () => true,
  find = () => {}, answered = () => {}, closed = () => {} } = {}) {
  const make = (tag, cls, text) => { const n = doc.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const button = (cls, html) => { const b = make('button', cls); b.type = 'button'; if (html != null) b.innerHTML = html; return b; };
  const card = make('section', 'tale-card ask-card');
  card.hidden = true;
  card.setAttribute('role', 'dialog');
  card.setAttribute('aria-label', 'Ask a question');
  const head = make('div', 'tale-head');
  const tag = make('span', 'tale-tag', 'Ask');
  const who = make('span', 'tale-who');
  const shut = button('tale-close');
  shut.textContent = '×';
  shut.setAttribute('aria-label', 'Close the questions');
  head.append(tag, who, shut);
  const persona = make('p', 'ask-persona');
  const body = make('div', 'tale-body ask-body');
  const note = make('p', 'tale-note', 'Reconstructed answers, true to their time, their life and their temper.');
  const keys = make('div', 'tale-keys');
  const findKey = button('tale-key tale-find');
  const backKey = button('tale-key ask-back', `${iconSvg('back', 16)}<span>Other questions</span>`);
  keys.append(findKey, backKey);
  card.append(head, persona, body, note, keys);
  (parent ?? doc.body).append(card);

  let showing = null;   // { teller, personId, persona, asks, done, manner, ask? }
  function close() {
    if (card.hidden) return;
    card.hidden = true;
    const was = showing;
    showing = null;
    closed(was);
  }
  shut.addEventListener('click', close);
  backKey.addEventListener('click', () => { if (showing) list(); });
  findKey.addEventListener('click', () => {
    const p = showing?.ask?.meet?.person;
    if (p && canFind(p) === true) find(p);
  });
  doc.addEventListener?.('keydown', (ev) => {
    if (!card.hidden && ev.key === 'Escape') { ev.stopPropagation?.(); close(); }
  }, true);

  function list() {
    showing.ask = null;
    const ol = make('ol', 'ask-list');
    for (const a of showing.asks) {
      const li = make('li');
      const b = button(`ask-q${showing.done.has(a.id) ? ' ask-done' : ''}`);
      b.append(make('span', 'ask-q-text', a.q));
      if (showing.done.has(a.id)) b.append(make('span', 'ask-tick', '✓'));
      b.addEventListener('click', () => answer(a));
      li.append(b);
      ol.append(li);
    }
    body.replaceChildren(make('p', 'ask-prompt', `What would you like to ask ${showing.teller || 'them'}?`), ol);
    readingTabs(card, { after: persona });
    findKey.hidden = true;
    backKey.hidden = true;
    body.scrollTop = 0;
  }

  function answer(a) {
    showing.ask = a;
    if (!showing.done.has(a.id)) { showing.done.add(a.id); answered(showing.personId, a.id); }
    const parts = [make('p', 'ask-you', a.q)];
    const manner = showing.manner?.(a.id);
    if (manner) parts.push(make('p', 'ask-manner', manner));
    for (const t of a.a) parts.push(make('p', null, t));
    const more = make('div', 'ask-more');
    for (const m of a.more ?? []) {
      const b = button('tale-key ask-follow', iconSvg('chat', 16));
      b.append(make('span', null, m.q));
      b.addEventListener('click', () => {
        const block = make('div', 'ask-reveal');
        block.append(make('p', 'ask-you', m.q), ...m.a.map((t) => make('p', null, t)));
        more.replaceChildren(...[...more.children].map((c) => (c === b ? block : c)));
        readingTabs(card, { after: persona }); // T-3645: the follow-up at the age shown
      });
      more.append(b);
    }
    parts.push(more);
    body.replaceChildren(...parts);
    const meet = a.meet;
    findKey.hidden = !meet;
    if (meet) {
      const ok = canFind(meet.person);
      findKey.disabled = ok !== true;
      findKey.title = ok === true ? `Find ${meet.name} in town` : String(ok);
      findKey.innerHTML = `${iconSvg('walk', 16)}<span>Find ${meet.name}</span>`;
      if (ok !== true) findKey.append(make('small', 'tale-why', ok));
    }
    backKey.hidden = false;
    // T-3645: the answer at the reader's age, where it is written at more than one.
    readingTabs(card, { after: persona });
    body.scrollTop = 0;
    card.scrollTop = 0;
  }

  return {
    el: card,
    get open() { return !card.hidden; },
    get showing() { return showing; },
    /**
     * @param {object} o
     * @param {string} o.teller          their name
     * @param {string} o.personId
     * @param {{label: string, who: string}} [o.persona]
     * @param {object[]} o.asks          their questions now
     * @param {Set<string>} [o.done]     the ones already answered
     * @param {(askId: string) => string} [o.manner]   how they come to an answer
     */
    show({ teller, personId, persona: p = null, asks, done = new Set(), manner = null }) {
      showing = { teller, personId, persona: p, asks, done: new Set(done), manner, ask: null };
      forgetAge(card);
      who.textContent = `Ask ${teller || 'them'}`;
      persona.textContent = [p?.label, p?.who].filter(Boolean).join('. ').replace(/\.\./g, '.');
      persona.hidden = !persona.textContent;
      list();
      card.hidden = false;
      return card;
    },
    /** Answer one of the questions showing (as a tap would). */
    pick(askId) { const a = showing?.asks.find((x) => x.id === askId); if (a) answer(a); return !!a; },
    close,
  };
}
