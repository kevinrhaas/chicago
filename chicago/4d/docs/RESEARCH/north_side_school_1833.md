# North Side school house, 1833 — research dossier

**Record:** `data/structures/north_side_school_1833.json` · **Scene status:** standing, and **in
use as a public school in 1835** · **north bank, on the river bank just east of Clark Street**

The house Colonels R. J. Hamilton and T. J. V. Owen are said to have built for a school in 1833
— "the first house built for a school in Chicago" — in which John Watkins carried on the school
he had begun in 1832 in Hamilton's twelve-foot horse stable.

---

## 1. Sequence

| date | event | source |
|---|---|---|
| May 1832 | John Watkins arrives in Chicago | Andreas (Watkins's own letter, 22 June 1879) |
| autumn 1832 | Hamilton and Owen employ Watkins "to teach a small school in the North Division, **near the old Indian agency-house in which Colonel Hamilton then resided**". The room is Hamilton's **horse stable, twelve feet square** | Andreas |
| after the first quarter | Watkins moves the school into Jesse Walker's **double log house on the West Side**, near the forks | Andreas |
| **1833** | Hamilton and Owen "**built a house on the north bank of the river, just east of Clark Street, in which Mr. Watkins continued his school** … the first house built for a school in Chicago" — *but this does not recur to Mr. Watkins's recollection* | Andreas, from Mr. Wells's report |
| 1834 | Jesse Walker's first quarterly meeting is held "in **the Watkins school-house, which was located on North Water Street, between Clark and LaSalle**" | Andreas, Methodist chapter |
| **1835** | "**John Watkins was then teaching what had become a public school on the North Side, on the river bank just east of Clark Street, in the building erected by Colonels Hamilton and Owen** … in 1833" | Andreas, schools chapter |
| 1835 | "Mr. Watkins taught as late as 1835, but **the exact date of his retirement is not known**" | Andreas |
| 19 Sept 1835 | the call to organise the township into school districts; District No. 1 is the North Side | Andreas |

## 2. The book disagrees with itself twice

**On whether the building exists.** Andreas prints the claim and the doubt in the same
paragraph: Wells's report says Hamilton and Owen built it; Watkins, who would have taught in it,
did not remember it. Forty pages later Andreas states it as fact, dates it, and cites himself
("as has already been stated"). This record follows the second statement and keeps the first as
the doubt it is.

**On which side of Clark Street it stood.** The schools chapter says twice "just east of Clark
Street". The Methodist chapter says "on North Water Street, **between Clark and LaSalle**" —
which is **west** of Clark, about a block away. The schools chapter is adopted: it is the more
specific statement, it is made twice, and it is the chapter about this building. **If the church
chapter is right, this building stands about 110 m west of where it is drawn.**

The two agree on the substance a reconstruction needs: a Watkins school-house stood on the North
Water Street frontage near Clark Street, and it was there in 1834 and 1835.

## 3. Position

Clark Street's modern centreline was read from OpenStreetMap through the Kinzie intersection
(EPSG:26916 E 447646.20, N 4637668.88 — local E +573.5, N +273.1) and carried south on the OSM
bearing; its east kerb is 12.2 m east of that, half an 80 ft platted street. The 1834 north bank
and the North Water Street frontage were read off the Wright 1834 sheet through this project's
fitted affine: the drawn bank runs at about local N +98 along this stretch and the block row's
south line — the street's north kerb — at about N +128. The building sits with its west face
6 m east of the Clark kerb and its south face 12.5 m north of the bank, which is what "on the
river bank" says.

Uncertainty: ~20 m from the georeference, ~5 m from reading the sheet by eye, and the
block-scale disagreement of § 2, which is larger than both.

## 4. What is invented

| attribute | state | note |
|---|---|---|
| `footprint` (7.3 × 5.5 m) | `conjectural` | 24 × 18 ft, sized for the thirty scholars Watkins's subscription was written for |
| `form.construction` (log) | `conjectural` | see § 5 |
| `form.stories`, `wall_height_m`, `roof_type`, `roof_pitch_deg`, `chimneys` | `inferred` | from type |
| `ground_contact` | `outside_modelled_ground` | 281 m east of the terrain box |

**Do not attach the one dimension the source gives.** "Twelve feet square" belongs to Watkins's
*first* schoolroom — Hamilton's horse stable of 1832 — and is not this building.

## 5. Log or frame

Genuinely two-sided at this date, and the choice also chose the archetype.

- **For log:** everything standing on the north bank in the 1820s was log (Andreas, of 1823:
  "All these houses were of logs"), and *Wau-Bun*'s 1831 north bank is a ring of log buildings.
- **For frame:** 1833 is the year the town began building in frame, and the nearest comparable
  building we can date is frame — the first Methodist meeting house, put up **at the corner of
  North Water and Clark streets**, one block away, on a contract signed 30 June 1834 for "a
  frame building twenty-six by thirty-eight feet; twelve-foot posts; sheeted and shingled roof;
  a neat pulpit; a platform for table and chairs" for $580.

Log is recorded, tagged `conjectural`, because a preference between two readings is not a
derivation.

## 6. A finding this parcel did not build

The passage above is a **documented, dimensioned, dated north-bank building standing on the scene
date**: the first Methodist meeting house at North Water and Clark, 26 × 38 ft, frame,
twelve-foot posts, finished and in use until 1836. It is **not** this project's
`walker_meeting_house` (a log building of 1831 whose bank is disputed) and it is not yet in the
dataset. It is the best-evidenced unbuilt structure this parcel turned up.
