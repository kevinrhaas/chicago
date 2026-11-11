/** T-2656 — the Navigator's Settings app (DESIGN §07 "Settings"): Display, Machine,
 * Performance with Auto, Sound, Units, and About & What's new. The groups the drawer
 * already had (Show, Movement, Units) keep their markup words; these are the new ones. */
import { register } from './index.js';

export default register('settings', {
  'research': 'Research',
  'display': 'Display',
  'theme': 'Light or dark',
  'theme.dark': 'Dark',
  'theme.light': 'Light',
  'textSize': 'Text size',
  'machine': 'Machine',
  'auto.use': 'Use Auto',
  'auto.on': 'Using Auto',
  'auto.line': 'Auto for this device: {detail} detail, {sharpness} sharpness, adaptive pacing.',
  'sound': 'Sound',
  'sound.master': 'Master',
  'sound.effects': 'Effects',
  'sound.ambience': 'Ambience',
  'sound.music': 'Music',
  'sound.off': 'Off',
  // T-2659: that the ambience is mood, not a recording; T-3445 cut it to that and Master.
  'sound.note': 'Off until you enable sound. Recorded ambience and era music; not a recording of the past.',
  'about': "About & What's new",
  'whatsnew.line': 'Release notes',
});
