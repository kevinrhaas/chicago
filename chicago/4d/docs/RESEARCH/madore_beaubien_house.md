
# Madore Beaubien's Log House — research dossier

**Record:** `data/structures/madore_beaubien_house.json` · **Scene status:** standing on
1835-07-01 on a continuity argument · **South Water Street parcel** ·
**`review_required: true`**

The oldest building on the modelled business street and the only log one on it — which is the
point of including it. South Water Street in July 1835 was not a uniform row of new frame stores.

## 1. What is documented

Andreas: *"a two roomed log house which was the first building on lot No. 1"*, built **1831**, at
the **south-west corner of South Water and Dearborn**. Madore Beaubien was licensed as a merchant
in 1831 and elected a town trustee in 1833.

"The first building on Lot 1" is a **plat reference**, which makes this the tightest locational
statement in the parcel.

## 2. What is not

No dimension, no height, no roof, no material beyond "log", and **nothing at all after 1831**.
The building stands in this scene on the ordinary continuity argument, and the counter-argument is
specific: this was prime frontage on the town's business street in the 1835 boom, the Dearborn
drawbridge landed at the foot of Dearborn a year before the scene date, and a four-year-old log
house on that corner is exactly what a boom replaces first. The same weakness, argued the same
way, carries `hogan_store`.

## 3. A collision worth watching

`bates_auction_room` is documented on the **west side of Dearborn between Lake and South Water** —
the same block face this building's east wall stands on. The two records do not overlap **only
because the auction room is placed at the middle of its face for want of any statement**. If the
auction room stood at the north end of that face, it stood on Lot 1, and one of the two records is
wrong about something.

## 4. Why review is flagged

`AGENTS.md` holds that Native presence and representation are not a research gap to be filled by
inference but a subject requiring consultation, and the final removal of the Potawatomi from
Chicago falls in **August 1835**, weeks after the scene date. This record and
`jb_beaubien_homestead` sit inside a family history that runs directly into that. The record
therefore states the built fabric and the two civic facts Andreas gives — merchant's licence 1831,
town trustee 1833 — and no more, and `review_required: true` blocks the 1835 scene from being
marked released until that consultation happens.

## 5. Open threads

- Any statement about the building after 1831.
- The 1830 Thompson plat's Lot 1, Block 1 boundary, which would tighten the corner further.

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
