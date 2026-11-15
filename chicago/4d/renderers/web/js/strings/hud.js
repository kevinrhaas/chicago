/** T-2624 — the HUD and its drawer: the rail's section names (section 03's renames:
 * Travel → Move, Firms → Shops & work, Evidence → Sources, Controls → Guide), the chips
 * and the messages the HUD says. Element ids and data-tab values do not change. */
import { register } from './index.js';

export default register('hud', {
  'tab.goto': 'Go to',
  'tab.move': 'Move',
  'tab.people': 'People',
  'tab.shops': 'Shops & work',
  'tab.shops.short': 'Shops',
  'tab.sources': 'Sources',
  'tab.settings': 'Settings',
  'tab.guide': 'Guide',
  'tab.whatsnew': "What's new",
  'menu.unread': "Guide, settings and what's new — {n} unread (H)",
  'move.note': 'Speeds, eye height and comfort:',
  'move.mode': 'How you move',
  // T-2727: Move › When you pick a place, and a Jaunt that cannot go the visitor's way.
  'move.jaunts': 'Jaunts use my choice',
  'move.arrive.note': 'Applies to Go to and the map.',
  'jaunt.keeps': 'Your choice ({way}) is not a way this Jaunt can be travelled, so it keeps the way it recommends.',
  'sources.list': 'Source list',
  'sources.grades': 'Attested, Inferred, Reconstructed: what each word promises',
  'levels.all': 'Showing every grade again',
  'fly.walk': 'Walk',
  'fly.fly': 'Fly',
  'fly.back': 'Back to walking (F)',
  'fly.up': 'Free-fly — rise above the town (F)',
  'notes.failed': 'The release notes could not load. Reopen this tab to retry.',
  'going': 'Going to',
  // T-3557: aboard a driven team (transport-interactions.js), on the travel bar and the hint line.
  'ride.aboard': 'Aboard',
  'ride.driving': 'Driving',
  'ride.getDown': 'Get down',
  'ride.keys': 'W/S go · whoa · A/D steer',
  'ride.stick': 'Stick: go · steer',
  'ride.reins.keys': 'Reins: W go · S whoa · A/D steer',
  'ride.reins.touch': 'Reins: stick up go · down whoa · sideways steer',
  'ride.returning': 'heading back',
  'ride.still': 'reduced motion: standing',
  'ride.held': 'held: {why}',
  // T-3557: inside the Glessner brougham's cab, and the coachman's way home and out again.
  'ride.inside': 'Riding in',
  'ride.getOut': 'Get out',
  'ride.home': 'driving home to the coach house',
  'ride.out': 'coming out of the coach house',
  'ride.stood': 'in the coach house',
  // T-2629: Settings › About.
  'about.title': 'About',
  'about.dev': 'DEV',
  'about.devNote': 'A preview build: not production, and not indexed.',
  'about.production': 'Open production',
  'about.unpublished': 'An unpublished build',
});
