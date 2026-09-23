# The lot-and-block address

*Policy. Written for T-0423, 2026-09-03. The tool is `tools/lot_addresses.py`, the ledger
is `data/research/newspapers/lot_addresses.json`, the liberty is **L216**, and the gate is
two steps in `tools/check.sh`.*

## The three ways a newspaper places a building, and this is the third

A Chicago paper of 1834 places a building in one of three grammars, and this project now
answers each of them differently because they are not the same claim.

| the paper says | what it constrains | the policy |
|---|---|---|
| a platted street and nothing narrower | a **face** | `docs/STREET-FACE-ADOPTION.md`, L212 |
| a count of doors off a named corner | a **position along a face**, and no lot | `docs/CORNER-ORDINAL.md`, L215 |
| a lot and a block | the **plat's own unit** | this document, L216 |

The third is the strongest statement the corpus makes and it is also the rarest: there is
**one** of it. G. Spring's For-Sale notice ran in the *Chicago Democrat* six times between
1834-06-18 and 1834-11-19 —

> For Sale, **LOT No. 7, in block No. 16, one lot east of Haddock's Tavern, on Lake
> street**, in the town of Chicago. There is on said lot a large **Dwelling-House and fine
> well**.

— and four of those printings carry the words legibly. T-0358 committed the Thompson
plat's block numbering so that this sentence could resolve to ground. It resolved to a
**polygon** and stopped there: the roof standing on that polygon went on carding as *"A
vacant one-room frame cottage"*, which is a claim about absence made over the top of a
source saying a house was there. This policy is the other half of T-0358.

## Authored, derived, and where the line falls

The **address** is authored. `data/research/newspapers/lot_addresses.json` carries the
printed words, the printings they are read from, what the notice says stood on the lot, and
who the advertiser was. It names no structure and no coordinate.

Everything from there is **derived**, by `tools/lot_addresses.py`:

1. **block number → block.** Through `data/traces/thompson_block_numbering.json`. The
   ledger states the block it believes it resolves to and the tool refuses a ledger that
   disagrees with the committed numbering — a stale copy of a reading that moved is not a
   second opinion.
2. **lot number → polygon.** Through `data/traces/vectors/thompson_lots.json`, whose lots
   carry `plat_lot_number` from that same committed numbering.
3. **polygon → roof.** The roof whose footprint **centroid** falls inside the lot.
   **Exactly one, or the address is refused.** An address landing on two roofs has placed
   neither; one landing on none has nothing to name. (Centroid, not the record's position:
   a record's origin is a corner of its own footprint frame, and on a 26 m lot the
   difference between a corner and a centre answers the question wrong at a lot line.)

## The grade does not rise, and the chain is why

The words are **read**. The block number is **`inferred`** — three blocks counted east of
the single numeral the Wright sheet shows. The lot number is **`conjectural`** twice over:
four lots to a block face is a reading of one block, the lot lines it numbers are the plat
module's and are drawn from no sheet, and the counter-clockwise scheme itself was read off
block 18.

A chain is as strong as its weakest link, so **the seating is graded at the bottom tier** —
exactly where the roof already stood. `confidence` is `const: "reconstructed"` in the
schema, the tool refuses any other value, and `--check` re-reads the structure's own phase
and fails if a documented address has quietly promoted a reconstructed roof.

## What a seating writes, and what it may not

It writes **one block** — `lot_address` on the structure record — and nothing else. It
touches no coordinate, no footprint, no form value, and **not even the record's
`function`**. That last restraint is not fussiness: `function.value` is what the dooryard,
fence, planting and signboard generators read to decide what stands in a yard, so a
documented address rewriting it would have moved fabric all over the lot in order to say a
name.

Four refusals, each an assertion in `--self-test` rather than a promise:

- **It may not move, resize or re-form the roof.** No coordinate, no polygon and no form
  value is authored, adjusted or nudged by an address. It may re-deal the count-unit's
  FAMILY, and only that, and only under the rule below — which is a different act: the
  family is dealt by the schedule and the band it carries is sampled by
  `tools/family_bands.py`, so the roof is still a count-unit drawn from a band and not a
  building somebody sized. (Until 2026-09-04 this refusal was absolute, and the ledger read
  "the house the notice calls LARGE is not made large". T-0593 ruled the other way; **L222**
  is the ruling and the paragraph below is the rule.)
- **It may not promote the roof.**
- **It may not seat a person.** The advertiser is the man to apply to for terms and nothing
  else, and the ledger's `is_the_occupant` and `is_the_owner` are `false` and refused if
  they are not. This house is *not* "G. Spring's": the same G. Spring is the attorney the
  papers put second door west of Franklin and South Water, and T-0412 is the same trap read
  from the other side — a building offered FOR SALE must not mint a placement on its vendor.
- **It may not seat two addresses on one roof, or one address on two roofs.**

## When the notice describes the building

A placement notice often says more than where. Spring's says **"a large Dwelling-House"**, and
for a year this policy spent the address and let the adjective fall on the floor: the roof the
address landed on was a 5.36 × 6.38 m one-room cottage, the smallest dwelling family the
665-roof programme deals, and the card printed the source's own word LARGE over it. That is a
documented statement about a building on the lot contradicted by an invented one standing on
it, and between a source and an invention the source wins. **T-0593 ruled it, L222 records it,
and this is the rule the next lot-and-block address inherits.**

**A documented address MAY re-deal the family of the count-unit it seats on, and may do nothing
else.** Five clauses, and an address that cannot satisfy all five does not re-deal:

1. **The source must describe the building, not the lot.** A size, a kind or a construction
   stated of the thing standing there — "a large Dwelling-House", "a two-story frame store".
   A price, a vendor, a neighbour or a street is about the parcel and reaches nothing.
2. **The band must actually contradict the word.** If the count-unit already answers the
   description, there is nothing to repair and nothing is touched.
3. **The lowest rung that answers the word, and not one above it.** The families are ranked by
   `data/reconstruction/1835_family_archetype_crosswalk.json`'s own labels, and the label is
   the test: D6 and below are *cottages*, D7 is a *Small* two-storey house, H1 is the first the
   crosswalk calls **larger** and calls a **house**. "Large" reaches H1 and stops there. An
   adjective is not evidence of storeys, paint, trade or wealth, and reading the best house a
   word will bear out of one word is the failure this clause exists to refuse.
4. **The district's remainder pays for it, so no total moves.** The family mix is an
   apportionment of a district's remainder and not a claim about any block, so the new family
   comes out of that remainder and the displaced one goes back into it. The block's roof
   count, its principal/ancillary split, its headroom and its open lot are all unchanged.
   `tools/reconcile_665.py` re-derives the result and `tools/check.sh` runs it. If the
   district's remainder holds none of the family the word reaches, the re-deal is refused and
   said so — growing the town's total to buy a roof the programme does not own is not
   available to an address.
5. **The grade does not move and nothing else about the record does.** `confidence` stays
   `reconstructed`, the position keeps its setback and offset, the household keeps its house,
   the advertiser is still not seated, and the record's `function` follows the family the
   schedule dealt rather than anything the notice says the building was for.

**Two mechanical consequences worth stating, because they cost a run to discover.** The record
id carries the family (`..._d3_03` becomes `..._h1_03`), so a re-deal RENAMES the structure:
every derived layer regenerates, and any append-only liberty whose `Covers:` names the old id
takes an appended paragraph and a re-pointed token, never a rewritten ruling. And the mesh is
stale the moment the band changes — `tools/validate.py --stale` hard-fails until
`tools/bake.sh --only <new id>` has run in the same commit.


## What it does not draw

The notice's second structure is **a fine well**, documented as plainly as the house. It is
not drawn, and the record says why: the town has no well — no archetype, no committed
structure, no yard record — so drawing this one would raise a new kind of object for the
whole scene rather than place a known one, and it would be the only well in Chicago. That
is filed as its own ticket. **A documented feature that is absent is stated, not omitted.**

## What a visitor sees

`tools/compile_scene.py` carries the address into the sidecar as an attribute row, so it
renders with the same confidence chip, sources and reasoning as every other thing the card
says, and `renderers/web/js/display-name.js` titles the building from it. A documented
address outranks a composed vacancy and ranks below a household — a house the town knew by
the family in it is known by the family in it. The production identity is not deleted:
`Reconstructed D3 one-room frame cottage #03` still prints under the title as the reference
line, and search takes both.
