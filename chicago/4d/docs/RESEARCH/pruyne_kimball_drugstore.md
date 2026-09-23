
# Pruyne & Kimball's Drug Store — research dossier

**Record:** `data/structures/pruyne_kimball_drugstore.json` · **Scene status:** asserted standing
on 1835-07-01 and unable to prove it · **South Water Street parcel**

## 1. The whole of the evidence

Andreas, one clause: Kimball was *"a partner of Mr. Pruyne in a drug store on South Water Street."*

No date. No block. No corner. No building. No description. The **trade** is the best-attested thing
about the record, which is the opposite of the usual case in this parcel.

## 2. Grading

| aspect | tag |
|---|---|
| the trade | **documented** |
| the street | **documented** (and it is the only part of the position that is evidence) |
| documented_range | *inferred*, and it is the weakest kind this dataset holds — Andreas dates the partnership only to "the 1830s" |
| position, footprint, storeys | **conjectural** |

The range is set to 1834-1835 rather than opening in 1830 because a range widened until the date
gate stops complaining is exactly the failure the gate warns about. **If evidence dates the
partnership after July 1835 this record belongs in `data/exclusions.json`** — that is the most
likely single correction to it.

## 3. Where it stands, and why that is not a finding

The point is on the south side of the Clark-to-Dearborn block, roughly mid-face. **Nothing whatever
supports that choice of block**: it is a lot on the right street, chosen because that block had an
unbuilt stretch between `harmon_loomis_store` and `madore_beaubien_house` wide enough to take a
building without overlapping either. **Placing a record where there is room is a rendering decision,
not a research finding**, and it is written on the record so a visitor can recover it. The
along-street uncertainty is the whole **630 m** of South Water Street from Market to State.

The **side** of the street is the one reasoned part: the north side was the river bank, wharves and
landings.

## 4. A name collision kept separate

A **W. Kimball** appears in the transcription accompanying *The Chicago Democrat* of 26 November
1833, advertising **dry goods, crockery, hardware, cutlery, caps and cloth** from a new store at the
corner of South Water and Clark. **Dry goods and drugs are different trades** and there is no
evidence the two Kimballs are one man. That advertisement is discussed on
`chicago_democrat_office` and is deliberately not attached here.

## 5. Open threads

Any *Chicago Democrat* or *Chicago American* advertisement for Pruyne and Kimball would date the
partnership and very likely give a block — **a single dated advertisement would move three
attributes at once**.

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
