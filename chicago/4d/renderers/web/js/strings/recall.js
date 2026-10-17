/** T-2735 — the way home: the recall prompt and the reverse ring.
 * Machine lore (the eyebrow, the ring's lines, the lamps) is written in sentence case here;
 * the stylesheet sets it in mono caps. */
import { register } from './index.js';

export default register('recall', {
  eyebrow: 'Temporal recall',
  code: '{year} › Observatory',
  'code.plain': 'Observatory',
  title: 'Return to the Temporal Observatory?',
  body: 'This releases the lock on Chicago, {year}.',
  'body.plain': 'This releases the lock on this destination.',
  cancel: 'Cancel',
  confirm: 'Return',
  'ring.release': 'Releasing field lock',
  'ring.rewind': 'Time mesh rewinding',
  'ring.home': 'Recall confirmed · Observatory',
  'lamp.arrive': 'Arrive',
  'lamp.lock': 'Lock',
  'lamp.scan': 'Scan',
  abort: 'Abort',
});
