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
  // T-3629: off the rail. Home's Move tile, the pace readout and Settings open it.
  inRail: false,
  icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="13" cy="4.5" r="1.8"/><path d="m9 21 2.5-6 3 2.5V22"/><path d="m7 12 3-4 4 1 2.5 3.5H19"/><path d="m11.5 15 1-6"/></svg>',
  // The one picker and one slider (T-2651, M6), in the drawer's Move section, moved into
  // the device as it is (T-2620).
  ...sectionScreen('move'),
};
