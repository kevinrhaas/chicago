# 1626 Prairie's main body refined from the district draft to a K01 brick house with its frame front bay (T-2356)

Piece 2 of T-1862 (1626, 1628 and 1630), split by house: 1628 is T-2355, 1630 (the small frame
house) T-2357. The draft T-2334 stood is refined **in place**: `house_1626_prairie` keeps its id
and its archetype changes from `prairie_draft` to `k01_frontage`, the plain brick front T-2341
taught the kit, matched to 1628's. The draft rules' `skip` names `s20-1626-f`, so the draft
builder stands no second building there, and the frontage row names the house (`house_id`), so
its stable keeps `house_1626_prairie_coach_house`.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1626-b1`, T-1840 census `s20-1626-f`: *'3B brick dwelling
(D), the north half of a pair attached to 1628; 2-storey frame (yellow) bay on the Prairie face'*):
three storeys over a basement, brick, attached to 1628 on the south. Built: the K03 common brick
on all four walls; K06 two-over-two sash under K09 cornice-hood lintels on the two lower storeys
and K01's flat stone lintels on the third; the K07 door and stoop at the north end (the draft
rules' row, so the pair's doors stand at their outer ends; 9.68 m to the walk); a K10 bracketed
timber cornice; a 30° K04/K05 hip in painted standing-seam tin; two brick stacks on the ridge;
K04 gutters and downpipes. 1628's floor lines, sash and heads, so the pair runs level.
**The south wall is the party wall and is blank**, standing on 1628's own blank north wall; the
north wall, over the side yard toward 1620 (whose house stands 7.9 m off it), has three windows a
storey (K01's `north_bays`, T-2342). Liberty `L-k01-1626-brick-frame-bay-2356`; 1626's house is
retired from `L-draft-prairie-16-18-west-2334` (its stable stays there).

## The plan: the whole front block, not the draft's strip

The draft's main rectangle was a 26.25 × 3.5 m strip (the rear range and the house in one) and
its front block only 6.25 m wide, because the trace takes the sheet's `12 12 8` numerals, printed
against the north wall at u 39.7-40.3, for a 0.9 m bite out of the house. The raster shows an
unbroken wall there (sheet crop, px 2550-3300 × 2740-3120). The body is the three-storey block the
sheet draws across the whole front: 12.25 m deep and 8.0 m along Prairie, its rear and south walls
laid on 1628's record (u 33.774, v -4.226 in 1626's lot frame), so the pair closes on one party
wall, 0.21 m south of the 1904 parcel line and well inside the sheet fit's 2.46 m.

## Found on the way: K01 bays had no timber

K08 bays on a K01 frontage were stone or brick only (T-2308). The sheet's bay is yellow — frame —
so K01 learned a third bay fabric, **`frame`**: the bay's body in a new `bay_frame` slot (the
glessner-v4 library's `painted_wood`, the dark green painted joinery), its plinth the house's brick
(`bay_brick`, a timber bay standing on the masonry basement), its bands, sills, heads and corbels
painted timber (the house's `fascia` slot). No clapboard lap is modelled; a bay of the period was
boarded and panelled. `generators/archetypes/k01_frontage.py` (`K08_FRAME_ROLES`) and
`k01_frontage_params.py` (`BAY_FABRICS`). No other K01 house's bytes moved: the nine meshes built
through that module were re-emitted for their new input hash and came out byte-identical.

The bay is the kit's canted bay (3.7 m at the wall, 1.1 m out), centred 2.75 m from the party
wall, two storeys under a low tin hip, against a traced yellow piece about 4.7 m along the front
and 2.0 m out (p1, p2). The two front window bays behind it are windows on the third storey only.

## Read but left open: the frame piece crosses the party line

The sheet draws the yellow piece on across the party line in front of 1628's north half, one piece
under a single dashed street side. The census reads it as 1626's bay; it may as well be one
two-tier frame piece across the pair's centre — which would also put the pair's doors at the
centre, not the outer ends the draft rules gave them. 1628 (T-2355) is built without it, so the
question is written into the liberty, not into the model.

## Not built

- **The rear pieces** behind the south part of the rear wall: a 1B brick piece, then a 2B brick
  wing ending in a one-storey frame piece (census `s20-1626-a1`). K01 builds one rectangle; they
  wait for T-2347. The rear window at 6.6 m (from the north) stands where the 1B piece joins.
- **A flat roof** (T-2350 asks for K05's); K01 builds a hip only, as the draft drew it.

## Before and after, the same stands (`tools/qa_k01_t2356.mjs`)

Actual published `/1904/` app; *before* is `dev` at 27eb2e1fe (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the south and north walks, rear (the yard), roof (the air). 0 page errors and 0 failed
requests on all runs; every stand `withinBudget`. Frame times are the median of 6 renders on the
runner's software GL, a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 6) |
|---|---|---|---|---|---|
| desktop before → after | 38.3 → 28.2 s | 26.0 → 26.3 MB | 94-116 → 106-128 (+12) | 1.722-3.039 M → 1.754-3.071 M (+32 k) | 3.00-6.11 → 3.11-6.22 s |
| phone before → after | 15.6 → 16.0 s | 26.0 → 26.3 MB | 59-79 → 71-91 (+12) | 357-443 k → 389-475 k (+32 k) | 0.75-1.20 → 0.82-1.24 s |

The master is 3.02 MB and the web derivative 1.10 MB. Load swings by seconds between runs on this
runner and is no claim. K01 has no light derivative yet, so the phone draws the full assembly:
+12 draws and +32 k triangles, the order of 1608, 1616 and 1628.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-before.json` (both
viewports) and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1626 or the pair has been read; every form is the kits'.
- The bay's dark green is the library's joinery paint, not a reading.
- 1628 on `dev` is still the draft until T-2355 lands; the party wall is laid on T-2355's record.
