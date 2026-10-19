/** T-2667 (NAV-1002) — Guide › About this destination: the old research hub's topics folded
 * into four cards (design doc section 12), and the order book behind Researcher mode
 * (owner ruling 2026-10-16). js/evidence.js draws the cards over the topics; the Guide's
 * own block (apps/guide-view.js) opens them. A key with a `researcher` segment is shown
 * only while Researcher mode is on (strings/index.js, isResearcherKey). */
import { register } from './index.js';

export default register('guide-about', {
  // The section's tab in Guide, and the head it shows.
  tab: 'About',
  'tab.title': 'About this destination',
  // The Guide's block that opens the four cards.
  k: 'About this destination',
  title: 'How we know what you see',
  intro: 'Four cards on where this town comes from. Tap one to open it.',
  // The four cards, in order. A card holds the topics evidence.js files under it.
  'card.grading': 'How we grade',
  'card.grading.line': 'Every fact carries a grade: Attested, Inferred or Reconstructed. Here is what each one promises.',
  'card.sources': 'Sources',
  'card.sources.line': 'The maps, books, photos and newspapers behind the town, each one named.',
  'card.sources.inspect': "One building's own sources are on its Sources tab in Inspect.",
  'card.liberties': 'Liberties',
  'card.liberties.line': 'Every choice we made without a source, by name. Also what we left out, and what is still open.',
  'card.liberties.inspect': "One building's own Liberties are on its Sources tab in Inspect.",
  'card.living': 'What lived and grew here',
  'card.living.line': 'The land itself, and the life our sources name on it.',
  // One line under each topic's tile. The grades line is the HUD's (hud.sources.grades).
  'topic.city': 'The town in numbers: what stands, who is named, and what each grade promises',
  'topic.sources': 'The sources: what each one supplied, and where it shows',
  'topic.liberties': 'Every value a record states without a source, admitted by name',
  'topic.exclusions': 'Buildings researched and left out: dated later, or already gone',
  'topic.uncertain': 'Doubts on the record, and what settling them would change',
  'topic.ground': 'The ground’s own graded claims: water, levels, banks',
  'topic.fauna': 'Animals researched into ten habitats, for 1 July. None are drawn.',
  'topic.plants': 'Plant communities and their species, for 1 July',
  'topic.population': 'Who the sources actually name, profiled axis by axis',
  // Researcher mode only (T-2657's switch): the order book is internal language.
  'researcher.card': 'Reconstructing the town',
  'researcher.card.line': 'For researchers: the order book, what the town still owes, bucket by bucket.',
  'researcher.topic.orderbook': 'What the town still owes: the quota, bucket by bucket',
});
