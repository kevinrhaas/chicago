/**
 * Confidence view (SCR 07), loaded the first time it opens (T-2647, NAV-601; DESIGN §09, M9).
 *
 * "See what's Attested. See what we Reconstructed. Choose how." It replaces the HUD's
 * Confidence chip, its caret and its checkbox menu:
 *
 *   - four presets, one tap each: NORMAL, BY GRADE, ATTESTED ONLY, X-RAY
 *     (confidence-presets.js says what each puts in force; C still toggles BY GRADE);
 *   - a row per grade (T-2648, confidence-rows.js): Show (the menu's old checkboxes,
 *     keeping their ids so every reader of them still finds them), how many structures
 *     stand at that grade, and — opened from the row's look, one row at a time — four
 *     curated swatches, the Look (Tint, Ghost, Dither) and an opacity slider, 0-100 %;
 *   - the colour-blind-safe set on all three grades at once, Show everything, and the
 *     footer readout: GRADE MASK (grades shown of three),
 *     MESHES (structures standing at the grades shown) and FRAME CLK (frames a second).
 *
 * It reads the page through ctx.api (the HUD and the renderer's confidence view). It
 * repaints at once when the HUD says the colouring or the hidden set moved, and twice a
 * second besides (for a look set from a test hook), so what it shows is the scene.
 */
import { PRESETS, LEVELS, applyPreset, presetOf, saveLooks } from '../confidence-presets.js';
import { count as countField } from '../field-log.js'; // T-2660
import { LOOKS, SAFE_SET, swatchesOf, swatchOf, setInForce, setSwatch, applySet, setLook, setOpacity, percentOf } from '../confidence-rows.js';
import { t as str } from '../strings/index.js';
import { gradeTerm } from '../strings/terms.js';
import '../strings/hud.js';
import '../strings/confidence.js';

const nameOf = (level) => gradeTerm(level).label;
let timer = null;
// Which row has its colour, look and opacity open. One at a time, as M9 draws it, so the
// three rows fit a phone; Reconstructed first, as the mockup has it. Kept for the visit.
let openRow = 'reconstructed';

function deps(ctx) {
  const api = ctx.api ?? {};
  let storage = null;
  try { storage = globalThis.localStorage; } catch { storage = null; }
  return { hud: api.hud, view: api.confidence, storage, api };
}

export function mount(el, ctx = {}) {
  const doc = el.ownerDocument;
  const d = deps(ctx);
  el.replaceChildren();
  const make = (tag, props = {}, ...kids) => {
    const n = doc.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === 'dataset') Object.assign(n.dataset, v);
      else if (k in n && k !== 'role') n[k] = v;
      else n.setAttribute(k, v);
    }
    n.append(...kids);
    return n;
  };

  const presets = make('div', { className: 'nav-presets', role: 'group', 'aria-label': 'Confidence view presets' });
  for (const p of PRESETS) {
    const b = make('button', { type: 'button', className: 'nav-preset', dataset: { preset: p.id }, title: p.note }, p.label);
    b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', () => { applyPreset(p.id, d); countField('confidencePreset'); paint(); });
    presets.append(b);
  }

  const rows = make('div', { className: 'nav-grades' });
  const cells = {};
  // What a row control does after it has written the renderer: keep the looks for the next
  // visit (as a preset does) and draw the app again from the scene.
  const done = (save = true) => { if (save && d.view) saveLooks(d.view, d.storage); paint(); };
  for (const level of LEVELS) {
    const name = nameOf(level);
    const box = make('input', { type: 'checkbox', id: `cm-${level}`, checked: true });
    box.addEventListener('change', () => { d.hud?.setHidden(level, !box.checked); paint(); });
    const swatch = make('span', { className: 'nav-grade-sw', 'aria-hidden': 'true' });
    const label = make('label', { className: 'nav-grade-show' }, box, swatch, make('span', { className: 'nav-grade-name' }, name));
    const look = make('button', { type: 'button', className: 'nav-grade-look', id: `cm-look-${level}`,
      'aria-expanded': 'false', 'aria-controls': `cm-controls-${level}`, 'aria-label': str('confidence.row.more', { grade: name }) });
    const count = make('span', { className: 'nav-grade-count cm-count', id: `cm-count-${level}` });
    // The look and the count travel together: on a phone too narrow for the whole row they
    // wrap under the name as one, so "Reconstructed" is never cut short.
    const head = make('div', { className: 'nav-grade-head' }, label, make('span', { className: 'nav-grade-meta' }, look, count));

    // Colour: the four swatches, one radio group.
    const swatches = make('div', { className: 'nav-swatches', role: 'radiogroup', 'aria-label': str('confidence.row.colour', { grade: name }) });
    const swatchButtons = swatchesOf(level).map((sw) => {
      const words = str(sw.colourBlindSafe ? 'confidence.swatch.safe' : 'confidence.swatch.label',
        { name: str(`confidence.swatch.${sw.name}`), grade: name });
      const b = make('button', { type: 'button', className: 'nav-swatch', role: 'radio', title: words, 'aria-label': words,
        dataset: { set: sw.set, ...(sw.colourBlindSafe ? { safe: '' } : {}) } });
      b.style.setProperty('--c', sw.hex);
      b.setAttribute('aria-checked', 'false');
      b.addEventListener('click', () => { setSwatch(d, level, sw.set); done(); });
      swatches.append(b);
      return b;
    });
    // Look: Tint, Ghost, Dither.
    const looks = make('div', { className: 'nav-looks', role: 'group', 'aria-label': `${name} · ${str('confidence.row.look')}` });
    const lookButtons = LOOKS.map((mode) => {
      const b = make('button', { type: 'button', className: 'nav-look', dataset: { look: mode }, title: str(`confidence.look.${mode}.note`) },
        str(`confidence.look.${mode}`));
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => { setLook(d, level, mode); done(); });
      looks.append(b);
      return b;
    });
    // Opacity: 0-100 %. Each step is a uniform write; the looks are kept when the drag ends.
    const slider = make('input', { type: 'range', className: 'nav-opacity-range', id: `cm-opacity-${level}`, min: '0', max: '100', step: '1',
      'aria-label': str('confidence.row.opacity.label', { grade: name }) });
    const pctOut = make('output', { className: 'nav-opacity-value', htmlFor: slider.id });
    slider.addEventListener('input', () => { cells[level].held = Date.now(); setOpacity(d, level, slider.value); done(false); });
    slider.addEventListener('change', () => done());
    const opacity = make('div', { className: 'nav-opacity' },
      make('span', { className: 'nav-opacity-k' }, str('confidence.row.opacity')), slider, pctOut);
    const controls = make('div', { className: 'nav-grade-controls', id: `cm-controls-${level}` }, swatches, looks, opacity);
    controls.hidden = true;
    look.addEventListener('click', () => { openRow = openRow === level ? null : level; paint(); });

    const row = make('div', { className: 'nav-grade', dataset: { grade: level } }, head, controls);
    rows.append(row);
    cells[level] = { box, swatch, look, count, row, controls, swatchButtons, lookButtons, slider, pctOut, held: 0 };
  }
  // The colour-blind-safe set, on all three grades in one tap.
  const safe = make('button', { type: 'button', className: 'nav-safe', id: 'cm-safe', title: str('confidence.safe.note') },
    str('confidence.safe.set'));
  safe.setAttribute('aria-pressed', 'false');
  safe.addEventListener('click', () => {
    applySet(d, SAFE_SET);
    d.hud?.say?.(str('confidence.safe.on'));
    done();
  });
  const reset = make('button', { type: 'button', className: 'nav-showall', id: 'cm-reset' }, str('confidence.show.all'));
  reset.addEventListener('click', () => {
    for (const level of LEVELS) d.hud?.setHidden(level, false, { announce: false });
    d.hud?.say?.(str('hud.levels.all'));
    paint();
  });
  const note = make('p', { className: 'nav-sub nav-cm-note', id: 'cm-note' }, str('confidence.note'));
  const readout = make('div', { className: 'nav-readout', 'aria-hidden': 'true' });
  const mask = make('span'), meshCell = make('span'), clock = make('span');
  readout.append(mask, meshCell, clock);
  el.append(presets, rows, safe, reset, note, readout);

  // The counts walk the whole registry, so they are taken again only when it changes size
  // (a scene's records arriving), not on every repaint.
  let counts = null, countsAt = -1;
  function paint() {
    const hud = d.hud, view = d.view;
    if (!hud || !view) return;
    const hidden = new Set(hud.hiddenLevels);
    const on = hud.confidenceOn;
    const current = presetOf({ on, hidden: [...hidden], view });
    for (const b of presets.children) b.setAttribute('aria-pressed', String(b.dataset.preset === current));
    const size = d.api?.registry?.size ?? 0;
    if (!counts || size !== countsAt) { counts = hud.levelCounts?.() ?? {}; countsAt = size; }
    let meshes = 0;
    for (const level of LEVELS) {
      const c = cells[level];
      c.box.checked = !hidden.has(level);
      c.row.classList.toggle('is-off', hidden.has(level));
      const g = view.grade(level);
      const pct = percentOf(g);
      c.look.textContent = on ? str('confidence.row.summary', { look: str(`confidence.look.${g.mode}`), percent: pct }) : str('confidence.look.off');
      const open = openRow === level;
      c.look.setAttribute('aria-expanded', String(open));
      c.controls.hidden = !open;
      c.row.classList.toggle('is-open', open);
      c.swatch.style.setProperty('--c', g.color);
      c.swatch.dataset.look = on ? g.mode : 'none';
      const worn = swatchOf(view, level);
      for (const b of c.swatchButtons) b.setAttribute('aria-checked', String(b.dataset.set === worn));
      for (const b of c.lookButtons) b.setAttribute('aria-pressed', String(b.dataset.look === g.mode));
      // Not mid-drag (the scene already has the value the thumb gives), else from the scene.
      if (Date.now() - (c.held ?? 0) > 400 && c.slider.value !== String(pct)) c.slider.value = String(pct);
      c.pctOut.textContent = `${pct}%`;
      c.count.textContent = String(counts[level] ?? 0);
      if (!hidden.has(level)) meshes += Number(counts[level] ?? 0);
    }
    safe.setAttribute('aria-pressed', String(setInForce(view) === SAFE_SET));
    const fps = d.api?.stats?.().fps;
    mask.textContent = `GRADE MASK ${LEVELS.length - hidden.size}/3`;
    meshCell.textContent = `MESHES ${meshes.toLocaleString('en-US')}`;
    clock.textContent = `FRAME CLK ${Number.isFinite(fps) ? fps : '--'}`;
  }
  paint();
  clearInterval(timer);
  timer = setInterval(paint, 500);
  // A change made anywhere — C, a hide by hand, the HUD's own switch — repaints at once.
  doc.removeEventListener('chicago4d-confidence', onChange);
  onChange = paint;
  doc.addEventListener('chicago4d-confidence', onChange);
}
let onChange = () => {};

export function unmount(el) {
  clearInterval(timer);
  timer = null;
  el.ownerDocument?.removeEventListener('chicago4d-confidence', onChange);
}
