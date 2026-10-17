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
  'move.note': 'The speeds for walking, running, a wagon and a horse, your eye height and the other comfort settings are under',
  'move.mode': 'How you move',
  // T-2727: Move › When you pick a place, and a Jaunt that cannot go the visitor's way.
  'move.jaunts': 'Jaunts use my choice',
  'move.arrive.note': 'Go to and the map use this choice. Jaunts keep the way each recommends, unless Jaunts use my choice is on. Then they use yours where they can.',
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
});
