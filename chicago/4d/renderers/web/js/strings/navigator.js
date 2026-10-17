/** T-2624 — the Navigator shell and its Home (T-2617, T-2618). Each app's own name and
 * screen code stay in its manifest under js/apps/, which is that app's section of the
 * table: tools/check_strings.py lints them with everything here. */
import { register } from './index.js';

export default register('nav', {
  name: 'Navigator',
  label: 'NAVIGATOR MK II',
  'home.code': 'SCR 01 · HOME',
  'home.title': 'Navigator Home',
  rail: 'Navigator apps',
  open: 'Open the Navigator',
  'open.on': 'Open the Navigator on {app}',
  lower: 'Lower the Navigator',
  collapse: 'Collapse the Navigator',
  'collapse.short': 'Collapse',
  'open.short': 'Open',
  'where.k': 'You are at',
  'where.looking': 'Looking for the street…',
  'where.off': 'Off the streets',
  'front.k': 'Right in front of you',
  'front.none': 'Nothing close by',
  'front.turn': 'Turn toward a building within {distance}.',
  'front.away': '{distance} away',
  'front.building': 'A building',
  inspect: 'Inspect {name}',
  'jaunt.k': 'Jaunt in progress',
  'tile.move': 'Move',
  'tile.confidence': 'Confidence view',
  on: 'On',
  off: 'Off',
  'move.fly': 'Flying',
  'move.walk': 'Walking',
  'move.wagon': 'By wagon',
  'move.horse': 'On horseback',
  'move.riding': '{how}, on the way',
});
