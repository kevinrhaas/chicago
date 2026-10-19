# T-2879: Glessner's courtyard, plan against section along S

HABS sheet 2 (first-floor plan) and sheet 4 (Section A-A, looking east) disagree along S
in the courtyard. Sheet 4 puts the bow at S26.3-38.6 where the plan puts it at
26.8-39.3. It puts the stair tower 0.63 ft south of the plan with a radius 0.3 ft larger,
and the terrace's terminal post about 1.1 ft north. T-2759 recorded this and left it open
because "there is no single datum shift to apply". This ticket rules on it. The building
work the ruling calls for is T-2880.

`read_court.py` takes every reading below off the native scans. Run it from `chicago/4d`.
Its output is in `readings.txt`. The frames are T-2218's plan controls and T-2228's section
controls, unchanged.

## The evidence neither earlier reading used: sheet 2's printed court chain

Sheet 2 prints the courtyard's N-S depth as a chain at about W51, beside the A-A cut line:
**12'-8" + 10'-0" + 12'-0" + 12'-6" = 47'-2"**, running north from the south line (S74.0).
A printed dimension outranks a scan reading, and the plan's drawn ticks reproduce it at
three of its four points:

| chain point | printed S | sheet 2 drawn | sheet 4 drawn |
|---|---|---|---|
| south line | 74.00 | 74.08 | — |
| tower mass, south junction with the east wing face | 61.33 | 61.27 | drum edge 62.30 |
| tower mass, north junction | 51.33 | 50.78 | drum edge 51.21 |
| bow's tangent on the east wing face | 39.33 | 39.42 | bow flank 38.66 |
| range's court face (26'-10") | 26.83 | 26.99 (beside the bow and west of the cut) | 26.21 (the cut) |

## The ruling

1. **Positions along S in the court come from the printed chain, then the plan.** The plan
   scan agrees with the printed chain within 0.16 ft at the face, the bow and the tower's
   south junction. Sheet 4 does not agree, and its disagreement is a **shift, not a scale**:
   it draws the bow 12.45 ft across against the printed 12'-6" (the plan scan reads 12.43),
   with both flanks moved north together with the court face it is cut through (face
   -0.62, bow tangent -0.67 against the printed values). Read sheet 4 for heights and
   shapes. Use its S positions in the court only after re-zeroing them on the printed court
   face: **+0.65 ft ± 0.05**.
2. **The bow stays as built** (S26.84-39.4, centre W27.8/S28.8, r 10.6). The printed 12'-6"
   places it there.
3. **The stair tower stays on the plan** (centre W27.3/S56.1, r 5.25). The printed 10'-0"
   ends at S61.33, and the record's circle meets the W26.5 face at S61.29. The plan's drum
   reads r 5.13 about its newel. Sheet 4 draws the drum 11.09 ft across. Re-zeroed, that is
   S51.86-62.95, which overruns the printed mass by 0.5 ft at the north and 1.6 ft at the
   south, so sheet 4 draws the drum wide. Its S56.73 / r 5.55 is not adopted for position
   or radius. Its tower heights (eave, bell, finial) are unaffected.
4. **The terminal post stays on the plan** (W33.81/S46.20, r 0.9; T-2759). Sheet 4 draws its
   shaft at S45.35-46.67. Re-zeroed, that is S46.0-47.3. Seen from the west, the plan-built
   post shows past the terrace wall's end from S46.2 (the wall's outer face, end-on) to
   S47.1. That agrees within 0.2 ft at both edges. **The "1.1 ft" was the frame, not the
   post.**

So the three disagreements reduce to one offset, plus one drafting error on the tower's
drum. T-2759 read the tower's 0.63 ft "the other way" as proof that no single shift
applies. The printed chain shows that 0.63 ft was the drum drawn too wide, not the plan
misplaced.

## What this leaves in the habs04-terrace-section view

`habs04-terrace-overlay.jpg` lays the drawing's ink (red) over the render from the
committed camera. The camera reads in sheet 4's own frame (S0 at the north wall, about
59.3 px/ft, principal column at S39.31). The model mixes the two frames, so the view still
shows the gap the ruling explains:

- read on sheet 4 and built at its un-re-zeroed S: the coping's traced section profile
  (`cap_section_profile`, ending at S45.35), the two terrace grilles' clears (`window_S`,
  T-2218) and the east-court garden light beyond the post. These line up with the drawing
  in this camera.
- read on the plan: the terrace wall's arc, the post, the bow and the stair. These sit
  about 0.65 ft south of the drawing in this camera.

Where the two meet, the render shows the coping reaching the post early over T-2759's
reconstructed shoulder (S45.35-46.8). It also shows the wall's end covering the post's
north half (render S46.3 against the drawing's stone shaft from S45.4). T-2880 carries
those sheet-4 readings and this camera onto the plan's frame by the same +0.65 ft, builds
the coping's terminal into the plan's post, rebakes, and brings the view to `matches`.

Nothing here is invented, and no liberty is added. The ruling is reasoning over two
unrestricted HABS drawings (`habs_glessner_house_il_1015_drawings`) and one printed
dimension chain.
