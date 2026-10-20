/** T-2641 — Inspect's Design tab (design doc "Field Navigator Mk II" §08 "Design", §12 "Style
 * library"): the style card, the numbered "On this house" hotspots and Compare styles. The
 * kickers are written in sentence case and drawn in capitals by the stylesheet. */
import { register } from './index.js';

export default register('inspect-design', {
  kicker: 'Style guide',
  'style.none': 'No style guide has been written for this building yet.',
  cues: 'How to spot it',
  hotspots: 'On this house',
  'hotspots.tap': 'On this house · tap to look',
  'hotspots.none': 'Our records say nothing yet about how this building was made.',
  'hotspots.label': 'Features of this building, numbered',
  'hotspot.look': 'Show me: {text}',
  shape: 'Its shape on the ground',
  liberty: 'Listed in Liberties.',
  compare: 'Compare styles',
  'compare.open': 'How to spot {name}',
  'plate.alt': 'Picture: {caption}',
});
