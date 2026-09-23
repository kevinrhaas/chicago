/**
 * businesses.js — the Businesses section of the drawer: every firm the town's
 * record knows, findable.
 *
 * WHY THIS EXISTS. The renderer never opened `register_1835.json` or the
 * business layer at all: a firm reached a visitor only through a building
 * card's "Use"/"Keepers" lines, a signboard tap, or the agencies panel. That
 * works for the 30 houses that stand in a roof of their own, and it leaves the
 * other 166 — 26 placed against a landmark and no closer, 61 known to a street
 * and no further, 79 the register could place nowhere at all — invisible in a
 * walk of the town. They are not
 * lesser evidence. A printed advertisement with no address is still a house
 * that traded here, and the one thing it must never become is a building
 * invented to carry it. So it gets a card instead of a roof.
 *
 * WHAT IT READS. `data/businesses/index.json`, which `tools/compile_businesses.py`
 * derives from the register, the gazetteer and the resident layer — one row a
 * firm, carrying what a list needs to sort, filter, count and search. The record
 * itself is fetched the first time a card is opened, the way `people.js` fetches
 * a household: the list is 196 rows and must paint at once; a card is one file.
 *
 * THE GRADE ON A ROW is the FIRM's, and a firm states its tiers in three places
 * — who ran it, where it stood, when it opened. `compile_businesses.record_grade`
 * folds those into one: attested where any of them is attested, reconstructed
 * where every one of them is, inferred otherwise. The card prints all three
 * separately, so the fold can always be unpicked.
 *
 * THE PLACE FILTER is the point of the view. `premises` is a roof of its own,
 * `anchored` is "next door to the Sauganash" and no roof, `street_only` is a
 * street and no more, `unplaceable` is a house the register could not put
 * anywhere — and every one of those says, in the record's own words, WHY it
 * stops there. A visitor can ask for the unplaceable ones and read 79 limits.
 *
 * It files a firm ONCE, under its primary location, so the tally it counts by is
 * `counts.by_where_kind` (firms) and never `counts.by_location_kind` (locations).
 * Four of these houses moved inside the window and carry two addresses; a firm
 * filed under the street it ended on still holds the unplaceable one it left.
 *
 * Contract (main.js): `mountBusinesses({ mount, index, registry, dataBase,
 * onGoTo, onPerson, onTitle, problems })` -> `{ businesses, error, search,
 * open, close, filter, results, state }`.
 */

import { escapeHtml } from './citations.js';
import { displayName } from './display-name.js';
import { loadResidentJoins, words } from './residents.js';
import { seatHtml, seatTarget } from './seat.js';

/** Diacritics folded, lower-cased, one space between words — the same reduction
 *  people.js applies, so the two directories answer a query the same way. */
function fold(s) {
  return String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim();
}

const n = (x) => Number(x || 0).toLocaleString('en-GB');

/**
 * THE CROSSWALK, BOTH WAYS — the index folded once so the three places a visitor
 * ALREADY IS can reach a firm's card without opening the directory at all.
 *
 * The directory is the way in for somebody who came looking for a firm. It is
 * the wrong way in for the visitor standing under a board, reading a building's
 * card, or reading the card of the man who kept the place: they are already at
 * the firm and the town made them go and find it by name. So the same two
 * questions — WHICH FIRMS DOES THIS PERSON HOLD A ROLE IN, and WHICH FIRMS DOES
 * THE REGISTER PUT IN THIS ROOF — are answered once, here, off the compiled
 * index, and `people.js` and `popup.js` share the answer instead of each folding
 * 196 rows their own way.
 *
 * `byPerson` reads each row's `people[]`, which `compile_businesses.index_people`
 * flattens from proprietors, partners and staff. 144 of those 196 roles name a
 * person the town holds a card for, 110 distinct people between them, and 27 of
 * those hold more than one firm — John Dean Caton holds four, which is a fact
 * about the town that no card said until this.
 *
 * Those counts fell in T-1401 and nothing left the layer: the register printed
 * thirteen of these roles twice, under a second style of the same person's name,
 * and the compiler folds them onto one row now (`also_printed_as` keeps the
 * styles). The fold used to happen here, over an index that double-counted.
 *
 * `byStructure` reads each row's PRIMARY location and answers with TWO relations,
 * because a roof holds houses two ways. `in` is a premises — the register puts the
 * firm in this building — and 22 roofs carry the 30 firms with one. `against` is an
 * `anchored` house: no roof of its own, and the paper sites it by this one. Until
 * T-1401 the second was unanswerable, because the landmark lived only inside
 * `limit_reason`'s sentence and `structure_id` was null on all 26; the compiler now
 * resolves the register's own `action_target` onto `where.anchor`, so the Tremont
 * House names the four houses standing against it and nothing here reads a sentence.
 *
 * Seven of the 26 anchor against another FIRM and four against a street crossing.
 * Neither is a roof, so neither joins this map — the business card prints them, and
 * the firm-to-firm one offers the other firm's card.
 *
 * @param {object|null} index  the compiled `businesses/index.json`
 * @returns {{byPerson: Map<string, object[]>, byStructure: Map<string, object[]>}}
 */
export function firmCrosswalk(index) {
  const byPerson = new Map();
  const byStructure = new Map();
  const push = (map, key, value) => {
    if (!key) return;
    const list = map.get(key);
    if (list) list.push(value);
    else map.set(key, [value]);
  };
  for (const r of (index?.businesses || [])) {
    const firm = {
      id: r.id,
      name: r.name,
      grade: r.grade,
      trade: r.trade || (r.occupation ? words(r.occupation) : ''),
      kind: r.where?.kind || null,
      street: r.where?.street || null,
      present: !!r.present_at_scene_date,
      opened: r.opened || null,
    };
    // ONE ROW A FIRM, NOT ONE ROW A PRINTING. The twelve person-firm pairs the
    // register printed under two styles fold in the DATA now (T-1401), so this
    // sees one row each where it used to see two. It still folds, for the reason
    // it was written: a record may legitimately name one person in two ROLES —
    // proprietor and staff of the same house — and the directory lists a firm
    // once under a person whatever the register called them that week.
    const seen = new Map();
    for (const p of (r.people || [])) {
      if (!p.person_id) continue;
      const key = `${p.person_id}\u0000${r.id}`;
      const had = seen.get(key);
      if (had) {
        if (p.role && !had.roles.includes(p.role)) had.roles.push(p.role);
        continue;
      }
      const entry = {
        ...firm, roles: [p.role || 'proprietor'], tier: p.tier || null,
        from: p.from || null, to: p.to || null,
      };
      seen.set(key, entry);
      push(byPerson, p.person_id, entry);
    }
    if (r.where?.kind === 'premises') push(byStructure, r.where.structure_id, { ...firm, relation: 'in' });
    else if (r.where?.kind === 'anchored' && r.where.anchor?.kind === 'structure') {
      push(byStructure, r.where.anchor.id, { ...firm, relation: 'against' });
    }
  }
  // A roof with three firms and a man with five want a settled order, and the one
  // the town can defend is the record's: what a source attests first, then by name.
  const rank = { attested: 0, inferred: 1, reconstructed: 2 };
  // Houses IN the roof before houses standing AGAINST it — the card asks the two
  // questions in that order — then what a source attests first, then by name.
  const sort = (list) => list.sort((a, b) => (a.relation === 'against') - (b.relation === 'against')
    || (rank[a.grade] ?? 3) - (rank[b.grade] ?? 3)
    || a.name.localeCompare(b.name));
  for (const list of byPerson.values()) sort(list);
  for (const list of byStructure.values()) sort(list);
  return { byPerson, byStructure };
}

/** How far the record could place a house, in the visitor's words. The order is
 *  the ladder: a roof, a landmark, a street, nothing. */
const PLACE = {
  premises: ['on a roof', 'A building of its own in this town — the card takes you to it'],
  anchored: ['by a landmark', 'Placed against a building the town holds, with no roof of its own'],
  street_only: ['street only', 'A street and no further: the printing names no premises'],
  unplaceable: ['unplaceable', 'The register resolved no place for this house at all'],
};

const GRADE_TITLE = {
  attested: 'a source attests this house — its keeper, its premises or its opening — at first hand',
  inferred: 'reasoned from the evidence: the printings put this house here, and no one claim of it is attested',
  reconstructed: 'no source speaks to this house; built to fill a count the town demonstrably needed',
};

/** The two liberties a compiled business can owe, in the schema's own words. */
const LIBERTY = {
  survival_required: 'Documented before 1 July 1835 and assumed still trading on it.',
  backdating_required: 'Documented only after 1 July 1835 and assumed already open on it.',
};

/** A date as a card prints it: the ISO day where there is one, the year alone
 *  where the record gives only that, an em dash where it gives nothing. */
function day(d) {
  if (!d) return '—';
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(d));
  if (!m) return String(d);
  const month = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'][Number(m[2]) - 1];
  return `${Number(m[3])} ${month} ${m[1]}`;
}

/** The filter rows, declared as data so the per-pill count pass can drop one row
 *  at a time — the same shape people.js uses, for the same reason. */
function filterSpecs(rows, counts, vocabulary) {
  const tally = (get) => {
    const c = new Map();
    for (const r of rows) for (const v of [].concat(get(r) ?? [])) if (v) c.set(v, (c.get(v) || 0) + 1);
    return c;
  };
  const types = tally((r) => r.type);
  const trades = tally((r) => r.occupation);
  const streets = tally((r) => r.where?.street);
  const topTypes = [...types.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 6);
  const topTrades = [...trades.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 8);
  const grades = ['attested', 'inferred', 'reconstructed'].filter((g) => (counts.by_grade || {})[g] > 0);
  // T-1378, from T-1177. The community of the house, read off the keepers its own
  // record names and their cards in the resident layer — never off a surname. The pills
  // stand in the vocabulary's order rather than by count, as the People view's do, and a
  // term no house carries is left off until a reading puts somebody behind it: today
  // that is Irish, German, French Canadian and all four Native terms. T-1403 put the
  // first two behind it — free Black on T-1377's two reconstructed firms, Metis on
  // Alexander Robinson's attested store at Wolf Point — so the filter the ticket asks
  // for is this one pill list and it now answers.
  // `Unknown` IS a pill. It is the answer for 85 of these 201 houses — the register
  // names nobody the town holds a card for, or names nobody at all — and a filter that
  // hid it would let the directory read as though the town's trade were settled.
  const communities = (vocabulary?.communities || []).filter((c) => c.count > 0);
  return [
    {
      key: 'type', label: 'Kind',
      options: topTypes.map(([v]) => [v, words(v)]),
      more: [...types.keys()].sort().map((v) => [v, words(v)]),
      test: (v) => (r) => r.type.includes(v),
    },
    {
      key: 'occupation', label: 'Trade',
      options: topTrades.map(([v]) => [v, words(v)]),
      more: [...trades.keys()].sort().map((v) => [v, words(v)]),
      test: (v) => (r) => r.occupation === v,
    },
    {
      key: 'street', label: 'Street',
      options: [...streets.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([v]) => [v, v.replace(/ Street$/, '')]),
      test: (v) => (r) => r.where?.street === v,
    },
    {
      key: 'place', label: 'How far it is placed',
      options: Object.keys(PLACE).map((v) => [v, PLACE[v][0]]),
      test: (v) => (r) => r.where?.kind === v,
    },
    {
      key: 'community', label: 'Community',
      options: communities.map((c) => [c.value, c.label]),
      test: (v) => (r) => (r.proprietor_community || 'unknown') === v,
    },
    {
      key: 'grade', label: 'Grade', group: 'facts',
      options: grades.map((v) => [v, v]),
      test: (v) => (r) => r.grade === v,
    },
    {
      key: 'present', label: '', toggle: true, group: 'facts',
      options: [['yes', 'Trading on 1 July']],
      test: () => (r) => !!r.present_at_scene_date,
    },
  ];
}

/**
 * Mount the directory into `mount` (`#businesses-directory`).
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount
 * @param {object|null} o.index        the compiled `businesses/index.json`, or null
 * @param {Map} o.registry             loaded structures by id, for a premises title
 * @param {URL} o.dataBase             where data/ lives
 * @param {(target: object) => void} o.onGoTo          travel to a firm's building
 * @param {(personId: string) => void} [o.onPerson]    open a proprietor's own card
 * @param {(text: string|null, onBack?: Function) => void} [o.onTitle]
 * @param {string[]} [o.problems]
 */
export async function mountBusinesses({
  mount, index, registry, dataBase, sceneId, onGoTo, onPerson = null, onTitle = null, problems = [],
} = {}) {
  const idle = {
    search() { return 0; }, open() { return Promise.resolve(false); }, close() {},
    filter() { return 0; }, results() { return []; }, get state() { return null; },
  };
  if (!mount) return { businesses: 0, error: 'no mount', ...idle };
  if (!index || !Array.isArray(index.businesses)) {
    mount.innerHTML = '<p class="legend-note">The businesses directory did not load '
      + '(<code>data/businesses/index.json</code>). The firms with a roof are still on their '
      + 'building cards.</p>';
    return { businesses: 0, error: 'businesses/index.json missing', ...idle };
  }

  const section = mount.closest('.panel-body');
  if (typeof onTitle === 'function') section?.classList.add('has-head-back');

  const counts = index.counts || {};
  const rows = index.businesses.map((r) => ({
    ...r,
    _name: fold(r.name),
    _words: fold(r.name).split(' '),
    // Searchable: the firm's name and every style it printed itself under, what it
    // sold, the trade word, the street, and everyone the record names — a visitor
    // looking for "Harmon" or for "crockery" is asking the same list one question.
    _text: fold([r.name, ...(r.firm_styles || []), ...(r.goods || []), r.trade,
      r.occupation ? words(r.occupation) : '', ...r.type.map((t) => words(t)),
      r.where?.street || '', ...(r.people || []).flatMap((p) => [p.name, ...(p.also_printed_as || [])])].join(' ')),
  }));
  const byId = new Map(rows.map((r) => [r.id, r]));
  const specs = filterSpecs(rows, counts, index.vocabulary);
  const COMMUNITY_LABEL = new Map(
    (index.vocabulary?.communities || []).map((c) => [c.value, c.label]));

  const compact = typeof matchMedia === 'function' ? matchMedia('(max-width: 620px)') : null;
  const state = {
    q: '', filters: {}, open: null, matched: 0, lastOpened: null,
    filtersOpen: !(compact && compact.matches),
    // The in-flight address-book seat fill for the open card (T-1493).
    seatPending: null,
  };

  mount.innerHTML = `
    <div class="people-home biz-home">
      <p class="people-count" id="businesses-count">${n(counts.records)} firms the record knows
        · ${n(counts.present_at_scene_date)} trading on 1 July 1835
        · ${n((counts.by_where_kind || {}).premises)} with a roof of their own</p>
      <div class="field people-field">
        <input type="search" id="businesses-search" placeholder="A firm, a keeper, a trade, a good…"
          autocomplete="off" spellcheck="false" aria-label="Search the businesses of the town"
          aria-controls="businesses-results">
      </div>
      <div class="people-toolbar">
        <button type="button" class="pill people-filters-toggle" id="businesses-filters-toggle"
          aria-expanded="false" aria-controls="businesses-filters">Filters</button>
      </div>
      <div id="businesses-filters" class="people-filters"></div>
      <p class="people-note" id="businesses-result-note" aria-live="polite"></p>
      <div id="businesses-results" class="people-results" role="listbox" aria-label="Businesses"></div>
    </div>
    <div id="businesses-card" class="people-card biz-card" hidden></div>`;

  const $ = (sel) => mount.querySelector(sel);
  const home = $('.biz-home');
  const input = $('#businesses-search');
  const filtersEl = $('#businesses-filters');
  const filtersToggle = $('#businesses-filters-toggle');
  const noteEl = $('#businesses-result-note');
  const resultsEl = $('#businesses-results');
  const cardEl = $('#businesses-card');

  // ---- filtering -------------------------------------------------------- //

  function activeTests(except = null) {
    const tests = [];
    for (const spec of specs) {
      const v = state.filters[spec.key];
      if (v === undefined || v === null || v === '' || spec.key === except) continue;
      tests.push(spec.test(v));
    }
    return tests;
  }

  function searchRank(r, q, qWords) {
    if (!q) return 0;
    for (const w of qWords) if (!r._text.includes(w)) return -1;
    if (r._name.startsWith(q)) return 0;
    if (r._words.some((w) => w.startsWith(q))) return 1;
    if (r._name.includes(q)) return 2;
    return 3;
  }

  function matches(except = null) {
    const q = fold(state.q);
    const qWords = q ? q.split(' ') : [];
    const tests = activeTests(except);
    const out = [];
    for (const r of rows) {
      let ok = true;
      for (const t of tests) if (!t(r)) { ok = false; break; }
      if (!ok) continue;
      const rank = searchRank(r, q, qWords);
      if (rank < 0) continue;
      out.push([rank, r]);
    }
    if (q) out.sort((a, b) => a[0] - b[0]);
    return out.map(([, r]) => r);
  }

  // ---- filter pills ----------------------------------------------------- //

  function pill(key, value, label, count, on) {
    const empty = count === 0 && !on;
    return `<button type="button" class="pill" data-filter="${escapeHtml(key)}" data-value="${escapeHtml(value)}"
      aria-pressed="${on ? 'true' : 'false'}"${empty ? ' disabled' : ''}>${escapeHtml(label)}${
      count === null ? '' : ` <span class="pill-n">${n(count)}</span>`}</button>`;
  }

  function paintFilters() {
    const anyOn = Object.values(state.filters).some((v) => v !== undefined && v !== null && v !== '');
    const rowHtml = (spec) => {
      const current = state.filters[spec.key] ?? '';
      const pool = matches(spec.key);
      const countOf = (v) => { const t = spec.test(v); let c = 0; for (const r of pool) if (t(r)) c++; return c; };
      const label = spec.label ? `<span class="people-flabel">${escapeHtml(spec.label)}</span>` : '';
      if (spec.toggle) {
        const [v, text] = spec.options[0];
        return `<div class="people-frow people-frow-toggle" data-row="${spec.key}">${label}
          <div class="pills">${pill(spec.key, v, text, countOf(v), current === v)}</div></div>`;
      }
      const inTop = spec.options.some(([v]) => v === current);
      const pills = pill(spec.key, '', 'All', pool.length, current === '')
        + spec.options.map(([v, text]) => pill(spec.key, v, text, countOf(v), current === v)).join('');
      const more = spec.more
        ? `<select class="people-more-select" id="businesses-more-${escapeHtml(spec.key)}"
            aria-label="More ${escapeHtml(spec.label.toLowerCase())}">
            <option value=""${current === '' || inTop ? ' selected' : ''}>more…</option>${
          spec.more.map(([v, text]) => `<option value="${escapeHtml(v)}"${current === v ? ' selected' : ''}>${
            escapeHtml(text)} (${countOf(v)})</option>`).join('')}</select>`
        : '';
      return `<div class="people-frow" data-row="${spec.key}">${label}<div class="pills">${pills}${more}</div></div>`;
    };
    let html = '';
    let group = null;
    for (const spec of specs) {
      if (spec.group) {
        if (group !== spec.group) { if (group) html += '</div>'; html += `<div class="people-fgroup" data-group="${spec.group}">`; group = spec.group; }
      } else if (group) { html += '</div>'; group = null; }
      html += rowHtml(spec);
    }
    if (group) html += '</div>';
    filtersEl.innerHTML = html
      + `<button type="button" class="people-clear link" id="businesses-clear"${anyOn ? '' : ' hidden'}>Clear filters</button>`;
    for (const pills of filtersEl.querySelectorAll('.pills')) {
      const on = pills.querySelector('.pill[aria-pressed="true"]:not([data-value=""])');
      if (on && pills.scrollWidth > pills.clientWidth) {
        const left = on.getBoundingClientRect().left - pills.getBoundingClientRect().left + pills.scrollLeft;
        pills.scrollLeft = Math.max(0, left - 12);
      }
    }
    const active = Object.keys(state.filters).length;
    filtersEl.hidden = !state.filtersOpen;
    filtersToggle.setAttribute('aria-expanded', String(state.filtersOpen));
    filtersToggle.classList.toggle('is-active', active > 0);
    filtersToggle.innerHTML = `Filters${active ? ` <span class="pill-n">${active} on</span>` : ''}`;
  }

  filtersToggle.addEventListener('click', () => {
    state.filtersOpen = !state.filtersOpen;
    paintFilters();
    if (state.filtersOpen) filtersEl.querySelector('.pill')?.focus?.({ preventScroll: true });
  });
  compact?.addEventListener?.('change', (ev) => {
    state.filtersOpen = !ev.matches || Object.keys(state.filters).length > 0;
    paintFilters();
  });
  filtersEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('button.pill');
    if (btn) {
      const on = btn.getAttribute('aria-pressed') === 'true';
      setFilter(btn.dataset.filter, on && btn.dataset.value !== '' ? '' : btn.dataset.value);
      return;
    }
    if (ev.target.closest('#businesses-clear')) { state.filters = {}; paint(); }
  });
  filtersEl.addEventListener('change', (ev) => {
    const sel = ev.target.closest('select.people-more-select');
    if (sel) setFilter(sel.id.replace('businesses-more-', ''), sel.value);
  });

  function setFilter(key, value) {
    if (!specs.some((s) => s.key === key)) return;
    if (value === '' || value === null || value === undefined) delete state.filters[key];
    else state.filters[key] = String(value);
    paint();
  }

  // ---- the list --------------------------------------------------------- //

  /** The building's title as the town names it, so a premises reads "The Green
   *  Tree tavern" and not `green_tree_tavern`. */
  function buildingTitle(id) {
    const rec = registry?.get?.(id);
    return rec ? displayName(rec.sidecar, id).title : null;
  }

  function whereText(r) {
    const p = r.where;
    if (!p) return '';
    if (p.kind === 'premises' && p.structure_id) return buildingTitle(p.structure_id) || p.street || 'a roof of its own';
    if (p.street) return p.street;
    if (p.kind === 'anchored' && p.anchor) return `by ${p.anchor.title}`;
    return '';
  }

  /** The community label on a LIST row, printed only where the layer reads one —
   *  the same rule people.js uses, so a house and its keeper read alike. */
  function communityText(r) {
    const v = r.proprietor_community;
    if (!v || v === 'unknown') return '';
    return COMMUNITY_LABEL.get(v) || words(v);
  }

  function rowHtml(r) {
    const sub = [
      r.trade || (r.occupation ? words(r.occupation) : ''),
      communityText(r),
      whereText(r),
      r.opened ? `from ${String(r.opened).slice(0, 4)}` : '',
    ].filter(Boolean).join(' · ');
    const kind = r.where?.kind;
    const mark = kind && kind !== 'premises'
      ? `<span class="person-mark mark-${escapeHtml(kind)}" title="${escapeHtml(PLACE[kind]?.[1] || '')}">${
        escapeHtml(PLACE[kind]?.[0] || words(kind))}</span>`
      : '';
    return `<button type="button" class="person-row" role="option" data-business-id="${escapeHtml(r.id)}"
        aria-selected="false">
      <i class="grade-dot grade-${escapeHtml(r.grade)}" title="${escapeHtml(r.grade)}: ${
        escapeHtml(GRADE_TITLE[r.grade] || GRADE_TITLE.inferred)}"></i>
      <span class="person-main"><span class="person-name">${escapeHtml(r.name)}</span>${
        sub ? `<small class="person-sub">${escapeHtml(sub)}</small>` : ''}</span>${mark}</button>`;
  }

  let current = [];
  function paintList() {
    current = matches();
    state.matched = current.length;
    resultsEl.innerHTML = current.length
      ? current.map(rowHtml).join('')
      : `<p class="people-empty">No firm by that name. Try a trade — "tailor", "forwarding" — or a good
         the papers advertised, like "crockery". ${n((counts.by_where_kind || {}).unplaceable)} of these
         houses are known from a printing and nothing else, so a street will not find them.</p>`;
    const narrowing = state.q.trim() || Object.keys(state.filters).length;
    noteEl.textContent = narrowing
      ? `${n(current.length)} of ${n(rows.length)} firms${state.q.trim() ? ` match “${state.q.trim()}”` : ''}`
      : `Every firm the record knows, by name. ${n(rows.length)} of them.`;
  }

  function paint() { paintFilters(); paintList(); }

  let typing = 0;
  input.addEventListener('input', () => {
    clearTimeout(typing);
    typing = setTimeout(() => { state.q = input.value; paint(); }, 60);
  });
  input.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowDown') { ev.preventDefault(); resultsEl.querySelector('.person-row')?.focus(); }
    if (ev.key === 'Enter') { const first = resultsEl.querySelector('.person-row'); if (first) open(first.dataset.businessId); }
  });
  resultsEl.addEventListener('keydown', (ev) => {
    const row = ev.target.closest('.person-row');
    if (!row) return;
    if (ev.key === 'ArrowDown') { ev.preventDefault(); row.nextElementSibling?.focus?.(); }
    if (ev.key === 'ArrowUp') { ev.preventDefault(); (row.previousElementSibling || input).focus(); }
  });
  resultsEl.addEventListener('click', (ev) => {
    const row = ev.target.closest('.person-row');
    if (row) open(row.dataset.businessId);
  });

  // ---- the business card ------------------------------------------------ //

  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };

  /** One dated location, in the ladder's own words. A premises offers the way to
   *  it; everything below a premises prints the limit the record states, because
   *  the limit is the finding. */
  function locationHtml(loc) {
    const kind = loc.kind || 'unplaceable';
    const [label, why] = PLACE[kind] || [words(kind), ''];
    const title = loc.structure_id ? buildingTitle(loc.structure_id) : null;
    // The anchor is the landmark, never the house's own roof, so it is read off
    // `anchor` and the `go` button below still keys on `structure_id` alone.
    const anchor = kind === 'anchored' ? loc.anchor : null;
    const where = kind === 'premises' && title ? title
      : anchor ? `by ${anchor.title}`
        : loc.street_id ? words(loc.street_id) : 'nowhere the register could name';
    const dates = loc.from || loc.to
      ? `<span class="biz-when">${escapeHtml(day(loc.from))} – ${loc.to ? escapeHtml(day(loc.to)) : 'no close recorded'}</span>`
      : '';
    // Three ways out of a location, and only the first two are a place on the ground:
    // its own roof, the roof it stands against, or the card of the firm it stands
    // against. A corner anchor offers none — two streets are not somewhere to stand.
    const landmark = anchor?.kind === 'structure' ? anchor.id : null;
    const goTo = loc.structure_id || landmark;
    const go = goTo && registry?.has?.(goTo)
      ? `<button type="button" class="people-go biz-go" data-structure="${escapeHtml(goTo)}">
          <span class="people-go-verb">Go to ${loc.structure_id ? 'the premises' : 'the landmark'}</span>
          <span class="people-go-title">${escapeHtml(title || anchor?.title || words(goTo))}</span></button>`
      : anchor?.kind === 'business'
        ? `<button type="button" class="link biz-anchor-firm" data-business="${escapeHtml(anchor.id)}">
            The house it stands by: ${escapeHtml(anchor.title)}</button>`
        : '';
    return `<li class="biz-loc${loc.primary ? ' is-primary' : ''}">
      <p class="biz-loc-head"><i class="grade-dot grade-${escapeHtml(loc.tier || 'inferred')}"></i>
        <b>${escapeHtml(where)}</b>
        <span class="person-mark mark-${escapeHtml(kind)}" title="${escapeHtml(why)}">${escapeHtml(label)}</span>${
      loc.primary ? '<span class="biz-primary">principal</span>' : ''}</p>
      ${dates}
      ${loc.basis ? `<p class="legend-note">${escapeHtml(loc.basis)}</p>` : ''}
      ${loc.limit_reason ? `<p class="legend-note biz-limit">How far the record goes: ${escapeHtml(loc.limit_reason)}</p>` : ''}
      ${go}</li>`;
  }

  /** One person the record names. The link is offered only where the town holds a
   *  card for them — 144 of 196 — and the rest are named without one, which is
   *  itself a reading: the register printed a name the resident layer never met.
   *
   *  A man the paper printed under two styles is ONE partner here (T-1401 folds
   *  them on `person_id` in the data), and the styles he was printed under are
   *  shown beside him rather than dropped: the typography is the evidence that the
   *  fold was a fold and not a deletion. */
  function personHtml(p) {
    const dates = p.from ? ` <span class="biz-when">${escapeHtml(day(p.from))}${p.to ? ` – ${escapeHtml(day(p.to))}` : ''}</span>` : '';
    const name = p.person_id && onPerson
      ? `<button type="button" class="link biz-person" data-person="${escapeHtml(p.person_id)}">${escapeHtml(p.name || p.person_id)}</button>`
      : `<b>${escapeHtml(p.name || 'unnamed')}</b>`;
    // THE STANDING AND THE TRADE ARE TWO WORDS AND THE CARD PRINTS BOTH (T-1462). `role`
    // is what this person IS at the house — a journeyman, a servant, a clerk — and
    // `occupation` is the trade they work there. One without the other reads as half a
    // row: "journeyman" of what, or "baker" on whose account.
    const trade = p.occupation && p.occupation !== p.role
      ? ` <span class="biz-role">${escapeHtml(words(p.occupation))}</span>` : '';
    // A DRAWN HAND SAYS IT WAS DRAWN, and hands a reader the seed that drew it. The
    // grade dot alone is a claim; the seed is what makes it unpickable, which is the
    // same bargain "Why this house is here" strikes for a reconstructed firm.
    const seed = p.tier === 'reconstructed' && p.seed
      ? `<span class="biz-drawn" title="${escapeHtml(p.replaceable_by || 'a source naming who worked here')}">drawn · <code>${escapeHtml(p.seed)}</code></span>`
      : '';
    return `<li><i class="grade-dot grade-${escapeHtml(p.tier || 'inferred')}" title="${escapeHtml(p.tier || '')}"></i>
      ${name} <span class="biz-role">${escapeHtml(words(p.role || 'proprietor'))}</span>${trade}${dates}${
      p.person_id ? '' : '<span class="person-mark mark-unplaceable" title="The register prints this name and the resident layer holds no card for it">no town card</span>'}${seed}${
      (p.also_printed_as || []).length
        ? `<span class="biz-styles" title="The same person, printed another way in the same papers">also printed ${
          p.also_printed_as.map((s) => escapeHtml(s)).join(', ')}</span>` : ''}</li>`;
  }

  /** WHO WORKED THERE, AND WHAT THE HOUSE STILL WANTS (T-1462). The keepers are the
   *  register's own reading and they have their own heading above; this is the other
   *  half of the house — the hands a source names, and the hands T-1433's seating drew
   *  where the town had a person of the trade and nowhere to follow it.
   *
   *  THE SHORTFALL PRINTS WHETHER OR NOT ANYBODY IS SEATED, and that is the point of it.
   *  A house carrying one of the two hands its class wants and a house carrying both
   *  printed exactly the same card until this block: a reader had to hold the staffing
   *  model in their head and subtract. Now the house says it, in the model's own numbers
   *  and in a sentence, and an undrawn hand names who would have to print one first. */
  function staffingHtml(staff, block) {
    if (!staff.length && !block) return '';
    const short = block && block.shortfall;
    const undrawn = ((block && block.hands) || []).filter((h) => !h.drawn);
    return `<h4 class="people-card-h">Who worked there</h4>
      ${staff.length
    ? `<ul class="biz-people">${staff.map(personHtml).join('')}</ul>`
    : '<p class="legend-note">No hand of this house is named or seated.</p>'}
      ${short ? `<p class="legend-note biz-shortfall${short.short_by > 0 ? ' biz-short' : ''}">${
    escapeHtml(short.statement)}</p>` : ''}
      ${undrawn.length
    ? `<ul class="biz-claims">${undrawn.map((h) => `<li>${
      escapeHtml(words(h.occupation || h.role))} <span class="biz-role">${
      escapeHtml(words(h.household_relationship))}</span> — ${
      escapeHtml(h.why_not_drawn || 'nobody has named one')}</li>`).join('')}</ul>`
    : ''}`;
  }

  /** What community the house is read as, and the whole of what it was read off.
   *  A silence prints too, and says WHICH silence it was: the register named nobody the
   *  town cards, or it named them and the resident layer knows no community for them. */
  function communityHtml(block) {
    if (!block || typeof block !== 'object') return '';
    const label = block.value === 'unknown' ? 'Not read'
      : (COMMUNITY_LABEL.get(block.value) || words(block.value));
    const people = (block.from || []).map((f) => `<li>
      <i class="grade-dot grade-${escapeHtml(f.tier || 'reconstructed')}" title="${escapeHtml(f.tier || '')}"></i>
      ${escapeHtml(f.name || f.person_id)} <span class="biz-role">${
  escapeHtml(COMMUNITY_LABEL.get(f.community) || words(f.community))}</span></li>`).join('');
    return `<h4 class="people-card-h">The community it is read as</h4>
      <p class="biz-dates">${block.tier ? `<i class="grade-dot grade-${escapeHtml(block.tier)}"></i>` : ''}
        <b>${escapeHtml(label)}</b>${block.tier ? ` <span class="biz-role">${escapeHtml(block.tier)}</span>` : ''}</p>
      <p class="legend-note">${escapeHtml(block.basis || '')}</p>
      ${people ? `<ul class="biz-people">${people}</ul>` : ''}`;
  }

  /** WHY A HOUSE NOBODY NAMED IS IN THE TOWN (T-1184). A reconstructed firm has no
   *  printings to show — that is the whole of what makes it reconstructed — so the card
   *  prints its ORDER instead: the census line that counts more of its class than the
   *  register holds, the bucket of the reconstruction order book that bought it, the seed
   *  a reader can retype to redraw its style and its face, and what retires it. A grade
   *  dot a reader cannot unpick is a claim; this is the unpicking. */
  function reconstructionHtml(block) {
    if (!block || typeof block !== 'object') return '';
    const basis = block.basis || {};
    return `<h4 class="people-card-h">Why this house is here</h4>
      <p class="legend-note biz-invented"><b>Nobody named this firm.</b> It stands in the town
        because a count the town demonstrably needed was short, and it is written down as an
        invention rather than as a finding.</p>
      ${basis.note ? `<p class="legend-note">${escapeHtml(basis.note)}</p>` : ''}
      <ul class="biz-claims">
        <li>ordered by <code>${escapeHtml(block.bucket || '')}</code> of the 1835 reconstruction order book</li>
        <li>written by <code>${escapeHtml(block.group || '')}</code> (${escapeHtml(block.ticket || '')})</li>
        <li>redraw it from the seed <code>${escapeHtml(block.seed || '')}</code></li>
      </ul>
      ${block.withdrawn_if ? `<p class="legend-note">Withdrawn if ${escapeHtml(block.withdrawn_if)}.</p>` : ''}`;
  }

  function recordHtml(rec, row) {
    // THE KEEPERS AND THE HANDS ARE TWO READINGS AND THE CARD KEEPS THEM APART (T-1462).
    // A proprietor is what the paper printed; a hand is what a later source attested or
    // what the staffing model seated. Folding all three lists into one "Who kept it"
    // made a drawn journeyman read like a named owner at a glance, which is exactly the
    // conflation the grade dot exists to prevent.
    const people = [
      ...(rec.proprietors || []).map((p) => ({ ...p, role: p.role || 'proprietor' })),
      ...(rec.partners || []).map((p) => ({ ...p, role: p.role || 'partner' })),
    ];
    const staff = (rec.staff || []).map((p) => ({ ...p, role: p.role || 'staff' }));
    const liberties = Object.entries(rec.liberties || {}).filter(([, on]) => on);
    const ev = rec.evidence || {};
    return [
      people.length
        ? `<h4 class="people-card-h">Who kept it</h4><ul class="biz-people">${people.map(personHtml).join('')}</ul>`
        : '<h4 class="people-card-h">Who kept it</h4><p class="legend-note">The printings name nobody. '
          + 'A house with no keeper on its record is a reading about the register, not about the town.</p>',
      staffingHtml(staff, rec.staffing),
      communityHtml(rec.proprietor_community),
      `<h4 class="people-card-h">Where it stood</h4><ul class="biz-locs">${
        (rec.locations || []).map(locationHtml).join('') || '<li class="legend-note">No location on the record.</li>'}</ul>
       <div class="biz-seat-slot"></div>`,
      `<h4 class="people-card-h">When</h4>
       <p class="biz-dates"><i class="grade-dot grade-${escapeHtml(rec.dates?.tier || 'inferred')}"></i>
         opened ${escapeHtml(day(rec.dates?.opened))} · closed ${rec.dates?.closed ? escapeHtml(day(rec.dates.closed)) : 'no close recorded'}${
  rec.dates?.precision ? ` <span class="biz-role">${escapeHtml(words(rec.dates.precision))}</span>` : ''}</p>
       ${rec.dates?.basis ? `<p class="legend-note">${escapeHtml(rec.dates.basis)}</p>` : ''}`,
      (rec.goods || []).length
        ? `<h4 class="people-card-h">What it sold</h4><p class="biz-goods">${
          rec.goods.map((g) => `<span class="biz-good">${escapeHtml(g)}</span>`).join('')}</p>`
        : '',
      // The printings, OR the order — never both, and never neither. A reconstructed
      // house has no first issue and no last, and a card that printed 'First printed —'
      // over one would be offering a silence as a date.
      rec.reconstruction
        ? reconstructionHtml(rec.reconstruction)
        : `<h4 class="people-card-h">The printings that attest it</h4>
       <p class="legend-note">First printed ${escapeHtml(day(ev.first_issue))}, last ${escapeHtml(day(ev.last_issue))}${
  (rec.claim_ids || []).length ? ` · ${n(rec.claim_ids.length)} claim${rec.claim_ids.length === 1 ? '' : 's'}` : ''}.</p>
       ${(rec.claim_ids || []).length ? `<ul class="biz-claims">${rec.claim_ids.map((c) => `<li><code>${escapeHtml(c)}</code></li>`).join('')}</ul>` : ''}`,
      liberties.length
        ? `<h4 class="people-card-h">What we made up</h4><ul class="biz-liberties">${
          liberties.map(([k]) => `<li>${escapeHtml(LIBERTY[k] || words(k))}</li>`).join('')}</ul>`
        : '',
      rec.replaceable_by
        ? `<h4 class="people-card-h">What would replace this</h4><p class="legend-note">${escapeHtml(rec.replaceable_by)}</p>`
        : '',
      row.review_required
        ? '<p class="legend-note biz-review">This record is marked for review before the scene is released.</p>'
        : '',
    ].filter(Boolean).join('');
  }

  let openSeq = 0;
  /** Open a firm's card in place of the list. Resolves true once the record has
   *  been fetched and rendered (or its failure written), so a harness can await it. */
  async function open(id) {
    const r = byId.get(id);
    if (!r) return false;
    const seq = ++openSeq;
    state.open = id;
    const kind = r.where?.kind;
    cardEl.innerHTML = `
      <button type="button" class="people-back" id="businesses-back">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>
        All businesses</button>
      <h3 class="people-card-name">${escapeHtml(r.name)}</h3>
      <p class="people-card-meta">
        <i class="grade-dot grade-${escapeHtml(r.grade)}"></i>${escapeHtml(r.grade)}${
  kind ? ` · <span class="person-mark mark-${escapeHtml(kind)}">${escapeHtml(PLACE[kind]?.[0] || words(kind))}</span>` : ''}${
  r.present_at_scene_date ? '' : ' · <span class="person-mark mark-unplaceable">not trading on 1 July</span>'}
        <br><span class="people-card-hh">${escapeHtml(r.trade || r.type.map((t) => words(t)).join(', '))}</span>
      </p>
      <p class="people-card-what">${escapeHtml(GRADE_TITLE[r.grade] || '')}.</p>
      <div class="people-card-body" aria-busy="true"><p class="legend-note">Loading the business record…</p></div>`;
    home.hidden = true;
    cardEl.hidden = false;
    section?.classList.add('people-card-open');
    if (typeof onTitle === 'function') onTitle(r.name, () => { state.lastOpened = state.open; close(); });
    mount.closest('.panel-scroll')?.scrollTo?.(0, 0);
    cardEl.querySelector('.people-back')?.focus?.({ preventScroll: true });

    const body = cardEl.querySelector('.people-card-body');
    try {
      const rec = await getJson(`businesses/${r.file}`);
      if (seq !== openSeq) return false;
      body.innerHTML = recordHtml(rec, r);
      // T-1493. THE SEAT, AND THE WAY TO IT. The record's own locations reach a
      // roof for 45 of these 179 firms; the address book seats 40 more on a block
      // face of the street the paper names, and until now the card printed that
      // street and offered nowhere to stand. The seat block goes in only where the
      // locations above it offered NOTHING — a firm with premises already has its
      // button, and two would read as two addresses.
      //
      // Awaited AFTER the record is painted, the way the person card does it: the
      // join is megabytes and the card must not wait on it. A firm whose row the
      // book has no seat for (the 62 unplaceable, the 32 owed) gets nothing here,
      // which is the honest answer and not a degradation.
      state.seatPending = seatSlot(cardEl, r).catch(() => {});
    } catch (err) {
      if (seq !== openSeq) return false;
      problems.push(`businesses: ${err.message} — one business record is missing`);
      body.innerHTML = `<p class="legend-note">This firm's record could not be loaded. It is committed at
        <code>data/businesses/${escapeHtml(r.file || '')}</code>.</p>`;
    } finally {
      if (seq === openSeq) body.removeAttribute('aria-busy');
    }
    return true;
  }

  /** Fill the card's seat slot from the address book, once the join settles.
   *  Keyed on `register_id`, the crosswalk `compile_businesses.py` commits
   *  between a business record (`biz_*`) and the register row the address book
   *  files it under (`business_*`); nothing here invents that mapping. */
  async function seatSlot(card, r) {
    if (!r.register_id) return;
    const joins = await loadResidentJoins(dataBase, sceneId, problems);
    const row = joins.seatByBusiness?.get(r.register_id);
    const slot = card.querySelector('.biz-seat-slot');
    if (!row || !slot || card.hidden) return;
    const target = seatTarget(row);
    const offered = !!card.querySelector('.biz-locs .biz-go');
    const goable = !offered && !!target && !!registry?.has?.(target.id);
    if (!goable && row.rung === 'structure') return; // the premises button already said it
    slot.innerHTML = seatHtml(row, {
      goable,
      title: goable ? (buildingTitle(target.id) || words(target.id)) : null,
    });
  }

  function close() {
    state.open = null;
    cardEl.hidden = true;
    cardEl.innerHTML = '';
    home.hidden = false;
    section?.classList.remove('people-card-open');
    if (typeof onTitle === 'function') onTitle(null);
    paintList();
    const row = resultsEl.querySelector(`.person-row[data-business-id="${CSS.escape(state.lastOpened || '')}"]`);
    (row || input)?.focus?.({ preventScroll: true });
  }

  cardEl.addEventListener('click', (ev) => {
    if (ev.target.closest('.people-back')) { state.lastOpened = state.open; close(); return; }
    const go = ev.target.closest('.biz-go');
    if (go) { onGoTo?.({ kind: 'structure', id: go.dataset.structure }); return; }
    // A house anchored against ANOTHER HOUSE — seven of the 26 — opens that one's
    // card, which is the only way out this location has: the landmark is a firm and
    // not a roof, so there is nowhere on the ground to send the visitor.
    const firm = ev.target.closest('.biz-anchor-firm');
    if (firm) { open(firm.dataset.business); return; }
    const person = ev.target.closest('.biz-person');
    if (person) onPerson?.(person.dataset.person);
  });

  paint();

  return {
    businesses: rows.length,
    error: null,
    /** Resolves when the open card's address-book seat has been filled in — the
     *  fetch is deliberately NOT awaited by `open`, so the harness needs a handle
     *  on it to assert about the seat block (T-1493). */
    seated: () => state.seatPending || Promise.resolve(),
    search(q) { input.value = String(q ?? ''); state.q = input.value; paint(); return state.matched; },
    open,
    close,
    filter(key, value) { setFilter(key, value); return state.matched; },
    showFilters(on = true) { state.filtersOpen = !!on; paintFilters(); },
    results() { return current.map((r) => r.id); },
    get state() { return { ...state, filters: { ...state.filters } }; },
  };
}
