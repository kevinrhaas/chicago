# T-3205 — the worked 1700-block Prairie houses: walks, gates and boundaries

The owner (2026-10-27): on the houses that are complete or have had significant work, check
that the walk to the house and the front and side gates, fences and borders match the
pictures; "some you have and they look good, others are missing, cant enter, or are just plain
wrong". This is the per-house audit for the 1700 block (T-3206 did the 1800 block the same way,
`docs/RESEARCH/house-boundaries-T-3206/`).

## What was wrong before

Read in the published 1904 app (`tools/qa_house_walks_t3205.mjs`, stills in `stills/`
`before-desktop-*`):

- **No walk at all** to 1709, 1712, 1720, 1721, 1726, 1729 and 1736: a visitor crossed lawn
  from the public walk to the stair. 1720 (a K16 frame house) had no yard and no boundary of any
  kind; K16 houses had no way to build one.
- **No boundary** before 1709, 1712, 1720, 1721 and 1726, where the pictures (or, with no
  picture, the block's other fronts) show a low coping or kerb on the street line.
- **Closed fronts**: 1729's coping and 1736's wall ran unbroken across the stair's foot; 1708's
  and 1730's entrance gates were drawn shut.
- **Under the ground**: walks laid at the house's foot sat under the app's terrain where the lot
  rises toward the street (0.02-0.11 m), so they flickered or vanished.

The walker itself was never stopped (every door was reached, closest 0.02-0.29 m, no blocked
frames: boundaries are not solid in the app), so "can't enter" was what a visitor saw — no
walk, no opening, a shut gate — not a collision.

## Per house

Walker: the app's own walker from the public walk toward the stoop's foot, 14 s at most;
distance to the foot before → after, metres (desktop 1280×800; the phone run at 390×780, `stills/walks-after-mobile.json`, reads the same). The walker was never stopped before either; what changed is what a visitor sees — a walk, an opening, an open gate.

| House | Pictures read | Walk | Front boundary | Opening / gate | Sides | Walker | Remaining gap |
|---|---|---|---|---|---|---|---|
| 1708 | chicagology townhouses photo (camera solved), GHM Christmas photo (camera solved; 1708 at the frame's edge) | flags 0.6 m to the stair; cinder service walk to the side gate | K11 iron spear fence on a stone curb (unchanged, the photo's) | double gate on piers at the stair, now drawn open 70° | side gate across the passage (unchanged) | 0.02 → 0.02 | none over 0.3 m |
| 1709 Kellogg | Rand McNally 1893 view (camera solved; drawing at ~6 px/m, no boundary resolved) | flags 1.5 m straight to the stoop | **reconstructed** low coping 0.35 m | 1.8 m opening at the stoop | none shown, none built | 0.21 → 0.21 | boundary not shown in any picture (liberty) |
| 1712 | none of the front (1911 Sanborn only) | flags 1.5 m | **reconstructed** low coping 0.35 m | 1.8 m opening | none | 0.29 → 0.29 | no picture (liberty) |
| 1720 Walker | Tyrrell photo before 1878 (camera solved), Tribune 1898 vignette, 2015 photo of the surviving kerb | flags 1.3 m straight out between posts; cinder walk in through the photo's paved way and down the north passage | rounded stone kerb 0.33 m with an iron railing to 0.95 m, six round-topped posts 1.2 m (five the photo's, within ~15 px) | 1.5 m at the stair's foot (the vignette's) and the photo's paved way at s 7.16-8.49 | none shown, none built | 0.09 → 0.09 | the photo's railing runs across the stair's foot where the 1898 vignette draws the opening: the vignette (nearer 1904) is built; railing bars are reconstructed |
| 1721 Dexter | Inland Architect 1891 plate (camera solved), GHM c1888 photo | flags 1.5 m to the stair | low coping 0.4 m, posts 0.9 m at the opening | 1.8 m at the stair | none shown | 0.13 → 0.13 | none over 0.3 m |
| 1726 | Tribune 1898 vignette (no camera) | flags 1.5 m | **reconstructed** low coping 0.35 m | 1.8 m at the stair | none | 0.12 → 0.12 | the vignette's scale (liberty) |
| 1729 Pullman | Detroit Publishing photo (camera solved), Albertype 1890 (vignette scale) | flags 1.5 m from the gap, jogging 0.7 m to the stair | 0.9 m stone wall along Prairie and round the 18th St corner (unchanged) | new 1.6 m gap between two square piers 1.2 m (the photo's ~1.5 m, within the bar) | 18th St side return (unchanged) | 0.16 → 0.16 | the 18th St run of posts on a lower curb east of u 35 and its court piers (Taylor 16555) are not built: the print does not resolve them (T-3160) — written into the conservatory view's match record |
| 1730 | Dewey landowner image 1874 (library image, no camera) | flags 0.6 m; cinder service walk to the side gate | 1.5 m board fence, now standing inside the street line (s 9.0) so it clears the walk | double gate on urn piers, drawn open 70° | side gate moved to the passage (pier s −8.2) | 0.10 → 0.10 | board height and the gate's form are reconstructed (liberty) |
| 1736 | McBirney c1890 photo (camera solved head-on; the print is oblique) | flags 1.0 m from the opening, turned to the stair | 0.74 m wall to the opening and 0.95 m beyond, the stair pier (unchanged heights) | new 1.0 m opening at the stair's foot | none shown | 0.03 → 0.03 | none over 0.3 m |

In scope but left alone:

- **1700 and 1706** are being built by PR 1384 (T-3211), still open and conflicting. Not
  touched here. **When that PR merges, 1700 and 1706 become worked K01 houses with no walk, and
  `tools/check_house_walks.py` will FAIL on them** (they are not on its PENDING list). That lane
  must give them yards (or a PENDING line naming T-3205) in the same merge.
- **The conservatory / palm-house records** (`pullman_house_1729_prairie_conservatory`) have no
  street boundary of their own; the Pullman lot's wall is the house record's. Their three match
  records were re-rendered (they draw the house too) and re-set to `matches` after looking.

## What changed in the records

- `data/structures/*.json` for the nine houses: `form.boundary` and `form.yard` at
  `as_mapped_1904`, every note citing the picture and the pixel reading it rests on; each yard
  carries `grade_m`, the app's ground over the house's lowest foot as measured in the published
  app, so the walks lie on the ground.
- `generators/archetypes/k16_yard.py` (new): K16 frame houses can now carry a kerb with posts,
  railing and openings, and flagged and cinder walks, written into the node extras as
  `k11.wall.stone_coping_wall` and `k14.yard.front_walk` so `check_house_walks.py` reads them.
- `generators/archetypes/k14_yard.py`: a yard behind a coping wall may name `lawn: none`.
  The six coping houses (1709, 1712, 1721, 1726, 1729, 1736) lay no turf: their grass is the
  app's own ground, as 1720's is. This is what kept the published tree inside its 416 MB budget:
  the turf sheet costs about 180 KB in every house GLB that lays it, and with it this PR read
  416.164 MB; without it, 415.097. (1708's and 1730's iron and board fences keep the kit's
  turf and cinder; their yard kit requires both.)
- `tools/check_house_walks.py`: the nine T-3205 PENDING lines are gone; every worked 1700-block
  house now passes.
- Match records re-set after looking at each side-by-side, each with a T-3205 difference
  (`data/reference_views/*/*.match.json`); Pullman's two stay `differs` for their earlier,
  unrelated open items.

## Liberty

`L-k14-walks-1700-block-3205` (docs/LIBERTIES.md): the reconstructed copings at 1709, 1712 and
1726 (no picture resolves them; built as the block's pictured fronts are), the walks' widths,
surfaces and courses past what the pictures show, 1720's railing bars and sixth post, 1729's
pier section, 1730's board height and gate.

## Stills

`stills/before-desktop-*` and `stills/after-{desktop,mobile}-*`: for each house a 'front'
still from the far edge of the public walk and a 'gate' still from the walk's mouth.
