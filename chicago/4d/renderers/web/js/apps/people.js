/**
 * People (SCR 04): who lived and worked nearby, with Shops & work as a filter.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'people',
  label: 'People',
  code: 'SCR 04 · PEOPLE',
  order: 30,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.5A5 5 0 0 1 22 19"/></svg>',
  // Only a scene with people records: 1835's directory. (1904 has none yet, so none shows.)
  when: (ctx) => !!ctx.hasPeople,
  // Stub until the People app lands: the drawer's People section.
  launch: (ctx) => ctx.actions?.openSection?.('people'),
};
