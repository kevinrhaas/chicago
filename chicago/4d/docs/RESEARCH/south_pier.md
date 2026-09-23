# South Pier — research memo

Record: `data/structures/south_pier.json` · Archetype: `pier_crib`
Written 2026-08-11. **Sections 2 and 3 of `north_pier.md` are shared with this record**
— the raster reading, the cross-check against the 200 ft entrance, the correction to
`data/traces/vectors/wright_1834_east.json`, and the argument that Wright drew the
authorised works rather than the built ones. This memo carries what is specific to the
south pier.

---

## 1. What this record is for

The southern of the two timber crib lines holding open the 1834 cut. It was the **first**
of the works to be begun — the improvement started on the south side of the river in
June 1833 under Major George Bender, commandant of Fort Dearborn, with Henry S. Handy as
assistant superintendent, before the north pier was carried out "a like distance" in the
spring of 1834. It is the shorter pier throughout the period: the littoral drift runs
south along this coast, so the north pier is the weather pier and takes the sand, and this
one holds the other bank of the channel.

## 2. The measured line

Read off the southern of the two red pier lines on Wright 1834, through the same fitted
affine as everything else (method in `north_pier.md` §2).

| | value |
|---|---|
| landward end of the inner face | resource pixel 3171, 1498 → local **E +1215.9, N +252.5** |
| bearing | **103.50°** from grid north (north pier: 103.36°) |
| perpendicular separation from the north pier's inner face | **64.2 m** |

Two lines that come out parallel to a tenth of a degree and four per cent from a
documented 200 ft entrance neither of them supplied is the check that says the right pair
was read.

**The polygon runs on the negative side of the measured line** — v from −7.62 to 0 — where
the north pier's runs from 0 to +7.62. The line that was read is the **channel** face of
both structures and they stand on opposite sides of it. Building this one the other way
would put a 25-ft crib inside a 200-ft entrance and narrow the harbour by an eighth.

**The drafted length is not used**, and on this pier the reason is at its starkest: the
southern line runs about 1,165 ft on the sheet, and the south pier did not reach that
length until after 1837.

## 3. The conflict this record exists to hold open

**Three statements about how long the south pier was when the 1835 season opened, and one
author on both sides.**

| statement | source |
|---|---|
| 400–500 ft of south pier built in the fall of 1833 under Bender | `andreas_1884_v1` I, scan pp. 261, 487 |
| south pier about 200 ft at the end of 1834 | `wikipedia_chicago_river` harbour-works summary |
| "extended 500 ft in 1835, total 700 ft" — i.e. 200 ft standing when the season opened | `andreas_1884_v1` I, scan pp. 487, 489 |

Those cannot all be true unless the pier lost a third to a half of its length between 1833
and 1835, which nothing reached reports.

**Settled by Andreas against Andreas rather than by preferring one author.** His own 1835
sentence contains the arithmetic: extended 500 ft to a total of 700 ft leaves 200 ft
standing at the start. That agrees exactly with Wikipedia's end-of-1834 figure, from a
source that did not derive it from him. So **two independent statements converge on
200 ft** and one earlier statement in the same volume disagrees with both.

Two explanations are available and **neither is evidenced**, which is why the conflict
stays on the record rather than being closed:

1. the fall-1833 figure describes work *contracted or attempted* rather than pier
   standing; or
2. a first season's cribs did not survive the February 1834 storm that breached the bar.

**It was not averaged, deliberately.** 200 and 450 average to 325 — a number no source
states and no reasoning supports — and the average would have concealed the more
interesting fact, which is that a compiler contradicts himself about this pier fifty years
after the event.

## 4. The length for 1 July is an interpolation, graded `inferred`

| date | length | source |
|---|---|---|
| end 1834 | ~200 ft | Wikipedia, corroborated by Andreas's own 1835 arithmetic |
| **1835-07-01** | **~400 ft (adopted)** | interpolation — this record |
| end 1835 season | 700 ft | `andreas_1884_v1` I, scan pp. 487, 489 |

From 200 ft to 700 ft is 500 ft in a season. Straight calendar interpolation puts 1 July
at 450 ft; a season-weighted reading — crib work runs roughly April to November, so
perhaps a third of the season's work is in the water by then — gives about 365 ft.
Dossier 04 §3 reaches "roughly 300–500 ft" independently. **400 ft** is the middle of that
band and sits between the two arithmetics.

**The error bar is the band**: anything from 300 to 500 ft is equally consistent, which is
±30 m on a 122 m structure — **a quarter of its own length**. That is what an
interpolation looks like when it is honest.

## 5. What is invented

Identical to the north pier, and deliberately from the same constants so that the two
inherit one invention rather than two that could drift apart:

- **`width_m: 7.62` (25 ft), `conjectural`** — `pier_crib_params.DEFAULT_WIDTH_M`. The
  survey cannot supply a width at 1:7,200; see `north_pier.md` §3. The footprint inherits
  it and the whole pier renders as massing.
- **`deck_height_m: 1.524` (5 ft), `inferred`** — **doubly borrowed** here: it is the
  middle of an uncited band that dossier 01 zone 24 states of the *north* pier, and
  zone 25 gives this pier no height at all. Retained because the two piers were built in
  the same works, in the same seasons, by the same supervisors, to hold the same channel.
- **`construction: timber_crib`, `inferred`** — zone 25 gives this pier no construction
  either. Period and regional practice; a reading, not a report.
- **Crib module, 30 ft** — the archetype's constant, not a record attribute.

## 6. Phase width and ground

Both as for the north pier. The `documented_range` is 1835-06-01 … 1835-07-31 because
this structure **more than trebled** during the season the scene sits in the middle of;
`ground_contact` is `outside_modelled_ground` because the heightfield stops at local
E +320 and this pier runs from E +1216 to about E +1335. See `north_pier.md` §6 and §7 for
the full arguments, including why `pier_crib`'s `GROUND_CONTACT = "ends"` is half wrong by
construction and what it will cost when ROADMAP S2e lands.

## 7. What would replace most of this

The Chief Engineer's annual report for 1835 or the House Document series, for the length;
J. D. Graham's 1857 and 1858 hydrographic surveys of the Chicago bar, or any specification
or voucher for the crib work, for the width and the construction.
