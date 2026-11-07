/**
 * T-2641 — Inspect's Design tab (design doc "Field Navigator Mk II" §08 "Design", mockup M8;
 * §12 "Style library"). T-3435 (the owner, 2026-11-06) made it a written STYLE GUIDE for every
 * building, the same shape on every card, top to bottom:
 *
 *   THE GUIDE (style-guide.js): a head naming the style where a module or the summary's key
 *   names one (else what the building is), its chips, a lead of up to three graded sentences,
 *   Look for, then Shape · Walls · Roof · Windows and doors · Grounds — always all five — and
 *   what the model was built from. Every line is filled from the building's own graded record.
 *
 *   LOOK FOR: a record's authored `onThisHouse` items where an author wrote them (the compiler
 *   holds each that names a sidecar attribute to that attribute's grade); one whose record names
 *   a camera is a button that turns the camera there with Show me (T-2640). A reconstructed item
 *   that names a liberty says "Listed in Liberties." Elsewhere, the guide's own highlights.
 *   The old dump of every sidecar attribute is gone from here: it is the Details tab's list.
 *
 *   ABOUT THE STYLE: the style module exactly as written (data/styles/<id>.json, gated by
 *   tools/compile_summaries.py into inspect/<scene>.json `styles`): its two lines, up to four
 *   "How to spot it" cues and a credited plate where the pictures file holds a copy that may be
 *   shown. COMPARE STYLES: up to three lines; one that points at another module opens that
 *   style's own lines and cues in place (T-2642).
 *
 * The model (`designModel`) is pure and separate from drawing it (`renderDesign`), so the test
 * drives both with fakes.
 */
import { t } from './strings/index.js';
import './strings/inspect-design.js';
import { claimValueText } from './claim-value.js';
import { cameraOf } from './show-me.js';
import { yearLabel, creditOf } from './photos-tab.js';
import { styleGuide } from './style-guide.js';

const GRADES = ['attested', 'inferred', 'reconstructed'];
const SHOWN_RIGHTS = /^(public domain|no known restrictions)/i;
/** Plain names for the commonest sidecar attributes; the rest are spelled out from the key. */
const LABELS = { construction: 'Built of', stories: 'Storeys', storeys: 'Storeys', function: 'Use', roof_type: 'Roof' };
const UNITS = { m: ' m', ft: ' ft', deg: '°' };

function graded(g) {
  return GRADES.includes(g) ? g : null;
}

/** An attribute key as a visitor reads it: 'roof_pitch_deg' → 'Roof pitch'. */
export function labelOf(key) {
  if (LABELS[key]) return LABELS[key];
  const parts = String(key).split('_').filter(Boolean);
  if (parts.length > 1 && UNITS[parts.at(-1)]) parts.pop();
  const words = parts.join(' ');
  return words ? words[0].toUpperCase() + words.slice(1) : '';
}

/** An attribute's value as a visitor reads it, with its unit: '35°', '2.5 m', 'log'. A
 *  structured value has no printable form here (claim-value.js) and prints nothing. */
export function valueOf(key, value) {
  const text = claimValueText(value);
  if (text == null || text === '—') return '';
  const unit = UNITS[String(key).split('_').at(-1)];
  return unit && typeof value === 'number' ? `${text}${unit}` : text;
}

/** The style module a record names, or null. */
export function styleFor(sum, styles) {
  const id = sum?.style;
  return (typeof id === 'string' && styles?.[id]) || null;
}

/** The module's plate, from the scene's pictures file, or null where it holds no copy that may be shown. */
export function plateOf(plate, pictures, sceneId) {
  if (!plate || String(plate.scene) !== String(sceneId ?? '')) return null;
  const base = pictures?.image_store?.base_url;
  const p = (pictures?.by_structure?.[plate.structure] ?? []).find((x) => x.id === plate.picture);
  if (!base || !p?.held?.f || !SHOWN_RIGHTS.test(String(p.rights ?? ''))) return null;
  let src;
  try { src = new URL(p.held.f, base).href; } catch { return null; }
  const year = yearLabel(p);
  return { src, caption: plate.caption, credit: [creditOf(p), year === 'Undated' ? '' : year].filter(Boolean).join(' · '), grade: graded(plate.grade) };
}

/** The numbered hotspots: the record's own, else the sidecar's shape and attributes. */
export function hotspots(sum, sidecar) {
  const authored = Array.isArray(sum?.onThisHouse) ? sum.onThisHouse : [];
  let items;
  let source;
  if (authored.length) {
    source = 'record';
    items = authored.map((h) => ({ text: h.text, detail: h.detail ?? '', grade: graded(h.grade),
      liberty: !!h.liberty && h.grade === 'reconstructed', camera: cameraOf(h) ? h.camera : null, feature: h.feature ?? null }));
  } else {
    source = 'sidecar';
    items = [];
    const fp = sidecar?.footprint;
    if (fp && graded(fp.confidence)) items.push({ text: t('inspect-design.shape'), detail: '', grade: fp.confidence });
    for (const [key, a] of Object.entries(sidecar?.attributes ?? {})) {
      if (!a || typeof a !== 'object' || !graded(a.confidence)) continue;
      items.push({ text: labelOf(key), detail: valueOf(key, a.value), grade: a.confidence });
    }
    items = items.map((h) => ({ ...h, liberty: false, camera: null, feature: null }));
  }
  items = items.filter((h) => h.grade && h.text).map((h, i) => ({ ...h, n: i + 1 }));
  return { source, items, tap: items.some((h) => h.camera) };
}

/** T-2642: the other module a Compare line points at, as the line opens it in place — its two
 *  lines and its cues, each graded — or null where the line names no module this file carries
 *  (or names the card's own). Its plate stays on its own card. */
export function compareCard(line, mod, styles) {
  const other = typeof line?.style === 'string' && line.style !== mod?.id ? styles?.[line.style] : null;
  if (!other || typeof other !== 'object') return null;
  return {
    id: other.id ?? line.style,
    name: other.name,
    description: other.description ? { text: other.description.text, grade: graded(other.description.grade) } : null,
    cues: (other.cues ?? []).slice(0, 4).map((c) => ({ text: c.text, grade: graded(c.grade) })),
  };
}

/** Everything the Design tab shows for one building: the written guide (style-guide.js, every
 *  building), the style module's card where one is named, and the record's own authored
 *  "On this house" items (which replace the guide's derived Look for, and can Show me). */
export function designModel({ sum = null, sidecar = null, styles = null, pictures = null, scene = null } = {}) {
  const mod = styleFor(sum, styles);
  const sceneId = scene?.id ?? scene?.scene_id ?? scene ?? null;
  const style = mod ? {
    id: mod.id,
    name: mod.name,
    description: mod.description ? { text: mod.description.text, grade: graded(mod.description.grade) } : null,
    cues: (mod.cues ?? []).slice(0, 4).map((c) => ({ text: c.text, grade: graded(c.grade) })),
    plate: plateOf(mod.plate, pictures, sceneId),
    compare: (mod.compare ?? []).slice(0, 3).map((c) => ({ name: c.name, text: c.text, grade: graded(c.grade), style: c.style ?? null,
      card: compareCard(c, mod, styles) })),
  } : null;
  const hot = hotspots(sum, sidecar);
  // T-3435: the sidecar's attribute list is the Details tab's now; only an author's items show here.
  const authored = hot.source === 'record' ? hot : { source: 'guide', items: [], tap: false };
  return { style, hot: authored, guide: styleGuide({ sidecar, sum, mod }) };
}

/** The five parts' glyphs: single-colour line icons, drawn in currentColor. */
const PART_ICON = {
  shape: '<path d="M4 8l8-4 8 4v8l-8 4-8-4z"/><path d="M4 8l8 4 8-4M12 12v8"/>',
  walls: '<path d="M3 5h18v14H3z"/><path d="M3 9.7h18M3 14.3h18M9 5v4.7M15 5v4.7M6 9.7v4.6M12 9.7v4.6M18 9.7v4.6M9 14.3V19M15 14.3V19"/>',
  roof: '<path d="M2 13 12 5l10 8"/><path d="M5 11v8h14v-8"/>',
  openings: '<path d="M6 3h12v18H6z"/><path d="M12 3v18M6 12h12"/>',
  grounds: '<path d="M4 20V8l2-3 2 3v12M16 20V8l2-3 2 3v12"/><path d="M8 11h8M8 16h8"/>',
};

/**
 * Draw the model. `dot(doc, grade)` is Inspect's grade dot; `onLook(item)` runs Show me for a
 * hotspot whose record names a camera (no button is drawn without it).
 */
export function renderDesign(doc, model, { dot, onLook = null } = {}) {
  const el = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const mark = (n, grade) => { if (grade && dot) n.append(dot(doc, grade)); return n; };
  // A graded line whose last word and dot stay together at a wrap (the card's own fact-tail).
  const tailed = (tag, cls, text, grade) => {
    const words = String(text).split(' ');
    const last = words.pop();
    const n = el(tag, cls, words.length ? `${words.join(' ')} ` : '');
    n.append(mark(el('span', 'sg-tail', last), grade));
    return n;
  };
  const svg = (paths) => {
    const i = el('span', 'sg-icon');
    i.setAttribute('aria-hidden', 'true');
    i.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
    return i;
  };
  const root = el('div', 'insp-design');
  const st = model.style;
  const g = model.guide ?? styleGuide({});
  root.dataset.style = st?.id ?? '';

  // The head: kicker, the style's (or the building's) name, what it is, and its chips.
  const head = el('header', 'sg-head');
  head.append(el('p', 'insp-kicker', t('inspect-design.kicker')), mark(el('h3', 'sg-name', g.name.text), g.name.grade));
  if (g.sub) head.append(mark(el('p', 'sg-sub', g.sub.text), g.sub.grade));
  if (g.chips.length) {
    const ul = el('ul', 'insp-chips sg-chips');
    for (const c of g.chips) {
      const li = el('li', 'insp-chip', c.k === 'built' ? t('inspect-design.chip.built', { year: c.text }) : c.text);
      li.dataset.k = c.k;
      ul.append(mark(li, c.grade));
    }
    head.append(ul);
  }
  root.append(head);

  // The lead: up to three sentences, each with its own grade.
  if (g.lead.length) {
    const p = el('p', 'sg-lead');
    for (const l of g.lead) p.append(tailed('span', 'sg-sentence', l.text, l.grade));
    root.append(p);
  }

  // Look for: the author's numbered items where written (Show me where a camera is named),
  // else the features that set this building apart.
  const hot = model.hot ?? { items: [] };
  const looks = hot.items.length ? hot.items : g.look.map((h, i) => ({ ...h, n: i + 1, camera: null, liberty: false, feature: null }));
  if (looks.length) {
    const sec = el('section', 'sg-look');
    sec.dataset.source = hot.items.length ? 'record' : 'guide';
    sec.append(el('h4', 'insp-h', t(hot.tap && onLook ? 'inspect-design.look.tap' : 'inspect-design.look')));
    const ol = el('ol', 'insp-hotspots sg-look-list');
    ol.setAttribute('aria-label', t('inspect-design.look.label'));
    for (const h of looks) {
      const li = el('li', 'insp-hot');
      li.dataset.n = String(h.n);
      li.dataset.grade = h.grade ?? '';
      if (h.feature) li.dataset.feature = h.feature;
      const live = h.camera && onLook;
      const body = el(live ? 'button' : 'div', 'insp-hot-row');
      if (live) {
        body.type = 'button';
        body.setAttribute('aria-label', t('inspect-design.look.go', { text: h.text }));
        body.addEventListener('click', () => onLook(h));
      }
      const words = el('span', 'insp-hot-body');
      words.append(mark(el('strong', 'insp-hot-text', h.text), h.grade));
      if (h.detail || h.liberty) {
        const d = el('span', 'insp-hot-detail', h.detail);
        if (h.liberty) d.append(el('span', 'insp-hot-lib', `${h.detail ? ' ' : ''}${t('inspect-design.liberty')}`));
        words.append(d);
      }
      body.append(el('span', 'insp-hot-n', String(h.n)), words);
      li.append(body);
      ol.append(li);
    }
    sec.append(ol);
    root.append(sec);
  }

  // The five parts, always all five and always in this order, so every card reads alike.
  const parts = el('div', 'sg-parts');
  for (const part of g.parts) {
    const box = el('section', 'sg-part');
    box.dataset.part = part.key;
    const h = el('h4', 'sg-part-h');
    h.append(svg(PART_ICON[part.key] ?? ''), el('span', null, t(`inspect-design.part.${part.key}`)));
    box.append(h);
    if (part.lines.length) {
      const ul = el('ul', 'sg-lines');
      for (const l of part.lines) ul.append(tailed('li', 'sg-line', l.text, l.grade));
      box.append(ul);
    } else {
      box.dataset.empty = '';
      box.append(el('p', 'sg-none', t('inspect-design.part.none')));
    }
    parts.append(box);
  }
  root.append(parts);

  // What the model was built from, in the structure grade's own words.
  if (g.basis) {
    const note = el('aside', 'sg-basis');
    note.dataset.grade = g.basis.grade;
    note.append(el('p', 'insp-kicker', t('inspect-design.basis')), tailed('p', 'sg-basis-text', g.basis.text, g.basis.grade));
    if (g.basis.draft) note.append(el('p', 'sg-basis-draft', t('inspect-design.basis.draft')));
    root.append(note);
  }

  // The style module: its own two lines, plate and cues.
  if (st) {
    const card = el('section', 'insp-style');
    card.append(el('p', 'insp-kicker', t('inspect-design.about.style')), el('h4', 'insp-style-name', st.name));
    if (st.description?.text) card.append(mark(el('p', 'insp-style-desc', st.description.text), st.description.grade));
    if (st.plate) {
      const fig = el('figure', 'insp-plate insp-style-plate');
      const img = el('img');
      img.alt = t('inspect-design.plate.alt', { caption: st.plate.caption });
      img.decoding = 'async';
      img.loading = 'lazy';
      img.src = st.plate.src;
      const cap = el('figcaption', 'insp-style-cap');
      cap.append(mark(el('span', 'insp-style-cap-text', st.plate.caption), st.plate.grade));
      if (st.plate.credit) cap.append(el('span', 'insp-credit', st.plate.credit));
      fig.append(img, cap);
      card.append(fig);
    }
    if (st.cues.length) {
      card.append(el('h4', 'insp-h', t('inspect-design.cues')));
      const ul = el('ul', 'insp-cues');
      for (const c of st.cues) ul.append(mark(el('li', 'insp-cue', c.text), c.grade));
      card.append(ul);
    }
    root.append(card);
  }

  if (st?.compare?.length) {
    const cmp = el('section', 'insp-sec insp-compare');
    cmp.append(el('h4', 'insp-h', t('inspect-design.compare')));
    const ul = el('ul', 'insp-list');
    for (const c of st.compare) {
      const li = el('li', 'insp-compare-item');
      if (c.style) li.dataset.style = c.style;
      li.append(mark(el('strong', 'insp-compare-name', c.name), c.grade), el('span', 'nav-sub', c.text));
      // T-2642: a line that points at another module opens that style's own card in place.
      if (c.card) {
        const more = el('details', 'insp-compare-more');
        more.dataset.style = c.card.id;
        more.append(el('summary', 'insp-compare-open', t('inspect-design.compare.open', { name: c.card.name })));
        if (c.card.description?.text) more.append(mark(el('p', 'insp-compare-desc', c.card.description.text), c.card.description.grade));
        if (c.card.cues.length) {
          const cues = el('ul', 'insp-cues insp-compare-cues');
          for (const q of c.card.cues) cues.append(mark(el('li', 'insp-compare-cue', q.text), q.grade));
          more.append(cues);
        }
        li.append(more);
      }
      ul.append(li);
    }
    cmp.append(ul);
    root.append(cmp);
  }

  // Where to read more: every fact with its grade, and where each one came from.
  const more = el('nav', 'sg-more');
  for (const [key, label] of [['details', 'inspect-design.more.details'], ['sources', 'inspect-design.more.sources']]) {
    const b = el('button', 'nav-tile sg-go', t(label));
    b.type = 'button';
    b.dataset.inspGo = key;
    more.append(b);
  }
  root.append(more);
  return root;
}
