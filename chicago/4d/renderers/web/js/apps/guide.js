/**
 * Guide (SCR 09): Tour mode, controls, glossary and "Is this real?". Pinned to the foot.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { sectionScreen } from './drawer-host.js';

export default {
  id: 'guide',
  label: 'Guide',
  code: 'SCR 09 · GUIDE',
  order: 90,
  pin: 'bottom',
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7"/><path d="M12 17h.01"/></svg>',
  // The controls sheet (T-2661), device-aware: touch or keyboard, from controls/intent.js,
  // with T-2662's glossary and questions. Under it, the drawer's Guide and Sources
  // sections, moved in as they are (T-2620); the old Sources hub is Guide › About this
  // destination, four cards (T-2667), which the sheet's own block opens.
  // `load` hands back the screen at once, so the rail switches to Guide in the same turn;
  // the sheet's module loads behind it and fills its own element when it arrives (on a
  // starved runner a first lazy load took longer than a 10 s wait, T-2620). The sheet
  // repaints its own element, so it gets one of its own, and the moved #panel sits after it.
  load: () => screen,
};

const sections = sectionScreen('guide');
const state = { sheet: null, view: null, ctx: null, on: false };
const screen = {
  mount(el, ctx) {
    // T-3021 (the owner, 2026-10-22: "there should be an option to take the tour anytime
    // even if you skip it"): the tour's block leads the screen, lifted out of the Guide
    // section it was written into, so its key keeps the id and listener main.js gave it.
    const tour = el.ownerDocument.getElementById('guide-tour');
    if (tour) el.append(tour);
    const sheet = el.ownerDocument.createElement('div');
    sheet.className = 'nav-guide-sheet';
    el.append(sheet);
    state.sheet = sheet;
    state.ctx = ctx;
    sections.mount(el, ctx);
    // Not returned: the rail would wait for it, and the point is that it does not.
    import('./guide-view.js').then((view) => {
      if (state.sheet !== sheet) return;
      state.view = view;
      view.mount(sheet, state.ctx);
      if (state.on) view.shown?.(sheet, state.ctx);
    }).catch(() => { /* the sections stay; the sheet's lane reports its own load */ });
  },
  shown(el, ctx) {
    state.on = true;
    state.ctx = ctx;
    state.view?.shown?.(state.sheet, ctx);
    sections.shown(el, ctx);
  },
  hidden(el, ctx) {
    state.on = false;
    sections.hidden(el, ctx);
  },
  unmount() {
    state.view?.unmount?.(state.sheet);
    state.sheet = null;
    state.view = null;
  },
};
