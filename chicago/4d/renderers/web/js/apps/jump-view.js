/**
 * Jump (SCR 08), loaded the first time it opens (T-2618; DESIGN §07 "Jump").
 *
 * The released destinations as small era cards, the one you are in marked HERE, and
 * Recall to the Observatory as the screen's one signal-red key. Picking another
 * destination goes to its page, which runs that scene's own arrival. Time of day
 * comes with the Jump app's own ticket, when a scene can be lit at another hour.
 */
import { scenePresentation } from '../scene-presentation.js';

const DESTINATIONS = [
  { year: 1835, date: '1835-07-01', href: '../1835/' },
  { year: 1904, date: '1904-07-01', href: '../1904/' },
];

export function mount(el, ctx = {}) {
  const doc = el.ownerDocument;
  const here = Number(ctx.scene?.id ?? ctx.scene?.target_date?.slice(0, 4));
  el.replaceChildren();
  const list = doc.createElement('div');
  list.className = 'nav-jump-list';
  for (const d of DESTINATIONS) {
    const p = scenePresentation(d.year, d.date);
    const card = doc.createElement(d.year === here ? 'div' : 'a');
    card.className = 'nav-block nav-jump';
    if (d.year === here) card.setAttribute('aria-current', 'page');
    else card.href = d.href;
    const k = doc.createElement('span');
    k.className = 'nav-k nav-k-row';
    k.append(Object.assign(doc.createElement('span'), { textContent: String(d.year) }));
    if (d.year === here) k.append(Object.assign(doc.createElement('span'), { className: 'nav-step', textContent: 'Here' }));
    const name = Object.assign(doc.createElement('strong'), { className: 'nav-place', textContent: p.place });
    const sub = Object.assign(doc.createElement('span'), { className: 'nav-sub', textContent: p.eyebrow !== p.place ? p.eyebrow : `Summer ${d.year}` });
    card.append(k, name, sub);
    list.append(card);
  }
  const recall = doc.createElement('a');
  recall.className = 'nav-key nav-recall';
  recall.href = '../';
  recall.textContent = 'Recall to the Observatory';
  recall.addEventListener('click', () => ctx.actions?.recall?.());
  el.append(list, recall);
}

export function unmount(el) { el.replaceChildren(); }
