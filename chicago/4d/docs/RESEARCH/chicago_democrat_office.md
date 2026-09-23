
# The Chicago Democrat Office — research dossier

**Record:** `data/structures/chicago_democrat_office.json` · **Scene status:** standing, the
paper twenty months old on 1835-07-01 · **South Water Street parcel**

The first record in this dataset whose **address comes from a contemporary document**.

## 1. The load-bearing passage

*The Chicago Democrat*, Vol. I No. 1, Tuesday 26 November 1833, in its own imprint:

> "THE DEMOCRAT, Is published every Tuesday, in the village of Chicago, Cook co. Ill. **in the
> building on the corner of South Water and Clark-streets**."

And Andreas, fifty years later:

> "An office was secured in a building on the **southwest** corner of South Water and Clark
> streets, **which was unfinished at the time**."

## 2. The junction and the corner are different claims

This is the distinction the record exists to make.

| claim | evidence | tag |
|---|---|---|
| the building stood at the junction of South Water and Clark | the paper's own imprint, tier 1, contemporary, self-reported | **documented** |
| it was the **south-west** corner | Andreas, tier 3, 1884 | *inferred* |

Two of the four corners fall away independently: the north side of South Water at Clark was the
river frontage, wharves and landings, so the building is south of the street. That leaves
south-west and south-east, and Andreas is the only statement either way. `harmon_loomis_store` is
recorded at the south-east corner of the same junction — see § 4.

## 3. The Kimball reading, and why there is no `kimball_store` record

The same issue carries an advertisement: *"Just Opened and for sale AT the New Store on the corner
of South Water and Clark-streets"* — dry goods, crockery and glass ware, hardware, cutlery, caps,
cotton batting, yarn, sheeting, blankets. The transcription supplied with the scan attributes it
to **W. Kimball**; the project's source record for the issue lists the advertisement without an
attribution, and that transcription is demonstrably imperfect elsewhere in the same four pages
(it reads "C. & L. Harmon" where the scan reads "C. & I. HARMON").

Three things converge and none is proof:

- the imprint says **"the building"** — definite, singular;
- Andreas says the building was **unfinished** in November 1833, and a store advertising itself as
  *"Just Opened"* at *"the New Store"* on that corner in that month is what an unfinished building
  looks like a few weeks later;
- both notices are in the same issue.

**Conclusion adopted:** the store and the printing office were most likely in one building, and
Kimball is recorded as an **occupancy** of this record rather than as a second structure. Building
a separate `kimball_store` would assert a second building at a junction where the only
contemporary document says *the* building, and would put an invented footprint on top of this one.
The alternative — that the junction held two or more buildings — is perfectly possible and is
recorded on the record.

## 4. What the new source did not do

It gave no size, height, storey count, material or roof. Everything visible about this building
except where it stands is still inference or invention.

**And it must not be allowed to give one.** The "Two Buildings to Let" advertisement in the same
issue carries an **engraving of a three-storey building with regular fenestration**. That is a
jobbing printer's generic stock cut, not a picture of a Chicago building — the project's source
record says so explicitly, and Chicago's first three-storey structure is the Saloon Building of
**1836**, already in `data/exclusions.json`. No attribute of this record derives from it.

## 5. Open threads

- Which corner. A deed, a lot number, or a later Democrat imprint with more detail.
- Whether Harmon & Loomis's building and this building are one building.
- A clean reading of the "Just Opened" advertisement's signature line.

## The parcel's shared inventions

Three things are true of every record in the South Water Street parcel and are written once here
rather than sixteen times:

1. **The borrowed rectangle.** No period map this project has georeferenced shows a building
   footprint, and no source gives a South Water or Lake Street commercial building a dimension
   except Hogan's store (45 x 20 ft) and Philo Carpenter's log shop (16 x 20 ft). Every other
   footprint in the parcel is a rectangle built from figures borrowed from the dataset's own
   attested buildings — 40 ft frontage (Green Tree Tavern, Western Hotel), 25 ft depth (derived
   from the Green Tree's room module), 20 ft depth (Hogan's store) — capped by Andreas's
   documented **55 ft South Water lot width**. The repetition is the admission.
2. **The position method.** Modern intersection centres read from OpenStreetMap at EPSG:26916 on
   2026-08-11, offset 12.2 m (half an 80 ft platted street) to the kerb. South Water Street is
   today's Wacker Drive along the south bank; Wacker was built on its right of way in 1924-26 and
   widened northward over the old dock line, so the two lines are close but not identical.
   Working uncertainty is about **20 m** — the georeference's own residual (17.5 m RMS on Wright
   1834, 3.7 per cent paper stretch) — plus whatever the source's own vagueness adds, which is
   stated per record.
3. **The ground is not there.** Everything in this parcel east of about local E +320 stands
   outside the committed `e1834_harbor_cut` terrain box and is declared
   `ground_contact: outside_modelled_ground`. That is a terrain gap, not a structure gap.
