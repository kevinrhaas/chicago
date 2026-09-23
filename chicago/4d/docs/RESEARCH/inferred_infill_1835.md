# Recommended anonymous building infill — July 1835

## Status

This is a production reconstruction programme, not a recovered building census. It preserves
every existing structure record and begins filling the large documented gap between the
project's named landmarks and the scale of Chicago in July 1835.

The programme source is the owner-supplied *Chicago · July 1835: Building Inventory and
Architectural Reconstruction Specification* (August 2026), recorded as
`owner_chicago_1835_reconstruction_spec_2026`. It is a modern synthesis at tier 5. It can
support aggregate inventory, type-level dimensions and production rules. It cannot turn an
anonymous individual roof, location, footprint, occupant or appearance into a documented fact.

## Quantitative target

| Constraint | Exact target |
|---|---:|
| Total roofed structures | 665 |
| Principal or functional roofs | 511 |
| Ancillary roofs | 154 |
| South / West / North / Fort | 370 / 135 / 150 / 10 |
| One storey or one storey plus storage loft | 500 |
| One-and-a-half storeys | 73 |
| Two storeys | 92 |
| Three or more storeys | 0 |

The defensible total range stated by the specification is 565–765, chiefly depending on the
treatment of very small and temporary structures. The exact value 665 is a production decision,
not a claim that a period enumerator counted 665 roofs.

The family schedule contains 35 codes and independently sums to 665. The district/group matrix
also sums to 665. `data/reconstruction/1835_building_inventory.json` stores both calculations so
the check gate can detect drift.

## Preservation and substitution rule

Existing records are protected. They include named buildings, bridges, stockade components,
yards and in some cases multi-roof compounds, so the number of structure records is not the
number of physical roofs. A dedicated reconciliation must map every existing record to zero,
one or several target roofs before the final inventory is filled.

When later evidence identifies an anonymous slot, the better-evidenced building substitutes for
that slot. It is not added on top of the 665 total. No existing named record is deleted merely to
make an aggregate count work.

## Phase 1: South Division mixed blocks

The first parcel adds 48 anonymous roofs—40 principal/functional and eight ancillary—to five
platted blocks between Franklin and State, south of Lake and north of Randolph. It deliberately
leaves alternating open lots. This is density zone B, not a continuous attached street wall.

| Families | Count | Role |
|---|---:|---|
| D1–D7 | 26 | cabins and ordinary frame dwellings |
| C1–C3 | 8 | shops and store-residences |
| W1–W4 | 4 | artisan workshops |
| F1–F2 | 2 | freight and storage |
| A1–A5 | 8 | stables, barn, privies and utility sheds |

Exact positions, yaw, footprints and individual existence are conjectural. Type-level form is
inferred within the source's family bands. Stable hashes select size, finish, age and condition,
so rebuilding produces byte-identical records and GLBs rather than a new town on each run.

## Geometry state

The first release uses intentionally simple review massing generated directly from each record
by `generators/inferred_placeholder.py`. Every GLB declares itself a placeholder, every popup
labels the structure “Recommended reconstruction,” and the confidence view treats its massing as
conjectural. These shapes make density, spacing, skyline and terrain contact reviewable now; they
are not the final 4k–12k-triangle family assets specified for ordinary principal roofs.

The current reusable archetypes compress several future families. In particular, D5/D6
gable-front extremes are constrained to the present eaves-front dwelling generator and C2's
one-and-a-half-storey store-residence is represented as one storey plus loft. This compression is
recorded in Liberty L81 and must disappear as the 35-family library is implemented.

## Next evidence and implementation passes

1. Reconcile the 76 pre-existing scene records to physical roof units.
2. Verify north and west occupied extents separately from the larger speculative plat before
   extending terrain or placing roofs there.
3. Build family archetypes and anti-cloning variants, then replace flagged massings.
4. Populate district parcels to reconciled targets while preserving at least 45% sparse/open
   platted land.
5. Add terrain-sampled foundations, rear yards and use-specific props without creating a hidden
   collision floor.

## Phase 2: North Division initial parcel

Sixty additional anonymous slots—45 principal or functional roofs and 15 ancillary roofs—are
now generated from `1835_north_division_initial_parcel.json`. Every footprint is checked against
the committed walking heightfield for coverage, dry land, collision and no more than 0.35 m of
perimeter relief. Slot 41 moved 7.1 m within its declared 25 m control radius because the authored
centre crossed 1.43 m of ridge relief. H2, H3 and I2 remain visibly flagged generic block massings
until their canonical boarding-house and institutional archetypes exist. The other 90 North
Division target roofs remain gated behind a single coordinated extension to local N +760 m.

## What could settle individual roofs

Parcel-specific evidence would require contemporary tax or assessment lists, deeds with
improvements, construction notices, account books, insurance records, surveyed building plans,
or sufficiently close contemporary views. A later retrospective map may orient research but
cannot by itself upgrade an anonymous roof to documented.
