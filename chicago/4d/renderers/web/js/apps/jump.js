/**
 * Jump (SCR 08): the other destinations and Recall to the Observatory (§07).
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'jump',
  label: 'Jump',
  code: 'SCR 08 · JUMP',
  order: 70,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4"/><path d="M12 8v4l3 2"/></svg>',
  // A real screen, loaded on first open (DESIGN §14 "Lazy and light").
  load: () => import('./jump-view.js'),
};
