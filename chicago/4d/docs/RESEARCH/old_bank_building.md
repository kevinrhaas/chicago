
# The Old Bank Building — research dossier

**Record:** `data/structures/old_bank_building.json` · **Scene status:** standing on
1835-07-01 on an untested continuity argument · **South Water Street parcel** ·
**the thinnest building in the parcel that is still a building**

## 1. The whole of the evidence

Andreas: in **1834** Gurdon S. Hubbard packed *"in the old bank building, corner of Lake and La
Salle streets"* — the season in which he packed some **five thousand hogs**.

That is one sentence. It gives a building, a junction, a year and a use. It gives **no corner, no
dimension, no material, no storey count and no description whatever**.

## 2. It was nearly excluded, and here is why it was built

The record was drafted as an exclusion — the argument being that everything a visitor would see
would be invention, which is the standard by which this project declined to build the Franklin
Street post office (`docs/RESEARCH/hogan_store.md` § 4). The project's direction then changed: **an
absent building is invisible to a visitor while a conjectural one is legible**, and the confidence
view is what makes that safe. The record is built and graded down hard: position, footprint and
storeys are all `conjectural`.

## 3. Three cautions

**1. The name is an anachronism.** Chicago had **no bank in 1834**; the Illinois State Bank branch
opened in **December 1835**, five months after the scene date. So "the old bank building" is
Andreas in 1884 naming a building by something it became, and **nobody in July 1835 called it that**.
The id and name are kept because renaming a record is worse than annotating one, but no interface
should present that name as period usage.

**2. The corner is a one-in-four guess.** This is why `position` is `conjectural` here while the
otherwise identical `harmon_loomis_store` is `inferred`: at Clark and South Water two corners fall
away on evidence (the river frontage) and a third is separately claimed, so the choice is reasoned.
Lake and LaSalle is an ordinary four-cornered crossing a block inland with nothing to eliminate any
quarter. The four candidates are about **40 m** apart.

**3. The size rests on a volume argument that is weaker than it sounds.** The footprint is the
parcel's only enlarged rectangle — 15.24 x 9.144 m = 50 x 30 ft — scaled up because five thousand
hogs is not a season's work in a 40 x 25 ft shop. But a packing season is months long and the
building needed to hold a **day's** work, not a season's.

One period detail about this crossing, recorded because it is vivid and decides nothing: Andreas
has *"a pond of water on Lake Street, corner of La Salle, inhabited by frogs"* as late as **July
1836**. Which part of the junction is unstated, and it was not used to choose a corner.

## 4. Open threads

Any statement naming the corner. Any description of the building at all. Andreas at page-image
level around scan p. 1151, where the packing narrative sits. The 1834-35 town lot records for the
Lake and LaSalle block.

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
