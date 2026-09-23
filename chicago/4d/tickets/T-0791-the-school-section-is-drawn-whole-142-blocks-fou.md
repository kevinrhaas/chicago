---
id: T-0791
title: The School Section is drawn whole — 142 blocks, four named streets and the rest unnamed, three reserved blocks — and 125 land-sale rows already name its blocks and cannot be put on the ground
state: split
epic: META
requested_by: owner
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T15:33:47.370Z
claimed_run: null
---

**The source, 2026-09-05.** The owner added a second copy of J. S. Wright's manuscript survey of
1834 at `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` — the Historic Urban Plans (Ithaca) reproduction of the
**National Archives original**, 5050 × 6628 px at 600 dpi, with its own caption: *"Two portions are
missing, the larger being near the lower center … the manuscript was mounted on cloth to repair this
tear."* It is a different scan of the same drawing this project already traces as `wright_1834`
(the BPL/Leventhal copy, 4204 × 5166 px, IIIF `commonwealth:js957744g`). The owner's instruction:
*"review this and create tickets to update and enhance the map … several items from this map should
be incorporated including the streets, there are streets documented here that are missing, including
the blocks, where the public square is, where the various sloughs are, things like 'the kinzie block'
… look at all of the streets and block numbers … the lakeshore edge and that whole area … the whole
path of the river going south … note the sections as labeled in the legend."*

## What the sheet shows

South of Madison Street, the legend's yellow tract — **"School Section, 1833"**, section 16 of
T39N R14E, the mile square the state sold in October 1833 to fund the schools — is drawn whole:

- **Named streets, four, at the top of the tract:** Madison · Monroe · Adams · Jackson. **South of
  Jackson the tiers are unnamed** — eight more rows of blocks to the section's south line (12th
  Street), drawn as lines with no lettering.
- **North–south streets** carried down from the Original Town: Des Plaines · Jefferson · Clinton ·
  Canal on the west; Market · Wells · Clark · (La Salle, Dearborn) · State on the east, the last
  the section's east line.
- **Blocks 1–142**, numbered in north–south columns from the north-west corner (1–12 down the west
  edge, 13–24 up the next, and so on), the South Branch cutting **70, 71, 78, 83, 84, 85, 86, 87,
  88** and the river-side blocks drawn with lot lines (71, 72, 80, 81, 83, 84) where the rest are
  whole.
- **Three blocks lettered "Reserved"**, coloured deeper: the section's **north-west corner** at
  Madison and the west line; the **north-east corner, block 119, at Madison and State**; and
  **blocks 87 and 88 on the east bank of the South Branch** — the owner's *"reserved school section
  on the south."* The sheet's larger tear (T-0787) sits on exactly these two.
- **No alleys.** The Original Town's blocks are drawn with the mid-block alley; the School Section's
  are not. The owner's reading of that, 2026-09-05: *"most of those streets on the south are unnamed
  so maybe in that less populated area the streets are not as well worn, there are no alleys and no
  street names but still a grid that should have some wilderness trees, etc."*

## What the project has, and the 125 rows waiting on it

The plat module stops at Madison; the terrain stops at Washington (T-0219 carries it to Madison,
T-0464 beyond). No block south of Madison exists in any file.

And **125 rows of `data/research/land_sales/` already name a block and lot in the School
Section** — *"lot 1 of block 83 of the school section (sec 16 T39N R14E)"* and its neighbours —
each marked *"Read, and not put on the ground. The row names a block — and usually a lot — in the
SCHOOL SECTION."* The October 1833 auction was read (191 rows landed 2026-09-04) and every one of
its placements is waiting for this grid. That is the owner's standing complaint — reading with no
output — with the output already named.

## The ask

1. **The grid, numbered.** Every one of the 142 blocks as a polygon on the committed street lines
   (extend the plat module south with the section's own dimensions, which differ from Thompson's —
   measure the block off the sheet, do not reuse the Original Town's module), each carrying its
   numeral read from the registered scan, tract-keyed. The blocks the South Branch cuts take the
   bank as an edge once T-0794 lands it.
2. **The four named streets into `data/streets/1835.json`**, and the unnamed tiers as streets
   with `name: null` and the sheet cited — a surveyed line the sheet does not name is still a line.
   Give them the `status` the owner's reading implies: platted, unopened, unworn — so the renderer
   can draw a survey line across prairie rather than a road, and the flora zones can put timber and
   wet prairie across the grid instead of clearing it. Name the alley absence in the record.
3. **The three reserved blocks.** Write them into `data/reconstruction/1835_reserved_ground.json`
   with the sheet as source, and **test the reservation against the sale**: if the 1833 auction
   rows never sell a lot in 87, 88, 119 or the north-west corner block, the sale corroborates the
   sheet and the grade rises; if they do, the sheet and the sale disagree and both are written down.
   The owner: *"not sure there is anything you will find there but consider that, there may be
   something of use that comes out of knowing that."*
4. **Then spend the 125 rows.** With the grid numbered, every land-sale row that names a block and
   lot resolves to a polygon — the purchaser's name onto ground, dated to the sale. That is the
   first pass at *who owned the south in 1835*, and it comes free once the blocks exist.
5. Nothing here draws a roof. The section was sold, not built; T-0464/T-0465 own the ground and
   water, and the roof programme owns what stands on it.

**Done when** all 142 blocks exist and are numbered from the sheet, the named and unnamed streets
are in the street file with the unworn status recorded, the three reservations are written and
tested against the sale, and the 125 land-sale rows are on the ground or refused by name.
