
# Thomas Church's Store — research dossier

**Record:** `data/structures/thomas_church_store.json` · **Scene status:** standing on
1835-07-01 **if the date is right** · **South Water Street parcel** (Lake Street)

The first store building on Lake Street — and the whole of the evidence is **one sentence**.

## 1. The sentence

From the uncredited editorial **addendum** at the foot of chicagology's early-street-maps page
(`chicagology_prefire275`):

> "In 1833, when Chicago received its charter as a village, Lake Street was the main street of the
> town.; in this same year the first Tremont House was erected at the northwest corner of Dearborn
> and Lake streets. **The first store building on Lake Street, a two-story frame structure, was
> built by Thomas Church.** The first Court House followed in 1835 and the City Hotel, later the
> Sherman House, in 1837."

It gives a **form** — two-storey, frame — and a **street**. It gives no year, no block, no lot, no
corner, no dimension.

**The page invites a date it does not give.** The sentences around it run 1833, 1835, 1837, so a
reader picks up 1833 from *position on the page* rather than from the sentence. The project's own
source record warns about exactly that, and the dossier tags the date unpinned and treats the
building as c. 1833-35.

## 2. A source that arrived mid-parcel

**An earlier draft of this record cited nothing at all.** When it was written there was no
`data/sources/chicagology_prefire275.json`, and citing an id that does not resolve is the one thing
`AGENTS.md` forbids outright — so the record carried no `sources` array anywhere and every
attribute that would otherwise be documented was tagged `inferred` with its reasoning written out,
plus a note saying which single file would fix it.

The source record landed during this parcel's work. `stories` and `function` moved from `inferred`
to **documented**; `construction` did **not**, because "frame" does not name a framing system.

**The caveat travels with every documented tag here:** this is uncredited modern editorial prose,
graded **tier 4**, and the project's own source record says the addendum is the weakest text in its
set and *must never outrank Andreas*. It is cited because it is explicit and because it is the only
place this building has been found — not because it is strong.

## 3. What is still invented

- **Position, outright.** The street is all the source gives. The block, the side and the point
  along it are chosen to avoid the Lake Street buildings this dataset knows the corners of and has
  not yet modelled — the Tremont House (NW Lake & Dearborn), the Mansion House (north side just
  east of Dearborn), the Exchange Coffee House (NW Lake & Wells), the First Presbyterian church
  (SW Lake & Clark), St Mary's (Lake & State). **That is a rendering decision, not a finding.**
  Along-street uncertainty is the whole of Lake Street inside the town, roughly 700 m, and the side
  of the street is a coin toss.
- **Footprint, outright.** Note that the documented **55 ft lot width is a South Water figure** and
  is not evidence about Lake Street, so no cap is claimed here.

## 4. The risk that could remove the record

If the store is **1835** work it may have been going up, or not yet standing, on 1835-07-01 — in
which case this record belongs in `data/exclusions.json` rather than in the scene.

## 5. Open threads

- **Andreas at page-image level** for any mention of Thomas Church, which would outrank the addendum
  on this project's own grading.
- A *Chicago Democrat* advertisement giving Church's address.

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
