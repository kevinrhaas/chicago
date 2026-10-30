/** T-2657 — Researcher mode (js/researcher.js) and the visitor's stand-ins for what it holds
 * back. Every string here is linted like any other: no mode shows an internal ticket number,
 * record id or file path (owner, 2026-10-18). */
import { register } from './index.js';

export default register('research', {
  // T-3022: the owner's words for it, "expert research".
  switch: 'Expert research',
  'switch.note': 'Adds a Research tab to every building: its evidence, liberties and full record. This device remembers it.',
  badge: 'RESEARCHER',
  // The three "Why this default" essays, each cut to the reason and what it changes (§12:
  // 40 words at most): the bubble a setting's "Why?" opens (T-2658, js/why-tips.js).
  // Researcher mode shows the full essay instead.
  'why.eye': 'The default, 1.68 m, is the average height of an American man in the 1830s. Raise it if the view feels low; it moves only the camera, never the town.',
  'why.road': 'The default paints the worn earth tracks as the record describes them. Raise it if they are hard to follow; it changes your screen, not the past.',
  'why.brightness': 'The default is the light matched to a July photograph taken at this latitude. Raise it for a dim room or a bright window. It changes nothing else.',
  // T-2658 (§07): the one line under each researched setting, beside its "Why?" button —
  // what the default is, short enough for one line on a phone.
  'hint.eye': 'Set to a man\'s height in the 1830s.',
  'hint.road': 'The tracks as the record describes them.',
  'hint.brightness': 'The light of a July photograph.',
  'why.ask': 'Why?',
  'why.ask.eye': 'Why this eye height',
  'why.ask.road': 'Why this road visibility',
  'why.ask.brightness': 'Why this brightness',
  // A link to the record of how something was worked out, as an external source would be
  // linked (owner, 2026-10-18): plain words, never a number.
  'link.decided': 'How this was decided',
  'link.record': 'The work record',
});
