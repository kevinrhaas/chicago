/**
 * Confidence view (SCR 07), loaded the first time it opens (T-2647, NAV-601; DESIGN §09, M9).
 *
 * "See what's Attested. See what we Reconstructed. Choose how." It replaces the HUD's
 * Confidence chip, its caret and its checkbox menu:
 *
 *   - four presets, one tap each: NORMAL, BY GRADE, ATTESTED ONLY, X-RAY
 *     (confidence-presets.js says what each puts in force; C still toggles BY GRADE);
 *   - a row per grade: shown or hidden (the menu's old checkboxes, keeping their ids so
 *     every reader of them still finds them), its colour, its look, and how many
 *     structures stand at that grade — the colour, Look and opacity controls of each row
 *     are T-2648's;
 *   - Show everything, and the footer readout: GRADE MASK (grades shown of three),
 *     MESHES (structures standing at the grades shown) and FRAME CLK (frames a second).
 *
 * It reads the page through ctx.api (the HUD and the renderer's confidence view) and
 * repaints twice a second while it is open, so a change made anywhere — C, a hide by
 * hand, a test hook — is what it shows.
 */
import { PRESETS, LEVELS, applyPreset, presetOf } from '../confidence-presets.js';

const NAMES = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const LOOK_WORDS = { tint: 'Tint', ghost: 'Ghost', dither: 'Dither' };
let timer = null;

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
    b.addEventListener('click', () => { applyPreset(p.id, d); paint(); });
    presets.append(b);
  }

  const rows = make('div', { className: 'nav-grades' });
  const cells = {};
  for (const level of LEVELS) {
    const box = make('input', { type: 'checkbox', id: `cm-${level}`, checked: true });
    box.addEventListener('change', () => { d.hud?.setHidden(level, !box.checked); paint(); });
    const swatch = make('span', { className: `nav-grade-sw cm-sw sw-${level === 'attested' ? 'att' : level === 'inferred' ? 'inf' : 'rec'}`, 'aria-hidden': 'true' });
    const name = make('span', { className: 'nav-grade-name' }, NAMES[level]);
    const look = make('span', { className: 'nav-grade-look' });
    const count = make('span', { className: 'nav-grade-count cm-count', id: `cm-count-${level}` });
    const row = make('label', { className: 'nav-grade', dataset: { grade: level } }, box, swatch, name, look, count);
    rows.append(row);
    cells[level] = { box, look, count, row };
  }
  const reset = make('button', { type: 'button', className: 'nav-showall', id: 'cm-reset' }, 'Show everything');
  reset.addEventListener('click', () => {
    for (const level of LEVELS) d.hud?.setHidden(level, false, { announce: false });
    d.hud?.say?.('Showing every grade again');
    paint();
  });
  const note = make('p', { className: 'nav-sub nav-cm-note', id: 'cm-note' },
    'Turning a grade off removes it from the view entirely, with the colouring on or off.');
  const readout = make('div', { className: 'nav-readout', 'aria-hidden': 'true' });
  const mask = make('span'), meshCell = make('span'), clock = make('span');
  readout.append(mask, meshCell, clock);
  el.append(presets, rows, reset, note, readout);

  function paint() {
    const hud = d.hud, view = d.view;
    if (!hud || !view) return;
    const hidden = new Set(hud.hiddenLevels);
    const on = hud.confidenceOn;
    const current = presetOf({ on, hidden: [...hidden], view });
    for (const b of presets.children) b.setAttribute('aria-pressed', String(b.dataset.preset === current));
    const counts = hud.levelCounts?.() ?? {};
    let meshes = 0;
    for (const level of LEVELS) {
      const c = cells[level];
      c.box.checked = !hidden.has(level);
      c.row.classList.toggle('is-off', hidden.has(level));
      const g = view.grade(level);
      c.look.textContent = on ? `${LOOK_WORDS[g.mode] ?? g.mode} · ${Math.round(g.opacity * 100)}%` : 'Off';
      c.count.textContent = String(counts[level] ?? 0);
      if (!hidden.has(level)) meshes += Number(counts[level] ?? 0);
    }
    const fps = d.api?.stats?.().fps;
    mask.textContent = `GRADE MASK ${LEVELS.length - hidden.size}/3`;
    meshCell.textContent = `MESHES ${meshes.toLocaleString('en-US')}`;
    clock.textContent = `FRAME CLK ${Number.isFinite(fps) ? fps : '--'}`;
  }
  paint();
  clearInterval(timer);
  timer = setInterval(paint, 500);
  el.__confidencePaint = paint;
}

export function unmount(el) {
  clearInterval(timer);
  timer = null;
  delete el.__confidencePaint;
}
