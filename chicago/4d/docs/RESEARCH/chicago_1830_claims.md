# "Map of Chicago in 1830" — what it is, and what it cannot be asked

**Parcel T-E1** (`docs/ROADMAP.md`, lane 3). Written 2026-08-14 after the owner supplied two
scans and asked that the town's eastward and southward extension "match the real geographic
maps of the city".

**Source record:** `data/sources/andreas_1884_chicago_1830_map.json`

---

## Identification — verified, not inferred

The sheet is the engraved fold-out inset in **Andreas, *History of Chicago*, vol. 1 (1884),
facing pp. 112–113**, imaged as **leaf `n240`** of the Internet Archive item
`historyofchicago01andr`.

The identification was made by opening the page image and reading the title banner, and it is
cross-fixed independently: leaf `n242` is p. 113 and carries the Harrison harbour map already
registered here as `harrison_1830_river_mouth`, which pins the leaf-to-page offset. Leaf `n241`
is the inset's blank verso, on which the map shows through mirrored.

Rights were already settled: the volume is registered as `andreas_1884_v1`, public domain.

**Two different plates in this volume are called "Chicago in 1830."** The volume's own table of
illustrations lists `Chicago in 1830 (inset) 112, 113` under MAPS and `Chicago in 1830 164`
under VIEWS. They are not the same document. **Cite the leaf, never the name.**

**The owner supplied two images and they are not the same document either.** The detailed
issue corresponds to this plate. The simplified line-art version — fewer trees, a decorative
banner, a reduced label set — is a different rendering whose publication has **not** been
identified. It must not be cited as this source. Anything read only from the line-art version
is currently uncited and cannot ground a claim.

---

## The finding that governs every use of this sheet

The plate carries a printed note, transcribed from the scan at 3× magnification:

> **NOTE.**—The names given on various tracts of land are those of the primary patentees, or
> persons by whom entry was made, entered or patented between the years 1828 and 1836. The
> Information is taken from "Book of Original Entry." Streets as shown were laid out
> subsequent to 1830.

### 1. It is a land-title map. A name is not a house.

The names are **who took title**, not who lived there, and not that anything was built. This is
the single most important constraint on the sheet, and it cuts directly against the intuition
that a densely-named map shows a densely-settled town. It does not. It shows a densely-*entered*
one.

**Consequence for the roof programme:** a named tract may **never** license an anonymous roof.
Lane 3's eligibility rule (T-E4) must not read "named ⇒ buildable". If anything, the sheet is
evidence for the owner's instinct that houses were *not* spread across this ground — the
handful of structures the plate bothers to draw and label is a far better guide to where
building had actually happened than the wall of names is.

### 2. The entry window runs past our scene date.

**1828 to 1836.** The scene is **1835-07-01**. Some names on this sheet belong to people who had
not yet entered the land when the scene is set, and the sheet does not date individual entries.
Treating it as a snapshot of 1835 imports up to a year and a half of later history.

Where a specific tract's entry date matters, it has to come from the Book of Original Entry
itself or another dated source — not from this plate.

### 3. It is an 1884 compilation that labels its anachronisms "present".

The sheet layers later features onto an 1830 base and marks several of them *present*, meaning
present **in 1884** — fifty-four years after its nominal date. Observed on the plate:

| label on the sheet | what it actually is | in 1835? |
|---|---|---|
| **"PRESENT CANAL"** (dashed) | the Illinois & Michigan Canal | **no** — not completed until 1848 |
| **"Present Court House Square"** | a later civic siting | not as drawn |
| **"present outlet of river"** (coloured issue) | the post-cut mouth | the cut is 1834; the label is 1884's present, not ours |
| the street grid | later survey | **no** — the plate's own note says the streets postdate 1830 |

**Every "present" on this plate is an anachronism of half a century.** A runner who traces the
canal would add a waterway that did not exist in 1835 by more than a decade.

---

## Division of labour, fixed

This is the table already in `docs/ROADMAP.md` lane 3, restated with the evidence now in hand:

| element | driver | why |
|---|---|---|
| lake shore, sand bar, harbour cut, piers, old southward channel | **Wright 1834** | a survey, five years closer, already the master warping raster |
| the pre-cut bar and the old mouth in detail | **`harrison_1830_river_mouth`** | a U.S. civil engineer's harbour survey — **already registered**, and a better sheet for the bar than this one |
| street and block geometry | **Thompson plat 1830** + **Hathaway 1834** | this plate disclaims its own streets |
| land entry, owners, Canal Land / School Section extent | **this plate** | the thing it is actually good for |

**Note for T-E2:** the sand bar half of that parcel may need no new evidence at all. The
Harrison plate — already held, already public domain — draws the bar, the "Sand and Gravel"
ground and the old southward channel in plan. Check it before going looking.

**Note for T-E4, added 2026-08-24 (T-0026), because this table is where the next reader will
come looking for southern ground.** The plate's Canal Land / School Section reading is real
and it is the thing this sheet is good for — and **it has no route into the scene, at any
confidence, until the terrain reaches Madison Street.** Measured by
`tools/measure_southern_ground.py`: the committed heightfield ends at local **N -400 m**,
which falls inside Washington Street's own platted corridor; Madison — the plat's south
boundary, and the line this plate divides the Canal Land and School Section along — is
**125.2 m further south**; and the plat's last tier between them (six blocks, 48 lots,
6.28 ha, Market to State) has **0 of 24** block-boundary points on modelled ground. So
reading a subdivision distinction off this sheet cannot license a roof: the eligible-ground
rule needs the ground first. The successor parcel is the southern heightfield extension,
**T-0219**, and what it needs from the traces is narrow — the South Branch's two banks
carried from N -405 to about N -531. The lake shore (N -589.2) and the bar (N -436) already
reach past Madison.

---

## Named structures the plate draws

These are the buildings the plate chose to draw and label, transcribed from leaf `n240` at
1.9× magnification. **This is a reading list, not a set of claims** — each still needs its own
record, its own citation and a standing-on-1835-07-01 test before it can enter the scene, and
several are certainly outside the modelled area.

- Miller's house · Elijah Wentworth's cabin · Robinson's trading house · La Framboise's cabin
  and store · Mark Beaubien's · "Present Court House Square" (see the anachronism table)
- Porter's log cabin · Billy Caldwell's frame house · the Kinzie house · Fort Dearborn with its
  garden, grove and field · "Entered by John Baptiste Beaubien" · "102½ Acres Entered by Robert
  A. Kinzie"
- Slaughter house on the north branch (Clybourn's, on the reading of the engraved hand)

Tract names read on the sheet, north and west of the town, as a starting index for T-E4:
Joshua Sackett, Henry W. Cleaveland, Horatio A. Cleaveland, John Ludby, William Bennett,
Charles Taylor, Lyman Meacham, Harvey Meacham, Joseph Davenport, William Davenport, William
Filkins, George W. Cassidy and assignee, Jedidiah Wooley, Ansel Chipman, D. Hunter, W. L.
Newberry, Temple and Brown, Sedgwick, Alexander McDole, Daniel Elston, Philo Carpenter, Wright,
Hiram Huganin, Jefferson T. Cross, Zachariah Grant, Edmund S. Kimberly, William H. Scott,
Francis C. Blanchard.

**Hands differ and several readings are uncertain** (McDole/McDale, Filkins/Filkian, Ludby,
Huganin). Any of these used in a record must be re-read at full resolution and the reading
recorded, not carried over from this list.

---

## Open questions this parcel did not settle

1. **The line-art issue is unidentified.** Find its publication or stop using it.
2. **Individual entry dates.** The sheet gives a 1828–1836 window and no per-tract dates. The
   Book of Original Entry would settle which tracts were entered before 1835-07-01.
3. **Whether the plate's drawn structures were standing on 1835-07-01.** Each is a per-record
   question; the plate's nominal 1830 date is not an answer, in either direction.

---

## T-E2's disposition of every structure the plate draws

Added **2026-08-15 by parcel T-E2**, whose acceptance requires that *every named claim
from the sheet is either a structure record, an exclusion with a citation, or listed as
an open question — nothing silently dropped.* The reading list above is transcribed from
leaf `n240`; this is what this project has done with each entry. **A row saying "open
question" is a disposition, not an omission** — it is the only honest one for a building
whose survival to 1835-07-01 nobody here has tested.

| the plate draws | disposition | where |
|---|---|---|
| Fort Dearborn, with its garden, grove and field | **records** — the stockade, parade and eleven buildings, plus the garrison garden | `data/structures/fort_dearborn_*.json`; all fifteen are on the reservation and permitted by `1835_no_build_ground.json` |
| the Kinzie house | **exclusion with a citation** — gone by the scene date, "dilapidated beyond repair" from 1832 | `data/exclusions.json` → `kinzie_house` |
| Billy Caldwell's frame house | **watch list, with the question stated** — existence itself is unverified, and the record sits inside AGENTS.md's standing constraint on 1835 and Indigenous history | `data/exclusions.json` → `watch_list` → `billy_caldwell_house` |
| the slaughter house on the north branch (Clybourn's, on the reading of the engraved hand) | **record** | `data/structures/clybourn_slaughterhouse.json` |
| Miller's house | **record** | `data/structures/miller_house.json` |
| Robinson's trading house | **record**, paired with Caldwell's in one entry | `data/structures/robinson_caldwell_cabins.json` |
| "Entered by John Baptiste Beaubien" (a tract name) | **not a house, by the plate's own note** — but Beaubien's dwelling and barn are records, on the reservation and permitted | `data/structures/jb_beaubien_homestead.json`, `beaubien_barn.json` |
| "102½ Acres Entered by Robert A. Kinzie" (a tract name) | **not a house, by the plate's own note.** Robert Kinzie's store is a separate record with its own evidence | `data/structures/robert_kinzie_store.json` |
| Mark Beaubien's | **OPEN QUESTION.** Andreas puts it "on what is now Michigan Avenue, about where the Exposition building now stands" — on or beside the reservation, south of the fort — and Mark had left the Sauganash by 1834. Neither its footprint nor its survival to 1835-07-01 has been tested here. It is not in the dataset and is not excluded | `docs/research/04-structures-south.md` line 217 |
| Elijah Wentworth's cabin | **OPEN QUESTION.** No record, no exclusion, no siting read at full resolution | — |
| La Framboise's cabin and store | **OPEN QUESTION.** As above | — |
| Porter's log cabin | **OPEN QUESTION.** As above | — |
| "Present Court House Square" | **an anachronism of the plate**, handled in the table above; the block itself is reserved ground on other evidence | `data/reconstruction/1835_reserved_ground.json` |

**Four open questions, and they are the same question four times: was it standing on
1835-07-01, and where exactly?** The plate cannot answer either half — it is a
land-title compilation of 1884 with a nominal date of 1830 — so none of them can be
closed from this sheet, which is why T-E2 lists them rather than inventing dispositions
for them. Three of the four (Wentworth, La Framboise, Porter) are almost certainly
outside the modelled area; **Mark Beaubien's is not**, and it is the one worth taking
first.

**What T-E2 did NOT do, so it is not assumed:** it made no new structure record and no
new exclusion. Every disposition above already existed, and the parcel's own work was
the ground rather than the buildings — which is the reason the four open questions are
still open after it.
