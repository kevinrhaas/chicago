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
 * THE TABS (T-2639, §08 "Tabs"): Overview · People · Design · Story · Photos · Sources, and
 * Research with Expert research on (T-3022: the floating card's evidence, liberties and
 * record, folded in; the card itself no longer opens on a building). A new
 * building always opens on Overview; the same building keeps its tab. People and Design are
 * the card's own content for now, rendered by popup.js `sections()` from the same renderers
 * and loaded state as the card, so the two cannot disagree while the card still exists
 * (Design fills in under T-2642). Photos is its own grid (T-2645, photos-tab.js), from the
 * card's own pictures file. Story is its own timeline
 * (T-2643, js/inspect-story.js): BUILT, YOU ARE HERE and TODAY from the record's dated facts,
 * filtered to the scene's era. Sources has its own layout (T-2644, inspect-sources.js):
 * every fact grouped by grade, Liberties as a section, human source titles, the full citation
 * folded under each fact; the Confidence meter counts the same facts, so the meter and the
 * tab it opens agree. Each pane is built the first time its tab opens. People lists the
 * card's "who was here" exactly as the card does (review notes included), each household
 * with a way into the People app; a scene whose sidecar lists nobody here (1904) lists the
 * people directory's residents of this building instead (T-2702).
 */
import { cardOpening } from '../popup.js';
import { displayName } from '../display-name.js';
import { fallbackSummary } from '../fallback-summary.js';
import { builtPhrase } from '../range-words.js';
import { hydratePictures } from '../pictures.js';
import { renderPhotos } from '../photos-tab.js';
import { cameraOf } from '../show-me.js';
import { buildingFacts, factCounts, sourcesPaneHtml } from '../inspect-sources.js';
import { storyTimeline, renderStory } from '../inspect-story.js';
import { count as countField } from '../field-log.js'; // T-2660
import { designModel, renderDesign } from '../inspect-design.js';
import { MODE_ATTR } from '../researcher.js';
import { personModel, renderPersonCard } from '../person-card.js';

const GRADES = ['attested', 'inferred', 'reconstructed'];
const WORD = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const GLOSS = { attested: 'a source says so', inferred: 'worked out from clues', reconstructed: 'built so the street makes sense' };
const SHOWN_RIGHTS = /^(public domain|no known restrictions)/i;
const MAX_RESIDENTS = 3;
const MAX_NOTABLE = 3;

let host = null;
let drawnFor = null;
let lastTab = 'overview';
let tabFor = null;            // the building the remembered tab belongs to
let personLinked = null;      // the last link whose person card was opened (T-3265)
const TABS = [['overview', 'Overview'], ['people', 'People'], ['design', 'Design'],
  ['story', 'Story'], ['photos', 'Photos'], ['sources', 'Sources'], ['research', 'Research']];
/** T-3022: the tabs only Expert research shows (Settings; js/researcher.js). They are drawn
 *  for every building and marked `data-researcher`, so the switch shows or hides them in place. */
const EXPERT_TABS = new Set(['research']);
const expertOn = (doc) => !!doc?.documentElement?.hasAttribute?.(MODE_ATTR);

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
  // T-3037: the build date as its sources give it — "Built 1886", "Built 1864 or 1875".
  const built = builtPhrase(s?.attributes?.built?.value).replace(/^in /, '');
  if (built) out.push({ text: `Built ${built}`, grade: s.attributes.built.confidence });
  return out;
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
  countField('inspect'); // T-2660: the first since landing is the field log's
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
      { text: `Built ${sum.built.phrase ?? sum.built.year}`, grade: sum.built.grade },
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
      // T-2640: Show me, only where the record names a camera for this feature.
      if (cameraOf(l) && ctx.actions?.showMe) {
        const b = el(doc, 'button', 'insp-showme', 'Show me');
        b.type = 'button';
        b.setAttribute('aria-label', `Show me: ${l.text}`);
        b.addEventListener('click', () => {
          // On a phone the device steps down so the turn is in view.
          if (['half', 'full'].includes(ctx.navigator?.detent)) ctx.navigator?.dock?.();
          void ctx.actions.showMe(id, l);
        });
        li.append(b);
      }
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

  // 8. The Confidence meter: every fact the Sources tab lists, by grade (T-2644). Tap opens it.
  const g = factCounts(buildingFacts(s, sum));
  const total = g.total;
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
    meter.setAttribute('aria-label', `${total} facts: ${words}. Open Sources.`);
    meter.addEventListener('click', () => selectTab(root, 'sources'));
    page.append(meter);
  }

  // T-3022: the full record is Inspect's own Research tab now, shown with Expert research on
  // (Settings); the floating card no longer opens from here.
  const full = el(doc, 'button', 'nav-tile insp-full', 'Research');
  full.type = 'button';
  full.setAttribute('data-researcher', '');
  full.setAttribute('aria-label', 'Open the Research tab: the evidence, liberties and record');
  full.addEventListener('click', () => { selectTab(root, 'research'); root.scrollTop = 0; });
  page.append(full);

  // The tabs. A new building opens on Overview; the same building keeps its tab.
  // A deep link (?nav=inspect:<id>&tab=, T-2621) opens its tab the first time this building
  // draws; after that the visitor's own choice is kept.
  const linked = ctx.link?.app === 'inspect' && ctx.link.id === id && TABS.some(([k]) => k === ctx.link.tab) ? ctx.link.tab : null;
  let tab = tabFor === id ? lastTab : (linked ?? 'overview');
  if (EXPERT_TABS.has(tab) && !expertOn(doc)) tab = 'overview';
  // T-3265: a link to a person (the People app, a map pin) opens People on their card, once.
  const person = ctx.link?.app === 'inspect' && ctx.link.id === id && ctx.link.person && ctx.link !== personLinked
    ? ctx.link.person : null;
  if (person) { personLinked = ctx.link; tab = 'people'; }
  tabFor = id;
  const bar = el(doc, 'nav', 'insp-tabs');
  bar.setAttribute('role', 'tablist');
  bar.setAttribute('aria-label', 'About this building');
  const panes = el(doc, 'div', 'insp-panes');
  for (const [key, label] of TABS) {
    const b = el(doc, 'button', 'insp-tab', label);
    b.type = 'button';
    b.dataset.inspTab = key;
    b.setAttribute('role', 'tab');
    b.id = `insp-tab-${key}`;
    b.setAttribute('aria-controls', `insp-pane-${key}`);
    if (EXPERT_TABS.has(key)) b.setAttribute('data-researcher', '');
    bar.append(b);
    const pane = el(doc, 'section', `insp-pane${key === 'overview' ? '' : ' insp-card-pane'}`);
    pane.id = `insp-pane-${key}`;
    pane.dataset.inspPane = key;
    pane.setAttribute('role', 'tabpanel');
    pane.setAttribute('aria-labelledby', b.id);
    if (key === 'overview') pane.append(page);
    panes.append(pane);
  }
  // T-3021 (the owner, 2026-10-22: "you cant navigate back from here in the building view"):
  // Back and the tabs ride one bar pinned to the top of the screen, so neither scrolls away.
  const head = el(doc, 'div', 'insp-bar');
  const to = ctx.navigator?.backTo?.() ?? null;
  if (to) {
    const back = el(doc, 'button', 'insp-back');
    back.type = 'button';
    back.dataset.inspBack = '';
    back.setAttribute('aria-label', `Back to ${to.label}`);
    back.title = `Back to ${to.label}`;
    back.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5-7 7 7 7"/></svg>';
    head.append(back);
  }
  head.append(bar);
  root.append(head, panes);
  root._insp = { id, sum, ctx, person };
  selectTab(root, tab);
  drawnFor = id;
}

// Who was here: the order a household is listed in (T-3258).
const RANK = { head: 0, wife: 1, husband: 1, son: 2, daughter: 2, child: 2, servant: 4 };

/** Show one tab; build its pane the first time. */
function selectTab(root, key) {
  if (!TABS.some(([k]) => k === key)) return;
  if (EXPERT_TABS.has(key) && !expertOn(root.ownerDocument)) key = 'overview';
  // T-2660: a tab the visitor moved to (the first draw selects one, and is not counted).
  const was = root.querySelector('.insp-tab[aria-selected="true"]')?.dataset.inspTab ?? null;
  if (was && was !== key) countField('tab');
  lastTab = key;
  for (const b of root.querySelectorAll('.insp-tab')) {
    const on = b.dataset.inspTab === key;
    b.setAttribute('aria-selected', String(on));
    b.tabIndex = on ? 0 : -1;
  }
  for (const pane of root.querySelectorAll('.insp-pane')) pane.hidden = pane.dataset.inspPane !== key;
  const pane = root.querySelector(`.insp-pane[data-insp-pane="${key}"]`);
  if (pane && key !== 'overview' && !pane.dataset.filled) void fillPane(root, pane, key);
}

async function fillPane(root, pane, key) {
  const { id, sum, ctx } = root._insp ?? {};
  if (!id) return;
  const doc = root.ownerDocument;
  pane.dataset.filled = 'pending';
  pane.replaceChildren(el(doc, 'p', 'nav-sub', 'Reading the record…'));
  let sec = null;
  try { sec = await ctx.actions?.cardSections?.(id); } catch { sec = null; }
  if (root._insp?.id !== id) return; // the building changed while this was read
  pane.replaceChildren();
  if (!sec) {
    pane.append(el(doc, 'p', 'nav-sub', 'This record could not be read.'));
    pane.dataset.filled = 'failed';
    return;
  }
  const html = (s) => { const d = el(doc, 'div', 'insp-card'); d.innerHTML = s; return d; };
  if (key === 'people') await fillPeople(pane, sec, ctx, id);
  else if (key === 'story') {
    // T-2643: BUILT, YOU ARE HERE and TODAY on one timeline, from the record's own dated facts,
    // the modelled phase and (1835 only) the fire limit; another scene's era never renders.
    const record = ctx.actions?.record?.(id) ?? null;
    pane.append(renderStory(doc, storyTimeline({ sum, sidecar: record?.sidecar ?? null, scene: ctx.scene, fireLimit: sec.fireLimit }), dot));
  } else if (key === 'design') {
    // T-2641: the style card, the numbered "On this house" hotspots with grades (replacing the
    // card's attribute table) and Compare styles (inspect-design.js); Show me where a hotspot's
    // record names a camera.
    const onLook = ctx.actions?.showMe ? (h) => {
      if (['half', 'full'].includes(ctx.navigator?.detent)) ctx.navigator?.dock?.();
      void ctx.actions.showMe(id, h);
    } : null;
    pane.append(renderDesign(doc, designModel({ sum, sidecar: ctx.actions?.record?.(id)?.sidecar ?? null,
      styles: ctx.inspectDoc?.styles ?? null, pictures: ctx.picturesDoc, scene: ctx.scene }), { dot, onLook }));
  } else if (key === 'sources') {
    const d = el(doc, 'div', 'insp-sources');
    d.innerHTML = sourcesPaneHtml({
      sidecar: ctx.actions?.record?.(id)?.sidecar ?? null,
      summary: sum ?? null,
      docSources: ctx.inspectDoc?.sources ?? null,
      liberties: sec.liberties ?? null,
      questions: sec.questions ?? null,
      dossier: sec.dossier ?? null,
      // T-2644: "from the time" only of a source dated by the scene's year.
      sourceDates: ctx.inspectDoc?.source_dates ?? null,
      sceneYear: ctx.inspectDoc?.scene ?? ctx.scene?.id ?? null,
    });
    pane.append(d);
  } else if (key === 'research') {
    // T-3022: the floating card's research, folded in — its flags and facts block, then its
    // Sources, Liberties and Record panes, each built by the card's own renderers (popup.js
    // `researchPanes`), so the two cannot disagree while the card still serves streets and trees.
    const r = sec.research;
    const d = el(doc, 'div', 'insp-card insp-research');
    if (!r) {
      d.append(el(doc, 'p', 'nav-sub', 'No research record for this building.'));
    } else {
      const fold = (label, count, inner, open) => `<details class="insp-fold"${open ? ' open' : ''}><summary>${label}${
        count ? ` <span class="pop-count">${count}</span>` : ''}</summary><div class="pop-pane">${inner}</div></details>`;
      d.innerHTML = `${r.head}${r.facts}${fold('Sources', 0, r.evidence, true)}${
        fold('Liberties', r.libertyCount, r.liberties, false)}${fold('Record', 0, r.record, false)}`;
    }
    pane.append(d);
  } else if (key === 'photos') {
    // T-2645: the Photos tab (photos-tab.js), from the card's own pictures file; the card's
    // Images pane where that file is not in hand.
    const onSpot = ctx.actions?.fromSpot ? (p) => {
      if (['half', 'full'].includes(ctx.navigator?.detent)) ctx.navigator?.dock?.();
      void ctx.actions.fromSpot(id, p);
    } : null;
    if (!renderPhotos(pane, { doc: ctx.picturesDoc, id, sceneYear: ctx.scene?.id ?? ctx.scene?.scene_id, onSpot })) {
      const d = html(sec.photos);
      pane.append(d);
      hydratePictures(d);
    }
  } else {
    pane.append(html(sec[key]));
  }
  pane.dataset.filled = 'yes';
}

/** People: the card's own "who was here" where the record seats anyone, with a way into the
 *  People app; else the directory's residents of this building (1904). */
async function fillPeople(pane, sec, ctx, id) {
  const doc = pane.ownerDocument;
  let dir = null;
  try { dir = await ctx.actions?.peopleDirectory?.(); } catch { dir = null; }
  const rows = Array.isArray(dir?.people) ? dir.people : [];
  if (sec.hasResidents) {
    const d = el(doc, 'div', 'insp-card');
    d.innerHTML = sec.people;
    pane.append(d);
    const links = el(doc, 'div', 'insp-people-links');
    for (const h of sec.households) {
      const person = rows.find((r) => r.household && r.household === h.household && r.relationship === 'head')
        ?? rows.find((r) => r.household && r.household === h.household);
      if (!person) continue;
      const b = el(doc, 'button', 'nav-tile insp-person-link', `${h.name || 'This household'} in People`);
      b.type = 'button';
      b.dataset.person = person.id;
      links.append(b);
    }
    if (links.children.length) pane.append(links);
    return;
  }
  const here = rows.filter((r) => r.lives_at === id || r.works_at === id);
  if (sec.people.includes('pop-flag')) { const f = el(doc, 'div', 'insp-card'); f.innerHTML = sec.people; pane.append(f); }
  if (!here.length) {
    pane.append(el(doc, 'p', 'nav-sub', 'Nobody in our records lives or works here.'));
    return;
  }
  const block = el(doc, 'section', 'insp-sec insp-people-home');
  block.append(heading(doc, 'Who was here'));
  // T-3265: a tap opens that person's own card here, in place of this list, with Back to it.
  pane._people = new Map(here.map((r) => [r.id, r]));
  // T-3258: the family before its staff — head, spouse, children, kin, then the servants the
  // 1900 census names — so a house of twelve servants still opens on the people it is named for.
  const order = (r) => RANK[r.relationship] ?? 3;
  for (const r of [...here].sort((a, b) => order(a) - order(b) || a.name.localeCompare(b.name))) {
    const b = el(doc, 'button', 'nav-person insp-person-link');
    b.type = 'button';
    b.dataset.personCard = r.id;
    b.append(line(doc, 'span', 'nav-person-name', r.name, r.grade),
      el(doc, 'span', 'nav-sub', [r.household_name, r.relationship === 'head' ? 'head of the household' : r.relationship].filter(Boolean).join(' · ')));
    block.append(b);
  }
  pane.append(block);
  const linked = pane.closest('.insp-panes')?.parentElement?._insp?.person;
  if (linked && pane._people.has(linked)) void openPersonCard(pane, linked, ctx);
}

/**
 * T-3265: one person's card in place of the household list (person-card.js). It draws at once
 * from the directory's row, then again once their household's record and the scene's
 * citations are read; Back puts the list back, on the row just read.
 */
async function openPersonCard(pane, personId, ctx) {
  const doc = pane.ownerDocument;
  const row = pane._people?.get(personId);
  const home = pane.querySelector('.insp-people-home');
  if (!row || !home) return false;
  pane.querySelector('.insp-person-card')?.remove();
  const sceneYear = Number(String(ctx?.scene?.id ?? ctx?.scene?.scene_id ?? '').slice(0, 4)) || null;
  const draw = (m) => {
    const card = renderPersonCard(doc, m, { dot });
    const was = pane.querySelector('.insp-person-card');
    if (was) was.replaceWith(card); else pane.append(card);
    return card;
  };
  home.hidden = true;
  pane.dataset.person = personId;
  const first = draw(personModel({ row, sceneYear }));
  const scroller = pane.closest('.insp-panes')?.parentElement;
  if (scroller) scroller.scrollTop = 0;
  first.querySelector('[data-person-back]')?.focus?.({ preventScroll: true });
  const [household, citations] = await Promise.all([
    Promise.resolve(ctx?.actions?.householdRecord?.(row.file)).catch(() => null),
    Promise.resolve(ctx?.actions?.residentCitations?.()).catch(() => null),
  ]);
  if (pane.dataset.person !== personId) return false; // Back, or another person, in the meantime
  const person = (household?.persons ?? []).find((p) => p.id === personId) ?? null;
  const card = draw(personModel({ row, person, household, citations, sceneYear }));
  if (!person) card.querySelector('.insp-person-wait')?.replaceWith(el(doc, 'p', 'nav-sub', 'This person\u2019s household record could not be read.'));
  if (doc.activeElement === doc.body || !doc.activeElement) card.querySelector('[data-person-back]')?.focus?.({ preventScroll: true });
  return true;
}

/** Back from a person's card to their household's list, on their row. */
function closePersonCard(pane) {
  const id = pane.dataset.person;
  delete pane.dataset.person;
  pane.querySelector('.insp-person-card')?.remove();
  const home = pane.querySelector('.insp-people-home');
  if (home) home.hidden = false;
  const row = id ? pane.querySelector(`[data-person-card="${CSS.escape(id)}"]`) : null;
  row?.scrollIntoView?.({ block: 'center' });
  row?.focus?.({ preventScroll: true });
}

/** Clicks inside Inspect: tabs, the card's own "why" toggles, a picture, a person. */
function onClick(e) {
  const root = e.currentTarget;
  const st = root._insp ?? {};
  if (e.target.closest('[data-insp-back]')) { void st.ctx?.navigator?.back?.(); return; }
  const card = e.target.closest('[data-person-card]');
  if (card) { void openPersonCard(card.closest('.insp-pane'), card.dataset.personCard, st.ctx); return; }
  if (e.target.closest('[data-person-back]')) { closePersonCard(e.target.closest('.insp-pane')); return; }
  const tab = e.target.closest('[data-insp-tab]');
  if (tab) {
    selectTab(root, tab.dataset.inspTab);
    // A tab opens at its top, under the pinned bar, not where the last one was scrolled to.
    root.scrollTop = 0;
    return;
  }
  if (e.target.closest('[data-insp-full]') && st.id) { st.ctx?.actions?.openCard?.(st.id); return; }
  const toggle = e.target.closest('[data-toggle-note]');
  if (toggle) {
    const note = toggle.parentElement.querySelector('[data-note]');
    if (!note) return;
    const shown = !note.hasAttribute('hidden');
    note.toggleAttribute('hidden', shown);
    toggle.textContent = shown ? 'why' : 'hide';
    return;
  }
  const pic = e.target.closest('[data-pic]');
  if (pic && st.id) { st.ctx?.actions?.openPicture?.(st.id, Number(pic.dataset.pic) || 0); return; }
  const person = e.target.closest('[data-person]');
  if (person) st.ctx?.actions?.openPerson?.(person.dataset.person);
}

async function refresh(root, ctx) {
  const id = ctx.selected ?? ctx.target?.id ?? null;
  // Hold this building while Inspect is open, and on a phone close the card, which would
  // otherwise cover the device (T-2639).
  if (id) ctx.actions?.holdInspect?.(id);
  if (ctx.isPhone) ctx.actions?.closeCard?.();
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
  el.addEventListener('click', onClick);
  await refresh(el, ctx);
}

/** Every time Inspect opens: draw the building in hand now, not the one it first opened on. */
export async function shown(el, ctx = {}) {
  host = el;
  await refresh(el, ctx);
}

export function unmount(el) {
  el.removeEventListener('click', onClick);
  if (host === el) host = null;
  drawnFor = null;
  el.replaceChildren();
}

/** For the tests: the plate and grade helpers, pure. */
export const _test = { plateFor, fallbackChips, fallbackResidents };
