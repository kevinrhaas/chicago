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
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5.5 5.5"/></svg>',
  // A building is selected, or one is under the reticle within 40 m; it stays 300 ms after
  // the target is lost, so a glance away does not make it flicker (QA-07).
  // §14: the first time a target appears, the scene's summaries are fetched, once (T-2638).
  when: (ctx) => {
    const on = !!(ctx.selected || ctx.target);
    if (on) void ctx.actions?.inspectSummaries?.();
    return on;
  },
  linger: 300,
  // The Overview front page (T-2638, §08 M7), loaded on first open. The building card stays
  // the full record, opened from it, until the Inspect tabs land (T-2639).
  load: () => import('./inspect-view.js'),
};
