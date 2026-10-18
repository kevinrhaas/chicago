/** T-2664 — the Field Check's offer on Home and the one-time hints after it (design doc
 * section 11: "It offers itself once after the first landing on a device"; "Contextual hints
 * after the tour are one-time only: first Jaunt, first Jump, first Reconstructed building").
 * Each hint is 14 words or fewer, like a bubble (tools/test_tour_offer.mjs holds it). */
import { register } from './index.js';

export default register('tour', {
  offer: 'First time? Take the 60-second tour',
  'hint.jaunt': 'Read each stop, then press Next Stop to go on.',
  'hint.jump': 'Another year, the same city. Jump takes you back any time.',
  'hint.reconstructed': 'Reconstructed means no record shows this building. We placed it, and say so.',
});
