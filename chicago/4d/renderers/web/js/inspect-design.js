/**
 * T-2641 — Inspect's Design tab (design doc "Field Navigator Mk II" §08 "Design", mockup M8;
 * §12 "Style library" and "Attribute table → Design hotspots"). Top to bottom:
 *
 *   THE STYLE CARD. The building's summary record names a style module (`style`, an id), which
 *   tools/compile_summaries.py gates from data/styles/<id>.json and carries into every scene's
 *   inspect/<scene>.json under `styles`. The card is that module exactly as written: its name,
 *   a two-line description, up to four "How to spot it" cues and a credited reference plate,
 *   each graded. A cue the sources do not support is left out of the module, so a card may
 *   show fewer than four. The plate shows only where the scene's pictures file holds a copy
 *   whose rights allow display; its credit is the pictures file's own (creator and year).
 *   A building with no module says so in one line and shows no card — nothing is composed.
 *
 *   ON THIS HOUSE: numbered hotspots, each with its grade dot. A record's `onThisHouse` items
 *   are shown as authored (the compiler holds each one that names a sidecar attribute to that
 *   attribute's own grade); one whose record names a camera is a button, and tapping it turns
 *   the camera there with Show me (T-2640) — never aimed where the record names none. A
 *   reconstructed hotspot that names a liberty says "Listed in Liberties." Every other
 *   building shows its own sidecar instead: its shape on the ground, then each attribute in
 *   the sidecar's order, as a plain label and value with that attribute's grade — the old
 *   attribute table, moved down into the same numbered list, with no table. An attribute
 *   with no grade is not listed (every hotspot has a dot); the full record still shows it.
 *
 *   COMPARE STYLES: the module's own lines, up to three, each graded.
 *
 * The model (`designModel`) is pure and separate from drawing it (`renderDesign`), so the test
 * drives both with fakes.
 */
import { t } from './strings/index.js';
import './strings/inspect-design.js';
import { claimValueText } from './claim-value.js';
import { cameraOf } from './show-me.js';
import { yearLabel, creditOf } from './photos-tab.js';

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

/** Everything the Design tab shows for one building. */
export function designModel({ sum = null, sidecar = null, styles = null, pictures = null, scene = null } = {}) {
  const mod = styleFor(sum, styles);
  const sceneId = scene?.id ?? scene?.scene_id ?? scene ?? null;
  const style = mod ? {
    id: mod.id,
    name: mod.name,
    description: mod.description ? { text: mod.description.text, grade: graded(mod.description.grade) } : null,
    cues: (mod.cues ?? []).slice(0, 4).map((c) => ({ text: c.text, grade: graded(c.grade) })),
    plate: plateOf(mod.plate, pictures, sceneId),
    compare: (mod.compare ?? []).slice(0, 3).map((c) => ({ name: c.name, text: c.text, grade: graded(c.grade), style: c.style ?? null })),
  } : null;
  return { style, hot: hotspots(sum, sidecar) };
}

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
  const root = el('div', 'insp-design');
  const st = model.style;
  root.dataset.style = st?.id ?? '';
  if (st) {
    const card = el('section', 'insp-style');
    card.append(el('p', 'insp-kicker', t('inspect-design.kicker')), el('h3', 'insp-style-name', st.name));
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
  } else {
    root.append(el('p', 'nav-sub insp-style-none', t('inspect-design.style.none')));
  }

  const hot = model.hot;
  const sec = el('section', 'insp-sec insp-hot-sec');
  sec.dataset.source = hot.source;
  sec.append(el('h3', 'insp-h', t(hot.tap && onLook ? 'inspect-design.hotspots.tap' : 'inspect-design.hotspots')));
  if (hot.items.length) {
    const ol = el('ol', 'insp-hotspots');
    ol.setAttribute('aria-label', t('inspect-design.hotspots.label'));
    for (const h of hot.items) {
      const li = el('li', 'insp-hot');
      li.dataset.n = String(h.n);
      li.dataset.grade = h.grade;
      if (h.feature) li.dataset.feature = h.feature;
      const live = h.camera && onLook;
      const body = el(live ? 'button' : 'div', 'insp-hot-row');
      if (live) {
        body.type = 'button';
        body.setAttribute('aria-label', t('inspect-design.hotspot.look', { text: h.text }));
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
  } else {
    sec.append(el('p', 'nav-sub', t('inspect-design.hotspots.none')));
  }
  root.append(sec);

  if (st?.compare?.length) {
    const cmp = el('section', 'insp-sec insp-compare');
    cmp.append(el('h3', 'insp-h', t('inspect-design.compare')));
    const ul = el('ul', 'insp-list');
    for (const c of st.compare) {
      const li = el('li', 'insp-compare-item');
      if (c.style) li.dataset.style = c.style;
      li.append(mark(el('strong', 'insp-compare-name', c.name), c.grade), el('span', 'nav-sub', c.text));
      ul.append(li);
    }
    cmp.append(ul);
    root.append(cmp);
  }
  return root;
}
