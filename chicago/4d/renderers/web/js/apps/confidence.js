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
  // T-2625: the Confidence chip and its caret left the HUD (§10) and live here, moved in as
  // they are — the same elements, ids and listeners — until the Confidence view app (§09)
  // replaces them. Opening the app opens the levels; C still toggles the view anywhere.
  mount(el) {
    const doc = el.ownerDocument;
    const group = doc.getElementById('confidence-group');
    const lead = doc.createElement('p');
    lead.className = 'nav-sub nav-confidence-lead';
    lead.textContent = 'Colour the town by how sure we are of it, or hide a level to see what the rest of the evidence leaves standing.';
    el.append(lead);
    if (group) el.append(group);
    // In the device the switch says what it switches, in the locked term.
    const label = doc.getElementById('btn-confidence')?.querySelector?.('.chip-label');
    if (label) label.textContent = 'Confidence view';
  },
  shown(el) {
    const doc = el.ownerDocument;
    const group = doc.getElementById('confidence-group');
    if (group && group.parentElement !== el) el.append(group);
    // After the click that opened the app has finished bubbling, or the menu's own
    // click-away (a click outside the group) would shut it again at once.
    const open = () => {
      const menu = doc.getElementById('confidence-menu');
      if (menu?.hidden && !el.hidden) doc.getElementById('btn-confidence-more')?.click();
    };
    (doc.defaultView ?? globalThis).setTimeout(open, 0);
  },
};
