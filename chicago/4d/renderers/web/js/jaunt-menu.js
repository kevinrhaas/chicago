/** Lazy catalog browser. A bounded, keyboard-accessible window holds at most 30 outings.
 *  T-2120: one compact row per outing — a type icon and colour, a one-line premise, its
 *  length — with Start on the row and the rest (travel mode, route preview) folded under it. */
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';
import { FAMILIES, familySlot, icon } from './menu-icons.js';

export const WINDOW_SIZE = 30;
const SHORT = { 'News & Knowledge': 'News' };
export function filterJaunts(rows, query = '', family = '') {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return rows.filter(row => (!family || row.primary_family === family) && words.every(word =>
    `${row.title} ${row.premise} ${row.category} ${row.primary_family}`.toLocaleLowerCase().includes(word)))
    .sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id));
}

export function createJauntMenu({ root, estimate, onStart, onPreview }) {
  const scroll = root.closest('.welcome-region') || root;
  const modes = new Map(), estimates = new Map(), open = new Set();
  let query = '', family = '', offset = 0, savedScroll = 0, focusKey = null;
  let rows = [], list, search, pills, clear, previous, more;
  const node = (tag, text = '', cls = '') => {
    const el = document.createElement(tag); el.textContent = text; el.className = cls; return el;
  };
  const button = (text, action, cls = 'welcome-link') => {
    const el = node('button', text, cls); el.type = 'button'; el.addEventListener('click', action); return el;
  };
  function remember(id, action, section) {
    savedScroll = scroll.scrollTop; focusKey = { id, action, section };
  }
  function card(row, section) {
    const slot = familySlot(row.primary_family), available = row.availability === 'available';
    const el = node('article', '', `jaunt-card jaunt-type-${slot}`); el.dataset.jaunt = row.id; el.dataset.section = section;
    const badge = node('span', '', 'jaunt-type'); badge.append(icon(FAMILIES.includes(row.primary_family) ? row.primary_family : 'view', 20));
    badge.title = row.primary_family;
    const body = node('div', '', 'jaunt-row-body'), head = node('div', '', 'jaunt-head');
    const title = node('h3', row.title);
    if (row.featured) title.append(node('span', '★', 'jaunt-star'));
    head.append(title);
    const length = node('span', '', 'jaunt-length'); length.dataset.jauntLength = row.id;
    const meta = node('p', '', 'jaunt-tags');
    meta.append(node('span', SHORT[row.primary_family] || row.primary_family, 'jaunt-family'), node('span', `${row.stop_count} stops`), length);
    body.append(head, node('p', row.premise, 'jaunt-premise'), meta);
    const actions = node('div', '', 'jaunt-actions');
    const details = node('div', '', 'jaunt-details'); details.id = `jaunt-more-${section}-${row.id}`;
    const toggle = button('', () => {
      const shown = el.classList.toggle('open');
      if (shown) open.add(row.id); else open.delete(row.id);
      toggle.setAttribute('aria-expanded', String(shown));
    }, 'jaunt-more');
    toggle.append(icon('more', 18)); toggle.dataset.action = 'more';
    toggle.setAttribute('aria-label', `More about ${row.title}`); toggle.setAttribute('aria-controls', details.id);
    toggle.setAttribute('aria-expanded', 'false');
    // Travel mode: a row of small icon toggles instead of a full-width select.
    const mode = node('div', '', 'jaunt-modes'); mode.setAttribute('role', 'radiogroup');
    mode.setAttribute('aria-label', `Travel mode for ${row.title}`); mode.dataset.action = 'mode';
    const duration = node('p', '', 'jaunt-meta'); duration.dataset.jauntEstimate = row.id;
    duration.setAttribute('aria-live', 'polite');
    let current = modes.get(row.id) || row.default_mode || 'walk';
    const price = () => {
      modes.set(row.id, current);
      const key = JSON.stringify([current, row.destinations, row.timing, row.stops]);
      if (!estimates.has(key)) { const e = estimate(row, current); estimates.set(key, { text: formatEstimate(e), s: e?.seconds }); }
      const { text, s } = estimates.get(key);
      duration.textContent = `${text} at ${PACES[current]?.label || current}`;
      length.textContent = Number.isFinite(s) ? `${Math.max(1, Math.round(s / 60))} min` : '';
      length.dataset.size = !Number.isFinite(s) ? '' : s < 600 ? 's' : s < 1200 ? 'm' : 'l';
      for (const b of mode.children) b.setAttribute('aria-checked', String(b.dataset.mode === current));
    };
    for (const id of row.allowed_modes || ['walk']) {
      const b = button('', () => { if (b.disabled) return; current = id; price(); }, 'jaunt-mode-pick');
      b.dataset.mode = id; b.setAttribute('role', 'radio'); b.append(icon(id, 18));
      b.setAttribute('aria-label', PACES[id]?.label || id); b.title = PACES[id]?.label || id;
      mode.append(b);
    }
    price();
    details.append(node('p', row.premise, 'jaunt-premise-full'), node('p', `${row.category} · ${row.primary_family}`, 'jaunt-meta'));
    if (!available) {
      for (const b of mode.children) b.disabled = true;
      meta.append(node('span', 'Held', 'jaunt-held'));
      details.append(node('p', `Unavailable — ${row.reason || 'Awaiting review.'}`, 'jaunt-meta'));
    } else {
      const pace = node('div', '', 'jaunt-pace'); pace.append(mode, duration);
      details.append(pace, node('p', `Recommended: ${PACES[row.default_mode || 'walk']?.label || row.default_mode}. Fly is a viewing convenience, not historical transport.`, 'jaunt-meta'));
      if (onStart) {
        const start = button('', async () => {
          remember(row.id, 'start', section); start.disabled = true;
          try { await onStart(row.id, { mode: current }); }
          finally { if (start.isConnected) start.disabled = false; }
        }, 'jaunt-start');
        start.append(icon('play', 16)); start.setAttribute('aria-label', 'Start Jaunt');
        start.title = `Start ${row.title}`; start.dataset.action = 'start'; actions.append(start);
      }
    }
    if (available) {
      const preview = button('Preview the route', () => { remember(row.id, 'preview', section); onPreview(row); });
      preview.dataset.action = 'preview'; details.append(preview);
    }
    actions.append(toggle);
    el.append(badge, body, actions, details);
    if (open.has(row.id)) { el.classList.add('open'); toggle.setAttribute('aria-expanded', 'true'); }
    return el;
  }
  function windowRows({ focus = false } = {}) {
    const matches = filterJaunts(rows, query, family);
    // Unfiltered, the featured outings lead the list rather than repeating above it.
    if (!query.trim() && !family) matches.sort((a, b) => (b.featured === true) - (a.featured === true));
    offset = Math.min(offset, Math.max(0, Math.floor((matches.length - 1) / WINDOW_SIZE) * WINDOW_SIZE));
    list.replaceChildren(...matches.slice(offset, offset + WINDOW_SIZE).map(row => card(row, 'all')));
    if (!matches.length) list.append(node('p', rows.length ? 'No matching outings.' : 'No jaunts are available yet. You can explore on your own.', 'jaunt-empty'));
    previous.hidden = offset === 0; more.hidden = offset + WINDOW_SIZE >= matches.length;
    clear.hidden = !query.trim() && !family;
    for (const pill of pills.children) if (pill.dataset.family !== undefined) pill.setAttribute('aria-pressed', String(pill.dataset.family === family));
    if (focus) {
      const target = list.querySelector('button, h3') || list;
      if (!target.matches('button')) target.tabIndex = -1;
      target.focus({ preventScroll: true }); list.scrollIntoView({ block: 'start' });
    }
  }
  function show(catalog, prefix = [], returnId = null, focusStart = false) {
    rows = catalog; estimates.clear();
    search = node('input'); search.type = 'search'; search.id = 'jaunt-menu-search';
    search.placeholder = 'Search outings'; search.autocomplete = 'off'; search.value = query;
    search.setAttribute('aria-label', 'Find an outing');
    pills = node('div', '', 'jaunt-categories'); pills.setAttribute('role', 'group'); pills.setAttribute('aria-label', 'Jaunt types');
    const present = FAMILIES.filter(f => rows.some(row => row.primary_family === f));
    for (const name of ['', ...present]) {
      const pill = button('', () => { family = family === name ? '' : name; offset = 0; windowRows(); }, `jaunt-pill${name ? ` jaunt-type-${familySlot(name)}` : ''}`);
      if (name) { pill.append(icon(name, 15)); pill.title = name; }
      pill.append(node('span', name ? (SHORT[name] || name) : 'All')); pill.setAttribute('aria-label', name || 'All types');
      pill.dataset.family = name; pills.append(pill);
    }
    search.addEventListener('input', () => { query = search.value; offset = 0; windowRows(); });
    clear = button('Clear filters', () => { query = family = ''; offset = 0; search.value = ''; windowRows(); search.focus(); });
    clear.classList.add('jaunt-clear'); pills.append(clear);
    const find = node('div', '', 'jaunt-find'); find.append(icon('search', 16), search);
    // The daybook rides on the search row rather than taking a line of its own.
    const chip = prefix.find(el => el.dataset?.action === 'daybook');
    if (chip) { prefix = prefix.filter(el => el !== chip); }
    const findRow = node('div', '', 'jaunt-find-row'); findRow.append(find, ...(chip ? [chip] : []));
    const filters = node('div', '', 'jaunt-filters'); filters.append(findRow, pills);
    list = node('div', '', 'jaunt-list'); list.setAttribute('aria-label', 'All jaunts');
    previous = button('Earlier outings', () => { offset -= WINDOW_SIZE; windowRows({ focus: true }); });
    more = button('More outings', () => { offset += WINDOW_SIZE; windowRows({ focus: true }); });
    const nav = node('nav', '', 'jaunt-window-nav'); nav.setAttribute('aria-label', 'Browse outings'); nav.append(previous, more);
    root.replaceChildren(...prefix, filters, list, nav);
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
