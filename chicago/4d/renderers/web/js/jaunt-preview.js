/** Lazy catalog, route preview and session handoff. */
import { addTable, tellingTable } from './reading-level.js';
import { understandingQuestions, createUnderstandingDraft } from './jaunt-understanding.js';
import { renderUnderstandingCheck } from './jaunt-understanding-view.js';
import { jauntInvestigation, createInvestigationDraft } from './jaunt-investigation.js';
import { renderInvestigation } from './jaunt-investigation-view.js';
import { createJauntMenu } from './jaunt-menu.js';
import { createJournal, presentKeepsake } from './jaunt-journal.js';
import { icon } from './menu-icons.js';
import { t } from './strings/index.js';
import './strings/license.js';
import { loadReaderText, readerCopy } from './reader-text.js';
import { localCatalog, localJaunt } from './jaunt-language.js';
import { currentStop, routeCount } from './jaunts.js';

export function createJauntPreview({ root, scene = '1835', dataBase, destinations, api, fetcher = fetch, onStart, onResume, onDismiss = () => {}, getSession = () => null, estimate = () => null, storage, plateFor = () => null, preferredMode = () => null, modeNote = () => '', license = null, narration = null, allowAdults = () => false }) {
  const base = new URL(`sidecars/${encodeURIComponent(scene)}/jaunts/`, dataBase);
  let catalogPromise, daybookPromise, journal = null, serial = 0, outcomeSeen = null;
  const contents = new Map();
  let checkSession = null, checkDraft = null, investigationDraft = null;
  const doc = root.ownerDocument ?? globalThis.document;
  if (doc?.head && !doc.getElementById('jaunt-understanding-style')) {
    const checkStyle = doc.createElement('link'); checkStyle.id = 'jaunt-understanding-style';
    checkStyle.rel = 'stylesheet';
    checkStyle.href = new URL('../css/jaunt-understanding.css', import.meta.url);
    doc.head.append(checkStyle);
  }
  if (doc?.head && !doc.getElementById('jaunt-investigation-style')) {
    const style = doc.createElement('link'); style.id = 'jaunt-investigation-style';
    style.rel = 'stylesheet'; style.href = new URL('../css/jaunt-investigation.css', import.meta.url);
    doc.head.append(style);
  }
  const menu = createJauntMenu({ root, estimate, onStart, onPreview: select, plateFor,
    kept: row => !!journal?.keepsakes.some(e => e.jaunt === row.id), preferredMode, modeNote });
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
  // The owner, 2026-11-15: an adults jaunt (audience adults, the 1812 fighting shown) is listed,
  // previewed and started only for a visitor who has turned on Move › 18+ jaunts.
  const allowed = (row) => row?.audience !== 'adults' || allowAdults() === true;
  const shown = (rows) => (Array.isArray(rows) ? rows.filter(allowed) : rows);
  async function json(name, options) {
    const response = await fetcher(new URL(name, base), options);
    if (name === 'catalog.json' && response.status === 404) return { scene: String(scene), jaunts: [] };
    if (!response.ok) throw new Error(`Jaunt request failed: ${response.status}`);
    return response.json();
  }
  function catalog() {
    if (!catalogPromise) catalogPromise = json('catalog.json').then(async data => {
      if (data.scene !== String(scene) || !Array.isArray(data.jaunts)) throw new Error('Invalid catalog');
      // Gap analysis item 15: titles and premises in the visitor's language (js/jaunt-language.js).
      const rows = await localCatalog(data.jaunts, base, fetcher);
      api.catalog = rows; return rows;
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
  // T-2665: the Navigator License, finishing the Field Check's keepsake (js/license.js), on the
  // shelf with the Jaunt keepsakes in every year's daybook. It is not a jaunt's, so it has no
  // family, moves no count or rank, and Reset daybook leaves it.
  function licenseCard() {
    const k = license?.card?.();
    if (!k) return null;
    const card = node('article', '', 'jaunt-keepsake jaunt-keepsake-license');
    card.dataset.keepsake = 'navigator-license';
    card.append(node('p', k.form, 'jaunt-keepsake-form'), node('h4', k.title), node('p', k.text), node('p', k.line, 'jaunt-keepsake-family'));
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
    const items = journal.keepsakes, held = licenseCard();
    if (!items.length) view.append(node('p', held ? t('license.no-jaunt-keepsakes') : 'No keepsakes yet. Finish a jaunt and its memento is kept here.'));
    if (items.length || held) {
      const shelf = node('div', '', 'jaunt-keepsakes');
      shelf.append(...items.reverse().map(keepsakeCard), ...(held ? [held] : []));
      view.append(shelf);
    }
    if (items.length) {
      const reset = button('Reset daybook', () => {
        if (reset.dataset.confirm) { journal.reset(); showDaybook(returnId); return; }
        reset.dataset.confirm = 'true'; reset.textContent = held ? t('license.reset-confirm') : 'Tap again to clear every keepsake';
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
      const entry = button(`${journal.level().title} · ${journal.keepsakes.length + (license?.held ? 1 : 0)} kept`, () => showDaybook(returnId));
      entry.title = 'Daybook'; entry.setAttribute('aria-label', `Daybook · ${entry.textContent}`);
      entry.dataset.action = 'daybook'; entry.classList.add('jaunt-daybook-chip'); entry.prepend(icon('News & Knowledge', 15)); prefix.push(entry);
    }
    const session = getSession();
    if (session?.phase !== 'outcome' || checkSession !== session.session) {
      checkSession = session?.phase === 'outcome' ? session.session : null;
      checkDraft = checkSession ? createUnderstandingDraft() : null;
      investigationDraft = checkSession ? createInvestigationDraft() : null;
    }
    if (session?.notice) prefix.push(node('p', session.notice, 'jaunt-session-note'));
    if (session?.jaunt && ['menu', 'outcome'].includes(session.phase)) {
      const note = node('section', '', 'jaunt-session-note');
      if (session.phase === 'outcome') {
        // T-3432 (owner, 2026-11-06: "outing complete that screen takes up the whole view and
        // you can't see the list of jaunts so make that "finish" screen outing complete much more
        // concise and expandable"): one compact card above the list — done, which jaunt, the
        // keepsake kept — with the ending, the keepsake and the counters behind one toggle.
        const fallback = session.outcome.fallback;
        note.classList.add('jaunt-outcome'); note.dataset.outcome = session.jaunt.id;
        const head = node('div', '', 'jaunt-outcome-head'), mark = node('span', '', 'jaunt-outcome-mark');
        mark.append(icon(fallback ? 'finish' : 'done', 22));
        const words = node('div', '', 'jaunt-outcome-words');
        words.append(node('h3', fallback ? 'Outing interrupted' : 'Outing complete'), node('p', session.jaunt.title, 'jaunt-outcome-title'));
        if (!fallback && session.jaunt.keepsake?.title) {
          const kept = node('p', '', 'jaunt-outcome-kept'); kept.append(icon('kept', 14), node('span', session.jaunt.keepsake.title)); words.append(kept);
        }
        head.append(mark, words);
        const clear = button('', () => { onDismiss(); list(api.catalog, session.jaunt.id); });
        clear.classList.add('jaunt-outcome-close'); clear.append(icon('close', 16)); clear.setAttribute('aria-label', 'Close the finished outing');
        clear.title = 'Close'; clear.dataset.action = 'outcome-close'; head.append(clear);
        const more = node('details', '', 'jaunt-outcome-more');
        const summary = node('summary', ''); summary.append(node('span', fallback ? 'What happened' : 'The ending and keepsake'), icon('more', 16));
        // T-3355: a long ending is told in paragraphs, split at blank lines.
        more.append(summary);
        // T-3578: a voiced ending can be heard again (it starts by itself as the outing finishes).
        if (narration?.clip(session.jaunt, 'ending', session.outcome.id)) {
          const hear = button('', () => { void narration.toggle(session.jaunt, 'ending', session.outcome.id); });
          hear.className = 'jaunt-listen'; hear.dataset.action = 'listen';
          const paint = () => {
            const on = narration.isPlaying(session.jaunt, 'ending', session.outcome.id);
            hear.setAttribute('aria-pressed', String(on)); hear.replaceChildren(icon(on ? 'stop' : 'listen', 15), node('span', on ? 'Stop' : 'Listen'));
            hear.title = on ? 'Stop the narration' : 'Listen: read aloud in a synthetic voice';
            // T-3671 (WCAG 1.2.1): an ending read aloud here is on screen while it is read.
            if (on) more.open = true;
          };
          paint();
          const off = narration.on(() => { if (!hear.isConnected) off(); else paint(); });
          more.append(hear);
        }
        more.append(...String(session.outcome.text).split(/\n\s*\n/).map(text => node('p', text.trim())));
        const awarded = !fallback && awardNote(session);
        if (awarded) more.append(awarded);
        else if (!fallback) more.append(node('h4', session.jaunt.keepsake.title), node('p', session.jaunt.keepsake.text));
        note.append(head, more);
        const check = checkDraft && renderUnderstandingCheck(doc, understandingQuestions(session, { placeOf: stop => destinations?.byId?.(stop.destination?.kind, stop.destination?.id)?.label }), checkDraft);
        if (check) note.append(check);
        const investigation = renderInvestigation(doc, jauntInvestigation(session), investigationDraft);
        if (investigation) note.append(investigation);
        const row = node('div', '', 'jaunt-outcome-actions');
        if (journal) {
          const book = button('Daybook', () => showDaybook(session.jaunt.id)); book.prepend(icon('News & Knowledge', 15));
          book.setAttribute('aria-label', 'Open your daybook'); row.append(book);
        }
        const again = button('Replay', () => { menu.capture(); onStart(session.jaunt.id, { mode: session.mode }); });
        again.prepend(icon('play', 14)); again.setAttribute('aria-label', 'Restart Jaunt'); again.dataset.action = 'restart';
        row.append(again); note.append(row);
      } else {
        // T-2631: the outing in progress, pinned on top — where you are and what comes next.
        // T-3754: the next stop on this route, and this route's count (a branching jaunt's
        // stopIndex counts its route, not its file of stops).
        const stops = session.jaunt.stops ?? [], at = session.stopIndex, here = currentStop(session);
        const nextId = session.visited?.[at + 1]?.id ?? (here?.choices?.length ? null : here?.next);
        const next = stops.find(x => x.id === nextId), deciding = !next && !!here?.choices?.length && nextId === null && !session.visited?.[at]?.committed;
        const label = stop => session.jaunt.places?.[stop.destination.id] || destinations.byId(stop.destination.kind, stop.destination.id)?.label || 'the next stop';
        note.classList.add('jaunt-continue'); note.dataset.continue = session.jaunt.id;
        const go = button('Continue', () => { menu.capture(); onResume(); }); go.dataset.action = 'continue';
        note.append(node('p', `Continue · Stop ${at + 1} of ${routeCount(session) || at + 1}`, 'jaunt-continue-k'), node('h3', session.jaunt.title),
          node('p', next ? `Next: ${label(next)}` : deciding ? 'Next: your choice' : 'Next: the end of the outing', 'jaunt-continue-next'), go);
      }
      if (session.phase === 'menu') note.append(button('Restart Jaunt', () => { menu.capture(); onStart(session.jaunt.id, { mode: session.mode }); }));
      // In progress, it leads the list; an outcome follows the daybook chip as before.
      if (session.phase === 'menu') prefix.unshift(note); else prefix.push(note);
    }
    menu.show(shown(rows), prefix, returnId, focusStart);
    // T-3432: a fresh Outing complete is seen at the top, with the list right under it.
    if (session?.phase === 'outcome' && outcomeSeen !== session.session) {
      outcomeSeen = session.session; const scroller = root.closest('.welcome-region') || root; scroller.scrollTop = 0;
    }
  }

  // T-3645: the jaunt last loaded reads its other tellings' words at the reader's other ages
  // (reading-level.js § tellingTable): its siblings are fetched alongside, once, and their
  // table takes the place of the one before.
  let dropTellings = null, tellingsFor = null, siblings = null;
  async function tellings(content) {
    if (tellingsFor === content.id) return;
    tellingsFor = content.id;
    const rows = await catalog();
    const baseOf = (r) => r?.version_of || r?.id;
    const own = rows.find((r) => r.id === content.id);
    const ids = rows.filter((r) => r.id !== content.id && baseOf(r) === baseOf(own) && r.audience !== 'adults' && r.availability === 'available').map((r) => r.id);
    const others = (await Promise.all(ids.map((sid) => fetchContent(sid).catch(() => null)))).filter(Boolean);
    if (tellingsFor !== content.id) return;
    dropTellings?.();
    dropTellings = addTable(tellingTable(content, others));
    siblings = { id: content.id, list: others };   // T-3735: for the voice an age tab reads in
  }
  async function load(id, options) {
    const content = await fetchContent(id, options);
    void tellings(content).catch((err) => console.warn('[4D Chicago] jaunt tellings for reading ages', err));
    return content;
  }
  async function fetchContent(id, options) {
    const rows = await catalog();
    if (!rows.some(row => row.id === id && row.availability === 'available' && allowed(row)) || !/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(id)) throw new Error('Jaunt unavailable');
    let content = contents.get(id);
    if (!content) {
      content = await json(`${id}.json`, options);
      if (content.scene !== String(scene) || content.id !== id || content.review_required || !content.stops?.length) throw new Error('Invalid jaunt');
      // T-2825: a stop's evidence (its locator, its reasoning, its citations) said for a
      // reader, by the overlay the gate lints; the story itself is already a visitor's text.
      content = readerCopy(content, await loadReaderText(dataBase, `jaunts_${scene}`));
      // Gap analysis item 15: the words in the visitor's language, over the English the reader
      // overlay just cleaned (its keys are the English strings').
      content = await localJaunt(content, base, fetcher);
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
        node('p', 'Route preview', 'jaunt-meta'),
        ...(content.quotesNote ? [node('p', content.quotesNote, 'jaunt-meta')] : []),
        ...String(content.opening.text).split(/\n\s*\n/).map(text => node('p', text.trim())));
      const stops = node('ol', '', 'jaunt-stops');
      for (const stop of content.stops) {
        const item = node('li', '');
        const place = destinations.byId(stop.destination.kind, stop.destination.id);
        // T-2946: the jaunt's own name for the stop, as its panel and road notes give it.
        item.append(node('h4', content.places?.[stop.destination.id] || place?.label || stop.destination.id), node('p', stop.since ? `${stop.since}. ${stop.text}` : stop.text));
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
        const toggle = button('Sources for this stop', () => {
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
  /** T-3735: the other tellings of the jaunt last loaded (compiled), once they have been read. */
  const tellingsOf = (id) => (siblings?.id === id ? siblings.list : []);
  return { open, load, award, daybook, tellingsOf };
}
