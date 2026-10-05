
# George W. Dole's Warehouse — research dossier

**Record:** `data/structures/dole_warehouse_south.json` · **Scene status:** standing on
1835-07-01 on a continuity argument; the slaughter yard probably gone · **South Water Street
parcel**

## 1. What is documented

Andreas: George W. Dole's **warehouse and slaughter yard**, **1832**, *"close to the present site
of the Tremont House"* (Lake and Dearborn). Dole packed the first beef and pork shipped out of
Chicago.

## 2. The landmark is itself ambiguous

Andreas writes in **1884**. There were three Tremont Houses at that crossing: the **first**, built
1833 by Alanson Sweet, on the **north-west** corner of Lake and Dearborn, burned October 1839; its
successors stood on the **south-east** corner, and that is the site "present" points at in 1884.
So the phrase locates the warehouse at the **crossing** and no closer. The record takes the
south-east corner as the reading Andreas's own sentence supports, and notes that the north-west
corner can be set aside independently because the first Tremont was standing on it from 1833.

**The trap:** the warehouse is 1832 and every Tremont is later. Andreas is dating a building by a
landmark that did not exist when it was built.

## 3. Two guards that travel with this record

1. **Newberry & Dole's forwarding warehouse was on the NORTH bank** of the river, immediately east
   of where Rush Street bridge later stood — that is where the schooner *Illinois* was cheered on
   12 July 1834. **Do not merge the two, and do not move this one to the river.**
2. **In 1834 Newberry and Dole built a slaughter-house on the South Branch**, which is where a
   slaughtering business goes when it outgrows a yard behind a warehouse two blocks from the river.
   At least half of what Andreas describes here had probably moved before the scene date.

## 4. What is invented

The footprint outright, and — unusually — the **storey count**, which is tagged `conjectural`
because there is no typological argument either way: period warehouses run from single-storey
sheds to two-and-a-half-storey lofted stores, and the choice changes the silhouette by half. The
**slaughter yard is not modelled**: no source gives it a size, a boundary or a side, and a fenced
yard drawn by eye would be a larger invention than the building it served.

`shopfront` is recorded **false**, `inferred` — a warehouse had no display front, which is a claim
made from the attested use against the archetype's default.

## 5. Open threads

- A Democrat advertisement of Dole's giving an address against a cross street.
- Andreas at page-image level around scan pp. 261 and 1151, where the packing narrative sits.
- The 1834-35 town lot records for the Lake and Dearborn block.

## 6. The firm's store, by its neighbours (T-2137, 2026-10-05)

The first open thread in §5 is answered by the *Chicago Democrat*, though not by an advertisement of
Dole's own. Five advertisers fix themselves off **"Newberry & Dole's store"**:

| advertiser | where | claim |
|---|---|---|
| Tuttle & Brown, grocers | "on Dearborn street, one door **south** of" it | `chicago_democrat_1834_06_04#c011` (copy 27 May 1834) |
| J. B. Brown | same words | `chicago_democrat_1834_07_02#c021` |
| W. H. Brown | "on Dearborn street, one door from" it | `chicago_democrat_1834_05_28#c004` |
| Wm. H. Taylor, boots and shoes | "on Dearborn street, a few rods **north** of" it | `chicago_democrat_1835_05_20#c020` (copy 8 July 1834) |
| D. Graves, baker | "on South Water-street, a few doors **north** of" it | `chicago_democrat_1834_03_25#c003` |

A store with Dearborn-street neighbours both south and north of it stands on the Dearborn face, not on
a South Water corner, where the only thing north is the roadway and the river. The South Water baker
"a few doors north" puts it some way south of South Water. Andreas's "close to the present site of the
Tremont House" is the Lake and Dearborn crossing, and this record is the one committed building there.
So **this house is read as the firm's store in 1834–35, inferred**, and the signboard is lettered
`NEWBERRY & DOLE / Dry Goods, Hardware & Crockery` off the firm's own card of 26 November 1833. The
record's name stays Andreas's, because he is who names the building.

**Guard 1 in §3 is superseded.** T-1723 ruled the forwarding house's bank SOUTH on the same paper, and
Andreas's north-bank sentence is the firm's 1839 warehouse. The guard against merging still holds,
for a different reason: the firm's **store house** on South Water is placed by Peter Cohen ("next door
below Messrs. Newberry and Dole's store house, on south water street") and is a second premises, kept
as `newberry_dole_warehouse`. No single lot is next door to a South Water lot and also has a Dearborn
neighbour a few rods north of it.

**Still open:** which corner of the crossing. Taylor's "a few rods north" and Tuttle & Brown's "one door
south" fit the south-east corner the record already takes, and they fit a store just north of Lake
on the Dearborn face too. Nothing moves until a printing settles that.

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
