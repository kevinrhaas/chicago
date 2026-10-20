/**
 * Map (SCR 05): the whole field with your arrow, tap-to-travel and the Jaunt route.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'map',
  label: 'Map',
  code: 'SCR 05 · MAP',
  order: 40,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/></svg>',
  // T-2654: its own screen, loaded on first open (DESIGN §14 "Lazy and light").
  load: () => import('./map-view.js'),
};
