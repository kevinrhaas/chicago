/** A lazy, read-only content preview. Story playback belongs to T-1279. */
export function createJauntPreview({ root, dataBase, destinations, api, fetcher = fetch }) {
  const base = new URL('sidecars/1835/jaunts/', dataBase);
  let catalogPromise, serial = 0;
  const contents = new Map();
  const node = (tag, text, className) => {
    const el = document.createElement(tag); el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const button = (text, action) => {
    const el = node('button', text, 'welcome-link'); el.type = 'button';
    el.addEventListener('click', action); return el;
  };
  async function json(name) {
    const response = await fetcher(new URL(name, base));
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
  function list(rows, returnId) {
    root.replaceChildren(node('p', 'A first look at the stories taking shape. Read a route here; guided travel will follow.'));
    for (const row of rows) {
      const card = node('article', '', 'jaunt-card'); card.dataset.jaunt = row.id;
      card.append(node('h3', row.title), node('p', `${row.category} · ${row.stop_count} stops · ${row.primary_family}`, 'jaunt-meta'), node('p', row.premise));
      if (row.availability === 'available') {
        const preview = button('Preview the route', () => select(row));
        card.append(preview); root.append(card);
        if (returnId === row.id) preview.focus({ preventScroll: true });
      } else {
        card.append(node('p', `Unavailable — ${row.reason || 'Awaiting review.'}`, 'jaunt-meta'));
        root.append(card);
      }
    }
    if (!rows.length) root.append(node('p', 'No route previews are available yet.'));
  }
  async function select(row) {
    const request = ++serial;
    root.replaceChildren(node('p', 'Loading the route…'));
    try {
      // Only a catalog identity can reach this URL; never interpret authored code/HTML.
      if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(row.id)) throw new Error('Invalid identity');
      let content = contents.get(row.id);
      if (!content) { content = await json(`${row.id}.json`); contents.set(row.id, content); }
      if (request !== serial) return;
      const title = node('h3', content.title);
      root.replaceChildren(button('Back to Jaunts', () => { ++serial; list(api.catalog, row.id); }), title,
        node('p', 'Route preview · not yet a guided jaunt', 'jaunt-meta'), node('p', content.opening.text));
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
  async function open() {
    const request = ++serial;
    root.replaceChildren(node('p', 'Loading jaunts…'));
    try { const rows = await catalog(); if (request === serial) list(rows); }
    catch { if (request === serial) root.replaceChildren(node('p', 'Jaunts could not load. You can still explore on your own.'), button('Try again', open)); }
  }
  return { open };
}
