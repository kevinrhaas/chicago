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
  load: () => import('./guide-view.js'),
};
