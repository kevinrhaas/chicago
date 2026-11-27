// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * person-creator.js — the character creator: the visitor's own person made full screen (T-3553).
 *
 * Kevin, 2026-11-27: "Make that whole build your character thing much more rich with more preview
 * simpler buttons and graphics to preview this and optimize the rendering of that. Use best
 * practice build your character style interfaces from aaa games". So, as a game's creator lays it
 * out: the person large on a lit stage, turned by dragging (or the arrows, or Front / Side / Back)
 * and seen whole or face up close; beside it (under it on a phone) a rail of categories with an
 * icon each (Body, Face, Skin and eyes, Hair, Clothes), and in each one picture choices, not
 * lists: every body style, age, cut, whisker and dress drawn as the person would wear it, colours
 * as swatches, the face library as faces. Randomize rolls a person of the year, Undo steps back,
 * Start again is the person every visitor starts as, Done closes. Every change is the person's at
 * once (visitor-person.js set), as on the You tab.
 *
 * The drawing is person-portrait.js's: the person's figure is kept between turns and zooms (one
 * render each, no build), a change is drawn once the clicking stops, and the option pictures are
 * built one at a time after the person is drawn, only for the category open, each kept until the
 * choice it shows changes. Opened from the You tab (person-settings.js) and loaded on that click.
 */
import { faceGroups, faceGroupOf, wardrobe, patchedChoice, randomChoice, personRecord, personAsset } from './visitor-person.js';
import { HAIR_COLOURS } from './human-hair-styles.js';

/* ------------------------------------------------------------ the pieces */

const PATHS = {
  body: '<circle cx="12" cy="4.8" r="2.3"/><path d="M8 21.5v-6.5l-1.6-4.6A2 2 0 0 1 8.3 7.8h7.4a2 2 0 0 1 1.9 2.6L16 15v6.5M12 15.5v6"/>',
  face: '<circle cx="12" cy="12" r="8.5"/><path d="M9 10.3v.4M15 10.3v.4"/><path d="M8.8 14.6c1.8 1.7 4.6 1.7 6.4 0"/>',
  skin: '<path d="M12 3.5C8.2 8 6 11.2 6 14a6 6 0 0 0 12 0c0-2.8-2.2-6-6-10.5z"/><path d="M9.3 14.5a2.8 2.8 0 0 0 2.7 2.6"/>',
  hair: '<path d="M4.5 20c-.6-6.5 1.4-12 7.5-12s8.1 5.5 7.5 12"/><path d="M6 10.5C8.5 8 9.5 5.5 12 3.5c1.2 2.7 4 5 6.5 6.4"/><path d="M8.5 20c0-4 .8-7 3.5-9"/>',
  clothes: '<path d="M8.5 3.5L12 6.5l3.5-3 5 3-2 4.5-2.2-1V20.5h-8.6V10l-2.2 1-2-4.5z"/><path d="M12 6.5v14"/>',
  dice: '<rect x="4" y="4" width="16" height="16" rx="3.5"/><circle cx="8.6" cy="8.6" r="1.1" fill="currentColor"/><circle cx="12" cy="12" r="1.1" fill="currentColor"/><circle cx="15.4" cy="15.4" r="1.1" fill="currentColor"/>',
  undo: '<path d="M8.5 13.5l-4-4 4-4"/><path d="M4.5 9.5h9.5a5.5 5.5 0 0 1 0 11H10"/>',
  restart: '<path d="M4.5 12a7.5 7.5 0 1 0 2.4-5.5L4.5 8.8"/><path d="M4.5 3.8v5h5"/>',
  left: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
  right: '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
  close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  check: '<path d="M5.5 12.5l4.2 4.2 8.8-9.2"/>',
};
export const CREATOR_ICONS = Object.freeze(Object.keys(PATHS));
const svg = (doc, name, size = 22) => {
  const span = doc.createElement('span');
  span.className = 'pc-icon';
  span.setAttribute('aria-hidden', 'true');
  span.innerHTML = `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${PATHS[name] ?? ''}</svg>`;
  return span;
};

const el = (doc, tag, props = {}, kids = []) => {
  const n = doc.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null) continue;
    if (k === 'class') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k.startsWith('data-') || k.startsWith('aria-') || k === 'role' || k === 'tabindex') n.setAttribute(k, v);
    else n[k] = v;
  }
  for (const kid of kids) if (kid) n.append(kid);
  return n;
};

/** The categories, in the rail's order. */
export const CREATOR_TABS = Object.freeze([
  { id: 'body', label: 'Body', icon: 'body' },
  { id: 'face', label: 'Face', icon: 'face' },
  { id: 'skin', label: 'Skin & eyes', icon: 'skin' },
  { id: 'hair', label: 'Hair', icon: 'hair' },
  { id: 'clothes', label: 'Clothes', icon: 'clothes' },
]);

/** Turns of the stage (degrees, as person-portrait.js draws them). */
export const VIEW_TURNS = Object.freeze({ front: 0, side: 70, back: 160 });

/* ------------------------------------------------------------ swatches */

const toSrgb = (v) => (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);
const rgb = (lin, gain = 1) => (Array.isArray(lin)
  ? `rgb(${lin.map((v) => Math.round(Math.max(0, Math.min(1, toSrgb(v * gain))) * 255)).join(', ')})` : null);

/** A hair colour as a swatch: the people layer's own linear colour (human-hair-styles.js), lifted
 * to how hair reads in the light (the strands' sheen lifts the dark base, the darkest most). */
export function hairSwatch(id) {
  const lin = HAIR_COLOURS[id];
  if (!Array.isArray(lin)) return null;
  const lift = (v) => 1 - Math.pow(1 - Math.max(0, Math.min(1, toSrgb(v))), 1.5);
  return `rgb(${lin.map((v) => Math.round(lift(v) * 255)).join(', ')})`;
}
/** An eye colour as an iris swatch (human-looks.js EYE_COLOUR, passed in), lifted as lit. */
export const eyeSwatch = (lin) => rgb(lin, 1.9);

/** One line of what the person is: style, age, complexion, eyes, hair, dress. */
export function summaryOf(catalog, choice, yc) {
  const lab = (list, id) => (list ?? []).find((o) => o.id === id)?.label ?? null;
  return [lab(catalog.sexes, choice.sex), lab(catalog.ages, choice.age), lab(catalog.complexions, choice.complexion),
    lab(catalog.eyes, choice.eyes) && `${lab(catalog.eyes, choice.eyes).toLowerCase()} eyes`,
    lab(catalog.hair_colours, choice.hair_colour) && `${lab(catalog.hair_colours, choice.hair_colour).toLowerCase()} hair`,
    yc?.outfit?.label].filter(Boolean).join(' · ');
}

/** A choice's key for its pictures: everything that changes how it is drawn (not when it was kept). */
export const choiceKey = (choice) => JSON.stringify({ ...choice, saved: '' });

/* ------------------------------------------------------------ the creator */

/**
 * Make the creator (once; `open` shows it). `person` is visitor-person.js's, `year` the scene's,
 * `portrait` person-portrait.js's (or null: the choices still work, with no pictures), `tints`
 * human-looks.js COMPLEXION_TINT, `eyes` its EYE_COLOUR, `skin(tint)` the complexion swatch.
 * `onOpen`/`onClose` let the You tab hold its own drawing while the creator is up.
 */
export function createPersonCreator({ doc = globalThis.document, person, year, portrait = null, tints = {}, eyes = {},
  skin = () => null, onOpen = () => {}, onClose = () => {}, win = doc?.defaultView ?? globalThis } = {}) {
  if (!doc || !person) return null;
  const C = person.catalog;
  const Y = String(year);
  if (doc.head && !doc.getElementById?.('person-creator-style')) {
    const css = doc.createElement('link'); css.id = 'person-creator-style'; css.rel = 'stylesheet';
    css.href = new URL('../css/person-creator.css', import.meta.url).href;
    doc.head.append(css);
  }

  const dialog = el(doc, 'dialog', { class: 'person-creator', 'aria-modal': 'true', 'aria-labelledby': 'pc-title' });
  dialog.setAttribute('role', 'dialog');

  // The head: what this is, the year it dresses for, close.
  const close = el(doc, 'button', { type: 'button', class: 'pc-close', 'aria-label': 'Close', title: 'Close (Esc)' }, [svg(doc, 'close')]);
  const head = el(doc, 'header', { class: 'pc-head' }, [
    el(doc, 'h2', { id: 'pc-title', class: 'pc-title', text: 'Your person' }),
    el(doc, 'span', { class: 'pc-year', text: Y, title: `Dressed for ${Y}` }), close]);

  // The stage: the person large, a drag (or the arrows) turns them; Body / Face zooms.
  const view = el(doc, 'canvas', { class: 'pc-view', width: 480, height: 720, tabindex: '0', role: 'img',
    'aria-label': 'Your person. Drag or use the arrow keys to turn.' });
  const busy = el(doc, 'div', { class: 'pc-busy', role: 'status', 'aria-live': 'polite' }, [el(doc, 'span', { class: 'pc-spinner' }), el(doc, 'span', { class: 'pc-busy-text', text: 'Updating' })]);
  busy.hidden = true;
  const zoom = el(doc, 'div', { class: 'pc-seg', role: 'radiogroup', 'aria-label': 'View' });
  const zoomBtn = (id, label) => {
    const b = el(doc, 'button', { type: 'button', role: 'radio', 'aria-checked': String(id === 'whole'), 'data-frame': id, text: label });
    b.addEventListener('click', () => setFrame(id));
    zoom.append(b);
    return b;
  };
  zoomBtn('whole', 'Body'); zoomBtn('face', 'Face');
  const turnBtn = (dir) => {
    const b = el(doc, 'button', { type: 'button', class: 'pc-turn', 'aria-label': dir < 0 ? 'Turn left' : 'Turn right', title: dir < 0 ? 'Turn left' : 'Turn right' },
      [svg(doc, dir < 0 ? 'left' : 'right', 26)]);
    b.addEventListener('click', () => spin(dir * 45));
    return b;
  };
  const presets = el(doc, 'div', { class: 'pc-presets' }, Object.entries(VIEW_TURNS).map(([id, deg]) => {
    const b = el(doc, 'button', { type: 'button', 'data-view': id, text: id[0].toUpperCase() + id.slice(1) });
    b.addEventListener('click', () => spinTo(deg));
    return b;
  }));
  const summary = el(doc, 'p', { class: 'pc-summary' });
  const stage = el(doc, 'section', { class: 'pc-stage', 'aria-label': 'Preview' }, [
    el(doc, 'div', { class: 'pc-floor', 'aria-hidden': 'true' }),
    view, busy, turnBtn(-1), turnBtn(1),
    el(doc, 'div', { class: 'pc-stage-tools' }, [zoom, presets]),
    summary]);
  stage.querySelectorAll('.pc-turn')[0].classList.add('pc-turn-left');
  stage.querySelectorAll('.pc-turn')[1].classList.add('pc-turn-right');
  if (!portrait) { view.hidden = true; stage.classList.add('no-picture'); }

  // The rail of categories and the open one's panel.
  const tabs = el(doc, 'nav', { class: 'pc-tabs', role: 'tablist', 'aria-label': 'Categories' });
  const panel = el(doc, 'section', { class: 'pc-panel', role: 'tabpanel', id: 'pc-panel', tabindex: '-1' });
  const tabBtns = new Map();
  for (const t of CREATOR_TABS) {
    const b = el(doc, 'button', { type: 'button', class: 'pc-tab', role: 'tab', id: `pc-tab-${t.id}`, 'aria-selected': 'false',
      'aria-controls': 'pc-panel', 'data-tab': t.id }, [svg(doc, t.icon, 24), el(doc, 'span', { class: 'pc-tab-label', text: t.label })]);
    b.addEventListener('click', () => showTab(t.id));
    tabs.append(b);
    tabBtns.set(t.id, b);
  }
  tabs.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' && e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    const ids = CREATOR_TABS.map((t) => t.id), at = ids.indexOf(tab);
    const next = ids[(at + (e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? ids.length - 1 : 1)) % ids.length];
    e.preventDefault(); showTab(next); tabBtns.get(next).focus();
  });

  // The foot: Randomize, Undo, Start again, Done.
  const footBtn = (cls, icon, label, fn) => {
    const b = el(doc, 'button', { type: 'button', class: `pc-foot-btn ${cls}`, title: label }, [svg(doc, icon, 20), el(doc, 'span', { text: label })]);
    b.addEventListener('click', fn);
    return b;
  };
  const rollBtn = footBtn('pc-roll', 'dice', 'Randomize', () => commit(randomChoice(person.choice, Y, C)));
  const undoBtn = footBtn('pc-undo', 'undo', 'Undo', undo);
  const resetBtn = footBtn('pc-reset', 'restart', 'Start again', () => { remember(); person.reset(); });
  const doneBtn = footBtn('pc-done', 'check', 'Done', () => hide());
  const foot = el(doc, 'footer', { class: 'pc-foot' }, [rollBtn, undoBtn, resetBtn, doneBtn]);
  const note = el(doc, 'p', { class: 'pc-liberty', text: 'Liberty: nobody of the town. Dress and looks are drawn from the year\'s own people.' });

  dialog.append(el(doc, 'div', { class: 'pc-shell' }, [head, stage,
    el(doc, 'div', { class: 'pc-side' }, [tabs, panel, note, foot])]));
  doc.body.append(dialog);
  close.addEventListener('click', () => hide());
  dialog.addEventListener('cancel', (e) => { e.preventDefault(); hide(); });

  /* ---- choosing */

  const history = [];
  const remember = () => { history.push(structuredClone(person.choice)); if (history.length > 40) history.shift(); undoBtn.disabled = false; };
  const apply = (patch) => { remember(); person.set(patch, Y); };
  const commit = (whole) => { remember(); person.replace(whole); };
  function undo() {
    const prev = history.pop();
    if (prev) person.replace(prev);
    undoBtn.disabled = !history.length;
  }
  undoBtn.disabled = true;

  /* ---- the stage */

  let frame = 'whole', turn = 0, shown = false, tab = 'body';
  let mainKey = '', mainBusy = null, drawTimer = 0;
  function setFrame(id) {
    frame = id;
    for (const b of zoom.children) b.setAttribute('aria-checked', String(b.dataset.frame === id));
    stage.dataset.frame = id;
    // The face up close is looked at from the front, whatever the figure was turned to.
    spinning++;
    if (id === 'face') turn = 0;
    void drawMain();
  }
  function drawMain() {
    if (!portrait || !shown) return Promise.resolve(false);
    const key = choiceKey(person.choice);
    const rebuild = key !== mainKey;
    if (rebuild) busy.hidden = false;
    const run = portrait.draw(view, { year: Y, turn, frame }).then((ok) => {
      if (ok) { mainKey = key; view.dataset.drawn = String(Date.now()); }
      return ok;
    }).catch((e) => { console.warn('[4D Chicago] person creator', e); return false; })
      .finally(() => { if (mainBusy === run) { mainBusy = null; busy.hidden = true; void pump(); } });
    mainBusy = run;
    return run;
  }
  // A change is drawn once the clicking stops; a turn at once, on the figure already built.
  const drawSoon = () => { win.clearTimeout(drawTimer); busy.hidden = !portrait; drawTimer = win.setTimeout(() => void drawMain(), 140); };
  const turnNow = () => { if (portrait && shown) void portrait.turnTo(view, { year: Y, turn, frame }); };
  let spinning = 0;
  function spinTo(deg) {
    const from = turn, to = from + ((((deg - from) % 360) + 540) % 360) - 180, t0 = win.performance?.now?.() ?? Date.now();
    const id = ++spinning;
    const step = () => {
      if (id !== spinning) return;
      const k = Math.min(1, ((win.performance?.now?.() ?? Date.now()) - t0) / 320);
      turn = from + (to - from) * (1 - Math.pow(1 - k, 3));
      turnNow();
      if (k < 1) win.requestAnimationFrame(step); else turn = ((to % 360) + 360) % 360;
    };
    step();
  }
  const spin = (by) => spinTo(turn + by);
  let drag = null;
  view.addEventListener('pointerdown', (e) => {
    drag = { x: e.clientX, turn, id: e.pointerId }; spinning++;
    try { view.setPointerCapture?.(e.pointerId); } catch { /* a pointer already gone: the drag still turns while over the stage */ }
    view.classList.add('is-dragging');
  });
  view.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    turn = drag.turn + (e.clientX - drag.x) * 0.6;
    turnNow();
  });
  const endDrag = (e) => { if (drag && e.pointerId === drag.id) { drag = null; view.classList.remove('is-dragging'); } };
  view.addEventListener('pointerup', endDrag);
  view.addEventListener('pointercancel', endDrag);
  view.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); spin(e.key === 'ArrowLeft' ? -30 : 30); }
  });

  /* ---- the option pictures */

  // Each picture's canvas is kept by its place (`slot`), so a panel drawn again keeps the
  // pictures it had; one whose choice has changed is dimmed until it is drawn again.
  const slots = new Map();
  const queue = [];
  let working = false;
  function picture(slot, patch, { frame: f = 'whole', turn: t = 0, w = 96, h = 144 } = {}) {
    let canvas = slots.get(slot);
    if (!canvas) {
      canvas = el(doc, 'canvas', { class: 'pc-pic', width: w * 2, height: h * 2, 'aria-hidden': 'true' });
      slots.set(slot, canvas);
    }
    if (!portrait) return canvas;
    const choice = patchedChoice(person.choice, patch, Y, C);
    const key = `${choiceKey(choice)}|${f}|${t}`;
    if (canvas.dataset.key !== key) {
      canvas.classList.toggle('is-stale', !!canvas.dataset.key);
      canvas.classList.toggle('is-empty', !canvas.dataset.key);
      const at = queue.findIndex((j) => j.slot === slot);
      if (at >= 0) queue.splice(at, 1);
      queue.push({ slot, canvas, choice, key, frame: f, turn: t });
      void pump();
    }
    return canvas;
  }
  async function pump() {
    if (working || !portrait) return;
    working = true;
    try {
      while (shown && queue.length) {
        if (mainBusy) { await mainBusy; continue; }
        await new Promise((done) => (win.requestIdleCallback ? win.requestIdleCallback(() => done(), { timeout: 300 }) : win.setTimeout(done, 16)));
        if (mainBusy) continue;
        const job = queue.shift();
        if (!job || !job.canvas.isConnected || job.canvas.dataset.key === job.key) continue;
        // The person as they are: their own figure, already built. Anyone else: a figure of its own.
        const own = choiceKey(job.choice) === choiceKey(person.choice);
        const ok = await (own ? portrait.draw(job.canvas, { year: Y, frame: job.frame, turn: job.turn })
          : portrait.preview(job.canvas, { catalog: C, record: (y) => personRecord(job.choice, y, C), asset: (y) => personAsset(job.choice, y, C) },
            { year: Y, frame: job.frame, turn: job.turn })).catch(() => false);
        if (ok) { job.canvas.dataset.key = job.key; job.canvas.classList.remove('is-stale', 'is-empty'); }
      }
    } finally { working = false; }
  }

  /* ---- the panels */

  const section = (title, kids, cls = '') => el(doc, 'div', { class: `pc-section ${cls}`.trim() }, [el(doc, 'h3', { class: 'pc-h', text: title }), ...kids]);
  const radios = (label, cls, items) => el(doc, 'div', { class: `pc-grid ${cls}`, role: 'radiogroup', 'aria-label': label }, items);
  /** A picture choice: its drawing (or a swatch), its name under it, pressed when it is the person's. */
  function tile({ label, sub = null, pressed, onPick, media, cls = '' }) {
    const b = el(doc, 'button', { type: 'button', class: `pc-tile ${cls}`.trim(), role: 'radio', 'aria-checked': String(pressed), title: label },
      [el(doc, 'span', { class: 'pc-tile-media' }, [media]), el(doc, 'span', { class: 'pc-tile-label', text: label }),
        sub ? el(doc, 'span', { class: 'pc-tile-sub', text: sub }) : null]);
    if (pressed) b.append(el(doc, 'span', { class: 'pc-tick', 'aria-hidden': 'true' }, [svg(doc, 'check', 14)]));
    b.addEventListener('click', () => { if (!pressed) onPick(); });
    return b;
  }
  function swatch({ label, colour, pressed, onPick, cls = '' }) {
    const dot = el(doc, 'span', { class: `pc-dot ${cls}`.trim() });
    if (colour) dot.style.setProperty('--c', colour);
    const b = el(doc, 'button', { type: 'button', class: 'pc-swatch', role: 'radio', 'aria-checked': String(pressed), 'aria-label': label, title: label },
      [dot, el(doc, 'span', { class: 'pc-swatch-label', text: label })]);
    b.addEventListener('click', () => { if (!pressed) onPick(); });
    return b;
  }

  const panels = {
    body(choice) {
      return [
        section(C.body_label ?? 'Body style', [radios('Body style', 'pc-grid-tall', C.sexes.map((s) => tile({
          label: s.label, pressed: s.id === choice.sex, onPick: () => apply({ sex: s.id }),
          media: picture(`sex:${s.id}`, { sex: s.id }, { w: 96, h: 144 }) })))]),
        section('Age', [radios('Age', 'pc-grid-face', C.ages.map((a) => tile({
          label: a.label, sub: Number.isFinite(a.years) ? `about ${a.years}` : null, pressed: a.id === choice.age, onPick: () => apply({ age: a.id }),
          media: picture(`age:${a.id}`, { age: a.id }, { frame: 'face', turn: 20, w: 96, h: 96 }) })))]),
      ];
    },
    face(choice) { return [faceLibrary(choice)]; },
    skin(choice) {
      return [
        section('Complexion', [radios('Complexion', 'pc-swatches', C.complexions.map((c) => swatch({
          label: c.label, colour: skin(tints[c.id]), pressed: c.id === choice.complexion, onPick: () => apply({ complexion: c.id }) })))]),
        section('Eyes', [radios('Eyes', 'pc-swatches', C.eyes.map((c) => swatch({
          label: c.label, colour: eyeSwatch(eyes[c.id]), cls: 'pc-iris', pressed: c.id === choice.eyes, onPick: () => apply({ eyes: c.id }) })))]),
      ];
    },
    hair(choice) {
      const yc = person.year(Y), facial = C.facial?.[choice.sex] ?? [];
      return [
        section('Hair colour', [radios('Hair colour', 'pc-swatches', C.hair_colours.map((c) => swatch({
          label: c.label, colour: hairSwatch(c.id), cls: 'pc-strand', pressed: c.id === choice.hair_colour, onPick: () => apply({ hair_colour: c.id }) })))]),
        section('Cut', [radios('Hair', 'pc-grid-face', wardrobe(C, 'cuts', yc.year, choice.sex).map((c) => tile({
          label: c.label, pressed: c.id === yc.cut?.id, onPick: () => apply({ cut: c.id }),
          media: picture(`cut:${c.id}`, { cut: c.id }, { frame: 'face', turn: 40, w: 96, h: 96 }) })))]),
        facial.length > 1 ? section('Whiskers', [radios('Whiskers', 'pc-grid-face', facial.map((f) => tile({
          label: f.label, pressed: f.id === choice.facial, onPick: () => apply({ facial: f.id }),
          media: picture(`facial:${f.id}`, { facial: f.id }, { frame: 'face', turn: 20, w: 96, h: 96 }) })))]) : null,
      ].filter(Boolean);
    },
    clothes(choice) {
      const yc = person.year(Y);
      return [section(`Dress in ${Y}`, [radios(`Dress in ${Y}`, 'pc-grid-cards', wardrobe(C, 'outfits', yc.year, choice.sex).map((o) => tile({
        label: o.label, sub: o.worn ?? null, cls: 'pc-card', pressed: o.id === yc.outfit?.id, onPick: () => apply({ outfit: o.id }),
        media: picture(`outfit:${o.id}`, { outfit: o.id }, { w: 120, h: 180 }) })))])];
    },
  };

  // The face library (T-3553): Auto, then a tab for each type (photographed faces by age, the
  // painted ones), and that type's faces in bands of tone. As the You tab had it, larger.
  let faceTab = null;
  function faceLibrary(choice) {
    const groups = faceGroups(C, choice.sex, choice.complexion);
    const autoId = choice.face === 'auto' ? person.record(Y).looks.face_pick : null;
    if (!groups.some((g) => g.id === faceTab)) faceTab = null;
    faceTab ??= faceGroupOf(groups, autoId ?? choice.face, choice.age);
    const auto = el(doc, 'button', { type: 'button', class: 'pc-auto', role: 'radio', 'aria-checked': String(choice.face === 'auto'),
      'data-id': 'auto' }, [svg(doc, 'face', 22), el(doc, 'span', { class: 'pc-auto-text' }, [
        el(doc, 'strong', { text: 'Auto' }), el(doc, 'span', { text: 'A face of your age nearest your complexion' })])]);
    auto.addEventListener('click', () => { if (choice.face !== 'auto') apply({ face: 'auto' }); });
    const bar = el(doc, 'div', { class: 'pc-chips', role: 'tablist', 'aria-label': 'Face library' }, groups.map((g) => {
      const t = el(doc, 'button', { type: 'button', class: 'pc-chip', role: 'tab', 'aria-selected': String(g.id === faceTab), 'data-group': g.id,
        title: `${g.label} faces (${g.count})` }, [el(doc, 'span', { text: g.label }), el(doc, 'span', { class: 'pc-chip-n', text: String(g.count) })]);
      if (g.bands.some((b) => b.faces.some((f) => f.id === choice.face))) t.classList.add('has-choice');
      t.addEventListener('click', () => { faceTab = g.id; render(); });
      return t;
    }));
    bar.hidden = groups.length < 2;
    const group = groups.find((g) => g.id === faceTab);
    let n = 0;
    const bands = (group?.bands ?? []).map((band) => el(doc, 'div', { class: 'pc-band' }, [
      band.label ? el(doc, 'span', { class: 'pc-band-label', text: band.label }) : null,
      el(doc, 'div', { class: 'pc-faces', role: 'radiogroup', 'aria-label': band.label || group.label }, band.faces.map((f) => {
        n++;
        const label = group.kind === 'photo' ? `${group.label} face ${n}, ${band.label.toLowerCase()}` : `Painted face ${n}`;
        const b = el(doc, 'button', { type: 'button', class: 'pc-face', role: 'radio', 'aria-checked': String(f.id === choice.face),
          'aria-label': label, title: label, 'data-id': f.id }, [faceThumb(f, group.kind)]);
        if (f.id === autoId) b.classList.add('is-auto');
        b.addEventListener('click', () => { if (f.id !== choice.face) apply({ face: f.id }); });
        return b;
      }))]));
    const words = choice.face === 'auto' ? `Auto: the ${autoId ? 'ringed ' : ''}face. Pick any face to keep it.`
      : group?.kind === 'photo' ? 'Your complexion, eyes and hair are worn with the face you pick.' : '';
    return el(doc, 'div', { class: 'pc-section pc-library' }, [el(doc, 'h3', { class: 'pc-h', text: 'Face' }), auto, bar,
      el(doc, 'div', { class: 'pc-bands' }, bands), words ? el(doc, 'p', { class: 'pc-note', text: words }) : null]);
  }

  function faceThumb(f, kind) {
    const pic = el(doc, 'span', { class: 'pc-face-pic' });
    if (kind === 'photo') {
      // The face's own picture on the library's sheet (tools/photo_face_thumbs.py), upright.
      const T = C.photoFaces.thumbs, [W, H] = T.size_px, t = T.tile_px;
      const x = (f.index % T.cols) * t, y = Math.floor(f.index / T.cols) * t;
      pic.style.backgroundImage = `url("${T.url}")`;
      pic.style.backgroundSize = `${(W / t) * 100}% ${(H / t) * 100}%`;
      pic.style.backgroundPosition = `${(x / Math.max(1, W - t)) * 100}% ${(y / Math.max(1, H - t)) * 100}%`;
      return pic;
    }
    // A painted face: the library sheet's tile, turned upright (the atlas lays a face on its side).
    const F = C.faces, [W, H] = F.size_px ?? [1280, 1280], t = F.tile_px ?? 256, cols = F.cols ?? 5;
    const x = (f.index % cols) * t, y = Math.floor(f.index / cols) * t;
    pic.classList.add('pc-face-painted');
    pic.style.backgroundImage = `url("${new URL(F.map, F.base).href}")`;
    pic.style.backgroundSize = `${(W / t) * 100}% ${(H / t) * 100}%`;
    pic.style.backgroundPosition = `${(x / (W - t)) * 100}% ${(y / (H - t)) * 100}%`;
    return pic;
  }

  function render() {
    const choice = person.choice;
    // The pictures wanted are the open panel's: the rest wait for their panel.
    queue.length = 0;
    const scroll = panel.scrollTop;
    panel.replaceChildren(...panels[tab](choice));
    panel.scrollTop = scroll;
    summary.textContent = summaryOf(C, choice, person.year(Y));
  }

  function showTab(id) {
    if (!panels[id]) return;
    tab = id;
    for (const [k, b] of tabBtns) b.setAttribute('aria-selected', String(k === id));
    panel.setAttribute('aria-labelledby', `pc-tab-${id}`);
    dialog.dataset.tab = id;
    panel.scrollTop = 0;
    render();
  }

  const off = person.onChange(() => {
    if (!shown) return;
    portrait?.forget?.();
    render();
    drawSoon();
  });

  /* ---- open and close */

  function show(at = tab) {
    if (shown) { showTab(at); return; }
    shown = true;
    onOpen();
    dialog.hidden = false;
    if (typeof dialog.showModal === 'function') { try { dialog.showModal(); } catch { dialog.setAttribute('open', ''); } }
    else dialog.setAttribute('open', '');
    doc.documentElement.classList.add('pc-open');
    showTab(at);
    void drawMain();
    tabBtns.get(at)?.focus?.();
  }
  function hide() {
    if (!shown) return;
    shown = false;
    spinning++;
    win.clearTimeout(drawTimer);
    queue.length = 0;
    if (dialog.open && typeof dialog.close === 'function') dialog.close(); else dialog.removeAttribute('open');
    dialog.hidden = true;
    doc.documentElement.classList.remove('pc-open');
    onClose();
  }
  dialog.hidden = true;

  return {
    open: show, close: hide, dialog,
    get isOpen() { return shown; },
    get tab() { return tab; },
    /** Settle: the person drawn and every picture of the open panel (the screenshots wait on it). */
    async settle() { await mainBusy; while (queue.length || working) await new Promise((d) => win.setTimeout(d, 50)); return true; },
    dispose() { hide(); off(); dialog.remove(); },
  };
}
