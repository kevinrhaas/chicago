/** T-3743 — the Report a bug key and its sheet (js/bug-report.js). */
import { register } from './index.js';

export default register('bugs', {
  key: 'Report a bug',
  title: 'Report a bug',
  close: 'Close',
  includeShot: 'Include this picture of the town',
  noShot: 'No picture: the town had not drawn yet.',
  shotAlt: 'The view you are reporting',
  comment: 'What went wrong?',
  placeholder: 'What you did, what you saw, what you expected.',
  what: 'Sent with it: your sign-in, the year, where you stand, settings, device, graphics, memory and recent errors.',
  cancel: 'Cancel',
  send: 'Send',
  copy: 'Copy report',
  sending: 'Sending…',
  sent: 'Sent. Thank you.',
  failed: 'That did not go through. Check your connection and try again.',
  notLive: 'Reports are sent only from the live site. Copy it instead.',
  copied: 'Report copied.',
  copyFailed: 'Copy was refused by this browser.',
  'settings.row': 'Report a bug key',
});
