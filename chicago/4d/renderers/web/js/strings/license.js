/** T-2665 — the Navigator License, the keepsake finishing the Field Check awards (design doc
 * section 11, M10 step 07). Its card sits with the Jaunt keepsakes in the Jaunts app's
 * daybook; the awarded line shows once, as Finish closes the tour. */
import { register } from './index.js';

export default register('license', {
  title: 'Navigator License',
  form: 'License · Field check passed',
  text: 'You looked around, walked, opened a building and asked how sure we are.',
  issued: 'Issued {date} · Good in every year',
  held: 'Good in every year',
  awarded: 'Navigator License earned. It is kept with your keepsakes in Jaunts.',
  'reset-confirm': 'Tap again to clear every jaunt keepsake. The Navigator License stays.',
  'no-jaunt-keepsakes': 'No jaunt keepsakes yet. Finish a jaunt and its memento is kept here.',
});
