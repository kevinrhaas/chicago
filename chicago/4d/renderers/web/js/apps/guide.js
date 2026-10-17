/**
 * Guide (SCR 09): Tour mode, controls, glossary and "Is this real?". Pinned to the foot.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'guide',
  label: 'Guide',
  code: 'SCR 09 · GUIDE',
  order: 90,
  pin: 'bottom',
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7"/><path d="M12 17h.01"/></svg>',
  // The controls sheet (T-2661), device-aware: touch or keyboard, from controls/intent.js.
  // Under it, the drawer's Guide and Sources sections, moved in as they are (T-2620);
  // Sources becomes the Guide's own in T-2667. The sheet repaints its own element, so it
  // gets one of its own, and the moved #panel sits after it.
  load: async () => {
    const [view, { sectionScreen }] = await Promise.all([import('./guide-view.js'), import('./drawer-host.js')]);
    const sections = sectionScreen('guide');
    const sheetOf = new WeakMap();
    return {
      mount(el, ctx) {
        const sheet = el.ownerDocument.createElement('div');
        sheet.className = 'nav-guide-sheet';
        el.append(sheet);
        sheetOf.set(el, sheet);
        view.mount(sheet, ctx);
        sections.mount(el, ctx);
      },
      shown(el, ctx) {
        view.shown?.(sheetOf.get(el), ctx);
        sections.shown(el, ctx);
      },
      hidden(el, ctx) { sections.hidden(el, ctx); },
      unmount(el) { view.unmount?.(sheetOf.get(el)); },
    };
  },
};
