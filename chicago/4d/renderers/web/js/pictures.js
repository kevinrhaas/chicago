/**
 * pictures.js — the building card's Images tab (T-2389).
 *
 * The owner, 2026-10-11: "As you build each once can you include those photos images of
 * the house on the card for the house on another tab", then "Like thumbnails of all
 * Images for each and you can review and open them". The pictures are the ones the
 * project already builds against: the Prairie library's records, with their copies in
 * the public image store, and the photograph and illustration sources a structure record
 * cites. `tools/compile_pictures.py` joins them to the structures and publish.sh ships
 * one slim file per scene (`data/pictures/<scene>.json`), fetched the first time a card
 * is drawn, never at boot.
 *
 * So the pane is a grid of every held picture's thumbnail, and a tap opens the viewer:
 * the full-size copy, its whole credit, and arrows through the rest. A picture that is
 * not held is listed as a link to its holder, never hot-linked.
 *
 * EVERY PICTURE SHOWN CARRIES ITS CREDIT, on the tile and in full in the viewer: a
 * reference copy is kept in the store on the owner's terms (credit shown wherever it is).
 *
 * PHONE MEMORY. Kevin tests on an iPhone, where a killed tab is the failure that matters.
 * No <img> carries a `src` until the Images pane is open (`hydratePictures`); the grid is
 * the store's thumbnails (≤480 px), loaded lazily as they scroll in; the viewer holds ONE
 * full-size copy at a time and drops it when it closes.
 */

import { escapeHtml } from './citations.js';

const storeUrl = (doc, file) => {
  const base = doc?.image_store?.base_url;
  if (!base || !file) return null;
  try { return new URL(file, base).href; } catch { return null; }
};

/** The pictures a scene's file holds for one structure; [] when none, null when not loaded. */
export function picturesFor(doc, id) {
  if (!doc || typeof doc !== 'object' || !doc.by_structure) return null;
  const list = doc.by_structure[id];
  return Array.isArray(list) ? list : [];
}

/** The held pictures, in the file's order — the grid and the viewer's sequence. */
function heldOf(doc, id) {
  return (picturesFor(doc, id) ?? []).filter((p) => p.held && storeUrl(doc, p.held.t));
}

/**
 * A plate for a Jaunt's card (T-2631): the first held picture of the first of `ids` (its
 * stops' buildings, in order) that has one, with its credit — a picture is never shown
 * without it. Null where none of them has a held picture: the card keeps its family
 * icon, never a stand-in picture.
 */
export function plateFor(doc, ids = []) {
  for (const id of ids) {
    const p = heldOf(doc, id)[0];
    if (!p) continue;
    const holder = String(p.holder ?? '').split(' — ')[0].trim();
    return {
      src: storeUrl(doc, p.held.t),
      alt: `${p.kind ?? 'Picture'}: ${p.title ?? p.id}`,
      credit: holder || 'holder not recorded',
      full: [p.title, p.creator, [p.holder, p.collection].filter(Boolean).join(' · '), rightsLabel(p)].filter(Boolean).join(' — '),
      structure: id,
    };
  }
  return null;
}

/** The rights line, in the card's terse register. */
function rightsLabel(p) {
  const r = String(p.rights ?? '').toLowerCase();
  if (r.startsWith('pending')) return 'RIGHTS PENDING';
  if (r.startsWith('public domain')) return 'PUBLIC DOMAIN';
  if (r.startsWith('no known')) return 'NO KNOWN RESTRICTIONS';
  if (p.reference_copy) return 'REFERENCE COPY · RIGHTS HELD BY HOLDER';
  if (r) return r.replace(/\s*—\s*link only$/, '').toUpperCase();
  return 'RIGHTS NOT RECORDED';
}

function libraryLink(doc, p) {
  if (!p.library || !doc?.library_viewer) return null;
  return `${doc.library_viewer}#image=${encodeURIComponent(p.id)}`;
}

/** The full credit for one picture — what the viewer shows under the image. */
function creditHtml(doc, p) {
  const links = [
    p.url ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">HOLDER ↗</a>` : '',
    libraryLink(doc, p) ? `<a href="${escapeHtml(libraryLink(doc, p))}" target="_blank" rel="noopener">LIBRARY ↗</a>` : '',
  ].filter(Boolean).join('');
  const holder = [p.holder, p.collection].filter(Boolean).join(' · ');
  return `<p class="pop-pic-kind">${escapeHtml([p.kind, p.view, p.date].filter(Boolean).join(' · '))}</p>
    <p class="pop-pic-title">${escapeHtml(p.title ?? p.id)}</p>
    <p class="pop-pic-credit">${p.creator ? `${escapeHtml(p.creator)}<br>` : ''}${
      holder ? escapeHtml(holder) : 'holder not recorded'}</p>
    <p class="pop-pic-rights">${escapeHtml(rightsLabel(p))}</p>
    ${links ? `<p class="pop-pic-links">${links}</p>` : ''}`;
}

/** A thumbnail that loads only once its pane is open: the URL waits in data-src. */
function thumbImg(doc, p, open) {
  const src = storeUrl(doc, p.held?.t);
  const alt = `${p.kind ?? 'Picture'}: ${p.title ?? p.id}`;
  return `<img class="pop-pic-thumb" alt="${escapeHtml(alt)}" decoding="async" loading="lazy" ${
    open ? 'src' : 'data-src'}="${escapeHtml(src ?? '')}">`;
}

/**
 * The Images pane for one building.
 *
 * @param {object|null} doc  the scene's pictures file; null while not loaded
 * @param {string} id  the structure
 * @param {object} opts
 * @param {boolean} opts.open  the pane is the one showing, so images may load now
 * @param {boolean} [opts.failed]  the file could not be fetched
 */
export function picturesPaneHtml(doc, id, { open, failed = false } = {}) {
  const list = picturesFor(doc, id);
  if (list === null) {
    return `<section class="pop-sec pop-pics"><h3>Pictures of this building</h3>
      <p class="pop-lib-none">${failed ? 'IMAGE INDEX OFFLINE — pictures could not be loaded.' : 'LOADING IMAGE INDEX…'}</p></section>`;
  }
  if (!list.length) {
    return `<section class="pop-sec pop-pics"><h3>Pictures of this building</h3>
      <p class="pop-lib-none">NO PICTURE ON FILE. No photograph or drawing of this building is
        held or cited yet; when a build finds one, it appears here.</p></section>`;
  }
  const held = heldOf(doc, id);
  const linked = list.filter((p) => !held.includes(p));
  const status = [`${list.length} ON FILE`, held.length ? `${held.length} HELD` : '',
    linked.length ? `${linked.length} LINK ONLY` : ''].filter(Boolean).join(' · ');

  const grid = held.length ? `<p class="pop-pic-hint">TAP A PICTURE TO OPEN IT</p>
    <ul class="pop-pic-grid">${held.map((p, i) => `
      <li><button type="button" class="pop-pic-tile" data-pic="${i}"
        aria-label="${escapeHtml(`Open ${p.kind ?? 'picture'}: ${p.title ?? p.id}`)}">
        ${thumbImg(doc, p, open)}
        <span class="pop-pic-tile-kind">${escapeHtml([p.kind, (p.date ?? '').slice(0, 14)].filter(Boolean).join(' · '))}</span>
        <span class="pop-pic-tile-credit">${escapeHtml(p.creator ?? p.holder ?? 'holder not recorded')}</span>
      </button></li>`).join('')}</ul>` : '';
  const links = linked.length ? `<h3 class="pop-pic-sub">Link only <span class="pop-count">${linked.length}</span></h3>
    <ol class="pop-pic-list">${linked.map((p) => `<li>
      ${p.url ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.title ?? p.id)}</a>`
        : escapeHtml(p.title ?? p.id)}
      <span class="pop-pic-meta">${escapeHtml([p.kind, p.date, p.creator, p.holder].filter(Boolean).join(' · '))}
        · ${escapeHtml(rightsLabel(p))}</span></li>`).join('')}</ol>` : '';

  return `<section class="pop-sec pop-pics" data-pics-for="${escapeHtml(id)}">
    <h3>Pictures of this building</h3>
    <p class="pop-pic-status">${escapeHtml(status)}</p>
    ${grid}${links}
    <p class="pop-pic-foot">Each picture is credited to its holder; HOLDER opens the original
      where it is kept.</p>
  </section>`;
}

/** Load the pane's thumbnails: called when the Images tab opens. */
export function hydratePictures(root) {
  for (const img of root.querySelectorAll('[data-pop-pane="images"] img[data-src]')) {
    const src = img.getAttribute('data-src');
    img.removeAttribute('data-src');
    if (src) img.setAttribute('src', src);
  }
}

/**
 * The viewer: one full-size picture over the scene, its whole credit, and arrows through
 * the building's other held pictures. One element for the page, made on first use.
 */
let viewer = null;
function viewerEl() {
  if (viewer) return viewer;
  viewer = document.createElement('div');
  viewer.className = 'pic-viewer';
  viewer.setAttribute('role', 'dialog');
  viewer.setAttribute('aria-modal', 'true');
  viewer.setAttribute('aria-label', 'Picture');
  viewer.hidden = true;
  viewer.innerHTML = `<div class="pic-viewer-bar">
      <span class="pic-viewer-count" data-pv-count></span>
      <a class="pic-viewer-full" data-pv-full target="_blank" rel="noopener">FULL SIZE ↗</a>
      <button type="button" class="pic-viewer-close" data-pv-close aria-label="Close">✕</button>
    </div>
    <div class="pic-viewer-stage">
      <button type="button" class="pic-viewer-step" data-pv-step="-1" aria-label="Previous picture">‹</button>
      <img class="pic-viewer-img" data-pv-img alt="" decoding="async">
      <button type="button" class="pic-viewer-step" data-pv-step="1" aria-label="Next picture">›</button>
    </div>
    <div class="pic-viewer-credit" data-pv-credit></div>`;
  document.body.appendChild(viewer);
  viewer.addEventListener('click', (e) => {
    if (e.target.closest('[data-pv-close]') || e.target === viewer) { closePictureViewer(); return; }
    const step = e.target.closest('[data-pv-step]');
    if (step) viewerShow(viewer._at + Number(step.dataset.pvStep));
  });
  document.addEventListener('keydown', (e) => {
    if (viewer.hidden) return;
    if (e.key === 'Escape') { e.stopPropagation(); closePictureViewer(); }
    else if (e.key === 'ArrowRight') { e.stopPropagation(); viewerShow(viewer._at + 1); }
    else if (e.key === 'ArrowLeft') { e.stopPropagation(); viewerShow(viewer._at - 1); }
  }, true);
  return viewer;
}

function viewerShow(i) {
  const v = viewer;
  const list = v._list;
  if (!list?.length) return;
  const at = (i + list.length) % list.length;
  const p = list[at];
  v._at = at;
  const img = v.querySelector('[data-pv-img]');
  const thumb = storeUrl(v._doc, p.held.t);
  const full = storeUrl(v._doc, p.held.f) ?? thumb;
  // The thumbnail first (already loaded by the grid), then the full copy over it once it
  // has arrived, so a slow link shows the picture at once and sharpens. One full copy at
  // a time: a step away abandons the one still loading.
  img.src = thumb;
  img.alt = `${p.kind ?? 'Picture'}: ${p.title ?? p.id}`;
  if (full !== thumb) {
    const pre = new Image();
    pre.decoding = 'async';
    pre.onload = () => { if (!v.hidden && v._list?.[v._at] === p) img.src = full; };
    pre.src = full;
  }
  v.querySelector('[data-pv-full]').href = full;
  v.querySelector('[data-pv-count]').textContent = `${at + 1} / ${list.length}`;
  v.querySelector('[data-pv-credit]').innerHTML = creditHtml(v._doc, p);
  for (const b of v.querySelectorAll('[data-pv-step]')) b.hidden = list.length < 2;
}

/** Open the viewer on held picture `i` of a building. */
export function openPictureViewer(doc, id, i) {
  const list = heldOf(doc, id);
  if (!list.length) return;
  const v = viewerEl();
  v._doc = doc;
  v._list = list;
  v.hidden = false;
  document.documentElement.classList.add('pic-viewer-open');
  viewerShow(Number(i) || 0);
  v.querySelector('[data-pv-close]').focus({ preventScroll: true });
}

/** Close it and let the full-size copy go. */
export function closePictureViewer() {
  if (!viewer || viewer.hidden) return;
  viewer.hidden = true;
  viewer._list = null;
  viewer.querySelector('[data-pv-img]').removeAttribute('src');
  document.documentElement.classList.remove('pic-viewer-open');
}
