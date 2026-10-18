/** T-2656 — the Navigator's Settings app (DESIGN §07 "Settings"): Display, Machine,
 * Performance with Auto, Sound, Units, and About & What's new. The groups the drawer
 * already had (Show, Movement, Units) keep their markup words; these are the new ones. */
import { register } from './index.js';

export default register('settings', {
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
  'sound.off': 'Off',
  'sound.none': 'Nothing in the town makes a sound yet. These are kept for when it does.',
  'about': "About & What's new",
  'whatsnew.line': 'Release notes',
});
