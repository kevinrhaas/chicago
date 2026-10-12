# 1613 Prairie refined from the district draft to a four-storey K01 brick house under a flat roof (T-2417)

Piece 1 of T-1868, which asked for 1613, 1615 and 1619 together. Three houses are more than one
run's demonstration, so the ticket was split by house, as T-1862 was: 1613 is this ticket, 1615 (its
attached south partner) is T-2418, and 1619 (the stone front with a drawing, under the image gate)
is T-2419. The draft T-2335 stood is refined **in place**: `house_1613_prairie` keeps its id and
its rear wall, its archetype changes from `prairie_draft` to `k01_frontage`, the draft rules' `skip`
names `s20-1613-f`, and the frontage row names the house (`house_id`).

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1613-b1`, T-1840 census `s20-1613-f` and `s20-1613-a1`):
four storeys, brick, the north half of a pair attached to 1615, with a one-storey frame (yellow)
porch across the whole rear. Built: the K03 common brick on all four walls; K06 two-over-two sash
under K09 cornice-hood lintels on the two principal storeys and K01's flat stone lintels on the two
above; the K07 door and stoop at the north end of a three-bay front, beside the side passage to
1611; a K10 bracketed timber cornice under the blocking course of K01's flat roof (K05's parapet
deck, T-2350, in painted flat-seam tin); two plain brick stacks against the party wall. Three
windows a storey on the world-north wall, over the passage; two in the rear. **The world-south wall
is the party wall with 1615 and is blank.** Liberty `L-k01-1613-brick-flat-2417`; 1613 is retired
from `L-draft-prairie-16-18-east-2335`.

## Found on the way

- **The first K01 house on the east side.** 1601, 1609 and 1611 there are K16 frame houses; every
  K01 house so far stood on the west side, where the
  plan's u runs east and v north. Here the lot frame turns 180 degrees (rotation 179.611), so K01's
  local south wall and south end are the world's north. Nothing in the kit is tied to the compass:
  `entrance_bay: "south"` puts the door at the front's world-north end, `side_bays` windows the
  world-north wall, and leaving `north_bays` empty builds the world-south party wall blank. The
  record's notes say which is which wherever a compass word appears.
- **The draft was 1.3 m too narrow.** The draft's fit stopped at 5.25 m because the trace takes the
  sheet's dimension numerals, printed against both side walls at u 19.5-21.7, for bites out of the
  house. The traced walls either side run straight from v -2.65 to 3.90, the lot's own south line,
  where 1615's traced main part begins (v 3.93). The body is 6.55 m wide, from the traced north
  wall to the party line, and the position moves 0.9 m north with it.
- **K01 wings learn a `frame` fabric.** The sheet's porch is frame, and K01's rear wings were brick
  only (`_rear_wings` refused any other fabric). A `frame` wing is the K08 frame bay's painted
  timber (T-2356) from grade to its flat tin deck, its sash cased in the painted trim, and it carries
  no brick string course. This touches `k01_frontage.py` and `k01_frontage_params.py`. Every
  K01/K12/K13/K16 mesh whose inputs hash the kit's code was re-emitted for its new input hash, and
  their bytes are unchanged.

## Not built

- **The porch's door, its steps to the yard, and any rear stair.** K01 wings cut sash only. Whether
  the porch stood open on posts or closed in boards and sash, no source says. K01 builds a closed
  one, and the liberty says that an open one is just as likely.
- **1615's half of the party wall.** 1615 is still the draft, whose north wall stands at v 4.22 in
  this lot's frame, 0.32 m off this one, until T-2418 lays its north wall on this one.

## Before and after, the same stands (`tools/qa_k01_t2417.mjs`)

Actual published `/1904/` app; *before* is `dev` at 3e5e943e2 (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the north and south walks, rear (1613's own yard) and roof (the air). 0 page errors and 0
failed requests on all four runs, and every stand is `withinBudget`. Frame times are software GL on
the runner: a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 40.4 → 30.6 s | 32.2 → 32.5 MB | 118-207 → 130-219 (+12) | 1.863-3.483 M → 1.889-3.509 M (+25.5 k) | 2.67-7.78 → 2.75-7.90 s |
| phone before → after | 19.1 → 19.4 s | 32.3 → 32.5 MB | 87-141 → 99-153 (+12) | 479-731 k → 505-757 k (+25.5 k) | 0.77-1.46 → 0.81-1.53 s |

The master is 2.61 MB and the web derivative 1.06 MB. Load swings by seconds between runs on this
runner, and neither the fall nor a rise is a claim. K01 has no light derivative yet, so the phone's
light tier draws the full assembly: +12 draws and +25.5 k triangles, the order of 1608, 1616 and
1628.

Screens: `before-*.jpg`, `after-*.jpg`. Readings: `browser-validation-before.json` (both
viewports) and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1613 or of the pair has been read. Every form is the kits'.
- The porch's dark-green boards are the frame bay's paint (T-2356), not a reading.
