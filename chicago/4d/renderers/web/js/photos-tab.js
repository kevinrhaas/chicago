/**
 * photos-tab.js — Inspect's Photos tab (T-2645, NAV-510; DESIGN §08 "Photos").
 *
 * "A grid sorted by date, each with year, a caption and a 'from this spot' button. Group the
 * 162 images and show the 12 best first." It reads the card's own pictures file — the same
 * `pictures/<scene>.json` the card's Images tab (T-2389, pictures.js) reads, compiled by
 * tools/compile_pictures.py — so the two tabs cannot disagree about which pictures belong to
 * a building or how each is credited. Nothing loads until the tab opens; the thumbnails are
 * the store's small copies, lazily; a tap opens the card's own viewer with the full credit.
 *
 * WHAT IS SHOWN. Exactly what the Images tab shows as pictures: the ones the image store
 * holds, each with its credit (creator, else holder) on its tile. One with neither is not
 * shown as a picture but listed with the ones kept elsewhere, as links to their holders.
 *
 * EACH PICTURE CARRIES
 *   - its YEAR from the data (`years`, the library's own earliest and latest): "1888",
 *     "1887–1892", "1887 or later"; "Undated" where the data has no year. Never guessed.
 *   - a CAPTION templated from its recorded view and kind ("The back, a photo."), never cut
 *     from its archival title, which is a catalogue line. The full title is in the viewer.
 *   - its CREDIT.
 *   - "FROM THIS SPOT" only where a solved camera of this building (data/reference_views/,
 *     the image gate) records where it was taken (`spot`). It stands the visitor there,
 *     facing the way the camera faced, with Show me's glide (show-me.js; a cut with reduced
 *     motion). On foot, at eye height: the camera's own height is not used.
 *
 * THE 12 BEST, AND THE RULE (ported from the prepared tools/compile_photos.py). Each shown
 * picture is keyed, in order: has a spot (so From this spot works); its period (in-period,
 * near-period, later — the library's own reading); its year's distance from the scene year,
 * nearest first, undated last; its kind (photographs, then prints, then drawings); its id.
 * Then VIEWPOINTS IN TURN: grouped by view, views ordered by their best picture, and taken
 * round-robin — each view's best, then each view's second — so forty photographs of one
 * corner still leave room for the other sides. The best are shown by date; "All N" shows
 * every picture by date.
 */
import { t } from './strings/index.js';
import './strings/photos.js';

export const BEST = 12;

const VIEW_KEY = {
  'front elevation': 'front', 'oblique front': 'corner', 'side elevation': 'side', rear: 'rear',
  'entrance detail': 'entrance', detail: 'detail', 'roof detail': 'roof', courtyard: 'court',
  'courtyard detail': 'court-detail', 'street view': 'street', aerial: 'aerial', plan: 'plan',
  section: 'section', interior: 'interior',
};
const KIND_KEY = {
  PHOTO: 'photo', STEREO: 'stereo', POSTCARD: 'postcard', AERIAL: 'aerial', ENGRAVING: 'engraving',
  LITHO: 'litho', PLATE: 'plate', ILLUSTRATION: 'illustration', DRAWING: 'drawing',
  'MEASURED DWG': 'measured', "BIRD'S-EYE": 'birdseye', NEWSPAPER: 'newspaper',
};
const KIND_ORDER = { PHOTO: 0, STEREO: 0, POSTCARD: 0, AERIAL: 0, DRAWING: 2, 'MEASURED DWG': 2 };
const PERIOD_ORDER = { 'in-period': 0, 'near-period': 1, later: 2 };
const DEG = Math.PI / 180;

const int = (x) => (Number.isInteger(x) ? x : null);

/** [earliest, latest] the data records, either of them null. */
export function yearsOf(p) {
  const y = Array.isArray(p?.years) ? p.years : [];
  return [int(y[0]), int(y[1])];
}

/** The year as a visitor reads it, from the data only. */
export function yearLabel(p) {
  const [lo, hi] = yearsOf(p);
  if (lo == null && hi == null) return t('photos.undated');
  if (lo == null) return t('photos.year.before', { hi });
  if (hi == null) return t('photos.year.after', { lo });
  return lo === hi ? String(lo) : t('photos.year.range', { lo, hi });
}

/** The year a picture sorts and ranks by: its earliest, else its latest; null if undated. */
function sortYear(p) {
  const [lo, hi] = yearsOf(p);
  return lo ?? hi;
}

/** The templated caption: what the picture shows and what kind of picture it is. */
export function captionOf(p) {
  const subject = t(`photos.view.${VIEW_KEY[p?.view] ?? 'other'}`);
  const noun = t(`photos.kind.${KIND_KEY[p?.kind] ?? 'other'}`);
  return t('photos.cap', { subject, noun });
}

/** The tile's credit: its creator, else its holder (the holder's first clause). */
export function creditOf(p) {
  const holder = String(p?.holder ?? '').split(' — ')[0].trim();
  return String(p?.creator ?? '').trim() || holder || '';
}

/** A recorded spot, or null: a solved camera's position and heading in the footprint frame. */
export function spotOf(p) {
  const s = p?.spot;
  if (!s || ![s.u, s.v, s.bearing].every(Number.isFinite)) return null;
  return { u: s.u, v: s.v, bearing: s.bearing, pitch: Number.isFinite(s.pitch) ? s.pitch : 0 };
}

/**
 * Where From this spot stands the visitor: the spot carried from the building's footprint
 * frame into the field by its placement (the same turn walker.js and navigation.js give a
 * footprint: clockwise from north by `rotation_deg`), facing the camera's bearing turned
 * the same way. Null without a spot or a placement.
 */
export function spotTarget(p, placement) {
  const s = spotOf(p);
  if (!s || !placement || !Number.isFinite(placement.local_e) || !Number.isFinite(placement.local_n)) return null;
  const turn = Number.isFinite(placement.rotation_deg) ? placement.rotation_deg : 0;
  const cos = Math.cos(turn * DEG), sin = Math.sin(turn * DEG);
  return {
    e: placement.local_e + s.u * cos + s.v * sin,
    n: placement.local_n - s.u * sin + s.v * cos,
    yaw: (((s.bearing + turn) % 360) + 360) % 360,
    pitch: Math.max(-60, Math.min(60, s.pitch)),
  };
}

function rankKey(p, sceneYear) {
  const y = sortYear(p);
  return [spotOf(p) ? 0 : 1, PERIOD_ORDER[p.period] ?? 1,
    y == null || !Number.isFinite(sceneYear) ? 9999 : Math.abs(y - sceneYear), KIND_ORDER[p.kind] ?? 1];
}

function compareKeys(a, b) {
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  return 0;
}

const byId = (a, b) => (String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0);

/** By date: earliest first, then latest, undated last, then id. */
export function byDate(a, b) {
  const ya = sortYear(a) ?? Infinity, yb = sortYear(b) ?? Infinity;
  if (ya !== yb) return ya - yb;
  const ha = yearsOf(a)[1] ?? ya, hb = yearsOf(b)[1] ?? yb;
  if (ha !== hb) return (ha ?? Infinity) - (hb ?? Infinity);
  return byId(a, b);
}

/** The best `n` by the rule in the header: ranked, then viewpoints in turn. */
export function chooseBest(list, sceneYear, n = BEST) {
  const ranked = [...list].sort((a, b) => compareKeys(rankKey(a, sceneYear), rankKey(b, sceneYear)) || byId(a, b));
  const queues = new Map();
  for (const p of ranked) {
    const v = p.view ?? '';
    if (!queues.has(v)) queues.set(v, []);
    queues.get(v).push(p);
  }
  const picked = [];
  while (picked.length < n && [...queues.values()].some((q) => q.length)) {
    for (const q of queues.values()) if (q.length && picked.length < n) picked.push(q.shift());
  }
  return picked;
}

const storeUrl = (doc, file) => {
  const base = doc?.image_store?.base_url;
  if (!base || !file) return null;
  try { return new URL(file, base).href; } catch { return null; }
};

/**
 * One building's Photos tab, as data: `all` (every shown picture by date), `best` (up to
 * 12, by date), `links` (the rest, kept by their holders). Each shown entry carries `at`,
 * its place in the card viewer's sequence (pictures.js: the file's held pictures, in order).
 * Null when the pictures file is not in hand.
 */
export function photosTab(doc, id, sceneYear) {
  if (!doc || typeof doc !== 'object' || !doc.by_structure) return null;
  const list = Array.isArray(doc.by_structure[id]) ? doc.by_structure[id] : [];
  const held = list.filter((p) => p.held && storeUrl(doc, p.held.t));
  const shown = [], links = [];
  held.forEach((p, at) => { if (creditOf(p)) shown.push({ ...p, at }); else links.push(p); });
  for (const p of list) if (!held.includes(p)) links.push(p);
  const best = chooseBest(shown, Number(sceneYear)).sort(byDate);
  return { count: shown.length, all: [...shown].sort(byDate), best, links: links.sort(byDate) };
}

function el(doc, tag, cls, text) {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function tile(doc, pics, p, { onSpot }) {
  const li = el(doc, 'li', 'ph-item');
  li.dataset.photo = p.id;
  const caption = captionOf(p);
  const year = yearLabel(p);
  const open = el(doc, 'button', 'ph-tile');
  open.type = 'button';
  open.dataset.pic = String(p.at);
  open.setAttribute('aria-label', t('photos.open', { caption: `${year}. ${caption}` }));
  const img = el(doc, 'img', 'ph-thumb');
  img.alt = caption;
  img.decoding = 'async';
  img.loading = 'lazy';
  img.src = storeUrl(pics, p.held.t);
  const badge = el(doc, 'span', 'ph-year', year);
  if (sortYear(p) == null) { badge.dataset.undated = ''; badge.title = t('photos.year.none'); }
  open.append(img, badge);
  li.append(open, el(doc, 'p', 'ph-cap', caption), el(doc, 'p', 'ph-credit', creditOf(p)));
  if (spotOf(p) && onSpot) {
    const b = el(doc, 'button', 'ph-spot', t('photos.spot'));
    b.type = 'button';
    b.setAttribute('aria-label', t('photos.spot.label', { caption }));
    b.addEventListener('click', () => onSpot(p));
    li.append(b);
  }
  return li;
}

/**
 * Fill a Photos pane. Returns false (and leaves the pane alone) when the pictures file is
 * not in hand, so the caller can fall back to the card's own Images pane.
 *
 * @param {Element} pane
 * @param {object} o
 * @param {object|null} o.doc  the scene's pictures file
 * @param {string} o.id  the structure
 * @param {number|string} o.sceneYear
 * @param {(p: object) => void} [o.onSpot]  From this spot, for a picture with a spot
 */
export function renderPhotos(pane, { doc: pics, id, sceneYear, onSpot = null }) {
  const tab = photosTab(pics, id, sceneYear);
  if (!tab) return false;
  const doc = pane.ownerDocument;
  const sec = el(doc, 'section', 'insp-sec ph-sec');
  sec.dataset.photos = String(tab.count);
  sec.append(el(doc, 'h3', 'insp-h', t('photos.title')));
  if (!tab.count && !tab.links.length) {
    sec.append(el(doc, 'p', 'nav-sub', t('photos.none')));
    pane.append(sec);
    return true;
  }
  if (tab.count) {
    const status = el(doc, 'p', 'nav-sub ph-status');
    const grid = el(doc, 'ul', 'ph-grid');
    let showingAll = false;
    const draw = () => {
      const list = showingAll || tab.count <= BEST ? tab.all : tab.best;
      grid.replaceChildren(...list.map((p) => tile(doc, pics, p, { onSpot })));
      grid.dataset.showing = showingAll ? 'all' : 'best';
      status.textContent = t(showingAll || tab.count <= BEST ? 'photos.status.all' : 'photos.status.best',
        { n: showingAll || tab.count <= BEST ? tab.count : tab.best.length });
    };
    draw();
    sec.append(status, grid);
    if (tab.count > BEST) {
      const more = el(doc, 'button', 'nav-tile ph-all', t('photos.all', { n: tab.count }));
      more.type = 'button';
      more.setAttribute('aria-expanded', 'false');
      more.addEventListener('click', () => {
        showingAll = !showingAll;
        draw();
        more.textContent = showingAll ? t('photos.best', { n: tab.best.length }) : t('photos.all', { n: tab.count });
        more.setAttribute('aria-expanded', String(showingAll));
      });
      sec.append(more);
    }
  }
  if (tab.links.length) {
    const det = el(doc, 'details', 'ph-links');
    const sum = el(doc, 'summary', 'insp-h', `${t('photos.links.title')} · ${tab.links.length}`);
    det.append(sum, el(doc, 'p', 'nav-sub', t('photos.links.note')));
    const ol = el(doc, 'ol', 'ph-link-list');
    for (const p of tab.links) {
      const li = el(doc, 'li');
      const label = `${yearLabel(p)} · ${captionOf(p)}`;
      if (/^https?:\/\//.test(String(p.url ?? ''))) {
        const a = el(doc, 'a', null, label);
        a.href = p.url;
        a.target = '_blank';
        a.rel = 'noopener';
        li.append(a);
      } else li.append(el(doc, 'span', null, label));
      // A linked picture has no local viewer exposing its catalogue title. Keep
      // the templated caption, but retain the source's identity/date qualifiers.
      if (String(p.title ?? '').trim()) li.append(el(doc, 'span', 'nav-sub', p.title));
      li.append(el(doc, 'span', 'nav-sub', creditOf(p) || t('photos.credit.none')));
      // Creator and holder answer different questions. Show the holder as well
      // when a creator exists; its first clause avoids local-copy locators.
      const holder = String(p.holder ?? '').split(' — ')[0].trim();
      if (String(p.creator ?? '').trim() && holder && holder !== creditOf(p)) {
        li.append(el(doc, 'span', 'nav-sub', holder));
      }
      ol.append(li);
    }
    det.append(ol);
    sec.append(det);
  }
  pane.append(sec);
  return true;
}
