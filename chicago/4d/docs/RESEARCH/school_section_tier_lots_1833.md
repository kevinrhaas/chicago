# The School Section's first tier, cut into the lots the 1833 sale witnesses

**T-1477, 2026-09-20.** Piece 1 of 2 of T-1456, itself piece 3 of 3 of T-1438. The
deliverable is `data/traces/vectors/school_section_tier_lots.json` — thirteen blocks
between Madison and Monroe, eighty lots, 37.4 acres of platted ground — written by
`tools/cut_school_section_tier.py`, which re-derives it in under a second and whose
`--check` refuses a committed file that no longer matches its own derivation.

## The tier, and why this one

Section 16 is a mile square and Wright draws all of it: T-0797 read the whole grid and
committed 142 numbered blocks (`school_section_blocks_1834.json`). It stopped at blocks.

The **tier** cut here is the northernmost row of that grid, between **Madison** and
**Monroe**. Madison is the Town of Chicago's own south line, so this row is the ground a
visitor standing at the south edge of the town looks straight across. It is the only tier
of the section a 1835 scene reaches, which is why it is cut first and cut alone; the other
eleven remain drawn as blocks and undivided.

## Where the lot count comes from, and why it is not a module

Wright rules the section into blocks and letters their numbers. **He does not rule a
single lot line inside one.** So the division cannot be read off the sheet, and a project
that cut it on a module would be inventing the number of lots in every block.

It does not have to. The state sold the school section lot by lot in **October 1833**, and
this project already holds the seller's own register — `data/research/land_sales/
entries.json`, the Illinois State Archives' tract register, 337 rows of `type_of_sale`
`SC` in section 16 of T39N R14E. Those rows print the plat's language:

    LOT3BL71    lot 3 in block 71
    BL106       block 106, sold whole

So the register **says how many pieces each block was cut into**, block by block, in a
record made by the seller at the moment of sale. That is a `documented` count, and it is
the one thing this cut needs that the sheet cannot give.

| the tier, west to east | what the register witnesses |
|---|---|
| block 1 | nothing — the sheet letters *Reserved* |
| blocks 24, 25, 48, 49 | lots 1–8 |
| blocks 72, 80 | lots 1–4, and never a fifth |
| blocks 81, 94, 95, 118, 119 | lots 1–8 |
| block 142 | nothing — the sheet letters *Reserved* |

The counts are read at run time, never typed, and a block whose witnessed numbers are not
a contiguous run from 1 is **refused** rather than filled in: a block the register names
lots 1, 2 and 4 in has told us three lots sold, not that it holds four. No block of this
tier is in that position; the refusal is there so that a re-reading of the register which
put one there would stop the build instead of being absorbed.

### Two records agreeing, neither consulted about the other

The blocks the sale never names are **exactly** the blocks the sheet letters *Reserved* —
1 and 142, the tier's two corners. A draughtsman in 1834 and a land agent in 1833 made
those two records independently, and the gate asserts the agreement rather than printing
it.

### The four-lot blocks are the river's

Blocks **72 and 80** are the two of this tier nearest the **South Branch**, and they are
the two the register cuts into four rather than eight. A third record, sharing no
arithmetic with the register, agrees about which ground that is: the committed heightfield
puts **187 of block 80's 396 lattice samples below datum**, and finds no other block on the
tier with a single wet sample. A larger parcel on the water and a town lot inland is what
the sale sold. Why the seller did it is not recorded here — only that two records say the
same thing about the same two blocks.

## What is adopted, and at what grade

| | grade | why |
|---|---|---|
| block boundary | `inferred` | the committed grid's own, quoted vertex for vertex — this module cuts no ground and re-reads no raster |
| lot count | `documented` | the October 1833 register, a source record, witnessing a count |
| lot lines | `inferred` | the Original Town's module — an 18 ft alley centred in the block, lots fronting the east–west streets — carried half a mile and five years because it is the town's own practice and the only one this project holds |
| lot numbers | `conjectural` | **nothing** places a School Section lot number on the ground; the register prints numbers and no positions |

The numbering run adopted is the one Original Town block whose lot numerals *are* read —
block 18, north row 4 3 2 and south row 5 6 7 (`clark_reach_bulge_1834.md` § 8) — so the
north row runs 4-3-2-1 west to east and the south row 5-6-7-8. That is a convention carried
from another plat onto this one, and it is a grade **lower** than the North Division tier's
lot numbers, where the sheet letters 4 on a known lot in every block read.

The tier is drawn **level**, because the committed block grid draws it level and T-0959's
re-measurement is why that stands: `school_section_tier_skew_1834.json` re-took all
thirteen east–west rules keeping the bands, and found Section 16's own PLSS boundaries —
lines that run true east–west on the ground by definition — tilting with the interior ones.
A tilt the cardinal control carries belongs to the registered frame, not to Wright's survey,
so it is not put into the lots.

## The register's acreage column, refused

118 rows of the sale buy a whole block and print an acreage, which looks like a free
independent measurement of every block in the section. It is not one. Against the 74 blocks
that carry an acreage and are drawn on this grid, the register runs **20 % large at the
median** and scatters from **0.72× to 3.26×** — nine of the seventy-four inside 5 %.

A column with that spread cannot tell a good block from a bad one. So the cut takes the
register's **count** and not its acreage, `--self-test` asserts that the column does *not*
measure this grid, and the figures are kept in the committed file's `acreage` section so
that the next person does not have to re-take the measurement to find the same thing out.

## What this does not say

Nothing about who built here. The school section in 1835 was ground that had been sold, and
mostly empty ground at that. This file says where the lots were — it seats no structure,
puts no purchaser on a lot (the register's buyers are the resident rulings' question), and
re-grades no street.

A School Section lot is also **not a town lot**: eight to a block of two and a half acres
makes every one of the eighty between a third and three quarters of an acre — 75 to 147 ft
of frontage on a uniform 175.4 ft of depth. That figure is the reason the tier is worth
cutting rather than assuming.

One limit of the ground reading, stated rather than left to be found: block 1, the reserved
block at the tier's west corner, has 220 of its 440 lattice samples **off the modelled
terrain field**, which does not reach that far west. Its `ground` block says so. The block
carries no lots, so nothing in this cut rests on it.
