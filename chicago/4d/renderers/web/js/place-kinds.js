/**
 * place-kinds.js — what KIND of place a Go-to row is, and whether the building it names
 * is a claim or a reconstruction.
 *
 * The owner, 2026-09-04: Go to should hide the reconstructed roofs by default and filter
 * "like taverns, shops, etc." Two rules live here so the menu, its pills and its note all
 * read the same ones:
 *
 * **Presence** — `presenceGrade(s)` answers "did this building stand HERE on the scene
 * date?" It is `documented_range.confidence`, the grade the record puts on the building's
 * existence, not on where the model stands (that is `placement.position_confidence`, a
 * different question the row carries as `data-jump-position`). A record with neither is a
 * reconstruction: the compiler grades every roof it derives, so an ungraded record is one
 * that nobody wrote a source for. That is the honest default — the other one would promote
 * a guess by omission, which AGENTS.md rules out in as many words.
 *
 * **Kind** — `placeKind(sidecar, id)` sorts a structure into one of the pill groups from
 * the record's own words, in a fixed precedence: what the record says the building was FOR
 * (`attributes.function.value`), then what archetype it was dealt, then the noun in its
 * title, then Homes & yards. The regex tables are ORDERED — waterfront before public before
 * taverns before stores before trades before homes — because the descriptions are hedged
 * ("small shop or office", "store and dwelling", "hotel stable") and the first reading is
 * the one the town would have used: a hotel's stable is part of the hotel, a freight shed
 * on the north bank is waterfront, a store-residence is a store. The one exception outside
 * the tables is the stockade: a root cellar or a provision store inside Fort Dearborn is
 * the garrison's, so a `fort_structure`/`palisade` archetype pulls those two readings into
 * Public & fort rather than into a homestead or a shop row.
 */

/** The pill groups, in the order the menu shows them. */
export const KINDS = [
  { id: 'viewpoints', label: 'Viewpoints' },
  { id: 'corners', label: 'Corners' },
  { id: 'people', label: 'People' },
  { id: 'taverns', label: 'Taverns & hotels' },
  { id: 'stores', label: 'Stores' },
  { id: 'trades', label: 'Trades' },
  { id: 'homes', label: 'Homes & yards' },
  { id: 'public', label: 'Public & fort' },
  { id: 'waterfront', label: 'Waterfront' },
];

/** Whether the building stood here: attested | inferred | reconstructed. */
export function presenceGrade(s) {
  return s?.documented_range?.confidence || s?.placement?.position_confidence || 'reconstructed';
}

/** A roof the menu hides until the visitor asks for it. */
export const isReconstructed = (s) => presenceGrade(s) === 'reconstructed';

/** Ordered: the first table whose pattern matches wins. */
const FUNCTION_TABLE = [
  ['waterfront', /river crossing|street crossing|harbou?r|pier|wharf|ferry|forwarding|commission|freight|warehouse|light$/],
  ['public', /church|school|meeting|jail|council|agency|pound|barracks|quarters|magazine|guard house|block-?house|artillery|parade|flagstaff|military|sutler|palisade/],
  ['taverns', /tavern|inn\b|hotel|boarding|lodging/],
  ['stores', /store|grocery|provision|drug|auction|trading house/],
  ['trades', /shop|smith|cooper|tannery|wheelwright|saddler|harness|tailor|shoemaker|barber|butcher|bakery|gunsmith|soap|candle|slaughter|packing|brickyard|sawpit|printing office|physician|office|workshop|manufactory|wash house/],
  ['homes', /dwelling|cottage|house|shanty|residence|farmstead|stable|barn|shed|privy|cellar|utility|carriage|wagon yard/],
];

/** The archetype a roof was dealt, when its function says nothing the tables know. */
const ARCHETYPE_KIND = {
  fort_structure: 'public', palisade: 'public',
  bridge_timber: 'waterfront', pier_crib: 'waterfront',
  frame_tavern: 'taverns', frame_storefront: 'stores',
  frame_dwelling: 'homes', log_dwelling: 'homes', outbuilding: 'homes',
};

/** The anonymous programme's family letters, read off what each family's 1835 roofs were
 *  dealt as functions (D and A dwellings and yards, C fronts, W workshops, H houses, F
 *  freight, I institution, T tavern). Every 1835 record carries a function, so this is a
 *  fallback for a record the compiler has not graded yet, not a rule the data exercises. */
const FAMILY_KIND = { D: 'homes', A: 'homes', C: 'stores', W: 'trades', H: 'homes', F: 'waterfront', I: 'public', T: 'taverns' };

const FORT_ARCHETYPES = new Set(['fort_structure', 'palisade']);

/** Lower-case, underscores to spaces, and only the first clause of a hedged description —
 *  "log house; infant school 1833-34, use on the scene date unattested" is read as the use
 *  the record leads with, not the later one. */
function normal(value) {
  return String(value ?? '').toLocaleLowerCase().replace(/_/g, ' ').trim();
}

function kindFromTables(text) {
  if (!text) return null;
  for (const [kind, pattern] of FUNCTION_TABLE) if (pattern.test(text)) return kind;
  return null;
}

/**
 * @param {object} sidecar   the compiled record
 * @param {string} [id]      the record id, for the last-resort title
 * @param {{title?: string}} [name]  the display name, if the caller already composed it
 * @returns {string} a KINDS id from taverns…waterfront (never viewpoints/corners/people)
 */
export function placeKind(sidecar, id = '', name = null) {
  const archetype = String(sidecar?.archetype ?? '');
  const fn = normal(sidecar?.attributes?.function?.value);
  let kind = kindFromTables(fn);
  if (kind && FORT_ARCHETYPES.has(archetype) && (kind === 'homes' || kind === 'stores')) kind = 'public';
  if (kind) return kind;
  if (ARCHETYPE_KIND[archetype]) return ARCHETYPE_KIND[archetype];
  const family = String(sidecar?.reconstruction?.family ?? '').charAt(0).toUpperCase();
  if (FAMILY_KIND[family]) return FAMILY_KIND[family];
  const title = normal(name?.title ?? sidecar?.name ?? id);
  return kindFromTables(title) ?? 'homes';
}
