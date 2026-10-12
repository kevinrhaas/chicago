# 1601 Prairie refined from the district draft to a whole K16 clapboard frame house under a front gable (T-2398)

Piece 1 of T-1866 (1601 and the station at 1605), split by building: the station's platforms,
canopies and signs are T-2399. This is 1601, the register's *frame dwelling* on the 16th Street
corner, which wanted the frame kit 1630 was built from (T-2357) rather than K01's brick. The draft
T-2335 stood is refined **in place**: `house_1601_prairie` keeps its id, its traced main-body
rectangle (15.5 m deep, 5.5 m along Prairie) and its placement, and its archetype changes from
`prairie_draft` to `k16_timber`. The draft rules' `skip` names `s20-1601-f`, so the draft builder
stands no second building there. The sheet draws nothing behind 1601 before the tracks, so there is
no stable to keep.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1601-b1`, T-1840 census `s20-1601-f`: *'2-storey frame
(yellow) dwelling (D), stepped outline; nothing behind it before the tracks'*), through the draft's
fit: a two-storey frame main block and a two-storey wing standing 1.5 m out on its 16th Street side
(u 5.25-12.5, the draft's `r2`), which is the sheet's stepped outline.

Built, all from the K16 kit (`data/components/prairie_1904/k16_timber.json`): clapboard laid board
by board on a water table over a 0.45 m foundation, corner boards at every outside corner; K06
two-over-two sash in the kit's flat timber casing (two bays on the front, four a storey down the
south side, two on the rear, two on the 16th Street side beyond the wing, three a storey on the
wing); a four-panel door at the south end of the front (the draft rules' entrance side, away from
the corner); a deep frieze under a boxed eave with scroll brackets round both blocks; the draft's
40° gable kept, its ridge running back from the street; an attic sash in each gable; a flat deck on
the lower wing (eave 5.8 m against the main block's 6.4 m); one brick stack on the ridge; a small
kit entrance porch with timber steps up to the door. Body paint a grey-green, trim cream, sash
dark green, so it does not repeat 1630's fawn. Liberty `L-k16-1601-frame-house-2398`; 1601 is
retired from `L-draft-prairie-16-18-east-2335`.

## What the kit learned: a gable

K16 closed whole houses under a hip or a flat deck (T-2357). 1601's draft roof is a gable, and a
small frame house of the period most often had one, so `generators/archetypes/k16_timber.py`
learned `roof.kind: "gable"` with `ridge: "u"` or `"v"` (`k16_timber_params.py` validates both):

- **the roof**: two slopes over the eave rectangle, and under each rake a verge box the eave's
  depth — a soffit from the wall out under the slope and a fascia at its outer edge — so the
  overhang reads closed from the ground, as the boxed eave does along the sides.
- **the gable** (`gable_end`, a new kit sample on each end wall the ridge points at): because the
  kit's boxed eave runs across every wall, the gable stands on it as a closed pediment. Clapboard is
  laid up from the eave in courses, each cut short where it meets the rake board's lower edge
  (`clapboards` takes a `span` clip for it), round any attic sash the wall's `gable_windows` names;
  a rake board runs under each verge to the apex.

Each gable is a part of the house, so `tools/check_timber_kit.py` holds it to the kit's rules like
every wall — laps, stagger, end grain, trim proud, no doubled face, costs, metric UVs. No other K16
bytes moved: the specimen, 1630 and 1638's front rebuild byte-identical (`k16_timber.py --check`,
`k16_emit.py --check`); 1630 and 1638's manifest entries carry the new code hash.

## Before and after, the same stands (`tools/qa_k16_t2398.mjs`)

Actual published `/1904/` app; *before* is `dev` at 9ddba5457 (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the south walk and from the 16th Street corner, rear (the tracks' side), roof (the air). 0 page
errors and 0 failed requests on all four runs; every stand `withinBudget`. Frame times are software
GL on the runner, a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 16.3 → 17.3 s | 31.7 → 31.7 MB | 94-110 → 95-111 (+1) | 0.512-1.729 M → 0.544-1.761 M (+32 k) | 1.02-1.40 → 1.10-1.48 s |
| phone before → after | 12.7 → 11.2 s | 31.7 → 31.7 MB | 72-83 → 72-83 (±0) | 348-365 k → 380-397 k (+32 k) | 0.28-0.42 → 0.31-0.46 s |

The master is 1.72 MB and the web derivative 0.20 MB, 1630's size. K16 has no light derivative, so
the phone draws the full house: +32 k triangles. Load swings by seconds between runs on this runner
and neither the fall nor a rise is a claim.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-before.json` (both
viewports) and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1601 has been read, so there is no image gate; every form
  but the plan, storeys and frame is the kit's.
- The sheet draws no porch. The door stands about 0.7 m over grade and needs steps, and the kit's
  porch is the smallest thing it builds that carries them; a source showing a bare stoop or a
  longer porch replaces it.
- Not built: the trace's narrower step at the front of the 16th Street side (about 1 m out, u
  13-16) and the rear wall's slant along the rear lot line (up to 1.9 m behind the rectangle). The
  rectangles stand where the draft fitted them.
- The gable is ~1 m lower than the draft's, because the draft's storeys were 3.9 and 3.5 m and the
  kit's frame house eaves at 6.4 m, as 1630's does.
- No gutters or downpipes (a box gutter is taken to lie in the boxed eave); no rear door; no
  cellar lights.
