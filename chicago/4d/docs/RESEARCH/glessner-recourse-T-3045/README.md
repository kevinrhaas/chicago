# Glessner's granite re-coursed above bed 7 (T-3045, of T-3026)

T-3044 read Taylor 2135 (c. 1887-89) through its T-2858 camera and found the Prairie front's
beds 7-23 standing 4.5-4.75 % over sheet 5's printed course inches, as sheet 6's 1965
photogrammetric plot draws them. This piece lays them so, and rules T-2986's printed-inches
ruling again (`L-glessner-coursing-2986`).

## What was built

- **The courses.** `v4_detail.ashlar_course_scale = {"beds": [7, 23], "scale": 1.045}` lays
  courses 8-23 at 1.045 times their printed inches. The record keeps the figures as written.
  The scale comes from sheet 6 (14.77 ft over 14.13) and Taylor 2135's two clean piers. The
  third pier, S1, read 4.75 % with correlation 0.65. Below bed 7 nothing moves (HABS 5, T-2949).
  One coursing still turns the NE corner, so both granite faces take it.

  | bed | printed, ft ng | laid, ft ng |
  |---|---|---|
  | 8 | 9.25 | 9.3044 |
  | 15 | 14.4583 | 14.7471 |
  | 19 | 19.25 | 19.7544 |
  | 23 | 22.1667 | 22.8023 |
  | cap top | 22.50 | 23.1356 (cut at the 23.1 eave) |

- **The north eave.** Sheet 4's scaled street eave is 23.1 ft ng. The cap's top now reaches
  0.04 ft over it, which is inside what a scaled section can be read to. So the eave stands
  and the cap is cut at it. The 18th Street eave band, our reconstruction, had stood at
  22.6-23.1 in the 0.6 ft the printed string left. It is now the cap course's own 22.80-23.1.
  A 22.6 ft foot would hang across bed 23 and the upper windows' heads.
- **Apertures on the string's sums (L305).** The corridor lights keep their beds: 8-15
  (9.3044-14.7471) and 19-23 (19.7544-22.8023). So does the window over the great arch
  (19-23). The Prairie first-floor sills stay on bed 8 (T-2974's rule) at 8.76 ft door. The
  Prairie heads keep sheet 6's 14.3 ft, now 0.09 ft over bed 15 rather than 0.38 ft up the
  20-inch course. Bed 19 now meets the 19.2 ft second-floor sills.
- **The north cameras.** Both north plates take the narrow first-floor light as a fixed
  height control. `tools/glessner_north_pairs.py` now reads that light from the record. Both
  cameras were re-solved (`--cameras`) and fit a little tighter: RMS 5.45 against 5.70 px on
  HABS 13, and 8.72 against 8.77 px on HABS 14. They read the gable pairs at 19.83-24.52 ft
  (HABS 13 19.89-24.43, HABS 14 19.77-24.61). The record builds that reading, which is
  +0.2 ft on 19.6-24.3. The north finial reading through HABS 14's camera was re-derived;
  its tip residual moves 29.4 to 30.5 px.
- **A clipping crumb.** The rebake left one 0.3 x 1.7 mm piece of rock face, where a facet
  was clipped at a partition line, as two faces back to back on K01's 1 mm lattice.
  `block()` now drops any face piece under 2.5 mm in every direction (`CRUMB_M`). That takes
  no random draw, so every other stone is unchanged. The full master loses 535 such
  triangles, and K01's coincident-face verdict is clean again.

## The re-reading

T-3044's own `read_courses.py` was run, unchanged, on the re-coursed master's bare render
through Taylor 2135's camera (`readings.json`, `pier-n2.png`):

| pier | correlation as laid, before | after | best free scale about bed 7, before | after |
|---|---|---|---|---|
| N1 | 0.04 | 0.77 | 1.045 | 0.9975 |
| N2 | 0.07 | 0.69 | 1.0475 | 1.000 |
| S1 | -0.12 | 0.17 | 1.045 | 0.995 |

The render's beds now stand where the photograph's do, to half a percent. Two other numbers
moved:

- **The openings registration** rises a little (north 1.0214 to 1.0246, south 1.0293 to
  1.034). It registers on the sills too, and the Prairie sills rose 0.05 ft.
- **The script's relief rows** (`relief_lower_lip`) are not reported here. They place the
  photograph's courses on the printed beds scaled by the fit, and they take the render as
  the printed string. That no longer holds, so the method has to be re-based on the laid
  beds before T-3046 measures the relief against it.
