/**
 * Inspect (SCR 03): the building dossier (§08). Contextual: it slides in under Jaunts.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'inspect',
  label: 'Inspect',
  code: 'SCR 03 · INSPECT',
  order: 20,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-6h6v6"/><path d="M4 21h16"/></svg>',
  // A building is selected, or one is under the reticle within 40 m; it stays 300 ms after
  // the target is lost, so a glance away does not make it flicker (QA-07).
  when: (ctx) => !!(ctx.selected || ctx.target),
  linger: 300,
  // Stub until the dossier lands (§08): the building's card, as a tap on it opens it.
  launch: (ctx) => ctx.actions?.inspect?.(ctx.selected ?? ctx.target?.id),
};
