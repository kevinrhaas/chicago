
# Harmon & Loomis's Store — research dossier

**Record:** `data/structures/harmon_loomis_store.json` · **Scene status:** standing and trading
on 1835-07-01 · **South Water Street parcel**

## 1. What the sources give

- Andreas: *"Jim Kinzie's store, P. F. W. Peck's store, Harmon's and Loomis's were all on South
  Water Street"* — the firm on the street by 1833.
- Andreas, separately: a **three-storey** building at the corner of Clark and South Water housing
  the *Daily Chicago American* on its third floor — **in 1839**.
- *The Chicago Democrat*, 26 November 1833: a display advertisement headed **"C. & I. HARMON"**,
  dated 18 November 1833 — dry goods, crockery, hardware, wet and dry groceries, and *"on
  commission, a large lot of Leather, Saddlery, &c."*

## 2. Two traps, and the record avoids both

**The height trap.** The vivid description available for this corner is the 1839 building.
Chicago's first three-storey structure is the Saloon Building of **1836**, which this project
already excludes by date, so three storeys in 1835 would import a boom that had not happened.
`stories` is recorded as **2, inferred**, and the record says in terms that the 1835 height is
unverified — which is exactly what the project's own dossier says.

**The name trap.** Andreas writes "Harmon's and Loomis's". The contemporary advertisement is
headed "C. & I. HARMON" and names no Loomis. Those are compatible but they are not the same
statement, and the record carries both. Note also that the transcription supplied with the scan
reads "C. & L. HARMON"; **the scan is cited, not the transcription.**

## 3. The corner, and the most likely way this parcel is wrong

Andreas gives *"corner of Clark and South Water"* and never a side. The north side of the street
is the river frontage, so the choice is south-west or south-east; the **south-west is separately
and explicitly claimed** by `chicago_democrat_office`, whose junction is confirmed by the paper's
own imprint. This record therefore takes the **south-east**.

That is a modelling choice, not evidence. **The honest alternative:** Andreas says Calhoun
*"secured an office IN a building"* — he rented. Harmon & Loomis owned a building at this junction.
A newspaper renting an office in a merchant's corner store is the ordinary arrangement of the
period. If that is right, this record stands **about 37 m east of where it belongs and duplicates
`chicago_democrat_office`**. It is the single most likely error in the parcel.

## 4. Open threads

- A Democrat advertisement of Harmon's giving a corner.
- Whether "C. & I. Harmon" and "Harmon & Loomis" are the same firm at different dates.
- Andreas at page-image level around scan pp. 295 and 777.

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
