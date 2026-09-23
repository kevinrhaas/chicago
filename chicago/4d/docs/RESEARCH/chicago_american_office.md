
# The Chicago American Office — research dossier

**Record:** `data/structures/chicago_american_office.json` · **Scene status:** standing;
**the paper is twenty-three days old on 1835-07-01** · **South Water Street parcel**

## 1. Why the record exists

On the scene date the *Chicago American* is **twenty-three days old**. A town of some 3,265 people
supporting two newspapers, one of them three weeks old, is the boom made legible, and that is a
fact worth putting on the ground.

Andreas: established by **T. O. Davis, 8 June 1835**; a weekly, sheet **15½ x 21½ inches**, six
columns, out on **Saturday mornings**; the office **"on Water Street, near the draw-bridge."**

## 2. The honest grade

| what | tag |
|---|---|
| the paper, the founder, the date to the day, the format | **documented** |
| that the office was on South Water near the drawbridge | **documented** |
| which side of Dearborn | *inferred* |
| construction, wall height, roof, pitch, chimney | *inferred* |
| footprint, storey count | **conjectural** |
| **that the office occupied a building of its own at all** | **the largest liberty in the record** |

That last point deserves its own paragraph. **Andreas is explicit when he means rooms in another
man's building** — of the *Democrat* he writes that "an office was secured **in a building**" — and
of the *American* he says only where the office was. This record draws a whole building on the
strength of a premises.

## 3. The drawbridge as an anchor

The **Dearborn Street bridge** of 1834 — about 300 ft of timber causeway with a 60 ft draw between
two tall gallows frames, built by Nelson R. Norton, repaired in 1835 — landed its south abutment at
the foot of Dearborn on South Water. "Near the draw-bridge" therefore means near the Dearborn
crossing, which fixes the position to within a block along the street.

**The side of Dearborn is this record's choice.** West of the crossing, Lot 1 is spoken for —
Andreas puts Madore Beaubien's log house there as the first building on it. East of the crossing
the block toward State is described by the dossier as sparse. East is adopted; if the office was
west of Dearborn this record stands about 34 m east of where it belongs and crowds
`madore_beaubien_house`.

**A corroboration:** the traced 1834 south bank runs **18.7 m** north of this record's north face —
a half-street and a river frontage, the tightest agreement anywhere on this street. The Dearborn
end of South Water is georeferenced better than the Clark end, where the same measurement is 79.6 m.

## 4. Open threads, in order of value

1. **Any surviving number of the *Chicago American* itself**, whose imprint would give its own
   address exactly as the *Democrat*'s first issue gives the *Democrat*'s. This would settle the
   position and possibly the building question in one line.
2. A *Chicago Democrat* advertisement of 1835 naming the American's location.
3. The 1835 town lot records for the South Water frontage between Dearborn and State.

Note for later: by **1839** the *Daily Chicago American* was printing from the third floor of the
Harmon & Loomis building at Clark and South Water. That is a different address, four years on, and
this record does not follow it.

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
