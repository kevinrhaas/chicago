/**
 * attribute-tiers.js — which tier one ATTRIBUTE stands on, in the card's words.
 *
 * T-1158, and the owner's ask in his own: *"note for each attribute of each person
 * what is attested, inferred or reconstructed and reasons why."*
 *
 * The layer has always put a `confidence` on an attribute, and the card has always
 * printed a swatch for it. What the card could not do was tell two very different
 * things apart, because `confidence: "reconstructed"` was doing both jobs:
 *
 *   - 7,314 blocks carry it over a value that asserts NOTHING — `value: null` with
 *     a note reading "Not attested.", or the occupation sentinel `none_recorded`.
 *   - 40 blocks carry it over a value somebody actually supplied — a conjectured
 *     arrival year, an address carried back from an 1843 directory.
 *
 * Under one word the card showed both with the hatched `reconstructed` chip, so an
 * unknown arrival read as an invention and an invention read as an unknown. The
 * first is the more common and the more misleading: most of this town's attributes
 * are simply not recorded, and a chip that says "we made this up" over "not
 * recorded" overstates how much of the town was made up.
 *
 * So there are four tiers on an attribute, and `unknown` is the new one. It is not a
 * weaker claim than `reconstructed`; it is the absence of a claim, and it gets a
 * chip of its own that says so.
 *
 * `tools/migrate_attribute_tiers.py` writes `tier` into every card and
 * `tools/check.sh` refuses a card whose tier has drifted from its own confidence, so
 * the tier this file reads is a committed value rather than a second derivation that
 * could come apart from the gate's. `tierOf` falls back to the derivation anyway,
 * for a record the migration has not reached — a card that renders as `unknown`
 * because nobody lifted it yet is better than one that renders as nothing.
 */

/** Best evidenced first. `unknown` last: the absence of a claim, not a weak one. */
export const TIERS = ['attested', 'inferred', 'reconstructed', 'unknown'];

/** Values that assert nothing. `none_recorded` is the occupation layer's sentinel. */
const NOT_ASSERTED = new Set([null, undefined, '', 'none_recorded']);

/** The word beside the value, and what it promises a reader. */
export const TIER_LABEL = {
  attested: 'attested',
  inferred: 'inferred',
  reconstructed: 'reconstructed',
  unknown: 'not recorded',
};

export const TIER_TITLE = {
  attested: 'A source says this. The citation is below.',
  inferred: 'Reasoned from evidence about this person. The reasoning is below.',
  reconstructed: 'Supplied by this project, not by a source. What it rests on, and what '
    + 'would replace it, are below.',
  unknown: 'Nothing is asserted. No source in this project records it, and nothing has '
    + 'been invented to fill the gap.',
};

/**
 * The tier of one claim block — the committed value where the card carries one, the
 * derivation from `confidence` and the value where it does not.
 *
 * Returns null for anything that is not a claim block, so a caller can keep its old
 * rendering for a record shape that never had a confidence in the first place.
 */
export function tierOf(block) {
  if (!block || typeof block !== 'object') return null;
  if (TIERS.includes(block.tier)) return block.tier;
  const conf = block.confidence;
  if (conf === 'reconstructed') {
    return NOT_ASSERTED.has(block.value) ? 'unknown' : 'reconstructed';
  }
  if (conf === 'attested' || conf === 'inferred') return conf;
  return null;
}

/** True when the block asserts no value at all, whatever its confidence says. */
export function isNotAsserted(block) {
  return !!block && typeof block === 'object' && NOT_ASSERTED.has(block.value);
}
