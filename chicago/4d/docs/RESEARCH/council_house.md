# The Council House — research dossier

**Record:** `data/structures/council_house.json` · **Scene status:** standing on 1835-07-01 by
bracketing — attested in use in 1834 and again on 18 August 1835 · **north bank, somewhere in a
215 m band** · `review_required: true`

A log council house on the north side of the river. The project's dossier had it only as the
assembly point of 18 August 1835 — six weeks **after** the scene date, with no description of the
building. Reading Andreas at full text supplied the other half.

---

## 1. The two attestations, and the join between them

**Before the scene date.** Andreas, on the Methodist society organised in 1834, while it was
still meeting wherever it could and before its own frame house was contracted on 30 June 1834:

> "For a time services were held in various places — **in Billy Caldwell's log council-house**,
> in Chester Ingersoll's tavern, or in Watkins's school-house; but as the membership of the
> Church increased, the necessity for a building became more pressing…"

**After the scene date.** The *Chicago Tribune* of 14 August 1910, printing John Dean Caton's
recollection of 18 August 1835, transcribed by chicagology:

> "They assembled at the '**Council House**' **on the north side of the river, east of the
> present State street and west of the 'Lake House,'** a hotel which was at the northeast corner
> of Rush and Water streets."

A building in use in 1834 and in use in August 1835 was standing in between unless something took
it down and put it back, which nothing says. **That inference is the strongest thing in this
record.**

**The join is its weakest.** Andreas's "Billy Caldwell's log council-house" and the Tribune's
"Council House" are treated as the same building, on the grounds that both are a council house on
the north side in the same two years and neither source knows of a second. *Neither source makes
the identification.* If they are two buildings, this record takes its construction from one and
its position from the other.

A third mention, on the same chicagology page, may push the building earlier: at the treaty
council of September 1833, "a keg of twisted tobacco was rolled into **the council house**". The
page does not say it is the same building, so the record's range opens at 1834 and says so.

## 2. Position — a point inside a band

The Tribune bounds it and nothing narrows it:

| bound | local E | derivation |
|---|---|---|
| east of State Street | +827 | modern OSM intersection at Kinzie, the same control the 1834 sheets were georeferenced against |
| west of the Lake House at Rush and Water | +1045 | modern OSM Rush Street |

That is a **215 m stretch of riverbank**. The record places the building near the middle of it,
a little north of the drawn 1834 waterline, and tags `position` **conjectural** with no sources —
a point chosen inside an attested band is not a derivation. Along-bank accuracy is no better than
**±110 m**, five times the georeference's own uncertainty and the largest positional error in
this dataset. The sidecar's flat `uncertainty_m: 20` badly understates it.

## 3. What is invented

| attribute | state | note |
|---|---|---|
| `position` | `conjectural` | see § 2 |
| `footprint` (12 × 7 m) | `conjectural` | ~40 × 23 ft, one room long enough to seat a council and a congregation — the two uses the sources record |
| `form.construction` (log) | `documented` | "Billy Caldwell's **log** council-house" — the only word anybody wrote about its fabric, and it rides on the join of § 1 |
| `form.stories`, `wall_height_m`, `roof_type`, `roof_pitch_deg`, `chimneys` | `inferred` | from type and use |
| `ground_contact` | `outside_modelled_ground` | 617 m east of the terrain box |

## 4. Review flag, and what this record does not do

The events the sources attach to this building are the 1833 Treaty of Chicago and the gathering
of 18 August 1835 — the removal of the Potawatomi from Chicago. `AGENTS.md` places that under a
standing constraint: **nothing in this dataset depicts, stages or narrates it**, and the scene
date is six and a half weeks before the second. What is modelled is a log building on a bank.
`review_required: true` holds the scene short of `released`.

**What would upgrade it:** any source naming a street, a corner or a lot. The *Chicago Democrat*'s
notices of agency business are the likeliest; the corrected 1835 Wabansia and Kinzie's Addition
plat would show which lots in that band were built on.
