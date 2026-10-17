/**
 * Move (SCR 06): Walk · Run · Wagon · Horse · Fly, speed, getting there, comfort.
 *
 * A Navigator app (T-2618): see js/nav-rail.js for the fields. Its lane owns this file.
 */
import { sectionScreen } from './drawer-host.js';

export default {
  id: 'move',
  label: 'Move',
  code: 'SCR 06 · MOVE',
  order: 60,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 16c-1.5 0-2.5-1.5-2.5-4S6.5 6 8 6s2.5 2 2.5 4.5S9.5 16 8 16z"/><path d="M16 20c-1.5 0-2.5-1.5-2.5-4s1-6 2.5-6 2.5 2 2.5 4.5S17.5 20 16 20z"/></svg>',
  // The drawer's Travel section, moved in as it is (T-2620) until the Move app's own ticket (M6).
  ...sectionScreen('move'),
};
