---
id: T-0789
title: Kinzie's Addition is on the sheet whole — 54 numbered blocks, 13 named streets, the Kinzie Block and the river-front water lots — and the North Division carries four streets
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T08:21:08.631Z
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

Kinzie's Addition (legend: *surveyed 1833*, green) is drawn complete east of the Original Town's
north division and north of the river:

- **East–west streets, south → north:** Michigan · Illinois · Indiana · Ohio · Ontario · Erie ·
  Huron · Superior.
- **North–south streets, west → east:** Wolcott · Cass · Rush · Pine · Sand — the last two
  running out along the lake shore.
- **Blocks 1–54**, numbered in tiers from the river northward (1–7 on the river tier, 8–13, 14–19,
  20–26, 27–31 · 32–36 · 37–43 · 44–48 · 49–54), the lake-shore blocks (20, 31, 32, 43, 44, 45, 54)
  cut by the shore.
- **"Kinzie Block"** — Wright letters it across **block 11**, between Illinois and Michigan, Cass to
  Rush, as a name and not a number. That is the only block on the whole sheet given a name apart
  from the Public Square.
- **The river-front water lots** — a strip of narrow numbered lots (1 to about 35) along the north
  bank from the Original Town's line east past the fort bend to the pier, drawn as lots and not as a
  street.

## What the project has

`data/streets/1835.json` carries four streets north of the river: `kinzie`, `north_water`,
`wolcott`, `michigan_north`. **Nothing of Cass, Rush, Pine, Sand, Illinois, Indiana, Ohio, Ontario,
Erie, Huron or Superior.** The North Division parcel (`1835_north_division_initial_parcel.json`)
places roofs against a grid it does not have. T-0451 already says *"only one north-south street
stands north of the river"* for the Original Town's north division; this is the same fault one
tract east, and a bigger one, because the Addition is the larger platted ground.

The newspapers already name the tract: the gazetteer carries *Kinzie's Addition* as a place, and
the Democrat's 1834–35 land notices sell lots in it by block and lot number — none of which can be
placed.

## The ask

1. **The thirteen streets into `data/streets/1835.json`**, source `wright_1834` (and the new scan,
   T-0787), with the corridor width Wright's drafting gives them — the Addition's streets are
   narrower than the Original Town's 80 ft; measure, do not assume — and the extents the sheet
   draws: Pine and Sand end on the shore, Superior is the last tier.
2. **Blocks 1–54 numbered**, in a numbering file of the same shape as the Thompson one but for this
   tract (`data/traces/kinzie_addition_block_numbering.json` or a tract-keyed extension of the
   existing file), every numeral read with its crop cited.
3. **The Kinzie Block, named.** Block 11 carries the name on the sheet; write it as the block's
   name with the reading cited, and search the newspaper corpus and the directories for the phrase —
   a named block in 1834 is a block the town talked about.
4. **The water lots as a layer.** The numbered river-front strip is neither a street nor a block
   under the plat module; it is the tract's wharfage. Record it as a lot strip with its numerals,
   feeding `data/wharves/` and `data/frontage/river_walk_frontage.json` rather than the block grid.
5. Do not draw a lot line inside a block the sheet does not subdivide — Wright subdivides the river
   tier and 14–19; the northern blocks are whole.

**Done when** the North Division's street file carries Kinzie's Addition entire, the 54 blocks are
numbered from the sheet, the Kinzie Block is named, the water lots are a recorded strip, and a
Democrat notice selling "lot N, block M, Kinzie's Addition" can be placed.
