/** T-2657 — Researcher mode (js/researcher.js) and the visitor's stand-ins for what it holds
 * back. Every string here is linted like any other: no mode shows an internal ticket number,
 * record id or file path (owner, 2026-10-18). */
import { register } from './index.js';

export default register('research', {
  // T-3022: the owner's words for it, "expert research".
  switch: 'Expert research',
  'switch.note': 'Adds a Research tab to every building.',
  badge: 'RESEARCHER',
  // A link to the record of how something was worked out, as an external source would be
  // linked (owner, 2026-10-18): plain words, never a number.
  'link.decided': 'How this was decided',
  'link.record': 'The work record',
});
