/**
 * goto.js — everywhere you can stand and everyone who stood there, in one searchable list.
 *
 * Lifted out of hud.js (2026-09-04) when the owner asked for three things the old list
 * could not do: hide the reconstructed roofs unless asked ("attested + inferred shown;
 * reconstructed available as an option"), filter by kind ("like taverns, shops, etc."), and
 * put the citizens in it ("the citizens should show there"). The list stays complete by
 * construction — destinations.js builds one inventory from the renderer's loaded
 * collections, including firms and people without an address. This view keeps the
 * behaviours a visitor already relies on: typing
 * never moves the camera; Enter goes to the first row (or the one the arrow keys reached);
 * the search folds diacritics, so "Beaubien" finds "Beaubien" however it was typed.
 *
 * Contract: createGoTo({ root, destinations, visitor,
 *   units, settings, isTouch, onGoTo, onPersist }) -> { paint(query), open(),
 *   refreshDistances(), setKind(id), setIncludeReconstructed(bool), targets }
 * `root` is the <section data-panel="goto">; this module renders its own markup into it.
 *
 * Two grades, one chip. The chip on a structure row is the PRESENCE grade — whether the
 * building stood here on the scene date — because that is the question a visitor choosing
 * where to go is asking. The position grade (how well we know WHERE) rides along as
 * `data-jump-position` for the smoke and the card. Viewpoints, corners and people carry no
 * chip: a viewpoint is where the camera is put, a corner is a survey fact, and a person's
 * grade belongs to the person card. An empty chip would read as a missing grade rather than
 * as a category that has none.
 *
 * Distances are the visitor's: measured from `visitor()` in the visitor's units, with the
 * arrow turned by (bearing to the place − the way the visitor faces), so it points where
 * they would turn. Repainted by `refreshDistances()` — on open, on a unit change, and on a
 * half-second tick while the section is showing — without re-sorting, so the list does not
 * shuffle under a pointer.
 */
import { formatDistance } from './units.js';
import { escapeHtml } from './citations.js';

const CARDINALS = [
  'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
];
const ARROW_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
  + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20V5"/><path d="M6 11l6-6 6 6"/></svg>';
const SEARCH_SVG = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" '
  + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4-4"/></svg>';

const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
const normalBearing = (value) => ((Number(value) || 0) % 360 + 360) % 360;
const cardinal = (bearing) => CARDINALS[Math.round(normalBearing(bearing) / 22.5) % CARDINALS.length];
export function createGoTo({
  root, destinations, visitor = null,
  units = () => 'imperial', settings = {}, isTouch = false, onGoTo, onPersist,
} = {}) {
  const noop = { paint() {}, open() {}, refreshDistances() {}, setKind() {}, setIncludeReconstructed() {}, targets: [] };
  if (!root) return noop;

  const { targets, groups } = destinations;
  const GROUP_LABEL = Object.fromEntries(groups.map(k => [k.id, k.label]));

  // ---- the markup ------------------------------------------------------------
  root.classList.toggle('jump-touch', !!isTouch);
  const pillHtml = (id, label) => `<button type="button" class="jump-pill" data-kind="${id}" aria-pressed="${id === 'all'}">`
    + `<span class="jump-pill-label">${escapeHtml(label)}</span><span class="jump-pill-n"></span></button>`;
  root.innerHTML = `
    <div class="jump-head">
      <label class="field jump-field">
        <span>Search everywhere <b id="jump-count"></b></span>
        <span class="jump-search-wrap">${SEARCH_SVG}<input type="search" id="jump-search"
          placeholder="A place, a business, a person…" autocomplete="off" spellcheck="false"
          role="combobox" aria-expanded="true" aria-haspopup="listbox" aria-autocomplete="list"
          aria-controls="jump-results"></span>
      </label>
      <div class="jump-pills" role="group" aria-label="Kinds of place">
        ${pillHtml('all', 'All')}${groups.map((k) => pillHtml(k.id, k.label)).join('')}
      </div>
      <label class="jump-toggle">
        <input type="checkbox" id="jump-reconstructed">
        <span>Include reconstructed roofs (<b id="jump-hidden-count">0</b>)</span>
      </label>
    </div>
    <div class="jump-results" id="jump-results" role="listbox" aria-label="Places and people"></div>
    <p class="legend-note" id="jump-note"></p>
    <p class="legend-note jump-legend">The chip on a building grades whether it stood here on the
      scene date — <span class="conf conf-attested">attested</span> by a source,
      <span class="conf conf-inferred">inferred</span> from one, or
      <span class="conf conf-reconstructed">reconstructed</span> to fill the block. It is not a
      grade of where the model stands. Viewpoints and corners are not claims about the town and
      carry no grade. A person or firm takes you to its known building; without an address, its card opens instead.</p>`;

  const $ = (sel) => root.querySelector(sel);
  const input = $('#jump-search');
  const results = $('#jump-results');
  const countEl = $('#jump-count');
  const hiddenCountEl = $('#jump-hidden-count');
  const noteEl = $('#jump-note');
  const toggle = $('#jump-reconstructed');
  const pills = [...root.querySelectorAll('.jump-pill')];

  // ---- state -----------------------------------------------------------------
  let kind = 'all';
  let includeReconstructed = !!settings.gotoReconstructed;
  let query = '';
  let active = -1;
  /** The rows on screen, in order: `{ t, el }`. */
  let painted = [];
  toggle.checked = includeReconstructed;

  function where() {
    try { return visitor?.() ?? null; } catch { return null; }
  }
  function distOf(t, v) {
    if (!v || !Number.isFinite(t.e) || !Number.isFinite(t.n)) return null;
    const dE = t.e - v.e; const dN = t.n - v.n;
    return { m: Math.hypot(dE, dN), bearing: normalBearing(Math.atan2(dE, dN) * 180 / Math.PI) };
  }

  function distHtml(d, v) {
    if (!d) return '';
    if (d.m < 4) return 'here';
    return `<i class="jump-arrow" style="--turn:${Math.round(normalBearing(d.bearing - (v?.bearingDeg ?? 0)))}deg">${ARROW_SVG}</i>`
      + `<span>${formatDistance(d.m, units())} ${cardinal(d.bearing)}</span>`;
  }

  function rowHtml(t, i, d, v) {
    const attrs = [`data-jump-kind="${t.kind}"`, `data-jump-id="${escapeHtml(t.id)}"`, `data-jump-group="${t.group}"`];
    if (t.kind === 'structure') attrs.push(`data-jump-confidence="${t.presence}"`, `data-jump-position="${t.position}"`);
    const chip = t.kind === 'structure' ? `<small class="conf conf-${t.presence}">${t.presence}</small>` : '';
    return `<button type="button" class="jump-result" role="option" id="jump-opt-${i}" aria-selected="false" ${attrs.join(' ')}>`
      + `<span class="jump-main"><span class="jump-name">${escapeHtml(t.label)}</span>`
      + `<small class="jump-sub">${escapeHtml(t.sub)}</small></span>`
      + `<span class="jump-side"><small class="jump-dist" data-m="${d ? Math.round(d.m) : ''}">${distHtml(d, v)}</small>${chip}</span>`
      + '</button>';
  }

  /** The teaching empty state: what to try next, never an apology. */
  function emptyText() {
    const tries = ['a surname', 'a street'];
    if (kind !== 'all') tries.push(`the All pill`);
    if (!includeReconstructed) tries.push('turning on the reconstructed roofs');
    if (kind === 'people' && !destinations.peopleAvailable) return 'The people directory is not available in this build, so nobody is listed here yet.';
    const last = tries.pop();
    return `Nothing here is called that. Try ${tries.join(', ')}, or ${last}.`;
  }

  function paintPills(base) {
    const n = {};
    for (const t of base) n[t.group] = (n[t.group] || 0) + 1;
    for (const pill of pills) {
      const id = pill.dataset.kind;
      const count = id === 'all' ? base.length : (n[id] || 0);
      pill.setAttribute('aria-pressed', String(id === kind));
      const label = pill.querySelector('.jump-pill-n');
      if (id === 'people' && !destinations.peopleAvailable) {
        label.textContent = '';
        pill.disabled = true;
        pill.title = 'The people directory is not available in this build';
      } else {
        label.textContent = String(count);
        pill.disabled = false;
        pill.removeAttribute('title');
      }
    }
  }

  // What the list adds up to, counted from the same targets it is painted from rather than
  // typed into the prose. It is not a flattering line and it is the honest summary.
  function paintNote() {
    const structures = targets.filter((t) => t.kind === 'structure');
    const tally = { attested: 0, inferred: 0, reconstructed: 0 };
    for (const t of structures) if (t.presence in tally) tally[t.presence]++;
    const total = structures.length;
    const shown = includeReconstructed ? total : total - tally.reconstructed;
    const viewpoints = targets.filter((t) => t.kind === 'anchor').length;
    const junctions = targets.filter((t) => t.kind === 'intersection').length;
    const withAddress = targets.filter((t) => t.kind === 'person' && t.at).length;
    const unknown = targets.filter(t => t.kind === 'person' && !t.at).length;
    const businesses = targets.filter(t => t.kind === 'business').length;
    const roofs = `${tally.reconstructed} reconstructed roofs are ${includeReconstructed
      ? 'showing too' : 'hidden until you ask for them'}`;
    const peopleLine = !destinations.peopleAvailable
      ? 'The people directory is not available in this build, so nobody is listed.'
      : `${withAddress} ${withAddress === 1 ? 'person has' : 'people have'} a known address. ${unknown} without an address can still open a card. ${businesses} businesses are searchable.`;
    noteEl.textContent = `${plural(viewpoints, 'viewpoint')}, ${plural(junctions, 'verified junction')} and `
      + `${shown} of ${total} structures — ${roofs}. Of all ${total}, ${tally.attested} are attested to have `
      + `stood here, ${tally.inferred} inferred and ${tally.reconstructed} reconstructed. ${peopleLine}`;
    hiddenCountEl.textContent = String(tally.reconstructed);
  }

  function paint(q = query) {
    query = String(q ?? '');
    const v = where();
    const base = destinations.search('', { includeReconstructed });
    const matched = destinations.search(query, { kind, includeReconstructed, visitor: v }).map(t => ({ t, d: distOf(t, v) }));

    countEl.textContent = matched.length === base.length
      ? `${plural(base.length, 'place')}` : `${matched.length} of ${base.length}`;
    paintPills(base);

    let html = ''; let lastGroup = null; let i = 0;
    for (const row of matched) {
      if (row.t.group !== lastGroup) {
        lastGroup = row.t.group;
        const n = matched.filter((r) => r.t.group === lastGroup).length;
        html += `<p class="jump-group" data-group="${lastGroup}">${escapeHtml(GROUP_LABEL[lastGroup] ?? lastGroup)}`
          + `<span class="jump-group-n">${n}</span></p>`;
      }
      html += rowHtml(row.t, i++, row.d, v);
    }
    results.innerHTML = matched.length ? html : `<p class="jump-empty">${escapeHtml(emptyText())}</p>`;
    const els = [...results.querySelectorAll('.jump-result')];
    painted = matched.map((row, j) => ({ t: row.t, el: els[j] }));
    setActive(-1);
    paintNote();
  }

  // ---- distances -------------------------------------------------------------
  function refreshDistances() {
    const v = where();
    if (!v) return;
    for (const { t, el } of painted) {
      const d = distOf(t, v);
      const dist = el.querySelector('.jump-dist');
      if (!dist) continue;
      dist.dataset.m = d ? String(Math.round(d.m)) : '';
      dist.innerHTML = distHtml(d, v);
    }
  }
  const panel = root.closest('.hud-panel');
  const showing = () => !root.hasAttribute('hidden') && !panel?.hasAttribute('hidden') && !document.hidden;
  let last = null;
  // A half-second tick while the section is showing: the arrows follow the visitor's turn
  // and the metres their steps, without re-sorting the rows under a pointer.
  setInterval(() => {
    if (!showing()) return;
    const v = where();
    if (!v) return;
    const turned = last ? Math.abs(((v.bearingDeg - last.bearingDeg + 540) % 360) - 180) : 999;
    if (last && Math.hypot(v.e - last.e, v.n - last.n) < 0.5 && turned < 2) return;
    last = v;
    refreshDistances();
  }, 500);

  // ---- keyboard --------------------------------------------------------------
  function setActive(i) {
    active = i;
    painted.forEach(({ el }, j) => {
      el.classList.toggle('is-active', j === i);
      el.setAttribute('aria-selected', String(j === i));
    });
    const row = painted[i]?.el;
    if (row) {
      input.setAttribute('aria-activedescendant', row.id);
      row.scrollIntoView({ block: 'nearest' });
    } else input.removeAttribute('aria-activedescendant');
  }
  input.addEventListener('input', () => paint(input.value));
  input.addEventListener('keydown', (e) => {
    const n = painted.length;
    if (e.key === 'ArrowDown') { e.preventDefault(); if (n) setActive(Math.min(n - 1, active + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); if (n) setActive(active < 0 ? n - 1 : Math.max(0, active - 1)); }
    else if (e.key === 'Home') { e.preventDefault(); if (n) setActive(0); }
    else if (e.key === 'End') { e.preventDefault(); if (n) setActive(n - 1); }
    else if (e.key === 'Enter') {
      const row = painted[active]?.el ?? painted[0]?.el;
      if (row) { e.preventDefault(); row.click(); }
    }
  });
  results.addEventListener('click', (e) => {
    const el = e.target.closest('.jump-result');
    if (!el) return;
    const row = painted.find((r) => r.el === el);
    if (row) onGoTo?.(row.t);
  });

  // ---- pills and the toggle ----------------------------------------------------
  function setKind(id) {
    kind = id === 'all' || GROUP_LABEL[id] ? id : 'all';
    paint();
  }
  for (const pill of pills) {
    // Single-select; pressing the pressed pill returns to All.
    pill.addEventListener('click', () => setKind(pill.dataset.kind === kind ? 'all' : pill.dataset.kind));
  }
  function setIncludeReconstructed(on) {
    includeReconstructed = !!on;
    toggle.checked = includeReconstructed;
    onPersist?.('gotoReconstructed', includeReconstructed);
    paint();
  }
  toggle.addEventListener('change', () => setIncludeReconstructed(toggle.checked));

  /** Shown: re-sort by where the visitor now stands, then point the arrows. */
  function open() {
    paint(input.value);
    refreshDistances();
  }

  paint('');
  return { paint, open, refreshDistances, setKind, setIncludeReconstructed, targets };
}
