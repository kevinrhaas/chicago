
# P. F. W. Peck's Store — research dossier

**Record:** `data/structures/peck_store.json` · **Scene status:** standing and in trade on
1835-07-01, with Peck living in it · **South Water Street parcel**

The anchor of the South Water Street commercial row: a two-storey frame store at the south-west
corner of South Water and LaSalle, with an unfinished loft over it that was used as lodging.

## 1. Sequence

| date | event | source |
|---|---|---|
| July 1831 | Peck arrives at Chicago with goods in the schooner *Telegraph*; licensed merchant | Andreas |
| 1832-33 | the store is built — **no month or year is fixed by any source reached** | Andreas (via the dossier) |
| **May 1833** | **Rev. Jeremiah Porter lodges in the store's unfinished loft** — the first date a source puts the building in existence | Andreas |
| 1834-35 | Peck advertising dry goods, hardware and groceries; living at the store | Andreas |
| **1835-07-01** | **scene date** | — |
| 1837 | Peck's **brick house** — the first in Chicago. Excluded: `data/exclusions.json` | Andreas, chicagology |

## 2. What is documented

- **Two storeys, frame.** Andreas says so directly. This is one of only two south-side commercial
  buildings whose height this dataset actually knows (the other is the Temple Building).
- **The south-west corner of South Water and LaSalle.**
- **The unfinished loft**, used as lodging.
- **Peck living there** — which is the load-bearing fact behind the project's exclusion of his
  1837 brick house from the scene.

## 3. What is invented

| aspect | tag | why |
|---|---|---|
| footprint 12.192 x 7.62 m | **conjectural** | no dimension attested; borrowed rectangle inside the documented 55 ft lot cap |
| position coordinate | *inferred* | the corner is documented, the metres are derived |
| wall height, roof, pitch, chimney count, framing system | *inferred* | typological, as everywhere in this dataset |
| ground contact | declared `outside_modelled_ground` | the terrain box stops 130 m short of this building |

## 4. The loft, and why it took two passes

The loft is `documented` and, at the time this record was first written, it was **not stated as an
attribute at all** — the `frame_storefront` archetype was being built in parallel and no record
should guess at a parameter vocabulary that does not exist yet. The archetype landed with `loft`
in its `CONSUMED` set (and with Peck's loft named in its own module docstring), so the attribute
is now stated and built as one gable opening.

`framing_exposed` is deliberately **not** stated. The archetype offers it for a building a source
describes as unfinished, and Andreas describes the loft as unfinished **in May 1833** — twenty-six
months before the scene date. Setting it would show a visitor a building site two years after the
one moment anybody described it.

## 5. Open threads

- **A dimension.** The most likely source is the *Chicago Democrat* itself: an advertiser
  describing his own premises, or a to-let notice. The project holds the issue of 26 Nov 1833 and
  more is expected.
- **The build date.** 1832 or 1833 is unresolved and would narrow `documented_range`.
- **Whether the loft was still unfinished in 1835.**

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
