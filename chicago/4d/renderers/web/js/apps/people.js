/**
 * People (SCR 04): who lived and worked nearby, with Shops & work as a filter.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { sectionScreen } from './drawer-host.js';

export default {
  id: 'people',
  label: 'People',
  code: 'SCR 04 · PEOPLE',
  order: 30,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.5A5 5 0 0 1 22 19"/></svg>',
  // Only a scene with a people directory: 1835's town, 1904's Glessner household (T-2702).
  when: (ctx) => !!ctx.hasPeople,
  // Where the scene has the drawer's People and Businesses sections (1835), they move in here
  // as they are (T-2620); where it has none (1904, T-1740), the People screen loads instead.
  async mount(el, ctx) {
    this.mode = ctx.peopleSection ? sectionScreen('people') : await import('./people-view.js');
    return this.mode.mount(el, ctx);
  },
  shown(el, ctx) { this.mode?.shown?.(el, ctx); },
  hidden(el, ctx) { this.mode?.hidden?.(el, ctx); },
};
