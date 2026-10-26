# T-3155 (piece 1 of T-1893) — 1815 Prairie onto K01 from the Chicagology photographs

It refines the district draft (T-2330) in place under `sears_meeker_house_1815_prairie`.
T-3156 (piece 2 of T-1893) owns what the photographs show that is not built yet, the oblique's camera, and the match
records' `matches`.

## The pictures

Chicagology prints two undated photographs of Joseph Sears's house side by side; the Prairie library
holds the print as `a18-cgy-1815-sears-two-views`, "link only". It is committed as the image store's
copy, with its attribution, at `data/sources/assets/sears_1815_photos_t1893/` under source record
`chicagology_1815_sears_two_views` (rights `check_required`: forms, counts and proportions are read
from it, nothing is derived from it as an asset). The left print is the street front square-on (the
house number 1815 on the transom); the right is the same front and the south flank from the
south-west, the view the Glessner House Museum's photograph `a18-gh-sears-house-exterior` also shows.
Both show one state of the house, and the interpretive panel at the site (c. 1980) draws the 1882
house the same way.

## The plan, from the 1911 sheet (trace s28fp-1815-b1, in the lot's frame: u toward the street, v south)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| front block | 17.5 – 34.96 | -7.12 – 3.35 | K01's main body, 17.46 x 10.47 m; the frame's origin is its rear north corner |
| north strip (in shadow on the print) | 29.0 – 34.1 | -8.7 – -7.1 | a K08 pavilion on the north flank, 5.0 m along it, 1.2 m out (the sheet's 1.55), 0.86 m behind the front |
| canted south flank bay | 18.1 – 25.6 | 3.35 – 4.8 | a K08 canted bay, 7.48 m at the wall, 1.43 m out, two storeys (reconstructed) |
| rear range | 9.6 – 17.5 | -7.12 – 3.35 | K01 rear wing, three storeys under a tin deck |
| one-storey projection on the front | 34.96 – 36.13 | -5.64 – -1.39 | not built: the print has no projection there (match record) |

## The camera

`data/reference_views/sears_meeker_house_1815_prairie/chicagology_square_on.json`, level and square-on
from the far walk of Prairie Avenue, scaled by the front's 10.42 m across the print (71.5 px/m). Its
`solve` says how it was fitted and how far it holds.

## Before and after, from the photograph's camera

- before: `before-draft-chicagology_square_on.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye u 52.25, v 4.08)
- after: `../photo-match/sears_meeker_house_1815_prairie/chicagology_square_on-side-by-side.jpg`

## What K01 could not carry, and so is open

- the pavilion's attic storey with its paired lights under its steep roof (K01's hipped crown starts
  at the main eave), and its full 4 m width (a door cannot be cut through a K08 projection);
- the door's pedimented hood (K07's hood is a flat balconied one), the stoop's newels;
- the rock-faced south flank (K01 lays stone on the street front only).

No generator rule was changed: every part is the K01, K02, K05 and K08 kits as they stand.

## T-3156 (piece 2 of T-1893): the attic storey, the oblique's camera, and 1904

- **The attic.** The pavilion (now 2.2 m wide, 0.3 m in from the north corner) is carried up a
  2.4 m attic storey past the main cornice, the main eave stopping square at its cheeks, its paired transomed lights
  read at x 200-325 px and y 390-250 px on the square-on print, and K01's hipped crown is raised
  onto its wall head by a new option, `mansard.crown.attic_m` (2.35 m: the crown's eave at the
  print's y 210 px, 11.6 m). Every other K01 house builds as before.
- **The oblique.** `data/reference_views/sears_meeker_house_1815_prairie/chicagology_oblique_sw.json`,
  the right print's camera, fitted to sixteen points on the front read in both prints and the
  south flank's cornice line (11.7 px rms on the front). Its `solve` says why the front alone
  could not fix the distance. Side-by-side:
  `../photo-match/sears_meeker_house_1815_prairie/chicagology_oblique_sw-side-by-side.jpg`. The
  Glessner House Museum's photograph of the same view (`a18-gh-sears-house-exterior`) is not in
  the image store, so its camera is not solved.
- **What the oblique shows that the build does not:** the corner bay running about 0.75 m south of
  the main front's south corner (the square-on agrees: its bay's south edge at x 905 px, the
  cornice's return at 850), the rock-faced south flank, its tall panelled stack, the main cornice's
  stone consoles, the curb's cresting. All open in the two match records.
- **Which front stood in 1904.** Sears sold the house to Mrs. Grace Murray Meeker in March 1902 with
  fifteen rooms (Inter Ocean, 28 March 1902); in May 1915 it had twenty-one, "extensively remodeled"
  after the purchase (Chicago Tribune, 1 May 1915), both as Chicagology transcribes them, which
  names Arthur Heun as the architect. The remodel falls between March 1902 and about 1905, so
  1 July 1904 could be either side of it. The photographs show the Sears house; the build follows
  them, and `L-k01-1815-sears-1893` says so. (The record's name, "Arthur Meeker's from 1893", is
  contradicted by the 1902 sale.)
