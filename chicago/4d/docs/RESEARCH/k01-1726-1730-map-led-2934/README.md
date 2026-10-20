# 1726 and 1730 Prairie onto K01 as bounded map-led brick houses (T-2934)

Piece 2 of T-1874 (1726, 1730 and 1736). 1736 has a photograph and is T-2933's; these two have
none, so each is a **bounded** design: the plan is read off the 1911 Sanborn sheet 20 and everything
above it is the kits', chosen so the two fronts do not read as one. The district draft (T-2334) is
refined **in place**: `house_1726_prairie` and `house_1730_prairie` keep their ids and lots, their
archetype changes from `prairie_draft` to `k01_frontage`, the draft rules' `skip` names `s20-1726-f`
and `s20-1730-f`, and their stables stay the draft's. Liberty `L-k01-1726-1730-map-led-2934`; both
houses are retired from `L-draft-prairie-16-18-west-2334`.

## What the sheet says, read off the raster

Sheet 20 at the two lots, the street to the right (east), north up. Read in the draft's lot frame
(`tools/draft_prairie_1904.py`'s `lot_frame`) from the trace `s20fp-1726-b1` / `s20fp-1730-b1` and
the raster itself:

- **1726, '2½B', brick, 'D'.** The front block is 8.4 m along the street (v -4.9 to 3.5) and the
  house 21.6 m deep (u 24.3 to 45.9) — the draft's fill had found only a 7.25 m rectangle inside a
  plan notched on both sides. A canted bay across the front's south part (4.2 m at the wall, 1.4 m
  out) and an open one-storey porch ('1', dashed) beside it on the north, where the entrance is. On
  the south side a canted bay (6.0 m at the wall, 1.6 m out) and, behind it, a rear section that
  stands 1.7 m further south for 9.7 m. On the north side a 1.0 m projection 4.7 m long. Behind the
  rear wall a brick piece printed '2B' and a frame porch, and a second frame porch north of the
  piece. '12 12' printed against the side walls: two 12-inch brick storeys, so the half storey is in
  the roof.
- **1730, '3B', rear '2B', brick, 'D'.** A wall drawn across the house divides a 12.5 m front block
  (u 33.4 to 45.9) from a 10.3 m two-storey rear range, both 7.9 m wide with the north wall on the
  lot line. Inside the front block's walls the sheet draws a **dashed line with a diagonal into each
  corner** — a mansard's curb and hips in plan — and prints '12 12' against its walls: two brick
  storeys, the third in the roof. 1736 next door carries the same dashed line and is a mansard in
  its c. 1890 photograph (T-2933). A small frame (yellow) canted bay on the front's north part; on
  the south a 2.1 m projection from u 36.3 to the front, under the mansard's line in its middle and
  printed '1' at its front end (a one-storey vestibule by the stoop). A frame porch behind the rear
  range.

## What is built

| | 1726 | 1730 |
|---|---|---|
| storeys | 2 + attic under a 38° hip, a street dormer | 2 + a convex slate mansard, two gabled dormers |
| floor, storeys | 1.7 m; 3.9 / 3.7 m | 1.8 m; 4.1 / 3.7 m |
| heads | K09 cornice hoods | flat stone lintels |
| door | north, high K07 stoop | south, high K07 stoop |
| K08 | front canted bay, south canted bay, south rear section, north projection (brick) | frame front bay (one storey), south projection, one-storey vestibule |
| rear wings | 2B brick piece (flat deck), frame porch | 2B brick rear range (flat deck), frame porch on its rear |
| cornice, roofing | K10 bracketed timber; painted standing-seam tin | K10 bracketed timber; Pennsylvania slate faces, tin deck |

## What the kit could not hold (bounded, in the liberty)

K08 holds a sheet's canted bay to 1.2 m out and a projection to 6.0 m by 1.2 m. So 1726's front and
south bays are built 1.2 m out (sheet 1.4 and 1.6), 6.0 m of its 9.7 m rear section 1.2 m proud
(sheet 1.7), its north projection square where the sheet cants its end; 1730's projection and
vestibule 1.2 m out (sheet 2.1). Where 1726's '2B' piece runs 2.9 m into the main rectangle it is
built at the main body's height. Not built: 1726's second rear frame porch (past its host wall —
a K01 wing stands inside it) and a roof over its front porch (the K07 stoop stands alone).

## The site budget

The two web GLBs are 1,923,648 and 1,997,992 bytes (the drafts' were 31,116 and 42,220) and take the
published tree from 318.39 to 322.17 MiB, over the 320 MiB budget. 80 % of each is the texture
sheets every K01 house embeds again (1726's: 1,540,977 bytes, its limestone sheet alone 639,980).
The budget goes to 328 MiB on T-2595's rule (`docs/SITE-BUDGET.md` § 10); sharing the sheets
across houses is the durable fix and is ticketed.

## Browser readings (`tools/qa_k01_t2934.mjs`)

The actual published `/1904/` app, desktop 1280×800 at full detail. Stands: front (across Prairie),
oblique from the south and north walks, rear (the yard between the two rear walls, looking east),
roof (the air). 0 page errors and 0 failed requests; load to ready 45 s and JS heap 57.0 MB on this
runner's software GL (a relative reading, not a device claim).

| stand | draw calls | triangles | within budget |
|---|---|---|---|
| rear | 294 | 2.92 M | yes (`browser-validation-after-desktop-c.json`) |
| roof | 314 | 4.38 M | yes (read in the run that first took the rear from 12 m up; that run's file was not kept) |

A first rear stand 12 m over the alley, and a second in the yard looking south-east down the backs
toward the 1800 block, read 398 and 393 draws against the 360 budget: both views take in half the
avenue, so the stand was re-aimed at the two rear walls. Screens: `after-desktop-*.jpg`. The phone
reading at 390×780 is the smoke's (the PR lists the legs run); a before/after pair from one camera
and a phone set of these stands were not taken in this run.

## Limits

- No photograph, plate or description of 1726 or 1730 has been read; every elevation is the kits'.
- 1736 is still the draft until T-2933 merges, so the three are not yet seen together finished.
