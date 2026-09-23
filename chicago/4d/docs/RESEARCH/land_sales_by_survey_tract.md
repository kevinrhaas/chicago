# The register's parcels, sorted onto Wright's survey tracts

*T-1104 (piece 1 of T-1102, itself piece 2 of T-1097 and of T-0792). Record:
`data/reconstruction/1835_land_sales_by_tract.json`. Tool:
`tools/sort_land_sales_onto_tracts.py`. Gate: `tools/check.sh`, two steps.*

Two files stood beside each other for a month without touching. T-0609 put the public
domain land tract sales on the ground — 346 of the register's 1,572 rows carry a ring in
`data/research/land_sales/ground.json`. T-1101 put seven of the nine chips of Wright's
1834 legend on the ground — the surveys, with dates and grades, in
`data/reconstruction/1835_survey_tracts.json`. One says who bought; the other says who
surveyed. Nothing asked either about the other.

This is the join, and the tract layer had already written down what it wanted from it.
`canal_section_9_remainder`'s owner refusal reads:

> The same seven 1830 canal entries cover section 9 as a whole; which of them fall
> outside the Original Town is T-1102's question, because it needs every entry sorted
> onto a polygon.

## The answer to that question

**All seven fall outside the Original Town, and the reason is that they are all in the
wrong half of the section.** Every one of the seven 1830 canal entries is an entry in the
NORTH half of section 9 — `W2NE`, `E2NE`, `E2NW` (twice), `W2NW`, and the two `VO` peers —
and the Original Town is cut out of the section's SOUTH-EAST corner. The clipped overlap
of each of the seven with the `canal_commissioners_1830` polygon is zero, to the square
metre.

| record | description | purchaser | date | tract | share |
|---|---|---|---|---|---|
| ls0050 | `W2NE` | Thomas Hartsell | 1830-09-29 | canal_section_9_remainder | 100.0% |
| ls0051 | `W2NEVO` | Thomas Hartzell | 1830-09-29 | canal_section_9_remainder | 100.0% |
| ls0052 | `E2NWVO` | James Kinzie | 1830-09-29 | canal_section_9_remainder | 100.0% *(12.2% also Wabansia)* |
| ls0053 | `E2NW` | James Kinzie | 1830-09-28 | canal_section_9_remainder | 100.0% *(12.2% also Wabansia)* |
| ls0054 | `W2NW` | Edmond Roberts | 1830-10-05 | **wabansia** | 81.1% *(the remainder covers it too)* |
| ls0055 | `E2NEVO` | Alexander Wolcott | 1830-09-29 | canal_section_9_remainder | 100.0% *(4.0% also Kinzie's Addition)* |
| ls0056 | `E2NE` | Alexander Wolcott | 1830-09-29 | canal_section_9_remainder | 100.0% *(4.0% also Kinzie's Addition)* |

## The finding the sort had to have a rule for: the layer does not tile

T-1101 never claimed the nine polygons partition the ground, and they do not. Four pairs
of them cover ground the same committed parcel stands on:

| pair | parcels touching both | largest share one parcel gives to both |
|---|---|---|
| `canal_section_9_remainder` ∩ `wabansia` | 3 | 81.1% |
| `canal_section_9_remainder` ∩ `kinzies_addition` | 2 | 4.0% |
| `fractional_section_15` ∩ `school_section` | 8 | 5.7% |
| `kinzies_addition` ∩ `us_military_reservation` | 1 | 0.1% |

Only the first is a whole tract sitting inside another: `canal_section_9_remainder` is
section 9 with the Original Town cut out and **nothing else** cut out, so Wabansia's
committed seating is inside it. The other three are boundary strips of 0.1% to 5.7%,
where two committed constructions — a street envelope, a block trace, a section line
carried a mile from one corner — disagree by a few metres. None of them is large enough
to move either file on.

So the sort states a precedence clause and applies it in one place:

> A parcel takes the tract that covers the most of it, EXCEPT that a **residual** tract —
> one whose ring is defined as what another tract leaves over — yields any parcel a
> non-residual tract covers at least half of.

`canal_section_9_remainder` is the layer's only residual, by its own `boundary_from`.
The clause fires once (Edmond Roberts's `W2NW`, 81.1% on Wabansia) and is withheld four
times (12.2%, 12.2%, 4.0%, 4.0% — all under half, all left on the residual with the
overlap recorded). Both behaviours are gated, so a later edit that quietly changed the
threshold would go red rather than read plausibly.

## Two rows that need saying out loud

**`ls0057` is a tautology and is reported as one.** John Baptist Beaubien's `SWFR` of
section 10, entered 1835-05-28, sorts onto `us_military_reservation` at 100.0% — and that
share proves nothing. The ring `ground.json` carries for the south-west fraction of
section 10 *is* the committed reservation ring, to the two decimals it is rounded at, and
so is the tract layer's reservation polygon. The clip is a ring against itself. It is
worth exactly one thing — the two files still carry the same ring — and is recorded as
that. The tract layer's refusal to name Beaubien the reservation's owner is untouched:
sorting a parcel onto a polygon says where the ground is, not who held it.

**Eight rows put a school-section block across the 15/16 section line.** Blocks 131 and
133–137 spill 0.3% to 5.7% into `fractional_section_15`. Both sides are committed —
`data/traces/vectors/school_section_blocks_1834.json` on one, the PLSS grid carried from
G1 (L219) on the other — and a grid carried a mile from a single corner is entitled to
that much. Recorded, not corrected.

## What is refused, and why the obvious way round the biggest refusal does not work

| refusal | rows |
|---|---|
| town-plat lots (a town code, no section) | 616 |
| outside the modelled ground | 607 |
| description not read | 3 |
| **sorted onto a tract** | **346** |

The 616 town-plat lots are the largest thing this file could have done and did not.
They carry `CHIOT`, `CHIOTV`, `CHIV`, `CHI`, `CHIOTVO` and no section at all — a code that
names a PLAT, which is exactly what a survey tract is. T-0830's standing rule refuses to
expand them: the Archives' key for the abbreviations is not reachable from this runner,
and guessing which addition `CHIV` names would put a house in the wrong half of the town.

What this work adds is the number that closes the obvious way round that rule. The
tempting argument is that the Original Town was platted in 58 blocks, so a town code
running to block 58 must be naming it. **It is not diagnostic.** The school section's own
rows — separately described by section, carrying no town code whatsoever — reach block 58
as well. A block number in the fifties distinguishes nothing, and the refusal stands
where T-0830 left it.

The 607 refused for being off the modelled ground are refused for ground, not for
reading: **not one of them names T39N R14E section 9, 10, 15 or 16**, the four sections
the PLSS grid is carried across and the only ground any tract polygon stands on. That is
measured in the record and gated, because it is what makes the refusal a statement about
the layer's extent rather than a hole inside it. The only rows a *reading* could still
bring onto a tract are the three whose description went unread: `ADDFRSEC` in sections 10
and 15, and `06126` in section 16.

## What this does not do

The parent ticket asked for two things and this was one of them. The other half — the
generators reading the tract layer — was split off as T-1105 and is **done**, in
[`generators_reading_the_tract_layer.md`](generators_reading_the_tract_layer.md). The plat
module now clips every block against the layer and stamps the tract, the share and the
module on it; the answer is that all nineteen blocks stand in `canal_commissioners_1830`
and the layer cannot discriminate this grid at all. What varies inside that one tract is
the DIVISION, and the West Division's own printed module is refused on arithmetic — two
180-ft lot columns need 360 ft of face and the committed blocks give 315.2 and 326.1 —
with the shortfall traced back to this project's West Division street spacing (T-0445) and
not to the module. `1835_reserved_ground.json` now cites the reservation polygon under
`federal_reserved_ground`.
