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

## The programme re-derived against the order book

*Appended 2026-09-20 (T-1196). The programme reasoning above is the 2026-08 record and is
left as it was written; the quantitative target table near the top still prints the 665/511
figures of that date, which T-0032, T-0283, T-0881, T-0883 and T-1036 have since moved to
668/510. The live numbers are `1835_building_inventory.json`'s and are gated.*

The 668-roof schedule was calibrated before this project had a population layer. It has one
now — the town model (T-1293), the lodging model (T-1370) and the reconstruction order book
(T-1166) — and the order book carries five `programme_deltas` rows stamped
`owning_ticket: T-1196` so that the comparison would be made deliberately rather than
discovered halfway through a district. `tools/reprogramme_roofs_1835.py` makes it, every
group, every gate run. The full record is
`docs/RESEARCH/1835_roof_programme_rederivation.md`.

**No group moved, and the total stays at 668** — inside the inventory's own defensible range
of 565–765. That is a result rather than an absence of one, because the largest delta on the
book is 308:

- **The order book orders 643 households and the programme schedules 335 ordinary
  dwellings.** Building 308 more roofs to close that would seat one family per roof, which is
  the exact error the town model was written to refuse: *"a roof programme that seats one
  family per roof undercounts the town."* It closes on **occupancy**. The programme's 377
  dwelling roofs (335 ordinary plus the 42 larger houses and boarding houses) hold 643
  households at **1.706 households to a dwelling** — and the November 1835 town census
  brackets that rate at **1.636–2.051**, being 8.204 people to a dwelling over a household
  size of 4.0 to 5.015. The rate the order book needs is inside the band the census implies,
  so the dwelling half of the programme holds the town it is ordered for without a roof being
  added.
- **The census's 398 dwellings.** The programme's 377 stand 5.3% below the count taken in
  November — four months after the scene, in the fastest-growing months the town had. That
  gap is growth across the interval, and it is the same date caution the trade-census
  crosswalk applies to every class it compares.
- **The delta of 10 on institutional and public roofs is a unit mismatch.** The town model's
  high end of 19 is *"9 institutional or public roofs outside the fort and 10 principal roofs
  inside it"*; the programme schedules those ten under `fort_principal`, not under
  `institutional_public`. 9 + 10 = 19. The two files already agree; only the comparison in
  `build_order_book_1835.programme_deltas` reads one group against a figure spanning two.
- **The delta of 0 on boarding houses is circular.** `model_town_1835.build_lodging` takes
  that figure straight off `district_group_matrix`, so it cannot disagree with the programme.
  A figure that cannot fail is not a check on 42 roofs, and it is recorded as a tautology
  rather than banked as corroboration.
- **The delta of 6 on inns and taverns compares roofs with printed notices.** The structure
  layer holds ten standing public houses and the programme schedules ten. The model's 16 is
  the business register's count of *records* at the scene date, of which four name
  Wentworth's house on Flag Creek and three name the Eagle; the trade-census crosswalk folds
  none of them, and folding a notice into a house is an identity ruling. None is made here.
  The delta is owed out to T-1190's convergence of the business layer by id.

The one thing that did move is the family-archetype crosswalk's own count fields, which had
drifted to 662 roofs and nine misplaced priority ranks. See that file's report for the 13
values and the dates they should have followed.
