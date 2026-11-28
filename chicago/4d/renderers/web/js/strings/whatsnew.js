/** T-3813 — the What's new tab: the latest release days as one line per release, and the
 * full history behind a button (Kevin, 2026-11-27: "consolidate it some and save the old
 * version and keep the what's new items more concise"). */
import { register } from './index.js';

export default register('whatsnew', {
  'lead': 'The latest changes. Tap one to read its notes.',
  'unread': '{n} more since your last visit are in the full history.',
  'history': 'Full history',
  'history.note': 'Every release since {date}, {n} in all, as first written.',
  'history.more': 'Show {n} more',
  'history.hide': 'Hide full history',
});
