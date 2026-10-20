# T-2861: Glessner's bow hood and its trough, to HABS sheet 4 (the hood section)

Piece 3 of T-2852. Every reading below comes off the native sheet-4 scan
(`prairie_1904_v1/research/public/glessner-habs-sheet-4.png`), on T-2228's section controls: north wall x 1165,
grade y 5858, 100.6 px/ft across and 97.7 px/ft up. The readings were taken on
`../glessner-court-exterior-T-2925/grid_crop.py` crops at 0.1 ft. Heights are feet above north grade. S is given in
sheet 4's own frame, then on the plan's frame after T-2879's re-zero (+0.65 ft). Each edge is good to about ±0.05 ft.

`native_over_render.py` puts the drawing (top) over the render from the `habs04-hood-section` camera (bottom), at the
camera's own scale and on one grid. The three images are the whole hood, its south end and its north end.

## The readings

| | sheet 4 | plan S | built before | built now |
|---|---|---|---|---|
| copper's south end | S38.62, at the eave 27.38 ft | 39.27 | about 39.9 (0.20 m past the wall) | 39.38 (0.05 ft past the wall's 39.33-39.4) |
| bow wall's drawn face | S38.62-38.66 | 39.27-39.31 | 39.4 (T-2925) | unchanged |
| trough, south end (end-on) | face 0.31 ft out from the wall; top 27.38, foot 27.0-27.04 | | 0.18 m box, face 1.13 ft out, 0.14 m deep | face 0.094 m (0.31 ft) out, 0.11 m deep |
| trough, north end (cut) | back S26.2, lip S26.55 at 27.30, floor 27.04 | | | the same section |
| fascia under the trough | none drawn: the wall's coursing runs up to 27.0 | | none | none |

The copper's line meets the wall line at the eave and goes no further: the hood does not oversail the bow. The short
steeper stroke from there down to the trough's outer corner (S38.93, 27.18 ft) is the trough's end. The record's
`hall_bow_roof.eave_overhang_ft` (0.05) puts the eave just past the built wall, so the hood's 45 mm drip apron stands
inside the trough and clear of the brick. `rainwater_details.bow_gutter` gives the bow's trough its own section
(`projection_m` from the wall, `depth_m`). Without either, the generator's output is the old one.

## On the render

- The copper now ends at S38.73 against the drawn 38.62. The 0.09-0.11 ft is the bow's carried radius (T-2925: the
  drawn bow ends at plan 39.31, the built one at 39.4), not the hood's.
- The trough's face and foot fall within about 0.1 ft of the drawn lines; its top renders 0.05 ft under the drawn
  eave, the section/eave datum T-2228 records.
- In `habs04-court-exterior` the hood and trough are trimmer at the bow's south end, and nothing else moves. The
  terrace section is pixel-identical.

## Left for T-2939

The north end shows one thing that no earlier review recorded: the court-bow leader. Sheet 4 draws it dropping from
the trough at about S26.95 to 26.56 ft, then offsetting north to S26.54 at 25.8 ft, with a ring at S26.45, 26.55 ft.
The build's box leader drops about 0.5 ft further north and has no ring. It is an `open` item on the match record, so
`habs04-hood-section` stays `differs` until T-2939 lands. Every item T-2861 owned is `fixed`.
