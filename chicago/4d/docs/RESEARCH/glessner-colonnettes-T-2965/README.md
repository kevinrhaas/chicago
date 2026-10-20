# T-2965: Glessner's Prairie window colonnettes, to HABS sheets 3 and 6 and the photographs

The owner's report (2026-10-20): the second-floor colonnettes on the Prairie Avenue front "have a tapered
look, and they fit with the stone color of the building and the top is ornamented and the bottom is an
angular base", and then "the top of each colonette is different, make sure you render those photographic
correct, use modern photos as needed".

Before this, every one of the seven was the same grey limestone column: a straight round shaft standing
0.19 m proud of the wall, a bell capital of repeated acanthus, and a plain plinth
(`before-sheet6-group-of-four.jpg`).

## What each source gives

| source | what it settles |
|---|---|
| HABS ILL-1015 sheet 6 (`prairie_1904_v1/research/public/glessner-habs-sheet-6.png`, 75.5 px/ft) | all seven colonnettes in elevation: the straight taper (about 0.63 ft at the neck, 0.9 ft at the foot), the splayed square base about 1.1-1.15 ft across at the sill and 0.13 of the opening tall, the block capital about 1.4 ft across, and the outline of each capital's band and body, every one different |
| HABS sheet 3 (plan) | each colonnette is the round front of a stone mullion about 0.95 x 1.5 ft, flush with the wall's face, not a free column |
| Glessner House Museum, "The stone capitals on Glessner House" (glessnerhouse.blogspot.com, 2013-02-11), three close-ups held as `a18-ghm-blog-capital-1-2013`, `-hhr-2013`, `-2-2013` | nine capitals (seven front, two north) carved in place from August 1887 by John Evans of Evans & Tomb, each different; the one over the front door carries Richardson's monogram. The close-ups show it and its two neighbours: a cushion block, straight-sided under a carved top band and rounded in to the shaft below, with the body, volutes and stiff leaf tips each capital carries |
| `a18-gh-glessner-front-with-keith` (c. 1888) | the taper and the base's joint seen in the round, from the north-east |
| `a18-rba-taylor-2135-glessner-ne` | that the colonnettes are the front's granite, not a lighter trim stone |

The capitals run south to north in the record (`prairie_colonnette.capitals` in
`data/structures/glessner_house.json`), each with the band, body and volutes it carries and a `read` note
saying where that came from. Three come from the close-ups; the other four are read off the sheet's small,
stippled drawing (see `docs/LIBERTIES.md`, L-glessner-colonnettes-2965).

## The images

Each is the drawing or photograph on the left and the neutral review render of the master GLB on the right,
from the cameras in `cameras/` (`node tools/photo_match.mjs cameras/<view>.json`).

- `before-sheet6-group-of-four.jpg`: dev before this change, against sheet 6's four-light group over the door.
- `after-sheet6-group-of-four.jpg`: the same view after. The taper, the splayed bases, the flush mullions and
  a different capital on each colonnette line up with the sheet.
- `after-capitals-2013-closeups.jpg`: the three capitals the museum photographed (south to north: basket weave
  under diamonds, the monogram under a checker band, crossing stems under discs), against the close-ups.
- `after-oblique-c1888-front.jpg`: the colonnade from the north-east against the c. 1888 front.
- `inapp-*.png`: the town itself at 1280 x 800 and 390 x 780, before and after.

## What is not changed

The openings and sashes, and the north gable pair's colonnettes (the other two of the nine). The carved string
course under the colonnade keeps its carving; it is now the front's granite, as the colonnettes over it are.
Sheet 6 draws the openings 5.0 ft tall where the record builds 4.5 ft; the colonnettes take their heights as
shares of the record's opening, and the difference is left for its own ticket.
