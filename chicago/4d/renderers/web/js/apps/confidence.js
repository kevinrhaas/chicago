/**
 * Confidence view (SCR 07): show, hide, colour and opacity per grade (§09).
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
export default {
  id: 'confidence',
  label: 'Confidence view',
  code: 'SCR 07 · CONFIDENCE VIEW',
  order: 50,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  // The icon glows while the Confidence view is on.
  glow: (ctx) => !!ctx.confidenceOn,
  // Stub until the Confidence view app lands (§09): the HUD's grade menu.
  launch: (ctx) => ctx.actions?.confidenceMenu?.(),
};
