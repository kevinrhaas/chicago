# Wolf Point Tavern — research dossier

**Record:** `data/structures/wolf_point_tavern.json` · **Scene status:** standing on 1835-07-01,
probably still in innkeeping under a changed name · **Milestone 1, west bank**

The building that named the place. Its identity is vivid and its geometry is unknown — the
painted wolf sign, the landlord succession, the 12½¢ rate and the Black Hawk War headquarters
are all attested, and not one source measures it, counts its storeys or fixes it to an
intersection. It is the least precisely placeable structure in this parcel and the record says
so in three separate places.

---

## 1. Identity and sequence

| period | landlord | note |
|---|---|---|
| 1828 (disputed — see §2) | built for **James Kinzie** | west bank at the forks |
| by 1829 | **Archibald Caldwell**, for Kinzie | liquor licence 8 December 1829 |
| from early 1830 | **Elijah "Old Geese" Wentworth** | the name most of the recollections use |
| 1831–1833 | **Charles and Mary Taylor** | |
| **1833–1836** | **William Walters** | **covers the scene date** |
| 1832 | — | Gen. Winfield Scott's Black Hawk War headquarters |

Aliases in circulation: Wolf Tavern, Wentworth's tavern, Old Geese's tavern, Rat Castle,
Taylor's tavern, Travelers' Home, Western Stage House. The last two are post-1834 renamings
and are part of the function dispute in §4.

Rates while it was a public house: 12½¢ a night, 13¢ to stable a horse.

## 2. Conflict: built 1823 or 1828?

| reading | source | what it says |
|---|---|---|
| **1828** *(adopted)* | `drloih_wolf_point` | "James Kinzie … built a tavern on the west bank of the river at Wolf Point in 1828" |
| 1823 | `drloih_hotels` | "opened in 1823 by James Kinzie, John Kinzie's son, and David Hall on Wolf Point" |

**These are the same publication contradicting itself**, which is a reason to distrust both
dates rather than to prefer one confidently. 1828 is adopted because it is the reading of the
narrative account that also carries the operator succession and the wolf sign — i.e. the page
that knows the most about the building — and because 1823 sits oddly with the licensing record,
in which Archibald Caldwell's liquor licence is dated 8 December 1829 and the settlement's first
Peoria County tavern licence went to Clybourn and Miller.

**It does not matter for the 1835 scene.** The building stood under either reading. The
`documented_range` is therefore tagged `inferred`, not `documented`, and the dispute is carried
in its note.

## 3. Conflict: what was it made of?

Not really a conflict, but a description that flattening would lose. chicagology:

> "This building was partly log and partly frame, and was situated on the ground north of Lake
> Street Bridge."

The record carries `construction: log` (documented) plus a separate `frame_addition: true`
(documented) so the mixed fabric survives into the data. **The frame element's size, position on
the building and date are all unattested** — a geometry requirement discovered from the evidence,
in the same way the Sauganash's attached log wing was.

*Updated 2026-08-10.* The attribute was written here and in the record as `frame_extension`,
which is not the name the `log_dwelling` archetype reads, so the documented frame half reached no
vertex and nothing said so; the same happened to the sign, recorded as `signage` against the
archetype's `sign`. Both are renamed and built as of 2026-08-10 — see `docs/LIBERTIES.md` L20 for
the account and L24 for the invented dimensions the build required. The frame bay is 4 m of the
12 m frontage, one storey, at the north end; those three numbers are conjectural and the record
says so on each. What would settle them is what would settle the footprint: Andreas vol. 1
pp. 626-631 at page-image level, or the Braunhold retrospective view at plate level.

## 4. Conflict: was it still an inn in July 1835?

Three readings, all from the same body of sources:

1. **William Walters was landlord 1833–1836** — ordinary innkeeping at the scene date.
2. It "ceased operations as a public house in 1834" (`drloih_hotels`).
3. After 1834 the name changed successively to the **Travelers' Home** and the **Western Stage
   House** — a change of sign, not of trade.

**Adopted: innkeeping, tagged `inferred`.** Two of the three readings are compatible with it, and
a stage house is still a public house. A landlord of a closed house is a contradiction the
sources have not resolved, which is exactly why the tag is not `documented`.

## 5. The wolf sign — the one documented visual feature

> "A painted sign of a wolf was hung outside the tavern by approximately 1833."

Hung well before the scene date, so it belongs in the 1835 model. **What it looked like is
entirely unattested** — size, board shape, how it hung, how the wolf was drawn. The archetype
should carry the sign as a distinct, separately-confidenced element rather than folding it into
the massing, so that a viewer using the confidence toggle sees "we know there was a wolf sign"
and "we invented this wolf" as two different claims.

Wau-Bun separately derives the Wolf Point name from an Indian resident called Moa-way, "the
Wolf". That is a competing etymology for the *place name*, not a competing fact about the sign.

## 6. Placement — and why it is the weakest in the parcel

**No surviving intersection locates this building**, so the Sauganash method (half an 80 ft
platted street off a documented corner) does not apply. The coordinate is derived from the datum
origin at the forks and from bank geometry.

What is attested:

- **West bank at the forks, north of the Lake Street crossing** — chicagology puts it "on the
  ground north of Lake Street Bridge".
- **James Kinzie's residence next south, Walker's meeting house north** — so it sits in the
  middle of a three-building river-front row, and the row's order constrains it.
- Wau-Bun's 1831 sequence reads "Facing down the river from the west was, first a small tavern
  kept by Mr. Wentworth", which is why the facade is put on the water.

Method: Lake Street's centreline northing at the west bank is 4637286.5, interpolated along Lake
between the two OpenStreetMap control points; its north kerb is 12.2 m beyond that at 4637298.7,
half an 80 ft platted street. The footprint's south face is set 40 m north of that kerb, leaving
room to the south for the Kinzie residence and ~50 m to the north for the meeting house, in the
documented order. Across the bank the east face sits 11–19 m back from the **modern** west-bank
line (OpenStreetMap water polygons), the setback varying because the modern bank runs north-west
across the building.

**Uncertainty: about 40 m along the bank and about 20 m across it.** The along-bank figure is
this record's own — nothing fixes how far north of the bridge the tavern stood. The across-bank
figure is the georeference's, compounded by the modern bank not being the 1835 bank: this reach
was wharfed and rebuilt, and the direction of that change is not established here.

Facade bearing 90°, due east onto the water; the bank runs north-west, so 75–105° is equally
defensible.

## 7. What is unknown

| question | where to look |
|---|---|
| Any dimension at all | Andreas vol. 1, "Wharfs, Piers and Early Hotels" pp. 626–631, at page-image level |
| Storey count | The same; or the retrospective "Wolf Point from the south as it might have appeared in 1830" reproduced in Andreas, examined at plate level — tier 5, and not yet opened for this record |
| Size and position of the frame element | Unattested in anything reached |
| What the wolf sign looked like | Unattested; probably unknowable |
| The building's fate after 1836 | No source reached gives one — which is why the phase closes at the end of Walters's tenancy rather than at a demolition |
