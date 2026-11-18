// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * person-settings.js — the Settings card's You tab (T-3644): the visitor's own person.
 *
 * Kevin, 2026-11-17: "you will need to provide options for users in settings to change the gender
 * appearance dress, etc. this becomes a person builder eventually but the foundation starts with
 * customizing the default person". So the tab is a small builder over visitor-person.js: a
 * portrait of the person (person-portrait.js, the figure the town draws, turned with a tap), then
 * Man or Woman, age, complexion (swatches), the face (the library's faces, Auto first), eyes, hair
 * colour and cut, whiskers, and the dress for the year the visitor is in, each year's kept
 * separately. Every change is the person's at once: a figure already in the saddle is re-made.
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
 * Fill `#s-person` with the builder. `person` is visitor-person.js's; `year` the scene's;
 * `portrait` person-portrait.js's (or null: no picture, the controls still work);
 * `tints` the complexion tints (human-looks.js COMPLEXION_TINT).
 */
export function wirePersonSettings({ doc = globalThis.document, person, year, portrait = null, tints = {} }) {
  const host = personHost(doc);
  if (!host || !person) return null;
  const C = person.catalog;
  host.replaceChildren();
  if (!(C.years ?? []).includes(String(year))) {
    host.append(el(doc, 'p', { class: 'legend-note', text: `Your person is drawn in ${(C.years ?? []).join(', ')}.` }));
    return null;
  }
  let turn = 0;

  // The portrait: the figure itself, a tap turns it.
  const canvas = el(doc, 'canvas', { class: 'person-portrait', width: 240, height: 360, 'aria-label': 'Your person' });
  const pic = el(doc, 'button', { type: 'button', class: 'person-pic', title: 'Turn', 'aria-label': 'Turn your person' }, [canvas]);
  const status = el(doc, 'p', { class: 'legend-note person-status', role: 'status' });
  pic.addEventListener('click', () => { turn = (turn + 1) % 8; paint(); });
  host.append(el(doc, 'div', { class: 'person-stage' }, [pic, status]));
  if (!portrait) pic.hidden = true;

  // A row of choices as buttons (one pressed), or as a select where the list is long.
  const rows = {};
  const choiceRow = (key, label, { swatch = false } = {}) => {
    const box = el(doc, 'div', { class: `person-row${swatch ? ' person-swatches' : ''}`, role: 'radiogroup', 'aria-label': label });
    const head = el(doc, 'span', { class: 'person-label', text: label });
    const list = el(doc, 'div', { class: 'person-choices' });
    box.append(head, list);
    host.append(box);
    rows[key] = { box, list, head };
    return rows[key];
  };
  const selectRow = (key, label) => {
    const id = `s-person-${key.replace(/_/g, '-')}`;
    const select = el(doc, 'select', { id });
    const box = el(doc, 'label', { class: 'field row person-row' }, [el(doc, 'span', { text: label }), select]);
    host.append(box);
    rows[key] = { box, select };
    return rows[key];
  };

  choiceRow('sex', 'Gender');
  selectRow('age', 'Age');
  choiceRow('complexion', 'Complexion', { swatch: true });
  choiceRow('face', 'Face');
  selectRow('eyes', 'Eyes');
  selectRow('hair_colour', 'Hair colour');
  selectRow('cut', 'Hair');
  selectRow('facial', 'Whiskers');
  selectRow('outfit', `Dress in ${year}`);
  const worn = el(doc, 'p', { class: 'legend-note person-worn' });
  host.append(worn);
  const reset = el(doc, 'button', { type: 'button', class: 'setting-button', text: 'Start again' });
  host.append(el(doc, 'div', { class: 'field row' }, [el(doc, 'span', { text: 'The person every visitor starts as' }), reset]));
  host.append(el(doc, 'p', { class: 'legend-note', text: 'You ride as this person. Kept on this device, and with your sign-in when you have one. Liberty: nobody of the town; dress and looks are drawn from the year\'s own people.' }));
  reset.addEventListener('click', () => person.reset());

  const fillSelect = (select, list, value) => {
    select.replaceChildren(...list.map((o) => el(doc, 'option', { value: o.id, text: o.label })));
    select.value = value ?? list[0]?.id ?? '';
    select.disabled = list.length < 2;
  };
  const fillButtons = (row, list, value, paintOne = null) => {
    row.list.replaceChildren(...list.map((o) => {
      const b = el(doc, 'button', { type: 'button', class: 'person-choice', role: 'radio', 'aria-checked': String(o.id === value),
        'aria-label': o.label, title: o.label, 'data-id': o.id });
      if (paintOne) paintOne(b, o); else b.textContent = o.label;
      b.addEventListener('click', () => set(row === rows.face ? 'face' : row === rows.complexion ? 'complexion' : 'sex', o.id));
      return b;
    }));
  };
  const set = (key, value) => person.set({ [key]: value }, year);
  for (const key of ['age', 'eyes', 'hair_colour', 'facial', 'cut', 'outfit']) {
    rows[key].select.addEventListener('change', (e) => set(key, e.target.value));
  }

  function faceThumb(b, f) {
    const F = C.faces;
    if (f.id === 'auto' || !F) { b.textContent = f.label; b.classList.add('person-face-word'); return; }
    // The library sheet's tile, turned upright (the atlas lays a face on its side).
    const [W, H] = F.size_px ?? [1280, 1280], t = F.tile_px ?? 256, cols = F.cols ?? 5;
    const i = f.index, x = (i % cols) * t, y = Math.floor(i / cols) * t;
    const tile = el(doc, 'span', { class: 'person-face-tile' });
    tile.style.backgroundImage = `url("${new URL(F.map, F.base).href}")`;
    tile.style.backgroundSize = `${(W / t) * 100}% ${(H / t) * 100}%`;
    tile.style.backgroundPosition = `${(x / (W - t)) * 100}% ${(y / (H - t)) * 100}%`;
    b.append(tile);
  }

  function show(choice = person.choice) {
    const sex = choice.sex, yc = person.year(year);
    fillButtons(rows.sex, C.sexes, sex);
    fillSelect(rows.age.select, C.ages, choice.age);
    fillButtons(rows.complexion, C.complexions, choice.complexion, (b, o) => {
      b.classList.add('person-swatch');
      const c = swatchColour(tints[o.id]);
      if (c) b.style.background = c;
    });
    const faces = [{ id: 'auto', label: 'Auto' }, ...(C.faces ? facesFor(C, sex, choice.complexion) : [])];
    fillButtons(rows.face, faces, choice.face, faceThumb);
    fillSelect(rows.eyes.select, C.eyes, choice.eyes);
    fillSelect(rows.hair_colour.select, C.hair_colours, choice.hair_colour);
    fillSelect(rows.cut.select, C.cuts?.[yc.year]?.[sex] ?? [], yc.cut?.id);
    const facial = C.facial?.[sex] ?? [];
    fillSelect(rows.facial.select, facial, choice.facial);
    rows.facial.box.hidden = facial.length < 2;
    fillSelect(rows.outfit.select, C.outfits?.[yc.year]?.[sex] ?? [], yc.outfit?.id);
    worn.textContent = yc.outfit?.worn ?? '';
  }

  let painting = null, again = false;
  async function paint() {
    if (!portrait) return;
    if (painting) { again = true; return painting; }
    status.textContent = 'Drawing…';
    painting = portrait.draw(canvas, { year, turn: turn * 45 })
      .then((ok) => { status.textContent = ok ? '' : 'Your person is drawn when the town\'s people have loaded.'; if (ok) canvas.dataset.drawn = String(Date.now()); })
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
    if (inView || !seen) void paint(); else dirty = true;
  });
  show();
  if (!seen) void paint();
  return { show, paint, dispose: () => { off(); seen?.disconnect(); portrait?.forget?.(); }, rows };
}

/** The faces on offer (visitor-person.js faceChoices), each with a plain label. */
export function facesFor(catalog, sex, complexion) {
  const word = { young: 'Young', middle: 'Middle-aged', old: 'Older' };
  return faceChoices(catalog.faces, sex, complexion).map((f, n) => ({ ...f, label: `${word[f.age] ?? 'A'} face ${n + 1}` }));
}
