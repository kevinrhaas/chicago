/** The Confidence view's overlays, at the foot of the app (T-2650, NAV-605; DESIGN §09, M9):
 * street names, building labels, people pins and the Jaunt route, each with its own switch.
 * Each switch's line says what this destination has for it, or that it has none. */
import { register } from './index.js';

export default register('confidence-overlays', {
  'title': 'Overlays',
  'group': 'Overlays on the town',
  'streets': 'Street names',
  'streets.note': 'The {year} street you stand on and today\'s, under the compass.',
  'streets.none': 'No streets are drawn in {year} yet, so only today\'s names show.',
  'labels': 'Building labels',
  'labels.note': '{count} buildings in {year} have a name of their own. The nearest in sight are labelled.',
  'labels.one': 'One building in {year} has a name of its own. It is labelled when in sight.',
  'labels.none': 'No building in {year} has a name of its own yet.',
  'labels.hidden': 'Buildings at a hidden grade are not labelled.',
  'people': 'People pins',
  'people.note': '{people} people at {places} known addresses in {year}. Tap a pin to see who.',
  'people.none': 'No people directory for {year} yet.',
  'people.nowhere': 'Nobody in the {year} directory has a known address yet.',
  'people.reading': 'Reading the people directory…',
  'people.pin': '{count} people here. Tap to see who.',
  'people.pin.one': 'One person here: {name}. Tap to see who.',
  'people.lives': 'Lives here',
  'people.works': 'Works here',
  'people.review': 'This record carries a standing review. Its card says why.',
  'people.close': 'Close',
  'people.more': 'and {count} more in People',
  'route': 'Jaunt route',
  'route.note': 'The Jaunt under way: {stops} stops, the next one ringed.',
  'route.nowhere': 'This Jaunt\'s stops have no place in the town to draw.',
  'route.idle': 'No Jaunt under way. Start one in Jaunts and its route shows here.',
  'route.none': 'No Jaunts for {year} yet.',
  'route.stop': 'Stop {n}',
});
