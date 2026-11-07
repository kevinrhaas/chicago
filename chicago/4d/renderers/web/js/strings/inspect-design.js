/** T-2641 — Inspect's Design tab (design doc "Field Navigator Mk II" §08 "Design", §12 "Style
 * library"); T-3435 made it a written style guide for every building: a head, a lead, Look for,
 * five parts in a fixed order, what the model was built from, then the style card and Compare
 * styles where a style module is named. The kickers are written in sentence case and drawn in
 * capitals by the stylesheet. */
import { register } from './index.js';

export default register('inspect-design', {
  kicker: 'Style guide',
  'chip.built': 'Built {year}',
  look: 'Look for',
  'look.tap': 'Look for · tap to see it',
  'look.label': 'Features of this building, numbered',
  'look.go': 'Show me: {text}',
  'part.shape': 'Shape',
  'part.walls': 'Walls',
  'part.roof': 'Roof',
  'part.openings': 'Windows and doors',
  'part.grounds': 'Grounds',
  'part.none': 'Our records do not say.',
  basis: 'Built from',
  'basis.draft': 'A stand-in from the map until it is modelled from pictures.',
  'about.style': 'About the style',
  cues: 'How to spot it',
  liberty: 'Listed in Liberties.',
  compare: 'Compare styles',
  'compare.open': 'How to spot {name}',
  'plate.alt': 'Picture: {caption}',
  'more.details': 'Every fact, graded',
  'more.sources': 'Where it comes from',
  shape: 'Its shape on the ground',
});
