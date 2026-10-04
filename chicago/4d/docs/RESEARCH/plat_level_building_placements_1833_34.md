# The 23 plat-level building placements of 1833–34, carried forward or refused

**T-1624.** T-1599 read the 88 `building` claims printed in the Chicago Democrat in 1833 and
1834 and closed 65 of them. It handed on 23 — the ones that do what almost nothing else in the
corpus does, and give a LOT AND A BLOCK NUMBER, a named corner, or an offset from a building the
committed town already holds — because each needed three decisions a ruling register has no
business making:

1. which lot of which block on the committed plat;
2. whether the 1834 building is one the 1835 town already carries under another name;
3. whether the corpus carries it forward the twelve to twenty months to 1835-07-01 at all.

All three are made here, with `data/traces/thompson_block_numbering.json`,
`data/reconstruction/1835_lot_ledger.json` and `data/structures/` in front of them. **Nothing in
this pass places a building, moves a structure, invents a coordinate or raises a confidence.**
Seven readings now seat onto a named committed lot cell and that is the gain; every one of the 23
refuses the forward carry, and that is the finding.

## The instrument, and why it only works in three tiers

`thompson_block_numbering.json` carries Wright's block numeral for all fifty-eight Original Town
blocks. Only **twenty-one** of them are stamped onto a committed block id, because
`tools/generate_plat_lots.py` emits the three South Division tiers and nothing else; the North
Division's Kinzie-to-the-river tier, the West Division's eighteen and the Washington–Madison seven
are held in that file's `blocks_not_in_the_grid` for exactly that reason — there is no id to stamp
them onto.

The lot numbers come from the same file's `lot_numbering` scheme — **4 3 2 1 across the north row
west to east, 5 6 7 8 across the south row west to east** — read on four blocks and graded
`conjectural`, because the lines it numbers are the Thompson module divided into a block and not
drawn from any sheet. Two consequences govern everything below. A lot number on a South Division
block resolves to a cell of the lot ledger and to a street frontage. A lot number anywhere else
does not resolve at all: there is no cell, and the West Division's blocks carry **ten** lots in two
columns of five, a shape the scheme does not describe.

**The scheme reproduces an address the structure layer already carried, from a different source.**
`first_presbyterian_church` states its own seat as "the south 25 ft of **Lot 1, Block 34**", read
off Andreas and Currey and placed on 2026-08-11 — before this numbering existed. Block 34 is
`blk_lake_lasalle` on the numbering file's independent reading of Wright's numeral, lot 1 is the
north row's east end under the scheme, and the lot ledger stands the church on
`blk_lake_lasalle#06`, plat lot 1, face north, fronting Lake. That is a cross-check the plat work
did not have to pass and passes.

## The seven that seat

Seven readings, eight rows: `1834_08_06#c013` names two lots.

| Reading | Notice's address | Committed block | Committed cell | Fronts |
| --- | --- | --- | --- | --- |
| `1834_04_16#c004` | lot 3, block 18 | `blk_south_water_lasalle` | `blk_south_water_lasalle#02` | South Water |
| `1834_06_18#c006` | lot 7, block 16 | `blk_south_water_dearborn` | `blk_south_water_dearborn#05` | Lake |
| `1834_07_02#c053` | lot 7, block 16 | `blk_south_water_dearborn` | `blk_south_water_dearborn#05` | Lake |
| `1834_07_09#c024` | lot 7, block 16 | `blk_south_water_dearborn` | `blk_south_water_dearborn#05` | Lake |
| `1834_08_06#c013` | lot 3, block 20 | `blk_south_water_franklin` | `blk_south_water_franklin#02` | South Water |
| `1834_08_06#c013` | lot 3, block 41 | `blk_randolph_franklin` | `blk_randolph_franklin#02` | Randolph |
| `1834_09_03#c005` | lot 7, block 16 | `blk_south_water_dearborn` | `blk_south_water_dearborn#05` | Lake |
| `1834_10_15#c006` | lot 7, block 16 | `blk_south_water_dearborn` | `blk_south_water_dearborn#05` | Lake |

Five of the seven are one address: **G. Spring's For-Sale notice**, "LOT No. 7, in block No. 16,
one lot east of Haddock's Tavern, on Lake street", printed five legible times between June and
October 1834. Three separate readings recorded that this was the most placeable statement in the
whole corpus and that placing it was somebody else's job; `thompson_block_numbering.json` says so
in its own `why_this_file_exists`. It is now placed. Block 16 is `blk_south_water_dearborn`,
Dearborn to State, South Water to Lake; lot 7 is the south row third from the west; the cell is
`blk_south_water_dearborn#05`, whose face is **south** and whose frontage is **Lake** — the street
the notice names. The notice's own two coordinates agree with each other through an instrument
neither of them knew about.

`1834_08_06#c013` is the one notice whose two lots fall in different tiers, which its street phrase
only half admits: block 20's lot 3 fronts South Water and is west of the Dearborn draw-bridge, as
the notice says, while block 41's lot 3 fronts Randolph two tiers south and stands
`harmon_log_cabin` today. Which of the two carried the two-storey house the notice does not say.

## What the seats do not buy

Under the evidence ladder ratified 2026-09-03 an **earlier** source no more promotes an 1835 fact
than a later one does. A for-sale, auction or lien notice of 1833–34 says a building stood on that
lot on the day the notice ran, and says nothing whatever about 1835-07-01. So every one of the 23
refuses the forward carry. Where the committed town already stands a roof on one of the seated
cells it stands there from the T-1199 policy deal and not from the notice — `#05` of block 16
carries one reconstructed H1 house, and the two South Water cells read `at_capacity` with four
dealt roofs each.

## The nine whose block is read and whose lot has nowhere to land

| Reading | Notice's address | Block reads onto | Why no cell |
| --- | --- | --- | --- |
| `1833_12_10#c009` | lot 7, block 8 | Clinton–Canal, Kinzie–Carroll (West) | off the grid; ten-lot block |
| `1834_02_04#c006` | lot 7, block 8; W½ lot 3, block 44 | as above; Canal–West Water, Randolph–Washington | off the grid; and block 44 carries land, not a building |
| `1834_11_12#c015` | block 1, no lot | Dearborn–Wolcott, Kinzie–river (North) | off the grid |
| `1834_11_19#c012` | lot 2, block 1 | as above | off the grid; lot 2 would be the Kinzie row, not North Water |
| `1834_11_26#c010` | lot 2, block 1 | as above | off the grid |
| `1834_12_03#c025` | lot 2, block 1 | as above | off the grid |
| `1834_12_10#c012` | lot 2, block 1 | as above | off the grid |
| `1834_12_17#c006` | lot 9, block 1 | as above | off the grid; and an eight-lot block has no lot 9 |
| `1834_12_24#c012` | lot 2, block 1 | as above | off the grid |

Two of these are worth more than their refusal.

**The meeting house by the North Branch bridge corroborates its own block.** Block 8 reads onto
Clinton Street to Canal Street, Kinzie Street to Carroll Street. The committed
`north_branch_bridge` lands its west end "near the south-east corner of Kinzie and Canal Streets",
one street's width from block 8's north-east corner — so the notice's landmark and Wright's numeral
agree without either being fitted to the other. The lot still cannot be seated.

**The plat sharpens T-0328's lot-digit tally without reopening it.** Four of Weaver's five settings
read lot 2 and the setting of 17 December reads lot 9. T-0328 settled it at 2 on the tally alone,
without the page images. An eight-lot Original Town block has no lot 9 at all, and the blocks that
carry ten are in the West Division and not the North — so 9 is the harder reading on the sheet as
well as in the count. Nothing is reopened; the agreement is recorded.

## The one that is off this ground

`1834_08_13#c012` — "the houses situated on Lot No. 3, i[n] Block No. 111, now owned by Charles H.
Cha[p]man", under a mechanic's lien. Thompson numbers fifty-eight blocks and stops. This project's
own land-sale ground register names 111 outright: "block 111 of the school section, section 16 T39N
R14E". Section 16 lies south and west of Madison Street, outside the Original Town and outside the
ground this reconstruction models — and the Democrat's own notice of 30 April 1834 puts "LOT No. 6,
in block 111" there too, "both on the schoo[l] secti[on]". Disposed `outside_chicago`.

## The six that anchor on another building

| Reading | Anchor | What the anchor does |
| --- | --- | --- |
| `1834_06_25#c001` | `first_presbyterian_church` | stands on block 34, one block **west** of the notice's "between Clark and Dearborn" |
| `1834_09_10#c006` | the post office, and the draw-bridge | the two anchors are four blocks apart; the office is unmodelled |
| `1834_09_17#c006` | `hogan_store` | stands on the Market wedge, which the lot ledger carries no cells for |
| `1834_09_17#c008` | as `1834_09_10#c006` | same |
| `1834_10_01#c005` | the post office | a **second** witness against Andreas's Franklin and South Water |
| `1834_11_05#c010` | `exchange_coffee_house` | "opposite" a corner house reaches two blocks and four lots |

Three of these are conflicts the committed records already own, and this pass adds a witness to
each rather than resolving it.

**Miss Waite's school and the Presbyterian Church.** The notice of 25 June 1834 puts the church
between Clark and Dearborn — block 35, `blk_lake_clark`. The town has it on block 34,
`blk_lake_lasalle`, from a documented corner. Seating the school would mean either moving a placed
record on an earlier source, which the ladder does not license, or putting a school behind a church
that is not there.

**The post office after July 1834.** `hogan_store` states that on 1835-07-01 the post office is "a
DIFFERENT, UNMODELLED building" near Franklin and South Water whose construction, size and side of
either street nothing reached describes, and which "would be almost entirely invention today".
Rider's three printings put it instead on South Water nearly opposite the draw-bridge, which is the
Dearborn crossing four blocks east. The 1 October setting is a second newspaper reading against
Andreas, and it is filed here as one; the conflict stays open where the structure record keeps it.

## The one placement question this pass opens, and does not take

`mansion_house` carries "Haddock's Tavern" among its names and stands on
`blk_south_water_dearborn#01`, plat lot 5 — the south row's **west** end, at Dearborn. Spring's
notice sells lot **7** and calls it "one lot east of Haddock's Tavern", which would put the tavern
on lot **6**. The structure record says of its own position that "THE POSITION ALONG THE BLOCK IS
THIS RECORD'S CHOICE" and declares a working uncertainty of "AT LEAST A LOT'S WIDTH ALONG LAKE
STREET", because "'near Dearborn' is not 'at the corner'" — and it was placed on 2026-08-11,
months before any block or lot numeral was read onto this grid. So the notice is evidence about a
**placed** building's seat rather than about a new one, and the case for acting on it is the
record's own.

Acting on it is a structure move and a bake, and it is filed as **T-1679** rather than taken
inside a register pass. Neither this document nor the ruling register moves the record.

**Taken by T-1679 (2026-10-04): the house moved to lot 6.** The "measurement or next door"
question did not need answering: either reading puts the tavern on the lot adjacent to lot 7 on
the west, and that is lot 6. The record's position note carries the argument, including why an
1834 notice may place a house whose 1835 existence rests on Andreas. Its stable moved with it,
and the anonymous D2 shanty that stood on lot 6 took the corner (docs/LIBERTIES.md L373).
