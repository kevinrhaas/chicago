/**
 * Home (SCR 01): where you are, what is in front of you, the Jaunt in progress,
 * Move and the Confidence view. Its screen is the static #nav-home that navigator.js
 * paints (T-2617); it ships in the boot payload, as DESIGN §14 asks of Home alone.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'home',
  label: 'Home',
  code: 'SCR 01 · HOME',
  order: 0,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11 12 4l8 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/></svg>',
  panel: 'nav-home',
};
