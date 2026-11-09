/**
 * People (SCR 04) as its own screen, loaded the first time it opens (T-2618).
 *
 * Used where a scene has a people directory but not the drawer's People section: 1904 and
 * 1812, whose directories (`sidecars/<scene>/people.json`, T-2702) are fetched here, on
 * first open, never at boot.
 *
 * T-3430 (the owner, 2026-11-06: "this should have some search to it to be able to find a
 * person or household and then click and get details on that person and household the way
 * we have it with their full story and overview and be able to go to that person and or
 * their house"): the screen is a directory. A search box over people and households, a
 * Households / People switch with counts, the household of the building in view pinned
 * first. A household opens its own card here (address, the scene-date reading, family,
 * staff, children of other years, who is not on it, former residents); a person opens the
 * same full card Inspect's People tab draws (person-card.js). Each card has Go to house
 * and Inspect house; a person placed in town also has Find and Follow (T-3404). Back
 * returns through the cards to the list, its search and scroll kept.
 *
 * T-3438 (the owner, 2026-11-07: "weird that the shorthalls at 1600 prairie are listed twice in
 * households?" and "it shows in the people list too?"): the pinned household was ALSO the first
 * row of the list under it, and on the People side a household row sat among the people. Now
 * the pin is said once: on Households the household in view, then "Every other household"; on
 * People that household's own people (never a household row), then "Everyone else". A search
 * drops the pin and lists every match.
 *
 * The pure half (households, search) is people-directory.js.
 */
import { personModel, renderPersonCard } from '../person-card.js';
import { formerResidentsBlock } from './former-residents.js';
import {
  directoryModel, search, householdOf, householdAt, householdCount, placeIn, workOf, yearsWords, away,
} from '../people-directory.js';

const GRADES = ['attested', 'inferred', 'reconstructed'];
const WORD = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const GLOSS = { attested: 'a source says so', inferred: 'worked out from clues', reconstructed: 'built so the street makes sense' };
const PAGE = 60;
const BACK_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5-7 7 7 7"/></svg>';
const FIND_SVG = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>';

function el(doc, tag, cls, text) {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
/** A grade dot, as Inspect draws it. */
function dot(doc, grade) {
  const g = GRADES.includes(grade) ? grade : null;
  if (!g) return doc.createTextNode('');
  const i = el(doc, 'i', `fact-dot fact-${g}`);
  i.setAttribute('role', 'img');
  i.setAttribute('aria-label', WORD[g]);
  i.title = `${WORD[g]}: ${GLOSS[g]}`;
  return i;
}
function line(doc, tag, cls, text, grade) {
  const n = el(doc, tag, cls, text);
  n.append(dot(doc, grade));
  return n;
}
const counted = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
const heading = (doc, text) => el(doc, 'h3', 'insp-h', text);
const button = (doc, cls, text) => { const b = el(doc, 'button', cls, text); b.type = 'button'; return b; };

let state = null;   // the one mounted screen

export async function mount(root, ctx = {}) {
  const doc = root.ownerDocument;
  root.replaceChildren(el(doc, 'p', 'nav-sub', 'Reading the directory…'));
  let dir = null;
  try { dir = await ctx.actions?.peopleDirectory?.(); } catch { dir = null; }
  root.replaceChildren();
  const model = directoryModel(dir);
  if (!model.people.length) {
    root.append(el(doc, 'p', 'nav-sub', 'The people directory for this scene could not be read.'));
    return;
  }
  const st = state = { root, ctx, dir, model, seg: 'households', shown: PAGE, stack: [], listTop: 0 };
  const sceneYear = Number(String(ctx?.scene?.id ?? ctx?.scene?.scene_id ?? '').slice(0, 4)) || null;
  st.sceneYear = sceneYear;

  // The list: search, switch, status, the household in view, the results.
  const list = st.list = el(doc, 'div', 'ppl-dir');
  const find = el(doc, 'label', 'ppl-find');
  find.insertAdjacentHTML('afterbegin', FIND_SVG);
  const input = st.input = el(doc, 'input', 'ppl-search');
  input.type = 'search';
  input.placeholder = 'Name, house, address, work';
  input.autocomplete = 'off';
  input.spellcheck = false;
  input.setAttribute('aria-label', 'Search people and households');
  find.append(input);
  const segs = el(doc, 'div', 'nav-segments ppl-segs');
  segs.setAttribute('role', 'tablist');
  st.segButtons = {};
  for (const [key, label] of [['households', 'Households'], ['people', 'People']]) {
    const b = button(doc, 'nav-segment', null);
    b.dataset.pplSeg = key;
    b.setAttribute('role', 'tab');
    b.append(el(doc, 'span', null, label), el(doc, 'span', 'ppl-seg-n', ''));
    b.addEventListener('click', () => { st.seg = key; st.shown = PAGE; drawResults(st); });
    segs.append(b);
    st.segButtons[key] = b;
  }
  st.status = el(doc, 'p', 'nav-k ppl-status');
  st.status.setAttribute('aria-live', 'polite');
  st.inView = el(doc, 'section', 'ppl-inview');
  st.inView.hidden = true;
  st.rest = el(doc, 'span', 'nav-k ppl-rest');
  st.rest.hidden = true;
  st.results = el(doc, 'div', 'ppl-results');
  st.more = button(doc, 'nav-segment ppl-more', '');
  st.more.addEventListener('click', () => { st.shown += PAGE; drawResults(st); });
  list.append(find, segs, st.status, st.inView, st.rest, st.results, st.more);
  st.card = el(doc, 'div', 'ppl-card');
  st.card.hidden = true;
  root.append(list, st.card);

  input.addEventListener('input', () => { st.shown = PAGE; drawResults(st, { auto: true }); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && input.value) { e.preventDefault(); e.stopPropagation(); input.value = ''; drawResults(st); }
    if (e.key === 'Enter') {
      e.preventDefault();
      root.querySelector('.ppl-results [data-ppl-open]')?.click();
    }
  });
  list.addEventListener('click', (e) => {
    const row = e.target.closest('[data-ppl-open]');
    if (row) open(st, row.dataset.pplKind, row.dataset.pplOpen);
  });
  st.card.addEventListener('click', (e) => onCardClick(st, e));
  drawInView(st, ctx);
}

/** Every time People opens: the household of the building now in view, and a fresh ctx. */
export function shown(root, ctx = {}) {
  if (!state || state.root !== root) return;
  state.ctx = ctx;
  drawInView(state, ctx);
}

export function unmount(root) {
  if (state?.root === root) state = null;
  root.replaceChildren();
}

/** The household living in the building Inspect holds, or the tag names, pinned first. */
function drawInView(st, ctx) {
  st.pinned = householdAt(st.model, ctx?.selected ?? ctx?.target?.id ?? null);
  drawResults(st);
}

/**
 * The pin, for this side of the switch: the household itself on Households; its people on
 * People (a household is never a row among people). Returns the ids it shows, which the list
 * under it leaves out, so nothing is said twice (T-3438).
 */
function pinFor(st, doc) {
  const h = st.pinned;
  st.inView.replaceChildren();
  if (!h) return new Set();
  if (st.seg === 'households') {
    st.inView.append(el(doc, 'span', 'nav-k', 'In view'), householdRow(doc, h));
    return new Set([h.id]);
  }
  const here = [...h.family, ...h.staff].map((p) => st.model.byId.get(p.id) ?? p);
  if (!here.length) return new Set();
  st.inView.append(el(doc, 'span', 'nav-k', `In view · ${h.short}`), ...here.map((p) => personRow(doc, p, { withHousehold: false })));
  return new Set(here.map((p) => p.id));
}

function householdRow(doc, h) {
  const b = button(doc, 'nav-person ppl-row ppl-hh', null);
  b.dataset.pplKind = 'household';
  b.dataset.pplOpen = h.id;
  b.append(el(doc, 'span', 'nav-person-name', h.short),
    el(doc, 'span', 'nav-sub', [h.address, householdCount(h)].filter(Boolean).join(' · ')));
  return b;
}

function personRow(doc, p, { withHousehold = true } = {}) {
  const b = button(doc, 'nav-person ppl-row', null);
  b.dataset.pplKind = 'person';
  b.dataset.pplOpen = p.id;
  // Staff by their work; family by their place in the household, then any work.
  const role = p.relationship === 'servant' ? [workOf(p) || placeIn(p.relationship)] : [placeIn(p.relationship), workOf(p)];
  const sub = [...role, away(p) ? `lived here ${yearsWords(p.lived_here)}`.trim() : '',
    withHousehold ? p.short : ''].filter(Boolean);
  b.append(line(doc, 'span', 'nav-person-name', p.name, p.grade), el(doc, 'span', 'nav-sub', sub.join(' · ')));
  return b;
}

/** The results for the query and switch, a page at a time. */
function drawResults(st, { auto = false } = {}) {
  const doc = st.root.ownerDocument;
  const r = search(st.model, st.input.value);
  // A query that finds nothing on this side but something on the other moves the switch there.
  if (auto && r.query) {
    if (st.seg === 'households' && !r.households.length && r.people.length) st.seg = 'people';
    else if (st.seg === 'people' && !r.people.length && r.households.length) st.seg = 'households';
  }
  for (const [key, b] of Object.entries(st.segButtons)) {
    const on = key === st.seg;
    b.classList.toggle('is-on', on);
    b.setAttribute('aria-selected', String(on));
    b.querySelector('.ppl-seg-n').textContent = String(r[key].length);
  }
  const all = { households: st.model.households.length, people: st.model.people.length };
  st.status.textContent = r.query
    ? (r.households.length + r.people.length
      ? `${counted(r.households.length, 'household')} · ${counted(r.people.length, 'person', 'people')} match` : 'No match')
    : `${counted(all.households, 'household')} · ${counted(all.people, 'person', 'people')}`;
  // The pin only on the whole list; a search lists every match, the household in view among them.
  const pinned = r.query ? new Set() : pinFor(st, doc);
  if (r.query) st.inView.replaceChildren();
  st.inView.hidden = !pinned.size;
  st.rest.hidden = !pinned.size;
  st.rest.textContent = st.seg === 'households' ? 'Every other household' : 'Everyone else';
  const items = pinned.size ? r[st.seg].filter((x) => !pinned.has(x.id)) : r[st.seg];
  st.results.replaceChildren(...items.slice(0, st.shown).map((x) => (st.seg === 'households' ? householdRow(doc, x) : personRow(doc, x))));
  const left = items.length - Math.min(items.length, st.shown);
  st.more.hidden = left <= 0;
  st.more.textContent = left > 0 ? `Show ${Math.min(PAGE, left)} more · ${left} left` : '';
}

// ---- the cards --------------------------------------------------------------------- //

/** Open a card over the list (or over the card before it), remembering where Back goes. */
function open(st, kind, id) {
  if (!id) return;
  if (!st.stack.length) st.listTop = st.root.scrollTop;
  st.stack.push({ kind, id });
  draw(st);
}

function back(st) {
  st.stack.pop();
  draw(st);
}

function draw(st) {
  const top = st.stack[st.stack.length - 1];
  st.list.hidden = !!top;
  st.card.hidden = !top;
  st.card.replaceChildren();
  if (!top) {
    st.root.scrollTop = st.listTop;
    return;
  }
  st.root.scrollTop = 0;
  if (top.kind === 'household') void drawHousehold(st, top.id);
  else void drawPerson(st, top.id);
}

/** Where Back goes, named: the card under this one, or the list. */
function backLabel(st) {
  const under = st.stack[st.stack.length - 2];
  if (!under) return 'People';
  if (under.kind === 'household') return st.model.householdById.get(under.id)?.short ?? 'Household';
  return st.model.byId.get(under.id)?.name ?? 'Back';
}

function backButton(doc, label) {
  const b = button(doc, 'insp-person-back', null);
  b.dataset.pplBack = '';
  b.setAttribute('aria-label', `Back to ${label}`);
  b.innerHTML = BACK_SVG;
  b.append(el(doc, 'span', null, label));
  return b;
}

/** Go to house / Inspect house, where the house stands in this scene. */
function houseKeys(st, structureId) {
  const doc = st.root.ownerDocument;
  const row = el(doc, 'div', 'ppl-keys');
  const built = !!structureId && !!st.ctx.actions?.record?.(structureId);
  if (!built) {
    row.append(el(doc, 'p', 'nav-k ppl-unbuilt', 'House not in this scene'));
    return row;
  }
  const go = button(doc, 'nav-key nav-roam ppl-go', 'Go to house');
  go.dataset.pplGo = structureId;
  const insp = button(doc, 'nav-key nav-roam ppl-inspect', 'Inspect house');
  insp.dataset.pplInspect = structureId;
  row.append(go, insp);
  return row;
}

async function drawHousehold(st, id) {
  const doc = st.root.ownerDocument;
  const h = st.model.householdById.get(id);
  if (!h) { back(st); return; }
  const card = el(doc, 'article', 'insp-person-card ppl-hh-card');
  card.dataset.household = id;
  card.append(backButton(doc, backLabel(st)));
  const head = el(doc, 'header', 'insp-person-head');
  head.append(el(doc, 'span', 'nav-k', 'Household'), el(doc, 'h2', 'insp-name insp-person-name', h.short));
  if (h.address) head.append(el(doc, 'p', 'insp-address', h.address));
  const chips = el(doc, 'ul', 'insp-chips');
  chips.append(el(doc, 'li', 'insp-chip', householdCount(h)));
  head.append(chips);
  card.append(head, houseKeys(st, h.lives_at));
  const when = el(doc, 'section', 'insp-sec ppl-when');
  card.append(when);

  const group = (title, rows) => {
    if (!rows.length) return;
    const s = el(doc, 'section', 'insp-sec ppl-members');
    s.append(heading(doc, title));
    for (const p of rows) s.append(personRow(doc, st.model.byId.get(p.id) ?? p, { withHousehold: false }));
    card.append(s);
  };
  group('Family', h.family);
  group('Live-in staff', h.staff);
  group('Children who lived here in other years', h.away);
  const not = el(doc, 'section', 'insp-sec ppl-not');
  card.append(not);
  const past = formerResidentsBlock(doc, st.dir?.former_residents?.[h.lives_at], { el, line, heading });
  if (past) card.append(past);
  st.card.replaceChildren(card);
  card.querySelector('[data-ppl-back]')?.focus?.({ preventScroll: true });

  // The household's own record: whether it was here on the scene date and why, and who is not on it.
  let rec = null;
  try { rec = await st.ctx.actions?.householdRecord?.(h.file); } catch { rec = null; }
  if (!card.isConnected) return;
  const present = rec?.present_on_scene_date;
  if (present?.note) {
    const year = st.sceneYear ? `In ${st.sceneYear}` : 'On the scene date';
    when.append(line(doc, 'h3', 'insp-h', year, present.confidence), el(doc, 'p', 'insp-summary', present.note));
  } else when.remove();
  const why = String(rec?.not_in_this_household?.note ?? '').replace(/^WHO IS NOT ON THIS CARD, AND WHY\.\s*/, '');
  if (why) not.append(heading(doc, 'Not on this card'), el(doc, 'p', 'nav-sub', why));
  else not.remove();
}

async function drawPerson(st, id) {
  const doc = st.root.ownerDocument;
  const row = st.model.byId.get(id);
  if (!row) { back(st); return; }
  const a = st.ctx.actions ?? {};
  const h = householdOf(st.model, id);
  const placed = (pid) => typeof a.inTown === 'function' && !!a.inTown(pid);
  const render = (m) => {
    // Find goes to someone placed in town, else to the house they are in (T-3521: the owner,
    // 2026-11-08, "a lot of people you cant click find this person and go to them").
    const card = renderPersonCard(doc, m, { dot, onFind: placed(id) || row.lives_at || row.works_at ? a.findPerson ?? null : null,
      onFollow: a.followPerson ?? null, inTown: a.inTown ?? null });
    const b = card.querySelector('[data-person-back]');
    if (b) b.replaceWith(backButton(doc, backLabel(st)));
    const keys = houseKeys(st, row.lives_at && !away(row) ? row.lives_at : (h?.lives_at ?? row.lives_at));
    const under = st.stack[st.stack.length - 2];
    if (h && !(under?.kind === 'household' && under.id === h.id)) {
      const hh = button(doc, 'nav-key nav-roam ppl-household', 'Household');
      hh.dataset.pplHousehold = h.id;
      keys.append(hh);
    }
    const head = card.querySelector('.insp-person-head');
    if (head?.after) head.after(keys); else card.append(keys);
    const was = st.card.querySelector('.insp-person-card');
    if (was) was.replaceWith(card); else st.card.append(card);
    return card;
  };
  render(personModel({ row, sceneYear: st.sceneYear })).querySelector('[data-ppl-back]')?.focus?.({ preventScroll: true });
  const [household, citations, likeness, told] = await Promise.all([
    Promise.resolve(a.householdRecord?.(row.file)).catch(() => null),
    Promise.resolve(a.residentCitations?.()).catch(() => null),
    Promise.resolve(a.personFace?.(id)).catch(() => null),
    Promise.resolve(a.personStory?.(id)).catch(() => null),   // T-3521
  ]);
  const top = st.stack[st.stack.length - 1];
  if (st !== state || top?.kind !== 'person' || top.id !== id) return;   // moved on meanwhile
  const person = (household?.persons ?? []).find((p) => p.id === id) ?? null;
  const card = render(personModel({ row, person, household, citations, sceneYear: st.sceneYear,
    face: likeness?.face ?? null, looks: likeness?.looks ?? null, assetBase: likeness?.base ?? null, told }));
  if (!person) card.querySelector('.insp-person-wait')?.replaceWith(el(doc, 'p', 'nav-sub', 'This person’s household record could not be read.'));
  const focus = doc.activeElement;
  if (!focus || focus === doc.body) card.querySelector('[data-ppl-back]')?.focus?.({ preventScroll: true });
}

function onCardClick(st, e) {
  const t = e.target;
  if (t.closest('[data-ppl-back]')) { back(st); return; }
  const go = t.closest('[data-ppl-go]');
  if (go) {
    const ok = st.ctx.actions?.goTo?.(go.dataset.pplGo);
    // On a phone the device steps down so the ride (or the arrival) is in view.
    if (ok !== false && ['half', 'full'].includes(st.ctx.navigator?.detent)) st.ctx.navigator?.dock?.();
    return;
  }
  const insp = t.closest('[data-ppl-inspect]');
  if (insp) { st.ctx.actions?.inspect?.(insp.dataset.pplInspect); return; }
  const hh = t.closest('[data-ppl-household]');
  if (hh) { open(st, 'household', hh.dataset.pplHousehold); return; }
  const row = t.closest('[data-ppl-open]');
  if (row) { open(st, row.dataset.pplKind, row.dataset.pplOpen); return; }
  // A grown child's own household card elsewhere in the scene (person-card.js `ownCard`).
  const own = t.closest('[data-person]');
  if (own && st.model.byId.has(own.dataset.person)) open(st, 'person', own.dataset.person);
}

/** For the tests. */
export const _test = { get state() { return state; } };
