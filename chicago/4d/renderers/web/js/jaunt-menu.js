/** Lazy catalog browser. A bounded, keyboard-accessible window holds at most 20 outings. */
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';

export const WINDOW_SIZE = 20;
export function filterJaunts(rows, query = '', category = '') {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return rows.filter(row => (!category || row.category === category) && words.every(word =>
    `${row.title} ${row.premise} ${row.category}`.toLocaleLowerCase().includes(word)))
    .sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id));
}

export function createJauntMenu({ root, estimate, onStart, onPreview }) {
  const scroll = root.closest('.welcome-region') || root;
  const modes = new Map(), estimates = new Map();
  let query = '', category = '', offset = 0, savedScroll = 0, focusKey = null;
  let rows = [], list, featured, search, pills, previous, more;
  const node = (tag, text = '', cls = '') => {
    const el = document.createElement(tag); el.textContent = text; el.className = cls; return el;
  };
  const button = (text, action) => {
    const el = node('button', text, 'welcome-link'); el.type = 'button'; el.addEventListener('click', action); return el;
  };
  function remember(id, action, section) {
    savedScroll = scroll.scrollTop; focusKey = { id, action, section };
  }
  function card(row, section) {
    const el = node('article', '', 'jaunt-card'); el.dataset.jaunt = row.id; el.dataset.section = section;
    el.append(node('h3', row.title), node('p', row.premise),
      node('p', `${row.category} · ${row.stop_count} stops · ${row.primary_family}`, 'jaunt-meta'));
    const mode = node('select'); mode.setAttribute('aria-label', `Travel mode for ${row.title}`);
    for (const id of row.allowed_modes || ['walk']) {
      const option = node('option', PACES[id]?.label || id); option.value = id; mode.append(option);
    }
    mode.value = modes.get(row.id) || row.default_mode || 'walk'; mode.dataset.action = 'mode';
    const duration = node('p', '', 'jaunt-meta'); duration.dataset.jauntEstimate = row.id;
    duration.setAttribute('aria-live', 'polite');
    const price = () => {
      modes.set(row.id, mode.value);
      const key = JSON.stringify([mode.value, row.destinations, row.timing, row.stops]);
      if (!estimates.has(key)) estimates.set(key, formatEstimate(estimate(row, mode.value)));
      duration.textContent = `${estimates.get(key)} at ${PACES[mode.value]?.label || mode.value}`;
    };
    mode.addEventListener('change', () => {
      price();
      // A featured card and its All jaunts copy always agree.
      for (const other of root.querySelectorAll('[data-jaunt]')) if (other !== el && other.dataset.jaunt === row.id) {
        other.querySelector('select').value = mode.value;
        other.querySelector('[data-jaunt-estimate]').textContent = duration.textContent;
      }
    });
    price(); el.append(mode, duration);
    if (row.availability !== 'available') {
      mode.disabled = true;
      el.append(node('p', `Unavailable — ${row.reason || 'Awaiting review.'}`, 'jaunt-meta')); return el;
    }
    el.append(node('p', `Recommended: ${PACES[row.default_mode || 'walk']?.label || row.default_mode}. Fly is a viewing convenience, not historical transport.`, 'jaunt-meta'));
    if (onStart) {
      const start = button('Start Jaunt', async () => {
        remember(row.id, 'start', section); start.disabled = true;
        try { await onStart(row.id, { mode: mode.value }); }
        finally { if (start.isConnected) start.disabled = false; }
      });
      start.dataset.action = 'start'; el.append(start);
    }
    const preview = button('Preview the route', () => { remember(row.id, 'preview', section); onPreview(row); });
    preview.dataset.action = 'preview'; el.append(preview);
    return el;
  }
  function windowRows({ focus = false } = {}) {
    const matches = filterJaunts(rows, query, category);
    offset = Math.min(offset, Math.max(0, Math.floor((matches.length - 1) / WINDOW_SIZE) * WINDOW_SIZE));
    list.replaceChildren(...matches.slice(offset, offset + WINDOW_SIZE).map(row => card(row, 'all')));
    if (!matches.length) list.append(node('p', rows.length ? 'No matching outings. Clear the search or choose another category.' : 'No jaunts are available yet. You can explore on your own.'));
    previous.hidden = offset === 0; more.hidden = offset + WINDOW_SIZE >= matches.length;
    featured.hidden = !!query.trim() || !!category || !featured.querySelector('article');
    for (const pill of pills.children) pill.setAttribute('aria-pressed', String(pill.dataset.category === category));
    if (focus) {
      const target = list.querySelector('button, select:not(:disabled), h3') || list;
      if (!target.matches('button, select')) target.tabIndex = -1;
      target.focus({ preventScroll: true }); list.scrollIntoView({ block: 'start' });
    }
  }
  function show(catalog, prefix = [], returnId = null, focusStart = false) {
    rows = catalog; estimates.clear();
    search = node('input'); search.type = 'search'; search.id = 'jaunt-menu-search';
    search.placeholder = 'Search outings'; search.autocomplete = 'off'; search.value = query;
    const label = node('label', 'Find an outing'); label.htmlFor = search.id;
    pills = node('div', '', 'jaunt-categories'); pills.setAttribute('role', 'group'); pills.setAttribute('aria-label', 'Jaunt categories');
    for (const name of ['', ...new Set(rows.map(row => row.category).sort())]) {
      const pill = button(name || 'All categories', () => { category = name; offset = 0; windowRows(); });
      pill.dataset.category = name; pills.append(pill);
    }
    search.addEventListener('input', () => { query = search.value; offset = 0; windowRows(); });
    const clear = button('Clear filters', () => { query = category = ''; offset = 0; search.value = ''; windowRows(); search.focus(); });
    const filters = node('div', '', 'jaunt-filters'); filters.append(label, search, pills, clear);
    featured = node('section', '', 'jaunt-featured'); featured.setAttribute('aria-label', 'Featured jaunts');
    featured.append(node('h3', 'Featured'));
    // Six priority outings; the full catalog remains available in the bounded list below.
    featured.append(...filterJaunts(rows).filter(row => row.featured).slice(0, 6).map(row => card(row, 'featured')));
    list = node('div', '', 'jaunt-list'); list.setAttribute('aria-label', 'All jaunts');
    previous = button('Earlier outings', () => { offset -= WINDOW_SIZE; windowRows({ focus: true }); });
    more = button('More outings', () => { offset += WINDOW_SIZE; windowRows({ focus: true }); });
    const nav = node('nav', '', 'jaunt-window-nav'); nav.setAttribute('aria-label', 'Browse outings'); nav.append(previous, more);
    root.replaceChildren(...prefix, filters, featured, node('h3', 'All jaunts'), list, nav);
    windowRows();
    if (returnId) {
      const key = focusKey?.id === returnId ? { ...focusKey } : { id: returnId, section: 'all', action: 'start' };
      if (focusStart) key.action = 'start';
      const match = [...root.querySelectorAll('[data-jaunt]')].find(el => el.dataset.jaunt === key.id && el.dataset.section === key.section);
      const target = match?.querySelector(`[data-action="${key.action}"]`) || search;
      target.focus({ preventScroll: true });
    }
    scroll.scrollTop = savedScroll;
  }
  return { show, capture: () => { savedScroll = scroll.scrollTop; } };
}
