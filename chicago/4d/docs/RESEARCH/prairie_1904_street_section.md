# The 1904 street section: the curb's reveal, the walk's fall, carriage walks (T-2474)

The owner, 2026-10-13, with the postcard of Prairie Avenue looking south from 18th Street:
*"Look at the curb height and make sure we are correct on that, with correct carriage walk
ways"*; then, with a second photograph, *"it shows the curbs nicely"*.

## What was read

| source | what it shows | carried as |
|---|---|---|
| `chicago_revised_municipal_code_1905`, the 'Slope' sections | the sidewalk space's grade: "a uniform incline from the street line toward the curb line, with a fall of one inch in every three feet" | the fall, inferred for 1904 |
| `picturesque_chicago_1892_prairie_avenue` (the 1887-91 view south from 18th Street; the owner's postcard copy) | a pale dressed stone curb standing above a smooth roadway; a paved crossing of the parkway from the walk to the curb | the reveal's order of size; that crossings existed |
| the owner's second photograph (`data/sources/assets/prairie_streetscape_owner_2026_10/owner_prairie_avenue_curbs_photo.jpg`; publication not identified) | the curb's top about one stoop riser above the roadway, walk and parkway level with the curb's top | the reveal's order of size |
| `views_of_chicago_1905_prairie_michigan` | dressed stone carriage blocks along the parkway's edge | that blocks existed |

No source read states the reveal as a number. A stoop riser of the period is about 7 in, so the
reveal is **7 in, reconstructed** (`docs/LIBERTIES.md` L-prairie-curb-reveal-2474).

## What was built

- `tools/lay_prairie_1904_street_section.py` writes `data/street_section/1904.json`: the fall,
  the reveal, the roadway's level (0.30 m below the lot line on a 66-ft street), and **91
  carriage walks**, one at the middle of every lot at least 40 ft wide, each 5 ft wide from the
  walk to the curb with a 3 x 2 ft, 18-in carriage block beside it at the curb
  (L-prairie-carriage-walks-2474). `check.sh` re-lays and diffs it.
- `renderers/web/js/street-grid.js` draws every band at its fall and every roadway at its level,
  a dressed stone face down from each curb, and a stone edge wherever a roadway at the district's
  edge meets no drawn sidewalk. It cuts the field's own ground out under all of it
  (`terrain.setGroundCut`: a 0.5 m coverage mask, a discard in the ground's shader behind a uniform
  switch, so no other scene's program changes) and tells the walker how far down the street is.
- The parkway elms stand on the parkway's fall and keep clear of the carriage walks.
- L293 (the street section) gains a line saying the section is now drawn.

## Side by side

![the curb at street level, before and after](prairie_1904_street_section/curb-before-after.jpg)
