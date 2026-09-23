
# J. H. Kinzie's Store — research dossier

**Record:** `data/structures/jh_kinzie_forwarding_store.json` · **Scene status:** standing on
1835-07-01 · **South Water Street parcel**

A documented trade on an undocumented lot.

## 1. What is documented

- Andreas: *"Jim Kinzie's store, P. F. W. Peck's store, Harmon's and Loomis's were all on South
  Water Street"* — a Kinzie store on the street by **1833**.
- Andreas, separately: **J. H. Kinzie advertising as a forwarding and commission merchant in 1834**.

Forwarding and commission was what South Water Street was *for*: taking other men's goods off the
schooners and getting them inland. Andreas records **250 vessel arrivals in 1835, 22,500 tons**.

## 2. The name question

**"Jim Kinzie" is James Kinzie**, who already appears in this dataset as the builder of the Wolf
Point Tavern and the Green Tree on the west bank. **The 1834 forwarding advertisements are John H.
Kinzie's.** Whether the South Water store belonged to one brother, the other, or both at different
times is not settled by anything reached. The record follows the **advertisement**, because an
advertisement is the man's own word about his own business, and the id carries those initials —
but `occupants` is tagged `inferred` for exactly this reason rather than `documented`.

## 3. Where it stands

`position` is `conjectural`. The street is all Andreas gives; the dossier records the block as
unattested. The point is on the south side of the **Franklin-to-Wells** block, and the choice of
block carries **one weak argument and no more**: a forwarding and commission house wants wharfage,
and the west end of South Water was the wharf and landing end nearest the forks and the South
Branch. That is a reason, not evidence — the difference between this and a coin toss, not the
difference between a guess and a finding. Along-street uncertainty is the whole **630 m** of the
street.

This is the one record in the parcel that lands **inside** the modelled terrain box (local
E +257), so it carries no `ground_contact` declaration.

## 4. Open threads

Any 1834-35 *Chicago Democrat* advertisement carrying the store's address — very likely to exist,
since Andreas is quoting from those files. The 1834-35 town lot records for South Water.

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
