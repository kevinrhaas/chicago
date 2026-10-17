/**
 * Inspect (SCR 03), the Overview front page (T-2638; DESIGN §08, mockup M7). Loaded the
 * first time Inspect opens.
 *
 * Top to bottom, as M7 orders it: plate, address line, name, three status chips, summary,
 * key facts, who lives here, Look for, notable facts, the Confidence meter. A building with
 * an authored summary record (data/summaries/, compiled by tools/compile_summaries.py into
 * `inspect/<scene>.json`, T-2635) shows that record exactly as written. Every other building
 * shows the templated fallback (T-2636, popup.js `cardOpening`) and only what its own
 * sidecar states: no line here is composed beyond what those two sources say.
 *
 * EVERY FACT LINE CARRIES ITS GRADE DOT (the card's own `fact-dot`), with the grade in
 * words for a screen reader. The address is printed once.
 *
 * The card's other content (Evidence, Images, Liberties, Record) is still the building card
 * until the Inspect tabs land (T-2639): "Full record" opens it, and the Confidence meter
 * opens it on its Evidence tab, which is where a fact's Sources are today.
 */
import { cardOpening } from '../popup.js';
import { displayName } from '../display-name.js';
import { fallbackSummary } from '../fallback-summary.js';

const GRADES = ['attested', 'inferred', 'reconstructed'];
const WORD = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const GLOSS = { attested: 'a source says so', inferred: 'worked out from clues', reconstructed: 'built so the street makes sense' };
const SHOWN_RIGHTS = /^(public domain|no known restrictions)/i;
const MAX_RESIDENTS = 3;
const MAX_NOTABLE = 3;

let host = null;
let drawnFor = null;

function el(doc, tag, cls, text) {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

/** A grade dot: the card's own mark, named for a screen reader. */
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

function heading(doc, text) {
  return el(doc, 'h3', 'insp-h', text);
}

/** The plate: the first picture whose rights allow display and that the store holds. */
function plateFor(pictures, id) {
  const list = pictures?.by_structure?.[id] ?? [];
  const base = pictures?.image_store?.base_url;
  if (!base) return null;
  const p = list.find((x) => x.held?.f && SHOWN_RIGHTS.test(String(x.rights ?? '')));
  if (!p) return null;
  try {
    return { src: new URL(p.held.f, base).href, p };
  } catch {
    return null;
  }
}

/** The fallback's chips: only what the sidecar states. */
function fallbackChips(s) {
  const out = [];
  const today = s?.attributes?.present_status;
  if (today?.value) {
    const v = String(today.value);
    out.push({ text: /^still standing/i.test(v) ? 'Still standing' : v.split(/[—–-]/)[0].trim(), grade: today.confidence });
  }
  return out;
}

/** The fallback's Confidence meter: the sidecar's own attribute grades. */
function fallbackGrades(s) {
  const n = { attested: 0, inferred: 0, reconstructed: 0 };
  for (const a of Object.values(s?.attributes ?? {})) {
    if (a && GRADES.includes(a.confidence)) n[a.confidence] += 1;
  }
  return n;
}

/** Who lives here, from the sidecar's households where there is no record: each person, with
 *  their own grade and role, as the card's "Who was here" lists them. */
function fallbackResidents(s) {
  const out = [];
  for (const h of Array.isArray(s?.residents) ? s.residents : []) {
    for (const person of Array.isArray(h?.persons) ? h.persons : []) {
      if (!person?.name) continue;
      const occ = person.occupation && !/^none/.test(String(person.occupation)) ? String(person.occupation).replace(/_/g, ' ') : '';
      const role = [occ,
        person.relationship && person.relationship !== 'head' ? String(person.relationship) : '',
        h.relation ? String(h.relation) : ''].filter(Boolean)[0] ?? '';
      out.push({ name: String(person.name), role, grade: person.grade ?? null });
    }
  }
  return out;
}

/** The front page's summary is at most 3 sentences and 60 words (§08). A building's own
 *  account longer than that stays on the full record, and the templated summary leads here. */
function fitsFrontPage(text) {
  const words = String(text).split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length;
  const sentences = (String(text).match(/[.!?](\s|$)/g) ?? []).length;
  return words <= 60 && sentences <= 3;
}

/** T-2636's opening for a building, or an empty one where the record has no sidecar. A
 *  helper rather than a ternary on the sidecar, so the sidecar-contract scanner (validate.py)
 *  does not take the opening's own fields for sidecar fields. */
function openingFor(sidecar, called) {
  if (!sidecar) return { title: called.title, address: '', aka: [], kind: [], lead: '', composed: true };
  return cardOpening(sidecar, called);
}

function render(root, ctx) {
  const doc = root.ownerDocument;
  const id = ctx.selected ?? ctx.target?.id ?? null;
  root.replaceChildren();
  root.dataset.structure = id ?? '';
  if (!id) {
    root.append(el(doc, 'p', 'nav-sub', 'Aim at a building, or tap one, to inspect it.'));
    return;
  }
  const record = ctx.actions?.record?.(id) ?? null;
  const s = record?.sidecar ?? null;
  const summaries = ctx.inspectDoc ?? null;
  const sum = summaries?.summaries?.[id] ?? null;
  const called = displayName(s ?? {}, id);
  const opening = openingFor(s, called);

  const page = el(doc, 'article', 'insp-page');
  page.dataset.source = sum ? 'record' : 'fallback';

  // 1. Plate.
  const plate = plateFor(ctx.picturesDoc, id);
  if (plate) {
    const fig = el(doc, 'figure', 'insp-plate');
    const img = el(doc, 'img');
    img.alt = `${plate.p.kind ?? 'Picture'} of ${sum?.name ?? opening.title}`;
    img.decoding = 'async';
    img.loading = 'lazy';
    img.src = plate.src;
    const cap = el(doc, 'figcaption', 'insp-credit',
      [plate.p.date, plate.p.creator ?? plate.p.holder].filter(Boolean).join(' · '));
    fig.append(img, cap);
    page.append(fig);
  }

  // 2. Address line, name, status chips.
  const address = sum?.address ?? opening.address;
  if (address) page.append(el(doc, 'p', 'insp-address', address));
  page.append(el(doc, 'h2', 'insp-name', sum?.name ?? opening.title));
  const chips = el(doc, 'ul', 'insp-chips');
  // The use chip's dot is the grade of the building's own `function`, which is that fact.
  const useGrade = s?.attributes?.function?.confidence ?? null;
  const chipList = sum
    ? [{ text: sum.status.text, grade: sum.status.grade },
      { text: `Built ${sum.built.year}`, grade: sum.built.grade },
      { text: sum.use, grade: useGrade }]
    : [...fallbackChips(s), ...(opening.kind[0] ? [{ text: opening.kind[0], grade: useGrade }] : [])];
  for (const c of chipList.filter((x) => x.text)) chips.append(line(doc, 'li', 'insp-chip', c.text, c.grade));
  if (chips.children.length) page.append(chips);

  // 3. Summary.
  let lead = sum?.summary ?? opening.lead;
  if (!sum && lead && !fitsFrontPage(lead)) {
    const today = s?.attributes?.present_status?.value ? String(s.attributes.present_status.value) : '';
    lead = fallbackSummary(s, { kind: opening.kind[0] ?? '', today }).text;
  }
  if (lead) {
    const p = el(doc, 'p', 'insp-summary', lead);
    if (!sum) p.dataset.composed = '';
    page.append(p);
  }

  // 4. Key facts.
  const key = sum?.key ?? [];
  if (key.length) {
    const dl = el(doc, 'dl', 'insp-key');
    for (const k of key) {
      const row = el(doc, 'div', 'insp-key-row');
      row.append(el(doc, 'dt', null, k.label), line(doc, 'dd', null, k.value, k.grade));
      dl.append(row);
    }
    page.append(dl);
  }

  // 5. Who lives here.
  const scene = String(ctx.scene?.id ?? ctx.scene?.scene_id ?? '');
  const people = sum ? (sum.residents ?? []).map((r) => ({ name: r.name, role: r.role, grade: r.grade }))
    : fallbackResidents(s);
  if (people.length) {
    const sec = el(doc, 'section', 'insp-sec insp-people');
    sec.append(heading(doc, scene ? `Who lives here · ${scene}` : 'Who lives here'));
    const ul = el(doc, 'ul', 'insp-list');
    for (const r of people.slice(0, MAX_RESIDENTS)) {
      const li = el(doc, 'li', 'insp-person');
      li.append(line(doc, 'strong', null, r.name, r.grade));
      if (r.role) li.append(el(doc, 'span', 'nav-sub', r.role));
      ul.append(li);
    }
    sec.append(ul);
    if (people.length > MAX_RESIDENTS) sec.append(el(doc, 'p', 'nav-sub insp-more', `+ ${people.length - MAX_RESIDENTS} more`));
    page.append(sec);
  }

  // 6. Look for (the camera move is T-2640's).
  const look = sum?.lookFor ?? [];
  if (look.length) {
    const sec = el(doc, 'section', 'insp-sec insp-look');
    sec.append(heading(doc, 'Look for'));
    const ul = el(doc, 'ul', 'insp-list');
    for (const l of look.slice(0, 3)) {
      const li = line(doc, 'li', 'insp-look-item', l.text, l.grade);
      li.dataset.feature = l.feature;
      ul.append(li);
    }
    sec.append(ul);
    page.append(sec);
  }

  // 7. Notable facts, swipeable.
  const notable = (sum?.notable ?? []).slice(0, MAX_NOTABLE);
  if (notable.length) {
    const sec = el(doc, 'section', 'insp-sec insp-notable');
    sec.append(heading(doc, 'Notable facts'));
    const track = el(doc, 'div', 'insp-swipe');
    track.setAttribute('role', 'list');
    notable.forEach((n, i) => {
      const card = line(doc, 'p', 'insp-fact', n.text, n.grade);
      card.setAttribute('role', 'listitem');
      card.setAttribute('aria-label', `${i + 1} of ${notable.length}`);
      track.append(card);
    });
    sec.append(track);
    if (notable.length > 1) sec.append(el(doc, 'p', 'nav-sub insp-swipe-hint', `${notable.length} facts · swipe`));
    page.append(sec);
  }

  // 8. The Confidence meter: tap opens the full record on its Evidence tab.
  const g = sum?.grades ?? fallbackGrades(s);
  const total = GRADES.reduce((n, k) => n + (g[k] ?? 0), 0);
  if (total) {
    const meter = el(doc, 'button', 'insp-meter');
    meter.type = 'button';
    const bar = el(doc, 'span', 'insp-meter-bar');
    for (const k of GRADES) {
      if (!g[k]) continue;
      const seg = el(doc, 'span', `insp-seg fact-${k}`);
      seg.style.flexGrow = String(g[k]);
      bar.append(seg);
    }
    const words = GRADES.filter((k) => g[k]).map((k) => `${g[k]} ${WORD[k]}`).join(' · ');
    meter.append(el(doc, 'span', 'nav-k', `Confidence · ${total} facts`), bar, el(doc, 'span', 'insp-meter-words', words));
    meter.setAttribute('aria-label', `${total} facts: ${words}. Open the sources.`);
    meter.addEventListener('click', () => ctx.actions?.openCard?.(id, 'evidence'));
    page.append(meter);
  }

  const full = el(doc, 'button', 'nav-tile insp-full', 'Full record');
  full.type = 'button';
  full.addEventListener('click', () => ctx.actions?.openCard?.(id));
  page.append(full);
  root.append(page);
  drawnFor = id;
}

async function refresh(root, ctx) {
  const id = ctx.selected ?? ctx.target?.id ?? null;
  // A different building: clear the last one now, so it never shows under the new name.
  if (root.dataset.structure !== (id ?? '')) {
    root.dataset.structure = id ?? '';
    root.replaceChildren(Object.assign(root.ownerDocument.createElement('p'), { className: 'nav-sub', textContent: 'Reading the record…' }));
  }
  // The summaries and the pictures are read once each, off the boot path; a building
  // without either still draws, from its sidecar.
  const [inspectDoc, picturesDoc] = await Promise.all([
    Promise.resolve(ctx.actions?.inspectSummaries?.()).catch(() => null),
    Promise.resolve(ctx.actions?.pictures?.()).catch(() => null),
  ]);
  if (root !== host) return;
  render(root, { ...ctx, inspectDoc, picturesDoc });
  if (id !== drawnFor) drawnFor = id;
}

export async function mount(el, ctx = {}) {
  host = el;
  await refresh(el, ctx);
}

/** Every time Inspect opens: draw the building in hand now, not the one it first opened on. */
export async function shown(el, ctx = {}) {
  host = el;
  await refresh(el, ctx);
}

export function unmount(el) {
  if (host === el) host = null;
  drawnFor = null;
  el.replaceChildren();
}

/** For the tests: the plate and grade helpers, pure. */
export const _test = { plateFor, fallbackChips, fallbackGrades, fallbackResidents };
