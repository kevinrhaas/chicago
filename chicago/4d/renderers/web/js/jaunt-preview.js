/** Lazy catalog, route preview and session handoff. */
import { createJauntMenu } from './jaunt-menu.js';
import { createJournal, presentKeepsake } from './jaunt-journal.js';
import { icon } from './menu-icons.js';
export function createJauntPreview({ root, scene = '1835', dataBase, destinations, api, fetcher = fetch, onStart, onResume, getSession = () => null, estimate = () => null, storage }) {
  const base = new URL(`sidecars/${encodeURIComponent(scene)}/jaunts/`, dataBase);
  let catalogPromise, daybookPromise, journal = null, serial = 0;
  const contents = new Map();
  const menu = createJauntMenu({ root, estimate, onStart, onPreview: select });
  const node = (tag, text, className) => {
    const el = document.createElement(tag); el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const button = (text, action) => {
    const el = node('button', text, 'welcome-link'); el.type = 'button';
    el.addEventListener('click', action); return el;
  };
  // T-2120: every sub-view of Jaunts leads with the same way back.
  const backButton = action => {
    const el = button('Back to Jaunts', action); el.classList.add('jaunt-back'); el.prepend(icon('back', 16)); return el;
  };
  async function json(name, options) {
    const response = await fetcher(new URL(name, base), options);
    if (name === 'catalog.json' && response.status === 404) return { scene: String(scene), jaunts: [] };
    if (!response.ok) throw new Error(`Jaunt request failed: ${response.status}`);
    return response.json();
  }
  function catalog() {
    if (!catalogPromise) catalogPromise = json('catalog.json').then(data => {
      if (data.scene !== String(scene) || !Array.isArray(data.jaunts)) throw new Error('Invalid catalog');
      api.catalog = data.jaunts; return data.jaunts;
    }).catch(error => { catalogPromise = null; throw error; });
    return catalogPromise;
  }
  // T-1258: the daybook loads with the menu, never at boot; a missing book costs only the daybook.
  function daybook() {
    daybookPromise ??= json('daybook.json').then(book => (journal = createJournal({ book, scene: String(scene), storage })))
      .catch(error => { daybookPromise = null; throw error; });
    return daybookPromise;
  }
  function award(session) {
    return daybook().then(j => j.award(session.jaunt, session.outcome)).catch(() => null);
  }
  function keepsakeCard(entry) {
    const k = presentKeepsake(journal.book, entry), card = node('article', '', `jaunt-keepsake jaunt-keepsake-${k.style}`);
    card.dataset.keepsake = entry.key;
    card.append(node('p', `${k.form} · ${k.lead}`, 'jaunt-keepsake-form'), node('h4', k.title), node('p', k.text),
      node('p', k.secondary ? `${k.family} · ${k.secondary}` : k.family, 'jaunt-keepsake-family'));
    return card;
  }
  function counters(counts, moved = new Set()) {
    const row = node('ul', '', 'jaunt-daybook-families'); row.setAttribute('aria-label', 'Keepsakes by family');
    for (const family of journal.book.families) {
      const item = node('li', '', moved.has(family.id) ? 'jaunt-daybook-moved' : '');
      item.dataset.family = family.id; item.title = family.description;
      item.append(node('strong', String(counts[family.id])), node('span', family.name)); row.append(item);
    }
    return row;
  }
  function rankLine() {
    const rank = journal.level(), next = journal.nextRank();
    const line = node('p', `Rank: ${rank.title}`, 'jaunt-daybook-rank'); line.dataset.level = rank.id;
    if (next) line.append(node('small', ` · ${next.title} at ${next.threshold} in every family`));
    return line;
  }
  function showDaybook(returnId) {
    menu.capture();
    ++serial;
    const title = node('h3', journal.book.title), back = backButton(() => list(api.catalog, returnId));
    const view = node('section', '', 'jaunt-daybook'); view.setAttribute('aria-label', 'Daybook');
    view.append(title, node('p', journal.book.disclaimer, 'jaunt-meta'));
    if (journal.notice) view.append(node('p', journal.notice, 'jaunt-session-note'));
    view.append(rankLine(), counters(journal.counts()));
    const items = journal.keepsakes;
    if (!items.length) view.append(node('p', 'No keepsakes yet. Finish a jaunt and its memento is kept here.'));
    else { const shelf = node('div', '', 'jaunt-keepsakes'); shelf.append(...items.reverse().map(keepsakeCard)); view.append(shelf); }
    if (items.length) {
      const reset = button('Reset daybook', () => {
        if (reset.dataset.confirm) { journal.reset(); showDaybook(returnId); return; }
        reset.dataset.confirm = 'true'; reset.textContent = 'Tap again to clear every keepsake';
      });
      reset.dataset.action = 'daybook-reset'; view.append(reset);
    }
    root.replaceChildren(back, view); focus(title); back.scrollIntoView?.({ block: 'nearest' });
  }
  function awardNote(session) {
    const result = journal?.lastAward;
    if (!result || result.jaunt !== session.jaunt.id || !result.entry) return null;
    const box = node('div', '', 'jaunt-award'); box.setAttribute('aria-live', 'polite');
    box.append(node('p', result.added ? 'Kept in your daybook' : 'Already in your daybook — replays keep one copy', 'jaunt-meta'), keepsakeCard(result.entry));
    const moved = new Set(Object.keys(result.after.counts).filter(id => result.after.counts[id] !== result.before.counts[id]));
    box.append(counters(result.after.counts, moved));
    if (result.rankChanged) box.append(node('p', `New rank: ${result.after.level.title}`, 'jaunt-daybook-rank'));
    return box;
  }
  function focus(el) {
    if (!root.closest('[hidden]')) { el.tabIndex = -1; el.focus({ preventScroll: true }); }
  }
  function list(rows, returnId, focusStart = false) {
    const prefix = [];
    if (journal) {
      const entry = button(`${journal.level().title} · ${journal.keepsakes.length} kept`, () => showDaybook(returnId));
      entry.title = 'Daybook'; entry.setAttribute('aria-label', `Daybook · ${entry.textContent}`);
      entry.dataset.action = 'daybook'; entry.classList.add('jaunt-daybook-chip'); entry.prepend(icon('News & Knowledge', 15)); prefix.push(entry);
    }
    const session = getSession();
    if (session?.notice) prefix.push(node('p', session.notice, 'jaunt-session-note'));
    if (session?.jaunt && ['menu', 'outcome'].includes(session.phase)) {
      const note = node('section', '', 'jaunt-session-note');
      if (session.phase === 'outcome') {
        note.append(node('h3', session.outcome.fallback ? 'Outing interrupted' : 'Outing complete'), node('p', session.outcome.text));
        const awarded = !session.outcome.fallback && awardNote(session);
        if (awarded) note.append(awarded);
        else if (!session.outcome.fallback) note.append(node('h4', session.jaunt.keepsake.title), node('p', session.jaunt.keepsake.text));
        if (journal) note.append(button('Open your daybook', () => showDaybook(session.jaunt.id)));
      } else note.append(node('h3', `Resume ${session.jaunt.title}`), node('p', `Stop ${session.stopIndex + 1}`), button('Resume Jaunt', () => { menu.capture(); onResume(); }));
      note.append(button('Restart Jaunt', () => { menu.capture(); onStart(session.jaunt.id, { mode: session.mode }); })); prefix.push(note);
    }
    menu.show(rows, prefix, returnId, focusStart);
  }

  async function load(id, options) {
    const rows = await catalog();
    if (!rows.some(row => row.id === id && row.availability === 'available') || !/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(id)) throw new Error('Jaunt unavailable');
    let content = contents.get(id);
    if (!content) {
      content = await json(`${id}.json`, options);
      if (content.scene !== String(scene) || content.id !== id || content.review_required || !content.stops?.length) throw new Error('Invalid jaunt');
      contents.set(id, content);
    }
    return content;
  }
  async function select(row) {
    const request = ++serial;
    root.replaceChildren(node('p', 'Loading the route…'));
    try {
      // Only a catalog identity can reach this URL; never interpret authored code/HTML.
      const content = await load(row.id);
      if (request !== serial) return;
      const title = node('h3', content.title);
      root.replaceChildren(backButton(() => { ++serial; list(api.catalog, row.id); }), title,
        node('p', 'Route preview', 'jaunt-meta'), node('p', content.opening.text));
      const stops = node('ol', '', 'jaunt-stops');
      for (const stop of content.stops) {
        const item = node('li', '');
        const place = destinations.byId(stop.destination.kind, stop.destination.id);
        item.append(node('h4', place?.label || stop.destination.id), node('p', stop.text));
        if (stop.choices?.length) item.append(node('p', `Optional preference: ${stop.choices.map(c => c.label).join(' / ')}. You may also skip it.`, 'jaunt-meta'));
        const evidence = node('div', '', 'jaunt-evidence'); evidence.hidden = true;
        for (const id of stop.evidence) {
          const claim = content.evidence.find(c => c.id === id);
          if (!claim) continue;
          evidence.append(node('p', `${{ attested: '[DOC]', inferred: '[INF]', reconstructed: '[CONJ]' }[claim.confidence]} ${claim.text}`));
          const sources = claim.sources.map(id => content.citations?.find(c => c.source_id === id)?.citation || 'Source reference unavailable');
          const locators = [claim.locator, claim.reasoning, claim.liberty ? 'Declared narrative reconstruction.' : null, ...sources].filter(Boolean);
          evidence.append(node('p', locators.join(' · '), 'jaunt-meta'));
        }
        const toggle = button('Evidence for this stop', () => {
          evidence.hidden = !evidence.hidden; toggle.setAttribute('aria-expanded', String(!evidence.hidden));
        });
        toggle.setAttribute('aria-expanded', 'false'); item.append(toggle, evidence); stops.append(item);
      }
      root.append(stops, node('h4', `Keepsake · ${content.keepsake.title}`), node('p', `${content.keepsake.family} — ${content.keepsake.text}`), node('p', 'This preview does not award a keepsake or start travel.', 'jaunt-meta'));
      focus(title);
    } catch {
      contents.delete(row.id);
      if (request !== serial) return;
      root.replaceChildren(node('p', 'This route could not load. Your place in the welcome is safe.'),
        button('Try the route again', () => select(row)), backButton(() => list(api.catalog, row.id)));
    }
  }
  async function open(returnId) {
    const request = ++serial;
    root.replaceChildren(node('p', 'Loading jaunts…'));
    try { const [rows] = await Promise.all([catalog(), daybook().catch(() => null)]); if (request === serial) list(rows, returnId, true); }
    catch { if (request === serial) root.replaceChildren(node('p', 'Jaunts could not load. You can still explore on your own.'), button('Try again', open)); }
  }
  return { open, load, award, daybook };
}
