// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * person-settings.js — the Settings card's You tab (T-3644): the visitor's own person.
 *
 * Kevin, 2026-11-17: "you will need to provide options for users in settings to change the gender
 * appearance dress, etc. this becomes a person builder eventually but the foundation starts with
 * customizing the default person". The tab shows the person (person-portrait.js, the figure the
 * town draws) and beside it their face up close (Kevin, 2026-11-19: "the face would be nice in
 * addition to the body to see the face up close"), what they are in a line, and "Edit your
 * person": the character creator (person-creator.js; Kevin, 2026-11-27, "much more rich with more
 * preview simpler buttons ... best practice build your character style interfaces from aaa
 * games"), where the body type (Kevin, 2026-11-19: named for the person's style, not their
 * gender, with a third type), age, complexion, face library, eyes, hair, whiskers and the year's
 * dress are chosen. Every change is the person's at once: a figure already in the saddle is
 * re-made.
 * The lists come from data/humans/visitor_person.json; nothing here names an id of its own.
 */
import { faceChoices } from './visitor-person.js';

/**
 * Swatch colours for the complexions: a light skin as the portrait's light shows it (linear)
 * under each tint (human-looks.js COMPLEXION_TINT), as sRGB. A swatch, not a measurement.
 */
const SKIN_LINEAR = [0.787, 0.477, 0.342];
const toSrgb = (v) => (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);
export function swatchColour(tint, skin = SKIN_LINEAR) {
  if (!Array.isArray(tint)) return null;
  const c = skin.map((v, k) => Math.max(0, Math.min(1, toSrgb(v * tint[k]))));
  return `rgb(${c.map((v) => Math.round(v * 255)).join(', ')})`;
}

const el = (doc, tag, props = {}, kids = []) => {
  const n = doc.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k.startsWith('data-') || k.startsWith('aria-') || k === 'role' || k === 'for') n.setAttribute(k, v);
    else n[k] = v;
  }
  for (const kid of kids) if (kid) n.append(kid);
  return n;
};

/**
 * The builder's place: `#s-person` under the "Your person" heading, in the You tab's group
 * (`.settings-group[data-set-pane="you"]`, put before Show's first group), all made here, once:
 * the page carries none of it (index.html sits at validate.py's 64 KB duplicate floor). The group
 * starts hidden unless You is the tab open; settings-app.js shows it with its tab from then on.
 */
export function personHost(doc = globalThis.document) {
  const found = doc?.getElementById?.('s-person');
  if (found) return found;
  let group = doc?.querySelector?.('.settings-group[data-set-pane="you"]');
  if (!group) {
    const show = doc?.querySelector?.('.settings-group[data-set-pane="show"]');
    if (!show) return null;
    group = el(doc, 'div', { class: 'settings-group', 'data-set-pane': 'you' });
    group.hidden = doc.querySelector?.('[data-set-tab="you"]')?.getAttribute?.('aria-selected') !== 'true';
    show.before(group);
  }
  const host = el(doc, 'div', { class: 'person-builder', id: 's-person' }, [
    el(doc, 'p', { class: 'legend-note', text: 'Your person loads with the town.' })]);
  group.append(el(doc, 'h4', { text: 'Your person' }), host);
  return host;
}

/**
 * Fill `#s-person`: the person's portrait and face, what they are in a line, and the button that
 * opens the character creator (person-creator.js, loaded on that click), where every choice is
 * made. `person` is visitor-person.js's; `year` the scene's; `portrait` person-portrait.js's (or
 * null: no picture, the creator still works); `tints` the complexion tints and `eyes` the eye
 * colours (human-looks.js COMPLEXION_TINT, EYE_COLOUR).
 */
export function wirePersonSettings({ doc = globalThis.document, person, year, portrait = null, tints = {}, eyes = {},
  loadCreator = () => import('./person-creator.js') }) {
  const host = personHost(doc);
  if (!host || !person) return null;
  const C = person.catalog;
  host.replaceChildren();
  if (!(C.years ?? []).includes(String(year))) {
    host.append(el(doc, 'p', { class: 'legend-note', text: `Your person is drawn in ${(C.years ?? []).join(', ')}.` }));
    return null;
  }

  // The portrait and beside it the face up close: a tap on either opens the creator there.
  const canvas = el(doc, 'canvas', { class: 'person-portrait', width: 240, height: 360, 'aria-label': 'Your person' });
  const pic = el(doc, 'button', { type: 'button', class: 'person-pic', title: 'Edit your person', 'aria-label': 'Edit your person' }, [canvas]);
  const faceCanvas = el(doc, 'canvas', { class: 'person-portrait person-face-close', width: 240, height: 240, 'aria-label': 'Your face, close' });
  const facePic = el(doc, 'button', { type: 'button', class: 'person-pic person-face-pic', title: 'Edit your face', 'aria-label': 'Edit your face' }, [faceCanvas]);
  const status = el(doc, 'p', { class: 'legend-note person-status', role: 'status' });
  const summary = el(doc, 'p', { class: 'person-summary' });
  pic.addEventListener('click', () => void openCreator('body'));
  facePic.addEventListener('click', () => void openCreator('face'));
  host.append(el(doc, 'div', { class: 'person-stage' }, [el(doc, 'div', { class: 'person-pics' }, [pic, facePic]), summary, status]));
  if (!portrait) pic.hidden = facePic.hidden = true;

  const edit = el(doc, 'button', { type: 'button', class: 'person-edit', text: 'Edit your person' });
  const reset = el(doc, 'button', { type: 'button', class: 'setting-button person-reset', text: 'Start again' });
  edit.addEventListener('click', () => void openCreator());
  reset.addEventListener('click', () => person.reset());
  host.append(el(doc, 'div', { class: 'person-actions' }, [edit, reset]));
  host.append(el(doc, 'p', { class: 'legend-note', text: 'You ride as this person. Kept on this device, and with your sign-in when you have one. Liberty: nobody of the town; dress and looks are drawn from the year\'s own people.' }));

  // The creator, made on its first opening. While it is up, this tab's pictures wait for it.
  let creator = null, making = null, held = false;
  async function openCreator(tab) {
    making ??= loadCreator().then(({ createPersonCreator }) => createPersonCreator({ doc, person, year, portrait, tints, eyes,
      skin: (tint) => swatchColour(tint),
      onOpen: () => { held = true; },
      onClose: () => { held = false; edit.focus?.(); if (dirty || !seen || inView) { dirty = false; void paint(); } } }));
    creator = await making;
    creator?.open(tab);
    return creator;
  }

  function show(choice = person.choice) {
    summary.textContent = summaryLine(C, choice, person.year(year));
  }

  let painting = null, again = false;
  async function paint() {
    if (!portrait) return;
    if (held) { dirty = true; return; }
    if (painting) { again = true; return painting; }
    status.textContent = 'Drawing…';
    painting = portrait.draw(canvas, { year, turn: 0 })
      .then(async (ok) => {
        // The face from the same figure: one more render, no second build.
        if (ok && !facePic.hidden) ok = await portrait.draw(faceCanvas, { year, turn: FACE_TURNS[1], frame: 'face' }).catch(() => false) && ok;
        status.textContent = ok ? '' : 'Your person is drawn when the town\'s people have loaded.';
        if (ok) canvas.dataset.drawn = faceCanvas.dataset.drawn = String(Date.now());
      })
      .catch((e) => { status.textContent = 'Could not draw your person here.'; console.warn('[4D Chicago] person portrait', e); })
      .finally(() => { painting = null; if (again) { again = false; void paint(); } });
    return painting;
  }

  // Drawn only while the tab is in view, and again when the person changes while it is.
  let dirty = true, inView = false;
  const seen = typeof IntersectionObserver === 'function' ? new IntersectionObserver((entries) => {
    inView = entries.some((e) => e.isIntersecting);
    if (inView && dirty) { dirty = false; void paint(); }
  }) : null;
  seen?.observe(pic);
  const off = person.onChange((c) => {
    show(c); portrait?.forget?.();
    if (!held && (inView || !seen)) void paint(); else dirty = true;
  });
  show();
  if (!seen) void paint();
  return { show, paint, openCreator, get creator() { return creator; },
    dispose: () => { off(); seen?.disconnect(); creator?.dispose?.(); portrait?.forget?.(); } };
}

/** What the person is, in a line (as the creator's stage says it). */
export function summaryLine(catalog, choice, yc) {
  const lab = (list, id) => (list ?? []).find((o) => o.id === id)?.label ?? null;
  return [lab(catalog.sexes, choice.sex), lab(catalog.ages, choice.age), lab(catalog.complexions, choice.complexion), yc?.outfit?.label]
    .filter(Boolean).join(' · ');
}

/** The faces on offer (visitor-person.js faceChoices), each with a plain label. */
export function facesFor(catalog, sex, complexion) {
  const word = { young: 'Young', middle: 'Middle-aged', old: 'Older' };
  return faceChoices(catalog.faces, sex, complexion, catalog).map((f, n) => ({ ...f, label: `${word[f.age] ?? 'A'} face ${n + 1}` }));
}

/** The close face's turns (degrees from the front, as person-portrait.js draws): front, three-quarters, profile. */
export const FACE_TURNS = Object.freeze([0, 40, 80]);
