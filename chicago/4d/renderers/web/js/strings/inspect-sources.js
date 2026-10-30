/** T-2644 — Inspect's Sources tab (design doc §08 "Sources", §12 "Move one level down").
 * Facts grouped by grade, Liberties as a section, human source titles, and the full citation
 * folded under each fact. The grade words and their plain lines come from terms.js. */
import { register } from './index.js';

export default register('inspect-sources', {
  lead: '{count} facts. {split}. Tap any one to see its sources.',
  'lead.one': '1 fact. {split}. Tap it to see its sources.',
  none: 'No facts in this group.',
  'off-scale': '{count} carry no grade on our scale. That is a fault in our record.',
  why: 'Why',
  'why.researchers': 'The reasoning for this one is written for researchers. It is in the full record.',
  absent: 'Not drawn in the 3-D town.',
  'sources.k': 'Where it comes from',
  'sources.none': 'No source is named for this one.',
  'sources.none.attested': 'No source is named, though this grade needs one. That is a fault in our record.',
  'source.untitled': 'A source with no title in our records',
  // What kind of source it is, from the evidence ladder's own definition of each rung
  // (docs/PROVENANCE.md § Evidence tiers). "from the time" is said only of a source whose
  // recorded date falls on or before the scene's year; every other source says its kind.
  'when.period': 'from the time',
  'kind.1': 'first-hand',
  'kind.2': 'a witness remembering',
  'kind.3': 'gathered from witnesses',
  'kind.4': "a historian's account",
  'kind.5': 'a modern reconstruction',
  'kind.6': 'a popular map',
  'cites.one': 'The full citation',
  'cites.many': 'The full citations',
  'liberties.none': 'No liberties are written down for this building. That does not mean none were taken.',
  'liberties.unread': 'Our list of liberties could not be read just now.',
  'liberties.researchers': 'The full entry is written for researchers. It is in the full record.',
  'liberty.untitled': 'A choice written down in the full record',
  'open.k': 'Is this settled?',
  'open.lead': 'No. This building is on our list of open questions.',
  'open.change': 'What it would change',
  'dossier.link': 'Read the research dossier',
  'dossier.none': 'No dossier has been written for this building yet.',
  'full.record': 'Full record',
  'label.today': 'Today',
  'label.built': 'Built',
  'label.look': 'Look for',
  'label.notable': 'Notable fact',
  'label.stood': 'Stood here',
  'label.stood.whether': 'Whether it stood here',
  'stood.in': 'In {year}',
  'label.place': 'Where it stood',
  'label.outline': 'Its outline',
  'label.detail': 'A recorded detail',
  'attr.present-status': 'Today',
  'attr.function': 'Use',
  'attr.built': 'Year built',
});
