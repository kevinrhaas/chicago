
# John Bates Jr.'s Auction Room — research dossier

**Record:** `data/structures/bates_auction_room.json` · **Scene status:** standing on
1835-07-01 · **South Water Street parcel**

## 1. What is documented

Andreas: *"a wooden structure, erected in 1833 or 1834, by John Bates, for an auction-room"*, on
the **west side of Dearborn Street between Lake and South Water**. Bates cried the school-section
sale of October 1833 and was deputy postmaster from the same year — sorting mail in `hogan_store`,
570 m away in this model.

This is one of the few buildings in the parcel whose **use is documented as the reason it was
built** rather than inferred from its occupant's trade.

## 2. The anisotropic uncertainty

The source fixes one axis tightly and leaves the other free:

- **across** Dearborn Street: about **20 m**, the georeference's residual;
- **along** Dearborn Street: about **55 m**, half the block, because nothing says where on the
  126 m face the room stood.

The record is placed at the middle of the face, which is a convention and not evidence. See
`madore_beaubien_house` § 3 for the collision this creates at the north end of the same face.

## 3. The two-year window

Andreas offers "1833 or 1834". `documented_range` opens at the start of **1834**, the later of the
two, as a floor. If he meant 1833 the building is a year older; if he meant late 1834 the range
opens a few months early. Neither changes the 1835 scene, which is why the ambiguity is recorded
rather than resolved.

## 4. Open threads

- An 1834-35 Democrat advertisement giving Bates's sale-room address against a cross street.
- The school-section sale notices of October 1833.
- The 1834 town lot records for the Dearborn frontage between Lake and South Water.

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
