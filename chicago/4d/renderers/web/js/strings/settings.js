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
  'sound.off': 'Off',
  // T-2659: what each level covers, and that the ambience is mood, not a recording.
  'sound.note': "Effects are the year ticker, the landing, and the Navigator's clicks and hum. Ambience is a quiet tone for each destination, made up for mood: it is not a recording of the past. Sound is off until you raise Master. It starts with your first tap, and Master at Off is silence.",
  'about': "About & What's new",
  'whatsnew.line': 'Release notes',
});
