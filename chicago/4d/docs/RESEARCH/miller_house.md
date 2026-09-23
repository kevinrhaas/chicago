# Miller House — research dossier

**Record:** `data/structures/miller_house.json` · **Scene status:** standing on 1835-07-01, in
store or residential use, **not an inn** · **Milestone 1, north bank**

The north-bank half of the pair that made the forks a settlement. Miller's house faced the Wolf
Point Tavern across the water; the two were joined by the Miller–Clybourn ferry licensed 2 June
1829; and the settlement's first Peoria County tavern licence went to Clybourn and Miller
jointly, on a $100 bond, with Miller licensed 13 April 1831.

By July 1835 it is the quieter of the pair — standing, past its innkeeping days for at least
three years, and modelled that way.

---

## 1. Identity and sequence

| period | event |
|---|---|
| c. 1827–1829 | **Samuel and John Miller** open a store on the north bank at the forks |
| **1827 or 1830** | a **two-storey house added to the log cabin, fronting the river** — see §3 |
| 1830 | enlarged and operated as a **tavern**, competing with the Wolf Point Tavern |
| 1831 | Wau-Bun already describes the house as **"at this time vacant"**; Miller had removed to the place becoming Michigan City |
| after 1832 | converted to **store** use, run by P. F. W. Peck per DRLOIH |
| 1834 | "Miller retired from the field" |
| **1835-07-01** | **standing; occupancy unattested** — see §5 |

John Miller's separate log house of 1831, used as a tannery and called Chicago's first recorded
factory, stood nearby in the same cluster. It is **not** modelled by this record.

## 2. Conflict: which bank? — recorded and resolved

| reading | sources |
|---|---|
| **North bank, on the point between the North Branch and the main stem** *(adopted)* | chicagology: "The Miller House stood on the point of land between the North Branch and the Main Channel. It was a log structure partly sided, and was erected by Mr. Samuel Miller." · Wau-Bun: "on the north side of the river … near the forks" · DRLOIH's Wolf Point narrative: a store "on the north bank of the river at the forks" |
| South branch, opposite Wolf Point | `drloih_hotels` |

**Four independent statements against one, and the ferry settles it.** The Miller–Clybourn ferry
was licensed to cross the **North Branch** between Miller's tavern and the Wolf Point Tavern; a
south-branch Miller house makes that route impossible. The outlier is treated as an error, and
it is the same chronology that is internally inconsistent about the Wolf Point Tavern's build
date and the Western Hotel's size.

## 3. Conflict: 1827 or 1830 for the two-storey addition?

| reading | source | wording |
|---|---|---|
| **1827** *(adopted)* | `drloih_hotels` | "In 1827, Samuel Miller and his brother John, with Archibald Clybourn holding a partnership interest, added a two-story house to the cabin, fronting the river." |
| 1830 | `drloih_wolf_point` | "In 1830, they enlarged their store and began to operate it as a tavern." |

1827 is adopted **because it is the statement that describes the form change being modelled** — a
two-storey house added to the cabin, fronting the river — where the 1830 statement describes a
change of trade. The two may well be different events: an enlargement in 1827 and a conversion
to innkeeping in 1830, in which case both are right. Either way the building had its 1835 form
well before the scene date, so the dispute does not touch the scene. Tagged `inferred`.

## 4. Form — a composite building, and what the archetype cannot yet do

Three descriptions, all compatible:

- "a two-story house added to the cabin, fronting the river" (DRLOIH)
- "a log structure partly sided" (chicagology)
- the 1833 view of that bank showing "a two-story building and adjoining log cabin"

So: **a one-storey log cabin with a two-storey frame range in front of it, facing the water.**

This has a consequence for geometry. `stories: 2` is documented for the *river-fronting range*;
the log cabin behind stands at roughly half that height. The record flags that the
`log_dwelling` archetype must build a **mixed-height mass** rather than extruding one footprint
to one wall height — the same kind of requirement the Sauganash's attached log wing produced for
`frame_tavern`, and discovered the same way, by reading the descriptions rather than the plan.
`wall_height_m: 5.2` describes the frame range and overstates the log part; it is flagged rather
than averaged, because an average would match neither description.

The footprint is an **L** that reflects the composition — a 9 × 6 m two-storey range on the river
frontage with a 6 × 5 m log cabin set back behind — but **every number in it is invented**, so
the polygon is tagged `conjectural` and cites no sources. The *shape* carries evidence; the
*size* does not, and the two should not be confused.

## 5. Function at the scene date — present, not innkeeping

Three accounts, disagreeing in chronology and agreeing in direction:

1. Wau-Bun, describing 1831, already calls the Miller house **"at this time vacant"**.
2. DRLOIH has the business converted to a **store** run by **P. F. W. Peck** after 1832.
3. A third account has **Miller retiring from the field in 1834**.

**Modelled as present and in secondary store or residential use, tagged `inferred`.**

**The record deliberately carries no `occupants` block.** The named candidates all belong to
earlier years, and the Peck attribution does not survive to the scene date on this project's own
evidence: `data/exclusions.json` (`peck_brick_house`) places Peck in 1835 at his two-storey frame
store at the south-west corner of South Water and LaSalle. Rather than name an occupant the
sources do not support for July 1835, the block is omitted and the gap is stated here.

## 6. Placement

**No surviving intersection locates this building.** The streets platted across this ground in
Kinzie's Addition were staked in 1833–35 and the point has since been rebuilt, so the coordinate
is derived from the datum origin at the forks and from bank geometry.

Modern water polygons from OpenStreetMap put the **nose of the point about 39 m north of the
datum origin**, with the main-stem north bank running east from there and the North Branch east
bank running north-west. The footprint's south face is set **14 m north of the main-stem bank**
and its west face about **22 m east of the North Branch bank**, which puts the building on the
point and off both waters.

**Uncertainty: ~20 m from the georeference, plus an unquantified allowance for the modern banks
not being the 1835 banks.** This ground was filled and wharfed and is now built over, and —
unlike the west bank — there is no street line here to check it against, so the along-bank
position is the softer of the two axes.

**Facade bearing 180°**, due south onto the main stem, from "a two-story house … fronting the
river". On a point the river is on two sides: about 215°, fronting the confluence and Wolf Point
across the water, is equally arguable and would rotate the building ~35°.

## 7. Open questions

| question | where to look |
|---|---|
| Any dimension | Andreas vol. 1, "Wharfs, Piers and Early Hotels" pp. 626–631, at page-image level |
| Who occupied it in July 1835 | Chicago Democrat advertisements, 1835; Andreas on the north side |
| When it came down | No source reached gives a date — which is why the phase closes at the end of 1835, the last date this record needs to claim |
| Relative heights of the log and frame elements | Unattested; currently 5.2 m for both, which is wrong for the cabin |
| The 1833 view of the north bank | Identify and open it — it is the only depiction reported to show this building |
