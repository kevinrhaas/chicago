
# Jones's Grocery and Provision Store — research dossier

**Record:** `data/structures/h_jones_store.json` · **Scene status:** standing on 1835-07-01 ·
**South Water Street parcel**

A contemporary advertisement and no address — the shape of most of the weak tier of this street.

## 1. What is documented

- *The Chicago Democrat*, 26 November 1833, a display advertisement headed **"Grocery & Provision
  Store. B. JONES. CHICAGO-ILLINOIS."** — primary evidence that the trade was being carried on in
  Chicago on that day.
- Andreas, among the 1834 advertisers: *"grocery and provision store and forwarding and commission
  store by H. Jones."*

Neither says **where**. The advertisement gives no address beyond "Chicago-Illinois".

## 2. The initial, recorded rather than chosen

Andreas writes **H. Jones**. The scan reads **B. JONES**. A contemporary advertisement is the man's
own word about his own name and would normally win outright — but the reading comes off a scan of a
damaged sheet, **B and H are among the easiest letters to confuse in a display face of this
period**, and the transcription accompanying the scan is demonstrably imperfect elsewhere in the
same issue ("C. & L. Harmon" for "C. & I. HARMON").

So **the surname is carried and the initial is not**. Both readings are in `aka`. The record id
keeps the `h_` this project's dossier assigned it, because renaming a record is worse than
annotating one.

## 3. Grading

| aspect | tag |
|---|---|
| the trade | **documented**, twice, once contemporaneously |
| position, footprint, storeys | **conjectural** |
| construction, wall height, roof, pitch, chimney | *inferred* (typological) |

The record sits at the west end of the Wells-to-LaSalle block; **nothing supports that choice of
block** — it is a lot on the right street with room on it. Along-street uncertainty is the whole
630 m of South Water Street. The **side** is reasoned: the north side was the river bank and
wharves.

The larger 40 x 25 ft rectangle is used rather than the small one because Andreas describes the
business as a grocery and provision store **and** a forwarding and commission store — two trades
under one roof, wanting floor for barrels. That is an argument about the trade, not the building.

## 4. Open threads

An 1834-35 advertisement carrying Jones's address, which Andreas's own 1834 summary implies exists
in the *Democrat*'s files. A clean reading of the 26 November 1833 advertisement block, which would
at least settle the initial.

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
