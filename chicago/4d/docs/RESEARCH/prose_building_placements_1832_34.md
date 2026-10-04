# The six prose building placements of 1832–34, carried forward or refused

**T-1625.** The prose counterpart of T-1624, and a separate ticket for a reason: T-1624's 23
readings give a lot number and a block number off a newspaper page, and these six give a
**corner, a cross street or a named neighbour** out of a compiled history — which is a different
instrument and a different kind of failure. Four come from Moses and Kirkland's *History of
Chicago* vol. 2 (1895) and two from the historical sketch in Norris's *Chicago Directory* of 1844.
`data/research/spend_rulings.json` held them under `the_prose_placement_waits_on_the_corner_pass`,
which named three jobs it had no business doing in a ledger:

1. resolving 1895 street names against 1835 ground — half these locators are "what is now";
2. deciding whether an undated fitting-up falls before or after 1835-07-01;
3. reading a relative bearing in rods off the plat.

All three are done here, with `data/traces/kinzie_addition_block_numbering.json`,
`data/traces/thompson_block_numbering.json`, `data/streets/1835.json`, `data/structures/` and
`data/exclusions.json` in front of them. The hand-off rule is **deleted** from the ledger rather
than renamed.

**One of the six reaches the scene and five are refused.** That is a better rate than T-1624's
nought for 23, and the reason is structural: a newspaper notice is a snapshot of a day, and a
compiled history sometimes gives a SPAN — and a span is the one shape in which a page printed
sixty years after the scene speaks to 1 July 1835 without being carried back to it.

## The one that reaches the scene: Richard J. Hamilton's house

`bk_mose2_006`, Moses and Kirkland vol. 2 p. 155:

> He lived first in the fort, and, when that grew too crowded with the refugees, he moved to the
> Agency House; and in 1833, with Col. Owen, hired John Watkins to teach the little school in the
> old stable near by. At about this time he built his house on what is now Michigan street between
> Cass and Rush, where he lived for nineteen years.

**The street names resolve.** Michigan Street on the north bank is today's Hubbard Street — *not*
Michigan Avenue, which is a different street on the other side of the river. Cass Street is today's
North Wabash Avenue, on this project's own ground control (`wright_1834_gcps.json`, GCP G6). Rush is
unchanged. So the locator is one block face in Kinzie's Addition: the `cass_rush` column of the
Michigan–Illinois tier, cell `c3r8`, **block 11** by the Addition's boustrophedon numbering.

Block 11 is worth a sentence of its own. It is the **one cell in the Addition whose numeral Wright's
sheet does not carry** — that file's own reading says "block 11's missing figure is the one place
only the rule speaks" — so the block *number* here rests on the run and not on ink, while the cell's
*boundary* rests on the Addition's measured module as usual. The Addition has no lot subdivision in
this project at all (`thompson_lots.json`, `kinzies_addition.lot_subdivision_withheld`: no lot rule
has been read for this plat), so naming the cell buys a face and not a lot.

**And the town already stands a house on that face.** `watkins_school_house` was placed in August
2026 from Andreas's sentence that John Watkins taught "later in a house on Michigan Street between
Cass and Rush" — a house Andreas gives **no owner** for. Moses and Kirkland give an owner for a
house on the same face and **no school** in it. The join is Hamilton himself: he is one of the two
colonels who hired Watkins, and both pages carry the same two colonels, the same schoolmaster, the
same year, and the same first schoolroom beside the Agency House. One house described twice is the
economical reading.

**The caveat, and it is live.** Moses and Kirkland do not say which SIDE of Michigan Street Hamilton
built on. This record stands on the north side on Andreas's authority alone; the south side is the
Addition's river tier, blocks 3–7. If Hamilton built on the south side these are two houses and
`watkins_school_house` has no owner again. A source naming the side settles it either way, and that
is the first thing on the record's "what would upgrade it".

### What was written, and what was not

| record | field | before | after |
|---|---|---|---|
| `hh_hamilton_richard_j` | `lives_at` | `cobweb_castle`, `inferred` | `watkins_school_house`, `inferred` |
| `watkins_school_house` | `occupants` | Watkins in 1833; "occupants on the scene date unattested" | Hamilton and his household from about 1833 |
| `watkins_school_house` | `name` | Watkins school house | Richard J. Hamilton's house on Michigan Street |

Three things did **not** move, and each is deliberate.

**No confidence was raised.** Moses and Kirkland is a compilation of 1895. Under the evidence ladder
ratified 2026-09-03 such a page corroborates and dates and may not promote, so both fields stay
`inferred` — exactly the grade `lives_at` carried when it pointed at the Agency House. What improved
is the reasoning under the grade, not the tier above it.

**No coordinate, footprint or form moved.** The identification is about whose building the record is.
The mid-block position, its ±55 m along the face and the unknown setback are as they were, and
`stands_on_lot` is untouched.

**The record id is not renamed.** `watkins_school_house` is a contract — the sidecars, the lot
seating, the dossiers and the Evidence panel all carry it — so the finding moves `name`, `aka`,
`occupants` and the notes, and leaves the key alone.

### The field it answered

The structure record's `documented_range.to` was its weakest field and said so: *"1835-12-31 IS AN
INFERENCE ABOUT PERSISTENCE, NOT AN ATTESTATION … If it had gone by the scene date, nothing in the
sources would show it."* Nineteen years from about 1833 runs to about 1852. **1835-07-01 falls
inside the span**, so the persistence inference now runs forward from a statement about this house
instead of from a general fact about a growing town. The grade is unchanged; the argument is not.

The household card's `lives_at` said the mirror image of the same gap: *"Nothing reached follows him
out of it or keeps him in it."* Something now follows him out of it.

**The ledger asserts this unit with no written ruling at all**, which is what a hand-off is supposed
to reach. `natural_disposition` reads the card, finds `bk_mose2_006` named on a graded field that
cites the volume, and closes the unit `asserted`; the draft ruling was deleted because
`spend_rulings.json` may only close a unit nothing else has closed.

## The five refusals

### `bk_mose2_003` — the First Baptist meeting house, South Water near Franklin

*"…occupying for that purpose the First Baptist church, a small frame building located on South
Water street near Franklin."* Sproat's English and classical school for boys held there on
weekdays, Miss Sarah L. Warren assisting from the spring of 1834, and by `bk_mose2_009` the town's
**first Episcopal services on 19 October 1834** in the same building. Three congregations' worth of
use in one small frame shell, and the best-evidenced building of the six.

**The street resolves and the block does not narrow to one.** "Near Franklin" reaches both blocks
Franklin Street divides — block 21 `blk_south_water_market` and block 20 `blk_south_water_franklin`
— and the unplatted river margin opposite, where this project has already refused building
positions at every tolerance. Two candidate blocks, no lot, a 220 m face.

**Corrected by T-1690: the town already held this building, so the unit is no longer refused.**
The ruling that stood here said no record names it. One does — `temple_building`, placed
2026-08-11 from Andreas's *"small house of worship belonging to the First Baptist Church Society,
on South Water Street, near Franklin"*, with *"the First Baptist meeting house"* among its names
and Sproat's school in its upper storey. It is the same building under the same street and the
same "near". It also already carried the fact the refusal said was missing: the Chicago American
of 4 July 1835 calls School District No. 2's electors to *"the Baptist Meeting House"* on 11 July,
ten days after the scene date, so the building is followed past October 1834 after all.

So nothing is placed and no roof is added. Moses and Kirkland's page 79 is written onto the record
as a corroboration of its keepers and of its locator, and page 348's 19 October 1834 Episcopal
service under Rev. Isaac W. Hallam is written onto its use as a single dated use, not a tenancy.
The ledger now reads this unit as **asserted** off `temple_building`'s keepers field, and the
written refusal was deleted, because a ruling may only close a unit nothing else has closed.

### `bk_mose2_008` — Mark Beaubien's frame building near Mr. Noble's house

The first Sunday school in Chicago, 19 August 1832, in *"a small frame building, erected by Mark
Beaubien, near Mr. Noble's house"*, which on the day it opened *"had neither doors nor windows, and
was very imperfectly roofed."*

**The anchor is not in the town, and that is checkable in one grep.** `data/structures/` holds no
Noble house and `data/exclusions.json` does not name one. There is no committed coordinate for
"near" to be near, so placing this building means inventing the anchor, then a distance, then a
bearing — three inventions under one citation. (The ledger note this replaces asserted that the
project holds the Noble house. It does not; that is what sent this pass looking.)

**The loss here is the condition**, and it is worth naming because it is the kind of material fact
the renderer can carry: a half-finished frame in August 1832 is, by 1 July 1835, finished or moved
or gone, and the page does not say which.

**The second building in the same sentence is ruled with it.** The school *"later assembled at the
house of Rufus Brown, within the stockade of the fort"*. This town stands `brown_boarding_house`,
in the South Division at local ENU E 428 N −30 — **outside** the palisade, not within it. Whether
Brown's house of 1832 inside the stockade and Brown's boarding house of 1835 outside it are one
building moved, two buildings, or one misremembered enclosure is **not settled here**. Nothing is
moved on the strength of a 1832 recollection, and the disagreement is recorded rather than resolved.

### `bk_mose2_009` — the building afterwards known as Tippecanoe Hall

*"Later, religious services were held in a building afterwards known as Tippecanoe Hall, situated
at the southeast corner of Kinzie and State streets, which was fitted up for the purpose at the
expense of John H. Kinzie."*

**The corner is the best locator in the whole set and it resolves.** `kinzie` and the north-bank
Wolcott line are both committed in `data/streets/1835.json` — Wolcott Street is today's North State
Street, the equivalence `cobweb_castle` is placed on — and the southeast quadrant of their crossing
is the north-bank tier at the foot of State, the ground the Agency House stands on the river side of.

**The date refuses it, and the page refuses itself.** The paragraph before is dated 19 October 1834;
the word is "Later"; the sentence after has Kinzie donating two lots at Cass and Illinois for the
permanent church, which is St. James', 1836–37. So the fitting-up falls in a bracket about two years
wide with **1835-07-01 inside it**, and nothing narrows it. A locator cannot supply a date and a
bracket is not one. **This project does not split a bracket**: choosing the half of an interval that
puts a building in the scene is choosing the answer, and a run that does it once cannot refuse the
next reading that wants the same favour.

**The name is anachronistic and is not a date either.** The Tippecanoe campaign is 1840 and
"afterwards known as" says the name was acquired later — which is evidence about the name and not
about the fabric, in either direction.

**What would settle it:** one dated notice of Episcopal service at Kinzie and State in the 1834–35
Chicago Democrat or Chicago American, a corpus this project has read for other purposes. The corner
is recorded so that reading lands on finished work.

### `n1844_tf_023` — Colonel Owings's house, 80 rods south of the Fur Company house

*"About 80 rods to the south of that, stood a house, once occupied by Colonel Owings, but since
washed away by the Lake."*

Eighty rods is 1,320 feet, about **402 m**, and the project could measure it the moment it had a
point to measure from. It has none. The Fur Company house Beaubien occupied is this project's
`john_dean_house`, and **`john_dean_house` is on the exclusion list** — refused for the 1835 scene
because no source attests its survival past 1818 and because nothing dimensions it. So the anchor is
a building this project has found in writing not to stand here, and a 402 m bearing off it would
place Owings's house on the strength of the first one's absence.

**The bearing is one-dimensional as well.** "About 80 rods to the south" fixes a distance along one
axis and says nothing about the across-shore offset — on ground where the across-shore axis is the
whole question, because the 1815–18 lakefront at the foot of Randolph, the 1828 cut, the 1833–34
piers and an eroding shore are four different waterlines in twenty years.

**And the house's own fate points away from the scene.** "Since washed away by the Lake" is a
terminus before 1844 with no beginning: the ground it stood on is gone, so an 1835 placement would
have to reconstruct the building *and* the shore under it. Norris is describing 1832. Refused on the
anchor and refused on the carry.

**The other two buildings in the sentence are already the town's** and are corroborated rather than
placed: "Cobweb Castle, on block No. 1" is `cobweb_castle`, which reaches the same corner from
Wau-Bun and Andreas; the Fur Company house is `john_dean_house` and its exclusion. Norris's **block
number** for Cobweb Castle is worth recording as an independent check on a position this project
derived without it.

### `n1844_tf_024` — Norris's inventory of what stood at Chicago in 1832

Five buildings besides the fort. **Three are already the town's or already refused:** John Kinzie's
dwelling east of the Lake House is `kinzie_house`, excluded as gone by the scene date; Mark
Beaubien's tavern "on the site of the Sauganash, generally known as the Eagle" is `sauganash_hotel`;
Robinson the Indian chief's cabin at Wolf Point is `robinson_caldwell_cabins`. **Two reach the plat
and nothing holds them.**

**The log building at the corner of Dearborn and South Water Streets.** Both streets are committed
and the crossing resolves, but a corner is four quadrants: the two landward ones are block 16
`blk_south_water_dearborn` and block 17 `blk_south_water_clark`, both numbered off Wright's sheet,
and the two river-side ones are the unplatted margin this project has already refused positions on.
No quadrant is named and no lot is given, so the locator stops at a crossing and reaches two blocks.

**The building on block 14, and this project refuses that block by name.**
`thompson_block_numbering.json` reads Wright's numerals by cutting each crop from the block's own
committed street lines, and its `refused` list names *"blocks 14 and 15, on the Carroll–Fulton band
east of the North Branch"* — refused because the grid does not reach that ground. There is no cell
on the map to put a building in, and inventing the cell to receive it would be inventing the plat.

**The forward carry is refused for both regardless**, and that is the whole weight of the unit:
Norris is inventorying 1832, three years before the scene. What the reading fixes is the **floor** —
five buildings in the whole of Chicago — and that is a fact about the town and not a seat for a roof.

## What this pass did not do

It placed no building, invented no coordinate, and moved no structure. The one record it changed
gained a name, a keeper and a better argument for a date it already carried, at the grade it already
carried it. Five readings are refused in writing with the block work recorded so nobody reads it a
third time, and one new ticket — T-1690 — carries the building that ought to exist. (T-1690 found
it already standing as `temple_building`; see the correction under `bk_mose2_003`. Four refusals
stand.)
