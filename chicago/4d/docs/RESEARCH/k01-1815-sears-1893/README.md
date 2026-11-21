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

## T-3562: the crown's cornice over the attic front alone, and its raked cheeks

The square-on print draws the pavilion's crown with its cornice over the attic's stone front
alone (x 205-402 px, 2.75 m), and on each side of that front a triangle of slate sloping out
and down from the cornice's end to the capped stone shoulder (from about y 230 to y 282 px,
roughly 50 degrees); over the north cheek there is sky, beside the free-standing north stack.
The oblique print draws the south cheek the same way, right of the attic. Read together, the
crown's sides carry down past its cornice to the shoulders, and the attic is narrower than the
pavilion under it above the shoulders' caps.

Built so: K01's hipped crown takes `cheek_inset_m` (its eave over the stone front between the
cheeks, 2.74 m with a 0.18 m overhang), and K08's cheeks take `raked` (over the shoulder the
attic's wall stops, and the slate is a slope from the stone front's edge under the cornice's end
down to the cheek's outer edge on the cap, run back the crown's 5 m depth). On the corner the
pavilion is flush with, the main mansard's lower faces (72 degrees, steeper than the slope)
are cut away over the cheek to the crown's depth, because the print shows sky there and not
slate; the stacks standing in that cut are joined again after it. How far back the cheeks run
is inferred (the prints show only the street end). Both match records re-judged: the crown's
cornice fixed on both; the oblique now matches; the square-on keeps one open item, which front
stood in 1904.

## T-3562: which front stood in 1904

The square-on's last open item is not a difference between the build and the print: the build
matches both prints. It is whether the front the prints show still stood on 1 July 1904. Read on
2026-11-21:

- **The remodel's date.** The Ryerson and Burnham Archives' building index gives the house as
  'Meeker, Arthur, Residence; Heath, D.C., and Company Building', Burnham and Root 1882, 'Heun,
  Arthur [1902 remodeling]', 'sold to Arthur Meeker, 1902, who drastically remodeled the
  residence' (`aic_rba_index_1815_meeker_residence`). Glessner House: 'In 1902, the house was sold
  to Arthur Meeker ... Meeker had the house significantly remodeled from plans prepared by
  architect Arthur Heun' (`glessner_blog_sears_meeker_1815_heun_remodel`). The Meekers' son was
  born on Prairie Avenue in 1902 (Tribune, 1949, on Chicagology's page). Against them stands only
  the 1915 Tribune's loose 'about ten years ago'. So the remodel most likely came in 1902-1903,
  before the 1904 target.
- **Not read on the page.** The finding aid and the Chicago Collections record both answered
  this runner with a browser challenge (403); their wording is as web-search excerpts gave it.
  Both source records are `verified: false` and say so.
- **The dated picture.** The Chicago Daily News photographed 'Arthur Meeker residence showing the
  front and one side with yard' in 1908 (DN-0005529, Chicago History Museum;
  `cdn_dn0005529_meeker_residence_1908`). It is the only known picture of the house after the
  sale, so it shows the remodelled front, or proves the remodel left the front alone. It is not
  in the image store; the store's fetch queue needs a direct image URL, which the catalogue page
  (unreachable here) would give.
- **Not tried, and worth trying:** the daily building-permit columns of the Inter Ocean and the
  Tribune for 1902-1903 (a line for 1815 Prairie, Arthur Meeker, alterations, Arthur Heun), and
  the Chicago Architectural Club's 1903 exhibition catalogue.

The build is unchanged: the photographs stay the 1904 front under `L-k01-1815-sears-1893`, now
weighed as most likely superseded by 1904. Which way to go is the owner's: T-3562 carries the
question (decision pending).
