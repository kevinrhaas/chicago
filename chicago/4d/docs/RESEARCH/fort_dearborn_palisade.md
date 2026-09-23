# Fort Dearborn — the stockade

> Part of the Fort Dearborn complex. The plan source, the scale derivation, the garrison chronology, the wrong-fort guards and the three corrections to `docs/research/04-structures-south.md` are all in **`docs/RESEARCH/fort_dearborn.md`**, which this memo does not repeat.

## What is evidence

- **A square stockade.** Andreas vol. 1 p. 84: "The fort, as rebuilt, consisted of a square
  stockade". The 1830 Harrison plan's two wall-to-wall distances agree within 3 %.
- **High pickets.** Kinzie, Wau-Bun ch. XVII, of 1831: "The fort was inclosed by high pickets".
- **Two gates, north and south.** Kinzie and Andreas independently; Hubbard locates four
  buildings by reference to them; the plan draws a break in each of those walls and no other.
- **Bastions at the north-west and south-east angles, block-house at the south-west.** Andreas
  p. 84; Hubbard 1827 for two of the three; Kinzie's "bastions at the alternate angles"; the
  plan draws works at exactly three angles.

## What is ours

The size (about 53 m square, ±20 %, derived — see the main memo § 3), the 8° rotation, and
every dimension of the fabric: picket height, width and spacing, gate width, bastion length and
projection. **L47** owns all of it. The posterns are documented and unbuilt.

**And the HEAD of the post, which L47 never named.** Every picket is sharpened over its top
**0.312 m** — 8.4 % of the 3.7 m height, cut out of that height rather than added to it — and no
source describes the head of a Fort Dearborn picket. It is built because a flat-topped post reads
as a fence rail and a pointed one reads as a stockade, which is a drawing argument and not
evidence. **L179** records it; the record's own `construction` note now says it where a visitor
reading the card will find it.

## The two plates, measured (T-0094, 2026-08-24)

`tools/measure_picket_plate.py` reads `p4_0` and the committed master and prints all of this.

- **The plate rules the curtain's top FLAT.** East reach of the north curtain: the cap resolves in
  138 of 195 columns and is straight to **0.45 px rms**, peak-to-peak 2.0 px. The same plate
  resolves individual pickets — column-profile autocorrelation **+0.70 at a 10 px lag**, +0.60 on
  the west reach — and stands the curtain **43 px** tall, so a head of the model's proportion would
  have serrated the line by **3.6 px**. `p4_1` rules the same flat cap. **The plate cannot be cited
  for a pointed picket.** It does not refute one either: a tier-5 lithographer rules a distant
  stockade, and the head stays unattested and ours.
- **The plate cannot be cited for a pale one.** It paints this one continuous wall across a
  **1.85×** range of tone in a single view — median sRGB (200, 191, 158) / lum 191 east of the gate
  work, (117, 102, 76) / lum 103 west of it, against the fort's own frame range at 183, bare bank
  earth at 115 and the paper at 218. `hewn_log`, the surface this project ships, is sRGB
  (158, 141, 120), **lum 143 — between the plate's two readings of the same wall**.
- **The whitewash stays refused.** Fergus's white-washed board fence is the enclosure of **1850**,
  after the pickets came down; nothing of it may tone a wall standing in 1835.
- **What the plate does say and nobody has acted on:** its drawn picket rhythm is ~0.23 of the
  wall's height per post against the model's 0.081 — nearly three times as coarse. Its own ticket.

Evidence: `docs/evidence/t-0094-plate-vs-model.png`, `docs/evidence/t-0094-p4_0-stand.png`.

## Range

Closed at 1849-12-31, which is an upper bound and not a terminus: Fergus says of the fort in
1850 that the enclosure was a whitewashed board fence, "the pickets having been removed at an
earlier date", and nothing dates that removal. The buildings inside therefore carry a longer
range than the wall round them.
