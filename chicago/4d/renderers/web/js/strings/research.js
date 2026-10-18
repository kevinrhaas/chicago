/** T-2657 — Researcher mode (js/researcher.js) and the visitor's stand-ins for what it holds
 * back. Every string here is linted like any other: no mode shows an internal ticket number,
 * record id or file path (owner, 2026-10-18). */
import { register } from './index.js';

export default register('research', {
  switch: 'Researcher mode',
  'switch.note': 'Shows the full reasoning and the working records we keep for researchers, in place. This device remembers it.',
  badge: 'RESEARCHER',
  // The three "Why this default" essays, each cut to the reason and what it changes (§12:
  // 40 words at most). Researcher mode shows the full essay beneath.
  'why.eye': 'The default, 1.68 m, is the average height of an American man in the 1830s. Raise it if the view feels low; it moves only the camera, never the town.',
  'why.road': 'The default paints the worn earth tracks as the record describes them. Raise it if they are hard to follow; it changes your screen, not the past.',
  'why.brightness': 'The default is the light matched to a July photograph taken at this latitude. Raise it for a dim room or a bright window. It changes nothing else.',
  // A link to the record of how something was worked out, as an external source would be
  // linked (owner, 2026-10-18): plain words, never a number.
  'link.decided': 'How this was decided',
  'link.record': 'The work record',
});
