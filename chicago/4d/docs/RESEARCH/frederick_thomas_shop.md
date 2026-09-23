
# Frederick Thomas's Shop — research dossier

**Record:** `data/structures/frederick_thomas_shop.json` · **Scene status:** standing on
1835-07-01 · **South Water Street parcel** · **the least-evidenced building in the model**

## 1. The whole of the evidence

Andreas records that **Frederick Thomas advertised from "two doors from the American office"** in
1835. That is it. Not a corner, not a block — a count of doors from a building that is itself only
placed "near the draw-bridge".

## 2. Everything is graded down, and that is the record working

| aspect | tag |
|---|---|
| that a man of this name advertised from these premises | **documented** |
| position | **conjectural** |
| footprint | **conjectural** |
| storeys | **conjectural** |
| **function** | **conjectural** — no source says what he sold |
| construction, wall height, roof, pitch, chimney | *inferred* (typological) |

## 3. The arithmetic, stated so it can be corrected

Andreas states South Water lots were **55 ft** wide, so "two doors" is about **110 ft = 33.5 m**.
The record sits 33.5 m east of `chicago_american_office`'s origin, on the same frontage.

**The direction is the one piece of real reasoning.** Two lots *west* of the American office would
cross Dearborn Street — that record's west wall stands on the Dearborn frontage — and "two doors"
describes premises on one block face, not across a crossing. East is the only reading that keeps
the phrase meaning what it means. **That argument inherits the American office's own guess** about
which side of Dearborn it stood on; if the American was west of Dearborn, the direction argument
evaporates.

## 4. Why it is worth having anyway

"Two doors from" is **evidence about the street** even when it is weak evidence about the building.
It says South Water Street east of Dearborn had a continuous enough row of premises in 1835 for a
man to give his address by counting them. A model that draws only the buildings whose corners are
documented shows a row of isolated structures with gaps between them that never existed — and that
is a false statement too, and a less visible one. This is the argument `docs/LIBERTIES.md` L37
makes.

## 5. Open threads

The *Chicago Democrat* or *Chicago American* for 1835 carry the advertisement Andreas is quoting.
A single number of either paper would move `function` from conjectural to documented and might
give a block.

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
