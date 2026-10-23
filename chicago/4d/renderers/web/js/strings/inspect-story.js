/** T-2643 — Inspect's Story tab (design doc "Field Navigator Mk II" §08 "Story", §12): the
 * timeline from design to today, with BUILT, YOU ARE HERE and TODAY marked on it. The kickers
 * are written in sentence case and drawn in capitals by the stylesheet. */
import { register } from './index.js';

export default register('inspect-story', {
  title: 'Story',
  lead: 'From design to today. Your visit is {date}.',
  'lead.year': 'From design to today. Your visit is in {year}.',
  built: 'Built',
  'built.none': 'Our records give no date for when it was built.',
  'built.phrase': 'Built {phrase}.',
  stood: 'Stood here',
  'stood.span': 'On record standing {span}.',
  here: 'You are here',
  today: 'Today',
  'today.none': 'Our records do not say what stands here now.',
  after: 'After your visit',
  'fire.inside': 'The town draws a fire limit. This building is inside it, so no hay may be stacked here.',
  'fire.outside': 'The town draws a fire limit round its built-up streets. This ground is outside it.',
  'list.label': 'Timeline, from design to today',
});
