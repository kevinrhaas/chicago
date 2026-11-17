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
  // T-3629: off the rail. The year chip and Home's Other years key open it.
  inRail: false,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="13.5" r="7.5"/><path d="M12 13.5V10M10 2.5h4M12 2.5V6M18.5 6.5l1.5-1.5"/></svg>',
  // A real screen, loaded on first open (DESIGN §14 "Lazy and light").
  load: () => import('./jump-view.js'),
};
