/**
 * evidence.js — the Evidence panel as a hub of topics rather than one scroll.
 *
 * The panel used to be seven lists and their explanatory paragraphs stacked into
 * a single column: everything in it was worth reading and none of it could be
 * found. This module leaves that markup where it is — the mounts `#liberties`,
 * `#ground`, `#fauna`, `#plants`, `#exclusions`, `#uncertain` and their `-note`
 * paragraphs keep their ids, because liberties.js, ground.js, fauna.js,
 * plants.js and exclusions.js render into them from main.js and the smoke reads
 * them by id — and shows ONE topic at a time behind a grid of tiles. A tile is
 * the topic's icon, its title, how many entries its mount holds, and one line
 * saying what the list is; a topic is its entries, a search box that narrows
 * them by text, pills built from whatever `.lib-scope` chips the entries
 * carry, and the long prose folded under "About this list" so the entries come
 * first.
 *
 * Nothing here knows the shape of a topic's data. Counts, pills and search all
 * read the DOM the mounting modules produce (`details` children of the mount,
 * `.lib-scope` chip texts), so a list that grows or gains a category is
 * reflected without this file changing — and because those modules fill their
 * mounts asynchronously after boot, the counts are re-read on every show and
 * whenever a mount mutates.
 *
 * Contract (main.js): createEvidenceHub({ root, onTitle }) ->
 *   { showHub({ keep }), showTopic(id), get topic }
 * `onTitle(text, onBack)` is the drawer head (hud.setTitle): a topic pushes its
 * title and a back action; `onTitle(null)` restores the section's own name.
 * `showHub({ keep: true })` is what the tab re-selection sends: an open topic
 * stays open (the head title is re-pushed, because selecting a tab resets it).
 */
import { escapeHtml } from './citations.js';

const SVG = (paths) => `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"`
  + ` stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;

/** The topics, in the order the tiles read. Titles are NOT here: they are
 *  read from each topic's own `h3.legend-h`, so the tile and the head can never
 *  say two different things. `facet` turns one entry into the pill it belongs
 *  under (null = no pill for this entry; a topic whose entries yield fewer than
 *  two distinct facets gets no pills at all). */
const TOPICS = [
  {
    id: 'grades',
    gloss: 'attested, inferred, reconstructed — what each word promises',
    icon: SVG('<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.2l2.3 2.3 4.7-5"/>'),
    entries: (topic) => [...topic.querySelectorAll('.legend-list > li')],
    facet: () => null,
  },
  {
    id: 'city',
    gloss: 'The town in numbers: what stands, who is named, and what each grade promises',
    icon: SVG('<path d="M4 20V8l4-3 4 3v12"/><path d="M12 20V5l4-2 4 2v15"/><path d="M2 20h20"/>'),
    mount: '#city',
    entries: (topic) => [...topic.querySelectorAll('#city .gc-row')],
    facet: () => null,
  },
  {
    id: 'liberties',
    gloss: 'Every value a record states without evidence, admitted by name',
    icon: SVG('<path d="M4 20l4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10z"/><path d="M13.5 8l3 3"/>'),
    facet: scopeFacet,
  },
  {
    id: 'ground',
    gloss: 'The terrain’s own graded claims: water, levels, banks',
    icon: SVG('<path d="M3 8c3 2 6 2 9 0s6-2 9 0"/><path d="M3 13c3 2 6 2 9 0s6-2 9 0"/>'
      + '<path d="M3 18c3 2 6 2 9 0s6-2 9 0"/>'),
    facet: scopeFacet,
  },
  {
    id: 'fauna',
    gloss: 'Animals researched into ten habitats, for 1 July. None are drawn.',
    icon: SVG('<circle cx="7.5" cy="9" r="1.6"/><circle cx="12" cy="6.5" r="1.6"/><circle cx="16.5" cy="9" r="1.6"/>'
      + '<path d="M12 11.5c-3 0-5.5 2.6-5.5 5.2 0 1.6 1.2 2.6 2.6 2.6 1.1 0 1.8-.6 2.9-.6s1.8.6 2.9.6c1.4 0 2.6-1 2.6-2.6 0-2.6-2.5-5.2-5.5-5.2z"/>'),
    facet: () => null,
  },
  {
    id: 'plants',
    gloss: 'Plant communities and their species, for 1 July',
    icon: SVG('<path d="M12 21v-9"/><path d="M12 12c0-4.5 3.2-7.5 8-7.5 0 5.2-3.2 8.2-8 7.5z"/>'
      + '<path d="M12 16c0-3-2.6-5-6-5 0 3.6 2.6 5.6 6 5z"/>'),
    facet: () => null,
  },
  {
    id: 'exclusions',
    gloss: 'Buildings dated later than 1 July 1835, or already gone',
    icon: SVG('<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>'),
    // The chip is the record's own `earliest_scene`; an entry without one had
    // already come down. Two findings, one list — the pills tell them apart.
    facet: (entry) => (scopeFacet(entry) ? 'not until' : 'came down'),
  },
  {
    id: 'uncertain',
    gloss: 'Doubts on the record, and what settling them would change',
    icon: SVG('<circle cx="12" cy="12" r="8.5"/><path d="M9.5 9.6a2.6 2.6 0 1 1 4.1 2.1c-1 .8-1.6 1.4-1.6 2.6"/>'
      + '<path d="M12 17.4h.01"/>'),
    facet: scopeFacet,
  },
  {
    id: 'population',
    gloss: 'Who the sources actually name, profiled axis by axis',
    icon: SVG('<circle cx="9" cy="8.5" r="3"/><path d="M3.5 19.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/>'
      + '<path d="M16 6.2a3 3 0 0 1 0 5.6"/><path d="M17.5 14.9c1.9.6 3 2.4 3 4.6"/>'),
    // The chip is the section's own row count: an axis is as big as the table
    // under it, and a pill per axis would be a pill per entry.
    facet: () => null,
  },
  {
    id: 'orderbook',
    gloss: 'What the town still owes: the quota, bucket by bucket',
    icon: SVG('<path d="M4 5.5h6.5a2 2 0 0 1 2 2V19a2 2 0 0 0-2-2H4z"/>'
      + '<path d="M20 5.5h-5.5a2 2 0 0 0-2 2V19a2 2 0 0 1 2-2H20z"/>'
      + '<path d="M12.5 7.5V19"/>'),
    // The chip is the family's own filled/to-do count, which the summary row
    // already carries — a pill per bucket would be a pill per cell of the town.
    facet: () => null,
  },
];

/** The chip text on an entry's own summary row — not a nested entry's. */
function scopeFacet(entry) {
  const chip = entry.querySelector(':scope > summary .lib-scope');
  return chip ? chip.textContent.trim() : null;
}

const norm = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();

export function createEvidenceHub({ root, onTitle = () => {} } = {}) {
  if (!root) return { showHub() {}, showTopic() {}, get topic() { return null; } };

  const hub = root.querySelector('#evidence-hub');
  const topics = new Map();
  for (const spec of TOPICS) {
    const el = root.querySelector(`.ev-topic[data-topic="${spec.id}"]`);
    if (!el) continue;
    const mount = el.querySelector(spec.mount || '.liberties') || el.querySelector('.legend-list');
    const title = el.querySelector('.ev-topic-title')?.textContent.trim() || spec.id;
    const entries = spec.entries || ((topic) => [...(mount?.querySelectorAll(':scope > details') ?? [])]);
    topics.set(spec.id, { ...spec, facetOf: spec.facet, el, mount, title, entries: () => entries(el), query: '', facet: null });
  }

  let current = null;

  // ---- tiles --------------------------------------------------------------
  if (hub) {
    hub.innerHTML = [...topics.values()].map((t) => `<button class="ev-tile" type="button" data-topic="${t.id}"`
      + ` aria-label="${escapeHtml(t.title)}">`
      + `<span class="ev-tile-head">${t.icon}<b class="ev-count" aria-label="entries">…</b></span>`
      + `<span class="ev-tile-title">${escapeHtml(t.title)}</span>`
      + `<span class="ev-gloss">${escapeHtml(t.gloss)}</span></button>`).join('');
    hub.addEventListener('click', (e) => {
      const tile = e.target.closest('.ev-tile');
      if (tile) showTopic(tile.dataset.topic, { focus: true });
    });
  }

  /** The count on a tile is the mount's entries, read now. A mount still marked
   *  `aria-busy` (the module has not filled it) shows an ellipsis rather than a
   *  zero, because zero would be a claim. */
  function paintCounts() {
    for (const t of topics.values()) {
      const chip = hub?.querySelector(`.ev-tile[data-topic="${t.id}"] .ev-count`);
      if (!chip) continue;
      const busy = t.mount?.hasAttribute('aria-busy');
      const n = t.entries().length;
      chip.textContent = busy && n === 0 ? '…' : String(n);
      chip.classList.toggle('is-busy', !!busy && n === 0);
    }
  }

  // The modules fill their mounts after boot, each on its own fetch; the tiles
  // follow the mounts rather than any of those promises.
  let raf = 0;
  const schedule = () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      paintCounts();
      if (current) applyFilter(topics.get(current), { rebuildPills: true });
    });
  };
  if (typeof MutationObserver === 'function') {
    const mo = new MutationObserver(schedule);
    for (const t of topics.values()) if (t.mount) mo.observe(t.mount, { childList: true, subtree: false, attributes: true, attributeFilter: ['aria-busy'] });
  }

  // ---- per-topic tools: search, pills, status -----------------------------
  for (const t of topics.values()) {
    if (t.id === 'grades' || t.id === 'city') continue; // compact summaries need no search box
    const tools = document.createElement('div');
    tools.className = 'ev-tools';
    tools.innerHTML = `<div class="ev-search-row"><input class="ev-search" type="search" autocomplete="off" spellcheck="false"`
      + ` placeholder="Search ${escapeHtml(t.title.toLowerCase())}…" aria-label="Search ${escapeHtml(t.title.toLowerCase())}">`
      + `<span class="ev-status" aria-live="polite"></span></div>`
      + `<div class="ev-pills" role="group" aria-label="Narrow by kind" hidden></div>`
      + `<p class="ev-empty" hidden></p>`;
    // First in the topic, after its (head-duplicated) title: the tools are what
    // a visitor reaches for before the note, and the mount stays the last child
    // so the `-note` → list sibling walk the smoke does still spans the block.
    const title = t.el.querySelector('.ev-topic-title');
    if (title) title.after(tools); else t.el.prepend(tools);
    t.tools = tools;
    t.search = tools.querySelector('.ev-search');
    t.status = tools.querySelector('.ev-status');
    t.pills = tools.querySelector('.ev-pills');
    t.empty = tools.querySelector('.ev-empty');
    // The empty state sits with the entries, where the entries would be.
    if (t.mount) t.mount.before(t.empty);
    t.search.addEventListener('input', () => { t.query = t.search.value; applyFilter(t); });
    t.pills.addEventListener('click', (e) => {
      const pill = e.target.closest('.ev-pill');
      if (!pill) return;
      const v = pill.dataset.facet ?? null;
      t.facet = (v === '' || t.facet === v) ? null : v;
      applyFilter(t);
    });
  }

  /** Pills are the distinct facets the entries carry right now, single-select,
   *  with "All" first. Rebuilt only when asked (a mount mutated) so the pressed
   *  one keeps its identity across filtering. */
  function buildPills(t) {
    if (!t.pills) return;
    const facets = new Map();
    for (const en of t.entries()) {
      const f = t.facetOf(en);
      if (f) facets.set(f, (facets.get(f) || 0) + 1);
    }
    if (facets.size < 2 || facets.size > 12) {
      t.pills.hidden = true; t.pills.innerHTML = ''; t.facet = null; return;
    }
    if (t.facet && !facets.has(t.facet)) t.facet = null;
    const items = [['', 'All', t.entries().length], ...[...facets.entries()].map(([f, n]) => [f, f, n])];
    t.pills.innerHTML = items.map(([v, label, n]) => `<button class="ev-pill" type="button" data-facet="${escapeHtml(v)}"`
      + ` aria-pressed="${String((t.facet ?? '') === v)}">${escapeHtml(label)} <small>${n}</small></button>`).join('');
    t.pills.hidden = false;
  }

  /** Show the entries whose text carries the query and whose facet is the
   *  pressed pill. Entries that hold entries (a habitat with its animals, a
   *  community with its plants) are opened around their matching children while
   *  a query stands, and closed again when it clears — the visitor's own opens
   *  are left alone. */
  function applyFilter(t, { rebuildPills = false } = {}) {
    if (!t || !t.tools) return;
    if (rebuildPills) buildPills(t);
    else t.pills?.querySelectorAll('.ev-pill').forEach((p) => p.setAttribute('aria-pressed', String((t.facet ?? '') === (p.dataset.facet ?? ''))));
    const q = norm(t.query);
    const all = t.entries();
    let shown = 0;
    for (const en of all) {
      const facetOk = !t.facet || t.facetOf(en) === t.facet;
      const textOk = !q || norm(en.textContent).includes(q);
      const on = facetOk && textOk;
      en.toggleAttribute('hidden', !on);
      if (on) shown += 1;
      const nested = [...en.querySelectorAll(':scope > * details, :scope > details')];
      if (!nested.length) continue;
      if (on && q) {
        const hits = nested.filter((d) => norm(d.textContent).includes(q));
        // A match on the parent's own words alone leaves its children as they were.
        const narrow = hits.length > 0 && hits.length < nested.length;
        nested.forEach((d) => d.toggleAttribute('hidden', narrow && !hits.includes(d)));
        if (hits.length && !en.open) { en.open = true; en.dataset.evOpened = '1'; }
      } else {
        nested.forEach((d) => d.removeAttribute('hidden'));
        if (en.dataset.evOpened) { delete en.dataset.evOpened; en.open = false; }
      }
    }
    const total = all.length;
    const filtered = !!q || !!t.facet;
    t.status.textContent = total === 0 ? '' : filtered ? `${shown} of ${total} shown` : `${total} entries`;
    const none = filtered && total > 0 && shown === 0;
    t.empty.hidden = !none;
    if (none) {
      t.empty.textContent = q
        ? `Nothing here carries “${t.query.trim()}”. Try a shorter word, a name, or clear the search.`
        : 'Nothing under this pill yet. Choose another, or All.';
    }
  }

  // ---- views ---------------------------------------------------------------
  function scrollTop() {
    const sc = root.closest('.panel-scroll') || root.parentElement;
    if (sc) sc.scrollTop = 0;
  }

  function showTopic(id, { focus = false } = {}) {
    const t = topics.get(id);
    if (!t) return;
    current = id;
    if (hub) hub.hidden = true;
    for (const o of topics.values()) o.el.hidden = o !== t;
    paintCounts();
    applyFilter(t, { rebuildPills: true });
    onTitle(t.title, () => showHub({ focusTile: id }));
    scrollTop();
    if (focus) {
      t.el.setAttribute('tabindex', '-1');
      t.el.focus({ preventScroll: true });
    }
  }

  function showHub({ keep = false, focusTile = null } = {}) {
    if (keep && current) {
      // The tab was re-selected: stay where the visitor was, and re-push the
      // head title the tab change just reset.
      const t = topics.get(current);
      paintCounts();
      applyFilter(t, { rebuildPills: true });
      onTitle(t.title, () => showHub({ focusTile: current }));
      return;
    }
    const left = focusTile ?? current;
    current = null;
    for (const o of topics.values()) o.el.hidden = true;
    if (hub) hub.hidden = false;
    paintCounts();
    onTitle(null);
    scrollTop();
    if (focusTile && hub) hub.querySelector(`.ev-tile[data-topic="${left}"]`)?.focus({ preventScroll: true });
  }

  showHub();

  return {
    showHub,
    showTopic,
    get topic() { return current; },
  };
}
