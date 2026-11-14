/** Lazy catalog browser. A bounded, keyboard-accessible window holds at most 30 outings.
 *  T-2120: one compact row per outing — a type icon and colour, a one-line premise, its
 *  length — with Start on the row and the rest (travel mode, route preview) folded under it. */
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';
import { GROUPS, groupIcon, groupOf, groupSlot, icon } from './menu-icons.js';
import { TIME_NAMES } from './time-of-day.js';

export const WINDOW_SIZE = 30;
/** A title as it sorts: without a leading A, An or The, so "A Letter Home" sits under L. */
export const sortTitle = (title = '') => String(title).replace(/^(?:a|an|the)\s+/i, '');
/**
 * T-2944 (owner, 2026-10-20: "do keep them sorted together so they make snese"): related
 * outings sit together, by group in the order the pills show (T-3584: Places, People,
 * Architecture, Stories, Errands, Work, Build log; anything else after), then the featured
 * ones first within their group, then by name without its article. T-3584 (owner,
 * 2026-11-13: "feature the household tour first and then the other glessner jaunt after
 * that"): a jaunt with a `menu_rank` leads the whole list, in rank order, ahead of every
 * group; the Build log (every building modelled so far) comes last.
 */
const rank = (r) => (Number.isInteger(r.menu_rank) ? r.menu_rank : Infinity);
/** T-3590: the US school grade bands a jaunt is written for (data/jaunts/schema.json grade_band). */
export const GRADE_BANDS = ['K-2', '3-5', '6-8', '9-10', '11-12'];
export const gradeLabel = (band) => (GRADE_BANDS.includes(band) ? `Grades ${band.replace('-', '–')}` : '');
function placeOrder(a, b) {
  const kind = (r) => { const i = GROUPS.indexOf(groupOf(r)); return i < 0 ? GROUPS.length : i; };
  return (rank(a) === rank(b) ? 0 : rank(a) < rank(b) ? -1 : 1)
    || kind(a) - kind(b) || (b.featured === true) - (a.featured === true)
    || sortTitle(a.title).localeCompare(sortTitle(b.title)) || String(a.id).localeCompare(String(b.id));
}
/** T-3590: a version of a jaunt for another grade band (`version_of`) sits right after the
 *  jaunt it retells, versions in grade order; `baseOf(row)` finds that jaunt's row. */
export function jauntOrder(a, b, baseOf = () => null) {
  const A = (a.version_of && baseOf(a)) || a, B = (b.version_of && baseOf(b)) || b;
  if (A !== B) return placeOrder(A, B);
  return (a === A ? -1 : 0) + (b === B ? 1 : 0)
    || GRADE_BANDS.indexOf(a.grade_band) - GRADE_BANDS.indexOf(b.grade_band) || String(a.id).localeCompare(String(b.id));
}
/** T-3377: the light an outing is walked in, as its card says it: "Dusk · Fall". */
export function ambienceLabel(ambience) {
  if (!ambience) return '';
  const hour = ambience.hour ? (TIME_NAMES.find(n => n.id === ambience.hour)?.label ?? ambience.hour) : '';
  const season = ambience.season ? ambience.season[0].toUpperCase() + ambience.season.slice(1) : '';
  return [hour, season].filter(Boolean).join(' · ');
}
export function filterJaunts(rows, query = '', group = '') {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const byId = new Map(rows.map(row => [row.id, row]));
  return rows.filter(row => (!group || groupOf(row) === group) && words.every(word =>
    `${row.title} ${row.premise} ${row.category} ${groupOf(row)} ${row.primary_family} ${gradeLabel(row.grade_band)}`.toLocaleLowerCase().includes(word)))
    .sort((a, b) => jauntOrder(a, b, row => byId.get(row.version_of)));
}

// T-2631: `plateFor(row)` gives a credited picture of the route's stops, or null; `kept(row)`
// says the visitor holds this outing's keepsake.
export function createJauntMenu({ root, estimate, onStart, onPreview, plateFor = () => null, kept = () => false, preferredMode = () => null, modeNote = () => '' }) {
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
    const group = groupOf(row), slot = groupSlot(group), available = row.availability === 'available';
    const el = node('article', '', `jaunt-card jaunt-type-${slot}`); el.dataset.jaunt = row.id; el.dataset.section = section;
    const badge = node('span', '', 'jaunt-type'); badge.append(icon(groupIcon(group), 20));
    badge.title = group;
    // T-2631: a credited picture of the route's own stops, where the project holds one.
    // Never a stand-in: with none, the family icon stays.
    const plate = plateFor(row);
    if (plate?.src) {
      const img = document.createElement('img');
      img.className = 'jaunt-plate'; img.alt = plate.alt; img.loading = 'lazy'; img.decoding = 'async'; img.src = plate.src;
      badge.replaceChildren(img); badge.classList.add('has-plate'); badge.title = plate.full;
    }
    const body = node('div', '', 'jaunt-row-body'), head = node('div', '', 'jaunt-head');
    const title = node('h3', row.title);
    if (row.featured) title.append(node('span', '★', 'jaunt-star'));
    head.append(title);
    const length = node('span', '', 'jaunt-length'); length.dataset.jauntLength = row.id;
    const meta = node('p', '', 'jaunt-tags');
    meta.append(node('span', group, 'jaunt-family'), node('span', `${row.stop_count} stops`), length);
    // T-3590: the school grades its words are written for.
    const grades = gradeLabel(row.grade_band);
    if (grades) { const tag = node('span', grades, 'jaunt-grade'); tag.title = `Written for US school ${grades.toLowerCase()}`; meta.append(tag); }
    const light = ambienceLabel(row.ambience);
    if (light) { const tag = node('span', light, 'jaunt-light'); tag.title = 'The jaunt sets this time of day and season, and gives yours back at the end'; meta.append(tag); }
    // T-2631: the keepsake, once earned, on the outing's own card.
    if (kept(row)) meta.append(node('span', 'Keepsake earned', 'jaunt-kept'));
    body.append(head, node('p', row.premise, 'jaunt-premise'), meta);
    if (plate?.src) { const credit = node('p', `Picture: ${plate.credit}`, 'jaunt-credit'); credit.title = plate.full; body.append(credit); }
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
    mode.setAttribute('aria-label', `How to move for ${row.title}`); mode.dataset.action = 'mode';
    const duration = node('p', '', 'jaunt-meta'); duration.dataset.jauntEstimate = row.id;
    duration.setAttribute('aria-live', 'polite');
    // T-2652/T-2727: a mode picked here by hand; else the visitor's getting-there choice,
    // where Jaunts use it and this outing allows it; else its own. Only a hand pick is
    // remembered, so turning Jaunts use my choice on or off reaches every card.
    let current = modes.get(row.id) || preferredMode(row) || row.default_mode || 'walk';
    const price = () => {
      const key = JSON.stringify([current, row.destinations, row.timing, row.stops]);
      if (!estimates.has(key)) { const e = estimate(row, current); estimates.set(key, { text: formatEstimate(e), s: e?.seconds }); }
      const { text, s } = estimates.get(key);
      duration.textContent = `${text} at ${PACES[current]?.label || current}`;
      length.textContent = Number.isFinite(s) ? `${Math.max(1, Math.round(s / 60))} min` : '';
      length.dataset.size = !Number.isFinite(s) ? '' : s < 600 ? 's' : s < 1200 ? 'm' : 'l';
      for (const b of mode.children) b.setAttribute('aria-checked', String(b.dataset.mode === current));
    };
    for (const id of row.allowed_modes || ['walk']) {
      const b = button('', () => { if (b.disabled) return; current = id; modes.set(row.id, id); price(); }, 'jaunt-mode-pick');
      b.dataset.mode = id; b.setAttribute('role', 'radio'); b.append(icon(id, 18));
      b.setAttribute('aria-label', PACES[id]?.label || id); b.title = PACES[id]?.label || id;
      mode.append(b);
    }
    price();
    details.append(node('p', row.premise, 'jaunt-premise-full'), node('p', `${row.category} · ${group}`, 'jaunt-meta'));
    if (!available) {
      for (const b of mode.children) b.disabled = true;
      meta.append(node('span', 'Held', 'jaunt-held'));
      details.append(node('p', `Unavailable — ${row.reason || 'Awaiting review.'}`, 'jaunt-meta'));
    } else {
      const pace = node('div', '', 'jaunt-pace'); pace.append(mode, duration);
      details.append(pace, node('p', `Recommended: ${PACES[row.default_mode || 'walk']?.label || row.default_mode}.`, 'jaunt-meta'));
      // T-2727: with Jaunts use my choice on, an outing that cannot go the visitor's way says so.
      const keeps = modeNote(row);
      if (keeps) { const p = node('p', keeps, 'jaunt-meta jaunt-keeps'); p.dataset.jauntKeeps = row.id; details.append(p); }
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
    // T-2944/T-3584: ranked first, then by group, featured first within each (jauntOrder); no second sort here.
    const matches = filterJaunts(rows, query, family);
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
    pills = node('div', '', 'jaunt-categories'); pills.setAttribute('role', 'group'); pills.setAttribute('aria-label', 'Jaunt groups');
    const present = GROUPS.filter(g => rows.some(row => groupOf(row) === g));
    for (const name of ['', ...present]) {
      const pill = button('', () => { family = family === name ? '' : name; offset = 0; windowRows(); }, `jaunt-pill${name ? ` jaunt-type-${groupSlot(name)}` : ''}`);
      if (name) { pill.append(icon(groupIcon(name), 15)); pill.title = name; }
      pill.append(node('span', name || 'All')); pill.setAttribute('aria-label', name || 'All types');
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
