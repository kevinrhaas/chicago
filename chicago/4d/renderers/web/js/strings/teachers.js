/** T-2666 (NAV-806) — Guide › For teachers: the field check on one printed page, with three
 * suggested Jaunts for each destination (js/apps/teacher-handout.js draws it). */
import { register } from './index.js';

export default register('teachers', {
  k: 'For teachers',
  title: 'The field check, on one page',
  intro: 'Print the eight steps and three Jaunts for each destination. It fits one sheet.',
  print: 'Print the handout',
  preview: 'Read the handout here',
  'handout.title': 'Navigator field check',
  'handout.lede': 'Sixty seconds of training in eight steps. Each step waits until the student does it.',
  'handout.start': 'To begin, open Guide and choose Take the tour. Skip is always there.',
  'handout.steps': 'The eight steps',
  'handout.jaunts': 'Three Jaunts for each destination',
  'handout.rule': 'Suggested: the featured Jaunts first, then the shortest.',
  'handout.dest': '{year} · {place}',
  'handout.stops': '{n} stops',
  'handout.reading': 'Reading the Jaunts…',
  'handout.none': 'No Jaunts here yet.',
  'handout.unread': 'The Jaunts could not be read just now.',
  'handout.foot': 'Every building carries a grade: Attested, Inferred or Reconstructed. The Confidence view colors the town by it.',
});
