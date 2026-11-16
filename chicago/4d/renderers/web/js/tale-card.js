// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: the card a story is told on. "<Name> tells you a story", the title, the telling,
 * and, where the teller sends you to somebody, a Find key for them. Another story asks the
 * same person again; X (or Escape) closes. On a phone it is a sheet along the bottom.
 *
 * Nothing here knows the town: main.js hands it what to do. tools/test_tales.mjs drives it
 * with a fake document.
 */

import { iconSvg } from './menu-icons.js';

/**
 * @param {object} o
 * @param {Document} [o.doc]
 * @param {HTMLElement} [o.parent]                      where the card lives (document.body)
 * @param {(personId: string) => (true|string)} [o.canFind]  true, or why they cannot be found now
 * @param {(personId: string) => void} [o.find]
 * @param {() => void} [o.another]                      ask the same teller for another story
 * @param {() => void} [o.closed]                       told once the card is put away
 */
export function createTaleCard({ doc = globalThis.document, parent = null, canFind = () => true,
  find = () => {}, another = () => {}, closed = () => {} } = {}) {
  const make = (tag, cls, text) => { const n = doc.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const card = make('section', 'tale-card');
  card.hidden = true;
  card.setAttribute('role', 'dialog');
  card.setAttribute('aria-label', 'A story');
  const head = make('div', 'tale-head');
  const tag = make('span', 'tale-tag', 'Story');
  const who = make('span', 'tale-who');
  const shut = make('button', 'tale-close', '×');
  shut.type = 'button';
  shut.setAttribute('aria-label', 'Close the story');
  head.append(tag, who, shut);
  const title = make('h3', 'tale-title');
  const body = make('div', 'tale-body');
  const note = make('p', 'tale-note');
  const keys = make('div', 'tale-keys');
  const findKey = make('button', 'tale-key tale-find');
  findKey.type = 'button';
  const againKey = make('button', 'tale-key tale-again');
  againKey.type = 'button';
  againKey.innerHTML = `${iconSvg('story', 16)}<span>Another story</span>`;
  keys.append(findKey, againKey);
  card.append(head, title, body, note, keys);
  (parent ?? doc.body).append(card);

  let showing = null;
  function close() {
    if (card.hidden) return;
    card.hidden = true;
    const was = showing;
    showing = null;
    closed(was);
  }
  shut.addEventListener('click', close);
  againKey.addEventListener('click', () => { if (showing) another(showing); });
  findKey.addEventListener('click', () => {
    const p = showing?.tale?.meet?.person;
    if (p && canFind(p) === true) { find(p); }
  });
  doc.addEventListener?.('keydown', (ev) => {
    if (!card.hidden && ev.key === 'Escape') { ev.stopPropagation?.(); close(); }
  }, true);

  return {
    el: card,
    get open() { return !card.hidden; },
    get showing() { return showing; },
    /**
     * @param {object} o
     * @param {string} o.teller     their name
     * @param {string} o.personId
     * @param {object} o.tale       { id, title, text[], meet? }
     * @param {boolean} [o.own]     one of their own stories
     */
    show({ teller, personId, tale, own = false }) {
      showing = { teller, personId, tale, own };
      who.textContent = `${teller || 'Someone'} tells you a story`;
      title.textContent = tale.title;
      body.replaceChildren(...tale.text.map((t) => make('p', null, t)));
      note.textContent = own
        ? 'A reconstructed telling, from what is known of their life.'
        : 'A reconstructed telling, true to their time and their kind of work.';
      const meet = tale.meet;
      findKey.hidden = !meet;
      if (meet) {
        const ok = canFind(meet.person);
        findKey.disabled = ok !== true;
        findKey.title = ok === true ? `Find ${meet.name} in town` : String(ok);
        findKey.innerHTML = `${iconSvg('walk', 16)}<span>Find ${meet.name}</span>`;
        if (ok !== true) findKey.append(make('small', 'tale-why', ok));
      }
      card.hidden = false;
      body.scrollTop = 0;
      card.scrollTop = 0;
      return card;
    },
    close,
  };
}
