/**
 * Jaunts (SCR 02): Jaunts · Go to · Free roam, the Welcome card's choices for good
 * (DESIGN §07, T-2630). Always on the rail.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'jaunts',
  label: 'Jaunts',
  code: 'SCR 02 · JAUNTS',
  order: 10,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/><path d="M8 18h6a4 4 0 0 0 0-8h-4a4 4 0 0 1 0-8h6"/></svg>',
  // T-2630: a real screen — Jaunts · Go to · Free roam — loaded on first open (jaunts-view.js).
  load: () => import('./jaunts-view.js'),
};
