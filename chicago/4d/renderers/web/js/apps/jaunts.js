/**
 * Jaunts (SCR 02): Jaunts · Go to · Free roam, the Welcome card's choices for good
 * (DESIGN §07). Always on the rail.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { sectionScreen } from './drawer-host.js';

export default {
  id: 'jaunts',
  label: 'Jaunts',
  code: 'SCR 02 · JAUNTS',
  order: 10,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/><path d="M8 18h6a4 4 0 0 0 0-8h-4a4 4 0 0 1 0-8h6"/></svg>',
  // The drawer's Go to section, moved in as it is (T-2620), under a key to the Jaunts list
  // the arrival device holds (Start / Jaunts opens the same). E4 redesigns the app.
  ...sectionScreen('jaunts', {
    lead(doc, ctx) {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = 'nav-key nav-jaunts-open';
      b.id = 'nav-jaunts-open';
      b.textContent = 'Take a Jaunt';
      b.addEventListener('click', () => { ctx.navigator?.dock?.(); ctx.actions?.jaunts?.(); });
      return b;
    },
  }),
};
