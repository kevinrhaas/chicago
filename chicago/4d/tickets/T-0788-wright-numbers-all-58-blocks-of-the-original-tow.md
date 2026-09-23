---
id: T-0788
title: Wright numbers all 58 blocks of the Original Town and this project has read six: read the rest — the Public Square is block 39 — so a lot-and-block address can finally land
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-07
pr: 955
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T09:49:55.216Z
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

## What the sheet shows, and what the project has

Wright writes a numeral on **every block of the Original Town**, on all three sides of the river.
Read on the 600 dpi crops made for this review (all counts to be re-read on the registered scan,
T-0787):

| tier | blocks, west → east |
|---|---|
| north of the river, Kinzie St to the bank | 7 · 6 · 5 · 4 · 3 · 2 · 1, and 14 · 15 on the North Branch's west bank |
| West Division, Kinzie → Madison | 10 9 8 · 11 12 13 · 25 24 23 22 · 26 27 28 29 · 47 46 45 44 · 48 49 50 51 |
| South Water → Lake | 21 20 19 18 17 16 |
| Lake → Randolph | 31 32 33 34 35 36 |
| Randolph → Washington | 43 42 41 40 · **39 = "Public Square"** · 38 37 |
| Washington → Madison | 52 53 54 55 56 57 58 |

The numbering snakes — it reverses direction tier by tier — which is exactly the kind of thing
that cannot be *counted* from two numerals and has to be *read*.

**The project has read six.** `data/traces/thompson_block_numbering.json` numbers the South Water
tier from two numerals on the BPL scan and refuses five more; `data/traces/vectors/thompson_lots.json`
says in its own header *"every other block in this file is unnumbered on purpose."* That was the
right refusal on a scan where the numerals could not be read. It is no longer the situation.

## Why it pays — the address that resolved to nothing

The numbering file exists because of one notice: G. Spring, *"LOT No. 7, in block No. 16, one lot
east of Haddock's Tavern, on Lake street"* — *"the most precise placement statement in the whole
newspaper corpus"*, and it resolved to nothing (T-0324, T-0358). `data/research/newspapers/
lot_addresses.json` still holds it, unresolved. The 1843/1844 directories, the land sales and the
old-settler recollections all speak in **block and lot**; without the numbers on the grid, every one
of those is a reading that cannot land.

## The ask

1. **Read every Original Town numeral off the registered scan** into
   `thompson_block_numbering.json`, `numeral_on_sheet: true`, with the crop region cited per block.
   Where a numeral is torn, stained or ambiguous (the West Division's 8/9/10 row is faint), say so
   and grade it down — never count across a gap that a neighbour's numeral could have bridged.
2. **Stamp them onto the grid.** `tools/generate_plat_lots.py` already stamps `plat_block_number`
   from the file; the 19 generated blocks and the 5 omitted ones all take a number. The West
   Division blocks the generator does not yet emit (T-0689 — lot dimensions unread) take a number
   in the numbering file regardless, so the number is waiting when the block arrives.
3. **The Public Square is block 39.** Write it onto `data/reconstruction/1835_reserved_ground.json`,
   whose own note already quotes the Wright GCPs for the square's corners.
4. **Verify the lot scheme on more than block 18.** The counter-clockwise-from-NE rule was read on
   one block; Wright prints lot numerals on several (16, 17, 18, 20 on the South Water tier; 1–7
   north of the river; the West Division's 27 carries 1–10). Confirm or correct the scheme, and
   note that some blocks carry ten lots, not eight — which the module does not know.
5. **Then land G. Spring.** Lot 7, block 16, on Lake Street, one lot east of Haddock's tavern — the
   first address the corpus ever gave, placed as the proof that the numbers work.

**Done when** every Original Town block the sheet numbers carries that number with its crop cited,
the square carries 39, the lot scheme is confirmed on three or more blocks, and G. Spring's lot is
on the ground or the refusal says which numeral stopped it.
