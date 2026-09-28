/** Lazy catalog, route preview and session handoff. */
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';
export function createJauntPreview({ root, dataBase, destinations, api, fetcher = fetch, onStart, onResume, getSession = () => null, estimate = () => null }) {
  const base = new URL('sidecars/1835/jaunts/', dataBase);
  let catalogPromise, serial = 0;
  const contents = new Map();
  const modes = new Map();
  const node = (tag, text, className) => {
    const el = document.createElement(tag); el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const button = (text, action) => {
    const el = node('button', text, 'welcome-link'); el.type = 'button';
    el.addEventListener('click', action); return el;
  };
  async function json(name, options) {
    const response = await fetcher(new URL(name, base), options);
    if (!response.ok) throw new Error(`Jaunt request failed: ${response.status}`);
    return response.json();
  }
  function catalog() {
    if (!catalogPromise) catalogPromise = json('catalog.json').then(data => {
      if (!Array.isArray(data.jaunts)) throw new Error('Invalid catalog');
      api.catalog = data.jaunts; return data.jaunts;
    }).catch(error => { catalogPromise = null; throw error; });
    return catalogPromise;
  }
  function focus(el) {
    if (!root.closest('[hidden]')) { el.tabIndex = -1; el.focus({ preventScroll: true }); }
  }
  function list(rows, returnId, focusStart = false) {
    root.replaceChildren(node('p', 'Choose an outing, or read its route before you start.'));
    const session = getSession();
    if (session?.jaunt && ['menu', 'outcome'].includes(session.phase)) {
      const note = node('section', '', 'jaunt-session-note');
      if (session.phase === 'outcome') {
        note.append(node('h3', 'Outing complete'), node('p', session.outcome.text),
          node('h4', session.jaunt.keepsake.title), node('p', session.jaunt.keepsake.text));
      } else note.append(node('h3', `Paused · ${session.jaunt.title}`), node('p', `Stop ${session.stopIndex + 1}`), button('Resume Jaunt', onResume));
      note.append(button('Restart Jaunt', () => onStart(session.jaunt.id, { mode: session.mode }))); root.append(note);
    }
    for (const row of rows) {
      const card = node('article', '', 'jaunt-card'); card.dataset.jaunt = row.id;
      card.append(node('h3', row.title), node('p', `${row.category} · ${row.stop_count} stops · ${row.primary_family}`, 'jaunt-meta'), node('p', row.premise));
      if (row.availability === 'available') {
        const mode = node('select'); mode.setAttribute('aria-label', `Travel mode for ${row.title}`);
        for (const id of row.allowed_modes || ['walk', 'wagon', 'horse', 'fly', 'instantly']) {
          const option = node('option', PACES[id]?.label || id); option.value = id; mode.append(option);
        }
        mode.value = modes.get(row.id) || row.default_mode || 'walk';
        const duration = node('p', '', 'jaunt-meta'); duration.dataset.jauntEstimate = row.id;
        const price = () => { modes.set(row.id, mode.value); duration.textContent = formatEstimate(estimate(row, mode.value)); };
        mode.addEventListener('change', price); price();
        card.append(mode, duration, node('p', `Recommended: ${PACES[row.default_mode || 'walk'].label}. Fly is a viewing convenience, not 1835 transport.`, 'jaunt-meta'));
        const preview = button('Preview the route', () => select(row));
        const start = onStart && button('Start Jaunt', async () => {
          start.disabled = true;
          try { await onStart(row.id, { mode: mode.value }); } finally { if (start.isConnected) start.disabled = false; }
        });
        if (start) card.append(start);
        card.append(preview); root.append(card);
        if (returnId === row.id) (focusStart && start ? start : preview).focus({ preventScroll: true });
      } else {
        card.append(node('p', `Unavailable — ${row.reason || 'Awaiting review.'}`, 'jaunt-meta'));
        root.append(card);
      }
    }
    if (!rows.length) root.append(node('p', 'No route previews are available yet.'));
  }
  async function load(id, options) {
    const rows = await catalog();
    if (!rows.some(row => row.id === id && row.availability === 'available') || !/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(id)) throw new Error('Jaunt unavailable');
    let content = contents.get(id);
    if (!content) {
      content = await json(`${id}.json`, options);
      if (content.id !== id || content.review_required || !content.stops?.length) throw new Error('Invalid jaunt');
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
      root.replaceChildren(button('Back to Jaunts', () => { ++serial; list(api.catalog, row.id); }), title,
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
        button('Try the route again', () => select(row)), button('Back to Jaunts', () => list(api.catalog, row.id)));
    }
  }
  async function open(returnId) {
    const request = ++serial;
    root.replaceChildren(node('p', 'Loading jaunts…'));
    try { const rows = await catalog(); if (request === serial) list(rows, returnId, true); }
    catch { if (request === serial) root.replaceChildren(node('p', 'Jaunts could not load. You can still explore on your own.'), button('Try again', open)); }
  }
  return { open, load };
}
