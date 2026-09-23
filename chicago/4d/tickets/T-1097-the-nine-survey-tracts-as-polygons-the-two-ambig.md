---
id: T-1097
title: The nine survey tracts as polygons: the two ambiguous swatches resolved by position, the land sales sorted onto the tracts, and a generator reading the layer
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0792
opened: 2026-09-12
closed: 2026-09-12
pr: null
claimed_by: run 9/12/2026, 8:25:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T01:27:28.458Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34730332513
---

The nine survey tracts as polygons: the two ambiguous swatches resolved by position, the land sales sorted onto the tracts, and a generator reading the layer.

Piece 2 of 2 of **T-0792 — The legend's nine coloured tracts are the town's survey history — who surveyed what ground, when, for whom — and the project has no tract layer**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

Piece 1 (T-1096) read the legend. This piece owns everything the parent asked that a
colour measurement cannot deliver.

1. **`data/reconstruction/1835_survey_tracts.json`** — nine polygons with the legend's
   wording verbatim, its survey date, the owner on the scene date with a source, and a
   grade. The lake-shore tracts close on the shore T-0793 traces. The reservation swatch
   has a control inside it already: Wright's *L. House* glyph, committed at
   `data/traces/wright_1834_lighthouse_glyph.json`, 40.9 m in from the derived tract — a
   traced blue edge should put the tower FURTHER inside, not nearer.
2. **The two ambiguous swatches — line 6 `Surveyed 1833` and line 8 `Surveyed in 1833` —
   resolved BY POSITION, not by colour.** T-1096 measured why: the nine chips carry six
   separable colours, chip 6 shares a class with Kinzie's Addition and Canal Section 9,
   and chip 8 stands 47 RGB units from the School Section against a 60.8 within-chip
   spread. The method that is left: inside a class whose other members are named ground,
   the band that is NOT on named ground belongs to the unnamed chip.
3. **Sort the land sales onto the tracts.** Every row in `data/research/land_sales/` that
   names a section or a tract gets the polygon it falls in.
4. **Feed the generators.** The plat module reads the tract it is inside to choose its
   street width and block module; the reserved-ground file cites the blue polygon.

**Two findings from T-1096 that will bite here.**

- **Nearest-chip assignment misfiles Wabansia.** Its boundary stroke in the north-west has
  faded far enough that it classifies with chip 8's duller orange rather than with chip 3,
  its own colour. Any polygon built by assigning ground to the nearest chip puts Wabansia
  in the wrong tract.
- **The largest coloured region on the sheet is paper damage.** Chip 8's class returns an
  8,184-cell region over the lake quadrant (E 1528…1983, N −2447…−1290): the foxing and the
  repair of the tear the sheet's own caption describes. Polygon work off the orange class
  needs a damage mask first, and the neat line committed in
  `data/traces/wright_1834_legend_swatches.json` (x 620…4400, y 960…5720) does not exclude
  it, because the lake is inside the neat line.
