/**
 * people.js — the People section of the drawer: a directory of everyone in the town.
 *
 * The household browser (`residents.js`) is organised the way the DATA is —
 * 1,380 household records, a letter-list cohort held apart, a vocabulary, the
 * researched-and-not-resident list — and it is the right shape for reading the
 * research. It is the wrong shape for the question a visitor actually walks in
 * with, which is a name. "Was there a Beaubien?" is a directory question, and a
 * directory is one row a PERSON, sorted by surname, that narrows as you type.
 *
 * So this reads `sidecars/<scene>/people.json`, which `tools/compile_scene.py
 * compile_people` flattens from the household records — one row a person, with
 * the fields a list needs to sort, filter and label and a pointer at the record
 * it came from. The record itself is fetched the first time a person's card is
 * opened and rendered with `householdHtml` from residents.js, the same function
 * the household browser uses: two sections, one rendering of a record, so a card
 * cannot say something its record does not.
 *
 * WHAT THE FILTERS ARE FOR. The owner's ruling of 30 August 2026 let every name
 * on a post-office letter list into the town, and 727 of these 1,404 people are
 * a name on such a list and nothing else — no trade, no street, no household.
 * A directory that mixed them in silently would be *"a wall of undifferentiated
 * people"*, which the ruling said would mean it had been implemented badly. So
 * the "How known" row is the first thing a visitor can narrow by, every row of
 * the list carries a mark saying which kind of person it is, and the counts on
 * the pills say how much of the town each kind is before anything is tapped.
 * The counts are read off the compiled rows, never typed.
 *
 * Nothing here is virtualised. 1,404 rows at 44 px is a list a browser paints
 * without complaint, but a drawer 440 px wide does not want 62,000 px of it, so
 * the list renders in pages of 80 with a "Show 80 more" button — cheaper than a
 * scroll listener and honest about how many are left.
 *
 * Contract (main.js): `mountPeople({ mount, people, registry, dataBase, sceneId,
 * onGoTo, problems })` → `{ people, error, search, open, close, filter, state }`.
 * `mount` is `#people-directory`, the first child of the People section; the
 * household browser's mounts (`#residents-note`, `#residents`) sit below it
 * untouched, under "Browse by household".
 */

import { escapeHtml } from './citations.js';
import { displayName } from './display-name.js';
import { householdHtml, loadResidentJoins, words } from './residents.js';

const PAGE = 80;

/** Diacritics folded, lower-cased, one space between words: the shape both the
 *  search box and the row's search text are reduced to, so "Beaubien" and
 *  "béaubien" meet. */
function fold(s) {
  return String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim();
}

/** `1,404` — the count line's numbers, in the locale's own grouping. */
function n(x) {
  return Number(x || 0).toLocaleString('en-GB');
}

/** How a row is known, in the words the mark and the card use. */
const KNOWN_LABEL = {
  documented: 'documented',
  letter_list: 'letter list',
  civic_mint: 'civic record',
  projected: 'projected',
};
const KNOWN_TITLE = {
  documented: 'Named by a source outside the post-office lists and the civic-list consolidation',
  letter_list: 'Known only from the post office’s lists of uncalled-for letters — a name, and nothing else',
  civic_mint: 'Minted by the evidence consolidation from a poll, tax or muster list, or a contemporary paper',
  projected: 'A projected resident: documented once or twice and placed by nothing',
};

/** The "Arrived" row's buckets. `arrival_year` is a bound for 1,318 of the 1,380
 *  households ("here by 1834", not "came 1834"), so the pill is a year and the
 *  row's own text says which kind of year it is. */
const ARRIVED = [
  ['pre1831', '1830 and earlier', (y) => y !== null && y <= 1830],
  ['1831', '1831', (y) => y === 1831],
  ['1832', '1832', (y) => y === 1832],
  ['1833', '1833', (y) => y === 1833],
  ['1834', '1834', (y) => y === 1834],
  ['1835', '1835', (y) => y === 1835],
];

/** The "How known" row's predicates — flags, not one exclusive word, because 85
 *  civic-mint people also carry the projected subtype and a filter that hid
 *  that overlap would be lying about the ladder. */
const KNOWN = {
  documented: (r) => !r.letter_list_only && !r.civic_mint && r.resident_subtype !== 'projected_resident',
  letter_list: (r) => !!r.letter_list_only,
  civic_mint: (r) => !!r.civic_mint,
  projected: (r) => r.resident_subtype === 'projected_resident',
};

/**
 * The filter rows, each a predicate factory: `test(value)` returns a row test.
 * Declared as data so the count-per-pill pass can run every row against every
 * OTHER row's filter without special-casing any of them.
 */
/** The three answers the roles filter offers, read off the compiled counts. */
const ROLE_FILTERS = {
  at_scene: (r) => (r.roles_at_scene_date || 0) > 0,
  off_scene: (r) => (r.roles || 0) > 0 && !(r.roles_at_scene_date || 0),
  none: (r) => !(r.roles || 0),
};

function filterSpecs(people) {
  const occCounts = new Map((people.vocabulary?.occupations || []).map((o) => [o.value, o.count]));
  const topTrades = [...occCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 10).map(([v]) => v);
  const grades = (people.vocabulary?.grades || []).filter((g) => (people.counts?.by_grade || {})[g] > 0);
  return [
    {
      key: 'occupation', label: 'Trade',
      options: topTrades.map((v) => [v, words(v)]),
      more: [...occCounts.keys()].sort().map((v) => [v, words(v)]),
      test: (v) => (r) => r.occupation === v,
    },
    {
      key: 'division', label: 'Division',
      options: (people.vocabulary?.divisions || []).map((v) => [v, words(v)]),
      test: (v) => (r) => r.division === v,
    },
    {
      key: 'arrived', label: 'Arrived',
      options: ARRIVED.map(([v, label]) => [v, label]),
      test: (v) => { const spec = ARRIVED.find((a) => a[0] === v); return (r) => !!spec && spec[2](r.arrival_year ?? null); },
    },
    {
      key: 'known', label: 'How known',
      options: [['documented', 'documented'], ['letter_list', 'letter list only'],
        ['civic_mint', 'civic record'], ['projected', 'projected resident']],
      test: (v) => KNOWN[v] || (() => false),
    },
    // The three short questions share one line (`group`): two or three pills
    // each, and a row apiece would cost the list three lines of the drawer.
    {
      key: 'present', label: 'Here on 1 July', group: 'facts',
      options: (people.vocabulary?.presence || []).filter((p) => (people.counts?.by_presence || {})[p] > 0)
        .map((v) => [v, words(v)]),
      test: (v) => (r) => r.present === v,
    },
    {
      key: 'grade', label: 'Grade', group: 'facts',
      options: grades.map((v) => [v, v]),
      test: (v) => (r) => r.grade === v,
    },
    {
      key: 'address', label: '', toggle: true, group: 'facts',
      options: [['yes', 'Has an address']],
      test: () => (r) => !!(r.lives_at || r.works_at),
    },
    // The dated roles, as the one question the plural field makes askable (T-1255):
    // who the sources word at the scene date, and who they word only in another
    // year. The second pill is the whole reason the field went plural — 135 people
    // hold a role and none of it reaches 1 July 1835, and the singular `occupation`
    // view showed them as having no trade.
    {
      key: 'roles', label: 'Dated roles',
      options: [['at_scene', 'a role on 1 July 1835'], ['off_scene', 'only in another year'],
        ['none', 'no role recorded']],
      test: (v) => ROLE_FILTERS[v] || (() => false),
    },
  ];
}

/**
 * Mount the directory into `mount`.
 *
 * @param {object} o
 * @param {HTMLElement|null} o.mount      `#people-directory`
 * @param {object|null} o.people          the compiled `people.json`, or null when it did not load
 * @param {Map} o.registry                loaded structures by id (`{ sidecar }`), for the Go-to titles
 * @param {URL} o.dataBase                where data/ lives
 * @param {string} o.sceneId              which scene's citation join to read
 * @param {(target: object) => void} o.onGoTo   travel to a person's building
 * @param {(text: string|null, onBack?: Function) => void} [o.onTitle]
 *   the drawer head's title hook (hud.setTitle), when the lead passes one: the
 *   open card puts the person's name in the head with a back arrow, and the
 *   card's own back button steps aside (`has-head-back` on the section)
 * @param {string[]} [o.problems]         the shared collector
 */
export async function mountPeople({
  mount, people, registry, dataBase, sceneId, onGoTo, onTitle = null, problems = [],
} = {}) {
  const idle = { search() {}, open() { return Promise.resolve(false); }, close() {}, filter() {}, get state() { return null; } };
  if (!mount) return { people: 0, error: 'no mount', ...idle };
  if (!people || !Array.isArray(people.people)) {
    // An honest note, not an empty list: the household browser below still works.
    mount.innerHTML = '<p class="legend-note" id="people-note">The people directory did not load '
      + `(<code>sidecars/${escapeHtml(String(sceneId))}/people.json</code>). The town's households `
      + 'are still listed below.</p>';
    return { people: 0, error: 'people.json missing', ...idle };
  }

  const section = mount.closest('.panel-body');
  if (typeof onTitle === 'function') section?.classList.add('has-head-back');
  const getJson = async (rel) => {
    const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
    return res.json();
  };
  // The citation join on its own — 159 records, a few kilobytes — so a card can
  // quote its sources the moment the household record arrives rather than after
  // the megabyte of directory crosswalks that `loadResidentJoins` also carries.
  let citationsPromise = null;
  const citations = () => {
    citationsPromise ??= getJson(`sidecars/${sceneId}/residents_sources.json`)
      .then((joined) => new Map(Object.entries(joined.citations || {})))
      .catch((err) => { problems.push(`people: ${err.message} — person cards are shown without their citations`); return new Map(); });
    return citationsPromise;
  };
  const rows = people.people.map((r) => ({
    ...r,
    _name: fold(r.name),
    _words: fold(r.name).split(' '),
    // Both wordings of every role (T-1255): the controlled word where the source's
    // wording has been adjudicated into the vocabulary and the wording AS PRINTED
    // where it has not. A visitor who types "brickmaker" is typing what a directory
    // printed, and before this the search could only match the one trade the
    // singular `occupation` view carried for 1 July 1835 — so 135 people whose every
    // role falls outside the scene window were unfindable by any trade at all.
    _text: fold([r.name, r.household_name, r.occupation ? words(r.occupation) : '',
      ...(r.role_words || []).map((w) => words(w)),
      r.division ? words(r.division) : '', r.relationship ? words(r.relationship) : ''].join(' ')),
  }));
  const byId = new Map(rows.map((r) => [r.id, r]));
  const counts = people.counts || {};
  const specs = filterSpecs(people);

  // On a phone the seven filter rows would sit between the search box and the
  // first row of the list, so they start folded there and open on demand; a
  // desktop drawer shows them always. The count on the toggle says how many
  // are active while folded.
  const compact = typeof matchMedia === 'function' ? matchMedia('(max-width: 620px)') : null;
  const state = {
    q: '',
    filters: {}, // key -> value (single-select per row; the address toggle is 'yes')
    shown: PAGE,
    open: null,
    matched: 0,
    filtersOpen: !(compact && compact.matches),
  };

  // ---- markup ----------------------------------------------------------- //

  mount.innerHTML = `
    <div class="people-home">
      <p class="people-count" id="people-count">${n(counts.people)} people in ${n(counts.households)} households
        · ${n(counts.letter_list_only)} known only from the letter lists
        · ${n(counts.with_address)} with a known address</p>
      <div class="field people-field">
        <input type="search" id="people-search" placeholder="A name, a surname, a trade…"
          autocomplete="off" spellcheck="false" aria-label="Search the people of the town"
          aria-controls="people-results">
      </div>
      <div class="people-toolbar">
        <button type="button" class="pill people-filters-toggle" id="people-filters-toggle"
          aria-expanded="false" aria-controls="people-filters">Filters</button>
      </div>
      <div id="people-filters" class="people-filters"></div>
      <p class="people-note" id="people-result-note" aria-live="polite"></p>
      <div id="people-results" class="people-results" role="listbox" aria-label="People"></div>
      <button type="button" class="people-more" id="people-more" hidden></button>
    </div>
    <div id="people-card" class="people-card" hidden></div>`;

  const $ = (sel) => mount.querySelector(sel);
  const home = $('.people-home');
  const input = $('#people-search');
  const filtersEl = $('#people-filters');
  const filtersToggle = $('#people-filters-toggle');
  const noteEl = $('#people-result-note');
  const resultsEl = $('#people-results');
  const moreBtn = $('#people-more');
  const cardEl = $('#people-card');

  // ---- filtering -------------------------------------------------------- //

  /** The row tests currently active, keyed by filter, so the per-pill counts can
   *  drop one at a time. */
  function activeTests(except = null) {
    const tests = [];
    for (const spec of specs) {
      const v = state.filters[spec.key];
      if (v === undefined || v === null || v === '' || spec.key === except) continue;
      tests.push(spec.test(v));
    }
    return tests;
  }

  /** Search: every typed word must appear in the row's text. Ranked so a name
   *  that starts with the query beats one that merely contains it. */
  function searchRank(r, q, qWords) {
    if (!q) return 0;
    for (const w of qWords) if (!r._text.includes(w)) return -1;
    if (r._name.startsWith(q)) return 0;
    if (r._words.some((w) => w.startsWith(q))) return 1;
    if (r._name.includes(q)) return 2;
    if (r._words.some((w) => qWords.some((qw) => w.startsWith(qw)))) return 3;
    return 4;
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
    if (q) out.sort((a, b) => a[0] - b[0]); // stable: surname order survives within a rank
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
      // Counts on this row's pills reflect every OTHER filter and the search, so
      // a pill says how many rows tapping it would leave.
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
        ? `<select class="people-more-select" id="people-occupation" aria-label="More trades">
            <option value=""${current === '' || inTop ? ' selected' : ''}>more trades…</option>${
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
      + `<button type="button" class="people-clear link" id="people-clear"${anyOn ? '' : ' hidden'}>Clear filters</button>`;
    // A row scrolls sideways, so the pill a visitor chose must not be off its edge.
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
    // Widen to a desktop and the rows unfold; narrow to a phone and they fold
    // unless a filter is on, which a visitor would then lose sight of.
    state.filtersOpen = !ev.matches || Object.keys(state.filters).length > 0;
    paintFilters();
  });

  filtersEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('button.pill');
    if (btn) {
      const key = btn.dataset.filter;
      const v = btn.dataset.value;
      const on = btn.getAttribute('aria-pressed') === 'true';
      setFilter(key, on && v !== '' ? '' : v);
      return;
    }
    if (ev.target.closest('#people-clear')) {
      state.filters = {};
      state.shown = PAGE;
      paint();
    }
  });
  filtersEl.addEventListener('change', (ev) => {
    const sel = ev.target.closest('select#people-occupation');
    if (sel) setFilter('occupation', sel.value);
  });

  function setFilter(key, value) {
    if (!specs.some((s) => s.key === key)) return;
    if (value === '' || value === null || value === undefined) delete state.filters[key];
    else state.filters[key] = String(value);
    state.shown = PAGE;
    paint();
  }

  // ---- the list --------------------------------------------------------- //

  function arrivalText(r) {
    if (!r.arrival_year) return '';
    return r.arrival_precision === 'not_later_than' ? `here by ${r.arrival_year}` : `came ${r.arrival_year}`;
  }

  /**
   * The trade on a LIST row (T-1255). `occupation` is the generated view of the
   * roles that cover 1 July 1835, so where it is null the row said nothing about
   * a trade even when the record holds one — 135 people whose every dated role
   * falls outside the scene window read as trade-less. Those get their earliest
   * role word and its year instead, with the year doing the marking: "brickmaker
   * 1839" is visibly not a claim about the scene date, and the card's timeline
   * says so in words.
   */
  function tradeText(r) {
    if (r.occupation) return words(r.occupation);
    const off = (r.role_labels || []).find((l) => l.word);
    if (!off) return '';
    return off.year ? `${words(off.word)} ${off.year}` : words(off.word);
  }

  function rowHtml(r) {
    const sub = [
      tradeText(r),
      r.division ? `${words(r.division)}${r.division === 'unplaced' ? '' : ' division'}` : '',
      arrivalText(r),
    ].filter(Boolean).join(' · ');
    const mark = r.how_known !== 'documented'
      ? `<span class="person-mark mark-${escapeHtml(r.how_known)}" title="${escapeHtml(KNOWN_TITLE[r.how_known] || '')}">${
        escapeHtml(KNOWN_LABEL[r.how_known] || words(r.how_known))}</span>`
      : '';
    return `<button type="button" class="person-row" role="option" data-person-id="${escapeHtml(r.id)}"
        data-household="${escapeHtml(r.household)}" aria-selected="false">
      <i class="grade-dot grade-${escapeHtml(r.grade)}" title="${escapeHtml(r.grade)}: ${
        r.grade === 'attested' ? 'a source names this person in Chicago at the scene date'
          : 'a real named person reasonably believed to belong to the 1835 town'}"></i>
      <span class="person-main"><span class="person-name">${escapeHtml(r.name)}</span>${
        sub ? `<small class="person-sub">${escapeHtml(sub)}</small>` : ''}</span>${mark}</button>`;
  }

  let current = [];
  function paintList() {
    current = matches();
    state.matched = current.length;
    const shown = current.slice(0, state.shown);
    if (!current.length) {
      resultsEl.innerHTML = `<p class="people-empty">No one by that name. Try a surname alone — ${
        n(counts.letter_list_only)} of this town's people are only a name on a post-office letter list.</p>`;
    } else {
      resultsEl.innerHTML = shown.map(rowHtml).join('');
    }
    const left = current.length - shown.length;
    moreBtn.hidden = left <= 0;
    moreBtn.textContent = left > 0 ? `Show ${n(Math.min(PAGE, left))} more · ${n(left)} left` : '';
    const anyNarrowing = state.q.trim() || Object.keys(state.filters).length;
    noteEl.textContent = anyNarrowing
      ? `${n(current.length)} of ${n(rows.length)} people${state.q.trim() ? ` match “${state.q.trim()}”` : ''}`
      : `Everyone, by surname. ${n(rows.length)} people.`;
  }

  function paint() {
    paintFilters();
    paintList();
  }

  moreBtn.addEventListener('click', () => {
    state.shown += PAGE;
    paintList();
    // Keep the reader where they were: focus the first newly shown row.
    const first = resultsEl.querySelectorAll('.person-row')[state.shown - PAGE];
    first?.focus?.({ preventScroll: true });
  });

  let typing = 0;
  input.addEventListener('input', () => {
    clearTimeout(typing);
    typing = setTimeout(() => {
      state.q = input.value;
      state.shown = PAGE;
      paint();
    }, 60);
  });
  input.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowDown') { ev.preventDefault(); resultsEl.querySelector('.person-row')?.focus(); }
    if (ev.key === 'Enter') { const first = resultsEl.querySelector('.person-row'); if (first) open(first.dataset.personId); }
  });
  resultsEl.addEventListener('keydown', (ev) => {
    const row = ev.target.closest('.person-row');
    if (!row) return;
    if (ev.key === 'ArrowDown') { ev.preventDefault(); (row.nextElementSibling || moreBtn)?.focus(); }
    if (ev.key === 'ArrowUp') { ev.preventDefault(); (row.previousElementSibling || input).focus(); }
  });
  resultsEl.addEventListener('click', (ev) => {
    const row = ev.target.closest('.person-row');
    if (row) open(row.dataset.personId);
  });

  // ---- the person card -------------------------------------------------- //

  /** The building's title as the card prints it — `displayName` over the loaded
   *  sidecar, so a reconstructed roof reads "The Pratt house", not "D3 #017". */
  function buildingTitle(id) {
    const rec = registry?.get?.(id);
    if (!rec) return null;
    return displayName(rec.sidecar, id).title;
  }

  function goButton(r, which, id, title) {
    const verb = which === 'both' ? 'lived and worked' : which === 'lives' ? 'lived' : 'worked';
    return `<button type="button" class="people-go" data-go="${which}" data-structure="${escapeHtml(id)}">
      <span class="people-go-verb">Go to where they ${verb}</span>
      <span class="people-go-title">${escapeHtml(title)}</span></button>`;
  }

  function actionsHtml(r) {
    const livesTitle = r.lives_at ? buildingTitle(r.lives_at) : null;
    const worksTitle = r.works_at ? buildingTitle(r.works_at) : null;
    if (livesTitle && worksTitle && r.lives_at === r.works_at) return goButton(r, 'both', r.lives_at, livesTitle);
    const out = [];
    if (livesTitle) out.push(goButton(r, 'lives', r.lives_at, livesTitle));
    if (worksTitle) out.push(goButton(r, 'works', r.works_at, worksTitle));
    if (out.length) return out.join('');
    const unresolved = (r.lives_at || r.works_at) ? ' — the building it names is not in this scene' : '';
    return `<p class="people-noaddr" data-reason="pending">No known address${escapeHtml(unresolved)}<span class="people-noaddr-why"></span></p>`;
  }

  let openSeq = 0;
  /**
   * Open a person's card in place of the list. Resolves `true` once the household
   * record has been fetched and rendered (or its failure written), so a harness
   * can await it.
   */
  async function open(id) {
    const r = byId.get(id);
    if (!r) return false;
    const seq = ++openSeq;
    state.open = id;
    const knownTitle = KNOWN_TITLE[r.how_known] || '';
    cardEl.innerHTML = `
      <button type="button" class="people-back" id="people-back">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>
        All people</button>
      <h3 class="people-card-name">${escapeHtml(r.name)}</h3>
      <p class="people-card-meta">
        <i class="grade-dot grade-${escapeHtml(r.grade)}"></i>${escapeHtml(r.grade)}
        · <span class="person-mark mark-${escapeHtml(r.how_known)}" title="${escapeHtml(knownTitle)}">${
          escapeHtml(r.how_known === 'documented' ? 'documented' : KNOWN_LABEL[r.how_known])}</span>${
        r.occupation ? ` · ${escapeHtml(words(r.occupation))}` : ''}
        <br><span class="people-card-hh">${escapeHtml(words(r.relationship))} of <b>${escapeHtml(r.household_name)}</b>${
          r.division && r.division !== 'unplaced' ? `, ${escapeHtml(words(r.division))} division` : ''}</span>
      </p>
      <div class="people-card-actions">${actionsHtml(r)}</div>
      <p class="people-card-what">${escapeHtml(knownTitle)}.</p>
      <div class="people-card-body" aria-busy="true"><p class="legend-note">Loading the household record…</p></div>`;
    home.hidden = true;
    cardEl.hidden = false;
    section?.classList.add('people-card-open');
    if (typeof onTitle === 'function') onTitle(r.name, () => { state.lastOpened = state.open; close(); });
    mount.closest('.panel-scroll')?.scrollTo?.(0, 0);
    cardEl.querySelector('.people-back')?.focus?.({ preventScroll: true });

    const body = cardEl.querySelector('.people-card-body');
    /** Render the record; called twice — with the citations alone as soon as the
     *  record arrives, and again with the identity reviews, the directory
     *  crosswalks and the ladder once those (a couple of megabytes) are in.
     *  The rows a reader opened in between stay open. */
    const render = (hh, joins) => {
      const wasOpen = new Set([...body.querySelectorAll('details[open] > summary')]
        .map((s) => s.textContent.replace(/\s+/g, ' ').trim()));
      body.innerHTML = '<h4 class="people-card-h">The household record</h4>'
        + householdHtml(hh, joins.citationsById, joins.researchByPerson, joins.directoryByPerson, joins.ladderRules,
          joins.agencies, joins.withheldByPerson);
      for (const det of body.querySelectorAll('details')) {
        const summary = det.querySelector(':scope > summary')?.textContent.replace(/\s+/g, ' ').trim() || '';
        const title = det.querySelector(':scope > summary .lib-title')?.textContent?.trim();
        // This person's own row leads; anything the reader had opened stays open.
        if (title === r.name || wasOpen.has(summary)) det.open = true;
      }
    };
    try {
      const [hh, citationsById] = await Promise.all([getJson(`residents/${r.file}`), citations()]);
      if (seq !== openSeq) return false; // a later open won
      render(hh, { citationsById, researchByPerson: new Map(), directoryByPerson: new Map(),
        withheldByPerson: new Map(), ladderRules: [] });
      const why = cardEl.querySelector('.people-noaddr-why');
      if (why) {
        const note = hh?.lives_at?.note || hh?.works_at?.note || '';
        if (note) { why.textContent = ` — ${note}`; why.closest('.people-noaddr')?.setAttribute('data-reason', 'record'); }
      }
      const joins = await loadResidentJoins(dataBase, sceneId, problems);
      if (seq !== openSeq) return false;
      render(hh, joins);
    } catch (err) {
      if (seq !== openSeq) return false;
      problems.push(`people: ${err.message} — one household record is missing`);
      body.innerHTML = `<p class="legend-note">This household's record could not be loaded. It is committed at
        <code>data/residents/${escapeHtml(r.file || '')}</code>.</p>`;
    } finally {
      if (seq === openSeq) body.removeAttribute('aria-busy');
    }
    return true;
  }

  function close() {
    state.open = null;
    cardEl.hidden = true;
    cardEl.innerHTML = '';
    home.hidden = false;
    section?.classList.remove('people-card-open');
    if (typeof onTitle === 'function') onTitle(null);
    paintList();
    const row = resultsEl.querySelector(`.person-row[data-person-id="${CSS.escape(state.lastOpened || '')}"]`);
    (row || input)?.focus?.({ preventScroll: true });
  }

  cardEl.addEventListener('click', (ev) => {
    if (ev.target.closest('.people-back')) { state.lastOpened = state.open; close(); return; }
    const go = ev.target.closest('.people-go');
    if (go && state.open) {
      const r = byId.get(state.open);
      const which = go.dataset.go;
      onGoTo?.({
        kind: 'person',
        id: r.id,
        label: r.name,
        lives_at: which === 'works' ? null : r.lives_at,
        works_at: which === 'lives' ? null : r.works_at,
      });
    }
  });

  paint();
  // The citation join, the identity reviews and the directory crosswalks are what
  // a card renders a record WITH, and together they are a couple of megabytes.
  // Started now, after the list has painted, so the first card a visitor opens
  // is not waiting on them; `loadResidentJoins` caches, so opening a card before
  // this settles simply awaits the same promise.
  setTimeout(() => { loadResidentJoins(dataBase, sceneId, problems).catch(() => {}); }, 0);

  return {
    people: rows.length,
    error: null,
    /** Type into the box programmatically and repaint at once. */
    search(q) { input.value = String(q ?? ''); state.q = input.value; state.shown = PAGE; paint(); return state.matched; },
    /** Open a person's card; resolves when the household body is rendered. */
    open,
    close,
    /** Set one filter row (`''`/null clears it). */
    filter(key, value) { setFilter(key, value); return state.matched; },
    /** Fold or unfold the filter rows (phones start folded). */
    showFilters(on = true) { state.filtersOpen = !!on; paintFilters(); },
    get state() { return { ...state, filters: { ...state.filters } }; },
    /** The ids currently listed, in order (for the harness). */
    results() { return current.map((r) => r.id); },
  };
}
