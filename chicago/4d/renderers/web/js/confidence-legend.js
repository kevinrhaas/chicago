/**
 * confidence-legend.js — the Confidence view's legend chip in the HUD (T-2649, NAV-604;
 * DESIGN §09 and §10: "While the view is on, a small legend chip sits under the year chip
 * in the HUD. Tapping it opens this app").
 *
 * It shows only while the view is not NORMAL — the colouring on, or a grade hidden — and
 * reads the scene, never a copy of it: one dot per grade in the colour that grade wears
 * (a ghosted grade's dot see-through, a hidden grade's an empty ring, the colouring off
 * a plain dot), then CONF in the year chip's mono caps. Its label says the same in words.
 * A tap opens the Navigator's Confidence view app (`open`).
 *
 * It repaints when the HUD or the app says the view moved (the `chicago4d-confidence`
 * event: the colouring, the hidden set, or a look kept by confidence-presets.js saveLooks).
 * On a desktop the Navigator's rail stands under the year chip, so there the chip sits
 * beside it (css/walk.css .hud-chips); it is the same chip.
 */
import { swatchOf, swatchesOf } from './confidence-rows.js';
import { viewIsOn } from './confidence-store.js';
import { t as str } from './strings/index.js';
import { gradeTerm } from './strings/terms.js';
import './strings/confidence.js';

const LEVELS = ['attested', 'inferred', 'reconstructed'];

/** What the chip says for this state, without a page: shown, the label and each dot. */
export function legendOf({ on, hidden, view }) {
  const gone = new Set(hidden ?? []);
  const shown = viewIsOn({ on, hidden: [...gone] });
  const dots = LEVELS.map((level) => {
    const g = view?.grade?.(level) ?? null;
    const name = gradeTerm(level).label;
    if (gone.has(level)) return { level, state: 'hidden', color: g?.color ?? '', words: str('confidence.legend.grade.hidden', { grade: name }) };
    if (!on || !g) return { level, state: 'plain', color: '', words: str('confidence.legend.grade.shown', { grade: name }) };
    const worn = swatchOf(view, level);
    const sw = swatchesOf(level).find((s) => s.set === worn);
    const colour = sw ? str(`confidence.swatch.${sw.name}`).toLowerCase() : str('confidence.legend.colour.own');
    return { level, state: g.mode, color: g.color, opacity: g.opacity, words: str('confidence.legend.grade', { grade: name, colour }) };
  });
  return { shown, dots, label: str('confidence.legend.label', { grades: dots.map((d) => d.words).join(', ') }) };
}

/**
 * Bind the chip. `el` is #conf-legend (its three dots marked data-grade); `hud` keeps the
 * colouring and the hidden set; `view` is the renderer's confidence view; `open` opens the
 * app. Returns { paint, get shown }.
 */
export function createConfidenceLegend({ el, hud, view, open = null, doc = el?.ownerDocument ?? globalThis.document } = {}) {
  let shown = false;
  const dots = Object.fromEntries(LEVELS.map((l) => [l, el?.querySelector?.(`[data-grade="${l}"]`) ?? null]));
  function paint() {
    if (!el || !hud) return false;
    const L = legendOf({ on: hud.confidenceOn, hidden: hud.hiddenLevels, view });
    shown = L.shown;
    el.hidden = !shown;
    if (!shown) return false;
    for (const d of L.dots) {
      const dot = dots[d.level];
      if (!dot) continue;
      dot.dataset.state = d.state;
      if (d.color) dot.style.setProperty('--c', d.color); else dot.style.removeProperty?.('--c');
      // A ghost's dot is as see-through as the ghost (never quite gone, so it still reads).
      dot.style.setProperty('--a', d.state === 'ghost' ? String(Math.max(0.3, Number(d.opacity) || 0)) : '1');
    }
    el.setAttribute('aria-label', L.label);
    el.title = L.label;
    return true;
  }
  el?.addEventListener?.('click', () => { open?.(); });
  doc?.addEventListener?.('chicago4d-confidence', paint);
  paint();
  return { paint, get shown() { return shown; } };
}
