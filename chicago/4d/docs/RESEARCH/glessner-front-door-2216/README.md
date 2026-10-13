# T-2216 (GA-14) — Glessner's Prairie Avenue door, from sheet No. 95

The audit's finding: *the main door has a plain square grid and a simplified lower field*.
`before-review-render.jpg` shows it: a 5 x 4 grid of bars over black glass, a flat lower field and
a bar handle.

## What the sources show

- **Sheet No. 95**, "Main Entrance Door" (`artic_glessner_sheet_95_main_entrance_door`; Art
  Institute of Chicago mqc 69517, 1885-1887, public domain by age; read for proportions, no pixels
  committed). Its "Copy" No. 95A (mqc 69194) agrees line for line. The leaf: a studded border round
  two fields with cusped corners; a square grille of six bars each way, each run past the frame to a
  round knob, the centre three cells by four filled, the top row with **1800** and the rows below
  with one curled scroll a cell; a strap across the middle rail with a boss and knob at its centre,
  a latch plate and drop ring at its left end; iron corners; two fielded panels.
- **The other No. 95A** (mqc 69279) draws a floral rosette grille and is endorsed "Not Correct".
  Nothing is read from it.
- **An undated photograph of the front** (Prairie library `a18-gh-glessner-front-with-keith`,
  probably 1890s-1920s; cited only). The leaf is nearly black, but contrast-stretched it shows the
  figures 1800 about a fifth of the way down and a knob at mid-height: where sheet 95 puts the
  grille's number row and the strap's boss. That is why sheet 95 is taken as the door as built.
- **HABS sheet 5** gives the leaf (4.7 x 7.5 ft); HABS data p. 21 records the doors as oak.

## What changed (generator, record, one bake)

- `generators/archetypes/masonry_house_v4_front_door.py` draws the leaf at sheet 95's shares of the
  opening, laid out from the **viewer's left as seen from outside** (the T-2214 handedness rule), so
  the latch is on the left and 1800 reads left to right from Prairie Avenue.
- Oak grain follows the members: stiles upright, rails and panels across, each member's figure
  shifted from its neighbour's (per-vertex metric UVs, the override the rock facets already use; no
  new material slot).
- The light (phone) tier keeps the grille, strap, boss, latch plate, corners and panels, and leaves
  out the studs, curls, figures and cusps: it stands at 199,204 of its 200,000 triangles.
- `after-app-desktop-entrance-front.jpg` and `after-app-mobile-entrance-front.jpg` are the published
  /1904/ app from `tools/qa_glessner_stone.mjs`'s entrance-front stand, full model at 1280x800 and
  light model at 390x780: zero page errors, the canonical GLBs loaded. The same stand before this
  change is `../glessner-stone-faces/after/desktop-entrance-front.png`. Its east-raking stand reads
  over the house's rendered-triangle allowance at both tiers (3,932,052 of 3,800,000 full; 1,268,352
  of 1,190,000 light); the door's share of the light model is 322 triangles, so that overrun was
  already there and is not this door's.
- `after-review-render.jpg` is `tools/photo_match.mjs` rendering the new GLB square-on from 20 m,
  framed to sheet 95 (a review camera, not a solved one; the drawing is an elevation).

## Left open

- The photograph shows 1800 reading **brighter** than the leaf; gilt or polished figures would
  explain it, but no finish is recorded and there is no bright-metal slot, so they are iron.
- The review render's pane is black (its unlit interior); in the app the pane reflects the sky, so
  the grille, the figures and the scrolls read from the walk.
- Depths, the scrolls' and figures' forms and the corner irons' shape are reconstructed.

Liberties: `docs/LIBERTIES.md` § `L-glessner-front-door-2216`. The house's image gate is T-2228's.
